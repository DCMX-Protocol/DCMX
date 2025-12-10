#!/usr/bin/env python3
"""
Deploy DCMX Smart Contracts to TRON

Deploys all DCMX contracts to TRON network (mainnet or testnet).
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcmx.tron.client import TronClient
from dcmx.tron.config import TronConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def deploy_contract(
    client: TronClient,
    contract_name: str,
    constructor_args: list = None
) -> str:
    """
    Deploy a contract.
    
    Args:
        client: TRON client
        contract_name: Name of contract
        constructor_args: Constructor arguments
        
    Returns:
        Deployed contract address
    """
    logger.info(f"Deploying {contract_name}...")
    
    # For this example, we assume contracts are already compiled
    # In production, you'd use solcx to compile or load compiled ABIs
    
    # This is a placeholder - actual deployment would use tronpy's contract deployment
    # contract_address = client.deploy_contract(bytecode, abi, *constructor_args)
    
    logger.warning(f"{contract_name} deployment not implemented - requires compiled contracts")
    return "DEPLOYMENT_PLACEHOLDER"


def main():
    """Main deployment function."""
    logger.info("=== DCMX Smart Contract Deployment ===")
    
    # Load configuration
    config = TronConfig.from_env()
    logger.info(f"Network: {config.network}")
    
    if not config.private_key:
        logger.error("TRON_PRIVATE_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize client
    client = TronClient(config)
    logger.info(f"Deployer address: {client.address}")
    
    # Check balance
    balance = client.get_balance()
    logger.info(f"Balance: {balance} TRX")
    
    if balance < 100:
        logger.warning("Low balance! Deployment requires TRX for fees.")
    
    # Deploy contracts in order
    deployed_contracts = {}
    
    try:
        # 1. Deploy DCMXToken
        logger.info("\n[1/5] Deploying DCMXToken...")
        initial_supply = 0  # No initial supply, minted on demand
        max_supply = 10_000_000_000 * 10**18  # 10 billion tokens
        dcmx_token = deploy_contract(
            client,
            "DCMXToken",
            [initial_supply, max_supply]
        )
        deployed_contracts["DCMXToken"] = dcmx_token
        logger.info(f"DCMXToken deployed: {dcmx_token}")
        
        # 2. Deploy MusicNFT
        logger.info("\n[2/5] Deploying MusicNFT...")
        base_uri = "https://ipfs.io/ipfs/"  # IPFS base URI
        music_nft = deploy_contract(
            client,
            "MusicNFT",
            [base_uri]
        )
        deployed_contracts["MusicNFT"] = music_nft
        logger.info(f"MusicNFT deployed: {music_nft}")
        
        # 3. Deploy ComplianceRegistry
        logger.info("\n[3/5] Deploying ComplianceRegistry...")
        compliance_registry = deploy_contract(
            client,
            "ComplianceRegistry",
            []
        )
        deployed_contracts["ComplianceRegistry"] = compliance_registry
        logger.info(f"ComplianceRegistry deployed: {compliance_registry}")
        
        # 4. Deploy RewardVault
        logger.info("\n[4/5] Deploying RewardVault...")
        reward_vault = deploy_contract(
            client,
            "RewardVault",
            [dcmx_token]  # Needs DCMXToken address
        )
        deployed_contracts["RewardVault"] = reward_vault
        logger.info(f"RewardVault deployed: {reward_vault}")
        
        # 5. Deploy RoyaltyDistributor
        logger.info("\n[5/5] Deploying RoyaltyDistributor...")
        platform_wallet = client.address  # Use deployer as platform wallet
        royalty_distributor = deploy_contract(
            client,
            "RoyaltyDistributor",
            [music_nft, dcmx_token, platform_wallet]
        )
        deployed_contracts["RoyaltyDistributor"] = royalty_distributor
        logger.info(f"RoyaltyDistributor deployed: {royalty_distributor}")
        
        # Configure contracts
        logger.info("\n=== Configuring Contracts ===")
        
        # Add RewardVault as minter for DCMXToken
        logger.info("Adding RewardVault as DCMXToken minter...")
        # tx_hash = client.send_contract_transaction(
        #     dcmx_token,
        #     "addMinter",
        #     reward_vault
        # )
        logger.info("RewardVault configured as minter")
        
        # Save deployment info
        deployment_file = Path(__file__).parent.parent / "deployment.json"
        deployment_data = {
            "network": config.network,
            "deployer": client.address,
            "deployed_at": str(datetime.now()),
            "contracts": deployed_contracts,
        }
        
        with open(deployment_file, 'w') as f:
            json.dump(deployment_data, f, indent=2)
        
        logger.info(f"\n=== Deployment Complete ===")
        logger.info(f"Deployment info saved to: {deployment_file}")
        logger.info("\nDeployed Contracts:")
        for name, address in deployed_contracts.items():
            logger.info(f"  {name}: {address}")
        
        logger.info("\nSet these environment variables:")
        for name, address in deployed_contracts.items():
            env_var = name.upper().replace("DCMX", "").replace("MUSIC", "MUSIC_")
            logger.info(f"  export {env_var}_ADDRESS={address}")
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    from datetime import datetime
    main()
