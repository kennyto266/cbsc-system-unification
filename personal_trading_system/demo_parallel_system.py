#!/usr/bin/env python3
"""
32-Core CPU Parallel Processing System Demo
Comprehensive demonstration of the high-performance parallel backtesting system
"""

import os
import sys
import time
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add parallel system to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parallel import (
    ParallelProcessingSystem,
    quick_backtest,
    quick_parameter_sweep,
    simple_ma_crossover_strategy,
    rsi_mean_reversion_strategy,
    BacktestConfig
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_sample_data(symbols: list, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Create sample price data for demonstration"""
    date_range = pd.date_range(start_date, end_date, freq='D')

    all_data = []
    for symbol in symbols:
        # Generate realistic price data with trends and volatility
        base_price = np.random.uniform(50, 200)
        trend = np.random.uniform(-0.001, 0.001, len(date_range))
        volatility = np.random.uniform(0.01, 0.03)

        prices = []
        current_price = base_price

        for i in range(len(date_range)):
            # Add trend and random walk
            price_change = trend[i] + np.random.normal(0, volatility)
            current_price *= (1 + price_change)

            # Ensure price stays positive
            current_price = max(current_price, 1.0)
            prices.append(current_price)

        # Create DataFrame
        df = pd.DataFrame({
            'open': np.array(prices) * (1 + np.random.normal(0, 0.002, len(date_range))),
            'high': np.array(prices) * (1 + np.abs(np.random.normal(0, 0.01, len(date_range)))),
            'low': np.array(prices) * (1 - np.abs(np.random.normal(0, 0.01, len(date_range)))),
            'close': prices,
            'volume': np.random.randint(100000, 10000000, len(date_range))
        }, index=date_range)

        df['symbol'] = symbol
        all_data.append(df)

    return pd.concat(all_data, ignore_index=True)


def demo_basic_functionality():
    """Demonstrate basic parallel processing functionality"""
    logger.info("🚀 Starting Basic Parallel Processing Demo")
    print("=" * 70)
    print("DEMO 1: Basic Parallel Processing Functionality")
    print("=" * 70)

    # Create sample data
    symbols = ['TECH_A', 'TECH_B', 'FINC_X', 'FINC_Y']
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2021, 12, 31)

    logger.info("Creating sample price data...")
    data = create_sample_data(symbols, start_date, end_date)
    logger.info(f"Created sample data: {len(data)} rows for {len(symbols)} symbols")

    # Quick backtest demo
    logger.info("Running quick backtest...")
    start_time = time.time()

    result = quick_backtest(
        data=data,
        strategy_function=simple_ma_crossover_strategy,
        symbols=symbols,
        max_workers=8,  # Reduced for demo
        strategy_params={'fast_period': 10, 'slow_period': 30}
    )

    processing_time = time.time() - start_time
    logger.info(f"Backtest completed in {processing_time:.2f} seconds")

    # Display results
    print(f"\n📊 BACKTEST RESULTS:")
    print(f"   Total Return: {result.total_return:.2%}")
    print(f"   Sharpe Ratio: {result.sharpe_ratio:.3f}")
    print(f"   Max Drawdown: {result.max_drawdown:.2%}")
    print(f"   Win Rate: {result.win_rate:.2%}")
    print(f"   Total Trades: {result.total_trades}")
    print(f"   Final Portfolio: ${result.final_portfolio_value:,.2f}")
    print(f"   Processing Time: {processing_time:.2f} seconds")

    return result


def demo_parameter_optimization():
    """Demonstrate parameter optimization with parallel processing"""
    logger.info("🎯 Starting Parameter Optimization Demo")
    print("\n" + "=" * 70)
    print("DEMO 2: Parameter Optimization Sweep")
    print("=" * 70)

    # Create sample data
    symbols = ['OPTIMIZE_TEST']
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2020, 12, 31)

    logger.info("Creating optimization data...")
    data = create_sample_data(symbols, start_date, end_date)

    # Define parameter grid
    parameter_grid = {
        'fast_period': [5, 10, 15, 20],
        'slow_period': [25, 30, 35, 40, 45, 50]
    }

    logger.info(f"Running parameter sweep with {len(parameter_grid['fast_period']) * len(parameter_grid['slow_period'])} combinations...")
    start_time = time.time()

    # Run parameter sweep
    results = quick_parameter_sweep(
        data=data,
        strategy_function=simple_ma_crossover_strategy,
        parameter_grid=parameter_grid,
        max_workers=8,  # Reduced for demo
        combination_limit=12  # Limit combinations for demo
    )

    processing_time = time.time() - start_time
    logger.info(f"Parameter sweep completed in {processing_time:.2f} seconds")

    # Display top results
    print(f"\n🏆 TOP 5 PARAMETER COMBINATIONS:")
    print("-" * 50)

    for i, result in enumerate(results[:5]):
        # Extract parameters from strategy_params (if available)
        params = getattr(result, 'strategy_params', {})
        fast_period = params.get('fast_period', 'N/A')
        slow_period = params.get('slow_period', 'N/A')

        print(f"{i+1}. Fast: {fast_period:2}, Slow: {slow_period:2} | "
              f"Sharpe: {result.sharpe_ratio:6.3f} | "
              f"Return: {result.total_return:7.2%} | "
              f"Trades: {result.total_trades:4d}")

    return results


def demo_large_scale_processing():
    """Demonstrate large-scale data processing capabilities"""
    logger.info("📈 Starting Large-Scale Processing Demo")
    print("\n" + "=" * 70)
    print("DEMO 3: Large-Scale Parallel Data Processing")
    print("=" * 70)

    # Create large dataset (simulating years of data)
    symbols = ['LARGE_SCALE_1', 'LARGE_SCALE_2', 'LARGE_SCALE_3', 'LARGE_SCALE_4', 'LARGE_SCALE_5']
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2022, 12, 31)  # 8 years of data

    logger.info("Creating large-scale dataset...")
    data = create_sample_data(symbols, start_date, end_date)
    logger.info(f"Created large dataset: {len(data)} rows for {len(symbols)} symbols over 8 years")

    # Initialize parallel system
    logger.info("Initializing parallel processing system...")
    from parallel import ParallelProcessingSystem

    with ParallelProcessingSystem(
        max_workers=16,  # Reduced for demo
        memory_limit_gb=32.0,
        enable_optimization=True,
        enable_monitoring=True
    ) as system:

        # Process data in parallel with technical indicators
        logger.info("Running parallel technical indicator calculation...")
        start_time = time.time()

        processed_data = system.process_data_parallel(
            data=data,
            processing_function='calculate_technical_indicators',
            chunk_size=1000,  # Process in chunks
            merge_results=True
        )

        processing_time = time.time() - start_time
        logger.info(f"Data processing completed in {processing_time:.2f} seconds")

        # Display processing results
        print(f"\n🔄 LARGE-SCALE PROCESSING RESULTS:")
        print(f"   Original Data Shape: {data.shape}")
        print(f"   Processed Data Shape: {processed_data.shape}")
        print(f"   New Indicators: {len(processed_data.columns) - len(data.columns)}")
        print(f"   Processing Time: {processing_time:.2f} seconds")
        print(f"   Processing Speed: {len(data) / processing_time:.0f} rows/second")

    return processed_data


def demo_advanced_backtesting():
    """Demonstrate advanced backtesting with multiple strategies"""
    logger.info("⚡ Starting Advanced Backtesting Demo")
    print("\n" + "=" * 70)
    print("DEMO 4: Advanced Multi-Strategy Backtesting")
    print("=" * 70)

    # Create diverse dataset
    symbols = ['TECH_LARGE', 'TECH_SMALL', 'FINC_BANK', 'FINC_INSURANCE', 'ENERGY_OIL', 'ENERGY_GAS']
    start_date = datetime(2019, 1, 1)
    end_date = datetime(2021, 12, 31)

    logger.info("Creating diverse dataset for advanced backtesting...")
    data = create_sample_data(symbols, start_date, end_date)

    # Initialize system with monitoring
    logger.info("Initializing advanced backtesting system...")
    from parallel import ParallelProcessingSystem

    with ParallelProcessingSystem(
        max_workers=12,
        memory_limit_gb=24.0,
        enable_optimization=True,
        enable_monitoring=True,
        enable_profiling=True
    ) as system:

        # Test multiple strategies
        strategies = [
            ("MA Crossover", simple_ma_crossover_strategy, {'fast_period': 10, 'slow_period': 30}),
            ("RSI Mean Reversion", rsi_mean_reversion_strategy, {'rsi_period': 14, 'oversold': 30, 'overbought': 70})
        ]

        results = {}

        for strategy_name, strategy_func, strategy_params in strategies:
            logger.info(f"Running {strategy_name} strategy...")
            start_time = time.time()

            result = system.run_backtest(
                data=data,
                strategy_function=strategy_func,
                symbols=symbols,
                strategy_params=strategy_params
            )

            processing_time = time.time() - start_time
            results[strategy_name] = result

            logger.info(f"{strategy_name} completed in {processing_time:.2f} seconds")

        # Compare strategies
        print(f"\n🏁 STRATEGY COMPARISON:")
        print("-" * 50)
        print(f"{'Strategy':<20} {'Sharpe':<10} {'Return':<12} {'Drawdown':<12} {'Trades':<8}")
        print("-" * 62)

        for strategy_name, result in results.items():
            print(f"{strategy_name:<20} {result.sharpe_ratio:<10.3f} "
                  f"{result.total_return:<12.2%} {result.max_drawdown:<12.2%} "
                  f"{result.total_trades:<8d}")

        # Get system performance metrics
        system_status = system.get_system_status()
        print(f"\n📊 SYSTEM PERFORMANCE METRICS:")
        print(f"   Peak CPU Usage: {system_status['real_time_metrics'].get('cpu_utilization', 0):.1f}%")
        print(f"   Memory Usage: {system_status['real_time_metrics'].get('memory_usage_mb', 0):.1f}MB")
        print(f"   Task Throughput: {system_status['real_time_metrics'].get('tasks_per_second', 0):.1f}/s")

    return results


def demo_system_optimization():
    """Demonstrate system optimization and tuning"""
    logger.info("🔧 Starting System Optimization Demo")
    print("\n" + "=" * 70)
    print("DEMO 5: System Optimization and Performance Tuning")
    print("=" * 70)

    from parallel import SystemOptimizer

    # Create system optimizer
    optimizer = SystemOptimizer(enable_detailed_profiling=True)

    # Profile the system
    logger.info("Profiling system capabilities...")
    system_profile = optimizer.profile_system()

    print(f"\n💻 SYSTEM PROFILE:")
    print(f"   CPU Cores: {system_profile.cpu_cores}")
    print(f"   CPU Threads: {system_profile.cpu_threads}")
    print(f"   CPU Frequency: {system_profile.cpu_freq_mhz:.1f}MHz")
    print(f"   Total Memory: {system_profile.total_memory_gb:.1f}GB")
    print(f"   System Tier: {system_profile.system_tier.value.upper()}")
    print(f"   GPU Available: {system_profile.gpu_available}")
    if system_profile.gpu_available:
        print(f"   GPU Memory: {system_profile.gpu_memory_gb:.1f}GB")

    # Get optimization recommendations
    logger.info("Generating optimization recommendations...")
    recommendations = optimizer.get_optimization_recommendations()

    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    recommendations_list = recommendations.get('recommendations', [])
    if recommendations_list:
        for i, rec in enumerate(recommendations_list[:5], 1):
            print(f"{i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"   Expected Improvement: {rec['expected_improvement']}")
            print(f"   Implementation Difficulty: {rec['implementation_difficulty']}")
            print()
    else:
        print("   No specific recommendations for this system configuration.")

    # Benchmark the system
    logger.info("Running system benchmarks...")
    benchmark_results = optimizer.benchmark_system(iterations=3)

    print(f"\n⚡ BENCHMARK RESULTS:")
    print(f"   CPU Performance: {benchmark_results.get('cpu_mops', 0):.1f} MOPS")
    print(f"   Memory Bandwidth: {benchmark_results.get('memory_gb_s', 0):.2f} GB/s")
    print(f"   Disk I/O Speed: {benchmark_results.get('disk_io_mb_s', 0):.1f} MB/s")
    print(f"   Parallel Efficiency: {benchmark_results.get('parallel_efficiency', 0):.1%}")

    return optimizer


def demo_integration():
    """Demonstrate complete system integration"""
    logger.info("🔗 Starting System Integration Demo")
    print("\n" + "=" * 70)
    print("DEMO 6: Complete System Integration")
    print("=" * 70)

    from parallel import ParallelProcessingSystem, BacktestConfig

    # Create comprehensive test scenario
    symbols = ['INTL_1', 'INTL_2', 'INTL_3', 'INTL_4', 'INTL_5', 'INTL_6']
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2021, 12, 31)

    logger.info("Setting up comprehensive integration test...")
    data = create_sample_data(symbols, start_date, end_date)

    # Initialize complete system
    with ParallelProcessingSystem(
        max_workers=16,
        memory_limit_gb=32.0,
        enable_optimization=True,
        enable_monitoring=True,
        enable_profiling=True
    ) as system:

        logger.info("Running comprehensive integration test...")
        start_time = time.time()

        # 1. Run technical indicator calculation
        processed_data = system.process_data_parallel(
            data=data,
            processing_function='calculate_technical_indicators',
            chunk_size=500
        )

        # 2. Run multiple strategy backtests
        ma_result = system.run_backtest(
            data=processed_data,
            strategy_function=simple_ma_crossover_strategy,
            symbols=symbols,
            strategy_params={'fast_period': 15, 'slow_period': 35}
        )

        rsi_result = system.run_backtest(
            data=processed_data,
            strategy_function=rsi_mean_reversion_strategy,
            symbols=symbols,
            strategy_params={'rsi_period': 14, 'oversold': 25, 'overbought': 75}
        )

        # 3. Run parameter optimization
        param_grid = {
            'fast_period': [5, 10, 15],
            'slow_period': [25, 35, 45]
        }

        param_results = system.run_parameter_sweep(
            data=processed_data,
            strategy_function=simple_ma_crossover_strategy,
            parameter_grid=param_grid,
            combination_limit=6
        )

        total_time = time.time() - start_time

        # Generate comprehensive report
        report = system.generate_report()

        print(f"\n🎉 INTEGRATION TEST COMPLETED")
        print(f"   Total Processing Time: {total_time:.2f} seconds")
        print(f"   Data Processed: {len(processed_data)} rows")
        print(f"   Strategies Tested: 2")
        print(f"   Parameter Combinations: {len(param_results)}")
        print(f"   Active Workers: {system.max_workers}")
        print(f"   Memory Limit: {system.memory_limit_gb}GB")

        print(f"\n📊 FINAL RESULTS:")
        print(f"   MA Strategy Sharpe: {ma_result.sharpe_ratio:.3f}")
        print(f"   RSI Strategy Sharpe: {rsi_result.sharpe_ratio:.3f}")
        print(f"   Best Parameter Sharpe: {param_results[0].sharpe_ratio:.3f}")

        # Save report to file
        report_file = Path("parallel_system_demo_report.json")
        with open(report_file, 'w') as f:
            f.write(report)

        print(f"\n📄 Report saved to: {report_file}")

    return True


def main():
    """Main demo function"""
    print("🚀 32-CORE CPU PARALLEL PROCESSING SYSTEM DEMO")
    print("=" * 70)
    print("This demo showcases the high-performance parallel processing capabilities")
    print("for quantitative backtesting and large-scale data processing.")
    print("=" * 70)

    demos = [
        demo_basic_functionality,
        demo_parameter_optimization,
        demo_large_scale_processing,
        demo_advanced_backtesting,
        demo_system_optimization,
        demo_integration
    ]

    results = {}

    try:
        for i, demo_func in enumerate(demos, 1):
            print(f"\n{'=' * 70}")
            print(f"Starting Demo {i}/{len(demos)}")
            print(f"{'=' * 70}")

            start_time = time.time()
            result = demo_func()
            processing_time = time.time() - start_time

            results[f"demo_{i}"] = {
                'success': True,
                'time': processing_time,
                'result': result
            }

            logger.info(f"Demo {i} completed successfully in {processing_time:.2f} seconds")

            # Short pause between demos
            if i < len(demos):
                print("\nPausing 3 seconds before next demo...")
                time.sleep(3)

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

    # Final summary
    print("\n" + "=" * 70)
    print("🏆 DEMO SUMMARY")
    print("=" * 70)

    successful_demos = sum(1 for r in results.values() if r['success'])
    total_time = sum(r['time'] for r in results.values())

    print(f"Successful Demos: {successful_demos}/{len(demos)}")
    print(f"Total Processing Time: {total_time:.2f} seconds")
    print(f"Average Demo Time: {total_time / len(demos):.2f} seconds")

    if successful_demos == len(demos):
        print("✅ All demos completed successfully!")
    else:
        print(f"⚠️  {len(demos) - successful_demos} demos failed")

    print("\nThank you for testing the 32-Core Parallel Processing System!")
    print("🚀 Ready for production-scale quantitative backtesting!")


if __name__ == "__main__":
    main()