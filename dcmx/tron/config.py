"""TRON network configuration for DCMX."""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict


class NetworkType(Enum):
    """TRON network types."""
    MAINNET = "mainnet"
    SHASTA = "shasta"  # Testnet
    NILE = "nile"  # Testnet


@dataclass
class TronConfig:
    """Configuration for TRON blockchain connection."""
    
    network: NetworkType = NetworkType.SHASTA
    private_key: Optional[str] = None
    
    # Contract addresses (set after deployment)
    dcmx_token_address: Optional[str] = None
    music_nft_address: Optional[str] = None
    compliance_registry_address: Optional[str] = None
    reward_vault_address: Optional[str] = None
    royalty_distributor_address: Optional[str] = None
    
    # Network endpoints
    _network_endpoints: Dict[NetworkType, str] = field(default_factory=lambda: {
        NetworkType.MAINNET: "https://api.trongrid.io",
        NetworkType.SHASTA: "https://api.shasta.trongrid.io",
        NetworkType.NILE: "https://api.nileex.io",
    })
    
    # API keys for TronGrid (optional but recommended for production)
    api_key: Optional[str] = None
    
    @property
    def rpc_endpoint(self) -> str:
        """Get RPC endpoint for configured network."""
        endpoint = self._network_endpoints.get(self.network)
        if not endpoint:
            raise ValueError(f"Unknown network: {self.network}")
        return endpoint
    
    @property
    def is_testnet(self) -> bool:
        """Check if using testnet."""
        return self.network in (NetworkType.SHASTA, NetworkType.NILE)
    
    @classmethod
    def from_env(cls) -> "TronConfig":
        """Load configuration from environment variables."""
        network_str = os.getenv("TRON_NETWORK", "shasta").lower()
        network = NetworkType[network_str.upper()]
        
        return cls(
            network=network,
            private_key=os.getenv("TRON_PRIVATE_KEY"),
            dcmx_token_address=os.getenv("DCMX_TOKEN_ADDRESS"),
            music_nft_address=os.getenv("MUSIC_NFT_ADDRESS"),
            compliance_registry_address=os.getenv("COMPLIANCE_REGISTRY_ADDRESS"),
            reward_vault_address=os.getenv("REWARD_VAULT_ADDRESS"),
            royalty_distributor_address=os.getenv("ROYALTY_DISTRIBUTOR_ADDRESS"),
            api_key=os.getenv("TRONGRID_API_KEY"),
        )
    
    def validate(self) -> None:
        """
        Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.private_key:
            raise ValueError("TRON_PRIVATE_KEY is required")
        
        if len(self.private_key) != 64:
            raise ValueError("Private key must be 64 hex characters")
        
        # Validate hex format
        try:
            int(self.private_key, 16)
        except ValueError:
            raise ValueError("Private key must be valid hex")
        
        # Warn if using weak/default private key
        import logging
        logger = logging.getLogger(__name__)
        weak_keys = ['0' * 64, '1' * 64, 'a' * 64, 'f' * 64]
        if self.private_key.lower() in weak_keys:
            logger.error("CRITICAL: Using weak/default private key - INSECURE!")
            raise ValueError("Weak private key detected - change immediately")
    
    def __repr__(self) -> str:
        """Safe string representation without exposing private key."""
        return (
            f"TronConfig(network={self.network.value}, "
            f"rpc={self.rpc_endpoint}, "
            f"private_key=***REDACTED***)"
        )
    
    def get_contract_address(self, contract_name: str) -> Optional[str]:
        """Get contract address by name."""
        mapping = {
            "dcmx_token": self.dcmx_token_address,
            "music_nft": self.music_nft_address,
            "compliance_registry": self.compliance_registry_address,
            "reward_vault": self.reward_vault_address,
            "royalty_distributor": self.royalty_distributor_address,
        }
        return mapping.get(contract_name.lower())


# Default configuration
DEFAULT_CONFIG = TronConfig()
