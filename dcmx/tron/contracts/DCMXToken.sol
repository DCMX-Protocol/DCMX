// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title DCMXToken
 * @dev TRC-20 utility token for DCMX platform
 * 
 * Token Economics:
 * - Fixed supply: 1,000,000,000 tokens
 * - Decimals: 18
 * - Utility: Platform fees, governance voting, reward distribution
 * - NOT an investment security - pure utility token
 */
contract DCMXToken {
    string public name = "DCMX";
    string public symbol = "DCMX";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**18;
    
    address public admin;
    bool public mintingFinished = false;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Mint(address indexed to, uint256 value);
    event Burn(address indexed from, uint256 value);
    event MintingFinished();
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    modifier canMint() {
        require(!mintingFinished, "Minting finished");
        _;
    }
    
    constructor(uint256 initialSupply) {
        require(initialSupply <= MAX_SUPPLY, "Exceeds max supply");
        admin = msg.sender;
        totalSupply = initialSupply;
        balanceOf[admin] = initialSupply;
        emit Transfer(address(0), admin, initialSupply);
    }
    
    function transfer(address to, uint256 value) public returns (bool) {
        require(to != address(0), "Invalid address");
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
        require(to != address(0), "Invalid address");
        require(balanceOf[from] >= value, "Insufficient balance");
        require(allowance[from][msg.sender] >= value, "Insufficient allowance");
        
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        
        emit Transfer(from, to, value);
        return true;
    }
    
    function mint(address to, uint256 value) public onlyAdmin canMint returns (bool) {
        require(to != address(0), "Invalid address");
        require(totalSupply + value <= MAX_SUPPLY, "Exceeds max supply");
        
        totalSupply += value;
        balanceOf[to] += value;
        
        emit Mint(to, value);
        emit Transfer(address(0), to, value);
        return true;
    }
    
    function burn(uint256 value) public returns (bool) {
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        
        balanceOf[msg.sender] -= value;
        totalSupply -= value;
        
        emit Burn(msg.sender, value);
        emit Transfer(msg.sender, address(0), value);
        return true;
    }
    
    function finishMinting() public onlyAdmin canMint returns (bool) {
        mintingFinished = true;
        emit MintingFinished();
        return true;
    }
}
