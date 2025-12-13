// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title DCMXToken
 * @dev TRC-20 Platform Utility Token for DCMX
 * 
 * Features:
 * - Fixed/configurable total supply
 * - Minting for reward claims (controlled by RewardVault)
 * - Burning for platform fees
 * - 18 decimals standard
 */
contract DCMXToken {
    string public constant name = "DCMX Token";
    string public constant symbol = "DCMX";
    uint8 public constant decimals = 18;
    
    uint256 public totalSupply;
    uint256 public maxSupply;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    address public owner;
    mapping(address => bool) public minters;  // Authorized minters (e.g., RewardVault)
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Mint(address indexed to, uint256 amount);
    event Burn(address indexed from, uint256 amount);
    event MinterAdded(address indexed minter);
    event MinterRemoved(address indexed minter);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier onlyMinter() {
        require(minters[msg.sender], "Not authorized minter");
        _;
    }
    
    constructor(uint256 _initialSupply, uint256 _maxSupply) {
        owner = msg.sender;
        maxSupply = _maxSupply;
        
        if (_initialSupply > 0) {
            require(_initialSupply <= _maxSupply, "Initial supply exceeds max");
            totalSupply = _initialSupply;
            balanceOf[msg.sender] = _initialSupply;
            emit Transfer(address(0), msg.sender, _initialSupply);
        }
    }
    
    function transfer(address to, uint256 value) public returns (bool) {
        require(to != address(0), "Invalid recipient");
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        
        emit Transfer(msg.sender, to, value);
        return true;
    }
    
    function approve(address spender, uint256 value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }
    
    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(to != address(0), "Invalid recipient");
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Insufficient allowance");
        
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        
        emit Transfer(from, to, value);
        return true;
    }
    
    /**
     * @dev Mint new tokens for rewards
     * Only authorized minters (RewardVault) can call this
     */
    function mint(address to, uint256 amount) external onlyMinter returns (bool) {
        require(to != address(0), "Invalid recipient");
        require(totalSupply + amount <= maxSupply, "Exceeds max supply");
        
        totalSupply += amount;
        balanceOf[to] += amount;
        
        emit Mint(to, amount);
        emit Transfer(address(0), to, amount);
        return true;
    }
    
    /**
     * @dev Burn tokens for platform fees
     */
    function burn(uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        
        balanceOf[msg.sender] -= amount;
        totalSupply -= amount;
        
        emit Burn(msg.sender, amount);
        emit Transfer(msg.sender, address(0), amount);
        return true;
    }
    
    /**
     * @dev Add authorized minter
     */
    function addMinter(address minter) external onlyOwner {
        require(minter != address(0), "Invalid minter");
        minters[minter] = true;
        emit MinterAdded(minter);
    }
    
    /**
     * @dev Remove authorized minter
     */
    function removeMinter(address minter) external onlyOwner {
        minters[minter] = false;
        emit MinterRemoved(minter);
    }
    
    /**
     * @dev Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid owner");
        owner = newOwner;
    }
}
