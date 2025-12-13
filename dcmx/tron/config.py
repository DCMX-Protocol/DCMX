"""
TRON Network Configuration

Supports both mainnet and testnet (Shasta/Nile) deployments.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict
from enum import Enum


class NetworkType(Enum):
    """TRON network types."""
    MAINNET = "mainnet"
    SHASTA = "shasta"  # Primary testnet
    NILE = "nile"      # Alternative testnet


@dataclass
class NetworkConfig:
    """Configuration for a TRON network."""
    name: str
    network_type: NetworkType
    full_node: str
    solidity_node: str
    event_server: str
    chain_id: int
    explorer_url: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "network_type": self.network_type.value,
            "full_node": self.full_node,
            "solidity_node": self.solidity_node,
            "event_server": self.event_server,
            "chain_id": self.chain_id,
            "explorer_url": self.explorer_url,
        }


# Network configurations
NETWORKS: Dict[str, NetworkConfig] = {
    "mainnet": NetworkConfig(
        name="TRON Mainnet",
        network_type=NetworkType.MAINNET,
        full_node="https://api.trongrid.io",
        solidity_node="https://api.trongrid.io",
        event_server="https://api.trongrid.io",
        chain_id=1,
        explorer_url="https://tronscan.org",
    ),
    "shasta": NetworkConfig(
        name="Shasta Testnet",
        network_type=NetworkType.SHASTA,
        full_node="https://api.shasta.trongrid.io",
        solidity_node="https://api.shasta.trongrid.io",
        event_server="https://api.shasta.trongrid.io",
        chain_id=2,
        explorer_url="https://shasta.tronscan.org",
    ),
    "nile": NetworkConfig(
        name="Nile Testnet",
        network_type=NetworkType.NILE,
        full_node="https://api.nileex.io",
        solidity_node="https://api.nileex.io",
        event_server="https://event.nileex.io",
        chain_id=3,
        explorer_url="https://nile.tronscan.org",
    ),
}


@dataclass
class TronConfig:
    """
    DCMX TRON Configuration
    
    Load from environment variables or provide directly.
    """
    network: str = "shasta"  # Default to testnet
    private_key: Optional[str] = None
    api_key: Optional[str] = None  # TronGrid API key (optional, for rate limits)
    
    # Contract addresses (populated after deployment)
    dcmx_token_address: Optional[str] = None
    music_nft_address: Optional[str] = None
    compliance_registry_address: Optional[str] = None
    reward_vault_address: Optional[str] = None
    royalty_distributor_address: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "TronConfig":
        """Load configuration from environment variables."""
        return cls(
            network=os.getenv("TRON_NETWORK", "shasta"),
            private_key=os.getenv("TRON_PRIVATE_KEY"),
            api_key=os.getenv("TRONGRID_API_KEY"),
            dcmx_token_address=os.getenv("DCMX_TOKEN_ADDRESS"),
            music_nft_address=os.getenv("MUSIC_NFT_ADDRESS"),
            compliance_registry_address=os.getenv("COMPLIANCE_REGISTRY_ADDRESS"),
            reward_vault_address=os.getenv("REWARD_VAULT_ADDRESS"),
            royalty_distributor_address=os.getenv("ROYALTY_DISTRIBUTOR_ADDRESS"),
        )
    
    def get_network_config(self) -> NetworkConfig:
        """Get network configuration."""
        if self.network not in NETWORKS:
            raise ValueError(f"Unknown network: {self.network}")
        return NETWORKS[self.network]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "network": self.network,
            "has_private_key": self.private_key is not None,
            "has_api_key": self.api_key is not None,
            "dcmx_token_address": self.dcmx_token_address,
            "music_nft_address": self.music_nft_address,
            "compliance_registry_address": self.compliance_registry_address,
            "reward_vault_address": self.reward_vault_address,
            "royalty_distributor_address": self.royalty_distributor_address,
        }


# Default configuration
DEFAULT_CONFIG = TronConfig(
    network="shasta",
    # Contract addresses will be populated after deployment
)


def get_config() -> TronConfig:
    """
    Get TRON configuration.
    
    Tries environment variables first, falls back to defaults.
    """
    try:
        return TronConfig.from_env()
    except Exception:
        return DEFAULT_CONFIG
