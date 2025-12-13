"""
Analytics & Insights System

Advanced analytics for artists and platform monitoring.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class ListeningStats:
    """Track listening statistics."""
    track_id: str
    total_plays: int = 0
    unique_listeners: int = 0
    total_listen_time_seconds: int = 0
    completion_rate: float = 0.0  # % who listened to completion
    
    # Geographic data
    listeners_by_country: Dict[str, int] = field(default_factory=dict)
    listeners_by_city: Dict[str, int] = field(default_factory=dict)
    
    # Time-based data
    plays_by_hour: Dict[int, int] = field(default_factory=dict)  # Hour 0-23
    plays_by_day: Dict[str, int] = field(default_factory=dict)  # Day of week
    
    # Platform data
    plays_by_platform: Dict[str, int] = field(default_factory=dict)  # web, mobile, etc.
    
    def add_play(
        self,
        listener_id: str,
        listen_duration: int,
        track_duration: int,
        country: Optional[str] = None,
        city: Optional[str] = None,
        platform: str = "web",
        timestamp: Optional[datetime] = None,
    ):
        """Record a play event."""
        self.total_plays += 1
        self.total_listen_time_seconds += listen_duration
        
        # Update completion rate
        if listen_duration >= track_duration * 0.9:  # 90% = complete
            self.completion_rate = (
                (self.completion_rate * (self.total_plays - 1) + 1) / self.total_plays
            )
        
        # Geographic
        if country:
            self.listeners_by_country[country] = self.listeners_by_country.get(country, 0) + 1
        if city:
            self.listeners_by_city[city] = self.listeners_by_city.get(city, 0) + 1
        
        # Platform
        self.plays_by_platform[platform] = self.plays_by_platform.get(platform, 0) + 1
        
        # Time-based
        if timestamp:
            hour = timestamp.hour
            day = timestamp.strftime("%A")
            self.plays_by_hour[hour] = self.plays_by_hour.get(hour, 0) + 1
            self.plays_by_day[day] = self.plays_by_day.get(day, 0) + 1


@dataclass
class RevenueStats:
    """Track revenue and earnings."""
    artist_wallet: str
    total_revenue_usd: float = 0.0
    total_revenue_eth: float = 0.0
    total_revenue_dcmx: float = 0.0
    
    # Revenue sources
    nft_sales_revenue: float = 0.0
    royalty_revenue: float = 0.0
    streaming_revenue: float = 0.0
    tips_revenue: float = 0.0
    
    # NFT stats
    total_nfts_sold: int = 0
    average_nft_price: float = 0.0
    
    # Time-based
    revenue_by_month: Dict[str, float] = field(default_factory=dict)  # YYYY-MM -> USD
    
    def add_sale(
        self,
        amount_usd: float,
        amount_eth: float,
        sale_type: str,  # "nft", "royalty", "streaming", "tip"
        timestamp: Optional[datetime] = None,
    ):
        """Record a revenue event."""
        self.total_revenue_usd += amount_usd
        self.total_revenue_eth += amount_eth
        
        # Categorize by type
        if sale_type == "nft":
            self.nft_sales_revenue += amount_usd
            self.total_nfts_sold += 1
            self.average_nft_price = self.nft_sales_revenue / self.total_nfts_sold
        elif sale_type == "royalty":
            self.royalty_revenue += amount_usd
        elif sale_type == "streaming":
            self.streaming_revenue += amount_usd
        elif sale_type == "tip":
            self.tips_revenue += amount_usd
        
        # Time-based
        if timestamp:
            month = timestamp.strftime("%Y-%m")
            self.revenue_by_month[month] = self.revenue_by_month.get(month, 0.0) + amount_usd


@dataclass
class AudienceInsights:
    """Audience demographic and behavioral insights."""
    artist_wallet: str
    
    # Demographics
    total_fans: int = 0
    age_distribution: Dict[str, int] = field(default_factory=dict)  # "18-24", "25-34", etc.
    gender_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Engagement
    average_session_duration: float = 0.0  # minutes
    return_listener_rate: float = 0.0  # % who return
    social_shares: int = 0
    playlist_adds: int = 0
    
    # Top listeners
    top_listeners: List[Dict[str, Any]] = field(default_factory=list)  # [{wallet, plays, hours}]
    
    # Growth
    follower_growth: Dict[str, int] = field(default_factory=dict)  # Date -> cumulative followers


@dataclass
class NetworkStats:
    """Platform-wide network statistics."""
    total_artists: int = 0
    total_tracks: int = 0
    total_listeners: int = 0
    total_nfts_minted: int = 0
    total_volume_usd: float = 0.0
    
    # Network health
    active_nodes: int = 0
    average_uptime_percentage: float = 0.0
    total_bandwidth_gb: float = 0.0
    
    # Engagement
    daily_active_users: int = 0
    monthly_active_users: int = 0
    average_session_time: float = 0.0
    
    # Content
    tracks_uploaded_today: int = 0
    tracks_uploaded_this_month: int = 0


class AnalyticsEngine:
    """
    Analytics & Insights Engine.
    
    Provides real-time and historical analytics for artists and platform.
    """
    
    def __init__(self):
        self.track_stats: Dict[str, ListeningStats] = {}
        self.artist_revenue: Dict[str, RevenueStats] = {}
        self.audience_insights: Dict[str, AudienceInsights] = {}
        self.network_stats = NetworkStats()
        
        # Event log for real-time processing
        self.event_queue: List[Dict[str, Any]] = []
    
    async def track_play_event(
        self,
        track_id: str,
        listener_id: str,
        listen_duration: int,
        track_duration: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a track play event."""
        if track_id not in self.track_stats:
            self.track_stats[track_id] = ListeningStats(track_id=track_id)
        
        stats = self.track_stats[track_id]
        stats.add_play(
            listener_id=listener_id,
            listen_duration=listen_duration,
            track_duration=track_duration,
            country=metadata.get('country') if metadata else None,
            city=metadata.get('city') if metadata else None,
            platform=metadata.get('platform', 'web') if metadata else 'web',
            timestamp=datetime.now(),
        )
        
        # Queue for real-time processing
        self.event_queue.append({
            "type": "play",
            "track_id": track_id,
            "listener_id": listener_id,
            "timestamp": datetime.now().isoformat(),
        })
    
    async def track_revenue_event(
        self,
        artist_wallet: str,
        amount_usd: float,
        amount_eth: float,
        sale_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a revenue event."""
        if artist_wallet not in self.artist_revenue:
            self.artist_revenue[artist_wallet] = RevenueStats(artist_wallet=artist_wallet)
        
        stats = self.artist_revenue[artist_wallet]
        stats.add_sale(
            amount_usd=amount_usd,
            amount_eth=amount_eth,
            sale_type=sale_type,
            timestamp=datetime.now(),
        )
        
        # Update network totals
        self.network_stats.total_volume_usd += amount_usd
    
    def get_track_analytics(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific track."""
        stats = self.track_stats.get(track_id)
        if not stats:
            return None
        
        return {
            "track_id": track_id,
            "total_plays": stats.total_plays,
            "unique_listeners": stats.unique_listeners,
            "total_hours": stats.total_listen_time_seconds / 3600,
            "completion_rate": f"{stats.completion_rate * 100:.1f}%",
            "geography": {
                "top_countries": sorted(
                    stats.listeners_by_country.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                "top_cities": sorted(
                    stats.listeners_by_city.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
            },
            "platforms": stats.plays_by_platform,
            "peak_hours": sorted(
                stats.plays_by_hour.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }
    
    def get_artist_dashboard(self, artist_wallet: str) -> Dict[str, Any]:
        """Get comprehensive artist dashboard."""
        revenue = self.artist_revenue.get(artist_wallet, RevenueStats(artist_wallet=artist_wallet))
        
        # Aggregate track stats for artist
        artist_tracks = [t for t in self.track_stats.values()]  # Filter by artist in real impl
        total_plays = sum(t.total_plays for t in artist_tracks)
        total_listeners = sum(t.unique_listeners for t in artist_tracks)
        
        return {
            "artist": artist_wallet,
            "revenue": {
                "total_usd": f"${revenue.total_revenue_usd:,.2f}",
                "total_eth": f"{revenue.total_revenue_eth:.4f} ETH",
                "breakdown": {
                    "nft_sales": f"${revenue.nft_sales_revenue:,.2f}",
                    "royalties": f"${revenue.royalty_revenue:,.2f}",
                    "streaming": f"${revenue.streaming_revenue:,.2f}",
                    "tips": f"${revenue.tips_revenue:,.2f}",
                },
                "nfts_sold": revenue.total_nfts_sold,
                "avg_nft_price": f"${revenue.average_nft_price:,.2f}",
            },
            "engagement": {
                "total_plays": total_plays,
                "total_listeners": total_listeners,
                "tracks_published": len(artist_tracks),
            },
            "growth": {
                "revenue_by_month": revenue.revenue_by_month,
            },
        }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get platform-wide statistics."""
        return {
            "network": {
                "total_artists": self.network_stats.total_artists,
                "total_tracks": self.network_stats.total_tracks,
                "total_listeners": self.network_stats.total_listeners,
                "total_volume": f"${self.network_stats.total_volume_usd:,.2f}",
            },
            "infrastructure": {
                "active_nodes": self.network_stats.active_nodes,
                "average_uptime": f"{self.network_stats.average_uptime_percentage:.1f}%",
                "total_bandwidth": f"{self.network_stats.total_bandwidth_gb:.2f} GB",
            },
            "engagement": {
                "daily_active_users": self.network_stats.daily_active_users,
                "monthly_active_users": self.network_stats.monthly_active_users,
                "avg_session_time": f"{self.network_stats.average_session_time:.1f} min",
            },
        }
    
    async def generate_insights(self, artist_wallet: str) -> Dict[str, Any]:
        """Generate AI-powered insights for artist."""
        revenue = self.artist_revenue.get(artist_wallet)
        if not revenue:
            return {"insights": []}
        
        insights = []
        
        # Revenue trend
        if len(revenue.revenue_by_month) >= 2:
            months = sorted(revenue.revenue_by_month.keys())
            last_month = revenue.revenue_by_month[months[-1]]
            prev_month = revenue.revenue_by_month[months[-2]]
            
            if last_month > prev_month:
                growth = ((last_month - prev_month) / prev_month) * 100
                insights.append({
                    "type": "positive",
                    "title": "Revenue Growth",
                    "message": f"Your revenue grew {growth:.1f}% last month!",
                    "recommendation": "Keep up the momentum by releasing new content.",
                })
            else:
                decline = ((prev_month - last_month) / prev_month) * 100
                insights.append({
                    "type": "warning",
                    "title": "Revenue Decline",
                    "message": f"Revenue decreased {decline:.1f}% last month.",
                    "recommendation": "Consider promotional campaigns or new releases.",
                })
        
        # NFT pricing
        if revenue.total_nfts_sold > 0:
            if revenue.average_nft_price < 0.05:
                insights.append({
                    "type": "info",
                    "title": "NFT Pricing",
                    "message": f"Your average NFT price is ${revenue.average_nft_price:.2f}",
                    "recommendation": "You may be undervaluing your work. Consider raising prices.",
                })
        
        return {"insights": insights}


class RealtimeDashboard:
    """Real-time analytics dashboard."""
    
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.engine = analytics_engine
        self.subscribers: Dict[str, List] = defaultdict(list)  # artist -> [websocket_connections]
    
    async def subscribe(self, artist_wallet: str, websocket):
        """Subscribe to real-time updates."""
        self.subscribers[artist_wallet].append(websocket)
    
    async def broadcast_update(self, artist_wallet: str, update: Dict[str, Any]):
        """Broadcast update to all subscribers."""
        for websocket in self.subscribers.get(artist_wallet, []):
            try:
                await websocket.send_json(update)
            except:
                pass  # Handle disconnected clients
    
    async def process_events(self):
        """Process event queue and broadcast updates."""
        while True:
            if self.engine.event_queue:
                event = self.engine.event_queue.pop(0)
                
                # Process and broadcast
                if event['type'] == 'play':
                    # Notify artist of new play
                    # In real impl, lookup artist from track_id
                    pass
            
            await asyncio.sleep(1)  # Process every second
