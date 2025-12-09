#!/usr/bin/env python3
"""
优化的策略信号生成器
Optimized strategy signal generators with GPU acceleration and caching
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class OptimizedStrategySignals:
    """优化的策略信号生成器"""

    def __init__(self, indicators_engine=None, gpu_manager=None):
        self.indicators = indicators_engine
        self.gpu_manager = gpu_manager

    def rsi_strategy_signals_optimized(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """优化的RSI策略信号生成"""
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        close = data['close']

        # 使用GPU或CPU计算RSI
        if self.gpu_manager and self.gpu_manager.is_gpu_available():
            rsi_values = self._calculate_rsi_gpu(close, period)
        else:
            rsi_values = self._calculate_rsi_cpu(close, period)

        # 转换为pandas Series
        if isinstance(rsi_values, np.ndarray):
            rsi_series = pd.Series(rsi_values, index=data.index, name='RSI')
        else:
            rsi_series = rsi_values

        # 生成交易信号 - 向量化操作
        buy_signals = (rsi_series < oversold) & (rsi_series.shift(1) >= oversold)
        sell_signals = (rsi_series > overbought) & (rsi_series.shift(1) <= overbought)

        return pd.DataFrame({
            'entries': buy_signals,
            'exits': sell_signals
        }, index=data.index)

    def macd_strategy_signals_optimized(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """优化的MACD策略信号生成"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        close = data['close']

        # 使用GPU或CPU计算MACD
        if self.gpu_manager and self.gpu_manager.is_gpu_available():
            macd_data = self._calculate_macd_gpu(close, fast, slow, signal)
        else:
            macd_data = self._calculate_macd_cpu(close, fast, slow, signal)

        macd_line = pd.Series(macd_data['MACD'], index=data.index, name='MACD')
        signal_line = pd.Series(macd_data['MACD_Signal'], index=data.index, name='Signal')

        # 生成交易信号 - 向量化操作
        golden_cross = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        death_cross = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        return pd.DataFrame({
            'entries': golden_cross,
            'exits': death_cross
        }, index=data.index)

    def bollinger_strategy_signals_optimized(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """优化的布林带策略信号生成"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)

        close = data['close']

        # 使用GPU或CPU计算布林带
        if self.gpu_manager and self.gpu_manager.is_gpu_available():
            bb_data = self._calculate_bollinger_gpu(close, period, std_dev)
        else:
            bb_data = self._calculate_bollinger_cpu(close, period, std_dev)

        bb_upper = pd.Series(bb_data['upper'], index=data.index, name='BB_Upper')
        bb_lower = pd.Series(bb_data['lower'], index=data.index, name='BB_Lower')

        # 生成交易信号 - 向量化操作
        price_cross_below_lower = (close < bb_lower) & (close.shift(1) >= bb_lower.shift(1))
        price_cross_above_upper = (close > bb_upper) & (close.shift(1) <= bb_upper.shift(1))

        return pd.DataFrame({
            'entries': price_cross_below_lower,
            'exits': price_cross_above_upper
        }, index=data.index)

    def dual_ma_strategy_signals_optimized(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """优化的双移动平均策略信号生成"""
        short_period = params.get('short_period', 20)
        long_period = params.get('long_period', 50)

        close = data['close']

        # 使用GPU或CPU计算移动平均
        if self.gpu_manager and self.gpu_manager.is_gpu_available():
            ma_data = self._calculate_ma_gpu(close, short_period, long_period)
        else:
            ma_data = self._calculate_ma_cpu(close, short_period, long_period)

        short_ma = pd.Series(ma_data['short_ma'], index=data.index, name='Short_MA')
        long_ma = pd.Series(ma_data['long_ma'], index=data.index, name='Long_MA')

        # 生成交易信号 - 向量化操作
        golden_cross = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
        death_cross = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

        return pd.DataFrame({
            'entries': golden_cross,
            'exits': death_cross
        }, index=data.index)

    def momentum_strategy_signals_optimized(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """优化的动量突破策略信号生成"""
        lookback = params.get('lookback', 20)
        threshold = params.get('threshold', 0.02)  # 2%突破

        close = data['close']

        # 计算动量
        momentum = close.pct_change(lookback)

        # 生成交易信号 - 向量化操作
        upward_cross = (momentum > threshold) & (momentum.shift(1) <= threshold)
        downward_cross = (momentum < -threshold) & (momentum.shift(1) >= -threshold)

        return pd.DataFrame({
            'entries': upward_cross,
            'exits': downward_cross
        }, index=data.index)

    def volatility_strategy_signals_optimized(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """优化的波动率突破策略信号生成"""
        atr_period = params.get('atr_period', 14)
        multiplier = params.get('multiplier', 2.0)

        close = data['close']
        high = data['high']
        low = data['low']

        # 使用GPU或CPU计算ATR
        if self.gpu_manager and self.gpu_manager.is_gpu_available():
            atr = self._calculate_atr_gpu(high, low, close, atr_period)
        else:
            atr = self._calculate_atr_cpu(high, low, close, atr_period)

        atr_series = pd.Series(atr, index=data.index, name='ATR')

        # 计算突破通道
        close_prev = close.shift(1)
        upper_band = close_prev + (atr_series * multiplier)
        lower_band = close_prev - (atr_series * multiplier)

        # 生成交易信号 - 向量化操作
        upward_breakout = (close > upper_band) & (close.shift(1) <= upper_band.shift(1))
        downward_breakout = (close < lower_band) & (close.shift(1) >= lower_band.shift(1))

        return pd.DataFrame({
            'entries': upward_breakout,
            'exits': downward_breakout
        }, index=data.index)

    # GPU计算方法
    def _calculate_rsi_gpu(self, prices, period=14):
        """GPU RSI计算"""
        if self.gpu_manager:
            indicators_config = {'rsi': {'period': period}}
            results = self.gpu_manager.compute_indicators(prices, indicators_config)
            return results.get('RSI', np.full(len(prices), 50.0))
        return self._calculate_rsi_cpu(prices, period)

    def _calculate_macd_gpu(self, prices, fast=12, slow=26, signal=9):
        """GPU MACD计算"""
        if self.gpu_manager:
            indicators_config = {'macd': {'fast': fast, 'slow': slow, 'signal': signal}}
            results = self.gpu_manager.compute_indicators(prices, indicators_config)
            return {
                'MACD': results.get('MACD', np.zeros(len(prices))),
                'MACD_Signal': results.get('MACD_Signal', np.zeros(len(prices)))
            }
        return self._calculate_macd_cpu(prices, fast, slow, signal)

    def _calculate_bollinger_gpu(self, prices, period=20, std_dev=2.0):
        """GPU布林带计算"""
        # 简化实现，实际中可以使用更复杂的GPU算法
        return self._calculate_bollinger_cpu(prices, period, std_dev)

    def _calculate_ma_gpu(self, prices, short_period=20, long_period=50):
        """GPU移动平均计算"""
        # 简化实现，实际中可以使用更复杂的GPU算法
        return self._calculate_ma_cpu(prices, short_period, long_period)

    def _calculate_atr_gpu(self, high, low, close, period=14):
        """GPU ATR计算"""
        # 简化实现，实际中可以使用更复杂的GPU算法
        return self._calculate_atr_cpu(high, low, close, period)

    # CPU计算方法
    def _calculate_rsi_cpu(self, prices, period=14):
        """CPU RSI计算"""
        if isinstance(prices, pd.Series):
            prices = prices.values

        delta = np.diff(prices, prepend=prices[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        # 使用pandas rolling计算，更高效
        if isinstance(prices, pd.Series):
            avg_gain = pd.Series(gain).rolling(window=period, min_periods=1).mean()
            avg_loss = pd.Series(loss).rolling(window=period, min_periods=1).mean()
        else:
            # 使用numpy滑动窗口
            avg_gain = np.convolve(gain, np.ones(period)/period, mode='same')
            avg_loss = np.convolve(loss, np.ones(period)/period, mode='same')

        rs = avg_gain / np.where(avg_loss == 0, np.nan, avg_loss)
        rsi = 100 - (100 / (1 + rs))
        rsi = np.nan_to_num(rsi, nan=50.0)

        return rsi

    def _calculate_macd_cpu(self, prices, fast=12, slow=26, signal=9):
        """CPU MACD计算"""
        if isinstance(prices, pd.Series):
            prices_series = prices
        else:
            prices_series = pd.Series(prices)

        # 使用pandas ewm，更高效
        ema_fast = prices_series.ewm(span=fast, adjust=False).mean()
        ema_slow = prices_series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()

        return {
            'MACD': macd_line.values,
            'MACD_Signal': signal_line.values
        }

    def _calculate_bollinger_cpu(self, prices, period=20, std_dev=2.0):
        """CPU布林带计算"""
        if isinstance(prices, pd.Series):
            prices_series = prices
        else:
            prices_series = pd.Series(prices)

        middle = prices_series.rolling(window=period, min_periods=1).mean()
        std = prices_series.rolling(window=period, min_periods=1).std()

        upper = middle + std * std_dev
        lower = middle - std * std_dev

        return {
            'upper': upper.values,
            'middle': middle.values,
            'lower': lower.values
        }

    def _calculate_ma_cpu(self, prices, short_period=20, long_period=50):
        """CPU移动平均计算"""
        if isinstance(prices, pd.Series):
            prices_series = prices
        else:
            prices_series = pd.Series(prices)

        short_ma = prices_series.rolling(window=short_period, min_periods=1).mean()
        long_ma = prices_series.rolling(window=long_period, min_periods=1).mean()

        return {
            'short_ma': short_ma.values,
            'long_ma': long_ma.values
        }

    def _calculate_atr_cpu(self, high, low, close, period=14):
        """CPU ATR计算"""
        if isinstance(high, pd.Series):
            high_series = high
            low_series = low
            close_series = close
        else:
            high_series = pd.Series(high)
            low_series = pd.Series(low)
            close_series = pd.Series(close)

        # 计算True Range
        tr1 = high_series - low_series
        tr2 = abs(high_series - close_series.shift(1))
        tr3 = abs(low_series - close_series.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=1).mean()

        return atr.fillna(0.0).values