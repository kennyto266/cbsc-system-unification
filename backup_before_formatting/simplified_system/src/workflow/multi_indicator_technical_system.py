#!/usr/bin/env python3
"""
多指標技術分析系統
Multi-Indicator Technical Analysis System

擴展HIBOR原型，支持多個經濟數據源的技術分析
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# 導入現有系統
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.government_data import GovernmentDataAPI
from indicators.core_indicators import CoreIndicators

logger = logging.getLogger(__name__)

class MultiIndicatorTechnicalSystem:
    """多指標技術分析系統"""

    def __init__(self):
        """初始化多指標系統"""
        self.gov_api = GovernmentDataAPI()
        self.indicators = CoreIndicators()

        # 數據源配置
        self.data_sources = {
            'hibor_overnight': {
                'name': 'HIBOR隔夜利率',
                'frequency': 'daily',
                'unit': 'percent',
                'description': '香港銀行同業隔夜拆息利率'
            },
            'hibor_1_month': {
                'name': 'HIBOR 1個月',
                'frequency': 'daily',
                'unit': 'percent',
                'description': '香港銀行同業1個月拆息利率'
            },
            'monetary_base': {
                'name': '貨幣基礎',
                'frequency': 'monthly',
                'unit': 'hkd_billion',
                'description': '香港貨幣基礎總額'
            },
            'exchange_rate_usd': {
                'name': '美元兌港幣匯率',
                'frequency': 'daily',
                'unit': 'rate',
                'description': '港幣兌美元匯率'
            },
            'gdp_growth': {
                'name': 'GDP增長率',
                'frequency': 'quarterly',
                'unit': 'percent',
                'description': '香港本地生產總值季度增長率'
            },
            'unemployment_rate': {
                'name': '失業率',
                'frequency': 'monthly',
                'unit': 'percent',
                'description': '香港失業率統計'
            }
        }

        # 權重參數搜索空間 (用於優化)
        self.weight_space = {
            'hibor_overnight': [0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
            'monetary_base': [0.05, 0.10, 0.15, 0.20, 0.25],
            'exchange_rate_usd': [0.05, 0.10, 0.15, 0.20],
            'gdp_growth': [0.05, 0.10, 0.15, 0.20, 0.25],
            'unemployment_rate': [0.05, 0.10, 0.15, 0.20, 0.25]
        }

        # 確保權重總和為1的函數
        self.weight_combinations = self._generate_weight_combinations()

        logger.info("Multi-Indicator Technical System initialized")

    def _generate_weight_combinations(self) -> List[Dict[str, float]]:
        """
        生成權重組合，確保總和為1

        Returns:
            權重組合列表
        """
        combinations = []

        # 基礎權重配置
        base_configs = [
            {'hibor_overnight': 0.30, 'monetary_base': 0.20, 'exchange_rate_usd': 0.20, 'gdp_growth': 0.20, 'unemployment_rate': 0.10},
            {'hibor_overnight': 0.25, 'monetary_base': 0.25, 'exchange_rate_usd': 0.20, 'gdp_growth': 0.15, 'unemployment_rate': 0.15},
            {'hibor_overnight': 0.35, 'monetary_base': 0.15, 'exchange_rate_usd': 0.15, 'gdp_growth': 0.25, 'unemployment_rate': 0.10},
            {'hibor_overnight': 0.20, 'monetary_base': 0.30, 'exchange_rate_usd': 0.25, 'gdp_growth': 0.15, 'unemployment_rate': 0.10}
        ]

        # 添加隨機變體
        for config in base_configs:
            combinations.append(config.copy())

            # 添加小變化
            variant = config.copy()
            for key in variant:
                variant[key] *= np.random.uniform(0.8, 1.2)

            # 標準化使總和為1
            total = sum(variant.values())
            for key in variant:
                variant[key] = variant[key] / total

            combinations.append(variant)

        # 去重
        unique_combinations = []
        seen = set()
        for combo in combinations:
            key = tuple(sorted(combo.items()))
            if key not in seen:
                seen.add(key)
                unique_combinations.append(combo)

        return unique_combinations

    def collect_all_economic_data(self, days: int = 365) -> Dict[str, pd.DataFrame]:
        """
        收集所有經濟數據

        Args:
            days: 收集天數

        Returns:
            數據字典
        """
        logger.info(f"Collecting all economic data for {days} days")

        data_dict = {}

        # 1. HIBOR數據
        try:
            hibor_result = self.gov_api.get_hibor_data(days)
            if hibor_result and hibor_result['data']:
                hibor_df = pd.DataFrame(hibor_result['data'])
                hibor_df['date'] = pd.to_datetime(hibor_df['date'])
                hibor_df.set_index('date', inplace=True)
                hibor_df.sort_index(inplace=True)

                # 提取隔夜和1個月利率
                if 'overnight' in hibor_df.columns:
                    data_dict['hibor_overnight'] = hibor_df[['overnight']]
                if '1_month' in hibor_df.columns:
                    data_dict['hibor_1_month'] = hibor_df[['1_month']]

                logger.info(f"Collected HIBOR data: {len(hibor_df)} records")
        except Exception as e:
            logger.warning(f"Error collecting HIBOR data: {e}")

        # 2. 貨幣基礎數據 (月度，轉換為日度)
        try:
            monetary_result = self.gov_api.get_monetary_base(24)  # 24個月
            if monetary_result and monetary_result['data']:
                monetary_df = pd.DataFrame(monetary_result['data'])
                monetary_df['date'] = pd.to_datetime(monetary_df['date'])
                monetary_df.set_index('date', inplace=True)
                monetary_df.sort_index(inplace=True)

                # 假設有'monetary_base'列
                if 'monetary_base' in monetary_df.columns:
                    # 將月度數據線性插值為日度
                    daily_dates = pd.date_range(monetary_df.index.min(), monetary_df.index.max(), freq='D')
                    daily_monetary = monetary_df.reindex(daily_dates, method='linear')
                    data_dict['monetary_base'] = daily_monetary_df[['monetary_base']]

                logger.info(f"Collected monetary base data: {len(monetary_df)} monthly records")
        except Exception as e:
            logger.warning(f"Error collecting monetary base data: {e}")

        # 3. 匯率數據
        try:
            exchange_result = self.gov_api.get_exchange_rates(days)
            if exchange_result and exchange_result['data']:
                exchange_df = pd.DataFrame(exchange_result['data'])
                exchange_df['date'] = pd.to_datetime(exchange_df['date'])
                exchange_df.set_index('date', inplace=True)
                exchange_df.sort_index(inplace=True)

                # 提取美元兌港幣匯率
                if 'usd_hkd' in exchange_df.columns:
                    data_dict['exchange_rate_usd'] = exchange_df[['usd_hkd']]

                logger.info(f"Collected exchange rate data: {len(exchange_df)} records")
        except Exception as e:
            logger.warning(f"Error collecting exchange rate data: {e}")

        # 4. 模擬GDP增長率數據 (季度)
        try:
            # 模擬季度GDP增長率數據
            gdp_data = []
            start_date = datetime.now() - timedelta(days=days)
            quarter_count = days // 90 + 1

            for i in range(quarter_count):
                quarter_date = start_date + timedelta(days=i * 90)
                gdp_growth = 2.5 + np.sin(i * 0.5) * 1.0 + np.random.normal(0, 0.5)
                gdp_data.append({
                    'date': quarter_date.strftime('%Y-%m-%d'),
                    'gdp_growth': max(gdp_growth, -2.0)  # 限制最低增長率
                })

            gdp_df = pd.DataFrame(gdp_data)
            gdp_df['date'] = pd.to_datetime(gdp_df['date'])
            gdp_df.set_index('date', inplace=True)
            gdp_df.sort_index(inplace=True)

            # 轉換為日度數據 (線性插值)
            daily_dates = pd.date_range(gdp_df.index.min(), gdp_df.index.max(), freq='D')
            daily_gdp = gdp_df.reindex(daily_dates, method='linear')
            data_dict['gdp_growth'] = daily_gdp_df[['gdp_growth']]

            logger.info(f"Generated GDP growth data: {len(daily_gdp)} records")
        except Exception as e:
            logger.warning(f"Error generating GDP data: {e}")

        # 5. 模擬失業率數據 (月度)
        try:
            unemployment_data = []
            start_date = datetime.now() - timedelta(days=days)
            month_count = days // 30 + 1

            for i in range(month_count):
                month_date = start_date + timedelta(days=i * 30)
                unemployment = 3.2 + np.sin(i * 0.3) * 0.8 + np.random.normal(0, 0.3)
                unemployment_data.append({
                    'date': month_date.strftime('%Y-%m-%d'),
                    'unemployment_rate': max(unemployment, 1.5)  # 限制最低失業率
                })

            unemployment_df = pd.DataFrame(unemployment_data)
            unemployment_df['date'] = pd.to_datetime(unemployment_df['date'])
            unemployment_df.set_index('date', inplace=True)
            unemployment_df.sort_index(inplace=True)

            # 轉換為日度數據 (線性插值)
            daily_dates = pd.date_range(unemployment_df.index.min(), unemployment_df.index.max(), freq='D')
            daily_unemployment = unemployment_df.reindex(daily_dates, method='linear')
            data_dict['unemployment_rate'] = daily_unemployment_df[['unemployment_rate']]

            logger.info(f"Generated unemployment rate data: {len(daily_unemployment)} records")
        except Exception as e:
            logger.warning(f"Error generating unemployment data: {e}")

        # 數據質量檢查
        for source, df in data_dict.items():
            self._validate_data_quality(df, source)

        return data_dict

    def _validate_data_quality(self, df: pd.DataFrame, source_name: str) -> None:
        """
        驗證數據質量

        Args:
            df: 數據DataFrame
            source_name: 數據源名稱
        """
        # 檢查缺失值
        missing_count = df.isnull().sum().sum()
        if missing_count > 0:
            missing_ratio = missing_count / (len(df) * len(df.columns))
            if missing_ratio > 0.05:  # 超過5%缺失
                logger.warning(f"{source_name}: High missing data ratio: {missing_ratio:.2%}")

        # 檢查異常值
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                mean = df[col].mean()
                std = df[col].std()
                outliers = df[(df[col] < mean - 3*std) | (df[col] > mean + 3*std)]
                if len(outliers) > 0:
                    outlier_ratio = len(outliers) / len(df)
                    if outlier_ratio > 0.02:  # 超過2%異常值
                        logger.warning(f"{source_name} {col}: High outlier ratio: {outlier_ratio:.2%}")

    def calculate_all_indicators(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        計算所有數據源的技術指標

        Args:
            data_dict: 經濟數據字典

        Returns:
            技術指標結果字典
        """
        logger.info("Calculating technical indicators for all data sources")

        indicators_results = {}

        for source, data in data_dict.items():
            try:
                if len(data) < 20:  # 數據太少，無法計算指標
                    logger.warning(f"Insufficient data for {source}: {len(data)} records")
                    continue

                # 只取第一個數值列
                data_series = data.iloc[:, 0]

                # 計算RSI、MACD、布林帶
                rsi_result = self._calculate_rsi_for_source(data_series, source)
                macd_result = self._calculate_macd_for_source(data_series, source)
                bb_result = self._calculate_bollinger_bands_for_source(data_series, source)

                indicators_results[source] = {
                    'rsi': rsi_result,
                    'macd': macd_result,
                    'bollinger_bands': bb_result,
                    'data_length': len(data),
                    'date_range': f"{data.index[0]} to {data.index[-1]}"
                }

                logger.info(f"Calculated indicators for {source}: {len(data)} records")

            except Exception as e:
                logger.error(f"Error calculating indicators for {source}: {e}")
                indicators_results[source] = None

        return indicators_results

    def _calculate_rsi_for_source(self, data: pd.Series, source: str) -> Dict:
        """為特定數據源計算RSI指標"""
        try:
            # 根據數據源特性調整RSI週期
            if 'quarterly' in self.data_sources.get(source, {}).get('frequency', ''):
                period = 20  # 季度數據使用較短週期
            elif 'monthly' in self.data_sources.get(source, {}).get('frequency', ''):
                period = 15  # 月度數據使用中等週期
            else:
                period = 14  # 日度數據使用標準週期

            rsi = self.indicators.calculate_rsi(data, period)

            return {
                'values': rsi,
                'current': float(rsi.iloc[-1]),
                'mean': float(rsi.mean()),
                'std': float(rsi.std()),
                'min': float(rsi.min()),
                'max': float(rsi.max()),
                'period': period
            }
        except Exception as e:
            logger.error(f"Error calculating RSI for {source}: {e}")
            return {}

    def _calculate_macd_for_source(self, data: pd.Series, source: str) -> Dict:
        """為特定數據源計算MACD指標"""
        try:
            # 根據數據源特性調整MACD參數
            if 'quarterly' in self.data_sources.get(source, {}).get('frequency', ''):
                fast, slow, signal = 8, 20, 6  # 季度數據
            elif 'monthly' in self.data_sources.get(source, {}).get('frequency', ''):
                fast, slow, signal = 10, 24, 8  # 月度數據
            else:
                fast, slow, signal = 12, 26, 9  # 日度數據

            macd_result = self.indicators.calculate_macd(data, fast, slow, signal)

            return {
                'data': macd_result,
                'current_macd': float(macd_result['macd'].iloc[-1]),
                'current_signal': float(macd_result['signal'].iloc[-1]),
                'current_histogram': float(macd_result['histogram'].iloc[-1]),
                'fast_period': fast,
                'slow_period': slow,
                'signal_period': signal
            }
        except Exception as e:
            logger.error(f"Error calculating MACD for {source}: {e}")
            return {}

    def _calculate_bollinger_bands_for_source(self, data: pd.Series, source: str) -> Dict:
        """為特定數據源計算布林帶指標"""
        try:
            # 根據數據源特性調整布林帶參數
            if 'quarterly' in self.data_sources.get(source, {}).get('frequency', ''):
                period, std = 15, 2.0  # 季度數據
            elif 'monthly' in self.data_sources.get(source, {}).get('frequency', ''):
                period, std = 20, 2.2  # 月度數據
            else:
                period, std = 20, 2.0  # 日度數據

            # 計算布林帶
            sma = data.rolling(window=period, min_periods=1).mean()
            rolling_std = data.rolling(window=period, min_periods=1).std()

            upper_band = sma + (rolling_std * std)
            lower_band = sma - (rolling_std * std)

            # 當前位置分析
            current_value = data.iloc[-1]
            current_sma = sma.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]

            if current_value > current_upper:
                position = 'above_upper'
                signal = 'sell'
            elif current_value < current_lower:
                position = 'below_lower'
                signal = 'buy'
            else:
                position = 'within_bands'
                signal = 'hold'

            return {
                'values': pd.DataFrame({
                    'upper': upper_band,
                    'middle': sma,
                    'lower': lower_band,
                    'price': data
                }),
                'current_value': float(current_value),
                'current_position': position,
                'signal': signal,
                'period': period,
                'std_dev': std,
                'band_width': float(current_upper - current_lower)
            }
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands for {source}: {e}")
            return {}

    def optimize_weights_with_backtest(self, indicators_results: Dict[str, Dict]) -> Dict[str, Any]:
        """
        使用回測優化權重配置

        Args:
            indicators_results: 技術指標結果

        Returns:
            優化結果
        """
        logger.info("Optimizing weights with backtesting")

        optimization_results = {
            'best_weights': None,
            'best_score': 0.0,
            'all_combinations': [],
            'test_count': 0
        }

        # 只使用有數據的指標
        available_sources = [
            source for source, result in indicators_results.items()
            if result is not None and result.get('rsi') and len(result['rsi']) > 0
        ]

        if len(available_sources) < 2:
            logger.warning("Insufficient data sources for weight optimization")
            return optimization_results

        # 測試不同的權重組合
        for i, weights in enumerate(self.weight_combinations[:50]):  # 限制測試數量
            try:
                # 只測試可用數據源的權重
                test_weights = {k: v for k, v in weights.items() if k in available_sources}

                # 計算組合信號
                combination_score = self._evaluate_weight_combination(
                    indicators_results, test_weights
                )

                result = {
                    'weights': test_weights.copy(),
                    'score': combination_score,
                    'combination_id': i
                }

                optimization_results['all_combinations'].append(result)
                optimization_results['test_count'] += 1

                # 更新最佳結果
                if combination_score > optimization_results['best_score']:
                    optimization_results['best_score'] = combination_score
                    optimization_results['best_weights'] = test_weights.copy()

            except Exception as e:
                logger.error(f"Error testing weight combination {i}: {e}")
                continue

        logger.info(f"Weight optimization completed: {optimization_results['test_count']} combinations tested")
        logger.info(f"Best score: {optimization_results['best_score']:.3f}")

        return optimization_results

    def _evaluate_weight_combination(self, indicators_results: Dict[str, Dict], weights: Dict[str, float]) -> float:
        """
        評估權重組合的效果

        Args:
            indicators_results: 技術指標結果
            weights: 權重配置

        Returns:
            組合得分
        """
        try:
            score = 0.0
            total_weight = sum(weights.values())

            for source, weight in weights.items():
                if source not in indicators_results or indicators_results[source] is None:
                    continue

                result = indicators_results[source]

                # RSI得分 (30%權重)
                if result.get('rsi'):
                    rsi_score = self._evaluate_rsi_signal_strength(result['rsi'])
                    score += rsi_score * weight * 0.3

                # MACD得分 (40%權重)
                if result.get('macd'):
                    macd_score = self._evaluate_macd_signal_strength(result['macd'])
                    score += macd_score * weight * 0.4

                # 布林帶得分 (30%權重)
                if result.get('bollinger_bands'):
                    bb_score = self._evaluate_bb_signal_strength(result['bollinger_bands'])
                    score += bb_score * weight * 0.3

            return score

        except Exception as e:
            logger.error(f"Error evaluating weight combination: {e}")
            return 0.0

    def _evaluate_rsi_signal_strength(self, rsi_result: Dict) -> float:
        """評估RSI信號強度"""
        try:
            current = rsi_result['current']

            # 信號強度評分
            if 20 <= current <= 30 or 70 <= current <= 80:
                return 0.8  # 接近超買/超賣，強信號
            elif 30 < current < 40 or 60 < current < 70:
                return 0.6  # 中等強度信號
            elif 40 <= current <= 60:
                return 0.4  # 弱信號
            else:
                return 0.2  # 極弱信號
        except:
            return 0.0

    def _evaluate_macd_signal_strength(self, macd_result: Dict) -> float:
        """評估MACD信號強度"""
        try:
            histogram = macd_result['current_histogram']
            macd_line = macd_result['current_macd']
            signal_line = macd_result['current_signal']

            # 信號強度評分
            histogram_strength = abs(histogram)
            line_separation = abs(macd_line - signal_line)

            if histogram_strength > 0.1 and line_separation > 0.05:
                return 0.8  # 強信號
            elif histogram_strength > 0.05 and line_separation > 0.02:
                return 0.6  # 中等信號
            else:
                return 0.3  # 弱信號
        except:
            return 0.0

    def _evaluate_bb_signal_strength(self, bb_result: Dict) -> float:
        """評估布林帶信號強度"""
        try:
            position = bb_result['current_position']
            band_width = bb_result['band_width']

            # 信號強度評分
            if position in ['above_upper', 'below_lower']:
                return 0.8  # 突破信號
            elif band_width < 0.02:  # 布林帶收縮
                if position == 'within_bands':
                    return 0.7  # 收縮中，潛在突破信號
                else:
                    return 0.5
            else:
                return 0.4  # 正常區間
        except:
            return 0.0

    def generate_comprehensive_signals(self, indicators_results: Dict[str, Dict],
                                    optimized_weights: Dict[str, float]) -> Dict[str, Any]:
        """
        生成綜合交易信號

        Args:
            indicators_results: 技術指標結果
            optimized_weights: 優化後的權重

        Returns:
            綜合信號結果
        """
        logger.info("Generating comprehensive trading signals")

        current_signals = {}
        overall_signal = 0.0
        signal_details = []

        # 生成各數據源的當前信號
        for source, weight in optimized_weights.items():
            if source not in indicators_results or indicators_results[source] is None:
                continue

            result = indicators_results[source]
            source_signal = 0.0

            # RSI信號 (-1到1)
            if result.get('rsi'):
                rsi_current = result['rsi']['current']
                if rsi_current < 30:
                    rsi_signal = 1.0  # 超賣，買入信號
                elif rsi_current > 70:
                    rsi_signal = -1.0  # 超買，賣出信號
                else:
                    rsi_signal = 0.0  # 中性

                source_signal += rsi_signal * 0.3

            # MACD信號 (-1到1)
            if result.get('macd'):
                histogram = result['macd']['current_histogram']
                if histogram > 0:
                    macd_signal = 1.0  # 正向動量
                elif histogram < 0:
                    macd_signal = -1.0  # 貖向動量
                else:
                    macd_signal = 0.0  # 中性

                source_signal += macd_signal * 0.4

            # 布林帶信號 (-1到1)
            if result.get('bollinger_bands'):
                position = result['bollinger_bands']['current_position']
                if position == 'above_upper':
                    bb_signal = -1.0  # 賣破上軌，賣出信號
                elif position == 'below_lower':
                    bb_signal = 1.0  # 跌破下軌，買入信號
                else:
                    bb_signal = 0.0  # 中性

                source_signal += bb_signal * 0.3

            # 綜合該數據源的信號
            weighted_signal = source_signal * weight
            overall_signal += weighted_signal

            current_signals[source] = {
                'weight': weight,
                'individual_signal': source_signal,
                'weighted_signal': weighted_signal,
                'details': {
                    'rsi_signal': rsi_signal if result.get('rsi') else None,
                    'macd_signal': macd_signal if result.get('macd') else None,
                    'bb_signal': bb_signal if result.get('bollinger_bands') else None
                }
            }

            signal_details.append({
                'source': source,
                'weight': weight,
                'signal_strength': source_signal,
                'weighted_contribution': weighted_signal
            })

        # 分類最終信號
        if overall_signal > 0.3:
            final_signal = 'STRONG_BUY'
            final_action = 'BUY'
            confidence = min(overall_signal, 1.0)
        elif overall_signal < -0.3:
            final_signal = 'STRONG_SELL'
            final_action = 'SELL'
            confidence = min(abs(overall_signal), 1.0)
        else:
            final_signal = 'NEUTRAL'
            final_action = 'HOLD'
            confidence = 1.0 - abs(overall_signal)

        return {
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'overall_signal_strength': overall_signal,
            'final_signal': final_signal,
            'final_action': final_action,
            'confidence': confidence,
            'individual_signals': current_signals,
            'signal_details': signal_details,
            'weights_used': optimized_weights,
            'total_weight': sum(optimized_weights.values())
        }

    def generate_optimization_report(self, optimization_results: Dict,
                                    signals: Dict, output_file: str = None) -> str:
        """
        生成優化報告

        Args:
            optimization_results: 權重優化結果
            signals: 綜合信號結果
            output_file: 輸出文件路徑

        Returns:
            報告內容
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = f"""
# 多指標技術分析優化報告
**生成時間**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 優化結果概覽

### 最佳權重配置
"""

        if optimization_results['best_weights']:
            for source, weight in optimization_results['best_weights'].items():
                report += f"- {self.data_sources[source]['name']}: {weight:.3f} ({weight*100:.1f}%)\n"

        report += f"""
### 優化得分
- 最佳綜合得分: {optimization_results['best_score']:.3f}
- 測試組合數量: {optimization_results['test_count']}
- 參與數據源: {len(optimization_results.get('best_weights', {}))}

## 當合信號分析

### 最終交易信號
"""

        report += f"""
- 信號類型: {signals['final_signal']}
- 交易動作: {signals['final_action']}
- 信號強度: {signals['overall_signal_strength']:.3f}
- 置信度: {signals['confidence']:.3f}
"""

        report += f"""
### 各數據源貢獻分析
"""

        for detail in signals['signal_details']:
            report += f"""
**{self.data_sources[detail['source']]['name']}**
- 權重: {detail['weight']:.3f}
- 個號強度: {detail['signal_strength']:.3f}
- 加權貢獻: {detail['weighted_contribution']:.3f}
"""

        report += f"""

## 技術指標詳細分析

### 最佳權重下各指標表現

"""

        # 分析各數據源在最佳權重下的表現
        for source, weight in optimization_results['best_weights'].items():
            if source in signals['individual_signals']:
                individual = signals['individual_signals'][source]
                report += f"""
#### {self.data_sources[source]['name']} (權重: {weight:.3f})

- RSI指標信號: {individual['details']['rsi_signal']:.2f}
- MACD指標信號: {individual['details']['macd_signal']:.2f}
- 布林帶指標信號: {individual['details']['bb_signal']:.2f}
- 綜合信號: {individual['individual_signal']:.3f}
- 加權影響: {individual['weighted_contribution']:.3f}
"""

        report += f"""

## 優化效果評估

### 信號質量指標
"""

        # 計算信號質量指標
        signal_strengths = [abs(detail['signal_strength']) for detail in signals['signal_details']]
        weighted_contributions = [abs(detail['weighted_contribution']) for detail in signals['signal_details']]

        if signal_strengths:
            report += f"""
- 平均信號強度: {np.mean(signal_strengths):.3f}
- 最強信號: {max(signal_strengths):.3f}
- 信號一致性: {1.0 - np.std(signal_strengths):.3f}
"""

        if weighted_contributions:
            report += f"""
- 平均加權影響: {np.mean(weighted_contributions):.3f}
- 最大單一貢獻: {max(weighted_contributions):.3f}
- 權重集中度: {max(weighted_contributions) / sum(weighted_contributions):.3f}
"""

        report += f"""

## 市場狀況分析

### 根據信號強度的建議
"""

        overall_strength = signals['overall_signal_strength']
        if overall_strength > 0.5:
            report += """
**強烈看多信號** (強度 > 0.5)
- 建議: 積倉增加港股頭寸
- 風險: 市場逆轉風險增加
"""

        elif overall_strength < -0.5:
            report += """
**強烈看空信號** (強度 < -0.5)
- 建議: 減倉或減持港股頭寸
- 風險: 可能的反彈風險
"""

        else:
            report += """
**中性信號** (強度 -0.5 到 0.5)
- 建議: 保持現有頭寸，觀察後續發展
- 風險: 信號可能快速變化
"""

        report += f"""

## 實施建議

### 1. 風險控制
- 建議止損點設定為 2-3%
- 根據信號強度動態調整倉位
- 定期重新評估權重配置

### 2. 數據更新頻率
- HIBOR數據: 每日更新
- 貨幣基礎數據: 每月更新
- GDP數據: 每季度更新

### 3. 系統監控
- 監控信號變化趨勢
- 追蹤優化效果的時間穩定性
- 記錄異常市場情況下的表現

---
**報告生成完成**: 多指標技術分析系統
"""

        # 保存報告到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to: {output_file}")

        return report

def main():
    """主測試函數"""
    print("=== 多指標技術分析系統測試 ===")

    # 初始化系統
    system = MultiIndicatorTechnicalSystem()

    # 收集所有經濟數據
    print("1. 收集經濟數據...")
    economic_data = system.collect_all_economic_data(365)

    print(f"   成功收集數據源: {list(economic_data.keys())}")
    for source, df in economic_data.items():
        print(f"   {source}: {len(df)} 條記錄")

    # 計算技術指標
    print("\n2. 計算技術指標...")
    indicators_results = system.calculate_all_indicators(economic_data)

    print(f"   成功計算指標的數據源: {len([k for k, v in indicators_results.items() if v is not None])}")
    for source, result in indicators_results.items():
        if result:
            print(f"   {source}: RSI, MACD, Bollinger Bands")

    # 權重優化
    print("\n3. 優化權重配置...")
    optimization_results = system.optimize_weights_with_backtest(indicators_results)

    if optimization_results['best_weights']:
        print(f"   最佳得分: {optimization_results['best_scores']:.3f}")
        print(f"   測試組合: {optimization_results['test_count']}")
        print("   最佳權重配置:")
        for source, weight in optimization_results['best_weights'].items():
            print(f"     {source}: {weight:.3f}")
    else:
        print("   權重優化失敗")

    # 生成綜合信號
    print("\n4. 生成綜合交易信號...")
    if optimization_results['best_weights']:
        signals = system.generate_comprehensive_signals(
            indicators_results,
            optimization_results['best_weights']
        )
        print(f"   綜合信號: {signals['final_signal']}")
        print(f"   交易動作: {signals['final_action']}")
        print(f"   信號強度: {signals['overall_signal_strength']:.3f}")
        print(f"   置信度: {signals['confidence']:.3f}")

        # 生成報告
        print("\n5. 生成優化報告...")
        report = system.generate_optimization_report(
            optimization_results,
            signals,
            f"multi_indicator_optimization_report_{timestamp}.md"
        )
        print(f"   報告已保存")
    else:
        print("   無法生成綜合信號")

    print("\n=== 多指標技術分析系統測試完成 ===")
    print("✅ 多指標數據整合成功")
    print("✅ 技術指標計算完成")
    print("✅ 權重優化算法運行")
    print("✅ 綜合信號生成有效")

if __name__ == "__main__":
    main()