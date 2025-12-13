"""
Social Features System

Community engagement, comments, likes, and social interactions.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json


class ReactionType(Enum):
    """Types of reactions users can give."""
    LIKE = "like"
    LOVE = "love"
    FIRE = "fire"
    STAR = "star"
    REPOST = "repost"


@dataclass
class Comment:
    """User comment on a track or artist."""
    id: str
    content: str
    author: str  # Wallet address or username
    track_id: Optional[str] = None
    artist_id: Optional[str] = None
    parent_comment_id: Optional[str] = None  # For replies
    created_at: datetime = field(default_factory=datetime.now)
    edited_at: Optional[datetime] = None
    likes: int = 0
    replies: List[str] = field(default_factory=list)  # Comment IDs
    flagged: bool = False
    deleted: bool = False
    
    def edit(self, new_content: str):
        """Edit comment content."""
        self.content = new_content
        self.edited_at = datetime.now()
    
    def flag(self):
        """Flag comment for moderation."""
        self.flagged = True
    
    def delete(self):
        """Soft delete comment."""
        self.deleted = True
        self.content = "[Comment deleted]"


@dataclass
class Reaction:
    """User reaction to content."""
    user: str  # Wallet address
    target_id: str  # Track ID, artist ID, or comment ID
    target_type: str  # "track", "artist", "comment"
    reaction_type: ReactionType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Playlist:
    """User-created playlist."""
    id: str
    name: str
    description: str
    owner: str  # Wallet address
    tracks: List[str] = field(default_factory=list)  # Track IDs
    cover_image_url: Optional[str] = None
    is_public: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    followers: int = 0
    plays: int = 0
    
    def add_track(self, track_id: str):
        """Add track to playlist."""
        if track_id not in self.tracks:
            self.tracks.append(track_id)
            self.updated_at = datetime.now()
    
    def remove_track(self, track_id: str):
        """Remove track from playlist."""
        if track_id in self.tracks:
            self.tracks.remove(track_id)
            self.updated_at = datetime.now()
    
    def reorder_tracks(self, track_ids: List[str]):
        """Reorder tracks in playlist."""
        self.tracks = track_ids
        self.updated_at = datetime.now()


@dataclass
class UserProfile:
    """Extended user profile with social features."""
    wallet_address: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    
    # Social connections
    followers: List[str] = field(default_factory=list)  # Wallet addresses
    following: List[str] = field(default_factory=list)
    
    # Activity
    total_listens: int = 0
    favorite_tracks: List[str] = field(default_factory=list)
    favorite_artists: List[str] = field(default_factory=list)
    
    # Social stats
    comments_count: int = 0
    playlists_count: int = 0
    
    # Settings
    is_public: bool = True
    allow_comments: bool = True
    
    def follow(self, wallet_address: str):
        """Follow another user."""
        if wallet_address not in self.following:
            self.following.append(wallet_address)
    
    def unfollow(self, wallet_address: str):
        """Unfollow a user."""
        if wallet_address in self.following:
            self.following.remove(wallet_address)
    
    def add_follower(self, wallet_address: str):
        """Add a follower."""
        if wallet_address not in self.followers:
            self.followers.append(wallet_address)
    
    def remove_follower(self, wallet_address: str):
        """Remove a follower."""
        if wallet_address in self.followers:
            self.followers.remove(wallet_address)


class SocialFeatures:
    """
    Social Features System.
    
    Manages comments, reactions, playlists, and user interactions.
    """
    
    def __init__(self):
        self.comments: Dict[str, Comment] = {}
        self.reactions: Dict[str, List[Reaction]] = {}  # target_id -> reactions
        self.playlists: Dict[str, Playlist] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # Activity feed
        self.activity_feed: List[Dict[str, Any]] = []
    
    async def create_comment(
        self,
        content: str,
        author: str,
        track_id: Optional[str] = None,
        artist_id: Optional[str] = None,
        parent_comment_id: Optional[str] = None,
    ) -> Comment:
        """
        Create a new comment.
        
        Args:
            content: Comment text
            author: Wallet address of author
            track_id: Track being commented on
            artist_id: Artist being commented on
            parent_comment_id: Parent comment for replies
            
        Returns:
            Created Comment
        """
        # Validate
        if not content.strip():
            raise ValueError("Comment cannot be empty")
        
        if len(content) > 1000:
            raise ValueError("Comment too long (max 1000 characters)")
        
        # Check user can comment
        profile = self.user_profiles.get(author)
        if profile and not profile.allow_comments:
            raise ValueError("Comments disabled for this user")
        
        # Create comment
        comment_id = f"comment_{len(self.comments) + 1}"
        comment = Comment(
            id=comment_id,
            content=content,
            author=author,
            track_id=track_id,
            artist_id=artist_id,
            parent_comment_id=parent_comment_id,
        )
        
        self.comments[comment_id] = comment
        
        # Update parent if reply
        if parent_comment_id and parent_comment_id in self.comments:
            self.comments[parent_comment_id].replies.append(comment_id)
        
        # Update user profile
        if author in self.user_profiles:
            self.user_profiles[author].comments_count += 1
        
        # Add to activity feed
        self._add_activity({
            "type": "comment",
            "user": author,
            "comment_id": comment_id,
            "track_id": track_id,
            "timestamp": datetime.now().isoformat(),
        })
        
        return comment
    
    async def add_reaction(
        self,
        user: str,
        target_id: str,
        target_type: str,
        reaction_type: ReactionType,
    ) -> Reaction:
        """Add a reaction to content."""
        # Check if already reacted
        existing = self.reactions.get(target_id, [])
        for reaction in existing:
            if reaction.user == user and reaction.reaction_type == reaction_type:
                # Already reacted, remove it (toggle)
                existing.remove(reaction)
                return reaction
        
        # Create new reaction
        reaction = Reaction(
            user=user,
            target_id=target_id,
            target_type=target_type,
            reaction_type=reaction_type,
        )
        
        if target_id not in self.reactions:
            self.reactions[target_id] = []
        
        self.reactions[target_id].append(reaction)
        
        # Update counts
        if target_type == "comment" and target_id in self.comments:
            self.comments[target_id].likes += 1
        
        # Add to activity feed
        self._add_activity({
            "type": "reaction",
            "user": user,
            "target_id": target_id,
            "reaction": reaction_type.value,
            "timestamp": datetime.now().isoformat(),
        })
        
        return reaction
    
    async def create_playlist(
        self,
        name: str,
        owner: str,
        description: str = "",
        is_public: bool = True,
    ) -> Playlist:
        """Create a new playlist."""
        playlist_id = f"playlist_{len(self.playlists) + 1}"
        
        playlist = Playlist(
            id=playlist_id,
            name=name,
            description=description,
            owner=owner,
            is_public=is_public,
        )
        
        self.playlists[playlist_id] = playlist
        
        # Update user profile
        if owner in self.user_profiles:
            self.user_profiles[owner].playlists_count += 1
        
        return playlist
    
    async def follow_user(self, follower: str, followed: str):
        """Follow another user."""
        # Get or create profiles
        if follower not in self.user_profiles:
            self.user_profiles[follower] = UserProfile(wallet_address=follower)
        
        if followed not in self.user_profiles:
            self.user_profiles[followed] = UserProfile(wallet_address=followed)
        
        # Update relationships
        self.user_profiles[follower].follow(followed)
        self.user_profiles[followed].add_follower(follower)
        
        # Add to activity feed
        self._add_activity({
            "type": "follow",
            "follower": follower,
            "followed": followed,
            "timestamp": datetime.now().isoformat(),
        })
    
    async def get_user_feed(
        self,
        user: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get personalized activity feed for user."""
        profile = self.user_profiles.get(user)
        if not profile:
            return []
        
        # Get activity from followed users
        feed_items = []
        for activity in reversed(self.activity_feed[-1000:]):  # Last 1000 activities
            if activity['user'] in profile.following or activity['user'] == user:
                feed_items.append(activity)
            
            if len(feed_items) >= limit:
                break
        
        return feed_items
    
    def get_track_comments(
        self,
        track_id: str,
        sort_by: str = "recent",
    ) -> List[Comment]:
        """Get all comments for a track."""
        comments = [
            c for c in self.comments.values()
            if c.track_id == track_id and not c.deleted
        ]
        
        if sort_by == "recent":
            comments.sort(key=lambda c: c.created_at, reverse=True)
        elif sort_by == "popular":
            comments.sort(key=lambda c: c.likes, reverse=True)
        
        return comments
    
    def get_track_reactions(self, track_id: str) -> Dict[str, int]:
        """Get reaction summary for track."""
        reactions = self.reactions.get(track_id, [])
        
        summary = {reaction.value: 0 for reaction in ReactionType}
        for reaction in reactions:
            summary[reaction.reaction_type.value] += 1
        
        return summary
    
    def get_user_playlists(self, user: str) -> List[Playlist]:
        """Get all playlists by user."""
        return [
            p for p in self.playlists.values()
            if p.owner == user
        ]
    
    def get_trending_tracks(
        self,
        time_window_hours: int = 24,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get trending tracks based on activity."""
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        
        # Count reactions per track
        track_scores: Dict[str, int] = {}
        
        for target_id, reactions in self.reactions.items():
            if target_id.startswith("track_"):
                score = 0
                for reaction in reactions:
                    if reaction.timestamp >= cutoff:
                        # Weight different reactions
                        weights = {
                            ReactionType.LIKE: 1,
                            ReactionType.LOVE: 2,
                            ReactionType.FIRE: 3,
                            ReactionType.STAR: 2,
                            ReactionType.REPOST: 5,
                        }
                        score += weights.get(reaction.reaction_type, 1)
                
                track_scores[target_id] = score
        
        # Sort by score
        trending = sorted(
            track_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        return [
            {"track_id": track_id, "score": score}
            for track_id, score in trending
        ]
    
    def _add_activity(self, activity: Dict[str, Any]):
        """Add activity to feed."""
        self.activity_feed.append(activity)
        
        # Keep only last 10,000 items
        if len(self.activity_feed) > 10000:
            self.activity_feed = self.activity_feed[-10000:]


# Moderation tools

class ContentModeration:
    """Content moderation system."""
    
    def __init__(self, social_features: SocialFeatures):
        self.social = social_features
        self.banned_words = set()  # Load from config
        self.flagged_content: List[str] = []
    
    async def moderate_comment(self, comment: Comment) -> bool:
        """
        Moderate comment for inappropriate content.
        
        Returns True if comment is acceptable, False if should be blocked.
        """
        content_lower = comment.content.lower()
        
        # Check for banned words
        for word in self.banned_words:
            if word in content_lower:
                comment.flag()
                self.flagged_content.append(comment.id)
                return False
        
        # Check for spam patterns
        if len(set(comment.content)) < 5:  # Too repetitive
            comment.flag()
            return False
        
        return True
    
    async def review_flagged_content(self) -> List[Comment]:
        """Get all flagged content for manual review."""
        return [
            self.social.comments[comment_id]
            for comment_id in self.flagged_content
            if comment_id in self.social.comments
        ]
