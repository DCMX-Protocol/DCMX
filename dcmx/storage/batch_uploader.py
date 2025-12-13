"""
Batch Upload Utility for DCMX Music Library

Upload multiple songs at once to decentralized storage.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from dcmx.storage.decentralized_storage import DecentralizedStorageManager

logger = logging.getLogger(__name__)


class BatchUploader:
    """
    Batch upload utility for music libraries.
    
    Features:
    - Upload multiple tracks simultaneously
    - Progress tracking
    - Error handling and retry
    - Upload report generation
    """
    
    def __init__(
        self,
        storage_manager: DecentralizedStorageManager,
        max_concurrent: int = 5,
    ):
        """
        Initialize batch uploader.
        
        Args:
            storage_manager: Decentralized storage manager
            max_concurrent: Maximum concurrent uploads
        """
        self.storage = storage_manager
        self.max_concurrent = max_concurrent
        self.results: List[Dict[str, Any]] = []
        
        logger.info(f"Batch uploader initialized (max concurrent: {max_concurrent})")
    
    async def upload_directory(
        self,
        music_dir: str,
        artwork_dir: Optional[str] = None,
        metadata_file: Optional[str] = None,
        audio_extensions: List[str] = [".mp3", ".flac", ".wav", ".m4a"],
    ) -> Dict[str, Any]:
        """
        Upload all audio files from a directory.
        
        Args:
            music_dir: Directory containing audio files
            artwork_dir: Directory containing artwork (optional)
            metadata_file: JSON file with track metadata (optional)
            audio_extensions: Audio file extensions to process
            
        Returns:
            Upload summary
        """
        music_path = Path(music_dir)
        
        if not music_path.exists():
            logger.error(f"Directory not found: {music_dir}")
            return {
                "success": False,
                "error": "Directory not found",
            }
        
        # Load metadata if provided
        metadata_map = {}
        if metadata_file and Path(metadata_file).exists():
            with open(metadata_file, 'r') as f:
                metadata_map = json.load(f)
        
        # Find all audio files
        audio_files = []
        for ext in audio_extensions:
            audio_files.extend(music_path.glob(f"*{ext}"))
        
        logger.info(f"Found {len(audio_files)} audio files to upload")
        
        if not audio_files:
            return {
                "success": False,
                "error": "No audio files found",
            }
        
        # Upload in batches
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = []
        
        for audio_file in audio_files:
            task = self._upload_single_track(
                audio_file=audio_file,
                artwork_dir=artwork_dir,
                metadata=metadata_map.get(audio_file.stem, {}),
                semaphore=semaphore,
            )
            tasks.append(task)
        
        # Execute all uploads
        self.results = await asyncio.gather(*tasks)
        
        # Generate summary
        summary = self._generate_summary()
        
        logger.info(
            f"Batch upload complete: {summary['successful']}/{summary['total']} successful"
        )
        
        return summary
    
    async def upload_track_list(
        self,
        track_list: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Upload tracks from a list of file paths and metadata.
        
        Args:
            track_list: List of dicts with 'audio_path', 'artwork_path', 'metadata'
            
        Example:
            track_list = [
                {
                    "audio_path": "/path/to/song1.mp3",
                    "artwork_path": "/path/to/artwork1.jpg",
                    "metadata": {"artist": "Artist 1", "title": "Song 1"}
                },
                ...
            ]
            
        Returns:
            Upload summary
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = []
        
        for track in track_list:
            audio_file = Path(track["audio_path"])
            artwork_file = Path(track.get("artwork_path", "")) if track.get("artwork_path") else None
            
            task = self._upload_complete_track(
                audio_file=audio_file,
                artwork_file=artwork_file,
                metadata=track.get("metadata", {}),
                semaphore=semaphore,
            )
            tasks.append(task)
        
        self.results = await asyncio.gather(*tasks)
        
        summary = self._generate_summary()
        logger.info(f"Track list upload complete: {summary['successful']}/{summary['total']}")
        
        return summary
    
    async def _upload_single_track(
        self,
        audio_file: Path,
        artwork_dir: Optional[str],
        metadata: Dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:
        """Upload single track with semaphore for concurrency control."""
        async with semaphore:
            try:
                # Find matching artwork
                artwork_file = None
                if artwork_dir:
                    artwork_path = Path(artwork_dir)
                    # Look for matching artwork (same name, different extension)
                    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                        potential_artwork = artwork_path / f"{audio_file.stem}{ext}"
                        if potential_artwork.exists():
                            artwork_file = potential_artwork
                            break
                
                # Fill in default metadata
                full_metadata = {
                    "title": metadata.get("title", audio_file.stem),
                    "artist": metadata.get("artist", "Unknown Artist"),
                    "album": metadata.get("album", ""),
                    "description": metadata.get("description", f"Track: {audio_file.stem}"),
                    **metadata,
                }
                
                logger.info(f"Uploading: {audio_file.name}")
                
                # Upload complete track if artwork exists
                if artwork_file:
                    result = await self.storage.upload_complete_track(
                        audio_file_path=str(audio_file),
                        artwork_file_path=str(artwork_file),
                        track_metadata=full_metadata,
                    )
                else:
                    # Upload audio only
                    result = await self.storage.upload_audio_file(
                        file_path=str(audio_file),
                        track_metadata=full_metadata,
                        include_ipfs=True,
                    )
                
                result["file_name"] = audio_file.name
                return result
                
            except Exception as e:
                logger.error(f"Error uploading {audio_file.name}: {e}")
                return {
                    "success": False,
                    "file_name": audio_file.name,
                    "error": str(e),
                }
    
    async def _upload_complete_track(
        self,
        audio_file: Path,
        artwork_file: Optional[Path],
        metadata: Dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> Dict[str, Any]:
        """Upload complete track (audio + artwork + metadata)."""
        async with semaphore:
            try:
                logger.info(f"Uploading complete track: {audio_file.name}")
                
                if artwork_file and artwork_file.exists():
                    result = await self.storage.upload_complete_track(
                        audio_file_path=str(audio_file),
                        artwork_file_path=str(artwork_file),
                        track_metadata=metadata,
                    )
                else:
                    result = await self.storage.upload_audio_file(
                        file_path=str(audio_file),
                        track_metadata=metadata,
                        include_ipfs=True,
                    )
                
                result["file_name"] = audio_file.name
                return result
                
            except Exception as e:
                logger.error(f"Error uploading {audio_file.name}: {e}")
                return {
                    "success": False,
                    "file_name": audio_file.name,
                    "error": str(e),
                }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate upload summary report."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.get("success", False))
        failed = total - successful
        
        total_size = sum(r.get("size", 0) for r in self.results if r.get("success"))
        
        failed_files = [
            {
                "file": r.get("file_name", "unknown"),
                "error": r.get("error", "Unknown error"),
            }
            for r in self.results
            if not r.get("success", False)
        ]
        
        return {
            "success": failed == 0,
            "total": total,
            "successful": successful,
            "failed": failed,
            "total_size_mb": total_size / 1024 / 1024,
            "failed_files": failed_files,
            "results": self.results,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def save_report(self, output_file: str = "upload_report.json") -> None:
        """
        Save upload report to JSON file.
        
        Args:
            output_file: Output file path
        """
        summary = self._generate_summary()
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Upload report saved: {output_file}")
    
    def print_summary(self) -> None:
        """Print upload summary to console."""
        summary = self._generate_summary()
        
        print("\n" + "=" * 60)
        print("BATCH UPLOAD SUMMARY")
        print("=" * 60)
        print(f"Total files:     {summary['total']}")
        print(f"Successful:      {summary['successful']} ✓")
        print(f"Failed:          {summary['failed']}")
        print(f"Total size:      {summary['total_size_mb']:.2f} MB")
        print(f"Timestamp:       {summary['timestamp']}")
        
        if summary['failed_files']:
            print("\nFailed uploads:")
            for failed in summary['failed_files']:
                print(f"  ✗ {failed['file']}: {failed['error']}")
        
        print("=" * 60 + "\n")


async def upload_music_library(
    music_dir: str,
    artwork_dir: Optional[str] = None,
    metadata_file: Optional[str] = None,
    max_concurrent: int = 5,
) -> Dict[str, Any]:
    """
    Convenience function to upload entire music library.
    
    Args:
        music_dir: Directory with audio files
        artwork_dir: Directory with artwork images
        metadata_file: JSON file with track metadata
        max_concurrent: Max concurrent uploads
        
    Returns:
        Upload summary
    """
    # Initialize storage manager from environment
    storage = DecentralizedStorageManager.from_env()
    
    # Create batch uploader
    uploader = BatchUploader(
        storage_manager=storage,
        max_concurrent=max_concurrent,
    )
    
    # Upload directory
    summary = await uploader.upload_directory(
        music_dir=music_dir,
        artwork_dir=artwork_dir,
        metadata_file=metadata_file,
    )
    
    # Print summary
    uploader.print_summary()
    
    # Save report
    uploader.save_report()
    
    # Cleanup
    await storage.cleanup()
    
    return summary
