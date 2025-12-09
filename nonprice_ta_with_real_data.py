#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Non-Price TA System with Real Government Data
使用真實香港政府經濟數據進行技術分析
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
    """加載真實HIBOR數據"""
    try:
        with open('gov_crawler/real_data/hibor_data.json', 'r', encoding='utf-8') as f:
            hibor_data = json.load(f)

        # 解析HIBOR數據
        overnight_rates = []
        dates = []

        for record in hibor_data:
            if record['tenor'] == 'Overnight':
                overnight_rates.append(float(record['rate']))
                dates.append(pd.to_datetime(record['date']))

        hibor_series = pd.Series(overnight_rates, index=dates)
        hibor_series = hibor_series.sort_index()

        print(f"✅ Loaded {len(hibor_series)} HIBOR overnight rates")
        print(f"   Date range: {hibor_series.index[0].date()} to {hibor_series.index[-1].date()}")
        print(f"   Rate range: {hibor_series.min():.2f}% - {hibor_series.max():.2f}%")

        return hibor_series

    except Exception as e:
        print(f"❌ Failed to load HIBOR data: {e}")
        return None

def load_real_gdp_data():
    """加載真實GDP數據"""
    try:
        with open('gov_crawler/real_data/gdp_data.json', 'r', encoding='utf-8') as f:
            gdp_data = json.load(f)

        # 解析GDP數據
        gdp_values = []
        dates = []

        for record in gdp_data:
            if 'quarter' in record and 'gdp_growth' in record:
                gdp_values.append(float(record['gdp_growth']))
                # Convert quarter to date (e.g., "2024Q1" -> 2024-03-31)
                quarter_str = record['quarter']
                year, quarter = quarter_str.split('Q')
                month = (int(quarter) - 1) * 3 + 1
                date = pd.to_datetime(f"{year}-{month:02d}-01")
                dates.append(date)

        gdp_series = pd.Series(gdp_values, index=dates)
        gdp_series = gdp_series.sort_index()

        print(f"✅ Loaded {len(gdp_series)} GDP growth rates")
        print(f"   Date range: {gdp_series.index[0].date()} to {gdp_series.index[-1].date()}")
        print(f"   Growth range: {gdp_series.min():.1f}% - {gdp_series.max():.1f}%")

        return gdp_series

    except Exception as e:
        print(f"❌ Failed to load GDP data: {e}")
        return None

def load_real_trade_data():
    """加載真實貿易數據"""
    try:
        with open('gov_crawler/real_data/trade_data.json', 'r', encoding='utf-8') as f:
            trade_data = json.load(f)

        # 解析貿易數據
        trade_values = []
        dates = []

        for record in trade_data:
            if 'month' in record and 'total_trade' in record:
                trade_values.append(float(record['total_trade']))
                dates.append(pd.to_datetime(record['month']))

        trade_series = pd.Series(trade_values, index=dates)
        trade_series = trade_series.sort_index()

        print(f"✅ Loaded {len(trade_series)} total trade values")
        print(f"   Date range: {trade_series.index[0].date()} to {trade_series.index[-1].date()}")
        print(f"   Trade range: {trade_series.min():.0f} - {trade_series.max():.0f}")

        return trade_series

    except Exception as e:
        print(f"❌ Failed to load trade data: {e}")
        return None

def get_stock_data(symbol="0700.HK", days=365):
    """獲取股票數據"""
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
            print(f"❌ Failed to get stock data: HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error getting stock data: {e}")
        return None

def calculate_nonprice_indicators(gov_data):
    """計算非價格技術指標"""
    print("\n📊 Calculating non-price technical indicators...")

    indicators = {}

    for data_type, series in gov_data.items():
        print(f"   Processing {data_type} indicators...")

        try:
            # RSI on non-price data
            def calculate_rsi(data, period=14):
                delta = data.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi

            # MACD on non-price data
            def calculate_macd(data, fast=12, slow=26, signal=9):
                if len(data) < slow:
                    return None, None, None
                ema_fast = data.ewm(span=fast).mean()
                ema_slow = data.ewm(span=slow).mean()
                macd_line = ema_fast - ema_slow
                signal_line = macd_line.ewm(span=signal).mean()
                histogram = macd_line - signal_line
                return macd_line, signal_line, histogram

            # Moving averages
            def calculate_ma(data, periods=[5, 10, 20]):
                mas = {}
                for period in periods:
                    if len(data) >= period:
                        mas[f'ma_{period}'] = data.rolling(window=period).mean()
                return mas

            # Calculate indicators
            indicators[data_type] = {
                'rsi_14': calculate_rsi(series, 14),
                'rsi_30': calculate_rsi(series, 30),
                'macd': calculate_macd(series),
                'ma': calculate_ma(series),
                'rate_of_change': series.pct_change(periods=10),
                'volatility': series.rolling(window=min(20, len(series)//2)).std(),
                'z_score': (series - series.rolling(window=min(20, len(series)//2)).mean()) / series.rolling(window=min(20, len(series)//2)).std()
            }

            print(f"   ✅ Generated {data_type} indicators")

        except Exception as e:
            print(f"   ❌ Failed to calculate {data_type} indicators: {e}")

    return indicators

def generate_hibor_trading_signals(hibor_indicators, stock_data):
    """基於HIBOR數據生成交易信號"""
    print("\n🎯 Generating HIBOR-based trading signals...")

    if 'rsi_14' not in hibor_indicators:
        return None

    hibor_rsi = hibor_indicators['rsi_14']
    hibor_macd = hibor_indicators['macd']
    macd_line, signal_line, histogram = hibor_macd

    # HIBOR trading logic (reverse logic - high rates are bearish for stocks)
    signals = pd.DataFrame(index=stock_data.index)
    signals['hibor_rsi'] = hibor_rsi.reindex(stock_data.index, method='ffill')
    signals['macd_line'] = macd_line.reindex(stock_data.index, method='ffill')
    signals['signal_line'] = signal_line.reindex(stock_data.index, method='ffill')

    # Generate signals
    buy_signals = (
        (signals['hibor_rsi'] > 70) &  # HIBOR RSI overbought (rates likely to fall)
        (signals['hibor_rsi'].shift(1) <= 70)
    ) | (
        (signals['macd_line'] < signals['signal_line']) &  # MACD bearish crossover
        (signals['macd_line'].shift(1) >= signals['signal_line'].shift(1))
    )

    sell_signals = (
        (signals['hibor_rsi'] < 30) &  # HIBOR RSI oversold (rates likely to rise)
        (signals['hibor_rsi'].shift(1) >= 30)
    ) | (
        (signals['macd_line'] > signals['signal_line']) &  # MACD bullish crossover
        (signals['macd_line'].shift(1) <= signals['signal_line'].shift(1))
    )

    signals['signal'] = 0
    signals.loc[buy_signals, 'signal'] = 1  # Buy when HIBOR is overbought
    signals.loc[sell_signals, 'signal'] = -1  # Sell when HIBOR is oversold

    print(f"   ✅ Generated {signals['signal'].abs().sum()} HIBOR trading signals")

    return signals

def backtest_hibor_strategy(stock_data, signals):
    """回測HIBOR策略"""
    print("\n📈 Backtesting HIBOR strategy...")

    if signals is None:
        return None

    try:
        # Forward fill signals
        positions = signals['signal'].replace(0, np.nan).ffill().fillna(0)

        # Calculate returns
        returns = stock_data['close'].pct_change()
        strategy_returns = positions.shift(1) * returns

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
        total_trades = len(positions[positions.diff() != 0])

        if len(winning_trades) + len(strategy_returns[strategy_returns < 0]) > 0:
            win_rate = len(winning_trades) / (len(winning_trades) + len(strategy_returns[strategy_returns < 0]))
        else:
            win_rate = 0

        result = {
            'strategy_type': 'HIBOR-Based',
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'data_points': len(strategy_returns)
        }

        print(f"   ✅ HIBOR strategy backtest completed")
        return result

    except Exception as e:
        print(f"   ❌ HIBOR backtest failed: {e}")
        return None

def compare_with_price_only_strategy(stock_data):
    """與價格策略比較"""
    print("\n🔄 Comparing with price-only RSI strategy...")

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
            'max_drawdown': max_drawdown
        }

        print(f"   ✅ Price-only RSI analysis completed")
        return result

    except Exception as e:
        print(f"   ❌ Price-only analysis failed: {e}")
        return None

def main():
    """主要函數"""
    print("=" * 80)
    print("🏛️ NON-PRICE TECHNICAL ANALYSIS WITH REAL GOVERNMENT DATA")
    print("   Using Real HIBOR, GDP, and Trade Data from Hong Kong Government")
    print("=" * 80)

    try:
        # Load real government data
        print("\n📁 Loading real government data...")

        gov_data = {}

        # Load HIBOR data
        hibor_series = load_real_hibor_data()
        if hibor_series is not None:
            gov_data['hibor'] = hibor_series

        # Load GDP data
        gdp_series = load_real_gdp_data()
        if gdp_series is not None:
            gov_data['gdp'] = gdp_series

        # Load trade data
        trade_series = load_real_trade_data()
        if trade_series is not None:
            gov_data['trade'] = trade_series

        if not gov_data:
            print("❌ No government data loaded. Exiting.")
            return False

        print(f"✅ Loaded {len(gov_data)} government data sources")

        # Get stock data
        print("\n📈 Loading stock data...")
        stock_data = get_stock_data("0700.HK", 365)

        if stock_data is None:
            print("❌ Could not load stock data")
            return False

        print(f"✅ Loaded {len(stock_data)} days of 0700.HK data")
        print(f"   Price range: ${stock_data['close'].min():.2f} - ${stock_data['close'].max():.2f}")

        # Calculate non-price indicators
        gov_indicators = calculate_nonprice_indicators(gov_data)

        if not gov_indicators:
            print("❌ Could not calculate indicators")
            return False

        # Focus on HIBOR strategy (most reliable data)
        if 'hibor' in gov_indicators:
            print("\n🎯 Implementing HIBOR-based trading strategy...")

            # Generate HIBOR trading signals
            signals = generate_hibor_trading_signals(gov_indicators['hibor'], stock_data)

            if signals is not None:
                # Backtest HIBOR strategy
                hibor_result = backtest_hibor_strategy(stock_data, signals)

                if hibor_result is not None:
                    # Compare with price-only strategy
                    price_result = compare_with_price_only_strategy(stock_data)

                    # Display results
                    print(f"\n{'='*80}")
                    print("📊 STRATEGY COMPARISON RESULTS")
                    print(f"{'='*80}")

                    print(f"\n🏛️ HIBOR-BASED STRATEGY:")
                    print(f"   Total Return: {hibor_result['total_return']:.2%}")
                    print(f"   Annual Return: {hibor_result['annual_return']:.2%}")
                    print(f"   Sharpe Ratio: {hibor_result['sharpe_ratio']:.3f}")
                    print(f"   Max Drawdown: {hibor_result['max_drawdown']:.2%}")
                    print(f"   Win Rate: {hibor_result['win_rate']:.1%}")
                    print(f"   Total Trades: {hibor_result['total_trades']}")

                    if price_result is not None:
                        print(f"\n💰 PRICE-ONLY RSI STRATEGY:")
                        print(f"   Total Return: {price_result['total_return']:.2%}")
                        print(f"   Sharpe Ratio: {price_result['sharpe_ratio']:.3f}")
                        print(f"   Max Drawdown: {price_result['max_drawdown']:.2%}")

                        # Calculate alpha
                        alpha = hibor_result['total_return'] - price_result['total_return']
                        sharpe_improvement = hibor_result['sharpe_ratio'] - price_result['sharpe_ratio']

                        print(f"\n🚀 NON-PRICE DATA ALPHA:")
                        print(f"   Alpha: {alpha:.2%}")
                        print(f"   Sharpe Improvement: {sharpe_improvement:.3f}")

                        # Determine winner
                        if hibor_result['sharpe_ratio'] > price_result['sharpe_ratio']:
                            print(f"\n🏆 CONCLUSION: HIBOR strategy OUTPERFORMS price-only approach")
                        else:
                            print(f"\n⚠️ CONCLUSION: HIBOR strategy needs refinement")

                    # Save results
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_data = {
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': '0700.HK',
                        'government_data_sources': list(gov_data.keys()),
                        'hibor_strategy_result': hibor_result,
                        'price_only_result': price_result,
                        'comparison': {
                            'alpha': hibor_result['total_return'] - (price_result['total_return'] if price_result else 0),
                            'sharpe_improvement': hibor_result['sharpe_ratio'] - (price_result['sharpe_ratio'] if price_result else 0)
                        },
                        'data_points': {
                            'stock_data': len(stock_data),
                            'hibor_data': len(gov_data.get('hibor', [])),
                            'gdp_data': len(gov_data.get('gdp', [])),
                            'trade_data': len(gov_data.get('trade', []))
                        }
                    }

                    filename = f'nonprice_real_data_analysis_{timestamp}.json'
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

                    print(f"\n💾 Results saved: {filename}")

                    return True

        print("❌ HIBOR strategy implementation failed")
        return False

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🎉 Non-price TA analysis completed successfully!")
        else:
            print("\n❌ Non-price TA analysis failed!")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)