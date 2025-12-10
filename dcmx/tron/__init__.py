"""TRON blockchain integration for DCMX.

This module provides TRON blockchain integration including:
- Smart contract deployment and interaction
- Event indexing and synchronization
- Token and NFT management
- Compliance registry integration
"""

from .client import TronClient
from .config import TronConfig, NetworkType
from .contracts import (
    DCMXTokenContract,
    MusicNFTContract,
    ComplianceRegistryContract,
    RewardVaultContract,
    RoyaltyDistributorContract,
)

__all__ = [
    "TronClient",
    "TronConfig",
    "NetworkType",
    "DCMXTokenContract",
    "MusicNFTContract",
    "ComplianceRegistryContract",
    "RewardVaultContract",
    "RoyaltyDistributorContract",
]
