"""
Phase 3 高级功能演示

此示例展示了蒙特卡罗模拟、压力测试和性能优化功能的使用。
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtest.monte_carlo import MonteCarloSimulator, MCSimulationConfig, run_monte_carlo
from backtest.advanced_backtest_engine import AdvancedBacktestEngine
from backtest.performance_optimizer import PerformanceOptimizer, VectorizedIndicators
from strategies.ma_crossover import MACrossoverStrategy
from strategies.rsi_strategy import RSIStrategy


def generate_sample_data(days=252):
    """生成示例价格数据"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')

    # 生成价格走势（带趋势和噪声）
    returns = np.random.normal(0.001, 0.02, days)
    prices = 100 * np.exp(np.cumsum(returns))

    # 创建 OHLCV 数据
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(days) * 0.002),
        'high': prices * (1 + np.abs(np.random.randn(days)) * 0.01),
        'low': prices * (1 - np.abs(np.random.randn(days)) * 0.01),
        'close': prices,
        'volume': np.random.randint(100000, 1000000, days)
    }, index=dates)

    return data


def demo_monte_carlo():
    """演示蒙特卡罗模拟"""
    print("\n" + "="*50)
    print("蒙特卡罗模拟演示")
    print("="*50)

    # 生成示例数据
    data = generate_sample_data(252)
    returns = data['close'].pct_change().dropna()

    print(f"\n历史数据统计:")
    print(f"  日均收益: {returns.mean():.4f}")
    print(f"  收益标准差: {returns.std():.4f}")
    print(f"  年化收益: {returns.mean() * 252:.2%}")
    print(f"  年化波动率: {returns.std() * np.sqrt(252):.2%}")

    # 配置蒙特卡罗模拟
    config = MCSimulationConfig(
        n_simulations=1000,  # 使用较少的模拟以便快速演示
        time_horizon=252,
        confidence_levels=[0.90, 0.95, 0.99],
        random_seed=42
    )

    # 创建模拟器
    simulator = MonteCarloSimulator(config)

    # 运行不同类型的模拟
    methods = ['bootstrap', 'parametric', 'gbm']

    for method in methods:
        print(f"\n{method.upper()} 模拟结果:")
        print("-" * 30)

        if method == 'bootstrap':
            results = simulator.simulate_bootstrap(returns, initial_capital=100000)
        elif method == 'parametric':
            results = simulator.simulate_parametric(returns, initial_capital=100000)
        else:  # gbm
            results = simulator.simulate_geometric_brownian(returns, initial_capital=100000)

        # 显示关键指标
        print(f"  最终价值均值: ${results.statistics['mean']:,.2f}")
        print(f"  最终价值中位数: ${results.statistics['median']:,.2f}")
        print(f"  标准差: ${results.statistics['std']:,.2f}")
        print(f"  95% VaR: ${results.var[0.95]:,.2f}")
        print(f"  正收益概率: {results.success_probability['positive_return']:.2%}")
        print(f"  翻倍概率: {results.success_probability['doubling']:.2%}")


def demo_stress_testing():
    """演示压力测试"""
    print("\n" + "="*50)
    print("压力测试演示")
    print("="*50)

    # 创建策略和数据
    strategy = MACrossoverStrategy(short_window=10, long_window=30)
    data = generate_sample_data(252)

    # 创建高级回测引擎
    engine = AdvancedBacktestEngine()

    # 定义压力测试场景
    stress_scenarios = [
        {
            'name': 'market_crash',
            'description': '突然 20% 市场下跌',
            'type': 'price_shock',
            'magnitude': -0.20,
            'duration': 5
        },
        {
            'name': 'volatility_spike',
            'description': '波动率增加 2 倍',
            'type': 'volatility_shock',
            'multiplier': 2.0,
            'duration': 15
        }
    ]

    # 运行压力测试
    print("\n运行基准测试和压力测试...")
    results = engine.run_stress_test(strategy, data, stress_scenarios)

    # 显示结果
    baseline = results['baseline']['metrics']
    print(f"\n基准回测结果:")
    print(f"  总收益: {baseline['total_return']:.2%}")
    print(f"  夏普比率: {baseline['sharpe_ratio']:.3f}")
    print(f"  最大回撤: {baseline['max_drawdown']:.2%}")

    print(f"\n压力测试结果:")
    for scenario_name, scenario_data in results['stress_tests'].items():
        impact = scenario_data['impact']
        print(f"\n{scenario_name}:")
        print(f"  总收益变化: {impact.get('total_return', {}).get('percent_change', 0):.2%}")
        print(f"  夏普比率变化: {impact.get('sharpe_ratio', {}).get('percent_change', 0):.2%}")
        print(f"  最大回撤变化: {impact.get('max_drawdown', {}).get('percent_change', 0):.2%}")

    # 显示摘要
    summary = results['summary']
    print(f"\n压力测试摘要:")
    print(f"  最糟糕场景: {summary['worst_scenario']}")
    if summary['recommendations']:
        print(f"  建议: {', '.join(summary['recommendations'])}")


def demo_performance_optimization():
    """演示性能优化"""
    print("\n" + "="*50)
    print("性能优化演示")
    print("="*50)

    # 创建优化器
    optimizer = PerformanceOptimizer()

    # 准备策略和参数
    data = generate_sample_data(126)  # 使用较少数据以便快速演示
    strategies = [
        MACrossoverStrategy(short_window=5, long_window=20),
        MACrossoverStrategy(short_window=10, long_window=30),
        RSIStrategy(period=14, overbought=70, oversold=30)
    ]

    # 批量回测
    print("\n运行批量回测...")
    start_time = datetime.now()

    batch_results = optimizer.batch_backtest_strategies(
        strategies=strategies,
        data=data,
        parallel=False  # 设置为 False 以避免并行处理问题
    )

    duration = (datetime.now() - start_time).total_seconds()
    print(f"批量回测完成，耗时: {duration:.2f} 秒")

    # 显示结果
    print(f"\n批量回测结果:")
    for i, result in enumerate(batch_results):
        if 'metrics' in result:
            metrics = result['metrics']
            strategy_name = strategies[i].__class__.__name__
            print(f"  {strategy_name}:")
            print(f"    总收益: {metrics.get('total_return', 0):.2%}")
            print(f"    夏普比率: {metrics.get('sharpe_ratio', 0):.3f}")

    # 参数优化演示
    print(f"\n参数优化演示...")
    param_grid = {
        'short_window': [5, 10, 15],
        'long_window': [20, 25, 30]
    }

    opt_start = datetime.now()
    optimization_results = optimizer.optimize_strategy_parameters(
        strategy_class=MACrossoverStrategy,
        param_grid=param_grid,
        data=data,
        objective='sharpe_ratio',
        parallel=False
    )
    opt_duration = (datetime.now() - opt_start).total_seconds()

    print(f"参数优化完成，耗时: {opt_duration:.2f} 秒")
    print(f"最佳参数: {optimization_results['best_parameters']}")
    print(f"最佳夏普比率: {optimization_results['best_score']:.3f}")


def demo_vectorized_indicators():
    """演示向量化指标"""
    print("\n" + "="*50)
    print("向量化指标演示")
    print("="*50)

    # 生成价格数据
    prices = generate_sample_data(100)['close'].values

    # 计算向量化指标
    print("\n计算技术指标...")

    # SMA
    sma_20 = VectorizedIndicators.sma(prices, 20)
    print(f"SMA(20) 最新值: {sma_20[-1]:.2f}")

    # EMA
    ema_20 = VectorizedIndicators.ema(prices, 20)
    print(f"EMA(20) 最新值: {ema_20[-1]:.2f}")

    # RSI
    rsi_14 = VectorizedIndicators.rsi(prices, 14)
    print(f"RSI(14) 最新值: {rsi_14[-1]:.2f}")

    # Bollinger Bands
    upper, middle, lower = VectorizedIndicators.bollinger_bands(prices, 20, 2)
    print(f"Bollinger Bands 最新值:")
    print(f"  上轨: {upper[-1]:.2f}")
    print(f"  中轨: {middle[-1]:.2f}")
    print(f"  下轨: {lower[-1]:.2f}")


def main():
    """主函数"""
    print("CBSC 量化交易系统 Phase 3 高级功能演示")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        # 运行各个演示
        demo_monte_carlo()
        demo_stress_testing()
        demo_performance_optimization()
        demo_vectorized_indicators()

        print("\n" + "="*50)
        print("演示完成！")
        print("="*50)
        print("\nPhase 3 新功能总结:")
        print("1. ✓ 蒙特卡罗模拟 - 评估策略不确定性和风险")
        print("2. ✓ 压力测试 - 测试极端市场条件下的表现")
        print("3. ✓ 性能优化 - 并行处理和向量化操作")
        print("4. ✓ 综合分析 - 整合所有分析维度")
        print("\n系统现在具备机构级量化分析能力！")

    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()