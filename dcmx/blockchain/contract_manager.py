"""Smart contract manager for DCMX blockchain operations."""

import logging
from typing import Optional, Dict, Any
from web3 import Web3


logger = logging.getLogger(__name__)


class ContractManager:
    """
    Manages interaction with DCMX smart contracts on blockchain.
    
    Handles:
    - ERC-721 NFT minting and transfers
    - ERC-20 token distribution
    - Governance voting
    - Reward distribution
    """
    
    def __init__(self, w3: Web3):
        """
        Initialize contract manager.
        
        Args:
            w3: Web3 instance connected to blockchain RPC endpoint
        """
        self.w3 = w3
        self.music_nft = None
        self.dcmx_token = None
        self.governance_dao = None
        self.reward_distributor = None
        
        logger.info(f"ContractManager initialized, connected to {w3.eth.chain_id}")
    
    async def load_contract(
        self,
        contract_name: str,
        contract_address: str,
        contract_abi: list
    ) -> Any:
        """
        Load a smart contract instance.
        
        Args:
            contract_name: Name of contract (for internal tracking)
            contract_address: Deployed contract address
            contract_abi: Contract ABI (Application Binary Interface)
            
        Returns:
            Contract instance
        """
        try:
            contract = self.w3.eth.contract(
                address=contract_address,
                abi=contract_abi
            )
            logger.info(f"Loaded contract {contract_name} at {contract_address}")
            return contract
        except Exception as e:
            logger.error(f"Failed to load contract {contract_name}: {e}")
            raise
    
    async def get_gas_estimate(self, transaction: Dict) -> int:
        """
        Estimate gas required for transaction.
        
        Args:
            transaction: Transaction dict
            
        Returns:
            Estimated gas amount
        """
        try:
            return self.w3.eth.estimate_gas(transaction)
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            return 300_000  # Default fallback
    
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        Check status of a submitted transaction.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt and status
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                "status": receipt.get("status", 0),
                "block_number": receipt.get("blockNumber"),
                "gas_used": receipt.get("gasUsed"),
                "logs": receipt.get("logs", [])
            }
        except Exception as e:
            logger.error(f"Failed to get transaction status {tx_hash}: {e}")
            return {"status": 0, "error": str(e)}
