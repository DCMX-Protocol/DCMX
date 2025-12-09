"""Blockchain agent for DCMX - handles NFT minting and token rewards."""

import logging
from typing import Optional
from web3 import Web3
from dataclasses import dataclass
from datetime import datetime, timezone

from dcmx.blockchain.contract_manager import ContractManager


logger = logging.getLogger(__name__)


@dataclass
class NFTMintRequest:
    """Request to mint a music NFT."""
    track_hash: str
    artist_wallet: str
    title: str
    edition_number: int
    max_editions: int
    price_wei: int  # In wei (10^-18 of native token)


@dataclass
class RewardDistribution:
    """Request to distribute tokens as reward."""
    node_id: str
    wallet_address: str
    amount: int  # Token amount
    reward_type: str  # "energy" | "voting" | "referral"
    proof: Optional[str] = None  # Verifiable proof of work


class BlockchainAgent:
    """
    Handles blockchain operations for DCMX.
    
    Responsibilities:
    - Mint limited edition music NFTs
    - Distribute utility tokens
    - Manage governance voting
    - Execute reward distributions
    """
    
    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        contract_addresses: Optional[dict] = None
    ):
        """
        Initialize blockchain agent.
        
        Args:
            rpc_url: RPC endpoint URL (e.g., Infura, Alchemy, Polygon RPC)
            private_key: Private key for signing transactions
            contract_addresses: Dict of contract addresses {name: address}
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")
        
        self.account = self.w3.eth.account.from_key(private_key)
        self.contract_manager = ContractManager(self.w3)
        self.contract_addresses = contract_addresses or {}
        
        logger.info(f"BlockchainAgent initialized: {self.account.address}")
    
    async def mint_nft(self, request: NFTMintRequest) -> str:
        """
        Mint a limited edition music NFT.
        
        Args:
            request: NFTMintRequest with track and edition info
            
        Returns:
            Transaction hash of NFT mint
        """
        try:
            # Build transaction
            tx = self.contract_manager.music_nft.functions.mint(
                self.account.address,
                request.track_hash,
                request.edition_number,
                request.max_editions,
                request.price_wei
            ).build_transaction({
                'from': self.account.address,
                'gas': 300_000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Minted NFT {request.track_hash} edition {request.edition_number}/{request.max_editions}: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"NFT minting failed for {request.track_hash}: {e}")
            raise
    
    async def distribute_rewards(self, distribution: RewardDistribution) -> str:
        """
        Distribute tokens as reward for network participation.
        
        Args:
            distribution: RewardDistribution with node and reward info
            
        Returns:
            Transaction hash of reward distribution
        """
        try:
            # Validate reward amount
            if distribution.amount <= 0:
                raise ValueError("Reward amount must be positive")
            
            if distribution.reward_type not in ["energy", "voting", "referral"]:
                raise ValueError(f"Invalid reward type: {distribution.reward_type}")
            
            # Build transaction
            tx = self.contract_manager.reward_distributor.functions.distribute(
                distribution.wallet_address,
                distribution.amount,
                distribution.reward_type
            ).build_transaction({
                'from': self.account.address,
                'gas': 200_000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(f"Distributed {distribution.amount} tokens ({distribution.reward_type}) to {distribution.wallet_address}: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Reward distribution failed: {e}")
            raise
    
    async def get_nft_metadata(self, token_id: int) -> dict:
        """
        Retrieve NFT metadata from contract.
        
        Args:
            token_id: NFT token ID
            
        Returns:
            NFT metadata (title, artist, edition, etc)
        """
        try:
            metadata = self.contract_manager.music_nft.functions.getMetadata(token_id).call()
            return {
                "token_id": token_id,
                "track_hash": metadata[0],
                "edition_number": metadata[1],
                "max_editions": metadata[2],
                "minted_at": metadata[3],
            }
        except Exception as e:
            logger.error(f"Failed to get NFT metadata for token {token_id}: {e}")
            return {}
