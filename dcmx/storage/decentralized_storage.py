"""
Unified Decentralized Storage Manager

Combines Storj, Web3.Storage, and NFT.Storage for optimal storage strategy.
"""

import logging
from typing import Optional, Dict, Any, Literal
from pathlib import Path
import os

from dcmx.storage.storj_storage import StorjStorage
from dcmx.storage.ipfs_storage import Web3Storage, NFTStorage

logger = logging.getLogger(__name__)

StorageProvider = Literal["storj", "ipfs", "nft_storage", "auto"]


class DecentralizedStorageManager:
    """
    Unified storage manager for DCMX.
    
    Storage Strategy:
    - Storj: Primary storage for audio files (150GB free)
    - Web3.Storage: IPFS backup for content addressing (10GB free)
    - NFT.Storage: NFT metadata and artwork (unlimited free)
    """
    
    def __init__(
        self,
        storj_access_key: Optional[str] = None,
        storj_secret_key: Optional[str] = None,
        web3_storage_token: Optional[str] = None,
        nft_storage_token: Optional[str] = None,
        storj_bucket: str = "dcmx-music",
    ):
        """
        Initialize storage manager.
        
        Args:
            storj_access_key: Storj access key
            storj_secret_key: Storj secret key
            web3_storage_token: Web3.Storage API token
            nft_storage_token: NFT.Storage API token
            storj_bucket: Storj bucket name
        """
        # Initialize Storj (primary storage)
        self.storj: Optional[StorjStorage] = None
        if storj_access_key and storj_secret_key:
            self.storj = StorjStorage(
                access_key=storj_access_key,
                secret_key=storj_secret_key,
                bucket_name=storj_bucket,
            )
            logger.info("Storj storage enabled")
        
        # Initialize Web3.Storage (IPFS)
        self.ipfs: Optional[Web3Storage] = None
        if web3_storage_token:
            self.ipfs = Web3Storage(api_token=web3_storage_token)
            logger.info("Web3.Storage (IPFS) enabled")
        
        # Initialize NFT.Storage (NFT metadata)
        self.nft_storage: Optional[NFTStorage] = None
        if nft_storage_token:
            self.nft_storage = NFTStorage(api_token=nft_storage_token)
            logger.info("NFT.Storage enabled")
        
        logger.info("Decentralized storage manager initialized")
    
    @classmethod
    def from_env(cls) -> "DecentralizedStorageManager":
        """
        Create storage manager from environment variables.
        
        Environment Variables:
            STORJ_ACCESS_KEY: Storj access key
            STORJ_SECRET_KEY: Storj secret key
            WEB3_STORAGE_TOKEN: Web3.Storage API token
            NFT_STORAGE_TOKEN: NFT.Storage API token
            STORJ_BUCKET: Storj bucket name (default: dcmx-music)
        """
        return cls(
            storj_access_key=os.getenv("STORJ_ACCESS_KEY"),
            storj_secret_key=os.getenv("STORJ_SECRET_KEY"),
            web3_storage_token=os.getenv("WEB3_STORAGE_TOKEN"),
            nft_storage_token=os.getenv("NFT_STORAGE_TOKEN"),
            storj_bucket=os.getenv("STORJ_BUCKET", "dcmx-music"),
        )
    
    async def upload_audio_file(
        self,
        file_path: str,
        track_metadata: Optional[Dict[str, Any]] = None,
        include_ipfs: bool = True,
    ) -> Dict[str, Any]:
        """
        Upload audio file with optimal storage strategy.
        
        Strategy:
        1. Upload to Storj (primary, fast retrieval)
        2. Optionally upload to IPFS (backup, content addressing)
        
        Args:
            file_path: Path to audio file
            track_metadata: Track metadata (artist, title, etc.)
            include_ipfs: Also upload to IPFS for content addressing
            
        Returns:
            Upload results with URLs from all providers
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "File not found",
            }
        
        file_name = Path(file_path).name
        metadata = track_metadata or {}
        
        results = {
            "success": True,
            "file_name": file_name,
            "urls": {},
            "metadata": metadata,
        }
        
        # Upload to Storj (primary)
        if self.storj:
            storj_result = self.storj.upload_file(
                file_path=file_path,
                object_name=file_name,
                metadata={
                    "artist": metadata.get("artist", "Unknown"),
                    "title": metadata.get("title", file_name),
                    "album": metadata.get("album", ""),
                },
                content_type=self._get_audio_mime_type(file_path),
            )
            
            if storj_result["success"]:
                results["urls"]["storj"] = storj_result["url"]
                results["content_hash"] = storj_result["content_hash"]
                results["size"] = storj_result["size"]
                logger.info(f"✓ Uploaded to Storj: {file_name}")
            else:
                results["storj_error"] = storj_result.get("error")
        
        # Upload to IPFS (backup, optional)
        if include_ipfs and self.ipfs:
            ipfs_result = await self.ipfs.upload_file(
                file_path=file_path,
                name=file_name,
            )
            
            if ipfs_result["success"]:
                results["urls"]["ipfs"] = ipfs_result["ipfs_url"]
                results["urls"]["ipfs_gateway"] = ipfs_result["gateway_url"]
                results["ipfs_cid"] = ipfs_result["cid"]
                logger.info(f"✓ Uploaded to IPFS: {file_name}")
            else:
                results["ipfs_error"] = ipfs_result.get("error")
        
        return results
    
    async def upload_nft_metadata(
        self,
        track_title: str,
        artist: str,
        description: str,
        audio_url: str,
        artwork_cid: str,
        attributes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Upload NFT metadata to NFT.Storage.
        
        Args:
            track_title: Track title
            artist: Artist name
            description: Track description
            audio_url: Audio file URL (Storj or IPFS)
            artwork_cid: Artwork IPFS CID
            attributes: Additional attributes
            
        Returns:
            NFT metadata CID and URL
        """
        if not self.nft_storage:
            return {
                "success": False,
                "error": "NFT.Storage not configured",
            }
        
        # Add audio URL to attributes
        full_attributes = {
            "audio_url": audio_url,
            **attributes,
        }
        
        result = await self.nft_storage.upload_nft_metadata(
            name=f"{track_title} - {artist}",
            description=description,
            image_cid=artwork_cid,
            attributes=full_attributes,
        )
        
        if result["success"]:
            logger.info(f"✓ NFT metadata uploaded: {track_title}")
        
        return result
    
    async def upload_complete_track(
        self,
        audio_file_path: str,
        artwork_file_path: str,
        track_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Upload complete track package (audio + artwork + NFT metadata).
        
        Workflow:
        1. Upload artwork to IPFS → get CID
        2. Upload audio to Storj + IPFS → get URLs
        3. Create NFT metadata with all references → upload to NFT.Storage
        
        Args:
            audio_file_path: Path to audio file
            artwork_file_path: Path to artwork image
            track_metadata: Complete track metadata
            
        Returns:
            Complete upload results
        """
        results = {
            "success": True,
            "track": track_metadata,
        }
        
        # Step 1: Upload artwork to IPFS
        if self.ipfs:
            artwork_result = await self.ipfs.upload_file(
                file_path=artwork_file_path,
                name=Path(artwork_file_path).name,
            )
            
            if artwork_result["success"]:
                results["artwork_cid"] = artwork_result["cid"]
                results["artwork_url"] = artwork_result["gateway_url"]
                logger.info(f"✓ Artwork uploaded: {artwork_result['cid']}")
            else:
                return {
                    "success": False,
                    "error": "Failed to upload artwork",
                    "details": artwork_result,
                }
        
        # Step 2: Upload audio
        audio_result = await self.upload_audio_file(
            file_path=audio_file_path,
            track_metadata=track_metadata,
            include_ipfs=True,
        )
        
        if not audio_result["success"]:
            return {
                "success": False,
                "error": "Failed to upload audio",
                "details": audio_result,
            }
        
        results["audio_urls"] = audio_result["urls"]
        results["content_hash"] = audio_result.get("content_hash")
        
        # Step 3: Upload NFT metadata
        if self.nft_storage:
            nft_result = await self.upload_nft_metadata(
                track_title=track_metadata.get("title", "Unknown"),
                artist=track_metadata.get("artist", "Unknown"),
                description=track_metadata.get("description", ""),
                audio_url=audio_result["urls"].get("storj", ""),
                artwork_cid=results.get("artwork_cid", ""),
                attributes={
                    "album": track_metadata.get("album", ""),
                    "duration": track_metadata.get("duration", 0),
                    "genre": track_metadata.get("genre", ""),
                    "year": track_metadata.get("year", ""),
                    "content_hash": results.get("content_hash", ""),
                    "ipfs_audio": audio_result["urls"].get("ipfs", ""),
                },
            )
            
            if nft_result["success"]:
                results["nft_metadata_cid"] = nft_result["cid"]
                results["nft_metadata_url"] = nft_result["gateway_url"]
                logger.info(f"✓ Complete track uploaded: {track_metadata.get('title')}")
            else:
                results["nft_metadata_error"] = nft_result.get("error")
        
        return results
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics from all providers.
        
        Returns:
            Combined storage stats
        """
        stats = {}
        
        if self.storj:
            stats["storj"] = self.storj.get_storage_stats()
        
        return stats
    
    async def cleanup(self) -> None:
        """Close all storage connections."""
        if self.ipfs:
            await self.ipfs.close()
        if self.nft_storage:
            await self.nft_storage.close()
        
        logger.info("Storage manager closed")
    
    def _get_audio_mime_type(self, file_path: str) -> str:
        """Determine audio MIME type from file extension."""
        ext = Path(file_path).suffix.lower()
        
        mime_types = {
            ".mp3": "audio/mpeg",
            ".flac": "audio/flac",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".aac": "audio/aac",
            ".ogg": "audio/ogg",
        }
        
        return mime_types.get(ext, "application/octet-stream")
