"""Blockchain integration for DCMX - Web3 smart contracts and token management."""

from .contracts import (
    BlockchainManager,
    TokenStandard,
    TokenMetadata,
    NFTMintRequest,
    EditionMintRequest,
    BatchMintRequest,
    TransferRequest,
    ApprovalRequest,
    RoyaltyInfo,
    RentalInfo,
    ERC721_ABI,
    ERC1155_ABI,
    ERC2981_ABI,
    ERC4907_ABI,
    MUSIC_NFT_ABI,
    DCMX_TOKEN_ABI,
    REWARD_DISTRIBUTOR_ABI,
    INTERFACE_IDS,
    NETWORKS,
)

from .contract_manager import (
    ContractManager,
    ContractConfig,
    ERC721Handler,
    ERC1155Handler,
    ERC4907Handler,
)

__all__ = [
    # Main managers
    "BlockchainManager",
    "ContractManager",
    "ContractConfig",
    # Token standards enum
    "TokenStandard",
    # Data classes
    "TokenMetadata",
    "NFTMintRequest",
    "EditionMintRequest",
    "BatchMintRequest",
    "TransferRequest",
    "ApprovalRequest",
    "RoyaltyInfo",
    "RentalInfo",
    # High-level handlers
    "ERC721Handler",
    "ERC1155Handler",
    "ERC4907Handler",
    # ABIs
    "ERC721_ABI",
    "ERC1155_ABI",
    "ERC2981_ABI",
    "ERC4907_ABI",
    "MUSIC_NFT_ABI",
    "DCMX_TOKEN_ABI",
    "REWARD_DISTRIBUTOR_ABI",
    # Constants
    "INTERFACE_IDS",
    "NETWORKS",
]
