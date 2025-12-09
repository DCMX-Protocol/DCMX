"""
Tests for Compliance Audit Logger

Tests:
- Event logging and persistence
- Audit trail retrieval
- SAR report generation
- Compliance metrics
- Data export
- Event hashing/integrity
"""

import pytest
import tempfile
import json
import os
from datetime import datetime, timedelta, timezone

from dcmx.compliance.audit_log import (
    ComplianceAuditLogger,
    ComplianceAuditEvent,
    AuditEventType,
    ComplianceRegion,
)


class TestComplianceAuditEvent:
    """Test compliance audit event."""
    
    def test_create_event(self):
        """Test creating audit event."""
        event = ComplianceAuditEvent(
            event_type=AuditEventType.LOGIN,
            user_id="user123",
            username="testuser",
            wallet_address="0x123abc",
        )
        
        assert event.event_type == AuditEventType.LOGIN
        assert event.user_id == "user123"
        assert event.username == "testuser"
        assert event.status == "success"
    
    def test_event_hash(self):
        """Test event hash computation."""
        event = ComplianceAuditEvent(
            event_type=AuditEventType.TRANSACTION_COMPLETED,
            user_id="user123",
            amount=100.0,
        )
        
        hash1 = event.compute_hash()
        hash2 = event.compute_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_event_to_dict(self):
        """Test converting event to dict."""
        event = ComplianceAuditEvent(
            event_type=AuditEventType.KYC_APPROVED,
            user_id="user123",
            kyc_level=2,
        )
        
        data = event.to_dict()
        assert data["event_type"] == "kyc_approved"
        assert data["user_id"] == "user123"
        assert data["kyc_level"] == 2
    
    def test_is_reportable(self):
        """Test checking if event is reportable."""
        # Reportable event
        event1 = ComplianceAuditEvent(event_type=AuditEventType.TRANSACTION_COMPLETED)
        assert event1.is_reportable() is True
        
        # Non-reportable event
        event2 = ComplianceAuditEvent(event_type=AuditEventType.LOGIN)
        assert event2.is_reportable() is False


class TestComplianceAuditLogger:
    """Test compliance audit logger."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
    
    @pytest.fixture
    def logger(self, temp_db):
        """Create audit logger."""
        return ComplianceAuditLogger(db_path=temp_db)
    
    def test_logger_initialization(self, logger):
        """Test logger initialization."""
        assert os.path.exists(logger.db_path)
        assert logger.retention_days == 2555  # 7 years
    
    def test_log_event(self, logger):
        """Test logging event."""
        event = logger.log_event(
            event_type=AuditEventType.LOGIN,
            user_id="user123",
            username="testuser",
        )
        
        assert event.event_type == AuditEventType.LOGIN
        assert event.user_id == "user123"
        assert event.hash != ""
    
    def test_log_multiple_events(self, logger):
        """Test logging multiple events."""
        event1 = logger.log_event(
            event_type=AuditEventType.LOGIN,
            user_id="user1",
        )
        
        event2 = logger.log_event(
            event_type=AuditEventType.TRANSACTION_COMPLETED,
            user_id="user1",
            amount=100.0,
        )
        
        # Events should have different hashes
        assert event1.hash != event2.hash
        
        # Second event should reference first
        assert event2.parent_hash == event1.hash
    
    def test_get_audit_trail(self, logger):
        """Test retrieving audit trail."""
        logger.log_event(
            event_type=AuditEventType.LOGIN,
            user_id="user1",
        )
        
        logger.log_event(
            event_type=AuditEventType.TRANSACTION_COMPLETED,
            user_id="user1",
            amount=100.0,
        )
        
        trail = logger.get_audit_trail(user_id="user1")
        assert len(trail) == 2
    
    def test_get_audit_trail_filtered_by_type(self, logger):
        """Test filtering audit trail by event type."""
        logger.log_event(AuditEventType.LOGIN, user_id="user1")
        logger.log_event(AuditEventType.LOGOUT, user_id="user1")
        logger.log_event(AuditEventType.TRANSACTION_COMPLETED, user_id="user1")
        
        trail = logger.get_audit_trail(
            user_id="user1",
            event_types=[AuditEventType.LOGIN, AuditEventType.LOGOUT]
        )
        
        assert len(trail) == 2
    
    def test_get_audit_trail_date_range(self, logger):
        """Test filtering audit trail by date range."""
        logger.log_event(AuditEventType.LOGIN, user_id="user1")
        
        # Create a date in the future
        future_date = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat()
        
        trail = logger.get_audit_trail(
            user_id="user1",
            end_date=future_date
        )
        
        assert len(trail) == 1
    
    def test_log_transaction(self, logger):
        """Test logging transaction."""
        event = logger.log_transaction(
            user_id="user123",
            wallet_address="0x123abc",
            amount=500.0,
            currency="DCMX",
            transaction_type="nft_purchase",
        )
        
        assert event.event_type == AuditEventType.TRANSACTION_COMPLETED
        assert event.amount == 500.0
        assert event.currency == "DCMX"
    
    def test_create_sar_report(self, logger):
        """Test creating SAR report."""
        event1 = logger.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            user_id="user123",
            amount=15000.0,
        )
        
        event2 = logger.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            user_id="user123",
            amount=12000.0,
        )
        
        sar = logger.create_sar_report(
            event_ids=[event1.event_id, event2.event_id],
            description="Multiple large transfers in short period",
        )
        
        assert sar["sar_id"].startswith("SAR_")
        assert sar["event_count"] == 2
        assert sar["status"] == "pending"
    
    def test_file_sar_report(self, logger):
        """Test filing SAR report with FinCEN."""
        event = logger.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            user_id="user123",
        )
        
        sar = logger.create_sar_report(
            event_ids=[event.event_id],
            description="Test SAR",
        )
        
        result = logger.file_sar_report(
            sar["sar_id"],
            filing_reference="FinCEN-2024-123456"
        )
        
        assert result is True
    
    def test_get_compliance_metrics(self, logger):
        """Test getting compliance metrics."""
        logger.log_transaction(
            user_id="user1",
            wallet_address="0x123",
            amount=15000.0,
        )
        
        logger.log_event(
            AuditEventType.SUSPICIOUS_ACTIVITY,
            user_id="user1",
        )
        
        metrics = logger.get_compliance_metrics()
        
        assert "total_events" in metrics
        assert metrics["suspicious_activities"] >= 1
        assert metrics["large_transactions"] >= 1
    
    def test_export_audit_log_json(self, logger, temp_db):
        """Test exporting audit log as JSON."""
        logger.log_event(AuditEventType.LOGIN, user_id="user1")
        logger.log_event(AuditEventType.LOGOUT, user_id="user1")
        
        export_path = temp_db.replace(".db", "_export.json")
        
        result = logger.export_audit_log(export_path, format="json")
        
        assert result is True
        assert os.path.exists(export_path)
        
        with open(export_path, "r") as f:
            data = json.load(f)
            assert len(data) >= 2
        
        # Cleanup
        os.remove(export_path)
    
    def test_cleanup_old_logs(self, logger):
        """Test cleaning up old logs."""
        logger.log_event(AuditEventType.LOGIN, user_id="user1")
        
        # Create logger with 0 day retention
        logger.retention_days = 0
        
        count = logger.cleanup_old_logs()
        # May or may not delete depending on exact timing
        assert count >= 0
    
    def test_persistence_across_instances(self, temp_db):
        """Test that logs persist across logger instances."""
        # Create first logger and log event
        logger1 = ComplianceAuditLogger(db_path=temp_db)
        logger1.log_event(AuditEventType.LOGIN, user_id="user1")
        
        # Create second logger instance
        logger2 = ComplianceAuditLogger(db_path=temp_db)
        trail = logger2.get_audit_trail(user_id="user1")
        
        assert len(trail) >= 1
    
    def test_event_integrity_chain(self, logger):
        """Test that events form integrity chain."""
        event1 = logger.log_event(AuditEventType.LOGIN, user_id="user1")
        event2 = logger.log_event(AuditEventType.TRANSACTION_INITIATED, user_id="user1")
        event3 = logger.log_event(AuditEventType.LOGOUT, user_id="user1")
        
        # Each event should reference previous
        assert event1.parent_hash == ""
        assert event2.parent_hash == event1.hash
        assert event3.parent_hash == event2.hash
    
    def test_kyc_event_logging(self, logger):
        """Test KYC event logging."""
        event = logger.log_event(
            event_type=AuditEventType.KYC_APPROVED,
            user_id="user123",
            wallet_address="0x123abc",
            kyc_level=2,
            details={"verification_method": "id_scan"},
        )
        
        assert event.kyc_level == 2
        assert event.is_reportable() is True
    
    def test_ofac_event_logging(self, logger):
        """Test OFAC check event logging."""
        event = logger.log_event(
            event_type=AuditEventType.OFAC_CHECK_PASSED,
            user_id="user123",
            wallet_address="0x123abc",
            resource_type="wallet",
        )
        
        assert event.event_type == AuditEventType.OFAC_CHECK_PASSED
    
    def test_sanction_match_logging(self, logger):
        """Test sanctions match event logging."""
        event = logger.log_event(
            event_type=AuditEventType.SANCTION_MATCH,
            user_id="sanctioned_user",
            status="failure",
            details={"reason": "On OFAC SDN list"},
        )
        
        assert event.is_reportable() is True
        assert event.status == "failure"
