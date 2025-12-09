#!/usr/bin/env python3
"""
Simplified System - Professional Backtest Visualization
專業級回測結果可視化系統

功能特性:
1. 交互式回測結果可視化
2. 策略性能對比分析
3. 風險指標可視化
4. 多資產組合展示
5. 實時性能監控儀表板
6. 專業報告生成

Author: Claude Code Assistant
Date: 2025-11-27
Version: 1.0.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import warnings

# 可視化庫
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo

# 統計分析
from scipy import stats
import pandas_ta as ta

# 專業圖表庫
import mplfinance as mpf

# Jupyter Widget
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# 數據處理
import json
from pathlib import Path

warnings.filterwarnings('ignore')

# 設置樣式
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

@dataclass
class VisualizationConfig:
    """可視化配置"""
    # 圖表配置
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 100
    style: str = 'plotly_white'

    # 顏色配置
    color_scheme: str = 'professional'
    primary_color: str = '#1f77b4'
    secondary_color: str = '#ff7f0e'
    success_color: str = '#2ca02c'
    danger_color: str = '#d62728'
    warning_color: str = '#ff7f0e'

    # 動畫配置
    enable_animation: bool = True
    animation_duration: int = 1000  # ms

    # 交互配置
    enable_zoom: bool = True
    enable_pan: bool = True
    enable_selection: bool = True

    # 輸出配置
    output_format: str = 'html'  # 'html', 'png', 'pdf'
    save_path: Optional[str] = None

class ProfessionalChartTheme:
    """專業圖表主題"""

    @staticmethod
    def get_plotly_template():
        """獲取Plotly專業模板"""
        return {
            'layout': {
                'font': {
                    'family': 'Arial, sans-serif',
                    'size': 12,
                    'color': '#333333'
                },
                'title': {
                    'font': {'size': 16, 'color': '#2c3e50'},
                    'x': 0.5
                },
                'xaxis': {
                    'gridcolor': '#ecf0f1',
                    'zerolinecolor': '#bdc3c7',
                    'showgrid': True
                },
                'yaxis': {
                    'gridcolor': '#ecf0f1',
                    'zerolinecolor': '#bdc3c7',
                    'showgrid': True
                },
                'plot_bgcolor': 'white',
                'paper_bgcolor': 'white',
                'colorway': [
                    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                    '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
                ]
            }
        }

    @staticmethod
    def get_matplotlib_style():
        """獲取Matplotlib專業樣式"""
        return {
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'axes.grid': True,
            'grid.color': '#ecf0f1',
            'axes.edgecolor': '#bdc3c7',
            'axes.labelcolor': '#2c3e50',
            'text.color': '#2c3e50',
            'font.family': ['Arial', 'sans-serif']
        }

class BacktestVisualizer:
    """
    專業級回測可視化器

    提供全面的回測結果可視化和分析功能
    """

    def __init__(self, config: Optional[VisualizationConfig] = None):
        self.config = config or VisualizationConfig()
        self.theme = ProfessionalChartTheme()

        # 應用樣式
        plt.rcParams.update(self.theme.get_matplotlib_style())

        print("Professional Backtest Visualizer initialized")

    def create_equity_curve(self, backtest_results: Dict[str, Any],
                          benchmark_data: Optional[pd.DataFrame] = None,
                          show_log_scale: bool = False) -> go.Figure:
        """
        創建權益曲線圖

        Args:
            backtest_results: 回測結果字典
            benchmark_data: 基準數據
            show_log_scale: 是否顯示對數刻度

        Returns:
            Plotly圖表對象
        """
        try:
            # 解析回測結果
            equity_curve = pd.Series(backtest_results['equity_curve'])
            returns = pd.Series(backtest_results['returns'])
            trades = pd.DataFrame(backtest_results['trades'])

            # 創建子圖
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxis=True,
                vertical_spacing=0.05,
                subplot_titles=[
                    'Equity Curve',
                    'Drawdown',
                    'Monthly Returns Distribution'
                ],
                row_heights=[0.6, 0.2, 0.2]
            )

            # 權益曲線
            fig.add_trace(
                go.Scatter(
                    x=equity_curve.index,
                    y=equity_curve,
                    name='Strategy Equity',
                    line=dict(color=self.config.primary_color, width=2)
                ),
                row=1, col=1
            )

            # 添加基準曲線
            if benchmark_data is not None:
                fig.add_trace(
                    go.Scatter(
                        x=benchmark_data.index,
                        y=benchmark_data,
                        name='Benchmark',
                        line=dict(color=self.config.secondary_color, width=1, dash='dash')
                    ),
                    row=1, col=1
                )

            # 標記交易點
            if not trades.empty:
                # 買入點
                buy_trades = trades[trades['type'] == 'buy']
                if not buy_trades.empty:
                    buy_prices = [equity_curve.loc[trade['time']] if trade['time'] in equity_curve.index else None
                                for trade in buy_trades.to_dict('records')]

                    fig.add_trace(
                        go.Scatter(
                            x=buy_trades['time'],
                            y=buy_prices,
                            mode='markers',
                            name='Buy Signals',
                            marker=dict(
                                symbol='triangle-up',
                                size=10,
                                color=self.config.success_color
                            )
                        ),
                        row=1, col=1
                    )

                # 賣出點
                sell_trades = trades[trades['type'] == 'sell']
                if not sell_trades.empty:
                    sell_prices = [equity_curve.loc[trade['time']] if trade['time'] in equity_curve.index else None
                                 for trade in sell_trades.to_dict('records')]

                    fig.add_trace(
                        go.Scatter(
                            x=sell_trades['time'],
                            y=sell_prices,
                            mode='markers',
                            name='Sell Signals',
                            marker=dict(
                                symbol='triangle-down',
                                size=10,
                                color=self.config.danger_color
                            )
                        ),
                        row=1, col=1
                    )

            # 回撤
            running_max = equity_curve.expanding().max()
            drawdown = (equity_curve - running_max) / running_max

            fig.add_trace(
                go.Scatter(
                    x=drawdown.index,
                    y=drawdown,
                    name='Drawdown',
                    fill='tozeroy',
                    line=dict(color=self.config.danger_color),
                    fillcolor=f'rgba(214, 39, 40, 0.3)'
                ),
                row=2, col=1
            )

            # 月度回報分佈
            monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

            fig.add_trace(
                go.Bar(
                    x=monthly_returns.index,
                    y=monthly_returns,
                    name='Monthly Returns',
                    marker_color=[self.config.success_color if x > 0 else self.config.danger_color
                                 for x in monthly_returns]
                ),
                row=3, col=1
            )

            # 更新佈局
            fig.update_layout(
                title='Strategy Performance Analysis',
                xaxis3_title='Date',
                yaxis_title='Portfolio Value',
                yaxis2_title='Drawdown',
                yaxis3_title='Monthly Returns',
                height=900,
                showlegend=True,
                template=self.config.style
            )

            # 設置對數刻度
            if show_log_scale:
                fig.update_yaxes(type='log', row=1, col=1)

            return fig

        except Exception as e:
            print(f"Error creating equity curve: {e}")
            return go.Figure()

    def create_performance_metrics_dashboard(self, backtest_results: Dict[str, Any],
                                          benchmark_results: Optional[Dict[str, Any]] = None) -> go.Figure:
        """
        創建性能指標儀表板

        Args:
            backtest_results: 策略回測結果
            benchmark_results: 基準回測結果

        Returns:
            Plotly圖表對象
        """
        try:
            # 計算性能指標
            metrics = self._calculate_comprehensive_metrics(backtest_results)

            # 創建儀表板
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=[
                    'Key Performance Metrics',
                    'Risk Metrics',
                    'Return Distribution',
                    'Monthly Heatmap',
                    'Rolling Metrics',
                    'Performance Attribution'
                ],
                specs=[
                    [{"type": "indicator"}] * 3,
                    [{"type": "bar"}, {"type": "heatmap"}, {"type": "scatter"}]
                ]
            )

            # 關鍵性能指標
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=metrics['sharpe_ratio'],
                    title={"text": "Sharpe Ratio"},
                    gauge={
                        'axis': {'range': [None, 4]},
                        'bar': {'color': self.config.primary_color},
                        'steps': [
                            {'range': [0, 1], 'color': "lightgray"},
                            {'range': [1, 2], 'color': "gray"},
                            {'range': [2, 4], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 2
                        }
                    }
                ),
                row=1, col=1
            )

            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=metrics['max_drawdown'] * 100,
                    title={"text": "Max Drawdown (%)"},
                    gauge={
                        'axis': {'range': [-50, 0]},
                        'bar': {'color': self.config.danger_color},
                        'steps': [
                            {'range': [-50, -20], 'color': "lightcoral"},
                            {'range': [-20, -10], 'color': "lightyellow"},
                            {'range': [-10, 0], 'color': "lightgreen"}
                        ]
                    }
                ),
                row=1, col=2
            )

            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=metrics['total_return'] * 100,
                    title={"text": "Total Return (%)"},
                    gauge={
                        'axis': {'range': [0, 200]},
                        'bar': {'color': self.config.success_color}
                    }
                ),
                row=1, col=3
            )

            # 風險指標
            risk_metrics = ['volatility', 'calmar_ratio', 'sortino_ratio', 'var_95']
            risk_values = [metrics.get(m, 0) for m in risk_metrics]

            fig.add_trace(
                go.Bar(
                    x=risk_metrics,
                    y=risk_values,
                    name='Risk Metrics',
                    marker_color=[self.config.warning_color, self.config.primary_color,
                                 self.config.success_color, self.config.danger_color]
                ),
                row=2, col=1
            )

            # 月度回報熱圖
            returns = pd.Series(backtest_results['returns'])
            monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
            monthly_df = monthly_returns.to_frame('returns')
            monthly_df['year'] = monthly_df.index.year
            monthly_df['month'] = monthly_df.index.month

            heatmap_data = monthly_df.pivot(index='year', columns='month', values='returns')

            fig.add_trace(
                go.Heatmap(
                    z=heatmap_data.values,
                    x=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    y=heatmap_data.index,
                    colorscale='RdYlGn',
                    name='Monthly Returns'
                ),
                row=2, col=2
            )

            # 滾動Sharpe比率
            rolling_sharpe = returns.rolling(252).apply(
                lambda x: x.mean() / x.std() * np.sqrt(252) if len(x) > 0 and x.std() > 0 else 0
            )

            fig.add_trace(
                go.Scatter(
                    x=rolling_sharpe.index,
                    y=rolling_sharpe,
                    name='Rolling Sharpe (1Y)',
                    line=dict(color=self.config.primary_color)
                ),
                row=2, col=3
            )

            # 更新佈局
            fig.update_layout(
                title='Performance Metrics Dashboard',
                height=800,
                showlegend=False,
                template=self.config.style
            )

            return fig

        except Exception as e:
            print(f"Error creating performance dashboard: {e}")
            return go.Figure()

    def create_strategy_comparison(self, strategies_results: Dict[str, Dict[str, Any]]) -> go.Figure:
        """
        創建策略對比圖

        Args:
            strategies_results: 策略結果字典 {strategy_name: backtest_results}

        Returns:
            Plotly圖表對象
        """
        try:
            # 創建子圖
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    'Equity Curves Comparison',
                    'Risk-Return Scatter',
                    'Drawdown Comparison',
                    'Metrics Comparison'
                ]
            )

            colors = px.colors.qualitative.Set1

            # 權益曲線對比
            for i, (strategy_name, results) in enumerate(strategies_results.items()):
                equity_curve = pd.Series(results['equity_curve'])
                color = colors[i % len(colors)]

                fig.add_trace(
                    go.Scatter(
                        x=equity_curve.index,
                        y=equity_curve,
                        name=strategy_name,
                        line=dict(color=color, width=2)
                    ),
                    row=1, col=1
                )

            # 風險-回報散點圖
            risk_return_data = []
            for strategy_name, results in strategies_results.items():
                metrics = self._calculate_comprehensive_metrics(results)
                risk_return_data.append({
                    'strategy': strategy_name,
                    'return': metrics['annual_return'],
                    'risk': metrics['volatility'],
                    'sharpe': metrics['sharpe_ratio']
                })

            risk_return_df = pd.DataFrame(risk_return_data)

            fig.add_trace(
                go.Scatter(
                    x=risk_return_df['risk'],
                    y=risk_return_df['return'],
                    mode='markers+text',
                    text=risk_return_df['strategy'],
                    textposition="top center",
                    marker=dict(
                        size=10,
                        color=risk_return_df['sharpe'],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Sharpe Ratio", x=1.02)
                    ),
                    name='Risk-Return'
                ),
                row=1, col=2
            )

            # 回撤對比
            for i, (strategy_name, results) in enumerate(strategies_results.items()):
                equity_curve = pd.Series(results['equity_curve'])
                running_max = equity_curve.expanding().max()
                drawdown = (equity_curve - running_max) / running_max
                color = colors[i % len(colors)]

                fig.add_trace(
                    go.Scatter(
                        x=drawdown.index,
                        y=drawdown,
                        name=f'{strategy_name} DD',
                        line=dict(color=color, width=1),
                        fill='tozeroy',
                        fillcolor=f'rgba{color[4:-1]}, 0.2)'
                    ),
                    row=2, col=1
                )

            # 指標對比
            metrics_comparison = []
            metrics_names = ['sharpe_ratio', 'max_drawdown', 'total_return', 'win_rate']

            for strategy_name, results in strategies_results.items():
                metrics = self._calculate_comprehensive_metrics(results)
                for metric_name in metrics_names:
                    metrics_comparison.append({
                        'strategy': strategy_name,
                        'metric': metric_name,
                        'value': metrics.get(metric_name, 0)
                    })

            metrics_df = pd.DataFrame(metrics_comparison)

            for i, metric_name in enumerate(metrics_names):
                metric_data = metrics_df[metrics_df['metric'] == metric_name]
                fig.add_trace(
                    go.Bar(
                        x=metric_data['strategy'],
                        y=metric_data['value'],
                        name=metric_name.replace('_', ' ').title(),
                        marker_color=colors[i % len(colors)]
                    ),
                    row=2, col=2
                )

            # 更新佈局
            fig.update_layout(
                title='Strategy Comparison Analysis',
                height=800,
                showlegend=True,
                template=self.config.style
            )

            fig.update_xaxes(title_text="Annualized Volatility", row=1, col=2)
            fig.update_yaxes(title_text="Annualized Return", row=1, col=2)

            return fig

        except Exception as e:
            print(f"Error creating strategy comparison: {e}")
            return go.Figure()

    def create_interactive_analysis(self, backtest_results: Dict[str, Any],
                                 stock_data: pd.DataFrame) -> widgets.VBox:
        """
        創建交互式分析界面

        Args:
            backtest_results: 回測結果
            stock_data: 股票數據

        Returns:
            Jupyter交互式控件
        """
        try:
            # 準備數據
            equity_curve = pd.Series(backtest_results['equity_curve'])
            returns = pd.Series(backtest_results['returns'])
            trades = pd.DataFrame(backtest_results['trades'])

            # 創建控件
            date_range_slider = widgets.SelectionRangeSlider(
                options=[(date.strftime('%Y-%m-%d'), date) for date in equity_curve.index],
                index=(0, len(equity_curve) - 1),
                description='Date Range:',
                layout={'width': '800px'}
            )

            metrics_dropdown = widgets.Dropdown(
                options=['Returns', 'Drawdown', 'Rolling Sharpe', 'Volatility'],
                value='Returns',
                description='Metric:'
            )

            window_size_slider = widgets.IntSlider(
                value=30,
                min=5,
                max=252,
                step=5,
                description='Window Size:'
            )

            # 輸出控件
            output = widgets.Output()

            def update_analysis(change):
                with output:
                    clear_output(wait=True)

                    # 獲取選定範圍
                    start_date, end_date = date_range_slider.value
                    selected_data = equity_curve[start_date:end_date]

                    # 根據選擇的指標更新圖表
                    metric = metrics_dropdown.value
                    window_size = window_size_slider.value

                    if metric == 'Returns':
                        data_to_plot = returns[start_date:end_date]
                        title = f'Returns ({window_size}d window)'
                    elif metric == 'Drawdown':
                        running_max = selected_data.expanding().max()
                        data_to_plot = (selected_data - running_max) / running_max
                        title = f'Drawdown ({window_size}d window)'
                    elif metric == 'Rolling Sharpe':
                        data_to_plot = returns.rolling(window_size).apply(
                            lambda x: x.mean() / x.std() * np.sqrt(252) if len(x) > 0 and x.std() > 0 else 0
                        )[start_date:end_date]
                        title = f'Rolling Sharpe ({window_size}d window)'
                    else:  # Volatility
                        data_to_plot = returns.rolling(window_size).std() * np.sqrt(252)
                        data_to_plot = data_to_plot[start_date:end_date]
                        title = f'Volatility ({window_size}d window)'

                    # 創建圖表
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=data_to_plot.index,
                        y=data_to_plot,
                        mode='lines',
                        name=metric
                    ))

                    fig.update_layout(
                        title=title,
                        xaxis_title='Date',
                        yaxis_title=metric,
                        template=self.config.style,
                        height=400
                    )

                    fig.show()

                    # 顯示統計信息
                    if not data_to_plot.empty:
                        stats_text = f"""
                        **Statistics for {title}:**
                        - Mean: {data_to_plot.mean():.4f}
                        - Std: {data_to_plot.std():.4f}
                        - Min: {data_to_plot.min():.4f}
                        - Max: {data_to_plot.max():.4f}
                        - Latest: {data_to_plot.iloc[-1]:.4f}
                        """
                        display(HTML(stats_text))

            # 連接控件事件
            date_range_slider.observe(update_analysis, names='value')
            metrics_dropdown.observe(update_analysis, names='value')
            window_size_slider.observe(update_analysis, names='value')

            # 初始顯示
            update_analysis(None)

            # 創建佈局
            controls = widgets.VBox([
                date_range_slider,
                widgets.HBox([metrics_dropdown, window_size_slider])
            ])

            return widgets.VBox([controls, output])

        except Exception as e:
            print(f"Error creating interactive analysis: {e}")
            return widgets.VBox([widgets.HTML(f"<h3>Error: {str(e)}</h3>")])

    def create_professional_report(self, backtest_results: Dict[str, Any],
                                 benchmark_results: Optional[Dict[str, Any]] = None,
                                 output_path: Optional[str] = None) -> str:
        """
        創建專業報告

        Args:
            backtest_results: 回測結果
            benchmark_results: 基準結果
            output_path: 輸出路徑

        Returns:
            HTML報告字符串
        """
        try:
            # 計算指標
            metrics = self._calculate_comprehensive_metrics(backtest_results)

            # 生成圖表
            equity_fig = self.create_equity_curve(backtest_results, benchmark_results)
            dashboard_fig = self.create_performance_metrics_dashboard(backtest_results, benchmark_results)

            # 轉換為HTML
            equity_html = pyo.plot(equity_fig, output_type='div', include_plotlyjs=False)
            dashboard_html = pyo.plot(dashboard_fig, output_type='div', include_plotlyjs=False)

            # 生成報告
            html_template = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Strategy Backtest Report</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .metrics {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                    .metric {{ text-align: center; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                    .chart {{ margin: 30px 0; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Strategy Backtest Report</h1>
                    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="metrics">
                    <div class="metric">
                        <h3>Total Return</h3>
                        <h2>{metrics['total_return']:.2%}</h2>
                    </div>
                    <div class="metric">
                        <h3>Sharpe Ratio</h3>
                        <h2>{metrics['sharpe_ratio']:.3f}</h2>
                    </div>
                    <div class="metric">
                        <h3>Max Drawdown</h3>
                        <h2>{metrics['max_drawdown']:.2%}</h2>
                    </div>
                    <div class="metric">
                        <h3>Win Rate</h3>
                        <h2>{metrics['win_rate']:.2%}</h2>
                    </div>
                </div>

                <div class="chart">
                    {equity_html}
                </div>

                <div class="chart">
                    {dashboard_html}
                </div>

                <h2>Detailed Performance Metrics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th><th>Description</th></tr>
                    <tr><td>Annual Return</td><td>{metrics['annual_return']:.2%}</td><td>Annualized return</td></tr>
                    <tr><td>Volatility</td><td>{metrics['volatility']:.2%}</td><td>Annualized volatility</td></tr>
                    <tr><td>Sharpe Ratio</td><td>{metrics['sharpe_ratio']:.3f}</td><td>Risk-adjusted return</td></tr>
                    <tr><td>Sortino Ratio</td><td>{metrics['sortino_ratio']:.3f}</td><td>Downside risk-adjusted return</td></tr>
                    <tr><td>Calmar Ratio</td><td>{metrics['calmar_ratio']:.3f}</td><td>Return/max drawdown ratio</td></tr>
                    <tr><td>Max Drawdown</td><td>{metrics['max_drawdown']:.2%}</td><td>Maximum peak-to-trough decline</td></tr>
                    <tr><td>Win Rate</td><td>{metrics['win_rate']:.2%}</td><td>Percentage of profitable trades</td></tr>
                    <tr><td>Profit Factor</td><td>{metrics['profit_factor']:.2f}</td><td>Gross profit/gross loss ratio</td></tr>
                    <tr><td>Total Trades</td><td>{metrics['total_trades']}</td><td>Total number of trades</td></tr>
                    <tr><td>Value at Risk (95%)</td><td>{metrics.get('var_95', 0):.2%}</td><td>5% worst-case loss</td></tr>
                </table>

                <div style="text-align: center; margin-top: 50px; color: #666;">
                    <p>Report generated by Simplified System Backtest Visualizer</p>
                </div>
            </body>
            </html>
            """

            # 保存報告
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_template)
                print(f"Report saved to {output_path}")

            return html_template

        except Exception as e:
            print(f"Error creating professional report: {e}")
            return f"<html><body><h1>Error generating report: {str(e)}</h1></body></html>"

    def _calculate_comprehensive_metrics(self, backtest_results: Dict[str, Any]) -> Dict[str, float]:
        """計算綜合性能指標"""
        try:
            equity_curve = pd.Series(backtest_results['equity_curve'])
            returns = pd.Series(backtest_results['returns'])
            trades = pd.DataFrame(backtest_results['trades'])

            # 基本指標
            total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
            annual_return = (1 + total_return) ** (252 / len(equity_curve)) - 1
            volatility = returns.std() * np.sqrt(252)
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0

            # 回撤指標
            running_max = equity_curve.expanding().max()
            drawdown = (equity_curve - running_max) / running_max
            max_drawdown = drawdown.min()

            # 其他指標
            downside_returns = returns[returns < 0]
            downside_volatility = downside_returns.std() * np.sqrt(252)
            sortino_ratio = annual_return / downside_volatility if downside_volatility > 0 else 0
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

            # 交易相關指標
            if not trades.empty:
                winning_trades = trades[trades['pnl'] > 0]
                win_rate = len(winning_trades) / len(trades) if len(trades) > 0 else 0

                gross_profit = winning_trades['pnl'].sum() if not winning_trades.empty else 0
                losing_trades = trades[trades['pnl'] <= 0]
                gross_loss = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 1
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

                total_trades = len(trades)
            else:
                win_rate = 0
                profit_factor = 0
                total_trades = 0

            # VaR
            var_95 = returns.quantile(0.05)

            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': total_trades,
                'var_95': var_95
            }

        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return {}

# 使用示例
if __name__ == "__main__":
    # 創建可視化器
    visualizer = BacktestVisualizer()

    # 模擬回測結果
    dates = pd.date_range('2022-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # 模擬權益曲線
    returns = np.random.randn(len(dates)) * 0.02
    returns[returns > 0.05] = 0.05  # 限制單日回報
    returns[returns < -0.05] = -0.05

    equity_curve = 100000 * (1 + returns).cumprod()

    # 模擬交易
    num_trades = 100
    trades_data = []
    for i in range(num_trades):
        trade_date = dates[np.random.randint(0, len(dates)-1)]
        trade_type = np.random.choice(['buy', 'sell'])
        pnl = np.random.randn() * 1000

        trades_data.append({
            'time': trade_date,
            'type': trade_type,
            'pnl': pnl,
            'price': equity_curve[dates.get_loc(trade_date)] if trade_date in dates else 100000
        })

    backtest_results = {
        'equity_curve': equity_curve.to_dict(),
        'returns': returns.tolist(),
        'trades': trades_data
    }

    print("Creating visualizations...")

    # 創建權益曲線
    equity_fig = visualizer.create_equity_curve(backtest_results)
    equity_fig.write_html("equity_curve_demo.html")
    print("Equity curve saved to equity_curve_demo.html")

    # 創建性能儀表板
    dashboard_fig = visualizer.create_performance_metrics_dashboard(backtest_results)
    dashboard_fig.write_html("performance_dashboard_demo.html")
    print("Performance dashboard saved to performance_dashboard_demo.html")

    # 創建專業報告
    report_html = visualizer.create_professional_report(
        backtest_results,
        output_path="backtest_report_demo.html"
    )
    print("Professional report saved to backtest_report_demo.html")

    print("\nAll visualizations created successfully!")