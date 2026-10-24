"""
Performance metrics display for Dash dashboard.

Provides MetricsDisplay class for creating comprehensive
performance analysis visualizations and tables.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np

try:
    from dash import html, dash_table
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

from .theme import ThemeManager
from .charts import ChartBuilders


class MetricsDisplay:
    """
    Display strategy performance metrics in Dash dashboard.

    Creates metric cards, detailed tables, and comparison charts
    for backtest results analysis.
    """

    def __init__(
        self,
        returns: Optional[pd.Series] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        """
        Initialize MetricsDisplay.

        Args:
            returns: Optional returns series for automatic metric calculation
            theme_manager: Optional ThemeManager for consistent styling
        """
        if not DASH_AVAILABLE:
            raise ImportError(
                "Dash is required for MetricsDisplay. "
                "Install with: pip install dash"
            )

        self.theme = theme_manager or ThemeManager()
        self.returns = returns
        self._chart_builder = ChartBuilders(theme_manager=self.theme)

        if returns is not None:
            self._metrics = self._calculate_metrics(returns)
        else:
            self._metrics = {}

    def _calculate_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate standard performance metrics.

        Args:
            returns: Returns series

        Returns:
            Dictionary of metric names to values
        """
        # Calculate cumulative returns
        cum_returns = (1 + returns).cumprod()

        # Calculate drawdown
        cummax = cum_returns.cummax()
        drawdown = (cum_returns - cummax) / cummax
        max_drawdown = drawdown.min()

        # Basic metrics
        total_return = cum_returns.iloc[-1] - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1

        # Risk metrics
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0

        # Win rate
        win_rate = (returns > 0).sum() / len(returns)

        # Other metrics
        mean_return = returns.mean()
        median_return = returns.median()

        return {
            'total_return': total_return * 100,
            'annual_return': annual_return * 100,
            'volatility': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'win_rate': win_rate * 100,
            'mean_return': mean_return * 100,
            'median_return': median_return * 100,
        }

    def summary_cards(self) -> List[dbc.Card]:
        """
        Create metric cards for key performance indicators.

        Returns:
            List of Dash Bootstrap Card components
        """
        if not self._metrics:
            return []

        colors = self.theme.get_colors()

        cards = []

        # Total Return Card
        cards.append(
            dbc.Card(
                [
                    dbc.CardBody([
                        html.H6("Total Return", className="text-muted mb-2"),
                        html.H3(
                            f"{self._metrics['total_return']:.2f}%",
                            style={
                                'color': colors['success']
                                if self._metrics['total_return'] > 0
                                else colors['danger']
                            }
                        ),
                    ])
                ],
                style=self.theme.get_card_style()
            )
        )

        # Annual Return Card
        cards.append(
            dbc.Card(
                [
                    dbc.CardBody([
                        html.H6("Annual Return", className="text-muted mb-2"),
                        html.H3(f"{self._metrics['annual_return']:.2f}%"),
                    ])
                ],
                style=self.theme.get_card_style()
            )
        )

        # Sharpe Ratio Card
        cards.append(
            dbc.Card(
                [
                    dbc.CardBody([
                        html.H6("Sharpe Ratio", className="text-muted mb-2"),
                        html.H3(f"{self._metrics['sharpe_ratio']:.2f}"),
                    ])
                ],
                style=self.theme.get_card_style()
            )
        )

        # Max Drawdown Card
        cards.append(
            dbc.Card(
                [
                    dbc.CardBody([
                        html.H6("Max Drawdown", className="text-muted mb-2"),
                        html.H3(
                            f"{self._metrics['max_drawdown']:.2f}%",
                            style={'color': colors['danger']}
                        ),
                    ])
                ],
                style=self.theme.get_card_style()
            )
        )

        # Win Rate Card
        cards.append(
            dbc.Card(
                [
                    dbc.CardBody([
                        html.H6("Win Rate", className="text-muted mb-2"),
                        html.H3(f"{self._metrics['win_rate']:.1f}%"),
                    ])
                ],
                style=self.theme.get_card_style()
            )
        )

        # Volatility Card
        cards.append(
            dbc.Card(
                [
                    dbc.CardBody([
                        html.H6("Volatility", className="text-muted mb-2"),
                        html.H3(f"{self._metrics['volatility']:.2f}%"),
                    ])
                ],
                style=self.theme.get_card_style()
            )
        )

        return cards

    def detailed_table(self) -> dash_table.DataTable:
        """
        Create detailed metrics table.

        Returns:
            Dash DataTable component with all metrics
        """
        if not self._metrics:
            raise ValueError("No metrics available. Provide returns series.")

        # Create display names and formats
        metric_info = {
            'total_return': ('Total Return', '{:.2f}%'),
            'annual_return': ('Annual Return', '{:.2f}%'),
            'volatility': ('Volatility (Ann.)', '{:.2f}%'),
            'sharpe_ratio': ('Sharpe Ratio', '{:.2f}'),
            'max_drawdown': ('Max Drawdown', '{:.2f}%'),
            'win_rate': ('Win Rate', '{:.1f}%'),
            'mean_return': ('Mean Return', '{:.2f}%'),
            'median_return': ('Median Return', '{:.2f}%'),
        }

        # Build table data
        table_data = []
        for key, (name, fmt) in metric_info.items():
            if key in self._metrics:
                table_data.append({
                    'Metric': name,
                    'Value': fmt.format(self._metrics[key])
                })

        df = pd.DataFrame(table_data)

        colors = self.theme.get_colors()

        return dash_table.DataTable(
            id='metrics-table',
            columns=[
                {'name': 'Metric', 'id': 'Metric'},
                {'name': 'Value', 'id': 'Value'}
            ],
            data=df.to_dict('records'),
            style_cell={
                'backgroundColor': colors['surface'],
                'color': colors['text'],
                'fontSize': '14px',
                'padding': '12px',
                'textAlign': 'left',
                'border': f'1px solid {colors["border"]}',
            },
            style_header={
                'backgroundColor': colors['primary'],
                'color': 'white',
                'fontWeight': 'bold',
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': colors['background'],
                }
            ],
        )

    def comparison_chart(
        self,
        benchmark_returns: pd.Series,
        title: str = "Performance Comparison"
    ) -> go.Figure:
        """
        Compare strategy performance with benchmark.

        Args:
            benchmark_returns: Benchmark returns series
            title: Chart title

        Returns:
            Plotly Figure with comparison charts
        """
        if self.returns is None:
            raise ValueError("No returns data available for comparison")

        # Calculate metrics for benchmark
        benchmark_metrics = self._calculate_metrics(benchmark_returns)

        # Create comparison table
        comparison_data = {
            'Metric': [
                'Total Return',
                'Annual Return',
                'Volatility',
                'Sharpe Ratio',
                'Max Drawdown',
            ],
            'Strategy': [
                f"{self._metrics['total_return']:.2f}%",
                f"{self._metrics['annual_return']:.2f}%",
                f"{self._metrics['volatility']:.2f}%",
                f"{self._metrics['sharpe_ratio']:.2f}",
                f"{self._metrics['max_drawdown']:.2f}%",
            ],
            'Benchmark': [
                f"{benchmark_metrics['total_return']:.2f}%",
                f"{benchmark_metrics['annual_return']:.2f}%",
                f"{benchmark_metrics['volatility']:.2f}%",
                f"{benchmark_metrics['sharpe_ratio']:.2f}",
                f"{benchmark_metrics['max_drawdown']:.2f}%",
            ],
        }

        df = pd.DataFrame(comparison_data)

        # Create figure with subplots
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.5, 0.5],
            subplot_titles=('Cumulative Returns', 'Metrics Comparison'),
            specs=[[{'type': 'scatter'}, {'type': 'table'}]]
        )

        # Add equity curve comparison
        colors = self.theme.get_colors()

        cum_strategy = (1 + self.returns).cumprod()
        cum_benchmark = (1 + benchmark_returns).cumprod()

        fig.add_trace(
            go.Scatter(
                x=cum_strategy.index,
                y=cum_strategy,
                mode='lines',
                name='Strategy',
                line=dict(color=colors['primary'], width=2),
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=cum_benchmark.index,
                y=cum_benchmark,
                mode='lines',
                name='Benchmark',
                line=dict(color=colors['secondary'], width=2, dash='dash'),
            ),
            row=1, col=1
        )

        # Add comparison table
        fig.add_trace(
            go.Table(
                header=dict(
                    values=list(df.columns),
                    fill_color=colors['primary'],
                    font=dict(color='white'),
                    align='left',
                ),
                cells=dict(
                    values=[df[col] for col in df.columns],
                    fill_color=[colors['surface'], colors['surface'], colors['surface']],
                    font=dict(color=colors['text']),
                    align='left',
                ),
            ),
            row=1, col=2
        )

        # Apply theme
        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=500,
            showlegend=True,
        )

        return fig

    def monthly_returns_heatmap(self, title: str = "Monthly Returns") -> go.Figure:
        """
        Create monthly returns heatmap.

        Returns:
            Plotly Figure with monthly returns heatmap
        """
        if self.returns is None:
            raise ValueError("No returns data available")

        # Calculate monthly returns
        monthly_returns = self.returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

        # Create year/month columns
        df = monthly_returns.to_frame('returns')
        df['year'] = df.index.year
        df['month'] = df.index.month

        # Pivot to get year x month matrix
        heatmap_data = df.pivot(index='year', columns='month', values='returns') * 100

        # Month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        colors = self.theme.get_colors()

        fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_data.values,
                x=month_names[:len(heatmap_data.columns)],
                y=heatmap_data.index,
                colorscale='RdYlGn',
                zmid=0,
                text=np.round(heatmap_data.values, 2),
                texttemplate='%{text:.2f}%',
                textfont={"size": 10},
                colorbar=dict(title="Return (%)"),
            )
        )

        fig.update_layout(
            template=template['layout'] if (template := self.theme.get_plotly_template()) else {},
            title=dict(text=title, x=0.5, xanchor='center'),
            xaxis_title="Month",
            yaxis_title="Year",
            paper_bgcolor=colors['background'],
            plot_bgcolor=colors['background'],
            font=dict(color=colors['text']),
        )

        return fig

    def rolling_metrics_chart(
        self,
        window: int = 252,
        title: str = "Rolling Metrics"
    ) -> go.Figure:
        """
        Create rolling Sharpe ratio and drawdown chart.

        Args:
            window: Rolling window size (default: 252 trading days)
            title: Chart title

        Returns:
            Plotly Figure with rolling metrics
        """
        if self.returns is None:
            raise ValueError("No returns data available")

        # Calculate rolling metrics
        rolling_returns = self.returns.rolling(window=window)
        rolling_sharpe = (
            rolling_returns.mean() * 252 /
            (rolling_returns.std() * np.sqrt(252))
        )

        # Calculate drawdown
        cum_returns = (1 + self.returns).cumprod()
        cummax = cum_returns.cummax()
        drawdown = (cum_returns - cummax) / cummax

        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Rolling Sharpe Ratio', 'Drawdown'),
        )

        colors = self.theme.get_colors()

        fig.add_trace(
            go.Scatter(
                x=rolling_sharpe.index,
                y=rolling_sharpe,
                mode='lines',
                name='Sharpe Ratio',
                line=dict(color=colors['primary'], width=2),
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown * 100,
                mode='lines',
                name='Drawdown',
                fill='tozeroy',
                line=dict(color=colors['danger'], width=1),
            ),
            row=2, col=1
        )

        template = self.theme.get_plotly_template()
        fig.update_layout(
            template=template['layout'],
            title=dict(text=title, x=0.5, xanchor='center'),
            height=600,
            hovermode='x unified',
        )

        return fig
