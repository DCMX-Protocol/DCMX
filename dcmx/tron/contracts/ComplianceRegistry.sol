// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title ComplianceRegistry
 * @dev Blockchain-based compliance tracking for GDPR/CCPA
 * 
 * Features:
 * - Immutable acceptance records
 * - Document version management
 * - Data deletion requests with timestamps
 * - Audit trail for regulatory compliance
 */
contract ComplianceRegistry {
    address public admin;
    
    enum DocumentType {
        TERMS_AND_CONDITIONS,
        PRIVACY_POLICY,
        COOKIE_POLICY,
        NFT_AGREEMENT,
        RISK_DISCLOSURE
    }
    
    struct AcceptanceRecord {
        bytes32 documentHash;
        DocumentType documentType;
        string version;
        uint256 timestamp;
        string ipAddress;  // Hashed in production
        bool isValid;
    }
    
    struct DeletionRequest {
        uint256 timestamp;
        string reason;
        bool processed;
        uint256 processedAt;
    }
    
    // User address => Document type => Acceptance records
    mapping(address => mapping(DocumentType => AcceptanceRecord[])) public acceptances;
    
    // User address => Deletion request
    mapping(address => DeletionRequest) public deletionRequests;
    
    // Document type => Version => Document hash
    mapping(DocumentType => mapping(string => bytes32)) public documentVersions;
    
    event AcceptanceRecorded(
        address indexed user,
        DocumentType indexed documentType,
        bytes32 documentHash,
        string version,
        uint256 timestamp
    );
    
    event DeletionRequested(
        address indexed user,
        uint256 timestamp,
        string reason
    );
    
    event DeletionProcessed(
        address indexed user,
        uint256 timestamp
    );
    
    event DocumentVersionRegistered(
        DocumentType indexed documentType,
        string version,
        bytes32 documentHash
    );
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    constructor() {
        admin = msg.sender;
    }
    
    function registerDocumentVersion(
        DocumentType documentType,
        string memory version,
        bytes32 documentHash
    ) public onlyAdmin {
        require(documentHash != bytes32(0), "Invalid hash");
        require(bytes(version).length > 0, "Invalid version");
        
        documentVersions[documentType][version] = documentHash;
        
        emit DocumentVersionRegistered(documentType, version, documentHash);
    }
    
    function recordAcceptance(
        address user,
        bytes32 documentHash,
        DocumentType documentType,
        string memory version,
        string memory ipAddress
    ) public onlyAdmin {
        require(user != address(0), "Invalid user");
        require(documentHash != bytes32(0), "Invalid hash");
        require(
            documentVersions[documentType][version] == documentHash,
            "Document hash mismatch"
        );
        
        AcceptanceRecord memory record = AcceptanceRecord({
            documentHash: documentHash,
            documentType: documentType,
            version: version,
            timestamp: block.timestamp,
            ipAddress: ipAddress,
            isValid: true
        });
        
        acceptances[user][documentType].push(record);
        
        emit AcceptanceRecorded(
            user,
            documentType,
            documentHash,
            version,
            block.timestamp
        );
    }
    
    function requestDataDeletion(string memory reason) public {
        require(bytes(reason).length > 0, "Reason required");
        require(!deletionRequests[msg.sender].processed, "Already processed");
        
        deletionRequests[msg.sender] = DeletionRequest({
            timestamp: block.timestamp,
            reason: reason,
            processed: false,
            processedAt: 0
        });
        
        emit DeletionRequested(msg.sender, block.timestamp, reason);
    }
    
    function processDeletionRequest(address user) public onlyAdmin {
        require(deletionRequests[user].timestamp > 0, "No request found");
        require(!deletionRequests[user].processed, "Already processed");
        
        deletionRequests[user].processed = true;
        deletionRequests[user].processedAt = block.timestamp;
        
        emit DeletionProcessed(user, block.timestamp);
    }
    
    function verifyAcceptance(
        address user,
        DocumentType documentType,
        bytes32 documentHash
    ) public view returns (bool) {
        AcceptanceRecord[] memory records = acceptances[user][documentType];
        
        for (uint i = 0; i < records.length; i++) {
            if (records[i].documentHash == documentHash && records[i].isValid) {
                return true;
            }
        }
        
        return false;
    }
    
    function getAcceptanceCount(address user, DocumentType documentType)
        public
        view
        returns (uint256)
    {
        return acceptances[user][documentType].length;
    }
    
    function getAcceptance(
        address user,
        DocumentType documentType,
        uint256 index
    ) public view returns (AcceptanceRecord memory) {
        require(index < acceptances[user][documentType].length, "Invalid index");
        return acceptances[user][documentType][index];
    }
    
    function getAuditTrail(address user, DocumentType documentType)
        public
        view
        returns (AcceptanceRecord[] memory)
    {
        return acceptances[user][documentType];
    }
}
