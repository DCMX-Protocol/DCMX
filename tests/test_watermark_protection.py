"""
Tests for watermark protection and tamper detection.
"""

import pytest
from dcmx.audio.watermark_protection import (
    WatermarkProtectionManager,
    WatermarkProtectionPolicy,
    TamperType,
    WatermarkIntegrityRecord
)
from datetime import datetime, timezone


@pytest.fixture
def protection_policy():
    """Create default protection policy."""
    return WatermarkProtectionPolicy()


@pytest.fixture
def protection_manager(protection_policy):
    """Create protection manager."""
    return WatermarkProtectionManager(policy=protection_policy)


@pytest.fixture
def valid_watermark_data():
    """Valid watermark data."""
    return {
        "watermark_found": True,
        "valid": True,
        "confidence": 0.95,
        "tamper_detected": False,
        "rights_holder": "Artist",
        "nft_contract": "0x123abc",
        "edition": 1,
        "max_editions": 100,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def tampered_watermark_data():
    """Tampered watermark data."""
    return {
        "watermark_found": False,
        "valid": False,
        "confidence": 0.3,
        "tamper_detected": True,
        "tamper_type": TamperType.REMOVAL_ATTEMPTED
    }


class TestWatermarkProtectionPolicy:
    """Test watermark protection policy."""
    
    def test_default_policy(self):
        """Test default policy values."""
        policy = WatermarkProtectionPolicy()
        
        assert policy.require_watermark_for_playback
        assert policy.require_watermark_for_distribution
        assert policy.prevent_unauthorized_removal
        assert policy.block_watermark_removed_content
        assert "wav" in policy.allowed_output_formats
        assert "flac" in policy.allowed_output_formats
        assert "mp3" not in policy.allowed_output_formats
    
    def test_custom_policy(self):
        """Test custom policy."""
        policy = WatermarkProtectionPolicy(
            confidence_threshold=0.9,
            prevent_format_conversion=False
        )
        
        assert policy.confidence_threshold == 0.9
        assert not policy.prevent_format_conversion


class TestWatermarkIntegrityRecord:
    """Test watermark integrity records."""
    
    def test_record_creation(self):
        """Test creating integrity record."""
        record = WatermarkIntegrityRecord(
            timestamp="2024-12-09T12:00:00Z",
            watermark_found=True,
            confidence=0.95,
            valid=True,
            tamper_detected=False,
            tamper_type=None,
            previous_hash="abc123",
            current_hash="abc123",
            hash_match=True,
            access_user="user123",
            access_ip="192.168.1.100",
            access_context="playback",
            action_taken="allow"
        )
        
        assert record.watermark_found
        assert record.confidence == 0.95
        assert record.action_taken == "allow"
    
    def test_record_to_dict(self):
        """Test converting record to dict."""
        record = WatermarkIntegrityRecord(
            timestamp="2024-12-09T12:00:00Z",
            watermark_found=True,
            confidence=0.95,
            valid=True,
            tamper_detected=True,
            tamper_type=TamperType.MODIFICATION_DETECTED,
            previous_hash="abc123",
            current_hash="def456",
            hash_match=False,
            access_user="user123",
            access_ip="192.168.1.100",
            access_context="playback",
            action_taken="block"
        )
        
        data = record.to_dict()
        assert data["watermark_found"]
        assert data["tamper_type"] == "modification_detected"
        assert data["action_taken"] == "block"


class TestWatermarkVerification:
    """Test watermark verification and access control."""
    
    @pytest.mark.asyncio
    async def test_valid_watermark_allows_access(
        self, protection_manager, valid_watermark_data
    ):
        """Test that valid watermark allows access."""
        audio_bytes = b"audio_data_123"
        
        result = await protection_manager.verify_watermark_access(
            audio_bytes=audio_bytes,
            watermark_data=valid_watermark_data,
            user_id="user123",
            ip_address="192.168.1.100",
            access_context="playback"
        )
        
        assert result["allowed"]
        assert result["action"] == "allow"
        assert not result["tamper_detected"]
        assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_missing_watermark_blocks_access(
        self, protection_manager
    ):
        """Test that missing watermark blocks access."""
        watermark_data = {
            "watermark_found": False,
            "valid": False,
            "confidence": 0.0,
            "tamper_detected": True,
            "tamper_type": TamperType.REMOVAL_ATTEMPTED
        }
        
        result = await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_data",
            watermark_data=watermark_data,
            user_id="user123",
            ip_address="192.168.1.100",
            access_context="playback"
        )
        
        assert not result["allowed"]
        assert result["action"] == "block"
        assert result["tamper_detected"]
        assert result["tamper_type"] == TamperType.REMOVAL_ATTEMPTED
    
    @pytest.mark.asyncio
    async def test_low_confidence_watermark(
        self, protection_manager
    ):
        """Test low confidence watermark handling."""
        watermark_data = {
            "watermark_found": True,
            "valid": False,
            "confidence": 0.5,  # Below 0.85 threshold
            "tamper_detected": True
        }
        
        result = await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_data",
            watermark_data=watermark_data,
            user_id="user123",
            ip_address="192.168.1.100",
            access_context="playback"
        )
        
        assert result["tamper_detected"]
        assert result["tamper_type"] == TamperType.MODIFICATION_DETECTED
        assert "confidence" in result["reasons"][0].lower()
    
    @pytest.mark.asyncio
    async def test_distribution_requires_watermark(
        self, protection_manager
    ):
        """Test that distribution requires watermark."""
        watermark_data = {
            "watermark_found": False,
            "valid": False,
            "confidence": 0.0
        }
        
        result = await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_data",
            watermark_data=watermark_data,
            user_id="user123",
            ip_address="192.168.1.100",
            access_context="distribution"
        )
        
        assert not result["allowed"]
        assert "distribution" in " ".join(result["reasons"]).lower()
    
    @pytest.mark.asyncio
    async def test_hash_mismatch_detection(
        self, protection_manager, valid_watermark_data
    ):
        """Test detection of file modification via hash."""
        audio_bytes = b"audio_data_123"
        previous_hash = "abc123def456"  # Different from audio hash
        
        result = await protection_manager.verify_watermark_access(
            audio_bytes=audio_bytes,
            watermark_data=valid_watermark_data,
            user_id="user123",
            ip_address="192.168.1.100",
            access_context="playback",
            previous_hash=previous_hash
        )
        
        assert not result["record"].hash_match
        assert result["tamper_detected"]
        assert result["tamper_type"] == TamperType.MODIFICATION_DETECTED


class TestCopyProtection:
    """Test copy protection mechanisms."""
    
    @pytest.mark.asyncio
    async def test_bit_for_bit_copy_allowed(self, protection_manager):
        """Test that bit-for-bit identical copy is allowed."""
        audio_bytes = b"exact_audio_data"
        
        result = await protection_manager.prevent_unauthorized_copy(
            original_bytes=audio_bytes,
            copy_bytes=audio_bytes,
            original_watermark={"watermark_found": True},
            user_id="user123",
            ip_address="192.168.1.100"
        )
        
        assert result["allowed"]
        assert result["bit_for_bit_match"]
        assert result["watermark_preserved"]
    
    @pytest.mark.asyncio
    async def test_lossy_conversion_blocked(self, protection_manager):
        """Test that lossy conversion is blocked."""
        original_bytes = b"a" * 1000  # 1000 bytes
        copy_bytes = b"b" * 700  # 70% size (significant loss)
        
        result = await protection_manager.prevent_unauthorized_copy(
            original_bytes=original_bytes,
            copy_bytes=copy_bytes,
            original_watermark={"watermark_found": True},
            user_id="user123",
            ip_address="192.168.1.100"
        )
        
        assert not result["allowed"]
        assert "lossy" in result["reason"].lower()


class TestFormatProtection:
    """Test format enforcement."""
    
    @pytest.mark.asyncio
    async def test_lossless_format_allowed(
        self, protection_manager, valid_watermark_data
    ):
        """Test that lossless formats are allowed."""
        result = await protection_manager.enforce_format_protection(
            audio_bytes=b"audio_data",
            watermark_data=valid_watermark_data,
            target_format="flac",
            user_id="user123"
        )
        
        assert result["allowed"]
        assert "flac" in result["recommended_format"].lower()
    
    @pytest.mark.asyncio
    async def test_lossy_format_blocked(
        self, protection_manager, valid_watermark_data
    ):
        """Test that lossy formats are blocked."""
        result = await protection_manager.enforce_format_protection(
            audio_bytes=b"audio_data",
            watermark_data=valid_watermark_data,
            target_format="mp3",
            user_id="user123"
        )
        
        assert not result["allowed"]
        assert "lossy" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_aac_format_blocked(
        self, protection_manager, valid_watermark_data
    ):
        """Test that AAC (lossy) is blocked."""
        result = await protection_manager.enforce_format_protection(
            audio_bytes=b"audio_data",
            watermark_data=valid_watermark_data,
            target_format="aac",
            user_id="user123"
        )
        
        assert not result["allowed"]
    
    @pytest.mark.asyncio
    async def test_missing_watermark_blocks_conversion(
        self, protection_manager
    ):
        """Test that missing watermark blocks any conversion."""
        watermark_data = {"watermark_found": False}
        
        result = await protection_manager.enforce_format_protection(
            audio_bytes=b"audio_data",
            watermark_data=watermark_data,
            target_format="flac",
            user_id="user123"
        )
        
        assert not result["allowed"]


class TestTamperDetection:
    """Test tamper detection."""
    
    @pytest.mark.asyncio
    async def test_removal_attempt_logged(
        self, protection_manager
    ):
        """Test that removal attempts are logged."""
        watermark_data = {
            "watermark_found": False,
            "valid": False,
            "confidence": 0.0,
            "tamper_detected": True,
            "tamper_type": TamperType.REMOVAL_ATTEMPTED
        }
        
        await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_data",
            watermark_data=watermark_data,
            user_id="attacker_user",
            ip_address="192.168.100.50",
            access_context="export"
        )
        
        records = protection_manager.get_integrity_records(tamper_only=True)
        assert len(records) > 0
        assert records[0].tamper_type == TamperType.REMOVAL_ATTEMPTED
    
    @pytest.mark.asyncio
    async def test_tamper_statistics(
        self, protection_manager, valid_watermark_data
    ):
        """Test tamper statistics calculation."""
        # Create valid access
        await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_1",
            watermark_data=valid_watermark_data,
            user_id="user1",
            ip_address="192.168.1.100",
            access_context="playback"
        )
        
        # Create tamper attempt
        tampered = {
            "watermark_found": False,
            "valid": False,
            "confidence": 0.0,
            "tamper_detected": True,
            "tamper_type": TamperType.REMOVAL_ATTEMPTED
        }
        
        await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_2",
            watermark_data=tampered,
            user_id="attacker",
            ip_address="192.168.100.50",
            access_context="export"
        )
        
        stats = protection_manager.get_tamper_statistics()
        
        assert stats["total_verifications"] == 2
        assert stats["tamper_attempts"] >= 1
        assert stats["tamper_rate"] > 0


class TestIntegrityRecords:
    """Test integrity record retrieval."""
    
    @pytest.mark.asyncio
    async def test_retrieve_all_records(
        self, protection_manager, valid_watermark_data
    ):
        """Test retrieving all integrity records."""
        for i in range(5):
            await protection_manager.verify_watermark_access(
                audio_bytes=f"audio_{i}".encode(),
                watermark_data=valid_watermark_data,
                user_id=f"user{i % 2}",
                ip_address=f"192.168.1.{100+i}",
                access_context="playback"
            )
        
        records = protection_manager.get_integrity_records()
        assert len(records) == 5
    
    @pytest.mark.asyncio
    async def test_filter_by_user(
        self, protection_manager, valid_watermark_data
    ):
        """Test filtering records by user."""
        for user_id in ["user1", "user2", "user1"]:
            await protection_manager.verify_watermark_access(
                audio_bytes=b"audio_data",
                watermark_data=valid_watermark_data,
                user_id=user_id,
                ip_address="192.168.1.100",
                access_context="playback"
            )
        
        user1_records = protection_manager.get_integrity_records(user_id="user1")
        assert len(user1_records) == 2
        assert all(r.access_user == "user1" for r in user1_records)
    
    @pytest.mark.asyncio
    async def test_tamper_only_filter(
        self, protection_manager, valid_watermark_data
    ):
        """Test filtering for tamper records only."""
        # Valid access
        await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_1",
            watermark_data=valid_watermark_data,
            user_id="user1",
            ip_address="192.168.1.100",
            access_context="playback"
        )
        
        # Tamper attempt
        tampered = {
            "watermark_found": False,
            "valid": False,
            "confidence": 0.0,
            "tamper_detected": True
        }
        
        await protection_manager.verify_watermark_access(
            audio_bytes=b"audio_2",
            watermark_data=tampered,
            user_id="attacker",
            ip_address="192.168.100.50",
            access_context="export"
        )
        
        tamper_records = protection_manager.get_integrity_records(tamper_only=True)
        assert len(tamper_records) >= 1
        assert all(r.tamper_detected for r in tamper_records)
