#!/usr / bin / env python3
"""
Phase 3 性能优化测试系统
Phase 3 Performance Optimization Test System

测试和验证所有性能优化功能
"""

import json
import logging
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

# 添加路径
sys.path.append(os.path.dirname(__file__))

from src.api.stock_api import get_hk_stock_data
from src.backtest.vectorbt_engine import VectorBTEngine
from src.indicators.core_indicators import CoreIndicators
from src.performance.gpu_manager import get_gpu_manager
from src.performance.high_performance_cache import global_cache
from src.performance.parallel_optimizer import global_parallel_optimizer
from src.performance.performance_monitor import (
    get_performance_monitor,
    start_global_monitoring,
    stop_global_monitoring,
)

# 配置日志
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceTestSuite:
    """性能测试套件"""

    def __init__(self):
        self.test_results = {}
        self.performance_monitor = get_performance_monitor()
        self.baseline_metrics = {}

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        logger.info("开始Phase 3性能优化测试")
        logger.info("Starting Phase 3 Performance Optimization Tests")

        # 启动性能监控
        start_global_monitoring()

        try:
            # 1. 缓存系统测试
            self.test_cache_performance()

            # 2. 并行计算测试
            self.test_parallel_computation()

            # 3. GPU加速测试
            self.test_gpu_acceleration()

            # 4. VectorBT引擎优化测试
            self.test_vectorbt_optimization()

            # 5. 技术指标计算优化测试
            self.test_indicator_optimization()

            # 6. 综合性能测试
            self.test_comprehensive_performance()

            # 生成测试报告
            report = self.generate_test_report()

            logger.info("Phase 3性能优化测试完成")
            logger.info("Phase 3 Performance Optimization Tests Completed")

            return report

        finally:
            # 停止性能监控
            stop_global_monitoring()

    def test_cache_performance(self):
        """测试缓存性能"""
        logger.info("测试缓存系统性能...")

        # 创建测试数据
        test_data = pd.DataFrame(
            {
                "close": np.random.randn(1000).cumsum() + 100,
                "open": np.random.randn(1000).cumsum() + 100,
                "high": np.random.randn(1000).cumsum() + 105,
                "low": np.random.randn(1000).cumsum() + 95,
                "volume": np.random.randint(1000000, 5000000, 1000),
            }
        )

        indicators = CoreIndicators()

        # 测试1: 无缓存性能
        start_time = time.time()
        for _ in range(100):
            rsi = indicators.calculate_rsi(test_data["close"], 14)
            sma = indicators.calculate_sma(test_data["close"], 20)
            macd = indicators.calculate_macd(test_data["close"])
        no_cache_time = time.time() - start_time

        # 清空缓存
        global_cache.clear_all()

        # 测试2: 有缓存性能
        start_time = time.time()
        for _ in range(100):
            cache_key = global_cache.generate_cache_key(
                test_data, "rsi_test", {"period": 14}
            )
            cached_rsi = global_cache.get(cache_key)
            if cached_rsi is None:
                rsi = indicators.calculate_rsi(test_data["close"], 14)
                global_cache.put(cache_key, rsi)

            cache_key = global_cache.generate_cache_key(
                test_data, "sma_test", {"period": 20}
            )
            cached_sma = global_cache.get(cache_key)
            if cached_sma is None:
                sma = indicators.calculate_sma(test_data["close"], 20)
                global_cache.put(cache_key, sma)

            cache_key = global_cache.generate_cache_key(
                test_data, "macd_test", {"fast": 12, "slow": 26}
            )
            cached_macd = global_cache.get(cache_key)
            if cached_macd is None:
                macd = indicators.calculate_macd(test_data["close"])
                global_cache.put(cache_key, macd)

        with_cache_time = time.time() - start_time

        # 计算性能提升
        speedup = no_cache_time / with_cache_time
        cache_stats = global_cache.get_comprehensive_stats()

        self.test_results["cache_performance"] = {
            "no_cache_time": no_cache_time,
            "with_cache_time": with_cache_time,
            "speedup": speedup,
            "cache_hit_rate": cache_stats["overall_stats"]["hit_rate"],
            "total_cache_requests": cache_stats["overall_stats"]["total_requests"],
        }

        # 记录到性能监控器
        self.performance_monitor.set_baseline("indicators_no_cache", no_cache_time)
        self.performance_monitor.record_operation_time(
            "indicators_with_cache", with_cache_time
        )

        logger.info(
            f"缓存性能测试完成: 加速 {speedup:.2f}x, 命中率 {cache_stats['overall_stats']['hit_rate']:.1%}"
        )

    def test_parallel_computation(self):
        """测试并行计算性能"""
        logger.info("测试并行计算性能...")

        # 生成大量参数组合
        param_combinations = []
        for period in range(10, 31, 5):
            for oversold in [20, 25, 30]:
                for overbought in [70, 75, 80]:
                    param_combinations.append(
                        {
                            "period": period,
                            "oversold": oversold,
                            "overbought": overbought,
                        }
                    )

        # 创建测试数据
        test_data = pd.DataFrame(
            {
                "close": np.random.randn(500).cumsum() + 100,
                "open": np.random.randn(500).cumsum() + 100,
                "high": np.random.randn(500).cumsum() + 105,
                "low": np.random.randn(500).cumsum() + 95,
                "volume": np.random.randint(1000000, 5000000, 500),
            }
        )

        engine = VectorBTEngine()

        def evaluate_rsi_params(params):
            """评估RSI参数"""
            try:
                result = engine.backtest_strategy(
                    test_data, "RSI_MEAN_REVERSION", params, "TEST"
                )
                return {
                    "parameters": params,
                    "sharpe_ratio": result.sharpe_ratio,
                    "total_return": result.total_return,
                    "max_drawdown": result.max_drawdown,
                }
            except Exception:
                return {
                    "parameters": params,
                    "sharpe_ratio": 0.0,
                    "total_return": 0.0,
                    "max_drawdown": 0.05,
                }

        # 测试1: 串行执行
        start_time = time.time()
        serial_results = []
        for params in param_combinations[:20]:  # 限制数量以节省时间
            result = evaluate_rsi_params(params)
            serial_results.append(result)
        serial_time = time.time() - start_time

        # 测试2: 并行执行
        start_time = time.time()
        parallel_results = global_parallel_optimizer.parallel_execute(
            evaluate_rsi_params, param_combinations[:20]
        )
        parallel_time = time.time() - start_time

        # 计算性能提升
        speedup = serial_time / parallel_time
        parallel_stats = global_parallel_optimizer.get_performance_stats()

        self.test_results["parallel_computation"] = {
            "serial_time": serial_time,
            "parallel_time": parallel_time,
            "speedup": speedup,
            "total_tasks": len(param_combinations[:20]),
            "optimal_workers": parallel_stats["worker_configuration"][
                "optimal_workers"
            ],
            "success_rate": parallel_stats["task_statistics"]["success_rate"],
        }

        # 记录到性能监控器
        self.performance_monitor.set_baseline("rsi_optimization_serial", serial_time)
        self.performance_monitor.record_operation_time(
            "rsi_optimization_parallel", parallel_time
        )

        logger.info(
            f"并行计算测试完成: 加速 {speedup:.2f}x, 使用 {parallel_stats['worker_configuration']['optimal_workers']} 个工作线程"
        )

    def test_gpu_acceleration(self):
        """测试GPU加速性能"""
        logger.info("测试GPU加速性能...")

        gpu_manager = get_gpu_manager()

        # 创建测试数据
        prices = np.random.randn(10000).cumsum() + 100

        indicators_config = {
            "rsi": {"period": 14},
            "macd": {"fast": 12, "slow": 26, "signal": 9},
        }

        # 测试CPU性能
        start_time = time.time()
        for _ in range(50):
            cpu_backend = gpu_manager.backend
            cpu_backend.compute_indicators(prices, indicators_config)
        cpu_time = time.time() - start_time

        # 测试GPU性能（如果可用）
        gpu_time = None
        speedup = None

        if gpu_manager.is_gpu_available():
            start_time = time.time()
            for _ in range(50):
                gpu_manager.compute_indicators(prices, indicators_config)
            gpu_time = time.time() - start_time
            speedup = cpu_time / gpu_time

        backend_info = gpu_manager.get_backend_info()

        self.test_results["gpu_acceleration"] = {
            "cpu_time": cpu_time,
            "gpu_time": gpu_time,
            "speedup": speedup,
            "gpu_available": gpu_manager.is_gpu_available(),
            "backend_type": backend_info.get("backend_type", "Unknown"),
        }

        if gpu_time:
            self.performance_monitor.set_baseline("indicators_cpu", cpu_time)
            self.performance_monitor.record_operation_time("indicators_gpu", gpu_time)

        if speedup:
            logger.info(f"GPU加速测试完成: 加速 {speedup:.2f}x")
        else:
            logger.info("GPU不可用，使用CPU计算")

    def test_vectorbt_optimization(self):
        """测试VectorBT引擎优化"""
        logger.info("测试VectorBT引擎优化...")

        try:
            # 获取真实数据
            data = get_hk_stock_data("0700.HK", 252)
            if data.empty:
                # 使用模拟数据
                data = pd.DataFrame(
                    {
                        "close": np.random.randn(252).cumsum() + 100,
                        "open": np.random.randn(252).cumsum() + 100,
                        "high": np.random.randn(252).cumsum() + 105,
                        "low": np.random.randn(252).cumsum() + 95,
                        "volume": np.random.randint(1000000, 5000000, 252),
                    }
                )

            engine = VectorBTEngine()

            # 测试参数优化
            param_ranges = {
                "period": range(10, 21, 5),
                "oversold": [25, 30],
                "overbought": [70, 75],
            }

            start_time = time.time()
            optimization_result = engine.optimize_parameters(
                data = data,
                strategy="RSI_MEAN_REVERSION",
                param_ranges = param_ranges,
                symbol="0700.HK",
                optimization_metric="sharpe_ratio",
                use_vectorbt_opt = False,  # 使用手动优化以测试优化
            )
            optimization_time = time.time() - start_time

            self.test_results["vectorbt_optimization"] = {
                "optimization_time": optimization_time,
                "total_combinations": optimization_result.get("total_combinations", 0),
                "successful_combinations": optimization_result.get(
                    "successful_combinations", 0
                ),
                "best_sharpe": optimization_result.get("best_performance", {}).get(
                    "sharpe_ratio", 0
                ),
                "combinations_per_second": (
                    optimization_result.get("total_combinations", 0) / optimization_time
                    if optimization_time > 0
                    else 0
                ),
            }

            self.performance_monitor.record_operation_time(
                "vectorbt_optimization", optimization_time
            )

            logger.info(
                f"VectorBT优化测试完成: {optimization_result.get('total_combinations', 0)} 个组合, {optimization_time:.2f}秒"
            )

        except Exception as e:
            logger.error(f"VectorBT优化测试失败: {e}")
            self.test_results["vectorbt_optimization"] = {
                "error": str(e),
                "optimization_time": None,
            }

    def test_indicator_optimization(self):
        """测试技术指标计算优化"""
        logger.info("测试技术指标计算优化...")

        # 创建测试数据
        test_data = pd.DataFrame(
            {
                "close": np.random.randn(5000).cumsum() + 100,
                "open": np.random.randn(5000).cumsum() + 100,
                "high": np.random.randn(5000).cumsum() + 105,
                "low": np.random.randn(5000).cumsum() + 95,
                "volume": np.random.randint(1000000, 5000000, 5000),
            }
        )

        indicators = CoreIndicators()

        # 测试单个指标计算
        start_time = time.time()
        for _ in range(100):
            indicators.calculate_rsi(test_data["close"], 14)
        rsi_time = time.time() - start_time

        start_time = time.time()
        for _ in range(100):
            indicators.calculate_macd(test_data["close"])
        macd_time = time.time() - start_time

        # 测试批量指标计算
        start_time = time.time()
        for _ in range(100):
            all_indicators = indicators.calculate_all_indicators(
                test_data, ["RSI", "MACD", "SMA", "BOLLINGER"]
            )
        batch_time = time.time() - start_time

        self.test_results["indicator_optimization"] = {
            "rsi_time": rsi_time,
            "macd_time": macd_time,
            "batch_time": batch_time,
            "rsi_per_second": 100 / rsi_time,
            "macd_per_second": 100 / macd_time,
            "batch_per_second": 100 / batch_time,
        }

        self.performance_monitor.record_operation_time("rsi_calculation", rsi_time)
        self.performance_monitor.record_operation_time("macd_calculation", macd_time)
        self.performance_monitor.record_operation_time("batch_indicators", batch_time)

        logger.info(
            f"技术指标优化测试完成: RSI {100 / rsi_time:.1f} 次 / 秒, MACD {100 / macd_time:.1f} 次 / 秒"
        )

    def test_comprehensive_performance(self):
        """综合性能测试"""
        logger.info("运行综合性能测试...")

        try:
            # 获取真实数据
            data = get_hk_stock_data("0700.HK", 504)  # 2年数据
            if data.empty:
                data = pd.DataFrame(
                    {
                        "close": np.random.randn(504).cumsum() + 100,
                        "open": np.random.randn(504).cumsum() + 100,
                        "high": np.random.randn(504).cumsum() + 105,
                        "low": np.random.randn(504).cumsum() + 95,
                        "volume": np.random.randint(1000000, 5000000, 504),
                    }
                )

            engine = VectorBTEngine()

            # 定义测试策略
            strategies = [
                (
                    "RSI_MEAN_REVERSION",
                    {"period": 14, "oversold": 30, "overbought": 70},
                ),
                ("MACD_CROSSOVER", {"fast": 12, "slow": 26, "signal": 9}),
                ("DUAL_MOVING_AVERAGE", {"short_period": 20, "long_period": 50}),
                ("BOLLINGER_BANDS", {"period": 20, "std_dev": 2.0}),
            ]

            # 运行所有策略
            start_time = time.time()
            strategy_results = []
            for strategy_name, params in strategies:
                try:
                    result = engine.backtest_strategy(
                        data, strategy_name, params, "0700.HK"
                    )
                    strategy_results.append(
                        {
                            "strategy": strategy_name,
                            "sharpe_ratio": result.sharpe_ratio,
                            "total_return": result.total_return,
                            "max_drawdown": result.max_drawdown,
                            "execution_time": result.execution_time,
                        }
                    )
                except Exception as e:
                    logger.warning(f"策略 {strategy_name} 测试失败: {e}")

            total_time = time.time() - start_time

            # 获取性能监控摘要
            performance_summary = self.performance_monitor.get_performance_summary()

            self.test_results["comprehensive_performance"] = {
                "total_strategies": len(strategies),
                "successful_strategies": len(strategy_results),
                "total_time": total_time,
                "average_time_per_strategy": total_time / len(strategies),
                "strategies_per_second": len(strategies) / total_time,
                "strategy_results": strategy_results,
                "performance_summary": performance_summary,
            }

            logger.info(
                f"综合性能测试完成: {len(strategy_results)}/{len(strategies)} 策略成功, {total_time:.2f}秒"
            )

        except Exception as e:
            logger.error(f"综合性能测试失败: {e}")
            self.test_results["comprehensive_performance"] = {"error": str(e)}

    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 性能改进总结
        cache_speedup = self.test_results.get("cache_performance", {}).get(
            "speedup", 1.0
        )
        parallel_speedup = self.test_results.get("parallel_computation", {}).get(
            "speedup", 1.0
        )
        gpu_speedup = self.test_results.get("gpu_acceleration", {}).get("speedup", 1.0)

        # 目标达成情况
        cache_target_met = cache_speedup >= 2.0  # 目标: 2倍性能提升
        parallel_target_met = (
            self.test_results.get("parallel_computation", {}).get("optimal_workers", 1)
            >= 4
        )  # 目标: 4 + 工作线程
        gpu_available = self.test_results.get("gpu_acceleration", {}).get(
            "gpu_available", False
        )

        # 综合性能评估
        total_optimizations = 3  # 缓存、并行、GPU
        successful_optimizations = sum(
            [
                1 if cache_target_met else 0,
                1 if parallel_target_met else 0,
                1 if gpu_available else 0,
            ]
        )

        performance_grade = (
            "A"
            if successful_optimizations >= 3
            else "B" if successful_optimizations >= 2 else "C"
        )

        report = {
            "test_timestamp": timestamp,
            "performance_grade": performance_grade,
            "optimization_summary": {
                "cache_speedup": cache_speedup,
                "parallel_speedup": parallel_speedup,
                "gpu_speedup": gpu_speedup,
                "cache_target_met": cache_target_met,
                "parallel_target_met": parallel_target_met,
                "gpu_available": gpu_available,
            },
            "detailed_results": self.test_results,
            "performance_monitor_summary": self.performance_monitor.get_performance_summary(),
            "recommendations": self._generate_recommendations(),
        }

        # 保存报告
        report_file = f"performance_test_report_{timestamp}.json"
        with open(report_file, "w", encoding="utf - 8") as f:
            json.dump(report, f, indent = 2, ensure_ascii = False, default = str)

        # 生成文本报告
        text_report = self._generate_text_report(report)
        text_report_file = f"performance_test_report_{timestamp}.txt"
        with open(text_report_file, "w", encoding="utf - 8") as f:
            f.write(text_report)

        logger.info(f"性能测试报告已保存: {report_file}, {text_report_file}")

        return report

    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []

        cache_speedup = self.test_results.get("cache_performance", {}).get(
            "speedup", 1.0
        )
        if cache_speedup < 2.0:
            recommendations.append("建议增加缓存大小或优化缓存策略")

        parallel_speedup = self.test_results.get("parallel_computation", {}).get(
            "speedup", 1.0
        )
        if parallel_speedup < 2.0:
            recommendations.append("建议增加并行工作线程数或优化任务分配")

        gpu_available = self.test_results.get("gpu_acceleration", {}).get(
            "gpu_available", False
        )
        if not gpu_available:
            recommendations.append("建议安装GPU驱动和相关库以启用GPU加速")

        cache_hit_rate = self.test_results.get("cache_performance", {}).get(
            "cache_hit_rate", 0
        )
        if cache_hit_rate < 0.8:
            recommendations.append("缓存命中率较低，建议调整缓存策略")

        return recommendations

    def _generate_text_report(self, report: Dict[str, Any]) -> str:
        """生成文本格式报告"""
        lines = [
            "=" * 80,
            "Phase 3 性能优化测试报告",
            "Phase 3 Performance Optimization Test Report",
            "=" * 80,
            f"测试时间: {report['test_timestamp']}",
            f"性能评级: {report['performance_grade']}",
            "",
            "优化成果总结",
            "-" * 40,
            f"缓存加速: {report['optimization_summary']['cache_speedup']:.2f}x",
            f"并行加速: {report['optimization_summary']['parallel_speedup']:.2f}x",
            f"GPU可用性: {'是' if report['optimization_summary']['gpu_available'] else '否'}",
            "",
            "目标达成情况",
            "-" * 40,
            f"缓存目标 (2x+): {'✅ 达成' if report['optimization_summary']['cache_target_met'] else '❌ 未达成'}",
            f"并行目标 (4+ 线程): {'✅ 达成' if report['optimization_summary']['parallel_target_met'] else '❌ 未达成'}",
            f"GPU加速: {'✅ 可用' if report['optimization_summary']['gpu_available'] else '❌ 不可用'}",
            "",
        ]

        # 详细结果
        if "cache_performance" in report["detailed_results"]:
            cache = report["detailed_results"]["cache_performance"]
            lines.extend(
                [
                    "缓存性能详情",
                    "-" * 40,
                    f"无缓存时间: {cache['no_cache_time']:.3f}s",
                    f"有缓存时间: {cache['with_cache_time']:.3f}s",
                    f"缓存命中率: {cache['cache_hit_rate']:.1%}",
                    f"总请求数: {cache['total_cache_requests']}",
                    "",
                ]
            )

        if "parallel_computation" in report["detailed_results"]:
            parallel = report["detailed_results"]["parallel_computation"]
            lines.extend(
                [
                    "并行计算详情",
                    "-" * 40,
                    f"串行时间: {parallel['serial_time']:.3f}s",
                    f"并行时间: {parallel['parallel_time']:.3f}s",
                    f"最优工作线程: {parallel['optimal_workers']}",
                    f"任务成功率: {parallel['success_rate']:.1%}",
                    "",
                ]
            )

        # 建议
        if report["recommendations"]:
            lines.extend(["优化建议", "-" * 40])
            lines.extend([f"- {rec}" for rec in report["recommendations"]])

        lines.extend(
            [
                "",
                "=" * 80,
            ]
        )

        return "\n".join(lines)


def main():
    """主函数"""
    print("启动Phase 3性能优化测试系统...")
    print("Starting Phase 3 Performance Optimization Test System...")

    test_suite = PerformanceTestSuite()
    report = test_suite.run_all_tests()

    print("\n" + "=" * 80)
    print("测试完成!")
    print("Test Completed!")
    print("=" * 80)

    # 显示关键结果
    summary = report["optimization_summary"]
    print(f"性能评级: {report['performance_grade']}")
    print(f"缓存加速: {summary['cache_speedup']:.2f}x")
    print(f"并行加速: {summary['parallel_speedup']:.2f}x")
    print(f"GPU加速: {'可用' if summary['gpu_available'] else '不可用'}")

    if report["recommendations"]:
        print("\n优化建议:")
        for rec in report["recommendations"]:
            print(f"- {rec}")

    return report


if __name__ == "__main__":
    main()
