"""
DCMX ML-based Recommendations Engine

Intelligent song discovery using:
- Collaborative filtering (user-user similarity)
- Content-based filtering (song features)
- Trending algorithm (recent + popular)
- Personalized discovery
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import random

logger = logging.getLogger(__name__)


@dataclass
class UserProfile:
    """User music preference profile."""
    user_id: str
    liked_songs: Set[str] = field(default_factory=set)  # Songs user liked
    disliked_songs: Set[str] = field(default_factory=set)  # Songs user disliked
    listened_songs: Set[str] = field(default_factory=set)  # All songs listened to
    favorite_artists: Dict[str, int] = field(default_factory=dict)  # artist -> listen count
    listening_history: List[Tuple[str, float, datetime]] = field(default_factory=list)  # (song_id, completion, timestamp)
    
    def get_preference_vector(self, all_songs: Dict[str, any]) -> Dict[str, float]:
        """
        Generate preference vector for this user.
        
        Returns: {feature: score, ...}
        """
        vector = defaultdict(float)
        
        for song_id in self.liked_songs:
            if song_id in all_songs:
                song = all_songs[song_id]
                # Boost liked song features
                for feature in song.get("features", []):
                    vector[feature] += 2.0
        
        for song_id in self.disliked_songs:
            if song_id in all_songs:
                song = all_songs[song_id]
                # Penalize disliked song features
                for feature in song.get("features", []):
                    vector[feature] -= 1.0
        
        return dict(vector)


@dataclass
class SongProfile:
    """Song characteristics for content-based filtering."""
    song_id: str
    title: str
    artist_id: str
    features: List[str] = field(default_factory=list)  # ["energetic", "upbeat", "dance"]
    genre: str = ""
    tempo_bpm: int = 0
    energy_level: float = 0.5  # 0.0-1.0
    danceability: float = 0.5  # 0.0-1.0
    acousticness: float = 0.5  # 0.0-1.0
    popularity: int = 0  # 0-100
    duration_seconds: int = 0
    release_date: str = ""
    
    # Engagement metrics
    total_listens: int = 0
    total_likes: int = 0
    total_dislikes: int = 0
    average_completion: float = 0.0


@dataclass
class Recommendation:
    """Recommended song with score."""
    song_id: str
    title: str
    artist_id: str
    score: float  # 0-100
    reason: str  # Why recommended ("similar to X", "trending", etc)
    confidence: float  # 0-1.0


class RecommendationEngine:
    """
    ML-based recommendation engine for DCMX.
    
    Algorithms:
    1. Collaborative Filtering: Find users with similar taste
    2. Content-Based: Recommend songs similar to liked songs
    3. Trending: Promote high-engagement songs
    4. Exploration: Introduce new artists/genres
    """
    
    def __init__(self):
        """Initialize recommendation engine."""
        self.user_profiles: Dict[str, UserProfile] = {}
        self.song_profiles: Dict[str, SongProfile] = {}
        self.user_similarity_cache: Dict[str, Dict[str, float]] = {}
    
    def register_user(self, user_id: str) -> UserProfile:
        """Register user in system."""
        profile = UserProfile(user_id=user_id)
        self.user_profiles[user_id] = profile
        logger.info(f"User registered: {user_id}")
        return profile
    
    def register_song(
        self,
        song_id: str,
        title: str,
        artist_id: str,
        **kwargs
    ) -> SongProfile:
        """Register song for recommendations."""
        profile = SongProfile(
            song_id=song_id,
            title=title,
            artist_id=artist_id,
            **kwargs
        )
        self.song_profiles[song_id] = profile
        logger.info(f"Song registered: {title}")
        return profile
    
    def record_like(self, user_id: str, song_id: str):
        """Record user liking a song."""
        if user_id not in self.user_profiles:
            self.register_user(user_id)
        
        profile = self.user_profiles[user_id]
        profile.liked_songs.add(song_id)
        profile.listened_songs.add(song_id)
        
        if song_id in self.song_profiles:
            song = self.song_profiles[song_id]
            if song.artist_id not in profile.favorite_artists:
                profile.favorite_artists[song.artist_id] = 0
            profile.favorite_artists[song.artist_id] += 1
        
        # Invalidate cache
        self.user_similarity_cache.pop(user_id, None)
    
    def record_dislike(self, user_id: str, song_id: str):
        """Record user disliking a song."""
        if user_id not in self.user_profiles:
            self.register_user(user_id)
        
        profile = self.user_profiles[user_id]
        profile.disliked_songs.add(song_id)
        profile.listened_songs.add(song_id)
        
        # Remove from liked if present
        profile.liked_songs.discard(song_id)
        
        # Invalidate cache
        self.user_similarity_cache.pop(user_id, None)
    
    def record_listen(
        self,
        user_id: str,
        song_id: str,
        completion_percentage: float,
    ):
        """Record user listening to a song."""
        if user_id not in self.user_profiles:
            self.register_user(user_id)
        
        profile = self.user_profiles[user_id]
        profile.listened_songs.add(song_id)
        profile.listening_history.append((song_id, completion_percentage, datetime.utcnow()))
        
        # Update song popularity
        if song_id in self.song_profiles:
            song = self.song_profiles[song_id]
            song.total_listens += 1
            if completion_percentage >= 0.9:
                song.average_completion = (song.average_completion * (song.total_listens - 1) + completion_percentage) / song.total_listens
    
    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two vectors."""
        all_keys = set(vec1.keys()) | set(vec2.keys())
        
        dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in all_keys)
        magnitude1 = math.sqrt(sum(v**2 for v in vec1.values())) or 1
        magnitude2 = math.sqrt(sum(v**2 for v in vec2.values())) or 1
        
        return dot_product / (magnitude1 * magnitude2)
    
    def find_similar_users(self, user_id: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Find users with similar taste to given user."""
        if user_id not in self.user_profiles:
            return []
        
        # Check cache
        if user_id in self.user_similarity_cache:
            similar = self.user_similarity_cache[user_id]
            return sorted(similar.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        user = self.user_profiles[user_id]
        user_vector = user.get_preference_vector(self.song_profiles)
        
        similarities = {}
        
        for other_id, other_user in self.user_profiles.items():
            if other_id == user_id:
                continue
            
            other_vector = other_user.get_preference_vector(self.song_profiles)
            similarity = self.cosine_similarity(user_vector, other_vector)
            
            if similarity > 0:
                similarities[other_id] = similarity
        
        self.user_similarity_cache[user_id] = similarities
        
        return sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    def get_content_based_recommendations(
        self,
        user_id: str,
        num_recommendations: int = 10,
    ) -> List[Recommendation]:
        """
        Get recommendations based on user's liked songs.
        
        Finds songs similar to ones they've liked.
        """
        if user_id not in self.user_profiles:
            return []
        
        user = self.user_profiles[user_id]
        
        if not user.liked_songs:
            return []
        
        # Build user preference vector
        user_vector = user.get_preference_vector(self.song_profiles)
        
        recommendations = []
        
        for song_id, song in self.song_profiles.items():
            # Skip already listened
            if song_id in user.listened_songs:
                continue
            
            # Build song vector
            song_vector = {feature: 1.0 for feature in song.features}
            song_vector["energy"] = song.energy_level
            song_vector["danceability"] = song.danceability
            song_vector["acousticness"] = song.acousticness
            
            # Calculate similarity
            similarity = self.cosine_similarity(user_vector, song_vector)
            
            if similarity > 0:
                score = min(similarity * 100, 100.0)
                recommendations.append(Recommendation(
                    song_id=song_id,
                    title=song.title,
                    artist_id=song.artist_id,
                    score=score,
                    reason=f"Similar to songs you liked",
                    confidence=min(similarity, 1.0),
                ))
        
        # Sort by score and return top
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:num_recommendations]
    
    def get_collaborative_recommendations(
        self,
        user_id: str,
        num_recommendations: int = 10,
    ) -> List[Recommendation]:
        """
        Get recommendations from similar users.
        
        Finds songs that similar users liked.
        """
        if user_id not in self.user_profiles:
            return []
        
        user = self.user_profiles[user_id]
        similar_users = self.find_similar_users(user_id, top_k=5)
        
        recommendations = []
        song_scores = defaultdict(float)
        
        for similar_user_id, similarity in similar_users:
            similar_user = self.user_profiles[similar_user_id]
            
            for liked_song in similar_user.liked_songs:
                # Skip if user already knows
                if liked_song in user.listened_songs:
                    continue
                
                # Add weighted score
                song_scores[liked_song] += similarity
        
        # Convert to recommendations
        for song_id, score in sorted(song_scores.items(), key=lambda x: x[1], reverse=True)[:num_recommendations]:
            if song_id in self.song_profiles:
                song = self.song_profiles[song_id]
                recommendations.append(Recommendation(
                    song_id=song_id,
                    title=song.title,
                    artist_id=song.artist_id,
                    score=min(score * 100, 100.0),
                    reason=f"Popular with users like you",
                    confidence=min(score, 1.0),
                ))
        
        return recommendations
    
    def get_trending_recommendations(
        self,
        hours: int = 24,
        num_recommendations: int = 10,
    ) -> List[Recommendation]:
        """Get trending songs (high engagement recently)."""
        recommendations = []
        
        # Calculate trending score
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=hours)
        
        song_scores = {}
        
        for song_id, song in self.song_profiles.items():
            # Weighted trending score
            # Favorites: likes + completion
            # Penalize: dislikes + skips
            engagement = (
                song.total_likes * 10 +
                int(song.average_completion * song.total_listens) -
                song.total_dislikes * 5
            )
            
            popularity_boost = min(song.popularity / 100, 1.0)
            
            score = engagement * (1 + popularity_boost)
            
            if score > 0:
                song_scores[song_id] = score
        
        # Get top trending
        for song_id in sorted(song_scores.keys(), key=lambda x: song_scores[x], reverse=True)[:num_recommendations]:
            song = self.song_profiles[song_id]
            recommendations.append(Recommendation(
                song_id=song_id,
                title=song.title,
                artist_id=song.artist_id,
                score=min(song_scores[song_id] / 100, 100.0),
                reason="Trending now",
                confidence=0.8,
            ))
        
        return recommendations
    
    def get_personalized_recommendations(
        self,
        user_id: str,
        num_recommendations: int = 10,
    ) -> List[Recommendation]:
        """
        Get personalized recommendations combining all strategies.
        
        Mix of:
        - Content-based (60%)
        - Collaborative (30%)
        - Trending (10%)
        - Exploration (novelty/new artists)
        """
        recommendations = []
        
        content_based = self.get_content_based_recommendations(user_id, int(num_recommendations * 0.6))
        recommendations.extend(content_based)
        
        collaborative = self.get_collaborative_recommendations(user_id, int(num_recommendations * 0.3))
        recommendations.extend(collaborative)
        
        trending = self.get_trending_recommendations(num_recommendations=int(num_recommendations * 0.1))
        recommendations.extend(trending)
        
        # Deduplicate and sort
        seen = set()
        final = []
        for rec in sorted(recommendations, key=lambda x: x.score, reverse=True):
            if rec.song_id not in seen:
                final.append(rec)
                seen.add(rec.song_id)
                if len(final) >= num_recommendations:
                    break
        
        return final
    
    def get_discovery_recommendations(
        self,
        user_id: str,
        num_recommendations: int = 5,
    ) -> List[Recommendation]:
        """
        Get discovery recommendations (new artists/genres).
        
        Introduce users to content outside their usual taste.
        """
        if user_id not in self.user_profiles:
            return []
        
        user = self.user_profiles[user_id]
        listened_artists = set(song.artist_id for song_id in user.listened_songs if song_id in self.song_profiles for song in [self.song_profiles[song_id]])
        
        recommendations = []
        
        for song in list(self.song_profiles.values()):
            # Skip familiar artists
            if song.artist_id in listened_artists:
                continue
            
            # Skip already listened
            if song.song_id in user.listened_songs:
                continue
            
            # Discovery score: engagement + freshness
            discovery_score = (song.total_likes + song.total_listens * 0.1) * random.uniform(0.8, 1.2)
            
            recommendations.append(Recommendation(
                song_id=song.song_id,
                title=song.title,
                artist_id=song.artist_id,
                score=min(discovery_score / 10, 100.0),
                reason=f"Discover new artist: {song.artist_id}",
                confidence=0.6,
            ))
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:num_recommendations]
    
    def get_engine_stats(self) -> Dict:
        """Get recommendation engine statistics."""
        total_users = len(self.user_profiles)
        total_songs = len(self.song_profiles)
        
        total_likes = sum(len(u.liked_songs) for u in self.user_profiles.values())
        total_dislikes = sum(len(u.disliked_songs) for u in self.user_profiles.values())
        total_listens = sum(len(u.listened_songs) for u in self.user_profiles.values())
        
        return {
            "total_users": total_users,
            "total_songs": total_songs,
            "total_likes": total_likes,
            "total_dislikes": total_dislikes,
            "total_listens": total_listens,
            "cache_size": len(self.user_similarity_cache),
        }
