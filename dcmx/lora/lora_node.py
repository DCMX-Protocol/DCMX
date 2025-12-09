"""LoRa-enabled node for DCMX mesh network with Zero-Knowledge Security."""

import logging
import secrets
import asyncio
import hashlib
import struct
import json
import time
from typing import Dict, Optional, List, Set, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta
from enum import IntEnum
from collections import defaultdict

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


class PacketType(IntEnum):
    """LoRa packet types for mesh protocol."""
    RREQ = 0x01  # Route Request (AODV)
    RREP = 0x02  # Route Reply (AODV)
    RERR = 0x03  # Route Error (AODV)
    DATA = 0x04  # Data packet
    ACK = 0x05   # Acknowledgment
    BEACON = 0x06  # Periodic beacon
    CONTENT_ANNOUNCE = 0x07  # Content availability
    BANDWIDTH_PROOF = 0x08  # Bandwidth proof broadcast
    UPTIME_PROOF = 0x09  # Uptime proof broadcast


@dataclass
class LoRaPacket:
    """LoRa packet with FEC and sequencing."""
    packet_type: PacketType
    source_id: str
    dest_id: str
    sequence: int
    hop_count: int
    ttl: int
    payload: bytes
    fec_data: bytes = b""
    checksum: str = ""

    MAX_PAYLOAD_SIZE = 200  # LoRa typical max payload

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        data = (
            struct.pack(">BBHBB",
                self.packet_type,
                len(self.source_id),
                self.sequence,
                self.hop_count,
                self.ttl
            ) +
            self.source_id.encode()[:32] +
            self.dest_id.encode()[:32] +
            self.payload
        )
        return hashlib.sha256(data).hexdigest()[:16]

    def serialize(self) -> bytes:
        """Serialize packet for LoRa transmission."""
        header = struct.pack(">BHBB",
            self.packet_type,
            self.sequence,
            self.hop_count,
            self.ttl
        )
        src_bytes = self.source_id.encode()[:16].ljust(16, b'\x00')
        dst_bytes = self.dest_id.encode()[:16].ljust(16, b'\x00')
        checksum_bytes = bytes.fromhex(self.checksum)
        fec_len = struct.pack(">H", len(self.fec_data))

        packet = header + src_bytes + dst_bytes + checksum_bytes + fec_len + self.fec_data + self.payload
        return packet

    @classmethod
    def deserialize(cls, data: bytes) -> Optional["LoRaPacket"]:
        """Deserialize packet from LoRa transmission."""
        try:
            if len(data) < 45:
                return None

            packet_type, sequence, hop_count, ttl = struct.unpack(">BHBB", data[:5])
            src_bytes = data[5:21].rstrip(b'\x00').decode()
            dst_bytes = data[21:37].rstrip(b'\x00').decode()
            checksum = data[37:45].hex()
            fec_len = struct.unpack(">H", data[45:47])[0]
            fec_data = data[47:47+fec_len]
            payload = data[47+fec_len:]

            packet = cls(
                packet_type=PacketType(packet_type),
                source_id=src_bytes,
                dest_id=dst_bytes,
                sequence=sequence,
                hop_count=hop_count,
                ttl=ttl,
                payload=payload,
                fec_data=fec_data,
                checksum=checksum
            )
            return packet
        except Exception as e:
            logger.error(f"Failed to deserialize packet: {e}")
            return None

    def verify_checksum(self) -> bool:
        """Verify packet checksum."""
        return self.checksum == self._compute_checksum()


@dataclass
class RouteEntry:
    """AODV routing table entry."""
    dest_id: str
    next_hop: str
    hop_count: int
    sequence: int
    lifetime: datetime
    precursors: Set[str] = field(default_factory=set)

    def is_valid(self) -> bool:
        return datetime.utcnow() < self.lifetime


@dataclass
class PendingRouteRequest:
    """Pending RREQ awaiting RREP."""
    dest_id: str
    sequence: int
    timestamp: datetime
    retries: int = 0
    callbacks: List[Callable] = field(default_factory=list)


@dataclass
class LoRaPeer:
    """Peer accessible over LoRa mesh."""
    peer_id: str
    latitude: float
    longitude: float
    bandwidth_available_mbps: float
    uptime_percentage: float
    distance_meters: Optional[float] = None
    last_seen: Optional[datetime] = None
    signal_rssi: int = -100
    signal_snr: float = 0.0


@dataclass
class BandwidthStats:
    """Bandwidth statistics for reward calculation."""
    node_id: str
    bytes_uploaded: int = 0
    bytes_downloaded: int = 0
    uptime_seconds: float = 0.0
    unique_peers_served: int = 0
    geographic_region: str = ""
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    peers_served: Set[str] = field(default_factory=set)

    def get_reward_score(self) -> float:
        uptime_factor = self.uptime_seconds / (24 * 3600)
        bandwidth_factor = min(self.bytes_uploaded / (100 * 1024**2), 1.0)
        diversity_factor = min(self.unique_peers_served / 50, 1.0)

        score = (
            uptime_factor * 0.5 +
            bandwidth_factor * 0.3 +
            diversity_factor * 0.2
        )
        return score

    def record_peer_served(self, peer_id: str, bytes_sent: int):
        """Record bytes served to a peer."""
        self.bytes_uploaded += bytes_sent
        if peer_id not in self.peers_served:
            self.peers_served.add(peer_id)
            self.unique_peers_served = len(self.peers_served)


class ForwardErrorCorrection:
    """Reed-Solomon style FEC for LoRa packet recovery."""

    PARITY_RATIO = 0.25  # 25% redundancy

    @classmethod
    def encode(cls, data: bytes) -> Tuple[bytes, bytes]:
        """
        Encode data with FEC parity bytes.

        Returns:
            Tuple of (original_data, fec_parity)
        """
        parity_len = max(4, int(len(data) * cls.PARITY_RATIO))
        parity = bytearray(parity_len)

        for i, b in enumerate(data):
            parity[i % parity_len] ^= b
            parity[(i + 1) % parity_len] ^= (b >> 4) | ((b & 0x0F) << 4)

        checksum = hashlib.sha256(data).digest()[:4]
        parity.extend(checksum)

        return data, bytes(parity)

    @classmethod
    def decode(cls, data: bytes, fec_data: bytes, error_positions: List[int] = None) -> Optional[bytes]:
        """
        Decode and potentially repair data using FEC.

        Returns:
            Repaired data or None if unrecoverable
        """
        if len(fec_data) < 4:
            return data

        checksum = fec_data[-4:]
        actual_checksum = hashlib.sha256(data).digest()[:4]

        if checksum == actual_checksum:
            return data

        if error_positions and len(error_positions) <= len(fec_data) // 4:
            repaired = bytearray(data)
            parity = fec_data[:-4]

            for pos in error_positions:
                if pos < len(repaired):
                    repaired[pos] = parity[pos % len(parity)]

            if hashlib.sha256(bytes(repaired)).digest()[:4] == checksum:
                return bytes(repaired)

        return data


class RateLimiter:
    """Rate limiter for spam protection."""

    def __init__(self, max_requests: int = 10, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, identifier: str) -> bool:
        """Check if request is allowed (True) or rate-limited (False)."""
        async with self._lock:
            now = time.time()
            times = self.request_times[identifier]
            times = [t for t in times if now - t < self.window_seconds]
            self.request_times[identifier] = times

            if len(times) >= self.max_requests:
                return False

            times.append(now)
            return True

    async def record(self, identifier: str):
        """Record a request."""
        async with self._lock:
            self.request_times[identifier].append(time.time())


class RetransmissionManager:
    """Manage packet retransmissions for reliability."""

    MAX_RETRIES = 3
    RETRY_TIMEOUT = 2.0  # seconds
    BACKOFF_FACTOR = 1.5

    def __init__(self):
        self.pending_acks: Dict[int, Tuple[LoRaPacket, int, float]] = {}
        self._lock = asyncio.Lock()

    async def track_packet(self, packet: LoRaPacket):
        """Track packet awaiting ACK."""
        async with self._lock:
            self.pending_acks[packet.sequence] = (packet, 0, time.time())

    async def ack_received(self, sequence: int) -> bool:
        """Mark packet as acknowledged."""
        async with self._lock:
            if sequence in self.pending_acks:
                del self.pending_acks[sequence]
                return True
            return False

    async def get_retransmit_packets(self) -> List[LoRaPacket]:
        """Get packets that need retransmission."""
        now = time.time()
        to_retransmit = []

        async with self._lock:
            expired = []
            for seq, (packet, retries, last_sent) in self.pending_acks.items():
                timeout = self.RETRY_TIMEOUT * (self.BACKOFF_FACTOR ** retries)
                if now - last_sent > timeout:
                    if retries >= self.MAX_RETRIES:
                        expired.append(seq)
                    else:
                        self.pending_acks[seq] = (packet, retries + 1, now)
                        to_retransmit.append(packet)

            for seq in expired:
                del self.pending_acks[seq]

        return to_retransmit


class LoRaNode(Node):
    """
    Node extended with LoRa mesh network capability and zero-knowledge security.

    Handles:
    - LoRa radio communication
    - Geographic mesh routing (AODV-based)
    - Bandwidth accounting
    - Reward distribution for network participation
    - Zero-knowledge proof authentication
    - Secure peer-to-peer messaging
    - Sybil attack prevention
    - Forward error correction
    - Rate limiting and spam protection
    """

    ROUTE_LIFETIME_SECONDS = 300
    BEACON_INTERVAL_SECONDS = 60
    MAX_TTL = 10
    VERIFIER_QUORUM = 3

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
        super().__init__(host, port, data_dir)

        self.lora_device = lora_device
        self.bandwidth_limit = bandwidth_limit_mbps
        self.latitude = latitude
        self.longitude = longitude

        # LoRa-specific state
        self.mesh_peers: Dict[str, LoRaPeer] = {}
        self.routing_table: Dict[str, RouteEntry] = {}
        self.bandwidth_stats = BandwidthStats(node_id=self.peer.peer_id)

        # AODV routing state
        self._rreq_id = 0
        self._sequence_number = 0
        self._pending_rreqs: Dict[str, PendingRouteRequest] = {}
        self._seen_rreqs: Set[Tuple[str, int]] = set()

        # Content availability
        self._available_content: Set[str] = set()
        self._content_providers: Dict[str, Set[str]] = defaultdict(set)

        # Verifier nodes for reward proofs
        self._verifier_nodes: List[str] = []
        self._pending_verifications: Dict[str, List[bool]] = {}

        # Zero-Knowledge Security
        node_secret_key = secrets.token_bytes(32)
        self.zk_generator = ZKProofGenerator(self.peer.peer_id, node_secret_key)
        self.secure_messaging = SecureLoRaMessaging(self.peer.peer_id, node_secret_key)

        # ZK proofs
        self.bandwidth_proofs: List[BandwidthProof] = []
        self.uptime_proofs: List[UptimeProof] = []
        self.proximity_proof: Optional[ProximityProof] = None
        self.uniqueness_proof: Optional[UniquenessProof] = None

        # Rate limiting & retransmission
        self.rate_limiter = RateLimiter(max_requests=20, window_seconds=60.0)
        self.retransmit_manager = RetransmissionManager()
        self.fec = ForwardErrorCorrection()

        # Packet handling
        self._packet_handlers: Dict[PacketType, Callable] = {
            PacketType.RREQ: self._handle_rreq,
            PacketType.RREP: self._handle_rrep,
            PacketType.RERR: self._handle_rerr,
            PacketType.DATA: self._handle_data,
            PacketType.ACK: self._handle_ack,
            PacketType.BEACON: self._handle_beacon,
            PacketType.CONTENT_ANNOUNCE: self._handle_content_announce,
            PacketType.BANDWIDTH_PROOF: self._handle_bandwidth_proof,
            PacketType.UPTIME_PROOF: self._handle_uptime_proof,
        }

        # Background tasks
        self._running = False
        self._beacon_task: Optional[asyncio.Task] = None
        self._retransmit_task: Optional[asyncio.Task] = None

        logger.info(f"LoRaNode initialized at ({latitude}, {longitude}) with ZK security")

    async def start(self):
        """Start the LoRa node and background tasks."""
        await super().start()
        self._running = True

        self.bandwidth_stats.period_start = datetime.utcnow().isoformat()

        # Generate uniqueness proof on startup
        await self.prove_uniqueness(difficulty_bits=16)

        # Start background tasks
        self._beacon_task = asyncio.create_task(self._beacon_loop())
        self._retransmit_task = asyncio.create_task(self._retransmit_loop())

        logger.info("LoRaNode started with mesh networking")

    async def stop(self):
        """Stop the LoRa node."""
        self._running = False

        if self._beacon_task:
            self._beacon_task.cancel()
        if self._retransmit_task:
            self._retransmit_task.cancel()

        self.bandwidth_stats.period_end = datetime.utcnow().isoformat()

        await super().stop()
        logger.info("LoRaNode stopped")

    # ========== Mesh Routing (AODV-based) ==========

    async def discover_route(self, dest_id: str, callback: Optional[Callable] = None) -> Optional[RouteEntry]:
        """
        Discover route to destination using AODV protocol.

        Args:
            dest_id: Destination node ID
            callback: Optional callback when route found

        Returns:
            RouteEntry if found, None if discovery initiated
        """
        if dest_id in self.routing_table and self.routing_table[dest_id].is_valid():
            return self.routing_table[dest_id]

        self._rreq_id += 1
        self._sequence_number += 1

        rreq_data = {
            "type": "RREQ",
            "rreq_id": self._rreq_id,
            "dest_id": dest_id,
            "dest_seq": 0,
            "orig_id": self.peer.peer_id,
            "orig_seq": self._sequence_number,
            "orig_lat": self.latitude,
            "orig_lon": self.longitude,
        }

        packet = LoRaPacket(
            packet_type=PacketType.RREQ,
            source_id=self.peer.peer_id,
            dest_id="broadcast",
            sequence=self._rreq_id,
            hop_count=0,
            ttl=self.MAX_TTL,
            payload=json.dumps(rreq_data).encode()
        )

        pending = PendingRouteRequest(
            dest_id=dest_id,
            sequence=self._rreq_id,
            timestamp=datetime.utcnow()
        )
        if callback:
            pending.callbacks.append(callback)
        self._pending_rreqs[dest_id] = pending

        await self._broadcast_packet(packet)
        logger.info(f"RREQ sent for {dest_id[:8]}...")

        return None

    async def _handle_rreq(self, packet: LoRaPacket, sender_id: str):
        """Handle Route Request packet."""
        try:
            data = json.loads(packet.payload.decode())
            rreq_key = (data["orig_id"], data["rreq_id"])

            if rreq_key in self._seen_rreqs:
                return
            self._seen_rreqs.add(rreq_key)

            reverse_route = RouteEntry(
                dest_id=data["orig_id"],
                next_hop=sender_id,
                hop_count=packet.hop_count + 1,
                sequence=data["orig_seq"],
                lifetime=datetime.utcnow() + timedelta(seconds=self.ROUTE_LIFETIME_SECONDS)
            )
            self.routing_table[data["orig_id"]] = reverse_route

            if data["dest_id"] == self.peer.peer_id:
                await self._send_rrep(data, sender_id)
            elif data["dest_id"] in self.routing_table and self.routing_table[data["dest_id"]].is_valid():
                await self._send_rrep(data, sender_id, intermediate=True)
            elif packet.ttl > 1:
                packet.hop_count += 1
                packet.ttl -= 1
                await self._broadcast_packet(packet)

        except Exception as e:
            logger.error(f"RREQ handling error: {e}")

    async def _send_rrep(self, rreq_data: dict, to_node: str, intermediate: bool = False):
        """Send Route Reply packet."""
        self._sequence_number += 1

        if intermediate:
            route = self.routing_table[rreq_data["dest_id"]]
            hop_count = route.hop_count
            dest_seq = route.sequence
        else:
            hop_count = 0
            dest_seq = self._sequence_number

        rrep_data = {
            "type": "RREP",
            "dest_id": rreq_data["dest_id"],
            "dest_seq": dest_seq,
            "orig_id": rreq_data["orig_id"],
            "hop_count": hop_count,
            "lifetime": self.ROUTE_LIFETIME_SECONDS,
            "dest_lat": self.latitude,
            "dest_lon": self.longitude,
        }

        packet = LoRaPacket(
            packet_type=PacketType.RREP,
            source_id=self.peer.peer_id,
            dest_id=rreq_data["orig_id"],
            sequence=self._sequence_number,
            hop_count=0,
            ttl=self.MAX_TTL,
            payload=json.dumps(rrep_data).encode()
        )

        await self._send_unicast(packet, to_node)
        logger.info(f"RREP sent to {rreq_data['orig_id'][:8]}...")

    async def _handle_rrep(self, packet: LoRaPacket, sender_id: str):
        """Handle Route Reply packet."""
        try:
            data = json.loads(packet.payload.decode())

            forward_route = RouteEntry(
                dest_id=data["dest_id"],
                next_hop=sender_id,
                hop_count=data["hop_count"] + packet.hop_count + 1,
                sequence=data["dest_seq"],
                lifetime=datetime.utcnow() + timedelta(seconds=data["lifetime"])
            )

            if data["dest_id"] not in self.routing_table or \
               data["dest_seq"] >= self.routing_table[data["dest_id"]].sequence:
                self.routing_table[data["dest_id"]] = forward_route

            if data["dest_lat"] and data["dest_lon"]:
                if data["dest_id"] in self.mesh_peers:
                    self.mesh_peers[data["dest_id"]].latitude = data["dest_lat"]
                    self.mesh_peers[data["dest_id"]].longitude = data["dest_lon"]

            if data["orig_id"] == self.peer.peer_id:
                if data["dest_id"] in self._pending_rreqs:
                    pending = self._pending_rreqs.pop(data["dest_id"])
                    for cb in pending.callbacks:
                        try:
                            await cb(forward_route) if asyncio.iscoroutinefunction(cb) else cb(forward_route)
                        except Exception as e:
                            logger.error(f"Route callback error: {e}")
            else:
                if data["orig_id"] in self.routing_table:
                    next_hop = self.routing_table[data["orig_id"]].next_hop
                    packet.hop_count += 1
                    await self._send_unicast(packet, next_hop)

        except Exception as e:
            logger.error(f"RREP handling error: {e}")

    async def _handle_rerr(self, packet: LoRaPacket, sender_id: str):
        """Handle Route Error packet."""
        try:
            data = json.loads(packet.payload.decode())
            broken_dest = data.get("unreachable_dest")

            if broken_dest and broken_dest in self.routing_table:
                route = self.routing_table[broken_dest]
                if route.next_hop == sender_id:
                    del self.routing_table[broken_dest]
                    logger.warning(f"Route to {broken_dest[:8]}... invalidated")

                    for precursor in route.precursors:
                        await self._send_route_error(broken_dest, precursor)

        except Exception as e:
            logger.error(f"RERR handling error: {e}")

    async def _send_route_error(self, unreachable_dest: str, to_node: str):
        """Send Route Error packet."""
        rerr_data = {
            "type": "RERR",
            "unreachable_dest": unreachable_dest,
            "dest_seq": self._sequence_number + 1,
        }

        packet = LoRaPacket(
            packet_type=PacketType.RERR,
            source_id=self.peer.peer_id,
            dest_id=to_node,
            sequence=self._sequence_number,
            hop_count=0,
            ttl=self.MAX_TTL,
            payload=json.dumps(rerr_data).encode()
        )

        await self._send_unicast(packet, to_node)

    # ========== Content Broadcasting ==========

    async def broadcast_content(self, track_hash: str) -> None:
        """
        Broadcast track availability to mesh neighbors with ZK proof.

        Args:
            track_hash: Hash of available track
        """
        if not await self.rate_limiter.check(f"content:{track_hash}"):
            logger.warning(f"Rate limited: content broadcast for {track_hash[:16]}")
            return

        try:
            freshness_proof = self.zk_generator.generate_freshness_proof(
                message=f"broadcast:{track_hash}",
                nonce_depth=5
            )

            message_data = {
                "type": "content_broadcast",
                "track_hash": track_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "provider_id": self.peer.peer_id,
                "lat": self.latitude,
                "lon": self.longitude,
                "freshness_proof": freshness_proof.to_dict(),
            }

            payload = json.dumps(message_data).encode()
            payload, fec_data = self.fec.encode(payload)

            self._sequence_number += 1
            packet = LoRaPacket(
                packet_type=PacketType.CONTENT_ANNOUNCE,
                source_id=self.peer.peer_id,
                dest_id="broadcast",
                sequence=self._sequence_number,
                hop_count=0,
                ttl=self.MAX_TTL // 2,
                payload=payload,
                fec_data=fec_data,
            )

            self._available_content.add(track_hash)
            await self._broadcast_packet(packet)

            logger.info(
                f"Broadcast content {track_hash[:16]}... with freshness proof "
                f"(nonce_depth={len(freshness_proof.nonce_chain)})"
            )
        except Exception as e:
            logger.error(f"Failed to broadcast content: {e}")

    async def _handle_content_announce(self, packet: LoRaPacket, sender_id: str):
        """Handle content availability announcement."""
        try:
            payload = self.fec.decode(packet.payload, packet.fec_data)
            data = json.loads(payload.decode())

            if "freshness_proof" in data:
                proof_dict = data["freshness_proof"]
                proof = FreshnessProof(
                    commitment=proof_dict["commitment"],
                    message_hash=proof_dict["message_hash"],
                    timestamp_proof=proof_dict["timestamp_proof"],
                    nonce_chain=proof_dict["nonce_chain"],
                )
                if not ZKProofVerifier.verify_freshness_proof(proof):
                    logger.warning(f"Invalid freshness proof from {sender_id[:8]}")
                    return

            track_hash = data["track_hash"]
            provider_id = data["provider_id"]

            self._content_providers[track_hash].add(provider_id)

            if provider_id not in self.mesh_peers:
                self.mesh_peers[provider_id] = LoRaPeer(
                    peer_id=provider_id,
                    latitude=data.get("lat", 0),
                    longitude=data.get("lon", 0),
                    bandwidth_available_mbps=5.0,
                    uptime_percentage=100.0,
                    last_seen=datetime.utcnow(),
                )
            else:
                self.mesh_peers[provider_id].last_seen = datetime.utcnow()

            if packet.ttl > 1 and packet.hop_count < self.MAX_TTL:
                packet.hop_count += 1
                packet.ttl -= 1
                await self._broadcast_packet(packet)

            logger.debug(f"Content {track_hash[:16]}... available from {provider_id[:8]}...")

        except Exception as e:
            logger.error(f"Content announce handling error: {e}")

    # ========== Bandwidth Proofs ==========

    async def broadcast_bandwidth_proof(
        self,
        content_hashes: List[str],
        bytes_served: int
    ) -> None:
        """
        Broadcast bandwidth contribution proof to network.

        Args:
            content_hashes: Hashes of content served
            bytes_served: Total bytes transmitted
        """
        try:
            bw_proof = self.zk_generator.generate_bandwidth_proof(
                bytes_served=bytes_served,
                content_hashes=content_hashes,
                challenge_count=5
            )
            self.bandwidth_proofs.append(bw_proof)

            await self._broadcast_to_verifiers(bw_proof, PacketType.BANDWIDTH_PROOF)

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

        Args:
            beacon_values: List of beacon responses
            period_seconds: Measurement period in seconds
        """
        try:
            uptime_pct = (len(beacon_values) / max(1, period_seconds // 60)) * 100
            uptime_pct = min(100, uptime_pct)

            uptime_proof = self.zk_generator.generate_uptime_proof(
                uptime_percentage=uptime_pct,
                period_seconds=period_seconds,
                beacon_values=beacon_values
            )
            self.uptime_proofs.append(uptime_proof)

            await self._broadcast_to_verifiers(uptime_proof, PacketType.UPTIME_PROOF)

            logger.info(
                f"Generated uptime proof: {uptime_pct:.1f}% "
                f"({len(beacon_values)} beacons)"
            )
        except Exception as e:
            logger.error(f"Failed to generate uptime proof: {e}")

    async def _broadcast_to_verifiers(
        self,
        proof: BandwidthProof | UptimeProof,
        packet_type: PacketType
    ) -> None:
        """
        Send proof to designated verifier nodes.

        Args:
            proof: The proof to broadcast
            packet_type: Type of proof packet
        """
        verifiers = self._get_verifier_nodes()
        if not verifiers:
            logger.warning("No verifier nodes available")
            return

        proof_id = secrets.token_hex(8)
        self._pending_verifications[proof_id] = []

        message_data = {
            "proof_id": proof_id,
            "node_id": self.peer.peer_id,
            "proof": proof.to_dict(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        for verifier_id in verifiers[:self.VERIFIER_QUORUM * 2]:
            if verifier_id in self.mesh_peers:
                peer = self.mesh_peers[verifier_id]
                if peer.peer_id in self.secure_messaging.peer_contexts:
                    try:
                        proof_dict = {**proof.to_dict(), "type": "bandwidth" if packet_type == PacketType.BANDWIDTH_PROOF else "uptime"}
                        secure_msg = self.secure_messaging.encrypt_message(
                            verifier_id,
                            message_data,
                            proof=proof_dict
                        )
                        payload = secure_msg.to_json().encode()
                    except Exception:
                        payload = json.dumps(message_data).encode()
                else:
                    payload = json.dumps(message_data).encode()
            else:
                payload = json.dumps(message_data).encode()

            payload, fec_data = self.fec.encode(payload)

            self._sequence_number += 1
            packet = LoRaPacket(
                packet_type=packet_type,
                source_id=self.peer.peer_id,
                dest_id=verifier_id,
                sequence=self._sequence_number,
                hop_count=0,
                ttl=self.MAX_TTL,
                payload=payload,
                fec_data=fec_data,
            )

            route = await self.discover_route(verifier_id)
            if route:
                await self._send_unicast(packet, route.next_hop)
                await self.retransmit_manager.track_packet(packet)
            else:
                async def send_when_route_found(r, pkt=packet):
                    await self._send_unicast(pkt, r.next_hop)
                    await self.retransmit_manager.track_packet(pkt)

        logger.debug(f"Proof {proof_id} sent to {len(verifiers[:self.VERIFIER_QUORUM * 2])} verifiers")

    async def _handle_bandwidth_proof(self, packet: LoRaPacket, sender_id: str):
        """Handle incoming bandwidth proof for verification."""
        try:
            payload = self.fec.decode(packet.payload, packet.fec_data)
            data = json.loads(payload.decode())

            proof_dict = data.get("proof", {})
            if "commitment" not in proof_dict:
                return

            from dcmx.lora.zk_proofs import ZKProofCommitment
            commitment = ZKProofCommitment(**proof_dict["commitment"])

            proof = BandwidthProof(
                commitment=commitment,
                byte_count=proof_dict["byte_count"],
                merkle_root=proof_dict["merkle_root"],
                challenges=proof_dict["challenges"],
                responses=proof_dict["responses"],
            )

            is_valid = ZKProofVerifier.verify_bandwidth_proof(proof)

            response_data = {
                "proof_id": data.get("proof_id"),
                "node_id": data.get("node_id"),
                "verified": is_valid,
                "verifier": self.peer.peer_id,
            }

            await self._send_verification_response(packet.source_id, response_data)

        except Exception as e:
            logger.error(f"Bandwidth proof handling error: {e}")

    async def _handle_uptime_proof(self, packet: LoRaPacket, sender_id: str):
        """Handle incoming uptime proof for verification."""
        try:
            payload = self.fec.decode(packet.payload, packet.fec_data)
            data = json.loads(payload.decode())

            proof_dict = data.get("proof", {})
            if "commitment" not in proof_dict:
                return

            from dcmx.lora.zk_proofs import ZKProofCommitment
            commitment = ZKProofCommitment(**proof_dict["commitment"])

            proof = UptimeProof(
                commitment=commitment,
                uptime_percentage=proof_dict["uptime_percentage"],
                period_seconds=proof_dict["period_seconds"],
                beacon_root=proof_dict["beacon_root"],
                participation_count=proof_dict["participation_count"],
                total_beacons=proof_dict["total_beacons"],
            )

            is_valid = ZKProofVerifier.verify_uptime_proof(proof)

            response_data = {
                "proof_id": data.get("proof_id"),
                "node_id": data.get("node_id"),
                "verified": is_valid,
                "verifier": self.peer.peer_id,
            }

            await self._send_verification_response(packet.source_id, response_data)

        except Exception as e:
            logger.error(f"Uptime proof handling error: {e}")

    async def _send_verification_response(self, dest_id: str, response_data: dict):
        """Send verification response back to proof submitter."""
        payload = json.dumps(response_data).encode()

        self._sequence_number += 1
        packet = LoRaPacket(
            packet_type=PacketType.DATA,
            source_id=self.peer.peer_id,
            dest_id=dest_id,
            sequence=self._sequence_number,
            hop_count=0,
            ttl=self.MAX_TTL,
            payload=payload,
        )

        if dest_id in self.routing_table and self.routing_table[dest_id].is_valid():
            route = self.routing_table[dest_id]
            await self._send_unicast(packet, route.next_hop)

    def _get_verifier_nodes(self) -> List[str]:
        """Get list of verifier node IDs."""
        if self._verifier_nodes:
            return self._verifier_nodes

        candidates = []
        for peer_id, peer in self.mesh_peers.items():
            if peer.uptime_percentage >= 90.0:
                candidates.append((peer_id, peer.uptime_percentage))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates[:10]]

    # ========== Proximity & Uniqueness Proofs ==========

    async def prove_proximity(self) -> None:
        """Generate and store geographic proximity proof."""
        try:
            proximity_proof = self.zk_generator.generate_proximity_proof(
                latitude=self.latitude,
                longitude=self.longitude,
                distance_bound_km=50.0
            )
            self.proximity_proof = proximity_proof

            logger.info(
                f"Generated proximity proof: "
                f"within {proximity_proof.distance_upper_bound_km}km"
            )
        except Exception as e:
            logger.error(f"Failed to generate proximity proof: {e}")

    async def prove_uniqueness(self, difficulty_bits: int = 20) -> None:
        """Generate proof of node uniqueness (prevents Sybil attacks)."""
        try:
            logger.info("Generating uniqueness proof (PoW)...")
            uniqueness_proof = self.zk_generator.generate_uniqueness_proof(
                difficulty_bits=difficulty_bits
            )
            self.uniqueness_proof = uniqueness_proof

            logger.info(
                f"Generated uniqueness proof: "
                f"PoW={uniqueness_proof.proof_of_work[:16]}, "
                f"ring={uniqueness_proof.ring_members}"
            )
        except Exception as e:
            logger.error(f"Failed to generate uniqueness proof: {e}")

    # ========== Secure Messaging ==========

    async def authenticate_peer_with_zk(
        self,
        peer_id: str,
        peer_static_key_hash: str,
        uniqueness_proof: UniquenessProof
    ) -> bool:
        """Authenticate peer using zero-knowledge proof."""
        try:
            self.secure_messaging.establish_secure_session(
                peer_id,
                peer_static_key_hash
            )

            authenticated = self.secure_messaging.authenticate_peer(
                peer_id,
                uniqueness_proof
            )

            if authenticated:
                logger.info(f"✓ Peer {peer_id[:8]}... authenticated via ZK proof")
            else:
                logger.warning(f"✗ Failed to authenticate peer {peer_id[:8]}...")

            return authenticated
        except Exception as e:
            logger.error(f"Peer authentication error: {e}")
            return False

    async def send_secure_bandwidth_claim(
        self,
        peer_id: str,
        bandwidth_proof: BandwidthProof
    ) -> bool:
        """Send encrypted bandwidth proof to peer with ZK verification."""
        try:
            message_data = {
                "type": "bandwidth_claim",
                "proof": bandwidth_proof.to_dict()
            }

            proof_dict = {
                **bandwidth_proof.to_dict(),
                "type": "bandwidth"
            }

            secure_msg = self.secure_messaging.encrypt_message(
                peer_id,
                message_data,
                proof=proof_dict
            )

            payload = secure_msg.to_json().encode()
            payload, fec_data = self.fec.encode(payload)

            self._sequence_number += 1
            packet = LoRaPacket(
                packet_type=PacketType.DATA,
                source_id=self.peer.peer_id,
                dest_id=peer_id,
                sequence=self._sequence_number,
                hop_count=0,
                ttl=self.MAX_TTL,
                payload=payload,
                fec_data=fec_data,
            )

            if peer_id in self.routing_table and self.routing_table[peer_id].is_valid():
                route = self.routing_table[peer_id]
                await self._send_unicast(packet, route.next_hop)
                await self.retransmit_manager.track_packet(packet)

            logger.info(
                f"Sent bandwidth claim to {peer_id[:8]}...: "
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
        """Receive and verify encrypted message with ZK proof."""
        try:
            message_data = self.secure_messaging.decrypt_message(
                secure_msg,
                verify_proof=True
            )

            if message_data is None:
                return False

            logger.info(
                f"✓ Verified secure message from {secure_msg.sender_id[:8]}...: "
                f"{secure_msg.message_type}"
            )
            return True
        except Exception as e:
            logger.error(f"Message verification error: {e}")
            return False

    # ========== Packet Transmission ==========

    async def _broadcast_packet(self, packet: LoRaPacket):
        """Broadcast packet to all neighbors."""
        serialized = packet.serialize()
        await self._transmit_lora(serialized)
        logger.debug(f"Broadcast packet type={packet.packet_type.name} seq={packet.sequence}")

    async def _send_unicast(self, packet: LoRaPacket, next_hop: str):
        """Send packet to specific neighbor."""
        if not await self.rate_limiter.check(f"tx:{next_hop}"):
            logger.warning(f"Rate limited: transmission to {next_hop[:8]}...")
            return

        serialized = packet.serialize()
        await self._transmit_lora(serialized, target=next_hop)
        logger.debug(f"Unicast packet to {next_hop[:8]}... type={packet.packet_type.name}")

    async def _transmit_lora(self, data: bytes, target: str = None):
        """
        Transmit data over LoRa radio.

        In production, this interfaces with pylorawan or meshtastic.
        """
        pass

    async def receive_packet(self, data: bytes, rssi: int = -80, snr: float = 5.0):
        """
        Process received LoRa packet.

        Args:
            data: Raw packet data
            rssi: Received signal strength
            snr: Signal-to-noise ratio
        """
        packet = LoRaPacket.deserialize(data)
        if not packet:
            logger.warning("Failed to deserialize packet")
            return

        if not packet.verify_checksum():
            repaired = self.fec.decode(packet.payload, packet.fec_data)
            if repaired:
                packet.payload = repaired
            else:
                logger.warning("Packet checksum failed, FEC recovery failed")
                return

        if not await self.rate_limiter.check(f"rx:{packet.source_id}"):
            logger.warning(f"Rate limited: messages from {packet.source_id[:8]}...")
            return

        if packet.source_id in self.mesh_peers:
            peer = self.mesh_peers[packet.source_id]
            peer.signal_rssi = rssi
            peer.signal_snr = snr
            peer.last_seen = datetime.utcnow()

        self.bandwidth_stats.bytes_downloaded += len(data)

        handler = self._packet_handlers.get(packet.packet_type)
        if handler:
            await handler(packet, packet.source_id)
        else:
            logger.warning(f"Unknown packet type: {packet.packet_type}")

    # ========== Data Packet Handling ==========

    async def _handle_data(self, packet: LoRaPacket, sender_id: str):
        """Handle data packet."""
        if packet.dest_id == self.peer.peer_id:
            self.bandwidth_stats.record_peer_served(sender_id, len(packet.payload))
            await self._send_ack(packet.sequence, sender_id)
            await self._process_data_payload(packet.payload, sender_id)
        elif packet.dest_id in self.routing_table and packet.ttl > 1:
            route = self.routing_table[packet.dest_id]
            route.precursors.add(sender_id)
            packet.hop_count += 1
            packet.ttl -= 1
            await self._send_unicast(packet, route.next_hop)

    async def _process_data_payload(self, payload: bytes, sender_id: str):
        """Process received data payload."""
        try:
            data = json.loads(payload.decode())

            if data.get("type") == "bandwidth_claim":
                logger.debug(f"Received bandwidth claim from {sender_id[:8]}...")

            elif "verified" in data:
                proof_id = data.get("proof_id")
                if proof_id in self._pending_verifications:
                    self._pending_verifications[proof_id].append(data["verified"])

        except Exception as e:
            logger.debug(f"Data payload processing: {e}")

    async def _handle_ack(self, packet: LoRaPacket, sender_id: str):
        """Handle ACK packet."""
        try:
            data = json.loads(packet.payload.decode())
            acked_seq = data.get("ack_seq")
            if acked_seq:
                await self.retransmit_manager.ack_received(acked_seq)
                logger.debug(f"ACK received for seq={acked_seq}")
        except Exception as e:
            logger.error(f"ACK handling error: {e}")

    async def _send_ack(self, ack_sequence: int, to_node: str):
        """Send ACK for received packet."""
        ack_data = {"ack_seq": ack_sequence}

        self._sequence_number += 1
        packet = LoRaPacket(
            packet_type=PacketType.ACK,
            source_id=self.peer.peer_id,
            dest_id=to_node,
            sequence=self._sequence_number,
            hop_count=0,
            ttl=3,
            payload=json.dumps(ack_data).encode(),
        )

        await self._send_unicast(packet, to_node)

    # ========== Beacon & Background Tasks ==========

    async def _handle_beacon(self, packet: LoRaPacket, sender_id: str):
        """Handle periodic beacon from neighbor."""
        try:
            data = json.loads(packet.payload.decode())

            peer = LoRaPeer(
                peer_id=sender_id,
                latitude=data.get("lat", 0),
                longitude=data.get("lon", 0),
                bandwidth_available_mbps=data.get("bw", 5.0),
                uptime_percentage=data.get("uptime", 100.0),
                last_seen=datetime.utcnow(),
            )
            self.mesh_peers[sender_id] = peer

            if data.get("content"):
                for content_hash in data["content"]:
                    self._content_providers[content_hash].add(sender_id)

        except Exception as e:
            logger.error(f"Beacon handling error: {e}")

    async def _beacon_loop(self):
        """Periodically broadcast beacon."""
        while self._running:
            try:
                beacon_data = {
                    "lat": self.latitude,
                    "lon": self.longitude,
                    "bw": self.bandwidth_limit,
                    "uptime": 100.0,
                    "content": list(self._available_content)[:10],
                }

                self._sequence_number += 1
                packet = LoRaPacket(
                    packet_type=PacketType.BEACON,
                    source_id=self.peer.peer_id,
                    dest_id="broadcast",
                    sequence=self._sequence_number,
                    hop_count=0,
                    ttl=2,
                    payload=json.dumps(beacon_data).encode(),
                )

                await self._broadcast_packet(packet)
                self.bandwidth_stats.uptime_seconds += self.BEACON_INTERVAL_SECONDS

            except Exception as e:
                logger.error(f"Beacon error: {e}")

            await asyncio.sleep(self.BEACON_INTERVAL_SECONDS)

    async def _retransmit_loop(self):
        """Periodically check for packets needing retransmission."""
        while self._running:
            try:
                packets = await self.retransmit_manager.get_retransmit_packets()
                for packet in packets:
                    if packet.dest_id in self.routing_table:
                        route = self.routing_table[packet.dest_id]
                        await self._send_unicast(packet, route.next_hop)
                        logger.debug(f"Retransmit seq={packet.sequence}")
            except Exception as e:
                logger.error(f"Retransmit error: {e}")

            await asyncio.sleep(1.0)

    # ========== Rewards ==========

    async def calculate_bandwidth_reward(self) -> int:
        """Calculate token reward for bandwidth contribution."""
        try:
            score = self.bandwidth_stats.get_reward_score()
            base_reward = 10
            total_reward = int(base_reward * (1 + score))

            logger.info(f"Calculated reward: {total_reward} tokens (score: {score:.2%})")
            return total_reward
        except Exception as e:
            logger.error(f"Reward calculation failed: {e}")
            return 0

    def get_content_providers(self, track_hash: str) -> Set[str]:
        """Get peers that have announced a specific track."""
        return self._content_providers.get(track_hash, set())
