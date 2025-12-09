"""
图表嵌入系统

支持：
- Plotly图表导出为高分辨率图像
- 自适应大小调整
- 图表标题和说明
- 多图表类型支持
"""

from __future__ import annotations

import base64
import logging
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class ChartManager:
    """
    图表管理器

    负责创建、格式化和嵌入各种类型的图表
    """

    # 默认图表配置
    DEFAULT_CONFIG = {
        "width": 800,
        "height": 500,
        "scale": 2,  # 高分辨率缩放
        "format": "png",
        "quality": 100,
    }

    # 图表颜色主题
    COLOR_THEME = {
        "primary": "#3498DB",
        "secondary": "#2ECC71",
        "danger": "#E74C3C",
        "warning": "#F39C12",
        "info": "#1ABC9C",
        "dark": "#34495E",
        "light": "#ECF0F1",
    }

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        """
        初始化图表管理器

        Args:
            output_dir: 图表输出目录，默认使用系统临时目录
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(tempfile.gettempdir()) / "pdf_charts"
            self.output_dir.mkdir(exist_ok=True)

        self.generated_charts: List[Path] = []
        logger.info(f"图表管理器初始化完成，输出目录: {self.output_dir}")

    def create_chart(
        self,
        chart_type: str,
        data: Union[pd.DataFrame, Dict, List],
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建图表

        Args:
            chart_type: 图表类型 (line, bar, pie, scatter, candlestick, etc.)
            data: 图表数据
            options: 图表选项

        Returns:
            包含图表信息的字典
        """
        options = options or {}
        config = {**self.DEFAULT_CONFIG, **options.get("config", {})}

        # 选择创建方法
        creators = {
            "line": self._create_line_chart,
            "bar": self._create_bar_chart,
            "pie": self._create_pie_chart,
            "scatter": self._create_scatter_chart,
            "candlestick": self._create_candlestick_chart,
            "heatmap": self._create_heatmap,
            "box": self._create_box_plot,
            "histogram": self._create_histogram,
            "area": self._create_area_chart,
        }

        if chart_type not in creators:
            raise ValueError(f"不支持的图表类型: {chart_type}")

        # 创建图表
        fig = creators[chart_type](data, options)

        # 设置布局
        self._set_layout(fig, options)

        # 导出为图像
        image_path = self._export_chart(fig, config)

        return {
            "image_path": image_path,
            "chart_type": chart_type,
            "title": options.get("title", ""),
            "width": config["width"],
            "height": config["height"],
        }

    def _create_line_chart(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建折线图"""
        if isinstance(data, pd.DataFrame):
            fig = px.line(
                data,
                x=options.get("x", data.columns[0]),
                y=options.get("y", data.columns[1:]),
                title=options.get("title", "折线图"),
                labels=options.get("labels", {}),
            )
        else:
            # 使用Plotly图形对象
            fig = go.Figure()

            if isinstance(data, dict):
                for key, values in data.items():
                    fig.add_trace(
                        go.Scatter(
                            x=values.get("x", []),
                            y=values.get("y", []),
                            mode="lines",
                            name=key,
                            line=dict(
                                color=options.get("colors", {}).get(
                                    key, self.COLOR_THEME["primary"]
                                ),
                                width=options.get("line_width", 2),
                            ),
                        )
                    )

        return fig

    def _create_bar_chart(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建柱状图"""
        if isinstance(data, pd.DataFrame):
            fig = px.bar(
                data,
                x=options.get("x", data.columns[0]),
                y=options.get("y", data.columns[1]),
                color=options.get("color", None),
                title=options.get("title", "柱状图"),
                barmode=options.get("barmode", "group"),
            )
        else:
            categories = data.get("categories", [])
            values = data.get("values", [])

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=categories,
                        y=values,
                        marker_color=options.get("color", self.COLOR_THEME["primary"]),
                    )
                ]
            )

        return fig

    def _create_pie_chart(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建饼图"""
        if isinstance(data, pd.DataFrame):
            fig = px.pie(
                data,
                values=options.get("values", data.columns[1]),
                names=options.get("names", data.columns[0]),
                title=options.get("title", "饼图"),
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
        else:
            labels = data.get("labels", [])
            values = data.get("values", [])

            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=values,
                        hole=options.get("hole", 0),
                    )
                ]
            )

        return fig

    def _create_scatter_chart(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建散点图"""
        if isinstance(data, pd.DataFrame):
            fig = px.scatter(
                data,
                x=options.get("x", data.columns[0]),
                y=options.get("y", data.columns[1]),
                color=options.get("color", None),
                size=options.get("size", None),
                title=options.get("title", "散点图"),
            )
        else:
            x_data = data.get("x", [])
            y_data = data.get("y", [])

            fig = go.Figure(
                data=[
                    go.Scatter(
                        x=x_data,
                        y=y_data,
                        mode="markers",
                        marker=dict(
                            size=options.get("size", 8),
                            color=options.get("color", self.COLOR_THEME["primary"]),
                            opacity=options.get("opacity", 0.7),
                        ),
                    )
                ]
            )

        return fig

    def _create_candlestick_chart(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建K线图"""
        if not isinstance(data, pd.DataFrame):
            raise ValueError("K线图需要DataFrame格式的数据")

        required_columns = ["open", "high", "low", "close"]
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"数据必须包含列: {required_columns}")

        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=(
                        data.index
                        if options.get("use_index", True)
                        else data[options.get("x", "date")]
                    ),
                    open=data["open"],
                    high=data["high"],
                    low=data["low"],
                    close=data["close"],
                    name=options.get("name", "OHLC"),
                )
            ]
        )

        return fig

    def _create_heatmap(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建热力图"""
        if isinstance(data, pd.DataFrame):
            fig = px.imshow(
                data.select_dtypes(include=["number"]),
                color_continuous_scale=options.get("color_scale", "RdYlBu_r"),
                title=options.get("title", "热力图"),
            )
        else:
            z_data = data.get("z", [])
            x_labels = data.get("x", list(range(len(z_data[0]) if z_data else 0)))
            y_labels = data.get("y", list(range(len(z_data))))

            fig = go.Figure(
                data=[
                    go.Heatmap(
                        z=z_data,
                        x=x_labels,
                        y=y_labels,
                        colorscale=options.get("color_scale", "RdYlBu_r"),
                    )
                ]
            )

        return fig

    def _create_box_plot(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建箱线图"""
        if isinstance(data, pd.DataFrame):
            fig = px.box(
                data,
                y=options.get("y", data.columns[-1]),
                title=options.get("title", "箱线图"),
            )
        else:
            values = data.get("values", [])

            fig = go.Figure(
                data=[
                    go.Box(
                        y=values,
                        name=options.get("name", "Box"),
                        boxpoints=options.get("boxpoints", "outliers"),
                    )
                ]
            )

        return fig

    def _create_histogram(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建直方图"""
        if isinstance(data, pd.DataFrame):
            fig = px.histogram(
                data,
                x=options.get("x", data.columns[0]),
                nbins=options.get("nbins", 30),
                title=options.get("title", "直方图"),
            )
        else:
            values = data.get("values", [])

            fig = go.Figure(
                data=[
                    go.Histogram(
                        x=values,
                        nbinsx=options.get("nbins", 30),
                        marker_color=options.get("color", self.COLOR_THEME["primary"]),
                    )
                ]
            )

        return fig

    def _create_area_chart(
        self,
        data: Union[pd.DataFrame, Dict],
        options: Dict[str, Any],
    ) -> go.Figure:
        """创建面积图"""
        if isinstance(data, pd.DataFrame):
            fig = px.area(
                data,
                x=options.get("x", data.columns[0]),
                y=options.get("y", data.columns[1:]),
                title=options.get("title", "面积图"),
            )
        else:
            fig = go.Figure()

            if isinstance(data, dict):
                for key, values in data.items():
                    fig.add_trace(
                        go.Scatter(
                            x=values.get("x", []),
                            y=values.get("y", []),
                            mode="lines",
                            fill="tonexty" if options.get("stacked") else "tozeroy",
                            name=key,
                        )
                    )

        return fig

    def _set_layout(self, fig: go.Figure, options: Dict[str, Any]) -> None:
        """设置图表布局"""
        # 基础布局
        fig.update_layout(
            title={
                "text": options.get("title", ""),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 20, "color": self.COLOR_THEME["dark"]},
            },
            font=dict(
                family=options.get("font_family", "Arial, sans - serif"),
                size=options.get("font_size", 12),
                color=self.COLOR_THEME["dark"],
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=options.get("show_legend", True),
            legend=dict(
                orientation=options.get("legend_orientation", "v"),
                yanchor=options.get("legend_yanchor", "top"),
                y=options.get("legend_y", 1),
                xanchor=options.get("legend_xanchor", "left"),
                x=options.get("legend_x", 1.02),
            ),
        )

        # X轴设置
        fig.update_xaxes(
            title=options.get("x_title", ""),
            showgrid=options.get("show_grid", True),
            gridcolor=self.COLOR_THEME["light"],
            linecolor=self.COLOR_THEME["dark"],
            linewidth=1,
        )

        # Y轴设置
        fig.update_yaxes(
            title=options.get("y_title", ""),
            showgrid=options.get("show_grid", True),
            gridcolor=self.COLOR_THEME["light"],
            linecolor=self.COLOR_THEME["dark"],
            linewidth=1,
        )

    def _export_chart(
        self,
        fig: go.Figure,
        config: Dict[str, Any],
    ) -> Optional[Path]:
        """
        导出图表为图像文件

        Args:
            fig: Plotly图表对象
            config: 导出配置

        Returns:
            图像文件路径
        """
        try:
            # 生成唯一文件名
            timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S_ % f")
            filename = f"chart_{timestamp}.{config['format']}"
            output_path = self.output_dir / filename

            # 导出图像
            fig.write_image(
                output_path,
                width=config["width"],
                height=config["height"],
                scale=config["scale"],
                format=config["format"],
                quality=config["quality"],
            )

            self.generated_charts.append(output_path)
            logger.info(f"图表已导出: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"图表导出失败: {e}")
            return None

    def create_performance_chart(
        self,
        data: pd.DataFrame,
        metrics: List[str],
    ) -> Dict[str, Any]:
        """
        创建性能分析图表

        Args:
            data: 性能数据
            metrics: 指标列表

        Returns:
            图表信息字典
        """
        # 创建子图
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=("累计收益率", "回撤", "月度收益", "风险收益散点"),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
            ],
        )

        # 1. 累计收益率
        if "cumulative_return" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["cumulative_return"],
                    name="累计收益率",
                    line=dict(color=self.COLOR_THEME["primary"], width=2),
                ),
                row=1,
                col=1,
            )

        # 2. 回撤
        if "drawdown" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["drawdown"],
                    name="回撤",
                    fill="tonexty",
                    line=dict(color=self.COLOR_THEME["danger"]),
                ),
                row=1,
                col=2,
            )

        # 3. 月度收益
        if "monthly_return" in data.columns:
            colors = [
                self.COLOR_THEME["secondary"] if x >= 0 else self.COLOR_THEME["danger"]
                for x in data["monthly_return"]
            ]
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data["monthly_return"],
                    name="月度收益",
                    marker_color=colors,
                ),
                row=2,
                col=1,
            )

        # 4. 风险收益散点
        if "return" in data.columns and "volatility" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data["volatility"],
                    y=data["return"],
                    mode="markers",
                    name="风险收益",
                    marker=dict(
                        size=8,
                        color=data["return"],
                        colorscale="RdYlGn",
                        showscale=True,
                    ),
                ),
                row=2,
                col=2,
            )

        # 更新布局
        fig.update_layout(
            height=800,
            title_text="投资组合性能分析",
            showlegend=False,
        )

        # 导出
        image_path = self._export_chart(fig, self.DEFAULT_CONFIG)

        return {
            "image_path": image_path,
            "chart_type": "performance",
            "title": "投资组合性能分析",
        }

    def create_risk_chart(
        self,
        data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """创建风险分析图表"""
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=("VaR分析", "波动率走势", "贝塔系数", "相关性矩阵"),
        )

        # VaR
        if "var" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["var"],
                    name="VaR",
                    line=dict(color=self.COLOR_THEME["warning"]),
                ),
                row=1,
                col=1,
            )

        # 波动率
        if "volatility" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["volatility"],
                    name="波动率",
                    line=dict(color=self.COLOR_THEME["info"]),
                ),
                row=1,
                col=2,
            )

        # 贝塔系数
        if "beta" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data["beta"],
                    name="贝塔",
                    line=dict(color=self.COLOR_THEME["dark"]),
                ),
                row=2,
                col=1,
            )

        # 相关性
        if "correlation" in data.columns and isinstance(
            data["correlation"].iloc[0], pd.DataFrame
        ):
            corr_matrix = data["correlation"].iloc[0]
            fig.add_trace(
                go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.index,
                    colorscale="RdBu",
                ),
                row=2,
                col=2,
            )

        fig.update_layout(
            height=800,
            title_text="风险分析图表",
            showlegend=False,
        )

        image_path = self._export_chart(fig, self.DEFAULT_CONFIG)

        return {
            "image_path": image_path,
            "chart_type": "risk",
            "title": "风险分析图表",
        }

    def cleanup(self) -> None:
        """清理生成的图表文件"""
        for chart_path in self.generated_charts:
            try:
                if chart_path.exists():
                    chart_path.unlink()
            except Exception as e:
                logger.warning(f"删除图表文件失败 {chart_path}: {e}")

        self.generated_charts.clear()
        logger.info("图表文件清理完成")
