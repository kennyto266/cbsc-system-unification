"""
Live update component for real-time data streaming.

Provides LiveUpdateComponent class for WebSocket integration
and real-time chart updates in Dash applications.
"""

from typing import Optional, List, Callable, Dict, Any
from collections import deque
import asyncio
import json

try:
    import dash
    from dash import html, dcc, Input, Output, State
    import websockets
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

import pandas as pd
import numpy as np

from .theme import ThemeManager


class CircularBuffer:
    """Thread-safe circular buffer for streaming data."""

    def __init__(self, size: int = 1000):
        """
        Initialize circular buffer.

        Args:
            size: Maximum buffer size
        """
        self.buffer = deque(maxlen=size)
        self.size = size

    def add(self, data: Any) -> None:
        """Add data to buffer."""
        self.buffer.append(data)

    def get_data(self) -> List[Any]:
        """Get all data from buffer."""
        return list(self.buffer)

    def get_dataframe(self) -> pd.DataFrame:
        """Convert buffer data to DataFrame."""
        if not self.buffer:
            return pd.DataFrame()

        # Assume buffer contains dictionaries
        return pd.DataFrame(list(self.buffer))

    def clear(self) -> None:
        """Clear buffer."""
        self.buffer.clear()

    def __len__(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)


class LiveUpdateComponent:
    """
    Component for real-time chart updates via WebSocket.

    Integrates WebSocket data streaming with Dash callbacks
    for live market data and strategy performance monitoring.
    """

    def __init__(
        self,
        update_interval: int = 1000,
        buffer_size: int = 1000,
        theme_manager: Optional[ThemeManager] = None,
    ):
        """
        Initialize LiveUpdateComponent.

        Args:
            update_interval: Update interval in milliseconds
            buffer_size: Size of circular data buffer
            theme_manager: Optional ThemeManager for styling
        """
        if not WEBSOCKET_AVAILABLE:
            raise ImportError(
                "websockets is required for LiveUpdateComponent. "
                "Install with: pip install websockets"
            )

        self.update_interval = update_interval
        self.data_buffer = CircularBuffer(size=buffer_size)
        self.theme = theme_manager or ThemeManager()

        self._ws_url: Optional[str] = None
        self._symbols: List[str] = []
        self._is_running = False
        self._websocket = None
        self._callback: Optional[Callable] = None

    def setup_websocket(
        self,
        ws_url: str,
        symbols: List[str],
    ) -> None:
        """
        Connect to WebSocket for live data.

        Args:
            ws_url: WebSocket server URL (e.g., 'ws://localhost:8000/ws')
            symbols: List of symbols to subscribe to
        """
        self._ws_url = ws_url
        self._symbols = symbols

    async def _websocket_handler(self) -> None:
        """Handle WebSocket connection and data stream."""
        if not self._ws_url:
            raise ValueError("WebSocket URL not set. Call setup_websocket() first.")

        try:
            async with websockets.connect(self._ws_url) as websocket:
                self._websocket = websocket

                # Subscribe to symbols
                subscribe_msg = {
                    "action": "subscribe",
                    "symbols": self._symbols,
                }
                await websocket.send(json.dumps(subscribe_msg))

                # Listen for messages
                self._is_running = True
                while self._is_running:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)

                        # Add to buffer
                        self.data_buffer.add(data)

                        # Trigger callback if registered
                        if self._callback:
                            await self._callback(data)

                    except websockets.exceptions.ConnectionClosed:
                        break

        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self._is_running = False
            self._websocket = None

    def start_streaming(self) -> None:
        """Start WebSocket streaming in background."""
        if not self._ws_url:
            raise ValueError("WebSocket URL not set. Call setup_websocket() first.")

        # Run in background thread
        import threading

        def run_loop():
            asyncio.run(self._websocket_handler())

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

    def stop_streaming(self) -> None:
        """Stop WebSocket streaming."""
        self._is_running = False

    def set_callback(self, callback: Callable) -> None:
        """
        Set callback function for incoming data.

        Args:
            callback: Async function to call with each data update
        """
        self._callback = callback

    def get_latest_data(self) -> pd.DataFrame:
        """
        Get latest data as DataFrame.

        Returns:
            DataFrame with buffered data
        """
        return self.data_buffer.get_dataframe()

    def get_buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self.data_buffer)

    def clear_buffer(self) -> None:
        """Clear data buffer."""
        self.data_buffer.clear()

    def update_layout(self) -> html.Div:
        """
        Return Dash layout for this component.

        Returns:
            Dash html.Div with live update controls
        """
        colors = self.theme.get_colors()

        return html.Div([
            # Interval component for periodic updates
            dcc.Interval(
                id='live-update-interval',
                interval=self.update_interval,
                n_intervals=0,
            ),

            # Status indicator
            html.Div([
                html.Span(
                    "●",
                    style={
                        'color': colors['success'] if self._is_running else colors['danger'],
                        'fontSize': '20px',
                        'marginRight': '10px',
                    }
                ),
                html.Span(
                    "Live" if self._is_running else "Disconnected",
                    style={'color': colors['text']}
                ),
            ], className="d-flex align-items-center mb-3"),

            # Live chart
            dcc.Graph(
                id='live-update-chart',
                style={'height': '400px'}
            ),

            # Data info
            html.Div(
                f"Buffer: {self.get_buffer_size()} / {self.data_buffer.size} points",
                className="text-muted mt-2",
                style={'color': colors['text_secondary']}
            ),
        ])

    def register_callbacks(self, app: 'dash.Dash') -> None:
        """
        Register callbacks for periodic updates.

        Args:
            app: Dash application instance
        """
        @app.callback(
            Output('live-update-chart', 'figure'),
            Input('live-update-interval', 'n_intervals'),
        )
        def update_chart(n):
            """Update live chart with latest data."""
            df = self.get_latest_data()

            if df.empty:
                # Return empty figure
                from plotly.graph_objects import Figure
                colors = self.theme.get_colors()

                fig = Figure()
                fig.update_layout(
                    template=self.theme.get_plotly_template()['layout'],
                    title="Waiting for data...",
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=False, showticklabels=False),
                    paper_bgcolor=colors['background'],
                    plot_bgcolor=colors['background'],
                )
                return fig

            # Create line chart from latest data
            import plotly.graph_objects as go
            colors = self.theme.get_colors()

            fig = go.Figure()

            # Plot each symbol
            if 'close' in df.columns:
                if 'symbol' in df.columns:
                    for symbol in df['symbol'].unique():
                        symbol_data = df[df['symbol'] == symbol]
                        fig.add_trace(
                            go.Scatter(
                                x=symbol_data.index,
                                y=symbol_data['close'],
                                mode='lines',
                                name=symbol,
                                line=dict(color=colors['primary'], width=2),
                            )
                        )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=df['close'],
                            mode='lines',
                            name='Price',
                            line=dict(color=colors['primary'], width=2),
                        )
                    )

            fig.update_layout(
                template=self.theme.get_plotly_template()['layout'],
                title="Live Data",
                hovermode='x unified',
                height=400,
            )

            return fig

    def create_sample_live_data(
        self,
        num_points: int = 100,
        symbols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Create sample live data for testing.

        Args:
            num_points: Number of data points to generate
            symbols: List of symbol names

        Returns:
            DataFrame with sample OHLCV data
        """
        if symbols is None:
            symbols = ['AAPL']

        data = []
        for symbol in symbols:
            base_price = 150.0
            for i in range(num_points):
                price = base_price + np.random.randn() * 5
                data.append({
                    'timestamp': pd.Timestamp.now() - pd.Timedelta(minutes=num_points - i),
                    'symbol': symbol,
                    'open': price + np.random.randn(),
                    'high': price + abs(np.random.randn()) * 2,
                    'low': price - abs(np.random.randn()) * 2,
                    'close': price + np.random.randn(),
                    'volume': int(1000000 + np.random.randn() * 100000),
                })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)

        return df

    @property
    def is_running(self) -> bool:
        """Check if streaming is active."""
        return self._is_running

    @property
    def websocket_url(self) -> Optional[str]:
        """Get current WebSocket URL."""
        return self._ws_url

    @property
    def subscribed_symbols(self) -> List[str]:
        """Get subscribed symbols."""
        return self._symbols.copy()
