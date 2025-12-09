# DCMX Testnet Deployment Guide

## Quick Start (Docker Compose)

### 1. Clone & Setup
```bash
git clone https://github.com/DCMX-Protocol/DCMX.git
cd DCMX/testnet
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Ethereum RPC URL and private key
nano .env
```

### 3. Deploy Testnet
```bash
docker-compose up -d
```

### 4. Verify Deployment
```bash
./scripts/verify-testnet.sh
```

### 5. Access Services
- **DCMX Node 1**: http://localhost:8001
- **DCMX Node 2**: http://localhost:8002
- **DCMX Node 3**: http://localhost:8003
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Jaeger**: http://localhost:6831

## Kubernetes Deployment

### Prerequisites
- Kubernetes 1.20+
- kubectl configured
- Docker registry access (for custom images)

### 1. Build Images
```bash
docker build -f testnet/Dockerfile -t dcmx:testnet ..
docker build -f testnet/Dockerfile.compliance -t dcmx:testnet-compliance ..
```

### 2. Deploy to Kubernetes
```bash
cd testnet/k8s
bash ../deploy-k8s.sh
```

### 3. Verify Deployment
```bash
kubectl get pods -n dcmx-testnet
kubectl logs -n dcmx-testnet deployment/compliance-monitor -f
```

## Testing

### Run Integration Tests
```bash
cd testnet
./scripts/run-tests.sh
```

### Expected Results
- ✓ All 273 unit tests pass
- ✓ Peer discovery successful
- ✓ Content distribution working
- ✓ NFT minting operational
- ✓ Compliance checks active

## Troubleshooting

### Issue: Nodes can't discover each other

**Solution:**
```bash
# Check network connectivity
docker-compose logs dcmx-node-1 | grep "peer"

# Verify peers are set correctly in .env
# Reset services
docker-compose down -v
docker-compose up -d
```

### Issue: High memory usage

**Solution:**
```bash
# Check running containers
docker stats

# Reduce log level
# Edit .env: DCMX_LOG_LEVEL=WARNING
# Restart: docker-compose restart
```

### Issue: Ethereum connection failed

**Solution:**
```bash
# Verify RPC URL
curl $ETHEREUM_RPC_URL

# Check network connectivity
docker exec dcmx-node-1 curl $ETHEREUM_RPC_URL
```

## Configuration

### Environment Variables

**Core DCMX**
- `DCMX_HOST`: Bind address (default: 0.0.0.0)
- `DCMX_PORT`: Listen port (default: 8001)
- `DCMX_LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `DCMX_PEERS`: Comma-separated peer list

**Ethereum**
- `ETHEREUM_RPC_URL`: Sepolia testnet RPC endpoint
- `PRIVATE_KEY`: Private key for transactions

**Compliance**
- `COMPLIANCE_ENABLED`: Enable compliance checks
- `COMPLIANCE_KYC_ENABLED`: Require KYC verification
- `COMPLIANCE_OFAC_ENABLED`: Enable OFAC checking

**Database**
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

## Monitoring

### Key Metrics
```
dcmx_peer_count              # Number of connected peers
dcmx_content_bytes_stored    # Total content in storage
dcmx_track_hash_count        # Number of unique tracks
dcmx_transaction_latency_ms  # P2P latency
dcmx_nft_mints_total         # NFTs minted
dcmx_reward_distribution     # Tokens distributed
```

### Grafana Dashboards
- Network Health
- Storage Distribution
- NFT Activity
- Compliance Status
- Token Economics

## Maintenance

### Backup Data
```bash
# Backup node storage
docker-compose exec dcmx-node-1 tar czf /tmp/backup.tar.gz /var/lib/dcmx

# Backup database
docker-compose exec compliance-db pg_dump -U compliance dcmx_compliance > backup.sql
```

### Update Nodes
```bash
# Build new image
docker build -f testnet/Dockerfile -t dcmx:testnet ..

# Restart services
docker-compose up -d --no-deps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f dcmx-node-1

# Follow error logs
docker-compose logs -f | grep ERROR
```

## Performance Tuning

### For High Load
```bash
# Increase resource limits in docker-compose.yml
# Increase peer timeout and batch sizes in .env
DCMX_PEER_TIMEOUT=600
BATCH_SIZE=5000
```

### For Low Latency
```bash
# Reduce peer discovery interval
# Set log level to WARNING
DCMX_LOG_LEVEL=WARNING
```

## Cleanup

### Stop Services
```bash
docker-compose down
```

### Remove All Data
```bash
docker-compose down -v
```

### Full Reset
```bash
./scripts/cleanup.sh --full
```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify config: `cat .env`
3. Run tests: `./scripts/run-tests.sh`
4. Check GitHub Issues: https://github.com/DCMX-Protocol/DCMX/issues

## Next Steps

After successful testnet deployment:

1. **Deploy Smart Contracts**: See `../blockchain/README.md`
2. **Configure Monitoring**: See Grafana documentation
3. **Run Load Tests**: See `./scripts/run-tests.sh`
4. **Enable Audio Features**: See `../dcmx/audio/README.md`
5. **Production Hardening**: See `./PRODUCTION.md`
