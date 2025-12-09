# Artist-First Economics with Wallet Conversion - DCMX Implementation Guide

## 📋 Overview

DCMX implements an **artist-first economic model** where:
- **Artists get 100% of revenue on primary NFT sales** (no intermediaries)
- **Users earn fair rewards** for sharing, listening, voting, and bandwidth contribution
- **Artists maintain majority earnings** on secondary market resales (80%)
- **Wallet conversion is seamless** - users convert external coins to DCMX tokens

This document explains the economic model, wallet integration flow, and fair reward distribution.

---

## 🎯 Core Principles

### Principle 1: Artist Gets 100% on First Sale

When a user purchases an NFT for the first time:

```
User: "I want to buy Edition 1 of 'Midnight Rain'"
      ↓ (converts $10 USD → 10 DCMX tokens via wallet bridge)
      ↓ 
NFT Purchase: $10 purchase price
      ↓
Artist Receives: $10 (100%) - NO deductions, NO fees
      ↓
Platform: $0 (Primary sales are artist-only)
Nodes: $0 (Bandwidth rewarded separately via token system)
```

**Why?** Artists control their content. They deserve full value of their first sale.

### Principle 2: Users Earn Rewards for Engagement

Users who help promote the platform earn tokens:
- **Sharing**: Recommend song to other users → 0.5 tokens per share
- **Listening**: Engage with content → 1 token base, +1 for 90%+ completion
- **Voting**: Participate in governance → 0.5 tokens per vote
- **Bandwidth**: Serve content (LoRa nodes) → 2 tokens base + bonuses per MB/listener

**Why?** Community participation and promotion are valuable. Reward them.

### Principle 3: Artist Still Earns Majority on Resales

On secondary market (user-to-user NFT trading):

```
Resale Price: 20 DCMX
      ↓
Artist: 16 DCMX (80%) - Ongoing royalties
Seller: 3 DCMX (15%) - Incentive to sell
Platform: 1 DCMX (5%) - Operational cost
```

**Why?** Artist retains value as work appreciates, sellers get fair return.

### Principle 4: Wallet Integration is Frictionless

Users don't need crypto experience:

```
New User:
  1. Sign up with email
  2. Add payment method (credit card, bank transfer, Apple Pay)
  3. Platform converts to DCMX automatically
  4. Purchase NFT with one click
  5. Artist gets paid in DCMX (or converts to USD)
```

**Why?** Removes crypto UX barriers. Mainstream adoption.

---

## 💰 Wallet Conversion System

### Step 1: Register Wallet

User connects their blockchain wallet (MetaMask, WalletConnect, Coinbase Wallet):

```python
from dcmx.royalties.artist_first_economics import ArtistFirstEconomics

economics = ArtistFirstEconomics()

# User registers wallet
wallet_info = economics.register_user_wallet(
    user_id="user_alice_123",
    wallet_address="0x1234...5678",
    wallet_type="metamask"
)
```

### Step 2: Convert Currency to DCMX

User converts their currency (stablecoin, fiat, crypto) to DCMX:

```python
# Alice has $100 USDC on Polygon
# She converts it to DCMX tokens
conversion = economics.convert_to_dcmx(
    user_id="user_alice_123",
    source_currency="USDC",
    source_amount=100.0,
    exchange_rate=1.0,  # 1 USDC = 1 DCMX
    source_chain="polygon"
)

# Result:
# - Source: 100 USDC
# - Fee: 0.50 DCMX (0.5% bridge fee)
# - Received: 99.50 DCMX
# - Alice's balance: 99.50 DCMX
```

**Supported Conversions:**
- Stablecoins: USDC, USDT, DAI (1:1 rate)
- Major crypto: ETH, BTC, SOL (market rate)
- Fiat on-ramp: Credit card, bank transfer (market rate + 2% on-ramp fee)
- Cross-chain swaps: Polygon ↔ Ethereum ↔ Solana

### Step 3: Use DCMX to Purchase NFTs

Now Alice has DCMX and can purchase NFTs:

```python
# Alice buys Edition 1 of "Midnight Rain"
payment = economics.process_nft_purchase(
    user_id="user_alice_123",
    song_title="Midnight Rain",
    artist="Artist Bob",
    artist_wallet="0xbob...wallet",
    content_hash="sha256_midnight_rain",
    edition_number=1,
    max_editions=100,
    price_dcmx=10.0,
    price_usd_equivalent=10.0,
    watermark_hash="watermark_hash_123",
    perceptual_fingerprint="fingerprint_123",
    nft_contract_address="0xnft_contract",
    token_id=1
)

# Artist Bob receives 10 DCMX immediately (100%)
# Alice's balance: 99.50 - 10.0 = 89.50 DCMX
# Alice owns the NFT
```

### Conversion Fee Structure

| Operation | Fee | Notes |
|-----------|-----|-------|
| Stablecoin Bridge | 0.5% | USDC, USDT, DAI to DCMX |
| Fiat On-Ramp | 2.0% | Credit card, bank transfer |
| Crypto Exchange | 0.5% | ETH, BTC, SOL to DCMX |
| Cross-Chain Swap | 1.0% | Between Polygon/Ethereum/Solana |
| **Withdrawal** | 0.5% | DCMX back to external |

---

## 🏆 Fair Reward Distribution System

### Activity Types & Rewards

#### 1. Sharing (Promotion)
User shares song with other users via link/social media.

**Reward Schedule:**
- Base: 0.5 tokens per share
- +1.0 token if recipient listens
- +2.0 tokens if recipient purchases NFT
- +0.5 tokens if recipient votes

**Example:**
```python
# Alice shares "Midnight Rain" with 3 friends
reward = economics.record_sharing_activity(
    user_wallet="0x_alice",
    song_content_hash="sha256_midnight_rain",
    shared_with_wallet="0x_friend1",
    activity_count=3
)

# Alice earns:
# - Base: 0.5 * 3 = 1.5 tokens (3 shares)
# - If 1 friend listens: +1.0 token
# - If 1 friend buys: +2.0 tokens
# - Total possible: 1.5 + 1 + 2 = 4.5 tokens
```

#### 2. Listening (Engagement)
User listens to shared song.

**Reward Schedule:**
- Base: 1.0 token per listen
- +1.0 token for 90-100% completion
- +0.5 tokens for 75-89% completion
- +0.25 tokens for 50-74% completion

**Example:**
```python
# Alice listens to "Midnight Rain" and gets 85% through
reward = economics.record_listening_activity(
    user_wallet="0x_alice",
    song_content_hash="sha256_midnight_rain",
    listen_duration_seconds=240,
    completion_percentage=85.0
)

# Alice earns:
# - Base: 1.0 token
# - Completion (75-89%): +0.5 tokens
# - Total: 1.5 tokens
```

#### 3. Voting (Governance)
User votes on platform governance proposals.

**Reward Schedule:**
- Base: 0.5 tokens per vote
- +0.2 bonus if 50%+ of token holders vote
- +0.1 bonus if vote matches community consensus

**Example:**
```python
# Alice votes "Yes" on proposal "Double listening rewards"
# The vote passes (matches community consensus)
reward = economics.record_voting_activity(
    user_wallet="0x_alice",
    governance_proposal_id="gov_proposal_001",
    vote_matches_community=True
)

# Alice earns:
# - Base: 0.5 tokens
# - Community match: +0.1 tokens
# - Total: 0.6 tokens
```

**Note:** Voting is advisory, not binding. Platform team makes final decisions. This prevents vote-buying while rewarding participation.

#### 4. Bandwidth Contribution (Network Service)
LoRa node serves content to other users.

**Reward Schedule:**
- Base: 2.0 tokens per service event
- +0.5 tokens per 100MB served
- +0.1 tokens per unique listener reached

**Example:**
```python
# Bob's LoRa node serves "Midnight Rain" to 5 users
# Total: 450 MB of data
reward = economics.record_bandwidth_contribution(
    node_id="lora_node_bob",
    song_content_hash="sha256_midnight_rain",
    bytes_served=450 * 1024 * 1024,  # 450 MB
    listeners_served=5
)

# Bob earns:
# - Base: 2.0 tokens
# - Per 100MB: 0.5 * 4.5 = 2.25 tokens
# - Per listener: 0.1 * 5 = 0.5 tokens
# - Total: 2.0 + 2.25 + 0.5 = 4.75 tokens
```

#### 5. Referral (Growth)
User refers new users to platform.

**Reward Schedule:**
- Base: 1.0 token per new user referred
- +0.5 tokens if referred user makes first purchase
- +0.2 tokens per month if referred user stays active

**Example:**
```python
# Alice refers her friend Charlie
# Charlie makes first NFT purchase
reward = economics.record_referral_activity(
    referrer_wallet="0x_alice",
    referred_wallet="0x_charlie",
    referred_made_purchase=True
)

# Alice earns:
# - Base (new user): 1.0 token
# - First purchase bonus: +0.5 tokens
# - Total: 1.5 tokens
```

### Fair Distribution Philosophy

**Why these reward amounts?**

1. **Sharing is worth less than listening** (0.5 vs 1.0)
   - Sharing is easy (1-click link)
   - Listening requires engagement (time investment)

2. **Completion bonuses incentivize quality**
   - Listening 50% = 1.25 tokens
   - Listening 90% = 2.0 tokens
   - Encourages artists to make good songs

3. **Voting is carefully balanced** (0.5-0.8 tokens)
   - Not enough to profit-maximize participation
   - Enough to incentivize civic engagement
   - Prevents Sybil attacks via ZK proofs

4. **Bandwidth is highest** (2-4.75 tokens)
   - Requires infrastructure (LoRa hardware)
   - Requires ongoing cost (electricity, data)
   - Essential for network viability

5. **Referrals maintain growth** (1-1.5 tokens)
   - Incentivizes network effect
   - Can earn ongoing (0.2 per month)
   - Aligned with platform growth

---

## 📊 Primary vs. Secondary Sales

### Primary Sale (100% Artist)

```
Event: User purchases NFT Edition 1 for first time
       ↓
Price: 10 DCMX
       ↓
Artist:   10 DCMX (100%)
Platform: 0 DCMX
Nodes:    0 DCMX
       ↓
Total distributed: 10 DCMX (all to artist)
```

**This happens once per edition** (when someone buys Edition 1, Edition 2, etc. for first time).

### Secondary Sale (Artist 80%, Seller 15%, Platform 5%)

```
Event: User1 resells their NFT Edition 1 to User2
       ↓
Price: 20 DCMX (market rate, possibly higher than original)
       ↓
Artist:   16 DCMX (80%) - Ongoing royalties on appreciation
Seller:   3 DCMX (15%) - Incentive to trade
Platform: 1 DCMX (5%) - Operational costs
       ↓
Total distributed: 20 DCMX
```

**This can happen many times** (User2 later sells to User3, User3 to User4, etc.).

### Example Timeline

```
Day 1:
- Alice buys Edition 1: 10 DCMX → Artist gets 10 DCMX (100%)
  (Platform: +0 DCMX, Alice owns Edition 1)

Day 7:
- Edition 1 value appreciates to 15 DCMX
- Bob wants to buy Edition 1 from Alice
- Alice sells to Bob for 15 DCMX:
  → Artist gets 12 DCMX (80%)
  → Alice gets 2.25 DCMX (15%)
  → Platform gets 0.75 DCMX (5%)
  (Bob now owns Edition 1)

Day 14:
- Edition 1 appreciates to 25 DCMX
- Charlie buys Edition 1 from Bob for 25 DCMX:
  → Artist gets 20 DCMX (80%)
  → Bob gets 3.75 DCMX (15%)
  → Platform gets 1.25 DCMX (5%)
  (Charlie now owns Edition 1)

Artist Lifetime Earnings from Edition 1: 10 + 12 + 20 = 42 DCMX
  (Started at 10, earned additional 32 DCMX from appreciation)
```

---

## 🔐 Security & Compliance

### Smart Contract Architecture

**Primary Sale Flow:**
```
1. User connects wallet → Sign auth message (prove ownership)
2. User converts currency → Bridge validates & mints DCMX
3. User purchases NFT → Escrow holds DCMX
4. Artist confirmed → Smart contract transfers DCMX
5. NFT minted → Transferred to user's wallet
6. Artist withdraws → Can convert DCMX to external currency
```

### Zero-Knowledge Proof Verification

All reward claims verified with ZK proofs to prevent fraud:

```python
# User claims: "I listened to this song for 90%"
# System verifies with ZK proof (no revealing actual listening data):
# - Proof that user is real (not Sybil attack)
# - Proof that user listened 90%+ (from encrypted listening stats)
# - Proof that user hasn't double-claimed for same listen
```

### Audit Trail & Compliance

All transactions immutably logged:

```
- Conversion ID: conv_user_123_1699999999
- Blockchain: Polygon
- Transaction Hash: 0x1234...abcd
- Artist Payout: 10 DCMX
- Timestamp: 2024-11-15T10:30:00Z
- Status: Completed
```

---

## 💾 Data Structures

### WalletConversion

```python
@dataclass
class WalletConversion:
    conversion_id: str              # Unique ID
    user_wallet: str                # User's blockchain wallet
    timestamp: str                  # ISO timestamp
    
    # Input (What user converts FROM)
    source_currency: str            # "USDC", "ETH", "USD"
    source_amount: float            # Amount being converted
    source_chain: str               # "ethereum", "polygon"
    
    # Output (What user receives)
    dcmx_tokens_received: float     # DCMX tokens user gets
    exchange_rate: float            # Conversion rate
    
    # Blockchain proof
    transaction_hash: str           # On-chain tx hash
    conversion_status: str          # "completed", "pending", "failed"
    completion_timestamp: str       # When it completed
    
    # Fees
    conversion_fee_percentage: float = 0.5
    actual_conversion_fee: float    # Calculated fee amount
```

### ArtistFirstPayment

```python
@dataclass
class ArtistFirstPayment:
    payment_id: str                 # Unique payment ID
    song_content_hash: str          # SHA256 of audio
    song_title: str                 # Song name
    artist: str                     # Artist name
    artist_wallet: str              # Artist's blockchain wallet
    
    # Purchase details
    edition_number: int             # 1-100
    max_editions: int               # Total editions
    buyer_wallet: str               # Who bought
    purchase_price_dcmx: float      # Purchase price
    purchase_price_usd_equivalent: float
    
    # Blockchain proof
    transaction_hash: str           # NFT minting tx
    nft_contract_address: str       # ERC-721 contract
    token_id: int                   # NFT ID
    purchase_date: str              # ISO timestamp
    blockchain: str                 # "polygon", "ethereum"
    
    # Artist payout (100%)
    artist_payout_dcmx: float       # Full purchase price
    artist_payout_status: str       # "completed", "pending"
    artist_payout_timestamp: str    # When paid
    
    # Content verification
    watermark_hash: str             # Audio watermark proof
    perceptual_fingerprint: str     # Content fingerprint
```

### UserActivityReward

```python
@dataclass
class UserActivityReward:
    reward_id: str                  # Unique ID
    user_wallet: str                # User earning reward
    activity_type: UserActivityType # SHARING, LISTENING, etc.
    
    # Activity details
    song_content_hash: str          # Which song (if applicable)
    activity_timestamp: str         # When activity happened
    activity_count: int             # Quantity
    
    # Reward calculation
    base_reward_tokens: float       # Base amount
    multiplier: float = 1.0         # Activity multiplier
    engagement_bonus: float = 0.0   # Bonus amount
    
    # Total = (base * multiplier) + bonus
    
    # Verification
    is_verified: bool = False       # ZK proof verified
    is_claimed: bool = False        # User claimed reward
    claim_timestamp: str            # When claimed
```

---

## 🎯 Implementation Checklist

### Phase 1: Wallet Integration
- [ ] Deploy bridge contracts (USDC → DCMX conversion)
- [ ] Integrate MetaMask, WalletConnect, Coinbase
- [ ] Implement fiat on-ramp (credit card/bank transfer)
- [ ] Test cross-chain swaps
- [ ] Set up withdrawal to external wallets

### Phase 2: Primary Sales
- [ ] Deploy NFT contract (ERC-721)
- [ ] Implement purchase flow (artist gets 100%)
- [ ] Integrate with wallet system
- [ ] Add watermarking & fingerprinting
- [ ] Test artist payouts

### Phase 3: Reward System
- [ ] Implement sharing activity tracking
- [ ] Implement listening activity tracking
- [ ] Implement voting activity tracking
- [ ] Implement bandwidth activity tracking
- [ ] Add ZK proof verification

### Phase 4: Secondary Market
- [ ] Enable NFT resales
- [ ] Implement 80/15/5 split (artist/seller/platform)
- [ ] Set up royalty enforcement (ERC-2981)
- [ ] Test resale flow

### Phase 5: Reporting & Analytics
- [ ] Artist earnings reports
- [ ] User activity reports
- [ ] Platform statistics dashboard
- [ ] Tax reporting (for accountants)

---

## 📚 Quick Reference

### Key Methods

```python
economics = ArtistFirstEconomics()

# Wallet Management
economics.register_user_wallet(user_id, wallet_address)
economics.convert_to_dcmx(user_id, source, amount, rate)
economics.get_user_dcmx_balance(user_id)

# Primary Sales
economics.process_nft_purchase(...)  # Artist gets 100%

# Rewards
economics.record_sharing_activity(...)
economics.record_listening_activity(...)
economics.record_voting_activity(...)
economics.record_bandwidth_contribution(...)
economics.record_referral_activity(...)

# Reporting
economics.generate_artist_report(artist)
economics.generate_user_activity_report(user_wallet)
economics.generate_platform_statistics()
```

### Reward Quick Reference

| Activity | Base | Bonus | Total |
|----------|------|-------|-------|
| Share (1x) | 0.5 | 0 | 0.5 |
| Share + Listen | 0.5 | 1.0 | 1.5 |
| Share + Purchase | 0.5 | 2.0 | 2.5 |
| Listen (50%) | 1.0 | 0.25 | 1.25 |
| Listen (75%) | 1.0 | 0.5 | 1.5 |
| Listen (90%) | 1.0 | 1.0 | 2.0 |
| Vote | 0.5 | 0-0.3 | 0.5-0.8 |
| Bandwidth 1MB | 2.0 | 0.005 | 2.005 |
| Bandwidth 100MB | 2.0 | 0.5 | 2.5 |
| Referral | 1.0 | 0-0.5 | 1.0-1.5 |

### Fee Structure

| Operation | Fee % | Notes |
|-----------|-------|-------|
| Bridge (Stablecoins) | 0.5% | USDC, USDT |
| Fiat On-Ramp | 2.0% | Credit card, ACH |
| Withdrawal | 0.5% | DCMX → External |
| **Artist Primary Sale** | **0%** | **100% to artist** |

---

## 🚀 Getting Started

See `ARTIST_FIRST_ECONOMICS_EXAMPLES.py` for working code examples:
1. User wallet registration
2. Currency conversion
3. NFT purchase (artist 100%)
4. Reward recording (all activity types)
5. Secondary sale processing
6. Report generation

See `/workspaces/DCMX/dcmx/royalties/artist_first_economics.py` for full implementation.
