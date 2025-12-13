#!/usr/bin/env python3
"""
DCMX Blockchain Event Indexer Daemon

Continuously monitors and indexes blockchain events to PostgreSQL.
"""

import sys
import time
import logging
import signal
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcmx.tron.client import TronClient
from dcmx.tron.config import TronConfig
from dcmx.database.sync import BlockchainSync
from dcmx.database.database import test_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndexerDaemon:
    """
    Blockchain event indexer daemon.
    
    Runs continuously to sync events from blockchain to database.
    """
    
    def __init__(self, poll_interval: int = 30):
        """
        Initialize indexer.
        
        Args:
            poll_interval: Seconds between sync cycles
        """
        self.poll_interval = poll_interval
        self.running = False
        
        # Load configuration
        self.config = TronConfig.from_env()
        logger.info(f"Network: {self.config.network}")
        
        # Initialize clients
        self.tron_client = TronClient(self.config)
        self.sync = BlockchainSync(self.tron_client)
        
        # Contract addresses to monitor
        self.contracts = []
        if self.config.dcmx_token_address:
            self.contracts.append(self.config.dcmx_token_address)
        if self.config.music_nft_address:
            self.contracts.append(self.config.music_nft_address)
        if self.config.compliance_registry_address:
            self.contracts.append(self.config.compliance_registry_address)
        if self.config.reward_vault_address:
            self.contracts.append(self.config.reward_vault_address)
        if self.config.royalty_distributor_address:
            self.contracts.append(self.config.royalty_distributor_address)
        
        if not self.contracts:
            logger.warning("No contract addresses configured!")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self):
        """Start the indexer daemon."""
        logger.info("=== DCMX Event Indexer Starting ===")
        
        # Test database connection
        if not test_connection():
            logger.error("Database connection failed!")
            sys.exit(1)
        
        # Test blockchain connection
        if not self.tron_client.is_connected():
            logger.error("TRON connection failed!")
            sys.exit(1)
        
        logger.info(f"Monitoring {len(self.contracts)} contracts:")
        for address in self.contracts:
            logger.info(f"  - {address}")
        
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info("Indexer running... (Ctrl+C to stop)")
        
        self.running = True
        
        while self.running:
            try:
                self._sync_cycle()
                
                if self.running:
                    time.sleep(self.poll_interval)
                    
            except Exception as e:
                logger.error(f"Sync cycle error: {e}", exc_info=True)
                # Continue running despite errors
                time.sleep(self.poll_interval)
        
        logger.info("Indexer stopped")
    
    def _sync_cycle(self):
        """Execute one sync cycle."""
        logger.info("--- Sync Cycle Start ---")
        
        for contract_address in self.contracts:
            try:
                logger.info(f"Syncing {contract_address[:10]}...")
                count = self.sync.sync_events(
                    contract_address=contract_address,
                    batch_size=100
                )
                
                if count > 0:
                    logger.info(f"Synced {count} events from {contract_address[:10]}")
                else:
                    logger.debug(f"No new events from {contract_address[:10]}")
                    
            except Exception as e:
                logger.error(f"Failed to sync {contract_address}: {e}")
        
        logger.info("--- Sync Cycle Complete ---")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DCMX Blockchain Event Indexer")
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Seconds between sync cycles (default: 30)"
    )
    
    args = parser.parse_args()
    
    # Create and start indexer
    indexer = IndexerDaemon(poll_interval=args.poll_interval)
    indexer.start()


if __name__ == "__main__":
    main()
