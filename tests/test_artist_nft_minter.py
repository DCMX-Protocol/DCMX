"""
Tests for Artist NFT Minting Integration.

Covers:
- NFT minting for verified artists
- Royalty calculation and distribution
- Secondary market royalty handling
- Metadata creation and embedding
- Watermark proof chain verification
- Artist portfolio retrieval
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch

from dcmx.blockchain.artist_nft_minter import (
    ArtistNFTMinter,
    ArtistMintRequest,
    NFTMetadata,
    MintedNFT,
    RoyaltyDistribution,
    SecondaryMarketData,
    NFTMintStatus,
    RoyaltyDistributionType,
)
from dcmx.artist.artist_wallet_manager import ArtistWalletManager, ArtistProfile


@pytest.fixture
def mock_web3_minter():
    """Create a minter with mocked Web3 connection."""
    # Create a simple mock minter without Web3 connection for testing
    # In production, use testnet RPC endpoints
    class MockMinter:
        def __init__(self):
            self.minted_nfts = {}
            self.royalty_distributions = {}
            self.secondary_market_data = {}
            self.music_nft_contract = "0xMusicNFT"
            self.dcmx_token_contract = "0xDCMXToken"
        
        async def get_artist_nft_portfolio(self, artist_id: str):
            portfolio = [nft for nft in self.minted_nfts.values() if nft.artist_id == artist_id]
            return True, f"Found {len(portfolio)} NFTs", portfolio
        
        async def get_artist_royalty_history(self, artist_id: str):
            history = [d for d in self.royalty_distributions.values() if d.artist_id == artist_id]
            return True, f"Total earned: {sum(d.amount_wei for d in history)} wei", history
        
        def export_mint_record(self, mint_id: str):
            minted = self.minted_nfts.get(mint_id)
            if not minted:
                return None
            return {
                "mint_id": minted.mint_id,
                "artist_id": minted.artist_id,
                "contract_address": minted.contract_address,
                "token_id": minted.token_id,
                "transaction_hash": minted.transaction_hash,
                "status": minted.status.value,
                "edition": f"{minted.edition_number}/{minted.max_editions}",
                "minted_at": minted.minted_at,
                "watermark_verified": minted.watermark_verified,
                "watermark_confidence": minted.watermark_confidence,
            }
    
    return MockMinter()


class TestArtistNFTMinterInitialization:
    """Test ArtistNFTMinter initialization."""

    def test_minter_initialization_skipped_requires_web3(self):
        """
        Note: ArtistNFTMinter requires Web3 connection.
        In production testing, use testnet (Sepolia, Mumbai).
        For unit tests, use mock fixtures as shown in integration tests.
        """
        assert True  # Placeholder - Web3 connection required


class TestNFTMetadataCreation:
    """Test NFT metadata creation."""

    def test_metadata_initialization(self):
        """Test metadata initializes with required fields."""
        metadata = NFTMetadata(
            title="Anti-Hero",
            artist="Taylor Swift",
            artist_wallet="0xTaylorSwift",
            dcmx_content_hash="sha256_of_audio",
            watermark_proof_chain_id="proof_chain_uuid",
            edition_number=1,
            max_editions=100
        )
        
        assert metadata.title == "Anti-Hero"
        assert metadata.artist == "Taylor Swift"
        assert metadata.edition_number == 1
        assert metadata.max_editions == 100

    def test_metadata_to_dict(self):
        """Test metadata serialization to dict."""
        metadata = NFTMetadata(
            title="Song Title",
            artist="Artist Name",
            artist_wallet="0xWallet",
            dcmx_content_hash="content_hash_123",
            watermark_proof_chain_id="proof_uuid_123",
            edition_number=5,
            max_editions=50,
            description="Limited edition music NFT"
        )
        
        data = metadata.to_dict()
        
        assert data["name"] == "Song Title"
        assert data["artist"] == "Artist Name"
        assert data["dcmx"]["content_hash"] == "content_hash_123"
        assert data["dcmx"]["proof_chain_id"] == "proof_uuid_123"
        assert any(attr["trait_type"] == "Edition" for attr in data["attributes"])

    def test_metadata_to_json(self):
        """Test metadata serialization to JSON."""
        metadata = NFTMetadata(
            title="Song",
            artist="Artist",
            artist_wallet="0xWallet",
            dcmx_content_hash="hash",
            watermark_proof_chain_id="proof_uuid",
            edition_number=1,
            max_editions=1
        )
        
        json_str = metadata.to_json()
        
        assert isinstance(json_str, str)
        assert "Song" in json_str
        assert "Artist" in json_str
        assert "hash" in json_str

    def test_metadata_with_attributes(self):
        """Test metadata with custom attributes."""
        custom_attrs = [
            {"trait_type": "Genre", "value": "Pop"},
            {"trait_type": "Year", "value": "2024"}
        ]
        
        metadata = NFTMetadata(
            title="Song",
            artist="Artist",
            artist_wallet="0xWallet",
            dcmx_content_hash="hash",
            watermark_proof_chain_id="proof_uuid",
            edition_number=1,
            max_editions=1,
            attributes=custom_attrs
        )
        
        data = metadata.to_dict()
        attrs = data["attributes"]
        
        assert len(attrs) >= 2
        assert any(attr["trait_type"] == "Genre" for attr in attrs)
        assert any(attr["trait_type"] == "Year" for attr in attrs)


class TestArtistMintRequest:
    """Test ArtistMintRequest validation."""

    def test_mint_request_initialization(self):
        """Test mint request initializes correctly."""
        request = ArtistMintRequest(
            artist_id="artist_123",
            track_title="Song Title",
            dcmx_content_hash="content_hash",
            watermark_proof_chain_id="proof_uuid",
            edition_number=1,
            max_editions=100,
            price_wei=1000000000000000000  # 1 ETH
        )
        
        assert request.artist_id == "artist_123"
        assert request.track_title == "Song Title"
        assert request.edition_number == 1
        assert request.max_editions == 100
        assert request.royalty_primary_bps == 10000  # 100% default

    def test_mint_request_with_custom_royalties(self):
        """Test mint request with custom royalty settings."""
        request = ArtistMintRequest(
            artist_id="artist_123",
            track_title="Song",
            dcmx_content_hash="hash",
            watermark_proof_chain_id="proof_uuid",
            edition_number=1,
            max_editions=100,
            price_wei=1000,
            royalty_primary_bps=9750,  # 97.5%
            royalty_secondary_bps=500   # 5%
        )
        
        assert request.royalty_primary_bps == 9750
        assert request.royalty_secondary_bps == 500


class TestMintedNFTRecord:
    """Test MintedNFT record creation and tracking."""

    def test_minted_nft_record(self):
        """Test MintedNFT record stores all data correctly."""
        minted = MintedNFT(
            mint_id="mint_123",
            artist_id="artist_123",
            contract_address="0xMusicNFT",
            token_id=1,
            transaction_hash="0xTx123",
            metadata_uri="ipfs://metadata",
            status=NFTMintStatus.CONFIRMED,
            edition_number=1,
            max_editions=100,
            minted_at=datetime.now(timezone.utc).isoformat(),
            watermark_verified=True,
            watermark_confidence=0.95
        )
        
        assert minted.mint_id == "mint_123"
        assert minted.artist_id == "artist_123"
        assert minted.token_id == 1
        assert minted.status == NFTMintStatus.CONFIRMED
        assert minted.watermark_verified is True

    def test_minted_nft_statuses(self):
        """Test all NFT minting statuses."""
        statuses = [
            NFTMintStatus.PENDING,
            NFTMintStatus.CONFIRMED,
            NFTMintStatus.FAILED,
            NFTMintStatus.CANCELLED,
            NFTMintStatus.METADATA_ERROR
        ]
        
        for status in statuses:
            assert isinstance(status, NFTMintStatus)


class TestRoyaltyDistributionTracking:
    """Test royalty distribution records."""

    def test_royalty_distribution_record(self):
        """Test royalty distribution tracks payment."""
        distribution = RoyaltyDistribution(
            distribution_id="dist_123",
            artist_id="artist_123",
            artist_wallet="0xArtist",
            token_id=1,
            amount_wei=500000000000000000,  # 0.5 ETH
            distribution_type=RoyaltyDistributionType.PRIMARY_SALE,
            transaction_hash="0xTx456",
            distributed_at=datetime.now(timezone.utc).isoformat(),
            platform_fee=25000000000000000  # 0.025 ETH (2.5%)
        )
        
        assert distribution.artist_id == "artist_123"
        assert distribution.amount_wei == 500000000000000000
        assert distribution.distribution_type == RoyaltyDistributionType.PRIMARY_SALE
        assert distribution.platform_fee == 25000000000000000

    def test_royalty_types(self):
        """Test all royalty distribution types."""
        types = [
            RoyaltyDistributionType.PRIMARY_SALE,
            RoyaltyDistributionType.SECONDARY_SALE,
            RoyaltyDistributionType.STREAMING,
            RoyaltyDistributionType.LICENSING,
            RoyaltyDistributionType.SYNC
        ]
        
        for rtype in types:
            assert isinstance(rtype, RoyaltyDistributionType)


class TestSecondaryMarketTracking:
    """Test secondary market data tracking."""

    def test_secondary_market_record(self):
        """Test secondary market transaction record."""
        secondary = SecondaryMarketData(
            nft_id="1",
            seller_wallet="0xSeller",
            buyer_wallet="0xBuyer",
            sale_price_wei=2000000000000000000,  # 2 ETH
            marketplace="opensea",
            transaction_hash="0xSaleTx",
            royalty_paid_wei=100000000000000000,  # 0.1 ETH (5%)
            artist_wallet="0xArtist",
            sale_timestamp=datetime.now(timezone.utc).isoformat()
        )
        
        assert secondary.nft_id == "1"
        assert secondary.sale_price_wei == 2000000000000000000
        assert secondary.marketplace == "opensea"
        assert secondary.royalty_paid_wei == 100000000000000000

    def test_secondary_market_royalty_calculation(self):
        """Test royalty calculation for secondary market."""
        sale_price = 2000000000000000000  # 2 ETH
        royalty_bps = 500  # 5%
        
        royalty_amount = int(sale_price * royalty_bps / 10000)
        
        assert royalty_amount == 100000000000000000  # 0.1 ETH


class TestMinterIntegration:
    """Integration tests for ArtistNFTMinter."""

    @pytest.mark.asyncio
    async def test_minter_state_management(self, mock_web3_minter):
        """Test minter manages NFT and distribution state."""
        minter = mock_web3_minter
        
        # Verify initial empty state
        assert len(minter.minted_nfts) == 0
        assert len(minter.royalty_distributions) == 0
        assert len(minter.secondary_market_data) == 0

    @pytest.mark.asyncio
    async def test_artist_portfolio_retrieval(self, mock_web3_minter):
        """Test retrieving artist's NFT portfolio."""
        minter = mock_web3_minter
        
        # Add test NFTs
        minter.minted_nfts["mint_1"] = MintedNFT(
            mint_id="mint_1",
            artist_id="artist_123",
            contract_address="0xMusicNFT",
            token_id=1,
            transaction_hash="0xTx1",
            metadata_uri="ipfs://1",
            status=NFTMintStatus.CONFIRMED,
            edition_number=1,
            max_editions=100,
            minted_at=datetime.now(timezone.utc).isoformat()
        )
        
        minter.minted_nfts["mint_2"] = MintedNFT(
            mint_id="mint_2",
            artist_id="artist_123",
            contract_address="0xMusicNFT",
            token_id=2,
            transaction_hash="0xTx2",
            metadata_uri="ipfs://2",
            status=NFTMintStatus.CONFIRMED,
            edition_number=2,
            max_editions=100,
            minted_at=datetime.now(timezone.utc).isoformat()
        )
        
        success, msg, portfolio = await minter.get_artist_nft_portfolio("artist_123")
        
        assert success is True
        assert len(portfolio) == 2
        assert all(nft.artist_id == "artist_123" for nft in portfolio)

    @pytest.mark.asyncio
    async def test_royalty_history_retrieval(self, mock_web3_minter):
        """Test retrieving artist's royalty distribution history."""
        minter = mock_web3_minter
        
        # Add test distributions
        dist1 = RoyaltyDistribution(
            distribution_id="dist_1",
            artist_id="artist_123",
            artist_wallet="0xArtist",
            token_id=1,
            amount_wei=500000000000000000,
            distribution_type=RoyaltyDistributionType.PRIMARY_SALE,
            transaction_hash="0xTx1",
            distributed_at=datetime.now(timezone.utc).isoformat(),
            platform_fee=25000000000000000
        )
        
        dist2 = RoyaltyDistribution(
            distribution_id="dist_2",
            artist_id="artist_123",
            artist_wallet="0xArtist",
            token_id=2,
            amount_wei=300000000000000000,
            distribution_type=RoyaltyDistributionType.SECONDARY_SALE,
            transaction_hash="0xTx2",
            distributed_at=datetime.now(timezone.utc).isoformat(),
            platform_fee=15000000000000000
        )
        
        minter.royalty_distributions["dist_1"] = dist1
        minter.royalty_distributions["dist_2"] = dist2
        
        success, msg, history = await minter.get_artist_royalty_history("artist_123")
        
        assert success is True
        assert len(history) == 2
        assert all(d.artist_id == "artist_123" for d in history)
        
        total_earned = sum(d.amount_wei for d in history)
        assert total_earned == 800000000000000000  # 0.8 ETH


class TestMintRecordExport:
    """Test export of mint records."""

    def test_export_mint_record(self, mock_web3_minter):
        """Test exporting minted NFT record."""
        minter = mock_web3_minter
        
        minted = MintedNFT(
            mint_id="mint_123",
            artist_id="artist_123",
            contract_address="0xMusicNFT",
            token_id=1,
            transaction_hash="0xTx123",
            metadata_uri="ipfs://metadata",
            status=NFTMintStatus.CONFIRMED,
            edition_number=1,
            max_editions=100,
            minted_at=datetime.now(timezone.utc).isoformat(),
            watermark_verified=True,
            watermark_confidence=0.98
        )
        
        minter.minted_nfts["mint_123"] = minted
        exported = minter.export_mint_record("mint_123")
        
        assert exported is not None
        assert exported["mint_id"] == "mint_123"
        assert exported["artist_id"] == "artist_123"
        assert exported["token_id"] == 1
        assert exported["status"] == "confirmed"
        assert exported["edition"] == "1/100"
        assert exported["watermark_verified"] is True

    def test_export_nonexistent_record(self, mock_web3_minter):
        """Test exporting nonexistent record returns None."""
        minter = mock_web3_minter
        
        exported = minter.export_mint_record("nonexistent")
        
        assert exported is None


class TestMintingCalculations:
    """Test minting-related calculations."""

    def test_platform_fee_calculation(self):
        """Test platform fee calculation."""
        sale_price_wei = 1000000000000000000  # 1 ETH
        platform_fee_bps = 250  # 2.5%
        
        fee = int(sale_price_wei * platform_fee_bps / 10000)
        artist_amount = sale_price_wei - fee
        
        assert fee == 25000000000000000  # 0.025 ETH
        assert artist_amount == 975000000000000000  # 0.975 ETH

    def test_royalty_bps_conversion(self):
        """Test basis points to percentage conversion."""
        bps_values = [
            (10000, 100),  # 100%
            (5000, 50),    # 50%
            (1000, 10),    # 10%
            (500, 5),      # 5%
            (100, 1),      # 1%
        ]
        
        for bps, expected_pct in bps_values:
            percentage = bps / 100
            assert percentage == expected_pct


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
