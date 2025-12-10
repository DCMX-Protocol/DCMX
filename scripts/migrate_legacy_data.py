#!/usr/bin/env python3
"""
Migrate legacy data to database.

Migrates from:
- JSONL files (legal acceptances) -> database
- In-memory dictionaries (API server) -> database
- SQLite audit logs -> unified database

Usage:
    python scripts/migrate_legacy_data.py [--source-dir PATH] [--dry-run]
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dcmx.database.database import get_db_manager
from dcmx.database.dal import DataAccessLayer
from dcmx.database.models import AcceptanceRecord, AuditEvent


logger = logging.getLogger(__name__)


class LegacyDataMigrator:
    """Migrate legacy data to database."""
    
    def __init__(self, source_dir: Path, dry_run: bool = False):
        """
        Initialize migrator.
        
        Args:
            source_dir: Directory containing legacy data files
            dry_run: If True, don't actually write to database
        """
        self.source_dir = source_dir
        self.dry_run = dry_run
        self.db_manager = get_db_manager()
        self.dal = DataAccessLayer()
        
        self.stats = {
            'acceptances_migrated': 0,
            'audit_events_migrated': 0,
            'errors': []
        }
    
    def find_acceptance_files(self) -> List[Path]:
        """Find all acceptance JSONL files."""
        files = []
        
        # Common locations
        search_paths = [
            self.source_dir / "compliance" / "acceptances.jsonl",
            Path.home() / ".dcmx" / "compliance" / "acceptances.jsonl",
            Path("/var/lib/dcmx/compliance/acceptances.jsonl"),
        ]
        
        for path in search_paths:
            if path.exists():
                files.append(path)
                logger.info(f"Found acceptance file: {path}")
        
        return files
    
    async def migrate_acceptances(self) -> int:
        """
        Migrate acceptance records from JSONL files.
        
        Returns:
            Number of records migrated
        """
        files = self.find_acceptance_files()
        
        if not files:
            logger.warning("No acceptance files found")
            return 0
        
        count = 0
        
        async with self.db_manager.get_async_session() as session:
            for file_path in files:
                logger.info(f"Migrating acceptances from: {file_path}")
                
                try:
                    with open(file_path, 'r') as f:
                        for line_num, line in enumerate(f, 1):
                            if not line.strip():
                                continue
                            
                            try:
                                data = json.loads(line)
                                
                                # Check if already exists
                                existing = await self.dal.get_acceptance(
                                    session,
                                    user_id=data['user_id'],
                                    document_type=data['document_type']
                                )
                                
                                if existing and existing.version == data['version']:
                                    logger.debug(f"Skipping duplicate: {data['user_id']} - {data['document_type']}")
                                    continue
                                
                                if not self.dry_run:
                                    await self.dal.record_acceptance(
                                        session,
                                        user_id=data['user_id'],
                                        wallet_address=data['wallet_address'],
                                        document_type=data['document_type'],
                                        version=data['version'],
                                        ip_address=data.get('ip_address'),
                                        user_agent=data.get('user_agent'),
                                        signature=data.get('signature'),
                                        read_time_seconds=data.get('read_time_seconds', 0),
                                        document_hash=data.get('document_hash')
                                    )
                                
                                count += 1
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"Invalid JSON at line {line_num}: {e}")
                                self.stats['errors'].append(f"File {file_path} line {line_num}: {e}")
                            except Exception as e:
                                logger.error(f"Error migrating acceptance at line {line_num}: {e}")
                                self.stats['errors'].append(f"File {file_path} line {line_num}: {e}")
                
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    self.stats['errors'].append(f"File {file_path}: {e}")
        
        self.stats['acceptances_migrated'] = count
        logger.info(f"Migrated {count} acceptance records")
        return count
    
    def find_audit_db(self) -> List[Path]:
        """Find SQLite audit log databases."""
        files = []
        
        search_paths = [
            self.source_dir / "compliance_audit.db",
            Path("compliance_audit.db"),
            Path.home() / ".dcmx" / "compliance_audit.db",
        ]
        
        for path in search_paths:
            if path.exists():
                files.append(path)
                logger.info(f"Found audit database: {path}")
        
        return files
    
    async def migrate_audit_logs(self) -> int:
        """
        Migrate audit logs from SQLite to main database.
        
        Returns:
            Number of records migrated
        """
        import sqlite3
        
        db_files = self.find_audit_db()
        
        if not db_files:
            logger.warning("No audit log databases found")
            return 0
        
        count = 0
        
        async with self.db_manager.get_async_session() as session:
            for db_path in db_files:
                logger.info(f"Migrating audit logs from: {db_path}")
                
                try:
                    conn = sqlite3.connect(str(db_path))
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Get all audit events
                    cursor.execute("SELECT * FROM audit_events")
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        try:
                            if not self.dry_run:
                                await self.dal.log_audit_event(
                                    session,
                                    event_id=row['event_id'],
                                    event_type=row['event_type'],
                                    user_id=row['user_id'],
                                    wallet_address=row['wallet_address'],
                                    resource_type=row['resource_type'],
                                    resource_id=row['resource_id'],
                                    action=row['action'],
                                    status=row['status'],
                                    result=row['result'],
                                    amount=row['amount'],
                                    currency=row['currency'],
                                    jurisdiction=row['jurisdiction'],
                                    kyc_level=row['kyc_level'],
                                    risk_score=row['risk_score'],
                                    ip_address=row['ip_address'],
                                    user_agent=row['user_agent'],
                                    session_id=row['session_id'],
                                    details=json.loads(row['details']) if row['details'] else {},
                                    error_message=row['error_message'],
                                    hash=row['hash'],
                                    parent_hash=row['parent_hash']
                                )
                            
                            count += 1
                            
                        except Exception as e:
                            logger.error(f"Error migrating audit event {row['event_id']}: {e}")
                            self.stats['errors'].append(f"Event {row['event_id']}: {e}")
                    
                    conn.close()
                    
                except Exception as e:
                    logger.error(f"Error reading database {db_path}: {e}")
                    self.stats['errors'].append(f"Database {db_path}: {e}")
        
        self.stats['audit_events_migrated'] = count
        logger.info(f"Migrated {count} audit events")
        return count
    
    async def migrate_all(self):
        """Migrate all legacy data."""
        logger.info("Starting legacy data migration...")
        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("="*60)
        
        # Migrate acceptances
        logger.info("\n1. Migrating acceptance records...")
        await self.migrate_acceptances()
        
        # Migrate audit logs
        logger.info("\n2. Migrating audit logs...")
        await self.migrate_audit_logs()
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("MIGRATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Acceptance records: {self.stats['acceptances_migrated']}")
        logger.info(f"Audit events: {self.stats['audit_events_migrated']}")
        
        if self.stats['errors']:
            logger.warning(f"\nErrors encountered: {len(self.stats['errors'])}")
            logger.warning("First 5 errors:")
            for error in self.stats['errors'][:5]:
                logger.warning(f"  - {error}")
        
        logger.info("="*60)
        
        if self.dry_run:
            logger.info("\n⚠️  DRY RUN - No data was actually migrated")
        else:
            logger.info("\n✓ Migration completed!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Migrate legacy DCMX data to database'
    )
    parser.add_argument(
        '--source-dir',
        type=Path,
        default=Path.home() / '.dcmx',
        help='Directory containing legacy data files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't actually write to database"
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create migrator
    migrator = LegacyDataMigrator(
        source_dir=args.source_dir,
        dry_run=args.dry_run
    )
    
    # Run migration
    try:
        asyncio.run(migrator.migrate_all())
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
