// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MusicNFT
 * @dev TRC-721 Music Rights NFT with Metadata and Royalties
 * 
 * Features:
 * - Music metadata (title, artist, content hash)
 * - Edition tracking (1 of 100, etc.)
 * - Royalty recipients (ERC-2981 compatible)
 * - Transfer history on-chain
 */
contract MusicNFT {
    string public constant name = "DCMX Music NFT";
    string public constant symbol = "DCMXMUSIC";
    
    uint256 private _tokenIdCounter;
    address public owner;
    
    struct MusicMetadata {
        string title;
        string artist;
        string contentHash;  // SHA-256 hash of audio file
        uint256 editionNumber;
        uint256 maxEditions;
        address artistWallet;
        uint96 royaltyBps;  // Basis points (1000 = 10%)
        uint256 mintedAt;
    }
    
    // Token ID => Owner
    mapping(uint256 => address) private _owners;
    
    // Owner => Balance
    mapping(address => uint256) private _balances;
    
    // Token ID => Approved address
    mapping(uint256 => address) private _tokenApprovals;
    
    // Owner => Operator => Approved
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    
    // Token ID => Metadata
    mapping(uint256 => MusicMetadata) public metadata;
    
    // Token URI base (e.g., "https://ipfs.io/ipfs/")
    string private _baseTokenURI;
    
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
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(string memory baseURI) {
        owner = msg.sender;
        _baseTokenURI = baseURI;
    }
    
    /**
     * @dev Mint a new music NFT
     */
    function mintMusic(
        address to,
        string memory title,
        string memory artist,
        string memory contentHash,
        uint256 editionNumber,
        uint256 maxEditions,
        uint96 royaltyBps
    ) external returns (uint256) {
        require(to != address(0), "Invalid recipient");
        require(bytes(title).length > 0, "Title required");
        require(bytes(artist).length > 0, "Artist required");
        require(bytes(contentHash).length > 0, "Content hash required");
        require(editionNumber > 0 && editionNumber <= maxEditions, "Invalid edition");
        require(royaltyBps <= 10000, "Royalty too high");
        
        _tokenIdCounter++;
        uint256 tokenId = _tokenIdCounter;
        
        _owners[tokenId] = to;
        _balances[to]++;
        
        metadata[tokenId] = MusicMetadata({
            title: title,
            artist: artist,
            contentHash: contentHash,
            editionNumber: editionNumber,
            maxEditions: maxEditions,
            artistWallet: msg.sender,
            royaltyBps: royaltyBps,
            mintedAt: block.timestamp
        });
        
        emit Transfer(address(0), to, tokenId);
        emit MusicMinted(tokenId, msg.sender, title, contentHash, editionNumber, maxEditions);
        
        return tokenId;
    }
    
    /**
     * @dev Get metadata for a token
     */
    function getMetadata(uint256 tokenId) external view returns (
        string memory title,
        string memory artist,
        string memory contentHash,
        uint256 editionNumber,
        uint256 maxEditions,
        address artistWallet
    ) {
        require(_owners[tokenId] != address(0), "Token not minted");
        MusicMetadata memory meta = metadata[tokenId];
        return (
            meta.title,
            meta.artist,
            meta.contentHash,
            meta.editionNumber,
            meta.maxEditions,
            meta.artistWallet
        );
    }
    
    /**
     * @dev Standard ERC-721 functions
     */
    function balanceOf(address owner_) external view returns (uint256) {
        require(owner_ != address(0), "Invalid address");
        return _balances[owner_];
    }
    
    function ownerOf(uint256 tokenId) public view returns (address) {
        address owner_ = _owners[tokenId];
        require(owner_ != address(0), "Token not minted");
        return owner_;
    }
    
    function approve(address to, uint256 tokenId) external {
        address owner_ = ownerOf(tokenId);
        require(msg.sender == owner_ || _operatorApprovals[owner_][msg.sender], "Not authorized");
        
        _tokenApprovals[tokenId] = to;
        emit Approval(owner_, to, tokenId);
    }
    
    function getApproved(uint256 tokenId) external view returns (address) {
        require(_owners[tokenId] != address(0), "Token not minted");
        return _tokenApprovals[tokenId];
    }
    
    function setApprovalForAll(address operator, bool approved) external {
        require(operator != msg.sender, "Cannot approve self");
        _operatorApprovals[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }
    
    function isApprovedForAll(address owner_, address operator) external view returns (bool) {
        return _operatorApprovals[owner_][operator];
    }
    
    function transferFrom(address from, address to, uint256 tokenId) public {
        require(_isApprovedOrOwner(msg.sender, tokenId), "Not authorized");
        require(from == ownerOf(tokenId), "Not token owner");
        require(to != address(0), "Invalid recipient");
        
        // Clear approval
        _tokenApprovals[tokenId] = address(0);
        
        _balances[from]--;
        _balances[to]++;
        _owners[tokenId] = to;
        
        emit Transfer(from, to, tokenId);
    }
    
    function safeTransferFrom(address from, address to, uint256 tokenId) external {
        transferFrom(from, to, tokenId);
    }
    
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory) external {
        transferFrom(from, to, tokenId);
    }
    
    /**
     * @dev ERC-2981 Royalty Info
     */
    function royaltyInfo(uint256 tokenId, uint256 salePrice) external view returns (
        address receiver,
        uint256 royaltyAmount
    ) {
        require(_owners[tokenId] != address(0), "Token not minted");
        MusicMetadata memory meta = metadata[tokenId];
        
        receiver = meta.artistWallet;
        royaltyAmount = (salePrice * meta.royaltyBps) / 10000;
    }
    
    /**
     * @dev Token URI
     */
    function tokenURI(uint256 tokenId) external view returns (string memory) {
        require(_owners[tokenId] != address(0), "Token not minted");
        
        // Return base URI + content hash for IPFS/Arweave metadata
        return string(abi.encodePacked(_baseTokenURI, metadata[tokenId].contentHash));
    }
    
    function setBaseURI(string memory baseURI) external onlyOwner {
        _baseTokenURI = baseURI;
    }
    
    function totalSupply() external view returns (uint256) {
        return _tokenIdCounter;
    }
    
    /**
     * @dev EIP-165 interface support
     */
    function supportsInterface(bytes4 interfaceId) external pure returns (bool) {
        return
            interfaceId == 0x01ffc9a7 || // ERC165
            interfaceId == 0x80ac58cd || // ERC721
            interfaceId == 0x2a55205a;   // ERC2981 Royalty
    }
    
    /**
     * @dev Internal helper
     */
    function _isApprovedOrOwner(address spender, uint256 tokenId) internal view returns (bool) {
        address owner_ = ownerOf(tokenId);
        return (spender == owner_ || _tokenApprovals[tokenId] == spender || _operatorApprovals[owner_][spender]);
    }
    
    /**
     * @dev Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        owner = newOwner;
    }
}
