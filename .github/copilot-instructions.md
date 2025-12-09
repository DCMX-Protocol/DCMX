# DCMX - AI Coding Agent Instructions

## Project Overview

DCMX is a **decentralized peer-to-peer music network** using mesh topology and content-addressed storage. The architecture eliminates central servers by enabling direct peer-to-peer content distribution where nodes maintain local content stores and discover peers through HTTP-based protocol.

## Architecture & Key Components

### Core Layer (`dcmx/core/`)
- **Node** (`node.py`): Main entity managing local state, peer connections, and network participation
  - Orchestrates ContentStore, Protocol, and Peer interactions
  - Uses aiohttp for HTTP server (routes: `/ping`, `/peers`, `/tracks`, `/discover`, `/content/{hash}`)
  - Async-first design throughout
  
- **Track** (`track.py`): Immutable metadata container for music
  - Content-addressed via SHA-256 hash of audio bytes
  - Serializable to/from dict for network transport
  - Static method `compute_content_hash(bytes)` for hash computation

### Network Layer (`dcmx/network/`)
- **Peer** (`peer.py`): Network identity with address + available tracks set
  - Unique `peer_id` (UUID) for identification
  - `available_tracks`: Set[str] of content hashes it can serve
  - Methods: `add_track()`, `has_track()`, `update_last_seen()`
  
- **Protocol** (`protocol.py`): Async HTTP client for peer communication
  - Single async method `connect(host, port)` for handshakes
  - Returns Peer + populates available_tracks from `/discover` response
  - Session management via aiohttp ClientSession

### Storage Layer (`dcmx/storage/`)
- **ContentStore** (`content_store.py`): Persistent content storage
  - Files stored as: `storage_path/{hash[:2]}/{hash}` (2-char prefix sharding for FS performance)
  - Methods: `store()`, `retrieve()`, `exists()`
  - All I/O is synchronous (no async)

## Critical Patterns & Conventions

### Content Addressing
- **Never** use filenames or IDs for content—always use SHA-256 hashes
- Hash computed from **audio bytes only** (not metadata)
- Enables automatic deduplication: identical files = identical hashes
- See `Track.compute_content_hash()` and `Track.get_metadata_hash()` for examples

### Async-Driven Design
- Node operations are async: `await node.start()`, `await node.stop()`, `await node.connect_to_peer()`
- Protocol calls are async: `await protocol.connect()`
- ContentStore is **synchronous** (sync filesystem I/O)—do not make it async
- Tests use `pytest-asyncio` with `asyncio_mode = auto` (see `pytest.ini`)

### Data Serialization
- Use `.to_dict()` / `.from_dict()` for network transport
- `asdict()` from dataclasses for Track → dict conversion
- Network protocol exchange: JSON payloads with `peer` and `tracks` keys

### Peer Discovery Flow
1. Local node calls `protocol.connect(remote_host, remote_port)`
2. Remote node receives POST `/discover` with `{"peer": local_peer.to_dict()}`
3. Remote responds: `{"peer": remote_peer.to_dict(), "tracks": [...]}`
4. Protocol parses response and populates `peer.available_tracks`

## Developer Workflows

### Running Tests
```bash
pytest                          # Run all tests
pytest tests/test_track.py      # Run specific test file
pytest -v --tb=short           # Verbose output with short tracebacks
pytest --asyncio-mode=auto     # Already default in pytest.ini
```

### Starting a Local Network
```bash
dcmx start --host 127.0.0.1 --port 8080
dcmx start --host 127.0.0.1 --port 8081 --peers 127.0.0.1:8080
```

### Adding Content
```bash
dcmx add song.mp3 --title "My Song" --artist "Artist" --album "Album"
dcmx list      # View available tracks
dcmx stats     # Node statistics
```

### Installation & Development
```bash
pip install -r requirements.txt
pip install -e .  # Editable install for development
```

## Important Implementation Details

### State Management
- **Node.peers**: Dict[str, Peer] mapping peer_id → Peer
- **Node.tracks**: Dict[str, Track] mapping content_hash → Track
- **Peer.available_tracks**: Set[str] of content hashes (not Track objects)
- Always update peer timestamps via `peer.update_last_seen()` on interaction

### Error Handling
- Protocol connection failures log errors but return None (see `protocol.connect()`)
- ContentStore operations check file existence before overwriting
- All file operations raise/log exceptions; CLI catches them

### Logging
- Standard `logging` module; each module creates its own logger: `logger = logging.getLogger(__name__)`
- Log levels: INFO for normal operations, DEBUG for detailed tracing, ERROR for failures
- CLI configures logging via `setup_logging(verbose=bool)`

## File Organization

```
dcmx/
  core/        # Business logic (Node, Track)
  network/     # P2P communication (Peer, Protocol)
  storage/     # Persistence (ContentStore)
  cli.py       # Command-line entry point
examples/      # Usage demonstrations
tests/         # Unit tests (async via pytest-asyncio)
```

## External Dependencies
- **aiohttp**: Async HTTP server/client for peer communication
- **cryptography**: Available but not yet actively used (for future verification)
- **msgpack**: Available for binary serialization (currently uses JSON)
- **pytest-asyncio**: Test async code with automatic event loop

## When Adding Features
1. **Content operations**: Always use content hashes, not filenames
2. **Network calls**: Use async/await; test with `@pytest.mark.asyncio`
3. **State changes**: Update Peer/Node dicts and Track metadata consistently
4. **New routes**: Add to Node HTTP app in `start()` method
5. **Storage**: Use ContentStore's path sharding pattern (`{hash[:2]}/{hash}`)

---

# REGULATORY & COMPLIANCE REQUIREMENTS

## SEC Token Classification (Howey Test)

**CRITICAL**: Native token may qualify as a security depending on reward structure.

### Token Classification Analysis - DCMX Specific
Your platform has mixed characteristics:

| Component | Security Risk | Notes |
|-----------|---|---|
| **NFT Sales** | LOW | You're selling your music, not a profit-bearing investment |
| **Voting Rewards** | **HIGH** | Creates "profits from efforts of others" (Howey prong) |
| **Energy/Participation Rewards** | LOW | Compensates actual work (like mining/staking) |
| **Wallet-to-Wallet Transfers** | LOW | Just money movement, not investment |

**Token Likely = Security IF**:
- Users expect voting rewards to appreciate/trade
- Rewards tied to platform growth (you controlling network)
- Token has no utility except voting/trading

**Token Likely = Utility IF**:
- Voting is purely governance (no profit expectation)
- Energy rewards compensate for actual network service
- Primary use case is purchasing NFTs

### Recommended Approach (Lower Risk)
```python
# Design token for UTILITY, not speculation:

@dataclass
class DCMXToken:
    """Platform utility token."""
    name: str = "DCMX Token"
    supply_cap: int = 1_000_000_000  # Fixed supply (prevents inflation)
    uses: List[str] = [
        "purchasing_nfts",      # Primary: buy your music NFTs
        "node_operation_fee",    # Stake to run node
        "voting_governance",     # Participate in DAO decisions
    ]
    
    # NOT: "speculative asset" or "profit-sharing"
    
    # Governance voting structure:
    # - 1 token = 1 vote
    # - Voting on: feature roadmap, platform fees, content moderation
    # - NO monetary rewards for voting
    # - NO profit distribution to token holders

# Energy rewards (MORE defensible):
@dataclass
class EnergyReward:
    """Reward for actual network participation."""
    node_id: str
    hours_served: float
    bandwidth_mbps: float
    reward_amount: int  # DCMX tokens for work
    
    # This is like mining: you get paid for providing compute/bandwidth
    # NOT "profits from efforts of others"
```

### Compliance Path
1. **Structure token as governance utility** (not investment security)
2. **NO promised returns** on token holding
3. **NO percentage of platform revenue** to token holders
4. **Voting must be non-binding** (advisory only, you make final decisions)
5. **Clear white paper** explaining token economics
6. **File Form D with SEC** if issuing to accredited investors (optional but safer)

### What to Avoid (Securities Red Flags)
- ❌ "Token will appreciate as platform grows"
- ❌ "Voting rewards proportional to token amount"
- ❌ "Earn staking yields"
- ❌ "Platform revenue shared with token holders"
- ❌ "Limited supply for scarcity-driven value"

✅ Instead say:
- "Token needed to use platform features"
- "Node operators compensated for real work (bandwidth/energy)"
- "Governance voting (advisory, not binding)"
- "Fixed supply, no inflation"

---

## Music Rights & Licensing

### Copyright Status (SIMPLIFIED)
- **Your songs**: You own composition & master → full distribution rights
- **No third-party licensing needed** for your own content
- **DMCA protection still applies**: Watermarking prevents unauthorized copying
- **ISRC codes (optional)**: Useful for streaming registry but not required for P2P distribution

### Implementation Requirements
1. **Track metadata must include**:
   - Artist/rights holder information (you)
   - ISRC code (optional, for streaming attribution)
   - Content hash for deduplication
   - Edition/version info (limited edition numbering)

2. **Track ownership verification**:
   ```python
   @dataclass
   class Track:
       """Track with ownership metadata."""
       title: str
       artist: str  # YOU - the rights holder
       content_hash: str  # SHA-256 of audio
       owner_wallet: str  # Your blockchain wallet address
       edition_number: Optional[int]  # "Limited Edition 1 of 100"
       isrc: Optional[str]  # International Standard Recording Code
       
       def verify_ownership(self, signer_wallet: str) -> bool:
           """Verify signer has rights to distribute."""
           return signer_wallet == self.owner_wallet
   ```

3. **No license validation needed**:
   - Store any Track you've created
   - Watermark prevents casual copying
   - DMCA § 1201 covers anti-circumvention

### Royalty Distribution (P2P NFT Sales)
- **Artist (you) receives**: Primary sale price (100% or minus platform fee)
- **Platform fee**: ~0-10% (transaction/network maintenance) - optional
- **Secondary sales**: Smart contract can enforce royalties on resale (e.g., 10% on each resale)
- **Node operators**: Reward in native token for serving content (not from artist revenue)
- **Auto-payout via blockchain**: Use smart contract to lock percentages

---

## Financial Compliance (AML/KYC)

### Money Transmission License
Your token + P2P payments likely trigger **FinCEN Money Transmitter regulations** in all 50 states (varies, but ~$500K-$2M compliance cost).

### Customer Identity Verification (KYC)
1. **Know Your Customer (KYC) implementation**:
   ```python
   @dataclass
   class UserProfile:
       """Compliant user identity tracking."""
       user_id: str  # UUID, NOT tied to real name in code
       wallet_address: str  # Blockchain address
       
       # Separately encrypted/stored in compliance DB
       # DO NOT log or transmit unencrypted
       kyc_verified: bool
       verification_timestamp: str  # When KYC completed
       verification_level: int  # 0=unverified, 1=basic, 2=enhanced
       jurisdiction: str  # "US" requires stricter rules
   ```

2. **Collect at token purchase**:
   - Full legal name, DOB, SSN (US)
   - Proof of address (utility bill, not older than 3 months)
   - Selfie ID verification (biometric match)
   - Beneficial ownership info if purchaser is entity

3. **Transaction monitoring**:
   - Flag transactions >$10K (report to FinCEN within 30 days)
   - Monitor for structuring (multiple <$10K to evade reporting)
   - Block sanctioned addresses (OFAC list)

### Anti-Money Laundering (AML)
```python
async def validate_transaction(sender_wallet: str, amount: int, recipient_wallet: str):
    """Check AML compliance before executing."""
    
    # Check OFAC sanctions list
    if check_ofac_list(sender_wallet) or check_ofac_list(recipient_wallet):
        log_compliance_alert(f"OFAC block: {sender_wallet}")
        raise ComplianceException("Transaction blocked")
    
    # Monitor patterns
    sender_24h_volume = await get_transaction_volume(sender_wallet, hours=24)
    if sender_24h_volume > DAILY_LIMIT:
        alert_compliance_team(sender_wallet, sender_24h_volume)
```

---

## Cryptographic Audio Watermarking & Fingerprinting

### Legal Basis
- Proves rightful ownership & deters unauthorized copying
- Enables DMCA compliance (Digital Millennium Copyright Act)
- Creates audit trail for royalty distribution

### Implementation Requirements
1. **Watermarking (metadata injection, invisible to ear)**:
   - Embed rights holder ID, license terms, NFT contract address
   - Use ISO/IEC 18040 (watermarking for audio) compliant method
   - Must survive:
     - Compression (MP3, AAC conversion)
     - Format changes (WAV → FLAC)
     - Minor audio processing
   - **Never remove watermark on P2P distribution**

2. **Fingerprinting (content hash, not tied to copy)**:
   - Generate perceptual hash (like Shazam's MFCC algorithm)
   - NOT the same as Track.compute_content_hash()
   - Allows detecting same song across:
     - Different bitrates (128kbps vs 320kbps MP3)
     - Format conversions (MP3 vs FLAC)
     - Minor remixes/covers (fuzzy matching)

### Code Structure
```python
from dcmx.core.track import Track
from dcmx.crypto.audio_watermark import AudioWatermark
from dcmx.crypto.audio_fingerprint import AudioFingerprint

@dataclass
class ProtectedTrack(Track):
    """Track with DRM compliance."""
    watermark: str  # Embedded in audio bytes
    perceptual_fingerprint: str  # Fuzzy content ID
    drm_enabled: bool  # Prevent casual copying
    license_terms: MusicLicense  # Tied to this copy
    
    @staticmethod
    async def create_from_file(
        audio_file_path: str,
        metadata: dict,
        license: MusicLicense
    ) -> "ProtectedTrack":
        """Create track with mandatory watermark/fingerprint."""
        content = Path(audio_file_path).read_bytes()
        
        # Add watermark (store license metadata)
        watermarked = AudioWatermark.embed(
            content,
            license.rights_holder,
            license.territory,
            license.expiry_date
        )
        
        # Generate fingerprint
        fingerprint = AudioFingerprint.generate(watermarked)
        
        track = ProtectedTrack(
            title=metadata['title'],
            artist=metadata['artist'],
            content_hash=Track.compute_content_hash(watermarked),
            watermark=watermarked,
            perceptual_fingerprint=fingerprint,
            license_terms=license,
            drm_enabled=True,
            **metadata
        )
        return track
```

### Compliance Notes
- Watermarks must be **irremovable** (DMCA § 1201 requirement)
- Fingerprinting must **not** prevent legitimate use
- Keep audit log of all watermark embeddings

---

## Data Privacy & GDPR/CCPA

### Personal Data Categories
- **KYC data**: Name, SSN, address (HIGHLY regulated)
- **Transaction history**: Wallet addresses, amounts, dates
- **User activity**: Voting patterns, song preferences, network participation
- **Device/location**: IP address, device ID (if collected)

### Storage Segregation (CRITICAL)
```python
class ComplianceDataStore:
    """Separate storage for personal vs anonymous data."""
    
    def __init__(self, compliant_db_path: Path):
        """Use encrypted, access-controlled database."""
        self.kyc_db = SecureDatabase(
            compliant_db_path / "kyc",
            encryption="AES-256",
            audit_log=True
        )
        self.transaction_log = AuditLog(
            compliant_db_path / "transactions",
            immutable=True
        )
    
    def store_kyc(self, user_id: str, kyc_data: dict):
        """Store in separate encrypted vault."""
        # NEVER in same database as Track/Peer data
        self.kyc_db.encrypt_and_store(user_id, kyc_data)
    
    async def right_to_deletion(self, user_id: str):
        """GDPR/CCPA data deletion request (30-day window)."""
        # Delete KYC data
        self.kyc_db.delete(user_id)
        
        # Keep transaction log (tax/audit requirements)
        self.transaction_log.mark_anonymized(user_id)
```

### Required Privacy Policies
- **Data retention**: How long you keep KYC data (recommend: until transaction closes + 3 years tax hold)
- **Deletion requests**: 30-day response window (GDPR) or 45 days (CCPA)
- **Data breaches**: Notify users within 30 days if >5,000 records exposed
- **Third-party sharing**: Explicitly disclose (e.g., blockchain explorer viewing transactions)

### LoRa Network Privacy
- LoRa nodes transmit unencrypted by default
- **Encrypt all user data at rest**: Use TLS 1.3+ for peer-to-peer
- **Never broadcast wallet addresses** unencrypted over LoRa
- Assume LoRa traffic is public; use zero-knowledge proofs for private transactions

---

## State Regulatory Compliance (Money Transmission)

### State License Requirements (U.S.)
Most states classify tokenized peer-to-peer payments as "money transmission" requiring state licenses:

| State | License Type | Cost | Notes |
|-------|---|---|---|
| **CA** | Money Transmitter License | $250K-$1M | Ongoing compliance |
| **NY** | BitLicense | $5K + ongoing | New York only |
| **TX** | Money Services License | $50K-$250K | Strict reserve requirements |
| **Most other states** | Money Transmitter | $25K-$500K | 10-50 states needed = $500K-$5M total |

**Practical approach**:
1. Start by **only serving your own songs** (no peer uploads) → more lenient classification
2. Use **existing stablecoin infrastructure** (Ethereum, Polygon) to sidestep licensing initially
3. Consult blockchain-specialized attorneys ($400-800/hr) before full P2P token launch

### Implementation: Geofencing
```python
from dcmx.compliance.geo_restrictions import GeoRestriction

class ComplianceNode(Node):
    """Node with state-level compliance."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geo_restriction = GeoRestriction()
    
    async def validate_peer_transaction(self, peer_id: str, amount: int):
        """Check state compliance before allowing transaction."""
        peer_location = await self.geo_restriction.get_peer_location(peer_id)
        
        # Block transactions from states without license
        if not self.geo_restriction.is_licensed_state(peer_location):
            logger.warning(f"Blocking transaction from {peer_location}")
            raise ComplianceException(
                f"Service not available in {peer_location}. "
                "Licensed states: CA, NY, TX, ..."
            )
        
        return True
```

---

## Audit Logging & Evidence Retention

### Immutable Transaction Log
**Every transaction must be logged and retained for 7 years (SEC requirement).**

```python
@dataclass
class ComplianceLog:
    """Immutable audit trail."""
    timestamp: str  # ISO format, UTC
    event_type: str  # "NFT_PURCHASE", "TOKEN_REWARD", "VOTING", etc
    user_id: str  # Anonymized
    wallet_address: str  # Blockchain address
    amount: int  # Token amount or USD equivalent
    action: str  # What happened
    result: str  # "SUCCESS" | "REJECTED"
    rejection_reason: str  # If rejected (AML/KYC/geo-block)
    
    def to_immutable_record(self) -> str:
        """Convert to tamper-evident format."""
        record = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(record.encode()).hexdigest()
```

### Logging Requirements
- **Geolocation**: Where transaction originated (IP → coordinates)
- **Compliance checks**: Which rules were applied, pass/fail
- **User consent**: Screenshots of terms-of-service acceptance
- **Regulatory events**: Sanctions checks, AML flags, license changes

---

## Compliance Checklist for Feature Development

Before releasing ANY feature involving:

### Tokens / Rewards
- ☐ Consulted securities attorney re: Howey Test
- ☐ Verified no unregistered securities offering
- ☐ Implemented transfer lock-up periods (if needed)
- ☐ Audit trail logs token distribution
- ☐ User consent for token economics disclosed

### NFT Sales
- ☐ Your music ownership documented (composition & master rights)
- ☐ Watermark + fingerprint embedded in content
- ☐ Smart contract locks artist royalty percentage
- ☐ ISRC code stored (optional, for streaming attribution)

### Peer-to-Peer Payments
- ☐ KYC verification at $10K+ lifetime spend threshold
- ☐ OFAC sanctions check before transaction
- ☐ AML monitoring active (pattern detection)
- ☐ State geofencing enforced
- ☐ 7-year immutable audit log

### Voting / User Data
- ☐ Privacy policy updated and user-acknowledged
- ☐ KYC data stored separately from transaction data
- ☐ Deletion requests processed within 30 days
- ☐ Data breach notification plan in place

---

## External Compliance Resources

- **SEC guidance on tokens**: https://www.sec.gov/news/statement/statement-clayton-2017-12-11
- **FinCEN MSB registration**: https://www.fincen.gov/money-services-business
- **OFAC sanctions list**: https://home.treasury.gov/policy-issues/financial-sanctions/specially-designated-nationals-list-data-formats-data-schemas
- **State money transmitter laws**: Varies by state; consult attorney
- **Audio watermarking ISO standards**: ISO/IEC 18040-1:2021
- **Music licensing**: Contact ASCAP/BMI/SESAC or MRI (MusicGremlin Rights Interchange)

---

# MULTI-AGENT DEVELOPMENT GUIDE

This section provides guidance for specialized AI agents building different components of DCMX. Each agent has a specific responsibility and should follow the patterns below.

## Agent 1: Blockchain Smart Contracts Agent (`dcmx-blockchain-agent`)

**Responsibility**: Build Web3 integration, NFT smart contracts, token economics, and royalty distribution.

**Tech Stack**:
- **Blockchain**: Ethereum/Polygon (Solana optional for lower fees)
- **Language**: Solidity (smart contracts) + Python (contract deployment/interaction)
- **Libraries**: web3.py, Brownie, Hardhat, ethers.py
- **Standards**: ERC-721 (NFTs), ERC-20 (utility token)

**Key Deliverables**:
1. **MusicNFT.sol**: ERC-721 smart contract for limited edition music NFTs
   ```solidity
   // Contract structure:
   // - Mint function: Creates limited editions (e.g., 100 copies of song)
   // - Ownership tracking: Links to DCMX content hash
   // - Royalty enforcement: Artist receives % on secondary sales (ERC-2981)
   // - Watermark metadata: Stores audio fingerprint + watermark hash
   ```

2. **DCMXToken.sol**: ERC-20 utility token for platform
   ```solidity
   // Token features:
   // - Fixed supply (no inflation)
   // - Reward minting: Controlled by governance contract
   // - NO automatic appreciation mechanism
   // - Transfer restrictions: Optional lock-up periods
   ```

3. **GovernanceDAO.sol**: Voting contract for platform decisions
   ```solidity
   // Governance structure:
   // - 1 token = 1 vote (advisory only)
   // - Voting periods: 48 hours
   // - Quorum: 10% of token supply
   // - Decision implementation: Controlled by team multisig (NOT automatic)
   ```

4. **RewardDistributor.sol**: Distribute rewards for network participation
   ```solidity
   // Reward categories:
   // - Energy rewards: Based on node uptime/bandwidth (verifiable on-chain)
   // - Voting engagement: Fixed amounts per valid vote (NOT proportional)
   // - Referral bonuses: Fixed amounts for peer referrals
   // - Platform stability: Weekly allocation for liquidity provision
   ```

**Python Integration Pattern**:
```python
from web3 import Web3
from dcmx.blockchain.contract_manager import ContractManager

class BlockchainAgent:
    """Handles Web3 interactions."""
    
    def __init__(self, rpc_url: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = self.w3.eth.account.from_key(private_key)
        self.contracts = ContractManager(self.w3)
    
    async def mint_nft(
        self, 
        track_hash: str, 
        edition_num: int, 
        max_editions: int, 
        price_wei: int
    ) -> str:
        """Mint limited edition NFT."""
        tx = self.contracts.music_nft.functions.mint(
            self.account.address,
            track_hash,
            edition_num,
            max_editions,
            price_wei
        ).build_transaction({
            'from': self.account.address,
            'gas': 300_000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash.hex()
    
    async def distribute_rewards(
        self, 
        node_id: str, 
        reward_amount: int, 
        reward_type: str  # "energy" | "voting" | "referral"
    ) -> str:
        """Distribute tokens for network participation."""
        # Verify reward legitimacy before sending
        assert reward_type in ["energy", "voting", "referral"]
        assert reward_amount > 0
        
        tx = self.contracts.reward_distributor.functions.distribute(
            node_id,
            reward_amount,
            reward_type
        ).build_transaction({...})
        
        return self.w3.eth.send_raw_transaction(
            self.w3.eth.account.sign_transaction(tx, self.account.key).rawTransaction
        ).hex()
```

**Compliance Requirements for Agent**:
- ☐ Verify token supply is fixed (no inflation)
- ☐ Confirm voting is advisory only (not binding)
- ☐ Validate reward structure (tied to work, not investment returns)
- ☐ Document smart contract audit plan (third-party review before mainnet)
- ☐ Implement 2-of-3 multisig for admin functions (no single point of failure)

---

## Agent 2: Audio Watermarking & Fingerprinting Agent (`dcmx-audio-agent`)

**Responsibility**: Implement cryptographic audio watermarking, perceptual fingerprinting, and DRM compliance.

**Tech Stack**:
- **Audio Processing**: librosa, pydub, soundfile
- **Watermarking**: PyDub + custom FFT-based embedding (ISO/IEC 18040 compliant)
- **Fingerprinting**: librosa (MFCC), essentia for perceptual hashing
- **Cryptography**: cryptography, hashlib

**Key Deliverables**:
1. **AudioWatermark.py**: Embed license metadata into audio
   ```python
   class AudioWatermark:
       """Embed irremovable watermark into audio content."""
       
       @staticmethod
       async def embed(
           audio_bytes: bytes,
           rights_holder: str,
           nft_contract_address: str,
           edition_number: int
       ) -> bytes:
           """
           Embed watermark containing:
           - Rights holder ID (encrypted)
           - NFT contract address + token ID
           - Edition number
           - Timestamp
           
           Survives: MP3 compression, format conversion, minor audio processing
           """
           # 1. Parse audio
           # 2. Apply FFT (Fast Fourier Transform)
           # 3. Embed license data in low-frequency magnitude spectrum
           # 4. Apply inverse FFT
           # 5. Return watermarked audio bytes
       
       @staticmethod
       async def verify(
           audio_bytes: bytes,
           expected_rights_holder: str
       ) -> bool:
           """Extract and verify watermark."""
   ```

2. **AudioFingerprint.py**: Generate perceptual hash (fuzzy matching)
   ```python
   class AudioFingerprint:
       """Generate perceptual fingerprint for content matching."""
       
       @staticmethod
       async def generate(audio_bytes: bytes) -> str:
           """
           Generate 256-bit fingerprint resistant to:
           - Different bitrates (MP3 128kbps vs 320kbps)
           - Format conversions (MP3 → WAV → FLAC)
           - Minor audio processing
           
           Returns: Hex string of perceptual hash
           """
           # Use MFCC (Mel-frequency cepstral coefficients)
           # Generate constellation map (landmark-based fingerprinting)
           # Return compact hash for fast lookup
       
       @staticmethod
       async def match_similarity(
           fingerprint1: str,
           fingerprint2: str,
           threshold: float = 0.95
       ) -> float:
           """Compare two fingerprints, return similarity score."""
   ```

3. **ProtectedTrack.py**: Integrate watermarking into Track model
   ```python
   @dataclass
   class ProtectedTrack(Track):
       """Track with mandatory watermarking + fingerprinting."""
       watermark_hash: str  # Verification hash of embedded watermark
       perceptual_fingerprint: str  # Fuzzy content ID
       nft_contract_address: str  # Ethereum contract
       token_id: int  # NFT token ID
       edition_number: int  # Edition # in limited set
       max_editions: int  # Total copies
       
       @staticmethod
       async def create_from_file(
           audio_file_path: str,
           metadata: dict,
           nft_contract_address: str,
           token_id: int,
           edition_number: int,
           max_editions: int
       ) -> "ProtectedTrack":
           """Create protected track with watermark + fingerprint."""
           content = Path(audio_file_path).read_bytes()
           
           # Generate watermark
           watermarked = await AudioWatermark.embed(
               content,
               rights_holder=metadata['artist'],
               nft_contract_address=nft_contract_address,
               edition_number=edition_number
           )
           
           # Generate fingerprint
           fingerprint = await AudioFingerprint.generate(watermarked)
           
           # Compute watermark verification hash
           watermark_hash = hashlib.sha256(watermarked).hexdigest()
           
           return ProtectedTrack(
               title=metadata['title'],
               artist=metadata['artist'],
               content_hash=Track.compute_content_hash(watermarked),
               watermark_hash=watermark_hash,
               perceptual_fingerprint=fingerprint,
               nft_contract_address=nft_contract_address,
               token_id=token_id,
               edition_number=edition_number,
               max_editions=max_editions,
               duration=metadata.get('duration', 0),
               size=len(watermarked),
               **metadata
           )
   ```

**Compliance Requirements for Agent**:
- ☐ Watermark is irremovable (DMCA § 1201 compliant)
- ☐ Fingerprinting doesn't prevent legitimate playback
- ☐ Audit log tracks all watermark operations
- ☐ Third-party verification: Test watermark survives compression
- ☐ ISRC code stored (for future streaming registration)

---

## Agent 3: KYC/AML Compliance Agent (`dcmx-compliance-agent`)

**Responsibility**: Implement customer identity verification, OFAC sanctions checking, and transaction monitoring.

**Tech Stack**:
- **KYC Verification**: twilio-verify (SMS), stripe-identity (biometric), or custom
- **OFAC Checking**: ofac-checker library, manual SDN list integration
- **Database**: Encrypted PostgreSQL or AWS Secrets Manager
- **Monitoring**: Real-time transaction analysis, anomaly detection

**Key Deliverables**:
1. **KYCVerifier.py**: Customer identity verification
   ```python
   class KYCVerifier:
       """Verify user identity for compliance."""
       
       async def verify_user(
           self,
           user_id: str,
           legal_name: str,
           dob: str,  # YYYY-MM-DD
           ssn: str,  # Hashed
           address: str,
           country: str = "US"
       ) -> Dict[str, Any]:
           """
           Verify user identity through:
           1. Name + DOB database check
           2. Address verification (utility bill scan)
           3. Biometric verification (selfie + ID match)
           4. SSN validation
           
           Returns: {"verified": bool, "level": int, "timestamp": str}
           """
           # 1. Check existing KYC records
           # 2. Call third-party KYC provider
           # 3. Store encrypted results in secure database
           # 4. Return verification status
       
       async def get_verification_level(self, user_id: str) -> int:
           """Return KYC level (0=none, 1=basic, 2=enhanced)."""
   ```

2. **OFACChecker.py**: Sanctions list compliance
   ```python
   class OFACChecker:
       """Check wallet addresses against OFAC sanctions list."""
       
       def __init__(self):
           # Load SDN (Specially Designated Nationals) list weekly from Treasury
           self.sdn_list = self._load_sdn_list()
           self.entity_cache = {}
       
       def _load_sdn_list(self) -> Set[str]:
           """
           Download latest OFAC SDN list from:
           https://home.treasury.gov/policy-issues/financial-sanctions/sdn-list
           
           Parse and index wallet addresses, company names, aliases
           """
       
       async def check_address(self, wallet_address: str) -> bool:
           """
           Check if wallet is on sanctions list.
           
           Returns: True if blocked (sanctioned), False if allowed
           """
           # Check exact matches first
           # Check blockchain history for connections to sanctioned entities
           # Log all checks for audit trail
       
       async def check_entity(self, entity_name: str) -> bool:
           """Check if company/person name appears on OFAC list."""
   ```

3. **TransactionMonitor.py**: Real-time transaction analysis
   ```python
   class TransactionMonitor:
       """Monitor transactions for suspicious patterns."""
       
       async def validate_transaction(
           self,
           user_id: str,
           wallet_from: str,
           wallet_to: str,
           amount_usd: float,
           transaction_type: str  # "token_purchase" | "nft_sale" | "transfer"
       ) -> Dict[str, Any]:
           """
           Check transaction against AML rules:
           
           Rules:
           1. >$10K → File FinCEN SAR within 30 days
           2. Multiple <$10K same hour → Structuring flag
           3. Velocity check: >$100K in 24h → Alert
           4. Geographic check: Sanctioned country → Block
           5. Destination check: OFAC list → Block
           """
           
           # Perform all checks
           # If any rule triggered, log and raise exception
           # Otherwise, proceed with transaction
       
       async def generate_sar_report(
           self,
           transaction_id: str,
           suspicious_activity: str,
           user_id: str
       ) -> str:
           """Generate Suspicious Activity Report for FinCEN."""
   ```

4. **ComplianceDatabase.py**: Encrypted storage for sensitive data
   ```python
   class ComplianceDatabase:
       """Secure, segregated storage for KYC/transaction data."""
       
       def __init__(self, db_url: str, encryption_key: str):
           self.engine = create_engine(db_url)
           self.cipher = Fernet(encryption_key)
       
       async def store_kyc(
           self,
           user_id: str,
           kyc_data: Dict[str, str]  # {name, ssn, address, etc}
       ) -> None:
           """
           Encrypt and store KYC data in separate schema.
           NEVER store in same database as Track/Peer data.
           """
       
       async def store_transaction(
           self,
           transaction_id: str,
           user_id: str,
           amount: float,
           timestamp: str,
           compliance_checks: Dict[str, bool]
       ) -> None:
           """Store immutable transaction log (7-year retention)."""
       
       async def audit_log(self, action: str, details: Dict) -> None:
           """Log all compliance operations for regulatory review."""
   ```

**Compliance Requirements for Agent**:
- ☐ KYC data encrypted at rest (AES-256)
- ☐ Separate database schema from public data (Track/Peer)
- ☐ OFAC list updated weekly (automatic)
- ☐ Transaction monitoring alerts compliance team
- ☐ FinCEN SAR reports filed within 30 days
- ☐ 7-year audit trail maintained
- ☐ Data deletion requests processed within 30 days (GDPR/CCPA)

---

## Agent 4: LoRa Network Infrastructure Agent (`dcmx-lora-agent`)

**Responsibility**: Build LoRa mesh network layer, bandwidth incentives, and distributed node coordination.

**Tech Stack**:
- **LoRa Library**: pylorawan, meshtastic-python, or custom LoRaWAN implementation
- **Network Coordination**: async/await with aiohttp for coordination server
- **Routing**: Geographic mesh routing (AODV or similar)
- **Bandwidth Tracking**: Per-node statistics, bandwidth accounting
- **Incentives**: Integration with blockchain for energy rewards

**Key Deliverables**:
1. **LoRaNode.py**: Extended Node for mesh network
   ```python
   class LoRaNode(Node):
       """Node with LoRa mesh capability."""
       
       def __init__(
           self,
           host: str,
           port: int,
           lora_device: str = "/dev/ttyUSB0",  # LoRa modem
           bandwidth_limit_mbps: float = 5.0,  # Rate limit
       ):
           super().__init__(host, port)
           self.lora_device = lora_device
           self.bandwidth_limit = bandwidth_limit_mbps
           
           # LoRa-specific state
           self.mesh_peers: Dict[str, LoRaPeer] = {}  # Mesh neighbors
           self.routing_table: Dict[str, Route] = {}  # Geographic routes
           self.bandwidth_stats = BandwidthStats()
       
       async def broadcast_content(self, track_hash: str) -> None:
           """
           Broadcast track availability to mesh neighbors.
           Uses LoRa regional parameters (lower bandwidth than WiFi).
           """
       
       async def receive_mesh_packet(self, packet: bytes) -> None:
           """Handle incoming LoRa mesh packet."""
       
       async def calculate_bandwidth_reward(self) -> int:
           """
           Calculate token reward based on:
           - Bytes served this period
           - Uptime percentage
           - Geographic coverage area
           
           Returns: Reward amount in tokens (0 if no activity)
           """
   ```

2. **BandwidthAccounting.py**: Track network usage
   ```python
   @dataclass
   class BandwidthStats:
       """Track node bandwidth usage."""
       node_id: str
       bytes_uploaded: int = 0  # Data served to other nodes
       bytes_downloaded: int = 0  # Data received from other nodes
       uptime_seconds: float = 0.0  # How long online this period
       unique_peers_served: int = 0  # Peer diversity bonus
       geographic_region: str = ""  # For incentive distribution
       
       def get_reward_score(self) -> float:
           """Calculate reward based on service metrics."""
           # Rewards favor consistency + diversity
           uptime_factor = self.uptime_seconds / (24 * 3600)  # % of day
           bandwidth_factor = self.bytes_uploaded / (100 * 1024**2)  # % of 100MB
           diversity_factor = min(self.unique_peers_served / 50, 1.0)
           
           return (uptime_factor * 0.5 + 
                   bandwidth_factor * 0.3 + 
                   diversity_factor * 0.2)
   ```

3. **MeshRouting.py**: Geographic routing
   ```python
   class MeshRouter:
       """Coordinate mesh routing with geographic awareness."""
       
       async def find_route(
           self,
           destination_node_id: str,
           source_lat: float,
           source_lon: float
       ) -> List[LoRaPeer]:
           """
           Find route to destination using:
           - Geographic proximity (prefer closer hops)
           - Uptime history (prefer reliable nodes)
           - Bandwidth availability
           
           Returns: Ordered list of hops
           """
       
       async def broadcast_route_update(self) -> None:
           """
           Periodically share location + capacity with neighbors.
           Update interval: 5 minutes (conservative for LoRa bandwidth)
           """
   ```

4. **RewardCalculator.py**: Determine energy rewards
   ```python
   class RewardCalculator:
       """Calculate token rewards for network participation."""
       
       async def calculate_period_reward(
           self,
           node_id: str,
           period_start: str,  # ISO timestamp
           period_end: str
       ) -> int:
           """
           Calculate token reward for a period (e.g., 1 week):
           
           Base calculation:
           - Minimum: 10 tokens (for just being online)
           - Bandwidth bonus: 1 token per 100MB served
           - Uptime bonus: +20% for >99% uptime
           - Coverage bonus: +10% for >10 unique peers
           - Regional bonus: Variable by network density
           
           Returns: Reward amount in tokens
           """
           stats = await self.get_bandwidth_stats(node_id, period_start, period_end)
           base_reward = 10
           
           bandwidth_bonus = (stats.bytes_uploaded / (100 * 1024**2)) * 1
           uptime_bonus = (stats.uptime_seconds / (7 * 24 * 3600)) * 0.2
           coverage_bonus = min(stats.unique_peers_served / 10, 1.0) * 0.1
           
           total = base_reward + bandwidth_bonus
           if stats.uptime_seconds / (7 * 24 * 3600) > 0.99:
               total *= 1.2
           
           return int(total)
   ```

**Compliance Requirements for Agent**:
- ☐ All peer-to-peer traffic encrypted (TLS 1.3+)
- ☐ No unencrypted wallet addresses on LoRa
- ☐ Reward structure tied to actual work (not speculation)
- ☐ Bandwidth accounting auditable (7-year logs)
- ☐ Geographic routing respects data residency laws
- ☐ Spam protection: Rate limits prevent abuse

---

## Multi-Agent Coordination Pattern

**Orchestration Strategy** (using Microsoft Agent Framework):

```python
from agent_framework import Agent, GroupChat, AssistantAgent

# Define specialized agents
blockchain_agent = Agent(
    name="Blockchain Agent",
    instructions="Build smart contracts for NFT sales and token rewards",
    system_prompt="""You are an expert Solidity developer and Web3 architect.
    Build secure, auditable smart contracts following best practices.
    Focus on: ERC-721 NFTs, ERC-20 tokens, governance, reward distribution."""
)

audio_agent = Agent(
    name="Audio Agent", 
    instructions="Implement audio watermarking and fingerprinting",
    system_prompt="""You are an expert in digital signal processing and DRM.
    Implement watermarking that survives compression and format conversion.
    Ensure DMCA § 1201 compliance for irremovable protection."""
)

compliance_agent = Agent(
    name="Compliance Agent",
    instructions="Build KYC/AML compliance and regulatory tracking",
    system_prompt="""You are an expert in financial compliance and regulations.
    Implement KYC verification, OFAC checking, transaction monitoring.
    Focus on: data security, audit logging, regulatory reporting."""
)

lora_agent = Agent(
    name="LoRa Agent",
    instructions="Build mesh network and bandwidth incentives",
    system_prompt="""You are an expert in mesh networks and distributed systems.
    Build resilient LoRa infrastructure with fair reward mechanisms.
    Focus on: geographic routing, bandwidth accounting, energy incentives."""
)

# Coordinate via group chat
group_chat = GroupChat(
    agents=[blockchain_agent, audio_agent, compliance_agent, lora_agent],
    max_turns=20,
    task="""
    You are building DCMX, a decentralized music NFT platform with LoRa mesh network.
    
    Blockchain Agent: Design smart contracts for NFT sales and token rewards
    Audio Agent: Implement audio watermarking and DRM protection
    Compliance Agent: Build KYC/AML compliance layer
    LoRa Agent: Build mesh network infrastructure
    
    Deliverables:
    1. Smart contract architecture (Solidity code)
    2. Audio watermarking implementation (Python)
    3. KYC/AML compliance system (Python)
    4. LoRa mesh network layer (Python + LoRaWAN)
    
    Each agent must coordinate with others to ensure:
    - Token rewards link to bandwidth metrics (LoRa → Blockchain)
    - Watermarked content tied to NFT contracts (Audio → Blockchain)
    - Transactions verified by compliance layer (Compliance → Blockchain)
    """
)

# Run orchestration
result = await group_chat.run()
```

---

## Integration Points Between Agents

| Agent | Dependencies | Provides To |
|-------|---|---|
| **Blockchain** | Audio fingerprints, Compliance approval | Token distribution to all agents |
| **Audio** | NFT contract address (from Blockchain) | Watermarked content hash to Blockchain |
| **Compliance** | User KYC approval required | Transaction approval to Blockchain, Bandwidth rewards to LoRa |
| **LoRa** | Bandwidth metrics to Compliance | Reward eligibility to Blockchain, Routing updates to Network |

---

## Development Phases

**Phase 1** (Weeks 1-2): Foundation
- Blockchain Agent: Deploy testnet contracts
- Audio Agent: Implement watermark embedding/verification
- Compliance Agent: Set up KYC verification
- LoRa Agent: Mesh network protocol design

**Phase 2** (Weeks 3-4): Integration
- All agents: Connect data flows
- Blockchain Agent: Link rewards to LoRa metrics
- Compliance Agent: Validate all transactions
- Audio Agent: Embed NFT metadata in watermarks

**Phase 3** (Week 5): Testing & Audit
- Security audit of smart contracts
- Watermark robustness testing (compression survival)
- Compliance testing (KYC/OFAC flows)
- LoRa network stress testing

**Phase 4** (Week 6): Deployment & Monitoring
- Testnet → Mainnet migration
- Compliance monitoring setup
- Bandwidth reward distribution starts
- Ongoing agent maintenance
