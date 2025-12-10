// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IMusicNFT {
    function royaltyInfo(uint256 tokenId, uint256 salePrice) external view returns (address, uint256);
    function ownerOf(uint256 tokenId) external view returns (address);
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}

/**
 * @title RoyaltyDistributor
 * @dev Automatic Artist Royalty Distribution
 * 
 * Features:
 * - NFT sale tracking
 * - Automatic royalty splits based on ERC-2981
 * - Multi-recipient support (collaborations)
 * - Payment processing in TRX or DCMX tokens
 */
contract RoyaltyDistributor {
    address public owner;
    IMusicNFT public musicNFT;
    IERC20 public dcmxToken;
    
    struct Sale {
        uint256 tokenId;
        address seller;
        address buyer;
        uint256 salePrice;
        uint256 royaltyAmount;
        address royaltyRecipient;
        uint256 timestamp;
        bool royaltyPaid;
        address paymentToken;  // address(0) for TRX, token address for ERC20
    }
    
    struct RoyaltySplit {
        address recipient;
        uint96 bps;  // Basis points (10000 = 100%)
    }
    
    // Sale ID => Sale
    mapping(uint256 => Sale) public sales;
    uint256 private _saleCounter;
    
    // Token ID => RoyaltySplit[] (for collaborations)
    mapping(uint256 => RoyaltySplit[]) public royaltySplits;
    
    // Artist => Total royalties earned (in TRX)
    mapping(address => uint256) public totalRoyaltiesEarned;
    
    // Platform fee (basis points)
    uint96 public platformFeeBps = 250;  // 2.5%
    address public platformWallet;
    
    event SaleRecorded(
        uint256 indexed saleId,
        uint256 indexed tokenId,
        address indexed seller,
        address buyer,
        uint256 salePrice,
        uint256 royaltyAmount
    );
    
    event RoyaltyPaid(
        uint256 indexed saleId,
        uint256 indexed tokenId,
        address indexed recipient,
        uint256 amount
    );
    
    event RoyaltySplitSet(
        uint256 indexed tokenId,
        address[] recipients,
        uint96[] shares
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    constructor(address _musicNFT, address _dcmxToken, address _platformWallet) {
        owner = msg.sender;
        musicNFT = IMusicNFT(_musicNFT);
        dcmxToken = IERC20(_dcmxToken);
        platformWallet = _platformWallet;
    }
    
    /**
     * @dev Record an NFT sale and calculate royalty
     */
    function recordSale(
        uint256 tokenId,
        address seller,
        address buyer,
        uint256 salePrice,
        address paymentToken
    ) external returns (uint256) {
        require(seller != address(0) && buyer != address(0), "Invalid addresses");
        require(salePrice > 0, "Invalid price");
        
        // Get royalty info from NFT contract
        (address royaltyRecipient, uint256 royaltyAmount) = musicNFT.royaltyInfo(tokenId, salePrice);
        
        _saleCounter++;
        uint256 saleId = _saleCounter;
        
        sales[saleId] = Sale({
            tokenId: tokenId,
            seller: seller,
            buyer: buyer,
            salePrice: salePrice,
            royaltyAmount: royaltyAmount,
            royaltyRecipient: royaltyRecipient,
            timestamp: block.timestamp,
            royaltyPaid: false,
            paymentToken: paymentToken
        });
        
        emit SaleRecorded(saleId, tokenId, seller, buyer, salePrice, royaltyAmount);
        
        return saleId;
    }
    
    /**
     * @dev Execute royalty payment for a sale
     */
    function payRoyalty(uint256 saleId) external payable {
        Sale storage sale = sales[saleId];
        require(!sale.royaltyPaid, "Already paid");
        require(sale.salePrice > 0, "Sale not found");
        
        // Calculate platform fee
        uint256 platformFee = (sale.salePrice * platformFeeBps) / 10000;
        uint256 sellerAmount = sale.salePrice - sale.royaltyAmount - platformFee;
        
        if (sale.paymentToken == address(0)) {
            // TRX payment
            require(msg.value == sale.salePrice, "Incorrect payment");
            
            // Pay platform fee
            payable(platformWallet).transfer(platformFee);
            
            // Pay royalty
            if (royaltySplits[sale.tokenId].length > 0) {
                _distributeRoyaltySplits(sale.tokenId, sale.royaltyAmount);
            } else {
                payable(sale.royaltyRecipient).transfer(sale.royaltyAmount);
                totalRoyaltiesEarned[sale.royaltyRecipient] += sale.royaltyAmount;
            }
            
            // Pay seller
            payable(sale.seller).transfer(sellerAmount);
            
        } else {
            // Token payment (DCMX or other)
            IERC20 token = IERC20(sale.paymentToken);
            
            // Transfer from buyer
            require(
                token.transferFrom(msg.sender, address(this), sale.salePrice),
                "Transfer failed"
            );
            
            // Pay platform fee
            require(token.transfer(platformWallet, platformFee), "Platform fee failed");
            
            // Pay royalty
            if (royaltySplits[sale.tokenId].length > 0) {
                _distributeRoyaltySplitsToken(sale.tokenId, sale.royaltyAmount, token);
            } else {
                require(token.transfer(sale.royaltyRecipient, sale.royaltyAmount), "Royalty failed");
                totalRoyaltiesEarned[sale.royaltyRecipient] += sale.royaltyAmount;
            }
            
            // Pay seller
            require(token.transfer(sale.seller, sellerAmount), "Seller payment failed");
        }
        
        sale.royaltyPaid = true;
        emit RoyaltyPaid(saleId, sale.tokenId, sale.royaltyRecipient, sale.royaltyAmount);
    }
    
    /**
     * @dev Distribute royalty to multiple recipients (TRX)
     */
    function _distributeRoyaltySplits(uint256 tokenId, uint256 totalRoyalty) internal {
        RoyaltySplit[] storage splits = royaltySplits[tokenId];
        
        for (uint256 i = 0; i < splits.length; i++) {
            uint256 amount = (totalRoyalty * splits[i].bps) / 10000;
            payable(splits[i].recipient).transfer(amount);
            totalRoyaltiesEarned[splits[i].recipient] += amount;
        }
    }
    
    /**
     * @dev Distribute royalty to multiple recipients (Token)
     */
    function _distributeRoyaltySplitsToken(
        uint256 tokenId,
        uint256 totalRoyalty,
        IERC20 token
    ) internal {
        RoyaltySplit[] storage splits = royaltySplits[tokenId];
        
        for (uint256 i = 0; i < splits.length; i++) {
            uint256 amount = (totalRoyalty * splits[i].bps) / 10000;
            require(token.transfer(splits[i].recipient, amount), "Split transfer failed");
            totalRoyaltiesEarned[splits[i].recipient] += amount;
        }
    }
    
    /**
     * @dev Set royalty splits for a token (for collaborations)
     */
    function setRoyaltySplits(
        uint256 tokenId,
        address[] memory recipients,
        uint96[] memory shares
    ) external {
        require(recipients.length == shares.length, "Length mismatch");
        require(recipients.length > 0, "Empty splits");
        
        // Verify caller is NFT owner or contract owner
        address tokenOwner = musicNFT.ownerOf(tokenId);
        require(msg.sender == tokenOwner || msg.sender == owner, "Not authorized");
        
        // Verify shares sum to 10000 (100%)
        uint256 totalShares = 0;
        for (uint256 i = 0; i < shares.length; i++) {
            totalShares += shares[i];
        }
        require(totalShares == 10000, "Shares must sum to 100%");
        
        // Clear existing splits
        delete royaltySplits[tokenId];
        
        // Set new splits
        for (uint256 i = 0; i < recipients.length; i++) {
            royaltySplits[tokenId].push(RoyaltySplit({
                recipient: recipients[i],
                bps: shares[i]
            }));
        }
        
        emit RoyaltySplitSet(tokenId, recipients, shares);
    }
    
    /**
     * @dev Get royalty splits for a token
     */
    function getRoyaltySplits(uint256 tokenId) external view returns (
        address[] memory recipients,
        uint96[] memory shares
    ) {
        RoyaltySplit[] storage splits = royaltySplits[tokenId];
        uint256 length = splits.length;
        
        recipients = new address[](length);
        shares = new uint96[](length);
        
        for (uint256 i = 0; i < length; i++) {
            recipients[i] = splits[i].recipient;
            shares[i] = splits[i].bps;
        }
    }
    
    /**
     * @dev Get sale details
     */
    function getSale(uint256 saleId) external view returns (
        uint256 tokenId,
        address seller,
        address buyer,
        uint256 salePrice,
        uint256 royaltyAmount,
        bool royaltyPaid
    ) {
        Sale memory sale = sales[saleId];
        return (
            sale.tokenId,
            sale.seller,
            sale.buyer,
            sale.salePrice,
            sale.royaltyAmount,
            sale.royaltyPaid
        );
    }
    
    /**
     * @dev Update platform fee
     */
    function setPlatformFee(uint96 newFeeBps) external onlyOwner {
        require(newFeeBps <= 1000, "Fee too high"); // Max 10%
        platformFeeBps = newFeeBps;
    }
    
    /**
     * @dev Update platform wallet
     */
    function setPlatformWallet(address newWallet) external onlyOwner {
        require(newWallet != address(0), "Invalid wallet");
        platformWallet = newWallet;
    }
    
    /**
     * @dev Total sales count
     */
    function totalSales() external view returns (uint256) {
        return _saleCounter;
    }
    
    /**
     * @dev Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        owner = newOwner;
    }
}
