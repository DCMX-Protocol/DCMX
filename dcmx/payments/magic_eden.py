"""
Magic Eden Marketplace Integration

Enables listing and selling DCMX music NFTs on Magic Eden marketplace.
Supports cross-chain listings (Solana, Ethereum, Polygon, Bitcoin).
"""

import logging
import aiohttp
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MagicEdenChain(Enum):
    """Supported Magic Eden chains."""
    SOLANA = "solana"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BITCOIN = "bitcoin"


@dataclass
class MagicEdenListing:
    """Magic Eden NFT listing."""
    listing_id: str
    nft_address: str
    token_id: str
    seller: str
    price: float
    currency: str
    chain: MagicEdenChain
    status: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "listing_id": self.listing_id,
            "nft_address": self.nft_address,
            "token_id": self.token_id,
            "seller": self.seller,
            "price": self.price,
            "currency": self.currency,
            "chain": self.chain.value,
            "status": self.status,
            "metadata": self.metadata,
        }


class MagicEdenClient:
    """
    Magic Eden API client for DCMX NFT marketplace integration.
    
    Features:
    - List music NFTs for sale
    - Update listing prices
    - Cancel listings
    - Track sales and royalties
    - Cross-chain support
    """
    
    # API endpoints by chain
    API_ENDPOINTS = {
        MagicEdenChain.SOLANA: "https://api-mainnet.magiceden.dev/v2",
        MagicEdenChain.ETHEREUM: "https://api.magiceden.io/v2/eth",
        MagicEdenChain.POLYGON: "https://api.magiceden.io/v2/polygon",
        MagicEdenChain.BITCOIN: "https://api.magiceden.io/v2/ord",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        chain: MagicEdenChain = MagicEdenChain.SOLANA,
    ):
        """
        Initialize Magic Eden client.
        
        Args:
            api_key: Magic Eden API key (optional for read-only)
            chain: Blockchain to use
        """
        self.api_key = api_key
        self.chain = chain
        self.base_url = self.API_ENDPOINTS[chain]
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Magic Eden client initialized for {chain.value}")
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self.session is None:
            headers: Dict[str, str] = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def list_nft(
        self,
        nft_address: str,
        token_id: str,
        price: float,
        seller_address: str,
        expiry_days: int = 30,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MagicEdenListing:
        """
        List an NFT for sale on Magic Eden.
        
        Args:
            nft_address: NFT contract address
            token_id: Token ID
            price: Listing price (in native currency)
            seller_address: Seller wallet address
            expiry_days: Days until listing expires
            metadata: Additional metadata
            
        Returns:
            MagicEdenListing object
        """
        await self._ensure_session()
        
        # Prepare listing data
        listing_data: Dict[str, Any] = {
            "nft_address": nft_address,
            "token_id": token_id,
            "price": price,
            "seller": seller_address,
            "expiry_days": expiry_days,
            "metadata": metadata or {},
        }
        
        try:
            # Magic Eden listing endpoint
            url = f"{self.base_url}/listings"
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.post(url, json=listing_data) as response:
                if response.status == 201:
                    data = await response.json()
                    
                    listing = MagicEdenListing(
                        listing_id=data.get("listing_id"),
                        nft_address=nft_address,
                        token_id=token_id,
                        seller=seller_address,
                        price=price,
                        currency="SOL" if self.chain == MagicEdenChain.SOLANA else "ETH",
                        chain=self.chain,
                        status="active",
                        metadata=metadata or {},
                    )
                    
                    logger.info(f"NFT listed on Magic Eden: {listing.listing_id}")
                    return listing
                else:
                    error = await response.text()
                    logger.error(f"Failed to list NFT: {error}")
                    raise Exception(f"Listing failed: {error}")
                    
        except Exception as e:
            logger.error(f"Error listing NFT on Magic Eden: {e}")
            raise
    
    async def update_listing_price(
        self,
        listing_id: str,
        new_price: float,
    ) -> bool:
        """
        Update listing price.
        
        Args:
            listing_id: Listing ID
            new_price: New price
            
        Returns:
            Success status
        """
        await self._ensure_session()
        
        try:
            url = f"{self.base_url}/listings/{listing_id}"
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.patch(url, json={"price": new_price}) as response:
                if response.status == 200:
                    logger.info(f"Listing {listing_id} price updated to {new_price}")
                    return True
                else:
                    logger.error(f"Failed to update listing price: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating listing: {e}")
            return False
    
    async def cancel_listing(self, listing_id: str) -> bool:
        """
        Cancel an active listing.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            Success status
        """
        await self._ensure_session()
        
        try:
            url = f"{self.base_url}/listings/{listing_id}/cancel"
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.post(url) as response:
                if response.status == 200:
                    logger.info(f"Listing {listing_id} cancelled")
                    return True
                else:
                    logger.error(f"Failed to cancel listing: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error cancelling listing: {e}")
            return False
    
    async def get_listing(self, listing_id: str) -> Optional[MagicEdenListing]:
        """
        Get listing details.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            MagicEdenListing or None
        """
        await self._ensure_session()
        
        try:
            url = f"{self.base_url}/listings/{listing_id}"
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return MagicEdenListing(
                        listing_id=data["listing_id"],
                        nft_address=data["nft_address"],
                        token_id=data["token_id"],
                        seller=data["seller"],
                        price=data["price"],
                        currency=data["currency"],
                        chain=self.chain,
                        status=data["status"],
                        metadata=data.get("metadata", {}),
                    )
                else:
                    logger.warning(f"Listing not found: {listing_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching listing: {e}")
            return None
    
    async def get_collection_stats(self, collection_symbol: str) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Args:
            collection_symbol: Collection symbol (e.g., "dcmx_music")
            
        Returns:
            Collection stats
        """
        await self._ensure_session()
        
        try:
            url = f"{self.base_url}/collections/{collection_symbol}/stats"
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    stats = await response.json()
                    logger.info(f"Collection stats retrieved for {collection_symbol}")
                    return stats
                else:
                    logger.warning(f"Collection stats not found: {collection_symbol}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Error fetching collection stats: {e}")
            return {}
    
    async def get_sales_history(
        self,
        nft_address: str,
        token_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get NFT sales history.
        
        Args:
            nft_address: NFT contract address
            token_id: Token ID
            limit: Max number of sales to return
            
        Returns:
            List of sales
        """
        await self._ensure_session()
        
        try:
            url = f"{self.base_url}/tokens/{nft_address}/{token_id}/activities"
            params = {"limit": limit, "offset": 0}
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    activities = await response.json()
                    
                    # Filter for sales only
                    sales = [
                        activity for activity in activities
                        if activity.get("type") == "sale"
                    ]
                    
                    logger.info(f"Retrieved {len(sales)} sales for token {token_id}")
                    return sales
                else:
                    logger.warning(f"No sales history found")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching sales history: {e}")
            return []
    
    async def calculate_royalties(
        self,
        sale_price: float,
        royalty_percentage: float,
    ) -> Dict[str, float]:
        """
        Calculate royalties from a sale.
        
        Args:
            sale_price: Sale price
            royalty_percentage: Royalty percentage (e.g., 10.0 for 10%)
            
        Returns:
            Royalty breakdown
        """
        royalty_amount = sale_price * (royalty_percentage / 100)
        seller_proceeds = sale_price - royalty_amount
        
        # Magic Eden takes 2% marketplace fee
        marketplace_fee = sale_price * 0.02
        net_to_seller = seller_proceeds - marketplace_fee
        
        return {
            "sale_price": sale_price,
            "royalty_amount": royalty_amount,
            "royalty_percentage": royalty_percentage,
            "marketplace_fee": marketplace_fee,
            "seller_proceeds": net_to_seller,
        }


class DCMXMagicEdenIntegration:
    """
    DCMX-specific Magic Eden integration.
    
    Handles listing DCMX music NFTs on Magic Eden marketplace.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        chain: MagicEdenChain = MagicEdenChain.SOLANA,
        collection_symbol: str = "dcmx_music",
    ):
        """
        Initialize DCMX Magic Eden integration.
        
        Args:
            api_key: Magic Eden API key
            chain: Blockchain to use
            collection_symbol: DCMX collection symbol
        """
        self.client = MagicEdenClient(api_key=api_key, chain=chain)
        self.collection_symbol = collection_symbol
        self.active_listings: Dict[str, MagicEdenListing] = {}
    
    async def list_music_nft(
        self,
        nft_address: str,
        token_id: str,
        artist: str,
        track_title: str,
        price: float,
        seller_address: str,
        royalty_percentage: float = 10.0,
        edition_number: Optional[int] = None,
        max_editions: Optional[int] = None,
    ) -> MagicEdenListing:
        """
        List a DCMX music NFT on Magic Eden.
        
        Args:
            nft_address: NFT contract address
            token_id: Token ID
            artist: Artist name
            track_title: Track title
            price: Listing price
            seller_address: Seller wallet
            royalty_percentage: Artist royalty percentage
            edition_number: Edition number (if limited)
            max_editions: Max editions (if limited)
            
        Returns:
            MagicEdenListing
        """
        # Prepare music-specific metadata
        metadata: Dict[str, Any] = {
            "collection": self.collection_symbol,
            "artist": artist,
            "track_title": track_title,
            "category": "music",
            "royalty_percentage": royalty_percentage,
        }
        
        if edition_number and max_editions:
            metadata["edition"] = f"{edition_number}/{max_editions}"
        
        # List on Magic Eden
        listing = await self.client.list_nft(
            nft_address=nft_address,
            token_id=token_id,
            price=price,
            seller_address=seller_address,
            metadata=metadata,
        )
        
        # Track active listing
        self.active_listings[listing.listing_id] = listing
        
        logger.info(
            f"Listed '{track_title}' by {artist} on Magic Eden: "
            f"{price} {listing.currency}"
        )
        
        return listing
    
    async def get_collection_floor_price(self) -> Optional[float]:
        """
        Get DCMX collection floor price on Magic Eden.
        
        Returns:
            Floor price or None
        """
        stats = await self.client.get_collection_stats(self.collection_symbol)
        return stats.get("floor_price")
    
    async def get_collection_volume(self) -> Dict[str, float]:
        """
        Get DCMX collection trading volume.
        
        Returns:
            Volume statistics
        """
        stats = await self.client.get_collection_stats(self.collection_symbol)
        
        return {
            "total_volume": stats.get("total_volume", 0),
            "volume_24h": stats.get("volume_24h", 0),
            "volume_7d": stats.get("volume_7d", 0),
            "volume_30d": stats.get("volume_30d", 0),
        }
    
    async def close(self) -> None:
        """Close client connection."""
        await self.client.close()
