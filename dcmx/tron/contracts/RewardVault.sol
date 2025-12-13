// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title RewardVault
 * @dev Manages DCMX token rewards for platform participation
 * 
 * Features:
 * - Three reward pools: Sharing, Listening, Bandwidth
 * - Claim verification with proof hashes
 * - Mint DCMX tokens for verified claims
 * - Anti-fraud protection
 */

interface IDCMXToken {
    function mint(address to, uint256 amount) external returns (bool);
}

contract RewardVault {
    address public admin;
    IDCMXToken public dcmxToken;
    
    enum ClaimType {
        SHARING,
        LISTENING,
        BANDWIDTH
    }
    
    struct Claim {
        address user;
        ClaimType claimType;
        uint256 amount;
        bytes32 proofHash;
        uint256 timestamp;
        bool verified;
        bool claimed;
    }
    
    // Claim ID => Claim
    mapping(uint256 => Claim) public claims;
    uint256 private _claimIdCounter;
    
    // User => Total rewards claimed
    mapping(address => uint256) public totalClaimed;
    
    // Pool allocations (in DCMX tokens)
    mapping(ClaimType => uint256) public poolAllocations;
    mapping(ClaimType => uint256) public poolDistributed;
    
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
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    constructor(address _dcmxToken) {
        admin = msg.sender;
        dcmxToken = IDCMXToken(_dcmxToken);
        
        // Initialize pool allocations (can be adjusted by admin)
        poolAllocations[ClaimType.SHARING] = 100_000_000 * 10**18;    // 100M tokens
        poolAllocations[ClaimType.LISTENING] = 100_000_000 * 10**18;  // 100M tokens
        poolAllocations[ClaimType.BANDWIDTH] = 200_000_000 * 10**18;  // 200M tokens
    }
    
    function submitClaim(
        ClaimType claimType,
        bytes32 proofHash,
        uint256 amount
    ) public returns (uint256) {
        require(amount > 0, "Invalid amount");
        require(proofHash != bytes32(0), "Invalid proof");
        
        uint256 claimId = _claimIdCounter++;
        
        claims[claimId] = Claim({
            user: msg.sender,
            claimType: claimType,
            amount: amount,
            proofHash: proofHash,
            timestamp: block.timestamp,
            verified: false,
            claimed: false
        });
        
        emit ClaimSubmitted(claimId, msg.sender, claimType, amount, proofHash);
        
        return claimId;
    }
    
    function verifyClaim(uint256 claimId, bool approved) public onlyAdmin {
        Claim storage claim = claims[claimId];
        require(claim.timestamp > 0, "Claim not found");
        require(!claim.verified, "Already verified");
        
        if (approved) {
            // Check pool has sufficient allocation
            uint256 remaining = poolAllocations[claim.claimType] - 
                                poolDistributed[claim.claimType];
            require(remaining >= claim.amount, "Insufficient pool allocation");
            
            claim.verified = true;
        } else {
            // Rejected claim
            claim.verified = false;
        }
        
        emit ClaimVerified(claimId, approved);
    }
    
    function claimRewards(uint256 claimId) public {
        Claim storage claim = claims[claimId];
        require(claim.user == msg.sender, "Not your claim");
        require(claim.verified, "Claim not verified");
        require(!claim.claimed, "Already claimed");
        
        // Mark as claimed
        claim.claimed = true;
        
        // Update pool distribution
        poolDistributed[claim.claimType] += claim.amount;
        
        // Update user total
        totalClaimed[msg.sender] += claim.amount;
        
        // Mint DCMX tokens to user
        require(
            dcmxToken.mint(msg.sender, claim.amount),
            "Minting failed"
        );
        
        emit RewardsClaimed(claimId, msg.sender, claim.amount);
    }
    
    function getUserRewards(address user) public view returns (
        uint256 pending,
        uint256 claimed
    ) {
        claimed = totalClaimed[user];
        pending = 0;
        
        // Count pending verified claims
        for (uint256 i = 0; i < _claimIdCounter; i++) {
            Claim memory claim = claims[i];
            if (claim.user == user && claim.verified && !claim.claimed) {
                pending += claim.amount;
            }
        }
        
        return (pending, claimed);
    }
    
    function allocatePool(ClaimType claimType, uint256 amount) public onlyAdmin {
        poolAllocations[claimType] = amount;
        emit PoolAllocated(claimType, amount);
    }
    
    function getPoolStatus(ClaimType claimType) public view returns (
        uint256 allocated,
        uint256 distributed,
        uint256 remaining
    ) {
        allocated = poolAllocations[claimType];
        distributed = poolDistributed[claimType];
        remaining = allocated - distributed;
        return (allocated, distributed, remaining);
    }
}
