# DCMX Smart Contracts Reference

## Overview

DCMX uses five core smart contracts deployed on TRON blockchain to manage tokens, NFTs, compliance, rewards, and royalties.

## Contract Addresses

### Shasta Testnet
```
DCMXToken: [PENDING DEPLOYMENT]
MusicNFT: [PENDING DEPLOYMENT]
ComplianceRegistry: [PENDING DEPLOYMENT]
RewardVault: [PENDING DEPLOYMENT]
RoyaltyDistributor: [PENDING DEPLOYMENT]
```

### Mainnet
```
[TO BE DEPLOYED]
```

## Contract Specifications

### 1. DCMXToken (TRC-20)

**File**: `dcmx/tron/contracts/DCMXToken.sol`

**Purpose**: Platform utility token for rewards, governance, and platform fees.

#### Constructor Parameters
- `initialSupply` (uint256): Initial token supply (can be 0)
- `maxSupply` (uint256): Maximum supply cap

#### State Variables
```solidity
string public constant name = "DCMX Token";
string public constant symbol = "DCMX";
uint8 public constant decimals = 18;
uint256 public totalSupply;
uint256 public maxSupply;
address public owner;
mapping(address => bool) public minters;  // Authorized minters
```

#### Key Functions

**Standard TRC-20**
```solidity
function transfer(address to, uint256 value) public returns (bool)
function approve(address spender, uint256 value) public returns (bool)
function transferFrom(address from, address to, uint256 value) public returns (bool)
function balanceOf(address account) public view returns (uint256)
function allowance(address owner, address spender) public view returns (uint256)
```

**Minting & Burning**
```solidity
// Mint new tokens (minters only)
function mint(address to, uint256 amount) external onlyMinter returns (bool)

// Burn tokens from caller
function burn(uint256 amount) external returns (bool)
```

**Access Control**
```solidity
// Add authorized minter (owner only)
function addMinter(address minter) external onlyOwner

// Remove authorized minter (owner only)
function removeMinter(address minter) external onlyOwner
```

#### Events
```solidity
event Transfer(address indexed from, address indexed to, uint256 value);
event Approval(address indexed owner, address indexed spender, uint256 value);
event Mint(address indexed to, uint256 amount);
event Burn(address indexed from, uint256 amount);
event MinterAdded(address indexed minter);
event MinterRemoved(address indexed minter);
```

#### Usage Example
```python
from dcmx.tron.contracts import DCMXTokenContract

# Initialize contract
token = DCMXTokenContract(client, contract_address)

# Check balance
balance = token.balance_of(wallet_address)
print(f"Balance: {balance / 10**18} DCMX")

# Transfer tokens
tx_hash = token.transfer(to_address, 100 * 10**18)  # 100 DCMX

# Mint tokens (authorized minter only)
tx_hash = token.mint(recipient, 1000 * 10**18)
```

---

### 2. MusicNFT (TRC-721)

**File**: `dcmx/tron/contracts/MusicNFT.sol`

**Purpose**: Music rights NFTs with edition tracking and royalties.

#### Constructor Parameters
- `baseURI` (string): Base URI for metadata (e.g., "https://ipfs.io/ipfs/")

#### Metadata Structure
```solidity
struct MusicMetadata {
    string title;
    string artist;
    string contentHash;      // SHA-256 of audio file
    uint256 editionNumber;   // 1-based edition number
    uint256 maxEditions;     // Total editions
    address artistWallet;    // Original artist
    uint96 royaltyBps;       // Royalty in basis points (1000 = 10%)
    uint256 mintedAt;        // Mint timestamp
}
```

#### Key Functions

**Minting**
```solidity
function mintMusic(
    address to,
    string memory title,
    string memory artist,
    string memory contentHash,
    uint256 editionNumber,
    uint256 maxEditions,
    uint96 royaltyBps
) external returns (uint256)  // Returns token ID
```

**Metadata**
```solidity
function getMetadata(uint256 tokenId) external view returns (
    string memory title,
    string memory artist,
    string memory contentHash,
    uint256 editionNumber,
    uint256 maxEditions,
    address artistWallet
)

function tokenURI(uint256 tokenId) external view returns (string memory)
```

**Standard TRC-721**
```solidity
function balanceOf(address owner) external view returns (uint256)
function ownerOf(uint256 tokenId) public view returns (address)
function transferFrom(address from, address to, uint256 tokenId) public
function approve(address to, uint256 tokenId) external
function setApprovalForAll(address operator, bool approved) external
```

**Royalties (ERC-2981)**
```solidity
function royaltyInfo(uint256 tokenId, uint256 salePrice) external view returns (
    address receiver,    // Royalty recipient
    uint256 royaltyAmount  // Amount in sale currency
)
```

#### Events
```solidity
event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
event MusicMinted(
    uint256 indexed tokenId,
    address indexed artist,
    string title,
    string contentHash,
    uint256 editionNumber,
    uint256 maxEditions
);
```

#### Usage Example
```python
from dcmx.tron.contracts import MusicNFTContract

# Initialize contract
nft = MusicNFTContract(client, contract_address)

# Mint music NFT
tx_hash = nft.mint_music(
    to_address=artist_wallet,
    title="My Song",
    artist="Artist Name",
    content_hash="a1b2c3d4...",  # SHA-256 of audio
    edition_number=1,
    max_editions=100,
    royalty_bps=1000  # 10% royalty
)

# Get metadata
metadata = nft.get_metadata(token_id)
print(f"Title: {metadata['title']}")
print(f"Edition: {metadata['edition_number']}/{metadata['max_editions']}")

# Get royalty info for sale
recipient, amount = nft.royalty_info(token_id, sale_price=1000)
print(f"Royalty: {amount} to {recipient}")
```

---

### 3. ComplianceRegistry

**File**: `dcmx/tron/contracts/ComplianceRegistry.sol`

**Purpose**: Immutable legal document acceptance tracking on blockchain.

#### Document Types
```solidity
enum DocumentType {
    TERMS_AND_CONDITIONS,    // 0
    PRIVACY_POLICY,          // 1
    COOKIE_POLICY,           // 2
    NFT_AGREEMENT,           // 3
    RISK_DISCLOSURE          // 4
}
```

#### Acceptance Record Structure
```solidity
struct AcceptanceRecord {
    address wallet;
    bytes32 documentHash;    // SHA-256 of document
    string documentVersion;  // e.g., "1.0"
    DocumentType docType;
    uint256 acceptedAt;      // Timestamp
    string ipAddress;        // Can be encrypted off-chain
    bool isValid;
}
```

#### Key Functions

**Document Management**
```solidity
// Register document version (owner only)
function registerDocumentVersion(
    DocumentType docType,
    string memory version,
    bytes32 documentHash
) external onlyOwner

// Verify document hash
function verifyDocumentHash(
    DocumentType docType,
    string memory version,
    bytes32 providedHash
) external view returns (bool)
```

**Acceptance Tracking**
```solidity
// Record user acceptance
function recordAcceptance(
    DocumentType docType,
    string memory version,
    bytes32 documentHash,
    string memory ipAddress
) external

// Check if user has accepted
function hasAccepted(
    address wallet,
    DocumentType docType,
    string memory requiredVersion
) external view returns (bool)

// Get latest acceptance
function getLatestAcceptance(address wallet, DocumentType docType) 
    external view returns (
        uint256 recordId,
        bytes32 documentHash,
        string memory version,
        uint256 acceptedAt,
        bool isValid
    )
```

**GDPR/CCPA Compliance**
```solidity
// Request data deletion
function requestDeletion(string memory requestType) external  // "GDPR" or "CCPA"

// Mark deletion as completed (owner only)
function completeDeletion(address wallet) external onlyOwner

// Get deletion request status
function getDeletionRequest(address wallet) external view returns (
    uint256 requestedAt,
    uint256 completedAt,
    bool isCompleted,
    string memory requestType
)
```

#### Events
```solidity
event AcceptanceRecorded(
    uint256 indexed recordId,
    address indexed wallet,
    DocumentType indexed docType,
    string version,
    bytes32 documentHash,
    uint256 timestamp
);

event DeletionRequested(
    address indexed wallet,
    string requestType,
    uint256 timestamp
);

event DeletionCompleted(
    address indexed wallet,
    uint256 completedAt
);
```

#### Usage Example
```python
from dcmx.tron.contracts import ComplianceRegistryContract
import hashlib

# Initialize contract
compliance = ComplianceRegistryContract(client, contract_address)

# Register document version (owner only)
doc_content = "Terms and Conditions v1.0 text..."
doc_hash = "0x" + hashlib.sha256(doc_content.encode()).hexdigest()
tx_hash = compliance.register_document_version(
    doc_type=0,  # TERMS_AND_CONDITIONS
    version="1.0",
    document_hash=doc_hash
)

# User accepts document
tx_hash = compliance.record_acceptance(
    doc_type=0,
    version="1.0",
    document_hash=doc_hash,
    ip_address="192.168.1.1"
)

# Check acceptance
has_accepted = compliance.has_accepted(wallet, doc_type=0, required_version="1.0")
print(f"Accepted: {has_accepted}")
```

---

## Deployment Guide

### 1. Compile Contracts

```bash
# Install Solidity compiler
pip install py-solc-x

# Compile contracts
python -c "
from solcx import compile_files
contracts = compile_files([
    'dcmx/tron/contracts/DCMXToken.sol',
    'dcmx/tron/contracts/MusicNFT.sol',
    'dcmx/tron/contracts/ComplianceRegistry.sol',
    'dcmx/tron/contracts/RewardVault.sol',
    'dcmx/tron/contracts/RoyaltyDistributor.sol',
])
"
```

### 2. Deploy to Testnet

```bash
# Set environment
export TRON_NETWORK=shasta
export TRON_PRIVATE_KEY=your_private_key

# Deploy
python scripts/deploy_contracts.py
```

### 3. Verify Deployment

```bash
# Check contract on TronScan
https://shasta.tronscan.org/#/contract/[CONTRACT_ADDRESS]
```

## Testing Contracts

```python
# Test DCMXToken
from dcmx.tron import TronClient, DCMXTokenContract

client = TronClient()
token = DCMXTokenContract(client, token_address)

# Test minting
assert token.total_supply() == 0
tx = token.mint(test_address, 1000 * 10**18)
client.wait_for_transaction(tx)
assert token.balance_of(test_address) == 1000 * 10**18
```

## Security Considerations

1. **Access Control**: Only owner can add minters, register documents, etc.
2. **Supply Limits**: DCMXToken has max supply to prevent inflation
3. **Immutability**: Compliance records cannot be modified once created
4. **Royalty Enforcement**: Automated royalty payments on NFT sales
5. **Pausability**: Consider adding pause mechanisms for emergency stops

## Gas Optimization

- Use `external` for functions called externally only
- Pack struct variables efficiently
- Batch operations where possible
- Use events instead of storage for historical data

## Upgradeability

Contracts are **not upgradeable** by design for:
- Immutability guarantees
- User trust
- Security

If upgrades needed:
1. Deploy new version
2. Migrate data
3. Update client configuration
4. Maintain old contracts for historical data
