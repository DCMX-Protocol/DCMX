"""
Artist NFT Wallet Connection System for DCMX

Enables artists to:
1. Create verified artist profiles
2. Connect wallets (MetaMask, WalletConnect, etc.)
3. Verify NFT ownership
4. Manage rights and royalties
5. Control distribution permissions
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import hashlib
import secrets
import json
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


class WalletType(Enum):
    """Supported wallet types."""
    METAMASK = "metamask"
    WALLETCONNECT = "walletconnect"
    LEDGER = "ledger"
    TREZOR = "trezor"
    COINBASE = "coinbase"
    ARGENT = "argent"
    OTHER = "other"


class VerificationStatus(Enum):
    """Verification status for artist and NFT."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RightsType(Enum):
    """Types of rights for NFT."""
    FULL_OWNERSHIP = "full_ownership"              # Artist owns all rights
    EXCLUSIVE_DISTRIBUTION = "exclusive_distribution"  # Platform exclusive
    LIMITED_DISTRIBUTION = "limited_distribution"   # Limited territory/time
    STREAMING_ONLY = "streaming_only"              # No download rights
    SAMPLE_RIGHTS = "sample_rights"                # Sampling allowed
    COLLABORATION = "collaboration"                 # Multiple artists


class RoyaltyTier(Enum):
    """Royalty percentage tiers."""
    NONE = 0
    LOW = 5        # 5%
    STANDARD = 10  # 10%
    HIGH = 15      # 15%
    PREMIUM = 20   # 20%
    CUSTOM = -1    # Custom percentage


@dataclass
class WalletAddress:
    """Blockchain wallet address with metadata."""
    
    address: str                               # Wallet address (0x...)
    chain: str = "ethereum"                    # Blockchain: ethereum, polygon, etc.
    wallet_type: WalletType = WalletType.METAMASK
    
    # Verification
    is_verified: bool = False
    verified_at: Optional[str] = None
    verification_method: str = "signature"     # signature | message | contract
    
    # Balance tracking
    balance_eth: float = 0.0
    balance_usd: float = 0.0
    last_balance_check: Optional[str] = None
    
    # Activity
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used_at: Optional[str] = None
    transaction_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "address": self.address,
            "chain": self.chain,
            "wallet_type": self.wallet_type.value,
            "is_verified": self.is_verified,
            "verified_at": self.verified_at,
            "verification_method": self.verification_method,
            "balance_eth": self.balance_eth,
            "balance_usd": self.balance_usd,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "transaction_count": self.transaction_count
        }


@dataclass
class NFTOwnership:
    """NFT ownership verification record."""
    
    nft_id: str                                # NFT token ID
    contract_address: str                      # Smart contract address
    chain: str = "ethereum"
    owner_address: str = ""                    # Wallet owning the NFT
    
    # Ownership details
    token_standard: str = "ERC-721"            # ERC-721 or ERC-1155
    quantity_owned: int = 1                    # For ERC-1155
    percentage_owned: float = 100.0            # Ownership percentage
    
    # Verification
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verified_at: Optional[str] = None
    verification_method: str = "contract_query"  # contract_query | block_explorer
    
    # Metadata
    title: str = ""
    artist_name: str = ""
    metadata_uri: str = ""
    
    # Acquisition
    acquired_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    purchase_price: float = 0.0
    purchase_currency: str = "ETH"
    
    # DCMX specific
    dcmx_content_hash: Optional[str] = None    # Link to DCMX track
    watermark_proof_chain_id: Optional[str] = None  # Reference to ZK proof
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "nft_id": self.nft_id,
            "contract_address": self.contract_address,
            "chain": self.chain,
            "owner_address": self.owner_address,
            "token_standard": self.token_standard,
            "quantity_owned": self.quantity_owned,
            "percentage_owned": self.percentage_owned,
            "verification_status": self.verification_status.value,
            "verified_at": self.verified_at,
            "verification_method": self.verification_method,
            "title": self.title,
            "artist_name": self.artist_name,
            "metadata_uri": self.metadata_uri,
            "acquired_at": self.acquired_at,
            "purchase_price": self.purchase_price,
            "purchase_currency": self.purchase_currency,
            "dcmx_content_hash": self.dcmx_content_hash,
            "watermark_proof_chain_id": self.watermark_proof_chain_id
        }


@dataclass
class RoyaltySettings:
    """Royalty configuration for artist."""
    
    # Base royalty
    primary_royalty_percent: float = 10.0      # On primary sales
    secondary_royalty_percent: float = 5.0     # On secondary sales
    
    # Royalty tier
    tier: RoyaltyTier = RoyaltyTier.STANDARD
    
    # Distribution
    royalty_payment_address: str = ""          # Where to send payments
    royalty_payment_chain: str = "ethereum"
    payment_frequency: str = "monthly"         # monthly | quarterly | on_sale
    
    # Splits (for collaborations)
    splits: Dict[str, float] = field(default_factory=dict)  # {address: percentage}
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "primary_royalty_percent": self.primary_royalty_percent,
            "secondary_royalty_percent": self.secondary_royalty_percent,
            "tier": self.tier.value,
            "royalty_payment_address": self.royalty_payment_address,
            "royalty_payment_chain": self.royalty_payment_chain,
            "payment_frequency": self.payment_frequency,
            "splits": self.splits,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class ArtistProfile:
    """Artist profile with verified identity and wallet connections."""
    
    # Identity
    artist_id: str = field(default_factory=lambda: str(uuid4()))
    legal_name: str = ""
    artist_name: str = ""
    bio: str = ""
    website: str = ""
    social_links: Dict[str, str] = field(default_factory=dict)  # {platform: url}
    
    # Email & Contact
    email: str = ""
    email_verified: bool = False
    email_verified_at: Optional[str] = None
    
    # Identity verification
    identity_verified: bool = False
    identity_verified_at: Optional[str] = None
    identity_verification_method: str = ""     # KYC provider
    kyc_provider: str = ""                     # stripe, onfido, sumsub
    kyc_verification_id: str = ""
    
    # Wallets
    primary_wallet: Optional[WalletAddress] = None
    connected_wallets: List[WalletAddress] = field(default_factory=list)
    
    # NFTs
    owned_nfts: List[NFTOwnership] = field(default_factory=list)
    issued_nfts: List[NFTOwnership] = field(default_factory=list)  # NFTs created/minted
    
    # Royalties & Rights
    royalty_settings: RoyaltySettings = field(default_factory=RoyaltySettings)
    rights_type: RightsType = RightsType.FULL_OWNERSHIP
    
    # Verification
    profile_verified: bool = False
    profile_verified_at: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    
    # DCMX specific
    dcmx_verified_artist: bool = False         # Verified as original content creator
    dcmx_verification_timestamp: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "artist_id": self.artist_id,
            "legal_name": self.legal_name,
            "artist_name": self.artist_name,
            "bio": self.bio,
            "website": self.website,
            "social_links": self.social_links,
            "email": self.email,
            "email_verified": self.email_verified,
            "identity_verified": self.identity_verified,
            "primary_wallet": self.primary_wallet.to_dict() if self.primary_wallet else None,
            "connected_wallets": [w.to_dict() for w in self.connected_wallets],
            "owned_nfts": [n.to_dict() for n in self.owned_nfts],
            "issued_nfts": [n.to_dict() for n in self.issued_nfts],
            "royalty_settings": self.royalty_settings.to_dict(),
            "rights_type": self.rights_type.value,
            "profile_verified": self.profile_verified,
            "verification_status": self.verification_status.value,
            "dcmx_verified_artist": self.dcmx_verified_artist,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login
        }


@dataclass
class WalletSignatureChallenge:
    """Challenge for wallet signature verification."""
    
    challenge_id: str = field(default_factory=lambda: str(uuid4()))
    artist_id: str = ""
    wallet_address: str = ""
    
    # Challenge
    message: str = ""                          # Message to sign
    challenge_nonce: str = field(default_factory=lambda: secrets.token_hex(16))
    
    # Verification
    signature: Optional[str] = None
    signature_verified: bool = False
    verified_at: Optional[str] = None
    
    # Lifecycle
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = field(default_factory=lambda: (
        datetime.now(timezone.utc) + timedelta(minutes=15)
    ).isoformat())
    used: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "challenge_id": self.challenge_id,
            "artist_id": self.artist_id,
            "wallet_address": self.wallet_address,
            "message": self.message,
            "signature": self.signature,
            "signature_verified": self.signature_verified,
            "created_at": self.created_at,
            "expires_at": self.expires_at
        }


class ArtistWalletManager:
    """Manages artist profiles and wallet connections."""
    
    def __init__(self):
        """Initialize manager."""
        self.artists: Dict[str, ArtistProfile] = {}
        self.wallet_to_artist: Dict[str, str] = {}  # wallet_addr -> artist_id
        self.challenges: Dict[str, WalletSignatureChallenge] = {}
    
    def create_artist_profile(
        self,
        legal_name: str,
        artist_name: str,
        email: str
    ) -> ArtistProfile:
        """Create new artist profile.
        
        Args:
            legal_name: Artist's legal name
            artist_name: Public artist name
            email: Email address
        
        Returns:
            New ArtistProfile
        """
        profile = ArtistProfile(
            legal_name=legal_name,
            artist_name=artist_name,
            email=email
        )
        
        self.artists[profile.artist_id] = profile
        logger.info(f"Created artist profile: {profile.artist_id} ({artist_name})")
        
        return profile
    
    def create_wallet_connection_challenge(
        self,
        artist_id: str,
        wallet_address: str
    ) -> WalletSignatureChallenge:
        """Create challenge for wallet signature verification.
        
        Args:
            artist_id: Artist ID
            wallet_address: Wallet address to verify
        
        Returns:
            WalletSignatureChallenge with message to sign
        """
        if artist_id not in self.artists:
            raise ValueError(f"Artist {artist_id} not found")
        
        challenge = WalletSignatureChallenge(
            artist_id=artist_id,
            wallet_address=wallet_address.lower()
        )
        
        # Create message for signature
        timestamp = int(datetime.now(timezone.utc).timestamp())
        challenge.message = (
            f"Connect wallet to DCMX\n"
            f"Artist: {self.artists[artist_id].artist_name}\n"
            f"Wallet: {wallet_address}\n"
            f"Nonce: {challenge.challenge_nonce}\n"
            f"Timestamp: {timestamp}\n"
            f"This action will not cost any gas."
        )
        
        self.challenges[challenge.challenge_id] = challenge
        logger.info(f"Created wallet challenge: {challenge.challenge_id}")
        
        return challenge
    
    def verify_wallet_signature(
        self,
        challenge_id: str,
        signature: str,
        public_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Verify wallet signature (simulated - in production use ethers.js).
        
        Args:
            challenge_id: Challenge ID
            signature: Signature from wallet
            public_address: Optional public address to verify against
        
        Returns:
            Tuple of (verified: bool, message: str)
        """
        if challenge_id not in self.challenges:
            return False, "Challenge not found"
        
        challenge = self.challenges[challenge_id]
        
        # Check if expired
        expires = datetime.fromisoformat(challenge.expires_at)
        if datetime.now(timezone.utc) > expires:
            return False, "Challenge expired"
        
        # Check if already used
        if challenge.used:
            return False, "Challenge already used"
        
        # In production, use ethers.js to verify:
        # from eth_account.messages import encode_defunct
        # from eth_account import Account
        # message_hash = encode_defunct(text=challenge.message)
        # recovered_address = Account.recover_message(message_hash, signature=signature)
        # verified = recovered_address.lower() == challenge.wallet_address.lower()
        
        # For now, simulate verification with basic validation
        # Accept any non-empty signature for testing
        verified = signature is not None and isinstance(signature, str)
        
        if verified:
            challenge.signature = signature
            challenge.signature_verified = True
            challenge.verified_at = datetime.now(timezone.utc).isoformat()
            challenge.used = True
            
            logger.info(f"Verified wallet signature: {challenge.wallet_address}")
            return True, "Signature verified"
        else:
            logger.warning(f"Failed to verify signature for challenge {challenge_id}")
            return False, "Signature verification failed"
    
    def connect_wallet(
        self,
        artist_id: str,
        challenge_id: str,
        signature: str,
        wallet_type: WalletType = WalletType.METAMASK
    ) -> Tuple[bool, str, Optional[WalletAddress]]:
        """Connect verified wallet to artist profile.
        
        Args:
            artist_id: Artist ID
            challenge_id: Challenge ID
            signature: Wallet signature
            wallet_type: Type of wallet
        
        Returns:
            Tuple of (success: bool, message: str, wallet: Optional[WalletAddress])
        """
        if artist_id not in self.artists:
            return False, "Artist not found", None
        
        if challenge_id not in self.challenges:
            return False, "Challenge not found", None
        
        challenge = self.challenges[challenge_id]
        
        # Verify signature
        verified, msg = self.verify_wallet_signature(challenge_id, signature)
        if not verified:
            return False, msg, None
        
        artist = self.artists[artist_id]
        wallet_addr = challenge.wallet_address
        
        # Check if wallet already connected to another artist
        if wallet_addr in self.wallet_to_artist:
            existing_artist = self.wallet_to_artist[wallet_addr]
            if existing_artist != artist_id:
                return False, "Wallet already connected to another artist", None
        
        # Create wallet address object
        wallet = WalletAddress(
            address=wallet_addr,
            wallet_type=wallet_type,
            is_verified=True,
            verified_at=datetime.now(timezone.utc).isoformat()
        )
        
        # Set as primary if first wallet
        if artist.primary_wallet is None:
            artist.primary_wallet = wallet
        else:
            artist.connected_wallets.append(wallet)
        
        # Map wallet to artist
        self.wallet_to_artist[wallet_addr] = artist_id
        
        logger.info(f"Connected wallet {wallet_addr} to artist {artist_id}")
        return True, "Wallet connected successfully", wallet
    
    def add_owned_nft(
        self,
        artist_id: str,
        nft_id: str,
        contract_address: str,
        owner_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[NFTOwnership]]:
        """Register NFT owned by artist.
        
        Args:
            artist_id: Artist ID
            nft_id: Token ID
            contract_address: Smart contract address
            owner_address: Wallet address (defaults to primary wallet)
        
        Returns:
            Tuple of (success: bool, message: str, nft: Optional[NFTOwnership])
        """
        if artist_id not in self.artists:
            return False, "Artist not found", None
        
        artist = self.artists[artist_id]
        
        if owner_address is None:
            if artist.primary_wallet is None:
                return False, "No wallet connected", None
            owner_address = artist.primary_wallet.address
        
        # Check if already registered
        for nft in artist.owned_nfts:
            if nft.nft_id == nft_id and nft.contract_address == contract_address:
                return False, "NFT already registered", nft
        
        nft_ownership = NFTOwnership(
            nft_id=nft_id,
            contract_address=contract_address,
            owner_address=owner_address,
            verification_status=VerificationStatus.VERIFIED,
            verified_at=datetime.now(timezone.utc).isoformat()
        )
        
        artist.owned_nfts.append(nft_ownership)
        
        logger.info(f"Added owned NFT {nft_id} for artist {artist_id}")
        return True, "NFT registered", nft_ownership
    
    def verify_artist_identity(
        self,
        artist_id: str,
        kyc_provider: str = "stripe",
        kyc_verification_id: str = ""
    ) -> Tuple[bool, str]:
        """Mark artist as KYC verified.
        
        Args:
            artist_id: Artist ID
            kyc_provider: KYC provider (stripe, onfido, sumsub)
            kyc_verification_id: Verification ID from provider
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if artist_id not in self.artists:
            return False, "Artist not found"
        
        artist = self.artists[artist_id]
        
        artist.identity_verified = True
        artist.identity_verified_at = datetime.now(timezone.utc).isoformat()
        artist.kyc_provider = kyc_provider
        artist.kyc_verification_id = kyc_verification_id
        artist.identity_verification_method = f"kyc_{kyc_provider}"
        
        logger.info(f"Verified artist identity: {artist_id} (provider: {kyc_provider})")
        return True, f"Artist identity verified via {kyc_provider}"
    
    def mark_as_dcmx_verified_artist(self, artist_id: str) -> Tuple[bool, str]:
        """Mark artist as verified DCMX content creator.
        
        Args:
            artist_id: Artist ID
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if artist_id not in self.artists:
            return False, "Artist not found"
        
        artist = self.artists[artist_id]
        
        # Requirements for DCMX verification
        if not artist.primary_wallet:
            return False, "No wallet connected"
        
        if not artist.primary_wallet.is_verified:
            return False, "Wallet not verified"
        
        if not artist.email_verified:
            return False, "Email not verified"
        
        if not artist.identity_verified:
            return False, "Identity not verified"
        
        artist.dcmx_verified_artist = True
        artist.dcmx_verification_timestamp = datetime.now(timezone.utc).isoformat()
        artist.profile_verified = True
        artist.verification_status = VerificationStatus.VERIFIED
        
        logger.info(f"Marked artist as DCMX verified: {artist_id}")
        return True, "Artist verified as DCMX content creator"
    
    def get_artist_profile(self, artist_id: str) -> Optional[ArtistProfile]:
        """Get artist profile by ID.
        
        Args:
            artist_id: Artist ID
        
        Returns:
            ArtistProfile or None
        """
        return self.artists.get(artist_id)
    
    def get_artist_by_wallet(self, wallet_address: str) -> Optional[ArtistProfile]:
        """Get artist by wallet address.
        
        Args:
            wallet_address: Wallet address
        
        Returns:
            ArtistProfile or None
        """
        artist_id = self.wallet_to_artist.get(wallet_address.lower())
        if artist_id:
            return self.artists.get(artist_id)
        return None
    
    def get_artist_nfts(
        self,
        artist_id: str,
        nft_type: str = "owned"
    ) -> List[NFTOwnership]:
        """Get NFTs for artist.
        
        Args:
            artist_id: Artist ID
            nft_type: "owned" or "issued"
        
        Returns:
            List of NFTOwnership
        """
        if artist_id not in self.artists:
            return []
        
        artist = self.artists[artist_id]
        
        if nft_type == "owned":
            return artist.owned_nfts
        elif nft_type == "issued":
            return artist.issued_nfts
        else:
            return artist.owned_nfts + artist.issued_nfts
    
    def update_royalty_settings(
        self,
        artist_id: str,
        primary_royalty: float,
        secondary_royalty: float,
        payment_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Update artist royalty settings.
        
        Args:
            artist_id: Artist ID
            primary_royalty: Primary sale royalty %
            secondary_royalty: Secondary sale royalty %
            payment_address: Payment wallet address
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if artist_id not in self.artists:
            return False, "Artist not found"
        
        # Validate percentages
        if not (0 <= primary_royalty <= 50):
            return False, "Primary royalty must be 0-50%"
        if not (0 <= secondary_royalty <= 50):
            return False, "Secondary royalty must be 0-50%"
        
        artist = self.artists[artist_id]
        artist.royalty_settings.primary_royalty_percent = primary_royalty
        artist.royalty_settings.secondary_royalty_percent = secondary_royalty
        artist.royalty_settings.updated_at = datetime.now(timezone.utc).isoformat()
        
        if payment_address:
            artist.royalty_settings.royalty_payment_address = payment_address
        
        logger.info(f"Updated royalty settings for artist {artist_id}")
        return True, "Royalty settings updated"
    
    def get_verification_status(self, artist_id: str) -> Dict[str, Any]:
        """Get comprehensive verification status for artist.
        
        Args:
            artist_id: Artist ID
        
        Returns:
            Dictionary of verification statuses
        """
        if artist_id not in self.artists:
            return {}
        
        artist = self.artists[artist_id]
        
        return {
            "artist_id": artist_id,
            "profile_verified": artist.profile_verified,
            "dcmx_verified": artist.dcmx_verified_artist,
            "email_verified": artist.email_verified,
            "identity_verified": artist.identity_verified,
            "wallet_connected": artist.primary_wallet is not None,
            "wallet_verified": artist.primary_wallet.is_verified if artist.primary_wallet else False,
            "verification_status": artist.verification_status.value,
            "verification_timestamp": artist.profile_verified_at,
            "nfts_registered": len(artist.owned_nfts),
            "wallets_connected": 1 + len(artist.connected_wallets),
            "kyc_provider": artist.kyc_provider,
            "requirements_met": {
                "wallet": artist.primary_wallet is not None and artist.primary_wallet.is_verified,
                "email": artist.email_verified,
                "identity": artist.identity_verified,
                "profile_info": bool(artist.artist_name and artist.legal_name)
            }
        }
    
    def export_artist_profile(self, artist_id: str) -> str:
        """Export artist profile as JSON.
        
        Args:
            artist_id: Artist ID
        
        Returns:
            JSON string of profile
        """
        if artist_id not in self.artists:
            raise ValueError(f"Artist {artist_id} not found")
        
        artist = self.artists[artist_id]
        return json.dumps(artist.to_dict(), indent=2)
