#!/usr/bin/env python3
"""
簡化系統 - 核心技術指標計算引擎
Simplified System - Core Technical Indicators Calculation Engine

高效、精確的技術指標計算，專注於量化交易核心需求
Efficient and precise technical indicator calculation focused on quantitative trading core needs
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any
import logging

logger = logging.getLogger(__name__)

class CoreIndicators:
    """
    核心技術指標計算引擎

    提供量化交易所需的最重要技術指標：
    - RSI (相對強弱指數)
    - MACD (移動平均收斂背離)
    - SMA/EMA (移動平均線)
    - Bollinger Bands (布林帶)
    - ATR (平均真實範圍)
    - Stochastic (隨機指標)
    - Williams %R (威廉指標)
    """

    def __init__(self):
        """初始化核心指標引擎"""
        self.cache = {}
        self.cache_timeout = 300  # 5分鐘緩存

        logger.info("Core Technical Indicators Engine initialized")

    # ==================== 趨勢指標 ====================

    def calculate_sma(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """
        計算簡單移動平均線 (Simple Moving Average)

        Args:
            prices: 價格序列
            period: 週期，默認20

        Returns:
            SMA序列
        """
        if len(prices) < period:
            logger.warning(f"Insufficient data for SMA{period}: need {period}, have {len(prices)}")
            return pd.Series([np.nan] * len(prices), index=prices.index)

        return prices.rolling(window=period, min_periods=1).mean()

    def calculate_ema(self, prices: pd.Series, period: int = 26) -> pd.Series:
        """
        計算指數移動平均線 (Exponential Moving Average)

        Args:
            prices: 價格序列
            period: 週期，默認26

        Returns:
            EMA序列
        """
        if len(prices) < period:
            logger.warning(f"Insufficient data for EMA{period}: need {period}, have {len(prices)}")
            return pd.Series([np.nan] * len(prices), index=prices.index)

        return prices.ewm(span=period, adjust=False).mean()

    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        計算MACD指標 (Moving Average Convergence Divergence)

        Args:
            prices: 價格序列
            fast: 快線週期，默認12
            slow: 慢線週期，默認26
            signal: 信號線週期，默認9

        Returns:
            包含MACD線、信號線、柱狀圖的字典
        """
        if len(prices) < slow:
            logger.warning(f"Insufficient data for MACD: need {slow}, have {len(prices)}")
            return {
                'macd': pd.Series([np.nan] * len(prices), index=prices.index),
                'signal': pd.Series([np.nan] * len(prices), index=prices.index),
                'histogram': pd.Series([np.nan] * len(prices), index=prices.index)
            }

        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }

    # ==================== 動量指標 ====================

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        計算相對強弱指數 (Relative Strength Index)

        Args:
            prices: 價格序列
            period: 週期，默認14

        Returns:
            RSI序列 (0-100)
        """
        if len(prices) < period + 1:
            logger.warning(f"Insufficient data for RSI{period}: need {period + 1}, have {len(prices)}")
            return pd.Series([50.0] * len(prices), index=prices.index)

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()

        # 避免除零錯誤
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        # 處理無窮大和NaN值
        rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50.0)

        return rsi

    def calculate_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Dict[str, pd.Series]:
        """
        計算隨機指標 (Stochastic Oscillator)

        Args:
            high: 最高價序列
            low: 最低價序列
            close: 收盤價序列
            k_period: %K週期，默認14
            d_period: %D週期，默認3

        Returns:
            包含%K和%D的字典
        """
        if len(close) < k_period:
            logger.warning(f"Insufficient data for Stochastic: need {k_period}, have {len(close)}")
            return {
                'k_percent': pd.Series([50.0] * len(close), index=close.index),
                'd_percent': pd.Series([50.0] * len(close), index=close.index)
            }

        lowest_low = low.rolling(window=k_period, min_periods=1).min()
        highest_high = high.rolling(window=k_period, min_periods=1).max()

        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        k_percent = k_percent.replace([np.inf, -np.inf], 50.0).fillna(50.0)

        d_percent = k_percent.rolling(window=d_period, min_periods=1).mean()

        return {
            'k_percent': k_percent,
            'd_percent': d_percent
        }

    def calculate_williams_r(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        計算威廉指標 (Williams %R)

        Args:
            high: 最高價序列
            low: 最低價序列
            close: 收盤價序列
            period: 週期，默認14

        Returns:
            Williams %R序列 (-100到0)
        """
        if len(close) < period:
            logger.warning(f"Insufficient data for Williams %R: need {period}, have {len(close)}")
            return pd.Series([-50.0] * len(close), index=close.index)

        highest_high = high.rolling(window=period, min_periods=1).max()
        lowest_low = low.rolling(window=period, min_periods=1).min()

        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        williams_r = williams_r.replace([np.inf, -np.inf], -50.0).fillna(-50.0)

        return williams_r

    # ==================== 波動率指標 ====================

    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        計算布林帶 (Bollinger Bands)

        Args:
            prices: 價格序列
            period: 週期，默認20
            std_dev: 標準差倍數，默認2.0

        Returns:
            包含上軌、中軌、下軌的字典
        """
        if len(prices) < period:
            logger.warning(f"Insufficient data for Bollinger Bands: need {period}, have {len(prices)}")
            middle = prices.rolling(window=period, min_periods=1).mean()
            std = prices.rolling(window=period, min_periods=1).std()
            return {
                'upper': middle + std * std_dev,
                'middle': middle,
                'lower': middle - std * std_dev,
                'width': (middle + std * std_dev - (middle - std * std_dev)) / middle
            }

        middle = prices.rolling(window=period, min_periods=1).mean()
        std = prices.rolling(window=period, min_periods=1).std()

        upper = middle + std * std_dev
        lower = middle - std * std_dev
        width = (upper - lower) / middle

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'width': width
        }

    def calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        計算平均真實範圍 (Average True Range)

        Args:
            high: 最高價序列
            low: 最低價序列
            close: 收盤價序列
            period: 週期，默認14

        Returns:
            ATR序列
        """
        if len(close) < period:
            logger.warning(f"Insufficient data for ATR: need {period}, have {len(close)}")
            return pd.Series([0.0] * len(close), index=close.index)

        # 計算真實範圍
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=1).mean()

        return atr.fillna(0.0)

    # ==================== 成交量指標 ====================

    def calculate_volume_ma(self, volume: pd.Series, period: int = 20) -> pd.Series:
        """
        計算成交量移動平均線

        Args:
            volume: 成交量序列
            period: 週期，默認20

        Returns:
            成交量移動平均線序列
        """
        if len(volume) < period:
            logger.warning(f"Insufficient data for Volume MA: need {period}, have {len(volume)}")
            return volume.rolling(window=period, min_periods=1).mean()

        return volume.rolling(window=period, min_periods=1).mean()

    # ==================== 綜合計算方法 ====================

    def calculate_all_indicators(
        self,
        data: pd.DataFrame,
        indicators: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        計算所有核心技術指標

        Args:
            data: OHLCV數據框，必須包含 open, high, low, close, volume 列
            indicators: 要計算的指標列表，None表示計算全部

        Returns:
            包含所有指標結果的字典
        """
        if indicators is None:
            indicators = ['RSI', 'MACD', 'SMA', 'EMA', 'BOLLINGER', 'ATR', 'VOLUME_MA', 'STOCH', 'WILLIAMS_R']

        results = {}

        # 驗證數據
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']

        try:
            # 趨勢指標
            if 'SMA' in indicators:
                results['SMA_20'] = self.calculate_sma(close, 20)
                results['SMA_50'] = self.calculate_sma(close, 50)
                results['SMA_200'] = self.calculate_sma(close, 200)

            if 'EMA' in indicators:
                results['EMA_12'] = self.calculate_ema(close, 12)
                results['EMA_26'] = self.calculate_ema(close, 26)

            if 'MACD' in indicators:
                macd_results = self.calculate_macd(close)
                results['MACD'] = macd_results['macd']
                results['MACD_Signal'] = macd_results['signal']
                results['MACD_Histogram'] = macd_results['histogram']

            # 動量指標
            if 'RSI' in indicators:
                results['RSI'] = self.calculate_rsi(close)

            if 'STOCH' in indicators:
                stoch_results = self.calculate_stochastic(high, low, close)
                results['Stoch_K'] = stoch_results['k_percent']
                results['Stoch_D'] = stoch_results['d_percent']

            if 'WILLIAMS_R' in indicators:
                results['Williams_R'] = self.calculate_williams_r(high, low, close)

            # 波動率指標
            if 'BOLLINGER' in indicators:
                bb_results = self.calculate_bollinger_bands(close)
                results['BB_Upper'] = bb_results['upper']
                results['BB_Middle'] = bb_results['middle']
                results['BB_Lower'] = bb_results['lower']
                results['BB_Width'] = bb_results['width']

            if 'ATR' in indicators:
                results['ATR'] = self.calculate_atr(high, low, close)

            # 成交量指標
            if 'VOLUME_MA' in indicators:
                results['Volume_MA_20'] = self.calculate_volume_ma(volume, 20)

            # 添加計算元數據
            results['_metadata'] = {
                'data_points': len(data),
                'indicators_calculated': indicators,
                'calculation_time': pd.Timestamp.now()
            }

            logger.info(f"Successfully calculated {len(indicators)} indicator types for {len(data)} data points")

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            raise

        return results

    def get_latest_values(self, indicators_data: Dict[str, pd.Series]) -> Dict[str, float]:
        """
        獲取所有指標的最新值

        Args:
            indicators_data: 指標數據字典

        Returns:
            最新值字典
        """
        latest_values = {}

        for name, series in indicators_data.items():
            if name.startswith('_'):  # 跳過元數據
                continue

            if isinstance(series, pd.Series) and len(series) > 0:
                latest_values[name] = float(series.iloc[-1])
            else:
                latest_values[name] = None

        return latest_values

# 全局實例
core_indicators = CoreIndicators()

# 便利函數
def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """便利函數：計算RSI"""
    return core_indicators.calculate_rsi(prices, period)

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """便利函數：計算MACD"""
    return core_indicators.calculate_macd(prices, fast, slow, signal)

def calculate_sma(prices: pd.Series, period: int = 20) -> pd.Series:
    """便利函數：計算SMA"""
    return core_indicators.calculate_sma(prices, period)

def calculate_all_indicators(data: pd.DataFrame, indicators: Optional[List[str]] = None) -> Dict[str, Any]:
    """便利函數：計算所有指標"""
    return core_indicators.calculate_all_indicators(data, indicators)