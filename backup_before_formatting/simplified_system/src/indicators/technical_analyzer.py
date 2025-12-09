#!/usr/bin/env python3
"""
簡化系統 - 技術分析器
Simplified System - Technical Analyzer

高級技術分析功能，包括趨勢分析、交易信號生成等
Advanced technical analysis including trend analysis, trading signals generation, etc.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime

from .core_indicators import CoreIndicators

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """
    高級技術分析器

    整合核心指標計算，提供：
    - 趨勢分析
    - 交易信號生成
    - 支撐阻力位計算
    - 綜合技術評分
    """

    def __init__(self):
        """初始化技術分析器"""
        self.indicators = CoreIndicators()

        # 信號閾值配置
        self.signal_thresholds = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'macd_bullish': 0,
            'bb_lower_buy': 0.02,  # 接近下軌2%
            'bb_upper_sell': 0.98,  # 接近上軌98%
            'volume_spike': 1.5,   # 成交量放大1.5倍
        }

        logger.info("Technical Analyzer initialized with signal thresholds")

    def analyze_trend(
        self,
        data: pd.DataFrame,  # Change to accept full DataFrame
        short_period: int = 20,
        long_period: int = 50
    ) -> Dict[str, Any]:
        """
        分析價格趨勢

        Args:
            data: 價格數據DataFrame
            short_period: 短期週期
            long_period: 長期週期

        Returns:
            趨勢分析結果
        """
        if 'close' not in data.columns:
            return {
                'trend': 'UNKNOWN',
                'strength': 'WEAK',
                'direction': 0,
                'confidence': 0.0
            }

        prices = data['close']
        if len(prices) < long_period:
            return {
                'trend': 'UNKNOWN',
                'strength': 'WEAK',
                'direction': 0,
                'confidence': 0.0
            }

        current_price = float(prices.iloc[-1])
        sma_short = self.indicators.calculate_sma(prices, short_period)
        sma_long = self.indicators.calculate_sma(prices, long_period)

        short_ma = float(sma_short.iloc[-1])
        long_ma = float(sma_long.iloc[-1])

        # 判斷趨勢方向
        if current_price > short_ma and short_ma > long_ma:
            trend = 'UP'
            strength = 'STRONG'
        elif current_price > short_ma and current_price > long_ma:
            trend = 'UP'
            strength = 'MODERATE'
        elif current_price < short_ma and short_ma < long_ma:
            trend = 'DOWN'
            strength = 'STRONG'
        elif current_price < short_ma and current_price < long_ma:
            trend = 'DOWN'
            strength = 'MODERATE'
        else:
            trend = 'SIDEWAYS'
            strength = 'WEAK'

        # 計算趨勢強度（0-1）
        if trend == 'UP':
            direction = 1.0
            confidence = min(1.0, ((current_price - long_ma) / long_ma) * 10)
        elif trend == 'DOWN':
            direction = -1.0
            confidence = min(1.0, ((long_ma - current_price) / long_ma) * 10)
        else:
            direction = 0.0
            confidence = 0.5

        return {
            'trend': trend,
            'strength': strength,
            'direction': direction,
            'confidence': max(0.0, min(1.0, confidence)),
            'current_price': float(current_price),
            'short_ma': float(short_ma),
            'long_ma': float(long_ma)
        }

    def generate_trading_signals(
        self,
        data: pd.DataFrame,
        indicators: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成交易信號

        Args:
            data: OHLCV數據
            indicators: 預計算的指標（可選）

        Returns:
            交易信號分析
        """
        if indicators is None:
            indicators = self.indicators.calculate_all_indicators(data)

        signals = {
            'overall_signal': 'NEUTRAL',
            'confidence': 0.0,
            'individual_signals': {},
            'signal_count': {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0}
        }

        close = data['close'].iloc[-1]
        signal_votes = []

        # RSI信號
        if 'RSI' in indicators:
            rsi = indicators['RSI'].iloc[-1] if isinstance(indicators['RSI'], pd.Series) else indicators['RSI']
            if rsi < self.signal_thresholds['rsi_oversold']:
                signals['individual_signals']['RSI'] = 'BUY'
                signal_votes.append('BUY')
            elif rsi > self.signal_thresholds['rsi_overbought']:
                signals['individual_signals']['RSI'] = 'SELL'
                signal_votes.append('SELL')
            else:
                signals['individual_signals']['RSI'] = 'NEUTRAL'
            signals['individual_signals']['RSI_Value'] = float(rsi)

        # MACD信號
        if 'MACD' in indicators and 'MACD_Signal' in indicators:
            macd = indicators['MACD'].iloc[-1] if isinstance(indicators['MACD'], pd.Series) else indicators['MACD']
            signal = indicators['MACD_Signal'].iloc[-1] if isinstance(indicators['MACD_Signal'], pd.Series) else indicators['MACD_Signal']
            histogram = indicators.get('MACD_Histogram', pd.Series([0])).iloc[-1] if isinstance(indicators.get('MACD_Histogram'), pd.Series) else indicators.get('MACD_Histogram', 0)

            if macd > signal and histogram > self.signal_thresholds['macd_bullish']:
                signals['individual_signals']['MACD'] = 'BUY'
                signal_votes.append('BUY')
            elif macd < signal and histogram < -self.signal_thresholds['macd_bullish']:
                signals['individual_signals']['MACD'] = 'SELL'
                signal_votes.append('SELL')
            else:
                signals['individual_signals']['MACD'] = 'NEUTRAL'

        # 布林帶信號
        if 'BB_Lower' in indicators and 'BB_Upper' in indicators:
            bb_lower = indicators['BB_Lower'].iloc[-1] if isinstance(indicators['BB_Lower'], pd.Series) else indicators['BB_Lower']
            bb_upper = indicators['BB_Upper'].iloc[-1] if isinstance(indicators['BB_Upper'], pd.Series) else indicators['BB_Upper']

            if close <= bb_lower * (1 + self.signal_thresholds['bb_lower_buy']):
                signals['individual_signals']['Bollinger'] = 'BUY'
                signal_votes.append('BUY')
            elif close >= bb_upper * self.signal_thresholds['bb_upper_sell']:
                signals['individual_signals']['Bollinger'] = 'SELL'
                signal_votes.append('SELL')
            else:
                signals['individual_signals']['Bollinger'] = 'NEUTRAL'

        # 成交量信號
        if 'Volume_MA_20' in indicators and 'volume' in data.columns:
            current_volume = data['volume'].iloc[-1]
            volume_ma = indicators['Volume_MA_20'].iloc[-1] if isinstance(indicators['Volume_MA_20'], pd.Series) else indicators['Volume_MA_20']

            if current_volume > volume_ma * self.signal_thresholds['volume_spike']:
                # 成交量放大，確認趨勢
                if signal_votes:
                    most_common_signal = max(set(signal_votes), key=signal_votes.count)
                    if most_common_signal != 'NEUTRAL':
                        signals['individual_signals']['Volume_Confirmation'] = most_common_signal
                    else:
                        signals['individual_signals']['Volume_Confirmation'] = 'NEUTRAL'

        # 計算整體信號
        if signal_votes:
            buy_count = signal_votes.count('BUY')
            sell_count = signal_votes.count('SELL')
            total_votes = len(signal_votes)

            if buy_count > sell_count:
                signals['overall_signal'] = 'BUY'
                signals['confidence'] = buy_count / total_votes
            elif sell_count > buy_count:
                signals['overall_signal'] = 'SELL'
                signals['confidence'] = sell_count / total_votes
            else:
                signals['overall_signal'] = 'NEUTRAL'
                signals['confidence'] = 0.5

        # 統計信號
        for signal in signal_votes:
            signals['signal_count'][signal] += 1

        # 信心度轉換為百分比
        signals['confidence'] = round(signals['confidence'] * 100, 1)

        return signals

    def calculate_support_resistance(
        self,
        data: pd.DataFrame,
        lookback_periods: List[int] = [10, 20, 50]
    ) -> Dict[str, List[Dict[str, float]]]:
        """
        計算支撐阻力位

        Args:
            data: OHLCV數據
            lookback_periods: 回看週期列表

        Returns:
            支撐阻力位信息
        """
        if len(data) < max(lookback_periods):
            return {
                'support': [],
                'resistance': []
            }

        high = data['high']
        low = data['low']
        current_price = data['close'].iloc[-1]

        support_levels = []
        resistance_levels = []

        for period in lookback_periods:
            if len(data) >= period:
                # 尋找最近的高點和低點
                recent_high = high.tail(period).max()
                recent_low = low.tail(period).min()

                # 計算強度基於距離當前價格的百分比
                resistance_distance = (recent_high - current_price) / current_price
                support_distance = (current_price - recent_low) / current_price

                # 阻力位：高點在當前價格之上
                if recent_high > current_price and resistance_distance < 0.1:  # 10%以內
                    resistance_levels.append({
                        'level': float(recent_high),
                        'period': period,
                        'strength': 'STRONG' if resistance_distance < 0.03 else 'MODERATE',
                        'distance_percent': round(resistance_distance * 100, 2)
                    })

                # 支撐位：低點在當前價格之下
                if recent_low < current_price and support_distance < 0.1:  # 10%以內
                    support_levels.append({
                        'level': float(recent_low),
                        'period': period,
                        'strength': 'STRONG' if support_distance < 0.03 else 'MODERATE',
                        'distance_percent': round(support_distance * 100, 2)
                    })

        # 排序（阻力位從低到高，支撐位從高到低）
        resistance_levels.sort(key=lambda x: x['level'])
        support_levels.sort(key=lambda x: x['level'], reverse=True)

        return {
            'support': support_levels[:3],  # 最多返回3個
            'resistance': resistance_levels[:3]  # 最多返回3個
        }

    def calculate_technical_score(
        self,
        data: pd.DataFrame,
        indicators: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        計算綜合技術評分 (0-100)

        Args:
            data: OHLCV數據
            indicators: 預計算的指標

        Returns:
            技術評分結果
        """
        if indicators is None:
            indicators = self.indicators.calculate_all_indicators(data)

        score_components = {}

        # 趨勢分析評分 (30%)
        trend_analysis = self.analyze_trend(data['close'])
        trend_score = 50  # 中性分數
        if trend_analysis['trend'] == 'UP':
            trend_score = 50 + trend_analysis['confidence'] * 50
        elif trend_analysis['trend'] == 'DOWN':
            trend_score = 50 - trend_analysis['confidence'] * 50

        score_components['trend'] = {
            'score': trend_score,
            'weight': 0.30,
            'trend': trend_analysis['trend'],
            'confidence': trend_analysis['confidence']
        }

        # RSI評分 (25%)
        if 'RSI' in indicators:
            rsi = indicators['RSI'].iloc[-1] if isinstance(indicators['RSI'], pd.Series) else indicators['RSI']
            # RSI在40-60之間給高分，超買超賣給低分
            if 40 <= rsi <= 60:
                rsi_score = 80 - abs(50 - rsi)  # 50分數最高，向兩側遞減
            elif rsi < 30:
                rsi_score = 30  # 超賣，但可能反彈
            elif rsi > 70:
                rsi_score = 20  # 超買，風險較高
            else:
                rsi_score = 60  # 中性偏強
        else:
            rsi_score = 50

        score_components['rsi'] = {
            'score': rsi_score,
            'weight': 0.25,
            'rsi_value': indicators.get('RSI', 'N/A')
        }

        # MACD評分 (25%)
        if 'MACD' in indicators and 'MACD_Signal' in indicators:
            macd = indicators['MACD'].iloc[-1] if isinstance(indicators['MACD'], pd.Series) else indicators['MACD']
            signal = indicators['MACD_Signal'].iloc[-1] if isinstance(indicators['MACD_Signal'], pd.Series) else indicators['MACD_Signal']

            if macd > signal:
                macd_score = 65 + 25  # 90分
            else:
                macd_score = 35  # 35分
        else:
            macd_score = 50

        score_components['macd'] = {
            'score': macd_score,
            'weight': 0.25,
            'bullish': macd > signal if 'MACD' in indicators else False
        }

        # 成交量確認 (20%)
        volume_score = 50
        if 'volume' in data.columns and 'Volume_MA_20' in indicators:
            current_volume = data['volume'].iloc[-1]
            volume_ma = indicators['Volume_MA_20'].iloc[-1] if isinstance(indicators['Volume_MA_20'], pd.Series) else indicators['Volume_MA_20']
            volume_ratio = current_volume / volume_ma

            if volume_ratio > 1.2:  # 成交量放大
                volume_score = 75
            elif volume_ratio > 0.8:  # 成交量正常
                volume_score = 60
            else:  # 成交量萎縮
                volume_score = 40

        score_components['volume'] = {
            'score': volume_score,
            'weight': 0.20,
            'volume_ratio': current_volume / volume_ma if 'volume' in data.columns and 'Volume_MA_20' in indicators else 1.0
        }

        # 計算加權總分
        total_score = sum(
            component['score'] * component['weight']
            for component in score_components.values()
        )

        # 確保分數在0-100範圍內
        total_score = max(0, min(100, total_score))

        # 評級
        if total_score >= 80:
            grade = 'A'
        elif total_score >= 70:
            grade = 'B'
        elif total_score >= 60:
            grade = 'C'
        elif total_score >= 50:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'total_score': round(total_score, 1),
            'grade': grade,
            'components': score_components,
            'recommendation': self._get_recommendation(total_score),
            'analysis_time': datetime.now().isoformat()
        }

    def _get_recommendation(self, score: float) -> str:
        """根據評分獲取建議"""
        if score >= 80:
            return "強烈看好，建議考慮買入"
        elif score >= 70:
            return "偏向看好，可考慮逢低買入"
        elif score >= 60:
            return "中性偏多，觀察為主"
        elif score >= 50:
            return "中性偏空，謹慎操作"
        elif score >= 40:
            return "偏向看淡，考慮減倉"
        else:
            return "強烈看淡，建議賣出"

    def comprehensive_analysis(
        self,
        data: pd.DataFrame,
        symbol: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        綜合技術分析

        Args:
            data: OHLCV數據
            symbol: 股票代碼

        Returns:
            完整的技術分析報告
        """
        try:
            # 計算所有指標
            indicators = self.indicators.calculate_all_indicators(data)

            # 趨勢分析
            trend_analysis = self.analyze_trend(data['close'])

            # 交易信號
            trading_signals = self.generate_trading_signals(data, indicators)

            # 支撐阻力
            support_resistance = self.calculate_support_resistance(data)

            # 技術評分
            technical_score = self.calculate_technical_score(data, indicators)

            # 獲取最新指標值
            latest_indicators = self.indicators.get_latest_values(indicators)

            # 組合結果
            analysis_result = {
                'symbol': symbol,
                'analysis_time': datetime.now().isoformat(),
                'data_points': len(data),
                'current_price': float(data['close'].iloc[-1]),
                'price_change': float(((data['close'].iloc[-1] / data['close'].iloc[-2]) - 1) * 100) if len(data) > 1 else 0.0,

                # 各個分析組件
                'trend_analysis': trend_analysis,
                'trading_signals': trading_signals,
                'support_resistance': support_resistance,
                'technical_score': technical_score,

                # 最新指標值
                'latest_indicators': latest_indicators,

                # 綜合建議
                'overall_recommendation': self._generate_overall_recommendation(
                    trend_analysis, trading_signals, technical_score
                )
            }

            logger.info(f"Comprehensive analysis completed for {symbol}")
            return analysis_result

        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'analysis_time': datetime.now().isoformat()
            }

    def _generate_overall_recommendation(
        self,
        trend: Dict[str, Any],
        signals: Dict[str, Any],
        score: Dict[str, Any]
    ) -> str:
        """生成綜合建議"""
        # 綜合三個因素的建議
        trend_bias = 1 if trend['trend'] == 'UP' else (-1 if trend['trend'] == 'DOWN' else 0)
        signal_bias = 1 if signals['overall_signal'] == 'BUY' else (-1 if signals['overall_signal'] == 'SELL' else 0)
        score_bias = 1 if score['total_score'] > 60 else (-1 if score['total_score'] < 40 else 0)

        total_bias = trend_bias + signal_bias + score_bias

        if total_bias >= 2:
            return "綜合分析：強烈買入信號"
        elif total_bias == 1:
            return "綜合分析：偏向買入"
        elif total_bias == 0:
            return "綜合分析：中性觀望"
        elif total_bias == -1:
            return "綜合分析：偏向賣出"
        else:
            return "綜合分析：強烈賣出信號"

# 全局實例
technical_analyzer = TechnicalAnalyzer()

# 便利函數
def analyze_symbol(data: pd.DataFrame, symbol: str = "UNKNOWN") -> Dict[str, Any]:
    """便利函數：分析單個股票"""
    return technical_analyzer.comprehensive_analysis(data, symbol)

def generate_signals(data: pd.DataFrame) -> Dict[str, Any]:
    """便利函數：生成交易信號"""
    return technical_analyzer.generate_trading_signals(data)