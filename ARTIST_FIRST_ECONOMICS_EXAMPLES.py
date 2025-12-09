"""
Working Examples: Artist-First Economics with Wallet Conversion System

Demonstrates all features of the artist-first economics implementation.
"""

import sys
sys.path.insert(0, '/workspaces/DCMX')

from dcmx.royalties.artist_first_economics import (
    ArtistFirstEconomics,
    UserActivityType,
    FairRewardSchedule
)
import json
from datetime import datetime


def example_1_wallet_registration_and_conversion():
    """
    Example 1: User registers wallet and converts external currency to DCMX.
    
    Scenario: Alice wants to buy NFTs, but she has USDC stablecoins.
    She converts USDC → DCMX via the platform's bridge.
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Wallet Registration & Currency Conversion")
    print("="*70)
    
    economics = ArtistFirstEconomics()
    
    # Step 1: Register wallet
    print("\n[STEP 1] Alice registers her MetaMask wallet...")
    wallet_info = economics.register_user_wallet(
        user_id="alice_user_001",
        wallet_address="0xAlice1234567890abcdefghijklmnop",
        wallet_type="metamask"
    )
    print(f"✓ Wallet registered: {wallet_info['wallet_address'][:30]}...")
    print(f"  Type: {wallet_info['wallet_type']}")
    print(f"  Initial DCMX balance: {wallet_info['dcmx_balance']:.2f}")
    
    # Step 2: Convert USDC to DCMX
    print("\n[STEP 2] Alice converts 100 USDC to DCMX...")
    conversion = economics.convert_to_dcmx(
        user_id="alice_user_001",
        source_currency="USDC",
        source_amount=100.0,
        exchange_rate=1.0,  # 1 USDC = 1 DCMX (stablecoin)
        source_chain="polygon"
    )
    
    print(f"✓ Conversion completed:")
    print(f"  Source: 100.00 USDC")
    print(f"  Exchange rate: 1.0 USDC = 1.0 DCMX")
    print(f"  Bridge fee: {conversion.actual_conversion_fee:.2f} DCMX ({conversion.conversion_fee_percentage}%)")
    print(f"  Received: {conversion.dcmx_tokens_received:.2f} DCMX")
    print(f"  TX hash: {conversion.transaction_hash[:40]}...")
    
    # Check balance
    balance = economics.get_user_dcmx_balance("alice_user_001")
    print(f"\n✓ Alice's DCMX balance: {balance:.2f} DCMX")
    
    return economics


def example_2_nft_purchase_artist_100_percent(economics: ArtistFirstEconomics):
    """
    Example 2: Alice purchases an NFT.
    Artist Bob receives 100% of the purchase price (no fees).
    
    Scenario: Alice buys Edition 1 of "Midnight Rain" by Bob for 10 DCMX.
    Bob receives 10 DCMX immediately (100% - no platform fees).
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: NFT Purchase - Artist Gets 100%")
    print("="*70)
    
    # Register artist Bob
    economics.register_user_wallet(
        user_id="bob_artist_001",
        wallet_address="0xBob9876543210fedcba9876543210fed",
        wallet_type="metamask"
    )
    
    print("\n[PURCHASE] Alice buys Edition 1 of 'Midnight Rain' by Bob")
    print("Purchase Price: 10 DCMX")
    
    payment = economics.process_nft_purchase(
        user_id="alice_user_001",
        song_title="Midnight Rain",
        artist="Bob",
        artist_wallet="0xBob9876543210fedcba9876543210fed",
        content_hash="sha256_midnight_rain_12345",
        edition_number=1,
        max_editions=100,
        price_dcmx=10.0,
        price_usd_equivalent=10.0,
        watermark_hash="watermark_qwerty_123",
        perceptual_fingerprint="fingerprint_asdf_456",
        nft_contract_address="0xNFTContract_abc123",
        token_id=1
    )
    
    print("\n✓ Payment Summary:")
    summary = payment.get_summary()
    for key, value in summary.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print(f"\n✓ Artist Payout Breakdown:")
    print(f"  Purchase price: {payment.purchase_price_dcmx:.2f} DCMX")
    print(f"  Artist receives: {payment.artist_payout_dcmx:.2f} DCMX (100%)")
    print(f"  Platform fee: 0.00 DCMX (0%)")
    print(f"  Payout status: {payment.artist_payout_status}")
    
    # Show updated balances
    alice_balance = economics.get_user_dcmx_balance("alice_user_001")
    bob_earnings = economics.get_artist_total_earnings("Bob")
    
    print(f"\n✓ Updated Balances:")
    print(f"  Alice DCMX: {alice_balance:.2f} DCMX (spent {payment.purchase_price_dcmx:.2f})")
    print(f"  Bob total earnings: {bob_earnings:.2f} DCMX")
    
    return payment


def example_3_sharing_activity_reward(economics: ArtistFirstEconomics):
    """
    Example 3: Alice shares "Midnight Rain" with her friends.
    She earns tokens for promoting the song.
    
    Scenario: Alice shares the NFT link with 3 friends.
    She earns 0.5 tokens per share = 1.5 tokens total.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Sharing Activity & Rewards")
    print("="*70)
    
    # Register Alice's friends
    friend_wallets = {
        "charlie": "0xCharlie1111111111111111111111111",
        "diana": "0xDiana2222222222222222222222222222",
        "evan": "0xEvan3333333333333333333333333333"
    }
    
    for friend_id, wallet in friend_wallets.items():
        economics.register_user_wallet(friend_id, wallet)
    
    print("\n[ACTIVITY] Alice shares 'Midnight Rain' with 3 friends")
    print("Friends: Charlie, Diana, Evan")
    
    reward = economics.record_sharing_activity(
        user_wallet="0xAlice1234567890abcdefghijklmnop",
        song_content_hash="sha256_midnight_rain_12345",
        shared_with_wallet="0xCharlie1111111111111111111111111",
        activity_count=3
    )
    
    print(f"\n✓ Sharing Reward Details:")
    print(f"  Activity: Shared 'Midnight Rain' 3 times")
    print(f"  Base reward: {FairRewardSchedule.SHARING_BASE_REWARD} tokens × 3 = {reward.base_reward_tokens:.2f} tokens")
    print(f"  Engagement bonus: {reward.engagement_bonus:.2f} tokens")
    print(f"  Total earned: {reward.total_tokens:.2f} tokens")
    print(f"  Reward ID: {reward.reward_id}")
    
    print(f"\n💡 Potential bonuses if friends engage:")
    print(f"   - If 1 friend listens: +{FairRewardSchedule.SHARING_LISTENING_BONUS:.1f} token")
    print(f"   - If 1 friend buys NFT: +{FairRewardSchedule.SHARING_PURCHASE_BONUS:.1f} tokens")
    print(f"   - If 1 friend votes: +{FairRewardSchedule.SHARING_VOTE_BONUS:.1f} token")
    
    return reward


def example_4_listening_activity_reward(economics: ArtistFirstEconomics):
    """
    Example 4: Charlie listens to "Midnight Rain" (shared by Alice).
    He earns tokens based on how much of the song he listens to.
    
    Scenarios:
    - Listen 50%: 1.25 tokens
    - Listen 75%: 1.5 tokens
    - Listen 90%: 2.0 tokens
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Listening Activity & Completion Bonuses")
    print("="*70)
    
    print("\n[SCENARIO A] Charlie listens to 50% of song")
    reward_50 = economics.record_listening_activity(
        user_wallet="0xCharlie1111111111111111111111111",
        song_content_hash="sha256_midnight_rain_12345",
        listen_duration_seconds=120,  # 2 minutes of 4-minute song
        completion_percentage=50.0
    )
    print(f"✓ Completion: 50%")
    print(f"  Base reward: {FairRewardSchedule.LISTENING_BASE_REWARD:.1f} token")
    print(f"  Completion bonus (50-74%): {FairRewardSchedule.LISTENING_COMPLETION_50_74:.2f} tokens")
    print(f"  Total: {reward_50.total_tokens:.2f} tokens")
    
    print("\n[SCENARIO B] Diana listens to 75% of song")
    reward_75 = economics.record_listening_activity(
        user_wallet="0xDiana2222222222222222222222222222",
        song_content_hash="sha256_midnight_rain_12345",
        listen_duration_seconds=180,
        completion_percentage=75.0
    )
    print(f"✓ Completion: 75%")
    print(f"  Base reward: {FairRewardSchedule.LISTENING_BASE_REWARD:.1f} token")
    print(f"  Completion bonus (75-89%): {FairRewardSchedule.LISTENING_COMPLETION_75_89:.2f} tokens")
    print(f"  Total: {reward_75.total_tokens:.2f} tokens")
    
    print("\n[SCENARIO C] Evan listens to 95% of song")
    reward_95 = economics.record_listening_activity(
        user_wallet="0xEvan3333333333333333333333333333",
        song_content_hash="sha256_midnight_rain_12345",
        listen_duration_seconds=228,  # Almost full song
        completion_percentage=95.0
    )
    print(f"✓ Completion: 95%")
    print(f"  Base reward: {FairRewardSchedule.LISTENING_BASE_REWARD:.1f} token")
    print(f"  Completion bonus (90-100%): {FairRewardSchedule.LISTENING_COMPLETION_90_100:.2f} tokens")
    print(f"  Total: {reward_95.total_tokens:.2f} tokens")
    
    print("\n💡 Incentive: Higher completion = higher reward")
    print(f"   Encourages artists to make engaging songs")


def example_5_voting_activity_reward(economics: ArtistFirstEconomics):
    """
    Example 5: Users vote on platform governance proposals.
    
    Proposals might be:
    - Double listening rewards?
    - Add new NFT features?
    - Increase artist payouts?
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Governance Voting & Rewards")
    print("="*70)
    
    print("\n[PROPOSAL] 'Increase artist royalties on secondary sales to 90%'")
    print("Users vote on whether to approve this proposal...")
    
    print("\n[VOTE 1] Alice votes YES (matches community - 70% vote YES)")
    vote_1 = economics.record_voting_activity(
        user_wallet="0xAlice1234567890abcdefghijklmnop",
        governance_proposal_id="gov_proposal_001_artist_royalties",
        vote_matches_community=True
    )
    print(f"✓ Vote reward:")
    print(f"  Base: {FairRewardSchedule.VOTING_BASE_REWARD:.1f} token")
    print(f"  Community match bonus: +{FairRewardSchedule.VOTING_COMMUNITY_DECISION:.1f} token")
    print(f"  Total: {vote_1.total_tokens:.2f} tokens")
    
    print("\n[VOTE 2] Bob votes YES (matches community)")
    vote_2 = economics.record_voting_activity(
        user_wallet="0xBob9876543210fedcba9876543210fed",
        governance_proposal_id="gov_proposal_001_artist_royalties",
        vote_matches_community=True
    )
    print(f"✓ Vote reward: {vote_2.total_tokens:.2f} tokens")
    
    print("\n[VOTE 3] Charlie votes NO (against community - 30% vote NO)")
    vote_3 = economics.record_voting_activity(
        user_wallet="0xCharlie1111111111111111111111111",
        governance_proposal_id="gov_proposal_001_artist_royalties",
        vote_matches_community=False  # Voted against majority
    )
    print(f"✓ Vote reward:")
    print(f"  Base: {FairRewardSchedule.VOTING_BASE_REWARD:.1f} token (no bonus for minority vote)")
    print(f"  Total: {vote_3.total_tokens:.2f} tokens")
    
    print("\n⚠️  Important: Voting is ADVISORY, not binding")
    print("   Platform team makes final decision. This prevents vote-buying.")


def example_6_bandwidth_contribution_reward(economics: ArtistFirstEconomics):
    """
    Example 6: LoRa node provides bandwidth, earning token rewards.
    
    Scenario: Bob's LoRa node serves "Midnight Rain" to multiple users.
    He earns rewards based on data served and users reached.
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Bandwidth Contribution & Rewards")
    print("="*70)
    
    print("\n[SERVICE] Bob's LoRa node serves 'Midnight Rain' to network")
    print("Data served: 450 MB")
    print("Unique listeners reached: 5")
    
    reward = economics.record_bandwidth_contribution(
        node_id="lora_node_bob_san_francisco",
        song_content_hash="sha256_midnight_rain_12345",
        bytes_served=450 * 1024 * 1024,  # 450 MB
        listeners_served=5
    )
    
    print(f"\n✓ Bandwidth Reward Breakdown:")
    print(f"  Base reward: {FairRewardSchedule.BANDWIDTH_BASE_REWARD:.1f} tokens")
    
    bandwidth_bonus = (450 / 100) * FairRewardSchedule.BANDWIDTH_PER_100MB
    print(f"  Per 100MB (450MB ÷ 100 = 4.5): {bandwidth_bonus:.2f} tokens")
    
    listener_bonus = 5 * FairRewardSchedule.BANDWIDTH_PER_LISTENER
    print(f"  Per unique listener (5 listeners): {listener_bonus:.2f} tokens")
    
    print(f"  TOTAL EARNED: {reward.total_tokens:.2f} tokens")
    
    print("\n💡 Incentive: Larger nodes reach more users = higher rewards")
    print("   Encourages infrastructure investment in network coverage")


def example_7_secondary_sale_artist_majority(economics: ArtistFirstEconomics):
    """
    Example 7: NFT resale on secondary market.
    
    Alice bought Edition 1 for 10 DCMX.
    Edition 1 appreciates to 20 DCMX.
    Alice sells to Diana, who resells to Charlie.
    
    Artist maintains 80% of each resale (ongoing royalties).
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Secondary Market Sales & Artist Royalties")
    print("="*70)
    
    print("\nTimeline:")
    print("Day 1: Alice buys Edition 1 for 10 DCMX")
    print("       → Artist Bob gets 10 DCMX (100%)")
    
    primary_earnings = 10.0
    bob_lifetime = primary_earnings
    
    print("\nDay 7: Alice sells to Diana for 15 DCMX (15% appreciation)")
    resale_1 = economics.process_secondary_sale(
        seller_wallet="0xAlice1234567890abcdefghijklmnop",
        buyer_wallet="0xDiana2222222222222222222222222222",
        song_content_hash="sha256_midnight_rain_12345",
        edition_number=1,
        artist="Bob",
        artist_wallet="0xBob9876543210fedcba9876543210fed",
        resale_price_dcmx=15.0
    )
    
    print(f"\n✓ Resale 1 Breakdown (15 DCMX):")
    print(f"  Artist (80%):  {resale_1['artist_payout']:>6.2f} DCMX ← Bob receives")
    print(f"  Seller (15%):  {resale_1['seller_payout']:>6.2f} DCMX ← Alice receives")
    print(f"  Platform (5%): {resale_1['platform_payout']:>6.2f} DCMX")
    
    bob_lifetime += resale_1['artist_payout']
    
    print("\nDay 14: Diana sells to Charlie for 20 DCMX (33% appreciation from Day 7)")
    resale_2 = economics.process_secondary_sale(
        seller_wallet="0xDiana2222222222222222222222222222",
        buyer_wallet="0xCharlie1111111111111111111111111",
        song_content_hash="sha256_midnight_rain_12345",
        edition_number=1,
        artist="Bob",
        artist_wallet="0xBob9876543210fedcba9876543210fed",
        resale_price_dcmx=20.0
    )
    
    print(f"\n✓ Resale 2 Breakdown (20 DCMX):")
    print(f"  Artist (80%):  {resale_2['artist_payout']:>6.2f} DCMX ← Bob receives")
    print(f"  Seller (15%):  {resale_2['seller_payout']:>6.2f} DCMX ← Diana receives")
    print(f"  Platform (5%): {resale_2['platform_payout']:>6.2f} DCMX")
    
    bob_lifetime += resale_2['artist_payout']
    
    print("\n" + "-" * 70)
    print("LIFETIME EARNINGS FOR ARTIST BOB:")
    print("-" * 70)
    print(f"  Primary sale (Edition 1):   10.00 DCMX")
    print(f"  Resale 1 (Alice→Diana):    +{resale_1['artist_payout']:>5.2f} DCMX")
    print(f"  Resale 2 (Diana→Charlie):  +{resale_2['artist_payout']:>5.2f} DCMX")
    print(f"  {'─' * 40}")
    print(f"  TOTAL:                     {bob_lifetime:>6.2f} DCMX")
    print(f"\nBob earned {bob_lifetime - primary_earnings:.2f} DCMX extra from appreciation!")


def example_8_user_activity_report(economics: ArtistFirstEconomics):
    """
    Example 8: Generate activity and earnings report for a user.
    
    Shows all activities and total rewards earned.
    """
    print("\n" + "="*70)
    print("EXAMPLE 8: User Activity Report")
    print("="*70)
    
    # Alice has done:
    # - 1 NFT purchase (spent 10 DCMX)
    # - Shared song (earned 1.5 tokens)
    # - Listened partially (earned 2.0 tokens from voting)
    # - Voted (earned 0.6 tokens)
    
    user_report = economics.generate_user_activity_report("alice_user_001")
    
    print(f"\nUser: {user_report['user_wallet']}")
    print(f"Registration: {user_report['registration_date']}")
    
    print(f"\n💰 DCMX Balance: {user_report['dcmx_balance']:.2f} DCMX")
    
    print(f"\n📊 Conversion History:")
    print(f"  - Conversions made: {user_report['conversions_made']}")
    
    print(f"\n🎵 NFT History:")
    print(f"  - NFTs purchased: {user_report['nfts_purchased']}")
    
    print(f"\n🏆 Rewards Earned:")
    rewards = user_report['rewards_earned']
    print(f"  Total activities: {rewards['total_activities']}")
    print(f"  Total tokens: {rewards['total_tokens_earned']:.2f}")
    
    print(f"\n📈 Breakdown by Activity:")
    for activity_type, data in rewards['breakdown_by_type'].items():
        if data['count'] > 0:
            print(f"  - {activity_type.replace('_', ' ').title()}: "
                  f"{data['count']} activities, {data['total_tokens']:.2f} tokens")


def example_9_platform_statistics(economics: ArtistFirstEconomics):
    """
    Example 9: Generate overall platform statistics.
    
    Shows total conversions, sales, rewards distributed, etc.
    """
    print("\n" + "="*70)
    print("EXAMPLE 9: Platform Statistics")
    print("="*70)
    
    stats = economics.generate_platform_statistics()
    
    print(f"\n💱 CONVERSION METRICS:")
    print(f"  Total conversions: {stats['total_conversions']}")
    print(f"  Total DCMX volume: {stats['total_conversion_volume_dcmx']:.2f} DCMX")
    
    print(f"\n🎵 NFT SALES METRICS:")
    print(f"  Total NFT sales: {stats['total_nft_sales']}")
    print(f"  Total artist payouts: {stats['total_artist_payouts']:.2f} DCMX")
    
    print(f"\n🏆 REWARD METRICS:")
    print(f"  Total rewards distributed: {stats['total_user_rewards']:.2f} tokens")
    
    print(f"\n👥 NETWORK METRICS:")
    print(f"  Registered wallets: {stats['registered_wallets']}")
    
    print(f"\n📊 ACTIVITY BREAKDOWN:")
    for activity_type, count in stats['total_activity_rewards'].items():
        if count > 0:
            print(f"  - {activity_type.replace('_', ' ').title()}: {count}")


def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "="*70)
    print("DCMX ARTIST-FIRST ECONOMICS - COMPREHENSIVE EXAMPLES")
    print("="*70)
    print("\nDemonstrating:")
    print("✓ Wallet registration & currency conversion")
    print("✓ NFT purchase (100% to artist)")
    print("✓ User activity rewards (sharing, listening, voting, bandwidth)")
    print("✓ Secondary market sales with artist royalties")
    print("✓ Reporting and analytics")
    
    # Run examples
    economics = example_1_wallet_registration_and_conversion()
    example_2_nft_purchase_artist_100_percent(economics)
    example_3_sharing_activity_reward(economics)
    example_4_listening_activity_reward(economics)
    example_5_voting_activity_reward(economics)
    example_6_bandwidth_contribution_reward(economics)
    example_7_secondary_sale_artist_majority(economics)
    example_8_user_activity_report(economics)
    example_9_platform_statistics(economics)
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED ✓")
    print("="*70)
    print("\nKey Takeaways:")
    print("1️⃣  Artist gets 100% on primary NFT sales")
    print("2️⃣  Users earn fair rewards for promotion and engagement")
    print("3️⃣  Artist maintains 80% on secondary resales")
    print("4️⃣  Wallet conversion is seamless for non-crypto users")
    print("5️⃣  Rewards incentivize quality (completion bonuses) and growth")


if __name__ == "__main__":
    run_all_examples()
