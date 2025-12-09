# DCMX Royalty and Rewards Payment Structure

**Complete system for NFT sales, certificate issuance, and reward distribution**

---

## 📋 Overview

The DCMX royalty and rewards system manages:

1. **NFT Certificate Issuance** - Each purchase gets a numbered certificate (Edition 1 of 100, etc.)
2. **Sharing Rewards** - Users earn tokens when they share songs with other wallets
3. **Listening Rewards** - Users earn tokens when they listen to shared songs
4. **Bandwidth Rewards** - LoRa node operators earn tokens for serving content
5. **Royalty Distribution** - Split payments after NFT sales
6. **Secondary Market Enforcement** - Artist receives % of all resales (ERC-2981)

---

## 🎫 NFT Certificate System

### What is an NFT Certificate?

When a user purchases an edition of your song, they receive:
- **Unique Certificate**: Edition #5 of 100 copies
- **Blockchain Proof**: ERC-721 NFT token linking to watermarked audio
- **Ownership Verification**: Proves they purchased legally
- **Secondary Market Rights**: Can resell with automatic artist royalties

### Example Certificate Metadata

```
Song: "My Music" by Artist
Edition: 5 of 100
Purchase Price: $50 USD
Date: 2025-12-09
Certificate ID: cert_abc123_5_1733739600
NFT Contract: 0x1234...
Token ID: 5
Blockchain: Polygon
```

### Creating a Certificate

```python
from dcmx.royalties import RoyaltyPaymentStructure

royalty = RoyaltyPaymentStructure()

# Issue certificate when user purchases
certificate = royalty.issue_nft_certificate(
    song_title="My Song",
    artist="Your Name",
    content_hash="abc123...",  # SHA256 of audio
    edition_number=1,           # This is edition #1
    max_editions=100,           # Total copies available
    buyer_wallet="0xUserWallet",
    purchase_price_usd=50.0,
    purchase_price_tokens=500,  # At current token price
    watermark_hash="...",       # Proof audio is watermarked
    perceptual_fingerprint="...", # Content ID for duplicate detection
    nft_contract_address="0xNFTContract",
    token_id=1,
    blockchain="polygon"
)

print(f"Certificate issued: {certificate.certificate_id}")
print(f"Owner: {certificate.owner_wallet}")
print(f"Edition: {certificate.edition_number}/{certificate.max_editions}")
```

### Listing User Certificates

```python
# User can see all their purchased certificates
user_certs = royalty.list_user_certificates("0xUserWallet")
for cert in user_certs:
    print(f"  {cert.song_title} - Edition {cert.edition_number}")
```

---

## 🎁 Reward Types & Earning

### 1. Sharing Rewards

**What**: User shares your song with another wallet and earns tokens.

```python
# Record sharing event
share_reward = royalty.record_sharing_event(
    sharer_wallet="0xAlice",
    song_content_hash="abc123...",
    shared_with_wallet="0xBob",
    base_reward=1  # 1 token per share
)

# Tokens earned: 1 token
# If Bob listens: Gets 1.5x bonus = 1.5 tokens
```

**Token Multipliers**:
- Base: 1 token per share
- If recipient listens: 1.5x bonus
- If recipient purchases NFT: Additional bonus

**Example Flow**:
1. Alice shares song with Bob (Alice gets 1 token)
2. Bob listens to the song (Alice gets 1.5x = 1.5 tokens, Bob gets 2 tokens)
3. Bob purchases the NFT (Alice gets additional bonus)

### 2. Listening Rewards

**What**: User listens to a shared song and earns tokens.

```python
# Record listening event
listen_reward = royalty.record_listening_event(
    listener_wallet="0xBob",
    song_content_hash="abc123...",
    sharer_wallet="0xAlice",
    listen_duration_seconds=240,       # Listened for 4 minutes
    completion_percentage=95.0,        # Listened to 95% of song
    base_reward=2  # 2 tokens per complete listen
)

# Tokens earned:
# - Base: 2 tokens
# - 95% completion: +2 bonus tokens
# - Total: 4 tokens
```

**Completion Bonuses**:
- 90%+ completion: +2 tokens
- 75%+ completion: +1 token
- 50%+ completion: +0.5 tokens
- <50% completion: No bonus

**Example Breakdown**:
```
Alice shares song with Bob
Bob listens:
  - Full listen (95%): 2 + 2 = 4 tokens for Bob
  - Alice (sharer) gets: 1 × 1.5 = 1.5 tokens referral bonus
```

### 3. Bandwidth Rewards

**What**: LoRa node operators earn tokens for serving content to listeners.

```python
# Record bandwidth serving by LoRa node
bandwidth_reward = royalty.record_bandwidth_serving(
    node_id="node_xyz",
    song_content_hash="abc123...",
    bytes_served=100_000_000,          # 100 MB served
    listeners_served=50,                # Reached 50 unique listeners
    transmission_time_seconds=3600,     # Served for 1 hour
    base_reward=5  # 5 tokens base
)

# Tokens earned:
# - Base: 5 tokens
# - Bandwidth bonus: (100MB / 100MB) × 1 = 1 token
# - Listener bonus: 50 listeners × 0.5 = 25 tokens
# - Total: 5 + 1 + 25 = 31 tokens
```

**Bandwidth Calculation**:
- Base: 5 tokens
- Per 100MB served: +1 token
- Per unique listener: +0.5 tokens

---

## 💰 Royalty Distribution

### Primary Sale (First Purchase)

When user buys Edition #1 of your song for $50:

| Recipient | Percentage | Amount | Purpose |
|-----------|-----------|--------|---------|
| **You (Artist)** | 70% | $35.00 | Your earnings |
| **Platform** | 15% | $7.50 | DCMX operational costs |
| **Node Operators** | 10% | $5.00 | Rewards pool for network |
| **Early Buyer Bonus** | 5% | $2.50 | Reserved for future features |

**Total**: $50.00

```python
# Process primary sale
payment = royalty.process_primary_sale(
    song_title="My Song",
    artist="Your Name",
    content_hash="abc123...",
    purchase_price_usd=50.0,
    purchase_price_tokens=500,
    nft_contract_address="0x...",
    token_id=1,
    blockchain="polygon"
)

print(f"Artist payout: ${payment.artist_payout_usd}")  # $35.00
print(f"Platform payout: ${payment.platform_payout_usd}")  # $7.50
print(f"Node operator pool: ${payment.node_operator_payout_usd}")  # $5.00
```

### Secondary Sale (Resale)

When user resells Edition #1 on secondary market for $100:

| Recipient | Percentage | Amount | Purpose |
|-----------|-----------|--------|---------|
| **You (Artist)** | 70% | $70.00 | Ongoing royalties |
| **Node Operators** | 20% | $20.00 | Incentivize distribution |
| **Platform** | 10% | $10.00 | Marketplace fees |

**Total**: $100.00

**Key Insight**: You earn royalties on EVERY resale!

```python
# Process secondary sale
payment = royalty.process_secondary_sale(
    song_title="My Song",
    artist="Your Name",
    content_hash="abc123...",
    token_id=1,
    seller_wallet="0xAlice",
    buyer_wallet="0xBob",
    sale_price_usd=100.0,
    nft_contract_address="0x..."
)

print(f"Artist royalty: ${payment.artist_payout_usd}")  # $70.00
print(f"Seller (Alice) receives: ${100.0 - payment.artist_payout_usd - 10.0}")  # $20.00
```

### Royalty Reports

```python
# Get your total royalties
artist_royalties = royalty.get_artist_royalties("Your Name")
print(f"Total earnings: ${artist_royalties:.2f}")

# Detailed breakdown
report = royalty.generate_royalty_report("Your Name")
print(f"Primary sales: {report['primary_sales']['count']} songs")
print(f"Secondary sales: {report['secondary_sales']['count']} resales")
print(f"Total royalties: ${report['total_royalties_usd']:.2f}")
```

---

## 🏆 Reward Claims & Verification

### Claim Flow

1. **User Accumulates Rewards**
   - Shares songs → Sharing rewards
   - Listens to shared songs → Listening rewards
   - LoRa node serves content → Bandwidth rewards

2. **User Submits Claim with ZK Proof**
   - Claim includes proof of activity
   - Zero-knowledge proof validates without revealing details

3. **Verifier Nodes Approve (Quorum)**
   - 4 independent verifier nodes check the claim
   - Requires 3-of-4 approval
   - ZK proof must be valid from 2+ verifiers

4. **Tokens Minted on Blockchain**
   - Once approved, smart contract mints tokens
   - Tokens transferred to user's wallet

### Creating a Reward Claim

```python
from dcmx.royalties import RewardType, RewardClaim

# Create claim for accumulated sharing rewards
claim = royalty.create_reward_claim(
    claimant_wallet="0xAlice",
    claim_type=RewardType.SHARING,
    song_content_hash="abc123...",
    total_tokens_claimed=15.5,  # 15.5 tokens from sharing
    activity_count=10  # From 10 share events
)

print(f"Claim created: {claim.claim_id}")
print(f"Tokens claimed: {claim.total_tokens_claimed}")
print(f"Status: Pending verification")
```

### Verifier Node Approval

```python
from dcmx.royalties import RewardClaimVerifier, VerifierNodeStatus

verifier = RewardClaimVerifier(royalty)

# Register 4 verifier nodes
verifier.register_verifier_node("verifier_1")
verifier.register_verifier_node("verifier_2")
verifier.register_verifier_node("verifier_3")
verifier.register_verifier_node("verifier_4")

# Distribute claim to all verifiers
verifiers = verifier.distribute_claim_to_verifiers(claim.claim_id)

# Each verifier checks and submits approval
for verifier_id in ["verifier_1", "verifier_2", "verifier_3"]:
    verifier.submit_verifier_approval(
        verifier_node_id=verifier_id,
        claim_id=claim.claim_id,
        status=VerifierNodeStatus.APPROVED,
        zk_proof_result=True,  # ZK proof is valid
        notes="Verified sharing rewards"
    )

# Check status
status = verifier.get_claim_verification_status(claim.claim_id)
print(f"Status: {status['status']}")  # APPROVED (3 approvals)
print(f"Tokens verified: {royalty.reward_claims[claim.claim_id].total_tokens_verified}")
```

### Minting Tokens

```python
# Once claim is approved by verifier quorum
claim = royalty.reward_claims[claim.claim_id]

# Call blockchain to mint tokens
royalty.approve_and_mint_tokens(
    claim_id=claim.claim_id,
    blockchain_tx_hash="0x1234567890abcdef..."
)

print(f"Tokens minted: {claim.total_tokens_verified} DCMX")
print(f"Transaction: {claim.mint_transaction_hash}")
```

---

## 🔗 Blockchain Integration

### Smart Contracts Used

| Contract | Standard | Purpose |
|----------|----------|---------|
| **MusicNFT.sol** | ERC-721 | Mint NFT certificates for purchased songs |
| **DCMXToken.sol** | ERC-20 | Mint reward tokens for sharing/listening |
| **RoyaltyDistributor.sol** | ERC-2981 | Distribute royalties on primary & secondary sales |
| **GovernanceDAO.sol** | Custom | Optional: DAO voting with DCMXToken |

### Complete NFT Purchase Flow

```python
from dcmx.royalties import (
    RoyaltyPaymentStructure,
    RewardClaimVerifier,
    BlockchainIntegration,
    RewardDistributionEngine
)

# Initialize all systems
royalty = RoyaltyPaymentStructure()
verifier = RewardClaimVerifier(royalty)
blockchain = BlockchainIntegration(
    rpc_url="https://rpc.polygon.com",
    private_key="your_private_key",
    nft_contract_address="0xNFTContract",
    token_contract_address="0xTokenContract",
    royalty_distributor_address="0xDistributor"
)
engine = RewardDistributionEngine(royalty, verifier, blockchain)

# Process complete NFT sale
nft_tx, token_id = await engine.process_nft_sale(
    song_title="My Song",
    artist="Your Name",
    content_hash="abc123...",
    edition_number=1,
    max_editions=100,
    buyer_wallet="0xBuyerWallet",
    purchase_price_usd=50.0,
    purchase_price_tokens=500,
    watermark_hash="watermark_abc123",
    perceptual_fingerprint="fingerprint_abc123"
)

# Result:
# 1. NFT minted on blockchain (ERC-721)
# 2. Certificate issued and stored
# 3. Royalties calculated and distributed
# 4. ERC-2981 enforcement set up for secondary sales
# 5. User receives NFT in wallet

print(f"NFT minted: {nft_tx}")
print(f"Token ID: {token_id}")
```

---

## 📊 Reporting & Analytics

### User Reward Report

```python
report = royalty.generate_user_reward_report("0xAlice")

print(f"User: {report['wallet']}")
print(f"Sharing rewards: {report['sharing_rewards']['total_tokens']} tokens from {report['sharing_rewards']['events']} shares")
print(f"Listening rewards: {report['listening_rewards']['total_tokens']} tokens from {report['listening_rewards']['events']} listens")
print(f"Total earned: {report['total_earned']} tokens")
print(f"Claimed tokens: {report['claimed_tokens']} tokens")
print(f"Pending claims: {report['pending_claims']}")
print(f"NFT certificates owned: {report['nft_certificates']}")
```

**Output Example**:
```
User: 0xAlice123...
Sharing rewards: 15.5 tokens from 10 shares
Listening rewards: 28.0 tokens from 14 listens
Total earned: 43.5 tokens
Claimed tokens: 20.0 tokens
Pending claims: 2
NFT certificates owned: 3
```

### Artist Royalty Report

```python
report = royalty.generate_royalty_report("Your Name")

print(f"Artist: {report['artist']}")
print(f"Total royalties: ${report['total_royalties_usd']:.2f}")
print(f"Primary sales: {report['primary_sales']['count']} at ${report['primary_sales']['avg_payout']:.2f} avg")
print(f"Secondary sales: {report['secondary_sales']['count']} at ${report['secondary_sales']['avg_payout']:.2f} avg")
print(f"NFTs issued: {report['nfts_issued']}")
```

### Platform Statistics

```python
stats = royalty.generate_platform_statistics()

print(f"Total revenue: ${stats['total_revenue_usd']:.2f}")
print(f"Platform earnings: ${stats['platform_earnings_usd']:.2f}")
print(f"Node operator pool: ${stats['node_operator_pool_usd']:.2f}")
print(f"NFTs issued: {stats['nfts_issued']}")
print(f"Reward claims approved: {stats['reward_claims_approved']}")
print(f"Total tokens distributed: {stats['total_tokens_distributed']}")
print(f"Sharing events: {stats['sharing_events']}")
print(f"Listening events: {stats['listening_events']}")
```

---

## 🔐 Security & Compliance

### Zero-Knowledge Proofs

- **No revealing private data**: ZK proofs verify claims without showing details
- **Verifiable by others**: Anyone can check proof is valid
- **Non-interactive**: Single proof, no back-and-forth
- **Prevents fraud**: Impossible to fake proof

### Verifier Quorum

- **3-of-4 Required**: Need approval from 3 independent verifiers
- **Decentralized**: No single point of trust
- **Transparent**: All approvals logged and auditable
- **Cryptographic Signatures**: Each verifier signs approval

### Smart Contract Safeguards

- **ERC-2981**: Automatic royalty enforcement on secondary sales
- **Multi-signature Control**: Admin functions require 2-of-3 signatures
- **Immutable Logs**: All transactions logged on blockchain
- **No Inflation**: Token supply capped, no unlimited minting

---

## 📁 File Structure

```
dcmx/royalties/
├── __init__.py                 # Module exports
├── royalty_structure.py        # Core royalty & reward classes
└── reward_integration.py       # Blockchain & verifier integration
```

---

## 🚀 Quick Start Example

```python
from dcmx.royalties import (
    RoyaltyPaymentStructure,
    RewardClaimVerifier,
    BlockchainIntegration,
    RewardDistributionEngine,
    RewardType
)

# 1. Initialize systems
royalty = RoyaltyPaymentStructure()
verifier = RewardClaimVerifier(royalty)
blockchain = BlockchainIntegration(
    rpc_url="https://rpc.polygon.com",
    private_key="your_key",
    nft_contract_address="0x...",
    token_contract_address="0x...",
    royalty_distributor_address="0x..."
)
engine = RewardDistributionEngine(royalty, verifier, blockchain)

# 2. Issue NFT for song purchase
nft_tx, token_id = await engine.process_nft_sale(
    song_title="My Song",
    artist="You",
    content_hash="abc123",
    edition_number=1,
    max_editions=100,
    buyer_wallet="0xBuyer",
    purchase_price_usd=50.0,
    purchase_price_tokens=500,
    watermark_hash="...",
    perceptual_fingerprint="..."
)

# 3. Record sharing event
share = await engine.process_sharing_reward(
    sharer_wallet="0xAlice",
    song_content_hash="abc123",
    shared_with_wallet="0xBob"
)

# 4. Record listening event
listen = await engine.process_listening_reward(
    listener_wallet="0xBob",
    song_content_hash="abc123",
    sharer_wallet="0xAlice",
    listen_duration_seconds=240,
    completion_percentage=95.0
)

# 5. Submit reward claim with ZK proof
claim_id = await engine.submit_and_verify_claim(
    claimant_wallet="0xAlice",
    claim_type=RewardType.SHARING,
    song_content_hash="abc123",
    total_tokens_claimed=15.5,
    zk_proof_data={"proof": "..."}
)

# 6. Verify claim through verifier quorum
verifier.register_verifier_node("node_1")
verifier.register_verifier_node("node_2")
verifier.register_verifier_node("node_3")
verifier.register_verifier_node("node_4")

verifiers = verifier.distribute_claim_to_verifiers(claim_id)
for node_id in verifiers[:3]:  # First 3 approve
    verifier.submit_verifier_approval(
        verifier_node_id=node_id,
        claim_id=claim_id,
        status=VerifierNodeStatus.APPROVED,
        zk_proof_result=True
    )

# 7. Mint tokens once approved
tx_hash = await engine.finalize_approved_claim(claim_id)

print(f"Tokens minted! Transaction: {tx_hash}")
```

---

## 📚 Integration with Other Systems

### Integration with LoRa Network

Bandwidth rewards are earned when LoRa nodes serve content:

```python
# From lora_node.py - record bandwidth serving
bandwidth_reward = engine.process_bandwidth_reward(
    node_id="node_xyz",
    song_content_hash="abc123",
    bytes_served=100_000_000,
    listeners_served=50,
    transmission_time_seconds=3600
)

# LoRa node can claim these rewards
claim = royalty.create_reward_claim(
    claimant_wallet="0xNodeOperator",
    claim_type=RewardType.BANDWIDTH,
    song_content_hash="abc123",
    total_tokens_claimed=bandwidth_reward.total_reward
)
```

### Integration with Blockchain Contracts

See `dcmx/blockchain/` for smart contract implementations:
- `MusicNFT.sol` - ERC-721 contract for NFT certificates
- `DCMXToken.sol` - ERC-20 contract for reward tokens
- `RoyaltyDistributor.sol` - ERC-2981 for automatic royalty enforcement

---

## ⚖️ Compliance Notes

### Artist Rights Protection
- ✅ Permanent watermarking prevents unauthorized copying
- ✅ Content hashes prove ownership
- ✅ Locked royalties on secondary sales
- ✅ All transactions logged for tax compliance

### User Privacy
- ✅ Zero-knowledge proofs minimize data exposure
- ✅ Wallet addresses can remain pseudonymous
- ✅ Sharing/listening activities not publicly logged
- ✅ Personal data stored separately from transaction logs

### Financial Transparency
- ✅ All royalty splits configurable but transparent
- ✅ Real-time auditable transaction history
- ✅ Artist can generate comprehensive reports
- ✅ No hidden fees or surprise deductions

---

## 🔄 Token Economics

**DCMX Token Supply**: Fixed (no inflation)

**Token Uses**:
1. **Purchase NFTs**: Buy your music with DCMX tokens
2. **Governance**: Vote on platform decisions (advisory)
3. **Rewards**: Earned for sharing, listening, bandwidth
4. **Staking**: Lock tokens to run verifier node (coming soon)

**Token Rewards** (not tradeable immediately):
- Sharing: 1 token per share (1.5x if listened)
- Listening: 2 tokens + completion bonus
- Bandwidth: 5 tokens base + bonuses
- Lock-up: 90 days before tradeable (prevents pump-and-dump)

---

## 📞 Support & References

For issues or questions:
1. Check DCMX documentation in `.github/copilot-instructions.md`
2. Review code examples in this guide
3. Check royalty_structure.py docstrings for API details
