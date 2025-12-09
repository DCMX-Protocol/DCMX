"""Audio processing and DRM for DCMX - watermarking and fingerprinting."""

from .audio_watermark import AudioWatermark, WatermarkMetadata
from .audio_fingerprint import AudioFingerprint, AudioLandmark
from .watermark_protection import (
    WatermarkProtectionManager,
    WatermarkProtectionPolicy,
    WatermarkIntegrityRecord,
    TamperType
)

__all__ = [
    "AudioWatermark",
    "AudioFingerprint",
    "WatermarkMetadata",
    "AudioLandmark",
    "WatermarkProtectionManager",
    "WatermarkProtectionPolicy",
    "WatermarkIntegrityRecord",
    "TamperType"
]
