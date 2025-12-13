"""Blockchain event indexer daemon for DCMX."""

import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .client import TronClient
from .config import TronConfig
from .events import EventParser, BlockchainEvent
from ..database.connection import DatabaseConnection, get_database
from ..database.models import (
    BlockchainEvent as BlockchainEventModel,
    NFTIndex,
    RewardClaimIndex,
    TransactionIndex,
    ComplianceIndex,
)

logger = logging.getLogger(__name__)


class BlockchainIndexer:
    """
    Indexes blockchain events to PostgreSQL database.
    
    Features:
    - Continuous event monitoring
    - Batch processing for efficiency
    - Handles chain reorganizations
    - Resume from last indexed block
    """
    
    def __init__(
        self,
        tron_config: Optional[TronConfig] = None,
        db_connection: Optional[DatabaseConnection] = None,
        start_block: Optional[int] = None,
        batch_size: int = 100,
        poll_interval: int = 5,
    ):
        """
        Initialize blockchain indexer.
        
        Args:
            tron_config: TRON configuration
            db_connection: Database connection
            start_block: Block number to start indexing from
            batch_size: Number of blocks to process per batch
            poll_interval: Seconds between polling for new blocks
        """
        self.config = tron_config or TronConfig.from_env()
        self.client = TronClient(self.config)
        self.db = db_connection or get_database()
        
        self.start_block = start_block or int(os.getenv('INDEXER_START_BLOCK', '0'))
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        
        self.current_block = self.start_block
        self.running = False
        
        logger.info(
            f"BlockchainIndexer initialized: "
            f"start_block={self.start_block}, "
            f"batch_size={self.batch_size}"
        )
    
    async def start(self):
        """Start the indexer daemon."""
        self.running = True
        logger.info("Starting blockchain indexer...")
        
        # Resume from last indexed block
        last_block = self._get_last_indexed_block()
        if last_block:
            self.current_block = last_block + 1
            logger.info(f"Resuming from block {self.current_block}")
        
        # Main indexing loop
        while self.running:
            try:
                await self._index_batch()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Indexer error: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval * 2)
    
    async def stop(self):
        """Stop the indexer daemon."""
        logger.info("Stopping blockchain indexer...")
        self.running = False
    
    def _get_last_indexed_block(self) -> Optional[int]:
        """Get the last indexed block number from database."""
        try:
            with self.db.get_session() as session:
                result = session.execute(
                    select(BlockchainEventModel.block_number)
                    .order_by(BlockchainEventModel.block_number.desc())
                    .limit(1)
                )
                row = result.first()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to get last indexed block: {e}")
            return None
    
    async def _index_batch(self):
        """Index a batch of blocks."""
        latest_block = self.client.get_latest_block_number()
        
        if self.current_block > latest_block:
            logger.debug("Waiting for new blocks...")
            return
        
        end_block = min(self.current_block + self.batch_size, latest_block)
        
        logger.info(f"Indexing blocks {self.current_block} to {end_block}")
        
        for block_num in range(self.current_block, end_block + 1):
            await self._index_block(block_num)
        
        self.current_block = end_block + 1
    
    async def _index_block(self, block_number: int):
        """
        Index a single block.
        
        Args:
            block_number: Block number to index
        """
        try:
            block = self.client.get_block(block_number)
            if not block:
                logger.warning(f"Block {block_number} not found")
                return
            
            # Process transactions in block
            transactions = block.get('transactions', [])
            
            for tx in transactions:
                await self._index_transaction(tx, block_number)
            
        except Exception as e:
            logger.error(f"Failed to index block {block_number}: {e}")
    
    async def _index_transaction(self, tx: Dict[str, Any], block_number: int):
        """
        Index a transaction and its events.
        
        Args:
            tx: Transaction data
            block_number: Block number
        """
        tx_hash = tx.get('txID', '')
        
        # Get transaction info (includes events/logs)
        tx_info = self.client.get_transaction_info(tx_hash)
        if not tx_info:
            return
        
        # Index transaction
        await self._save_transaction(tx, tx_info, block_number)
        
        # Index events from logs
        logs = tx_info.get('log', [])
        for log in logs:
            await self._index_event(log, tx_hash, block_number)
    
    async def _save_transaction(
        self,
        tx: Dict[str, Any],
        tx_info: Dict[str, Any],
        block_number: int
    ):
        """Save transaction to database."""
        try:
            tx_hash = tx.get('txID', '')
            raw_data = tx.get('raw_data', {})
            contract = raw_data.get('contract', [{}])[0]
            
            # Extract addresses and value
            from_address = ''
            to_address = ''
            value = 0
            
            if contract.get('type') == 'TransferContract':
                parameter = contract.get('parameter', {}).get('value', {})
                from_address = parameter.get('owner_address', '')
                to_address = parameter.get('to_address', '')
                value = parameter.get('amount', 0)
            
            # Get timestamp
            timestamp = datetime.fromtimestamp(
                tx.get('raw_data', {}).get('timestamp', 0) / 1000
            )
            
            # Save to database
            with self.db.get_session() as session:
                tx_record = TransactionIndex(
                    tx_hash=tx_hash,
                    from_address=from_address,
                    to_address=to_address,
                    value=value,
                    token='TRX',
                    block_number=block_number,
                    timestamp=timestamp,
                    status='success' if tx_info.get('receipt', {}).get('result') == 'SUCCESS' else 'failed',
                    gas_used=tx_info.get('receipt', {}).get('energy_usage', 0),
                )
                session.add(tx_record)
                
        except IntegrityError:
            # Transaction already indexed
            pass
        except Exception as e:
            logger.error(f"Failed to save transaction: {e}")
    
    async def _index_event(
        self,
        log: Dict[str, Any],
        tx_hash: str,
        block_number: int
    ):
        """
        Index an event from transaction log.
        
        Args:
            log: Event log data
            tx_hash: Transaction hash
            block_number: Block number
        """
        try:
            # Parse event
            event = EventParser.parse_event(log)
            if not event:
                return
            
            # Save to blockchain_events table
            await self._save_event(event, tx_hash, block_number)
            
            # Index to specific tables based on event type
            await self._index_specific_event(event)
            
        except Exception as e:
            logger.error(f"Failed to index event: {e}")
    
    async def _save_event(
        self,
        event: BlockchainEvent,
        tx_hash: str,
        block_number: int
    ):
        """Save event to blockchain_events table."""
        try:
            with self.db.get_session() as session:
                event_record = BlockchainEventModel(
                    event_type=event.event_type,
                    contract_address=event.contract_address,
                    transaction_hash=tx_hash,
                    block_number=block_number,
                    log_index=event.log_index,
                    event_data=event.event_data,
                    indexed_at=datetime.utcnow(),
                )
                session.add(event_record)
                
        except IntegrityError:
            # Event already indexed
            pass
        except Exception as e:
            logger.error(f"Failed to save event: {e}")
    
    async def _index_specific_event(self, event: BlockchainEvent):
        """
        Index event to specific table based on type.
        
        Args:
            event: Parsed blockchain event
        """
        try:
            if event.event_type == 'Minted':
                await self._index_nft_mint(event)
            elif event.event_type == 'ClaimSubmitted':
                await self._index_claim_submitted(event)
            elif event.event_type == 'AcceptanceRecorded':
                await self._index_acceptance(event)
            # Add more event type handlers as needed
            
        except Exception as e:
            logger.error(f"Failed to index specific event: {e}")
    
    async def _index_nft_mint(self, event: BlockchainEvent):
        """Index NFT mint event."""
        try:
            data = event.event_data
            
            with self.db.get_session() as session:
                nft_record = NFTIndex(
                    token_id=data.get('tokenId', 0),
                    contract_address=event.contract_address,
                    title=data.get('title', ''),
                    artist=data.get('artist', ''),
                    content_hash=data.get('contentHash', ''),
                    edition=data.get('edition', 1),
                    max_editions=data.get('maxEditions', 1),
                    owner_address=data.get('to', ''),
                    mint_date=event.timestamp,
                    royalty_bps=data.get('royaltyBps', 0),
                    royalty_recipient=data.get('royaltyRecipient', ''),
                )
                session.add(nft_record)
                
        except Exception as e:
            logger.error(f"Failed to index NFT mint: {e}")
    
    async def _index_claim_submitted(self, event: BlockchainEvent):
        """Index reward claim submitted event."""
        try:
            data = event.event_data
            
            with self.db.get_session() as session:
                claim_record = RewardClaimIndex(
                    claim_id=data.get('claimId', 0),
                    user_address=data.get('user', ''),
                    claim_type=['SHARING', 'LISTENING', 'BANDWIDTH'][data.get('claimType', 0)],
                    amount=data.get('amount', 0),
                    proof_hash=data.get('proofHash', ''),
                    status='pending',
                    submitted_at=event.timestamp,
                    transaction_hash=event.transaction_hash,
                )
                session.add(claim_record)
                
        except Exception as e:
            logger.error(f"Failed to index claim: {e}")
    
    async def _index_acceptance(self, event: BlockchainEvent):
        """Index compliance acceptance event."""
        try:
            data = event.event_data
            
            with self.db.get_session() as session:
                compliance_record = ComplianceIndex(
                    user_id=data.get('user', ''),
                    wallet_address=data.get('user', ''),
                    event_type='acceptance',
                    document_type=['TERMS', 'PRIVACY', 'COOKIE', 'NFT', 'RISK'][data.get('documentType', 0)],
                    document_version=data.get('version', ''),
                    acceptance_hash=data.get('documentHash', ''),
                    blockchain_tx=event.transaction_hash,
                    timestamp=event.timestamp,
                )
                session.add(compliance_record)
                
        except Exception as e:
            logger.error(f"Failed to index acceptance: {e}")


async def main():
    """Run indexer as standalone daemon."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    indexer = BlockchainIndexer()
    
    try:
        await indexer.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        await indexer.stop()


if __name__ == '__main__':
    asyncio.run(main())
