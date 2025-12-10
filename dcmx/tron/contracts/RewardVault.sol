// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IDCMXToken {
    function mint(address to, uint256 amount) external returns (bool);
}

/**
 * @title RewardVault
 * @dev Decentralized Reward Distribution System
 * 
 * Features:
 * - Separate reward pools (sharing, listening, bandwidth)
 * - Claim verification & minting
 * - Anti-gaming mechanisms
 * - ZK proof integration placeholder for privacy
 */
contract RewardVault {
    address public owner;
    IDCMXToken public dcmxToken;
    
    enum RewardType {
        SHARING,
        LISTENING,
        BANDWIDTH,
        VOTING,
        REFERRAL
    }
    
    struct RewardClaim {
        address claimant;
        RewardType rewardType;
        uint256 amount;
        uint256 timestamp;
        bytes32 proofHash;  // Hash of ZK proof or activity proof
        bool claimed;
        bool verified;
    }
    
    struct RewardPool {
        uint256 totalAllocated;
        uint256 totalClaimed;
        uint256 dailyLimit;
        uint256 minClaimAmount;
        bool active;
    }
    
    // Reward pools by type
    mapping(RewardType => RewardPool) public rewardPools;
    
    // Claim ID => RewardClaim
    mapping(uint256 => RewardClaim) public claims;
    uint256 private _claimCounter;
    
    // User => Reward Type => Daily claimed amount
    mapping(address => mapping(RewardType => uint256)) public dailyClaimed;
    mapping(address => uint256) public lastClaimDate;  // Date in days since epoch
    
    // Authorized verifiers (can approve claims)
    mapping(address => bool) public verifiers;
    
    event RewardClaimed(
        uint256 indexed claimId,
        address indexed claimant,
        RewardType indexed rewardType,
        uint256 amount,
        uint256 timestamp
    );
    
    event ClaimVerified(
        uint256 indexed claimId,
        address indexed verifier,
        bool approved
    );
    
    event RewardPoolUpdated(
        RewardType indexed rewardType,
        uint256 totalAllocated,
        uint256 dailyLimit
    );
    
    event VerifierAdded(address indexed verifier);
    event VerifierRemoved(address indexed verifier);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier onlyVerifier() {
        require(verifiers[msg.sender], "Not authorized verifier");
        _;
    }
    
    constructor(address _dcmxToken) {
        owner = msg.sender;
        dcmxToken = IDCMXToken(_dcmxToken);
        
        // Initialize default reward pools
        _initializeRewardPool(RewardType.SHARING, 1000000 * 10**18, 10000 * 10**18, 1 * 10**18);
        _initializeRewardPool(RewardType.LISTENING, 2000000 * 10**18, 20000 * 10**18, 1 * 10**18);
        _initializeRewardPool(RewardType.BANDWIDTH, 3000000 * 10**18, 30000 * 10**18, 5 * 10**18);
        _initializeRewardPool(RewardType.VOTING, 500000 * 10**18, 5000 * 10**18, 1 * 10**18);
        _initializeRewardPool(RewardType.REFERRAL, 500000 * 10**18, 5000 * 10**18, 10 * 10**18);
    }
    
    function _initializeRewardPool(
        RewardType rewardType,
        uint256 totalAllocated,
        uint256 dailyLimit,
        uint256 minClaimAmount
    ) internal {
        rewardPools[rewardType] = RewardPool({
            totalAllocated: totalAllocated,
            totalClaimed: 0,
            dailyLimit: dailyLimit,
            minClaimAmount: minClaimAmount,
            active: true
        });
    }
    
    /**
     * @dev Submit a reward claim
     */
    function submitClaim(
        RewardType rewardType,
        uint256 amount,
        bytes32 proofHash
    ) external returns (uint256) {
        RewardPool storage pool = rewardPools[rewardType];
        require(pool.active, "Pool inactive");
        require(amount >= pool.minClaimAmount, "Below minimum");
        require(amount <= pool.dailyLimit, "Exceeds daily limit");
        require(pool.totalClaimed + amount <= pool.totalAllocated, "Pool depleted");
        
        // Check daily limit per user
        uint256 currentDate = block.timestamp / 1 days;
        if (lastClaimDate[msg.sender] != currentDate) {
            // Reset daily counter
            dailyClaimed[msg.sender][rewardType] = 0;
            lastClaimDate[msg.sender] = currentDate;
        }
        
        require(
            dailyClaimed[msg.sender][rewardType] + amount <= pool.dailyLimit,
            "Daily limit exceeded"
        );
        
        _claimCounter++;
        uint256 claimId = _claimCounter;
        
        claims[claimId] = RewardClaim({
            claimant: msg.sender,
            rewardType: rewardType,
            amount: amount,
            timestamp: block.timestamp,
            proofHash: proofHash,
            claimed: false,
            verified: false
        });
        
        return claimId;
    }
    
    /**
     * @dev Verify a claim (by authorized verifier)
     */
    function verifyClaim(uint256 claimId, bool approved) external onlyVerifier {
        RewardClaim storage claim = claims[claimId];
        require(claim.claimant != address(0), "Claim not found");
        require(!claim.verified, "Already verified");
        require(!claim.claimed, "Already claimed");
        
        claim.verified = approved;
        
        if (approved) {
            // Execute claim
            _executeClaim(claimId);
        }
        
        emit ClaimVerified(claimId, msg.sender, approved);
    }
    
    /**
     * @dev Execute an approved claim (internal)
     */
    function _executeClaim(uint256 claimId) internal {
        RewardClaim storage claim = claims[claimId];
        require(claim.verified, "Not verified");
        require(!claim.claimed, "Already claimed");
        
        RewardPool storage pool = rewardPools[claim.rewardType];
        
        // Update state
        claim.claimed = true;
        pool.totalClaimed += claim.amount;
        dailyClaimed[claim.claimant][claim.rewardType] += claim.amount;
        
        // Mint tokens to claimant
        require(
            dcmxToken.mint(claim.claimant, claim.amount),
            "Mint failed"
        );
        
        emit RewardClaimed(
            claimId,
            claim.claimant,
            claim.rewardType,
            claim.amount,
            block.timestamp
        );
    }
    
    /**
     * @dev Batch verify claims (for efficiency)
     */
    function batchVerifyClaims(uint256[] memory claimIds, bool[] memory approvals) 
        external 
        onlyVerifier 
    {
        require(claimIds.length == approvals.length, "Length mismatch");
        
        for (uint256 i = 0; i < claimIds.length; i++) {
            verifyClaim(claimIds[i], approvals[i]);
        }
    }
    
    /**
     * @dev Update reward pool parameters
     */
    function updateRewardPool(
        RewardType rewardType,
        uint256 totalAllocated,
        uint256 dailyLimit,
        uint256 minClaimAmount,
        bool active
    ) external onlyOwner {
        RewardPool storage pool = rewardPools[rewardType];
        require(totalAllocated >= pool.totalClaimed, "Cannot reduce below claimed");
        
        pool.totalAllocated = totalAllocated;
        pool.dailyLimit = dailyLimit;
        pool.minClaimAmount = minClaimAmount;
        pool.active = active;
        
        emit RewardPoolUpdated(rewardType, totalAllocated, dailyLimit);
    }
    
    /**
     * @dev Add authorized verifier
     */
    function addVerifier(address verifier) external onlyOwner {
        require(verifier != address(0), "Invalid verifier");
        verifiers[verifier] = true;
        emit VerifierAdded(verifier);
    }
    
    /**
     * @dev Remove authorized verifier
     */
    function removeVerifier(address verifier) external onlyOwner {
        verifiers[verifier] = false;
        emit VerifierRemoved(verifier);
    }
    
    /**
     * @dev Get claim details
     */
    function getClaim(uint256 claimId) external view returns (
        address claimant,
        RewardType rewardType,
        uint256 amount,
        uint256 timestamp,
        bool claimed,
        bool verified
    ) {
        RewardClaim memory claim = claims[claimId];
        return (
            claim.claimant,
            claim.rewardType,
            claim.amount,
            claim.timestamp,
            claim.claimed,
            claim.verified
        );
    }
    
    /**
     * @dev Get reward pool status
     */
    function getPoolStatus(RewardType rewardType) external view returns (
        uint256 totalAllocated,
        uint256 totalClaimed,
        uint256 remaining,
        uint256 dailyLimit,
        bool active
    ) {
        RewardPool memory pool = rewardPools[rewardType];
        return (
            pool.totalAllocated,
            pool.totalClaimed,
            pool.totalAllocated - pool.totalClaimed,
            pool.dailyLimit,
            pool.active
        );
    }
    
    /**
     * @dev Get user's daily claim status
     */
    function getUserDailyClaimed(address user, RewardType rewardType) 
        external 
        view 
        returns (uint256) 
    {
        uint256 currentDate = block.timestamp / 1 days;
        if (lastClaimDate[user] != currentDate) {
            return 0;  // New day, no claims yet
        }
        return dailyClaimed[user][rewardType];
    }
    
    /**
     * @dev Total claims count
     */
    function totalClaims() external view returns (uint256) {
        return _claimCounter;
    }
    
    /**
     * @dev Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        owner = newOwner;
    }
}
