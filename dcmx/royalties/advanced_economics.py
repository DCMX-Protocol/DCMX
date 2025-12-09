"""
Advanced Economics Features for DCMX Artist-First System.

Extends artist_first_economics.py with:
- Dynamic pricing and demand-based adjustments
- Tiered artist incentives (based on success)
- Seasonal and promotional rewards
- Artist analytics and insights
- User engagement scoring and badges
- Revenue sharing pools and collectives
- Streaming analytics integration
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class ArtistTier(Enum):
    """Artist tiers based on cumulative earnings and sales."""
    EMERGING = "emerging"  # 0-100 DCMX lifetime
    RISING = "rising"  # 100-1,000 DCMX lifetime
    ESTABLISHED = "established"  # 1,000-10,000 DCMX lifetime
    PLATINUM = "platinum"  # 10,000+ DCMX lifetime


class UserBadge(Enum):
    """User engagement badges."""
    EARLY_SUPPORTER = "early_supporter"  # Purchased first editions
    SUPER_SHARER = "super_sharer"  # Shared 50+ times
    DEVOTED_LISTENER = "devoted_listener"  # 90%+ average completion
    SONG_LOVER = "song_lover"  # Liked/voted thumbs up 10+ times
    BANDWIDTH_CHAMPION = "bandwidth_champion"  # Served 1TB+ data
    ACTIVE_MEMBER = "active_member"  # Active 7+ days/month


@dataclass
class DynamicPricingModel:
    """
    Adjust NFT prices based on demand and market conditions.
    
    Factors:
    - Demand (how many people want to buy)
    - Time (early editions more valuable)
    - Artist tier (established artists can charge more)
    - Market conditions (bullish/bearish)
    """
    song_content_hash: str
    current_price_dcmx: float
    base_price_dcmx: float
    
    # Demand metrics
    demand_score: float = 0.0  # 0-1, based on shares/listens/interest
    editions_sold: int = 0
    max_editions: int = 100
    
    # Time decay (early editions premium)
    days_since_release: int = 0
    time_premium_multiplier: float = 1.0  # 1.0 = normal, 1.5 = 50% premium
    
    # Artist tier bonus
    artist_tier: ArtistTier = ArtistTier.EMERGING
    tier_multiplier: float = 1.0  # 1.0 = emerging, 1.2 = rising, 1.5 = platinum
    
    # Market conditions
    market_sentiment: str = "neutral"  # bullish, neutral, bearish
    sentiment_multiplier: float = 1.0  # 1.2 = bullish, 1.0 = neutral, 0.8 = bearish
    
    # Surge pricing (scarcity)
    editions_remaining: int = 100
    scarcity_multiplier: float = 1.0  # Increases as fewer editions remain
    
    def __post_init__(self):
        """Recalculate dynamic price."""
        self.calculate_dynamic_price()
    
    def calculate_dynamic_price(self) -> float:
        """
        Calculate price based on all factors.
        
        Formula:
        Dynamic Price = Base Price × Tier × Time × Sentiment × Scarcity
        
        Examples:
        - New platinum artist with high demand: 100 × 1.5 × 1.3 × 1.2 × 1.4 = 327 DCMX
        - Established artist, low demand: 50 × 1.2 × 0.9 × 0.8 × 1.0 = 43 DCMX
        """
        self.current_price_dcmx = (
            self.base_price_dcmx 
            * self.tier_multiplier 
            * self.time_premium_multiplier 
            * self.sentiment_multiplier 
            * self.scarcity_multiplier
        )
        
        logger.info(
            f"Dynamic pricing: {self.song_content_hash[:16]}... "
            f"Base: {self.base_price_dcmx:.2f} → Current: {self.current_price_dcmx:.2f} DCMX"
        )
        
        return self.current_price_dcmx
    
    def update_demand(self, demand_score: float) -> None:
        """Update demand and recalculate if needed."""
        self.demand_score = min(demand_score, 1.0)
        # Higher demand = higher time premium
        self.time_premium_multiplier = 1.0 + (self.demand_score * 0.5)
        self.calculate_dynamic_price()
    
    def update_scarcity(self) -> None:
        """Recalculate scarcity multiplier based on remaining editions."""
        percentage_sold = 1.0 - (self.editions_remaining / self.max_editions)
        # Last 10% are 2x more expensive, last 1% is 5x
        if percentage_sold >= 0.99:
            self.scarcity_multiplier = 5.0
        elif percentage_sold >= 0.90:
            self.scarcity_multiplier = 2.0
        elif percentage_sold >= 0.75:
            self.scarcity_multiplier = 1.5
        elif percentage_sold >= 0.50:
            self.scarcity_multiplier = 1.2
        else:
            self.scarcity_multiplier = 1.0
        
        self.calculate_dynamic_price()


@dataclass
class ArtistTierBenefit:
    """Benefits unlocked at each artist tier."""
    tier: ArtistTier
    earnings_threshold: float
    
    # Financial benefits
    revenue_share_increase: float = 0.0  # Additional % on secondary sales
    royalty_boost: float = 1.0  # Multiplier on all earnings
    
    # Feature unlocks
    can_set_custom_price: bool = False
    can_create_bundles: bool = False
    can_run_promotions: bool = False
    can_pre_order: bool = False
    can_collaborate: bool = False
    
    # Support benefits
    priority_support: bool = False
    marketing_assistance: bool = False
    analytics_dashboard: bool = False
    
    @staticmethod
    def get_tier_benefits(tier: ArtistTier) -> "ArtistTierBenefit":
        """Get benefits for a specific tier."""
        benefits = {
            ArtistTier.EMERGING: ArtistTierBenefit(
                tier=ArtistTier.EMERGING,
                earnings_threshold=0.0,
                revenue_share_increase=0.0,
                royalty_boost=1.0,
            ),
            ArtistTier.RISING: ArtistTierBenefit(
                tier=ArtistTier.RISING,
                earnings_threshold=100.0,
                revenue_share_increase=5.0,  # +5% on secondary
                royalty_boost=1.05,
                can_set_custom_price=True,
                can_create_bundles=True,
                analytics_dashboard=True,
            ),
            ArtistTier.ESTABLISHED: ArtistTierBenefit(
                tier=ArtistTier.ESTABLISHED,
                earnings_threshold=1000.0,
                revenue_share_increase=10.0,  # +10% on secondary
                royalty_boost=1.1,
                can_set_custom_price=True,
                can_create_bundles=True,
                can_run_promotions=True,
                priority_support=True,
                marketing_assistance=True,
                analytics_dashboard=True,
            ),
            ArtistTier.PLATINUM: ArtistTierBenefit(
                tier=ArtistTier.PLATINUM,
                earnings_threshold=10000.0,
                revenue_share_increase=15.0,  # +15% on secondary
                royalty_boost=1.15,
                can_set_custom_price=True,
                can_create_bundles=True,
                can_run_promotions=True,
                can_pre_order=True,
                can_collaborate=True,
                priority_support=True,
                marketing_assistance=True,
                analytics_dashboard=True,
            ),
        }
        return benefits[tier]


@dataclass
class UserEngagementScore:
    """
    Gamified engagement scoring system.
    
    Users earn points for activities, which unlock badges and perks.
    """
    user_wallet: str
    total_points: float = 0.0
    
    # Activity tallies
    shares_count: int = 0
    listens_count: int = 0
    votes_count: int = 0
    nfts_owned: int = 0
    days_active: int = 0
    
    # Badges earned
    badges: List[UserBadge] = field(default_factory=list)
    
    # Status
    monthly_active: bool = True
    points_this_month: float = 0.0
    last_activity: Optional[str] = None
    
    def add_points(self, activity: str, points: float) -> None:
        """Add points for an activity."""
        self.total_points += points
        self.points_this_month += points
        self.last_activity = datetime.utcnow().isoformat()
        
        logger.debug(f"User {self.user_wallet[:20]}... earned {points} points for {activity}")
    
    def check_badge_eligibility(self) -> List[UserBadge]:
        """Check and award eligible badges."""
        new_badges = []
        
        if self.shares_count >= 50 and UserBadge.SUPER_SHARER not in self.badges:
            new_badges.append(UserBadge.SUPER_SHARER)
        
        if self.nfts_owned >= 1 and UserBadge.EARLY_SUPPORTER not in self.badges:
            new_badges.append(UserBadge.EARLY_SUPPORTER)
        
        if self.votes_count >= 10 and UserBadge.SONG_LOVER not in self.badges:
            new_badges.append(UserBadge.SONG_LOVER)
        
        if self.days_active >= 30 and UserBadge.ACTIVE_MEMBER not in self.badges:
            new_badges.append(UserBadge.ACTIVE_MEMBER)
        
        self.badges.extend(new_badges)
        
        if new_badges:
            logger.info(f"User {self.user_wallet[:20]}... earned badges: {[b.value for b in new_badges]}")
        
        return new_badges


@dataclass
class SeasonalPromotion:
    """
    Time-limited promotions to boost engagement and sales.
    
    Examples:
    - "New Year Boost": 2x rewards for shares in January
    - "Artist Spotlight": Featured artist gets 20% sales boost
    - "Listen-to-Earn": 3x listening rewards for specific songs
    """
    promotion_id: str
    name: str
    description: str
    promotion_type: str  # "global", "artist", "song", "user"
    
    # Timing
    start_date: str  # ISO timestamp
    end_date: str
    is_active: bool = True
    
    # Scope
    target_id: Optional[str] = None  # artist_name, song_hash, or user_wallet
    
    # Incentives
    reward_multiplier: float = 1.0  # 2.0 = 2x rewards
    discount_percentage: float = 0.0  # For purchase discounts
    bonus_tokens: float = 0.0  # Flat bonus tokens
    
    # Metrics
    users_participated: int = 0
    total_rewards_distributed: float = 0.0
    roi: float = 0.0  # Return on investment
    
    def is_promotion_active(self) -> bool:
        """Check if promotion is currently running."""
        now = datetime.utcnow().isoformat()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def calculate_boosted_reward(self, base_reward: float) -> float:
        """Calculate reward with promotion applied."""
        return (base_reward * self.reward_multiplier) + self.bonus_tokens
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)


@dataclass
class StreamingAnalytics:
    """
    Track listening patterns and generate insights.
    
    Used by artists to understand their audience and improve content.
    """
    song_content_hash: str
    song_title: str
    artist: str
    
    # Listening metrics
    total_listens: int = 0
    unique_listeners: int = 0
    avg_completion_percentage: float = 0.0
    
    # Time-based metrics
    listens_24h: int = 0
    listens_7d: int = 0
    listens_30d: int = 0
    
    # Engagement metrics
    skip_count: int = 0
    replay_count: int = 0
    completion_by_quartile: Dict[str, int] = field(default_factory=lambda: {
        "0-25%": 0,
        "25-50%": 0,
        "50-75%": 0,
        "75-100%": 0
    })
    
    # Geographic (if available)
    top_countries: Dict[str, int] = field(default_factory=dict)
    top_cities: Dict[str, int] = field(default_factory=dict)
    
    # Audience insights
    avg_listener_age_range: Optional[str] = None
    primary_gender: Optional[str] = None
    listener_retention_rate: float = 0.0  # % who listen to next song
    
    def update_completion_data(self, completion_percentage: float) -> None:
        """Update completion quartile based on listen."""
        if completion_percentage < 25:
            self.completion_by_quartile["0-25%"] += 1
        elif completion_percentage < 50:
            self.completion_by_quartile["25-50%"] += 1
        elif completion_percentage < 75:
            self.completion_by_quartile["50-75%"] += 1
        else:
            self.completion_by_quartile["75-100%"] += 1
        
        # Update average
        total_listens = sum(self.completion_by_quartile.values())
        if total_listens > 0:
            weighted_completion = (
                (self.completion_by_quartile["0-25%"] * 12.5) +
                (self.completion_by_quartile["25-50%"] * 37.5) +
                (self.completion_by_quartile["50-75%"] * 62.5) +
                (self.completion_by_quartile["75-100%"] * 87.5)
            ) / total_listens
            self.avg_completion_percentage = weighted_completion
    
    def get_insights(self) -> Dict:
        """Generate actionable insights for artist."""
        insights = {
            "engagement_level": "low" if self.avg_completion_percentage < 50 else
                               "medium" if self.avg_completion_percentage < 75 else "high",
            "listener_drop_off": max(0, self.completion_by_quartile["0-25%"] - self.completion_by_quartile["75-100%"]),
            "viral_potential": "high" if self.replay_count > self.total_listens * 0.2 else "medium" if self.replay_count > self.total_listens * 0.1 else "low",
            "recommendation": self._generate_recommendation(),
        }
        return insights
    
    def _generate_recommendation(self) -> str:
        """Generate recommendation based on data."""
        if self.avg_completion_percentage < 40:
            return "Consider shortening intro or improving hook in first 25%"
        elif self.replay_count < self.total_listens * 0.05:
            return "Strong initial interest but low replay. Try different versions or remixes."
        elif self.listener_retention_rate < 0.3:
            return "Listeners aren't coming back. Release more frequently to maintain momentum."
        else:
            return "Great engagement! Consider creating a follow-up or remix."


class AdvancedEconomicsEngine:
    """
    Advanced economics features for DCMX platform.
    
    Manages:
    - Dynamic pricing
    - Artist tiers and benefits
    - User engagement scoring
    - Seasonal promotions
    - Streaming analytics
    - Revenue pools and collectives
    """
    
    def __init__(self):
        """Initialize advanced economics engine."""
        self.dynamic_prices: Dict[str, DynamicPricingModel] = {}
        self.artist_tiers: Dict[str, ArtistTier] = {}
        self.user_engagement: Dict[str, UserEngagementScore] = {}
        self.promotions: Dict[str, SeasonalPromotion] = {}
        self.analytics: Dict[str, StreamingAnalytics] = {}
        
        logger.info("AdvancedEconomicsEngine initialized")
    
    # ==================== DYNAMIC PRICING ====================
    
    def create_dynamic_pricing(
        self,
        song_content_hash: str,
        base_price_dcmx: float,
        max_editions: int = 100
    ) -> DynamicPricingModel:
        """Create dynamic pricing model for a song."""
        pricing = DynamicPricingModel(
            song_content_hash=song_content_hash,
            current_price_dcmx=base_price_dcmx,
            base_price_dcmx=base_price_dcmx,
            max_editions=max_editions,
            editions_remaining=max_editions,
        )
        
        self.dynamic_prices[song_content_hash] = pricing
        logger.info(f"Dynamic pricing created for {song_content_hash[:16]}... at {base_price_dcmx:.2f} DCMX")
        
        return pricing
    
    def get_current_price(self, song_content_hash: str) -> float:
        """Get current dynamic price for a song."""
        if song_content_hash not in self.dynamic_prices:
            return None
        
        pricing = self.dynamic_prices[song_content_hash]
        pricing.update_scarcity()  # Recalculate based on current scarcity
        return pricing.current_price_dcmx
    
    def update_artist_tier(self, artist: str, lifetime_earnings: float) -> ArtistTier:
        """Update artist tier based on earnings."""
        if lifetime_earnings >= 10000:
            tier = ArtistTier.PLATINUM
        elif lifetime_earnings >= 1000:
            tier = ArtistTier.ESTABLISHED
        elif lifetime_earnings >= 100:
            tier = ArtistTier.RISING
        else:
            tier = ArtistTier.EMERGING
        
        self.artist_tiers[artist] = tier
        logger.info(f"Artist {artist} promoted to {tier.value} (${lifetime_earnings:.2f} lifetime)")
        
        return tier
    
    # ==================== USER ENGAGEMENT ====================
    
    def get_or_create_user_score(self, user_wallet: str) -> UserEngagementScore:
        """Get or create engagement score for user."""
        if user_wallet not in self.user_engagement:
            self.user_engagement[user_wallet] = UserEngagementScore(user_wallet=user_wallet)
        
        return self.user_engagement[user_wallet]
    
    def record_user_activity(
        self,
        user_wallet: str,
        activity_type: str,
        reward_tokens: float
    ) -> UserEngagementScore:
        """Record user activity and update engagement score."""
        score = self.get_or_create_user_score(user_wallet)
        
        # Update tallies
        if activity_type == "share":
            score.shares_count += 1
            score.add_points("share", 5)
        elif activity_type == "listen":
            score.listens_count += 1
            score.add_points("listen", 10)
        elif activity_type == "vote":
            score.votes_count += 1
            score.add_points("vote", 15)
        elif activity_type == "nft_purchase":
            score.nfts_owned += 1
            score.add_points("nft_purchase", 50)
        
        # Check for new badges
        new_badges = score.check_badge_eligibility()
        
        return score
    
    # ==================== PROMOTIONS ====================
    
    def create_promotion(
        self,
        name: str,
        description: str,
        duration_days: int,
        promotion_type: str,
        reward_multiplier: float = 1.0,
        discount_percentage: float = 0.0,
        target_id: Optional[str] = None
    ) -> SeasonalPromotion:
        """Create a new seasonal promotion."""
        promotion_id = f"promo_{name.replace(' ', '_')}_{datetime.utcnow().timestamp()}"
        
        now = datetime.utcnow()
        start_date = now.isoformat()
        end_date = (now + timedelta(days=duration_days)).isoformat()
        
        promotion = SeasonalPromotion(
            promotion_id=promotion_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            promotion_type=promotion_type,
            target_id=target_id,
            reward_multiplier=reward_multiplier,
            discount_percentage=discount_percentage,
        )
        
        self.promotions[promotion_id] = promotion
        logger.info(f"Promotion created: {name} ({duration_days} days, {reward_multiplier}x rewards)")
        
        return promotion
    
    def get_active_promotions(self) -> List[SeasonalPromotion]:
        """Get all currently active promotions."""
        return [p for p in self.promotions.values() if p.is_promotion_active()]
    
    # ==================== STREAMING ANALYTICS ====================
    
    def create_analytics(
        self,
        song_content_hash: str,
        song_title: str,
        artist: str
    ) -> StreamingAnalytics:
        """Create analytics tracking for a song."""
        analytics = StreamingAnalytics(
            song_content_hash=song_content_hash,
            song_title=song_title,
            artist=artist,
        )
        
        self.analytics[song_content_hash] = analytics
        return analytics
    
    def record_listen(
        self,
        song_content_hash: str,
        completion_percentage: float,
        user_wallet: str
    ) -> StreamingAnalytics:
        """Record a listen event and update analytics."""
        if song_content_hash not in self.analytics:
            return None
        
        analytics = self.analytics[song_content_hash]
        analytics.total_listens += 1
        analytics.listens_24h += 1
        analytics.listens_7d += 1
        analytics.listens_30d += 1
        analytics.update_completion_data(completion_percentage)
        
        return analytics
    
    def get_analytics_report(self, song_content_hash: str) -> Dict:
        """Get full analytics report for a song."""
        if song_content_hash not in self.analytics:
            return None
        
        analytics = self.analytics[song_content_hash]
        
        return {
            "song": analytics.song_title,
            "artist": analytics.artist,
            "total_listens": analytics.total_listens,
            "unique_listeners": analytics.unique_listeners,
            "avg_completion": f"{analytics.avg_completion_percentage:.1f}%",
            "metrics_24h": analytics.listens_24h,
            "metrics_7d": analytics.listens_7d,
            "metrics_30d": analytics.listens_30d,
            "completion_breakdown": analytics.completion_by_quartile,
            "insights": analytics.get_insights(),
        }


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    import json
    
    engine = AdvancedEconomicsEngine()
    
    # Example 1: Dynamic pricing
    print("\n=== DYNAMIC PRICING ===")
    pricing = engine.create_dynamic_pricing("song_hash_123", 10.0, max_editions=100)
    print(f"Base price: {pricing.base_price_dcmx:.2f} DCMX")
    print(f"Current price: {pricing.current_price_dcmx:.2f} DCMX")
    
    # Simulate demand
    pricing.update_demand(0.8)
    print(f"After high demand: {pricing.current_price_dcmx:.2f} DCMX")
    
    # Simulate scarcity (50 editions left)
    pricing.editions_remaining = 50
    current = engine.get_current_price("song_hash_123")
    print(f"After 50% sold: {current:.2f} DCMX")
    
    # Example 2: Artist tier benefits
    print("\n=== ARTIST TIERS ===")
    tier = engine.update_artist_tier("Artist Bob", 5000)
    benefits = ArtistTierBenefit.get_tier_benefits(tier)
    print(f"Tier: {tier.value}")
    print(f"Revenue share increase: +{benefits.revenue_share_increase}%")
    print(f"Can run promotions: {benefits.can_run_promotions}")
    
    # Example 3: User engagement
    print("\n=== USER ENGAGEMENT ===")
    score = engine.get_or_create_user_score("0xUser123")
    engine.record_user_activity("0xUser123", "share", 5)
    engine.record_user_activity("0xUser123", "listen", 10)
    engine.record_user_activity("0xUser123", "nft_purchase", 50)
    
    print(f"User total points: {score.total_points}")
    print(f"Badges: {[b.value for b in score.badges]}")
    
    # Example 4: Promotions
    print("\n=== PROMOTIONS ===")
    promo = engine.create_promotion(
        name="New Year Boost",
        description="2x rewards for all activities in January",
        duration_days=31,
        promotion_type="global",
        reward_multiplier=2.0
    )
    
    base_reward = 10.0
    boosted = promo.calculate_boosted_reward(base_reward)
    print(f"Base reward: {base_reward} → Boosted: {boosted} tokens")
    
    # Example 5: Streaming analytics
    print("\n=== STREAMING ANALYTICS ===")
    analytics = engine.create_analytics("song_hash_123", "Midnight Rain", "Artist Bob")
    engine.record_listen("song_hash_123", 95.0, "0xUser123")
    engine.record_listen("song_hash_123", 45.0, "0xUser456")
    
    report = engine.get_analytics_report("song_hash_123")
    print(json.dumps(report, indent=2))
