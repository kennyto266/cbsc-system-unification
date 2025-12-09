"""
移动平均线指标实现

提供简单移动平均(SMA)、指数移动平均(EMA)和加权移动平均(WMA)。
"""

from typing import List

import numpy as np
import pandas as pd

from ..traits import BaseIndicator
from . import register_indicator


@register_indicator(
    name="sma",
    params_schema={
        "period": {"type": int, "min": 1, "max": 500, "default": 20},
        "column": {"type": str, "default": "close"},
    },
    description="Simple Moving Average - 简单移动平均",
    required_columns=["close"],
    output_columns=["sma"],
)
class SMAIndicator(BaseIndicator):
    """简单移动平均线指标

    计算指定周期的简单移动平均值。
    SMA = (P1 + P2 + ... + Pn) / n

    Args:
        period: 移动平均周期，默认20
        column: 计算列名，默认'close'
    """

    def __init__(self, period: int = 20, column: str = "close") -> None:
        super().__init__("SMA", {"period": period, "column": column})
        self.period = period
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算简单移动平均"""
        self.validate_input(data)

        if len(data) < self.period:
            raise ValueError(f"数据长度 {len(data)} 小于周期 {self.period}")

        result = data.copy()
        result["sma"] = (
            result[self.column].rolling(window=self.period, min_periods=1).mean()
        )

        return result[[self.column, "sma"]] if self.column != "sma" else result

    def get_required_columns(self) -> List[str]:
        return [self.column]

    def get_output_columns(self) -> List[str]:
        return ["sma"]


@register_indicator(
    name="ema",
    params_schema={
        "period": {"type": int, "min": 1, "max": 500, "default": 20},
        "column": {"type": str, "default": "close"},
    },
    description="Exponential Moving Average - 指数移动平均",
    required_columns=["close"],
    output_columns=["ema"],
)
class EMAIndicator(BaseIndicator):
    """指数移动平均线指标

    使用指数加权移动平均，对近期价格给予更高权重。
    EMA = (Close * k) + (EMA_previous * (1 - k))
    其中 k = 2 / (period + 1)

    Args:
        period: 移动平均周期，默认20
        column: 计算列名，默认'close'
    """

    def __init__(self, period: int = 20, column: str = "close") -> None:
        super().__init__("EMA", {"period": period, "column": column})
        self.period = period
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算指数移动平均"""
        self.validate_input(data)

        if len(data) < self.period:
            raise ValueError(f"数据长度 {len(data)} 小于周期 {self.period}")

        result = data.copy()
        result["ema"] = result[self.column].ewm(span=self.period, adjust=False).mean()

        return result[[self.column, "ema"]] if self.column != "ema" else result

    def get_required_columns(self) -> List[str]:
        return [self.column]

    def get_output_columns(self) -> List[str]:
        return ["ema"]


@register_indicator(
    name="wma",
    params_schema={
        "period": {"type": int, "min": 1, "max": 500, "default": 20},
        "column": {"type": str, "default": "close"},
    },
    description="Weighted Moving Average - 加权移动平均",
    required_columns=["close"],
    output_columns=["wma"],
)
class WMAIndicator(BaseIndicator):
    """加权移动平均线指标

    为每个价格点分配不同的权重，越近期的价格权重越大。
    WMA = (P1 * n + P2 * (n - 1) + ... + Pn * 1) / (n + (n - 1) + ... + 1)

    Args:
        period: 移动平均周期，默认20
        column: 计算列名，默认'close'
    """

    def __init__(self, period: int = 20, column: str = "close") -> None:
        super().__init__("WMA", {"period": period, "column": column})
        self.period = period
        self.column = column

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算加权移动平均"""
        self.validate_input(data)

        if len(data) < self.period:
            raise ValueError(f"数据长度 {len(data)} 小于周期 {self.period}")

        result = data.copy()

        # 计算权重
        weights = np.arange(1, self.period + 1)

        # 计算WMA
        def wma_calc(x):
            if len(x) < self.period:
                return x.mean()
            return np.dot(x, weights) / weights.sum()

        result["wma"] = (
            result[self.column].rolling(window=self.period).apply(wma_calc, raw=True)
        )

        return result[[self.column, "wma"]] if self.column != "wma" else result

    def get_required_columns(self) -> List[str]:
        return [self.column]

    def get_output_columns(self) -> List[str]:
        return ["wma"]


@register_indicator(
    name="vwma",
    params_schema={
        "period": {"type": int, "min": 1, "max": 500, "default": 20},
    },
    description="Volume Weighted Moving Average - 成交量加权移动平均",
    required_columns=["close", "volume"],
    output_columns=["vwma"],
)
class VWMAIndicator(BaseIndicator):
    """成交量加权移动平均线指标

    根据成交量对价格进行加权平均，成交量大的时期权重更高。

    Args:
        period: 移动平均周期，默认20
    """

    def __init__(self, period: int = 20) -> None:
        super().__init__("VWMA", {"period": period})
        self.period = period

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算成交量加权移动平均"""
        self.validate_input(data)

        if "volume" not in data.columns:
            raise ValueError("数据中缺少 'volume' 列")

        if len(data) < self.period:
            raise ValueError(f"数据长度 {len(data)} 小于周期 {self.period}")

        result = data.copy()

        # 计算VWMA
        def vwma_calc(window):
            if len(window) < self.period:
                return window["close"].mean()

            return (window["close"] * window["volume"]).sum() / window["volume"].sum()

        result["vwma"] = result.rolling(window=self.period).apply(vwma_calc, raw=False)

        return result

    def get_required_columns(self) -> List[str]:
        return ["close", "volume"]

    def get_output_columns(self) -> List[str]:
        return ["vwma"]
