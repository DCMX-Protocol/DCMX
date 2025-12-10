"""TRON smart contract interaction classes."""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .client import TronClient
from .config import TronConfig

logger = logging.getLogger(__name__)


@dataclass
class ContractCallResult:
    """Result of a contract function call."""
    success: bool
    transaction_hash: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Any] = None


class BaseContract:
    """Base class for contract interactions."""
    
    def __init__(self, client: TronClient, contract_address: str):
        """
        Initialize contract wrapper.
        
        Args:
            client: TronClient instance
            contract_address: Contract address on blockchain
        """
        self.client = client
        self.contract_address = contract_address
        self.contract = client.get_contract(contract_address)
        logger.info(f"{self.__class__.__name__} initialized: {contract_address}")
    
    def _call_function(
        self,
        function_name: str,
        *args,
        fee_limit: int = 100_000_000,
        **kwargs
    ) -> ContractCallResult:
        """
        Call a contract function.
        
        Args:
            function_name: Function name
            *args: Function arguments
            fee_limit: Max fee in SUN
            
        Returns:
            ContractCallResult
        """
        try:
            result = self.client.call_contract_function(
                self.contract_address,
                function_name,
                *args,
                fee_limit=fee_limit,
                **kwargs
            )
            
            tx_hash = result.get('txid')
            return ContractCallResult(
                success=True,
                transaction_hash=tx_hash,
                data=result
            )
            
        except Exception as e:
            logger.error(f"Contract call failed: {function_name} - {e}")
            return ContractCallResult(
                success=False,
                error=str(e)
            )


class DCMXTokenContract(BaseContract):
    """DCMX TRC-20 token contract wrapper."""
    
    def get_balance(self, address: str) -> int:
        """Get token balance for address."""
        try:
            balance = self.contract.functions.balanceOf(address)
            return int(balance)
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0
    
    def get_total_supply(self) -> int:
        """Get total token supply."""
        try:
            return int(self.contract.functions.totalSupply())
        except Exception as e:
            logger.error(f"Failed to get total supply: {e}")
            return 0
    
    def transfer(self, to_address: str, amount: int) -> ContractCallResult:
        """
        Transfer tokens to address.
        
        Args:
            to_address: Recipient address
            amount: Amount in smallest unit (10^-18)
            
        Returns:
            ContractCallResult
        """
        return self._call_function('transfer', to_address, amount)
    
    def approve(self, spender: str, amount: int) -> ContractCallResult:
        """Approve spender to use tokens."""
        return self._call_function('approve', spender, amount)
    
    def mint(self, to_address: str, amount: int) -> ContractCallResult:
        """
        Mint new tokens (admin only).
        
        Args:
            to_address: Recipient address
            amount: Amount to mint
            
        Returns:
            ContractCallResult
        """
        return self._call_function('mint', to_address, amount)
    
    def burn(self, amount: int) -> ContractCallResult:
        """Burn tokens from sender's balance."""
        return self._call_function('burn', amount)


class MusicNFTContract(BaseContract):
    """Music NFT TRC-721 contract wrapper."""
    
    def mint(
        self,
        to_address: str,
        title: str,
        artist: str,
        content_hash: str,
        edition: int,
        max_editions: int,
        royalty_bps: int = 1000,
        royalty_recipient: Optional[str] = None
    ) -> ContractCallResult:
        """
        Mint a music NFT.
        
        Args:
            to_address: Owner address
            title: Track title
            artist: Artist name
            content_hash: Content hash
            edition: Edition number
            max_editions: Max editions
            royalty_bps: Royalty basis points (1000 = 10%)
            royalty_recipient: Royalty recipient address
            
        Returns:
            ContractCallResult
        """
        recipient = royalty_recipient or to_address
        
        return self._call_function(
            'mint',
            to_address,
            title,
            artist,
            content_hash,
            edition,
            max_editions,
            royalty_bps,
            recipient,
            fee_limit=200_000_000  # Higher limit for minting
        )
    
    def get_owner(self, token_id: int) -> Optional[str]:
        """Get NFT owner address."""
        try:
            return self.contract.functions.ownerOf(token_id)
        except Exception as e:
            logger.error(f"Failed to get owner: {e}")
            return None
    
    def get_metadata(self, token_id: int) -> Optional[Dict[str, Any]]:
        """Get NFT metadata."""
        try:
            metadata = self.contract.functions.tokenMetadata(token_id)
            return {
                'title': metadata[0],
                'artist': metadata[1],
                'content_hash': metadata[2],
                'edition': int(metadata[3]),
                'max_editions': int(metadata[4]),
                'royalty_bps': int(metadata[5]),
                'royalty_recipient': metadata[6],
            }
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return None
    
    def transfer(self, to_address: str, token_id: int) -> ContractCallResult:
        """Transfer NFT to address."""
        return self._call_function('transfer', to_address, token_id)


class ComplianceRegistryContract(BaseContract):
    """Compliance registry contract wrapper."""
    
    def register_document_version(
        self,
        document_type: int,
        version: str,
        document_hash: str
    ) -> ContractCallResult:
        """
        Register a document version.
        
        Args:
            document_type: Document type enum value
            version: Version string
            document_hash: Document hash (bytes32)
            
        Returns:
            ContractCallResult
        """
        # Convert hash to bytes32 format
        if not document_hash.startswith('0x'):
            document_hash = '0x' + document_hash
        
        return self._call_function(
            'registerDocumentVersion',
            document_type,
            version,
            document_hash
        )
    
    def record_acceptance(
        self,
        user_address: str,
        document_hash: str,
        document_type: int,
        version: str,
        ip_address: str
    ) -> ContractCallResult:
        """
        Record user acceptance of a document.
        
        Args:
            user_address: User's wallet address
            document_hash: Document hash
            document_type: Document type enum
            version: Document version
            ip_address: Hashed IP address
            
        Returns:
            ContractCallResult
        """
        if not document_hash.startswith('0x'):
            document_hash = '0x' + document_hash
        
        return self._call_function(
            'recordAcceptance',
            user_address,
            document_hash,
            document_type,
            version,
            ip_address
        )
    
    def request_data_deletion(self, reason: str) -> ContractCallResult:
        """Request data deletion (GDPR/CCPA)."""
        return self._call_function('requestDataDeletion', reason)
    
    def verify_acceptance(
        self,
        user_address: str,
        document_type: int,
        document_hash: str
    ) -> bool:
        """Verify if user has accepted a document."""
        try:
            if not document_hash.startswith('0x'):
                document_hash = '0x' + document_hash
            
            return self.contract.functions.verifyAcceptance(
                user_address,
                document_type,
                document_hash
            )
        except Exception as e:
            logger.error(f"Failed to verify acceptance: {e}")
            return False


class RewardVaultContract(BaseContract):
    """Reward vault contract wrapper."""
    
    def submit_claim(
        self,
        claim_type: int,
        proof_hash: str,
        amount: int
    ) -> ContractCallResult:
        """
        Submit a reward claim.
        
        Args:
            claim_type: Claim type (0=SHARING, 1=LISTENING, 2=BANDWIDTH)
            proof_hash: Proof hash (bytes32)
            amount: Reward amount
            
        Returns:
            ContractCallResult
        """
        if not proof_hash.startswith('0x'):
            proof_hash = '0x' + proof_hash
        
        return self._call_function('submitClaim', claim_type, proof_hash, amount)
    
    def verify_claim(self, claim_id: int, approved: bool) -> ContractCallResult:
        """Verify a claim (admin only)."""
        return self._call_function('verifyClaim', claim_id, approved)
    
    def claim_rewards(self, claim_id: int) -> ContractCallResult:
        """Claim verified rewards."""
        return self._call_function('claimRewards', claim_id)
    
    def get_user_rewards(self, user_address: str) -> Dict[str, int]:
        """Get user's pending and claimed rewards."""
        try:
            result = self.contract.functions.getUserRewards(user_address)
            return {
                'pending': int(result[0]),
                'claimed': int(result[1]),
            }
        except Exception as e:
            logger.error(f"Failed to get user rewards: {e}")
            return {'pending': 0, 'claimed': 0}


class RoyaltyDistributorContract(BaseContract):
    """Royalty distributor contract wrapper."""
    
    def set_royalty_split(
        self,
        nft_contract: str,
        nft_token_id: int,
        recipients: List[str],
        percentages: List[int]
    ) -> ContractCallResult:
        """
        Set royalty split for an NFT.
        
        Args:
            nft_contract: NFT contract address
            nft_token_id: Token ID
            recipients: List of recipient addresses
            percentages: List of percentages (basis points)
            
        Returns:
            ContractCallResult
        """
        return self._call_function(
            'setRoyaltySplit',
            nft_contract,
            nft_token_id,
            recipients,
            percentages,
            fee_limit=150_000_000
        )
    
    def record_sale(
        self,
        nft_contract: str,
        nft_token_id: int,
        seller: str,
        buyer: str,
        sale_price: int
    ) -> ContractCallResult:
        """Record an NFT sale."""
        return self._call_function(
            'recordSale',
            nft_contract,
            nft_token_id,
            seller,
            buyer,
            sale_price
        )
    
    def distribute_royalties(self, sale_id: int) -> ContractCallResult:
        """Distribute royalties for a sale."""
        return self._call_function('distributeRoyalties', sale_id)
    
    def withdraw_royalties(self) -> ContractCallResult:
        """Withdraw pending royalties."""
        return self._call_function('withdrawRoyalties')
    
    def get_pending_royalties(self, recipient: str) -> int:
        """Get pending royalties for recipient."""
        try:
            return int(self.contract.functions.getPendingRoyalties(recipient))
        except Exception as e:
            logger.error(f"Failed to get pending royalties: {e}")
            return 0


class ContractManager:
    """Manages all DCMX smart contracts."""
    
    def __init__(self, config: Optional[TronConfig] = None):
        """
        Initialize contract manager.
        
        Args:
            config: TRON configuration
        """
        self.config = config or TronConfig.from_env()
        self.client = TronClient(self.config)
        
        # Initialize contract wrappers
        self.token: Optional[DCMXTokenContract] = None
        self.nft: Optional[MusicNFTContract] = None
        self.compliance: Optional[ComplianceRegistryContract] = None
        self.rewards: Optional[RewardVaultContract] = None
        self.royalties: Optional[RoyaltyDistributorContract] = None
        
        self._initialize_contracts()
    
    def _initialize_contracts(self):
        """Initialize contract instances."""
        if self.config.dcmx_token_address:
            self.token = DCMXTokenContract(
                self.client,
                self.config.dcmx_token_address
            )
        
        if self.config.music_nft_address:
            self.nft = MusicNFTContract(
                self.client,
                self.config.music_nft_address
            )
        
        if self.config.compliance_registry_address:
            self.compliance = ComplianceRegistryContract(
                self.client,
                self.config.compliance_registry_address
            )
        
        if self.config.reward_vault_address:
            self.rewards = RewardVaultContract(
                self.client,
                self.config.reward_vault_address
            )
        
        if self.config.royalty_distributor_address:
            self.royalties = RoyaltyDistributorContract(
                self.client,
                self.config.royalty_distributor_address
            )
        
        logger.info("Contract manager initialized")
