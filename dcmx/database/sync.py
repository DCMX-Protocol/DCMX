"""
Blockchain-to-Database Sync

Synchronizes blockchain events to PostgreSQL for indexing.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from dcmx.tron.client import TronClient
from dcmx.tron.events import parse_event, BaseEvent
from .models import (
    BlockchainEvent,
    NFTIndex,
    UserProfile,
    RewardClaimIndex,
    TransactionIndex,
    ComplianceIndex,
)
from .database import get_session

logger = logging.getLogger(__name__)


class BlockchainSync:
    """
    Synchronize blockchain events to database.
    
    Processes events and updates indexed tables.
    """
    
    def __init__(self, tron_client: TronClient):
        """
        Initialize sync manager.
        
        Args:
            tron_client: TRON blockchain client
        """
        self.client = tron_client
    
    def sync_events(
        self,
        contract_address: str,
        from_block: Optional[int] = None,
        to_block: Optional[int] = None,
        batch_size: int = 200
    ) -> int:
        """
        Sync events from contract to database.
        
        Args:
            contract_address: Contract to sync
            from_block: Starting block (None = last synced)
            to_block: Ending block (None = latest)
            batch_size: Events per batch
            
        Returns:
            Number of events synced
        """
        session = get_session()
        
        try:
            # Get last synced block if not provided
            if from_block is None:
                from_block = self._get_last_synced_block(session, contract_address)
            
            # Get latest block if not provided
            if to_block is None:
                to_block = self.client.get_latest_block_number()
            
            logger.info(
                f"Syncing events for {contract_address}: "
                f"blocks {from_block} to {to_block}"
            )
            
            total_synced = 0
            current_block = from_block
            
            while current_block <= to_block:
                # Get events in batch
                batch_end = min(current_block + batch_size, to_block)
                
                events = self.client.get_events_by_contract(
                    contract_address=contract_address,
                    min_block=current_block,
                    max_block=batch_end,
                    limit=batch_size
                )
                
                # Process events
                for event_data in events:
                    self._process_event(session, event_data)
                    total_synced += 1
                
                session.commit()
                current_block = batch_end + 1
                
                logger.debug(f"Synced {total_synced} events, up to block {batch_end}")
            
            logger.info(f"Sync complete: {total_synced} events indexed")
            return total_synced
            
        except Exception as e:
            session.rollback()
            logger.error(f"Sync failed: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def _get_last_synced_block(self, session: Session, contract_address: str) -> int:
        """Get last synced block number for contract."""
        result = (
            session.query(BlockchainEvent.block_number)
            .filter(BlockchainEvent.contract_address == contract_address)
            .order_by(BlockchainEvent.block_number.desc())
            .first()
        )
        
        return result[0] if result else 0
    
    def _process_event(self, session: Session, event_data: Dict[str, Any]):
        """
        Process a single event.
        
        Args:
            session: Database session
            event_data: Raw event data from blockchain
        """
        # Parse event
        event = parse_event(event_data)
        if not event:
            logger.warning(f"Unknown event type: {event_data.get('event_name')}")
            return
        
        # Check if already indexed
        existing = (
            session.query(BlockchainEvent)
            .filter(BlockchainEvent.transaction_hash == event.transaction_hash)
            .first()
        )
        
        if existing:
            logger.debug(f"Event already indexed: {event.transaction_hash}")
            return
        
        # Store raw event
        db_event = BlockchainEvent(
            transaction_hash=event.transaction_hash,
            block_number=event.block_number,
            block_timestamp=event.block_timestamp,
            contract_address=event.contract_address,
            event_name=event.event_type,
            event_data=event.to_dict(),
            indexed_at=datetime.utcnow(),
            processed=False,
        )
        session.add(db_event)
        
        # Process event type-specific indexing
        self._index_event(session, event)
        
        # Mark as processed
        db_event.processed = True
    
    def _index_event(self, session: Session, event: BaseEvent):
        """
        Index event to appropriate tables.
        
        Args:
            session: Database session
            event: Parsed event
        """
        from dcmx.tron.events import (
            MusicMintedEvent,
            RewardClaimedEvent,
            TransferEvent,
            AcceptanceRecordedEvent,
        )
        
        # Index based on event type
        if isinstance(event, MusicMintedEvent):
            self._index_music_minted(session, event)
        
        elif isinstance(event, RewardClaimedEvent):
            self._index_reward_claimed(session, event)
        
        elif isinstance(event, TransferEvent):
            self._index_transfer(session, event)
        
        elif isinstance(event, AcceptanceRecordedEvent):
            self._index_acceptance(session, event)
    
    def _index_music_minted(self, session: Session, event):
        """Index MusicMinted event."""
        nft = NFTIndex(
            token_id=event.token_id,
            contract_address=event.contract_address,
            title=event.title,
            artist=event.artist,
            content_hash=event.content_hash,
            edition_number=event.edition_number,
            max_editions=event.max_editions,
            owner_wallet=event.artist_address,  # Initially owned by artist
            artist_wallet=event.artist_address,
            minted_at=datetime.fromtimestamp(event.block_timestamp),
            indexed_at=datetime.utcnow(),
        )
        session.add(nft)
        logger.debug(f"Indexed NFT mint: token_id={event.token_id}")
    
    def _index_reward_claimed(self, session: Session, event):
        """Index RewardClaimed event."""
        claim = RewardClaimIndex(
            claim_id=event.claim_id,
            claimant_wallet=event.claimant_address,
            reward_type=event.reward_type,
            amount=event.amount,
            verified=True,  # Only claimed if verified
            claimed=True,
            submitted_at=datetime.fromtimestamp(event.timestamp),
            claimed_at=datetime.fromtimestamp(event.timestamp),
            indexed_at=datetime.utcnow(),
        )
        session.add(claim)
        logger.debug(f"Indexed reward claim: claim_id={event.claim_id}")
    
    def _index_transfer(self, session: Session, event):
        """Index Transfer event."""
        tx = TransactionIndex(
            transaction_hash=event.transaction_hash,
            block_number=event.block_number,
            from_wallet=event.from_address,
            to_wallet=event.to_address,
            tx_type="transfer",
            contract_address=event.contract_address,
            token_amount=event.value if event.value else None,
            timestamp=datetime.fromtimestamp(event.block_timestamp),
            indexed_at=datetime.utcnow(),
        )
        session.add(tx)
        
        # Update NFT owner if TRC-721 transfer
        if event.token_id is not None:
            nft = (
                session.query(NFTIndex)
                .filter(NFTIndex.token_id == event.token_id)
                .filter(NFTIndex.contract_address == event.contract_address)
                .first()
            )
            
            if nft:
                nft.owner_wallet = event.to_address
                nft.last_transferred_at = datetime.utcnow()
        
        logger.debug(f"Indexed transfer: {event.transaction_hash}")
    
    def _index_acceptance(self, session: Session, event):
        """Index AcceptanceRecorded event."""
        acceptance = ComplianceIndex(
            record_id=event.record_id,
            wallet_address=event.wallet_address,
            document_type=event.document_type,
            document_version=event.version,
            document_hash=event.document_hash,
            accepted_at=datetime.fromtimestamp(event.timestamp),
            indexed_at=datetime.utcnow(),
        )
        session.add(acceptance)
        logger.debug(f"Indexed compliance acceptance: record_id={event.record_id}")
    
    def sync_all_contracts(self, contract_addresses: List[str]) -> Dict[str, int]:
        """
        Sync events from multiple contracts.
        
        Args:
            contract_addresses: List of contract addresses
            
        Returns:
            Dict mapping contract address to events synced
        """
        results = {}
        
        for address in contract_addresses:
            try:
                count = self.sync_events(address)
                results[address] = count
            except Exception as e:
                logger.error(f"Failed to sync {address}: {e}")
                results[address] = 0
        
        return results
    
    def resync_from_block(self, contract_address: str, from_block: int):
        """
        Resync events from a specific block.
        
        Useful for reprocessing data after changes.
        
        Args:
            contract_address: Contract address
            from_block: Block to resync from
        """
        session = get_session()
        
        try:
            # Delete events from this block onwards
            session.query(BlockchainEvent).filter(
                BlockchainEvent.contract_address == contract_address,
                BlockchainEvent.block_number >= from_block
            ).delete()
            
            session.commit()
            logger.info(f"Deleted events from block {from_block} for {contract_address}")
            
            # Resync
            self.sync_events(contract_address, from_block=from_block)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Resync failed: {e}", exc_info=True)
            raise
        finally:
            session.close()
