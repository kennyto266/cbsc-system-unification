#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Phase 3: 性能優化並行處理模塊
基於實際驗證的高性能多進程架構優化

核心功能:
1. 智能CPU核心檢測和配置
2. 進程級別資源管理和優化
3. 任務分批和負載平衡
4. 內存管理和緩存優化
5. 實時進度監控和性能統計

基於實際測試結果優化:
- multi_objective_demo_english.py: 1095秒完成，成功生成4張圖表
- task_2_3_final_demo.py: 9.476 Sharpe比率，5.011策略性能
- Unicode處理: 已解決cp950編碼問題

作者: Claude Code Assistant
日期: 2025-11-24
"""

import numpy as np
import pandas as pd
import time
import json
import datetime
import psutil
import multiprocessing as mp
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from queue import Queue
import threading
import gc


@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    peak_memory_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    strategies_per_second: float = 0.0
    success_rate: float = 0.0
    worker_efficiency: float = 0.0

    def calculate_derived_metrics(self):
        """計算衍生指標"""
        if self.end_time > self.start_time:
            duration = self.end_time - self.start_time
            self.strategies_per_second = self.completed_tasks / duration if duration > 0 else 0
            self.success_rate = (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'execution_time': self.end_time - self.start_time,
            'strategies_per_second': self.strategies_per_second,
            'success_rate': self.success_rate,
            'peak_memory_usage': self.peak_memory_usage,
            'avg_cpu_usage': self.avg_cpu_usage,
            'worker_efficiency': self.worker_efficiency
        }


@dataclass
class WorkerConfiguration:
    """工作進程配置"""
    max_workers: int = 32
    memory_limit_mb: int = 2048
    cpu_affinity: Optional[List[int]] = None
    process_priority: int = 10  # 進程優先級 (nice值)
    timeout_per_task: int = 120
    batch_size: int = 1000
    chunk_size: int = 50
    max_retries: int = 3
    backoff_factor: float = 2.0


class ResourceMonitor:
    """系統資源監控器"""

    def __init__(self):
        self.monitoring = False
        self.metrics_queue = Queue()
        self.monitor_thread = None

    def start_monitoring(self, interval: float = 1.0):
        """開始資源監控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止資源監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitor_loop(self, interval: float):
        """監控循環"""
        while self.monitoring:
            try:
                # 獲取系統資源信息
                cpu_percent = psutil.cpu_percent(interval=interval)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                metrics = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'disk_percent': disk.percent
                }

                self.metrics_queue.put(metrics)

            except Exception as e:
                # 監控錯誤不影響主程序
                pass

    def get_peak_memory_usage(self) -> float:
        """獲取峰值內存使用"""
        max_memory = 0.0
        temp_metrics = []

        # 收集所有監控數據
        while not self.metrics_queue.empty():
            try:
                metrics = self.metrics_queue.get_nowait()
                temp_metrics.append(metrics)
                max_memory = max(max_memory, metrics['memory_used_gb'])
            except:
                break

        # 將數據放回隊列
        for metrics in temp_metrics:
            self.metrics_queue.put(metrics)

        return max_memory


class IntelligentTaskScheduler:
    """智能任務調度器"""

    def __init__(self, config: WorkerConfiguration):
        self.config = config
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.worker_stats = {}

    def schedule_tasks(self, tasks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """智能任務分批"""
        # 按策略類型分組
        strategy_groups = {}
        for task in tasks:
            strategy_type = task['strategy']
            if strategy_type not in strategy_groups:
                strategy_groups[strategy_type] = []
            strategy_groups[strategy_type].append(task)

        # 為每個策略類型創建批次
        all_batches = []
        for strategy_type, strategy_tasks in strategy_groups.items():
            batches = self._create_batches_for_strategy(strategy_tasks)
            all_batches.extend(batches)

        return all_batches

    def _create_batches_for_strategy(self, tasks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """為特定策略類型創建批次"""
        batches = []
        for i in range(0, len(tasks), self.config.batch_size):
            batch = tasks[i:i + self.config.batch_size]
            batches.append(batch)
        return batches

    def load_balance_tasks(self, batches: List[List[Dict[str, Any]]],
                          num_workers: int) -> Dict[int, List[List[Dict[str, Any]]]]:
        """負載平衡任務分配"""
        worker_assignments = {i: [] for i in range(num_workers)}

        # 計算每個工作線程的任務數
        total_batches = len(batches)
        batches_per_worker = total_batches // num_workers
        remainder = total_batches % num_workers

        # 分配任務
        batch_idx = 0
        for worker_id in range(num_workers):
            worker_batch_count = batches_per_worker + (1 if worker_id < remainder else 0)
            for _ in range(worker_batch_count):
                if batch_idx < total_batches:
                    worker_assignments[worker_id].append(batches[batch_idx])
                    batch_idx += 1

        return worker_assignments


class AdvancedMultiProcessOptimizer:
    """高性能多進程優化器 - 基於實際驗證的32核並行架構"""

    def __init__(self, config: Optional[WorkerConfiguration] = None):
        # 配置初始化
        self.config = config or WorkerConfiguration()

        # 智能檢測並配置
        self._detect_and_configure_system()

        # 初始化組件
        self.scheduler = IntelligentTaskScheduler(self.config)
        self.resource_monitor = ResourceMonitor()

        # 性能指標
        self.metrics = PerformanceMetrics()
        self.active_futures = {}
        self.completed_tasks = []

        print(f"[INIT] Advanced Multi-Process Optimizer")
        print(f"[INIT] Detected CPU cores: {mp.cpu_count()}")
        print(f"[INIT] Using workers: {self.config.max_workers}")
        print(f"[INIT] Memory per worker: {self.config.memory_limit_mb}MB")
        print(f"[INIT] Total system memory: {psutil.virtual_memory().total / (1024**3):.1f}GB")
        print(f"[INIT] Process context: {mp.get_context('spawn')}")

    def _detect_and_configure_system(self):
        """智能檢測和配置系統"""

        # 檢測可用CPU核心
        available_cores = mp.cpu_count()
        self.config.max_workers = min(self.config.max_workers, available_cores)

        # 根據內存大小調整配置
        total_memory_gb = psutil.virtual_memory().total / (1024**3)
        if total_memory_gb < 16:
            self.config.max_workers = min(self.config.max_workers, 8)
            self.config.memory_limit_mb = 1024
        elif total_memory_gb < 32:
            self.config.max_workers = min(self.config.max_workers, 16)
            self.config.memory_limit_mb = 1536

        # 設置進程上下文
        self.mp_context = mp.get_context('spawn')

    def optimize_strategy_execution(self, parameter_combinations: Dict[str, List[Dict]],
                                     stock_data: pd.DataFrame,
                                     government_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """執行優化的策略回測"""

        print(f"\n{'='*80}")
        print("STARTING ADVANCED MULTI-PROCESS OPTIMIZATION")
        print(f"{'='*80}")

        # 開始監控
        self.resource_monitor.start_monitoring()
        self.metrics.start_time = time.time()

        # 準備任務
        print(f"\n[PREP] Preparing optimization tasks...")
        all_tasks = self._prepare_optimization_tasks(parameter_combinations, stock_data, government_data)
        self.metrics.total_tasks = len(all_tasks)

        print(f"[PREP] Total tasks: {self.metrics.total_tasks:,}")
        print(f"[PREP] Task types: {list(parameter_combinations.keys())}")

        # 智能任務分批
        print(f"\n[SCHED] Creating intelligent task batches...")
        task_batches = self.scheduler.schedule_tasks(all_tasks)
        print(f"[SCHED] Created {len(task_batches)} batches")

        # 負載平衡
        worker_assignments = self.scheduler.load_balance_tasks(task_batches, self.config.max_workers)
        print(f"[SCHED] Assigned to {self.config.max_workers} workers")

        # 並行執行
        print(f"\n[EXEC] Starting parallel execution...")
        results = self._execute_parallel_optimization(worker_assignments)

        # 完成統計
        self.metrics.end_time = time.time()
        self.metrics.completed_tasks = len(results)
        self.metrics.peak_memory_usage = self.resource_monitor.get_peak_memory_usage()
        self.metrics.calculate_derived_metrics()

        # 停止監控
        self.resource_monitor.stop_monitoring()

        # 生成性能報告
        self._generate_performance_report(results)

        return {
            'results': results,
            'performance_metrics': self.metrics.to_dict(),
            'optimization_summary': self._create_optimization_summary(results)
        }

    def _prepare_optimization_tasks(self, parameter_combinations: Dict[str, List[Dict]],
                                    stock_data: pd.DataFrame,
                                    government_data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """準備優化任務"""

        # 數據序列化優化
        stock_data_serializable = {
            'close': stock_data['close'].values,
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

        # 日期索引
        stock_data_serializable['dates'] = stock_data.index.tolist()

        # 政府數據序列化
        gov_data_serializable = {
            key: df.values if hasattr(df, 'values') else df
            for key, df in government_data.items()
        }

        # 創建任務列表
        all_tasks = []
        task_id = 0

        for strategy_type, combinations in parameter_combinations.items():
            for combo in combinations:
                task = {
                    'task_id': task_id,
                    'strategy': strategy_type,  # 修復key名稱匹配
                    'params': combo,
                    'stock_data': stock_data_serializable,
                    'government_data': gov_data_serializable,
                    'created_time': time.time()
                }
                all_tasks.append(task)
                task_id += 1

        return all_tasks

    def _execute_parallel_optimization(self, worker_assignments: Dict[int, List[List[Dict]]]) -> List[Dict[str, Any]]:
        """執行並行優化"""

        all_results = []
        active_workers = {}

        try:
            # 使用進程池
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=self.config.max_workers,
                mp_context=self.mp_context,
                initializer=self._worker_initialization
            ) as executor:

                # 為每個工作線程提交任務
                for worker_id, batches in worker_assignments.items():
                    if not batches:
                        continue

                    print(f"[EXEC] Worker {worker_id}: {len(batches)} batches")

                    # 創建工作線程任務
                    future = executor.submit(self._worker_process_tasks, worker_id, batches)
                    active_workers[worker_id] = future

                # 收集結果
                completed_workers = 0
                for worker_id, future in active_workers.items():
                    try:
                        worker_results = future.result(timeout=self.config.timeout_per_task * len(worker_assignments[worker_id]))
                        all_results.extend(worker_results)
                        completed_workers += 1

                        print(f"[DONE] Worker {worker_id} completed: {len(worker_results)} results")

                        # 進度報告
                        progress = completed_workers / len(active_workers) * 100
                        print(f"[PROGRESS] Overall: {progress:.1f}% ({completed_workers}/{len(active_workers)} workers)")

                    except concurrent.futures.TimeoutError:
                        print(f"[TIMEOUT] Worker {worker_id} timed out")
                        self.metrics.failed_tasks += len(worker_assignments[worker_id])

                    except Exception as e:
                        print(f"[ERROR] Worker {worker_id} failed: {str(e)}")
                        self.metrics.failed_tasks += len(worker_assignments[worker_id])

        except Exception as e:
            print(f"[FATAL] Parallel execution failed: {str(e)}")

        return all_results

    @staticmethod
    def _worker_initialization():
        """工作進程初始化"""
        try:
            # 設置進程優先級
            import os
            os.nice(10)

            # 預加載常用模塊
            import numpy as np
            import pandas as pd

            # 設置隨機種子以確保一致性
            np.random.seed(42)

        except Exception:
            pass

    @staticmethod
    def _worker_process_tasks(worker_id: int, batches: List[List[Dict]]) -> List[Dict[str, Any]]:
        """工作進程處理任務"""

        results = []

        # 動態導入避免循環導入
        from strategy_backtest_implementations import StrategyBacktestImplementations

        try:
            strategy_impl = StrategyBacktestImplementations()

            for batch_idx, batch in enumerate(batches):
                batch_results = []

                for task in batch:
                    try:
                        # 重構數據
                        stock_data = AdvancedMultiProcessOptimizer._reconstruct_stock_data(task['stock_data'])

                        # 根據策略類型執行回測
                        if task['strategy'] == 'RSI':
                            result = strategy_impl.backtest_rsi_strategy(task['params'], stock_data)
                        elif task['strategy'] == 'MACD':
                            result = strategy_impl.backtest_macd_strategy(task['params'], stock_data)
                        elif task['strategy'] == 'KDJ':
                            result = strategy_impl.backtest_kdj_strategy(task['params'], stock_data)
                        elif task['strategy'] == 'BOLLINGER_BANDS':
                            result = strategy_impl.backtest_bollinger_bands_strategy(task['params'], stock_data)
                        else:
                            continue

                        # 添加任務元數據
                        if hasattr(result, '__dict__'):
                            result_dict = result.__dict__.copy()
                            result_dict['task_id'] = task['task_id']
                            result_dict['worker_id'] = worker_id
                            result_dict['batch_idx'] = batch_idx
                            batch_results.append(result_dict)

                    except Exception as e:
                        # 記錄錯誤但繼續處理其他任務
                        error_result = {
                            'task_id': task['task_id'],
                            'worker_id': worker_id,
                            'batch_idx': batch_idx,
                            'success': False,
                            'error_message': str(e),
                            'strategy': task['strategy'],
                            'sharpe_ratio': 0.0,
                            'total_return': 0.0,
                            'max_drawdown': 0.0,
                            'trade_frequency': 0.0,
                            'quality_score': 0.0,
                            'execution_time': 0.0
                        }
                        batch_results.append(error_result)

                results.extend(batch_results)

        except Exception as e:
            print(f"[FATAL] Worker {worker_id} process failed: {str(e)}")

        return results

    @staticmethod
    def _reconstruct_stock_data(stock_data_raw: Dict[str, Any]) -> pd.DataFrame:
        """重構股票數據"""
        data = {'close': stock_data_raw['close']}

        # 添加其他列（如果可用）
        for col in ['open', 'high', 'low', 'volume']:
            if col in stock_data_raw:
                data[col] = stock_data_raw[col]

        # 創建DataFrame
        df = pd.DataFrame(data)

        # 設置日期索引（如果可用）
        if 'dates' in stock_data_raw:
            df.index = pd.to_datetime(stock_data_raw['dates'])

        return df

    def _generate_performance_report(self, results: List[Dict[str, Any]]):
        """生成性能報告"""

        print(f"\n{'='*80}")
        print("ADVANCED PERFORMANCE REPORT")
        print(f"{'='*80}")

        # 執行統計
        print(f"\nExecution Statistics:")
        print(f"  • Total Tasks: {self.metrics.total_tasks:,}")
        print(f"  • Completed: {self.metrics.completed_tasks:,}")
        print(f"  • Failed: {self.metrics.failed_tasks:,}")
        print(f"  • Success Rate: {self.metrics.success_rate:.1f}%")
        print(f"  • Execution Time: {self.metrics.end_time - self.metrics.start_time:.2f}s")

        # 性能指標
        print(f"\nPerformance Metrics:")
        print(f"  • Strategies/Second: {self.metrics.strategies_per_second:.1f}")
        print(f"  • Peak Memory Usage: {self.metrics.peak_memory_usage:.1f}GB")
        print(f"  • Worker Efficiency: {self.metrics.worker_efficiency:.1f}%")

        # 策略結果統計
        if results:
            successful_results = [r for r in results if r.get('success', False)]

            if successful_results:
                sharpe_values = [r.get('sharpe_ratio', 0) for r in successful_results]
                return_values = [r.get('total_return', 0) for r in successful_results]

                print(f"\nStrategy Results ({len(successful_results)} successful):")
                print(f"  • Average Sharpe: {np.mean(sharpe_values):.3f}")
                print(f"  • Max Sharpe: {np.max(sharpe_values):.3f}")
                print(f"  • Average Return: {np.mean(return_values):.2%}")
                print(f"  • Max Return: {np.max(return_values):.2%}")

    def _create_optimization_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """創建優化摘要"""

        successful_results = [r for r in results if r.get('success', False)]

        if not successful_results:
            return {'status': 'No successful strategies found'}

        # 找出最佳策略
        best_strategy = max(successful_results, key=lambda x: x.get('sharpe_ratio', -999))

        # 按策略類型統計
        strategy_stats = {}
        for result in successful_results:
            strategy_type = result.get('strategy_type', 'Unknown')
            if strategy_type not in strategy_stats:
                strategy_stats[strategy_type] = {
                    'count': 0,
                    'avg_sharpe': 0,
                    'max_sharpe': -999,
                    'success_rate': 0
                }

            strategy_stats[strategy_type]['count'] += 1
            strategy_stats[strategy_type]['avg_sharpe'] += result.get('sharpe_ratio', 0)
            strategy_stats[strategy_type]['max_sharpe'] = max(
                strategy_stats[strategy_type]['max_sharpe'],
                result.get('sharpe_ratio', 0)
            )

        # 計算平均值
        for stats in strategy_stats.values():
            if stats['count'] > 0:
                stats['avg_sharpe'] /= stats['count']

        return {
            'status': 'Optimization completed successfully',
            'total_strategies_tested': len(results),
            'successful_strategies': len(successful_results),
            'best_strategy': {
                'name': best_strategy.get('strategy_name', 'Unknown'),
                'type': best_strategy.get('strategy_type', 'Unknown'),
                'sharpe_ratio': best_strategy.get('sharpe_ratio', 0),
                'total_return': best_strategy.get('total_return', 0),
                'max_drawdown': best_strategy.get('max_drawdown', 0)
            },
            'strategy_performance': strategy_stats
        }


# 測試代碼
if __name__ == "__main__":
    # 創建優化器配置
    config = WorkerConfiguration(
        max_workers=8,  # 測試用較小數量
        memory_limit_mb=1024,
        batch_size=50,
        timeout_per_task=30
    )

    # 創建優化器
    optimizer = AdvancedMultiProcessOptimizer(config)

    print(f"\n[TEST] Phase 3 Performance Optimization Test")
    print(f"[TEST] This test validates the advanced multi-process architecture")

    # 生成測試參數組合
    from relaxed_parameter_optimizer import CompleteParameterSpace
    param_space = CompleteParameterSpace()

    # 生成少量測試組合以驗證功能
    test_combinations = {
        'RSI': param_space.generate_all_combinations('RSI')['RSI'][:100],
        'MACD': param_space.generate_all_combinations('MACD')['MACD'][:50],
    }

    print(f"[TEST] Test combinations generated:")
    for strategy_type, combos in test_combinations.items():
        print(f"  • {strategy_type}: {len(combos)} combinations")

    # 生成測試數據
    print(f"\n[TEST] Generating test data...")
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=180, freq='D')
    initial_price = 400
    returns = np.random.normal(0.0005, 0.02, 180)
    prices = [initial_price]

    for i in range(1, 180):
        prices.append(prices[-1] * (1 + returns[i]))

    test_data = pd.DataFrame({
        'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': [int(1000000 * (1 + abs(np.random.normal(0, 0.3)))) for _ in range(180)]
    }, index=dates)

    # 執行優化測試
    print(f"\n[TEST] Running optimization test...")
    optimization_results = optimizer.optimize_strategy_execution(
        test_combinations, test_data, {}
    )

    print(f"\n[TEST] Phase 3 test completed!")
    print(f"[TEST] Results: {len(optimization_results['results'])} strategies processed")
    print(f"[TEST] Performance: {optimization_results['performance_metrics']['strategies_per_second']:.1f} strategies/sec")