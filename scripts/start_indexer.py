#!/usr/bin/env python3
"""Start blockchain event indexer daemon."""

import sys
import asyncio
import logging
import signal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcmx.tron.indexer import BlockchainIndexer
from dcmx.tron.config import TronConfig
from dcmx.database.connection import get_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndexerDaemon:
    """Indexer daemon with graceful shutdown."""
    
    def __init__(
        self,
        start_block: int = None,
        batch_size: int = 100,
        poll_interval: int = 5
    ):
        self.indexer = None
        self.start_block = start_block
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        
    async def run(self):
        """Run the indexer."""
        logger.info("Starting DCMX blockchain indexer daemon...")
        
        try:
            # Load configuration
            config = TronConfig.from_env()
            logger.info(f"Network: {config.network.value}")
            logger.info(f"Contracts configured: "
                       f"Token={bool(config.dcmx_token_address)}, "
                       f"NFT={bool(config.music_nft_address)}, "
                       f"Compliance={bool(config.compliance_registry_address)}")
            
            # Initialize database
            db = get_database()
            if not db.test_connection():
                logger.error("Database connection failed")
                return
            
            # Create indexer
            self.indexer = BlockchainIndexer(
                tron_config=config,
                db_connection=db,
                start_block=self.start_block,
                batch_size=self.batch_size,
                poll_interval=self.poll_interval,
            )
            
            # Start indexing
            await self.indexer.start()
            
        except Exception as e:
            logger.error(f"Indexer error: {e}", exc_info=True)
        finally:
            if self.indexer:
                await self.indexer.stop()
    
    async def shutdown(self, signal=None):
        """Graceful shutdown."""
        if signal:
            logger.info(f"Received exit signal {signal.name}...")
        
        if self.indexer:
            await self.indexer.stop()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Start DCMX blockchain indexer')
    parser.add_argument(
        '--start-block',
        type=int,
        help='Block number to start indexing from (default: from env or 0)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of blocks to process per batch (default: 100)'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=5,
        help='Seconds between polling for new blocks (default: 5)'
    )
    
    args = parser.parse_args()
    
    # Create daemon
    daemon = IndexerDaemon(
        start_block=args.start_block,
        batch_size=args.batch_size,
        poll_interval=args.poll_interval
    )
    
    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    
    for s in signals:
        loop.add_signal_handler(
            s,
            lambda s=s: asyncio.create_task(daemon.shutdown(s))
        )
    
    # Run daemon
    try:
        await daemon.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await daemon.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
