#!/usr/bin/env python3
"""
Database initialization script for DCMX.

Usage:
    python scripts/init_database.py [--drop] [--verify] [--async]
    
Options:
    --drop      Drop all existing tables before creating (DANGER!)
    --verify    Verify database after initialization
    --async     Use async initialization
    --sqlite    Use SQLite instead of PostgreSQL
    
Environment Variables:
    DCMX_DB_HOST        Database host (default: localhost)
    DCMX_DB_PORT        Database port (default: 5432)
    DCMX_DB_NAME        Database name (default: dcmx)
    DCMX_DB_USER        Database user (default: dcmx_app)
    DCMX_DB_PASSWORD    Database password (default: dcmx_password)
    DCMX_DB_USE_SQLITE  Use SQLite (true/false)
"""

import argparse
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dcmx.database.config import DatabaseConfig, config
from dcmx.database.migrations import DatabaseMigration


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Initialize DCMX database schema'
    )
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Drop all existing tables before creating (DANGER!)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify database after initialization'
    )
    parser.add_argument(
        '--async',
        dest='use_async',
        action='store_true',
        help='Use async initialization'
    )
    parser.add_argument(
        '--sqlite',
        action='store_true',
        help='Use SQLite instead of PostgreSQL'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show migration status only'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Override SQLite if requested
    if args.sqlite:
        os.environ['DCMX_DB_USE_SQLITE'] = 'true'
        # Reload config
        from dcmx.database.config import DatabaseConfig
        db_config = DatabaseConfig.from_env()
    else:
        db_config = config
    
    # Initialize migration manager
    from dcmx.database.database import DatabaseManager
    db_manager = DatabaseManager(db_config)
    migration = DatabaseMigration(db_manager)
    
    # Show status if requested
    if args.status:
        logger.info("Checking database migration status...")
        status = migration.get_migration_status()
        
        print("\n" + "="*60)
        print("DATABASE MIGRATION STATUS")
        print("="*60)
        print(f"Status: {status['status']}")
        print(f"Initialized: {status['initialized']}")
        print(f"Tables: {status.get('table_count', 0)}")
        
        if status.get('tables'):
            print("\nTables found:")
            for table in status['tables']:
                print(f"  - {table}")
        
        if status.get('config_count'):
            print(f"\nConfigurations: {status['config_count']}")
        
        if status.get('error'):
            print(f"\nError: {status['error']}")
        
        print("="*60 + "\n")
        return
    
    # Confirm drop if requested
    if args.drop:
        logger.warning("⚠️  WARNING: You are about to DROP ALL TABLES!")
        logger.warning("⚠️  This will DELETE ALL DATA in the database!")
        
        response = input("Are you sure? Type 'yes' to continue: ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            return
    
    # Initialize database
    try:
        logger.info("="*60)
        logger.info("DCMX DATABASE INITIALIZATION")
        logger.info("="*60)
        logger.info(f"Database Type: {'SQLite' if db_config.use_sqlite else 'PostgreSQL'}")
        
        if not db_config.use_sqlite:
            logger.info(f"Database Host: {db_config.host}:{db_config.port}")
            logger.info(f"Database Name: {db_config.database}")
            logger.info(f"Database User: {db_config.username}")
        else:
            logger.info(f"SQLite Path: {db_config.sqlite_path}")
        
        logger.info("="*60)
        
        if args.use_async:
            logger.info("Using async initialization...")
            asyncio.run(migration.initialize_database_async(drop_existing=args.drop))
        else:
            logger.info("Using sync initialization...")
            migration.initialize_database(drop_existing=args.drop)
        
        logger.info("✓ Database initialized successfully!")
        
        # Verify if requested
        if args.verify:
            logger.info("\nVerifying database...")
            
            if args.use_async:
                is_valid = asyncio.run(migration.verify_database_async())
            else:
                is_valid = migration.verify_database()
            
            if is_valid:
                logger.info("✓ Database verification passed!")
            else:
                logger.error("✗ Database verification failed!")
                sys.exit(1)
        
        # Show final status
        logger.info("\n" + "="*60)
        status = migration.get_migration_status()
        logger.info(f"Tables created: {status['table_count']}")
        logger.info(f"Configurations: {status.get('config_count', 0)}")
        logger.info("="*60)
        
        logger.info("\n✓ Database is ready for use!")
        
        # Show usage examples
        print("\nNext steps:")
        print("  1. Start the API server: python -m dcmx.api.server")
        print("  2. View database status: python scripts/init_database.py --status")
        print("  3. Verify database: python scripts/init_database.py --verify")
        
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
