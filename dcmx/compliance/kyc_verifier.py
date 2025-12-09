"""KYC (Know Your Customer) verification for DCMX compliance."""

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class KYCLevel(Enum):
    """KYC verification levels."""
    UNVERIFIED = 0
    BASIC = 1        # Email verification only
    STANDARD = 2     # ID + address verification
    ENHANCED = 3     # Full verification + source of funds


class VerificationStatus(Enum):
    """Status of a verification step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REQUIRES_REVIEW = "requires_review"


class DocumentType(Enum):
    """Accepted identity document types."""
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    RESIDENCE_PERMIT = "residence_permit"


class RiskLevel(Enum):
    """User risk classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DocumentVerification:
    """Result of document verification."""
    document_type: DocumentType
    document_number: str
    issuing_country: str
    expiry_date: Optional[str] = None
    verified: bool = False
    confidence_score: float = 0.0
    verification_timestamp: Optional[str] = None
    rejection_reason: Optional[str] = None


@dataclass
class AddressVerification:
    """Result of address verification."""
    address_line1: str
    address_line2: Optional[str] = None
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""
    verified: bool = False
    verification_method: str = ""  # utility_bill, bank_statement, etc.
    verification_timestamp: Optional[str] = None


@dataclass
class BiometricVerification:
    """Result of biometric/liveness verification."""
    liveness_check_passed: bool = False
    face_match_score: float = 0.0
    face_match_passed: bool = False
    verification_timestamp: Optional[str] = None
    provider_reference: Optional[str] = None


@dataclass
class RiskAssessment:
    """Risk scoring for a user."""
    overall_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    factors: Dict[str, float] = field(default_factory=dict)
    flags: List[str] = field(default_factory=list)
    assessment_timestamp: Optional[str] = None


@dataclass
class UserProfile:
    """User identity profile with KYC data."""
    user_id: str
    wallet_address: str
    email: Optional[str] = None
    email_verified: bool = False
    kyc_level: KYCLevel = KYCLevel.UNVERIFIED
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_timestamp: Optional[str] = None
    jurisdiction: str = "US"

    # PII (encrypted at rest)
    legal_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None

    # Verification results
    document_verification: Optional[DocumentVerification] = None
    address_verification: Optional[AddressVerification] = None
    biometric_verification: Optional[BiometricVerification] = None
    risk_assessment: Optional[RiskAssessment] = None

    # Enhanced verification (Level 3)
    source_of_funds: Optional[str] = None
    source_of_funds_verified: bool = False
    occupation: Optional[str] = None
    employer: Optional[str] = None

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None


class KYCProviderError(Exception):
    """Error from external KYC provider."""
    pass


class KYCVerifier:
    """
    Verifies customer identity for regulatory compliance.

    Supports three KYC levels:
    - Level 1 (Basic): Email verification
    - Level 2 (Standard): ID + address verification
    - Level 3 (Enhanced): Full verification + source of funds

    Features:
    - Document verification (ID validation)
    - Address verification
    - Biometric/liveness check (interface for external provider)
    - Risk scoring based on verification results
    - Encrypted storage of PII
    - Retry logic with exponential backoff
    """

    KYC_THRESHOLD_USD = 10_000  # $10K lifetime spend requires Level 2
    ENHANCED_THRESHOLD_USD = 50_000  # $50K requires Level 3

    DEFAULT_RETRY_ATTEMPTS = 3
    BASE_BACKOFF_SECONDS = 1.0
    MAX_BACKOFF_SECONDS = 30.0

    def __init__(
        self,
        kyc_provider_url: Optional[str] = None,
        encryption_key: Optional[str] = None,
        db_path: str = "kyc_data.db",
    ):
        """
        Initialize KYC verifier.

        Args:
            kyc_provider_url: Third-party KYC service URL (Stripe, Onfido, etc)
            encryption_key: Fernet encryption key for PII storage
            db_path: Path to SQLite database for KYC records
        """
        self.kyc_provider_url = kyc_provider_url
        self.db_path = db_path

        # Initialize encryption
        if encryption_key:
            self._fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
        else:
            key = os.getenv("KYC_ENCRYPTION_KEY")
            if key:
                self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
            else:
                self._fernet = Fernet(Fernet.generate_key())
                logger.warning("Using auto-generated encryption key. Set KYC_ENCRYPTION_KEY for persistence.")

        # In-memory cache
        self.verified_users: Dict[str, UserProfile] = {}

        # Initialize database
        self._init_database()

        logger.info("KYCVerifier initialized")

    def _init_database(self):
        """Initialize SQLite database for KYC records."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kyc_profiles (
                user_id TEXT PRIMARY KEY,
                wallet_address TEXT NOT NULL,
                email_encrypted TEXT,
                email_verified INTEGER DEFAULT 0,
                kyc_level INTEGER DEFAULT 0,
                verification_status TEXT DEFAULT 'pending',
                verification_timestamp TEXT,
                jurisdiction TEXT DEFAULT 'US',
                pii_encrypted TEXT,
                document_data_encrypted TEXT,
                address_data_encrypted TEXT,
                biometric_data_encrypted TEXT,
                risk_assessment TEXT,
                source_of_funds_encrypted TEXT,
                source_of_funds_verified INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                expires_at TEXT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wallet ON kyc_profiles(wallet_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kyc_level ON kyc_profiles(kyc_level)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON kyc_profiles(verification_status)")

        conn.commit()
        conn.close()
        logger.info(f"KYC database initialized: {self.db_path}")

    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self._fernet.encrypt(data.encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self._fernet.decrypt(encrypted_data.encode()).decode()

    async def _call_provider_with_retry(
        self,
        operation: str,
        payload: Dict[str, Any],
        max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
    ) -> Dict[str, Any]:
        """
        Call external KYC provider with exponential backoff retry.

        Args:
            operation: Operation name (for logging)
            payload: Request payload
            max_attempts: Maximum retry attempts

        Returns:
            Provider response

        Raises:
            KYCProviderError: If all retries fail
        """
        last_error = None

        for attempt in range(max_attempts):
            try:
                if self.kyc_provider_url:
                    # In production, make actual HTTP call here
                    # response = await aiohttp.ClientSession().post(...)
                    pass

                # Simulate provider response for now
                return await self._simulate_provider_call(operation, payload)

            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    backoff = min(
                        self.BASE_BACKOFF_SECONDS * (2 ** attempt),
                        self.MAX_BACKOFF_SECONDS
                    )
                    logger.warning(
                        f"KYC provider {operation} failed (attempt {attempt + 1}/{max_attempts}), "
                        f"retrying in {backoff:.1f}s: {e}"
                    )
                    await asyncio.sleep(backoff)

        raise KYCProviderError(f"KYC provider {operation} failed after {max_attempts} attempts: {last_error}")

    async def _simulate_provider_call(
        self,
        operation: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Simulate KYC provider response (replace with real API calls in production).
        """
        await asyncio.sleep(0.1)  # Simulate network latency

        if operation == "verify_document":
            return {
                "verified": True,
                "confidence_score": 0.95,
                "document_valid": True,
                "expiry_valid": True,
            }
        elif operation == "verify_address":
            return {
                "verified": True,
                "match_score": 0.92,
            }
        elif operation == "verify_biometric":
            return {
                "liveness_passed": True,
                "face_match_score": 0.97,
                "reference": f"bio_{uuid.uuid4().hex[:12]}",
            }
        elif operation == "check_sanctions":
            return {
                "is_sanctioned": False,
                "match_score": 0.0,
            }

        return {"success": True}

    async def verify_email(
        self,
        user_id: str,
        wallet_address: str,
        email: str,
    ) -> Dict[str, Any]:
        """
        Level 1: Basic email verification.

        Args:
            user_id: User identifier
            wallet_address: Blockchain wallet address
            email: Email address to verify

        Returns:
            Verification result
        """
        try:
            # Validate email format
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return {
                    "verified": False,
                    "level": KYCLevel.UNVERIFIED.value,
                    "message": "Invalid email format",
                }

            now = datetime.now(timezone.utc).isoformat()

            profile = UserProfile(
                user_id=user_id,
                wallet_address=wallet_address,
                email=email,
                email_verified=True,
                kyc_level=KYCLevel.BASIC,
                verification_status=VerificationStatus.APPROVED,
                verification_timestamp=now,
                created_at=now,
                updated_at=now,
            )

            # Store profile
            await self._store_profile(profile)
            self.verified_users[user_id] = profile

            logger.info(f"KYC Level 1 (Basic) verified for {user_id}")

            return {
                "verified": True,
                "level": KYCLevel.BASIC.value,
                "level_name": "Basic",
                "timestamp": now,
                "message": "Email verification completed",
            }

        except Exception as e:
            logger.error(f"Email verification failed for {user_id}: {e}")
            return {
                "verified": False,
                "level": KYCLevel.UNVERIFIED.value,
                "message": str(e),
            }

    async def verify_document(
        self,
        user_id: str,
        document_type: DocumentType,
        document_number: str,
        issuing_country: str,
        expiry_date: Optional[str] = None,
        document_image_front: Optional[bytes] = None,
        document_image_back: Optional[bytes] = None,
    ) -> DocumentVerification:
        """
        Verify identity document.

        Args:
            user_id: User identifier
            document_type: Type of document
            document_number: Document number
            issuing_country: Country that issued the document
            expiry_date: Document expiry date (YYYY-MM-DD)
            document_image_front: Front image of document
            document_image_back: Back image of document

        Returns:
            DocumentVerification result
        """
        try:
            # Call provider with retry
            result = await self._call_provider_with_retry(
                "verify_document",
                {
                    "document_type": document_type.value,
                    "document_number": document_number,
                    "issuing_country": issuing_country,
                    "expiry_date": expiry_date,
                },
            )

            now = datetime.now(timezone.utc).isoformat()

            verification = DocumentVerification(
                document_type=document_type,
                document_number=document_number,
                issuing_country=issuing_country,
                expiry_date=expiry_date,
                verified=result.get("verified", False),
                confidence_score=result.get("confidence_score", 0.0),
                verification_timestamp=now,
            )

            if not verification.verified:
                verification.rejection_reason = result.get("rejection_reason", "Document verification failed")

            logger.info(f"Document verification for {user_id}: {verification.verified}")
            return verification

        except KYCProviderError as e:
            logger.error(f"Document verification failed for {user_id}: {e}")
            return DocumentVerification(
                document_type=document_type,
                document_number=document_number,
                issuing_country=issuing_country,
                verified=False,
                rejection_reason=str(e),
            )

    async def verify_address(
        self,
        user_id: str,
        address_line1: str,
        city: str,
        postal_code: str,
        country: str,
        address_line2: Optional[str] = None,
        state: Optional[str] = None,
        verification_document: Optional[bytes] = None,
        verification_method: str = "utility_bill",
    ) -> AddressVerification:
        """
        Verify user's address.

        Args:
            user_id: User identifier
            address_line1: Primary address line
            city: City
            postal_code: Postal/ZIP code
            country: Country code
            address_line2: Secondary address line
            state: State/province
            verification_document: Proof of address document
            verification_method: Method used (utility_bill, bank_statement, etc.)

        Returns:
            AddressVerification result
        """
        try:
            result = await self._call_provider_with_retry(
                "verify_address",
                {
                    "address_line1": address_line1,
                    "address_line2": address_line2,
                    "city": city,
                    "state": state,
                    "postal_code": postal_code,
                    "country": country,
                },
            )

            now = datetime.now(timezone.utc).isoformat()

            verification = AddressVerification(
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state or "",
                postal_code=postal_code,
                country=country,
                verified=result.get("verified", False),
                verification_method=verification_method,
                verification_timestamp=now,
            )

            logger.info(f"Address verification for {user_id}: {verification.verified}")
            return verification

        except KYCProviderError as e:
            logger.error(f"Address verification failed for {user_id}: {e}")
            return AddressVerification(
                address_line1=address_line1,
                city=city,
                postal_code=postal_code,
                country=country,
                verified=False,
            )

    async def verify_biometric(
        self,
        user_id: str,
        selfie_image: Optional[bytes] = None,
        video_liveness: Optional[bytes] = None,
        document_face_image: Optional[bytes] = None,
    ) -> BiometricVerification:
        """
        Perform biometric/liveness verification.

        Args:
            user_id: User identifier
            selfie_image: User's selfie
            video_liveness: Video for liveness check
            document_face_image: Face from ID document

        Returns:
            BiometricVerification result
        """
        try:
            result = await self._call_provider_with_retry(
                "verify_biometric",
                {
                    "user_id": user_id,
                    "has_selfie": selfie_image is not None,
                    "has_video": video_liveness is not None,
                },
            )

            now = datetime.now(timezone.utc).isoformat()

            verification = BiometricVerification(
                liveness_check_passed=result.get("liveness_passed", False),
                face_match_score=result.get("face_match_score", 0.0),
                face_match_passed=result.get("face_match_score", 0.0) >= 0.85,
                verification_timestamp=now,
                provider_reference=result.get("reference"),
            )

            logger.info(f"Biometric verification for {user_id}: liveness={verification.liveness_check_passed}, face_match={verification.face_match_passed}")
            return verification

        except KYCProviderError as e:
            logger.error(f"Biometric verification failed for {user_id}: {e}")
            return BiometricVerification(
                liveness_check_passed=False,
                face_match_passed=False,
            )

    async def calculate_risk_score(
        self,
        user_id: str,
        profile: UserProfile,
    ) -> RiskAssessment:
        """
        Calculate risk score based on verification results.

        Args:
            user_id: User identifier
            profile: User's KYC profile

        Returns:
            RiskAssessment with overall score and factors
        """
        factors: Dict[str, float] = {}
        flags: List[str] = []
        base_score = 0.0

        # Email verification factor
        if profile.email_verified:
            factors["email_verified"] = 0.0
        else:
            factors["email_verified"] = 10.0
            base_score += 10.0
            flags.append("email_not_verified")

        # Document verification factor
        if profile.document_verification:
            if profile.document_verification.verified:
                factors["document_verified"] = 0.0
                if profile.document_verification.confidence_score < 0.9:
                    factors["document_confidence"] = 5.0
                    base_score += 5.0
            else:
                factors["document_verified"] = 20.0
                base_score += 20.0
                flags.append("document_not_verified")
        else:
            factors["document_verified"] = 15.0
            base_score += 15.0

        # Address verification factor
        if profile.address_verification:
            if profile.address_verification.verified:
                factors["address_verified"] = 0.0
            else:
                factors["address_verified"] = 15.0
                base_score += 15.0
                flags.append("address_not_verified")
        else:
            factors["address_verified"] = 10.0
            base_score += 10.0

        # Biometric verification factor
        if profile.biometric_verification:
            if profile.biometric_verification.liveness_check_passed and profile.biometric_verification.face_match_passed:
                factors["biometric_verified"] = 0.0
            else:
                factors["biometric_verified"] = 25.0
                base_score += 25.0
                flags.append("biometric_failed")
        else:
            factors["biometric_verified"] = 20.0
            base_score += 20.0

        # Source of funds factor (for enhanced verification)
        if profile.kyc_level == KYCLevel.ENHANCED:
            if profile.source_of_funds_verified:
                factors["source_of_funds"] = 0.0
            else:
                factors["source_of_funds"] = 30.0
                base_score += 30.0
                flags.append("source_of_funds_not_verified")

        # Jurisdiction risk
        high_risk_jurisdictions = {"IR", "KP", "CU", "SY", "RU", "BY"}
        if profile.jurisdiction in high_risk_jurisdictions:
            factors["jurisdiction_risk"] = 50.0
            base_score += 50.0
            flags.append(f"high_risk_jurisdiction_{profile.jurisdiction}")

        # Determine risk level
        if base_score >= 70:
            risk_level = RiskLevel.CRITICAL
        elif base_score >= 50:
            risk_level = RiskLevel.HIGH
        elif base_score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        assessment = RiskAssessment(
            overall_score=min(base_score, 100.0),
            risk_level=risk_level,
            factors=factors,
            flags=flags,
            assessment_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(f"Risk assessment for {user_id}: score={assessment.overall_score}, level={risk_level.value}")
        return assessment

    async def verify_user(
        self,
        user_id: str,
        wallet_address: str,
        legal_name: str,
        date_of_birth: str,
        address: str,
        country: str = "US",
        email: Optional[str] = None,
        document_type: Optional[DocumentType] = None,
        document_number: Optional[str] = None,
        document_expiry: Optional[str] = None,
        source_of_funds: Optional[str] = None,
        target_level: KYCLevel = KYCLevel.STANDARD,
    ) -> Dict[str, Any]:
        """
        Full KYC verification flow.

        Args:
            user_id: User identifier
            wallet_address: Blockchain wallet address
            legal_name: Full legal name
            date_of_birth: DOB (YYYY-MM-DD)
            address: Physical address
            country: Country of residence
            email: Email address (required for Level 1+)
            document_type: Type of ID document (required for Level 2+)
            document_number: ID document number (required for Level 2+)
            document_expiry: Document expiry date
            source_of_funds: Source of funds declaration (required for Level 3)
            target_level: Target KYC level

        Returns:
            Verification result with level, status, and details
        """
        try:
            now = datetime.now(timezone.utc).isoformat()

            # Check if user already exists
            existing = await self.get_profile(user_id)
            if existing and existing.kyc_level.value >= target_level.value:
                return {
                    "verified": True,
                    "level": existing.kyc_level.value,
                    "level_name": existing.kyc_level.name,
                    "timestamp": existing.verification_timestamp,
                    "message": f"Already verified at {existing.kyc_level.name} level",
                }

            # Parse address components
            address_parts = address.split(",")
            address_line1 = address_parts[0].strip() if address_parts else address
            city = address_parts[1].strip() if len(address_parts) > 1 else ""
            state = address_parts[2].strip() if len(address_parts) > 2 else ""
            postal_code = address_parts[3].strip() if len(address_parts) > 3 else ""

            # Initialize profile
            profile = UserProfile(
                user_id=user_id,
                wallet_address=wallet_address,
                email=email,
                legal_name=legal_name,
                date_of_birth=date_of_birth,
                jurisdiction=country,
                created_at=now,
                updated_at=now,
            )

            achieved_level = KYCLevel.UNVERIFIED

            # Level 1: Email verification
            if email and target_level.value >= KYCLevel.BASIC.value:
                email_result = await self.verify_email(user_id, wallet_address, email)
                if email_result.get("verified"):
                    profile.email_verified = True
                    achieved_level = KYCLevel.BASIC

            # Level 2: Document + Address verification
            if target_level.value >= KYCLevel.STANDARD.value:
                # Document verification
                if document_type and document_number:
                    doc_result = await self.verify_document(
                        user_id=user_id,
                        document_type=document_type,
                        document_number=document_number,
                        issuing_country=country,
                        expiry_date=document_expiry,
                    )
                    profile.document_verification = doc_result

                # Address verification
                addr_result = await self.verify_address(
                    user_id=user_id,
                    address_line1=address_line1,
                    city=city,
                    postal_code=postal_code,
                    country=country,
                    state=state,
                )
                profile.address_verification = addr_result

                # Biometric verification
                bio_result = await self.verify_biometric(user_id=user_id)
                profile.biometric_verification = bio_result

                # Check if Level 2 achieved
                if (profile.document_verification and profile.document_verification.verified and
                    profile.address_verification.verified and
                    profile.biometric_verification.liveness_check_passed):
                    achieved_level = KYCLevel.STANDARD

            # Level 3: Enhanced verification
            if target_level.value >= KYCLevel.ENHANCED.value and achieved_level == KYCLevel.STANDARD:
                if source_of_funds:
                    profile.source_of_funds = source_of_funds
                    # In production, this would involve manual review or additional checks
                    profile.source_of_funds_verified = True
                    achieved_level = KYCLevel.ENHANCED
                else:
                    logger.warning(f"Source of funds required for Enhanced verification: {user_id}")

            # Calculate risk score
            profile.risk_assessment = await self.calculate_risk_score(user_id, profile)

            # Determine final status
            if achieved_level == target_level:
                profile.verification_status = VerificationStatus.APPROVED
            elif achieved_level.value > KYCLevel.UNVERIFIED.value:
                profile.verification_status = VerificationStatus.APPROVED
            elif profile.risk_assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                profile.verification_status = VerificationStatus.REQUIRES_REVIEW
            else:
                profile.verification_status = VerificationStatus.REJECTED

            profile.kyc_level = achieved_level
            profile.verification_timestamp = now
            profile.updated_at = now

            # Store profile
            await self._store_profile(profile)
            self.verified_users[user_id] = profile

            logger.info(f"KYC verification completed for {user_id}: level={achieved_level.name}, status={profile.verification_status.value}")

            return {
                "verified": profile.verification_status == VerificationStatus.APPROVED,
                "level": achieved_level.value,
                "level_name": achieved_level.name,
                "status": profile.verification_status.value,
                "timestamp": profile.verification_timestamp,
                "risk_score": profile.risk_assessment.overall_score,
                "risk_level": profile.risk_assessment.risk_level.value,
                "message": f"KYC verification completed at {achieved_level.name} level",
            }

        except Exception as e:
            logger.error(f"KYC verification failed for {user_id}: {e}")
            return {
                "verified": False,
                "level": KYCLevel.UNVERIFIED.value,
                "status": VerificationStatus.REJECTED.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": str(e),
            }

    async def _store_profile(self, profile: UserProfile) -> None:
        """Store user profile with encrypted PII."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Encrypt sensitive data
            pii_data = json.dumps({
                "legal_name": profile.legal_name,
                "date_of_birth": profile.date_of_birth,
                "nationality": profile.nationality,
                "occupation": profile.occupation,
                "employer": profile.employer,
            })
            pii_encrypted = self._encrypt(pii_data)

            email_encrypted = self._encrypt(profile.email) if profile.email else None

            document_data = None
            if profile.document_verification:
                doc_dict = asdict(profile.document_verification)
                doc_dict["document_type"] = profile.document_verification.document_type.value
                document_data = self._encrypt(json.dumps(doc_dict))

            address_data = None
            if profile.address_verification:
                address_data = self._encrypt(json.dumps(asdict(profile.address_verification)))

            biometric_data = None
            if profile.biometric_verification:
                biometric_data = self._encrypt(json.dumps(asdict(profile.biometric_verification)))

            source_of_funds_encrypted = None
            if profile.source_of_funds:
                source_of_funds_encrypted = self._encrypt(profile.source_of_funds)

            risk_assessment_json = None
            if profile.risk_assessment:
                risk_dict = asdict(profile.risk_assessment)
                risk_dict["risk_level"] = profile.risk_assessment.risk_level.value
                risk_assessment_json = json.dumps(risk_dict)

            cursor.execute("""
                INSERT OR REPLACE INTO kyc_profiles (
                    user_id, wallet_address, email_encrypted, email_verified,
                    kyc_level, verification_status, verification_timestamp,
                    jurisdiction, pii_encrypted, document_data_encrypted,
                    address_data_encrypted, biometric_data_encrypted,
                    risk_assessment, source_of_funds_encrypted,
                    source_of_funds_verified, created_at, updated_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                profile.wallet_address,
                email_encrypted,
                1 if profile.email_verified else 0,
                profile.kyc_level.value,
                profile.verification_status.value,
                profile.verification_timestamp,
                profile.jurisdiction,
                pii_encrypted,
                document_data,
                address_data,
                biometric_data,
                risk_assessment_json,
                source_of_funds_encrypted,
                1 if profile.source_of_funds_verified else 0,
                profile.created_at,
                profile.updated_at,
                profile.expires_at,
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store KYC profile for {profile.user_id}: {e}")
            raise

    async def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Retrieve user's KYC profile.

        Args:
            user_id: User identifier

        Returns:
            UserProfile if found, None otherwise
        """
        # Check cache first
        if user_id in self.verified_users:
            return self.verified_users[user_id]

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM kyc_profiles WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            # Decrypt and reconstruct profile
            pii_data = json.loads(self._decrypt(row["pii_encrypted"])) if row["pii_encrypted"] else {}

            profile = UserProfile(
                user_id=row["user_id"],
                wallet_address=row["wallet_address"],
                email=self._decrypt(row["email_encrypted"]) if row["email_encrypted"] else None,
                email_verified=bool(row["email_verified"]),
                kyc_level=KYCLevel(row["kyc_level"]),
                verification_status=VerificationStatus(row["verification_status"]),
                verification_timestamp=row["verification_timestamp"],
                jurisdiction=row["jurisdiction"],
                legal_name=pii_data.get("legal_name"),
                date_of_birth=pii_data.get("date_of_birth"),
                nationality=pii_data.get("nationality"),
                occupation=pii_data.get("occupation"),
                employer=pii_data.get("employer"),
                source_of_funds_verified=bool(row["source_of_funds_verified"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                expires_at=row["expires_at"],
            )

            if row["source_of_funds_encrypted"]:
                profile.source_of_funds = self._decrypt(row["source_of_funds_encrypted"])

            # Reconstruct document verification
            if row["document_data_encrypted"]:
                doc_data = json.loads(self._decrypt(row["document_data_encrypted"]))
                profile.document_verification = DocumentVerification(
                    document_type=DocumentType(doc_data["document_type"]),
                    document_number=doc_data["document_number"],
                    issuing_country=doc_data["issuing_country"],
                    expiry_date=doc_data.get("expiry_date"),
                    verified=doc_data["verified"],
                    confidence_score=doc_data.get("confidence_score", 0.0),
                    verification_timestamp=doc_data.get("verification_timestamp"),
                    rejection_reason=doc_data.get("rejection_reason"),
                )

            # Reconstruct address verification
            if row["address_data_encrypted"]:
                addr_data = json.loads(self._decrypt(row["address_data_encrypted"]))
                profile.address_verification = AddressVerification(**addr_data)

            # Reconstruct biometric verification
            if row["biometric_data_encrypted"]:
                bio_data = json.loads(self._decrypt(row["biometric_data_encrypted"]))
                profile.biometric_verification = BiometricVerification(**bio_data)

            # Reconstruct risk assessment
            if row["risk_assessment"]:
                risk_data = json.loads(row["risk_assessment"])
                profile.risk_assessment = RiskAssessment(
                    overall_score=risk_data["overall_score"],
                    risk_level=RiskLevel(risk_data["risk_level"]),
                    factors=risk_data.get("factors", {}),
                    flags=risk_data.get("flags", []),
                    assessment_timestamp=risk_data.get("assessment_timestamp"),
                )

            # Cache the profile
            self.verified_users[user_id] = profile
            return profile

        except Exception as e:
            logger.error(f"Failed to retrieve KYC profile for {user_id}: {e}")
            return None

    async def get_verification_level(self, user_id: str) -> KYCLevel:
        """
        Get current KYC verification level.

        Args:
            user_id: User identifier

        Returns:
            KYCLevel
        """
        profile = await self.get_profile(user_id)
        if profile:
            return profile.kyc_level
        return KYCLevel.UNVERIFIED

    async def is_transaction_allowed(
        self,
        user_id: str,
        transaction_amount_usd: float,
        lifetime_spend_usd: float,
    ) -> Dict[str, Any]:
        """
        Check if transaction is allowed based on KYC level.

        Args:
            user_id: User identifier
            transaction_amount_usd: Transaction amount in USD
            lifetime_spend_usd: User's lifetime spending in USD

        Returns:
            Dict with allowed status and required KYC level if not allowed
        """
        level = await self.get_verification_level(user_id)
        total_spend = lifetime_spend_usd + transaction_amount_usd

        # Enhanced KYC required for >$50K
        if total_spend > self.ENHANCED_THRESHOLD_USD:
            if level.value < KYCLevel.ENHANCED.value:
                logger.warning(f"Transaction blocked for {user_id}: Enhanced KYC required for >${self.ENHANCED_THRESHOLD_USD}")
                return {
                    "allowed": False,
                    "reason": "Enhanced KYC required",
                    "required_level": KYCLevel.ENHANCED.value,
                    "required_level_name": KYCLevel.ENHANCED.name,
                    "threshold": self.ENHANCED_THRESHOLD_USD,
                }

        # Standard KYC required for >$10K
        if total_spend > self.KYC_THRESHOLD_USD:
            if level.value < KYCLevel.STANDARD.value:
                logger.warning(f"Transaction blocked for {user_id}: Standard KYC required for >${self.KYC_THRESHOLD_USD}")
                return {
                    "allowed": False,
                    "reason": "Standard KYC required",
                    "required_level": KYCLevel.STANDARD.value,
                    "required_level_name": KYCLevel.STANDARD.name,
                    "threshold": self.KYC_THRESHOLD_USD,
                }

        return {
            "allowed": True,
            "current_level": level.value,
            "current_level_name": level.name,
        }

    async def revoke_verification(
        self,
        user_id: str,
        reason: str,
    ) -> bool:
        """
        Revoke user's KYC verification.

        Args:
            user_id: User identifier
            reason: Reason for revocation

        Returns:
            True if revoked successfully
        """
        try:
            profile = await self.get_profile(user_id)
            if not profile:
                return False

            profile.kyc_level = KYCLevel.UNVERIFIED
            profile.verification_status = VerificationStatus.REJECTED
            profile.updated_at = datetime.now(timezone.utc).isoformat()

            if profile.risk_assessment:
                profile.risk_assessment.flags.append(f"revoked:{reason}")

            await self._store_profile(profile)
            self.verified_users[user_id] = profile

            logger.warning(f"KYC verification revoked for {user_id}: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke KYC for {user_id}: {e}")
            return False


# Legacy compatibility alias
VerificationLevel = KYCLevel
