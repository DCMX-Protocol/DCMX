"""Command-line interface for DCMX mesh music network."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from dcmx.core.node import Node
from dcmx.core.track import Track


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def start_node(args):
    """Start a DCMX node."""
    node = Node(host=args.host, port=args.port)
    
    print(f"Starting DCMX node...")
    print(f"  Peer ID: {node.peer.peer_id}")
    print(f"  Address: {node.peer.address}")
    print(f"  Data directory: {node.data_dir}")
    
    await node.start()
    
    # Connect to bootstrap peers if provided
    if args.peers:
        for peer_addr in args.peers:
            try:
                host, port = peer_addr.split(":")
                print(f"Connecting to peer {host}:{port}...")
                await node.connect_to_peer(host, int(port))
            except Exception as e:
                print(f"Failed to connect to {peer_addr}: {e}")
    
    print("\nNode is running. Press Ctrl+C to stop.")
    
    try:
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping node...")
        await node.stop()


async def add_track(args):
    """Add a track to the network."""
    if not args.file.exists():
        print(f"Error: File not found: {args.file}")
        return
    
    # Read file content
    content = args.file.read_bytes()
    
    # Compute content hash
    content_hash = Track.compute_content_hash(content)
    
    # Create track metadata
    track = Track(
        title=args.title or args.file.stem,
        artist=args.artist or "Unknown Artist",
        content_hash=content_hash,
        duration=args.duration or 0,
        size=len(content),
        format=args.format or "mp3",
        album=args.album,
        year=args.year,
        genre=args.genre,
    )
    
    # Add to node
    node = Node(host=args.host, port=args.port)
    node.add_track(track, content)
    
    print(f"Track added successfully!")
    print(f"  Title: {track.title}")
    print(f"  Artist: {track.artist}")
    print(f"  Content Hash: {track.content_hash}")
    print(f"  Size: {track.size} bytes")


def list_tracks(args):
    """List tracks available on a node."""
    node = Node(host=args.host, port=args.port)
    
    if not node.tracks:
        print("No tracks available.")
        return
    
    print(f"Available tracks ({len(node.tracks)}):\n")
    for track in node.tracks.values():
        print(f"  {track}")
        print(f"    Hash: {track.content_hash}")
        print(f"    Size: {track.size} bytes")
        print()


def show_stats(args):
    """Show node statistics."""
    node = Node(host=args.host, port=args.port)
    stats = node.get_stats()
    
    print("DCMX Node Statistics:")
    print(f"  Peer ID: {stats['peer_id']}")
    print(f"  Address: {stats['address']}")
    print(f"  Connected Peers: {stats['connected_peers']}")
    print(f"  Tracks: {stats['tracks']}")
    print(f"  Storage Size: {stats['storage_size']} bytes")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DCMX - Decentralized Mesh Music Network"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start node command
    start_parser = subparsers.add_parser("start", help="Start a DCMX node")
    start_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1)"
    )
    start_parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    start_parser.add_argument(
        "--peers",
        nargs="+",
        help="Bootstrap peers to connect to (format: host:port)"
    )
    
    # Add track command
    add_parser = subparsers.add_parser("add", help="Add a track to the network")
    add_parser.add_argument("file", type=Path, help="Audio file to add")
    add_parser.add_argument("--title", help="Track title")
    add_parser.add_argument("--artist", help="Artist name")
    add_parser.add_argument("--album", help="Album name")
    add_parser.add_argument("--year", type=int, help="Release year")
    add_parser.add_argument("--genre", help="Genre")
    add_parser.add_argument("--duration", type=int, help="Duration in seconds")
    add_parser.add_argument("--format", help="Audio format (default: mp3)")
    add_parser.add_argument("--host", default="127.0.0.1", help="Node host")
    add_parser.add_argument("--port", type=int, default=8080, help="Node port")
    
    # List tracks command
    list_parser = subparsers.add_parser("list", help="List available tracks")
    list_parser.add_argument("--host", default="127.0.0.1", help="Node host")
    list_parser.add_argument("--port", type=int, default=8080, help="Node port")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show node statistics")
    stats_parser.add_argument("--host", default="127.0.0.1", help="Node host")
    stats_parser.add_argument("--port", type=int, default=8080, help="Node port")
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == "start":
        asyncio.run(start_node(args))
    elif args.command == "add":
        asyncio.run(add_track(args))
    elif args.command == "list":
        list_tracks(args)
    elif args.command == "stats":
        show_stats(args)


if __name__ == "__main__":
    main()
