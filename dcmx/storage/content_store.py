"""Content storage for distributed music files."""

import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class ContentStore:
    """
    Manages local storage of music content.
    
    Content is stored in a content-addressed manner using the
    content hash as the filename.
    """
    
    def __init__(self, storage_path: Path):
        """
        Initialize content store.
        
        Args:
            storage_path: Directory path for storing content
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Content store initialized at {self.storage_path}")
    
    def _get_content_path(self, content_hash: str) -> Path:
        """
        Get the file path for a content hash.
        
        Args:
            content_hash: Content hash
            
        Returns:
            Path object for the content file
        """
        # Use first 2 characters as subdirectory for better file system performance
        subdir = self.storage_path / content_hash[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / content_hash
    
    def store(self, content_hash: str, content: bytes) -> bool:
        """
        Store content with the given hash.
        
        Args:
            content_hash: Content hash
            content: Content bytes
            
        Returns:
            True if successful
        """
        try:
            path = self._get_content_path(content_hash)
            
            # Don't overwrite if already exists
            if path.exists():
                logger.debug(f"Content {content_hash[:16]}... already exists")
                return True
            
            path.write_bytes(content)
            logger.info(f"Stored content {content_hash[:16]}... ({len(content)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Failed to store content {content_hash[:16]}...: {e}")
            return False
    
    def retrieve(self, content_hash: str) -> Optional[bytes]:
        """
        Retrieve content by hash.
        
        Args:
            content_hash: Content hash
            
        Returns:
            Content bytes if found, None otherwise
        """
        try:
            path = self._get_content_path(content_hash)
            
            if not path.exists():
                logger.debug(f"Content {content_hash[:16]}... not found")
                return None
            
            content = path.read_bytes()
            logger.debug(f"Retrieved content {content_hash[:16]}... ({len(content)} bytes)")
            return content
        except Exception as e:
            logger.error(f"Failed to retrieve content {content_hash[:16]}...: {e}")
            return None
    
    def has_content(self, content_hash: str) -> bool:
        """
        Check if content exists in storage.
        
        Args:
            content_hash: Content hash
            
        Returns:
            True if content exists
        """
        path = self._get_content_path(content_hash)
        return path.exists()
    
    def delete(self, content_hash: str) -> bool:
        """
        Delete content from storage.
        
        Args:
            content_hash: Content hash
            
        Returns:
            True if successful
        """
        try:
            path = self._get_content_path(content_hash)
            
            if path.exists():
                path.unlink()
                logger.info(f"Deleted content {content_hash[:16]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete content {content_hash[:16]}...: {e}")
            return False
    
    def get_size(self) -> int:
        """
        Get total size of stored content.
        
        Returns:
            Total size in bytes
        """
        total = 0
        try:
            for path in self.storage_path.rglob("*"):
                if path.is_file():
                    total += path.stat().st_size
        except Exception as e:
            logger.error(f"Failed to calculate storage size: {e}")
        return total
    
    def list_content(self) -> list:
        """
        List all stored content hashes.
        
        Returns:
            List of content hashes
        """
        hashes = []
        try:
            for path in self.storage_path.rglob("*"):
                if path.is_file():
                    hashes.append(path.name)
        except Exception as e:
            logger.error(f"Failed to list content: {e}")
        return hashes
