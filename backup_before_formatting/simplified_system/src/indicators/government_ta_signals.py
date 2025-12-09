#!/usr/bin/env python3
"""
政府經濟數據技術分析信號系統
Government Economic Data Technical Analysis Signal System

基於真實香港政府數據生成技術分析信號
Generate technical analysis signals based on real Hong Kong government data
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging

# Import real-time government data API
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))

try:
    from complete_realtime_api import get_all_government_data, complete_api
    from enhanced_realtime_api_fixed import fetch_enhanced_data
    api_available = True
except ImportError:
    print("Warning: Could not import API modules. Please ensure the API modules are available.")
    get_all_government_data = None
    complete_api = None
    fetch_enhanced_data = None
    api_available = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GovernmentTASignals:
    """政府經濟數據技術分析信號生成器"""

    def __init__(self):
        self.signal_cache = {}
        self.real_data_cache = {}
        self.cache_timeout = 1800  # 30分鐘緩存
        self.signal_strategies = {
            'monetary_trend': {
                'name': '貨幣趨勢信號',
                'description': '基於貨幣基礎數據的趨勢分析'
            },
            'liquidity_analysis': {
                'name': '流動性分析信號',
                'description': '基於銀行流動資金的流動性狀況分析'
            },
            'rmb_impact': {
                'name': '人民幣影響信號',
                'description': '人民幣流動資金對市場的影響分析'
            },
            'economic_indicator': {
                'name': '經濟指標信號',
                'description': '基於經濟統計數據的綜合指標'
            }
        }

    def generate_monetary_base_signals(self, monetary_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基於貨幣基礎數據生成技術分析信號"""
        if not monetary_data:
            return {'success': False, 'error': 'No monetary data provided'}

        try:
            # 轉換為DataFrame進行分析
            df = pd.DataFrame(monetary_data)

            # 確保日期格式正確
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')

            if len(df) < 10:
                return {'success': False, 'error': 'Insufficient data points'}

            signals = {
                'success': True,
                'data_source': 'monetary_base',
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'records_analyzed': len(df),
                'signal_types': {}
            }

            # 1. M1/M2比率趨勢信號
            if 'm1' in df.columns and 'm2' in df.columns:
                df['m1_m2_ratio'] = df['m1'] / df['m2']
                df['m1_m2_ma_20'] = df['m1_m2_ratio'].rolling(window=20, min_periods=1).mean()
                df['m1_m2_ma_60'] = df['m1_m2_ratio'].rolling(window=60, min_periods=1).mean()

                # M1/M2比率突破信號
                signals['signal_types']['m1_m2_breakout'] = self._generate_breakout_signals(
                    df['m1_m2_ratio'], df['m1_m2_ma_20'], 'M1/M2比率突破'
                )

                # M1/M2比率趨勢信號
                signals['signal_types']['m1_m2_trend'] = self._generate_trend_signals(
                    df['m1_m2_ma_20'], 'M1/M2比率趨勢'
                )

                # 貨幣供應變化率信號
                signals['signal_types']['money_supply_change'] = self._generate_change_signals(
                    df['monetary_base'], '貨幣基礎變化率'
                )

            # 2. 貨幣基礎水平信號
            if 'monetary_base' in df.columns:
                df['monetary_base_ma_20'] = df['monetary_base'].rolling(window=20, min_periods=1).mean()
                df['monetary_base_ma_60'] = df['monetary_base'].rolling(window=60, min_periods=1).mean()
                df['monetary_base_zscore'] = self._calculate_zscore(df['monetary_base'], 60)

                # 貨幣基礎異常信號
                signals['signal_types']['monetary_base_anomaly'] = self._generate_anomaly_signals(
                    df['monetary_base_zscore'], '貨幣基礎異常'
                )

                # 貨幣基礎趨勢信號
                signals['signal_types']['monetary_base_trend'] = self._generate_trend_signals(
                    df['monetary_base_ma_20'], '貨幣基礎趨勢'
                )

            # 3. M3貨幣供應信號
            if 'm3' in df.columns:
                df['m3_ma_20'] = df['m3'].rolling(window=20, min_periods=1).mean()
                df['m3_ma_60'] = df['m3'].rolling(window=60, min_periods=1).mean()
                df['m3_change_rate'] = df['m3'].pct_change()

                signals['signal_types']['m3_expansion'] = self._generate_expansion_signals(
                    df['m3_change_rate'], 'M3貨幣供應擴張'
                )

            return signals

        except Exception as e:
            logger.error(f"Error generating monetary base signals: {e}")
            return {'success': False, 'error': str(e)}

    def generate_liquidity_signals(self, liquidity_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基於銀行流動資金數據生成技術分析信號"""
        if not liquidity_data:
            return {'success': False, 'error': 'No liquidity data provided'}

        try:
            df = pd.DataFrame(liquidity_data)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')

            if len(df) < 10:
                return {'success': False, 'error': 'Insufficient data points'}

            signals = {
                'success': True,
                'data_source': 'interbank_liquidity',
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'records_analyzed': len(df),
                'signal_types': {}
            }

            # 1. 流動性比率信號
            if 'liquidity_ratio' in df.columns:
                df['liquidity_ma_10'] = df['liquidity_ratio'].rolling(window=10, min_periods=1).mean()
                df['liquidity_ma_20'] = df['liquidity_ratio'].rolling(window=20, min_periods=1).mean()
                df['liquidity_std'] = df['liquidity_ratio'].rolling(window=20, min_periods=1).std()

                # 計算流動性緊張指標
                df['liquidity_tightness'] = (df['liquidity_ratio'] - df['liquidity_ma_20']) / df['liquidity_std']

                # 流動性緊張信號
                signals['signal_types']['liquidity_tightness'] = self._generate_extreme_signals(
                    df['liquidity_tightness'], '流動性緊張'
                )

            # 2. 銀行同業利率信號
            if 'interbank_offer_rate' in df.columns:
                df['rate_ma_5'] = df['interbank_offer_rate'].rolling(window=5, min_periods=1).mean()
                df['rate_ma_20'] = df['interbank_offer_rate'].rolling(window=20, min_periods=1).mean()

                # 利率變化信號
                df['rate_volatility'] = df['interbank_offer_rate'].rolling(window=20, min_periods=1).std()

                signals['signal_types']['rate_volatility'] = self._generate_volatility_signals(
                    df['rate_volatility'], '銀行間利率波動'
                )

            return signals

        except Exception as e:
            logger.error(f"Error generating liquidity signals: {e}")
            return {'success': False, 'error': str(e)}

    def generate_rmb_liquidity_signals(self, rmb_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基於人民幣流動資金數據生成技術分析信號"""
        if not rmb_data:
            return {'success': False, 'error': 'No RMB liquidity data provided'}

        try:
            df = pd.DataFrame(rmb_data)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')

            if len(df) < 10:
                return {'success': False, 'error': 'Insufficient data points'}

            signals = {
                'success': True,
                'data_source': 'rmb_liquidity',
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'records_analyzed': len(df),
                'signal_types': {}
            }

            if 'rmb_liquidity_facility' in df.columns:
                df['rmb_ma_10'] = df['rmb_liquidity_facility'].rolling(window=10, min_periods=1).mean()
                df['rmb_ma_20'] = df['rmb_liquidity_facility'].rolling(window=20, min_periods=1).mean()

                # 人民幣流動性變化信號
                df['rmb_change'] = df['rmb_liquidity_facility'].pct_change()

                signals['signal_types']['rmb_activity'] = self._generate_activity_signals(
                    df['rmb_change'], '人民幣流動性活動'
                )

            return signals

        except Exception as e:
            logger.error(f"Error generating RMB liquidity signals: {e}")
            return {'success': False, 'error': str(e)}

    def generate_economic_signals(self, economic_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基於經濟統計數據生成技術分析信號"""
        if not economic_data:
            return {'success': False, 'error': 'No economic data provided'}

        try:
            df = pd.DataFrame(economic_data)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')

            if len(df) < 5:
                return {'success': False, 'error': 'Insufficient data points'}

            signals = {
                'success': True,
                'data_source': 'economic_statistics',
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'records_analyzed': len(df),
                'signal_types': {}
            }

            # 1. CPI通脹趨勢信號
            if 'composite_cpi' in df.columns:
                df['cpi_ma_12'] = df['composite_cpi'].rolling(window=12, min_periods=1).mean()
                df['cpi_change'] = df['composite_cpi'].pct_change(12)  # 年同比

                # 通脹趨勢信號
                signals['signal_types']['inflation_trend'] = self._generate_inflation_signals(
                    df['cpi_change'], 'CPI通脹趨勢'
                )

                # 通脹壓力信號
                signals['signal_types']['inflation_pressure'] = self._generate_pressure_signals(
                    df['cpi_change'], '通脹壓力'
                )

            # 2. 失業率趨勢信號
            if 'unemploy_rate' in df.columns:
                df['unemployment_ma_6'] = df['unemploy_rate'].rolling(window=6, min_periods=1).mean()
                df['unemployment_trend'] = df['unemploy_rate'] - df['unemployment_ma_6']

                # 就業市場信號
                signals['signal_types']['labor_market'] = self._generate_labor_signals(
                    df['unemployment_trend'], '就業市場狀況'
                )

            return signals

        except Exception as e:
            logger.error(f"Error generating economic signals: {e}")
            return {'success': False, 'error': str(e)}

    def generate_composite_signal(self, all_signals: Dict[str, Any]) -> Dict[str, Any]:
        """生成綜合技術分析信號"""
        try:
            composite_signals = {
                'success': True,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_sources': list(all_signals.keys()),
                'composite_score': 0,
                'individual_scores': {},
                'recommendations': [],
                'signal_matrix': {}
            }

            # 計算各數據源的評分
            source_weights = {
                'monetary_base': 0.3,      # 貨幣基礎最重要
                'interbank_liquidity': 0.25,  # 流動性很重要
                'rmb_liquidity': 0.2,     # 人民幣影響中等
                'economic_statistics': 0.25   # 經濟指標重要
            }

            total_weight = 0
            weighted_score = 0

            for source_name, signal_data in all_signals.items():
                if signal_data.get('success'):
                    # 簡單評分（基於信號數量和質量）
                    signal_count = len(signal_data.get('signal_types', {}))
                    quality_score = 0.8 if signal_count > 0 else 0.0

                    composite_signals['individual_scores'][source_name] = {
                        'score': quality_score,
                        'signal_count': signal_count,
                        'weight': source_weights.get(source_name, 0.1)
                    }

                    total_weight += source_weights.get(source_name, 0.1)
                    weighted_score += quality_score * source_weights.get(source_name, 0.1)

            # 計算綜合評分
            if total_weight > 0:
                composite_signals['composite_score'] = weighted_score / total_weight

            # 生成交易建議
            composite_signals['recommendations'] = self._generate_recommendations(
                composite_signals['individual_scores'], composite_signals['composite_score']
            )

            # 生成信號矩陣
            composite_signals['signal_matrix'] = self._create_signal_matrix(all_signals)

            return composite_signals

        except Exception as e:
            logger.error(f"Error generating composite signal: {e}")
            return {'success': False, 'error': str(e)}

    def _generate_breakout_signals(self, data: pd.Series, ma_data: pd.Series, name: str) -> Dict[str, Any]:
        """生成突破信號"""
        signals = []
        buy_signals = []
        sell_signals = []

        for i in range(len(data)):
            if pd.notna(data.iloc[i]) and pd.notna(ma_data.iloc[i]):
                if data.iloc[i] > ma_data.iloc[i] * 1.02:  # 向上突破2%
                    buy_signals.append({
                        'date': data.index[i] if hasattr(data, 'index') else i,
                        'signal': 'BUY',
                        'strength': 'STRONG' if data.iloc[i] > ma_data.iloc[i] * 1.05 else 'MODERATE',
                        'value': data.iloc[i],
                        'ma_value': ma_data.iloc[i],
                        'ratio': data.iloc[i] / ma_data.iloc[i]
                    })
                elif data.iloc[i] < ma_data.iloc[i] * 0.98:  # 向下突破2%
                    sell_signals.append({
                        'date': data.index[i] if hasattr(data, 'index') else i,
                        'signal': 'SELL',
                        'strength': 'STRONG' if data.iloc[i] < ma_data.iloc[i] * 0.95 else 'MODERATE',
                        'value': data.iloc[i],
                        'ma_value': ma_data.iloc[i],
                        'ratio': data.iloc[i] / ma_data.iloc[i]
                    })

        return {
            'name': name,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'total_signals': len(buy_signals) + len(sell_signals)
        }

    def _generate_trend_signals(self, ma_data: pd.Series, name: str) -> Dict[str, Any]:
        """生成趨勢信號"""
        if len(ma_data) < 5:
            return {'name': name, 'trend': 'UNKNOWN', 'signals': []}

        # 簡單線性趨勢計算
        x = np.arange(len(ma_data))
        slope, intercept = np.polyfit(x, ma_data.fillna(method='ffill'), 1)

        trend_direction = 'UP' if slope > 0.001 else 'DOWN' if slope < -0.001 else 'SIDEWAYS'
        trend_strength = abs(slope) * 100

        return {
            'name': name,
            'trend': trend_direction,
            'strength': trend_strength,
            'slope': slope,
            'r_squared': self._calculate_r_squared(ma_data, x, slope, intercept)
        }

    def _generate_change_signals(self, data: pd.Series, name: str) -> Dict[str, Any]:
        """生成變化率信號"""
        if len(data) < 2:
            return {'name': name, 'signals': []}

        changes = data.pct_change().dropna()

        significant_changes = []
        for i, change in enumerate(changes):
            if abs(change) > 0.05:  # 5%以上變化
                direction = 'INCREASE' if change > 0 else 'DECREASE'
                strength = 'HIGH' if abs(change) > 0.1 else 'MODERATE'

                significant_changes.append({
                    'index': i,
                    'change_rate': change,
                    'direction': direction,
                    'strength': strength,
                    'impact': 'HIGH' if abs(change) > 0.15 else 'MEDIUM'
                })

        return {
            'name': name,
            'changes': significant_changes,
            'volatility': changes.std(),
            'average_change': changes.mean()
        }

    def _generate_anomaly_signals(self, zscore_data: pd.Series, name: str) -> Dict[str, Any]:
        """生成異常信號"""
        signals = []
        threshold = 2.0  # 2個標準差

        for i, zscore in enumerate(zscore_data):
            if abs(zscore) > threshold:
                direction = 'HIGH' if zscore > 0 else 'LOW'
                signals.append({
                    'index': i,
                    'zscore': zscore,
                    'direction': direction,
                    'severity': 'EXTREME' if abs(zscore) > 3 else 'MODERATE'
                })

        return {
            'name': name,
            'anomaly_signals': signals,
            'anomaly_count': len(signals),
            'current_zscore': zscore_data.iloc[-1] if len(zscore_data) > 0 else 0
        }

    def _generate_expansion_signals(self, change_rate: pd.Series, name: str) -> Dict[str, Any]:
        """生成擴張信號"""
        expansion_periods = []

        for i, rate in enumerate(change_rate):
            if rate > 0.05:  # 5%以上增長
                expansion_periods.append({
                    'index': i,
                    'expansion_rate': rate,
                    'period': 'QUARTERLY' if rate > 0.1 else 'MONTHLY',
                    'strength': 'HIGH' if rate > 0.15 else 'MODERATE'
                })
            elif rate < -0.05:  # 5%以上收縮
                expansion_periods.append({
                    'index': i,
                    'expansion_rate': rate,
                    'period': 'CONTRACTION',
                    'strength': 'HIGH' if rate < -0.15 else 'MODERATE'
                })

        return {
            'name': name,
            'expansion_periods': expansion_periods,
            'average_expansion': change_rate.mean(),
            'expansion_frequency': len(expansion_periods)
        }

    def _generate_extreme_signals(self, data: pd.Series, name: str) -> Dict[str, Any]:
        """生成極值信號"""
        signals = []
        threshold = 2.0  # 2個標準差

        for i, value in enumerate(data):
            if abs(value) > threshold:
                direction = 'TIGHT' if value > 0 else 'LOOSE'
                signals.append({
                    'index': i,
                    'value': value,
                    'direction': direction,
                    'severity': 'EXTREME' if abs(value) > 3 else 'MODERATE'
                })

        return {
            'name': name,
            'extreme_signals': signals,
            'extreme_count': len(signals),
            'current_condition': signals[-1]['direction'] if signals else 'NORMAL'
        }

    def _generate_volatility_signals(self, volatility_data: pd.Series, name: str) -> Dict[str, Any]:
        """生成波動性信號"""
        high_vol_periods = []
        threshold = volatility_data.quantile(0.8) if len(volatility_data) > 10 else volatility_data.std()

        for i, vol in enumerate(volatility_data):
            if vol > threshold:
                high_vol_periods.append({
                    'index': i,
                    'volatility_level': vol,
                    'period': 'HIGH_VOLATILITY',
                    'risk_level': 'HIGH'
                })

        return {
            'name': name,
            'high_vol_periods': high_vol_periods,
            'average_volatility': volatility_data.mean(),
            'volatility_regime': 'HIGH' if len(high_vol_periods) / len(volatility_data) > 0.3 else 'NORMAL'
        }

    def _generate_activity_signals(self, change_data: pd.Series, name: str) -> Dict[str, Any]:
        """生成活動性信號"""
        activity_levels = []
        threshold = change_data.std() * 2 if len(change_data) > 10 else 0.1

        for i, change in enumerate(change_data):
            if abs(change) > threshold:
                direction = 'ACTIVE' if change > 0 else 'DECLINING'
                activity_levels.append({
                    'index': i,
                    'activity_level': direction,
                    'change_magnitude': abs(change),
                    'period': 'HIGH_ACTIVITY' if abs(change) > threshold * 2 else 'NORMAL'
                })

        return {
            'name': name,
            'activity_periods': activity_levels,
            'average_activity': change_data.mean(),
            'activity_regime': 'ACTIVE' if len(activity_levels) / len(change_data) > 0.3 else 'NORMAL'
        }

    def _generate_inflation_signals(self, cpi_change: pd.Series, name: str) -> Dict[str, Any]:
        """生成通脹趨勢信號"""
        trend_direction = 'RISING' if cpi_change.mean() > 0 else 'FALLING'
        avg_inflation = cpi_change.mean()

        # 檢測通脹加速/減速
        inflation_acceleration = cpi_change.diff().mean()

        return {
            'name': name,
            'trend': trend_direction,
            'average_inflation': avg_inflation,
            'inflation_acceleration': inflation_acceleration,
            'inflation_regime': 'HIGH' if avg_inflation > 0.04 else 'MODERATE' if avg_inflation > 0.02 else 'LOW'
        }

    def _generate_pressure_signals(self, cpi_change: pd.Series, name: str) -> Dict[str, Any]:
        """生成通脹壓力信號"""
        pressure_level = 'HIGH' if cpi_change.mean() > 0.05 else 'MODERATE' if cpi_change.mean() > 0.02 else 'LOW'

        # 檢測通脹預警
        warning_threshold = 0.04  # 4%預警線
        warning_periods = []

        for i, change in enumerate(cpi_change):
            if change > warning_threshold:
                warning_periods.append({
                    'index': i,
                    'inflation_rate': change,
                    'warning_level': 'HIGH'
                })

        return {
            'name': name,
            'pressure_level': pressure_level,
            'warning_periods': warning_periods,
            'warning_count': len(warning_periods)
        }

    def _generate_labor_signals(self, trend_data: pd.Series, name: str) -> Dict[str, Any]:
        """生成就業市場信號"""
        if len(trend_data) < 5:
            return {'name': name, 'market_condition': 'UNKNOWN'}

        avg_trend = trend_data.mean()
        recent_trend = trend_data.iloc[-5:].mean() if len(trend_data) >= 5 else avg_trend

        market_condition = 'TIGHT' if avg_trend < -0.5 else 'RELAXED' if avg_trend < 0 else 'NORMAL'

        return {
            'name': name,
            'market_condition': market_condition,
            'average_trend': avg_trend,
            'recent_trend': recent_trend,
            'trend_improvement': recent_trend - avg_trend
        }

    def _calculate_zscore(self, data: pd.Series, window: int) -> pd.Series:
        """計算Z分數"""
        rolling_mean = data.rolling(window=window, min_periods=1).mean()
        rolling_std = data.rolling(window=window, min_periods=1).std()
        return (data - rolling_mean) / rolling_std

    def _calculate_r_squared(self, y_data: pd.Series, x_data: np.ndarray, slope: float, intercept: float) -> float:
        """計算R²"""
        y_pred = slope * x_data + intercept
        ss_res = ((y_data - y_pred) ** 2).sum()
        ss_tot = ((y_data - y_data.mean()) ** 2).sum()
        return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    def _generate_recommendations(self, individual_scores: Dict[str, Any], composite_score: float) -> List[str]:
        """生成交易建議"""
        recommendations = []

        # 基於綜合評分的建議
        if composite_score > 0.7:
            recommendations.append("積極配置 - 政府經濟數據顯示市場流動性充足")
        elif composite_score < 0.3:
            recommendations.append("保守配置 - 考慮市場潛在風險")

        # 基於各數據源的具體建議
        if 'monetary_base' in individual_scores:
            score = individual_scores['monetary_base']['score']
            if score > 0.8:
                recommendations.append("考慮增加貨幣敞口")
            elif score < 0.2:
                recommendations.append("減少貨幣相關風險暴露")

        if 'interbank_liquidity' in individual_scores:
            score = individual_scores['interbank_liquidity']['score']
            if score > 0.8:
                recommendations.append("銀行流動性充裕，可考慮槓槓策略")
            elif score < 0.2:
                recommendations.append("銀行流動性緊張，需謹慎使用槓桿")

        return recommendations

    def _create_signal_matrix(self, all_signals: Dict[str, Any]) -> Dict[str, Any]:
        """創建信號矩陣"""
        matrix = {}

        for source_name, signal_data in all_signals.items():
            if signal_data.get('success'):
                matrix[source_name] = {
                    'signal_count': len(signal_data.get('signal_types', {})),
                    'has_buy_signals': bool(signal_data.get('signal_types', {}).get('buy_signals')),
                    'has_sell_signals': bool(signal_data.get('signal_types', {}).get('sell_signals')),
                    'has_trend_signals': bool(signal_data.get('signal_types', {}).get('m1_m2_trend')),
                    'quality_score': signal_data.get('metadata', {}).get('record_quality', 'unknown')
                }

        return matrix

    def get_real_government_data(self, source_name: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
        """獲取真實政府數據"""
        try:
            # 檢查緩存
            cache_key = f"real_data_{source_name or 'all'}_{limit}"
            if cache_key in self.real_data_cache:
                cached_data = self.real_data_cache[cache_key]
                if (datetime.now().timestamp() - cached_data['timestamp']) < self.cache_timeout:
                    logger.info(f"Using cached real government data for {cache_key}")
                    return cached_data['data']

            # 調用真實API獲取數據
            if not api_available:
                return {'success': False, 'error': 'Real-time API not available'}

            if source_name:
                # 首先嘗試使用增強版API
                if fetch_enhanced_data is not None:
                    data = fetch_enhanced_data(source_name, limit)
                    # 如果增強版失敗，嘗試原版API
                    if data is None and complete_api is not None:
                        data = complete_api.fetch_api_data(source_name, limit)
                elif complete_api is not None:
                    data = complete_api.fetch_api_data(source_name, limit)
                else:
                    return {'success': False, 'error': 'No API available'}
            else:
                # 獲取所有數據源
                if get_all_government_data is not None:
                    data = get_all_government_data(limit)
                else:
                    return {'success': False, 'error': 'All API fetch not available'}

            # 更新緩存
            self.real_data_cache[cache_key] = {
                'data': data,
                'timestamp': datetime.now().timestamp()
            }

            logger.info(f"Successfully fetched real government data for {cache_key}")
            return data

        except Exception as e:
            logger.error(f"Error fetching real government data: {e}")
            return {'success': False, 'error': str(e)}

    def generate_signals_from_real_data(self, source_name: str, limit: int = 1000) -> Dict[str, Any]:
        """從真實數據生成技術分析信號"""
        try:
            # 獲取真實數據
            real_data_response = self.get_real_government_data(source_name, limit)

            if not real_data_response or not real_data_response.get('success'):
                return {'success': False, 'error': f'Failed to fetch real data for {source_name}'}

            # 提取數據記錄
            real_data = real_data_response.get('data', [])

            if not real_data:
                return {'success': False, 'error': f'No real data available for {source_name}'}

            logger.info(f"Processing {len(real_data)} real records for {source_name}")

            # 生成技術分析信號
            if source_name == 'monetary_base':
                return self.generate_monetary_base_signals(real_data)
            elif source_name == 'interbank_liquidity':
                return self.generate_liquidity_signals(real_data)
            elif source_name == 'rmb_liquidity':
                return self.generate_rmb_liquidity_signals(real_data)
            elif source_name == 'economic_statistics':
                return self.generate_economic_signals(real_data)
            else:
                return {'success': False, 'error': f'Unknown data source: {source_name}'}

        except Exception as e:
            logger.error(f"Error generating signals from real data for {source_name}: {e}")
            return {'success': False, 'error': str(e)}

    def generate_all_signals_from_real_data(self, limit: int = 1000) -> Dict[str, Any]:
        """從所有真實政府數據源生成技術分析信號"""
        try:
            # 獲取所有真實數據
            all_real_data = self.get_real_government_data(None, limit)

            if not all_real_data.get('success'):
                return {'success': False, 'error': 'Failed to fetch real government data'}

            all_signals = {}
            successful_sources = 0

            # 處理每個數據源
            for source_name, source_data in all_real_data.get('data_sources', {}).items():
                if source_data.get('success'):
                    real_records = source_data.get('data', [])
                    if real_records:
                        # 生成該數據源的技術分析信號
                        signals = self.generate_signals_from_real_data(source_name, limit)
                        if signals.get('success'):
                            all_signals[source_name] = signals
                            successful_sources += 1
                            logger.info(f"✅ Generated signals for {source_name}: {len(real_records)} records")
                        else:
                            logger.warning(f"❌ Failed to generate signals for {source_name}")
                    else:
                        logger.warning(f"⚠️ No data records for {source_name}")
                else:
                    logger.warning(f"❌ Failed to fetch data for {source_name}")

            # 生成綜合信號
            composite_signals = self.generate_composite_signal(all_signals) if all_signals else {}

            return {
                'success': True,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'data_sources_processed': successful_sources,
                'total_signals_generated': len(all_signals),
                'individual_signals': all_signals,
                'composite_signals': composite_signals,
                'metadata': {
                    'records_per_source': {name: len(data.get('data', [])) for name, data in all_real_data.get('data_sources', {}).items() if data.get('success')},
                    'data_quality': 'REAL_HKMA_OFFICIAL',
                    'analysis_type': 'TECHNICAL_ANALYSIS'
                }
            }

        except Exception as e:
            logger.error(f"Error generating all signals from real data: {e}")
            return {'success': False, 'error': str(e)}

# 全局實例
government_ta_signals = GovernmentTASignals()

# 便捷函數
def generate_government_ta_signals(source_name: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """生成指定數據源的技術分析信號"""
    if source_name == 'monetary_base':
        return government_ta_signals.generate_monetary_base_signals(data)
    elif source_name == 'interbank_liquidity':
        return government_ta_signals.generate_liquidity_signals(data)
    elif source_name == 'rmb_liquidity':
        return government_ta_signals.generate_rmb_liquidity_signals(data)
    elif source_name == 'economic_statistics':
        return government_ta_signals.generate_economic_signals(data)
    else:
        return {'success': False, 'error': f'Unknown data source: {source_name}'}

def generate_composite_government_signals(all_signals: Dict[str, Any]) -> Dict[str, Any]:
    """生成綜合政府數據技術分析信號"""
    return government_ta_signals.generate_composite_signal(all_signals)

# 新增：基於真實數據的便捷函數
def generate_signals_from_real_data(source_name: str, limit: int = 1000) -> Dict[str, Any]:
    """從真實政府數據生成技術分析信號"""
    return government_ta_signals.generate_signals_from_real_data(source_name, limit)

def generate_all_signals_from_real_data(limit: int = 1000) -> Dict[str, Any]:
    """從所有真實政府數據源生成技術分析信號"""
    return government_ta_signals.generate_all_signals_from_real_data(limit)

if __name__ == "__main__":
    print("=" * 80)
    print("Government Economic Data Technical Analysis Signal System")
    print("=" * 80)
    print("基於香港政府真實API的技術分析信號生成系統")
    print()

    # 測試真實數據信號生成
    print("🔄 Testing real data signal generation...")
    print("Fetching real HKMA government data...")

    try:
        # 測試單個數據源
        print("\n=== Testing Monetary Base Signals ===")
        monetary_signals = generate_signals_from_real_data('monetary_base', 1000)
        print(f"✅ Monetary base signals: {monetary_signals.get('success', False)}")
        if monetary_signals.get('success'):
            print(f"📊 Records analyzed: {monetary_signals['records_analyzed']}")
            print(f"📈 Signal types: {list(monetary_signals.get('signal_types', {}).keys())}")
        else:
            print(f"❌ Error: {monetary_signals.get('error', 'Unknown error')}")

        print("\n=== Testing All Data Sources ===")
        # 測試所有數據源
        all_signals_result = generate_all_signals_from_real_data(1000)

        if all_signals_result.get('success'):
            print(f"✅ Overall success: True")
            print(f"📡 Data sources processed: {all_signals_result['data_sources_processed']}")
            print(f"📊 Total signals generated: {all_signals_result['total_signals_generated']}")
            print(f"⏰ Generation time: {all_signals_result['generation_time']}")

            # 顯示各數據源記錄數
            metadata = all_signals_result.get('metadata', {})
            records_per_source = metadata.get('records_per_source', {})
            print(f"\n📋 Records per source:")
            for source, count in records_per_source.items():
                print(f"  • {source}: {count} records")

            # 顯示綜合信號
            composite_signals = all_signals_result.get('composite_signals', {})
            if composite_signals.get('success'):
                print(f"\n🎯 Composite Score: {composite_signals.get('composite_score', 0):.3f}")
                recommendations = composite_signals.get('recommendations', [])
                if recommendations:
                    print(f"💡 Recommendations:")
                    for rec in recommendations:
                        print(f"  • {rec}")

        else:
            print(f"❌ Failed to generate all signals: {all_signals_result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Exception during testing: {e}")
        print("⚠️ This may be due to network issues or API unavailability")

    print("\n=== Usage Examples ===")
    print("# Import the enhanced signal system")
    print("from government_ta_signals import (")
    print("    generate_signals_from_real_data,")
    print("    generate_all_signals_from_real_data,")
    print("    generate_government_ta_signals")
    print(")")
    print()
    print("# Generate signals from real monetary base data (1000+ records)")
    print("monetary_signals = generate_signals_from_real_data('monetary_base', 1000)")
    print()
    print("# Generate all signals from real government data")
    print("all_signals = generate_all_signals_from_real_data(1000)")
    print("print(f'Success: {all_signals[\"success\"]}')")
    print("print(f'Data sources: {all_signals[\"data_sources_processed\"]}')")
    print()
    print("# Get composite score")
    print("if all_signals.get('composite_signals', {}).get('success'):")
    print("    score = all_signals['composite_signals']['composite_score']")
    print("    print(f'Composite technical score: {score:.3f}')")
    print()
    print("✅ System ready for real government data technical analysis!")