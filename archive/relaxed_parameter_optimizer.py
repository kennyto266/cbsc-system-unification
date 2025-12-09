#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
放寬回測進場條件的全面參數優化系統
基於OpenSpec relaxed-entry-conditions提案實現

核心功能:
- 0-300範圍，步長5的完整參數覆蓋
- 三種進場條件：嚴格/中等/寬鬆
- 高性能多進程並行處理
- 四大策略：RSI, MACD, KDJ, 布林帶

作者: Claude Code Assistant
日期: 2025-11-24
"""

import numpy as np
import pandas as pd
import time
import json
import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from itertools import product


class CompleteParameterSpace:
    """完整參數空間探索器 - 0-300範圍，步長5"""

    def __init__(self):
        # 完整的參數範圍定義
        self.parameter_ranges = {
            'rsi_period': list(range(5, 301, 5)),      # 5, 10, 15, ..., 300
            'macd_fast': list(range(5, 51, 5)),        # 5, 10, 15, ..., 50
            'macd_slow': list(range(55, 301, 5)),      # 55, 60, 65, ..., 300
            'macd_signal': list(range(5, 21, 5)),      # 5, 10, 15, 20
            'bb_period': list(range(5, 301, 5)),       # 5, 10, 15, ..., 300
            'bb_std': [1.5, 2.0, 2.5, 3.0],            # 布林帶標準差
            'kdj_k': list(range(5, 301, 5)),           # K週期: 5, 10, ..., 300
            'kdj_d': list(range(1, 21, 5)),            # D平滑: 1, 6, 11, 16
            'sma_short': list(range(5, 101, 5)),       # 短期SMA: 5, 10, ..., 100
            'sma_long': list(range(105, 301, 5))       # 長期SMA: 105, 110, ..., 300
        }

        # 三層進場條件系統
        self.entry_conditions = {
            'strict': {
                'oversold_levels': [25, 30, 35],
                'overbought_levels': [65, 70, 75],
                'description': '嚴格條件 - 需要明確穿越邊界'
            },
            'moderate': {
                'oversold_levels': [20, 25, 30, 35, 40],
                'overbought_levels': [60, 65, 70, 75, 80],
                'description': '中等條件 - 允許邊界附近觸發'
            },
            'relaxed': {
                'oversold_levels': [15, 20, 25, 30, 35, 40, 45],
                'overbought_levels': [55, 60, 65, 70, 75, 80, 85],
                'description': '寬鬆條件 - 大幅放寬進場門檻'
            }
        }

        print("[INIT] 完整參數空間生成器")
        print(f"[INIT] RSI週期範圍: {len(self.parameter_ranges['rsi_period'])}個值")
        print(f"[INIT] MACD參數組合: {len(self.parameter_ranges['macd_fast'])}×{len(self.parameter_ranges['macd_slow'])}×{len(self.parameter_ranges['macd_signal'])}")
        print(f"[INIT] KDJ參數組合: {len(self.parameter_ranges['kdj_k'])}×{len(self.parameter_ranges['kdj_d'])}")
        print(f"[INIT] 布林帶參數組合: {len(self.parameter_ranges['bb_period'])}×{len(self.parameter_ranges['bb_std'])}")

    def generate_all_combinations(self, strategy_type='all') -> Dict[str, List[Dict]]:
        """生成所有可能的參數組合"""

        all_combinations = {}

        if strategy_type in ['all', 'RSI']:
            # RSI策略組合
            rsi_combinations = []
            for period in self.parameter_ranges['rsi_period']:
                for condition_type, levels in self.entry_conditions.items():
                    for oversold in levels['oversold_levels']:
                        for overbought in levels['overbought_levels']:
                            if oversold < overbought:  # 確保邏輯正確
                                rsi_combinations.append({
                                    'strategy': 'RSI',
                                    'period': period,
                                    'oversold': oversold,
                                    'overbought': overbought,
                                    'condition_type': condition_type
                                })
            all_combinations['RSI'] = rsi_combinations

        if strategy_type in ['all', 'MACD']:
            # MACD策略組合
            macd_combinations = []
            for fast in self.parameter_ranges['macd_fast']:
                for slow in self.parameter_ranges['macd_slow']:
                    if fast < slow:  # 確保邏輯正確
                        for signal in self.parameter_ranges['macd_signal']:
                            macd_combinations.append({
                                'strategy': 'MACD',
                                'fast': fast,
                                'slow': slow,
                                'signal': signal,
                                'condition_type': 'standard'
                            })
            all_combinations['MACD'] = macd_combinations

        if strategy_type in ['all', 'KDJ']:
            # KDJ策略組合
            kdj_combinations = []
            for k_period in self.parameter_ranges['kdj_k']:
                for d_period in self.parameter_ranges['kdj_d']:
                    kdj_combinations.append({
                        'strategy': 'KDJ',
                        'k_period': k_period,
                        'd_period': d_period,
                        'condition_type': 'standard'
                    })
            all_combinations['KDJ'] = kdj_combinations

        if strategy_type in ['all', 'BOLLINGER_BANDS']:
            # 布林帶策略組合
            bb_combinations = []
            for period in self.parameter_ranges['bb_period']:
                for std in self.parameter_ranges['bb_std']:
                    bb_combinations.append({
                        'strategy': 'BOLLINGER_BANDS',
                        'period': period,
                        'std_dev': std,
                        'condition_type': 'standard'
                    })
            all_combinations['BOLLINGER_BANDS'] = bb_combinations

        return all_combinations

    def get_total_combinations_count(self) -> Dict[str, int]:
        """計算總策略組合數量"""
        combinations = self.generate_all_combinations()
        counts = {strategy: len(combos) for strategy, combos in combinations.items()}
        counts['total'] = sum(counts.values())
        return counts

    def validate_parameters(self, params: Dict[str, Any]) -> Tuple[bool, str]:
        """驗證參數邏輯"""
        try:
            if params['strategy'] == 'RSI':
                if params['oversold'] >= params['overbought']:
                    return False, "RSI oversold must be less than overbought"
                if not (5 <= params['period'] <= 300):
                    return False, "RSI period must be between 5 and 300"

            elif params['strategy'] == 'MACD':
                if params['fast'] >= params['slow']:
                    return False, "MACD fast must be less than slow"
                if not (5 <= params['fast'] <= 50):
                    return False, "MACD fast must be between 5 and 50"
                if not (55 <= params['slow'] <= 300):
                    return False, "MACD slow must be between 55 and 300"

            elif params['strategy'] == 'KDJ':
                if not (5 <= params['k_period'] <= 300):
                    return False, "KDJ K period must be between 5 and 300"
                if not (1 <= params['d_period'] <= 20):
                    return False, "KDJ D period must be between 1 and 20"

            elif params['strategy'] == 'BOLLINGER_BANDS':
                if not (5 <= params['period'] <= 300):
                    return False, "Bollinger Bands period must be between 5 and 300"
                if params['std_dev'] not in [1.5, 2.0, 2.5, 3.0]:
                    return False, "Bollinger Bands std dev must be 1.5, 2.0, 2.5, or 3.0"

            return True, "Valid parameters"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def print_summary(self):
        """打印參數空間摘要"""
        counts = self.get_total_combinations_count()

        print("\n" + "="*80)
        print("PARAMETER SPACE SUMMARY")
        print("="*80)

        print(f"RSI Strategies: {counts['RSI']:,} combinations")
        print(f"  - Period Range: 5-300 (step 5)")
        print(f"  - Entry Conditions: 3 types")
        print(f"  - oversold/overbought: {len(self.entry_conditions['strict']['oversold_levels'])} + {len(self.entry_conditions['moderate']['oversold_levels'])} + {len(self.entry_conditions['relaxed']['oversold_levels'])} choices")

        print(f"\nMACD Strategies: {counts['MACD']:,} combinations")
        print(f"  - Fast Range: 5-50 (step 5)")
        print(f"  - Slow Range: 55-300 (step 5)")
        print(f"  - Signal Range: 5-20 (step 5)")

        print(f"\nKDJ Strategies: {counts['KDJ']:,} combinations")
        print(f"  - K Period Range: 5-300 (step 5)")
        print(f"  - D Smoothing Range: 1-20 (step 5)")

        print(f"\nBollinger Bands Strategies: {counts['BOLLINGER_BANDS']:,} combinations")
        print(f"  - Period Range: 5-300 (step 5)")
        print(f"  - Std Dev Range: 1.5, 2.0, 2.5, 3.0")

        print(f"\nTotal Strategy Combinations: {counts['total']:,}")
        print(f"Estimated Processing Time: {counts['total']/200/60:.1f} minutes (based on 200 strategies/sec)")
        print("="*80)


class RelaxedEntryConditionEngine:
    """放寬的進場條件引擎"""

    def __init__(self, condition_type='moderate'):
        self.condition_type = condition_type
        self.min_trade_frequency = 0.1  # 最小交易頻率10%

        # 三層進場條件系統
        self.entry_conditions = {
            'strict': {
                'oversold_levels': [25, 30, 35],
                'overbought_levels': [65, 70, 75],
                'description': '嚴格條件 - 需要明確穿越邊界'
            },
            'moderate': {
                'oversold_levels': [20, 25, 30, 35, 40],
                'overbought_levels': [60, 65, 70, 75, 80],
                'description': '中等條件 - 允許邊界附近觸發'
            },
            'relaxed': {
                'oversold_levels': [15, 20, 25, 30, 35, 40, 45],
                'overbought_levels': [55, 60, 65, 70, 75, 80, 85],
                'description': '寬鬆條件 - 大幅放寬進場門檻'
            }
        }

        print(f"[INIT] Relaxed Entry Condition Engine")
        print(f"[INIT] Current condition type: {condition_type}")
        print(f"[INIT] Minimum trade frequency: {self.min_trade_frequency:.1%}")

    def generate_rsi_signals(self, rsi_series: pd.Series, oversold: float, overbought: float,
                           condition_type: str = None) -> Tuple[pd.Series, pd.Series]:
        """生成RSI交易信號 - 支持多種條件類型"""

        if condition_type is None:
            condition_type = self.condition_type

        if condition_type == 'strict':
            # 嚴格條件：需要明確穿越邊界
            entries = rsi_series < oversold
            exits = rsi_series > overbought

        elif condition_type == 'moderate':
            # 中等條件：接近邊界即可觸發
            oversold_buffer = 5
            overbought_buffer = 5

            entries = rsi_series < (oversold + oversold_buffer)
            exits = rsi_series > (overbought - overbought_buffer)

        elif condition_type == 'relaxed':
            # 寬鬆條件：大幅放寬進場門檻
            oversold_buffer = 10
            overbought_buffer = 10

            entries = rsi_series < (oversold + oversold_buffer)
            exits = rsi_series > (overbought - overbought_buffer)

        else:
            raise ValueError(f"Unknown condition type: {condition_type}")

        return entries, exits

    def generate_macd_signals(self, macd_line: pd.Series, signal_line: pd.Series,
                           condition_type: str = None) -> Tuple[pd.Series, pd.Series]:
        """生成MACD交易信號"""

        if condition_type is None:
            condition_type = self.condition_type

        if condition_type == 'strict':
            # 嚴格條件：明確的金叉死叉
            entries = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
            exits = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))

        elif condition_type == 'moderate':
            # 中等條件：接近零軸也考慮
            zero_cross_buffer = 0.1
            entries = ((macd_line > signal_line) &
                      (macd_line.shift(1) <= signal_line.shift(1))) | \
                     ((macd_line > zero_cross_buffer) & (macd_line.shift(1) <= zero_cross_buffer))
            exits = ((macd_line < signal_line) &
                    (macd_line.shift(1) >= signal_line.shift(1))) | \
                   ((macd_line < -zero_cross_buffer) & (macd_line.shift(1) >= -zero_cross_buffer))

        elif condition_type == 'relaxed':
            # 寬鬆條件：考慮趨勢方向
            trend_threshold = 0.05
            entries = (macd_line > signal_line) | (macd_line > trend_threshold)
            exits = (macd_line < signal_line) | (macd_line < -trend_threshold)

        return entries, exits

    def validate_signal_frequency(self, entries: pd.Series, exits: pd.Series,
                                 min_periods: int = 252) -> Tuple[bool, str]:
        """驗證交易信號頻率是否足夠"""

        total_periods = len(entries)
        if total_periods < min_periods:
            return False, f"Insufficient data period: {total_periods} < {min_periods}"

        # 計算交易信號數量
        entry_signals = entries.sum()
        exit_signals = exits.sum()

        # 計算交易頻率
        entry_frequency = entry_signals / total_periods
        exit_frequency = exit_signals / total_periods

        # 檢查是否達到最小交易頻率
        if entry_frequency < self.min_trade_frequency:
            return False, f"Entry signals too few: {entry_frequency:.2%} < {self.min_trade_frequency:.2%}"

        if exit_frequency < self.min_trade_frequency:
            return False, f"Exit signals too few: {exit_frequency:.2%} < {self.min_trade_frequency:.2%}"

        return True, f"Signal frequency normal: Entry{entry_frequency:.2%}, Exit{exit_frequency:.2%}"

    def print_condition_summary(self):
        """打印進場條件摘要"""
        print(f"\n" + "="*80)
        print("ENTRY CONDITION SYSTEM")
        print("="*80)

        for condition_type, levels in self.entry_conditions.items():
            print(f"\n{condition_type.upper()} CONDITIONS:")
            print(f"  • Oversold Range: {levels['oversold_levels']}")
            print(f"  • Overbought Range: {levels['overbought_levels']}")
            print(f"  • Description: {levels['description']}")

        print(f"\nCurrent Type: {self.condition_type}")
        print(f"Minimum Trade Frequency: {self.min_trade_frequency:.1%}")
        print("="*80)


# 測試代碼
if __name__ == "__main__":
    # 創建參數空間生成器
    param_space = CompleteParameterSpace()
    param_space.print_summary()

    # 創建進場條件引擎
    entry_engine = RelaxedEntryConditionEngine('moderate')
    entry_engine.print_condition_summary()

    # 生成少量組合進行測試
    print("\n測試參數組合生成...")
    test_combinations = param_space.generate_all_combinations('RSI')
    print(f"RSI測試組合數量: {len(test_combinations['RSI'])}")

    # 顯示前5個組合
    print("\n前5個RSI組合:")
    for i, combo in enumerate(test_combinations['RSI'][:5], 1):
        print(f"  {i}. {combo}")

    # 驗證參數
    print(f"\n參數驗證測試:")
    valid, msg = param_space.validate_parameters(test_combinations['RSI'][0])
    print(f"  測試組合: {msg}")

    print("\nCompleteParameterSpace 和 RelaxedEntryConditionEngine 初始化完成!")


import multiprocessing as mp
import concurrent.futures
import psutil
import requests
import asyncio
from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class StrategyResult:
    """策略回測結果數據結構"""
    strategy_type: str
    strategy_name: str
    params: Dict[str, Any]
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    trade_frequency: float
    quality_score: float
    execution_time: float
    success: bool = True
    error_message: Optional[str] = None


class AdvancedMultiProcessBacktestEngine:
    """高性能多進程回測引擎 - 基於實際驗證的32核並行架構"""

    def __init__(self, max_workers: Optional[int] = None):
        # 智能檢測並行核心數
        self.max_workers = max_workers or min(32, mp.cpu_count())
        self.parameter_space = CompleteParameterSpace()
        self.entry_engine = RelaxedEntryConditionEngine()

        # 進程池配置
        self.process_config = {
            'max_workers': self.max_workers,
            'mp_context': mp.get_context('spawn'),  # Windows兼容
            'timeout_per_task': 120,  # 120秒超時
            'chunk_size': 1000,       # 批次大小
            'memory_limit': '2GB'     # 每進程內存限制
        }

        print(f"[INIT] 高性能多進程回測引擎")
        print(f"[INIT] 檢測到CPU核心: {mp.cpu_count()}核")
        print(f"[INIT] 使用並行核心: {self.max_workers}核")
        print(f"[INIT] 內存總量: {psutil.virtual_memory().total / (1024**3):.1f}GB")
        print(f"[INIT] 進程上下文: {self.process_config['mp_context']}")

        # 計算總組合數量
        total_combinations = self.parameter_space.get_total_combinations_count()
        print(f"[INIT] 總策略組合: {total_combinations['total']:,}")
        print(f"[INIT] 預估處理時間: {total_combinations['total']/self.max_workers/60:.1f}分鐘")
        print(f"[INIT] 支持策略類型: RSI, MACD, KDJ, BOLLINGER_BANDS")

    def _worker_init(self):
        """工作進程初始化"""
        # 設置進程優先級
        try:
            import os
            os.nice(10)  # 降低優先級，避免影響系統
        except:
            pass

        # 預加載常用模塊
        import numpy as np
        import pandas as pd

    def run_comprehensive_optimization(self, stock_data: pd.DataFrame,
                                     government_data: Dict[str, pd.DataFrame]) -> List[StrategyResult]:
        """執行全面參數優化 - 智能分批並行處理"""

        print("\n" + "="*80)
        print("STARTING COMPREHENSIVE PARAMETER OPTIMIZATION")
        print("="*80)

        start_time = time.time()

        # 生成所有參數組合
        all_combinations = self.parameter_space.generate_all_combinations()

        # 準備多進程任務
        all_tasks = self._prepare_tasks(all_combinations, stock_data, government_data)

        print(f"\n[INFO] 任務準備完成:")
        print(f"       • RSI策略: {len(all_tasks['RSI']):,}個任務")
        print(f"       • MACD策略: {len(all_tasks['MACD']):,}個任務")
        print(f"       • KDJ策略: {len(all_tasks['KDJ']):,}個任務")
        print(f"       • 布林帶策略: {len(all_tasks['BOLLINGER_BANDS']):,}個任務")
        print(f"       • 總任務數: {sum(len(tasks) for tasks in all_tasks.values()):,}")

        # 分策略類型並行執行
        all_results = {}

        for strategy_type, tasks in all_tasks.items():
            print(f"\n[PROCESS] 開始處理 {strategy_type} 策略...")
            results = self._execute_strategy_batch(strategy_type, tasks)
            all_results[strategy_type] = results

            # 即時結果摘要
            if results:
                best_sharpe = max(r.get('sharpe_ratio', 0) for r in results)
                avg_sharpe = np.mean([r.get('sharpe_ratio', 0) for r in results])
                print(f"         ✓ 完成 {len(results)}個策略，最佳Sharpe: {best_sharpe:.3f}")
                print(f"         ✓ 平均Sharpe: {avg_sharpe:.3f}")

        # 合併和排序所有結果
        final_results = []
        for strategy_type, results in all_results.items():
            final_results.extend(results)

        # 按Sharpe比率排序
        final_results.sort(key=lambda x: x.get('sharpe_ratio', -999), reverse=True)

        # 性能統計
        end_time = time.time()
        execution_time = end_time - start_time
        total_tasks = sum(len(tasks) for tasks in all_tasks.values())
        success_rate = len(final_results) / total_tasks * 100

        print("\n" + "="*80)
        print("OPTIMIZATION COMPLETION STATISTICS")
        print("="*80)
        print(f"執行時間: {execution_time:.2f}秒 ({execution_time/60:.1f}分鐘)")
        print(f"成功策略: {len(final_results):,}/{total_tasks:,} ({success_rate:.1f}%)")
        print(f"處理速度: {total_tasks/execution_time:.1f} 策略/秒")
        print(f"並行效率: {self.max_workers * total_tasks/execution_time/60:.1f} 策略/核心/分鐘")

        # 最佳策略展示
        if final_results:
            print(f"\nTOP 5 BEST STRATEGIES:")
            for i, result in enumerate(final_results[:5], 1):
                print(f"   {i}. {result.strategy_name}")
                print(f"      Sharpe: {result.sharpe_ratio:.3f}, "
                      f"Return: {result.total_return:.2%}, "
                      f"Drawdown: {result.max_drawdown:.2%}")

        return final_results

    def _prepare_tasks(self, all_combinations: Dict[str, List[Dict]],
                        stock_data: pd.DataFrame, government_data: Dict[str, pd.DataFrame]) -> Dict[str, List[Dict]]:
        """準備多進程任務 - 數據序列化優化"""

        # 將大型數據轉換為更高效的格式
        stock_data_serializable = {
            'close': stock_data['close'].values,
            'dates': stock_data.index.tolist() if hasattr(stock_data.index, 'tolist') else list(range(len(stock_data))),
            'length': len(stock_data)
        }

        # 添加OHLC數據（如果可用）
        if 'open' in stock_data.columns:
            stock_data_serializable['open'] = stock_data['open'].values
        if 'high' in stock_data.columns:
            stock_data_serializable['high'] = stock_data['high'].values
        if 'low' in stock_data.columns:
            stock_data_serializable['low'] = stock_data['low'].values
        if 'volume' in stock_data.columns:
            stock_data_serializable['volume'] = stock_data['volume'].values

        government_data_serializable = {
            key: df.values if hasattr(df, 'values') else df
            for key, df in government_data.items()
        }

        all_tasks = {}

        for strategy_type, combinations in all_combinations.items():
            tasks = []
            for combo in combinations:
                task = {
                    'strategy': strategy_type,
                    'params': combo,
                    'stock_data': stock_data_serializable,
                    'government_data': government_data_serializable,
                    'task_id': f"{strategy_type}_{hash(str(combo)) % 1000000}"
                }
                tasks.append(task)

            all_tasks[strategy_type] = tasks

        return all_tasks

    def _execute_strategy_batch(self, strategy_type: str, tasks: List[Dict]) -> List[StrategyResult]:
        """執行單個策略類型的批次任務"""

        results = []
        completed = 0
        failed = 0

        # 使用進程池執行
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers,
            mp_context=self.process_config['mp_context'],
            initializer=self._worker_init
        ) as executor:

            # 提交所有任務
            future_to_task = {
                executor.submit(self._execute_single_backtest_optimized, task): task
                for task in tasks
            }

            # 收集結果
            for future in concurrent.futures.as_completed(future_to_task, timeout=300):
                task = future_to_task[future]
                completed += 1

                try:
                    result = future.result(timeout=self.process_config['timeout_per_task'])
                    if result and isinstance(result, StrategyResult):
                        results.append(result)
                    else:
                        failed += 1

                except concurrent.futures.TimeoutError:
                    failed += 1
                    print(f"[TIMEOUT] {strategy_type} 任務超時: {task['task_id']}")

                except Exception as e:
                    failed += 1
                    # 避免打印過多錯誤信息
                    if failed <= 5:
                        print(f"[ERROR] {strategy_type} 任務失敗: {str(e)[:100]}")

                # 進度報告
                if completed % 500 == 0 or completed == len(tasks):
                    progress = completed / len(tasks) * 100
                    print(f"[PROGRESS] {strategy_type}: {completed:,}/{len(tasks):,} ({progress:.1f}%) - "
                          f"成功: {len(results)}, 失敗: {failed}")

        # 最終統計
        if failed > 0:
            print(f"[WARNING] {strategy_type} 失敗任務: {failed}個")

        return results

    @staticmethod
    def _execute_single_backtest_optimized(task: Dict) -> Optional[StrategyResult]:
        """優化的單個回測任務執行 - 靜態方法避免序列化問題"""

        try:
            strategy_type = task['strategy']
            params = task['params']
            stock_data_raw = task['stock_data']
            government_data_raw = task['government_data']

            # 重構數據對象
            stock_data = pd.DataFrame({
                'close': stock_data_raw['close']
            })

            # 添加OHLC數據（如果可用）
            if 'open' in stock_data_raw:
                stock_data['open'] = stock_data_raw['open']
            if 'high' in stock_data_raw:
                stock_data['high'] = stock_data_raw['high']
            if 'low' in stock_data_raw:
                stock_data['low'] = stock_data_raw['low']
            if 'volume' in stock_data_raw:
                stock_data['volume'] = stock_data_raw['volume']

            # 確保有日期索引
            if 'dates' in stock_data_raw:
                stock_data.index = pd.to_datetime(stock_data_raw['dates'])

            # 動態導入策略實現器以避免循環導入
            from strategy_backtest_implementations import StrategyBacktestImplementations
            strategy_impl = StrategyBacktestImplementations()

            # 根據策略類型執行回測
            if strategy_type == 'RSI':
                return strategy_impl.backtest_rsi_strategy(params, stock_data)
            elif strategy_type == 'MACD':
                return strategy_impl.backtest_macd_strategy(params, stock_data)
            elif strategy_type == 'KDJ':
                return strategy_impl.backtest_kdj_strategy(params, stock_data)
            elif strategy_type == 'BOLLINGER_BANDS':
                return strategy_impl.backtest_bollinger_bands_strategy(params, stock_data)
            else:
                # 未知策略類型
                return StrategyResult(
                    strategy_type=strategy_type,
                    strategy_name=f"Unknown_{strategy_type}",
                    params=params,
                    sharpe_ratio=0.0,
                    total_return=0.0,
                    max_drawdown=0.0,
                    trade_frequency=0.0,
                    quality_score=0.0,
                    execution_time=0.0,
                    success=False,
                    error_message=f"Unknown strategy type: {strategy_type}"
                )

        except Exception as e:
            # 返回錯誤信息而不是直接拋出異常
            return StrategyResult(
                strategy_type=strategy_type,
                strategy_name=f"Error_{strategy_type}",
                params=params,
                sharpe_ratio=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                trade_frequency=0.0,
                quality_score=0.0,
                execution_time=0.0,
                success=False,
                error_message=str(e)
            )

    @staticmethod
    def _backtest_rsi_strategy_optimized(params: Dict, stock_data: pd.DataFrame) -> StrategyResult:
        """優化的RSI策略回測"""

        import time
        start_time = time.time()

        period = params['period']
        oversold = params['oversold']
        overbought = params['overbought']
        condition_type = params['condition_type']

        # 快速RSI計算
        close_prices = stock_data['close'].values
        rsi = AdvancedMultiProcessBacktestEngine._calculate_rsi_fast(close_prices, period)

        # 生成交易信號
        entries, exits = AdvancedMultiProcessBacktestEngine._generate_rsi_signals_fast(
            rsi, oversold, overbought, condition_type
        )

        # 驗證信號頻率
        total_periods = len(entries)
        entry_frequency = entries.sum() / total_periods
        exit_frequency = exits.sum() / total_periods

        if entry_frequency < 0.1 or exit_frequency < 0.1:
            return StrategyResult(
                strategy_type='RSI',
                strategy_name=f"RSI_{period}_{oversold}_{overbought}_{condition_type}",
                params=params,
                sharpe_ratio=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                trade_frequency=entry_frequency,
                quality_score=0.0,
                execution_time=time.time() - start_time,
                success=False,
                error_message="Trade frequency too low"
            )

        # 計算回測結果
        returns = AdvancedMultiProcessBacktestEngine._calculate_returns_fast(
            close_prices, entries, exits
        )

        if len(returns) == 0:
            return StrategyResult(
                strategy_type='RSI',
                strategy_name=f"RSI_{period}_{oversold}_{overbought}_{condition_type}",
                params=params,
                sharpe_ratio=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                trade_frequency=entry_frequency,
                quality_score=0.0,
                execution_time=time.time() - start_time,
                success=False,
                error_message="No returns calculated"
            )

        # 計算性能指標
        sharpe_ratio = AdvancedMultiProcessBacktestEngine._calculate_sharpe_fast(returns)
        max_drawdown = AdvancedMultiProcessBacktestEngine._calculate_max_drawdown_fast(returns)
        total_return = (1 + returns).prod() - 1

        # 計算質量分數
        quality_score = (
            min(sharpe_ratio * 20, 40) +  # Sharpe權重40%
            min(total_return * 50, 30) +   # 回報權重30%
            min((1 + max_drawdown) * 20, 20) +  # 回撤權重20%
            min(entry_frequency * 100, 10)  # 頻率權重10%
        )

        return StrategyResult(
            strategy_type='RSI',
            strategy_name=f"RSI_{period}_{oversold}_{overbought}_{condition_type}",
            params=params,
            sharpe_ratio=sharpe_ratio,
            total_return=total_return,
            max_drawdown=max_drawdown,
            trade_frequency=entry_frequency,
            quality_score=quality_score,
            execution_time=time.time() - start_time,
            success=True
        )

    @staticmethod
    def _calculate_rsi_fast(prices: np.ndarray, period: int) -> np.ndarray:
        """快速RSI計算 - 向量化實現"""
        delta = np.diff(prices)
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.zeros_like(prices)
        avg_loss = np.zeros_like(prices)

        if len(gain) >= period:
            avg_gain[period] = np.mean(gain[:period])
            avg_loss[period] = np.mean(loss[:period])

            for i in range(period + 1, len(prices)):
                avg_gain[i] = (avg_gain[i-1] * (period-1) + gain[i-1]) / period
                avg_loss[i] = (avg_loss[i-1] * (period-1) + loss[i-1]) / period

            rs = avg_gain[period:] / (avg_loss[period:] + 1e-10)
            rsi = 100 - (100 / (1 + rs))
            return np.concatenate([[np.nan] * period, rsi])

        return np.full(len(prices), np.nan)

    @staticmethod
    def _generate_rsi_signals_fast(rsi: np.ndarray, oversold: float, overbought: float,
                                   condition_type: str) -> Tuple[np.ndarray, np.ndarray]:
        """快速RSI信號生成"""

        if condition_type == 'strict':
            entries = rsi < oversold
            exits = rsi > overbought
        elif condition_type == 'moderate':
            entries = rsi < (oversold + 5)
            exits = rsi > (overbought - 5)
        else:  # relaxed
            entries = rsi < (oversold + 10)
            exits = rsi > (overbought - 10)

        return entries, exits

    @staticmethod
    def _calculate_returns_fast(prices: np.ndarray, entries: np.ndarray, exits: np.ndarray) -> np.ndarray:
        """快速回報計算"""
        positions = np.zeros_like(prices)

        # 簡化的進出場邏輯
        for i in range(1, len(positions)):
            if entries[i]:
                positions[i] = 1
            elif exits[i] and positions[i-1] > 0:
                positions[i] = 0
            else:
                positions[i] = positions[i-1]

        # 計算日收益率
        price_returns = np.diff(np.log(prices))
        strategy_returns = positions[1:] * price_returns

        return strategy_returns

    @staticmethod
    def _calculate_sharpe_fast(returns: np.ndarray, risk_free_rate: float = 0.03) -> float:
        """快速Sharpe計算"""
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate/252
        if np.std(excess_returns) == 0:
            return 0.0

        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

    @staticmethod
    def _calculate_max_drawdown_fast(returns: np.ndarray) -> float:
        """快速最大回撤計算"""
        if len(returns) == 0:
            return 0.0

        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        return np.min(drawdowns)