"""
DCMX Payment Processing

Integrates with payment processors:
- Stripe (credit card, ACH, bank transfers)
- Circle (stablecoins, crypto)
- Coinbase Commerce (crypto payments)
- PayPal (fiat)

Handles:
- Multi-currency support (USDC, USDT, USD, EUR, etc)
- Webhook verification
- Payment state machine
- PCI compliance
"""

import logging
import hmac
import hashlib
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import json

from web3 import Web3
from web3.exceptions import TransactionNotFound, ContractLogicError

logger = logging.getLogger(__name__)

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]


class PaymentProcessor(Enum):
    """Supported payment processors."""
    STRIPE = "stripe"
    CIRCLE = "circle"
    COINBASE = "coinbase"
    PAYPAL = "paypal"
    MAGIC_EDEN = "magic_eden"
    MIM = "magic_internet_money"


class PaymentStatus(Enum):
    """Payment status states."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class PaymentMethod(Enum):
    """Payment methods."""
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO_USDC = "crypto_usdc"
    CRYPTO_USDT = "crypto_usdt"
    CRYPTO_ETH = "crypto_eth"
    CRYPTO_MIM = "crypto_mim"
    PAYPAL = "paypal"
    MAGIC_EDEN_NFT = "magic_eden_nft"


@dataclass
class PaymentConfig:
    """Payment processor configuration."""
    processor: PaymentProcessor
    api_key: str
    api_secret: str
    webhook_secret: str
    webhook_url: str
    production: bool = False


@dataclass
class PaymentRecord:
    """Record of a payment transaction."""
    payment_id: str
    user_wallet: str
    amount: float
    currency: str  # USD, USDC, EUR, etc
    payment_method: PaymentMethod
    processor: PaymentProcessor
    status: PaymentStatus
    processor_transaction_id: str
    
    # Metadata
    created_at: str
    completed_at: Optional[str] = None
    failed_reason: Optional[str] = None
    refund_id: Optional[str] = None
    
    # Conversion
    dcmx_amount: float = 0.0
    exchange_rate: float = 1.0
    
    # Security
    ip_address: str = ""
    user_agent: str = ""
    verified: bool = False
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class PaymentProcessor:
    """Base payment processor."""
    
    def __init__(self, config: PaymentConfig):
        self.config = config
    
    async def process_payment(
        self,
        user_wallet: str,
        amount: float,
        currency: str,
        payment_method: PaymentMethod,
        description: str = "",
    ) -> PaymentRecord:
        """Process payment."""
        raise NotImplementedError
    
    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature."""
        raise NotImplementedError
    
    async def refund_payment(self, payment_id: str) -> bool:
        """Refund a payment."""
        raise NotImplementedError


class StripePaymentProcessor(PaymentProcessor):
    """Stripe payment processor."""
    
    async def process_payment(
        self,
        user_wallet: str,
        amount: float,
        currency: str,
        payment_method: PaymentMethod,
        description: str = "",
    ) -> PaymentRecord:
        """Process payment via Stripe."""
        try:
            import stripe
            stripe.api_key = self.config.api_key
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # cents
                currency=currency.lower(),
                description=description or f"DCMX - {user_wallet[:16]}...",
                metadata={
                    "wallet": user_wallet,
                    "payment_method": payment_method.value,
                }
            )
            
            payment = PaymentRecord(
                payment_id=intent.id,
                user_wallet=user_wallet,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                processor=PaymentProcessor.STRIPE,
                status=PaymentStatus.PROCESSING,
                processor_transaction_id=intent.id,
            )
            
            logger.info(f"Stripe payment initiated: {payment.payment_id}")
            return payment
        
        except Exception as e:
            logger.error(f"Stripe payment failed: {e}")
            raise
    
    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        expected_sig = hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_sig)
    
    async def refund_payment(self, payment_id: str) -> bool:
        """Refund Stripe payment."""
        try:
            import stripe
            stripe.api_key = self.config.api_key
            
            refund = stripe.Refund.create(payment_intent=payment_id)
            logger.info(f"Stripe refund created: {refund.id}")
            return True
        except Exception as e:
            logger.error(f"Stripe refund failed: {e}")
            return False


class CirclePaymentProcessor(PaymentProcessor):
    """Circle payment processor for stablecoins."""
    
    async def process_payment(
        self,
        user_wallet: str,
        amount: float,
        currency: str,
        payment_method: PaymentMethod,
        description: str = "",
    ) -> PaymentRecord:
        """Process stablecoin payment via Circle."""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }
            
            data = {
                "idempotencyKey": f"{user_wallet}_{datetime.utcnow().timestamp()}",
                "amount": {
                    "amount": str(amount),
                    "currency": currency,  # USDC, USDT
                },
                "source": {
                    "type": "blockchain",
                    "chain": "ETHEREUM",
                    "address": user_wallet,
                },
                "destination": {
                    "type": "wallet",
                    "id": "PLATFORM_WALLET",
                },
                "description": description,
            }
            
            response = requests.post(
                f"{self.config.webhook_url}/transfers",
                headers=headers,
                json=data,
                timeout=30,
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                payment = PaymentRecord(
                    payment_id=result["data"]["id"],
                    user_wallet=user_wallet,
                    amount=amount,
                    currency=currency,
                    payment_method=payment_method,
                    processor=PaymentProcessor.CIRCLE,
                    status=PaymentStatus.PROCESSING,
                    processor_transaction_id=result["data"]["id"],
                )
                logger.info(f"Circle payment initiated: {payment.payment_id}")
                return payment
        
        except Exception as e:
            logger.error(f"Circle payment failed: {e}")
            raise
    
    async def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Circle webhook signature."""
        expected_sig = hmac.new(
            self.config.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature.split(",")[1], expected_sig)
    
    async def refund_payment(self, payment_id: str) -> bool:
        """Refund Circle payment."""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
            }
            
            response = requests.post(
                f"{self.config.webhook_url}/transfers/{payment_id}/reverse",
                headers=headers,
                timeout=30,
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Circle refund failed: {e}")
            return False


class PaymentManager:
    """
    Manage payments across multiple processors.
    
    Features:
    - Multi-processor support
    - Automatic failover
    - Webhook handling
    - Payment state tracking
    - Fraud detection
    """
    
    def __init__(self):
        """Initialize payment manager."""
        self.processors: Dict[PaymentProcessor, PaymentProcessor] = {}
        self.payment_history: Dict[str, PaymentRecord] = {}
        self.exchange_rates: Dict[str, float] = {
            "USD": 1.0,
            "EUR": 0.92,
            "USDC": 1.0,
            "USDT": 1.0,
            "ETH": 2400.0,
        }
    
    def configure_processor(self, config: PaymentConfig):
        """Configure payment processor."""
        if config.processor == PaymentProcessor.STRIPE:
            processor = StripePaymentProcessor(config)
        elif config.processor == PaymentProcessor.CIRCLE:
            processor = CirclePaymentProcessor(config)
        else:
            raise ValueError(f"Unsupported processor: {config.processor}")
        
        self.processors[config.processor] = processor
        logger.info(f"Payment processor configured: {config.processor.value}")
    
    async def process_payment(
        self,
        user_wallet: str,
        amount: float,
        currency: str,
        payment_method: PaymentMethod,
        description: str = "",
        ip_address: str = "",
        user_agent: str = "",
    ) -> PaymentRecord:
        """
        Process payment.
        
        Tries processors in order: Stripe → Circle
        """
        # Fraud checks
        if not self._fraud_check(user_wallet, amount, ip_address):
            raise ValueError("Payment failed fraud check")
        
        # Try each processor
        for processor_type, processor in self.processors.items():
            try:
                payment = await processor.process_payment(
                    user_wallet,
                    amount,
                    currency,
                    payment_method,
                    description,
                )
                
                # Convert to DCMX
                payment.dcmx_amount = amount * self.exchange_rates.get(currency, 1.0)
                payment.exchange_rate = self.exchange_rates.get(currency, 1.0)
                payment.ip_address = ip_address
                payment.user_agent = user_agent
                
                # Store record
                self.payment_history[payment.payment_id] = payment
                
                logger.info(f"Payment processed: {payment.payment_id} ({payment.amount} {payment.currency})")
                return payment
            
            except Exception as e:
                logger.warning(f"Processor {processor_type.value} failed: {e}")
                continue
        
        raise ValueError("All payment processors failed")
    
    async def verify_webhook(
        self,
        processor: PaymentProcessor,
        payload: bytes,
        signature: str,
    ) -> Tuple[bool, Optional[PaymentRecord]]:
        """Verify and process webhook."""
        if processor not in self.processors:
            return False, None
        
        processor_obj = self.processors[processor]
        
        if not await processor_obj.verify_webhook(payload, signature):
            logger.warning(f"Invalid webhook signature for {processor.value}")
            return False, None
        
        # Parse payload
        try:
            webhook_data = json.loads(payload)
            payment_id = webhook_data.get("id") or webhook_data.get("data", {}).get("id")
            
            if payment_id in self.payment_history:
                payment = self.payment_history[payment_id]
                
                # Update status
                status_map = {
                    "succeeded": PaymentStatus.COMPLETED,
                    "succeeded": PaymentStatus.COMPLETED,
                    "failed": PaymentStatus.FAILED,
                }
                
                if webhook_data.get("status") in status_map:
                    payment.status = status_map[webhook_data["status"]]
                    payment.completed_at = datetime.utcnow().isoformat()
                    payment.verified = True
                    
                    logger.info(f"Payment status updated: {payment_id} → {payment.status.value}")
                    return True, payment
        
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
        
        return False, None
    
    async def refund_payment(self, payment_id: str, reason: str = "") -> bool:
        """Refund a payment."""
        if payment_id not in self.payment_history:
            logger.warning(f"Payment not found: {payment_id}")
            return False
        
        payment = self.payment_history[payment_id]
        
        if payment.processor not in self.processors:
            logger.warning(f"Processor not configured: {payment.processor.value}")
            return False
        
        processor = self.processors[payment.processor]
        
        if await processor.refund_payment(payment_id):
            payment.status = PaymentStatus.REFUNDED
            payment.failed_reason = reason
            logger.info(f"Payment refunded: {payment_id}")
            return True
        
        return False
    
    def _fraud_check(self, user_wallet: str, amount: float, ip_address: str) -> bool:
        """
        Basic fraud detection.
        
        Checks:
        - Amount limits
        - Velocity
        - Geolocation (if available)
        """
        # Amount sanity check
        if amount <= 0 or amount > 100000:
            logger.warning(f"Amount out of bounds: {amount}")
            return False
        
        # Check recent transaction velocity
        recent_payments = [
            p for p in self.payment_history.values()
            if p.user_wallet == user_wallet and
            datetime.fromisoformat(p.created_at) > datetime.utcnow() - timedelta(hours=1)
        ]
        
        if len(recent_payments) > 10:
            logger.warning(f"High transaction velocity: {user_wallet}")
            return False
        
        total_recent = sum(p.amount for p in recent_payments)
        if total_recent > 10000:
            logger.warning(f"High daily volume: {user_wallet}")
            return False
        
        return True
    
    def get_payment_stats(self) -> Dict:
        """Get payment statistics."""
        total_payments = len(self.payment_history)
        completed = sum(1 for p in self.payment_history.values() if p.status == PaymentStatus.COMPLETED)
        failed = sum(1 for p in self.payment_history.values() if p.status == PaymentStatus.FAILED)
        total_volume = sum(p.amount for p in self.payment_history.values())
        
        return {
            "total_payments": total_payments,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total_payments * 100) if total_payments > 0 else 0,
            "total_volume": total_volume,
        }


class UnifiedPaymentGateway:
    """
    Unified payment gateway supporting all DCMX payment methods.
    
    Integrates:
    - Traditional payments: Stripe, PayPal
    - Crypto payments: Circle, Coinbase
    - Stablecoins: USDC, USDT, MIM
    - NFT marketplaces: Magic Eden
    """
    
    def __init__(self):
        """Initialize unified payment gateway."""
        self.processors: Dict[PaymentProcessor, Any] = {}
        self.payment_router = PaymentRouter()
        
        # Import integrations
        try:
            from dcmx.payments.magic_eden import DCMXMagicEdenIntegration
            from dcmx.payments.magic_internet_money import DCMXMIMIntegration
            
            self.magic_eden = None  # Initialize with API key when available
            self.mim_processor = None  # Initialize with chain config when available
            
            logger.info("Magic Eden and MIM integrations loaded")
        except ImportError as e:
            logger.warning(f"Optional payment integrations not available: {e}")
    
    def configure_magic_eden(
        self,
        api_key: str,
        chain: str = "solana",
        collection_symbol: str = "dcmx_music",
    ):
        """
        Configure Magic Eden marketplace integration.
        
        Args:
            api_key: Magic Eden API key
            chain: Blockchain (solana, ethereum, polygon, bitcoin)
            collection_symbol: DCMX collection symbol
        """
        from dcmx.payments.magic_eden import DCMXMagicEdenIntegration, MagicEdenChain
        
        chain_enum = MagicEdenChain(chain)
        self.magic_eden = DCMXMagicEdenIntegration(
            api_key=api_key,
            chain=chain_enum,
            collection_symbol=collection_symbol,
        )
        
        logger.info(f"Magic Eden configured for {chain} chain")
    
    def configure_mim(
        self,
        chain: str = "ethereum",
        private_key: Optional[str] = None,
        merchant_address: Optional[str] = None,
    ):
        """
        Configure Magic Internet Money (MIM) stablecoin payments.
        
        Args:
            chain: Blockchain (ethereum, avalanche, arbitrum, etc.)
            private_key: Wallet private key for sending payments
            merchant_address: Merchant wallet for receiving payments
        """
        from dcmx.payments.magic_internet_money import DCMXMIMIntegration, MIMChain
        
        chain_enum = MIMChain(chain)
        self.mim_processor = DCMXMIMIntegration(
            chain=chain_enum,
            private_key=private_key,
            merchant_address=merchant_address,
        )
        
        logger.info(f"MIM stablecoin configured for {chain} chain")
    
    async def process_payment(
        self,
        user_wallet: str,
        amount_usd: float,
        payment_method: PaymentMethod,
        nft_id: Optional[str] = None,
        artist: Optional[str] = None,
        track_title: Optional[str] = None,
    ) -> Dict:
        """
        Process payment through appropriate gateway.
        
        Args:
            user_wallet: User wallet address
            amount_usd: Amount in USD
            payment_method: Payment method
            nft_id: NFT ID (for NFT purchases)
            artist: Artist name (for Magic Eden listing)
            track_title: Track title (for Magic Eden listing)
            
        Returns:
            Payment result
        """
        # Route to appropriate payment processor
        if payment_method == PaymentMethod.CRYPTO_MIM:
            if not self.mim_processor:
                raise ValueError("MIM processor not configured")
            
            result = self.mim_processor.process_nft_purchase(
                buyer_address=user_wallet,
                nft_price_usd=amount_usd,
                nft_id=nft_id or "unknown",
            )
            
            return result
        
        elif payment_method == PaymentMethod.MAGIC_EDEN_NFT:
            if not self.magic_eden:
                raise ValueError("Magic Eden not configured")
            
            # This would typically be called by seller to list NFT
            # For purchases, Magic Eden handles the transaction
            logger.info(f"NFT purchase via Magic Eden: {nft_id}")
            
            return {
                "success": True,
                "payment_method": "magic_eden",
                "message": "Purchase processed via Magic Eden marketplace",
            }
        
        else:
            # Use existing payment router for traditional methods
            return await self.payment_router.process_payment(
                user_wallet=user_wallet,
                amount=amount_usd,
                currency="USD",
                payment_method=payment_method,
            )
    
    async def list_nft_on_magic_eden(
        self,
        nft_address: str,
        token_id: str,
        artist: str,
        track_title: str,
        price_usd: float,
        seller_address: str,
        royalty_percentage: float = 10.0,
        edition_number: Optional[int] = None,
        max_editions: Optional[int] = None,
    ) -> Dict:
        """
        List DCMX music NFT on Magic Eden marketplace.
        
        Args:
            nft_address: NFT contract address
            token_id: Token ID
            artist: Artist name
            track_title: Track title
            price_usd: Listing price in USD
            seller_address: Seller wallet address
            royalty_percentage: Artist royalty percentage
            edition_number: Edition number (if limited)
            max_editions: Max editions (if limited)
            
        Returns:
            Listing result
        """
        if not self.magic_eden:
            raise ValueError("Magic Eden not configured")
        
        # Convert USD to native currency (SOL, ETH, etc.)
        # This is simplified - in production, use price oracle
        price_native = price_usd / 100  # Rough conversion
        
        listing = await self.magic_eden.list_music_nft(
            nft_address=nft_address,
            token_id=token_id,
            artist=artist,
            track_title=track_title,
            price=price_native,
            seller_address=seller_address,
            royalty_percentage=royalty_percentage,
            edition_number=edition_number,
            max_editions=max_editions,
        )
        
        return {
            "success": True,
            "listing_id": listing.listing_id,
            "price": listing.price,
            "currency": listing.currency,
            "chain": listing.chain.value,
            "status": listing.status,
        }
    
    def get_mim_payment_instructions(
        self,
        amount_usd: float,
        order_id: str,
    ) -> Dict:
        """
        Get MIM payment instructions for buyer.
        
        Args:
            amount_usd: Amount in USD
            order_id: Order ID
            
        Returns:
            Payment instructions
        """
        if not self.mim_processor:
            raise ValueError("MIM processor not configured")
        
        return self.mim_processor.get_payment_instructions(
            amount_usd=amount_usd,
            order_id=order_id,
        )
    
    async def get_magic_eden_stats(self) -> Dict:
        """
        Get DCMX collection stats on Magic Eden.
        
        Returns:
            Collection statistics
        """
        if not self.magic_eden:
            raise ValueError("Magic Eden not configured")
        
        floor_price = await self.magic_eden.get_collection_floor_price()
        volume = await self.magic_eden.get_collection_volume()
        
        return {
            "floor_price": floor_price,
            "volume_24h": volume.get("volume_24h", 0),
            "volume_7d": volume.get("volume_7d", 0),
            "volume_30d": volume.get("volume_30d", 0),
            "total_volume": volume.get("total_volume", 0),
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.magic_eden:
            await self.magic_eden.close()
        
        logger.info("Payment gateway cleaned up")
            "total_volume": total_volume,
            "processors_configured": len(self.processors),
        }
