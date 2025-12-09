"""Tests for Track functionality."""

import pytest
from dcmx.core.track import Track


def test_track_creation():
    """Test basic track creation."""
    track = Track(
        title="Test Song",
        artist="Test Artist",
        content_hash="abc123",
        duration=180,
        size=5000000,
        format="mp3",
    )
    
    assert track.title == "Test Song"
    assert track.artist == "Test Artist"
    assert track.content_hash == "abc123"
    assert track.duration == 180
    assert track.size == 5000000
    assert track.format == "mp3"
    assert track.timestamp is not None


def test_track_with_optional_fields():
    """Test track with optional metadata."""
    track = Track(
        title="Test Song",
        artist="Test Artist",
        content_hash="abc123",
        duration=180,
        size=5000000,
        album="Test Album",
        year=2024,
        genre="Electronic",
    )
    
    assert track.album == "Test Album"
    assert track.year == 2024
    assert track.genre == "Electronic"


def test_compute_content_hash():
    """Test content hash computation."""
    content = b"test audio data"
    hash1 = Track.compute_content_hash(content)
    hash2 = Track.compute_content_hash(content)
    
    # Same content should produce same hash
    assert hash1 == hash2
    
    # Different content should produce different hash
    different_content = b"different audio data"
    hash3 = Track.compute_content_hash(different_content)
    assert hash1 != hash3


def test_track_metadata_hash():
    """Test metadata hash generation."""
    track = Track(
        title="Test Song",
        artist="Test Artist",
        content_hash="abc123",
        duration=180,
        size=5000000,
    )
    
    hash1 = track.get_metadata_hash()
    hash2 = track.get_metadata_hash()
    
    # Same metadata should produce same hash
    assert hash1 == hash2


def test_track_to_dict():
    """Test track serialization to dictionary."""
    track = Track(
        title="Test Song",
        artist="Test Artist",
        content_hash="abc123",
        duration=180,
        size=5000000,
        album="Test Album",
    )
    
    track_dict = track.to_dict()
    
    assert track_dict["title"] == "Test Song"
    assert track_dict["artist"] == "Test Artist"
    assert track_dict["content_hash"] == "abc123"
    assert track_dict["album"] == "Test Album"


def test_track_from_dict():
    """Test track deserialization from dictionary."""
    track_dict = {
        "title": "Test Song",
        "artist": "Test Artist",
        "content_hash": "abc123",
        "duration": 180,
        "size": 5000000,
        "format": "mp3",
    }
    
    track = Track.from_dict(track_dict)
    
    assert track.title == "Test Song"
    assert track.artist == "Test Artist"
    assert track.content_hash == "abc123"
    assert track.duration == 180


def test_track_str_repr():
    """Test string representations."""
    track = Track(
        title="Test Song",
        artist="Test Artist",
        content_hash="abc123def456",
        duration=180,
        size=5000000,
        format="mp3",
    )
    
    str_repr = str(track)
    assert "Test Artist" in str_repr
    assert "Test Song" in str_repr
    
    repr_str = repr(track)
    assert "Track" in repr_str
    assert "Test Song" in repr_str
