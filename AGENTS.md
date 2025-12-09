# DCMX Multi-Agent Development System

This document describes the four specialized AI agents that build and maintain different components of the DCMX platform.

## 📋 Overview

Each agent specializes in a specific domain and can work independently or coordinate with other agents to deliver integrated functionality.

| Agent | Responsibility | Language | Key Files |
|-------|---|---|---|
| **Blockchain Agent** | Smart contracts, NFTs, tokens, governance | Solidity + Python | `dcmx/blockchain/` |
| **Audio Agent** | Watermarking, fingerprinting, DRM | Python (librosa, pydub) | `dcmx/audio/` |
| **Compliance Agent** | KYC/AML, OFAC checks, audit logging | Python | `dcmx/compliance/` |
| **LoRa Agent** | Mesh networking, bandwidth rewards | Python (pylorawan) | `dcmx/lora/` |

---

## 🚀 Quick Start for Each Agent

### Agent 1: Blockchain Agent

**Focus**: Build smart contracts for NFT sales and token distribution

**Setup**:
```bash
# Install dependencies
pip install web3 eth-brownie eth-keys

# Load environment variables
export ETHEREUM_RPC_URL="https://rpc.polygonscan.com"  # or Infura, Alchemy, etc
export PRIVATE_KEY="your_private_key_here"
```

**Key Classes**:
- `BlockchainAgent`: Main orchestrator for blockchain operations
- `ContractManager`: Manages deployed contract instances
- `NFTMintRequest`: Request structure for minting NFTs
- `RewardDistribution`: Token reward distribution

**TODO Implementations**:
- [ ] Deploy MusicNFT.sol (ERC-721) contract
- [ ] Deploy DCMXToken.sol (ERC-20) contract
- [ ] Deploy GovernanceDAO.sol voting contract
- [ ] Deploy RewardDistributor.sol for token payouts
- [ ] Implement `mint_nft()` transaction building
- [ ] Implement `distribute_rewards()` transaction building

**Example**:
```python
from dcmx.blockchain.blockchain_agent import BlockchainAgent, NFTMintRequest

agent = BlockchainAgent(
    rpc_url="https://rpc.polygonscan.com",
    private_key=os.getenv("PRIVATE_KEY")
)

request = NFTMintRequest(
    track_hash="abc123...",
    artist_wallet="0x...",
    title="My Song",
    edition_number=1,
    max_editions=100,
    price_wei=1000000000000000000  # 1 ETH in wei
)

tx_hash = await agent.mint_nft(request)
```

---

### Agent 2: Audio Agent

**Focus**: Implement audio watermarking and perceptual fingerprinting

**Setup**:
```bash
# Install dependencies
pip install librosa pydub soundfile essentia
pip install cryptography

# Optional: Install ffmpeg for audio format conversion
sudo apt-get install ffmpeg
```

**Key Classes**:
- `AudioWatermark`: Embed and verify watermarks
- `AudioFingerprint`: Generate perceptual hashes
- `ProtectedTrack`: Track with watermark + fingerprint metadata

**TODO Implementations**:
- [ ] Implement FFT-based watermark embedding (ISO/IEC 18040)
- [ ] Implement watermark extraction and verification
- [ ] Implement MFCC-based fingerprinting (like Shazam)
- [ ] Implement fuzzy matching for duplicate detection
- [ ] Test watermark survival through MP3 compression
- [ ] Test format conversion robustness

**Example**:
```python
from dcmx.audio.audio_watermark import AudioWatermark
from dcmx.audio.audio_fingerprint import AudioFingerprint

# Watermark audio
audio_bytes = open("song.mp3", "rb").read()
watermarked = await AudioWatermark.embed(
    audio_bytes,
    rights_holder="Artist Name",
    nft_contract_address="0x...",
    edition_number=1
)

# Generate fingerprint
fingerprint = await AudioFingerprint.generate(watermarked)

# Detect duplicates
existing = ["fp1", "fp2", "fp3"]
match = await AudioFingerprint.detect_duplicate(fingerprint, existing)
```

---

### Agent 3: Compliance Agent

**Focus**: KYC/AML compliance and regulatory tracking

**Setup**:
```bash
# Install dependencies
pip install sqlalchemy cryptography fernet
pip install twilio  # for SMS verification
pip install stripe  # for KYC provider

# Set up encrypted database
export DATABASE_URL="postgresql://user:pass@localhost/dcmx_compliance"
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

**Key Classes**:
- `KYCVerifier`: Customer identity verification
- `OFACChecker`: Sanctions list compliance
- `TransactionMonitor`: Real-time AML monitoring
- `ComplianceDatabase`: Encrypted storage

**TODO Implementations**:
- [ ] Integrate with KYC provider (Stripe Identity, Onfido)
- [ ] Download and parse OFAC SDN list (weekly)
- [ ] Implement transaction monitoring rules ($10K threshold, structuring detection)
- [ ] Implement FinCEN SAR report generation
- [ ] Create encrypted storage schema
- [ ] Implement 7-year audit trail

**Example**:
```python
from dcmx.compliance.kyc_verifier import KYCVerifier
from dcmx.compliance.ofac_checker import OFACChecker

# Verify user identity
kyc = KYCVerifier()
result = await kyc.verify_user(
    user_id="user123",
    wallet_address="0x...",
    legal_name="John Doe",
    date_of_birth="1990-01-15",
    address="123 Main St, USA"
)

# Check OFAC
ofac = OFACChecker()
await ofac.load_sdn_list()
is_blocked = await ofac.check_address("0x...")
```

---

### Agent 4: LoRa Agent

**Focus**: Mesh network infrastructure and bandwidth rewards

**Setup**:
```bash
# Install dependencies
pip install pylorawan meshtastic aiohttp

# Hardware: LoRa modem (e.g., RasPi with LoRa HAT)
# Device path: /dev/ttyUSB0
```

**Key Classes**:
- `LoRaNode`: Extended Node with LoRa capabilities
- `BandwidthStats`: Per-node bandwidth tracking
- `RewardCalculator`: Calculate token rewards
- `MeshRouter`: Geographic routing

**TODO Implementations**:
- [ ] Implement LoRa packet transmission/reception
- [ ] Implement geographic mesh routing (AODV-based)
- [ ] Implement bandwidth accounting and statistics
- [ ] Implement reward calculation algorithm
- [ ] Add geolocation tracking (latitude/longitude)
- [ ] Implement rate limiting and spam protection

**Example**:
```python
from dcmx.lora.lora_node import LoRaNode, BandwidthStats

node = LoRaNode(
    host="127.0.0.1",
    port=8080,
    lora_device="/dev/ttyUSB0",
    latitude=37.7749,  # San Francisco
    longitude=-122.4194
)

# Broadcast availability
await node.broadcast_content("track_hash_abc123")

# Calculate rewards
reward = await node.calculate_bandwidth_reward()
print(f"Earned: {reward} tokens")
```

---

## 🔗 Integration Points

### Blockchain ↔ Audio
- Audio Agent generates `perceptual_fingerprint` and `watermark_hash`
- Blockchain Agent stores fingerprint + hash in NFT metadata
- Track is immutable once minted

### Blockchain ↔ Compliance
- Compliance Agent verifies user KYC before allowing transactions
- Blockchain Agent checks compliance approval before minting/distributing
- All transactions logged in immutable audit trail

### Blockchain ↔ LoRa
- LoRa Agent measures bandwidth and uptime
- Compliance Agent validates measurements
- Blockchain Agent distributes rewards based on verified metrics
- Tokens are non-transferable until lock-up expires

### Compliance ↔ All
- Every transaction routed through Compliance Agent first
- OFAC checks before wallet interaction
- KYC level determines transaction limits
- All actions logged for regulatory audit

---

## 📦 Shared State & Coordination

Agents coordinate through the `MultiAgentOrchestrator`:

```python
from dcmx.agents.orchestrator import MultiAgentOrchestrator, AgentType

orchestrator = MultiAgentOrchestrator()

# Register agents
await orchestrator.register_agent(AgentType.BLOCKCHAIN, blockchain_agent)
await orchestrator.register_agent(AgentType.AUDIO, audio_agent)
await orchestrator.register_agent(AgentType.COMPLIANCE, compliance_agent)
await orchestrator.register_agent(AgentType.LORA, lora_agent)

# Share state between agents
orchestrator.set_shared_state("nft_contract_address", "0x...")
orchestrator.set_shared_state("token_contract_address", "0x...")

# Execute coordinated task
result = await orchestrator.coordinate_agents()
```

---

## 🛡️ Compliance Checklist

Before each agent completes a feature:

### Blockchain Agent
- ☐ Smart contracts audited by third-party firm
- ☐ Token supply fixed and immutable
- ☐ Voting is advisory-only (not binding)
- ☐ Reward structure tied to actual work (not speculation)
- ☐ 2-of-3 multisig controls admin functions

### Audio Agent
- ☐ Watermark is irremovable (DMCA § 1201)
- ☐ Fingerprinting doesn't prevent playback
- ☐ Tested against MP3 compression
- ☐ Tested against format conversion
- ☐ Audit log of all watermark operations

### Compliance Agent
- ☐ KYC data encrypted at rest (AES-256)
- ☐ Separate storage from transaction data
- ☐ OFAC list updated weekly (automated)
- ☐ FinCEN SAR filed within 30 days
- ☐ 7-year audit trail immutable

### LoRa Agent
- ☐ P2P traffic encrypted (TLS 1.3+)
- ☐ No unencrypted wallet addresses on LoRa
- ☐ Bandwidth accounting auditable
- ☐ Rate limiting prevents spam
- ☐ Geographic routing respects data residency

---

## 📊 Development Timeline

**Week 1-2: Foundation**
- Blockchain Agent: Deploy testnet contracts
- Audio Agent: Implement watermarking prototype
- Compliance Agent: Set up KYC and OFAC infrastructure
- LoRa Agent: Mesh protocol design

**Week 3-4: Integration**
- All agents: Connect data flows
- Blockchain Agent: Link rewards to LoRa metrics
- Compliance Agent: Gate all transactions
- Audio Agent: Embed NFT metadata in watermarks

**Week 5: Testing & Audit**
- Security audit of smart contracts
- Watermark compression testing
- Compliance testing (KYC/OFAC flows)
- LoRa network stress testing

**Week 6: Deployment**
- Testnet → Mainnet migration
- Monitoring & alerting setup
- Bandwidth reward distribution begins

---

## 🔧 Troubleshooting

### Blockchain Agent
- Gas estimation too low? Increase by 20%
- Transaction reverted? Check contract state with `eth_call`
- Nonce issues? Reset with `web3.eth.get_transaction_count(account)`

### Audio Agent
- Watermark survives compression? Use low-frequency band (<5kHz)
- Fingerprint collisions? Increase bit depth or use constellation maps

### Compliance Agent
- KYC provider timeout? Implement exponential backoff + retry
- OFAC list too large? Use bloom filter for O(1) lookup

### LoRa Agent
- Packet loss on mesh? Implement forward error correction (FEC)
- Reward calculation drift? Use blockchain timestamp as canonical time source

---

## 📚 References

- **Solidity**: https://docs.soliditylang.org/
- **Web3.py**: https://web3py.readthedocs.io/
- **librosa**: https://librosa.org/
- **ISO/IEC 18040**: Audio watermarking standard
- **FinCEN SAR**: https://www.fincen.gov/suspicious-activity-report
- **LoRaWAN**: https://lora-alliance.org/

---

## 👥 Agent Handoff Protocol

When handing off work from one agent to another:

1. **Blockchain → Audio**: Provide NFT contract address and metadata schema
2. **Audio → Blockchain**: Deliver watermarked audio hash and fingerprint
3. **Blockchain → Compliance**: Request transaction approval with wallet address
4. **Compliance → Blockchain**: Return KYC level and OFAC clearance
5. **Compliance → LoRa**: Request bandwidth statistics for reward calculation
6. **LoRa → Blockchain**: Submit bandwidth proofs for reward verification

---

## Questions?

Each agent should refer to `.github/copilot-instructions.md` for project-wide conventions and patterns.

For agent-specific questions, see the `TODO` comments in each implementation file.
