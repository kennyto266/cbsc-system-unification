"""
Mean Reversion Strategy Template

Template for mean-reversion trading strategies.
Generates code for strategies that trade based on price deviations from mean.
"""

from typing import Any
from .base import StrategyTemplate, StrategyType, TemplateFactory


class MeanReversionTemplate(StrategyTemplate):
    """
    Template for mean-reversion strategies.

    Generates strategies that identify when prices have deviated significantly
    from their mean and trade the expected reversion.

    Required Parameters:
        - lookback_period: Period for mean calculation
        - entry_threshold: Standard deviations for entry
        - exit_threshold: Standard deviations for exit

    Optional Parameters:
        - use_bollinger: Use Bollinger Bands instead of fixed thresholds
        - bb_period: Bollinger Bands period
        - bb_std: Bollinger Bands standard deviation multiplier
        - min_holding_period: Minimum position holding period
    """

    @classmethod
    def get_strategy_type(cls) -> StrategyType:
        return StrategyType.MEAN_REVERSION

    @classmethod
    def get_required_parameters(cls) -> list[str]:
        return [
            "lookback_period",
            "entry_threshold",
            "exit_threshold",
        ]

    @classmethod
    def get_optional_parameters(cls) -> list[str]:
        return [
            "use_bollinger",
            "bb_period",
            "bb_std",
            "min_holding_period",
            "position_size",
        ]

    def generate_code(
        self,
        parameters: dict[str, Any],
        indicators: dict[str, Any],
    ) -> str:
        """Generate mean reversion strategy code."""
        strategy_name = parameters.get("name", "MeanReversionStrategy")
        lookback = parameters.get("lookback_period", 20)
        entry_threshold = parameters.get("entry_threshold", 2.0)
        exit_threshold = parameters.get("exit_threshold", 0.5)
        position_size = parameters.get("position_size", 0.1)

        use_bollinger = parameters.get("use_bollinger", False)

        if use_bollinger:
            bb_period = parameters.get("bb_period", 20)
            bb_std = parameters.get("bb_std", 2.0)
            bb_code = f"""
        # Use Bollinger Bands
        self.bb_period = {bb_period}
        self.bb_std = {bb_std}
        self.entry_threshold = {entry_threshold}
        self.exit_threshold = {exit_threshold}"""
            signal_logic = f"""
        # Calculate Bollinger Bands
        bb_upper, bb_lower, bb_middle = self._calculate_bollinger_bands(data)
        z_score = (data['close'] - bb_middle) / (bb_upper - bb_lower) * 2"""
        else:
            bb_code = f"""
        self.entry_threshold = {entry_threshold}
        self.exit_threshold = {exit_threshold}"""
            signal_logic = """
        # Calculate z-score of price
        rolling_mean = data['close'].rolling(window=self.lookback_period).mean()
        rolling_std = data['close'].rolling(window=self.lookback_period).std()
        z_score = (data['close'] - rolling_mean) / rolling_std"""

        min_holding_code = ""
        if "min_holding_period" in parameters:
            min_holding = parameters.get("min_holding_period", 5)
            min_holding_code = f"""
        # Enforce minimum holding period
        signals = self._apply_min_holding_period(signals, {min_holding})"""

        return f'''"""
{strategy_name}

Mean-reversion trading strategy that identifies when prices have
deviated significantly from their mean and trades the reversion.

Parameters:
    - lookback_period: {lookback} - Period for mean/std calculation
    - entry_threshold: {entry_threshold} - Z-score for entry signals
    - exit_threshold: {exit_threshold} - Z-score for exit signals
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any


class {strategy_name}:
    \"\"\"
    Mean Reversion Strategy Implementation.

    Identifies price deviations from statistical mean and trades
    the expected reversion to the mean.
    \"\"\"

    def __init__(
        self,
        lookback_period: int = {lookback},
        entry_threshold: float = {entry_threshold},
        exit_threshold: float = {exit_threshold},
        position_size: float = {position_size},
    ):
        \"\"\"
        Initialize mean reversion strategy.

        Args:
            lookback_period: Period for mean calculation
            entry_threshold: Z-score threshold for entry (standard deviations)
            exit_threshold: Z-score threshold for exit
            position_size: Fraction of capital to allocate per trade
        \"\"\"
        self.lookback_period = lookback_period
        self.position_size = position_size
{bb_code}

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        \"\"\"
        Generate trading signals based on mean reversion.

        Args:
            data: DataFrame with 'close' prices

        Returns:
            Series of trading signals (1=long, -1=short, 0=neutral)
        \"\"\"
{signal_logic}

        # Generate signals
        signals = pd.Series(0, index=data.index)

        # Entry signals
        signals[z_score < -self.entry_threshold] = 1   # Oversold - buy
        signals[z_score > self.entry_threshold] = -1  # Overbought - sell

        # Exit signals
        signals[abs(z_score) < self.exit_threshold] = 0
{min_holding_code}
        return signals
{self._get_bollinger_method(parameters)}
{self._get_holding_period_method(parameters)}

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        \"\"\"
        Run backtest on historical data.

        Args:
            data: Historical price data
            initial_capital: Starting capital

        Returns:
            Dictionary with backtest results
        \"\"\"
        signals = self.generate_signals(data)

        # Calculate returns
        returns = signals.shift(1) * data['close'].pct_change()

        # Calculate equity curve
        equity = (1 + returns * self.position_size).cumprod() * initial_capital

        return {{
            "final_equity": equity.iloc[-1],
            "total_return": (equity.iloc[-1] / initial_capital) - 1,
            "sharpe_ratio": self._calculate_sharpe(returns * self.position_size),
            "max_drawdown": self._calculate_max_drawdown(equity),
            "equity_curve": equity,
            "signals": signals,
        }}

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        \"\"\"Calculate Sharpe ratio.\"\"\"
        return returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0

    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        \"\"\"Calculate maximum drawdown.\"\"\"
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max
        return drawdown.min()
'''

    def _get_bollinger_method(self, parameters: dict) -> str:
        """Get Bollinger Bands calculation method if enabled."""
        if parameters.get("use_bollinger"):
            period = parameters.get("bb_period", 20)
            std_mult = parameters.get("bb_std", 2.0)
            return f"""

    def _calculate_bollinger_bands(
        self,
        data: pd.DataFrame
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        \"\"\"
        Calculate Bollinger Bands.

        Args:
            data: DataFrame with 'close' prices

        Returns:
            Tuple of (upper_band, lower_band, middle_band)
        \"\"\"
        middle = data['close'].rolling(window={period}).mean()
        std = data['close'].rolling(window={period}).std()
        upper = middle + ({std_mult} * std)
        lower = middle - ({std_mult} * std)
        return upper, lower, middle"""
        return ""

    def _get_holding_period_method(self, parameters: dict) -> str:
        """Get minimum holding period method if enabled."""
        if "min_holding_period" in parameters:
            return """

    def _apply_min_holding_period(
        self,
        signals: pd.Series,
        min_periods: int
    ) -> pd.Series:
        \"\"\"Apply minimum holding period constraint.\"\"\"
        result = signals.copy()
        last_entry = 0

        for i in range(1, len(result)):
            if result.iloc[i] != 0 and result.iloc[i-1] == 0:
                last_entry = i

            if result.iloc[i] == 0 and result.iloc[i-1] != 0:
                if i - last_entry < min_periods:
                    result.iloc[i] = result.iloc[i-1]

        return result"""
        return ""

    def _validate_parameter_values(
        self,
        parameters: dict[str, Any]
    ) -> tuple[bool, Any]:
        """Validate mean reversion specific parameters."""
        lookback = parameters.get("lookback_period")
        entry_threshold = parameters.get("entry_threshold")
        exit_threshold = parameters.get("exit_threshold")

        if lookback is not None and lookback <= 0:
            return False, "lookback_period must be positive"

        if entry_threshold is not None and exit_threshold is not None:
            if entry_threshold <= exit_threshold:
                return False, "entry_threshold must be greater than exit_threshold"

        return True, None


# Register template
TemplateFactory.register(MeanReversionTemplate)
