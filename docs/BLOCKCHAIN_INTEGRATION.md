# Blockchain Integration Guide

## Quick Start

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
vim .env
```

Required variables:
```bash
TRON_NETWORK=shasta
TRON_PRIVATE_KEY=your_64_char_hex_key
DATABASE_URL=postgresql://user:pass@localhost/dcmx_main
```

### 2. Initialize Database

```bash
python scripts/initialize_db.py
```

### 3. Deploy Contracts (Testnet)

```bash
python scripts/deploy_contracts.py --network shasta
```

### 4. Start Event Indexer

```bash
python scripts/start_indexer.py
```

### 5. Run API Server

```bash
# Add web3 router to your FastAPI app
from dcmx.api.web3_endpoints import web3_router
app.include_router(web3_router)

# Run server
uvicorn dcmx.api.server:app --reload
```

## API Usage Examples

### Mint NFT

```bash
curl -X POST http://localhost:8000/api/v1/nft/mint \
  -H "Content-Type: application/json" \
  -d '{
    "to_address": "TRON_ADDRESS_HERE",
    "title": "My Song",
    "artist": "Artist Name",
    "content_hash": "QmHash...",
    "edition": 1,
    "max_editions": 100,
    "royalty_bps": 1000
  }'
```

### Submit Reward Claim

```bash
curl -X POST http://localhost:8000/api/v1/reward/claim \
  -H "Content-Type: application/json" \
  -d '{
    "claim_type": "BANDWIDTH",
    "proof_data": {"bytes_served": 1000000, "uptime": 86400},
    "amount": 100000000000000000000
  }'
```

### Check Blockchain Status

```bash
curl http://localhost:8000/api/v1/blockchain/status
```

## Python Integration

### Basic Usage

```python
from dcmx.tron.contracts import ContractManager
from dcmx.tron.config import TronConfig

# Initialize
config = TronConfig.from_env()
manager = ContractManager(config)

# Mint NFT
result = manager.nft.mint(
    to_address="T...",
    title="Song Title",
    artist="Artist",
    content_hash="hash",
    edition=1,
    max_editions=100,
    royalty_bps=1000
)

print(f"TX: {result.transaction_hash}")
```

### Event Listening

```python
from dcmx.tron.indexer import BlockchainIndexer

indexer = BlockchainIndexer(start_block=0)
await indexer.start()
```

### Database Queries

```python
from dcmx.database.connection import get_database
from dcmx.database.models import NFTIndex

db = get_database()

with db.get_session() as session:
    nfts = session.query(NFTIndex).filter(
        NFTIndex.artist == "Artist Name"
    ).all()
```

## Legal Compliance Integration

### Record Acceptance

```python
from dcmx.tron.contracts import ContractManager
from dcmx.tron import utils

manager = ContractManager()

# Compute document hash
doc_hash = utils.compute_document_hash(document_content)

# Record on blockchain
result = manager.compliance.record_acceptance(
    user_address="T...",
    document_hash=doc_hash,
    document_type=0,  # TERMS
    version="1.0",
    ip_address=utils.compute_document_hash("ip_address")
)
```

### Verify Acceptance

```python
verified = manager.compliance.verify_acceptance(
    user_address="T...",
    document_type=0,
    document_hash=doc_hash
)
```

## Troubleshooting

### Contract Not Found

Check contract addresses in .env:
```bash
echo $MUSIC_NFT_ADDRESS
```

### Indexer Not Syncing

Check logs:
```bash
tail -f /var/log/dcmx/indexer.log
```

Restart indexer:
```bash
python scripts/start_indexer.py
```

### Database Connection Failed

Test connection:
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Transaction Failed

Check TRX balance:
```python
balance = manager.client.get_balance()
print(f"Balance: {balance / 1_000_000} TRX")
```

## Production Deployment

1. Use managed PostgreSQL (AWS RDS, etc.)
2. Deploy indexer as systemd service
3. Use process manager (PM2, supervisord)
4. Setup monitoring (Prometheus, Grafana)
5. Configure log rotation
6. Enable SSL/TLS for API
7. Setup backup strategy
8. Use hardware wallet for private keys

## Resources

- Web3 Architecture: docs/WEB3_ARCHITECTURE.md
- Smart Contracts: docs/SMART_CONTRACTS.md
- Event Indexing: docs/EVENT_INDEXING.md
