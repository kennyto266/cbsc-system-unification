#!/usr / bin / env python3
"""
Simplified System - Bollinger Bands Strategy
简化系统 - 布林带策略

基于布林带的突破策略。
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

from .base_strategy import BaseStrategy


class BollingerStrategy(BaseStrategy):
    """布林带突破策略"""

    def __init__(self):
        super().__init__("Bollinger_Bands")

    def _get_default_parameters(self) -> Dict[str, Any]:
        return {"period": 20, "std_dev": 2.0}

    def _get_description(self) -> str:
        return "布林带策略：价格突破上轨买入，跌破下轨卖出"

    def _get_optimization_ranges(self) -> Dict[str, Any]:
        return {"period": list(range(10, 31)), "std_dev": [1.5, 2.0, 2.5, 3.0]}

    def calculate_bollinger_bands(
        self, prices: pd.Series, period: int, std_dev: float
    ) -> Dict[str, pd.Series]:
        """
        计算布林带

        Args:
            prices: 价格序列
            period: 移动平均周期
            std_dev: 标准差倍数

        Returns:
            布林带指标字典
        """
        # 中轨 (简单移动平均线)
        middle_band = prices.rolling(window = period).mean()

        # 标准差
        rolling_std = prices.rolling(window = period).std()

        # 上轨
        upper_band = middle_band + (rolling_std * std_dev)

        # 下轨
        lower_band = middle_band - (rolling_std * std_dev)

        # 带宽 (可选指标)
        bandwidth = (upper_band - lower_band) / middle_band

        # %B (价格在布林带中的位置)
        percent_b = (prices - lower_band) / (upper_band - lower_band)

        return {
            "upper": upper_band,
            "middle": middle_band,
            "lower": lower_band,
            "bandwidth": bandwidth,
            "percent_b": percent_b,
        }

    def generate_signals(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> pd.Series:
        """
        生成布林带交易信号

        Args:
            data: 价格数据
            parameters: 策略参数

        Returns:
            交易信号序列 (1 = 买入, 0 = 持有, -1 = 卖出)
        """
        period = parameters.get("period", 20)
        std_dev = parameters.get("std_dev", 2.0)

        # 计算布林带
        bb_data = self.calculate_bollinger_bands(data["close"], period, std_dev)

        upper_band = bb_data["upper"]
        lower_band = bb_data["lower"]
        bb_data["percent_b"]

        # 生成信号
        signals = pd.Series(0, index = data.index)

        # 突破上轨买入信号
        signals[
            (data["close"] > upper_band)
            & (data["close"].shift(1) <= upper_band.shift(1))
        ] = 1

        # 跌破下轨卖出信号
        signals[
            (data["close"] < lower_band)
            & (data["close"].shift(1) >= lower_band.shift(1))
        ] = -1

        # 可选：基于%B指标的过滤
        # %B > 1 时确认强势买入
        # %B < 0 时确认强势卖出

        # 平滑信号：避免频繁交易
        signals = signals.ffill().fillna(0)

        return signals
