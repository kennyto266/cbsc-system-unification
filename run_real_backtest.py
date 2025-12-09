#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real CBSC Strategy Backtest with Authentic Market Data
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def load_real_market_data():
    """加载真实市场数据"""
    print("Loading real market data...")

    try:
        # 加载真实的HSIF和USDCNH数据
        data = pd.read_csv('acheng_sharpe_results.csv')
        data['Date'] = pd.to_datetime(data['Date'])
        data.set_index('Date', inplace=True)

        print(f"[OK] Loaded real market data: {len(data)} records")
        print(f"Date range: {data.index.min().date()} to {data.index.max().date()}")
        print(f"Assets: HSIF (恒生指數期貨), USDCNH (離岸人民幣)")

        # 重命名列以标准化
        data.rename(columns={
            'HSIF_close': 'HSIF_Close',
            'USDCNH_close': 'USDCNH_Close',
            'HSIF_return': 'HSIF_Return',
            'USDCNH_return': 'USDCNH_Return'
        }, inplace=True)

        return data

    except FileNotFoundError:
        print("[ERROR] Real data file not found. Please ensure 'acheng_sharpe_results.csv' exists.")
        return None

def calculate_real_technical_indicators(data):
    """计算真实数据的技术指标"""
    print("Calculating technical indicators on real data...")

    # 计算HSIF的技术指标
    data['HSIF_RSI_14'] = calculate_rsi(data['HSIF_Close'])
    data['HSIF_RSI_21'] = calculate_rsi(data['HSIF_Close'], 21)

    # MACD
    data['HSIF_MACD'], data['HSIF_MACD_Signal'], data['HSIF_MACD_Histogram'] = calculate_macd(data['HSIF_Close'])

    # 布林带
    data['HSIF_BB_Upper'], data['HSIF_BB_Middle'], data['HSIF_BB_Lower'] = calculate_bollinger_bands(data['HSIF_Close'])

    # 移动平均线
    data['HSIF_MA_5'] = data['HSIF_Close'].rolling(5).mean()
    data['HSIF_MA_10'] = data['HSIF_Close'].rolling(10).mean()
    data['HSIF_MA_20'] = data['HSIF_Close'].rolling(20).mean()
    data['HSIF_MA_50'] = data['HSIF_Close'].rolling(50).mean()

    # 波动率
    data['HSIF_Volatility_20'] = data['HSIF_Return'].rolling(20).std() * np.sqrt(252)

    print("[OK] Technical indicators calculated on real market data")
    return data

def calculate_rsi(prices, period=14):
    """计算RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """计算布林带"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

def implement_real_rsi_strategy(data, rsi_period=14, overbought=70, oversold=30):
    """实施真实RSI策略"""
    print(f"Implementing Real RSI Strategy (period={rsi_period}, overbought={overbought}, oversold={oversold})")

    signals = pd.DataFrame(index=data.index)
    signals['position'] = 0

    # 使用HSIF的RSI指标
    rsi_col = f'HSIF_RSI_{rsi_period}'

    # 确保有足够的数据
    valid_data = data[rsi_col].notna()
    signals.loc[valid_data & (data[rsi_col] < oversold), 'position'] = 1
    signals.loc[valid_data & (data[rsi_col] > overbought), 'position'] = -1

    # 移除连续相同信号
    signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

    return signals

def implement_real_macd_strategy(data, fast=12, slow=26, signal=9):
    """实施真实MACD策略"""
    print(f"Implementing Real MACD Strategy (fast={fast}, slow={slow}, signal={signal})")

    signals = pd.DataFrame(index=data.index)
    signals['position'] = 0

    # MACD金叉死叉
    valid_data = data['HSIF_MACD'].notna() & data['HSIF_MACD_Signal'].notna()

    # 金叉
    signals.loc[valid_data &
                (data['HSIF_MACD'] > data['HSIF_MACD_Signal']) &
                (data['HSIF_MACD'].shift(1) <= data['HSIF_MACD_Signal'].shift(1)), 'position'] = 1

    # 死叉
    signals.loc[valid_data &
                (data['HSIF_MACD'] < data['HSIF_MACD_Signal']) &
                (data['HSIF_MACD'].shift(1) >= data['HSIF_MACD_Signal'].shift(1)), 'position'] = -1

    # 持有仓位直到反向信号
    signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

    return signals

def implement_real_bollinger_strategy(data, period=20, std_dev=2):
    """实施真实布林带策略"""
    print(f"Implementing Real Bollinger Bands Strategy (period={period}, std_dev={std_dev})")

    signals = pd.DataFrame(index=data.index)
    signals['position'] = 0

    # 布林带突破策略
    valid_data = data['HSIF_BB_Lower'].notna() & data['HSIF_BB_Upper'].notna()

    signals.loc[valid_data & (data['HSIF_Close'] < data['HSIF_BB_Lower']), 'position'] = 1
    signals.loc[valid_data & (data['HSIF_Close'] > data['HSIF_BB_Upper']), 'position'] = -1

    # 持有仓位直到回到中轨
    position = 0
    for i in range(len(data)):
        if signals.iloc[i]['position'] != 0:
            position = signals.iloc[i]['position']
        elif valid_data.iloc[i] and ((position == 1 and data.iloc[i]['HSIF_Close'] >= data.iloc[i]['HSIF_BB_Middle']) or
                                     (position == -1 and data.iloc[i]['HSIF_Close'] <= data.iloc[i]['HSIF_BB_Middle'])):
            position = 0
        signals.iloc[i, signals.columns.get_loc('position')] = position

    return signals

def backtest_real_strategy(data, signals, initial_capital=1000000, transaction_cost=0.002, slippage=0.001):
    """回测真实策略（包含滑点和更真实的交易成本）"""
    print(f"Starting Real Backtest (Initial Capital: ${initial_capital:,.0f})")
    print(f"Transaction Cost: {transaction_cost:.1%}, Slippage: {slippage:.1%}")

    # 使用真实的HSIF收益率
    data['strategy_returns'] = data['HSIF_Return'] * signals['position'].shift(1)

    # 应用滑点影响
    data['slippage_cost'] = np.abs(signals['position'].diff()) * slippage
    data['strategy_returns_after_slippage'] = data['strategy_returns'] - data['slippage_cost']

    # 计算累积收益
    data['cumulative_returns'] = (1 + data['strategy_returns_after_slippage']).cumprod()
    data['equity_curve'] = initial_capital * data['cumulative_returns']

    # 计算基准收益（买入持有HSIF）
    data['benchmark_returns'] = data['HSIF_Return'].fillna(0)
    data['benchmark_cumulative'] = (1 + data['benchmark_returns']).cumprod()
    data['benchmark_equity'] = initial_capital * data['benchmark_cumulative']

    # 计算交易次数
    trades = signals['position'].diff().abs().sum()

    # 计算交易成本（更现实）
    trading_costs = trades * initial_capital * transaction_cost
    data['equity_after_costs'] = data['equity_curve'] - trading_costs

    # 计算性能指标
    final_equity = data['equity_after_costs'].iloc[-1]
    total_return = (final_equity / initial_capital) - 1

    # 年化收益率
    days = len(data)
    years = days / 252  # 交易日年化
    annual_return = (1 + total_return) ** (1 / years) - 1

    # 夏普比率（更真实的计算）
    risk_free_rate = 0.025  # 2.5%无风险利率
    excess_returns = data['strategy_returns_after_slippage'] - risk_free_rate / 252
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

    # 最大回撤
    peak = data['equity_after_costs'].expanding(min_periods=1).max()
    drawdown = (data['equity_after_costs'] - peak) / peak
    max_drawdown = drawdown.min()

    # 胜率
    winning_days = (data['strategy_returns_after_slippage'] > 0).sum()
    total_trading_days = (data['strategy_returns_after_slippage'] != 0).sum()
    win_rate = winning_days / total_trading_days if total_trading_days > 0 else 0

    # Calmar比率
    calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

    # Sortino比率
    downside_returns = data['strategy_returns_after_slippage'][data['strategy_returns_after_slippage'] < 0]
    sortino_ratio = (data['strategy_returns_after_slippage'].mean() - risk_free_rate/252) / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

    performance_metrics = {
        'final_equity': final_equity,
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_trades': int(trades),
        'trading_costs': trading_costs,
        'calmar_ratio': calmar_ratio,
        'sortino_ratio': sortino_ratio,
        'years_tested': years
    }

    print("[OK] Real backtest calculation completed")
    return performance_metrics, data

def print_real_performance_report(strategy_name, metrics):
    """打印真实性能报告"""
    print(f"\n{'='*60}")
    print(f"REAL {strategy_name} PERFORMANCE REPORT")
    print(f"{'='*60}")
    print(f"Final Equity: ${metrics['final_equity']:,.0f}")
    print(f"Total Return: {metrics['total_return']:.2%}")
    print(f"Annual Return: {metrics['annual_return']:.2%}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    print(f"Calmar Ratio: {metrics['calmar_ratio']:.3f}")
    print(f"Sortino Ratio: {metrics['sortino_ratio']:.3f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Win Rate: {metrics['win_rate']:.2%}")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Trading Costs: ${metrics['trading_costs']:,.0f}")
    print(f"Years Tested: {metrics['years_tested']:.1f}")

def main():
    """主回测函数"""
    print("="*80)
    print("CBSC STRATEGY FRAMEWORK - REAL DATA BACKTEST")
    print("="*80)

    start_total_time = time.time()

    # 1. 加载真实市场数据
    data = load_real_market_data()
    if data is None:
        return

    # 2. 计算技术指标
    data = calculate_real_technical_indicators(data)

    # 3. 实施多种策略
    strategies = {}

    # RSI策略变体
    strategies['RSI Conservative'] = implement_real_rsi_strategy(data, rsi_period=14, overbought=70, oversold=30)
    strategies['RSI Aggressive'] = implement_real_rsi_strategy(data, rsi_period=21, overbought=80, oversold=20)

    # MACD策略变体
    strategies['MACD Standard'] = implement_real_macd_strategy(data, fast=12, slow=26, signal=9)
    strategies['MACD Sensitive'] = implement_real_macd_strategy(data, fast=8, slow=17, signal=9)

    # 布林带策略变体
    strategies['Bollinger Breakout'] = implement_real_bollinger_strategy(data, period=20, std_dev=2)
    strategies['Bollinger Wide'] = implement_real_bollinger_strategy(data, period=10, std_dev=1.5)

    print(f"\n[INFO] Implemented {len(strategies)} strategy variants on REAL market data")

    # 4. 回测所有策略
    results = {}

    for strategy_name, signals in strategies.items():
        print(f"\n{'='*80}")
        print(f"REAL BACKTESTING: {strategy_name}")
        print(f"{'='*80}")

        start_time = time.time()
        metrics, backtest_data = backtest_real_strategy(data, signals)
        end_time = time.time()

        results[strategy_name] = {
            'metrics': metrics,
            'execution_time': end_time - start_time,
            'data': backtest_data
        }

        print_real_performance_report(strategy_name, metrics)
        print(f"Execution Time: {end_time - start_time:.3f} seconds")

    # 5. 生成比较报告
    print(f"\n{'='*100}")
    print("REAL STRATEGY COMPARISON REPORT")
    print(f"{'='*100}")

    comparison_data = []
    for strategy_name, result in results.items():
        metrics = result['metrics']
        comparison_data.append({
            'Strategy': strategy_name,
            'Total Return': f"{metrics['total_return']:.2%}",
            'Annual Return': f"{metrics['annual_return']:.2%}",
            'Sharpe Ratio': f"{metrics['sharpe_ratio']:.3f}",
            'Calmar Ratio': f"{metrics['calmar_ratio']:.3f}",
            'Max Drawdown': f"{metrics['max_drawdown']:.2%}",
            'Win Rate': f"{metrics['win_rate']:.2%}",
            'Total Trades': metrics['total_trades']
        })

    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))

    # 6. 找出最佳策略
    best_sharpe_strategy = max(results.keys(), key=lambda x: results[x]['metrics']['sharpe_ratio'])
    best_return_strategy = max(results.keys(), key=lambda x: results[x]['metrics']['total_return'])
    best_calmar_strategy = max(results.keys(), key=lambda x: results[x]['metrics']['calmar_ratio'])

    print(f"\n[WINNER] Best Sharpe Ratio: {best_sharpe_strategy}")
    print(f"   Sharpe Ratio: {results[best_sharpe_strategy]['metrics']['sharpe_ratio']:.3f}")

    print(f"\n[WINNER] Highest Return: {best_return_strategy}")
    print(f"   Total Return: {results[best_return_strategy]['metrics']['total_return']:.2%}")

    print(f"\n[WINNER] Best Calmar Ratio: {best_calmar_strategy}")
    print(f"   Calmar Ratio: {results[best_calmar_strategy]['metrics']['calmar_ratio']:.3f}")

    # 7. 市场基准比较
    print(f"\n{'='*80}")
    print("MARKET BENCHMARK COMPARISON")
    print(f"{'='*80}")

    # 计算买入持有HSIF的基准
    hsif_start_price = data['HSIF_Close'].iloc[0]
    hsif_end_price = data['HSIF_Close'].iloc[-1]
    hsif_total_return = (hsif_end_price / hsif_start_price) - 1
    hsif_annual_return = (1 + hsif_total_return) ** (1 / list(results.values())[0]['metrics']['years_tested']) - 1

    print(f"Buy & Hold HSIF:")
    print(f"  Total Return: {hsif_total_return:.2%}")
    print(f"  Annual Return: {hsif_annual_return:.2%}")

    # 找出跑赢基准的策略
    outperforming_strategies = []
    for strategy_name, result in results.items():
        if result['metrics']['total_return'] > hsif_total_return:
            outperforming_strategies.append(strategy_name)

    if outperforming_strategies:
        print(f"\n[BEAT MARKET] Strategies beating Buy & Hold: {', '.join(outperforming_strategies)}")
    else:
        print(f"\n[MARKET BEAT] No strategy outperformed Buy & Hold HSIF")

    # 8. 保存结果
    results_file = f'real_cbsc_backtest_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    save_results = {}
    for strategy_name, result in results.items():
        save_results[strategy_name] = {
            'metrics': result['metrics'],
            'execution_time': result['execution_time']
        }
    save_results['market_benchmark'] = {
        'hsif_total_return': hsif_total_return,
        'hsif_annual_return': hsif_annual_return,
        'outperforming_strategies': outperforming_strategies
    }

    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(save_results, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n[SAVE] Real backtest results saved: {results_file}")

    total_time = time.time() - start_total_time
    print(f"\n[SUCCESS] Real CBSC backtest completed!")
    print(f"[INFO] Data Source: Real HSIF + USDCNH market data")
    print(f"[INFO] Period: {data.index.min().date()} to {data.index.max().date()}")
    print(f"[INFO] Total Records: {len(data)} trading days")
    print(f"[INFO] Strategies Tested: {len(strategies)}")
    print(f"[INFO] Total Execution Time: {total_time:.3f} seconds")

    return results

if __name__ == "__main__":
    results = main()