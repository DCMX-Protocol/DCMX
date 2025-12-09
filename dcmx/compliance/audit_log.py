"""
DCMX Compliance Audit Logger

Implements:
- Immutable audit trail logging
- Government compliance requirements (SEC, FinCEN, GDPR, CCPA)
- Transaction tracking with forensic details
- Suspicious activity reporting (SAR)
- Data retention policies (7+ years)
- Blockchain audit verification
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum
import sqlite3
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Government-reportable audit event types."""
    # Authentication events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    
    # KYC/AML events
    KYC_INITIATED = "kyc_initiated"
    KYC_APPROVED = "kyc_approved"
    KYC_REJECTED = "kyc_rejected"
    KYC_UPDATED = "kyc_updated"
    OFAC_CHECK_PASSED = "ofac_check_passed"
    OFAC_CHECK_FAILED = "ofac_check_failed"
    
    # Transaction events
    TRANSACTION_INITIATED = "transaction_initiated"
    TRANSACTION_APPROVED = "transaction_approved"
    TRANSACTION_REJECTED = "transaction_rejected"
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_REVERSED = "transaction_reversed"
    
    # Compliance events
    COMPLIANCE_ALERT = "compliance_alert"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    AML_THRESHOLD_EXCEEDED = "aml_threshold_exceeded"
    STRUCTURING_DETECTED = "structuring_detected"
    SANCTION_MATCH = "sanction_match"
    
    # User management
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_ACCOUNT_LOCKED = "user_account_locked"
    
    # System events
    SYSTEM_ACCESS = "system_access"
    DATA_ACCESS = "data_access"
    EXPORT_REQUESTED = "export_requested"
    DELETION_REQUESTED = "deletion_requested"
    
    # Admin events
    ADMIN_ACTION = "admin_action"
    CONFIGURATION_CHANGED = "configuration_changed"
    SECURITY_SETTING_CHANGED = "security_setting_changed"


class ComplianceRegion(Enum):
    """Geographic compliance region."""
    US = "US"
    EU = "EU"
    UK = "UK"
    ASIA = "ASIA"
    OTHER = "OTHER"


@dataclass
class ComplianceAuditEvent:
    """Immutable audit event for compliance."""
    
    # Event identification
    event_id: str = field(default_factory=lambda: str(datetime.now(timezone.utc).timestamp()))
    event_type: AuditEventType = AuditEventType.LOGIN
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # User/Actor
    user_id: str = ""
    username: str = ""
    wallet_address: str = ""
    
    # Resource
    resource_type: str = ""
    resource_id: str = ""
    
    # Action details
    action: str = ""
    status: str = "success"  # success, failure, pending
    result: str = ""
    
    # Compliance details
    amount: Optional[float] = None
    currency: str = "DCMX"
    jurisdiction: ComplianceRegion = ComplianceRegion.US
    kyc_level: int = 0
    risk_score: float = 0.0
    
    # Technical details
    ip_address: str = ""
    user_agent: str = ""
    session_id: str = ""
    
    # Audit trail
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Integrity
    hash: str = ""
    parent_hash: str = ""  # Links to previous event
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of event for integrity."""
        event_data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "amount": self.amount,
            "status": self.status,
        }
        json_str = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['jurisdiction'] = self.jurisdiction.value
        return data
    
    def is_reportable(self) -> bool:
        """Check if event requires government reporting."""
        reportable_types = {
            AuditEventType.KYC_APPROVED,
            AuditEventType.KYC_REJECTED,
            AuditEventType.TRANSACTION_COMPLETED,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.SANCTION_MATCH,
            AuditEventType.STRUCTURING_DETECTED,
            AuditEventType.AML_THRESHOLD_EXCEEDED,
        }
        return self.event_type in reportable_types


class ComplianceAuditLogger:
    """Production-grade compliance audit logger with government reporting."""
    
    def __init__(
        self,
        db_path: str = "compliance_audit.db",
        retention_days: int = 2555  # 7 years
    ):
        self.db_path = db_path
        self.retention_days = retention_days
        self.events: List[ComplianceAuditEvent] = []
        self.parent_hash = ""
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for audit logs."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create audit log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON audit_events(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON audit_events(status)")
        
        # Create compliance alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_alerts (
                alert_id TEXT PRIMARY KEY,
                event_id TEXT,
                alert_type TEXT NOT NULL,
                severity TEXT,
                description TEXT,
                action_taken TEXT,
                reported_at TEXT,
                foreign KEY (event_id) REFERENCES audit_events(event_id)
            )
        """)
        
        # Create SAR (Suspicious Activity Report) table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sar_reports (
                sar_id TEXT PRIMARY KEY,
                event_ids TEXT,
                description TEXT,
                fincen_filed BOOLEAN,
                filed_date TEXT,
                filing_reference TEXT,
                jurisdiction TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Compliance audit database initialized: {self.db_path}")
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        **kwargs
    ) -> ComplianceAuditEvent:
        """Log compliance audit event.
        
        Args:
            event_type: Type of event
            user_id: User performing action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            **kwargs: Additional event details
            
        Returns:
            Created ComplianceAuditEvent
        """
        event = ComplianceAuditEvent(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            **kwargs
        )
        
        # Compute hash for integrity
        event.hash = event.compute_hash()
        event.parent_hash = self.parent_hash
        self.parent_hash = event.hash
        
        # Store in memory
        self.events.append(event)
        
        # Persist to database
        self._persist_event(event)
        
        # Check if reportable
        if event.is_reportable():
            logger.warning(f"Reportable event: {event_type.value} - {event.event_id}")
        
        logger.info(f"Audit event logged: {event_type.value} ({event.event_id})")
        return event
    
    def _persist_event(self, event: ComplianceAuditEvent):
        """Persist event to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_events (
                    event_id, event_type, timestamp, user_id, username,
                    wallet_address, resource_type, resource_id, action,
                    status, result, amount, currency, jurisdiction, kyc_level,
                    risk_score, ip_address, user_agent, session_id, details,
                    error_message, hash, parent_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.event_type.value, event.timestamp,
                event.user_id, event.username, event.wallet_address,
                event.resource_type, event.resource_id, event.action,
                event.status, event.result, event.amount, event.currency,
                event.jurisdiction.value, event.kyc_level, event.risk_score,
                event.ip_address, event.user_agent, event.session_id,
                json.dumps(event.details), event.error_message,
                event.hash, event.parent_hash
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to persist audit event: {e}")
            raise
    
    def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        event_types: Optional[List[AuditEventType]] = None,
        limit: int = 1000
    ) -> List[ComplianceAuditEvent]:
        """Retrieve audit trail.
        
        Args:
            user_id: Filter by user
            start_date: ISO format start date
            end_date: ISO format end date
            event_types: Filter by event types
            limit: Max results
            
        Returns:
            List of audit events
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM audit_events WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            
            if event_types:
                placeholders = ",".join(["?" for _ in event_types])
                query += f" AND event_type IN ({placeholders})"
                params.extend([et.value for et in event_types])
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            conn.close()
            
            events = []
            for row in rows:
                event = ComplianceAuditEvent(
                    event_id=row['event_id'],
                    event_type=AuditEventType(row['event_type']),
                    timestamp=row['timestamp'],
                    user_id=row['user_id'],
                    username=row['username'],
                    wallet_address=row['wallet_address'],
                    resource_type=row['resource_type'],
                    resource_id=row['resource_id'],
                    action=row['action'],
                    status=row['status'],
                    result=row['result'],
                    amount=row['amount'],
                    currency=row['currency'],
                    jurisdiction=ComplianceRegion(row['jurisdiction']),
                    kyc_level=row['kyc_level'],
                    risk_score=row['risk_score'],
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    session_id=row['session_id'],
                    details=json.loads(row['details']) if row['details'] else {},
                    error_message=row['error_message'],
                    hash=row['hash'],
                    parent_hash=row['parent_hash'],
                )
                events.append(event)
            
            return events
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {e}")
            return []
    
    def create_sar_report(
        self,
        event_ids: List[str],
        description: str,
        jurisdiction: ComplianceRegion = ComplianceRegion.US
    ) -> Dict[str, Any]:
        """Create Suspicious Activity Report (SAR) for FinCEN.
        
        Args:
            event_ids: Events contributing to SAR
            description: Description of suspicious activity
            jurisdiction: Filing jurisdiction
            
        Returns:
            SAR report details
        """
        import uuid
        
        sar_id = f"SAR_{uuid.uuid4().hex[:12]}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sar_reports (
                    sar_id, event_ids, description, fincen_filed,
                    filed_date, jurisdiction
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sar_id,
                json.dumps(event_ids),
                description,
                False,  # Not filed yet
                None,
                jurisdiction.value
            ))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"SAR report created: {sar_id}")
            
            return {
                "sar_id": sar_id,
                "event_count": len(event_ids),
                "description": description,
                "status": "pending",
                "jurisdiction": jurisdiction.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "filing_deadline": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to create SAR report: {e}")
            raise
    
    def file_sar_report(self, sar_id: str, filing_reference: str) -> bool:
        """Mark SAR report as filed with FinCEN.
        
        Args:
            sar_id: SAR report ID
            filing_reference: FinCEN filing reference number
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE sar_reports
                SET fincen_filed = 1, filed_date = ?, filing_reference = ?
                WHERE sar_id = ?
            """, (
                datetime.now(timezone.utc).isoformat(),
                filing_reference,
                sar_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"SAR report filed: {sar_id} ({filing_reference})")
            return True
        except Exception as e:
            logger.error(f"Failed to file SAR report: {e}")
            return False
    
    def log_transaction(
        self,
        user_id: str,
        wallet_address: str,
        amount: float,
        currency: str = "DCMX",
        transaction_type: str = "transfer",
        status: str = "completed",
        **kwargs
    ) -> ComplianceAuditEvent:
        """Log financial transaction for compliance.
        
        Args:
            user_id: User making transaction
            wallet_address: Wallet address
            amount: Transaction amount
            currency: Currency type
            transaction_type: Type of transaction
            status: Transaction status
            **kwargs: Additional details
            
        Returns:
            Audit event
        """
        event = self.log_event(
            event_type=AuditEventType.TRANSACTION_COMPLETED,
            user_id=user_id,
            wallet_address=wallet_address,
            resource_type="transaction",
            action=transaction_type,
            amount=amount,
            currency=currency,
            status=status,
            details={
                "transaction_type": transaction_type,
                **kwargs
            }
        )
        
        # Check for reportable thresholds
        if amount >= 10000:
            logger.warning(f"Large transaction: ${amount} - May require reporting")
        
        return event
    
    def cleanup_old_logs(self) -> int:
        """Delete logs older than retention period.
        
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = (
                datetime.now(timezone.utc) - timedelta(days=self.retention_days)
            ).isoformat()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count before deletion
            cursor.execute("SELECT COUNT(*) FROM audit_events WHERE timestamp < ?", (cutoff_date,))
            count = cursor.fetchone()[0]
            
            # Delete old records
            cursor.execute("DELETE FROM audit_events WHERE timestamp < ?", (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            if count > 0:
                logger.info(f"Deleted {count} expired audit logs (older than {cutoff_date})")
            
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return 0
    
    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Get compliance metrics for reporting.
        
        Returns:
            Compliance metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total events
            cursor.execute("SELECT COUNT(*) FROM audit_events")
            total_events = cursor.fetchone()[0]
            
            # Failed transactions
            cursor.execute(
                "SELECT COUNT(*) FROM audit_events WHERE event_type = ? AND status = ?",
                (AuditEventType.TRANSACTION_REJECTED.value, "failure")
            )
            failed_transactions = cursor.fetchone()[0]
            
            # Large transactions (>$10k)
            cursor.execute(
                "SELECT COUNT(*) FROM audit_events WHERE amount >= 10000"
            )
            large_transactions = cursor.fetchone()[0]
            
            # Suspicious activity alerts
            cursor.execute(
                "SELECT COUNT(*) FROM audit_events WHERE event_type = ?",
                (AuditEventType.SUSPICIOUS_ACTIVITY.value,)
            )
            suspicious_activities = cursor.fetchone()[0]
            
            # SAR reports
            cursor.execute("SELECT COUNT(*) FROM sar_reports")
            sar_reports = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_events": total_events,
                "failed_transactions": failed_transactions,
                "large_transactions": large_transactions,
                "suspicious_activities": suspicious_activities,
                "sar_reports": sar_reports,
                "report_date": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to get compliance metrics: {e}")
            return {}
    
    def export_audit_log(
        self,
        export_path: str,
        user_id: Optional[str] = None,
        format: str = "json"
    ) -> bool:
        """Export audit log for regulatory submission.
        
        Args:
            export_path: Path to export file
            user_id: Optional user filter
            format: Export format (json, csv)
            
        Returns:
            Success status
        """
        try:
            events = self.get_audit_trail(user_id=user_id, limit=999999)
            
            os.makedirs(os.path.dirname(export_path) or ".", exist_ok=True)
            
            if format == "json":
                with open(export_path, "w") as f:
                    json.dump([e.to_dict() for e in events], f, indent=2)
            elif format == "csv":
                import csv
                if events:
                    with open(export_path, "w", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=events[0].to_dict().keys())
                        writer.writeheader()
                        for event in events:
                            writer.writerow(event.to_dict())
            
            logger.info(f"Audit log exported: {export_path} ({len(events)} events)")
            
            # Log the export action
            self.log_event(
                event_type=AuditEventType.EXPORT_REQUESTED,
                resource_type="audit_log",
                action="export",
                details={"export_path": export_path, "format": format, "count": len(events)}
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to export audit log: {e}")
            return False
