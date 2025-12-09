"""Peer representation in the mesh network."""

import uuid
from dataclasses import dataclass, field
from typing import Set, Optional
from datetime import datetime, timezone


@dataclass
class Peer:
    """
    Represents a peer node in the DCMX mesh network.
    
    Each peer has a unique ID and maintains information about its
    connectivity and available content.
    """
    
    peer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    host: str = "127.0.0.1"
    port: int = 8080
    last_seen: Optional[str] = None
    available_tracks: Set[str] = field(default_factory=set)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize last_seen timestamp."""
        if self.last_seen is None:
            self.last_seen = datetime.now(timezone.utc).isoformat()
    
    @property
    def address(self) -> str:
        """Get peer's network address."""
        return f"{self.host}:{self.port}"
    
    def update_last_seen(self):
        """Update the last seen timestamp to current time."""
        self.last_seen = datetime.now(timezone.utc).isoformat()
    
    def add_track(self, content_hash: str):
        """
        Add a track to the peer's available tracks.
        
        Args:
            content_hash: Content hash of the track
        """
        self.available_tracks.add(content_hash)
    
    def remove_track(self, content_hash: str):
        """
        Remove a track from the peer's available tracks.
        
        Args:
            content_hash: Content hash of the track
        """
        self.available_tracks.discard(content_hash)
    
    def has_track(self, content_hash: str) -> bool:
        """
        Check if peer has a specific track.
        
        Args:
            content_hash: Content hash of the track
            
        Returns:
            True if peer has the track
        """
        return content_hash in self.available_tracks
    
    def to_dict(self) -> dict:
        """Convert peer to dictionary representation."""
        return {
            "peer_id": self.peer_id,
            "host": self.host,
            "port": self.port,
            "last_seen": self.last_seen,
            "available_tracks": list(self.available_tracks),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Peer":
        """
        Create Peer instance from dictionary.
        
        Args:
            data: Dictionary containing peer data
            
        Returns:
            Peer instance
        """
        available_tracks = set(data.get("available_tracks", []))
        return cls(
            peer_id=data["peer_id"],
            host=data["host"],
            port=data["port"],
            last_seen=data.get("last_seen"),
            available_tracks=available_tracks,
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        """String representation of the peer."""
        return f"Peer({self.peer_id[:8]}... @ {self.address})"
    
    def __repr__(self) -> str:
        """Detailed representation of the peer."""
        return (
            f"Peer(peer_id='{self.peer_id}', address='{self.address}', "
            f"tracks={len(self.available_tracks)})"
        )
    
    def __hash__(self) -> int:
        """Hash based on peer_id for use in sets."""
        return hash(self.peer_id)
    
    def __eq__(self, other) -> bool:
        """Equality based on peer_id."""
        if not isinstance(other, Peer):
            return False
        return self.peer_id == other.peer_id
