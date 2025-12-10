"""TRON smart contract event definitions and handlers."""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Smart contract event types."""
    # Token events
    TOKEN_TRANSFER = "Transfer"
    TOKEN_APPROVAL = "Approval"
    TOKEN_MINT = "Mint"
    TOKEN_BURN = "Burn"
    
    # NFT events
    NFT_MINTED = "Minted"
    NFT_TRANSFER = "Transfer"
    NFT_APPROVAL = "Approval"
    NFT_APPROVAL_FOR_ALL = "ApprovalForAll"
    
    # Compliance events
    ACCEPTANCE_RECORDED = "AcceptanceRecorded"
    DELETION_REQUESTED = "DeletionRequested"
    DELETION_PROCESSED = "DeletionProcessed"
    DOCUMENT_VERSION_REGISTERED = "DocumentVersionRegistered"
    
    # Reward events
    CLAIM_SUBMITTED = "ClaimSubmitted"
    CLAIM_VERIFIED = "ClaimVerified"
    REWARDS_CLAIMED = "RewardsClaimed"
    POOL_ALLOCATED = "PoolAllocated"
    
    # Royalty events
    SALE_RECORDED = "SaleRecorded"
    ROYALTIES_DISTRIBUTED = "RoyaltiesDistributed"
    ROYALTY_PAID = "RoyaltyPaid"
    ROYALTY_SPLIT_SET = "RoyaltySplitSet"
    WITHDRAWAL = "Withdrawal"


@dataclass
class BlockchainEvent:
    """Base blockchain event."""
    event_type: str
    contract_address: str
    transaction_hash: str
    block_number: int
    log_index: int
    timestamp: datetime
    event_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'event_type': self.event_type,
            'contract_address': self.contract_address,
            'transaction_hash': self.transaction_hash,
            'block_number': self.block_number,
            'log_index': self.log_index,
            'timestamp': self.timestamp.isoformat(),
            'event_data': self.event_data,
        }


@dataclass
class TokenTransferEvent(BlockchainEvent):
    """Token transfer event."""
    from_address: str = ""
    to_address: str = ""
    value: int = 0
    
    @classmethod
    def from_log(cls, log_data: Dict[str, Any]) -> 'TokenTransferEvent':
        """Parse from transaction log."""
        event_data = log_data.get('result', {})
        return cls(
            event_type=EventType.TOKEN_TRANSFER.value,
            contract_address=log_data.get('contract_address', ''),
            transaction_hash=log_data.get('transaction_id', ''),
            block_number=log_data.get('block_number', 0),
            log_index=log_data.get('log_index', 0),
            timestamp=datetime.fromtimestamp(log_data.get('block_timestamp', 0) / 1000),
            event_data=event_data,
            from_address=event_data.get('from', ''),
            to_address=event_data.get('to', ''),
            value=int(event_data.get('value', 0)),
        )


@dataclass
class NFTMintedEvent(BlockchainEvent):
    """NFT minted event."""
    to_address: str = ""
    token_id: int = 0
    content_hash: str = ""
    
    @classmethod
    def from_log(cls, log_data: Dict[str, Any]) -> 'NFTMintedEvent':
        """Parse from transaction log."""
        event_data = log_data.get('result', {})
        return cls(
            event_type=EventType.NFT_MINTED.value,
            contract_address=log_data.get('contract_address', ''),
            transaction_hash=log_data.get('transaction_id', ''),
            block_number=log_data.get('block_number', 0),
            log_index=log_data.get('log_index', 0),
            timestamp=datetime.fromtimestamp(log_data.get('block_timestamp', 0) / 1000),
            event_data=event_data,
            to_address=event_data.get('to', ''),
            token_id=int(event_data.get('tokenId', 0)),
            content_hash=event_data.get('contentHash', ''),
        )


@dataclass
class AcceptanceRecordedEvent(BlockchainEvent):
    """Compliance acceptance recorded event."""
    user_address: str = ""
    document_type: int = 0
    document_hash: str = ""
    version: str = ""
    
    @classmethod
    def from_log(cls, log_data: Dict[str, Any]) -> 'AcceptanceRecordedEvent':
        """Parse from transaction log."""
        event_data = log_data.get('result', {})
        return cls(
            event_type=EventType.ACCEPTANCE_RECORDED.value,
            contract_address=log_data.get('contract_address', ''),
            transaction_hash=log_data.get('transaction_id', ''),
            block_number=log_data.get('block_number', 0),
            log_index=log_data.get('log_index', 0),
            timestamp=datetime.fromtimestamp(log_data.get('block_timestamp', 0) / 1000),
            event_data=event_data,
            user_address=event_data.get('user', ''),
            document_type=int(event_data.get('documentType', 0)),
            document_hash=event_data.get('documentHash', ''),
            version=event_data.get('version', ''),
        )


@dataclass
class ClaimSubmittedEvent(BlockchainEvent):
    """Reward claim submitted event."""
    claim_id: int = 0
    user_address: str = ""
    claim_type: int = 0
    amount: int = 0
    proof_hash: str = ""
    
    @classmethod
    def from_log(cls, log_data: Dict[str, Any]) -> 'ClaimSubmittedEvent':
        """Parse from transaction log."""
        event_data = log_data.get('result', {})
        return cls(
            event_type=EventType.CLAIM_SUBMITTED.value,
            contract_address=log_data.get('contract_address', ''),
            transaction_hash=log_data.get('transaction_id', ''),
            block_number=log_data.get('block_number', 0),
            log_index=log_data.get('log_index', 0),
            timestamp=datetime.fromtimestamp(log_data.get('block_timestamp', 0) / 1000),
            event_data=event_data,
            claim_id=int(event_data.get('claimId', 0)),
            user_address=event_data.get('user', ''),
            claim_type=int(event_data.get('claimType', 0)),
            amount=int(event_data.get('amount', 0)),
            proof_hash=event_data.get('proofHash', ''),
        )


@dataclass
class SaleRecordedEvent(BlockchainEvent):
    """NFT sale recorded event."""
    sale_id: int = 0
    nft_contract: str = ""
    nft_token_id: int = 0
    seller: str = ""
    buyer: str = ""
    sale_price: int = 0
    
    @classmethod
    def from_log(cls, log_data: Dict[str, Any]) -> 'SaleRecordedEvent':
        """Parse from transaction log."""
        event_data = log_data.get('result', {})
        return cls(
            event_type=EventType.SALE_RECORDED.value,
            contract_address=log_data.get('contract_address', ''),
            transaction_hash=log_data.get('transaction_id', ''),
            block_number=log_data.get('block_number', 0),
            log_index=log_data.get('log_index', 0),
            timestamp=datetime.fromtimestamp(log_data.get('block_timestamp', 0) / 1000),
            event_data=event_data,
            sale_id=int(event_data.get('saleId', 0)),
            nft_contract=event_data.get('nftContract', ''),
            nft_token_id=int(event_data.get('nftTokenId', 0)),
            seller=event_data.get('seller', ''),
            buyer=event_data.get('buyer', ''),
            sale_price=int(event_data.get('salePrice', 0)),
        )


class EventParser:
    """Parse blockchain events from transaction logs."""
    
    @staticmethod
    def parse_event(log_data: Dict[str, Any]) -> Optional[BlockchainEvent]:
        """
        Parse event from transaction log.
        
        Args:
            log_data: Raw log data from blockchain
            
        Returns:
            Parsed event or None if unknown
        """
        event_name = log_data.get('event_name', '')
        
        parsers = {
            EventType.TOKEN_TRANSFER.value: TokenTransferEvent.from_log,
            EventType.NFT_MINTED.value: NFTMintedEvent.from_log,
            EventType.ACCEPTANCE_RECORDED.value: AcceptanceRecordedEvent.from_log,
            EventType.CLAIM_SUBMITTED.value: ClaimSubmittedEvent.from_log,
            EventType.SALE_RECORDED.value: SaleRecordedEvent.from_log,
        }
        
        parser = parsers.get(event_name)
        if parser:
            try:
                return parser(log_data)
            except Exception as e:
                logger.error(f"Failed to parse event {event_name}: {e}")
                return None
        else:
            # Generic event
            return BlockchainEvent(
                event_type=event_name,
                contract_address=log_data.get('contract_address', ''),
                transaction_hash=log_data.get('transaction_id', ''),
                block_number=log_data.get('block_number', 0),
                log_index=log_data.get('log_index', 0),
                timestamp=datetime.fromtimestamp(log_data.get('block_timestamp', 0) / 1000),
                event_data=log_data.get('result', {}),
            )
