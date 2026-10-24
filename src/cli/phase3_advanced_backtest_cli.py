#!/usr/bin/env python3
"""
Phase 3: Advanced CLI for 5+ Year Backtesting with VectorBT Optimization
======================================================================

Professional command-line interface for high-performance long-term backtesting.
Supports chunked processing, parallel execution, and advanced performance monitoring.

Features:
- Simple and professional CLI modes
- Batch processing capabilities
- Real-time progress monitoring
- Performance benchmarking
- Advanced configuration options
- Professional reporting

Author: Claude Code Assistant
Date: 2025-11-29
Phase: 3 - Enhanced CLI Commands
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backtest.phase3_optimized_vectorbt_engine import (
    Phase3OptimizedVectorBTEngine,
    Phase3BacktestConfig,
    ChunkedProcessingConfig,
    run_optimized_long_term_backtest
)
from src.cli.cli_utils import setup_logging, print_banner, format_results_table

# Import strategy modules
try:
    from simplified_system.src.strategies.technical_indicators import TechnicalIndicatorStrategies
    STRATEGIES_AVAILABLE = True
except ImportError:
    STRATEGIES_AVAILABLE = False

logger = logging.getLogger(__name__)


class AdvancedBacktestCLI:
    """Advanced CLI for 5+ year backtesting"""

    def __init__(self):
        self.config = None
        self.results = None

    def setup_argument_parser(self) -> argparse.ArgumentParser:
        """Setup comprehensive argument parser"""

        parser = argparse.ArgumentParser(
            description="Phase 3: Advanced 5+ Year Backtesting CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Simple 5-year backtest
  python phase3_advanced_backtest_cli.py --symbol 0700.HK --years 5 --strategy rsi_mean_reversion

  # Professional mode with optimizations
  python phase3_advanced_backtest_cli.py --symbol 0700.HK --start-date 2018-01-01 --end-date 2023-12-31 \\
    --strategy custom --chunk-size 3 --parallel --memory-limit 6 --output results/

  # Batch processing multiple symbols
  python phase3_advanced_backtest_cli.py --symbols 0700.HK,0941.HK,1299.HK --years 5 \\
    --strategy momentum --batch-mode --output batch_results/

  # Performance benchmarking
  python phase3_advanced_backtest_cli.py --symbol 0700.HK --years 10 \\
    --strategy rsi_mean_reversion --benchmark --verbose
            """
        )

        # Basic arguments
        parser.add_argument(
            '--symbol', '-s',
            type=str,
            help='Stock symbol (e.g., 0700.HK)'
        )
        parser.add_argument(
            '--symbols',
            type=str,
            help='Multiple symbols for batch processing (comma-separated)'
        )
        parser.add_argument(
            '--start-date',
            type=lambda d: datetime.strptime(d, '%Y-%m-%d'),
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--end-date',
            type=lambda d: datetime.strptime(d, '%Y-%m-%d'),
            default=datetime.now(),
            help='End date (YYYY-MM-DD, default: today)'
        )
        parser.add_argument(
            '--years', '-y',
            type=int,
            help='Number of years of data to use (overrides start-date)'
        )

        # Strategy arguments
        parser.add_argument(
            '--strategy',
            choices=['rsi_mean_reversion', 'momentum', 'mean_reversion', 'trend_following', 'custom'],
            default='rsi_mean_reversion',
            help='Trading strategy to test'
        )
        parser.add_argument(
            '--strategy-file',
            type=str,
            help='Python file containing custom strategy function'
        )
        parser.add_argument(
            '--strategy-params',
            type=str,
            help='Strategy parameters as JSON string'
        )

        # Performance optimization arguments
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=2,
            help='Data chunk size in years (default: 2)'
        )
        parser.add_argument(
            '--memory-limit',
            type=float,
            default=4.0,
            help='Memory limit in GB (default: 4.0)'
        )
        parser.add_argument(
            '--parallel',
            action='store_true',
            help='Enable parallel processing'
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            help='Maximum number of worker processes'
        )
        parser.add_argument(
            '--low-memory',
            action='store_true',
            help='Enable low-memory mode'
        )
        parser.add_argument(
            '--disable-vectorbt',
            action='store_true',
            help='Disable VectorBT optimizations'
        )

        # Processing options
        parser.add_argument(
            '--batch-mode',
            action='store_true',
            help='Run in batch processing mode'
        )
        parser.add_argument(
            '--save-intermediate',
            action='store_true',
            help='Save intermediate chunk results'
        )
        parser.add_argument(
            '--intermediate-path',
            type=str,
            default='intermediate_results',
            help='Path for intermediate results'
        )

        # Output options
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='backtest_results',
            help='Output directory for results'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'csv', 'excel', 'all'],
            default='json',
            help='Output format'
        )
        parser.add_argument(
            '--save-plots',
            action='store_true',
            help='Save performance plots'
        )
        parser.add_argument(
            '--report-template',
            choices=['simple', 'detailed', 'professional'],
            default='detailed',
            help='Report template'
        )

        # Monitoring and debugging
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        parser.add_argument(
            '--benchmark',
            action='store_true',
            help='Run performance benchmarking'
        )
        parser.add_argument(
            '--profile',
            action='store_true',
            help='Enable performance profiling'
        )
        parser.add_argument(
            '--log-file',
            type=str,
            help='Log file path'
        )

        # Configuration
        parser.add_argument(
            '--config-file',
            type=str,
            help='Configuration file path (JSON)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform dry run without executing backtest'
        )

        return parser

    def create_config(self, args: argparse.Namespace) -> Phase3BacktestConfig:
        """Create configuration from arguments"""

        # Chunked processing config
        chunked_config = ChunkedProcessingConfig(
            max_memory_usage_gb=args.memory_limit,
            chunk_size_years=args.chunk_size,
            enable_parallel=args.parallel,
            max_workers=args.max_workers,
            use_low_memory_mode=args.low_memory,
            enable_vectorbt_optimization=not args.disable_vectorbt,
            enable_chunk_caching=args.save_intermediate,
            cache_directory=args.intermediate_path if args.save_intermediate else None
        )

        # Main configuration
        config = Phase3BacktestConfig(
            chunked_config=chunked_config,
            enable_real_time_progress=args.verbose,
            save_intermediate_results=args.save_intermediate,
            intermediate_results_path=args.intermediate_path if args.save_intermediate else None,
            enable_data_validation=True,
            enable_result_verification=True,
            enable_performance_monitoring=True
        )

        # Override with config file if provided
        if args.config_file:
            config = self._load_config_from_file(args.config_file, config)

        return config

    def _load_config_from_file(self, config_path: str,
                              default_config: Phase3BacktestConfig) -> Phase3BacktestConfig:
        """Load configuration from JSON file"""

        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            # Update chunked config
            if 'chunked_config' in config_data:
                for key, value in config_data['chunked_config'].items():
                    if hasattr(default_config.chunked_config, key):
                        setattr(default_config.chunked_config, key, value)

            # Update main config
            for key, value in config_data.items():
                if key != 'chunked_config' and hasattr(default_config, key):
                    setattr(default_config, key, value)

            logger.info(f"Configuration loaded from {config_path}")
            return default_config

        except Exception as e:
            logger.warning(f"Failed to load config file {config_path}: {e}")
            return default_config

    def prepare_data_range(self, args: argparse.Namespace) -> tuple[datetime, datetime]:
        """Prepare start and end dates from arguments"""

        if args.start_date and args.end_date:
            return args.start_date, args.end_date

        if args.years:
            end_date = args.end_date or datetime.now()
            start_date = end_date - timedelta(days=args.years * 365)
            return start_date, end_date

        # Default to 5 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5 * 365)
        return start_date, end_date

    def get_strategy_function(self, args: argparse.Namespace):
        """Get strategy function based on arguments"""

        strategy_params = {}
        if args.strategy_params:
            try:
                strategy_params = json.loads(args.strategy_params)
            except json.JSONDecodeError:
                logger.error(f"Invalid strategy parameters: {args.strategy_params}")
                sys.exit(1)

        if args.strategy == 'custom' and args.strategy_file:
            return self._load_custom_strategy(args.strategy_file, strategy_params)

        elif STRATEGIES_AVAILABLE:
            if args.strategy == 'rsi_mean_reversion':
                return TechnicalIndicatorStrategies.rsi_mean_reversion
            elif args.strategy == 'momentum':
                return TechnicalIndicatorStrategies.momentum
            elif args.strategy == 'mean_reversion':
                return TechnicalIndicatorStrategies.mean_reversion
            elif args.strategy == 'trend_following':
                return TechnicalIndicatorStrategies.trend_following

        # Fallback to sample strategies
        from src.backtest.phase3_optimized_vectorbt_engine import sample_rsi_strategy, sample_momentum_strategy

        if args.strategy == 'rsi_mean_reversion':
            return lambda data, **kwargs: sample_rsi_strategy(data, **strategy_params)
        elif args.strategy == 'momentum':
            return lambda data, **kwargs: sample_momentum_strategy(data, **strategy_params)
        else:
            logger.error(f"Strategy {args.strategy} not available")
            sys.exit(1)

    def _load_custom_strategy(self, strategy_file: str, params: Dict[str, Any]):
        """Load custom strategy from Python file"""

        try:
            # Add strategy file directory to path
            strategy_dir = os.path.dirname(os.path.abspath(strategy_file))
            if strategy_dir not in sys.path:
                sys.path.insert(0, strategy_dir)

            # Import strategy module
            module_name = os.path.splitext(os.path.basename(strategy_file))[0]
            strategy_module = __import__(module_name)

            # Look for strategy function
            if hasattr(strategy_module, 'strategy_function'):
                strategy_func = strategy_module.strategy_function
            elif hasattr(strategy_module, 'main_strategy'):
                strategy_func = strategy_module.main_strategy
            else:
                raise ValueError("Strategy file must contain 'strategy_function' or 'main_strategy'")

            logger.info(f"Loaded custom strategy from {strategy_file}")
            return lambda data, **kwargs: strategy_func(data, **{**params, **kwargs})

        except Exception as e:
            logger.error(f"Failed to load custom strategy from {strategy_file}: {e}")
            sys.exit(1)

    async def run_single_backtest(self, symbol: str, start_date: datetime,
                                end_date: datetime, strategy_func,
                                config: Phase3BacktestConfig) -> Dict[str, Any]:
        """Run single backtest"""

        print(f"\n{'='*60}")
        print(f"Running Advanced Backtest for {symbol}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Data Points: ~{(end_date - start_date).days // 1:.0f} days")
        print(f"Chunk Size: {config.chunked_config.chunk_size_years} years")
        print(f"Memory Limit: {config.chunked_config.max_memory_usage_gb} GB")
        print(f"Parallel Processing: {config.chunked_config.enable_parallel}")
        print(f"{'='*60}\n")

        if config.chunked_config.enable_parallel:
            print(f"Using {config.chunked_config.max_workers or 'auto'} worker processes")

        # Create and initialize engine
        engine = Phase3OptimizedVectorBTEngine(config)

        try:
            await engine.initialize()

            # Run backtest
            start_time = datetime.now()
            results = await engine.run_optimized_backtest(
                symbol, start_date, end_date, strategy_func
            )
            end_time = datetime.now()

            # Add metadata
            results['metadata'] = {
                'symbol': symbol,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'execution_time': (end_time - start_time).total_seconds(),
                'config_used': {
                    'chunk_size_years': config.chunked_config.chunk_size_years,
                    'max_memory_gb': config.chunked_config.max_memory_usage_gb,
                    'parallel_processing': config.chunked_config.enable_parallel,
                    'vectorbt_optimization': config.chunked_config.enable_vectorbt_optimization
                }
            }

            # Get performance report
            results['performance_report'] = await engine.get_performance_report()

            return results

        finally:
            await engine.cleanup()

    async def run_batch_backtest(self, symbols: List[str], start_date: datetime,
                               end_date: datetime, strategy_func,
                               config: Phase3BacktestConfig) -> Dict[str, Any]:
        """Run batch backtest for multiple symbols"""

        print(f"\n{'='*60}")
        print(f"Running Batch Advanced Backtest")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"Total Symbols: {len(symbols)}")
        print(f"{'='*60}\n")

        batch_results = {
            'batch_info': {
                'symbols': symbols,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_symbols': len(symbols)
            },
            'results': {},
            'summary': {}
        }

        # Process symbols sequentially (or implement parallel processing across symbols)
        for i, symbol in enumerate(symbols, 1):
            print(f"\nProcessing Symbol {i}/{len(symbols)}: {symbol}")

            try:
                result = await self.run_single_backtest(
                    symbol, start_date, end_date, strategy_func, config
                )
                batch_results['results'][symbol] = result

                # Print summary
                print(f"\n✓ {symbol} Results:")
                print(f"  Total Return: {result['total_return']:.2%}")
                print(f"  Sharpe Ratio: {result['sharpe_ratio']:.2f}")
                print(f"  Max Drawdown: {result['max_drawdown']:.2%}")
                print(f"  Processing Time: {result['processing_time']:.2f}s")

            except Exception as e:
                logger.error(f"Failed to backtest {symbol}: {e}")
                batch_results['results'][symbol] = {
                    'error': str(e),
                    'symbol': symbol
                }

        # Calculate batch summary
        successful_results = [r for r in batch_results['results'].values() if 'error' not in r]
        if successful_results:
            batch_results['summary'] = {
                'successful_backtests': len(successful_results),
                'failed_backtests': len(symbols) - len(successful_results),
                'average_return': sum(r['total_return'] for r in successful_results) / len(successful_results),
                'average_sharpe': sum(r['sharpe_ratio'] for r in successful_results) / len(successful_results),
                'best_performer': max(successful_results, key=lambda x: x['total_return']),
                'worst_performer': min(successful_results, key=lambda x: x['total_return'])
            }

        return batch_results

    def save_results(self, results: Dict[str, Any], output_dir: str,
                    format_type: str, symbol: str = None) -> None:
        """Save results in specified format"""

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_filename = f"backtest_{symbol}_{timestamp}" if symbol else f"backtest_batch_{timestamp}"

        if format_type in ['json', 'all']:
            json_file = os.path.join(output_dir, f"{base_filename}.json")
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✓ Results saved to {json_file}")

        if format_type in ['csv', 'all'] and 'results' in results:
            csv_file = os.path.join(output_dir, f"{base_filename}.csv")

            # Convert results to DataFrame
            if 'batch_info' in results:  # Batch results
                summary_data = []
                for symbol, result in results['results'].items():
                    if 'error' not in result:
                        summary_data.append({
                            'Symbol': symbol,
                            'Total Return': result.get('total_return', 0),
                            'Annualized Return': result.get('annualized_return', 0),
                            'Sharpe Ratio': result.get('sharpe_ratio', 0),
                            'Max Drawdown': result.get('max_drawdown', 0),
                            'Volatility': result.get('volatility', 0),
                            'Processing Time': result.get('processing_time', 0)
                        })

                df = pd.DataFrame(summary_data)
                df.to_csv(csv_file, index=False)
            else:  # Single results
                # Create summary dataframe
                summary_data = [{
                    'Metric': 'Total Return',
                    'Value': results.get('total_return', 0),
                    'Format': 'percentage'
                }, {
                    'Metric': 'Annualized Return',
                    'Value': results.get('annualized_return', 0),
                    'Format': 'percentage'
                }, {
                    'Metric': 'Sharpe Ratio',
                    'Value': results.get('sharpe_ratio', 0),
                    'Format': 'ratio'
                }, {
                    'Metric': 'Max Drawdown',
                    'Value': results.get('max_drawdown', 0),
                    'Format': 'percentage'
                }, {
                    'Metric': 'Volatility',
                    'Value': results.get('volatility', 0),
                    'Format': 'percentage'
                }]

                df = pd.DataFrame(summary_data)
                df.to_csv(csv_file, index=False)

            print(f"✓ CSV summary saved to {csv_file}")

        if format_type in ['excel', 'all']:
            excel_file = os.path.join(output_dir, f"{base_filename}.xlsx")

            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                if 'batch_info' in results:  # Batch results
                    # Summary sheet
                    summary_data = []
                    for symbol, result in results['results'].items():
                        if 'error' not in result:
                            summary_data.append({
                                'Symbol': symbol,
                                'Total Return': result.get('total_return', 0),
                                'Annualized Return': result.get('annualized_return', 0),
                                'Sharpe Ratio': result.get('sharpe_ratio', 0),
                                'Max Drawdown': result.get('max_drawdown', 0),
                                'Volatility': result.get('volatility', 0),
                                'Processing Time': result.get('processing_time', 0)
                            })

                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)

                    # Individual symbol sheets
                    for symbol, result in results['results'].items():
                        if 'error' not in result:
                            symbol_data = {
                                'Metric': ['Total Return', 'Annualized Return', 'Sharpe Ratio',
                                         'Max Drawdown', 'Volatility', 'Processing Time'],
                                'Value': [result.get('total_return', 0),
                                         result.get('annualized_return', 0),
                                         result.get('sharpe_ratio', 0),
                                         result.get('max_drawdown', 0),
                                         result.get('volatility', 0),
                                         result.get('processing_time', 0)]
                            }
                            symbol_df = pd.DataFrame(symbol_data)
                            safe_sheet_name = symbol.replace('.', '_')[:31]  # Excel sheet name limit
                            symbol_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)

                else:  # Single results
                    summary_data = pd.DataFrame({
                        'Metric': ['Total Return', 'Annualized Return', 'Sharpe Ratio',
                                 'Max Drawdown', 'Volatility', 'Processing Time'],
                        'Value': [results.get('total_return', 0),
                                 results.get('annualized_return', 0),
                                 results.get('sharpe_ratio', 0),
                                 results.get('max_drawdown', 0),
                                 results.get('volatility', 0),
                                 results.get('processing_time', 0)]
                    })
                    summary_data.to_excel(writer, sheet_name='Results', index=False)

            print(f"✓ Excel report saved to {excel_file}")

    def print_results_summary(self, results: Dict[str, Any]) -> None:
        """Print formatted results summary"""

        print(f"\n{'='*60}")
        print("BACKTEST RESULTS SUMMARY")
        print(f"{'='*60}")

        if 'batch_info' in results:  # Batch results
            print(f"\nBatch Summary:")
            print(f"  Total Symbols: {results['batch_info']['total_symbols']}")
            if 'summary' in results:
                summary = results['summary']
                print(f"  Successful: {summary['successful_backtests']}")
                print(f"  Failed: {summary['failed_backtests']}")
                print(f"  Average Return: {summary['average_return']:.2%}")
                print(f"  Average Sharpe: {summary['average_sharpe']:.2f}")

                if 'best_performer' in summary:
                    best = summary['best_performer']
                    print(f"  Best Performer: {best['symbol']} ({best['total_return']:.2%})")

                if 'worst_performer' in summary:
                    worst = summary['worst_performer']
                    print(f"  Worst Performer: {worst['symbol']} ({worst['total_return']:.2%})")

            # Individual results table
            print(f"\nIndividual Results:")
            print("-" * 80)
            print(f"{'Symbol':<12} {'Return':<10} {'Sharpe':<8} {'MaxDD':<10} {'Time(s)':<8}")
            print("-" * 80)

            for symbol, result in results['results'].items():
                if 'error' not in result:
                    print(f"{symbol:<12} {result['total_return']:<10.2%} "
                          f"{result['sharpe_ratio']:<8.2f} {result['max_drawdown']:<10.2%} "
                          f"{result['processing_time']:<8.1f}")
                else:
                    print(f"{symbol:<12} {'ERROR':<10} {'-':<8} {'-':<10} {'-':<8}")

        else:  # Single results
            print(f"\nPerformance Metrics:")
            print(f"  Total Return: {results.get('total_return', 0):.2%}")
            print(f"  Annualized Return: {results.get('annualized_return', 0):.2%}")
            print(f"  Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}")
            print(f"  Max Drawdown: {results.get('max_drawdown', 0):.2%}")
            print(f"  Volatility: {results.get('volatility', 0):.2%}")
            print(f"  Processing Time: {results.get('processing_time', 0):.2f} seconds")
            print(f"  Processing Speed: {results.get('processing_speed', 0):.0f} points/sec")

        # Performance report
        if 'performance_report' in results:
            perf_report = results['performance_report']
            print(f"\nPerformance Report:")
            print(f"  Peak Memory Usage: {perf_report['memory_performance']['peak_memory_gb']:.2f} GB")
            print(f"  Memory Efficiency: {perf_report['memory_performance']['memory_efficiency']:.2f}x")
            print(f"  Chunks Processed: {perf_report['processing_summary']['chunks_processed']}")

        print(f"\n{'='*60}")

    async def run(self, args: argparse.Namespace) -> None:
        """Main CLI execution method"""

        # Setup logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        setup_logging(log_level, args.log_file)

        print_banner("Phase 3: Advanced 5+ Year Backtesting")

        # Dry run mode
        if args.dry_run:
            print("DRY RUN MODE - No actual backtesting will be performed")
            print(f"Configuration would be applied with chunk size: {args.chunk_size} years")
            print(f"Memory limit: {args.memory_limit} GB")
            print(f"Parallel processing: {args.parallel}")
            return

        # Create configuration
        self.config = self.create_config(args)

        # Prepare data range
        start_date, end_date = self.prepare_data_range(args)

        # Validate data requirements
        data_years = (end_date - start_date).days / 365.25
        if data_years < 5:
            print(f"Warning: Data period {data_years:.1f} years is less than recommended 5+ years for long-term analysis")

        # Get strategy function
        strategy_func = self.get_strategy_function(args)

        # Run backtest(s)
        try:
            if args.batch_mode or args.symbols:
                # Batch processing
                symbols = args.symbols.split(',') if args.symbols else [args.symbol]
                symbols = [s.strip() for s in symbols]

                results = await self.run_batch_backtest(
                    symbols, start_date, end_date, strategy_func, self.config
                )
            else:
                # Single symbol processing
                if not args.symbol:
                    print("Error: --symbol or --symbols required for single backtest mode")
                    sys.exit(1)

                results = await self.run_single_backtest(
                    args.symbol, start_date, end_date, strategy_func, self.config
                )

            self.results = results

            # Print results
            self.print_results_summary(results)

            # Save results
            self.save_results(
                results, args.output, args.format,
                args.symbol if not (args.batch_mode or args.symbols) else None
            )

            # Save plots if requested
            if args.save_plots and 'equity' in results:
                self.save_performance_plots(results, args.output)

        except KeyboardInterrupt:
            print("\nBacktesting interrupted by user")
            sys.exit(1)
        except Exception as e:
            logger.exception(f"Backtesting failed: {e}")
            sys.exit(1)

    def save_performance_plots(self, results: Dict[str, Any], output_dir: str) -> None:
        """Save performance plots if available"""

        try:
            import matplotlib.pyplot as plt

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Equity curve plot
            if 'equity' in results:
                plt.figure(figsize=(12, 6))
                results['equity'].plot(title='Equity Curve')
                plt.ylabel('Portfolio Value')
                plt.xlabel('Date')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                plot_file = os.path.join(output_dir, f"equity_curve_{timestamp}.png")
                plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"✓ Equity curve plot saved to {plot_file}")

            # Returns distribution plot
            if 'returns' in results:
                plt.figure(figsize=(12, 6))
                results['returns'].hist(bins=50, alpha=0.7, edgecolor='black')
                plt.title('Daily Returns Distribution')
                plt.xlabel('Daily Return')
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                plot_file = os.path.join(output_dir, f"returns_distribution_{timestamp}.png")
                plt.savefig(plot_file, dpi=300, bbox_inches='tight')
                plt.close()
                print(f"✓ Returns distribution plot saved to {plot_file}")

        except ImportError:
            logger.warning("Matplotlib not available, plots not saved")
        except Exception as e:
            logger.warning(f"Failed to save plots: {e}")


def main():
    """Main CLI entry point"""

    cli = AdvancedBacktestCLI()
    parser = cli.setup_argument_parser()
    args = parser.parse_args()

    # Validate arguments
    if not args.symbol and not args.symbols:
        print("Error: --symbol or --symbols required")
        sys.exit(1)

    if args.strategy == 'custom' and not args.strategy_file:
        print("Error: --strategy-file required when using custom strategy")
        sys.exit(1)

    # Run CLI
    asyncio.run(cli.run(args))


if __name__ == "__main__":
    main()