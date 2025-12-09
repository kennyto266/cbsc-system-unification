#!/usr/bin/env python3
"""
GPU性能基准测试 - 验证GPU加速效果和性能提升
GPU Performance Benchmark - Validate GPU acceleration and performance improvements

测试目标：
- 验证GPU vs CPU性能差异
- 测量不同数据规模的性能表现
- 验证计算精度一致性
- 提供性能基准报告
"""

import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Tuple
import json
import logging
from datetime import datetime
import multiprocessing as mp
import warnings

# 导入我们的GPU引擎
from src.performance.gpu_accelerated_engine import (
    GPUAcceleratedCoreIndicators,
    GPUOptimizedParameterOptimizer,
    GPUAccelerationConfig,
    get_gpu_indicators_engine,
    get_gpu_optimizer_engine
)
from src.indicators.core_indicators import CoreIndicators
from src.backtest.vectorbt_engine import VectorBTEngine

logger = logging.getLogger(__name__)

class GPUPerformanceBenchmark:
    """GPU性能基准测试套件"""

    def __init__(self):
        self.results = {}
        self.gpu_engine = None
        self.cpu_engine = None

        # 测试配置
        self.test_sizes = [1000, 5000, 10000, 50000, 100000]
        self.rsi_periods = [5, 10, 14, 20, 30, 50]
        self.macd_params = [(5, 10, 3), (12, 26, 9), (20, 40, 8)]

    def setup(self):
        """初始化测试环境"""
        logger.info("Setting up benchmark environment")

        # 初始化GPU引擎
        config = GPUAccelerationConfig(
            indicator_batch_size=50000,
            parallel_strategies=500,
            max_parameter_combinations=50000
        )

        self.gpu_engine = get_gpu_indicators_engine(config)
        self.gpu_optimizer = get_gpu_optimizer_engine(config)

        # 初始化CPU引擎
        self.cpu_engine = CoreIndicators()

        logger.info(f"GPU Backend: {self.gpu_engine.backend.get_backend_info()}")
        logger.info("Benchmark environment setup complete")

    def benchmark_rsi_calculation(self) -> Dict[str, Any]:
        """基准测试RSI计算性能"""
        logger.info("Starting RSI calculation benchmark")

        results = {
            'test_type': 'RSI Calculation',
            'data_sizes': [],
            'gpu_times': [],
            'cpu_times': [],
            'speedup_ratios': [],
            'accuracy_results': []
        }

        for size in self.test_sizes:
            logger.info(f"Testing RSI calculation with {size:,} data points")

            # 生成测试数据
            test_data = self._generate_price_data(size)

            # GPU计算
            start_time = time.time()
            for period in self.rsi_periods:
                gpu_rsi = self.gpu_engine.calculate_rsi_batch_gpu(
                    test_data.values, [period]
                )[period]
            gpu_time = time.time() - start_time

            # CPU计算
            start_time = time.time()
            for period in self.rsi_periods:
                cpu_rsi = self.cpu_engine.calculate_rsi(
                    test_data, period
                )
            cpu_time = time.time() - start_time

            # 验证精度
            gpu_rsi_single = self.gpu_engine.calculate_rsi(test_data.values, 14)
            cpu_rsi_single = self.cpu_engine.calculate_rsi(test_data, 14)
            accuracy = self._measure_accuracy(gpu_rsi_single, cpu_rsi_single)

            # 记录结果
            results['data_sizes'].append(size)
            results['gpu_times'].append(gpu_time)
            results['cpu_times'].append(cpu_time)
            results['speedup_ratios'].append(cpu_time / gpu_time if gpu_time > 0 else 0)
            results['accuracy_results'].append(accuracy)

            logger.info(f"Size {size:,}: GPU {gpu_time:.3f}s, CPU {cpu_time:.3f}s, "
                       f"Speedup {cpu_time/gpu_time:.1f}x, Accuracy {accuracy:.6f}")

        return results

    def benchmark_macd_calculation(self) -> Dict[str, Any]:
        """基准测试MACD计算性能"""
        logger.info("Starting MACD calculation benchmark")

        results = {
            'test_type': 'MACD Calculation',
            'data_sizes': [],
            'gpu_times': [],
            'cpu_times': [],
            'speedup_ratios': [],
            'accuracy_results': []
        }

        for size in self.test_sizes:
            logger.info(f"Testing MACD calculation with {size:,} data points")

            # 生成测试数据
            test_data = self._generate_price_data(size)

            # GPU计算
            start_time = time.time()
            gpu_results = self.gpu_engine.calculate_macd_batch_gpu(
                test_data.values, self.macd_params
            )
            gpu_time = time.time() - start_time

            # CPU计算
            start_time = time.time()
            cpu_results = {}
            for fast, slow, signal in self.macd_params:
                cpu_result = self.cpu_engine.calculate_macd(test_data, fast, slow, signal)
                cpu_results[(fast, slow, signal)] = cpu_result
            cpu_time = time.time() - start_time

            # 验证精度
            key_param = self.macd_params[0]
            gpu_accuracy = self._measure_accuracy(
                gpu_results[key_param]['macd'],
                cpu_results[key_param]['macd']
            )

            # 记录结果
            results['data_sizes'].append(size)
            results['gpu_times'].append(gpu_time)
            results['cpu_times'].append(cpu_time)
            results['speedup_ratios'].append(cpu_time / gpu_time if gpu_time > 0 else 0)
            results['accuracy_results'].append(gpu_accuracy)

            logger.info(f"Size {size:,}: GPU {gpu_time:.3f}s, CPU {cpu_time:.3f}s, "
                       f"Speedup {cpu_time/gpu_time:.1f}x, Accuracy {gpu_accuracy:.6f}")

        return results

    def benchmark_parameter_optimization(self) -> Dict[str, Any]:
        """基准测试参数优化性能"""
        logger.info("Starting parameter optimization benchmark")

        results = {
            'test_type': 'Parameter Optimization',
            'data_sizes': [],
            'combination_counts': [],
            'gpu_times': [],
            'strategies_per_second': [],
            'best_sharpe_ratios': []
        }

        # 测试不同规模的参数优化
        optimization_configs = [
            {'name': 'Small', 'periods': [5, 10, 14, 20], 'oversold': [20, 30], 'overbought': [70, 80]},
            {'name': 'Medium', 'periods': list(range(5, 31, 2)), 'oversold': [15, 20, 25, 30, 35], 'overbought': [65, 70, 75, 80, 85]},
            {'name': 'Large', 'periods': list(range(3, 51, 2)), 'oversold': list(range(10, 41, 5)), 'overbought': list(range(60, 91, 5))}
        ]

        test_data_size = 10000  # 使用固定大小的数据
        test_data = self._generate_ohlcv_data(test_data_size)

        for config in optimization_configs:
            logger.info(f"Testing {config['name']} optimization")

            param_ranges = {
                'period': config['periods'],
                'oversold': config['oversold'],
                'overbought': config['overbought']
            }

            # 计算参数组合数量
            total_combinations = (len(param_ranges['period']) *
                               len(param_ranges['oversold']) *
                               len(param_ranges['overbought']))

            # GPU优化
            start_time = time.time()
            gpu_result = self.gpu_optimizer.massive_parameter_optimization_gpu(
                test_data, param_ranges, "RSI_MEAN_REVERSION"
            )
            gpu_time = time.time() - start_time

            strategies_per_second = gpu_result['strategies_per_second']
            best_sharpe = gpu_result['best_strategy']['sharpe_ratio']

            # 记录结果
            results['data_sizes'].append(f"{config['name']} ({total_combinations:,} combos)")
            results['combination_counts'].append(total_combinations)
            results['gpu_times'].append(gpu_time)
            results['strategies_per_second'].append(strategies_per_second)
            results['best_sharpe_ratios'].append(best_sharpe)

            logger.info(f"{config['name']}: {total_combinations:,} combos in {gpu_time:.2f}s, "
                       f"{strategies_per_second:.1f} strategies/sec, Best Sharpe: {best_sharpe:.4f}")

        return results

    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """基准测试内存使用情况"""
        logger.info("Starting memory usage benchmark")

        results = {
            'test_type': 'Memory Usage',
            'data_sizes': [],
            'memory_before': [],
            'memory_after': [],
            'memory_usage_mb': []
        }

        try:
            import psutil
            process = psutil.Process()

            for size in self.test_sizes:
                # 记录内存使用
                memory_before = process.memory_info().rss / 1024 / 1024  # MB

                # 执行GPU计算
                test_data = self._generate_price_data(size)
                gpu_rsi = self.gpu_engine.calculate_rsi(test_data.values, 14)

                # 记录内存使用
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = memory_after - memory_before

                results['data_sizes'].append(size)
                results['memory_before'].append(memory_before)
                results['memory_after'].append(memory_after)
                results['memory_usage_mb'].append(memory_usage)

                logger.info(f"Size {size:,}: Memory usage {memory_usage:.2f} MB")

                # 清理GPU内存
                if hasattr(self.gpu_engine.backend, 'clear_cache'):
                    self.gpu_engine.backend.clear_cache()

        except ImportError:
            logger.warning("psutil not available, skipping memory benchmark")
            return None

        return results

    def benchmark_scalability(self) -> Dict[str, Any]:
        """基准测试可扩展性"""
        logger.info("Starting scalability benchmark")

        results = {
            'test_type': 'Scalability',
            'thread_counts': [1, 2, 4, 8, 16],
            'execution_times': [],
            'efficiency': []
        }

        # 使用固定大小的数据
        test_data = self._generate_ohlcv_data(50000)
        param_ranges = {
            'period': list(range(5, 26, 2)),
            'oversold': [20, 25, 30, 35],
            'overbought': [65, 70, 75, 80]
        }

        # 测试不同线程数的性能
        for thread_count in results['thread_counts']:
            logger.info(f"Testing with {thread_count} threads")

            # 更新配置
            config = GPUAccelerationConfig(parallel_workers=thread_count)
            optimizer = get_gpu_optimizer_engine(config)

            start_time = time.time()
            result = optimizer.massive_parameter_optimization_gpu(
                test_data, param_ranges, "RSI_MEAN_REVERSION"
            )
            execution_time = time.time() - start_time

            results['execution_times'].append(execution_time)

            # 计算效率（相对于1个线程）
            if thread_count == 1:
                baseline_time = execution_time
                efficiency = 1.0
            else:
                efficiency = baseline_time / (execution_time * thread_count)

            results['efficiency'].append(efficiency)

            logger.info(f"Threads {thread_count}: {execution_time:.2f}s, Efficiency {efficiency:.2f}")

        return results

    def _generate_price_data(self, size: int) -> pd.Series:
        """生成测试价格数据"""
        np.random.seed(42)  # 确保可重复性

        # 生成模拟价格走势
        returns = np.random.normal(0.001, 0.02, size)
        prices = [100]

        for ret in returns:
            new_price = prices[-1] * (1 + ret)
            prices.append(new_price)

        return pd.Series(prices[1:])

    def _generate_ohlcv_data(self, size: int) -> pd.DataFrame:
        """生成测试OHLCV数据"""
        np.random.seed(42)

        close_prices = self._generate_price_data(size).values

        # 生成OHLC数据
        high_prices = close_prices * (1 + np.abs(np.random.normal(0, 0.01, size)))
        low_prices = close_prices * (1 - np.abs(np.random.normal(0, 0.01, size)))
        open_prices = close_prices * (1 + np.random.normal(0, 0.005, size))
        volume = np.random.uniform(1000, 100000, size)

        return pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume
        })

    def _measure_accuracy(self, gpu_result: np.ndarray, cpu_result: np.ndarray) -> float:
        """测量计算精度（RMSE）"""
        # 确保两个数组长度相同
        min_length = min(len(gpu_result), len(cpu_result))
        gpu_truncated = gpu_result[:min_length]
        cpu_truncated = cpu_result[:min_length]

        # 计算均方根误差
        mse = np.mean((gpu_truncated - cpu_truncated) ** 2)
        rmse = np.sqrt(mse)

        return rmse

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """运行综合基准测试"""
        logger.info("Starting comprehensive GPU performance benchmark")

        # 设置测试环境
        self.setup()

        # 运行各项测试
        benchmark_results = {}

        try:
            benchmark_results['rsi_calculation'] = self.benchmark_rsi_calculation()
            logger.info("RSI calculation benchmark completed")
        except Exception as e:
            logger.error(f"RSI calculation benchmark failed: {e}")

        try:
            benchmark_results['macd_calculation'] = self.benchmark_macd_calculation()
            logger.info("MACD calculation benchmark completed")
        except Exception as e:
            logger.error(f"MACD calculation benchmark failed: {e}")

        try:
            benchmark_results['parameter_optimization'] = self.benchmark_parameter_optimization()
            logger.info("Parameter optimization benchmark completed")
        except Exception as e:
            logger.error(f"Parameter optimization benchmark failed: {e}")

        try:
            memory_results = self.benchmark_memory_usage()
            if memory_results:
                benchmark_results['memory_usage'] = memory_results
                logger.info("Memory usage benchmark completed")
        except Exception as e:
            logger.error(f"Memory usage benchmark failed: {e}")

        try:
            benchmark_results['scalability'] = self.benchmark_scalability()
            logger.info("Scalability benchmark completed")
        except Exception as e:
            logger.error(f"Scalability benchmark failed: {e}")

        # 生成综合报告
        comprehensive_report = self._generate_comprehensive_report(benchmark_results)

        logger.info("Comprehensive GPU performance benchmark completed")
        return comprehensive_report

    def _generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'gpu_backend_info': self.gpu_engine.backend.get_backend_info(),
            'test_results': results,
            'summary': {}
        }

        # 计算性能摘要
        if 'rsi_calculation' in results:
            rsi_results = results['rsi_calculation']
            avg_speedup = np.mean(rsi_results['speedup_ratios'])
            avg_accuracy = np.mean(rsi_results['accuracy_results'])

            report['summary']['rsi_calculation'] = {
                'average_speedup': float(avg_speedup),
                'average_accuracy': float(avg_accuracy),
                'max_speedup': float(max(rsi_results['speedup_ratios'])),
                'best_performance_at_size': int(rsi_results['data_sizes'][np.argmax(rsi_results['speedup_ratios'])])
            }

        if 'macd_calculation' in results:
            macd_results = results['macd_calculation']
            avg_speedup = np.mean(macd_results['speedup_ratios'])

            report['summary']['macd_calculation'] = {
                'average_speedup': float(avg_speedup),
                'max_speedup': float(max(macd_results['speedup_ratios'])),
                'best_performance_at_size': int(macd_results['data_sizes'][np.argmax(macd_results['speedup_ratios'])])
            }

        if 'parameter_optimization' in results:
            opt_results = results['parameter_optimization']
            max_strategies_per_sec = max(opt_results['strategies_per_second'])
            best_sharpe = max(opt_results['best_sharpe_ratios'])

            report['summary']['parameter_optimization'] = {
                'max_strategies_per_second': float(max_strategies_per_sec),
                'best_sharpe_ratio': float(best_sharpe),
                'total_strategies_tested': sum([r['total_combinations_tested'] for r in opt_results['combination_counts']])  # 这个需要修正
            }

        # 总体性能评估
        speedups = []
        if 'rsi_calculation' in results:
            speedups.extend(results['rsi_calculation']['speedup_ratios'])
        if 'macd_calculation' in results:
            speedups.extend(results['macd_calculation']['speedup_ratios'])

        if speedups:
            report['summary']['overall_performance'] = {
                'average_gpu_speedup': float(np.mean(speedups)),
                'max_gpu_speedup': float(max(speedups)),
                'min_gpu_speedup': float(min(speedups)),
                'gpu_acceleration_effective': np.mean(speedups) > 1.0
            }

        return report

    def save_benchmark_results(self, results: Dict[str, Any], filename: str = None):
        """保存基准测试结果"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gpu_performance_benchmark_{timestamp}.json"

        filepath = f"C:/Users/Penguin8n/CODEX--/simplified_system/{filename}"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Benchmark results saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save benchmark results: {e}")
            return None

    def generate_visualization_report(self, results: Dict[str, Any], save_path: str = None):
        """生成可视化报告"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('GPU Performance Benchmark Results', fontsize=16, fontweight='bold')

            # RSI计算性能对比
            if 'rsi_calculation' in results:
                rsi_results = results['rsi_calculation']
                ax1 = axes[0, 0]
                ax1.plot(rsi_results['data_sizes'], rsi_results['cpu_times'], 'o-', label='CPU', linewidth=2)
                ax1.plot(rsi_results['data_sizes'], rsi_results['gpu_times'], 'o-', label='GPU', linewidth=2)
                ax1.set_xlabel('Data Size')
                ax1.set_ylabel('Execution Time (seconds)')
                ax1.set_title('RSI Calculation Performance')
                ax1.legend()
                ax1.grid(True, alpha=0.3)

            # 加速比图表
            if 'rsi_calculation' in results:
                ax2 = axes[0, 1]
                ax2.bar(range(len(rsi_results['speedup_ratios'])), rsi_results['speedup_ratios'])
                ax2.set_xlabel('Data Size Index')
                ax2.set_ylabel('Speedup Ratio (CPU/GPU)')
                ax2.set_title('GPU Speedup Ratio')
                ax2.grid(True, alpha=0.3)

            # 参数优化性能
            if 'parameter_optimization' in results:
                opt_results = results['parameter_optimization']
                ax3 = axes[1, 0]
                x_pos = np.arange(len(opt_results['data_sizes']))
                ax3.bar(x_pos, opt_results['strategies_per_second'])
                ax3.set_xlabel('Optimization Scale')
                ax3.set_ylabel('Strategies per Second')
                ax3.set_title('Parameter Optimization Throughput')
                ax3.set_xticks(x_pos)
                ax3.set_xticklabels(opt_results['data_sizes'], rotation=45, ha='right')
                ax3.grid(True, alpha=0.3)

            # 内存使用情况
            if 'memory_usage' in results:
                mem_results = results['memory_usage']
                ax4 = axes[1, 1]
                ax4.plot(mem_results['data_sizes'], mem_results['memory_usage_mb'], 'o-', color='red', linewidth=2)
                ax4.set_xlabel('Data Size')
                ax4.set_ylabel('Memory Usage (MB)')
                ax4.set_title('GPU Memory Usage')
                ax4.grid(True, alpha=0.3)
            else:
                # 如果没有内存测试结果，显示GPU后端信息
                ax4.text(0.5, 0.5, f"GPU Backend: {results['gpu_backend_info']['backend_type']}\n"
                        f"Version: {results['gpu_backend_info'].get('version', 'Unknown')}\n"
                        f"GPU Available: {results['gpu_backend_info'].get('cuda_available', False)}",
                        ha='center', va='center', fontsize=12, transform=ax4.transAxes)
                ax4.set_title('GPU Backend Information')

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"Visualization saved to {save_path}")

            plt.show()

        except Exception as e:
            logger.error(f"Failed to generate visualization: {e}")

def run_gpu_performance_benchmark():
    """运行GPU性能基准测试的主函数"""
    print("=" * 80)
    print("GPU ACCELERATED QUANTITATIVE TRADING PERFORMANCE BENCHMARK")
    print("=" * 80)

    # 创建基准测试实例
    benchmark = GPUPerformanceBenchmark()

    # 运行综合基准测试
    results = benchmark.run_comprehensive_benchmark()

    # 保存结果
    results_file = benchmark.save_benchmark_results(results)
    if results_file:
        print(f"\n📊 Benchmark results saved to: {results_file}")

    # 生成可视化报告
    viz_file = f"C:/Users/Penguin8n/CODEX--/simplified_system/gpu_performance_chart.png"
    benchmark.generate_visualization_report(results, viz_file)

    # 打印摘要报告
    print("\n" + "=" * 80)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 80)

    gpu_backend = results['gpu_backend_info']
    print(f"\nGPU Backend: {gpu_backend['backend_type']}")
    print(f"GPU Available: {'Yes' if gpu_backend.get('cuda_available', False) else 'No'}")

    if 'summary' in results:
        summary = results['summary']

        if 'overall_performance' in summary:
            overall = summary['overall_performance']
            print(f"\n🚀 Overall GPU Performance:")
            print(f"   Average Speedup: {overall['average_gpu_speedup']:.1f}x")
            print(f"   Maximum Speedup: {overall['max_gpu_speedup']:.1f}x")
            print(f"   GPU Acceleration Effective: {'✅ Yes' if overall['gpu_acceleration_effective'] else '❌ No'}")

        if 'rsi_calculation' in summary:
            rsi = summary['rsi_calculation']
            print(f"\n📈 RSI Calculation Performance:")
            print(f"   Average Speedup: {rsi['average_speedup']:.1f}x")
            print(f"   Calculation Accuracy (RMSE): {rsi['average_accuracy']:.6f}")
            print(f"   Best Performance at {rsi['best_performance_at_size']:,} data points")

        if 'parameter_optimization' in summary:
            opt = summary['parameter_optimization']
            print(f"\n⚡ Parameter Optimization Performance:")
            print(f"   Maximum Throughput: {opt['max_strategies_per_second']:.0f} strategies/second")
            print(f"   Best Sharpe Ratio Found: {opt['best_sharpe_ratio']:.4f}")

    print("\n" + "=" * 80)
    print("GPU ACCELERATION BENCHMARK COMPLETED")
    print("=" * 80)

    return results

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行基准测试
    results = run_gpu_performance_benchmark()