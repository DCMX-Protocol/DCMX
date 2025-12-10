// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title MusicNFT
 * @dev TRC-721 NFT for music tracks with edition tracking and royalties
 * 
 * Features:
 * - Limited edition support (e.g., 100 copies of a song)
 * - Royalty tracking (ERC-2981 compatible)
 * - Content hash storage for integrity
 * - Metadata storage (title, artist, album)
 */
contract MusicNFT {
    string public name = "DCMX Music NFT";
    string public symbol = "DCMX-NFT";
    
    address public admin;
    uint256 private _tokenIdCounter;
    
    struct NFTMetadata {
        string title;
        string artist;
        string contentHash;
        uint256 edition;
        uint256 maxEditions;
        uint256 royaltyBps;  // Basis points (100 = 1%)
        address royaltyRecipient;
    }
    
    // Token ID => Owner
    mapping(uint256 => address) public ownerOf;
    
    // Owner => Token count
    mapping(address => uint256) public balanceOf;
    
    // Token ID => Approved address
    mapping(uint256 => address) public getApproved;
    
    // Owner => Operator => Approved
    mapping(address => mapping(address => bool)) public isApprovedForAll;
    
    // Token ID => Metadata
    mapping(uint256 => NFTMetadata) public tokenMetadata;
    
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    event Minted(address indexed to, uint256 indexed tokenId, string contentHash);
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    modifier onlyOwnerOf(uint256 tokenId) {
        require(ownerOf[tokenId] == msg.sender, "Not token owner");
        _;
    }
    
    constructor() {
        admin = msg.sender;
    }
    
    function mint(
        address to,
        string memory title,
        string memory artist,
        string memory contentHash,
        uint256 edition,
        uint256 maxEditions,
        uint256 royaltyBps,
        address royaltyRecipient
    ) public onlyAdmin returns (uint256) {
        require(to != address(0), "Invalid address");
        require(edition > 0 && edition <= maxEditions, "Invalid edition");
        require(royaltyBps <= 10000, "Royalty too high");
        
        uint256 tokenId = _tokenIdCounter++;
        
        ownerOf[tokenId] = to;
        balanceOf[to]++;
        
        tokenMetadata[tokenId] = NFTMetadata({
            title: title,
            artist: artist,
            contentHash: contentHash,
            edition: edition,
            maxEditions: maxEditions,
            royaltyBps: royaltyBps,
            royaltyRecipient: royaltyRecipient
        });
        
        emit Transfer(address(0), to, tokenId);
        emit Minted(to, tokenId, contentHash);
        
        return tokenId;
    }
    
    function transfer(address to, uint256 tokenId) public {
        require(ownerOf[tokenId] == msg.sender, "Not owner");
        require(to != address(0), "Invalid address");
        
        _transfer(msg.sender, to, tokenId);
    }
    
    function transferFrom(address from, address to, uint256 tokenId) public {
        require(to != address(0), "Invalid address");
        require(ownerOf[tokenId] == from, "Not owner");
        require(
            msg.sender == from ||
            getApproved[tokenId] == msg.sender ||
            isApprovedForAll[from][msg.sender],
            "Not authorized"
        );
        
        _transfer(from, to, tokenId);
    }
    
    function approve(address to, uint256 tokenId) public onlyOwnerOf(tokenId) {
        getApproved[tokenId] = to;
        emit Approval(msg.sender, to, tokenId);
    }
    
    function setApprovalForAll(address operator, bool approved) public {
        isApprovedForAll[msg.sender][operator] = approved;
        emit ApprovalForAll(msg.sender, operator, approved);
    }
    
    function _transfer(address from, address to, uint256 tokenId) private {
        balanceOf[from]--;
        balanceOf[to]++;
        ownerOf[tokenId] = to;
        delete getApproved[tokenId];
        
        emit Transfer(from, to, tokenId);
    }
    
    function royaltyInfo(uint256 tokenId, uint256 salePrice)
        external
        view
        returns (address receiver, uint256 royaltyAmount)
    {
        NFTMetadata memory metadata = tokenMetadata[tokenId];
        receiver = metadata.royaltyRecipient;
        royaltyAmount = (salePrice * metadata.royaltyBps) / 10000;
    }
    
    function tokenURI(uint256 tokenId) public view returns (string memory) {
        require(ownerOf[tokenId] != address(0), "Token doesn't exist");
        NFTMetadata memory metadata = tokenMetadata[tokenId];
        
        // Return basic metadata (in production, return IPFS URI)
        return string(abi.encodePacked(
            "data:application/json,{",
            '"title":"', metadata.title, '",',
            '"artist":"', metadata.artist, '",',
            '"contentHash":"', metadata.contentHash, '",',
            '"edition":', _uint2str(metadata.edition), ',',
            '"maxEditions":', _uint2str(metadata.maxEditions),
            "}"
        ));
    }
    
    function _uint2str(uint256 _i) private pure returns (string memory) {
        if (_i == 0) return "0";
        
        uint256 j = _i;
        uint256 len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        
        bytes memory bstr = new bytes(len);
        uint256 k = len;
        while (_i != 0) {
            k = k - 1;
            uint8 temp = (48 + uint8(_i - _i / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        
        return string(bstr);
    }
}
