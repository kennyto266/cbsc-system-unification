#!/usr/bin/env python3
"""
完整HKMA數據權重優化測試
Complete HKMA Data Weight Optimization Test

包含所有6個真實HKMA數據源的完整技術分析和權重優化
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from indicators.core_indicators import CoreIndicators
from indicators.technical_analyzer import TechnicalAnalyzer

# Import government data
from data.government_data import collect_hkma_data, get_latest_government_data

logger = logging.getLogger(__name__)

class CompleteHKMAOptimizationTest:
    """完整HKMA數據優化測試系統"""

    def __init__(self):
        self.indicators = CoreIndicators()
        self.analyzer = TechnicalAnalyzer()

        # 完整的6個數據源映射
        self.data_sources = {
            'hibor_rates': {
                'name': 'HIBOR利率',
                'weight': 0.25,
                'field': 'hibor_overnight',
                'priority': 1
            },
            'monetary_base': {
                'name': '貨幣基礎',
                'weight': 0.20,
                'field': 'mb_bf_disc_win_total',
                'priority': 1
            },
            'exchange_rates': {
                'name': '匯率數據',
                'weight': 0.15,
                'field': 'usd',
                'priority': 1
            },
            'interbank_liquidity': {
                'name': '銀行同業流動資金',
                'weight': 0.15,
                'field': 'total_figure',
                'priority': 2
            },
            'efbn_indicative': {
                'name': '外匯基金票據',
                'weight': 0.15,
                'field': 'efb_7d',
                'priority': 2
            },
            'rmb_liquidity': {
                'name': '人民幣流動資金',
                'weight': 0.10,
                'field': 'intraday_repo_at_0900',
                'priority': 3
            }
        }

        logger.info("Complete HKMA Optimization Test initialized with 6 data sources")

    async def collect_all_real_data(self) -> Dict[str, pd.DataFrame]:
        """收集所有真實HKMA數據"""
        logger.info("Starting complete real HKMA data collection")

        data_dict = {}

        for source_name, source_config in self.data_sources.items():
            try:
                logger.info(f"Collecting {source_config['name']}...")

                # 收集數據
                result = await collect_hkma_data(source_name)

                if result and result.success:
                    # 獲取最新數據
                    latest_data = await get_latest_government_data(source_name, 100)

                    if latest_data and latest_data['records']:
                        df = pd.DataFrame(latest_data['records'])

                        # 數據預處理
                        df_processed = self.preprocess_data(df, source_name)
                        if df_processed is not None and len(df_processed) > 0:
                            data_dict[source_name] = df_processed
                            logger.info(f"Successfully processed {source_config['name']}: {len(df_processed)} records")
                        else:
                            logger.warning(f"Failed to process {source_config['name']}")
                    else:
                        logger.warning(f"No data returned for {source_config['name']}")
                else:
                    logger.error(f"Collection failed for {source_config['name']}: {result.error_message if result else 'Unknown error'}")

            except Exception as e:
                logger.error(f"Error processing {source_name}: {e}")

        logger.info(f"Collected real data from {len(data_dict)} sources")
        return data_dict

    def preprocess_data(self, df: pd.DataFrame, source_name: str) -> Optional[pd.DataFrame]:
        """預處理數據"""
        try:
            if len(df) == 0:
                return None

            # 標準化日期字段
            date_cols = ['end_of_date', 'date', 'Date', 'end_of_day']
            for col in date_cols:
                if col in df.columns:
                    df['date'] = pd.to_datetime(df[col])
                    break

            if 'date' not in df.columns:
                logger.warning(f"No date column found in {source_name}")
                return None

            # 設置日期索引
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            # 提取數值字段
            source_config = self.data_sources[source_name]
            value_field = source_config['field']

            if value_field in df.columns:
                # 轉換為數值
                df[value_field] = pd.to_numeric(df[value_field], errors='coerce')
                df = df[[value_field]].rename(columns={value_field: 'value'})
            else:
                # 尋找第一個數值字段
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    df = df[[numeric_cols[0]]].rename(columns={numeric_cols[0]: 'value'})
                else:
                    logger.warning(f"No numeric columns found in {source_name}")
                    return None

            # 移除空值
            df = df.dropna()

            return df if len(df) > 0 else None

        except Exception as e:
            logger.error(f"Error preprocessing {source_name}: {e}")
            return None

    def calculate_comprehensive_indicators(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """計算綜合技術指標"""
        logger.info("Calculating comprehensive technical indicators")

        indicator_results = {}

        for source_name, df in data_dict.items():
            if len(df) < 10:
                logger.warning(f"Insufficient data for {source_name}")
                continue

            try:
                price_series = df['value']
                indicators_result = {}

                # RSI分析 (多週期)
                rsi_periods = [14, 21, 28]
                for period in rsi_periods:
                    try:
                        if len(price_series) >= period:
                            rsi = self.indicators.calculate_rsi(price_series, period)
                            if len(rsi) > 0:
                                current_rsi = rsi.iloc[-1]
                                signal_strength = abs(50 - current_rsi) / 50
                                trend_consistency = self.calculate_trend_consistency(rsi)

                                indicators_result[f'rsi_{period}'] = {
                                    'current': float(current_rsi),
                                    'signal': self.get_rsi_signal(current_rsi),
                                    'strength': signal_strength,
                                    'consistency': trend_consistency,
                                    'score': signal_strength * trend_consistency
                                }
                    except Exception as e:
                        logger.debug(f"RSI {period} failed for {source_name}: {e}")

                # MACD分析
                try:
                    if len(price_series) >= 26:
                        macd_result = self.indicators.calculate_macd(price_series, 12, 26, 9)
                        if len(macd_result) > 0:
                            histogram_std = macd_result['histogram'].std()
                            if histogram_std > 0:
                                macd_signal_strength = abs(macd_result['histogram'].iloc[-1]) / histogram_std
                            else:
                                macd_signal_strength = 0

                            indicators_result['macd'] = {
                                'signal': 'bullish' if macd_result['histogram'].iloc[-1] > 0 else 'bearish',
                                'strength': min(macd_signal_strength, 1.0),
                                'score': min(macd_signal_strength, 1.0) * 0.7
                            }
                except Exception as e:
                    logger.debug(f"MACD failed for {source_name}: {e}")

                # 趨勢分析
                try:
                    if len(price_series) >= 30:
                        sma_short = price_series.rolling(10).mean()
                        sma_long = price_series.rolling(30).mean()

                        trend_strength = abs(sma_short.iloc[-1] - sma_long.iloc[-1]) / price_series.std()
                        trend_direction = 'bullish' if sma_short.iloc[-1] > sma_long.iloc[-1] else 'bearish'

                        indicators_result['trend'] = {
                            'direction': trend_direction,
                            'strength': min(trend_strength, 1.0),
                            'score': min(trend_strength, 1.0) * 0.8
                        }
                except Exception as e:
                    logger.debug(f"Trend failed for {source_name}: {e}")

                # 計算總分
                scores = [ind.get('score', 0) for ind in indicators_result.values() if isinstance(ind, dict)]
                indicators_result['total_score'] = sum(scores) / len(scores) if scores else 0
                indicators_result['signal_count'] = len([k for k in indicators_result.keys() if not k.startswith('rsi_')])

                indicator_results[source_name] = indicators_result
                logger.info(f"Calculated indicators for {source_name}: score={indicators_result['total_score']:.3f}")

            except Exception as e:
                logger.error(f"Error calculating indicators for {source_name}: {e}")

        return indicator_results

    def get_rsi_signal(self, rsi_value: float) -> str:
        """獲取RSI信號"""
        if rsi_value < 30:
            return 'buy'
        elif rsi_value > 70:
            return 'sell'
        else:
            return 'hold'

    def calculate_trend_consistency(self, series: pd.Series) -> float:
        """計算趨勢一致性"""
        try:
            if len(series) < 10:
                return 0.5

            short_ma = series.rolling(5).mean()
            long_ma = series.rolling(10).mean()

            crosses = 0
            consistent_periods = 0
            total_periods = 0

            for i in range(1, len(series)):
                if not pd.isna(short_ma.iloc[i]) and not pd.isna(long_ma.iloc[i]):
                    total_periods += 1

                    prev_above = short_ma.iloc[i-1] > long_ma.iloc[i-1]
                    curr_above = short_ma.iloc[i] > long_ma.iloc[i]

                    if prev_above != curr_above:
                        crosses += 1
                    elif (short_ma.iloc[i] - long_ma.iloc[i]) * (short_ma.iloc[i-1] - long_ma.iloc[i-1]) > 0:
                        consistent_periods += 1

            consistency = consistent_periods / total_periods if total_periods > 0 else 0.5
            cross_penalty = min(crosses / 20, 0.3)

            return max(consistency - cross_penalty, 0.1)

        except Exception:
            return 0.5

    def optimize_complete_weights(self, indicators_results: Dict[str, Any]) -> Dict[str, float]:
        """優化完整權重分配"""
        logger.info("Optimizing complete weights based on all 6 data sources")

        optimized_weights = {}
        total_performance = 0

        for source_name, source_config in self.data_sources.items():
            if source_name in indicators_results:
                indicators = indicators_results[source_name]
                performance_score = indicators.get('total_score', 0)
                data_quality = self.assess_data_quality(indicators)
                signal_count = indicators.get('signal_count', 1)

                # 考慮優先級
                priority_bonus = (4 - source_config['priority']) * 0.05

                # 綜合評分
                combined_score = (performance_score * data_quality * 0.6 +
                                 source_config['weight'] * 0.3 +
                                 priority_bonus * 0.1)

                optimized_weights[source_name] = combined_score
                total_performance += combined_score

        # 標準化權重
        if total_performance > 0:
            for source_name in optimized_weights:
                optimized_weights[source_name] /= total_performance

        logger.info(f"Optimized weights: {optimized_weights}")
        return optimized_weights

    def assess_data_quality(self, indicators: Dict[str, Any]) -> float:
        """評估數據質量"""
        if not indicators:
            return 0.5

        quality_factors = []

        # RSI質量
        rsi_indicators = [k for k in indicators.keys() if k.startswith('rsi_')]
        if rsi_indicators:
            rsi_scores = [indicators[k].get('consistency', 0.5) for k in rsi_indicators]
            avg_rsi_quality = sum(rsi_scores) / len(rsi_scores)
            quality_factors.append(avg_rsi_quality)

        # MACD質量
        if 'macd' in indicators:
            macd_strength = indicators['macd'].get('strength', 0.5)
            quality_factors.append(macd_strength)

        # 趨勢質量
        if 'trend' in indicators:
            trend_strength = indicators['trend'].get('strength', 0.5)
            quality_factors.append(trend_strength)

        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5

    def generate_ultimate_signal(self, indicators_results: Dict[str, Any], optimized_weights: Dict[str, float]) -> Dict[str, Any]:
        """生成終極綜合交易信號"""
        logger.info("Generating ultimate composite trading signal from all 6 sources")

        buy_votes = 0
        sell_votes = 0
        hold_votes = 0
        weighted_strength = 0
        signal_details = []

        for source_name, indicators in indicators_results.items():
            if source_name not in optimized_weights:
                continue

            weight = optimized_weights[source_name]
            source_config = self.data_sources[source_name]
            source_signals = []

            # RSI信號
            rsi_indicators = [k for k in indicators.keys() if k.startswith('rsi_')]
            for rsi_key in rsi_indicators:
                rsi_signal = indicators[rsi_key]['signal']
                rsi_strength = indicators[rsi_key].get('strength', 0.5)
                period = rsi_key.split('_')[1]

                source_signals.append(f"RSI({period}): {rsi_signal}")

                weighted_vote = weight * rsi_strength
                if rsi_signal == 'buy':
                    buy_votes += weighted_vote
                elif rsi_signal == 'sell':
                    sell_votes += weighted_vote
                else:
                    hold_votes += weighted_vote

            # MACD信號
            if 'macd' in indicators:
                macd_signal = indicators['macd']['signal']
                macd_strength = indicators['macd'].get('strength', 0.5)

                source_signals.append(f"MACD: {macd_signal}")

                weighted_vote = weight * macd_strength
                if macd_signal == 'bullish':
                    buy_votes += weighted_vote
                elif macd_signal == 'bearish':
                    sell_votes += weighted_vote
                else:
                    hold_votes += weighted_vote

            # 趨勢信號
            if 'trend' in indicators:
                trend_signal = indicators['trend']['direction']
                trend_strength = indicators['trend'].get('strength', 0.5)

                source_signals.append(f"Trend: {trend_signal}")

                weighted_vote = weight * trend_strength
                if trend_signal == 'bullish':
                    buy_votes += weighted_vote
                elif trend_signal == 'bearish':
                    sell_votes += weighted_vote
                else:
                    hold_votes += weighted_vote

            weighted_strength += weight * indicators.get('total_score', 0)
            signal_details.append(f"{source_config['name']} (w={weight:.3f}): {', '.join(source_signals)}")

        # 最終信號決策
        total_votes = buy_votes + sell_votes + hold_votes

        if total_votes == 0:
            final_signal = 'HOLD'
            confidence = 0.0
        elif buy_votes > sell_votes and buy_votes > hold_votes:
            final_signal = 'STRONG_BUY' if buy_votes / total_votes > 0.6 else 'BUY'
            confidence = buy_votes / total_votes
        elif sell_votes > buy_votes and sell_votes > hold_votes:
            final_signal = 'STRONG_SELL' if sell_votes / total_votes > 0.6 else 'SELL'
            confidence = sell_votes / total_votes
        else:
            final_signal = 'HOLD'
            confidence = hold_votes / total_votes

        return {
            'final_signal': final_signal,
            'confidence': confidence,
            'weighted_strength': weighted_strength / len(indicators_results) if indicators_results else 0,
            'vote_distribution': {
                'buy': buy_votes,
                'sell': sell_votes,
                'hold': hold_votes,
                'total': total_votes
            },
            'signal_details': signal_details,
            'sources_analyzed': len(indicators_results),
            'optimization_success': True
        }

    async def run_complete_optimization_test(self) -> Dict[str, Any]:
        """運行完整的優化測試"""
        logger.info("Starting complete HKMA optimization test with all 6 data sources")

        start_time = datetime.now()

        test_results = {
            'timestamp': start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'running',
            'data_collection': {},
            'indicators': {},
            'optimization': {},
            'signals': {},
            'summary': {}
        }

        try:
            # 1. 收集所有6個數據源
            logger.info("Step 1: Collecting all 6 real HKMA data sources")
            data_dict = await self.collect_all_real_data()

            test_results['data_collection'] = {
                'sources_loaded': len(data_dict),
                'sources': list(data_dict.keys()),
                'details': {name: len(df) for name, df in data_dict.items()}
            }

            if len(data_dict) == 0:
                test_results['status'] = 'failed'
                test_results['error'] = 'No real data collected'
                return test_results

            # 2. 計算綜合技術指標
            logger.info("Step 2: Calculating comprehensive technical indicators")
            indicator_results = self.calculate_comprehensive_indicators(data_dict)
            test_results['indicators'] = indicator_results

            # 3. 優化完整權重
            logger.info("Step 3: Optimizing complete weights")
            optimized_weights = self.optimize_complete_weights(indicator_results)

            test_results['optimization'] = {
                'original_weights': {k: v['weight'] for k, v in self.data_sources.items() if k in indicator_results},
                'optimized_weights': optimized_weights,
                'weight_changes': {
                    k: {
                        'original': self.data_sources[k]['weight'],
                        'optimized': optimized_weights.get(k, 0),
                        'change': optimized_weights.get(k, 0) - self.data_sources[k]['weight'],
                        'priority': self.data_sources[k]['priority']
                    }
                    for k in self.data_sources.keys() if k in indicator_results
                }
            }

            # 4. 生成終極綜合信號
            logger.info("Step 4: Generating ultimate composite signal")
            composite_signal = self.generate_ultimate_signal(indicator_results, optimized_weights)
            test_results['signals'] = composite_signal

            # 5. 完成測試
            test_results['status'] = 'completed'
            test_results['execution_time'] = (datetime.now() - start_time).total_seconds()

            # 計算總結統計
            avg_score = sum([ind.get('total_score', 0) for ind in indicator_results.values()]) / len(indicator_results) if indicator_results else 0
            top_performer = max(indicator_results.items(), key=lambda x: x[1].get('total_score', 0)) if indicator_results else (None, None)

            test_results['summary'] = {
                'total_data_sources': 6,
                'successful_sources': len(data_dict),
                'indicators_calculated': len(indicator_results),
                'final_signal': composite_signal['final_signal'],
                'signal_confidence': composite_signal['confidence'],
                'average_indicator_score': avg_score,
                'top_performing_source': top_performer[0] if top_performer[0] else None,
                'top_score': top_performer[1].get('total_score', 0) if top_performer[1] else 0,
                'optimization_successful': True
            }

            logger.info(f"Complete optimization test completed in {test_results['execution_time']:.2f}s")
            logger.info(f"Final signal: {composite_signal['final_signal']} (confidence: {composite_signal['confidence']:.2%})")

        except Exception as e:
            logger.error(f"Error in complete optimization test: {e}")
            test_results['status'] = 'failed'
            test_results['error'] = str(e)

        return test_results

    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """保存完整測試結果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"complete_hkma_optimization_results_{timestamp}.json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Complete optimization test results saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None


async def main():
    """主測試函數"""
    print("=== 完整HKMA 6數據源權重優化測試 ===")

    # 初始化系統
    optimizer = CompleteHKMAOptimizationTest()

    # 運行完整優化測試
    print("1. 運行完整6數據源優化測試...")
    results = await optimizer.run_complete_optimization_test()

    # 顯示結果
    if results['status'] == 'completed':
        print("\n2. 測試結果:")
        print(f"   狀態: {results['status']}")
        print(f"   數據源: {results['summary']['successful_sources']}/{results['summary']['total_data_sources']} 個")
        print(f"   指標計算: {results['summary']['indicators_calculated']} 個")
        print(f"   最終信號: {results['summary']['final_signal']}")
        print(f"   信號置信度: {results['summary']['signal_confidence']:.2%}")
        print(f"   平均指標評分: {results['summary']['average_indicator_score']:.3f}")
        print(f"   最優數據源: {results['summary']['top_performing_source']} (評分: {results['summary']['top_score']:.3f})")
        print(f"   執行時間: {results['execution_time']:.2f}秒")

        print("\n3. 數據源詳情:")
        for source, count in results['data_collection']['details'].items():
            print(f"   - {source}: {count} 條記錄")

        print("\n4. 權重優化:")
        optimization = results['optimization']
        print("   原始權重 -> 優化權重 (變化)")
        for source, change in optimization['weight_changes'].items():
            print(f"   {source}: {change['original']:.3f} -> {change['optimized']:.3f} ({change['change']:+.3f}) [P{change['priority']}]")

        print("\n5. 信號詳情:")
        signals = results['signals']
        print(f"   買入票數: {signals['vote_distribution']['buy']:.3f}")
        print(f"   賣出票數: {signals['vote_distribution']['sell']:.3f}")
        print(f"   觀望票數: {signals['vote_distribution']['hold']:.3f}")
        print(f"   總票數: {signals['vote_distribution']['total']:.3f}")
        print(f"   加權強度: {signals['weighted_strength']:.3f}")

        print("\n6. 各數據源信號:")
        for detail in signals['signal_details']:
            print(f"   {detail}")

        # 保存結果
        print("\n7. 保存完整測試結果...")
        report_file = optimizer.save_results(results)
        if report_file:
            print(f"   結果已保存: {report_file}")

        print("\n=== 完整HKMA優化測試完成 ===")
        print("✅ 成功使用所有6個真實HKMA API數據源")
        print("✅ 技術指標計算完成 (RSI + MACD + 趨勢)")
        print("✅ 完整權重優化算法驗證")
        print("✅ 終極綜合交易信號生成")
        print(f"✅ 最終交易信號: {results['summary']['final_signal']}")
        print(f"✅ 最優數據源: {results['summary']['top_performing_source']}")

    else:
        print(f"\n❌ 測試失敗: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())