# DCMX Compliance Audit Logger

**Production-grade audit logging system for government compliance and forensic investigation.**

## Features

- ✅ **Immutable Audit Trail**: SHA-256 hashing with blockchain-style integrity chain
- ✅ **SQLite Persistence**: Durable storage with 7-year retention policy
- ✅ **Government Compliance**: FinCEN, SEC, GDPR, CCPA requirements
- ✅ **SAR Reporting**: Suspicious Activity Report generation for FinCEN filing
- ✅ **Transaction Tracking**: All financial transactions logged with compliance details
- ✅ **Forensic Investigation**: Complete audit trail with chain of custody
- ✅ **Export Capabilities**: JSON and CSV export for regulatory submission
- ✅ **Compliance Metrics**: Real-time compliance reporting

## Quick Start

```python
from dcmx.compliance import ComplianceAuditLogger, AuditEventType

# Initialize logger
audit_logger = ComplianceAuditLogger(db_path="compliance_audit.db")

# Log login event
audit_logger.log_event(
    event_type=AuditEventType.LOGIN,
    user_id="user123",
    username="john_doe",
    ip_address="192.168.1.100"
)

# Log transaction
audit_logger.log_transaction(
    user_id="user123",
    wallet_address="0x123abc...",
    amount=15000.0,
    currency="DCMX",
    transaction_type="nft_purchase"
)

# Get audit trail
trail = audit_logger.get_audit_trail(user_id="user123")

# Create SAR report
sar = audit_logger.create_sar_report(
    event_ids=[event.event_id for event in trail],
    description="Multiple large transfers detected"
)

# Export for regulatory submission
audit_logger.export_audit_log("audit_export.json", format="json")
```

## Event Types

### Authentication
- `LOGIN` - User login
- `LOGOUT` - User logout
- `LOGIN_FAILED` - Failed login attempt
- `PASSWORD_CHANGE` - Password changed

### KYC/AML
- `KYC_INITIATED` - KYC verification started
- `KYC_APPROVED` - KYC verification approved
- `KYC_REJECTED` - KYC verification rejected
- `OFAC_CHECK_PASSED` - OFAC sanctions check passed
- `OFAC_CHECK_FAILED` - OFAC sanctions check failed
- `SANCTION_MATCH` - Address matched sanctions list

### Transactions
- `TRANSACTION_INITIATED` - Transaction started
- `TRANSACTION_APPROVED` - Transaction approved
- `TRANSACTION_REJECTED` - Transaction rejected
- `TRANSACTION_COMPLETED` - Transaction completed
- `TRANSACTION_REVERSED` - Transaction reversed

### Compliance
- `AML_THRESHOLD_EXCEEDED` - Transaction > $10,000
- `STRUCTURING_DETECTED` - Pattern of transactions to avoid reporting
- `SUSPICIOUS_ACTIVITY` - Suspicious activity detected
- `COMPLIANCE_ALERT` - General compliance alert

### User Management
- `USER_CREATED` - New user created
- `USER_UPDATED` - User profile updated
- `USER_DELETED` - User deleted
- `USER_ACCOUNT_LOCKED` - Account locked

### Data Access
- `DATA_ACCESS` - Sensitive data accessed
- `EXPORT_REQUESTED` - Data export requested
- `DELETION_REQUESTED` - Data deletion requested

## Audit Trail Structure

```python
ComplianceAuditEvent(
    event_id="1702161600.123456",           # Unique ID
    event_type=AuditEventType.TRANSACTION_COMPLETED,
    timestamp="2024-12-09T20:00:00+00:00",  # UTC ISO format
    
    # Actor
    user_id="user123",
    username="john_doe",
    wallet_address="0x123abc...",
    
    # Resource
    resource_type="transaction",
    resource_id="txn_12345",
    
    # Action
    action="nft_purchase",
    status="success",
    
    # Compliance
    amount=1000.0,
    currency="DCMX",
    kyc_level=2,
    jurisdiction=ComplianceRegion.US,
    
    # Technical
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0...",
    session_id="sess_abc123",
    
    # Integrity
    hash="abc123def456...",              # SHA-256 of event
    parent_hash="xyz789...",              # Hash of previous event
)
```

## Compliance Requirements

### SEC Requirements
- ✅ Transaction audit trail (7 years)
- ✅ User access logging
- ✅ Admin action tracking
- ✅ System change logs

### FinCEN (Money Transmission)
- ✅ Customer Identification Program (KYC)
- ✅ Anti-Money Laundering (AML) monitoring
- ✅ Suspicious Activity Report (SAR) generation
- ✅ $10K transaction reporting
- ✅ Structuring detection

### GDPR (EU)
- ✅ Data access logging
- ✅ Right to deletion tracking
- ✅ Data breach notifications
- ✅ User consent records

### CCPA (California)
- ✅ Personal data access logs
- ✅ Deletion request tracking
- ✅ Sale opt-out logging

## Usage Examples

### Log KYC Verification

```python
audit_logger.log_event(
    event_type=AuditEventType.KYC_APPROVED,
    user_id="user123",
    wallet_address="0x123abc",
    kyc_level=2,
    details={
        "verification_method": "id_scan",
        "verified_by": "admin_user",
        "document_type": "passport"
    }
)
```

### Log Large Transaction

```python
audit_logger.log_transaction(
    user_id="user123",
    wallet_address="0x456def",
    amount=25000.0,
    currency="DCMX",
    transaction_type="nft_sale",
    recipient_wallet="0x789ghi"
)
```

### Detect Suspicious Patterns

```python
# Check for structuring (multiple transactions to avoid $10k reporting)
trail = audit_logger.get_audit_trail(user_id="user123", limit=100)
large_txns = [e for e in trail if e.amount and e.amount > 9000]

if len(large_txns) > 5 in timedelta(hours=1):
    audit_logger.log_event(
        event_type=AuditEventType.STRUCTURING_DETECTED,
        user_id="user123",
        status="alert",
        details={"transaction_count": len(large_txns)}
    )
```

### Generate SAR Report

```python
# Retrieve suspicious events
suspicious_events = audit_logger.get_audit_trail(
    event_types=[AuditEventType.SUSPICIOUS_ACTIVITY],
    limit=100
)

# Create SAR
sar = audit_logger.create_sar_report(
    event_ids=[e.event_id for e in suspicious_events],
    description="Pattern of suspicious transactions detected"
)

# File with FinCEN
audit_logger.file_sar_report(
    sar_id=sar["sar_id"],
    filing_reference="FinCEN-2024-123456"
)
```

### Export for Audit

```python
# Export all transactions for specific user
audit_logger.export_audit_log(
    export_path="audit_user123.json",
    user_id="user123",
    format="json"
)

# Export all large transactions
all_events = audit_logger.get_audit_trail(limit=999999)
large_txns = [e for e in all_events if e.amount and e.amount > 10000]

# Save to CSV
import csv
with open("large_transactions.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=large_txns[0].to_dict().keys())
    writer.writeheader()
    for event in large_txns:
        writer.writerow(event.to_dict())
```

### Retrieve Audit Trail

```python
# All events for user
trail = audit_logger.get_audit_trail(user_id="user123")

# Events in date range
start = "2024-01-01T00:00:00Z"
end = "2024-12-31T23:59:59Z"
trail = audit_logger.get_audit_trail(
    start_date=start,
    end_date=end
)

# Specific event types
trail = audit_logger.get_audit_trail(
    event_types=[
        AuditEventType.TRANSACTION_COMPLETED,
        AuditEventType.TRANSACTION_REJECTED
    ]
)

# With limit
trail = audit_logger.get_audit_trail(limit=50)
```

### Get Compliance Metrics

```python
metrics = audit_logger.get_compliance_metrics()

print(f"Total events: {metrics['total_events']}")
print(f"Failed transactions: {metrics['failed_transactions']}")
print(f"Large transactions: {metrics['large_transactions']}")
print(f"Suspicious activities: {metrics['suspicious_activities']}")
print(f"SAR reports: {metrics['sar_reports']}")
```

## Database Schema

### `audit_events` Table
```sql
CREATE TABLE audit_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_id TEXT,
    username TEXT,
    wallet_address TEXT,
    resource_type TEXT,
    resource_id TEXT,
    action TEXT,
    status TEXT,
    result TEXT,
    amount REAL,
    currency TEXT,
    jurisdiction TEXT,
    kyc_level INTEGER,
    risk_score REAL,
    ip_address TEXT,
    user_agent TEXT,
    session_id TEXT,
    details TEXT,
    error_message TEXT,
    hash TEXT,
    parent_hash TEXT,
    created_at TIMESTAMP
)
```

### `compliance_alerts` Table
```sql
CREATE TABLE compliance_alerts (
    alert_id TEXT PRIMARY KEY,
    event_id TEXT,
    alert_type TEXT NOT NULL,
    severity TEXT,
    description TEXT,
    action_taken TEXT,
    reported_at TEXT
)
```

### `sar_reports` Table
```sql
CREATE TABLE sar_reports (
    sar_id TEXT PRIMARY KEY,
    event_ids TEXT,
    description TEXT,
    fincen_filed BOOLEAN,
    filed_date TEXT,
    filing_reference TEXT,
    jurisdiction TEXT,
    created_at TIMESTAMP
)
```

## Integrity Chain

Events are linked in an immutable chain using SHA-256 hashing:

```
Event 1: hash=abc123, parent_hash=""
   ↓
Event 2: hash=def456, parent_hash=abc123
   ↓
Event 3: hash=ghi789, parent_hash=def456
   ↓
Event 4: hash=jkl012, parent_hash=ghi789
```

Any tampering with earlier events will break the chain, making attacks detectable.

## Data Retention

- **Default**: 7 years (2555 days) - SEC requirement
- **Configurable**: Pass `retention_days` to constructor
- **Automatic Cleanup**: Call `cleanup_old_logs()` to remove expired events

```python
# Configure custom retention
logger = ComplianceAuditLogger(
    db_path="audit.db",
    retention_days=365 * 10  # 10 years
)

# Manual cleanup
deleted_count = logger.cleanup_old_logs()
```

## Performance

- **Logging**: O(1) per event
- **Retrieval**: O(n) indexed by user/timestamp
- **Export**: O(n) for all events
- **Cleanup**: O(n) for expired events

### Optimization Tips
1. Create indexes on frequently queried columns
2. Archive events older than 2 years to separate database
3. Use event types to filter at query time
4. Batch exports instead of retrieving all events

## Security

- ✅ SQLite with journaling (atomic writes)
- ✅ SHA-256 integrity hashing
- ✅ Immutable event chain
- ✅ Event timestamps in UTC
- ✅ User/IP/session tracking
- ✅ Detailed error logging

## Production Deployment

### Requirements
```bash
pip install sqlite3  # Included in Python
```

### Configuration
```python
import os
from dcmx.compliance import ComplianceAuditLogger

# Load from environment
db_path = os.getenv("COMPLIANCE_DB_PATH", "/var/dcmx/compliance_audit.db")
retention_days = int(os.getenv("AUDIT_RETENTION_DAYS", "2555"))

audit_logger = ComplianceAuditLogger(
    db_path=db_path,
    retention_days=retention_days
)
```

### Backup Strategy
```bash
# Daily backup
0 2 * * * sqlite3 /var/dcmx/compliance_audit.db ".backup /backups/audit-$(date +\%Y\%m\%d).db"
```

### Monitoring
```python
# Health check
metrics = audit_logger.get_compliance_metrics()
if metrics['suspicious_activities'] > 10:
    alert_compliance_team("High suspicious activity count")
```

## Testing

```bash
pytest tests/test_compliance_audit.py -v
```

## Troubleshooting

### Database Locked
```python
# Reduce concurrent access or increase timeout
import sqlite3
conn = sqlite3.connect(db_path, timeout=30.0)
```

### Large Database Size
```python
# Run cleanup
count = audit_logger.cleanup_old_logs()
print(f"Deleted {count} expired events")

# Vacuum to reclaim space
import sqlite3
conn = sqlite3.connect(audit_logger.db_path)
conn.execute("VACUUM")
conn.close()
```

### Missing Events
```python
# Verify database integrity
trail = audit_logger.get_audit_trail(limit=1)
if trail:
    print(f"Latest event: {trail[0].event_id}")
```

## References

- **FinCEN SAR**: https://www.fincen.gov/suspicious-activity-report
- **SEC Rule 10b5**: https://www.sec.gov/cgi-bin/viewer?action=view&cik=&accession_number=0000950123-20-011606
- **GDPR Article 5**: https://gdpr-info.eu/articles/principles-relating-to-processing/
- **CCPA**: https://oag.ca.gov/privacy/ccpa

---

**Next Steps**: Integrate with Node for automatic event logging on all operations.
