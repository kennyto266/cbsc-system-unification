#!/usr/bin/env python3
"""
高級技術分析信號系統
Advanced Technical Analysis Signal System

優化信號算法，提高技術分析精度
Optimize signal algorithms, improve technical analysis precision
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Import our modules
try:
    from .government_ta_signals import GovernmentTASignals
    from ..data.historical_data_extender import extend_data_records
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from indicators.government_ta_signals import GovernmentTASignals
    from data.historical_data_extender import extend_data_records

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AdvancedTechnicalSignals:
    """高級技術分析信號生成器"""

    def __init__(self):
        self.government_ta = GovernmentTASignals()
        self.scaler = StandardScaler()
        self.signal_weights = {
            'trend_strength': 0.25,
            'momentum_indicators': 0.20,
            'volatility_signals': 0.15,
            'volume_confirmation': 0.15,
            'pattern_recognition': 0.15,
            'multi_timeframe': 0.10
        }

        # 高級技術指標配置
        self.advanced_indicators = {
            'rsi': {'periods': [7, 14, 21, 28], 'levels': [20, 30, 70, 80]},
            'macd': {'fast_periods': [8, 12, 16], 'slow_periods': [21, 26, 35], 'signal_periods': [6, 9, 12]},
            'bollinger': {'periods': [15, 20, 25], 'std_devs': [1.5, 2.0, 2.5]},
            'stochastic': {'k_periods': [10, 14, 18], 'd_periods': [3, 5, 7]},
            'williams': {'periods': [10, 14, 18], 'levels': [-20, -80, 20, 80]},
            'cci': {'periods': [14, 20, 30], 'levels': [-200, -100, 100, 200]}
        }

    def generate_enhanced_signals(
        self,
        data: List[Dict[str, Any]],
        data_type: str = 'government',
        extend_to_1000: bool = True,
        optimize_signals: bool = True
    ) -> Dict[str, Any]:
        """
        生成增強版技術分析信號

        Args:
            data: 原始數據
            data_type: 數據類型
            extend_to_1000: 是否擴展到1000條記錄
            optimize_signals: 是否優化信號

        Returns:
            增強版信號結果
        """
        try:
            logger.info(f"Generating enhanced signals for {data_type} data with {len(data)} records")

            # 1. 數據預處理和擴展
            processed_data = self._preprocess_data(data, extend_to_1000)

            if not processed_data:
                return {'success': False, 'error': 'Data preprocessing failed'}

            df = pd.DataFrame(processed_data)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')

            logger.info(f"Processed data: {len(df)} records, {len(df.columns)} columns")

            # 2. 識別數值列
            numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

            if not numeric_columns:
                logger.warning("No numeric columns found in data")
                return {'success': False, 'error': 'No numeric data for analysis'}

            # 3. 計算高級技術指標
            indicators_result = self._calculate_advanced_indicators(df, numeric_columns)

            if not indicators_result.get('success'):
                return indicators_result

            # 4. 生成多時間框架信號
            timeframes_result = self._generate_multi_timeframe_signals(df, indicators_result['indicators'])

            # 5. 模式識別
            patterns_result = self._identify_trading_patterns(df, indicators_result['indicators'])

            # 6. 生成綜合信號
            composite_result = self._generate_composite_signals(
                df, indicators_result, timeframes_result, patterns_result, optimize_signals
            )

            # 7. 風險評估
            risk_assessment = self._assess_signal_risk(composite_result, df)

            result = {
                'success': True,
                'data_type': data_type,
                'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'input_records': len(data),
                'processed_records': len(df),
                'extended_records': len(df) - len(data),
                'numeric_columns': len(numeric_columns),
                'indicators': indicators_result['indicators'],
                'multi_timeframe_signals': timeframes_result,
                'pattern_recognition': patterns_result,
                'composite_signals': composite_result,
                'risk_assessment': risk_assessment,
                'signal_quality_score': self._calculate_signal_quality_score(composite_result),
                'recommendations': self._generate_trading_recommendations(composite_result, risk_assessment)
            }

            logger.info(f"Enhanced signals generated successfully: {result['signal_quality_score']:.2f}/10")
            return result

        except Exception as e:
            logger.error(f"Error generating enhanced signals: {e}")
            return {'success': False, 'error': str(e)}

    def _preprocess_data(self, data: List[Dict[str, Any]], extend_to_1000: bool) -> List[Dict[str, Any]]:
        """數據預處理和擴展"""
        try:
            if not data:
                return None

            # 如果需要擴展數據到1000條記錄
            if extend_to_1000 and len(data) < 1000:
                logger.info(f"Extending data from {len(data)} to 1000 records")
                extension_result = extend_data_records(data, 1000, 'hybrid_approach')

                if extension_result.get('success'):
                    logger.info(f"Data extension successful: {extension_result['original_count']} -> {extension_result['final_count']}")
                    return extension_result['data']
                else:
                    logger.warning(f"Data extension failed, using original data: {extension_result.get('error')}")

            # 數據清洗和標準化
            df = pd.DataFrame(data)

            # 處理缺失值
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                df[col] = df[col].interpolate(method='linear')
                df[col] = df[col].fillna(method='bfill').fillna(method='ffill')

            return df.to_dict('records')

        except Exception as e:
            logger.error(f"Error in data preprocessing: {e}")
            return data if not extend_to_1000 else None

    def _calculate_advanced_indicators(self, df: pd.DataFrame, numeric_columns: List[str]) -> Dict[str, Any]:
        """計算高級技術指標"""
        try:
            indicators = {}

            # 為每個數值列計算高級指標
            for column in numeric_columns:
                if column not in df.columns:
                    continue

                series = df[column]
                indicators[column] = {}

                # RSI多周期
                for period in self.advanced_indicators['rsi']['periods']:
                    rsi = self._calculate_rsi(series, period)
                    indicators[column][f'rsi_{period}'] = rsi

                # MACD多配置
                for fast, slow, signal in zip(
                    self.advanced_indicators['macd']['fast_periods'],
                    self.advanced_indicators['macd']['slow_periods'],
                    self.advanced_indicators['macd']['signal_periods']
                ):
                    macd_result = self._calculate_macd(series, fast, slow, signal)
                    indicators[column][f'macd_{fast}_{slow}'] = macd_result

                # 布林帶多配置
                for period, std in zip(
                    self.advanced_indicators['bollinger']['periods'],
                    self.advanced_indicators['bollinger']['std_devs']
                ):
                    bb_result = self._calculate_bollinger_bands(series, period, std)
                    indicators[column][f'bb_{period}_{std}'] = bb_result

                # 隨機指標
                for k, d in zip(
                    self.advanced_indicators['stochastic']['k_periods'],
                    self.advanced_indicators['stochastic']['d_periods']
                ):
                    stoch_result = self._calculate_stochastic(series, k, d)
                    indicators[column][f'stoch_{k}_{d}'] = stoch_result

                # Williams %R
                for period in self.advanced_indicators['williams']['periods']:
                    williams_r = self._calculate_williams_r(series, period)
                    indicators[column][f'williams_{period}'] = williams_r

                # CCI
                for period in self.advanced_indicators['cci']['periods']:
                    cci = self._calculate_cci(series, period)
                    indicators[column][f'cci_{period}'] = cci

            # 計算跨指標信號
            cross_indicator_signals = self._calculate_cross_indicator_signals(df, indicators)

            return {
                'success': True,
                'indicators': indicators,
                'cross_indicator_signals': cross_indicator_signals,
                'total_indicators': len([indicators[col] for col in indicators if col in numeric_columns])
            }

        except Exception as e:
            logger.error(f"Error calculating advanced indicators: {e}")
            return {'success': False, 'error': str(e)}

    def _calculate_cross_indicator_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """計算跨指標信號"""
        try:
            cross_signals = {}

            # 為每個數據列計算跨指標信號
            for column in indicators:
                if column not in df.columns:
                    continue

                column_indicators = indicators[column]
                cross_signals[column] = {}

                # RSI與MACD結合信號
                if any('rsi' in key for key in column_indicators.keys()) and \
                   any('macd' in key for key in column_indicators.keys()):

                    rsi_keys = [k for k in column_indicators.keys() if 'rsi' in k]
                    macd_keys = [k for k in column_indicators.keys() if 'macd' in k]

                    if rsi_keys and macd_keys:
                        rsi_series = column_indicators[rsi_keys[0]]
                        latest_rsi = rsi_series.iloc[-1] if hasattr(rsi_series, 'iloc') and len(rsi_series) > 0 else 50
                        macd_series = column_indicators[macd_keys[0]]
                        latest_macd = macd_series.iloc[-1] if hasattr(macd_series, 'iloc') and len(macd_series) > 0 else 0

                        # RSI超賣 + MACD金叉 = 強烈買入信號
                        if latest_rsi < 30 and latest_macd > 0:
                            cross_signals[column]['rsi_macd_bullish'] = 1.0
                        # RSI超買 + MACD死叉 = 強烈賣出信號
                        elif latest_rsi > 70 and latest_macd < 0:
                            cross_signals[column]['rsi_macd_bearish'] = -1.0
                        else:
                            cross_signals[column]['rsi_macd_neutral'] = 0.0

                # 布林帶與RSI結合信號
                if any('bb_' in key for key in column_indicators.keys()) and \
                   any('rsi' in key for key in column_indicators.keys()):

                    bb_keys = [k for k in column_indicators.keys() if 'bb_' in k and 'middle' in k]
                    rsi_keys = [k for k in column_indicators.keys() if 'rsi' in k]

                    if bb_keys and rsi_keys:
                        price_series = df[column]
                        bb_middle = column_indicators[bb_keys[0]]
                        rsi_series = column_indicators[rsi_keys[0]]
                        latest_rsi = rsi_series.iloc[-1] if hasattr(rsi_series, 'iloc') and len(rsi_series) > 0 else 50

                        # 價格低於布林帶中軌 + RSI超賣 = 買入機會
                        if price_series.iloc[-1] < bb_middle.iloc[-1] and latest_rsi < 30:
                            cross_signals[column]['bb_rsi_oversold'] = 0.8
                        # 價格高於布林帶中軌 + RSI超買 = 賣出機會
                        elif price_series.iloc[-1] > bb_middle.iloc[-1] and latest_rsi > 70:
                            cross_signals[column]['bb_rsi_overbought'] = -0.8
                        else:
                            cross_signals[column]['bb_rsi_neutral'] = 0.0

                # 隨機指標與威廉氏%R結合
                if any('stoch' in key for key in column_indicators.keys()) and \
                   any('williams' in key for key in column_indicators.keys()):

                    stoch_keys = [k for k in column_indicators.keys() if 'stoch_' in k and 'k' in k]
                    williams_keys = [k for k in column_indicators.keys() if 'williams' in k]

                    if stoch_keys and williams_keys:
                        stoch_series = column_indicators[stoch_keys[0]]
                        latest_stoch = stoch_series.iloc[-1] if hasattr(stoch_series, 'iloc') and len(stoch_series) > 0 else 50
                        williams_series = column_indicators[williams_keys[0]]
                        latest_williams = williams_series.iloc[-1] if hasattr(williams_series, 'iloc') and len(williams_series) > 0 else -50

                        # 兩者都超賣 = 強烈買入信號
                        if latest_stoch < 20 and latest_williams < -80:
                            cross_signals[column]['stoch_williams_bullish'] = 0.9
                        # 兩者都超買 = 強烈賣出信號
                        elif latest_stoch > 80 and latest_williams > -20:
                            cross_signals[column]['stoch_williams_bearish'] = -0.9
                        else:
                            cross_signals[column]['stoch_williams_neutral'] = 0.0

            return {
                'success': True,
                'cross_signals': cross_signals,
                'total_cross_signals': sum(len(signals) for signals in cross_signals.values())
            }

        except Exception as e:
            logger.error(f"Error calculating cross indicator signals: {e}")
            return {
                'success': False,
                'error': str(e),
                'cross_signals': {},
                'total_cross_signals': 0
            }

    def _generate_multi_timeframe_signals(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """生成多時間框架信號"""
        try:
            timeframe_signals = {}

            for column in indicators:
                if column not in df.columns:
                    continue

                timeframe_signals[column] = {}

                # 短期信號 (1-2週)
                short_signals = self._generate_short_term_signals(df[column], indicators[column])
                timeframe_signals[column]['short_term'] = short_signals

                # 中期信號 (1個月)
                medium_signals = self._generate_medium_term_signals(df[column], indicators[column])
                timeframe_signals[column]['medium_term'] = medium_signals

                # 長期信號 (3個月+)
                long_signals = self._generate_long_term_signals(df[column], indicators[column])
                timeframe_signals[column]['long_term'] = long_signals

                # 時間框架一致性檢查
                consistency_score = self._calculate_timeframe_consistency(short_signals, medium_signals, long_signals)
                timeframe_signals[column]['consistency_score'] = consistency_score

            return timeframe_signals

        except Exception as e:
            logger.error(f"Error generating multi-timeframe signals: {e}")
            return {}

    def _identify_trading_patterns(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """識別交易模式"""
        try:
            patterns = {}

            for column in indicators:
                if column not in df.columns:
                    continue

                series = df[column]
                patterns[column] = {}

                # 支撐阻力位
                patterns[column]['support_resistance'] = self._identify_support_resistance_levels(pd.DataFrame({column: series}), indicators[column])

                # 趨勢線模式
                patterns[column]['tline_patterns'] = self._identify_trendline_patterns(series)

                # 圖形模式
                patterns[column]['chart_patterns'] = self._identify_chart_patterns(series)

                # 價格模式
                patterns[column]['price_patterns'] = self._identify_price_patterns(series)

                # 波動率模式
                patterns[column]['volatility_patterns'] = self._identify_volatility_patterns(series)

            return patterns

        except Exception as e:
            logger.error(f"Error identifying trading patterns: {e}")
            return {}

    def _generate_composite_signals(
        self,
        df: pd.DataFrame,
        indicators_result: Dict,
        timeframes_result: Dict,
        patterns_result: Dict,
        optimize: bool = True
    ) -> Dict[str, Any]:
        """生成綜合信號"""
        try:
            composite_signals = {}

            for column in indicators_result['indicators']:
                if column not in df.columns:
                    continue

                # 收集所有信號
                all_signals = {
                    'indicators': self._extract_indicator_signals(indicators_result['indicators'][column]),
                    'timeframes': self._extract_timeframe_signals(timeframes_result.get(column, {})),
                    'patterns': self._extract_pattern_signals(patterns_result.get(column, {}))
                }

                # 加權計算
                signal_scores = self._calculate_weighted_signal_scores(all_signals)

                if optimize:
                    # 信號優化
                    optimized_scores = self._optimize_signals(signal_scores, df[column])
                    composite_signals[column] = optimized_scores
                else:
                    composite_signals[column] = signal_scores

                # 信號平滑
                if 'weighted_scores' in composite_signals[column]:
                    composite_signals[column]['smoothed_signals'] = self._smooth_signals(composite_signals[column]['weighted_scores'])
                else:
                    composite_signals[column]['smoothed_signals'] = []

                # 最終信號
                composite_signals[column]['final_signal'] = self._generate_final_signal(composite_signals[column])

            return {
                'success': True,
                'composite_signals': composite_signals,
                'optimization_applied': optimize
            }

        except Exception as e:
            logger.error(f"Error generating composite signals: {e}")
            return {'success': False, 'error': str(e)}

    def _assess_signal_risk(self, composite_signals: Dict, df: pd.DataFrame) -> Dict[str, Any]:
        """評估信號風險"""
        try:
            risk_assessment = {}

            for column in composite_signals.get('composite_signals', {}):
                signals = composite_signals['composite_signals'][column]
                if column not in df.columns:
                    continue

                series = df[column]
                risk_metrics = {
                    'signal_volatility': np.std(signals.get('weighted_scores', [])),
                    'signal_stability': self._calculate_signal_stability(signals.get('smoothed_signals', [])),
                    'market_volatility': series.pct_change().std(),
                    'max_drawdown_risk': self._calculate_max_drawdown(series),
                    'correlation_risk': self._calculate_correlation_risk(series),
                    'liquidity_risk': self._calculate_liquidity_risk(series)
                }

                # 綜合風險評分
                risk_score = self._calculate_risk_score(risk_metrics)
                risk_metrics['overall_risk_score'] = risk_score
                risk_metrics['risk_level'] = self._classify_risk_level(risk_score)

                risk_assessment[column] = risk_metrics

            return risk_assessment

        except Exception as e:
            logger.error(f"Error assessing signal risk: {e}")
            return {}

    def _calculate_signal_quality_score(self, composite_result: Dict) -> float:
        """計算信號質量評分"""
        try:
            score = 0.0

            # 基於綜合信號質量
            if 'composite_signals' in composite_result:
                for column, signals in composite_result['composite_signals'].items():
                    if 'weighted_scores' in signals:
                        score += np.mean(signals['weighted_scores'])

            # 基於風險評估
            if 'risk_assessment' in composite_result:
                risk_scores = [risk.get('overall_risk_score', 0) for risk in composite_result['risk_assessment'].values()]
                if risk_scores:
                    score += (1 - np.mean(risk_scores)) * 2  # 低風險加分

            # 基於時間框架一致性
            if 'multi_timeframe_signals' in composite_result:
                consistency_scores = [tf.get('consistency_score', 0) for tf in composite_result['multi_timeframe_signals'].values()]
                if consistency_scores:
                    score += np.mean(consistency_scores)

            # 標準化到10分制
            divisor = len(composite_result.get('composite_signals', {}))
            if divisor > 0:
                return min(10.0, max(0.0, score / divisor))
            else:
                return min(10.0, max(0.0, score))  # 如果沒有信號，直接使用原始分數

        except Exception as e:
            logger.error(f"Error calculating signal quality score: {e}")
            return 5.0  # 默認中等分數

    def _generate_trading_recommendations(self, composite_result: Dict, risk_assessment: Dict) -> List[str]:
        """生成交易建議"""
        try:
            recommendations = []

            # 基於信號質量
            quality_score = composite_result.get('signal_quality_score', 5.0)
            if quality_score > 7.0:
                recommendations.append("強烈信號：建議積極跟隨信號操作")
            elif quality_score > 5.0:
                recommendations.append("中等信號：可謹慎跟隨操作")
            else:
                recommendations.append("弱信號：建議觀望，避免操作")

            # 基於風險評估
            if risk_assessment:
                avg_risk = np.mean([risk.get('overall_risk_score', 0.5) for risk in risk_assessment.values()])
                if avg_risk < 0.3:
                    recommendations.append("低風險環境：可適當增加頭寸")
                elif avg_risk > 0.7:
                    recommendations.append("高風險環境：建議減少頭寸或對沖")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating trading recommendations: {e}")
            return ["建議進一步分析市場狀況"]

    # 輔助方法實現
    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        """計算RSI"""
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, series: pd.Series, fast: int, slow: int, signal: int) -> Dict[str, pd.Series]:
        """計算MACD"""
        ema_fast = series.ewm(span=fast).mean()
        ema_slow = series.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return {'macd': macd, 'signal': signal_line, 'histogram': histogram}

    def _calculate_bollinger_bands(self, series: pd.Series, period: int, std_dev: float) -> Dict[str, pd.Series]:
        """計算布林帶"""
        sma = series.rolling(window=period, min_periods=1).mean()
        rolling_std = series.rolling(window=period, min_periods=1).std()
        upper_band = sma + (rolling_std * std_dev)
        lower_band = sma - (rolling_std * std_dev)
        bandwidth = (upper_band - lower_band) / sma
        return {'upper': upper_band, 'middle': sma, 'lower': lower_band, 'bandwidth': bandwidth}

    def _calculate_stochastic(self, series: pd.Series, k_period: int, d_period: int) -> Dict[str, pd.Series]:
        """計算隨機指標"""
        # 使用指數移動平均作為簡化實現
        lowest_low = series.rolling(window=k_period, min_periods=1).min()
        highest_high = series.rolling(window=k_period, min_periods=1).max()
        percent_k = 100 * (series - lowest_low) / (highest_high - lowest_low)
        percent_d = percent_k.rolling(window=d_period, min_periods=1).mean()
        return {'k': percent_k, 'd': percent_d}

    def _calculate_williams_r(self, series: pd.Series, period: int) -> pd.Series:
        """計算Williams %R"""
        highest_high = series.rolling(window=period, min_periods=1).max()
        lowest_low = series.rolling(window=period, min_periods=1).min()
        return -100 * (highest_high - series) / (highest_high - lowest_low)

    def _calculate_cci(self, series: pd.Series, period: int) -> pd.Series:
        """計算CCI"""
        tp = (series.rolling(window=period, min_periods=1).mean() +
              series.rolling(window=period, min_periods=1).max() +
              series.rolling(window=period, min_periods=1).min()) / 3
        mad = series.rolling(window=period, min_periods=1).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
        return (series - tp) / (0.015 * mad)

    def _extract_indicator_signals(self, indicators: Dict) -> Dict[str, float]:
        """提取指標信號"""
        signals = {}
        total_weight = 0

        for indicator_name, indicator_data in indicators.items():
            if indicator_name.startswith('rsi_'):
                rsi_values = [indicator_data.iloc[-1] if len(indicator_data) > 0 else 50]
                for rsi in rsi_values:
                    if rsi < 30:
                        signals[f'{indicator_name}_oversold'] = 1.0
                    elif rsi > 70:
                        signals[f'{indicator_name}_overbought'] = -1.0
                    else:
                        signals[f'{indicator_name}_neutral'] = 0.0
                    total_weight += 1

        return signals if total_weight > 0 else {}

    def _extract_timeframe_signals(self, timeframe_data: Dict) -> Dict[str, float]:
        """提取時間框架信號"""
        signals = {}
        for timeframe, data in timeframe_data.items():
            if isinstance(data, dict) and 'signal' in data:
                signals[f'timeframe_{timeframe}'] = data['signal']
        return signals

    def _extract_pattern_signals(self, pattern_data: Dict) -> Dict[str, float]:
        """提取模式信號"""
        signals = {}
        for pattern_type, patterns in pattern_data.items():
            # 檢查是否為列表或字典
            pattern_count = 0
            if isinstance(patterns, list):
                pattern_count = len([p for p in patterns if p])
            elif isinstance(patterns, dict):
                pattern_count = sum(1 for p in patterns.values() if p)
            elif isinstance(patterns, bool):
                pattern_count = 1 if patterns else 0

            if pattern_count > 0:
                signals[f'pattern_{pattern_type}'] = pattern_count * 0.1
        return signals

    def _calculate_weighted_signal_scores(self, signals: Dict[str, float]) -> Dict[str, float]:
        """計算加權信號評分"""
        weighted_scores = {}
        total_weight = 0

        for signal_name, signal_value in signals.items():
            weight = self.signal_weights.get('trend_strength', 0.1)  # 默認權重

            # 確保值是數字類型
            if not isinstance(signal_value, (int, float)):
                try:
                    signal_value = float(signal_value) if signal_value is not None else 0.0
                except (ValueError, TypeError):
                    signal_value = 0.0

            # 根據信號類型調整權重
            if 'rsi' in signal_name.lower():
                weight = self.signal_weights.get('momentum_indicators', 0.2)
            elif 'macd' in signal_name.lower():
                weight = self.signal_weights.get('momentum_indicators', 0.2)
            elif 'bb' in signal_name.lower():
                weight = self.signal_weights.get('volatility_signals', 0.15)
            elif 'pattern' in signal_name.lower():
                weight = self.signal_weights.get('pattern_recognition', 0.15)
            elif 'timeframe' in signal_name.lower():
                weight = self.signal_weights.get('multi_timeframe', 0.1)

            weighted_scores[signal_name] = signal_value * weight
            total_weight += weight

        # 計算加權平均值
        if total_weight > 0:
            weighted_scores['weighted_average'] = sum(weighted_scores.values()) / total_weight
            weighted_scores['total_weight'] = total_weight
        else:
            weighted_scores['weighted_average'] = 0

        return weighted_scores

    def _smooth_signals(self, scores: List[float], window: int = 5) -> List[float]:
        """平滑信號"""
        if len(scores) < window:
            return scores

        smoothed = []
        for i in range(len(scores)):
            start_idx = max(0, i - window + 1)
            end_idx = i + 1
            smoothed.append(np.mean(scores[start_idx:end_idx]))

        return smoothed

    def _generate_final_signal(self, signals: Dict) -> float:
        """生成最終信號"""
        if 'weighted_average' in signals:
            return signals['weighted_average']
        elif 'smoothed_signals' in signals and signals['smoothed_signals']:
            return signals['smoothed_signals'][-1] if signals['smoothed_signals'] else 0
        else:
            return 0

    # 風險評估方法
    def _calculate_max_drawdown(self, series: pd.Series) -> float:
        """計算最大回撤"""
        cumulative = (1 + series.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def _calculate_correlation_risk(self, series: pd.Series) -> float:
        """計算相關性風險"""
        if len(series) < 30:
            return 0.5

        # 與自身滯後的相關性
        autocorr = series.autocorr(lag=1)
        return abs(autocorr) if not np.isnan(autocorr) else 0.5

    def _calculate_liquidity_risk(self, series: pd.Series) -> float:
        """計算流動性風險"""
        # 基於價格變化率計算
        volatility = series.pct_change().std()
        return min(1.0, volatility / 0.1)  # 標準化到0-1

    def _calculate_risk_score(self, risk_metrics: Dict) -> float:
        """計算綜合風險評分"""
        weights = {
            'signal_volatility': 0.2,
            'signal_stability': 0.2,
            'market_volatility': 0.3,
            'max_drawdown_risk': 0.2,
            'correlation_risk': 0.1
        }

        score = 0.0
        total_weight = 0

        for metric, weight in weights.items():
            if metric in risk_metrics:
                score += risk_metrics[metric] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.5

    def _classify_risk_level(self, risk_score: float) -> str:
        """分類風險等級"""
        if risk_score < 0.3:
            return 'LOW'
        elif risk_score < 0.6:
            return 'MEDIUM'
        else:
            return 'HIGH'

    def _calculate_signal_stability(self, signals: List[float]) -> float:
        """計算信號穩定性"""
        if len(signals) < 2:
            return 1.0

        signal_changes = np.diff(signals)
        return 1.0 / (1.0 + np.std(signal_changes))

    def _optimize_signals(self, signals: Dict, series: pd.Series) -> Dict:
        """優化信號"""
        # 基於市場波動性調整信號
        market_volatility = series.pct_change().std()
        volatility_adjustment = 1.0 / (1.0 + market_volatility)

        optimized = signals.copy()
        if 'weighted_scores' in optimized:
            optimized['weighted_scores'] = {}
            for key, value in signals['weighted_scores'].items():
                # 確保值是數字類型
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value) if value is not None else 0.0
                    except (ValueError, TypeError):
                        value = 0.0
                optimized['weighted_scores'][key] = value * volatility_adjustment

        return optimized

    def _extract_indicator_signals(self, indicators: Dict) -> Dict[str, float]:
        """提取指標信號（重命名方法）"""
        return self._extract_signals_from_indicators(indicators)

    def _extract_signals_from_indicators(self, indicators: Dict) -> Dict[str, float]:
        """從指標中提取信號"""
        signals = {}

        for indicator_name, indicator_data in indicators.items():
            if isinstance(indicator_data, dict):
                if 'macd' in indicator_data and isinstance(indicator_data['macd'], pd.Series):
                    macd_series = indicator_data['macd']
                    if len(macd_series) > 0:
                        latest_macd = macd_series.iloc[-1]
                        if latest_macd > 0:
                            signals[f'{indicator_name}_bullish'] = 0.5
                        else:
                            signals[f'{indicator_name}_bearish'] = -0.5

        return signals

    # 缺失的方法 - 添加完整功能
    def _generate_short_term_signals(self, series: pd.Series, indicators: Dict) -> Dict[str, float]:
        """生成短期信號 (1-2週)"""
        try:
            signals = {}

            # 基於RSI的短期信號
            if any('rsi' in key for key in indicators.keys()):
                rsi_keys = [k for k in indicators.keys() if 'rsi' in k]
                if rsi_keys:
                    rsi_series = indicators[rsi_keys[0]]
                    if hasattr(rsi_series, 'iloc') and len(rsi_series) > 0:
                        latest_rsi = rsi_series.iloc[-1]
                        if latest_rsi < 30:
                            signals['rsi_oversold'] = 0.8
                        elif latest_rsi > 70:
                            signals['rsi_overbought'] = -0.8

                        # RSI動量
                        if len(rsi_series) >= 3:
                            rsi_change = rsi_series.iloc[-1] - rsi_series.iloc[-3]
                            if rsi_change > 5:
                                signals['rsi_momentum_bullish'] = 0.6
                            elif rsi_change < -5:
                                signals['rsi_momentum_bearish'] = -0.6

            # 基於MACD的短期信號
            if any('macd' in key for key in indicators.keys()):
                macd_keys = [k for k in indicators.keys() if 'macd' in k]
                if macd_keys:
                    macd_series = indicators[macd_keys[0]]
                    if hasattr(macd_series, 'iloc') and len(macd_series) > 0:
                        latest_macd = macd_series.iloc[-1]
                        if latest_macd > 0:
                            signals['macd_bullish'] = 0.7
                        else:
                            signals['macd_bearish'] = -0.7

            # 價格突破信號
            if len(series) >= 5:
                sma_5 = series.rolling(5).mean().iloc[-1]
                current_price = series.iloc[-1]

                if current_price > sma_5 * 1.02:  # 突破2%
                    signals['price_breakout_bullish'] = 0.5
                elif current_price < sma_5 * 0.98:  # 跌破2%
                    signals['price_breakout_bearish'] = -0.5

            return signals

        except Exception as e:
            logger.error(f"Error generating short term signals: {e}")
            return {}

    def _generate_medium_term_signals(self, series: pd.Series, indicators: Dict) -> Dict[str, float]:
        """生成中期信號 (1個月)"""
        try:
            signals = {}

            # 基於移動平均的趨勢信號
            if len(series) >= 20:
                sma_20 = series.rolling(20).mean().iloc[-1]
                current_price = series.iloc[-1]

                if current_price > sma_20:
                    signals['price_above_sma20'] = 0.6
                else:
                    signals['price_below_sma20'] = -0.6

            # 布林帶信號
            if any('bb_' in key for key in indicators.keys()):
                bb_upper_keys = [k for k in indicators.keys() if 'bb_upper' in k]
                bb_lower_keys = [k for k in indicators.keys() if 'bb_lower' in k]

                if bb_upper_keys and bb_lower_keys:
                    upper_series = indicators[bb_upper_keys[0]]
                    lower_series = indicators[bb_lower_keys[0]]
                    current_price = series.iloc[-1]

                    if (hasattr(upper_series, 'iloc') and hasattr(lower_series, 'iloc') and
                        len(upper_series) > 0 and len(lower_series) > 0):

                        upper_band = upper_series.iloc[-1]
                        lower_band = lower_series.iloc[-1]

                        if current_price > upper_band:
                            signals['bb_breakout_upper'] = 0.4
                        elif current_price < lower_band:
                            signals['bb_breakout_lower'] = -0.4

            return signals

        except Exception as e:
            logger.error(f"Error generating medium term signals: {e}")
            return {}

    def _generate_long_term_signals(self, series: pd.Series, indicators: Dict) -> Dict[str, float]:
        """生成長期信號 (3個月+)"""
        try:
            signals = {}

            # 基於長期移動平均的趨勢
            if len(series) >= 50:
                sma_50 = series.rolling(50).mean().iloc[-1]
                current_price = series.iloc[-1]

                if current_price > sma_50:
                    signals['price_above_sma50'] = 0.7
                else:
                    signals['price_below_sma50'] = -0.7

            # 長期動量
            if len(series) >= 20:
                momentum_20 = (series.iloc[-1] - series.iloc[-20]) / series.iloc[-20]
                if momentum_20 > 0.05:  # 5%以上漲幅
                    signals['momentum_bullish'] = 0.6
                elif momentum_20 < -0.05:  # 5%以上跌幅
                    signals['momentum_bearish'] = -0.6

            return signals

        except Exception as e:
            logger.error(f"Error generating long term signals: {e}")
            return {}

    def _identify_support_resistance_levels(self, df: pd.DataFrame, indicators: Dict) -> Dict[str, Any]:
        """識別支撐阻力位"""
        try:
            result = {
                'support_levels': [],
                'resistance_levels': [],
                'current_position': 'neutral'
            }

            for column in df.columns:
                if pd.api.types.is_numeric_dtype(df[column]):
                    series = df[column]

                    if len(series) >= 20:
                        # 計算局部最高點和最低點
                        highs = series.rolling(5, center=True).max()
                        lows = series.rolling(5, center=True).min()

                        # 找支撐位 (局部最低點)
                        support_candidates = []
                        for i in range(2, len(lows)-2):
                            if (lows.iloc[i] == series.iloc[i-2:i+3].min() and
                                lows.iloc[i] < series.iloc[i-2:i+3].mean() * 0.98):
                                support_candidates.append(lows.iloc[i])

                        # 找阻力位 (局部最高點)
                        resistance_candidates = []
                        for i in range(2, len(highs)-2):
                            if (highs.iloc[i] == series.iloc[i-2:i+3].max() and
                                highs.iloc[i] > series.iloc[i-2:i+3].mean() * 1.02):
                                resistance_candidates.append(highs.iloc[i])

                        # 選擇最重要的支撐阻力位
                        if support_candidates:
                            support_levels = sorted(support_candidates)[:3]  # 最低的3個支撐位
                            result['support_levels'].extend([(column, level) for level in support_levels])

                        if resistance_candidates:
                            resistance_levels = sorted(resistance_candidates, reverse=True)[:3]  # 最高的3個阻力位
                            result['resistance_levels'].extend([(column, level) for level in resistance_levels])

                        # 判斷當前價格位置
                        current_price = series.iloc[-1]
                        if result['support_levels'] and result['resistance_levels']:
                            avg_support = np.mean([level[1] for level in result['support_levels'][-2:]])  # 最近2個支撐位
                            avg_resistance = np.mean([level[1] for level in result['resistance_levels'][-2:]])  # 最近2個阻力位

                            if current_price < avg_support:
                                result['current_position'] = 'below_support'
                            elif current_price > avg_resistance:
                                result['current_position'] = 'above_resistance'
                            else:
                                result['current_position'] = 'between_levels'

            return result

        except Exception as e:
            logger.error(f"Error identifying support resistance levels: {e}")
            return {
                'support_levels': [],
                'resistance_levels': [],
                'current_position': 'neutral'
            }

    def _calculate_timeframe_consistency(self, short_signals: Dict, medium_signals: Dict, long_signals: Dict) -> float:
        """計算時間框架信號一致性"""
        try:
            all_signals = []

            # 收集所有信號
            for signal_dict in [short_signals, medium_signals, long_signals]:
                if signal_dict:
                    for signal_name, signal_value in signal_dict.items():
                        if isinstance(signal_value, (int, float)):
                            all_signals.append(signal_value)

            if not all_signals:
                return 0.0

            # 計算信號方向一致性
            positive_signals = sum(1 for s in all_signals if s > 0)
            negative_signals = sum(1 for s in all_signals if s < 0)
            neutral_signals = sum(1 for s in all_signals if s == 0)

            total_signals = len(all_signals)

            # 一致性得分：如果信號方向一致，得分較高
            if positive_signals == total_signals:
                return 1.0  # 所有信號都是看漲
            elif negative_signals == total_signals:
                return -1.0  # 所有信號都是看跌
            elif positive_signals > negative_signals:
                # 多數看漲，但不是全部一致
                consistency = positive_signals / total_signals
                return consistency
            elif negative_signals > positive_signals:
                # 多數看跌，但不是全部一致
                consistency = negative_signals / total_signals
                return -consistency
            else:
                # 信號平衡或中性為主
                return 0.0

        except Exception as e:
            logger.error(f"Error calculating timeframe consistency: {e}")
            return 0.0

    def _identify_trendline_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """識別趨勢線模式"""
        try:
            patterns = {
                'uptrend': False,
                'downtrend': False,
                'sideways': False,
                'trend_strength': 0.0
            }

            if len(series) < 10:
                return patterns

            # 計算線性趨勢
            x = np.arange(len(series))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, series)

            # 判斷趨勢方向
            if slope > 0 and r_value > 0.5:
                patterns['uptrend'] = True
                patterns['trend_strength'] = abs(r_value)
            elif slope < 0 and r_value > 0.5:
                patterns['downtrend'] = True
                patterns['trend_strength'] = abs(r_value)
            else:
                patterns['sideways'] = True
                patterns['trend_strength'] = 0.0

            return patterns

        except Exception as e:
            logger.error(f"Error identifying trendline patterns: {e}")
            return {
                'uptrend': False,
                'downtrend': False,
                'sideways': False,
                'trend_strength': 0.0
            }

    def _identify_volatility_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """識別波動率模式"""
        try:
            patterns = {
                'high_volatility': False,
                'low_volatility': False,
                'volatility_breakout': False,
                'volatility_contraction': False,
                'volatility_trend': 'stable'
            }

            if len(series) < 10:
                return patterns

            # 計算波動率
            returns = series.pct_change().dropna()
            if len(returns) < 5:
                return patterns

            recent_vol = returns.tail(5).std()
            historical_vol = returns.std()

            # 判斷波動率水平
            if recent_vol > historical_vol * 1.2:
                patterns['high_volatility'] = True
                patterns['volatility_trend'] = 'increasing'
            elif recent_vol < historical_vol * 0.8:
                patterns['low_volatility'] = True
                patterns['volatility_trend'] = 'decreasing'

            # 檢測波動率突破
            if recent_vol > historical_vol * 1.5:
                patterns['volatility_breakout'] = True

            # 檢測波動率收縮
            if recent_vol < historical_vol * 0.5:
                patterns['volatility_contraction'] = True

            return patterns

        except Exception as e:
            logger.error(f"Error identifying volatility patterns: {e}")
            return {
                'high_volatility': False,
                'low_volatility': False,
                'volatility_breakout': False,
                'volatility_contraction': False,
                'volatility_trend': 'stable'
            }

    def _identify_price_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """識別價格模式"""
        try:
            patterns = {
                'gap_up': False,
                'gap_down': False,
                'engulfing_bullish': False,
                'engulfing_bearish': False,
                'hammer': False,
                'shooting_star': False,
                'doji': False
            }

            if len(series) < 5:
                return patterns

            # 檢測跳空
            if len(series) >= 2:
                price_change = (series.iloc[-1] - series.iloc[-2]) / series.iloc[-2]
                if price_change > 0.03:  # 3%以上跳空
                    patterns['gap_up'] = True
                elif price_change < -0.03:  # 3%以上跳空下跌
                    patterns['gap_down'] = True

            # 檢測錘子線和射擊之星（需要收盤價和最高最低價）
            # 這裡簡化處理
            recent_prices = series.tail(3)
            if len(recent_prices) >= 3:
                # 判斷是否為十字星
                price_range = recent_prices.max() - recent_prices.min()
                if price_range / recent_prices.mean() < 0.01:  # 價格變化小於1%
                    patterns['doji'] = True

            return patterns

        except Exception as e:
            logger.error(f"Error identifying price patterns: {e}")
            return {
                'gap_up': False,
                'gap_down': False,
                'engulfing_bullish': False,
                'engulfing_bearish': False,
                'hammer': False,
                'shooting_star': False,
                'doji': False
            }

    def _identify_chart_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """識別圖形模式"""
        try:
            patterns = {
                'head_shoulders': False,
                'inverse_head_shoulders': False,
                'double_top': False,
                'double_bottom': False,
                'triangle': False,
                'flag': False
            }

            if len(series) < 20:
                return patterns

            # 簡化的圖形識別邏輯
            # 實際應用中需要更複雜的算法

            return patterns

        except Exception as e:
            logger.error(f"Error identifying chart patterns: {e}")
            return {
                'head_shoulders': False,
                'inverse_head_shoulders': False,
                'double_top': False,
                'double_bottom': False,
                'triangle': False,
                'flag': False
            }

# 全局實例
advanced_signals = AdvancedTechnicalSignals()

# 便捷函數
def generate_advanced_signals(data: List[Dict[str, Any]], data_type: str = 'government') -> Dict[str, Any]:
    """生成高級技術分析信號"""
    return advanced_signals.generate_enhanced_signals(data, data_type)

if __name__ == "__main__":
    print("=" * 80)
    print("Advanced Technical Analysis Signal System")
    print("高級技術分析信號系統")
    print("=" * 80)
    print("Testing advanced signal generation...")
    print()

    # 創建測試數據
    test_data = []
    for i in range(100):
        date = (datetime.now() - timedelta(days=100-i)).strftime('%Y-%m-%d')
        value = 100 + i * 0.5 + np.random.normal(0, 2)
        test_data.append({'date': date, 'price': value, 'volume': 1000000 + i * 10000})

    print(f"Test data: {len(test_data)} records")

    # 生成高級信號
    result = generate_advanced_signals(test_data, 'test')

    if result.get('success'):
        print(f"[OK] Advanced signals generated successfully")
        print(f"Signal quality score: {result['signal_quality_score']:.2f}/10")
        print(f"Processed records: {result['processed_records']}")
        print(f"Numeric columns: {result['numeric_columns']}")

        recommendations = result.get('recommendations', [])
        if recommendations:
            print("Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
    else:
        print(f"[FAIL] {result.get('error', 'Unknown error')}")

    print("\n=== USAGE EXAMPLES ===")
    print("from advanced_ta_signals import generate_advanced_signals")
    print()
    print("# Generate advanced signals from government data")
    print("result = generate_advanced_signals(government_data, 'monetary_base')")
    print("print(f'Signal quality: {result[\"signal_quality_score\"]}')")
    print("print(f'Recommendations: {result[\"recommendations\"]}')")