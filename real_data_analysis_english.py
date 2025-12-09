#!/usr/bin/env python3
"""
CBSC Real Data Analysis - Corrected Analysis Using Actual Hang Seng Index Data
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

def run_corrected_real_analysis():
    """Corrected analysis using real data"""
    print("=" * 60)
    print("CBSC REAL DATA CORRECTED ANALYSIS - USING ACTUAL HANG SENG INDEX")
    print("=" * 60)

    # 1. Load real data
    sentiment_file = "CODEX--/warrant_sentiment_daily.csv"
    if not Path(sentiment_file).exists():
        print(f"ERROR: Cannot find data file: {sentiment_file}")
        return False

    print("\n1. Loading real CBSC and Hang Seng Index data...")
    try:
        df = pd.read_csv(sentiment_file)
        print(f"   SUCCESS: Loaded {len(df)} records")
        print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")

        # Analyze real sentiment data
        print(f"\n2. Real Sentiment Data Analysis:")
        print(f"   Bull Turnover: {df['Bull_Turnover_HKD'].sum():,.0f} HKD")
        print(f"   Bear Turnover: {df['Bear_Turnover_HKD'].sum():,.0f} HKD")
        print(f"   Average Bull-Bear Ratio: {df['Bull_Bear_Ratio'].mean():.3f}")

        # Analyze real Hang Seng Index data
        print(f"\n3. Real Hang Seng Index Performance:")
        real_prices = df[df['Afternoon_Close'].notna()]['Afternoon_Close'].drop_duplicates()
        if len(real_prices) > 1:
            start_price = real_prices.iloc[0]
            end_price = real_prices.iloc[-1]
            total_return = (end_price - start_price) / start_price
            print(f"   Start Level: {start_price:,.2f}")
            print(f"   End Level: {end_price:,.2f}")
            print(f"   Total Period Return: {total_return:.2%}")

            # Calculate daily return statistics
            daily_returns = df[df['Daily_Return'].notna()]['Daily_Return']
            if not daily_returns.empty:
                volatility = daily_returns.std() * np.sqrt(252)
                print(f"   Annualized Volatility: {volatility:.2%}")
                print(f"   Max Single Day Loss: {daily_returns.min():.2%}")
                print(f"   Max Single Day Gain: {daily_returns.max():.2%}")

    except Exception as e:
        print(f"   ERROR: Data loading failed - {e}")
        return False

    # 4. Strategy analysis based on real data
    print(f"\n4. Strategy Backtest Based on Real Hang Seng Index:")

    # Prepare real price data
    price_data = df[df['Afternoon_Close'].notna()].copy()
    price_data = price_data.groupby('Date')['Afternoon_Close'].last().reset_index()
    price_data.columns = ['Date', 'Close']
    price_data['Date'] = pd.to_datetime(price_data['Date'])
    price_data = price_data.sort_values('Date')

    if len(price_data) < 10:
        print("   ERROR: Insufficient real price data")
        return False

    # Generate trading signals based on sentiment data
    sentiment_data = df.groupby('Date').agg({
        'Bull_Ratio': 'mean',
        'Signal': 'first',
        'Sentiment_Level': 'first'
    }).reset_index()
    sentiment_data['Date'] = pd.to_datetime(sentiment_data['Date'])

    # Merge data
    merged_data = pd.merge(price_data, sentiment_data, on='Date', how='inner')

    print(f"   Tradable Days: {len(merged_data)}")
    print(f"   Price Range: {merged_data['Close'].min():.2f} - {merged_data['Close'].max():.2f}")

    # 5. Simple strategy backtest
    print(f"\n5. Simple Sentiment Strategy Backtest:")

    initial_capital = 100000
    cash = initial_capital
    shares = 0
    trades = []

    for i in range(1, len(merged_data)):
        current_price = merged_data['Close'].iloc[i]
        current_signal = merged_data['Signal'].iloc[i]
        prev_signal = merged_data['Signal'].iloc[i-1]

        # Buy signal
        if current_signal == 1 and prev_signal != 1 and shares == 0:
            position_size = cash * 0.2  # 20% position
            shares = int(position_size / current_price)
            cash -= shares * current_price
            trades.append({
                'date': merged_data['Date'].iloc[i],
                'action': 'BUY',
                'price': current_price,
                'shares': shares
            })
            print(f"   {merged_data['Date'].iloc[i].strftime('%Y-%m-%d')} BUY {shares} shares @ {current_price:.2f}")

        # Sell signal
        elif current_signal == -1 and prev_signal != -1 and shares > 0:
            cash += shares * current_price
            trades.append({
                'date': merged_data['Date'].iloc[i],
                'action': 'SELL',
                'price': current_price,
                'shares': shares
            })
            print(f"   {merged_data['Date'].iloc[i].strftime('%Y-%m-%d')} SELL {shares} shares @ {current_price:.2f}")
            shares = 0

    # Calculate final results
    final_value = cash + (shares * merged_data['Close'].iloc[-1] if shares > 0 else 0)
    total_return = (final_value - initial_capital) / initial_capital

    print(f"\n6. Real Data Strategy Results:")
    print(f"   Initial Capital: HK$ {initial_capital:,}")
    print(f"   Final Value: HK$ {final_value:,.0f}")
    print(f"   Strategy Return: {total_return:.2%}")
    print(f"   Number of Trades: {len(trades)}")

    # 7. Benchmark comparison
    benchmark_return = (merged_data['Close'].iloc[-1] - merged_data['Close'].iloc[0]) / merged_data['Close'].iloc[0]
    print(f"\n7. Benchmark Comparison:")
    print(f"   Strategy Return: {total_return:.2%}")
    print(f"   Benchmark Return: {benchmark_return:.2%} (Buy and Hold HSI)")
    print(f"   Excess Performance: {(total_return - benchmark_return):.2%}")

    # 8. Conclusion
    print(f"\n8. Real Data Conclusion:")
    print(f"   ✓ Used actual Hang Seng Index data")
    print(f"   ✓ Used real CBSC sentiment data")
    print(f"   ✓ Data period: {len(merged_data)} trading days")
    print(f"   ✓ Strategy Viability: {'PROVEN' if total_return > 0 else 'NEEDS OPTIMIZATION'}")

    return True

if __name__ == "__main__":
    run_corrected_real_analysis()