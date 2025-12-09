# DCMX Testnet Deployment

This directory contains configurations and scripts for deploying DCMX to testnet environments.

## Architecture

### Multi-Node Testnet
- **3-5 DCMX nodes** running in Docker containers
- **Ethereum Sepolia testnet** for smart contracts (NFTs, tokens, governance)
- **LoRa mesh simulator** for peer-to-peer communication testing
- **Compliance monitor** for KYC/AML validation
- **Observability stack** (Prometheus, Grafana, Jaeger)

### Network Topology
```
┌─────────────────────────────────────────┐
│         Ethereum Sepolia                │
│  (Smart Contracts, NFT, Governance)     │
└─────────────────────────────────────────┘
           ↑                    ↑
           │                    │
    ┌──────────────────────────────────────┐
    │      DCMX Testnet Mesh Network      │
    │                                      │
    │  ┌──────────┐  ┌──────────┐        │
    │  │  Node 1  │  │  Node 2  │  ...  │
    │  │(Port 8001)  │(Port 8002)        │
    │  └──────────┘  └──────────┘        │
    │       ↑              ↑              │
    │       └──────────────┘              │
    │      P2P HTTP Links                │
    └──────────────────────────────────────┘
           ↑                    ↑
    ┌──────────────┐  ┌──────────────────┐
    │  Compliance  │  │  Observability   │
    │   Monitor    │  │  (Prometheus,    │
    │              │  │   Grafana,       │
    │ (KYC/OFAC)   │  │   Jaeger)        │
    └──────────────┘  └──────────────────┘
```

## Quick Start

### Prerequisites
- Docker & Docker Compose (v2+)
- Python 3.10+
- Ethereum testnet RPC URL (Sepolia)
- Private key with testnet ETH for gas fees

### Setup

1. **Copy environment template**
   ```bash
   cp .env.example .env
   ```

2. **Fill in environment variables**
   ```bash
   # .env
   ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
   PRIVATE_KEY=your_testnet_private_key
   DISCORD_WEBHOOK=optional_monitoring_webhook
   ```

3. **Deploy testnet**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   ./scripts/verify_testnet.sh
   ```

## Environments

### Local Testnet (Single Node)
For rapid development and testing on a single machine.

```bash
docker-compose -f docker-compose.local.yml up -d
```

**Endpoints:**
- Node: http://localhost:8001
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Jaeger: http://localhost:6831

### Staging Testnet (3-5 Nodes)
Multi-node setup for integration testing and performance validation.

```bash
docker-compose -f docker-compose.staging.yml up -d
```

**Network:**
- Nodes on separate containers
- Load balancer (nginx) on port 8000
- Shared compliance service
- Full observability stack

### Production Testnet (Kubernetes)
For long-term testnet operation with automatic scaling and recovery.

```bash
kubectl apply -f k8s/
```

See `k8s/README.md` for details.

## Configuration

### Node Configuration
Each node is configured via environment variables:

```bash
DCMX_HOST=0.0.0.0
DCMX_PORT=8001
DCMX_STORAGE_PATH=/var/lib/dcmx
DCMX_LOG_LEVEL=DEBUG
DCMX_PEERS=node2:8002,node3:8003  # Comma-separated peer list
```

### Smart Contracts
Deploy to Sepolia testnet:

```bash
cd blockchain/
npm install
npm run compile
npm run deploy:sepolia
```

Deployed contracts are stored in `blockchain/deployments/sepolia.json`.

### Compliance Configuration
KYC/OFAC checking is enabled by default in testnet:

```bash
COMPLIANCE_KYC_ENABLED=true
COMPLIANCE_OFAC_ENABLED=true
COMPLIANCE_OFAC_UPDATE_FREQ=7d  # Weekly updates
```

## Monitoring & Observability

### Prometheus Metrics
Access metrics dashboard:
```
http://localhost:9090
```

**Key metrics:**
- `dcmx_peer_count`: Number of connected peers
- `dcmx_content_bytes_stored`: Total content in storage
- `dcmx_track_hash_count`: Number of unique tracks
- `dcmx_transaction_latency_ms`: P2P transaction times
- `dcmx_nft_mints_total`: Total NFTs minted
- `dcmx_reward_distribution_total`: Tokens distributed

### Grafana Dashboards
Access visualizations:
```
http://localhost:3000
Default: admin / admin
```

Pre-loaded dashboards:
- **Network Health**: Peer connectivity, bandwidth, latency
- **Storage**: Content distribution, disk usage
- **NFT Activity**: Mint rate, holders, trading volume
- **Compliance**: KYC verifications, OFAC checks, flags
- **Token Economics**: Reward distribution, holders, transfers

### Jaeger Tracing
Distributed tracing for debugging:
```
http://localhost:6831
```

## Testing

### Run Testnet Validation Tests
```bash
./scripts/run_tests.sh
```

Tests include:
- Peer discovery and connectivity
- Content distribution and retrieval
- NFT minting and metadata
- KYC/AML compliance flows
- Reward calculation accuracy
- Network resilience and recovery

### Load Testing
Simulate network traffic:

```bash
./scripts/load_test.sh --nodes 5 --duration 10m --rps 100
```

## Logs

### View Real-Time Logs
```bash
# All nodes
docker-compose logs -f

# Specific node
docker-compose logs -f dcmx-node-1

# Specific service
docker-compose logs -f compliance-monitor
```

### Export Logs for Analysis
```bash
docker-compose logs > /tmp/dcmx-testnet.log
```

## Troubleshooting

### Node Won't Start
```bash
docker-compose logs dcmx-node-1
# Check: Port conflicts, insufficient disk space, invalid config
```

### Peers Not Discovering
```bash
# Test peer connectivity
curl http://localhost:8001/peers
# Should return list of discovered peers
```

### Smart Contract Issues
```bash
# Check Ethereum RPC connectivity
curl $ETHEREUM_RPC_URL
# Check contract deployment
cat blockchain/deployments/sepolia.json
```

### High CPU/Memory Usage
Check node logs for sync issues or infinite loops:
```bash
docker stats dcmx-node-1
docker-compose logs dcmx-node-1 | grep -i error
```

## Cleanup

### Stop All Services
```bash
docker-compose down
```

### Remove Persistent Data
```bash
docker-compose down -v
# Removes volumes (stored content, databases)
```

### Full Reset
```bash
./scripts/cleanup.sh --full
```

## CI/CD Integration

Automated deployments via GitHub Actions (see `.github/workflows/testnet-deploy.yml`):

1. **Push to `testnet-*` branch** → Deploy to staging
2. **Merge to `main`** → Deploy to production testnet
3. **Release tag** → Archive testnet state for auditing

## Compliance Checklist

Before deploying to production testnet:

- [ ] All 273 tests passing
- [ ] Smart contracts audited
- [ ] Watermark/fingerprint functionality verified
- [ ] KYC/OFAC checks operational
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures tested
- [ ] Security audit completed
- [ ] Documentation reviewed

## Support & Issues

For issues or questions:
1. Check `TROUBLESHOOTING.md` in this directory
2. Review logs in `logs/` directory
3. Check GitHub Issues: https://github.com/DCMX-Protocol/DCMX/issues
4. Contact team: support@dcmx.io
