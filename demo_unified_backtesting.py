#!/usr/bin/env python3
"""
Unified Backtesting Framework Demo

Demonstration of the comprehensive parameter optimization system
for CBSC trading strategies with 0-300 range testing using multi-process VectorBT.

Usage:
    python demo_unified_backtesting.py [--strategy rsi_strategy] [--quick] [--workers 8]
"""

import argparse
import logging
import time
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Import the unified backtesting framework
from src.unified_backtesting import (
    UnifiedBacktestingFramework,
    BacktestingConfig,
    OptimizationRequest,
    quick_optimization
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_backtesting_demo.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_sample_data(ticker: str = "AAPL", period: str = "2y") -> pd.DataFrame:
    """
    Create sample price data for demonstration

    Args:
        ticker: Stock ticker symbol
        period: Time period for data

    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"Fetching sample data for {ticker} over {period}")

    try:
        # Download data from Yahoo Finance
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)

        # Ensure we have the required columns
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
        data.columns = [col.lower() for col in data.columns]

        logger.info(f"Downloaded {len(data)} days of data for {ticker}")
        return data

    except Exception as e:
        logger.error(f"Failed to download data: {str(e)}")
        # Create synthetic data as fallback
        logger.info("Creating synthetic data for demonstration...")
        return create_synthetic_data()


def create_synthetic_data(days: int = 504) -> pd.DataFrame:
    """
    Create synthetic price data for demonstration

    Args:
        days: Number of trading days (2 years = 504 days)

    Returns:
        DataFrame with synthetic OHLCV data
    """
    np.random.seed(42)

    # Generate synthetic price series
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.0005, 0.02, days)))

    # Create OHLCV data
    data = pd.DataFrame({
        'open': prices,
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
        'close': np.roll(prices, -1),  # Next day's open becomes today's close
        'volume': np.random.randint(1000000, 10000000, days)
    }, index=dates)

    # Adjust the last day's close
    data.loc[dates[-1], 'close'] = data.loc[dates[-1], 'open']

    logger.info(f"Created synthetic data with {len(data)} days")
    return data


def progress_callback(status):
    """Progress callback for optimization monitoring"""
    progress_percent = (status.processed_combinations / status.total_combinations) * 100
    logger.info(f"Progress: {progress_percent:.1f}% - "
               f"{status.successful_combinations} successful, "
               f"{status.failed_combinations} failed, "
               f"Memory: {status.memory_usage_gb:.2f}GB, "
               f"ETA: {status.estimated_time_remaining/60:.1f}min")


def demo_basic_optimization():
    """Demonstrate basic optimization functionality"""
    logger.info("=== Basic Optimization Demo ===")

    # Create sample data
    price_data = create_sample_data("AAPL", "1y")

    # Create configuration
    config = BacktestingConfig(
        param_range_start=10,    # Smaller range for demo
        param_range_end=50,
        param_step_size=5,
        max_workers=4,           # Fewer workers for demo
        chunk_size=100,          # Smaller chunks for demo
        memory_limit_gb=2.0      # Lower memory limit for demo
    )

    # Create optimization request
    request = OptimizationRequest(
        strategy_name="rsi_strategy",
        price_data=price_data,
        output_directory="demo_results/basic"
    )

    # Run optimization
    framework = UnifiedBacktestingFramework(config)
    framework.add_progress_callback(progress_callback)

    try:
        framework.start_memory_management()
        logger.info("Starting basic RSI strategy optimization...")

        start_time = time.time()
        results = framework.run_optimization(request)
        total_time = time.time() - start_time

        # Display results
        logger.info(f"Optimization completed in {total_time:.1f} seconds")
        logger.info(f"Success rate: {results.success_rate:.1%}")
        logger.info(f"Top Sharpe ratio: {results.top_sharpe_results[0].sharpe_ratio:.3f}")
        logger.info(f"Best parameters: {results.top_sharpe_results[0].parameters}")

        # Generate report
        report = framework.create_optimization_report(
            results,
            "demo_results/basic/optimization_report.md"
        )
        logger.info("Report generated successfully")

    finally:
        framework.stop_memory_management()


def demo_multi_strategy_optimization():
    """Demonstrate multi-strategy optimization"""
    logger.info("=== Multi-Strategy Optimization Demo ===")

    # Create sample data
    price_data = create_sample_data("SPY", "2y")

    # Create configuration
    config = BacktestingConfig(
        param_range_start=5,
        param_range_end=30,
        param_step_size=5,
        max_workers=6,
        chunk_size=200,
        memory_limit_gb=3.0
    )

    # Create optimization requests for multiple strategies
    requests = [
        OptimizationRequest(
            strategy_name="rsi_strategy",
            price_data=price_data,
            output_directory="demo_results/multi_strategy/rsi"
        ),
        OptimizationRequest(
            strategy_name="macd_strategy",
            price_data=price_data,
            output_directory="demo_results/multi_strategy/macd"
        ),
        OptimizationRequest(
            strategy_name="bollinger_strategy",
            price_data=price_data,
            output_directory="demo_results/multi_strategy/bollinger"
        )
    ]

    # Run multi-strategy optimization
    framework = UnifiedBacktestingFramework(config)
    framework.add_progress_callback(progress_callback)

    try:
        framework.start_memory_management()
        logger.info("Starting multi-strategy optimization...")

        start_time = time.time()
        results = framework.run_multi_strategy_optimization(requests)
        total_time = time.time() - start_time

        # Display results
        logger.info(f"Multi-strategy optimization completed in {total_time:.1f} seconds")
        for strategy_name, result in results.items():
            logger.info(f"{strategy_name}: Sharpe={result.top_sharpe_results[0].sharpe_ratio:.3f}, "
                       f"Return={result.top_sharpe_results[0].total_return:.1%}")

        # Create comparison report
        comparison_report = "# Strategy Comparison Report\n\n"
        for strategy_name, result in results.items():
            comparison_report += f"## {strategy_name}\n"
            comparison_report += f"- Best Sharpe Ratio: {result.top_sharpe_results[0].sharpe_ratio:.3f}\n"
            comparison_report += f"- Best Total Return: {result.top_sharpe_results[0].total_return:.1%}\n"
            comparison_report += f"- Max Drawdown: {result.top_sharpe_results[0].max_drawdown:.1%}\n"
            comparison_report += f"- Success Rate: {result.success_rate:.1%}\n\n"

        with open("demo_results/multi_strategy/strategy_comparison.md", "w") as f:
            f.write(comparison_report)

    finally:
        framework.stop_memory_management()


def demo_quick_optimization():
    """Demonstrate quick optimization function"""
    logger.info("=== Quick Optimization Demo ===")

    # Create sample data
    price_data = create_synthetic_data(252)  # 1 year of synthetic data

    try:
        logger.info("Starting quick RSI optimization...")
        start_time = time.time()

        # Use the quick optimization function
        results = quick_optimization(
            strategy_name="rsi_strategy",
            price_data=price_data,
            param_range=(10, 50, 10),  # Smaller range for quick demo
            max_workers=4,
            output_dir="demo_results/quick"
        )

        total_time = time.time() - start_time

        logger.info(f"Quick optimization completed in {total_time:.1f} seconds")
        logger.info(f"Processed {results.total_combinations} combinations")
        logger.info(f"Best Sharpe: {results.top_sharpe_results[0].sharpe_ratio:.3f}")

    except Exception as e:
        logger.error(f"Quick optimization failed: {str(e)}")


def demo_parameter_space_analysis():
    """Demonstrate parameter space generation and analysis"""
    logger.info("=== Parameter Space Analysis Demo ===")

    from src.unified_backtesting.parameters.generator import ComprehensiveParameterSpace

    # Create parameter space
    config = BacktestingConfig(param_range_start=0, param_range_end=100, param_step_size=10)
    param_space = ComprehensiveParameterSpace(config)

    # Analyze parameter space
    logger.info("Available strategies:")
    for strategy in ["rsi_strategy", "macd_strategy", "bollinger_strategy", "sentiment_strategy"]:
        count = param_space.get_parameter_combinations_count(strategy)
        logger.info(f"  {strategy}: {count:,} combinations")

    # Generate sample combinations
    logger.info("Generating sample RSI parameter combinations...")
    sample_combinations = list(param_space.generate_parameter_combinations("rsi_strategy", limit=10))

    for i, (params, index) in enumerate(sample_combinations):
        logger.info(f"  Combination {index + 1}: {params}")

    # Get parameter information
    param_info = param_space.get_parameter_info()
    logger.info(f"Parameter information: {len(param_info)} parameters available")


def demo_memory_management():
    """Demonstrate memory management features"""
    logger.info("=== Memory Management Demo ===")

    from src.unified_backtesting.memory.manager import AdaptiveMemoryManager

    # Create memory manager
    config = BacktestingConfig(memory_limit_gb=1.0)
    memory_manager = AdaptiveMemoryManager(config)

    try:
        memory_manager.start_memory_management()
        logger.info("Memory management started")

        # Get current memory statistics
        stats = memory_manager.get_comprehensive_stats()
        logger.info(f"Current memory usage: {stats['memory_stats']['process_memory_gb']:.2f}GB")
        logger.info(f"Cache utilization: {stats['cache_stats']['utilization_percent']:.1f}%")

        # Simulate memory pressure
        logger.info("Simulating memory operations...")
        large_data = np.random.random((1000, 1000))  # Allocate memory

        # Check memory again
        stats_after = memory_manager.get_comprehensive_stats()
        logger.info(f"Memory usage after allocation: {stats_after['memory_stats']['process_memory_gb']:.2f}GB")

        # Clear data and check again
        del large_data
        stats_final = memory_manager.get_comprehensive_stats()
        logger.info(f"Memory usage after cleanup: {stats_final['memory_stats']['process_memory_gb']:.2f}GB")

    finally:
        memory_manager.stop_memory_management()


def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="Unified Backtesting Framework Demo")
    parser.add_argument("--strategy", default="rsi_strategy",
                       choices=["rsi_strategy", "macd_strategy", "bollinger_strategy", "all"],
                       help="Strategy to optimize")
    parser.add_argument("--quick", action="store_true", help="Run quick demo only")
    parser.add_argument("--workers", type=int, default=4, help="Number of workers")
    parser.add_argument("--data", default="AAPL", help="Stock ticker or 'synthetic'")

    args = parser.parse_args()

    logger.info("Starting Unified Backtesting Framework Demo")
    logger.info(f"Strategy: {args.strategy}, Workers: {args.workers}")

    # Create output directory
    import os
    os.makedirs("demo_results", exist_ok=True)

    try:
        # Run parameter space analysis
        logger.info("\n" + "="*60)
        demo_parameter_space_analysis()

        # Run memory management demo
        logger.info("\n" + "="*60)
        demo_memory_management()

        if args.quick:
            # Run quick optimization
            logger.info("\n" + "="*60)
            demo_quick_optimization()
        else:
            # Run comprehensive demos
            logger.info("\n" + "="*60)
            demo_basic_optimization()

            if args.strategy == "all":
                logger.info("\n" + "="*60)
                demo_multi_strategy_optimization()

        logger.info("\n" + "="*60)
        logger.info("Demo completed successfully!")
        logger.info("Check demo_results/ directory for output files")

    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()