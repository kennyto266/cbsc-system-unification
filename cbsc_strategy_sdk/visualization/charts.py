"""
Chart building module for interactive Plotly visualizations.

Provides ChartBuilder class for creating various financial charts
including candlestick, line, indicator overlays, and signal markers.
"""

from typing import Optional, List, Dict, Any, Union
import pandas as pd
from datetime import datetime

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from .themes import get_theme, Theme


class ChartBuilder:
    """
    Builder class for creating interactive Plotly charts.

    Supports candlestick, line, indicator overlays, and signal markers
    with customizable themes and layouts.
    """

    def __init__(self, theme: Union[str, Theme] = "dark"):
        """
        Initialize ChartBuilder with a theme.

        Args:
            theme: Theme name or Theme object for chart styling
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError(
                "Plotly is required for ChartBuilder. "
                "Install with: pip install plotly"
            )

        self.theme = get_theme(theme) if isinstance(theme, str) else theme
        self._figure = None

    def create_candlestick(
        self,
        data: pd.DataFrame,
        title: str = "Price Chart",
        show_volume: bool = True,
        height: int = 600,
    ) -> any:
        """
        Create an interactive candlestick chart.

        Args:
            data: DataFrame with OHLCV data
            title: Chart title
            show_volume: Whether to show volume subplot
            height: Chart height in pixels

        Returns:
            Plotly Figure object
        """
        required_cols = ['open', 'high', 'low', 'close']
        missing = [c for c in required_cols if c not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        if show_volume and 'volume' in data.columns:
            row_heights = [0.7, 0.3]
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=row_heights,
            )
        else:
            fig = go.Figure()

        colors = {
            'up': self.theme.colors.get('up', '#26a69a'),
            'down': self.theme.colors.get('down', '#ef5350')
        }

        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name='OHLC',
                increasing_line_color=colors['up'],
                decreasing_line_color=colors['down'],
            ),
            row=1, col=1
        )

        if show_volume and 'volume' in data.columns:
            colors_array = [
                colors['up'] if close >= open_val else colors['down']
                for close, open_val in zip(data['close'], data['open'])
            ]

            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['volume'],
                    name='Volume',
                    marker_color=colors_array,
                    opacity=0.7,
                ),
                row=2, col=1
            )

        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title=title,
            height=height,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
        )

        fig.update_yaxes(title_text="Price", row=1, col=1)
        if show_volume and 'volume' in data.columns:
            fig.update_yaxes(title_text="Volume", row=2, col=1)

        self._figure = fig
        return fig

    def plot_signals(
        self,
        data: pd.DataFrame,
        signals: pd.DataFrame,
        signal_col: str = 'signal',
    ) -> any:
        """
        Overlay buy/sell signals on an existing chart.

        Args:
            data: Price data DataFrame
            signals: DataFrame with signal column
            signal_col: Name of column containing signals (1=buy, -1=sell, 0=hold)

        Returns:
            Plotly Figure with signal markers
        """
        if self._figure is None:
            self.create_candlestick(data)

        fig = self._figure

        buy_color = self.theme.colors.get('buy', '#4caf50')
        sell_color = self.theme.colors.get('sell', '#f44336')

        buy_signals = signals[signals[signal_col] == 1]
        if not buy_signals.empty:
            buy_prices = data.loc[buy_signals.index, 'close']
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_prices,
                    mode='markers',
                    name='Buy',
                    marker=dict(
                        symbol='triangle-up',
                        size=15,
                        color=buy_color,
                        line=dict(width=2, color='white')
                    ),
                ),
                row=1, col=1
            )

        sell_signals = signals[signals[signal_col] == -1]
        if not sell_signals.empty:
            sell_prices = data.loc[sell_signals.index, 'close']
            fig.add_trace(
                go.Scatter(
                    x=sell_signals.index,
                    y=sell_prices,
                    mode='markers',
                    name='Sell',
                    marker=dict(
                        symbol='triangle-down',
                        size=15,
                        color=sell_color,
                        line=dict(width=2, color='white')
                    ),
                ),
                row=1, col=1
            )

        return fig

    def add_moving_average(
        self,
        data: pd.DataFrame,
        periods: List[int] = [5, 10, 20],
        column: str = 'close',
    ) -> any:
        """Add moving average lines to the chart."""
        if self._figure is None:
            self.create_candlestick(data)

        fig = self._figure

        ma_colors = [
            self.theme.colors.get('ma_short', '#29b6f6'),
            self.theme.colors.get('ma_medium', '#66bb6a'),
            self.theme.colors.get('ma_long', '#ffa726'),
        ]

        for i, period in enumerate(periods):
            ma = data[column].rolling(window=period).mean()
            color = ma_colors[i % len(ma_colors)]

            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=ma,
                    mode='lines',
                    name=f'MA{period}',
                    line=dict(color=color, width=1.5),
                ),
                row=1, col=1
            )

        return fig

    def add_bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = 'close',
    ) -> any:
        """Add Bollinger Bands to the chart."""
        if self._figure is None:
            self.create_candlestick(data)

        fig = self._figure

        ma = data[column].rolling(window=period).mean()
        std = data[column].rolling(window=period).std()
        upper = ma + (std * std_dev)
        lower = ma - (std * std_dev)

        upper_color = self.theme.colors.get('bb_upper', '#ef5350')
        lower_color = self.theme.colors.get('bb_lower', '#26a69a')
        middle_color = self.theme.colors.get('bb_middle', '#78909c')

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=upper,
                mode='lines',
                name=f'BB Upper ({period})',
                line=dict(color=upper_color, width=1),
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=lower,
                mode='lines',
                name=f'BB Lower ({period})',
                line=dict(color=lower_color, width=1),
                fill='tonexty',
                fillcolor='rgba(128, 128, 128, 0.1)',
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=ma,
                mode='lines',
                name=f'BB Middle ({period})',
                line=dict(color=middle_color, width=1, dash='dash'),
            ),
            row=1, col=1
        )

        return fig

    def create_line_chart(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        title: str = "Line Chart",
        height: int = 400,
    ) -> any:
        """Create a multi-line chart."""
        if columns is None:
            numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
            columns = numeric_cols[:1] if numeric_cols else [data.columns[0]]

        fig = go.Figure()

        default_colors = [
            self.theme.colors.get('primary', '#42a5f5'),
            self.theme.colors.get('secondary', '#ab47bc'),
            self.theme.colors.get('accent', '#ffca28'),
        ]

        for i, col in enumerate(columns):
            if col not in data.columns:
                continue
            color = default_colors[i % len(default_colors)]
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[col],
                    mode='lines',
                    name=col,
                    line=dict(color=color, width=2),
                )
            )

        template = self.theme.to_plotly_template()
        fig.update_layout(
            template=template,
            title=title,
            height=height,
            hovermode='x unified',
        )

        self._figure = fig
        return fig

    def export_html(self, filepath: str, include_plotlyjs: bool = True) -> None:
        """Export current figure to HTML file."""
        if self._figure is None:
            raise ValueError("No figure to export. Create a chart first.")

        self._figure.write_html(
            filepath,
            include_plotlyjs=include_plotlyjs,
            config={'displayModeBar': True}
        )

    def export_image(
        self,
        filepath: str,
        format: str = 'png',
        width: int = 1920,
        height: int = 1080,
        scale: float = 1.0,
    ) -> None:
        """Export current figure to image file."""
        if self._figure is None:
            raise ValueError("No figure to export. Create a chart first.")

        self._figure.write_image(
            filepath,
            format=format,
            width=width,
            height=height,
            scale=scale,
        )

    def show(self) -> None:
        """Display the current figure."""
        if self._figure is None:
            raise ValueError("No figure to display. Create a chart first.")
        self._figure.show()

    def get_figure(self) -> Optional[any]:
        """Get the current Plotly Figure object."""
        return self._figure


def create_sample_data(days: int = 100) -> pd.DataFrame:
    """Create sample OHLCV data for testing."""
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range(
        start=datetime.now() - pd.Timedelta(days=days),
        periods=days,
        freq='D'
    )

    returns = np.random.normal(0.001, 0.02, days)
    price = 100 * np.cumprod(1 + returns)

    noise = np.random.normal(0, 0.01, days)
    data = pd.DataFrame({
        'open': price * (1 + noise * 0.5),
        'high': price * (1 + np.abs(noise)),
        'low': price * (1 - np.abs(noise)),
        'close': price,
        'volume': np.random.randint(1000000, 10000000, days),
    }, index=dates)

    data['high'] = data[['open', 'close', 'high']].max(axis=1)
    data['low'] = data[['open', 'close', 'low']].min(axis=1)

    return data
