# DCMX Blockchain Integration Guide

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- TRON wallet with TRX for gas fees

### Environment Setup

```bash
# Clone repository
git clone https://github.com/DCMX-Protocol/DCMX.git
cd DCMX

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration
```

### Environment Variables

```bash
# TRON Configuration
TRON_NETWORK=shasta              # or mainnet
TRON_PRIVATE_KEY=your_hex_key    # Without 0x prefix
TRONGRID_API_KEY=your_api_key    # Optional, for higher rate limits

# Contract Addresses (set after deployment)
DCMX_TOKEN_ADDRESS=
MUSIC_NFT_ADDRESS=
COMPLIANCE_REGISTRY_ADDRESS=
REWARD_VAULT_ADDRESS=
ROYALTY_DISTRIBUTOR_ADDRESS=

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dcmx
DB_USER=dcmx
DB_PASSWORD=your_secure_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## Deployment Steps

### 1. Deploy Smart Contracts

```bash
# Deploy to Shasta testnet
python scripts/deploy_contracts.py

# Output will include contract addresses
# Update .env with these addresses
```

### 2. Initialize Database

```bash
# Create database tables
python scripts/initialize_db.py

# Verify tables created
psql -h localhost -U dcmx -d dcmx -c "\dt"
```

### 3. Start Event Indexer

```bash
# Start indexer daemon
python scripts/start_indexer.py --poll-interval 30

# Or run as systemd service (production)
sudo systemctl start dcmx-indexer
```

### 4. Verify Integration

```python
from dcmx.tron import TronClient, DCMXTokenContract
from dcmx.database import get_database

# Test blockchain connection
client = TronClient()
assert client.is_connected()

# Test database connection
db = get_database()
assert db.test_connection()

# Test contract interaction
token = DCMXTokenContract(client, token_address)
supply = token.total_supply()
print(f"Total supply: {supply / 10**18} DCMX")
```

## Integration Patterns

### Pattern 1: Mint NFT with Indexing

```python
from dcmx.tron.contracts import MusicNFTContract
from dcmx.database.sync import BlockchainSync

# 1. Mint NFT on blockchain
nft = MusicNFTContract(client, nft_address)
tx_hash = nft.mint_music(
    to_address=artist_wallet,
    title="My Song",
    artist="Artist Name",
    content_hash=audio_hash,
    edition_number=1,
    max_editions=100,
    royalty_bps=1000
)

# 2. Wait for confirmation
client.wait_for_transaction(tx_hash)

# 3. Sync to database
sync = BlockchainSync(client)
sync.sync_events(nft_address)

# 4. Query from database
from dcmx.database.queries import DatabaseQueries
nfts = DatabaseQueries.get_nfts_by_artist(artist_wallet)
```

### Pattern 2: Record Legal Acceptance

```python
from dcmx.tron.contracts import ComplianceRegistryContract
import hashlib

# 1. Calculate document hash
document_content = "Terms and Conditions v1.0..."
doc_hash = "0x" + hashlib.sha256(document_content.encode()).hexdigest()

# 2. Record on blockchain
compliance = ComplianceRegistryContract(client, compliance_address)
tx_hash = compliance.record_acceptance(
    doc_type=0,  # TERMS_AND_CONDITIONS
    version="1.0",
    document_hash=doc_hash,
    ip_address=user_ip
)

# 3. Wait for confirmation
client.wait_for_transaction(tx_hash)

# 4. Query acceptance status
has_accepted = compliance.has_accepted(
    wallet=user_wallet,
    doc_type=0,
    required_version="1.0"
)
```

### Pattern 3: Process Reward Claim

```python
from dcmx.tron.contracts import RewardVaultContract

# 1. User submits claim
vault = RewardVaultContract(client, vault_address)
tx_hash = vault.submit_claim(
    reward_type=1,  # LISTENING
    amount=10 * 10**18,  # 10 DCMX
    proof_hash="0xabcd..."  # Hash of activity proof
)

claim_id = get_claim_id_from_tx(tx_hash)

# 2. Verifier approves claim
tx_hash = vault.verify_claim(claim_id, approved=True)

# 3. Tokens automatically minted to user
# 4. Check claim status
claim = vault.get_claim(claim_id)
assert claim['claimed'] == True
```

## API Integration

### FastAPI Endpoints

```python
from fastapi import FastAPI
from dcmx.tron import TronClient, MusicNFTContract
from dcmx.database.queries import DatabaseQueries

app = FastAPI()

@app.post("/api/v1/nft/mint")
async def mint_nft(
    title: str,
    artist: str,
    content_hash: str,
    edition: int,
    max_editions: int
):
    # Mint on blockchain
    nft = MusicNFTContract(client, nft_address)
    tx_hash = nft.mint_music(...)
    
    # Wait for confirmation
    client.wait_for_transaction(tx_hash)
    
    # Sync to database
    sync.sync_events(nft_address)
    
    return {"tx_hash": tx_hash, "status": "minted"}

@app.get("/api/v1/nft/{token_id}")
async def get_nft(token_id: int):
    # Query from database (fast)
    nft = DatabaseQueries.get_nft_by_token_id(token_id, nft_address)
    
    if not nft:
        raise HTTPException(404, "NFT not found")
    
    return {
        "token_id": nft.token_id,
        "title": nft.title,
        "artist": nft.artist,
        "owner": nft.owner_wallet,
        "edition": f"{nft.edition_number}/{nft.max_editions}"
    }
```

## Testing

### Unit Tests

```python
import pytest
from dcmx.tron import TronClient
from dcmx.tron.contracts import DCMXTokenContract

@pytest.fixture
def client():
    return TronClient()

@pytest.fixture
def token(client):
    return DCMXTokenContract(client, token_address)

def test_token_balance(token):
    balance = token.balance_of(test_wallet)
    assert balance >= 0

def test_token_transfer(token, client):
    initial_balance = token.balance_of(recipient)
    
    tx_hash = token.transfer(recipient, 100 * 10**18)
    client.wait_for_transaction(tx_hash)
    
    final_balance = token.balance_of(recipient)
    assert final_balance == initial_balance + 100 * 10**18
```

### Integration Tests

```python
def test_nft_mint_and_query():
    # 1. Mint NFT
    nft = MusicNFTContract(client, nft_address)
    tx_hash = nft.mint_music(...)
    client.wait_for_transaction(tx_hash)
    
    # 2. Sync to database
    sync = BlockchainSync(client)
    sync.sync_events(nft_address)
    
    # 3. Query from database
    nfts = DatabaseQueries.get_nfts_by_artist(artist_wallet)
    assert len(nfts) > 0
    assert nfts[0].title == "My Song"
```

## Monitoring

### Health Checks

```python
from dcmx.tron import TronClient
from dcmx.database import test_connection

def health_check():
    checks = {
        "blockchain": False,
        "database": False,
        "indexer_lag": 0
    }
    
    # Check blockchain
    try:
        client = TronClient()
        checks["blockchain"] = client.is_connected()
    except:
        pass
    
    # Check database
    checks["database"] = test_connection()
    
    # Check indexer lag
    if checks["blockchain"] and checks["database"]:
        latest_block = client.get_latest_block_number()
        last_indexed = get_last_indexed_block()
        checks["indexer_lag"] = latest_block - last_indexed
    
    return checks
```

### Metrics

```python
from prometheus_client import Counter, Gauge

# Define metrics
events_indexed = Counter('dcmx_events_indexed_total', 'Total events indexed')
indexer_lag = Gauge('dcmx_indexer_lag_blocks', 'Indexer lag in blocks')
contract_calls = Counter('dcmx_contract_calls_total', 'Contract calls', ['contract'])

# Update metrics
events_indexed.inc(count)
indexer_lag.set(lag)
contract_calls.labels(contract='DCMXToken').inc()
```

## Troubleshooting

### Issue: Indexer Not Syncing

**Symptoms**: No new events in database despite blockchain activity

**Solutions**:
1. Check indexer logs: `tail -f /var/log/dcmx-indexer.log`
2. Verify TRON connection: `client.is_connected()`
3. Check contract addresses in .env
4. Restart indexer: `systemctl restart dcmx-indexer`

### Issue: Transaction Failed

**Symptoms**: Transaction reverted or insufficient energy

**Solutions**:
1. Check TRX balance: `client.get_balance()`
2. Check energy/bandwidth: `client.get_account_resource()`
3. Increase fee limit in transaction
4. Wait for network congestion to clear

### Issue: Database Connection Failed

**Symptoms**: Cannot connect to PostgreSQL

**Solutions**:
1. Verify PostgreSQL is running: `systemctl status postgresql`
2. Check credentials in .env
3. Test connection: `psql -h $DB_HOST -U $DB_USER -d $DB_NAME`
4. Check firewall rules

## Production Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: dcmx
      POSTGRES_USER: dcmx
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  indexer:
    build: .
    command: python scripts/start_indexer.py
    environment:
      TRON_NETWORK: ${TRON_NETWORK}
      TRON_PRIVATE_KEY: ${TRON_PRIVATE_KEY}
      DB_HOST: postgres
    depends_on:
      - postgres
    restart: unless-stopped
  
  api:
    build: .
    command: uvicorn dcmx.api.server:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      TRON_NETWORK: ${TRON_NETWORK}
      DB_HOST: postgres
    depends_on:
      - postgres
      - indexer
    restart: unless-stopped

volumes:
  postgres_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmx-indexer
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: indexer
        image: dcmx/indexer:latest
        env:
        - name: TRON_NETWORK
          value: mainnet
        - name: DB_HOST
          value: postgres-service
        - name: TRON_PRIVATE_KEY
          valueFrom:
            secretKeyRef:
              name: tron-credentials
              key: private-key
```

## Best Practices

1. **Environment Separation**: Use separate networks for dev/staging/prod
2. **Key Management**: Store private keys in secure vaults (AWS Secrets Manager, HashiCorp Vault)
3. **Monitoring**: Set up alerts for indexer lag, failed transactions, low balances
4. **Backups**: Regular database backups with point-in-time recovery
5. **Rate Limiting**: Use API keys and implement rate limiting
6. **Error Handling**: Implement retry logic with exponential backoff
7. **Logging**: Structured logging with correlation IDs
8. **Testing**: Comprehensive test coverage before mainnet deployment
