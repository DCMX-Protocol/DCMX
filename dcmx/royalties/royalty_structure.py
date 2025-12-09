"""
DCMX Royalty and Rewards Payment Structure.

Implements:
- NFT Certificate system (unique ownership tokens with edition numbers)
- Token rewards for sharing, listening, and bandwidth usage
- Royalty distribution (artist + platform + node operators)
- Secondary market royalty enforcement
- Reward claim mechanism with zero-knowledge verification
"""

import logging
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """Types of rewards nodes can earn."""
    SHARING = "sharing"  # Share track with other wallets
    LISTENING = "listening"  # Users listen to shared track
    BANDWIDTH = "bandwidth"  # Serving content (data transfer)
    UPTIME = "uptime"  # Maintaining availability
    REFERRAL = "referral"  # Refer new users
    PLATFORM_CONTRIBUTION = "platform_contribution"  # Community contributions


class RoyaltyRecipient(Enum):
    """Who receives royalties from sales."""
    ARTIST = "artist"  # Original rights holder (you)
    PLATFORM = "platform"  # DCMX platform fees
    NODE_OPERATOR = "node_operator"  # LoRa node operators who served content
    EARLY_BUYER = "early_buyer"  # Buyers of early editions (optional)


@dataclass
class NFTCertificate:
    """
    NFT Certificate for purchased song edition.
    
    Represents ownership of a specific edition number of a song.
    Enables secondary market sales with locked royalties.
    """
    certificate_id: str  # Unique ID for this certificate (UUID)
    song_content_hash: str  # SHA256 hash of original audio
    song_title: str
    artist: str  # Rights holder (you)
    
    # Edition Information
    edition_number: int  # This is edition #5 of 100
    max_editions: int  # Total copies available (100)
    
    # Ownership
    owner_wallet: str  # Current owner's blockchain address
    original_buyer_wallet: str  # First purchaser (for secondary sales)
    
    # Smart Contract
    nft_contract_address: str  # Ethereum/Polygon contract
    token_id: int  # NFT token ID (for ERC-721)
    blockchain: str  # "ethereum" | "polygon" | "solana"
    
    # Metadata
    purchase_date: str  # ISO timestamp of first purchase
    purchase_price_usd: float  # Original sale price
    purchase_price_dcmx_tokens: int  # Token cost at time of purchase
    
    # Watermark & DRM
    watermark_hash: str  # Proof of audio watermarking
    perceptual_fingerprint: str  # Content fingerprint for duplicate detection
    
    # Rights & Licensing
    personal_use_only: bool = True  # Can only use, not resell
    commercial_license: bool = False  # Commercial distribution rights
    license_expiry: Optional[str] = None  # When commercial license expires
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)
    
    def get_certificate_metadata(self) -> Dict:
        """Get human-readable certificate metadata."""
        return {
            "certificate_id": self.certificate_id,
            "song": f"{self.song_title} by {self.artist}",
            "edition": f"{self.edition_number} of {self.max_editions}",
            "owner": self.owner_wallet[:10] + "...",
            "purchased": self.purchase_date,
            "price_paid": f"${self.purchase_price_usd:.2f}",
            "nft_address": f"{self.nft_contract_address[:10]}...",
            "token_id": self.token_id,
        }


@dataclass
class SharingReward:
    """Reward earned by user for sharing song with others."""
    reward_id: str  # Unique reward ID
    sharer_wallet: str  # User who shared the song
    song_content_hash: str  # Which song was shared
    shared_with_wallet: str  # Who received the share
    timestamp: str  # When share happened
    
    # Reward Amount
    base_reward_tokens: int = 1  # Base: 1 token per share
    listening_multiplier: float = 1.0  # 1.5x if recipient listens
    engagement_bonus: float = 0.0  # Bonus if recipient purchases
    
    @property
    def total_reward(self) -> float:
        """Calculate total reward including multipliers."""
        return self.base_reward_tokens * self.listening_multiplier + self.engagement_bonus
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        d = asdict(self)
        d["total_reward"] = self.total_reward
        return d


@dataclass
class ListeningReward:
    """Reward earned when user listens to shared song."""
    reward_id: str  # Unique reward ID
    listener_wallet: str  # User who listened
    song_content_hash: str  # Which song was listened to
    sharer_wallet: str  # Original sharer (gets referral bonus)
    timestamp: str  # When listening happened
    
    # Listening Session Details
    listen_duration_seconds: int  # How long they listened
    completion_percentage: float  # % of song completed (0-100)
    
    # Reward Amount
    base_reward_tokens: int = 2  # Base: 2 tokens per complete listen
    
    @property
    def completion_bonus(self) -> float:
        """Bonus based on how much of song was listened."""
        if self.completion_percentage >= 90:
            return 2.0  # 2 extra tokens for full listen
        elif self.completion_percentage >= 75:
            return 1.0  # 1 extra token for 75%+
        elif self.completion_percentage >= 50:
            return 0.5  # 0.5 tokens for half listen
        else:
            return 0.0  # No bonus if barely listened
    
    @property
    def total_reward(self) -> float:
        """Calculate total listening reward."""
        return self.base_reward_tokens + self.completion_bonus
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        d = asdict(self)
        d["completion_bonus"] = self.completion_bonus
        d["total_reward"] = self.total_reward
        return d


@dataclass
class BandwidthReward:
    """Reward earned by LoRa node for serving content."""
    reward_id: str  # Unique reward ID
    node_id: str  # LoRa node that served content
    song_content_hash: str  # Which content was served
    
    # Bandwidth Details
    bytes_served: int  # Bytes transmitted
    listeners_served: int  # Number of unique listeners
    transmission_time_seconds: int  # How long to serve content
    
    # Reward Amount (based on contribution)
    base_reward_tokens: int = 5  # Base: 5 tokens per 100MB served
    
    @property
    def bandwidth_bonus(self) -> float:
        """Bonus based on bytes served."""
        # 1 token per 100MB served
        return (self.bytes_served / (100 * 1024 * 1024)) * 1.0
    
    @property
    def listener_bonus(self) -> float:
        """Bonus based on number of listeners."""
        # 0.5 tokens per unique listener
        return self.listeners_served * 0.5
    
    @property
    def total_reward(self) -> float:
        """Calculate total bandwidth reward."""
        return self.base_reward_tokens + self.bandwidth_bonus + self.listener_bonus
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        d = asdict(self)
        d["bandwidth_bonus"] = self.bandwidth_bonus
        d["listener_bonus"] = self.listener_bonus
        d["total_reward"] = self.total_reward
        return d


@dataclass
class RoyaltyPayment:
    """Payment distribution after NFT sale or secondary market transaction."""
    payment_id: str  # Unique payment ID
    song_content_hash: str
    song_title: str
    artist: str
    
    # Transaction Details
    transaction_hash: str  # Blockchain tx hash
    sale_price_usd: float  # Sale price in USD
    sale_price_dcmx_tokens: int  # Sale price in DCMX tokens
    sale_date: str  # ISO timestamp
    
    # Sale Type
    is_primary_sale: bool  # True = first purchase; False = secondary market
    primary_buyer_wallet: Optional[str] = None  # Who bought in primary sale
    secondary_seller_wallet: Optional[str] = None  # Who is selling in secondary
    secondary_buyer_wallet: Optional[str] = None  # Who is buying in secondary
    
    # Royalty Split (adds to 100%)
    artist_percentage: float = 70.0  # Artist gets 70%
    platform_percentage: float = 15.0  # Platform gets 15%
    node_operator_percentage: float = 10.0  # LoRa operators get 10%
    early_buyer_percentage: float = 5.0  # Early edition bonus (optional)
    
    # Calculated Amounts
    artist_payout_usd: float = field(init=False)
    platform_payout_usd: float = field(init=False)
    node_operator_payout_usd: float = field(init=False)
    early_buyer_payout_usd: float = field(init=False)
    
    def __post_init__(self):
        """Calculate payout amounts."""
        self.artist_payout_usd = self.sale_price_usd * (self.artist_percentage / 100)
        self.platform_payout_usd = self.sale_price_usd * (self.platform_percentage / 100)
        self.node_operator_payout_usd = self.sale_price_usd * (self.node_operator_percentage / 100)
        self.early_buyer_payout_usd = self.sale_price_usd * (self.early_buyer_percentage / 100)
    
    def get_payout_breakdown(self) -> Dict[RoyaltyRecipient, Tuple[str, float, float]]:
        """
        Get breakdown of who receives what.
        
        Returns: Dict mapping recipient type to (wallet, amount_usd, percentage)
        """
        # Note: Wallets would be retrieved from blockchain in real implementation
        return {
            RoyaltyRecipient.ARTIST: ("artist_wallet_address", self.artist_payout_usd, self.artist_percentage),
            RoyaltyRecipient.PLATFORM: ("platform_wallet_address", self.platform_payout_usd, self.platform_percentage),
            RoyaltyRecipient.NODE_OPERATOR: ("node_operator_pool", self.node_operator_payout_usd, self.node_operator_percentage),
            RoyaltyRecipient.EARLY_BUYER: ("early_buyer_address", self.early_buyer_payout_usd, self.early_buyer_percentage),
        }
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)


@dataclass
class RewardClaim:
    """
    Claim for earned rewards (requires ZK proof verification).
    
    User submits proof of activity (sharing, listening, or bandwidth)
    and claims tokens. Verifiers validate the claim before tokens are minted.
    """
    claim_id: str  # Unique claim ID
    claimant_wallet: str  # Wallet claiming rewards
    claim_type: RewardType  # Type of activity (sharing, listening, bandwidth)
    
    # Claim Details
    song_content_hash: str  # Which song earned rewards
    activity_count: int  # Number of shares/listens/bytes served
    timestamp: str  # When claim submitted
    
    # Evidence (ZK Proof)
    proof_type: str  # "sharing_proof", "listening_proof", "bandwidth_proof"
    proof_data: Dict = field(default_factory=dict)  # ZK proof attachment
    proof_verified: bool = False
    verification_timestamp: Optional[str] = None
    
    # Reward Calculation
    total_tokens_claimed: float = 0.0
    total_tokens_verified: float = 0.0  # After verification
    
    # Payment Status
    is_approved: bool = False
    approval_timestamp: Optional[str] = None
    tokens_minted: bool = False
    mint_transaction_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)


class RoyaltyPaymentStructure:
    """
    Manages royalty and reward payments for the DCMX platform.
    
    Key responsibilities:
    1. Issue NFT certificates when users purchase songs
    2. Track and distribute sharing/listening rewards
    3. Calculate and distribute royalties on NFT sales
    4. Manage reward claims with ZK proof verification
    5. Interface with blockchain for token minting
    """
    
    def __init__(self):
        """Initialize royalty system."""
        self.certificates: Dict[str, NFTCertificate] = {}
        self.reward_claims: Dict[str, RewardClaim] = {}
        self.royalty_payments: Dict[str, RoyaltyPayment] = {}
        self.sharing_rewards: Dict[str, SharingReward] = {}
        self.listening_rewards: Dict[str, ListeningReward] = {}
        self.bandwidth_rewards: Dict[str, BandwidthReward] = {}
        
        logger.info("RoyaltyPaymentStructure initialized")
    
    # ==================== NFT CERTIFICATE SYSTEM ====================
    
    def issue_nft_certificate(
        self,
        song_title: str,
        artist: str,
        content_hash: str,
        edition_number: int,
        max_editions: int,
        buyer_wallet: str,
        purchase_price_usd: float,
        purchase_price_tokens: int,
        watermark_hash: str,
        perceptual_fingerprint: str,
        nft_contract_address: str,
        token_id: int,
        blockchain: str = "polygon"
    ) -> NFTCertificate:
        """
        Issue NFT certificate when user purchases a song edition.
        
        Each purchase gives unique certificate with edition number.
        Certificate proves ownership and enables secondary market sales.
        
        Args:
            song_title: Name of song
            artist: Rights holder (artist)
            content_hash: SHA256 hash of audio
            edition_number: Which edition this is (1-100)
            max_editions: Total editions available
            buyer_wallet: Buyer's blockchain wallet
            purchase_price_usd: USD cost
            purchase_price_tokens: DCMX token cost
            watermark_hash: Proof of audio watermarking
            perceptual_fingerprint: Content fingerprint
            nft_contract_address: ERC-721 contract address
            token_id: NFT token ID
            blockchain: "ethereum" or "polygon"
            
        Returns:
            NFTCertificate object
        """
        certificate_id = f"cert_{content_hash}_{edition_number}_{datetime.utcnow().timestamp()}"
        
        certificate = NFTCertificate(
            certificate_id=certificate_id,
            song_content_hash=content_hash,
            song_title=song_title,
            artist=artist,
            edition_number=edition_number,
            max_editions=max_editions,
            owner_wallet=buyer_wallet,
            original_buyer_wallet=buyer_wallet,
            nft_contract_address=nft_contract_address,
            token_id=token_id,
            blockchain=blockchain,
            purchase_date=datetime.utcnow().isoformat(),
            purchase_price_usd=purchase_price_usd,
            purchase_price_dcmx_tokens=purchase_price_tokens,
            watermark_hash=watermark_hash,
            perceptual_fingerprint=perceptual_fingerprint,
        )
        
        self.certificates[certificate_id] = certificate
        
        logger.info(
            f"Issued NFT certificate: {song_title} Edition {edition_number}/{max_editions} "
            f"to {buyer_wallet[:10]}... (${purchase_price_usd})"
        )
        
        return certificate
    
    def get_certificate(self, certificate_id: str) -> Optional[NFTCertificate]:
        """Get NFT certificate by ID."""
        return self.certificates.get(certificate_id)
    
    def list_user_certificates(self, wallet_address: str) -> List[NFTCertificate]:
        """Get all certificates owned by user."""
        return [
            cert for cert in self.certificates.values()
            if cert.owner_wallet == wallet_address
        ]
    
    # ==================== SHARING REWARDS ====================
    
    def record_sharing_event(
        self,
        sharer_wallet: str,
        song_content_hash: str,
        shared_with_wallet: str,
        base_reward: int = 1
    ) -> SharingReward:
        """
        Record when user shares song with another wallet.
        
        User earns tokens for sharing. Gets bonus if recipient listens.
        
        Args:
            sharer_wallet: Wallet of user sharing song
            song_content_hash: Which song is shared
            shared_with_wallet: Recipient wallet
            base_reward: Base tokens for sharing (default 1)
            
        Returns:
            SharingReward object
        """
        reward_id = f"share_{sharer_wallet}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        reward = SharingReward(
            reward_id=reward_id,
            sharer_wallet=sharer_wallet,
            song_content_hash=song_content_hash,
            shared_with_wallet=shared_with_wallet,
            timestamp=datetime.utcnow().isoformat(),
            base_reward_tokens=base_reward
        )
        
        self.sharing_rewards[reward_id] = reward
        
        logger.info(
            f"Sharing event recorded: {sharer_wallet[:10]}... → {shared_with_wallet[:10]}... "
            f"({reward.base_reward_tokens} tokens)"
        )
        
        return reward
    
    def apply_listening_multiplier(
        self,
        sharing_reward_id: str,
        multiplier: float = 1.5
    ) -> Optional[SharingReward]:
        """
        Apply multiplier to sharing reward if recipient listens.
        
        When shared-with wallet listens to song, sharer gets 1.5x bonus.
        
        Args:
            sharing_reward_id: ID of sharing reward
            multiplier: Bonus multiplier (default 1.5x)
            
        Returns:
            Updated SharingReward, or None if not found
        """
        reward = self.sharing_rewards.get(sharing_reward_id)
        if not reward:
            return None
        
        reward.listening_multiplier = multiplier
        logger.info(f"Applied {multiplier}x multiplier to sharing reward {sharing_reward_id}")
        
        return reward
    
    def get_user_sharing_rewards(self, wallet_address: str) -> List[SharingReward]:
        """Get all sharing rewards earned by user."""
        return [r for r in self.sharing_rewards.values() if r.sharer_wallet == wallet_address]
    
    def calculate_total_sharing_tokens(self, wallet_address: str) -> float:
        """Calculate total tokens earned from sharing."""
        rewards = self.get_user_sharing_rewards(wallet_address)
        return sum(r.total_reward for r in rewards)
    
    # ==================== LISTENING REWARDS ====================
    
    def record_listening_event(
        self,
        listener_wallet: str,
        song_content_hash: str,
        sharer_wallet: str,
        listen_duration_seconds: int,
        completion_percentage: float,
        base_reward: int = 2
    ) -> ListeningReward:
        """
        Record when user listens to shared song.
        
        Listener earns tokens, sharer gets referral bonus.
        Reward scales with completion percentage.
        
        Args:
            listener_wallet: Wallet of user listening
            song_content_hash: Which song
            sharer_wallet: Original sharer (gets referral bonus)
            listen_duration_seconds: How long they listened
            completion_percentage: % of song completed (0-100)
            base_reward: Base tokens for listening (default 2)
            
        Returns:
            ListeningReward object
        """
        reward_id = f"listen_{listener_wallet}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        reward = ListeningReward(
            reward_id=reward_id,
            listener_wallet=listener_wallet,
            song_content_hash=song_content_hash,
            sharer_wallet=sharer_wallet,
            timestamp=datetime.utcnow().isoformat(),
            listen_duration_seconds=listen_duration_seconds,
            completion_percentage=completion_percentage,
            base_reward_tokens=base_reward
        )
        
        self.listening_rewards[reward_id] = reward
        
        logger.info(
            f"Listening event recorded: {listener_wallet[:10]}... "
            f"(song: {song_content_hash[:16]}, {completion_percentage:.0f}%, "
            f"{reward.total_reward:.1f} tokens)"
        )
        
        return reward
    
    def get_user_listening_rewards(self, wallet_address: str) -> List[ListeningReward]:
        """Get all listening rewards earned by user."""
        return [r for r in self.listening_rewards.values() if r.listener_wallet == wallet_address]
    
    def calculate_total_listening_tokens(self, wallet_address: str) -> float:
        """Calculate total tokens earned from listening."""
        rewards = self.get_user_listening_rewards(wallet_address)
        return sum(r.total_reward for r in rewards)
    
    # ==================== BANDWIDTH REWARDS ====================
    
    def record_bandwidth_serving(
        self,
        node_id: str,
        song_content_hash: str,
        bytes_served: int,
        listeners_served: int,
        transmission_time_seconds: int,
        base_reward: int = 5
    ) -> BandwidthReward:
        """
        Record LoRa node serving content to listeners.
        
        Node earns tokens based on bytes served and listeners reached.
        
        Args:
            node_id: LoRa node ID
            song_content_hash: Which content served
            bytes_served: Bytes transmitted
            listeners_served: Number of unique listeners
            transmission_time_seconds: Duration of service
            base_reward: Base tokens (default 5 per 100MB)
            
        Returns:
            BandwidthReward object
        """
        reward_id = f"bandwidth_{node_id}_{song_content_hash}_{datetime.utcnow().timestamp()}"
        
        reward = BandwidthReward(
            reward_id=reward_id,
            node_id=node_id,
            song_content_hash=song_content_hash,
            bytes_served=bytes_served,
            listeners_served=listeners_served,
            transmission_time_seconds=transmission_time_seconds,
            base_reward_tokens=base_reward
        )
        
        self.bandwidth_rewards[reward_id] = reward
        
        logger.info(
            f"Bandwidth serving recorded: Node {node_id[:10]}... "
            f"({bytes_served / (1024**2):.1f}MB to {listeners_served} listeners, "
            f"{reward.total_reward:.1f} tokens)"
        )
        
        return reward
    
    def get_node_bandwidth_rewards(self, node_id: str) -> List[BandwidthReward]:
        """Get all bandwidth rewards earned by node."""
        return [r for r in self.bandwidth_rewards.values() if r.node_id == node_id]
    
    def calculate_total_bandwidth_tokens(self, node_id: str) -> float:
        """Calculate total tokens earned by node from bandwidth."""
        rewards = self.get_node_bandwidth_rewards(node_id)
        return sum(r.total_reward for r in rewards)
    
    # ==================== ROYALTY DISTRIBUTION ====================
    
    def process_primary_sale(
        self,
        song_title: str,
        artist: str,
        content_hash: str,
        purchase_price_usd: float,
        purchase_price_tokens: int,
        nft_contract_address: str,
        token_id: int,
        blockchain: str = "polygon"
    ) -> RoyaltyPayment:
        """
        Process primary sale (first purchase of NFT).
        
        Royalty split:
        - Artist: 70% (you keep most)
        - Platform: 15% (DCMX operational costs)
        - Node Operators: 10% (LoRa network rewards pool)
        - Early Buyer Bonus: 5% (optional, reserved for future use)
        
        Args:
            song_title: Song name
            artist: Rights holder
            content_hash: SHA256 of audio
            purchase_price_usd: Sale price in USD
            purchase_price_tokens: Sale price in tokens
            nft_contract_address: ERC-721 contract
            token_id: NFT token ID
            blockchain: "ethereum" or "polygon"
            
        Returns:
            RoyaltyPayment object with split details
        """
        payment_id = f"payment_{content_hash}_{token_id}_{datetime.utcnow().timestamp()}"
        
        payment = RoyaltyPayment(
            payment_id=payment_id,
            song_content_hash=content_hash,
            song_title=song_title,
            artist=artist,
            transaction_hash=f"{nft_contract_address}_{token_id}",
            sale_price_usd=purchase_price_usd,
            sale_price_dcmx_tokens=purchase_price_tokens,
            sale_date=datetime.utcnow().isoformat(),
            is_primary_sale=True,
            primary_buyer_wallet="unknown",  # Set by blockchain integration
            artist_percentage=70.0,
            platform_percentage=15.0,
            node_operator_percentage=10.0,
            early_buyer_percentage=5.0,
        )
        
        self.royalty_payments[payment_id] = payment
        
        logger.info(
            f"Primary sale recorded: {song_title} (${purchase_price_usd:.2f}) "
            f"→ Artist: ${payment.artist_payout_usd:.2f} "
            f"| Platform: ${payment.platform_payout_usd:.2f} "
            f"| Nodes: ${payment.node_operator_payout_usd:.2f}"
        )
        
        return payment
    
    def process_secondary_sale(
        self,
        song_title: str,
        artist: str,
        content_hash: str,
        token_id: int,
        seller_wallet: str,
        buyer_wallet: str,
        sale_price_usd: float,
        nft_contract_address: str
    ) -> RoyaltyPayment:
        """
        Process secondary sale (resale on open market).
        
        Secondary sales locked royalties:
        - Original Artist: 70% (locked in smart contract)
        - Node Operators: 20% (incentivize distribution)
        - Platform: 10% (marketplace fees)
        
        This enables artists to earn ongoing revenue from resales.
        
        Args:
            song_title: Song name
            artist: Original artist (rights holder)
            content_hash: SHA256 of audio
            token_id: NFT token ID
            seller_wallet: Current owner selling
            buyer_wallet: New owner buying
            sale_price_usd: Resale price in USD
            nft_contract_address: ERC-721 contract
            
        Returns:
            RoyaltyPayment with secondary market split
        """
        payment_id = f"secondary_{content_hash}_{token_id}_{datetime.utcnow().timestamp()}"
        
        payment = RoyaltyPayment(
            payment_id=payment_id,
            song_content_hash=content_hash,
            song_title=song_title,
            artist=artist,
            transaction_hash=f"{nft_contract_address}_{token_id}_resale",
            sale_price_usd=sale_price_usd,
            sale_price_dcmx_tokens=int(sale_price_usd * 10),  # Approx conversion
            sale_date=datetime.utcnow().isoformat(),
            is_primary_sale=False,
            primary_buyer_wallet=None,  # Not tracked in secondary sale
            secondary_seller_wallet=seller_wallet,
            secondary_buyer_wallet=buyer_wallet,
            # Secondary market split (different from primary)
            artist_percentage=70.0,  # Artist still gets 70%
            platform_percentage=10.0,  # Platform gets 10%
            node_operator_percentage=20.0,  # Nodes get 20% (more incentive)
            early_buyer_percentage=0.0,  # No early buyer bonus
        )
        
        self.royalty_payments[payment_id] = payment
        
        logger.info(
            f"Secondary sale recorded: {song_title} (${sale_price_usd:.2f}) "
            f"{seller_wallet[:10]}... → {buyer_wallet[:10]}... "
            f"→ Artist: ${payment.artist_payout_usd:.2f}"
        )
        
        return payment
    
    def get_artist_royalties(self, artist: str) -> float:
        """Get total royalties owed to artist."""
        payments = [
            p for p in self.royalty_payments.values()
            if p.artist == artist
        ]
        return sum(p.artist_payout_usd for p in payments)
    
    def get_platform_royalties(self) -> float:
        """Get total royalties owed to platform."""
        return sum(p.platform_payout_usd for p in self.royalty_payments.values())
    
    def get_node_operator_pool(self) -> float:
        """Get total royalties in node operator pool."""
        return sum(p.node_operator_payout_usd for p in self.royalty_payments.values())
    
    # ==================== REWARD CLAIMS & VERIFICATION ====================
    
    def create_reward_claim(
        self,
        claimant_wallet: str,
        claim_type: RewardType,
        song_content_hash: str,
        total_tokens_claimed: float,
        activity_count: int = 1
    ) -> RewardClaim:
        """
        Create reward claim for verification.
        
        User submits claim with ZK proof. Verifiers check proof before
        tokens are minted.
        
        Args:
            claimant_wallet: User claiming rewards
            claim_type: Type of activity (sharing, listening, bandwidth)
            song_content_hash: Which song earned rewards
            total_tokens_claimed: Total tokens claimed
            activity_count: Number of activities
            
        Returns:
            RewardClaim object (requires ZK proof verification)
        """
        claim_id = f"claim_{claimant_wallet}_{claim_type.value}_{datetime.utcnow().timestamp()}"
        
        claim = RewardClaim(
            claim_id=claim_id,
            claimant_wallet=claimant_wallet,
            claim_type=claim_type,
            song_content_hash=song_content_hash,
            activity_count=activity_count,
            timestamp=datetime.utcnow().isoformat(),
            total_tokens_claimed=total_tokens_claimed,
            proof_type=f"{claim_type.value}_proof"
        )
        
        self.reward_claims[claim_id] = claim
        
        logger.info(
            f"Reward claim created: {claimant_wallet[:10]}... "
            f"(type: {claim_type.value}, tokens: {total_tokens_claimed}, "
            f"activities: {activity_count})"
        )
        
        return claim
    
    def verify_reward_claim(
        self,
        claim_id: str,
        zk_proof_data: Dict,
        verifier_signature: str
    ) -> bool:
        """
        Verify reward claim using ZK proof.
        
        Called by verifier node after checking ZK proof.
        Once approved by quorum of verifiers, tokens are minted.
        
        Args:
            claim_id: ID of claim to verify
            zk_proof_data: ZK proof attachment
            verifier_signature: Verifier's digital signature
            
        Returns:
            True if claim verified successfully
        """
        claim = self.reward_claims.get(claim_id)
        if not claim:
            logger.warning(f"Reward claim not found: {claim_id}")
            return False
        
        # In real implementation, would verify ZK proof cryptographically
        claim.proof_data = zk_proof_data
        claim.proof_verified = True
        claim.verification_timestamp = datetime.utcnow().isoformat()
        claim.total_tokens_verified = claim.total_tokens_claimed
        
        logger.info(f"Reward claim verified: {claim_id} ({claim.total_tokens_verified} tokens)")
        
        return True
    
    def approve_and_mint_tokens(
        self,
        claim_id: str,
        blockchain_tx_hash: str
    ) -> bool:
        """
        Approve verified claim and mint tokens on blockchain.
        
        Called after quorum of verifiers (3-of-4) approve the claim.
        Mints tokens to user's wallet on blockchain.
        
        Args:
            claim_id: ID of verified claim
            blockchain_tx_hash: Transaction hash of token mint
            
        Returns:
            True if tokens successfully minted
        """
        claim = self.reward_claims.get(claim_id)
        if not claim:
            return False
        
        if not claim.proof_verified:
            logger.warning(f"Cannot mint: claim not verified: {claim_id}")
            return False
        
        claim.is_approved = True
        claim.approval_timestamp = datetime.utcnow().isoformat()
        claim.tokens_minted = True
        claim.mint_transaction_hash = blockchain_tx_hash
        
        logger.info(
            f"Tokens minted: {claim.claimant_wallet[:10]}... "
            f"({claim.total_tokens_verified} tokens, tx: {blockchain_tx_hash[:16]}...)"
        )
        
        return True
    
    def get_user_pending_claims(self, wallet_address: str) -> List[RewardClaim]:
        """Get all pending reward claims from user."""
        return [
            c for c in self.reward_claims.values()
            if c.claimant_wallet == wallet_address and not c.is_approved
        ]
    
    def get_user_total_claimed_tokens(self, wallet_address: str) -> float:
        """Get total tokens user has claimed (approved claims)."""
        claims = [
            c for c in self.reward_claims.values()
            if c.claimant_wallet == wallet_address and c.is_approved
        ]
        return sum(c.total_tokens_verified for c in claims)
    
    # ==================== REPORTING & ANALYTICS ====================
    
    def generate_user_reward_report(self, wallet_address: str) -> Dict:
        """Generate comprehensive reward report for user."""
        sharing_tokens = self.calculate_total_sharing_tokens(wallet_address)
        listening_tokens = self.calculate_total_listening_tokens(wallet_address)
        claimed_tokens = self.get_user_total_claimed_tokens(wallet_address)
        pending_claims = len(self.get_user_pending_claims(wallet_address))
        
        return {
            "wallet": wallet_address[:20] + "...",
            "sharing_rewards": {
                "events": len(self.get_user_sharing_rewards(wallet_address)),
                "total_tokens": sharing_tokens
            },
            "listening_rewards": {
                "events": len(self.get_user_listening_rewards(wallet_address)),
                "total_tokens": listening_tokens
            },
            "total_earned": sharing_tokens + listening_tokens,
            "claimed_tokens": claimed_tokens,
            "pending_claims": pending_claims,
            "nft_certificates": len(self.list_user_certificates(wallet_address)),
        }
    
    def generate_royalty_report(self, artist: str) -> Dict:
        """Generate royalty report for artist."""
        artist_royalties = self.get_artist_royalties(artist)
        payments = [p for p in self.royalty_payments.values() if p.artist == artist]
        
        primary_sales = [p for p in payments if p.is_primary_sale]
        secondary_sales = [p for p in payments if not p.is_primary_sale]
        
        return {
            "artist": artist,
            "total_royalties_usd": artist_royalties,
            "primary_sales": {
                "count": len(primary_sales),
                "total_usd": sum(p.artist_payout_usd for p in primary_sales),
                "avg_payout": sum(p.artist_payout_usd for p in primary_sales) / len(primary_sales) if primary_sales else 0
            },
            "secondary_sales": {
                "count": len(secondary_sales),
                "total_usd": sum(p.artist_payout_usd for p in secondary_sales),
                "avg_payout": sum(p.artist_payout_usd for p in secondary_sales) / len(secondary_sales) if secondary_sales else 0
            },
            "nfts_issued": len([c for c in self.certificates.values() if c.artist == artist]),
        }
    
    def generate_platform_statistics(self) -> Dict:
        """Generate overall platform statistics."""
        return {
            "total_revenue_usd": sum(p.sale_price_usd for p in self.royalty_payments.values()),
            "total_royalties_distributed_usd": sum(
                p.artist_payout_usd + p.platform_payout_usd + p.node_operator_payout_usd
                for p in self.royalty_payments.values()
            ),
            "platform_earnings_usd": self.get_platform_royalties(),
            "node_operator_pool_usd": self.get_node_operator_pool(),
            "nfts_issued": len(self.certificates),
            "reward_claims_submitted": len(self.reward_claims),
            "reward_claims_approved": len([c for c in self.reward_claims.values() if c.is_approved]),
            "total_tokens_distributed": sum(c.total_tokens_verified for c in self.reward_claims.values() if c.is_approved),
            "sharing_events": len(self.sharing_rewards),
            "listening_events": len(self.listening_rewards),
            "bandwidth_rewards": len(self.bandwidth_rewards),
        }
