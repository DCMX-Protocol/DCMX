#!/usr/bin/env python3
"""
Initialize DCMX PostgreSQL Database

Creates database tables and sets up initial schema.
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcmx.database.database import (
    DatabaseConfig,
    initialize_database,
    create_all_tables,
    test_connection,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main initialization function."""
    logger.info("=== DCMX Database Initialization ===")
    
    # Load config from environment
    config = DatabaseConfig.from_env()
    logger.info(f"Database: {config.database} @ {config.host}:{config.port}")
    
    # Test connection
    logger.info("Testing database connection...")
    if not test_connection(config):
        logger.error("Database connection failed!")
        sys.exit(1)
    
    logger.info("Connection successful!")
    
    # Create tables
    logger.info("Creating database tables...")
    try:
        create_all_tables(config)
        logger.info("Database tables created successfully!")
        
        # List created tables
        from dcmx.database.models import Base
        tables = Base.metadata.tables.keys()
        logger.info(f"\nCreated {len(tables)} tables:")
        for table_name in sorted(tables):
            logger.info(f"  - {table_name}")
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("\n=== Initialization Complete ===")
    logger.info("Database is ready for use!")


if __name__ == "__main__":
    main()
