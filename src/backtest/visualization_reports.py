"""
Backtest Visualization Reports Generator
=======================================

Comprehensive visualization and reporting tools for backtesting results:
- Interactive charts with Plotly
- Performance dashboards
- Risk analysis visualizations
- Attribution charts
- Monte Carlo simulation plots
- HTML report generation
- Export capabilities

Author: CBSC Quant Team
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import warnings

# Visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.dates as mdates

# HTML templates
from jinja2 import Environment, FileSystemLoader, Template
import base64
import io

logger = logging.getLogger(__name__)


class ChartType(str, Enum):
    """Chart types"""
    EQUITY_CURVE = "equity_curve"
    DRAWDOWN = "drawdown"
    RETURNS_DISTRIBUTION = "returns_distribution"
    ROLLING_METRICS = "rolling_metrics"
    CORRELATION_HEATMAP = "correlation_heatmap"
    SCATTER_PLOT = "scatter_plot"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    VIOLIN_PLOT = "violin_plot"
    CANDLESTICK = "candlestick"
    OHLC = "ohlc"
    WATERFALL = "waterfall"
    TREE_MAP = "tree_map"
    SUNBURST = "sunburst"


class ReportFormat(str, Enum):
    """Report formats"""
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"
    INTERACTIVE_HTML = "interactive_html"


@dataclass
class VisualizationConfig:
    """Visualization configuration"""
    theme: str = "plotly_white"  # plotly_white, plotly_dark, ggplot2, seaborn
    color_palette: List[str] = field(default_factory=lambda: [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ])
    figure_size: Tuple[int, int] = (1200, 800)
    font_family: str = "Arial"
    font_size: int = 12

    # Chart settings
    show_legend: bool = True
    show_grid: bool = True
    show_zero_line: bool = True
    interactive: bool = True

    # Export settings
    image_format: str = "png"  # png, svg, pdf, html
    image_dpi: int = 300
    include_plotlyjs: bool = True


@dataclass
class ReportConfig:
    """Report generation configuration"""
    title: str = "Backtest Report"
    subtitle: str = ""
    author: str = "CBSC Quant Team"
    date: datetime = field(default_factory=datetime.now)

    # Content sections
    include_summary: bool = True
    include_performance: bool = True
    include_risk_analysis: bool = True
    include_attribution: bool = True
    include_monte_carlo: bool = True
    include_trades: bool = True

    # Format settings
    format: ReportFormat = ReportFormat.INTERACTIVE_HTML
    template_dir: str = "templates"
    output_dir: str = "reports"

    # Additional options
    include_raw_data: bool = False
    include_code: bool = False
    compress_output: bool = True


class BacktestVisualizer:
    """
    Advanced backtest visualization and reporting generator
    """

    def __init__(self, viz_config: Optional[VisualizationConfig] = None):
        """
        Initialize visualizer

        Args:
            viz_config: Visualization configuration
        """
        self.viz_config = viz_config or VisualizationConfig()
        self.figures: Dict[str, go.Figure] = {}
        self.charts_html: Dict[str, str] = {}

        logger.info("Backtest visualizer initialized")

    def create_equity_curve(
        self,
        portfolio_values: pd.Series,
        benchmark_values: Optional[pd.Series] = None,
        title: str = "Portfolio Equity Curve"
    ) -> go.Figure:
        """
        Create equity curve chart

        Args:
            portfolio_values: Portfolio value series
            benchmark_values: Optional benchmark values
            title: Chart title

        Returns:
            Plotly figure
        """
        fig = go.Figure()

        # Portfolio equity curve
        fig.add_trace(go.Scatter(
            x=portfolio_values.index,
            y=portfolio_values.values,
            mode='lines',
            name='Portfolio',
            line=dict(color=self.viz_config.color_palette[0], width=2),
            hovertemplate='Date: %{x}<br>Value: %{y:,.0f}<extra></extra>'
        ))

        # Benchmark if provided
        if benchmark_values is not None:
            # Align dates
            common_dates = portfolio_values.index.intersection(benchmark_values.index)
            portfolio_aligned = portfolio_values.loc[common_dates]
            benchmark_aligned = benchmark_values.loc[common_dates]

            # Normalize to start at same point
            portfolio_norm = portfolio_aligned / portfolio_aligned.iloc[0]
            benchmark_norm = benchmark_aligned / benchmark_aligned.iloc[0]

            fig.add_trace(go.Scatter(
                x=common_dates,
                y=benchmark_norm.values * portfolio_values.iloc[0],
                mode='lines',
                name='Benchmark',
                line=dict(color=self.viz_config.color_palette[1], width=2, dash='dash'),
                hovertemplate='Date: %{x}<br>Value: %{y:,.0f}<extra></extra>'
            ))

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Portfolio Value",
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            showlegend=self.viz_config.show_legend,
            hovermode='x unified'
        )

        self.figures['equity_curve'] = fig
        return fig

    def create_drawdown_chart(
        self,
        portfolio_values: pd.Series,
        title: str = "Portfolio Drawdown"
    ) -> go.Figure:
        """
        Create drawdown chart

        Args:
            portfolio_values: Portfolio value series
            title: Chart title

        Returns:
            Plotly figure
        """
        # Calculate drawdown
        cumulative = (1 + portfolio_values.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        fig = go.Figure()

        # Drawdown area
        fig.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values * 100,
            mode='lines',
            name='Drawdown',
            fill='tozeroy',
            line=dict(color='red', width=1),
            hovertemplate='Date: %{x}<br>Drawdown: %{y:.2f}%<extra></extra>'
        ))

        # Zero line
        fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.3)

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            showlegend=False,
            yaxis=dict(tickformat='.1f')
        )

        self.figures['drawdown'] = fig
        return fig

    def create_returns_distribution(
        self,
        returns: pd.Series,
        title: str = "Returns Distribution"
    ) -> go.Figure:
        """
        Create returns distribution chart

        Args:
            returns: Returns series
            title: Chart title

        Returns:
            Plotly figure
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Histogram', 'Box Plot', 'Q-Q Plot', 'Violin Plot'),
            specs=[[{"type": "scatter"}, {"type": "box"}],
                   [{"type": "scatter"}, {"type": "violin"}]]
        )

        # Remove NaN values
        clean_returns = returns.dropna()

        # Histogram
        fig.add_trace(
            go.Histogram(
                x=clean_returns.values,
                nbinsx=50,
                name='Returns',
                marker_color=self.viz_config.color_palette[0],
                opacity=0.7
            ),
            row=1, col=1
        )

        # Box plot
        fig.add_trace(
            go.Box(
                y=clean_returns.values,
                name='Returns',
                marker_color=self.viz_config.color_palette[1]
            ),
            row=1, col=2
        )

        # Q-Q plot
        from scipy import stats
        theoretical_quantiles = stats.norm.ppf(np.linspace(0.01, 0.99, len(clean_returns)))
        sample_quantiles = np.sort(clean_returns)

        fig.add_trace(
            go.Scatter(
                x=theoretical_quantiles,
                y=sample_quantiles,
                mode='markers',
                name='Q-Q Plot',
                marker=dict(color=self.viz_config.color_palette[2], size=4)
            ),
            row=2, col=1
        )

        # Add diagonal line to Q-Q plot
        min_val = min(theoretical_quantiles.min(), sample_quantiles.min())
        max_val = max(theoretical_quantiles.max(), sample_quantiles.max())
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode='lines',
                name='Reference',
                line=dict(color='black', dash='dash'),
                showlegend=False
            ),
            row=2, col=1
        )

        # Violin plot
        fig.add_trace(
            go.Violin(
                y=clean_returns.values,
                name='Returns',
                box_visible=True,
                meanline_visible=True,
                fillcolor=self.viz_config.color_palette[3],
                opacity=0.7
            ),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title_text=title,
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            showlegend=False
        )

        self.figures['returns_distribution'] = fig
        return fig

    def create_rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 252,
        title: str = "Rolling Performance Metrics"
    ) -> go.Figure:
        """
        Create rolling performance metrics chart

        Args:
            returns: Returns series
            window: Rolling window in days
            title: Chart title

        Returns:
            Plotly figure
        """
        # Calculate rolling metrics
        rolling_mean = returns.rolling(window=window).mean() * np.sqrt(252)
        rolling_std = returns.rolling(window=window).std() * np.sqrt(252)
        rolling_sharpe = rolling_mean / rolling_std
        rolling_sortino = rolling_mean / (
            returns[returns < 0].rolling(window=window).std() * np.sqrt(252)
        )

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Rolling Return', 'Rolling Volatility',
                          'Rolling Sharpe', 'Rolling Sortino'),
            vertical_spacing=0.1
        )

        # Rolling return
        fig.add_trace(
            go.Scatter(
                x=rolling_mean.index,
                y=rolling_mean.values * 100,
                mode='lines',
                name='Rolling Return',
                line=dict(color=self.viz_config.color_palette[0])
            ),
            row=1, col=1
        )

        # Rolling volatility
        fig.add_trace(
            go.Scatter(
                x=rolling_std.index,
                y=rolling_std.values * 100,
                mode='lines',
                name='Rolling Volatility',
                line=dict(color=self.viz_config.color_palette[1])
            ),
            row=1, col=2
        )

        # Rolling Sharpe
        fig.add_trace(
            go.Scatter(
                x=rolling_sharpe.index,
                y=rolling_sharpe.values,
                mode='lines',
                name='Rolling Sharpe',
                line=dict(color=self.viz_config.color_palette[2])
            ),
            row=2, col=1
        )

        # Rolling Sortino
        fig.add_trace(
            go.Scatter(
                x=rolling_sortino.index,
                y=rolling_sortino.values,
                mode='lines',
                name='Rolling Sortino',
                line=dict(color=self.viz_config.color_palette[3])
            ),
            row=2, col=2
        )

        # Update layout
        fig.update_layout(
            title_text=title,
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            height=800
        )

        # Update y-axes labels
        fig.update_yaxes(title_text="Return (%)", row=1, col=1)
        fig.update_yaxes(title_text="Volatility (%)", row=1, col=2)
        fig.update_yaxes(title_text="Sharpe Ratio", row=2, col=1)
        fig.update_yaxes(title_text="Sortino Ratio", row=2, col=2)

        self.figures['rolling_metrics'] = fig
        return fig

    def create_correlation_heatmap(
        self,
        returns: pd.DataFrame,
        title: str = "Asset Correlation Matrix"
    ) -> go.Figure:
        """
        Create correlation heatmap

        Args:
            returns: Returns DataFrame
            title: Chart title

        Returns:
            Plotly figure
        """
        # Calculate correlation matrix
        corr_matrix = returns.corr()

        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale='RdBu',
                zmid=0,
                text=np.round(corr_matrix.values, 2),
                texttemplate="%{text}",
                textfont={"size": 10},
                hovertemplate='Asset 1: %{x}<br>Asset 2: %{y}<br>Correlation: %{z:.3f}<extra></extra>'
            )
        )

        fig.update_layout(
            title=title,
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            width=800,
            height=800
        )

        self.figures['correlation_heatmap'] = fig
        return fig

    def create_performance_attribution(
        self,
        attribution_data: Dict[str, Dict[str, float]],
        title: str = "Performance Attribution"
    ) -> go.Figure:
        """
        Create performance attribution chart

        Args:
            attribution_data: Attribution data
            title: Chart title

        Returns:
            Plotly figure
        """
        # Prepare data
        categories = list(attribution_data.keys())
        allocation = [attribution_data[cat].get('allocation', 0) for cat in categories]
        selection = [attribution_data[cat].get('selection', 0) for cat in categories]
        interaction = [attribution_data[cat].get('interaction', 0) for cat in categories]

        fig = go.Figure()

        # Stacked bar chart
        fig.add_trace(go.Bar(
            name='Allocation',
            x=categories,
            y=allocation,
            marker_color=self.viz_config.color_palette[0]
        ))

        fig.add_trace(go.Bar(
            name='Selection',
            x=categories,
            y=selection,
            marker_color=self.viz_config.color_palette[1]
        ))

        if any(interaction):
            fig.add_trace(go.Bar(
                name='Interaction',
                x=categories,
                y=interaction,
                marker_color=self.viz_config.color_palette[2]
            ))

        fig.update_layout(
            title=title,
            xaxis_title='Category',
            yaxis_title='Contribution (%)',
            barmode='stack',
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            showlegend=True
        )

        self.figures['performance_attribution'] = fig
        return fig

    def create_monte_carlo_results(
        self,
        equity_curves: np.ndarray,
        confidence_levels: List[float] = [0.05, 0.25, 0.5, 0.75, 0.95],
        title: str = "Monte Carlo Simulation Results"
    ) -> go.Figure:
        """
        Create Monte Carlo simulation visualization

        Args:
            equity_curves: Monte Carlo equity curves
            confidence_levels: Confidence levels to display
            title: Chart title

        Returns:
            Plotly figure
        """
        fig = go.Figure()

        # Calculate percentiles
        percentiles = {}
        for level in confidence_levels:
            percentile = np.percentile(equity_curves, level * 100, axis=0)
            percentiles[level] = percentile

        # Sample some individual paths
        n_sample = min(100, equity_curves.shape[0])
        sample_indices = np.random.choice(equity_curves.shape[0], n_sample, replace=False)

        # Plot sample paths with low opacity
        for idx in sample_indices:
            fig.add_trace(go.Scatter(
                x=list(range(len(equity_curves[idx]))),
                y=equity_curves[idx],
                mode='lines',
                line=dict(width=0.5, color='lightblue'),
                opacity=0.1,
                showlegend=False,
                hoverinfo='skip'
            ))

        # Plot confidence bands
        colors = ['rgba(255,0,0,0.2)', 'rgba(255,165,0,0.2)', 'rgba(255,255,0,0.2)',
                   'rgba(0,255,0,0.2)', 'rgba(0,0,255,0.2)']

        for i, (level, color) in enumerate(zip(confidence_levels, colors)):
            upper_level = 1 - level
            lower_level = level

            # Upper percentile
            fig.add_trace(go.Scatter(
                x=list(range(len(percentiles[upper_level]))),
                y=percentiles[upper_level],
                mode='lines',
                line=dict(width=0),
                fillcolor=color,
                fill='tonexty' if i > 0 else None,
                name=f'{upper_level*100:.0f}% Percentile',
                showlegend=False
            ))

            # Lower percentile
            fig.add_trace(go.Scatter(
                x=list(range(len(percentiles[lower_level]))),
                y=percentiles[lower_level],
                mode='lines',
                line=dict(width=0),
                fillcolor=color,
                name=f'{lower_level*100:.0f}%-{upper_level*100:.0f}% Confidence',
                showlegend=True
            ))

        # Median
        median = np.median(equity_curves, axis=0)
        fig.add_trace(go.Scatter(
            x=list(range(len(median))),
            y=median,
            mode='lines',
            name='Median',
            line=dict(color='black', width=2),
            hovertemplate='Day: %{x}<br>Median: %{y:,.0f}<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            xaxis_title='Time Period',
            yaxis_title='Portfolio Value',
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            showlegend=True,
            hovermode='x unified'
        )

        self.figures['monte_carlo'] = fig
        return fig

    def create_dashboard(
        self,
        results: Dict[str, Any],
        title: str = "Backtest Dashboard"
    ) -> go.Figure:
        """
        Create comprehensive dashboard

        Args:
            results: Backtest results dictionary
            title: Dashboard title

        Returns:
            Plotly figure with subplots
        """
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=('Equity Curve', 'Drawdown', 'Returns Distribution',
                          'Rolling Metrics', 'Monthly Returns', 'Risk Metrics',
                          'Trade Distribution', 'Asset Allocation', 'Performance Summary'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}, {"type": "histogram"}],
                   [{"secondary_y": False}, {"secondary_y": False}, {"type": "table"}],
                   [{"type": "pie"}, {"type": "bar"}, {"type": "indicator"}]]
        )

        # This is a placeholder implementation
        # In practice, you would populate each subplot with actual data

        # Equity curve (placeholder)
        fig.add_trace(
            go.Scatter(x=[1, 2, 3], y=[100, 110, 120], name='Portfolio'),
            row=1, col=1
        )

        # Add more charts...

        fig.update_layout(
            title_text=title,
            template=self.viz_config.theme,
            font=dict(family=self.viz_config.font_family, size=self.viz_config.font_size),
            height=1200,
            showlegend=True
        )

        return fig

    def save_figure(
        self,
        fig_name: str,
        filepath: Optional[str] = None,
        format: str = "html"
    ) -> str:
        """
        Save figure to file

        Args:
            fig_name: Name of the figure
            filepath: Output filepath
            format: Output format

        Returns:
            Filepath of saved figure
        """
        if fig_name not in self.figures:
            raise ValueError(f"Figure {fig_name} not found")

        fig = self.figures[fig_name]

        if filepath is None:
            filepath = f"{fig_name}.{format}"

        if format == "html":
            fig.write_html(filepath, include_plotlyjs=self.viz_config.include_plotlyjs)
        elif format == "png":
            fig.write_image(filepath, engine="kaleido", width=self.viz_config.figure_size[0],
                           height=self.viz_config.figure_size[1], scale=2)
        elif format == "pdf":
            fig.write_image(filepath, engine="kaleido", format="pdf")
        elif format == "svg":
            fig.write_image(filepath, engine="kaleido", format="svg")

        logger.info(f"Figure {fig_name} saved to {filepath}")
        return filepath

    def get_figure_html(self, fig_name: str) -> str:
        """Get HTML representation of figure"""
        if fig_name not in self.figures:
            raise ValueError(f"Figure {fig_name} not found")

        fig = self.figures[fig_name]
        return fig.to_html(include_plotlyjs='cdn', div_id=f"chart_{fig_name}")


class ReportGenerator:
    """
    Advanced report generator with multiple output formats
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """
        Initialize report generator

        Args:
            config: Report configuration
        """
        self.config = config or ReportConfig()
        self.template_env = None

        logger.info("Report generator initialized")

    def generate_html_report(
        self,
        results: Dict[str, Any],
        figures: Dict[str, go.Figure],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate HTML report

        Args:
            results: Backtest results
            figures: Visualization figures
            output_path: Output filepath

        Returns:
            HTML report content
        """
        # Create HTML template
        template = self._get_html_template()

        # Convert figures to HTML
        figures_html = {}
        for name, fig in figures.items():
            figures_html[name] = fig.to_html(include_plotlyjs='cdn', div_id=f"chart_{name}")

        # Prepare metrics
        metrics = self._prepare_metrics_summary(results)

        # Generate HTML content
        html_content = template.render(
            title=self.config.title,
            subtitle=self.config.subtitle,
            author=self.config.author,
            date=self.config.date.strftime("%Y-%m-%d"),
            results=results,
            figures=figures_html,
            metrics=metrics,
            config=self.config
        )

        # Save to file if path provided
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML report saved to {output_path}")

        return html_content

    def generate_pdf_report(
        self,
        results: Dict[str, Any],
        figures: Dict[str, go.Figure],
        output_path: str
    ) -> None:
        """
        Generate PDF report

        Args:
            results: Backtest results
            figures: Visualization figures
            output_path: Output filepath
        """
        try:
            with PdfPages(output_path) as pdf:
                # Add title page
                fig, ax = plt.subplots(figsize=(8, 11))
                ax.text(0.5, 0.9, self.config.title, ha='center', fontsize=24, weight='bold')
                ax.text(0.5, 0.85, self.config.subtitle, ha='center', fontsize=18)
                ax.text(0.5, 0.8, f"Generated: {self.config.date.strftime('%Y-%m-%d')}",
                       ha='center', fontsize=14)
                ax.text(0.5, 0.75, f"Author: {self.config.author}", ha='center', fontsize=12)
                ax.axis('off')
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

                # Add figures
                for name, fig in figures.items():
                    # Convert Plotly figure to matplotlib
                    fig_matplotlib = self._plotly_to_matplotlib(fig)
                    pdf.savefig(fig_matplotlib, bbox_inches='tight')
                    plt.close(fig_matplotlib)

            logger.info(f"PDF report saved to {output_path}")

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise

    def generate_excel_report(
        self,
        results: Dict[str, Any],
        output_path: str
    ) -> None:
        """
        Generate Excel report

        Args:
            results: Backtest results
            output_path: Output filepath
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = self._prepare_summary_dataframe(results)
                summary_data.to_excel(writer, sheet_name='Summary', index=False)

                # Performance metrics sheet
                if 'performance_metrics' in results:
                    metrics_df = pd.DataFrame([results['performance_metrics']])
                    metrics_df.T.to_excel(writer, sheet_name='Performance Metrics')

                # Trades sheet
                if 'trades' in results:
                    trades_df = pd.DataFrame(results['trades'])
                    trades_df.to_excel(writer, sheet_name='Trades', index=False)

                # Detailed results sheet
                if 'detailed_results' in results:
                    detailed_df = pd.DataFrame(results['detailed_results'])
                    detailed_df.to_excel(writer, sheet_name='Detailed Results')

            logger.info(f"Excel report saved to {output_path}")

        except Exception as e:
            logger.error(f"Failed to generate Excel report: {e}")
            raise

    def _get_html_template(self) -> Template:
        """Get HTML template"""
        template_str = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>{{ title }}</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                    color: #333;
                }
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #eee;
                }
                .section {
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }
                .metric-card {
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .metric-value {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }
                .metric-label {
                    font-size: 14px;
                    color: #7f8c8d;
                }
                .chart-container {
                    margin: 30px 0;
                    text-align: center;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background-color: #f2f2f2;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{{ title }}</h1>
                {% if subtitle %}<h2>{{ subtitle }}</h2>{% endif %}
                <p>Generated: {{ date }} | Author: {{ author }}</p>
            </div>

            {% if include_summary %}
            <div class="section">
                <h2>Performance Summary</h2>
                <div class="metrics-grid">
                    {% for metric, value in metrics.items() %}
                    <div class="metric-card">
                        <div class="metric-value">{{ value }}</div>
                        <div class="metric-label">{{ metric }}</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if figures %}
            <div class="section">
                <h2>Visualizations</h2>
                {% for fig_name, fig_html in figures.items() %}
                <div class="chart-container">
                    <h3>{{ fig_name|title }}</h3>
                    {{ fig_html|safe }}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <div class="section">
                <h2>Raw Results</h2>
                <pre>{{ results|pprint }}</pre>
            </div>
        </body>
        </html>
        """
        return Template(template_str)

    def _prepare_metrics_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Prepare metrics summary for report"""
        metrics = {}

        # Basic metrics
        if 'total_return' in results:
            metrics['Total Return'] = f"{results['total_return']:.2%}"
        if 'sharpe_ratio' in results:
            metrics['Sharpe Ratio'] = f"{results['sharpe_ratio']:.2f}"
        if 'max_drawdown' in results:
            metrics['Max Drawdown'] = f"{results['max_drawdown']:.2%}"
        if 'volatility' in results:
            metrics['Volatility'] = f"{results['volatility']:.2%}"

        # Add more metrics as needed
        return metrics

    def _prepare_summary_dataframe(self, results: Dict[str, Any]) -> pd.DataFrame:
        """Prepare summary DataFrame for Excel report"""
        summary_data = {
            'Metric': [],
            'Value': []
        }

        for key, value in results.items():
            if isinstance(value, (int, float)):
                summary_data['Metric'].append(key)
                summary_data['Value'].append(value)

        return pd.DataFrame(summary_data)

    def _plotly_to_matplotlib(self, fig: go.Figure) -> plt.Figure:
        """Convert Plotly figure to matplotlib"""
        # This is a simplified conversion
        # In practice, you'd use more sophisticated conversion
        matplotlib_fig, ax = plt.subplots(figsize=(12, 8))

        # Basic line chart conversion (placeholder)
        ax.plot([1, 2, 3], [1, 2, 3])
        ax.set_title('Chart')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')

        return matplotlib_fig


# Utility functions
def create_visualization_config(
    theme: str = "plotly_white",
    **kwargs
) -> VisualizationConfig:
    """Create visualization configuration"""
    config = {
        'theme': theme,
        'interactive': True,
        'show_legend': True
    }

    config.update(kwargs)
    return VisualizationConfig(**config)


def create_report_config(
    format: ReportFormat = ReportFormat.INTERACTIVE_HTML,
    **kwargs
) -> ReportConfig:
    """Create report configuration"""
    config = {
        'format': format,
        'include_summary': True,
        'include_performance': True,
        'include_risk_analysis': True
    }

    config.update(kwargs)
    return ReportConfig(**config)


__all__ = [
    'BacktestVisualizer',
    'ReportGenerator',
    'VisualizationConfig',
    'ReportConfig',
    'ChartType',
    'ReportFormat',
    'create_visualization_config',
    'create_report_config'
]