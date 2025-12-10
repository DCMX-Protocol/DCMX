# DCMX Web3 Architecture

## Overview

DCMX implements an enterprise-grade Web3 architecture that combines TRON blockchain (source of truth) with PostgreSQL indexing for scalability and performance. This hybrid approach provides the benefits of decentralization while maintaining query performance for user-facing features.

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│   DCMX Frontend / Mobile App            │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
   ┌────▼─────┐      ┌────▼──────┐
   │ FastAPI  │      │ Flask API  │
   │ /api/v1/ │      │ /legal/    │
   └────┬─────┘      └────┬───────┘
        │                 │
        └────────┬────────┘
                 │
        ┌────────▼──────────────┐
        │  TRON Client Wrapper  │
        │  (dcmx/tron/client.py)│
        └────────┬──────────────┘
                 │
    ┌────────────▼──────────────────┐
    │     TRON BLOCKCHAIN            │
    │     (Source of Truth)          │
    ├────────────────────────────────┤
    │  ├─ DCMXToken (TRC-20)         │
    │  ├─ MusicNFT (TRC-721)         │
    │  ├─ ComplianceRegistry         │
    │  ├─ RewardVault                │
    │  └─ RoyaltyDistributor         │
    └────────────┬───────────────────┘
                 │ (Events)
        ┌────────▼──────────────┐
        │  Event Indexer Daemon │
        │  (scripts/start_indexer.py)│
        └────────┬──────────────┘
                 │
        ┌────────▼──────────────┐
        │  PostgreSQL Index DB  │
        │  (Fast Queries)        │
        ├───────────────────────┤
        │  - blockchain_events  │
        │  - user_profiles      │
        │  - nft_index          │
        │  - reward_claims      │
        │  - transaction_index  │
        │  - compliance_index   │
        │  - analytics          │
        └───────────────────────┘
```

## Design Principles

### 1. Blockchain as Source of Truth

All critical state changes are written to TRON smart contracts:
- **Token transfers** → DCMXToken contract
- **NFT minting/transfers** → MusicNFT contract
- **Legal acceptances** → ComplianceRegistry contract
- **Reward claims** → RewardVault contract
- **Royalty payments** → RoyaltyDistributor contract

### 2. PostgreSQL for Query Performance

Blockchain events are indexed to PostgreSQL for:
- Fast queries (milliseconds vs. seconds)
- Complex filtering and aggregations
- Full-text search
- Analytics and dashboards
- Reduced blockchain API calls

### 3. Event-Driven Synchronization

The Event Indexer Daemon:
- Monitors smart contract events in real-time
- Parses and validates event data
- Updates PostgreSQL index tables
- Handles chain reorganizations
- Provides fault tolerance

## Component Details

### TRON Layer (`dcmx/tron/`)

#### Client (`client.py`)
- Wraps tronpy library for simplified blockchain interaction
- Manages wallet connections and transaction signing
- Provides retry logic and error handling
- Supports both mainnet and testnet (Shasta/Nile)

#### Contracts (`contracts.py`)
- High-level interfaces for each smart contract
- Type-safe function calls with validation
- Automatic gas estimation
- Event parsing and filtering

#### Events (`events.py`)
- Typed event definitions (dataclasses)
- Event parsing from raw blockchain data
- Event filtering and transformation

#### Config (`config.py`)
- Network configuration (mainnet/testnet)
- Contract address management
- API key handling

### Database Layer (`dcmx/database/`)

#### Models (`models.py`)
- SQLAlchemy ORM models for all indexed data
- Proper indexing for query performance
- Relationships between entities
- GDPR-compliant soft deletes

#### Database (`database.py`)
- Connection pooling and management
- Session lifecycle handling
- Transaction management
- Connection health checks

#### Sync (`sync.py`)
- Blockchain-to-database synchronization
- Event parsing and indexing
- Batch processing for efficiency
- Resumable syncing from last block

#### Queries (`queries.py`)
- Common query helpers
- Optimized query patterns
- Pagination support
- Aggregations and analytics

### Smart Contracts (`dcmx/tron/contracts/`)

#### DCMXToken.sol (TRC-20)
**Purpose**: Platform utility token for rewards and governance

**Features**:
- Fixed maximum supply (configurable)
- Minting for reward claims (controlled by RewardVault)
- Burning for platform fees
- 18 decimals standard

**Key Functions**:
- `transfer(to, amount)` - Transfer tokens
- `mint(to, amount)` - Mint new tokens (minters only)
- `burn(amount)` - Burn tokens
- `addMinter(address)` - Add authorized minter (owner only)

#### MusicNFT.sol (TRC-721)
**Purpose**: Music rights NFTs with metadata and edition tracking

**Features**:
- Unique music NFTs with rich metadata
- Edition tracking (1 of 100, etc.)
- ERC-2981 royalty standard support
- IPFS/Arweave metadata storage

**Key Functions**:
- `mintMusic(to, title, artist, contentHash, edition, maxEditions, royaltyBps)` - Mint NFT
- `getMetadata(tokenId)` - Get NFT metadata
- `royaltyInfo(tokenId, salePrice)` - Get royalty information
- `transferFrom(from, to, tokenId)` - Transfer NFT

#### ComplianceRegistry.sol
**Purpose**: Immutable legal document acceptance tracking

**Features**:
- Document version control with hashing
- Acceptance records linked to wallet addresses
- GDPR/CCPA deletion request tracking
- Immutable audit trail on blockchain

**Key Functions**:
- `registerDocumentVersion(docType, version, hash)` - Register document (owner)
- `recordAcceptance(docType, version, hash, ipAddress)` - Record acceptance
- `hasAccepted(wallet, docType, version)` - Check acceptance status
- `requestDeletion(requestType)` - Request data deletion

#### RewardVault.sol
**Purpose**: Decentralized reward distribution system

**Features**:
- Separate reward pools (sharing, listening, bandwidth, voting, referral)
- Claim verification by authorized verifiers
- Daily limits per user and pool
- Anti-gaming mechanisms

**Key Functions**:
- `submitClaim(rewardType, amount, proofHash)` - Submit reward claim
- `verifyClaim(claimId, approved)` - Verify claim (verifier only)
- `getPoolStatus(rewardType)` - Get pool status
- `addVerifier(address)` - Add authorized verifier (owner)

#### RoyaltyDistributor.sol
**Purpose**: Automatic artist royalty distribution

**Features**:
- NFT sale tracking with royalty calculation
- Automatic royalty splits for collaborations
- Payment processing in TRX or tokens
- Platform fee collection

**Key Functions**:
- `recordSale(tokenId, seller, buyer, salePrice, paymentToken)` - Record sale
- `payRoyalty(saleId)` - Execute royalty payment
- `setRoyaltySplits(tokenId, recipients, shares)` - Configure splits
- `totalRoyaltiesEarned(artist)` - Get artist earnings

## Data Flow Examples

### NFT Minting Flow

```
1. User calls mintMusic() on MusicNFT contract
   ↓
2. Transaction confirmed on TRON blockchain
   ↓
3. MusicMinted event emitted
   ↓
4. Event Indexer detects event
   ↓
5. Event parsed and stored in blockchain_events table
   ↓
6. NFT metadata indexed to nft_index table
   ↓
7. User profile updated (if needed)
   ↓
8. API queries return NFT from PostgreSQL
```

### Reward Claim Flow

```
1. User submits claim via submitClaim()
   ↓
2. Claim stored on-chain with proof hash
   ↓
3. Verifier calls verifyClaim(claimId, true)
   ↓
4. If approved, DCMXToken.mint() is called
   ↓
5. RewardClaimed event emitted
   ↓
6. Event indexed to reward_claims_index
   ↓
7. User balance updated in user_profiles
```

### Legal Acceptance Flow

```
1. User accepts document via ComplianceRegistry
   ↓
2. recordAcceptance() writes hash to blockchain
   ↓
3. AcceptanceRecorded event emitted
   ↓
4. Event indexed to compliance_index
   ↓
5. API can query acceptance status instantly
```

## Deployment

### Prerequisites
- PostgreSQL 13+ database
- TRON wallet with TRX for gas fees
- Python 3.8+ environment

### Setup Steps

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
# TRON Configuration
export TRON_NETWORK=shasta  # or mainnet
export TRON_PRIVATE_KEY=your_private_key
export TRONGRID_API_KEY=your_api_key

# Database Configuration
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=dcmx
export DB_USER=dcmx
export DB_PASSWORD=secure_password
```

3. **Deploy Smart Contracts**
```bash
python scripts/deploy_contracts.py
```

4. **Initialize Database**
```bash
python scripts/initialize_db.py
```

5. **Start Event Indexer**
```bash
python scripts/start_indexer.py --poll-interval 30
```

## Monitoring

### Key Metrics

- **Blockchain**: Block height, transaction count, event count
- **Database**: Index lag, query performance, table sizes
- **Indexer**: Sync speed, error rate, uptime

### Health Checks

```python
from dcmx.tron.client import TronClient
from dcmx.database.database import test_connection

# Check TRON connection
client = TronClient()
is_connected = client.is_connected()

# Check database connection
db_healthy = test_connection()
```

## Security Considerations

1. **Private Key Management**
   - Never commit private keys to git
   - Use environment variables or key vaults
   - Rotate keys periodically

2. **Database Security**
   - Use encrypted connections (SSL)
   - Implement role-based access control
   - Regular backups with encryption

3. **Smart Contract Security**
   - Audited before mainnet deployment
   - Multi-sig for admin functions
   - Pausable contracts for emergency stops

4. **API Security**
   - Rate limiting on endpoints
   - Authentication for write operations
   - Input validation and sanitization

## Performance Optimization

### Blockchain Queries
- Cache frequently accessed data
- Use batch queries when possible
- Implement query result pagination

### Database Optimization
- Proper indexing on query columns
- Materialized views for complex analytics
- Query optimization and EXPLAIN analysis
- Connection pooling (10-20 connections)

### Event Indexing
- Batch event processing (100-200 per batch)
- Parallel processing for multiple contracts
- Checkpoint-based resumption after failures

## Troubleshooting

### Common Issues

**Event Indexer Not Syncing**
- Check TRON connection: `client.is_connected()`
- Verify contract addresses are set
- Check database connection
- Review indexer logs for errors

**Missing Events**
- Check block range in sync_events()
- Verify event_server URL is correct
- Check for chain reorganizations
- Re-sync from specific block if needed

**Slow Queries**
- Analyze with EXPLAIN
- Add missing indexes
- Use query helpers from queries.py
- Consider materialized views

## Future Enhancements

1. **Layer 2 Scaling**: Integrate with TRON Layer 2 solutions
2. **IPFS Integration**: Decentralized metadata storage
3. **GraphQL API**: More flexible queries
4. **Real-time Updates**: WebSocket subscriptions for live events
5. **Cross-chain Bridge**: Support other blockchains (Ethereum, Polygon)
6. **ZK Proofs**: Privacy-preserving reward claims
