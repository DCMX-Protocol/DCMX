# Decentralized Storage Setup Guide

## Overview

We're implementing **three free decentralized storage providers** to handle your 150+ song library:

| Provider | Free Tier | Purpose | Total Capacity |
|----------|-----------|---------|----------------|
| **Storj DCS** | 150GB storage + 150GB bandwidth/month | Primary audio storage (S3-compatible) | 150 GB |
| **Web3.Storage** | 10GB storage + 10GB bandwidth/month | IPFS backup for audio | 10 GB |
| **NFT.Storage** | Unlimited | NFT metadata storage | Unlimited |
| **TOTAL** | - | - | **260+ GB FREE** |

## Quick Start

### 1. Install Dependencies

```bash
pip install boto3 botocore aiofiles aiohttp
```

Or run the setup script:

```bash
./scripts/setup_storage.sh
```

### 2. Obtain API Keys

#### Storj DCS (Primary Storage)

1. Sign up: https://www.storj.io/signup
2. Create an account and verify email
3. In Dashboard → Access → **Create S3 Credentials**:
   - Name: `DCMX Music Storage`
   - Permissions: **All**
   - Buckets: **All** (or create `dcmx-music`)
4. Copy **Access Key** and **Secret Key**

#### Web3.Storage (IPFS Backup)

1. Sign up: https://web3.storage
2. Create account with email or GitHub
3. In Account → API Tokens → **Create Token**:
   - Name: `DCMX IPFS Storage`
4. Copy **API Token**

#### NFT.Storage (Metadata)

1. Sign up: https://nft.storage
2. Create account with email or GitHub
3. In Account → API Keys → **New Key**:
   - Name: `DCMX NFT Metadata`
4. Copy **API Key**

### 3. Configure Environment

Create `.env` file (or copy from `.env.storage.example`):

```bash
# Storj DCS
STORJ_ACCESS_KEY=your_access_key_here
STORJ_SECRET_KEY=your_secret_key_here
STORJ_BUCKET=dcmx-music

# Web3.Storage
WEB3_STORAGE_TOKEN=your_web3_storage_token_here

# NFT.Storage
NFT_STORAGE_TOKEN=your_nft_storage_token_here

# Upload settings
MAX_CONCURRENT_UPLOADS=5
INCLUDE_IPFS_BACKUP=true
```

### 4. Verify Setup

Test connection:

```python
from dcmx.storage.decentralized_storage import DecentralizedStorageManager
import asyncio

async def test():
    storage = DecentralizedStorageManager.from_env()
    stats = storage.get_storage_stats()
    print(f"Storj connected: {stats.get('storj', {}).get('connected', False)}")
    await storage.cleanup()

asyncio.run(test())
```

## Usage Examples

### Upload Single Track

```python
from dcmx.storage.decentralized_storage import DecentralizedStorageManager
import asyncio

async def upload_track():
    storage = DecentralizedStorageManager.from_env()
    
    result = await storage.upload_complete_track(
        audio_file_path="/path/to/song.mp3",
        artwork_file_path="/path/to/cover.jpg",
        track_metadata={
            "artist": "Your Name",
            "title": "Song Title",
            "album": "Album Name",
            "description": "Limited edition #1",
            "genre": "Electronic",
            "year": "2025",
        }
    )
    
    if result["success"]:
        print(f"✓ Uploaded successfully!")
        print(f"  Storj URL: {result['audio_urls'].get('storj')}")
        print(f"  IPFS CID:  {result['audio_urls'].get('ipfs')}")
        print(f"  NFT URL:   {result.get('nft_metadata_url')}")
    
    await storage.cleanup()

asyncio.run(upload_track())
```

### Batch Upload Music Library

```python
from dcmx.storage.batch_uploader import upload_music_library
import asyncio

async def upload_library():
    summary = await upload_music_library(
        music_dir="/path/to/your/music",
        artwork_dir="/path/to/artwork",  # Optional
        max_concurrent=5,  # Upload 5 files at once
    )
    
    print(f"✓ Uploaded {summary['successful']}/{summary['total']} tracks")
    print(f"Total size: {summary['total_size_mb']:.2f} MB")

asyncio.run(upload_library())
```

### Upload with Metadata File

Create `metadata.json`:

```json
{
  "song1": {
    "artist": "Artist Name",
    "title": "Song Title 1",
    "album": "Album Name",
    "genre": "Electronic",
    "year": "2025"
  },
  "song2": {
    "artist": "Artist Name",
    "title": "Song Title 2",
    "album": "Album Name",
    "genre": "Electronic",
    "year": "2025"
  }
}
```

Then upload:

```python
from dcmx.storage.batch_uploader import upload_music_library
import asyncio

async def upload_with_metadata():
    summary = await upload_music_library(
        music_dir="/path/to/music",
        artwork_dir="/path/to/artwork",
        metadata_file="metadata.json",
        max_concurrent=5,
    )
    
    print(f"✓ Uploaded {summary['successful']} tracks with metadata")

asyncio.run(upload_with_metadata())
```

## Storage Strategy

### Where Files Go

1. **Audio Files** (MP3, FLAC, WAV):
   - Primary: Storj DCS (S3-compatible, fast retrieval)
   - Backup: Web3.Storage (IPFS, content-addressed)
   - Total: 2 copies for redundancy

2. **Artwork** (JPG, PNG):
   - Web3.Storage (IPFS)
   - Content-addressed CID for NFT metadata

3. **NFT Metadata** (JSON):
   - NFT.Storage (unlimited, ERC-721 compatible)
   - Contains IPFS CIDs for audio + artwork

### Content Addressing

All files are **content-addressed**:
- **SHA-256 hash** for uniqueness (prevents duplicates)
- **IPFS CID** for decentralized retrieval
- **Storj object key** for fast S3-compatible access

### Bandwidth Considerations

With 150 songs (~15-20 GB):

- **Initial Upload**: Uses Storj (150GB free bandwidth)
- **Downloads**: Storj serves primary traffic
- **IPFS Backup**: Only used if Storj unavailable
- **Monthly Bandwidth**: 150GB free on Storj

## CLI Usage

### Quick Commands

```bash
# Upload entire music directory
python -c "from dcmx.storage.batch_uploader import upload_music_library; \
           import asyncio; \
           asyncio.run(upload_music_library('/path/to/music'))"

# Check storage stats
python -c "from dcmx.storage.decentralized_storage import DecentralizedStorageManager; \
           import asyncio; \
           async def stats(): \
               s = DecentralizedStorageManager.from_env(); \
               print(s.get_storage_stats()); \
               await s.cleanup(); \
           asyncio.run(stats())"
```

### Setup Script

Run the automated setup:

```bash
./scripts/setup_storage.sh
```

This will:
1. Check Python version
2. Install dependencies
3. Create `.env` configuration
4. Display API key instructions
5. Verify setup

## Monitoring & Maintenance

### Check Storage Usage

```python
from dcmx.storage.decentralized_storage import DecentralizedStorageManager
import asyncio

async def check_usage():
    storage = DecentralizedStorageManager.from_env()
    stats = storage.get_storage_stats()
    
    if "storj" in stats:
        storj = stats["storj"]
        print(f"Storj Usage:")
        print(f"  Files: {storj['total_files']}")
        print(f"  Size:  {storj['total_size_gb']:.2f} GB / 150 GB")
        print(f"  Usage: {storj['usage_percentage']:.1f}%")
    
    await storage.cleanup()

asyncio.run(check_usage())
```

### Track Upload Progress

The batch uploader provides real-time progress:

```python
from dcmx.storage.batch_uploader import BatchUploader
from dcmx.storage.decentralized_storage import DecentralizedStorageManager
import asyncio

async def track_progress():
    storage = DecentralizedStorageManager.from_env()
    uploader = BatchUploader(storage, max_concurrent=5)
    
    # Upload with progress tracking
    await uploader.upload_directory("/path/to/music")
    
    # Print summary
    uploader.print_summary()
    
    # Save detailed report
    uploader.save_report("upload_report.json")
    
    await storage.cleanup()

asyncio.run(track_progress())
```

## Troubleshooting

### Common Issues

**"Invalid credentials" error:**
- Double-check API keys in `.env`
- Ensure no extra spaces in keys
- Verify keys are active (not expired)

**"Bucket not found" error:**
- Create bucket in Storj dashboard
- Or set `STORJ_BUCKET=dcmx-music` in `.env`

**Upload timeout:**
- Reduce `MAX_CONCURRENT_UPLOADS` to 3
- Check internet connection
- Try uploading smaller batch first

**IPFS CID not found:**
- IPFS propagation takes 1-5 minutes
- Use Storj URL for immediate access
- IPFS backup is for redundancy

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Cost Estimates

### Free Tier (Current)

- **Storj**: 150 GB storage, 150 GB bandwidth/month = **$0/month**
- **Web3.Storage**: 10 GB storage, 10 GB bandwidth/month = **$0/month**
- **NFT.Storage**: Unlimited metadata = **$0/month**
- **Total**: **$0/month** for up to 150 songs

### Paid Tier (If Needed)

If you exceed free tier:

- **Storj**: $0.004/GB storage, $0.007/GB bandwidth
  - 200 GB storage = $0.80/month
  - 200 GB bandwidth = $1.40/month
  - **Total: ~$2.20/month**

- **Web3.Storage**: $5/month for 100GB
- **NFT.Storage**: Always free

## Next Steps

1. Run setup script: `./scripts/setup_storage.sh`
2. Add API keys to `.env`
3. Test single file upload
4. Batch upload your music library
5. Integrate with NFT minting

See [examples/storage_upload_examples.py](../examples/storage_upload_examples.py) for more examples.

## Support

- **Storj**: https://docs.storj.io
- **Web3.Storage**: https://web3.storage/docs
- **NFT.Storage**: https://nft.storage/docs
- **DCMX**: See [AGENTS.md](../AGENTS.md) for architecture details
