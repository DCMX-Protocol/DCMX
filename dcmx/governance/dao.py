"""
DAO Governance System

Decentralized governance for DCMX platform decisions.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import json


class ProposalStatus(Enum):
    """Proposal lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PASSED = "passed"
    REJECTED = "rejected"
    EXECUTED = "executed"
    CANCELLED = "cancelled"


class VoteChoice(Enum):
    """Vote options."""
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


@dataclass
class Proposal:
    """DAO governance proposal."""
    id: str
    title: str
    description: str
    proposer: str  # Wallet address
    proposal_type: str  # "feature", "parameter", "treasury", "upgrade"
    created_at: datetime
    voting_start: datetime
    voting_end: datetime
    status: ProposalStatus = ProposalStatus.DRAFT
    
    # Voting requirements
    quorum_percentage: float = 10.0  # % of total supply
    approval_threshold: float = 51.0  # % of votes
    
    # Vote tallies
    votes_for: int = 0
    votes_against: int = 0
    votes_abstain: int = 0
    total_voting_power: int = 0
    
    # Execution
    executable_code: Optional[str] = None  # On-chain execution code
    executed_at: Optional[datetime] = None
    execution_tx_hash: Optional[str] = None
    
    # Metadata
    discussion_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_vote(self, voting_power: int, choice: VoteChoice):
        """Add a vote to the proposal."""
        if choice == VoteChoice.FOR:
            self.votes_for += voting_power
        elif choice == VoteChoice.AGAINST:
            self.votes_against += voting_power
        elif choice == VoteChoice.ABSTAIN:
            self.votes_abstain += voting_power
        
        self.total_voting_power += voting_power
    
    def calculate_results(self, total_token_supply: int) -> Dict[str, Any]:
        """Calculate voting results."""
        total_votes = self.votes_for + self.votes_against + self.votes_abstain
        
        # Calculate percentages
        quorum_met = (total_votes / total_token_supply * 100) >= self.quorum_percentage
        
        if self.votes_for + self.votes_against > 0:
            approval_rate = (self.votes_for / (self.votes_for + self.votes_against)) * 100
        else:
            approval_rate = 0.0
        
        threshold_met = approval_rate >= self.approval_threshold
        
        passed = quorum_met and threshold_met
        
        return {
            "quorum_met": quorum_met,
            "quorum_percentage": (total_votes / total_token_supply * 100),
            "approval_rate": approval_rate,
            "threshold_met": threshold_met,
            "passed": passed,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "votes_abstain": self.votes_abstain,
            "total_votes": total_votes,
        }
    
    def can_execute(self, total_token_supply: int) -> bool:
        """Check if proposal can be executed."""
        if self.status != ProposalStatus.PASSED:
            return False
        
        if datetime.now() < self.voting_end:
            return False
        
        results = self.calculate_results(total_token_supply)
        return results['passed']


@dataclass
class Vote:
    """Individual vote record."""
    proposal_id: str
    voter: str  # Wallet address
    choice: VoteChoice
    voting_power: int
    timestamp: datetime
    reason: Optional[str] = None  # Optional comment


class DAOGovernance:
    """
    DAO Governance System.
    
    Manages proposals, voting, and execution.
    """
    
    def __init__(
        self,
        token_contract_address: str,
        total_token_supply: int,
        min_proposal_tokens: int = 1000,  # Min tokens to create proposal
    ):
        self.token_contract_address = token_contract_address
        self.total_token_supply = total_token_supply
        self.min_proposal_tokens = min_proposal_tokens
        
        self.proposals: Dict[str, Proposal] = {}
        self.votes: Dict[str, List[Vote]] = {}  # proposal_id -> votes
        self.voter_addresses: Dict[str, Dict[str, bool]] = {}  # proposal_id -> {voter -> voted}
    
    async def create_proposal(
        self,
        title: str,
        description: str,
        proposer: str,
        proposal_type: str,
        voting_duration_hours: int = 72,
        quorum_percentage: float = 10.0,
        approval_threshold: float = 51.0,
        executable_code: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Proposal:
        """
        Create a new governance proposal.
        
        Args:
            title: Proposal title
            description: Detailed description
            proposer: Wallet address of proposer
            proposal_type: Type of proposal
            voting_duration_hours: How long voting is open
            quorum_percentage: Min % of supply that must vote
            approval_threshold: Min % approval to pass
            executable_code: Optional on-chain execution code
            metadata: Additional metadata
            
        Returns:
            Created Proposal
        """
        # Check proposer has minimum tokens
        proposer_balance = await self._get_token_balance(proposer)
        if proposer_balance < self.min_proposal_tokens:
            raise ValueError(
                f"Proposer must have at least {self.min_proposal_tokens} tokens. "
                f"Current balance: {proposer_balance}"
            )
        
        # Generate proposal ID
        proposal_id = f"DCMX-{len(self.proposals) + 1:04d}"
        
        # Create proposal
        now = datetime.now()
        proposal = Proposal(
            id=proposal_id,
            title=title,
            description=description,
            proposer=proposer,
            proposal_type=proposal_type,
            created_at=now,
            voting_start=now + timedelta(hours=24),  # 24h delay before voting
            voting_end=now + timedelta(hours=24 + voting_duration_hours),
            quorum_percentage=quorum_percentage,
            approval_threshold=approval_threshold,
            executable_code=executable_code,
            metadata=metadata or {},
        )
        
        self.proposals[proposal_id] = proposal
        self.votes[proposal_id] = []
        self.voter_addresses[proposal_id] = {}
        
        return proposal
    
    async def cast_vote(
        self,
        proposal_id: str,
        voter: str,
        choice: VoteChoice,
        reason: Optional[str] = None,
    ) -> Vote:
        """
        Cast a vote on a proposal.
        
        Args:
            proposal_id: ID of proposal
            voter: Wallet address
            choice: Vote choice (FOR, AGAINST, ABSTAIN)
            reason: Optional explanation
            
        Returns:
            Vote record
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        # Check voting is open
        now = datetime.now()
        if now < proposal.voting_start:
            raise ValueError("Voting has not started yet")
        if now > proposal.voting_end:
            raise ValueError("Voting has ended")
        
        # Check haven't voted already
        if self.voter_addresses[proposal_id].get(voter):
            raise ValueError("Already voted on this proposal")
        
        # Get voting power (token balance)
        voting_power = await self._get_token_balance(voter)
        if voting_power == 0:
            raise ValueError("No voting power (no tokens)")
        
        # Record vote
        vote = Vote(
            proposal_id=proposal_id,
            voter=voter,
            choice=choice,
            voting_power=voting_power,
            timestamp=now,
            reason=reason,
        )
        
        self.votes[proposal_id].append(vote)
        self.voter_addresses[proposal_id][voter] = True
        
        # Update proposal tallies
        proposal.add_vote(voting_power, choice)
        
        return vote
    
    async def finalize_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """
        Finalize a proposal after voting ends.
        
        Calculates results and updates status.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        # Check voting has ended
        if datetime.now() < proposal.voting_end:
            raise ValueError("Voting has not ended yet")
        
        # Calculate results
        results = proposal.calculate_results(self.total_token_supply)
        
        # Update status
        if results['passed']:
            proposal.status = ProposalStatus.PASSED
        else:
            proposal.status = ProposalStatus.REJECTED
        
        return {
            "proposal_id": proposal_id,
            "status": proposal.status.value,
            "results": results,
        }
    
    async def execute_proposal(self, proposal_id: str) -> Dict[str, Any]:
        """
        Execute a passed proposal.
        
        For proposals with executable_code, this would trigger on-chain execution.
        """
        proposal = self.proposals.get(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        
        # Check can execute
        if not proposal.can_execute(self.total_token_supply):
            raise ValueError("Proposal cannot be executed")
        
        # Execute (simplified - real implementation would interact with blockchain)
        if proposal.executable_code:
            # This would call smart contract function
            execution_result = await self._execute_on_chain(proposal.executable_code)
            proposal.execution_tx_hash = execution_result.get('tx_hash')
        
        proposal.status = ProposalStatus.EXECUTED
        proposal.executed_at = datetime.now()
        
        return {
            "proposal_id": proposal_id,
            "status": "executed",
            "tx_hash": proposal.execution_tx_hash,
        }
    
    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get proposal by ID."""
        return self.proposals.get(proposal_id)
    
    def list_proposals(
        self,
        status: Optional[ProposalStatus] = None,
        proposal_type: Optional[str] = None,
    ) -> List[Proposal]:
        """List all proposals with optional filters."""
        proposals = list(self.proposals.values())
        
        if status:
            proposals = [p for p in proposals if p.status == status]
        
        if proposal_type:
            proposals = [p for p in proposals if p.proposal_type == proposal_type]
        
        return sorted(proposals, key=lambda p: p.created_at, reverse=True)
    
    def get_proposal_votes(self, proposal_id: str) -> List[Vote]:
        """Get all votes for a proposal."""
        return self.votes.get(proposal_id, [])
    
    async def _get_token_balance(self, wallet_address: str) -> int:
        """Get token balance for wallet."""
        # Real implementation would query blockchain
        # For now, return mock value
        return 1000
    
    async def _execute_on_chain(self, executable_code: str) -> Dict[str, Any]:
        """Execute code on blockchain."""
        # Real implementation would interact with smart contract
        return {
            "success": True,
            "tx_hash": "0x1234567890abcdef",
        }


class ProposalTemplates:
    """Pre-built proposal templates for common governance actions."""
    
    @staticmethod
    def feature_request(
        title: str,
        description: str,
        implementation_details: str,
    ) -> Dict[str, Any]:
        """Template for new feature proposals."""
        return {
            "title": f"[Feature Request] {title}",
            "description": f"""
## Description
{description}

## Implementation Details
{implementation_details}

## Benefits
- Improve user experience
- Enhance platform capabilities

## Risks
- Development time required
- Potential technical complexity

## Timeline
- Phase 1: Design & Planning (2 weeks)
- Phase 2: Development (4-6 weeks)
- Phase 3: Testing (1-2 weeks)
- Phase 4: Deployment
            """.strip(),
            "proposal_type": "feature",
            "voting_duration_hours": 72,
            "quorum_percentage": 10.0,
            "approval_threshold": 51.0,
        }
    
    @staticmethod
    def parameter_change(
        parameter_name: str,
        current_value: Any,
        proposed_value: Any,
        rationale: str,
    ) -> Dict[str, Any]:
        """Template for changing platform parameters."""
        return {
            "title": f"[Parameter Change] Update {parameter_name}",
            "description": f"""
## Parameter
**{parameter_name}**

## Current Value
`{current_value}`

## Proposed Value
`{proposed_value}`

## Rationale
{rationale}

## Impact Analysis
- Technical impact: [Analysis required]
- User impact: [Analysis required]
- Economic impact: [Analysis required]
            """.strip(),
            "proposal_type": "parameter",
            "voting_duration_hours": 48,
            "quorum_percentage": 5.0,
            "approval_threshold": 60.0,
        }
    
    @staticmethod
    def treasury_allocation(
        amount: float,
        recipient: str,
        purpose: str,
    ) -> Dict[str, Any]:
        """Template for treasury spending."""
        return {
            "title": f"[Treasury] Allocate {amount} DCMX for {purpose}",
            "description": f"""
## Amount
{amount} DCMX tokens

## Recipient
{recipient}

## Purpose
{purpose}

## Budget Breakdown
- [Item 1]: [Amount]
- [Item 2]: [Amount]
- Total: {amount} DCMX

## Expected Outcomes
- [Outcome 1]
- [Outcome 2]

## Accountability
- Milestone-based releases
- Monthly progress reports
            """.strip(),
            "proposal_type": "treasury",
            "voting_duration_hours": 120,  # 5 days for treasury
            "quorum_percentage": 15.0,
            "approval_threshold": 66.0,  # Higher threshold for spending
        }
