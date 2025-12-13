# DCMX Smart Contracts Documentation

## Overview

DCMX uses five core smart contracts deployed on the TRON blockchain to power the decentralized music platform.

## Contract Addresses

### Testnet (Shasta)
```
DCMX_TOKEN_ADDRESS=<to be deployed>
MUSIC_NFT_ADDRESS=<to be deployed>
COMPLIANCE_REGISTRY_ADDRESS=<to be deployed>
REWARD_VAULT_ADDRESS=<to be deployed>
ROYALTY_DISTRIBUTOR_ADDRESS=<to be deployed>
```

### Mainnet
```
DCMX_TOKEN_ADDRESS=<to be deployed>
MUSIC_NFT_ADDRESS=<to be deployed>
COMPLIANCE_REGISTRY_ADDRESS=<to be deployed>
REWARD_VAULT_ADDRESS=<to be deployed>
ROYALTY_DISTRIBUTOR_ADDRESS=<to be deployed>
```

---

## 1. DCMXToken (TRC-20)

### Description
Utility token for the DCMX platform. Used for rewards, governance, and platform fees.

### Token Economics
- **Name**: DCMX
- **Symbol**: DCMX
- **Decimals**: 18
- **Max Supply**: 1,000,000,000 (1 billion)
- **Initial Supply**: Set at deployment
- **Type**: Utility token (NOT a security)

### Key Functions

#### `transfer(address to, uint256 value) → bool`
Transfer tokens to another address.

**Parameters**:
- `to`: Recipient address
- `value`: Amount to transfer (in smallest unit, 10^-18)

**Returns**: `true` if successful

**Events**: `Transfer(from, to, value)`

**Example**:
```solidity
// Transfer 100 DCMX tokens
dcmxToken.transfer(recipientAddress, 100 * 10**18);
```

#### `approve(address spender, uint256 value) → bool`
Approve another address to spend tokens on your behalf.

**Parameters**:
- `spender`: Address authorized to spend
- `value`: Maximum amount they can spend

**Returns**: `true` if successful

**Events**: `Approval(owner, spender, value)`

#### `transferFrom(address from, address to, uint256 value) → bool`
Transfer tokens on behalf of another address (requires prior approval).

**Parameters**:
- `from`: Address to transfer from
- `to`: Recipient address
- `value`: Amount to transfer

**Returns**: `true` if successful

**Events**: `Transfer(from, to, value)`

#### `mint(address to, uint256 value) → bool` (Admin only)
Mint new tokens (up to max supply).

**Parameters**:
- `to`: Recipient address
- `value`: Amount to mint

**Returns**: `true` if successful

**Events**: `Mint(to, value)`, `Transfer(0x0, to, value)`

**Access**: Admin only

#### `burn(uint256 value) → bool`
Burn tokens from sender's balance.

**Parameters**:
- `value`: Amount to burn

**Returns**: `true` if successful

**Events**: `Burn(from, value)`, `Transfer(from, 0x0, value)`

### Read Functions

#### `balanceOf(address owner) → uint256`
Get token balance of an address.

#### `totalSupply() → uint256`
Get total circulating supply.

#### `allowance(address owner, address spender) → uint256`
Get approved spending amount.

### Events

```solidity
event Transfer(address indexed from, address indexed to, uint256 value);
event Approval(address indexed owner, address indexed spender, uint256 value);
event Mint(address indexed to, uint256 value);
event Burn(address indexed from, uint256 value);
event MintingFinished();
```

---

## 2. MusicNFT (TRC-721)

### Description
NFT contract for music tracks with edition tracking and royalty support.

### Key Functions

#### `mint(...) → uint256` (Admin only)
Mint a new music NFT.

**Parameters**:
```solidity
address to,                 // NFT recipient
string memory title,        // Track title
string memory artist,       // Artist name
string memory contentHash,  // Content hash (SHA-256)
uint256 edition,            // Edition number (1-based)
uint256 maxEditions,        // Total editions
uint256 royaltyBps,         // Royalty in basis points (1000 = 10%)
address royaltyRecipient    // Royalty recipient address
```

**Returns**: Token ID

**Events**: `Minted(to, tokenId, contentHash)`, `Transfer(0x0, to, tokenId)`

**Example**:
```solidity
uint256 tokenId = musicNFT.mint(
    artistAddress,
    "My Song",
    "Artist Name",
    "QmContentHash123...",
    1,      // Edition 1
    100,    // of 100
    1000,   // 10% royalty
    artistAddress
);
```

#### `transfer(address to, uint256 tokenId)`
Transfer NFT to another address.

**Parameters**:
- `to`: Recipient address
- `tokenId`: NFT token ID

**Events**: `Transfer(from, to, tokenId)`

#### `approve(address to, uint256 tokenId)` (Owner only)
Approve another address to transfer this NFT.

**Parameters**:
- `to`: Approved address
- `tokenId`: NFT token ID

**Events**: `Approval(owner, approved, tokenId)`

#### `setApprovalForAll(address operator, bool approved)`
Approve/revoke an operator for all your NFTs.

**Parameters**:
- `operator`: Operator address
- `approved`: Approval status

**Events**: `ApprovalForAll(owner, operator, approved)`

### Read Functions

#### `ownerOf(uint256 tokenId) → address`
Get NFT owner.

#### `balanceOf(address owner) → uint256`
Get NFT count for address.

#### `tokenMetadata(uint256 tokenId) → NFTMetadata`
Get NFT metadata:
```solidity
struct NFTMetadata {
    string title;
    string artist;
    string contentHash;
    uint256 edition;
    uint256 maxEditions;
    uint256 royaltyBps;
    address royaltyRecipient;
}
```

#### `royaltyInfo(uint256 tokenId, uint256 salePrice) → (address, uint256)`
Calculate royalty for a sale (ERC-2981 compatible).

**Returns**: Recipient address and royalty amount

**Example**:
```solidity
(address recipient, uint256 royaltyAmount) = 
    musicNFT.royaltyInfo(tokenId, 1000000); // 1 TRX sale
```

#### `tokenURI(uint256 tokenId) → string`
Get metadata URI (returns inline JSON for now).

### Events

```solidity
event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
event Minted(address indexed to, uint256 indexed tokenId, string contentHash);
```

---

## 3. ComplianceRegistry

### Description
Tracks legal document acceptances for GDPR/CCPA compliance.

### Document Types Enum
```solidity
enum DocumentType {
    TERMS_AND_CONDITIONS,  // 0
    PRIVACY_POLICY,        // 1
    COOKIE_POLICY,         // 2
    NFT_AGREEMENT,         // 3
    RISK_DISCLOSURE        // 4
}
```

### Key Functions

#### `registerDocumentVersion(...)` (Admin only)
Register a new document version.

**Parameters**:
```solidity
DocumentType documentType,
string memory version,      // e.g., "1.0", "2.0"
bytes32 documentHash        // SHA-256 hash of document
```

**Events**: `DocumentVersionRegistered(documentType, version, documentHash)`

#### `recordAcceptance(...)` (Admin only)
Record user acceptance of a document.

**Parameters**:
```solidity
address user,
bytes32 documentHash,
DocumentType documentType,
string memory version,
string memory ipAddress     // Hashed for privacy
```

**Events**: `AcceptanceRecorded(user, documentType, documentHash, version, timestamp)`

#### `requestDataDeletion(string memory reason)`
User requests data deletion.

**Parameters**:
- `reason`: Deletion reason

**Events**: `DeletionRequested(user, timestamp, reason)`

#### `processDeletionRequest(address user)` (Admin only)
Mark deletion request as processed.

**Parameters**:
- `user`: User address

**Events**: `DeletionProcessed(user, timestamp)`

### Read Functions

#### `verifyAcceptance(...) → bool`
Verify if user has accepted a document.

**Parameters**:
```solidity
address user,
DocumentType documentType,
bytes32 documentHash
```

**Returns**: `true` if accepted

#### `getAcceptanceCount(address user, DocumentType documentType) → uint256`
Get number of acceptances for user.

#### `getAcceptance(...) → AcceptanceRecord`
Get specific acceptance record.

**Returns**:
```solidity
struct AcceptanceRecord {
    bytes32 documentHash;
    DocumentType documentType;
    string version;
    uint256 timestamp;
    string ipAddress;
    bool isValid;
}
```

#### `getAuditTrail(address user, DocumentType documentType) → AcceptanceRecord[]`
Get full audit trail for user.

### Events

```solidity
event AcceptanceRecorded(
    address indexed user,
    DocumentType indexed documentType,
    bytes32 documentHash,
    string version,
    uint256 timestamp
);
event DeletionRequested(address indexed user, uint256 timestamp, string reason);
event DeletionProcessed(address indexed user, uint256 timestamp);
event DocumentVersionRegistered(DocumentType indexed documentType, string version, bytes32 documentHash);
```

---

## 4. RewardVault

### Description
Manages reward distribution for platform participation.

### Claim Types Enum
```solidity
enum ClaimType {
    SHARING,    // 0: Content sharing rewards
    LISTENING,  // 1: Listening rewards
    BANDWIDTH   // 2: Network bandwidth rewards
}
```

### Key Functions

#### `submitClaim(...) → uint256`
Submit a reward claim.

**Parameters**:
```solidity
ClaimType claimType,
bytes32 proofHash,      // Hash of proof data
uint256 amount          // Reward amount in tokens
```

**Returns**: Claim ID

**Events**: `ClaimSubmitted(claimId, user, claimType, amount, proofHash)`

#### `verifyClaim(uint256 claimId, bool approved)` (Admin only)
Verify or reject a claim.

**Parameters**:
- `claimId`: Claim ID
- `approved`: Verification result

**Events**: `ClaimVerified(claimId, approved)`

#### `claimRewards(uint256 claimId)`
Claim verified rewards (mints DCMX tokens).

**Parameters**:
- `claimId`: Claim ID

**Events**: `RewardsClaimed(claimId, user, amount)`

#### `allocatePool(ClaimType claimType, uint256 amount)` (Admin only)
Set pool allocation.

**Parameters**:
- `claimType`: Pool type
- `amount`: Allocation amount

**Events**: `PoolAllocated(claimType, amount)`

### Read Functions

#### `getUserRewards(address user) → (uint256 pending, uint256 claimed)`
Get user's reward status.

**Returns**:
- `pending`: Verified but unclaimed rewards
- `claimed`: Total claimed rewards

#### `getPoolStatus(ClaimType claimType) → (uint256 allocated, uint256 distributed, uint256 remaining)`
Get pool status.

### Events

```solidity
event ClaimSubmitted(
    uint256 indexed claimId,
    address indexed user,
    ClaimType claimType,
    uint256 amount,
    bytes32 proofHash
);
event ClaimVerified(uint256 indexed claimId, bool approved);
event RewardsClaimed(uint256 indexed claimId, address indexed user, uint256 amount);
event PoolAllocated(ClaimType indexed claimType, uint256 amount);
```

---

## 5. RoyaltyDistributor

### Description
Manages NFT sales and automatic royalty distribution.

### Key Functions

#### `setRoyaltySplit(...)` (Admin only)
Configure royalty splits for an NFT.

**Parameters**:
```solidity
address nftContract,
uint256 nftTokenId,
address[] memory recipients,
uint256[] memory percentages  // Basis points (sum ≤ 10000)
```

**Events**: `RoyaltySplitSet(nftContract, nftTokenId, recipient, percentage)` for each recipient

**Example**:
```solidity
// 70% to artist, 20% to producer, 10% to platform
address[] memory recipients = [artist, producer, platform];
uint256[] memory percentages = [7000, 2000, 1000];

royaltyDistributor.setRoyaltySplit(
    nftContract,
    tokenId,
    recipients,
    percentages
);
```

#### `recordSale(...) → uint256` (Admin only)
Record an NFT sale.

**Parameters**:
```solidity
address nftContract,
uint256 nftTokenId,
address seller,
address buyer,
uint256 salePrice        // In SUN (10^-6 TRX)
```

**Returns**: Sale ID

**Events**: `SaleRecorded(saleId, nftContract, nftTokenId, seller, buyer, salePrice)`

#### `distributeRoyalties(uint256 saleId)` (Admin only)
Distribute royalties for a sale.

**Parameters**:
- `saleId`: Sale ID

**Events**: `RoyaltiesDistributed(saleId, totalRoyalties)`, `RoyaltyPaid(recipient, amount)` for each recipient

#### `withdrawRoyalties()`
Withdraw pending royalties.

**Events**: `Withdrawal(recipient, amount)`

### Read Functions

#### `getRoyaltyInfo(address nftContract, uint256 nftTokenId) → RoyaltySplit[]`
Get royalty configuration.

**Returns**:
```solidity
struct RoyaltySplit {
    address recipient;
    uint256 percentage;  // Basis points
}
```

#### `getPendingRoyalties(address recipient) → uint256`
Get pending royalty balance.

#### `getSale(uint256 saleId) → Sale`
Get sale details.

**Returns**:
```solidity
struct Sale {
    uint256 nftTokenId;
    address nftContract;
    address seller;
    address buyer;
    uint256 salePrice;
    uint256 timestamp;
    bool royaltiesDistributed;
}
```

### Events

```solidity
event SaleRecorded(
    uint256 indexed saleId,
    address indexed nftContract,
    uint256 indexed nftTokenId,
    address seller,
    address buyer,
    uint256 salePrice
);
event RoyaltiesDistributed(uint256 indexed saleId, uint256 totalRoyalties);
event RoyaltyPaid(address indexed recipient, uint256 amount);
event Withdrawal(address indexed recipient, uint256 amount);
event RoyaltySplitSet(
    address indexed nftContract,
    uint256 indexed nftTokenId,
    address recipient,
    uint256 percentage
);
```

---

## Security Considerations

### Access Control

All contracts use simple admin-based access control:
```solidity
address public admin;

modifier onlyAdmin() {
    require(msg.sender == admin, "Only admin");
    _;
}
```

**Recommendation**: For production, upgrade to role-based access control (e.g., OpenZeppelin's AccessControl).

### Input Validation

All contracts validate inputs:
- Non-zero addresses
- Valid enum values
- Amount limits
- Array length matches

### Reentrancy Protection

Contracts follow checks-effects-interactions pattern:
1. Check conditions
2. Update state
3. External calls

**Note**: For additional safety, consider adding OpenZeppelin's ReentrancyGuard.

### Integer Overflow

Solidity 0.8+ has built-in overflow protection.

### Gas Optimization

- Use `uint256` (cheaper than smaller types in storage)
- Batch operations where possible
- Minimize storage writes
- Use events for historical data

## Testing

### Unit Tests

Test each contract function:
```javascript
// Example with TronBox
contract('DCMXToken', (accounts) => {
    it('should transfer tokens correctly', async () => {
        const token = await DCMXToken.deployed();
        await token.transfer(accounts[1], 100);
        const balance = await token.balanceOf(accounts[1]);
        assert.equal(balance, 100);
    });
});
```

### Integration Tests

Test contract interactions:
- Mint NFT → Record Sale → Distribute Royalties
- Submit Claim → Verify → Claim Rewards
- Register Document → Record Acceptance → Verify

### Mainnet Testing

1. Deploy to testnet (Shasta)
2. Test all functions
3. Monitor for 1 week
4. Perform security audit
5. Deploy to mainnet

## Upgradability

Current contracts are **not upgradable** (immutable).

**Pros**: Maximum trust and security
**Cons**: Cannot fix bugs or add features

**For Future**: Consider using proxy patterns (e.g., UUPS) for upgradability while maintaining security.

## Gas Costs (Estimated)

| Operation | Estimated Gas | TRX Cost (approx) |
|-----------|---------------|-------------------|
| Token Transfer | ~20,000 | ~0.001 TRX |
| NFT Mint | ~150,000 | ~0.008 TRX |
| Submit Claim | ~100,000 | ~0.005 TRX |
| Record Acceptance | ~80,000 | ~0.004 TRX |
| Record Sale | ~120,000 | ~0.006 TRX |

**Note**: Actual costs depend on network congestion and contract complexity.

## Audit Status

- [ ] Internal audit complete
- [ ] External audit scheduled
- [ ] Bug bounty program active
- [ ] Mainnet deployment

## Resources

- **TRON Contract Standards**: https://developers.tron.network/docs/trc20
- **Solidity Documentation**: https://docs.soliditylang.org/
- **OpenZeppelin Contracts**: https://docs.openzeppelin.com/contracts/
- **Security Best Practices**: https://consensys.github.io/smart-contract-best-practices/
