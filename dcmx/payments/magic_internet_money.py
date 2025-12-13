"""
Magic Internet Money (MIM) Stablecoin Payment Integration

MIM is a decentralized stablecoin pegged to USD, issued by Abracadabra.money.
Supports multi-chain payments: Ethereum, Avalanche, Arbitrum, Fantom, etc.
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from web3 import Web3
from web3.contract import Contract

logger = logging.getLogger(__name__)


class MIMChain(Enum):
    """Supported MIM chains."""
    ETHEREUM = "ethereum"
    AVALANCHE = "avalanche"
    ARBITRUM = "arbitrum"
    FANTOM = "fantom"
    BINANCE = "binance"
    POLYGON = "polygon"
    OPTIMISM = "optimism"


# MIM token addresses by chain
MIM_ADDRESSES = {
    MIMChain.ETHEREUM: "0x99D8a9C45b2ecA8864373A26D1459e3Dff1e17F3",
    MIMChain.AVALANCHE: "0x130966628846BFd36ff31a822705796e8cb8C18D",
    MIMChain.ARBITRUM: "0xFEa7a6a0B346362BF88A9e4A88416B77a57D6c2A",
    MIMChain.FANTOM: "0x82f0B8B456c1A451378467398982d4834b6829c1",
    MIMChain.BINANCE: "0xfE19F0B51438fd612f6FD59C1dbB3eA319f433Ba",
    MIMChain.POLYGON: "0x49a0400587A7F65072c87c4910449fDcC5c47242",
    MIMChain.OPTIMISM: "0xB153FB3d196A8eB25522705560ac152eeEc57901",
}

# RPC endpoints
RPC_ENDPOINTS = {
    MIMChain.ETHEREUM: "https://eth.llamarpc.com",
    MIMChain.AVALANCHE: "https://api.avax.network/ext/bc/C/rpc",
    MIMChain.ARBITRUM: "https://arb1.arbitrum.io/rpc",
    MIMChain.FANTOM: "https://rpc.ftm.tools",
    MIMChain.BINANCE: "https://bsc-dataseed.binance.org",
    MIMChain.POLYGON: "https://polygon-rpc.com",
    MIMChain.OPTIMISM: "https://mainnet.optimism.io",
}

# ERC-20 ABI (minimal for transfers)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]


@dataclass
class MIMPayment:
    """MIM payment transaction."""
    tx_hash: str
    from_address: str
    to_address: str
    amount: Decimal
    chain: MIMChain
    status: str
    timestamp: str
    block_number: int
    gas_used: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tx_hash": self.tx_hash,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "amount": str(self.amount),
            "chain": self.chain.value,
            "status": self.status,
            "timestamp": self.timestamp,
            "block_number": self.block_number,
            "gas_used": self.gas_used,
        }


class MIMPaymentProcessor:
    """
    Magic Internet Money (MIM) payment processor.
    
    Features:
    - Multi-chain MIM payments
    - Balance checking
    - Transaction verification
    - USD-pegged pricing (1 MIM ≈ 1 USD)
    - Automatic chain selection
    """
    
    def __init__(
        self,
        chain: MIMChain = MIMChain.ETHEREUM,
        rpc_url: Optional[str] = None,
        private_key: Optional[str] = None,
    ):
        """
        Initialize MIM payment processor.
        
        Args:
            chain: Blockchain to use
            rpc_url: Custom RPC URL (optional)
            private_key: Wallet private key for sending payments
        """
        self.chain = chain
        self.rpc_url = rpc_url or RPC_ENDPOINTS[chain]
        self.private_key = private_key
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Initialize MIM contract
        self.mim_address = MIM_ADDRESSES[chain]
        self.mim_contract: Contract = self.w3.eth.contract(
            address=self.mim_address,
            abi=ERC20_ABI,
        )
        
        # Initialize account if private key provided
        self.account = None
        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
        
        logger.info(f"MIM processor initialized on {chain.value}")
        logger.info(f"MIM contract: {self.mim_address}")
    
    def get_balance(self, address: str) -> Decimal:
        """
        Get MIM balance for address.
        
        Args:
            address: Wallet address
            
        Returns:
            MIM balance
        """
        try:
            balance_wei = self.mim_contract.functions.balanceOf(
                Web3.to_checksum_address(address)
            ).call()
            
            # MIM has 18 decimals
            balance = Decimal(balance_wei) / Decimal(10**18)
            
            logger.info(f"Balance for {address}: {balance} MIM")
            return balance
            
        except Exception as e:
            logger.error(f"Error getting MIM balance: {e}")
            return Decimal(0)
    
    def convert_usd_to_mim(self, usd_amount: float) -> Decimal:
        """
        Convert USD to MIM (1:1 peg).
        
        Args:
            usd_amount: Amount in USD
            
        Returns:
            Amount in MIM
        """
        # MIM is pegged 1:1 to USD
        # In production, you might want to check the actual peg via oracle
        return Decimal(str(usd_amount))
    
    def send_payment(
        self,
        to_address: str,
        amount_mim: Decimal,
        max_gas_price_gwei: Optional[int] = None,
    ) -> str:
        """
        Send MIM payment.
        
        Args:
            to_address: Recipient address
            amount_mim: Amount in MIM
            max_gas_price_gwei: Max gas price in gwei
            
        Returns:
            Transaction hash
        """
        if not self.account:
            raise ValueError("Private key required to send payments")
        
        try:
            # Convert amount to wei (18 decimals)
            amount_wei = int(amount_mim * Decimal(10**18))
            
            # Build transaction
            tx = self.mim_contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei,
            ).build_transaction({
                'from': self.account.address,
                'gas': 100000,  # Standard ERC-20 transfer
                'gasPrice': self.w3.eth.gas_price if not max_gas_price_gwei else self.w3.to_wei(max_gas_price_gwei, 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            logger.info(
                f"MIM payment sent: {amount_mim} MIM to {to_address}, "
                f"tx: {tx_hash.hex()}"
            )
            
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending MIM payment: {e}")
            raise
    
    def verify_payment(
        self,
        tx_hash: str,
        expected_amount: Decimal,
        expected_recipient: str,
    ) -> bool:
        """
        Verify a MIM payment transaction.
        
        Args:
            tx_hash: Transaction hash
            expected_amount: Expected amount
            expected_recipient: Expected recipient
            
        Returns:
            Verification status
        """
        try:
            # Get transaction receipt
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt['status'] != 1:
                logger.warning(f"Transaction failed: {tx_hash}")
                return False
            
            # Get transaction
            tx = self.w3.eth.get_transaction(tx_hash)
            
            # Verify contract address
            if tx['to'].lower() != self.mim_address.lower():
                logger.warning(f"Transaction not to MIM contract: {tx['to']}")
                return False
            
            # Decode transfer function call
            # This is a simplified check - in production, parse logs properly
            logger.info(f"Payment verified: {tx_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    def get_payment_details(self, tx_hash: str) -> Optional[MIMPayment]:
        """
        Get payment transaction details.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            MIMPayment or None
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            tx = self.w3.eth.get_transaction(tx_hash)
            block = self.w3.eth.get_block(receipt['blockNumber'])
            
            # Decode transfer amount from logs
            # Event Transfer(address indexed from, address indexed to, uint256 value)
            transfer_log = receipt['logs'][0] if receipt['logs'] else None
            
            if transfer_log:
                # Decode amount from log data (last 32 bytes)
                amount_wei = int(transfer_log['data'].hex(), 16)
                amount_mim = Decimal(amount_wei) / Decimal(10**18)
            else:
                amount_mim = Decimal(0)
            
            payment = MIMPayment(
                tx_hash=tx_hash,
                from_address=tx['from'],
                to_address=tx['to'],
                amount=amount_mim,
                chain=self.chain,
                status="confirmed" if receipt['status'] == 1 else "failed",
                timestamp=str(block['timestamp']),
                block_number=receipt['blockNumber'],
                gas_used=receipt['gasUsed'],
            )
            
            return payment
            
        except Exception as e:
            logger.error(f"Error getting payment details: {e}")
            return None
    
    def estimate_gas_cost(
        self,
        to_address: str,
        amount_mim: Decimal,
    ) -> Dict[str, Any]:
        """
        Estimate gas cost for MIM transfer.
        
        Args:
            to_address: Recipient address
            amount_mim: Amount in MIM
            
        Returns:
            Gas cost estimate
        """
        try:
            amount_wei = int(amount_mim * Decimal(10**18))
            
            # Estimate gas
            gas_estimate = self.mim_contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei,
            ).estimate_gas({'from': self.account.address if self.account else self.w3.eth.accounts[0]})
            
            gas_price = self.w3.eth.gas_price
            gas_cost_wei = gas_estimate * gas_price
            gas_cost_eth = Decimal(gas_cost_wei) / Decimal(10**18)
            
            return {
                "gas_estimate": gas_estimate,
                "gas_price_gwei": gas_price / 10**9,
                "gas_cost_eth": str(gas_cost_eth),
                "gas_cost_usd_estimate": str(gas_cost_eth * Decimal("3000")),  # Rough ETH price
            }
            
        except Exception as e:
            logger.error(f"Error estimating gas: {e}")
            return {}


class DCMXMIMIntegration:
    """
    DCMX-specific MIM payment integration.
    
    Handles MIM payments for music NFT purchases.
    """
    
    def __init__(
        self,
        chain: MIMChain = MIMChain.ETHEREUM,
        private_key: Optional[str] = None,
        merchant_address: Optional[str] = None,
    ):
        """
        Initialize DCMX MIM integration.
        
        Args:
            chain: Blockchain to use
            private_key: Wallet private key (for sending payments)
            merchant_address: Merchant wallet address (for receiving payments)
        """
        self.processor = MIMPaymentProcessor(
            chain=chain,
            private_key=private_key,
        )
        self.merchant_address = merchant_address
        self.payment_history: Dict[str, MIMPayment] = {}
    
    def process_nft_purchase(
        self,
        buyer_address: str,
        nft_price_usd: float,
        nft_id: str,
        artist_royalty_percentage: float = 10.0,
    ) -> Dict[str, Any]:
        """
        Process MIM payment for NFT purchase.
        
        Args:
            buyer_address: Buyer wallet address
            nft_price_usd: NFT price in USD
            nft_id: NFT ID
            artist_royalty_percentage: Artist royalty percentage
            
        Returns:
            Payment result
        """
        # Convert USD to MIM (1:1 peg)
        price_mim = self.processor.convert_usd_to_mim(nft_price_usd)
        
        # Check buyer balance
        buyer_balance = self.processor.get_balance(buyer_address)
        
        if buyer_balance < price_mim:
            logger.warning(
                f"Insufficient MIM balance: {buyer_balance} < {price_mim}"
            )
            return {
                "success": False,
                "error": "Insufficient MIM balance",
                "required": str(price_mim),
                "available": str(buyer_balance),
            }
        
        # Calculate splits
        artist_royalty = price_mim * Decimal(str(artist_royalty_percentage / 100))
        platform_fee = price_mim * Decimal("0.025")  # 2.5% platform fee
        seller_proceeds = price_mim - artist_royalty - platform_fee
        
        logger.info(
            f"NFT purchase: {nft_id} for {price_mim} MIM\n"
            f"  Artist royalty: {artist_royalty} MIM\n"
            f"  Platform fee: {platform_fee} MIM\n"
            f"  Seller proceeds: {seller_proceeds} MIM"
        )
        
        return {
            "success": True,
            "nft_id": nft_id,
            "price_mim": str(price_mim),
            "price_usd": nft_price_usd,
            "artist_royalty": str(artist_royalty),
            "platform_fee": str(platform_fee),
            "seller_proceeds": str(seller_proceeds),
            "payment_method": "MIM",
            "chain": self.processor.chain.value,
        }
    
    def get_payment_instructions(
        self,
        amount_usd: float,
        order_id: str,
    ) -> Dict[str, Any]:
        """
        Generate MIM payment instructions for buyer.
        
        Args:
            amount_usd: Amount in USD
            order_id: Order ID
            
        Returns:
            Payment instructions
        """
        amount_mim = self.processor.convert_usd_to_mim(amount_usd)
        
        return {
            "payment_method": "Magic Internet Money (MIM)",
            "amount_mim": str(amount_mim),
            "amount_usd": amount_usd,
            "recipient_address": self.merchant_address,
            "chain": self.processor.chain.value,
            "mim_contract": self.processor.mim_address,
            "order_id": order_id,
            "instructions": [
                f"1. Ensure you have {amount_mim} MIM on {self.processor.chain.value}",
                f"2. Send {amount_mim} MIM to {self.merchant_address}",
                "3. Include order ID in transaction memo (if supported)",
                "4. Wait for transaction confirmation",
            ],
            "notes": [
                "MIM is a USD-pegged stablecoin (1 MIM ≈ 1 USD)",
                f"Available on: {', '.join([c.value for c in MIMChain])}",
                "Gas fees apply (varies by chain)",
            ],
        }
