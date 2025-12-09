#!/usr/bin/env python3
"""
Complete 0700.HK Backtest using Unified Backtesting Framework
Full parameter optimization with performance monitoring
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import sys
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('0700_backtest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import backtesting components
try:
    from src.unified_backtesting.core.engine import UnifiedBacktestEngine
    from src.unified_backtesting.config.strategy_config import StrategyConfig
    from src.unified_backtesting.core.parameter_space import ParameterSpaceGenerator
    from src.unified_backtesting.core.performance_calculator import StandardPerformanceCalculator
except ImportError as e:
    logger.error(f"Failed to import backtesting components: {e}")
    sys.exit(1)


class Complete0700Backtest:
    """Complete 0700.HK backtest using unified framework"""

    def __init__(self):
        self.start_time = time.time()
        self.backtest_id = f"0700_hk_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results = {
            'backtest_id': self.backtest_id,
            'symbol': '0700.HK',
            'start_time': datetime.now().isoformat(),
            'parameters': {},
            'backtest_results': {},
            'performance_metrics': {},
            'best_strategies': [],
            'error_analysis': []
        }

    def prepare_test_data(self):
        """Prepare test data for 0700.HK"""
        logger.info("Preparing 0700.HK test data...")

        try:
            # Try to load existing data first
            data_files = [
                'data/0700_hk_data.csv',
                'data/cache/0700_hk_data.json',
                'data/long_term_storage/0700_hk_data.json'
            ]

            data = None
            for file_path in data_files:
                if Path(file_path).exists():
                    try:
                        if file_path.endswith('.csv'):
                            data = pd.read_csv(file_path, index_col=0, parse_dates=True)
                        else:
                            with open(file_path, 'r') as f:
                                json_data = json.load(f)
                                data = pd.DataFrame(json_data['data'])
                                if 'date' in data.columns:
                                    data['date'] = pd.to_datetime(data['date'])
                                    data.set_index('date', inplace=True)

                        logger.info(f"Loaded data from {file_path}: {len(data)} records")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to load {file_path}: {e}")
                        continue

            if data is None or len(data) < 100:
                logger.warning("Insufficient real data, generating realistic test data")
                data = self._generate_realistic_0700_data()

            # Validate data quality
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_columns if col not in data.columns]
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")

            # Ensure proper data types
            for col in required_columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

            # Drop any NaN values
            data = data.dropna()

            logger.info(f"Final dataset: {len(data)} records from {data.index.min()} to {data.index.max()}")
            return data

        except Exception as e:
            logger.error(f"Error preparing test data: {e}")
            raise

    def _generate_realistic_0700_data(self):
        """Generate realistic 0700.HK test data"""
        logger.info("Generating realistic 0700.HK test data...")

        # Create 2 years of daily data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = dates[dates.weekday < 5]  # Weekdays only

        # Base price around 0700.HK typical range (50-100 HKD)
        np.random.seed(42)  # For reproducibility
        base_price = 75.0
        returns = np.random.normal(0.0005, 0.025, len(dates))  # Daily returns

        # Add some volatility clustering
        volatility = np.ones(len(dates))
        for i in range(10, len(dates)):
            if abs(returns[i-1]) > 0.03:  # Big move
                volatility[i:i+5] = 1.5

        returns *= volatility

        # Generate price series
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        prices = np.array(prices)

        # Generate OHLCV data
        data = []
        for i, (date, close_price) in enumerate(zip(dates, prices)):
            # High and Low around close with some randomness
            daily_range = close_price * np.random.uniform(0.01, 0.04)
            high = close_price + np.random.uniform(0, daily_range)
            low = close_price - np.random.uniform(0, daily_range)

            # Open near previous close with some gap
            if i == 0:
                open_price = close_price
            else:
                gap = np.random.normal(0, close_price * 0.01)
                open_price = prices[i-1] + gap

            # Ensure OHLC relationships are correct
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)

            # Volume (scaled appropriately for HK stocks)
            base_volume = 2000000  # 2M shares base volume
            volume_multiplier = 1 + abs(returns[i]) * 10  # Higher volume on big moves
            volume = int(base_volume * volume_multiplier * np.random.uniform(0.5, 2.0))

            data.append({
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            })

        df = pd.DataFrame(data, index=dates)
        logger.info(f"Generated {len(df)} records of realistic 0700.HK data")
        return df

    def configure_parameter_space(self):
        """Configure parameter space for optimization"""
        logger.info("Configuring parameter space...")

        # CBSC strategy parameters
        parameter_config = {
            'rsi_strategy': {
                'rsi_period': [14, 21, 30],
                'rsi_overbought': [70, 75, 80],
                'rsi_oversold': [20, 25, 30],
                'volume_threshold': [1000000, 2000000, 5000000]
            },
            'macd_strategy': {
                'fast_period': [12, 15, 18],
                'slow_period': [26, 30, 35],
                'signal_period': [9, 12],
                'volume_multiplier': [1.5, 2.0, 3.0]
            },
            'bollinger_strategy': {
                'bb_period': [20, 25, 30],
                'bb_std': [1.5, 2.0, 2.5],
                'rsi_filter': [True, False],
                'volume_confirm': [True, False]
            },
            'sentiment_momentum': {
                'momentum_period': [10, 14, 20],
                'sentiment_threshold': [0.6, 0.7, 0.8],
                'volume_weight': [0.3, 0.5, 0.7]
            }
        }

        # Calculate total combinations
        total_combinations = 1
        for strategy, params in parameter_config.items():
            for param_name, param_values in params.items():
                total_combinations *= len(param_values)

        logger.info(f"Total parameter combinations: {total_combinations:,}")

        # Limit combinations for practical testing
        max_combinations = 1000
        if total_combinations > max_combinations:
            logger.info(f"Limiting to {max_combinations} combinations for practical testing")
            # Reduce parameter ranges
            for strategy, params in parameter_config.items():
                for param_name, param_values in params.items():
                    if len(param_values) > 2:
                        # Keep first, middle, and last values
                        if len(param_values) > 3:
                            step = len(param_values) // 3
                            parameter_config[strategy][param_name] = [
                                param_values[0],
                                param_values[step],
                                param_values[-1]
                            ]
                        else:
                            parameter_config[strategy][param_name] = param_values[:2]

        # Recalculate combinations
        total_combinations = 1
        for strategy, params in parameter_config.items():
            for param_name, param_values in params.items():
                total_combinations *= len(param_values)

        logger.info(f"Final parameter combinations: {total_combinations:,}")

        self.results['parameters'] = {
            'config': parameter_config,
            'total_combinations': total_combinations
        }

        return parameter_config

    def execute_backtest(self, data, parameter_config):
        """Execute the complete backtest"""
        logger.info("Starting complete backtest execution...")

        try:
            # Initialize backtest engine
            engine = UnifiedBacktestEngine(
                data=data,
                symbol='0700.HK',
                initial_capital=1000000,
                commission=0.001,
                slippage=0.0005
            )

            # Initialize parameter space generator
            param_generator = ParameterSpaceGenerator(parameter_config)

            # Execute parameter optimization
            logger.info("Starting parameter optimization...")
            optimization_results = []

            total_combinations = self.results['parameters']['total_combinations']
            processed_count = 0

            for i, params in enumerate(param_generator.generate_combinations()):
                try:
                    # Execute backtest with current parameters
                    strategy_result = engine.run_backtest(params)

                    # Calculate performance metrics
                    perf_calc = StandardPerformanceCalculator()
                    metrics = perf_calc.calculate_all_metrics(strategy_result)

                    # Store results
                    result_entry = {
                        'parameter_set_id': i,
                        'parameters': params,
                        'performance_metrics': metrics,
                        'equity_curve': strategy_result['equity_curve'].tolist() if 'equity_curve' in strategy_result else None,
                        'trades': strategy_result.get('trades', [])
                    }

                    optimization_results.append(result_entry)
                    processed_count += 1

                    # Progress reporting
                    if processed_count % 100 == 0 or processed_count == total_combinations:
                        progress = (processed_count / total_combinations) * 100
                        logger.info(f"Progress: {processed_count}/{total_combinations} ({progress:.1f}%)")

                except Exception as e:
                    logger.error(f"Error in parameter set {i}: {e}")
                    self.results['error_analysis'].append({
                        'parameter_set_id': i,
                        'error': str(e),
                        'parameters': params
                    })
                    continue

            logger.info(f"Completed {processed_count} parameter combinations")

            # Sort results by Sharpe ratio
            optimization_results.sort(
                key=lambda x: x['performance_metrics'].get('sharpe_ratio', -999),
                reverse=True
            )

            self.results['backtest_results'] = {
                'total_processed': processed_count,
                'total_errors': len(self.results['error_analysis']),
                'optimization_results': optimization_results[:50]  # Keep top 50
            }

            return optimization_results

        except Exception as e:
            logger.error(f"Error in backtest execution: {e}")
            raise

    def analyze_results(self, optimization_results):
        """Analyze and summarize backtest results"""
        logger.info("Analyzing backtest results...")

        if not optimization_results:
            logger.error("No optimization results to analyze")
            return

        # Top performers
        top_performers = optimization_results[:10]
        self.results['best_strategies'] = []

        for i, result in enumerate(top_performers):
            metrics = result['performance_metrics']
            strategy_summary = {
                'rank': i + 1,
                'strategy_name': f"Strategy_{result['parameter_set_id']}",
                'parameters': result['parameters'],
                'performance': {
                    'total_return': metrics.get('total_return', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown': metrics.get('max_drawdown', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'profit_factor': metrics.get('profit_factor', 0),
                    'calmar_ratio': metrics.get('calmar_ratio', 0),
                    'total_trades': metrics.get('total_trades', 0)
                }
            }
            self.results['best_strategies'].append(strategy_summary)

        # Overall statistics
        all_sharpe_ratios = [r['performance_metrics'].get('sharpe_ratio', 0) for r in optimization_results]
        all_returns = [r['performance_metrics'].get('total_return', 0) for r in optimization_results]
        all_drawdowns = [r['performance_metrics'].get('max_drawdown', 0) for r in optimization_results]

        self.results['performance_metrics'] = {
            'best_sharpe_ratio': max(all_sharpe_ratios),
            'worst_sharpe_ratio': min(all_sharpe_ratios),
            'average_sharpe_ratio': np.mean(all_sharpe_ratios),
            'best_return': max(all_returns),
            'worst_return': min(all_returns),
            'average_return': np.mean(all_returns),
            'average_max_drawdown': np.mean(all_drawdowns),
            'profitable_strategies': len([r for r in all_returns if r > 0]),
            'total_strategies_tested': len(optimization_results)
        }

        # Parameter analysis
        self._analyze_parameter_impact(optimization_results)

    def _analyze_parameter_impact(self, optimization_results):
        """Analyze impact of different parameters on performance"""
        logger.info("Analyzing parameter impact...")

        parameter_impact = {}

        # Analyze each parameter type
        all_params = optimization_results[0]['parameters'].keys()

        for param_name in all_params:
            param_values = {}
            for result in optimization_results:
                param_value = str(result['parameters'][param_name])
                sharpe_ratio = result['performance_metrics'].get('sharpe_ratio', 0)

                if param_value not in param_values:
                    param_values[param_value] = []
                param_values[param_value].append(sharpe_ratio)

            # Calculate average performance for each parameter value
            param_analysis = {}
            for value, ratios in param_values.items():
                param_analysis[value] = {
                    'count': len(ratios),
                    'avg_sharpe': np.mean(ratios),
                    'max_sharpe': max(ratios),
                    'min_sharpe': min(ratios)
                }

            parameter_impact[param_name] = param_analysis

        self.results['parameter_analysis'] = parameter_impact

    def save_results(self):
        """Save complete backtest results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"0700_hk_complete_backtest_{timestamp}.json"

        try:
            # Add final metadata
            self.results['end_time'] = datetime.now().isoformat()
            self.results['total_duration'] = time.time() - self.start_time
            self.results['status'] = 'completed'

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Results saved to: {results_file}")
            return results_file

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return None

    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "=" * 80)
        print("0700.HK COMPLETE BACKTEST RESULTS")
        print("=" * 80)

        # Basic info
        print(f"Backtest ID: {self.results['backtest_id']}")
        print(f"Symbol: {self.results['symbol']}")
        print(f"Total Duration: {self.results.get('total_duration', 0):.2f} seconds")
        print(f"Status: {self.results.get('status', 'unknown').upper()}")

        # Parameter testing
        total_params = self.results['parameters']['total_combinations']
        processed = self.results['backtest_results']['total_processed']
        errors = self.results['backtest_results']['total_errors']

        print(f"\nParameter Testing:")
        print(f"  Total Combinations: {total_params:,}")
        print(f"  Successfully Processed: {processed:,}")
        print(f"  Errors: {errors:,}")
        print(f"  Success Rate: {(processed/total_params*100):.1f}%")

        # Performance overview
        perf_metrics = self.results['performance_metrics']
        print(f"\nPerformance Overview:")
        print(f"  Best Sharpe Ratio: {perf_metrics['best_sharpe_ratio']:.3f}")
        print(f"  Average Sharpe Ratio: {perf_metrics['average_sharpe_ratio']:.3f}")
        print(f"  Best Total Return: {perf_metrics['best_return']:.2%}")
        print(f"  Average Return: {perf_metrics['average_return']:.2%}")
        print(f"  Average Max Drawdown: {perf_metrics['average_max_drawdown']:.2%}")
        print(f"  Profitable Strategies: {perf_metrics['profitable_strategies']:,}/{perf_metrics['total_strategies_tested']:,}")

        # Top 5 strategies
        print(f"\nTop 5 Strategies:")
        for strategy in self.results['best_strategies'][:5]:
            perf = strategy['performance']
            print(f"  {strategy['rank']}. Sharpe: {perf['sharpe_ratio']:.3f}, "
                  f"Return: {perf['total_return']:.2%}, "
                  f"Win Rate: {perf['win_rate']:.1%}, "
                  f"Trades: {perf['total_trades']}")

        # Best strategy details
        if self.results['best_strategies']:
            best_strategy = self.results['best_strategies'][0]
            print(f"\nBest Strategy Details:")
            print(f"  Strategy ID: {best_strategy['strategy_name']}")
            print(f"  Parameters: {best_strategy['parameters']}")
            print(f"  Performance:")
            perf = best_strategy['performance']
            print(f"    Total Return: {perf['total_return']:.2%}")
            print(f"    Sharpe Ratio: {perf['sharpe_ratio']:.3f}")
            print(f"    Max Drawdown: {perf['max_drawdown']:.2%}")
            print(f"    Win Rate: {perf['win_rate']:.1%}")
            print(f"    Profit Factor: {perf['profit_factor']:.2f}")
            print(f"    Calmar Ratio: {perf['calmar_ratio']:.3f}")

    async def run_complete_backtest(self):
        """Run the complete backtest process"""
        try:
            logger.info("Starting complete 0700.HK backtest...")

            # Step 1: Prepare data
            data = self.prepare_test_data()

            # Step 2: Configure parameters
            parameter_config = self.configure_parameter_space()

            # Step 3: Execute backtest
            optimization_results = self.execute_backtest(data, parameter_config)

            # Step 4: Analyze results
            self.analyze_results(optimization_results)

            # Step 5: Save results
            results_file = self.save_results()

            # Step 6: Print summary
            self.print_summary()

            return results_file

        except Exception as e:
            logger.error(f"Complete backtest failed: {e}")
            traceback.print_exc()
            self.results['status'] = 'failed'
            self.results['error'] = str(e)
            return None


async def main():
    """Main execution function"""
    print("0700.HK Complete Backtest using Unified Framework")
    print("=" * 60)

    backtest = Complete0700Backtest()

    try:
        results_file = await backtest.run_complete_backtest()

        if results_file:
            print(f"\nDetailed results saved to: {results_file}")
            return True
        else:
            print("\nBacktest failed - no results file generated")
            return False

    except Exception as e:
        print(f"\nBacktest execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)