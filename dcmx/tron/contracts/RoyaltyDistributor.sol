// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title RoyaltyDistributor
 * @dev Manages NFT sales and automatic royalty distribution
 * 
 * Features:
 * - Track NFT sales and prices
 * - Automatic royalty calculation
 * - Multi-recipient payment splitting
 * - Withdraw mechanism for recipients
 */
contract RoyaltyDistributor {
    address public admin;
    
    struct Sale {
        uint256 nftTokenId;
        address nftContract;
        address seller;
        address buyer;
        uint256 salePrice;
        uint256 timestamp;
        bool royaltiesDistributed;
    }
    
    struct RoyaltySplit {
        address recipient;
        uint256 percentage;  // Basis points (100 = 1%)
    }
    
    // Sale ID => Sale record
    mapping(uint256 => Sale) public sales;
    uint256 private _saleIdCounter;
    
    // NFT contract => Token ID => Royalty splits
    mapping(address => mapping(uint256 => RoyaltySplit[])) public royaltySplits;
    
    // Recipient => Pending balance
    mapping(address => uint256) public pendingWithdrawals;
    
    event SaleRecorded(
        uint256 indexed saleId,
        address indexed nftContract,
        uint256 indexed nftTokenId,
        address seller,
        address buyer,
        uint256 salePrice
    );
    
    event RoyaltiesDistributed(
        uint256 indexed saleId,
        uint256 totalRoyalties
    );
    
    event RoyaltyPaid(
        address indexed recipient,
        uint256 amount
    );
    
    event Withdrawal(
        address indexed recipient,
        uint256 amount
    );
    
    event RoyaltySplitSet(
        address indexed nftContract,
        uint256 indexed nftTokenId,
        address recipient,
        uint256 percentage
    );
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    constructor() {
        admin = msg.sender;
    }
    
    function setRoyaltySplit(
        address nftContract,
        uint256 nftTokenId,
        address[] memory recipients,
        uint256[] memory percentages
    ) public onlyAdmin {
        require(recipients.length == percentages.length, "Length mismatch");
        require(recipients.length > 0, "No recipients");
        
        // Verify percentages sum to <= 10000 (100%)
        uint256 totalPercentage = 0;
        for (uint256 i = 0; i < percentages.length; i++) {
            totalPercentage += percentages[i];
        }
        require(totalPercentage <= 10000, "Percentage exceeds 100%");
        
        // Clear existing splits
        delete royaltySplits[nftContract][nftTokenId];
        
        // Set new splits
        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Invalid recipient");
            
            royaltySplits[nftContract][nftTokenId].push(RoyaltySplit({
                recipient: recipients[i],
                percentage: percentages[i]
            }));
            
            emit RoyaltySplitSet(
                nftContract,
                nftTokenId,
                recipients[i],
                percentages[i]
            );
        }
    }
    
    function recordSale(
        address nftContract,
        uint256 nftTokenId,
        address seller,
        address buyer,
        uint256 salePrice
    ) public payable onlyAdmin returns (uint256) {
        require(nftContract != address(0), "Invalid contract");
        require(seller != address(0) && buyer != address(0), "Invalid addresses");
        require(salePrice > 0, "Invalid price");
        
        uint256 saleId = _saleIdCounter++;
        
        sales[saleId] = Sale({
            nftTokenId: nftTokenId,
            nftContract: nftContract,
            seller: seller,
            buyer: buyer,
            salePrice: salePrice,
            timestamp: block.timestamp,
            royaltiesDistributed: false
        });
        
        emit SaleRecorded(
            saleId,
            nftContract,
            nftTokenId,
            seller,
            buyer,
            salePrice
        );
        
        return saleId;
    }
    
    function distributeRoyalties(uint256 saleId) public payable onlyAdmin {
        Sale storage sale = sales[saleId];
        require(sale.timestamp > 0, "Sale not found");
        require(!sale.royaltiesDistributed, "Already distributed");
        
        RoyaltySplit[] memory splits = royaltySplits[sale.nftContract][sale.nftTokenId];
        require(splits.length > 0, "No royalty splits configured");
        
        uint256 totalRoyalties = 0;
        
        // Calculate and distribute to each recipient
        for (uint256 i = 0; i < splits.length; i++) {
            uint256 amount = (sale.salePrice * splits[i].percentage) / 10000;
            
            if (amount > 0) {
                pendingWithdrawals[splits[i].recipient] += amount;
                totalRoyalties += amount;
                
                emit RoyaltyPaid(splits[i].recipient, amount);
            }
        }
        
        sale.royaltiesDistributed = true;
        
        emit RoyaltiesDistributed(saleId, totalRoyalties);
    }
    
    function withdrawRoyalties() public {
        uint256 amount = pendingWithdrawals[msg.sender];
        require(amount > 0, "No pending withdrawals");
        
        pendingWithdrawals[msg.sender] = 0;
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        emit Withdrawal(msg.sender, amount);
    }
    
    function getRoyaltyInfo(address nftContract, uint256 nftTokenId)
        public
        view
        returns (RoyaltySplit[] memory)
    {
        return royaltySplits[nftContract][nftTokenId];
    }
    
    function getPendingRoyalties(address recipient)
        public
        view
        returns (uint256)
    {
        return pendingWithdrawals[recipient];
    }
    
    function getSale(uint256 saleId)
        public
        view
        returns (Sale memory)
    {
        return sales[saleId];
    }
    
    // Allow contract to receive TRX
    receive() external payable {}
}
