#!/usr/bin/env python3
"""
Universal Stock Backtest Tool
通用股票回測工具

Input any stock symbol to run comprehensive backtest analysis
"""

import sys
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime


def get_stock_data(symbol, duration_days=365):
    """Get stock data from API"""
    print(f"GETTING {symbol.upper()} DATA FROM API")
    print("=" * 50)

    try:
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": symbol.lower(), "duration": duration_days}

        print(f"Requesting: {url}")
        print(f"Symbol: {symbol.upper()}")
        print(f"Duration: {duration_days} days")

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if 'data' in data and 'close' in data['data']:
                # Parse the data
                dates = list(data['data']['close'].keys())
                prices = list(data['data']['close'].values())

                print(f"[OK] Data loaded successfully!")
                print(f"   Data points: {len(prices)}")
                print(f"   Date range: {dates[0]} to {dates[-1]}")
                print(f"   Price range: {min(prices):.2f} - {max(prices):.2f}")
                print(f"   Current price: {prices[-1]:.2f}")

                # Create DataFrame
                df = pd.DataFrame({
                    'date': pd.to_datetime(dates),
                    'close': prices
                })
                df.set_index('date', inplace=True)

                return df
            else:
                print(f"[ERROR] Invalid API response structure for {symbol}")
                return None
        else:
            print(f"[ERROR] API HTTP error: {response.status_code} for {symbol}")
            return None

    except Exception as e:
        print(f"[ERROR] Failed to get {symbol} data: {e}")
        return None


def calculate_indicators(prices):
    """Calculate multiple technical indicators"""
    indicators = {}

    try:
        # RSI indicators
        def calculate_rsi(prices, period):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        indicators['RSI_14'] = calculate_rsi(prices, 14)
        indicators['RSI_21'] = calculate_rsi(prices, 21)
        indicators['RSI_30'] = calculate_rsi(prices, 30)

        # Moving Averages
        indicators['SMA_20'] = prices.rolling(window=20).mean()
        indicators['SMA_50'] = prices.rolling(window=50).mean()
        indicators['SMA_100'] = prices.rolling(window=100).mean()
        indicators['EMA_20'] = prices.ewm(span=20).mean()

        # Volatility
        indicators['VOLATILITY_20'] = prices.rolling(window=20).std()
        indicators['VOLATILITY_50'] = prices.rolling(window=50).std()

        # Price levels
        indicators['HIGH_20'] = prices.rolling(window=20).max()
        indicators['LOW_20'] = prices.rolling(window=20).min()

        print(f"[OK] Calculated {len(indicators)} technical indicators")
        return indicators

    except Exception as e:
        print(f"[ERROR] Indicator calculation failed: {e}")
        return {}


def run_strategy_backtest(prices, signals, strategy_name):
    """Run backtest for a single strategy"""
    try:
        # Calculate returns
        returns = prices.pct_change().dropna()

        # Apply trading signals (shift by 1 for next day execution)
        strategy_returns = returns.shift(-1) * signals.shift(1)

        # Remove NaN values
        strategy_returns = strategy_returns.dropna()

        if len(strategy_returns) == 0:
            return None

        # Calculate metrics
        total_return = (1 + strategy_returns).prod() - 1
        cumulative_returns = (1 + strategy_returns).cumprod()

        # Calculate Sharpe ratio with 3% risk-free rate
        risk_free_rate = 0.03
        daily_risk_free = risk_free_rate / 365
        excess_returns = strategy_returns - daily_risk_free

        if len(excess_returns) > 0 and excess_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(365)
        else:
            sharpe_ratio = 0.0

        # Calculate max drawdown
        peak = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = drawdown.min()

        # Calculate win rate
        winning_days = (strategy_returns > 0).sum()
        total_trading_days = len(strategy_returns)
        win_rate = winning_days / total_trading_days if total_trading_days > 0 else 0

        # Calculate volatility
        volatility = strategy_returns.std() * np.sqrt(365)

        # Quality score
        quality_score = min(100, max(0,
            (sharpe_ratio * 20) + (total_return * 100) - (abs(max_drawdown) * 50) + (win_rate * 10)
        ))

        return {
            'strategy': strategy_name,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'win_rate': win_rate,
            'trading_days': total_trading_days,
            'quality_score': quality_score,
            'success': True
        }

    except Exception as e:
        print(f"[ERROR] Backtest failed for {strategy_name}: {e}")
        return {
            'strategy': strategy_name,
            'error': str(e),
            'success': False
        }


def generate_signals(prices, indicators):
    """Generate trading signals based on indicators"""
    signals = {}

    try:
        # RSI Mean Reversion Strategies
        if 'RSI_14' in indicators:
            rsi_signals = pd.Series(0, index=prices.index)
            rsi_signals[indicators['RSI_14'] < 30] = 1   # Buy
            rsi_signals[indicators['RSI_14'] > 70] = -1  # Sell
            signals['RSI_MR_14'] = rsi_signals

        if 'RSI_21' in indicators:
            rsi_signals = pd.Series(0, index=prices.index)
            rsi_signals[indicators['RSI_21'] < 25] = 1   # More conservative
            rsi_signals[indicators['RSI_21'] > 75] = -1
            signals['RSI_MR_21'] = rsi_signals

        # Moving Average Crossover Strategies
        if 'SMA_20' in indicators and 'SMA_50' in indicators:
            ma_signals = pd.Series(0, index=prices.index)
            buy_signal = (indicators['SMA_20'] > indicators['SMA_50']) & (indicators['SMA_20'].shift(1) <= indicators['SMA_50'].shift(1))
            sell_signal = (indicators['SMA_20'] < indicators['SMA_50']) & (indicators['SMA_20'].shift(1) >= indicators['SMA_50'].shift(1))
            ma_signals[buy_signal] = 1
            ma_signals[sell_signal] = -1
            signals['SMA_XOVER_20_50'] = ma_signals

        if 'SMA_20' in indicators and 'SMA_100' in indicators:
            ma_signals = pd.Series(0, index=prices.index)
            buy_signal = (indicators['SMA_20'] > indicators['SMA_100']) & (indicators['SMA_20'].shift(1) <= indicators['SMA_100'].shift(1))
            sell_signal = (indicators['SMA_20'] < indicators['SMA_100']) & (indicators['SMA_20'].shift(1) >= indicators['SMA_100'].shift(1))
            ma_signals[buy_signal] = 1
            ma_signals[sell_signal] = -1
            signals['SMA_XOVER_20_100'] = ma_signals

        # Price Breakout Strategy
        if 'HIGH_20' in indicators and 'LOW_20' in indicators:
            breakout_signals = pd.Series(0, index=prices.index)
            breakout_signals[prices > indicators['HIGH_20'].shift(1)] = 1   # Breakout high
            breakout_signals[prices < indicators['LOW_20'].shift(1)] = -1   # Breakout low
            signals['BREAKOUT_20'] = breakout_signals

        # Momentum Strategy (using price vs SMA)
        if 'SMA_20' in indicators:
            momentum_signals = pd.Series(0, index=prices.index)
            momentum_signals[prices > indicators['SMA_20'] * 1.02] = 1   # 2% above MA
            momentum_signals[prices < indicators['SMA_20'] * 0.98] = -1  # 2% below MA
            signals['MOMENTUM_2PCT'] = momentum_signals

        # Buy and Hold (Benchmark)
        signals['BUY_HOLD'] = pd.Series(1, index=prices.index)

        print(f"[OK] Generated {len(signals)} trading strategies")
        return signals

    except Exception as e:
        print(f"[ERROR] Signal generation failed: {e}")
        return {'BUY_HOLD': pd.Series(1, index=prices.index)}


def run_comprehensive_backtest(symbol, duration_days=365):
    """Run comprehensive backtest for given symbol"""
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE BACKTEST: {symbol.upper()}")
    print(f"{'='*60}")

    # Get stock data
    df = get_stock_data(symbol, duration_days)
    if df is None:
        return None

    prices = df['close']

    # Calculate indicators
    indicators = calculate_indicators(prices)

    # Generate signals
    signals = generate_signals(prices, indicators)

    # Run backtests
    print(f"\nRUNNING BACKTESTS FOR {len(signals)} STRATEGIES")
    print("-" * 50)

    all_results = []
    for strategy_name, signal in signals.items():
        print(f"\nStrategy: {strategy_name}")
        try:
            result = run_strategy_backtest(prices, signal, strategy_name)
            if result and result['success']:
                print(f"[OK] {strategy_name}:")
                print(f"    Return: {result['total_return']:.2%}")
                print(f"    Sharpe: {result['sharpe_ratio']:.3f}")
                print(f"    Max DD: {result['max_drawdown']:.2%}")
                print(f"    Win Rate: {result['win_rate']:.1%}")
                print(f"    Quality: {result['quality_score']:.1f}")
                all_results.append(result)
            else:
                print(f"[FAIL] {strategy_name}: No results")
        except Exception as e:
            print(f"[ERROR] {strategy_name}: {e}")

    # Generate final report
    return generate_final_report(symbol, all_results, len(prices), duration_days)


def generate_final_report(symbol, results, data_points, duration_days):
    """Generate final comprehensive report"""
    print(f"\n{'='*80}")
    print(f"FINAL BACKTEST REPORT: {symbol.upper()}")
    print(f"{'='*80}")

    successful_results = [r for r in results if r.get('success', False)]

    print(f"\nSUMMARY:")
    print(f"Stock Symbol: {symbol.upper()}")
    print(f"Data Points: {data_points}")
    print(f"Duration: {duration_days} days")
    print(f"Total Strategies: {len(results)}")
    print(f"Successful: {len(successful_results)}")
    print(f"Success Rate: {len(successful_results)/len(results)*100:.1f}%")

    if successful_results:
        # Sort by Sharpe ratio
        sorted_results = sorted(successful_results, key=lambda x: x['sharpe_ratio'], reverse=True)

        print(f"\nTOP 5 STRATEGIES (by Sharpe Ratio):")
        print("-" * 80)
        print(f"{'Rank':<6} {'Strategy':<20} {'Return':<10} {'Sharpe':<10} {'Max DD':<10} {'Win Rate':<10} {'Quality':<8}")
        print("-" * 80)

        for i, result in enumerate(sorted_results[:5], 1):
            print(f"{i:<6} {result['strategy']:<20} {result['total_return']:<10.2%} "
                  f"{result['sharpe_ratio']:<10.3f} {result['max_drawdown']:<10.2%} "
                  f"{result['win_rate']:<10.1%} {result['quality_score']:<8.1f}")

        # Best strategy details
        best_strategy = sorted_results[0]
        print(f"\nBEST STRATEGY DETAILS:")
        print(f"Strategy: {best_strategy['strategy']}")
        print(f"Total Return: {best_strategy['total_return']:.2%}")
        print(f"Sharpe Ratio: {best_strategy['sharpe_ratio']:.3f}")
        print(f"Max Drawdown: {best_strategy['max_drawdown']:.2%}")
        print(f"Volatility: {best_strategy['volatility']:.2%}")
        print(f"Win Rate: {best_strategy['win_rate']:.1%}")
        print(f"Trading Days: {best_strategy['trading_days']}")
        print(f"Quality Score: {best_strategy['quality_score']:.1f}")

        # Sharpe validation
        if 0.5 <= best_strategy['sharpe_ratio'] <= 3.0:
            print(f"[OK] Best Sharpe ratio is in expected range (0.5-3.0)")
        elif best_strategy['sharpe_ratio'] > 3.0:
            print(f"[WARN] Best Sharpe ratio seems high ({best_strategy['sharpe_ratio']:.3f})")
        else:
            print(f"[WARN] Low Sharpe ratio ({best_strategy['sharpe_ratio']:.3f})")

        # Compare with Buy & Hold
        buy_hold = next((r for r in sorted_results if r['strategy'] == 'BUY_HOLD'), None)
        if buy_hold and best_strategy['strategy'] != 'BUY_HOLD':
            outperformance = best_strategy['total_return'] - buy_hold['total_return']
            sharpe_improvement = best_strategy['sharpe_ratio'] - buy_hold['sharpe_ratio']
            print(f"\nvs Buy & Hold:")
            print(f"  Return Outperformance: {outperformance:+.2%}")
            print(f"  Sharpe Improvement: {sharpe_improvement:+.3f}")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"backtest_{symbol.lower()}_{timestamp}.json"

        results_data = {
            'stock_symbol': symbol.upper(),
            'backtest_date': timestamp,
            'data_points': data_points,
            'duration_days': duration_days,
            'total_strategies': len(results),
            'successful_strategies': len(successful_results),
            'success_rate': len(successful_results)/len(results)*100,
            'best_strategy': best_strategy,
            'top_strategies': sorted_results[:5],
            'all_results': results
        }

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Results saved to: {results_file}")
        print(f"[OK] Backtest completed successfully for {symbol.upper()}!")

        return True
    else:
        print(f"\n[FAILED] No successful strategies found for {symbol.upper()}")
        return False


def main():
    """Main interactive execution"""
    print("UNIVERSAL STOCK BACKTEST TOOL")
    print("通用股票回測工具")
    print("=" * 50)

    # Get user input for stock symbol
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        print("\nEnter stock symbol (e.g., 0700.HK, 0941.HK, AAPL):")
        symbol = input("Symbol: ").strip()

    if not symbol:
        print("[ERROR] No symbol provided")
        return False

    # Get duration (optional)
    duration = 365
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            duration = 365

    print(f"\nStarting backtest for {symbol.upper()}...")
    print(f"Duration: {duration} days")

    try:
        success = run_comprehensive_backtest(symbol, duration)

        if success:
            print(f"\n{'='*50}")
            print(f"BACKTEST COMPLETED SUCCESSFULLY!")
            print(f"Results saved for {symbol.upper()}")
            print(f"{'='*50}")
            return True
        else:
            print(f"\n{'='*50}")
            print(f"BACKTEST FAILED!")
            print(f"Check logs for errors")
            print(f"{'='*50}")
            return False

    except Exception as e:
        print(f"[ERROR] Main execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)