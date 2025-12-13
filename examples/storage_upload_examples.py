"""
Example: Upload Music Library to Decentralized Storage

Demonstrates batch uploading 150+ songs to Storj + IPFS + NFT.Storage
"""

import asyncio
from dcmx.storage.batch_uploader import upload_music_library


async def example_basic_upload():
    """Example: Upload all songs from a directory."""
    
    print("Example 1: Basic Upload")
    print("=" * 60)
    
    # Upload all MP3 files from music directory
    summary = await upload_music_library(
        music_dir="/path/to/your/music",
        max_concurrent=5,  # Upload 5 files at once
    )
    
    print(f"\n✓ Uploaded {summary['successful']} songs")
    print(f"Total size: {summary['total_size_mb']:.2f} MB")


async def example_upload_with_artwork():
    """Example: Upload songs with matching artwork."""
    
    print("\nExample 2: Upload with Artwork")
    print("=" * 60)
    
    # Upload songs + artwork (will auto-match by filename)
    summary = await upload_music_library(
        music_dir="/path/to/music",
        artwork_dir="/path/to/artwork",  # Same filename, e.g., song1.mp3 → song1.jpg
        max_concurrent=3,
    )
    
    print(f"\n✓ Uploaded {summary['successful']} songs with artwork")


async def example_upload_with_metadata():
    """Example: Upload with custom metadata from JSON file."""
    
    print("\nExample 3: Upload with Metadata")
    print("=" * 60)
    
    # Create metadata.json:
    # {
    #   "song1": {"artist": "Artist Name", "title": "Song Title", "album": "Album"},
    #   "song2": {"artist": "Another Artist", "title": "Another Song"},
    #   ...
    # }
    
    summary = await upload_music_library(
        music_dir="/path/to/music",
        artwork_dir="/path/to/artwork",
        metadata_file="/path/to/metadata.json",
        max_concurrent=5,
    )
    
    print(f"\n✓ Uploaded {summary['successful']} songs with metadata")


async def example_custom_upload():
    """Example: Custom upload with full control."""
    
    from dcmx.storage.decentralized_storage import DecentralizedStorageManager
    from dcmx.storage.batch_uploader import BatchUploader
    
    print("\nExample 4: Custom Upload")
    print("=" * 60)
    
    # Initialize storage manager
    storage = DecentralizedStorageManager.from_env()
    
    # Create batch uploader
    uploader = BatchUploader(
        storage_manager=storage,
        max_concurrent=5,
    )
    
    # Custom track list
    track_list = [
        {
            "audio_path": "/path/to/song1.mp3",
            "artwork_path": "/path/to/cover1.jpg",
            "metadata": {
                "artist": "Your Name",
                "title": "Song Title 1",
                "album": "My Album",
                "genre": "Electronic",
                "year": "2025",
            },
        },
        {
            "audio_path": "/path/to/song2.flac",
            "artwork_path": "/path/to/cover2.jpg",
            "metadata": {
                "artist": "Your Name",
                "title": "Song Title 2",
                "album": "My Album",
                "genre": "Electronic",
                "year": "2025",
            },
        },
        # ... 148 more songs
    ]
    
    # Upload
    summary = await uploader.upload_track_list(track_list)
    
    # Print results
    uploader.print_summary()
    
    # Save report
    uploader.save_report("my_upload_report.json")
    
    # Cleanup
    await storage.cleanup()
    
    print(f"\n✓ Custom upload complete")


async def example_single_track():
    """Example: Upload a single complete track."""
    
    from dcmx.storage.decentralized_storage import DecentralizedStorageManager
    
    print("\nExample 5: Single Track Upload")
    print("=" * 60)
    
    # Initialize storage
    storage = DecentralizedStorageManager.from_env()
    
    # Upload complete track (audio + artwork + NFT metadata)
    result = await storage.upload_complete_track(
        audio_file_path="/path/to/song.mp3",
        artwork_file_path="/path/to/cover.jpg",
        track_metadata={
            "artist": "Your Name",
            "title": "Amazing Song",
            "album": "Best Album",
            "description": "Limited edition track #1",
            "genre": "Electronic",
            "year": "2025",
            "duration": 180,  # seconds
        },
    )
    
    if result["success"]:
        print("\n✓ Track uploaded successfully!")
        print(f"  Storj URL:     {result['audio_urls'].get('storj')}")
        print(f"  IPFS URL:      {result['audio_urls'].get('ipfs')}")
        print(f"  Artwork CID:   {result.get('artwork_cid')}")
        print(f"  NFT Metadata:  {result.get('nft_metadata_url')}")
        print(f"  Content Hash:  {result.get('content_hash')}")
    
    await storage.cleanup()


async def example_check_storage_stats():
    """Example: Check storage usage."""
    
    from dcmx.storage.decentralized_storage import DecentralizedStorageManager
    
    print("\nExample 6: Storage Statistics")
    print("=" * 60)
    
    storage = DecentralizedStorageManager.from_env()
    
    stats = storage.get_storage_stats()
    
    if "storj" in stats:
        storj_stats = stats["storj"]
        print(f"\nStorj Storage:")
        print(f"  Total files:   {storj_stats['total_files']}")
        print(f"  Total size:    {storj_stats['total_size_gb']:.2f} GB")
        print(f"  Free tier:     150 GB")
        print(f"  Usage:         {storj_stats['usage_percentage']:.1f}%")
    
    await storage.cleanup()


if __name__ == "__main__":
    print("=" * 60)
    print("DCMX Decentralized Storage Examples")
    print("=" * 60)
    print()
    
    # Set up your environment variables first:
    # export STORJ_ACCESS_KEY="your_key"
    # export STORJ_SECRET_KEY="your_secret"
    # export WEB3_STORAGE_TOKEN="your_token"
    # export NFT_STORAGE_TOKEN="your_token"
    
    # Run examples (uncomment the one you want to try)
    
    # asyncio.run(example_basic_upload())
    # asyncio.run(example_upload_with_artwork())
    # asyncio.run(example_upload_with_metadata())
    # asyncio.run(example_custom_upload())
    # asyncio.run(example_single_track())
    asyncio.run(example_check_storage_stats())
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
