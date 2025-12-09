#!/usr/bin/env python3
"""
0700.HK 0-300 Parameter Backtesting System Demo
Comprehensive demonstration of the parameter optimization system
"""

import time
import json
import logging
from datetime import datetime

# Set path
import sys
sys.path.append('src')
sys.path.append('src/parameter_space')
sys.path.append('src/adapters')
sys.path.append('src/optimization')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def demonstrate_parameter_space():
    """Demonstrate parameter space management"""
    print("=" * 80)
    print("0700.HK Parameter Space Manager Demo")
    print("=" * 80)

    try:
        from hk700_parameter_manager import HK700ParameterManager
        manager = HK700ParameterManager()

        # Display all parameter spaces
        print("\nAvailable Parameter Spaces:")
        for space_name in manager.parameter_spaces.keys():
            stats = manager.get_space_statistics(space_name)
            print(f"  {space_name}:")
            print(f"    - Total Combinations: {stats['total_combinations']:,}")
            print(f"    - Parameter Count: {stats['total_parameters']}")
            print(f"    - Constraints Count: {stats['constraints_count']}")
            print(f"    - Description: {stats['description']}")

        # Show parameter ranges
        print(f"\nRSI 0-300 Parameter Range Details:")
        rsi_space = manager.parameter_spaces['RSI_0_300']
        for param in rsi_space.parameters:
            param_range = param.generate_range()
            print(f"  {param.name}:")
            print(f"    - Range: {param.min_value} - {param.max_value} (step: {param.step})")
            print(f"    - Type: {param.param_type}")
            print(f"    - Options Count: {len(param_range)}")
            if len(param_range) <= 10:
                print(f"    - Sample Values: {param_range[:5]}...")

        # Demonstrate smart sampling
        print(f"\nSmart Sampling Demo:")
        sample_size = 1000
        smart_sample = manager.generate_smart_sample('RSI_0_300', sample_size)
        print(f"  Generated {len(smart_sample)} smart sample combinations")

        # Analyze sampling strategy
        rsi_oversold_values = [p['rsi_oversold'] for p in smart_sample]
        rsi_overbought_values = [p['rsi_overbought'] for p in smart_sample]

        print(f"  RSI Oversold Distribution: min={min(rsi_oversold_values)}, max={max(rsi_oversold_values)}, avg={sum(rsi_oversold_values)/len(rsi_oversold_values):.1f}")
        print(f"  RSI Overbought Distribution: min={min(rsi_overbought_values)}, max={max(rsi_overbought_values)}, avg={sum(rsi_overbought_values)/len(rsi_overbought_values):.1f}")

    except Exception as e:
        logger.error(f"Parameter space demo failed: {e}")
        return False

    return True


def demonstrate_data_adapter():
    """Demonstrate data adapter"""
    print("\n" + "=" * 80)
    print("0700.HK Data Adapter Demo")
    print("=" * 80)

    try:
        from hk700_data_adapter import HK700DataAdapter
        adapter = HK700DataAdapter()

        # Get data statistics
        print("\nData Statistics:")
        stats = adapter.get_data_statistics()
        if 'error' in stats:
            print("  Unable to get data")
            return False

        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    - {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")

        # Load processed data
        print(f"\nLoading Technical Indicator Data...")
        data_with_indicators = adapter.get_data_with_indicators()

        if not data_with_indicators.empty:
            print(f"  Successfully loaded {len(data_with_indicators)} data points")
            print(f"  Technical Indicators: {list(data_with_indicators.columns)}")

            # Display latest indicator values
            print(f"\nLatest Technical Indicator Values:")
            latest_row = data_with_indicators.iloc[-1]
            for col in ['rsi_14', 'macd', 'atr', 'volume_ratio']:
                if col in data_with_indicators.columns:
                    print(f"  - {col}: {latest_row[col]:.3f}")
        else:
            print("  Unable to load indicator data")

    except Exception as e:
        logger.error(f"Data adapter demo failed: {e}")
        return False

    return True


def demonstrate_optimizer():
    """Demonstrate optimizer functionality"""
    print("\n" + "=" * 80)
    print("0700.HK Parameter Optimizer Demo")
    print("=" * 80)

    try:
        from hk700_optimizer import HK700Optimizer

        # Initialize optimizer
        print("Initializing optimizer...")
        optimizer = HK700Optimizer(max_workers=4)

        # Set optimization parameters
        test_combinations = 1000
        optimization_metric = "sharpe_ratio"

        print(f"Starting small-scale optimization test...")
        print(f"  - Test combinations: {test_combinations:,}")
        print(f"  - Optimization metric: {optimization_metric}")
        print(f"  - Using threads: {optimizer.max_workers}")

        # Execute optimization (using small-scale test)
        start_time = time.time()
        result = optimizer.run_parameter_optimization(
            parameter_space="RSI_0_300",
            optimization_metric=optimization_metric,
            max_combinations=test_combinations,
            use_smart_sampling=True
        )
        optimization_time = time.time() - start_time

        # Display results
        print(f"\nOptimization Results (Time: {optimization_time:.2f} seconds):")
        print(f"  Strategy Name: {result.strategy_name}")
        print(f"  Tested Combinations: {result.total_combinations:,}")
        print(f"  Successful Combinations: {result.successful_combinations:,}")
        print(f"  Processing Speed: {result.successful_combinations/optimization_time:.1f} combinations/second")
        print(f"  Cache Hit Rate: {result.cache_hit_rate:.1%}")
        print(f"  Threads Used: {result.workers_used}")

        # Display best parameters
        print(f"\nBest Parameter Combination:")
        for param, value in result.best_parameters.items():
            print(f"  - {param}: {value}")

        # Display best performance
        print(f"\nBest Performance Metrics:")
        key_metrics = ['sharpe_ratio', 'total_return', 'max_drawdown', 'win_rate']
        for metric in key_metrics:
            if metric in result.best_performance:
                value = result.best_performance[metric]
                if metric in ['sharpe_ratio']:
                    print(f"  - {metric}: {value:.3f}")
                elif metric in ['total_return', 'max_drawdown']:
                    print(f"  - {metric}: {value:.2%}")
                else:
                    print(f"  - {metric}: {value}")

        # Display performance statistics
        if result.performance_statistics:
            print(f"\nOptimization Statistics:")
            stats = result.performance_statistics
            print(f"  - Average Score: {stats['mean_score']:.4f}")
            print(f"  - Score Standard Deviation: {stats['std_score']:.4f}")
            print(f"  - Score Range: {stats['min_score']:.4f} - {stats['max_score']:.4f}")
            print(f"  - Success Rate: {stats['successful_rate']:.1%}")

        # Generate and display report
        report = optimizer.generate_optimization_report(result)
        print(report)

    except Exception as e:
        logger.error(f"Optimizer demo failed: {e}")
        return False

    return True


def run_comparison_demo():
    """Run parameter space comparison demo"""
    print("\n" + "=" * 80)
    print("Parameter Space Comparison Demo")
    print("=" * 80)

    try:
        from hk700_optimizer import HK700Optimizer

        # Initialize optimizer
        optimizer = HK700Optimizer(max_workers=2)  # Use fewer threads for faster demo

        # Test multiple parameter spaces
        test_spaces = ["RSI_0_300", "MACD_0_300", "MA_0_300"]
        test_combinations = 500

        print(f"Comparing parameter spaces: {', '.join(test_spaces)}")
        print(f"Testing per space: {test_combinations:,} combinations")

        # Run comparison
        results = optimizer.compare_parameter_spaces(
            parameter_spaces=test_spaces,
            max_combinations_per_space=test_combinations,
            optimization_metric="sharpe_ratio"
        )

        # Display comparison results
        print(f"\nComparison Results Overview:")
        for space_name, result in results.items():
            sharpe = result.best_performance.get('sharpe_ratio', 0)
            print(f"  {space_name}:")
            print(f"    - Best Sharpe: {sharpe:.3f}")
            print(f"    - Total Return: {result.best_performance.get('total_return', 0):.2%}")
            print(f"    - Max Drawdown: {result.best_performance.get('max_drawdown', 0):.2%}")
            print(f"    - Optimization Time: {result.optimization_time:.2f} seconds")

        # Find best strategy
        best_space = max(results.items(), key=lambda x: x[1].best_performance.get('sharpe_ratio', 0))
        print(f"\nBest Strategy: {best_space[0]} (Sharpe: {best_space[1].best_performance.get('sharpe_ratio', 0):.3f})")

    except Exception as e:
        logger.error(f"Comparison demo failed: {e}")
        return False

    return True


def main():
    """Main demonstration function"""
    print("0700.HK 0-300 Parameter Backtesting System Demo")
    print("Professional quantitative trading optimization platform for Tencent Holdings")
    print("Supporting full 0-300 range parameter combination testing and intelligent sampling optimization")
    print()

    start_time = time.time()

    # Run various demo modules
    demos = [
        demonstrate_parameter_space,
        demonstrate_data_adapter,
        demonstrate_optimizer,
        run_comparison_demo
    ]

    results = []
    for demo in demos:
        try:
            result = demo()
            results.append(result)
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            results.append(False)

    # Summary
    total_time = time.time() - start_time
    success_count = sum(results)

    print("\n" + "=" * 80)
    print("Demo Completion Summary")
    print("=" * 80)
    print(f"Successful Demos: {success_count}/{len(demos)}")
    print(f"Total Time: {total_time:.2f} seconds")
    print()
    print("Core Features Demonstrated:")
    print("  - Parameter Space Manager - Supports full 0-300 range")
    print("  - Intelligent Sampling Algorithm - Reduces computational complexity")
    print("  - High-performance Parallel Processing - Multi-threaded optimization")
    print("  - Data Caching Mechanism - Improves processing efficiency")
    print("  - Comprehensive Performance Analysis - Sharpe, Sortino and other metrics")
    print("  - Real-time Result Visualization - Complete report generation")
    print()
    print("System ready for large-scale 0-300 parameter backtesting!")
    print("You can run: python hk700_parameter_backtest.py --mode=full")

    if success_count == len(demos):
        print("\nAll demos completed successfully! 0700.HK parameter backtesting system is ready.")
        return True
    else:
        print(f"\nSome demos failed, please check logs for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)