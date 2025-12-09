#!/usr/bin/env python3
"""
Simple 0700.HK Backtest
簡單0700.HK回測

Direct backtest implementation for 0700.HK using real API data
"""

import sys
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime


def get_0700_hk_data():
    """Get real 0700.HK data from API"""
    print("GETTING 0700.HK DATA FROM API")
    print("=" * 40)

    try:
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": "0700.hk", "duration": 365}

        print(f"Requesting: {url}")
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
                print("[ERROR] Invalid API response structure")
                return None
        else:
            print(f"[ERROR] API HTTP error: {response.status_code}")
            return None

    except Exception as e:
        print(f"[ERROR] Failed to get data: {e}")
        return None


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        print(f"[ERROR] RSI calculation failed: {e}")
        return None


def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    try:
        return prices.rolling(window=period).mean()
    except Exception as e:
        print(f"[ERROR] SMA calculation failed: {e}")
        return None


def run_backtest(prices, signals, strategy_name):
    """Run backtest with given signals"""
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

        # Quality score
        quality_score = min(100, max(0,
            (sharpe_ratio * 20) + (total_return * 100) - (abs(max_drawdown) * 50)
        ))

        return {
            'strategy': strategy_name,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'quality_score': quality_score,
            'trading_days': len(strategy_returns),
            'success': True
        }

    except Exception as e:
        print(f"[ERROR] Backtest failed for {strategy_name}: {e}")
        return {
            'strategy': strategy_name,
            'error': str(e),
            'success': False
        }


def run_strategies_backtest():
    """Run multiple strategies on 0700.HK"""
    print("\nRUNNING STRATEGIES BACKTEST")
    print("=" * 40)

    # Get data
    df = get_0700_hk_data()
    if df is None:
        return False

    prices = df['close']
    all_results = []

    # Strategy 1: RSI Mean Reversion (14)
    print("\nStrategy 1: RSI Mean Reversion (14)")
    try:
        rsi_14 = calculate_rsi(prices, 14)
        if rsi_14 is not None:
            # Buy when RSI < 30, sell when RSI > 70
            signals = pd.Series(0, index=prices.index)
            signals[rsi_14 < 30] = 1   # Buy signal
            signals[rsi_14 > 70] = -1  # Sell signal

            result = run_backtest(prices, signals, "RSI_MR_14")
            if result and result['success']:
                print(f"[OK] RSI_MR_14:")
                print(f"    Return: {result['total_return']:.2%}")
                print(f"    Sharpe: {result['sharpe_ratio']:.3f}")
                print(f"    Max DD: {result['max_drawdown']:.2%}")
                print(f"    Quality: {result['quality_score']:.1f}")
                all_results.append(result)
    except Exception as e:
        print(f"[ERROR] RSI_MR_14 failed: {e}")

    # Strategy 2: RSI Mean Reversion (21)
    print("\nStrategy 2: RSI Mean Reversion (21)")
    try:
        rsi_21 = calculate_rsi(prices, 21)
        if rsi_21 is not None:
            signals = pd.Series(0, index=prices.index)
            signals[rsi_21 < 25] = 1   # More conservative buy
            signals[rsi_21 > 75] = -1  # More conservative sell

            result = run_backtest(prices, signals, "RSI_MR_21")
            if result and result['success']:
                print(f"[OK] RSI_MR_21:")
                print(f"    Return: {result['total_return']:.2%}")
                print(f"    Sharpe: {result['sharpe_ratio']:.3f}")
                print(f"    Max DD: {result['max_drawdown']:.2%}")
                print(f"    Quality: {result['quality_score']:.1f}")
                all_results.append(result)
    except Exception as e:
        print(f"[ERROR] RSI_MR_21 failed: {e}")

    # Strategy 3: SMA Crossover (20/50)
    print("\nStrategy 3: SMA Crossover (20/50)")
    try:
        sma_20 = calculate_sma(prices, 20)
        sma_50 = calculate_sma(prices, 50)

        if sma_20 is not None and sma_50 is not None:
            signals = pd.Series(0, index=prices.index)

            # Buy when short MA crosses above long MA
            buy_signal = (sma_20 > sma_50) & (sma_20.shift(1) <= sma_50.shift(1))
            sell_signal = (sma_20 < sma_50) & (sma_20.shift(1) >= sma_50.shift(1))

            signals[buy_signal] = 1
            signals[sell_signal] = -1

            result = run_backtest(prices, signals, "SMA_XOVER_20_50")
            if result and result['success']:
                print(f"[OK] SMA_XOVER_20_50:")
                print(f"    Return: {result['total_return']:.2%}")
                print(f"    Sharpe: {result['sharpe_ratio']:.3f}")
                print(f"    Max DD: {result['max_drawdown']:.2%}")
                print(f"    Quality: {result['quality_score']:.1f}")
                all_results.append(result)
    except Exception as e:
        print(f"[ERROR] SMA_XOVER_20_50 failed: {e}")

    # Strategy 4: Buy and Hold (Benchmark)
    print("\nStrategy 4: Buy and Hold (Benchmark)")
    try:
        signals = pd.Series(1, index=prices.index)  # Always hold

        result = run_backtest(prices, signals, "BUY_HOLD")
        if result and result['success']:
            print(f"[OK] BUY_HOLD:")
            print(f"    Return: {result['total_return']:.2%}")
            print(f"    Sharpe: {result['sharpe_ratio']:.3f}")
            print(f"    Max DD: {result['max_drawdown']:.2%}")
            print(f"    Quality: {result['quality_score']:.1f}")
            all_results.append(result)
    except Exception as e:
        print(f"[ERROR] BUY_HOLD failed: {e}")

    return all_results


def generate_report(results):
    """Generate backtest report"""
    print("\n" + "=" * 60)
    print("0700.HK BACKTEST REPORT")
    print("=" * 60)

    successful_results = [r for r in results if r.get('success', False)]

    print(f"\nSummary:")
    print(f"Total Strategies: {len(results)}")
    print(f"Successful: {len(successful_results)}")
    print(f"Success Rate: {len(successful_results)/len(results)*100:.1f}%")

    if successful_results:
        # Find best strategy
        best_strategy = max(successful_results, key=lambda x: x['sharpe_ratio'])

        print(f"\nBest Strategy: {best_strategy['strategy']}")
        print(f"Total Return: {best_strategy['total_return']:.2%}")
        print(f"Sharpe Ratio: {best_strategy['sharpe_ratio']:.3f}")
        print(f"Max Drawdown: {best_strategy['max_drawdown']:.2%}")
        print(f"Quality Score: {best_strategy['quality_score']:.1f}")

        # Validate Sharpe ratio
        if 0.5 <= best_strategy['sharpe_ratio'] <= 3.0:
            print(f"[OK] Sharpe ratio is in expected range (0.5-3.0)")
        elif best_strategy['sharpe_ratio'] > 3.0:
            print(f"[WARN] Sharpe ratio seems high ({best_strategy['sharpe_ratio']:.3f})")
        else:
            print(f"[WARN] Low Sharpe ratio ({best_strategy['sharpe_ratio']:.3f})")

        # Compare with Buy and Hold
        buy_hold = next((r for r in successful_results if r['strategy'] == 'BUY_HOLD'), None)
        if buy_hold and best_strategy['strategy'] != 'BUY_HOLD':
            outperformance = best_strategy['total_return'] - buy_hold['total_return']
            print(f"\nvs Buy & Hold: {outperformance:+.2%}")

        return True
    else:
        print(f"\n[FAILED] No successful strategies found")
        return False


def main():
    """Main execution"""
    print("0700.HK SIMPLE BACKTEST")
    print("=" * 60)

    try:
        # Run strategies
        results = run_strategies_backtest()

        if not results:
            print("[FAILED] No results generated")
            return False

        # Generate report
        success = generate_report(results)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"simple_0700_backtest_{timestamp}.json"

        results_data = {
            'stock_symbol': '0700.HK',
            'backtest_date': timestamp,
            'results': results,
            'summary': {
                'total_strategies': len(results),
                'successful_strategies': len([r for r in results if r.get('success', False)]),
                'best_strategy': max([r for r in results if r.get('success', False)],
                                  key=lambda x: x['sharpe_ratio']) if results else None
            }
        }

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Results saved to: {results_file}")

        return success

    except Exception as e:
        print(f"[ERROR] Main execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("0700.HK BACKTEST COMPLETED SUCCESSFULLY!")
    else:
        print("0700.HK BACKTEST FAILED!")
    print(f"{'='*60}")

    sys.exit(0 if success else 1)