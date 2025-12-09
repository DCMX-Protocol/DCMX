"""
DCMX Artist Analytics Dashboard

Real-time analytics for artists showing:
- Earnings (primary & secondary)
- Song engagement (likes, dislikes, completion %)
- Listener demographics
- Revenue breakdown
- Performance trends
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class EngagementType(Enum):
    """Types of song engagement."""
    LISTEN = "listen"
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    SHARE = "share"


@dataclass
class ListenerDemographic:
    """Listener demographic information."""
    listener_id: str
    username: str
    total_listens: int = 0
    average_completion: float = 0.0
    likes_given: int = 0
    dislikes_given: int = 0
    total_spent_dcmx: float = 0.0
    first_listen_date: str = ""
    last_listen_date: str = ""
    favorite_artist: Optional[str] = None


@dataclass
class SongAnalytics:
    """Analytics for a single song."""
    song_id: str
    title: str
    artist_wallet: str
    created_date: str
    
    # Engagement metrics
    total_listens: int = 0
    total_likes: int = 0
    total_dislikes: int = 0
    total_skips: int = 0
    total_shares: int = 0
    
    # Listening patterns
    average_completion_percentage: float = 0.0
    median_completion_percentage: float = 0.0
    completion_distribution: Dict[str, int] = field(default_factory=dict)  # "0-25%": count
    
    # Revenue
    sales_count: int = 0
    primary_revenue_dcmx: float = 0.0
    secondary_royalties_dcmx: float = 0.0
    
    # Derived metrics
    like_dislike_ratio: float = 0.0
    sentiment_percentage: float = 0.0  # % of likes vs total engagement
    completion_rate: float = 0.0  # % that complete 90%+
    
    def calculate_sentiment(self):
        """Calculate sentiment percentage."""
        total_votes = self.total_likes + self.total_dislikes
        if total_votes == 0:
            self.sentiment_percentage = 0.0
        else:
            self.sentiment_percentage = (self.total_likes / total_votes) * 100
    
    def calculate_like_ratio(self):
        """Calculate like-to-dislike ratio."""
        if self.total_dislikes == 0:
            self.like_dislike_ratio = float('inf') if self.total_likes > 0 else 0.0
        else:
            self.like_dislike_ratio = self.total_likes / self.total_dislikes


@dataclass
class ArtistAnalytics:
    """Comprehensive analytics for an artist."""
    artist_wallet: str
    artist_name: str
    join_date: str
    
    # Song metrics
    total_songs: int = 0
    total_listens: int = 0
    total_likes: int = 0
    total_dislikes: int = 0
    
    # Revenue metrics
    total_primary_sales_dcmx: float = 0.0
    total_secondary_royalties_dcmx: float = 0.0
    total_earnings_dcmx: float = 0.0
    current_balance_dcmx: float = 0.0
    
    # Listener metrics
    unique_listeners: int = 0
    repeat_listeners: int = 0
    listener_demographics: Dict[str, ListenerDemographic] = field(default_factory=dict)
    
    # Time-based metrics
    earnings_by_day: Dict[str, float] = field(default_factory=dict)
    listens_by_hour: Dict[str, int] = field(default_factory=dict)
    
    # Songs
    songs: Dict[str, SongAnalytics] = field(default_factory=dict)
    
    # Top performers
    top_song_by_likes: Optional[str] = None
    top_song_by_listens: Optional[str] = None
    top_song_by_revenue: Optional[str] = None
    
    def update_totals(self):
        """Recalculate totals from individual songs."""
        self.total_songs = len(self.songs)
        self.total_listens = sum(s.total_listens for s in self.songs.values())
        self.total_likes = sum(s.total_likes for s in self.songs.values())
        self.total_dislikes = sum(s.total_dislikes for s in self.songs.values())
        self.total_primary_sales_dcmx = sum(s.primary_revenue_dcmx for s in self.songs.values())
        self.total_secondary_royalties_dcmx = sum(s.secondary_royalties_dcmx for s in self.songs.values())
        self.total_earnings_dcmx = self.total_primary_sales_dcmx + self.total_secondary_royalties_dcmx
        
        # Find top performers
        if self.songs:
            self.top_song_by_likes = max(self.songs.keys(), key=lambda k: self.songs[k].total_likes) if max((s.total_likes for s in self.songs.values()), default=0) > 0 else None
            self.top_song_by_listens = max(self.songs.keys(), key=lambda k: self.songs[k].total_listens)
            self.top_song_by_revenue = max(self.songs.keys(), key=lambda k: self.songs[k].primary_revenue_dcmx) if max((s.primary_revenue_dcmx for s in self.songs.values()), default=0) > 0 else None


class AnalyticsDashboard:
    """
    Analytics dashboard for artist insights.
    
    Tracks:
    - Song performance metrics
    - Listener demographics
    - Revenue analytics
    - Engagement trends
    - Growth metrics
    """
    
    def __init__(self):
        """Initialize analytics dashboard."""
        self.artists: Dict[str, ArtistAnalytics] = {}
        self.engagement_events: List[Dict] = []
    
    def register_artist(self, wallet: str, name: str) -> ArtistAnalytics:
        """Register artist in analytics system."""
        analytics = ArtistAnalytics(
            artist_wallet=wallet,
            artist_name=name,
            join_date=datetime.utcnow().isoformat(),
        )
        self.artists[wallet] = analytics
        logger.info(f"Artist registered: {name} ({wallet})")
        return analytics
    
    def add_song(
        self,
        artist_wallet: str,
        song_id: str,
        title: str,
    ) -> SongAnalytics:
        """Add song for tracking."""
        if artist_wallet not in self.artists:
            raise ValueError(f"Artist {artist_wallet} not registered")
        
        song = SongAnalytics(
            song_id=song_id,
            title=title,
            artist_wallet=artist_wallet,
            created_date=datetime.utcnow().isoformat(),
        )
        
        self.artists[artist_wallet].songs[song_id] = song
        logger.info(f"Song added: {title} by {artist_wallet}")
        return song
    
    def record_listen(
        self,
        artist_wallet: str,
        song_id: str,
        listener_id: str,
        completion_percentage: float,
        listen_duration_seconds: int,
    ):
        """Record a listening event."""
        if artist_wallet not in self.artists:
            raise ValueError(f"Artist {artist_wallet} not registered")
        
        if song_id not in self.artists[artist_wallet].songs:
            raise ValueError(f"Song {song_id} not found")
        
        song = self.artists[artist_wallet].songs[song_id]
        song.total_listens += 1
        
        # Update completion distribution
        if completion_percentage >= 0.9:
            key = "90-100%"
        elif completion_percentage >= 0.75:
            key = "75-89%"
        elif completion_percentage >= 0.5:
            key = "50-74%"
        else:
            key = "0-49%"
        
        song.completion_distribution[key] = song.completion_distribution.get(key, 0) + 1
        
        # Update average completion
        song.average_completion_percentage = (
            (song.average_completion_percentage * (song.total_listens - 1) + completion_percentage) /
            song.total_listens
        )
        
        # Track listener
        if listener_id not in self.artists[artist_wallet].listener_demographics:
            self.artists[artist_wallet].listener_demographics[listener_id] = ListenerDemographic(
                listener_id=listener_id,
                username=f"User_{listener_id[:8]}",
                first_listen_date=datetime.utcnow().isoformat(),
            )
            self.artists[artist_wallet].unique_listeners += 1
        else:
            self.artists[artist_wallet].repeat_listeners += 1
        
        listener = self.artists[artist_wallet].listener_demographics[listener_id]
        listener.total_listens += 1
        listener.average_completion = (
            (listener.average_completion * (listener.total_listens - 1) + completion_percentage) /
            listener.total_listens
        )
        listener.last_listen_date = datetime.utcnow().isoformat()
        
        self.engagement_events.append({
            "type": EngagementType.LISTEN.value,
            "artist": artist_wallet,
            "song_id": song_id,
            "listener": listener_id,
            "completion": completion_percentage,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def record_like(
        self,
        artist_wallet: str,
        song_id: str,
        user_id: str,
    ):
        """Record a 'like' vote on a song."""
        if artist_wallet not in self.artists:
            raise ValueError(f"Artist {artist_wallet} not registered")
        
        if song_id not in self.artists[artist_wallet].songs:
            raise ValueError(f"Song {song_id} not found")
        
        song = self.artists[artist_wallet].songs[song_id]
        song.total_likes += 1
        song.calculate_sentiment()
        
        # Update listener
        if user_id in self.artists[artist_wallet].listener_demographics:
            self.artists[artist_wallet].listener_demographics[user_id].likes_given += 1
        
        self.artists[artist_wallet].total_likes += 1
        
        self.engagement_events.append({
            "type": EngagementType.LIKE.value,
            "artist": artist_wallet,
            "song_id": song_id,
            "user": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def record_dislike(
        self,
        artist_wallet: str,
        song_id: str,
        user_id: str,
    ):
        """Record a 'dislike' vote on a song."""
        if artist_wallet not in self.artists:
            raise ValueError(f"Artist {artist_wallet} not registered")
        
        if song_id not in self.artists[artist_wallet].songs:
            raise ValueError(f"Song {song_id} not found")
        
        song = self.artists[artist_wallet].songs[song_id]
        song.total_dislikes += 1
        song.calculate_sentiment()
        
        # Update listener
        if user_id in self.artists[artist_wallet].listener_demographics:
            self.artists[artist_wallet].listener_demographics[user_id].dislikes_given += 1
        
        self.artists[artist_wallet].total_dislikes += 1
        
        self.engagement_events.append({
            "type": EngagementType.DISLIKE.value,
            "artist": artist_wallet,
            "song_id": song_id,
            "user": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    def record_sale(
        self,
        artist_wallet: str,
        song_id: str,
        sale_price_dcmx: float,
        is_secondary: bool = False,
    ):
        """Record NFT sale (primary or secondary)."""
        if artist_wallet not in self.artists:
            raise ValueError(f"Artist {artist_wallet} not registered")
        
        if song_id not in self.artists[artist_wallet].songs:
            raise ValueError(f"Song {song_id} not found")
        
        song = self.artists[artist_wallet].songs[song_id]
        
        if is_secondary:
            song.secondary_royalties_dcmx += sale_price_dcmx
        else:
            song.primary_revenue_dcmx += sale_price_dcmx
            song.sales_count += 1
        
        self.artists[artist_wallet].total_earnings_dcmx += sale_price_dcmx
    
    def get_artist_dashboard(self, artist_wallet: str) -> Dict:
        """Get complete dashboard for artist."""
        if artist_wallet not in self.artists:
            raise ValueError(f"Artist {artist_wallet} not registered")
        
        artist = self.artists[artist_wallet]
        artist.update_totals()
        
        return {
            "artist": {
                "name": artist.artist_name,
                "wallet": artist.artist_wallet,
                "join_date": artist.join_date,
            },
            "overview": {
                "total_songs": artist.total_songs,
                "total_listens": artist.total_listens,
                "unique_listeners": artist.unique_listeners,
                "repeat_listeners": artist.repeat_listeners,
                "total_earnings_dcmx": artist.total_earnings_dcmx,
                "current_balance_dcmx": artist.current_balance_dcmx,
            },
            "engagement": {
                "total_likes": artist.total_likes,
                "total_dislikes": artist.total_dislikes,
                "overall_sentiment": "positive" if artist.total_likes > artist.total_dislikes else "negative" if artist.total_dislikes > artist.total_likes else "neutral",
                "sentiment_percentage": (artist.total_likes / (artist.total_likes + artist.total_dislikes) * 100) if (artist.total_likes + artist.total_dislikes) > 0 else 0,
            },
            "revenue": {
                "primary_sales_dcmx": artist.total_primary_sales_dcmx,
                "secondary_royalties_dcmx": artist.total_secondary_royalties_dcmx,
                "total_earnings_dcmx": artist.total_earnings_dcmx,
            },
            "top_performers": {
                "top_by_likes": artist.top_song_by_likes,
                "top_by_listens": artist.top_song_by_listens,
                "top_by_revenue": artist.top_song_by_revenue,
            },
            "songs": [
                {
                    "id": song_id,
                    "title": song.title,
                    "listens": song.total_listens,
                    "likes": song.total_likes,
                    "dislikes": song.total_dislikes,
                    "sentiment": f"{song.sentiment_percentage:.1f}%",
                    "avg_completion": f"{song.average_completion_percentage*100:.1f}%",
                    "revenue_dcmx": song.primary_revenue_dcmx + song.secondary_royalties_dcmx,
                }
                for song_id, song in artist.songs.items()
            ],
            "listener_demographics": {
                "total_unique": artist.unique_listeners,
                "repeat_visitors": artist.repeat_listeners,
                "top_listeners": sorted(
                    [
                        {
                            "username": listener.username,
                            "listens": listener.total_listens,
                            "avg_completion": f"{listener.average_completion*100:.1f}%",
                        }
                        for listener in artist.listener_demographics.values()
                    ],
                    key=lambda x: x["listens"],
                    reverse=True
                )[:10]
            },
        }
    
    def get_platform_leaderboard(self) -> Dict:
        """Get platform-wide leaderboard."""
        self.artists_list = []
        
        for artist in self.artists.values():
            artist.update_totals()
            self.artists_list.append({
                "name": artist.artist_name,
                "wallet": artist.artist_wallet,
                "songs": artist.total_songs,
                "listens": artist.total_listens,
                "likes": artist.total_likes,
                "earnings_dcmx": artist.total_earnings_dcmx,
                "sentiment": "positive" if artist.total_likes > artist.total_dislikes else "negative" if artist.total_dislikes > artist.total_likes else "neutral",
            })
        
        return {
            "total_artists": len(self.artists),
            "leaderboard": sorted(self.artists_list, key=lambda x: x["earnings_dcmx"], reverse=True),
        }
