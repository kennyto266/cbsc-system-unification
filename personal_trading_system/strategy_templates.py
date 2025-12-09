#!/usr/bin/env python3
"""
Strategy Templates
策略模板
基于VectorBT实现的常用技术指标策略
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any
import logging

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    vbt = None

logger = logging.getLogger(__name__)


class BaseStrategy:
    """策略基类"""

    def __init__(self, name: str):
        self.name = name

    def generate_signals(self, data: pd.DataFrame, **params) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成交易信号

        Args:
            data: OHLCV数据
            **params: 策略参数

        Returns:
            (entries, exits) 交易信号数组
        """
        raise NotImplementedError("子类必须实现此方法")

    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数"""
        raise NotImplementedError("子类必须实现此方法")

    def get_param_grid(self) -> Dict[str, list]:
        """获取参数优化网格"""
        raise NotImplementedError("子类必须实现此方法")


class RSIStrategy(BaseStrategy):
    """
    RSI策略
    基于相对强弱指数的均值回归策略
    """

    def __init__(self):
        super().__init__("RSI Mean Reversion")

    def generate_signals(
        self,
        data: pd.DataFrame,
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成RSI交易信号

        Args:
            data: OHLCV数据
            period: RSI周期
            oversold: 超卖线
            overbought: 超买线

        Returns:
            (entries, exits) 交易信号数组
        """
        if VECTORBT_AVAILABLE:
            return self._generate_signals_vectorbt(data, period, oversold, overbought)
        else:
            return self._generate_signals_manual(data, period, oversold, overbought)

    def _generate_signals_vectorbt(
        self,
        data: pd.DataFrame,
        period: int,
        oversold: float,
        overbought: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """使用VectorBT生成RSI信号"""
        close = data['close']

        # 计算RSI
        rsi = vbt.RSI.run(close, window=period)

        # 生成信号
        entries = rsi.rsi.vbt.crossed_below(oversold)
        exits = rsi.rsi.vbt.crossed_above(overbought)

        return entries.values, exits.values

    def _generate_signals_manual(
        self,
        data: pd.DataFrame,
        period: int,
        oversold: float,
        overbought: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """手动计算RSI信号"""
        close = data['close'].values

        # 计算价格变化
        delta = np.diff(close)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        # 计算平均增益和损失
        avg_gain = pd.Series(gain).rolling(window=period).mean()
        avg_loss = pd.Series(loss).rolling(window=period).mean()

        # 计算RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # 生成信号
        entries = (rsi < oversold).values
        exits = (rsi > overbought).values

        # 确保数组长度一致
        entries = np.concatenate([[False], entries])
        exits = np.concatenate([[False], exits])

        return entries, exits

    def get_default_params(self) -> Dict[str, Any]:
        return {
            'period': 14,
            'oversold': 30,
            'overbought': 70
        }

    def get_param_grid(self) -> Dict[str, list]:
        return {
            'period': [10, 14, 21],
            'oversold': [20, 30, 35],
            'overbought': [65, 70, 80]
        }


class MACDStrategy(BaseStrategy):
    """
    MACD策略
    基于移动平均收敛发散指标的动量策略
    """

    def __init__(self):
        super().__init__("MACD Crossover")

    def generate_signals(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成MACD交易信号

        Args:
            data: OHLCV数据
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期

        Returns:
            (entries, exits) 交易信号数组
        """
        if VECTORBT_AVAILABLE:
            return self._generate_signals_vectorbt(data, fast_period, slow_period, signal_period)
        else:
            return self._generate_signals_manual(data, fast_period, slow_period, signal_period)

    def _generate_signals_vectorbt(
        self,
        data: pd.DataFrame,
        fast_period: int,
        slow_period: int,
        signal_period: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """使用VectorBT生成MACD信号"""
        close = data['close']

        # 计算MACD
        macd = vbt.MACD.run(
            close,
            fast_window=fast_period,
            slow_window=slow_period,
            signal_window=signal_period
        )

        # 生成信号：MACD线上穿信号线买入，下穿卖出
        entries = macd.macd.vbt.crossed_above(macd.signal)
        exits = macd.macd.vbt.crossed_below(macd.signal)

        return entries.values, exits.values

    def _generate_signals_manual(
        self,
        data: pd.DataFrame,
        fast_period: int,
        slow_period: int,
        signal_period: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """手动计算MACD信号"""
        close = data['close']

        # 计算指数移动平均
        ema_fast = close.ewm(span=fast_period).mean()
        ema_slow = close.ewm(span=slow_period).mean()

        # 计算MACD线
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()

        # 生成信号
        entries = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        exits = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        return entries.values, exits.values

    def get_default_params(self) -> Dict[str, Any]:
        return {
            'fast_period': 12,
            'slow_period': 26,
            'signal_period': 9
        }

    def get_param_grid(self) -> Dict[str, list]:
        return {
            'fast_period': [8, 12, 16],
            'slow_period': [21, 26, 34],
            'signal_period': [6, 9, 12]
        }


class MAStrategy(BaseStrategy):
    """
    移动平均策略
    基于移动平均线的趋势跟踪策略
    """

    def __init__(self):
        super().__init__("Moving Average Crossover")

    def generate_signals(
        self,
        data: pd.DataFrame,
        short_period: int = 20,
        long_period: int = 50,
        use_ema: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成移动平均交易信号

        Args:
            data: OHLCV数据
            short_period: 短期均线周期
            long_period: 长期均线周期
            use_ema: 是否使用指数移动平均

        Returns:
            (entries, exits) 交易信号数组
        """
        close = data['close']

        # 计算移动平均
        if use_ema:
            short_ma = close.ewm(span=short_period).mean()
            long_ma = close.ewm(span=long_period).mean()
        else:
            short_ma = close.rolling(window=short_period).mean()
            long_ma = close.rolling(window=long_period).mean()

        # 生成信号：金叉买入，死叉卖出
        entries = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        exits = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

        return entries.values, exits.values

    def get_default_params(self) -> Dict[str, Any]:
        return {
            'short_period': 20,
            'long_period': 50,
            'use_ema': False
        }

    def get_param_grid(self) -> Dict[str, list]:
        return {
            'short_period': [10, 20, 30],
            'long_period': [40, 50, 60],
            'use_ema': [True, False]
        }


class BBStrategy(BaseStrategy):
    """
    布林带策略
    基于布林带的突破策略
    """

    def __init__(self):
        super().__init__("Bollinger Bands Breakout")

    def generate_signals(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        strategy: str = 'breakout'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成布林带交易信号

        Args:
            data: OHLCV数据
            period: 布林带周期
            std_dev: 标准差倍数
            strategy: 策略类型 ('breakout' 或 'reversion')

        Returns:
            (entries, exits) 交易信号数组
        """
        if VECTORBT_AVAILABLE:
            return self._generate_signals_vectorbt(data, period, std_dev, strategy)
        else:
            return self._generate_signals_manual(data, period, std_dev, strategy)

    def _generate_signals_vectorbt(
        self,
        data: pd.DataFrame,
        period: int,
        std_dev: float,
        strategy: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """使用VectorBT生成布林带信号"""
        close = data['close']

        # 计算布林带
        bb = vbt.BBANDS.run(close, window=period, std=std_dev)

        if strategy == 'breakout':
            # 突破策略：价格突破上轨买入，跌破下轨卖出
            entries = close.vbt.crossed_above(bb.upper)
            exits = close.vbt.crossed_below(bb.lower)
        else:
            # 均值回归策略：价格跌破下轨买入，涨破上轨卖出
            entries = close.vbt.crossed_below(bb.lower)
            exits = close.vbt.crossed_above(bb.upper)

        return entries.values, exits.values

    def _generate_signals_manual(
        self,
        data: pd.DataFrame,
        period: int,
        std_dev: float,
        strategy: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """手动计算布林带信号"""
        close = data['close']

        # 计算布林带
        sma = close.rolling(window=period).mean()
        rolling_std = close.rolling(window=period).std()
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)

        if strategy == 'breakout':
            # 突破策略
            entries = (close > upper_band) & (close.shift(1) <= upper_band.shift(1))
            exits = (close < lower_band) & (close.shift(1) >= lower_band.shift(1))
        else:
            # 均值回归策略
            entries = (close < lower_band) & (close.shift(1) >= lower_band.shift(1))
            exits = (close > upper_band) & (close.shift(1) <= upper_band.shift(1))

        return entries.values, exits.values

    def get_default_params(self) -> Dict[str, Any]:
        return {
            'period': 20,
            'std_dev': 2.0,
            'strategy': 'breakout'
        }

    def get_param_grid(self) -> Dict[str, list]:
        return {
            'period': [15, 20, 25],
            'std_dev': [1.5, 2.0, 2.5],
            'strategy': ['breakout', 'reversion']
        }


class StrategyFactory:
    """策略工厂类"""

    _strategies = {
        'RSI': RSIStrategy,
        'MACD': MACDStrategy,
        'MA': MAStrategy,
        'BB': BBStrategy
    }

    @classmethod
    def create_strategy(cls, strategy_name: str) -> BaseStrategy:
        """
        创建策略实例

        Args:
            strategy_name: 策略名称

        Returns:
            BaseStrategy: 策略实例
        """
        if strategy_name not in cls._strategies:
            raise ValueError(f"不支持的策略: {strategy_name}")

        return cls._strategies[strategy_name]()

    @classmethod
    def get_available_strategies(cls) -> list:
        """获取可用策略列表"""
        return list(cls._strategies.keys())

    @classmethod
    def get_strategy_info(cls, strategy_name: str) -> Dict[str, Any]:
        """
        获取策略信息

        Args:
            strategy_name: 策略名称

        Returns:
            策略信息字典
        """
        if strategy_name not in cls._strategies:
            raise ValueError(f"不支持的策略: {strategy_name}")

        strategy = cls.create_strategy(strategy_name)
        return {
            'name': strategy.name,
            'default_params': strategy.get_default_params(),
            'param_grid': strategy.get_param_grid()
        }


def get_strategy_function(strategy_name: str):
    """
    获取策略函数，用于与VectorBT引擎集成

    Args:
        strategy_name: 策略名称

    Returns:
        策略函数
    """
    if strategy_name not in StrategyFactory._strategies:
        raise ValueError(f"不支持的策略: {strategy_name}")

    def strategy_func(data: pd.DataFrame, **params):
        strategy = StrategyFactory.create_strategy(strategy_name)
        return strategy.generate_signals(data, **params)

    return strategy_func


# 导出的策略别名
RSIStrategy = RSIStrategy
MACDStrategy = MACDStrategy
MAStrategy = MAStrategy
BBStrategy = BBStrategy