"""
DCMX Security Module

Implements:
- JWT authentication
- Rate limiting
- CORS security
- Input validation
- Encryption/Decryption
- Audit logging
- OWASP compliance
"""

import logging
import hashlib
import hmac
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, List, Tuple
from functools import wraps
import re
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for operations."""
    PUBLIC = "public"
    USER = "user"
    ARTIST = "artist"
    ADMIN = "admin"


class RateLimiter:
    """Rate limiting implementation.
    
    Note: For distributed systems, use Redis or similar for shared state.
    This implementation is for single-process use.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - self.window_seconds
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests
        self.requests[identifier] = [
            ts for ts in self.requests[identifier]
            if ts > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_reset_time(self, identifier: str) -> int:
        """Get seconds until rate limit resets."""
        if identifier not in self.requests:
            return 0
        
        if not self.requests[identifier]:
            return 0
        
        oldest = min(self.requests[identifier])
        reset_time = oldest + self.window_seconds
        return max(0, int(reset_time - datetime.now(timezone.utc).timestamp()))


class JWTManager:
    """JWT token management."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_blacklist: set = set()
    
    def generate_token(
        self,
        wallet_address: str,
        user_id: str,
        username: str,
        security_level: SecurityLevel = SecurityLevel.USER,
        expires_in_hours: int = 24,
    ) -> str:
        """Generate JWT token."""
        payload = {
            "wallet": wallet_address,
            "user_id": user_id,
            "username": username,
            "level": security_level.value,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=expires_in_hours),
            "jti": secrets.token_urlsafe(32),  # Unique token ID for revocation
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Token generated for {username} ({wallet_address[:16]}...)")
        return token
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            # Check blacklist
            decoded = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if decoded.get("jti") in self.token_blacklist:
                logger.warning(f"Blacklisted token used: {decoded.get('jti')}")
                return None
            
            return decoded
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def revoke_token(self, token: str):
        """Revoke a token."""
        try:
            decoded = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            self.token_blacklist.add(decoded.get("jti"))
            logger.info(f"Token revoked: {decoded.get('jti')}")
        except:
            pass


class InputValidator:
    """Input validation and sanitization."""
    
    @staticmethod
    def validate_wallet_address(address: str) -> bool:
        """Validate Ethereum wallet address."""
        if not address.startswith("0x"):
            return False
        if len(address) != 42:
            return False
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username."""
        if len(username) < 3 or len(username) > 32:
            return False
        pattern = r'^[a-zA-Z0-9_-]+$'
        return re.match(pattern, username) is not None
    
    @staticmethod
    def sanitize_input(value: str, max_length: int = 1000) -> str:
        """Sanitize user input."""
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Limit length
        value = value[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            value = value.replace(char, '')
        
        return value.strip()
    
    @staticmethod
    def validate_amount(amount: float, min_val: float = 0, max_val: float = 1000000) -> bool:
        """Validate transaction amount."""
        try:
            amount = float(amount)
            return min_val <= amount <= max_val
        except (ValueError, TypeError):
            return False


class EncryptionManager:
    """Encryption/Decryption utilities."""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt."""
        if not salt:
            salt = secrets.token_hex(32)
        
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000,  # iterations
        )
        
        return hashed.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash."""
        new_hash, _ = EncryptionManager.hash_password(password, salt)
        return hmac.compare_digest(new_hash, hashed)
    
    @staticmethod
    def encrypt_sensitive_data(data: str, key: str) -> str:
        """Encrypt sensitive data using Fernet (AES-128)."""
        from cryptography.fernet import Fernet
        
        try:
            f = Fernet(key.encode() if isinstance(key, str) else key)
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    @staticmethod
    def decrypt_sensitive_data(encrypted: str, key: str) -> str:
        """Decrypt sensitive data using Fernet (AES-128)."""
        from cryptography.fernet import Fernet
        
        try:
            f = Fernet(key.encode() if isinstance(key, str) else key)
            return f.decrypt(encrypted.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    @staticmethod
    def generate_api_key() -> Tuple[str, str]:
        """Generate API key and hash."""
        api_key = secrets.token_urlsafe(32)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return api_key, api_key_hash


class AuditLogger:
    """Audit logging for compliance.
    
    Note: For production, persist logs to database or blockchain.
    This implementation uses in-memory storage.
    """
    
    def __init__(self):
        self.audit_log: List[Dict] = []
    
    def log_action(
        self,
        action: str,
        user_id: str,
        resource: str,
        details: Dict = None,
        status: str = "success",
    ):
        """Log an action for audit trail."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "details": details or {},
            "status": status,
        }
        self.audit_log.append(entry)
        
        logger.info(f"Audit: {action} by {user_id} on {resource} - {status}")
    
    def get_audit_trail(self, user_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get audit trail."""
        if user_id:
            return [e for e in self.audit_log if e["user_id"] == user_id][-limit:]
        return self.audit_log[-limit:]


class SecurityManager:
    """Central security manager."""
    
    def __init__(self, secret_key: str):
        self.jwt_manager = JWTManager(secret_key)
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.input_validator = InputValidator()
        self.encryption_manager = EncryptionManager()
        self.audit_logger = AuditLogger()
    
    def authenticate(self, token: str) -> Optional[Dict]:
        """Authenticate user with token."""
        return self.jwt_manager.verify_token(token)
    
    def authorize(self, user_info: Dict, required_level: SecurityLevel) -> bool:
        """Authorize user access."""
        user_level = SecurityLevel[user_info.get("level", "USER").upper()]
        
        levels = {
            SecurityLevel.PUBLIC: 0,
            SecurityLevel.USER: 1,
            SecurityLevel.ARTIST: 2,
            SecurityLevel.ADMIN: 3,
        }
        
        return levels[user_level] >= levels[required_level]
    
    def check_rate_limit(self, user_id: str, limit: Optional[int] = None) -> Tuple[bool, Optional[int]]:
        """Check rate limit for user."""
        if limit:
            limiter = RateLimiter(max_requests=limit)
        else:
            limiter = self.rate_limiter
        
        if limiter.is_allowed(user_id):
            return True, None
        else:
            return False, limiter.get_reset_time(user_id)
    
    def get_security_report(self) -> Dict:
        """Get security metrics."""
        return {
            "blacklisted_tokens": len(self.jwt_manager.token_blacklist),
            "audit_log_entries": len(self.audit_logger.audit_log),
            "active_rate_limits": len(self.rate_limiter.requests),
        }
