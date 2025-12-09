# DCMX Artist NFT Wallet Connection System

## Overview

The Artist NFT Wallet Connection System enables musicians to:
- Create verified artist profiles with identity verification
- Connect blockchain wallets (MetaMask, WalletConnect, etc.)
- Verify ownership of their own NFTs
- Manage royalties and distribution rights
- Link NFTs to watermarked audio content for proof of authenticity

This system bridges the gap between **artist identity** → **wallet ownership** → **NFT verification** → **watermarked content** → **blockchain proof**.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Artist NFT System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Artist Profile Management                                │   │
│  │ ├─ Create profile (legal name, artist name, email)      │   │
│  │ ├─ Email verification                                    │   │
│  │ ├─ Identity verification (KYC/AML)                      │   │
│  │ └─ DCMX verified artist badge                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Wallet Connection                                        │   │
│  │ ├─ Challenge-response signature verification           │   │
│  │ ├─ Support: MetaMask, WalletConnect, Ledger, Trezor   │   │
│  │ ├─ Multiple wallets per artist                         │   │
│  │ └─ Primary wallet designation                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ NFT Ownership Verification                              │   │
│  │ ├─ Blockchain queries (ERC-721, ERC-1155)              │   │
│  │ ├─ Verify artist owns their own NFTs                   │   │
│  │ ├─ Link NFTs to DCMX content hashes                    │   │
│  │ └─ Content watermark matching                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                            ↓                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Rights & Royalty Management                             │   │
│  │ ├─ Primary/secondary sale royalty %                    │   │
│  │ ├─ Rights type (full ownership, exclusive, limited)   │   │
│  │ ├─ Royalty payment address                             │   │
│  │ └─ Collaboration splits                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
    Integrates with Watermark & ZK Proof Systems
```

## Key Components

### 1. ArtistWalletManager

Main orchestrator for artist management.

**Responsibilities:**
- Create and manage artist profiles
- Wallet connection challenges and verification
- NFT registration
- Identity verification
- DCMX artist verification

**Key Methods:**

```python
# Profile creation
profile = manager.create_artist_profile(
    legal_name="Jane Doe",
    artist_name="JaneDoe",
    email="jane@example.com"
)

# Wallet challenge
challenge = manager.create_wallet_connection_challenge(
    artist_id="uuid",
    wallet_address="0x..."
)

# Verify signature and connect wallet
success, msg, wallet = manager.connect_wallet(
    artist_id="uuid",
    challenge_id="uuid",
    signature="0x...",
    wallet_type=WalletType.METAMASK
)

# Register owned NFT
success, msg, nft = manager.add_owned_nft(
    artist_id="uuid",
    nft_id="token_123",
    contract_address="0x..."
)

# Mark as DCMX verified artist
success, msg = manager.mark_as_dcmx_verified_artist(artist_id="uuid")

# Get verification status
status = manager.get_verification_status(artist_id="uuid")
```

### 2. ArtistProfile

Immutable profile record for artist.

**Fields:**
- `artist_id` - Unique identifier (UUID)
- `legal_name` - Full legal name
- `artist_name` - Public stage name
- `email` - Contact email
- `primary_wallet` - Main blockchain wallet
- `connected_wallets` - Additional wallets
- `owned_nfts` - NFTs created/owned by artist
- `royalty_settings` - Royalty configuration
- `verification_status` - PENDING, VERIFIED, FAILED, EXPIRED, REVOKED
- `dcmx_verified_artist` - DCMX content creator badge

### 3. WalletAddress

Blockchain wallet with verification metadata.

**Fields:**
- `address` - Wallet address (0x...)
- `chain` - Network (ethereum, polygon, etc.)
- `wallet_type` - MetaMask, WalletConnect, Ledger, etc.
- `is_verified` - Signature verification status
- `verified_at` - Verification timestamp
- `balance_eth` - Current ETH balance
- `is_active` - Wallet status
- `transaction_count` - Historical transactions

### 4. WalletSignatureChallenge

Challenge for wallet signature verification.

**Flow:**
```
1. Manager creates challenge: message to sign + nonce
2. User signs message with wallet (MetaMask, etc.)
3. Manager verifies signature
4. Challenge marked as used (prevents replay)
5. Wallet connected to artist profile
```

**Features:**
- 15-minute expiration
- One-time use (prevents replay attacks)
- Includes artist name, nonce, timestamp
- No gas required (message signing only)

### 5. NFTOwnershipVerifier

Verifies NFT ownership through blockchain queries.

**Responsibilities:**
- Query blockchain for NFT ownership
- Verify contract legitimacy (ERC-721, ERC-1155)
- Link NFTs to DCMX content
- Verify watermark authenticity
- Register verified creators

**Methods:**

```python
# Verify NFT ownership
verified, msg, result = await verifier.verify_nft_ownership(
    contract_address="0x...",
    nft_id="token_123",
    claimed_owner="0x..."
)

# Verify multiple NFTs
results = await verifier.verify_batch_ownership([
    ("0xContract1", "token1", "0xWallet"),
    ("0xContract1", "token2", "0xWallet"),
])

# Get artist portfolio
success, msg, nfts = await verifier.get_artist_nft_portfolio(
    artist_wallet="0x...",
    contract_address="0x..."
)

# Verify contract is legitimate
valid, msg, info = await verifier.verify_contract_legitimacy(
    "0x...",
    expected_standard=TokenStandard.ERC_721
)
```

### 6. BlockchainProvider

Abstract interface for blockchain queries.

**Implementations:**
- `MockBlockchainProvider` - For testing
- `Web3Provider` - Production (Ethereum/Polygon/etc.)
- `GraphQLProvider` - Fast queries via The Graph

```python
# Provider interface
provider = MockBlockchainProvider()
provider.set_mock_ownership(contract, nft_id, owner)
result = await provider.get_nft_owner(contract, nft_id)

# In production:
# from dcmx.artist.web3_provider import Web3Provider
# provider = Web3Provider(rpc_url="https://rpc.polygonscan.com")
# result = await provider.get_nft_owner(contract, nft_id)
```

### 7. ContentWatermarkLink

Links NFT to DCMX watermarked content.

**Enables:**
- Verify NFT contains expected audio
- Match watermark proof to NFT metadata
- Confirm artist created the content
- Prevent counterfeit NFTs

**Matching:**
- Content hash verification
- Watermark proof chain verification
- Metadata matching (title, artist, fingerprint)
- Confidence scoring (0-100%)

## Verification Flow

### Complete Artist Onboarding

```python
import asyncio
from dcmx.artist import ArtistWalletManager, NFTOwnershipVerifier, MockBlockchainProvider

# 1. Create artist profile
manager = ArtistWalletManager()
artist = manager.create_artist_profile(
    legal_name="Taylor Swift",
    artist_name="TaylorSwift",
    email="taylor@example.com"
)

# 2. Connect wallet
challenge = manager.create_wallet_connection_challenge(
    artist.artist_id,
    "0xTaylorSwift"
)

# User signs with MetaMask/WalletConnect
signature = await user_wallet.sign_message(challenge.message)

success, msg, wallet = manager.connect_wallet(
    artist.artist_id,
    challenge.challenge_id,
    signature,
    WalletType.METAMASK
)
# ✓ Wallet connected

# 3. Verify identity (KYC)
manager.verify_artist_identity(
    artist.artist_id,
    kyc_provider="stripe",
    kyc_verification_id="verify_stripe_123"
)
# ✓ Identity verified

# 4. Verify email
artist.email_verified = True

# 5. Mark as DCMX verified artist
success, msg = manager.mark_as_dcmx_verified_artist(artist.artist_id)
# ✓ DCMX verified badge awarded

# 6. Register NFTs
success, msg, nft = manager.add_owned_nft(
    artist.artist_id,
    "ts_song_001",
    "0xMusicNFT"
)
# ✓ NFT registered

# 7. Verify NFT ownership on blockchain
verifier = NFTOwnershipVerifier()
verified, msg, result = await verifier.verify_nft_ownership(
    "0xMusicNFT",
    "ts_song_001",
    "0xTaylorSwift"
)
# ✓ Ownership verified

# 8. Link to watermarked content
verifier.link_nft_to_content(
    nft_id="ts_song_001",
    contract_address="0xMusicNFT",
    dcmx_content_hash="sha256_hash",
    watermark_proof_chain_id="proof_uuid"
)
# ✓ Content linked

# 9. Verify watermark authenticity
verified, msg, confidence = verifier.verify_nft_watermark_match(
    nft_id="ts_song_001",
    watermark_proof_chain_id="proof_uuid",
    dcmx_content_hash="sha256_hash",
    title="Anti-Hero",
    artist="Taylor Swift"
)
# ✓ Watermark verified (confidence: 90%)

# 10. Final verification status
status = manager.get_verification_status(artist.artist_id)
print(status)
# {
#   'dcmx_verified': True,
#   'wallet_connected': True,
#   'email_verified': True,
#   'identity_verified': True,
#   'nfts_registered': 1,
#   'requirements_met': {
#       'wallet': True,
#       'email': True,
#       'identity': True,
#       'profile_info': True
#   }
# }
```

## Enums & Data Types

### WalletType
```python
METAMASK = "metamask"
WALLETCONNECT = "walletconnect"
LEDGER = "ledger"
TREZOR = "trezor"
COINBASE = "coinbase"
ARGENT = "argent"
OTHER = "other"
```

### VerificationStatus
```python
PENDING = "pending"
VERIFIED = "verified"
FAILED = "failed"
EXPIRED = "expired"
REVOKED = "revoked"
```

### RightsType
```python
FULL_OWNERSHIP = "full_ownership"
EXCLUSIVE_DISTRIBUTION = "exclusive_distribution"
LIMITED_DISTRIBUTION = "limited_distribution"
STREAMING_ONLY = "streaming_only"
SAMPLE_RIGHTS = "sample_rights"
COLLABORATION = "collaboration"
```

### RoyaltyTier
```python
NONE = 0
LOW = 5          # 5%
STANDARD = 10    # 10%
HIGH = 15        # 15%
PREMIUM = 20     # 20%
CUSTOM = -1      # Custom percentage
```

### BlockchainNetwork
```python
ETHEREUM = "ethereum"
POLYGON = "polygon"
ARBITRUM = "arbitrum"
OPTIMISM = "optimism"
BASE = "base"
SEPOLIA_TESTNET = "sepolia"
MUMBAI_TESTNET = "mumbai"
```

### TokenStandard
```python
ERC_721 = "ERC-721"      # Single ownership
ERC_1155 = "ERC-1155"    # Multiple ownership
ERC_404 = "ERC-404"      # Hybrid
```

## Integration Points

### With Watermark Protection System
```python
from dcmx.audio.watermark_protection import WatermarkProtectionManager

# Artist wants to distribute their music
content_hash = "sha256_of_audio"
watermark_verified, records = protection_manager.verify_watermark_access(
    content_hash=content_hash,
    user_id=artist_id,
    access_context="distribution"
)

if watermark_verified:
    # Artist can distribute their own content
    distribute_to_network(content_hash)
```

### With ZK Proof System
```python
from dcmx.audio.zk_watermark_proof import CascadingProofOrchestrator

# Link cascading proof to artist NFT
orchestrator = CascadingProofOrchestrator()
chain = orchestrator.create_cascade_chain(
    watermark_data=audio_bytes,
    chain_depth=3
)

# Store proof chain ID in NFT
nft_ownership = manager.add_owned_nft(
    artist_id=artist_id,
    nft_id="token_123",
    contract_address="0x..."
)

# Link proof to NFT
verifier.link_nft_to_content(
    nft_id="token_123",
    contract_address="0x...",
    dcmx_content_hash=content_hash,
    watermark_proof_chain_id=chain.chain_id
)
```

### With Compliance System
```python
from dcmx.compliance.kyc_verifier import KYCVerifier

# Verify artist identity before allowing NFT minting
kyc = KYCVerifier()
result = await kyc.verify_user(
    user_id=artist_id,
    legal_name=artist.legal_name,
    email=artist.email,
    dob=artist.date_of_birth,
    ssn=artist_ssn_hashed
)

if result['verified']:
    manager.verify_artist_identity(
        artist_id=artist_id,
        kyc_provider="stripe",
        kyc_verification_id=result['verification_id']
    )
```

### With Blockchain Agent
```python
from dcmx.blockchain.blockchain_agent import BlockchainAgent

# Artist mints their verified NFT
blockchain = BlockchainAgent(rpc_url="...", private_key="...")

# Get artist wallet
artist = manager.get_artist_profile(artist_id)
artist_wallet = artist.primary_wallet.address

# Mint NFT
tx_hash = await blockchain.mint_nft(
    artist_wallet=artist_wallet,
    content_hash=content_hash,
    watermark_proof_chain_id=proof_chain_id,
    title=track_title,
    artist_name=artist.artist_name,
    edition_number=1,
    max_editions=100,
    price_wei=int(1e18)  # 1 ETH
)

# Link to artist profile
nft = manager.add_owned_nft(
    artist_id=artist_id,
    nft_id=token_id,
    contract_address=nft_contract_address
)
```

## Security Considerations

### Wallet Signature Verification
- **Challenge-response**: Prevents MITM attacks
- **Expiration**: Challenges expire after 15 minutes
- **One-time use**: Prevents replay attacks
- **No private keys**: Only message signing required

### Identity Verification
- **KYC/AML**: Third-party verification (Stripe, Onfido, Sumsub)
- **Email verification**: Ownership confirmation
- **Separated storage**: KYC data in secure vault
- **7-year audit trail**: Regulatory compliance

### NFT Verification
- **Blockchain queries**: Verify actual ownership on-chain
- **Contract whitelisting**: Only verified contracts
- **Watermark matching**: Confirm artist created content
- **Proof chain verification**: ZK proofs validate authenticity

### Royalty Management
- **Payment address validation**: Ensure correct wallet
- **Percentage caps**: 0-50% limits
- **Immutable records**: Blockchain-backed royalties
- **Audit trail**: Every royalty transaction logged

## Testing

All 35 artist system tests pass:

```bash
pytest tests/test_artist_nft_system.py -v
# 35 passed in 0.93s ✓
```

**Test Coverage:**
- Artist profile creation & management (5 tests)
- Wallet connection challenges & verification (6 tests)
- Wallet connection & multi-wallet support (4 tests)
- NFT ownership registration (3 tests)
- Identity verification (3 tests)
- Royalty configuration (2 tests)
- Verification status reporting (2 tests)
- NFT ownership verification (4 tests)
- Content watermark linking (5 tests)
- Complete end-to-end workflow (1 test)

## Production Deployment

### Phase 1: Testing (Current)
- ✓ MockBlockchainProvider for testing
- ✓ All 35 tests passing
- ✓ Integration with watermark and ZK proof systems

### Phase 2: Staging
- Deploy Web3Provider with testnet RPC
- Test with Mumbai (Polygon testnet) NFTs
- Implement real KYC provider integration
- Connect to staging blockchain contracts

### Phase 3: Production
- Deploy with production RPC endpoints
- Mainnet support (Ethereum, Polygon)
- Real KYC/AML providers (Stripe, Onfido)
- Artist onboarding campaign
- MetaMask/WalletConnect integration

### Environment Variables
```bash
# Blockchain
ETHEREUM_RPC_URL="https://rpc.infura.io/v3/YOUR_KEY"
POLYGON_RPC_URL="https://polygon-rpc.com"

# KYC
KYC_PROVIDER="stripe"  # or "onfido", "sumsub"
STRIPE_API_KEY="sk_test_..."
STRIPE_IDENTITY_KEY="..."

# Compliance
OFAC_API_KEY="..."
SANCTIONS_CHECK_ENABLED="true"

# Email
SENDGRID_API_KEY="SG...."
```

## Future Enhancements

1. **Collaboration Support**
   - Multiple artist splits on single NFT
   - Collaborative royalty distribution
   - Joint ownership verification

2. **Advanced Rights Management**
   - Time-limited distribution rights
   - Territorial restrictions
   - Sampling permissions
   - Remix rights management

3. **Secondary Sales**
   - Royalty enforcement on resales
   - Marketplace integration
   - Creator royalty tracking

4. **Analytics Dashboard**
   - Artist earnings tracking
   - NFT sale statistics
   - Watermark verification reports
   - Royalty distribution history

5. **API for Platforms**
   - OAuth integration for music platforms
   - Batch artist verification
   - Automated royalty payments
   - Real-time verification webhooks

## References

- [DCMX Architecture Guide](./copilot-instructions.md)
- [Watermark Protection System](./COMPLETE_WATERMARK_INTEGRATION.md)
- [Zero-Knowledge Proof Watermarking](./ZK_WATERMARK_PROOF_FINAL_SUMMARY.md)
- [Blockchain Integration](../blockchain/)
- [ERC-721 Standard](https://eips.ethereum.org/EIPS/eip-721)
- [ERC-1155 Standard](https://eips.ethereum.org/EIPS/eip-1155)
- [ERC-2981 Royalties](https://eips.ethereum.org/EIPS/eip-2981)
