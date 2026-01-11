"""
BacktestResult with visualization and analysis methods.

This module provides the BacktestResult class which encapsulates
backtest results with pandas DataFrame conversion and Plotly visualization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .models import BacktestJob, BacktestMetrics, BacktestResultData, BacktestTrade


class BacktestResult:
    """Container for backtest results with visualization methods.

    This class provides methods for parsing backtest results, converting
    to pandas DataFrames, and generating Plotly visualizations.

    Attributes:
        raw: Raw result data from API
        job: Job metadata
        metrics: Performance metrics
        trades: List of trades
        equity_curve: Equity curve data

    Example:
        >>> result = BacktestResult(raw_data=api_response)
        >>>
        >>> # View summary
        >>> print(result.summary())
        >>>
        >>> # Convert to DataFrame
        >>> df = result.to_dataframe()
        >>>
        >>> # Plot equity curve
        >>> result.plot_equity_curve()
    """

    def __init__(self, raw_data: BacktestResultData) -> None:
        """Initialize BacktestResult.

        Args:
            raw_data: Raw result data from API
        """
        self.raw: BacktestResultData = raw_data
        self.job: BacktestJob = raw_data.job
        self.metrics: BacktestMetrics = raw_data.metrics
        self.trades: List[BacktestTrade] = raw_data.trades
        self.equity_curve: List[Dict[str, Any]] = raw_data.equity_curve

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to pandas DataFrame.

        Creates a DataFrame with trade data including entry/exit times,
        prices, PnL, and other trade details.

        Returns:
            DataFrame with trade data

        Example:
            >>> df = result.to_dataframe()
            >>> print(df.head())
            >>> print(df.groupby('direction')['pnl'].sum())
        """
        if not self.trades:
            return pd.DataFrame()

        data = []
        for trade in self.trades:
            data.append({
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "entry_time": trade.entry_time,
                "exit_time": trade.exit_time,
                "direction": trade.direction,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "quantity": trade.quantity,
                "pnl": trade.pnl,
                "pnl_percent": trade.pnl_percent,
            })

        df = pd.DataFrame(data)

        # Add derived columns
        if not df.empty:
            df["holding_period_days"] = (df["exit_time"] - df["entry_time"]).dt.total_seconds() / 86400
            df["is_winner"] = df["pnl"] > 0

        return df

    def get_equity_dataframe(self) -> pd.DataFrame:
        """Get equity curve as pandas DataFrame.

        Returns:
            DataFrame with timestamp and equity value columns

        Example:
            >>> df = result.get_equity_dataframe()
            >>> df.plot(figsize=(12, 6))
        """
        if not self.equity_curve:
            return pd.DataFrame(columns=["timestamp", "equity", "drawdown"])

        data = []
        for point in self.equity_curve:
            data.append({
                "timestamp": datetime.fromisoformat(point.get("timestamp", "")),
                "equity": point.get("equity", 0),
                "drawdown": point.get("drawdown", 0),
            })

        return pd.DataFrame(data)

    def plot_equity_curve(
        self,
        figsize: Tuple[int, int] = (12, 6),
        show_drawdown: bool = True,
        benchmark_return: Optional[float] = None,
    ) -> Optional[go.Figure]:
        """Plot equity curve using Plotly.

        Args:
            figsize: Figure size (width, height)
            show_drawdown: Whether to show drawdown subplot
            benchmark_return: Optional benchmark return to compare

        Returns:
            Plotly figure object, or None if Plotly not available

        Example:
            >>> fig = result.plot_equity_curve()
            >>> fig.show()
        """
        if not PLOTLY_AVAILABLE:
            print("Plotly not available. Install with: pip install plotly")
            return None

        equity_df = self.get_equity_dataframe()

        if equity_df.empty:
            print("No equity curve data available")
            return None

        # Create subplot with drawdown if requested
        if show_drawdown:
            fig = make_subplots(
                rows=2,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=("Equity Curve", "Drawdown"),
            )
        else:
            fig = go.Figure()

        # Add equity curve trace
        fig.add_trace(
            go.Scatter(
                x=equity_df["timestamp"],
                y=equity_df["equity"],
                mode="lines",
                name="Strategy",
                line=dict(color="#2ecc71", width=2),
            ),
            row=1,
            col=1,
        )

        # Add benchmark if provided
        if benchmark_return is not None:
            initial_equity = equity_df["equity"].iloc[0]
            benchmark_equity = initial_equity * (1 + benchmark_return * np.arange(len(equity_df)) / len(equity_df))

            fig.add_trace(
                go.Scatter(
                    x=equity_df["timestamp"],
                    y=benchmark_equity,
                    mode="lines",
                    name="Benchmark",
                    line=dict(color="#95a5a6", width=1, dash="dash"),
                ),
                row=1,
                col=1,
            )

        # Add drawdown
        if show_drawdown:
            fig.add_trace(
                go.Scatter(
                    x=equity_df["timestamp"],
                    y=equity_df["drawdown"] * 100,  # Convert to percentage
                    mode="lines",
                    name="Drawdown",
                    fill="tozeroy",
                    line=dict(color="#e74c3c", width=1),
                ),
                row=2,
                col=1,
            )

        # Update layout
        fig.update_layout(
            width=figsize[0] * 80,
            height=figsize[1] * 80,
            title=dict(
                text=f"Backtest Results: {self.job.job_id}",
                x=0.5,
                xanchor="center",
            ),
            hovermode="x unified",
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Equity ($)", row=1, col=1)

        if show_drawdown:
            fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)

        return fig

    def plot_drawdown(self, figsize: Tuple[int, int] = (12, 4)) -> Optional[go.Figure]:
        """Plot drawdown chart.

        Args:
            figsize: Figure size (width, height)

        Returns:
            Plotly figure object, or None if Plotly not available

        Example:
            >>> fig = result.plot_drawdown()
            >>> fig.show()
        """
        if not PLOTLY_AVAILABLE:
            print("Plotly not available. Install with: pip install plotly")
            return None

        equity_df = self.get_equity_dataframe()

        if equity_df.empty or "drawdown" not in equity_df.columns:
            print("No drawdown data available")
            return None

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=equity_df["timestamp"],
                y=equity_df["drawdown"] * 100,
                mode="lines",
                name="Drawdown",
                fill="tozeroy",
                line=dict(color="#e74c3c", width=2),
            )
        )

        fig.update_layout(
            width=figsize[0] * 80,
            height=figsize[1] * 80,
            title=dict(
                text="Drawdown Analysis",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode="x",
        )

        return fig

    def plot_monthly_returns(
        self,
        figsize: Tuple[int, int] = (12, 6),
    ) -> Optional[go.Figure]:
        """Plot monthly returns heatmap.

        Args:
            figsize: Figure size (width, height)

        Returns:
            Plotly figure object, or None if Plotly not available

        Example:
            >>> fig = result.plot_monthly_returns()
            >>> fig.show()
        """
        if not PLOTLY_AVAILABLE:
            print("Plotly not available. Install with: pip install plotly")
            return None

        equity_df = self.get_equity_dataframe()

        if equity_df.empty:
            print("No equity data available")
            return None

        # Calculate daily returns
        equity_df = equity_df.set_index("timestamp").sort_index()
        daily_returns = equity_df["equity"].pct_change().fillna(0)

        # Resample to monthly returns
        monthly_returns = daily_returns.resample("M").apply(
            lambda x: (1 + x).prod() - 1
        ) * 100

        # Create pivot table for heatmap
        monthly_df = pd.DataFrame({
            "year": monthly_returns.index.year,
            "month": monthly_returns.index.month,
            "return": monthly_returns.values,
        })

        pivot = monthly_df.pivot(index="month", columns="year", values="return")

        # Create heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=[
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ],
                colorscale="RdYlGn",
                text=np.round(pivot.values, 2),
                texttemplate="%{text}%",
                textfont={"size": 10},
                colorbar=dict(title="Return (%)"),
            )
        )

        fig.update_layout(
            width=figsize[0] * 80,
            height=figsize[1] * 80,
            title=dict(
                text="Monthly Returns (%)",
                x=0.5,
                xanchor="center",
            ),
            xaxis_title="Year",
            yaxis_title="Month",
        )

        return fig

    def summary(self) -> str:
        """Generate text summary of results.

        Returns:
            Formatted summary string

        Example:
            >>> print(result.summary())
        """
        lines = [
            "=" * 60,
            f"Backtest Summary: {self.job.job_id}",
            "=" * 60,
            "",
            "Performance Metrics:",
            f"  Total Return:     {self.metrics.total_return:>8.2f}%",
            f"  Annual Return:    {self.metrics.annual_return:>8.2f}%",
            f"  Sharpe Ratio:     {self.metrics.sharpe_ratio:>8.2f}",
            f"  Max Drawdown:     {self.metrics.max_drawdown:>8.2f}%",
            f"  Win Rate:         {self.metrics.win_rate:>8.2f}%",
            f"  Profit Factor:    {self.metrics.profit_factor:>8.2f}",
            "",
            "Trading Statistics:",
            f"  Total Trades:     {self.metrics.total_trades:>8}",
            f"  Profit Trades:    {self.metrics.profit_trades:>8}",
            f"  Loss Trades:      {self.metrics.total_trades - self.metrics.profit_trades:>8}",
            f"  Avg Profit:       {self.metrics.avg_profit:>8.2f}%",
            f"  Avg Loss:         {self.metrics.avg_loss:>8.2f}%",
            "",
        ]

        # Add timing information
        if self.job.started_at and self.job.completed_at:
            duration = (self.job.completed_at - self.job.started_at).total_seconds()
            lines.extend([
                "Job Information:",
                f"  Started:          {self.job.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"  Completed:        {self.job.completed_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"  Duration:         {duration:>8.1f} seconds",
                "",
            ])

        lines.append("=" * 60)

        return "\n".join(lines)

    def get_metrics_dict(self) -> Dict[str, Any]:
        """Get metrics as dictionary.

        Returns:
            Dictionary of metrics

        Example:
            >>> metrics = result.get_metrics_dict()
            >>> print(f"Sharpe: {metrics['sharpe_ratio']}")
        """
        return {
            "total_return": self.metrics.total_return,
            "annual_return": self.metrics.annual_return,
            "sharpe_ratio": self.metrics.sharpe_ratio,
            "sortino_ratio": self.metrics.sortino_ratio,
            "max_drawdown": self.metrics.max_drawdown,
            "calmar_ratio": self.metrics.calmar_ratio,
            "win_rate": self.metrics.win_rate,
            "profit_factor": self.metrics.profit_factor,
            "total_trades": self.metrics.total_trades,
            "profit_trades": self.metrics.profit_trades,
            "avg_profit": self.metrics.avg_profit,
            "avg_loss": self.metrics.avg_loss,
        }

    def calculate_rolling_metrics(
        self,
        window: int = 20,
    ) -> pd.DataFrame:
        """Calculate rolling performance metrics.

        Args:
            window: Rolling window size in days

        Returns:
            DataFrame with rolling metrics

        Example:
            >>> rolling = result.calculate_rolling_metrics(window=30)
            >>> rolling.plot(y=['sharpe', 'returns'])
        """
        equity_df = self.get_equity_dataframe()

        if equity_df.empty:
            return pd.DataFrame()

        equity_df = equity_df.set_index("timestamp").sort_index()

        # Calculate daily returns
        daily_returns = equity_df["equity"].pct_change().fillna(0)

        # Calculate rolling metrics
        rolling = pd.DataFrame({
            "returns": daily_returns.rolling(window).mean() * 252,  # Annualized
            "volatility": daily_returns.rolling(window).std() * np.sqrt(252),
            "sharpe": (daily_returns.rolling(window).mean() * 252) /
                     (daily_returns.rolling(window).std() * np.sqrt(252) + 1e-6),
            "drawdown": equity_df["drawdown"],
        })

        return rolling

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"BacktestResult(job_id='{self.job.job_id}', "
            f"return={self.metrics.total_return:.2f}%, "
            f"sharpe={self.metrics.sharpe_ratio:.2f})"
        )
