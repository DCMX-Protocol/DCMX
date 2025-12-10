# Event Indexing Guide

## Overview

The DCMX event indexer continuously monitors blockchain events and indexes them to PostgreSQL for fast querying.

## Architecture

```
Blockchain → TronClient → EventParser → Indexer → PostgreSQL
```

## Event Types

### Token Events
- `Transfer`: Token transfers
- `Approval`: Spending approvals
- `Mint`: New tokens minted
- `Burn`: Tokens burned

### NFT Events
- `Minted`: NFT created
- `Transfer`: NFT ownership change
- `Approval`: NFT transfer approval

### Compliance Events
- `AcceptanceRecorded`: Document acceptance
- `DeletionRequested`: Data deletion request
- `DeletionProcessed`: Deletion completed

### Reward Events
- `ClaimSubmitted`: Reward claim submitted
- `ClaimVerified`: Claim verified/rejected
- `RewardsClaimed`: Rewards claimed

### Royalty Events
- `SaleRecorded`: NFT sale recorded
- `RoyaltiesDistributed`: Royalties distributed
- `RoyaltyPaid`: Payment to recipient

## Running the Indexer

### Start Indexer

```bash
python scripts/start_indexer.py --start-block 0
```

Options:
- `--start-block`: Block to start from (default: 0 or last indexed)
- `--batch-size`: Blocks per batch (default: 100)
- `--poll-interval`: Seconds between polls (default: 5)

### As System Service

Create `/etc/systemd/system/dcmx-indexer.service`:

```ini
[Unit]
Description=DCMX Blockchain Indexer
After=network.target postgresql.service

[Service]
Type=simple
User=dcmx
WorkingDirectory=/opt/dcmx
Environment="DATABASE_URL=postgresql://..."
ExecStart=/usr/bin/python3 scripts/start_indexer.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable dcmx-indexer
sudo systemctl start dcmx-indexer
sudo systemctl status dcmx-indexer
```

## Event Processing Flow

1. **Poll Blockchain**: Check for new blocks
2. **Fetch Block Data**: Get transactions and events
3. **Parse Events**: Convert to typed event objects
4. **Store in DB**: Save to indexed tables
5. **Update State**: Record last processed block

## Handling Chain Reorganizations

The indexer handles chain reorgs by:
1. Detecting block hash mismatches
2. Rolling back affected blocks
3. Re-indexing from stable block

## Performance Tuning

### Batch Size

```python
# Small batches: Lower latency, more DB writes
indexer = BlockchainIndexer(batch_size=10)

# Large batches: Higher throughput, more lag
indexer = BlockchainIndexer(batch_size=1000)
```

### Poll Interval

```python
# Fast polling: Lower lag, more RPC calls
indexer = BlockchainIndexer(poll_interval=1)

# Slow polling: Fewer RPC calls, higher lag
indexer = BlockchainIndexer(poll_interval=30)
```

### Database Optimization

Create indexes:
```sql
CREATE INDEX CONCURRENTLY idx_events_block 
ON blockchain_events(block_number);

CREATE INDEX CONCURRENTLY idx_events_contract 
ON blockchain_events(contract_address, event_type);
```

## Monitoring

### Check Indexer Status

```python
from dcmx.database.connection import get_database
from dcmx.database.models import BlockchainEvent

db = get_database()
with db.get_session() as session:
    last_block = session.query(
        BlockchainEvent.block_number
    ).order_by(
        BlockchainEvent.block_number.desc()
    ).first()
    
    print(f"Last indexed block: {last_block}")
```

### Indexing Lag

```python
from dcmx.tron.client import TronClient

client = TronClient()
latest = client.get_latest_block_number()
lag = latest - last_indexed_block

print(f"Indexing lag: {lag} blocks")
```

### Event Metrics

```sql
-- Events per hour
SELECT 
    date_trunc('hour', indexed_at) as hour,
    event_type,
    COUNT(*) as count
FROM blockchain_events
WHERE indexed_at > NOW() - INTERVAL '24 hours'
GROUP BY hour, event_type
ORDER BY hour DESC;
```

## Troubleshooting

### Indexer Stuck

Check logs:
```bash
journalctl -u dcmx-indexer -f
```

Restart:
```bash
sudo systemctl restart dcmx-indexer
```

### Missing Events

Re-index range:
```python
indexer = BlockchainIndexer(start_block=problem_block)
await indexer._index_block(problem_block)
```

### Database Connection Issues

Check connection pool:
```python
from dcmx.database.connection import get_database

db = get_database()
print(f"Pool size: {db.engine.pool.size()}")
print(f"Checked out: {db.engine.pool.checkedout()}")
```

### RPC Rate Limits

Use API key and increase poll interval:
```bash
export TRONGRID_API_KEY=your_key
python scripts/start_indexer.py --poll-interval 10
```

## Best Practices

1. **Start from checkpoint**: Don't re-index entire chain
2. **Monitor lag**: Alert if lag > 100 blocks
3. **Graceful shutdown**: Use signal handlers
4. **Log errors**: Track failed transactions
5. **Backup database**: Before re-indexing
6. **Use read replicas**: For heavy queries
7. **Partition tables**: For better performance
8. **Archive old data**: Keep hot data small

## Advanced Features

### Custom Event Handlers

```python
from dcmx.tron.indexer import BlockchainIndexer

class CustomIndexer(BlockchainIndexer):
    async def _index_specific_event(self, event):
        if event.event_type == 'CustomEvent':
            # Handle custom event
            pass
```

### Filtering Events

```python
# Only index specific contracts
indexer = BlockchainIndexer()
indexer.contract_filter = [
    config.music_nft_address,
    config.reward_vault_address
]
```

### Real-time Notifications

```python
import asyncio

async def on_event(event):
    if event.event_type == 'Minted':
        # Send notification
        await notify_user(event.data['to'])

indexer.on_event_callback = on_event
```

## Resources

- Web3 Architecture: docs/WEB3_ARCHITECTURE.md
- Database Models: dcmx/database/models.py
- Event Definitions: dcmx/tron/events.py
