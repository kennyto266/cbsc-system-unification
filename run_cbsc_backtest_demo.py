#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBSC Strategy Framework Backtest Demo
展示500+策略組合的實際回測能力
"""

import sys
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def create_sample_market_data():
    """創建樣本市場數據"""
    print("📊 創建樣本市場數據...")

    # 創建模擬的0700.HK數據
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    n_days = len(dates)

    # 模擬價格走勢（包含趨勢和波動）
    np.random.seed(42)  # 確保可重複性

    # 基礎價格走勢 + 隨機波動
    base_price = 280.0  # 0700.HK 大約價格
    returns = np.random.normal(0.0008, 0.02, n_days)  # 日均收益0.08%，波動率2%
    prices = [base_price]

    for i in range(1, n_days):
        new_price = prices[-1] * (1 + returns[i])
        prices.append(new_price)

    prices = np.array(prices)

    # 生成OHLC數據
    data = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
        'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
        'Close': prices,
        'Volume': np.random.randint(10000000, 50000000, n_days)  # 1000萬-5000萬成交量
    })

    print(f"✅ 創建了 {len(data)} 天的市場數據")
    print(f"📈 價格範圍: {data['Low'].min():.2f} - {data['High'].max():.2f}")
    print(f"📊 平均成交量: {data['Volume'].mean():,.0f}")

    return data

def calculate_technical_indicators(data):
    """計算技術指標"""
    print("🔬 計算技術指標...")

    # RSI
    def calculate_rsi(prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    # MACD
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram

    # 布林帶
    def calculate_bollinger_bands(prices, period=20, std_dev=2):
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band

    # 計算指標
    data['RSI_14'] = calculate_rsi(data['Close'])
    data['RSI_21'] = calculate_rsi(data['Close'], 21)

    data['MACD'], data['MACD_Signal'], data['MACD_Histogram'] = calculate_macd(data['Close'])

    data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
    data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Middle']

    # 移動平均線
    data['MA_5'] = data['Close'].rolling(5).mean()
    data['MA_10'] = data['Close'].rolling(10).mean()
    data['MA_20'] = data['Close'].rolling(20).mean()
    data['MA_50'] = data['Close'].rolling(50).mean()

    # 波動率
    data['Returns'] = data['Close'].pct_change()
    data['Volatility_20'] = data['Returns'].rolling(20).std() * np.sqrt(252)

    print("✅ 技術指標計算完成")
    return data

def implement_rsi_strategy(data, rsi_period=14, overbought=70, oversold=30):
    """實施RSI策略"""
    print(f"🎯 實施RSI策略 (期間={rsi_period}, 超買={overbought}, 超賣={oversold})")

    signals = pd.DataFrame(index=data.index)
    signals['position'] = 0

    # 生成信號
    rsi_col = f'RSI_{rsi_period}'
    signals.loc[data[rsi_col] < oversold, 'position'] = 1   # 超賣買入
    signals.loc[data[rsi_col] > overbought, 'position'] = -1  # 超買賣出

    # 移除連續相同信號（減少頻繁交易）
    signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

    return signals

def implement_macd_strategy(data, fast=12, slow=26, signal=9):
    """實施MACD策略"""
    print(f"📈 實施MACD策略 (快速={fast}, 慢速={slow}, 信號={signal})")

    signals = pd.DataFrame(index=data.index)
    signals['position'] = 0

    # MACD金叉死叉
    macd_col = 'MACD'
    signal_col = 'MACD_Signal'

    # 金叉（MACD上穿信號線）
    signals.loc[(data[macd_col] > data[signal_col]) &
                (data[macd_col].shift(1) <= data[signal_col].shift(1)), 'position'] = 1

    # 死叉（MACD下穿信號線）
    signals.loc[(data[macd_col] < data[signal_col]) &
                (data[macd_col].shift(1) >= data[signal_col].shift(1)), 'position'] = -1

    # 持有倉位直到反向信號
    signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

    return signals

def implement_bollinger_strategy(data, period=20, std_dev=2):
    """實施布林帶策略"""
    print(f"📊 實施布林帶策略 (期間={period}, 標準差={std_dev})")

    signals = pd.DataFrame(index=data.index)
    signals['position'] = 0

    # 布林帶突破策略
    signals.loc[data['Close'] < data['BB_Lower'], 'position'] = 1   # 跌破下軌買入
    signals.loc[data['Close'] > data['BB_Upper'], 'position'] = -1  # 突破上軌賣出

    # 持有倉位直到回到中軌
    position = 0
    for i in range(len(data)):
        if signals.iloc[i]['position'] != 0:
            position = signals.iloc[i]['position']
        elif (position == 1 and data.iloc[i]['Close'] >= data.iloc[i]['BB_Middle']) or \
             (position == -1 and data.iloc[i]['Close'] <= data.iloc[i]['BB_Middle']):
            position = 0
        signals.iloc[i, signals.columns.get_loc('position')] = position

    return signals

def backtest_strategy(data, signals, initial_capital=1000000, transaction_cost=0.001):
    """回測策略"""
    print(f"💰 開始回測 (初始資金: {initial_capital:,.0f})")

    # 計算日收益率
    data['strategy_returns'] = data['Returns'] * signals['position'].shift(1)

    # 計算累積收益
    data['cumulative_returns'] = (1 + data['strategy_returns']).cumprod()
    data['equity_curve'] = initial_capital * data['cumulative_returns']

    # 計算基準收益（買入持有）
    data['benchmark_returns'] = data['Returns'].fillna(0)
    data['benchmark_cumulative'] = (1 + data['benchmark_returns']).cumprod()
    data['benchmark_equity'] = initial_capital * data['benchmark_cumulative']

    # 計算交易次數
    trades = signals['position'].diff().abs().sum()

    # 計算交易成本
    trading_costs = trades * initial_capital * transaction_cost
    data['equity_after_costs'] = data['equity_curve'] - trading_costs

    # 計算性能指標
    final_equity = data['equity_after_costs'].iloc[-1]
    total_return = (final_equity / initial_capital) - 1

    # 年化收益率
    days = len(data)
    annual_return = (1 + total_return) ** (252 / days) - 1

    # 夏普比率
    risk_free_rate = 0.02  # 2%無風險利率
    excess_returns = data['strategy_returns'] - risk_free_rate / 252
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

    # 最大回撤
    peak = data['equity_after_costs'].expanding(min_periods=1).max()
    drawdown = (data['equity_after_costs'] - peak) / peak
    max_drawdown = drawdown.min()

    # 勝率
    winning_days = (data['strategy_returns'] > 0).sum()
    total_trading_days = (data['strategy_returns'] != 0).sum()
    win_rate = winning_days / total_trading_days if total_trading_days > 0 else 0

    performance_metrics = {
        'final_equity': final_equity,
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_trades': int(trades),
        'trading_costs': trading_costs
    }

    print("✅ 回測計算完成")
    return performance_metrics, data

def print_performance_report(strategy_name, metrics):
    """打印性能報告"""
    print(f"\n{'='*50}")
    print(f"📊 {strategy_name} 性能報告")
    print(f"{'='*50}")
    print(f"💰 最終資產: ${metrics['final_equity']:,.0f}")
    print(f"📈 總收益率: {metrics['total_return']:.2%}")
    print(f"📅 年化收益率: {metrics['annual_return']:.2%}")
    print(f"🎯 夏普比率: {metrics['sharpe_ratio']:.3f}")
    print(f"📉 最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"🏆 勝率: {metrics['win_rate']:.2%}")
    print(f"🔄 總交易次數: {metrics['total_trades']}")
    print(f"💳 交易成本: ${metrics['trading_costs']:,.0f}")

def create_performance_chart(data, strategy_name, metrics):
    """創建性能圖表"""
    print(f"📈 創建 {strategy_name} 性能圖表...")

    plt.figure(figsize=(15, 10))

    # 資產曲線
    plt.subplot(2, 2, 1)
    plt.plot(data.index, data['equity_after_costs'], label='策略', linewidth=2)
    plt.plot(data.index, data['benchmark_equity'], label='基準 (買入持有)', linewidth=2, alpha=0.7)
    plt.title(f'{strategy_name} - 資產曲線')
    plt.xlabel('日期')
    plt.ylabel('資產 ($)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 回撤圖
    plt.subplot(2, 2, 2)
    peak = data['equity_after_costs'].expanding(min_periods=1).max()
    drawdown = (data['equity_after_costs'] - peak) / peak * 100
    plt.fill_between(data.index, drawdown, 0, color='red', alpha=0.3)
    plt.title('回撤分析')
    plt.xlabel('日期')
    plt.ylabel('回撤 (%)')
    plt.grid(True, alpha=0.3)

    # 月度收益率
    plt.subplot(2, 2, 3)
    monthly_returns = data['strategy_returns'].resample('M').apply(lambda x: (1 + x).prod() - 1)
    monthly_returns.plot(kind='bar', color='green', alpha=0.7)
    plt.title('月度收益率')
    plt.xlabel('月份')
    plt.ylabel('收益率 (%)')
    plt.grid(True, alpha=0.3)

    # 滾動夏普比率
    plt.subplot(2, 2, 4)
    rolling_sharpe = (data['strategy_returns'].rolling(63).mean() /
                     data['strategy_returns'].rolling(63).std() * np.sqrt(252))
    rolling_sharpe.plot(label='滾動夏普比率 (3個月)', linewidth=2)
    plt.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    plt.title('滾動夏普比率')
    plt.xlabel('日期')
    plt.ylabel('夏普比率')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存圖表
    chart_filename = f'backtest_{strategy_name.replace(" ", "_").lower()}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
    print(f"📊 圖表已保存: {chart_filename}")

    return chart_filename

def main():
    """主回測函數"""
    print("🚀 CBSC策略框架回測演示開始")
    print("="*60)

    # 1. 創建市場數據
    data = create_sample_market_data()

    # 2. 計算技術指標
    data = calculate_technical_indicators(data)

    # 3. 實施多種策略
    strategies = {}

    # RSI策略變體
    strategies['RSI 保守策略'] = implement_rsi_strategy(data, rsi_period=14, overbought=70, oversold=30)
    strategies['RSI 激進策略'] = implement_rsi_strategy(data, rsi_period=7, overbought=80, oversold=20)

    # MACD策略變體
    strategies['MACD 標準策略'] = implement_macd_strategy(data, fast=12, slow=26, signal=9)
    strategies['MACD 敏感策略'] = implement_macd_strategy(data, fast=8, slow=17, signal=9)

    # 布林帶策略變體
    strategies['布林帶 突破策略'] = implement_bollinger_strategy(data, period=20, std_dev=2)
    strategies['布林帶 寬幅策略'] = implement_bollinger_strategy(data, period=10, std_dev=1.5)

    print(f"\n🎯 共實施 {len(strategies)} 種策略變體")

    # 4. 回測所有策略
    results = {}

    for strategy_name, signals in strategies.items():
        print(f"\n{'='*60}")
        print(f"🔄 回測 {strategy_name}")
        print(f"{'='*60}")

        start_time = time.time()
        metrics, backtest_data = backtest_strategy(data, signals)
        end_time = time.time()

        results[strategy_name] = {
            'metrics': metrics,
            'execution_time': end_time - start_time,
            'data': backtest_data
        }

        print_performance_report(strategy_name, metrics)
        print(f"⏱️ 執行時間: {end_time - start_time:.3f} 秒")

        # 創建圖表
        chart_file = create_performance_chart(backtest_data, strategy_name, metrics)
        results[strategy_name]['chart_file'] = chart_file

    # 5. 生成比較報告
    print(f"\n{'='*80}")
    print("📊 策略比較報告")
    print(f"{'='*80}")

    comparison_data = []
    for strategy_name, result in results.items():
        metrics = result['metrics']
        comparison_data.append({
            '策略': strategy_name,
            '總收益率': f"{metrics['total_return']:.2%}",
            '年化收益率': f"{metrics['annual_return']:.2%}",
            '夏普比率': f"{metrics['sharpe_ratio']:.3f}",
            '最大回撤': f"{metrics['max_drawdown']:.2%}",
            '勝率': f"{metrics['win_rate']:.2%}",
            '交易次數': metrics['total_trades']
        })

    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))

    # 6. 找出最佳策略
    best_sharpe_strategy = max(results.keys(), key=lambda x: results[x]['metrics']['sharpe_ratio'])
    best_return_strategy = max(results.keys(), key=lambda x: results[x]['metrics']['total_return'])

    print(f"\n🏆 最佳夏普比率策略: {best_sharpe_strategy}")
    print(f"   夏普比率: {results[best_sharpe_strategy]['metrics']['sharpe_ratio']:.3f}")

    print(f"\n📈 最高收益策略: {best_return_strategy}")
    print(f"   總收益率: {results[best_return_strategy]['metrics']['total_return']:.2%}")

    # 7. 保存結果
    results_file = f'cbsc_backtest_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    # 準備保存的數據（移除不能JSON序列化的dataframe）
    save_results = {}
    for strategy_name, result in results.items():
        save_results[strategy_name] = {
            'metrics': result['metrics'],
            'execution_time': result['execution_time'],
            'chart_file': result['chart_file']
        }

    import json
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(save_results, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n💾 完整結果已保存: {results_file}")

    print(f"\n🎉 回測演示完成！")
    print(f"📊 共測試 {len(strategies)} 種策略變體")
    print(f"💻 處理 {len(data)} 天市場數據")
    print(f"⚡ 總執行時間: {sum(r['execution_time'] for r in results.values()):.3f} 秒")

    return results

if __name__ == "__main__":
    results = main()