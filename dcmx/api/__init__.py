"""
DCMX Web3 Economy REST API

Provides HTTP endpoints for:
- Wallet management
- NFT creation & purchases
- Song voting & skip tracking
- User rewards & earnings
- Artist analytics
- Platform statistics
"""

from .server import app, start_server

__all__ = ["app", "start_server"]
