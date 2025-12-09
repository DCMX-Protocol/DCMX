"""LoRa-enabled node for DCMX mesh network with Zero-Knowledge Security."""

import logging
import secrets
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from dcmx.core.node import Node
from dcmx.lora.zk_proofs import (
    ZKProofGenerator, ZKProofVerifier,
    BandwidthProof, UptimeProof, ProximityProof,
    FreshnessProof, UniquenessProof
)
from dcmx.lora.secure_messaging import (
    SecureLoRaMessaging, SecureMessage, PeerSecurityContext
)


logger = logging.getLogger(__name__)


@dataclass
class LoRaPeer:
    """Peer accessible over LoRa mesh."""
    peer_id: str
    latitude: float
    longitude: float
    bandwidth_available_mbps: float
    uptime_percentage: float
    distance_meters: Optional[float] = None


@dataclass
class BandwidthStats:
    """Bandwidth statistics for reward calculation."""
    node_id: str
    bytes_uploaded: int = 0  # Data served
    bytes_downloaded: int = 0  # Data received
    uptime_seconds: float = 0.0  # Online time
    unique_peers_served: int = 0  # Diversity metric
    geographic_region: str = ""  # Region for bonuses
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    
    def get_reward_score(self) -> float:
        """
        Calculate reward score based on metrics.
        
        Returns:
            Weighted score for this period
        """
        # Normalize metrics
        uptime_factor = self.uptime_seconds / (24 * 3600)  # % of day
        bandwidth_factor = min(self.bytes_uploaded / (100 * 1024**2), 1.0)  # % of 100MB
        diversity_factor = min(self.unique_peers_served / 50, 1.0)  # Diversity bonus
        
        # Weighted average
        score = (
            uptime_factor * 0.5 +
            bandwidth_factor * 0.3 +
            diversity_factor * 0.2
        )
        
        return score


class LoRaNode(Node):
    """
    Node extended with LoRa mesh network capability and zero-knowledge security.
    
    Handles:
    - LoRa radio communication
    - Geographic mesh routing
    - Bandwidth accounting
    - Reward distribution for network participation
    - Zero-knowledge proof authentication
    - Secure peer-to-peer messaging
    - Sybil attack prevention
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        data_dir: Optional[Path] = None,
        lora_device: str = "/dev/ttyUSB0",
        bandwidth_limit_mbps: float = 5.0,
        latitude: float = 0.0,
        longitude: float = 0.0,
    ):
        """
        Initialize LoRa-enabled node with ZK security.
        
        Args:
            host: HTTP server host
            port: HTTP server port
            data_dir: Data directory
            lora_device: LoRa modem device path
            bandwidth_limit_mbps: Bandwidth rate limit
            latitude: Node geographic latitude
            longitude: Node geographic longitude
        """
        super().__init__(host, port, data_dir)
        
        self.lora_device = lora_device
        self.bandwidth_limit = bandwidth_limit_mbps
        self.latitude = latitude
        self.longitude = longitude
        
        # LoRa-specific state
        self.mesh_peers: Dict[str, LoRaPeer] = {}
        self.routing_table: Dict[str, list] = {}  # peer_id -> route hops
        self.bandwidth_stats = BandwidthStats(node_id=self.peer.peer_id)
        
        # Zero-Knowledge Security
        node_secret_key = secrets.token_bytes(32)
        self.zk_generator = ZKProofGenerator(self.peer.peer_id, node_secret_key)
        
        self.secure_messaging = SecureLoRaMessaging(
            self.peer.peer_id,
            node_secret_key
        )
        
        # Track ZK proofs for this node
        self.bandwidth_proofs: List[BandwidthProof] = []
        self.uptime_proofs: List[UptimeProof] = []
        self.proximity_proof: Optional[ProximityProof] = None
        self.uniqueness_proof: Optional[UniquenessProof] = None
        
        logger.info(
            f"LoRaNode initialized at ({latitude}, {longitude}) with ZK security"
        )
    
    async def broadcast_content(self, track_hash: str) -> None:
        """
        Broadcast track availability to mesh neighbors with ZK proof.
        
        Args:
            track_hash: Hash of available track
        """
        try:
            # Generate freshness proof to prevent replay attacks
            freshness_proof = self.zk_generator.generate_freshness_proof(
                message=f"broadcast:{track_hash}",
                nonce_depth=5
            )
            
            message_data = {
                "type": "content_broadcast",
                "track_hash": track_hash,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # TODO: Implement LoRa broadcast
            # 1. Encrypt message with secure_messaging
            # 2. Attach ZK freshness proof
            # 3. Compress for LoRa payload
            # 4. Send over LoRa radio to nearby nodes
            # 5. Handle retries and ACKs
            
            logger.info(
                f"Broadcast content {track_hash} with freshness proof "
                f"(nonce_depth={len(freshness_proof.nonce_chain)})"
            )
        except Exception as e:
            logger.error(f"Failed to broadcast content: {e}")
    
    async def broadcast_bandwidth_proof(
        self,
        content_hashes: List[str],
        bytes_served: int
    ) -> None:
        """
        Broadcast bandwidth contribution proof to network.
        
        Proves bytes served without revealing content details.
        
        Args:
            content_hashes: Hashes of content served
            bytes_served: Total bytes transmitted
        """
        try:
            # Generate bandwidth proof
            bw_proof = self.zk_generator.generate_bandwidth_proof(
                bytes_served=bytes_served,
                content_hashes=content_hashes,
                challenge_count=5
            )
            
            self.bandwidth_proofs.append(bw_proof)
            
            # TODO: Broadcast to reward verifiers
            # 1. Serialize proof with ZK commitment
            # 2. Send to designated verifier nodes
            # 3. Collect verification responses
            # 4. Submit to blockchain for reward calculation
            
            logger.info(
                f"Generated bandwidth proof: {bytes_served} bytes, "
                f"merkle_root={bw_proof.merkle_root[:16]}"
            )
        except Exception as e:
            logger.error(f"Failed to generate bandwidth proof: {e}")
    
    async def broadcast_uptime_proof(
        self,
        beacon_values: List[str],
        period_seconds: int
    ) -> None:
        """
        Broadcast uptime/availability proof to network.
        
        Proves continuous availability without revealing exact activity times.
        
        Args:
            beacon_values: List of beacon responses
            period_seconds: Measurement period in seconds
        """
        try:
            # Calculate uptime percentage
            uptime_pct = (len(beacon_values) / max(1, period_seconds // 60)) * 100
            uptime_pct = min(100, uptime_pct)
            
            # Generate uptime proof
            uptime_proof = self.zk_generator.generate_uptime_proof(
                uptime_percentage=uptime_pct,
                period_seconds=period_seconds,
                beacon_values=beacon_values
            )
            
            self.uptime_proofs.append(uptime_proof)
            
            # TODO: Broadcast to reward verifiers
            # 1. Encrypt with peer session keys
            # 2. Send to distributed verifier set
            # 3. Collect verification quorum
            # 4. Submit aggregate proof to blockchain
            
            logger.info(
                f"Generated uptime proof: {uptime_pct:.1f}% "
                f"({len(beacon_values)} beacons)"
            )
        except Exception as e:
            logger.error(f"Failed to generate uptime proof: {e}")
    
    async def prove_proximity(self) -> None:
        """
        Generate and store geographic proximity proof.
        
        Proves location within distance bound without revealing exact coordinates.
        """
        try:
            proximity_proof = self.zk_generator.generate_proximity_proof(
                latitude=self.latitude,
                longitude=self.longitude,
                distance_bound_km=50.0
            )
            
            self.proximity_proof = proximity_proof
            
            # TODO: Use in mesh routing to verify peer claims
            # 1. Include in peer discovery messages
            # 2. Verify peers are geographically near
            # 3. Prevent geographic spoofing attacks
            
            logger.info(
                f"Generated proximity proof: "
                f"within {proximity_proof.distance_upper_bound_km}km"
            )
        except Exception as e:
            logger.error(f"Failed to generate proximity proof: {e}")
    
    async def prove_uniqueness(self, difficulty_bits: int = 20) -> None:
        """
        Generate proof of node uniqueness (prevents Sybil attacks).
        
        Args:
            difficulty_bits: PoW difficulty level
        """
        try:
            logger.info("Generating uniqueness proof (PoW)...")
            uniqueness_proof = self.zk_generator.generate_uniqueness_proof(
                difficulty_bits=difficulty_bits
            )
            
            self.uniqueness_proof = uniqueness_proof
            
            # TODO: Broadcast on network join
            # 1. Include in peer discovery
            # 2. Verifiers check PoW and ring signature
            # 3. Prevents same attacker from creating multiple nodes
            # 4. Valid for ~1 week before needing refresh
            
            logger.info(
                f"Generated uniqueness proof: "
                f"PoW={uniqueness_proof.proof_of_work[:16]}, "
                f"ring={uniqueness_proof.ring_members}"
            )
        except Exception as e:
            logger.error(f"Failed to generate uniqueness proof: {e}")
    
    async def authenticate_peer_with_zk(
        self,
        peer_id: str,
        peer_static_key_hash: str,
        uniqueness_proof: UniquenessProof
    ) -> bool:
        """
        Authenticate peer using zero-knowledge proof.
        
        Args:
            peer_id: Peer to authenticate
            peer_static_key_hash: Hash of peer's public key
            uniqueness_proof: Peer's uniqueness proof
            
        Returns:
            True if peer authenticated successfully
        """
        try:
            # Establish secure session
            self.secure_messaging.establish_secure_session(
                peer_id,
                peer_static_key_hash
            )
            
            # Authenticate with proof
            authenticated = self.secure_messaging.authenticate_peer(
                peer_id,
                uniqueness_proof
            )
            
            if authenticated:
                logger.info(f"✓ Peer {peer_id} authenticated via ZK proof")
            else:
                logger.warning(f"✗ Failed to authenticate peer {peer_id}")
            
            return authenticated
        except Exception as e:
            logger.error(f"Peer authentication error: {e}")
            return False
    
    async def send_secure_bandwidth_claim(
        self,
        peer_id: str,
        bandwidth_proof: BandwidthProof
    ) -> bool:
        """
        Send encrypted bandwidth proof to peer with ZK verification.
        
        Args:
            peer_id: Recipient peer
            bandwidth_proof: Proof to send
            
        Returns:
            True if sent successfully
        """
        try:
            # Create message with proof
            message_data = {
                "type": "bandwidth_claim",
                "proof": bandwidth_proof.to_dict()
            }
            
            proof_dict = {
                **bandwidth_proof.to_dict(),
                "type": "bandwidth"
            }
            
            # Encrypt and send
            secure_msg = self.secure_messaging.encrypt_message(
                peer_id,
                message_data,
                proof=proof_dict
            )
            
            # TODO: Send secure_msg over LoRa to peer
            
            logger.info(
                f"Sent bandwidth claim to {peer_id}: "
                f"{bandwidth_proof.byte_count} bytes"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send bandwidth claim: {e}")
            return False
    
    async def receive_and_verify_secure_message(
        self,
        secure_msg: SecureMessage
    ) -> bool:
        """
        Receive and verify encrypted message with ZK proof.
        
        Args:
            secure_msg: Received secure message
            
        Returns:
            True if message verified successfully
        """
        try:
            # Decrypt and verify
            message_data = self.secure_messaging.decrypt_message(
                secure_msg,
                verify_proof=True
            )
            
            if message_data is None:
                return False
            
            logger.info(
                f"✓ Verified secure message from {secure_msg.sender_id}: "
                f"{secure_msg.message_type}"
            )
            return True
        except Exception as e:
            logger.error(f"Message verification error: {e}")
            return False
    
    async def calculate_bandwidth_reward(self) -> int:
        """
        Calculate token reward for bandwidth contribution.
        
        Returns:
            Reward amount in tokens
        """
        try:
            # Use RewardCalculator to determine reward
            score = self.bandwidth_stats.get_reward_score()
            
            # Base reward: 10 tokens per period
            base_reward = 10
            
            # Scale by score (0-1)
            total_reward = int(base_reward * (1 + score))
            
            logger.info(f"Calculated reward: {total_reward} tokens (score: {score:.2%})")
            return total_reward
        except Exception as e:
            logger.error(f"Reward calculation failed: {e}")
            return 0
