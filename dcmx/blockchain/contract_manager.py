"""Smart contract manager for DCMX blockchain operations."""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from web3 import Web3
from web3.contract import Contract

from .contracts import (
    ERC721_ABI,
    ERC1155_ABI,
    ERC2981_ABI,
    ERC4907_ABI,
    MUSIC_NFT_ABI,
    DCMX_TOKEN_ABI,
    REWARD_DISTRIBUTOR_ABI,
    INTERFACE_IDS,
    TokenStandard,
    NFTMintRequest,
    EditionMintRequest,
    BatchMintRequest,
    TransferRequest,
    ApprovalRequest,
    RoyaltyInfo,
    RentalInfo,
)

logger = logging.getLogger(__name__)


@dataclass
class ContractConfig:
    """Configuration for a deployed contract."""
    address: str
    abi: list
    standard: TokenStandard
    name: Optional[str] = None


class ContractManager:
    """
    Manages interaction with DCMX smart contracts on blockchain.

    Supports:
    - ERC-721: Single NFTs for unique music tracks
    - ERC-1155: Multi-token for editions
    - ERC-2981: Royalty standard
    - ERC-4907: Rentable NFTs
    - ERC-20: DCMX utility token
    """

    def __init__(self, w3: Web3, signer_key: Optional[str] = None):
        self.w3 = w3
        self.signer_key = signer_key
        self._contracts: Dict[str, Contract] = {}
        self._configs: Dict[str, ContractConfig] = {}

        logger.info(f"ContractManager initialized, chain_id={w3.eth.chain_id}")

    @property
    def signer_address(self) -> Optional[str]:
        """Get signer wallet address."""
        if self.signer_key:
            from eth_account import Account
            return Account.from_key(self.signer_key).address
        return None

    def _get_abi_for_standard(self, standard: TokenStandard) -> list:
        """Get default ABI for token standard."""
        mapping = {
            TokenStandard.ERC20: DCMX_TOKEN_ABI,
            TokenStandard.ERC721: ERC721_ABI,
            TokenStandard.ERC1155: ERC1155_ABI,
            TokenStandard.ERC2981: ERC2981_ABI,
            TokenStandard.ERC4907: ERC4907_ABI,
        }
        return mapping.get(standard, ERC721_ABI)

    async def register_contract(
        self,
        name: str,
        address: str,
        standard: TokenStandard,
        abi: Optional[list] = None
    ) -> Contract:
        """
        Register a contract for management.

        Args:
            name: Identifier for the contract (e.g., "music_nft", "dcmx_token")
            address: Deployed contract address
            standard: Token standard enum
            abi: Optional custom ABI, defaults to standard ABI

        Returns:
            Web3 Contract instance
        """
        if abi is None:
            abi = self._get_abi_for_standard(standard)

        contract = self.w3.eth.contract(address=address, abi=abi)
        self._contracts[name] = contract
        self._configs[name] = ContractConfig(
            address=address,
            abi=abi,
            standard=standard,
            name=name
        )

        logger.info(f"Registered {standard.value} contract '{name}' at {address}")
        return contract

    def get_contract(self, name: str) -> Contract:
        """Get registered contract by name."""
        if name not in self._contracts:
            raise ValueError(f"Contract '{name}' not registered")
        return self._contracts[name]

    def _build_tx(self, gas: int = 300_000) -> Dict[str, Any]:
        """Build base transaction parameters."""
        if not self.signer_key:
            raise ValueError("Signer key required for transactions")

        return {
            'from': self.signer_address,
            'gas': gas,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.signer_address),
            'chainId': self.w3.eth.chain_id,
        }

    def _send_tx(self, tx: Dict) -> str:
        """Sign and send transaction."""
        if not self.signer_key:
            raise ValueError("Signer key required for transactions")

        from eth_account import Account
        signed = Account.sign_transaction(tx, self.signer_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()

    # ========================================================================
    # ERC-721 OPERATIONS
    # ========================================================================

    async def erc721_owner_of(self, contract_name: str, token_id: int) -> str:
        """Get owner of ERC-721 token."""
        contract = self.get_contract(contract_name)
        return contract.functions.ownerOf(token_id).call()

    async def erc721_balance_of(self, contract_name: str, owner: str) -> int:
        """Get ERC-721 token balance for owner."""
        contract = self.get_contract(contract_name)
        return contract.functions.balanceOf(owner).call()

    async def erc721_token_uri(self, contract_name: str, token_id: int) -> str:
        """Get token URI for ERC-721 token."""
        contract = self.get_contract(contract_name)
        return contract.functions.tokenURI(token_id).call()

    async def erc721_transfer_from(
        self,
        contract_name: str,
        request: TransferRequest
    ) -> str:
        """Transfer ERC-721 token (non-safe)."""
        contract = self.get_contract(contract_name)
        tx = contract.functions.transferFrom(
            request.from_address,
            request.to_address,
            request.token_id
        ).build_transaction(self._build_tx())
        return self._send_tx(tx)

    async def erc721_safe_transfer_from(
        self,
        contract_name: str,
        request: TransferRequest
    ) -> str:
        """Safe transfer ERC-721 token."""
        contract = self.get_contract(contract_name)
        if request.data:
            tx = contract.functions.safeTransferFrom(
                request.from_address,
                request.to_address,
                request.token_id,
                request.data
            ).build_transaction(self._build_tx())
        else:
            tx = contract.functions.safeTransferFrom(
                request.from_address,
                request.to_address,
                request.token_id
            ).build_transaction(self._build_tx())
        return self._send_tx(tx)

    async def erc721_approve(
        self,
        contract_name: str,
        to: str,
        token_id: int
    ) -> str:
        """Approve address for single ERC-721 token."""
        contract = self.get_contract(contract_name)
        tx = contract.functions.approve(to, token_id).build_transaction(self._build_tx())
        return self._send_tx(tx)

    async def erc721_set_approval_for_all(
        self,
        contract_name: str,
        operator: str,
        approved: bool = True
    ) -> str:
        """Set approval for all ERC-721 tokens."""
        contract = self.get_contract(contract_name)
        tx = contract.functions.setApprovalForAll(
            operator, approved
        ).build_transaction(self._build_tx())
        return self._send_tx(tx)

    async def erc721_get_approved(self, contract_name: str, token_id: int) -> str:
        """Get approved address for ERC-721 token."""
        contract = self.get_contract(contract_name)
        return contract.functions.getApproved(token_id).call()

    async def erc721_is_approved_for_all(
        self,
        contract_name: str,
        owner: str,
        operator: str
    ) -> bool:
        """Check if operator approved for all tokens."""
        contract = self.get_contract(contract_name)
        return contract.functions.isApprovedForAll(owner, operator).call()

    # ========================================================================
    # ERC-1155 OPERATIONS
    # ========================================================================

    async def erc1155_balance_of(
        self,
        contract_name: str,
        account: str,
        token_id: int
    ) -> int:
        """Get ERC-1155 token balance for account and token ID."""
        contract = self.get_contract(contract_name)
        return contract.functions.balanceOf(account, token_id).call()

    async def erc1155_balance_of_batch(
        self,
        contract_name: str,
        accounts: List[str],
        token_ids: List[int]
    ) -> List[int]:
        """Get batch balances for multiple accounts/token IDs."""
        contract = self.get_contract(contract_name)
        return contract.functions.balanceOfBatch(accounts, token_ids).call()

    async def erc1155_safe_transfer_from(
        self,
        contract_name: str,
        request: TransferRequest
    ) -> str:
        """Safe transfer ERC-1155 tokens."""
        contract = self.get_contract(contract_name)
        tx = contract.functions.safeTransferFrom(
            request.from_address,
            request.to_address,
            request.token_id,
            request.amount,
            request.data
        ).build_transaction(self._build_tx())
        return self._send_tx(tx)

    async def erc1155_safe_batch_transfer_from(
        self,
        contract_name: str,
        from_address: str,
        to_address: str,
        token_ids: List[int],
        amounts: List[int],
        data: bytes = b""
    ) -> str:
        """Batch transfer ERC-1155 tokens."""
        contract = self.get_contract(contract_name)
        tx = contract.functions.safeBatchTransferFrom(
            from_address,
            to_address,
            token_ids,
            amounts,
            data
        ).build_transaction(self._build_tx(gas=500_000))
        return self._send_tx(tx)

    async def erc1155_set_approval_for_all(
        self,
        contract_name: str,
        operator: str,
        approved: bool = True
    ) -> str:
        """Set approval for all ERC-1155 tokens."""
        contract = self.get_contract(contract_name)
        tx = contract.functions.setApprovalForAll(
            operator, approved
        ).build_transaction(self._build_tx())
        return self._send_tx(tx)

    async def erc1155_is_approved_for_all(
        self,
        contract_name: str,
        account: str,
        operator: str
    ) -> bool:
        """Check if operator approved for all ERC-1155 tokens."""
        contract = self.get_contract(contract_name)
        return contract.functions.isApprovedForAll(account, operator).call()

    async def erc1155_uri(self, contract_name: str, token_id: int) -> str:
        """Get URI for ERC-1155 token."""
        contract = self.get_contract(contract_name)
        return contract.functions.uri(token_id).call()

    # ========================================================================
    # ERC-2981 ROYALTY OPERATIONS
    # ========================================================================

    async def erc2981_royalty_info(
        self,
        contract_name: str,
        token_id: int,
        sale_price: int
    ) -> RoyaltyInfo:
        """Get royalty info for token sale."""
        contract = self.get_contract(contract_name)
        receiver, amount = contract.functions.royaltyInfo(token_id, sale_price).call()
        royalty_bps = (amount * 10000) // sale_price if sale_price > 0 else 0
        return RoyaltyInfo(
            receiver=receiver,
            royalty_amount=amount,
            royalty_bps=royalty_bps
        )

    # ========================================================================
    # ERC-4907 RENTABLE NFT OPERATIONS
    # ========================================================================

    async def erc4907_set_user(
        self,
        contract_name: str,
        token_id: int,
        user: str,
        expires: int
    ) -> str:
        """Set user (renter) for ERC-4907 token."""
        contract = self.get_contract(contract_name)
        tx = contract.functions.setUser(
            token_id, user, expires
        ).build_transaction(self._build_tx())
        return self._send_tx(tx)

    async def erc4907_user_of(self, contract_name: str, token_id: int) -> str:
        """Get current user (renter) of ERC-4907 token."""
        contract = self.get_contract(contract_name)
        return contract.functions.userOf(token_id).call()

    async def erc4907_user_expires(self, contract_name: str, token_id: int) -> int:
        """Get rental expiration timestamp for ERC-4907 token."""
        contract = self.get_contract(contract_name)
        return contract.functions.userExpires(token_id).call()

    async def erc4907_get_rental_info(
        self,
        contract_name: str,
        token_id: int
    ) -> RentalInfo:
        """Get full rental info for ERC-4907 token."""
        user = await self.erc4907_user_of(contract_name, token_id)
        expires = await self.erc4907_user_expires(contract_name, token_id)
        return RentalInfo(user=user, expires=expires, token_id=token_id)

    # ========================================================================
    # EIP-165 INTERFACE DETECTION
    # ========================================================================

    async def supports_interface(
        self,
        contract_name: str,
        interface_id: str
    ) -> bool:
        """Check if contract supports interface (EIP-165)."""
        contract = self.get_contract(contract_name)
        try:
            return contract.functions.supportsInterface(interface_id).call()
        except Exception:
            return False

    async def detect_standards(self, contract_name: str) -> List[str]:
        """Detect which token standards a contract supports."""
        supported = []
        for name, iface_id in INTERFACE_IDS.items():
            if await self.supports_interface(contract_name, iface_id):
                supported.append(name)
        return supported

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def get_gas_estimate(self, transaction: Dict) -> int:
        """Estimate gas for transaction."""
        try:
            return self.w3.eth.estimate_gas(transaction)
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}")
            return 300_000

    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """Check status of submitted transaction."""
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                "status": "success" if receipt.get("status") == 1 else "failed",
                "block_number": receipt.get("blockNumber"),
                "gas_used": receipt.get("gasUsed"),
                "logs": receipt.get("logs", [])
            }
        except Exception as e:
            return {"status": "pending", "error": str(e)}

    async def wait_for_confirmation(
        self,
        tx_hash: str,
        timeout: int = 120,
        poll_interval: float = 2.0
    ) -> Dict[str, Any]:
        """Wait for transaction confirmation."""
        import asyncio
        import time

        start = time.time()
        while time.time() - start < timeout:
            status = await self.get_transaction_status(tx_hash)
            if status["status"] != "pending":
                return status
            await asyncio.sleep(poll_interval)

        return {"status": "timeout", "tx_hash": tx_hash}


class ERC721Handler:
    """High-level handler for ERC-721 operations."""

    def __init__(self, manager: ContractManager, contract_name: str):
        self.manager = manager
        self.contract_name = contract_name

    async def owner_of(self, token_id: int) -> str:
        return await self.manager.erc721_owner_of(self.contract_name, token_id)

    async def balance_of(self, owner: str) -> int:
        return await self.manager.erc721_balance_of(self.contract_name, owner)

    async def token_uri(self, token_id: int) -> str:
        return await self.manager.erc721_token_uri(self.contract_name, token_id)

    async def transfer(
        self,
        from_addr: str,
        to_addr: str,
        token_id: int,
        safe: bool = True
    ) -> str:
        request = TransferRequest(
            from_address=from_addr,
            to_address=to_addr,
            token_id=token_id
        )
        if safe:
            return await self.manager.erc721_safe_transfer_from(self.contract_name, request)
        return await self.manager.erc721_transfer_from(self.contract_name, request)

    async def approve(self, to: str, token_id: int) -> str:
        return await self.manager.erc721_approve(self.contract_name, to, token_id)

    async def set_approval_for_all(self, operator: str, approved: bool = True) -> str:
        return await self.manager.erc721_set_approval_for_all(
            self.contract_name, operator, approved
        )

    async def get_approved(self, token_id: int) -> str:
        return await self.manager.erc721_get_approved(self.contract_name, token_id)

    async def is_approved_for_all(self, owner: str, operator: str) -> bool:
        return await self.manager.erc721_is_approved_for_all(
            self.contract_name, owner, operator
        )


class ERC1155Handler:
    """High-level handler for ERC-1155 operations."""

    def __init__(self, manager: ContractManager, contract_name: str):
        self.manager = manager
        self.contract_name = contract_name

    async def balance_of(self, account: str, token_id: int) -> int:
        return await self.manager.erc1155_balance_of(
            self.contract_name, account, token_id
        )

    async def balance_of_batch(
        self,
        accounts: List[str],
        token_ids: List[int]
    ) -> List[int]:
        return await self.manager.erc1155_balance_of_batch(
            self.contract_name, accounts, token_ids
        )

    async def transfer(
        self,
        from_addr: str,
        to_addr: str,
        token_id: int,
        amount: int,
        data: bytes = b""
    ) -> str:
        request = TransferRequest(
            from_address=from_addr,
            to_address=to_addr,
            token_id=token_id,
            amount=amount,
            data=data
        )
        return await self.manager.erc1155_safe_transfer_from(self.contract_name, request)

    async def batch_transfer(
        self,
        from_addr: str,
        to_addr: str,
        token_ids: List[int],
        amounts: List[int],
        data: bytes = b""
    ) -> str:
        return await self.manager.erc1155_safe_batch_transfer_from(
            self.contract_name, from_addr, to_addr, token_ids, amounts, data
        )

    async def set_approval_for_all(self, operator: str, approved: bool = True) -> str:
        return await self.manager.erc1155_set_approval_for_all(
            self.contract_name, operator, approved
        )

    async def is_approved_for_all(self, account: str, operator: str) -> bool:
        return await self.manager.erc1155_is_approved_for_all(
            self.contract_name, account, operator
        )

    async def uri(self, token_id: int) -> str:
        return await self.manager.erc1155_uri(self.contract_name, token_id)


class ERC4907Handler:
    """High-level handler for ERC-4907 rentable NFT operations."""

    def __init__(self, manager: ContractManager, contract_name: str):
        self.manager = manager
        self.contract_name = contract_name

    async def set_user(self, token_id: int, user: str, expires: int) -> str:
        return await self.manager.erc4907_set_user(
            self.contract_name, token_id, user, expires
        )

    async def user_of(self, token_id: int) -> str:
        return await self.manager.erc4907_user_of(self.contract_name, token_id)

    async def user_expires(self, token_id: int) -> int:
        return await self.manager.erc4907_user_expires(self.contract_name, token_id)

    async def get_rental_info(self, token_id: int) -> RentalInfo:
        return await self.manager.erc4907_get_rental_info(self.contract_name, token_id)

    async def is_rented(self, token_id: int) -> bool:
        """Check if token is currently rented."""
        import time
        expires = await self.user_expires(token_id)
        return expires > int(time.time())
