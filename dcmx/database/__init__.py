"""
DCMX Database Module

Provides database infrastructure for persistent storage across all DCMX systems:
- Legal compliance and document acceptance tracking
- User wallets and profiles
- NFT certificates and ownership
- Reward and royalty distribution
- Transaction history and audit logs
- System configuration
"""

from dcmx.database.config import DatabaseConfig
from dcmx.database.database import DatabaseManager, get_session, get_async_session
from dcmx.database.models import (
    Base,
    AcceptanceRecord,
    AuditEvent,
    DataDeletionRequest,
    Wallet,
    User,
    UserRole,
    UserSession,
    NFTCertificate,
    MusicNFT,
    NFTSale,
    NFTRoyalty,
    RewardClaim,
    SharingReward,
    ListeningReward,
    BandwidthReward,
    RoyaltyPayment,
    RevenuePool,
    Transaction,
    VotingRecord,
    SkipRecord,
    BlockchainTransaction,
    SystemConfiguration,
    AdminAction,
    MultisigProposal,
)
from dcmx.database.dal import DataAccessLayer

__all__ = [
    "DatabaseConfig",
    "DatabaseManager",
    "get_session",
    "get_async_session",
    "Base",
    "AcceptanceRecord",
    "AuditEvent",
    "DataDeletionRequest",
    "Wallet",
    "User",
    "UserRole",
    "UserSession",
    "NFTCertificate",
    "MusicNFT",
    "NFTSale",
    "NFTRoyalty",
    "RewardClaim",
    "SharingReward",
    "ListeningReward",
    "BandwidthReward",
    "RoyaltyPayment",
    "RevenuePool",
    "Transaction",
    "VotingRecord",
    "SkipRecord",
    "BlockchainTransaction",
    "SystemConfiguration",
    "AdminAction",
    "MultisigProposal",
    "DataAccessLayer",
]
