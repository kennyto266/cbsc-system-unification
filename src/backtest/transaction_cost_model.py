"""
Advanced Transaction Cost Modeling
==================================

Comprehensive transaction cost modeling with realistic market impact,
bid-ask spreads, financing costs, and tax considerations.

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from scipy.optimize import minimize
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class CommissionModel(str, Enum):
    """Commission model types"""
    PERCENTAGE = "percentage"
    FIXED = "fixed"
    TIERED = "tiered"
    PER_SHARE = "per_share"
    SCHEDULED = "scheduled"


class SlippageModel(str, Enum):
    """Slippage model types"""
    LINEAR = "linear"
    SQUARE_ROOT = "square_root"
    PERCENTAGE = "percentage"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    NONLINEAR = "nonlinear"
    ALMGREN_CHRISS = "almgren_chriss"


class MarketImpactModel(str, Enum):
    """Market impact model types"""
    SQUARE_ROOT = "square_root"
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    ALMGREN_CHRISS = "almgren_chriss"
    OBIZHAEVA_WANG = "obizhaeva_wang"


@dataclass
class Trade:
    """Trade information"""
    timestamp: pd.Timestamp
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    volume: float  # Daily volume
    bid_ask_spread: float
    volatility: float
    mid_price: float


@dataclass
class CostComponents:
    """Individual cost components"""
    commission: float
    slippage: float
    market_impact: float
    financing: float
    taxes: float
    exchange_fees: float
    clearing_fees: float
    total: float


class BaseCostModel(ABC):
    """Base class for cost models"""

    @abstractmethod
    def calculate_cost(self, trade: Trade) -> CostComponents:
        """Calculate cost for a trade"""
        pass


class CommissionCalculator:
    """Commission calculation with various models"""

    def __init__(self, model: CommissionModel, **kwargs):
        self.model = model
        self.config = kwargs

    def calculate(self, trade: Trade) -> float:
        """Calculate commission for a trade"""

        if self.model == CommissionModel.PERCENTAGE:
            return self._percentage_commission(trade)
        elif self.model == CommissionModel.FIXED:
            return self._fixed_commission(trade)
        elif self.model == CommissionModel.TIERED:
            return self._tiered_commission(trade)
        elif self.model == CommissionModel.PER_SHARE:
            return self._per_share_commission(trade)
        elif self.model == CommissionModel.SCHEDULED:
            return self._scheduled_commission(trade)
        else:
            raise ValueError(f"Unknown commission model: {self.model}")

    def _percentage_commission(self, trade: Trade) -> float:
        """Percentage-based commission"""
        rate = self.config.get('rate', 0.001)  # 0.1% default
        commission = abs(trade.quantity * trade.price * rate)

        # Apply min/max
        min_commission = self.config.get('min_commission', 0)
        max_commission = self.config.get('max_commission', float('inf'))

        return max(min_commission, min(commission, max_commission))

    def _fixed_commission(self, trade: Trade) -> float:
        """Fixed commission per trade"""
        return self.config.get('fixed_amount', 1.0)

    def _tiered_commission(self, trade: Trade) -> float:
        """Tiered commission based on trade size"""
        trade_value = abs(trade.quantity * trade.price)
        tiers = self.config.get('tiers', [
            (0, 0.002),      # < 10k: 0.2%
            (10000, 0.0015),  # 10k-100k: 0.15%
            (100000, 0.001),  # 100k-1M: 0.1%
            (1000000, 0.0005) # > 1M: 0.05%
        ])

        for threshold, rate in reversed(tiers):
            if trade_value >= threshold:
                return trade_value * rate

        return trade_value * tiers[0][1]

    def _per_share_commission(self, trade: Trade) -> float:
        """Per-share commission"""
        per_share_rate = self.config.get('per_share_rate', 0.005)  # $0.005 per share
        min_commission = self.config.get('min_commission', 1.0)

        commission = abs(trade.quantity) * per_share_rate
        return max(commission, min_commission)

    def _scheduled_commission(self, trade: Trade) -> float:
        """Scheduled commission based on time/liquidity"""
        base_rate = self.config.get('base_rate', 0.001)

        # Time-based adjustment
        hour = trade.timestamp.hour
        if 9 <= hour <= 10:  # Open
            time_multiplier = 1.5
        elif 15 <= hour <= 16:  # Close
            time_multiplier = 1.3
        else:
            time_multiplier = 1.0

        # Volume-based adjustment
        volume_ratio = abs(trade.quantity) / trade.volume
        if volume_ratio > 0.01:  # > 1% of daily volume
            volume_multiplier = 1.2
        else:
            volume_multiplier = 1.0

        commission = abs(trade.quantity * trade.price * base_rate * time_multiplier * volume_multiplier)
        return commission


class SlippageCalculator:
    """Slippage calculation with various models"""

    def __init__(self, model: SlippageModel, **kwargs):
        self.model = model
        self.config = kwargs

    def calculate(self, trade: Trade) -> float:
        """Calculate slippage for a trade"""

        if self.model == SlippageModel.LINEAR:
            return self._linear_slippage(trade)
        elif self.model == SlippageModel.SQUARE_ROOT:
            return self._square_root_slippage(trade)
        elif self.model == SlippageModel.PERCENTAGE:
            return self._percentage_slippage(trade)
        elif self.model == SlippageModel.VOLATILITY_ADJUSTED:
            return self._volatility_adjusted_slippage(trade)
        elif self.model == SlippageModel.ALMGREN_CHRISS:
            return self._almgren_chriss_slippage(trade)
        else:
            raise ValueError(f"Unknown slippage model: {self.model}")

    def _linear_slippage(self, trade: Trade) -> float:
        """Linear slippage model"""
        rate = self.config.get('rate', 0.0005)  # 5 bps default
        impact_factor = self.config.get('impact_factor', 0.1)

        # Size impact
        volume_ratio = abs(trade.quantity) / trade.volume
        size_impact = impact_factor * volume_ratio

        total_slippage = rate + size_impact
        slippage_cost = abs(trade.quantity * trade.price * total_slippage)

        return slippage_cost

    def _square_root_slippage(self, trade: Trade) -> float:
        """Square root slippage model"""
        base_rate = self.config.get('base_rate', 0.0005)
        impact_factor = self.config.get('impact_factor', 0.01)

        # Size impact with square root
        volume_ratio = abs(trade.quantity) / trade.volume
        size_impact = impact_factor * np.sqrt(volume_ratio)

        total_slippage = base_rate + size_impact
        slippage_cost = abs(trade.quantity * trade.price * total_slippage)

        return slippage_cost

    def _percentage_slippage(self, trade: Trade) -> float:
        """Percentage-based slippage"""
        rate = self.config.get('rate', 0.001)  # 10 bps default

        # Bid-ask spread component
        spread_cost = abs(trade.quantity * trade.bid_ask_spread / 2)

        # Percentage slippage
        percentage_cost = abs(trade.quantity * trade.price * rate)

        return spread_cost + percentage_cost

    def _volatility_adjusted_slippage(self, trade: Trade) -> float:
        """Volatility-adjusted slippage"""
        base_rate = self.config.get('base_rate', 0.0005)
        volatility_factor = self.config.get('volatility_factor', 0.5)

        # Adjust for volatility
        volatility_adjustment = volatility_factor * trade.volatility

        total_slippage = base_rate * (1 + volatility_adjustment)
        slippage_cost = abs(trade.quantity * trade.price * total_slippage)

        return slippage_cost

    def _almgren_chriss_slippage(self, trade: Trade) -> float:
        """Almgren-Chriss slippage model"""
        # Almgren-Chriss parameters
        eta = self.config.get('eta', 0.0001)  # Temporary impact coefficient
        gamma = self.config.get('gamma', 0.0001)  # Permanent impact coefficient
        lambda_param = self.config.get('lambda', 0.01)  # Risk aversion
        sigma = trade.volatility

        # Trade size as fraction of daily volume
        epsilon = abs(trade.quantity) / trade.volume

        # Temporary impact
        temporary_impact = eta * epsilon

        # Permanent impact
        permanent_impact = gamma * epsilon

        # Total slippage
        total_impact = temporary_impact + permanent_impact
        slippage_cost = abs(trade.quantity * trade.price * total_impact)

        return slippage_cost


class MarketImpactCalculator:
    """Market impact calculation"""

    def __init__(self, model: MarketImpactModel, **kwargs):
        self.model = model
        self.config = kwargs

    def calculate(self, trade: Trade) -> float:
        """Calculate market impact for a trade"""

        if self.model == MarketImpactModel.SQUARE_ROOT:
            return self._square_root_impact(trade)
        elif self.model == MarketImpactModel.LINEAR:
            return self._linear_impact(trade)
        elif self.model == MarketImpactModel.LOGARITHMIC:
            return self._logarithmic_impact(trade)
        elif self.model == MarketImpactModel.ALMGREN_CHRISS:
            return self._almgren_chriss_impact(trade)
        elif self.model == MarketImpactModel.OBIZHAEVA_WANG:
            return self._obizhaeva_wang_impact(trade)
        else:
            raise ValueError(f"Unknown market impact model: {self.model}")

    def _square_root_impact(self, trade: Trade) -> float:
        """Square root market impact model"""
        alpha = self.config.get('alpha', 0.001)  # Impact coefficient
        beta = self.config.get('beta', 0.5)  # Impact exponent

        # Trade size as fraction of daily volume
        volume_ratio = abs(trade.quantity) / trade.volume

        # Market impact
        impact = alpha * np.power(volume_ratio, beta)
        impact_cost = abs(trade.quantity * trade.price * impact)

        return impact_cost

    def _linear_impact(self, trade: Trade) -> float:
        """Linear market impact model"""
        alpha = self.config.get('alpha', 0.001)

        volume_ratio = abs(trade.quantity) / trade.volume
        impact = alpha * volume_ratio
        impact_cost = abs(trade.quantity * trade.price * impact)

        return impact_cost

    def _logarithmic_impact(self, trade: Trade) -> float:
        """Logarithmic market impact model"""
        alpha = self.config.get('alpha', 0.001)

        volume_ratio = abs(trade.quantity) / trade.volume
        impact = alpha * np.log(1 + volume_ratio)
        impact_cost = abs(trade.quantity * trade.price * impact)

        return impact_cost

    def _almgren_chriss_impact(self, trade: Trade) -> float:
        """Almgren-Chriss market impact model"""
        gamma = self.config.get('gamma', 0.0001)  # Permanent impact coefficient

        volume_ratio = abs(trade.quantity) / trade.volume
        impact = gamma * volume_ratio
        impact_cost = abs(trade.quantity * trade.price * impact)

        return impact_cost

    def _obizhaeva_wang_impact(self, trade: Trade) -> float:
        """Obizhaeva-Wang market impact model"""
        # This is a simplified version
        eta = self.config.get('eta', 0.001)
        kappa = self.config.get('kappa', 0.1)  # Decay rate

        volume_ratio = abs(trade.quantity) / trade.volume
        impact = eta * volume_ratio * (1 - np.exp(-kappa))
        impact_cost = abs(trade.quantity * trade.price * impact)

        return impact_cost


class FinancingCostCalculator:
    """Financing cost calculation"""

    def __init__(self, **kwargs):
        self.config = kwargs

    def calculate(
        self,
        positions: pd.DataFrame,
        prices: pd.DataFrame,
        holding_period: float = 1.0
    ) -> pd.Series:
        """
        Calculate financing costs for positions

        Args:
            positions: Position DataFrame
            prices: Price DataFrame
            holding_period: Holding period in years

        Returns:
            Financing costs Series
        """
        # Get financing parameters
        financing_rate = self.config.get('financing_rate', 0.02)  # 2% annual
        short_premium = self.config.get('short_premium', 0.005)  # 0.5% for shorts
        margin_rate = self.config.get('margin_rate', 0.5)  # 50% margin requirement

        # Calculate position values
        position_values = positions.abs() * prices

        # Calculate financing costs
        long_costs = position_values.clip(lower=0) * financing_rate * holding_period / 365
        short_costs = position_values.clip(upper=0) * (financing_rate + short_premium) * holding_period / 365

        # Apply margin multiplier
        margin_multiplier = 1 + margin_rate
        total_costs = (long_costs + abs(short_costs)) * margin_multiplier

        return total_costs.sum(axis=1)


class TaxCalculator:
    """Tax calculation"""

    def __init__(self, **kwargs):
        self.config = kwargs

    def calculate(self, trades: List[Trade], current_prices: Dict[str, float]) -> float:
        """
        Calculate taxes for realized gains/losses

        Args:
            trades: List of trades
            current_prices: Current prices for unrealized positions

        Returns:
            Total tax amount
        """
        tax_rate = self.config.get('tax_rate', 0.2)  # 20% capital gains tax
        stt_rate = self.config.get('stt_rate', 0.001)  # Securities Transaction Tax

        # Calculate realized gains/losses
        realized_gains = self._calculate_realized_gains(trades)
        realized_tax = max(0, realized_gains * tax_rate)

        # Calculate STT
        trade_values = [abs(trade.quantity * trade.price) for trade in trades]
        stt_tax = sum(trade_values) * stt_rate

        return realized_tax + stt_tax

    def _calculate_realized_gains(self, trades: List[Trade]) -> float:
        """Calculate realized gains from trades"""
        positions = {}  # Track positions and average costs
        total_gains = 0

        for trade in trades:
            symbol = trade.symbol

            if symbol not in positions:
                positions[symbol] = {'quantity': 0, 'total_cost': 0}

            pos = positions[symbol]

            if trade.side == 'buy':
                # Update position
                new_quantity = pos['quantity'] + trade.quantity
                new_total_cost = pos['total_cost'] + (trade.quantity * trade.price)
                pos['quantity'] = new_quantity
                pos['total_cost'] = new_total_cost
            else:
                # Sell trade - calculate realized gain/loss
                if pos['quantity'] > 0:
                    avg_cost = pos['total_cost'] / pos['quantity']
                    sell_quantity = min(trade.quantity, pos['quantity'])
                    realized_gain = sell_quantity * (trade.price - avg_cost)
                    total_gains += realized_gain

                    # Update position
                    pos['quantity'] -= sell_quantity
                    pos['total_cost'] -= sell_quantity * avg_cost

        return total_gains


class TransactionCostModel:
    """
    Comprehensive transaction cost model
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transaction cost model

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Initialize cost calculators
        self.commission_calculator = CommissionCalculator(
            model=CommissionModel(config.get('commission_model', 'percentage')),
            **config.get('commission_config', {})
        )

        self.slippage_calculator = SlippageCalculator(
            model=SlippageModel(config.get('slippage_model', 'square_root')),
            **config.get('slippage_config', {})
        )

        self.market_impact_calculator = MarketImpactCalculator(
            model=MarketImpactModel(config.get('market_impact_model', 'square_root')),
            **config.get('market_impact_config', {})
        )

        self.financing_calculator = FinancingCostCalculator(
            **config.get('financing_config', {})
        )

        self.tax_calculator = TaxCalculator(
            **config.get('tax_config', {})
        )

        # Additional fees
        self.exchange_fees = config.get('exchange_fees', 0.0001)  # 1 bps
        self.clearing_fees = config.get('clearing_fees', 0.0001)  # 1 bps

        logger.info("Transaction cost model initialized")

    def calculate_trade_costs(self, trade: Trade) -> CostComponents:
        """
        Calculate all costs for a single trade

        Args:
            trade: Trade information

        Returns:
            CostComponents: All cost components
        """
        # Calculate individual components
        commission = self.commission_calculator.calculate(trade)
        slippage = self.slippage_calculator.calculate(trade)
        market_impact = self.market_impact_calculator.calculate(trade)

        # Exchange and clearing fees
        trade_value = abs(trade.quantity * trade.price)
        exchange_fee = trade_value * self.exchange_fees
        clearing_fee = trade_value * self.clearing_fees

        # Sum all components
        total = commission + slippage + market_impact + exchange_fee + clearing_fee

        return CostComponents(
            commission=commission,
            slippage=slippage,
            market_impact=market_impact,
            financing=0,  # Calculated separately for positions
            taxes=0,  # Calculated at portfolio level
            exchange_fees=exchange_fee,
            clearing_fees=clearing_fee,
            total=total
        )

    def calculate_portfolio_costs(
        self,
        trades: List[Trade],
        positions: pd.DataFrame,
        prices: pd.DataFrame,
        current_prices: Dict[str, float],
        holding_period: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate all portfolio-level costs

        Args:
            trades: List of all trades
            positions: Position DataFrame
            prices: Price DataFrame
            current_prices: Current prices for positions
            holding_period: Holding period in years

        Returns:
            Dictionary with all cost breakdowns
        """
        # Trade-level costs
        trade_costs = {
            'commission': 0,
            'slippage': 0,
            'market_impact': 0,
            'exchange_fees': 0,
            'clearing_fees': 0
        }

        for trade in trades:
            costs = self.calculate_trade_costs(trade)
            trade_costs['commission'] += costs.commission
            trade_costs['slippage'] += costs.slippage
            trade_costs['market_impact'] += costs.market_impact
            trade_costs['exchange_fees'] += costs.exchange_fees
            trade_costs['clearing_fees'] += costs.clearing_fees

        # Financing costs
        financing_costs = self.financing_calculator.calculate(positions, prices, holding_period)

        # Taxes
        tax_costs = self.tax_calculator.calculate(trades, current_prices)

        # Total costs
        total_trade_costs = sum(trade_costs.values())
        total_financing = financing_costs.sum()
        total_taxes = tax_costs
        total_costs = total_trade_costs + total_financing + total_taxes

        return {
            'commission': trade_costs['commission'],
            'slippage': trade_costs['slippage'],
            'market_impact': trade_costs['market_impact'],
            'exchange_fees': trade_costs['exchange_fees'],
            'clearing_fees': trade_costs['clearing_fees'],
            'financing': total_financing,
            'taxes': total_taxes,
            'total_trade_costs': total_trade_costs,
            'total_costs': total_costs,
            'cost_breakdown': {
                'trade_execution': total_trade_costs,
                'financing': total_financing,
                'taxes': total_taxes
            }
        }

    def optimize_execution(
        self,
        order: Dict[str, float],
        market_data: Dict[str, Any],
        time_horizon: float = 1.0
    ) -> Dict[str, Any]:
        """
        Optimize execution strategy to minimize costs

        Args:
            order: Order specification {symbol: quantity}
            market_data: Market data
            time_horizon: Execution time horizon in days

        Returns:
            Optimized execution schedule
        """
        # This is a simplified implementation
        # In practice, you would use more sophisticated algorithms

        optimized_schedule = {}
        total_cost = 0

        for symbol, quantity in order.items():
            # Get market data
            volume = market_data[symbol]['volume']
            volatility = market_data[symbol]['volatility']
            price = market_data[symbol]['price']

            # Calculate optimal execution size
            # Using square root impact model
            daily_volume_fraction = 0.1  # Execute 10% of daily volume
            optimal_daily_quantity = daily_volume_fraction * volume

            # Calculate number of days needed
            days_needed = int(np.ceil(abs(quantity) / optimal_daily_quantity))
            daily_quantity = quantity / days_needed

            # Calculate costs
            trade = Trade(
                timestamp=pd.Timestamp.now(),
                symbol=symbol,
                side='buy' if quantity > 0 else 'sell',
                quantity=daily_quantity,
                price=price,
                volume=volume,
                bid_ask_spread=price * 0.001,  # Assume 0.1% spread
                volatility=volatility,
                mid_price=price
            )

            daily_cost = self.calculate_trade_costs(trade)
            total_symbol_cost = daily_cost.total * days_needed
            total_cost += total_symbol_cost

            optimized_schedule[symbol] = {
                'daily_quantity': daily_quantity,
                'days_needed': days_needed,
                'daily_cost': daily_cost.total,
                'total_cost': total_symbol_cost
            }

        return {
            'schedule': optimized_schedule,
            'total_cost': total_cost,
            'time_horizon': max([s['days_needed'] for s in optimized_schedule.values()])
        }

    def estimate_costs_for_strategy(
        self,
        signals: pd.DataFrame,
        prices: pd.DataFrame,
        volumes: pd.DataFrame,
        volatilities: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Estimate costs for trading strategy signals

        Args:
            signals: Trading signals
            prices: Price data
            volumes: Volume data
            volatilities: Volatility data

        Returns:
            DataFrame with estimated costs
        """
        # Calculate position changes
        position_changes = signals.diff().fillna(0)

        # Initialize cost DataFrame
        costs = pd.DataFrame(index=position_changes.index, columns=position_changes.columns)

        for date in position_changes.index:
            for asset in position_changes.columns:
                if position_changes.loc[date, asset] != 0:
                    # Create trade object
                    trade = Trade(
                        timestamp=date,
                        symbol=asset,
                        side='buy' if position_changes.loc[date, asset] > 0 else 'sell',
                        quantity=abs(position_changes.loc[date, asset]),
                        price=prices.loc[date, asset],
                        volume=volumes.loc[date, asset],
                        bid_ask_spread=prices.loc[date, asset] * 0.001,
                        volatility=volatilities.loc[date, asset],
                        mid_price=prices.loc[date, asset]
                    )

                    # Calculate costs
                    trade_costs = self.calculate_trade_costs(trade)
                    costs.loc[date, asset] = trade_costs.total

        return costs.fillna(0)


# Utility functions
def create_default_cost_config() -> Dict[str, Any]:
    """Create default transaction cost configuration"""
    return {
        'commission_model': 'percentage',
        'commission_config': {
            'rate': 0.001,
            'min_commission': 0,
            'max_commission': float('inf')
        },
        'slippage_model': 'square_root',
        'slippage_config': {
            'base_rate': 0.0005,
            'impact_factor': 0.01
        },
        'market_impact_model': 'square_root',
        'market_impact_config': {
            'alpha': 0.001,
            'beta': 0.5
        },
        'financing_config': {
            'financing_rate': 0.02,
            'short_premium': 0.005,
            'margin_rate': 0.5
        },
        'tax_config': {
            'tax_rate': 0.2,
            'stt_rate': 0.001
        },
        'exchange_fees': 0.0001,
        'clearing_fees': 0.0001
    }


__all__ = [
    'TransactionCostModel',
    'CommissionCalculator',
    'SlippageCalculator',
    'MarketImpactCalculator',
    'FinancingCostCalculator',
    'TaxCalculator',
    'CostComponents',
    'Trade',
    'CommissionModel',
    'SlippageModel',
    'MarketImpactModel',
    'create_default_cost_config'
]