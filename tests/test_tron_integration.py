"""Tests for TRON blockchain integration."""

import pytest
from dcmx.tron.config import TronConfig, NetworkType
from dcmx.tron import utils


class TestTronConfig:
    """Test TRON configuration."""
    
    def test_config_creation(self):
        """Test creating config."""
        config = TronConfig(
            network=NetworkType.SHASTA,
            private_key="0" * 64
        )
        
        assert config.network == NetworkType.SHASTA
        assert config.is_testnet is True
        assert "shasta" in config.rpc_endpoint.lower()
    
    def test_mainnet_config(self):
        """Test mainnet configuration."""
        config = TronConfig(network=NetworkType.MAINNET)
        
        assert config.network == NetworkType.MAINNET
        assert config.is_testnet is False
        assert "trongrid.io" in config.rpc_endpoint
    
    def test_get_contract_address(self):
        """Test getting contract address."""
        config = TronConfig()
        config.dcmx_token_address = "TTokenAddress"
        
        assert config.get_contract_address("dcmx_token") == "TTokenAddress"
        assert config.get_contract_address("unknown") is None


class TestTronUtils:
    """Test utility functions."""
    
    def test_sun_conversion(self):
        """Test TRX to SUN conversion."""
        assert utils.to_sun(1.0) == 1_000_000
        assert utils.to_sun(10.5) == 10_500_000
        assert utils.from_sun(1_000_000) == 1.0
        assert utils.from_sun(10_500_000) == 10.5
    
    def test_token_units_conversion(self):
        """Test token units conversion."""
        # 18 decimals
        assert utils.to_token_units(1.0) == 10 ** 18
        assert utils.to_token_units(100.0) == 100 * (10 ** 18)
        assert utils.from_token_units(10 ** 18) == 1.0
        assert utils.from_token_units(100 * (10 ** 18)) == 100.0
    
    def test_document_hash(self):
        """Test document hashing."""
        content = "Test document content"
        hash1 = utils.compute_document_hash(content)
        hash2 = utils.compute_document_hash(content)
        
        # Same content = same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex
        
        # Different content = different hash
        hash3 = utils.compute_document_hash("Different content")
        assert hash1 != hash3
    
    def test_proof_hash(self):
        """Test proof hashing."""
        data = {"key1": "value1", "key2": 123}
        hash1 = utils.compute_proof_hash(data)
        hash2 = utils.compute_proof_hash(data)
        
        assert hash1 == hash2
        assert len(hash1) == 64
    
    def test_address_validation(self):
        """Test TRON address validation."""
        # Valid format
        assert utils.validate_address("T" + "1" * 33) is True
        
        # Invalid formats
        assert utils.validate_address("0x" + "1" * 40) is False
        assert utils.validate_address("T" + "1" * 32) is False
        assert utils.validate_address("X" + "1" * 33) is False
    
    def test_royalty_calculation(self):
        """Test royalty calculation."""
        sale_price = 1_000_000  # 1 TRX in SUN
        
        # 10% royalty (1000 bps)
        royalty = utils.calculate_royalty(sale_price, 1000)
        assert royalty == 100_000  # 0.1 TRX
        
        # 5% royalty (500 bps)
        royalty = utils.calculate_royalty(sale_price, 500)
        assert royalty == 50_000  # 0.05 TRX
    
    def test_royalty_validation(self):
        """Test royalty basis points validation."""
        assert utils.validate_royalty_bps(0) is True
        assert utils.validate_royalty_bps(1000) is True
        assert utils.validate_royalty_bps(10000) is True
        assert utils.validate_royalty_bps(10001) is False
        assert utils.validate_royalty_bps(-1) is False
    
    def test_format_token_amount(self):
        """Test token amount formatting."""
        amount = 100 * (10 ** 18)  # 100 tokens
        formatted = utils.format_token_amount(amount)
        
        assert "100.00" in formatted
        assert "DCMX" in formatted
    
    def test_format_nft_edition(self):
        """Test NFT edition formatting."""
        formatted = utils.format_nft_edition(1, 100)
        assert formatted == "#1 of 100"
        
        formatted = utils.format_nft_edition(50, 100)
        assert formatted == "#50 of 100"


class TestDatabaseModels:
    """Test database models."""
    
    def test_import_models(self):
        """Test importing database models."""
        from dcmx.database.models import (
            Base,
            BlockchainEvent,
            UserProfile,
            NFTIndex,
            RewardClaimIndex,
            TransactionIndex,
            ComplianceIndex,
            Analytics
        )
        
        # All models should be importable
        assert Base is not None
        assert BlockchainEvent is not None
        assert UserProfile is not None
        assert NFTIndex is not None
        assert RewardClaimIndex is not None
        assert TransactionIndex is not None
        assert ComplianceIndex is not None
        assert Analytics is not None


class TestContractInterfaces:
    """Test contract interface classes."""
    
    def test_import_contracts(self):
        """Test importing contract classes."""
        from dcmx.tron.contracts import (
            DCMXTokenContract,
            MusicNFTContract,
            ComplianceRegistryContract,
            RewardVaultContract,
            RoyaltyDistributorContract,
            ContractManager
        )
        
        # All contracts should be importable
        assert DCMXTokenContract is not None
        assert MusicNFTContract is not None
        assert ComplianceRegistryContract is not None
        assert RewardVaultContract is not None
        assert RoyaltyDistributorContract is not None
        assert ContractManager is not None


class TestEventParsing:
    """Test event parsing."""
    
    def test_import_events(self):
        """Test importing event classes."""
        from dcmx.tron.events import (
            EventType,
            EventParser,
            BlockchainEvent,
            TokenTransferEvent,
            NFTMintedEvent,
            AcceptanceRecordedEvent
        )
        
        # All event types should be importable
        assert EventType is not None
        assert EventParser is not None
        assert BlockchainEvent is not None
        assert TokenTransferEvent is not None
        assert NFTMintedEvent is not None
        assert AcceptanceRecordedEvent is not None


class TestWeb3Endpoints:
    """Test Web3 API endpoints."""
    
    def test_import_endpoints(self):
        """Test importing Web3 endpoints."""
        from dcmx.api.web3_endpoints import (
            web3_router,
            NFTMintRequest,
            RewardClaimRequest,
            RoyaltyDistributionRequest
        )
        
        # Router and models should be importable
        assert web3_router is not None
        assert NFTMintRequest is not None
        assert RewardClaimRequest is not None
        assert RoyaltyDistributionRequest is not None
    
    def test_nft_mint_request_model(self):
        """Test NFT mint request model."""
        from dcmx.api.web3_endpoints import NFTMintRequest
        
        request = NFTMintRequest(
            to_address="TAddress123",
            title="Test Song",
            artist="Test Artist",
            content_hash="hash123",
            edition=1,
            max_editions=100
        )
        
        assert request.to_address == "TAddress123"
        assert request.title == "Test Song"
        assert request.royalty_bps == 1000  # Default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
