#!/usr / bin / env python3
"""
Simplified System - VectorBT性能基準測試
Enhanced VectorBT Integration Performance Benchmark

測試向量化改進前後的性能差異
"""

import logging
import time
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd

from src.api.stock_api import get_hk_stock_data
from src.backtest.vectorbt_engine import BacktestConfig, VectorBTEngine

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class VectorBTPerformanceBenchmark:
    """VectorBT性能基準測試類"""

    def __init__(self):
        self.engine = VectorBTEngine()
        self.results = {
            "test_time": datetime.now().isoformat(),
            "strategies": {},
            "summary": {},
        }

    def load_test_data(self, symbol: str = "0700.HK", days: int = 365) -> pd.DataFrame:
        """加載測試數據"""
        logger.info(f"Loading {symbol} data for {days} days...")

        try:
            data = get_hk_stock_data(symbol, days)
            df = pd.DataFrame(data)

            # 確保數據格式正確
            if "timestamp" in df.columns:
                df["date"] = pd.to_datetime(df["timestamp"])
                df.set_index("date", inplace = True)

            # 確保必要的列存在
            required_columns = ["open", "high", "low", "close", "volume"]
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    raise ValueError(f"Missing required column: {col}")

            logger.info(f"Loaded {len(df)} records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error loading data: {e}")
            # 創建模擬數據進行測試
            logger.warning("Using simulated data for benchmarking...")
            dates = pd.date_range(start="2023 - 01 - 01", periods = days, freq="D")
            np.random.seed(42)

            # 模擬股價數據
            initial_price = 500.0
            returns = np.random.normal(0.001, 0.02, days)
            prices = [initial_price]

            for ret in returns:
                prices.append(prices[-1] * (1 + ret))

            close_prices = pd.Series(prices[1:], index = dates)

            df = pd.DataFrame(
                {
                    "open": close_prices * (1 + np.random.normal(0, 0.005, days)),
                    "high": close_prices * (1 + abs(np.random.normal(0, 0.01, days))),
                    "low": close_prices * (1 - abs(np.random.normal(0, 0.01, days))),
                    "close": close_prices,
                    "volume": np.random.randint(1000000, 10000000, days),
                }
            )

            return df

    def benchmark_strategy(
        self,
        strategy_name: str,
        parameters: Dict,
        data: pd.DataFrame,
        iterations: int = 10,
    ) -> Dict:
        """基準測試單個策略"""
        logger.info(f"Benchmarking {strategy_name}...")

        execution_times = []

        for i in range(iterations):
            start_time = time.time()

            try:
                result = self.engine.backtest_strategy(
                    data = data,
                    strategy = strategy_name,
                    parameters = parameters,
                    symbol="TEST",
                )
                execution_time = time.time() - start_time
                execution_times.append(execution_time)

            except Exception as e:
                logger.error(f"Error in {strategy_name} iteration {i}: {e}")
                continue

        if execution_times:
            avg_time = np.mean(execution_times)
            min_time = np.min(execution_times)
            max_time = np.max(execution_times)
            std_time = np.std(execution_times)

            # 計算每秒策略數
            strategies_per_second = 1.0 / avg_time

            benchmark_result = {
                "strategy": strategy_name,
                "parameters": parameters,
                "iterations": iterations,
                "execution_times": {
                    "average": round(avg_time, 4),
                    "minimum": round(min_time, 4),
                    "maximum": round(max_time, 4),
                    "std_dev": round(std_time, 4),
                },
                "performance": {
                    "strategies_per_second": round(strategies_per_second, 2),
                    "execution_time_ms": round(avg_time * 1000, 2),
                },
                "success_rate": len(execution_times) / iterations,
            }

            logger.info(f"{strategy_name}: {strategies_per_second:.2f} strategies / sec")
            return benchmark_result
        else:
            return {
                "strategy": strategy_name,
                "error": "All iterations failed",
                "success_rate": 0,
            }

    def run_comprehensive_benchmark(self) -> Dict:
        """運行綜合性能基準測試"""
        logger.info("Starting comprehensive VectorBT performance benchmark...")

        # 加載測試數據
        data = self.load_test_data()

        # 定義測試策略和參數
        test_strategies = [
            ("RSI_MEAN_REVERSION", {"period": 14, "oversold": 30, "overbought": 70}),
            ("MACD_CROSSOVER", {"fast": 12, "slow": 26, "signal": 9}),
            ("BOLLINGER_BANDS", {"period": 20, "std_dev": 2.0}),
            ("DUAL_MOVING_AVERAGE", {"short_period": 20, "long_period": 50}),
            ("MOMENTUM_BREAKOUT", {"lookback": 20, "threshold": 0.02}),
            ("VOLATILITY_BREAKOUT", {"atr_period": 14, "multiplier": 2.0}),
        ]

        # 運行每個策略的基準測試
        for strategy_name, parameters in test_strategies:
            result = self.benchmark_strategy(
                strategy_name, parameters, data, iterations = 20
            )
            self.results["strategies"][strategy_name] = result

        # 計算整體性能統計
        successful_strategies = [
            r for r in self.results["strategies"].values() if "performance" in r
        ]

        if successful_strategies:
            avg_strategies_per_sec = np.mean(
                [
                    r["performance"]["strategies_per_second"]
                    for r in successful_strategies
                ]
            )
            total_time = np.sum(
                [
                    r["execution_times"]["average"] * r["iterations"]
                    for r in successful_strategies
                ]
            )

            self.results["summary"] = {
                "total_strategies_tested": len(test_strategies),
                "successful_strategies": len(successful_strategies),
                "average_strategies_per_second": round(avg_strategies_per_sec, 2),
                "total_execution_time": round(total_time, 4),
                "target_performance": 600.0,  # 目標：600策略 / 秒
                "performance_target_met": avg_strategies_per_sec >= 600.0,
                "performance_improvement_needed": max(
                    0, 600.0 - avg_strategies_per_sec
                ),
            }

        return self.results

    def generate_report(self) -> str:
        """生成性能報告"""
        report = []
        report.append("=" * 60)
        report.append("VectorBT Performance Benchmark Report")
        report.append("=" * 60)
        report.append(f"Test Date: {self.results['test_time']}")
        report.append("")

        # 整體性能摘要
        if "summary" in self.results:
            summary = self.results["summary"]
            report.append("Overall Performance Summary:")
            report.append(f"  Strategies Tested: {summary['total_strategies_tested']}")
            report.append(
                f"  Successful Strategies: {summary['successful_strategies']}"
            )
            report.append(
                f"  Average Performance: {summary['average_strategies_per_second']:.2f} strategies / sec"
            )
            report.append(
                f"  Target Performance: {summary['target_performance']:.2f} strategies / sec"
            )
            report.append(
                f"  Target Met: {'YES' if summary['performance_target_met'] else 'NO'}"
            )

            if not summary["performance_target_met"]:
                report.append(
                    f"  Improvement Needed: {summary['performance_improvement_needed']:.2f} strategies / sec"
                )
            report.append("")

        # 詳細策略性能
        report.append("Detailed Strategy Performance:")
        report.append("-" * 40)

        for strategy_name, result in self.results["strategies"].items():
            report.append(f"\n{strategy_name}:")
            if "performance" in result:
                perf = result["performance"]
                exec_time = result["execution_times"]
                report.append(
                    f"  Performance: {perf['strategies_per_second']:.2f} strategies / sec"
                )
                report.append(
                    f"  Avg Time: {exec_time['average']:.4f}s ({perf['execution_time_ms']:.2f}ms)"
                )
                report.append(f"  Success Rate: {result['success_rate']*100:.1f}%")
                report.append(
                    f"  Time Range: {exec_time['minimum']:.4f}s - {exec_time['maximum']:.4f}s"
                )
            else:
                report.append(
                    f"  Status: FAILED - {result.get('error', 'Unknown error')}"
                )

        report.append("")
        report.append("=" * 60)
        report.append("End of Report")
        report.append("=" * 60)

        return "\n".join(report)


def main():
    """主測試函數"""
    benchmark = VectorBTPerformanceBenchmark()

    try:
        results = benchmark.run_comprehensive_benchmark()
        report = benchmark.generate_report()

        print(report)

        # 保存結果到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vectorbt_benchmark_report_{timestamp}.txt"

        with open(filename, "w", encoding="utf - 8") as f:
            f.write(report)

        logger.info(f"Benchmark report saved to: {filename}")

        return results

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    main()
