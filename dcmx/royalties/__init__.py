"""
DCMX Royalties and Rewards Module.

Implements comprehensive royalty and rewards payment structure for DCMX platform.

Key Components:
- NFT Certificate System: Unique ownership tokens with edition numbers
- Reward Types: Sharing, Listening, Bandwidth, Uptime, Referral, Platform Contribution
- Royalty Distribution: Artist, Platform, Node Operators, Early Buyers
- Reward Claims: ZK proof verification + verifier quorum approval
- Blockchain Integration: Smart contract interactions (ERC-721, ERC-20, ERC-2981)

Usage Example:
    from dcmx.royalties import (
        RoyaltyPaymentStructure,
        RewardClaimVerifier,
        BlockchainIntegration,
        RewardDistributionEngine,
        RewardType
    )
    
    # Initialize systems
    royalty = RoyaltyPaymentStructure()
    verifier = RewardClaimVerifier(royalty)
    blockchain = BlockchainIntegration(
        rpc_url="https://rpc.polygon.com",
        private_key="...",
        nft_contract_address="0x...",
        token_contract_address="0x...",
        royalty_distributor_address="0x..."
    )
    engine = RewardDistributionEngine(royalty, verifier, blockchain)
    
    # Process NFT purchase and royalties
    nft_tx, token_id = await engine.process_nft_sale(
        song_title="My Song",
        artist="Artist Name",
        content_hash="abc123...",
        edition_number=1,
        max_editions=100,
        buyer_wallet="0x...",
        purchase_price_usd=50.0,
        purchase_price_tokens=500,
        watermark_hash="...",
        perceptual_fingerprint="..."
    )
    
    # Process sharing rewards
    share_reward = await engine.process_sharing_reward(
        sharer_wallet="0x...",
        song_content_hash="abc123...",
        shared_with_wallet="0x..."
    )
    
    # Process listening rewards
    listen_reward = await engine.process_listening_reward(
        listener_wallet="0x...",
        song_content_hash="abc123...",
        sharer_wallet="0x...",
        listen_duration_seconds=240,
        completion_percentage=95.0
    )
"""

from dcmx.royalties.royalty_structure import (
    # Enums
    RewardType,
    RoyaltyRecipient,
    
    # Data Classes
    NFTCertificate,
    SharingReward,
    ListeningReward,
    BandwidthReward,
    RoyaltyPayment,
    RewardClaim,
    
    # Main Class
    RoyaltyPaymentStructure,
)

from dcmx.royalties.reward_integration import (
    # Enums
    VerifierNodeStatus,
    
    # Data Classes
    VerifierApproval,
    
    # Classes
    RewardClaimVerifier,
    BlockchainIntegration,
    RewardDistributionEngine,
)

from dcmx.royalties.artist_first_economics import (
    # Enums
    UserActivityType,
    
    # Data Classes
    WalletConversion,
    ArtistFirstPayment,
    UserActivityReward,
    
    # Constants
    FairRewardSchedule,
    
    # Main Class
    ArtistFirstEconomics,
)

from dcmx.royalties.advanced_economics import (
    # Enums
    ArtistTier,
    UserBadge,
    
    # Data Classes
    DynamicPricingModel,
    ArtistTierBenefit,
    UserEngagementScore,
    SeasonalPromotion,
    StreamingAnalytics,
    
    # Main Class
    AdvancedEconomicsEngine,
)

from dcmx.royalties.revenue_pools import (
    # Enums
    PoolType,
    
    # Data Classes
    PoolMember,
    RevenuePool,
    Collaboration,
    ReferralNetwork,
    
    # Main Class
    RevenuePoolManager,
)

from dcmx.royalties.sustainability import (
    # Enums
    TokenomicsModel,
    
    # Data Classes
    TokenSupplyConfig,
    DynamicFeeStructure,
    BurnMechanism,
    PlatformTreasury,
    SustainabilityMetrics,
    
    # Main Class
    SustainabilityEngine,
)

__all__ = [
    # Enums
    "RewardType",
    "RoyaltyRecipient",
    "VerifierNodeStatus",
    "UserActivityType",
    "ArtistTier",
    "UserBadge",
    "PoolType",
    "TokenomicsModel",
    
    # Data Classes
    "NFTCertificate",
    "SharingReward",
    "ListeningReward",
    "BandwidthReward",
    "RoyaltyPayment",
    "RewardClaim",
    "VerifierApproval",
    "WalletConversion",
    "ArtistFirstPayment",
    "UserActivityReward",
    "DynamicPricingModel",
    "ArtistTierBenefit",
    "UserEngagementScore",
    "SeasonalPromotion",
    "StreamingAnalytics",
    "PoolMember",
    "RevenuePool",
    "Collaboration",
    "ReferralNetwork",
    "TokenSupplyConfig",
    "DynamicFeeStructure",
    "BurnMechanism",
    "PlatformTreasury",
    "SustainabilityMetrics",
    
    # Constants
    "FairRewardSchedule",
    
    # Main Classes
    "RoyaltyPaymentStructure",
    "RewardClaimVerifier",
    "BlockchainIntegration",
    "RewardDistributionEngine",
    "ArtistFirstEconomics",
    "AdvancedEconomicsEngine",
    "RevenuePoolManager",
    "SustainabilityEngine",
]
