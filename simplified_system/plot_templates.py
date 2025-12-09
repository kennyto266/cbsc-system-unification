#!/usr / bin / env python3
"""
📊 專業量化分析圖表模板
Professional Quantitative Analysis Chart Templates

高級量化交易專用圖表模板庫
Advanced chart template library specifically for quantitative trading

Features:
- Professional candlestick charts with technical indicators
- Risk - return analysis visualizations
- Portfolio composition charts
- Performance attribution diagrams
- Correlation heatmaps
- Drawdown analysis charts

Author: Claude Code Assistant
Date: 2025 - 11 - 27
Version: 1.0
"""

from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots


class QuantitativeChartTemplates:
    """專業量化分析圖表模板類

    Professional quantitative analysis chart templates class
    """

    def __init__(self, theme: str = "quantitative"):
        """初始化圖表模板

        Initialize chart templates

        Args:
            theme: 圖表主題 ('quantitative', 'professional', 'dark', 'light')
        """
        self.theme = theme
        self.colors = self._get_color_palette()
        self.layout_config = self._get_layout_config()

    def _get_color_palette(self) -> Dict[str, str]:
        """獲取量化分析專用顏色板

        Get quantitative analysis specific color palette
        """
        return {
            # Market colors
            "bull_market": "#00d084",  # Green - bullish
            "bear_market": "#ff4757",  # Red - bearish
            "neutral": "#95a5a6",  # Gray - neutral
            # Technical indicator colors
            "ma5": "#3498db",  # Blue
            "ma10": "#9b59b6",  # Purple
            "ma20": "#e74c3c",  # Red
            "ma50": "#f39c12",  # Orange
            "ma200": "#34495e",  # Dark gray
            "rsi": "#8e44ad",  # Purple
            "rsi_overbought": "#e74c3c",  # Red
            "rsi_oversold": "#27ae60",  # Green
            "rsi_neutral": "#95a5a6",  # Gray
            "macd": "#2980b9",  # Blue
            "macd_signal": "#c0392b",  # Red
            "macd_histogram": "#27ae60",  # Green
            "bb_upper": "#e67e22",  # Orange
            "bb_middle": "#3498db",  # Blue
            "bb_lower": "#e67e22",  # Orange
            # Portfolio colors
            "portfolio": "#3498db",  # Blue
            "benchmark": "#95a5a6",  # Gray
            "outperformance": "#27ae60",  # Green
            "underperformance": "#e74c3c",  # Red
            # Risk colors
            "low_risk": "#27ae60",  # Green
            "medium_risk": "#f39c12",  # Orange
            "high_risk": "#e74c3c",  # Red
            # Gradient colors
            "gradient_start": "#3498db",
            "gradient_end": "#2980b9",
            # Additional colors
            "volume": "#ecf0f1",  # Light gray
            "background": "#ffffff",  # White
            "grid": "#ecf0f1",  # Light gray
            "text": "#2c3e50",  # Dark gray
        }

    def _get_layout_config(self) -> Dict[str, Any]:
        """獲取佈局配置

        Get layout configuration
        """
        return {
            "font_family": "Arial, SimHei, sans - serif",
            "font_size": 12,
            "margin": dict(l = 80, r = 40, t = 80, b = 80),
            "legend": dict(
                orientation="h",
                yanchor="bottom",
                y = 1.02,
                xanchor="right",
                x = 1,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgb(200,200,200)",
                borderwidth = 1,
            ),
            "showbackground": False,
            "plot_bgcolor": self.colors["background"],
            "paper_bgcolor": self.colors["background"],
        }

    def candlestick_chart(
        self,
        data: pd.DataFrame,
        title: str = "股價K線圖",
        indicators: Optional[Dict[str, pd.Series]] = None,
        volume: bool = True,
        show_moving_averages: List[str] = None,
        show_bollinger_bands: bool = False,
        show_volume_bars: bool = True,
    ) -> go.Figure:
        """創建專業K線圖

        Create professional candlestick chart

        Args:
            data: 股票數據，必須包含 Open, High, Low, Close 列
            title: 圖表標題
            indicators: 技術指標字典 {名稱: Series}
            volume: 是否顯示成交量
            show_moving_averages: 要顯示的移動平均線列表 ['MA5', 'MA20', etc.]
            show_bollinger_bands: 是否顯示布林帶
            show_volume_bars: 是否顯示成交量柱狀圖

        Returns:
            Plotly Figure對象
        """
        # 確定子圖行數
        rows = 2 if volume and show_volume_bars else 1
        row_heights = [0.7, 0.3] if rows == 2 else [1.0]

        # 創建子圖
        fig = make_subplots(
            rows = rows,
            cols = 1,
            shared_xaxes = True,
            vertical_spacing = 0.02,
            row_heights = row_heights,
            subplot_titles=[title, "成交量"] if rows == 2 else [title],
        )

        # K線圖
        fig.add_trace(
            go.Candlestick(
                x = data.index,
                open = data["Open"],
                high = data["High"],
                low = data["Low"],
                close = data["Close"],
                name="股價",
                increasing_line_color = self.colors["bull_market"],
                decreasing_line_color = self.colors["bear_market"],
                increasing_fillcolor = self.colors["bull_market"],
                decreasing_fillcolor = self.colors["bear_market"],
                line_width = 1,
            ),
            row = 1,
            col = 1,
        )

        # 添加移動平均線
        if show_moving_averages:
            for ma in show_moving_averages:
                if ma in data.columns:
                    color_key = ma.lower().replace("ma", "ma")
                    color = self.colors.get(color_key, self.colors["neutral"])

                    fig.add_trace(
                        go.Scatter(
                            x = data.index,
                            y = data[ma],
                            mode="lines",
                            name = ma,
                            line = dict(color = color, width = 1.5),
                            opacity = 0.8,
                        ),
                        row = 1,
                        col = 1,
                    )

        # 添加布林帶
        if show_bollinger_bands:
            bb_cols = ["BB_upper", "BB_middle", "BB_lower"]
            if all(col in data.columns for col in bb_cols):
                # 上軌
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["BB_upper"],
                        mode="lines",
                        name="BB上軌",
                        line = dict(color = self.colors["bb_upper"], dash="dash", width = 1),
                        opacity = 0.7,
                    ),
                    row = 1,
                    col = 1,
                )

                # 中軌
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["BB_middle"],
                        mode="lines",
                        name="BB中軌",
                        line = dict(color = self.colors["bb_middle"], width = 1),
                        opacity = 0.7,
                    ),
                    row = 1,
                    col = 1,
                )

                # 下軌
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["BB_lower"],
                        mode="lines",
                        name="BB下軌",
                        line = dict(color = self.colors["bb_lower"], dash="dash", width = 1),
                        fill="tonexty",
                        fillcolor = f'rgba({int(self.colors["bb_lower"][1:3], 16)}, '
                        f'{int(self.colors["bb_lower"][3:5], 16)}, '
                        f'{int(self.colors["bb_lower"][5:7], 16)}, 0.1)',
                        opacity = 0.7,
                    ),
                    row = 1,
                    col = 1,
                )

        # 添加自定義指標
        if indicators:
            for name, values in indicators.items():
                if isinstance(values, pd.Series) and len(values) == len(data):
                    fig.add_trace(
                        go.Scatter(
                            x = data.index,
                            y = values,
                            mode="lines",
                            name = name,
                            line = dict(width = 2),
                            opacity = 0.8,
                        ),
                        row = 1,
                        col = 1,
                    )

        # 成交量
        if volume and show_volume_bars and "Volume" in data.columns:
            # 根據漲跌設置顏色
            colors = [
                (
                    self.colors["bull_market"]
                    if close >= open
                    else self.colors["bear_market"]
                )
                for close, open in zip(data["Close"], data["Open"])
            ]

            fig.add_trace(
                go.Bar(
                    x = data.index,
                    y = data["Volume"],
                    name="成交量",
                    marker_color = colors,
                    opacity = 0.7,
                ),
                row = 2,
                col = 1,
            )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            legend = self.layout_config["legend"],
            xaxis_rangeslider_visible = False,
            height = 800 if rows == 2 else 600,
            **self.layout_config,
        )

        # 更新坐標軸
        fig.update_yaxes(
            title_text="價格 (HKD)", row = 1, col = 1, gridcolor = self.colors["grid"]
        )
        if rows == 2:
            fig.update_yaxes(
                title_text="成交量", row = 2, col = 1, gridcolor = self.colors["grid"]
            )

        fig.update_xaxes(showgrid = True, gridcolor = self.colors["grid"])

        return fig

    def technical_indicators_chart(
        self,
        data: pd.DataFrame,
        indicators: Dict[str, pd.Series],
        title: str = "技術指標分析",
    ) -> go.Figure:
        """創建技術指標組合圖表

        Create technical indicators combination chart

        Args:
            data: 價格數據
            indicators: 技術指標字典
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        # 計算子圖數量
        subplot_count = len(indicators)
        fig = make_subplots(
            rows = subplot_count,
            cols = 1,
            shared_xaxes = True,
            vertical_spacing = 0.05,
            subplot_titles = list(indicators.keys()),
        )

        # 添加價格圖（第一個子圖）
        fig.add_trace(
            go.Scatter(
                x = data.index,
                y = data["Close"],
                mode="lines",
                name="收盤價",
                line = dict(color = self.colors["neutral"], width = 2),
            ),
            row = 1,
            col = 1,
        )

        # 添加各個技術指標
        for i, (name, values) in enumerate(indicators.items(), 1):
            if isinstance(values, pd.Series) and len(values) == len(data):
                # RSI特殊處理
                if "RSI" in name.upper():
                    fig.add_trace(
                        go.Scatter(
                            x = data.index,
                            y = values,
                            mode="lines",
                            name = name,
                            line = dict(color = self.colors["rsi"], width = 2),
                        ),
                        row = i,
                        col = 1,
                    )

                    # 添加超買超賣線
                    fig.add_hline(
                        y = 70,
                        line_dash="dash",
                        line_color = self.colors["rsi_overbought"],
                        row = i,
                        col = 1,
                        opacity = 0.7,
                    )
                    fig.add_hline(
                        y = 30,
                        line_dash="dash",
                        line_color = self.colors["rsi_oversold"],
                        row = i,
                        col = 1,
                        opacity = 0.7,
                    )

                # MACD特殊處理
                elif "MACD" in name.upper():
                    fig.add_trace(
                        go.Scatter(
                            x = data.index,
                            y = values,
                            mode="lines",
                            name = name,
                            line = dict(color = self.colors["macd"], width = 2),
                        ),
                        row = i,
                        col = 1,
                    )

                # 其他指標
                else:
                    fig.add_trace(
                        go.Scatter(
                            x = data.index,
                            y = values,
                            mode="lines",
                            name = name,
                            line = dict(width = 2),
                        ),
                        row = i,
                        col = 1,
                    )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            height = 200 * subplot_count + 100,
            showlegend = True,
            **self.layout_config,
        )

        return fig

    def portfolio_performance_chart(
        self,
        portfolio: pd.DataFrame,
        benchmark: Optional[pd.Series] = None,
        title: str = "投資組合表現",
    ) -> go.Figure:
        """創建投資組合表現圖表

        Create portfolio performance chart

        Args:
            portfolio: 投資組合淨值序列
            benchmark: 基準指數序列
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        fig = go.Figure()

        # 投資組合淨值
        fig.add_trace(
            go.Scatter(
                x = portfolio.index,
                y = portfolio.values,
                mode="lines",
                name="投資組合",
                line = dict(color = self.colors["portfolio"], width = 3),
            )
        )

        # 基準指數
        if benchmark is not None:
            # 標準化基準指數
            benchmark_norm = (benchmark / benchmark.iloc[0]) * portfolio.iloc[0]
            fig.add_trace(
                go.Scatter(
                    x = benchmark_norm.index,
                    y = benchmark_norm.values,
                    mode="lines",
                    name="基準指數",
                    line = dict(color = self.colors["benchmark"], width = 2, dash="dash"),
                )
            )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            xaxis_title="日期",
            yaxis_title="淨值",
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            height = 500,
            legend = dict(yanchor="top", y = 0.99, xanchor="left", x = 0.01),
            **self.layout_config,
        )

        return fig

    def drawdown_chart(
        self, equity_curve: pd.Series, title: str = "回撤分析"
    ) -> go.Figure:
        """創建回撤分析圖表

        Create drawdown analysis chart

        Args:
            equity_curve: 淨值曲線
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        # 計算回撤
        cumulative_max = equity_curve.expanding().max()
        drawdown = (equity_curve / cumulative_max - 1) * 100

        fig = make_subplots(
            rows = 2,
            cols = 1,
            shared_xaxes = True,
            vertical_spacing = 0.05,
            subplot_titles=("淨值曲線", "回撤 (%)"),
            row_heights=[0.7, 0.3],
        )

        # 淨值曲線
        fig.add_trace(
            go.Scatter(
                x = equity_curve.index,
                y = equity_curve.values,
                mode="lines",
                name="淨值",
                line = dict(color = self.colors["portfolio"], width = 2),
            ),
            row = 1,
            col = 1,
        )

        # 回撤
        fig.add_trace(
            go.Scatter(
                x = drawdown.index,
                y = drawdown.values,
                mode="lines",
                name="回撤",
                fill="tozeroy",
                fillcolor = f'rgba({int(self.colors["bear_market"][1:3], 16)}, '
                f'{int(self.colors["bear_market"][3:5], 16)}, '
                f'{int(self.colors["bear_market"][5:7], 16)}, 0.3)',
                line = dict(color = self.colors["bear_market"], width = 2),
            ),
            row = 2,
            col = 1,
        )

        # 標記最大回撤
        max_dd_idx = drawdown.idxmin()
        max_dd_value = drawdown.min()

        fig.add_annotation(
            x = max_dd_idx,
            y = max_dd_value,
            text = f"最大回撤: {max_dd_value:.2f}%",
            showarrow = True,
            arrowhead = 2,
            arrowsize = 1,
            arrowwidth = 2,
            arrowcolor = self.colors["bear_market"],
            row = 2,
            col = 1,
        )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            height = 600,
            **self.layout_config,
        )

        fig.update_yaxes(title_text="淨值", row = 1, col = 1)
        fig.update_yaxes(title_text="回撤 (%)", row = 2, col = 1)

        return fig

    def correlation_heatmap(
        self, correlation_matrix: pd.DataFrame, title: str = "資產相關性熱力圖"
    ) -> go.Figure:
        """創建資產相關性熱力圖

        Create asset correlation heatmap

        Args:
            correlation_matrix: 相關性矩陣
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        fig = go.Figure(
            data = go.Heatmap(
                z = correlation_matrix.values,
                x = correlation_matrix.columns,
                y = correlation_matrix.index,
                colorscale="RdBu",
                zmid = 0,
                zmin = -1,
                zmax = 1,
                text = correlation_matrix.round(3).values,
                texttemplate="%{text}",
                textfont={"size": 11},
                hoverongaps = False,
                colorbar = dict(
                    title="相關性係數",
                    titleside="right",
                    tickmode="linear",
                    tick0 = -1,
                    dtick = 0.2,
                ),
            )
        )

        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            width = 700,
            height = 600,
            xaxis_showgrid = False,
            yaxis_showgrid = False,
            **self.layout_config,
        )

        return fig

    def risk_return_scatter(
        self, strategies: pd.DataFrame, title: str = "策略風險回報分析"
    ) -> go.Figure:
        """創建策略風險回報散點圖

        Create strategy risk - return scatter plot

        Args:
            strategies: 策略數據，包含 'return', 'volatility', 'sharpe', 'name' 列
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        # 根據Sharpe比率設置顏色
        colors = []
        for sharpe in strategies["sharpe"]:
            if sharpe > 1.5:
                colors.append(self.colors["low_risk"])
            elif sharpe > 0.8:
                colors.append(self.colors["medium_risk"])
            else:
                colors.append(self.colors["high_risk"])

        # 根據最大回撤設置大小
        sizes = (
            strategies.get("max_drawdown", pd.Series([0.1] * len(strategies))).abs()
            * 1000
            + 10
        )

        fig = go.Figure()

        # 添加散點
        fig.add_trace(
            go.Scatter(
                x = strategies["volatility"],
                y = strategies["return"],
                mode="markers + text",
                marker = dict(
                    size = sizes,
                    color = colors,
                    line = dict(width = 2, color="white"),
                    opacity = 0.8,
                ),
                text = strategies["name"],
                textposition="top center",
                name="策略",
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "年化回報: %{y:.2%}<br>"
                    "年化波動率: %{x:.2%}<br>"
                    "Sharpe比率: %{customdata:.3f}<br>"
                    "<extra></extra>"
                ),
                customdata = strategies["sharpe"],
            )
        )

        # 添加有效率前緣（簡化版）
        efficient_frontier_x = np.linspace(0.05, 0.3, 100)
        efficient_frontier_y = 0.03 + 1.2 * efficient_frontier_x  # 簡化的有效率前緣

        fig.add_trace(
            go.Scatter(
                x = efficient_frontier_x,
                y = efficient_frontier_y,
                mode="lines",
                name="有效率前緣",
                line = dict(color = self.colors["neutral"], dash="dash", width = 2),
                opacity = 0.7,
            )
        )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            xaxis_title="年化波動率",
            yaxis_title="年化回報",
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            width = 800,
            height = 600,
            **self.layout_config,
        )

        return fig

    def performance_attribution_chart(
        self, attribution_data: Dict[str, float], title: str = "績效歸因分析"
    ) -> go.Figure:
        """創建績效歸因瀑布圖

        Create performance attribution waterfall chart

        Args:
            attribution_data: 歸因數據字典 {因子: 貢獻值}
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        factors = list(attribution_data.keys())
        values = list(attribution_data.values())

        # 設置顏色
        colors = []
        for value in values:
            if value > 0:
                colors.append(self.colors["bull_market"])
            else:
                colors.append(self.colors["bear_market"])

        fig = go.Figure()

        # 添加瀑布圖
        fig.add_trace(
            go.Waterfall(
                name="績效歸因",
                orientation="v",
                measure=["relative"] * len(values),
                x = factors,
                y = values,
                text=[f"{v:.2%}" for v in values],
                textposition="outside",
                textfont={"size": 12},
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": self.colors["bear_market"]}},
                increasing={"marker": {"color": self.colors["bull_market"]}},
                totals={"marker": {"color": self.colors["neutral"]}},
            )
        )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            xaxis_title="歸因因子",
            yaxis_title="貢獻度",
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            height = 500,
            showlegend = False,
            **self.layout_config,
        )

        return fig

    def rolling_metrics_chart(
        self, returns: pd.Series, window: int = 252, title: str = "滾動風險指標"
    ) -> go.Figure:
        """創建滾動風險指標圖表

        Create rolling risk metrics chart

        Args:
            returns: 收益率序列
            window: 滾動窗口
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        # 計算滾動指標
        rolling_vol = returns.rolling(window = window).std() * np.sqrt(252)
        rolling_sharpe = (
            returns.rolling(window = window).mean() * 252 - 0.03
        ) / rolling_vol
        rolling_var = returns.rolling(window = window).quantile(0.05)

        fig = make_subplots(
            rows = 3,
            cols = 1,
            shared_xaxes = True,
            vertical_spacing = 0.05,
            subplot_titles=(
                f"滾動波動率 ({window}天)",
                f"滾動Sharpe比率 ({window}天)",
                f"滾動VaR (5%, {window}天)",
            ),
        )

        # 波動率
        fig.add_trace(
            go.Scatter(
                x = rolling_vol.index,
                y = rolling_vol.values,
                mode="lines",
                name="波動率",
                line = dict(color = self.colors["medium_risk"], width = 2),
            ),
            row = 1,
            col = 1,
        )

        # Sharpe比率
        fig.add_trace(
            go.Scatter(
                x = rolling_sharpe.index,
                y = rolling_sharpe.values,
                mode="lines",
                name="Sharpe比率",
                line = dict(color = self.colors["portfolio"], width = 2),
            ),
            row = 2,
            col = 1,
        )

        # 添加Sharpe = 1的參考線
        fig.add_hline(
            y = 1,
            line_dash="dash",
            line_color = self.colors["neutral"],
            row = 2,
            col = 1,
            opacity = 0.7,
        )

        # VaR
        fig.add_trace(
            go.Scatter(
                x = rolling_var.index,
                y = rolling_var.values,
                mode="lines",
                name="VaR",
                line = dict(color = self.colors["high_risk"], width = 2),
                fill="tonexty",
                fillcolor = f'rgba({int(self.colors["high_risk"][1:3], 16)}, '
                f'{int(self.colors["high_risk"][3:5], 16)}, '
                f'{int(self.colors["high_risk"][5:7], 16)}, 0.1)',
            ),
            row = 3,
            col = 1,
        )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            height = 700,
            **self.layout_config,
        )

        fig.update_yaxes(title_text="波動率", row = 1, col = 1)
        fig.update_yaxes(title_text="Sharpe比率", row = 2, col = 1)
        fig.update_yaxes(title_text="VaR", row = 3, col = 1)

        return fig

    def exposure_analysis_chart(
        self, exposure_data: pd.DataFrame, title: str = "風險暴露分析"
    ) -> go.Figure:
        """創建風險暴露分析圖表

        Create risk exposure analysis chart

        Args:
            exposure_data: 暴露數據 DataFrame
            title: 圖表標題

        Returns:
            Plotly Figure對象
        """
        fig = make_subplots(
            rows = 1,
            cols = 2,
            specs=[[{"type": "bar"}, {"type": "pie"}]],
            subplot_titles=("行業暴露", "行業權重分佈"),
        )

        # 行業暴露柱狀圖
        fig.add_trace(
            go.Bar(
                x = exposure_data.index,
                y = exposure_data["exposure"],
                name="風險暴露",
                marker_color = self.colors["portfolio"],
                opacity = 0.8,
            ),
            row = 1,
            col = 1,
        )

        # 行業權重餅圖
        fig.add_trace(
            go.Pie(
                labels = exposure_data.index,
                values = exposure_data["weight"],
                name="權重分佈",
                hole = 0.3,
            ),
            row = 1,
            col = 2,
        )

        # 更新佈局
        fig.update_layout(
            template="plotly_white",
            title = dict(text = title, x = 0.5, font_size = 16),
            font_family = self.layout_config["font_family"],
            font_size = self.layout_config["font_size"],
            margin = self.layout_config["margin"],
            height = 500,
            showlegend = False,
            **self.layout_config,
        )

        return fig


# 使用示例
if __name__ == "__main__":
    # 創建圖表模板實例
    chart_templates = QuantitativeChartTemplates()

    # 生成模擬數據進行測試
    np.random.seed(42)
    dates = pd.date_range("2020 - 01 - 01", "2023 - 12 - 31", freq="D")

    # 模擬股價數據
    prices = 100 + np.cumsum(np.random.normal(0.001, 0.02, len(dates)))

    # 創建OHLC數據
    stock_data = pd.DataFrame(
        {
            "Open": prices,
            "High": prices * (1 + np.random.uniform(0, 0.02, len(dates))),
            "Low": prices * (1 - np.random.uniform(0, 0.02, len(dates))),
            "Close": prices,
            "Volume": np.random.randint(1000000, 5000000, len(dates)),
        },
        index = dates,
    )

    print("✅ Quantitative Chart Templates initialized successfully!")
    print(
        f"📊 Available templates: {len([method for method in dir(chart_templates) if not method.startswith('_')])}"
    )
    print("🎯 Ready for professional quantitative analysis visualization!")
