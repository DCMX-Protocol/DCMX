"""
Smart Contract Builder - Usage Examples

Demonstrates how artists/customers can create custom contracts.
"""

import asyncio
from dcmx.blockchain.contract_builder import (
    ContractBuilder,
    SecurityLevel,
    create_royalty_split_contract,
    create_time_locked_contract,
    create_auction_contract,
)
from dcmx.blockchain.contract_deployer import (
    DeploymentConfig,
    ContractDeployer,
    deploy_from_template,
)


async def example_1_list_templates():
    """Example: List all available contract templates."""
    print("Example 1: List Contract Templates")
    print("=" * 60)
    
    builder = ContractBuilder()
    templates = builder.list_templates()
    
    for template in templates:
        print(f"\n📋 {template['name']}")
        print(f"   Type: {template['type']}")
        print(f"   Description: {template['description']}")
        print(f"   Security: {template['security_level']}")
        print(f"   Gas Estimate: ~{template['gas_estimate']:,} wei")
        print(f"   Audit Required: {'Yes' if template['audit_required'] else 'No'}")
        print(f"   Parameters:")
        for param in template['parameters']:
            required = "required" if param['required'] else "optional"
            print(f"     - {param['name']} ({param['type']}, {required}): {param['description']}")


async def example_2_create_royalty_split():
    """Example: Create royalty split contract."""
    print("\n\nExample 2: Create Royalty Split Contract")
    print("=" * 60)
    
    # Quick create using convenience function
    contract = create_royalty_split_contract(
        track_name="My Awesome Song",
        max_recipients=5,
    )
    
    print(f"\n✓ Contract created!")
    print(f"  Template: {contract['template']}")
    print(f"  Security Level: {contract['security_level']}")
    print(f"  Gas Estimate: ~{contract['gas_estimate']:,} wei")
    
    # Check validation results
    validation = contract['validation']
    print(f"\n  Validation:")
    print(f"    Passed: {validation['passed']}")
    print(f"    Issues: {len(validation['issues'])}")
    print(f"    Warnings: {len(validation['warnings'])}")
    
    if validation['warnings']:
        print(f"\n  Warnings:")
        for warning in validation['warnings']:
            print(f"    ⚠️  {warning}")
    
    # Save contract
    builder = ContractBuilder()
    sol_file, json_file = builder.save_contract(contract, "output/royalty_split.json")
    print(f"\n  Saved to:")
    print(f"    Solidity: {sol_file}")
    print(f"    Metadata: {json_file}")


async def example_3_create_time_locked():
    """Example: Create time-locked release contract."""
    print("\n\nExample 3: Create Time-Locked Release")
    print("=" * 60)
    
    contract = create_time_locked_contract(
        track_name="Exclusive Drop - Coming Soon",
    )
    
    print(f"\n✓ Time-locked contract created!")
    print(f"  Template: {contract['template']}")
    print(f"  This contract will:")
    print(f"    1. Hide content until release time")
    print(f"    2. Automatically reveal at scheduled date")
    print(f"    3. Provide verifiable proof of pre-existence")
    
    validation = contract['validation']
    if validation['passed']:
        print(f"\n  ✓ Security validation passed")
    else:
        print(f"\n  ✗ Security issues found:")
        for issue in validation['issues']:
            print(f"    - Line {issue.get('line', '?')}: {issue['description']}")


async def example_4_create_auction():
    """Example: Create NFT auction contract."""
    print("\n\nExample 4: Create NFT Auction")
    print("=" * 60)
    
    # 1 ETH minimum bid
    contract = create_auction_contract(
        min_bid_wei="1000000000000000000",
    )
    
    print(f"\n✓ Auction contract created!")
    print(f"  Minimum Bid: 1.0 ETH")
    print(f"  Features:")
    print(f"    - Automatic bid tracking")
    print(f"    - Outbid refunds")
    print(f"    - Winner receives NFT")
    print(f"    - Seller receives payment")
    
    validation = contract['validation']
    if validation['audit_required']:
        print(f"\n  ⚠️  AUDIT REQUIRED")
        print(f"     This contract handles funds and requires professional audit")
        print(f"     before deployment to mainnet.")


async def example_5_validate_custom_contract():
    """Example: Validate a custom contract."""
    print("\n\nExample 5: Validate Custom Contract")
    print("=" * 60)
    
    # Custom contract code (with intentional issues for demo)
    custom_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CustomContract {
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function withdrawAll() public {
        require(msg.sender == owner, "Not owner");
        payable(msg.sender).transfer(address(this).balance);  // Issue: use of transfer
    }
    
    function updateOwner(address newOwner) public {
        require(tx.origin == owner, "Not owner");  // Issue: tx.origin
        owner = newOwner;
    }
}
"""
    
    builder = ContractBuilder()
    validation = builder.validate_custom_contract(
        custom_contract,
        SecurityLevel.STRICT,
    )
    
    print(f"\n  Validation Results:")
    print(f"    Passed: {validation.passed}")
    print(f"    Audit Required: {validation.audit_required}")
    
    if validation.issues:
        print(f"\n  ❌ Security Issues Found:")
        for issue in validation.issues:
            severity = issue['severity'].upper()
            line = f"Line {issue.get('line', '?')}"
            print(f"    [{severity}] {line}: {issue['description']}")
    
    if validation.warnings:
        print(f"\n  ⚠️  Warnings:")
        for warning in validation.warnings:
            print(f"    {warning}")
    
    print(f"\n  Gas Estimate: ~{validation.gas_estimate:,} wei")


async def example_6_deploy_contract():
    """Example: Deploy a contract (testnet)."""
    print("\n\nExample 6: Deploy Contract to Testnet")
    print("=" * 60)
    
    # Configuration for Polygon Mumbai testnet
    config = DeploymentConfig(
        network="polygon-mumbai",
        rpc_url="https://rpc-mumbai.maticvigil.com",
        chain_id=80001,
        deployer_private_key="0xYOUR_PRIVATE_KEY_HERE",  # Replace with actual key
        gas_price_gwei=None,  # Auto-detect
        verify_on_etherscan=False,
    )
    
    print(f"\n  Deploying to: {config.network}")
    print(f"  Chain ID: {config.chain_id}")
    
    # Deploy royalty split contract
    result = await deploy_from_template(
        template_name="royalty_split",
        parameters={
            "track_name": "My Song",
            "max_recipients": 10,
        },
        constructor_args=[
            ["0xArtist1", "0xArtist2", "0xProducer"],  # Wallet addresses
            [5000, 3000, 2000],  # Percentages (50%, 30%, 20%)
        ],
        config=config,
    )
    
    if result.success:
        print(f"\n  ✓ Deployment Successful!")
        print(f"    Contract Address: {result.contract_address}")
        print(f"    Transaction Hash: {result.transaction_hash}")
        print(f"    Gas Used: {result.gas_used:,}")
        print(f"    Cost: {result.deployment_cost_eth:.6f} ETH")
    else:
        print(f"\n  ✗ Deployment Failed")
        print(f"    Error: {result.error}")


async def example_7_custom_template():
    """Example: Create contract with custom parameters."""
    print("\n\nExample 7: Custom Parameters")
    print("=" * 60)
    
    builder = ContractBuilder()
    
    # Build with custom parameters
    contract = builder.build_contract(
        template_name="royalty_split",
        parameters={
            "track_name": "Limited Edition Track #1",
            "max_recipients": 3,  # Only 3 collaborators
        },
        validate=True,
    )
    
    print(f"\n  ✓ Contract built with custom parameters")
    print(f"    Track: {contract['parameters']['track_name']}")
    print(f"    Max Recipients: {contract['parameters']['max_recipients']}")
    
    # Show partial contract code
    code_preview = contract['contract_code'].split('\n')[0:20]
    print(f"\n  Contract Code Preview:")
    for line in code_preview:
        if line.strip():
            print(f"    {line}")


if __name__ == "__main__":
    print("=" * 60)
    print("DCMX Smart Contract Builder - Examples")
    print("=" * 60)
    print()
    
    # Run examples
    asyncio.run(example_1_list_templates())
    asyncio.run(example_2_create_royalty_split())
    asyncio.run(example_3_create_time_locked())
    asyncio.run(example_4_create_auction())
    asyncio.run(example_5_validate_custom_contract())
    # asyncio.run(example_6_deploy_contract())  # Uncomment to deploy
    asyncio.run(example_7_custom_template())
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("\nNext steps:")
    print("  1. Review generated contracts in output/")
    print("  2. Add your private key to deploy")
    print("  3. Test on testnet before mainnet")
    print("  4. Get professional audit for production")
    print("=" * 60)
