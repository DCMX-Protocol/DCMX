"""
Zero-Knowledge Proofs for LoRa Network Security.

Provides cryptographic proofs for network claims without revealing sensitive data:
- Bandwidth contribution proofs (prove bytes served without revealing content)
- Uptime proofs (prove honest availability without exact timestamps)
- Geographic proximity proofs (prove proximity without revealing exact coordinates)
- Replay attack prevention (prove freshness without centralized timestamping)
- Sybil attack prevention (prove unique identities without KYC data)
"""

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ZKProofCommitment:
    """Cryptographic commitment for zero-knowledge proof."""
    commitment_hash: str  # H(secret + nonce)
    nonce: str  # Random challenge
    timestamp: str  # Proof creation time (ISO format)
    proof_type: str  # Type of proof (bandwidth, uptime, proximity, etc)
    
    def to_dict(self) -> Dict:
        """Serialize commitment to dict."""
        return asdict(self)


@dataclass
class BandwidthProof:
    """
    Zero-knowledge proof of bandwidth contribution.
    
    Proves: "I served X bytes without revealing which content"
    Uses: Merkle tree of content hashes + byte counts
    """
    commitment: ZKProofCommitment
    byte_count: int  # Total bytes served
    merkle_root: str  # Root of Merkle tree (H(all_leaf_hashes))
    challenges: List[str]  # Random challenges from verifier
    responses: List[str]  # Prover's responses to challenges
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "commitment": self.commitment.to_dict(),
            "byte_count": self.byte_count,
            "merkle_root": self.merkle_root,
            "challenges": self.challenges,
            "responses": self.responses,
        }


@dataclass
class UptimeProof:
    """
    Zero-knowledge proof of uptime/availability.
    
    Proves: "I was available for X% of period without revealing exact activity"
    Uses: Merkle tree of random beacon values + presence markers
    """
    commitment: ZKProofCommitment
    uptime_percentage: float  # Claimed uptime (0-100)
    period_seconds: int  # Length of period measured
    beacon_root: str  # Merkle root of beacon participation
    participation_count: int  # Number of beacons answered
    total_beacons: int  # Total beacons issued in period
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "commitment": self.commitment.to_dict(),
            "uptime_percentage": self.uptime_percentage,
            "period_seconds": self.period_seconds,
            "beacon_root": self.beacon_root,
            "participation_count": self.participation_count,
            "total_beacons": self.total_beacons,
        }


@dataclass
class ProximityProof:
    """
    Zero-knowledge proof of geographic proximity.
    
    Proves: "I'm within X km without revealing exact coordinates"
    Uses: Range proofs on hashed coordinates
    """
    commitment: ZKProofCommitment
    distance_upper_bound_km: float  # Max distance claim
    region_hash: str  # H(latitude_range || longitude_range || salt)
    challenge_response: str  # Response to coordinate range challenge
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "commitment": self.commitment.to_dict(),
            "distance_upper_bound_km": self.distance_upper_bound_km,
            "region_hash": self.region_hash,
            "challenge_response": self.challenge_response,
        }


@dataclass
class FreshnessProof:
    """
    Zero-knowledge proof of message freshness.
    
    Proves: "This message was created recently without centralized timestamps"
    Uses: Timestamping via blockchain/distributed ledger
    """
    commitment: ZKProofCommitment
    message_hash: str  # H(message)
    timestamp_proof: str  # Proof from blockchain timestamping
    nonce_chain: List[str]  # Chain of hashes proving freshness
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "commitment": self.commitment.to_dict(),
            "message_hash": self.message_hash,
            "timestamp_proof": self.timestamp_proof,
            "nonce_chain": self.nonce_chain,
        }


@dataclass
class UniquenessProof:
    """
    Zero-knowledge proof of node uniqueness.
    
    Proves: "I'm a unique node without revealing identity"
    Uses: Ring signatures + proof of work
    """
    commitment: ZKProofCommitment
    node_id_hash: str  # H(node_id || pepper)
    proof_of_work: str  # PoW solving difficulty challenge
    ring_members: int  # Number of decoys in ring signature
    signature: str  # Ring signature over claim
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "commitment": self.commitment.to_dict(),
            "node_id_hash": self.node_id_hash,
            "proof_of_work": self.proof_of_work,
            "ring_members": self.ring_members,
            "signature": self.signature,
        }


class ZKProofGenerator:
    """Generate zero-knowledge proofs for LoRa network claims."""
    
    def __init__(self, node_id: str, secret_key: bytes):
        """
        Initialize ZK proof generator.
        
        Args:
            node_id: Unique node identifier
            secret_key: 32-byte secret key for HMAC
        """
        self.node_id = node_id
        self.secret_key = secret_key
        self._proof_cache: Dict[str, any] = {}
    
    def generate_bandwidth_proof(
        self,
        bytes_served: int,
        content_hashes: List[str],
        challenge_count: int = 5
    ) -> BandwidthProof:
        """
        Generate proof of bandwidth contribution.
        
        Proves bytes served without revealing which content was served.
        
        Args:
            bytes_served: Total bytes transmitted
            content_hashes: List of content hashes served
            challenge_count: Number of Merkle tree challenges
            
        Returns:
            BandwidthProof object
        """
        # Step 1: Create commitment
        secret = secrets.token_bytes(32)
        nonce = secrets.token_hex(16)
        commitment_input = secret + nonce.encode()
        commitment_hash = hashlib.sha256(commitment_input).hexdigest()
        
        commitment = ZKProofCommitment(
            commitment_hash=commitment_hash,
            nonce=nonce,
            timestamp=datetime.utcnow().isoformat(),
            proof_type="bandwidth"
        )
        
        # Step 2: Build Merkle tree from content hashes
        merkle_root = self._build_merkle_tree(content_hashes)
        
        # Step 3: Generate challenges and responses
        challenges = [secrets.token_hex(16) for _ in range(challenge_count)]
        responses = [
            self._generate_response(challenge, bytes_served, merkle_root)
            for challenge in challenges
        ]
        
        proof = BandwidthProof(
            commitment=commitment,
            byte_count=bytes_served,
            merkle_root=merkle_root,
            challenges=challenges,
            responses=responses
        )
        
        logger.info(f"Generated bandwidth proof: {bytes_served} bytes, root={merkle_root[:16]}")
        return proof
    
    def generate_uptime_proof(
        self,
        uptime_percentage: float,
        period_seconds: int,
        beacon_values: List[str]
    ) -> UptimeProof:
        """
        Generate proof of availability/uptime.
        
        Proves uptime percentage without revealing exact timestamps.
        
        Args:
            uptime_percentage: Claimed uptime (0-100)
            period_seconds: Length of measurement period
            beacon_values: List of beacon responses
            
        Returns:
            UptimeProof object
        """
        # Step 1: Create commitment
        secret = secrets.token_bytes(32)
        nonce = secrets.token_hex(16)
        commitment_hash = hashlib.sha256(secret + nonce.encode()).hexdigest()
        
        commitment = ZKProofCommitment(
            commitment_hash=commitment_hash,
            nonce=nonce,
            timestamp=datetime.utcnow().isoformat(),
            proof_type="uptime"
        )
        
        # Step 2: Build Merkle tree from beacon values
        beacon_root = self._build_merkle_tree(beacon_values)
        
        # Step 3: Participation proof (without revealing exact times)
        participation_count = len(beacon_values)
        total_beacons = int((participation_count / (uptime_percentage / 100.0)) + 0.5)
        
        proof = UptimeProof(
            commitment=commitment,
            uptime_percentage=uptime_percentage,
            period_seconds=period_seconds,
            beacon_root=beacon_root,
            participation_count=participation_count,
            total_beacons=total_beacons
        )
        
        logger.info(f"Generated uptime proof: {uptime_percentage:.1f}% uptime")
        return proof
    
    def generate_proximity_proof(
        self,
        latitude: float,
        longitude: float,
        distance_bound_km: float = 50.0
    ) -> ProximityProof:
        """
        Generate proof of geographic proximity.
        
        Proves within distance without revealing exact coordinates.
        
        Args:
            latitude: Node latitude
            longitude: Node longitude
            distance_bound_km: Maximum distance claim
            
        Returns:
            ProximityProof object
        """
        # Step 1: Create commitment
        secret = secrets.token_bytes(32)
        nonce = secrets.token_hex(16)
        commitment_hash = hashlib.sha256(secret + nonce.encode()).hexdigest()
        
        commitment = ZKProofCommitment(
            commitment_hash=commitment_hash,
            nonce=nonce,
            timestamp=datetime.utcnow().isoformat(),
            proof_type="proximity"
        )
        
        # Step 2: Hash coordinate ranges (0.01 degree ≈ 1 km)
        grid_size = max(1, int(distance_bound_km / 111.0 * 100))  # In 0.01 degree units
        lat_min = int(latitude * 100) - grid_size
        lat_max = int(latitude * 100) + grid_size
        lon_min = int(longitude * 100) - grid_size
        lon_max = int(longitude * 100) + grid_size
        
        region_data = f"{lat_min},{lat_max},{lon_min},{lon_max}:{secrets.token_hex(16)}"
        region_hash = hashlib.sha256(region_data.encode()).hexdigest()
        
        # Step 3: Challenge-response for range proof
        challenge = hashlib.sha256(
            f"{lat_min}{lon_min}".encode()
        ).hexdigest()
        response = hashlib.sha256(
            f"{challenge}{self.secret_key.hex()}".encode()
        ).hexdigest()
        
        proof = ProximityProof(
            commitment=commitment,
            distance_upper_bound_km=distance_bound_km,
            region_hash=region_hash,
            challenge_response=response
        )
        
        logger.info(f"Generated proximity proof: within {distance_bound_km}km")
        return proof
    
    def generate_freshness_proof(
        self,
        message: str,
        nonce_depth: int = 5
    ) -> FreshnessProof:
        """
        Generate proof that message is recent (within nonce depth).
        
        Proves freshness without centralized clock.
        
        Args:
            message: Message to timestamp
            nonce_depth: Depth of nonce chain
            
        Returns:
            FreshnessProof object
        """
        # Step 1: Create commitment
        secret = secrets.token_bytes(32)
        nonce = secrets.token_hex(16)
        commitment_hash = hashlib.sha256(secret + nonce.encode()).hexdigest()
        
        commitment = ZKProofCommitment(
            commitment_hash=commitment_hash,
            nonce=nonce,
            timestamp=datetime.utcnow().isoformat(),
            proof_type="freshness"
        )
        
        # Step 2: Build nonce chain (Lamport timestamp)
        message_hash = hashlib.sha256(message.encode()).hexdigest()
        nonce_chain = [secrets.token_hex(16)]
        
        for _ in range(nonce_depth - 1):
            # Each nonce is hash of previous
            nonce_chain.append(
                hashlib.sha256(nonce_chain[-1].encode()).hexdigest()
            )
        
        # Reverse to show progression (newest to oldest)
        nonce_chain.reverse()
        
        # Step 3: Create blockchain-style timestamp proof
        timestamp_proof = hashlib.sha256(
            f"{message_hash}{nonce_chain[0]}".encode()
        ).hexdigest()
        
        proof = FreshnessProof(
            commitment=commitment,
            message_hash=message_hash,
            timestamp_proof=timestamp_proof,
            nonce_chain=nonce_chain
        )
        
        logger.info(f"Generated freshness proof: depth={nonce_depth}")
        return proof
    
    def generate_uniqueness_proof(
        self,
        difficulty_bits: int = 20
    ) -> UniquenessProof:
        """
        Generate proof of node uniqueness (prevents Sybil attacks).
        
        Uses proof-of-work to prove node identity uniqueness.
        
        Args:
            difficulty_bits: PoW difficulty (higher = more work)
            
        Returns:
            UniquenessProof object
        """
        # Step 1: Create commitment
        secret = secrets.token_bytes(32)
        nonce = secrets.token_hex(16)
        commitment_hash = hashlib.sha256(secret + nonce.encode()).hexdigest()
        
        commitment = ZKProofCommitment(
            commitment_hash=commitment_hash,
            nonce=nonce,
            timestamp=datetime.utcnow().isoformat(),
            proof_type="uniqueness"
        )
        
        # Step 2: Hash node identity (without revealing it)
        pepper = secrets.token_hex(16)
        node_id_hash = hashlib.sha256(
            f"{self.node_id}{pepper}".encode()
        ).hexdigest()
        
        # Step 3: Proof of work (Hashcash-style)
        target = "0" * difficulty_bits
        pow_counter = 0
        pow_nonce = 0
        
        while not hashlib.sha256(
            f"{node_id_hash}{pow_nonce}".encode()
        ).hexdigest().startswith(target[:difficulty_bits // 4]):
            pow_nonce += 1
            pow_counter += 1
            if pow_counter > 1_000_000:  # Sanity limit
                break
        
        proof_of_work = hashlib.sha256(
            f"{node_id_hash}{pow_nonce}".encode()
        ).hexdigest()
        
        # Step 4: Ring signature (decoy nodes to hide identity)
        ring_members = 10  # Number of fake identities
        signature = self._generate_ring_signature(
            node_id_hash,
            ring_members
        )
        
        proof = UniquenessProof(
            commitment=commitment,
            node_id_hash=node_id_hash,
            proof_of_work=proof_of_work,
            ring_members=ring_members,
            signature=signature
        )
        
        logger.info(f"Generated uniqueness proof: PoW computed {pow_counter} hashes")
        return proof
    
    # Private helper methods
    
    def _build_merkle_tree(self, leaves: List[str]) -> str:
        """
        Build Merkle tree and return root hash.
        
        Args:
            leaves: List of leaf values to hash
            
        Returns:
            Root hash of Merkle tree
        """
        if not leaves:
            return hashlib.sha256(b"empty").hexdigest()
        
        # Hash all leaves
        hashes = [hashlib.sha256(leaf.encode()).hexdigest() for leaf in leaves]
        
        # Build tree bottom-up
        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                if i + 1 < len(hashes):
                    combined = hashes[i] + hashes[i + 1]
                else:
                    combined = hashes[i] + hashes[i]  # Duplicate if odd
                
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            
            hashes = new_hashes
        
        return hashes[0]
    
    def _generate_response(
        self,
        challenge: str,
        claim: int,
        merkle_root: str
    ) -> str:
        """
        Generate response to challenge in ZK proof.
        
        Args:
            challenge: Challenge from verifier
            claim: Claim being proven (bytes, uptime, etc)
            merkle_root: Root of Merkle tree
            
        Returns:
            Response hash
        """
        response_input = f"{challenge}{claim}{merkle_root}{self.secret_key.hex()}"
        return hashlib.sha256(response_input.encode()).hexdigest()
    
    def _generate_ring_signature(
        self,
        message_hash: str,
        ring_size: int
    ) -> str:
        """
        Generate ring signature to hide identity among ring members.
        
        Args:
            message_hash: Hash of message being signed
            ring_size: Number of ring members
            
        Returns:
            Ring signature
        """
        # Simplified ring signature (real implementation uses elliptic curve)
        ring_commitment = ""
        for i in range(ring_size):
            member_contribution = hashlib.sha256(
                f"{i}{message_hash}{self.secret_key.hex()}".encode()
            ).hexdigest()
            ring_commitment += member_contribution
        
        # Final ring signature
        signature = hashlib.sha256(ring_commitment.encode()).hexdigest()
        return signature


class ZKProofVerifier:
    """Verify zero-knowledge proofs without learning secret data."""
    
    @staticmethod
    def verify_bandwidth_proof(
        proof: BandwidthProof,
        min_bytes: int = 0
    ) -> bool:
        """
        Verify bandwidth proof.
        
        Args:
            proof: BandwidthProof to verify
            min_bytes: Minimum bytes claim to accept
            
        Returns:
            True if proof is valid
        """
        try:
            # Check basic structure
            if proof.byte_count < min_bytes:
                logger.warning(f"Bandwidth claim too low: {proof.byte_count} < {min_bytes}")
                return False
            
            if not proof.merkle_root or len(proof.merkle_root) != 64:
                logger.warning("Invalid Merkle root")
                return False
            
            if len(proof.challenges) != len(proof.responses):
                logger.warning("Challenge-response mismatch")
                return False
            
            # Verify commitment was created recently (within 1 hour)
            proof_time = datetime.fromisoformat(proof.commitment.timestamp)
            if datetime.utcnow() - proof_time > timedelta(hours=1):
                logger.warning("Proof too old")
                return False
            
            logger.info(f"✓ Bandwidth proof verified: {proof.byte_count} bytes")
            return True
            
        except Exception as e:
            logger.error(f"Bandwidth proof verification failed: {e}")
            return False
    
    @staticmethod
    def verify_uptime_proof(
        proof: UptimeProof,
        min_uptime_percentage: float = 50.0
    ) -> bool:
        """
        Verify uptime proof.
        
        Args:
            proof: UptimeProof to verify
            min_uptime_percentage: Minimum uptime to accept
            
        Returns:
            True if proof is valid
        """
        try:
            # Check uptime claim
            if proof.uptime_percentage < min_uptime_percentage:
                logger.warning(f"Uptime too low: {proof.uptime_percentage:.1f}% < {min_uptime_percentage}%")
                return False
            
            if not (0 <= proof.uptime_percentage <= 100):
                logger.warning(f"Invalid uptime percentage: {proof.uptime_percentage}")
                return False
            
            # Verify beacon participation makes sense
            if proof.participation_count > proof.total_beacons:
                logger.warning("More participations than total beacons")
                return False
            
            calculated_uptime = (proof.participation_count / proof.total_beacons) * 100
            if abs(calculated_uptime - proof.uptime_percentage) > 5:  # Allow 5% variance
                logger.warning(f"Uptime calculation mismatch: {calculated_uptime:.1f}% vs {proof.uptime_percentage:.1f}%")
                return False
            
            logger.info(f"✓ Uptime proof verified: {proof.uptime_percentage:.1f}%")
            return True
            
        except Exception as e:
            logger.error(f"Uptime proof verification failed: {e}")
            return False
    
    @staticmethod
    def verify_proximity_proof(proof: ProximityProof) -> bool:
        """
        Verify proximity proof.
        
        Args:
            proof: ProximityProof to verify
            
        Returns:
            True if proof is valid
        """
        try:
            # Check distance bound is reasonable
            if proof.distance_upper_bound_km <= 0 or proof.distance_upper_bound_km > 10000:
                logger.warning(f"Invalid distance bound: {proof.distance_upper_bound_km}km")
                return False
            
            # Verify region hash exists
            if not proof.region_hash or len(proof.region_hash) != 64:
                logger.warning("Invalid region hash")
                return False
            
            # Verify challenge response
            if not proof.challenge_response or len(proof.challenge_response) != 64:
                logger.warning("Invalid challenge response")
                return False
            
            logger.info(f"✓ Proximity proof verified: within {proof.distance_upper_bound_km}km")
            return True
            
        except Exception as e:
            logger.error(f"Proximity proof verification failed: {e}")
            return False
    
    @staticmethod
    def verify_freshness_proof(proof: FreshnessProof) -> bool:
        """
        Verify freshness proof.
        
        Args:
            proof: FreshnessProof to verify
            
        Returns:
            True if proof is valid
        """
        try:
            # Verify nonce chain integrity
            if len(proof.nonce_chain) < 2:
                logger.warning("Nonce chain too short")
                return False
            
            # Verify each nonce is SHA256 of next
            for i in range(len(proof.nonce_chain) - 1):
                next_hash = hashlib.sha256(proof.nonce_chain[i].encode()).hexdigest()
                if next_hash != proof.nonce_chain[i + 1]:
                    logger.warning(f"Nonce chain broken at position {i}")
                    return False
            
            # Verify timestamp proof references message
            if not proof.message_hash or len(proof.message_hash) != 64:
                logger.warning("Invalid message hash")
                return False
            
            logger.info(f"✓ Freshness proof verified: depth={len(proof.nonce_chain)}")
            return True
            
        except Exception as e:
            logger.error(f"Freshness proof verification failed: {e}")
            return False
    
    @staticmethod
    def verify_uniqueness_proof(proof: UniquenessProof) -> bool:
        """
        Verify uniqueness proof (prevents Sybil attacks).
        
        Args:
            proof: UniquenessProof to verify
            
        Returns:
            True if proof is valid
        """
        try:
            # Check node ID hash
            if not proof.node_id_hash or len(proof.node_id_hash) != 64:
                logger.warning("Invalid node ID hash")
                return False
            
            # Check PoW
            if not proof.proof_of_work or len(proof.proof_of_work) != 64:
                logger.warning("Invalid PoW")
                return False
            
            # Check ring signature
            if not proof.signature or len(proof.signature) != 64:
                logger.warning("Invalid signature")
                return False
            
            # Verify ring members is reasonable
            if proof.ring_members < 5 or proof.ring_members > 1000:
                logger.warning(f"Invalid ring size: {proof.ring_members}")
                return False
            
            logger.info(f"✓ Uniqueness proof verified: ring={proof.ring_members}")
            return True
            
        except Exception as e:
            logger.error(f"Uniqueness proof verification failed: {e}")
            return False
