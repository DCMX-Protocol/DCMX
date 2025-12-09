"""Network protocol implementation for peer communication."""

import logging
from typing import Optional
import aiohttp

from dcmx.network.peer import Peer


logger = logging.getLogger(__name__)


class Protocol:
    """
    Handles network communication protocol between peers.
    
    Implements basic HTTP-based messaging for peer discovery,
    track metadata exchange, and content transfer.
    """
    
    def __init__(self, local_peer: Peer):
        """
        Initialize protocol handler.
        
        Args:
            local_peer: The local peer instance
        """
        self.local_peer = local_peer
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the protocol session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def connect(self, host: str, port: int) -> Optional[Peer]:
        """
        Connect to a peer and exchange information.
        
        Args:
            host: Peer host address
            port: Peer port
            
        Returns:
            Peer instance if connection successful
        """
        url = f"http://{host}:{port}/discover"
        
        try:
            session = await self._get_session()
            async with session.post(
                url,
                json={"peer": self.local_peer.to_dict()},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    peer_data = data.get("peer")
                    
                    if peer_data:
                        peer = Peer.from_dict(peer_data)
                        logger.info(f"Connected to peer {peer}")
                        
                        # Update with tracks from response
                        tracks = data.get("tracks", [])
                        for track_data in tracks:
                            peer.add_track(track_data["content_hash"])
                        
                        return peer
        except Exception as e:
            logger.error(f"Connection failed to {host}:{port}: {e}")
        
        return None
    
    async def ping(self, peer: Peer) -> bool:
        """
        Ping a peer to check if it's alive.
        
        Args:
            peer: Peer to ping
            
        Returns:
            True if peer responds
        """
        url = f"http://{peer.host}:{peer.port}/ping"
        
        try:
            session = await self._get_session()
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status") == "ok"
        except Exception as e:
            logger.debug(f"Ping failed to {peer}: {e}")
        
        return False
    
    async def request_content(self, peer: Peer, content_hash: str) -> Optional[bytes]:
        """
        Request track content from a peer.
        
        Args:
            peer: Peer to request from
            content_hash: Content hash of the track
            
        Returns:
            Track content bytes if successful
        """
        url = f"http://{peer.host}:{peer.port}/content/{content_hash}"
        
        try:
            session = await self._get_session()
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    return await response.read()
        except Exception as e:
            logger.error(f"Content request failed from {peer}: {e}")
        
        return None
    
    async def get_peers(self, peer: Peer) -> list:
        """
        Get peer list from another peer.
        
        Args:
            peer: Peer to query
            
        Returns:
            List of peer dictionaries
        """
        url = f"http://{peer.host}:{peer.port}/peers"
        
        try:
            session = await self._get_session()
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("peers", [])
        except Exception as e:
            logger.error(f"Failed to get peers from {peer}: {e}")
        
        return []
    
    async def get_tracks(self, peer: Peer) -> list:
        """
        Get available tracks from a peer.
        
        Args:
            peer: Peer to query
            
        Returns:
            List of track dictionaries
        """
        url = f"http://{peer.host}:{peer.port}/tracks"
        
        try:
            session = await self._get_session()
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("tracks", [])
        except Exception as e:
            logger.error(f"Failed to get tracks from {peer}: {e}")
        
        return []
