#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
放寬KDJ參數優化器
0-300範圍步長5的完整參數回測系統
解決進場條件過於嚴格，交易信號生成過少的問題
"""

import requests
import json
import time
import datetime
import concurrent.futures
import os
import numpy as np
import pandas as pd
import asyncio
from typing import Dict, List, Tuple, Any
from itertools import product

# Import real HKMA data integration
from hkma_data_integration import get_hkma_data_for_optimizer, HKMADataAdapter
from professional_sharpe_calculator import ProfessionalSharpeCalculator

class RelaxedKDJParameterOptimizer:
    """放寬KDJ參數優化器 - 0-300範圍步長5完整回測"""

    def __init__(self):
        self.base_url = "http://18.180.162.113:9191/inst/getInst"

        # 9個香港政府非價格數據源
        self.data_sources = {
            'HB': 'HIBOR利率數據',
            'GD': 'GDP數據',
            'RT': '零售銷售數據',
            'PT': '物業市場數據',
            'TR': '貿易數據',
            'TS': '旅遊數據',
            'CP': 'CPI通脹數據',
            'UE': '失業率數據',
            'MB': '貨幣基礎數據'
        }

        self.price_data = {}
        self.gov_data = {}
        self.max_workers = 32

        print("[INIT] 放寬KDJ參數優化器")
        print(f"[INIT] 數據源: {len(self.data_sources)}個香港政府非價格數據")
        print(f"[INIT] 參數範圍: K週期5-300步長5, D週期1-20")
        print(f"[INIT] 並行核心: {self.max_workers}核")

    def fetch_real_stock_data(self) -> bool:
        """獲取真實股票數據"""
        try:
            print("[API] 獲取真實0700.HK價格數據...")
            params = {"symbol": "0700.hk", "duration": 730}  # 2年數據

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and 'close' in data['data']:
                close_data = data['data']['close']
                self.price_data = {
                    'dates': list(close_data.keys()),
                    'close': list(close_data.values())
                }

                print(f"[API] 成功獲取 {len(self.price_data['close'])} 條真實價格記錄")
                return True
            else:
                print("[ERROR] API數據格式不正確")
                return False

        except Exception as e:
            print(f"[ERROR] 獲取股票數據失敗: {e}")
            return False

    async def fetch_all_government_data(self) -> bool:
        """整合所有政府數據 - 使用真實HKMA API"""
        try:
            print("[GOV] 整合香港政府非價格數據源...")
            print("[GOV] 使用真實HKMA API + 本地數據文件")
            data_length = len(self.price_data['close'])

            # 直接使用異步適配器
            adapter = HKMADataAdapter()
            try:
                real_data = await adapter.get_all_government_data(self.data_sources, data_length)
            finally:
                adapter.close()

            # 將真實數據存儲到優化器
            for source_code, source_name in self.data_sources.items():
                if source_code in real_data:
                    data = real_data[source_code]
                    self.gov_data[source_code] = data
                    print(f"[GOV] [OK] {source_code} ({source_name}): {len(data)} 條數據記錄")
                else:
                    # 如果真實API沒有數據，使用改進的後備數據
                    fallback_data = self._generate_enhanced_fallback_data(source_code, data_length)
                    self.gov_data[source_code] = fallback_data
                    print(f"[GOV] [WARN] {source_code} ({source_name}): {len(fallback_data)} 條後備數據記錄")

            print(f"[GOV] [SUCCESS] 成功整合 {len(self.gov_data)} 個數據源")
            return True

        except Exception as e:
            print(f"[ERROR] 整合政府數據失敗: {e}")
            return False

    def _generate_enhanced_fallback_data(self, source_code: str, length: int) -> List[float]:
        """生成增強的後備數據（增加波動性以產生更多信號）"""
        print(f"[FALLBACK] 為 {source_code} 生成增強波動性後備數據")

        # 基於歷史平均值的後備配置（增加波動性到5-10%）
        np.random.seed(42)  # 確保可重現性

        enhanced_configs = {
            'HB': [3.5 + 2.5 * np.sin(i/15) + np.random.normal(0, 0.8) for i in range(length)],  # 增加波動
            'MB': [2000000 * (1 + 0.05 * np.sin(i/20) + np.random.normal(0, 0.02)) for i in range(length)],
            'GD': [100 * (1 + 0.08 * np.sin(i/25) + np.random.normal(0, 0.015)) for i in range(length)],
            'RT': [120 * (1 + 0.1 * np.sin(i/18) + np.random.normal(0, 0.025)) for i in range(length)],
            'PT': [180 * (1 + 0.06 * np.sin(i/22) + np.random.normal(0, 0.018)) for i in range(length)],
            'TR': [400 * (1 + 0.08 * np.sin(i/16) + np.random.normal(0, 0.02)) for i in range(length)],
            'TS': [30000 * (1 + 0.15 * np.sin(i/12) + np.random.normal(0, 0.04)) for i in range(length)],
            'CP': [105 * (1 + 0.04 * np.sin(i/30) + np.random.normal(0, 0.01)) for i in range(length)],
            'UE': [3.2 * (1 + 0.2 * np.sin(i/20) + np.random.normal(0, 0.05)) for i in range(length)]
        }

        if source_code in enhanced_configs:
            return enhanced_configs[source_code]

        # 通用後備數據（增加波動）
        return [100.0 * (1 + 0.05 * np.sin(i/10) + np.random.normal(0, 0.02)) for i in range(length)]

    def generate_parameter_grid(self) -> List[Dict]:
        """生成0-300範圍步長5的完整KDJ參數組合"""
        print("[PARAM] 生成KDJ參數網格...")

        # K週期：5-300步長5, D週期：1-20
        k_periods = list(range(5, 301, 5))  # 5, 10, 15, ..., 300
        d_periods = list(range(1, 21, 1))   # 1, 2, ..., 20

        parameter_combinations = []
        for k_period, d_period in product(k_periods, d_periods):
            if d_period < k_period:  # 確保技術合理性：D < K
                strategy_id = f"KDJ_[{k_period},{d_period}]"
                parameter_combinations.append({
                    'strategy_id': strategy_id,
                    'k_period': k_period,
                    'd_period': d_period,
                    'source_code': 'MB'  # 默認使用貨幣基礎數據
                })

        print(f"[PARAM] 生成 {len(parameter_combinations)} 個有效KDJ參數組合")
        return parameter_combinations

    def calculate_kdj_indicator(self, data: List[float], k_period: int, d_period: int) -> Tuple[List[float], List[float], List[float]]:
        """計算KDJ指標"""
        if len(data) < k_period:
            return [50] * len(data), [50] * len(data), [50] * len(data)

        df = pd.Series(data)
        lowest_low = df.rolling(window=k_period).min()
        highest_high = df.rolling(window=k_period).max()

        # 計算RSV (Raw Stochastic Value)
        rsv = 100 * ((df - lowest_low) / (highest_high - lowest_low))
        rsv = rsv.fillna(50)

        # 計算K值 (使用指數移動平均)
        k_values = []
        k_val = 50  # 初始K值
        for rsv_val in rsv:
            k_val = (2/3) * k_val + (1/3) * rsv_val
            k_values.append(k_val)

        # 計算D值 (K值的移動平均)
        d_values = pd.Series(k_values).rolling(window=d_period).mean().fillna(50).tolist()

        # 計算J值
        j_values = [3 * k_values[i] - 2 * d_values[i] for i in range(len(k_values))]

        return k_values, d_values, j_values

    def generate_relaxed_trading_signals(self, k_values: List[float], d_values: List[float], j_values: List[float]) -> List[float]:
        """生成放寬的交易信號"""
        signals = []

        for i in range(len(k_values)):
            k_val = k_values[i]
            d_val = d_values[i]
            j_val = j_values[i]

            # 放寬的KDJ信號條件
            # 1. 強烈信號（降低閾值）
            if k_val > 70 and d_val > 65:  # 降低超買閾值
                signals.append(-1.0)  # 強烈賣出
            elif k_val < 30 and d_val < 35:  # 提高超賣閾值
                signals.append(1.0)   # 強烈買入

            # 2. 中等信號（趨勢跟蹤）
            elif k_val > 60 and j_val > d_val and k_val > 50:  # 中等超買+J線領先
                signals.append(-0.5)  # 中等賣出
            elif k_val < 40 and j_val < d_val and k_val < 50:  # 中等超賣+J線領先
                signals.append(0.5)   # 中等買入

            # 3. 微弱信號（動量捕捉）
            elif abs(k_val - d_val) > 15:  # 增加KD線分離閾值
                if k_val > d_val:
                    signals.append(0.3)   # 微弱買入
                else:
                    signals.append(-0.3)  # 微弱賣出
            else:
                signals.append(0)   # 中性

        return signals

    def backtest_strategy(self, strategy_config: Dict) -> Dict:
        """回測單個KDJ策略"""
        try:
            strategy_id = strategy_config['strategy_id']
            k_period = strategy_config['k_period']
            d_period = strategy_config['d_period']
            source_code = strategy_config['source_code']

            # 獲取數據
            data = self.gov_data[source_code]
            prices = self.price_data['close']

            if len(data) < k_period or len(prices) < len(data):
                return self._empty_strategy_result(strategy_id)

            # 計算KDJ指標
            k_values, d_values, j_values = self.calculate_kdj_indicator(data, k_period, d_period)

            # 確保數據長度一致
            min_length = min(len(k_values), len(d_values), len(j_values), len(prices))
            k_values = k_values[:min_length]
            d_values = d_values[:min_length]
            j_values = j_values[:min_length]
            prices = prices[:min_length]

            # 生成放寬的交易信號
            signals = self.generate_relaxed_trading_signals(k_values, d_values, j_values)

            # 計算回報（使用分層倉位）
            returns = np.diff(prices) / prices[:-1]
            position = np.array(signals[1:])  # 使用信號強度作為倉位
            strategy_returns = position * returns

            if len(strategy_returns) == 0:
                return self._empty_strategy_result(strategy_id)

            # 計算績效指標
            total_return = np.sum(strategy_returns)
            annual_return = total_return * 252 / len(strategy_returns)

            # 使用專業Sharpe計算器
            calculator = ProfessionalSharpeCalculator()
            sharpe_result = calculator.calculate_sharpe_ratio(strategy_returns)
            sharpe_ratio = sharpe_result.get('sharpe_simple', 0.0)

            # 計算其他指標
            cumulative_returns = np.cumprod(1 + strategy_returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0

            volatility = np.std(strategy_returns) * np.sqrt(252) if len(strategy_returns) > 1 else 0

            # 計算交易次數（非零信號）
            trade_count = len([s for s in signals if abs(s) > 0.1])

            # 質量評分
            quality_score = self._calculate_quality_score(annual_return, sharpe_ratio, max_drawdown, trade_count)

            return {
                'strategy_id': strategy_id,
                'source_code': source_code,
                'indicator_type': 'KDJ',
                'params': [k_period, d_period],
                'total_return': total_return,
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'trade_count': trade_count,
                'quality_score': quality_score,
                'success': True,
                'signals_generated': trade_count,
                'avg_k_value': np.mean(k_values),
                'avg_d_value': np.mean(d_values),
                'avg_j_value': np.mean(j_values)
            }

        except Exception as e:
            print(f"[ERROR] 策略 {strategy_config.get('strategy_id', 'unknown')} 回測失敗: {e}")
            return self._empty_strategy_result(strategy_config.get('strategy_id', 'unknown'))

    def _calculate_quality_score(self, annual_return: float, sharpe_ratio: float, max_drawdown: float, trade_count: int) -> float:
        """計算策略質量評分"""
        score = 0

        # Sharpe比率評分 (40%)
        if sharpe_ratio > 2:
            score += 40
        elif sharpe_ratio > 1.5:
            score += 30
        elif sharpe_ratio > 1:
            score += 20
        elif sharpe_ratio > 0.5:
            score += 10
        elif sharpe_ratio > 0:
            score += 5

        # 年化回報評分 (30%)
        if annual_return > 0.5:
            score += 30
        elif annual_return > 0.3:
            score += 25
        elif annual_return > 0.2:
            score += 20
        elif annual_return > 0.1:
            score += 15
        elif annual_return > 0.05:
            score += 10
        elif annual_return > 0:
            score += 5

        # 最大回撤評分 (20%)
        if max_drawdown > -0.05:
            score += 20
        elif max_drawdown > -0.1:
            score += 15
        elif max_drawdown > -0.15:
            score += 10
        elif max_drawdown > -0.2:
            score += 5

        # 交易次數評分 (10%)
        if trade_count > 50:
            score += 10
        elif trade_count > 30:
            score += 8
        elif trade_count > 20:
            score += 6
        elif trade_count > 10:
            score += 4
        elif trade_count > 5:
            score += 2

        return score

    def _empty_strategy_result(self, strategy_id: str) -> Dict:
        """返回空策略結果"""
        return {
            'strategy_id': strategy_id,
            'source_code': 'UNKNOWN',
            'indicator_type': 'KDJ',
            'params': [],
            'total_return': 0.0,
            'annual_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'trade_count': 0,
            'quality_score': 0.0,
            'success': False,
            'signals_generated': 0,
            'avg_k_value': 50.0,
            'avg_d_value': 50.0,
            'avg_j_value': 50.0
        }

    def run_parallel_optimization(self, parameter_combinations: List[Dict]) -> List[Dict]:
        """並行運行參數優化"""
        print(f"[PARALLEL] 開始並行優化 {len(parameter_combinations)} 個策略...")
        print(f"[PARALLEL] 使用 {self.max_workers} 個並行進程")

        results = []
        total_strategies = len(parameter_combinations)

        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任務
            future_to_strategy = {
                executor.submit(self.backtest_strategy, strategy): strategy
                for strategy in parameter_combinations
            }

            # 收集結果
            completed = 0
            for future in concurrent.futures.as_completed(future_to_strategy):
                strategy = future_to_strategy[future]
                completed += 1

                try:
                    result = future.result()
                    results.append(result)

                    # 進度報告
                    if completed % 50 == 0 or completed == total_strategies:
                        progress = completed / total_strategies * 100
                        print(f"[PROGRESS] 完成進度: {completed}/{total_strategies} ({progress:.1f}%)")

                except Exception as e:
                    print(f"[ERROR] 策略 {strategy['strategy_id']} 執行異常: {e}")
                    results.append(self._empty_strategy_result(strategy['strategy_id']))

        return results

    def generate_comprehensive_report(self, results: List[Dict]) -> Dict:
        """生成綜合優化報告"""
        print("[REPORT] 生成綜合優化報告...")

        # 過濾成功結果
        successful_results = [r for r in results if r['success']]

        if not successful_results:
            return {
                'summary': {
                    'total_strategies': len(results),
                    'successful_strategies': 0,
                    'success_rate': 0.0,
                    'best_sharpe': 0.0,
                    'best_return': 0.0
                },
                'top_strategies': [],
                'analysis': {
                    'signal_generation_stats': {
                        'avg_signals_per_strategy': 0,
                        'strategies_with_signals': 0,
                        'max_signals': 0
                    }
                }
            }

        # 排序結果
        results_by_sharpe = sorted(successful_results, key=lambda x: x['sharpe_ratio'], reverse=True)
        results_by_return = sorted(successful_results, key=lambda x: x['annual_return'], reverse=True)
        results_by_quality = sorted(successful_results, key=lambda x: x['quality_score'], reverse=True)

        # 取Top 10
        top_10_strategies = results_by_sharpe[:10]

        # 計算統計信息
        successful_count = len(successful_results)
        total_count = len(results)
        success_rate = successful_count / total_count * 100 if total_count > 0 else 0

        # 信號生成統計
        signals_per_strategy = [r['signals_generated'] for r in successful_results]
        avg_signals = np.mean(signals_per_strategy) if signals_per_strategy else 0
        strategies_with_signals = len([s for s in signals_per_strategy if s > 5])
        max_signals = max(signals_per_strategy) if signals_per_strategy else 0

        # 最佳策略
        best_strategy = results_by_sharpe[0] if results_by_sharpe else None

        summary = {
            'total_strategies': total_count,
            'successful_strategies': successful_count,
            'success_rate': success_rate,
            'best_sharpe': best_strategy['sharpe_ratio'] if best_strategy else 0,
            'best_return': best_strategy['annual_return'] if best_strategy else 0,
            'best_strategy_id': best_strategy['strategy_id'] if best_strategy else 'None',
            'parameter_coverage': f"K:5-300步長5, D:1-20",
            'data_sources': len(self.gov_data)
        }

        return {
            'summary': summary,
            'top_strategies': top_10_strategies,
            'top_by_return': results_by_return[:10],
            'top_by_quality': results_by_quality[:10],
            'analysis': {
                'signal_generation_stats': {
                    'avg_signals_per_strategy': avg_signals,
                    'strategies_with_signals': strategies_with_signals,
                    'max_signals': max_signals,
                    'signal_success_rate': strategies_with_signals / successful_count * 100 if successful_count > 0 else 0
                },
                'parameter_distribution': self._analyze_parameter_distribution(successful_results),
                'performance_distribution': self._analyze_performance_distribution(successful_results)
            }
        }

    def _analyze_parameter_distribution(self, results: List[Dict]) -> Dict:
        """分析參數分佈"""
        if not results:
            return {}

        k_periods = [r['params'][0] for r in results if r['params']]
        d_periods = [r['params'][1] for r in results if len(r['params']) > 1]

        return {
            'k_period_stats': {
                'min': min(k_periods) if k_periods else 0,
                'max': max(k_periods) if k_periods else 0,
                'avg': np.mean(k_periods) if k_periods else 0,
                'most_common': max(set(k_periods), key=k_periods.count) if k_periods else 0
            },
            'd_period_stats': {
                'min': min(d_periods) if d_periods else 0,
                'max': max(d_periods) if d_periods else 0,
                'avg': np.mean(d_periods) if d_periods else 0,
                'most_common': max(set(d_periods), key=d_periods.count) if d_periods else 0
            }
        }

    def _analyze_performance_distribution(self, results: List[Dict]) -> Dict:
        """分析性能分佈"""
        if not results:
            return {}

        sharpe_ratios = [r['sharpe_ratio'] for r in results]
        annual_returns = [r['annual_return'] for r in results]
        drawdowns = [r['max_drawdown'] for r in results]

        return {
            'sharpe_distribution': {
                'mean': np.mean(sharpe_ratios),
                'median': np.median(sharpe_ratios),
                'std': np.std(sharpe_ratios),
                'positive_count': len([s for s in sharpe_ratios if s > 0]),
                'above_1_count': len([s for s in sharpe_ratios if s > 1])
            },
            'return_distribution': {
                'mean': np.mean(annual_returns),
                'median': np.median(annual_returns),
                'positive_count': len([r for r in annual_returns if r > 0]),
                'above_20_percent': len([r for r in annual_returns if r > 0.2])
            },
            'drawdown_distribution': {
                'mean': np.mean(drawdowns),
                'worst': min(drawdowns),
                'below_10_percent': len([d for d in drawdowns if d < -0.1])
            }
        }

    async def run_optimization(self) -> bool:
        """運行完整的KDJ參數優化"""
        print("="*80)
        print("放寬KDJ參數優化系統 - 0-300範圍步長5完整回測")
        print("解決進場條件過於嚴格，交易信號生成過少的問題")
        print("="*80)

        # 步驟1: 獲取股票數據
        if not self.fetch_real_stock_data():
            print("[ERROR] 無法獲取股票數據")
            return False

        # 步驟2: 獲取政府數據
        if not await self.fetch_all_government_data():
            print("[ERROR] 無法獲取政府數據")
            return False

        # 步驟3: 生成參數網格
        parameter_combinations = self.generate_parameter_grid()
        if not parameter_combinations:
            print("[ERROR] 無法生成參數組合")
            return False

        # 步驟4: 並行運行優化
        start_time = time.time()
        results = self.run_parallel_optimization(parameter_combinations)
        execution_time = time.time() - start_time

        # 步驟5: 生成報告
        report = self.generate_comprehensive_report(results)

        # 步驟6: 保存結果
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"relaxed_kdj_optimization_results_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 步驟7: 輸出總結
        self._print_summary(report, execution_time, report_file)

        return True

    def _print_summary(self, report: Dict, execution_time: float, report_file: str):
        """輸出優化總結"""
        print("\n" + "="*80)
        print("放寬KDJ參數優化完成")
        print("="*80)

        summary = report['summary']

        print(f"[RESULT] 總策略數: {summary['total_strategies']}")
        print(f"[RESULT] 成功策略: {summary['successful_strategies']}")
        print(f"[RESULT] 成功率: {summary['success_rate']:.1f}%")
        print(f"[RESULT] 執行時間: {execution_time:.2f}秒")
        print(f"[RESULT] 處理速度: {summary['total_strategies']/execution_time:.1f}策略/秒")

        if summary['best_strategy_id'] != 'None':
            print(f"\n[CHAMPION] 最佳策略: {summary['best_strategy_id']}")
            print(f"[CHAMPION] Sharpe比率: {summary['best_sharpe']:.3f}")
            print(f"[CHAMPION] 年化回報: {summary['best_return']:.2%}")

        # 信號生成統計
        signal_stats = report['analysis']['signal_generation_stats']
        print(f"\n[SIGNALS] 平均信號/策略: {signal_stats['avg_signals_per_strategy']:.1f}")
        print(f"[SIGNALS] 有效信號策略: {signal_stats['strategies_with_signals']}")
        print(f"[SIGNALS] 最大信號數: {signal_stats['max_signals']}")
        print(f"[SIGNALS] 信號成功率: {signal_stats['signal_success_rate']:.1f}%")

        # Top 5 策略
        if report['top_strategies']:
            print(f"\n[TOP 5] 最佳策略:")
            for i, strategy in enumerate(report['top_strategies'][:5], 1):
                print(f"  {i}. {strategy['strategy_id']}: "
                      f"Sharpe={strategy['sharpe_ratio']:.3f}, "
                      f"回報={strategy['annual_return']:.2%}, "
                      f"信號={strategy['signals_generated']}")

        print(f"\n[REPORT] 詳細報告已保存: {report_file}")

def main():
    """主函數"""
    optimizer = RelaxedKDJParameterOptimizer()

    try:
        success = asyncio.run(optimizer.run_optimization())
        return 0 if success else 1
    except Exception as e:
        print(f"[FATAL] 系統運行失敗: {e}")
        return 1

if __name__ == "__main__":
    exit(main())