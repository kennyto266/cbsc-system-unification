# src/strategies/optimization/backtest/engine.py
import pandas as pd
import numpy as np
from typing import Callable, Dict, Any

class BacktestEngine:
    """
    Simple vectorized backtest engine for strategy optimization

    Supports:
    - Single asset backtesting
    - Transaction costs
    - Long/short positions
    """

    def __init__(self, initial_capital: float = 10000,
                 commission: float = 0.001,
                 slippage: float = 0.0001):
        """
        Initialize backtest engine

        Args:
            initial_capital: Starting capital
            commission: Commission rate (default: 0.1%)
            slippage: Slippage per trade (default: 0.01%)
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run(self, data: pd.DataFrame,
            strategy: Callable) -> Dict[str, Any]:
        """
        Run backtest with given strategy

        Args:
            data: DataFrame with OHLCV data
            strategy: Function that takes data window and returns position (-1, 0, 1)

        Returns:
            Dictionary with backtest results
        """
        # Generate signals
        signals = self._generate_signals(data, strategy)

        # Calculate returns
        returns = self._calculate_returns(data, signals)

        # Calculate metrics
        metrics = self._calculate_metrics(returns, data['close'])

        return metrics

    def _generate_signals(self, data: pd.DataFrame,
                         strategy: Callable) -> pd.Series:
        """Generate trading signals using strategy"""
        signals = pd.Series(0, index=data.index)

        # Rolling window strategy application
        window_size = 50  # Adjust based on strategy needs

        for i in range(window_size, len(data)):
            window = data.iloc[i-window_size:i]
            signal = strategy(window)
            signals.iloc[i] = signal

        return signals

    def _calculate_returns(self, data: pd.DataFrame,
                          signals: pd.Series) -> pd.Series:
        """Calculate returns from signals"""
        # Calculate price returns
        price_returns = data['close'].pct_change()

        # Apply signals with lag (trade at next open)
        position = signals.shift(1)

        # Calculate strategy returns
        strategy_returns = position * price_returns

        # Subtract transaction costs
        trades = position.diff().abs()
        transaction_costs = trades * (self.commission + self.slippage)

        net_returns = strategy_returns - transaction_costs

        return net_returns.fillna(0)

    def _calculate_metrics(self, returns: pd.Series,
                          prices: pd.Series) -> Dict[str, Any]:
        """Calculate backtest performance metrics"""
        # Total return
        total_return = (1 + returns).prod() - 1

        # Annualized return
        n_days = len(returns)
        annual_return = (1 + total_return) ** (252 / n_days) - 1

        # Volatility
        annual_vol = returns.std() * np.sqrt(252)

        # Sharpe Ratio
        risk_free_rate = 0.02
        sharpe_ratio = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0

        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calmar Ratio
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Win Rate
        win_rate = (returns > 0).sum() / len(returns) if len(returns) > 0 else 0

        return {
            'returns': returns,
            'total_return': float(total_return),
            'annual_return': float(annual_return),
            'volatility': float(annual_vol),
            'sharpe_ratio': float(sharpe_ratio),
            'max_drawdown': float(max_drawdown),
            'calmar_ratio': float(calmar_ratio),
            'win_rate': float(win_rate),
            'n_trades': int((returns != 0).sum())
        }
