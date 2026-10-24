"""
Performance visualization module for strategy analysis.

Provides PerformanceCharts class for creating PnL, drawdown,
returns analysis, and backtest comparison charts.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .themes import get_theme, Theme


class PerformanceCharts:
    """
    Create performance analysis charts for trading strategies.

    Supports cumulative returns, drawdown analysis, PnL curves,
    and multi-strategy comparison visualizations.
    """

    def __init__(self, theme: str = "dark"):
        """
        Initialize PerformanceCharts with a theme.

        Args:
            theme: Theme name for chart styling
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError(
                "Plotly is required for PerformanceCharts. "
                "Install with: pip install plotly"
            )

        self.theme = get_theme(theme)

    def plot_performance(
        self,
        returns: pd.Series,
        benchmark: Optional[pd.Series] = None,
        title: str = "Strategy Performance",
        height: int = 500,
    ) -> any:
        """
        Plot cumulative returns and drawdown.

        Args:
            returns: Series of strategy returns
            benchmark: Optional benchmark returns series
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure with performance and drawdown subplots
        """
        # Calculate cumulative returns
        cum_returns = (1 + returns).cumprod()

        # Calculate drawdown
        cummax = cum_returns.cummax()
        drawdown = (cum_returns - cummax) / cummax

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=('Cumulative Returns', 'Drawdown'),
        )

        # Get colors
        primary_color = self.theme.colors.get('primary', '#42a5f5')
        benchmark_color = self.theme.colors.get('secondary', '#ab47bc')
        down_color = self.theme.colors.get('down', '#ef5350')

        # Add strategy returns
        fig.add_trace(
            go.Scatter(
                x=cum_returns.index,
                y=cum_returns,
                mode='lines',
                name='Strategy',
                line=dict(color=primary_color, width=2),
            ),
            row=1, col=1
        )

        # Add benchmark if provided
        if benchmark is not None:
            cum_benchmark = (1 + benchmark).cumprod()
            fig.add_trace(
                go.Scatter(
                    x=cum_benchmark.index,
                    y=cum_benchmark,
                    mode='lines',
                    name='Benchmark',
                    line=dict(color=benchmark_color, width=2, dash='dash'),
                ),
                row=1, col=1
            )

        # Add drawdown
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color=down_color, width=1.5),
            ),
            row=2, col=1
        )

        # Apply theme
        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title=title,
            height=height,
            hovermode='x unified',
        )

        fig.update_yaxes(title_text="Cumulative Return", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown", row=2, col=1)

        return fig

    def plot_pnl(
        self,
        pnl: pd.Series,
        title: str = "PnL Analysis",
        show_cumulative: bool = True,
        height: int = 500,
    ) -> any:
        """
        Plot profit and loss analysis.

        Args:
            pnl: Series of PnL values
            title: Chart title
            show_cumulative: Whether to show cumulative PnL
            height: Chart height in pixels

        Returns:
            Plotly Figure with PnL analysis
        """
        if show_cumulative:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=[0.6, 0.4],
                subplot_titles=('Cumulative PnL', 'Period PnL'),
            )

            cum_pnl = pnl.cumsum()

            # Colors
            up_color = self.theme.colors.get('up', '#26a69a')
            down_color = self.theme.colors.get('down', '#ef5350')

            # Color bars by profit/loss
            colors = [up_color if v >= 0 else down_color for v in cum_pnl]

            fig.add_trace(
                go.Bar(
                    x=cum_pnl.index,
                    y=cum_pnl,
                    name='Cumulative PnL',
                    marker_color=colors,
                ),
                row=1, col=1
            )

            colors = [up_color if v >= 0 else down_color for v in pnl]
            fig.add_trace(
                go.Bar(
                    x=pnl.index,
                    y=pnl,
                    name='Period PnL',
                    marker_color=colors,
                ),
                row=2, col=1
            )
        else:
            fig = go.Figure()

            up_color = self.theme.colors.get('up', '#26a69a')
            down_color = self.theme.colors.get('down', '#ef5350')

            colors = [up_color if v >= 0 else down_color for v in pnl]

            fig.add_trace(
                go.Bar(
                    x=pnl.index,
                    y=pnl,
                    name='PnL',
                    marker_color=colors,
                )
            )

        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title=title,
            height=height,
            hovermode='x',
        )

        return fig

    def plot_backtest_comparison(
        self,
        results: Dict[str, pd.DataFrame],
        metric: str = 'returns',
        title: str = "Strategy Comparison",
        height: int = 500,
    ) -> any:
        """
        Compare multiple backtest results.

        Args:
            results: Dictionary of strategy_name -> returns DataFrame
            metric: Metric to compare ('returns', 'sharpe', 'sortino')
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure comparing strategies
        """
        fig = go.Figure()

        colors = [
            self.theme.colors.get('primary', '#42a5f5'),
            self.theme.colors.get('secondary', '#ab47bc'),
            self.theme.colors.get('accent', '#ffca28'),
            self.theme.colors.get('up', '#26a69a'),
            self.theme.colors.get('down', '#ef5350'),
        ]

        for i, (name, data) in enumerate(results.items()):
            if metric == 'returns':
                if isinstance(data, pd.DataFrame):
                    returns = data.iloc[:, 0] if len(data.columns) > 0 else data
                else:
                    returns = data
                y_values = (1 + returns).cumprod()
                y_name = f'{name} (Cumulative)'
            elif metric == 'sharpe':
                # Calculate rolling sharpe
                if isinstance(data, pd.DataFrame):
                    returns = data.iloc[:, 0] if len(data.columns) > 0 else data
                else:
                    returns = data
                y_values = returns.rolling(20).mean() / returns.rolling(20).std()
                y_name = f'{name} (Sharpe)'
            else:
                # Default to cumulative returns
                if isinstance(data, pd.DataFrame):
                    returns = data.iloc[:, 0] if len(data.columns) > 0 else data
                else:
                    returns = data
                y_values = (1 + returns).cumprod()
                y_name = name

            color = colors[i % len(colors)]

            fig.add_trace(
                go.Scatter(
                    x=y_values.index,
                    y=y_values,
                    mode='lines',
                    name=y_name,
                    line=dict(color=color, width=2),
                )
            )

        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title=title,
            height=height,
            hovermode='x unified',
            xaxis_title="Date",
            yaxis_title="Value",
        )

        return fig

    def plot_rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 20,
        title: str = "Rolling Metrics",
        height: int = 500,
    ) -> any:
        """
        Plot rolling Sharpe and Sortino ratios.

        Args:
            returns: Series of returns
            window: Rolling window size
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure with rolling metrics
        """
        # Calculate rolling metrics
        mean = returns.rolling(window).mean()
        std = returns.rolling(window).std()

        # Sharpe ratio (assuming daily returns, annualizing)
        sharpe = (mean / std) * np.sqrt(252)

        # Sortino ratio (downside deviation)
        negative_returns = returns[returns < 0]
        downside_std = returns.rolling(window).apply(
            lambda x: np.sqrt(np.mean(np.minimum(x, 0) ** 2))
        )
        sortino = (mean / downside_std) * np.sqrt(252)

        fig = go.Figure()

        sharpe_color = self.theme.colors.get('primary', '#42a5f5')
        sortino_color = self.theme.colors.get('secondary', '#ab47bc')

        fig.add_trace(
            go.Scatter(
                x=sharpe.index,
                y=sharpe,
                mode='lines',
                name=f'Rolling Sharpe ({window})',
                line=dict(color=sharpe_color, width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=sortino.index,
                y=sortino,
                mode='lines',
                name=f'Rolling Sortino ({window})',
                line=dict(color=sortino_color, width=2),
            )
        )

        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray")

        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title=title,
            height=height,
            hovermode='x unified',
            xaxis_title="Date",
            yaxis_title="Ratio",
        )

        return fig

    def plot_monthly_returns(
        self,
        returns: pd.Series,
        title: str = "Monthly Returns Heatmap",
    ) -> any:
        """
        Create a monthly returns heatmap.

        Args:
            returns: Series of daily returns
            title: Chart title

        Returns:
            Plotly Figure with heatmap
        """
        # Resample to monthly returns
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

        # Create year and month columns
        monthly_returns = monthly_returns.to_frame('returns')
        monthly_returns['year'] = monthly_returns.index.year
        monthly_returns['month'] = monthly_returns.index.month

        # Pivot for heatmap
        pivot_table = monthly_returns.pivot(
            index='year',
            columns='month',
            values='returns'
        ) * 100  # Convert to percentage

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=month_names,
            y=pivot_table.index.astype(str),
            colorscale='RdYlGn',
            text=np.round(pivot_table.values, 2),
            texttemplate='%{text:.2f}%',
            textfont={"size": 10},
            colorbar=dict(title="Return %"),
        ))

        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title=title,
            xaxis_title="Month",
            yaxis_title="Year",
        )

        return fig

    def create_performance_dashboard(
        self,
        returns: pd.Series,
        benchmark: Optional[pd.Series] = None,
        height: int = 800,
    ) -> any:
        """
        Create comprehensive performance dashboard.

        Args:
            returns: Series of strategy returns
            benchmark: Optional benchmark returns
            height: Dashboard height

        Returns:
            Plotly Figure with multiple performance charts
        """
        # Calculate metrics
        cum_returns = (1 + returns).cumprod()
        cummax = cum_returns.cummax()
        drawdown = (cum_returns - cummax) / cummax

        # Create subplots (2x2 grid)
        fig = make_subplots(
            rows=2, cols=2,
            shared_xaxes=False,
            vertical_spacing=0.08,
            horizontal_spacing=0.08,
            subplot_titles=(
                'Cumulative Returns',
                'Drawdown',
                'Returns Distribution',
                'Rolling Sharpe (20)',
            ),
        )

        primary_color = self.theme.colors.get('primary', '#42a5f5')
        benchmark_color = self.theme.colors.get('secondary', '#ab47bc')
        down_color = self.theme.colors.get('down', '#ef5350')
        up_color = self.theme.colors.get('up', '#26a69a')

        # 1. Cumulative returns
        fig.add_trace(
            go.Scatter(
                x=cum_returns.index,
                y=cum_returns,
                mode='lines',
                name='Strategy',
                line=dict(color=primary_color, width=2),
            ),
            row=1, col=1
        )

        if benchmark is not None:
            cum_benchmark = (1 + benchmark).cumprod()
            fig.add_trace(
                go.Scatter(
                    x=cum_benchmark.index,
                    y=cum_benchmark,
                    mode='lines',
                    name='Benchmark',
                    line=dict(color=benchmark_color, width=2, dash='dash'),
                ),
                row=1, col=1
            )

        # 2. Drawdown
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color=down_color, width=1.5),
            ),
            row=1, col=2
        )

        # 3. Returns distribution
        fig.add_trace(
            go.Histogram(
                x=returns * 100,
                nbinsx=50,
                name='Returns',
                marker_color=primary_color,
            ),
            row=2, col=1
        )

        # 4. Rolling Sharpe
        rolling_sharpe = (
            returns.rolling(20).mean() /
            returns.rolling(20).std()
        ) * np.sqrt(252)

        fig.add_trace(
            go.Scatter(
                x=rolling_sharpe.index,
                y=rolling_sharpe,
                mode='lines',
                name='Sharpe',
                line=dict(color=up_color, width=2),
            ),
            row=2, col=2
        )

        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title="Performance Dashboard",
            height=height,
            hovermode='x unified',
            showlegend=True,
        )

        return fig
