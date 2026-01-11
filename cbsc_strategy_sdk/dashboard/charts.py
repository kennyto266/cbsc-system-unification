"""
Chart builders for Dash dashboard integration.

Provides ChartBuilders class for creating Plotly figures
compatible with Dash dcc.Graph components.
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

from .theme import ThemeManager


class ChartBuilders:
    """
    Collection of Plotly chart builders for Dash dashboards.

    Creates financial charts including candlestick, line charts,
    heatmaps, and performance analysis visualizations.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        """
        Initialize ChartBuilders.

        Args:
            theme_manager: Optional ThemeManager for consistent styling
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError(
                "Plotly is required for ChartBuilders. "
                "Install with: pip install plotly"
            )

        self.theme = theme_manager or ThemeManager()

    def candlestick_chart(
        self,
        df: pd.DataFrame,
        title: str = "Price Chart",
        show_volume: bool = True,
        height: int = 600,
    ) -> go.Figure:
        """
        Create candlestick chart for OHLCV data.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            title: Chart title
            show_volume: Whether to show volume subplot
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        required_cols = ['open', 'high', 'low', 'close']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Create subplots if showing volume
        if show_volume and 'volume' in df.columns:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
            )
        else:
            fig = go.Figure()

        # Get theme colors
        colors = self.theme.get_colors()

        # Add candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC',
                increasing_line_color=colors['up'],
                decreasing_line_color=colors['down'],
            ),
            row=1, col=1
        )

        # Add volume if available
        if show_volume and 'volume' in df.columns:
            colors_vol = [
                colors['up'] if close >= open_ else colors['down']
                for close, open_ in zip(df['close'], df['open'])
            ]

            fig.add_trace(
                go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='Volume',
                    marker_color=colors_vol,
                ),
                row=2, col=1
            )

        # Apply theme template
        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=height,
            xaxis_rangeslider_visible=False,
        )

        return fig

    def line_chart(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        title: str = "Line Chart",
        height: int = 400,
    ) -> go.Figure:
        """
        Create multi-line chart.

        Args:
            df: DataFrame with time series data
            columns: List of column names to plot (default: all numeric columns)
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not columns:
            raise ValueError("No numeric columns found in DataFrame")

        fig = go.Figure()

        # Get theme colors
        colors = self.theme.get_colors()
        color_palette = [
            colors['primary'],
            colors['secondary'],
            colors['success'],
            colors['warning'],
            colors['info'],
        ]

        for i, col in enumerate(columns):
            color = color_palette[i % len(color_palette)]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df[col],
                    mode='lines',
                    name=col,
                    line=dict(color=color, width=2),
                )
            )

        # Apply theme template
        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=height,
            hovermode='x unified',
        )

        return fig

    def heatmap(
        self,
        df: pd.DataFrame,
        title: str = "Correlation Heatmap",
        height: int = 500,
    ) -> go.Figure:
        """
        Create correlation heatmap.

        Args:
            df: DataFrame for correlation analysis
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        # Calculate correlation
        corr = df.corr()

        # Get theme colors
        colors = self.theme.get_colors()

        fig = go.Figure(
            data=go.Heatmap(
                z=corr.values,
                x=corr.columns,
                y=corr.columns,
                colorscale='RdBu',
                zmid=0,
                text=np.round(corr.values, 2),
                texttemplate='%{text}',
                textfont={"size": 10},
                colorbar=dict(title="Correlation"),
            )
        )

        # Apply theme
        fig.update_layout(
            template=template['layout'] if (template := self.theme.get_plotly_template()) else {},
            title=dict(text=title, x=0.5, xanchor='center'),
            height=height,
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            font=dict(color=colors['text']),
        )

        return fig

    def equity_curve(
        self,
        returns: pd.Series,
        benchmark: Optional[pd.Series] = None,
        title: str = "Equity Curve",
        height: int = 500,
    ) -> go.Figure:
        """
        Create equity curve chart from returns series.

        Args:
            returns: Series of strategy returns
            benchmark: Optional benchmark returns series
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        # Calculate cumulative returns
        cum_returns = (1 + returns).cumprod()

        fig = go.Figure()

        # Get theme colors
        colors = self.theme.get_colors()

        # Add strategy equity
        fig.add_trace(
            go.Scatter(
                x=cum_returns.index,
                y=cum_returns,
                mode='lines',
                name='Strategy',
                line=dict(color=colors['primary'], width=2),
            )
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
                    line=dict(color=colors['secondary'], width=2, dash='dash'),
                )
            )

        # Apply theme template
        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=height,
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
            hovermode='x unified',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        return fig

    def drawdown_chart(
        self,
        returns: pd.Series,
        title: str = "Drawdown Analysis",
        height: int = 400,
    ) -> go.Figure:
        """
        Create drawdown chart from returns series.

        Args:
            returns: Series of strategy returns
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        # Calculate cumulative returns and drawdown
        cum_returns = (1 + returns).cumprod()
        cummax = cum_returns.cummax()
        drawdown = (cum_returns - cummax) / cummax

        # Get theme colors
        colors = self.theme.get_colors()

        fig = go.Figure()

        # Add drawdown area
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color=colors['danger'], width=1),
            )
        )

        # Apply theme template
        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=height,
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode='x unified',
        )

        return fig

    def returns_distribution(
        self,
        returns: pd.Series,
        title: str = "Returns Distribution",
        height: int = 400,
    ) -> go.Figure:
        """
        Create returns distribution histogram.

        Args:
            returns: Series of strategy returns
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        # Get theme colors
        colors = self.theme.get_colors()

        fig = go.Figure()

        # Add histogram
        fig.add_trace(
            go.Histogram(
                x=returns,
                nbinsx=50,
                name='Returns',
                marker_color=colors['primary'],
                opacity=0.7,
            )
        )

        # Add mean line
        mean_return = returns.mean()
        fig.add_vline(
            x=mean_return,
            line_dash="dash",
            line_color=colors['text_secondary'],
            annotation_text=f"Mean: {mean_return:.2%}",
        )

        # Apply theme template
        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=height,
            xaxis_title="Return",
            yaxis_title="Frequency",
            showlegend=False,
        )

        return fig

    def comparison_chart(
        self,
        results: Dict[str, pd.Series],
        title: str = "Strategy Comparison",
        height: int = 500,
    ) -> go.Figure:
        """
        Create multi-strategy comparison chart.

        Args:
            results: Dictionary of strategy names to returns series
            title: Chart title
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        fig = go.Figure()

        # Get theme colors
        colors = self.theme.get_colors()
        color_palette = [
            colors['primary'],
            colors['secondary'],
            colors['success'],
            colors['warning'],
            colors['info'],
        ]

        for i, (name, returns) in enumerate(results.items()):
            cum_returns = (1 + returns).cumprod()
            color = color_palette[i % len(color_palette)]

            fig.add_trace(
                go.Scatter(
                    x=cum_returns.index,
                    y=cum_returns,
                    mode='lines',
                    name=name,
                    line=dict(color=color, width=2),
                )
            )

        # Apply theme template
        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=height,
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
            hovermode='x unified',
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        return fig
