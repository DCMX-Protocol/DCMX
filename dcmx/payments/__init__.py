"""Payment integrations package."""

from dcmx.payments.processor import (
    UnifiedPaymentGateway,
    PaymentProcessor,
    PaymentStatus,
    PaymentMethod,
    PaymentRecord,
)

try:
    from dcmx.payments.magic_eden import (
        MagicEdenClient,
        DCMXMagicEdenIntegration,
        MagicEdenChain,
        MagicEdenListing,
    )
except ImportError:
    pass

try:
    from dcmx.payments.magic_internet_money import (
        MIMPaymentProcessor,
        DCMXMIMIntegration,
        MIMChain,
        MIMPayment,
    )
except ImportError:
    pass

__all__ = [
    "UnifiedPaymentGateway",
    "PaymentProcessor",
    "PaymentStatus",
    "PaymentMethod",
    "PaymentRecord",
    "MagicEdenClient",
    "DCMXMagicEdenIntegration",
    "MagicEdenChain",
    "MagicEdenListing",
    "MIMPaymentProcessor",
    "DCMXMIMIntegration",
    "MIMChain",
    "MIMPayment",
]
