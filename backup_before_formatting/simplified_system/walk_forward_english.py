#!/usr/bin/env python3
"""
Walk-Forward Analysis for 0700.HK Trading Strategies (English Version)
Professional Walk-Forward Analysis System

Implements rolling window analysis based on quant trading best practices
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import time
import warnings
warnings.filterwarnings('ignore')

@dataclass
class WalkForwardConfig:
    """Walk-Forward Analysis Configuration"""
    train_period: int = 252      # Training period length (1 year)
    test_period: int = 63         # Testing period length (3 months)
    step_size: int = 21           # Rolling step size (1 month)
    min_train_periods: int = 126  # Minimum training periods (6 months)
    min_trades: int = 5           # Minimum number of trades

@dataclass
class StrategyResult:
    """Strategy Backtest Result"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades_count: int
    volatility: float
    calmar_ratio: float

class WalkForwardAnalyzer:
    """Professional Walk-Forward Analyzer"""

    def __init__(self, config: WalkForwardConfig = None):
        self.config = config or WalkForwardConfig()
        self.results = []
        self.portfolio_results = []

    def load_0700_data(self) -> pd.DataFrame:
        """Load 0700.HK historical data"""
        try:
            # Try to load real data
            data_file = "simplified_system/0700_results_20251125_181239.csv"
            if not pd.io.common.file_exists(data_file):
                # If no CSV file, generate simulated data
                data = self._generate_extended_0700_data()
            else:
                data = pd.read_csv(data_file)
                if 'date' not in data.columns:
                    data = self._generate_extended_0700_data()
                else:
                    data['date'] = pd.to_datetime(data['date'])
                    data = data.set_index('date').sort_index()

            # Ensure sufficient data points
            if len(data) < 1000:
                print(f"Insufficient data points ({len(data)}), generating extended data...")
                extended_data = self._generate_extended_0700_data()
                data = extended_data.iloc[:len(data)].copy()
                data['Close'] = extended_data['Close'].iloc[:len(data)].values

            return data

        except Exception as e:
            print(f"Data loading failed: {e}")
            return self._generate_extended_0700_data()

    def _generate_extended_0700_data(self) -> pd.DataFrame:
        """Generate extended 0700.HK simulated data (5 years)"""
        print("Generating 5-year 0700.HK historical data...")

        # Generate data based on real price ranges
        start_price = 400.0  # Starting price
        end_price = 520.0    # Ending price (uptrend)

        # Generate 5 years of data (approximately 1260 trading days)
        n_days = 1260
        dates = pd.date_range(start='2019-01-01', periods=n_days, freq='D')
        # Filter weekends
        dates = dates[dates.weekday < 5][:n_days]

        # Price path generation (with trend and volatility)
        trend = np.linspace(start_price, end_price, len(dates))
        volatility = 0.02  # Daily volatility 2%

        # Add random walk and seasonality
        random_walk = np.random.normal(0, 1, len(dates))
        seasonal = 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 252)  # Annual seasonality

        prices = trend * (1 + volatility * random_walk) + seasonal
        prices = np.maximum(prices, 100)  # Ensure price not below 100

        # Generate OHLC data
        data = pd.DataFrame({
            'date': dates,
            'Open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
            'High': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
            'Low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
            'Close': prices,
            'Volume': np.random.lognormal(15, 0.5, len(dates)).astype(int)
        })

        # Ensure OHLC relationships are correct
        data['High'] = np.maximum.reduce([data['Open'], data['Close'], data['High']])
        data['Low'] = np.minimum.reduce([data['Open'], data['Close'], data['Low']])

        return data.set_index('date').sort_index()

    def calculate_rsi_strategy(self, data: pd.DataFrame, period: int,
                              oversold: float, overbought: float) -> StrategyResult:
        """Calculate RSI strategy results"""
        try:
            # Calculate RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Generate trading signals
            signals = pd.DataFrame(index=data.index)
            signals['position'] = 0

            # RSI strategy signals
            buy_signals = (rsi < oversold) & (rsi.shift(1) >= oversold)
            sell_signals = (rsi > overbought) & (rsi.shift(1) <= overbought)

            signals.loc[buy_signals, 'position'] = 1
            signals.loc[sell_signals, 'position'] = -1

            # Position logic
            signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

            # Calculate returns
            returns = data['Close'].pct_change().fillna(0)
            strategy_returns = signals['position'].shift(1) * returns

            # Calculate performance metrics
            total_return = (1 + strategy_returns).prod() - 1
            sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std() if strategy_returns.std() > 0 else 0
            max_drawdown = self._calculate_max_drawdown(strategy_returns)
            win_rate = (strategy_returns > 0).mean()
            trades_count = (signals['position'].diff() != 0).sum()
            volatility = strategy_returns.std() * np.sqrt(252)
            calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

            return StrategyResult(
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                trades_count=trades_count,
                volatility=volatility,
                calmar_ratio=calmar_ratio
            )

        except Exception as e:
            print(f"RSI strategy calculation error: {e}")
            return StrategyResult(0, 0, 0, 0, 0, 0, 0)

    def calculate_ma_strategy(self, data: pd.DataFrame, short_period: int,
                             long_period: int) -> StrategyResult:
        """Calculate moving average strategy results"""
        try:
            # Calculate moving averages
            short_ma = data['Close'].rolling(window=short_period).mean()
            long_ma = data['Close'].rolling(window=long_period).mean()

            # Generate trading signals
            signals = pd.DataFrame(index=data.index)
            signals['position'] = 0

            # MA crossover strategy signals
            buy_signals = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
            sell_signals = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

            signals.loc[buy_signals, 'position'] = 1
            signals.loc[sell_signals, 'position'] = -1

            # Position logic
            signals['position'] = signals['position'].replace(0, np.nan).ffill().fillna(0)

            # Calculate returns
            returns = data['Close'].pct_change().fillna(0)
            strategy_returns = signals['position'].shift(1) * returns

            # Calculate performance metrics
            total_return = (1 + strategy_returns).prod() - 1
            sharpe_ratio = np.sqrt(252) * strategy_returns.mean() / strategy_returns.std() if strategy_returns.std() > 0 else 0
            max_drawdown = self._calculate_max_drawdown(strategy_returns)
            win_rate = (strategy_returns > 0).mean()
            trades_count = (signals['position'].diff() != 0).sum()
            volatility = strategy_returns.std() * np.sqrt(252)
            calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

            return StrategyResult(
                total_return=total_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                trades_count=trades_count,
                volatility=volatility,
                calmar_ratio=calmar_ratio
            )

        except Exception as e:
            print(f"MA strategy calculation error: {e}")
            return StrategyResult(0, 0, 0, 0, 0, 0, 0)

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def run_walk_forward_analysis(self, data: pd.DataFrame, strategy_configs: List[Dict]) -> Dict:
        """Run Walk-Forward analysis"""
        print("Starting Walk-Forward analysis...")
        print(f"Data range: {data.index[0]} to {data.index[-1]}")
        print(f"Total trading days: {len(data)}")

        all_results = {}

        for i, config in enumerate(strategy_configs):
            strategy_name = config['name']
            print(f"\nAnalyzing strategy {i+1}/{len(strategy_configs)}: {strategy_name}")
            print(f"Parameters: {config['params']}")

            strategy_results = []

            # Calculate rolling window count
            total_periods = len(data)
            current_train_start = 0

            window_count = 0

            while current_train_start + self.config.train_period + self.config.test_period <= total_periods:
                # Define training and testing periods
                train_end = current_train_start + self.config.train_period
                test_end = train_end + self.config.test_period

                train_data = data.iloc[current_train_start:train_end]
                test_data = data.iloc[train_end:test_end]

                print(f"  Window {window_count + 1}: Training {train_data.index[0].date()} to {train_data.index[-1].date()}, "
                      f"Testing {test_data.index[0].date()} to {test_data.index[-1].date()}")

                # Run strategy
                if strategy_name.startswith('RSI'):
                    result = self.calculate_rsi_strategy(
                        test_data,
                        config['params']['period'],
                        config['params']['oversold'],
                        config['params']['overbought']
                    )
                else:  # MA
                    result = self.calculate_ma_strategy(
                        test_data,
                        config['params']['short_period'],
                        config['params']['long_period']
                    )

                # Only keep strategies that meet minimum requirements
                if result.trades_count >= self.config.min_trades:
                    result.window_info = {
                        'train_start': train_data.index[0],
                        'train_end': train_data.index[-1],
                        'test_start': test_data.index[0],
                        'test_end': test_data.index[-1]
                    }
                    strategy_results.append(result)
                    print(f"    OK Return: {result.total_return:.2%}, Sharpe: {result.sharpe_ratio:.2f}, Trades: {result.trades_count}")
                else:
                    print(f"    FAIL Insufficient trades ({result.trades_count} < {self.config.min_trades})")

                # Roll window
                current_train_start += self.config.step_size
                window_count += 1

            if strategy_results:
                # Calculate summary statistics
                all_results[strategy_name] = {
                    'params': config['params'],
                    'windows': strategy_results,
                    'summary': self._calculate_summary_stats(strategy_results)
                }
                print(f"{strategy_name} Overall Performance: Avg Sharpe {all_results[strategy_name]['summary']['mean_sharpe']:.2f}, "
                      f"Avg Return {all_results[strategy_name]['summary']['mean_return']:.2%}")
            else:
                print(f"FAIL {strategy_name} No valid window results")

        return all_results

    def _calculate_summary_stats(self, results: List[StrategyResult]) -> Dict:
        """Calculate summary statistics"""
        returns = [r.total_return for r in results]
        sharpes = [r.sharpe_ratio for r in results]
        drawdowns = [r.max_drawdown for r in results]
        win_rates = [r.win_rate for r in results]
        trades_counts = [r.trades_count for r in results]
        calmar_ratios = [r.calmar_ratio for r in results]

        return {
            'num_windows': len(results),
            'mean_return': np.mean(returns),
            'std_return': np.std(returns),
            'mean_sharpe': np.mean(sharpes),
            'std_sharpe': np.std(sharpes),
            'mean_drawdown': np.mean(drawdowns),
            'max_drawdown': np.min(drawdowns),
            'mean_win_rate': np.mean(win_rates),
            'mean_trades': np.mean(trades_counts),
            'mean_calmar': np.mean(calmar_ratios),
            'success_rate': len([r for r in results if r.total_return > 0]) / len(results) if results else 0,
            'low_risk_rate': len([r for r in results if r.max_drawdown > -0.2]) / len(results) if results else 0
        }

    def generate_report(self, results: Dict) -> str:
        """Generate analysis report"""
        report = "="*80 + "\n"
        report += "0700.HK Walk-Forward Analysis Report\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Configuration: Training {self.config.train_period} days, Testing {self.config.test_period} days, Step {self.config.step_size} days\n"
        report += "="*80 + "\n\n"

        # Strategy comparison
        report += "Strategy Performance Comparison:\n"
        report += "-"*50 + "\n"

        strategy_comparison = []
        for name, data in results.items():
            summary = data['summary']
            strategy_comparison.append({
                'Strategy': name,
                'Parameters': str(data['params']),
                'Windows': summary['num_windows'],
                'Avg Return': f"{summary['mean_return']:.2%}",
                'Avg Sharpe': f"{summary['mean_sharpe']:.2f}",
                'Avg Drawdown': f"{summary['mean_drawdown']:.2%}",
                'Win Rate': f"{summary['mean_win_rate']:.1%}",
                'Success Rate': f"{summary['success_rate']:.1%}"
            })

        # Format table
        report += "{:<15} {:<25} {:<8} {:<12} {:<12} {:<15} {:<10} {:<12}\n".format(
            "Strategy", "Parameters", "Windows", "Avg Return", "Avg Sharpe", "Avg Drawdown", "Win Rate", "Success Rate"
        )
        report += "-"*100 + "\n"

        for comp in strategy_comparison:
            report += "{:<15} {:<25} {:<8} {:<12} {:<12} {:<15} {:<10} {:<12}\n".format(
                comp['Strategy'][:14], comp['Parameters'][:24], comp['Windows'],
                comp['Avg Return'], comp['Avg Sharpe'], comp['Avg Drawdown'],
                comp['Win Rate'], comp['Success Rate']
            )

        # Recommended strategies
        report += "\nRecommended Strategies:\n"
        report += "-"*30 + "\n"

        best_sharpe = max(results.items(), key=lambda x: x[1]['summary']['mean_sharpe'])
        best_return = max(results.items(), key=lambda x: x[1]['summary']['mean_return'])
        best_stable = min(results.items(), key=lambda x: x[1]['summary']['std_sharpe'])

        report += f"Highest Sharpe: {best_sharpe[0]} (Sharpe: {best_sharpe[1]['summary']['mean_sharpe']:.2f})\n"
        report += f"Highest Return: {best_return[0]} (Return: {best_return[1]['summary']['mean_return']:.2%})\n"
        report += f"Most Stable: {best_stable[0]} (Sharpe Std Dev: {best_stable[1]['summary']['std_sharpe']:.2f})\n"

        # Risk assessment
        report += "\nRisk Assessment:\n"
        report += "-"*20 + "\n"

        high_risk_strategies = []
        for name, data in results.items():
            if data['summary']['mean_drawdown'] < -0.15:
                high_risk_strategies.append(name)

        if high_risk_strategies:
            report += f"High Drawdown Risk Strategies: {', '.join(high_risk_strategies)}\n"

        low_trade_strategies = []
        for name, data in results.items():
            if data['summary']['mean_trades'] < 3:
                low_trade_strategies.append(name)

        if low_trade_strategies:
            report += f"Low Trading Frequency Strategies: {', '.join(low_trade_strategies)}\n"

        # Recommended configuration
        report += "\nRecommended Configuration:\n"
        report += "-"*30 + "\n"

        # Best configuration based on Walk-Forward results
        if results:
            # Select strategy with highest comprehensive score
            def strategy_score(data):
                summary = data['summary']
                return (
                    summary['mean_sharpe'] * 0.4 +
                    summary['mean_return'] * 10 * 0.3 +  # Higher weight for returns
                    summary['success_rate'] * 0.2 +
                    summary['low_risk_rate'] * 0.1
                )

            best_strategy = max(results.items(), key=lambda x: strategy_score(x[1]))

            report += f"Recommended Strategy: {best_strategy[0]}\n"
            report += f"Recommended Parameters: {best_strategy[1]['params']}\n"
            report += f"Expected Sharpe: {best_strategy[1]['summary']['mean_sharpe']:.2f}\n"
            report += f"Expected Annual Return: {best_strategy[1]['summary']['mean_return']:.2%}\n"
            report += f"Maximum Drawdown: {best_strategy[1]['summary']['mean_drawdown']:.2%}\n"

        return report

    def save_results(self, results: Dict, filename: str = None):
        """Save results to file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"simplified_system/walk_forward_results_{timestamp}.json"

        # Convert results to serializable format
        serializable_results = {}
        for name, data in results.items():
            serializable_results[name] = {
                'params': data['params'],
                'summary': data['summary'],
                'windows': [
                    {
                        'total_return': r.total_return,
                        'sharpe_ratio': r.sharpe_ratio,
                        'max_drawdown': r.max_drawdown,
                        'win_rate': r.win_rate,
                        'trades_count': r.trades_count,
                        'volatility': r.volatility,
                        'calmar_ratio': r.calmar_ratio,
                        'window_info': getattr(r, 'window_info', None)
                    } for r in data['windows']
                ]
            }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

        print(f"Results saved to: {filename}")
        return filename

def main():
    """Main function"""
    print("Starting 0700.HK Walk-Forward Professional Analysis System")

    # Configure analyzer
    config = WalkForwardConfig(
        train_period=252,    # 1 year training
        test_period=63,      # 3 months testing
        step_size=21,        # 1 month rolling
        min_trades=5         # Minimum 5 trades
    )

    analyzer = WalkForwardAnalyzer(config)

    # Load data
    data = analyzer.load_0700_data()
    print(f"Data loaded: {len(data)} trading days")

    # Define test strategies
    strategy_configs = [
        {
            'name': 'RSI_Conservative',
            'params': {'period': 21, 'oversold': 25, 'overbought': 75}
        },
        {
            'name': 'RSI_Moderate',
            'params': {'period': 14, 'oversold': 30, 'overbought': 70}
        },
        {
            'name': 'RSI_Aggressive',
            'params': {'period': 10, 'oversold': 35, 'overbought': 65}
        },
        {
            'name': 'MA_Short',
            'params': {'short_period': 10, 'long_period': 30}
        },
        {
            'name': 'MA_Medium',
            'params': {'short_period': 20, 'long_period': 60}
        },
        {
            'name': 'MA_Long',
            'params': {'short_period': 30, 'long_period': 90}
        }
    ]

    # Run analysis
    start_time = time.time()
    results = analyzer.run_walk_forward_analysis(data, strategy_configs)
    analysis_time = time.time() - start_time

    print(f"\nAnalysis completed, time elapsed: {analysis_time:.2f} seconds")

    # Generate report
    report = analyzer.generate_report(results)
    print("\n" + report)

    # Save results
    filename = analyzer.save_results(results)

    # Save report
    report_filename = filename.replace('.json', '_report.txt')
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Report saved to: {report_filename}")

    return results, filename

if __name__ == "__main__":
    results, filename = main()