"""Database migration and initialization utilities."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from dcmx.database.database import DatabaseManager, get_db_manager
from dcmx.database.models import Base, SystemConfiguration

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """Database migration manager."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize migration manager.
        
        Args:
            db_manager: Database manager instance. Uses global if None.
        """
        self.db_manager = db_manager or get_db_manager()
    
    def initialize_database(self, drop_existing: bool = False):
        """
        Initialize database schema.
        
        Args:
            drop_existing: If True, drop all existing tables first (DANGER!)
        """
        if drop_existing:
            logger.warning("Dropping all existing tables...")
            self.db_manager.drop_tables()
        
        logger.info("Creating database tables...")
        self.db_manager.create_tables()
        
        # Insert default configuration
        self._insert_default_config()
        
        logger.info("Database initialization complete")
    
    async def initialize_database_async(self, drop_existing: bool = False):
        """
        Initialize database schema asynchronously.
        
        Args:
            drop_existing: If True, drop all existing tables first (DANGER!)
        """
        if drop_existing:
            logger.warning("Dropping all existing tables...")
            await self.db_manager.drop_tables_async()
        
        logger.info("Creating database tables...")
        await self.db_manager.create_tables_async()
        
        # Insert default configuration
        await self._insert_default_config_async()
        
        logger.info("Database initialization complete (async)")
    
    def _insert_default_config(self):
        """Insert default system configuration."""
        with self.db_manager.get_session() as session:
            # Check if config already exists
            existing = session.query(SystemConfiguration).first()
            if existing:
                logger.info("System configuration already exists, skipping defaults")
                return
            
            # Default configurations
            configs = [
                SystemConfiguration(
                    config_key="platform_name",
                    config_value={"value": "DCMX"},
                    config_type="string",
                    description="Platform name",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="platform_version",
                    config_value={"value": "1.0.0"},
                    config_type="string",
                    description="Platform version",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="artist_primary_royalty_percentage",
                    config_value={"value": 100.0},
                    config_type="number",
                    description="Artist receives 100% on primary NFT sales",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="artist_secondary_royalty_percentage",
                    config_value={"value": 5.0},
                    config_type="number",
                    description="Artist receives 5% on secondary NFT sales",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="skip_charge_threshold",
                    config_value={"value": 0.25},
                    config_type="number",
                    description="Completion percentage threshold before skip charge applies",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="voting_reward_tokens",
                    config_value={"value": 5.0},
                    config_type="number",
                    description="Tokens awarded per vote",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="listening_base_reward",
                    config_value={"value": 1.0},
                    config_type="number",
                    description="Base tokens for listening",
                    is_public=True
                ),
            ]
            
            for config in configs:
                session.add(config)
            
            session.commit()
            logger.info(f"Inserted {len(configs)} default configurations")
    
    async def _insert_default_config_async(self):
        """Insert default system configuration asynchronously."""
        async with self.db_manager.get_async_session() as session:
            from sqlalchemy import select
            
            # Check if config already exists
            result = await session.execute(select(SystemConfiguration))
            existing = result.scalars().first()
            
            if existing:
                logger.info("System configuration already exists, skipping defaults")
                return
            
            # Default configurations
            configs = [
                SystemConfiguration(
                    config_key="platform_name",
                    config_value={"value": "DCMX"},
                    config_type="string",
                    description="Platform name",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="platform_version",
                    config_value={"value": "1.0.0"},
                    config_type="string",
                    description="Platform version",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="artist_primary_royalty_percentage",
                    config_value={"value": 100.0},
                    config_type="number",
                    description="Artist receives 100% on primary NFT sales",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="artist_secondary_royalty_percentage",
                    config_value={"value": 5.0},
                    config_type="number",
                    description="Artist receives 5% on secondary NFT sales",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="skip_charge_threshold",
                    config_value={"value": 0.25},
                    config_type="number",
                    description="Completion percentage threshold before skip charge applies",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="voting_reward_tokens",
                    config_value={"value": 5.0},
                    config_type="number",
                    description="Tokens awarded per vote",
                    is_public=True
                ),
                SystemConfiguration(
                    config_key="listening_base_reward",
                    config_value={"value": 1.0},
                    config_type="number",
                    description="Base tokens for listening",
                    is_public=True
                ),
            ]
            
            for config in configs:
                session.add(config)
            
            await session.commit()
            logger.info(f"Inserted {len(configs)} default configurations")
    
    def verify_database(self) -> bool:
        """
        Verify database is properly initialized.
        
        Returns:
            True if database is valid, False otherwise
        """
        try:
            with self.db_manager.get_session() as session:
                # Try to query each major table
                from sqlalchemy import inspect
                
                inspector = inspect(self.db_manager.sync_engine)
                tables = inspector.get_table_names()
                
                required_tables = [
                    'acceptance_records', 'audit_events', 'wallets', 'users',
                    'music_nfts', 'nft_sales', 'reward_claims', 'transactions',
                    'voting_records', 'system_configuration'
                ]
                
                missing = [t for t in required_tables if t not in tables]
                
                if missing:
                    logger.error(f"Missing tables: {missing}")
                    return False
                
                logger.info("Database verification passed")
                return True
                
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False
    
    async def verify_database_async(self) -> bool:
        """
        Verify database is properly initialized asynchronously.
        
        Returns:
            True if database is valid, False otherwise
        """
        try:
            async with self.db_manager.get_async_session() as session:
                # Try to execute a simple query
                from sqlalchemy import select
                
                result = await session.execute(
                    select(SystemConfiguration).limit(1)
                )
                result.scalars().first()
                
                logger.info("Database verification passed (async)")
                return True
                
        except Exception as e:
            logger.error(f"Database verification failed (async): {e}")
            return False
    
    def get_migration_status(self) -> dict:
        """
        Get database migration status.
        
        Returns:
            Dictionary with migration status information
        """
        try:
            with self.db_manager.get_session() as session:
                from sqlalchemy import inspect
                
                inspector = inspect(self.db_manager.sync_engine)
                tables = inspector.get_table_names()
                
                # Get config count
                config_count = session.query(SystemConfiguration).count()
                
                return {
                    'initialized': len(tables) > 0,
                    'table_count': len(tables),
                    'tables': sorted(tables),
                    'config_count': config_count,
                    'status': 'ready' if len(tables) > 0 else 'not_initialized'
                }
        except Exception as e:
            return {
                'initialized': False,
                'error': str(e),
                'status': 'error'
            }


def initialize_database(drop_existing: bool = False):
    """
    Initialize database (convenience function).
    
    Args:
        drop_existing: If True, drop all tables before creating (DANGER!)
    """
    migration = DatabaseMigration()
    migration.initialize_database(drop_existing=drop_existing)


async def initialize_database_async(drop_existing: bool = False):
    """
    Initialize database asynchronously (convenience function).
    
    Args:
        drop_existing: If True, drop all tables before creating (DANGER!)
    """
    migration = DatabaseMigration()
    await migration.initialize_database_async(drop_existing=drop_existing)


def verify_database() -> bool:
    """
    Verify database is properly initialized (convenience function).
    
    Returns:
        True if database is valid, False otherwise
    """
    migration = DatabaseMigration()
    return migration.verify_database()


async def verify_database_async() -> bool:
    """
    Verify database is properly initialized asynchronously (convenience function).
    
    Returns:
        True if database is valid, False otherwise
    """
    migration = DatabaseMigration()
    return await migration.verify_database_async()
