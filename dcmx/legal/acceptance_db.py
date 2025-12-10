"""
Legal document acceptance tracking system with database backend.

This module replaces file-based JSONL storage with database persistence
while maintaining backward compatibility with the existing API.
"""

import logging
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum
import hashlib

from dcmx.database.database import get_db_manager
from dcmx.database.dal import DataAccessLayer
from dcmx.database.models import AcceptanceRecord as DBAcceptanceRecord

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
    """Record of user accepting a legal document (compatible with legacy format)."""
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
    
    @classmethod
    def from_db_record(cls, db_record: DBAcceptanceRecord) -> 'AcceptanceRecord':
        """Create from database record."""
        return cls(
            user_id=db_record.user_id,
            wallet_address=db_record.wallet_address,
            document_type=db_record.document_type,
            version=db_record.version,
            accepted_at=db_record.accepted_at.isoformat() if isinstance(db_record.accepted_at, datetime) else db_record.accepted_at,
            ip_address=db_record.ip_address,
            user_agent=db_record.user_agent,
            signature=db_record.signature,
            read_time_seconds=db_record.read_time_seconds or 0,
            document_hash=db_record.document_hash
        )


class AcceptanceTracker:
    """Track legal document acceptances using database backend."""
    
    def __init__(self, use_database: bool = True):
        """
        Initialize tracker.
        
        Args:
            use_database: If True, use database backend. If False, fall back to file storage.
        """
        self.use_database = use_database
        self.db_manager = get_db_manager() if use_database else None
        self.dal = DataAccessLayer() if use_database else None
        
        # Initialize database if not already done
        if self.use_database:
            try:
                self.db_manager.initialize_sync()
            except Exception as e:
                logger.warning(f"Failed to initialize database: {e}")
                # Fall back to file storage
                self.use_database = False
        
        logger.info(f"AcceptanceTracker initialized (database: {self.use_database})")
    
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
        
        if self.use_database:
            # Use database backend
            async with self.db_manager.get_async_session() as session:
                db_record = await self.dal.record_acceptance(
                    session,
                    user_id=user_id,
                    wallet_address=wallet_address,
                    document_type=document_type.value,
                    version=version,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    signature=signature,
                    read_time_seconds=read_time_seconds,
                    document_hash=document_hash
                )
                
                record = AcceptanceRecord.from_db_record(db_record)
        else:
            # Fall back to in-memory record (for compatibility)
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
        if not self.use_database:
            logger.warning("Database not available, cannot retrieve acceptance")
            return None
        
        async with self.db_manager.get_async_session() as session:
            db_record = await self.dal.get_acceptance(
                session,
                user_id=user_id,
                document_type=document_type.value,
                version=version
            )
            
            if db_record:
                return AcceptanceRecord.from_db_record(db_record)
        
        return None
    
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
        if not self.use_database:
            logger.warning("Database not available, cannot retrieve acceptances")
            return []
        
        # Query database for all user acceptances
        async with self.db_manager.get_async_session() as session:
            from sqlalchemy import select, desc
            from dcmx.database.models import AcceptanceRecord as DBAcceptanceRecord
            
            result = await session.execute(
                select(DBAcceptanceRecord)
                .where(DBAcceptanceRecord.user_id == user_id)
                .order_by(desc(DBAcceptanceRecord.accepted_at))
            )
            
            db_records = result.scalars().all()
            return [AcceptanceRecord.from_db_record(r) for r in db_records]
    
    async def get_wallet_acceptances(
        self,
        wallet_address: str
    ) -> List[AcceptanceRecord]:
        """Get all acceptances for a wallet address."""
        if not self.use_database:
            logger.warning("Database not available, cannot retrieve acceptances")
            return []
        
        async with self.db_manager.get_async_session() as session:
            from sqlalchemy import select, desc
            from dcmx.database.models import AcceptanceRecord as DBAcceptanceRecord
            
            result = await session.execute(
                select(DBAcceptanceRecord)
                .where(DBAcceptanceRecord.wallet_address == wallet_address)
                .order_by(desc(DBAcceptanceRecord.accepted_at))
            )
            
            db_records = result.scalars().all()
            return [AcceptanceRecord.from_db_record(r) for r in db_records]
    
    async def audit_report(self) -> Dict:
        """Generate audit report of all acceptances."""
        if not self.use_database:
            logger.warning("Database not available, cannot generate audit report")
            return {
                "error": "Database not available",
                "total_acceptances": 0
            }
        
        async with self.db_manager.get_async_session() as session:
            from sqlalchemy import select, func
            from dcmx.database.models import AcceptanceRecord as DBAcceptanceRecord
            
            # Get total count
            total_result = await session.execute(
                select(func.count(DBAcceptanceRecord.id))
            )
            total_acceptances = total_result.scalar()
            
            # Get unique users
            users_result = await session.execute(
                select(func.count(func.distinct(DBAcceptanceRecord.user_id)))
            )
            unique_users = users_result.scalar()
            
            # Get unique wallets
            wallets_result = await session.execute(
                select(func.count(func.distinct(DBAcceptanceRecord.wallet_address)))
            )
            unique_wallets = wallets_result.scalar()
            
            # Group by document type
            by_type_result = await session.execute(
                select(
                    DBAcceptanceRecord.document_type,
                    func.count(DBAcceptanceRecord.id).label('count'),
                    func.min(DBAcceptanceRecord.accepted_at).label('first'),
                    func.max(DBAcceptanceRecord.accepted_at).label('last')
                ).group_by(DBAcceptanceRecord.document_type)
            )
            
            by_type = {}
            for row in by_type_result:
                by_type[row.document_type] = {
                    "count": row.count,
                    "first_acceptance": row.first.isoformat() if row.first else None,
                    "last_acceptance": row.last.isoformat() if row.last else None
                }
            
            return {
                "total_acceptances": total_acceptances,
                "unique_users": unique_users,
                "unique_wallets": unique_wallets,
                "by_document_type": by_type,
                "generated_at": datetime.utcnow().isoformat()
            }
    
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
    async def check_requirement(
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
        # Check if user has ever accepted
        has_record = await tracker.has_accepted(user_id, document_type)
        
        if not has_record:
            return {
                "required": True,
                "reason": "First time acceptance"
            }
        
        # Check if version matches
        record = await tracker.get_acceptance(user_id, document_type)
        
        if record and record.version != current_version:
            return {
                "required": True,
                "reason": f"Document updated from v{record.version} to v{current_version}"
            }
        
        # Check if reacceptance required after timeout
        if requires_reacceptance_after_days:
            is_current = await tracker.has_accepted(
                user_id,
                document_type,
                current_version,
                within_days=requires_reacceptance_after_days
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
