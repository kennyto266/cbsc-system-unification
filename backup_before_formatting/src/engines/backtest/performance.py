"""
Performance Analyzer for Backtesting
回測性能分析器

Provides comprehensive performance analysis capabilities for backtest results.
為回測結果提供全面的性能分析功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from ...core.logging import get_logger

logger = get_logger("engines.performance")


class PerformanceAnalyzer:
    """Comprehensive performance analyzer for backtesting results."""

    def __init__(self):
        self.logger = logger

    async def analyze(
        self,
        equity_curve: List[Tuple[datetime, float]],
        daily_returns: List[float],
        trades: List[Any],
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Analyze backtest performance comprehensively.

        Args:
            equity_curve: List of (timestamp, equity) tuples
            daily_returns: List of daily returns
            trades: List of executed trades
            initial_capital: Initial portfolio value

        Returns:
            Comprehensive performance metrics
        """
        if not equity_curve:
            return {"error": "No equity curve data available"}

        try:
            # Convert to pandas for easier analysis
            equity_df = pd.DataFrame(equity_curve, columns=["timestamp", "equity"])
            returns_series = pd.Series(daily_returns)

            # Basic metrics
            basic_metrics = self._calculate_basic_metrics(
                equity_df, returns_series, initial_capital
            )

            # Risk metrics
            risk_metrics = self._calculate_risk_metrics(returns_series, initial_capital)

            # Trade analysis
            trade_metrics = self._analyze_trades(trades)

            # Drawdown analysis
            drawdown_metrics = self._analyze_drawdowns(equity_df)

            # Monthly and yearly analysis
            time_metrics = self._analyze_time_periods(equity_df)

            # Combine all metrics
            performance_report = {
                "basic_metrics": basic_metrics,
                "risk_metrics": risk_metrics,
                "trade_metrics": trade_metrics,
                "drawdown_metrics": drawdown_metrics,
                "time_metrics": time_metrics,
                "analysis_timestamp": datetime.now().isoformat()
            }

            self.logger.info(
                "Performance analysis completed",
                total_return=basic_metrics["total_return"],
                sharpe_ratio=risk_metrics["sharpe_ratio"],
                max_drawdown=drawdown_metrics["max_drawdown"]
            )

            return performance_report

        except Exception as e:
            self.logger.error(f"Performance analysis failed: {e}")
            return {"error": str(e)}

    def _calculate_basic_metrics(
        self,
        equity_df: pd.DataFrame,
        returns: pd.Series,
        initial_capital: float
    ) -> Dict[str, Any]:
        """Calculate basic performance metrics."""
        final_equity = equity_df["equity"].iloc[-1]
        total_return = (final_equity - initial_capital) / initial_capital * 100

        # Annualized return
        if len(equity_df) > 1:
            days = (equity_df["timestamp"].iloc[-1] - equity_df["timestamp"].iloc[0]).days
            if days > 0:
                years = days / 365.25
                annualized_return = ((final_equity / initial_capital) ** (1/years) - 1) * 100
            else:
                annualized_return = 0.0
        else:
            annualized_return = 0.0

        # Daily statistics
        daily_stats = {}
        if not returns.empty:
            daily_stats = {
                "mean_daily_return": returns.mean(),
                "std_daily_return": returns.std(),
                "min_daily_return": returns.min(),
                "max_daily_return": returns.max(),
                "positive_days": (returns > 0).sum(),
                "negative_days": (returns < 0).sum(),
                "total_days": len(returns)
            }

        return {
            "initial_capital": initial_capital,
            "final_equity": final_equity,
            "total_return": round(total_return, 2),
            "annualized_return": round(annualized_return, 2),
            "daily_statistics": daily_stats,
            "total_trading_days": len(equity_df)
        }

    def _calculate_risk_metrics(
        self,
        returns: pd.Series,
        initial_capital: float
    ) -> Dict[str, Any]:
        """Calculate risk-related metrics."""
        if returns.empty:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "volatility": 0.0,
                "var_95": 0.0,
                "var_99": 0.0,
                "skewness": 0.0,
                "kurtosis": 0.0
            }

        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252)

        # Sharpe Ratio (assuming 3% risk-free rate)
        risk_free_rate = 0.03
        excess_return = returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0.0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if not downside_returns.empty:
            downside_deviation = downside_returns.std() * np.sqrt(252)
            sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0.0
        else:
            sortino_ratio = float('inf') if excess_return > 0 else 0.0

        # Value at Risk
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)

        # Skewness and Kurtosis
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        # Maximum loss
        max_loss = returns.min()

        return {
            "sharpe_ratio": round(sharpe_ratio, 4),
            "sortino_ratio": round(sortino_ratio, 4),
            "calmar_ratio": 0.0,  # Would need max drawdown to calculate
            "volatility": round(volatility * 100, 2),  # As percentage
            "var_95": round(var_95 * 100, 2),  # As percentage
            "var_99": round(var_99 * 100, 2),  # As percentage
            "max_daily_loss": round(max_loss * 100, 2),  # As percentage
            "skewness": round(skewness, 4),
            "kurtosis": round(kurtosis, 4)
        }

    def _analyze_trades(self, trades: List[Any]) -> Dict[str, Any]:
        """Analyze trading performance."""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "total_commission": 0.0
            }

        # Separate buy and sell trades
        buy_trades = [t for t in trades if hasattr(t, 'side') and t.side.value == "buy"]
        sell_trades = [t for t in trades if hasattr(t, 'side') and t.side.value == "sell"]

        if len(buy_trades) != len(sell_trades):
            # Incomplete trade pairs
            completed_pairs = min(len(buy_trades), len(sell_trades))
            buy_trades = buy_trades[:completed_pairs]
            sell_trades = sell_trades[:completed_pairs]

        if not buy_trades or not sell_trades:
            return self._empty_trade_analysis()

        # Calculate P&L for each completed trade
        trade_pnls = []
        total_commission = 0.0

        for buy_trade, sell_trade in zip(buy_trades, sell_trades):
            if buy_trade.symbol == sell_trade.symbol:
                # Calculate gross P&L
                gross_pnl = (sell_trade.price - buy_trade.price) * buy_trade.quantity

                # Subtract commissions
                total_commission += buy_trade.commission + sell_trade.commission
                net_pnl = gross_pnl - buy_trade.commission - sell_trade.commission

                trade_pnls.append(net_pnl)

        if not trade_pnls:
            return self._empty_trade_analysis()

        # Calculate statistics
        winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
        losing_trades = [pnl for pnl in trade_pnls if pnl < 0]

        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        total_trades_count = len(trade_pnls)

        win_rate = (win_count / total_trades_count * 100) if total_trades_count > 0 else 0.0
        avg_win = np.mean(winning_trades) if winning_trades else 0.0
        avg_loss = np.mean(losing_trades) if losing_trades else 0.0

        total_wins = sum(winning_trades)
        total_losses = abs(sum(losing_trades))
        profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf')

        # Trade duration analysis (if timestamps available)
        avg_duration_days = 0.0
        if buy_trades and sell_trades:
            durations = []
            for buy_trade, sell_trade in zip(buy_trades, sell_trades):
                if (hasattr(buy_trade, 'timestamp') and hasattr(sell_trade, 'timestamp') and
                    buy_trade.timestamp and sell_trade.timestamp):
                    duration = (sell_trade.timestamp - buy_trade.timestamp).days
                    durations.append(duration)

            if durations:
                avg_duration_days = np.mean(durations)

        return {
            "total_trades": total_trades_count,
            "winning_trades": win_count,
            "losing_trades": loss_count,
            "win_rate": round(win_rate, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "avg_win_percent": round((avg_win / buy_trades[0].price * buy_trades[0].quantity) * 100, 2) if buy_trades else 0.0,
            "avg_loss_percent": round((avg_loss / buy_trades[0].price * buy_trades[0].quantity) * 100, 2) if buy_trades else 0.0,
            "profit_factor": round(profit_factor, 2),
            "largest_win": round(max(winning_trades), 2) if winning_trades else 0.0,
            "largest_loss": round(min(losing_trades), 2) if losing_trades else 0.0,
            "avg_trade_duration_days": round(avg_duration_days, 1),
            "total_commission": round(total_commission, 2),
            "net_profit": round(sum(trade_pnls), 2)
        }

    def _empty_trade_analysis(self) -> Dict[str, Any]:
        """Return empty trade analysis structure."""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "avg_win_percent": 0.0,
            "avg_loss_percent": 0.0,
            "profit_factor": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "avg_trade_duration_days": 0.0,
            "total_commission": 0.0,
            "net_profit": 0.0
        }

    def _analyze_drawdowns(self, equity_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze drawdown characteristics."""
        if len(equity_df) < 2:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_duration": 0,
                "avg_drawdown": 0.0,
                "drawdown_frequency": 0.0
            }

        # Calculate running maximum and drawdown
        equity_df["running_max"] = equity_df["equity"].expanding().max()
        equity_df["drawdown"] = (equity_df["equity"] - equity_df["running_max"]) / equity_df["running_max"] * 100

        # Maximum drawdown
        max_drawdown = equity_df["drawdown"].min()

        # Find all drawdown periods
        in_drawdown = equity_df["drawdown"] < 0
        drawdown_periods = []

        start_idx = None
        for idx, is_dd in enumerate(in_drawdown):
            if is_dd and start_idx is None:
                start_idx = idx
            elif not is_dd and start_idx is not None:
                drawdown_periods.append((start_idx, idx))
                start_idx = None

        # Handle case where we end in drawdown
        if start_idx is not None:
            drawdown_periods.append((start_idx, len(equity_df) - 1))

        # Calculate drawdown statistics
        max_drawdown_duration = 0
        total_drawdown = 0.0
        drawdown_count = len(drawdown_periods)

        for start, end in drawdown_periods:
            duration = end - start
            max_drawdown_duration = max(max_drawdown_duration, duration)

            period_drawdown = equity_df["drawdown"].iloc[start:end]
            total_drawdown += period_drawdown.sum()

        avg_drawdown = (total_drawdown / len(in_drawdown)) if in_drawdown.any() else 0.0
        drawdown_frequency = (drawdown_count / len(equity_df)) * 100 if len(equity_df) > 0 else 0.0

        return {
            "max_drawdown": round(abs(max_drawdown), 2),
            "max_drawdown_duration": max_drawdown_duration,
            "avg_drawdown": round(abs(avg_drawdown), 2),
            "drawdown_frequency": round(drawdown_frequency, 2),
            "drawdown_periods": drawdown_count,
            "current_drawdown": round(abs(equity_df["drawdown"].iloc[-1]), 2) if not equity_df.empty else 0.0
        }

    def _analyze_time_periods(self, equity_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by time periods (monthly, yearly)."""
        if len(equity_df) < 2:
            return {"monthly_returns": {}, "yearly_returns": {}}

        # Convert timestamp to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(equity_df["timestamp"]):
            equity_df["timestamp"] = pd.to_datetime(equity_df["timestamp"])

        # Set timestamp as index
        equity_df.set_index("timestamp", inplace=True)

        # Calculate monthly returns
        monthly_equity = equity_df["equity"].resample("M").last()
        monthly_returns = monthly_equity.pct_change().dropna() * 100

        monthly_stats = {}
        if not monthly_returns.empty:
            monthly_stats = {
                "avg_monthly_return": round(monthly_returns.mean(), 2),
                "best_month": round(monthly_returns.max(), 2),
                "worst_month": round(monthly_returns.min(), 2),
                "positive_months": (monthly_returns > 0).sum(),
                "negative_months": (monthly_returns < 0).sum(),
                "total_months": len(monthly_returns)
            }

        # Calculate yearly returns
        yearly_equity = equity_df["equity"].resample("Y").last()
        yearly_returns = yearly_equity.pct_change().dropna() * 100

        yearly_stats = {}
        if not yearly_returns.empty:
            yearly_stats = {
                "avg_yearly_return": round(yearly_returns.mean(), 2),
                "best_year": round(yearly_returns.max(), 2),
                "worst_year": round(yearly_returns.min(), 2),
                "positive_years": (yearly_returns > 0).sum(),
                "negative_years": (yearly_returns < 0).sum(),
                "total_years": len(yearly_returns)
            }

        return {
            "monthly_analysis": monthly_stats,
            "yearly_analysis": yearly_stats,
            "monthly_returns": monthly_returns.to_dict(),
            "yearly_returns": yearly_returns.to_dict()
        }