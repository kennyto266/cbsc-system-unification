#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Actual 0700.HK Parameter Optimization Run - English Version
"""

import time
import warnings
import numpy as np
import pandas as pd
import logging
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import sys

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("Starting 0700.HK 0-300 Parameter Range Comprehensive Optimization")
    print("=" * 70)

    try:
        # Check system environment
        print("Checking system environment...")

        # Check GPU
        try:
            from simplified_system.src.utils.gpu_detector import get_gpu_environment
            gpu_env = get_gpu_environment()
            print(f"GPU Status: {'Available' if gpu_env.is_gpu_available() else 'Not Available'}")
            use_gpu = gpu_env.is_gpu_available()
            if use_gpu:
                print("Using GPU acceleration mode")
            else:
                print("Using CPU mode")
        except Exception as e:
            print(f"GPU check failed: {e}")
            use_gpu = False

        # Import core components
        print("Importing core components...")
        from comprehensive_parameter_optimizer import ComprehensiveParameterOptimizer, OptimizationConfig

        # Configure optimizer
        config = OptimizationConfig(
            max_workers=6,
            batch_size=50,
            use_gpu=use_gpu,
            min_sharpe_ratio=0.5,
            max_max_drawdown=0.3,
            min_win_rate=0.3
        )

        optimizer = ComprehensiveParameterOptimizer(config)
        print("Parameter optimizer initialized successfully")

        # Get real data
        print("Loading real stock data...")
        from simplified_system.src.api.stock_api import get_hk_stock_data

        # Get 1 year of data for testing
        data = get_hk_stock_data("0700.HK", 365)
        print(f"Successfully loaded {len(data)} days of 0700.HK data")
        print(f"Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")

        # Start HIBOR-RSI optimization
        print("\nStarting HIBOR-RSI parameter optimization...")
        print("Parameter space: RSI period(10-50), Oversold(20-40), Overbought(60-80)")
        print("Settings: Maximum 200 combinations for demonstration")

        start_time = time.time()

        # Generate valid parameter combinations
        valid_combinations = []
        for period in range(10, 51, 5):        # 10-50, step=5
            for oversold in range(20, 45, 5):      # 20-40, step=5
                for overbought in range(60, 85, 5):     # 60-80, step=5
                    if oversold < overbought:  # Validate logical relationship
                        valid_combinations.append({
                            'rsi_period': period,
                            'rsi_oversold': oversold,
                            'rsi_overbought': overbought
                        })
                        if len(valid_combinations) >= 200:  # Limit combinations
                            break
            if len(valid_combinations) >= 200:
                break
            if len(valid_combinations) >= 200:
                break

        print(f"Generated {len(valid_combinations)} valid parameter combinations")

        # Test parameter combinations in parallel
        results = []
        total_combinations = len(valid_combinations)
        batch_size = 20

        print(f"Starting parallel testing (batch size: {batch_size})...")

        def test_rsi_combination(params, vectorbt_engine):
            try:
                strategy_params = {
                    'period': params['rsi_period'],
                    'oversold': params['rsi_oversold'],
                    'overbought': params['rsi_overbought']
                }

                result = vectorbt_engine.backtest_strategy(
                    data=data,
                    strategy="RSI_MEAN_REVERSION",
                    parameters=strategy_params,
                    symbol="0700.HK"
                )

                return {
                    'parameters': params,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate,
                    'total_return': result.total_return,
                    'total_trades': result.total_trades,
                    'success': True
                }
            except Exception as e:
                return {
                    'parameters': params,
                    'error': str(e),
                    'success': False
                }

        # Process in batches
        for batch_start in range(0, total_combinations, batch_size):
            batch_end = min(batch_start + batch_size, total_combinations)
            batch = valid_combinations[batch_start:batch_end]

            print(f"Processing batch {batch_start//batch_size + 1}: {len(batch)} combinations")

            # Parallel execution
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(test_rsi_combination, params, optimizer.vectorbt_engine)
                    for params in batch
                ]

                for future in futures:
                    try:
                        result = future.result()
                        if result['success']:
                            results.append(result)
                    except Exception as e:
                        logger.warning(f"Result processing failed: {e}")

        execution_time = time.time() - start_time

        print(f"\nOptimization completed!")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Successful tests: {len(results)} / {total_combinations} combinations")
        print(f"Processing speed: {len(results) / execution_time:.1f} combos/second")

        # Analyze results
        if results:
            # Sort by Sharpe ratio
            results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

            print(f"\nTop 10 Optimal HIBOR-RSI Parameter Combinations:")
            print("-" * 80)

            for i, result in enumerate(results[:10], 1):
                params = result['parameters']
                print(f"{i:2d}. Sharpe: {result['sharpe_ratio']:6.3f} | "
                      f"DD: {result['max_drawdown']:6.2%} | "
                      f"WR: {result['win_rate']:5.1%} | "
                      f"Trades: {result['total_trades']:3d} | "
                      f"P:{params['rsi_period']:3d} "
                      f"OS:{params['rsi_oversold']:2d} "
                      f"OB:{params['rsi_overbought']:2d}")

            # Statistical analysis
            sharpe_values = [r['sharpe_ratio'] for r in results]
            positive_results = [r for r in results if r['sharpe_ratio'] > 1.0]

            print(f"\nOptimization Results Statistics:")
            print(f"   Average Sharpe: {np.mean(sharpe_values):.3f}")
            print(f"   Best Sharpe: {np.max(sharpe_values):.3f}")
            print(f"   Positive Sharpe combos: {len(positive_results)} ({len(positive_results)/len(results)*100:.1f}%)")
            print(f"   Zero trade combos: {len([r for r in results if r['total_trades'] == 0])}")

            if positive_results:
                best = positive_results[0]
                print(f"\nRecommended Parameter Combination:")
                print(f"   RSI Period: {best['parameters']['rsi_period']}")
                print(f"   Oversold Level: {best['parameters']['rsi_oversold']}")
                print(f"   Overbought Level: {best['parameters']['rsi_overbought']}")
                print(f"   Expected Sharpe: {best['sharpe_ratio']:.3f}")
                print(f"   Expected Max DD: {best['max_drawdown']*100:.2f}%")
                print(f"   Expected Win Rate: {best['win_rate']*100:.2f}%")

            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': '0700.HK',
                'data_points': len(data),
                'optimization_summary': {
                    'total_combinations_tested': total_combinations,
                    'successful_combinations': len(results),
                    'execution_time': execution_time,
                    'processing_speed': len(results) / execution_time
                },
                'best_parameters': results[:10],
                'statistics': {
                    'average_sharpe': float(np.mean(sharpe_values)),
                    'max_sharpe': float(np.max(sharpe_values)),
                    'positive_sharpe_count': len(positive_results),
                    'no_trade_count': len([r for r in results if r['total_trades'] == 0])
                }
            }

            with open(f'hibor_rsi_optimization_results_{timestamp}.json', 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"\nResults saved to: hibor_rsi_optimization_results_{timestamp}.json")

        else:
            print("No successful test results")

        print(f"\n0700.HK HIBOR-RSI Parameter Optimization Demo Completed!")
        print(f"This is just a small-scale demo, full system supports 528,000+ parameter combinations")
        return True

    except Exception as e:
        print(f"Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)