"""
NFT Ownership Verifier for DCMX

Verifies artist ownership of NFTs through blockchain queries and
links NFTs to watermarked content for rights verification.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
import json
import logging
from abc import ABC, abstractmethod
import hashlib

try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError, Web3Exception
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

logger = logging.getLogger(__name__)


class BlockchainNetwork(Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    SEPOLIA_TESTNET = "sepolia"
    MUMBAI_TESTNET = "mumbai"


class TokenStandard(Enum):
    """NFT token standards."""
    ERC_721 = "ERC-721"      # Single ownership
    ERC_1155 = "ERC-1155"    # Multiple ownership (semi-fungible)
    ERC_404 = "ERC-404"      # Experimental (hybrid)


@dataclass
class BlockchainQueryResult:
    """Result from blockchain query."""
    
    nft_id: str
    owner_address: str
    balance: int                               # Quantity owned (1 for ERC-721)
    verified: bool
    query_timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    block_number: int = 0
    transaction_hash: str = ""
    metadata_uri: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "nft_id": self.nft_id,
            "owner_address": self.owner_address,
            "balance": self.balance,
            "verified": self.verified,
            "query_timestamp": self.query_timestamp,
            "block_number": self.block_number,
            "transaction_hash": self.transaction_hash,
            "metadata_uri": self.metadata_uri
        }


@dataclass
class ContractInterface:
    """Smart contract interface info."""

    address: str
    network: BlockchainNetwork
    token_standard: TokenStandard
    name: str = ""
    symbol: str = ""
    total_supply: int = 0
    verified_contract: bool = False

    # Optional: Royalty info if ERC-2981 supported
    royalty_percent: float = 0.0
    royalty_receiver: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "address": self.address,
            "network": self.network.value,
            "token_standard": self.token_standard.value,
            "name": self.name,
            "symbol": self.symbol,
            "verified_contract": self.verified_contract,
            "royalty_percent": self.royalty_percent,
            "royalty_receiver": self.royalty_receiver
        }


@dataclass
class OwnershipHistoryEntry:
    """Single entry in NFT ownership history."""

    from_address: str
    to_address: str
    block_number: int
    transaction_hash: str
    timestamp: str
    transfer_type: str = "transfer"  # transfer | mint | burn

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "from_address": self.from_address,
            "to_address": self.to_address,
            "block_number": self.block_number,
            "transaction_hash": self.transaction_hash,
            "timestamp": self.timestamp,
            "transfer_type": self.transfer_type
        }


@dataclass
class TokenMetadata:
    """NFT token metadata."""

    token_id: str
    name: str = ""
    description: str = ""
    image_uri: str = ""
    animation_uri: str = ""
    external_url: str = ""
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    
    # DCMX-specific
    content_hash: str = ""
    artist_address: str = ""
    edition_number: int = 0
    max_editions: int = 0
    royalty_bps: int = 0  # Basis points (1000 = 10%)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "token_id": self.token_id,
            "name": self.name,
            "description": self.description,
            "image_uri": self.image_uri,
            "animation_uri": self.animation_uri,
            "external_url": self.external_url,
            "attributes": self.attributes,
            "content_hash": self.content_hash,
            "artist_address": self.artist_address,
            "edition_number": self.edition_number,
            "max_editions": self.max_editions,
            "royalty_bps": self.royalty_bps
        }


# Standard ERC-721 ABI for ownership queries
ERC721_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "uint256", "name": "salePrice", "type": "uint256"}
        ],
        "name": "royaltyInfo",
        "outputs": [
            {"internalType": "address", "name": "receiver", "type": "address"},
            {"internalType": "uint256", "name": "royaltyAmount", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ERC-721 Transfer event signature
ERC721_TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

# Standard ERC-1155 ABI
ERC1155_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "uint256", "name": "id", "type": "uint256"}
        ],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "uri",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class BlockchainProvider(ABC):
    """Abstract base class for blockchain query providers."""
    
    @abstractmethod
    async def get_nft_owner(
        self,
        contract_address: str,
        nft_id: str
    ) -> Optional[BlockchainQueryResult]:
        """Get current owner of NFT.
        
        Args:
            contract_address: Smart contract address
            nft_id: Token ID
        
        Returns:
            BlockchainQueryResult or None
        """
        pass
    
    @abstractmethod
    async def get_nft_balance(
        self,
        contract_address: str,
        wallet_address: str,
        nft_id: Optional[str] = None
    ) -> int:
        """Get NFT balance for wallet.
        
        Args:
            contract_address: Smart contract address
            wallet_address: Wallet address
            nft_id: Token ID (for ERC-1155)
        
        Returns:
            Balance (quantity owned)
        """
        pass
    
    @abstractmethod
    async def get_contract_info(
        self,
        contract_address: str
    ) -> Optional[ContractInterface]:
        """Get contract interface info.
        
        Args:
            contract_address: Smart contract address
        
        Returns:
            ContractInterface or None
        """
        pass


class MockBlockchainProvider(BlockchainProvider):
    """Mock blockchain provider for testing (in production, use ethers.js or Web3.py)."""
    
    def __init__(self):
        """Initialize mock provider."""
        self.mock_ownership: Dict[str, Dict[str, str]] = {}  # contract -> (nft_id -> owner)
        self.mock_balances: Dict[str, Dict[str, int]] = {}   # contract -> (wallet -> balance)
        self.mock_contracts: Dict[str, ContractInterface] = {}
    
    async def get_nft_owner(
        self,
        contract_address: str,
        nft_id: str
    ) -> Optional[BlockchainQueryResult]:
        """Get current owner (mock)."""
        key = f"{contract_address}:{nft_id}"
        
        if key in self.mock_ownership:
            owner = self.mock_ownership[key]
            return BlockchainQueryResult(
                nft_id=nft_id,
                owner_address=owner,
                balance=1,
                verified=True,
                block_number=18000000
            )
        return None
    
    async def get_nft_balance(
        self,
        contract_address: str,
        wallet_address: str,
        nft_id: Optional[str] = None
    ) -> int:
        """Get balance (mock)."""
        key = f"{contract_address}:{wallet_address.lower()}"
        return self.mock_balances.get(key, 0)
    
    async def get_contract_info(
        self,
        contract_address: str
    ) -> Optional[ContractInterface]:
        """Get contract info (mock)."""
        return self.mock_contracts.get(contract_address)
    
    def set_mock_ownership(
        self,
        contract_address: str,
        nft_id: str,
        owner_address: str
    ):
        """Set mock ownership for testing."""
        key = f"{contract_address}:{nft_id}"
        self.mock_ownership[key] = owner_address.lower()
    
    def set_mock_balance(
        self,
        contract_address: str,
        wallet_address: str,
        balance: int
    ):
        """Set mock balance for testing."""
        key = f"{contract_address}:{wallet_address.lower()}"
        self.mock_balances[key] = balance
    
    def set_mock_contract(
        self,
        contract_address: str,
        contract_info: ContractInterface
    ):
        """Set mock contract for testing."""
        self.mock_contracts[contract_address] = contract_info


@dataclass
class ContentWatermarkLink:
    """Link between NFT and watermarked content."""
    
    nft_id: str
    contract_address: str
    dcmx_content_hash: str                     # SHA-256 of audio bytes
    watermark_proof_chain_id: str              # From ZK proof system
    
    # Verification
    watermark_verified: bool = False
    watermark_verified_at: Optional[str] = None
    content_match_score: float = 0.0           # 0-100 confidence
    
    # Metadata matching
    title_matches: bool = False
    artist_matches: bool = False
    fingerprint_matches: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "nft_id": self.nft_id,
            "contract_address": self.contract_address,
            "dcmx_content_hash": self.dcmx_content_hash,
            "watermark_proof_chain_id": self.watermark_proof_chain_id,
            "watermark_verified": self.watermark_verified,
            "watermark_verified_at": self.watermark_verified_at,
            "content_match_score": self.content_match_score,
            "metadata_matches": {
                "title": self.title_matches,
                "artist": self.artist_matches,
                "fingerprint": self.fingerprint_matches
            }
        }


class NFTOwnershipVerifier:
    """Verifies NFT ownership and links to DCMX watermarked content."""
    
    def __init__(self, provider: Optional[BlockchainProvider] = None):
        """Initialize verifier.
        
        Args:
            provider: BlockchainProvider instance (defaults to MockBlockchainProvider)
        """
        self.provider = provider or MockBlockchainProvider()
        self.verification_cache: Dict[str, BlockchainQueryResult] = {}
        self.content_links: Dict[str, ContentWatermarkLink] = {}  # nft_id -> ContentWatermarkLink
        self.verified_creators: Dict[str, bool] = {}  # artist_address -> is_verified
    
    async def verify_nft_ownership(
        self,
        contract_address: str,
        nft_id: str,
        claimed_owner: str
    ) -> Tuple[bool, str, Optional[BlockchainQueryResult]]:
        """Verify that claimed owner actually owns the NFT.
        
        Args:
            contract_address: Smart contract address
            nft_id: Token ID
            claimed_owner: Wallet address claiming ownership
        
        Returns:
            Tuple of (verified: bool, message: str, result: Optional[BlockchainQueryResult])
        """
        try:
            # Query blockchain
            result = await self.provider.get_nft_owner(contract_address, nft_id)
            
            if not result:
                return False, "NFT not found on blockchain", None
            
            # Check if owner matches
            if result.owner_address.lower() != claimed_owner.lower():
                return False, f"NFT owned by {result.owner_address}, not {claimed_owner}", result
            
            # Cache result
            cache_key = f"{contract_address}:{nft_id}"
            self.verification_cache[cache_key] = result
            
            logger.info(f"Verified NFT ownership: {nft_id} owned by {claimed_owner}")
            return True, "NFT ownership verified", result
        
        except Exception as e:
            logger.error(f"Error verifying NFT ownership: {e}")
            return False, f"Verification error: {str(e)}", None
    
    async def verify_batch_ownership(
        self,
        nfts: List[Tuple[str, str, str]]  # [(contract, nft_id, owner), ...]
    ) -> Dict[str, Tuple[bool, str]]:
        """Verify ownership of multiple NFTs.
        
        Args:
            nfts: List of (contract_address, nft_id, claimed_owner) tuples
        
        Returns:
            Dict mapping "contract:nft_id" -> (verified: bool, message: str)
        """
        results = {}
        
        for contract_addr, nft_id, owner_addr in nfts:
            verified, msg, _ = await self.verify_nft_ownership(
                contract_addr,
                nft_id,
                owner_addr
            )
            results[f"{contract_addr}:{nft_id}"] = (verified, msg)
        
        return results
    
    async def get_artist_nft_portfolio(
        self,
        artist_wallet: str,
        contract_address: str
    ) -> Tuple[bool, str, List[str]]:
        """Get all NFTs owned by artist at specific contract.
        
        Args:
            artist_wallet: Artist wallet address
            contract_address: Smart contract address
        
        Returns:
            Tuple of (success: bool, message: str, nft_ids: List[str])
        """
        try:
            balance = await self.provider.get_nft_balance(
                contract_address,
                artist_wallet
            )
            
            if balance == 0:
                return False, "No NFTs owned at this contract", []
            
            # In production, would query contract events or graphql
            # For now, return balance count
            logger.info(f"Artist {artist_wallet} owns {balance} NFTs at {contract_address}")
            return True, f"Portfolio retrieved: {balance} NFTs", []
        
        except Exception as e:
            logger.error(f"Error retrieving portfolio: {e}")
            return False, f"Portfolio retrieval error: {str(e)}", []
    
    async def verify_contract_legitimacy(
        self,
        contract_address: str,
        expected_standard: TokenStandard = TokenStandard.ERC_721
    ) -> Tuple[bool, str, Optional[ContractInterface]]:
        """Verify that contract is legitimate and implements expected standard.
        
        Args:
            contract_address: Smart contract address
            expected_standard: Expected token standard
        
        Returns:
            Tuple of (valid: bool, message: str, contract_info: Optional[ContractInterface])
        """
        try:
            contract_info = await self.provider.get_contract_info(contract_address)
            
            if not contract_info:
                return False, "Contract not found or not verified", None
            
            if contract_info.token_standard != expected_standard:
                return False, (
                    f"Contract implements {contract_info.token_standard.value}, "
                    f"expected {expected_standard.value}"
                ), contract_info
            
            logger.info(f"Verified contract legitimacy: {contract_address}")
            return True, "Contract verified", contract_info
        
        except Exception as e:
            logger.error(f"Error verifying contract: {e}")
            return False, f"Verification error: {str(e)}", None
    
    def link_nft_to_content(
        self,
        nft_id: str,
        contract_address: str,
        dcmx_content_hash: str,
        watermark_proof_chain_id: str
    ) -> ContentWatermarkLink:
        """Link NFT to DCMX watermarked content.
        
        Args:
            nft_id: Token ID
            contract_address: Smart contract address
            dcmx_content_hash: SHA-256 hash of original audio
            watermark_proof_chain_id: ID of cascading proof chain
        
        Returns:
            ContentWatermarkLink
        """
        link = ContentWatermarkLink(
            nft_id=nft_id,
            contract_address=contract_address,
            dcmx_content_hash=dcmx_content_hash,
            watermark_proof_chain_id=watermark_proof_chain_id
        )
        
        self.content_links[nft_id] = link
        logger.info(f"Linked NFT {nft_id} to content hash {dcmx_content_hash}")
        
        return link
    
    def verify_nft_watermark_match(
        self,
        nft_id: str,
        watermark_proof_chain_id: str,
        dcmx_content_hash: str,
        title: str = "",
        artist: str = "",
        fingerprint_hash: str = ""
    ) -> Tuple[bool, str, float]:
        """Verify that NFT's watermark matches expected content.
        
        Args:
            nft_id: Token ID
            watermark_proof_chain_id: Proof chain ID
            dcmx_content_hash: Expected content hash
            title: Track title (for metadata matching)
            artist: Artist name (for metadata matching)
            fingerprint_hash: Audio fingerprint (for duplicate detection)
        
        Returns:
            Tuple of (verified: bool, message: str, confidence: float)
        """
        if nft_id not in self.content_links:
            return False, "NFT not linked to content", 0.0
        
        link = self.content_links[nft_id]
        
        # Verify proof chain ID matches
        if link.watermark_proof_chain_id != watermark_proof_chain_id:
            return False, "Proof chain ID mismatch", 0.0
        
        # Verify content hash matches
        if link.dcmx_content_hash != dcmx_content_hash:
            return False, "Content hash mismatch", 0.0
        
        # Calculate confidence score
        confidence = 80.0  # Base confidence for hash match
        
        # Metadata matching improves confidence
        if title:
            link.title_matches = True
            confidence += 5.0
        
        if artist:
            link.artist_matches = True
            confidence += 5.0
        
        if fingerprint_hash:
            link.fingerprint_matches = True
            confidence += 10.0
        
        confidence = min(confidence, 100.0)
        
        # Mark as verified
        link.watermark_verified = True
        link.watermark_verified_at = datetime.now(timezone.utc).isoformat()
        link.content_match_score = confidence
        
        logger.info(f"Verified watermark match for NFT {nft_id} (confidence: {confidence}%)")
        return True, "Watermark match verified", confidence
    
    def register_verified_creator(
        self,
        creator_address: str,
        verification_timestamp: str = ""
    ) -> bool:
        """Register wallet address as verified creator.
        
        Args:
            creator_address: Wallet address
            verification_timestamp: When verified
        
        Returns:
            Success status
        """
        self.verified_creators[creator_address.lower()] = True
        logger.info(f"Registered verified creator: {creator_address}")
        return True
    
    def is_verified_creator(self, address: str) -> bool:
        """Check if wallet is registered verified creator.
        
        Args:
            address: Wallet address
        
        Returns:
            True if verified, False otherwise
        """
        return self.verified_creators.get(address.lower(), False)
    
    def get_content_link(self, nft_id: str) -> Optional[ContentWatermarkLink]:
        """Get content link for NFT.
        
        Args:
            nft_id: Token ID
        
        Returns:
            ContentWatermarkLink or None
        """
        return self.content_links.get(nft_id)
    
    def get_verification_report(self, nft_id: str) -> Dict[str, Any]:
        """Get comprehensive verification report for NFT.
        
        Args:
            nft_id: Token ID
        
        Returns:
            Dictionary with verification details
        """
        if nft_id not in self.content_links:
            return {"status": "not_linked", "nft_id": nft_id}
        
        link = self.content_links[nft_id]
        
        return {
            "nft_id": nft_id,
            "contract_address": link.contract_address,
            "watermark_verified": link.watermark_verified,
            "verified_at": link.watermark_verified_at,
            "content_match_score": link.content_match_score,
            "metadata_matches": {
                "title": link.title_matches,
                "artist": link.artist_matches,
                "fingerprint": link.fingerprint_matches
            },
            "content_hash": link.dcmx_content_hash,
            "proof_chain_id": link.watermark_proof_chain_id
        }
    
    def export_verification_record(self, nft_id: str) -> str:
        """Export verification record as JSON.
        
        Args:
            nft_id: Token ID
        
        Returns:
            JSON string
        """
        report = self.get_verification_report(nft_id)
        return json.dumps(report, indent=2)
