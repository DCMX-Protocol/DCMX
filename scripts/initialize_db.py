#!/usr/bin/env python3
"""Initialize PostgreSQL database for DCMX."""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcmx.database.connection import DatabaseConnection
from dcmx.database.models import Base, create_additional_indexes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_database(database_url: str = None, drop_existing: bool = False):
    """
    Initialize database schema.
    
    Args:
        database_url: PostgreSQL connection string
        drop_existing: If True, drop existing tables first
    """
    logger.info("Initializing DCMX database...")
    
    try:
        # Create database connection
        db = DatabaseConnection(database_url)
        
        # Test connection
        if not db.test_connection():
            logger.error("Database connection failed")
            return False
        
        # Drop existing tables if requested
        if drop_existing:
            logger.warning("Dropping existing tables...")
            db.drop_tables()
        
        # Create all tables
        logger.info("Creating database tables...")
        db.create_tables()
        
        # Create additional indexes
        logger.info("Creating performance indexes...")
        create_additional_indexes(db.engine)
        
        logger.info("Database initialization complete!")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False
    finally:
        db.close()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize DCMX database')
    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection string (default: from DATABASE_URL env var)'
    )
    parser.add_argument(
        '--drop-existing',
        action='store_true',
        help='Drop existing tables before creating new ones (DANGEROUS!)'
    )
    
    args = parser.parse_args()
    
    # Confirm if dropping existing tables
    if args.drop_existing:
        response = input(
            "WARNING: This will delete all existing data. "
            "Are you sure? (type 'yes' to confirm): "
        )
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            return
    
    success = initialize_database(
        database_url=args.database_url,
        drop_existing=args.drop_existing
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
