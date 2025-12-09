"""
DCMX Web3 Economy REST API Server

FastAPI-based REST API for DCMX platform.
Provides endpoints for wallets, NFTs, rewards, voting, and analytics.
"""

import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from dcmx.royalties import (
    ArtistFirstEconomics,
    AdvancedEconomicsEngine,
    RevenuePoolManager,
    SustainabilityEngine,
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DCMX Web3 Economy API",
    description="Decentralized music network with artist-first economics",
    version="1.0.0",
)

# Enable CORS for Web3 frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize economics engines
economics = ArtistFirstEconomics()
advanced = AdvancedEconomicsEngine()
pools = RevenuePoolManager()
sustainability = SustainabilityEngine()

# In-memory data store (replace with DB in production)
wallets: Dict[str, Any] = {}
nfts: Dict[str, Any] = {}
user_votes: Dict[str, Any] = {}
user_skips: Dict[str, Any] = {}


# ============================================================================
# WALLET ENDPOINTS
# ============================================================================

@app.post("/api/v1/wallet/create")
async def create_wallet(
    wallet_address: str = Body(...),
    username: str = Body(...),
):
    """Create or register a user wallet."""
    if wallet_address in wallets:
        raise HTTPException(status_code=400, detail="Wallet already exists")
    
    wallets[wallet_address] = {
        "address": wallet_address,
        "username": username,
        "balance_dcmx": 0.0,
        "created_at": datetime.utcnow().isoformat(),
        "is_artist": False,
    }
    
    logger.info(f"Wallet created: {wallet_address}")
    return {
        "success": True,
        "wallet": wallets[wallet_address],
    }


@app.get("/api/v1/wallet/{wallet_address}")
async def get_wallet(wallet_address: str):
    """Get wallet information."""
    if wallet_address not in wallets:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    return wallets[wallet_address]


@app.post("/api/v1/wallet/{wallet_address}/fund")
async def fund_wallet(
    wallet_address: str,
    amount_dcmx: float = Body(...),
):
    """Fund a wallet (for testing/onboarding)."""
    if wallet_address not in wallets:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallets[wallet_address]["balance_dcmx"] += amount_dcmx
    logger.info(f"Wallet {wallet_address} funded with {amount_dcmx} DCMX")
    
    return {
        "success": True,
        "wallet": wallets[wallet_address],
    }


@app.post("/api/v1/wallet/{wallet_address}/artist-register")
async def register_artist(wallet_address: str):
    """Register wallet as artist."""
    if wallet_address not in wallets:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    wallets[wallet_address]["is_artist"] = True
    logger.info(f"Artist registered: {wallet_address}")
    
    return {
        "success": True,
        "message": "Wallet registered as artist",
        "wallet": wallets[wallet_address],
    }


# ============================================================================
# NFT ENDPOINTS
# ============================================================================

@app.post("/api/v1/nft/create")
async def create_nft(
    artist_wallet: str = Body(...),
    song_title: str = Body(...),
    price_dcmx: float = Body(...),
    edition_number: int = Body(...),
    max_editions: int = Body(...),
):
    """Create NFT certificate for song."""
    if artist_wallet not in wallets:
        raise HTTPException(status_code=404, detail="Artist wallet not found")
    
    if not wallets[artist_wallet]["is_artist"]:
        raise HTTPException(status_code=400, detail="Wallet not registered as artist")
    
    nft = economics.create_nft_certificate(
        artist_wallet=artist_wallet,
        song_title=song_title,
        edition_number=edition_number,
        max_editions=max_editions,
        price_dcmx=price_dcmx,
        shared_with_wallet=None,
        completion_percentage=0.0,
    )
    
    nft_id = nft.content_hash
    nfts[nft_id] = {
        "id": nft_id,
        "title": song_title,
        "artist": artist_wallet,
        "artist_username": wallets[artist_wallet].get("username", "Unknown"),
        "price_dcmx": price_dcmx,
        "edition": edition_number,
        "max_editions": max_editions,
        "content_hash": nft.content_hash,
        "created_at": datetime.utcnow().isoformat(),
        "likes": 0,
        "dislikes": 0,
        "listeners": 0,
        "engagement_metrics": {
            "average_completion": 0.0,
            "total_listens": 0,
            "skip_count": 0,
        }
    }
    
    logger.info(f"NFT created: {song_title} by {artist_wallet}")
    return {
        "success": True,
        "nft": nfts[nft_id],
    }


@app.get("/api/v1/nft/{nft_id}")
async def get_nft(nft_id: str):
    """Get NFT details."""
    if nft_id not in nfts:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    return nfts[nft_id]


@app.get("/api/v1/nft/artist/{artist_wallet}")
async def get_artist_nfts(artist_wallet: str):
    """Get all NFTs by artist."""
    artist_nfts = [nft for nft in nfts.values() if nft["artist"] == artist_wallet]
    return {
        "artist": artist_wallet,
        "nfts": artist_nfts,
        "total": len(artist_nfts),
    }


@app.post("/api/v1/nft/{nft_id}/purchase")
async def purchase_nft(
    nft_id: str,
    buyer_wallet: str = Body(...),
):
    """Purchase NFT."""
    if nft_id not in nfts:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    if buyer_wallet not in wallets:
        raise HTTPException(status_code=404, detail="Buyer wallet not found")
    
    nft = nfts[nft_id]
    price = nft["price_dcmx"]
    
    if wallets[buyer_wallet]["balance_dcmx"] < price:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Process purchase
    wallets[buyer_wallet]["balance_dcmx"] -= price
    wallets[nft["artist"]]["balance_dcmx"] += price  # 100% to artist
    
    logger.info(f"NFT purchased: {buyer_wallet} bought {nft_id} for {price} DCMX")
    
    return {
        "success": True,
        "transaction": {
            "buyer": buyer_wallet,
            "artist": nft["artist"],
            "nft_id": nft_id,
            "price_dcmx": price,
            "buyer_balance": wallets[buyer_wallet]["balance_dcmx"],
            "artist_balance": wallets[nft["artist"]]["balance_dcmx"],
        }
    }


# ============================================================================
# LISTENING & ENGAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/song/listen")
async def record_listen(
    user_wallet: str = Body(...),
    nft_id: str = Body(...),
    completion_percentage: float = Body(...),
    listen_duration_seconds: int = Body(...),
):
    """Record user listening to a song."""
    if user_wallet not in wallets:
        raise HTTPException(status_code=404, detail="User wallet not found")
    
    if nft_id not in nfts:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    nft = nfts[nft_id]
    
    # Record listening reward
    reward = economics.add_listening_reward(
        user_wallet=user_wallet,
        song_content_hash=nft_id,
        shared_with_wallet=nft["artist"],
        listen_duration_seconds=listen_duration_seconds,
        completion_percentage=completion_percentage,
    )
    
    # Update user balance
    wallets[user_wallet]["balance_dcmx"] += reward.total_tokens
    
    # Update NFT metrics
    nft["engagement_metrics"]["total_listens"] += 1
    nft["engagement_metrics"]["average_completion"] = (
        (nft["engagement_metrics"]["average_completion"] * (nft["engagement_metrics"]["total_listens"] - 1) +
         completion_percentage) / nft["engagement_metrics"]["total_listens"]
    )
    nft["listeners"] += 1
    
    logger.info(f"Listen recorded: {user_wallet} listened {completion_percentage*100:.0f}% to {nft_id}")
    
    return {
        "success": True,
        "reward_tokens": reward.total_tokens,
        "user_balance": wallets[user_wallet]["balance_dcmx"],
        "nft_metrics": nft["engagement_metrics"],
    }


@app.post("/api/v1/song/vote")
async def vote_on_song(
    user_wallet: str = Body(...),
    nft_id: str = Body(...),
    preference: str = Body(...),  # "like" or "dislike"
):
    """Record user song preference vote (like/dislike)."""
    if user_wallet not in wallets:
        raise HTTPException(status_code=404, detail="User wallet not found")
    
    if nft_id not in nfts:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    if preference not in ["like", "dislike"]:
        raise HTTPException(status_code=400, detail="Preference must be 'like' or 'dislike'")
    
    nft = nfts[nft_id]
    
    # Record song preference vote
    reward = economics.record_song_preference_vote(
        user_wallet=user_wallet,
        song_content_hash=nft_id,
        artist_wallet=nft["artist"],
        preference=preference,
    )
    
    # Update user balance
    wallets[user_wallet]["balance_dcmx"] += reward.total_tokens
    
    # Update NFT engagement
    if preference == "like":
        nft["likes"] += 1
    else:
        nft["dislikes"] += 1
    
    # Track vote
    vote_key = f"{user_wallet}_{nft_id}_{datetime.utcnow().timestamp()}"
    user_votes[vote_key] = {
        "user": user_wallet,
        "nft_id": nft_id,
        "preference": preference,
        "reward": reward.total_tokens,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    logger.info(f"Vote recorded: {user_wallet} voted {preference} on {nft_id}")
    
    return {
        "success": True,
        "preference": preference,
        "reward_tokens": reward.total_tokens,
        "user_balance": wallets[user_wallet]["balance_dcmx"],
        "song_metrics": {
            "likes": nft["likes"],
            "dislikes": nft["dislikes"],
            "sentiment": "positive" if nft["likes"] > nft["dislikes"] else "negative" if nft["dislikes"] > nft["likes"] else "neutral",
        }
    }


@app.post("/api/v1/song/skip")
async def record_skip(
    user_wallet: str = Body(...),
    nft_id: str = Body(...),
    completion_percentage: float = Body(...),
):
    """Record user skipping a song (applies skip charge if early)."""
    if user_wallet not in wallets:
        raise HTTPException(status_code=404, detail="User wallet not found")
    
    if nft_id not in nfts:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    nft = nfts[nft_id]
    
    # Record skip charge
    charge = economics.record_skip_activity(
        user_wallet=user_wallet,
        song_content_hash=nft_id,
        artist_wallet=nft["artist"],
        completion_percentage=completion_percentage,
    )
    
    # Apply charge to user balance
    wallets[user_wallet]["balance_dcmx"] += charge.total_tokens  # Will be negative
    
    # Update NFT metrics
    if completion_percentage < 0.25:
        nft["engagement_metrics"]["skip_count"] += 1
    
    # Track skip
    skip_key = f"{user_wallet}_{nft_id}_{datetime.utcnow().timestamp()}"
    user_skips[skip_key] = {
        "user": user_wallet,
        "nft_id": nft_id,
        "completion": completion_percentage,
        "charge": charge.total_tokens,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    charged = charge.total_tokens < 0
    logger.info(f"Skip recorded: {user_wallet} skipped at {completion_percentage*100:.0f}% on {nft_id}" + 
                (f", charged {abs(charge.total_tokens):.2f} DCMX" if charged else ""))
    
    return {
        "success": True,
        "completion_percentage": completion_percentage,
        "charge_applied": charged,
        "charge_amount": abs(charge.total_tokens) if charged else 0.0,
        "user_balance": wallets[user_wallet]["balance_dcmx"],
        "message": f"Charged {abs(charge.total_tokens):.2f} DCMX for skipping before 25%" if charged else "No charge (listened to 25%+)",
    }


# ============================================================================
# ARTIST ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/artist/{artist_wallet}/earnings")
async def get_artist_earnings(artist_wallet: str):
    """Get artist total earnings."""
    if artist_wallet not in wallets:
        raise HTTPException(status_code=404, detail="Artist wallet not found")
    
    # Calculate earnings from owned NFTs
    artist_nfts = [nft for nft in nfts.values() if nft["artist"] == artist_wallet]
    total_sales = sum(nft["price_dcmx"] for nft in artist_nfts)
    current_balance = wallets[artist_wallet]["balance_dcmx"]
    
    return {
        "artist": artist_wallet,
        "username": wallets[artist_wallet].get("username", "Unknown"),
        "nfts_created": len(artist_nfts),
        "total_sales_dcmx": total_sales,
        "current_balance_dcmx": current_balance,
        "songs": [
            {
                "id": nft["id"],
                "title": nft["title"],
                "price": nft["price_dcmx"],
                "edition": f"{nft['edition']}/{nft['max_editions']}",
                "engagement": {
                    "listeners": nft["listeners"],
                    "likes": nft["likes"],
                    "dislikes": nft["dislikes"],
                    "sentiment_ratio": f"{nft['likes']}:{nft['dislikes']}",
                    "avg_completion": f"{nft['engagement_metrics']['average_completion']*100:.1f}%",
                    "skips": nft["engagement_metrics"]["skip_count"],
                }
            }
            for nft in artist_nfts
        ]
    }


@app.get("/api/v1/artist/{artist_wallet}/analytics")
async def get_artist_analytics(artist_wallet: str):
    """Get detailed artist analytics."""
    if artist_wallet not in wallets:
        raise HTTPException(status_code=404, detail="Artist wallet not found")
    
    artist_nfts = [nft for nft in nfts.values() if nft["artist"] == artist_wallet]
    
    total_listeners = sum(nft["listeners"] for nft in artist_nfts)
    total_likes = sum(nft["likes"] for nft in artist_nfts)
    total_dislikes = sum(nft["dislikes"] for nft in artist_nfts)
    avg_completion = sum(nft["engagement_metrics"]["average_completion"] for nft in artist_nfts) / len(artist_nfts) if artist_nfts else 0
    
    return {
        "artist": artist_wallet,
        "summary": {
            "total_songs": len(artist_nfts),
            "total_listeners": total_listeners,
            "total_likes": total_likes,
            "total_dislikes": total_dislikes,
            "like_dislike_ratio": f"{total_likes}:{total_dislikes}",
            "average_completion": f"{avg_completion*100:.1f}%",
            "sentiment": "positive" if total_likes > total_dislikes else "negative" if total_dislikes > total_likes else "neutral",
        },
        "songs_breakdown": [
            {
                "title": nft["title"],
                "id": nft["id"],
                "listeners": nft["listeners"],
                "likes": nft["likes"],
                "dislikes": nft["dislikes"],
                "avg_completion": f"{nft['engagement_metrics']['average_completion']*100:.1f}%",
                "skips": nft["engagement_metrics"]["skip_count"],
            }
            for nft in sorted(artist_nfts, key=lambda x: x["listeners"], reverse=True)
        ]
    }


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get("/api/v1/user/{user_wallet}/profile")
async def get_user_profile(user_wallet: str):
    """Get user profile and statistics."""
    if user_wallet not in wallets:
        raise HTTPException(status_code=404, detail="User wallet not found")
    
    # Calculate user stats
    user_votes_list = [v for v in user_votes.values() if v["user"] == user_wallet]
    user_skips_list = [s for s in user_skips.values() if s["user"] == user_wallet]
    
    likes_count = sum(1 for v in user_votes_list if v["preference"] == "like")
    dislikes_count = sum(1 for v in user_votes_list if v["preference"] == "dislike")
    total_rewards = sum(v["reward"] for v in user_votes_list)
    total_charges = sum(s["charge"] for s in user_skips_list if s["charge"] < 0)
    
    return {
        "wallet": user_wallet,
        "username": wallets[user_wallet].get("username", "Unknown"),
        "balance_dcmx": wallets[user_wallet]["balance_dcmx"],
        "is_artist": wallets[user_wallet]["is_artist"],
        "statistics": {
            "votes_cast": len(user_votes_list),
            "likes": likes_count,
            "dislikes": dislikes_count,
            "songs_skipped": len(user_skips_list),
            "total_rewards_earned": total_rewards,
            "total_skip_charges": abs(total_charges),
            "net_earnings": total_rewards + total_charges,
        }
    }


@app.get("/api/v1/user/{user_wallet}/votes")
async def get_user_votes(user_wallet: str):
    """Get user's voting history."""
    if user_wallet not in wallets:
        raise HTTPException(status_code=404, detail="User wallet not found")
    
    user_votes_list = [v for v in user_votes.values() if v["user"] == user_wallet]
    
    return {
        "wallet": user_wallet,
        "total_votes": len(user_votes_list),
        "votes": sorted(user_votes_list, key=lambda x: x["timestamp"], reverse=True),
    }


# ============================================================================
# PLATFORM STATISTICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/platform/stats")
async def get_platform_stats():
    """Get platform-wide statistics."""
    total_users = len(wallets)
    total_artists = sum(1 for w in wallets.values() if w["is_artist"])
    total_nfts = len(nfts)
    total_votes = len(user_votes)
    total_skips = len(user_skips)
    
    total_balance = sum(w["balance_dcmx"] for w in wallets.values())
    total_listeners = sum(nft["listeners"] for nft in nfts.values())
    total_likes = sum(nft["likes"] for nft in nfts.values())
    total_dislikes = sum(nft["dislikes"] for nft in nfts.values())
    
    # Sustainability check
    score, is_sustainable = sustainability.check_sustainability()
    
    return {
        "users": {
            "total": total_users,
            "artists": total_artists,
            "listeners": total_users - total_artists,
        },
        "content": {
            "total_nfts": total_nfts,
            "total_listeners": total_listeners,
            "total_likes": total_likes,
            "total_dislikes": total_dislikes,
        },
        "engagement": {
            "total_votes": total_votes,
            "total_skips": total_skips,
            "like_dislike_ratio": f"{total_likes}:{total_dislikes}",
        },
        "economics": {
            "total_platform_balance_dcmx": total_balance,
            "avg_user_balance_dcmx": total_balance / total_users if total_users > 0 else 0,
        },
        "sustainability": {
            "score": score,
            "status": "sustainable" if is_sustainable else "at_risk",
        }
    }


@app.get("/api/v1/platform/leaderboard/artists")
async def get_artist_leaderboard():
    """Get top artists by earnings."""
    artist_wallets = [w for w in wallets.values() if w["is_artist"]]
    artist_earnings = []
    
    for artist in artist_wallets:
        artist_nfts = [nft for nft in nfts.values() if nft["artist"] == artist["address"]]
        total_sales = sum(nft["price_dcmx"] for nft in artist_nfts)
        total_listeners = sum(nft["listeners"] for nft in artist_nfts)
        total_likes = sum(nft["likes"] for nft in artist_nfts)
        
        artist_earnings.append({
            "artist": artist["username"],
            "wallet": artist["address"],
            "earnings_dcmx": artist["balance_dcmx"],
            "nfts_created": len(artist_nfts),
            "total_listeners": total_listeners,
            "total_likes": total_likes,
        })
    
    return {
        "leaderboard": sorted(artist_earnings, key=lambda x: x["earnings_dcmx"], reverse=True),
        "total_artists": len(artist_earnings),
    }


@app.get("/api/v1/platform/leaderboard/songs")
async def get_songs_leaderboard():
    """Get top songs by likes."""
    songs_list = sorted(
        [
            {
                "title": nft["title"],
                "artist": nft["artist_username"],
                "id": nft["id"],
                "listeners": nft["listeners"],
                "likes": nft["likes"],
                "dislikes": nft["dislikes"],
                "sentiment": "positive" if nft["likes"] > nft["dislikes"] else "negative" if nft["dislikes"] > nft["likes"] else "neutral",
                "avg_completion": f"{nft['engagement_metrics']['average_completion']*100:.1f}%",
            }
            for nft in nfts.values()
        ],
        key=lambda x: x["likes"],
        reverse=True
    )
    
    return {
        "leaderboard": songs_list[:100],  # Top 100
        "total_songs": len(nfts),
    }


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/info")
async def api_info():
    """API information."""
    return {
        "name": "DCMX Web3 Economy API",
        "version": "1.0.0",
        "description": "Decentralized music network with artist-first economics",
        "endpoints": {
            "wallets": "/api/v1/wallet/*",
            "nfts": "/api/v1/nft/*",
            "engagement": "/api/v1/song/*",
            "analytics": "/api/v1/artist/*/analytics",
            "platform": "/api/v1/platform/*",
        }
    }


# ============================================================================
# SERVER STARTUP
# ============================================================================

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    logging.basicConfig(level=logging.INFO)
    logger.info(f"Starting DCMX API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
