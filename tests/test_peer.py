"""Tests for Peer functionality."""

import pytest
from dcmx.network.peer import Peer


def test_peer_creation():
    """Test basic peer creation."""
    peer = Peer(host="192.168.1.1", port=8080)
    
    assert peer.host == "192.168.1.1"
    assert peer.port == 8080
    assert peer.peer_id is not None
    assert peer.last_seen is not None
    assert len(peer.available_tracks) == 0


def test_peer_with_id():
    """Test peer creation with specific ID."""
    peer = Peer(peer_id="test-peer-id", host="127.0.0.1", port=9000)
    
    assert peer.peer_id == "test-peer-id"


def test_peer_address():
    """Test peer address property."""
    peer = Peer(host="192.168.1.1", port=8080)
    assert peer.address == "192.168.1.1:8080"


def test_peer_add_track():
    """Test adding tracks to peer."""
    peer = Peer()
    
    peer.add_track("hash1")
    peer.add_track("hash2")
    
    assert len(peer.available_tracks) == 2
    assert "hash1" in peer.available_tracks
    assert "hash2" in peer.available_tracks


def test_peer_remove_track():
    """Test removing tracks from peer."""
    peer = Peer()
    peer.add_track("hash1")
    peer.add_track("hash2")
    
    peer.remove_track("hash1")
    
    assert len(peer.available_tracks) == 1
    assert "hash1" not in peer.available_tracks
    assert "hash2" in peer.available_tracks


def test_peer_has_track():
    """Test checking if peer has track."""
    peer = Peer()
    peer.add_track("hash1")
    
    assert peer.has_track("hash1") is True
    assert peer.has_track("hash2") is False


def test_peer_to_dict():
    """Test peer serialization to dictionary."""
    peer = Peer(peer_id="test-id", host="127.0.0.1", port=8080)
    peer.add_track("hash1")
    peer.metadata = {"version": "1.0"}
    
    peer_dict = peer.to_dict()
    
    assert peer_dict["peer_id"] == "test-id"
    assert peer_dict["host"] == "127.0.0.1"
    assert peer_dict["port"] == 8080
    assert "hash1" in peer_dict["available_tracks"]
    assert peer_dict["metadata"]["version"] == "1.0"


def test_peer_from_dict():
    """Test peer deserialization from dictionary."""
    peer_dict = {
        "peer_id": "test-id",
        "host": "127.0.0.1",
        "port": 8080,
        "available_tracks": ["hash1", "hash2"],
        "metadata": {"version": "1.0"},
    }
    
    peer = Peer.from_dict(peer_dict)
    
    assert peer.peer_id == "test-id"
    assert peer.host == "127.0.0.1"
    assert peer.port == 8080
    assert len(peer.available_tracks) == 2
    assert peer.has_track("hash1")
    assert peer.has_track("hash2")
    assert peer.metadata["version"] == "1.0"


def test_peer_equality():
    """Test peer equality comparison."""
    peer1 = Peer(peer_id="test-id", host="127.0.0.1", port=8080)
    peer2 = Peer(peer_id="test-id", host="192.168.1.1", port=9000)
    peer3 = Peer(peer_id="other-id", host="127.0.0.1", port=8080)
    
    # Same peer_id means equal
    assert peer1 == peer2
    
    # Different peer_id means not equal
    assert peer1 != peer3


def test_peer_hash():
    """Test peer hashing for use in sets."""
    peer1 = Peer(peer_id="test-id")
    peer2 = Peer(peer_id="test-id")
    peer3 = Peer(peer_id="other-id")
    
    # Same peer_id should have same hash
    assert hash(peer1) == hash(peer2)
    
    # Can be used in sets
    peer_set = {peer1, peer2, peer3}
    assert len(peer_set) == 2  # peer1 and peer2 are considered same


def test_peer_update_last_seen():
    """Test updating last seen timestamp."""
    peer = Peer()
    original_time = peer.last_seen
    
    # Wait a bit and update
    import time
    time.sleep(0.01)
    peer.update_last_seen()
    
    assert peer.last_seen != original_time
