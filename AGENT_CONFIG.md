# DCMX Agent Configuration Examples

This file contains example configurations and environment setup for each agent.

---

## Blockchain Agent Configuration

### Environment Variables

```bash
# Polygon RPC endpoint (recommended for low gas costs)
export ETHEREUM_RPC_URL="https://polygon-rpc.com"
# or Infura: "https://polygon-mainnet.infura.io/v3/YOUR_INFURA_KEY"
# or Alchemy: "https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY"

# Private key for transaction signing (keep secure!)
export PRIVATE_KEY="0x..."

# Contract deployment addresses (after deployment)
export MUSIC_NFT_ADDRESS="0x..."
export DCMX_TOKEN_ADDRESS="0x..."
export GOVERNANCE_DAO_ADDRESS="0x..."
export REWARD_DISTRIBUTOR_ADDRESS="0x..."
```

### Initialize Blockchain Agent

```python
import os
from dcmx.blockchain.blockchain_agent import BlockchainAgent

agent = BlockchainAgent(
    rpc_url=os.getenv("ETHEREUM_RPC_URL"),
    private_key=os.getenv("PRIVATE_KEY"),
    contract_addresses={
        "music_nft": os.getenv("MUSIC_NFT_ADDRESS"),
        "dcmx_token": os.getenv("DCMX_TOKEN_ADDRESS"),
        "governance": os.getenv("GOVERNANCE_DAO_ADDRESS"),
        "rewards": os.getenv("REWARD_DISTRIBUTOR_ADDRESS"),
    }
)

# Verify connection
print(f"Connected to chain ID: {agent.w3.eth.chain_id}")
print(f"Account: {agent.account.address}")
```

### Deploy Contracts (Hardhat/Brownie)

```bash
# Using Hardhat
npx hardhat compile
npx hardhat run scripts/deploy.js --network polygon-testnet

# Using Brownie
brownie compile
brownie run scripts/deploy.py --network polygon-testnet
```

### Example: Mint NFT

```python
from dcmx.blockchain.blockchain_agent import NFTMintRequest

request = NFTMintRequest(
    track_hash="qmXabc123...bafybeiczsscw",  # IPFS hash
    artist_wallet="0x1234567890abcdef1234567890abcdef12345678",
    title="My Song",
    edition_number=1,
    max_editions=100,
    price_wei=1000000000000000000  # 1 MATIC (or ETH on mainnet)
)

tx_hash = await agent.mint_nft(request)
print(f"NFT minted: {tx_hash}")

# Check status
status = await agent.contract_manager.get_transaction_status(tx_hash)
print(f"Status: {status}")
```

---

## Audio Agent Configuration

### Environment Variables

```bash
# FFmpeg for audio format conversion
export FFMPEG_PATH="/usr/bin/ffmpeg"

# Watermarking parameters
export WATERMARK_STRENGTH="0.05"  # 5% amplitude modulation
export WATERMARK_FREQUENCY_BAND="low"  # low, mid, or high

# Fingerprinting parameters
export FINGERPRINT_BIT_DEPTH="256"
export FINGERPRINT_SAMPLE_RATE="22050"  # Hz
```

### Initialize Audio Agent

```python
from dcmx.audio.audio_watermark import AudioWatermark
from dcmx.audio.audio_fingerprint import AudioFingerprint

# Process audio file
audio_file = "my_song.mp3"
with open(audio_file, "rb") as f:
    audio_bytes = f.read()

# Add watermark
watermarked = await AudioWatermark.embed(
    audio_bytes,
    rights_holder="Artist Name",
    nft_contract_address="0x...",
    edition_number=1,
    max_editions=100
)

# Generate fingerprint
fingerprint = await AudioFingerprint.generate(watermarked)
print(f"Fingerprint: {fingerprint}")

# Save watermarked audio
with open("my_song_watermarked.mp3", "wb") as f:
    f.write(watermarked)
```

### Verify Watermark

```python
# Load watermarked audio
with open("my_song_watermarked.mp3", "rb") as f:
    watermarked_audio = f.read()

# Verify watermark
is_valid = await AudioWatermark.verify(watermarked_audio, "Artist Name")
print(f"Watermark valid: {is_valid}")
```

### Test Compression Robustness

```python
import subprocess

# Re-encode MP3 at different bitrate
subprocess.run([
    "ffmpeg", "-i", "my_song_watermarked.mp3",
    "-b:a", "128k",  # Lower bitrate
    "my_song_128k.mp3"
])

# Check if watermark survives
with open("my_song_128k.mp3", "rb") as f:
    compressed = f.read()

survives = await AudioWatermark.verify(compressed, "Artist Name")
print(f"Watermark survives 128k MP3: {survives}")
```

---

## Compliance Agent Configuration

### Environment Variables

```bash
# PostgreSQL database
export DATABASE_URL="postgresql://user:password@localhost:5432/dcmx_compliance"

# Encryption key for KYC data (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export ENCRYPTION_KEY="..."

# Third-party KYC provider
export KYC_PROVIDER="stripe"  # or "onfido"
export STRIPE_API_KEY="sk_test_..."
export STRIPE_CLIENT_ID="ca_..."

# OFAC checking
export OFAC_CHECK_ENABLED="true"
export OFAC_UPDATE_INTERVAL_DAYS="7"

# Transaction monitoring
export AML_MONITOR_ENABLED="true"
export KYC_THRESHOLD_USD="10000"
export DAILY_LIMIT_USD="100000"
```

### Initialize Compliance Agent

```python
import os
from dcmx.compliance.kyc_verifier import KYCVerifier
from dcmx.compliance.ofac_checker import OFACChecker

# KYC Verification
kyc = KYCVerifier(kyc_provider_url=os.getenv("STRIPE_API_KEY"))

# Verify user
result = await kyc.verify_user(
    user_id="user_12345",
    wallet_address="0x...",
    legal_name="John Doe",
    date_of_birth="1990-01-15",
    address="123 Main St, Anytown, USA",
    country="US"
)
print(f"KYC Result: {result}")

# OFAC Checking
ofac = OFACChecker()
await ofac.load_sdn_list()  # Download latest SDN list

is_blocked = await ofac.check_address("0x...")
print(f"Address blocked: {is_blocked}")
```

### Transaction Validation

```python
from dcmx.compliance.ofac_checker import OFACChecker
from dcmx.compliance.kyc_verifier import KYCVerifier

async def validate_transaction(user_id, amount_usd, from_wallet, to_wallet):
    """Validate transaction against compliance rules."""
    
    # Check OFAC
    ofac = OFACChecker()
    if await ofac.check_address(from_wallet) or await ofac.check_address(to_wallet):
        return {"approved": False, "reason": "OFAC sanctions"}
    
    # Check KYC level
    kyc = KYCVerifier()
    level = await kyc.get_verification_level(user_id)
    if level == 0 and amount_usd > 10_000:
        return {"approved": False, "reason": "KYC required"}
    
    # Check AML rules
    if amount_usd > 10_000:
        # File FinCEN SAR
        return {"approved": True, "requires_sar": True}
    
    return {"approved": True, "requires_sar": False}

result = await validate_transaction(
    user_id="user_123",
    amount_usd=15_000,
    from_wallet="0x...",
    to_wallet="0x..."
)
print(f"Transaction: {result}")
```

---

## LoRa Agent Configuration

### Environment Variables

```bash
# LoRa hardware device
export LORA_DEVICE="/dev/ttyUSB0"
export LORA_BAUD_RATE="115200"

# Node location (for geographic routing)
export NODE_LATITUDE="37.7749"
export NODE_LONGITUDE="-122.4194"

# Network parameters
export BANDWIDTH_LIMIT_MBPS="5.0"
export MESH_UPDATE_INTERVAL_SECONDS="300"  # 5 minutes

# Reward parameters
export MIN_REWARD_TOKENS="10"
export BANDWIDTH_REWARD_PER_100MB="1"
export UPTIME_BONUS_PERCENT="20"
export COVERAGE_BONUS_PERCENT="10"
```

### Initialize LoRa Node

```python
import os
from dcmx.lora.lora_node import LoRaNode

node = LoRaNode(
    host="0.0.0.0",
    port=8080,
    lora_device=os.getenv("LORA_DEVICE"),
    bandwidth_limit_mbps=float(os.getenv("BANDWIDTH_LIMIT_MBPS")),
    latitude=float(os.getenv("NODE_LATITUDE")),
    longitude=float(os.getenv("NODE_LONGITUDE"))
)

# Start node
await node.start()
print(f"Node started: {node.peer.address}")
```

### Broadcast Content

```python
# Node announces track availability to mesh neighbors
await node.broadcast_content("qmXabc123...bafybeiczsscw")
```

### Calculate Rewards

```python
# Simulate bandwidth stats
node.bandwidth_stats.bytes_uploaded = 500_000_000  # 500 MB
node.bandwidth_stats.uptime_seconds = 24 * 3600  # 24 hours
node.bandwidth_stats.unique_peers_served = 15

# Calculate reward
reward = await node.calculate_bandwidth_reward()
print(f"Earned: {reward} tokens")
```

### Monitor Network

```python
import asyncio

async def monitor_rewards():
    """Periodically calculate and report rewards."""
    while True:
        reward = await node.calculate_bandwidth_reward()
        print(f"Reward: {reward} tokens at {datetime.now()}")
        
        # Submit reward to blockchain
        # await blockchain_agent.distribute_rewards(...)
        
        await asyncio.sleep(3600)  # Every hour

# Run monitoring
asyncio.run(monitor_rewards())
```

---

## Multi-Agent Orchestration Example

```python
from dcmx.agents.orchestrator import MultiAgentOrchestrator, AgentType
from dcmx.blockchain.blockchain_agent import BlockchainAgent
from dcmx.audio.audio_watermark import AudioWatermark
from dcmx.compliance.kyc_verifier import KYCVerifier
from dcmx.lora.lora_node import LoRaNode
import os

# Initialize orchestrator
orchestrator = MultiAgentOrchestrator()

# Initialize agents
blockchain = BlockchainAgent(
    rpc_url=os.getenv("ETHEREUM_RPC_URL"),
    private_key=os.getenv("PRIVATE_KEY")
)

audio = AudioWatermark()  # or load from module
kyc = KYCVerifier()
lora = LoRaNode(
    lora_device=os.getenv("LORA_DEVICE"),
    latitude=float(os.getenv("NODE_LATITUDE")),
    longitude=float(os.getenv("NODE_LONGITUDE"))
)

# Register agents
await orchestrator.register_agent(AgentType.BLOCKCHAIN, blockchain)
await orchestrator.register_agent(AgentType.AUDIO, audio)
await orchestrator.register_agent(AgentType.COMPLIANCE, kyc)
await orchestrator.register_agent(AgentType.LORA, lora)

# Coordinate multi-agent workflow
result = await orchestrator.coordinate_agents()
print(f"Orchestration result: {result}")
```

---

## Typical Workflow

### Minting a Limited Edition Music NFT

```python
# 1. AUDIO AGENT: Process and watermark audio
audio_bytes = open("song.mp3", "rb").read()
watermarked = await audio_agent.embed(audio_bytes, "Artist")
fingerprint = await audio_agent.generate_fingerprint(watermarked)

# 2. COMPLIANCE AGENT: Verify artist KYC
kyc_result = await compliance_agent.verify_user(
    user_id="artist_123",
    wallet_address="0x...",
    legal_name="Artist Name",
    ...
)

# 3. BLOCKCHAIN AGENT: Mint NFT
nft_request = NFTMintRequest(
    track_hash=compute_hash(watermarked),
    artist_wallet="0x...",
    title="Song Title",
    edition_number=1,
    max_editions=100,
    price_wei=1000000000000000000
)
tx_hash = await blockchain_agent.mint_nft(nft_request)

# 4. BLOCKCHAIN AGENT: Verify transaction
status = await blockchain_agent.get_transaction_status(tx_hash)
print(f"NFT minted: {status}")
```

### Distributing Network Participation Rewards

```python
# 1. LORA AGENT: Measure bandwidth
reward_amount = await lora_node.calculate_bandwidth_reward()

# 2. COMPLIANCE AGENT: Verify reward eligibility
can_reward = await compliance_agent.validate_transaction(
    user_id="node_456",
    amount_usd=reward_amount * token_price,
    from_wallet="0x...",  # Reward distributor
    to_wallet="0x..."     # Node operator
)

# 3. BLOCKCHAIN AGENT: Distribute tokens
if can_reward["approved"]:
    distribution = RewardDistribution(
        node_id="node_456",
        wallet_address="0x...",
        amount=reward_amount,
        reward_type="energy",
        proof=lora_bandwidth_proof
    )
    tx_hash = await blockchain_agent.distribute_rewards(distribution)
    print(f"Reward distributed: {tx_hash}")
```

---

## Troubleshooting

### "Could not connect to RPC endpoint"
```python
# Check RPC endpoint is working
import requests
response = requests.post(
    "https://polygon-rpc.com",
    json={"jsonrpc": "2.0", "method": "eth_chainId", "params": [], "id": 1}
)
print(response.json())  # Should return {"result": "0x89", ...}
```

### "Insufficient gas"
```python
# Increase gas limit by 20%
current_gas = await contract_manager.get_gas_estimate(transaction)
transaction['gas'] = int(current_gas * 1.2)
```

### "KYC provider timeout"
```python
# Implement exponential backoff
import asyncio
backoff = 1
for attempt in range(3):
    try:
        result = await kyc_provider.verify(data)
        return result
    except TimeoutError:
        await asyncio.sleep(backoff)
        backoff *= 2
```

### "OFAC list not found"
```bash
# Manually download SDN list
wget https://home.treasury.gov/policy-issues/financial-sanctions/sdn-list
# Then parse and index for fast lookups
```

---

**This configuration file should be kept updated as agents develop their implementations.**
