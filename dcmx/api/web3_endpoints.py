"""Web3 blockchain endpoints for DCMX API."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

from dcmx.tron.contracts import ContractManager
from dcmx.tron.config import TronConfig
from dcmx.tron import utils
from dcmx.database.connection import get_database
from dcmx.database.models import NFTIndex, RewardClaimIndex, TransactionIndex

logger = logging.getLogger(__name__)

# Create router
web3_router = APIRouter(prefix="/api/v1", tags=["web3"])

# Initialize contract manager (lazy loading)
_contract_manager: Optional[ContractManager] = None

def get_contract_manager() -> ContractManager:
    """Get or initialize contract manager."""
    global _contract_manager
    if _contract_manager is None:
        try:
            config = TronConfig.from_env()
            _contract_manager = ContractManager(config)
            logger.info("Contract manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize contract manager: {e}")
            raise HTTPException(
                status_code=503,
                detail="Blockchain service unavailable"
            )
    return _contract_manager


# ============================================================================
# NFT ENDPOINTS
# ============================================================================

class NFTMintRequest(BaseModel):
    """Request model for minting NFT."""
    to_address: str
    title: str
    artist: str
    content_hash: str
    edition: int
    max_editions: int
    royalty_bps: int = 1000  # 10% default
    royalty_recipient: Optional[str] = None


@web3_router.post("/nft/mint")
async def mint_nft(request: NFTMintRequest):
    """
    Mint a music NFT.
    
    Args:
        request: NFT mint request
        
    Returns:
        Transaction hash and NFT details
    """
    try:
        manager = get_contract_manager()
        
        if not manager.nft:
            raise HTTPException(
                status_code=503,
                detail="NFT contract not configured"
            )
        
        # Mint NFT on blockchain
        result = manager.nft.mint(
            to_address=request.to_address,
            title=request.title,
            artist=request.artist,
            content_hash=request.content_hash,
            edition=request.edition,
            max_editions=request.max_editions,
            royalty_bps=request.royalty_bps,
            royalty_recipient=request.royalty_recipient,
        )
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Minting failed: {result.error}"
            )
        
        logger.info(f"NFT minted: {result.transaction_hash}")
        
        return {
            "success": True,
            "transaction_hash": result.transaction_hash,
            "nft": {
                "title": request.title,
                "artist": request.artist,
                "content_hash": request.content_hash,
                "edition": request.edition,
                "max_editions": request.max_editions,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"NFT minting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web3_router.get("/nft/{token_id}")
async def get_nft(token_id: int):
    """
    Get NFT details by token ID.
    
    Args:
        token_id: NFT token ID
        
    Returns:
        NFT metadata
    """
    try:
        # Try database first (indexed)
        db = get_database()
        with db.get_session() as session:
            nft = session.query(NFTIndex).filter(
                NFTIndex.token_id == token_id
            ).first()
            
            if nft:
                return {
                    "token_id": nft.token_id,
                    "title": nft.title,
                    "artist": nft.artist,
                    "content_hash": nft.content_hash,
                    "edition": nft.edition,
                    "max_editions": nft.max_editions,
                    "owner": nft.owner_address,
                    "mint_date": nft.mint_date.isoformat(),
                    "royalty_bps": nft.royalty_bps,
                    "source": "indexed"
                }
        
        # Fall back to blockchain
        manager = get_contract_manager()
        if not manager.nft:
            raise HTTPException(
                status_code=503,
                detail="NFT contract not configured"
            )
        
        metadata = manager.nft.get_metadata(token_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="NFT not found")
        
        owner = manager.nft.get_owner(token_id)
        
        return {
            "token_id": token_id,
            "title": metadata["title"],
            "artist": metadata["artist"],
            "content_hash": metadata["content_hash"],
            "edition": metadata["edition"],
            "max_editions": metadata["max_editions"],
            "owner": owner,
            "royalty_bps": metadata["royalty_bps"],
            "source": "blockchain"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get NFT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web3_router.get("/nft/by-artist/{artist}")
async def get_nfts_by_artist(
    artist: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get NFTs by artist.
    
    Args:
        artist: Artist name
        page: Page number
        per_page: Items per page
        
    Returns:
        List of NFTs
    """
    try:
        db = get_database()
        offset = (page - 1) * per_page
        
        with db.get_session() as session:
            nfts = session.query(NFTIndex).filter(
                NFTIndex.artist == artist
            ).offset(offset).limit(per_page).all()
            
            return {
                "artist": artist,
                "page": page,
                "per_page": per_page,
                "nfts": [
                    {
                        "token_id": nft.token_id,
                        "title": nft.title,
                        "content_hash": nft.content_hash,
                        "edition": nft.edition,
                        "max_editions": nft.max_editions,
                        "owner": nft.owner_address,
                    }
                    for nft in nfts
                ]
            }
            
    except Exception as e:
        logger.error(f"Get NFTs by artist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# REWARD ENDPOINTS
# ============================================================================

class RewardClaimRequest(BaseModel):
    """Request model for reward claim."""
    claim_type: str  # SHARING, LISTENING, BANDWIDTH
    proof_data: Dict[str, Any]
    amount: int


@web3_router.post("/reward/claim")
async def submit_reward_claim(request: RewardClaimRequest):
    """
    Submit a reward claim.
    
    Args:
        request: Reward claim request
        
    Returns:
        Claim ID and status
    """
    try:
        manager = get_contract_manager()
        
        if not manager.rewards:
            raise HTTPException(
                status_code=503,
                detail="Reward vault not configured"
            )
        
        # Map claim type to enum
        claim_type_map = {
            "SHARING": 0,
            "LISTENING": 1,
            "BANDWIDTH": 2,
        }
        claim_type = claim_type_map.get(request.claim_type.upper())
        if claim_type is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid claim type"
            )
        
        # Compute proof hash
        proof_hash = utils.compute_proof_hash(request.proof_data)
        
        # Submit claim
        result = manager.rewards.submit_claim(
            claim_type=claim_type,
            proof_hash=proof_hash,
            amount=request.amount
        )
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Claim submission failed: {result.error}"
            )
        
        logger.info(f"Reward claim submitted: {result.transaction_hash}")
        
        return {
            "success": True,
            "transaction_hash": result.transaction_hash,
            "claim_type": request.claim_type,
            "amount": request.amount,
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reward claim error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web3_router.get("/reward/user/{address}")
async def get_user_rewards(address: str):
    """
    Get user's reward status.
    
    Args:
        address: User wallet address
        
    Returns:
        Pending and claimed rewards
    """
    try:
        manager = get_contract_manager()
        
        if not manager.rewards:
            raise HTTPException(
                status_code=503,
                detail="Reward vault not configured"
            )
        
        # Get from blockchain
        rewards = manager.rewards.get_user_rewards(address)
        
        # Also get from database (indexed claims)
        db = get_database()
        with db.get_session() as session:
            claims = session.query(RewardClaimIndex).filter(
                RewardClaimIndex.user_address == address
            ).all()
            
            claim_history = [
                {
                    "claim_id": claim.claim_id,
                    "type": claim.claim_type,
                    "amount": str(claim.amount),
                    "status": claim.status,
                    "submitted_at": claim.submitted_at.isoformat(),
                }
                for claim in claims
            ]
        
        return {
            "address": address,
            "pending": rewards["pending"],
            "claimed": rewards["claimed"],
            "claim_history": claim_history,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user rewards error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROYALTY ENDPOINTS
# ============================================================================

class RoyaltyDistributionRequest(BaseModel):
    """Request model for royalty distribution."""
    nft_contract: str
    nft_token_id: int
    seller: str
    buyer: str
    sale_price: int  # In SUN


@web3_router.post("/royalty/distribute")
async def distribute_royalties(request: RoyaltyDistributionRequest):
    """
    Record NFT sale and distribute royalties.
    
    Args:
        request: Royalty distribution request
        
    Returns:
        Sale ID and distribution status
    """
    try:
        manager = get_contract_manager()
        
        if not manager.royalties:
            raise HTTPException(
                status_code=503,
                detail="Royalty distributor not configured"
            )
        
        # Record sale
        sale_result = manager.royalties.record_sale(
            nft_contract=request.nft_contract,
            nft_token_id=request.nft_token_id,
            seller=request.seller,
            buyer=request.buyer,
            sale_price=request.sale_price
        )
        
        if not sale_result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Sale recording failed: {sale_result.error}"
            )
        
        logger.info(f"Sale recorded: {sale_result.transaction_hash}")
        
        return {
            "success": True,
            "sale_transaction": sale_result.transaction_hash,
            "sale_price": request.sale_price,
            "sale_price_trx": utils.from_sun(request.sale_price),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Royalty distribution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@web3_router.get("/royalty/{recipient}")
async def get_pending_royalties(recipient: str):
    """
    Get pending royalties for recipient.
    
    Args:
        recipient: Recipient address
        
    Returns:
        Pending royalty amount
    """
    try:
        manager = get_contract_manager()
        
        if not manager.royalties:
            raise HTTPException(
                status_code=503,
                detail="Royalty distributor not configured"
            )
        
        pending = manager.royalties.get_pending_royalties(recipient)
        
        return {
            "recipient": recipient,
            "pending_sun": pending,
            "pending_trx": utils.from_sun(pending),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get pending royalties error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BLOCKCHAIN INFO ENDPOINTS
# ============================================================================

@web3_router.get("/blockchain/status")
async def get_blockchain_status():
    """Get blockchain connection status."""
    try:
        manager = get_contract_manager()
        
        # Get balance
        balance_sun = manager.client.get_balance()
        
        return {
            "connected": True,
            "network": manager.config.network.value,
            "address": manager.client.address,
            "balance_sun": balance_sun,
            "balance_trx": utils.from_sun(balance_sun),
            "contracts": {
                "token": manager.config.dcmx_token_address,
                "nft": manager.config.music_nft_address,
                "compliance": manager.config.compliance_registry_address,
                "rewards": manager.config.reward_vault_address,
                "royalties": manager.config.royalty_distributor_address,
            }
        }
        
    except Exception as e:
        logger.error(f"Blockchain status error: {e}")
        return {
            "connected": False,
            "error": str(e)
        }


@web3_router.get("/transactions/{address}")
async def get_transactions(
    address: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """
    Get transaction history for address.
    
    Args:
        address: Wallet address
        page: Page number
        per_page: Items per page
        
    Returns:
        List of transactions
    """
    try:
        db = get_database()
        offset = (page - 1) * per_page
        
        with db.get_session() as session:
            from sqlalchemy import or_
            
            txs = session.query(TransactionIndex).filter(
                or_(
                    TransactionIndex.from_address == address,
                    TransactionIndex.to_address == address
                )
            ).order_by(
                TransactionIndex.timestamp.desc()
            ).offset(offset).limit(per_page).all()
            
            return {
                "address": address,
                "page": page,
                "per_page": per_page,
                "transactions": [
                    {
                        "tx_hash": tx.tx_hash,
                        "from": tx.from_address,
                        "to": tx.to_address,
                        "value_sun": str(tx.value),
                        "value_trx": utils.from_sun(int(tx.value)),
                        "token": tx.token,
                        "timestamp": tx.timestamp.isoformat(),
                        "status": tx.status,
                    }
                    for tx in txs
                ]
            }
            
    except Exception as e:
        logger.error(f"Get transactions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
