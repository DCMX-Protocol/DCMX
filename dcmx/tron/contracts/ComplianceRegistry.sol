// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ComplianceRegistry
 * @dev Immutable Legal Acceptance Tracking on TRON
 * 
 * Features:
 * - Immutable acceptance records (hash-based)
 * - Document version control
 * - User data deletion requests (GDPR/CCPA)
 * - Compliance audit trail with blockchain timestamps
 */
contract ComplianceRegistry {
    address public owner;
    
    enum DocumentType {
        TERMS_AND_CONDITIONS,
        PRIVACY_POLICY,
        COOKIE_POLICY,
        NFT_AGREEMENT,
        RISK_DISCLOSURE
    }
    
    struct AcceptanceRecord {
        address wallet;
        bytes32 documentHash;  // SHA-256 hash of document content
        string documentVersion;
        DocumentType docType;
        uint256 acceptedAt;
        string ipAddress;  // Can be encrypted off-chain
        bool isValid;
    }
    
    struct DeletionRequest {
        address wallet;
        uint256 requestedAt;
        uint256 completedAt;
        bool isCompleted;
        string requestType;  // "GDPR" or "CCPA"
    }
    
    // Wallet => Document Type => Latest Acceptance Record ID
    mapping(address => mapping(DocumentType => uint256)) public latestAcceptance;
    
    // Unique acceptance record ID => AcceptanceRecord
    mapping(uint256 => AcceptanceRecord) public acceptances;
    uint256 private _acceptanceCounter;
    
    // Wallet => Deletion Request
    mapping(address => DeletionRequest) public deletionRequests;
    
    // Document Type => Version => Hash
    mapping(DocumentType => mapping(string => bytes32)) public documentHashes;
    
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
    
    event DocumentVersionRegistered(
        DocumentType indexed docType,
        string version,
        bytes32 documentHash
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @dev Register a document version hash
     * Only owner can register official document versions
     */
    function registerDocumentVersion(
        DocumentType docType,
        string memory version,
        bytes32 documentHash
    ) external onlyOwner {
        require(documentHashes[docType][version] == bytes32(0), "Version exists");
        require(documentHash != bytes32(0), "Invalid hash");
        
        documentHashes[docType][version] = documentHash;
        emit DocumentVersionRegistered(docType, version, documentHash);
    }
    
    /**
     * @dev Record user acceptance of a legal document
     */
    function recordAcceptance(
        DocumentType docType,
        string memory version,
        bytes32 documentHash,
        string memory ipAddress
    ) external {
        require(documentHashes[docType][version] == documentHash, "Document hash mismatch");
        
        _acceptanceCounter++;
        uint256 recordId = _acceptanceCounter;
        
        acceptances[recordId] = AcceptanceRecord({
            wallet: msg.sender,
            documentHash: documentHash,
            documentVersion: version,
            docType: docType,
            acceptedAt: block.timestamp,
            ipAddress: ipAddress,
            isValid: true
        });
        
        latestAcceptance[msg.sender][docType] = recordId;
        
        emit AcceptanceRecorded(
            recordId,
            msg.sender,
            docType,
            version,
            documentHash,
            block.timestamp
        );
    }
    
    /**
     * @dev Get latest acceptance for a user and document type
     */
    function getLatestAcceptance(address wallet, DocumentType docType) 
        external 
        view 
        returns (
            uint256 recordId,
            bytes32 documentHash,
            string memory version,
            uint256 acceptedAt,
            bool isValid
        ) 
    {
        recordId = latestAcceptance[wallet][docType];
        require(recordId > 0, "No acceptance found");
        
        AcceptanceRecord memory record = acceptances[recordId];
        return (
            recordId,
            record.documentHash,
            record.documentVersion,
            record.acceptedAt,
            record.isValid
        );
    }
    
    /**
     * @dev Check if user has accepted a document
     */
    function hasAccepted(
        address wallet,
        DocumentType docType,
        string memory requiredVersion
    ) external view returns (bool) {
        uint256 recordId = latestAcceptance[wallet][docType];
        if (recordId == 0) return false;
        
        AcceptanceRecord memory record = acceptances[recordId];
        if (!record.isValid) return false;
        
        // Check if version matches (if specified)
        if (bytes(requiredVersion).length > 0) {
            return keccak256(bytes(record.documentVersion)) == keccak256(bytes(requiredVersion));
        }
        
        return true;
    }
    
    /**
     * @dev Request data deletion (GDPR/CCPA)
     * This creates an immutable record of the deletion request
     * Actual data deletion happens off-chain with this timestamp as proof
     */
    function requestDeletion(string memory requestType) external {
        require(
            keccak256(bytes(requestType)) == keccak256(bytes("GDPR")) ||
            keccak256(bytes(requestType)) == keccak256(bytes("CCPA")),
            "Invalid request type"
        );
        require(deletionRequests[msg.sender].requestedAt == 0, "Request already exists");
        
        deletionRequests[msg.sender] = DeletionRequest({
            wallet: msg.sender,
            requestedAt: block.timestamp,
            completedAt: 0,
            isCompleted: false,
            requestType: requestType
        });
        
        emit DeletionRequested(msg.sender, requestType, block.timestamp);
    }
    
    /**
     * @dev Mark deletion request as completed (admin only)
     */
    function completeDeletion(address wallet) external onlyOwner {
        require(deletionRequests[wallet].requestedAt > 0, "No request found");
        require(!deletionRequests[wallet].isCompleted, "Already completed");
        
        deletionRequests[wallet].completedAt = block.timestamp;
        deletionRequests[wallet].isCompleted = true;
        
        emit DeletionCompleted(wallet, block.timestamp);
    }
    
    /**
     * @dev Invalidate an acceptance record (admin only, for data corrections)
     */
    function invalidateAcceptance(uint256 recordId) external onlyOwner {
        require(acceptances[recordId].wallet != address(0), "Record not found");
        acceptances[recordId].isValid = false;
    }
    
    /**
     * @dev Get deletion request status
     */
    function getDeletionRequest(address wallet) external view returns (
        uint256 requestedAt,
        uint256 completedAt,
        bool isCompleted,
        string memory requestType
    ) {
        DeletionRequest memory request = deletionRequests[wallet];
        return (
            request.requestedAt,
            request.completedAt,
            request.isCompleted,
            request.requestType
        );
    }
    
    /**
     * @dev Get total number of acceptance records
     */
    function totalAcceptances() external view returns (uint256) {
        return _acceptanceCounter;
    }
    
    /**
     * @dev Verify document hash matches registered version
     */
    function verifyDocumentHash(
        DocumentType docType,
        string memory version,
        bytes32 providedHash
    ) external view returns (bool) {
        return documentHashes[docType][version] == providedHash;
    }
    
    /**
     * @dev Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        owner = newOwner;
    }
}
