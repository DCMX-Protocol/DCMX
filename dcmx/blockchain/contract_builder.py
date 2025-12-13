"""
Smart Contract Builder SDK

Allows artists/customers to create custom smart contracts with safety guardrails.
Provides templates, validation, and deployment tools.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import hashlib
from pathlib import Path


class ContractType(Enum):
    """Supported smart contract types."""
    ROYALTY_SPLIT = "royalty_split"
    TIME_LOCKED_RELEASE = "time_locked_release"
    AUCTION = "auction"
    SUBSCRIPTION = "subscription"
    VOTING = "voting"
    CUSTOM = "custom"


class SecurityLevel(Enum):
    """Security validation levels."""
    BASIC = "basic"  # Simple validation only
    STANDARD = "standard"  # Recommended for most contracts
    STRICT = "strict"  # Full audit required
    VERIFIED = "verified"  # Professionally audited


@dataclass
class ContractParameter:
    """Smart contract parameter definition."""
    name: str
    param_type: str  # "address", "uint256", "string", "bool", etc.
    description: str
    default_value: Optional[Any] = None
    required: bool = True
    validation_rule: Optional[str] = None  # Regex or custom rule
    
    def validate(self, value: Any) -> bool:
        """Validate parameter value."""
        if self.required and value is None:
            return False
        
        if self.validation_rule and value:
            # Basic regex validation
            if isinstance(value, str):
                return bool(re.match(self.validation_rule, value))
        
        return True


@dataclass
class ContractTemplate:
    """Smart contract template."""
    name: str
    contract_type: ContractType
    description: str
    solidity_template: str
    parameters: List[ContractParameter]
    security_level: SecurityLevel
    gas_estimate: int
    audit_required: bool = False
    
    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate all parameters."""
        errors = []
        
        for param in self.parameters:
            if param.name not in params:
                if param.required:
                    errors.append(f"Missing required parameter: {param.name}")
                continue
            
            if not param.validate(params[param.name]):
                errors.append(f"Invalid value for {param.name}")
        
        return len(errors) == 0, errors
    
    def generate_contract(self, params: Dict[str, Any]) -> str:
        """Generate Solidity contract from template."""
        valid, errors = self.validate_parameters(params)
        if not valid:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")
        
        # Substitute parameters into template
        contract_code = self.solidity_template
        for key, value in params.items():
            placeholder = f"{{{{ {key} }}}}"
            contract_code = contract_code.replace(placeholder, str(value))
        
        return contract_code


@dataclass
class SecurityValidation:
    """Security validation result."""
    passed: bool
    security_level: SecurityLevel
    issues: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    gas_estimate: Optional[int] = None
    audit_required: bool = False
    
    def add_issue(self, severity: str, description: str, line: Optional[int] = None):
        """Add security issue."""
        self.issues.append({
            "severity": severity,
            "description": description,
            "line": line,
        })
        if severity in ["critical", "high"]:
            self.passed = False
            self.audit_required = True


class ContractValidator:
    """Validates smart contracts for security issues."""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = {
        r"selfdestruct": "Use of selfdestruct is not allowed",
        r"delegatecall": "Use of delegatecall requires audit",
        r"tx\.origin": "tx.origin authentication is vulnerable",
        r"block\.timestamp": "block.timestamp manipulation possible",
        r"transfer\(": "Use call instead of transfer for gas forwarding",
    }
    
    # Required patterns for safety
    REQUIRED_PATTERNS = {
        r"require\(": "Missing require statements for input validation",
        r"ReentrancyGuard": "Missing reentrancy protection",
    }
    
    # Gas optimization issues
    GAS_ISSUES = {
        r"for\s*\(.*\)": "Unbounded loops can cause out-of-gas",
        r"storage\s+\w+\s*\[": "Storage arrays can be expensive",
    }
    
    def validate_contract(
        self,
        contract_code: str,
        security_level: SecurityLevel = SecurityLevel.STANDARD
    ) -> SecurityValidation:
        """
        Validate smart contract code for security issues.
        
        Args:
            contract_code: Solidity contract source code
            security_level: Validation strictness level
            
        Returns:
            SecurityValidation with issues and recommendations
        """
        validation = SecurityValidation(
            passed=True,
            security_level=security_level,
        )
        
        lines = contract_code.split('\n')
        
        # Check for dangerous patterns
        for i, line in enumerate(lines, 1):
            for pattern, message in self.DANGEROUS_PATTERNS.items():
                if re.search(pattern, line, re.IGNORECASE):
                    severity = "critical" if pattern in ["selfdestruct", "delegatecall"] else "high"
                    validation.add_issue(severity, message, i)
        
        # Check for required patterns (if STANDARD or STRICT)
        if security_level in [SecurityLevel.STANDARD, SecurityLevel.STRICT]:
            for pattern, message in self.REQUIRED_PATTERNS.items():
                if not re.search(pattern, contract_code, re.IGNORECASE):
                    validation.add_issue("medium", message)
        
        # Check for gas issues (warnings only)
        for i, line in enumerate(lines, 1):
            for pattern, message in self.GAS_ISSUES.items():
                if re.search(pattern, line):
                    validation.warnings.append(f"Line {i}: {message}")
        
        # Strict mode requires audit for any issues
        if security_level == SecurityLevel.STRICT and len(validation.issues) > 0:
            validation.audit_required = True
        
        # Estimate gas (simplified)
        validation.gas_estimate = self._estimate_gas(contract_code)
        
        return validation
    
    def _estimate_gas(self, contract_code: str) -> int:
        """Estimate deployment gas cost."""
        # Simple estimate based on code size
        base_cost = 21000  # Transaction base cost
        code_size_cost = len(contract_code.encode()) * 200  # ~200 gas per byte
        
        # Add costs for storage variables
        storage_vars = len(re.findall(r'\s+(uint|address|bool|string)\s+\w+\s*;', contract_code))
        storage_cost = storage_vars * 20000  # ~20k gas per storage slot
        
        return base_cost + code_size_cost + storage_cost


class ContractBuilder:
    """
    Smart Contract Builder SDK for artists/customers.
    
    Provides safe contract creation with templates and validation.
    """
    
    def __init__(self):
        self.templates: Dict[str, ContractTemplate] = {}
        self.validator = ContractValidator()
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load built-in contract templates."""
        
        # Template 1: Royalty Split Contract
        royalty_split_template = ContractTemplate(
            name="Royalty Split",
            contract_type=ContractType.ROYALTY_SPLIT,
            description="Split royalties among multiple recipients automatically",
            solidity_template="""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract RoyaltySplit is ReentrancyGuard, Ownable {
    string public trackName = "{{ track_name }}";
    
    struct Recipient {
        address payable wallet;
        uint256 percentage; // In basis points (1% = 100)
    }
    
    Recipient[] public recipients;
    uint256 public totalReceived;
    
    event RoyaltyDistributed(uint256 amount, uint256 timestamp);
    
    constructor(
        address[] memory _wallets,
        uint256[] memory _percentages
    ) {
        require(_wallets.length == _percentages.length, "Arrays must match");
        require(_wallets.length <= {{ max_recipients }}, "Too many recipients");
        
        uint256 totalPercentage = 0;
        for (uint256 i = 0; i < _wallets.length; i++) {
            require(_wallets[i] != address(0), "Invalid address");
            require(_percentages[i] > 0, "Percentage must be > 0");
            
            recipients.push(Recipient({
                wallet: payable(_wallets[i]),
                percentage: _percentages[i]
            }));
            totalPercentage += _percentages[i];
        }
        
        require(totalPercentage == 10000, "Percentages must sum to 100%");
    }
    
    receive() external payable {
        totalReceived += msg.value;
        distributeRoyalties();
    }
    
    function distributeRoyalties() public nonReentrant {
        require(address(this).balance > 0, "No balance");
        
        uint256 balance = address(this).balance;
        
        for (uint256 i = 0; i < recipients.length; i++) {
            uint256 amount = (balance * recipients[i].percentage) / 10000;
            (bool success, ) = recipients[i].wallet.call{value: amount}("");
            require(success, "Transfer failed");
        }
        
        emit RoyaltyDistributed(balance, block.timestamp);
    }
    
    function getRecipients() external view returns (Recipient[] memory) {
        return recipients;
    }
}
""",
            parameters=[
                ContractParameter(
                    name="track_name",
                    param_type="string",
                    description="Name of the track",
                    required=True,
                ),
                ContractParameter(
                    name="max_recipients",
                    param_type="uint256",
                    description="Maximum number of royalty recipients",
                    default_value=10,
                    required=True,
                ),
            ],
            security_level=SecurityLevel.STANDARD,
            gas_estimate=350000,
            audit_required=False,
        )
        
        self.templates["royalty_split"] = royalty_split_template
        
        # Template 2: Time-Locked Release
        time_locked_template = ContractTemplate(
            name="Time-Locked Release",
            contract_type=ContractType.TIME_LOCKED_RELEASE,
            description="Release content at a specific time",
            solidity_template="""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract TimeLockedRelease is Ownable {
    string public trackName = "{{ track_name }}";
    string public ipfsCID;
    uint256 public releaseTime;
    bool public released = false;
    
    event ContentReleased(string ipfsCID, uint256 timestamp);
    
    constructor(
        uint256 _releaseTime
    ) {
        require(_releaseTime > block.timestamp, "Release time must be in future");
        releaseTime = _releaseTime;
    }
    
    function setContent(string memory _ipfsCID) external onlyOwner {
        require(!released, "Already released");
        require(bytes(_ipfsCID).length > 0, "Invalid CID");
        ipfsCID = _ipfsCID;
    }
    
    function release() external {
        require(block.timestamp >= releaseTime, "Not yet time");
        require(!released, "Already released");
        require(bytes(ipfsCID).length > 0, "Content not set");
        
        released = true;
        emit ContentReleased(ipfsCID, block.timestamp);
    }
    
    function getContent() external view returns (string memory) {
        require(released || msg.sender == owner(), "Not released yet");
        return ipfsCID;
    }
    
    function timeUntilRelease() external view returns (uint256) {
        if (block.timestamp >= releaseTime) return 0;
        return releaseTime - block.timestamp;
    }
}
""",
            parameters=[
                ContractParameter(
                    name="track_name",
                    param_type="string",
                    description="Name of the track",
                    required=True,
                ),
            ],
            security_level=SecurityLevel.STANDARD,
            gas_estimate=280000,
            audit_required=False,
        )
        
        self.templates["time_locked_release"] = time_locked_template
        
        # Template 3: Auction Contract
        auction_template = ContractTemplate(
            name="NFT Auction",
            contract_type=ContractType.AUCTION,
            description="Auction your music NFT to highest bidder",
            solidity_template="""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

contract NFTAuction is ReentrancyGuard {
    address public seller;
    address public nftContract;
    uint256 public tokenId;
    uint256 public endTime;
    uint256 public minBid = {{ min_bid }};
    
    address public highestBidder;
    uint256 public highestBid;
    mapping(address => uint256) public pendingReturns;
    
    bool public ended = false;
    
    event NewBid(address bidder, uint256 amount);
    event AuctionEnded(address winner, uint256 amount);
    
    constructor(
        address _nftContract,
        uint256 _tokenId,
        uint256 _duration
    ) {
        seller = msg.sender;
        nftContract = _nftContract;
        tokenId = _tokenId;
        endTime = block.timestamp + _duration;
        
        // Verify seller owns NFT
        require(
            IERC721(_nftContract).ownerOf(_tokenId) == seller,
            "Seller must own NFT"
        );
    }
    
    function bid() external payable nonReentrant {
        require(block.timestamp < endTime, "Auction ended");
        require(msg.value >= minBid, "Bid too low");
        require(msg.value > highestBid, "Bid not high enough");
        
        if (highestBidder != address(0)) {
            pendingReturns[highestBidder] += highestBid;
        }
        
        highestBidder = msg.sender;
        highestBid = msg.value;
        
        emit NewBid(msg.sender, msg.value);
    }
    
    function withdraw() external nonReentrant {
        uint256 amount = pendingReturns[msg.sender];
        require(amount > 0, "No funds to withdraw");
        
        pendingReturns[msg.sender] = 0;
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Withdrawal failed");
    }
    
    function endAuction() external nonReentrant {
        require(block.timestamp >= endTime, "Auction not ended");
        require(!ended, "Already ended");
        
        ended = true;
        
        if (highestBidder != address(0)) {
            // Transfer NFT to winner
            IERC721(nftContract).transferFrom(seller, highestBidder, tokenId);
            
            // Transfer funds to seller
            (bool success, ) = seller.call{value: highestBid}("");
            require(success, "Payment failed");
            
            emit AuctionEnded(highestBidder, highestBid);
        } else {
            emit AuctionEnded(address(0), 0);
        }
    }
}
""",
            parameters=[
                ContractParameter(
                    name="min_bid",
                    param_type="uint256",
                    description="Minimum bid in wei",
                    default_value="1000000000000000000",  # 1 ETH
                    required=True,
                ),
            ],
            security_level=SecurityLevel.STANDARD,
            gas_estimate=420000,
            audit_required=True,  # Auctions handle funds, need audit
        )
        
        self.templates["auction"] = auction_template
    
    def get_template(self, template_name: str) -> Optional[ContractTemplate]:
        """Get contract template by name."""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        return [
            {
                "name": template.name,
                "type": template.contract_type.value,
                "description": template.description,
                "security_level": template.security_level.value,
                "gas_estimate": template.gas_estimate,
                "audit_required": template.audit_required,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.param_type,
                        "description": p.description,
                        "required": p.required,
                        "default": p.default_value,
                    }
                    for p in template.parameters
                ],
            }
            for template in self.templates.values()
        ]
    
    def build_contract(
        self,
        template_name: str,
        parameters: Dict[str, Any],
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Build a smart contract from template.
        
        Args:
            template_name: Name of template to use
            parameters: Contract parameters
            validate: Whether to run security validation
            
        Returns:
            Dict with contract code, validation results, deployment info
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template not found: {template_name}")
        
        # Generate contract code
        contract_code = template.generate_contract(parameters)
        
        result = {
            "template": template_name,
            "contract_code": contract_code,
            "parameters": parameters,
            "security_level": template.security_level.value,
            "gas_estimate": template.gas_estimate,
        }
        
        # Validate if requested
        if validate:
            validation = self.validator.validate_contract(
                contract_code,
                template.security_level
            )
            result["validation"] = {
                "passed": validation.passed,
                "issues": validation.issues,
                "warnings": validation.warnings,
                "audit_required": validation.audit_required,
                "gas_estimate": validation.gas_estimate,
            }
        
        # Generate deployment metadata
        contract_hash = hashlib.sha256(contract_code.encode()).hexdigest()
        result["metadata"] = {
            "contract_hash": contract_hash,
            "template_version": "1.0.0",
            "created_at": "{{ timestamp }}",
            "audit_required": template.audit_required or (validate and validation.audit_required),
        }
        
        return result
    
    def validate_custom_contract(
        self,
        contract_code: str,
        security_level: SecurityLevel = SecurityLevel.STRICT
    ) -> SecurityValidation:
        """
        Validate a custom contract (not from template).
        
        Custom contracts require STRICT validation by default.
        """
        return self.validator.validate_contract(contract_code, security_level)
    
    def save_contract(self, contract_data: Dict[str, Any], output_path: str):
        """Save contract to file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save Solidity code
        contract_file = output_path.replace('.json', '.sol')
        with open(contract_file, 'w') as f:
            f.write(contract_data['contract_code'])
        
        # Save metadata
        metadata = {
            "template": contract_data.get("template"),
            "parameters": contract_data.get("parameters"),
            "validation": contract_data.get("validation"),
            "metadata": contract_data.get("metadata"),
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return contract_file, output_path


# Convenience functions

def create_royalty_split_contract(
    track_name: str,
    max_recipients: int = 10,
) -> Dict[str, Any]:
    """Quick create royalty split contract."""
    builder = ContractBuilder()
    return builder.build_contract(
        "royalty_split",
        {
            "track_name": track_name,
            "max_recipients": max_recipients,
        }
    )


def create_time_locked_contract(
    track_name: str,
) -> Dict[str, Any]:
    """Quick create time-locked release contract."""
    builder = ContractBuilder()
    return builder.build_contract(
        "time_locked_release",
        {
            "track_name": track_name,
        }
    )


def create_auction_contract(
    min_bid_wei: str = "1000000000000000000",
) -> Dict[str, Any]:
    """Quick create auction contract."""
    builder = ContractBuilder()
    return builder.build_contract(
        "auction",
        {
            "min_bid": min_bid_wei,
        }
    )
