# DCMX Database Integration Guide

## Overview

This guide explains how to integrate the DCMX database system into your application code. The database system supports both PostgreSQL (production) and SQLite (development) with automatic fallback to in-memory storage.

## Quick Start

### 1. Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Dependencies added:
- `sqlalchemy>=2.0.0` - ORM framework
- `alembic>=1.12.0` - Database migrations
- `psycopg2-binary>=2.9.9` - PostgreSQL adapter
- `asyncpg>=0.29.0` - Async PostgreSQL adapter
- `aiosqlite>=0.19.0` - Async SQLite adapter

### 2. Configuration

Set environment variables:

```bash
# PostgreSQL (Production)
export DCMX_DB_HOST=localhost
export DCMX_DB_PORT=5432
export DCMX_DB_NAME=dcmx
export DCMX_DB_USER=dcmx_app
export DCMX_DB_PASSWORD=dcmx_password

# OR SQLite (Development)
export DCMX_DB_USE_SQLITE=true
export DCMX_DB_SQLITE_PATH=dcmx.db

# Enable database mode in API server
export DCMX_USE_DATABASE=true
```

### 3. Initialize Database

```bash
# Create all tables
python scripts/init_database.py

# Verify initialization
python scripts/init_database.py --verify
```

### 4. Start Using

```python
from dcmx.database.database import get_db_manager
from dcmx.database.dal import DataAccessLayer

# Get database manager
db_manager = get_db_manager()

# Use in async code
async with db_manager.get_async_session() as session:
    dal = DataAccessLayer()
    wallet = await dal.create_wallet(session, "0x1234...", "alice")
    print(f"Created wallet: {wallet.address}")
```

---

## Database Manager

The `DatabaseManager` class handles database connections and sessions.

### Getting Database Manager

```python
from dcmx.database.database import get_db_manager

# Get singleton instance
db_manager = get_db_manager()
```

### Synchronous Usage

```python
# Initialize sync engine
db_manager.initialize_sync()

# Get session context manager
with db_manager.get_session() as session:
    # Perform database operations
    from dcmx.database.models import Wallet
    
    wallet = Wallet(
        address="0x1234...",
        username="alice",
        balance_dcmx=100.0
    )
    session.add(wallet)
    session.commit()
```

### Asynchronous Usage

```python
# Initialize async engine
await db_manager.initialize_async()

# Get async session context manager
async with db_manager.get_async_session() as session:
    # Perform async database operations
    from dcmx.database.models import Wallet
    from sqlalchemy import select
    
    result = await session.execute(
        select(Wallet).where(Wallet.address == "0x1234...")
    )
    wallet = result.scalars().first()
```

---

## Data Access Layer (DAL)

The DAL provides high-level methods for common operations.

### Creating DAL Instance

```python
from dcmx.database.dal import DataAccessLayer

dal = DataAccessLayer()
```

### Wallet Operations

```python
async with get_async_session() as session:
    # Create wallet
    wallet = await dal.create_wallet(
        session,
        address="0x1234...",
        username="alice",
        is_artist=False
    )
    
    # Get wallet
    wallet = await dal.get_wallet(session, "0x1234...")
    
    # Update balance
    wallet = await dal.update_wallet_balance(
        session,
        address="0x1234...",
        amount=10.0,
        operation="add"  # or "subtract", "set"
    )
```

### NFT Operations

```python
async with get_async_session() as session:
    # Create NFT
    nft = await dal.create_nft(
        session,
        nft_id="nft_123",
        title="My Song",
        artist_wallet="0x1234...",
        price_dcmx=50.0,
        edition=1,
        max_editions=100,
        content_hash="abc123..."
    )
    
    # Get NFT
    nft = await dal.get_nft(session, "nft_123")
    
    # Get artist NFTs
    nfts = await dal.get_artist_nfts(session, "0x1234...")
    
    # Record purchase
    sale = await dal.record_nft_purchase(
        session,
        nft_id="nft_123",
        buyer_wallet="0x5678...",
        seller_wallet="0x1234...",
        price_dcmx=50.0,
        sale_type="primary"
    )
```

### Reward Operations

```python
async with get_async_session() as session:
    # Record listening reward
    reward = await dal.create_listening_reward(
        session,
        user_wallet="0x1234...",
        nft_id="nft_123",
        listen_duration_seconds=180,
        completion_percentage=0.95,
        total_reward=1.5
    )
    
    # Record vote
    vote = await dal.create_voting_record(
        session,
        user_wallet="0x1234...",
        nft_id="nft_123",
        preference="like",
        reward_tokens=5.0
    )
    
    # Record skip
    skip = await dal.create_skip_record(
        session,
        user_wallet="0x1234...",
        nft_id="nft_123",
        completion_percentage=0.15,
        charge_applied=-0.5
    )
```

### Transaction Operations

```python
async with get_async_session() as session:
    # Create transaction
    tx = await dal.create_transaction(
        session,
        from_wallet="0x1234...",
        to_wallet="0x5678...",
        amount_dcmx=10.0,
        transaction_type="transfer",
        blockchain_hash="0xabc..."
    )
    
    # Get user transactions
    txs = await dal.get_user_transactions(
        session,
        wallet_address="0x1234...",
        limit=100
    )
```

### Analytics Operations

```python
async with get_async_session() as session:
    # Get platform stats
    stats = await dal.get_platform_stats(session)
    print(f"Total Users: {stats['total_users']}")
    print(f"Total NFTs: {stats['total_nfts']}")
    
    # Get artist earnings
    earnings = await dal.get_artist_earnings(session, "0x1234...")
    print(f"Artist Balance: {earnings['current_balance_dcmx']}")
    
    # Get user profile stats
    profile = await dal.get_user_profile_stats(session, "0x1234...")
    print(f"Votes Cast: {profile['statistics']['votes_cast']}")
```

### Legal Compliance Operations

```python
async with get_async_session() as session:
    # Record acceptance
    record = await dal.record_acceptance(
        session,
        user_id="user123",
        wallet_address="0x1234...",
        document_type="terms_and_conditions",
        version="1.0",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0...",
        read_time_seconds=45
    )
    
    # Get acceptance
    record = await dal.get_acceptance(
        session,
        user_id="user123",
        document_type="terms_and_conditions",
        version="1.0"
    )
    
    # Log audit event
    event = await dal.log_audit_event(
        session,
        event_type="login",
        user_id="user123",
        wallet_address="0x1234...",
        status="success",
        ip_address="192.168.1.1"
    )
```

---

## Direct ORM Usage

For complex queries, use SQLAlchemy ORM directly:

```python
from sqlalchemy import select, and_, or_, func, desc
from dcmx.database.models import Wallet, MusicNFT, VotingRecord

async with get_async_session() as session:
    # Complex query
    result = await session.execute(
        select(MusicNFT)
        .where(
            and_(
                MusicNFT.artist_wallet == "0x1234...",
                MusicNFT.likes > 10
            )
        )
        .order_by(desc(MusicNFT.created_at))
        .limit(10)
    )
    nfts = result.scalars().all()
    
    # Aggregate query
    result = await session.execute(
        select(
            VotingRecord.nft_id,
            func.count(VotingRecord.id).label('vote_count'),
            func.sum(VotingRecord.reward_tokens).label('total_rewards')
        )
        .group_by(VotingRecord.nft_id)
        .having(func.count(VotingRecord.id) > 5)
    )
    
    for row in result:
        print(f"NFT: {row.nft_id}, Votes: {row.vote_count}, Rewards: {row.total_rewards}")
```

---

## FastAPI Integration

### Startup Event

```python
from fastapi import FastAPI
from dcmx.database.database import get_db_manager

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    db_manager = get_db_manager()
    await db_manager.initialize_async()
    print("Database initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    db_manager = get_db_manager()
    await db_manager.close_async()
    print("Database connections closed")
```

### Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from dcmx.database.database import get_async_session

async def get_session() -> AsyncSession:
    """Dependency for database session."""
    async with get_async_session() as session:
        yield session

@app.get("/wallets/{address}")
async def get_wallet(
    address: str,
    session: AsyncSession = Depends(get_session)
):
    """Get wallet with dependency injection."""
    from dcmx.database.dal import DataAccessLayer
    
    dal = DataAccessLayer()
    wallet = await dal.get_wallet(session, address)
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return {
        "address": wallet.address,
        "balance": float(wallet.balance_dcmx)
    }
```

### Dual-Mode Operation

Support both database and in-memory storage:

```python
import os
from dcmx.database.database import get_async_session
from dcmx.database.dal import DataAccessLayer

USE_DATABASE = os.getenv("DCMX_USE_DATABASE", "true").lower() == "true"
dal = DataAccessLayer() if USE_DATABASE else None

# In-memory fallback
wallets_memory = {}

@app.post("/wallet/create")
async def create_wallet(address: str, username: str):
    """Create wallet (database or in-memory)."""
    if USE_DATABASE:
        async with get_async_session() as session:
            wallet = await dal.create_wallet(session, address, username)
            return {"address": wallet.address, "username": wallet.username}
    else:
        # In-memory fallback
        wallets_memory[address] = {"address": address, "username": username}
        return wallets_memory[address]
```

---

## Legal Acceptance Tracker

Use the database-backed acceptance tracker:

```python
from dcmx.legal.acceptance_db import AcceptanceTracker, DocumentType

# Create tracker (automatically uses database if available)
tracker = AcceptanceTracker(use_database=True)

# Record acceptance
record = await tracker.record_acceptance(
    user_id="user123",
    wallet_address="0x1234...",
    document_type=DocumentType.TERMS_AND_CONDITIONS,
    version="1.0",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0...",
    read_time_seconds=45,
    document_content="<full document text>"
)

# Check if accepted
has_accepted = await tracker.has_accepted(
    user_id="user123",
    document_type=DocumentType.TERMS_AND_CONDITIONS,
    required_version="1.0",
    within_days=365
)

# Get user acceptances
acceptances = await tracker.get_user_acceptances("user123")

# Generate audit report
report = await tracker.audit_report()
print(f"Total Acceptances: {report['total_acceptances']}")
print(f"Unique Users: {report['unique_users']}")
```

---

## Migration from Legacy Systems

### JSONL to Database

```python
# Use migration script
# python scripts/migrate_legacy_data.py

# Or programmatically
from dcmx.database.database import get_db_manager
from dcmx.database.dal import DataAccessLayer
import json

async def migrate_jsonl():
    """Migrate JSONL acceptance records."""
    dal = DataAccessLayer()
    
    async with get_db_manager().get_async_session() as session:
        with open("acceptances.jsonl", "r") as f:
            for line in f:
                data = json.loads(line)
                
                await dal.record_acceptance(
                    session,
                    user_id=data["user_id"],
                    wallet_address=data["wallet_address"],
                    document_type=data["document_type"],
                    version=data["version"],
                    # ... other fields
                )
```

### In-Memory to Database

```python
# Migrate in-memory wallets to database
async def migrate_wallets(wallets_dict):
    """Migrate in-memory wallets."""
    dal = DataAccessLayer()
    
    async with get_db_manager().get_async_session() as session:
        for address, wallet_data in wallets_dict.items():
            await dal.create_wallet(
                session,
                address=address,
                username=wallet_data["username"],
                is_artist=wallet_data.get("is_artist", False)
            )
            
            # Update balance
            if wallet_data.get("balance_dcmx", 0) > 0:
                await dal.update_wallet_balance(
                    session,
                    address=address,
                    amount=wallet_data["balance_dcmx"],
                    operation="set"
                )
```

---

## Testing

### Unit Tests

```python
import pytest
from dcmx.database.database import DatabaseManager
from dcmx.database.config import DatabaseConfig
from dcmx.database.dal import DataAccessLayer

@pytest.fixture
async def db_session():
    """Test database session fixture."""
    # Use SQLite in-memory for tests
    config = DatabaseConfig(use_sqlite=True, sqlite_path=":memory:")
    db_manager = DatabaseManager(config)
    
    # Initialize database
    await db_manager.initialize_async()
    await db_manager.create_tables_async()
    
    # Yield session
    async with db_manager.get_async_session() as session:
        yield session
    
    # Cleanup
    await db_manager.drop_tables_async()

@pytest.mark.asyncio
async def test_create_wallet(db_session):
    """Test wallet creation."""
    dal = DataAccessLayer()
    
    wallet = await dal.create_wallet(
        db_session,
        address="0xtest",
        username="testuser"
    )
    
    assert wallet.address == "0xtest"
    assert wallet.username == "testuser"
    assert wallet.balance_dcmx == 0
```

---

## Performance Optimization

### Connection Pooling

Configure via environment variables:

```bash
export DCMX_DB_POOL_SIZE=20
export DCMX_DB_MAX_OVERFLOW=40
export DCMX_DB_POOL_TIMEOUT=30
export DCMX_DB_POOL_RECYCLE=3600
```

### Batch Operations

```python
async with get_async_session() as session:
    # Batch insert
    wallets = [
        Wallet(address=f"0x{i}", username=f"user{i}")
        for i in range(100)
    ]
    
    session.add_all(wallets)
    await session.commit()
```

### Eager Loading

```python
from sqlalchemy.orm import selectinload

async with get_async_session() as session:
    # Eager load relationships
    result = await session.execute(
        select(MusicNFT)
        .options(selectinload(MusicNFT.sales))
        .where(MusicNFT.artist_wallet == "0x1234...")
    )
    nfts = result.scalars().all()
```

---

## Error Handling

```python
from sqlalchemy.exc import IntegrityError, OperationalError

async with get_async_session() as session:
    try:
        wallet = await dal.create_wallet(session, "0x1234...", "alice")
    except IntegrityError:
        # Duplicate wallet
        print("Wallet already exists")
    except OperationalError:
        # Database connection error
        print("Database unavailable")
    except Exception as e:
        # Other errors
        print(f"Error: {e}")
```

---

## Troubleshooting

### Database Connection Issues

```python
# Test connection
from dcmx.database.database import get_db_manager

db_manager = get_db_manager()
try:
    db_manager.initialize_sync()
    print("✓ Database connected")
except Exception as e:
    print(f"✗ Connection failed: {e}")
```

### Check Migration Status

```bash
python scripts/init_database.py --status
```

### Enable SQL Logging

```python
from dcmx.database.database import DatabaseManager

db_manager = DatabaseManager()
db_manager.sync_engine = create_engine(
    db_manager.config.get_sync_url(),
    echo=True  # Enable SQL logging
)
```

### Verify Tables

```python
from sqlalchemy import inspect

inspector = inspect(db_manager.sync_engine)
tables = inspector.get_table_names()
print(f"Tables: {tables}")
```

---

## Best Practices

1. **Always use context managers** for session management
2. **Use DAL methods** for common operations
3. **Enable connection pooling** in production
4. **Use SQLite** for development and testing
5. **Commit explicitly** when using sync sessions
6. **Handle IntegrityError** for duplicate records
7. **Use indexes** for frequently queried columns
8. **Batch operations** for bulk inserts
9. **Close connections** properly on shutdown
10. **Test with in-memory SQLite** for unit tests

---

## Additional Resources

- [Database Schema Documentation](DATABASE_SCHEMA.md)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Database Integration](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## Support

For integration issues:
1. Check environment variables
2. Verify database connection
3. Run `python scripts/init_database.py --verify`
4. Enable verbose logging: `--verbose`
5. Check database logs
