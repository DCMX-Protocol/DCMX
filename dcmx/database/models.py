"""PostgreSQL database models for DCMX blockchain indexing."""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime,
    Index, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class BlockchainEvent(Base):
    """Indexed blockchain events from smart contracts."""
    __tablename__ = 'blockchain_events'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False, index=True)
    contract_address = Column(String(100), nullable=False, index=True)
    transaction_hash = Column(String(100), nullable=False, unique=True, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    log_index = Column(Integer, nullable=False)
    event_data = Column(JSONB, nullable=False)  # Flexible event data storage
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_event_contract_block', 'event_type', 'contract_address', 'block_number'),
        Index('idx_event_indexed_at', 'indexed_at'),
    )


class UserProfile(Base):
    """User profile data (GDPR compliant)."""
    __tablename__ = 'user_profiles'
    
    user_id = Column(String(100), primary_key=True)
    wallet_address = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    kyc_level = Column(Integer, default=0)  # 0=unverified, 1=basic, 2=standard, 3=enhanced
    verified_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Privacy flags
    data_deletion_requested = Column(Boolean, default=False)
    deletion_request_date = Column(DateTime)
    
    __table_args__ = (
        Index('idx_user_wallet', 'wallet_address'),
        Index('idx_user_kyc', 'kyc_level'),
    )


class NFTIndex(Base):
    """Indexed NFT metadata."""
    __tablename__ = 'nft_index'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    token_id = Column(BigInteger, nullable=False)
    contract_address = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    artist = Column(String(255), nullable=False, index=True)
    content_hash = Column(String(100), nullable=False, index=True)
    edition = Column(Integer, nullable=False)
    max_editions = Column(Integer, nullable=False)
    owner_address = Column(String(100), nullable=False, index=True)
    mint_date = Column(DateTime, nullable=False)
    last_sale_price = Column(Numeric(precision=30, scale=0))  # In SUN
    royalty_bps = Column(Integer)  # Basis points
    royalty_recipient = Column(String(100))
    
    __table_args__ = (
        Index('idx_nft_token', 'contract_address', 'token_id', unique=True),
        Index('idx_nft_content', 'content_hash'),
        Index('idx_nft_artist', 'artist'),
    )


class RewardClaimIndex(Base):
    """Indexed reward claims."""
    __tablename__ = 'reward_claims_index'
    
    claim_id = Column(BigInteger, primary_key=True)
    user_address = Column(String(100), nullable=False, index=True)
    claim_type = Column(String(50), nullable=False)  # SHARING, LISTENING, BANDWIDTH
    amount = Column(Numeric(precision=30, scale=0), nullable=False)  # Token amount
    proof_hash = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)  # pending, verified, claimed, rejected
    submitted_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime)
    claimed_at = Column(DateTime)
    transaction_hash = Column(String(100), index=True)
    
    __table_args__ = (
        Index('idx_claim_user_status', 'user_address', 'status'),
        Index('idx_claim_type', 'claim_type'),
    )


class TransactionIndex(Base):
    """Indexed blockchain transactions."""
    __tablename__ = 'transaction_index'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tx_hash = Column(String(100), unique=True, nullable=False, index=True)
    from_address = Column(String(100), nullable=False, index=True)
    to_address = Column(String(100), nullable=False, index=True)
    value = Column(Numeric(precision=30, scale=0), nullable=False)  # In SUN
    token = Column(String(50))  # TRX, DCMX, or token name
    contract_address = Column(String(100), index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), nullable=False)  # success, failed
    gas_used = Column(BigInteger)
    
    __table_args__ = (
        Index('idx_tx_addresses', 'from_address', 'to_address'),
        Index('idx_tx_timestamp', 'timestamp'),
    )


class ComplianceIndex(Base):
    """Compliance audit index."""
    __tablename__ = 'compliance_index'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)
    wallet_address = Column(String(100), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # acceptance, deletion_request, etc.
    document_type = Column(String(100))  # TERMS, PRIVACY, etc.
    document_version = Column(String(50))
    acceptance_hash = Column(String(100))
    blockchain_tx = Column(String(100), index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    ip_address_hash = Column(String(100))  # Hashed for privacy
    metadata = Column(JSONB)  # Additional event metadata
    
    __table_args__ = (
        Index('idx_compliance_user_event', 'user_id', 'event_type'),
        Index('idx_compliance_timestamp', 'timestamp'),
    )


class Analytics(Base):
    """User metrics and analytics."""
    __tablename__ = 'analytics'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    metric_id = Column(String(100), nullable=False, index=True)
    user_address = Column(String(100), index=True)
    metric_type = Column(String(100), nullable=False, index=True)  # balance, nft_count, rewards, etc.
    value = Column(Numeric(precision=30, scale=6), nullable=False)
    metadata = Column(JSONB)  # Additional metric data
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_analytics_user_metric', 'user_address', 'metric_type'),
        Index('idx_analytics_recorded', 'recorded_at'),
    )


# Create indexes for common query patterns
def create_additional_indexes(engine):
    """Create additional performance indexes."""
    from sqlalchemy import DDL
    
    # Partial indexes for active data
    active_claims_idx = DDL(
        "CREATE INDEX IF NOT EXISTS idx_active_claims "
        "ON reward_claims_index (user_address, status) "
        "WHERE status IN ('pending', 'verified')"
    )
    
    recent_transactions_idx = DDL(
        "CREATE INDEX IF NOT EXISTS idx_recent_transactions "
        "ON transaction_index (timestamp DESC) "
        "WHERE timestamp > NOW() - INTERVAL '30 days'"
    )
    
    # Execute
    active_claims_idx.execute(bind=engine)
    recent_transactions_idx.execute(bind=engine)
