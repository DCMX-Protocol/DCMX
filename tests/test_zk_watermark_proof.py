"""
Tests for Zero-Knowledge Watermark Proof System with Cascading Verification
"""

import pytest
import asyncio
import json
from dcmx.audio.zk_watermark_proof import (
    ZKWatermarkProofGenerator,
    ZKWatermarkVerifier,
    CascadingProofOrchestrator,
    ZKWatermarkProof,
    CascadingProofChain,
    ZKCommitment,
    ProofType,
    VerificationStatus
)
from datetime import datetime, timezone, timedelta


@pytest.fixture
def watermark_data():
    """Sample watermark data."""
    return b"This is a test watermark for DCMX music NFT"


@pytest.fixture
def generator():
    """Create proof generator."""
    return ZKWatermarkProofGenerator(proof_ttl_seconds=86400)


@pytest.fixture
def verifier(generator):
    """Create proof verifier."""
    return ZKWatermarkVerifier(generator.generator_g, generator.generator_h)


@pytest.fixture
def orchestrator():
    """Create cascade proof orchestrator."""
    return CascadingProofOrchestrator()


class TestZKCommitment:
    """Test Pedersen commitment generation."""
    
    def test_commitment_generation(self, generator, watermark_data):
        """Test basic commitment generation."""
        commitment = generator.generate_commitment(watermark_data)
        
        assert commitment.commitment
        assert commitment.blinding_factor
        assert commitment.challenge_response
        assert commitment.validity_proof
        assert len(commitment.commitment) == 64  # 256-bit hex
    
    def test_commitment_reproducibility(self, generator, watermark_data):
        """Test commitment is reproducible with same seed."""
        seed = b"test_seed_12345"
        
        commitment1 = generator.generate_commitment(watermark_data, seed)
        commitment2 = generator.generate_commitment(watermark_data, seed)
        
        # Same seed should produce same commitment
        assert commitment1.commitment == commitment2.commitment
    
    def test_commitment_uniqueness(self, generator, watermark_data):
        """Test different seeds produce different commitments."""
        commitment1 = generator.generate_commitment(watermark_data, b"seed1")
        commitment2 = generator.generate_commitment(watermark_data, b"seed2")
        
        # Different seeds should produce different commitments
        assert commitment1.commitment != commitment2.commitment
    
    def test_commitment_structure(self, generator, watermark_data):
        """Test commitment has all required fields."""
        commitment = generator.generate_commitment(watermark_data)
        
        assert hasattr(commitment, 'commitment')
        assert hasattr(commitment, 'blinding_factor')
        assert hasattr(commitment, 'challenge_response')
        assert hasattr(commitment, 'validity_proof')
        assert hasattr(commitment, 'created_at')
    
    def test_commitment_serialization(self, generator, watermark_data):
        """Test commitment can be serialized to dict."""
        commitment = generator.generate_commitment(watermark_data)
        commit_dict = commitment.__dict__
        
        assert commit_dict['commitment']
        assert commit_dict['blinding_factor']
        assert 'created_at' in commit_dict


class TestZKWatermarkProof:
    """Test zero-knowledge proof generation and structure."""
    
    def test_proof_creation(self, generator, watermark_data):
        """Test basic proof creation."""
        proof = generator.create_proof(watermark_data)
        
        assert proof.proof_id
        assert proof.proof_type == ProofType.COMMITMENT_PROOF
        assert proof.commitment
        assert proof.status == VerificationStatus.UNVERIFIED
    
    def test_proof_types(self, generator, watermark_data):
        """Test different proof types can be created."""
        proof_types = [
            ProofType.COMMITMENT_PROOF,
            ProofType.RANGE_PROOF,
            ProofType.DISCRETE_LOG_PROOF
        ]
        
        for proof_type in proof_types:
            proof = generator.create_proof(watermark_data, proof_type=proof_type)
            assert proof.proof_type == proof_type
    
    def test_proof_ttl(self):
        """Test proof expiration TTL."""
        generator_ttl = ZKWatermarkProofGenerator(proof_ttl_seconds=60)
        proof = generator_ttl.create_proof(b"test")
        
        assert proof.expires_at
        expires_time = datetime.fromisoformat(proof.expires_at)
        now = datetime.now(timezone.utc)
        # Should expire around 60 seconds from now
        delta = (expires_time - now).total_seconds()
        assert 55 < delta < 65
    
    def test_proof_metadata(self, generator, watermark_data):
        """Test proof can carry metadata."""
        metadata = {
            "artist": "Test Artist",
            "title": "Test Track",
            "nft_id": "0x123"
        }
        
        proof = generator.create_proof(watermark_data, metadata=metadata)
        
        assert proof.proven_metadata["artist"] == "Test Artist"
        assert proof.proven_metadata["title"] == "Test Track"
    
    def test_proof_serialization(self, generator, watermark_data):
        """Test proof can be serialized to dict."""
        proof = generator.create_proof(watermark_data)
        proof_dict = proof.to_dict()
        
        assert proof_dict['proof_id'] == proof.proof_id
        assert proof_dict['proof_type'] == 'commitment_proof'
        assert proof_dict['status'] == 'unverified'
    
    def test_proof_deserialization(self, generator, watermark_data):
        """Test proof can be deserialized from dict."""
        proof1 = generator.create_proof(watermark_data)
        proof_dict = proof1.to_dict()
        
        proof2 = ZKWatermarkProof.from_dict(proof_dict)
        
        assert proof2.proof_id == proof1.proof_id
        assert proof2.proof_type == proof1.proof_type
        assert proof2.status == proof1.status


class TestZKWatermarkVerifier:
    """Test proof verification."""
    
    def test_commitment_verification(self, generator, verifier, watermark_data):
        """Test commitment verification."""
        commitment = generator.generate_commitment(watermark_data)
        
        assert verifier.verify_commitment(commitment)
    
    def test_proof_verification(self, generator, verifier, watermark_data):
        """Test proof verification."""
        proof = generator.create_proof(watermark_data)
        
        is_valid = verifier.verify_proof(proof)
        
        assert is_valid
        assert proof.status == VerificationStatus.VALID
        assert proof.verified_by == "unknown"
        assert proof.verification_timestamp
    
    def test_proof_verification_with_verifier_id(self, generator, verifier, watermark_data):
        """Test proof verification records verifier ID."""
        proof = generator.create_proof(watermark_data)
        
        verifier.verify_proof(proof, verifier_id="blockchain_validator")
        
        assert proof.verified_by == "blockchain_validator"
    
    def test_invalid_proof_rejection(self, generator, verifier):
        """Test invalid proofs are rejected."""
        proof = ZKWatermarkProof()
        proof.commitment = "invalid"  # Too short
        
        is_valid = verifier.verify_proof(proof)
        
        assert not is_valid
        assert proof.status == VerificationStatus.INVALID
    
    def test_expired_proof_rejection(self, verifier):
        """Test expired proofs are rejected."""
        generator_ttl = ZKWatermarkProofGenerator(proof_ttl_seconds=0)
        proof = generator_ttl.create_proof(b"test")
        
        # Move expiration time to past
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        proof.expires_at = past_time.isoformat()
        
        is_valid = verifier.verify_proof(proof)
        
        assert not is_valid
        assert proof.status == VerificationStatus.EXPIRED
    
    def test_revoked_proof_rejection(self, generator, verifier, watermark_data):
        """Test revoked proofs are rejected."""
        proof = generator.create_proof(watermark_data)
        proof.revoked = True
        proof.revocation_reason = "Compromised watermark"
        
        is_valid = verifier.verify_proof(proof)
        
        assert not is_valid
        assert proof.status == VerificationStatus.INVALID


class TestCascadingProofChain:
    """Test cascading proof chain creation and verification."""
    
    def test_cascade_chain_creation(self, orchestrator, watermark_data):
        """Test cascade chain creation."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=3)
        
        assert chain.chain_id
        assert chain.root_proof is not None
        assert len(chain.layer_proofs) == 2  # depth-1 layers
        assert chain.depth == 3
    
    def test_cascade_chain_proof_types(self, orchestrator, watermark_data):
        """Test cascade chain has varied proof types."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=3)
        
        # Root should be commitment proof
        assert chain.root_proof.proof_type == ProofType.COMMITMENT_PROOF
        
        # Layer 1 should be range proof
        assert chain.layer_proofs[0].proof_type == ProofType.RANGE_PROOF
        
        # Layer 2 should be discrete log proof
        assert chain.layer_proofs[1].proof_type == ProofType.DISCRETE_LOG_PROOF
    
    def test_cascade_continuity(self, orchestrator, watermark_data):
        """Test cascade chain maintains proof continuity."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=3)
        
        # Each layer should reference previous layer
        for i, proof in enumerate(chain.layer_proofs):
            if i == 0:
                assert proof.cascaded_from == chain.root_proof.proof_id
            else:
                assert proof.cascaded_from == chain.layer_proofs[i-1].proof_id
    
    def test_cascade_verification(self, orchestrator, watermark_data):
        """Test cascade chain verification."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=3)
        
        verified, report = orchestrator.verify_cascade_chain(chain.chain_id)
        
        assert verified
        assert "root" in report["verified_layers"]
        assert f"layer_0" in report["verified_layers"]
        assert f"layer_1" in report["verified_layers"]
    
    def test_cascade_chain_serialization(self, orchestrator, watermark_data):
        """Test cascade chain can be serialized."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=3)
        
        chain_json = orchestrator.export_chain_proof(chain.chain_id)
        chain_dict = json.loads(chain_json)
        
        assert chain_dict['chain_id'] == chain.chain_id
        assert chain_dict['depth'] == 3
        assert chain_dict['root_proof'] is not None
        assert len(chain_dict['layer_proofs']) == 2


class TestCascadingProofOrchestrator:
    """Test cascade proof orchestration."""
    
    def test_blockchain_commitment(self, orchestrator, watermark_data):
        """Test cascade chain blockchain commitment."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=2)
        
        # Commit to blockchain
        tx_hash = "0x" + "a" * 64
        block_number = 12345
        block_time = datetime.now(timezone.utc).isoformat()
        
        committed = orchestrator.commit_chain_to_blockchain(
            chain.chain_id,
            tx_hash,
            block_number,
            block_time
        )
        
        assert committed
        assert chain.root_proof.blockchain_tx_hash == tx_hash
        assert chain.root_proof.blockchain_block_number == block_number
        assert chain.layer_proofs[0].blockchain_tx_hash == tx_hash
    
    def test_proof_revocation(self, orchestrator, watermark_data):
        """Test proof revocation in cascade chain."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=2)
        proof_id = chain.layer_proofs[0].proof_id
        
        revoked = orchestrator.revoke_proof(
            chain.chain_id,
            proof_id,
            "Watermark compromised"
        )
        
        assert revoked
        assert chain.layer_proofs[0].revoked
        assert chain.layer_proofs[0].revocation_reason == "Watermark compromised"
    
    def test_chain_statistics(self, orchestrator, watermark_data):
        """Test cascade chain statistics."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=3)
        
        # Verify chain
        orchestrator.verify_cascade_chain(chain.chain_id)
        
        stats = orchestrator.get_chain_statistics(chain.chain_id)
        
        assert stats['chain_id'] == chain.chain_id
        assert stats['depth'] == 3
        assert stats['total_proofs'] == 3  # root + 2 layers
        assert stats['verified_proofs'] > 0
    
    def test_chain_import_export(self, orchestrator, watermark_data):
        """Test cascade chain import/export."""
        # Create and export chain
        chain1 = orchestrator.create_cascade_chain(watermark_data, chain_depth=2)
        chain_json = orchestrator.export_chain_proof(chain1.chain_id)
        
        # Import into new orchestrator
        new_orchestrator = CascadingProofOrchestrator()
        imported_chain_id = new_orchestrator.import_chain_proof(chain_json)
        
        # Verify imported chain
        imported_chain = new_orchestrator.chains[imported_chain_id]
        assert imported_chain.depth == 2
        assert len(imported_chain.layer_proofs) == 1
    
    def test_multiple_chains(self, orchestrator, watermark_data):
        """Test orchestrator can manage multiple cascade chains."""
        chain1 = orchestrator.create_cascade_chain(watermark_data, chain_depth=2)
        chain2 = orchestrator.create_cascade_chain(watermark_data + b"_2", chain_depth=3)
        
        assert chain1.chain_id != chain2.chain_id
        assert len(orchestrator.chains) == 2
        
        # Verify both chains independently
        verified1, _ = orchestrator.verify_cascade_chain(chain1.chain_id)
        verified2, _ = orchestrator.verify_cascade_chain(chain2.chain_id)
        
        assert verified1
        assert verified2


class TestRangeProof:
    """Test range proof generation."""
    
    def test_range_proof_creation(self, generator):
        """Test range proof creation."""
        range_proof = generator.create_range_proof(
            value=500,
            min_val=0,
            max_val=1000
        )
        
        assert range_proof['range_proof']
        assert range_proof['min_value'] == '0'
        assert range_proof['max_value'] == '1000'
        assert 'bit_commitments' in range_proof
    
    def test_range_proof_parameters(self, generator):
        """Test range proof has correct parameters."""
        range_proof = generator.create_range_proof(
            value=100,
            min_val=0,
            max_val=256
        )
        
        bit_count = int(range_proof['bit_count'])
        # 256 requires 9 bits (0-256 range is 257 values, needing 9 bits)
        assert bit_count == 9


class TestDiscreteLogProof:
    """Test discrete log proof generation."""
    
    def test_discrete_log_proof_creation(self, generator):
        """Test discrete log proof creation."""
        base = 2
        exponent = 10
        result = pow(base, exponent, 2**256)
        
        dl_proof = generator.create_discrete_log_proof(base, exponent, result)
        
        assert dl_proof['discrete_log_proof']
        assert dl_proof['challenge']
        assert dl_proof['base'] == '2'
        assert dl_proof['result'] == str(result)


class TestProofIntegration:
    """Integration tests for complete proof workflows."""
    
    def test_end_to_end_cascade_verification(self, orchestrator, watermark_data):
        """Test complete cascade proof workflow."""
        # 1. Create cascade chain
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=3)
        
        # 2. Verify cascade
        verified, report = orchestrator.verify_cascade_chain(chain.chain_id)
        assert verified
        
        # 3. Get statistics
        stats = orchestrator.get_chain_statistics(chain.chain_id)
        assert stats['verification_rate'] == "100.0%"
        
        # 4. Commit to blockchain
        orchestrator.commit_chain_to_blockchain(
            chain.chain_id,
            "0x" + "b" * 64,
            99999,
            datetime.now(timezone.utc).isoformat()
        )
        
        # 5. Export and verify
        chain_json = orchestrator.export_chain_proof(chain.chain_id)
        assert chain.chain_id in chain_json
    
    def test_cascade_chain_across_watermarks(self, orchestrator):
        """Test cascade chains for different watermarks."""
        watermarks = [
            b"watermark_1",
            b"watermark_2",
            b"watermark_3"
        ]
        
        chains = []
        for wm in watermarks:
            chain = orchestrator.create_cascade_chain(wm, chain_depth=2)
            chains.append(chain)
        
        # Verify all chains independently
        for chain in chains:
            verified, _ = orchestrator.verify_cascade_chain(chain.chain_id)
            assert verified
        
        assert len(orchestrator.chains) == 3


class TestProofDataStructures:
    """Test data structure serialization and integrity."""
    
    def test_proof_chain_to_dict(self, orchestrator, watermark_data):
        """Test cascade chain serialization."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=2)
        chain_dict = chain.to_dict()
        
        assert isinstance(chain_dict, dict)
        assert 'chain_id' in chain_dict
        assert 'root_proof' in chain_dict
        assert 'layer_proofs' in chain_dict
    
    def test_proof_chain_from_dict(self, orchestrator, watermark_data):
        """Test cascade chain deserialization."""
        chain1 = orchestrator.create_cascade_chain(watermark_data, chain_depth=2)
        chain_dict = chain1.to_dict()
        
        chain2 = CascadingProofChain.from_dict(chain_dict)
        
        assert chain2.chain_id == chain1.chain_id
        assert chain2.depth == chain1.depth
        assert len(chain2.layer_proofs) == len(chain1.layer_proofs)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_watermark(self, generator):
        """Test handling of empty watermark."""
        proof = generator.create_proof(b"")
        
        assert proof is not None
        assert proof.commitment
    
    def test_large_watermark(self, generator):
        """Test handling of large watermark."""
        large_watermark = b"x" * 1000000  # 1MB
        
        proof = generator.create_proof(large_watermark)
        
        assert proof is not None
        assert proof.proven_metadata['watermark_size'] == 1000000
    
    def test_cascade_single_layer(self, orchestrator, watermark_data):
        """Test cascade with depth 1 (no layers)."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=1)
        
        assert chain.root_proof is not None
        assert len(chain.layer_proofs) == 0
    
    def test_cascade_deep_chain(self, orchestrator, watermark_data):
        """Test cascade with many layers."""
        chain = orchestrator.create_cascade_chain(watermark_data, chain_depth=5)
        
        verified, _ = orchestrator.verify_cascade_chain(chain.chain_id)
        assert verified
        assert len(chain.layer_proofs) == 4
