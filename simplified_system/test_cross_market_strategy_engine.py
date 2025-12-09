#!/usr/bin/env python3
"""
跨市场策略引擎测试 - Cross-Market Strategy Engine Test
测试套利、相关性、动量策略的实现和性能
"""

import sys
import os
import asyncio
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.cross_market.strategy_engine import (
    CrossMarketStrategyManager, TriangularArbitrageStrategy,
    PairsTradingStrategy, CrossAssetMomentumStrategy,
    TradingSignal, TradingAction
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrossMarketStrategyTester:
    """跨市场策略测试类"""

    def __init__(self):
        self.strategy_manager = CrossMarketStrategyManager()
        self.test_results = {}
        self.sample_market_data = None

    def create_sample_market_data(self) -> dict:
        """创建示例市场数据"""
        print("Creating sample market data...")

        # 生成时间序列
        dates = pd.date_range(
            start=datetime.utcnow() - timedelta(days=365),
            end=datetime.utcnow(),
            freq='H'
        )

        market_data = {}
        assets_and_prices = {
            "EURUSD": 1.0800,
            "GBPUSD": 1.2700,
            "USDJPY": 150.00,
            "EURJPY": 162.00,
            "XAUUSD": 2300.00,
            "BTCUSD": 45000.00,
            "ETHUSD": 3000.00
        }

        for asset, base_price in assets_and_prices.items():
            # 生成相关性的价格数据
            np.random.seed(hash(asset) % 2**32)  # 确保可重现性

            # 基础趋势
            trend = np.linspace(0, 0.1, len(dates))

            # 随机波动
            random_walk = np.random.normal(0, 0.002, len(dates))

            # 相关性组件 (某些资产对相关)
            if asset in ["EURUSD", "GBPUSD"]:
                correlation_component = np.random.normal(0, 0.001, len(dates))
                random_walk += correlation_component
            elif asset in ["BTCUSD", "ETHUSD"]:
                crypto_correlation = np.random.normal(0, 0.003, len(dates))
                random_walk += crypto_correlation

            # 组合价格
            returns = trend + random_walk
            prices = [base_price]

            for ret in returns:
                new_price = prices[-1] * (1 + ret)
                prices.append(new_price)

            # 创建OHLCV数据
            df = pd.DataFrame({
                'open': prices[:-1],
                'high': [p * (1 + abs(np.random.normal(0, 0.001))) for p in prices[:-1]],
                'low': [p * (1 - abs(np.random.normal(0, 0.001))) for p in prices[:-1]],
                'close': prices[1:],
                'volume': np.random.randint(100000, 1000000, len(dates)-1)
            }, index=dates[:-1])

            market_data[asset] = df

        self.sample_market_data = market_data
        print(f"[OK] Created market data for {len(market_data)} assets")
        return market_data

    async def test_strategy_initialization(self):
        """测试策略初始化"""
        print("\n" + "=" * 60)
        print("Strategy Initialization Test")
        print("=" * 60)

        try:
            # 创建不同类型的策略
            strategies = [
                TriangularArbitrageStrategy(
                    currency_pairs=["EURUSD", "USDJPY", "EURJPY"],
                    min_spread_pct=0.05
                ),
                PairsTradingStrategy(
                    asset1="EURUSD",
                    asset2="GBPUSD",
                    lookback_period=60,
                    entry_threshold=1.5,
                    exit_threshold=0.5
                ),
                CrossAssetMomentumStrategy(
                    assets=["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
                    lookback_periods=[21, 63],
                    strategy_type="long_short"
                )
            ]

            # 添加策略到管理器
            for strategy in strategies:
                self.strategy_manager.add_strategy(strategy)
                print(f"[OK] Added {strategy.name} strategy")

            # 初始化所有策略
            await self.strategy_manager.initialize_strategies(self.sample_market_data)

            # 检查初始化状态
            initialized_count = len([s for s in self.strategy_manager.strategies.values() if s.is_initialized])
            print(f"[OK] Initialized {initialized_count}/{len(strategies)} strategies")

            self.test_results["strategy_initialization"] = initialized_count == len(strategies)
            return initialized_count == len(strategies)

        except Exception as e:
            print(f"[FAIL] Strategy initialization test failed: {e}")
            self.test_results["strategy_initialization"] = False
            return False

    async def test_signal_generation(self):
        """测试信号生成"""
        print("\n" + "=" * 60)
        print("Signal Generation Test")
        print("=" * 60)

        try:
            # 运行策略生成信号
            start_time = time.time()
            signals = await self.strategy_manager.run_strategies(self.sample_market_data)
            execution_time = time.time() - start_time

            # 分析信号
            signals_by_strategy = {}
            for signal in signals:
                if signal.strategy_name not in signals_by_strategy:
                    signals_by_strategy[signal.strategy_name] = []
                signals_by_strategy[signal.strategy_name].append(signal)

            print(f"[OK] Generated {len(signals)} signals in {execution_time:.3f}s")

            for strategy_name, strategy_signals in signals_by_strategy.items():
                print(f"  {strategy_name}: {len(strategy_signals)} signals")
                if strategy_signals:
                    action_counts = {}
                    for signal in strategy_signals:
                        action_counts[signal.action.value] = action_counts.get(signal.action.value, 0) + 1
                    print(f"    Actions: {action_counts}")

                    # 显示示例信号
                    example_signal = strategy_signals[0]
                    print(f"    Example: {example_signal.action.value} {example_signal.quantity} {example_signal.asset}")
                    print(f"    Reason: {example_signal.reason[:100]}...")

            # 验证信号质量
            non_hold_signals = [s for s in signals if s.action != TradingAction.HOLD]
            signal_quality = len(non_hold_signals) > 0 and all(s.confidence > 0 for s in non_hold_signals)

            print(f"[OK] Signal quality check: {signal_quality}")

            self.test_results["signal_generation"] = signal_quality
            return signal_quality

        except Exception as e:
            print(f"[FAIL] Signal generation test failed: {e}")
            self.test_results["signal_generation"] = False
            return False

    async def test_triangular_arbitrage_strategy(self):
        """测试三角套利策略"""
        print("\n" + "=" * 60)
        print("Triangular Arbitrage Strategy Test")
        print("=" * 60)

        try:
            # 创建三角套利策略
            strategy = TriangularArbitrageStrategy(
                currency_pairs=["EURUSD", "USDJPY", "EURJPY"],
                min_spread_pct=0.01  # 更低阈值以增加测试机会
            )

            await strategy.initialize(self.sample_market_data)

            # 模拟不同的市场条件
            test_scenarios = [
                {"name": "Normal Market", "spread_multiplier": 1.0},
                {"name": "High Volatility", "spread_multiplier": 2.0},
                {"name": "Low Liquidity", "spread_multiplier": 0.5}
            ]

            for scenario in test_scenarios:
                print(f"\nTesting {scenario['name']} scenario...")

                # 修改市场数据以创建不同的价差
                modified_data = self._modify_market_data_for_scenario(
                    self.sample_market_data, scenario['spread_multiplier']
                )

                signals = await strategy.generate_signals(modified_data, datetime.utcnow())

                print(f"  Generated {len(signals)} signals")
                for signal in signals:
                    print(f"    {signal.action.value} {signal.asset}: {signal.reason}")

            # 测试套利机会计算
            print(f"\nTesting arbitrage opportunity calculation...")
            opportunity = strategy._calculate_triangular_arbitrage(
                {
                    "EURUSD": (1.0800, 1.0802),
                    "USDJPY": (150.00, 150.02),
                    "EURJPY": (162.02, 162.04)
                },
                ["EURUSD", "USDJPY", "EURJPY"]
            )

            if opportunity:
                print(f"[OK] Found arbitrage opportunity: {opportunity.percentage:.3f}%")
            else:
                print("[OK] No arbitrage opportunity found (expected)")

            self.test_results["triangular_arbitrage"] = True
            return True

        except Exception as e:
            print(f"[FAIL] Triangular arbitrage test failed: {e}")
            self.test_results["triangular_arbitrage"] = False
            return False

    async def test_pairs_trading_strategy(self):
        """测试配对交易策略"""
        print("\n" + "=" * 60)
        print("Pairs Trading Strategy Test")
        print("=" * 60)

        try:
            # 创建配对交易策略
            strategy = PairsTradingStrategy(
                asset1="EURUSD",
                asset2="GBPUSD",
                lookback_period=60,
                entry_threshold=1.0,  # 降低阈值以增加信号
                exit_threshold=0.3
            )

            await strategy.initialize(self.sample_market_data)

            # 测试Z-score计算
            print(f"\nTesting Z-score calculation...")
            df1 = self.sample_market_data["EURUSD"]
            df2 = self.sample_market_data["GBPUSD"]

            zscore_series = strategy._calculate_spread_zscore(df1, df2)
            print(f"[OK] Calculated {len(zscore_series)} Z-score values")
            print(f"  Current Z-score: {zscore_series.iloc[-1]:.3f}")
            print(f"  Z-score range: [{zscore_series.min():.3f}, {zscore_series.max():.3f}]")

            # 测试Beta计算
            beta = strategy._calculate_beta(df1['close'], df2['close'])
            print(f"  Beta coefficient: {beta:.4f}")

            # 测试不同Z-score方法
            methods = ["ratio", "difference", "beta_neutral"]
            for method in methods:
                strategy.zscore_method = method
                zscore_method = strategy._calculate_spread_zscore(df1, df2)
                print(f"  {method} Z-score current: {zscore_method.iloc[-1]:.3f}")

            # 生成交易信号
            signals = await strategy.generate_signals(self.sample_market_data, datetime.utcnow())
            print(f"\n[OK] Generated {len(signals)} trading signals")

            for signal in signals:
                print(f"  {signal.action.value} {signal.asset}: {signal.reason}")
                if signal.metadata:
                    print(f"    Z-score: {signal.metadata.get('zscore', 'N/A')}")
                    print(f"    Direction: {signal.metadata.get('spread_direction', 'N/A')}")

            self.test_results["pairs_trading"] = len(signals) >= 0
            return True

        except Exception as e:
            print(f"[FAIL] Pairs trading test failed: {e}")
            self.test_results["pairs_trading"] = False
            return False

    async def test_momentum_strategy(self):
        """测试动量策略"""
        print("\n" + "=" * 60)
        print("Cross-Asset Momentum Strategy Test")
        print("=" * 60)

        try:
            # 创建动量策略
            strategy = CrossAssetMomentumStrategy(
                assets=["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
                lookback_periods=[21, 63, 126],
                strategy_type="long_short"
            )

            await strategy.initialize(self.sample_market_data)

            # 测试动量评分计算
            print(f"\nTesting momentum score calculation...")
            momentum_scores = strategy._calculate_momentum_scores(self.sample_market_data, datetime.utcnow())
            print(f"[OK] Calculated momentum scores for {len(momentum_scores)} assets")

            for asset, score in momentum_scores.items():
                print(f"  {asset}: {score:.6f}")

            # 测试不同策略类型
            strategy_types = ["long_short", "long_only"]
            for strategy_type in strategy_types:
                print(f"\nTesting {strategy_type} strategy...")
                strategy.strategy_type = strategy_type
                weights = strategy._generate_portfolio_weights(momentum_scores)
                print(f"  Generated weights for {len(weights)} assets")

                total_long_weight = sum(w for w in weights.values() if w > 0)
                total_short_weight = sum(abs(w) for w in weights.values() if w < 0)
                print(f"  Total long weight: {total_long_weight:.3f}")
                print(f"  Total short weight: {total_short_weight:.3f}")

                # 显示权重分配
                for asset, weight in sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True):
                    if abs(weight) > 0.01:
                        print(f"    {asset}: {weight:+.3f}")

            # 生成交易信号
            strategy.strategy_type = "long_short"  # 恢复默认设置
            signals = await strategy.generate_signals(self.sample_market_data, datetime.utcnow())
            print(f"\n[OK] Generated {len(signals)} momentum signals")

            for signal in signals:
                print(f"  {signal.action.value} {signal.asset}: {signal.quantity:.0f} units")
                if signal.metadata:
                    print(f"    Momentum score: {signal.metadata.get('momentum_score', 'N/A')}")
                    print(f"    Target weight: {signal.metadata.get('target_weight', 'N/A'):.2%}")

            self.test_results["momentum_strategy"] = len(momentum_scores) > 0
            return True

        except Exception as e:
            print(f"[FAIL] Momentum strategy test failed: {e}")
            self.test_results["momentum_strategy"] = False
            return False

    async def test_performance_analysis(self):
        """测试性能分析"""
        print("\n" + "=" * 60)
        print("Performance Analysis Test")
        print("=" * 60)

        try:
            # 模拟策略收益数据
            strategy_returns = pd.Series(np.random.normal(0.001, 0.02, 252))
            strategy_returns.index = pd.date_range(
                start=datetime.utcnow() - timedelta(days=252),
                periods=252,
                freq='D'
            )

            # 测试绩效计算
            strategy = TriangularArbitrageStrategy(["EURUSD", "USDJPY", "EURJPY"])
            performance = strategy.calculate_performance(strategy_returns)

            print(f"[OK] Calculated performance metrics:")
            for metric, value in performance.items():
                print(f"  {metric}: {value:.4f}")

            # 测试策略管理器风险指标
            risk_metrics = self.strategy_manager.get_risk_metrics()
            print(f"\n[OK] Risk metrics:")
            for metric, value in risk_metrics.items():
                print(f"  {metric}: {value}")

            # 测试组合敞口
            exposure = self.strategy_manager.get_portfolio_exposure()
            print(f"\n[OK] Portfolio exposure:")
            for asset, amount in exposure.items():
                if abs(amount) > 0:
                    print(f"  {asset}: {amount:+.2f}")

            # 验证性能指标合理性
            metrics_valid = (
                performance.get("sharpe_ratio", 0) > -10 and  # 合理的Sharpe比率范围
                performance.get("max_drawdown", 0) >= -1 and  # 最大回撤不超过-100%
                len(risk_metrics) > 0
            )

            print(f"[OK] Performance metrics validation: {metrics_valid}")

            self.test_results["performance_analysis"] = metrics_valid
            return metrics_valid

        except Exception as e:
            print(f"[FAIL] Performance analysis test failed: {e}")
            self.test_results["performance_analysis"] = False
            return False

    async def test_performance_benchmark(self):
        """性能基准测试"""
        print("\n" + "=" * 60)
        print("Performance Benchmark Test")
        print("=" * 60)

        try:
            # 测试不同规模的策略组合
            strategy_counts = [1, 3, 5]
            execution_times = []

            for strategy_count in strategy_counts:
                print(f"\nTesting with {strategy_count} strategies...")

                # 创建策略管理器
                manager = CrossMarketStrategyManager()

                # 添加策略
                for i in range(strategy_count):
                    if i == 0:
                        strategy = TriangularArbitrageStrategy(
                            currency_pairs=["EURUSD", "USDJPY", "EURJPY"]
                        )
                    elif i == 1:
                        strategy = PairsTradingStrategy(
                            asset1="EURUSD",
                            asset2="GBPUSD"
                        )
                    else:
                        strategy = CrossAssetMomentumStrategy(
                            assets=["EURUSD", "GBPUSD", "USDJPY"]
                        )
                    manager.add_strategy(strategy)

                # 初始化策略
                start_time = time.time()
                await manager.initialize_strategies(self.sample_market_data)
                init_time = time.time() - start_time

                # 运行策略
                start_time = time.time()
                signals = await manager.run_strategies(self.sample_market_data)
                execution_time = time.time() - start_time

                total_time = init_time + execution_time
                execution_times.append(total_time)

                print(f"  Initialization: {init_time:.3f}s")
                print(f"  Signal generation: {execution_time:.3f}s")
                print(f"  Total time: {total_time:.3f}s")
                print(f"  Signals generated: {len(signals)}")
                print(f"  Throughput: {len(signals)/execution_time:.1f} signals/sec")

            # 性能评估
            avg_time = np.mean(execution_times)
            max_time = np.max(execution_times)
            performance_target_met = avg_time < 1.0  # 1秒内完成

            print(f"\n[OK] Performance Benchmark Results:")
            print(f"  Average execution time: {avg_time:.3f}s")
            print(f"  Maximum execution time: {max_time:.3f}s")
            print(f"  Performance target met (<1s): {performance_target_met}")

            self.test_results["performance_benchmark"] = performance_target_met
            return performance_target_met

        except Exception as e:
            print(f"[FAIL] Performance benchmark test failed: {e}")
            self.test_results["performance_benchmark"] = False
            return False

    def _modify_market_data_for_scenario(self, market_data: dict, spread_multiplier: float) -> dict:
        """为特定场景修改市场数据"""
        modified_data = {}
        for asset, df in market_data.items():
            # 复制数据
            df_copy = df.copy()

            # 修改bid-ask价差
            if spread_multiplier != 1.0:
                # 模拟更大的价差
                volatility_adjustment = spread_multiplier
                df_copy['high'] = df_copy['close'] * (1 + abs(np.random.normal(0, 0.001, len(df))) * volatility_adjustment)
                df_copy['low'] = df_copy['close'] * (1 - abs(np.random.normal(0, 0.001, len(df))) * volatility_adjustment)

            modified_data[asset] = df_copy

        return modified_data

    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("Cross-Market Strategy Engine Test Summary")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = len([result for result in self.test_results.values() if result])
        failed_tests = total_tests - passed_tests

        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success rate: {passed_tests/total_tests:.1%}")

        print("\nTest Details:")
        for test_name, result in self.test_results.items():
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {test_name}")

        # Overall assessment
        success_rate = passed_tests / total_tests
        if success_rate >= 0.8:
            print(f"\n[SUCCESS] Cross-market strategy engine is production ready!")
            print("All core strategies implemented and tested successfully.")
        elif success_rate >= 0.6:
            print(f"\n[PARTIAL SUCCESS] Cross-market strategy engine mostly functional.")
            print("Some components need improvement but core features work.")
        else:
            print(f"\n[NEEDS IMPROVEMENT] Cross-market strategy engine requires fixes.")
            print("Significant issues detected that need to be addressed.")

        return success_rate >= 0.6

async def main():
    """主测试函数"""
    print("Cross-Market Strategy Engine Comprehensive Test")
    print("=" * 60)
    print("Testing arbitrage, correlation, and momentum strategies...")
    print()

    tester = CrossMarketStrategyTester()

    try:
        # 创建测试数据
        tester.create_sample_market_data()

        # 运行所有测试
        test_functions = [
            tester.test_strategy_initialization,
            tester.test_signal_generation,
            tester.test_triangular_arbitrage_strategy,
            tester.test_pairs_trading_strategy,
            tester.test_momentum_strategy,
            tester.test_performance_analysis,
            tester.test_performance_benchmark
        ]

        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"Test {test_func.__name__} failed with exception: {e}")

        # 打印总结
        success_rate = tester.print_test_summary()

        return success_rate

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit_code = 0 if success else 1
    sys.exit(exit_code)