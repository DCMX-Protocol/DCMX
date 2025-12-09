# DCMX Architecture Reference

## Visual Architecture Diagrams

### 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DCMX Mesh Network                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Blockchain Layer (Optional)                              │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • NFT Smart Contracts (ERC-721)                          │  │
│  │ • Token Distribution (ERC-20)                            │  │
│  │ • Governance DAO                                         │  │
│  │ • Royalty Distribution                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Application Layer                                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ • CLI Interface (dcmx start, add, list)                 │  │
│  │ • Web UI (HTML/CSS/JavaScript)                          │  │
│  │ • Mobile Apps (iOS/Android)                             │  │
│  │ • API Integrations                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Node Core Layer                                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ ┌────────────────┐  ┌────────────────┐  ┌──────────────┐│  │
│  │ │ Track Manager  │  │ Peer Manager   │  │ HTTP Server  ││  │
│  │ │                │  │                │  │              ││  │
│  │ │ • Track meta   │  │ • Peer dir     │  │ • /discover  ││  │
│  │ │ • Content hash │  │ • Peer state   │  │ • /tracks    ││  │
│  │ │ • Dedup        │  │ • Peer health  │  │ • /content   ││  │
│  │ │ • Metadata     │  │ • Discovery    │  │ • /peers     ││  │
│  │ └────────────────┘  └────────────────┘  └──────────────┘│  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Network Layer                                            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ ┌────────────────┐  ┌────────────────┐                   │  │
│  │ │ Protocol       │  │ Async Runtime  │                   │  │
│  │ │ (aiohttp)      │  │ (asyncio)      │                   │  │
│  │ │                │  │                │                   │  │
│  │ │ • HTTP client  │  │ • Event loop   │                   │  │
│  │ │ • HTTP server  │  │ • Task mgmt    │                   │  │
│  │ │ • Connections  │  │ • Concurrency  │                   │  │
│  │ └────────────────┘  └────────────────┘                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Storage Layer                                            │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ ┌────────────────┐  ┌────────────────┐                   │  │
│  │ │ ContentStore   │  │ Metadata DB    │                   │  │
│  │ │                │  │                │                   │  │
│  │ │ • File I/O     │  │ • SQLite       │                   │  │
│  │ │ • Sharding     │  │ • Track info   │                   │  │
│  │ │ • Dedup        │  │ • Peer list    │                   │  │
│  │ │ • Cache        │  │ • Config       │                   │  │
│  │ └────────────────┘  └────────────────┘                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Peer-to-Peer Mesh Network

```
                Individual Node Topology
                ═════════════════════════

                    ┌─────────┐
                    │ DCMX    │
                    │ Node A  │
                    └────┬────┘
                    host:port
                    peer_id
                    
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
        Peer B       Peer C        Peer D
      (Known)      (Known)       (Known)
      host:port    host:port     host:port
      tracks[]     tracks[]      tracks[]
      
        │             │             │
        └─────────────┼─────────────┘
                      │
              HTTP Gossip Protocol
              (Every 5-30 seconds)
              
                      │
                      ▼
              Peer discovery
              Track exchange
              Network state sync
```

### 3. Content Discovery Flow

```
User Request: "Get track abc123"
      │
      ▼
┌──────────────────────┐
│ Local Node           │
│                      │
│ Check local storage  │
└──────┬───────────────┘
       │
    ┌──┴──┐
    │     │
    │     └─► If found: Serve immediately ✓
    │
    ▼
Not in local storage → Query known peers
    │
    ├─► Peer A: has_track(abc123)? YES
    │   └─► GET /content/abc123
    │       │
    │       ▼
    │   Receive audio bytes
    │       │
    │       ▼
    │   Verify hash ✓
    │       │
    │       ▼
    │   Cache locally (optional)
    │       │
    │       ▼
    │   Return to user ✓
    │
    ├─► Peer B: has_track(abc123)? NO
    │
    └─► Peer C: has_track(abc123)? NO
```

### 4. Node State Machine

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                      Initialized
                           │
                           ▼
                    ┌─────────────┐
                    │  IDLE       │
                    │             │
                    │ Known peers │
                    │ Cached tracks
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    User adds      Start discovery    Network event
         track           │
          │              ▼
          │         ┌────────────┐
          │         │ DISCOVERING│
          │         │            │
          │         │ Contact    │
          │         │ known peers│
          │         └────┬───────┘
          │              │
          ▼              ▼
    ┌──────────────────────────┐
    │ Update local state       │
    │ • Add track to index     │
    │ • Update peer list       │
    │ • Broadcast changes      │
    └─────────────┬────────────┘
                  │
                  ▼
          ┌─────────────┐
          │  IDLE       │
          │             │
          │ Network     │
          │ consistent  │
          └─────────────┘
```

### 5. File Storage Organization

```
~/.dcmx/
│
├── content/                 # Media storage
│   ├── ab/                  # 2-char prefix sharding
│   │   ├── abc123def456...  # content_hash
│   │   ├── abf789ghi012...
│   │   └── (1000s of files)
│   │
│   ├── cd/
│   │   ├── cde345jkl678...
│   │   └── ...
│   │
│   ├── ef/
│   │   └── ...
│   │
│   └── zz/
│       └── ...
│
├── metadata/
│   ├── tracks.json          # Local track catalog
│   ├── peers.json           # Known peers
│   └── config.yaml          # Node configuration
│
└── logs/
    ├── node.log             # Application logs
    ├── network.log          # Network activity
    └── errors.log           # Error traces
```

### 6. Data Flow - Add Track Operation

```
User: "Add song.mp3"
│
├─► Load audio file → bytes
│
├─► Compute hash = SHA-256(bytes)
│   hash = "abc123def456..."
│
├─► Create Track metadata
│   {
│     "title": "My Song",
│     "artist": "Me",
│     "content_hash": "abc123def456...",
│     "size": 5000000,
│     "duration": 240
│   }
│
├─► Store in ContentStore
│   File: ~/.dcmx/content/ab/abc123def456...
│
├─► Add to local index
│   tracks["abc123def456..."] = Track(...)
│
└─► Broadcast to peers
    POST /discover
    {
      "available_tracks": ["abc123def456...", ...]
    }
```

### 7. Data Flow - Download Track Operation

```
User: "Stream track xyz789"
│
├─► Check local cache
│   │
│   ├─ Found: Serve from disk ✓
│   │
│   └─ Not found: Search network
│        │
│        ├─► Known peers for hash?
│        │   │
│        │   └─► Parallel GET /content/xyz789
│        │       to multiple peers
│        │
│        └─► First response wins
│            │
│            ├─► Verify hash
│            │
│            ├─► Store in cache
│            │
│            └─► Return to user ✓
```

## Key Invariants

### Data Invariant 1: Content Addressability
```
Every piece of content has exactly one hash:
  content1 + content2 = hash1
  content1 (again) = hash1 (same hash)
  
No hash collisions possible (with SHA-256):
  2^256 possible hashes >> universe of content
  Collision probability: 1 in 2^128 (infeasible)
```

### Data Invariant 2: Peer Autonomy
```
Each node maintains independent state:
  Node A's track list ≠ Node B's track list
  (May become consistent eventually via gossip)
  
Each node has authority over its data:
  Only Node A can add tracks to Node A's store
  Peers can query but not modify
```

### Data Invariant 3: Content Immutability
```
Once content is stored with hash H:
  retrieve(H) always returns same content
  
Cannot modify content without changing hash:
  modified_content → different_hash
  
Verification is deterministic:
  compute_hash(retrieved_content) == H ✓
```

## Scalability Analysis

### Network Growth

```
N nodes in network

Peer Knowledge per node:
  Optimal: O(log N)        # DHT-like
  Current: O(N)            # Full knowledge small networks
  Future: O(log N)         # DHT implementation

Storage Capacity:
  Total: N × capacity_per_node
  Example: 1000 nodes × 1TB = 1PB
  Linear scaling with N

Content Availability:
  k copies of content
  Probability available: 1 - (1-p)^k
  where p = fraction of network with content
```

### Latency Characteristics

```
Operation: Download track not in cache

Scenario 1: Content on known peer
  Latency = Network roundtrip
  Typical: < 100ms for local networks
           < 500ms for Internet

Scenario 2: Content on unknown peer (discovery needed)
  Latency = Gossip propagation time + download
  Typical: 5-30 seconds for O(log N) hops
           + download latency

Cached afterward: Fast (< 100ms)
```

## Security Properties

### Content Integrity
```
Guarantee: Downloaded content not tampered with

Mechanism:
  1. Compute SHA-256 of received content
  2. Compare with expected hash
  3. Hash mismatch → reject content
  
Security: SHA-256 has 2^256 possible values
         Probability of accidental collision: 2^-128
         Probability of intentional collision: depends on attacker power
```

### Peer Authentication (Current)
```
Limitation: No cryptographic peer authentication
           Peer identified by peer_id (UUID) only

Risk: Malicious node could impersonate legitimate peer
Mitigation: HTTPS/TLS for transport security
            Content verification by hash
            
Future: Sign peer identity with private keys
```

### Privacy
```
What is tracked:
  • Peer IP addresses (for connectivity)
  • Tracks available on each peer (no personal data)
  • Content hashes (deterministic, not linkable to user)
  
What is NOT tracked:
  • User identities
  • Listening history
  • User profiles
  • Behavioral analytics
```

---

## Performance Benchmarks (Reference)

These are typical performance characteristics for a DCMX node:

### Network I/O

| Operation | Latency | Bandwidth |
|-----------|---------|-----------|
| Peer discovery | 100-500ms | ~1KB (HTTP) |
| Track metadata exchange | 50-200ms | ~10KB (per peer) |
| Content fetch (1GB) | ~10-100s | Limited by link |
| Full sync (100 tracks) | 1-5s | ~50KB per track |

### Local I/O

| Operation | Time | Notes |
|-----------|------|-------|
| Hash computation (1GB) | 500ms | SHA-256, single threaded |
| File write (100MB) | 100ms | Depends on disk |
| File read (100MB) | 100ms | Depends on disk |
| Index update | < 1ms | In-memory operation |

### Memory Usage

| Component | Size | Notes |
|-----------|------|-------|
| Per peer | ~1KB | Metadata + track set |
| Per track | ~500B | Metadata entry |
| Network cache | Variable | User tracks |
| Typical node | 100-500MB | With 1000 tracks |

---

## Implementation Checklist

For developers implementing DCMX:

### Core Components
- [ ] Peer class with UUID, address, track set
- [ ] Track class with content hash computation
- [ ] Node orchestrator managing peers and tracks
- [ ] ContentStore for file-based storage
- [ ] HTTP Protocol handler (aiohttp)

### Network Operations
- [ ] Peer discovery (/discover endpoint)
- [ ] Peer gossip protocol (periodic updates)
- [ ] Content distribution (/content/{hash} endpoint)
- [ ] Health checking (/ping endpoint)
- [ ] Graceful error handling

### Storage
- [ ] 2-character prefix sharding for files
- [ ] Hash verification on retrieval
- [ ] Filesystem error handling
- [ ] Optional content caching
- [ ] Metadata persistence (JSON/SQLite)

### Integration
- [ ] CLI interface (start, add, list, stats)
- [ ] Configuration management
- [ ] Logging and monitoring
- [ ] Unit and integration tests
- [ ] Performance benchmarking

---

**Document Version**: 1.0  
**Date**: December 9, 2025  
**Last Updated**: December 9, 2025
