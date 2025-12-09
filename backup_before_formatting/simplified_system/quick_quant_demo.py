#!/usr/bin/env python3
"""
快速量化交易演示 - 简化版
"""

import sys
import time
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def get_stock_data():
    """获取股票数据"""
    print("Getting stock data...")
    try:
        from api.stock_api import get_hk_stock_data
        data = get_hk_stock_data('0700.HK', 252)
        if data is not None and len(data) > 0:
            if isinstance(data, dict) and 'data' in data:
                # 处理字典格式数据
                close_prices = list(data['data']['close'].values())
                latest_price = close_prices[-1] if close_prices else 0
                record_count = len(close_prices)
            else:
                # 处理DataFrame格式数据
                latest_price = data['close'].iloc[-1]
                record_count = len(data)
            print(f"Success: {record_count} records loaded")
            print(f"Latest price: {latest_price:.2f}")
            return data
        else:
            print("No data available")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def calculate_indicators(data):
    """计算技术指标"""
    print("Calculating technical indicators...")

    if isinstance(data, dict) and 'data' in data:
        # 处理字典格式数据
        close_prices = list(data['data']['close'].values())
        prices = pd.Series(close_prices)
    else:
        # 处理DataFrame格式数据
        prices = data['close']

    # RSI
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # SMA
    sma_20 = prices.rolling(window=20).mean()
    sma_50 = prices.rolling(window=50).mean()

    # EMA
    ema_12 = prices.ewm(span=12).mean()

    # MACD
    ema_26 = prices.ewm(span=26).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9).mean()

    # Bollinger Bands
    sma_20_bb = prices.rolling(window=20).mean()
    std_20 = prices.rolling(window=20).std()
    upper_bb = sma_20_bb + 2 * std_20
    lower_bb = sma_20_bb - 2 * std_20

    results = {
        'rsi': rsi.iloc[-1],
        'sma_20': sma_20.iloc[-1],
        'sma_50': sma_50.iloc[-1],
        'ema_12': ema_12.iloc[-1],
        'macd': macd.iloc[-1],
        'signal': signal.iloc[-1],
        'upper_bb': upper_bb.iloc[-1],
        'lower_bb': lower_bb.iloc[-1],
        'current_price': prices.iloc[-1]
    }

    print(f"RSI(14): {results['rsi']:.1f}")
    print(f"SMA(20): {results['sma_20']:.2f}")
    print(f"SMA(50): {results['sma_50']:.2f}")
    print(f"MACD: {results['macd']:.4f}")

    return results

def analyze_signals(indicators):
    """分析交易信号"""
    print("\nAnalyzing trading signals...")

    signals = []

    # RSI signals
    if indicators['rsi'] < 30:
        signals.append("RSI: BUY - Oversold")
    elif indicators['rsi'] > 70:
        signals.append("RSI: SELL - Overbought")

    # MA signals
    if indicators['current_price'] > indicators['sma_20'] > indicators['sma_50']:
        signals.append("MA: BUY - Uptrend")
    elif indicators['current_price'] < indicators['sma_20'] < indicators['sma_50']:
        signals.append("MA: SELL - Downtrend")

    # MACD signals
    if indicators['macd'] > indicators['signal']:
        signals.append("MACD: BUY - Bullish")
    else:
        signals.append("MACD: SELL - Bearish")

    # Bollinger Bands
    bb_position = (indicators['current_price'] - indicators['lower_bb']) / (indicators['upper_bb'] - indicators['lower_bb'])
    if bb_position > 0.9:
        signals.append("BB: SELL - Near upper band")
    elif bb_position < 0.1:
        signals.append("BB: BUY - Near lower band")

    print("Current signals:")
    for signal in signals:
        print(f"  - {signal}")

    return signals

def simple_backtest(data):
    """简单回测"""
    print("\nRunning simple backtest...")

    if isinstance(data, dict) and 'data' in data:
        # 处理字典格式数据
        close_prices = list(data['data']['close'].values())
        prices = pd.Series(close_prices)
    else:
        # 处理DataFrame格式数据
        prices = data['close']

    # RSI strategy
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Generate signals
    buy_signals = rsi < 30
    sell_signals = rsi > 70

    # Simple positions
    positions = pd.Series(0, index=prices.index)
    positions[buy_signals] = 1
    positions[sell_signals] = -1

    # Holding logic
    current_pos = 0
    for i in range(1, len(positions)):
        if current_pos == 0 and buy_signals.iloc[i]:
            current_pos = 1
        elif current_pos == 1 and sell_signals.iloc[i]:
            current_pos = 0
        positions.iloc[i] = current_pos

    # Calculate returns
    returns = positions * prices.pct_change().shift(-1)
    total_return = (1 + returns).cumprod().iloc[-2] - 1
    annual_return = total_return * 252 / len(returns)

    # Calculate Sharpe ratio
    excess_returns = returns - 0.03/252  # 3% risk-free rate
    if excess_returns.std() > 0:
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    else:
        sharpe_ratio = 0

    # Calculate max drawdown
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # Buy and hold benchmark
    buy_hold_return = (prices.iloc[-1] / prices.iloc[0] - 1)
    buy_hold_annual = buy_hold_return * 252 / len(prices)

    print(f"Strategy Results:")
    print(f"  Total Return: {total_return:.2%}")
    print(f"  Annual Return: {annual_return:.2%}")
    print(f"  Sharpe Ratio: {sharpe_ratio:.3f}")
    print(f"  Max Drawdown: {max_drawdown:.2%}")
    print(f"  Trade Count: {len(positions[positions.diff() != 0])}")

    print(f"\nBenchmark (Buy & Hold):")
    print(f"  Total Return: {buy_hold_return:.2%}")
    print(f"  Annual Return: {buy_hold_annual:.2%}")
    print(f"  Outperformance: {(annual_return - buy_hold_annual):.2%}")

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'buy_hold_return': buy_hold_return
    }

def get_hibor_data():
    """获取HIBOR数据"""
    print("\nGetting HIBOR data...")
    try:
        from api.government_data import get_latest_hibor
        hibor = get_latest_hibor()

        if hibor:
            print(f"HIBOR Overnight: {hibor.get('overnight', 'N/A')}%")
            print(f"HIBOR 1 Week: {hibor.get('1_week', 'N/A')}%")
            print(f"HIBOR 1 Month: {hibor.get('1_month', 'N/A')}%")
            return hibor
        else:
            print("No HIBOR data available")
            return None
    except Exception as e:
        print(f"Error getting HIBOR: {e}")
        return None

def main():
    """主函数"""
    print("=" * 60)
    print("QUANTITATIVE TRADING SYSTEM DEMO")
    print("=" * 60)
    print("Stock: 0700.HK (Tencent)")
    print("Time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)

    # Step 1: Get stock data
    stock_data = get_stock_data()
    if stock_data is None:
        print("Cannot proceed without stock data")
        return

    # Step 2: Calculate indicators
    indicators = calculate_indicators(stock_data)

    # Step 3: Analyze signals
    signals = analyze_signals(indicators)

    # Step 4: Get government data
    hibor_data = get_hibor_data()

    # Step 5: Run backtest
    backtest_results = simple_backtest(stock_data)

    # Step 6: Generate recommendation
    print("\n" + "=" * 60)
    print("INVESTMENT RECOMMENDATION")
    print("=" * 60)

    buy_signals = len([s for s in signals if 'BUY' in s])
    sell_signals = len([s for s in signals if 'SELL' in s])

    if buy_signals > sell_signals:
        recommendation = "BUY - More bullish signals"
        print(f"[+] RECOMMENDATION: {recommendation}")
    elif sell_signals > buy_signals:
        recommendation = "SELL - More bearish signals"
        print(f"[-] RECOMMENDATION: {recommendation}")
    else:
        recommendation = "HOLD - Mixed signals"
        print(f"[=] RECOMMENDATION: {recommendation}")

    print(f"\nCurrent Analysis:")
    print(f"  Price: {indicators['current_price']:.2f} HKD")
    print(f"  RSI: {indicators['rsi']:.1f}")
    print(f"  Trend: {'UPTREND' if indicators['current_price'] > indicators['sma_20'] else 'DOWNTREND'}")
    print(f"  Momentum: {'BULLISH' if indicators['macd'] > indicators['signal'] else 'BEARISH'}")

    if hibor_data:
        print(f"  HIBOR: {hibor_data.get('overnight', 'N/A')}%")
        if hibor_data.get('overnight', 0) > 5:
            print(f"  Market: HIGH INTEREST RATE ENVIRONMENT")
        else:
            print(f"  Market: NORMAL INTEREST RATE ENVIRONMENT")

    if backtest_results:
        print(f"\nPerformance:")
        print(f"  Strategy Annual Return: {backtest_results['annual_return']:.2%}")
        print(f"  Sharpe Ratio: {backtest_results['sharpe_ratio']:.3f}")

        if backtest_results['sharpe_ratio'] > 1.0:
            print(f"  Rating: EXCELLENT")
        elif backtest_results['sharpe_ratio'] > 0.5:
            print(f"  Rating: GOOD")
        else:
            print(f"  Rating: NEEDS IMPROVEMENT")

    print("\n" + "=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("Quantitative trading system operational with:")
    print("  [+] Real-time stock data integration")
    print("  [+] Technical indicator calculations")
    print("  [+] Trading signal generation")
    print("  [+] Strategy backtesting")
    print("  [+] Government economic data")
    print("  [+] Investment recommendations")

    return {
        'stock_data_loaded': len(stock_data) if stock_data is not None else 0,
        'indicators_calculated': len(indicators) if indicators else 0,
        'signals_generated': len(signals),
        'backtest_completed': backtest_results is not None,
        'recommendation': recommendation
    }

if __name__ == "__main__":
    result = main()
    print(f"\nDemo completed with result: {result}")