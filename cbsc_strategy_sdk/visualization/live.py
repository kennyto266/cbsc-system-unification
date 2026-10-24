"""Live charting with Plotly for real-time data visualization.

Provides Plotly-based charts that update in real-time with streaming data.
"""

import asyncio
import logging
from typing import Optional, Union

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    make_subplots = None

from ..data.models import TickData
from ..data.buffer import TickCircularBuffer

logger = logging.getLogger(__name__)


class LiveChart:
    """Plotly chart that updates in real-time with streaming data.

    Creates interactive charts that automatically update as new data arrives.
    Designed for use in Jupyter notebooks with FigureWidget.

    Example:
        >>> chart = LiveChart(title="AAPL Live Price", max_points=100)
        >>> chart.add_line(name='price', color='blue')
        >>>
        >>> # Update with tick data
        >>> chart.update(tick)
        >>>
        >>> # Display in Jupyter
        >>> chart.show()
    """

    def __init__(
        self,
        title: str = "Live Data",
        max_points: int = 1000,
        subplot_count: int = 1,
    ) -> None:
        """Initialize live chart.

        Args:
            title: Chart title
            max_points: Maximum number of points to display
            subplot_count: Number of subplots (1 or 2)

        Raises:
            ImportError: If Plotly is not installed
        """
        if not PLOTLY_AVAILABLE:
            raise ImportError("Plotly is required. Install: pip install plotly")

        self.title = title
        self.max_points = max_points
        self.subplot_count = subplot_count

        # Data storage
        self._timestamps: list = []
        self._data: dict[str, list] = {}

        # Create figure
        if subplot_count == 1:
            self.fig = go.Figure()
        else:
            self.fig = make_subplots(
                rows=subplot_count,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.02,
            )

        # Update layout
        self._setup_layout()

    def _setup_layout(self) -> None:
        """Configure chart layout."""
        self.fig.update_layout(
            title=self.title,
            xaxis_title="Time",
            yaxis_title="Value",
            hovermode='x unified',
            showlegend=True,
            height=400,
            margin=dict(l=0, r=0, t=40, b=0),
        )

    def add_line(
        self,
        name: str,
        color: str = 'blue',
        row: int = 1,
    ) -> None:
        """Add a line trace to the chart.

        Args:
            name: Trace name
            color: Line color
            row: Subplot row (1-indexed)

        Example:
            >>> chart.add_line(name='price', color='green')
            >>> chart.add_line(name='volume', color='orange', row=2)
        """
        if name not in self._data:
            self._data[name] = []

        # Add scatter trace
        self.fig.add_trace(
            go.Scatter(
                name=name,
                mode='lines+markers',
                line=dict(color=color, width=1),
                marker=dict(size=4),
                opacity=0.8,
            ),
            row=row,
            col=1,
        )

    def add_candlestick(
        self,
        name: str = "OHLCV",
        row: int = 1,
    ) -> None:
        """Add a candlestick trace for OHLCV data.

        Args:
            name: Trace name
            row: Subplot row (1-indexed)

        Example:
            >>> chart.add_candlestick(name='AAPL')
        """
        # Add candlestick trace
        self.fig.add_trace(
            go.Candlestick(
                name=name,
                increasing=dict(line=dict(color='green')),
                decreasing=dict(line=dict(color='red')),
            ),
            row=row,
            col=1,
        )

    def update(self, tick: Union[TickData, dict], field_map: Optional[dict] = None) -> None:
        """Update chart with new tick data.

        Args:
            tick: TickData object or dictionary
            field_map: Optional mapping from tick fields to trace names
                e.g., {'price': 'price', 'volume': 'volume'}

        Example:
            >>> # With TickData
            >>> chart.update(tick)
            >>>
            >>> # With custom mapping
            >>> chart.update(tick, field_map={'price': 'AAPL Price'})
        """
        if isinstance(tick, TickData):
            timestamp = tick.timestamp
            data = {
                'price': [tick.price],
                'volume': [tick.volume],
                'bid': [tick.bid] if tick.bid else [],
                'ask': [tick.ask] if tick.ask else [],
            }
        else:
            timestamp = tick.get('timestamp')
            data = {k: [v] for k, v in tick.items() if k != 'timestamp'}

        # Add timestamp
        self._timestamps.append(timestamp)

        # Apply field mapping
        if field_map:
            mapped_data = {}
            for trace_name, field in field_map.items():
                if field in data:
                    mapped_data[trace_name] = data[field]
            data = mapped_data

        # Update data storage
        for field, values in data.items():
            if field not in self._data:
                self._data[field] = []
            self._data[field].extend(values)

        # Trim to max points
        if len(self._timestamps) > self.max_points:
            self._timestamps = self._timestamps[-self.max_points:]
            for field in self._data:
                self._data[field] = self._data[field][-self.max_points:]

        # Update figure
        self._update_figure()

    def _update_figure(self) -> None:
        """Update figure data with current buffers."""
        for i, trace in enumerate(self.fig.data):
            # Get trace name
            trace_name = trace.name

            if trace_name in self._data and self._timestamps:
                # Update trace data
                y_data = self._data[trace_name]

                # Ensure lengths match
                min_len = min(len(self._timestamps), len(y_data))
                x_data = self._timestamps[-min_len:]
                y_data = y_data[-min_len:]

                # Update trace
                with self.fig.batch_update():
                    self.fig.data[i].x = x_data
                    self.fig.data[i].y = y_data

    def update_from_buffer(self, buffer: TickCircularBuffer) -> None:
        """Update chart from a TickCircularBuffer.

        Args:
            buffer: TickCircularBuffer with data

        Example:
            >>> chart.update_from_buffer(stream.get_buffer('AAPL'))
        """
        if buffer.is_empty:
            return

        df = buffer.to_dataframe()

        if df.empty:
            return

        # Update timestamps
        if 'timestamp' in df.columns:
            self._timestamps = df['timestamp'].tolist()

        # Update data fields
        for col in df.columns:
            if col == 'timestamp':
                continue
            if col not in self._data:
                self._data[col] = []
            self._data[col] = df[col].tolist()

        # Update figure
        self._update_figure()

    def to_widget(self):
        """Convert to Plotly FigureWidget for Jupyter.

        Returns:
            plotly.graph_objects.FigureWidget

        Example:
            >>> widget = chart.to_widget()
            >>> display(widget)
        """
        return go.FigureWidget(self.fig)

    def show(self) -> None:
        """Display the chart.

        In Jupyter: displays inline
        In script: opens browser

        Example:
            >>> chart.show()
        """
        self.fig.show()

    def clear(self) -> None:
        """Clear all data from the chart.

        Example:
            >>> chart.clear()
        """
        self._timestamps.clear()
        for field in self._data:
            self._data[field].clear()

        # Update figure
        self._update_figure()

    def save(self, filename: str) -> None:
        """Save chart to HTML file.

        Args:
            filename: Output HTML filename

        Example:
            >>> chart.save("live_chart.html")
        """
        self.fig.write_html(filename)
        logger.info(f"Chart saved to {filename}")

    def __repr__(self) -> str:
        """String representation of chart."""
        return f"LiveChart(title='{self.title}', points={len(self._timestamps)})"


class LiveChartManager:
    """Manage multiple live charts for different symbols.

    Creates and updates multiple charts simultaneously.

    Example:
        >>> manager = LiveChartManager()
        >>> manager.add_symbol('AAPL', 'AAPL Live Price')
        >>> manager.add_symbol('0700.HK', 'Tencent Live Price')
        >>>
        >>> # Update all charts
        >>> async for tick in stream:
        ...     manager.update(tick)
    """

    def __init__(self) -> None:
        """Initialize chart manager."""
        self._charts: dict[str, LiveChart] = {}

    def add_symbol(
        self,
        symbol: str,
        title: Optional[str] = None,
        max_points: int = 100,
    ) -> LiveChart:
        """Add a chart for a symbol.

        Args:
            symbol: Trading symbol
            title: Chart title (defaults to symbol)
            max_points: Maximum points to display

        Returns:
            LiveChart instance

        Example:
            >>> chart = manager.add_symbol('AAPL', 'Apple Live Price')
        """
        if title is None:
            title = f"{symbol} Live Price"

        self._charts[symbol] = LiveChart(
            title=title,
            max_points=max_points,
        )
        self._charts[symbol].add_line(name='price', color='blue')

        return self._charts[symbol]

    def remove_symbol(self, symbol: str) -> None:
        """Remove chart for a symbol.

        Args:
            symbol: Trading symbol
        """
        if symbol in self._charts:
            del self._charts[symbol]

    def update(self, tick: TickData) -> None:
        """Update chart for a symbol with new tick.

        Args:
            tick: TickData object

        Example:
            >>> manager.update(tick)
        """
        if tick.symbol in self._charts:
            self._charts[tick.symbol].update(tick)

    def get_chart(self, symbol: str) -> Optional[LiveChart]:
        """Get chart for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            LiveChart or None
        """
        return self._charts.get(symbol)

    def show_all(self) -> None:
        """Display all charts.

        Example:
            >>> manager.show_all()
        """
        for chart in self._charts.values():
            chart.show()

    def clear_all(self) -> None:
        """Clear all charts.

        Example:
            >>> manager.clear_all()
        """
        for chart in self._charts.values():
            chart.clear()

    def __repr__(self) -> str:
        """String representation of manager."""
        return f"LiveChartManager(symbols={list(self._charts.keys())})"
