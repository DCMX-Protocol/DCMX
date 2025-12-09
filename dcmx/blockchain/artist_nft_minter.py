"""
Artist NFT Minting Integration - Bridges verified artists with blockchain NFT creation.

This module handles:
- Automated NFT minting for verified artists
- Royalty configuration and enforcement (ERC-2981)
- Edition management and limited supply control
- Watermark metadata embedding
- Secondary market royalty distribution
- Wallet-to-NFT linkage verification
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from uuid import uuid4

from dcmx.artist.artist_wallet_manager import ArtistWalletManager, ArtistProfile
from dcmx.artist.nft_ownership_verifier import NFTOwnershipVerifier
from dcmx.audio.zk_watermark_proof import ZKWatermarkProofGenerator, CascadingProofChain
from dcmx.blockchain.contract_manager import ContractManager


logger = logging.getLogger(__name__)


class NFTMintStatus(Enum):
    """Status of NFT minting operation."""
    PENDING = "pending"  # Awaiting blockchain confirmation
    CONFIRMED = "confirmed"  # On-chain confirmed
    FAILED = "failed"  # Transaction failed
    CANCELLED = "cancelled"  # User cancelled
    METADATA_ERROR = "metadata_error"  # Metadata invalid


class RoyaltyDistributionType(Enum):
    """Type of royalty distribution."""
    PRIMARY_SALE = "primary_sale"  # Artist receives 100% (minus platform fee)
    SECONDARY_SALE = "secondary_sale"  # Artist receives configured %
    STREAMING = "streaming"  # From streaming platform
    LICENSING = "licensing"  # Commercial use
    SYNC = "sync"  # Sync licensing (film/TV)


@dataclass
class ArtistMintRequest:
    """Request to mint NFT for verified artist."""
    artist_id: str
    track_title: str
    dcmx_content_hash: str  # SHA-256 of audio
    watermark_proof_chain_id: str  # Link to ZK proof chain
    edition_number: int
    max_editions: int
    price_wei: int  # Sale price in wei
    royalty_primary_bps: int = 10000  # 100% default (artist gets everything)
    royalty_secondary_bps: int = 500  # 5% secondary market
    primary_sale_timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class NFTMetadata:
    """Complete metadata for minted NFT."""
    title: str
    artist: str
    artist_wallet: str
    dcmx_content_hash: str  # Links to audio watermark
    watermark_proof_chain_id: str  # Links to ZK proof
    edition_number: int
    max_editions: int
    watermark_status: str = "verified"  # verified | pending | failed
    watermark_confidence: float = 0.95  # Confidence score
    royalty_recipient: str = ""
    royalty_bps_primary: int = 10000  # Basis points
    royalty_bps_secondary: int = 500
    image_url: str = ""
    animation_url: str = ""  # Audio file URL
    external_url: str = ""  # Link to DCMX
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to metadata dict for IPFS/URI."""
        return {
            "name": self.title,
            "description": self.description or f"Limited Edition {self.edition_number} of {self.max_editions}",
            "image": self.image_url,
            "animation_url": self.animation_url,
            "external_url": self.external_url,
            "artist": self.artist,
            "artist_wallet": self.artist_wallet,
            "attributes": self.attributes + [
                {"trait_type": "Edition", "value": f"{self.edition_number}/{self.max_editions}"},
                {"trait_type": "Watermark Status", "value": self.watermark_status},
                {"trait_type": "Watermark Confidence", "value": str(self.watermark_confidence)},
                {"trait_type": "DCMX Content Hash", "value": self.dcmx_content_hash},
                {"trait_type": "Proof Chain ID", "value": self.watermark_proof_chain_id},
            ],
            "dcmx": {
                "content_hash": self.dcmx_content_hash,
                "proof_chain_id": self.watermark_proof_chain_id,
                "watermark_verified": self.watermark_status == "verified",
                "watermark_confidence": self.watermark_confidence,
                "created_at": self.created_at,
            },
            "royalty": {
                "recipient": self.royalty_recipient,
                "primary_bps": self.royalty_bps_primary,
                "secondary_bps": self.royalty_bps_secondary,
            }
        }

    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class MintedNFT:
    """Record of successfully minted NFT."""
    mint_id: str
    artist_id: str
    contract_address: str
    token_id: int
    transaction_hash: str
    metadata_uri: str
    status: NFTMintStatus
    edition_number: int
    max_editions: int
    minted_at: str
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    watermark_verified: bool = True
    watermark_confidence: float = 0.95
    platform_fee_bps: int = 250  # 2.5% platform fee
    artist_receives_bps: int = 9750  # 97.5% to artist


@dataclass
class RoyaltyDistribution:
    """Record of royalty payment to artist."""
    distribution_id: str
    artist_id: str
    artist_wallet: str
    token_id: int
    amount_wei: int
    distribution_type: RoyaltyDistributionType
    transaction_hash: str
    distributed_at: str
    platform_fee: int  # Absolute amount


@dataclass
class SecondaryMarketData:
    """Data for secondary market royalty enforcement."""
    nft_id: str
    seller_wallet: str
    buyer_wallet: str
    sale_price_wei: int
    marketplace: str  # "opensea", "rarible", "custom"
    transaction_hash: str
    royalty_paid_wei: int
    artist_wallet: str
    sale_timestamp: str


class ArtistNFTMinter:
    """
    Orchestrates NFT minting for verified artists.
    
    Integrates:
    - Artist verification (ArtistWalletManager)
    - Watermark verification (ZKWatermarkProofGenerator)
    - Blockchain minting (ContractManager)
    - Royalty enforcement (ERC-2981)
    - Secondary market tracking
    """

    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        music_nft_contract: str,
        dcmx_token_contract: str,
    ):
        """
        Initialize artist NFT minter.
        
        Args:
            rpc_url: RPC endpoint URL
            private_key: Private key for signing transactions
            music_nft_contract: MusicNFT contract address
            dcmx_token_contract: DCMX token contract address
        """
        from web3 import Web3
        
        self.artist_manager = ArtistWalletManager()
        self.nft_verifier = NFTOwnershipVerifier()
        self.watermark_generator = ZKWatermarkProofGenerator()
        
        # Initialize Web3 and ContractManager
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_manager = ContractManager(w3=w3, signer_key=private_key)
        
        self.music_nft_contract = music_nft_contract
        self.dcmx_token_contract = dcmx_token_contract
        
        # Track minted NFTs
        self.minted_nfts: Dict[str, MintedNFT] = {}
        self.royalty_distributions: Dict[str, RoyaltyDistribution] = {}
        self.secondary_market_data: Dict[str, SecondaryMarketData] = {}
        
        logger.info(f"ArtistNFTMinter initialized")

    async def mint_artist_nft(
        self,
        request: ArtistMintRequest,
        metadata_uri: str
    ) -> Tuple[bool, str, Optional[MintedNFT]]:
        """
        Mint NFT for verified artist.
        
        Process:
        1. Verify artist is fully verified (KYC + wallet + email)
        2. Verify watermark proof chain exists and is valid
        3. Create NFT metadata with watermark link
        4. Mint NFT on blockchain
        5. Link NFT to artist profile
        6. Configure royalty settings
        
        Args:
            request: ArtistMintRequest with minting details
            metadata_uri: URI pointing to metadata (IPFS, HTTP, etc)
            
        Returns:
            Tuple of (success, message, MintedNFT record)
        """
        mint_id = str(uuid4())
        
        try:
            # Step 1: Verify artist
            logger.info(f"[{mint_id}] Verifying artist {request.artist_id}...")
            artist = self.artist_manager.get_artist_profile(request.artist_id)
            if not artist:
                return False, f"Artist not found: {request.artist_id}", None
            
            # Check artist is fully verified
            status = self.artist_manager.get_verification_status(request.artist_id)
            if not status.get("dcmx_verified"):
                return False, "Artist not DCMX verified. Please complete KYC and identity verification.", None
            
            if not status.get("wallet_connected"):
                return False, "Artist wallet not connected. Please connect wallet first.", None
            
            # Step 2: Verify watermark proof chain
            logger.info(f"[{mint_id}] Verifying watermark proof chain {request.watermark_proof_chain_id}...")
            # Note: In production, retrieve from ZK proof chain storage
            proof_verified = await self._verify_proof_chain(request.watermark_proof_chain_id)
            if not proof_verified:
                return False, f"Watermark proof chain invalid: {request.watermark_proof_chain_id}", None
            
            # Step 3: Create metadata
            logger.info(f"[{mint_id}] Creating NFT metadata...")
            artist_wallet = status.get("wallet_address", "")
            metadata = self._create_nft_metadata(
                request=request,
                artist=artist,
                artist_wallet=artist_wallet
            )
            
            # Step 4: Mint on blockchain
            logger.info(f"[{mint_id}] Minting NFT on blockchain...")
            tx_hash, token_id, gas_used = await self._mint_on_blockchain(
                contract_address=self.music_nft_contract,
                to_address=artist_wallet,
                token_id_hint=request.edition_number,
                metadata_uri=metadata_uri,
                royalty_recipient=artist_wallet,
                royalty_bps=request.royalty_primary_bps
            )
            
            if not tx_hash:
                return False, "Blockchain minting failed", None
            
            # Step 5: Link to artist profile
            logger.info(f"[{mint_id}] Linking NFT to artist profile...")
            success, msg = self.artist_manager.add_owned_nft(
                artist_id=request.artist_id,
                token_id=str(token_id),
                contract_address=self.music_nft_contract
            )
            
            if not success:
                logger.warning(f"[{mint_id}] Failed to link NFT to artist profile: {msg}")
            
            # Step 6: Create minted NFT record
            minted = MintedNFT(
                mint_id=mint_id,
                artist_id=request.artist_id,
                contract_address=self.music_nft_contract,
                token_id=token_id,
                transaction_hash=tx_hash,
                metadata_uri=metadata_uri,
                status=NFTMintStatus.CONFIRMED,
                edition_number=request.edition_number,
                max_editions=request.max_editions,
                minted_at=datetime.now(timezone.utc).isoformat(),
                watermark_verified=True,
                watermark_confidence=0.95,
                gas_used=gas_used
            )
            
            self.minted_nfts[mint_id] = minted
            
            logger.info(f"[{mint_id}] NFT minted successfully. Token ID: {token_id}, TX: {tx_hash}")
            return True, f"NFT minted successfully. Token ID: {token_id}", minted
            
        except Exception as e:
            logger.error(f"[{mint_id}] Minting failed: {str(e)}", exc_info=True)
            return False, f"Minting error: {str(e)}", None

    async def distribute_primary_sale_royalty(
        self,
        mint_id: str,
        sale_price_wei: int
    ) -> Tuple[bool, str, Optional[RoyaltyDistribution]]:
        """
        Distribute royalties from primary sale.
        
        Artist receives configured percentage (default 97.5% after 2.5% platform fee).
        
        Args:
            mint_id: ID of minted NFT
            sale_price_wei: Sale price in wei
            
        Returns:
            Tuple of (success, message, RoyaltyDistribution)
        """
        try:
            minted = self.minted_nfts.get(mint_id)
            if not minted:
                return False, f"Minted NFT not found: {mint_id}", None
            
            artist = self.artist_manager.get_artist_profile(minted.artist_id)
            if not artist:
                return False, f"Artist not found: {minted.artist_id}", None
            
            # Calculate amounts
            platform_fee = int(sale_price_wei * minted.platform_fee_bps / 10000)
            artist_amount = sale_price_wei - platform_fee
            
            # Send to artist wallet
            artist_wallet = next(
                (w.address for w in artist.connected_wallets if w.verified),
                None
            )
            
            if not artist_wallet:
                return False, "Artist has no verified wallet", None
            
            # Transfer funds (in production, use smart contract transfer)
            tx_hash = await self._send_funds(artist_wallet, artist_amount)
            
            if not tx_hash:
                return False, "Transfer failed", None
            
            distribution_id = str(uuid4())
            distribution = RoyaltyDistribution(
                distribution_id=distribution_id,
                artist_id=minted.artist_id,
                artist_wallet=artist_wallet,
                token_id=minted.token_id,
                amount_wei=artist_amount,
                distribution_type=RoyaltyDistributionType.PRIMARY_SALE,
                transaction_hash=tx_hash,
                distributed_at=datetime.now(timezone.utc).isoformat(),
                platform_fee=platform_fee
            )
            
            self.royalty_distributions[distribution_id] = distribution
            
            logger.info(
                f"Primary sale royalty distributed. Artist: {artist_amount} wei, "
                f"Platform: {platform_fee} wei"
            )
            
            return True, "Royalty distributed", distribution
            
        except Exception as e:
            logger.error(f"Royalty distribution failed: {str(e)}", exc_info=True)
            return False, f"Distribution error: {str(e)}", None

    async def handle_secondary_market_sale(
        self,
        token_id: int,
        seller_wallet: str,
        buyer_wallet: str,
        sale_price_wei: int,
        marketplace: str,
        transaction_hash: str
    ) -> Tuple[bool, str, Optional[RoyaltyDistribution]]:
        """
        Handle secondary market sale and distribute royalties.
        
        Process:
        1. Verify NFT ownership
        2. Calculate royalty amount
        3. Distribute to artist
        4. Record transaction
        
        Args:
            token_id: Token ID of NFT
            seller_wallet: Current owner wallet
            buyer_wallet: New owner wallet
            sale_price_wei: Sale price
            marketplace: Marketplace name
            transaction_hash: Blockchain transaction hash
            
        Returns:
            Tuple of (success, message, RoyaltyDistribution)
        """
        try:
            # Find corresponding minted NFT
            minted = next(
                (m for m in self.minted_nfts.values() if m.token_id == token_id),
                None
            )
            
            if not minted:
                return False, f"NFT not found in DCMX system: {token_id}", None
            
            # Calculate royalty
            royalty_amount = int(sale_price_wei * minted.platform_fee_bps / 10000)
            
            # Get artist wallet
            artist = self.artist_manager.get_artist_profile(minted.artist_id)
            if not artist:
                return False, f"Artist not found: {minted.artist_id}", None
            
            artist_wallet = next(
                (w.address for w in artist.connected_wallets if w.verified),
                None
            )
            
            if not artist_wallet:
                return False, "Artist has no verified wallet", None
            
            # Distribute royalty
            royalty_tx = await self._send_funds(artist_wallet, royalty_amount)
            
            if not royalty_tx:
                return False, "Royalty transfer failed", None
            
            # Record secondary market data
            secondary_id = str(uuid4())
            secondary_data = SecondaryMarketData(
                nft_id=str(token_id),
                seller_wallet=seller_wallet,
                buyer_wallet=buyer_wallet,
                sale_price_wei=sale_price_wei,
                marketplace=marketplace,
                transaction_hash=transaction_hash,
                royalty_paid_wei=royalty_amount,
                artist_wallet=artist_wallet,
                sale_timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            self.secondary_market_data[secondary_id] = secondary_data
            
            # Create distribution record
            distribution_id = str(uuid4())
            distribution = RoyaltyDistribution(
                distribution_id=distribution_id,
                artist_id=minted.artist_id,
                artist_wallet=artist_wallet,
                token_id=token_id,
                amount_wei=royalty_amount,
                distribution_type=RoyaltyDistributionType.SECONDARY_SALE,
                transaction_hash=royalty_tx,
                distributed_at=datetime.now(timezone.utc).isoformat(),
                platform_fee=royalty_amount
            )
            
            self.royalty_distributions[distribution_id] = distribution
            
            logger.info(
                f"Secondary market royalty: {royalty_amount} wei to {artist_wallet}"
            )
            
            return True, "Secondary market royalty distributed", distribution
            
        except Exception as e:
            logger.error(f"Secondary market handling failed: {str(e)}", exc_info=True)
            return False, f"Secondary market error: {str(e)}", None

    async def get_artist_nft_portfolio(
        self,
        artist_id: str
    ) -> Tuple[bool, str, List[MintedNFT]]:
        """
        Get all NFTs minted by artist.
        
        Args:
            artist_id: Artist ID
            
        Returns:
            Tuple of (success, message, list of MintedNFT)
        """
        try:
            artist = self.artist_manager.get_artist_profile(artist_id)
            if not artist:
                return False, f"Artist not found: {artist_id}", []
            
            portfolio = [
                nft for nft in self.minted_nfts.values()
                if nft.artist_id == artist_id
            ]
            
            return True, f"Found {len(portfolio)} NFTs", portfolio
            
        except Exception as e:
            logger.error(f"Portfolio fetch failed: {str(e)}", exc_info=True)
            return False, f"Error: {str(e)}", []

    async def get_artist_royalty_history(
        self,
        artist_id: str
    ) -> Tuple[bool, str, List[RoyaltyDistribution]]:
        """
        Get royalty distribution history for artist.
        
        Args:
            artist_id: Artist ID
            
        Returns:
            Tuple of (success, message, list of RoyaltyDistribution)
        """
        try:
            history = [
                d for d in self.royalty_distributions.values()
                if d.artist_id == artist_id
            ]
            
            total_earned = sum(d.amount_wei for d in history)
            
            return True, f"Total earned: {total_earned} wei", history
            
        except Exception as e:
            logger.error(f"Royalty history fetch failed: {str(e)}", exc_info=True)
            return False, f"Error: {str(e)}", []

    # ===== PRIVATE HELPER METHODS =====

    async def _verify_proof_chain(self, proof_chain_id: str) -> bool:
        """
        Verify watermark proof chain is valid and on-chain committed.
        
        In production, queries blockchain or proof storage.
        """
        # Placeholder: In production, query blockchain or IPFS
        return True

    def _create_nft_metadata(
        self,
        request: ArtistMintRequest,
        artist: ArtistProfile,
        artist_wallet: str
    ) -> NFTMetadata:
        """Create complete NFT metadata."""
        return NFTMetadata(
            title=request.track_title,
            artist=artist.artist_name,
            artist_wallet=artist_wallet,
            dcmx_content_hash=request.dcmx_content_hash,
            watermark_proof_chain_id=request.watermark_proof_chain_id,
            edition_number=request.edition_number,
            max_editions=request.max_editions,
            royalty_recipient=artist_wallet,
            royalty_bps_primary=request.royalty_primary_bps,
            royalty_bps_secondary=request.royalty_secondary_bps,
            created_at=datetime.now(timezone.utc).isoformat(),
            description=request.metadata.get("description", "") if request.metadata else ""
        )

    async def _mint_on_blockchain(
        self,
        contract_address: str,
        to_address: str,
        token_id_hint: int,
        metadata_uri: str,
        royalty_recipient: str,
        royalty_bps: int
    ) -> Tuple[Optional[str], int, Optional[int]]:
        """
        Mint NFT on blockchain.
        
        In production, uses web3.py to sign and send transaction.
        For now, returns mock values.
        """
        # Placeholder implementation
        # In production: use self.contract_manager to mint
        tx_hash = f"0x{'1' * 64}"
        token_id = token_id_hint
        gas_used = 85000
        
        logger.info(f"Mock blockchain mint: {tx_hash[:10]}..., Token ID: {token_id}")
        return tx_hash, token_id, gas_used

    async def _send_funds(
        self,
        to_address: str,
        amount_wei: int
    ) -> Optional[str]:
        """
        Send funds to wallet.
        
        In production, uses smart contract transfer.
        For now, returns mock transaction hash.
        """
        # Placeholder implementation
        tx_hash = f"0x{'2' * 64}"
        logger.info(f"Mock transfer: {amount_wei} wei to {to_address[:10]}...")
        return tx_hash

    def export_mint_record(self, mint_id: str) -> Optional[Dict[str, Any]]:
        """Export minted NFT record as dict."""
        minted = self.minted_nfts.get(mint_id)
        if not minted:
            return None
        
        return {
            "mint_id": minted.mint_id,
            "artist_id": minted.artist_id,
            "contract_address": minted.contract_address,
            "token_id": minted.token_id,
            "transaction_hash": minted.transaction_hash,
            "status": minted.status.value,
            "edition": f"{minted.edition_number}/{minted.max_editions}",
            "minted_at": minted.minted_at,
            "watermark_verified": minted.watermark_verified,
            "watermark_confidence": minted.watermark_confidence,
        }
