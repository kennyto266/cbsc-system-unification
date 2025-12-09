#!/usr/bin/env python3
"""
Test Enhanced Core Indicators System
測試增強核心指標系統
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedCoreIndicators:
    """
    增強核心技術指標計算引擎
    Enhanced Core Technical Indicators Engine
    """

    def __init__(self):
        """初始化增強核心指標引擎"""
        self.cache = {}
        self.cache_timeout = 300

        # 數據類型檢測配置
        self.rate_data_keywords = ['rate', 'interest', 'hibor', 'yield', 'liquidity']
        self.flow_data_keywords = ['flow', 'change', 'movement', 'activity']
        self.ratio_data_keywords = ['ratio', 'index', 'level']

        logger.info("Enhanced Core Technical Indicators Engine initialized")

    def detect_data_type(self, data: pd.Series, column_name: str = None) -> str:
        """檢測數據類型並返回適配策略"""
        if data.empty:
            return 'unknown'

        # 基於列名判斷
        if column_name:
            col_lower = column_name.lower()
            if any(keyword in col_lower for keyword in self.rate_data_keywords):
                return 'rate_data'
            elif any(keyword in col_lower for keyword in self.flow_data_keywords):
                return 'flow_data'
            elif any(keyword in col_lower for keyword in self.ratio_data_keywords):
                return 'ratio_data'

        # 基於數據特徵判斷
        values = data.dropna()
        if len(values) < 10:
            return 'unknown'

        # 檢查是否為利率類型
        positive_ratio = (values > 0).mean()
        if positive_ratio > 0.9 and values.max() < 100:
            return 'rate_data'

        # 檢查是否為流量數據
        has_negative = (values < 0).any()
        if has_negative:
            return 'flow_data'

        return 'ratio_data'

    def calculate_sma(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """計算簡單移動平均線"""
        if len(prices) < period:
            logger.warning(f"Insufficient data for SMA{period}: need {period}, have {len(prices)}")
            return pd.Series([np.nan] * len(prices), index=prices.index)

        return prices.rolling(window=period, min_periods=1).mean()

    def calculate_ema(self, prices: pd.Series, period: int = 26) -> pd.Series:
        """計算指數移動平均線"""
        if len(prices) < period:
            logger.warning(f"Insufficient data for EMA{period}: need {period}, have {len(prices)}")
            return pd.Series([np.nan] * len(prices), index=prices.index)

        return prices.ewm(span=period, adjust=False).mean()

    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """計算MACD指標"""
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

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算相對強弱指數"""
        if len(prices) < period + 1:
            logger.warning(f"Insufficient data for RSI{period}: need {period + 1}, have {len(prices)}")
            return pd.Series([50.0] * len(prices), index=prices.index)

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()

        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50.0)

        return rsi

    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """計算布林帶"""
        if len(prices) < period:
            return {
                'upper': pd.Series([np.nan] * len(prices), index=prices.index),
                'middle': pd.Series([np.nan] * len(prices), index=prices.index),
                'lower': pd.Series([np.nan] * len(prices), index=prices.index)
            }

        middle = prices.rolling(window=period, min_periods=1).mean()
        std = prices.rolling(window=period, min_periods=1).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }

    # ==================== 增強方法 ====================

    def calculate_sma_non_price(self, data: pd.Series, period: int = None, column_name: str = None) -> Tuple[pd.Series, Dict]:
        """為非價格數據計算SMA"""
        data_type = self.detect_data_type(data, column_name)

        # 自動適配週期
        if period is None:
            if data_type == 'rate_data':
                period = 20
            elif data_type == 'flow_data':
                period = 30
            else:  # ratio_data
                period = 25

        sma = self.calculate_sma(data, int(period))

        adaptation_info = {
            'data_type': data_type,
            'period_used': int(period),
            'data_length': len(data),
            'adaptation_reason': f'Adapted for {data_type}'
        }

        return sma, adaptation_info

    def calculate_rsi_non_price(self, data: pd.Series, period: int = None, column_name: str = None) -> Tuple[pd.Series, Dict]:
        """為非價格數據計算RSI"""
        data_type = self.detect_data_type(data, column_name)

        if period is None:
            if data_type == 'rate_data':
                period = 14
            elif data_type == 'flow_data':
                period = 21
            else:  # ratio_data
                period = 16

        rsi = self.calculate_rsi(data, int(period))

        adaptation_info = {
            'data_type': data_type,
            'period_used': int(period),
            'data_length': len(data),
            'adaptation_reason': f'Optimized for {data_type}'
        }

        return rsi, adaptation_info

    def calculate_macd_non_price(self, data: pd.Series, fast: int = None, slow: int = None,
                                signal: int = None, column_name: str = None) -> Dict:
        """為非價格數據計算MACD"""
        data_type = self.detect_data_type(data, column_name)

        # 自動適配參數
        if fast is None or slow is None:
            if data_type == 'rate_data':
                fast, slow = 12, 26
            elif data_type == 'flow_data':
                fast, slow = 18, 35
            else:  # ratio_data
                fast, slow = 10, 22

        if signal is None:
            signal = 9

        macd_result = self.calculate_macd(data, int(fast), int(slow), int(signal))

        adaptation_info = {
            'data_type': data_type,
            'parameters_used': {'fast': int(fast), 'slow': int(slow), 'signal': int(signal)},
            'data_length': len(data)
        }

        return {
            'macd': macd_result['macd'],
            'signal': macd_result['signal'],
            'histogram': macd_result['histogram'],
            'adaptation_info': adaptation_info
        }

    def calculate_rate_spread(self, rate_data_short: pd.Series, rate_data_long: pd.Series) -> Dict:
        """計算利率期限結構利差"""
        # 確保數據對齊
        common_index = rate_data_short.index.intersection(rate_data_long.index)
        short_aligned = rate_data_short.loc[common_index]
        long_aligned = rate_data_long.loc[common_index]

        # 計算利差
        spread = long_aligned - short_aligned
        spread_mean = spread.rolling(window=20, min_periods=1).mean()
        spread_std = spread.rolling(window=20, min_periods=1).std()

        return {
            'spread': spread,
            'spread_mean': spread_mean,
            'spread_zscore': (spread - spread_mean) / spread_std,
            'metadata': {
                'average_spread': spread.mean(),
                'spread_volatility': spread.std(),
                'data_points': len(spread)
            }
        }

    def calculate_comprehensive_indicators(self, df: pd.DataFrame, target_columns: List[str] = None) -> Dict[str, Dict]:
        """為DataFrame計算全面的技術指標"""
        if target_columns is None:
            # 自動選擇數值列
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # 排除日期列
            target_columns = [col for col in numeric_cols if 'date' not in col.lower()]

        results = {}

        for column in target_columns:
            if column not in df.columns:
                continue

            data = df[column].dropna()
            if len(data) < 20:
                continue

            logger.info(f"Calculating indicators for column: {column}")

            column_results = {
                'data_type': self.detect_data_type(data, column),
                'data_length': len(data),
                'indicators': {}
            }

            try:
                # 趨勢指標
                sma, sma_info = self.calculate_sma_non_price(data, column_name=column)
                ema = self.calculate_ema(data, 20)
                macd_result = self.calculate_macd_non_price(data, column_name=column)

                column_results['indicators']['sma'] = {'values': sma, 'info': sma_info}
                column_results['indicators']['ema'] = {'values': ema}
                column_results['indicators']['macd'] = macd_result

                # 動量指標
                rsi, rsi_info = self.calculate_rsi_non_price(data, column_name=column)
                column_results['indicators']['rsi'] = {'values': rsi, 'info': rsi_info}

                # 波動率指標
                bb_result = self.calculate_bollinger_bands(data)
                column_results['indicators']['bollinger_bands'] = bb_result

                results[column] = column_results

            except Exception as e:
                logger.error(f"Error calculating indicators for column {column}: {e}")
                results[column] = {
                    'error': str(e),
                    'data_type': self.detect_data_type(data, column),
                    'data_length': len(data)
                }

        return results

    def save_indicators_results(self, results: Dict, output_path: str = None):
        """保存指標計算結果"""
        if output_path is None:
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'data/enhanced_indicators_results_{timestamp}.json'

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 準備可序列化的結果
        serializable_results = {}
        for column, data in results.items():
            if 'error' in data:
                serializable_results[column] = data
            else:
                serializable_data = {
                    'data_type': data['data_type'],
                    'data_length': data['data_length']
                }

                if 'indicators' in data:
                    serializable_data['indicators'] = {}
                    for indicator_name, indicator_data in data['indicators'].items():
                        if isinstance(indicator_data, dict) and 'values' in indicator_data:
                            # 保存統計信息
                            values = indicator_data['values'].dropna()
                            if not values.empty:
                                serializable_data['indicators'][indicator_name] = {
                                    'mean': float(values.mean()),
                                    'std': float(values.std()),
                                    'min': float(values.min()),
                                    'max': float(values.max()),
                                    'latest': float(values.iloc[-1]),
                                    'info': indicator_data.get('info', {}),
                                    'data_points': len(values)
                                }
                        else:
                            serializable_data['indicators'][indicator_name] = indicator_data

                serializable_results[column] = serializable_data

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Indicators results saved to: {output_path}")
        return output_path


def main():
    """主測試函數"""
    # 創建增強核心指標引擎
    enhanced_indicators = EnhancedCoreIndicators()

    # 加載對齊後的數據
    aligned_data_dir = Path('data/aligned')
    data_dict = {}

    print("[START] Enhanced Core Indicators Testing")
    print("=" * 60)

    # 加載已對齊的數據
    for file_path in aligned_data_dir.glob('*_aligned_*.csv'):
        source_name = file_path.stem.split('_aligned_')[0]
        try:
            df = pd.read_csv(file_path)
            if not df.empty and 'date' in df.columns:
                data_dict[source_name] = df
                print(f"[LOADED] {source_name}: {len(df)} records, {len(df.columns)} columns")
        except Exception as e:
            print(f"[ERROR] Failed to load {source_name}: {e}")

    if not data_dict:
        print("[ERROR] No aligned data found. Please run data alignment first.")
        return

    # 為每個數據源計算全面指標
    for source_name, df in data_dict.items():
        print(f"\n[PROCESSING] {source_name}")
        print("-" * 40)

        try:
            # 計算全面指標
            results = enhanced_indicators.calculate_comprehensive_indicators(df)

            print(f"Data type analysis:")
            for column, data in results.items():
                if 'error' not in data:
                    print(f"  {column}: {data['data_type']} ({data['data_length']} points)")

                    if 'indicators' in data:
                        indicators = data['indicators']
                        print(f"    Calculated indicators: {list(indicators.keys())}")

                        # 顯示SMA信息
                        if 'sma' in indicators and 'info' in indicators['sma']:
                            sma_info = indicators['sma']['info']
                            print(f"    SMA adaptation: {sma_info.get('adaptation_reason', 'Unknown')}")

                        # 顯示RSI信息
                        if 'rsi' in indicators and 'info' in indicators['rsi']:
                            rsi_info = indicators['rsi']['info']
                            print(f"    RSI adaptation: {rsi_info.get('adaptation_reason', 'Unknown')}")

            # 保存結果
            output_path = enhanced_indicators.save_indicators_results(
                results, f'data/enhanced_indicators_{source_name}.json'
            )
            print(f"[SAVED] Results saved to: {output_path}")

        except Exception as e:
            print(f"[ERROR] Failed to process {source_name}: {e}")

    print(f"\n[COMPLETE] Enhanced Core Indicators testing completed successfully!")


if __name__ == "__main__":
    main()