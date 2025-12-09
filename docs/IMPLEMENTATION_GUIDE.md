# DCMX Implementation Guide

A comprehensive guide for implementing and extending the DCMX protocol.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Node Implementation](#node-implementation)
4. [Network Integration](#network-integration)
5. [Storage Management](#storage-management)
6. [Advanced Topics](#advanced-topics)
7. [Testing & Debugging](#testing--debugging)
8. [Deployment](#deployment)

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Basic understanding of async/await
- Familiarity with P2P networking concepts

### Installation

```bash
# Clone repository
git clone https://github.com/DCMX-Protocol/DCMX.git
cd DCMX

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Verify installation
dcmx --version
python -m pytest tests/
```

### Quick Start

```bash
# Terminal 1: Start first node (bootstrap)
dcmx start --host 127.0.0.1 --port 8080

# Terminal 2: Start second node (connect to first)
dcmx start --host 127.0.0.1 --port 8081 --peers 127.0.0.1:8080

# Terminal 3: Add content to first node
dcmx add ~/music/song.mp3 --title "Song" --artist "Artist"

# Terminal 4: Query from second node
dcmx list  # Should show song from first node
```

---

## Core Concepts

### Content Addressing

The foundation of DCMX is **content addressing**: identifying content by its cryptographic hash rather than arbitrary names.

```python
import hashlib

def compute_content_hash(content: bytes) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content).hexdigest()

# Example
audio_bytes = open("song.mp3", "rb").read()
content_hash = compute_content_hash(audio_bytes)
# content_hash = "abc123def456..." (64 hex characters)
```

**Advantages**:
- Immutable: Hash never changes for same content
- Deduplication: Same file → same hash → single copy stored
- Verification: Re-compute hash to verify integrity
- Distribution: Multiple peers can serve same content

### Peer Identity

Each peer has a globally unique identity:

```python
from uuid import uuid4

class Peer:
    def __init__(self, host: str, port: int):
        self.peer_id = str(uuid4())  # Globally unique
        self.host = host
        self.port = port
        self.available_tracks = set()  # Content hashes

# Example
peer = Peer("192.168.1.100", 8080)
# peer.peer_id = "550e8400-e29b-41d4-a716-446655440000"
# peer.address = "192.168.1.100:8080"
```

### Track Metadata

Tracks contain immutable metadata:

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Track:
    title: str              # "Song Name"
    artist: str             # "Artist Name"
    album: str = ""         # "Album Name"
    duration: int = 0       # Seconds
    content_hash: str = ""  # SHA-256 hash
    size: int = 0           # Bytes
    created_at: str = ""    # ISO timestamp
```

---

## Node Implementation

### Creating a Node

```python
from dcmx.core.node import Node
from pathlib import Path

# Create node
node = Node(
    host="127.0.0.1",
    port=8080,
    data_dir=Path.home() / ".dcmx"
)

# Node components:
# - node.peer: Network identity
# - node.peers: Dict of known peers
# - node.tracks: Dict of local tracks
# - node.content_store: File storage
# - node.protocol: Network communication
```

### Starting and Stopping

```python
import asyncio

async def run():
    # Start node (begins HTTP server)
    await node.start()
    
    try:
        # Node running...
        await asyncio.sleep(60)
    finally:
        # Shutdown gracefully
        await node.stop()

# Run async code
asyncio.run(run())
```

### Adding Tracks

```python
from dcmx.core.track import Track

# Load audio file
audio_path = "~/music/song.mp3"
audio_bytes = open(audio_path, "rb").read()

# Compute hash
content_hash = Track.compute_content_hash(audio_bytes)

# Create metadata
track = Track(
    title="My Song",
    artist="Artist Name",
    album="Album Name",
    duration=240,
    content_hash=content_hash,
    size=len(audio_bytes),
    created_at="2025-12-09T15:30:00Z"
)

# Add to node
node.add_track(track, audio_bytes)

# Track now available for other peers to discover
```

### Listing Local Tracks

```python
# Get all local tracks
for content_hash, track in node.tracks.items():
    print(f"{track.title} - {track.artist}")
    print(f"  Hash: {content_hash}")
    print(f"  Duration: {track.duration}s")
    print(f"  Size: {track.size} bytes")
```

### Querying Node State

```python
# Get node statistics
print(f"Node ID: {node.peer.peer_id}")
print(f"Address: {node.peer.address}")
print(f"Local tracks: {len(node.tracks)}")
print(f"Known peers: {len(node.peers)}")

# Get peer information
for peer_id, peer in node.peers.items():
    print(f"Peer {peer_id[:8]}: {peer.address}")
    print(f"  Tracks available: {len(peer.available_tracks)}")
```

---

## Network Integration

### Connecting to Peers

```python
# Connect to a known peer
peer_info = await node.protocol.connect("192.168.1.100", 8080)

# peer_info contains:
# - peer_id: Remote node's UUID
# - host: Remote node's address
# - port: Remote node's port
# - available_tracks: Set of content hashes

# Add to known peers
node.peers[peer_info.peer_id] = peer_info
```

### Peer Discovery

```python
# Run periodic peer discovery
async def discover():
    while node._running:
        # Contact each known peer
        for peer in list(node.peers.values()):
            try:
                updated = await node.protocol.connect(peer.host, peer.port)
                # Peer still alive, update info
                node.peers[updated.peer_id] = updated
            except ConnectionError:
                # Peer offline, mark for retry
                pass
        
        # Wait before next discovery round
        await asyncio.sleep(30)

# Run discovery in background
asyncio.create_task(discover())
```

### HTTP Endpoints

The node provides these HTTP endpoints for peer communication:

#### GET /ping
```python
# Health check - peer is responsive

# Request
GET http://127.0.0.1:8080/ping

# Response
200 OK
{"status": "ok"}
```

#### GET /peers
```python
# Get list of known peers

# Request
GET http://127.0.0.1:8080/peers

# Response
200 OK
[
  {
    "peer_id": "550e8400-e29b-41d4-a716-446655440000",
    "host": "192.168.1.100",
    "port": 8080,
    "available_tracks": [
      "abc123def456...",
      "fed654cba321..."
    ]
  },
  ...
]
```

#### GET /tracks
```python
# Get list of available tracks

# Request
GET http://127.0.0.1:8080/tracks

# Response
200 OK
[
  {
    "title": "Song Name",
    "artist": "Artist Name",
    "content_hash": "abc123def456...",
    "size": 5000000,
    "duration": 240
  },
  ...
]
```

#### POST /discover
```python
# Peer discovery handshake

# Request
POST http://127.0.0.1:8080/discover
Content-Type: application/json

{
  "peer": {
    "peer_id": "550e8400-e29b-41d4-a716-446655440001",
    "host": "192.168.1.101",
    "port": 8080
  }
}

# Response
200 OK
{
  "peer": {
    "peer_id": "550e8400-e29b-41d4-a716-446655440000",
    "host": "192.168.1.100",
    "port": 8080,
    "available_tracks": ["abc123...", ...]
  },
  "tracks": [
    {
      "title": "Song",
      "artist": "Artist",
      "content_hash": "abc123...",
      "size": 5000000,
      "duration": 240
    },
    ...
  ]
}
```

#### GET /content/{hash}
```python
# Download content by hash

# Request
GET http://127.0.0.1:8080/content/abc123def456...

# Response
200 OK
Content-Type: application/octet-stream
Content-Length: 5000000

[Binary audio data...]

# Supported headers
Range: bytes=0-1048575  # Partial download support
```

---

## Storage Management

### ContentStore Operations

```python
from dcmx.storage.content_store import ContentStore
from pathlib import Path

store = ContentStore(Path.home() / ".dcmx" / "content")

# Store content
audio_bytes = b"...audio data..."
content_hash = "abc123def456..."
store.store(content_hash, audio_bytes)

# Retrieve content
retrieved = store.retrieve(content_hash)
assert retrieved == audio_bytes

# Check if exists
if store.exists(content_hash):
    print("Content found")
```

### Storage Layout

```
~/.dcmx/content/
├── ab/              # 2-char prefix shard
│   ├── abc123...
│   ├── abf456...
│   └── (avg 1000-5000 files)
├── cd/
├── ef/
└── zz/
```

### File Management

```python
# Size calculation
import os

def get_storage_size(content_dir: Path) -> int:
    """Calculate total storage used."""
    total = 0
    for dirpath, dirnames, filenames in os.walk(content_dir):
        for filename in filenames:
            filepath = Path(dirpath) / filename
            total += filepath.stat().st_size
    return total

# Example
size_bytes = get_storage_size(Path.home() / ".dcmx" / "content")
size_gb = size_bytes / (1024 ** 3)
print(f"Storage used: {size_gb:.2f} GB")
```

### Caching Strategy

```python
class NodeWithCache(Node):
    """Node with optional local caching of remote tracks."""
    
    async def get_track(self, content_hash: str) -> bytes:
        """Get track, fetching from network if needed."""
        
        # Try local storage
        if self.content_store.exists(content_hash):
            return self.content_store.retrieve(content_hash)
        
        # Try network
        for peer in self.peers.values():
            if content_hash not in peer.available_tracks:
                continue
            
            try:
                content = await self.protocol.fetch_content(
                    peer.host, peer.port, content_hash
                )
                
                # Cache locally for future
                self.content_store.store(content_hash, content)
                return content
                
            except Exception as e:
                logger.warning(f"Failed to fetch from {peer}: {e}")
                continue
        
        raise ContentNotFoundError(f"Track {content_hash} not available")
```

---

## Advanced Topics

### Custom Metadata

Extend Track with additional metadata:

```python
from dcmx.core.track import Track
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class ExtendedTrack(Track):
    """Track with additional metadata."""
    genre: Optional[str] = None
    release_date: Optional[str] = None
    composer: Optional[str] = None
    isrc: Optional[str] = None  # International Standard Recording Code
    tags: List[str] = None
    
    def to_dict(self):
        """Serialize including custom fields."""
        data = super().to_dict()
        data.update({
            "genre": self.genre,
            "release_date": self.release_date,
            "composer": self.composer,
            "isrc": self.isrc,
            "tags": self.tags or [],
        })
        return data
```

### Custom Peer Scoring

Implement intelligent peer selection:

```python
class PeerScore:
    """Score peers for content selection."""
    
    @staticmethod
    def score_peer(peer: Peer, content_hash: str) -> float:
        """Score peer for downloading content."""
        
        score = 0.0
        
        # Has content?
        if content_hash not in peer.available_tracks:
            return 0.0
        
        score += 1.0
        
        # Track count (more tracks = more reliable)
        reliability = min(len(peer.available_tracks) / 1000, 1.0)
        score += reliability * 0.5
        
        # Network proximity (if available)
        # score += measure_latency(peer) * factor
        
        # Peer age (older = more reliable)
        # age_days = (now - peer.created_at).days
        # score += min(age_days / 365, 1.0) * 0.3
        
        return score

# Use for peer selection
best_peer = max(
    [p for p in node.peers.values() if hash in p.available_tracks],
    key=lambda p: PeerScore.score_peer(p, hash)
)
```

### Bandwidth Limiting

Implement rate limiting:

```python
import time
from collections import deque

class BandwidthLimiter:
    """Limit bandwidth usage."""
    
    def __init__(self, rate_mbps: float):
        self.rate_mbps = rate_mbps
        self.rate_bps = rate_mbps * 1_000_000
        self.timestamps = deque()
    
    async def acquire(self, bytes_count: int):
        """Wait if necessary to stay under rate limit."""
        now = time.time()
        
        # Remove old timestamps (outside window)
        window_start = now - 1.0
        while self.timestamps and self.timestamps[0] < window_start:
            self.timestamps.popleft()
        
        # Check current rate
        bytes_in_window = sum(
            bytes for ts, bytes in self.timestamps
        )
        
        if bytes_in_window + bytes_count > self.rate_bps:
            # Wait until we can transmit
            wait_time = (bytes_in_window + bytes_count - self.rate_bps) / self.rate_bps
            await asyncio.sleep(wait_time)
        
        self.timestamps.append((time.time(), bytes_count))
```

---

## Testing & Debugging

### Unit Tests

```python
import pytest
from dcmx.core.track import Track

def test_content_hash_deterministic():
    """Hash should be deterministic."""
    content = b"test audio"
    hash1 = Track.compute_content_hash(content)
    hash2 = Track.compute_content_hash(content)
    assert hash1 == hash2

def test_track_metadata():
    """Track should preserve metadata."""
    track = Track(
        title="Song",
        artist="Artist",
        content_hash="abc123",
        duration=240,
        size=5000000
    )
    
    assert track.title == "Song"
    assert track.duration == 240
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_peer_discovery():
    """Two nodes should discover each other."""
    
    # Setup
    node1 = Node("127.0.0.1", 8080)
    node2 = Node("127.0.0.1", 8081)
    
    await node1.start()
    await node2.start()
    
    # Discover
    peer_info = await node1.protocol.connect("127.0.0.1", 8081)
    
    # Verify
    assert peer_info.host == "127.0.0.1"
    assert peer_info.port == 8081
    
    # Cleanup
    await node1.stop()
    await node2.stop()
```

### Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Log peer state
logger = logging.getLogger("dcmx")
logger.debug(f"Peers: {node.peers}")
logger.debug(f"Tracks: {node.tracks}")

# Inspect peer availability
for peer_id, peer in node.peers.items():
    logger.info(f"Peer {peer_id}: {peer.address}, tracks={len(peer.available_tracks)}")
```

---

## Deployment

### Production Checklist

- [ ] Use HTTPS/TLS for peer communication
- [ ] Configure firewall rules for node port
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Test disaster recovery
- [ ] Load test with expected scale
- [ ] Security audit of code
- [ ] Performance tuning

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy code
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Create data directory
RUN mkdir -p /data/dcmx

# Run node
CMD ["dcmx", "start", "--host", "0.0.0.0", "--port", "8080", "--data-dir", "/data/dcmx"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dcmx-node
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dcmx
  template:
    metadata:
      labels:
        app: dcmx
    spec:
      containers:
      - name: dcmx
        image: dcmx:latest
        ports:
        - containerPort: 8080
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: dcmx-data
```

---

## Resources

- **Protocol Specification**: See `DCMX_TECHNICAL_WHITEPAPER.md`
- **Architecture Reference**: See `ARCHITECTURE_REFERENCE.md`
- **API Documentation**: See inline code docstrings
- **Examples**: See `examples/` directory

---

**Document Version**: 1.0  
**Date**: December 9, 2025  
**Last Updated**: December 9, 2025
