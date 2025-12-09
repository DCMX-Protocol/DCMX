"""Legal document acceptance tracking system."""

import logging
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of legal documents."""
    TERMS_AND_CONDITIONS = "terms_and_conditions"
    PRIVACY_POLICY = "privacy_policy"
    COOKIE_POLICY = "cookie_policy"
    NFT_AGREEMENT = "nft_agreement"
    RISK_DISCLOSURE = "risk_disclosure"


@dataclass
class AcceptanceRecord:
    """Record of user accepting a legal document."""
    user_id: str
    wallet_address: str
    document_type: str
    version: str
    accepted_at: str  # ISO format datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    signature: Optional[str] = None  # Optional blockchain signature proof
    read_time_seconds: int = 0
    document_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AcceptanceRecord':
        """Create from dictionary."""
        return cls(**data)


class AcceptanceTracker:
    """Track legal document acceptances."""
    
    def __init__(self, storage_path: str = None):
        """
        Initialize tracker.
        
        Args:
            storage_path: Path to store acceptance records
                Default: /var/lib/dcmx/compliance (production)
                        ~/.dcmx/compliance (development)
                Can be overridden via DCMX_COMPLIANCE_PATH env var
        """
        import os
        
        if storage_path is None:
            # Use environment variable if set
            storage_path = os.getenv('DCMX_COMPLIANCE_PATH')
            
            if storage_path is None:
                # Auto-detect: use /var/lib in production, ~/.dcmx in dev
                if os.path.exists('/var/lib/dcmx'):
                    storage_path = '/var/lib/dcmx/compliance'
                else:
                    storage_path = os.path.expanduser('~/.dcmx/compliance')
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.acceptance_file = self.storage_path / "acceptances.jsonl"
        self.immutable_log = self.storage_path / "acceptance.log"
        
        # Ensure files exist
        self.acceptance_file.touch(exist_ok=True)
        self.immutable_log.touch(exist_ok=True)
    
    async def record_acceptance(
        self,
        user_id: str,
        wallet_address: str,
        document_type: DocumentType,
        version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        signature: Optional[str] = None,
        read_time_seconds: int = 0,
        document_content: Optional[str] = None
    ) -> AcceptanceRecord:
        """
        Record that a user accepted a legal document.
        
        Args:
            user_id: Unique user identifier
            wallet_address: Ethereum wallet address
            document_type: Type of document
            version: Document version
            ip_address: User's IP address
            user_agent: Browser user agent
            signature: Optional blockchain signature for non-repudiation
            read_time_seconds: How long user spent reading
            document_content: Optional full document text for hashing
        
        Returns:
            AcceptanceRecord that was saved
        """
        # Calculate document hash for integrity
        document_hash = None
        if document_content:
            document_hash = hashlib.sha256(
                document_content.encode()
            ).hexdigest()
        
        record = AcceptanceRecord(
            user_id=user_id,
            wallet_address=wallet_address,
            document_type=document_type.value,
            version=version,
            accepted_at=datetime.utcnow().isoformat(),
            ip_address=ip_address,
            user_agent=user_agent,
            signature=signature,
            read_time_seconds=read_time_seconds,
            document_hash=document_hash
        )
        
        # Write to JSONL file (append-only for immutability)
        with open(self.acceptance_file, 'a') as f:
            f.write(json.dumps(record.to_dict()) + '\n')
        
        # Write to immutable log
        log_entry = (
            f"{record.accepted_at} | {user_id} | {wallet_address} | "
            f"{document_type.value} | v{version} | {ip_address}\n"
        )
        with open(self.immutable_log, 'a') as f:
            f.write(log_entry)
        
        logger.info(
            f"Acceptance recorded: {user_id} accepted {document_type.value} v{version}"
        )
        
        return record
    
    async def get_acceptance(
        self,
        user_id: str,
        document_type: DocumentType,
        version: Optional[str] = None
    ) -> Optional[AcceptanceRecord]:
        """
        Get most recent acceptance for a document.
        
        Args:
            user_id: User identifier
            document_type: Type of document
            version: Specific version (None = any version)
        
        Returns:
            AcceptanceRecord if found, None otherwise
        """
        matching_records = []
        
        try:
            with open(self.acceptance_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    record = AcceptanceRecord.from_dict(data)
                    
                    if record.user_id == user_id and \
                       record.document_type == document_type.value:
                        if version is None or record.version == version:
                            matching_records.append(record)
        except FileNotFoundError:
            return None
        
        if not matching_records:
            return None
        
        # Return most recent
        return max(matching_records, key=lambda r: r.accepted_at)
    
    async def has_accepted(
        self,
        user_id: str,
        document_type: DocumentType,
        required_version: Optional[str] = None,
        within_days: Optional[int] = None
    ) -> bool:
        """
        Check if user has accepted a document.
        
        Args:
            user_id: User identifier
            document_type: Type of document
            required_version: If specified, must match this version
            within_days: If specified, acceptance must be recent
        
        Returns:
            True if accepted per criteria
        """
        record = await self.get_acceptance(user_id, document_type, required_version)
        
        if not record:
            return False
        
        if within_days:
            accepted_time = datetime.fromisoformat(record.accepted_at)
            now = datetime.utcnow()
            if (now - accepted_time).days > within_days:
                return False
        
        return True
    
    async def get_user_acceptances(
        self,
        user_id: str
    ) -> List[AcceptanceRecord]:
        """Get all acceptances for a user."""
        records = []
        
        try:
            with open(self.acceptance_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    record = AcceptanceRecord.from_dict(data)
                    
                    if record.user_id == user_id:
                        records.append(record)
        except FileNotFoundError:
            pass
        
        # Sort by date, most recent first
        return sorted(records, key=lambda r: r.accepted_at, reverse=True)
    
    async def get_wallet_acceptances(
        self,
        wallet_address: str
    ) -> List[AcceptanceRecord]:
        """Get all acceptances for a wallet address."""
        records = []
        
        try:
            with open(self.acceptance_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    record = AcceptanceRecord.from_dict(data)
                    
                    if record.wallet_address.lower() == wallet_address.lower():
                        records.append(record)
        except FileNotFoundError:
            pass
        
        return sorted(records, key=lambda r: r.accepted_at, reverse=True)
    
    async def audit_report(self) -> Dict:
        """Generate audit report of all acceptances."""
        all_records = []
        
        try:
            with open(self.acceptance_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    record = AcceptanceRecord.from_dict(data)
                    all_records.append(record)
        except FileNotFoundError:
            pass
        
        # Group by document type
        by_type = {}
        for record in all_records:
            doc_type = record.document_type
            if doc_type not in by_type:
                by_type[doc_type] = []
            by_type[doc_type].append(record)
        
        # Calculate statistics
        stats = {
            "total_acceptances": len(all_records),
            "unique_users": len(set(r.user_id for r in all_records)),
            "unique_wallets": len(set(r.wallet_address.lower() for r in all_records)),
            "by_document_type": {
                doc_type: {
                    "count": len(records),
                    "first_acceptance": min(records, key=lambda r: r.accepted_at).accepted_at,
                    "last_acceptance": max(records, key=lambda r: r.accepted_at).accepted_at,
                }
                for doc_type, records in by_type.items()
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return stats
    
    async def export_acceptances(
        self,
        output_path: str,
        format: str = "json"
    ) -> None:
        """
        Export acceptance records.
        
        Args:
            output_path: Path to export file
            format: 'json' or 'csv'
        """
        all_records = []
        
        try:
            with open(self.acceptance_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    all_records.append(data)
        except FileNotFoundError:
            logger.warning("No acceptance records found")
            return
        
        output_path = Path(output_path)
        
        if format == "json":
            with open(output_path, 'w') as f:
                json.dump(all_records, f, indent=2)
        
        elif format == "csv":
            import csv
            
            if not all_records:
                return
            
            keys = all_records[0].keys()
            
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(all_records)
        
        logger.info(f"Exported {len(all_records)} records to {output_path}")
    
    async def verify_acceptance(
        self,
        user_id: str,
        document_type: DocumentType,
        expected_hash: str
    ) -> bool:
        """
        Verify that document content hasn't changed since user accepted.
        
        Args:
            user_id: User identifier
            document_type: Type of document
            expected_hash: Current SHA256 hash of document
        
        Returns:
            True if document matches what user accepted
        """
        record = await self.get_acceptance(user_id, document_type)
        
        if not record:
            return False
        
        if record.document_hash is None:
            # No hash stored for this record, cannot verify
            logger.warning(f"No hash stored for acceptance: {user_id} - {document_type.value}")
            return True  # Assume valid if no hash to check against
        
        if record.document_hash != expected_hash:
            logger.warning(
                f"Document hash mismatch for {user_id} - {document_type.value}. "
                f"Document may have been modified since acceptance."
            )
            return False
        
        return True


class AcceptanceRequirement:
    """Check if user must accept/reaccept a document."""
    
    @staticmethod
    def check_requirement(
        tracker: AcceptanceTracker,
        user_id: str,
        document_type: DocumentType,
        current_version: str,
        requires_reacceptance_after_days: Optional[int] = None
    ) -> Dict:
        """
        Check if user must accept/reaccept document.
        
        Returns:
            Dict with 'required' bool and optional 'reason' string
        """
        import asyncio
        
        # Check if user has ever accepted
        has_record = asyncio.run(
            tracker.has_accepted(user_id, document_type)
        )
        
        if not has_record:
            return {
                "required": True,
                "reason": "First time acceptance"
            }
        
        # Check if version matches
        record = asyncio.run(
            tracker.get_acceptance(user_id, document_type)
        )
        
        if record.version != current_version:
            return {
                "required": True,
                "reason": f"Document updated from v{record.version} to v{current_version}"
            }
        
        # Check if reacceptance required after timeout
        if requires_reacceptance_after_days:
            is_current = asyncio.run(
                tracker.has_accepted(
                    user_id,
                    document_type,
                    current_version,
                    within_days=requires_reacceptance_after_days
                )
            )
            
            if not is_current:
                return {
                    "required": True,
                    "reason": f"Acceptance required every {requires_reacceptance_after_days} days"
                }
        
        return {
            "required": False,
            "reason": "User has accepted current version"
        }
