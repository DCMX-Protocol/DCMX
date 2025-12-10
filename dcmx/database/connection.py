"""Database connection management for DCMX."""

import logging
import os
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages PostgreSQL database connections."""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False
    ):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection string
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            echo: Echo SQL queries (for debugging)
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost/dcmx_main'
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=echo,
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database connection initialized: {self._safe_url()}")
    
    def _safe_url(self) -> str:
        """Get database URL with password masked."""
        url = self.database_url
        if '@' in url:
            # Mask password
            parts = url.split('@')
            creds = parts[0].split('//')[-1]
            if ':' in creds:
                user = creds.split(':')[0]
                url = url.replace(creds, f"{user}:***")
        return url
    
    def create_tables(self):
        """Create all tables in database."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Get a database session context manager.
        
        Usage:
            with db.get_session() as session:
                # Use session
                session.query(Model).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get a database session (must be closed manually)."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("Database connection closed")
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False


# Global database instance
_db_instance: Optional[DatabaseConnection] = None


def get_database(
    database_url: Optional[str] = None,
    reset: bool = False
) -> DatabaseConnection:
    """
    Get or create global database instance.
    
    Args:
        database_url: Optional database URL
        reset: Force create new instance
        
    Returns:
        DatabaseConnection instance
    """
    global _db_instance
    
    if _db_instance is None or reset:
        _db_instance = DatabaseConnection(database_url)
    
    return _db_instance


def close_database():
    """Close global database connection."""
    global _db_instance
    
    if _db_instance:
        _db_instance.close()
        _db_instance = None
