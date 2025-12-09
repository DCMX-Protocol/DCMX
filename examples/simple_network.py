#!/usr/bin/env python3
"""
Simple example demonstrating DCMX mesh music network.

This example creates two nodes and shows how they can:
1. Share track metadata
2. Connect to each other
3. Discover available tracks
"""

import asyncio
import logging
from dcmx.core.node import Node
from dcmx.core.track import Track


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """Run a simple two-node network example."""
    
    print("=" * 60)
    print("DCMX Mesh Music Network - Simple Example")
    print("=" * 60)
    print()
    
    # Create two nodes
    print("Creating nodes...")
    node1 = Node(host="127.0.0.1", port=8080)
    node2 = Node(host="127.0.0.1", port=8081)
    
    print(f"Node 1: {node1.peer.peer_id[:8]}... @ {node1.peer.address}")
    print(f"Node 2: {node2.peer.peer_id[:8]}... @ {node2.peer.address}")
    print()
    
    # Create some sample tracks
    print("Creating sample tracks...")
    
    # Simulate audio content
    audio_content_1 = b"Sample audio data for track 1" * 1000
    audio_content_2 = b"Sample audio data for track 2" * 1000
    
    track1 = Track(
        title="Mesh Melody",
        artist="Decentralized Artist",
        content_hash=Track.compute_content_hash(audio_content_1),
        duration=180,
        size=len(audio_content_1),
        format="mp3",
        genre="Electronic",
        year=2024,
    )
    
    track2 = Track(
        title="P2P Beats",
        artist="Network Musician",
        content_hash=Track.compute_content_hash(audio_content_2),
        duration=220,
        size=len(audio_content_2),
        format="mp3",
        genre="Electronic",
        year=2024,
    )
    
    # Add tracks to nodes
    print("Adding tracks to nodes...")
    node1.add_track(track1, audio_content_1)
    node2.add_track(track2, audio_content_2)
    
    print(f"  Node 1 has: {track1.title}")
    print(f"  Node 2 has: {track2.title}")
    print()
    
    # Start nodes
    print("Starting nodes...")
    await node1.start()
    await node2.start()
    print("Nodes started successfully!")
    print()
    
    # Connect nodes
    print("Connecting Node 2 to Node 1...")
    connected = await node2.connect_to_peer("127.0.0.1", 8080)
    
    if connected:
        print("✓ Nodes connected successfully!")
        print()
        
        # Show network state
        print("Network State:")
        print(f"  Node 1 connected peers: {len(node1.peers)}")
        print(f"  Node 2 connected peers: {len(node2.peers)}")
        print()
        
        # Show track discovery
        print("Track Discovery:")
        print(f"  Node 1 knows about {len(node1.tracks)} tracks")
        print(f"  Node 2 knows about {len(node2.tracks)} tracks")
        print()
        
        # Show statistics
        print("Node 1 Statistics:")
        stats1 = node1.get_stats()
        for key, value in stats1.items():
            print(f"  {key}: {value}")
        print()
        
        print("Node 2 Statistics:")
        stats2 = node2.get_stats()
        for key, value in stats2.items():
            print(f"  {key}: {value}")
        print()
        
        # Demonstrate content request (if implemented)
        print("Content Request Test:")
        print(f"  Node 2 requesting track from Node 1...")
        peers_with_track = node2.discover_track(track1.content_hash)
        print(f"  Found {len(peers_with_track)} peers with the track")
        
    else:
        print("✗ Failed to connect nodes")
    
    print()
    print("=" * 60)
    print("Example complete! Press Ctrl+C to exit...")
    print("=" * 60)
    
    # Keep running for a bit
    try:
        await asyncio.sleep(5)
    except KeyboardInterrupt:
        pass
    
    # Cleanup
    print("\nShutting down nodes...")
    await node1.stop()
    await node2.stop()
    print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
