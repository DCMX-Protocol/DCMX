"""
DCMX User Authentication & Wallet Management

Implements:
- Wallet-based authentication
- User profile management
- Session management
- KYC verification tracking
"""

import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

from dcmx.security.manager import EncryptionManager, AuditLogger

logger = logging.getLogger(__name__)


class KYCLevel(Enum):
    """KYC verification levels."""
    NONE = 0
    BASIC = 1  # Email verified
    ENHANCED = 2  # ID verified
    FULL = 3  # ID + Address verified


class UserRole(Enum):
    """User roles."""
    LISTENER = "listener"
    ARTIST = "artist"
    NODE_OPERATOR = "node_operator"
    ADMIN = "admin"


@dataclass
class UserProfile:
    """User profile with authentication."""
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str = ""
    username: str = ""
    email: str = ""
    profile_image_url: str = ""
    bio: str = ""
    
    # Security & Compliance
    kyc_level: KYCLevel = KYCLevel.NONE
    kyc_verified_at: Optional[str] = None
    roles: List[UserRole] = field(default_factory=list)
    
    # Account
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    active: bool = True
    
    # Stats
    total_tracks: int = 0
    total_followers: int = 0
    total_earnings: float = 0.0
    reputation_score: float = 50.0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['kyc_level'] = self.kyc_level.value
        data['roles'] = [r.value for r in self.roles]
        return data
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "UserProfile":
        """Create from dictionary."""
        if 'kyc_level' in data:
            data['kyc_level'] = KYCLevel(data['kyc_level'])
        if 'roles' in data:
            data['roles'] = [UserRole(r) for r in data['roles']]
        return UserProfile(**data)
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.now(timezone.utc).isoformat()
        self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def verify_kyc(self, level: KYCLevel):
        """Update KYC verification."""
        if level.value > self.kyc_level.value:
            self.kyc_level = level
            self.kyc_verified_at = datetime.now(timezone.utc).isoformat()
            self.updated_at = datetime.now(timezone.utc).isoformat()
            logger.info(f"KYC updated for {self.username}: level {level.value}")
    
    def add_role(self, role: UserRole):
        """Add role to user."""
        if role not in self.roles:
            self.roles.append(role)
            self.updated_at = datetime.now(timezone.utc).isoformat()
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has role."""
        return role in self.roles


@dataclass
class WalletCredentials:
    """Wallet login credentials."""
    wallet_address: str
    nonce: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=15))
    
    def is_expired(self) -> bool:
        """Check if nonce is expired."""
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class Session:
    """User session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    wallet_address: str = ""
    token: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str = ""
    user_agent: str = ""
    active: bool = True
    
    def is_valid(self, max_idle_minutes: int = 120) -> bool:
        """Check if session is still valid."""
        if not self.active:
            return False
        
        idle_time = datetime.now(timezone.utc) - self.last_activity
        return idle_time < timedelta(minutes=max_idle_minutes)
    
    def touch(self):
        """Update last activity."""
        self.last_activity = datetime.now(timezone.utc)


class SessionManager:
    """Manage user sessions.
    
    Note: For production with concurrency, use thread-safe storage (Redis, etc.)
    """
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
    
    def create_session(
        self,
        user_id: str,
        wallet_address: str,
        token: str,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Session:
        """Create new session."""
        session = Session(
            user_id=user_id,
            wallet_address=wallet_address,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        self.sessions[session.session_id] = session
        
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(session.session_id)
        
        logger.info(f"Session created for {user_id}: {session.session_id[:16]}...")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session."""
        session = self.sessions.get(session_id)
        
        if session and session.is_valid():
            session.touch()
            return session
        
        return None
    
    def revoke_session(self, session_id: str):
        """Revoke session."""
        if session_id in self.sessions:
            self.sessions[session_id].active = False
            logger.info(f"Session revoked: {session_id}")
    
    def revoke_user_sessions(self, user_id: str, keep_current: Optional[str] = None):
        """Revoke all user sessions."""
        if user_id in self.user_sessions:
            for session_id in self.user_sessions[user_id]:
                if session_id != keep_current:
                    self.revoke_session(session_id)
            logger.info(f"All sessions revoked for {user_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired = [
            sid for sid, session in self.sessions.items()
            if not session.is_valid()
        ]
        
        for session_id in expired:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up {len(expired)} expired sessions")


class WalletAuthManager:
    """Manage wallet-based authentication.
    
    Handles nonce generation, user registration, session creation, and profile management.
    """
    
    def __init__(self) -> None:
        self.pending_nonces: Dict[str, WalletCredentials] = {}
        self.user_profiles: Dict[str, UserProfile] = {}  # user_id -> profile
        self.wallet_users: Dict[str, str] = {}  # wallet_address -> user_id
        self.session_manager = SessionManager()
        self.audit_logger = AuditLogger()
    
    def generate_nonce(self, wallet_address: str) -> str:
        """Generate nonce for wallet login.
        
        Args:
            wallet_address: Ethereum wallet address
            
        Returns:
            Random nonce string (expires in 15 minutes)
        """
        import secrets
        nonce = secrets.token_hex(32)
        credentials = WalletCredentials(wallet_address=wallet_address, nonce=nonce)
        self.pending_nonces[nonce] = credentials
        
        logger.info(f"Nonce generated for {wallet_address}")
        return nonce
    
    def get_nonce(self, wallet_address: str) -> Optional[str]:
        """Get pending nonce for wallet."""
        for nonce, creds in list(self.pending_nonces.items()):
            if creds.wallet_address == wallet_address:
                if not creds.is_expired():
                    return nonce
                else:
                    del self.pending_nonces[nonce]
        return None
    
    def register_user(
        self,
        wallet_address: str,
        username: str,
        email: str = "",
        roles: List[UserRole] = None
    ) -> UserProfile:
        """Register new user.
        
        Args:
            wallet_address: Ethereum wallet address
            username: User's username
            email: Optional email address
            roles: Optional list of roles (defaults to LISTENER)
            
        Returns:
            Created UserProfile
            
        Raises:
            ValueError: If wallet already registered
        """
        if wallet_address in self.wallet_users:
            raise ValueError(f"Wallet already registered: {wallet_address}")
        
        profile = UserProfile(
            wallet_address=wallet_address,
            username=username,
            email=email,
            roles=roles or [UserRole.LISTENER],
        )
        
        self.user_profiles[profile.user_id] = profile
        self.wallet_users[wallet_address] = profile.user_id
        
        self.audit_logger.log_action(
            action="user_registration",
            user_id=profile.user_id,
            resource=wallet_address,
            details={"username": username},
        )
        
        logger.info(f"User registered: {username} ({wallet_address})")
        return profile
    
    def get_user_by_wallet(self, wallet_address: str) -> Optional[UserProfile]:
        """Get user profile by wallet."""
        user_id = self.wallet_users.get(wallet_address)
        return self.user_profiles.get(user_id) if user_id else None
    
    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        return self.user_profiles.get(user_id)
    
    def update_profile(
        self,
        user_id: str,
        **kwargs
    ) -> Optional[UserProfile]:
        """Update user profile."""
        profile = self.user_profiles.get(user_id)
        if not profile:
            return None
        
        allowed_fields = [
            'username', 'email', 'profile_image_url', 'bio'
        ]
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now(timezone.utc).isoformat()
        
        self.audit_logger.log_action(
            action="profile_update",
            user_id=user_id,
            resource=user_id,
            details=kwargs,
        )
        
        logger.info(f"Profile updated for {user_id}")
        return profile
    
    def create_session_from_nonce(
        self,
        nonce: str,
        token: str,
        ip_address: str = "",
        user_agent: str = ""
    ) -> Optional[Session]:
        """Create session from verified nonce."""
        credentials = self.pending_nonces.get(nonce)
        
        if not credentials or credentials.is_expired():
            logger.warning(f"Invalid or expired nonce: {nonce}")
            return None
        
        # Get or create user
        user = self.get_user_by_wallet(credentials.wallet_address)
        if not user:
            user = self.register_user(credentials.wallet_address, f"user_{credentials.wallet_address[:8]}")
        
        user.update_last_login()
        
        # Create session
        session = self.session_manager.create_session(
            user_id=user.user_id,
            wallet_address=credentials.wallet_address,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # Clean up nonce
        del self.pending_nonces[nonce]
        
        self.audit_logger.log_action(
            action="session_created",
            user_id=user.user_id,
            resource="session",
            details={"wallet": credentials.wallet_address},
        )
        
        return session
    
    def get_auth_status(self) -> Dict[str, Any]:
        """Get authentication system status."""
        return {
            "total_users": len(self.user_profiles),
            "total_sessions": len(self.session_manager.sessions),
            "pending_nonces": len(self.pending_nonces),
            "active_sessions": sum(
                1 for s in self.session_manager.sessions.values()
                if s.is_valid()
            ),
        }
