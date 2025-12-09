"""
DCMX Web3 Storage Integration

Integrates with decentralized storage solutions:
- Filecoin (long-term archival)
- IPFS (content addressing)
- Arweave (permanent storage)
- Local caching layer

Provides:
- Content upload/download
- Automatic replication
- Redundancy management
"""

import logging
import asyncio
import hashlib
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class StorageProvider(Enum):
    """Supported storage providers."""
    IPFS = "ipfs"
    FILECOIN = "filecoin"
    ARWEAVE = "arweave"
    LOCAL = "local"


@dataclass
class StorageConfig:
    """Storage provider configuration."""
    provider: StorageProvider
    endpoint_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    redundancy_copies: int = 3  # Number of replicas


@dataclass
class StoredContent:
    """Metadata for stored content."""
    content_hash: str
    content_id: str  # Provider-specific ID
    provider: StorageProvider
    size_bytes: int
    timestamp: str
    replicas: List[str]  # IDs on other providers
    is_encrypted: bool = False
    encryption_key: Optional[str] = None


class Web3StorageManager:
    """
    Manage content across Web3 storage providers.
    
    Provides:
    - Unified API for multiple providers
    - Automatic failover
    - Content replication
    - Encryption support
    """
    
    def __init__(self):
        """Initialize storage manager."""
        self.providers: Dict[StorageProvider, StorageConfig] = {}
        self.content_registry: Dict[str, StoredContent] = {}
        self.local_cache: Dict[str, bytes] = {}
    
    def configure_provider(
        self,
        provider: StorageProvider,
        endpoint_url: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        redundancy_copies: int = 3,
    ):
        """Configure storage provider."""
        config = StorageConfig(
            provider=provider,
            endpoint_url=endpoint_url,
            api_key=api_key,
            api_secret=api_secret,
            redundancy_copies=redundancy_copies,
        )
        self.providers[provider] = config
        logger.info(f"Storage provider configured: {provider.value}")
    
    def calculate_content_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()
    
    async def upload_content(
        self,
        content: bytes,
        content_type: str = "audio/mpeg",
        encrypt: bool = False,
        encryption_key: Optional[str] = None,
    ) -> StoredContent:
        """
        Upload content to storage providers.
        
        Automatically replicates across configured providers.
        """
        content_hash = self.calculate_content_hash(content)
        
        # Check if already stored
        if content_hash in self.content_registry:
            logger.info(f"Content already stored: {content_hash[:16]}...")
            return self.content_registry[content_hash]
        
        # Encrypt if requested
        if encrypt:
            content = self._encrypt_content(content, encryption_key)
        
        # Upload to primary provider
        primary_provider = list(self.providers.keys())[0]
        content_id = await self._upload_to_provider(
            primary_provider,
            content,
            content_type,
        )
        
        replicas = [content_id]
        
        # Replicate to other providers
        for provider in list(self.providers.keys())[1:]:
            try:
                replica_id = await self._upload_to_provider(
                    provider,
                    content,
                    content_type,
                )
                replicas.append(replica_id)
            except Exception as e:
                logger.warning(f"Failed to replicate to {provider.value}: {e}")
        
        # Register content
        stored = StoredContent(
            content_hash=content_hash,
            content_id=content_id,
            provider=primary_provider,
            size_bytes=len(content),
            timestamp=__import__("datetime").datetime.utcnow().isoformat(),
            replicas=replicas,
            is_encrypted=encrypt,
            encryption_key=encryption_key,
        )
        
        self.content_registry[content_hash] = stored
        
        # Cache locally
        self.local_cache[content_hash] = content
        
        logger.info(
            f"Content uploaded: {content_hash[:16]}... "
            f"({len(content)} bytes, {len(replicas)} replicas)"
        )
        
        return stored
    
    async def download_content(
        self,
        content_hash: str,
    ) -> Optional[bytes]:
        """
        Download content from storage.
        
        Tries local cache first, then primary provider, then replicas.
        """
        # Check local cache
        if content_hash in self.local_cache:
            logger.info(f"Content loaded from cache: {content_hash[:16]}...")
            return self.local_cache[content_hash]
        
        # Check registry
        if content_hash not in self.content_registry:
            logger.warning(f"Content not found: {content_hash[:16]}...")
            return None
        
        stored = self.content_registry[content_hash]
        
        # Try primary provider
        try:
            content = await self._download_from_provider(
                stored.provider,
                stored.content_id,
            )
            
            # Decrypt if needed
            if stored.is_encrypted:
                content = self._decrypt_content(content, stored.encryption_key)
            
            # Cache locally
            self.local_cache[content_hash] = content
            
            logger.info(f"Content downloaded: {content_hash[:16]}... ({len(content)} bytes)")
            return content
        
        except Exception as e:
            logger.warning(f"Failed to download from primary provider: {e}")
        
        # Try replicas
        for replica_id in stored.replicas[1:]:
            try:
                # Infer provider from replica_id format
                for provider, config in self.providers.items():
                    try:
                        content = await self._download_from_provider(provider, replica_id)
                        
                        if stored.is_encrypted:
                            content = self._decrypt_content(content, stored.encryption_key)
                        
                        self.local_cache[content_hash] = content
                        
                        logger.info(f"Content recovered from replica: {content_hash[:16]}...")
                        return content
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Replica download failed: {e}")
        
        logger.error(f"Could not retrieve content: {content_hash[:16]}...")
        return None
    
    async def _upload_to_provider(
        self,
        provider: StorageProvider,
        content: bytes,
        content_type: str,
    ) -> str:
        """Upload content to specific provider."""
        config = self.providers[provider]
        
        if provider == StorageProvider.IPFS:
            # IPFS: ipfs.io
            import requests
            response = requests.post(
                f"{config.endpoint_url}/api/v0/add",
                files={"file": content},
                params={"wrap-with-directory": "true"},
                timeout=30,
            )
            if response.status_code == 200:
                return response.json()["Hash"]
        
        elif provider == StorageProvider.FILECOIN:
            # Filecoin via Web3.Storage
            import requests
            headers = {"Authorization": f"Bearer {config.api_key}"}
            response = requests.post(
                f"{config.endpoint_url}/upload",
                files={"file": content},
                headers=headers,
                timeout=60,
            )
            if response.status_code == 200:
                return response.json()["cid"]
        
        elif provider == StorageProvider.ARWEAVE:
            # Arweave: permanent storage
            import requests
            headers = {"Authorization": f"Bearer {config.api_key}"}
            response = requests.post(
                f"{config.endpoint_url}/tx",
                data=content,
                headers=headers,
                timeout=60,
            )
            if response.status_code == 200:
                return response.json()["id"]
        
        elif provider == StorageProvider.LOCAL:
            # Local filesystem storage
            import hashlib
            content_hash = hashlib.sha256(content).hexdigest()
            storage_path = Path("/tmp/dcmx_storage") / content_hash[:2] / content_hash
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            storage_path.write_bytes(content)
            return str(storage_path)
        
        raise ValueError(f"Unsupported provider: {provider}")
    
    async def _download_from_provider(
        self,
        provider: StorageProvider,
        content_id: str,
    ) -> bytes:
        """Download content from specific provider."""
        config = self.providers[provider]
        
        if provider == StorageProvider.IPFS:
            import requests
            response = requests.get(
                f"{config.endpoint_url}/ipfs/{content_id}",
                timeout=30,
            )
            if response.status_code == 200:
                return response.content
        
        elif provider == StorageProvider.FILECOIN:
            import requests
            headers = {"Authorization": f"Bearer {config.api_key}"}
            response = requests.get(
                f"{config.endpoint_url}/download/{content_id}",
                headers=headers,
                timeout=60,
            )
            if response.status_code == 200:
                return response.content
        
        elif provider == StorageProvider.ARWEAVE:
            import requests
            response = requests.get(
                f"{config.endpoint_url}/{content_id}",
                timeout=60,
            )
            if response.status_code == 200:
                return response.content
        
        elif provider == StorageProvider.LOCAL:
            path = Path(content_id)
            if path.exists():
                return path.read_bytes()
        
        raise ValueError(f"Could not download from {provider}")
    
    def _encrypt_content(self, content: bytes, key: Optional[str]) -> bytes:
        """Encrypt content using AES-256."""
        from cryptography.fernet import Fernet
        
        if not key:
            key = Fernet.generate_key()
        
        cipher = Fernet(key)
        return cipher.encrypt(content)
    
    def _decrypt_content(self, encrypted: bytes, key: str) -> bytes:
        """Decrypt content."""
        from cryptography.fernet import Fernet
        
        cipher = Fernet(key.encode() if isinstance(key, str) else key)
        return cipher.decrypt(encrypted)
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        total_content = len(self.content_registry)
        total_size = sum(c.size_bytes for c in self.content_registry.values())
        cache_size = sum(len(c) for c in self.local_cache.values())
        replicas = sum(len(c.replicas) for c in self.content_registry.values())
        
        return {
            "total_content_items": total_content,
            "total_size_bytes": total_size,
            "cache_size_bytes": cache_size,
            "total_replicas": replicas,
            "providers_configured": len(self.providers),
        }
