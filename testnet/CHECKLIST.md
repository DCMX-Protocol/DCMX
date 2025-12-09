# DCMX Testnet Deployment Checklist

## Pre-Deployment

### Environment Setup
- [ ] Clone DCMX repository
- [ ] Install Docker & Docker Compose (v2+)
- [ ] Install kubectl (if using Kubernetes)
- [ ] Have Ethereum Sepolia RPC URL ready
- [ ] Have testnet private key ready

### Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Fill in `ETHEREUM_RPC_URL` with Sepolia RPC endpoint
- [ ] Fill in `PRIVATE_KEY` with test wallet private key
- [ ] Verify all required environment variables are set
- [ ] Review `docker-compose.yml` for port conflicts

## Deployment

### Docker Compose (Local/Staging)
- [ ] Navigate to `testnet/` directory
- [ ] Run `docker-compose up -d`
- [ ] Wait 30 seconds for services to start
- [ ] Verify with `./scripts/verify-testnet.sh`
- [ ] Check logs: `docker-compose logs -f`

### Kubernetes (Production)
- [ ] Build Docker images: `docker build -f testnet/Dockerfile -t dcmx:testnet ..`
- [ ] Update image registry in Kubernetes manifests
- [ ] Update Secrets in `k8s/02-configmap.yml`
- [ ] Run `./deploy-k8s.sh`
- [ ] Verify with `kubectl get pods -n dcmx-testnet`

## Verification

### Health Checks
- [ ] DCMX Node 1 responding to `/ping` (port 8001)
- [ ] DCMX Node 2 responding to `/ping` (port 8002)
- [ ] DCMX Node 3 responding to `/ping` (port 8003)
- [ ] Compliance Monitor responding (port 9001)
- [ ] Prometheus scraping metrics (port 9090)
- [ ] Grafana accessible (port 3000)
- [ ] Jaeger tracing active (port 6831)

### Network Verification
- [ ] Nodes discovering each other: `curl http://localhost:8001/peers`
- [ ] Each node sees at least 2 peers
- [ ] Peer latency < 1000ms
- [ ] No "connection refused" errors in logs

### Compliance Verification
- [ ] PostgreSQL running and accessible
- [ ] Redis cache operational
- [ ] OFAC SDN list downloaded
- [ ] KYC verification endpoints working
- [ ] Compliance audit log created

### Data Verification
- [ ] Node storage directories created (`/var/lib/dcmx/`)
- [ ] Database tables initialized (check PostgreSQL)
- [ ] Prometheus has collected metrics
- [ ] Jaeger has received spans

## Testing

### Unit Tests
- [ ] Run: `cd /workspaces/DCMX && python -m pytest tests/ -v`
- [ ] Result: **All 273 tests passing** ✅
- [ ] No hanging tests
- [ ] No resource leaks

### Integration Tests
- [ ] Run: `./scripts/run-tests.sh`
- [ ] Peer discovery test passing
- [ ] Content distribution test passing
- [ ] Compliance check tests passing
- [ ] Transaction latency < 200ms

### Manual Smoke Tests
```bash
# Test node connectivity
curl -s http://localhost:8001/ping

# Test peer discovery
curl -s http://localhost:8001/peers | jq .

# Test track listing
curl -s http://localhost:8001/tracks | jq .

# Test compliance endpoint
curl -s http://localhost:9001/health | jq .
```

## Monitoring Setup

### Prometheus
- [ ] Targets page shows all services UP
- [ ] Metrics being scraped every 10-15 seconds
- [ ] No "connection refused" errors
- [ ] Retention policy set to 30 days

### Grafana
- [ ] Admin login successful (admin/admin)
- [ ] Prometheus datasource configured
- [ ] At least one dashboard visible
- [ ] Metrics graphs updating in real-time

### Jaeger
- [ ] Service list populated
- [ ] Traces being received
- [ ] Can query recent traces
- [ ] Span details visible

## Documentation Review

- [ ] Read `testnet/README.md`
- [ ] Review `testnet/DEPLOYMENT.md`
- [ ] Understand `testnet/PRODUCTION.md` for production deployment
- [ ] Check troubleshooting section for common issues
- [ ] Review environment variable options

## Security Hardening

### Secrets Management
- [ ] Private key not in version control
- [ ] `.env` file added to `.gitignore`
- [ ] Use Kubernetes Secrets for production (not ConfigMaps)
- [ ] Rotate private key periodically

### Network Security
- [ ] Enable firewall rules restricting access
- [ ] Use VPN for accessing services in production
- [ ] Enable TLS/SSL for inter-service communication
- [ ] Configure network policies in Kubernetes

### Database Security
- [ ] Change default PostgreSQL password
- [ ] Enable SSL for database connections
- [ ] Set up regular automated backups
- [ ] Test backup restoration procedure

## Backup & Recovery

### Backup Setup
- [ ] Configure daily PostgreSQL backups
- [ ] Configure daily volume snapshots
- [ ] Test backup restoration
- [ ] Document recovery procedures
- [ ] Store backups in secure location

### Disaster Recovery
- [ ] Document RTO (Recovery Time Objective)
- [ ] Document RPO (Recovery Point Objective)
- [ ] Test failover procedures
- [ ] Have incident response plan

## Maintenance Planning

### Regular Tasks
- [ ] **Daily**: Monitor logs for errors
- [ ] **Weekly**: Verify backups integrity
- [ ] **Weekly**: Check disk space usage
- [ ] **Monthly**: Review compliance audit logs
- [ ] **Monthly**: Update OFAC list
- [ ] **Quarterly**: Run security audit
- [ ] **Quarterly**: Compliance review

### Scaling Plan
- [ ] Document node scaling procedure
- [ ] Set up auto-scaling (Kubernetes HPA)
- [ ] Load testing to determine capacity limits
- [ ] Capacity planning for 6-12 months

## Compliance Readiness

### Regulatory
- [ ] Smart contract audit completed
- [ ] Watermark/DRM implementation verified
- [ ] KYC/AML workflows tested
- [ ] GDPR/CCPA procedures documented
- [ ] Data retention policies defined

### Audit Trail
- [ ] Immutable audit logs operational
- [ ] 7-year retention policy enforced
- [ ] Log integrity verification working
- [ ] SAR filing capability verified

## Go-Live Preparation

### Final Checks (48 hours before)
- [ ] All tests passing one final time
- [ ] No critical log errors in past 24 hours
- [ ] Backup verified in past 24 hours
- [ ] Team on-call schedule confirmed
- [ ] Escalation procedures documented

### Go-Live Day
- [ ] All team members online and available
- [ ] Monitoring dashboards open and visible
- [ ] Incident communication channels active
- [ ] Deployment rolled out to small percentage first
- [ ] Monitor metrics during deployment

### Post-Deployment (First 24 hours)
- [ ] No spike in error rates
- [ ] Transaction latency stable
- [ ] Compliance checks processing normally
- [ ] Backup ran successfully
- [ ] Monitoring alerts working correctly

## Post-Deployment

### Documentation
- [ ] Document actual deployment configuration
- [ ] Record any deviations from plan
- [ ] Update runbooks with real endpoints
- [ ] Share credentials securely with team

### Team Training
- [ ] On-call engineer familiar with deployment
- [ ] SRE team trained on monitoring
- [ ] Compliance team briefed on audit logs
- [ ] Operations team ready for scaling

### Monitoring & Alerting
- [ ] Alerting rules tested and verified
- [ ] Slack/PagerDuty integration working
- [ ] Alert severity levels appropriate
- [ ] Escalation procedures clear

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Deployment Lead | | | ☐ |
| Infrastructure Lead | | | ☐ |
| Compliance Officer | | | ☐ |
| Security Lead | | | ☐ |

## Notes & Issues

Use this section to document any issues encountered during deployment:

```
Issue 1: 
- Description: 
- Resolution: 
- Prevention: 

Issue 2:
- Description:
- Resolution:
- Prevention:
```

---

## Quick Reference Commands

```bash
# Start testnet
docker-compose up -d

# Stop testnet
docker-compose down

# View logs
docker-compose logs -f

# Run tests
./scripts/run-tests.sh

# Verify health
./scripts/verify-testnet.sh

# Clean up
./scripts/cleanup.sh --full

# Access services
# Nodes: http://localhost:8001-8003
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
# Jaeger: http://localhost:6831
```

---

**Deployment Date**: _______________
**Deployed By**: _______________
**Environment**: [ ] Local [ ] Staging [ ] Production
**Testnet Version**: v0.1.0
