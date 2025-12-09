# DCMX Developer Quick Start

Get up and running with DCMX in 15 minutes.

---

## 1. Installation (2 minutes)

```bash
# Install Python 3.8+
python3 --version

# Clone and setup
git clone https://github.com/DCMX-Protocol/DCMX.git
cd DCMX

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Verify
pytest tests/ -v
```

Expected output:
```
tests/test_track.py::test_track_creation PASSED
tests/test_peer.py::test_peer_identity PASSED
tests/test_content_store.py::test_store_retrieve PASSED
```

---

## 2. Start Your First Node (3 minutes)

**Terminal 1 - Node 1:**
```bash
dcmx start --host 127.0.0.1 --port 8080
```

Expected output:
```
2025-12-09 15:30:45 INFO dcmx.core.node: Node starting on 127.0.0.1:8080
2025-12-09 15:30:45 INFO dcmx.core.node: Node ID: 550e8400-e29b-41d4-a716-446655440000
2025-12-09 15:30:45 INFO dcmx.core.node: HTTP server started
```

**Terminal 2 - Node 2:**
```bash
dcmx start --host 127.0.0.1 --port 8081 --peers 127.0.0.1:8080
```

Expected output:
```
2025-12-09 15:30:50 INFO dcmx.core.node: Node starting on 127.0.0.1:8081
2025-12-09 15:30:50 INFO dcmx.core.node: Connecting to peer 127.0.0.1:8080
2025-12-09 15:30:50 INFO dcmx.core.node: Connected to 1 peer
```

---

## 3. Add Music Content (3 minutes)

**Terminal 3:**

```bash
# Download sample music (or use your own)
wget -q https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3

# Add to node 1
dcmx add SoundHelix-Song-1.mp3 \
  --title "SoundHelix Song 1" \
  --artist "SoundHelix" \
  --album "Demo Album"
```

Expected output:
```
Track added successfully
Content hash: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
Size: 4.89 MB
Duration: 360 seconds
```

---

## 4. Verify Content Distribution (3 minutes)

**On Node 2 terminal:**
```bash
# List available tracks from all peers
dcmx list

# Expected output:
# Available Tracks:
# 1. SoundHelix Song 1 (SoundHelix)
#    Hash: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
#    Duration: 360s | Size: 4.89 MB
#    From: Node 1 (550e8400-e29b-41d4-a716-446655440000)
```

---

## 5. Download and Play (2 minutes)

```bash
# Download from peer
dcmx get a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6 -o downloaded.mp3

# Expected output:
# Downloading from peer: 550e8400-e29b-41d4-a716-446655440000
# Downloaded: downloaded.mp3 (4.89 MB)

# Play with your favorite player
ffplay downloaded.mp3
# or
vlc downloaded.mp3
```

---

## 6. Check Node Statistics (2 minutes)

**On either node:**

```bash
# View node status
dcmx stats

# Expected output:
# Node Statistics
# ===============
# Node ID: 550e8400-e29b-41d4-a716-446655440001
# Address: 127.0.0.1:8081
# 
# Local Tracks: 0
# Known Peers: 1
# Total Network Capacity: 4.89 MB
# 
# Peer Summary:
#   550e8400-e29b-41d4-a716-446655440000 (127.0.0.1:8080)
#     Tracks: 1
#     Last Seen: just now
```

---

## 7. Add Second Track (2 minutes)

Create a test track programmatically:

```python
# save as test_track.py
from dcmx.core.track import Track
import asyncio

async def main():
    # Create a simple track
    track = Track(
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        duration=240,
        content_hash="abc123def456",
        size=3000000,
        created_at="2025-12-09T15:30:00Z"
    )
    
    print(f"Created: {track.title} by {track.artist}")
    print(f"Hash: {track.content_hash}")
    print(f"Metadata: {track.to_dict()}")

asyncio.run(main())
```

Run it:
```bash
python test_track.py
```

---

## 8. Understanding the Key Concepts

### Content Addressing
```
Every track has a SHA-256 hash (content hash):
  - "SoundHelix-Song-1.mp3" → a1b2c3d4e5f6...
  
This hash is:
  ✓ Immutable (never changes for same file)
  ✓ Deterministic (same file = same hash)
  ✓ Unique (different file = different hash)
  ✓ Verifiable (recompute to verify integrity)
```

### Peer Discovery
```
Node 2 discovers Node 1:
  1. Node 2: "Hi, I'm Node 2, looking for music"
  2. Node 1: "I'm Node 1, I have 1 track"
  3. Node 1 sends: [SoundHelix-Song-1]
  4. Node 2: "Great! I'll cache that info"
  
Result: Node 2 knows Node 1 has "SoundHelix-Song-1"
```

### Content Distribution
```
Node 3 wants SoundHelix-Song-1:
  1. Node 3: "Who has a1b2c3d4e5f6?"
  2. Node 3's peers: "Node 1 and Node 2 have it"
  3. Node 3: "Node 1, send me a1b2c3d4e5f6"
  4. Node 1: (streams file)
  5. Node 3: Verifies hash, stores locally
  
Result: Content replicated across network
```

---

## 9. Next Steps

### Try These Exercises

**Exercise 1: Multi-node Network**
```bash
# Terminal 1
dcmx start --port 8080

# Terminal 2
dcmx start --port 8081 --peers 127.0.0.1:8080

# Terminal 3
dcmx start --port 8082 --peers 127.0.0.1:8080

# Terminal 4
dcmx add song.mp3 --port 8080
dcmx list --port 8082  # Should see song from node 1
```

**Exercise 2: Network Resilience**
```bash
# Start 3 nodes as above
# Kill node 1 (Ctrl+C)
# Node 2 and 3 still have content from node 1
dcmx list --port 8082  # Still shows content
```

**Exercise 3: Custom Metadata**
```python
from dcmx.core.track import Track

# Add track with all metadata
track = Track(
    title="My Song",
    artist="My Artist",
    album="My Album",
    duration=300,
    content_hash="xyz789...",
    size=5000000,
    created_at="2025-12-09T16:00:00Z"
)

# Print metadata
for key, value in track.to_dict().items():
    print(f"{key}: {value}")
```

### Explore the Code

```bash
# Core protocol implementation
cat dcmx/core/node.py          # Main Node class
cat dcmx/network/peer.py       # Peer identity
cat dcmx/core/track.py         # Track metadata
cat dcmx/storage/content_store.py  # File storage

# Examples
cat examples/simple_network.py  # Full example
```

### Read Full Documentation

- **Technical Whitepaper**: `docs/DCMX_TECHNICAL_WHITEPAPER.md`
- **Architecture Reference**: `docs/ARCHITECTURE_REFERENCE.md`
- **Implementation Guide**: `docs/IMPLEMENTATION_GUIDE.md`

---

## 10. Common Commands Reference

```bash
# Node Management
dcmx start --host 127.0.0.1 --port 8080        # Start node
dcmx start --peers HOST:PORT --port 8081       # Start and connect
dcmx stats                                      # Show statistics

# Content Management
dcmx add FILE.mp3 --title "Title" --artist "Artist"  # Add track
dcmx list                                       # List available tracks
dcmx get HASH -o output.mp3                    # Download track

# Peer Management
dcmx peers                                      # List connected peers
dcmx search QUERY                               # Search tracks

# Development
pytest                                          # Run all tests
pytest tests/test_track.py -v                  # Run specific test
dcmx --version                                  # Show version
```

---

## 11. Troubleshooting

### Port Already in Use
```bash
# Change port
dcmx start --port 9000

# Or kill existing process
lsof -ti:8080 | xargs kill -9
```

### Can't Connect to Peer
```bash
# Check if peer is running
curl http://127.0.0.1:8080/ping

# Check firewall
sudo ufw allow 8080

# Try explicit connection
dcmx start --peers 127.0.0.1:8080 --port 8081
```

### Content Not Found
```bash
# List what's available
dcmx list

# Check peer status
dcmx peers

# Try adding content
dcmx add song.mp3
```

---

## 12. Architecture Overview (1 page)

```
         ┌─────────────────────────┐
         │   Application (CLI)     │
         │  (dcmx add/list/get)    │
         └────────────┬────────────┘
                      │
         ┌────────────┴────────────┐
         │   Core Layer (Node)     │
         │ - track management      │
         │ - peer management       │
         │ - HTTP server           │
         └────────────┬────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
   ┌──┴──┐        ┌───┴────┐     ┌───┴────┐
   │Store│        │Network │     │Content  │
   │     │        │Protocol│     │Store    │
   └──┬──┘        └───┬────┘     └───┬────┘
      │               │              │
      ↓               ↓              ↓
   Peers ←────────→ HTTP ←────→ Filesystem
   Peers ←────────→ HTTP ←────→ Filesystem
   Peers ←────────→ HTTP ←────→ Filesystem
```

**Key Properties:**
- **Decentralized**: No central server, all peers equal
- **Content-addressed**: Find by SHA-256 hash, not filename
- **Resilient**: Works with peer failures, network partitions
- **Efficient**: Automatic deduplication, bandwidth sharing

---

## 13. Success Criteria

You've mastered DCMX when you can:

- ✅ Start 3+ nodes on same machine
- ✅ Add tracks to one node
- ✅ Download from other nodes
- ✅ Understand content addressing (hashing)
- ✅ Implement custom peer selection
- ✅ Write tests for your code
- ✅ Deploy in containers/cloud

---

## Getting Help

- **GitHub Issues**: https://github.com/DCMX-Protocol/DCMX/issues
- **Discord Community**: https://discord.gg/dcmx
- **Documentation**: `/workspaces/DCMX/docs/`
- **Examples**: `/workspaces/DCMX/examples/`

---

**Happy Building! 🚀**

Document Version: 1.0  
Last Updated: December 9, 2025
