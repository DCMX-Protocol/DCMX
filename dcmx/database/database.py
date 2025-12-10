"""
Database Connection Management

Handles PostgreSQL connections and session management.
"""

import os
import logging
from typing import Optional, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from .models import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "dcmx",
        user: str = "dcmx",
        password: str = "",
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False,
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "dcmx"),
            user=os.getenv("DB_USER", "dcmx"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    
    def get_url(self) -> str:
        """Get database URL."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseConnection:
    """
    Database connection manager.
    
    Manages SQLAlchemy engine and session factory.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Initialize database connection.
        
        Args:
            config: Database configuration (or load from env)
        """
        if config is None:
            config = DatabaseConfig.from_env()
        
        self.config = config
        self.engine = None
        self.session_factory = None
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine."""
        db_url = self.config.get_url()
        
        # Create engine with connection pooling
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=True,  # Verify connections before using
            echo=self.config.echo,
        )
        
        # Set up event listeners
        self._setup_event_listeners()
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )
        
        logger.info(f"Database connection initialized: {self.config.database}")
    
    def _setup_event_listeners(self):
        """Set up SQLAlchemy event listeners."""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Set up connection when created."""
            # Set timezone to UTC
            cursor = dbapi_conn.cursor()
            cursor.execute("SET timezone='UTC'")
            cursor.close()
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Verify connection is alive on checkout."""
            # Connection pre-ping handles this
            pass
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        Base.metadata.drop_all(self.engine)
        logger.warning("Database tables dropped")
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        Usage:
            with db.session_scope() as session:
                session.add(obj)
                # session.commit() is called automatically
        
        Yields:
            Database session
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection.
        
        Returns:
            True if connection successful
        """
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close database connection and dispose engine."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")


# Global database connection
_db_connection: Optional[DatabaseConnection] = None


def initialize_database(config: Optional[DatabaseConfig] = None) -> DatabaseConnection:
    """
    Initialize global database connection.
    
    Args:
        config: Database configuration
        
    Returns:
        Database connection
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection(config)
    
    return _db_connection


def get_database() -> DatabaseConnection:
    """
    Get global database connection.
    
    Returns:
        Database connection
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = initialize_database()
    
    return _db_connection


def get_session() -> Session:
    """
    Get a new database session from global connection.
    
    Returns:
        SQLAlchemy session
    """
    db = get_database()
    return db.get_session()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Provide a transactional scope using global connection.
    
    Yields:
        Database session
    """
    db = get_database()
    with db.session_scope() as session:
        yield session


def create_all_tables(config: Optional[DatabaseConfig] = None):
    """
    Create all database tables.
    
    Args:
        config: Database configuration
    """
    db = initialize_database(config)
    db.create_tables()


def test_connection(config: Optional[DatabaseConfig] = None) -> bool:
    """
    Test database connection.
    
    Args:
        config: Database configuration
        
    Returns:
        True if successful
    """
    db = initialize_database(config)
    return db.test_connection()
