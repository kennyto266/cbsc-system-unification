"""
Dynamic Risk Adjustment Mechanism

This module implements dynamic risk adjustment strategies including:
- Volatility-based position sizing
- Portfolio rebalancing triggers
- Volatility targeting algorithms
- Dynamic stop-loss mechanisms
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AdjustmentSignal(Enum):
    """Adjustment signal types"""
    NO_ACTION = "no_action"
    REDUCE_POSITION = "reduce_position"
    INCREASE_POSITION = "increase_position"
    REBALANCE_PORTFOLIO = "rebalance_portfolio"
    EMERGENCY_REDUCTION = "emergency_reduction"


@dataclass
class AdjustmentAction:
    """Adjustment action details"""
    signal: AdjustmentSignal
    asset: Optional[str] = None
    target_weight: Optional[float] = None
    current_weight: Optional[float] = None
    adjustment_factor: Optional[float] = None
    reason: Optional[str] = None
    timestamp: Optional[datetime] = None
    priority: int = 1  # 1=low, 2=medium, 3=high


class VolatilityTargeter:
    """Volatility targeting implementation"""

    def __init__(
        self,
        target_volatility: float = 0.15,
        lookback_window: int = 60,
        min_volatility: float = 0.05,
        max_volatility: float = 0.40
    ):
        """
        Initialize volatility targeter

        Args:
            target_volatility: Target annualized volatility (15% default)
            lookback_window: Window for volatility calculation
            min_volatility: Minimum volatility floor
            max_volatility: Maximum volatility ceiling
        """
        self.target_volatility = target_volatility
        self.lookback_window = lookback_window
        self.min_volatility = min_volatility
        self.max_volatility = max_volatility

    def calculate_volatility_scaled_position(
        self,
        returns: pd.Series,
        base_position: float = 1.0
    ) -> float:
        """
        Calculate position size based on volatility scaling

        Args:
            returns: Asset returns series
            base_position: Base position size

        Returns:
            Scaled position size
        """
        # Calculate realized volatility
        realized_vol = self._calculate_realized_volatility(returns)

        # Apply volatility floor and ceiling
        realized_vol = np.clip(realized_vol, self.min_volatility, self.max_volatility)

        # Scale position to target volatility
        scaled_position = base_position * (self.target_volatility / realized_vol)

        return scaled_position

    def calculate_portfolio_volatility_target(
        self,
        portfolio_returns: pd.Series,
        target_leverage: float = 1.0
    ) -> float:
        """
        Calculate portfolio leverage to achieve target volatility

        Args:
            portfolio_returns: Portfolio returns series
            target_leverage: Target maximum leverage

        Returns:
            Target leverage
        """
        realized_vol = self._calculate_realized_volatility(portfolio_returns)
        target_leverage = min(target_leverage, self.target_volatility / realized_vol)

        return max(0, target_leverage)

    def _calculate_realized_volatility(self, returns: pd.Series) -> float:
        """Calculate realized volatility with lookback window"""
        if len(returns) < self.lookback_window:
            window = len(returns)
        else:
            window = self.lookback_window

        # Use exponentially weighted volatility
        recent_returns = returns.tail(window)
        vol = recent_returns.ewm(span=min(20, window)).std().iloc[-1]

        # Annualize (assuming daily returns)
        return vol * np.sqrt(252)


class DynamicRebalancer:
    """Dynamic portfolio rebalancing implementation"""

    def __init__(
        self,
        rebalance_threshold: float = 0.05,
        lookback_window: int = 20,
        min_trade_size: float = 0.01,
        max_trade_size: float = 0.50
    ):
        """
        Initialize dynamic rebalancer

        Args:
            rebalance_threshold: Deviation threshold for rebalancing (5% default)
            lookback_window: Window for weight calculation
            min_trade_size: Minimum trade size
            max_trade_size: Maximum trade size
        """
        self.rebalance_threshold = rebalance_threshold
        self.lookback_window = lookback_window
        self.min_trade_size = min_trade_size
        self.max_trade_size = max_trade_size

    def calculate_rebalance_trades(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series
    ) -> List[AdjustmentAction]:
        """
        Calculate trades needed to rebalance portfolio

        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights

        Returns:
            List of adjustment actions
        """
        actions = []
        weight_diff = target_weights - current_weights
        weight_diff = weight_diff.dropna()

        for asset, diff in weight_diff.items():
            if abs(diff) > self.rebalance_threshold:
                # Calculate trade size
                trade_size = np.clip(
                    diff,
                    -self.max_trade_size,
                    self.max_trade_size
                )

                if abs(trade_size) >= self.min_trade_size:
                    action = AdjustmentAction(
                        signal=AdjustmentSignal.REBALANCE_PORTFOLIO,
                        asset=asset,
                        current_weight=current_weights.get(asset, 0),
                        target_weight=target_weights.get(asset, 0),
                        adjustment_factor=trade_size,
                        reason=f"Weight deviation: {diff:.2%}",
                        timestamp=datetime.now(),
                        priority=2
                    )
                    actions.append(action)

        return actions

    def should_rebalance(
        self,
        current_weights: pd.Series,
        target_weights: pd.Series
    ) -> bool:
        """
        Check if rebalancing is needed

        Args:
            current_weights: Current weights
            target_weights: Target weights

        Returns:
            True if rebalancing is needed
        """
        weight_diff = (target_weights - current_weights).abs()
        max_deviation = weight_diff.max()
        return max_deviation > self.rebalance_threshold


class DynamicStopLoss:
    """Dynamic stop-loss implementation"""

    def __init__(
        self,
        initial_stop_loss: float = 0.05,
        trailing_stop: bool = True,
        volatility_adjustment: bool = True,
        lookback_window: int = 20
    ):
        """
        Initialize dynamic stop-loss

        Args:
            initial_stop_loss: Initial stop-loss level (5% default)
            trailing_stop: Enable trailing stop
            volatility_adjustment: Adjust stop based on volatility
            lookback_window: Window for volatility calculation
        """
        self.initial_stop_loss = initial_stop_loss
        self.trailing_stop = trailing_stop
        self.volatility_adjustment = volatility_adjustment
        self.lookback_window = lookback_window
        self.highest_prices = {}  # Track highest prices for trailing stop

    def calculate_stop_loss_level(
        self,
        current_price: float,
        returns: pd.Series,
        position_side: str = "long",
        asset_id: str = "default"
    ) -> float:
        """
        Calculate dynamic stop-loss level

        Args:
            current_price: Current asset price
            returns: Recent returns for volatility
            position_side: "long" or "short"
            asset_id: Asset identifier for tracking

        Returns:
            Stop-loss price level
        """
        # Base stop-loss
        stop_loss = self.initial_stop_loss

        # Adjust for volatility if enabled
        if self.volatility_adjustment and len(returns) > 0:
            vol = returns.tail(self.lookback_window).std()
            vol_adjustment = min(vol * 2, 0.10)  # Cap at 10%
            stop_loss = max(self.initial_stop_loss, vol_adjustment)

        # Update highest price for trailing stop
        if position_side == "long":
            if asset_id not in self.highest_prices:
                self.highest_prices[asset_id] = current_price
            else:
                self.highest_prices[asset_id] = max(
                    self.highest_prices[asset_id],
                    current_price
                )

            # Calculate trailing stop price
            if self.trailing_stop:
                highest_price = self.highest_prices[asset_id]
                stop_price = highest_price * (1 - stop_loss)
            else:
                stop_price = current_price * (1 - stop_loss)

        else:  # short position
            if asset_id not in self.highest_prices:
                self.highest_prices[asset_id] = current_price
            else:
                self.highest_prices[asset_id] = min(
                    self.highest_prices[asset_id],
                    current_price
                )

            # Calculate trailing stop price for short
            if self.trailing_stop:
                lowest_price = self.highest_prices[asset_id]
                stop_price = lowest_price * (1 + stop_loss)
            else:
                stop_price = current_price * (1 + stop_loss)

        return stop_price

    def check_stop_loss_trigger(
        self,
        current_price: float,
        stop_price: float,
        position_side: str = "long"
    ) -> bool:
        """
        Check if stop-loss is triggered

        Args:
            current_price: Current price
            stop_price: Stop-loss price
            position_side: "long" or "short"

        Returns:
            True if stop-loss is triggered
        """
        if position_side == "long":
            return current_price <= stop_price
        else:  # short
            return current_price >= stop_price


class DynamicRiskAdjuster:
    """Main dynamic risk adjustment coordinator"""

    def __init__(
        self,
        volatility_targeter: VolatilityTargeter,
        rebalancer: DynamicRebalancer,
        stop_loss: DynamicStopLoss,
        config: Optional[Dict] = None
    ):
        """
        Initialize dynamic risk adjuster

        Args:
            volatility_targeter: Volatility targeting instance
            rebalancer: Rebalancing instance
            stop_loss: Stop-loss instance
            config: Configuration dictionary
        """
        self.volatility_targeter = volatility_targeter
        self.rebalancer = rebalancer
        self.stop_loss = stop_loss
        self.config = config or {}

        # Risk limits
        self.max_portfolio_volatility = self.config.get(
            "max_portfolio_volatility", 0.25
        )
        self.max_single_position = self.config.get(
            "max_single_position", 0.30
        )
        self.emergency_exit_threshold = self.config.get(
            "emergency_exit_threshold", 0.15
        )

    def generate_adjustment_signals(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        current_positions: Dict[str, float],
        current_prices: Dict[str, float]
    ) -> List[AdjustmentAction]:
        """
        Generate comprehensive adjustment signals

        Args:
            portfolio_data: Dictionary with returns and prices for each asset
            current_positions: Current positions (weights or absolute)
            current_prices: Current asset prices

        Returns:
            List of adjustment actions
        """
        actions = []

        # 1. Volatility-based position adjustments
        vol_actions = self._generate_volatility_adjustments(
            portfolio_data, current_positions
        )
        actions.extend(vol_actions)

        # 2. Portfolio rebalancing
        rebalance_actions = self._generate_rebalance_signals(
            portfolio_data, current_positions
        )
        actions.extend(rebalance_actions)

        # 3. Stop-loss checks
        stop_loss_actions = self._generate_stop_loss_signals(
            portfolio_data, current_positions, current_prices
        )
        actions.extend(stop_loss_actions)

        # 4. Risk limit checks
        risk_limit_actions = self._check_risk_limits(
            portfolio_data, current_positions
        )
        actions.extend(risk_limit_actions)

        # Sort by priority
        actions.sort(key=lambda x: x.priority, reverse=True)

        return actions

    def _generate_volatility_adjustments(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        current_positions: Dict[str, float]
    ) -> List[AdjustmentAction]:
        """Generate volatility-based adjustment actions"""
        actions = []

        # Portfolio-level volatility check
        if "portfolio" in portfolio_data:
            portfolio_returns = portfolio_data["portfolio"]["returns"]
            target_leverage = self.volatility_targeter.calculate_portfolio_volatility_target(
                portfolio_returns
            )

            current_leverage = sum(abs(pos) for pos in current_positions.values())

            if current_leverage > target_leverage * 1.1:  # 10% tolerance
                reduction_factor = target_leverage / current_leverage
                action = AdjustmentAction(
                    signal=AdjustmentSignal.REDUCE_POSITION,
                    adjustment_factor=reduction_factor,
                    reason=f"Reduce leverage from {current_leverage:.2f} to {target_leverage:.2f}",
                    timestamp=datetime.now(),
                    priority=2
                )
                actions.append(action)

        # Asset-level volatility adjustments
        for asset, data in portfolio_data.items():
            if asset == "portfolio" or "returns" not in data:
                continue

            returns = data["returns"]
            current_pos = current_positions.get(asset, 0)

            if current_pos != 0:
                scaled_position = self.volatility_targeter.calculate_volatility_scaled_position(
                    returns, abs(current_pos)
                )

                # Check if significant adjustment needed
                adjustment_factor = scaled_position / abs(current_pos)
                if abs(adjustment_factor - 1) > 0.1:  # 10% threshold
                    action = AdjustmentAction(
                        signal=AdjustmentSignal.REDUCE_POSITION if adjustment_factor < 1 else AdjustmentSignal.INCREASE_POSITION,
                        asset=asset,
                        current_weight=current_pos,
                        target_weight=scaled_position * np.sign(current_pos),
                        adjustment_factor=adjustment_factor,
                        reason=f"Volatility scaling: {adjustment_factor:.2f}",
                        timestamp=datetime.now(),
                        priority=2
                    )
                    actions.append(action)

        return actions

    def _generate_rebalance_signals(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        current_positions: Dict[str, float]
    ) -> List[AdjustmentAction]:
        """Generate portfolio rebalancing signals"""
        # This would integrate with the strategy management system
        # For now, return empty list
        return []

    def _generate_stop_loss_signals(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        current_positions: Dict[str, float],
        current_prices: Dict[str, float]
    ) -> List[AdjustmentAction]:
        """Generate stop-loss signals"""
        actions = []

        for asset, data in portfolio_data.items():
            if asset == "portfolio" or "returns" not in data:
                continue

            current_pos = current_positions.get(asset, 0)
            current_price = current_prices.get(asset)

            if current_pos != 0 and current_price is not None:
                returns = data["returns"]
                position_side = "long" if current_pos > 0 else "short"

                stop_price = self.stop_loss.calculate_stop_loss_level(
                    current_price, returns, position_side, asset
                )

                if self.stop_loss.check_stop_loss_trigger(
                    current_price, stop_price, position_side
                ):
                    action = AdjustmentAction(
                        signal=AdjustmentSignal.EMERGENCY_REDUCTION,
                        asset=asset,
                        current_weight=current_pos,
                        target_weight=0,
                        reason=f"Stop-loss triggered at {stop_price:.2f}",
                        timestamp=datetime.now(),
                        priority=3
                    )
                    actions.append(action)

        return actions

    def _check_risk_limits(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        current_positions: Dict[str, float]
    ) -> List[AdjustmentAction]:
        """Check risk limits and generate alerts"""
        actions = []

        # Check single position limits
        for asset, position in current_positions.items():
            if abs(position) > self.max_single_position:
                action = AdjustmentAction(
                    signal=AdjustmentSignal.REDUCE_POSITION,
                    asset=asset,
                    current_weight=position,
                    target_weight=np.sign(position) * self.max_single_position,
                    reason=f"Position exceeds limit: {abs(position):.2%} > {self.max_single_position:.2%}",
                    timestamp=datetime.now(),
                    priority=3
                )
                actions.append(action)

        # Check portfolio volatility limit
        if "portfolio" in portfolio_data and "returns" in portfolio_data["portfolio"]:
            returns = portfolio_data["portfolio"]["returns"]
            if len(returns) > 20:
                current_vol = returns.tail(20).std() * np.sqrt(252)

                if current_vol > self.max_portfolio_volatility:
                    action = AdjustmentAction(
                        signal=AdjustmentSignal.EMERGENCY_REDUCTION,
                        adjustment_factor=self.max_portfolio_volatility / current_vol,
                        reason=f"Portfolio volatility exceeds limit: {current_vol:.2%}",
                        timestamp=datetime.now(),
                        priority=3
                    )
                    actions.append(action)

        return actions