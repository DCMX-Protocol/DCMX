# DCMX Web3 Architecture

## Overview

DCMX implements a complete Web3 architecture combining TRON blockchain smart contracts with PostgreSQL indexing for a production-grade decentralized music platform.

## Architecture Components

```
┌─────────────────────────────┐
│   Frontend / Mobile App     │
│   - Web3 Wallet Integration │
│   - NFT Marketplace         │
│   - Reward Dashboard        │
└────────────┬────────────────┘
             │
    ┌────────▼──────────┐
    │  FastAPI Server   │
    │  /api/v1/*        │
    │  - NFT Endpoints  │
    │  - Rewards API    │
    │  - Compliance API │
    └────────┬──────────┘
             │
    ┌────────▼──────────────┐
    │   TRON Client Layer   │
    │  - Contract Calls     │
    │  - Event Listening    │
    │  - Transaction Mgmt   │
    └────────┬──────────────┘
             │
  ┌──────────▼───────────────┐
  │   TRON BLOCKCHAIN        │
  ├──────────────────────────┤
  │ • DCMXToken (TRC-20)     │
  │ • MusicNFT (TRC-721)     │
  │ • ComplianceRegistry     │
  │ • RewardVault            │
  │ • RoyaltyDistributor     │
  └──────────┬───────────────┘
             │
  ┌──────────▼────────────────┐
  │ Event Indexer Daemon      │
  │  - Real-time event sync   │
  │  - Batch processing       │
  │  - Chain reorg handling   │
  └──────────┬────────────────┘
             │
  ┌──────────▼────────────────┐
  │  PostgreSQL Database      │
  ├──────────────────────────┤
  │ • blockchain_events       │
  │ • user_profiles           │
  │ • nft_index               │
  │ • reward_claims_index     │
  │ • transaction_index       │
  │ • compliance_index        │
  │ • analytics               │
  └───────────────────────────┘
```

## Key Design Principles

### 1. Blockchain as Source of Truth

All critical operations are recorded on the TRON blockchain:
- NFT ownership and transfers
- Token rewards distribution
- Legal compliance acceptances
- Royalty payments

This ensures:
- **Immutability**: Records cannot be altered
- **Transparency**: All transactions are publicly verifiable
- **Decentralization**: No single point of control
- **Trust**: Cryptographic verification of all operations

### 2. Database for Performance

PostgreSQL indexes blockchain data for efficient queries:
- Fast NFT searches by artist, genre, etc.
- User transaction history
- Analytics and trending
- Real-time dashboard updates

Benefits:
- **Speed**: Sub-second query response times
- **Flexibility**: Complex SQL queries for analytics
- **Scalability**: Handle millions of transactions
- **Cost**: Cheaper than blockchain queries

### 3. Event-Driven Synchronization

The indexer daemon continuously monitors blockchain events:
- Listens to smart contract events
- Indexes events to database in real-time
- Handles blockchain reorganizations
- Maintains data consistency

## Smart Contract Architecture

### DCMXToken (TRC-20)

**Purpose**: Utility token for platform operations

**Features**:
- Fixed supply: 1 billion tokens
- Mint/burn capabilities (admin only)
- Standard TRC-20 interface
- Used for rewards and platform fees

**Key Functions**:
- `transfer(to, amount)`: Transfer tokens
- `approve(spender, amount)`: Approve spending
- `mint(to, amount)`: Mint new tokens (admin)
- `burn(amount)`: Burn tokens

### MusicNFT (TRC-721)

**Purpose**: Represent music tracks as unique NFTs

**Features**:
- Limited edition support
- Built-in royalty tracking (ERC-2981 compatible)
- Content hash for integrity verification
- Edition numbering (e.g., "1 of 100")

**Key Functions**:
- `mint(...)`: Create new music NFT
- `transfer(to, tokenId)`: Transfer NFT
- `tokenMetadata(tokenId)`: Get NFT details
- `royaltyInfo(tokenId, salePrice)`: Calculate royalty

### ComplianceRegistry

**Purpose**: GDPR/CCPA compliance tracking

**Features**:
- Immutable acceptance records
- Document version management
- Data deletion requests
- Audit trail

**Key Functions**:
- `recordAcceptance(...)`: Record user acceptance
- `requestDataDeletion(reason)`: Request deletion
- `verifyAcceptance(...)`: Verify past acceptance
- `getAuditTrail(user)`: Get full audit history

### RewardVault

**Purpose**: Manage token reward distribution

**Features**:
- Three reward pools (Sharing, Listening, Bandwidth)
- Proof-based claim verification
- Automatic token minting
- Anti-fraud protection

**Key Functions**:
- `submitClaim(type, proof, amount)`: Submit claim
- `verifyClaim(claimId, approved)`: Verify claim (admin)
- `claimRewards(claimId)`: Claim tokens
- `getUserRewards(user)`: Get user's rewards

### RoyaltyDistributor

**Purpose**: Automate royalty payments

**Features**:
- Multi-recipient splits
- Automatic calculation
- Withdraw mechanism
- Sale tracking

**Key Functions**:
- `recordSale(...)`: Record NFT sale
- `distributeRoyalties(saleId)`: Distribute royalties
- `withdrawRoyalties()`: Withdraw pending royalties
- `getRoyaltyInfo(nftTokenId)`: Get royalty config

## Database Schema

### Core Tables

**blockchain_events**
- Indexes all smart contract events
- Used for audit and debugging
- Enables event replay

**user_profiles**
- User wallet addresses
- KYC verification status
- Privacy preferences

**nft_index**
- NFT metadata cache
- Owner tracking
- Fast artist/genre searches

**reward_claims_index**
- Reward claim history
- Status tracking
- User reward totals

**transaction_index**
- Transaction history
- Balance calculations
- Activity analytics

**compliance_index**
- Legal acceptance records
- Deletion requests
- Compliance audit logs

**analytics**
- Platform metrics
- User statistics
- Trending data

## Data Flow Examples

### Example 1: NFT Minting

1. Artist calls API: `POST /api/v1/nft/mint`
2. API validates request
3. Contract call: `MusicNFT.mint(...)`
4. Transaction broadcast to blockchain
5. Event emitted: `Minted(to, tokenId, contentHash)`
6. Indexer picks up event
7. NFT metadata saved to `nft_index` table
8. Event saved to `blockchain_events` table
9. API returns transaction hash to artist

### Example 2: Reward Claiming

1. User submits claim: `POST /api/v1/reward/claim`
2. API computes proof hash from data
3. Contract call: `RewardVault.submitClaim(...)`
4. Claim recorded on blockchain
5. Event emitted: `ClaimSubmitted(claimId, user, ...)`
6. Indexer saves claim to `reward_claims_index`
7. Admin verifies claim: `RewardVault.verifyClaim(claimId, true)`
8. User claims: `RewardVault.claimRewards(claimId)`
9. DCMX tokens minted to user
10. Event indexed: `RewardsClaimed(claimId, user, amount)`

### Example 3: Compliance Acceptance

1. User accepts terms: `POST /api/legal/accept`
2. Document hash computed
3. Contract call: `ComplianceRegistry.recordAcceptance(...)`
4. Acceptance recorded immutably on blockchain
5. Event emitted: `AcceptanceRecorded(user, docType, ...)`
6. Indexer saves to `compliance_index`
7. Acceptance can be verified anytime via blockchain

## Performance Optimizations

### 1. Read from Database, Write to Blockchain

**Pattern**: Query indexed data for reads, use blockchain for writes

```python
# Fast read from database
nfts = session.query(NFTIndex).filter(artist="ArtistName").all()

# Write to blockchain
result = nft_contract.mint(...)
```

### 2. Batch Event Processing

**Pattern**: Process multiple blocks in batches

```python
# Efficient batch processing
for block_num in range(start_block, end_block, batch_size):
    events = get_events_batch(block_num, batch_size)
    save_to_database(events)
```

### 3. Caching Hot Data

**Pattern**: Cache frequently accessed data in Redis

```python
# Cache NFT metadata
redis.setex(f"nft:{token_id}", 3600, nft_metadata)
```

### 4. Connection Pooling

**Pattern**: Reuse database connections

```python
# SQLAlchemy connection pool
engine = create_engine(
    database_url,
    pool_size=10,
    max_overflow=20
)
```

## Security Considerations

### 1. Private Key Management

- **Never** commit private keys to code
- Use environment variables or secure vaults
- Rotate keys periodically
- Use different keys for testnet and mainnet

### 2. Input Validation

- Validate all API inputs
- Sanitize user data
- Check TRON address format
- Verify proof hashes

### 3. Rate Limiting

- Limit API requests per user
- Throttle contract calls
- Prevent spam attacks

### 4. Access Control

- Admin-only functions protected
- Wallet signature verification
- Role-based permissions

### 5. Contract Audits

- Audit contracts before mainnet deployment
- Use established security firms
- Bug bounty program
- Regular security reviews

## Monitoring & Observability

### Metrics to Track

1. **Blockchain Metrics**
   - Transaction success rate
   - Average gas costs
   - Block confirmation times
   - Event indexing lag

2. **Database Metrics**
   - Query performance
   - Index efficiency
   - Connection pool usage
   - Storage growth

3. **API Metrics**
   - Request latency
   - Error rates
   - Active users
   - Peak traffic times

4. **Business Metrics**
   - NFTs minted
   - Rewards distributed
   - Active wallets
   - Transaction volume

### Logging Strategy

```python
# Structured logging
logger.info(
    "NFT minted",
    extra={
        "token_id": token_id,
        "artist": artist,
        "tx_hash": tx_hash,
        "gas_used": gas_used
    }
)
```

## Deployment Checklist

### Testnet Deployment (Shasta)

- [ ] Deploy smart contracts
- [ ] Verify contracts on TronScan
- [ ] Initialize database
- [ ] Start indexer daemon
- [ ] Test API endpoints
- [ ] Validate event indexing
- [ ] Perform load testing

### Mainnet Deployment

- [ ] Complete security audit
- [ ] Review all configurations
- [ ] Setup monitoring/alerts
- [ ] Deploy contracts to mainnet
- [ ] Migrate historical data
- [ ] Start indexer with correct start block
- [ ] Monitor for first 24 hours
- [ ] Announce to users

## Disaster Recovery

### Blockchain Failures

- Blockchain data is immutable and replicated
- Can re-sync from any block
- Multiple RPC endpoints for redundancy

### Database Failures

- Regular backups (hourly/daily)
- Point-in-time recovery
- Can rebuild from blockchain events
- Multi-region replication

### Indexer Failures

- Automatically resumes from last block
- Handles chain reorganizations
- Can replay events if needed
- Health checks and auto-restart

## Future Enhancements

1. **Multi-chain Support**
   - Add Ethereum, Polygon, BNB Chain
   - Cross-chain NFT bridges

2. **Layer 2 Scaling**
   - Use TRON DAppChain for high frequency operations
   - Reduce transaction costs

3. **Advanced Analytics**
   - Machine learning for recommendations
   - Price prediction models
   - Fraud detection

4. **Mobile SDKs**
   - Native iOS/Android libraries
   - In-app wallet integration
   - Push notifications for events

## Resources

- **TRON Documentation**: https://developers.tron.network/
- **TronPy Library**: https://tronpy.readthedocs.io/
- **Smart Contract Standards**: See docs/SMART_CONTRACTS.md
- **API Documentation**: See docs/BLOCKCHAIN_INTEGRATION.md
- **Event Indexing**: See docs/EVENT_INDEXING.md
