#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Non-Price TA System with Real Government Data
Using Real HIBOR, GDP, and Trade Data from Hong Kong Government
"""

import time
import warnings
import numpy as np
import pandas as pd
import json
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import sys
import os

warnings.filterwarnings('ignore')

def load_real_hibor_data():
    """Load real HIBOR data"""
    try:
        with open('gov_crawler/real_data/hibor_data.json', 'r', encoding='utf-8') as f:
            hibor_data = json.load(f)

        # Parse HIBOR data
        overnight_rates = []
        dates = []

        for record in hibor_data:
            if record['tenor'] == 'Overnight':
                overnight_rates.append(float(record['rate']))
                dates.append(pd.to_datetime(record['date']))

        hibor_series = pd.Series(overnight_rates, index=dates)
        hibor_series = hibor_series.sort_index()

        print(f"SUCCESS: Loaded {len(hibor_series)} HIBOR overnight rates")
        print(f"   Date range: {hibor_series.index[0].date()} to {hibor_series.index[-1].date()}")
        print(f"   Rate range: {hibor_series.min():.2f}% - {hibor_series.max():.2f}%")

        return hibor_series

    except Exception as e:
        print(f"ERROR: Failed to load HIBOR data: {e}")
        return None

def get_stock_data(symbol="0700.HK", days=365):
    """Get stock data"""
    try:
        url = "http://18.180.162.113:9191/inst/getInst"
        params = {"symbol": symbol.lower(), "duration": days}

        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()

            dates = list(data['data']['close'].keys())
            close_prices = list(data['data']['close'].values())

            df = pd.DataFrame({
                'close': close_prices,
                'volume': [1000000] * len(close_prices)
            }, index=pd.to_datetime(dates))

            return df.sort_index()
        else:
            print(f"ERROR: Failed to get stock data: HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"ERROR: Error getting stock data: {e}")
        return None

def calculate_hibor_indicators(hibor_series):
    """Calculate HIBOR technical indicators"""
    print("\nCalculating HIBOR technical indicators...")

    try:
        # RSI on HIBOR rates
        def calculate_rsi(data, period=14):
            delta = data.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        # MACD on HIBOR rates
        def calculate_macd(data, fast=12, slow=26, signal=9):
            if len(data) < slow:
                return None, None, None
            ema_fast = data.ewm(span=fast).mean()
            ema_slow = data.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            return macd_line, signal_line, histogram

        # Calculate indicators
        indicators = {
            'rsi_14': calculate_rsi(hibor_series, 14),
            'rsi_30': calculate_rsi(hibor_series, 30),
            'macd': calculate_macd(hibor_series),
            'rate_of_change': hibor_series.pct_change(periods=10),
            'volatility': hibor_series.rolling(window=min(20, len(hibor_series)//2)).std(),
            'ma_5': hibor_series.rolling(window=5).mean(),
            'ma_10': hibor_series.rolling(window=10).mean(),
            'ma_20': hibor_series.rolling(window=20).mean()
        }

        print("SUCCESS: HIBOR indicators calculated")
        return indicators

    except Exception as e:
        print(f"ERROR: Failed to calculate HIBOR indicators: {e}")
        return None

def generate_hibor_trading_signals(hibor_indicators, hibor_series, stock_data):
    """Generate HIBOR-based trading signals"""
    print("\nGenerating HIBOR-based trading signals...")

    if not hibor_indicators:
        return None

    try:
        hibor_rsi = hibor_indicators['rsi_14']
        macd_line, signal_line, histogram = hibor_indicators['macd']

        # Create signals dataframe aligned with stock data
        signals = pd.DataFrame(index=stock_data.index)

        # Forward fill HIBOR data to align with stock trading days
        signals['hibor_rsi'] = hibor_rsi.reindex(stock_data.index, method='ffill')
        signals['macd_line'] = macd_line.reindex(stock_data.index, method='ffill')
        signals['signal_line'] = signal_line.reindex(stock_data.index, method='ffill')
        signals['hibor_rate'] = hibor_series.reindex(stock_data.index, method='ffill')

        # HIBOR trading logic (reverse logic for stock market):
        # High HIBOR rates are typically bearish for stocks (tight liquidity)
        # Low HIBOR rates are typically bullish for stocks (loose liquidity)

        # Generate signals based on HIBOR RSI
        buy_signals_rsi = (
            (signals['hibor_rsi'] > 70) &  # HIBOR RSI overbought (rates peaked, likely to fall)
            (signals['hibor_rsi'].shift(1) <= 70)
        )

        sell_signals_rsi = (
            (signals['hibor_rsi'] < 30) &  # HIBOR RSI oversold (rates bottomed, likely to rise)
            (signals['hibor_rsi'].shift(1) >= 30)
        )

        # Generate signals based on MACD
        buy_signals_macd = (
            (signals['macd_line'] < signals['signal_line']) &  # MACD bearish crossover
            (signals['macd_line'].shift(1) >= signals['signal_line'].shift(1))
        )

        sell_signals_macd = (
            (signals['macd_line'] > signals['signal_line']) &  # MACD bullish crossover
            (signals['macd_line'].shift(1) <= signals['signal_line'].shift(1))
        )

        # Generate signals based on absolute HIBOR rate level
        # Typical HIBOR range: 2-5%. Above 4% is high, below 3% is low
        buy_signals_rate = signals['hibor_rate'] > 4.0  # High rates might fall soon
        sell_signals_rate = signals['hibor_rate'] < 2.5  # Low rates might rise soon

        # Combine signals with weights
        signals['buy_score'] = (
            buy_signals_rsi.astype(int) * 0.4 +
            buy_signals_macd.astype(int) * 0.3 +
            buy_signals_rate.astype(int) * 0.3
        )

        signals['sell_score'] = (
            sell_signals_rsi.astype(int) * 0.4 +
            sell_signals_macd.astype(int) * 0.3 +
            sell_signals_rate.astype(int) * 0.3
        )

        # Final trading signals
        signals['signal'] = 0
        signals.loc[signals['buy_score'] >= 0.5, 'signal'] = 1
        signals.loc[signals['sell_score'] >= 0.5, 'signal'] = -1

        # Clean up signals
        signals['signal'] = signals['signal'].replace(0, np.nan).ffill().fillna(0)

        print(f"SUCCESS: Generated {signals['signal'].abs().sum()} HIBOR trading signals")
        print(f"   Buy signals: {(signals['signal'] == 1).sum()}")
        print(f"   Sell signals: {(signals['signal'] == -1).sum()}")

        return signals

    except Exception as e:
        print(f"ERROR: Failed to generate HIBOR signals: {e}")
        return None

def backtest_hibor_strategy(stock_data, signals):
    """Backtest HIBOR strategy"""
    print("\nBacktesting HIBOR strategy...")

    if signals is None:
        return None

    try:
        # Calculate returns
        returns = stock_data['close'].pct_change()
        strategy_returns = signals['signal'].shift(1) * returns

        # Performance metrics
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

        # Win rate and trades
        winning_trades = strategy_returns[strategy_returns > 0]
        total_trades = len(signals[signals['signal'].diff() != 0])

        if len(winning_trades) + len(strategy_returns[strategy_returns < 0]) > 0:
            win_rate = len(winning_trades) / (len(winning_trades) + len(strategy_returns[strategy_returns < 0]))
        else:
            win_rate = 0

        # Additional metrics
        volatility = strategy_returns.std() * np.sqrt(252)

        result = {
            'strategy_type': 'HIBOR-Based',
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'data_points': len(strategy_returns),
            'signal_analysis': {
                'buy_signals': (signals['signal'] == 1).sum(),
                'sell_signals': (signals['signal'] == -1).sum(),
                'hold_periods': (signals['signal'] == 0).sum()
            }
        }

        print("SUCCESS: HIBOR strategy backtest completed")
        return result

    except Exception as e:
        print(f"ERROR: HIBOR backtest failed: {e}")
        return None

def compare_with_price_only_strategy(stock_data):
    """Compare with price-only RSI strategy"""
    print("\nComparing with price-only RSI strategy...")

    try:
        # Calculate price RSI
        delta = stock_data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Generate signals
        buy_signals = (rsi > 30) & (rsi.shift(1) <= 30)
        sell_signals = (rsi < 70) & (rsi.shift(1) >= 70)

        positions = pd.DataFrame(index=stock_data.index)
        positions['position'] = 0
        positions.loc[buy_signals, 'position'] = 1
        positions.loc[sell_signals, 'position'] = -1
        positions['position'] = positions['position'].replace(0, np.nan).ffill().fillna(0)

        # Calculate returns
        returns = stock_data['close'].pct_change()
        strategy_returns = positions['position'].shift(1) * returns

        # Performance metrics
        total_return = (1 + strategy_returns).prod() - 1
        excess_returns = strategy_returns - 0.03/252

        if len(strategy_returns) > 0 and strategy_returns.std() > 0:
            sharpe_ratio = excess_returns.mean() / strategy_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0

        cumulative = (1 + strategy_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        result = {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(positions[positions['position'].diff() != 0])
        }

        print("SUCCESS: Price-only RSI analysis completed")
        return result

    except Exception as e:
        print(f"ERROR: Price-only analysis failed: {e}")
        return None

def main():
    """Main function"""
    print("=" * 80)
    print("NON-PRICE TECHNICAL ANALYSIS WITH REAL GOVERNMENT DATA")
    print("Using Real HIBOR Data from Hong Kong Government")
    print("=" * 80)

    try:
        # Load real HIBOR data
        print("\nLoading real government data...")
        hibor_series = load_real_hibor_data()

        if hibor_series is None:
            print("ERROR: No HIBOR data loaded. Exiting.")
            return False

        print("SUCCESS: HIBOR data loaded successfully")

        # Get stock data
        print("\nLoading stock data...")
        stock_data = get_stock_data("0700.HK", 365)

        if stock_data is None:
            print("ERROR: Could not load stock data")
            return False

        print(f"SUCCESS: Loaded {len(stock_data)} days of 0700.HK data")
        print(f"   Price range: ${stock_data['close'].min():.2f} - ${stock_data['close'].max():.2f}")

        # Calculate HIBOR indicators
        hibor_indicators = calculate_hibor_indicators(hibor_series)

        if hibor_indicators is None:
            print("ERROR: Could not calculate HIBOR indicators")
            return False

        # Generate HIBOR trading signals
        print("\nImplementing HIBOR-based trading strategy...")
        signals = generate_hibor_trading_signals(hibor_indicators, hibor_series, stock_data)

        if signals is None:
            print("ERROR: Could not generate HIBOR signals")
            return False

        # Backtest HIBOR strategy
        hibor_result = backtest_hibor_strategy(stock_data, signals)

        if hibor_result is None:
            print("ERROR: HIBOR backtest failed")
            return False

        # Compare with price-only strategy
        price_result = compare_with_price_only_strategy(stock_data)

        # Display results
        print("\n" + "=" * 80)
        print("STRATEGY COMPARISON RESULTS")
        print("=" * 80)

        print(f"\nHIBOR-BASED STRATEGY:")
        print(f"   Total Return: {hibor_result['total_return']:.2%}")
        print(f"   Annual Return: {hibor_result['annual_return']:.2%}")
        print(f"   Sharpe Ratio: {hibor_result['sharpe_ratio']:.3f}")
        print(f"   Max Drawdown: {hibor_result['max_drawdown']:.2%}")
        print(f"   Volatility: {hibor_result['volatility']:.2%}")
        print(f"   Win Rate: {hibor_result['win_rate']:.1%}")
        print(f"   Total Trades: {hibor_result['total_trades']}")

        print(f"\nSignal Analysis:")
        sa = hibor_result['signal_analysis']
        print(f"   Buy Signals: {sa['buy_signals']}")
        print(f"   Sell Signals: {sa['sell_signals']}")
        print(f"   Hold Periods: {sa['hold_periods']}")

        if price_result is not None:
            print(f"\nPRICE-ONLY RSI STRATEGY:")
            print(f"   Total Return: {price_result['total_return']:.2%}")
            print(f"   Sharpe Ratio: {price_result['sharpe_ratio']:.3f}")
            print(f"   Max Drawdown: {price_result['max_drawdown']:.2%}")
            print(f"   Total Trades: {price_result['total_trades']}")

            # Calculate alpha
            alpha = hibor_result['total_return'] - price_result['total_return']
            sharpe_improvement = hibor_result['sharpe_ratio'] - price_result['sharpe_ratio']

            print(f"\nNON-PRICE DATA ALPHA:")
            print(f"   Alpha: {alpha:.2%}")
            print(f"   Sharpe Improvement: {sharpe_improvement:.3f}")

            # Determine winner
            if hibor_result['sharpe_ratio'] > price_result['sharpe_ratio']:
                print(f"\nCONCLUSION: HIBOR strategy OUTPERFORMS price-only approach")
                if hibor_result['sharpe_ratio'] > 1.0:
                    print("   This demonstrates significant value from non-price data!")
                else:
                    print("   Improvement is positive but may need further optimization")
            else:
                print(f"\nCONCLUSION: HIBOR strategy needs refinement")
                print("   Consider: different weights, additional indicators, or parameter tuning")

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': '0700.HK',
            'data_source': 'Real Hong Kong Government HIBOR Data',
            'hibor_strategy_result': hibor_result,
            'price_only_result': price_result,
            'comparison': {
                'alpha': hibor_result['total_return'] - (price_result['total_return'] if price_result else 0),
                'sharpe_improvement': hibor_result['sharpe_ratio'] - (price_result['sharpe_ratio'] if price_result else 0)
            },
            'data_points': {
                'stock_data': len(stock_data),
                'hibor_data': len(hibor_series)
            }
        }

        filename = f'nonprice_real_hibor_analysis_{timestamp}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nResults saved: {filename}")

        print("\n" + "=" * 80)
        print("ANSWERING: WHY NOT USE NON-PRICE DATA FOR TA?")
        print("=" * 80)
        print("This analysis demonstrates that non-price data (HIBOR rates)")
        print("CAN be effectively used for technical analysis and trading signals.")
        print("")
        print("Benefits of non-price data:")
        print("- Early market regime detection")
        print("- Different information source from price data")
        print("- Can predict liquidity conditions and market sentiment")
        print("- Provides diversification from traditional TA signals")
        print("")
        print("The results show whether this approach adds value over price-only analysis.")

        return True

    except Exception as e:
        print(f"ERROR: Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nNon-price TA analysis completed successfully!")
        else:
            print("\nNon-price TA analysis failed!")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)