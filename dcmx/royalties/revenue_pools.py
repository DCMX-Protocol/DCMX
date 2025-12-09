"""
Revenue Sharing Pools and Collective Economics for DCMX.

Implements:
- Artist collectives (groups pool resources)
- Revenue sharing pools (distribute earnings fairly)
- Collaboration royalties (split payments between artists)
- Governance pools (community treasuries)
- Referral networks (earn from network effects)
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class PoolType(Enum):
    """Types of revenue pools."""
    ARTIST_COLLECTIVE = "artist_collective"
    COLLABORATION = "collaboration"
    GOVERNANCE = "governance"
    REFERRAL_NETWORK = "referral_network"


@dataclass
class PoolMember:
    """Member of a revenue pool."""
    wallet: str
    share_percentage: float  # 0-100
    join_date: str
    contribution_usd: float = 0.0
    rewards_earned: float = 0.0
    is_active: bool = True


@dataclass
class RevenuePool:
    """
    Revenue sharing pool for artists, collectives, or networks.
    
    Pool collects earnings and distributes them to members
    based on pre-defined share percentages.
    """
    pool_id: str
    pool_name: str
    pool_type: PoolType
    
    # Pool management
    creator_wallet: str
    creation_date: str
    is_active: bool = True
    
    # Members (wallet → share %)
    members: Dict[str, PoolMember] = field(default_factory=dict)
    
    # Finances
    total_balance: float = 0.0
    total_distributed: float = 0.0
    distribution_history: List[Dict] = field(default_factory=list)
    
    # Rules
    min_payout_threshold: float = 1.0  # Minimum balance to trigger distribution
    distribution_frequency_days: int = 30  # Distribute every 30 days
    last_distribution_date: Optional[str] = None
    
    def add_member(
        self,
        wallet: str,
        share_percentage: float,
        contribution: float = 0.0
    ) -> PoolMember:
        """Add member to pool."""
        if sum(m.share_percentage for m in self.members.values()) + share_percentage > 100:
            raise ValueError("Total share percentage would exceed 100%")
        
        member = PoolMember(
            wallet=wallet,
            share_percentage=share_percentage,
            join_date=datetime.utcnow().isoformat(),
            contribution_usd=contribution
        )
        
        self.members[wallet] = member
        logger.info(f"Member {wallet[:20]}... added to {self.pool_name} ({share_percentage}% share)")
        
        return member
    
    def deposit(self, amount_dcmx: float) -> None:
        """Add funds to pool."""
        self.total_balance += amount_dcmx
        logger.info(f"Pool {self.pool_name} received {amount_dcmx:.2f} DCMX (balance: {self.total_balance:.2f})")
    
    def distribute_earnings(self) -> Dict[str, float]:
        """
        Distribute current pool balance to members based on shares.
        
        Returns: Dict of wallet → amount distributed
        """
        if self.total_balance < self.min_payout_threshold:
            logger.warning(f"Pool {self.pool_name} balance {self.total_balance:.2f} below threshold {self.min_payout_threshold}")
            return {}
        
        distribution = {}
        
        for wallet, member in self.members.items():
            if not member.is_active:
                continue
            
            amount = self.total_balance * (member.share_percentage / 100.0)
            distribution[wallet] = amount
            member.rewards_earned += amount
        
        # Record distribution
        self.distribution_history.append({
            "date": datetime.utcnow().isoformat(),
            "total_amount": self.total_balance,
            "distribution": distribution
        })
        
        # Reset balance
        self.total_distributed += self.total_balance
        self.total_balance = 0.0
        self.last_distribution_date = datetime.utcnow().isoformat()
        
        logger.info(f"Pool {self.pool_name} distributed {self.total_distributed:.2f} DCMX total")
        
        return distribution
    
    def get_member_stats(self, wallet: str) -> Dict:
        """Get statistics for a pool member."""
        if wallet not in self.members:
            return None
        
        member = self.members[wallet]
        
        return {
            "wallet": wallet,
            "pool": self.pool_name,
            "share_percentage": member.share_percentage,
            "join_date": member.join_date,
            "contribution": member.contribution_usd,
            "rewards_earned": member.rewards_earned,
            "is_active": member.is_active,
        }
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return asdict(self)


@dataclass
class Collaboration:
    """
    Multi-artist collaboration with shared revenue.
    
    When multiple artists work together, earnings are split
    according to agreed percentages.
    """
    collaboration_id: str
    name: str
    description: str
    
    # Collaborators
    collaborators: Dict[str, float] = field(default_factory=dict)  # wallet → share %
    
    # Release info
    release_date: str = ""
    song_content_hash: str = ""
    
    # Finances
    total_revenue: float = 0.0
    distributions: List[Dict] = field(default_factory=list)
    
    def add_collaborator(self, wallet: str, share_percentage: float) -> None:
        """Add collaborator to project."""
        if sum(self.collaborators.values()) + share_percentage > 100:
            raise ValueError("Total shares exceed 100%")
        
        self.collaborators[wallet] = share_percentage
        logger.info(f"Collaborator {wallet[:20]}... added with {share_percentage}% share")
    
    def record_revenue(self, amount_dcmx: float) -> None:
        """Record revenue from the collaboration."""
        self.total_revenue += amount_dcmx
        logger.info(f"Collaboration {self.name} earned {amount_dcmx:.2f} DCMX")
    
    def distribute_revenue(self, amount_dcmx: float) -> Dict[str, float]:
        """Distribute specific amount according to shares."""
        distribution = {}
        
        for wallet, share in self.collaborators.items():
            payout = amount_dcmx * (share / 100.0)
            distribution[wallet] = payout
        
        self.distributions.append({
            "date": datetime.utcnow().isoformat(),
            "amount": amount_dcmx,
            "breakdown": distribution
        })
        
        return distribution


@dataclass
class ReferralNetwork:
    """
    Affiliate/referral network where users earn from referrals.
    
    User A refers User B → User A earns commission from User B's activities.
    """
    network_id: str
    creator_wallet: str
    creation_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Network structure
    nodes: Dict[str, Set[str]] = field(default_factory=dict)  # wallet → set of referrals
    
    # Commission structure
    direct_commission: float = 5.0  # 5% of referred user's purchases
    indirect_commission: float = 2.0  # 2% from referred user's referrals
    
    # Stats
    total_members: int = 0
    total_commissions_paid: float = 0.0
    
    def add_referral(self, referrer_wallet: str, referred_wallet: str) -> None:
        """Record a referral relationship."""
        if referrer_wallet not in self.nodes:
            self.nodes[referrer_wallet] = set()
        
        self.nodes[referrer_wallet].add(referred_wallet)
        self.total_members += 1
        
        logger.info(f"Referral network: {referrer_wallet[:20]}... → {referred_wallet[:20]}...")
    
    def calculate_commission(
        self,
        referrer_wallet: str,
        purchase_amount: float,
        generation: int = 1
    ) -> float:
        """
        Calculate commission for a purchase in referral network.
        
        Generation 1 (direct): 5%
        Generation 2 (indirect): 2%
        Generation 3+: 0%
        """
        if generation == 1:
            commission = purchase_amount * (self.direct_commission / 100.0)
        elif generation == 2:
            commission = purchase_amount * (self.indirect_commission / 100.0)
        else:
            commission = 0.0
        
        self.total_commissions_paid += commission
        return commission
    
    def get_network_size(self, wallet: str, depth: int = 2) -> int:
        """Get size of network under a wallet (up to specified depth)."""
        if wallet not in self.nodes:
            return 0
        
        if depth == 1:
            return len(self.nodes[wallet])
        
        # Recursive count
        count = len(self.nodes[wallet])
        for referral in self.nodes[wallet]:
            count += self.get_network_size(referral, depth - 1)
        
        return count


class RevenuePoolManager:
    """
    Manages revenue pools, collaborations, and referral networks.
    
    Handles distribution of earnings across complex structures.
    """
    
    def __init__(self):
        """Initialize pool manager."""
        self.pools: Dict[str, RevenuePool] = {}
        self.collaborations: Dict[str, Collaboration] = {}
        self.referral_networks: Dict[str, ReferralNetwork] = {}
        
        logger.info("RevenuePoolManager initialized")
    
    # ==================== POOLS ====================
    
    def create_pool(
        self,
        pool_name: str,
        pool_type: PoolType,
        creator_wallet: str
    ) -> RevenuePool:
        """Create a new revenue pool."""
        pool_id = f"pool_{pool_name.replace(' ', '_')}_{datetime.utcnow().timestamp()}"
        
        pool = RevenuePool(
            pool_id=pool_id,
            pool_name=pool_name,
            pool_type=pool_type,
            creator_wallet=creator_wallet,
            creation_date=datetime.utcnow().isoformat(),
        )
        
        self.pools[pool_id] = pool
        logger.info(f"Pool created: {pool_name} ({pool_type.value})")
        
        return pool
    
    def add_pool_member(
        self,
        pool_id: str,
        wallet: str,
        share_percentage: float
    ) -> PoolMember:
        """Add member to an existing pool."""
        pool = self.pools[pool_id]
        return pool.add_member(wallet, share_percentage)
    
    def distribute_pool(self, pool_id: str) -> Dict[str, float]:
        """Trigger distribution for a pool."""
        pool = self.pools[pool_id]
        return pool.distribute_earnings()
    
    def get_pool_report(self, pool_id: str) -> Dict:
        """Get full report for a pool."""
        pool = self.pools[pool_id]
        
        return {
            "pool_id": pool.pool_id,
            "name": pool.pool_name,
            "type": pool.pool_type.value,
            "current_balance": pool.total_balance,
            "total_distributed": pool.total_distributed,
            "member_count": len([m for m in pool.members.values() if m.is_active]),
            "members": {
                wallet: {
                    "share": member.share_percentage,
                    "rewards": member.rewards_earned
                }
                for wallet, member in pool.members.items()
            }
        }
    
    # ==================== COLLABORATIONS ====================
    
    def create_collaboration(
        self,
        name: str,
        description: str,
        lead_artist_wallet: str
    ) -> Collaboration:
        """Create multi-artist collaboration."""
        collab_id = f"collab_{name.replace(' ', '_')}_{datetime.utcnow().timestamp()}"
        
        collab = Collaboration(
            collaboration_id=collab_id,
            name=name,
            description=description,
        )
        
        collab.add_collaborator(lead_artist_wallet, 0)  # Lead artist added without share initially
        
        self.collaborations[collab_id] = collab
        logger.info(f"Collaboration created: {name}")
        
        return collab
    
    def add_collaborator(
        self,
        collab_id: str,
        wallet: str,
        share_percentage: float
    ) -> None:
        """Add collaborator to project."""
        collab = self.collaborations[collab_id]
        collab.add_collaborator(wallet, share_percentage)
    
    def process_collaboration_sale(
        self,
        collab_id: str,
        sale_price_dcmx: float
    ) -> Dict[str, float]:
        """Process NFT sale for a collaboration."""
        collab = self.collaborations[collab_id]
        return collab.distribute_revenue(sale_price_dcmx)
    
    # ==================== REFERRAL NETWORKS ====================
    
    def create_referral_network(self, creator_wallet: str) -> ReferralNetwork:
        """Create new referral network."""
        network_id = f"network_{datetime.utcnow().timestamp()}"
        
        network = ReferralNetwork(
            network_id=network_id,
            creator_wallet=creator_wallet,
        )
        
        self.referral_networks[network_id] = network
        logger.info(f"Referral network created by {creator_wallet[:20]}...")
        
        return network
    
    def add_referral(self, network_id: str, referrer: str, referred: str) -> None:
        """Record referral in network."""
        network = self.referral_networks[network_id]
        network.add_referral(referrer, referred)
    
    def get_referral_commission(
        self,
        network_id: str,
        referrer_wallet: str,
        purchase_amount: float,
        generation: int = 1
    ) -> float:
        """Calculate referral commission for a purchase."""
        network = self.referral_networks[network_id]
        return network.calculate_commission(referrer_wallet, purchase_amount, generation)


if __name__ == "__main__":
    import json
    
    manager = RevenuePoolManager()
    
    # Example 1: Artist Collective
    print("\n=== ARTIST COLLECTIVE POOL ===")
    collective = manager.create_pool(
        pool_name="Jazz Collective",
        pool_type=PoolType.ARTIST_COLLECTIVE,
        creator_wallet="0xLeadArtist"
    )
    
    manager.add_pool_member(collective.pool_id, "0xArtist1", 40.0)
    manager.add_pool_member(collective.pool_id, "0xArtist2", 35.0)
    manager.add_pool_member(collective.pool_id, "0xArtist3", 25.0)
    
    collective.deposit(100.0)  # 100 DCMX in collective pool
    distribution = manager.distribute_pool(collective.pool_id)
    
    print("Distribution:")
    for wallet, amount in distribution.items():
        print(f"  {wallet[:20]}... receives {amount:.2f} DCMX")
    
    # Example 2: Collaboration
    print("\n=== COLLABORATION ===")
    collab = manager.create_collaboration(
        name="Summer Hit",
        description="Collaboration between 3 artists",
        lead_artist_wallet="0xArtist1"
    )
    
    manager.add_collaborator(collab.collaboration_id, "0xArtist1", 50.0)
    manager.add_collaborator(collab.collaboration_id, "0xArtist2", 30.0)
    manager.add_collaborator(collab.collaboration_id, "0xProducer", 20.0)
    
    splits = manager.process_collaboration_sale(collab.collaboration_id, 50.0)
    print("Sale splits:")
    for wallet, amount in splits.items():
        print(f"  {wallet[:20]}... receives {amount:.2f} DCMX")
    
    # Example 3: Referral Network
    print("\n=== REFERRAL NETWORK ===")
    network = manager.create_referral_network("0xNetworkCreator")
    
    manager.add_referral(network.network_id, "0xInfluencer1", "0xNewUser1")
    manager.add_referral(network.network_id, "0xInfluencer1", "0xNewUser2")
    manager.add_referral(network.network_id, "0xNewUser1", "0xNewUser3")
    
    commission = manager.get_referral_commission(
        network.network_id,
        "0xInfluencer1",
        100.0  # New user spends 100 DCMX
    )
    
    print(f"Commission for influencer: {commission:.2f} DCMX")
    print(f"Indirect commission from new user1's referral: {manager.get_referral_commission(network.network_id, '0xInfluencer1', 50.0, generation=2):.2f} DCMX")
