#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete RSI Parameter Optimizer
Buy < x, Sell > y, Range 0-300, Step 5, Testing all combinations
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import itertools
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class CompleteRSIOptimizer:
    def __init__(self):
        self.rsi_period = 14  # Standard RSI period
        self.results = {}
        self.best_results = {}
        self.optimization_data = None

    def generate_rsi_parameters(self) -> List[Tuple[int, int]]:
        """Generate all RSI parameter combinations"""
        buy_values = list(range(5, 301, 5))  # Buy: 5, 10, 15, ..., 300
        sell_values = list(range(5, 301, 5))  # Sell: 5, 10, 15, ..., 300

        print(f"Generating RSI parameter combinations...")
        print(f"Buy parameter range: {len(buy_values)} values (5 to 300, step 5)")
        print(f"Sell parameter range: {len(sell_values)} values (5 to 300, step 5)")
        print(f"Total combinations: {len(buy_values) * len(sell_values)}")

        # Generate all valid combinations (Buy must be less than Sell)
        valid_combinations = []
        for buy in buy_values:
            for sell in sell_values:
                if buy < sell:  # Ensure Buy < Sell
                    valid_combinations.append((buy, sell))

        print(f"Valid combinations: {len(valid_combinations)}")
        return valid_combinations

    def load_cbsc_data(self):
        """Load CBSC data"""
        print("Loading CBSC data...")

        try:
            # Try to load real CBSC data
            data_files = [
                'warrant_sentiment_merged.csv',
                'acheng_sharpe_results.csv',
                'strategy_performance_demo.csv'
            ]

            data = None
            for file in data_files:
                try:
                    data = pd.read_csv(file)
                    if 'Date' in data.columns or 'date' in data.columns:
                        print(f"Successfully loaded data file: {file}")
                        break
                except:
                    continue

            # Process the loaded data to ensure consistent column names
            if 'HSIF_close' in data.columns:
                data = data.rename(columns={'HSIF_close': 'Close'})
                print("Renamed HSIF_close to Close")
            elif 'close' in data.columns:
                data = data.rename(columns={'close': 'Close'})
                print("Renamed close to Close")

            if data is None or 'Close' not in data.columns:
                # Generate simulated data for testing
                print("No valid data found, generating simulated CBSC data for testing...")
                dates = pd.date_range(start='2025-09-01', end='2025-10-17', freq='D')
                dates = dates[dates.weekday < 5]  # Keep only weekdays

                np.random.seed(42)  # Ensure reproducible results
                n_days = len(dates)

                data = pd.DataFrame({
                    'Date': dates,
                    'Close': 100 + np.cumsum(np.random.normal(0, 0.02, n_days)),
                    'Volume': np.random.uniform(100000000, 500000000, n_days),
                    'Bull_Ratio': np.random.uniform(0.3, 0.7, n_days),
                    'Bear_Turnover_HKD': np.random.uniform(50000000, 300000000, n_days),
                    'Signal': np.random.choice(['BUY', 'SELL', 'HOLD'], n_days)
                })

                # Ensure Bull_Ratio is in reasonable range
                data['Bull_Ratio'] = np.clip(data['Bull_Ratio'], 0.2, 0.8)

            # Ensure Date column format is correct
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
            elif 'date' in data.columns:
                data['Date'] = pd.to_datetime(data['date'])
                data = data.drop('date', axis=1)

            # Sort by date
            data = data.sort_values('Date').reset_index(drop=True)

            print(f"Data loaded successfully: {len(data)} records")
            print(f"Data period: {data['Date'].min().strftime('%Y-%m-%d')} to {data['Date'].max().strftime('%Y-%m-%d')}")

            self.optimization_data = data
            return True

        except Exception as e:
            print(f"Data loading failed: {e}")
            return False

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def simulate_rsi_strategy(self, data: pd.DataFrame, buy_threshold: int, sell_threshold: int) -> Dict:
        """Simulate RSI strategy"""

        # Calculate RSI
        data['RSI'] = self.calculate_rsi(data['Close'], self.rsi_period)

        # Generate trading signals
        data['Signal'] = 'HOLD'
        data.loc[data['RSI'] < buy_threshold, 'Signal'] = 'BUY'
        data.loc[data['RSI'] > sell_threshold, 'Signal'] = 'SELL'

        # Calculate positions and returns
        data['Position'] = 0
        data['Returns'] = 0.0

        position = 0
        entry_price = 0
        trades = []
        portfolio_values = [100000]  # Initial capital $100,000
        current_cash = 100000

        for i in range(len(data)):
            current_price = data.loc[i, 'Close']
            signal = data.loc[i, 'Signal']

            if signal == 'BUY' and position == 0 and current_cash > current_price:
                # Buy
                position = current_cash // current_price
                current_cash = current_cash % current_price
                entry_price = current_price
                trades.append({'type': 'BUY', 'date': data.loc[i, 'Date'], 'price': current_price, 'rsi': data.loc[i, 'RSI']})

            elif signal == 'SELL' and position > 0:
                # Sell
                current_cash = position * current_price
                portfolio_value = current_cash
                portfolio_values.append(portfolio_value)
                trades.append({'type': 'SELL', 'date': data.loc[i, 'Date'], 'price': current_price, 'rsi': data.loc[i, 'RSI']})
                position = 0

            # Record current portfolio value
            if position > 0:
                portfolio_value = current_cash + position * current_price
                portfolio_values.append(portfolio_value)

        # Calculate performance metrics
        if len(portfolio_values) > 1:
            portfolio_returns = pd.Series(portfolio_values).pct_change().dropna()
            total_return = (portfolio_values[-1] / portfolio_values[0] - 1)

            # Annualized return (based on actual trading days)
            trading_days = len(data)
            annual_return = total_return * (252 / trading_days) if trading_days > 0 else 0

            # Calculate volatility
            volatility = np.std(portfolio_returns) * np.sqrt(252) if len(portfolio_returns) > 1 else 0.15

            # Calculate Sharpe ratio
            sharpe_ratio = (annual_return - 0.02) / volatility if volatility > 0 else 0

            # Calculate maximum drawdown
            portfolio_series = pd.Series(portfolio_values)
            rolling_max = portfolio_series.expanding().max()
            drawdown = (portfolio_series - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # Calculate Calmar ratio
            calmar_ratio = abs(annual_return / max_drawdown) if max_drawdown != 0 else annual_return / 0.001

            # Calculate trading statistics
            buy_trades = len([t for t in trades if t['type'] == 'BUY'])
            sell_trades = len([t for t in trades if t['type'] == 'SELL'])
            total_trades = min(buy_trades, sell_trades)

            # Calculate win rate
            profitable_trades = 0
            trade_pairs = []
            for i, trade in enumerate(trades):
                if trade['type'] == 'SELL' and i > 0 and trades[i-1]['type'] == 'BUY':
                    buy_price = trades[i-1]['price']
                    sell_price = trade['price']
                    if sell_price > buy_price:
                        profitable_trades += 1
                    trade_pairs.append({
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'profit_pct': (sell_price - buy_price) / buy_price,
                        'buy_rsi': trades[i-1]['rsi'],
                        'sell_rsi': trade['rsi']
                    })

            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            avg_profit = np.mean([t['profit_pct'] for t in trade_pairs]) if trade_pairs else 0

        else:
            total_return = 0
            annual_return = 0
            sharpe_ratio = 0
            max_drawdown = 0
            calmar_ratio = 0
            win_rate = 0
            total_trades = 0
            avg_profit = 0
            volatility = 0.15

        return {
            'buy_threshold': buy_threshold,
            'sell_threshold': sell_threshold,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'avg_profit': avg_profit,
            'volatility': volatility,
            'final_value': portfolio_values[-1] if portfolio_values else 100000,
            'trade_count': len(trades),
            'profitable_trades': profitable_trades if 'profitable_trades' in locals() else 0
        }

    def run_complete_optimization(self):
        """Run complete RSI parameter optimization"""
        print("Starting complete RSI parameter optimization...")
        print("=" * 80)

        # Load data
        if not self.load_cbsc_data():
            print("Data loading failed, cannot proceed with optimization")
            return None

        # Generate parameter combinations
        parameter_combinations = self.generate_rsi_parameters()

        print(f"\nStarting testing of {len(parameter_combinations)} RSI parameter combinations...")
        print("=" * 80)

        # Run optimization
        results = []
        best_sharpe = -float('inf')
        best_return = -float('inf')
        best_calmar = -float('inf')
        best_trades = 0

        optimal_sharpe = None
        optimal_return = None
        optimal_calmar = None
        optimal_trades = None

        total_combinations = len(parameter_combinations)

        for idx, (buy_threshold, sell_threshold) in enumerate(parameter_combinations):
            # Progress display
            if (idx + 1) % 100 == 0 or idx == 0:
                progress = (idx + 1) / total_combinations * 100
                print(f"Progress: {progress:.1f}% ({idx+1}/{total_combinations}) - Current Best Sharpe: {best_sharpe:.4f}")

            # Simulate strategy
            result = self.simulate_rsi_strategy(self.optimization_data.copy(), buy_threshold, sell_threshold)
            results.append(result)

            # Update best results
            if result['sharpe_ratio'] > best_sharpe and result['total_trades'] > 0:
                best_sharpe = result['sharpe_ratio']
                optimal_sharpe = result.copy()

            if result['total_return'] > best_return and result['total_trades'] > 0:
                best_return = result['total_return']
                optimal_return = result.copy()

            if result['calmar_ratio'] > best_calmar and result['total_trades'] > 0:
                best_calmar = result['calmar_ratio']
                optimal_calmar = result.copy()

            if result['total_trades'] > best_trades:
                best_trades = result['total_trades']
                optimal_trades = result.copy()

        # Save results
        self.results = {
            'all_results': results,
            'total_combinations_tested': len(parameter_combinations),
            'optimization_metadata': {
                'data_period': f"{self.optimization_data['Date'].min().strftime('%Y-%m-%d')} to {self.optimization_data['Date'].max().strftime('%Y-%m-%d')}",
                'trading_days': len(self.optimization_data),
                'rsi_period': self.rsi_period,
                'buy_range': '5-300 (step 5)',
                'sell_range': '5-300 (step 5)',
                'total_combinations': total_combinations,
                'valid_combinations': len(parameter_combinations)
            }
        }

        self.best_results = {
            'best_sharpe': optimal_sharpe,
            'best_return': optimal_return,
            'best_calmar': optimal_calmar,
            'most_trades': optimal_trades
        }

        print(f"\nOptimization complete!")
        print(f"Tested combinations: {len(parameter_combinations)}")
        print(f"Data period: {self.optimization_data['Date'].min().strftime('%Y-%m-%d')} to {self.optimization_data['Date'].max().strftime('%Y-%m-%d')}")

        return self.results

    def analyze_results(self):
        """Analyze optimization results"""
        print("\n" + "=" * 80)
        print("RSI Parameter Optimization Results Analysis")
        print("=" * 80)

        if not self.results:
            print("No results to analyze")
            return

        results = self.results['all_results']
        metadata = self.results['optimization_metadata']

        # Statistical analysis
        print(f"\nOptimization Statistics:")
        print(f"  Total combinations tested: {metadata['total_combinations']:,}")
        print(f"  Valid combinations: {metadata['valid_combinations']:,}")
        print(f"  Data days: {metadata['trading_days']}")
        print(f"  RSI period: {metadata['rsi_period']}")

        # Filter results with trades
        trading_results = [r for r in results if r['total_trades'] > 0]
        print(f"  Combinations with trades: {len(trading_results):,}")

        if trading_results:
            print(f"\nPerformance Statistics (combinations with trades):")
            print(f"  Average total return: {np.mean([r['total_return'] for r in trading_results]):.6f}")
            print(f"  Average Sharpe ratio: {np.mean([r['sharpe_ratio'] for r in trading_results]):.4f}")
            print(f"  Average max drawdown: {np.mean([r['max_drawdown'] for r in trading_results]):.6f}")
            print(f"  Average win rate: {np.mean([r['win_rate'] for r in trading_results]):.4f}")
            print(f"  Average trade count: {np.mean([r['total_trades'] for r in trading_results]):.1f}")

            print(f"\nBest Performing Combinations:")

            # Sort by different metrics
            best_sharpe = max(trading_results, key=lambda x: x['sharpe_ratio'])
            best_return = max(trading_results, key=lambda x: x['total_return'])
            best_calmar = max(trading_results, key=lambda x: x['calmar_ratio'])
            most_trades = max(trading_results, key=lambda x: x['total_trades'])

            print(f"\n  1. Best Sharpe Ratio:")
            print(f"     Buy < {best_sharpe['buy_threshold']}, Sell > {best_sharpe['sell_threshold']}")
            print(f"     Sharpe: {best_sharpe['sharpe_ratio']:.6f}, Return: {best_sharpe['total_return']:.6f}, Trades: {best_sharpe['total_trades']}")

            print(f"\n  2. Highest Total Return:")
            print(f"     Buy < {best_return['buy_threshold']}, Sell > {best_return['sell_threshold']}")
            print(f"     Return: {best_return['total_return']:.6f}, Sharpe: {best_return['sharpe_ratio']:.6f}, Trades: {best_return['total_trades']}")

            print(f"\n  3. Best Calmar Ratio:")
            print(f"     Buy < {best_calmar['buy_threshold']}, Sell > {best_calmar['sell_threshold']}")
            print(f"     Calmar: {best_calmar['calmar_ratio']:.6f}, Return: {best_calmar['total_return']:.6f}, MDD: {best_calmar['max_drawdown']:.6f}")

            print(f"\n  4. Most Trades:")
            print(f"     Buy < {most_trades['buy_threshold']}, Sell > {most_trades['sell_threshold']}")
            print(f"     Trade count: {most_trades['total_trades']}, Return: {most_trades['total_return']:.6f}, Win rate: {most_trades['win_rate']:.4f}")

        # Parameter range analysis
        print(f"\nParameter Range Analysis:")

        # Buy parameter analysis
        buy_analysis = {}
        for buy in range(5, 301, 5):
            buy_results = [r for r in trading_results if r['buy_threshold'] == buy]
            if buy_results:
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in buy_results])
                buy_analysis[buy] = avg_sharpe

        if buy_analysis:
            best_buy_range = max(buy_analysis.items(), key=lambda x: x[1])
            print(f"  Best Buy range: < {best_buy_range[0]} (avg Sharpe: {best_buy_range[1]:.4f})")

        # Sell parameter analysis
        sell_analysis = {}
        for sell in range(5, 301, 5):
            sell_results = [r for r in trading_results if r['sell_threshold'] == sell]
            if sell_results:
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in sell_results])
                sell_analysis[sell] = avg_sharpe

        if sell_analysis:
            best_sell_range = max(sell_analysis.items(), key=lambda x: x[1])
            print(f"  Best Sell range: > {best_sell_range[0]} (avg Sharpe: {best_sell_range[1]:.4f})")

        # Top 10 results by Sharpe ratio
        print(f"\nTop 10 Combinations by Sharpe Ratio:")
        top_10_sharpe = sorted(trading_results, key=lambda x: x['sharpe_ratio'], reverse=True)[:10]
        for i, result in enumerate(top_10_sharpe, 1):
            print(f"  {i:2d}. Buy < {result['buy_threshold']:3d}, Sell > {result['sell_threshold']:3d} | "
                  f"Sharpe: {result['sharpe_ratio']:7.4f} | Return: {result['total_return']:7.4f} | "
                  f"Trades: {result['total_trades']:3d} | Win%: {result['win_rate']:6.3f}")

    def save_results(self):
        """Save optimization results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save complete results
        results_file = f"rsi_optimization_complete_{timestamp}.json"

        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'optimization_metadata': self.results['optimization_metadata'],
                    'best_results': self.best_results,
                    'summary_statistics': {
                        'total_combinations_tested': self.results['total_combinations_tested'],
                        'trading_combinations': len([r for r in self.results['all_results'] if r['total_trades'] > 0]),
                        'analysis_timestamp': timestamp
                    }
                }, f, indent=2, ensure_ascii=False)

            print(f"\nComplete results saved to: {results_file}")

            # Save simplified report
            report_file = f"rsi_optimization_report_{timestamp}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("RSI Parameter Complete Optimization Report\n")
                f.write(f"Generated: {timestamp}\n")
                f.write("=" * 50 + "\n\n")

                metadata = self.results['optimization_metadata']
                f.write(f"Optimization Configuration:\n")
                f.write(f"  Buy parameter range: {metadata['buy_range']}\n")
                f.write(f"  Sell parameter range: {metadata['sell_range']}\n")
                f.write(f"  RSI period: {metadata['rsi_period']}\n")
                f.write(f"  Total combinations tested: {metadata['total_combinations']:,}\n")
                f.write(f"  Valid combinations: {metadata['valid_combinations']:,}\n")
                f.write(f"  Data period: {metadata['data_period']}\n")
                f.write(f"  Trading days: {metadata['trading_days']}\n\n")

                if self.best_results and self.best_results['best_sharpe']:
                    f.write("Best Parameter Combinations:\n\n")

                    best = self.best_results['best_sharpe']
                    f.write(f"Best Sharpe Ratio Combination:\n")
                    f.write(f"  Buy < {best['buy_threshold']}, Sell > {best['sell_threshold']}\n")
                    f.write(f"  Total Return: {best['total_return']:.6f}\n")
                    f.write(f"  Annual Return: {best['annual_return']:.6f}\n")
                    f.write(f"  Sharpe Ratio: {best['sharpe_ratio']:.6f}\n")
                    f.write(f"  Max Drawdown: {best['max_drawdown']:.6f}\n")
                    f.write(f"  Calmar Ratio: {best['calmar_ratio']:.6f}\n")
                    f.write(f"  Win Rate: {best['win_rate']:.4f}\n")
                    f.write(f"  Total Trades: {best['total_trades']}\n")
                    f.write(f"  Average Profit: {best['avg_profit']:.6f}\n\n")

                f.write("Detailed results available in JSON file.\n")

            print(f"Simplified report saved to: {report_file}")

        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    """Main execution function"""
    print("RSI Parameter Complete Optimizer")
    print("Buy < x, Sell > y, Range 0-300, Step 5")
    print("=" * 80)

    optimizer = CompleteRSIOptimizer()

    try:
        # Run complete optimization
        results = optimizer.run_complete_optimization()

        if results:
            # Analyze results
            optimizer.analyze_results()

            # Save results
            optimizer.save_results()

            print(f"\nOptimization Complete!")
            print(f"All RSI parameter combinations tested, best configurations identified.")
        else:
            print("Optimization failed")

    except Exception as e:
        print(f"Execution error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()