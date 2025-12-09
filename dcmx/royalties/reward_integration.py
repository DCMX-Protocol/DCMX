"""
DCMX Reward Claim Integration with ZK Verification.

Integrates the royalty system with:
- Zero-knowledge proofs (from lora_node)
- Blockchain smart contracts
- Verifier node quorum approval
- Token minting on-chain
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import json

from dcmx.royalties.royalty_structure import (
    RoyaltyPaymentStructure,
    RewardClaim,
    RewardType,
    SharingReward,
    ListeningReward,
    BandwidthReward,
)

logger = logging.getLogger(__name__)


class VerifierNodeStatus(Enum):
    """Status of verifier node in quorum."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_MORE_INFO = "needs_more_info"


@dataclass
class VerifierApproval:
    """Approval from one verifier node on reward claim."""
    verifier_node_id: str  # Which node is verifying
    claim_id: str  # Which claim being verified
    status: VerifierNodeStatus
    zk_proof_result: bool  # ZK proof valid?
    verification_timestamp: str
    notes: str = ""  # Any additional notes
    signature: str = ""  # Verifier's digital signature


class RewardClaimVerifier:
    """
    Manages reward claim verification using quorum of verifier nodes.
    
    Flow:
    1. User submits claim with ZK proof
    2. Claim distributed to 4 verifier nodes
    3. Each node independently verifies ZK proof
    4. If 3+ approve, claim approved and tokens minted
    5. Tokens transferred to user's blockchain wallet
    """
    
    def __init__(self, royalty_structure: RoyaltyPaymentStructure):
        """Initialize verifier with link to royalty system."""
        self.royalty = royalty_structure
        self.verifier_approvals: Dict[str, List[VerifierApproval]] = {}
        self.verifier_nodes: List[str] = []
        
        logger.info("RewardClaimVerifier initialized")
    
    def register_verifier_node(self, node_id: str) -> None:
        """Register a verifier node to participate in quorum."""
        self.verifier_nodes.append(node_id)
        logger.info(f"Registered verifier node: {node_id}")
    
    def distribute_claim_to_verifiers(self, claim_id: str) -> List[str]:
        """
        Distribute claim to all verifier nodes for approval.
        
        Args:
            claim_id: ID of reward claim to verify
            
        Returns:
            List of verifier node IDs that will verify
        """
        if claim_id not in self.verifier_approvals:
            self.verifier_approvals[claim_id] = []
        
        logger.info(f"Distributing claim {claim_id} to {len(self.verifier_nodes)} verifiers")
        return self.verifier_nodes
    
    def submit_verifier_approval(
        self,
        verifier_node_id: str,
        claim_id: str,
        status: VerifierNodeStatus,
        zk_proof_result: bool,
        notes: str = ""
    ) -> bool:
        """
        Submit approval from verifier node.
        
        Called by each verifier node after it checks the ZK proof.
        
        Args:
            verifier_node_id: Which verifier is submitting
            claim_id: Which claim is being approved
            status: APPROVED, REJECTED, PENDING, or NEEDS_MORE_INFO
            zk_proof_result: True if ZK proof is valid
            notes: Any notes from verifier
            
        Returns:
            True if approval recorded
        """
        if claim_id not in self.verifier_approvals:
            self.verifier_approvals[claim_id] = []
        
        approval = VerifierApproval(
            verifier_node_id=verifier_node_id,
            claim_id=claim_id,
            status=status,
            zk_proof_result=zk_proof_result,
            verification_timestamp=datetime.utcnow().isoformat(),
            notes=notes
        )
        
        self.verifier_approvals[claim_id].append(approval)
        
        logger.info(
            f"Verifier approval submitted: {verifier_node_id} → {claim_id} "
            f"(status: {status.value}, zk_proof: {zk_proof_result})"
        )
        
        # Check if quorum reached
        self._check_quorum_and_approve(claim_id)
        
        return True
    
    def _check_quorum_and_approve(self, claim_id: str) -> Optional[bool]:
        """
        Check if quorum reached (3-of-4 verifiers approve) and approve claim.
        
        Requires:
        - At least 3 of 4 verifiers submitted approval
        - At least 2 of 3 approved
        - ZK proof valid
        
        Args:
            claim_id: Claim to check
            
        Returns:
            True if claim approved, False if rejected, None if not ready
        """
        approvals = self.verifier_approvals.get(claim_id, [])
        
        if len(approvals) < 3:
            # Not enough verifiers yet
            return None
        
        # Count approvals
        approved = [a for a in approvals if a.status == VerifierNodeStatus.APPROVED]
        rejected = [a for a in approvals if a.status == VerifierNodeStatus.REJECTED]
        zk_valid = [a for a in approvals if a.zk_proof_result]
        
        # Approval requires:
        # - 2+ verifiers approved
        # - ZK proof valid from 2+ verifiers
        if len(approved) >= 2 and len(zk_valid) >= 2:
            claim = self.royalty.reward_claims.get(claim_id)
            if claim:
                claim.proof_verified = True
                logger.info(f"QUORUM REACHED: Claim {claim_id} approved! ({len(approved)}/4 approved)")
                return True
        elif len(rejected) >= 2:
            # Rejected by quorum
            logger.warning(f"QUORUM REJECTED: Claim {claim_id} rejected ({len(rejected)}/4 rejected)")
            return False
        
        return None
    
    def get_claim_verification_status(self, claim_id: str) -> Dict:
        """Get verification status of a claim."""
        approvals = self.verifier_approvals.get(claim_id, [])
        claim = self.royalty.reward_claims.get(claim_id)
        
        if not claim:
            return {"error": "Claim not found"}
        
        approved = len([a for a in approvals if a.status == VerifierNodeStatus.APPROVED])
        rejected = len([a for a in approvals if a.status == VerifierNodeStatus.REJECTED])
        
        return {
            "claim_id": claim_id,
            "claimant": claim.claimant_wallet[:20] + "...",
            "claim_type": claim.claim_type.value,
            "total_tokens_claimed": claim.total_tokens_claimed,
            "approvals": approved,
            "rejections": rejected,
            "verifiers_responded": len(approvals),
            "status": "APPROVED" if claim.proof_verified else "PENDING",
            "verifier_details": [
                {
                    "verifier": a.verifier_node_id[:10] + "...",
                    "status": a.status.value,
                    "zk_proof_valid": a.zk_proof_result
                }
                for a in approvals
            ]
        }


class BlockchainIntegration:
    """
    Interfaces with blockchain smart contracts for:
    - NFT minting (ERC-721)
    - Token reward minting (ERC-20)
    - Royalty distribution
    - Secondary market enforcement
    """
    
    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        nft_contract_address: str,
        token_contract_address: str,
        royalty_distributor_address: str
    ):
        """
        Initialize blockchain integration.
        
        Args:
            rpc_url: Ethereum/Polygon RPC endpoint
            private_key: Private key for transactions
            nft_contract_address: ERC-721 contract (MusicNFT.sol)
            token_contract_address: ERC-20 contract (DCMXToken.sol)
            royalty_distributor_address: Royalty distribution contract
        """
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.nft_contract = nft_contract_address
        self.token_contract = token_contract_address
        self.royalty_distributor = royalty_distributor_address
        
        logger.info(f"BlockchainIntegration initialized (RPC: {rpc_url})")
    
    async def mint_nft_certificate(
        self,
        song_title: str,
        song_content_hash: str,
        watermark_hash: str,
        edition_number: int,
        max_editions: int,
        receiver_wallet: str
    ) -> Tuple[str, int]:
        """
        Mint NFT certificate on blockchain.
        
        Creates ERC-721 token representing music ownership.
        
        Args:
            song_title: Name of song
            song_content_hash: SHA256 of audio
            watermark_hash: Proof of watermarking
            edition_number: Edition number (1-100)
            max_editions: Total editions
            receiver_wallet: Buyer's wallet
            
        Returns:
            Tuple of (transaction_hash, token_id)
        """
        logger.info(
            f"Minting NFT: {song_title} Edition {edition_number}/{max_editions} "
            f"to {receiver_wallet[:20]}..."
        )
        
        # In real implementation, would call contract via web3.py:
        # tx = nft_contract.functions.mint(
        #     receiver_wallet,
        #     song_content_hash,
        #     watermark_hash,
        #     edition_number,
        #     max_editions
        # ).build_transaction({...})
        # tx_hash = w3.eth.send_raw_transaction(...)
        
        # Mock implementation
        tx_hash = f"0x{'mock_tx_' + song_content_hash[:60]}"
        token_id = edition_number
        
        return (tx_hash, token_id)
    
    async def distribute_royalties(
        self,
        payment_id: str,
        artist_wallet: str,
        artist_amount: float,
        platform_wallet: str,
        platform_amount: float,
        node_operator_pool: str,
        node_operator_amount: float
    ) -> str:
        """
        Distribute royalties to all recipients on blockchain.
        
        Uses smart contract to atomically split payment.
        
        Args:
            payment_id: Payment ID for tracking
            artist_wallet: Where to send artist royalties
            artist_amount: Amount in USD (will be converted to tokens)
            platform_wallet: Where to send platform fees
            platform_amount: Amount in USD
            node_operator_pool: Pool wallet for node operators
            node_operator_amount: Amount in USD
            
        Returns:
            Transaction hash
        """
        logger.info(
            f"Distributing royalties ({payment_id}): "
            f"Artist ${artist_amount:.2f} | Platform ${platform_amount:.2f} | "
            f"Nodes ${node_operator_amount:.2f}"
        )
        
        # In real implementation, would call smart contract:
        # tx = royalty_distributor.functions.distributeRoyalties(
        #     artist_wallet,
        #     int(artist_amount * 100),  # in cents
        #     platform_wallet,
        #     int(platform_amount * 100),
        #     node_operator_pool,
        #     int(node_operator_amount * 100)
        # ).build_transaction({...})
        
        tx_hash = f"0x{'royalty_' + payment_id[:58]}"
        
        return tx_hash
    
    async def mint_reward_tokens(
        self,
        recipient_wallet: str,
        token_amount: float,
        reason: str  # "sharing", "listening", "bandwidth"
    ) -> str:
        """
        Mint reward tokens for user.
        
        Called after verifier quorum approves reward claim.
        
        Args:
            recipient_wallet: User's wallet
            token_amount: Number of DCMX tokens to mint
            reason: Why tokens are being minted
            
        Returns:
            Transaction hash
        """
        logger.info(
            f"Minting reward tokens: {recipient_wallet[:20]}... "
            f"({token_amount} DCMX tokens for {reason})"
        )
        
        # In real implementation:
        # tx = token_contract.functions.mint(
        #     recipient_wallet,
        #     int(token_amount * 10**18)  # Convert to wei
        # ).build_transaction({...})
        
        tx_hash = f"0x{'mint_' + str(token_amount)[:54]}"
        
        return tx_hash
    
    async def set_royalty_enforcement(
        self,
        token_id: int,
        artist_wallet: str,
        royalty_percentage: int  # e.g., 70 for 70%
    ) -> str:
        """
        Set up ERC-2981 royalty enforcement for secondary sales.
        
        Ensures artist receives % of all future resales.
        
        Args:
            token_id: NFT token ID
            artist_wallet: Artist's wallet (receives royalties)
            royalty_percentage: Percentage (70 for 70%)
            
        Returns:
            Transaction hash
        """
        logger.info(
            f"Setting ERC-2981 royalty: Token {token_id} → "
            f"Artist {artist_wallet[:20]}... ({royalty_percentage}%)"
        )
        
        # In real implementation:
        # tx = nft_contract.functions.setTokenRoyalty(
        #     token_id,
        #     artist_wallet,
        #     royalty_percentage * 100  # ERC-2981 uses basis points
        # ).build_transaction({...})
        
        tx_hash = f"0x{'royalty_' + str(token_id)[:60]}"
        
        return tx_hash


class RewardDistributionEngine:
    """
    Orchestrates entire reward and royalty distribution flow.
    
    Coordinates:
    1. ZK proof generation and verification
    2. Verifier node quorum approval
    3. Blockchain token minting
    4. Royalty smart contract interactions
    """
    
    def __init__(
        self,
        royalty_structure: RoyaltyPaymentStructure,
        claim_verifier: RewardClaimVerifier,
        blockchain: BlockchainIntegration
    ):
        """Initialize distribution engine."""
        self.royalty = royalty_structure
        self.verifier = claim_verifier
        self.blockchain = blockchain
        
        logger.info("RewardDistributionEngine initialized")
    
    async def process_sharing_reward(
        self,
        sharer_wallet: str,
        song_content_hash: str,
        shared_with_wallet: str
    ) -> SharingReward:
        """
        Process sharing event and create reward claim.
        
        Args:
            sharer_wallet: User sharing song
            song_content_hash: Which song
            shared_with_wallet: Recipient
            
        Returns:
            SharingReward object
        """
        # 1. Record sharing event
        reward = self.royalty.record_sharing_event(
            sharer_wallet=sharer_wallet,
            song_content_hash=song_content_hash,
            shared_with_wallet=shared_with_wallet,
            base_reward=1
        )
        
        # 2. Would integrate with LoRa node to generate ZK proof:
        # zk_proof = await lora_node.generate_freshness_proof(
        #     message={"sharer": sharer_wallet, "song": song_content_hash},
        #     nonce_depth=5
        # )
        
        logger.info(f"Sharing reward recorded: {reward.reward_id}")
        
        return reward
    
    async def process_listening_reward(
        self,
        listener_wallet: str,
        song_content_hash: str,
        sharer_wallet: str,
        listen_duration_seconds: int,
        completion_percentage: float
    ) -> ListeningReward:
        """
        Process listening event and create reward claim.
        
        Args:
            listener_wallet: User who listened
            song_content_hash: Which song
            sharer_wallet: Who shared the song
            listen_duration_seconds: How long listened
            completion_percentage: % completed (0-100)
            
        Returns:
            ListeningReward object
        """
        # 1. Record listening event
        reward = self.royalty.record_listening_event(
            listener_wallet=listener_wallet,
            song_content_hash=song_content_hash,
            sharer_wallet=sharer_wallet,
            listen_duration_seconds=listen_duration_seconds,
            completion_percentage=completion_percentage,
            base_reward=2
        )
        
        # 2. Apply multiplier to sharer's reward if listened
        if completion_percentage >= 50:
            # Sharer gets 1.5x bonus
            sharing_rewards = [
                r for r in self.royalty.sharing_rewards.values()
                if r.sharer_wallet == sharer_wallet and r.shared_with_wallet == listener_wallet
            ]
            for sr in sharing_rewards:
                self.royalty.apply_listening_multiplier(sr.reward_id, multiplier=1.5)
        
        logger.info(f"Listening reward recorded: {reward.reward_id}")
        
        return reward
    
    async def process_bandwidth_reward(
        self,
        node_id: str,
        song_content_hash: str,
        bytes_served: int,
        listeners_served: int,
        transmission_time_seconds: int
    ) -> BandwidthReward:
        """
        Process bandwidth serving and create reward claim.
        
        Args:
            node_id: LoRa node that served content
            song_content_hash: Which content
            bytes_served: Bytes transmitted
            listeners_served: Number of listeners
            transmission_time_seconds: Service duration
            
        Returns:
            BandwidthReward object
        """
        # 1. Record bandwidth event
        reward = self.royalty.record_bandwidth_serving(
            node_id=node_id,
            song_content_hash=song_content_hash,
            bytes_served=bytes_served,
            listeners_served=listeners_served,
            transmission_time_seconds=transmission_time_seconds,
            base_reward=5
        )
        
        logger.info(f"Bandwidth reward recorded: {reward.reward_id}")
        
        return reward
    
    async def submit_and_verify_claim(
        self,
        claimant_wallet: str,
        claim_type: RewardType,
        song_content_hash: str,
        total_tokens_claimed: float,
        zk_proof_data: Dict
    ) -> Optional[str]:
        """
        Submit reward claim with ZK proof and distribute to verifiers.
        
        Args:
            claimant_wallet: User claiming rewards
            claim_type: Type of activity
            song_content_hash: Which song
            total_tokens_claimed: Tokens to claim
            zk_proof_data: ZK proof from LoRa node
            
        Returns:
            Claim ID, or None if failed
        """
        # 1. Create claim
        claim = self.royalty.create_reward_claim(
            claimant_wallet=claimant_wallet,
            claim_type=claim_type,
            song_content_hash=song_content_hash,
            total_tokens_claimed=total_tokens_claimed
        )
        
        # 2. Verify ZK proof
        zk_verified = self.royalty.verify_reward_claim(
            claim_id=claim.claim_id,
            zk_proof_data=zk_proof_data,
            verifier_signature=""  # Would be actual signature
        )
        
        if not zk_verified:
            logger.warning(f"ZK proof verification failed for claim {claim.claim_id}")
            return None
        
        # 3. Distribute to verifier nodes for quorum approval
        verifiers = self.verifier.distribute_claim_to_verifiers(claim.claim_id)
        
        logger.info(
            f"Claim submitted for verification: {claim.claim_id} "
            f"({len(verifiers)} verifiers assigned)"
        )
        
        return claim.claim_id
    
    async def finalize_approved_claim(
        self,
        claim_id: str
    ) -> Optional[str]:
        """
        Finalize approved claim and mint tokens on blockchain.
        
        Called after verifier quorum (3-of-4) approves.
        
        Args:
            claim_id: ID of approved claim
            
        Returns:
            Transaction hash, or None if failed
        """
        claim = self.royalty.reward_claims.get(claim_id)
        if not claim or not claim.proof_verified:
            logger.warning(f"Cannot finalize: claim not verified: {claim_id}")
            return None
        
        # 1. Mint tokens on blockchain
        tx_hash = await self.blockchain.mint_reward_tokens(
            recipient_wallet=claim.claimant_wallet,
            token_amount=claim.total_tokens_verified,
            reason=claim.claim_type.value
        )
        
        # 2. Update claim with tx hash
        self.royalty.approve_and_mint_tokens(claim_id, tx_hash)
        
        logger.info(
            f"Claim finalized: {claim.claimant_wallet[:20]}... "
            f"received {claim.total_tokens_verified} tokens (tx: {tx_hash[:16]}...)"
        )
        
        return tx_hash
    
    async def process_nft_sale(
        self,
        song_title: str,
        artist: str,
        content_hash: str,
        edition_number: int,
        max_editions: int,
        buyer_wallet: str,
        purchase_price_usd: float,
        purchase_price_tokens: int,
        watermark_hash: str,
        perceptual_fingerprint: str
    ) -> Tuple[str, int]:
        """
        Process NFT sale end-to-end.
        
        1. Mint NFT on blockchain (ERC-721)
        2. Record certificate
        3. Calculate and distribute royalties
        4. Set up royalty enforcement for secondary sales
        
        Args:
            song_title: Song name
            artist: Artist (you)
            content_hash: SHA256 of audio
            edition_number: Which edition (1-100)
            max_editions: Total editions
            buyer_wallet: Buyer's wallet
            purchase_price_usd: Sale price in USD
            purchase_price_tokens: Sale price in tokens
            watermark_hash: Watermarking proof
            perceptual_fingerprint: Content fingerprint
            
        Returns:
            Tuple of (nft_tx_hash, token_id)
        """
        # 1. Mint NFT on blockchain
        nft_tx_hash, token_id = await self.blockchain.mint_nft_certificate(
            song_title=song_title,
            song_content_hash=content_hash,
            watermark_hash=watermark_hash,
            edition_number=edition_number,
            max_editions=max_editions,
            receiver_wallet=buyer_wallet
        )
        
        # 2. Issue certificate locally
        certificate = self.royalty.issue_nft_certificate(
            song_title=song_title,
            artist=artist,
            content_hash=content_hash,
            edition_number=edition_number,
            max_editions=max_editions,
            buyer_wallet=buyer_wallet,
            purchase_price_usd=purchase_price_usd,
            purchase_price_tokens=purchase_price_tokens,
            watermark_hash=watermark_hash,
            perceptual_fingerprint=perceptual_fingerprint,
            nft_contract_address=self.blockchain.nft_contract,
            token_id=token_id
        )
        
        # 3. Process royalty payment
        payment = self.royalty.process_primary_sale(
            song_title=song_title,
            artist=artist,
            content_hash=content_hash,
            purchase_price_usd=purchase_price_usd,
            purchase_price_tokens=purchase_price_tokens,
            nft_contract_address=self.blockchain.nft_contract,
            token_id=token_id
        )
        
        # 4. Distribute royalties on blockchain
        royalty_tx = await self.blockchain.distribute_royalties(
            payment_id=payment.payment_id,
            artist_wallet="YOUR_WALLET_ADDRESS",  # Artist wallet
            artist_amount=payment.artist_payout_usd,
            platform_wallet="PLATFORM_WALLET",
            platform_amount=payment.platform_payout_usd,
            node_operator_pool="NODE_POOL_WALLET",
            node_operator_amount=payment.node_operator_payout_usd
        )
        
        # 5. Set up ERC-2981 royalty enforcement
        await self.blockchain.set_royalty_enforcement(
            token_id=token_id,
            artist_wallet="YOUR_WALLET_ADDRESS",
            royalty_percentage=70  # 70% on secondary sales
        )
        
        logger.info(
            f"NFT sale processed: {song_title} Edition {edition_number} "
            f"sold to {buyer_wallet[:20]}... for ${purchase_price_usd:.2f}"
        )
        
        return (nft_tx_hash, token_id)
