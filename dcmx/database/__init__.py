"""Database layer for DCMX blockchain indexing and analytics.

This module provides PostgreSQL integration for:
- Blockchain event indexing
- User profile management
- NFT metadata tracking
- Transaction history
- Compliance audit logs
- Analytics and metrics
"""

from .models import (
    Base,
    BlockchainEvent,
    UserProfile,
    NFTIndex,
    RewardClaimIndex,
    TransactionIndex,
    ComplianceIndex,
    Analytics,
)
from .connection import DatabaseConnection

__all__ = [
    "Base",
    "BlockchainEvent",
    "UserProfile",
    "NFTIndex",
    "RewardClaimIndex",
    "TransactionIndex",
    "ComplianceIndex",
    "Analytics",
    "DatabaseConnection",
]
