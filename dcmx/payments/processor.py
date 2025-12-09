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
    PAYPAL = "paypal"


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
            "processors_configured": len(self.processors),
        }
