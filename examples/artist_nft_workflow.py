"""
Integration Example: Complete Artist NFT Workflow with Watermarks

This example demonstrates the complete flow from artist profile creation
through NFT minting with watermark verification.
"""

import asyncio
from dcmx.artist import (
    ArtistWalletManager,
    NFTOwnershipVerifier,
    MockBlockchainProvider,
    BlockchainNetwork,
    TokenStandard,
    ContractInterface,
    WalletType,
)


async def main():
    """Complete artist to NFT workflow."""
    
    print("=" * 70)
    print("DCMX Artist NFT System - Complete Workflow Example")
    print("=" * 70)
    
    # =========================================================================
    # STEP 1: Artist Profile Creation
    # =========================================================================
    print("\n[STEP 1] Creating Artist Profile...")
    manager = ArtistWalletManager()
    
    artist = manager.create_artist_profile(
        legal_name="Taylor Swift",
        artist_name="TaylorSwift",
        email="taylor.swift@music.com"
    )
    
    print(f"✓ Artist profile created: {artist.artist_id}")
    print(f"  - Name: {artist.artist_name}")
    print(f"  - Email: {artist.email}")
    
    # =========================================================================
    # STEP 2: Wallet Connection
    # =========================================================================
    print("\n[STEP 2] Connecting Wallet...")
    
    # Create challenge
    challenge = manager.create_wallet_connection_challenge(
        artist.artist_id,
        "0xTaylorSwiftWallet123"
    )
    
    print(f"✓ Challenge created: {challenge.challenge_id}")
    print(f"  Message to sign:\n{challenge.message}\n")
    
    # Simulate wallet signature (in production, user signs with MetaMask)
    simulated_signature = "0x" + ("a" * 130)  # Simulated signature
    
    # Verify signature and connect
    success, msg, wallet = manager.connect_wallet(
        artist.artist_id,
        challenge.challenge_id,
        simulated_signature,
        WalletType.METAMASK
    )
    
    if success:
        print(f"✓ Wallet connected successfully")
        print(f"  - Wallet: {wallet.address}")
        print(f"  - Type: {wallet.wallet_type.value}")
        print(f"  - Verified: {wallet.is_verified}")
    else:
        print(f"✗ Failed to connect wallet: {msg}")
        return
    
    # =========================================================================
    # STEP 3: Identity Verification (KYC)
    # =========================================================================
    print("\n[STEP 3] Identity Verification...")
    
    success, msg = manager.verify_artist_identity(
        artist.artist_id,
        kyc_provider="stripe",
        kyc_verification_id="verify_stripe_12345"
    )
    
    print(f"✓ Identity verified via {msg}")
    
    # =========================================================================
    # STEP 4: Email Verification
    # =========================================================================
    print("\n[STEP 4] Email Verification...")
    
    artist = manager.get_artist_profile(artist.artist_id)
    artist.email_verified = True
    
    print(f"✓ Email verified: {artist.email}")
    
    # =========================================================================
    # STEP 5: Mark as DCMX Verified Artist
    # =========================================================================
    print("\n[STEP 5] DCMX Artist Verification...")
    
    success, msg = manager.mark_as_dcmx_verified_artist(artist.artist_id)
    
    if success:
        print(f"✓ {msg}")
        print(f"  Artist now has DCMX verified badge!")
    
    # =========================================================================
    # STEP 6: Set up NFT Blockchain Contract
    # =========================================================================
    print("\n[STEP 6] Setting up NFT Contract...")
    
    provider = MockBlockchainProvider()
    
    # Define NFT contract
    contract = ContractInterface(
        address="0xMusicNFTContractAddress",
        network=BlockchainNetwork.ETHEREUM,
        token_standard=TokenStandard.ERC_721,
        name="TaylorSwift NFTs",
        symbol="TS",
        verified_contract=True,
        royalty_percent=10.0,
        royalty_receiver="0xTaylorSwiftWallet123"
    )
    
    provider.set_mock_contract("0xMusicNFTContractAddress", contract)
    
    print(f"✓ Contract registered: {contract.name}")
    print(f"  - Address: {contract.address}")
    print(f"  - Standard: {contract.token_standard.value}")
    print(f"  - Royalty: {contract.royalty_percent}%")
    
    # =========================================================================
    # STEP 7: Mint NFT (Simulated)
    # =========================================================================
    print("\n[STEP 7] Minting NFT...")
    
    # In production, this would call BlockchainAgent.mint_nft()
    nft_id = "ts_anti_hero_001"
    content_hash = "sha256_of_anti_hero_audio"
    proof_chain_id = "zk_proof_chain_uuid_12345"
    
    # Simulate NFT ownership on blockchain
    provider.set_mock_ownership(
        "0xMusicNFTContractAddress",
        nft_id,
        "0xTaylorSwiftWallet123"
    )
    
    print(f"✓ NFT minted: {nft_id}")
    print(f"  - Content Hash: {content_hash}")
    print(f"  - Proof Chain: {proof_chain_id}")
    
    # =========================================================================
    # STEP 8: Register NFT in Artist Profile
    # =========================================================================
    print("\n[STEP 8] Registering NFT...")
    
    success, msg, nft_record = manager.add_owned_nft(
        artist.artist_id,
        nft_id,
        "0xMusicNFTContractAddress"
    )
    
    if success:
        print(f"✓ NFT registered in artist profile")
        print(f"  - Token ID: {nft_record.nft_id}")
        print(f"  - Status: {nft_record.verification_status.value}")
    
    # =========================================================================
    # STEP 9: Verify NFT Ownership on Blockchain
    # =========================================================================
    print("\n[STEP 9] Verifying NFT Ownership...")
    
    verifier = NFTOwnershipVerifier(provider)
    
    verified, msg, result = await verifier.verify_nft_ownership(
        "0xMusicNFTContractAddress",
        nft_id,
        "0xTaylorSwiftWallet123"
    )
    
    if verified:
        print(f"✓ NFT ownership verified on blockchain")
        print(f"  - Owner: {result.owner_address}")
        print(f"  - Block: {result.block_number}")
    else:
        print(f"✗ Failed to verify: {msg}")
    
    # =========================================================================
    # STEP 10: Link to Watermarked Content
    # =========================================================================
    print("\n[STEP 10] Linking to Watermarked Content...")
    
    link = verifier.link_nft_to_content(
        nft_id=nft_id,
        contract_address="0xMusicNFTContractAddress",
        dcmx_content_hash=content_hash,
        watermark_proof_chain_id=proof_chain_id
    )
    
    print(f"✓ NFT linked to watermarked content")
    print(f"  - Content Hash: {link.dcmx_content_hash}")
    print(f"  - Proof Chain: {link.watermark_proof_chain_id}")
    
    # =========================================================================
    # STEP 11: Verify Watermark Authenticity
    # =========================================================================
    print("\n[STEP 11] Verifying Watermark Authenticity...")
    
    verified, msg, confidence = verifier.verify_nft_watermark_match(
        nft_id=nft_id,
        watermark_proof_chain_id=proof_chain_id,
        dcmx_content_hash=content_hash,
        title="Anti-Hero",
        artist="Taylor Swift",
        fingerprint_hash="perceptual_fingerprint_hash"
    )
    
    if verified:
        print(f"✓ Watermark authenticity verified")
        print(f"  - Confidence: {confidence}%")
        print(f"  - Message: {msg}")
    else:
        print(f"✗ Watermark verification failed: {msg}")
    
    # =========================================================================
    # STEP 12: Update Royalty Settings
    # =========================================================================
    print("\n[STEP 12] Configuring Royalties...")
    
    success, msg = manager.update_royalty_settings(
        artist.artist_id,
        primary_royalty=10.0,
        secondary_royalty=5.0,
        payment_address="0xTaylorSwiftRoyalties"
    )
    
    if success:
        print(f"✓ Royalty settings configured")
        artist = manager.get_artist_profile(artist.artist_id)
        print(f"  - Primary: {artist.royalty_settings.primary_royalty_percent}%")
        print(f"  - Secondary: {artist.royalty_settings.secondary_royalty_percent}%")
        print(f"  - Payment: {artist.royalty_settings.royalty_payment_address}")
    
    # =========================================================================
    # STEP 13: Final Status Report
    # =========================================================================
    print("\n[STEP 13] Final Status Report...")
    
    status = manager.get_verification_status(artist.artist_id)
    
    print(f"\n{'ARTIST VERIFICATION STATUS':^70}")
    print("=" * 70)
    print(f"  Artist ID:             {status['artist_id']}")
    print(f"  DCMX Verified:         {'✓ YES' if status['dcmx_verified'] else '✗ NO'}")
    print(f"  Wallet Connected:      {'✓ YES' if status['wallet_connected'] else '✗ NO'}")
    print(f"  Wallet Verified:       {'✓ YES' if status['wallet_verified'] else '✗ NO'}")
    print(f"  Email Verified:        {'✓ YES' if status['email_verified'] else '✗ NO'}")
    print(f"  Identity Verified:     {'✓ YES' if status['identity_verified'] else '✗ NO'}")
    print(f"  NFTs Registered:       {status['nfts_registered']}")
    print(f"  Wallets Connected:     {status['wallets_connected']}")
    print(f"  Verification Status:   {status['verification_status']}")
    print(f"  Verified At:           {status['verification_timestamp']}")
    print("\n  Requirements Met:")
    for req, met in status['requirements_met'].items():
        print(f"    - {req.capitalize():20} {'✓' if met else '✗'}")
    print("=" * 70)
    
    # =========================================================================
    # STEP 14: Export Profile
    # =========================================================================
    print("\n[STEP 14] Exporting Profile...")
    
    profile_json = manager.export_artist_profile(artist.artist_id)
    print(f"✓ Profile exported (JSON format)")
    print(f"  Size: {len(profile_json)} bytes")
    
    # Print key fields
    import json
    profile_dict = json.loads(profile_json)
    print(f"  - Legal Name: {profile_dict['legal_name']}")
    print(f"  - Artist Name: {profile_dict['artist_name']}")
    print(f"  - Profile Verified: {profile_dict['profile_verified']}")
    print(f"  - DCMX Verified: {profile_dict['dcmx_verified_artist']}")
    
    # =========================================================================
    # COMPLETION
    # =========================================================================
    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE! ✓")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Artist can mint more NFTs")
    print("2. NFTs can be listed on secondary markets")
    print("3. Royalties distributed automatically")
    print("4. Watermarks prevent unauthorized copying")
    print("5. ZK proofs verify authenticity without revealing content")


if __name__ == "__main__":
    asyncio.run(main())
