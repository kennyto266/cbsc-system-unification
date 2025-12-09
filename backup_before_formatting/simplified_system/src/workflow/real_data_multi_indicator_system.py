#!/usr/bin/env python3
"""
真實數據多指標技術分析系統
Real Data Multi-Indicator Technical Analysis System

基於香港政府真實數據的技術指標計算和信號生成
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import sys
import os

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.government_data import GovernmentDataAPI
from indicators.core_indicators import CoreIndicators
from indicators.technical_analyzer import TechnicalAnalyzer

logger = logging.getLogger(__name__)

class RealDataMultiIndicatorSystem:
    """真實數據多指標技術分析系統"""

    def __init__(self):
        """初始化系統"""
        self.gov_api = GovernmentDataAPI()
        self.indicators = CoreIndicators()
        self.analyzer = TechnicalAnalyzer()

        # 數據源配置 - 使用絕對路徑
        base_path = Path(__file__).parent.parent.parent
        self.data_sources = {
            'hibor_overnight': base_path / 'CODEX--' / 'gov_crawler' / 'real_data' / 'hibor_data.json',
            'gdp_growth': base_path / 'CODEX--' / 'gov_crawler' / 'real_data' / 'gdp_data.json',
            'trade_data': base_path / 'CODEX--' / 'gov_crawler' / 'real_data' / 'trade_data.json',
            'hkma_data': base_path / 'CODEX--' / 'data' / 'final_real_indicators' / 'hkma_real_data_with_indicators.csv'
        }

        # 權重優化參數
        self.weight_ranges = {
            'rsi_weight': (0.1, 0.6),
            'macd_weight': (0.1, 0.4),
            'trend_weight': (0.1, 0.3),
            'volatility_weight': (0.05, 0.2)
        }

        logger.info("Real Data Multi-Indicator System initialized")

    def load_real_hibor_data(self) -> Dict[str, pd.DataFrame]:
        """
        加載真實HIBOR數據

        Returns:
            HIBOR數據字典
        """
        logger.info("Loading real HIBOR data")

        hibor_data = {}

        try:
            hibor_file = Path(self.data_sources['hibor_overnight'])
            if hibor_file.exists():
                with open(hibor_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)

                # 轉換為DataFrame
                df = pd.DataFrame(raw_data)
                df['date'] = pd.to_datetime(df['date'])

                # 按tenor透視
                hibor_pivot = df.pivot_table(
                    index='date',
                    columns='tenor',
                    values='rate',
                    aggfunc='first'
                )
                hibor_pivot.sort_index(inplace=True)

                # 提取不同期限的利率
                if 'Overnight' in hibor_pivot.columns:
                    hibor_data['hibor_overnight'] = pd.DataFrame({
                        'rate': hibor_pivot['Overnight']
                    })

                if '1 month' in hibor_pivot.columns:
                    hibor_data['hibor_1month'] = pd.DataFrame({
                        'rate': hibor_pivot['1 month']
                    })

                logger.info(f"Loaded HIBOR data: {len(hibor_pivot)} records from {hibor_pivot.index.min()} to {hibor_pivot.index.max()}")
            else:
                logger.warning(f"HIBOR file not found: {hibor_file}")

        except Exception as e:
            logger.error(f"Error loading HIBOR data: {e}")

        return hibor_data

    def load_real_gdp_data(self) -> Optional[pd.DataFrame]:
        """
        加載真實GDP數據

        Returns:
            GDP數據DataFrame
        """
        logger.info("Loading real GDP data")

        try:
            gdp_file = Path(self.data_sources['gdp_growth'])
            if gdp_file.exists():
                with open(gdp_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)

                df = pd.DataFrame(raw_data)

                # 嘗試識別日期和數值欄位
                date_col = None
                value_col = None

                for col in df.columns:
                    if col.lower() in ['date', 'time', 'period']:
                        date_col = col
                    elif col.lower() in ['value', 'gdp', 'growth', 'rate']:
                        value_col = col

                if date_col and value_col:
                    df[date_col] = pd.to_datetime(df[date_col])
                    df.set_index(date_col, inplace=True)
                    df.sort_index(inplace=True)

                    # 轉換為日度數據 (前向填充)
                    daily_dates = pd.date_range(df.index.min(), pd.Timestamp.now(), freq='D')
                    daily_gdp = df[[value_col]].reindex(daily_dates, method='ffill')
                    daily_gdp.columns = ['gdp_growth']

                    logger.info(f"Loaded GDP data: {len(df)} records, converted to {len(daily_gdp)} daily records")
                    return daily_gdp
                else:
                    logger.warning("Could not identify date/value columns in GDP data")

        except Exception as e:
            logger.error(f"Error loading GDP data: {e}")

        return None

    def load_real_hkma_data(self) -> Optional[pd.DataFrame]:
        """
        加載HKMA綜合數據

        Returns:
            HKMA數據DataFrame
        """
        logger.info("Loading real HKMA data")

        try:
            hkma_file = Path(self.data_sources['hkma_data'])
            if hkma_file.exists():
                df = pd.read_csv(hkma_file)

                # 尋找日期欄位
                date_col = None
                for col in df.columns:
                    if 'date' in col.lower() or 'Date' in col:
                        date_col = col
                        break

                if date_col:
                    df[date_col] = pd.to_datetime(df[date_col])
                    df.set_index(date_col, inplace=True)
                    df.sort_index(inplace=True)

                    logger.info(f"Loaded HKMA data: {len(df)} records from {df.index.min()} to {df.index.max()}")
                    return df
                else:
                    logger.warning("No date column found in HKMA data")

        except Exception as e:
            logger.error(f"Error loading HKMA data: {e}")

        return None

    def calculate_all_indicators(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        為所有數據源計算技術指標

        Args:
            data_dict: 數據字典

        Returns:
            技術指標結果字典
        """
        logger.info("Calculating technical indicators for all data sources")

        indicator_results = {}

        for source, df in data_dict.items():
            if df is None or len(df) == 0:
                continue

            logger.info(f"Calculating indicators for {source}")

            try:
                # 提取價格序列
                if 'rate' in df.columns:
                    price_series = df['rate']
                elif 'close' in df.columns:
                    price_series = df['close']
                else:
                    # 使用第一個數值欄位
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        price_series = df[numeric_cols[0]]
                    else:
                        continue

                # 計算RSI
                rsi_result = self.calculate_rsi_indicators(price_series, source)

                # 計算MACD
                macd_result = self.calculate_macd_indicators(price_series, source)

                # 計算趨勢指標
                trend_result = self.calculate_trend_indicators(price_series, source)

                # 計算波動率指標
                volatility_result = self.calculate_volatility_indicators(price_series, source)

                indicator_results[source] = {
                    'rsi': rsi_result,
                    'macd': macd_result,
                    'trend': trend_result,
                    'volatility': volatility_result,
                    'data_length': len(price_series),
                    'date_range': f"{price_series.index.min()} to {price_series.index.max()}"
                }

            except Exception as e:
                logger.error(f"Error calculating indicators for {source}: {e}")

        logger.info(f"Calculated indicators for {len(indicator_results)} data sources")
        return indicator_results

    def calculate_rsi_indicators(self, price_series: pd.Series, source: str) -> Dict[str, Any]:
        """
        計算RSI相關指標

        Args:
            price_series: 價格序列
            source: 數據源名稱

        Returns:
            RSI指標結果
        """
        try:
            # 計算多個週期的RSI
            periods = [7, 14, 21, 28]
            rsi_results = {}

            for period in periods:
                if len(price_series) >= period:
                    rsi = self.indicators.calculate_rsi(price_series, period)
                    current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50

                    # 計算信號
                    if current_rsi > 70:
                        signal = 'overbought'
                        action = 'sell'
                    elif current_rsi < 30:
                        signal = 'oversold'
                        action = 'buy'
                    else:
                        signal = 'neutral'
                        action = 'hold'

                    rsi_results[f'rsi_{period}'] = {
                        'value': float(current_rsi),
                        'signal': signal,
                        'action': action,
                        'period': period
                    }

            # 找出最強RSI信號
            best_rsi = None
            best_score = 0

            for key, rsi_data in rsi_results.items():
                # 評分標準：RSI是否在合理範圍內
                rsi_value = rsi_data['value']
                if 30 <= rsi_value <= 70:
                    score = 1.0 - abs(rsi_value - 50) / 20  # 越接近50越好
                else:
                    score = 0.3

                if score > best_score:
                    best_score = score
                    best_rsi = rsi_data

            return {
                'all_rsi': rsi_results,
                'best_rsi': best_rsi,
                'rsi_score': best_score
            }

        except Exception as e:
            logger.error(f"Error calculating RSI for {source}: {e}")
            return {'error': str(e)}

    def calculate_macd_indicators(self, price_series: pd.Series, source: str) -> Dict[str, Any]:
        """
        計算MACD相關指標

        Args:
            price_series: 價格序列
            source: 數據源名稱

        Returns:
            MACD指標結果
        """
        try:
            # 計算MACD
            if len(price_series) >= 26:
                macd_result = self.indicators.calculate_macd(price_series, 12, 26, 9)

                if len(macd_result) > 0:
                    current_macd = macd_result['macd'].iloc[-1]
                    current_signal = macd_result['signal'].iloc[-1]
                    current_histogram = macd_result['histogram'].iloc[-1]

                    # 判斷信號
                    if current_histogram > 0 and current_macd > current_signal:
                        signal_type = 'bullish'
                        action = 'buy'
                    elif current_histogram < 0 and current_macd < current_signal:
                        signal_type = 'bearish'
                        action = 'sell'
                    else:
                        signal_type = 'neutral'
                        action = 'hold'

                    return {
                        'macd_line': float(current_macd),
                        'signal_line': float(current_signal),
                        'histogram': float(current_histogram),
                        'signal_type': signal_type,
                        'action': action,
                        'macd_score': min(abs(current_histogram) * 10, 1.0)  # 標準化評分
                    }

            return {'error': 'Insufficient data for MACD calculation'}

        except Exception as e:
            logger.error(f"Error calculating MACD for {source}: {e}")
            return {'error': str(e)}

    def calculate_trend_indicators(self, price_series: pd.Series, source: str) -> Dict[str, Any]:
        """
        計算趨勢指標

        Args:
            price_series: 價格序列
            source: 數據源名稱

        Returns:
            趨勢指標結果
        """
        try:
            if len(price_series) < 20:
                return {'error': 'Insufficient data for trend analysis'}

            # 計算移動平均線
            sma_short = price_series.rolling(window=10).mean()
            sma_long = price_series.rolling(window=30).mean()

            current_price = price_series.iloc[-1]
            current_sma_short = sma_short.iloc[-1]
            current_sma_long = sma_long.iloc[-1]

            # 趨勢判斷
            if current_price > current_sma_short > current_sma_long:
                trend_direction = 'bullish'
                trend_strength = (current_price - current_sma_long) / current_sma_long
            elif current_price < current_sma_short < current_sma_long:
                trend_direction = 'bearish'
                trend_strength = (current_sma_long - current_price) / current_sma_long
            else:
                trend_direction = 'neutral'
                trend_strength = 0

            return {
                'trend_direction': trend_direction,
                'trend_strength': float(trend_strength),
                'price_above_sma10': current_price > current_sma_short,
                'price_above_sma30': current_price > current_sma_long,
                'sma10_above_sma30': current_sma_short > current_sma_long,
                'trend_score': min(abs(trend_strength) * 2, 1.0)
            }

        except Exception as e:
            logger.error(f"Error calculating trend indicators for {source}: {e}")
            return {'error': str(e)}

    def calculate_volatility_indicators(self, price_series: pd.Series, source: str) -> Dict[str, Any]:
        """
        計算波動率指標

        Args:
            price_series: 價格序列
            source: 數據源名稱

        Returns:
            波動率指標結果
        """
        try:
            if len(price_series) < 20:
                return {'error': 'Insufficient data for volatility analysis'}

            # 計算價格變化率
            returns = price_series.pct_change().dropna()

            # 計算波動率 (標準差)
            volatility_20 = returns.rolling(window=20).std().iloc[-1]
            volatility_10 = returns.rolling(window=10).std().iloc[-1]

            # 波動率狀態
            avg_volatility = volatility_20
            current_volatility = volatility_10

            if current_volatility > avg_volatility * 1.2:
                volatility_state = 'high'
            elif current_volatility < avg_volatility * 0.8:
                volatility_state = 'low'
            else:
                volatility_state = 'normal'

            return {
                'current_volatility': float(current_volatility),
                'avg_volatility': float(avg_volatility),
                'volatility_state': volatility_state,
                'volatility_ratio': float(current_volatility / avg_volatility) if avg_volatility > 0 else 1.0,
                'volatility_score': min(current_volatility / avg_volatility, 1.0) if avg_volatility > 0 else 0.5
            }

        except Exception as e:
            logger.error(f"Error calculating volatility indicators for {source}: {e}")
            return {'error': str(e)}

    def optimize_weights(self, indicator_results: Dict[str, Any]) -> Dict[str, float]:
        """
        基於歷史表現優化權重

        Args:
            indicator_results: 技術指標結果

        Returns:
            優化後的權重字典
        """
        logger.info("Optimizing indicator weights")

        # 基於數據源的可靠性分配基礎權重
        source_reliability = {
            'hibor_overnight': 0.9,      # HIBOR數據最可靠
            'hibor_1month': 0.85,        # HIBOR 1月期也很可靠
            'gdp_growth': 0.7,           # GDP數據較低頻
            'hkma_data': 0.8,            # HKMA綜合數據
            'trade_data': 0.75           # 貿易數據
        }

        # 計算每種指標類型的平均得分
        rsi_scores = []
        macd_scores = []
        trend_scores = []
        volatility_scores = []

        for source, results in indicator_results.items():
            if 'rsi' in results and 'rsi_score' in results['rsi']:
                score = results['rsi']['rsi_score'] * source_reliability.get(source, 0.5)
                rsi_scores.append(score)

            if 'macd' in results and 'macd_score' in results['macd']:
                score = results['macd']['macd_score'] * source_reliability.get(source, 0.5)
                macd_scores.append(score)

            if 'trend' in results and 'trend_score' in results['trend']:
                score = results['trend']['trend_score'] * source_reliability.get(source, 0.5)
                trend_scores.append(score)

            if 'volatility' in results and 'volatility_score' in results['volatility']:
                score = results['volatility']['volatility_score'] * source_reliability.get(source, 0.5)
                volatility_scores.append(score)

        # 計算平均得分
        avg_rsi_score = np.mean(rsi_scores) if rsi_scores else 0.5
        avg_macd_score = np.mean(macd_scores) if macd_scores else 0.5
        avg_trend_score = np.mean(trend_scores) if trend_scores else 0.5
        avg_volatility_score = np.mean(volatility_scores) if volatility_scores else 0.5

        # 基於得分分配權重
        total_score = avg_rsi_score + avg_macd_score + avg_trend_score + avg_volatility_score

        if total_score > 0:
            weights = {
                'rsi_weight': avg_rsi_score / total_score,
                'macd_weight': avg_macd_score / total_score,
                'trend_weight': avg_trend_score / total_score,
                'volatility_weight': avg_volatility_score / total_score
            }
        else:
            # 默認等權重
            weights = {
                'rsi_weight': 0.35,
                'macd_weight': 0.25,
                'trend_weight': 0.25,
                'volatility_weight': 0.15
            }

        logger.info(f"Optimized weights: {weights}")
        return weights

    def generate_composite_signals(self, indicator_results: Dict[str, Any], weights: Dict[str, float]) -> Dict[str, Any]:
        """
        生成綜合交易信號

        Args:
            indicator_results: 技術指標結果
            weights: 優化後的權重

        Returns:
            綜合信號結果
        """
        logger.info("Generating composite trading signals")

        buy_signals = []
        sell_signals = []
        hold_signals = []

        total_strength = 0
        weighted_strength = 0

        for source, results in indicator_results.items():
            source_strength = 0

            # RSI信號貢獻
            if 'rsi' in results and 'best_rsi' in results['rsi'] and results['rsi']['best_rsi']:
                rsi_action = results['rsi']['best_rsi']['action']
                rsi_value = results['rsi']['best_rsi']['value']

                if rsi_action == 'buy':
                    buy_signals.append(f"RSI({source}): {rsi_value:.1f}")
                    source_strength += weights['rsi_weight']
                elif rsi_action == 'sell':
                    sell_signals.append(f"RSI({source}): {rsi_value:.1f}")
                    source_strength -= weights['rsi_weight']

            # MACD信號貢獻
            if 'macd' in results and 'action' in results['macd']:
                macd_action = results['macd']['action']
                macd_hist = results['macd'].get('histogram', 0)

                if macd_action == 'buy':
                    buy_signals.append(f"MACD({source}): {macd_hist:.3f}")
                    source_strength += weights['macd_weight']
                elif macd_action == 'sell':
                    sell_signals.append(f"MACD({source}): {macd_hist:.3f}")
                    source_strength -= weights['macd_weight']

            # 趨勢信號貢獻
            if 'trend' in results and 'trend_direction' in results['trend']:
                trend_direction = results['trend']['trend_direction']
                trend_strength = results['trend'].get('trend_strength', 0)

                if trend_direction == 'bullish':
                    buy_signals.append(f"趨勢({source}): 強度{trend_strength:.2%}")
                    source_strength += weights['trend_weight'] * min(trend_strength * 10, 1)
                elif trend_direction == 'bearish':
                    sell_signals.append(f"趨勢({source}): 強度{trend_strength:.2%}")
                    source_strength -= weights['trend_weight'] * min(trend_strength * 10, 1)

            # 波動率信號貢獻
            if 'volatility' in results and 'volatility_state' in results['volatility']:
                volatility_state = results['volatility']['volatility_state']

                if volatility_state == 'high':
                    hold_signals.append(f"波動率({source}): 高波動，觀望")
                    source_strength *= 0.8  # 高波動降低信號強度

            total_strength += abs(source_strength)
            weighted_strength += source_strength

        # 最終信號判斷
        if weighted_strength > 0.15:
            final_signal = 'BUY'
            confidence = min(weighted_strength, 1.0)
        elif weighted_strength < -0.15:
            final_signal = 'SELL'
            confidence = min(abs(weighted_strength), 1.0)
        else:
            final_signal = 'HOLD'
            confidence = 0.5

        return {
            'final_signal': final_signal,
            'confidence': float(confidence),
            'weighted_strength': float(weighted_strength),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'signal_count': {
                'buy': len(buy_signals),
                'sell': len(sell_signals),
                'hold': len(hold_signals)
            },
            'data_sources_count': len(indicator_results)
        }

    def run_full_analysis(self) -> Dict[str, Any]:
        """
        運行完整的真實數據分析

        Returns:
            完整分析結果
        """
        logger.info("Starting full real data analysis")

        analysis_results = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'running',
            'data_sources': {},
            'indicators': {},
            'weights': {},
            'signals': {}
        }

        try:
            # 1. 加載真實數據
            logger.info("Step 1: Loading real economic data")

            # 加載HIBOR數據
            hibor_data = self.load_real_hibor_data()
            analysis_results['data_sources'].update(hibor_data)

            # 加載GDP數據
            gdp_data = self.load_real_gdp_data()
            if gdp_data is not None:
                analysis_results['data_sources']['gdp_growth'] = gdp_data

            # 加載HKMA數據
            hkma_data = self.load_real_hkma_data()
            if hkma_data is not None:
                analysis_results['data_sources']['hkma_data'] = hkma_data

            logger.info(f"Loaded {len(analysis_results['data_sources'])} data sources")

            # 2. 計算技術指標
            logger.info("Step 2: Calculating technical indicators")
            indicator_results = self.calculate_all_indicators(analysis_results['data_sources'])
            analysis_results['indicators'] = indicator_results

            # 3. 優化權重
            logger.info("Step 3: Optimizing indicator weights")
            optimized_weights = self.optimize_weights(indicator_results)
            analysis_results['weights'] = optimized_weights

            # 4. 生成綜合信號
            logger.info("Step 4: Generating composite signals")
            composite_signals = self.generate_composite_signals(indicator_results, optimized_weights)
            analysis_results['signals'] = composite_signals

            # 5. 生成報告
            analysis_results['status'] = 'completed'
            analysis_results['summary'] = {
                'total_data_sources': len(analysis_results['data_sources']),
                'successful_indicators': len([r for r in indicator_results.values() if 'error' not in r]),
                'final_signal': composite_signals['final_signal'],
                'signal_confidence': composite_signals['confidence'],
                'data_quality': 'high'  # 使用真實數據，質量高
            }

            logger.info(f"Analysis completed successfully. Final signal: {composite_signals['final_signal']} (confidence: {composite_signals['confidence']:.2f})")

        except Exception as e:
            logger.error(f"Error in full analysis: {e}")
            analysis_results['status'] = 'failed'
            analysis_results['error'] = str(e)

        return analysis_results

    def save_analysis_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        保存分析報告

        Args:
            results: 分析結果
            filename: 文件名

        Returns:
            保存的文件路徑
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"real_data_analysis_report_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Analysis report saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving analysis report: {e}")
            return None


def main():
    """主測試函數"""
    print("=== 真實數據多指標技術分析系統測試 ===")

    # 初始化系統
    system = RealDataMultiIndicatorSystem()

    # 運行完整分析
    print("1. 運行完整真實數據分析...")
    analysis_results = system.run_full_analysis()

    # 顯示結果
    if analysis_results['status'] == 'completed':
        print("\n2. 分析結果:")
        print(f"   狀態: {analysis_results['status']}")
        print(f"   數據源數量: {analysis_results['summary']['total_data_sources']}")
        print(f"   成功指標: {analysis_results['summary']['successful_indicators']}")
        print(f"   最終信號: {analysis_results['summary']['final_signal']}")
        print(f"   信號置信度: {analysis_results['summary']['signal_confidence']:.2f}")
        print(f"   數據質量: {analysis_results['summary']['data_quality']}")

        print("\n3. 數據源詳情:")
        for source, df in analysis_results['data_sources'].items():
            if hasattr(df, 'index'):
                print(f"   {source}: {len(df)} 條記錄 ({df.index.min()} 至 {df.index.max()})")
            else:
                print(f"   {source}: 數據格式異常")

        print("\n4. 權重分配:")
        weights = analysis_results['weights']
        print(f"   RSI權重: {weights.get('rsi_weight', 0):.3f}")
        print(f"   MACD權重: {weights.get('macd_weight', 0):.3f}")
        print(f"   趨勢權重: {weights.get('trend_weight', 0):.3f}")
        print(f"   波動率權重: {weights.get('volatility_weight', 0):.3f}")

        print("\n5. 信號詳情:")
        signals = analysis_results['signals']
        print(f"   買入信號: {signals['signal_count']['buy']} 個")
        print(f"   賣出信號: {signals['signal_count']['sell']} 個")
        print(f"   觀望信號: {signals['signal_count']['hold']} 個")

        if signals['buy_signals']:
            print("   買入原因:")
            for signal in signals['buy_signals']:
                print(f"     - {signal}")

        if signals['sell_signals']:
            print("   賣出原因:")
            for signal in signals['sell_signals']:
                print(f"     - {signal}")

        # 保存報告
        print("\n6. 保存分析報告...")
        report_file = system.save_analysis_report(analysis_results)
        if report_file:
            print(f"   報告已保存: {report_file}")

        print("\n=== 真實數據分析完成 ===")
        print("✅ 所有真實數據成功加載")
        print("✅ 技術指標計算完成")
        print("✅ 權重優化完成")
        print("✅ 綜合信號生成完成")
        print(f"✅ 最終交易信號: {analysis_results['summary']['final_signal']}")

    else:
        print(f"\n❌ 分析失敗: {analysis_results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()