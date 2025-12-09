#!/usr / bin / env python3
"""
性能图表组件
Performance Charts

专业的金融图表生成器，包括：
- 价格和技术指标图表
- 性能雷达图
- 收益率分布
- 回撤分析
- 相关性热力图
- 月度收益热力图
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class PerformanceCharts:
    """性能图表生成器"""

    def __init__(self):
        """初始化图表生成器"""
        # 颜色主题
        self.colors = {
            "primary": "#00D4AA",
            "secondary": "#FF6B6B",
            "success": "#4ECDC4",
            "warning": "#FFE66D",
            "danger": "#FF6B6B",
            "info": "#4ECB71",
            "dark": "#2C3E50",
            "light": "#ECF0F1",
        }

        # 图表默认配置
        self.default_layout = go.Layout(
            template="plotly_dark",
            font = dict(size = 12, family="Arial"),
            margin = dict(l = 50, r = 50, t = 50, b = 50),
            showlegend = True,
            legend = dict(
                orientation="h", yanchor="bottom", y = 1.02, xanchor="right", x = 1
            ),
        )

    def create_price_chart(
        self, data: pd.DataFrame, show_indicators: bool = True, show_volume: bool = True
    ) -> go.Figure:
        """
        创建价格和策略信号图表

        Args:
            data: OHLCV数据及指标
            show_indicators: 是否显示技术指标
            show_volume: 是否显示成交量

        Returns:
            Plotly图表对象
        """
        try:
            # 创建子图
            rows = 3 if show_indicators and show_volume else 2
            subplot_titles = (
                ["价格走势", "成交量", "技术指标"]
                if show_volume
                else ["价格走势", "技术指标"]
            )

            fig = make_subplots(
                rows = rows,
                cols = 1,
                shared_xaxes = True,
                vertical_spacing = 0.02,
                subplot_titles = subplot_titles,
                row_width=[0.2, 0.2, 0.7] if rows == 3 else [0.2, 0.8],
            )

            # K线图
            fig.add_trace(
                go.Candlestick(
                    x = data.index,
                    open = data["open"],
                    high = data["high"],
                    low = data["low"],
                    close = data["close"],
                    name="价格",
                    increasing_line_color = self.colors["success"],
                    decreasing_line_color = self.colors["danger"],
                ),
                row = 1,
                col = 1,
            )

            # 移动平均线
            if "SMA_20" in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["SMA_20"],
                        name="SMA(20)",
                        line = dict(color = self.colors["warning"], width = 2),
                        opacity = 0.8,
                    ),
                    row = 1,
                    col = 1,
                )

            if "SMA_50" in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["SMA_50"],
                        name="SMA(50)",
                        line = dict(color = self.colors["info"], width = 2),
                        opacity = 0.8,
                    ),
                    row = 1,
                    col = 1,
                )

            # 布林带
            if all(col in data.columns for col in ["BB_Upper", "BB_Lower"]):
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["BB_Upper"],
                        name="布林带上轨",
                        line = dict(color = self.colors["secondary"], width = 1),
                        fill = None,
                    ),
                    row = 1,
                    col = 1,
                )

                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["BB_Lower"],
                        name="布林带下轨",
                        line = dict(color = self.colors["secondary"], width = 1),
                        fill="tonexty",
                        fillcolor="rgba(255, 107, 107, 0.1)",
                    ),
                    row = 1,
                    col = 1,
                )

            # 成交量
            if show_volume and "volume" in data.columns:
                fig.add_trace(
                    go.Bar(
                        x = data.index,
                        y = data["volume"],
                        name="成交量",
                        marker_color = self.colors["primary"],
                        opacity = 0.6,
                    ),
                    row = 2,
                    col = 1,
                )

            # RSI指标
            if show_indicators and "RSI_14" in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["RSI_14"],
                        name="RSI(14)",
                        line = dict(color = self.colors["primary"], width = 2),
                    ),
                    row = rows,
                    col = 1,
                )

                # RSI超买超卖线
                fig.add_hline(
                    y = 70,
                    line_dash="dash",
                    line_color = self.colors["danger"],
                    annotation_text="超买(70)",
                    row = rows,
                    col = 1,
                )
                fig.add_hline(
                    y = 30,
                    line_dash="dash",
                    line_color = self.colors["success"],
                    annotation_text="超卖(30)",
                    row = rows,
                    col = 1,
                )

            # MACD指标
            if show_indicators and all(
                col in data.columns for col in ["MACD", "MACD_Signal"]
            ):
                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["MACD"],
                        name="MACD",
                        line = dict(color = self.colors["primary"], width = 2),
                    ),
                    row = rows,
                    col = 1,
                )

                fig.add_trace(
                    go.Scatter(
                        x = data.index,
                        y = data["MACD_Signal"],
                        name="MACD Signal",
                        line = dict(color = self.colors["warning"], width = 2),
                    ),
                    row = rows,
                    col = 1,
                )

            # 更新布局
            fig.update_layout(
                title="价格走势与技术指标",
                xaxis_title="日期",
                yaxis_title="价格",
                height = 800 if show_volume else 600,
                showlegend = True,
                **self.default_layout.to_plotly_json(),
            )

            # 更新坐标轴
            fig.update_yaxes(title_text="价格", row = 1, col = 1)
            if show_volume:
                fig.update_yaxes(title_text="成交量", row = 2, col = 1)
                fig.update_yaxes(title_text="指标值", row = 3, col = 1)
            else:
                fig.update_yaxes(title_text="指标值", row = 2, col = 1)

            return fig

        except Exception as e:
            logger.error(f"Error creating price chart: {e}")
            return go.Figure()

    def create_performance_radar(
        self, results_json: Optional[str] = None, benchmark_data: Optional[Dict] = None
    ) -> go.Figure:
        """
        创建性能雷达图

        Args:
            results_json: 回测结果JSON
            benchmark_data: 基准数据

        Returns:
            Plotly雷达图
        """
        try:
            fig = go.Figure()

            if results_json:
                import json

                result_data = json.loads(results_json)
                performance = result_data.get("performance", {})

                # 雷达图指标
                metrics = [
                    "总回报率",
                    "Sharpe比率",
                    "最大回撤(反向)",
                    "胜率",
                    "Calmar比率",
                    "Sortino比率",
                ]

                # 标准化指标值到0 - 1范围
                values = [
                    min(abs(performance.get("total_return", 0)) / 50, 1),  # 50%为满分
                    min(performance.get("sharpe_ratio", 0) / 3, 1),  # Sharpe 3为满分
                    min(
                        1 - abs(performance.get("max_drawdown", 0)) / 20, 1
                    ),  # 最大回撤反向
                    performance.get("win_rate", 0) / 100,  # 胜率百分比
                    min(performance.get("calmar_ratio", 0) / 3, 1),  # Calmar 3为满分
                    min(performance.get("sortino_ratio", 0) / 3, 1),  # Sortino 3为满分
                ]

                # 策略性能
                fig.add_trace(
                    go.Scatterpolar(
                        r = values,
                        theta = metrics,
                        fill="toself",
                        name="策略性能",
                        line_color = self.colors["primary"],
                        fillcolor = f"rgba(0, 212, 170, 0.3)",
                    )
                )

            # 基准性能
            if benchmark_data:
                benchmark_values = [
                    min(abs(benchmark_data.get("total_return", 0)) / 50, 1),
                    min(benchmark_data.get("sharpe_ratio", 0) / 3, 1),
                    min(1 - abs(benchmark_data.get("max_drawdown", 0)) / 20, 1),
                    benchmark_data.get("win_rate", 0) / 100,
                    min(benchmark_data.get("calmar_ratio", 0) / 3, 1),
                    min(benchmark_data.get("sortino_ratio", 0) / 3, 1),
                ]

                fig.add_trace(
                    go.Scatterpolar(
                        r = benchmark_values,
                        theta = metrics,
                        fill="toself",
                        name="基准",
                        line_color = self.colors["warning"],
                        fillcolor = f"rgba(255, 230, 109, 0.2)",
                    )
                )

            # 更新布局
            fig.update_layout(
                polar = dict(radialaxis = dict(visible = True, range=[0, 1])),
                title="性能指标雷达图",
                height = 500,
                **self.default_layout.to_plotly_json(),
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating performance radar: {e}")
            return go.Figure()

    def create_returns_distribution(self, data: pd.DataFrame) -> go.Figure:
        """
        创建收益率分布图

        Args:
            data: 价格数据

        Returns:
            Plotly分布图
        """
        try:
            # 计算日收益率
            returns = data["close"].pct_change().dropna()

            # 创建直方图
            fig = go.Figure()

            # 收益率分布
            fig.add_trace(
                go.Histogram(
                    x = returns,
                    nbinsx = 50,
                    name="收益率分布",
                    marker_color = self.colors["primary"],
                    opacity = 0.7,
                    histnorm="probability density",
                )
            )

            # 添加正态分布拟合
            mean_return = returns.mean()
            std_return = returns.std()
            x_range = np.linspace(returns.min(), returns.max(), 100)
            normal_dist = (1 / (std_return * np.sqrt(2 * np.pi))) * np.exp(
                -0.5 * ((x_range - mean_return) / std_return) ** 2
            )

            fig.add_trace(
                go.Scatter(
                    x = x_range,
                    y = normal_dist,
                    mode="lines",
                    name="正态分布拟合",
                    line = dict(color = self.colors["danger"], width = 2, dash="dash"),
                )
            )

            # 添加统计信息
            fig.add_vline(
                x = mean_return,
                line_dash="solid",
                line_color = self.colors["warning"],
                annotation_text = f"均值: {mean_return:.4f}",
            )

            # 更新布局
            fig.update_layout(
                title="日收益率分布",
                xaxis_title="日收益率",
                yaxis_title="概率密度",
                height = 400,
                **self.default_layout.to_plotly_json(),
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating returns distribution: {e}")
            return go.Figure()

    def create_drawdown_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        创建回撤图

        Args:
            data: 价格数据

        Returns:
            Plotly回撤图
        """
        try:
            # 计算累积收益
            cumulative_returns = (1 + data["close"].pct_change()).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max

            fig = go.Figure()

            # 回撤面积图
            fig.add_trace(
                go.Scatter(
                    x = data.index,
                    y = drawdown * 100,
                    fill="tozeroy",
                    name="回撤",
                    line = dict(color = self.colors["danger"]),
                    fillcolor = f"rgba(255, 107, 107, 0.3)",
                )
            )

            # 标记最大回撤
            max_dd_idx = drawdown.idxmin()
            max_dd_value = drawdown.min()

            fig.add_trace(
                go.Scatter(
                    x=[max_dd_idx],
                    y=[max_dd_value * 100],
                    mode="markers",
                    name = f"最大回撤: {max_dd_value:.2%}",
                    marker = dict(color = self.colors["warning"], size = 10, symbol="star"),
                )
            )

            # 更新布局
            fig.update_layout(
                title="策略回撤分析",
                xaxis_title="日期",
                yaxis_title="回撤 (%)",
                height = 400,
                **self.default_layout.to_plotly_json(),
            )

            # 设置Y轴方向
            fig.update_yaxes(autorange="reversed")

            return fig

        except Exception as e:
            logger.error(f"Error creating drawdown chart: {e}")
            return go.Figure()

    def create_correlation_heatmap(
        self, data: pd.DataFrame, additional_assets: Optional[pd.DataFrame] = None
    ) -> go.Figure:
        """
        创建相关性热力图

        Args:
            data: 主要资产数据
            additional_assets: 其他资产数据

        Returns:
            Plotly热力图
        """
        try:
            # 计算收益率
            returns_data = pd.DataFrame()
            returns_data["主资产"] = data["close"].pct_change()

            # 添加其他资产（如果有）
            if additional_assets is not None:
                for col in additional_assets.columns:
                    returns_data[col] = additional_assets[col].pct_change()

            # 如果只有一个资产，创建模拟的其他资产相关性
            if len(returns_data.columns) == 1:
                # 添加一些技术指标作为对比
                returns_data["SMA_20收益率"] = data.get(
                    "SMA_20", data["close"]
                ).pct_change()
                returns_data["成交量变化率"] = data["volume"].pct_change()

            # 计算相关性矩阵
            corr_matrix = returns_data.corr()

            # 创建热力图
            fig = go.Figure(
                data = go.Heatmap(
                    z = corr_matrix.values,
                    x = corr_matrix.columns,
                    y = corr_matrix.columns,
                    colorscale="RdYlBu",
                    zmid = 0,
                    text = corr_matrix.round(3).values,
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hoverongaps = False,
                )
            )

            # 更新布局
            fig.update_layout(
                title="资产相关性热力图",
                height = 400,
                **self.default_layout.to_plotly_json(),
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating correlation heatmap: {e}")
            return go.Figure()

    def create_monthly_returns_heatmap(self, data: pd.DataFrame) -> go.Figure:
        """
        创建月度收益热力图

        Args:
            data: 价格数据

        Returns:
            Plotly月度收益热力图
        """
        try:
            # 计算月度收益率
            monthly_returns = data["close"].resample("M").last().pct_change()

            # 创建年 - 月矩阵
            monthly_pivot = pd.DataFrame()
            monthly_pivot["Year"] = monthly_returns.index.year
            monthly_pivot["Month"] = monthly_returns.index.month
            monthly_pivot["Return"] = monthly_returns.values * 100  # 转换为百分比

            # 创建热力图数据
            pivot_table = monthly_pivot.pivot_table(
                values="Return", index="Month", columns="Year", aggfunc="mean"
            )

            # 月度标签
            month_labels = [
                "1月",
                "2月",
                "3月",
                "4月",
                "5月",
                "6月",
                "7月",
                "8月",
                "9月",
                "10月",
                "11月",
                "12月",
            ]

            # 创建热力图
            fig = go.Figure(
                data = go.Heatmap(
                    z = pivot_table.values,
                    x = pivot_table.columns,
                    y = month_labels,
                    colorscale="RdYlGn",
                    zmid = 0,
                    text = pivot_table.round(2).values,
                    texttemplate="%{text}%",
                    textfont={"size": 10},
                    hoverongaps = False,
                )
            )

            # 更新布局
            fig.update_layout(
                title="月度收益率热力图 (%)",
                xaxis_title="年份",
                yaxis_title="月份",
                height = 400,
                **self.default_layout.to_plotly_json(),
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating monthly returns heatmap: {e}")
            return go.Figure()

    def create_comparison_chart(
        self,
        strategy_data: pd.DataFrame,
        benchmark_data: Optional[pd.DataFrame] = None,
        title: str = "策略表现对比",
    ) -> go.Figure:
        """
        创建策略对比图表

        Args:
            strategy_data: 策略数据
            benchmark_data: 基准数据
            title: 图表标题

        Returns:
            Plotly对比图
        """
        try:
            fig = go.Figure()

            # 计算累积收益
            strategy_cumret = (1 + strategy_data.pct_change()).cumprod()

            # 策略表现
            fig.add_trace(
                go.Scatter(
                    x = strategy_cumret.index,
                    y = strategy_cumret,
                    mode="lines",
                    name="策略",
                    line = dict(color = self.colors["primary"], width = 2),
                )
            )

            # 基准表现
            if benchmark_data is not None:
                benchmark_cumret = (1 + benchmark_data.pct_change()).cumprod()
                fig.add_trace(
                    go.Scatter(
                        x = benchmark_cumret.index,
                        y = benchmark_cumret,
                        mode="lines",
                        name="基准",
                        line = dict(color = self.colors["warning"], width = 2, dash="dash"),
                    )
                )

            # 更新布局
            fig.update_layout(
                title = title,
                xaxis_title="日期",
                yaxis_title="累积收益",
                height = 500,
                **self.default_layout.to_plotly_json(),
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating comparison chart: {e}")
            return go.Figure()

    def create_risk_return_scatter(
        self, strategies_data: List[Dict[str, float]]
    ) -> go.Figure:
        """
        创建风险收益散点图

        Args:
            strategies_data: 策略数据列表

        Returns:
            Plotly散点图
        """
        try:
            fig = go.Figure()

            # 提取数据
            returns = [s["annual_return"] for s in strategies_data]
            risks = [abs(s["max_drawdown"]) for s in strategies_data]
            names = [s["name"] for s in strategies_data]

            # 添加散点
            fig.add_trace(
                go.Scatter(
                    x = risks,
                    y = returns,
                    mode="markers + text",
                    text = names,
                    textposition="top center",
                    marker = dict(size = 10, color = self.colors["primary"], opacity = 0.7),
                    name="策略",
                )
            )

            # 更新布局
            fig.update_layout(
                title="风险收益散点图",
                xaxis_title="最大回撤 (%)",
                yaxis_title="年化收益率 (%)",
                height = 500,
                **self.default_layout.to_plotly_json(),
            )

            return fig

        except Exception as e:
            logger.error(f"Error creating risk - return scatter: {e}")
            return go.Figure()
