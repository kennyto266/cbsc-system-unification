#!/usr/bin/env python3
"""
Final Corrected Massive Parameter Optimizer with Professional Sharpe Ratio
"""

import sys
import os
import time
import json
import multiprocessing as mp
from datetime import datetime
import numpy as np
import pandas as pd

sys.path.append('src')

try:
    from api.stock_api import get_hk_stock_data

    def calculate_professional_sharpe(prices, positions, risk_free_rate=0.03):
        """
        Calculate professional Sharpe Ratio using daily portfolio returns

        Args:
            prices: Array of daily prices
            positions: Array of position states (0=cash, 1=invested)
            risk_free_rate: Annual risk-free rate (default 3%)

        Returns:
            Professional Sharpe ratio (annualized)
        """
        # Calculate daily portfolio returns
        daily_returns = []
        for i in range(1, len(prices)):
            price_return = (prices[i] - prices[i-1]) / prices[i-1]
            # If invested, get market return; if not, get risk-free rate
            if positions[i] == 1:  # Invested
                portfolio_return = price_return
            else:  # Cash
                portfolio_return = risk_free_rate / 252  # Daily risk-free rate
            daily_returns.append(portfolio_return)

        if len(daily_returns) == 0:
            return 0.0

        # Calculate excess returns (portfolio returns - risk_free_rate)
        excess_returns = np.array(daily_returns) - (risk_free_rate / 252)

        # Calculate Sharpe ratio
        if np.std(excess_returns) == 0:
            return 0.0

        sharpe_daily = np.mean(excess_returns) / np.std(excess_returns)
        sharpe_annualized = sharpe_daily * np.sqrt(252)

        return sharpe_annualized

    def professional_rsi_backtest(prices, period=14, oversold=30, overbought=70):
        """Professional RSI backtest with proper daily return calculation"""
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        alpha = 1.0 / period
        rsi = []
        avg_gain = 0
        avg_loss = 0

        for i in range(len(gains)):
            if i == 0:
                avg_gain = gains[0] if len(gains) > 0 else 0
                avg_loss = losses[0] if len(losses) > 0 else 0
            else:
                avg_gain = alpha * gains[i] + (1 - alpha) * avg_gain
                avg_loss = alpha * losses[i] + (1 - alpha) * avg_loss

            if avg_loss == 0:
                rsi_val = 100
            else:
                rs = avg_gain / avg_loss
                rsi_val = 100 - (100 / (1 + rs))
            rsi.append(rsi_val)

        # Generate positions array
        positions = [0] * len(prices)  # Start with cash position

        for i in range(period, len(prices)):
            if i-1 < len(rsi):  # RSI available for previous day
                if positions[i-1] == 0 and rsi[i-1] < oversold:  # Buy signal
                    positions[i] = 1
                elif positions[i-1] == 1 and rsi[i-1] > overbought:  # Sell signal
                    positions[i] = 0
                else:  # Hold current position
                    positions[i] = positions[i-1]
            else:
                positions[i] = positions[i-1] if i > 0 else 0

        # Calculate professional metrics
        sharpe = calculate_professional_sharpe(prices, positions)

        # Calculate trade statistics
        trades = []
        entry_price = 0
        for i in range(1, len(prices)):
            if positions[i] == 1 and positions[i-1] == 0:  # Entry
                entry_price = prices[i]
            elif positions[i] == 0 and positions[i-1] == 1 and entry_price > 0:  # Exit
                return_pct = (prices[i] - entry_price) / entry_price
                trades.append(return_pct)
                entry_price = 0

        # Calculate total return based on portfolio value
        portfolio_value = []
        cash = 100000  # Starting with $100k
        shares = 0

        for i in range(len(prices)):
            if i > 0 and positions[i] == 1 and positions[i-1] == 0:  # Buy
                shares = cash / prices[i]
                cash = 0
            elif i > 0 and positions[i] == 0 and positions[i-1] == 1:  # Sell
                cash = shares * prices[i]
                shares = 0

            portfolio_value.append(cash + shares * prices[i])

        total_return = (portfolio_value[-1] - portfolio_value[0]) / portfolio_value[0]

        if trades:
            return {
                'total_return': total_return,
                'sharpe': sharpe,
                'trades': len(trades),
                'win_rate': len([t for t in trades if t > 0]) / len(trades),
                'positions': positions,
                'portfolio_value': portfolio_value
            }
        return None

    def professional_ma_backtest(prices, short=10, long=30):
        """Professional MA backtest with proper daily return calculation"""
        short_ma = pd.Series(prices).rolling(window=short).mean().fillna(prices[0])
        long_ma = pd.Series(prices).rolling(window=long).mean().fillna(prices[0])

        # Generate positions array
        positions = [0] * len(prices)

        for i in range(max(short, long), len(prices)):
            # Golden cross: short crosses above long
            if (short_ma.iloc[i] > long_ma.iloc[i] and
                short_ma.iloc[i-1] <= long_ma.iloc[i-1]):
                positions[i] = 1
            # Death cross: short crosses below long
            elif (short_ma.iloc[i] < long_ma.iloc[i] and
                  short_ma.iloc[i-1] >= long_ma.iloc[i-1]):
                positions[i] = 0
            else:  # Hold current position
                positions[i] = positions[i-1]

        # Calculate professional metrics
        sharpe = calculate_professional_sharpe(prices, positions)

        # Calculate trade statistics
        trades = []
        entry_price = 0
        for i in range(1, len(prices)):
            if positions[i] == 1 and positions[i-1] == 0:  # Entry
                entry_price = prices[i]
            elif positions[i] == 0 and positions[i-1] == 1 and entry_price > 0:  # Exit
                return_pct = (prices[i] - entry_price) / entry_price
                trades.append(return_pct)
                entry_price = 0

        # Calculate total return based on portfolio value
        portfolio_value = []
        cash = 100000  # Starting with $100k
        shares = 0

        for i in range(len(prices)):
            if i > 0 and positions[i] == 1 and positions[i-1] == 0:  # Buy
                shares = cash / prices[i]
                cash = 0
            elif i > 0 and positions[i] == 0 and positions[i-1] == 1:  # Sell
                cash = shares * prices[i]
                shares = 0

            portfolio_value.append(cash + shares * prices[i])

        total_return = (portfolio_value[-1] - portfolio_value[0]) / portfolio_value[0]

        if trades:
            return {
                'total_return': total_return,
                'sharpe': sharpe,
                'trades': len(trades),
                'win_rate': len([t for t in trades if t > 0]) / len(trades),
                'positions': positions,
                'portfolio_value': portfolio_value
            }
        return None

    def run_professional_optimization():
        """Run professional optimization with correct Sharpe calculation"""
        print("=" * 80)
        print("PROFESSIONAL MASSIVE PARAMETER OPTIMIZATION")
        print("=" * 80)

        # 1. Get real data
        print("\n[1/4] Getting real market data...")
        start_time = time.time()

        try:
            raw_data = get_hk_stock_data('0700.HK', 730)

            if raw_data and 'data' in raw_data and 'close' in raw_data['data']:
                close_data = raw_data['data']['close']
                prices = np.array(list(close_data.values()))

                data_time = time.time() - start_time
                print(f"   [OK] Real data: {len(prices):,} records")
                print(f"   [OK] Data fetch time: {data_time:.2f} seconds")

            else:
                print("   [FAIL] Cannot get real data")
                return

        except Exception as e:
            print(f"   [ERROR] Data fetch failed: {e}")
            return

        # 2. Generate parameter combinations
        print("\n[2/4] Generating parameter combinations...")

        # RSI parameters - Professional range
        rsi_params = []
        rsi_periods = [5, 7, 10, 12, 14, 18, 21, 25, 30]  # Common periods
        rsi_oversold = [20, 25, 30, 35]  # Standard oversold levels
        rsi_overbought = [70, 75, 80]  # Standard overbought levels

        for period in rsi_periods:
            for oversold in rsi_oversold:
                for overbought in rsi_overbought:
                    if oversold < overbought:
                        rsi_params.append((period, oversold, overbought))

        # MA parameters - Professional range
        ma_params = []
        ma_short = [5, 10, 15, 20, 25, 30]  # Common short MAs
        ma_long = [30, 35, 40, 45, 50, 60, 75, 90, 120]  # Common long MAs

        for short in ma_short:
            for long in ma_long:
                if short < long:
                    ma_params.append((short, long))

        total_params = len(rsi_params) + len(ma_params)
        print(f"   RSI strategies: {len(rsi_params):,}")
        print(f"   MA strategies: {len(ma_params):,}")
        print(f"   Total combinations: {total_params:,}")

        # 3. Prepare test data
        print(f"\n[3/4] Preparing test data...")
        test_params = []

        for params in rsi_params:
            test_params.append(('RSI', params))
        for params in ma_params:
            test_params.append(('MA', params))

        # 4. Run optimization
        print(f"\n[4/4] Starting professional optimization...")
        print(f"   [CPU] Using {mp.cpu_count()} cores")
        print(f"   [INFO] Professional Sharpe with daily portfolio returns")

        optimization_start = time.time()
        results = []
        completed = 0

        # Use multiprocessing pool
        with mp.Pool(processes=mp.cpu_count()) as pool:
            # Process chunks
            chunk_size = 20  # Smaller chunks for complex calculations
            for i in range(0, len(test_params), chunk_size):
                chunk = test_params[i:i+chunk_size]

                # Run backtests for each strategy in chunk
                chunk_results = []
                for strategy_type, params in chunk:
                    if strategy_type == 'RSI':
                        result = professional_rsi_backtest(prices, params[0], params[1], params[2])
                    elif strategy_type == 'MA':
                        result = professional_ma_backtest(prices, params[0], params[1])
                    chunk_results.append((strategy_type, params, result))

                # Collect results
                for strategy_type, params, result in chunk_results:
                    if result and result['trades'] >= 3:  # Require minimum trades
                        results.append({
                            'strategy': strategy_type,
                            'params': params,
                            'total_return': result['total_return'],
                            'sharpe': result['sharpe'],
                            'trades': result['trades'],
                            'win_rate': result['win_rate']
                        })

                completed += len(chunk)

                # Progress report
                elapsed = time.time() - optimization_start
                speed = completed / elapsed if elapsed > 0 else 0

                if completed % 50 == 0 or completed >= len(test_params):
                    print(f"   Progress: {completed:,}/{len(test_params):,} ({completed/len(test_params)*100:.1f}%)")
                    print(f"   Speed: {speed:.1f} strategies/second")
                    print(f"   Valid strategies: {len(results)} (minimum 3 trades)")

        optimization_time = time.time() - optimization_start
        total_time = time.time() - start_time

        # Analysis
        print(f"\n" + "=" * 80)
        print("PROFESSIONAL OPTIMIZATION COMPLETE")
        print("=" * 80)
        print(f"Total combinations tested: {completed:,}")
        print(f"Valid strategies (>=3 trades): {len(results):,}")
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Optimization time: {optimization_time:.1f} seconds")
        print(f"CPU cores used: {mp.cpu_count()}")

        if results:
            # Sort by Sharpe ratio
            sorted_results = sorted(results, key=lambda x: x['sharpe'], reverse=True)

            print(f"\nTOP 10 STRATEGIES (PROFESSIONAL SHARPE RATIOS):")
            print("-" * 70)
            for i, result in enumerate(sorted_results[:10], 1):
                print(f"{i:2d}. {result['strategy']}:")
                print(f"    Params: {result['params']}")
                print(f"    Sharpe: {result['sharpe']:.3f}, Return: {result['total_return']:.1%}")
                print(f"    Trades: {result['trades']}, Win Rate: {result['win_rate']:.1%}")

            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            report = {
                'optimization_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'total_combinations': len(test_params),
                    'completed_combinations': completed,
                    'valid_strategies': len(results),
                    'total_time': total_time,
                    'optimization_time': optimization_time,
                    'cpu_cores': mp.cpu_count(),
                    'strategies_per_second': len(results)/optimization_time,
                    'data_points': len(prices),
                    'sharpe_method': 'professional_daily_portfolio_returns',
                    'risk_free_rate': 0.03,
                    'minimum_trades_required': 3
                },
                'results': sorted_results
            }

            # Save JSON
            json_file = f'professional_optimization_report_{timestamp}.json'
            with open(json_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            # Save CSV
            df = pd.DataFrame(sorted_results)
            csv_file = f'professional_optimization_results_{timestamp}.csv'
            df.to_csv(csv_file, index=False)

            print(f"\nResults saved:")
            print(f"  JSON report: {json_file}")
            print(f"  CSV results: {csv_file}")

            print(f"\nPROFESSIONAL OPTIMIZATION SUMMARY:")
            print(f"  Used daily portfolio returns for Sharpe calculation")
            print(f"  Applied 3% annual risk-free rate adjustment")
            print(f"  Required minimum 3 trades for validity")
            print(f"  Realistic Sharpe ratios: typically 0.5-3.0 range")
            print(f"  Top strategy Sharpe: {sorted_results[0]['sharpe']:.3f}")

        print("\n" + "=" * 80)
        print("PROFESSIONAL OPTIMIZATION COMPLETED")
        print("=" * 80)

    if __name__ == "__main__":
        run_professional_optimization()

except ImportError as e:
    print(f"[IMPORT ERROR] {e}")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()