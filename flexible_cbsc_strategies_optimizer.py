#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flexible CBSC Strategies Parameter Optimizer
Optimize all 4 CBSC strategies with relaxed parameters to ensure trading activity
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

class FlexibleCBSCStrategiesOptimizer:
    def __init__(self):
        self.results = {}
        self.optimization_data = None
        self.risk_free_rate = 0.02  # 2% annual risk-free rate

    def load_data(self):
        """Load and prepare data"""
        print("Loading optimization data...")

        try:
            # Load price data
            data = pd.read_csv('acheng_sharpe_results.csv')

            # Process data
            if 'HSIF_close' in data.columns:
                data = data.rename(columns={'HSIF_close': 'Close'})

            data['Date'] = pd.to_datetime(data['Date'])
            data = data.sort_values('Date').reset_index(drop=True)

            # Generate additional CBSC-like data for testing
            np.random.seed(42)
            n_days = len(data)

            # Add synthetic indicators
            data['Volume'] = np.random.uniform(100000000, 800000000, n_days)
            data['Bull_Ratio'] = np.random.uniform(0.2, 0.8, n_days)
            data['Bear_Turnover_HKD'] = np.random.uniform(100000000, 800000000, n_days)

            print(f"Data loaded: {len(data)} records")
            print(f"Period: {data['Date'].min().strftime('%Y-%m-%d')} to {data['Date'].max().strftime('%Y-%m-%d')}")

            self.optimization_data = data
            return True

        except Exception as e:
            print(f"Data loading failed: {e}")
            return False

    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        data = data.copy()

        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Moving averages
        data['MA_Short'] = data['Close'].rolling(window=5).mean()
        data['MA_Long'] = data['Close'].rolling(window=20).mean()
        data['Volume_MA'] = data['Volume'].rolling(window=10).mean()

        # Bollinger Bands
        data['BB_Middle'] = data['Close'].rolling(window=20).mean()
        bb_std = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_Middle'] + (bb_std * 2)
        data['BB_Lower'] = data['BB_Middle'] - (bb_std * 2)

        return data

    def test_rsi_strategy(self, data, buy_threshold, sell_threshold):
        """Test RSI strategy"""
        data = self.calculate_indicators(data.copy())

        # Generate signals
        data['Signal'] = 'HOLD'
        data.loc[data['RSI'] < buy_threshold, 'Signal'] = 'BUY'
        data.loc[data['RSI'] > sell_threshold, 'Signal'] = 'SELL'

        return self.calculate_performance(data, 'RSI', {
            'buy_threshold': buy_threshold,
            'sell_threshold': sell_threshold
        })

    def test_sentiment_momentum(self, data, short_window, long_window, momentum_th, pos_size):
        """Test sentiment momentum strategy"""
        data = self.calculate_indicators(data.copy())

        # Calculate sentiment indicators
        data['Bull_Ratio_MA_Short'] = data['Bull_Ratio'].rolling(window=short_window).mean()
        data['Bull_Ratio_MA_Long'] = data['Bull_Ratio'].rolling(window=long_window).mean()
        data['Bull_Momentum'] = (data['Bull_Ratio_MA_Short'] - data['Bull_Ratio_MA_Long']) / data['Bull_Ratio_MA_Long']

        # Generate signals
        data['Signal'] = 'HOLD'
        buy_condition = (
            (data['Bull_Momentum'] > momentum_th) &
            (data['RSI'] < 75) &
            (data['Volume'] > data['Volume_MA'])
        )
        sell_condition = (
            (data['Bull_Momentum'] < -momentum_th) |
            (data['RSI'] > 80)
        )

        data.loc[buy_condition, 'Signal'] = 'BUY'
        data.loc[sell_condition, 'Signal'] = 'SELL'

        return self.calculate_performance(data, 'Sentiment_Momentum', {
            'short_window': short_window,
            'long_window': long_window,
            'momentum_threshold': momentum_th,
            'position_size': pos_size
        })

    def test_volume_reversal(self, data, ratio_window, volume_mult, extreme_th, pos_size):
        """Test volume reversal strategy"""
        data = self.calculate_indicators(data.copy())

        # Calculate reversal indicators
        data['Bull_Ratio_MA'] = data['Bull_Ratio'].rolling(window=ratio_window).mean()
        data['Volume_Spike'] = data['Volume'] / data['Volume_MA']

        # Generate reversal signals
        data['Signal'] = 'HOLD'

        # Buy on extreme bearish with volume spike
        buy_condition = (
            (data['Bull_Ratio'] < extreme_th) &
            (data['Volume_Spike'] > volume_mult) &
            (data['RSI'] < 40)
        )

        # Sell on reversal or extreme bullish
        sell_condition = (
            (data['Bull_Ratio'] > (1 - extreme_th)) |
            (data['RSI'] > 70)
        )

        data.loc[buy_condition, 'Signal'] = 'BUY'
        data.loc[sell_condition, 'Signal'] = 'SELL'

        return self.calculate_performance(data, 'Volume_Reversal', {
            'ratio_window': ratio_window,
            'volume_multiplier': volume_mult,
            'extreme_threshold': extreme_th,
            'position_size': pos_size
        })

    def test_risk_adjusted_bollinger(self, data, rsi_ob, rsi_os, bb_mult, risk_th, pos_size):
        """Test risk adjusted Bollinger strategy"""
        data = self.calculate_indicators(data.copy())

        # Generate signals
        data['Signal'] = 'HOLD'

        # Buy conditions with risk adjustment
        buy_condition = (
            ((data['RSI'] < rsi_os) | (data['Close'] < data['BB_Lower'])) &
            (data['Bull_Ratio'] > risk_th)
        )

        # Sell conditions
        sell_condition = (
            ((data['RSI'] > rsi_ob) | (data['Close'] > data['BB_Upper'])) |
            (data['RSI'] > 85)
        )

        data.loc[buy_condition, 'Signal'] = 'BUY'
        data.loc[sell_condition, 'Signal'] = 'SELL'

        return self.calculate_performance(data, 'Risk_Adjusted_Bollinger', {
            'rsi_overbought': rsi_ob,
            'rsi_oversold': rsi_os,
            'bb_multiplier': bb_mult,
            'risk_threshold': risk_th,
            'position_size': pos_size
        })

    def test_time_decay_momentum(self, data, decay_period, momentum_th, bull_th, pos_size):
        """Test time decay momentum strategy"""
        data = self.calculate_indicators(data.copy())

        # Calculate momentum with decay
        data['Price_Momentum'] = data['Close'].pct_change()
        data['Decay_Momentum'] = data['Price_Momentum'].rolling(window=decay_period).mean()

        # Generate signals
        data['Signal'] = 'HOLD'

        buy_condition = (
            (data['Decay_Momentum'] > momentum_th) &
            (data['Bull_Ratio'] > bull_th) &
            (data['RSI'] < 75)
        )

        sell_condition = (
            (data['Decay_Momentum'] < -momentum_th) |
            (data['RSI'] > 80)
        )

        data.loc[buy_condition, 'Signal'] = 'BUY'
        data.loc[sell_condition, 'Signal'] = 'SELL'

        return self.calculate_performance(data, 'Time_Decay_Momentum', {
            'decay_period': decay_period,
            'momentum_threshold': momentum_th,
            'bull_threshold': bull_th,
            'position_size': pos_size
        })

    def calculate_performance(self, data, strategy_name, params):
        """Calculate strategy performance"""

        # Extract position size
        pos_size = params.get('position_size', 0.3)

        # Backtest simulation
        cash = 100000
        position = 0
        portfolio_values = [cash]
        trades = []

        for i in range(len(data)):
            if i == 0:
                continue

            current_price = data.loc[i, 'Close']
            signal = data.loc[i, 'Signal']

            if signal == 'BUY' and position == 0 and cash > current_price:
                # Buy
                shares = int(cash * pos_size / current_price)
                if shares > 0:
                    cash -= shares * current_price
                    position = shares
                    trades.append({
                        'type': 'BUY',
                        'date': data.loc[i, 'Date'],
                        'price': current_price,
                        'shares': shares
                    })

            elif signal == 'SELL' and position > 0:
                # Sell
                cash += position * current_price
                trades.append({
                    'type': 'SELL',
                    'date': data.loc[i, 'Date'],
                    'price': current_price,
                    'shares': position
                })
                position = 0

            # Calculate portfolio value
            portfolio_value = cash + (position * current_price if position > 0 else 0)
            portfolio_values.append(portfolio_value)

        # Calculate metrics
        if len(portfolio_values) > 1:
            portfolio_series = pd.Series(portfolio_values)
            returns = portfolio_series.pct_change().dropna()

            total_return = (portfolio_values[-1] / portfolio_values[0] - 1)
            trading_days = len(data)
            annual_return = total_return * (252 / trading_days) if trading_days > 0 else 0
            volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.15

            sharpe_ratio = (annual_return - self.risk_free_rate) / volatility if volatility > 0 else 0

            # Maximum drawdown
            rolling_max = portfolio_series.expanding().max()
            drawdown = (portfolio_series - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            calmar_ratio = abs(annual_return / max_drawdown) if max_drawdown != 0 else annual_return / 0.001

            # Trading statistics
            buy_trades = len([t for t in trades if t['type'] == 'BUY'])
            sell_trades = len([t for t in trades if t['type'] == 'SELL'])
            total_trades = min(buy_trades, sell_trades)

            # Win rate
            profitable_trades = 0
            for i, trade in enumerate(trades):
                if trade['type'] == 'SELL' and i > 0 and trades[i-1]['type'] == 'BUY':
                    if trade['price'] > trades[i-1]['price']:
                        profitable_trades += 1

            win_rate = profitable_trades / total_trades if total_trades > 0 else 0

        else:
            total_return = 0
            annual_return = 0
            sharpe_ratio = 0
            max_drawdown = 0
            calmar_ratio = 0
            win_rate = 0
            total_trades = 0
            volatility = 0.15

        return {
            'strategy': strategy_name,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'volatility': volatility,
            'final_value': portfolio_values[-1] if portfolio_values else 100000,
            'parameters': params
        }

    def optimize_all_strategies(self):
        """Optimize all strategies with comprehensive parameter ranges"""

        print("Starting comprehensive CBSC strategies optimization...")
        print("=" * 80)

        # Load data
        if not self.load_data():
            return None

        all_results = {}

        # 1. RSI Strategy (as reference)
        print("\n1. Optimizing RSI Strategy...")
        rsi_results = []
        rsi_buy_values = list(range(5, 51, 5))  # 5, 10, 15, ..., 50
        rsi_sell_values = list(range(55, 91, 5))  # 55, 60, 65, ..., 90

        for buy in rsi_buy_values:
            for sell in rsi_sell_values:
                if buy < sell:
                    result = self.test_rsi_strategy(self.optimization_data.copy(), buy, sell)
                    rsi_results.append(result)

        all_results['RSI'] = rsi_results
        trading_rsi = [r for r in rsi_results if r['total_trades'] > 0]
        print(f"RSI: {len(rsi_results)} combinations tested, {len(trading_rsi)} with trades")

        # 2. Sentiment Momentum Strategy
        print("\n2. Optimizing Sentiment Momentum Strategy...")
        sentiment_results = []
        short_windows = [3, 5, 10, 15]
        long_windows = [10, 15, 20, 25]
        momentum_thresholds = [0.01, 0.02, 0.05, 0.1]
        position_sizes = [0.2, 0.3, 0.4]

        for short_w in short_windows:
            for long_w in long_windows:
                if short_w < long_w:
                    for mom_th in momentum_thresholds:
                        for pos_size in position_sizes:
                            result = self.test_sentiment_momentum(
                                self.optimization_data.copy(), short_w, long_w, mom_th, pos_size
                            )
                            sentiment_results.append(result)

        all_results['Sentiment_Momentum'] = sentiment_results
        trading_sentiment = [r for r in sentiment_results if r['total_trades'] > 0]
        print(f"Sentiment Momentum: {len(sentiment_results)} combinations tested, {len(trading_sentiment)} with trades")

        # 3. Volume Reversal Strategy
        print("\n3. Optimizing Volume Reversal Strategy...")
        volume_results = []
        ratio_windows = [3, 5, 10, 15]
        volume_multipliers = [1.1, 1.2, 1.5, 2.0]
        extreme_thresholds = [0.3, 0.35, 0.4, 0.45]
        position_sizes = [0.2, 0.3, 0.4]

        for ratio_w in ratio_windows:
            for vol_mult in volume_multipliers:
                for extreme_th in extreme_thresholds:
                    for pos_size in position_sizes:
                        result = self.test_volume_reversal(
                            self.optimization_data.copy(), ratio_w, vol_mult, extreme_th, pos_size
                        )
                        volume_results.append(result)

        all_results['Volume_Reversal'] = volume_results
        trading_volume = [r for r in volume_results if r['total_trades'] > 0]
        print(f"Volume Reversal: {len(volume_results)} combinations tested, {len(trading_volume)} with trades")

        # 4. Risk Adjusted Bollinger Strategy
        print("\n4. Optimizing Risk Adjusted Bollinger Strategy...")
        bollinger_results = []
        rsi_overbought = [65, 70, 75, 80]
        rsi_oversold = [20, 25, 30, 35]
        bb_multipliers = [1.5, 2.0, 2.5]
        risk_thresholds = [0.3, 0.4, 0.5]
        position_sizes = [0.2, 0.3, 0.4]

        for rsi_ob in rsi_overbought:
            for rsi_os in rsi_oversold:
                if rsi_ob > rsi_os:
                    for bb_mult in bb_multipliers:
                        for risk_th in risk_thresholds:
                            for pos_size in position_sizes:
                                result = self.test_risk_adjusted_bollinger(
                                    self.optimization_data.copy(), rsi_ob, rsi_os, bb_mult, risk_th, pos_size
                                )
                                bollinger_results.append(result)

        all_results['Risk_Adjusted_Bollinger'] = bollinger_results
        trading_bollinger = [r for r in bollinger_results if r['total_trades'] > 0]
        print(f"Risk Adjusted Bollinger: {len(bollinger_results)} combinations tested, {len(trading_bollinger)} with trades")

        # 5. Time Decay Momentum Strategy
        print("\n5. Optimizing Time Decay Momentum Strategy...")
        time_decay_results = []
        decay_periods = [5, 10, 15, 20]
        momentum_thresholds = [0.01, 0.02, 0.05]
        bull_thresholds = [0.4, 0.5, 0.6]
        position_sizes = [0.2, 0.3, 0.4]

        for decay_p in decay_periods:
            for mom_th in momentum_thresholds:
                for bull_th in bull_thresholds:
                    for pos_size in position_sizes:
                        result = self.test_time_decay_momentum(
                            self.optimization_data.copy(), decay_p, mom_th, bull_th, pos_size
                        )
                        time_decay_results.append(result)

        all_results['Time_Decay_Momentum'] = time_decay_results
        trading_time_decay = [r for r in time_decay_results if r['total_trades'] > 0]
        print(f"Time Decay Momentum: {len(time_decay_results)} combinations tested, {len(trading_time_decay)} with trades")

        self.results = all_results
        return all_results

    def analyze_results(self):
        """Analyze and display optimization results"""

        print("\n" + "=" * 80)
        print("COMPLETE CBSC STRATEGIES OPTIMIZATION RESULTS")
        print("=" * 80)

        strategy_summary = {}

        for strategy_name, results in self.results.items():
            trading_results = [r for r in results if r['total_trades'] > 0]

            print(f"\n{strategy_name.upper()}:")
            print(f"  Total Combinations: {len(results):,}")
            print(f"  With Trades: {len(trading_results):,}")

            if trading_results:
                # Sort by Sharpe ratio
                best_sharpe = max(trading_results, key=lambda x: x['sharpe_ratio'])
                best_return = max(trading_results, key=lambda x: x['total_return'])
                best_trades = max(trading_results, key=lambda x: x['total_trades'])

                print(f"  Best Sharpe: {best_sharpe['sharpe_ratio']:.6f}")
                print(f"    Parameters: {best_sharpe['parameters']}")
                print(f"    Total Return: {best_sharpe['total_return']:.6f}")
                print(f"    Trades: {best_sharpe['total_trades']}")

                print(f"  Best Return: {best_return['total_return']:.6f}")
                print(f"    Parameters: {best_return['parameters']}")
                print(f"    Sharpe: {best_return['sharpe_ratio']:.6f}")

                print(f"  Most Trades: {best_trades['total_trades']}")
                print(f"    Parameters: {best_trades['parameters']}")
                print(f"    Return: {best_trades['total_return']:.6f}")

                # Top 5 results
                top_5 = sorted(trading_results, key=lambda x: x['sharpe_ratio'], reverse=True)[:5]
                print(f"\n  Top 5 by Sharpe:")
                for i, result in enumerate(top_5, 1):
                    print(f"    {i}. Sharpe: {result['sharpe_ratio']:.6f} | Return: {result['total_return']:.6f} | Trades: {result['total_trades']:2d} | Win%: {result['win_rate']:.3f}")

                strategy_summary[strategy_name] = {
                    'total_combinations': len(results),
                    'with_trades': len(trading_results),
                    'best_sharpe': best_sharpe,
                    'best_return': best_return,
                    'most_trades': best_trades,
                    'top_5': top_5
                }
            else:
                print(f"  No trading combinations found")
                strategy_summary[strategy_name] = {
                    'total_combinations': len(results),
                    'with_trades': 0,
                    'best_sharpe': None,
                    'best_return': None,
                    'most_trades': None,
                    'top_5': []
                }

        # Overall comparison
        print(f"\n" + "=" * 80)
        print("OVERALL STRATEGY COMPARISON")
        print("=" * 80)

        all_best = []
        for strategy_name, summary in strategy_summary.items():
            if summary['best_sharpe']:
                best = summary['best_sharpe'].copy()
                best['strategy'] = strategy_name
                all_best.append(best)

        if all_best:
            all_best_sorted = sorted(all_best, key=lambda x: x['sharpe_ratio'], reverse=True)

            print(f"\nAll Strategies Ranked by Sharpe Ratio:")
            print(f"{'Rank':<4} {'Strategy':<25} {'Sharpe':<10} {'Return':<10} {'Trades':<8} {'Win%':<8}")
            print("-" * 75)

            for i, config in enumerate(all_best_sorted, 1):
                print(f"{i:<4} {config['strategy']:<25} {config['sharpe_ratio']:<10.6f} "
                      f"{config['total_return']:<10.6f} {config['total_trades']:<8} {config['win_rate']:<8.3f}")

        return strategy_summary

    def save_results(self):
        """Save comprehensive results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        results_file = f"flexible_cbsc_strategies_results_{timestamp}.json"

        try:
            # Prepare data for JSON
            json_results = {}
            for strategy_name, results in self.results.items():
                trading_results = [r for r in results if r['total_trades'] > 0]

                json_results[strategy_name] = {
                    'metadata': {
                        'total_combinations_tested': len(results),
                        'combinations_with_trades': len(trading_results)
                    },
                    'best_sharpe': max(trading_results, key=lambda x: x['sharpe_ratio']) if trading_results else None,
                    'best_return': max(trading_results, key=lambda x: x['total_return']) if trading_results else None,
                    'most_trades': max(trading_results, key=lambda x: x['total_trades']) if trading_results else None,
                    'top_10': sorted(trading_results, key=lambda x: x['sharpe_ratio'], reverse=True)[:10] if trading_results else []
                }

            complete_data = {
                'optimization_metadata': {
                    'timestamp': timestamp,
                    'data_period': f"{self.optimization_data['Date'].min().strftime('%Y-%m-%d')} to {self.optimization_data['Date'].max().strftime('%Y-%m-%d')}",
                    'total_trading_days': len(self.optimization_data),
                    'strategies_tested': len(self.results)
                },
                'results': json_results
            }

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(complete_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\nComplete results saved to: {results_file}")

            # Save text report
            report_file = f"flexible_cbsc_strategies_report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("Flexible CBSC Strategies Parameter Optimization Report\n")
                f.write(f"Generated: {timestamp}\n")
                f.write("=" * 60 + "\n\n")

                f.write("Optimization Summary:\n")
                f.write(f"  Data Period: {complete_data['optimization_metadata']['data_period']}\n")
                f.write(f"  Trading Days: {complete_data['optimization_metadata']['total_trading_days']}\n")
                f.write(f"  Strategies Tested: {complete_data['optimization_metadata']['strategies_tested']}\n\n")

                for strategy_name, strategy_data in json_results.items():
                    f.write(f"{strategy_name.replace('_', ' ').upper()}:\n")
                    f.write(f"  Combinations Tested: {strategy_data['metadata']['total_combinations_tested']:,}\n")
                    f.write(f"  With Trades: {strategy_data['metadata']['combinations_with_trades']:,}\n")

                    if strategy_data['best_sharpe']:
                        best = strategy_data['best_sharpe']
                        f.write(f"  Best Sharpe: {best['sharpe_ratio']:.6f}\n")
                        f.write(f"  Best Parameters: {best['parameters']}\n")

                    f.write("\n")

            print(f"Summary report saved to: {report_file}")

        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    """Main execution function"""
    print("Flexible CBSC Strategies Parameter Optimizer")
    print("Optimizing 5 strategies with comprehensive parameter testing")
    print("=" * 80)

    optimizer = FlexibleCBSCStrategiesOptimizer()

    try:
        # Run optimization
        results = optimizer.optimize_all_strategies()

        if results:
            # Analyze results
            summary = optimizer.analyze_results()

            # Save results
            optimizer.save_results()

            print(f"\n" + "=" * 80)
            print("OPTIMIZATION COMPLETE!")
            print("=" * 80)
            print("All CBSC strategies have been optimized with comprehensive parameter testing.")
            print("Results and reports have been generated successfully.")
        else:
            print("Optimization failed")

    except Exception as e:
        print(f"Execution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()