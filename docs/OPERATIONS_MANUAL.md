# DCMX Deployment and Operations Manual

Complete guide for deploying and operating DCMX nodes in production environments.

---

## Table of Contents

1. [Pre-Deployment Planning](#pre-deployment-planning)
2. [System Requirements](#system-requirements)
3. [Installation & Configuration](#installation--configuration)
4. [Monitoring & Health Checks](#monitoring--health-checks)
5. [Performance Optimization](#performance-optimization)
6. [Security Hardening](#security-hardening)
7. [Disaster Recovery](#disaster-recovery)
8. [Troubleshooting](#troubleshooting)
9. [Upgrade Procedures](#upgrade-procedures)

---

## Pre-Deployment Planning

### Capacity Planning

Estimate your infrastructure needs:

```python
# Example calculation for 50,000 daily users

users = 50_000
avg_tracks_per_user = 50
avg_track_size_mb = 5
avg_replication_factor = 2  # Each track on 2 nodes

total_storage_tb = (users * avg_tracks_per_user * avg_track_size_mb * avg_replication_factor) / (1024 * 1024)
# = ~5 TB total

# Per node (assuming 5 nodes)
per_node_storage = total_storage_tb / 5
# = 1 TB per node

# Bandwidth (peak hours)
concurrent_users = users * 0.1  # 10% concurrent
avg_bitrate_mbps = 2  # High quality
required_bandwidth_gbps = (concurrent_users * avg_bitrate_mbps) / 1000
# = ~10 Gbps (scale horizontally)
```

### Architecture Decision Tree

```
How many daily users?
├─ <100 (personal)
│  └─ 1x PC/laptop with Python
│
├─ 100-10,000 (small community)
│  └─ 3-5 nodes on VPS ($50/month each)
│     - 2 GB RAM, 100 GB SSD
│     - 10 Mbps upload minimum
│
├─ 10,000-100,000 (growing)
│  └─ 10-20 nodes on managed hosting
│     - 4-8 GB RAM, 500 GB SSD
│     - Geographic distribution
│
└─ 100,000+ (enterprise)
   └─ 50-100+ nodes on cloud infrastructure
      - Auto-scaling groups
      - Load balancers
      - Geographic redundancy
```

### Geographic Distribution

For resilience, spread nodes globally:

```
North America (1-2 nodes)
  ├─ East Coast (AWS us-east-1)
  └─ West Coast (AWS us-west-2)

Europe (1-2 nodes)
  ├─ EU-Central (Azure eu-central)
  └─ EU-West (AWS eu-west-1)

Asia-Pacific (1-2 nodes)
  ├─ Singapore (AWS ap-southeast-1)
  └─ Tokyo (AWS ap-northeast-1)
```

Benefits:
- **Lower latency**: Users download from nearby node
- **Resilience**: Regional outage doesn't block everything
- **Bandwidth**: Distribute load across regions

---

## System Requirements

### Hardware Requirements

| Workload | CPU | RAM | Storage | Bandwidth |
|----------|-----|-----|---------|-----------|
| **Light** (1-10 tracks) | 1 core | 512 MB | 10 GB | 1 Mbps |
| **Medium** (100-1000 tracks) | 2 cores | 2 GB | 100 GB | 10 Mbps |
| **Heavy** (10,000+ tracks) | 4 cores | 8 GB | 1 TB | 100 Mbps |
| **Enterprise** (50,000+ tracks) | 8+ cores | 16+ GB | 10 TB+ | 1 Gbps+ |

### Software Requirements

```bash
# Operating System
Ubuntu 20.04 LTS (recommended)
CentOS 8+
Debian 10+
macOS 10.15+

# Python
Python 3.8 or higher
pip package manager

# System Dependencies
apt-get install -y python3-dev libffi-dev libssl-dev

# Optional (for advanced features)
docker / podman (containerization)
nginx (reverse proxy)
prometheus (monitoring)
postgresql (audit logging)
```

### Network Requirements

```
Ports needed:
  - 8080 (DCMX protocol)
  - 443 (HTTPS, optional)
  - 22 (SSH management)
  - 9090 (Prometheus metrics, internal)
  
Firewall rules:
  ✓ Inbound: 8080 (all)
  ✓ Inbound: 443 (all)
  ✓ Inbound: 22 (admin only)
  ✓ Inbound: 9090 (monitoring only)
  ✓ Outbound: All (for peer discovery)
  
DNS:
  - Dynamic DNS (if IP changes)
  - Or static IP (recommended for production)
```

---

## Installation & Configuration

### Docker Installation (Recommended)

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY dcmx/ ./dcmx/
COPY setup.py .

# Install DCMX
RUN pip install -e .

# Create data directory
RUN mkdir -p /data/dcmx

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/ping || exit 1

# Run node
CMD ["dcmx", "start", "--host", "0.0.0.0", "--port", "8080", "--data-dir", "/data/dcmx"]
```

```bash
# Build image
docker build -t dcmx:latest .

# Run container
docker run -d \
  --name dcmx-node \
  -p 8080:8080 \
  -v /data/dcmx:/data/dcmx \
  --restart unless-stopped \
  dcmx:latest

# Check logs
docker logs -f dcmx-node

# Stop container
docker stop dcmx-node

# Remove container
docker rm dcmx-node
```

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  dcmx-node:
    build: .
    container_name: dcmx-node
    ports:
      - "8080:8080"
    volumes:
      - dcmx-data:/data/dcmx
    environment:
      - DCMX_HOST=0.0.0.0
      - DCMX_PORT=8080
      - DCMX_DATA_DIR=/data/dcmx
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    depends_on:
      - dcmx-node

volumes:
  dcmx-data:
  prometheus-data:
```

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Upgrade image and restart
docker-compose build --no-cache
docker-compose up -d
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/DCMX-Protocol/DCMX.git
cd DCMX

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Create data directory
mkdir -p ~/.dcmx/content

# Test installation
pytest tests/ -v

# Start node
dcmx start --host 0.0.0.0 --port 8080
```

### Kubernetes Deployment

```yaml
# dcmx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmx-node
  labels:
    app: dcmx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dcmx
  template:
    metadata:
      labels:
        app: dcmx
    spec:
      containers:
      - name: dcmx
        image: dcmx:latest
        ports:
        - containerPort: 8080
          name: http
        volumeMounts:
        - name: dcmx-data
          mountPath: /data/dcmx
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /ping
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ping
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: dcmx-data
        persistentVolumeClaim:
          claimName: dcmx-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: dcmx-service
spec:
  type: LoadBalancer
  selector:
    app: dcmx
  ports:
  - port: 8080
    targetPort: 8080
    protocol: TCP
  sessionAffinity: None

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dcmx-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

```bash
# Deploy to Kubernetes
kubectl apply -f dcmx-deployment.yaml

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/dcmx-node

# Scale deployment
kubectl scale deployment dcmx-node --replicas=5

# Update image
kubectl set image deployment/dcmx-node \
  dcmx=dcmx:v1.1.0 --record
```

---

## Monitoring & Health Checks

### Health Check Endpoints

```bash
# Ping endpoint (minimal)
curl http://localhost:8080/ping
# Response: {"status": "ok"}

# Peers endpoint
curl http://localhost:8080/peers | jq .

# Tracks endpoint
curl http://localhost:8080/tracks | jq length

# Full stats
curl http://localhost:8080/stats | jq .
```

### Prometheus Metrics

```python
# prometheus_exporter.py
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import asyncio

# Metrics
peers_count = Gauge('dcmx_peers_count', 'Number of connected peers')
tracks_count = Gauge('dcmx_tracks_count', 'Number of local tracks')
content_size_bytes = Gauge('dcmx_content_size_bytes', 'Total content stored')
downloads_total = Counter('dcmx_downloads_total', 'Total downloads')
upload_bytes_total = Counter('dcmx_upload_bytes_total', 'Total bytes uploaded')
request_duration = Histogram('dcmx_request_duration_seconds', 'Request duration')

# Update metrics periodically
async def update_metrics(node):
    while True:
        peers_count.set(len(node.peers))
        tracks_count.set(len(node.tracks))
        # content_size_bytes.set(...)
        await asyncio.sleep(30)
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'dcmx'
    static_configs:
      - targets: ['localhost:9090']
```

### Logging Configuration

```python
# Setup comprehensive logging
import logging
import logging.handlers

# Create logger
logger = logging.getLogger('dcmx')
logger.setLevel(logging.DEBUG)

# File handler (rotate daily)
file_handler = logging.handlers.RotatingFileHandler(
    '/var/log/dcmx/node.log',
    maxBytes=100_000_000,  # 100 MB
    backupCount=10  # Keep 10 backups
)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)
```

### Alerting

```python
# alerting.py - Send alerts on critical events

async def check_health(node):
    """Monitor node health and send alerts."""
    
    while True:
        # Check peer connectivity
        if len(node.peers) == 0:
            alert("No peers connected!", severity="CRITICAL")
        elif len(node.peers) < 3:
            alert("Low peer count", severity="WARNING")
        
        # Check storage
        storage_mb = get_storage_size(node.data_dir) / (1024 ** 2)
        if storage_mb > STORAGE_THRESHOLD_MB:
            alert(f"Storage high: {storage_mb}MB", severity="WARNING")
        
        # Check error rate
        error_rate = get_error_rate(node)
        if error_rate > 0.05:  # 5% errors
            alert(f"High error rate: {error_rate*100}%", severity="WARNING")
        
        await asyncio.sleep(60)

def alert(message, severity="INFO"):
    """Send alert (email, Slack, PagerDuty, etc)."""
    if severity == "CRITICAL":
        send_email(ADMIN_EMAIL, message)
        send_slack(ALERTS_CHANNEL, message)
    elif severity == "WARNING":
        send_slack(ALERTS_CHANNEL, message)
```

---

## Performance Optimization

### Connection Pooling

```python
# Reuse HTTP connections
import aiohttp

class OptimizedProtocol:
    def __init__(self, max_connections=100):
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=10,
            ttl_dns_cache=300  # 5 min
        )
        self.session = aiohttp.ClientSession(connector=connector)
    
    async def connect(self, host, port):
        """Reuse connection from pool."""
        async with self.session.post(
            f"http://{host}:{port}/discover",
            timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            return await resp.json()
```

### Caching Strategy

```python
# Cache peer information and track metadata
from functools import lru_cache
import time

class CachedNode:
    def __init__(self):
        self.peer_cache = {}  # {peer_id: (peer_info, timestamp)}
        self.track_cache = {}  # {hash: track}
        self.cache_ttl = 300  # 5 minutes
    
    def get_cached_peer(self, peer_id):
        """Get peer from cache if fresh."""
        if peer_id in self.peer_cache:
            peer_info, timestamp = self.peer_cache[peer_id]
            if time.time() - timestamp < self.cache_ttl:
                return peer_info
        return None
    
    async def refresh_cache(self):
        """Periodically refresh stale entries."""
        now = time.time()
        expired = [
            pid for pid, (_, ts) in self.peer_cache.items()
            if now - ts > self.cache_ttl
        ]
        for pid in expired:
            del self.peer_cache[pid]
```

### Parallel Operations

```python
# Download from multiple peers in parallel
import asyncio

async def parallel_download(node, content_hash, num_chunks=5):
    """Download content from multiple peers in parallel."""
    
    # Find peers with content
    peers_with_content = [
        p for p in node.peers.values()
        if content_hash in p.available_tracks
    ]
    
    if not peers_with_content:
        raise ContentNotFound()
    
    # Split into chunks
    chunk_size = TRACK_SIZE // num_chunks
    
    # Download chunks in parallel
    tasks = [
        download_chunk(peer, content_hash, i*chunk_size, chunk_size)
        for i, peer in enumerate(peers_with_content[:num_chunks])
    ]
    
    chunks = await asyncio.gather(*tasks)
    return b''.join(chunks)
```

### Database Optimization (if using storage)

```python
# Batch operations to reduce I/O
async def batch_add_tracks(node, tracks):
    """Add multiple tracks efficiently."""
    
    # Group by content shard
    shards = {}
    for track in tracks:
        shard = track.content_hash[:2]
        if shard not in shards:
            shards[shard] = []
        shards[shard].append(track)
    
    # Add each shard in one operation
    for shard, shard_tracks in shards.items():
        node.content_store.batch_store(shard_tracks)
```

---

## Security Hardening

### TLS/HTTPS Configuration

```python
# Enable HTTPS
from dcmx.core.node import Node
import ssl

# Create SSL context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    '/etc/ssl/certs/node.crt',
    '/etc/ssl/private/node.key'
)

# Create node with HTTPS
node = Node(
    host="0.0.0.0",
    port=8080,
    ssl_context=ssl_context
)

# Now all communication is encrypted
# https://node:8080/ping
```

### Rate Limiting

```python
# Protect against abuse
from aiohttp import web

class RateLimiter:
    def __init__(self, requests_per_minute=100):
        self.limit = requests_per_minute
        self.requests = {}  # {ip: [timestamps]}
    
    async def check_rate_limit(self, request):
        """Check if IP has exceeded rate limit."""
        ip = request.remote
        now = time.time()
        
        # Clean old entries
        if ip in self.requests:
            self.requests[ip] = [
                ts for ts in self.requests[ip]
                if now - ts < 60
            ]
        else:
            self.requests[ip] = []
        
        # Check limit
        if len(self.requests[ip]) >= self.limit:
            return False
        
        self.requests[ip].append(now)
        return True
```

### Input Validation

```python
# Validate all peer input
def validate_peer_info(peer_dict):
    """Validate peer object from network."""
    
    required = ['peer_id', 'host', 'port']
    if not all(k in peer_dict for k in required):
        raise ValueError("Missing required fields")
    
    # Validate types
    if not isinstance(peer_dict['peer_id'], str):
        raise ValueError("peer_id must be string")
    if not isinstance(peer_dict['host'], str):
        raise ValueError("host must be string")
    if not isinstance(peer_dict['port'], int) or not 0 < peer_dict['port'] < 65536:
        raise ValueError("port must be 1-65535")
    
    # Validate format
    if len(peer_dict['peer_id']) != 36:  # UUID length
        raise ValueError("Invalid peer_id format")
    
    return peer_dict
```

### Key Management

```bash
# Generate secure node ID
python -c "from uuid import uuid4; print(uuid4())"

# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout node.key -out node.crt -days 365

# Store secrets securely
DCMX_PRIVATE_KEY=$(cat /etc/secrets/node.key)
DCMX_CERTIFICATE=$(cat /etc/secrets/node.crt)

# Don't commit to version control
echo "/etc/secrets/*" >> .gitignore
```

---

## Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Daily backup script

BACKUP_DIR="/backups/dcmx"
DATA_DIR="$HOME/.dcmx"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup important files (not content - that's replicated)
tar czf "$BACKUP_DIR/dcmx_metadata_$DATE.tar.gz" \
  "$DATA_DIR/tracks.json" \
  "$DATA_DIR/peers.json" \
  "$DATA_DIR/config.json"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

# Upload to cloud (optional)
aws s3 sync "$BACKUP_DIR" s3://dcmx-backups/
```

### Recovery Procedure

```bash
#!/bin/bash
# restore.sh - Recovery from backup

BACKUP_FILE="$1"
DATA_DIR="$HOME/.dcmx"

# Stop node
dcmx stop

# Restore from backup
tar xzf "$BACKUP_FILE" -C "$DATA_DIR"

# Restart node
dcmx start

echo "Restored from $BACKUP_FILE"
```

### High Availability Setup

```yaml
# haproxy.cfg - Load balance across nodes
global
    maxconn 4096

frontend dcmx_frontend
    bind *:8080
    default_backend dcmx_backend

backend dcmx_backend
    balance roundrobin
    option httpchk GET /ping
    server node1 10.0.1.10:8080 check
    server node2 10.0.1.11:8080 check
    server node3 10.0.1.12:8080 check
```

---

## Troubleshooting

### Node Won't Start

```bash
# Check logs
tail -100 ~/.dcmx/node.log

# Verify port is available
lsof -i :8080

# Check file permissions
ls -la ~/.dcmx/
chmod 755 ~/.dcmx

# Try with verbose output
dcmx start --verbose --log-level DEBUG
```

### High Memory Usage

```python
# Check what's consuming memory
import tracemalloc
tracemalloc.start()

# Run node
# ... after some time ...

current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.1f} MB")
print(f"Peak: {peak / 1024 / 1024:.1f} MB")

# Find top allocations
tracemalloc.stop()
```

### Slow Peer Discovery

```python
# Increase peer discovery parallelism
async def discover_peers(node):
    # Old: sequential discovery (slow)
    # for peer in node.peers:
    #     await connect_peer(peer)
    
    # New: parallel discovery (fast)
    tasks = [connect_peer(p) for p in node.peers]
    await asyncio.gather(*tasks, return_exceptions=True)
```

### Network Latency Issues

```bash
# Test latency to peer
ping -c 5 10.0.1.10

# Test bandwidth to peer
iperf3 -c 10.0.1.10 -t 10

# Check network connectivity
traceroute 10.0.1.10

# Monitor in real-time
watch -n 1 'netstat -i'
```

---

## Upgrade Procedures

### Zero-Downtime Upgrade (Blue-Green)

```bash
#!/bin/bash
# upgrade.sh - Upgrade without downtime

# 1. Verify new version
docker build -t dcmx:v1.1.0 .
docker run --rm dcmx:v1.1.0 dcmx --version

# 2. Start new instance (green)
docker run -d --name dcmx-green -p 8081:8080 dcmx:v1.1.0

# 3. Wait for green to be healthy
sleep 30
curl http://localhost:8081/ping

# 4. Switch traffic to green (via load balancer)
# Update HAProxy/Nginx to route to port 8081

# 5. Stop blue (old version)
docker stop dcmx-blue
docker rm dcmx-blue

# 6. Rename green to production
docker rename dcmx-green dcmx-blue

echo "Upgrade complete"
```

### Rollback Procedure

```bash
#!/bin/bash
# rollback.sh - Revert to previous version

# 1. Identify previous version
PREVIOUS_VERSION="v1.0.9"

# 2. Start old version on alternate port
docker run -d --name dcmx-rollback -p 8082:8080 dcmx:$PREVIOUS_VERSION

# 3. Test
curl http://localhost:8082/ping

# 4. Switch traffic back
# Update load balancer to route to port 8082

# 5. Stop new version
docker stop dcmx-blue
docker rm dcmx-blue

# 6. Rename rollback to production
docker rename dcmx-rollback dcmx-blue

echo "Rolled back to $PREVIOUS_VERSION"
```

---

## Operations Checklist

### Daily Tasks
- [ ] Check node health endpoint
- [ ] Verify peer connectivity
- [ ] Monitor disk usage
- [ ] Review error logs
- [ ] Check alert system

### Weekly Tasks
- [ ] Review performance metrics
- [ ] Verify backup completion
- [ ] Update software patches
- [ ] Test disaster recovery
- [ ] Review security logs

### Monthly Tasks
- [ ] Full system audit
- [ ] Capacity planning review
- [ ] Upgrade planning
- [ ] Security assessment
- [ ] Documentation update

### Quarterly Tasks
- [ ] Major version upgrade testing
- [ ] Load testing
- [ ] Disaster recovery drill
- [ ] Security penetration test
- [ ] Architecture review

---

## Emergency Contacts

```
Primary Admin: [name] - [email] - [phone]
Backup Admin:  [name] - [email] - [phone]
On-call:       [rotation schedule]

Cloud Provider Support: [account number]
DNS Provider:          [contact info]
```

---

**Document Version**: 1.0  
**Last Updated**: December 9, 2025  
**Maintained By**: DCMX Operations Team
