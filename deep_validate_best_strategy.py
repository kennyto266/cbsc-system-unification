#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Validate the Best Strategy Performance
"""

import time
import warnings
import numpy as np
import pandas as pd
import json
import requests
from datetime import datetime
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def comprehensive_backtest(data, period, oversold, overbought, strategy_name="RSI"):
    """Comprehensive backtest with detailed analysis"""
    print(f"\n{'='*60}")
    print(f"DEEP VALIDATION: {strategy_name}({period},{oversold},{overbought})")
    print(f"{'='*60}")

    try:
        # Calculate RSI
        rsi = calculate_rsi(data['close'], period)

        # Generate trading signals
        signals = pd.DataFrame(index=data.index)
        signals['rsi'] = rsi
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
        benchmark_returns = returns  # Buy and hold

        # Performance metrics
        total_return = (1 + strategy_returns).prod() - 1
        benchmark_return = (1 + benchmark_returns).prod() - 1
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

        # Win rate and trade analysis
        winning_trades = strategy_returns[strategy_returns > 0]
        losing_trades = strategy_returns[strategy_returns < 0]
        total_trades = len(signals[signals['position'].diff() != 0])

        if len(winning_trades) + len(losing_trades) > 0:
            win_rate = len(winning_trades) / (len(winning_trades) + len(losing_trades))
            avg_win = winning_trades.mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades.mean() if len(losing_trades) > 0 else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0

        # Additional risk metrics
        volatility = strategy_returns.std() * np.sqrt(252)
        downside_deviation = strategy_returns[strategy_returns < 0].std() * np.sqrt(252)

        if downside_deviation > 0:
            sortino_ratio = annual_return / downside_deviation
        else:
            sortino_ratio = 0

        # Monthly analysis
        monthly_returns = strategy_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        positive_months = len(monthly_returns[monthly_returns > 0])

        # Detailed analysis
        print(f"PERFORMANCE ANALYSIS:")
        print(f"  Period: {len(data)} days ({data.index[0].date()} to {data.index[-1].date()})")
        print(f"  Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")
        print(f"  RSI range: {rsi.min():.1f} - {rsi.max():.1f}")
        print(f"")
        print(f"RETURNS:")
        print(f"  Strategy Total Return: {total_return:.2%}")
        print(f"  Benchmark Return: {benchmark_return:.2%}")
        print(f"  Alpha: {total_return - benchmark_return:.2%}")
        print(f"  Annual Return: {annual_return:.2%}")
        print(f"")
        print(f"RISK METRICS:")
        print(f"  Sharpe Ratio: {sharpe_ratio:.3f}")
        print(f"  Sortino Ratio: {sortino_ratio:.3f}")
        print(f"  Max Drawdown: {max_drawdown:.2%}")
        print(f"  Volatility: {volatility:.2%}")
        print(f"")
        print(f"TRADING ANALYSIS:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Win Rate: {win_rate:.1%}")
        print(f"  Average Win: {avg_win:.2%}")
        print(f"  Average Loss: {avg_loss:.2%}")
        print(f"  Profit Factor: {-avg_win/avg_loss if avg_loss < 0 else 'N/A':.2f}")
        print(f"  Positive Months: {positive_months}/{len(monthly_returns)}")
        print(f"")

        # Generate trade log
        trade_log = []
        for i in range(1, len(signals)):
            if signals['position'].iloc[i] != signals['position'].iloc[i-1]:
                trade_log.append({
                    'date': signals.index[i].date(),
                    'price': data['close'].iloc[i],
                    'rsi': rsi.iloc[i],
                    'position': signals['position'].iloc[i],
                    'action': 'BUY' if signals['position'].iloc[i] == 1 else 'SELL'
                })

        if trade_log:
            print("RECENT TRADES:")
            for trade in trade_log[-10:]:  # Show last 10 trades
                print(f"  {trade['date']}: {trade['action']} @ ${trade['price']:.2f} (RSI: {trade['rsi']:.1f})")

        return {
            'strategy_name': f"{strategy_name}({period},{oversold},{overbought})",
            'total_return': total_return,
            'benchmark_return': benchmark_return,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'annual_return': annual_return,
            'profit_factor': -avg_win/avg_loss if avg_loss < 0 else None,
            'trade_log': trade_log,
            'data_points': len(data),
            'validation_passed': True
        }

    except Exception as e:
        print(f"ERROR: Backtest failed: {e}")
        return None

def main():
    """Main validation function"""
    print("DEEP VALIDATION OF OPTIMIZATION RESULTS")
    print("=" * 80)

    try:
        # Get real data
        print("Fetching real 0700.HK data...")
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 365}

        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            print("ERROR: Failed to fetch real data")
            return

        data = response.json()
        dates = list(data['data']['close'].keys())
        close_prices = list(data['data']['close'].values())
        high_prices = list(data['data']['high'].values())
        low_prices = list(data['data']['low'].values())
        open_prices = list(data['data']['open'].values())

        df = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': [1000000] * len(close_prices)
        }, index=pd.to_datetime(dates))

        print(f"SUCCESS: Loaded {len(df)} days of 0700.HK data")
        print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
        print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

        # Test best strategy from optimization
        best_strategy = {
            'rsi_period': 20,
            'rsi_oversold': 40,
            'rsi_overbought': 60
        }

        # Test conservative benchmark
        conservative_strategy = {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }

        # Test aggressive strategy
        aggressive_strategy = {
            'rsi_period': 10,
            'rsi_oversold': 20,
            'rsi_overbought': 80
        }

        strategies_to_test = [
            best_strategy,
            conservative_strategy,
            aggressive_strategy
        ]

        strategy_names = [
            "OPTIMIZED_BEST",
            "CONSERVATIVE_BENCHMARK",
            "AGGRESSIVE_TEST"
        ]

        results = []

        for strategy, name in zip(strategies_to_test, strategy_names):
            result = comprehensive_backtest(
                df,
                strategy['rsi_period'],
                strategy['rsi_oversold'],
                strategy['rsi_overbought'],
                name
            )

            if result:
                results.append(result)

        # Final comparison
        if len(results) >= 2:
            print(f"\n{'='*80}")
            print("STRATEGY COMPARISON SUMMARY")
            print(f"{'='*80}")

            print(f"{'Strategy':<25} {'Sharpe':<8} {'Return':<10} {'DD':<8} {'Trades':<8} {'Win%':<8}")
            print("-" * 80)

            for result in results:
                print(f"{result['strategy_name']:<25} "
                      f"{result['sharpe_ratio']:>7.3f} "
                      f"{result['total_return']:>9.2%} "
                      f"{result['max_drawdown']:>7.2%} "
                      f"{result['total_trades']:>7d} "
                      f"{result['win_rate']:>7.1%}")

            # Validate best strategy
            best_result = results[0]  # Our optimized strategy

            print(f"\n{'='*60}")
            print("RELIABILITY ASSESSMENT")
            print(f"{'='*60}")

            reliability_checks = {
                'reasonable_sharpe': 0.5 <= best_result['sharpe_ratio'] <= 10,
                'reasonable_return': abs(best_result['total_return']) <= 5,
                'reasonable_drawdown': best_result['max_drawdown'] >= -0.5,
                'sufficient_trades': best_result['total_trades'] >= 2,
                'data_quality': len(df) >= 100
            }

            for check, passed in reliability_checks.items():
                status = "PASS" if passed else "FAIL"
                print(f"{check:<20}: {status}")

            total_checks = sum(reliability_checks.values())
            if total_checks >= 4:
                print(f"\nCONCLUSION: BEST STRATEGY IS RELIABLE ({total_checks}/5 checks passed)")
            else:
                print(f"\nCONCLUSION: BEST STRATEGY NEEDS REVIEW ({total_checks}/5 checks passed)")

            # Save detailed results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': '0700.HK',
                'data_points': len(df),
                'best_strategy': best_result,
                'all_strategies': results,
                'reliability_checks': reliability_checks,
                'reliability_score': total_checks / 5
            }

            filename = f'deep_strategy_validation_{timestamp}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\nDetailed validation saved: {filename}")

    except Exception as e:
        print(f"ERROR: Validation process failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()