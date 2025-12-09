"""
Comprehensive tests for DCMX Artist NFT Wallet Connection System

Tests cover:
- Artist profile creation and management
- Wallet connection and signature verification
- NFT ownership verification
- Rights and royalty management
- Integration with blockchain
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from dcmx.artist.artist_wallet_manager import (
    ArtistWalletManager,
    ArtistProfile,
    WalletAddress,
    WalletSignatureChallenge,
    WalletType,
    VerificationStatus,
    RightsType,
    RoyaltyTier,
    NFTOwnership,
)

from dcmx.artist.nft_ownership_verifier import (
    NFTOwnershipVerifier,
    MockBlockchainProvider,
    BlockchainNetwork,
    TokenStandard,
    ContractInterface,
    BlockchainQueryResult,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def manager():
    """Create artist wallet manager."""
    return ArtistWalletManager()


@pytest.fixture
def verifier():
    """Create NFT ownership verifier."""
    provider = MockBlockchainProvider()
    return NFTOwnershipVerifier(provider)


@pytest.fixture
def mock_provider(verifier):
    """Get mock blockchain provider from verifier."""
    return verifier.provider


@pytest.fixture
def artist_profile(manager):
    """Create test artist profile."""
    return manager.create_artist_profile(
        legal_name="Jane Doe",
        artist_name="JaneDoe",
        email="jane@example.com"
    )


# ============================================================================
# ARTIST PROFILE TESTS
# ============================================================================

class TestArtistProfileCreation:
    """Test artist profile creation."""
    
    def test_create_artist_profile(self, manager):
        """Test creating new artist profile."""
        profile = manager.create_artist_profile(
            legal_name="John Smith",
            artist_name="JSmith",
            email="john@example.com"
        )
        
        assert profile.artist_id is not None
        assert profile.legal_name == "John Smith"
        assert profile.artist_name == "JSmith"
        assert profile.email == "john@example.com"
        assert profile.profile_verified is False
        assert profile.verification_status == VerificationStatus.PENDING
    
    def test_artist_profile_initial_state(self, artist_profile):
        """Test artist profile initial state."""
        assert artist_profile.primary_wallet is None
        assert len(artist_profile.connected_wallets) == 0
        assert len(artist_profile.owned_nfts) == 0
        assert artist_profile.identity_verified is False
        assert artist_profile.dcmx_verified_artist is False
    
    def test_get_artist_profile(self, manager, artist_profile):
        """Test retrieving artist profile."""
        retrieved = manager.get_artist_profile(artist_profile.artist_id)
        
        assert retrieved is not None
        assert retrieved.artist_id == artist_profile.artist_id
        assert retrieved.artist_name == artist_profile.artist_name
    
    def test_get_nonexistent_artist(self, manager):
        """Test getting nonexistent artist."""
        result = manager.get_artist_profile("nonexistent_id")
        assert result is None
    
    def test_export_profile_to_json(self, artist_profile):
        """Test exporting profile to JSON."""
        profile_dict = artist_profile.to_dict()
        
        assert "artist_id" in profile_dict
        assert "artist_name" in profile_dict
        assert profile_dict["profile_verified"] is False
        assert profile_dict["dcmx_verified_artist"] is False


# ============================================================================
# WALLET CONNECTION TESTS
# ============================================================================

class TestWalletConnectionChallenge:
    """Test wallet signature challenge creation and verification."""
    
    def test_create_wallet_challenge(self, manager, artist_profile):
        """Test creating wallet connection challenge."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xUser123456789"
        )
        
        assert challenge.challenge_id is not None
        assert challenge.artist_id == artist_profile.artist_id
        assert challenge.wallet_address == "0xuser123456789"  # Lowercased
        assert challenge.message != ""
        assert challenge.signature_verified is False
    
    def test_challenge_message_format(self, manager, artist_profile):
        """Test challenge message includes all required fields."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xWallet"
        )
        
        assert "Connect wallet to DCMX" in challenge.message
        assert artist_profile.artist_name in challenge.message
        assert challenge.challenge_nonce in challenge.message
        assert "not cost any gas" in challenge.message
    
    def test_challenge_expiration(self, manager, artist_profile):
        """Test challenge expiration time."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xWallet"
        )
        
        expires = datetime.fromisoformat(challenge.expires_at)
        now = datetime.now(timezone.utc)
        diff = (expires - now).total_seconds()
        
        # Should expire in ~15 minutes
        assert 840 < diff < 960  # 14-16 minutes
    
    def test_verify_valid_signature(self, manager, artist_profile):
        """Test verifying valid signature."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xWallet"
        )
        
        verified, msg = manager.verify_wallet_signature(
            challenge.challenge_id,
            "valid_signature_12345"
        )
        
        assert verified is True
        assert "verified" in msg.lower()
    
    def test_verify_expired_challenge(self, manager, artist_profile):
        """Test rejecting expired challenge."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xWallet"
        )
        
        # Manually set as expired
        challenge.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        
        verified, msg = manager.verify_wallet_signature(
            challenge.challenge_id,
            "signature"
        )
        
        assert verified is False
        assert "expired" in msg.lower()
    
    def test_verify_already_used_challenge(self, manager, artist_profile):
        """Test rejecting already-used challenge."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xWallet"
        )
        
        # First use
        manager.verify_wallet_signature(challenge.challenge_id, "sig1")
        
        # Second attempt should fail
        verified, msg = manager.verify_wallet_signature(
            challenge.challenge_id,
            "sig2"
        )
        
        assert verified is False
        assert "already used" in msg.lower()


class TestWalletConnection:
    """Test connecting wallets to artist profile."""
    
    def test_connect_first_wallet(self, manager, artist_profile):
        """Test connecting first wallet."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xPrimaryWallet"
        )
        
        success, msg, wallet = manager.connect_wallet(
            artist_profile.artist_id,
            challenge.challenge_id,
            "valid_signature",
            WalletType.METAMASK
        )
        
        assert success is True
        assert wallet is not None
        assert wallet.address == "0xprimarywallet"
        assert wallet.is_verified is True
        assert wallet.wallet_type == WalletType.METAMASK
        
        # Refresh profile
        profile = manager.get_artist_profile(artist_profile.artist_id)
        assert profile.primary_wallet is not None
        assert profile.primary_wallet.address == "0xprimarywallet"
    
    def test_connect_multiple_wallets(self, manager, artist_profile):
        """Test connecting multiple wallets."""
        # First wallet
        challenge1 = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xWallet1"
        )
        manager.connect_wallet(
            artist_profile.artist_id,
            challenge1.challenge_id,
            "sig1",
            WalletType.METAMASK
        )
        
        # Second wallet
        challenge2 = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xWallet2"
        )
        success, msg, wallet = manager.connect_wallet(
            artist_profile.artist_id,
            challenge2.challenge_id,
            "sig2",
            WalletType.WALLETCONNECT
        )
        
        assert success is True
        
        # Refresh and check
        profile = manager.get_artist_profile(artist_profile.artist_id)
        assert profile.primary_wallet.address == "0xwallet1"
        assert len(profile.connected_wallets) == 1
        assert profile.connected_wallets[0].address == "0xwallet2"
    
    def test_wallet_already_connected_to_another_artist(self, manager):
        """Test preventing wallet from being connected to multiple artists."""
        # Create two artists
        artist1 = manager.create_artist_profile(
            legal_name="Artist1",
            artist_name="A1",
            email="a1@example.com"
        )
        artist2 = manager.create_artist_profile(
            legal_name="Artist2",
            artist_name="A2",
            email="a2@example.com"
        )
        
        # Connect wallet to artist1
        challenge1 = manager.create_wallet_connection_challenge(
            artist1.artist_id,
            "0xSharedWallet"
        )
        manager.connect_wallet(
            artist1.artist_id,
            challenge1.challenge_id,
            "sig1"
        )
        
        # Try to connect same wallet to artist2
        challenge2 = manager.create_wallet_connection_challenge(
            artist2.artist_id,
            "0xSharedWallet"
        )
        success, msg, wallet = manager.connect_wallet(
            artist2.artist_id,
            challenge2.challenge_id,
            "sig2"
        )
        
        assert success is False
        assert "already connected" in msg.lower()
    
    def test_get_artist_by_wallet(self, manager, artist_profile):
        """Test finding artist by wallet address."""
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xArtistWallet"
        )
        manager.connect_wallet(
            artist_profile.artist_id,
            challenge.challenge_id,
            "sig"
        )
        
        found_artist = manager.get_artist_by_wallet("0xArtistWallet")
        assert found_artist is not None
        assert found_artist.artist_id == artist_profile.artist_id


# ============================================================================
# NFT OWNERSHIP TESTS
# ============================================================================

class TestNFTOwnership:
    """Test NFT ownership registration."""
    
    def test_add_owned_nft(self, manager, artist_profile):
        """Test adding owned NFT."""
        # First connect wallet
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xArtistWallet"
        )
        manager.connect_wallet(
            artist_profile.artist_id,
            challenge.challenge_id,
            "sig"
        )
        
        # Add NFT
        success, msg, nft = manager.add_owned_nft(
            artist_profile.artist_id,
            "token_123",
            "0xContractAddress"
        )
        
        assert success is True
        assert nft is not None
        assert nft.nft_id == "token_123"
        assert nft.contract_address == "0xContractAddress"
        assert nft.verification_status == VerificationStatus.VERIFIED
    
    def test_add_nft_without_wallet(self, manager, artist_profile):
        """Test adding NFT without connected wallet fails."""
        success, msg, nft = manager.add_owned_nft(
            artist_profile.artist_id,
            "token_123",
            "0xContract"
        )
        
        assert success is False
        assert "no wallet" in msg.lower()
    
    def test_get_artist_nfts(self, manager, artist_profile):
        """Test retrieving artist NFTs."""
        # Connect wallet and add NFTs
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xArtistWallet"
        )
        manager.connect_wallet(
            artist_profile.artist_id,
            challenge.challenge_id,
            "sig"
        )
        
        manager.add_owned_nft(artist_profile.artist_id, "token_1", "0xContract1")
        manager.add_owned_nft(artist_profile.artist_id, "token_2", "0xContract1")
        
        nfts = manager.get_artist_nfts(artist_profile.artist_id, "owned")
        
        assert len(nfts) == 2
        assert any(n.nft_id == "token_1" for n in nfts)
        assert any(n.nft_id == "token_2" for n in nfts)


# ============================================================================
# IDENTITY VERIFICATION TESTS
# ============================================================================

class TestIdentityVerification:
    """Test artist identity verification."""
    
    def test_verify_artist_identity_kyc(self, manager, artist_profile):
        """Test verifying artist identity via KYC."""
        success, msg = manager.verify_artist_identity(
            artist_profile.artist_id,
            kyc_provider="stripe",
            kyc_verification_id="verify_stripe_123"
        )
        
        assert success is True
        
        profile = manager.get_artist_profile(artist_profile.artist_id)
        assert profile.identity_verified is True
        assert profile.kyc_provider == "stripe"
        assert profile.kyc_verification_id == "verify_stripe_123"
    
    def test_mark_as_dcmx_verified_artist_missing_wallet(self, manager, artist_profile):
        """Test DCMX verification fails without wallet."""
        success, msg = manager.mark_as_dcmx_verified_artist(artist_profile.artist_id)
        
        assert success is False
        assert "wallet" in msg.lower()
    
    def test_mark_as_dcmx_verified_artist_complete_flow(self, manager, artist_profile):
        """Test complete DCMX artist verification flow."""
        # 1. Verify email
        artist_profile.email_verified = True
        artist_profile.email_verified_at = datetime.now(timezone.utc).isoformat()
        
        # 2. Connect wallet
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xArtistWallet"
        )
        manager.connect_wallet(
            artist_profile.artist_id,
            challenge.challenge_id,
            "sig"
        )
        
        # 3. Verify identity
        manager.verify_artist_identity(
            artist_profile.artist_id,
            kyc_provider="stripe",
            kyc_verification_id="verify_123"
        )
        
        # 4. Mark as DCMX verified
        success, msg = manager.mark_as_dcmx_verified_artist(artist_profile.artist_id)
        
        assert success is True
        assert "dcmx" in msg.lower()
        
        profile = manager.get_artist_profile(artist_profile.artist_id)
        assert profile.dcmx_verified_artist is True
        assert profile.profile_verified is True


# ============================================================================
# ROYALTY TESTS
# ============================================================================

class TestRoyaltySettings:
    """Test royalty configuration."""
    
    def test_update_royalty_settings(self, manager, artist_profile):
        """Test updating royalty percentages."""
        success, msg = manager.update_royalty_settings(
            artist_profile.artist_id,
            primary_royalty=15.0,
            secondary_royalty=8.0,
            payment_address="0xRoyaltyWallet"
        )
        
        assert success is True
        
        profile = manager.get_artist_profile(artist_profile.artist_id)
        assert profile.royalty_settings.primary_royalty_percent == 15.0
        assert profile.royalty_settings.secondary_royalty_percent == 8.0
        assert profile.royalty_settings.royalty_payment_address == "0xRoyaltyWallet"
    
    def test_royalty_percentage_validation(self, manager, artist_profile):
        """Test rejecting invalid royalty percentages."""
        # Too high
        success, msg = manager.update_royalty_settings(
            artist_profile.artist_id,
            primary_royalty=100.0,
            secondary_royalty=5.0
        )
        assert success is False
        
        # Negative
        success, msg = manager.update_royalty_settings(
            artist_profile.artist_id,
            primary_royalty=-5.0,
            secondary_royalty=5.0
        )
        assert success is False


# ============================================================================
# VERIFICATION STATUS TESTS
# ============================================================================

class TestVerificationStatus:
    """Test verification status reporting."""
    
    def test_get_verification_status_unverified(self, manager, artist_profile):
        """Test verification status for unverified artist."""
        status = manager.get_verification_status(artist_profile.artist_id)
        
        assert status["dcmx_verified"] is False
        assert status["wallet_connected"] is False
        assert status["email_verified"] is False
        assert status["identity_verified"] is False
        assert status["nfts_registered"] == 0
    
    def test_get_verification_status_fully_verified(self, manager, artist_profile):
        """Test verification status for fully verified artist."""
        # Connect wallet
        challenge = manager.create_wallet_connection_challenge(
            artist_profile.artist_id,
            "0xArtistWallet"
        )
        manager.connect_wallet(
            artist_profile.artist_id,
            challenge.challenge_id,
            "sig"
        )
        
        # Add NFT
        manager.add_owned_nft(artist_profile.artist_id, "token_1", "0xContract")
        
        # Verify email and identity
        artist_profile.email_verified = True
        artist_profile.email_verified_at = datetime.now(timezone.utc).isoformat()
        
        manager.verify_artist_identity(artist_profile.artist_id)
        
        # Get status
        status = manager.get_verification_status(artist_profile.artist_id)
        
        assert status["wallet_connected"] is True
        assert status["nfts_registered"] == 1
        assert status["requirements_met"]["wallet"] is True
        assert status["requirements_met"]["email"] is True
        assert status["requirements_met"]["identity"] is True


# ============================================================================
# NFT OWNERSHIP VERIFIER TESTS
# ============================================================================

class TestNFTOwnershipVerifier:
    """Test NFT ownership verification against blockchain."""
    
    @pytest.mark.asyncio
    async def test_verify_nft_ownership_success(self, verifier, mock_provider):
        """Test successful NFT ownership verification."""
        # Set up mock data
        mock_provider.set_mock_ownership(
            "0xContractAddress",
            "token_123",
            "0xOwnerWallet"
        )
        
        # Verify ownership
        verified, msg, result = await verifier.verify_nft_ownership(
            "0xContractAddress",
            "token_123",
            "0xOwnerWallet"
        )
        
        assert verified is True
        assert result is not None
        # Owner address is lowercased internally
        assert result.owner_address.lower() == "0xownerwallet"
    
    @pytest.mark.asyncio
    async def test_verify_nft_ownership_mismatch(self, verifier, mock_provider):
        """Test NFT ownership verification failure."""
        mock_provider.set_mock_ownership(
            "0xContractAddress",
            "token_123",
            "0xRealOwner"
        )
        
        verified, msg, result = await verifier.verify_nft_ownership(
            "0xContractAddress",
            "token_123",
            "0xClaimedOwner"
        )
        
        assert verified is False
        assert "owned by" in msg.lower()
    
    @pytest.mark.asyncio
    async def test_verify_batch_ownership(self, verifier, mock_provider):
        """Test verifying multiple NFT ownerships."""
        mock_provider.set_mock_ownership("0xContract1", "token1", "0xWallet1")
        mock_provider.set_mock_ownership("0xContract1", "token2", "0xWallet1")
        
        nfts = [
            ("0xContract1", "token1", "0xWallet1"),
            ("0xContract1", "token2", "0xWallet1"),
            ("0xContract2", "token3", "0xWallet2"),
        ]
        
        results = await verifier.verify_batch_ownership(nfts)
        
        assert len(results) == 3
        assert results["0xContract1:token1"][0] is True
        assert results["0xContract1:token2"][0] is True
    
    @pytest.mark.asyncio
    async def test_verify_contract_legitimacy(self, verifier, mock_provider):
        """Test contract legitimacy verification."""
        contract = ContractInterface(
            address="0xContractAddress",
            network=BlockchainNetwork.ETHEREUM,
            token_standard=TokenStandard.ERC_721,
            name="ArtistNFTs",
            verified_contract=True
        )
        
        mock_provider.set_mock_contract("0xContractAddress", contract)
        
        valid, msg, info = await verifier.verify_contract_legitimacy(
            "0xContractAddress",
            TokenStandard.ERC_721
        )
        
        assert valid is True
        assert info is not None
        assert info.name == "ArtistNFTs"


# ============================================================================
# CONTENT WATERMARK LINK TESTS
# ============================================================================

class TestContentWatermarkLink:
    """Test linking NFTs to watermarked content."""
    
    def test_link_nft_to_content(self, verifier):
        """Test linking NFT to DCMX content."""
        link = verifier.link_nft_to_content(
            nft_id="token_123",
            contract_address="0xContractAddress",
            dcmx_content_hash="abc123def456",
            watermark_proof_chain_id="chain_uuid_123"
        )
        
        assert link.nft_id == "token_123"
        assert link.dcmx_content_hash == "abc123def456"
        assert link.watermark_proof_chain_id == "chain_uuid_123"
    
    def test_verify_nft_watermark_match(self, verifier):
        """Test verifying watermark matches for NFT."""
        # Link NFT to content
        verifier.link_nft_to_content(
            nft_id="token_123",
            contract_address="0xContract",
            dcmx_content_hash="content_hash_123",
            watermark_proof_chain_id="chain_123"
        )
        
        # Verify match
        verified, msg, confidence = verifier.verify_nft_watermark_match(
            nft_id="token_123",
            watermark_proof_chain_id="chain_123",
            dcmx_content_hash="content_hash_123",
            title="Song Title",
            artist="Artist Name"
        )
        
        assert verified is True
        assert confidence > 80.0
    
    def test_verify_nft_watermark_mismatch(self, verifier):
        """Test rejecting watermark mismatch."""
        verifier.link_nft_to_content(
            nft_id="token_123",
            contract_address="0xContract",
            dcmx_content_hash="hash_abc",
            watermark_proof_chain_id="chain_123"
        )
        
        # Wrong content hash
        verified, msg, confidence = verifier.verify_nft_watermark_match(
            nft_id="token_123",
            watermark_proof_chain_id="chain_123",
            dcmx_content_hash="hash_wrong"
        )
        
        assert verified is False
        assert confidence == 0.0
    
    def test_register_verified_creator(self, verifier):
        """Test registering verified creator."""
        verifier.register_verified_creator("0xArtistWallet")
        
        assert verifier.is_verified_creator("0xArtistWallet") is True
        assert verifier.is_verified_creator("0xOtherWallet") is False
    
    def test_get_verification_report(self, verifier):
        """Test generating verification report."""
        verifier.link_nft_to_content(
            nft_id="token_123",
            contract_address="0xContract",
            dcmx_content_hash="hash_123",
            watermark_proof_chain_id="chain_123"
        )
        
        report = verifier.get_verification_report("token_123")
        
        assert report["nft_id"] == "token_123"
        assert report["contract_address"] == "0xContract"
        assert "watermark_verified" in report


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestFullArtistWorkflow:
    """Test complete artist onboarding and NFT management workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_artist_to_nft_workflow(self, manager, verifier, mock_provider):
        """Test complete workflow: Create artist → Connect wallet → Verify NFT."""
        
        # 1. Create artist profile
        artist = manager.create_artist_profile(
            legal_name="Taylor Swift",
            artist_name="TaylorSwift",
            email="taylor@example.com"
        )
        assert artist.artist_id is not None
        
        # 2. Connect wallet
        challenge = manager.create_wallet_connection_challenge(
            artist.artist_id,
            "0xTaylorSwift"
        )
        success, msg, wallet = manager.connect_wallet(
            artist.artist_id,
            challenge.challenge_id,
            "metamask_signature_123"
        )
        assert success is True
        
        # 3. Verify identity
        manager.verify_artist_identity(
            artist.artist_id,
            kyc_provider="stripe",
            kyc_verification_id="kyc_123"
        )
        
        # 4. Verify email
        artist.email_verified = True
        
        # 5. Mark as DCMX verified
        success, msg = manager.mark_as_dcmx_verified_artist(artist.artist_id)
        assert success is True
        
        # 6. Set up NFT contract on blockchain
        contract = ContractInterface(
            address="0xMusicNFT",
            network=BlockchainNetwork.ETHEREUM,
            token_standard=TokenStandard.ERC_721,
            name="TaylorSwiftNFTs",
            verified_contract=True
        )
        mock_provider.set_mock_contract("0xMusicNFT", contract)
        
        # 7. Verify NFT ownership
        mock_provider.set_mock_ownership(
            "0xMusicNFT",
            "ts_song_001",
            "0xTaylorSwift"
        )
        
        verified, msg, result = await verifier.verify_nft_ownership(
            "0xMusicNFT",
            "ts_song_001",
            "0xTaylorSwift"
        )
        assert verified is True
        
        # 8. Register NFT in artist profile
        success, msg, nft = manager.add_owned_nft(
            artist.artist_id,
            "ts_song_001",
            "0xMusicNFT"
        )
        assert success is True
        
        # 9. Link NFT to watermarked content
        verifier.link_nft_to_content(
            nft_id="ts_song_001",
            contract_address="0xMusicNFT",
            dcmx_content_hash="sha256_song_hash",
            watermark_proof_chain_id="proof_chain_uuid"
        )
        
        # 10. Verify watermark match
        verified, msg, confidence = verifier.verify_nft_watermark_match(
            nft_id="ts_song_001",
            watermark_proof_chain_id="proof_chain_uuid",
            dcmx_content_hash="sha256_song_hash",
            title="Anti-Hero",
            artist="Taylor Swift"
        )
        assert verified is True
        assert confidence > 80.0
        
        # 11. Check final artist status
        status = manager.get_verification_status(artist.artist_id)
        assert status["dcmx_verified"] is True
        assert status["wallet_connected"] is True
        assert status["nfts_registered"] == 1
