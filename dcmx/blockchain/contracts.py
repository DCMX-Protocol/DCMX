"""
DCMX Smart Contracts - Complete Token Standards & Python Integration

This module contains all Solidity contract ABIs and Python interfaces for DCMX.
Supports: ERC-721, ERC-1155, ERC-2981, ERC-4907, ERC-20

Deploy to: Ethereum mainnet or Polygon for lower gas fees.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES FOR TOKEN OPERATIONS
# ============================================================================

@dataclass
class TokenMetadata:
    """NFT metadata structure."""
    name: str
    description: str
    image: str
    external_url: Optional[str] = None
    animation_url: Optional[str] = None
    attributes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class NFTMintRequest:
    """Request structure for minting ERC-721 NFTs."""
    to: str
    token_id: int
    token_uri: str
    royalty_recipient: Optional[str] = None
    royalty_bps: int = 1000  # 10% default


@dataclass
class EditionMintRequest:
    """Request structure for minting ERC-1155 editions."""
    to: str
    token_id: int
    amount: int
    data: bytes = b""


@dataclass
class BatchMintRequest:
    """Request structure for batch minting ERC-1155 tokens."""
    to: str
    token_ids: List[int] = field(default_factory=list)
    amounts: List[int] = field(default_factory=list)
    data: bytes = b""


@dataclass
class TransferRequest:
    """Request structure for token transfers."""
    from_address: str
    to_address: str
    token_id: int
    amount: int = 1  # For ERC-1155
    data: bytes = b""


@dataclass
class ApprovalRequest:
    """Request structure for token approvals."""
    owner: str
    operator: str
    approved: bool = True
    token_id: Optional[int] = None  # For single token approval


@dataclass
class RoyaltyInfo:
    """ERC-2981 royalty information."""
    receiver: str
    royalty_amount: int  # In wei or token units
    royalty_bps: int  # Basis points (100 = 1%)


@dataclass
class RentalInfo:
    """ERC-4907 rental information."""
    user: str
    expires: int  # Unix timestamp
    token_id: int


class TokenStandard(Enum):
    """Supported token standards."""
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    ERC2981 = "ERC2981"
    ERC4907 = "ERC4907"


# ============================================================================
# ERC-721 FULL ABI (OpenZeppelin Standard + Extensions)
# ============================================================================

ERC721_ABI = json.loads("""
[
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"}
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "bool", "name": "approved", "type": "bool"}
        ],
        "name": "setApprovalForAll",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getApproved",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "operator", "type": "address"}
        ],
        "name": "isApprovedForAll",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": true, "internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "approved", "type": "address"},
            {"indexed": true, "internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "Approval",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "operator", "type": "address"},
            {"indexed": false, "internalType": "bool", "name": "approved", "type": "bool"}
        ],
        "name": "ApprovalForAll",
        "type": "event"
    }
]
""")


# ============================================================================
# ERC-1155 FULL ABI (Multi-Token Standard for Editions)
# ============================================================================

ERC1155_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "uint256", "name": "id", "type": "uint256"}
        ],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address[]", "name": "accounts", "type": "address[]"},
            {"internalType": "uint256[]", "name": "ids", "type": "uint256[]"}
        ],
        "name": "balanceOfBatch",
        "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "id", "type": "uint256"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"}
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256[]", "name": "ids", "type": "uint256[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
            {"internalType": "bytes", "name": "data", "type": "bytes"}
        ],
        "name": "safeBatchTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "bool", "name": "approved", "type": "bool"}
        ],
        "name": "setApprovalForAll",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "account", "type": "address"},
            {"internalType": "address", "name": "operator", "type": "address"}
        ],
        "name": "isApprovedForAll",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "id", "type": "uint256"}],
        "name": "uri",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "operator", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "id", "type": "uint256"},
            {"indexed": false, "internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "TransferSingle",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "operator", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": false, "internalType": "uint256[]", "name": "ids", "type": "uint256[]"},
            {"indexed": false, "internalType": "uint256[]", "name": "values", "type": "uint256[]"}
        ],
        "name": "TransferBatch",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "account", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "operator", "type": "address"},
            {"indexed": false, "internalType": "bool", "name": "approved", "type": "bool"}
        ],
        "name": "ApprovalForAll",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": false, "internalType": "string", "name": "value", "type": "string"},
            {"indexed": true, "internalType": "uint256", "name": "id", "type": "uint256"}
        ],
        "name": "URI",
        "type": "event"
    }
]
""")


# ============================================================================
# ERC-2981 ROYALTY STANDARD ABI
# ============================================================================

ERC2981_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "uint256", "name": "salePrice", "type": "uint256"}
        ],
        "name": "royaltyInfo",
        "outputs": [
            {"internalType": "address", "name": "receiver", "type": "address"},
            {"internalType": "uint256", "name": "royaltyAmount", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]
""")


# ============================================================================
# ERC-4907 RENTABLE NFT STANDARD ABI
# ============================================================================

ERC4907_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint64", "name": "expires", "type": "uint64"}
        ],
        "name": "setUser",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "userOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "userExpires",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"indexed": true, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": false, "internalType": "uint64", "name": "expires", "type": "uint64"}
        ],
        "name": "UpdateUser",
        "type": "event"
    }
]
""")


# ============================================================================
# DCMX MUSIC NFT ABI (ERC-721 + ERC-2981 + Custom Extensions)
# ============================================================================

MUSIC_NFT_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "string", "name": "title", "type": "string"},
            {"internalType": "string", "name": "artist", "type": "string"},
            {"internalType": "string", "name": "contentHash", "type": "string"},
            {"internalType": "uint256", "name": "editionNumber", "type": "uint256"},
            {"internalType": "uint256", "name": "maxEditions", "type": "uint256"},
            {"internalType": "uint96", "name": "royaltyBps", "type": "uint96"}
        ],
        "name": "mintMusic",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getMetadata",
        "outputs": [
            {"internalType": "string", "name": "title", "type": "string"},
            {"internalType": "string", "name": "artist", "type": "string"},
            {"internalType": "string", "name": "contentHash", "type": "string"},
            {"internalType": "uint256", "name": "editionNumber", "type": "uint256"},
            {"internalType": "uint256", "name": "maxEditions", "type": "uint256"},
            {"internalType": "address", "name": "artistWallet", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "from", "type": "address"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "bytes", "name": "data", "type": "bytes"}
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "operator", "type": "address"},
            {"internalType": "bool", "name": "approved", "type": "bool"}
        ],
        "name": "setApprovalForAll",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "getApproved",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "operator", "type": "address"}
        ],
        "name": "isApprovedForAll",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "tokenId", "type": "uint256"},
            {"internalType": "uint256", "name": "salePrice", "type": "uint256"}
        ],
        "name": "royaltyInfo",
        "outputs": [
            {"internalType": "address", "name": "receiver", "type": "address"},
            {"internalType": "uint256", "name": "royaltyAmount", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes4", "name": "interfaceId", "type": "bytes4"}],
        "name": "supportsInterface",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]
""")


# ============================================================================
# DCMX TOKEN ABI (ERC-20)
# ============================================================================

DCMX_TOKEN_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "sender", "type": "address"},
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "transferFrom",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "spender", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "address", "name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"internalType": "uint8", "name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "from", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "to", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": true, "internalType": "address", "name": "spender", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "value", "type": "uint256"}
        ],
        "name": "Approval",
        "type": "event"
    }
]
""")


# ============================================================================
# REWARD DISTRIBUTOR ABI
# ============================================================================

REWARD_DISTRIBUTOR_ABI = json.loads("""
[
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "rewardType", "type": "string"}
        ],
        "name": "distributeReward",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address[]", "name": "users", "type": "address[]"},
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"},
            {"internalType": "string", "name": "rewardType", "type": "string"}
        ],
        "name": "batchDistributeReward",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "totalRewardsEarned",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "string", "name": "rewardType", "type": "string"}
        ],
        "name": "rewardsByType",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": false,
        "inputs": [
            {"indexed": true, "internalType": "address", "name": "user", "type": "address"},
            {"indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": false, "internalType": "string", "name": "rewardType", "type": "string"}
        ],
        "name": "RewardDistributed",
        "type": "event"
    }
]
""")


# ============================================================================
# INTERFACE ID CONSTANTS (EIP-165)
# ============================================================================

INTERFACE_IDS = {
    "ERC165": "0x01ffc9a7",
    "ERC721": "0x80ac58cd",
    "ERC721Metadata": "0x5b5e139f",
    "ERC721Enumerable": "0x780e9d63",
    "ERC1155": "0xd9b67a26",
    "ERC1155MetadataURI": "0x0e89341c",
    "ERC2981": "0x2a55205a",
    "ERC4907": "0xad092b5c",
}


# ============================================================================
# PYTHON BLOCKCHAIN MANAGER
# ============================================================================

class BlockchainManager:
    """Manage DCMX smart contracts on Ethereum/Polygon."""

    def __init__(
        self,
        rpc_url: str,
        private_key: str,
        music_nft_address: Optional[str] = None,
        dcmx_token_address: Optional[str] = None,
        reward_distributor_address: Optional[str] = None,
    ):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)

        self.music_nft_address = music_nft_address
        self.dcmx_token_address = dcmx_token_address
        self.reward_distributor_address = reward_distributor_address

        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")

        logger.info(f"Connected to blockchain: {self.w3.eth.chain_id}")

    def _build_tx(self, gas: int = 300_000) -> Dict[str, Any]:
        """Build base transaction dict."""
        return {
            'from': self.account.address,
            'gas': gas,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.w3.eth.chain_id,
        }

    def _send_tx(self, tx: Dict) -> str:
        """Sign and send transaction, return tx hash."""
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    async def mint_music_nft(
        self,
        title: str,
        artist: str,
        content_hash: str,
        edition_number: int,
        max_editions: int,
        royalty_percentage: int = 1000,
    ) -> Dict[str, Any]:
        """Mint a music NFT on-chain."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )

        tx = contract.functions.mintMusic(
            self.account.address,
            title,
            artist,
            content_hash,
            edition_number,
            max_editions,
            royalty_percentage,
        ).build_transaction(self._build_tx())

        tx_hash = self._send_tx(tx)
        logger.info(f"Minted NFT: {title} by {artist}, tx: {tx_hash}")

        return {
            "tx_hash": tx_hash,
            "title": title,
            "artist": artist,
            "status": "pending",
        }

    async def owner_of(self, token_id: int) -> str:
        """Get owner of ERC-721 token."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )
        return contract.functions.ownerOf(token_id).call()

    async def get_token_uri(self, token_id: int) -> str:
        """Get token URI for ERC-721 token."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )
        return contract.functions.tokenURI(token_id).call()

    async def transfer_nft(
        self,
        from_address: str,
        to_address: str,
        token_id: int,
        safe: bool = True
    ) -> Dict[str, Any]:
        """Transfer ERC-721 token."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )

        if safe:
            tx = contract.functions.safeTransferFrom(
                from_address, to_address, token_id
            ).build_transaction(self._build_tx())
        else:
            tx = contract.functions.transferFrom(
                from_address, to_address, token_id
            ).build_transaction(self._build_tx())

        tx_hash = self._send_tx(tx)
        logger.info(f"Transferred NFT {token_id} from {from_address} to {to_address}")

        return {"tx_hash": tx_hash, "status": "pending"}

    async def approve_nft(
        self,
        to_address: str,
        token_id: int
    ) -> Dict[str, Any]:
        """Approve address for single ERC-721 token."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )

        tx = contract.functions.approve(
            to_address, token_id
        ).build_transaction(self._build_tx())

        tx_hash = self._send_tx(tx)
        return {"tx_hash": tx_hash, "status": "pending"}

    async def set_approval_for_all_nft(
        self,
        operator: str,
        approved: bool = True
    ) -> Dict[str, Any]:
        """Set approval for all ERC-721 tokens."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )

        tx = contract.functions.setApprovalForAll(
            operator, approved
        ).build_transaction(self._build_tx())

        tx_hash = self._send_tx(tx)
        return {"tx_hash": tx_hash, "status": "pending"}

    async def get_approved(self, token_id: int) -> str:
        """Get approved address for ERC-721 token."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )
        return contract.functions.getApproved(token_id).call()

    async def is_approved_for_all_nft(self, owner: str, operator: str) -> bool:
        """Check if operator is approved for all tokens of owner."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )
        return contract.functions.isApprovedForAll(owner, operator).call()

    async def get_royalty_info(
        self,
        token_id: int,
        sale_price: int
    ) -> RoyaltyInfo:
        """Get ERC-2981 royalty info for token."""
        if not self.music_nft_address:
            raise ValueError("MusicNFT contract not configured")

        contract = self.w3.eth.contract(
            address=self.music_nft_address,
            abi=MUSIC_NFT_ABI
        )
        receiver, amount = contract.functions.royaltyInfo(token_id, sale_price).call()
        royalty_bps = (amount * 10000) // sale_price if sale_price > 0 else 0

        return RoyaltyInfo(
            receiver=receiver,
            royalty_amount=amount,
            royalty_bps=royalty_bps
        )

    async def distribute_reward(
        self,
        user_address: str,
        amount_dcmx: float,
        reward_type: str,
    ) -> Dict[str, Any]:
        """Distribute DCMX token rewards to user."""
        if not self.reward_distributor_address:
            raise ValueError("RewardDistributor contract not configured")

        amount_wei = self.w3.to_wei(amount_dcmx, 'ether')

        contract = self.w3.eth.contract(
            address=self.reward_distributor_address,
            abi=REWARD_DISTRIBUTOR_ABI
        )

        tx = contract.functions.distributeReward(
            user_address,
            amount_wei,
            reward_type,
        ).build_transaction(self._build_tx(gas=200_000))

        tx_hash = self._send_tx(tx)
        logger.info(f"Reward distributed: {amount_dcmx} DCMX to {user_address}")

        return {
            "tx_hash": tx_hash,
            "recipient": user_address,
            "amount": amount_dcmx,
            "reward_type": reward_type,
            "status": "pending",
        }

    async def get_token_balance(self, wallet_address: str) -> float:
        """Get DCMX token balance for wallet."""
        if not self.dcmx_token_address:
            raise ValueError("DCMXToken contract not configured")

        contract = self.w3.eth.contract(
            address=self.dcmx_token_address,
            abi=DCMX_TOKEN_ABI
        )

        balance_wei = contract.functions.balanceOf(wallet_address).call()
        return float(self.w3.from_wei(balance_wei, 'ether'))

    async def get_total_token_supply(self) -> float:
        """Get total DCMX token supply."""
        if not self.dcmx_token_address:
            raise ValueError("DCMXToken contract not configured")

        contract = self.w3.eth.contract(
            address=self.dcmx_token_address,
            abi=DCMX_TOKEN_ABI
        )

        supply_wei = contract.functions.totalSupply().call()
        return float(self.w3.from_wei(supply_wei, 'ether'))

    async def supports_interface(
        self,
        contract_address: str,
        interface_id: str
    ) -> bool:
        """Check EIP-165 interface support."""
        contract = self.w3.eth.contract(
            address=contract_address,
            abi=ERC721_ABI
        )
        return contract.functions.supportsInterface(interface_id).call()


# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

NETWORKS = {
    "polygon_mainnet": {
        "rpc_url": "https://polygon-rpc.com/",
        "chain_id": 137,
        "name": "Polygon (Recommended for low fees)",
    },
    "polygon_mumbai": {
        "rpc_url": "https://rpc-mumbai.maticvigil.com/",
        "chain_id": 80001,
        "name": "Polygon Mumbai Testnet",
    },
    "ethereum_mainnet": {
        "rpc_url": "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY",
        "chain_id": 1,
        "name": "Ethereum Mainnet",
    },
    "ethereum_sepolia": {
        "rpc_url": "https://eth-sepolia.g.alchemy.com/v2/YOUR_KEY",
        "chain_id": 11155111,
        "name": "Ethereum Sepolia Testnet",
    },
}
