"""
Tests for Authentication Module

Tests:
- Wallet authentication
- User profiles
- Sessions
- KYC verification
"""

import pytest
import time
from datetime import datetime, timedelta, timezone

from dcmx.auth.wallet_auth import (
    WalletAuthManager,
    UserProfile,
    UserRole,
    KYCLevel,
    SessionManager,
    WalletCredentials,
)


class TestUserProfile:
    """Test user profile."""
    
    def test_create_profile(self):
        """Test creating user profile."""
        profile = UserProfile(
            wallet_address="0x123abc",
            username="testuser",
            email="test@example.com",
        )
        
        assert profile.user_id is not None
        assert profile.wallet_address == "0x123abc"
        assert profile.username == "testuser"
        assert profile.kyc_level == KYCLevel.NONE
    
    def test_profile_to_dict(self):
        """Test converting profile to dict."""
        profile = UserProfile(
            wallet_address="0x123abc",
            username="testuser",
            roles=[UserRole.ARTIST],
        )
        
        data = profile.to_dict()
        assert data["username"] == "testuser"
        assert data["roles"] == ["artist"]
    
    def test_profile_from_dict(self):
        """Test creating profile from dict."""
        data = {
            "user_id": "user123",
            "wallet_address": "0x123abc",
            "username": "testuser",
            "kyc_level": 1,
            "roles": ["artist"],
        }
        
        profile = UserProfile.from_dict(data)
        assert profile.username == "testuser"
        assert profile.kyc_level == KYCLevel.BASIC
        assert UserRole.ARTIST in profile.roles
    
    def test_update_last_login(self):
        """Test updating last login."""
        profile = UserProfile(
            wallet_address="0x123abc",
            username="testuser",
        )
        
        old_login = profile.last_login
        profile.update_last_login()
        
        assert profile.last_login is not None
        assert profile.last_login > old_login if old_login else True
    
    def test_verify_kyc(self):
        """Test KYC verification."""
        profile = UserProfile(
            wallet_address="0x123abc",
            username="testuser",
        )
        
        assert profile.kyc_level == KYCLevel.NONE
        
        profile.verify_kyc(KYCLevel.ENHANCED)
        assert profile.kyc_level == KYCLevel.ENHANCED
        assert profile.kyc_verified_at is not None
    
    def test_add_role(self):
        """Test adding role."""
        profile = UserProfile(
            wallet_address="0x123abc",
            username="testuser",
        )
        
        assert UserRole.ARTIST not in profile.roles
        
        profile.add_role(UserRole.ARTIST)
        assert UserRole.ARTIST in profile.roles
        
        # Adding same role again shouldn't duplicate
        profile.add_role(UserRole.ARTIST)
        assert profile.roles.count(UserRole.ARTIST) == 1
    
    def test_has_role(self):
        """Test checking role."""
        profile = UserProfile(
            wallet_address="0x123abc",
            username="testuser",
            roles=[UserRole.ARTIST],
        )
        
        assert profile.has_role(UserRole.ARTIST) is True
        assert profile.has_role(UserRole.ADMIN) is False


class TestWalletCredentials:
    """Test wallet credentials."""
    
    def test_create_credentials(self):
        """Test creating credentials."""
        creds = WalletCredentials(wallet_address="0x123abc", nonce="abc123")
        
        assert creds.wallet_address == "0x123abc"
        assert creds.nonce == "abc123"
        assert not creds.is_expired()
    
    def test_credentials_expire(self):
        """Test credentials expiration."""
        creds = WalletCredentials(
            wallet_address="0x123abc",
            nonce="abc123",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        
        assert creds.is_expired() is True


class TestSessionManager:
    """Test session management."""
    
    def test_create_session(self):
        """Test creating session."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="user123",
            wallet_address="0x123abc",
            token="token123",
            ip_address="127.0.0.1",
        )
        
        assert session.user_id == "user123"
        assert session.wallet_address == "0x123abc"
        assert session.active is True
    
    def test_get_session(self):
        """Test getting session."""
        manager = SessionManager()
        
        session1 = manager.create_session(
            user_id="user123",
            wallet_address="0x123abc",
            token="token123",
        )
        
        session2 = manager.get_session(session1.session_id)
        assert session2 is not None
        assert session2.session_id == session1.session_id
    
    def test_get_invalid_session(self):
        """Test getting invalid session."""
        manager = SessionManager()
        
        session = manager.get_session("invalid_session_id")
        assert session is None
    
    def test_revoke_session(self):
        """Test revoking session."""
        manager = SessionManager()
        
        session = manager.create_session(
            user_id="user123",
            wallet_address="0x123abc",
            token="token123",
        )
        
        manager.revoke_session(session.session_id)
        
        retrieved = manager.get_session(session.session_id)
        assert retrieved is None
    
    def test_revoke_user_sessions(self):
        """Test revoking all user sessions."""
        manager = SessionManager()
        
        session1 = manager.create_session(
            user_id="user123",
            wallet_address="0x123abc",
            token="token1",
        )
        
        session2 = manager.create_session(
            user_id="user123",
            wallet_address="0x123abc",
            token="token2",
        )
        
        manager.revoke_user_sessions("user123")
        
        assert manager.get_session(session1.session_id) is None
        assert manager.get_session(session2.session_id) is None


class TestWalletAuthManager:
    """Test wallet authentication manager."""
    
    def test_generate_nonce(self):
        """Test generating nonce."""
        manager = WalletAuthManager()
        
        nonce = manager.generate_nonce("0x123abc")
        assert nonce is not None
        assert len(nonce) > 0
    
    def test_get_nonce(self):
        """Test getting nonce."""
        manager = WalletAuthManager()
        
        generated_nonce = manager.generate_nonce("0x123abc")
        retrieved_nonce = manager.get_nonce("0x123abc")
        
        assert retrieved_nonce == generated_nonce
    
    def test_register_user(self):
        """Test registering user."""
        manager = WalletAuthManager()
        
        profile = manager.register_user(
            wallet_address="0x123abc",
            username="testuser",
            email="test@example.com",
            roles=[UserRole.ARTIST],
        )
        
        assert profile.username == "testuser"
        assert profile.wallet_address == "0x123abc"
        assert UserRole.ARTIST in profile.roles
    
    def test_register_duplicate_wallet(self):
        """Test registering duplicate wallet."""
        manager = WalletAuthManager()
        
        manager.register_user(
            wallet_address="0x123abc",
            username="testuser1",
        )
        
        with pytest.raises(ValueError):
            manager.register_user(
                wallet_address="0x123abc",
                username="testuser2",
            )
    
    def test_get_user_by_wallet(self):
        """Test getting user by wallet."""
        manager = WalletAuthManager()
        
        profile1 = manager.register_user(
            wallet_address="0x123abc",
            username="testuser",
        )
        
        profile2 = manager.get_user_by_wallet("0x123abc")
        assert profile2 is not None
        assert profile2.user_id == profile1.user_id
    
    def test_get_user(self):
        """Test getting user by ID."""
        manager = WalletAuthManager()
        
        profile1 = manager.register_user(
            wallet_address="0x123abc",
            username="testuser",
        )
        
        profile2 = manager.get_user(profile1.user_id)
        assert profile2 is not None
        assert profile2.username == "testuser"
    
    def test_update_profile(self):
        """Test updating profile."""
        manager = WalletAuthManager()
        
        profile1 = manager.register_user(
            wallet_address="0x123abc",
            username="testuser",
        )
        
        updated = manager.update_profile(
            user_id=profile1.user_id,
            email="newemail@example.com",
            bio="My bio",
        )
        
        assert updated.email == "newemail@example.com"
        assert updated.bio == "My bio"
    
    def test_create_session_from_nonce(self):
        """Test creating session from nonce."""
        manager = WalletAuthManager()
        
        nonce = manager.generate_nonce("0x123abc")
        
        session = manager.create_session_from_nonce(
            nonce=nonce,
            token="token123",
            ip_address="127.0.0.1",
        )
        
        assert session is not None
        assert session.user_id is not None
        assert session.token == "token123"
    
    def test_create_session_invalid_nonce(self):
        """Test creating session with invalid nonce."""
        manager = WalletAuthManager()
        
        session = manager.create_session_from_nonce(
            nonce="invalid_nonce",
            token="token123",
        )
        
        assert session is None
    
    def test_get_auth_status(self):
        """Test getting auth status."""
        manager = WalletAuthManager()
        
        manager.register_user("0x123abc", "user1")
        manager.register_user("0x456def", "user2")
        
        status = manager.get_auth_status()
        assert status["total_users"] == 2
        assert status["active_sessions"] == 0
