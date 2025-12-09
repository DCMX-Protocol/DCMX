"""DCMX Artist Management Module

Enables artists to:
- Create verified profiles
- Connect wallets (MetaMask, WalletConnect, etc.)
- Verify NFT ownership
- Manage rights and royalties
- Control distribution permissions
"""

from dcmx.artist.artist_wallet_manager import (
    ArtistWalletManager,
    ArtistProfile,
    WalletAddress,
    NFTOwnership,
    RoyaltySettings,
    WalletSignatureChallenge,
    WalletType,
    VerificationStatus,
    RightsType,
    RoyaltyTier,
)

from dcmx.artist.nft_ownership_verifier import (
    NFTOwnershipVerifier,
    BlockchainProvider,
    MockBlockchainProvider,
    BlockchainNetwork,
    TokenStandard,
    ContractInterface,
    ContentWatermarkLink,
    BlockchainQueryResult,
)

__all__ = [
    # Artist Management
    "ArtistWalletManager",
    "ArtistProfile",
    "WalletAddress",
    "NFTOwnership",
    "RoyaltySettings",
    "WalletSignatureChallenge",
    
    # Enums
    "WalletType",
    "VerificationStatus",
    "RightsType",
    "RoyaltyTier",
    
    # NFT Verification
    "NFTOwnershipVerifier",
    "BlockchainProvider",
    "MockBlockchainProvider",
    "BlockchainNetwork",
    "TokenStandard",
    "ContractInterface",
    "ContentWatermarkLink",
    "BlockchainQueryResult",
]
