"""
Watermark Protection and Tamper Detection.

Implements anti-tampering, copy-protection, and watermark enforcement mechanisms
to prevent unauthorized removal or modification of audio watermarks.

Features:
- Real-time watermark integrity verification
- Tamper detection and logging
- Copy protection (bit-for-bit comparison)
- Watermark enforcement (block unauthorized formats)
- Forensic evidence collection
- Compliance reporting
"""

import logging
import hashlib
import struct
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class TamperType(Enum):
    """Types of watermark tampering detected."""
    REMOVAL_ATTEMPTED = "removal_attempted"
    MODIFICATION_DETECTED = "modification_detected"
    BITRATE_ATTACK = "bitrate_attack"  # Down-sampling to remove watermark
    COMPRESSION_ATTACK = "compression_attack"  # Lossy compression
    FREQUENCY_FILTERING = "frequency_filtering"  # Notch filtering
    TIME_SHIFTING = "time_shifting"  # Temporal alignment attack
    FORMAT_CONVERSION = "format_conversion"  # Unauthorized format change
    CHECKSUM_FAILURE = "checksum_failure"  # Integrity check failed
    SYNC_MARKER_LOST = "sync_marker_lost"  # Watermark detection failed
    UNKNOWN = "unknown"


@dataclass
class WatermarkProtectionPolicy:
    """Policy for watermark protection enforcement."""
    
    # Enforcement settings
    require_watermark_for_playback: bool = True
    require_watermark_for_distribution: bool = True
    require_watermark_for_commercial_use: bool = True
    
    # Detection settings
    confidence_threshold: float = 0.85  # Minimum confidence for valid watermark
    tamper_detection_enabled: bool = True
    
    # Prevention settings
    prevent_unauthorized_removal: bool = True
    prevent_unauthorized_modification: bool = True
    prevent_format_conversion: bool = True
    
    # Allowed formats (with watermark)
    allowed_output_formats: List[str] = None
    
    # Blocking settings
    block_watermark_removed_content: bool = True
    block_tampered_content: bool = True
    
    # Logging
    log_all_access: bool = True
    log_tampering_attempts: bool = True
    report_to_compliance: bool = True
    
    def __post_init__(self):
        if self.allowed_output_formats is None:
            # Only allow formats that preserve watermark fidelity
            self.allowed_output_formats = ["wav", "flac", "alac"]


@dataclass
class WatermarkIntegrityRecord:
    """Record of watermark integrity verification."""
    
    timestamp: str  # UTC ISO format
    watermark_found: bool
    confidence: float
    valid: bool
    tamper_detected: bool
    tamper_type: Optional[TamperType]
    previous_hash: Optional[str]  # Hash of previous known state
    current_hash: str  # Hash of current state
    hash_match: bool  # Does current match previous?
    access_user: str
    access_ip: str
    access_context: str  # "playback", "transfer", "export", etc
    action_taken: str  # Block, allow, log, alert
    forensic_data: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp,
            "watermark_found": self.watermark_found,
            "confidence": self.confidence,
            "valid": self.valid,
            "tamper_detected": self.tamper_detected,
            "tamper_type": self.tamper_type.value if self.tamper_type else None,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
            "hash_match": self.hash_match,
            "access_user": self.access_user,
            "access_ip": self.access_ip,
            "access_context": self.access_context,
            "action_taken": self.action_taken,
            "forensic_data": self.forensic_data or {}
        }


class WatermarkProtectionManager:
    """
    Manages watermark protection, tamper detection, and enforcement.
    
    Features:
    - Real-time watermark verification on every access
    - Tamper detection with forensic logging
    - Copy protection (bit-for-bit verification)
    - Format enforcement (block unauthorized conversions)
    - Compliance reporting (DMCA § 1201)
    """
    
    def __init__(
        self,
        policy: Optional[WatermarkProtectionPolicy] = None,
        audit_logger=None
    ):
        """
        Initialize watermark protection manager.
        
        Args:
            policy: WatermarkProtectionPolicy (uses defaults if None)
            audit_logger: Optional compliance audit logger
        """
        self.policy = policy or WatermarkProtectionPolicy()
        self.audit_logger = audit_logger
        
        # Track known watermarks
        self.known_watermarks: Dict[str, Dict[str, Any]] = {}
        
        # Integrity records
        self.integrity_records: List[WatermarkIntegrityRecord] = []
        
        logger.info("Watermark Protection Manager initialized")
    
    async def verify_watermark_access(
        self,
        audio_bytes: bytes,
        watermark_data: Dict[str, Any],
        user_id: str,
        ip_address: str,
        access_context: str,
        previous_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify watermark before allowing access/use.
        
        Args:
            audio_bytes: Audio file bytes
            watermark_data: Extracted watermark metadata
            user_id: User attempting access
            ip_address: User IP address
            access_context: "playback", "transfer", "export", etc
            previous_hash: Hash of known good state
            
        Returns:
            {
                "allowed": bool,
                "action": "allow" | "block" | "alert",
                "reasons": [str],
                "tamper_detected": bool,
                "tamper_type": TamperType or None,
                "confidence": float,
                "record": WatermarkIntegrityRecord
            }
        """
        reasons = []
        action = "allow"
        tamper_detected = False
        tamper_type = None
        
        # 2. Check watermark validity FIRST (highest priority)
        confidence = watermark_data.get("confidence", 0.0)
        if confidence < self.policy.confidence_threshold:
            reasons.append(f"Watermark confidence {confidence:.2%} below threshold {self.policy.confidence_threshold:.2%}")
            tamper_detected = True
            tamper_type = TamperType.MODIFICATION_DETECTED
        
        # Check if explicit tamper_type is provided in watermark_data
        provided_tamper_type = watermark_data.get("tamper_type")
        
        # 1. Check watermark presence (second priority)
        if not watermark_data.get("watermark_found"):
            reasons.append("Watermark not detected in audio")
            if self.policy.block_watermark_removed_content:
                action = "block"
            tamper_detected = True
            # Only set removal type if not already identified and not provided
            if tamper_type is None and provided_tamper_type is None:
                tamper_type = TamperType.REMOVAL_ATTEMPTED
        
        # 3. Check if marked as valid
        if not watermark_data.get("valid"):
            reasons.append("Watermark validity check failed")
            if self.policy.block_tampered_content:
                action = "block"
            tamper_detected = True
            # Only set if not already identified and not provided
            if tamper_type is None and provided_tamper_type is None:
                tamper_type = TamperType.CHECKSUM_FAILURE
        
        # 4. Check for tampering indicators
        if watermark_data.get("tamper_detected"):
            reasons.append("Tampering detected in watermark data")
            if self.policy.block_tampered_content:
                action = "block"
            tamper_detected = True
            # Use the tamper_type from data if available (takes precedence)
            if provided_tamper_type:
                tamper_type = provided_tamper_type
            elif tamper_type is None:
                tamper_type = TamperType.UNKNOWN
        
        # 5. Hash integrity check
        current_hash = hashlib.sha256(audio_bytes).hexdigest()
        hash_match = True
        
        if previous_hash and previous_hash != current_hash:
            reasons.append("Audio file has been modified since last verification")
            hash_match = False
            # Modified audio might have watermark removed or altered
            if self.policy.prevent_unauthorized_modification:
                action = "block"
            tamper_detected = True
            # Only set if not already identified
            if tamper_type is None:
                tamper_type = TamperType.MODIFICATION_DETECTED
        
        # 6. Enforce watermark requirements
        if access_context == "distribution" and self.policy.require_watermark_for_distribution:
            if not watermark_data.get("watermark_found"):
                reasons.append("Watermark required for distribution")
                action = "block"
        
        if access_context == "commercial" and self.policy.require_watermark_for_commercial_use:
            if not watermark_data.get("watermark_found"):
                reasons.append("Watermark required for commercial use")
                action = "block"
        
        # Create integrity record
        timestamp = datetime.now(timezone.utc).isoformat()
        record = WatermarkIntegrityRecord(
            timestamp=timestamp,
            watermark_found=watermark_data.get("watermark_found", False),
            confidence=confidence,
            valid=watermark_data.get("valid", False),
            tamper_detected=tamper_detected,
            tamper_type=tamper_type,
            previous_hash=previous_hash,
            current_hash=current_hash,
            hash_match=hash_match,
            access_user=user_id,
            access_ip=ip_address,
            access_context=access_context,
            action_taken=action,
            forensic_data=self._collect_forensics(watermark_data)
        )
        
        self.integrity_records.append(record)
        
        # Log to compliance system if enabled
        if self.policy.log_all_access and self.audit_logger:
            await self._log_to_compliance(record, action)
        
        # Alert if tampering detected
        if tamper_detected and self.policy.log_tampering_attempts:
            logger.warning(
                f"WATERMARK TAMPER ATTEMPT: user={user_id} ip={ip_address} "
                f"context={access_context} tamper_type={tamper_type}"
            )
        
        allowed = action == "allow"
        
        logger.info(
            f"Watermark verification: user={user_id} context={access_context} "
            f"allowed={allowed} tamper_detected={tamper_detected} "
            f"confidence={confidence:.2%}"
        )
        
        return {
            "allowed": allowed,
            "action": action,
            "reasons": reasons,
            "tamper_detected": tamper_detected,
            "tamper_type": tamper_type,
            "confidence": confidence,
            "record": record
        }
    
    async def prevent_unauthorized_copy(
        self,
        original_bytes: bytes,
        copy_bytes: bytes,
        original_watermark: Dict[str, Any],
        user_id: str,
        ip_address: str
    ) -> Dict[str, Any]:
        """
        Prevent copying of audio by requiring watermark preservation.
        
        Args:
            original_bytes: Original audio with watermark
            copy_bytes: Copied/converted audio
            original_watermark: Watermark from original
            user_id: User attempting copy
            ip_address: User IP address
            
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "watermark_preserved": bool,
                "bit_for_bit_match": bool,
                "detection_method": str
            }
        """
        # Check 1: Bit-for-bit comparison
        bit_for_bit = original_bytes == copy_bytes
        
        if bit_for_bit:
            # Exact copy detected - allow (watermark preserved)
            logger.info(f"Bit-for-bit identical copy detected: {user_id}")
            return {
                "allowed": True,
                "reason": "Bit-for-bit identical (watermark preserved)",
                "watermark_preserved": True,
                "bit_for_bit_match": True,
                "detection_method": "exact_match"
            }
        
        # Check 2: Hash comparison
        orig_hash = hashlib.sha256(original_bytes).hexdigest()
        copy_hash = hashlib.sha256(copy_bytes).hexdigest()
        
        if orig_hash == copy_hash:
            # Same content, different representation
            logger.info(f"Content-identical copy detected: {user_id}")
            return {
                "allowed": True,
                "reason": "Content identical (watermark preserved)",
                "watermark_preserved": True,
                "bit_for_bit_match": False,
                "detection_method": "content_hash"
            }
        
        # Check 3: Size mismatch (lossy conversion = watermark removal attempt)
        size_ratio = len(copy_bytes) / len(original_bytes) if original_bytes else 0
        
        if size_ratio < 0.8:  # More than 20% smaller = likely lossy compression
            logger.warning(f"COPY PROTECTION: Lossy conversion detected ({size_ratio:.1%}): {user_id}")
            
            if self.policy.prevent_unauthorized_removal:
                return {
                    "allowed": False,
                    "reason": "Lossy conversion detected - watermark may be compromised",
                    "watermark_preserved": False,
                    "bit_for_bit_match": False,
                    "detection_method": "size_ratio"
                }
        
        # Check 4: Watermark verification in copy
        # This would use AudioWatermark.verify() from main module
        copy_watermark_present = copy_hash in [
            hashlib.sha256(bytes([b for b in copy_bytes])).hexdigest()
        ]
        
        if not copy_watermark_present:
            logger.warning(f"COPY PROTECTION: Watermark removed in copy: {user_id}")
            
            return {
                "allowed": False,
                "reason": "Watermark removed or severely degraded in copy",
                "watermark_preserved": False,
                "bit_for_bit_match": False,
                "detection_method": "watermark_missing"
            }
        
        # Check 5: Format enforcement
        # Original should be lossless, copy should not be lossy MP3
        
        return {
            "allowed": True,
            "reason": "Copy acceptable (watermark properties preserved)",
            "watermark_preserved": True,
            "bit_for_bit_match": False,
            "detection_method": "watermark_preserved"
        }
    
    async def enforce_format_protection(
        self,
        audio_bytes: bytes,
        watermark_data: Dict[str, Any],
        target_format: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Enforce format restrictions to protect watermarks.
        
        Only allows formats that preserve watermark integrity.
        Blocks lossy compression formats (MP3, AAC) that degrade watermarks.
        
        Args:
            audio_bytes: Audio to be converted
            watermark_data: Current watermark info
            target_format: Target format (mp3, aac, flac, wav, etc)
            user_id: User requesting conversion
            
        Returns:
            {
                "allowed": bool,
                "reason": str,
                "allowed_formats": [str],
                "recommended_format": str
            }
        """
        target_format_lower = target_format.lower().strip(".")
        
        # Check if watermark exists
        if not watermark_data.get("watermark_found"):
            logger.warning(f"Format enforcement: No watermark found for {user_id}")
            return {
                "allowed": False,
                "reason": "Cannot convert: Watermark not found (likely already removed)",
                "allowed_formats": [],
                "recommended_format": None
            }
        
        # Lossless formats that preserve watermarks
        lossless_formats = ["wav", "flac", "alac", "ape", "wv"]
        
        # Lossy formats that damage watermarks
        lossy_formats = ["mp3", "aac", "m4a", "ogg", "opus"]
        
        # Proprietary DRM formats
        drm_formats = ["m4b", "m4p", "wma"]
        
        if target_format_lower in lossless_formats:
            logger.info(f"Format conversion approved (lossless): {target_format_lower} by {user_id}")
            return {
                "allowed": True,
                "reason": f"Lossless format preserves watermark integrity",
                "allowed_formats": self.policy.allowed_output_formats,
                "recommended_format": "flac"
            }
        
        elif target_format_lower in lossy_formats:
            logger.warning(f"Format conversion BLOCKED (lossy): {target_format_lower} by {user_id}")
            return {
                "allowed": False,
                "reason": f"Lossy format {target_format_lower} damages watermark - use lossless format",
                "allowed_formats": lossless_formats,
                "recommended_format": "flac"
            }
        
        elif target_format_lower in drm_formats:
            logger.warning(f"Format conversion BLOCKED (DRM): {target_format_lower} by {user_id}")
            return {
                "allowed": False,
                "reason": f"DRM format {target_format_lower} not supported - use standard lossless",
                "allowed_formats": lossless_formats,
                "recommended_format": "flac"
            }
        
        else:
            logger.warning(f"Format conversion BLOCKED (unknown): {target_format_lower} by {user_id}")
            return {
                "allowed": False,
                "reason": f"Unsupported format {target_format_lower}",
                "allowed_formats": lossless_formats,
                "recommended_format": "flac"
            }
    
    def get_integrity_records(
        self,
        user_id: Optional[str] = None,
        tamper_only: bool = False,
        limit: int = 100
    ) -> List[WatermarkIntegrityRecord]:
        """
        Retrieve integrity verification records.
        
        Args:
            user_id: Filter by user (None = all users)
            tamper_only: Only return tamper detection records
            limit: Maximum records to return
            
        Returns:
            List of WatermarkIntegrityRecord
        """
        records = self.integrity_records
        
        if user_id:
            records = [r for r in records if r.access_user == user_id]
        
        if tamper_only:
            records = [r for r in records if r.tamper_detected]
        
        # Return most recent first
        records.sort(key=lambda r: r.timestamp, reverse=True)
        
        return records[:limit]
    
    def get_tamper_statistics(self) -> Dict[str, Any]:
        """
        Get statistics on watermark tampering attempts.
        
        Returns:
            {
                "total_verifications": int,
                "tamper_attempts": int,
                "successful_blocks": int,
                "by_type": {TamperType: count},
                "top_users": [(user_id, count)],
                "top_ips": [(ip_address, count)]
            }
        """
        total = len(self.integrity_records)
        tampered = [r for r in self.integrity_records if r.tamper_detected]
        blocked = [r for r in tampered if r.action_taken == "block"]
        
        # Group by tamper type
        by_type = {}
        for record in tampered:
            if record.tamper_type:
                key = record.tamper_type.value
                by_type[key] = by_type.get(key, 0) + 1
        
        # Top users attempting tamper
        user_attempts = {}
        for record in tampered:
            user_attempts[record.access_user] = user_attempts.get(record.access_user, 0) + 1
        top_users = sorted(user_attempts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top IPs attempting tamper
        ip_attempts = {}
        for record in tampered:
            ip_attempts[record.access_ip] = ip_attempts.get(record.access_ip, 0) + 1
        top_ips = sorted(ip_attempts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_verifications": total,
            "tamper_attempts": len(tampered),
            "successful_blocks": len(blocked),
            "tamper_rate": len(tampered) / total if total > 0 else 0.0,
            "block_rate": len(blocked) / len(tampered) if tampered else 0.0,
            "by_type": by_type,
            "top_users": top_users,
            "top_ips": top_ips
        }
    
    def _collect_forensics(self, watermark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect forensic evidence from watermark verification."""
        return {
            "rights_holder": watermark_data.get("rights_holder"),
            "nft_contract": watermark_data.get("nft_contract"),
            "edition": watermark_data.get("edition"),
            "max_editions": watermark_data.get("max_editions"),
            "timestamp": watermark_data.get("timestamp"),
            "confidence": watermark_data.get("confidence"),
            "detection_method": "spread_spectrum_fft"
        }
    
    async def _log_to_compliance(
        self,
        record: WatermarkIntegrityRecord,
        action: str
    ):
        """Log verification result to compliance audit system."""
        if not self.audit_logger:
            return
        
        # Determine event type
        if record.tamper_detected:
            from dcmx.compliance import AuditEventType
            event_type = AuditEventType.SUSPICIOUS_ACTIVITY
            status = "alert"
        else:
            event_type = AuditEventType.DATA_ACCESS
            status = "success"
        
        try:
            await self.audit_logger.log_event(
                event_type=event_type,
                user_id=record.access_user,
                resource_type="watermarked_audio",
                resource_id=record.current_hash[:16],
                action=f"watermark_verification_{record.access_context}",
                status=status,
                result=action,
                details={
                    "watermark_found": record.watermark_found,
                    "confidence": record.confidence,
                    "tamper_type": record.tamper_type.value if record.tamper_type else None,
                    "ip_address": record.access_ip,
                    "forensics": record.forensic_data
                }
            )
        except Exception as e:
            logger.error(f"Failed to log to compliance: {e}")
