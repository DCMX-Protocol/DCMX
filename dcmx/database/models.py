"""
PostgreSQL Database Models for DCMX

SQLAlchemy ORM models for indexing blockchain data.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    BigInteger,
    Boolean,
    Text,
    DateTime,
    Float,
    JSON,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class BlockchainEvent(Base):
    """
    Indexed blockchain events.
    
    Stores all events emitted by DCMX contracts.
    """
    __tablename__ = "blockchain_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    block_timestamp = Column(BigInteger, nullable=False)
    
    # Event details
    contract_address = Column(String(42), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)  # Full event data as JSON
    
    # Processing status
    indexed_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False, index=True)
    
    __table_args__ = (
        Index("idx_contract_event", "contract_address", "event_name"),
        Index("idx_block_time", "block_number", "block_timestamp"),
    )


class UserProfile(Base):
    """
    User profiles with KYC data.
    
    GDPR compliant with soft delete support.
    """
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    wallet_address = Column(String(42), unique=True, nullable=False, index=True)
    
    # Profile data
    username = Column(String(100))
    email = Column(String(255))  # Encrypted
    kyc_verified = Column(Boolean, default=False, index=True)
    kyc_level = Column(Integer, default=0)  # 0=none, 1=basic, 2=enhanced
    verified_at = Column(DateTime)
    
    # User preferences
    preferences = Column(JSON)  # Arbitrary JSON preferences
    
    # Account status
    is_artist = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)  # Soft delete for GDPR
    
    # Relationships
    nfts = relationship("NFTIndex", back_populates="owner", foreign_keys="NFTIndex.owner_wallet")
    transactions = relationship("TransactionIndex", back_populates="user", foreign_keys="TransactionIndex.user_wallet")
    
    __table_args__ = (
        Index("idx_user_kyc", "kyc_verified", "kyc_level"),
    )


class NFTIndex(Base):
    """
    NFT metadata index for fast queries.
    
    Indexes MusicNFT contract data.
    """
    __tablename__ = "nft_index"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_id = Column(BigInteger, unique=True, nullable=False, index=True)
    contract_address = Column(String(42), nullable=False, index=True)
    
    # NFT metadata
    title = Column(String(255), nullable=False)
    artist = Column(String(255), nullable=False, index=True)
    content_hash = Column(String(64), nullable=False, index=True)
    token_uri = Column(Text)
    
    # Edition info
    edition_number = Column(Integer, nullable=False)
    max_editions = Column(Integer, nullable=False)
    
    # Ownership
    owner_wallet = Column(String(42), ForeignKey("user_profiles.wallet_address"), index=True)
    artist_wallet = Column(String(42), nullable=False, index=True)
    
    # Royalty
    royalty_bps = Column(Integer, default=1000)  # Basis points
    
    # Engagement metrics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    play_count = Column(Integer, default=0)
    
    # Timestamps
    minted_at = Column(DateTime, nullable=False)
    last_transferred_at = Column(DateTime)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("UserProfile", back_populates="nfts", foreign_keys=[owner_wallet])
    
    __table_args__ = (
        Index("idx_nft_artist", "artist", "minted_at"),
        Index("idx_nft_owner", "owner_wallet", "minted_at"),
        Index("idx_nft_content", "content_hash"),
    )


class RewardClaimIndex(Base):
    """
    Indexed reward claims for analytics.
    
    Indexes RewardVault contract claims.
    """
    __tablename__ = "reward_claims_index"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(BigInteger, unique=True, nullable=False, index=True)
    
    # Claim details
    claimant_wallet = Column(String(42), nullable=False, index=True)
    reward_type = Column(Integer, nullable=False, index=True)  # Enum value
    amount = Column(BigInteger, nullable=False)
    proof_hash = Column(String(64))
    
    # Status
    verified = Column(Boolean, default=False, index=True)
    claimed = Column(Boolean, default=False, index=True)
    verifier_wallet = Column(String(42))
    
    # Timestamps
    submitted_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime)
    claimed_at = Column(DateTime)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_claim_user", "claimant_wallet", "submitted_at"),
        Index("idx_claim_type", "reward_type", "submitted_at"),
        Index("idx_claim_status", "verified", "claimed"),
    )


class TransactionIndex(Base):
    """
    Indexed transaction history.
    
    Tracks all user transactions across contracts.
    """
    __tablename__ = "transaction_index"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_hash = Column(String(66), unique=True, nullable=False, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    
    # Transaction details
    from_wallet = Column(String(42), index=True)
    to_wallet = Column(String(42), index=True)
    user_wallet = Column(String(42), ForeignKey("user_profiles.wallet_address"), index=True)
    
    # Transaction type
    tx_type = Column(String(50), nullable=False, index=True)  # transfer, mint, burn, etc
    contract_address = Column(String(42), index=True)
    
    # Value
    value_sun = Column(BigInteger)  # TRX value in SUN
    token_amount = Column(BigInteger)  # Token amount
    
    # Status
    status = Column(String(20), default="success", index=True)
    error_message = Column(Text)
    
    # Timestamps
    timestamp = Column(DateTime, nullable=False, index=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserProfile", back_populates="transactions", foreign_keys=[user_wallet])
    
    __table_args__ = (
        Index("idx_tx_user", "user_wallet", "timestamp"),
        Index("idx_tx_type", "tx_type", "timestamp"),
        Index("idx_tx_wallets", "from_wallet", "to_wallet"),
    )


class ComplianceIndex(Base):
    """
    Off-chain compliance audit index.
    
    Indexes ComplianceRegistry contract events.
    """
    __tablename__ = "compliance_index"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(BigInteger, unique=True, index=True)
    
    # User info
    wallet_address = Column(String(42), nullable=False, index=True)
    
    # Document info
    document_type = Column(Integer, nullable=False, index=True)  # Enum value
    document_version = Column(String(20), nullable=False)
    document_hash = Column(String(64), nullable=False)
    
    # Acceptance details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)
    
    # Status
    is_valid = Column(Boolean, default=True, index=True)
    
    # Timestamps
    accepted_at = Column(DateTime, nullable=False, index=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_compliance_wallet", "wallet_address", "accepted_at"),
        Index("idx_compliance_doc", "document_type", "document_version"),
    )


class Analytics(Base):
    """
    Pre-computed analytics for dashboard.
    
    Stores aggregated metrics for fast querying.
    """
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # daily, weekly, monthly, total
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    
    # Metric value
    value_int = Column(BigInteger)
    value_float = Column(Float)
    value_json = Column(JSON)
    
    # Context
    entity_type = Column(String(50))  # user, nft, artist, platform
    entity_id = Column(String(255), index=True)
    
    # Timestamps
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_analytics_metric", "metric_name", "period_start"),
        Index("idx_analytics_entity", "entity_type", "entity_id"),
    )


# Deletion requests table (GDPR/CCPA)
class DeletionRequest(Base):
    """
    Data deletion requests.
    
    Tracks GDPR/CCPA deletion requests with blockchain timestamp.
    """
    __tablename__ = "deletion_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_address = Column(String(42), nullable=False, index=True)
    
    # Request details
    request_type = Column(String(10), nullable=False)  # GDPR or CCPA
    blockchain_timestamp = Column(BigInteger)  # Timestamp from blockchain event
    transaction_hash = Column(String(66))
    
    # Timeline
    requested_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=False)  # 30 days from request
    completed_at = Column(DateTime)
    
    # Status
    status = Column(String(20), default="pending", index=True)  # pending, processing, completed
    completion_notes = Column(Text)
    
    __table_args__ = (
        Index("idx_deletion_status", "status", "deadline"),
    )


# Create indexes for performance
def create_indexes(engine):
    """Create additional indexes for optimized queries."""
    from sqlalchemy import event
    
    @event.listens_for(Base.metadata, 'after_create')
    def receive_after_create(target, connection, tables, **kw):
        """Create custom indexes after table creation."""
        # Add any custom indexes here if needed
        pass
