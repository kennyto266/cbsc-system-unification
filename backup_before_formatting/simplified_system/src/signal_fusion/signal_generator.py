#!/usr/bin/env python3
"""
簡化系統 - 智能信號生成器
Simplified System - Intelligent Signal Generator

Phase 4.1: 單指標信號生成系統
- 實現SignalGenerator類，支持所有技術指標
- 標準化信號格式 (買入/賣出/持有，強度1-10)
- 實現信號置信度評估算法
- 添加信號歷史記錄和追蹤
- 實現信號有效性驗證
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
from enum import Enum

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信號類型枚舉"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalStrength(Enum):
    """信號強度枚舉 (1-10)"""
    VERY_WEAK = 1
    WEAK = 3
    MODERATE = 5
    STRONG = 7
    VERY_STRONG = 9

@dataclass
class TradingSignal:
    """交易信號數據類"""
    # 基本信息
    symbol: str
    indicator_name: str
    signal_type: SignalType
    strength: float  # 1-10
    confidence: float  # 0-1

    # 時間信息
    timestamp: datetime
    data_time: pd.Timestamp

    # 指標數值
    indicator_value: float
    trigger_price: float
    trigger_conditions: Dict[str, Any]

    # 信號解釋
    reason: str
    explanation: str

    # 歷史信息
    historical_performance: Dict[str, float] = field(default_factory=dict)
    signal_id: str = field(default="")

    def __post_init__(self):
        """生成唯一信號ID"""
        if not self.signal_id:
            self.signal_id = f"{self.symbol}_{self.indicator_name}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"

class SignalGenerator:
    """
    智能信號生成器

    核心功能：
    1. 將技術指標轉換為標準化交易信號
    2. 評估信號強度和置信度
    3. 提供信號解釋和理由
    4. 追蹤信號歷史性能
    5. 驗證信號有效性
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化信號生成器"""
        self.config = config or self._get_default_config()

        # 信號生成規則
        self.signal_rules = {
            'RSI': self._generate_rsi_signals,
            'MACD': self._generate_macd_signals,
            'SMA': self._generate_sma_signals,
            'EMA': self._generate_ema_signals,
            'BOLLINGER': self._generate_bollinger_signals,
            'STOCH': self._generate_stochastic_signals,
            'WILLIAMS_R': self._generate_williams_r_signals,
            'ATR': self._generate_atr_signals,
            'VOLUME_MA': self._generate_volume_signals,
        }

        # 信號歷史記錄
        self.signal_history: List[TradingSignal] = []
        self.performance_tracker: Dict[str, Dict[str, float]] = {}

        # 置信度計算器
        self.confidence_calculator = ConfidenceCalculator()

        logger.info("Signal Generator initialized with signal rules")

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            'rsi_thresholds': {
                'oversold': 25,
                'overbought': 75,
                'extreme_oversold': 20,
                'extreme_overbought': 80
            },
            'macd_thresholds': {
                'zero_cross_strength': 0.1,
                'signal_cross_strength': 0.05
            },
            'bollinger_thresholds': {
                'lower_band_touch': 0.02,
                'upper_band_touch': 0.02,
                'band_squeeze_threshold': 0.1
            },
            'volume_thresholds': {
                'spike_multiplier': 1.5,
                'dry_up_threshold': 0.5
            },
            'signal_strength_weights': {
                'indicator_position': 0.4,
                'trend_alignment': 0.3,
                'volume_confirmation': 0.2,
                'historical_accuracy': 0.1
            },
            'confidence_threshold': 0.3,
            'signal_decay_days': 5,
            'min_signal_strength': 3.0
        }

    def generate_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: Optional[datetime] = None
    ) -> List[TradingSignal]:
        """
        為所有技術指標生成交易信號

        Args:
            symbol: 股票代碼
            data: OHLCV數據
            indicators: 技術指標數據
            current_time: 當前時間

        Returns:
            交易信號列表
        """
        if current_time is None:
            current_time = datetime.now()

        signals = []

        try:
            # 為每個指標生成信號
            for indicator_name, indicator_data in indicators.items():
                if indicator_name.startswith('_'):  # 跳過元數據
                    continue

                # 檢查是否有對應的信號生成規則
                base_indicator = self._get_base_indicator_name(indicator_name)
                if base_indicator in self.signal_rules:
                    try:
                        indicator_signals = self.signal_rules[base_indicator](
                            symbol, data, indicators, current_time
                        )
                        signals.extend(indicator_signals)
                    except Exception as e:
                        logger.warning(f"Error generating signals for {indicator_name}: {e}")
                        continue

            # 過濾和驗證信號
            valid_signals = self._filter_and_validate_signals(signals)

            # 更新信號歷史
            self._update_signal_history(valid_signals)

            logger.info(f"Generated {len(valid_signals)} signals for {symbol}")
            return valid_signals

        except Exception as e:
            logger.error(f"Error generating signals for {symbol}: {e}")
            return []

    def _get_base_indicator_name(self, indicator_name: str) -> str:
        """獲取基礎指標名稱"""
        # 特殊處理MACD相關指標
        if indicator_name in ['MACD', 'MACD_Signal', 'MACD_Histogram']:
            return 'MACD'

        for base_name in self.signal_rules.keys():
            if indicator_name.startswith(base_name):
                return base_name
        return indicator_name

    def _generate_rsi_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成RSI信號"""
        signals = []

        # 獲取RSI數據
        rsi_series = None
        for key in indicators.keys():
            if key.startswith('RSI'):
                rsi_series = indicators[key]
                break

        if rsi_series is None or len(rsi_series) == 0:
            return signals

        # 獲取當前值和歷史值
        if isinstance(rsi_series, pd.Series):
            current_rsi = float(rsi_series.iloc[-1])
            prev_rsi = float(rsi_series.iloc[-2]) if len(rsi_series) > 1 else current_rsi
        else:
            current_rsi = float(rsi_series)
            prev_rsi = current_rsi

        current_price = float(data['close'].iloc[-1])
        data_time = data.index[-1]

        thresholds = self.config['rsi_thresholds']

        # 檢測超賣信號
        if current_rsi <= thresholds['extreme_oversold']:
            signal_type = SignalType.BUY
            strength = SignalStrength.VERY_STRONG.value + 1
            reason = "極端超賣，強烈反彈信號"
            explanation = f"RSI為{current_rsi:.1f}，處於極端超賣區域({thresholds['extreme_oversold']})，通常預示著強勁反彈"

        elif current_rsi <= thresholds['oversold']:
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG.value
            reason = "超賣，買入信號"
            explanation = f"RSI為{current_rsi:.1f}，處於超賣區域({thresholds['oversold']})，可能出現反彈"

        # 檢測超買信號
        elif current_rsi >= thresholds['extreme_overbought']:
            signal_type = SignalType.SELL
            strength = SignalStrength.VERY_STRONG.value + 1
            reason = "極端超買，強烈賣出信號"
            explanation = f"RSI為{current_rsi:.1f}，處於極端超買區域({thresholds['extreme_overbought']})，高風險賣出"

        elif current_rsi >= thresholds['overbought']:
            signal_type = SignalType.SELL
            strength = SignalStrength.STRONG.value
            reason = "超買，賣出信號"
            explanation = f"RSI為{current_rsi:.1f}，處於超買區域({thresholds['overbought']})，可能出現回調"

        # 檢測RSI轉向
        elif prev_rsi < 30 < current_rsi:
            signal_type = SignalType.BUY
            strength = SignalStrength.MODERATE.value
            reason = "RSI脫離超賣區域"
            explanation = f"RSI從{prev_rsi:.1f}反彈至{current_rsi:.1f}，脫離超賣區域"

        elif prev_rsi > 70 > current_rsi:
            signal_type = SignalType.SELL
            strength = SignalStrength.MODERATE.value
            reason = "RSI脫離超買區域"
            explanation = f"RSI從{prev_rsi:.1f}回落至{current_rsi:.1f}，脫離超買區域"

        else:
            # 中性區間
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK.value
            reason = "RSI處於中性區域"
            explanation = f"RSI為{current_rsi:.1f}，處於中性區域，無明顯信號"

        # 計算置信度
        confidence = self.confidence_calculator.calculate_rsi_confidence(
            current_rsi, prev_rsi, len(rsi_series)
        )

        # 獲取歷史表現
        historical_perf = self._get_indicator_performance('RSI', signal_type)

        # 創建信號
        if confidence >= self.config['confidence_threshold']:
            signal = TradingSignal(
                symbol=symbol,
                indicator_name="RSI",
                signal_type=signal_type,
                strength=min(10.0, strength),
                confidence=confidence,
                timestamp=current_time,
                data_time=data_time,
                indicator_value=current_rsi,
                trigger_price=current_price,
                trigger_conditions={
                    'current_rsi': current_rsi,
                    'prev_rsi': prev_rsi,
                    'thresholds': thresholds
                },
                reason=reason,
                explanation=explanation,
                historical_performance=historical_perf
            )
            signals.append(signal)

        return signals

    def _generate_macd_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成MACD信號"""
        signals = []

        # 獲取MACD數據
        macd_series = indicators.get('MACD')
        signal_series = indicators.get('MACD_Signal')
        histogram_series = indicators.get('MACD_Histogram')

        if not all([macd_series, signal_series, histogram_series]):
            return signals

        # 獲取當前值
        if isinstance(macd_series, pd.Series):
            current_macd = float(macd_series.iloc[-1])
            current_signal = float(signal_series.iloc[-1])
            current_hist = float(histogram_series.iloc[-1])

            if len(macd_series) > 1:
                prev_macd = float(macd_series.iloc[-2])
                prev_signal = float(signal_series.iloc[-2])
                prev_hist = float(histogram_series.iloc[-2])
            else:
                prev_macd, prev_signal, prev_hist = current_macd, current_signal, current_hist
        else:
            return signals

        current_price = float(data['close'].iloc[-1])
        data_time = data.index[-1]

        thresholds = self.config['macd_thresholds']

        # 檢測MACD黃金交叉
        if prev_macd <= prev_signal and current_macd > current_signal:
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG.value
            reason = "MACD黃金交叉"
            explanation = f"MACD線({current_macd:.4f})向上穿越信號線({current_signal:.4f})，看漲信號"

        # 檢測MACD死亡交叉
        elif prev_macd >= prev_signal and current_macd < current_signal:
            signal_type = SignalType.SELL
            strength = SignalStrength.STRONG.value
            reason = "MACD死亡交叉"
            explanation = f"MACD線({current_macd:.4f})向下穿越信號線({current_signal:.4f})，看跌信號"

        # 檢測MACD零軸突破
        elif prev_macd <= 0 < current_macd and current_hist > thresholds['zero_cross_strength']:
            signal_type = SignalType.BUY
            strength = SignalStrength.MODERATE.value
            reason = "MACD突破零軸"
            explanation = f"MACD從負轉正({current_macd:.4f})，勢頭轉強"

        elif prev_macd >= 0 > current_macd and current_hist < -thresholds['zero_cross_strength']:
            signal_type = SignalType.SELL
            strength = SignalStrength.MODERATE.value
            reason = "MACD跌破零軸"
            explanation = f"MACD從正轉負({current_macd:.4f})，勢頭轉弱"

        else:
            # 中性信號
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK.value
            reason = "MACD無明顯信號"
            explanation = f"MACD線({current_macd:.4f})與信號線({current_signal:.4f})無明顯交叉"

        # 計算置信度
        confidence = self.confidence_calculator.calculate_macd_confidence(
            current_macd, current_signal, current_hist, prev_macd, prev_signal
        )

        # 獲取歷史表現
        historical_perf = self._get_indicator_performance('MACD', signal_type)

        # 創建信號
        if confidence >= self.config['confidence_threshold']:
            signal = TradingSignal(
                symbol=symbol,
                indicator_name="MACD",
                signal_type=signal_type,
                strength=min(10.0, strength),
                confidence=confidence,
                timestamp=current_time,
                data_time=data_time,
                indicator_value=current_macd,
                trigger_price=current_price,
                trigger_conditions={
                    'macd': current_macd,
                    'signal': current_signal,
                    'histogram': current_hist,
                    'prev_macd': prev_macd,
                    'prev_signal': prev_signal
                },
                reason=reason,
                explanation=explanation,
                historical_performance=historical_perf
            )
            signals.append(signal)

        return signals

    def _generate_bollinger_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成布林帶信號"""
        signals = []

        # 獲取布林帶數據
        upper_series = indicators.get('BB_Upper')
        lower_series = indicators.get('BB_Lower')
        middle_series = indicators.get('BB_Middle')
        width_series = indicators.get('BB_Width')

        if not all([upper_series, lower_series, middle_series]):
            return signals

        # 獲取當前值
        current_price = float(data['close'].iloc[-1])
        data_time = data.index[-1]

        if isinstance(upper_series, pd.Series):
            current_upper = float(upper_series.iloc[-1])
            current_lower = float(lower_series.iloc[-1])
            current_middle = float(middle_series.iloc[-1])
            current_width = float(width_series.iloc[-1]) if width_series is not None else 0
        else:
            return signals

        thresholds = self.config['bollinger_thresholds']

        # 計算價格在布林帶中的位置
        band_position = (current_price - current_lower) / (current_upper - current_lower)

        # 檢測觸及下軌
        if current_price <= current_lower * (1 + thresholds['lower_band_touch']):
            signal_type = SignalType.BUY
            strength = SignalStrength.STRONG.value
            reason = "價格觸及布林帶下軌"
            explanation = f"價格({current_price:.2f})觸及布林帶下軌({current_lower:.2f})，可能反彈"

        # 檢測觸及上軌
        elif current_price >= current_upper * (1 - thresholds['upper_band_touch']):
            signal_type = SignalType.SELL
            strength = SignalStrength.STRONG.value
            reason = "價格觸及布林帶上軌"
            explanation = f"價格({current_price:.2f})觸及布林帶上軌({current_upper:.2f})，可能回調"

        # 檢測布林帶收縮
        elif current_width < thresholds['band_squeeze_threshold']:
            signal_type = SignalType.HOLD
            strength = SignalStrength.MODERATE.value
            reason = "布林帶收縮"
            explanation = f"布林帶寬度({current_width:.3f})收窄，等待突破"

        # 檢測突破中軌
        elif current_price > current_middle and band_position > 0.7:
            signal_type = SignalType.BUY
            strength = SignalStrength.MODERATE.value
            reason = "價格突破布林帶中軌"
            explanation = f"價格({current_price:.2f})站上中軌({current_middle:.2f})，勢頭轉強"

        elif current_price < current_middle and band_position < 0.3:
            signal_type = SignalType.SELL
            strength = SignalStrength.MODERATE.value
            reason = "價格跌破布林帶中軌"
            explanation = f"價格({current_price:.2f})跌破中軌({current_middle:.2f})，勢頭轉弱"

        else:
            # 中性信號
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK.value
            reason = "價格在布林帶中間區域"
            explanation = f"價格在布林帶中間運行，位置{band_position:.2f}"

        # 計算置信度
        confidence = self.confidence_calculator.calculate_bollinger_confidence(
            band_position, current_width, len(data)
        )

        # 獲取歷史表現
        historical_perf = self._get_indicator_performance('BOLLINGER', signal_type)

        # 創建信號
        if confidence >= self.config['confidence_threshold']:
            signal = TradingSignal(
                symbol=symbol,
                indicator_name="BOLLINGER",
                signal_type=signal_type,
                strength=min(10.0, strength),
                confidence=confidence,
                timestamp=current_time,
                data_time=data_time,
                indicator_value=band_position,
                trigger_price=current_price,
                trigger_conditions={
                    'band_position': band_position,
                    'upper_band': current_upper,
                    'lower_band': current_lower,
                    'middle_band': current_middle,
                    'band_width': current_width
                },
                reason=reason,
                explanation=explanation,
                historical_performance=historical_perf
            )
            signals.append(signal)

        return signals

    def _generate_sma_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成SMA信號"""
        # 簡化實現，主要檢測均線交叉
        return self._generate_ma_signals(symbol, data, indicators, current_time, "SMA")

    def _generate_ema_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成EMA信號"""
        # 簡化實現，主要檢測均線交叉
        return self._generate_ma_signals(symbol, data, indicators, current_time, "EMA")

    def _generate_ma_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime,
        ma_type: str
    ) -> List[TradingSignal]:
        """生成移動平均線信號的通用方法"""
        signals = []

        # 獲取不同週期的均線
        ma_indicators = {k: v for k, v in indicators.items() if k.startswith(ma_type)}

        if len(ma_indicators) < 2:
            return signals

        # 按週期排序
        ma_periods = []
        ma_series = []

        for key, series in ma_indicators.items():
            try:
                period = int(key.split('_')[-1])
                ma_periods.append(period)
                ma_series.append(series)
            except:
                continue

        if len(ma_periods) < 2:
            return signals

        # 排序
        sorted_pairs = sorted(zip(ma_periods, ma_series))
        ma_periods, ma_series = zip(*sorted_pairs)

        # 獲取短期和長期均線
        short_ma = ma_series[0]
        long_ma = ma_series[-1]

        if isinstance(short_ma, pd.Series) and isinstance(long_ma, pd.Series):
            current_short = float(short_ma.iloc[-1])
            current_long = float(long_ma.iloc[-1])
            current_price = float(data['close'].iloc[-1])

            if len(short_ma) > 1 and len(long_ma) > 1:
                prev_short = float(short_ma.iloc[-2])
                prev_long = float(long_ma.iloc[-2])
            else:
                prev_short, prev_long = current_short, current_long
        else:
            return signals

        data_time = data.index[-1]

        # 檢測黃金交叉
        if prev_short <= prev_long and current_short > current_long:
            signal_type = SignalType.BUY
            strength = SignalStrength.MODERATE.value
            reason = f"{ma_type}黃金交叉"
            explanation = f"短期{ma_type}({ma_periods[0]})向上穿越長期{ma_type}({ma_periods[-1]})"

        # 檢測死亡交叉
        elif prev_short >= prev_long and current_short < current_long:
            signal_type = SignalType.SELL
            strength = SignalStrength.MODERATE.value
            reason = f"{ma_type}死亡交叉"
            explanation = f"短期{ma_type}({ma_periods[0]})向下穿越長期{ma_type}({ma_periods[-1]})"

        # 檢測價格與均線關係
        elif current_price > current_short and current_short > current_long:
            signal_type = SignalType.BUY
            strength = SignalStrength.WEAK.value
            reason = f"價格站上{ma_type}"
            explanation = f"價格在短期和長期{ma_type}之上，趨勢向好"

        elif current_price < current_short and current_short < current_long:
            signal_type = SignalType.SELL
            strength = SignalStrength.WEAK.value
            reason = f"價格跌破{ma_type}"
            explanation = f"價格在短期和長期{ma_type}之下，趨勢向淡"

        else:
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK.value
            reason = f"{ma_type}排列混亂"
            explanation = f"{ma_type}無明顯方向性排列"

        # 計算置信度
        confidence = self.confidence_calculator.calculate_ma_confidence(
            current_price, current_short, current_long, len(data)
        )

        # 獲取歷史表現
        historical_perf = self._get_indicator_performance(ma_type, signal_type)

        # 創建信號
        if confidence >= self.config['confidence_threshold']:
            signal = TradingSignal(
                symbol=symbol,
                indicator_name=ma_type,
                signal_type=signal_type,
                strength=min(10.0, strength),
                confidence=confidence,
                timestamp=current_time,
                data_time=data_time,
                indicator_value=current_short,
                trigger_price=current_price,
                trigger_conditions={
                    'short_ma': current_short,
                    'long_ma': current_long,
                    'short_period': ma_periods[0],
                    'long_period': ma_periods[-1]
                },
                reason=reason,
                explanation=explanation,
                historical_performance=historical_perf
            )
            signals.append(signal)

        return signals

    def _generate_stochastic_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成隨機指標信號"""
        # 簡化實現
        return []

    def _generate_williams_r_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成威廉指標信號"""
        # 簡化實現
        return []

    def _generate_atr_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成ATR信號"""
        # ATR主要用於風險管理，這裡簡化實現
        return []

    def _generate_volume_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        indicators: Dict[str, Any],
        current_time: datetime
    ) -> List[TradingSignal]:
        """生成成交量信號"""
        signals = []

        if 'volume' not in data.columns:
            return signals

        volume_ma_20 = indicators.get('Volume_MA_20')
        if volume_ma_20 is None:
            return signals

        current_volume = float(data['volume'].iloc[-1])
        current_price = float(data['close'].iloc[-1])
        data_time = data.index[-1]

        if isinstance(volume_ma_20, pd.Series):
            avg_volume = float(volume_ma_20.iloc[-1])
        else:
            avg_volume = float(volume_ma_20)

        thresholds = self.config['volume_thresholds']
        volume_ratio = current_volume / avg_volume

        # 成交量放大
        if volume_ratio >= thresholds['sppike_multiplier']:
            signal_type = SignalType.BUY if current_price > data['close'].iloc[-2] else SignalType.SELL
            strength = SignalStrength.MODERATE.value
            reason = "成交量異常放大"
            explanation = f"成交量({current_volume:,.0f})是平均量的{volume_ratio:.1f}倍，確認現有趨勢"

        # 成交量萎縮
        elif volume_ratio <= thresholds['dry_up_threshold']:
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK.value
            reason = "成交量萎縮"
            explanation = f"成交量({current_volume:,.0f})僅為平均量的{volume_ratio:.1f}倍，市場缺乏動力"

        else:
            return signals

        # 計算置信度
        confidence = min(0.8, volume_ratio / 3.0)  # 基於成交量放大程度

        # 獲取歷史表現
        historical_perf = self._get_indicator_performance('VOLUME', signal_type)

        # 創建信號
        if confidence >= self.config['confidence_threshold']:
            signal = TradingSignal(
                symbol=symbol,
                indicator_name="VOLUME",
                signal_type=signal_type,
                strength=min(10.0, strength),
                confidence=confidence,
                timestamp=current_time,
                data_time=data_time,
                indicator_value=volume_ratio,
                trigger_price=current_price,
                trigger_conditions={
                    'current_volume': current_volume,
                    'avg_volume': avg_volume,
                    'volume_ratio': volume_ratio
                },
                reason=reason,
                explanation=explanation,
                historical_performance=historical_perf
            )
            signals.append(signal)

        return signals

    def _filter_and_validate_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """過濾和驗證信號"""
        valid_signals = []

        for signal in signals:
            # 檢查信號強度
            if signal.strength < self.config['min_signal_strength']:
                continue

            # 檢查信號時間（避免過期信號）
            signal_age = datetime.now() - signal.timestamp
            if signal_age.days > self.config['signal_decay_days']:
                continue

            # 檢查信號置信度
            if signal.confidence < self.config['confidence_threshold']:
                continue

            valid_signals.append(signal)

        return valid_signals

    def _update_signal_history(self, signals: List[TradingSignal]):
        """更新信號歷史記錄"""
        self.signal_history.extend(signals)

        # 限制歷史記錄數量
        max_history = 1000
        if len(self.signal_history) > max_history:
            self.signal_history = self.signal_history[-max_history:]

    def _get_indicator_performance(self, indicator: str, signal_type: SignalType) -> Dict[str, float]:
        """獲取指標歷史表現"""
        key = f"{indicator}_{signal_type.value}"

        if key not in self.performance_tracker:
            # 默認性能指標
            self.performance_tracker[key] = {
                'accuracy': 0.5,
                'profit_rate': 0.0,
                'signal_count': 0,
                'avg_return': 0.0
            }

        return self.performance_tracker[key]

    def update_signal_performance(self, signal: TradingSignal, outcome: float):
        """更新信號性能追蹤"""
        key = f"{signal.indicator_name}_{signal.signal_type.value}"

        if key not in self.performance_tracker:
            self.performance_tracker[key] = {
                'accuracy': 0.0,
                'profit_rate': 0.0,
                'signal_count': 0,
                'avg_return': 0.0,
                'total_return': 0.0
            }

        perf = self.performance_tracker[key]

        # 更新統計
        perf['signal_count'] += 1
        perf['total_return'] += outcome
        perf['avg_return'] = perf['total_return'] / perf['signal_count']

        # 更新勝率
        if outcome > 0:
            perf['profit_rate'] = (perf['profit_rate'] * (perf['signal_count'] - 1) + 1) / perf['signal_count']
        else:
            perf['profit_rate'] = (perf['profit_rate'] * (perf['signal_count'] - 1)) / perf['signal_count']

        logger.info(f"Updated performance for {key}: {perf}")

    def get_signal_summary(self, signals: List[TradingSignal]) -> Dict[str, Any]:
        """獲取信號摘要"""
        if not signals:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0,
                'avg_confidence': 0.0,
                'avg_strength': 0.0
            }

        buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
        sell_signals = [s for s in signals if s.signal_type == SignalType.SELL]
        hold_signals = [s for s in signals if s.signal_type == SignalType.HOLD]

        return {
            'total_signals': len(signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'hold_signals': len(hold_signals),
            'avg_confidence': np.mean([s.confidence for s in signals]),
            'avg_strength': np.mean([s.strength for s in signals]),
            'top_signals': sorted(signals, key=lambda x: x.strength * x.confidence, reverse=True)[:3]
        }

class ConfidenceCalculator:
    """置信度計算器"""

    def calculate_rsi_confidence(self, current_rsi: float, prev_rsi: float, data_points: int) -> float:
        """計算RSI信號置信度"""
        # 基於RSI值的極值程度
        if current_rsi <= 20 or current_rsi >= 80:
            base_confidence = 0.9
        elif current_rsi <= 30 or current_rsi >= 70:
            base_confidence = 0.7
        else:
            base_confidence = 0.4

        # 基於RSI變化方向
        if abs(current_rsi - prev_rsi) > 5:
            base_confidence += 0.1

        # 基於數據充足度
        data_factor = min(1.0, data_points / 100)

        return min(1.0, base_confidence * data_factor)

    def calculate_macd_confidence(
        self,
        current_macd: float,
        current_signal: float,
        current_hist: float,
        prev_macd: float,
        prev_signal: float
    ) -> float:
        """計算MACD信號置信度"""
        # 基於交叉的明確程度
        cross_strength = abs(current_macd - current_signal)
        base_confidence = min(0.8, cross_strength * 20)

        # 基於趨勢一致性
        if (current_macd > current_signal and current_hist > 0) or \
           (current_macd < current_signal and current_hist < 0):
            base_confidence += 0.1

        # 基於動量變化
        momentum_change = abs((current_macd - prev_macd) / (prev_macd + 0.0001))
        if momentum_change > 0.1:
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def calculate_bollinger_confidence(self, band_position: float, band_width: float, data_points: int) -> float:
        """計算布林帶信號置信度"""
        # 基於價格位置
        if band_position <= 0.1 or band_position >= 0.9:
            position_confidence = 0.8
        elif band_position <= 0.2 or band_position >= 0.8:
            position_confidence = 0.6
        else:
            position_confidence = 0.3

        # 基於布林帶寬度（寬度越窄，突破信號越可靠）
        width_confidence = min(0.2, (0.2 - band_width) * 2)

        # 基於數據充足度
        data_factor = min(1.0, data_points / 50)

        total_confidence = position_confidence + width_confidence
        return min(1.0, total_confidence * data_factor)

    def calculate_ma_confidence(self, price: float, short_ma: float, long_ma: float, data_points: int) -> float:
        """計算移動平均線信號置信度"""
        # 基於均線間距
        ma_distance = abs(short_ma - long_ma) / long_ma
        base_confidence = min(0.7, ma_distance * 5)

        # 基於價格與均線關係
        if (price > short_ma and short_ma > long_ma) or \
           (price < short_ma and short_ma < long_ma):
            base_confidence += 0.2

        # 基於數據充足度
        data_factor = min(1.0, data_points / (50 * 2))  # 需要更長的數據來支持長期均線

        return min(1.0, base_confidence * data_factor)

# 全局實例
signal_generator = SignalGenerator()

# 便利函數
def generate_signals(symbol: str, data: pd.DataFrame, indicators: Dict[str, Any]) -> List[TradingSignal]:
    """便利函數：生成交易信號"""
    return signal_generator.generate_signals(symbol, data, indicators)