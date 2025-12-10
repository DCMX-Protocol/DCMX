"""
TRON Smart Contract Interaction Classes

Provides high-level interfaces for interacting with DCMX smart contracts.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from .client import TronClient
from .config import TronConfig

logger = logging.getLogger(__name__)


@dataclass
class ContractDeployment:
    """Result of contract deployment."""
    contract_address: str
    transaction_hash: str
    deployer_address: str
    block_number: int


class BaseContract:
    """Base class for contract interaction."""
    
    def __init__(self, client: TronClient, contract_address: str):
        """
        Initialize contract interface.
        
        Args:
            client: TRON client
            contract_address: Deployed contract address
        """
        self.client = client
        self.contract_address = contract_address
        self.contract = client.get_contract(contract_address)
    
    def call(self, function_name: str, *args, **kwargs) -> Any:
        """Call a read-only contract function."""
        return self.client.call_contract(
            self.contract_address,
            function_name,
            *args,
            **kwargs
        )
    
    def send(self, function_name: str, *args, **kwargs) -> str:
        """Send a state-changing transaction."""
        return self.client.send_contract_transaction(
            self.contract_address,
            function_name,
            *args,
            **kwargs
        )


class DCMXTokenContract(BaseContract):
    """
    DCMXToken (TRC-20) contract interface.
    
    Features:
    - Balance queries
    - Token transfers
    - Minting (authorized)
    - Burning
    """
    
    def name(self) -> str:
        """Get token name."""
        return self.call("name")
    
    def symbol(self) -> str:
        """Get token symbol."""
        return self.call("symbol")
    
    def decimals(self) -> int:
        """Get token decimals."""
        return self.call("decimals")
    
    def total_supply(self) -> int:
        """Get total token supply."""
        return self.call("totalSupply")
    
    def max_supply(self) -> int:
        """Get maximum token supply."""
        return self.call("maxSupply")
    
    def balance_of(self, address: str) -> int:
        """
        Get token balance for address.
        
        Args:
            address: Wallet address
            
        Returns:
            Balance in wei (10^18 units)
        """
        return self.call("balanceOf", address)
    
    def transfer(self, to_address: str, amount: int) -> str:
        """
        Transfer tokens to an address.
        
        Args:
            to_address: Recipient address
            amount: Amount in wei
            
        Returns:
            Transaction hash
        """
        return self.send("transfer", to_address, amount)
    
    def approve(self, spender: str, amount: int) -> str:
        """
        Approve spender to spend tokens.
        
        Args:
            spender: Spender address
            amount: Amount in wei
            
        Returns:
            Transaction hash
        """
        return self.send("approve", spender, amount)
    
    def allowance(self, owner: str, spender: str) -> int:
        """
        Get approved allowance.
        
        Args:
            owner: Token owner
            spender: Spender address
            
        Returns:
            Allowance amount
        """
        return self.call("allowance", owner, spender)
    
    def transfer_from(self, from_address: str, to_address: str, amount: int) -> str:
        """
        Transfer tokens on behalf of another address.
        
        Args:
            from_address: Source address
            to_address: Destination address
            amount: Amount in wei
            
        Returns:
            Transaction hash
        """
        return self.send("transferFrom", from_address, to_address, amount)
    
    def mint(self, to_address: str, amount: int) -> str:
        """
        Mint new tokens (authorized minters only).
        
        Args:
            to_address: Recipient address
            amount: Amount in wei
            
        Returns:
            Transaction hash
        """
        return self.send("mint", to_address, amount)
    
    def burn(self, amount: int) -> str:
        """
        Burn tokens.
        
        Args:
            amount: Amount in wei
            
        Returns:
            Transaction hash
        """
        return self.send("burn", amount)
    
    def add_minter(self, minter_address: str) -> str:
        """
        Add authorized minter (owner only).
        
        Args:
            minter_address: Address to authorize
            
        Returns:
            Transaction hash
        """
        return self.send("addMinter", minter_address)
    
    def remove_minter(self, minter_address: str) -> str:
        """
        Remove authorized minter (owner only).
        
        Args:
            minter_address: Address to remove
            
        Returns:
            Transaction hash
        """
        return self.send("removeMinter", minter_address)


class MusicNFTContract(BaseContract):
    """
    MusicNFT (TRC-721) contract interface.
    
    Features:
    - NFT minting with metadata
    - Ownership queries
    - Transfers
    - Royalty info (ERC-2981)
    """
    
    def name(self) -> str:
        """Get NFT collection name."""
        return self.call("name")
    
    def symbol(self) -> str:
        """Get NFT collection symbol."""
        return self.call("symbol")
    
    def total_supply(self) -> int:
        """Get total NFTs minted."""
        return self.call("totalSupply")
    
    def balance_of(self, owner: str) -> int:
        """
        Get NFT balance for owner.
        
        Args:
            owner: Wallet address
            
        Returns:
            Number of NFTs owned
        """
        return self.call("balanceOf", owner)
    
    def owner_of(self, token_id: int) -> str:
        """
        Get owner of NFT.
        
        Args:
            token_id: Token ID
            
        Returns:
            Owner address
        """
        return self.call("ownerOf", token_id)
    
    def mint_music(
        self,
        to_address: str,
        title: str,
        artist: str,
        content_hash: str,
        edition_number: int,
        max_editions: int,
        royalty_bps: int = 1000
    ) -> str:
        """
        Mint a music NFT.
        
        Args:
            to_address: Recipient address
            title: Song title
            artist: Artist name
            content_hash: SHA-256 hash of audio file
            edition_number: Edition number (1-based)
            max_editions: Total editions
            royalty_bps: Royalty percentage in basis points (1000 = 10%)
            
        Returns:
            Transaction hash
        """
        return self.send(
            "mintMusic",
            to_address,
            title,
            artist,
            content_hash,
            edition_number,
            max_editions,
            royalty_bps
        )
    
    def get_metadata(self, token_id: int) -> Dict[str, Any]:
        """
        Get NFT metadata.
        
        Args:
            token_id: Token ID
            
        Returns:
            Metadata dict
        """
        result = self.call("getMetadata", token_id)
        return {
            "title": result[0],
            "artist": result[1],
            "content_hash": result[2],
            "edition_number": result[3],
            "max_editions": result[4],
            "artist_wallet": result[5],
        }
    
    def token_uri(self, token_id: int) -> str:
        """
        Get token URI.
        
        Args:
            token_id: Token ID
            
        Returns:
            Token URI
        """
        return self.call("tokenURI", token_id)
    
    def transfer_from(self, from_address: str, to_address: str, token_id: int) -> str:
        """
        Transfer NFT.
        
        Args:
            from_address: Current owner
            to_address: New owner
            token_id: Token ID
            
        Returns:
            Transaction hash
        """
        return self.send("transferFrom", from_address, to_address, token_id)
    
    def approve(self, to_address: str, token_id: int) -> str:
        """
        Approve address for token.
        
        Args:
            to_address: Approved address
            token_id: Token ID
            
        Returns:
            Transaction hash
        """
        return self.send("approve", to_address, token_id)
    
    def set_approval_for_all(self, operator: str, approved: bool) -> str:
        """
        Set operator approval for all tokens.
        
        Args:
            operator: Operator address
            approved: Approval status
            
        Returns:
            Transaction hash
        """
        return self.send("setApprovalForAll", operator, approved)
    
    def royalty_info(self, token_id: int, sale_price: int) -> Tuple[str, int]:
        """
        Get royalty info (ERC-2981).
        
        Args:
            token_id: Token ID
            sale_price: Sale price
            
        Returns:
            (recipient_address, royalty_amount)
        """
        result = self.call("royaltyInfo", token_id, sale_price)
        return (result[0], result[1])


class ComplianceRegistryContract(BaseContract):
    """
    ComplianceRegistry contract interface.
    
    Features:
    - Legal document acceptance tracking
    - Document version registration
    - GDPR/CCPA deletion requests
    """
    
    def register_document_version(
        self,
        doc_type: int,
        version: str,
        document_hash: str
    ) -> str:
        """
        Register a document version (owner only).
        
        Args:
            doc_type: Document type enum value (0-4)
            version: Version string (e.g., "1.0")
            document_hash: SHA-256 hash of document
            
        Returns:
            Transaction hash
        """
        return self.send("registerDocumentVersion", doc_type, version, document_hash)
    
    def record_acceptance(
        self,
        doc_type: int,
        version: str,
        document_hash: str,
        ip_address: str = ""
    ) -> str:
        """
        Record user acceptance of a document.
        
        Args:
            doc_type: Document type enum value
            version: Document version
            document_hash: Document hash
            ip_address: User IP address (optional)
            
        Returns:
            Transaction hash
        """
        return self.send("recordAcceptance", doc_type, version, document_hash, ip_address)
    
    def get_latest_acceptance(self, wallet: str, doc_type: int) -> Dict[str, Any]:
        """
        Get latest acceptance record.
        
        Args:
            wallet: User wallet address
            doc_type: Document type
            
        Returns:
            Acceptance record
        """
        result = self.call("getLatestAcceptance", wallet, doc_type)
        return {
            "record_id": result[0],
            "document_hash": result[1],
            "version": result[2],
            "accepted_at": result[3],
            "is_valid": result[4],
        }
    
    def has_accepted(self, wallet: str, doc_type: int, required_version: str = "") -> bool:
        """
        Check if user has accepted a document.
        
        Args:
            wallet: User wallet address
            doc_type: Document type
            required_version: Required version (empty = any version)
            
        Returns:
            True if accepted
        """
        return self.call("hasAccepted", wallet, doc_type, required_version)
    
    def request_deletion(self, request_type: str) -> str:
        """
        Request data deletion (GDPR/CCPA).
        
        Args:
            request_type: "GDPR" or "CCPA"
            
        Returns:
            Transaction hash
        """
        return self.send("requestDeletion", request_type)
    
    def get_deletion_request(self, wallet: str) -> Dict[str, Any]:
        """
        Get deletion request status.
        
        Args:
            wallet: User wallet address
            
        Returns:
            Deletion request info
        """
        result = self.call("getDeletionRequest", wallet)
        return {
            "requested_at": result[0],
            "completed_at": result[1],
            "is_completed": result[2],
            "request_type": result[3],
        }
    
    def complete_deletion(self, wallet: str) -> str:
        """
        Mark deletion as completed (owner only).
        
        Args:
            wallet: User wallet address
            
        Returns:
            Transaction hash
        """
        return self.send("completeDeletion", wallet)
    
    def total_acceptances(self) -> int:
        """Get total number of acceptance records."""
        return self.call("totalAcceptances")


class RewardVaultContract(BaseContract):
    """
    RewardVault contract interface.
    
    Features:
    - Reward claim submission
    - Claim verification
    - Pool management
    """
    
    def submit_claim(
        self,
        reward_type: int,
        amount: int,
        proof_hash: str
    ) -> str:
        """
        Submit a reward claim.
        
        Args:
            reward_type: Reward type enum (0-4)
            amount: Reward amount in wei
            proof_hash: Hash of activity proof
            
        Returns:
            Transaction hash
        """
        return self.send("submitClaim", reward_type, amount, proof_hash)
    
    def verify_claim(self, claim_id: int, approved: bool) -> str:
        """
        Verify a claim (verifier only).
        
        Args:
            claim_id: Claim ID
            approved: Approval status
            
        Returns:
            Transaction hash
        """
        return self.send("verifyClaim", claim_id, approved)
    
    def get_claim(self, claim_id: int) -> Dict[str, Any]:
        """
        Get claim details.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            Claim info
        """
        result = self.call("getClaim", claim_id)
        return {
            "claimant": result[0],
            "reward_type": result[1],
            "amount": result[2],
            "timestamp": result[3],
            "claimed": result[4],
            "verified": result[5],
        }
    
    def get_pool_status(self, reward_type: int) -> Dict[str, Any]:
        """
        Get reward pool status.
        
        Args:
            reward_type: Reward type
            
        Returns:
            Pool status
        """
        result = self.call("getPoolStatus", reward_type)
        return {
            "total_allocated": result[0],
            "total_claimed": result[1],
            "remaining": result[2],
            "daily_limit": result[3],
            "active": result[4],
        }
    
    def get_user_daily_claimed(self, user: str, reward_type: int) -> int:
        """
        Get user's daily claimed amount.
        
        Args:
            user: User address
            reward_type: Reward type
            
        Returns:
            Claimed amount today
        """
        return self.call("getUserDailyClaimed", user, reward_type)
    
    def add_verifier(self, verifier: str) -> str:
        """
        Add authorized verifier (owner only).
        
        Args:
            verifier: Verifier address
            
        Returns:
            Transaction hash
        """
        return self.send("addVerifier", verifier)
    
    def total_claims(self) -> int:
        """Get total number of claims."""
        return self.call("totalClaims")


class RoyaltyDistributorContract(BaseContract):
    """
    RoyaltyDistributor contract interface.
    
    Features:
    - NFT sale tracking
    - Royalty payment processing
    - Royalty splits for collaborations
    """
    
    def record_sale(
        self,
        token_id: int,
        seller: str,
        buyer: str,
        sale_price: int,
        payment_token: str
    ) -> str:
        """
        Record an NFT sale.
        
        Args:
            token_id: NFT token ID
            seller: Seller address
            buyer: Buyer address
            sale_price: Sale price
            payment_token: Payment token address (address(0) for TRX)
            
        Returns:
            Transaction hash
        """
        return self.send("recordSale", token_id, seller, buyer, sale_price, payment_token)
    
    def pay_royalty(self, sale_id: int, value: int = 0) -> str:
        """
        Execute royalty payment.
        
        Args:
            sale_id: Sale ID
            value: TRX value to send (if paying in TRX)
            
        Returns:
            Transaction hash
        """
        kwargs = {}
        if value > 0:
            kwargs["call_value"] = value
        return self.send("payRoyalty", sale_id, **kwargs)
    
    def get_sale(self, sale_id: int) -> Dict[str, Any]:
        """
        Get sale details.
        
        Args:
            sale_id: Sale ID
            
        Returns:
            Sale info
        """
        result = self.call("getSale", sale_id)
        return {
            "token_id": result[0],
            "seller": result[1],
            "buyer": result[2],
            "sale_price": result[3],
            "royalty_amount": result[4],
            "royalty_paid": result[5],
        }
    
    def set_royalty_splits(
        self,
        token_id: int,
        recipients: List[str],
        shares: List[int]
    ) -> str:
        """
        Set royalty splits for collaboration.
        
        Args:
            token_id: NFT token ID
            recipients: List of recipient addresses
            shares: List of shares in basis points (must sum to 10000)
            
        Returns:
            Transaction hash
        """
        return self.send("setRoyaltySplits", token_id, recipients, shares)
    
    def get_royalty_splits(self, token_id: int) -> Dict[str, Any]:
        """
        Get royalty splits for a token.
        
        Args:
            token_id: NFT token ID
            
        Returns:
            Splits info
        """
        result = self.call("getRoyaltySplits", token_id)
        return {
            "recipients": result[0],
            "shares": result[1],
        }
    
    def total_royalties_earned(self, artist: str) -> int:
        """
        Get total royalties earned by artist.
        
        Args:
            artist: Artist address
            
        Returns:
            Total earned
        """
        return self.call("totalRoyaltiesEarned", artist)
    
    def total_sales(self) -> int:
        """Get total number of sales."""
        return self.call("totalSales")
