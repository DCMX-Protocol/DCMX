"""
SQLAlchemy ORM models for DCMX database.

All tables required for replacing in-memory and file-based storage:
- Legal compliance (acceptance records, audit events, deletion requests)
- Wallets and users (profiles, roles, sessions)
- NFTs and assets (certificates, ownership, sales, royalties)
- Rewards and economics (claims, sharing, listening, bandwidth)
- Transactions and activity (blockchain txs, voting, skips)
- System configuration (settings, admin actions, multisig)
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey,
    Enum as SQLEnum, Index, UniqueConstraint, CheckConstraint, DECIMAL, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET, ARRAY as PG_ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator

Base = declarative_base()


# Custom UUID type that works with both PostgreSQL and SQLite
class UUID(TypeDecorator):
    """Platform-independent UUID type."""
    impl = String(36)
    cache_ok = True
    
    def __init__(self, *args, **kwargs):
        # Remove as_uuid argument if present (not supported by base impl)
        kwargs.pop('as_uuid', None)
        super().__init__(*args, **kwargs)
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


# ============================================================================
# LEGAL COMPLIANCE TABLES
# ============================================================================

class AcceptanceRecord(Base):
    """Legal document acceptance records (replaces JSONL file storage)."""
    __tablename__ = "acceptance_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)  # terms_and_conditions, privacy_policy, etc.
    version = Column(String(20), nullable=False)
    accepted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Optional metadata
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    signature = Column(String(132))  # Blockchain signature proof
    read_time_seconds = Column(Integer, default=0)
    document_hash = Column(String(64))  # SHA-256 of document content
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_acceptance_user_doc', 'user_id', 'document_type'),
        Index('idx_acceptance_wallet', 'wallet_address'),
        Index('idx_acceptance_date', 'accepted_at'),
    )


class AuditEvent(Base):
    """Compliance audit events (extends existing audit_log.py)."""
    __tablename__ = "audit_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Actor/User
    user_id = Column(String(255), index=True)
    username = Column(String(255))
    wallet_address = Column(String(42), index=True)
    
    # Resource
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    
    # Action details
    action = Column(String(255))
    status = Column(String(20), index=True)  # success, failure, pending
    result = Column(Text)
    
    # Compliance details
    amount = Column(Float)
    currency = Column(String(10), default="DCMX")
    jurisdiction = Column(String(10), default="US")
    kyc_level = Column(Integer, default=0)
    risk_score = Column(Float, default=0.0)
    
    # Technical details
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(255))
    
    # Additional data
    details = Column(JSON)
    error_message = Column(Text)
    
    # Integrity (blockchain-style chaining)
    hash = Column(String(64))
    parent_hash = Column(String(64))
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_audit_user_time', 'user_id', 'timestamp'),
        Index('idx_audit_type_status', 'event_type', 'status'),
    )


class DataDeletionRequest(Base):
    """GDPR/CCPA data deletion requests."""
    __tablename__ = "data_deletion_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    wallet_address = Column(String(42))
    request_type = Column(String(20), nullable=False)  # gdpr, ccpa
    
    # Timeline
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deadline = Column(DateTime, nullable=False)  # 30 days from request
    completed_at = Column(DateTime)
    
    # Status
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed, cancelled
    completion_summary = Column(Text)
    
    # Audit
    requested_by = Column(String(255))  # Email or admin ID
    notes = Column(Text)
    
    __table_args__ = (
        Index('idx_deletion_status_deadline', 'status', 'deadline'),
    )


# ============================================================================
# WALLET & USER TABLES
# ============================================================================

class Wallet(Base):
    """User wallet addresses and balances (replaces in-memory dict)."""
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(42), unique=True, nullable=False, index=True)
    username = Column(String(255), index=True)
    balance_dcmx = Column(DECIMAL(36, 18), default=0, nullable=False)  # High precision for tokens
    
    # Flags
    is_artist = Column(Boolean, default=False, index=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    nfts = relationship("MusicNFT", back_populates="artist_wallet_rel", foreign_keys="MusicNFT.artist_wallet")
    reward_claims = relationship("RewardClaim", back_populates="user_wallet_rel")
    transactions_from = relationship("Transaction", foreign_keys="Transaction.from_wallet", back_populates="from_wallet_rel")
    transactions_to = relationship("Transaction", foreign_keys="Transaction.to_wallet", back_populates="to_wallet_rel")


class User(Base):
    """User profiles and KYC information."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"))
    
    # Profile
    email = Column(String(255), unique=True, index=True)
    username = Column(String(255), unique=True, index=True)
    display_name = Column(String(255))
    bio = Column(Text)
    avatar_url = Column(String(512))
    
    # KYC
    kyc_status = Column(String(20), default="unverified", index=True)  # unverified, pending, verified, rejected
    kyc_level = Column(Integer, default=0)  # 0=none, 1=basic, 2=enhanced
    kyc_verified_at = Column(DateTime)
    
    # Settings
    preferences = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    wallet = relationship("Wallet")
    roles = relationship("UserRole", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")


class UserRole(Base):
    """User role-based access control."""
    __tablename__ = "user_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_name = Column(String(50), nullable=False)  # admin, artist, moderator, user
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_user_role', 'user_id', 'role_name'),
        UniqueConstraint('user_id', 'role_name', name='uq_user_role'),
    )


class UserSession(Base):
    """Authentication sessions."""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")


# ============================================================================
# NFT & ASSET TABLES
# ============================================================================

class NFTCertificate(Base):
    """NFT certificates for songs (from blockchain integration)."""
    __tablename__ = "nft_certificates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Song metadata
    song_title = Column(String(255), nullable=False)
    artist_wallet = Column(String(42), nullable=False, index=True)
    
    # Edition info
    edition_number = Column(Integer, nullable=False)
    max_editions = Column(Integer, nullable=False)
    
    # Pricing
    price_dcmx = Column(DECIMAL(36, 18), nullable=False)
    price_usd_equivalent = Column(DECIMAL(18, 2))
    
    # Watermark & DRM
    watermark_hash = Column(String(64))
    perceptual_fingerprint = Column(String(64))
    watermark_proof_chain_id = Column(String(255))
    
    # Blockchain
    nft_contract_address = Column(String(42))
    token_id = Column(BigInteger)
    transaction_hash = Column(String(66))
    blockchain = Column(String(20), default="polygon")
    
    # Status
    mint_status = Column(String(20), default="pending")  # pending, confirmed, failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    minted_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_nft_cert_artist', 'artist_wallet', 'created_at'),
        CheckConstraint('edition_number <= max_editions', name='check_edition_valid'),
    )


class MusicNFT(Base):
    """Music NFT metadata and ownership."""
    __tablename__ = "music_nfts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nft_id = Column(String(64), unique=True, nullable=False, index=True)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("nft_certificates.id"))
    
    # Metadata
    title = Column(String(255), nullable=False, index=True)
    artist = Column(String(255), nullable=False)
    artist_wallet = Column(String(42), ForeignKey("wallets.address"), nullable=False)
    artist_username = Column(String(255))
    
    # Edition
    edition = Column(Integer, nullable=False)
    max_editions = Column(Integer, nullable=False)
    
    # Pricing
    price_dcmx = Column(DECIMAL(36, 18), nullable=False)
    
    # Blockchain
    content_hash = Column(String(64), nullable=False)
    
    # Engagement metrics
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)
    listeners = Column(Integer, default=0)
    
    # Advanced metrics (JSON for flexibility)
    engagement_metrics = Column(JSON)  # {average_completion, total_listens, skip_count}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    certificate = relationship("NFTCertificate")
    artist_wallet_rel = relationship("Wallet", back_populates="nfts", foreign_keys=[artist_wallet])
    sales = relationship("NFTSale", back_populates="nft")
    royalties = relationship("NFTRoyalty", back_populates="nft")


class NFTSale(Base):
    """NFT transaction history."""
    __tablename__ = "nft_sales"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nft_id = Column(UUID(as_uuid=True), ForeignKey("music_nfts.id"), nullable=False, index=True)
    
    # Sale details
    sale_type = Column(String(20), nullable=False)  # primary, secondary
    seller_wallet = Column(String(42), nullable=False)
    buyer_wallet = Column(String(42), nullable=False, index=True)
    
    # Pricing
    price_dcmx = Column(DECIMAL(36, 18), nullable=False)
    price_usd_equivalent = Column(DECIMAL(18, 2))
    
    # Transaction
    transaction_hash = Column(String(66))
    blockchain = Column(String(20), default="polygon")
    
    # Timestamps
    sale_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    nft = relationship("MusicNFT", back_populates="sales")


class NFTRoyalty(Base):
    """Royalty distribution from NFT sales."""
    __tablename__ = "nft_royalties"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nft_id = Column(UUID(as_uuid=True), ForeignKey("music_nfts.id"), nullable=False, index=True)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("nft_sales.id"))
    
    # Recipient
    artist_wallet = Column(String(42), nullable=False, index=True)
    
    # Royalty details
    royalty_type = Column(String(20), nullable=False)  # primary_sale, secondary_sale
    royalty_percentage = Column(Float, nullable=False)
    royalty_amount_dcmx = Column(DECIMAL(36, 18), nullable=False)
    
    # Status
    payment_status = Column(String(20), default="pending")  # pending, completed, failed
    
    # Timestamps
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime)
    
    # Relationships
    nft = relationship("MusicNFT", back_populates="royalties")
    sale = relationship("NFTSale")


# ============================================================================
# REWARD & ECONOMICS TABLES
# ============================================================================

class RewardClaim(Base):
    """User reward claims with ZK proof status."""
    __tablename__ = "reward_claims"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(String(255), unique=True, nullable=False, index=True)
    user_wallet = Column(String(42), ForeignKey("wallets.address"), nullable=False, index=True)
    
    # Reward details
    reward_type = Column(String(50), nullable=False, index=True)  # sharing, listening, voting, bandwidth
    amount_dcmx = Column(DECIMAL(36, 18), nullable=False)
    
    # ZK proof
    zk_proof_verified = Column(Boolean, default=False)
    zk_proof_data = Column(JSON)
    
    # Status
    claim_status = Column(String(20), default="pending", index=True)  # pending, verified, claimed, rejected
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime)
    claimed_at = Column(DateTime)
    
    # Relationships
    user_wallet_rel = relationship("Wallet", back_populates="reward_claims")


class SharingReward(Base):
    """Rewards for file sharing."""
    __tablename__ = "sharing_rewards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_wallet = Column(String(42), nullable=False, index=True)
    song_content_hash = Column(String(64), nullable=False)
    shared_with_wallet = Column(String(42), nullable=False)
    
    # Reward calculation
    base_reward = Column(DECIMAL(36, 18), nullable=False)
    bonus_reward = Column(DECIMAL(36, 18), default=0)
    total_reward = Column(DECIMAL(36, 18), nullable=False)
    
    # Activity tracking
    recipient_listened = Column(Boolean, default=False)
    recipient_purchased = Column(Boolean, default=False)
    
    # Timestamps
    shared_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reward_claimed = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_sharing_user_date', 'user_wallet', 'shared_at'),
    )


class ListeningReward(Base):
    """Rewards for listening activity."""
    __tablename__ = "listening_rewards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_wallet = Column(String(42), nullable=False, index=True)
    nft_id = Column(String(64), nullable=False, index=True)
    
    # Listening details
    listen_duration_seconds = Column(Integer, nullable=False)
    completion_percentage = Column(Float, nullable=False)
    
    # Reward calculation
    base_reward = Column(DECIMAL(36, 18), nullable=False)
    completion_bonus = Column(DECIMAL(36, 18), default=0)
    total_reward = Column(DECIMAL(36, 18), nullable=False)
    
    # Timestamps
    listened_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    reward_claimed = Column(Boolean, default=False)


class BandwidthReward(Base):
    """Rewards for bandwidth contribution."""
    __tablename__ = "bandwidth_rewards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_wallet = Column(String(42), nullable=False, index=True)
    
    # Bandwidth metrics
    bytes_uploaded = Column(BigInteger, default=0)
    bytes_downloaded = Column(BigInteger, default=0)
    uptime_seconds = Column(Integer, default=0)
    unique_peers_served = Column(Integer, default=0)
    
    # Reward calculation
    base_reward = Column(DECIMAL(36, 18), nullable=False)
    bandwidth_bonus = Column(DECIMAL(36, 18), default=0)
    uptime_bonus = Column(DECIMAL(36, 18), default=0)
    total_reward = Column(DECIMAL(36, 18), nullable=False)
    
    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reward_claimed = Column(Boolean, default=False)
    
    __table_args__ = (
        Index('idx_bandwidth_node_period', 'node_wallet', 'period_start', 'period_end'),
    )


class RoyaltyPayment(Base):
    """Artist royalty payments."""
    __tablename__ = "royalty_payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(String(255), unique=True, nullable=False, index=True)
    artist_wallet = Column(String(42), nullable=False, index=True)
    
    # Payment details
    payment_type = Column(String(50), nullable=False)  # nft_sale, streaming, licensing
    amount_dcmx = Column(DECIMAL(36, 18), nullable=False)
    amount_usd_equivalent = Column(DECIMAL(18, 2))
    
    # Source
    source_transaction_id = Column(String(255))
    source_nft_id = Column(UUID(as_uuid=True), ForeignKey("music_nfts.id"))
    
    # Status
    payment_status = Column(String(20), default="pending", index=True)
    
    # Timestamps
    earned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime)
    
    # Relationships
    source_nft = relationship("MusicNFT")


class RevenuePool(Base):
    """Revenue distribution pools."""
    __tablename__ = "revenue_pools"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pool_name = Column(String(100), nullable=False, unique=True, index=True)
    pool_type = Column(String(50), nullable=False)  # artist, platform, community
    
    # Balance
    balance_dcmx = Column(DECIMAL(36, 18), default=0, nullable=False)
    
    # Distribution rules
    distribution_rules = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_distribution = Column(DateTime)


# ============================================================================
# TRANSACTION & ACTIVITY TABLES
# ============================================================================

class Transaction(Base):
    """All platform transactions."""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Parties
    from_wallet = Column(String(42), ForeignKey("wallets.address"), nullable=False, index=True)
    to_wallet = Column(String(42), ForeignKey("wallets.address"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False, index=True)  # transfer, nft_purchase, reward_claim
    amount_dcmx = Column(DECIMAL(36, 18), nullable=False)
    
    # Status
    status = Column(String(20), default="pending", index=True)  # pending, completed, failed
    
    # Blockchain
    blockchain_hash = Column(String(66), index=True)
    blockchain = Column(String(20), default="polygon")
    
    # Additional data (renamed from 'metadata' to avoid SQLAlchemy conflict)
    transaction_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    
    # Relationships
    from_wallet_rel = relationship("Wallet", foreign_keys=[from_wallet], back_populates="transactions_from")
    to_wallet_rel = relationship("Wallet", foreign_keys=[to_wallet], back_populates="transactions_to")


class VotingRecord(Base):
    """User voting on songs."""
    __tablename__ = "voting_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_wallet = Column(String(42), nullable=False, index=True)
    nft_id = Column(String(64), nullable=False, index=True)
    
    # Vote details
    preference = Column(String(20), nullable=False)  # like, dislike
    reward_tokens = Column(DECIMAL(36, 18), default=0)
    
    # Timestamps
    voted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_vote_user_nft', 'user_wallet', 'nft_id', 'voted_at'),
    )


class SkipRecord(Base):
    """Skip activity tracking."""
    __tablename__ = "skip_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_wallet = Column(String(42), nullable=False, index=True)
    nft_id = Column(String(64), nullable=False, index=True)
    
    # Skip details
    completion_percentage = Column(Float, nullable=False)
    charge_applied = Column(DECIMAL(36, 18), default=0)  # Can be negative
    
    # Timestamps
    skipped_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_skip_user_nft', 'user_wallet', 'nft_id', 'skipped_at'),
    )


class BlockchainTransaction(Base):
    """Blockchain transaction history."""
    __tablename__ = "blockchain_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_hash = Column(String(66), unique=True, nullable=False, index=True)
    
    # Blockchain details
    blockchain = Column(String(20), nullable=False, default="polygon")
    block_number = Column(BigInteger, index=True)
    block_timestamp = Column(DateTime, index=True)
    
    # Transaction details
    from_address = Column(String(42), nullable=False, index=True)
    to_address = Column(String(42), index=True)
    value_wei = Column(DECIMAL(78, 0))  # High precision for wei
    gas_used = Column(BigInteger)
    gas_price_wei = Column(DECIMAL(78, 0))
    
    # Status
    is_confirmed = Column(Boolean, default=False, index=True)
    confirmations = Column(Integer, default=0)
    
    # Contract interaction
    contract_address = Column(String(42))
    input_data = Column(Text)
    
    # Additional data
    transaction_type = Column(String(50))  # transfer, mint, approve, etc.
    additional_data = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    
    # Link to platform transaction
    platform_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    platform_transaction = relationship("Transaction")


# ============================================================================
# SETTINGS & CONFIGURATION TABLES
# ============================================================================

class SystemConfiguration(Base):
    """Platform configuration settings."""
    __tablename__ = "system_configuration"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(JSON, nullable=False)
    config_type = Column(String(50), nullable=False)  # string, number, boolean, json
    
    # Metadata
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    updater = relationship("User")


class AdminAction(Base):
    """Admin action logs."""
    __tablename__ = "admin_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Action details
    action_type = Column(String(100), nullable=False, index=True)
    target_type = Column(String(50))  # user, wallet, nft, transaction, etc.
    target_id = Column(String(255))
    
    # Details
    description = Column(Text)
    parameters = Column(JSON)
    result = Column(Text)
    
    # Timestamps
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    admin = relationship("User")


class MultisigProposal(Base):
    """Multisig wallet proposals."""
    __tablename__ = "multisig_proposals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Proposal details
    proposal_type = Column(String(50), nullable=False)  # transfer, config_change, admin_action
    description = Column(Text, nullable=False)
    
    # Target
    target_wallet = Column(String(42))
    amount_dcmx = Column(DECIMAL(36, 18))
    
    # Voting
    required_signatures = Column(Integer, nullable=False)
    current_signatures = Column(Integer, default=0)
    signers = Column(JSON)  # Array of wallet addresses (JSON for SQLite compatibility)
    
    # Status
    status = Column(String(20), default="pending", index=True)  # pending, approved, rejected, executed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)
    executed_at = Column(DateTime)
    
    # Transaction
    execution_hash = Column(String(66))
    
    __table_args__ = (
        Index('idx_proposal_status_expiry', 'status', 'expires_at'),
    )
