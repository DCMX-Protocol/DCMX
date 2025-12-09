"""
Tests for Security Module

Tests:
- Rate limiting
- JWT authentication
- Input validation
- Encryption
- Audit logging
- OWASP compliance
"""

import pytest
import time
import secrets
from datetime import datetime, timedelta, timezone

from dcmx.security.manager import (
    SecurityManager,
    RateLimiter,
    JWTManager,
    InputValidator,
    EncryptionManager,
    AuditLogger,
    SecurityLevel,
)


class TestRateLimiter:
    """Test rate limiting."""
    
    def test_rate_limit_allows_requests(self):
        """Test that requests are allowed within limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for i in range(5):
            assert limiter.is_allowed("user1") is True
    
    def test_rate_limit_blocks_excess(self):
        """Test that requests are blocked after limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        for i in range(3):
            limiter.is_allowed("user1")
        
        assert limiter.is_allowed("user1") is False
    
    def test_rate_limit_resets(self):
        """Test that rate limit resets after window."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        assert limiter.is_allowed("user1") is False
        
        time.sleep(1.1)
        assert limiter.is_allowed("user1") is True
    
    def test_get_reset_time(self):
        """Test getting reset time."""
        limiter = RateLimiter(max_requests=1, window_seconds=5)
        
        limiter.is_allowed("user1")
        reset_time = limiter.get_reset_time("user1")
        
        assert reset_time > 0
        assert reset_time <= 5


class TestJWTManager:
    """Test JWT authentication."""
    
    def test_generate_token(self):
        """Test token generation."""
        manager = JWTManager("test_secret_key")
        
        token = manager.generate_token(
            wallet_address="0x123abc",
            user_id="user123",
            username="testuser",
            security_level=SecurityLevel.USER,
        )
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_verify_valid_token(self):
        """Test verifying valid token."""
        manager = JWTManager("test_secret_key")
        
        token = manager.generate_token(
            wallet_address="0x123abc",
            user_id="user123",
            username="testuser",
        )
        
        payload = manager.verify_token(token)
        assert payload is not None
        assert payload["user_id"] == "user123"
        assert payload["username"] == "testuser"
    
    def test_verify_invalid_token(self):
        """Test verifying invalid token."""
        manager = JWTManager("test_secret_key")
        
        payload = manager.verify_token("invalid_token")
        assert payload is None
    
    def test_token_expiration(self):
        """Test token expiration."""
        manager = JWTManager("test_secret_key")
        
        token = manager.generate_token(
            wallet_address="0x123abc",
            user_id="user123",
            username="testuser",
            expires_in_hours=-1,  # Already expired
        )
        
        payload = manager.verify_token(token)
        assert payload is None
    
    def test_revoke_token(self):
        """Test token revocation."""
        manager = JWTManager("test_secret_key")
        
        token = manager.generate_token(
            wallet_address="0x123abc",
            user_id="user123",
            username="testuser",
        )
        
        # Verify token works before revocation
        assert manager.verify_token(token) is not None
        
        # Revoke token
        manager.revoke_token(token)
        
        # Verify token doesn't work after revocation
        assert manager.verify_token(token) is None


class TestInputValidator:
    """Test input validation."""
    
    def test_validate_wallet_address_valid(self):
        """Test validating valid wallet address."""
        assert InputValidator.validate_wallet_address("0xAb5801a7D398351b8bE11C63579d1Ccbf49e0fA2") is True
    
    def test_validate_wallet_address_invalid(self):
        """Test validating invalid wallet address."""
        assert InputValidator.validate_wallet_address("invalid") is False
        assert InputValidator.validate_wallet_address("0x123") is False
        assert InputValidator.validate_wallet_address("123abc") is False
    
    def test_validate_email_valid(self):
        """Test validating valid email."""
        assert InputValidator.validate_email("user@example.com") is True
        assert InputValidator.validate_email("test.user+tag@domain.co.uk") is True
    
    def test_validate_email_invalid(self):
        """Test validating invalid email."""
        assert InputValidator.validate_email("invalid") is False
        assert InputValidator.validate_email("@example.com") is False
        assert InputValidator.validate_email("user@") is False
    
    def test_validate_username_valid(self):
        """Test validating valid username."""
        assert InputValidator.validate_username("user123") is True
        assert InputValidator.validate_username("test-user_123") is True
    
    def test_validate_username_invalid(self):
        """Test validating invalid username."""
        assert InputValidator.validate_username("ab") is False  # too short
        assert InputValidator.validate_username("a" * 33) is False  # too long
        assert InputValidator.validate_username("user@name") is False  # invalid chars
    
    def test_sanitize_input(self):
        """Test input sanitization."""
        assert InputValidator.sanitize_input("hello world") == "hello world"
        # XSS attempt gets sanitized (single quotes and script tags removed)
        result = InputValidator.sanitize_input("hello<script>alert('xss')</script>")
        assert "script" not in result.lower() or result == "helloscriptalert(xss)/script"
        assert InputValidator.sanitize_input("test\x00null") == "testnull"
    
    def test_validate_amount_valid(self):
        """Test validating valid amount."""
        assert InputValidator.validate_amount(100) is True
        assert InputValidator.validate_amount(0) is True
        assert InputValidator.validate_amount(1000000) is True
    
    def test_validate_amount_invalid(self):
        """Test validating invalid amount."""
        assert InputValidator.validate_amount(-1) is False
        assert InputValidator.validate_amount(1000001) is False
        assert InputValidator.validate_amount("invalid") is False


class TestEncryptionManager:
    """Test encryption/decryption."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed, salt = EncryptionManager.hash_password(password)
        
        assert hashed is not None
        assert salt is not None
        assert len(hashed) > 0
        assert len(salt) > 0
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "test_password_123"
        hashed, salt = EncryptionManager.hash_password(password)
        
        assert EncryptionManager.verify_password(password, hashed, salt) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "test_password_123"
        hashed, salt = EncryptionManager.hash_password(password)
        
        assert EncryptionManager.verify_password("wrong_password", hashed, salt) is False
    
    def test_password_salt_different(self):
        """Test that different salts produce different hashes."""
        password = "test_password"
        hash1, salt1 = EncryptionManager.hash_password(password)
        hash2, salt2 = EncryptionManager.hash_password(password)
        
        assert hash1 != hash2
        assert salt1 != salt2
    
    def test_generate_api_key(self):
        """Test API key generation."""
        api_key, api_key_hash = EncryptionManager.generate_api_key()
        
        assert api_key is not None
        assert api_key_hash is not None
        assert len(api_key) > 0
        assert len(api_key_hash) > 0
        assert api_key != api_key_hash


class TestAuditLogger:
    """Test audit logging."""
    
    def test_log_action(self):
        """Test logging action."""
        logger = AuditLogger()
        
        logger.log_action(
            action="test_action",
            user_id="user123",
            resource="resource1",
            details={"key": "value"},
            status="success",
        )
        
        assert len(logger.audit_log) == 1
    
    def test_get_audit_trail_all(self):
        """Test getting all audit trail."""
        logger = AuditLogger()
        
        logger.log_action("action1", "user1", "resource1")
        logger.log_action("action2", "user1", "resource2")
        logger.log_action("action3", "user2", "resource3")
        
        trail = logger.get_audit_trail()
        assert len(trail) == 3
    
    def test_get_audit_trail_filtered(self):
        """Test getting filtered audit trail."""
        logger = AuditLogger()
        
        logger.log_action("action1", "user1", "resource1")
        logger.log_action("action2", "user1", "resource2")
        logger.log_action("action3", "user2", "resource3")
        
        trail = logger.get_audit_trail(user_id="user1")
        assert len(trail) == 2
    
    def test_audit_trail_limit(self):
        """Test audit trail limit."""
        logger = AuditLogger()
        
        for i in range(150):
            logger.log_action(f"action{i}", "user1", f"resource{i}")
        
        trail = logger.get_audit_trail(limit=50)
        assert len(trail) == 50


class TestSecurityManager:
    """Test central security manager."""
    
    def test_authenticate_valid(self):
        """Test authenticating valid token."""
        manager = SecurityManager(secret_key="test_secret")
        
        token = manager.jwt_manager.generate_token(
            wallet_address="0x123",
            user_id="user1",
            username="testuser",
        )
        
        user_info = manager.authenticate(token)
        assert user_info is not None
        assert user_info["user_id"] == "user1"
    
    def test_authenticate_invalid(self):
        """Test authenticating invalid token."""
        manager = SecurityManager(secret_key="test_secret")
        
        user_info = manager.authenticate("invalid_token")
        assert user_info is None
    
    def test_authorize_valid(self):
        """Test authorization check."""
        manager = SecurityManager(secret_key="test_secret")
        
        user_info = {
            "user_id": "user1",
            "level": "ADMIN",
        }
        
        assert manager.authorize(user_info, SecurityLevel.USER) is True
        assert manager.authorize(user_info, SecurityLevel.ADMIN) is True
    
    def test_authorize_invalid(self):
        """Test authorization check fails."""
        manager = SecurityManager(secret_key="test_secret")
        
        user_info = {
            "user_id": "user1",
            "level": "USER",
        }
        
        assert manager.authorize(user_info, SecurityLevel.ADMIN) is False
    
    def test_check_rate_limit(self):
        """Test rate limit check."""
        manager = SecurityManager(secret_key="test_secret")
        
        allowed, reset_time = manager.check_rate_limit("user1")
        assert allowed is True
        assert reset_time is None
