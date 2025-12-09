"""
DCMX Royalty and Rewards System - Implementation Examples

Complete working examples for all royalty and reward operations.
"""

# ============================================================================
# EXAMPLE 1: COMPLETE NFT PURCHASE WORKFLOW
# ============================================================================

async def example_complete_nft_purchase():
    """
    Complete workflow: User purchases NFT, gets certificate, royalties distributed.
    """
    from dcmx.royalties import (
        RoyaltyPaymentStructure,
        RewardClaimVerifier,
        BlockchainIntegration,
        RewardDistributionEngine
    )
    
    # Step 1: Initialize systems
    royalty = RoyaltyPaymentStructure()
    verifier = RewardClaimVerifier(royalty)
    blockchain = BlockchainIntegration(
        rpc_url="https://rpc.polygon.com",
        private_key="sk_live_...",
        nft_contract_address="0x123456789abcdef",
        token_contract_address="0xabcdef123456789",
        royalty_distributor_address="0x9876543210fedcba"
    )
    engine = RewardDistributionEngine(royalty, verifier, blockchain)
    
    # Step 2: User purchases Edition #1 of your song for $50 USD
    print("🎵 NFT PURCHASE WORKFLOW")
    print("=" * 60)
    
    nft_tx_hash, token_id = await engine.process_nft_sale(
        song_title="My Beautiful Song",
        artist="Artist Name",
        content_hash="sha256_abc123def456",
        edition_number=1,  # Edition 1 of 100
        max_editions=100,
        buyer_wallet="0xBuyerWalletAddress",
        purchase_price_usd=50.0,
        purchase_price_tokens=500,  # 50 tokens per $1
        watermark_hash="watermark_hash_abc123",
        perceptual_fingerprint="fingerprint_abc123"
    )
    
    print(f"✅ NFT Minted: {nft_tx_hash}")
    print(f"   Token ID: {token_id}")
    
    # Step 3: Verify certificate was issued
    certs = royalty.list_user_certificates("0xBuyerWalletAddress")
    print(f"\n🎫 Certificate issued:")
    for cert in certs:
        metadata = cert.get_certificate_metadata()
        for key, value in metadata.items():
            print(f"   {key}: {value}")
    
    # Step 4: Verify royalties were distributed
    artist_royalties = royalty.get_artist_royalties("Artist Name")
    print(f"\n💰 Artist Royalties Earned: ${artist_royalties:.2f}")
    
    platform_pool = royalty.get_platform_royalties()
    print(f"💰 Platform Pool: ${platform_pool:.2f}")
    
    node_pool = royalty.get_node_operator_pool()
    print(f"💰 Node Operator Pool: ${node_pool:.2f}")
    
    # Step 5: Show detailed payment breakdown
    payments = [p for p in royalty.royalty_payments.values() if p.is_primary_sale]
    if payments:
        payment = payments[-1]
        breakdown = payment.get_payout_breakdown()
        print(f"\n💸 Royalty Split for ${payment.sale_price_usd:.2f} sale:")
        for recipient, (wallet, amount, percentage) in breakdown.items():
            print(f"   {recipient.value:20} {percentage:5.1f}% = ${amount:.2f}")


# ============================================================================
# EXAMPLE 2: SHARING AND LISTENING REWARDS
# ============================================================================

async def example_sharing_listening_rewards():
    """
    Workflow: Alice shares with Bob, Bob listens, both earn rewards.
    """
    from dcmx.royalties import RoyaltyPaymentStructure
    
    royalty = RoyaltyPaymentStructure()
    
    print("\n🎁 SHARING AND LISTENING REWARDS")
    print("=" * 60)
    
    # Step 1: Alice shares song with Bob
    print("\n1️⃣ Alice shares song with Bob")
    share_reward = royalty.record_sharing_event(
        sharer_wallet="0xAlice",
        song_content_hash="sha256_abc123",
        shared_with_wallet="0xBob",
        base_reward=1
    )
    print(f"   Sharing reward created: {share_reward.reward_id}")
    print(f"   Alice earned: {share_reward.base_reward_tokens} token")
    
    # Step 2: Bob listens to the shared song
    print("\n2️⃣ Bob listens to shared song (95% completion)")
    listen_reward = royalty.record_listening_event(
        listener_wallet="0xBob",
        song_content_hash="sha256_abc123",
        sharer_wallet="0xAlice",
        listen_duration_seconds=240,  # 4 minutes
        completion_percentage=95.0,   # 95% of song
        base_reward=2
    )
    print(f"   Listening reward created: {listen_reward.reward_id}")
    print(f"   Bob earned: {listen_reward.total_reward} tokens")
    print(f"      - Base: {listen_reward.base_reward_tokens}")
    print(f"      - 95% completion bonus: {listen_reward.completion_bonus}")
    
    # Step 3: Apply multiplier to Alice's share reward
    print("\n3️⃣ Alice gets listening multiplier bonus")
    updated_share = royalty.apply_listening_multiplier(
        share_reward.reward_id,
        multiplier=1.5
    )
    print(f"   Alice's share reward updated: 1.0 × 1.5 = {updated_share.total_reward} tokens")
    
    # Step 4: Calculate totals
    print("\n📊 REWARD SUMMARY")
    alice_total = royalty.calculate_total_sharing_tokens("0xAlice")
    bob_sharing = royalty.calculate_total_sharing_tokens("0xBob")
    bob_listening = royalty.calculate_total_listening_tokens("0xBob")
    
    print(f"   Alice's total: {alice_total} tokens (from sharing + bonus)")
    print(f"   Bob's total: {bob_sharing + bob_listening} tokens (sharing + listening)")


# ============================================================================
# EXAMPLE 3: BANDWIDTH REWARDS FOR LORA NODES
# ============================================================================

async def example_bandwidth_rewards():
    """
    Workflow: LoRa node serves content to 50 listeners, earns tokens.
    """
    from dcmx.royalties import RoyaltyPaymentStructure
    
    royalty = RoyaltyPaymentStructure()
    
    print("\n📡 BANDWIDTH REWARDS FOR LORA NODES")
    print("=" * 60)
    
    # Step 1: Node serves content
    print("\n1️⃣ LoRa node serving content...")
    bandwidth = royalty.record_bandwidth_serving(
        node_id="node_lora_xyz_123",
        song_content_hash="sha256_abc123",
        bytes_served=100_000_000,     # 100 MB
        listeners_served=50,           # 50 unique listeners
        transmission_time_seconds=3600, # 1 hour
        base_reward=5
    )
    
    print(f"   Bandwidth serving recorded: {bandwidth.reward_id}")
    print(f"   Data served: {bandwidth.bytes_served / (1024**2):.1f} MB")
    print(f"   Listeners reached: {bandwidth.listeners_served}")
    print(f"   Service time: {bandwidth.transmission_time_seconds} seconds")
    
    # Step 2: Calculate rewards
    print("\n2️⃣ Calculating reward breakdown:")
    print(f"   Base reward: {bandwidth.base_reward_tokens} tokens")
    print(f"   Bandwidth bonus: {bandwidth.bandwidth_bonus:.2f} tokens (1 per 100MB)")
    print(f"   Listener bonus: {bandwidth.listener_bonus:.2f} tokens (0.5 per listener)")
    print(f"   TOTAL: {bandwidth.total_reward:.2f} tokens")
    
    # Step 3: Multiple serving events (accumulated)
    print("\n3️⃣ Node accumulates more rewards...")
    for i in range(3):
        royalty.record_bandwidth_serving(
            node_id="node_lora_xyz_123",
            song_content_hash=f"sha256_{i}",
            bytes_served=50_000_000,
            listeners_served=25,
            transmission_time_seconds=1800,
            base_reward=5
        )
    
    # Step 4: Total rewards for node
    node_total = royalty.calculate_total_bandwidth_tokens("node_lora_xyz_123")
    print(f"\n   Total accumulated: {node_total:.2f} tokens")


# ============================================================================
# EXAMPLE 4: REWARD CLAIM WITH VERIFIER QUORUM
# ============================================================================

async def example_reward_claim_verification():
    """
    Workflow: User submits claim → Verifier quorum approves → Tokens minted.
    """
    from dcmx.royalties import (
        RoyaltyPaymentStructure,
        RewardClaimVerifier,
        RewardType,
        VerifierNodeStatus
    )
    
    royalty = RoyaltyPaymentStructure()
    verifier = RewardClaimVerifier(royalty)
    
    print("\n✅ REWARD CLAIM AND VERIFIER QUORUM")
    print("=" * 60)
    
    # Step 1: Accumulate sharing rewards
    print("\n1️⃣ Alice accumulates sharing rewards...")
    for i in range(5):
        royalty.record_sharing_event(
            sharer_wallet="0xAlice",
            song_content_hash="sha256_abc123",
            shared_with_wallet=f"0xUser{i}",
            base_reward=1
        )
    
    total_earned = royalty.calculate_total_sharing_tokens("0xAlice")
    print(f"   Total sharing rewards: {total_earned} tokens")
    
    # Step 2: Create claim with ZK proof
    print("\n2️⃣ Alice submits reward claim with ZK proof...")
    claim = royalty.create_reward_claim(
        claimant_wallet="0xAlice",
        claim_type=RewardType.SHARING,
        song_content_hash="sha256_abc123",
        total_tokens_claimed=total_earned,
        activity_count=5
    )
    print(f"   Claim created: {claim.claim_id}")
    print(f"   Tokens claimed: {claim.total_tokens_claimed}")
    print(f"   Status: {claim.claim_id}")
    
    # Step 3: Register verifier nodes
    print("\n3️⃣ Registering verifier nodes...")
    for i in range(4):
        verifier.register_verifier_node(f"verifier_node_{i+1}")
    print(f"   Registered 4 verifier nodes")
    
    # Step 4: Distribute to verifiers
    print("\n4️⃣ Distributing claim to verifiers...")
    verifiers = verifier.distribute_claim_to_verifiers(claim.claim_id)
    print(f"   Distributed to {len(verifiers)} verifiers")
    
    # Step 5: Verifiers check and approve
    print("\n5️⃣ Verifiers independently verify ZK proof...")
    approvals = 0
    for node_id in ["verifier_node_1", "verifier_node_2", "verifier_node_3"]:
        verifier.submit_verifier_approval(
            verifier_node_id=node_id,
            claim_id=claim.claim_id,
            status=VerifierNodeStatus.APPROVED,
            zk_proof_result=True,
            notes="ZK proof verified successfully"
        )
        approvals += 1
        print(f"   ✓ {node_id} approved")
    
    # Step 6: Check quorum status
    print("\n6️⃣ Checking quorum status...")
    status = verifier.get_claim_verification_status(claim.claim_id)
    print(f"   Approvals: {status['approvals']}/4")
    print(f"   Status: {status['status']}")
    
    if status['status'] == "APPROVED":
        print(f"   ✅ QUORUM REACHED - Claim approved!")
        
        # Step 7: Approve and mint tokens
        print("\n7️⃣ Minting tokens on blockchain...")
        royalty.approve_and_mint_tokens(
            claim.claim_id,
            blockchain_tx_hash="0xabcdef1234567890"
        )
        print(f"   ✅ Tokens minted: {claim.total_tokens_verified} DCMX")
        print(f"   Transaction: 0xabcdef1234567890")


# ============================================================================
# EXAMPLE 5: SECONDARY MARKET RESALE WITH ROYALTIES
# ============================================================================

async def example_secondary_market_resale():
    """
    Workflow: User resells NFT on secondary market, artist gets royalties.
    """
    from dcmx.royalties import RoyaltyPaymentStructure
    
    royalty = RoyaltyPaymentStructure()
    
    print("\n🔄 SECONDARY MARKET RESALE")
    print("=" * 60)
    
    # Step 1: Original purchase (primary sale)
    print("\n1️⃣ Alice purchases Edition #5 for $50")
    primary = royalty.process_primary_sale(
        song_title="My Song",
        artist="Artist Name",
        content_hash="sha256_abc123",
        purchase_price_usd=50.0,
        purchase_price_tokens=500,
        nft_contract_address="0x123456",
        token_id=5
    )
    print(f"   Artist receives: ${primary.artist_payout_usd:.2f} (70%)")
    print(f"   Platform receives: ${primary.platform_payout_usd:.2f} (15%)")
    print(f"   Node pool receives: ${primary.node_operator_payout_usd:.2f} (10%)")
    
    # Step 2: Secondary market resale
    print("\n2️⃣ Alice resells Edition #5 on OpenSea for $150")
    secondary = royalty.process_secondary_sale(
        song_title="My Song",
        artist="Artist Name",
        content_hash="sha256_abc123",
        token_id=5,
        seller_wallet="0xAlice",
        buyer_wallet="0xBob",
        sale_price_usd=150.0,
        nft_contract_address="0x123456"
    )
    
    print(f"   Resale price: ${secondary.sale_price_usd:.2f}")
    print(f"   Artist receives: ${secondary.artist_payout_usd:.2f} (70%)")
    print(f"   Platform receives: ${secondary.platform_payout_usd:.2f} (10%)")
    print(f"   Node pool receives: ${secondary.node_operator_payout_usd:.2f} (20%)")
    
    # Step 3: Alice keeps the difference
    alice_profit = 150.0 - 50.0 - secondary.artist_payout_usd - secondary.platform_payout_usd
    print(f"\n   Alice's profit: ${alice_profit:.2f}")
    print(f"   (Resale $150 - Original cost $50 - Artist royalties $105 - Platform $15)")
    
    # Step 4: Compare primary vs secondary
    print("\n📊 COMPARISON: Primary vs Secondary")
    print("=" * 60)
    print("   ALICE (Seller)")
    print(f"     Primary sale: Received NFT for $50")
    print(f"     Secondary sale: Received $150 - $105 artist - $15 platform = ${alice_profit:.2f}")
    print()
    print("   ARTIST")
    print(f"     Primary sale: ${primary.artist_payout_usd:.2f}")
    print(f"     Secondary sale: ${secondary.artist_payout_usd:.2f}")
    print(f"     Total from this NFT: ${primary.artist_payout_usd + secondary.artist_payout_usd:.2f}")
    print()
    print("   KEY INSIGHT: Artist earns ongoing royalties from EVERY resale!")


# ============================================================================
# EXAMPLE 6: COMPREHENSIVE USER REPORT
# ============================================================================

async def example_user_report():
    """
    Generate comprehensive reward and earning report for user.
    """
    from dcmx.royalties import RoyaltyPaymentStructure
    
    royalty = RoyaltyPaymentStructure()
    
    print("\n📋 COMPREHENSIVE USER REPORT")
    print("=" * 60)
    
    # Simulate activity
    for i in range(10):
        royalty.record_sharing_event(
            sharer_wallet="0xAlice",
            song_content_hash="sha256_song1",
            shared_with_wallet=f"0xUser{i}",
            base_reward=1
        )
    
    for i in range(5):
        royalty.record_listening_event(
            listener_wallet="0xAlice",
            song_content_hash="sha256_song2",
            sharer_wallet="0xUser{i}",
            listen_duration_seconds=180,
            completion_percentage=80.0,
            base_reward=2
        )
    
    royalty.issue_nft_certificate(
        song_title="Song A",
        artist="Artist",
        content_hash="sha256_song1",
        edition_number=1,
        max_editions=100,
        buyer_wallet="0xAlice",
        purchase_price_usd=50.0,
        purchase_price_tokens=500,
        watermark_hash="wm_hash",
        perceptual_fingerprint="fp_hash",
        nft_contract_address="0x123",
        token_id=1
    )
    
    # Generate report
    report = royalty.generate_user_reward_report("0xAlice")
    
    print("\nUSER REWARD REPORT")
    print(f"Wallet: {report['wallet']}")
    print()
    print("SHARING REWARDS")
    print(f"  Events: {report['sharing_rewards']['events']}")
    print(f"  Total tokens: {report['sharing_rewards']['total_tokens']}")
    print()
    print("LISTENING REWARDS")
    print(f"  Events: {report['listening_rewards']['events']}")
    print(f"  Total tokens: {report['listening_rewards']['total_tokens']}")
    print()
    print("TOTALS")
    print(f"  Total earned: {report['total_earned']} tokens")
    print(f"  Claimed: {report['claimed_tokens']} tokens")
    print(f"  Pending claims: {report['pending_claims']}")
    print()
    print("CERTIFICATES")
    print(f"  NFT certificates owned: {report['nft_certificates']}")


# ============================================================================
# EXAMPLE 7: ARTIST ROYALTY REPORT
# ============================================================================

async def example_artist_report():
    """
    Generate comprehensive royalty report for artist.
    """
    from dcmx.royalties import RoyaltyPaymentStructure
    
    royalty = RoyaltyPaymentStructure()
    
    print("\n👨‍🎨 ARTIST ROYALTY REPORT")
    print("=" * 60)
    
    # Simulate multiple sales
    for i in range(10):
        royalty.process_primary_sale(
            song_title="My Song",
            artist="Artist Name",
            content_hash="sha256_song1",
            purchase_price_usd=50.0 + i * 5,
            purchase_price_tokens=500 + i * 50,
            nft_contract_address="0x123",
            token_id=i+1
        )
    
    for i in range(5):
        royalty.process_secondary_sale(
            song_title="My Song",
            artist="Artist Name",
            content_hash="sha256_song1",
            token_id=i+1,
            seller_wallet="0xSeller",
            buyer_wallet="0xBuyer",
            sale_price_usd=100.0 + i * 20,
            nft_contract_address="0x123"
        )
    
    # Generate report
    report = royalty.generate_royalty_report("Artist Name")
    
    print("\nARTIST: Artist Name")
    print(f"Total Royalties Earned: ${report['total_royalties_usd']:.2f}")
    print()
    print("PRIMARY SALES")
    print(f"  Count: {report['primary_sales']['count']}")
    print(f"  Total: ${report['primary_sales']['total_usd']:.2f}")
    print(f"  Average: ${report['primary_sales']['avg_payout']:.2f}")
    print()
    print("SECONDARY SALES (Resales)")
    print(f"  Count: {report['secondary_sales']['count']}")
    print(f"  Total: ${report['secondary_sales']['total_usd']:.2f}")
    print(f"  Average: ${report['secondary_sales']['avg_payout']:.2f}")
    print()
    print("OTHER")
    print(f"  NFTs issued: {report['nfts_issued']}")
    print()
    print("KEY INSIGHT: 70% of every sale (primary + secondary) goes to artist!")


# ============================================================================
# EXAMPLE 8: PLATFORM STATISTICS
# ============================================================================

async def example_platform_stats():
    """
    Show overall platform statistics and health metrics.
    """
    from dcmx.royalties import RoyaltyPaymentStructure
    
    royalty = RoyaltyPaymentStructure()
    
    print("\n📊 PLATFORM STATISTICS")
    print("=" * 60)
    
    # Generate platform stats
    stats = royalty.generate_platform_statistics()
    
    print(f"\nREVENUE & EARNINGS")
    print(f"  Total revenue: ${stats['total_revenue_usd']:,.2f}")
    print(f"  Platform earnings: ${stats['platform_earnings_usd']:,.2f}")
    print(f"  Node operator pool: ${stats['node_operator_pool_usd']:,.2f}")
    print(f"  Total distributed: ${stats['total_royalties_distributed_usd']:,.2f}")
    print()
    print(f"NFTS & CERTIFICATES")
    print(f"  Total issued: {stats['nfts_issued']}")
    print()
    print(f"REWARD CLAIMS")
    print(f"  Submitted: {stats['reward_claims_submitted']}")
    print(f"  Approved: {stats['reward_claims_approved']}")
    print(f"  Total tokens distributed: {stats['total_tokens_distributed']}")
    print()
    print(f"ENGAGEMENT")
    print(f"  Sharing events: {stats['sharing_events']}")
    print(f"  Listening events: {stats['listening_events']}")
    print(f"  Bandwidth rewards: {stats['bandwidth_rewards']}")


# ============================================================================
# RUN ALL EXAMPLES
# ============================================================================

async def run_all_examples():
    """Run all examples in sequence."""
    import asyncio
    
    print("\n" + "=" * 60)
    print("DCMX ROYALTY AND REWARDS SYSTEM - COMPLETE EXAMPLES")
    print("=" * 60)
    
    await example_complete_nft_purchase()
    await example_sharing_listening_rewards()
    await example_bandwidth_rewards()
    await example_reward_claim_verification()
    await example_secondary_market_resale()
    await example_user_report()
    await example_artist_report()
    await example_platform_stats()
    
    print("\n" + "=" * 60)
    print("✅ ALL EXAMPLES COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_all_examples())
