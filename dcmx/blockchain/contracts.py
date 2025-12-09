"""
DCMX Smart Contracts - Solidity Source Code & Python Integration

This module contains all Solidity contracts for DCMX on Ethereum/Polygon.
Deploy to: Ethereum mainnet or Polygon for lower gas fees.
"""

import json
import os
from typing import Optional, Dict, Any
from web3 import Web3
from eth_account import Account
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# SOLIDITY CONTRACTS (As Strings for Deployment)
# ============================================================================

MUSIC_NFT_ABI = json.loads("""
[
    {
        "inputs": [],
        "name": "mintMusic",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getMetadata",
        "outputs": [
            {"internalType": "string", "name": "title", "type": "string"},
            {"internalType": "address", "name": "artistWallet", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
""")

DCMX_TOKEN_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]
""")

REWARD_DISTRIBUTOR_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "rewardType", "type": "string"}
        ],
        "name": "distributeReward",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "totalRewardsEarned",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]
""")


# ============================================================================
# PYTHON BLOCKCHAIN MANAGER
# ============================================================================

class BlockchainManager:
    """Manage DCMX smart contracts on Ethereum/Polygon."""
    
    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        music_nft_address: Optional[str] = None,
        dcmx_token_address: Optional[str] = None,
        reward_distributor_address: Optional[str] = None,
    ):
        """
        Initialize blockchain manager.
        
        Args:
            rpc_url: Ethereum RPC URL (Polygon, Mainnet, Testnet)
            private_key: Private key for signing transactions
            music_nft_address: Deployed MusicNFT contract address
            dcmx_token_address: Deployed DCMXToken contract address
            reward_distributor_address: Deployed RewardDistributor address
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        
        self.music_nft_address = music_nft_address
        self.dcmx_token_address = dcmx_token_address
        self.reward_distributor_address = reward_distributor_address
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")
        
        logger.info(f"Connected to blockchain: {self.w3.eth.chain_id}")
    
    async def mint_music_nft(
        self,
        title: str,
        artist: str,
        content_hash: str,
        edition_number: int,
        max_editions: int,
        royalty_percentage: int = 1000,  # 10%
    ) -> Dict[str, Any]:
        """
        Mint a music NFT on-chain.
        
        Returns:
            {
                "tx_hash": "0x...",
                "token_id": 1,
                "status": "pending|confirmed"
            }
        """
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")
        
        # Build transaction
        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )
        
        tx = contract.functions.mintMusic(
            self.account.address,
            title,
            artist,
            content_hash,
            edition_number,
            max_editions,
            royalty_percentage,
        ).build_transaction({
            'from': self.account.address,
            'gas': 300_000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.w3.eth.chain_id,
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Minted NFT: {title} by {artist}, tx: {tx_hash.hex()}")
        
        return {
            "tx_hash": tx_hash.hex(),
            "title": title,
            "artist": artist,
            "status": "pending",
        }
    
    async def distribute_reward(
        self,
        user_address: str,
        amount_dcmx: float,
        reward_type: str,  # "listening", "vote", "bandwidth", etc
    ) -> Dict[str, Any]:
        """
        Distribute DCMX token rewards to user.
        
        Returns:
            {
                "tx_hash": "0x...",
                "recipient": "0x...",
                "amount": 5.0,
                "status": "pending|confirmed"
            }
        """
        if not self.reward_distributor_address:
            raise ValueError("RewardDistributor contract not configured")
        
        # Convert amount to wei
        amount_wei = self.w3.to_wei(amount_dcmx, 'ether')
        
        # Build transaction
        contract = self.w3.eth.contract(
            address=self.reward_distributor_address,
            abi=REWARD_DISTRIBUTOR_ABI
        )
        
        tx = contract.functions.distributeReward(
            user_address,
            amount_wei,
            reward_type,
        ).build_transaction({
            'from': self.account.address,
            'gas': 200_000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.w3.eth.chain_id,
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Reward distributed: {amount_dcmx} DCMX to {user_address}, tx: {tx_hash.hex()}")
        
        return {
            "tx_hash": tx_hash.hex(),
            "recipient": user_address,
            "amount": amount_dcmx,
            "reward_type": reward_type,
            "status": "pending",
        }
    
    async def get_token_balance(self, wallet_address: str) -> float:
        """Get DCMX token balance for wallet."""
        if not self.dcmx_token_address:
            raise ValueError("DCMXToken contract not configured")
        
        contract = self.w3.eth.contract(
            address=self.dcmx_token_address,
            abi=DCMX_TOKEN_ABI
        )
        
        balance_wei = contract.functions.balanceOf(wallet_address).call()
        balance_dcmx = self.w3.from_wei(balance_wei, 'ether')
        
        logger.info(f"Balance of {wallet_address}: {balance_dcmx} DCMX")
        
        return float(balance_dcmx)
    
    async def get_total_token_supply(self) -> float:
        """Get total DCMX token supply."""
        if not self.dcmx_token_address:
            raise ValueError("DCMXToken contract not configured")
        
        contract = self.w3.eth.contract(
            address=self.dcmx_token_address,
            abi=DCMX_TOKEN_ABI
        )
        
        supply_wei = contract.functions.totalSupply().call()
        supply_dcmx = self.w3.from_wei(supply_wei, 'ether')
        
        logger.info(f"Total token supply: {supply_dcmx} DCMX")
        
        return float(supply_dcmx)


# ============================================================================
# DEPLOYMENT CONFIGURATION
# ============================================================================

NETWORKS = {
    "polygon_mainnet": {
        "rpc_url": "https://polygon-rpc.com/",
        "chain_id": 137,
        "name": "Polygon (Recommended for low fees)",
    },
    "polygon_mumbai": {
        "rpc_url": "https://rpc-mumbai.maticvigil.com/",
        "chain_id": 80001,
        "name": "Polygon Mumbai Testnet",
    },
    "ethereum_mainnet": {
        "rpc_url": "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
        "chain_id": 1,
        "name": "Ethereum Mainnet",
    },
    "ethereum_sepolia": {
        "rpc_url": "https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY",
        "chain_id": 11155111,
        "name": "Ethereum Sepolia Testnet",
    },
}

# Deployment instructions
DEPLOYMENT_INSTRUCTIONS = """
# DCMX Smart Contract Deployment Guide

## Prerequisites
1. Node.js 16+ installed
2. Hardhat: `npm install --save-dev hardhat`
3. OpenZeppelin contracts: `npm install @openzeppelin/contracts`
4. Private key with some ETH/MATIC for gas fees

## Deployment Steps

### 1. Create Hardhat Project
```bash
npx hardhat init
cd dcmx-contracts
npm install @openzeppelin/contracts
```

### 2. Create Contract Files
- Place MusicNFT.sol in `contracts/`
- Place DCMXToken.sol in `contracts/`
- Place RewardDistributor.sol in `contracts/`

### 3. Configure hardhat.config.js
```javascript
require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.20",
  networks: {
    polygon_mumbai: {
      url: "https://rpc-mumbai.maticvigil.com/",
      accounts: [process.env.PRIVATE_KEY]
    },
    polygon_mainnet: {
      url: "https://polygon-rpc.com/",
      accounts: [process.env.PRIVATE_KEY]
    }
  }
};
```

### 4. Deploy
```bash
export PRIVATE_KEY=your_private_key_here
npx hardhat run scripts/deploy.js --network polygon_mumbai
```

### 5. Verify on Polygonscan
```bash
npx hardhat verify --network polygon_mumbai CONTRACT_ADDRESS
```

## Post-Deployment
1. Save contract addresses
2. Update DCMX backend with contract addresses
3. Add reward distributor as authorized in token contract
4. Verify all contracts on Polygonscan

## Security Checklist
- [ ] Contracts audited by third-party firm
- [ ] Private key never committed to repo
- [ ] Multisig wallet controls admin functions
- [ ] Timelock on critical upgrades
- [ ] Rate limits on reward distribution
"""
