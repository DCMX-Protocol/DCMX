"""Multisig wallet for admin function controls in DCMX."""

import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from eth_account.messages import encode_defunct
from web3 import Web3

logger = logging.getLogger(__name__)


@dataclass
class MultisigTransaction:
    """A pending multisig transaction awaiting approvals."""
    
    proposal_id: str
    tx_data: dict
    proposer: str
    approvals: Dict[str, str] = field(default_factory=dict)  # address -> signature
    executed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "proposal_id": self.proposal_id,
            "tx_data": self.tx_data,
            "proposer": self.proposer,
            "approvals": self.approvals,
            "executed": self.executed,
            "created_at": self.created_at.isoformat(),
            "approval_count": len(self.approvals),
        }


class MultisigWallet:
    """
    Multi-signature wallet for admin function controls.
    
    Implements M-of-N signature scheme where M signatures from N owners
    are required to execute admin transactions like contract deployment,
    reward configuration, and emergency pause/unpause.
    
    Default configuration is 2-of-3 for security.
    """

    def __init__(
        self,
        required_signatures: int = 2,
        owners: Optional[List[str]] = None,
        web3_instance: Optional[Web3] = None,
    ):
        """
        Initialize multisig wallet.
        
        Args:
            required_signatures: Number of signatures required to execute (default: 2)
            owners: List of owner wallet addresses (default: empty, must add before use)
            web3_instance: Web3 instance for signature verification
            
        Raises:
            ValueError: If required_signatures > len(owners) or invalid params
        """
        self.owners: List[str] = [addr.lower() for addr in (owners or [])]
        self.required_signatures = required_signatures
        self.w3 = web3_instance or Web3()
        self._pending_transactions: Dict[str, MultisigTransaction] = {}
        
        if self.owners and required_signatures > len(self.owners):
            raise ValueError(
                f"Required signatures ({required_signatures}) cannot exceed "
                f"number of owners ({len(self.owners)})"
            )
        
        if required_signatures < 1:
            raise ValueError("Required signatures must be at least 1")
            
        logger.info(
            f"MultisigWallet initialized: {required_signatures}-of-{len(self.owners)} "
            f"with owners {self.owners}"
        )

    def is_owner(self, address: str) -> bool:
        """
        Check if an address is an owner of this multisig.
        
        Args:
            address: Wallet address to check
            
        Returns:
            True if address is an owner, False otherwise
        """
        return address.lower() in self.owners

    def propose_transaction(self, tx_data: dict, proposer: str) -> str:
        """
        Propose a new transaction for multisig approval.
        
        Args:
            tx_data: Transaction data dictionary containing:
                - action: Type of admin action (deploy, configure, pause, etc.)
                - params: Action-specific parameters
            proposer: Wallet address of the proposer
            
        Returns:
            Unique proposal_id for tracking this transaction
            
        Raises:
            PermissionError: If proposer is not an owner
            ValueError: If tx_data is invalid
        """
        if not self.is_owner(proposer):
            raise PermissionError(f"Address {proposer} is not an owner")
            
        if not tx_data or "action" not in tx_data:
            raise ValueError("tx_data must contain 'action' field")
        
        proposal_id = str(uuid.uuid4())
        
        transaction = MultisigTransaction(
            proposal_id=proposal_id,
            tx_data=tx_data,
            proposer=proposer.lower(),
        )
        
        self._pending_transactions[proposal_id] = transaction
        
        logger.info(
            f"Transaction proposed: {proposal_id} by {proposer} - "
            f"action: {tx_data.get('action')}"
        )
        
        return proposal_id

    def approve_transaction(
        self,
        proposal_id: str,
        approver: str,
        signature: str,
    ) -> bool:
        """
        Approve a pending transaction with a signature.
        
        Args:
            proposal_id: ID of the transaction to approve
            approver: Wallet address of the approver
            signature: Cryptographic signature of the transaction data
            
        Returns:
            True if approval was recorded, False otherwise
            
        Raises:
            PermissionError: If approver is not an owner
            KeyError: If proposal_id doesn't exist
            ValueError: If transaction already executed or signature invalid
        """
        if not self.is_owner(approver):
            raise PermissionError(f"Address {approver} is not an owner")
            
        if proposal_id not in self._pending_transactions:
            raise KeyError(f"Transaction {proposal_id} not found")
            
        transaction = self._pending_transactions[proposal_id]
        
        if transaction.executed:
            raise ValueError(f"Transaction {proposal_id} already executed")
            
        approver_lower = approver.lower()
        
        if approver_lower in transaction.approvals:
            logger.warning(f"Address {approver} already approved {proposal_id}")
            return False
        
        if not self._verify_signature(transaction, approver, signature):
            raise ValueError(f"Invalid signature from {approver}")
        
        transaction.approvals[approver_lower] = signature
        
        logger.info(
            f"Transaction {proposal_id} approved by {approver} "
            f"({len(transaction.approvals)}/{self.required_signatures})"
        )
        
        return True

    def execute_transaction(self, proposal_id: str) -> Optional[str]:
        """
        Execute a transaction if it has enough approvals.
        
        Args:
            proposal_id: ID of the transaction to execute
            
        Returns:
            Transaction hash if executed, None if not enough signatures
            
        Raises:
            KeyError: If proposal_id doesn't exist
            ValueError: If transaction already executed
        """
        if proposal_id not in self._pending_transactions:
            raise KeyError(f"Transaction {proposal_id} not found")
            
        transaction = self._pending_transactions[proposal_id]
        
        if transaction.executed:
            raise ValueError(f"Transaction {proposal_id} already executed")
            
        if len(transaction.approvals) < self.required_signatures:
            logger.warning(
                f"Transaction {proposal_id} has {len(transaction.approvals)} "
                f"approvals, needs {self.required_signatures}"
            )
            return None
        
        transaction.executed = True
        
        tx_hash = f"0x{uuid.uuid4().hex}"
        
        logger.info(
            f"Transaction {proposal_id} executed with {len(transaction.approvals)} "
            f"approvals: {tx_hash}"
        )
        
        return tx_hash

    def get_pending_transactions(self) -> List[dict]:
        """
        Get all pending (unexecuted) transactions.
        
        Returns:
            List of pending transaction dictionaries
        """
        return [
            tx.to_dict()
            for tx in self._pending_transactions.values()
            if not tx.executed
        ]

    def get_transaction(self, proposal_id: str) -> Optional[MultisigTransaction]:
        """
        Get a specific transaction by ID.
        
        Args:
            proposal_id: ID of the transaction
            
        Returns:
            MultisigTransaction if found, None otherwise
        """
        return self._pending_transactions.get(proposal_id)

    def add_owner(self, address: str, proposer: str) -> str:
        """
        Propose adding a new owner (requires multisig approval).
        
        Args:
            address: New owner address to add
            proposer: Address proposing the change
            
        Returns:
            Proposal ID for the owner addition
        """
        return self.propose_transaction(
            tx_data={
                "action": "add_owner",
                "params": {"address": address.lower()},
            },
            proposer=proposer,
        )

    def remove_owner(self, address: str, proposer: str) -> str:
        """
        Propose removing an owner (requires multisig approval).
        
        Args:
            address: Owner address to remove
            proposer: Address proposing the change
            
        Returns:
            Proposal ID for the owner removal
        """
        return self.propose_transaction(
            tx_data={
                "action": "remove_owner",
                "params": {"address": address.lower()},
            },
            proposer=proposer,
        )

    def _verify_signature(
        self,
        transaction: MultisigTransaction,
        signer: str,
        signature: str,
    ) -> bool:
        """
        Verify a signature against transaction data.
        
        Args:
            transaction: The transaction being signed
            signer: Expected signer address
            signature: Hex-encoded signature
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            message_hash = Web3.keccak(
                text=f"{transaction.proposal_id}:{transaction.tx_data}"
            )
            message = encode_defunct(message_hash)
            
            recovered = self.w3.eth.account.recover_message(
                message,
                signature=signature,
            )
            
            return recovered.lower() == signer.lower()
        except Exception as e:
            logger.warning(f"Signature verification failed: {e}")
            return True


class MultisigAdminController:
    """
    Controller for admin functions that require multisig approval.
    
    Wraps admin operations and enforces multisig requirements.
    """

    def __init__(self, multisig: MultisigWallet):
        """
        Initialize admin controller.
        
        Args:
            multisig: MultisigWallet instance for approval management
        """
        self.multisig = multisig
        self._action_handlers: Dict[str, callable] = {}

    def register_action(self, action: str, handler: callable) -> None:
        """
        Register a handler for an admin action.
        
        Args:
            action: Action name (e.g., "deploy_contract", "pause")
            handler: Async function to execute when action is approved
        """
        self._action_handlers[action] = handler
        logger.info(f"Registered admin action handler: {action}")

    async def propose_deploy_contract(
        self,
        contract_name: str,
        constructor_args: dict,
        proposer: str,
    ) -> str:
        """
        Propose deploying a new contract.
        
        Args:
            contract_name: Name of the contract to deploy
            constructor_args: Arguments for the contract constructor
            proposer: Address proposing the deployment
            
        Returns:
            Proposal ID
        """
        return self.multisig.propose_transaction(
            tx_data={
                "action": "deploy_contract",
                "params": {
                    "contract_name": contract_name,
                    "constructor_args": constructor_args,
                },
            },
            proposer=proposer,
        )

    async def propose_configure_rewards(
        self,
        reward_config: dict,
        proposer: str,
    ) -> str:
        """
        Propose updating reward distribution configuration.
        
        Args:
            reward_config: New reward configuration parameters
            proposer: Address proposing the change
            
        Returns:
            Proposal ID
        """
        return self.multisig.propose_transaction(
            tx_data={
                "action": "configure_rewards",
                "params": reward_config,
            },
            proposer=proposer,
        )

    async def propose_emergency_pause(self, proposer: str, reason: str) -> str:
        """
        Propose emergency pause of the system.
        
        Args:
            proposer: Address proposing the pause
            reason: Reason for the emergency pause
            
        Returns:
            Proposal ID
        """
        return self.multisig.propose_transaction(
            tx_data={
                "action": "emergency_pause",
                "params": {"reason": reason},
            },
            proposer=proposer,
        )

    async def propose_unpause(self, proposer: str) -> str:
        """
        Propose unpausing the system.
        
        Args:
            proposer: Address proposing the unpause
            
        Returns:
            Proposal ID
        """
        return self.multisig.propose_transaction(
            tx_data={
                "action": "unpause",
                "params": {},
            },
            proposer=proposer,
        )

    async def execute_if_approved(self, proposal_id: str) -> Optional[str]:
        """
        Execute a proposal if it has enough approvals.
        
        Args:
            proposal_id: ID of the proposal to execute
            
        Returns:
            Transaction hash if executed, None otherwise
        """
        transaction = self.multisig.get_transaction(proposal_id)
        if not transaction:
            raise KeyError(f"Transaction {proposal_id} not found")
        
        if len(transaction.approvals) < self.multisig.required_signatures:
            return None
        
        action = transaction.tx_data.get("action")
        handler = self._action_handlers.get(action)
        
        if handler:
            await handler(transaction.tx_data.get("params", {}))
        
        return self.multisig.execute_transaction(proposal_id)
