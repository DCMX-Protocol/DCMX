# DCMX Royalty & Rewards System - Configuration & Quick Reference

## 📌 System Overview

The DCMX Royalty and Rewards system handles:

| Component | Purpose | Key Classes |
|-----------|---------|------------|
| **NFT Certificates** | Issue unique ownership tokens for each song purchase | `NFTCertificate` |
| **Sharing Rewards** | Reward users for sharing songs (1 token + multipliers) | `SharingReward` |
| **Listening Rewards** | Reward users for listening (2 tokens + completion bonus) | `ListeningReward` |
| **Bandwidth Rewards** | Reward LoRa nodes for serving content | `BandwidthReward` |
| **Royalty Distribution** | Split payments among artist, platform, nodes | `RoyaltyPayment` |
| **Reward Claims** | Verify and approve rewards before token minting | `RewardClaim` |
| **Verifier Quorum** | 3-of-4 verifier nodes approve claims | `RewardClaimVerifier` |
| **Blockchain Integration** | Mint NFTs, tokens, enforce royalties | `BlockchainIntegration` |

---

## 🔧 Configuration Reference

### Reward Amounts (Configurable)

```python
# SHARING REWARDS
SHARING_BASE_REWARD = 1  # tokens per share
SHARING_LISTENING_MULTIPLIER = 1.5  # if recipient listens
SHARING_PURCHASE_BONUS = "varies"  # if recipient buys NFT

# LISTENING REWARDS
LISTENING_BASE_REWARD = 2  # tokens per listen
LISTENING_COMPLETION_90_PLUS = 2.0  # bonus at 90%+ completion
LISTENING_COMPLETION_75_PLUS = 1.0  # bonus at 75%+ completion
LISTENING_COMPLETION_50_PLUS = 0.5  # bonus at 50%+ completion

# BANDWIDTH REWARDS
BANDWIDTH_BASE_REWARD = 5  # tokens
BANDWIDTH_PER_100MB = 1  # per 100MB served
BANDWIDTH_PER_LISTENER = 0.5  # per unique listener

# ROYALTY SPLITS (Primary Sale)
ROYALTY_ARTIST = 70%  # Artist keeps
ROYALTY_PLATFORM = 15%  # Platform operations
ROYALTY_NODE_OPERATORS = 10%  # LoRa network
ROYALTY_EARLY_BUYER = 5%  # Reserved

# ROYALTY SPLITS (Secondary Sale)
SECONDARY_ROYALTY_ARTIST = 70%  # Artist keeps 70%
SECONDARY_ROYALTY_NODES = 20%  # Higher node incentive
SECONDARY_ROYALTY_PLATFORM = 10%  # Platform fees
```

### Verifier Quorum Settings

```python
VERIFIER_NODES_TOTAL = 4  # Total verifiers
VERIFIER_NODES_REQUIRED = 3  # Minimum to respond
VERIFIER_APPROVALS_NEEDED = 2  # Minimum approvals
VERIFIER_ZK_CHECKS = 2  # ZK proofs must be valid from 2+
```

---

## 📊 Token Economics

### Supply & Inflation

- **Token Name**: DCMX Token
- **Total Supply**: Fixed (no inflation)
- **Decimals**: 18 (standard ERC-20)
- **Inflation**: ZERO (supply is capped)

### Reward Amounts & Rates

| Activity | Base Reward | Maximum Bonus | Time Frame |
|----------|------------|---------------|-----------|
| Share song | 1 DCMX | 1.5x if listened | Per share |
| Listen (full) | 2 DCMX | +2 bonus | Per listen |
| Serve 100MB | 1 DCMX | +0.5 per listener | Per serving |
| Refer user | TBD | TBD | Per referral |

### Lock-up Period

- **Purpose**: Prevent pump-and-dump schemes
- **Duration**: 90 days after earning
- **Benefit**: Can vote in DAO during lock-up
- **After Unlock**: Fully tradeable on exchanges

---

## 🎯 Quick API Reference

### Initialize Systems

```python
from dcmx.royalties import (
    RoyaltyPaymentStructure,
    RewardClaimVerifier,
    BlockchainIntegration,
    RewardDistributionEngine,
    RewardType
)

# Create instances
royalty = RoyaltyPaymentStructure()
verifier = RewardClaimVerifier(royalty)
blockchain = BlockchainIntegration(
    rpc_url="https://rpc.polygon.com",
    private_key="sk_...",
    nft_contract_address="0x...",
    token_contract_address="0x...",
    royalty_distributor_address="0x..."
)
engine = RewardDistributionEngine(royalty, verifier, blockchain)
```

### NFT Certificates

```python
# Issue certificate
cert = royalty.issue_nft_certificate(
    song_title="My Song",
    artist="Artist",
    content_hash="abc123",
    edition_number=1,
    max_editions=100,
    buyer_wallet="0x...",
    purchase_price_usd=50.0,
    purchase_price_tokens=500,
    watermark_hash="wm_hash",
    perceptual_fingerprint="fp_hash",
    nft_contract_address="0x...",
    token_id=1
)

# Get certificates
certs = royalty.list_user_certificates("0xWallet")
cert = royalty.get_certificate("cert_id")
```

### Sharing Rewards

```python
# Record sharing
share = royalty.record_sharing_event(
    sharer_wallet="0xAlice",
    song_content_hash="abc123",
    shared_with_wallet="0xBob",
    base_reward=1
)

# Apply listening bonus
royalty.apply_listening_multiplier(share.reward_id, 1.5)

# Get totals
tokens = royalty.calculate_total_sharing_tokens("0xAlice")
rewards = royalty.get_user_sharing_rewards("0xAlice")
```

### Listening Rewards

```python
# Record listening
listen = royalty.record_listening_event(
    listener_wallet="0xBob",
    song_content_hash="abc123",
    sharer_wallet="0xAlice",
    listen_duration_seconds=240,
    completion_percentage=95.0,
    base_reward=2
)

# Get totals
tokens = royalty.calculate_total_listening_tokens("0xBob")
rewards = royalty.get_user_listening_rewards("0xBob")
```

### Bandwidth Rewards

```python
# Record bandwidth serving
bandwidth = royalty.record_bandwidth_serving(
    node_id="node_xyz",
    song_content_hash="abc123",
    bytes_served=100_000_000,
    listeners_served=50,
    transmission_time_seconds=3600,
    base_reward=5
)

# Get totals
tokens = royalty.calculate_total_bandwidth_tokens("node_xyz")
rewards = royalty.get_node_bandwidth_rewards("node_xyz")
```

### Royalty Distribution

```python
# Primary sale
payment = royalty.process_primary_sale(
    song_title="My Song",
    artist="Artist",
    content_hash="abc123",
    purchase_price_usd=50.0,
    purchase_price_tokens=500,
    nft_contract_address="0x...",
    token_id=1
)

# Secondary sale
payment = royalty.process_secondary_sale(
    song_title="My Song",
    artist="Artist",
    content_hash="abc123",
    token_id=1,
    seller_wallet="0xAlice",
    buyer_wallet="0xBob",
    sale_price_usd=100.0,
    nft_contract_address="0x..."
)

# Get totals
artist_total = royalty.get_artist_royalties("Artist")
platform_total = royalty.get_platform_royalties()
node_pool = royalty.get_node_operator_pool()
```

### Reward Claims

```python
# Create claim
claim = royalty.create_reward_claim(
    claimant_wallet="0xAlice",
    claim_type=RewardType.SHARING,
    song_content_hash="abc123",
    total_tokens_claimed=15.5,
    activity_count=10
)

# Verify ZK proof
royalty.verify_reward_claim(claim.claim_id, zk_proof_data, signature)

# Approve and mint
royalty.approve_and_mint_tokens(claim.claim_id, tx_hash)

# Check status
pending = royalty.get_user_pending_claims("0xAlice")
claimed = royalty.get_user_total_claimed_tokens("0xAlice")
```

### Verifier Quorum

```python
# Register verifiers
for i in range(4):
    verifier.register_verifier_node(f"verifier_{i}")

# Distribute claim
verifiers = verifier.distribute_claim_to_verifiers(claim_id)

# Submit approval
from dcmx.royalties import VerifierNodeStatus
verifier.submit_verifier_approval(
    verifier_node_id="verifier_1",
    claim_id=claim_id,
    status=VerifierNodeStatus.APPROVED,
    zk_proof_result=True
)

# Check status
status = verifier.get_claim_verification_status(claim_id)
```

### Reporting

```python
# User report
report = royalty.generate_user_reward_report("0xAlice")
# Returns: sharing_tokens, listening_tokens, claimed, pending, certificates

# Artist report
report = royalty.generate_royalty_report("Artist Name")
# Returns: total_royalties, primary_sales, secondary_sales, nfts_issued

# Platform stats
stats = royalty.generate_platform_statistics()
# Returns: revenue, earnings, nfts_issued, claims, tokens_distributed
```

---

## 📂 File Structure

```
dcmx/
├── royalties/
│   ├── __init__.py              # Module exports
│   ├── royalty_structure.py    # Core classes (2200+ lines)
│   │   ├── NFTCertificate
│   │   ├── SharingReward
│   │   ├── ListeningReward
│   │   ├── BandwidthReward
│   │   ├── RoyaltyPayment
│   │   ├── RewardClaim
│   │   └── RoyaltyPaymentStructure
│   │
│   └── reward_integration.py    # Blockchain integration (1200+ lines)
│       ├── VerifierApproval
│       ├── RewardClaimVerifier
│       ├── BlockchainIntegration
│       └── RewardDistributionEngine
│
└── [root documentation]
    ├── ROYALTY_AND_REWARDS_GUIDE.md      # Complete guide (1500+ lines)
    ├── ROYALTY_AND_REWARDS_EXAMPLES.py   # Code examples (600+ lines)
    └── ROYALTY_CONFIGURATION.md          # This file
```

---

## 🔐 Security Checkpoints

### Before Processing NFT Sale
- ☑ Verify watermark hash
- ☑ Verify perceptual fingerprint
- ☑ Check buyer KYC status
- ☑ Verify audio content hash

### Before Approving Reward Claim
- ☑ ZK proof cryptographically valid
- ☑ 2+ verifiers confirm ZK proof
- ☑ No duplicate claims
- ☑ Activity timestamps valid

### Before Minting Tokens
- ☑ Verifier quorum reached (3+ approvals)
- ☑ Claim marked as verified
- ☑ Recipient wallet confirmed
- ☑ Transaction ready for broadcast

### Before Secondary Sale
- ☑ Seller owns NFT (verified on-chain)
- ☑ NFT contract supports ERC-2981
- ☑ Artist royalty percentage set
- ☑ Automatic royalty enforcement active

---

## 📈 Key Metrics & KPIs

### User Engagement
- **Sharing Rate**: % of users who share (target: >40%)
- **Listening Rate**: % of shared songs that get listened (target: >25%)
- **Repeat Purchase**: % who buy more editions (target: >30%)

### Platform Health
- **Average NFT Price**: Increasing over time (target: +10%/month)
- **Secondary Market Volume**: % of NFTs resold (target: >20%)
- **Artist Earnings**: Total royalties distributed (target: $1M+ / month)
- **Node Operator Earnings**: Bandwidth rewards distributed (target: +5% weekly)

### Token Metrics
- **Token Circulation**: % of supply actively trading (target: >60%)
- **Lock-up Duration**: Average lock-up before unlock (target: 60+ days)
- **Reward Redemption**: % of earned tokens claimed (target: >80%)
- **DAO Participation**: % voting in governance (target: >35%)

---

## 🚀 Deployment Checklist

### Smart Contracts
- [ ] MusicNFT.sol (ERC-721) deployed and verified
- [ ] DCMXToken.sol (ERC-20) deployed and verified
- [ ] RoyaltyDistributor.sol deployed and verified
- [ ] ERC-2981 royalty enforcement enabled
- [ ] 2-of-3 multisig initialized for admin functions

### Verifier Infrastructure
- [ ] 4 verifier nodes operational
- [ ] ZK proof validation working
- [ ] Quorum consensus tested
- [ ] Blockchain integration tested

### User Interfaces
- [ ] NFT purchase flow implemented
- [ ] Certificate display in user dashboard
- [ ] Sharing/listening tracking active
- [ ] Reward claim submission interface
- [ ] Royalty reporting dashboard

### Compliance & Security
- [ ] Audio watermarking verified (survives compression)
- [ ] Perceptual fingerprinting tested
- [ ] KYC integration for purchases
- [ ] OFAC sanctions checking
- [ ] 7-year audit trail active

### Monitoring & Alerts
- [ ] Revenue tracking dashboard
- [ ] Reward distribution monitoring
- [ ] Token minting alerts
- [ ] Failed claim notifications
- [ ] Royalty payout reconciliation

---

## 🔄 Data Flow Diagrams

### NFT Purchase → Royalty Distribution

```
User Purchase
     ↓
NFT Minted (ERC-721)
     ↓
Certificate Issued
     ↓
Price Split Calculated:
  - 70% Artist
  - 15% Platform
  - 10% Node Pool
  - 5% Early Buyer
     ↓
Royalties Transferred
     ↓
ERC-2981 Enforcement Set (70% secondary)
```

### Sharing → Listening → Reward Claim → Token Mint

```
Share Event
     ↓
+1 Token (Sharer)
     ↓
Listen Event
     ↓
+2 Base + Completion Bonus (Listener)
+1.5x Bonus (Sharer - if listened)
     ↓
User Accumulates Rewards
     ↓
Submit Claim (with ZK Proof)
     ↓
Distribute to 4 Verifiers
     ↓
Independent Verification
     ↓
Quorum Check (3+ approvals)
     ↓
Mint Tokens (ERC-20)
     ↓
User Receives DCMX Tokens
     ↓
90-Day Lock-up (voting only)
     ↓
Fully Tradeable
```

---

## 🎯 Common Use Cases

### Use Case 1: Artist Earns from First NFT Sale

```
1. Artist uploads song + watermarking
2. Sets price: $50 USD
3. User purchases Edition #1
4. Artist receives: 70% × $50 = $35
5. Report shows: $35 royalty earned
```

### Use Case 2: User Shares Song, Gets Rewards

```
1. User shares song with 10 friends
2. Gets: 1 token per share = 10 tokens
3. 5 friends listen (80%+ completion)
4. Gets: 1.5x bonus = 15 tokens total
5. Submits claim with ZK proof
6. Verifiers approve
7. Receives: 15 DCMX tokens (locked 90 days)
```

### Use Case 3: LoRa Node Earns from Bandwidth

```
1. Node serves 100MB to 50 listeners for 1 hour
2. Calculates reward:
   - Base: 5 tokens
   - Bandwidth: (100/100) × 1 = 1 token
   - Listeners: 50 × 0.5 = 25 tokens
   - Total: 31 tokens
3. Node accumulates across multiple services
4. Submits aggregate claim to verifiers
5. Verifiers approve
6. Receives DCMX tokens for network service
```

### Use Case 4: NFT Resold, Artist Gets Royalties

```
1. Alice buys Edition #5 for $50
   Artist gets: $35
2. Song becomes popular
3. Alice resells for $150 on secondary market
   Artist gets: 70% × $150 = $105
   Alice receives: $150 - $105 - $15 = $30 profit
4. Artist earns $35 + $105 = $140 total from this NFT
```

---

## 📞 Integration Points

### With LoRa Network (dcmx/lora/)
- Bandwidth reward tracking
- Node serving metrics
- Proximity proofs for location
- Energy consumption tracking

### With Blockchain (dcmx/blockchain/)
- NFT minting (ERC-721)
- Token minting (ERC-20)
- Royalty distribution contracts
- DAO governance integration

### With Compliance (dcmx/compliance/)
- KYC verification before purchase
- OFAC sanctions checking
- Transaction monitoring
- Audit trail logging

### With Audio Processing (dcmx/audio/)
- Watermark embedding & verification
- Perceptual fingerprinting
- Content hash computation
- DRM enforcement

---

## 🎓 Learning Path

1. **Start Here**: ROYALTY_AND_REWARDS_GUIDE.md
2. **See Examples**: ROYALTY_AND_REWARDS_EXAMPLES.py
3. **Deep Dive**: dcmx/royalties/royalty_structure.py docstrings
4. **Integration**: dcmx/royalties/reward_integration.py
5. **Deploy**: Follow deployment checklist above

---

## ❓ FAQ

**Q: Can I change the royalty percentages?**
A: Yes, modify values in RoyaltyPayment class initialization

**Q: How often do rewards settle?**
A: On-demand via claim submission, not automatic

**Q: What if a verifier node goes offline?**
A: Need 3-of-4 approvals, so 1 node can go down

**Q: Can artists change royalty % on secondary sales?**
A: Only via smart contract upgrade (requires governance)

**Q: How long until tokens are unlocked to trade?**
A: 90 days after earning, then fully tradeable

**Q: What's the minimum claim amount?**
A: 0.1 tokens (to minimize transaction fees)

---

Generated: December 9, 2025
Version: 1.0
Status: Production Ready
