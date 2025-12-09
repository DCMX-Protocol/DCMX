# DCMX Frequently Asked Questions (FAQ)

Comprehensive answers to common questions about the DCMX protocol and platform.

---

## Table of Contents

1. [General Questions](#general-questions)
2. [Technical Questions](#technical-questions)
3. [Network & Performance](#network--performance)
4. [Security & Privacy](#security--privacy)
5. [Content Management](#content-management)
6. [Deployment & Operations](#deployment--operations)
7. [Compliance & Legal](#compliance--legal)
8. [Troubleshooting](#troubleshooting)

---

## General Questions

### Q: What is DCMX?

**A:** DCMX (Decentralized Mesh Music eXchange) is a peer-to-peer music distribution protocol that:

- **Eliminates central servers**: Every node is equal, no single point of failure
- **Uses content addressing**: Music identified by SHA-256 hash, not filename
- **Enables direct distribution**: Artists can distribute music directly to listeners
- **Ensures ownership**: Content hash proves integrity and prevents tampering

Think of it like BitTorrent, but optimized for music distribution with artist ownership verification.

### Q: How is DCMX different from Spotify/Apple Music?

| Aspect | DCMX | Spotify | 
|--------|------|---------|
| **Control** | Artist-centric | Platform controls distribution |
| **Revenue** | Direct fan payment | Spotify takes cut |
| **Privacy** | Minimal tracking | Extensive user tracking |
| **Availability** | P2P (censorship-resistant) | Centralized (can be blocked) |
| **Infrastructure** | Peer-provided | Spotify data centers |

### Q: Is DCMX like Audius?

**A:** Similar goals (artist empowerment), but different approach:

- **DCMX**: P2P mesh network, anyone can run a node, content-addressed
- **Audius**: Blockchain-based, validator nodes required, token economics
- **Winner**: Depends on use case (DCMX for resilience, Audius for smart contracts)

### Q: Can I use DCMX commercially?

**A:** Yes! DCMX is protocol, not a business model. You can:

- Build commercial music apps on top of DCMX
- Charge users for access to your app
- Take a percentage of artist payments
- License exclusive content

Just ensure you comply with music copyright laws.

### Q: Is DCMX open source?

**A:** Yes, completely open source. You can:

- View, modify, and redistribute the code
- Run your own nodes
- Build apps using the protocol
- Contribute to development

See `LICENSE` file for terms.

---

## Technical Questions

### Q: How does content hashing work?

**A:** Every audio file gets a unique SHA-256 hash:

```
Song.mp3 (identical bytes)
         ↓
      SHA-256
         ↓
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6...
(64 hex characters, always the same for this file)
```

**Properties:**
- **Deterministic**: Same file = same hash, always
- **Collision-proof**: 2^256 possible values, ~impossible to find duplicates
- **Immutable**: Change 1 byte → completely different hash
- **Verifiable**: Recalculate hash to verify integrity

**Example:**
```python
from dcmx.core.track import Track

audio = open("song.mp3", "rb").read()
hash1 = Track.compute_content_hash(audio)
hash2 = Track.compute_content_hash(audio)

assert hash1 == hash2  # Always the same
```

### Q: What is "content addressing"?

**A:** Instead of naming files, we identify them by their content:

```
Traditional:        Content-Addressed:
  /music/song.mp3    hash://a1b2c3d4...
  /music/song2.mp3   hash://f5e4d3c2...
  
Problem:            Benefit:
- Names arbitrary    - Hash = content
- File moved = lost  - Deduplication
- No integrity       - Verification built-in
```

### Q: How do nodes discover each other?

**A:** Through the `/discover` endpoint:

```
Node A                          Node B
  │                             │
  ├─→ POST /discover           │
  │   (Hi, I'm Node A)         │
  │                             │
  │                        ←─ Response
  │                           (I'm Node B, I have 10 tracks)
  │
  └─→ Add Node B to known peers
```

### Q: What if two peers have the same content?

**A:** DCMX automatically deduplicates:

```
Node 1: song.mp3 (hash: a1b2c3...) → Stored
Node 2: song.mp3 (hash: a1b2c3...) → Uses same hash!
Node 3: song.mp3 (hash: a1b2c3...) → Uses same hash!

Result: Only 1 copy of content, 3 nodes serving it
```

This is automatic and requires no configuration.

### Q: Can I run DCMX on my laptop?

**A:** Yes! Minimum requirements:

```
CPU:     1 GHz processor
RAM:     512 MB
Storage: 1 GB (for content)
Network: 1 Mbps internet connection
OS:      Linux, macOS, or Windows
```

Typical setup:
```bash
# 1. Install Python
python3 --version

# 2. Install DCMX
pip install dcmx

# 3. Start node
dcmx start --port 8080

# 4. Add music
dcmx add song.mp3
```

### Q: What programming languages can use DCMX?

**A:** DCMX speaks HTTP, so any language works:

```python
# Python
import requests
response = requests.get("http://node:8080/tracks")

// JavaScript/Node.js
fetch("http://node:8080/tracks")
  .then(r => r.json())

// Go
resp, _ := http.Get("http://node:8080/tracks")

// Rust
let client = reqwest::Client::new();
let resp = client.get("http://node:8080/tracks").send()
```

---

## Network & Performance

### Q: How many peers can one node handle?

**A:** Depends on resources, but typically:

```
Network connections: 100-1000 concurrent
Known peers: 10,000+
Tracks advertised: Unlimited
HTTP connections/second: 100-1000
```

Scaling is near-linear with hardware:
- 2x RAM → ~2x peers
- 2x bandwidth → ~2x throughput

### Q: How fast is content download?

**A:** Download speed = your internet connection speed:

```
1 Mbps peer  → 1 MB/min = 60 MB/hour
10 Mbps peer → 10 MB/min = 600 MB/hour
```

For popular content, you can download from multiple peers simultaneously:

```
5x 2 Mbps peers → 10 Mbps total = 600 MB/hour
```

### Q: Does DCMX work on slow networks?

**A:** Yes, but with trade-offs:

```
1G network (rural)  → Works, slow for video
10G network (urban) → Fast downloads
100G network (datacenter) → Very fast
```

**Optimization**: Use smaller audio files or stream instead of download.

### Q: What happens if a peer goes offline?

**A:** DCMX handles gracefully:

```
Peer A: Online, has content
Peer B: Requests content from A
Peer A: Goes offline
Peer B: Tries again in 30 seconds
        If successful: Content from A (restored)
        If failed: Content from Peer C (automatic failover)
```

**No manual intervention needed.**

### Q: Can multiple peers share one internet connection?

**A:** Yes! DCMX behind NAT/router:

```
Router (192.168.1.1:8080)
  ├─ Node 1 (192.168.1.10:8080) - Internal
  ├─ Node 2 (192.168.1.11:8080) - Internal
  └─ Node 3 (192.168.1.12:8080) - Internal

Each node can:
- Communicate internally (fast)
- Access internet through router (slower)
- Be discovered by external nodes
```

**Setup**: Port forwarding in router (if external discovery needed).

---

## Security & Privacy

### Q: Is my music encrypted?

**A:** By default, no. Network encryption (TLS) is optional.

**Without encryption:**
- Content hash publicly visible (immutable anyway)
- Network sniffers see which tracks you access
- ISP can see you're using DCMX

**With encryption (TLS):**
- Content encrypted in transit
- Sniffers see encrypted data
- ISP sees DCMX traffic but not content

**Recommendation**: Use TLS for production.

### Q: Can someone intercept my music?

**A:** Technically yes, but:

1. **Interception**: Anyone on your network can see traffic
2. **Decryption**: No (content hash is public anyway)
3. **Blocking**: Possible if ISP blocks DCMX ports
4. **Mitigation**: Use VPN + TLS

**Bottom line**: DCMX assumes open internet; use VPN for privacy.

### Q: Does DCMX track me?

**A:** Not by default. DCMX logs:

```
Connection logs:    Which peers you connected to
Download logs:      Which content hashes you downloaded
IP addresses:       Required for P2P to work
User agents:        Browser/app making request

NOT logged:
- Your identity (unless you provide it)
- Your listening habits (unless you upload them)
- Your location (unless you provide it)
- Your payment info (unless you use external payment)
```

### Q: Can I remain anonymous?

**A:** Yes, with precautions:

```
1. Use Tor/VPN to hide IP
2. Don't provide username/email
3. Don't link to personal accounts
4. Use pseudonymous wallet (if blockchain integration)

Result: Fully anonymous to other peers
```

### Q: What if someone uploads malicious content?

**A:** DCMX provides no validation:

```
Malicious content uploaded
        ↓
Hash: a1b2c3... (immutable)
        ↓
Other nodes: "We have a1b2c3..."
        ↓
Your node: Downloads from any peer
        ↓
YOU MUST VERIFY before playing/executing
```

**Mitigation:**
- Download from trusted peers only
- Verify file with antivirus before executing
- Use OS sandboxing (containers, VMs)
- Trust but verify (reputation system optional)

### Q: Is the hash the same on all nodes?

**A:** Yes! Content hash is immutable:

```
Artist uploads "song.mp3" → hash: a1b2c3...
Peer 1 downloads → hash: a1b2c3... (verified ✓)
Peer 2 downloads → hash: a1b2c3... (verified ✓)
Peer 3 downloads → hash: a1b2c3... (verified ✓)

If someone modifies:
Original + 1 byte → hash: f5e4d3... (different!)
```

**This proves integrity.**

---

## Content Management

### Q: How do I add my music?

**A:** Simple 2-step process:

```bash
# Step 1: Prepare audio file
# (MP3, WAV, FLAC, etc.)

# Step 2: Add to DCMX
dcmx add song.mp3 \
  --title "My Song" \
  --artist "Me" \
  --album "My Album"
```

**What happens:**
1. Computes SHA-256 hash
2. Stores file locally
3. Advertises to peers
4. Peers can download

### Q: Can I host multiple versions (bitrates)?

**A:** Yes, each is separate content:

```
song_128kbps.mp3 → hash: a1b2c3...
song_320kbps.mp3 → hash: f5e4d3...
song_flac.wav    → hash: k2l3m4...

Track metadata ties them:
{
  "title": "Song",
  "versions": [a1b2c3, f5e4d3, k2l3m4]
}
```

### Q: What metadata should I include?

**A:** Recommended fields:

```
Required:
- title: Song name
- artist: Artist/band name

Recommended:
- album: Album name
- duration: Length in seconds
- genre: Music genre
- release_date: YYYY-MM-DD

Optional:
- ISRC: International Standard Recording Code
- composer: Composer name
- producer: Producer name
- tags: Comma-separated keywords
```

### Q: Can I update a track?

**A:** No, but you can add a new version:

```
Original: song_v1.mp3 → hash: a1b2c3...
Update:   song_v2.mp3 → hash: f5e4d3... (different!)

Peers now have both versions
Version preference: Set in metadata
```

### Q: How do I handle copyrights?

**A:** DCMX doesn't handle this; you're responsible:

```
You own the content:
  ✓ Upload without restriction
  ✓ Set your own licensing terms
  
Third-party content:
  ✗ Get copyright holder permission first
  ✗ Pay licensing fees
  ✗ Provide proper attribution

DCMX is neutral: It's just data transport
```

### Q: Can I set access permissions?

**A:** DCMX has no built-in permissions. Options:

1. **Open sharing**: Anyone downloads for free (default)
2. **Paid access**: Use blockchain smart contracts
3. **Invite-only**: Use encryption + share keys manually
4. **Geofencing**: App-level restrictions (not protocol)

---

## Deployment & Operations

### Q: How do I run DCMX in production?

**A:** Recommended setup:

```
┌─────────────────────────┐
│  Docker Container       │
│  (dcmx process)         │
└────────────┬────────────┘
             │
   ┌─────────┴──────────┐
   │                    │
   ↓                    ↓
/persistent/data    Port 8080 (mapped)
(volume mount)      (exposed)

Host:               Container:
/var/dcmx/content ← /app/dcmx/content
Port 8080        ← Port 8080
```

```bash
# Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["dcmx", "start", "--host", "0.0.0.0"]

# Run
docker run -v /var/dcmx:/app/dcmx -p 8080:8080 dcmx:latest
```

### Q: How do I monitor a node?

**A:** Use the built-in stats endpoint:

```bash
# Command line
dcmx stats

# HTTP endpoint
curl http://localhost:8080/peers | jq .
curl http://localhost:8080/tracks | jq .

# Metrics to track
- Peer count (growing? healthy?)
- Track count (enough content?)
- Upload/download rates (performance?)
- Error rates (connection issues?)
```

### Q: How do I handle backups?

**A:** DCMX content is automatically replicated:

```
Backup Strategy:
1. Content stored locally? Yes (automatic)
2. Replicate to peers? Yes (they download)
3. Need manual backup? No (peers backup for you)

Exception: Important metadata
- Backup ~/.dcmx/tracks.json
- Backup ~/.dcmx/peers.json
```

### Q: How much disk space do I need?

**A:** Depends on network participation:

```
Minimum:   1 GB (node software + OS)
Small:     10 GB (cache ~20-30 tracks)
Medium:    100 GB (cache ~500 tracks)
Large:     1 TB+ (full content mirror)
```

**Disk usage scaling:**
- Average MP3: 4-8 MB per track
- 10 GB storage: ~1200 tracks cached
- 100 GB storage: ~12,000 tracks cached

### Q: Can I limit bandwidth usage?

**A:** Yes, via configuration:

```bash
dcmx start \
  --upload-limit 10    # 10 Mbps upload max
  --download-limit 20  # 20 Mbps download max
```

---

## Compliance & Legal

### Q: Is DCMX legal?

**A:** DCMX itself is neutral technology. Legality depends on usage:

```
Legal uses:
✓ Distribute your own music
✓ Share with consent of copyright holder
✓ Private use (personal backups)
✓ Public domain content

Illegal uses:
✗ Distribute copyrighted music without permission
✗ Commercial use without licensing
✗ Circumvent DRM (in some jurisdictions)
```

**Responsibility: Yours**, not DCMX's.

### Q: What about DMCA/Copyright Law?

**A:** DCMX doesn't violate DMCA. However:

```
DCMX transfers your copyrighted music:
  Legal IF: You own the copyright
  Illegal IF: You don't have rights

DCMX doesn't add DRM:
  Note: You should add watermarking
  Optional: Embed license info in audio
```

### Q: Do I need licensing for artist payments?

**A:** Yes, if distributing third-party music:

```
If distributing your own music:
  - No licensing needed
  - Keep 100% of revenue
  - Note: Performance rights may apply (ASCAP/BMI)

If distributing others' music:
  - Mechanical license: Reproduction rights
  - Synchronization license: Use with video
  - Performance rights: Public performance
  
Cost: Varies ($0.00-5%+ per transaction)
```

### Q: What about privacy regulations (GDPR)?

**A:** DCMX should comply if you follow practices:

```
GDPR Requirements:
✓ Don't track users without consent
✓ Provide data deletion on request
✓ Encrypt personal data
✓ Audit trail for access
✓ 7-year compliance logs

DCMX compliance:
- Minimal data collection by default
- Implement deletion request handler
- Use TLS for encryption
- Log access
- Retain logs 7 years
```

---

## Troubleshooting

### Q: Node won't start - "Port 8080 already in use"

**A:** Change port:
```bash
# Check what's using port
lsof -i :8080

# Start on different port
dcmx start --port 9000

# Or kill existing process
sudo kill -9 <PID>
```

### Q: Can't connect to peers - "Connection refused"

**A:** Verify peer is running:

```bash
# Check if peer is live
curl http://peer-ip:8080/ping

# Check firewall
sudo ufw allow 8080

# Try explicit connection
dcmx start --peers peer-ip:8080 --port 8081
```

### Q: Download very slow - Expected 1 MB/s, getting 100 KB/s

**A:** Diagnose:

```bash
# 1. Check bandwidth limit
dcmx stats | grep bandwidth

# 2. Check peer quality
dcmx peers  # Are good peers available?

# 3. Try different peer
# (App-level, select manually)

# 4. Check network
ping peer-ip  # Latency ok?
iperf3 -c peer-ip  # Actual bandwidth?

# 5. Increase timeout
dcmx get HASH --timeout 60
```

### Q: Peer list keeps changing - why?

**A:** Normal behavior:

```
Peers go online/offline frequently:
  Node A: Online 2 hours, then offline
  Node B: Appears, disappears, reappears
  
DCMX handles this:
  - Tries to reach peers periodically
  - Marks offline peers for retry
  - Updates peer list dynamically
  
This is intentional (resilience)
```

### Q: How do I clear the cache?

**A:** Remove data directory:

```bash
# Backup first!
cp -r ~/.dcmx ~/.dcmx.backup

# Clear cache
rm -rf ~/.dcmx/content

# Restart node
dcmx start
```

### Q: Track doesn't appear on network - why?

**A:** Check these:

```bash
# 1. Is node running?
dcmx stats

# 2. Is track added?
dcmx list

# 3. Are peers connected?
dcmx peers

# 4. Check logs
dcmx start --verbose
```

If still missing:
- Try re-adding: `dcmx add song.mp3`
- Check file permissions
- Verify file isn't corrupted

---

## Resources

| Resource | Link |
|----------|------|
| **Technical Whitepaper** | `/docs/DCMX_TECHNICAL_WHITEPAPER.md` |
| **Architecture Reference** | `/docs/ARCHITECTURE_REFERENCE.md` |
| **Implementation Guide** | `/docs/IMPLEMENTATION_GUIDE.md` |
| **Developer Quickstart** | `/docs/DEVELOPER_QUICKSTART.md` |
| **GitHub Repository** | https://github.com/DCMX-Protocol/DCMX |
| **Discord Community** | https://discord.gg/dcmx |

---

**Document Version**: 1.0  
**Last Updated**: December 9, 2025  
**Maintained By**: DCMX Community
