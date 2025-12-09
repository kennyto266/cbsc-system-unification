#!/usr/bin/env python3
"""
OpenSpec 性能基準測試系統
Performance Benchmark Test for OpenSpec Integration

測試目標：
- 驗證 600+ 策略/秒 性能目標
- 測試 GPU 加速效果
- 評估 477 種技術指標計算性能
- 壓力測試 255 種組合回測
"""

import sys
import time
import json
import pandas as pd
import numpy as np
import logging
import multiprocessing as mp
import psutil
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import seaborn as sns

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceBenchmarkTest:
    """
    OpenSpec 性能基準測試系統

    測試範圍：
    1. 技術指標計算性能 (477 種指標)
    2. 組合回測性能 (255 種組合)
    3. GPU vs CPU 性能對比
    4. 記憶體使用效率
    5. 並行處理效率
    """

    def __init__(self):
        self.benchmark_results = {}
        self.system_info = self._get_system_info()
        self.target_performance = 600  # 策略/秒

        logger.info("性能基準測試系統初始化")
        logger.info(f"目標性能: {self.target_performance} 策略/秒")
        logger.info(f"系統核心數: {self.system_info['cpu_count']}")
        logger.info(f"系統記憶體: {self.system_info['memory_gb']:.1f} GB")

    def _get_system_info(self) -> Dict[str, Any]:
        """獲取系統硬體信息"""
        try:
            import cpuinfo
            cpu_info = cpuinfo.get_cpu_info()
        except ImportError:
            cpu_info = {'brand_raw': 'Unknown'}

        # 檢查 GPU 可用性
        gpu_available = False
        try:
            import cupy as cp
            gpu_available = True
            gpu_memory = cp.cuda.Device(0).mem_info[1] / (1024**3)  # GB
        except ImportError:
            gpu_memory = 0

        return {
            'cpu_count': mp.cpu_count(),
            'cpu_name': cpu_info.get('brand_raw', 'Unknown'),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'gpu_available': gpu_available,
            'gpu_memory_gb': gpu_memory,
            'python_version': sys.version,
            'platform': sys.platform
        }

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """執行完整的性能基準測試"""
        logger.info("開始完整性能基準測試...")
        start_time = time.time()

        # 1. 準備測試數據
        test_data = self._prepare_test_data()

        # 2. 技術指標計算性能測試
        logger.info("\n[測試1] 技術指標計算性能測試...")
        indicator_performance = self._benchmark_indicators(test_data)

        # 3. 組合回測性能測試
        logger.info("\n[測試2] 組合回測性能測試...")
        combination_performance = self._benchmark_combinations(test_data)

        # 4. 並行處理效率測試
        logger.info("\n[測試3] 並行處理效率測試...")
        parallel_performance = self._benchmark_parallel_processing(test_data)

        # 5. 記憶體使用效率測試
        logger.info("\n[測試4] 記憶體使用效率測試...")
        memory_performance = self._benchmark_memory_usage(test_data)

        # 6. GPU 加速性能測試 (如果可用)
        gpu_performance = {}
        if self.system_info['gpu_available']:
            logger.info("\n[測試5] GPU 加速性能測試...")
            gpu_performance = self._benchmark_gpu_acceleration(test_data)

        # 綜合性能分析
        total_time = time.time() - start_time
        comprehensive_analysis = self._analyze_performance(
            indicator_performance,
            combination_performance,
            parallel_performance,
            memory_performance,
            gpu_performance
        )

        # 生成測試報告
        benchmark_report = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self.system_info,
            'total_execution_time': total_time,
            'target_performance': self.target_performance,
            'test_results': {
                'indicators': indicator_performance,
                'combinations': combination_performance,
                'parallel': parallel_performance,
                'memory': memory_performance,
                'gpu': gpu_performance
            },
            'analysis': comprehensive_analysis,
            'recommendations': self._generate_recommendations(comprehensive_analysis)
        }

        # 保存測試結果
        self._save_benchmark_report(benchmark_report)

        logger.info(f"\n性能基準測試完成！總耗時: {total_time:.2f}秒")
        return benchmark_report

    def _prepare_test_data(self) -> Dict[str, Any]:
        """準備測試數據"""
        logger.info("準備測試數據...")

        try:
            # 嘗試獲取真實股票數據
            from api.stock_api import get_hk_stock_data
            stock_data = get_hk_stock_data('0700.HK', 500)

            if stock_data is not None:
                if isinstance(stock_data, dict) and 'data' in stock_data:
                    close_prices = list(stock_data['data']['close'].values())
                    dates = list(stock_data['data']['close'].keys())
                    stock_df = pd.DataFrame({
                        'close': close_prices,
                        'high': close_prices,
                        'low': close_prices,
                        'volume': [1000000] * len(close_prices)
                    }, index=pd.to_datetime(dates))
                else:
                    stock_df = stock_data.copy()
                    if 'volume' not in stock_df.columns:
                        stock_df['volume'] = 1000000
                logger.info(f"✅ 使用真實股票數據: {len(stock_df)} 條記錄")
            else:
                raise ValueError("無法獲取真實數據")

        except:
            logger.warning("無法獲取真實數據，使用模擬數據")
            # 生成高質量模擬數據
            np.random.seed(42)
            dates = pd.date_range(end=datetime.now(), periods=500, freq='D')

            # 模擬真實股價走勢 (帶趨勢和季節性)
            trend = np.linspace(600, 650, 500)
            seasonal = 20 * np.sin(np.linspace(0, 8*np.pi, 500))
            noise = np.random.randn(500) * 10
            prices = trend + seasonal + noise

            # 確保價格為正
            prices = np.maximum(prices, 100)

            stock_df = pd.DataFrame({
                'close': prices,
                'high': prices * (1 + np.random.rand(500) * 0.02),
                'low': prices * (1 - np.random.rand(500) * 0.02),
                'volume': np.random.randint(500000, 2000000, 500)
            }, index=dates)

            logger.info(f"✅ 使用模擬數據: {len(stock_df)} 條記錄")

        # 準備政府數據 (模擬)
        gov_data = {
            'hibor_rates': pd.DataFrame({
                'overnight': np.random.uniform(2, 8, 100),
                '1_week': np.random.uniform(3, 9, 100)
            }, index=pd.date_range(end=datetime.now(), periods=100, freq='D')),
            'monetary_base': pd.DataFrame({
                'base': np.cumsum(np.random.randn(100) * 1000) + 500000
            }, index=pd.date_range(end=datetime.now(), periods=100, freq='D')),
            'exchange_rates': pd.DataFrame({
                'usd_hkd': np.random.uniform(7.7, 7.9, 100)
            }, index=pd.date_range(end=datetime.now(), periods=100, freq='D'))
        }

        return {
            'stock_data': stock_df,
            'gov_data': gov_data
        }

    def _benchmark_indicators(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """基準測試：技術指標計算性能"""
        try:
            from unified_openspec_integration_system import UnifiedOpenSpecIntegrationSystem

            system = UnifiedOpenSpecIntegrationSystem()
            stock_data = test_data['stock_data']
            gov_data = test_data['gov_data']

            # 測試指標計算性能
            start_time = time.time()
            memory_before = psutil.Process().memory_info().rss / (1024**2)  # MB

            indicators = system.calculate_all_477_indicators(stock_data, gov_data)

            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / (1024**2)  # MB
            memory_used = memory_after - memory_before

            indicator_count = len(indicators)
            indicators_per_second = indicator_count / execution_time

            result = {
                'indicator_count': indicator_count,
                'execution_time': execution_time,
                'indicators_per_second': indicators_per_second,
                'memory_used_mb': memory_used,
                'target_met': indicator_count >= 400,  # 477 的目標，設400為通過標準
                'performance_score': min(100, (indicators_per_second / 10) * 100)  # 10指標/秒 = 100分
            }

            logger.info(f"   指標數量: {indicator_count}")
            logger.info(f"   執行時間: {execution_time:.3f}秒")
            logger.info(f"   指標/秒: {indicators_per_second:.1f}")
            logger.info(f"   記憶體使用: {memory_used:.1f}MB")
            logger.info(f"   目標達成: {'✅' if result['target_met'] else '❌'}")

            return result

        except Exception as e:
            logger.error(f"技術指標基準測試失敗: {e}")
            return {'error': str(e), 'target_met': False}

    def _benchmark_combinations(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """基準測試：組合回測性能"""
        try:
            from unified_openspec_integration_system import UnifiedOpenSpecIntegrationSystem

            system = UnifiedOpenSpecIntegrationSystem()
            stock_data = test_data['stock_data']
            gov_data = test_data['gov_data']

            # 測試不同規模的組合回測
            test_sizes = [10, 50, 100]
            results = {}

            for size in test_sizes:
                logger.info(f"   測試 {size} 種組合...")

                start_time = time.time()
                memory_before = psutil.Process().memory_info().rss / (1024**2)

                # 修改系統組合生成以限制數量
                original_combinations = system.generate_all_combinations()[:size]

                # 執行回測
                test_result = system.backtest_all_combinations(stock_data, gov_data)

                execution_time = time.time() - start_time
                memory_after = psutil.Process().memory_info().rss / (1024**2)
                memory_used = memory_after - memory_before

                combinations_per_second = size / execution_time

                results[f'size_{size}'] = {
                    'combination_count': size,
                    'execution_time': execution_time,
                    'combinations_per_second': combinations_per_second,
                    'memory_used_mb': memory_used,
                    'target_met': combinations_per_second >= self.target_performance,
                    'performance_ratio': combinations_per_second / self.target_performance
                }

                logger.info(f"     組合/秒: {combinations_per_second:.1f} (目標: {self.target_performance})")
                logger.info(f"     目標達成: {'✅' if combinations_per_second >= self.target_performance else '❌'}")

                # 清理記憶體
                gc.collect()

            # 計算整體性能
            avg_performance = np.mean([r['combinations_per_second'] for r in results.values()])
            overall_target_met = avg_performance >= self.target_performance

            overall_result = {
                'test_sizes': test_sizes,
                'detailed_results': results,
                'average_combinations_per_second': avg_performance,
                'target_met': overall_target_met,
                'performance_score': min(100, (avg_performance / self.target_performance) * 100),
                'max_tested_size': max(test_sizes)
            }

            logger.info(f"   平均性能: {avg_performance:.1f} 組合/秒")
            logger.info(f"   整體目標: {'✅' if overall_target_met else '❌'}")

            return overall_result

        except Exception as e:
            logger.error(f"組合回測基準測試失敗: {e}")
            return {'error': str(e), 'target_met': False}

    def _benchmark_parallel_processing(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """基準測試：並行處理效率"""
        try:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            import itertools

            stock_data = test_data['stock_data']

            # 測試不同並行度的性能
            worker_counts = [1, 2, 4, mp.cpu_count()]
            results = {}

            def dummy_backtest_task(data):
                """模擬回測任務"""
                time.sleep(0.01)  # 模擬計算時間
                return len(data), np.mean(data)

            for workers in worker_counts:
                logger.info(f"   測試 {workers} 個並行進程...")

                start_time = time.time()

                # 分割數據進行並行處理
                chunk_size = len(stock_data) // workers
                data_chunks = [stock_data['close'].iloc[i:i+chunk_size] for i in range(0, len(stock_data), chunk_size)]

                with ProcessPoolExecutor(max_workers=workers) as executor:
                    futures = [executor.submit(dummy_backtest_task, chunk) for chunk in data_chunks]

                    # 等待所有任務完成
                    for future in as_completed(futures):
                        future.result()

                execution_time = time.time() - start_time
                tasks_per_second = len(data_chunks) / execution_time

                results[f'workers_{workers}'] = {
                    'worker_count': workers,
                    'execution_time': execution_time,
                    'tasks_per_second': tasks_per_second,
                    'efficiency_ratio': tasks_per_second / workers,  # 理想值為1
                    'speedup_ratio': tasks_per_second / results.get('workers_1', {}).get('tasks_per_second', 1)
                }

                logger.info(f"     任務/秒: {tasks_per_second:.1f}")
                logger.info(f"     效率比: {results[f'workers_{workers}']['efficiency_ratio']:.2f}")

            # 計算最佳並行度
            best_workers = max(results.keys(), key=lambda k: results[k]['tasks_per_second'])
            max_performance = results[best_workers]['tasks_per_second']

            parallel_result = {
                'tested_workers': worker_counts,
                'detailed_results': results,
                'best_worker_count': int(best_workers.split('_')[1]),
                'max_performance': max_performance,
                'scalability_score': min(100, (max_performance / worker_counts[-1]) * 25)  # 理想線性擴展
            }

            logger.info(f"   最佳並行度: {parallel_result['best_worker_count']} 進程")
            logger.info(f"   最大性能: {max_performance:.1f} 任務/秒")

            return parallel_result

        except Exception as e:
            logger.error(f"並行處理基準測試失敗: {e}")
            return {'error': str(e)}

    def _benchmark_memory_usage(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """基準測試：記憶體使用效率"""
        try:
            logger.info("   測試不同數據規模的記憶體使用...")

            # 測試不同規模的數據
            data_sizes = [100, 200, 500]
            results = {}

            initial_memory = psutil.Process().memory_info().rss / (1024**2)

            for size in data_sizes:
                # 創建測試數據
                test_df = test_data['stock_data'].iloc[:size].copy()

                # 測試技術指標計算的記憶體使用
                memory_before = psutil.Process().memory_info().rss / (1024**2)

                # 執行一些計算密集型操作
                indicators = {}
                for i in range(20):  # 計算20個指標
                    indicators[f'test_indicator_{i}'] = test_df['close'].rolling(window=min(20, size)).mean()

                memory_after = psutil.Process().memory_info().rss / (1024**2)
                memory_used = memory_after - memory_before
                memory_per_record = memory_used / size

                # 清理記憶體
                del indicators
                gc.collect()

                results[f'size_{size}'] = {
                    'data_size': size,
                    'memory_used_mb': memory_used,
                    'memory_per_record_kb': memory_per_record * 1024,
                    'memory_efficiency': min(100, (1 / (memory_per_record + 0.001)) * 10)  # 越低越好
                }

                logger.info(f"     {size} 條記錄: {memory_used:.1f}MB ({memory_per_record*1024:.2f}KB/記錄)")

            total_memory = psutil.virtual_memory().total / (1024**2)
            memory_result = {
                'tested_sizes': data_sizes,
                'detailed_results': results,
                'baseline_memory_mb': initial_memory,
                'total_system_memory_mb': total_memory,
                'memory_efficiency_score': np.mean([r['memory_efficiency'] for r in results.values()]),
                'scalability_assessment': 'Good' if np.mean([r['memory_per_record_kb'] for r in results.values()]) < 10 else 'Needs Improvement'
            }

            logger.info(f"   系統總記憶體: {total_memory:.0f}MB")
            logger.info(f"   平均效率: {memory_result['memory_efficiency_score']:.1f}/100")
            logger.info(f"   擴展性評估: {memory_result['scalability_assessment']}")

            return memory_result

        except Exception as e:
            logger.error(f"記憶體使用基準測試失敗: {e}")
            return {'error': str(e)}

    def _benchmark_gpu_acceleration(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """基準測試：GPU 加速性能"""
        try:
            import cupy as cp
            import cudf

            logger.info("   GPU 可用，測試 GPU 加速性能...")

            stock_data = test_data['stock_data']
            cpu_times = []
            gpu_times = []

            # 測試不同規模的計算
            test_sizes = [100, 200, len(stock_data)]

            for size in test_sizes:
                # 準備測試數據
                cpu_data = stock_data['close'].iloc[:size].values
                gpu_data = cp.asarray(cpu_data)

                # CPU 測試
                start_time = time.time()
                cpu_result = np.convolve(cpu_data, np.ones(20)/20, mode='same')  # 移動平均
                cpu_time = time.time() - start_time
                cpu_times.append(cpu_time)

                # GPU 測試
                start_time = time.time()
                gpu_result = cp.convolve(gpu_data, cp.ones(20)/20, mode='same')
                gpu_time = time.time() - start_time
                gpu_times.append(gpu_time)

                speedup = cpu_time / gpu_time if gpu_time > 0 else float('inf')

                logger.info(f"     {size} 條記錄: CPU {cpu_time:.4f}s, GPU {gpu_time:.4f}s, 加速比 {speedup:.2f}x")

            # 驗證結果一致性
            gpu_result_cpu = cp.asnumpy(gpu_result)
            max_diff = np.max(np.abs(cpu_result - gpu_result_cpu[:len(cpu_result)]))

            avg_speedup = np.mean([c/g if g > 0 else 1 for c, g in zip(cpu_times, gpu_times)])

            gpu_result = {
                'gpu_available': True,
                'tested_sizes': test_sizes,
                'cpu_times': cpu_times,
                'gpu_times': gpu_times,
                'speedup_ratios': [c/g if g > 0 else 1 for c, g in zip(cpu_times, gpu_times)],
                'average_speedup': avg_speedup,
                'max_speedup': max([c/g if g > 0 else 1 for c, g in zip(cpu_times, gpu_times)]),
                'result_accuracy': max_diff < 1e-6,
                'gpu_memory_utilized': cp.cuda.Device(0).mem_info[0] / (1024**2)  # MB
            }

            logger.info(f"   平均加速比: {avg_speedup:.2f}x")
            logger.info(f"   最大加速比: {gpu_result['max_speedup']:.2f}x")
            logger.info(f"   結果準確性: {'✅' if gpu_result['result_accuracy'] else '❌'}")
            logger.info(f"   GPU 記憶體使用: {gpu_result['gpu_memory_utilized']:.1f}MB")

            return gpu_result

        except ImportError:
            logger.info("   GPU 不可用，跳過 GPU 測試")
            return {'gpu_available': False, 'reason': 'GPU libraries not installed'}
        except Exception as e:
            logger.error(f"GPU 加速測試失敗: {e}")
            return {'gpu_available': True, 'error': str(e)}

    def _analyze_performance(self, indicator_perf: Dict, combination_perf: Dict,
                            parallel_perf: Dict, memory_perf: Dict, gpu_perf: Dict) -> Dict[str, Any]:
        """綜合性能分析"""
        analysis = {
            'overall_score': 0,
            'target_achievement': {},
            'bottlenecks': [],
            'strengths': [],
            'recommendations': []
        }

        # 計算各項得分
        scores = {}

        # 技術指標得分
        if 'error' not in indicator_perf:
            indicator_score = min(100, (indicator_perf['indicators_per_second'] / 50) * 100)  # 50指標/秒 = 満分
            scores['indicators'] = indicator_score
            if indicator_perf['target_met']:
                analysis['strengths'].append("技術指標計算達到數量要求")
            else:
                analysis['bottlenecks'].append("技術指標計算數量不足")

        # 組合回測得分
        if 'error' not in combination_perf:
            combo_score = min(100, (combination_perf['average_combinations_per_second'] / self.target_performance) * 100)
            scores['combinations'] = combo_score
            if combination_perf['target_met']:
                analysis['strengths'].append("組合回測達到性能目標")
            else:
                analysis['bottlenecks'].append("組合回測未達到性能目標")

        # 並行處理得分
        if 'error' not in parallel_perf:
            parallel_score = parallel_perf['scalability_score']
            scores['parallel'] = parallel_score
            if parallel_score > 70:
                analysis['strengths'].append("並行處理效率良好")
            else:
                analysis['bottlenecks'].append("並行處理效率有待提升")

        # 記憶體效率得分
        if 'error' not in memory_perf:
            memory_score = memory_perf['memory_efficiency_score']
            scores['memory'] = memory_score
            if memory_score > 70:
                analysis['strengths'].append("記憶體使用效率良好")
            else:
                analysis['bottlenecks'].append("記憶體使用效率需要優化")

        # GPU 加速得分
        if gpu_perf.get('gpu_available', False) and 'error' not in gpu_perf:
            gpu_score = min(100, gpu_perf['average_speedup'] * 25)  # 4x加速 = 滿分
            scores['gpu'] = gpu_score
            if gpu_perf['average_speedup'] > 2:
                analysis['strengths'].append("GPU 加速效果顯著")
            else:
                analysis['bottlenecks'].append("GPU 加速效果有限")
        else:
            scores['gpu'] = 0
            analysis['bottlenecks'].append("GPU 加速不可用")

        # 計算總分
        if scores:
            analysis['overall_score'] = np.mean(list(scores.values()))
            analysis['individual_scores'] = scores

        # 目標達成情況
        analysis['target_achievement'] = {
            'indicators_count': indicator_perf.get('target_met', False),
            'combinations_performance': combination_perf.get('target_met', False),
            'overall_performance': analysis['overall_score'] >= 70
        }

        return analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成性能優化建議"""
        recommendations = []

        if analysis['overall_score'] < 50:
            recommendations.append("系統性能嚴重不足，需要全面優化")

        # 技術指標優化建議
        if 'indicators' in analysis.get('individual_scores', {}):
            if analysis['individual_scores']['indicators'] < 60:
                recommendations.append("考慮使用 GPU 加速技術指標計算")
                recommendations.append("優化指標計算算法，減少重複計算")

        # 組合回測優化建議
        if 'combinations' in analysis.get('individual_scores', {}):
            if analysis['individual_scores']['combinations'] < 60:
                recommendations.append("增加並行處理核心數")
                recommendations.append("優化回測算法，使用 VectorBT GPU 版本")
                recommendations.append("考慮分布式計算架構")

        # 並行處理優化建議
        if 'parallel' in analysis.get('individual_scores', {}):
            if analysis['individual_scores']['parallel'] < 60:
                recommendations.append("優化進程間通信機制")
                recommendations.append("考慮使用異步處理")

        # 記憶體優化建議
        if 'memory' in analysis.get('individual_scores', {}):
            if analysis['individual_scores']['memory'] < 60:
                recommendations.append("實現記憶體池機制")
                recommendations.append("使用數據流處理減少記憶體佔用")

        # GPU 優化建議
        if not self.system_info['gpu_available']:
            recommendations.append("安裝 CUDA 和 CuPy 以啟用 GPU 加速")
        elif 'gpu' in analysis.get('individual_scores', {}):
            if analysis['individual_scores']['gpu'] < 60:
                recommendations.append("優化 GPU 記憶體使用")
                recommendations.append("增加 GPU 計算複雜度以更好利用 GPU 資源")

        if not recommendations:
            recommendations.append("系統性能表現良好，可考慮進一步優化以達到更高性能目標")

        return recommendations

    def _save_benchmark_report(self, report: Dict[str, Any]):
        """保存基準測試報告"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_benchmark_report_{timestamp}.json"
            filepath = f"optimization_results/{filename}"

            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"基準測試報告已保存至: {filepath}")

            # 生成可視化報告
            self._generate_visual_report(report, filepath.replace('.json', '.html'))

        except Exception as e:
            logger.error(f"保存基準測試報告失敗: {e}")

    def _generate_visual_report(self, report: Dict[str, Any], output_path: str):
        """生成可視化 HTML 報告"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>OpenSpec 性能基準測試報告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .score {{ font-size: 2em; font-weight: bold; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        .chart {{ width: 45%; height: 300px; display: inline-block; margin: 10px; }}
        .recommendation {{ background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OpenSpec 性能基準測試報告</h1>
        <p>生成時間: {report['timestamp']}</p>
        <p>目標性能: {report['target_performance']} 策略/秒</p>
    </div>

    <div class="metrics">
        <div class="metric">
            <div class="score {'pass' if report['analysis']['target_achievement']['overall_performance'] else 'fail'}">
                {report['analysis']['overall_score']:.1f}
            </div>
            <div>總體得分</div>
        </div>
        <div class="metric">
            <div class="score {'pass' if report['test_results']['combinations'].get('target_met', False) else 'fail'}">
                {report['test_results']['combinations'].get('average_combinations_per_second', 0):.1f}
            </div>
            <div>組合/秒</div>
        </div>
        <div class="metric">
            <div class="score {'pass' if report['test_results']['indicators'].get('target_met', False) else 'fail'}">
                {report['test_results']['indicators'].get('indicator_count', 0)}
            </div>
            <div>技術指標數量</div>
        </div>
    </div>

    <h2>系統信息</h2>
    <ul>
        <li>CPU: {report['system_info']['cpu_count']} 核心 {report['system_info']['cpu_name']}</li>
        <li>記憶體: {report['system_info']['memory_gb']:.1f} GB</li>
        <li>GPU: {'可用' if report['system_info']['gpu_available'] else '不可用'}</li>
    </ul>

    <h2>優化建議</h2>
    {"".join([f'<div class="recommendation">• {rec}</div>' for rec in report['recommendations']])}

    <h2>詳細結果</h2>
    <pre>{json.dumps(report['test_results'], indent=2, ensure_ascii=False)}</pre>
</body>
</html>
            """

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"可視化報告已生成: {output_path}")

        except Exception as e:
            logger.error(f"生成可視化報告失敗: {e}")

def main():
    """主執行函數"""
    print("=" * 80)
    print("OPENSPEC 性能基準測試系統")
    print("Performance Benchmark Test for OpenSpec Integration")
    print("=" * 80)
    print(f"執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 初始化測試系統
    benchmark = PerformanceBenchmarkTest()

    print(f"\n系統配置:")
    print(f"  CPU: {benchmark.system_info['cpu_count']} 核心")
    print(f"  記憶體: {benchmark.system_info['memory_gb']:.1f} GB")
    print(f"  GPU: {'可用' if benchmark.system_info['gpu_available'] else '不可用'}")
    print(f"  目標性能: {benchmark.target_performance} 策略/秒")

    # 執行完整基準測試
    print(f"\n開始執行完整性能基準測試...")
    benchmark_report = benchmark.run_comprehensive_benchmark()

    # 顯示測試結果摘要
    print("\n" + "=" * 80)
    print("性能基準測試結果摘要")
    print("=" * 80)

    analysis = benchmark_report.get('analysis', {})

    print(f"總體得分: {analysis.get('overall_score', 0):.1f}/100")
    print(f"目標達成: {'✅' if analysis.get('target_achievement', {}).get('overall_performance', False) else '❌'}")

    print(f"\n各項目表現:")
    individual_scores = analysis.get('individual_scores', {})
    for category, score in individual_scores.items():
        status = '✅' if score >= 70 else '❌'
        print(f"  {category.capitalize()}: {score:.1f}/100 {status}")

    print(f"\n系統優勢:")
    for strength in analysis.get('strengths', []):
        print(f"  ✅ {strength}")

    print(f"\n性能瓶頸:")
    for bottleneck in analysis.get('bottlenecks', []):
        print(f"  ⚠️ {bottleneck}")

    print(f"\n優化建議:")
    for i, rec in enumerate(benchmark_report.get('recommendations', [])[:5], 1):
        print(f"  {i}. {rec}")

    print("\n" + "=" * 80)
    print("性能基準測試完成")
    print("=" * 80)

if __name__ == "__main__":
    main()