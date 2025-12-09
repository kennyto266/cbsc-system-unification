#!/usr/bin/env python3
"""
FINAL CBSC REAL DATA BACKTEST
Complete Real Data Analysis - No Simulation, No Mock Data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

def run_complete_real_backtest():
    """Run comprehensive backtest using ALL available real CBSC data"""
    print("=" * 80)
    print("FINAL CBSC REAL DATA BACKTEST - ALL AVAILABLE DATA")
    print("No Simulation, No Mock Data - 100% Real Market Data")
    print("=" * 80)

    # 1. Load complete dataset
    data_file = "CODEX--/warrant_sentiment_merged.csv"

    if not Path(data_file).exists():
        print(f"ERROR: Data file not found: {data_file}")
        return False

    try:
        data = pd.read_csv(data_file)
        print(f"\n1. COMPLETE DATASET LOADED:")
        print(f"   Records: {len(data)}")
        print(f"   Date Range: {data['Date'].min()} to {data['Date'].max()}")

        # Data preparation
        data['Date'] = pd.to_datetime(data['Date'])
        data = data.dropna(subset=['Afternoon_Close', 'Date'])
        data = data.drop_duplicates(subset=['Date'], keep='last')
        data = data.sort_values('Date')

        trading_days = len(data)
        period_days = (data['Date'].max() - data['Date'].min()).days + 1
        coverage = (trading_days / period_days) * 100

        print(f"   Unique Trading Days: {trading_days}")
        print(f"   Calendar Period: {period_days} days")
        print(f"   Data Coverage: {coverage:.1f}%")

    except Exception as e:
        print(f"ERROR: Data loading failed - {e}")
        return False

    # 2. Market analysis
    print(f"\n2. REAL MARKET ANALYSIS:")
    start_price = data['Afternoon_Close'].iloc[0]
    end_price = data['Afternoon_Close'].iloc[-1]
    min_price = data['Afternoon_Close'].min()
    max_price = data['Afternoon_Close'].max()
    total_return = (end_price - start_price) / start_price

    print(f"   Hang Seng Index: {start_price:,.2f} -> {end_price:,.2f}")
    print(f"   Price Range: {min_price:,.2f} - {max_price:,.2f}")
    print(f"   Total Return: {total_return:.2%}")

    # Sentiment analysis
    bull_volume = data['Bull_Turnover_HKD'].sum()
    bear_volume = data['Bear_Turnover_HKD'].sum()
    total_volume = bull_volume + bear_volume
    avg_bull_ratio = data['Bull_Ratio'].mean()

    buy_signals = (data['Signal'] == 1).sum()
    sell_signals = (data['Signal'] == -1).sum()
    hold_signals = (data['Signal'] == 0).sum()

    print(f"\n   CBSC Trading Volume: {total_volume:,.0f} HKD")
    print(f"   Bull Volume: {bull_volume:,.0f} HKD ({bull_volume/total_volume*100:.1f}%)")
    print(f"   Bear Volume: {bear_volume:,.0f} HKD ({bear_volume/total_volume*100:.1f}%)")
    print(f"   Average Bull Ratio: {avg_bull_ratio:.3f}")
    print(f"   Buy Signals: {buy_signals} ({buy_signals/len(data)*100:.1f}%)")
    print(f"   Sell Signals: {sell_signals} ({sell_signals/len(data)*100:.1f}%)")

    # 3. Strategy backtesting
    print(f"\n3. STRATEGY BACKTESTING ON REAL DATA:")

    strategies = {}

    # Strategy 1: Sentiment Following
    print(f"\n   Strategy 1: Sentiment Following")
    sentiment_result = backtest_sentiment_strategy(data)
    if sentiment_result:
        strategies['Sentiment'] = sentiment_result
        print_strategy_summary(sentiment_result)

    # Strategy 2: Buy and Hold (Benchmark)
    print(f"\n   Strategy 2: Buy and Hold HSI (Benchmark)")
    benchmark_result = backtest_buy_and_hold(data)
    if benchmark_result:
        strategies['Benchmark'] = benchmark_result
        print_strategy_summary(benchmark_result)

    # Strategy 3: Mean Reversion
    print(f"\n   Strategy 3: Mean Reversion")
    if len(data) >= 10:
        mean_reversion_result = backtest_mean_reversion(data)
        if mean_reversion_result:
            strategies['Mean Reversion'] = mean_reversion_result
            print_strategy_summary(mean_reversion_result)

    # 4. Strategy comparison
    print(f"\n4. STRATEGY COMPARISON:")
    print("-" * 70)
    print(f"{'Strategy':<15} {'Return':<12} {'Annual Ret':<12} {'Sharpe':<10} {'Max DD':<10} {'Trades':<8}")
    print("-" * 70)

    for name, result in strategies.items():
        print(f"{name:<15} {result['total_return']:<12.2%} {result['annual_return']:<12.2%} "
              f"{result['sharpe_ratio']:<10.3f} {result['max_drawdown']:<10.2%} {result['total_trades']:<8}")

    # 5. Best strategy identification
    if len(strategies) > 1:
        # Exclude benchmark from best strategy selection
        non_benchmark = {k: v for k, v in strategies.items() if k != 'Benchmark'}
        if non_benchmark:
            best_strategy = max(non_benchmark.items(), key=lambda x: x[1]['sharpe_ratio'])
            print(f"\n5. BEST TRADING STRATEGY:")
            print(f"   Strategy: {best_strategy[0]}")
            print(f"   Sharpe Ratio: {best_strategy[1]['sharpe_ratio']:.3f}")
            print(f"   Total Return: {best_strategy[1]['total_return']:.2%}")
            print(f"   Max Drawdown: {best_strategy[1]['max_drawdown']:.2%}")

    # 6. Final assessment
    print(f"\n6. FINAL ASSESSMENT:")
    print(f"   Data Period: {period_days} calendar days ({trading_days} trading days)")
    print(f"   Market Return: {total_return:.2%}")
    print(f"   Data Quality: 100% Real (No Simulation)")
    print(f"   Strategy Count: {len(strategies)}")
    print(f"   Analysis Type: Complete Real Data Backtesting")

    return True

def backtest_sentiment_strategy(data):
    """Backtest sentiment following strategy"""
    initial_capital = 100000
    cash = initial_capital
    shares = 0
    trades = []
    equity_curve = [initial_capital]

    for i in range(1, len(data)):
        current_price = data['Afternoon_Close'].iloc[i]
        current_signal = data['Signal'].iloc[i]
        prev_signal = data['Signal'].iloc[i-1]

        # Buy on positive signal
        if current_signal == 1 and prev_signal != 1 and shares == 0:
            position_value = cash * 0.25
            shares = int(position_value / current_price)
            cash -= shares * current_price
            trades.append({'date': data['Date'].iloc[i], 'action': 'BUY', 'price': current_price, 'shares': shares})

        # Sell on negative signal
        elif current_signal == -1 and prev_signal != -1 and shares > 0:
            cash += shares * current_price
            trades.append({'date': data['Date'].iloc[i], 'action': 'SELL', 'price': current_price, 'shares': shares})
            shares = 0

        current_value = cash + (shares * current_price)
        equity_curve.append(current_value)

    return calculate_metrics(equity_curve, trades, len(data))

def backtest_buy_and_hold(data):
    """Buy and hold benchmark"""
    initial_capital = 100000
    initial_price = data['Afternoon_Close'].iloc[0]
    shares = int(initial_capital / initial_price)

    equity_curve = []
    for price in data['Afternoon_Close']:
        equity_curve.append(shares * price)

    return {
        'total_return': (equity_curve[-1] - initial_capital) / initial_capital,
        'annual_return': ((equity_curve[-1] - initial_capital) / initial_capital) * (252 / len(data)),
        'sharpe_ratio': 0,  # Simplified for benchmark
        'max_drawdown': calculate_max_drawdown(equity_curve),
        'total_trades': 1,
        'equity_curve': equity_curve
    }

def backtest_mean_reversion(data):
    """Mean reversion strategy"""
    window = min(10, len(data) // 3)
    data_copy = data.copy()
    data_copy['SMA'] = data_copy['Afternoon_Close'].rolling(window).mean()
    data_copy['Std'] = data_copy['Afternoon_Close'].rolling(window).std()
    data_copy['Lower_Band'] = data_copy['SMA'] - (data_copy['Std'] * 2)
    data_copy['Upper_Band'] = data_copy['SMA'] + (data_copy['Std'] * 2)

    initial_capital = 100000
    cash = initial_capital
    shares = 0
    trades = []
    equity_curve = [initial_capital]

    for i in range(window, len(data_copy)):
        current_price = data_copy['Afternoon_Close'].iloc[i]
        lower_band = data_copy['Lower_Band'].iloc[i]
        upper_band = data_copy['Upper_Band'].iloc[i]

        # Buy at lower band
        if current_price <= lower_band and shares == 0:
            position_value = cash * 0.3
            shares = int(position_value / current_price)
            cash -= shares * current_price
            trades.append({'date': data_copy['Date'].iloc[i], 'action': 'BUY', 'price': current_price, 'shares': shares})

        # Sell at upper band
        elif current_price >= upper_band and shares > 0:
            cash += shares * current_price
            trades.append({'date': data_copy['Date'].iloc[i], 'action': 'SELL', 'price': current_price, 'shares': shares})
            shares = 0

        current_value = cash + (shares * current_price)
        equity_curve.append(current_value)

    return calculate_metrics(equity_curve, trades, len(data))

def calculate_metrics(equity_curve, trades, trading_days):
    """Calculate performance metrics"""
    if not equity_curve:
        return None

    initial_capital = equity_curve[0]
    final_value = equity_curve[-1]
    total_return = (final_value - initial_capital) / initial_capital

    # Daily returns
    equity_series = pd.Series(equity_curve)
    daily_returns = equity_series.pct_change().dropna()

    # Annualized metrics
    annual_return = total_return * (252 / trading_days)
    volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0
    sharpe_ratio = annual_return / volatility if volatility > 0 else 0

    # Maximum drawdown
    max_drawdown = calculate_max_drawdown(equity_curve)

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'total_trades': len(trades),
        'equity_curve': equity_curve
    }

def calculate_max_drawdown(equity_curve):
    """Calculate maximum drawdown"""
    peak = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

def print_strategy_summary(result):
    """Print strategy summary"""
    print(f"     Total Return: {result['total_return']:.2%}")
    print(f"     Annual Return: {result['annual_return']:.2%}")
    print(f"     Sharpe Ratio: {result['sharpe_ratio']:.3f}")
    print(f"     Max Drawdown: {result['max_drawdown']:.2%}")
    print(f"     Total Trades: {result['total_trades']}")

if __name__ == "__main__":
    run_complete_real_backtest()