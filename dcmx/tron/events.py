"""
TRON Blockchain Event Definitions

Defines event structures for parsing blockchain events.
"""

from dataclasses import dataclass
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Types of blockchain events."""
    TRANSFER = "Transfer"
    APPROVAL = "Approval"
    APPROVAL_FOR_ALL = "ApprovalForAll"
    MINT = "Mint"
    BURN = "Burn"
    MUSIC_MINTED = "MusicMinted"
    ACCEPTANCE_RECORDED = "AcceptanceRecordedEvent"
    DELETION_REQUESTED = "DeletionRequested"
    REWARD_CLAIMED = "RewardClaimed"
    CLAIM_VERIFIED = "ClaimVerified"
    SALE_RECORDED = "SaleRecorded"
    ROYALTY_PAID = "RoyaltyPaid"


@dataclass
class BaseEvent:
    """Base class for all blockchain events."""
    event_type: str
    transaction_hash: str
    block_number: int
    block_timestamp: int
    contract_address: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "block_timestamp": self.block_timestamp,
            "contract_address": self.contract_address,
        }


@dataclass
class TransferEvent(BaseEvent):
    """
    Transfer event (TRC-20 and TRC-721).
    
    Emitted when tokens are transferred between addresses.
    """
    from_address: str
    to_address: str
    value: Optional[int] = None  # For TRC-20
    token_id: Optional[int] = None  # For TRC-721
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "from_address": self.from_address,
            "to_address": self.to_address,
            "value": self.value,
            "token_id": self.token_id,
        })
        return data


@dataclass
class MintEvent(BaseEvent):
    """
    Mint event (DCMXToken).
    
    Emitted when new tokens are minted.
    """
    to_address: str
    amount: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "to_address": self.to_address,
            "amount": self.amount,
        })
        return data


@dataclass
class BurnEvent(BaseEvent):
    """
    Burn event (DCMXToken).
    
    Emitted when tokens are burned.
    """
    from_address: str
    amount: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "from_address": self.from_address,
            "amount": self.amount,
        })
        return data


@dataclass
class ApprovalEvent(BaseEvent):
    """
    Approval event (TRC-20 and TRC-721).
    
    Emitted when an address approves another to spend tokens.
    """
    owner_address: str
    spender_address: str
    value: Optional[int] = None  # For TRC-20
    token_id: Optional[int] = None  # For TRC-721
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "owner_address": self.owner_address,
            "spender_address": self.spender_address,
            "value": self.value,
            "token_id": self.token_id,
        })
        return data


@dataclass
class MusicMintedEvent(BaseEvent):
    """
    MusicMinted event (MusicNFT).
    
    Emitted when a new music NFT is minted.
    """
    token_id: int
    artist_address: str
    title: str
    content_hash: str
    edition_number: int
    max_editions: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "token_id": self.token_id,
            "artist_address": self.artist_address,
            "title": self.title,
            "content_hash": self.content_hash,
            "edition_number": self.edition_number,
            "max_editions": self.max_editions,
        })
        return data


@dataclass
class AcceptanceRecordedEvent(BaseEvent):
    """
    AcceptanceRecorded event (ComplianceRegistry).
    
    Emitted when a user accepts a legal document.
    """
    record_id: int
    wallet_address: str
    document_type: int  # Enum value
    version: str
    document_hash: str
    timestamp: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "record_id": self.record_id,
            "wallet_address": self.wallet_address,
            "document_type": self.document_type,
            "version": self.version,
            "document_hash": self.document_hash,
            "timestamp": self.timestamp,
        })
        return data


@dataclass
class DeletionRequestedEvent(BaseEvent):
    """
    DeletionRequested event (ComplianceRegistry).
    
    Emitted when a user requests data deletion (GDPR/CCPA).
    """
    wallet_address: str
    request_type: str
    timestamp: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "wallet_address": self.wallet_address,
            "request_type": self.request_type,
            "timestamp": self.timestamp,
        })
        return data


@dataclass
class RewardClaimedEvent(BaseEvent):
    """
    RewardClaimed event (RewardVault).
    
    Emitted when a reward is claimed.
    """
    claim_id: int
    claimant_address: str
    reward_type: int  # Enum value
    amount: int
    timestamp: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "claim_id": self.claim_id,
            "claimant_address": self.claimant_address,
            "reward_type": self.reward_type,
            "amount": self.amount,
            "timestamp": self.timestamp,
        })
        return data


@dataclass
class ClaimVerifiedEvent(BaseEvent):
    """
    ClaimVerified event (RewardVault).
    
    Emitted when a claim is verified by an authorized verifier.
    """
    claim_id: int
    verifier_address: str
    approved: bool
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "claim_id": self.claim_id,
            "verifier_address": self.verifier_address,
            "approved": self.approved,
        })
        return data


@dataclass
class SaleRecordedEvent(BaseEvent):
    """
    SaleRecorded event (RoyaltyDistributor).
    
    Emitted when an NFT sale is recorded.
    """
    sale_id: int
    token_id: int
    seller_address: str
    buyer_address: str
    sale_price: int
    royalty_amount: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "sale_id": self.sale_id,
            "token_id": self.token_id,
            "seller_address": self.seller_address,
            "buyer_address": self.buyer_address,
            "sale_price": self.sale_price,
            "royalty_amount": self.royalty_amount,
        })
        return data


@dataclass
class RoyaltyPaidEvent(BaseEvent):
    """
    RoyaltyPaid event (RoyaltyDistributor).
    
    Emitted when royalty is paid to the artist.
    """
    sale_id: int
    token_id: int
    recipient_address: str
    amount: int
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "sale_id": self.sale_id,
            "token_id": self.token_id,
            "recipient_address": self.recipient_address,
            "amount": self.amount,
        })
        return data


def parse_event(event_data: Dict[str, Any]) -> Optional[BaseEvent]:
    """
    Parse raw event data into typed event object.
    
    Args:
        event_data: Raw event data from blockchain
        
    Returns:
        Parsed event object or None if unknown event type
    """
    event_name = event_data.get("event_name", "")
    
    # Extract common fields
    base_args = {
        "event_type": event_name,
        "transaction_hash": event_data.get("transaction_id", ""),
        "block_number": event_data.get("block_number", 0),
        "block_timestamp": event_data.get("block_timestamp", 0),
        "contract_address": event_data.get("contract_address", ""),
    }
    
    result = event_data.get("result", {})
    
    # Parse based on event type
    if event_name == "Transfer":
        return TransferEvent(
            **base_args,
            from_address=result.get("from", ""),
            to_address=result.get("to", ""),
            value=result.get("value"),
            token_id=result.get("tokenId"),
        )
    
    elif event_name == "Mint":
        return MintEvent(
            **base_args,
            to_address=result.get("to", ""),
            amount=result.get("amount", 0),
        )
    
    elif event_name == "Burn":
        return BurnEvent(
            **base_args,
            from_address=result.get("from", ""),
            amount=result.get("amount", 0),
        )
    
    elif event_name == "MusicMinted":
        return MusicMintedEvent(
            **base_args,
            token_id=result.get("tokenId", 0),
            artist_address=result.get("artist", ""),
            title=result.get("title", ""),
            content_hash=result.get("contentHash", ""),
            edition_number=result.get("editionNumber", 0),
            max_editions=result.get("maxEditions", 0),
        )
    
    elif event_name == "AcceptanceRecorded":
        return AcceptanceRecordedEvent(
            **base_args,
            record_id=result.get("recordId", 0),
            wallet_address=result.get("wallet", ""),
            document_type=result.get("docType", 0),
            version=result.get("version", ""),
            document_hash=result.get("documentHash", ""),
            timestamp=result.get("timestamp", 0),
        )
    
    elif event_name == "DeletionRequested":
        return DeletionRequestedEvent(
            **base_args,
            wallet_address=result.get("wallet", ""),
            request_type=result.get("requestType", ""),
            timestamp=result.get("timestamp", 0),
        )
    
    elif event_name == "RewardClaimed":
        return RewardClaimedEvent(
            **base_args,
            claim_id=result.get("claimId", 0),
            claimant_address=result.get("claimant", ""),
            reward_type=result.get("rewardType", 0),
            amount=result.get("amount", 0),
            timestamp=result.get("timestamp", 0),
        )
    
    elif event_name == "ClaimVerified":
        return ClaimVerifiedEvent(
            **base_args,
            claim_id=result.get("claimId", 0),
            verifier_address=result.get("verifier", ""),
            approved=result.get("approved", False),
        )
    
    elif event_name == "SaleRecorded":
        return SaleRecordedEvent(
            **base_args,
            sale_id=result.get("saleId", 0),
            token_id=result.get("tokenId", 0),
            seller_address=result.get("seller", ""),
            buyer_address=result.get("buyer", ""),
            sale_price=result.get("salePrice", 0),
            royalty_amount=result.get("royaltyAmount", 0),
        )
    
    elif event_name == "RoyaltyPaid":
        return RoyaltyPaidEvent(
            **base_args,
            sale_id=result.get("saleId", 0),
            token_id=result.get("tokenId", 0),
            recipient_address=result.get("recipient", ""),
            amount=result.get("amount", 0),
        )
    
    return None
