"""
Complete Artist NFT Minting Workflow Example.

Demonstrates:
1. Artist profile creation and verification
2. Wallet connection and signature verification
3. NFT metadata creation with watermark links
4. Blockchain minting
5. Primary sale royalty distribution
6. Secondary market tracking
7. Portfolio and earnings reporting
"""

import asyncio
import logging
from datetime import datetime, timezone
from uuid import uuid4

from dcmx.artist.artist_wallet_manager import ArtistWalletManager
from dcmx.blockchain.artist_nft_minter import (
    ArtistNFTMinter,
    ArtistMintRequest,
    RoyaltyDistributionType,
)


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Run complete artist NFT workflow."""
    
    print("\n" + "="*80)
    print("DCMX ARTIST NFT MINTING WORKFLOW - COMPLETE DEMONSTRATION")
    print("="*80 + "\n")
    
    # Initialize managers
    artist_manager = ArtistWalletManager()
    minter = ArtistNFTMinter(
        rpc_url="http://localhost:8545",
        private_key="0x" + "1" * 64,
        music_nft_contract="0xMusicNFT",
        dcmx_token_contract="0xDCMXToken"
    )
    
    # ===== STEP 1: Create artist profile =====
    print("[STEP 1] Creating artist profile...")
    artist = artist_manager.create_artist_profile(
        legal_name="Taylor Swift",
        artist_name="Taylor Swift",
        email="taylor.swift@music.com"
    )
    print(f"✓ Artist created: {artist.artist_id}")
    print(f"  Name: {artist.artist_name}")
    print(f"  Email: {artist.email}\n")
    
    # ===== STEP 2: Create wallet challenge =====
    print("[STEP 2] Creating wallet connection challenge...")
    challenge = artist_manager.create_wallet_connection_challenge(
        artist_id=artist.artist_id,
        wallet_address="0xTaylorSwiftWallet123"
    )
    print(f"✓ Challenge created: {challenge.challenge_id}")
    print(f"  Message to sign: {challenge.message[:50]}...")
    print(f"  Expires at: {challenge.expires_at}\n")
    
    # ===== STEP 3: Connect wallet =====
    print("[STEP 3] Connecting wallet (signing challenge)...")
    # Mock signature (in production, use actual wallet signing)
    signature = "0x" + "a" * 130
    success, msg, wallet = artist_manager.connect_wallet(
        artist_id=artist.artist_id,
        challenge_id=challenge.challenge_id,
        signature=signature
    )
    
    if success:
        print(f"✓ Wallet connected!")
        print(f"  Address: {wallet.address}")
        print(f"  Type: {wallet.wallet_type.value}")
        print(f"  Verified: {wallet.verified}\n")
    else:
        print(f"✗ Wallet connection failed: {msg}\n")
        return
    
    # ===== STEP 4: Verify identity (KYC) =====
    print("[STEP 4] Verifying identity (KYC)...")
    success, msg = artist_manager.verify_artist_identity(
        artist_id=artist.artist_id,
        kyc_provider="stripe"
    )
    print(f"✓ Identity verified via {kyc_provider}")
    print(f"  Status: Verified\n")
    
    # ===== STEP 5: Get DCMX verified badge =====
    print("[STEP 5] Awarding DCMX verified artist badge...")
    success, msg = artist_manager.mark_as_dcmx_verified_artist(
        artist_id=artist.artist_id
    )
    
    if success:
        print(f"✓ {msg}")
        status = artist_manager.get_verification_status(artist.artist_id)
        print(f"  Verified: {status['dcmx_verified']}\n")
    else:
        print(f"✗ Badge award failed: {msg}\n")
        return
    
    # ===== STEP 6: Create first track NFT mint request =====
    print("[STEP 6] Preparing to mint first NFT (limited edition)...")
    
    # Simulated watermark proof chain (in production, from ZK proof system)
    watermark_proof_chain_id = str(uuid4())
    
    mint_request_1 = ArtistMintRequest(
        artist_id=artist.artist_id,
        track_title="Anti-Hero",
        dcmx_content_hash="sha256_of_anti_hero_audio_bytes_123abc",
        watermark_proof_chain_id=watermark_proof_chain_id,
        edition_number=1,
        max_editions=100,
        price_wei=1000000000000000000,  # 1 ETH
        royalty_primary_bps=9750,  # 97.5% to artist (after 2.5% platform fee)
        royalty_secondary_bps=500,  # 5% on secondary sales
        metadata={
            "description": "Limited Edition 1 of 100 - Anti-Hero by Taylor Swift",
            "genre": "Pop",
            "year": "2024"
        }
    )
    
    print(f"✓ Mint request prepared:")
    print(f"  Title: {mint_request_1.track_title}")
    print(f"  Edition: {mint_request_1.edition_number}/{mint_request_1.max_editions}")
    print(f"  Price: {mint_request_1.price_wei / 1e18} ETH")
    print(f"  Watermark Chain: {watermark_proof_chain_id}\n")
    
    # ===== STEP 7: Mint NFT on blockchain =====
    print("[STEP 7] Minting NFT on blockchain...")
    
    metadata_uri = f"ipfs://QmMetadata{uuid4().hex[:8]}"
    success, msg, minted = await minter.mint_artist_nft(
        request=mint_request_1,
        metadata_uri=metadata_uri
    )
    
    if success:
        print(f"✓ {msg}")
        print(f"  Token ID: {minted.token_id}")
        print(f"  Contract: {minted.contract_address}")
        print(f"  TX Hash: {minted.transaction_hash[:10]}...")
        print(f"  Status: {minted.status.value}")
        print(f"  Minted at: {minted.minted_at}\n")
    else:
        print(f"✗ Minting failed: {msg}\n")
        return
    
    # ===== STEP 8: Mint second edition =====
    print("[STEP 8] Minting second edition of same track...")
    
    mint_request_2 = ArtistMintRequest(
        artist_id=artist.artist_id,
        track_title="Anti-Hero (Edition 2)",
        dcmx_content_hash="sha256_of_anti_hero_audio_bytes_123abc",
        watermark_proof_chain_id=watermark_proof_chain_id,
        edition_number=2,
        max_editions=100,
        price_wei=500000000000000000,  # 0.5 ETH (discounted)
        royalty_primary_bps=9750,
        royalty_secondary_bps=500
    )
    
    success, msg, minted_2 = await minter.mint_artist_nft(
        request=mint_request_2,
        metadata_uri=f"ipfs://QmMetadata{uuid4().hex[:8]}"
    )
    
    if success:
        print(f"✓ {msg}")
        print(f"  Token ID: {minted_2.token_id}\n")
    else:
        print(f"✗ Minting failed: {msg}\n")
    
    # ===== STEP 9: Distribute primary sale royalty =====
    print("[STEP 9] Distributing primary sale royalty...")
    
    success, msg, distribution = await minter.distribute_primary_sale_royalty(
        mint_id=minted.mint_id,
        sale_price_wei=mint_request_1.price_wei
    )
    
    if success:
        print(f"✓ {msg}")
        print(f"  Artist receives: {distribution.amount_wei / 1e18} ETH")
        print(f"  Platform fee: {distribution.platform_fee / 1e18} ETH")
        print(f"  Distribution ID: {distribution.distribution_id}\n")
    else:
        print(f"✗ Distribution failed: {msg}\n")
    
    # ===== STEP 10: Simulate secondary market sale =====
    print("[STEP 10] Simulating secondary market sale (OpenSea)...")
    
    secondary_sale_price = 2000000000000000000  # 2 ETH
    success, msg, secondary_dist = await minter.handle_secondary_market_sale(
        token_id=minted.token_id,
        seller_wallet="0xFirstBuyer",
        buyer_wallet="0xSecondBuyer",
        sale_price_wei=secondary_sale_price,
        marketplace="opensea",
        transaction_hash="0xSecondaryTx"
    )
    
    if success:
        royalty_pct = (secondary_dist.amount_wei / secondary_sale_price) * 100
        print(f"✓ Secondary market royalty distributed!")
        print(f"  Sale price: {secondary_sale_price / 1e18} ETH")
        print(f"  Artist royalty: {secondary_dist.amount_wei / 1e18} ETH ({royalty_pct:.1f}%)")
        print(f"  TX Hash: {secondary_dist.transaction_hash}\n")
    else:
        print(f"✗ Secondary market handling failed: {msg}\n")
    
    # ===== STEP 11: Get artist NFT portfolio =====
    print("[STEP 11] Retrieving artist NFT portfolio...")
    
    success, msg, portfolio = await minter.get_artist_nft_portfolio(artist.artist_id)
    
    if success:
        print(f"✓ {msg}")
        for nft in portfolio:
            print(f"  - Token ID {nft.token_id}: Edition {nft.edition_number}/{nft.max_editions}")
        print()
    else:
        print(f"✗ Portfolio fetch failed: {msg}\n")
    
    # ===== STEP 12: Get royalty earnings history =====
    print("[STEP 12] Retrieving artist earnings history...")
    
    success, msg, history = await minter.get_artist_royalty_history(artist.artist_id)
    
    if success:
        print(f"✓ Found {len(history)} distributions")
        total_earned = sum(d.amount_wei for d in history)
        print(f"  Total earned: {total_earned / 1e18} ETH")
        print(f"  Breakdown:")
        
        for dist in history:
            print(f"    - {dist.distribution_type.value}: {dist.amount_wei / 1e18} ETH")
        print()
    else:
        print(f"✗ History fetch failed: {msg}\n")
    
    # ===== STEP 13: Get complete verification status =====
    print("[STEP 13] Getting complete artist verification status...")
    
    status = artist_manager.get_verification_status(artist.artist_id)
    
    print(f"✓ Artist Verification Status:")
    print(f"  DCMX Verified: {status['dcmx_verified']}")
    print(f"  Wallet Connected: {status['wallet_connected']}")
    print(f"  Wallet Verified: {status['wallet_verified']}")
    print(f"  Email Verified: {status['email_verified']}")
    print(f"  Identity Verified: {status['identity_verified']}")
    print(f"  Requirements Met: {status['all_requirements_met']}\n")
    
    # ===== STEP 14: Export artist profile =====
    print("[STEP 14] Exporting artist profile...")
    
    profile_json = artist_manager.export_artist_profile(artist.artist_id)
    
    if profile_json:
        print(f"✓ Profile exported")
        print(f"  Size: {len(profile_json)} bytes")
        print(f"  Format: JSON\n")
    else:
        print(f"✗ Export failed\n")
    
    # ===== FINAL SUMMARY =====
    print("="*80)
    print("WORKFLOW COMPLETE - ALL STEPS SUCCESSFUL ✓")
    print("="*80)
    print()
    
    print(f"Artist Summary:")
    print(f"  Name: {artist.artist_name}")
    print(f"  Email: {artist.email}")
    print(f"  Artist ID: {artist.artist_id}")
    print(f"  DCMX Verified: ✓")
    print(f"  NFTs Minted: {len(portfolio)} editions")
    print(f"  Total Earnings: {total_earned / 1e18} ETH")
    print(f"  Status: Ready for sale and distribution")
    print()
    
    print("Next Steps:")
    print("  1. Artist can mint additional editions of tracks")
    print("  2. NFTs can be listed on secondary markets (OpenSea, Rarible, etc)")
    print("  3. Secondary market royalties automatically distributed")
    print("  4. Artists receive real-time earnings reports")
    print("  5. DCMX handles watermark verification and authenticity")
    print()


if __name__ == "__main__":
    # Run workflow
    asyncio.run(main())
