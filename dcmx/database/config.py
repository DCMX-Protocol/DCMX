"""Database configuration for DCMX."""

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus


@dataclass
class DatabaseConfig:
    """Database configuration."""
    
    # Database connection parameters
    host: str = "localhost"
    port: int = 5432
    database: str = "dcmx"
    username: str = "dcmx_app"
    password: str = "dcmx_password"
    
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # SQLite fallback for development
    use_sqlite: bool = False
    sqlite_path: str = "dcmx.db"
    
    # Async settings
    async_pool_size: int = 5
    async_max_overflow: int = 10
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("DCMX_DB_HOST", "localhost"),
            port=int(os.getenv("DCMX_DB_PORT", "5432")),
            database=os.getenv("DCMX_DB_NAME", "dcmx"),
            username=os.getenv("DCMX_DB_USER", "dcmx_app"),
            password=os.getenv("DCMX_DB_PASSWORD", "dcmx_password"),
            pool_size=int(os.getenv("DCMX_DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DCMX_DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DCMX_DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DCMX_DB_POOL_RECYCLE", "3600")),
            use_sqlite=os.getenv("DCMX_DB_USE_SQLITE", "false").lower() == "true",
            sqlite_path=os.getenv("DCMX_DB_SQLITE_PATH", "dcmx.db"),
            async_pool_size=int(os.getenv("DCMX_DB_ASYNC_POOL_SIZE", "5")),
            async_max_overflow=int(os.getenv("DCMX_DB_ASYNC_MAX_OVERFLOW", "10")),
        )
    
    def get_sync_url(self) -> str:
        """Get synchronous database URL."""
        if self.use_sqlite:
            return f"sqlite:///{self.sqlite_path}"
        
        password = quote_plus(self.password)
        return f"postgresql://{self.username}:{password}@{self.host}:{self.port}/{self.database}"
    
    def get_async_url(self) -> str:
        """Get asynchronous database URL."""
        if self.use_sqlite:
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        
        password = quote_plus(self.password)
        return f"postgresql+asyncpg://{self.username}:{password}@{self.host}:{self.port}/{self.database}"


# Global configuration instance
config = DatabaseConfig.from_env()
