# DCMX Testnet Production Deployment

This guide covers hardening the testnet for production-like environments and long-term operation.

## Security Hardening

### Private Key Management
```bash
# Use environment secrets, NOT plain files
# For production: Use HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault

# Example with Kubernetes Secrets
kubectl create secret generic dcmx-keys \
  --from-literal=PRIVATE_KEY=$YOUR_PRIVATE_KEY \
  -n dcmx-testnet
```

### Network Security
```yaml
# Add Network Policy to Kubernetes
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: dcmx-network-policy
spec:
  podSelector:
    matchLabels:
      app: dcmx-node
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: dcmx-node
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: dcmx-node
  - to:
    - namespaceSelector: {}
```

### Database Hardening
```bash
# Update PostgreSQL password
ALTER USER compliance WITH PASSWORD 'strong_password_here';

# Enable SSL
# In docker-compose.yml, add: -c ssl=on

# Regular backups
0 2 * * * pg_dump postgresql://compliance:pass@localhost/dcmx_compliance > backup-$(date +\%Y\%m\%d).sql
```

### HTTPS/TLS Configuration
```bash
# Generate self-signed certificate for testing
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# For production: Use Let's Encrypt
# Add to nginx reverse proxy in docker-compose
```

## Compliance Hardening

### GDPR/CCPA Compliance
```python
# Ensure data deletion is working
# Test deletion request workflow
# Verify audit logs are immutable

# Regular compliance audits (quarterly)
SELECT COUNT(*) FROM deletion_requests WHERE status = 'completed';
SELECT COUNT(*) FROM suspicious_activity_reports WHERE filed = TRUE;
```

### AML/KYC Enhanced Controls
```bash
# Increase OFAC check frequency in production
COMPLIANCE_OFAC_UPDATE_FREQ=3d

# Enable transaction monitoring
COMPLIANCE_AML_ENABLED=true

# Set lower thresholds for monitoring
AML_TRANSACTION_THRESHOLD=5000  # USD
AML_24H_THRESHOLD=50000  # USD
```

## Operational Excellence

### Monitoring & Alerting
```yaml
# Set up Prometheus alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: dcmx-alerts
spec:
  groups:
  - name: dcmx.rules
    interval: 30s
    rules:
    - alert: HighPeerLatency
      expr: histogram_quantile(0.95, dcmx_transaction_latency_ms) > 1000
      for: 5m
      annotations:
        summary: "High peer latency detected"
    
    - alert: NodeDiskFull
      expr: dcmx_storage_usage_percent > 90
      for: 1m
      annotations:
        summary: "Node disk nearly full"
    
    - alert: ComplianceMonitorDown
      expr: up{job="compliance-monitor"} == 0
      for: 1m
      annotations:
        summary: "Compliance monitor is down"
```

### Disaster Recovery

**Backup Strategy**
```bash
# Daily backups of all data
0 3 * * * docker-compose exec compliance-db pg_dump -U compliance dcmx_compliance | gzip > /backups/db-$(date +%Y%m%d).sql.gz

# Weekly blockchain state snapshots
0 4 * * 0 docker-compose exec dcmx-node-1 tar czf /tmp/state.tar.gz /var/lib/dcmx && mv /tmp/state.tar.gz /backups/state-$(date +%Y%m%d).tar.gz
```

**Recovery Procedures**
```bash
# Restore from backup
docker-compose down
gzip -d backup.sql.gz | docker exec -i dcmx-compliance-db psql -U compliance dcmx_compliance
docker-compose up -d
```

### Performance Optimization

**Database Tuning**
```sql
-- PostgreSQL optimization for production
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

SELECT pg_reload_conf();
```

**Node Tuning**
```bash
# Increase file descriptors
ulimit -n 65536

# Tune kernel network parameters
sysctl -w net.core.somaxconn=4096
sysctl -w net.ipv4.tcp_max_syn_backlog=2048
```

## Capacity Planning

### Resource Requirements by Load

| Metric | Light | Medium | Heavy |
|--------|-------|--------|-------|
| **Nodes** | 1 | 3 | 5+ |
| **Node RAM** | 256MB | 512MB | 1GB+ |
| **Node CPU** | 100m | 500m | 2+ cores |
| **Storage** | 10GB | 50GB | 500GB+ |
| **Database** | 1GB | 5GB | 50GB+ |
| **Throughput** | 10 tx/s | 100 tx/s | 1000+ tx/s |

### Scaling Strategies

**Horizontal Scaling**
```bash
# Add more nodes to the network
docker-compose scale dcmx-node=5

# Or in Kubernetes
kubectl scale statefulset dcmx-node --replicas=10 -n dcmx-testnet
```

**Vertical Scaling**
```yaml
# Increase node resources in docker-compose.yml
resources:
  limits:
    memory: "2G"
    cpus: "2.0"
```

## Compliance Checklist

### Before Production Deployment

- [ ] All 273 tests passing
- [ ] Security audit completed
- [ ] Encryption keys stored securely
- [ ] Database backups tested
- [ ] Disaster recovery procedures documented
- [ ] Monitoring and alerting configured
- [ ] Compliance checks operational
- [ ] GDPR/CCPA procedures documented
- [ ] AML/KYC workflows tested
- [ ] Rate limiting configured
- [ ] DDoS protection enabled
- [ ] Incident response plan documented

### Regular Maintenance

- [ ] Weekly: Check logs for errors
- [ ] Weekly: Verify backup integrity
- [ ] Monthly: Review access logs
- [ ] Monthly: Update OFAC list
- [ ] Quarterly: Security audit
- [ ] Quarterly: Compliance review
- [ ] Yearly: Full infrastructure review

## Troubleshooting Production Issues

### High Memory Usage
```bash
# Check what's using memory
docker stats

# Profile heap usage
python -m memory_profiler -o profile.txt dcmx/node.py

# Restart affected service
docker-compose restart dcmx-node-1
```

### Database Corruption
```bash
# Check database integrity
docker exec dcmx-compliance-db reindex DATABASE dcmx_compliance;

# If severe, restore from backup
```

### Network Congestion
```bash
# Monitor peer latency
curl http://localhost:9090/api/v1/query?query=dcmx_transaction_latency_ms

# Reduce broadcast frequency if too high
# Implement message batching
```

## Support & Escalation

### Emergency Contacts
- **Security Issues**: security@dcmx.io
- **Operations**: ops@dcmx.io
- **Compliance**: compliance@dcmx.io

### Documentation References
- [DCMX Architecture](../README.md)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/sql-syntax.html)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
