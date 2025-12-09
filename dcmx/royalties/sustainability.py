"""
Economic Sustainability Module for DCMX.

Implements mechanisms to prevent:
- Hyperinflation of native token
- Unsustainable reward structures
- Platform collapse from ponzi-like dynamics
- Market manipulation

Ensures long-term viability through:
- Token supply caps
- Dynamic fee mechanisms
- Burn mechanisms
- Treasury management
- Sustainable reward curves
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class TokenomicsModel(Enum):
    """Types of token economic models."""
    FIXED_SUPPLY = "fixed_supply"  # No new tokens ever
    DIMINISHING_EMISSION = "diminishing_emission"  # Halvings like Bitcoin
    CONTROLLED_EXPANSION = "controlled_expansion"  # Capped annual percentage
    DEFLATIONARY = "deflationary"  # Burn mechanism reduces supply


@dataclass
class TokenSupplyConfig:
    """
    Configuration for token supply and emission.
    
    Defines how many tokens exist and how new ones are created.
    """
    model: TokenomicsModel
    
    # Supply constraints
    max_total_supply: int  # Hard cap
    current_circulating: int = 0
    tokens_reserved_for_rewards: int = 0
    
    # Emission parameters
    annual_emission_cap: Optional[float] = None  # Percentage of current supply
    halving_interval_blocks: Optional[int] = None  # For diminishing model
    blocks_since_genesis: int = 0
    
    def get_current_emission_rate(self) -> float:
        """Calculate current emission rate."""
        if self.model == TokenomicsModel.FIXED_SUPPLY:
            return 0.0
        
        elif self.model == TokenomicsModel.DIMINISHING_EMISSION:
            if self.halving_interval_blocks is None:
                return 0.0
            
            halvings = self.blocks_since_genesis // self.halving_interval_blocks
            base_rate = 50.0  # Start with 50 tokens per block
            return base_rate / (2 ** halvings)
        
        elif self.model == TokenomicsModel.CONTROLLED_EXPANSION:
            if self.annual_emission_cap is None:
                return 0.0
            
            # Annual emission cap as percentage of supply
            return (self.current_circulating * self.annual_emission_cap) / (365 * 24 * 60 * 60)
        
        else:  # DEFLATIONARY
            return 0.0
    
    def validate_emission_budget(self, requested_tokens: int) -> bool:
        """Check if emission request is within budget."""
        if self.model == TokenomicsModel.FIXED_SUPPLY:
            return self.current_circulating + requested_tokens <= self.max_total_supply
        
        if self.current_circulating + requested_tokens > self.max_total_supply:
            logger.warning(f"Emission request {requested_tokens} exceeds max supply")
            return False
        
        if self.tokens_reserved_for_rewards < requested_tokens:
            logger.warning(f"Insufficient tokens reserved for rewards")
            return False
        
        return True


@dataclass
class DynamicFeeStructure:
    """
    Dynamic platform fees that adjust based on network activity.
    
    Lower fees when network is slow → encourage usage
    Higher fees when network is congested → fund sustainability
    """
    base_platform_fee: float = 2.0  # 2% base
    
    # Fee adjustments
    min_fee: float = 0.5  # Floor
    max_fee: float = 5.0  # Ceiling
    
    # Congestion pricing
    congestion_threshold: int = 10000  # Transactions per hour
    fee_increase_per_1k_transactions: float = 0.25  # +0.25% per 1k tx over threshold
    
    # Recent transaction volume
    transactions_this_hour: int = 0
    transactions_24h: List[int] = field(default_factory=lambda: [0] * 24)
    
    # Fee allocation
    artist_share_of_fees: float = 20.0  # 20% of fees → artists
    treasury_share: float = 50.0  # 50% → platform treasury
    burn_share: float = 30.0  # 30% → token burn
    
    def update_transaction_count(self, count: int) -> None:
        """Update transaction count for congestion pricing."""
        self.transactions_this_hour = count
        logger.info(f"Updated transaction count: {count}")
    
    def calculate_current_fee(self) -> float:
        """Calculate current platform fee percentage."""
        base = self.base_platform_fee
        
        # Add congestion surcharge
        if self.transactions_this_hour > self.congestion_threshold:
            excess = self.transactions_this_hour - self.congestion_threshold
            surcharge = (excess // 1000) * self.fee_increase_per_1k_transactions
            base += surcharge
        
        # Clamp to min/max
        return max(self.min_fee, min(base, self.max_fee))
    
    def allocate_fees(self, total_fee_amount: float) -> Dict[str, float]:
        """Allocate collected fees."""
        return {
            "artist_fund": total_fee_amount * (self.artist_share_of_fees / 100.0),
            "treasury": total_fee_amount * (self.treasury_share / 100.0),
            "burn": total_fee_amount * (self.burn_share / 100.0),
        }


@dataclass
class BurnMechanism:
    """
    Token burn mechanism to create deflation.
    
    Reduces token supply over time, supporting price stability.
    """
    annual_burn_rate: float = 2.0  # Percentage per year
    total_burned: int = 0
    burn_history: List[Tuple[str, int]] = field(default_factory=list)  # (date, amount)
    
    # Burn triggers
    burn_on_transaction_fees: bool = True
    burn_on_platform_revenue: bool = True
    burn_on_governance_vote: bool = False
    
    def calculate_annual_burn(self, current_supply: int) -> int:
        """Calculate tokens to burn this year."""
        return int(current_supply * (self.annual_burn_rate / 100.0))
    
    def burn_tokens(self, amount: int, reason: str) -> None:
        """Permanently remove tokens from circulation."""
        self.total_burned += amount
        self.burn_history.append((datetime.utcnow().isoformat(), amount))
        
        logger.info(f"Burned {amount} tokens ({reason}). Total burned: {self.total_burned}")
    
    def get_burn_impact(self, original_supply: int, current_supply: int) -> float:
        """Calculate deflation impact (%)."""
        return (1.0 - (current_supply / original_supply)) * 100.0


@dataclass
class PlatformTreasury:
    """
    Platform treasury for long-term sustainability.
    
    Accumulates revenue and deploys it strategically.
    """
    treasury_wallet: str
    current_balance_dcmx: float = 0.0
    current_balance_usd: float = 0.0
    
    # Allocation targets
    development_fund: float = 0.0  # Engineer salaries, R&D
    marketing_fund: float = 0.0  # Growth initiatives
    emergency_reserve: float = 0.0  # Stability fund
    
    # Target allocation percentages
    target_dev: float = 40.0  # 40% to development
    target_marketing: float = 35.0  # 35% to marketing
    target_emergency: float = 25.0  # 25% emergency reserve
    
    # Fund allocation history
    allocation_history: List[Dict] = field(default_factory=list)
    
    # Spending
    total_spent: float = 0.0
    spending_log: List[Dict] = field(default_factory=list)
    
    def deposit(self, amount: float, source: str) -> None:
        """Add funds to treasury."""
        self.current_balance_dcmx += amount
        logger.info(f"Treasury received {amount:.2f} DCMX from {source}")
    
    def allocate_funds(self) -> Dict[str, float]:
        """
        Allocate treasury funds to strategic initiatives.
        
        Returns: Dict of allocation → amount
        """
        total = self.current_balance_dcmx
        
        dev_amount = total * (self.target_dev / 100.0)
        marketing_amount = total * (self.target_marketing / 100.0)
        emergency_amount = total * (self.target_emergency / 100.0)
        
        self.development_fund += dev_amount
        self.marketing_fund += marketing_amount
        self.emergency_reserve += emergency_amount
        
        allocation = {
            "development": dev_amount,
            "marketing": marketing_amount,
            "emergency_reserve": emergency_amount,
        }
        
        self.allocation_history.append({
            "date": datetime.utcnow().isoformat(),
            "allocation": allocation
        })
        
        self.current_balance_dcmx = 0.0  # Reset after allocation
        
        logger.info(f"Treasury allocated: Dev={dev_amount:.2f}, Marketing={marketing_amount:.2f}, Reserve={emergency_amount:.2f}")
        
        return allocation
    
    def spend(self, fund: str, amount: float, description: str) -> None:
        """Spend from a fund."""
        if fund == "development":
            self.development_fund -= amount
        elif fund == "marketing":
            self.marketing_fund -= amount
        elif fund == "emergency_reserve":
            self.emergency_reserve -= amount
        else:
            raise ValueError(f"Unknown fund: {fund}")
        
        self.total_spent += amount
        
        self.spending_log.append({
            "date": datetime.utcnow().isoformat(),
            "fund": fund,
            "amount": amount,
            "description": description
        })
        
        logger.info(f"Spent {amount:.2f} from {fund}: {description}")
    
    def get_status(self) -> Dict:
        """Get treasury status."""
        return {
            "pending_allocation": self.current_balance_dcmx,
            "development_fund": self.development_fund,
            "marketing_fund": self.marketing_fund,
            "emergency_reserve": self.emergency_reserve,
            "total_allocated": self.development_fund + self.marketing_fund + self.emergency_reserve,
            "total_spent": self.total_spent,
            "runway_months": (self.emergency_reserve / (self.total_spent / 12)) if self.total_spent > 0 else None,
        }


@dataclass
class SustainabilityMetrics:
    """
    Key metrics for platform sustainability monitoring.
    
    Tracks health indicators and warns of unsustainable dynamics.
    """
    # Token metrics
    token_inflation_rate: float = 0.0  # Annual %
    token_burn_rate: float = 0.0  # Annual %
    net_emission_rate: float = 0.0  # Inflation - Burn
    
    # Activity metrics
    dau: int = 0  # Daily active users
    dau_growth_7d: float = 0.0  # 7-day growth %
    transaction_volume_24h: float = 0.0
    
    # Financial metrics
    average_transaction_value: float = 0.0
    artist_revenue_24h: float = 0.0
    platform_revenue_24h: float = 0.0
    
    # Health indicators
    token_price_stability: float = 0.0  # 0-100, 100 = stable
    reward_sustainability: float = 0.0  # 0-100, 100 = sustainable
    treasury_runway_months: float = 0.0
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    
    def calculate_sustainability_score(self) -> float:
        """Calculate overall platform sustainability (0-100)."""
        score = 100.0
        
        # Token health: Net emission should be negative (deflation) or very low
        if self.net_emission_rate > 5.0:
            score -= 20.0
            self.warnings.append(f"Net emission {self.net_emission_rate}% too high")
        
        # Activity health: Should have positive DAU growth
        if self.dau_growth_7d < 0:
            score -= 15.0
            self.warnings.append(f"DAU declining at {self.dau_growth_7d}%")
        
        # Financial health: Revenue should exceed emissions
        if self.platform_revenue_24h < self.transaction_volume_24h * 0.02:
            score -= 10.0
            self.warnings.append("Platform revenue too low relative to volume")
        
        # Treasury health: Should have 6+ months runway
        if self.treasury_runway_months < 6:
            score -= 25.0
            self.warnings.append(f"Low treasury runway: {self.treasury_runway_months:.1f} months")
        
        # Price stability: Should be stable
        if self.token_price_stability < 70:
            score -= 10.0
            self.warnings.append(f"Token price unstable: {self.token_price_stability}%")
        
        return max(0.0, score)
    
    def to_report(self) -> Dict:
        """Generate full sustainability report."""
        score = self.calculate_sustainability_score()
        
        return {
            "sustainability_score": score,
            "status": "healthy" if score >= 70 else "warning" if score >= 40 else "critical",
            "token_metrics": {
                "inflation_rate": self.token_inflation_rate,
                "burn_rate": self.token_burn_rate,
                "net_emission": self.net_emission_rate,
            },
            "activity": {
                "daily_active_users": self.dau,
                "dau_growth_7d": self.dau_growth_7d,
                "transaction_volume_24h": self.transaction_volume_24h,
            },
            "financial": {
                "average_tx_value": self.average_transaction_value,
                "artist_revenue_24h": self.artist_revenue_24h,
                "platform_revenue_24h": self.platform_revenue_24h,
            },
            "health": {
                "price_stability": self.token_price_stability,
                "reward_sustainability": self.reward_sustainability,
                "treasury_runway": self.treasury_runway_months,
            },
            "warnings": self.warnings,
        }


class SustainabilityEngine:
    """
    Main engine for managing platform sustainability.
    
    Coordinates token supply, fees, burns, and treasury.
    """
    
    def __init__(self):
        """Initialize sustainability engine."""
        # Token supply
        self.supply_config = TokenSupplyConfig(
            model=TokenomicsModel.CONTROLLED_EXPANSION,
            max_total_supply=1_000_000_000,  # 1 billion max
            current_circulating=100_000_000,  # 100 million initial
            tokens_reserved_for_rewards=500_000_000,  # 500 million reserved
            annual_emission_cap=5.0,  # 5% per year max
        )
        
        # Fee structure
        self.fee_structure = DynamicFeeStructure()
        
        # Burn mechanism
        self.burn = BurnMechanism()
        
        # Treasury
        self.treasury = PlatformTreasury(
            treasury_wallet="0xDCMXTreasury"
        )
        
        # Metrics
        self.metrics = SustainabilityMetrics()
        
        logger.info("SustainabilityEngine initialized")
    
    def process_transaction(self, amount: float, tx_id: str) -> Dict:
        """
        Process a transaction and collect fees.
        
        Returns: Fee allocation dict
        """
        fee_rate = self.fee_structure.calculate_current_fee()
        fee_amount = amount * (fee_rate / 100.0)
        
        # Allocate fees
        allocation = self.fee_structure.allocate_fees(fee_amount)
        
        # Burn tokens
        burn_amount = int(allocation["burn"])
        self.burn.burn_tokens(burn_amount, f"Transaction fee burn (tx:{tx_id})")
        
        # Add to treasury
        treasury_amount = allocation["treasury"]
        self.treasury.deposit(treasury_amount, f"Transaction fee (tx:{tx_id})")
        
        # Add to artist fund (immediate distribution)
        artist_fund = allocation["artist_fund"]
        
        logger.info(f"Transaction {tx_id}: Fee {fee_amount:.4f} DCMX collected (Rate: {fee_rate}%)")
        
        return allocation
    
    def check_sustainability(self) -> Tuple[float, bool]:
        """
        Check if platform is sustainable.
        
        Returns: (score, is_sustainable)
        """
        score = self.metrics.calculate_sustainability_score()
        is_sustainable = score >= 50
        
        if not is_sustainable:
            logger.warning(f"Sustainability score {score:.1f} - immediate action needed")
        
        return score, is_sustainable
    
    def get_status_report(self) -> Dict:
        """Get comprehensive sustainability status."""
        return {
            "token_supply": {
                "model": self.supply_config.model.value,
                "max_supply": self.supply_config.max_total_supply,
                "current_supply": self.supply_config.current_circulating,
                "emission_rate": self.supply_config.get_current_emission_rate(),
            },
            "fees": {
                "current_rate": self.fee_structure.calculate_current_fee(),
                "min": self.fee_structure.min_fee,
                "max": self.fee_structure.max_fee,
            },
            "burn": {
                "total_burned": self.burn.total_burned,
                "annual_burn_rate": self.burn.annual_burn_rate,
            },
            "treasury": self.treasury.get_status(),
            "sustainability": self.metrics.to_report(),
        }


if __name__ == "__main__":
    engine = SustainabilityEngine()
    
    # Simulate transactions
    print("\n=== SIMULATING PLATFORM ACTIVITY ===")
    
    for i in range(5):
        allocation = engine.process_transaction(100.0, f"tx_{i}")
        print(f"\nTransaction {i}:")
        print(f"  Artist Fund: {allocation['artist_fund']:.4f} DCMX")
        print(f"  Treasury: {allocation['treasury']:.4f} DCMX")
        print(f"  Burn: {allocation['burn']:.4f} DCMX")
    
    # Allocate treasury
    print("\n=== TREASURY ALLOCATION ===")
    allocated = engine.treasury.allocate_funds()
    for fund, amount in allocated.items():
        print(f"  {fund}: {amount:.4f} DCMX")
    
    # Check sustainability
    print("\n=== SUSTAINABILITY CHECK ===")
    score, is_sustainable = engine.check_sustainability()
    print(f"Sustainability Score: {score:.1f}")
    print(f"Status: {'✓ SUSTAINABLE' if is_sustainable else '✗ AT RISK'}")
    
    # Full report
    print("\n=== FULL STATUS REPORT ===")
    report = engine.get_status_report()
    print(f"Token Model: {report['token_supply']['model']}")
    print(f"Current Supply: {report['token_supply']['current_supply']:,}")
    print(f"Emission Rate: {report['token_supply']['emission_rate']:.4f}/sec")
    print(f"Current Fee Rate: {report['fees']['current_rate']:.2f}%")
    print(f"Total Burned: {report['burn']['total_burned']}")
