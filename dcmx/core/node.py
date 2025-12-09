"""Main node implementation for DCMX mesh network."""

import asyncio
import logging
from typing import Dict, Set, List, Optional
from pathlib import Path

from dcmx.core.track import Track
from dcmx.network.peer import Peer
from dcmx.network.protocol import Protocol
from dcmx.storage.content_store import ContentStore


logger = logging.getLogger(__name__)


class Node:
    """
    Main node in the DCMX mesh music network.
    
    A Node manages local content, maintains connections to peers,
    and handles content discovery and distribution across the network.
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        data_dir: Optional[Path] = None,
    ):
        """
        Initialize a DCMX node.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
            data_dir: Directory for storing node data
        """
        self.peer = Peer(host=host, port=port)
        self.data_dir = data_dir or Path.home() / ".dcmx"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Network components
        self.protocol = Protocol(self.peer)
        self.peers: Dict[str, Peer] = {}  # peer_id -> Peer
        
        # Content storage
        self.content_store = ContentStore(self.data_dir / "content")
        self.tracks: Dict[str, Track] = {}  # content_hash -> Track
        
        # Network state
        self._running = False
        self._server: Optional[asyncio.Server] = None
        
        logger.info(f"Initialized node {self.peer.peer_id[:8]}... at {self.peer.address}")
    
    async def start(self):
        """Start the node and begin listening for connections."""
        if self._running:
            logger.warning("Node already running")
            return
        
        self._running = True
        
        # Start HTTP server for peer communication
        from aiohttp import web
        app = web.Application()
        app.router.add_get('/ping', self._handle_ping)
        app.router.add_get('/peers', self._handle_get_peers)
        app.router.add_get('/tracks', self._handle_get_tracks)
        app.router.add_post('/discover', self._handle_discover)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.peer.host, self.peer.port)
        await site.start()
        
        logger.info(f"Node started at {self.peer.address}")
    
    async def stop(self):
        """Stop the node and close all connections."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        # Close protocol session
        await self.protocol.close()
        
        logger.info("Node stopped")
    
    def add_track(self, track: Track, content: Optional[bytes] = None):
        """
        Add a track to the node's local storage.
        
        Args:
            track: Track metadata
            content: Optional audio content bytes
        """
        self.tracks[track.content_hash] = track
        self.peer.add_track(track.content_hash)
        
        if content:
            self.content_store.store(track.content_hash, content)
        
        logger.info(f"Added track: {track}")
    
    def get_track(self, content_hash: str) -> Optional[Track]:
        """
        Get track metadata by content hash.
        
        Args:
            content_hash: Content hash of the track
            
        Returns:
            Track metadata if available
        """
        return self.tracks.get(content_hash)
    
    def get_track_content(self, content_hash: str) -> Optional[bytes]:
        """
        Get track audio content by content hash.
        
        Args:
            content_hash: Content hash of the track
            
        Returns:
            Audio content bytes if available
        """
        return self.content_store.retrieve(content_hash)
    
    async def connect_to_peer(self, host: str, port: int) -> bool:
        """
        Connect to a peer and exchange information.
        
        Args:
            host: Peer host address
            port: Peer port
            
        Returns:
            True if connection successful
        """
        try:
            peer = await self.protocol.connect(host, port)
            if peer:
                self.peers[peer.peer_id] = peer
                logger.info(f"Connected to peer {peer}")
                return True
        except Exception as e:
            logger.error(f"Failed to connect to {host}:{port}: {e}")
        return False
    
    def discover_track(self, content_hash: str) -> List[Peer]:
        """
        Find peers that have a specific track.
        
        Args:
            content_hash: Content hash of the track
            
        Returns:
            List of peers that have the track
        """
        return [peer for peer in self.peers.values() if peer.has_track(content_hash)]
    
    async def request_track(self, content_hash: str) -> Optional[bytes]:
        """
        Request track content from peers.
        
        Args:
            content_hash: Content hash of the track
            
        Returns:
            Track content if found
        """
        # First check local storage
        content = self.get_track_content(content_hash)
        if content:
            return content
        
        # Find peers with the track
        peers_with_track = self.discover_track(content_hash)
        
        if not peers_with_track:
            logger.warning(f"No peers have track {content_hash[:16]}...")
            return None
        
        # Try to download from first available peer
        for peer in peers_with_track:
            try:
                content = await self.protocol.request_content(peer, content_hash)
                if content:
                    # Cache locally
                    self.content_store.store(content_hash, content)
                    logger.info(f"Downloaded track {content_hash[:16]}... from {peer}")
                    return content
            except Exception as e:
                logger.error(f"Failed to download from {peer}: {e}")
        
        return None
    
    def get_stats(self) -> dict:
        """
        Get node statistics.
        
        Returns:
            Dictionary of node statistics
        """
        return {
            "peer_id": self.peer.peer_id,
            "address": self.peer.address,
            "connected_peers": len(self.peers),
            "tracks": len(self.tracks),
            "storage_size": self.content_store.get_size(),
        }
    
    # HTTP handlers
    async def _handle_ping(self, request):
        """Handle ping request."""
        from aiohttp import web
        return web.json_response({"status": "ok", "peer_id": self.peer.peer_id})
    
    async def _handle_get_peers(self, request):
        """Handle request for peer list."""
        from aiohttp import web
        peers_data = [peer.to_dict() for peer in self.peers.values()]
        return web.json_response({"peers": peers_data})
    
    async def _handle_get_tracks(self, request):
        """Handle request for available tracks."""
        from aiohttp import web
        tracks_data = [track.to_dict() for track in self.tracks.values()]
        return web.json_response({"tracks": tracks_data})
    
    async def _handle_discover(self, request):
        """Handle peer discovery request."""
        from aiohttp import web
        data = await request.json()
        peer_data = data.get("peer")
        
        if peer_data:
            peer = Peer.from_dict(peer_data)
            self.peers[peer.peer_id] = peer
            logger.info(f"Discovered peer {peer}")
        
        return web.json_response({
            "peer": self.peer.to_dict(),
            "tracks": [track.to_dict() for track in self.tracks.values()],
        })
