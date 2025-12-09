#!/usr / bin / env python3
"""
Simplified System - MACD Strategy
简化系统 - MACD策略

基于MACD指标的趋势跟踪策略。
"""

from typing import Any, Dict

import numpy as np
import pandas as pd

from .base_strategy import BaseStrategy


class MACDStrategy(BaseStrategy):
    """MACD趋势跟踪策略"""

    def __init__(self):
        super().__init__("MACD_Crossover")

    def _get_default_parameters(self) -> Dict[str, Any]:
        return {"fast_period": 12, "slow_period": 26, "signal_period": 9}

    def _get_description(self) -> str:
        return "MACD交叉策略：快线上穿慢线买入，快线下穿慢线卖出"

    def _get_optimization_ranges(self) -> Dict[str, Any]:
        return {
            "fast_period": list(range(8, 21)),
            "slow_period": list(range(20, 41)),
            "signal_period": list(range(5, 15)),
        }

    def calculate_macd(
        self, prices: pd.Series, fast: int, slow: int, signal: int
    ) -> Dict[str, pd.Series]:
        """
        计算MACD指标

        Args:
            prices: 价格序列
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            MACD指标字典
        """
        # 计算指数移动平均线
        ema_fast = prices.ewm(span = fast).mean()
        ema_slow = prices.ewm(span = slow).mean()

        # MACD线
        macd_line = ema_fast - ema_slow

        # 信号线
        signal_line = macd_line.ewm(span = signal).mean()

        # 柱状图
        histogram = macd_line - signal_line

        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    def generate_signals(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> pd.Series:
        """
        生成MACD交易信号

        Args:
            data: 价格数据
            parameters: 策略参数

        Returns:
            交易信号序列 (1 = 买入, 0 = 持有, -1 = 卖出)
        """
        fast = parameters.get("fast_period", 12)
        slow = parameters.get("slow_period", 26)
        signal = parameters.get("signal_period", 9)

        # 验证参数
        if fast >= slow:
            raise ValueError("Fast period must be less than slow period")

        # 计算MACD
        macd_data = self.calculate_macd(data["close"], fast, slow, signal)

        macd_line = macd_data["macd"]
        signal_line = macd_data["signal"]
        macd_data["histogram"]

        # 生成信号
        signals = pd.Series(0, index = data.index)

        # MACD金叉买入信号 (MACD线上穿信号线)
        signals[
            (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        ] = 1

        # MACD死叉卖出信号 (MACD线下穿信号线)
        signals[
            (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
        ] = -1

        # 柱状图确认 (可选)
        # 当柱状图由负转正时确认买入信号
        # 当柱状图由正转负时确认卖出信号

        return signals
