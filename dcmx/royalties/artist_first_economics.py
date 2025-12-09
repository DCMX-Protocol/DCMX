"""
DCMX Artist-First Economics with Wallet Conversion System.

Implements:
- 100% artist profit on initial NFT purchases
- Fair user rewards for promotion, listening, voting, and energy sharing
- Wallet conversion system (external coins → DCMX tokens)
- Secondary market with majority artist royalties
- Governance rewards for community voting
"""

import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class UserActivityType(Enum):
    """Types of user activities that earn rewards."""
    SHARING = "sharing"  # Share song with other wallets
    LISTENING = "listening"  # Listen to shared song
    VOTING = "voting"  # Vote on individual songs (like/dislike thumbs up/down)
    BANDWIDTH_CONTRIBUTION = "bandwidth_contribution"  # Serve content (LoRa)
    REFERRAL = "referral"  # Refer new users to platform
    ENGAGEMENT = "engagement"  # Community engagement (comments, playlists)


@dataclass
class WalletConversion:
    """
    User converts external coins (crypto, fiat on-ramp) to DCMX native tokens.
    
    Flow:
    1. User connects wallet (MetaMask, etc.)
    2. User has external coins (USDC, ETH, credit card)
    3. User converts to DCMX tokens via bridge/exchange
    4. User purchases NFTs with DCMX tokens
    5. Artist receives 100% of purchase price in DCMX tokens
    """
    conversion_id: str  # Unique conversion ID
    user_wallet: str  # User's blockchain wallet address
    timestamp: str  # When conversion happened
    
    # Input (What user is converting FROM)
    source_currency: str  # "USDC", "ETH", "USD" (fiat), etc.
    source_amount: float  # Amount user is converting
    source_chain: str  # "ethereum", "polygon", "solana", etc.
    
    # Output (What user receives)
    dcmx_tokens_received: float  # DCMX tokens user gets
    exchange_rate: float  # How many DCMX per source unit
    
    # Transaction Details
    transaction_hash: str  # Blockchain tx hash
    conversion_status: str  # "pending", "completed", "failed"
    completion_timestamp: Optional[str] = None
    
    # Fees & Conversions
    conversion_fee_percentage: float = 0.5  # 0.5% bridge fee
    actual_conversion_fee: float = field(init=False)
    
    def __post_init__(self):
        """Calculate actual conversion fee."""
        self.actual_conversion_fee = self.dcmx_tokens_received * (self.conversion_fee_percentage / 100)
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)


@dataclass
class ArtistFirstPayment:
    """
    Primary sale payment - 100% goes to artist.
    
    When a user purchases an NFT edition for the first time,
    the artist receives 100% of the purchase price.
    No platform fees, no intermediaries.
    """
    payment_id: str  # Unique payment ID
    song_content_hash: str
    song_title: str
    artist: str  # Rights holder
    artist_wallet: str  # Where to send payment
    
    # Purchase Details
    edition_number: int  # Edition purchased (1 of 100)
    max_editions: int  # Total editions available
    buyer_wallet: str  # Who purchased
    purchase_price_dcmx: float  # Price in DCMX tokens (converted from user's currency)
    purchase_price_usd_equivalent: float  # Equivalent USD value for reporting
    
    # Transaction Details
    transaction_hash: str  # NFT minting tx hash
    nft_contract_address: str
    token_id: int
    purchase_date: str  # ISO timestamp
    blockchain: str  # "polygon", "ethereum", "solana"
    
    # Watermark & DRM
    watermark_hash: str
    perceptual_fingerprint: str
    
    # Artist Gets 100% (calculated field)
    artist_payout_dcmx: float = field(init=False)
    artist_payout_status: str = "completed"
    artist_payout_timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Ensure artist gets 100%."""
        self.artist_payout_dcmx = self.purchase_price_dcmx
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)
    
    def get_summary(self) -> Dict:
        """Human-readable payment summary."""
        return {
            "song": self.song_title,
            "artist": self.artist,
            "edition": f"{self.edition_number}/{self.max_editions}",
            "buyer": self.buyer_wallet[:20] + "...",
            "price": f"{self.purchase_price_dcmx:.2f} DCMX (${self.purchase_price_usd_equivalent:.2f})",
            "artist_receives": f"{self.artist_payout_dcmx:.2f} DCMX (100%)",
            "date": self.purchase_date,
        }


@dataclass
class UserActivityReward:
    """
    Fair reward distribution based on user activities.
    
    Users earn rewards for:
    - Sharing songs with others
    - Listening to and engaging with music
    - Voting on platform governance
    - Contributing bandwidth (LoRa nodes)
    - Referring new users
    """
    reward_id: str  # Unique reward ID
    user_wallet: str  # User earning rewards
    activity_type: UserActivityType
    
    # Activity Details
    song_content_hash: str  # Which song (if applicable)
    activity_timestamp: str  # When activity happened
    activity_count: int  # How many (shares, votes, listens, etc.)
    
    # Reward Calculation
    base_reward_tokens: float
    multiplier: float = 1.0  # Activity-specific multiplier
    engagement_bonus: float = 0.0  # Bonus from community response
    
    # Status
    is_verified: bool = False  # ZK proof verified
    is_claimed: bool = False  # User claimed reward
    claim_timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Calculate total reward."""
        self.total_tokens = (self.base_reward_tokens * self.multiplier) + self.engagement_bonus
    
    @property
    def total_tokens(self) -> float:
        """Total tokens earned from this activity."""
        return (self.base_reward_tokens * self.multiplier) + self.engagement_bonus
    
    @total_tokens.setter
    def total_tokens(self, value: float):
        """Allow setting total (calculated property)."""
        pass
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)


class FairRewardSchedule:
    """
    Fair reward distribution based on user activities.
    
    Philosophy: Users who promote, vote, listen, and share energy
    deserve rewards, but artist maintains the majority value.
    """
    
    # Sharing Rewards (Promoting the platform)
    SHARING_BASE_REWARD = 0.5  # tokens per share
    SHARING_LISTENING_BONUS = 1.0  # additional token if recipient listens
    SHARING_PURCHASE_BONUS = 2.0  # additional tokens if recipient buys NFT
    SHARING_VOTE_BONUS = 0.5  # additional token if recipient votes
    
    # Listening Rewards (Engaging with music)
    LISTENING_BASE_REWARD = 1.0  # tokens per listen
    LISTENING_COMPLETION_90_100 = 1.0  # 90-100% completion bonus
    LISTENING_COMPLETION_75_89 = 0.5  # 75-89% completion bonus
    LISTENING_COMPLETION_50_74 = 0.25  # 50-74% completion bonus
    
    # Song Preference Voting Rewards (User likes/dislikes on individual songs)
    VOTING_BASE_REWARD = 5.0  # tokens per "like" vote on a song (5 DCMX per like)
    VOTING_PARTICIPATION_BONUS = 0.0  # no bonus (voting is song preference, not governance)
    VOTING_COMMUNITY_DECISION = 0.0  # no bonus (voting is song preference, not governance)
    
    # Bandwidth Rewards (Network contribution)
    BANDWIDTH_BASE_REWARD = 2.0  # tokens base
    BANDWIDTH_PER_100MB = 0.5  # per 100MB served
    BANDWIDTH_PER_LISTENER = 0.1  # per unique listener
    
    # Referral Rewards (Growth incentive)
    REFERRAL_NEW_USER = 1.0  # tokens per new user referred
    REFERRAL_FIRST_PURCHASE = 0.5  # tokens if referral makes first purchase
    REFERRAL_MONTHLY_ACTIVE = 0.2  # tokens if referral stays active
    
    # Engagement Rewards (Community participation)
    ENGAGEMENT_COMMENT = 0.1  # per meaningful comment
    ENGAGEMENT_PLAYLIST = 0.25  # per playlist created
    ENGAGEMENT_COMMUNITY_FAVORITE = 0.5  # if song marked as favorite by 10+ users


class ArtistFirstEconomics:
    """
    Artist-first economic model for DCMX music NFTs.
    
    Key principles:
    1. Artist gets 100% on primary sale
    2. Users earn fair rewards for promotion and engagement
    3. Artist still earns majority on secondary sales
    4. Wallet conversion is frictionless
    5. Transparent, auditable reward distribution
    """
    
    def __init__(self):
        """Initialize artist-first economics system."""
        self.conversions: Dict[str, WalletConversion] = {}
        self.artist_payments: Dict[str, ArtistFirstPayment] = {}
        self.user_rewards: Dict[str, UserActivityReward] = {}
        self.user_wallets: Dict[str, Dict] = {}  # user_id -> wallet info
        
        logger.info("ArtistFirstEconomics initialized")
    
    # ==================== WALLET CONVERSION SYSTEM ====================
    
    def register_user_wallet(
        self,
        user_id: str,
        wallet_address: str,
        wallet_type: str = "ethereum"  # metamask, walletconnect, etc.
    ) -> Dict:
        """
        Register user's blockchain wallet.
        
        User connects their wallet to enable:
        - Currency conversion to DCMX
        - NFT purchase with DCMX tokens
        - Reward claim and distribution
        
        Args:
            user_id: Application user ID
            wallet_address: Blockchain wallet address
            wallet_type: Type of wallet (metamask, walletconnect, etc.)
            
        Returns:
            Wallet registration info
        """
        self.user_wallets[user_id] = {
            "wallet_address": wallet_address,
            "wallet_type": wallet_type,
            "registration_timestamp": datetime.utcnow().isoformat(),
            "conversions": [],
            "nft_purchases": [],
            "rewards_earned": [],
            "dcmx_balance": 0.0,  # DCMX tokens held
        }
        
        logger.info(f"Wallet registered: {user_id} → {wallet_address[:20]}...")
        
        return self.user_wallets[user_id]
    
    def convert_to_dcmx(
        self,
        user_id: str,
        source_currency: str,
        source_amount: float,
        exchange_rate: float,
        source_chain: str = "ethereum"
    ) -> WalletConversion:
        """
        Convert external currency to DCMX native tokens.
        
        User can convert:
        - Stablecoins (USDC, USDT, DAI)
        - Major cryptos (ETH, BTC, SOL)
        - Fiat via on-ramp (credit card, bank transfer)
        
        Bridge handles:
        - Cross-chain swaps if needed
        - Price conversion at market rate
        - Minimal fees (0.5%)
        
        Args:
            user_id: User converting currency
            source_currency: Currency being converted (USDC, ETH, USD, etc.)
            source_amount: Amount being converted
            exchange_rate: How many DCMX per source unit
            source_chain: Which blockchain the source is on
            
        Returns:
            WalletConversion object with conversion details
        """
        if user_id not in self.user_wallets:
            raise ValueError(f"User wallet not registered: {user_id}")
        
        conversion_id = f"conv_{user_id}_{datetime.utcnow().timestamp()}"
        
        # Calculate tokens user receives (after fee)
        dcmx_gross = source_amount * exchange_rate
        fee_percentage = 0.5  # 0.5% bridge fee
        fee_amount = dcmx_gross * (fee_percentage / 100)
        dcmx_net = dcmx_gross - fee_amount
        
        conversion = WalletConversion(
            conversion_id=conversion_id,
            user_wallet=self.user_wallets[user_id]["wallet_address"],
            timestamp=datetime.utcnow().isoformat(),
            source_currency=source_currency,
            source_amount=source_amount,
            source_chain=source_chain,
            dcmx_tokens_received=dcmx_net,
            exchange_rate=exchange_rate,
            transaction_hash=f"0x{conversion_id[:60]}",
            conversion_status="completed"
        )
        
        self.conversions[conversion_id] = conversion
        
        # Update user's DCMX balance
        self.user_wallets[user_id]["dcmx_balance"] += dcmx_net
        self.user_wallets[user_id]["conversions"].append(conversion_id)
        
        logger.info(
            f"Currency conversion: {user_id} converted {source_amount} {source_currency} "
            f"→ {dcmx_net:.2f} DCMX (fee: {fee_amount:.2f} DCMX)"
        )
        
        return conversion
    
    def get_user_dcmx_balance(self, user_id: str) -> float:
        """Get user's DCMX token balance."""
        if user_id not in self.user_wallets:
            return 0.0
        return self.user_wallets[user_id]["dcmx_balance"]
    
    # ==================== PRIMARY SALES (Artist Gets 100%) ====================
    
    def process_nft_purchase(
        self,
        user_id: str,
        song_title: str,
        artist: str,
        artist_wallet: str,
        content_hash: str,
        edition_number: int,
        max_editions: int,
        price_dcmx: float,
        price_usd_equivalent: float,
        watermark_hash: str,
        perceptual_fingerprint: str,
        nft_contract_address: str,
        token_id: int
    ) -> ArtistFirstPayment:
        """
        Process NFT purchase - Artist receives 100%.
        
        When user purchases an NFT:
        1. User spends DCMX tokens (converted from their currency)
        2. Artist receives 100% of purchase price immediately
        3. No intermediaries, no platform fees on primary sale
        4. NFT minted and transferred to user's wallet
        5. Artist can withdraw DCMX or convert back to external currency
        
        Args:
            user_id: User making purchase
            song_title: Name of song
            artist: Artist name
            artist_wallet: Artist's blockchain wallet
            content_hash: SHA256 of audio
            edition_number: Which edition (1-100)
            max_editions: Total editions available
            price_dcmx: Purchase price in DCMX tokens
            price_usd_equivalent: Equivalent USD value
            watermark_hash: Audio watermark proof
            perceptual_fingerprint: Content fingerprint
            nft_contract_address: ERC-721 contract
            token_id: NFT token ID
            
        Returns:
            ArtistFirstPayment (artist receives 100%)
        """
        if user_id not in self.user_wallets:
            raise ValueError(f"User wallet not registered: {user_id}")
        
        # Check user has sufficient DCMX balance
        user_balance = self.get_user_dcmx_balance(user_id)
        if user_balance < price_dcmx:
            raise ValueError(
                f"Insufficient DCMX balance: {user_balance:.2f} < {price_dcmx:.2f}"
            )
        
        payment_id = f"primary_{content_hash}_{edition_number}_{datetime.utcnow().timestamp()}"
        
        payment = ArtistFirstPayment(
            payment_id=payment_id,
            song_content_hash=content_hash,
            song_title=song_title,
            artist=artist,
            artist_wallet=artist_wallet,
            edition_number=edition_number,
            max_editions=max_editions,
            buyer_wallet=self.user_wallets[user_id]["wallet_address"],
            purchase_price_dcmx=price_dcmx,
            purchase_price_usd_equivalent=price_usd_equivalent,
            transaction_hash=f"0x{payment_id[:60]}",
            nft_contract_address=nft_contract_address,
            token_id=token_id,
            purchase_date=datetime.utcnow().isoformat(),
            blockchain="polygon",  # Configurable
            watermark_hash=watermark_hash,
            perceptual_fingerprint=perceptual_fingerprint,
            artist_payout_timestamp=datetime.utcnow().isoformat(),
        )
        
        self.artist_payments[payment_id] = payment
        
        # Deduct from user's DCMX balance
        self.user_wallets[user_id]["dcmx_balance"] -= price_dcmx
        self.user_wallets[user_id]["nft_purchases"].append(payment_id)
        
        logger.info(
            f"NFT Purchase (Artist 100%): {user_id} purchased Edition {edition_number} "
            f"of '{song_title}' for {price_dcmx:.2f} DCMX → "
            f"{artist} receives {payment.artist_payout_dcmx:.2f} DCMX"
        )
        
        return payment
    
    def get_artist_total_earnings(self, artist: str) -> float:
        """Get total earnings for artist from all primary sales."""
        total = sum(
            p.artist_payout_dcmx for p in self.artist_payments.values()
            if p.artist == artist and p.artist_payout_status == "completed"
        )
        return total
    
    # ==================== USER ACTIVITY REWARDS ====================
    
    def record_sharing_activity(
        self,
        user_wallet: str,
        song_content_hash: str,
        shared_with_wallet: str,
        activity_count: int = 1
    ) -> UserActivityReward:
        """
        Record user sharing song (promotion activity).
        
        User earns:
        - 0.5 tokens per share
        - +1.0 token if recipient listens
        - +2.0 tokens if recipient purchases NFT
        - +0.5 tokens if recipient votes
        
        Args:
            user_wallet: User sharing
            song_content_hash: Which song
            shared_with_wallet: Recipient
            activity_count: Number of shares
            
        Returns:
            UserActivityReward
        """
        reward_id = f"share_{user_wallet}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        base_reward = FairRewardSchedule.SHARING_BASE_REWARD * activity_count
        
        reward = UserActivityReward(
            reward_id=reward_id,
            user_wallet=user_wallet,
            activity_type=UserActivityType.SHARING,
            song_content_hash=song_content_hash,
            activity_timestamp=datetime.utcnow().isoformat(),
            activity_count=activity_count,
            base_reward_tokens=base_reward,
            multiplier=1.0
        )
        
        self.user_rewards[reward_id] = reward
        
        logger.info(
            f"Sharing activity recorded: {user_wallet[:20]}... shared {activity_count} time(s), "
            f"earning {reward.total_tokens:.2f} tokens"
        )
        
        return reward
    
    def record_listening_activity(
        self,
        user_wallet: str,
        song_content_hash: str,
        listen_duration_seconds: int,
        completion_percentage: float
    ) -> UserActivityReward:
        """
        Record user listening to song (engagement activity).
        
        User earns:
        - 1.0 token base per listen
        - +1.0 token for 90-100% completion
        - +0.5 tokens for 75-89% completion
        - +0.25 tokens for 50-74% completion
        
        Args:
            user_wallet: User listening
            song_content_hash: Which song
            listen_duration_seconds: How long they listened
            completion_percentage: % of song heard (0-100)
            
        Returns:
            UserActivityReward
        """
        reward_id = f"listen_{user_wallet}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        base_reward = FairRewardSchedule.LISTENING_BASE_REWARD
        
        # Completion bonus
        completion_bonus = 0.0
        if completion_percentage >= 90:
            completion_bonus = FairRewardSchedule.LISTENING_COMPLETION_90_100
        elif completion_percentage >= 75:
            completion_bonus = FairRewardSchedule.LISTENING_COMPLETION_75_89
        elif completion_percentage >= 50:
            completion_bonus = FairRewardSchedule.LISTENING_COMPLETION_50_74
        
        reward = UserActivityReward(
            reward_id=reward_id,
            user_wallet=user_wallet,
            activity_type=UserActivityType.LISTENING,
            song_content_hash=song_content_hash,
            activity_timestamp=datetime.utcnow().isoformat(),
            activity_count=1,
            base_reward_tokens=base_reward,
            engagement_bonus=completion_bonus
        )
        
        self.user_rewards[reward_id] = reward
        
        logger.info(
            f"Listening activity recorded: {user_wallet[:20]}... listened {completion_percentage:.0f}%, "
            f"earning {reward.total_tokens:.2f} tokens"
        )
        
        return reward
    
    def record_song_preference_vote(
        self,
        user_wallet: str,
        song_content_hash: str,
        artist_wallet: str,
        preference: str = "like"  # "like" or "dislike"
    ) -> UserActivityReward:
        """
        Record user song preference voting (likes/dislikes on individual songs).
        
        Users vote on whether they like/dislike SONGS (not governance decisions).
        
        User earns:
        - 5.0 tokens per "like" vote on a song
        - 0 tokens for "dislike" vote (but counts for analytics)
        
        This incentivizes genuine engagement with music while:
        - Giving artists feedback on song reception
        - Helping platform recommend better songs
        - Preventing governance gaming
        
        Args:
            user_wallet: User expressing preference
            song_content_hash: Which song they're voting on
            artist_wallet: Song artist
            preference: "like" (thumbs up) or "dislike" (thumbs down)
            
        Returns:
            UserActivityReward with tokens earned from like vote
        """
        reward_id = f"song_vote_{user_wallet}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        # Only reward "like" votes with tokens
        if preference.lower() == "like":
            base_reward = FairRewardSchedule.VOTING_BASE_REWARD  # 5.0 tokens
            bonus = 0.0
        else:  # dislike
            base_reward = 0.0
            bonus = 0.0
        
        reward = UserActivityReward(
            reward_id=reward_id,
            user_wallet=user_wallet,
            activity_type=UserActivityType.VOTING,
            song_content_hash=song_content_hash,  # Song-specific voting
            activity_timestamp=datetime.utcnow().isoformat(),
            activity_count=1,
            base_reward_tokens=base_reward,
            engagement_bonus=bonus
        )
        
        self.user_rewards[reward_id] = reward
        
        logger.info(
            f"Song preference vote recorded: {user_wallet[:20]}... voted {preference} on "
            f"song {song_content_hash[:16]}... by {artist_wallet[:20]}..., "
            f"earning {reward.total_tokens:.2f} tokens"
        )
        
        return reward
    
    def record_skip_activity(
        self,
        user_wallet: str,
        song_content_hash: str,
        artist_wallet: str,
        completion_percentage: float = 0.0
    ) -> UserActivityReward:
        """
        Record user skipping a song and apply skip charge.
        
        When a user skips before minimum listen threshold (25%),
        they are charged a skip fee to disincentivize gaming:
        
        - Skip charge: 1.0 DCMX token
        - Goes to: Platform treasury (not artist)
        - Purpose: Incentivizes genuine listening
        
        Args:
            user_wallet: User who skipped
            song_content_hash: Which song was skipped
            artist_wallet: Song artist
            completion_percentage: How much was listened (triggers charge if <25%)
            
        Returns:
            UserActivityReward with negative tokens (charge applied)
        """
        reward_id = f"skip_charge_{user_wallet}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        # Only charge if skipped early (before 25% completion)
        skip_threshold = 0.25
        if completion_percentage < skip_threshold:
            skip_charge = 1.0  # 1 DCMX token charge
        else:
            skip_charge = 0.0  # No charge if listened to minimum
        
        reward = UserActivityReward(
            reward_id=reward_id,
            user_wallet=user_wallet,
            activity_type=UserActivityType.SHARING,  # Reuse activity type for tracking
            song_content_hash=song_content_hash,
            activity_timestamp=datetime.utcnow().isoformat(),
            activity_count=1,
            base_reward_tokens=-skip_charge,  # Negative = charge to user
            engagement_bonus=0.0
        )
        
        self.user_rewards[reward_id] = reward
        
        if skip_charge > 0:
            logger.info(
                f"Skip charge applied: {user_wallet[:20]}... skipped after {completion_percentage*100:.0f}% "
                f"completion on {song_content_hash[:16]}..., charged {skip_charge:.2f} tokens"
            )
        
        return reward
    
    def record_bandwidth_contribution(
        self,
        node_id: str,
        song_content_hash: str,
        bytes_served: int,
        listeners_served: int
    ) -> UserActivityReward:
        """
        Record LoRa node bandwidth contribution (network service).
        
        Node earns:
        - 2.0 tokens base
        - +0.5 tokens per 100MB served
        - +0.1 tokens per unique listener reached
        
        Args:
            node_id: LoRa node providing bandwidth
            song_content_hash: Which content served
            bytes_served: Bytes transmitted
            listeners_served: Number of unique listeners
            
        Returns:
            UserActivityReward
        """
        reward_id = f"bandwidth_{node_id}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        base_reward = FairRewardSchedule.BANDWIDTH_BASE_REWARD
        
        # Per 100MB bonus
        bandwidth_bonus = (bytes_served / (100 * 1024 * 1024)) * FairRewardSchedule.BANDWIDTH_PER_100MB
        
        # Per listener bonus
        listener_bonus = listeners_served * FairRewardSchedule.BANDWIDTH_PER_LISTENER
        
        total_bonus = bandwidth_bonus + listener_bonus
        
        reward = UserActivityReward(
            reward_id=reward_id,
            user_wallet=node_id,  # Node is identified by its ID
            activity_type=UserActivityType.BANDWIDTH_CONTRIBUTION,
            song_content_hash=song_content_hash,
            activity_timestamp=datetime.utcnow().isoformat(),
            activity_count=1,
            base_reward_tokens=base_reward,
            engagement_bonus=total_bonus
        )
        
        self.user_rewards[reward_id] = reward
        
        logger.info(
            f"Bandwidth contribution recorded: {node_id[:20]}... served {bytes_served / (1024**2):.1f}MB "
            f"to {listeners_served} listeners, earning {reward.total_tokens:.2f} tokens"
        )
        
        return reward
    
    def record_referral_activity(
        self,
        referrer_wallet: str,
        referred_wallet: str,
        referred_made_purchase: bool = False
    ) -> UserActivityReward:
        """
        Record user referring new user to platform (growth incentive).
        
        Referrer earns:
        - 1.0 token per new user referred
        - +0.5 tokens if referred user makes first purchase
        - +0.2 tokens per month if referred user stays active
        
        Args:
            referrer_wallet: User making referral
            referred_wallet: New user referred
            referred_made_purchase: Did referred user buy NFT?
            
        Returns:
            UserActivityReward
        """
        reward_id = f"referral_{referrer_wallet}_{referred_wallet}_{datetime.utcnow().timestamp()}"
        
        base_reward = FairRewardSchedule.REFERRAL_NEW_USER
        
        bonus = 0.0
        if referred_made_purchase:
            bonus = FairRewardSchedule.REFERRAL_FIRST_PURCHASE
        
        reward = UserActivityReward(
            reward_id=reward_id,
            user_wallet=referrer_wallet,
            activity_type=UserActivityType.REFERRAL,
            song_content_hash="",  # Not song-specific
            activity_timestamp=datetime.utcnow().isoformat(),
            activity_count=1,
            base_reward_tokens=base_reward,
            engagement_bonus=bonus
        )
        
        self.user_rewards[reward_id] = reward
        
        logger.info(
            f"Referral activity recorded: {referrer_wallet[:20]}... referred {referred_wallet[:20]}..., "
            f"earning {reward.total_tokens:.2f} tokens"
        )
        
        return reward
    
    def get_user_total_rewards(self, user_wallet: str) -> Dict:
        """
        Get total rewards earned by user across all activities.
        
        Returns breakdown by activity type.
        """
        user_rewards = [
            r for r in self.user_rewards.values()
            if r.user_wallet == user_wallet
        ]
        
        breakdown = {}
        for activity_type in UserActivityType:
            activities = [r for r in user_rewards if r.activity_type == activity_type]
            breakdown[activity_type.value] = {
                "count": len(activities),
                "total_tokens": sum(r.total_tokens for r in activities)
            }
        
        return {
            "user_wallet": user_wallet[:20] + "...",
            "total_activities": len(user_rewards),
            "total_tokens_earned": sum(r.total_tokens for r in user_rewards),
            "breakdown_by_type": breakdown
        }
    
    # ==================== SECONDARY MARKET (Artist Majority) ====================
    
    def process_secondary_sale(
        self,
        seller_wallet: str,
        buyer_wallet: str,
        song_content_hash: str,
        edition_number: int,
        artist: str,
        artist_wallet: str,
        resale_price_dcmx: float
    ) -> Dict:
        """
        Process NFT resale on secondary market.
        
        Unlike primary sale, secondary sale is split:
        - Artist: 80% (still majority - ongoing royalties)
        - Seller: 15% (incentive to sell)
        - Platform: 5% (operational costs)
        
        This ensures:
        1. Artist continues earning from all resales
        2. Seller gets meaningful return
        3. Platform sustainable
        4. Artist still maintains control & majority value
        
        Args:
            seller_wallet: Current NFT owner selling
            buyer_wallet: New owner buying
            song_content_hash: Which song's NFT
            edition_number: Which edition
            artist: Original artist
            artist_wallet: Artist's wallet
            resale_price_dcmx: Resale price in DCMX
            
        Returns:
            Dict with payment breakdown
        """
        artist_payout = resale_price_dcmx * 0.80  # 80%
        seller_payout = resale_price_dcmx * 0.15  # 15%
        platform_payout = resale_price_dcmx * 0.05  # 5%
        
        logger.info(
            f"Secondary sale: {song_content_hash[:16]}... Edition {edition_number} "
            f"→ Artist: {artist_payout:.2f} DCMX (80%) | "
            f"Seller: {seller_payout:.2f} DCMX (15%) | "
            f"Platform: {platform_payout:.2f} DCMX (5%)"
        )
        
        return {
            "resale_price": resale_price_dcmx,
            "artist_payout": artist_payout,
            "seller_payout": seller_payout,
            "platform_payout": platform_payout,
        }
    
    # ==================== REPORTING ====================
    
    def generate_artist_report(self, artist: str) -> Dict:
        """Generate earnings report for artist."""
        primary_earnings = self.get_artist_total_earnings(artist)
        
        # Count NFTs sold by this artist
        artist_payments = [p for p in self.artist_payments.values() if p.artist == artist]
        editions_sold = len(artist_payments)
        avg_price = (
            sum(p.purchase_price_dcmx for p in artist_payments) / editions_sold
            if artist_payments else 0
        )
        
        return {
            "artist": artist,
            "total_earnings_dcmx": primary_earnings,
            "editions_sold": editions_sold,
            "average_price_dcmx": avg_price,
            "payment_details": [
                {
                    "song": p.song_title,
                    "edition": f"{p.edition_number}/{p.max_editions}",
                    "price": p.purchase_price_dcmx,
                    "buyer": p.buyer_wallet[:20] + "...",
                    "date": p.purchase_date
                }
                for p in artist_payments
            ]
        }
    
    def generate_user_activity_report(self, user_wallet: str) -> Dict:
        """Generate activity and earnings report for user."""
        user_info = self.user_wallets.get(user_wallet, {})
        
        return {
            "user_wallet": user_wallet[:20] + "...",
            "dcmx_balance": user_info.get("dcmx_balance", 0.0),
            "conversions_made": len(user_info.get("conversions", [])),
            "nfts_purchased": len(user_info.get("nft_purchases", [])),
            "rewards_earned": self.get_user_total_rewards(user_wallet),
            "registration_date": user_info.get("registration_timestamp", "N/A"),
        }
    
    def generate_platform_statistics(self) -> Dict:
        """Generate overall platform statistics."""
        return {
            "total_conversions": len(self.conversions),
            "total_conversion_volume_dcmx": sum(
                c.dcmx_tokens_received for c in self.conversions.values()
            ),
            "total_nft_sales": len(self.artist_payments),
            "total_artist_payouts": sum(
                p.artist_payout_dcmx for p in self.artist_payments.values()
            ),
            "total_user_rewards": sum(
                r.total_tokens for r in self.user_rewards.values()
            ),
            "registered_wallets": len(self.user_wallets),
            "total_activity_rewards": {
                activity_type.value: len([
                    r for r in self.user_rewards.values()
                    if r.activity_type == activity_type
                ])
                for activity_type in UserActivityType
            }
        }
