# DCMX Database Schema Documentation

## Overview

The DCMX database schema provides persistent storage for all platform operations, replacing file-based and in-memory storage with a robust PostgreSQL/SQLite backend.

## Database Configuration

### Environment Variables

```bash
# PostgreSQL Configuration
export DCMX_DB_HOST=localhost
export DCMX_DB_PORT=5432
export DCMX_DB_NAME=dcmx
export DCMX_DB_USER=dcmx_app
export DCMX_DB_PASSWORD=dcmx_password

# Connection Pool Settings
export DCMX_DB_POOL_SIZE=10
export DCMX_DB_MAX_OVERFLOW=20
export DCMX_DB_POOL_TIMEOUT=30
export DCMX_DB_POOL_RECYCLE=3600

# SQLite Fallback (Development)
export DCMX_DB_USE_SQLITE=true
export DCMX_DB_SQLITE_PATH=dcmx.db

# API Server Database Mode
export DCMX_USE_DATABASE=true
```

## Schema Overview

### Table Categories

1. **Legal Compliance** (3 tables)
2. **Wallets & Users** (4 tables)
3. **NFTs & Assets** (4 tables)
4. **Rewards & Economics** (6 tables)
5. **Transactions & Activity** (4 tables)
6. **Settings & Configuration** (3 tables)

**Total: 24 tables**

---

## Legal Compliance Tables

### acceptance_records

Stores legal document acceptance records (replaces JSONL file storage).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | VARCHAR(255) | User identifier (indexed) |
| wallet_address | VARCHAR(42) | Ethereum wallet address (indexed) |
| document_type | VARCHAR(50) | Document type (terms_and_conditions, privacy_policy, etc.) |
| version | VARCHAR(20) | Document version |
| accepted_at | TIMESTAMP | Acceptance timestamp (indexed) |
| ip_address | VARCHAR(45) | User's IP address (IPv4/IPv6) |
| user_agent | TEXT | Browser user agent |
| signature | VARCHAR(132) | Blockchain signature proof |
| read_time_seconds | INTEGER | Time spent reading document |
| document_hash | VARCHAR(64) | SHA-256 hash of document content |
| created_at | TIMESTAMP | Record creation timestamp |

**Indexes:**
- `idx_acceptance_user_doc (user_id, document_type)`
- `idx_acceptance_wallet (wallet_address)`
- `idx_acceptance_date (accepted_at)`

**Use Case:** Track GDPR/CCPA compliance, document version acceptance, audit trail

---

### audit_events

Compliance audit events for all platform activities.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| event_id | VARCHAR(255) | Unique event identifier (indexed, unique) |
| event_type | VARCHAR(100) | Event type (login, transaction, kyc_approved, etc.) |
| timestamp | TIMESTAMP | Event timestamp (indexed) |
| user_id | VARCHAR(255) | Actor user ID (indexed) |
| username | VARCHAR(255) | Actor username |
| wallet_address | VARCHAR(42) | Actor wallet (indexed) |
| resource_type | VARCHAR(100) | Resource affected |
| resource_id | VARCHAR(255) | Resource ID |
| action | VARCHAR(255) | Action performed |
| status | VARCHAR(20) | Status (success, failure, pending) (indexed) |
| result | TEXT | Result description |
| amount | FLOAT | Transaction amount (if applicable) |
| currency | VARCHAR(10) | Currency (default: DCMX) |
| jurisdiction | VARCHAR(10) | Legal jurisdiction (US, EU, etc.) |
| kyc_level | INTEGER | KYC verification level |
| risk_score | FLOAT | Risk assessment score |
| ip_address | VARCHAR(45) | IP address |
| user_agent | TEXT | User agent |
| session_id | VARCHAR(255) | Session identifier |
| details | JSON | Additional event details |
| error_message | TEXT | Error message (if failure) |
| hash | VARCHAR(64) | SHA-256 event hash (integrity) |
| parent_hash | VARCHAR(64) | Previous event hash (blockchain-style chaining) |
| created_at | TIMESTAMP | Record creation |

**Indexes:**
- `idx_audit_user_time (user_id, timestamp)`
- `idx_audit_type_status (event_type, status)`

**Use Case:** Government compliance (SEC, FinCEN), security audits, forensic analysis

---

### data_deletion_requests

GDPR/CCPA data deletion request tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | VARCHAR(255) | User requesting deletion (indexed) |
| wallet_address | VARCHAR(42) | Wallet address |
| request_type | VARCHAR(20) | Request type (gdpr, ccpa) |
| requested_at | TIMESTAMP | Request timestamp |
| deadline | TIMESTAMP | Legal deadline (30 days) |
| completed_at | TIMESTAMP | Completion timestamp |
| status | VARCHAR(20) | Status (pending, processing, completed, cancelled) (indexed) |
| completion_summary | TEXT | Summary of actions taken |
| requested_by | VARCHAR(255) | Email or admin ID |
| notes | TEXT | Additional notes |

**Indexes:**
- `idx_deletion_status_deadline (status, deadline)`

**Use Case:** GDPR Article 17 (Right to Erasure), CCPA compliance

---

## Wallets & Users Tables

### wallets

User wallet addresses and token balances.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| address | VARCHAR(42) | Ethereum wallet address (unique, indexed) |
| username | VARCHAR(255) | Display username (indexed) |
| balance_dcmx | DECIMAL(36,18) | DCMX token balance (high precision) |
| is_artist | BOOLEAN | Artist flag (indexed) |
| is_verified | BOOLEAN | Verification status |
| is_active | BOOLEAN | Active status (indexed) |
| created_at | TIMESTAMP | Account creation |
| last_activity | TIMESTAMP | Last activity timestamp |

**Relationships:**
- One-to-many with `music_nfts` (artist's NFTs)
- One-to-many with `reward_claims` (user's rewards)
- One-to-many with `transactions` (sent/received)

**Use Case:** Wallet management, balance tracking, artist identification

---

### users

Extended user profiles with KYC information.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | VARCHAR(255) | Unique user identifier (indexed, unique) |
| wallet_id | UUID | Foreign key to wallets table |
| email | VARCHAR(255) | Email address (unique, indexed) |
| username | VARCHAR(255) | Username (unique, indexed) |
| display_name | VARCHAR(255) | Display name |
| bio | TEXT | User biography |
| avatar_url | VARCHAR(512) | Avatar image URL |
| kyc_status | VARCHAR(20) | KYC status (unverified, pending, verified, rejected) (indexed) |
| kyc_level | INTEGER | KYC level (0=none, 1=basic, 2=enhanced) |
| kyc_verified_at | TIMESTAMP | KYC verification timestamp |
| preferences | JSON | User preferences |
| created_at | TIMESTAMP | Account creation |
| updated_at | TIMESTAMP | Last update |
| last_login | TIMESTAMP | Last login timestamp |

**Relationships:**
- Many-to-one with `wallets`
- One-to-many with `user_roles`
- One-to-many with `user_sessions`

**Use Case:** User profiles, KYC compliance, authentication

---

### user_roles

Role-based access control.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users table |
| role_name | VARCHAR(50) | Role (admin, artist, moderator, user) |
| granted_at | TIMESTAMP | Role grant timestamp |
| granted_by | UUID | Admin who granted role |

**Unique Constraint:** `(user_id, role_name)`

**Indexes:**
- `idx_user_role (user_id, role_name)`

**Use Case:** Admin access control, feature permissions

---

### user_sessions

Authentication session tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to users table (indexed) |
| session_token | VARCHAR(255) | Session token (unique, indexed) |
| ip_address | VARCHAR(45) | Login IP address |
| user_agent | TEXT | Browser user agent |
| created_at | TIMESTAMP | Session creation |
| expires_at | TIMESTAMP | Session expiration |
| last_activity | TIMESTAMP | Last activity timestamp |

**Use Case:** Authentication, session management, security tracking

---

## NFTs & Assets Tables

### nft_certificates

NFT certificates for songs (blockchain integration).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| content_hash | VARCHAR(64) | DCMX content hash (SHA-256, unique, indexed) |
| song_title | VARCHAR(255) | Song title |
| artist_wallet | VARCHAR(42) | Artist wallet address (indexed) |
| edition_number | INTEGER | Edition number (1, 2, 3, ...) |
| max_editions | INTEGER | Total editions available |
| price_dcmx | DECIMAL(36,18) | NFT price in DCMX tokens |
| price_usd_equivalent | DECIMAL(18,2) | USD equivalent price |
| watermark_hash | VARCHAR(64) | Audio watermark hash |
| perceptual_fingerprint | VARCHAR(64) | Perceptual audio fingerprint |
| watermark_proof_chain_id | VARCHAR(255) | ZK proof chain ID |
| nft_contract_address | VARCHAR(42) | Blockchain contract address |
| token_id | BIGINT | NFT token ID |
| transaction_hash | VARCHAR(66) | Minting transaction hash |
| blockchain | VARCHAR(20) | Blockchain (polygon, ethereum, etc.) |
| mint_status | VARCHAR(20) | Status (pending, confirmed, failed) |
| created_at | TIMESTAMP | Certificate creation |
| minted_at | TIMESTAMP | Blockchain minting timestamp |

**Constraints:**
- `CHECK (edition_number <= max_editions)`

**Indexes:**
- `idx_nft_cert_artist (artist_wallet, created_at)`

**Use Case:** NFT minting, edition tracking, watermark verification

---

### music_nfts

Music NFT metadata and ownership records.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| nft_id | VARCHAR(64) | Unique NFT identifier (unique, indexed) |
| certificate_id | UUID | Foreign key to nft_certificates |
| title | VARCHAR(255) | Song title (indexed) |
| artist | VARCHAR(255) | Artist name |
| artist_wallet | VARCHAR(42) | Artist wallet (foreign key to wallets) |
| artist_username | VARCHAR(255) | Artist username |
| edition | INTEGER | Edition number |
| max_editions | INTEGER | Total editions |
| price_dcmx | DECIMAL(36,18) | Price in DCMX |
| content_hash | VARCHAR(64) | Content hash |
| likes | INTEGER | Like count |
| dislikes | INTEGER | Dislike count |
| listeners | INTEGER | Listener count |
| engagement_metrics | JSON | Engagement data (average_completion, total_listens, skip_count) |
| created_at | TIMESTAMP | Record creation |

**Relationships:**
- Many-to-one with `nft_certificates`
- Many-to-one with `wallets` (artist)
- One-to-many with `nft_sales`
- One-to-many with `nft_royalties`

**Use Case:** NFT catalog, engagement tracking, artist analytics

---

### nft_sales

NFT transaction history.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| nft_id | UUID | Foreign key to music_nfts (indexed) |
| sale_type | VARCHAR(20) | Sale type (primary, secondary) |
| seller_wallet | VARCHAR(42) | Seller address |
| buyer_wallet | VARCHAR(42) | Buyer address (indexed) |
| price_dcmx | DECIMAL(36,18) | Sale price in DCMX |
| price_usd_equivalent | DECIMAL(18,2) | USD equivalent |
| transaction_hash | VARCHAR(66) | Blockchain transaction hash |
| blockchain | VARCHAR(20) | Blockchain |
| sale_date | TIMESTAMP | Sale timestamp (indexed) |

**Use Case:** Sales history, revenue tracking, market analytics

---

### nft_royalties

Royalty distribution from NFT sales.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| nft_id | UUID | Foreign key to music_nfts (indexed) |
| sale_id | UUID | Foreign key to nft_sales |
| artist_wallet | VARCHAR(42) | Royalty recipient (indexed) |
| royalty_type | VARCHAR(20) | Type (primary_sale, secondary_sale) |
| royalty_percentage | FLOAT | Royalty percentage |
| royalty_amount_dcmx | DECIMAL(36,18) | Royalty amount |
| payment_status | VARCHAR(20) | Status (pending, completed, failed) |
| earned_at | TIMESTAMP | Earning timestamp |
| paid_at | TIMESTAMP | Payment timestamp |

**Use Case:** Artist royalty payments, revenue distribution

---

## Rewards & Economics Tables

### reward_claims

User reward claims with ZK proof verification.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| claim_id | VARCHAR(255) | Unique claim ID (unique, indexed) |
| user_wallet | VARCHAR(42) | User wallet (foreign key, indexed) |
| reward_type | VARCHAR(50) | Type (sharing, listening, voting, bandwidth) (indexed) |
| amount_dcmx | DECIMAL(36,18) | Reward amount |
| zk_proof_verified | BOOLEAN | ZK proof verification status |
| zk_proof_data | JSON | ZK proof data |
| claim_status | VARCHAR(20) | Status (pending, verified, claimed, rejected) (indexed) |
| created_at | TIMESTAMP | Claim creation |
| verified_at | TIMESTAMP | Verification timestamp |
| claimed_at | TIMESTAMP | Claim timestamp |

**Use Case:** Reward distribution, ZK proof verification, claim tracking

---

### sharing_rewards

Rewards for file sharing.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_wallet | VARCHAR(42) | Sharer wallet (indexed) |
| song_content_hash | VARCHAR(64) | Song hash |
| shared_with_wallet | VARCHAR(42) | Recipient wallet |
| base_reward | DECIMAL(36,18) | Base reward amount |
| bonus_reward | DECIMAL(36,18) | Bonus reward |
| total_reward | DECIMAL(36,18) | Total reward |
| recipient_listened | BOOLEAN | Recipient listened flag |
| recipient_purchased | BOOLEAN | Recipient purchased flag |
| shared_at | TIMESTAMP | Sharing timestamp |
| reward_claimed | BOOLEAN | Claim status |

**Indexes:**
- `idx_sharing_user_date (user_wallet, shared_at)`

**Use Case:** Viral marketing rewards, referral tracking

---

### listening_rewards

Rewards for listening activity.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_wallet | VARCHAR(42) | Listener wallet (indexed) |
| nft_id | VARCHAR(64) | NFT ID (indexed) |
| listen_duration_seconds | INTEGER | Listen duration |
| completion_percentage | FLOAT | Completion percentage |
| base_reward | DECIMAL(36,18) | Base reward |
| completion_bonus | DECIMAL(36,18) | Completion bonus |
| total_reward | DECIMAL(36,18) | Total reward |
| listened_at | TIMESTAMP | Listen timestamp (indexed) |
| reward_claimed | BOOLEAN | Claim status |

**Use Case:** Listener engagement rewards

---

### bandwidth_rewards

Rewards for bandwidth contribution (LoRa nodes).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| node_wallet | VARCHAR(42) | Node wallet (indexed) |
| bytes_uploaded | BIGINT | Bytes uploaded |
| bytes_downloaded | BIGINT | Bytes downloaded |
| uptime_seconds | INTEGER | Node uptime |
| unique_peers_served | INTEGER | Unique peer count |
| base_reward | DECIMAL(36,18) | Base reward |
| bandwidth_bonus | DECIMAL(36,18) | Bandwidth bonus |
| uptime_bonus | DECIMAL(36,18) | Uptime bonus |
| total_reward | DECIMAL(36,18) | Total reward |
| period_start | TIMESTAMP | Period start |
| period_end | TIMESTAMP | Period end |
| calculated_at | TIMESTAMP | Calculation timestamp |
| reward_claimed | BOOLEAN | Claim status |

**Indexes:**
- `idx_bandwidth_node_period (node_wallet, period_start, period_end)`

**Use Case:** Node operator rewards, network incentives

---

### royalty_payments

Artist royalty payment tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| payment_id | VARCHAR(255) | Unique payment ID (unique, indexed) |
| artist_wallet | VARCHAR(42) | Artist wallet (indexed) |
| payment_type | VARCHAR(50) | Type (nft_sale, streaming, licensing) |
| amount_dcmx | DECIMAL(36,18) | Payment amount |
| amount_usd_equivalent | DECIMAL(18,2) | USD equivalent |
| source_transaction_id | VARCHAR(255) | Source transaction |
| source_nft_id | UUID | Source NFT (foreign key) |
| payment_status | VARCHAR(20) | Status (pending, completed, failed) (indexed) |
| earned_at | TIMESTAMP | Earning timestamp |
| paid_at | TIMESTAMP | Payment timestamp |

**Use Case:** Artist payment tracking, revenue reporting

---

### revenue_pools

Revenue distribution pools.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| pool_name | VARCHAR(100) | Pool name (unique, indexed) |
| pool_type | VARCHAR(50) | Type (artist, platform, community) |
| balance_dcmx | DECIMAL(36,18) | Pool balance |
| distribution_rules | JSON | Distribution rule configuration |
| created_at | TIMESTAMP | Pool creation |
| last_distribution | TIMESTAMP | Last distribution timestamp |

**Use Case:** Platform economics, revenue sharing

---

## Transactions & Activity Tables

### transactions

All platform transactions.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| transaction_id | VARCHAR(255) | Unique transaction ID (unique, indexed) |
| from_wallet | VARCHAR(42) | Sender wallet (foreign key, indexed) |
| to_wallet | VARCHAR(42) | Recipient wallet (foreign key, indexed) |
| transaction_type | VARCHAR(50) | Type (transfer, nft_purchase, reward_claim) (indexed) |
| amount_dcmx | DECIMAL(36,18) | Transaction amount |
| status | VARCHAR(20) | Status (pending, completed, failed) (indexed) |
| blockchain_hash | VARCHAR(66) | Blockchain hash (indexed) |
| blockchain | VARCHAR(20) | Blockchain |
| metadata | JSON | Additional metadata |
| created_at | TIMESTAMP | Transaction creation (indexed) |
| completed_at | TIMESTAMP | Completion timestamp |

**Relationships:**
- Many-to-one with `wallets` (from_wallet)
- Many-to-one with `wallets` (to_wallet)

**Use Case:** Transaction history, balance updates, audit trail

---

### voting_records

User voting on songs (like/dislike).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_wallet | VARCHAR(42) | Voter wallet (indexed) |
| nft_id | VARCHAR(64) | NFT ID (indexed) |
| preference | VARCHAR(20) | Preference (like, dislike) |
| reward_tokens | DECIMAL(36,18) | Reward tokens earned |
| voted_at | TIMESTAMP | Vote timestamp (indexed) |

**Indexes:**
- `idx_vote_user_nft (user_wallet, nft_id, voted_at)`

**Use Case:** Song sentiment analysis, user preferences, engagement rewards

---

### skip_records

Skip activity tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_wallet | VARCHAR(42) | User wallet (indexed) |
| nft_id | VARCHAR(64) | NFT ID (indexed) |
| completion_percentage | FLOAT | Listen completion percentage |
| charge_applied | DECIMAL(36,18) | Skip charge (negative value) |
| skipped_at | TIMESTAMP | Skip timestamp (indexed) |

**Indexes:**
- `idx_skip_user_nft (user_wallet, nft_id, skipped_at)`

**Use Case:** Engagement analysis, skip charge enforcement

---

### blockchain_transactions

Blockchain transaction history.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| transaction_hash | VARCHAR(66) | Blockchain hash (unique, indexed) |
| blockchain | VARCHAR(20) | Blockchain network |
| block_number | BIGINT | Block number (indexed) |
| block_timestamp | TIMESTAMP | Block timestamp (indexed) |
| from_address | VARCHAR(42) | From address (indexed) |
| to_address | VARCHAR(42) | To address (indexed) |
| value_wei | DECIMAL(78,0) | Transaction value in wei |
| gas_used | BIGINT | Gas used |
| gas_price_wei | DECIMAL(78,0) | Gas price in wei |
| is_confirmed | BOOLEAN | Confirmation status (indexed) |
| confirmations | INTEGER | Confirmation count |
| contract_address | VARCHAR(42) | Contract address (if contract interaction) |
| input_data | TEXT | Transaction input data |
| transaction_type | VARCHAR(50) | Type (transfer, mint, approve, etc.) |
| metadata | JSON | Additional metadata |
| platform_transaction_id | UUID | Foreign key to transactions |
| created_at | TIMESTAMP | Record creation |

**Use Case:** Blockchain synchronization, transaction verification

---

## Settings & Configuration Tables

### system_configuration

Platform configuration settings.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| config_key | VARCHAR(100) | Configuration key (unique, indexed) |
| config_value | JSON | Configuration value |
| config_type | VARCHAR(50) | Type (string, number, boolean, json) |
| description | TEXT | Configuration description |
| is_public | BOOLEAN | Public visibility flag |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| updated_by | UUID | Admin user who updated (foreign key) |

**Default Configurations:**
- `platform_name: "DCMX"`
- `artist_primary_royalty_percentage: 100.0`
- `artist_secondary_royalty_percentage: 5.0`
- `skip_charge_threshold: 0.25`
- `voting_reward_tokens: 5.0`
- `listening_base_reward: 1.0`

**Use Case:** Platform configuration, feature flags

---

### admin_actions

Admin action audit log.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| admin_id | UUID | Admin user ID (foreign key, indexed) |
| action_type | VARCHAR(100) | Action type (indexed) |
| target_type | VARCHAR(50) | Target resource type |
| target_id | VARCHAR(255) | Target resource ID |
| description | TEXT | Action description |
| parameters | JSON | Action parameters |
| result | TEXT | Action result |
| performed_at | TIMESTAMP | Action timestamp (indexed) |

**Use Case:** Admin accountability, security audit

---

### multisig_proposals

Multisig wallet proposals.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| proposal_id | VARCHAR(255) | Unique proposal ID (unique, indexed) |
| proposal_type | VARCHAR(50) | Type (transfer, config_change, admin_action) |
| description | TEXT | Proposal description |
| target_wallet | VARCHAR(42) | Target wallet |
| amount_dcmx | DECIMAL(36,18) | Amount (if transfer) |
| required_signatures | INTEGER | Required signature count |
| current_signatures | INTEGER | Current signature count |
| signers | ARRAY(VARCHAR(42)) | Array of signer wallet addresses |
| status | VARCHAR(20) | Status (pending, approved, rejected, executed) (indexed) |
| created_at | TIMESTAMP | Creation timestamp |
| expires_at | TIMESTAMP | Expiration timestamp |
| executed_at | TIMESTAMP | Execution timestamp |
| execution_hash | VARCHAR(66) | Execution transaction hash |

**Indexes:**
- `idx_proposal_status_expiry (status, expires_at)`

**Use Case:** Multisig governance, treasury management

---

## Database Initialization

### Using Scripts

```bash
# Initialize database (PostgreSQL)
python scripts/init_database.py

# Initialize with SQLite (development)
python scripts/init_database.py --sqlite

# Drop and recreate (DANGER!)
python scripts/init_database.py --drop

# Verify database
python scripts/init_database.py --verify

# Check status
python scripts/init_database.py --status
```

### Using Python

```python
from dcmx.database.migrations import initialize_database

# Initialize
initialize_database()

# Drop and recreate (DANGER!)
initialize_database(drop_existing=True)
```

### Using Async

```python
import asyncio
from dcmx.database.migrations import initialize_database_async

asyncio.run(initialize_database_async())
```

---

## Data Migration

Migrate legacy data from JSONL files and SQLite:

```bash
# Dry run (preview changes)
python scripts/migrate_legacy_data.py --dry-run

# Migrate data
python scripts/migrate_legacy_data.py

# Specify source directory
python scripts/migrate_legacy_data.py --source-dir /path/to/legacy/data
```

---

## Query Examples

### Get User Profile with Stats

```python
from dcmx.database.database import get_db_manager
from dcmx.database.dal import DataAccessLayer

async with get_db_manager().get_async_session() as session:
    dal = DataAccessLayer()
    profile = await dal.get_user_profile_stats(session, "0x1234...")
    print(profile)
```

### Get Platform Statistics

```python
async with get_db_manager().get_async_session() as session:
    stats = await dal.get_platform_stats(session)
    print(f"Total Users: {stats['total_users']}")
    print(f"Total NFTs: {stats['total_nfts']}")
```

### Record Legal Acceptance

```python
from dcmx.legal.acceptance_db import AcceptanceTracker, DocumentType

tracker = AcceptanceTracker(use_database=True)
record = await tracker.record_acceptance(
    user_id="user123",
    wallet_address="0x1234...",
    document_type=DocumentType.TERMS_AND_CONDITIONS,
    version="1.0",
    ip_address="192.168.1.1"
)
```

---

## Performance Optimization

### Indexes

All tables have appropriate indexes for common query patterns:
- Primary keys (UUID)
- Foreign keys
- Frequently queried columns (user_id, wallet_address, timestamps)
- Composite indexes for multi-column queries

### Connection Pooling

Configured via environment variables:
- `DCMX_DB_POOL_SIZE`: Connection pool size (default: 10)
- `DCMX_DB_MAX_OVERFLOW`: Max overflow connections (default: 20)
- `DCMX_DB_POOL_RECYCLE`: Connection recycle time in seconds (default: 3600)

### Precision Types

High-precision types for financial data:
- `DECIMAL(36,18)` for DCMX token amounts
- `DECIMAL(78,0)` for blockchain wei values
- `DECIMAL(18,2)` for USD equivalents

---

## Backup and Recovery

### PostgreSQL Backup

```bash
# Backup
pg_dump -U dcmx_app dcmx > dcmx_backup.sql

# Restore
psql -U dcmx_app dcmx < dcmx_backup.sql
```

### SQLite Backup

```bash
# Backup
cp dcmx.db dcmx_backup.db

# Restore
cp dcmx_backup.db dcmx.db
```

---

## Security Considerations

1. **Sensitive Data**: User PII and KYC data should be encrypted at rest
2. **Access Control**: Use role-based permissions
3. **Audit Logging**: All sensitive operations logged to `audit_events`
4. **SQL Injection**: SQLAlchemy ORM protects against SQL injection
5. **Connection Security**: Use SSL/TLS for PostgreSQL connections

---

## Support

For database issues, check:
1. Connection configuration (`dcmx/database/config.py`)
2. Migration status (`python scripts/init_database.py --status`)
3. Logs (enable with `--verbose` flag)
4. Test connection: `python scripts/init_database.py --verify`
