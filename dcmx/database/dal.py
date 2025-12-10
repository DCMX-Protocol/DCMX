"""
Data Access Layer (DAL) for DCMX database operations.

Provides high-level async and sync methods for common database operations:
- Legal compliance (acceptance records, audit events)
- Wallets and users
- NFTs and sales
- Rewards and royalties
- Transactions and activity
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from dcmx.database.models import (
    AcceptanceRecord, AuditEvent, DataDeletionRequest,
    Wallet, User, UserRole, UserSession,
    NFTCertificate, MusicNFT, NFTSale, NFTRoyalty,
    RewardClaim, SharingReward, ListeningReward, BandwidthReward,
    RoyaltyPayment, RevenuePool,
    Transaction, VotingRecord, SkipRecord, BlockchainTransaction,
    SystemConfiguration, AdminAction, MultisigProposal
)

logger = logging.getLogger(__name__)


class DataAccessLayer:
    """Data access layer for DCMX database operations."""
    
    # ========================================================================
    # LEGAL COMPLIANCE METHODS
    # ========================================================================
    
    @staticmethod
    async def record_acceptance(
        session: AsyncSession,
        user_id: str,
        wallet_address: str,
        document_type: str,
        version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        signature: Optional[str] = None,
        read_time_seconds: int = 0,
        document_hash: Optional[str] = None
    ) -> AcceptanceRecord:
        """Record legal document acceptance."""
        record = AcceptanceRecord(
            user_id=user_id,
            wallet_address=wallet_address,
            document_type=document_type,
            version=version,
            ip_address=ip_address,
            user_agent=user_agent,
            signature=signature,
            read_time_seconds=read_time_seconds,
            document_hash=document_hash,
            accepted_at=datetime.utcnow()
        )
        
        session.add(record)
        await session.commit()
        await session.refresh(record)
        
        logger.info(f"Acceptance recorded: {user_id} accepted {document_type} v{version}")
        return record
    
    @staticmethod
    async def get_acceptance(
        session: AsyncSession,
        user_id: str,
        document_type: str,
        version: Optional[str] = None
    ) -> Optional[AcceptanceRecord]:
        """Get most recent acceptance for a document."""
        query = select(AcceptanceRecord).where(
            and_(
                AcceptanceRecord.user_id == user_id,
                AcceptanceRecord.document_type == document_type
            )
        )
        
        if version:
            query = query.where(AcceptanceRecord.version == version)
        
        query = query.order_by(desc(AcceptanceRecord.accepted_at))
        
        result = await session.execute(query)
        return result.scalars().first()
    
    @staticmethod
    async def log_audit_event(
        session: AsyncSession,
        event_type: str,
        user_id: Optional[str] = None,
        wallet_address: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        status: str = "success",
        **kwargs
    ) -> AuditEvent:
        """Log compliance audit event."""
        event = AuditEvent(
            event_id=kwargs.get('event_id', f"{event_type}_{uuid4().hex[:12]}"),
            event_type=event_type,
            user_id=user_id,
            wallet_address=wallet_address,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            timestamp=datetime.utcnow(),
            **{k: v for k, v in kwargs.items() if k != 'event_id'}
        )
        
        session.add(event)
        await session.commit()
        await session.refresh(event)
        
        return event
    
    # ========================================================================
    # WALLET & USER METHODS
    # ========================================================================
    
    @staticmethod
    async def create_wallet(
        session: AsyncSession,
        address: str,
        username: str,
        is_artist: bool = False
    ) -> Wallet:
        """Create or get wallet."""
        # Check if wallet exists
        result = await session.execute(
            select(Wallet).where(Wallet.address == address)
        )
        existing = result.scalars().first()
        
        if existing:
            logger.warning(f"Wallet already exists: {address}")
            return existing
        
        wallet = Wallet(
            address=address,
            username=username,
            is_artist=is_artist,
            balance_dcmx=0
        )
        
        session.add(wallet)
        await session.commit()
        await session.refresh(wallet)
        
        logger.info(f"Wallet created: {address}")
        return wallet
    
    @staticmethod
    async def get_wallet(
        session: AsyncSession,
        address: str
    ) -> Optional[Wallet]:
        """Get wallet by address."""
        result = await session.execute(
            select(Wallet).where(Wallet.address == address)
        )
        return result.scalars().first()
    
    @staticmethod
    async def update_wallet_balance(
        session: AsyncSession,
        address: str,
        amount: float,
        operation: str = "add"
    ) -> Wallet:
        """Update wallet balance."""
        wallet = await DataAccessLayer.get_wallet(session, address)
        if not wallet:
            raise ValueError(f"Wallet not found: {address}")
        
        if operation == "add":
            wallet.balance_dcmx += amount
        elif operation == "subtract":
            wallet.balance_dcmx -= amount
        elif operation == "set":
            wallet.balance_dcmx = amount
        
        wallet.last_activity = datetime.utcnow()
        await session.commit()
        await session.refresh(wallet)
        
        return wallet
    
    # ========================================================================
    # NFT METHODS
    # ========================================================================
    
    @staticmethod
    async def create_nft(
        session: AsyncSession,
        nft_id: str,
        title: str,
        artist_wallet: str,
        price_dcmx: float,
        edition: int,
        max_editions: int,
        content_hash: str,
        **kwargs
    ) -> MusicNFT:
        """Create NFT record."""
        nft = MusicNFT(
            nft_id=nft_id,
            title=title,
            artist=kwargs.get('artist', ''),
            artist_wallet=artist_wallet,
            artist_username=kwargs.get('artist_username', ''),
            edition=edition,
            max_editions=max_editions,
            price_dcmx=price_dcmx,
            content_hash=content_hash,
            engagement_metrics=kwargs.get('engagement_metrics', {
                'average_completion': 0.0,
                'total_listens': 0,
                'skip_count': 0
            })
        )
        
        session.add(nft)
        await session.commit()
        await session.refresh(nft)
        
        logger.info(f"NFT created: {title} ({nft_id})")
        return nft
    
    @staticmethod
    async def get_nft(
        session: AsyncSession,
        nft_id: str
    ) -> Optional[MusicNFT]:
        """Get NFT by ID."""
        result = await session.execute(
            select(MusicNFT).where(MusicNFT.nft_id == nft_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def get_artist_nfts(
        session: AsyncSession,
        artist_wallet: str
    ) -> List[MusicNFT]:
        """Get all NFTs by artist."""
        result = await session.execute(
            select(MusicNFT).where(MusicNFT.artist_wallet == artist_wallet)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def record_nft_purchase(
        session: AsyncSession,
        nft_id: str,
        buyer_wallet: str,
        seller_wallet: str,
        price_dcmx: float,
        sale_type: str = "primary"
    ) -> NFTSale:
        """Record NFT purchase."""
        # Get NFT
        nft = await DataAccessLayer.get_nft(session, nft_id)
        if not nft:
            raise ValueError(f"NFT not found: {nft_id}")
        
        sale = NFTSale(
            nft_id=nft.id,
            sale_type=sale_type,
            seller_wallet=seller_wallet,
            buyer_wallet=buyer_wallet,
            price_dcmx=price_dcmx
        )
        
        session.add(sale)
        await session.commit()
        await session.refresh(sale)
        
        logger.info(f"NFT purchase recorded: {buyer_wallet} bought {nft_id}")
        return sale
    
    # ========================================================================
    # REWARD METHODS
    # ========================================================================
    
    @staticmethod
    async def create_listening_reward(
        session: AsyncSession,
        user_wallet: str,
        nft_id: str,
        listen_duration_seconds: int,
        completion_percentage: float,
        total_reward: float
    ) -> ListeningReward:
        """Record listening reward."""
        reward = ListeningReward(
            user_wallet=user_wallet,
            nft_id=nft_id,
            listen_duration_seconds=listen_duration_seconds,
            completion_percentage=completion_percentage,
            base_reward=total_reward,
            total_reward=total_reward
        )
        
        session.add(reward)
        await session.commit()
        await session.refresh(reward)
        
        return reward
    
    @staticmethod
    async def create_voting_record(
        session: AsyncSession,
        user_wallet: str,
        nft_id: str,
        preference: str,
        reward_tokens: float = 0
    ) -> VotingRecord:
        """Record user vote on song."""
        vote = VotingRecord(
            user_wallet=user_wallet,
            nft_id=nft_id,
            preference=preference,
            reward_tokens=reward_tokens
        )
        
        session.add(vote)
        await session.commit()
        await session.refresh(vote)
        
        return vote
    
    @staticmethod
    async def create_skip_record(
        session: AsyncSession,
        user_wallet: str,
        nft_id: str,
        completion_percentage: float,
        charge_applied: float = 0
    ) -> SkipRecord:
        """Record skip activity."""
        skip = SkipRecord(
            user_wallet=user_wallet,
            nft_id=nft_id,
            completion_percentage=completion_percentage,
            charge_applied=charge_applied
        )
        
        session.add(skip)
        await session.commit()
        await session.refresh(skip)
        
        return skip
    
    # ========================================================================
    # TRANSACTION METHODS
    # ========================================================================
    
    @staticmethod
    async def create_transaction(
        session: AsyncSession,
        from_wallet: str,
        to_wallet: str,
        amount_dcmx: float,
        transaction_type: str,
        **kwargs
    ) -> Transaction:
        """Create transaction record."""
        transaction = Transaction(
            transaction_id=kwargs.get('transaction_id', f"tx_{uuid4().hex}"),
            from_wallet=from_wallet,
            to_wallet=to_wallet,
            amount_dcmx=amount_dcmx,
            transaction_type=transaction_type,
            status=kwargs.get('status', 'completed'),
            blockchain_hash=kwargs.get('blockchain_hash'),
            blockchain=kwargs.get('blockchain', 'polygon'),
            metadata=kwargs.get('metadata', {})
        )
        
        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        
        return transaction
    
    @staticmethod
    async def get_user_transactions(
        session: AsyncSession,
        wallet_address: str,
        limit: int = 100
    ) -> List[Transaction]:
        """Get user transaction history."""
        result = await session.execute(
            select(Transaction).where(
                or_(
                    Transaction.from_wallet == wallet_address,
                    Transaction.to_wallet == wallet_address
                )
            ).order_by(desc(Transaction.created_at)).limit(limit)
        )
        return list(result.scalars().all())
    
    # ========================================================================
    # ANALYTICS METHODS
    # ========================================================================
    
    @staticmethod
    async def get_platform_stats(session: AsyncSession) -> Dict[str, Any]:
        """Get platform-wide statistics."""
        # Total wallets
        total_wallets_result = await session.execute(select(func.count(Wallet.id)))
        total_wallets = total_wallets_result.scalar()
        
        # Total artists
        total_artists_result = await session.execute(
            select(func.count(Wallet.id)).where(Wallet.is_artist == True)
        )
        total_artists = total_artists_result.scalar()
        
        # Total NFTs
        total_nfts_result = await session.execute(select(func.count(MusicNFT.id)))
        total_nfts = total_nfts_result.scalar()
        
        # Total votes
        total_votes_result = await session.execute(select(func.count(VotingRecord.id)))
        total_votes = total_votes_result.scalar()
        
        # Total skips
        total_skips_result = await session.execute(select(func.count(SkipRecord.id)))
        total_skips = total_skips_result.scalar()
        
        # Total platform balance
        total_balance_result = await session.execute(select(func.sum(Wallet.balance_dcmx)))
        total_balance = total_balance_result.scalar() or 0
        
        return {
            'total_users': total_wallets,
            'total_artists': total_artists,
            'total_nfts': total_nfts,
            'total_votes': total_votes,
            'total_skips': total_skips,
            'total_platform_balance_dcmx': float(total_balance)
        }
    
    @staticmethod
    async def get_artist_earnings(
        session: AsyncSession,
        artist_wallet: str
    ) -> Dict[str, Any]:
        """Get artist earnings summary."""
        # Get artist wallet
        wallet = await DataAccessLayer.get_wallet(session, artist_wallet)
        if not wallet:
            raise ValueError(f"Artist wallet not found: {artist_wallet}")
        
        # Get artist NFTs
        nfts = await DataAccessLayer.get_artist_nfts(session, artist_wallet)
        
        # Calculate total sales
        total_sales = sum(nft.price_dcmx for nft in nfts)
        
        return {
            'artist': artist_wallet,
            'username': wallet.username,
            'nfts_created': len(nfts),
            'total_sales_dcmx': float(total_sales),
            'current_balance_dcmx': float(wallet.balance_dcmx),
            'songs': [
                {
                    'id': nft.nft_id,
                    'title': nft.title,
                    'price': float(nft.price_dcmx),
                    'edition': f"{nft.edition}/{nft.max_editions}",
                    'likes': nft.likes,
                    'dislikes': nft.dislikes,
                    'listeners': nft.listeners
                }
                for nft in nfts
            ]
        }
    
    @staticmethod
    async def get_user_votes(
        session: AsyncSession,
        user_wallet: str,
        limit: int = 100
    ) -> List[VotingRecord]:
        """Get user voting history."""
        result = await session.execute(
            select(VotingRecord).where(
                VotingRecord.user_wallet == user_wallet
            ).order_by(desc(VotingRecord.voted_at)).limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_user_profile_stats(
        session: AsyncSession,
        user_wallet: str
    ) -> Dict[str, Any]:
        """Get user profile and statistics."""
        wallet = await DataAccessLayer.get_wallet(session, user_wallet)
        if not wallet:
            raise ValueError(f"User wallet not found: {user_wallet}")
        
        # Get votes
        votes = await DataAccessLayer.get_user_votes(session, user_wallet, limit=1000)
        likes_count = sum(1 for v in votes if v.preference == "like")
        dislikes_count = sum(1 for v in votes if v.preference == "dislike")
        total_rewards = sum(v.reward_tokens for v in votes)
        
        # Get skips
        skips_result = await session.execute(
            select(SkipRecord).where(SkipRecord.user_wallet == user_wallet)
        )
        skips = list(skips_result.scalars().all())
        total_charges = sum(s.charge_applied for s in skips if s.charge_applied < 0)
        
        return {
            'wallet': user_wallet,
            'username': wallet.username,
            'balance_dcmx': float(wallet.balance_dcmx),
            'is_artist': wallet.is_artist,
            'statistics': {
                'votes_cast': len(votes),
                'likes': likes_count,
                'dislikes': dislikes_count,
                'songs_skipped': len(skips),
                'total_rewards_earned': float(total_rewards),
                'total_skip_charges': float(abs(total_charges)),
                'net_earnings': float(total_rewards + total_charges)
            }
        }
