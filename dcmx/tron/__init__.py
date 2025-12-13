"""
DCMX TRON Blockchain Integration

This module provides integration with TRON blockchain for:
- Smart contract deployment and interaction
- Event indexing and monitoring
- Transaction management
- Wallet integration
"""

from .config import TronConfig, NetworkConfig, NETWORKS
from .client import TronClient
from .contracts import (
    DCMXTokenContract,
    MusicNFTContract,
    ComplianceRegistryContract,
    RewardVaultContract,
    RoyaltyDistributorContract,
)
from .events import (
    TransferEvent,
    MintEvent,
    ApprovalEvent,
    AcceptanceRecordedEvent,
    RewardClaimedEvent,
    SaleRecordedEvent,
)

__all__ = [
    "TronConfig",
    "NetworkConfig",
    "NETWORKS",
    "TronClient",
    "DCMXTokenContract",
    "MusicNFTContract",
    "ComplianceRegistryContract",
    "RewardVaultContract",
    "RoyaltyDistributorContract",
    "TransferEvent",
    "MintEvent",
    "ApprovalEvent",
    "AcceptanceRecordedEvent",
    "RewardClaimedEvent",
    "SaleRecordedEvent",
]
