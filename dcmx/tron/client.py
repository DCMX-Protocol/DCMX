"""
TRON Client Wrapper

Provides a high-level interface for interacting with TRON blockchain.
"""

import logging
from typing import Optional, Dict, Any, List
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider

from .config import TronConfig, NetworkConfig, NETWORKS

logger = logging.getLogger(__name__)


class TronClient:
    """
    TRON blockchain client wrapper.
    
    Provides simplified interface for:
    - Wallet management
    - Transaction signing and sending
    - Contract interaction
    - Event querying
    """
    
    def __init__(self, config: Optional[TronConfig] = None):
        """
        Initialize TRON client.
        
        Args:
            config: TRON configuration (or load from env)
        """
        if config is None:
            from .config import get_config
            config = get_config()
        
        self.config = config
        self.network_config = config.get_network_config()
        
        # Initialize tronpy client
        provider = HTTPProvider(
            api_key=config.api_key,
            endpoint_uri=self.network_config.full_node
        )
        
        self.client = Tron(provider=provider, network=config.network)
        
        # Load private key if provided
        self.private_key = None
        self.address = None
        if config.private_key:
            self.private_key = PrivateKey(bytes.fromhex(config.private_key))
            self.address = self.private_key.public_key.to_base58check_address()
            logger.info(f"Loaded wallet: {self.address}")
        
        logger.info(f"Connected to {self.network_config.name}")
    
    def get_balance(self, address: Optional[str] = None) -> float:
        """
        Get TRX balance for an address.
        
        Args:
            address: Address to check (or use loaded wallet)
            
        Returns:
            Balance in TRX
        """
        addr = address or self.address
        if not addr:
            raise ValueError("No address provided")
        
        balance_sun = self.client.get_account_balance(addr)
        return balance_sun / 1_000_000  # Convert from SUN to TRX
    
    def get_account_resource(self, address: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account resource info (bandwidth, energy).
        
        Args:
            address: Address to check
            
        Returns:
            Resource information
        """
        addr = address or self.address
        if not addr:
            raise ValueError("No address provided")
        
        return self.client.get_account_resource(addr)
    
    def send_trx(self, to_address: str, amount_trx: float) -> str:
        """
        Send TRX to an address.
        
        Args:
            to_address: Recipient address
            amount_trx: Amount in TRX
            
        Returns:
            Transaction hash
        """
        if not self.private_key:
            raise ValueError("No private key loaded")
        
        amount_sun = int(amount_trx * 1_000_000)
        
        txn = (
            self.client.trx.transfer(self.address, to_address, amount_sun)
            .build()
            .sign(self.private_key)
        )
        
        result = txn.broadcast()
        tx_hash = result.get("txid", "")
        
        logger.info(f"Sent {amount_trx} TRX to {to_address}, tx: {tx_hash}")
        return tx_hash
    
    def get_contract(self, contract_address: str):
        """
        Get contract instance.
        
        Args:
            contract_address: Contract address
            
        Returns:
            Contract object
        """
        return self.client.get_contract(contract_address)
    
    def call_contract(
        self,
        contract_address: str,
        function_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Call a contract view function (read-only).
        
        Args:
            contract_address: Contract address
            function_name: Function name
            *args: Function arguments
            **kwargs: Additional parameters
            
        Returns:
            Function result
        """
        contract = self.get_contract(contract_address)
        return contract.functions[function_name](*args, **kwargs)
    
    def send_contract_transaction(
        self,
        contract_address: str,
        function_name: str,
        *args,
        fee_limit: int = 100_000_000,  # 100 TRX default
        **kwargs
    ) -> str:
        """
        Send a contract transaction (state-changing).
        
        Args:
            contract_address: Contract address
            function_name: Function name
            *args: Function arguments
            fee_limit: Maximum fee in SUN
            **kwargs: Additional parameters
            
        Returns:
            Transaction hash
        """
        if not self.private_key:
            raise ValueError("No private key loaded")
        
        contract = self.get_contract(contract_address)
        
        txn = (
            contract.functions[function_name](*args, **kwargs)
            .with_owner(self.address)
            .fee_limit(fee_limit)
            .build()
            .sign(self.private_key)
        )
        
        result = txn.broadcast()
        tx_hash = result.get("txid", "")
        
        logger.info(f"Contract transaction: {function_name}, tx: {tx_hash}")
        return tx_hash
    
    def wait_for_transaction(
        self,
        tx_hash: str,
        timeout: int = 30,
        interval: int = 2
    ) -> Dict[str, Any]:
        """
        Wait for transaction to be confirmed.
        
        Args:
            tx_hash: Transaction hash
            timeout: Maximum wait time in seconds
            interval: Check interval in seconds
            
        Returns:
            Transaction receipt
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                receipt = self.client.get_transaction_info(tx_hash)
                if receipt:
                    logger.info(f"Transaction confirmed: {tx_hash}")
                    return receipt
            except Exception as e:
                logger.debug(f"Transaction not yet confirmed: {e}")
            
            time.sleep(interval)
        
        raise TimeoutError(f"Transaction not confirmed after {timeout}s: {tx_hash}")
    
    def get_events_by_contract(
        self,
        contract_address: str,
        event_name: Optional[str] = None,
        block_number: Optional[int] = None,
        min_block: Optional[int] = None,
        max_block: Optional[int] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Get events emitted by a contract.
        
        Args:
            contract_address: Contract address
            event_name: Filter by event name
            block_number: Specific block number
            min_block: Minimum block number
            max_block: Maximum block number
            limit: Maximum number of results
            
        Returns:
            List of events
        """
        params = {
            "limit": limit,
        }
        
        if event_name:
            params["event_name"] = event_name
        if block_number:
            params["block_number"] = block_number
        if min_block:
            params["min_block_timestamp"] = min_block
        if max_block:
            params["max_block_timestamp"] = max_block
        
        # Use event server API
        url = f"{self.network_config.event_server}/v1/contracts/{contract_address}/events"
        
        import requests
        headers = {}
        if self.config.api_key:
            headers["TRON-PRO-API-KEY"] = self.config.api_key
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data.get("data", [])
    
    def get_latest_block_number(self) -> int:
        """
        Get the latest block number.
        
        Returns:
            Block number
        """
        block = self.client.get_latest_solid_block()
        return block.get("block_header", {}).get("raw_data", {}).get("number", 0)
    
    def get_block(self, block_number: int) -> Dict[str, Any]:
        """
        Get block by number.
        
        Args:
            block_number: Block number
            
        Returns:
            Block data
        """
        return self.client.get_block(block_number)
    
    def to_base58(self, hex_address: str) -> str:
        """
        Convert hex address to base58.
        
        Args:
            hex_address: Hex format address
            
        Returns:
            Base58 format address
        """
        return self.client.to_base58check_address(hex_address)
    
    def to_hex(self, base58_address: str) -> str:
        """
        Convert base58 address to hex.
        
        Args:
            base58_address: Base58 format address
            
        Returns:
            Hex format address
        """
        return self.client.to_hex_address(base58_address)
    
    def is_connected(self) -> bool:
        """
        Check if client is connected to network.
        
        Returns:
            True if connected
        """
        try:
            self.get_latest_block_number()
            return True
        except Exception:
            return False
    
    def get_explorer_url(self, tx_hash: str) -> str:
        """
        Get block explorer URL for a transaction.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Explorer URL
        """
        return f"{self.network_config.explorer_url}/#/transaction/{tx_hash}"
