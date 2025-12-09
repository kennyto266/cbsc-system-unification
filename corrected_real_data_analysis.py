#!/usr/bin/env python3
"""
CBSC Real Data Analysis - 使用真实恒生指数数据的修正分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

def run_corrected_real_analysis():
    """使用真实数据的修正分析"""
    print("=" * 60)
    print("CBSC 真实数据修正分析 - 使用恒生指数实际数据")
    print("=" * 60)

    # 1. 加载真实数据
    sentiment_file = "CODEX--/warrant_sentiment_daily.csv"
    if not Path(sentiment_file).exists():
        print(f"ERROR: 找不到数据文件: {sentiment_file}")
        return False

    print("\n1. 加载真实CBSC和恒生指数数据...")
    try:
        df = pd.read_csv(sentiment_file)
        print(f"   SUCCESS: 加载 {len(df)} 条记录")
        print(f"   日期范围: {df['Date'].min()} 到 {df['Date'].max()}")

        # 分析真实情绪数据
        print(f"\n2. 真实情绪数据分析:")
        print(f"   牛证成交额: {df['Bull_Turnover_HKD'].sum():,.0f} HKD")
        print(f"   熊证成交额: {df['Bear_Turnover_HKD'].sum():,.0f} HKD")
        print(f"   平均牛熊比例: {df['Bull_Bear_Ratio'].mean():.3f}")

        # 分析真实恒生指数数据
        print(f"\n3. 真实恒生指数表现:")
        real_prices = df[df['Afternoon_Close'].notna()]['Afternoon_Close'].drop_duplicates()
        if len(real_prices) > 1:
            start_price = real_prices.iloc[0]
            end_price = real_prices.iloc[-1]
            total_return = (end_price - start_price) / start_price
            print(f"   起始点位: {start_price:,.2f}")
            print(f"   结束点位: {end_price:,.2f}")
            print(f"   期间总回报: {total_return:.2%}")

            # 计算日收益率统计
            daily_returns = df[df['Daily_Return'].notna()]['Daily_Return']
            if not daily_returns.empty:
                volatility = daily_returns.std() * np.sqrt(252)
                print(f"   年化波动率: {volatility:.2%}")
                print(f"   最大单日跌幅: {daily_returns.min():.2%}")
                print(f"   最大单日涨幅: {daily_returns.max():.2%}")

    except Exception as e:
        print(f"   ERROR: 数据加载失败 - {e}")
        return False

    # 4. 基于真实数据的策略分析
    print(f"\n4. 基于真实恒生指数的策略回测:")

    # 准备真实价格数据
    price_data = df[df['Afternoon_Close'].notna()].copy()
    price_data = price_data.groupby('Date')['Afternoon_Close'].last().reset_index()
    price_data.columns = ['Date', 'Close']
    price_data['Date'] = pd.to_datetime(price_data['Date'])
    price_data = price_data.sort_values('Date')

    if len(price_data) < 10:
        print("   ERROR: 真实价格数据不足")
        return False

    # 生成交易信号基于情绪数据
    sentiment_data = df.groupby('Date').agg({
        'Bull_Ratio': 'mean',
        'Signal': 'first',
        'Sentiment_Level': 'first'
    }).reset_index()
    sentiment_data['Date'] = pd.to_datetime(sentiment_data['Date'])

    # 合并数据
    merged_data = pd.merge(price_data, sentiment_data, on='Date', how='inner')

    print(f"   可交易天数: {len(merged_data)}")
    print(f"   价格范围: {merged_data['Close'].min():.2f} - {merged_data['Close'].max():.2f}")

    # 5. 简单策略回测
    print(f"\n5. 简单情绪策略回测:")

    initial_capital = 100000
    cash = initial_capital
    shares = 0
    trades = []

    for i in range(1, len(merged_data)):
        current_price = merged_data['Close'].iloc[i]
        current_signal = merged_data['Signal'].iloc[i]
        prev_signal = merged_data['Signal'].iloc[i-1]

        # 买入信号
        if current_signal == 1 and prev_signal != 1 and shares == 0:
            position_size = cash * 0.2  # 20%仓位
            shares = int(position_size / current_price)
            cash -= shares * current_price
            trades.append({
                'date': merged_data['Date'].iloc[i],
                'action': 'BUY',
                'price': current_price,
                'shares': shares
            })
            print(f"   {merged_data['Date'].iloc[i].strftime('%Y-%m-%d')} BUY {shares}股 @ {current_price:.2f}")

        # 卖出信号
        elif current_signal == -1 and prev_signal != -1 and shares > 0:
            cash += shares * current_price
            trades.append({
                'date': merged_data['Date'].iloc[i],
                'action': 'SELL',
                'price': current_price,
                'shares': shares
            })
            print(f"   {merged_data['Date'].iloc[i].strftime('%Y-%m-%d')} SELL {shares}股 @ {current_price:.2f}")
            shares = 0

    # 计算最终结果
    final_value = cash + (shares * merged_data['Close'].iloc[-1] if shares > 0 else 0)
    total_return = (final_value - initial_capital) / initial_capital

    print(f"\n6. 真实数据策略结果:")
    print(f"   初始资金: HK$ {initial_capital:,}")
    print(f"   最终价值: HK$ {final_value:,.0f}")
    print(f"   策略回报: {total_return:.2%}")
    print(f"   交易次数: {len(trades)}")

    # 7. 与基准比较
    benchmark_return = (merged_data['Close'].iloc[-1] - merged_data['Close'].iloc[0]) / merged_data['Close'].iloc[0]
    print(f"\n7. 基准比较:")
    print(f"   策略回报: {total_return:.2%}")
    print(f"   基准回报: {benchmark_return:.2%} (买入持有恒生指数)")
    print(f"   超额表现: {(total_return - benchmark_return):.2%}")

    # 8. 结论
    print(f"\n8. 真实数据结论:")
    print(f"   ✓ 使用真实恒生指数数据")
    print(f"   ✓ 使用真实CBSC情绪数据")
    print(f"   ✓ 数据期间: {len(merged_data)} 个交易日")
    print(f"   ✓ 策略可行性: {'PROVEN' if total_return > 0 else 'NEEDS OPTIMIZATION'}")

    return True

if __name__ == "__main__":
    run_corrected_real_analysis()