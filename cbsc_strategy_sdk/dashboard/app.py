"""
Main Dash application for strategy monitoring dashboard.

Provides StrategyDashboard class for creating interactive dashboards
embedded in Jupyter notebooks with real-time updates.
"""

from typing import Optional, List, Dict, Any
import pandas as pd

try:
    import dash
    from dash import html, dcc, Input, Output, State, callback_context
    import dash_bootstrap_components as dbc
    from dash.exceptions import PreventUpdate
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

from .theme import ThemeManager
from .layout import DashboardLayout
from .charts import ChartBuilders
from .metrics import MetricsDisplay
from .live import LiveUpdateComponent


class StrategyDashboard:
    """
    Interactive Dash dashboard for strategy monitoring.

    Embeds directly into Jupyter notebooks and provides real-time
    visualization of strategy performance, market data, and backtest results.
    """

    def __init__(
        self,
        title: str = "Strategy Dashboard",
        port: int = 8050,
        mode: str = 'inline',
        theme: str = 'dark',
        debug: bool = False,
    ):
        """
        Initialize StrategyDashboard.

        Args:
            title: Dashboard title
            port: Port number for Dash server
            mode: Dash mode ('inline', 'jupyterlab', or 'external')
            theme: Initial theme ('dark' or 'light')
            debug: Enable debug mode
        """
        if not DASH_AVAILABLE:
            raise ImportError(
                "Dash and dash-bootstrap-components are required. "
                "Install with: pip install dash dash-bootstrap-components"
            )

        self.title = title
        self.port = port
        self.mode = mode
        self.debug = debug

        # Initialize components
        self.theme_manager = ThemeManager(initial_theme=theme)
        self.layout_builder = DashboardLayout(theme_manager=self.theme_manager)
        self.chart_builder = ChartBuilders(theme_manager=self.theme_manager)

        # Create Dash app
        external_stylesheets = [self.theme_manager.get_stylesheet_url()]

        self.app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True,
        )

        # Store for data
        self._data_store: Dict[str, Any] = {}

        # Register layout and callbacks
        self._setup_layout()
        self._setup_callbacks()

        # Live update component (optional)
        self._live_component: Optional[LiveUpdateComponent] = None

    def _setup_layout(self) -> None:
        """Configure dashboard layout."""
        colors = self.theme_manager.get_colors()

        self.app.layout = dbc.Container([
            # Header
            self.layout_builder.header(
                title=self.title,
                subtitle="Real-time strategy monitoring and analysis",
            ),

            # Theme toggle
            html.Div(id='theme-container', style={'display': 'none'}),

            # Main content area
            dbc.Row([
                # Control panel
                dbc.Col([
                    html.Div(id='control-panel')
                ], width=3),

                # Charts area
                dbc.Col([
                    # Metric cards row
                    dbc.Row([
                        dbc.Col(html.Div(id='metric-card-1'), width=2),
                        dbc.Col(html.Div(id='metric-card-2'), width=2),
                        dbc.Col(html.Div(id='metric-card-3'), width=2),
                        dbc.Col(html.Div(id='metric-card-4'), width=2),
                        dbc.Col(html.Div(id='metric-card-5'), width=2),
                        dbc.Col(html.Div(id='metric-card-6'), width=2),
                    ], className="mb-4"),

                    # Main chart
                    html.Div(id='main-chart'),

                    # Secondary charts row
                    dbc.Row([
                        dbc.Col(html.Div(id='secondary-chart-1'), width=6),
                        dbc.Col(html.Div(id='secondary-chart-2'), width=6),
                    ], className="mt-4"),

                ], width=9),
            ]),

            # Store components for client-side data
            dcc.Store(id='data-store'),
            dcc.Store(id='theme-store', data=self.theme_manager.current_theme),

        ], fluid=True, style={'backgroundColor': colors['background']})

    def _setup_callbacks(self) -> None:
        """Register Dash callbacks for interactivity."""

        @self.app.callback(
            Output('theme-container', 'children'),
            Input('theme-toggle-btn', 'n_clicks'),
            State('theme-store', 'data'),
        )
        def toggle_theme(n_clicks, current_theme):
            """Toggle between dark and light themes."""
            if n_clicks is None:
                raise PreventUpdate

            # Toggle theme
            new_theme = self.theme_manager.toggle_theme()

            # Return new theme
            return new_theme

        @self.app.callback(
            [Output('metric-card-1', 'children'),
             Output('metric-card-2', 'children'),
             Output('metric-card-3', 'children'),
             Output('metric-card-4', 'children'),
             Output('metric-card-5', 'children'),
             Output('metric-card-6', 'children')],
            [Input('data-store', 'data')],
        )
        def update_metrics(data):
            """Update metric cards."""
            if data is None or 'returns' not in data:
                raise PreventUpdate

            # Create metrics display
            returns = pd.Series(data['returns'], index=pd.to_datetime(data['dates']))
            metrics_display = MetricsDisplay(returns=returns, theme_manager=self.theme_manager)

            cards = metrics_display.summary_cards()

            # Return 6 cards
            return cards[:6]

        @self.app.callback(
            Output('main-chart', 'children'),
            [Input('data-store', 'data')],
        )
        def update_main_chart(data):
            """Update main chart."""
            if data is None or 'price_data' not in data:
                # Return placeholder
                colors = self.theme_manager.get_colors()
                return html.Div("No data loaded", style={
                    'textAlign': 'center',
                    'padding': '50px',
                    'color': colors['text_secondary']
                })

            # Create chart
            df = pd.DataFrame(data['price_data'])
            df.set_index('timestamp', inplace=True)

            fig = self.chart_builder.candlestick_chart(df, title="Price Chart")

            return self.layout_builder.chart_panel(
                title="Price Analysis",
                figure_id='main-chart-graph',
            )

    def run(
        self,
        host: str = '127.0.0.1',
        port: Optional[int] = None,
        debug: Optional[bool] = None,
    ) -> None:
        """
        Start dashboard server.

        Args:
            host: Host address to bind to
            port: Port number (default: use self.port)
            debug: Enable debug mode (default: use self.debug)
        """
        port = port or self.port
        debug = debug if debug is not None else self.debug

        self.app.run_server(
            host=host,
            port=port,
            debug=debug,
            mode=self.mode,
        )

    def show(self) -> None:
        """Display dashboard in Jupyter notebook."""
        try:
            from IPython.display import IFrame, display
            display(IFrame(f'http://127.0.0.1:{self.port}', width='100%', height='800px'))
        except ImportError:
            print("IPython not available. Run dashboard.show() in Jupyter notebook.")

    def load_data(
        self,
        price_data: pd.DataFrame,
        returns: Optional[pd.Series] = None,
    ) -> None:
        """
        Load data into dashboard.

        Args:
            price_data: DataFrame with OHLCV data
            returns: Optional returns series for metrics
        """
        self._data_store['price_data'] = price_data.to_dict('records')

        if returns is not None:
            self._data_store['returns'] = returns.tolist()
            self._data_store['dates'] = returns.index.strftime('%Y-%m-%d').tolist()

    def load_backtest_results(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
    ) -> None:
        """
        Load backtest results for visualization.

        Args:
            returns: Strategy returns series
            benchmark_returns: Optional benchmark returns
        """
        self._data_store['returns'] = returns.tolist()
        self._data_store['dates'] = returns.index.strftime('%Y-%m-%d').tolist()

        if benchmark_returns is not None:
            self._data_store['benchmark_returns'] = benchmark_returns.tolist()

    def setup_live_updates(
        self,
        ws_url: str,
        symbols: List[str],
        update_interval: int = 1000,
    ) -> LiveUpdateComponent:
        """
        Setup live data streaming via WebSocket.

        Args:
            ws_url: WebSocket server URL
            symbols: List of symbols to subscribe to
            update_interval: Update interval in milliseconds

        Returns:
            LiveUpdateComponent instance
        """
        self._live_component = LiveUpdateComponent(
            update_interval=update_interval,
            theme_manager=self.theme_manager,
        )

        self._live_component.setup_websocket(ws_url, symbols)
        self._live_component.register_callbacks(self.app)

        return self._live_component

    def export_html(
        self,
        filename: str = "dashboard.html",
    ) -> None:
        """
        Export dashboard to HTML file.

        Args:
            filename: Output filename
        """
        try:
            from plotly.io import to_html
            # Implement HTML export
            print(f"Exporting to {filename}...")
            print("HTML export not yet fully implemented.")
        except ImportError:
            print("plotly is required for HTML export")

    def export_png(
        self,
        filename: str = "dashboard.png",
        width: int = 1920,
        height: int = 1080,
    ) -> None:
        """
        Export dashboard to PNG image.

        Args:
            filename: Output filename
            width: Image width in pixels
            height: Image height in pixels
        """
        try:
            # Requires kaleido package
            print(f"Exporting to {filename}...")
            print("PNG export requires kaleido: pip install kaleido")
        except Exception as e:
            print(f"PNG export failed: {e}")

    @property
    def app_instance(self) -> 'dash.Dash':
        """Get underlying Dash app instance."""
        return self.app

    @property
    def current_theme(self) -> str:
        """Get current theme name."""
        return self.theme_manager.current_theme

    def set_theme(self, theme: str) -> None:
        """
        Set dashboard theme.

        Args:
            theme: Theme name ('dark' or 'light')
        """
        self.theme_manager.set_theme(theme)


def create_dashboard(
    title: str = "Strategy Dashboard",
    theme: str = 'dark',
    port: int = 8050,
) -> StrategyDashboard:
    """
    Convenience function to create a StrategyDashboard.

    Args:
        title: Dashboard title
        theme: Initial theme
        port: Port number

    Returns:
        StrategyDashboard instance

    Example:
        >>> dashboard = create_dashboard(title="My Strategy")
        >>> dashboard.run()
    """
    return StrategyDashboard(
        title=title,
        theme=theme,
        port=port,
    )
