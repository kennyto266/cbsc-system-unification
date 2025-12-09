#!/usr/bin/env python3
"""
Expanded Trading Strategies Library
擴展交易策略庫 - 25種專業交易策略

Based on VectorBT professional backtesting engine
基於VectorBT專業回測引擎
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
import logging

try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False
    logging.warning("VectorBT not available")

logger = logging.getLogger(__name__)

class ExpandedStrategies:
    """
    擴展策略庫 - 包含25種專業交易策略

    Categories:
    1. 趨勢策略 (Trend Following)
    2. 均值回歸策略 (Mean Reversion)
    3. 波動率策略 (Volatility)
    4. 價格行為策略 (Price Action)
    5. 進階組合策略 (Advanced Combination)
    """

    STRATEGY_REGISTRY = {
        # 趨勢策略
        "RSI_MEAN_REVERSION": "_rsi_mean_reversion",
        "MACD_CROSSOVER": "_macd_crossover",
        "DUAL_MOVING_AVERAGE": "_dual_moving_average",
        "TRIPLE_MOVING_AVERAGE": "_triple_moving_average",
        "ADX_MOMENTUM": "_adx_momentum",
        "PARABOLIC_SAR": "_parabolic_sar",

        # 均值回歸策略
        "BOLLINGER_BANDS": "_bollinger_bands",
        "STOCHASTIC_OVERSOLD": "_stochastic_oversold",
        "WILLIAMS_R": "_williams_r",
        "COMMODITY_CHANNEL_INDEX": "_commodity_channel_index",
        "RELATIVE_VIGOR_INDEX": "_relative_vigor_index",

        # 波動率策略
        "VOLATILITY_BREAKOUT": "_volatility_breakout",
        "AVERAGE_TRUE_RANGE": "_average_true_range",
        "KELTNER_CHANNELS": "_keltner_channels",
        "DONCHIAN_CHANNELS": "_donchian_channels",

        # 價格行為策略
        "MOMENTUM_BREAKOUT": "_momentum_breakout",
        "PRICE_RATE_CHANGE": "_price_rate_change",
        "ON_BALANCE_VOLUME": "_on_balance_volume",
        "VOLUME_WEIGHTED_AVERAGE_PRICE": "_volume_weighted_average_price",

        # 進階組合策略
        "RSI_MACD_CONFLUENCE": "_rsi_macd_confluence",
        "BOLLINGER_RSI_FILTER": "_bollinger_rsi_filter",
        "MULTI_TIMEFRAME_RSI": "_multi_timeframe_rsi",
        "VOLATILITY_ADJUSTED_RSI": "_volatility_adjusted_rsi",
        "ICHIMOKU_CLOUD": "_ichimoku_cloud",
        "ELDER_RAY_SYSTEM": "_elder_ray_system"
    }

    def __init__(self):
        """初始化擴展策略庫"""
        self.strategies = list(self.STRATEGY_REGISTRY.keys())
        logger.info(f"Expanded strategies initialized: {len(self.strategies)} strategies")

    def generate_signals(self, data: pd.DataFrame, strategy: str, parameters: Dict[str, Any]) -> pd.DataFrame:
        """
        生成交易信號

        Args:
            data: OHLCV數據
            strategy: 策略名稱
            parameters: 策略參數

        Returns:
            信號DataFrame (entries, exits)
        """
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT is required for expanded strategies")

        if strategy not in self.STRATEGY_REGISTRY:
            raise ValueError(f"Unknown strategy: {strategy}. Available: {self.strategies}")

        method_name = self.STRATEGY_REGISTRY[strategy]
        method = getattr(self, method_name)

        return method(data, parameters)

    # ============ 趨勢策略 ============

    def _rsi_mean_reversion(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """RSI均值回歸策略"""
        period = params.get('period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        rsi = vbt.RSI.run(data['close'], window=period)
        rsi_values = rsi.rsi

        entries = (rsi_values < oversold) & (~(rsi_values.shift(1) < oversold))
        exits = (rsi_values > overbought) & (~(rsi_values.shift(1) > overbought))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _macd_crossover(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """MACD交叉策略"""
        fast = params.get('fast', 12)
        slow = params.get('slow', 26)
        signal = params.get('signal', 9)

        macd = vbt.MACD.run(data['close'], fast_window=fast, slow_window=slow, signal_window=signal)

        entries = (macd.macd > macd.signal) & (~(macd.macd.shift(1) > macd.signal.shift(1)))
        exits = (macd.macd < macd.signal) & (~(macd.macd.shift(1) < macd.signal.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _dual_moving_average(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """雙移動平均策略"""
        short_period = params.get('short_period', 20)
        long_period = params.get('long_period', 50)

        short_ma = data['close'].rolling(short_period).mean()
        long_ma = data['close'].rolling(long_period).mean()

        entries = (short_ma > long_ma) & (~(short_ma.shift(1) > long_ma.shift(1)))
        exits = (short_ma < long_ma) & (~(short_ma.shift(1) < long_ma.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _triple_moving_average(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """三移動平均策略"""
        short = params.get('short_period', 10)
        medium = params.get('medium_period', 20)
        long = params.get('long_period', 50)

        short_ma = data['close'].rolling(short).mean()
        medium_ma = data['close'].rolling(medium).mean()
        long_ma = data['close'].rolling(long).mean()

        # 買入信號：短期 > 中期 > 長期
        entries = (short_ma > medium_ma) & (medium_ma > long_ma) & \
                 (~(short_ma.shift(1) > medium_ma.shift(1)) | ~(medium_ma.shift(1) > long_ma.shift(1)))

        # 賣出信號：短期 < 中期
        exits = (short_ma < medium_ma) & (~(short_ma.shift(1) < medium_ma.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _adx_momentum(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """ADX動量策略"""
        period = params.get('period', 14)
        threshold = params.get('threshold', 25)

        # Calculate ADX using VectorBT
        high, low, close = data['high'], data['low'], data['close']

        # True Range
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift(1)),
            'lc': abs(low - close.shift(1))
        }).max(axis=1)

        atr = tr.rolling(period).mean()

        # Directional Movement
        dm_plus = np.where((high - high.shift(1)) > (low.shift(1) - low),
                          np.maximum(high - high.shift(1), 0), 0)
        dm_minus = np.where((low.shift(1) - low) > (high - high.shift(1)),
                           np.maximum(low.shift(1) - low, 0), 0)

        di_plus = 100 * pd.Series(dm_plus).rolling(period).mean() / atr
        di_minus = 100 * pd.Series(dm_minus).rolling(period).mean() / atr

        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(period).mean()

        # Signals based on ADX and directional indicators
        entries = (adx > threshold) & (di_plus > di_minus) & \
                 (~(adx.shift(1) > threshold) | ~(di_plus.shift(1) > di_minus.shift(1)))
        exits = (di_plus < di_minus) & (~(di_plus.shift(1) < di_minus.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _parabolic_sar(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """拋物線SAR策略"""
        acceleration = params.get('acceleration', 0.02)
        maximum = params.get('maximum', 0.2)

        # Simplified Parabolic SAR implementation
        high, low, close = data['high'], data['low'], data['close']

        # Calculate SAR (simplified version)
        ep = high.rolling(2).max()  # Extreme point
        sar = low.rolling(2).min()   # SAR values
        af = pd.Series([acceleration] * len(data), index=data.index)  # Acceleration factor

        # Generate signals
        entries = (close > sar) & (~(close.shift(1) > sar.shift(1)))
        exits = (close < sar) & (~(close.shift(1) < sar.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    # ============ 均值回歸策略 ============

    def _bollinger_bands(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """布林帶策略"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)

        bb = vbt.BBANDS.run(data['close'], window=period, std=std_dev)

        entries = (data['close'] <= bb.lower) & (~(data['close'].shift(1) <= bb.lower.shift(1)))
        exits = (data['close'] >= bb.upper) & (~(data['close'].shift(1) >= bb.upper.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _stochastic_oversold(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """隨機指標超賣策略"""
        k_period = params.get('k_period', 14)
        d_period = params.get('d_period', 3)
        oversold = params.get('oversold', 20)
        overbought = params.get('overbought', 80)

        stoch = vbt.STOCH.run(data['high'], data['low'], data['close'],
                              k_window=k_period, d_window=d_period)

        entries = (stoch.stoch_k < oversold) & (~(stoch.stoch_k.shift(1) < oversold))
        exits = (stoch.stoch_k > overbought) & (~(stoch.stoch_k.shift(1) > overbought))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _williams_r(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """威廉姆斯%R策略"""
        period = params.get('period', 14)
        oversold = params.get('oversold', -80)
        overbought = params.get('overbought', -20)

        # Calculate Williams %R
        high_max = data['high'].rolling(period).max()
        low_min = data['low'].rolling(period).min()

        williams_r = -100 * (high_max - data['close']) / (high_max - low_min)

        entries = (williams_r < oversold) & (~(williams_r.shift(1) < oversold))
        exits = (williams_r > overbought) & (~(williams_r.shift(1) > overbought))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _commodity_channel_index(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """商品通道指數策略"""
        period = params.get('period', 20)
        oversold = params.get('oversold', -100)
        overbought = params.get('overbought', 100)

        # Calculate CCI
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        sma_tp = typical_price.rolling(period).mean()

        # Mean Deviation
        mean_deviation = typical_price.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())))

        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)

        entries = (cci < oversold) & (~(cci.shift(1) < oversold))
        exits = (cci > overbought) & (~(cci.shift(1) > overbought))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _relative_vigor_index(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """相對活力指數策略"""
        period = params.get('period', 10)

        # Calculate RVI (simplified)
        close = data['close']
        open_price = data.get('open', close.shift(1))

        # Calculate up and down moves
        up = close - open_price
        down = open_price - close.shift(1)

        # RVI calculation
        up_sum = up.rolling(period).sum()
        down_sum = down.rolling(period).sum()

        rvi = up_sum / (up_sum + down_sum)

        # Signal line
        signal = rvi.rolling(4).mean()

        entries = (rvi > signal) & (rvi < 0.7) & (~(rvi.shift(1) > signal.shift(1)))
        exits = (rvi < signal) & (~(rvi.shift(1) < signal.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    # ============ 波動率策略 ============

    def _volatility_breakout(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """波動率突破策略"""
        atr_period = params.get('atr_period', 14)
        multiplier = params.get('multiplier', 2.0)

        # Calculate ATR
        high, low, close = data['high'], data['low'], data['close']

        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift(1)),
            'lc': abs(low - close.shift(1))
        }).max(axis=1)

        atr = tr.rolling(atr_period).mean()

        # Breakout levels
        close_prev = close.shift(1)
        upper_breakout = close_prev + (atr * multiplier)
        lower_breakout = close_prev - (atr * multiplier)

        entries = close > upper_breakout
        exits = close < lower_breakout

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _average_true_range(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """平均真實波幅策略"""
        period = params.get('period', 14)
        multiplier = params.get('multiplier', 1.5)

        # Calculate ATR
        high, low, close = data['high'], data['low'], data['close']

        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift(1)),
            'lc': abs(low - close.shift(1))
        }).max(axis=1)

        atr = tr.rolling(period).mean()

        # ATR-based signals
        close_change = close.pct_change()
        volatility_threshold = atr / close * multiplier

        entries = (close_change > volatility_threshold) & (~(close_change.shift(1) > volatility_threshold.shift(1)))
        exits = (close_change < -volatility_threshold) & (~(close_change.shift(1) < -volatility_threshold.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _keltner_channels(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """凱特納通道策略"""
        period = params.get('period', 20)
        multiplier = params.get('multiplier', 2.0)

        # Calculate Keltner Channels
        ema = data['close'].ewm(span=period).mean()

        # Calculate ATR for channel width
        high, low, close = data['high'], data['low'], data['close']
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift(1)),
            'lc': abs(low - close.shift(1))
        }).max(axis=1)

        atr = tr.rolling(period).mean()

        upper_band = ema + (atr * multiplier)
        lower_band = ema - (atr * multiplier)

        entries = (data['close'] <= lower_band) & (~(data['close'].shift(1) <= lower_band.shift(1)))
        exits = (data['close'] >= upper_band) & (~(data['close'].shift(1) >= upper_band.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _donchian_channels(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """唐奇安通道策略"""
        period = params.get('period', 20)

        # Calculate Donchian Channels
        upper_channel = data['high'].rolling(period).max()
        lower_channel = data['low'].rolling(period).min()
        middle_channel = (upper_channel + lower_channel) / 2

        entries = (data['close'] > upper_channel) & (~(data['close'].shift(1) > upper_channel.shift(1)))
        exits = (data['close'] < lower_channel) & (~(data['close'].shift(1) < lower_channel.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    # ============ 價格行為策略 ============

    def _momentum_breakout(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """動量突破策略"""
        lookback = params.get('lookback', 20)
        threshold = params.get('threshold', 0.02)

        # Calculate momentum
        returns = data['close'].pct_change(lookback)

        entries = (returns > threshold) & (~(returns.shift(1) > threshold))
        exits = (returns < -threshold) & (~(returns.shift(1) < -threshold))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _price_rate_change(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """價格變化率策略"""
        period = params.get('period', 10)
        overbought = params.get('overbought', 10)
        oversold = params.get('oversold', -10)

        # Calculate ROC
        roc = ((data['close'] - data['close'].shift(period)) / data['close'].shift(period)) * 100

        entries = (roc < oversold) & (~(roc.shift(1) < oversold))
        exits = (roc > overbought) & (~(roc.shift(1) > overbought))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _on_balance_volume(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """能量潮策略"""
        period = params.get('period', 10)

        # Calculate OBV
        price_change = data['close'].diff()
        obv_change = np.where(price_change > 0, data['volume'],
                             np.where(price_change < 0, -data['volume'], 0))
        obv = pd.Series(obv_change).cumsum()

        # OBV moving average
        obv_ma = obv.rolling(period).mean()

        entries = (obv > obv_ma) & (~(obv.shift(1) > obv_ma.shift(1)))
        exits = (obv < obv_ma) & (~(obv.shift(1) < obv_ma.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _volume_weighted_average_price(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """成交量加權平均價策略"""
        period = params.get('period', 20)

        # Calculate VWAP
        typical_price = (data['high'] + data['low'] + data['close']) / 3
        vwap = (typical_price * data['volume']).rolling(period).sum() / data['volume'].rolling(period).sum()

        entries = (data['close'] > vwap) & (~(data['close'].shift(1) > vwap.shift(1)))
        exits = (data['close'] < vwap) & (~(data['close'].shift(1) < vwap.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    # ============ 進階組合策略 ============

    def _rsi_macd_confluence(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """RSI-MACD匯流策略"""
        rsi_period = params.get('rsi_period', 14)
        rsi_oversold = params.get('rsi_oversold', 30)
        macd_fast = params.get('macd_fast', 12)
        macd_slow = params.get('macd_slow', 26)
        macd_signal = params.get('macd_signal', 9)

        # Calculate indicators
        rsi = vbt.RSI.run(data['close'], window=rsi_period)
        macd = vbt.MACD.run(data['close'], fast_window=macd_fast, slow_window=macd_slow, signal_window=macd_signal)

        # Combined signals
        entries = ((rsi.rsi < rsi_oversold) & (macd.macd > macd.signal)) & \
                 (~(rsi.rsi.shift(1) < rsi_oversold) | ~(macd.macd.shift(1) > macd.signal.shift(1)))

        exits = (rsi.rsi > 70) & (macd.macd < macd.signal) & \
                (~(rsi.rsi.shift(1) > 70) | ~(macd.macd.shift(1) < macd.signal.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _bollinger_rsi_filter(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """布林帶RSI濾波策略"""
        bb_period = params.get('bb_period', 20)
        bb_std = params.get('bb_std', 2.0)
        rsi_period = params.get('rsi_period', 14)
        rsi_threshold = params.get('rsi_threshold', 50)

        # Calculate indicators
        bb = vbt.BBANDS.run(data['close'], window=bb_period, std=bb_std)
        rsi = vbt.RSI.run(data['close'], window=rsi_period)

        # Bollinger Band breakout with RSI filter
        entries = (data['close'] > bb.upper) & (rsi.rsi > rsi_threshold) & \
                 (~(data['close'].shift(1) > bb.upper.shift(1)))

        exits = (data['close'] < bb.lower) | (rsi.rsi < 30)

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _multi_timeframe_rsi(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """多時間框架RSI策略"""
        short_period = params.get('short_period', 7)
        long_period = params.get('long_period', 21)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        # Calculate multiple timeframe RSI
        rsi_short = vbt.RSI.run(data['close'], window=short_period)
        rsi_long = vbt.RSI.run(data['close'], window=long_period)

        # Confluence signals
        entries = ((rsi_short.rsi < oversold) & (rsi_long.rsi < oversold)) & \
                 (~(rsi_short.rsi.shift(1) < oversold) | ~(rsi_long.rsi.shift(1) < oversold))

        exits = ((rsi_short.rsi > overbought) & (rsi_long.rsi > overbought)) & \
                (~(rsi_short.rsi.shift(1) > overbought) | ~(rsi_long.rsi.shift(1) > overbought))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _volatility_adjusted_rsi(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """波動率調整RSI策略"""
        rsi_period = params.get('rsi_period', 14)
        atr_period = params.get('atr_period', 14)
        volatility_threshold = params.get('volatility_threshold', 0.02)

        # Calculate indicators
        rsi = vbt.RSI.run(data['close'], window=rsi_period)

        # Calculate volatility
        returns = data['close'].pct_change()
        volatility = returns.rolling(atr_period).std()

        # Dynamic RSI thresholds based on volatility
        base_oversold = params.get('base_oversold', 30)
        base_overbought = params.get('base_overbought', 70)

        # Adjust thresholds based on volatility
        volatility_factor = volatility / volatility_threshold
        adjusted_oversold = base_oversold - (volatility_factor * 10)
        adjusted_overbought = base_overbought + (volatility_factor * 10)

        adjusted_oversold = np.maximum(adjusted_oversold, 10)
        adjusted_overbought = np.minimum(adjusted_overbought, 90)

        entries = (rsi.rsi < adjusted_oversold) & (~(rsi.rsi.shift(1) < adjusted_oversold.shift(1)))
        exits = (rsi.rsi > adjusted_overbought) & (~(rsi.rsi.shift(1) > adjusted_overbought.shift(1)))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _ichimoku_cloud(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """一目均衡表策略"""
        tenkan_period = params.get('tenkan_period', 9)
        kijun_period = params.get('kijun_period', 26)
        senkou_b_period = params.get('senkou_b_period', 52)

        high, low, close = data['high'], data['low'], data['close']

        # Calculate Ichimoku components
        tenkan_sen = (high.rolling(tenkan_period).max() + low.rolling(tenkan_period).min()) / 2
        kijun_sen = (high.rolling(kijun_period).max() + low.rolling(kijun_period).min()) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
        senkou_span_b = (high.rolling(senkou_b_period).max() + low.rolling(senkou_b_period).min()) / 2
        senkou_span_b = senkou_span_b.shift(kijun_period)

        # Cloud (Kumo)
        cloud_top = np.maximum(senkou_span_a, senkou_span_b)
        cloud_bottom = np.minimum(senkou_span_a, senkou_span_b)

        # Trading signals
        entries = (close > cloud_top) & (tenkan_sen > kijun_sen) & \
                 (~(close.shift(1) > cloud_top.shift(1)) | ~(tenkan_sen.shift(1) > kijun_sen.shift(1)))

        exits = (close < cloud_bottom) | (tenkan_sen < kijun_sen)

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

    def _elder_ray_system(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """艾爾德射線系統策略"""
        ema_period = params.get('ema_period', 13)

        # Calculate EMA
        ema = data['close'].ewm(span=ema_period).mean()

        # Calculate Elder Ray components
        bull_power = data['high'] - ema
        bear_power = data['low'] - ema

        # Signals
        entries = (bull_power > 0) & (bear_power < 0) & (ema > ema.shift(1)) & \
                 (~(bull_power.shift(1) > 0) | ~(bear_power.shift(1) < 0))

        exits = (bear_power > 0) & (ema < ema.shift(1))

        return pd.DataFrame({'entries': entries, 'exits': exits}, index=data.index)

# Convenience function for creating strategy instance
def create_expanded_strategies() -> ExpandedStrategies:
    """創建擴展策略實例"""
    return ExpandedStrategies()

# Strategy categorization for easy access
STRATEGY_CATEGORIES = {
    "Trend": ["RSI_MEAN_REVERSION", "MACD_CROSSOVER", "DUAL_MOVING_AVERAGE",
              "TRIPLE_MOVING_AVERAGE", "ADX_MOMENTUM", "PARABOLIC_SAR"],
    "Mean Reversion": ["BOLLINGER_BANDS", "STOCHASTIC_OVERSOLD", "WILLIAMS_R",
                      "COMMODITY_CHANNEL_INDEX", "RELATIVE_VIGOR_INDEX"],
    "Volatility": ["VOLATILITY_BREAKOUT", "AVERAGE_TRUE_RANGE", "KELTNER_CHANNELS",
                  "DONCHIAN_CHANNELS"],
    "Price Action": ["MOMENTUM_BREAKOUT", "PRICE_RATE_CHANGE", "ON_BALANCE_VOLUME",
                    "VOLUME_WEIGHTED_AVERAGE_PRICE"],
    "Advanced": ["RSI_MACD_CONFLUENCE", "BOLLINGER_RSI_FILTER", "MULTI_TIMEFRAME_RSI",
                "VOLATILITY_ADJUSTED_RSI", "ICHIMOKU_CLOUD", "ELDER_RAY_SYSTEM"]
}

def get_strategies_by_category(category: str) -> list:
    """根據類別獲取策略列表"""
    return STRATEGY_CATEGORIES.get(category, [])

def get_all_strategies() -> list:
    """獲取所有策略"""
    return list(ExpandedStrategies.STRATEGY_REGISTRY.keys())