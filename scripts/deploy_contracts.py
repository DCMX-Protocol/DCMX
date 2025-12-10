#!/usr/bin/env python3
"""Deploy DCMX smart contracts to TRON blockchain."""

import sys
import json
import logging
from pathlib import Path
from typing import Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dcmx.tron.client import TronClient
from dcmx.tron.config import TronConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContractDeployer:
    """Deploy DCMX smart contracts."""
    
    def __init__(self, config: TronConfig = None):
        """
        Initialize deployer.
        
        Args:
            config: TRON configuration
        """
        self.config = config or TronConfig.from_env()
        self.client = TronClient(self.config)
        self.deployed_addresses: Dict[str, str] = {}
        
        logger.info(f"Deployer initialized on {self.config.network.value}")
        logger.info(f"Deployer address: {self.client.address}")
    
    def deploy_all(self) -> Dict[str, str]:
        """
        Deploy all DCMX contracts.
        
        Returns:
            Dictionary of contract names to addresses
        """
        logger.info("Starting contract deployment...")
        
        try:
            # 1. Deploy DCMX Token
            logger.info("Deploying DCMXToken...")
            token_address = self.deploy_token()
            if not token_address:
                logger.error("Failed to deploy DCMXToken")
                return {}
            self.deployed_addresses['DCMXToken'] = token_address
            
            # 2. Deploy Music NFT
            logger.info("Deploying MusicNFT...")
            nft_address = self.deploy_music_nft()
            if not nft_address:
                logger.error("Failed to deploy MusicNFT")
                return {}
            self.deployed_addresses['MusicNFT'] = nft_address
            
            # 3. Deploy Compliance Registry
            logger.info("Deploying ComplianceRegistry...")
            compliance_address = self.deploy_compliance_registry()
            if not compliance_address:
                logger.error("Failed to deploy ComplianceRegistry")
                return {}
            self.deployed_addresses['ComplianceRegistry'] = compliance_address
            
            # 4. Deploy Reward Vault (needs token address)
            logger.info("Deploying RewardVault...")
            reward_address = self.deploy_reward_vault(token_address)
            if not reward_address:
                logger.error("Failed to deploy RewardVault")
                return {}
            self.deployed_addresses['RewardVault'] = reward_address
            
            # 5. Deploy Royalty Distributor
            logger.info("Deploying RoyaltyDistributor...")
            royalty_address = self.deploy_royalty_distributor()
            if not royalty_address:
                logger.error("Failed to deploy RoyaltyDistributor")
                return {}
            self.deployed_addresses['RoyaltyDistributor'] = royalty_address
            
            logger.info("All contracts deployed successfully!")
            return self.deployed_addresses
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}", exc_info=True)
            return {}
    
    def deploy_token(self) -> str:
        """Deploy DCMX Token contract."""
        # Note: In practice, you would compile the Solidity contract
        # and deploy using tronpy or TronWeb
        # This is a placeholder showing the structure
        
        logger.warning(
            "Contract deployment requires compiled bytecode. "
            "Please use TronBox or tronpy to compile and deploy contracts."
        )
        
        # Placeholder - in real implementation, would deploy contract
        # initial_supply = utils.to_token_units(1_000_000_000)  # 1B tokens
        # contract = self.tron.contract().deploy(bytecode, abi, initial_supply)
        
        return ""
    
    def deploy_music_nft(self) -> str:
        """Deploy Music NFT contract."""
        logger.warning("Contract deployment requires compiled bytecode.")
        return ""
    
    def deploy_compliance_registry(self) -> str:
        """Deploy Compliance Registry contract."""
        logger.warning("Contract deployment requires compiled bytecode.")
        return ""
    
    def deploy_reward_vault(self, token_address: str) -> str:
        """Deploy Reward Vault contract."""
        logger.warning("Contract deployment requires compiled bytecode.")
        return ""
    
    def deploy_royalty_distributor(self) -> str:
        """Deploy Royalty Distributor contract."""
        logger.warning("Contract deployment requires compiled bytecode.")
        return ""
    
    def save_addresses(self, output_file: str = None):
        """
        Save deployed contract addresses.
        
        Args:
            output_file: Path to save addresses (default: contract_addresses.json)
        """
        if not output_file:
            output_file = Path(__file__).parent.parent / "contract_addresses.json"
        
        # Add network info
        data = {
            'network': self.config.network.value,
            'deployer': self.client.address,
            'contracts': self.deployed_addresses,
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Contract addresses saved to {output_file}")
    
    def print_env_config(self):
        """Print environment variable configuration."""
        logger.info("\n" + "="*80)
        logger.info("Add these to your .env file:")
        logger.info("="*80)
        
        for name, address in self.deployed_addresses.items():
            env_name = name.replace('DCMX', 'DCMX_').replace('Music', 'MUSIC_').upper()
            if not env_name.endswith('_ADDRESS'):
                env_name += '_ADDRESS'
            logger.info(f"{env_name}={address}")
        
        logger.info("="*80 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy DCMX smart contracts')
    parser.add_argument(
        '--network',
        choices=['mainnet', 'shasta', 'nile'],
        help='TRON network to deploy to'
    )
    parser.add_argument(
        '--output',
        help='Output file for contract addresses (default: contract_addresses.json)'
    )
    
    args = parser.parse_args()
    
    # Load or create config
    config = TronConfig.from_env()
    if args.network:
        from dcmx.tron.config import NetworkType
        config.network = NetworkType[args.network.upper()]
    
    # Confirm deployment
    response = input(
        f"Deploy contracts to {config.network.value}? "
        f"(type 'yes' to confirm): "
    )
    if response.lower() != 'yes':
        logger.info("Deployment cancelled")
        return
    
    # Deploy contracts
    deployer = ContractDeployer(config)
    addresses = deployer.deploy_all()
    
    if addresses:
        deployer.save_addresses(args.output)
        deployer.print_env_config()
        logger.info("Deployment complete!")
    else:
        logger.error("Deployment failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
