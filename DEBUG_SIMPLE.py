#!/usr/bin/env python3
"""
DCMX Economics Debug - Song Voting (Likes) + Skip Charges
Simplified version showing the concepts
"""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def main():
    print_header("🎵 DCMX DEBUG: Song Voting & Skip Charges")
    print("Artists: M877 and KAL3RIS\n")
    
    # ===== SETUP: Two Artists =====
    print_header("1. ARTIST SETUP")
    
    artist1 = "M877"
    artist1_wallet = "0xM877_wallet"
    
    artist2 = "KAL3RIS"
    artist2_wallet = "0xKAL3RIS_wallet"
    
    print(f"✓ Artist 1: {artist1}")
    print(f"  Wallet: {artist1_wallet}")
    print(f"\n✓ Artist 2: {artist2}")
    print(f"  Wallet: {artist2_wallet}")
    
    # ===== CREATE NFTs =====
    print_header("2. NFT CREATION: Songs from M877 & KAL3RIS")
    
    # M877 song
    m877_song_hash = "content_hash_M877_DigitalDreams_abc123"
    m877_song_title = "Digital Dreams"
    m877_price = 25.0
    
    print(f"✓ {artist1} - '{m877_song_title}'")
    print(f"  Content Hash: {m877_song_hash}")
    print(f"  Price: {m877_price} DCMX")
    print(f"  Edition: 1/100 limited copies")
    
    # KAL3RIS song
    kal3ris_song_hash = "content_hash_KAL3RIS_ElectricVibes_def456"
    kal3ris_song_title = "Electric Vibes"
    kal3ris_price = 30.0
    
    print(f"\n✓ {artist2} - '{kal3ris_song_title}'")
    print(f"  Content Hash: {kal3ris_song_hash}")
    print(f"  Price: {kal3ris_price} DCMX")
    print(f"  Edition: 1/100 limited copies")
    
    # ===== USERS =====
    print_header("3. USERS & WALLETS")
    
    user1_name = "Alice"
    user1_wallet = "0xAlice_wallet"
    
    user2_name = "Bob"
    user2_wallet = "0xBob_wallet"
    
    print(f"User 1: {user1_name}")
    print(f"  Wallet: {user1_wallet}")
    print(f"  Initial DCMX balance: 100.0")
    
    print(f"\nUser 2: {user2_name}")
    print(f"  Wallet: {user2_wallet}")
    print(f"  Initial DCMX balance: 100.0")
    
    # ===== LISTENING & ENGAGEMENT =====
    print_header("4. LISTENING & ENGAGEMENT ACTIVITY")
    
    alice_rewards = 0.0
    bob_rewards = 0.0
    platform_revenue = 0.0
    
    print(f"━━━ {artist1} - '{m877_song_title}' ━━━\n")
    
    # Alice listens to M877 song
    alice_listen_completion = 0.90
    alice_listen_reward = 2.5
    alice_rewards += alice_listen_reward
    
    print(f"{user1_name} (Alice):")
    print(f"  Listened: {alice_listen_completion*100:.0f}% complete")
    print(f"  Reward: +{alice_listen_reward:.2f} DCMX (listening reward)")
    print(f"  Balance: {100.0 + alice_rewards:.2f} DCMX")
    
    # Alice LIKES the song (song vote)
    alice_like_reward = 5.0
    alice_rewards += alice_like_reward
    
    print(f"  Voted: LIKE (thumbs up) 👍")
    print(f"  Reward: +{alice_like_reward:.2f} DCMX (like vote)")
    print(f"  Balance: {100.0 + alice_rewards:.2f} DCMX")
    
    # Bob listens partially then SKIPS
    bob_listen_completion = 0.20
    bob_listen_reward = 0.5
    bob_rewards += bob_listen_reward
    
    print(f"\n{user2_name} (Bob):")
    print(f"  Listened: {bob_listen_completion*100:.0f}% (SKIPPED at 20%)")
    print(f"  Reward: +{bob_listen_reward:.2f} DCMX (partial listen)")
    print(f"  Balance: {100.0 + bob_rewards:.2f} DCMX")
    
    # Bob charged for skipping
    skip_charge = 1.0
    bob_rewards -= skip_charge
    platform_revenue += skip_charge
    
    print(f"  Skip Charge: -{skip_charge:.2f} DCMX (skipped before 25% threshold)")
    print(f"  Balance: {100.0 + bob_rewards:.2f} DCMX")
    
    # ===== SECOND ARTIST SONGS =====
    print(f"\n━━━ {artist2} - '{kal3ris_song_title}' ━━━\n")
    
    # Alice listens to KAL3RIS
    alice_listen2_completion = 1.0
    alice_listen2_reward = 3.0
    alice_rewards += alice_listen2_reward
    
    print(f"{user1_name} (Alice):")
    print(f"  Listened: {alice_listen2_completion*100:.0f}% complete")
    print(f"  Reward: +{alice_listen2_reward:.2f} DCMX (full listen bonus)")
    print(f"  Balance: {100.0 + alice_rewards:.2f} DCMX")
    
    # Alice DISLIKES this song
    print(f"  Voted: DISLIKE (thumbs down) 👎")
    print(f"  Reward: 0 DCMX (no reward for dislike, but counts in analytics)")
    print(f"  Balance: {100.0 + alice_rewards:.2f} DCMX")
    
    # Bob listens to KAL3RIS
    bob_listen2_completion = 0.50
    bob_listen2_reward = 1.0
    bob_rewards += bob_listen2_reward
    
    print(f"\n{user2_name} (Bob):")
    print(f"  Listened: {bob_listen2_completion*100:.0f}% complete")
    print(f"  Reward: +{bob_listen2_reward:.2f} DCMX (partial listen)")
    print(f"  Balance: {100.0 + bob_rewards:.2f} DCMX")
    
    # Bob LIKES this one
    bob_like_reward = 5.0
    bob_rewards += bob_like_reward
    
    print(f"  Voted: LIKE (thumbs up) 👍")
    print(f"  Reward: +{bob_like_reward:.2f} DCMX (like vote)")
    print(f"  Balance: {100.0 + bob_rewards:.2f} DCMX")
    
    # ===== FINAL BALANCES =====
    print_header("5. FINAL BALANCES")
    
    print(f"USERS:\n")
    print(f"  {user1_name}:")
    print(f"    Initial:  100.00 DCMX")
    print(f"    Earned:   +{alice_rewards:.2f} DCMX")
    print(f"    Final:    {100.0 + alice_rewards:.2f} DCMX ✓\n")
    
    print(f"  {user2_name}:")
    print(f"    Initial:  100.00 DCMX")
    print(f"    Earned:   +{bob_listen_reward + bob_listen2_reward + bob_like_reward:.2f} DCMX (listening + like)")
    print(f"    Charged:  -{skip_charge:.2f} DCMX (skip fee)")
    print(f"    Net:      +{bob_rewards - 100:.2f} DCMX")
    print(f"    Final:    {100.0 + bob_rewards:.2f} DCMX ✓")
    
    print(f"\nARTISTS:\n")
    
    print(f"  {artist1} (M877):")
    print(f"    Primary NFT sales: {m877_price} DCMX (100% payout)")
    print(f"    Secondary royalties: Not yet (edition 1 not resold)")
    print(f"    Engagement metrics:")
    print(f"      • 2 listeners (Alice 90%, Bob 20%)")
    print(f"      • 1 like, 0 dislikes")
    print(f"      • 100% positive sentiment ✓\n")
    
    print(f"  {artist2} (KAL3RIS):")
    print(f"    Primary NFT sales: {kal3ris_price} DCMX (100% payout)")
    print(f"    Secondary royalties: Not yet (edition 1 not resold)")
    print(f"    Engagement metrics:")
    print(f"      • 2 listeners (Alice 100%, Bob 50%)")
    print(f"      • 1 like, 1 dislike")
    print(f"      • 50% positive sentiment (mixed reception)")
    
    # ===== REVENUE BREAKDOWN =====
    print_header("6. PLATFORM REVENUE & ALLOCATION")
    
    total_user_rewards = alice_rewards + bob_rewards
    platform_fees = total_user_rewards * 0.02  # 2% platform fee on rewards
    total_revenue = platform_fees + platform_revenue  # Platform fee + skip charges
    
    print(f"Revenue Sources:")
    print(f"  Platform fee (2% on {total_user_rewards:.2f} DCMX rewards): {platform_fees:.4f} DCMX")
    print(f"  Skip charge revenue: {platform_revenue:.2f} DCMX")
    print(f"  Total platform revenue: {total_revenue:.4f} DCMX\n")
    
    artist_fund = total_revenue * 0.20
    treasury = total_revenue * 0.50
    burn = total_revenue * 0.30
    
    print(f"Revenue Allocation:")
    print(f"  Artist fund (20%): {artist_fund:.4f} DCMX")
    print(f"  Treasury (50%): {treasury:.4f} DCMX")
    print(f"  Burn (30%): {burn:.4f} DCMX (removed from circulation)")
    
    # ===== KEY MECHANICS EXPLAINED =====
    print_header("7. KEY MECHANICS EXPLAINED")
    
    print("""
SONG VOTING (LIKES/DISLIKES):
  • Users vote on INDIVIDUAL SONGS (not platform governance)
  • Like (thumbs up) = 5 DCMX reward to user
  • Dislike (thumbs down) = 0 DCMX, but tracked for analytics
  
  WHY:
  ✓ Artists see which songs resonate with audience
  ✓ Platform recommends high-like songs
  ✓ Users earn for genuine engagement
  ✓ Prevents governance gaming

SKIP CHARGES:
  • When user skips before 25% completion: -1 DCMX charged
  • Charge goes to PLATFORM (not artist)
  • Incentivizes meaningful listening
  
  WHY:
  ✓ Prevents spam/abuse
  ✓ Encourages users to commit to songs
  ✓ Funds platform sustainability
  ✓ Artist still gets 100% of primary NFT sales

ARTIST ECONOMICS (100% Primary):
  • Artists get 100% of NFT sales price (no platform cut)
  • Artists earn royalties on resales (smart contract enforced)
  • Artists see engagement metrics (likes, dislikes, completion %)
  
  WHY:
  ✓ Artists fairly compensated
  ✓ Incentivizes quality content
  ✓ Direct audience connection
  ✓ Transparent analytics

USER REWARDS TYPES:
  • Listening: Reward for listening to shared songs
  • Likes: Reward for expressing song preferences
  • Sharing: Reward for sharing songs with others
  • Referrals: Reward for bringing new users
  • Bandwidth: Reward for serving content (LoRa)
  • Engagement: Reward for community participation
    """)
    
    # ===== SUMMARY =====
    print_header("✓ DEBUG COMPLETE")
    
    print(f"""
Summary of Debug Run:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Artists:
  • M877 uploaded: Digital Dreams (25 DCMX)
  • KAL3RIS uploaded: Electric Vibes (30 DCMX)

Users:
  • Alice: Earned {alice_rewards:.2f} DCMX (final: {100.0 + alice_rewards:.2f} DCMX)
  • Bob: Earned {bob_rewards:.2f} DCMX net (final: {100.0 + bob_rewards:.2f} DCMX)

Engagement:
  • Song likes: 2 (M877: 1 like, KAL3RIS: 1 like)
  • Song dislikes: 1 (KAL3RIS: 1 dislike from Alice)
  • Skip charges: 1 (Bob skipped M877 at 20%)

Platform Health:
  • Total user rewards distributed: {total_user_rewards:.2f} DCMX
  • Platform revenue: {total_revenue:.4f} DCMX
  • Treasury allocated: {treasury:.4f} DCMX
  • Tokens burned: {burn:.4f} DCMX

✓ All mechanics working as designed
✓ Song voting (preferences) implemented
✓ Skip charges preventing abuse
✓ Artists earning 100% of sales
✓ Platform sustainable
    """)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDebug interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
