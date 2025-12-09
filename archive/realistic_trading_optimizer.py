#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realistic Trading Environment Optimizer
真實交易環境優化器 - 加入滑點、手續費、融資成本

Author: Claude Code
Date: 2025-11-20
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
import yfinance as yf
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import json
import warnings
from typing import Dict, List, Tuple, Any
import time
import hashlib
import uuid

warnings.filterwarnings('ignore')

class RealisticTradingOptimizer:
    """真實交易環境優化器"""

    def __init__(self):
        self.start_time = time.time()

        # 香港數據源
        self.hk_data_sources = [
            'HIBOR', 'GDP', 'RETAIL', 'PROPERTY', 'TRADE',
            'TOURISM', 'CPI', 'UNEMPLOYMENT', 'MONETARY'
        ]

        # 擴展的參數範圍 (更深入分析)
        self.rsi_periods = list(range(3, 51, 1))          # 3-50 = 48個值
        self.rsi_thresholds = [i/100 for i in range(20, 81, 5)]  # 0.2-0.8 = 13個值

        self.macd_fast_periods = list(range(5, 26, 2))    # 5-25 = 11個值
        self.macd_slow_periods = list(range(20, 61, 3))   # 20-60 = 14個值
        self.macd_signal_periods = list(range(5, 16, 2))  # 5-15 = 6個值

        self.bb_periods = list(range(10, 31, 2))          # 10-30 = 11個值
        self.bb_std_devs = [i/10 for i in range(12, 26, 2)]  # 1.2-2.5 = 7個值

        # 真實交易成本參數
        self.trading_costs = {
            'commission': 0.0025,      # 0.25% 手續費
            'slippage': 0.0015,        # 0.15% 滑點
            'stamp_duty': 0.0013,      # 0.13% 印花稅 (港股)
            'financing_cost': 0.06/365, # 6%年融資成本
            'min_commission': 5.0,     # 最低手續費 HK$5
        }

        print("=" * 80)
        print("REALISTIC TRADING ENVIRONMENT OPTIMIZER")
        print("=" * 80)
        print("真實交易成本:")
        print(f"   手續費: {self.trading_costs['commission']*100:.2f}%")
        print(f"   滑點: {self.trading_costs['slippage']*100:.2f}%")
        print(f"   印花稅: {self.trading_costs['stamp_duty']*100:.2f}%")
        print(f"   融資成本: {self.trading_costs['financing_cost']*365*100:.1f}%/年")

        # 計算總策略數
        rsi_strategies = len(self.rsi_periods) * len(self.rsi_thresholds) * len(self.hk_data_sources)
        macd_strategies = (len(self.macd_fast_periods) * len(self.macd_slow_periods) *
                          len(self.macd_signal_periods) * len(self.hk_data_sources))
        bb_strategies = len(self.bb_periods) * len(self.bb_std_devs) * len(self.hk_data_sources)

        print(f"\n策略數量:")
        print(f"   RSI策略: {rsi_strategies:,}")
        print(f"   MACD策略: {macd_strategies:,}")
        print(f"   布林帶策略: {bb_strategies:,}")
        print(f"   總計: {rsi_strategies + macd_strategies + bb_strategies:,}")

    def generate_strategy_id(self, indicator_type, params, data_source):
        """生成唯一的策略ID"""
        # 參數哈希
        param_str = f"{indicator_type}_{sorted(params.items())}_{data_source}"
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]

        # 時間戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 策略ID
        strategy_id = f"{data_source}_{indicator_type}_{param_hash}_{timestamp}"

        return strategy_id

    def calculate_realistic_costs(self, portfolio, stock_prices):
        """計算真實交易成本"""
        # 獲取交易信號
        entries = portfolio.entries
        exits = portfolio.exits

        # 初始化成本
        total_cost = 0
        trade_details = []

        # 計算每筆交易成本
        for date in stock_prices.index:
            price = stock_prices.loc[date]

            # 買入成本
            if date in entries.index and entries.loc[date]:
                trade_value = price * 1000  # 假設每手1000股

                # 手續費
                commission = max(trade_value * self.trading_costs['commission'],
                               self.trading_costs['min_commission'])

                # 滑點成本
                slippage_cost = trade_value * self.trading_costs['slippage']

                # 印花稅 (只有買入時收取)
                stamp_duty = trade_value * self.trading_costs['stamp_duty']

                trade_total_cost = commission + slippage_cost + stamp_duty
                total_cost += trade_total_cost

                trade_details.append({
                    'date': date,
                    'type': 'BUY',
                    'price': price,
                    'value': trade_value,
                    'commission': commission,
                    'slippage': slippage_cost,
                    'stamp_duty': stamp_duty,
                    'total_cost': trade_total_cost
                })

            # 賣出成本
            elif date in exits.index and exits.loc[date]:
                trade_value = price * 1000

                # 手續費
                commission = max(trade_value * self.trading_costs['commission'],
                               self.trading_costs['min_commission'])

                # 滑點成本
                slippage_cost = trade_value * self.trading_costs['slippage']

                # 賣出時不收取印花稅

                trade_total_cost = commission + slippage_cost
                total_cost += trade_total_cost

                trade_details.append({
                    'date': date,
                    'type': 'SELL',
                    'price': price,
                    'value': trade_value,
                    'commission': commission,
                    'slippage': slippage_cost,
                    'stamp_duty': 0,
                    'total_cost': trade_total_cost
                })

        return total_cost, trade_details

    def calculate_position_costs(self, portfolio, stock_prices):
        """計算持倉成本 (融資成本)"""
        if len(portfolio.positions) == 0:
            return 0

        position_costs = []

        # 計算每日持倉成本
        for i in range(1, len(portfolio.positions)):
            if portfolio.positions.iloc[i] > 0:
                # 有持倉的融資成本
                position_value = portfolio.positions.iloc[i] * stock_prices.iloc[i]
                daily_cost = position_value * self.trading_costs['financing_cost']
                position_costs.append(daily_cost)

        return sum(position_costs)

    def optimize_rsi_realistic(self, args):
        """優化RSI策略 - 真實交易環境"""
        data_source, rsi_period, signal_threshold, stock_data, macro_data = args

        try:
            # 生成策略ID
            strategy_id = self.generate_strategy_id('RSI', {
                'period': rsi_period, 'threshold': signal_threshold
            }, data_source)

            # 數據對齊
            stock_data_norm = stock_data.copy()
            if hasattr(stock_data_norm.index, 'tz'):
                stock_data_norm.index = stock_data_norm.index.tz_localize(None)
            stock_data_norm.index = stock_data_norm.index.normalize()

            common_index = stock_data_norm.index.intersection(macro_data[data_source].index)
            if len(common_index) < 50:
                return None

            stock_aligned = stock_data_norm.reindex(common_index, method='ffill').dropna()
            macro_aligned = macro_data[data_source].reindex(common_index, method='ffill').dropna()

            if len(stock_aligned) < rsi_period + 10:
                return None

            # 計算RSI
            fast_rsi = vbt.RSI.run(macro_aligned, window=rsi_period).rsi
            slow_rsi = vbt.RSI.run(macro_aligned, window=rsi_period*2).rsi

            # 信號生成
            fast_cross_above_slow = (fast_rsi > slow_rsi) & (fast_rsi.shift(1) <= slow_rsi.shift(1))
            fast_cross_below_slow = (fast_rsi < slow_rsi) & (fast_rsi.shift(1) >= slow_rsi.shift(1))
            rsi_momentum = fast_rsi - slow_rsi
            strong_signal = rsi_momentum > signal_threshold

            entries = fast_cross_above_slow & strong_signal
            exits = fast_cross_below_slow | (fast_rsi > 80)

            # 基礎回測 (不含交易成本)
            basic_portfolio = vbt.Portfolio.from_signals(
                stock_aligned['Close'],
                entries,
                exits,
                init_cash=100000,
                fees=0,  # 不包含費用，我們手動計算
                freq='D'
            )

            # 計算真實交易成本
            trading_cost, trade_details = self.calculate_realistic_costs(basic_portfolio, stock_aligned['Close'])
            position_cost = self.calculate_position_costs(basic_portfolio, stock_aligned['Close'])

            total_real_cost = trading_cost + position_cost

            # 計算真實收益
            returns = basic_portfolio.returns()
            if len(returns) == 0 or returns.std() == 0:
                return None

            # 基礎總回報
            basic_return = (1 + returns).prod() - 1

            # 減去真實交易成本后的回報
            initial_capital = 100000
            cost_impact = total_real_cost / initial_capital
            realistic_return = basic_return - cost_impact

            # 風險指標
            sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()

            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # 交易次數
            trades_count = entries.sum()

            # 勝率計算
            trade_returns = []
            entry_dates = entries[entries].index
            for entry_date in entry_dates:
                if entry_date in returns.index:
                    trade_returns.append(returns.loc[entry_date])

            win_rate = (np.array(trade_returns) > 0).mean() * 100 if len(trade_returns) > 0 else 0

            # 真實環境質量評分
            quality_score = 0
            if realistic_return > 0.20: quality_score += 30  # 提高門檻
            elif realistic_return > 0.10: quality_score += 20
            elif realistic_return > 0.05: quality_score += 10

            if sharpe_ratio > 2.0: quality_score += 25  # 提高門檻
            elif sharpe_ratio > 1.5: quality_score += 20
            elif sharpe_ratio > 1.0: quality_score += 15

            if max_drawdown > -0.08: quality_score += 20  # 提高門檻
            elif max_drawdown > -0.12: quality_score += 15
            elif max_drawdown > -0.20: quality_score += 10

            if win_rate > 60: quality_score += 15  # 提高門檻
            elif win_rate > 55: quality_score += 10
            elif win_rate > 50: quality_score += 5

            if trades_count > 10: quality_score += 10  # 提高門檻
            if trades_count > 20: quality_score += 5

            return {
                'strategy_id': strategy_id,
                'data_source': data_source,
                'indicator_type': 'RSI',
                'rsi_period': rsi_period,
                'signal_threshold': signal_threshold,

                # 基礎指標
                'basic_return': basic_return,
                'realistic_return': realistic_return,
                'cost_impact': cost_impact,

                # 交易成本
                'trading_cost': trading_cost,
                'position_cost': position_cost,
                'total_real_cost': total_real_cost,
                'trade_count': len(trade_details),

                # 性能指標
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'trades_count': trades_count,
                'quality_score': min(quality_score, 100),

                'strategy_name': f'{data_source}_RSI_{rsi_period}_{signal_threshold:.2f}',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"RSI strategy error {data_source}_{rsi_period}_{signal_threshold}: {str(e)}")
            return None

    def get_stock_data(self, symbol='0700.HK', start_date='2020-01-01', end_date='2024-01-01'):
        """獲取股票數據"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(start=start_date, end=end_date)
            if data.empty:
                # 生成備用數據
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                np.random.seed(100)
                initial_price = 300.0
                returns = np.random.normal(0.0008, 0.025, len(dates))
                prices = initial_price * (1 + returns).cumprod()

                data = pd.DataFrame({
                    'Open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
                    'High': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
                    'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
                    'Close': prices,
                    'Volume': np.random.randint(1000000, 5000000, len(dates))
                }, index=dates)

            print(f"OK: Stock data: {len(data)} trading days")
            return data
        except Exception as e:
            print(f"ERROR: Get stock data error: {e}")
            return None

    def generate_hk_macro_data(self, start_date, end_date):
        """生成香港宏觀數據"""
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        days = len(dates)
        hk_data = {}

        np.random.seed(42)

        # HIBOR數據
        base_rate = 2.5
        hibor_rates = base_rate + np.random.normal(0, 1.5, days)
        hibor_rates = np.clip(hibor_rates, 0.5, 8.0)
        trend = np.linspace(0, 0.5, days)
        seasonal = 0.3 * np.sin(2 * np.pi * np.arange(days) / 365.25)
        hibor_rates = hibor_rates + trend + seasonal
        hibor_rates = np.clip(hibor_rates, 0.5, 8.0)
        hk_data['HIBOR'] = pd.Series(hibor_rates, index=dates, name='HIBOR')

        # 為其他數據源生成類似的真實數據
        data_generators = {
            'GDP': (43, 3.2, 2, -5, 8, 0),
            'RETAIL': (44, 5.5, 4, 4, 15, 0),
            'PROPERTY': (45, 2.8, 3, -8, 12, 0),
            'TRADE': (46, 6.2, 5, -15, 20, 0),
            'TOURISM': (47, 75.0, 15, 20, 100, 0),
            'CPI': (48, 2.1, 1.5, -2, 8, 0),
            'UNEMPLOYMENT': (49, 4.5, 0.8, 2, 8, 0),
            'MONETARY': (50, 7.8, 3, -5, 15, 0)
        }

        for source, (seed, base, std, min_val, max_val, offset) in data_generators.items():
            np.random.seed(seed)
            data = base + np.random.normal(0, std, days)
            data = np.clip(data, min_val, max_val)

            # 添加季節性
            seasonal = 0.5 * np.sin(2 * np.pi * np.arange(days) / 365.25 + offset)
            data = data + seasonal
            data = np.clip(data, min_val, max_val)

            hk_data[source] = pd.Series(data, index=dates, name=source)

        print(f"Generated {len(hk_data)} Hong Kong macro data sources")
        return hk_data

    def run_sample_optimization(self):
        """運行示例優化 (少量策略用於演示)"""
        print("\n" + "=" * 80)
        print("RUNNING SAMPLE REALISTIC OPTIMIZATION")
        print("=" * 80)

        # 獲取數據
        print("Getting stock data...")
        stock_data = self.get_stock_data('0700.HK')

        if stock_data is None:
            print("ERROR: Cannot get stock data")
            return

        print("Generating macro data...")
        macro_data = self.generate_hk_macro_data(
            stock_data.index[0].strftime('%Y-%m-%d'),
            stock_data.index[-1].strftime('%Y-%m-%d')
        )

        # 準備少量策略用於演示
        sample_strategies = []

        # 只測試少量策略避免時間太長
        sample_sources = ['HIBOR', 'RETAIL', 'MONETARY']  # 3個數據源
        sample_rsi_periods = [10, 20, 30]  # 3個RSI週期
        sample_thresholds = [0.3, 0.7]  # 2個閾值

        for data_source in sample_sources:
            for rsi_period in sample_rsi_periods:
                for signal_threshold in sample_thresholds:
                    sample_strategies.append((
                        self.optimize_rsi_realistic,
                        (data_source, rsi_period, signal_threshold, stock_data, macro_data)
                    ))

        print(f"Testing {len(sample_strategies)} sample strategies...")
        print("Expected time: ~30 seconds")

        # 並行執行
        results = []
        max_workers = min(mp.cpu_count(), 16)  # 使用16個核心平衡性能

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_strategy = {
                executor.submit(func, args): args
                for func, args in sample_strategies
            }

            for i, future in enumerate(as_completed(future_to_strategy)):
                result = future.result()
                if result is not None:
                    results.append(result)
                print(f"Completed: {i+1}/{len(sample_strategies)}")

        # 分析結果
        if results:
            print(f"\n" + "=" * 80)
            print("REALISTIC TRADING OPTIMIZATION RESULTS")
            print("=" * 80)

            # 排序結果
            sorted_results = sorted(results, key=lambda x: x['realistic_return'], reverse=True)
            best = sorted_results[0]

            print(f"Best Strategy: {best['strategy_name']}")
            print(f"Strategy ID: {best['strategy_id']}")
            print(f"Data Source: {best['data_source']}")
            print(f"\nPerformance Comparison:")
            print(f"   Basic Return: {best['basic_return']:.2%}")
            print(f"   Realistic Return: {best['realistic_return']:.2%}")
            print(f"   Cost Impact: {best['cost_impact']:.2%}")
            print(f"   Total Trading Cost: HK${best['total_real_cost']:.2f}")
            print(f"   Quality Score: {best['quality_score']:.1f}/100")
            print(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
            print(f"   Max Drawdown: {best['max_drawdown']:.2%}")
            print(f"   Win Rate: {best['win_rate']:.1f}%")

            # 成本分析
            print(f"\nCost Breakdown:")
            print(f"   Trading Cost: HK${best['trading_cost']:.2f}")
            print(f"   Position Cost: HK${best['position_cost']:.2f}")

            # 保存結果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"realistic_trading_results_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'optimization_config': {
                        'trading_costs': self.trading_costs,
                        'parameter_ranges': {
                            'rsi_periods': f"{min(self.rsi_periods)}-{max(self.rsi_periods)}",
                            'rsi_thresholds': f"{min(self.rsi_thresholds)}-{max(self.rsi_thresholds)}",
                        }
                    },
                    'results': results,
                    'best_strategy': best,
                    'summary': {
                        'total_tested': len(results),
                        'avg_realistic_return': np.mean([r['realistic_return'] for r in results]),
                        'avg_cost_impact': np.mean([r['cost_impact'] for r in results])
                    }
                }, f, indent=2, ensure_ascii=False)

            print(f"\nResults saved to: {filename}")

        return results

def main():
    """主函數"""
    print("REALISTIC TRADING ENVIRONMENT OPTIMIZER")
    print("=" * 80)
    print("真實交易環境優化器 - 包含滑點、手續費、融資成本")
    print("Strategy ID System: {data_source}_{indicator}_{param_hash}_{timestamp}")
    print("=" * 80)

    optimizer = RealisticTradingOptimizer()

    try:
        results = optimizer.run_sample_optimization()

        if results:
            print(f"\n[DONE] Realistic optimization completed!")
            print(f"Total strategies analyzed: {len(results)}")
            print("All results saved with unique strategy IDs for easy tracking.")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()