#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Parameter Optimization Demo
0700.HK RSI Parameter Optimization (0-300 range)
"""

import time
import warnings
import numpy as np
import pandas as pd
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import sys

warnings.filterwarnings('ignore')

def generate_mock_stock_data(days=252, start_price=400):
    """Generate mock stock data for demonstration"""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=days, freq='D')

    # Generate realistic price movements
    returns = np.random.normal(0.001, 0.02, days)  # Daily returns with volatility
    prices = start_price * np.cumprod(1 + returns)

    # Generate OHLCV data
    data = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, days)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, days)
    }, index=dates)

    return data

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def backtest_rsi_strategy(data, period, oversold, overbought):
    """Simple RSI mean reversion backtest"""
    try:
        # Calculate RSI
        rsi = calculate_rsi(data['close'], period)

        # Generate trading signals
        signals = pd.DataFrame(index=data.index)
        signals['position'] = 0

        # Buy when RSI crosses above oversold
        buy_signals = (rsi > oversold) & (rsi.shift(1) <= oversold)
        # Sell when RSI crosses below overbought
        sell_signals = (rsi < overbought) & (rsi.shift(1) >= overbought)

        signals.loc[buy_signals, 'position'] = 1
        signals.loc[sell_signals, 'position'] = -1

        # Forward fill positions
        signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

        # Calculate returns
        returns = data['close'].pct_change()
        strategy_returns = signals['position'].shift(1) * returns

        # Calculate performance metrics
        total_return = (1 + strategy_returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(strategy_returns)) - 1

        # Sharpe ratio (risk-free rate = 3%)
        excess_returns = strategy_returns - 0.03/252
        if len(strategy_returns) > 0 and strategy_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / strategy_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0

        # Max drawdown
        cumulative = (1 + strategy_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Win rate
        winning_trades = strategy_returns[strategy_returns > 0]
        win_rate = len(winning_trades) / len(strategy_returns[strategy_returns != 0]) if len(strategy_returns[strategy_returns != 0]) > 0 else 0

        # Total trades
        total_trades = len(signals[signals['position'].diff() != 0])

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'annual_return': annual_return,
            'success': True
        }

    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

def run_parameter_optimization():
    """Run comprehensive parameter optimization"""
    print("=" * 80)
    print("0700.HK RSI Parameter Optimization System")
    print("Parameter Range: 0-300")
    print("=" * 80)

    # Generate test data
    print("Generating test data...")
    data = generate_mock_stock_data(365, 400)  # 1 year of data
    print(f"Generated {len(data)} days of stock data")
    print(f"Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")

    # Generate parameter combinations
    print("\nGenerating parameter combinations...")

    # RSI parameter ranges for 0-300 optimization
    rsi_periods = list(range(5, 301, 5))      # 5-300, step=5
    oversold_levels = list(range(10, 50, 5))  # 10-45, step=5
    overbought_levels = list(range(55, 95, 5)) # 55-90, step=5

    valid_combinations = []
    for period in rsi_periods:
        for oversold in oversold_levels:
            for overbought in overbought_levels:
                if oversold < overbought:  # Validate logical relationship
                    valid_combinations.append({
                        'rsi_period': period,
                        'rsi_oversold': oversold,
                        'rsi_overbought': overbought
                    })

    # Limit to manageable number for demo
    max_combinations = min(1000, len(valid_combinations))
    combinations_to_test = valid_combinations[:max_combinations]

    print(f"Generated {len(valid_combinations)} total combinations")
    print(f"Testing {max_combinations} combinations for demonstration")

    # Run optimization
    print(f"\nStarting parallel optimization...")
    start_time = time.time()

    results = []
    batch_size = 20
    total_batches = (len(combinations_to_test) + batch_size - 1) // batch_size

    def test_combination(params):
        result = backtest_rsi_strategy(data,
                                     params['rsi_period'],
                                     params['rsi_oversold'],
                                     params['rsi_overbought'])
        if result['success']:
            return {
                'parameters': params,
                'sharpe_ratio': result['sharpe_ratio'],
                'total_return': result['total_return'],
                'max_drawdown': result['max_drawdown'],
                'win_rate': result['win_rate'],
                'total_trades': result['total_trades'],
                'annual_return': result['annual_return']
            }
        return None

    # Process in batches
    for batch_idx in range(0, len(combinations_to_test), batch_size):
        batch = combinations_to_test[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1

        print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} combinations)...")

        # Parallel execution
        with ThreadPoolExecutor(max_workers=4) as executor:
            batch_results = list(executor.map(test_combination, batch))

        # Filter successful results
        for result in batch_results:
            if result is not None:
                results.append(result)

    execution_time = time.time() - start_time

    print(f"\nOptimization completed!")
    print(f"Execution time: {execution_time:.2f} seconds")
    print(f"Successful tests: {len(results)} / {len(combinations_to_test)}")
    print(f"Processing speed: {len(results) / execution_time:.1f} combos/second")

    # Analyze results
    if results:
        # Sort by Sharpe ratio
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

        print(f"\n{'='*80}")
        print("TOP 10 OPTIMAL PARAMETER COMBINATIONS")
        print(f"{'='*80}")

        print(f"{'Rank':<5} {'Sharpe':<8} {'Return':<10} {'Max DD':<10} {'Win Rate':<10} {'Trades':<8} {'Parameters'}")
        print("-" * 80)

        for i, result in enumerate(results[:10], 1):
            params = result['parameters']
            print(f"{i:<5} {result['sharpe_ratio']:>7.3f} "
                  f"{result['total_return']:>9.2%} "
                  f"{result['max_drawdown']:>9.2%} "
                  f"{result['win_rate']:>9.1%} "
                  f"{result['total_trades']:>7d} "
                  f"P:{params['rsi_period']:3d} "
                  f"OS:{params['rsi_oversold']:2d} "
                  f"OB:{params['rsi_overbought']:2d}")

        # Statistical analysis
        sharpe_values = [r['sharpe_ratio'] for r in results]
        positive_results = [r for r in results if r['sharpe_ratio'] > 1.0]
        profitable_results = [r for r in results if r['total_return'] > 0]

        print(f"\n{'='*60}")
        print("OPTIMIZATION STATISTICS")
        print(f"{'='*60}")
        print(f"Total combinations tested: {len(combinations_to_test):,}")
        print(f"Successful combinations: {len(results):,}")
        print(f"Average Sharpe ratio: {np.mean(sharpe_values):.3f}")
        print(f"Best Sharpe ratio: {np.max(sharpe_values):.3f}")
        print(f"Positive Sharpe combos: {len(positive_results):,} ({len(positive_results)/len(results)*100:.1f}%)")
        print(f"Profitable combos: {len(profitable_results):,} ({len(profitable_results)/len(results)*100:.1f}%)")
        print(f"Zero trade combos: {len([r for r in results if r['total_trades'] == 0])}")

        if positive_results:
            best = positive_results[0]
            print(f"\n{'='*60}")
            print("RECOMMENDED PARAMETER COMBINATION")
            print(f"{'='*60}")
            print(f"RSI Period: {best['parameters']['rsi_period']}")
            print(f"Oversold Level: {best['parameters']['rsi_oversold']}")
            print(f"Overbought Level: {best['parameters']['rsi_overbought']}")
            print(f"Expected Sharpe: {best['sharpe_ratio']:.3f}")
            print(f"Expected Annual Return: {best['annual_return']:.2%}")
            print(f"Expected Max Drawdown: {best['max_drawdown']*100:.2f}%")
            print(f"Expected Win Rate: {best['win_rate']*100:.2f}%")

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': '0700.HK',
            'data_points': len(data),
            'optimization_summary': {
                'total_combinations_tested': len(combinations_to_test),
                'successful_combinations': len(results),
                'execution_time': execution_time,
                'processing_speed': len(results) / execution_time
            },
            'best_parameters': results[:10],
            'statistics': {
                'average_sharpe': float(np.mean(sharpe_values)),
                'max_sharpe': float(np.max(sharpe_values)),
                'positive_sharpe_count': len(positive_results),
                'profitable_count': len(profitable_results),
                'no_trade_count': len([r for r in results if r['total_trades'] == 0])
            }
        }

        filename = f'simple_rsi_optimization_results_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to: {filename}")

    else:
        print("ERROR: No successful optimization results")

    print(f"\n{'='*80}")
    print("0700.HK RSI Parameter Optimization Demo Completed!")
    print("This demonstrates the core functionality of the 0-300 parameter optimization system")
    print(f"{'='*80}")

if __name__ == "__main__":
    try:
        run_parameter_optimization()
        print("\n✅ Optimization completed successfully!")
    except Exception as e:
        print(f"\n❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)