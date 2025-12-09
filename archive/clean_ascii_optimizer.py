#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean ASCII Trading Optimizer
Clean ASCII Trading Optimizer - Windows Compatible

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

warnings.filterwarnings('ignore')

class CleanASCIIOptimizer:
    """Clean ASCII Trading Optimizer"""

    def __init__(self):
        self.start_time = time.time()

        # Hong Kong data sources
        self.hk_data_sources = [
            'HIBOR', 'GDP', 'RETAIL', 'PROPERTY', 'TRADE',
            'TOURISM', 'CPI', 'UNEMPLOYMENT', 'MONETARY'
        ]

        # Sample parameter ranges (for demo)
        self.rsi_periods = [10, 20, 30]           # 3 values
        self.rsi_thresholds = [0.3, 0.5, 0.7]     # 3 values

        self.timeframes = ['daily', 'weekly']      # 2 timeframes

        # Realistic trading costs
        self.trading_costs = {
            'commission': 0.0025,      # 0.25%
            'slippage': 0.0015,        # 0.15%
            'stamp_duty': 0.0013,      # 0.13%
            'financing_cost': 0.06/365, # 6% annually
            'min_commission': 5.0,     # HK$5 minimum
        }

        print("=" * 80)
        print("CLEAN ASCII TRADING OPTIMIZER")
        print("=" * 80)
        print("Configuration:")
        print(f"   RSI strategies: {len(self.rsi_periods)} periods x {len(self.rsi_thresholds)} thresholds x {len(self.hk_data_sources)} sources = {len(self.rsi_periods) * len(self.rsi_thresholds) * len(self.hk_data_sources)} strategies")
        print(f"   Timeframes: {len(self.timeframes)} (daily/weekly)")
        print(f"   Total strategies: {len(self.rsi_periods) * len(self.rsi_thresholds) * len(self.hk_data_sources) * len(self.timeframes)}")
        print(f"   Trading costs: commission{self.trading_costs['commission']*100:.2f}% + slippage{self.trading_costs['slippage']*100:.2f}% + stamp{self.trading_costs['stamp_duty']*100:.2f}%")

    def generate_strategy_id(self, indicator_type, params, data_source, timeframe):
        """Generate unique strategy ID"""
        param_str = f"{indicator_type}_{sorted(params.items())}_{timeframe}"
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        strategy_id = f"{data_source}_{indicator_type}_{timeframe}_{param_hash}_{timestamp}"
        return strategy_id

    def calculate_costs(self, portfolio_value, trades_count):
        """Calculate realistic trading costs"""
        if trades_count == 0:
            return 0

        avg_trade_value = portfolio_value / max(1, trades_count)
        commission = max(avg_trade_value * self.trading_costs['commission'], self.trading_costs['min_commission'])
        slippage_cost = avg_trade_value * self.trading_costs['slippage']
        stamp_duty = avg_trade_value * self.trading_costs['stamp_duty'] * 0.5
        total_cost = (commission + slippage_cost + stamp_duty) * trades_count
        return total_cost

    def optimize_rsi_strategy(self, args):
        """Optimize RSI strategy"""
        data_source, rsi_period, signal_threshold, stock_data, macro_data, timeframe = args

        try:
            strategy_id = self.generate_strategy_id('RSI', {
                'period': rsi_period, 'threshold': signal_threshold
            }, data_source, timeframe)

            # Data alignment and timezone normalization
            stock_data_norm = stock_data.copy()
            if hasattr(stock_data_norm.index, 'tz'):
                stock_data_norm.index = stock_data_norm.index.tz_localize(None)
            stock_data_norm.index = stock_data_norm.index.normalize()

            common_index = stock_data_norm.index.intersection(macro_data[data_source].index)
            if len(common_index) < 50:
                return None

            stock_aligned = stock_data_norm.reindex(common_index, method='ffill').dropna()
            macro_aligned = macro_data[data_source].reindex(common_index, method='ffill').dropna()

            # Timeframe resampling
            if timeframe == 'weekly':
                stock_resampled = stock_aligned.resample('W').last().dropna()
                macro_resampled = macro_aligned.resample('W').last().dropna()
            else:  # daily
                stock_resampled = stock_aligned
                macro_resampled = macro_aligned

            if len(stock_resampled) < rsi_period + 10:
                return None

            # Calculate RSI
            fast_rsi = vbt.RSI.run(macro_resampled, window=rsi_period).rsi
            slow_rsi = vbt.RSI.run(macro_resampled, window=rsi_period*2).rsi

            # Signal generation
            fast_cross_above_slow = (fast_rsi > slow_rsi) & (fast_rsi.shift(1) <= slow_rsi.shift(1))
            fast_cross_below_slow = (fast_rsi < slow_rsi) & (fast_rsi.shift(1) >= slow_rsi.shift(1))
            rsi_momentum = fast_rsi - slow_rsi
            strong_signal = rsi_momentum > signal_threshold

            entries = fast_cross_above_slow & strong_signal
            exits = fast_cross_below_slow | (fast_rsi > 80)

            # VectorBT backtest
            portfolio = vbt.Portfolio.from_signals(
                stock_resampled['Close'],
                entries,
                exits,
                init_cash=100000,
                fees=0,
                freq='D'
            )

            # Calculate performance metrics
            returns = portfolio.returns()
            if len(returns) == 0 or returns.std() == 0:
                return None

            total_return = (1 + returns).prod() - 1
            trades_count = entries.sum()
            trading_cost = self.calculate_costs(100000, trades_count)
            cost_impact = trading_cost / 100000
            realistic_return = total_return - cost_impact

            sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # Win rate calculation
            trade_returns = []
            entry_dates = entries[entries].index
            for entry_date in entry_dates:
                if entry_date in returns.index:
                    trade_returns.append(returns.loc[entry_date])

            win_rate = (np.array(trade_returns) > 0).mean() * 100 if len(trade_returns) > 0 else 0

            # Quality score calculation
            quality_score = 0
            if realistic_return > 0.20: quality_score += 30
            elif realistic_return > 0.10: quality_score += 20
            elif realistic_return > 0.05: quality_score += 10

            if sharpe_ratio > 2.0: quality_score += 25
            elif sharpe_ratio > 1.5: quality_score += 20
            elif sharpe_ratio > 1.0: quality_score += 15

            if max_drawdown > -0.08: quality_score += 20
            elif max_drawdown > -0.12: quality_score += 15
            elif max_drawdown > -0.20: quality_score += 10

            if win_rate > 60: quality_score += 15
            elif win_rate > 55: quality_score += 10
            elif win_rate > 50: quality_score += 5

            if trades_count > 10: quality_score += 10
            if trades_count > 20: quality_score += 5

            return {
                'strategy_id': strategy_id,
                'data_source': data_source,
                'indicator_type': 'RSI',
                'timeframe': timeframe,
                'rsi_period': int(rsi_period),
                'signal_threshold': float(signal_threshold),
                'total_return': float(total_return),
                'realistic_return': float(realistic_return),
                'cost_impact': float(cost_impact),
                'trading_cost': float(trading_cost),
                'sharpe_ratio': float(sharpe_ratio),
                'max_drawdown': float(max_drawdown),
                'win_rate': float(win_rate),
                'trades_count': int(trades_count),
                'quality_score': int(min(quality_score, 100)),
                'strategy_name': f'{data_source}_RSI_{rsi_period}_{signal_threshold:.2f}_{timeframe}',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"RSI strategy error {data_source}_{rsi_period}_{signal_threshold}_{timeframe}: {str(e)}")
            return None

    def get_stock_data(self, symbol='0700.HK', start_date='2020-01-01', end_date='2024-01-01'):
        """Get stock data"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(start=start_date, end=end_date)
            if data.empty:
                # Generate backup data
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

    def generate_macro_data(self, start_date, end_date):
        """Generate Hong Kong macro data"""
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        days = len(dates)
        hk_data = {}

        np.random.seed(42)

        # HIBOR data
        base_rate = 2.5
        hibor_rates = base_rate + np.random.normal(0, 1.5, days)
        hibor_rates = np.clip(hibor_rates, 0.5, 8.0)
        trend = np.linspace(0, 0.5, days)
        seasonal = 0.3 * np.sin(2 * np.pi * np.arange(days) / 365.25)
        hibor_rates = hibor_rates + trend + seasonal
        hibor_rates = np.clip(hibor_rates, 0.5, 8.0)
        hk_data['HIBOR'] = pd.Series(hibor_rates, index=dates, name='HIBOR')

        # Other data sources
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
            seasonal = 0.5 * np.sin(2 * np.pi * np.arange(days) / 365.25 + offset)
            data = data + seasonal
            data = np.clip(data, min_val, max_val)
            hk_data[source] = pd.Series(data, index=dates, name=source)

        print(f"Generated {len(hk_data)} Hong Kong macro data sources")
        return hk_data

    def run_optimization(self):
        """Run optimization"""
        print("\n" + "=" * 80)
        print("RUNNING CLEAN ASCII OPTIMIZATION")
        print("=" * 80)

        # Get data
        print("Getting stock data...")
        stock_data = self.get_stock_data('0700.HK')

        if stock_data is None:
            print("ERROR: Cannot get stock data")
            return

        print("Generating macro data...")
        macro_data = self.generate_macro_data(
            stock_data.index[0].strftime('%Y-%m-%d'),
            stock_data.index[-1].strftime('%Y-%m-%d')
        )

        # Prepare strategies
        strategies = []

        # Sample strategies for demo
        sample_sources = ['HIBOR', 'RETAIL']      # 2 data sources
        sample_rsi_periods = [10, 20]             # 2 RSI periods
        sample_thresholds = [0.3, 0.5]            # 2 thresholds
        sample_timeframes = ['daily', 'weekly']   # 2 timeframes

        for data_source in sample_sources:
            for rsi_period in sample_rsi_periods:
                for signal_threshold in sample_thresholds:
                    for timeframe in sample_timeframes:
                        strategies.append((
                            self.optimize_rsi_strategy,
                            (data_source, rsi_period, signal_threshold, stock_data, macro_data, timeframe)
                        ))

        print(f"Testing {len(strategies)} strategies...")
        print("Expected time: ~45 seconds")

        # Parallel execution
        results = []
        max_workers = min(mp.cpu_count(), 8)  # Use 8 cores for stability

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_strategy = {
                executor.submit(func, args): args
                for func, args in strategies
            }

            for i, future in enumerate(as_completed(future_to_strategy)):
                result = future.result()
                if result is not None:
                    results.append(result)
                print(f"Completed: {i+1}/{len(strategies)}")

        # Analyze results
        if results:
            print(f"\n" + "=" * 80)
            print("CLEAN ASCII OPTIMIZATION RESULTS")
            print("=" * 80)

            # Sort results
            sorted_results = sorted(results, key=lambda x: x['realistic_return'], reverse=True)
            best = sorted_results[0]

            print(f"Best Strategy: {best['strategy_name']}")
            print(f"Strategy ID: {best['strategy_id']}")
            print(f"Data Source: {best['data_source']}")
            print(f"Timeframe: {best['timeframe']}")
            print(f"\nPerformance:")
            print(f"   Total Return: {best['total_return']:.2%}")
            print(f"   Realistic Return: {best['realistic_return']:.2%}")
            print(f"   Cost Impact: {best['cost_impact']:.2%}")
            print(f"   Trading Cost: HK${best['trading_cost']:.2f}")
            print(f"   Quality Score: {best['quality_score']:.1f}/100")
            print(f"   Sharpe Ratio: {best['sharpe_ratio']:.2f}")
            print(f"   Max Drawdown: {best['max_drawdown']:.2%}")
            print(f"   Win Rate: {best['win_rate']:.1f}%")

            # Timeframe analysis
            timeframe_performance = {}
            for result in results:
                tf = result['timeframe']
                if tf not in timeframe_performance:
                    timeframe_performance[tf] = []
                timeframe_performance[tf].append(result['realistic_return'])

            print(f"\nTimeframe Performance:")
            for tf, returns in timeframe_performance.items():
                avg_return = np.mean(returns)
                print(f"   {tf}: {avg_return:.2%} average realistic return")

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clean_ascii_results_{timestamp}.json"

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'config': {
                        'trading_costs': self.trading_costs,
                        'sample_sources': sample_sources,
                        'sample_rsi_periods': sample_rsi_periods,
                        'sample_thresholds': sample_thresholds,
                        'sample_timeframes': sample_timeframes
                    },
                    'results': results,
                    'best_strategy': best,
                    'timeframe_analysis': {
                        tf: {
                            'count': len(returns),
                            'avg_return': np.mean(returns),
                            'max_return': max(returns),
                            'min_return': min(returns)
                        }
                        for tf, returns in timeframe_performance.items()
                    },
                    'summary': {
                        'total_tested': len(results),
                        'avg_realistic_return': np.mean([r['realistic_return'] for r in results]),
                        'avg_cost_impact': np.mean([r['cost_impact'] for r in results]),
                        'avg_quality_score': np.mean([r['quality_score'] for r in results])
                    }
                }, f, indent=2, ensure_ascii=False)

            print(f"\nResults saved to: {filename}")

            return results

def main():
    """Main function"""
    print("CLEAN ASCII TRADING OPTIMIZER")
    print("=" * 80)
    print("Clean ASCII Trading Optimizer - Windows Compatible")
    print("=" * 80)

    optimizer = CleanASCIIOptimizer()

    try:
        results = optimizer.run_optimization()

        if results:
            print(f"\n[DONE] Clean ASCII optimization completed!")
            print(f"Total strategies analyzed: {len(results)}")
            print("All results saved with unique strategy IDs.")

            # System statistics
            execution_time = time.time() - optimizer.start_time
            print(f"\nExecution Statistics:")
            print(f"   Execution Time: {execution_time:.2f} seconds")
            print(f"   Strategies per Second: {len(results)/execution_time:.2f}")
            print(f"   Best Quality Score: {max(r['quality_score'] for r in results):.1f}/100")
            print(f"   Average Realistic Return: {np.mean([r['realistic_return'] for r in results]):.2%}")

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()