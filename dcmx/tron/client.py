"""TRON blockchain client wrapper for DCMX."""

import logging
from typing import Optional, Dict, Any, List
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

from .config import TronConfig, NetworkType

logger = logging.getLogger(__name__)


class TronClient:
    """Wrapper for TRON blockchain interaction using tronpy."""
    
    def __init__(self, config: Optional[TronConfig] = None):
        """
        Initialize TRON client.
        
        Args:
            config: TRON configuration, defaults to environment config
        """
        self.config = config or TronConfig.from_env()
        self.config.validate()
        
        # Initialize tronpy client
        if self.config.network == NetworkType.MAINNET:
            self.tron = Tron(network='mainnet')
        else:
            # Use custom provider for testnets
            provider = HTTPProvider(
                self.config.rpc_endpoint,
                api_key=self.config.api_key
            )
            self.tron = Tron(provider=provider)
        
        # Load private key
        self.private_key = PrivateKey(bytes.fromhex(self.config.private_key))
        self.address = self.private_key.public_key.to_base58check_address()
        
        logger.info(
            f"TronClient initialized: network={self.config.network.value}, "
            f"address={self.address}"
        )
    
    def get_balance(self, address: Optional[str] = None) -> int:
        """
        Get TRX balance for an address.
        
        Args:
            address: Address to check, defaults to client address
            
        Returns:
            Balance in SUN (1 TRX = 1,000,000 SUN)
        """
        addr = address or self.address
        try:
            balance = self.tron.get_account_balance(addr)
            return int(balance * 1_000_000)  # Convert to SUN
        except Exception as e:
            logger.error(f"Failed to get balance for {addr}: {e}")
            return 0
    
    def get_contract(self, address: str) -> Any:
        """
        Get contract instance.
        
        Args:
            address: Contract address
            
        Returns:
            Contract instance
        """
        return self.tron.get_contract(address)
    
    def send_transaction(
        self,
        to_address: str,
        amount_sun: int,
        memo: Optional[str] = None
    ) -> str:
        """
        Send TRX to address.
        
        Args:
            to_address: Recipient address
            amount_sun: Amount in SUN
            memo: Optional transaction memo
            
        Returns:
            Transaction hash
        """
        try:
            txn = (
                self.tron.trx.transfer(self.address, to_address, amount_sun)
                .memo(memo or "")
                .build()
                .sign(self.private_key)
            )
            result = txn.broadcast()
            
            tx_hash = result.get('txid')
            logger.info(f"Transaction sent: {tx_hash}")
            return tx_hash
            
        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            raise
    
    def call_contract_function(
        self,
        contract_address: str,
        function_name: str,
        *args,
        fee_limit: int = 100_000_000,  # 100 TRX default
        **kwargs
    ) -> Any:
        """
        Call a contract function.
        
        Args:
            contract_address: Contract address
            function_name: Function name to call
            *args: Function arguments
            fee_limit: Maximum fee in SUN
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction result
        """
        try:
            contract = self.get_contract(contract_address)
            
            # Build transaction
            txn = (
                contract.functions[function_name](*args)
                .with_owner(self.address)
                .fee_limit(fee_limit)
                .build()
                .sign(self.private_key)
            )
            
            # Broadcast
            result = txn.broadcast()
            tx_hash = result.get('txid')
            
            logger.info(
                f"Contract call: {function_name} on {contract_address}, "
                f"tx={tx_hash}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Contract call failed: {e}")
            raise
    
    def get_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction data or None if not found
        """
        try:
            return self.tron.get_transaction(tx_hash)
        except Exception as e:
            logger.warning(f"Failed to get transaction {tx_hash}: {e}")
            return None
    
    def get_transaction_info(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction execution info.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction info or None
        """
        try:
            return self.tron.get_transaction_info(tx_hash)
        except Exception as e:
            logger.warning(f"Failed to get transaction info {tx_hash}: {e}")
            return None
    
    def get_events_by_contract(
        self,
        contract_address: str,
        event_name: Optional[str] = None,
        block_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get events from a contract.
        
        Args:
            contract_address: Contract address
            event_name: Optional specific event name
            block_number: Optional specific block number
            
        Returns:
            List of events
        """
        try:
            contract = self.get_contract(contract_address)
            
            # Get events (tronpy doesn't have direct event querying,
            # would need to query transactions and parse logs)
            # This is a placeholder for the indexer to implement
            logger.warning("Event querying requires custom implementation")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return []
    
    def get_block(self, block_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get block data.
        
        Args:
            block_number: Block number, defaults to latest
            
        Returns:
            Block data or None
        """
        try:
            if block_number is None:
                return self.tron.get_latest_block()
            else:
                return self.tron.get_block(block_number)
        except Exception as e:
            logger.error(f"Failed to get block: {e}")
            return None
    
    def get_latest_block_number(self) -> int:
        """
        Get latest block number.
        
        Returns:
            Latest block number
        """
        try:
            block = self.tron.get_latest_block()
            return block.get('block_header', {}).get('raw_data', {}).get('number', 0)
        except Exception as e:
            logger.error(f"Failed to get latest block number: {e}")
            return 0
