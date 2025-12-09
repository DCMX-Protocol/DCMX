# DCMX - Decentralized Mesh Music Network

DCMX is a peer-to-peer music sharing and streaming platform built on mesh network principles. It enables decentralized music distribution without relying on centralized servers, giving artists and listeners direct control over their content.

## Features

- **Decentralized Architecture**: No central server - all nodes are equal peers
- **Content-Addressed Storage**: Music files are identified by their cryptographic hash
- **Peer Discovery**: Automatic discovery of peers and available content
- **Direct Distribution**: Share music directly between peers without intermediaries
- **Resilient Network**: Mesh topology ensures network resilience and redundancy

## Installation

```bash
# Clone the repository
git clone https://github.com/DCMX-Protocol/DCMX.git
cd DCMX

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

### Starting a Node

Start a DCMX node to join the network:

```bash
dcmx start --host 127.0.0.1 --port 8080
```

### Connecting to Other Peers

Connect to existing peers in the network:

```bash
dcmx start --host 127.0.0.1 --port 8081 --peers 127.0.0.1:8080
```

### Adding Music

Add a music track to your node:

```bash
dcmx add song.mp3 --title "My Song" --artist "Artist Name" --album "Album Name"
```

### Viewing Available Tracks

List all tracks available on your node:

```bash
dcmx list
```

### Node Statistics

View statistics about your node:

```bash
dcmx stats
```

## Architecture

### Core Components

- **Node**: Main entry point that manages local content and peer connections
- **Track**: Represents music metadata with content-addressed storage
- **Peer**: Represents a peer in the mesh network
- **Protocol**: Handles network communication between peers
- **ContentStore**: Manages local storage of music files

### Network Protocol

DCMX uses HTTP-based communication for simplicity:

- `GET /ping` - Health check
- `GET /peers` - Get list of known peers
- `GET /tracks` - Get available tracks metadata
- `POST /discover` - Peer discovery and handshake
- `GET /content/{hash}` - Download track content

### Content Addressing

Music files are identified by their SHA-256 hash, ensuring:
- **Immutability**: Content cannot be modified without changing its identifier
- **Deduplication**: Identical files share the same hash
- **Verification**: Content integrity can be verified by recomputing the hash

## Use Cases

- **Independent Artists**: Share music directly with fans without intermediaries
- **Music Collectors**: Build distributed collections across multiple nodes
- **Community Radio**: Decentralized music streaming for communities
- **Resilient Archives**: Preserve music across distributed storage

## Development

### Project Structure

```
dcmx/
├── core/           # Core functionality
│   ├── node.py     # Main node implementation
│   └── track.py    # Track metadata
├── network/        # Network layer
│   ├── peer.py     # Peer representation
│   └── protocol.py # Communication protocol
├── storage/        # Storage layer
│   └── content_store.py  # Content storage
└── cli.py          # Command-line interface
```

### Running Tests

```bash
pytest tests/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.