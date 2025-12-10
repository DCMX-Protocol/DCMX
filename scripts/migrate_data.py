#!/usr/bin/env python3
"""Migrate data from file-based storage to blockchain + database."""

import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcmx.legal.acceptance import AcceptanceTracker, DocumentType
from dcmx.tron.contracts import ContractManager
from dcmx.tron.config import TronConfig
from dcmx.tron import utils
from dcmx.database.connection import get_database
from dcmx.database.models import ComplianceIndex

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataMigrator:
    """Migrate legacy data to blockchain and database."""
    
    def __init__(self):
        """Initialize migrator."""
        self.tracker = AcceptanceTracker()
        self.config = TronConfig.from_env()
        self.contracts = ContractManager(self.config)
        self.db = get_database()
        
        logger.info("Data migrator initialized")
    
    async def migrate_all(self):
        """Migrate all data."""
        logger.info("Starting data migration...")
        
        try:
            # Migrate acceptance records
            await self.migrate_acceptance_records()
            
            logger.info("Migration complete!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
    
    async def migrate_acceptance_records(self):
        """Migrate acceptance records to blockchain."""
        logger.info("Migrating acceptance records...")
        
        if not self.contracts.compliance:
            logger.error("Compliance contract not configured")
            return
        
        # Get all acceptance records from file storage
        records = self._load_legacy_acceptances()
        logger.info(f"Found {len(records)} acceptance records")
        
        migrated = 0
        failed = 0
        
        for record in records:
            try:
                # Register document version if not already registered
                doc_type = self._get_document_type_enum(record.document_type)
                doc_hash = record.document_hash or utils.compute_document_hash("legacy")
                
                # Record acceptance on blockchain
                result = self.contracts.compliance.record_acceptance(
                    user_address=record.wallet_address,
                    document_hash=doc_hash,
                    document_type=doc_type,
                    version=record.version,
                    ip_address=record.ip_address or "unknown"
                )
                
                if result.success:
                    # Also save to database
                    await self._save_to_database(record, result.transaction_hash)
                    migrated += 1
                    logger.info(
                        f"Migrated acceptance for {record.user_id}: "
                        f"tx={result.transaction_hash}"
                    )
                else:
                    failed += 1
                    logger.error(f"Failed to migrate {record.user_id}: {result.error}")
                
                # Rate limit to avoid overwhelming network
                await asyncio.sleep(0.5)
                
            except Exception as e:
                failed += 1
                logger.error(f"Error migrating record: {e}")
        
        logger.info(f"Migration complete: {migrated} succeeded, {failed} failed")
    
    def _load_legacy_acceptances(self) -> List:
        """Load acceptance records from legacy JSONL file."""
        records = []
        
        if not self.tracker.acceptance_file.exists():
            logger.warning("No legacy acceptance file found")
            return records
        
        try:
            with open(self.tracker.acceptance_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        from dcmx.legal.acceptance import AcceptanceRecord
                        records.append(AcceptanceRecord.from_dict(data))
        except Exception as e:
            logger.error(f"Failed to load legacy acceptances: {e}")
        
        return records
    
    def _get_document_type_enum(self, doc_type_str: str) -> int:
        """Convert document type string to enum value."""
        mapping = {
            'terms_and_conditions': 0,
            'privacy_policy': 1,
            'cookie_policy': 2,
            'nft_agreement': 3,
            'risk_disclosure': 4,
        }
        return mapping.get(doc_type_str, 0)
    
    async def _save_to_database(self, record, tx_hash: str):
        """Save migrated record to database."""
        try:
            with self.db.get_session() as session:
                compliance_record = ComplianceIndex(
                    user_id=record.user_id,
                    wallet_address=record.wallet_address,
                    event_type='acceptance',
                    document_type=record.document_type,
                    document_version=record.version,
                    acceptance_hash=record.document_hash,
                    blockchain_tx=tx_hash,
                    timestamp=datetime.fromisoformat(record.accepted_at),
                    ip_address_hash=record.ip_address,
                )
                session.add(compliance_record)
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate DCMX data to blockchain')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migration without executing'
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - no changes will be made")
    else:
        # Confirm migration
        response = input(
            "This will migrate data to blockchain. "
            "Are you sure? (type 'yes' to confirm): "
        )
        if response.lower() != 'yes':
            logger.info("Migration cancelled")
            return
    
    # Run migration
    migrator = DataMigrator()
    
    if not args.dry_run:
        await migrator.migrate_all()
    else:
        logger.info("Dry run complete")


if __name__ == '__main__':
    asyncio.run(main())
