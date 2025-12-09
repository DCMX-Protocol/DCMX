"""Track metadata representation for distributed music content."""

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class Track:
    """
    Represents a music track in the DCMX network.
    
    Tracks are content-addressed using their content hash, ensuring
    immutability and enabling efficient deduplication across the network.
    """
    
    title: str
    artist: str
    content_hash: str  # SHA-256 hash of the audio content
    duration: int  # Duration in seconds
    size: int  # File size in bytes
    format: str = "mp3"  # Audio format
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    @staticmethod
    def compute_content_hash(data: bytes) -> str:
        """
        Compute SHA-256 hash of audio content.
        
        Args:
            data: Raw audio file bytes
            
        Returns:
            Hexadecimal string representation of the hash
        """
        return hashlib.sha256(data).hexdigest()
    
    def get_metadata_hash(self) -> str:
        """
        Compute hash of track metadata for verification.
        
        Returns:
            SHA-256 hash of the metadata
        """
        metadata_dict = asdict(self)
        metadata_json = json.dumps(metadata_dict, sort_keys=True)
        return hashlib.sha256(metadata_json.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert track to dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Track":
        """
        Create Track instance from dictionary.
        
        Args:
            data: Dictionary containing track data
            
        Returns:
            Track instance
        """
        return cls(**data)
    
    def __str__(self) -> str:
        """String representation of the track."""
        return f"{self.artist} - {self.title} ({self.format}, {self.duration}s)"
    
    def __repr__(self) -> str:
        """Detailed representation of the track."""
        return (
            f"Track(title='{self.title}', artist='{self.artist}', "
            f"content_hash='{self.content_hash[:16]}...', format='{self.format}')"
        )
