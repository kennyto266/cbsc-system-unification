"""
MACD指标实现

MACD(Moving Average Convergence Divergence)是趋势跟踪动量指标。
"""

from typing import List

import numpy as np
import pandas as pd

from ..traits import BaseIndicator
from . import register_indicator


@register_indicator(
    name="macd",
    params_schema={
        "fast_period": {"type": int, "min": 2, "max": 100, "default": 12},
        "slow_period": {"type": int, "min": 10, "max": 200, "default": 26},
        "signal_period": {"type": int, "min": 2, "max": 50, "default": 9},
        "column": {"type": str, "default": "close"},
    },
    description="MACD - Moving Average Convergence Divergence",
    required_columns=["close"],
    output_columns=["macd", "macd_signal", "macd_histogram"],
)
class MACDIndicator(BaseIndicator):
    """MACD(指数平滑异同移动平均)指标

    MACD由三部分组成：
    1. MACD线：快线EMA - 慢线EMA
    2. 信号线：MACD线的EMA
    3. 柱状图：MACD线 - 信号线

    常用交易信号：
    - MACD线上穿信号线：买入信号
    - MACD线下穿信号线：卖出信号
    - MACD线在零轴上方：上升趋势
    - MACD线在零轴下方：下降趋势

    Args:
        fast_period: 快线周期，默认12
        slow_period: 慢线周期，默认26
        signal_period: 信号线周期，默认9
        column: 计算列名，默认'close'
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "close",
    ) -> None:
        super().__init__(
            "MACD",
            {
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period,
                "column": column,
            },
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.column = column

        # 验证参数
        if slow_period <= fast_period:
            raise ValueError("slow_period 必须大于 fast_period")

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算MACD指标"""
        self.validate_input(data)

        if len(data) < self.slow_period:
            raise ValueError(f"数据长度 {len(data)} 小于慢线周期 {self.slow_period}")

        result = data.copy()

        # 计算快线和慢线EMA
        ema_fast = result[self.column].ewm(span=self.fast_period).mean()
        ema_slow = result[self.column].ewm(span=self.slow_period).mean()

        # 计算MACD线
        macd_line = ema_fast - ema_slow

        # 计算信号线（MACD线的EMA）
        macd_signal = macd_line.ewm(span=self.signal_period).mean()

        # 计算柱状图
        macd_histogram = macd_line - macd_signal

        result["macd"] = macd_line
        result["macd_signal"] = macd_signal
        result["macd_histogram"] = macd_histogram

        return result

    def get_required_columns(self) -> List[str]:
        return [self.column]

    def get_output_columns(self) -> List[str]:
        return ["macd", "macd_signal", "macd_histogram"]


@register_indicator(
    name="macd_extended",
    params_schema={
        "fast_period": {"type": int, "min": 2, "max": 100, "default": 12},
        "slow_period": {"type": int, "min": 10, "max": 200, "default": 26},
        "signal_period": {"type": int, "min": 2, "max": 50, "default": 9},
        "histogram_period": {"type": int, "min": 1, "max": 20, "default": 5},
    },
    description="Extended MACD - 扩展MACD指标",
    required_columns=["close"],
    output_columns=[
        "macd",
        "macd_signal",
        "macd_histogram",
        "macd_histogram_ema",
    ],
)
class MACDExtendedIndicator(BaseIndicator):
    """扩展MACD指标

    在标准MACD基础上添加柱状图的EMA，提供更平滑的信号。

    Args:
        fast_period: 快线周期，默认12
        slow_period: 慢线周期，默认26
        signal_period: 信号线周期，默认9
        histogram_period: 柱状图EMA周期，默认5
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        histogram_period: int = 5,
    ) -> None:
        super().__init__(
            "MACD_Extended",
            {
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period,
                "histogram_period": histogram_period,
            },
        )
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.histogram_period = histogram_period

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算扩展MACD指标"""
        self.validate_input(data)

        if len(data) < self.slow_period:
            raise ValueError(f"数据长度 {len(data)} 小于慢线周期 {self.slow_period}")

        result = data.copy()

        # 计算标准MACD
        ema_fast = result["close"].ewm(span=self.fast_period).mean()
        ema_slow = result["close"].ewm(span=self.slow_period).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=self.signal_period).mean()
        macd_histogram = macd_line - macd_signal

        # 计算柱状图的EMA
        macd_histogram_ema = macd_histogram.ewm(span=self.histogram_period).mean()

        result["macd"] = macd_line
        result["macd_signal"] = macd_signal
        result["macd_histogram"] = macd_histogram
        result["macd_histogram_ema"] = macd_histogram_ema

        return result

    def get_required_columns(self) -> List[str]:
        return ["close"]

    def get_output_columns(self) -> List[str]:
        return [
            "macd",
            "macd_signal",
            "macd_histogram",
            "macd_histogram_ema",
        ]
