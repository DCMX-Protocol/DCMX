"""Tests for ContentStore functionality."""

import pytest
import tempfile
from pathlib import Path
from dcmx.storage.content_store import ContentStore


@pytest.fixture
def temp_storage():
    """Create temporary storage directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_content_store_creation(temp_storage):
    """Test content store initialization."""
    store = ContentStore(temp_storage / "content")
    assert store.storage_path.exists()


def test_store_and_retrieve_content(temp_storage):
    """Test storing and retrieving content."""
    store = ContentStore(temp_storage / "content")
    
    content = b"test audio content data"
    content_hash = "abc123def456"
    
    # Store content
    result = store.store(content_hash, content)
    assert result is True
    
    # Retrieve content
    retrieved = store.retrieve(content_hash)
    assert retrieved == content


def test_has_content(temp_storage):
    """Test checking if content exists."""
    store = ContentStore(temp_storage / "content")
    
    content_hash = "abc123"
    content = b"test data"
    
    assert store.has_content(content_hash) is False
    
    store.store(content_hash, content)
    assert store.has_content(content_hash) is True


def test_store_duplicate_content(temp_storage):
    """Test storing duplicate content doesn't overwrite."""
    store = ContentStore(temp_storage / "content")
    
    content1 = b"original content"
    content2 = b"different content"
    content_hash = "abc123"
    
    # Store original
    store.store(content_hash, content1)
    
    # Try to store different content with same hash
    store.store(content_hash, content2)
    
    # Should still have original content
    retrieved = store.retrieve(content_hash)
    assert retrieved == content1


def test_retrieve_nonexistent_content(temp_storage):
    """Test retrieving content that doesn't exist."""
    store = ContentStore(temp_storage / "content")
    
    retrieved = store.retrieve("nonexistent_hash")
    assert retrieved is None


def test_delete_content(temp_storage):
    """Test deleting content."""
    store = ContentStore(temp_storage / "content")
    
    content_hash = "abc123"
    content = b"test data"
    
    store.store(content_hash, content)
    assert store.has_content(content_hash) is True
    
    result = store.delete(content_hash)
    assert result is True
    assert store.has_content(content_hash) is False


def test_delete_nonexistent_content(temp_storage):
    """Test deleting content that doesn't exist."""
    store = ContentStore(temp_storage / "content")
    
    result = store.delete("nonexistent_hash")
    assert result is False


def test_get_storage_size(temp_storage):
    """Test calculating total storage size."""
    store = ContentStore(temp_storage / "content")
    
    # Initially empty
    assert store.get_size() == 0
    
    # Add some content
    content1 = b"x" * 1000
    content2 = b"y" * 2000
    
    store.store("hash1", content1)
    store.store("hash2", content2)
    
    total_size = store.get_size()
    assert total_size == 3000


def test_list_content(temp_storage):
    """Test listing all stored content."""
    store = ContentStore(temp_storage / "content")
    
    # Initially empty
    assert len(store.list_content()) == 0
    
    # Add some content
    store.store("hash1", b"content1")
    store.store("hash2", b"content2")
    store.store("hash3", b"content3")
    
    content_list = store.list_content()
    assert len(content_list) == 3
    assert "hash1" in content_list
    assert "hash2" in content_list
    assert "hash3" in content_list


def test_subdirectory_organization(temp_storage):
    """Test that content is organized in subdirectories."""
    store = ContentStore(temp_storage / "content")
    
    # Store content with hash starting with "ab"
    content_hash = "abc123def456"
    store.store(content_hash, b"test")
    
    # Check that subdirectory was created
    subdir = store.storage_path / "ab"
    assert subdir.exists()
    assert (subdir / content_hash).exists()
