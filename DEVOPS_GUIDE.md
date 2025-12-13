# DCMX DevOps Guide

Complete guide for deploying and operating DCMX infrastructure.

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/DCMX-Protocol/DCMX.git
cd DCMX

# Start with Docker Compose
docker-compose up -d

# Access services
# API: http://localhost:8000
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Production Deployment

```bash
# 1. Set up secrets
kubectl create namespace dcmx-production
kubectl create secret generic dcmx-secrets \
  --from-literal=database-url='postgresql://...' \
  --from-literal=jwt-secret='...' \
  --from-literal=tron-private-key='...' \
  -n dcmx-production

# 2. Deploy to Kubernetes
kubectl apply -f k8s/base/deployment.yaml

# 3. Verify deployment
kubectl get pods -n dcmx-production
kubectl logs -f deployment/dcmx-api -n dcmx-production
```

## CI/CD Pipeline

### GitHub Actions Workflows

**Continuous Integration** (`.github/workflows/ci.yml`):
- ✅ Python tests with pytest (coverage required >80%)
- ✅ Frontend tests with Jest
- ✅ Code linting (flake8, black, mypy)
- ✅ Security scanning (Bandit, Safety, Trivy)
- ✅ Docker image builds
- ✅ Codecov integration

**Continuous Deployment** (`.github/workflows/cd.yml`):
- 🚀 Auto-deploy to staging on main branch
- 🚀 Manual deploy to production with approval
- 🚀 Database migrations with backup
- 🚀 Health checks and smoke tests
- 🚀 Slack notifications

**Security Scanning** (`.github/workflows/security.yml`):
- 🔒 Daily dependency vulnerability scans
- 🔒 SAST with Semgrep
- 🔒 Secret detection with TruffleHog
- 🔒 Container scanning with Trivy & Grype
- 🔒 IaC scanning with Checkov

### Triggering Deployments

```bash
# Deploy to staging (automatic on merge to main)
git push origin main

# Deploy to production (tag-based)
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Manual deployment
gh workflow run cd.yml -f environment=production
```

## Docker Containers

### Building Images

```bash
# Build API server
docker build -f docker/Dockerfile.api -t dcmx-api:latest .

# Build worker
docker build -f docker/Dockerfile.worker -t dcmx-worker:latest .

# Build frontend
cd frontend && docker build -t dcmx-frontend:latest .
```

### Running Locally

```bash
# Full stack
docker-compose up

# API only
docker-compose up api postgres redis

# View logs
docker-compose logs -f api
```

## Kubernetes Deployment

### Cluster Setup

**Requirements:**
- Kubernetes 1.28+
- cert-manager for TLS
- nginx-ingress-controller
- Persistent volume provisioner

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Install nginx-ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.9.0/deploy/static/provider/cloud/deploy.yaml
```

### Configuration

**Secrets (create before deployment):**

```bash
# Create from file
kubectl create secret generic dcmx-secrets \
  --from-env-file=.env.production \
  -n dcmx-production

# Or individual values
kubectl create secret generic dcmx-secrets \
  --from-literal=database-url='postgresql://dcmx:PASSWORD@postgres:5432/dcmx' \
  --from-literal=redis-url='redis://redis:6379' \
  --from-literal=jwt-secret='$(openssl rand -hex 32)' \
  --from-literal=tron-private-key='YOUR_PRIVATE_KEY' \
  -n dcmx-production
```

**ConfigMaps:**

```bash
kubectl create configmap dcmx-config \
  --from-literal=TRON_NETWORK=mainnet \
  --from-literal=LOG_LEVEL=INFO \
  -n dcmx-production
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment dcmx-api --replicas=5 -n dcmx-production

# Auto-scaling (HPA already configured)
kubectl get hpa -n dcmx-production

# Check pod status
kubectl get pods -n dcmx-production -w
```

### Database Migrations

```bash
# Run migrations
kubectl exec -n dcmx-production deployment/dcmx-api -- \
  python -m alembic upgrade head

# Rollback one version
kubectl exec -n dcmx-production deployment/dcmx-api -- \
  python -m alembic downgrade -1

# View migration history
kubectl exec -n dcmx-production deployment/dcmx-api -- \
  python -m alembic history
```

## Monitoring & Observability

### Prometheus Metrics

**Endpoint:** `http://localhost:9090` (development) or configured ingress

**Key Metrics:**
- `http_requests_total` - HTTP request counter
- `http_request_duration_seconds` - Request latency histogram
- `db_connections_active` - Active database connections
- `blockchain_last_indexed_block_number` - Indexer progress
- `nft_mints_total` - Total NFTs minted
- `auth_failed_total` - Failed auth attempts

### Grafana Dashboards

**Access:** `http://localhost:3000` (admin/admin)

**Dashboards:**
1. **DCMX Overview** - System health, request rates, errors
2. **Database Performance** - Query times, connection pool, slow queries
3. **Blockchain Indexer** - Block processing, transaction throughput
4. **Business Metrics** - NFT sales, revenue, active users
5. **Security** - Auth failures, rate limiting, suspicious activity

### Alerts

Configured in `monitoring/alerts.yml`:

**Critical Alerts:**
- API server down >2 minutes
- Database unreachable >1 minute
- Redis unreachable >1 minute

**Warning Alerts:**
- High error rate >5%
- Slow response times (p95 >2s)
- High CPU/memory usage >80%
- Blockchain indexer lag >5 minutes

**Notification Channels:**
- Slack: `#dcmx-alerts`
- PagerDuty: On-call rotation
- Email: ops@dcmx.network

### Logging

**Centralized logging** with Loki/ELK:

```bash
# View logs
kubectl logs -f deployment/dcmx-api -n dcmx-production

# Search logs
kubectl logs deployment/dcmx-api -n dcmx-production | grep ERROR

# Export logs
kubectl logs deployment/dcmx-api -n dcmx-production --since=1h > api-logs.txt
```

## Security

### Environment Variables

**Never commit:**
- `JWT_SECRET_KEY`
- `TRON_PRIVATE_KEY`
- `DB_PASSWORD`
- API keys

**Use Kubernetes secrets or vault:**

```bash
# Using sealed-secrets
kubeseal --format=yaml < secret.yaml > sealed-secret.yaml
kubectl apply -f sealed-secret.yaml
```

### SSL/TLS

**cert-manager** automatically provisions Let's Encrypt certificates:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@dcmx.network
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Network Policies

```bash
# Apply network policies
kubectl apply -f k8s/base/network-policies.yaml

# Verify
kubectl get networkpolicies -n dcmx-production
```

## Backup & Disaster Recovery

### Database Backups

**Automated daily backups:**

```bash
# Create backup
kubectl exec -n dcmx-production deployment/dcmx-postgres -- \
  pg_dump -U dcmx dcmx | gzip > backup-$(date +%Y%m%d).sql.gz

# Restore from backup
gunzip < backup-20240101.sql.gz | \
  kubectl exec -i -n dcmx-production deployment/dcmx-postgres -- \
  psql -U dcmx dcmx
```

**Backup schedule:**
- Daily: Retained 7 days
- Weekly: Retained 4 weeks  
- Monthly: Retained 12 months

### Disaster Recovery Plan

1. **Database failure:** Restore from latest backup (<1 hour RTO)
2. **Cluster failure:** Deploy to backup cluster (DNS failover)
3. **Region failure:** Multi-region deployment (active-passive)

## Performance Tuning

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_nft_owner ON nft_index(owner_wallet, minted_at);
CREATE INDEX idx_transaction_user ON transaction_index(user_wallet, timestamp);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM nft_index WHERE owner_wallet = '...';
```

### Caching Strategy

**Redis caching:**
- User profiles: TTL 5 minutes
- NFT metadata: TTL 1 hour
- Blockchain data: TTL 30 seconds
- API responses: TTL 10 seconds

### Load Testing

```bash
# Using k6
k6 run --vus 100 --duration 30s load-test.js

# Using Apache Bench
ab -n 10000 -c 100 https://api.dcmx.network/health
```

## Troubleshooting

### Common Issues

**1. Pod won't start:**
```bash
kubectl describe pod <pod-name> -n dcmx-production
kubectl logs <pod-name> -n dcmx-production --previous
```

**2. Database connection issues:**
```bash
# Test connection
kubectl exec -it deployment/dcmx-api -n dcmx-production -- \
  python -c "from dcmx.database import get_db_manager; get_db_manager().test_connection()"
```

**3. High memory usage:**
```bash
# Check resource usage
kubectl top pods -n dcmx-production

# Increase limits
kubectl set resources deployment dcmx-api --limits=memory=4Gi
```

### Debug Mode

```bash
# Enable debug logging
kubectl set env deployment/dcmx-api LOG_LEVEL=DEBUG -n dcmx-production

# Access pod shell
kubectl exec -it deployment/dcmx-api -n dcmx-production -- /bin/bash
```

## Support

- **Documentation:** https://docs.dcmx.network
- **Issues:** https://github.com/DCMX-Protocol/DCMX/issues
- **Slack:** #dcmx-devops
- **On-call:** ops@dcmx.network
