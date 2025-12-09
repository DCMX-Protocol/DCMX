"""
DCMX LoRa Mesh Networking Layer

Peer-to-peer content distribution via LoRa mesh network.
- Geographic routing (proximity-based neighbor discovery)
- Bandwidth-based incentives (node operators rewarded)
- Content addressable storage (IPFS-style hashing)
"""

import logging
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of LoRa mesh nodes."""
    LISTENER = "listener"  # User node (mobile)
    RELAY = "relay"  # Routing node
    CONTENT_PROVIDER = "content_provider"  # Artist/seeder node
    GATEWAY = "gateway"  # Internet bridge


class RouteQuality(Enum):
    """Signal quality indicators."""
    EXCELLENT = 5  # SNR > 10dB
    GOOD = 4       # SNR 5-10dB
    FAIR = 3       # SNR 0-5dB
    POOR = 2       # SNR -10-0dB
    VERY_POOR = 1  # SNR < -10dB


@dataclass
class GeoLocation:
    """Geographic coordinates for routing."""
    latitude: float
    longitude: float
    altitude_meters: Optional[float] = None
    
    def distance_to(self, other: "GeoLocation") -> float:
        """Calculate distance in meters (Haversine formula)."""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c


@dataclass
class LoRaSignal:
    """LoRa signal quality metrics."""
    rssi: int  # Received signal strength (-120 to -30 dBm)
    snr: float  # Signal-to-noise ratio (dB)
    spreading_factor: int = 12  # 7-12 (lower = faster, less range)
    frequency_mhz: float = 915.0  # ISM band
    
    def get_quality(self) -> RouteQuality:
        """Get signal quality."""
        if self.snr > 10:
            return RouteQuality.EXCELLENT
        elif self.snr > 5:
            return RouteQuality.GOOD
        elif self.snr > 0:
            return RouteQuality.FAIR
        elif self.snr > -10:
            return RouteQuality.POOR
        else:
            return RouteQuality.VERY_POOR


@dataclass
class ContentBlock:
    """Content block for distributed storage."""
    content_hash: str  # SHA-256 of content
    block_number: int  # Block index in sequence
    total_blocks: int  # Total blocks in file
    data: bytes  # Actual content
    size_bytes: int = 0
    
    def __post_init__(self):
        self.size_bytes = len(self.data) if self.data else 0


@dataclass
class LoRaNode:
    """LoRa mesh network node."""
    node_id: str
    node_type: NodeType
    location: GeoLocation
    wallet_address: str
    
    # Network identity
    peers: Dict[str, "LoRaNode"] = field(default_factory=dict)  # node_id -> Node
    signal_quality: Dict[str, LoRaSignal] = field(default_factory=dict)  # node_id -> Signal
    
    # Content storage
    content_store: Dict[str, List[ContentBlock]] = field(default_factory=dict)  # content_hash -> blocks
    
    # Statistics
    messages_sent: int = 0
    messages_received: int = 0
    bytes_served: int = 0
    bytes_received: int = 0
    
    # Timing
    last_seen: str = ""
    uptime_seconds: float = 0.0
    start_time: str = ""
    
    def __post_init__(self):
        self.last_seen = datetime.utcnow().isoformat()
        self.start_time = datetime.utcnow().isoformat()


@dataclass
class BandwidthReward:
    """Reward earned by node for bandwidth contribution."""
    node_id: str
    period_start: str
    period_end: str
    bytes_served: int
    uptime_percentage: float
    unique_peers_served: int
    reward_tokens_dcmx: float = 0.0
    
    def calculate_reward(self) -> float:
        """
        Calculate token reward based on contribution.
        
        Formula:
        - Base: 10 tokens
        - Bandwidth bonus: bytes_served / 100MB * 1 token
        - Uptime bonus: uptime_percentage * 0.2 tokens
        - Peer diversity: unique_peers_served / 10 * 0.1 tokens
        """
        base = 10.0
        bandwidth_bonus = (self.bytes_served / (100 * 1024**2)) * 1.0
        uptime_bonus = self.uptime_percentage * 0.2
        diversity_bonus = min(self.unique_peers_served / 10, 1.0) * 0.1
        
        self.reward_tokens_dcmx = base + bandwidth_bonus + uptime_bonus + diversity_bonus
        return self.reward_tokens_dcmx


class LoRaMeshNetwork:
    """
    LoRa mesh network coordinator.
    
    Responsibilities:
    - Peer discovery (geographic proximity)
    - Route finding (AODV-like algorithm)
    - Content distribution (IPFS-style blocks)
    - Bandwidth tracking and incentives
    """
    
    def __init__(self):
        """Initialize mesh network."""
        self.nodes: Dict[str, LoRaNode] = {}
        self.routing_table: Dict[str, List[str]] = {}  # destination -> [hops]
        self.bandwidth_history: List[Dict] = []
    
    async def register_node(
        self,
        node_id: str,
        node_type: NodeType,
        location: GeoLocation,
        wallet_address: str,
    ) -> LoRaNode:
        """Register node in mesh network."""
        node = LoRaNode(
            node_id=node_id,
            node_type=node_type,
            location=location,
            wallet_address=wallet_address,
        )
        
        self.nodes[node_id] = node
        logger.info(f"Node registered: {node_id} ({node_type.value}) at ({location.latitude}, {location.longitude})")
        
        # Discover nearby peers
        await self.discover_peers(node_id)
        
        return node
    
    async def discover_peers(
        self,
        node_id: str,
        max_distance_km: float = 5.0,
    ):
        """Discover peers within range."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        max_distance_m = max_distance_km * 1000
        
        for other_id, other_node in self.nodes.items():
            if other_id == node_id:
                continue
            
            distance = node.location.distance_to(other_node.location)
            
            if distance <= max_distance_m:
                # Peer is in range
                node.peers[other_id] = other_node
                
                # Simulate signal quality
                # Closer = better signal
                rssi = -30 - int((distance / max_distance_m) * 90)  # -30 to -120 dBm
                snr = 10 - (distance / max_distance_m) * 20  # 10 to -10 dB
                
                node.signal_quality[other_id] = LoRaSignal(
                    rssi=rssi,
                    snr=snr,
                )
                
                logger.info(f"Peer discovered: {node_id} -> {other_id} ({distance/1000:.1f}km, {node.signal_quality[other_id].get_quality().name})")
    
    async def find_route(
        self,
        source_node_id: str,
        destination_node_id: str,
        max_hops: int = 5,
    ) -> Optional[List[str]]:
        """
        Find route to destination using AODV-like algorithm.
        
        Returns: [source, hop1, hop2, ..., destination]
        """
        if source_node_id not in self.nodes:
            raise ValueError(f"Source node {source_node_id} not found")
        
        if destination_node_id not in self.nodes:
            raise ValueError(f"Destination node {destination_node_id} not found")
        
        # BFS to find shortest path
        from collections import deque
        
        queue = deque([(source_node_id, [source_node_id])])
        visited = {source_node_id}
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_hops:
                continue
            
            if current == destination_node_id:
                return path
            
            current_node = self.nodes[current]
            
            for peer_id in current_node.peers:
                if peer_id not in visited:
                    visited.add(peer_id)
                    queue.append((peer_id, path + [peer_id]))
        
        return None
    
    async def store_content(
        self,
        node_id: str,
        content_hash: str,
        blocks: List[ContentBlock],
    ):
        """Store content blocks on node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        node.content_store[content_hash] = blocks
        
        total_size = sum(block.size_bytes for block in blocks)
        logger.info(f"Content stored: {node_id} storing {content_hash[:16]}... ({total_size} bytes, {len(blocks)} blocks)")
    
    async def retrieve_content(
        self,
        node_id: str,
        content_hash: str,
    ) -> Optional[bytes]:
        """Retrieve content from node."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        
        if content_hash not in node.content_store:
            return None
        
        blocks = node.content_store[content_hash]
        content = b"".join(block.data for block in sorted(blocks, key=lambda b: b.block_number))
        
        node.bytes_served += len(content)
        logger.info(f"Content retrieved: {node_id} serving {content_hash[:16]}... ({len(content)} bytes)")
        
        return content
    
    async def distribute_content(
        self,
        source_node_id: str,
        content_hash: str,
        content_data: bytes,
        block_size: int = 250,  # 250 bytes per block (LoRa limit)
    ):
        """
        Distribute content across mesh network.
        
        Splits content into blocks and sends to nearby high-capacity nodes.
        """
        if source_node_id not in self.nodes:
            raise ValueError(f"Source node {source_node_id} not found")
        
        source_node = self.nodes[source_node_id]
        
        # Split into blocks
        blocks = []
        total_blocks = (len(content_data) + block_size - 1) // block_size
        
        for i in range(total_blocks):
            start = i * block_size
            end = min(start + block_size, len(content_data))
            
            block = ContentBlock(
                content_hash=content_hash,
                block_number=i,
                total_blocks=total_blocks,
                data=content_data[start:end],
            )
            blocks.append(block)
        
        # Store locally
        await self.store_content(source_node_id, content_hash, blocks)
        
        # Distribute to peers (prioritize high-quality connections)
        sorted_peers = sorted(
            source_node.peers.items(),
            key=lambda x: source_node.signal_quality[x[0]].snr,
            reverse=True
        )
        
        for peer_id, peer_node in sorted_peers[:3]:  # Replicate to 3 best peers
            await self.store_content(peer_id, content_hash, blocks)
            logger.info(f"Content replicated: {source_node_id} -> {peer_id}")
    
    async def record_bandwidth(
        self,
        node_id: str,
        bytes_served: int,
        bytes_received: int,
    ):
        """Record bandwidth usage."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
        
        node = self.nodes[node_id]
        node.bytes_served += bytes_served
        node.bytes_received += bytes_received
        
        self.bandwidth_history.append({
            "node_id": node_id,
            "timestamp": datetime.utcnow().isoformat(),
            "bytes_served": bytes_served,
            "bytes_received": bytes_received,
        })
    
    async def calculate_rewards(
        self,
        period_hours: int = 24,
    ) -> Dict[str, BandwidthReward]:
        """Calculate rewards for all nodes."""
        rewards = {}
        now = datetime.utcnow()
        period_start = (now - timedelta(hours=period_hours)).isoformat()
        period_end = now.isoformat()
        
        for node_id, node in self.nodes.items():
            # Calculate uptime
            start_time = datetime.fromisoformat(node.start_time)
            uptime = (now - start_time).total_seconds()
            uptime_percentage = min(uptime / (period_hours * 3600), 1.0)
            
            # Calculate unique peers
            unique_peers = len(node.peers)
            
            reward = BandwidthReward(
                node_id=node_id,
                period_start=period_start,
                period_end=period_end,
                bytes_served=node.bytes_served,
                uptime_percentage=uptime_percentage,
                unique_peers_served=unique_peers,
            )
            reward.calculate_reward()
            
            rewards[node_id] = reward
            
            logger.info(f"Reward calculated: {node_id} earning {reward.reward_tokens_dcmx:.2f} DCMX")
        
        return rewards
    
    def get_network_stats(self) -> Dict:
        """Get network statistics."""
        total_nodes = len(self.nodes)
        total_content = sum(len(n.content_store) for n in self.nodes.values())
        total_bytes_served = sum(n.bytes_served for n in self.nodes.values())
        total_bytes_received = sum(n.bytes_received for n in self.nodes.values())
        
        nodes_by_type = {}
        for node in self.nodes.values():
            type_name = node.node_type.value
            nodes_by_type[type_name] = nodes_by_type.get(type_name, 0) + 1
        
        return {
            "total_nodes": total_nodes,
            "nodes_by_type": nodes_by_type,
            "total_content_items": total_content,
            "total_bytes_served": total_bytes_served,
            "total_bytes_received": total_bytes_received,
            "bandwidth_history_entries": len(self.bandwidth_history),
        }
