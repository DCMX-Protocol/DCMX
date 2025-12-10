"""Database connection and session management for DCMX."""

import logging
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool, NullPool

from dcmx.database.config import config
from dcmx.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_config=None):
        """
        Initialize database manager.
        
        Args:
            database_config: Optional DatabaseConfig instance. Uses global config if None.
        """
        self.config = database_config or config
        
        # Synchronous engine
        self.sync_engine = None
        self.SyncSessionLocal = None
        
        # Asynchronous engine
        self.async_engine = None
        self.AsyncSessionLocal = None
        
        self._initialized = False
    
    def initialize_sync(self):
        """Initialize synchronous database engine and session maker."""
        if self.sync_engine is not None:
            logger.warning("Sync engine already initialized")
            return
        
        # Create engine with connection pooling
        if self.config.use_sqlite:
            # SQLite-specific configuration
            self.sync_engine = create_engine(
                self.config.get_sync_url(),
                poolclass=NullPool,
                echo=False,  # Set to True for SQL debugging
            )
        else:
            # PostgreSQL configuration
            self.sync_engine = create_engine(
                self.config.get_sync_url(),
                poolclass=QueuePool,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=False,  # Set to True for SQL debugging
            )
        
        # Create session maker
        self.SyncSessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.sync_engine
        )
        
        logger.info(f"Sync database engine initialized: {self.config.get_sync_url().split('@')[-1]}")
    
    async def initialize_async(self):
        """Initialize asynchronous database engine and session maker."""
        if self.async_engine is not None:
            logger.warning("Async engine already initialized")
            return
        
        # Create async engine
        if self.config.use_sqlite:
            # SQLite-specific configuration
            self.async_engine = create_async_engine(
                self.config.get_async_url(),
                poolclass=NullPool,
                echo=False,  # Set to True for SQL debugging
            )
        else:
            # PostgreSQL configuration
            self.async_engine = create_async_engine(
                self.config.get_async_url(),
                poolclass=QueuePool,
                pool_size=self.config.async_pool_size,
                max_overflow=self.config.async_max_overflow,
                echo=False,  # Set to True for SQL debugging
            )
        
        # Create async session maker
        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info(f"Async database engine initialized: {self.config.get_async_url().split('@')[-1]}")
    
    def create_tables(self):
        """Create all database tables (synchronous)."""
        if self.sync_engine is None:
            self.initialize_sync()
        
        Base.metadata.create_all(bind=self.sync_engine)
        logger.info("Database tables created")
    
    async def create_tables_async(self):
        """Create all database tables (asynchronous)."""
        if self.async_engine is None:
            await self.initialize_async()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created (async)")
    
    def drop_tables(self):
        """Drop all database tables (synchronous) - USE WITH CAUTION."""
        if self.sync_engine is None:
            self.initialize_sync()
        
        Base.metadata.drop_all(bind=self.sync_engine)
        logger.warning("All database tables dropped")
    
    async def drop_tables_async(self):
        """Drop all database tables (asynchronous) - USE WITH CAUTION."""
        if self.async_engine is None:
            await self.initialize_async()
        
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("All database tables dropped (async)")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a synchronous database session.
        
        Usage:
            with db_manager.get_session() as session:
                # Use session
                session.add(obj)
                session.commit()
        
        Yields:
            Session: SQLAlchemy session
        """
        if self.SyncSessionLocal is None:
            self.initialize_sync()
        
        session = self.SyncSessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an asynchronous database session.
        
        Usage:
            async with db_manager.get_async_session() as session:
                # Use session
                session.add(obj)
                await session.commit()
        
        Yields:
            AsyncSession: SQLAlchemy async session
        """
        if self.AsyncSessionLocal is None:
            await self.initialize_async()
        
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database async session error: {e}")
                raise
    
    def close(self):
        """Close database connections."""
        if self.sync_engine:
            self.sync_engine.dispose()
            logger.info("Sync database connections closed")
        
        if self.async_engine:
            # Async engine cleanup happens automatically
            logger.info("Async database connections marked for cleanup")
    
    async def close_async(self):
        """Close async database connections."""
        if self.async_engine:
            await self.async_engine.dispose()
            logger.info("Async database connections closed")


# Global database manager instance
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """Get or create global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_session() -> Generator[Session, None, None]:
    """
    Get a synchronous database session (convenience function).
    
    Usage:
        with get_session() as session:
            # Use session
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an asynchronous database session (convenience function).
    
    Usage:
        async with get_async_session() as session:
            # Use session
    """
    db_manager = get_db_manager()
    async with db_manager.get_async_session() as session:
        yield session


def init_database(drop_existing: bool = False):
    """
    Initialize database (create tables).
    
    Args:
        drop_existing: If True, drop all tables before creating (DANGER!)
    """
    db_manager = get_db_manager()
    
    if drop_existing:
        logger.warning("Dropping existing tables...")
        db_manager.drop_tables()
    
    db_manager.create_tables()
    logger.info("Database initialized successfully")


async def init_database_async(drop_existing: bool = False):
    """
    Initialize database (create tables) asynchronously.
    
    Args:
        drop_existing: If True, drop all tables before creating (DANGER!)
    """
    db_manager = get_db_manager()
    
    if drop_existing:
        logger.warning("Dropping existing tables...")
        await db_manager.drop_tables_async()
    
    await db_manager.create_tables_async()
    logger.info("Database initialized successfully (async)")
