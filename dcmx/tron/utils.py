"""Utility functions for TRON integration."""

import hashlib
import logging
from typing import Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def to_sun(trx_amount: float) -> int:
    """
    Convert TRX to SUN (smallest unit).
    
    Args:
        trx_amount: Amount in TRX
        
    Returns:
        Amount in SUN (1 TRX = 1,000,000 SUN)
    """
    return int(trx_amount * 1_000_000)


def from_sun(sun_amount: int) -> float:
    """
    Convert SUN to TRX.
    
    Args:
        sun_amount: Amount in SUN
        
    Returns:
        Amount in TRX
    """
    return sun_amount / 1_000_000


def to_token_units(amount: float, decimals: int = 18) -> int:
    """
    Convert decimal amount to token units.
    
    Args:
        amount: Amount in decimal form
        decimals: Token decimals
        
    Returns:
        Amount in smallest token unit
    """
    return int(amount * (10 ** decimals))


def from_token_units(amount: int, decimals: int = 18) -> float:
    """
    Convert token units to decimal amount.
    
    Args:
        amount: Amount in smallest token unit
        decimals: Token decimals
        
    Returns:
        Amount in decimal form
    """
    return amount / (10 ** decimals)


def compute_document_hash(content: str) -> str:
    """
    Compute SHA-256 hash of document content.
    
    Args:
        content: Document content
        
    Returns:
        Hex hash string
    """
    return hashlib.sha256(content.encode()).hexdigest()


def compute_proof_hash(data: dict) -> str:
    """
    Compute proof hash from data.
    
    Args:
        data: Data dictionary
        
    Returns:
        Hex hash string
    """
    import json
    content = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def format_address(address: str) -> str:
    """
    Format TRON address (ensure proper format).
    
    Args:
        address: Address string
        
    Returns:
        Formatted address
    """
    # TRON addresses start with 'T' and are base58 encoded
    if not address.startswith('T'):
        logger.warning(f"Invalid TRON address format: {address}")
    return address


def validate_address(address: str) -> bool:
    """
    Validate TRON address format.
    
    Args:
        address: Address to validate
        
    Returns:
        True if valid
    """
    # Basic validation: TRON addresses start with 'T' and are 34 chars
    return (
        isinstance(address, str) and
        address.startswith('T') and
        len(address) == 34
    )


def timestamp_to_datetime(timestamp: int) -> datetime:
    """
    Convert blockchain timestamp to datetime.
    
    Args:
        timestamp: Timestamp in milliseconds
        
    Returns:
        datetime object
    """
    return datetime.fromtimestamp(timestamp / 1000)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    Convert datetime to blockchain timestamp.
    
    Args:
        dt: datetime object
        
    Returns:
        Timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int.
    
    Args:
        value: Value to convert
        default: Default if conversion fails
        
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """
    Safely convert value to string.
    
    Args:
        value: Value to convert
        default: Default if conversion fails
        
    Returns:
        String value
    """
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def parse_contract_error(error: Exception) -> str:
    """
    Parse contract error message.
    
    Args:
        error: Exception from contract call
        
    Returns:
        Human-readable error message
    """
    error_str = str(error)
    
    # Common error patterns
    if "revert" in error_str.lower():
        return "Transaction reverted - check contract requirements"
    elif "insufficient" in error_str.lower():
        return "Insufficient balance or allowance"
    elif "unauthorized" in error_str.lower():
        return "Unauthorized - check permissions"
    else:
        return error_str


def format_token_amount(amount: int, decimals: int = 18, symbol: str = "DCMX") -> str:
    """
    Format token amount for display.
    
    Args:
        amount: Amount in smallest unit
        decimals: Token decimals
        symbol: Token symbol
        
    Returns:
        Formatted string
    """
    value = from_token_units(amount, decimals)
    return f"{value:,.2f} {symbol}"


def format_nft_edition(edition: int, max_editions: int) -> str:
    """
    Format NFT edition number.
    
    Args:
        edition: Edition number
        max_editions: Max editions
        
    Returns:
        Formatted string
    """
    return f"#{edition} of {max_editions}"


def calculate_royalty(sale_price: int, royalty_bps: int) -> int:
    """
    Calculate royalty amount.
    
    Args:
        sale_price: Sale price in SUN
        royalty_bps: Royalty in basis points (100 = 1%)
        
    Returns:
        Royalty amount in SUN
    """
    return (sale_price * royalty_bps) // 10000


def validate_royalty_bps(bps: int) -> bool:
    """
    Validate royalty basis points.
    
    Args:
        bps: Basis points
        
    Returns:
        True if valid (0-10000)
    """
    return 0 <= bps <= 10000
