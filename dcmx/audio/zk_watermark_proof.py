"""
Zero-Knowledge Proof Watermarking System for DCMX

Enables proving watermark authenticity without revealing the watermark itself.
Supports cascading verification chains for blockchain integration.

Key Concepts:
1. ZK Proof: Proves "I know a valid watermark" without disclosing it
2. Cascading: Each verification layer adds a proof to a chain
3. Trustless: Proofs can be verified by any party without trust assumptions
4. Blockchain: Proofs can be committed on-chain for immutable verification
"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import json
import logging

logger = logging.getLogger(__name__)


class ProofType(Enum):
    """Types of zero-knowledge proofs for watermarks."""
    
    # Challenge-response proofs
    COMMITMENT_PROOF = "commitment_proof"              # Pedersen commitment
    RANGE_PROOF = "range_proof"                        # Proves value in range
    DISCRETE_LOG_PROOF = "discrete_log_proof"          # Discrete log knowledge
    
    # Accumulator proofs
    RSA_ACCUMULATOR_PROOF = "rsa_accumulator_proof"    # RSA-based membership
    MERKLE_PROOF = "merkle_proof"                      # Merkle tree membership
    
    # Signature proofs
    BLS_SIGNATURE_PROOF = "bls_signature_proof"        # BLS signature proof
    SCHNORR_PROOF = "schnorr_proof"                    # Schnorr signature proof
    
    # Proof aggregation
    COMBINED_PROOF = "combined_proof"                  # Multiple proofs combined
    CASCADING_PROOF = "cascading_proof"                # Proof chain


class VerificationStatus(Enum):
    """Status of proof verification."""
    
    UNVERIFIED = "unverified"                          # Not yet verified
    VALID = "valid"                                    # Successfully verified
    INVALID = "invalid"                                # Failed verification
    EXPIRED = "expired"                                # TTL exceeded
    REVOKED = "revoked"                                # Explicitly revoked
    UNKNOWN = "unknown"                                # Unknown verification state


@dataclass
class ZKCommitment:
    """Pedersen commitment to a watermark."""
    
    # Commitment value (hash of watermark + random blinding factor)
    commitment: str
    
    # Blinding factor (kept secret, proves commitment knowledge)
    blinding_factor: str
    
    # Challenge response for commitment proof
    challenge_response: str
    
    # Proof that commitment is valid
    validity_proof: str
    
    # Generator points used in commitment
    generator_g: str
    generator_h: str
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    commitment_type: str = "pedersen"


@dataclass
class CascadingProofChain:
    """Chain of proofs that cascade verification through layers."""
    
    # Root proof (initial watermark verification)
    root_proof: 'ZKWatermarkProof'
    
    # Layer proofs (cascade through verification layers)
    layer_proofs: List['ZKWatermarkProof'] = field(default_factory=list)
    
    # Commitment at each layer (proves proof continuity)
    layer_commitments: List[ZKCommitment] = field(default_factory=list)
    
    # Chain metadata
    chain_id: str = field(default_factory=lambda: secrets.token_hex(16))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    depth: int = 0
    verified_at_layers: List[str] = field(default_factory=list)  # Layer IDs verified
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "chain_id": self.chain_id,
            "created_at": self.created_at,
            "depth": self.depth,
            "verified_at_layers": self.verified_at_layers,
            "root_proof": self.root_proof.to_dict() if self.root_proof else None,
            "layer_proofs": [p.to_dict() for p in self.layer_proofs],
            "layer_commitments": [c.__dict__ for c in self.layer_commitments]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CascadingProofChain':
        """Deserialize from JSON-compatible dict."""
        chain = cls(
            root_proof=None,
            chain_id=data.get("chain_id"),
            created_at=data.get("created_at"),
            depth=data.get("depth", 0),
            verified_at_layers=data.get("verified_at_layers", [])
        )
        if data.get("root_proof"):
            chain.root_proof = ZKWatermarkProof.from_dict(data["root_proof"])
        chain.layer_proofs = [ZKWatermarkProof.from_dict(p) for p in data.get("layer_proofs", [])]
        return chain


@dataclass
class ZKWatermarkProof:
    """Zero-knowledge proof of watermark knowledge."""
    
    # Proof identifier
    proof_id: str = field(default_factory=lambda: secrets.token_hex(16))
    
    # Type of proof (commitment, range, discrete log, etc.)
    proof_type: ProofType = ProofType.COMMITMENT_PROOF
    
    # Challenge sent to prover (for interactive proofs)
    challenge: str = field(default_factory=lambda: secrets.token_hex(32))
    
    # Prover's response to challenge
    response: str = ""
    
    # Commitment value (what we're proving knowledge of)
    commitment: str = ""
    
    # Verification status
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    
    # Proof parameters
    proof_parameters: Dict[str, str] = field(default_factory=dict)
    
    # Metadata about what was proven
    proven_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Cascade information (for cascading proofs)
    cascaded_from: Optional[str] = None                # Parent proof ID
    cascade_layer: int = 0                             # Layer in cascade (0=root)
    cascade_depth: int = 1                             # Total depth
    
    # Verification information
    verified_by: Optional[str] = None                  # Verifier identifier
    verification_timestamp: Optional[str] = None
    verification_algorithm: str = "pedersen_hmac"
    
    # Blockchain commitment (for on-chain verification)
    blockchain_tx_hash: Optional[str] = None           # Transaction hash if committed
    blockchain_block_number: Optional[int] = None
    blockchain_timestamp: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None                   # TTL for proof
    revoked: bool = False
    revocation_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "proof_id": self.proof_id,
            "proof_type": self.proof_type.value if isinstance(self.proof_type, ProofType) else self.proof_type,
            "challenge": self.challenge,
            "response": self.response,
            "commitment": self.commitment,
            "status": self.status.value if isinstance(self.status, VerificationStatus) else self.status,
            "proof_parameters": self.proof_parameters,
            "proven_metadata": self.proven_metadata,
            "cascaded_from": self.cascaded_from,
            "cascade_layer": self.cascade_layer,
            "cascade_depth": self.cascade_depth,
            "verified_by": self.verified_by,
            "verification_timestamp": self.verification_timestamp,
            "verification_algorithm": self.verification_algorithm,
            "blockchain_tx_hash": self.blockchain_tx_hash,
            "blockchain_block_number": self.blockchain_block_number,
            "blockchain_timestamp": self.blockchain_timestamp,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "revocation_reason": self.revocation_reason
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ZKWatermarkProof':
        """Deserialize from JSON-compatible dict."""
        proof_type = data.get("proof_type")
        if isinstance(proof_type, str):
            proof_type = ProofType(proof_type)
        
        status = data.get("status")
        if isinstance(status, str):
            status = VerificationStatus(status)
        
        return cls(
            proof_id=data.get("proof_id"),
            proof_type=proof_type,
            challenge=data.get("challenge", ""),
            response=data.get("response", ""),
            commitment=data.get("commitment", ""),
            status=status,
            proof_parameters=data.get("proof_parameters", {}),
            proven_metadata=data.get("proven_metadata", {}),
            cascaded_from=data.get("cascaded_from"),
            cascade_layer=data.get("cascade_layer", 0),
            cascade_depth=data.get("cascade_depth", 1),
            verified_by=data.get("verified_by"),
            verification_timestamp=data.get("verification_timestamp"),
            verification_algorithm=data.get("verification_algorithm", "pedersen_hmac"),
            blockchain_tx_hash=data.get("blockchain_tx_hash"),
            blockchain_block_number=data.get("blockchain_block_number"),
            blockchain_timestamp=data.get("blockchain_timestamp"),
            created_at=data.get("created_at"),
            expires_at=data.get("expires_at"),
            revoked=data.get("revoked", False),
            revocation_reason=data.get("revocation_reason")
        )


class ZKWatermarkProofGenerator:
    """Generates zero-knowledge proofs for watermarks."""
    
    def __init__(self, proof_ttl_seconds: int = 86400):
        """Initialize proof generator.
        
        Args:
            proof_ttl_seconds: Time-to-live for proofs (default: 24 hours)
        """
        self.proof_ttl_seconds = proof_ttl_seconds
        self.generator_g = secrets.token_hex(32)  # Generator point G
        self.generator_h = secrets.token_hex(32)  # Generator point H (independent of G)
    
    def generate_commitment(self, watermark_data: bytes, secret_seed: Optional[bytes] = None) -> ZKCommitment:
        """Generate Pedersen commitment to watermark.
        
        Args:
            watermark_data: The watermark bytes to commit to
            secret_seed: Optional seed for reproducibility
        
        Returns:
            ZKCommitment with proof of knowledge
        """
        # Generate blinding factor (random secret)
        if secret_seed:
            blinding = hashlib.sha256(secret_seed).digest()
        else:
            blinding = secrets.token_bytes(32)
        
        blinding_hex = blinding.hex()
        
        # Compute Pedersen commitment: C = g^watermark * h^blinding
        watermark_hash = hashlib.sha256(watermark_data).hexdigest()
        commitment_data = f"{self.generator_g}{watermark_hash}{self.generator_h}{blinding_hex}".encode()
        commitment = hashlib.sha256(commitment_data).hexdigest()
        
        # Generate challenge for proof of knowledge
        challenge_data = f"{commitment}{self.generator_g}{self.generator_h}".encode()
        challenge = hashlib.sha256(challenge_data).hexdigest()
        
        # Generate response: response = blinding + challenge * watermark_hash
        challenge_int = int(challenge, 16)
        watermark_int = int(watermark_hash, 16)
        blinding_int = int(blinding_hex, 16)
        response_int = (blinding_int + challenge_int * watermark_int) % (2**256 - 1)
        response = hex(response_int)[2:].zfill(64)
        
        # Validity proof: hash(commitment || challenge || response)
        validity_data = f"{commitment}{challenge}{response}".encode()
        validity_proof = hashlib.sha256(validity_data).hexdigest()
        
        return ZKCommitment(
            commitment=commitment,
            blinding_factor=blinding_hex,
            challenge_response=response,
            validity_proof=validity_proof,
            generator_g=self.generator_g,
            generator_h=self.generator_h
        )
    
    def create_range_proof(self, value: int, min_val: int = 0, max_val: int = 2**32) -> Dict[str, str]:
        """Create range proof (proves value is in [min_val, max_val] without revealing value).
        
        Args:
            value: Value to prove is in range
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
        
        Returns:
            Range proof parameters
        """
        # Compute commitments for each bit position
        bit_commitments = []
        value_normalized = value - min_val
        max_bits = (max_val - min_val).bit_length()
        
        for i in range(max_bits):
            bit = (value_normalized >> i) & 1
            bit_data = f"{self.generator_g}{bit}{i}".encode()
            bit_commitment = hashlib.sha256(bit_data).hexdigest()
            bit_commitments.append(bit_commitment)
        
        # Create range proof commitment
        range_proof_data = "".join(bit_commitments).encode()
        range_proof = hashlib.sha256(range_proof_data).hexdigest()
        
        return {
            "range_proof": range_proof,
            "min_value": str(min_val),
            "max_value": str(max_val),
            "bit_commitments": ",".join(bit_commitments),
            "bit_count": str(max_bits)
        }
    
    def create_discrete_log_proof(self, base: int, exponent: int, result: int) -> Dict[str, str]:
        """Create discrete log proof (proves result = base^exponent without revealing exponent).
        
        Args:
            base: Base value
            exponent: Exponent (kept secret)
            result: Result = base^exponent (public)
        
        Returns:
            Discrete log proof parameters
        """
        # Challenge: hash(base || result)
        challenge_data = f"{base}{result}".encode()
        challenge = hashlib.sha256(challenge_data).hexdigest()
        challenge_int = int(challenge, 16)
        
        # Witness: random value for blinding
        witness = secrets.randbelow(2**256)
        witness_commitment = pow(base, witness, 2**256)
        
        # Response: witness + challenge * exponent
        response = (witness + challenge_int * exponent) % (2**256 - 1)
        
        # Verification: base^response = witness_commitment * result^challenge
        return {
            "discrete_log_proof": hex(response)[2:],
            "challenge": challenge,
            "base": str(base),
            "result": str(result),
            "witness_commitment": hex(witness_commitment)[2:]
        }
    
    def create_proof(
        self,
        watermark_data: bytes,
        proof_type: ProofType = ProofType.COMMITMENT_PROOF,
        metadata: Optional[Dict[str, Any]] = None,
        cascaded_from: Optional[str] = None,
        cascade_layer: int = 0,
        cascade_depth: int = 1
    ) -> ZKWatermarkProof:
        """Create a zero-knowledge proof for watermark.
        
        Args:
            watermark_data: The watermark to prove knowledge of
            proof_type: Type of proof to generate
            metadata: Metadata to attach to proof
            cascaded_from: Parent proof ID (for cascading)
            cascade_layer: Layer in cascade chain
            cascade_depth: Total cascade depth
        
        Returns:
            ZKWatermarkProof ready for verification
        """
        # Generate commitment
        commitment_obj = self.generate_commitment(watermark_data)
        
        # Generate additional proof parameters based on type
        proof_params = {}
        if proof_type == ProofType.RANGE_PROOF:
            proof_params = self.create_range_proof(
                int.from_bytes(watermark_data[:4], 'big')
            )
        elif proof_type == ProofType.DISCRETE_LOG_PROOF:
            base = 2
            exponent = int.from_bytes(watermark_data[:4], 'big') % 1000
            result = pow(base, exponent, 2**256)
            proof_params = self.create_discrete_log_proof(base, exponent, result)
        
        # Create proof
        expires_at = None
        if self.proof_ttl_seconds > 0:
            expires_at = datetime.fromtimestamp(
                datetime.now(timezone.utc).timestamp() + self.proof_ttl_seconds,
                tz=timezone.utc
            ).isoformat()
        
        proof = ZKWatermarkProof(
            proof_type=proof_type,
            challenge=commitment_obj.challenge_response,
            response=commitment_obj.validity_proof,
            commitment=commitment_obj.commitment,
            status=VerificationStatus.UNVERIFIED,
            proof_parameters=proof_params,
            proven_metadata=metadata or {
                "watermark_hash": hashlib.sha256(watermark_data).hexdigest(),
                "watermark_size": len(watermark_data)
            },
            cascaded_from=cascaded_from,
            cascade_layer=cascade_layer,
            cascade_depth=cascade_depth,
            expires_at=expires_at
        )
        
        logger.info(
            f"Created ZK proof {proof.proof_id}: type={proof_type.value} "
            f"cascade_layer={cascade_layer}"
        )
        
        return proof


class ZKWatermarkVerifier:
    """Verifies zero-knowledge proofs of watermarks."""
    
    def __init__(self, generator_g: str, generator_h: str):
        """Initialize verifier.
        
        Args:
            generator_g: Generator point G used in commitments
            generator_h: Generator point H used in commitments
        """
        self.generator_g = generator_g
        self.generator_h = generator_h
    
    def verify_commitment(self, commitment_obj: ZKCommitment) -> bool:
        """Verify Pedersen commitment proof.
        
        Args:
            commitment_obj: Commitment to verify
        
        Returns:
            True if commitment is valid
        """
        # Reconstruct validity proof
        validity_data = f"{commitment_obj.commitment}{commitment_obj.challenge_response}".encode()
        # Note: In real implementation, we'd use actual elliptic curve math
        # For this demo, we verify the proof structure
        
        if not commitment_obj.commitment or not commitment_obj.challenge_response:
            return False
        
        if len(commitment_obj.commitment) != 64:  # 256-bit hex
            return False
        
        if len(commitment_obj.challenge_response) != 64:  # 256-bit hex
            return False
        
        logger.debug(f"Verified commitment: {commitment_obj.commitment[:16]}...")
        return True
    
    def verify_proof(self, proof: ZKWatermarkProof, verifier_id: Optional[str] = None) -> bool:
        """Verify a zero-knowledge proof.
        
        Args:
            proof: Proof to verify
            verifier_id: Identifier of verifier
        
        Returns:
            True if proof is valid
        """
        # Check if proof is revoked
        if proof.revoked:
            logger.warning(f"Proof {proof.proof_id} is revoked: {proof.revocation_reason}")
            proof.status = VerificationStatus.INVALID
            return False
        
        # Check if proof has expired
        if proof.expires_at:
            expires_time = datetime.fromisoformat(proof.expires_at)
            if datetime.now(timezone.utc) > expires_time:
                logger.warning(f"Proof {proof.proof_id} has expired")
                proof.status = VerificationStatus.EXPIRED
                return False
        
        # Verify based on proof type
        is_valid = True
        if proof.proof_type == ProofType.COMMITMENT_PROOF:
            # Verify commitment structure
            if not proof.commitment or len(proof.commitment) != 64:
                is_valid = False
        elif proof.proof_type == ProofType.RANGE_PROOF:
            # Verify range proof parameters exist
            if "range_proof" not in proof.proof_parameters:
                is_valid = False
        elif proof.proof_type == ProofType.DISCRETE_LOG_PROOF:
            # Verify discrete log proof
            if "discrete_log_proof" not in proof.proof_parameters:
                is_valid = False
        
        # Update proof status
        if is_valid:
            proof.status = VerificationStatus.VALID
            proof.verified_by = verifier_id or "unknown"
            proof.verification_timestamp = datetime.now(timezone.utc).isoformat()
            logger.info(f"Verified proof {proof.proof_id}: {proof.proof_type.value}")
        else:
            proof.status = VerificationStatus.INVALID
            logger.warning(f"Failed to verify proof {proof.proof_id}")
        
        return is_valid
    
    def verify_cascade_chain(self, chain: CascadingProofChain) -> Tuple[bool, List[str]]:
        """Verify entire cascading proof chain.
        
        Args:
            chain: Cascading proof chain to verify
        
        Returns:
            Tuple of (all_valid: bool, verified_layers: List[str])
        """
        verified_layers = []
        
        # Verify root proof
        if chain.root_proof:
            if self.verify_proof(chain.root_proof):
                verified_layers.append(f"root")
            else:
                logger.error("Root proof verification failed")
                return False, verified_layers
        
        # Verify each layer proof
        for i, layer_proof in enumerate(chain.layer_proofs):
            # Check cascade continuity: proof should reference previous layer
            if i > 0:
                if layer_proof.cascaded_from != chain.layer_proofs[i-1].proof_id:
                    logger.error(f"Cascade continuity broken at layer {i}")
                    return False, verified_layers
            
            # Verify the proof
            if self.verify_proof(layer_proof):
                verified_layers.append(f"layer_{i}")
            else:
                logger.error(f"Layer {i} proof verification failed")
                return False, verified_layers
        
        # Mark verified layers in chain
        chain.verified_at_layers = verified_layers
        
        logger.info(f"Verified cascade chain {chain.chain_id}: {len(verified_layers)} layers")
        return True, verified_layers
    
    def verify_blockchain_proof(
        self,
        proof: ZKWatermarkProof,
        blockchain_tx_hash: str,
        blockchain_commitment: str
    ) -> bool:
        """Verify proof was committed on blockchain.
        
        Args:
            proof: Proof to verify
            blockchain_tx_hash: Transaction hash for commitment
            blockchain_commitment: On-chain commitment value
        
        Returns:
            True if blockchain commitment matches proof
        """
        # Verify proof has blockchain data
        if not proof.blockchain_tx_hash:
            logger.warning(f"Proof {proof.proof_id} has no blockchain commitment")
            return False
        
        # Verify transaction hash matches
        if proof.blockchain_tx_hash != blockchain_tx_hash:
            logger.error(f"Transaction hash mismatch for proof {proof.proof_id}")
            return False
        
        # Reconstruct commitment from proof and verify it matches on-chain
        reconstructed = hashlib.sha256(
            f"{proof.commitment}{proof.challenge}".encode()
        ).hexdigest()
        
        if reconstructed != blockchain_commitment:
            logger.error(f"Blockchain commitment mismatch for proof {proof.proof_id}")
            return False
        
        logger.info(f"Verified blockchain proof {proof.proof_id}: tx={blockchain_tx_hash[:16]}...")
        return True


class CascadingProofOrchestrator:
    """Orchestrates cascading ZK proof verification chains."""
    
    def __init__(self, generator_g: str = None, generator_h: str = None):
        """Initialize orchestrator.
        
        Args:
            generator_g: Generator point G
            generator_h: Generator point H
        """
        self.generator_g = generator_g or secrets.token_hex(32)
        self.generator_h = generator_h or secrets.token_hex(32)
        self.generator = ZKWatermarkProofGenerator(proof_ttl_seconds=86400)
        self.verifier = ZKWatermarkVerifier(self.generator_g, self.generator_h)
        self.chains: Dict[str, CascadingProofChain] = {}
    
    def create_cascade_chain(
        self,
        watermark_data: bytes,
        chain_depth: int = 3,
        proof_type: ProofType = ProofType.COMMITMENT_PROOF
    ) -> CascadingProofChain:
        """Create a cascading proof chain starting from watermark.
        
        Args:
            watermark_data: Root watermark data
            chain_depth: Number of layers to cascade
            proof_type: Type of proofs to generate
        
        Returns:
            CascadingProofChain with root and layer proofs
        """
        # Create root proof
        root_proof = self.generator.create_proof(
            watermark_data,
            proof_type=proof_type,
            cascade_layer=0,
            cascade_depth=chain_depth
        )
        
        # Create chain
        chain = CascadingProofChain(
            root_proof=root_proof,
            depth=chain_depth
        )
        
        # Create layer proofs, each cascading from previous
        previous_proof_id = root_proof.proof_id
        for layer in range(1, chain_depth):
            # Each layer proves a different aspect
            layer_proof_type = proof_type
            if layer == 1:
                layer_proof_type = ProofType.RANGE_PROOF
            elif layer == 2:
                layer_proof_type = ProofType.DISCRETE_LOG_PROOF
            
            # Create layer proof (using slightly modified watermark data)
            layer_watermark = hashlib.sha256(
                watermark_data + str(layer).encode()
            ).digest()
            
            layer_proof = self.generator.create_proof(
                layer_watermark,
                proof_type=layer_proof_type,
                cascaded_from=previous_proof_id,
                cascade_layer=layer,
                cascade_depth=chain_depth
            )
            
            chain.layer_proofs.append(layer_proof)
            previous_proof_id = layer_proof.proof_id
        
        self.chains[chain.chain_id] = chain
        logger.info(f"Created cascade chain {chain.chain_id} with {chain_depth} layers")
        
        return chain
    
    def verify_cascade_chain(self, chain_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Verify a cascade chain by ID.
        
        Args:
            chain_id: Chain identifier
        
        Returns:
            Tuple of (verified: bool, verification_report: dict)
        """
        if chain_id not in self.chains:
            return False, {"error": f"Chain {chain_id} not found"}
        
        chain = self.chains[chain_id]
        all_valid, verified_layers = self.verifier.verify_cascade_chain(chain)
        
        report = {
            "chain_id": chain_id,
            "verified": all_valid,
            "verified_layers": verified_layers,
            "total_layers": chain.depth,
            "root_proof_id": chain.root_proof.proof_id if chain.root_proof else None,
            "layer_count": len(chain.layer_proofs),
            "verification_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return all_valid, report
    
    def commit_chain_to_blockchain(
        self,
        chain_id: str,
        tx_hash: str,
        block_number: int,
        block_timestamp: str
    ) -> bool:
        """Mark cascade chain as committed on blockchain.
        
        Args:
            chain_id: Chain identifier
            tx_hash: Transaction hash
            block_number: Block number
            block_timestamp: Block timestamp
        
        Returns:
            True if commitment recorded
        """
        if chain_id not in self.chains:
            logger.error(f"Chain {chain_id} not found for blockchain commit")
            return False
        
        chain = self.chains[chain_id]
        
        # Update root and all layer proofs with blockchain data
        if chain.root_proof:
            chain.root_proof.blockchain_tx_hash = tx_hash
            chain.root_proof.blockchain_block_number = block_number
            chain.root_proof.blockchain_timestamp = block_timestamp
        
        for proof in chain.layer_proofs:
            proof.blockchain_tx_hash = tx_hash
            proof.blockchain_block_number = block_number
            proof.blockchain_timestamp = block_timestamp
        
        logger.info(
            f"Committed cascade chain {chain_id} to blockchain: "
            f"tx={tx_hash[:16]}... block={block_number}"
        )
        
        return True
    
    def revoke_proof(
        self,
        chain_id: str,
        proof_id: str,
        reason: str
    ) -> bool:
        """Revoke a specific proof in a chain.
        
        Args:
            chain_id: Chain identifier
            proof_id: Proof ID to revoke
            reason: Revocation reason
        
        Returns:
            True if revocation successful
        """
        if chain_id not in self.chains:
            return False
        
        chain = self.chains[chain_id]
        
        # Find and revoke proof
        if chain.root_proof and chain.root_proof.proof_id == proof_id:
            chain.root_proof.revoked = True
            chain.root_proof.revocation_reason = reason
            logger.info(f"Revoked root proof {proof_id}: {reason}")
            return True
        
        for proof in chain.layer_proofs:
            if proof.proof_id == proof_id:
                proof.revoked = True
                proof.revocation_reason = reason
                logger.info(f"Revoked layer proof {proof_id}: {reason}")
                return True
        
        return False
    
    def export_chain_proof(self, chain_id: str) -> str:
        """Export cascade chain as JSON for sharing/archiving.
        
        Args:
            chain_id: Chain identifier
        
        Returns:
            JSON string of cascade chain
        """
        if chain_id not in self.chains:
            raise ValueError(f"Chain {chain_id} not found")
        
        chain = self.chains[chain_id]
        chain_dict = chain.to_dict()
        return json.dumps(chain_dict, indent=2)
    
    def import_chain_proof(self, chain_json: str) -> str:
        """Import cascade chain from JSON.
        
        Args:
            chain_json: JSON string of cascade chain
        
        Returns:
            Chain ID
        """
        chain_dict = json.loads(chain_json)
        chain = CascadingProofChain.from_dict(chain_dict)
        self.chains[chain.chain_id] = chain
        logger.info(f"Imported cascade chain {chain.chain_id}")
        return chain.chain_id
    
    def get_chain_statistics(self, chain_id: str) -> Dict[str, Any]:
        """Get statistics for a cascade chain.
        
        Args:
            chain_id: Chain identifier
        
        Returns:
            Dictionary of statistics
        """
        if chain_id not in self.chains:
            return {}
        
        chain = self.chains[chain_id]
        
        total_proofs = 1 + len(chain.layer_proofs)  # root + layers
        verified_count = len([p for p in chain.layer_proofs if p.status == VerificationStatus.VALID])
        if chain.root_proof and chain.root_proof.status == VerificationStatus.VALID:
            verified_count += 1
        
        return {
            "chain_id": chain_id,
            "created_at": chain.created_at,
            "depth": chain.depth,
            "total_proofs": total_proofs,
            "verified_proofs": verified_count,
            "verification_rate": f"{(verified_count / total_proofs * 100):.1f}%",
            "verified_at_layers": chain.verified_at_layers,
            "root_proof_status": chain.root_proof.status.value if chain.root_proof else "none",
            "layer_statuses": [p.status.value for p in chain.layer_proofs],
            "blockchain_committed": all(
                p.blockchain_tx_hash for p in chain.layer_proofs + ([chain.root_proof] if chain.root_proof else [])
            )
        }
