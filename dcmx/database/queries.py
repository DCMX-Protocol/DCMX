"""
Database Query Helpers

Provides convenient query functions for common operations.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from .models import (
    BlockchainEvent,
    UserProfile,
    NFTIndex,
    RewardClaimIndex,
    TransactionIndex,
    ComplianceIndex,
    Analytics,
)
from .database import get_session

logger = logging.getLogger(__name__)


class DatabaseQueries:
    """Helper class for common database queries."""
    
    @staticmethod
    def get_user_by_wallet(wallet_address: str) -> Optional[UserProfile]:
        """Get user profile by wallet address."""
        session = get_session()
        try:
            return (
                session.query(UserProfile)
                .filter(UserProfile.wallet_address == wallet_address)
                .filter(UserProfile.deleted_at.is_(None))
                .first()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_nfts_by_owner(owner_wallet: str, limit: int = 100) -> List[NFTIndex]:
        """Get NFTs owned by wallet."""
        session = get_session()
        try:
            return (
                session.query(NFTIndex)
                .filter(NFTIndex.owner_wallet == owner_wallet)
                .order_by(desc(NFTIndex.minted_at))
                .limit(limit)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_nfts_by_artist(artist_wallet: str, limit: int = 100) -> List[NFTIndex]:
        """Get NFTs created by artist."""
        session = get_session()
        try:
            return (
                session.query(NFTIndex)
                .filter(NFTIndex.artist_wallet == artist_wallet)
                .order_by(desc(NFTIndex.minted_at))
                .limit(limit)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_nft_by_token_id(token_id: int, contract_address: str) -> Optional[NFTIndex]:
        """Get NFT by token ID."""
        session = get_session()
        try:
            return (
                session.query(NFTIndex)
                .filter(NFTIndex.token_id == token_id)
                .filter(NFTIndex.contract_address == contract_address)
                .first()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_user_transactions(
        wallet_address: str,
        limit: int = 100,
        tx_type: Optional[str] = None
    ) -> List[TransactionIndex]:
        """Get transactions for user."""
        session = get_session()
        try:
            query = (
                session.query(TransactionIndex)
                .filter(TransactionIndex.user_wallet == wallet_address)
            )
            
            if tx_type:
                query = query.filter(TransactionIndex.tx_type == tx_type)
            
            return (
                query
                .order_by(desc(TransactionIndex.timestamp))
                .limit(limit)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_reward_claims(
        wallet_address: str,
        limit: int = 100
    ) -> List[RewardClaimIndex]:
        """Get reward claims for user."""
        session = get_session()
        try:
            return (
                session.query(RewardClaimIndex)
                .filter(RewardClaimIndex.claimant_wallet == wallet_address)
                .order_by(desc(RewardClaimIndex.submitted_at))
                .limit(limit)
                .all()
            )
        finally:
            session.close()
    
    @staticmethod
    def get_platform_stats() -> Dict[str, Any]:
        """Get platform-wide statistics."""
        session = get_session()
        try:
            return {
                "total_users": session.query(func.count(UserProfile.id)).scalar(),
                "total_artists": (
                    session.query(func.count(UserProfile.id))
                    .filter(UserProfile.is_artist == True)
                    .scalar()
                ),
                "total_nfts": session.query(func.count(NFTIndex.id)).scalar(),
                "total_transactions": session.query(func.count(TransactionIndex.id)).scalar(),
                "total_claims": session.query(func.count(RewardClaimIndex.id)).scalar(),
            }
        finally:
            session.close()
    
    @staticmethod
    def search_nfts(
        query: str,
        limit: int = 50
    ) -> List[NFTIndex]:
        """Search NFTs by title or artist."""
        session = get_session()
        try:
            search_pattern = f"%{query}%"
            return (
                session.query(NFTIndex)
                .filter(
                    (NFTIndex.title.ilike(search_pattern)) |
                    (NFTIndex.artist.ilike(search_pattern))
                )
                .order_by(desc(NFTIndex.minted_at))
                .limit(limit)
                .all()
            )
        finally:
            session.close()
