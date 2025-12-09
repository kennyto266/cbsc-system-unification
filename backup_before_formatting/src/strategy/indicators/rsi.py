"""
相对强度指数(RSI)指标实现

RSI是衡量价格变动速度和幅度的动量 oscillator 指标。
"""

from typing import List

import numpy as np
import pandas as pd

from ..traits import BaseIndicator
from . import register_indicator


@register_indicator(
    name="rsi",
    params_schema={
        "period": {"type": int, "min": 2, "max": 100, "default": 14},
        "column": {"type": str, "default": "close"},
    },
    description="Relative Strength Index - 相对强度指数",
    required_columns=["close"],
    output_columns=["rsi"],
)
class RSIIndicator(BaseIndicator):
    """相对强度指数(RSI)指标

    RSI测量价格变动的速度和幅度，通常在0 - 100之间波动：
    - RSI > 70: 可能超买
    - RSI < 30: 可能超卖

    计算公式：
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss

    Args:
        period: RSI周期，默认14
        column: 计算列名，默认'close'
    """

    def __init__(self, period: int = 14, column: str = "close") -> None:
        super().__init__("RSI", {"period": period, "column": column})
        self.period = period
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算RSI指标"""
        self.validate_input(data)

        if len(data) < self.period + 1:
            raise ValueError(
                f"数据长度 {len(data)} 小于RSI计算所需最小长度 {self.period + 1}"
            )

        result = data.copy()

        # 计算价格变化
        delta = result[self.column].diff()

        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # 计算平均收益和损失
        avg_gain = gain.rolling(window=self.period, min_periods=self.period).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=self.period).mean()

        # 使用Wilder平滑法进行后续计算
        avg_gain.iloc[self.period] = gain[: self.period].mean()
        avg_loss.iloc[self.period] = loss[: self.period].mean()

        for i in range(self.period + 1, len(data)):
            avg_gain.iloc[i] = (
                avg_gain.iloc[i - 1] * (self.period - 1) + gain.iloc[i]
            ) / self.period
            avg_loss.iloc[i] = (
                avg_loss.iloc[i - 1] * (self.period - 1) + loss.iloc[i]
            ) / self.period

        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        result["rsi"] = rsi

        return result[[self.column, "rsi"]] if self.column != "rsi" else result

    def get_required_columns(self) -> List[str]:
        return [self.column]

    def get_output_columns(self) -> List[str]:
        return ["rsi"]


@register_indicator(
    name="rsi_macd",
    params_schema={
        "rsi_period": {"type": int, "min": 2, "max": 100, "default": 14},
        "macd_fast": {"type": int, "min": 2, "max": 50, "default": 12},
        "macd_slow": {"type": int, "min": 10, "max": 100, "default": 26},
        "macd_signal": {"type": int, "min": 2, "max": 50, "default": 9},
    },
    description="RSI - MACD Hybrid - RSI和MACD组合指标",
    required_columns=["close"],
    output_columns=["rsi", "macd", "macd_signal", "macd_histogram"],
)
class RSI_MACDIndicator(BaseIndicator):
    """RSI和MACD组合指标

    同时计算RSI和MACD，用于更全面的动量分析。

    Args:
        rsi_period: RSI周期，默认14
        macd_fast: MACD快线周期，默认12
        macd_slow: MACD慢线周期，默认26
        macd_signal: MACD信号线周期，默认9
    """

    def __init__(
        self,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
    ) -> None:
        super().__init__(
            "RSI_MACD",
            {
                "rsi_period": rsi_period,
                "macd_fast": macd_fast,
                "macd_slow": macd_slow,
                "macd_signal": macd_signal,
            },
        )
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算RSI和MACD组合指标"""
        self.validate_input(data)

        result = data.copy()

        # 计算RSI
        delta = result["close"].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        avg_gain = gain.ewm(span=self.rsi_period).mean()
        avg_loss = loss.ewm(span=self.rsi_period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        result["rsi"] = rsi

        # 计算MACD
        ema_fast = result["close"].ewm(span=self.macd_fast).mean()
        ema_slow = result["close"].ewm(span=self.macd_slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=self.macd_signal).mean()
        macd_histogram = macd - macd_signal

        result["macd"] = macd
        result["macd_signal"] = macd_signal
        result["macd_histogram"] = macd_histogram

        return result

    def get_required_columns(self) -> List[str]:
        return ["close"]

    def get_output_columns(self) -> List[str]:
        return ["rsi", "macd", "macd_signal", "macd_histogram"]
