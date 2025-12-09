#!/usr / bin / env python3
"""
Simplified System - RSI Strategy
简化系统 - RSI策略

基于RSI指标的均值回归策略。
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

from .base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """RSI均值回归策略"""

    def __init__(self):
        super().__init__("RSI_Mean_Reversion")

    def _get_default_parameters(self) -> Dict[str, Any]:
        return {"period": 14, "oversold": 30, "overbought": 70}

    def _get_description(self) -> str:
        return "RSI均值回归策略：在RSI超卖时买入，超买时卖出"

    def _get_optimization_ranges(self) -> Dict[str, Any]:
        return {
            "period": list(range(5, 51)),
            "oversold": list(range(20, 40)),
            "overbought": list(range(60, 80)),
        }

    def calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """
        计算RSI指标

        Args:
            prices: 价格序列
            period: RSI周期

        Returns:
            RSI序列
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window = period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window = period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> pd.Series:
        """
        生成RSI交易信号

        Args:
            data: 价格数据
            parameters: 策略参数

        Returns:
            交易信号序列 (1 = 买入, 0 = 持有, -1 = 卖出)
        """
        period = parameters.get("period", 14)
        oversold = parameters.get("oversold", 30)
        overbought = parameters.get("overbought", 70)

        # 计算RSI
        rsi = self.calculate_rsi(data["close"], period)

        # 生成信号
        signals = pd.Series(0, index = data.index)

        # RSI超卖时买入信号
        signals[rsi < oversold] = 1

        # RSI超买时卖出信号
        signals[rsi > overbought] = -1

        # 平滑信号：避免频繁交易
        signals = signals.ffill().fillna(0)

        return signals
