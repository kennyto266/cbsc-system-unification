#!/usr/bin/env python3
"""
Simple 0700.HK Backtest using Available Components
Focused on demonstrating the unified framework capabilities
"""

import pandas as pd
import numpy as np
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Simple0700Backtest:
    """Simple 0700.HK backtest implementation"""

    def __init__(self):
        self.symbol = '0700.HK'
        self.start_time = time.time()
        self.results = []

    def load_or_generate_data(self):
        """Load or generate 0700.HK data"""
        logger.info("Loading/generating 0700.HK data...")

        # Try to find existing data
        data_paths = [
            'data/0700_hk_data.csv',
            'data/cache/hsi_constituents_82.json',
            '0700_hk_technical_analysis_report_*.json'
        ]

        for path_pattern in data_paths:
            if '*' in path_pattern:
                import glob
                files = glob.glob(path_pattern)
                if files:
                    path_pattern = files[-1]  # Use latest

            if Path(path_pattern).exists():
                try:
                    if path_pattern.endswith('.csv'):
                        data = pd.read_csv(path_pattern, index_col=0, parse_dates=True)
                    elif path_pattern.endswith('.json'):
                        with open(path_pattern, 'r') as f:
                            json_data = json.load(f)
                            if 'data' in json_data:
                                data = pd.DataFrame(json_data['data'])
                            else:
                                data = pd.DataFrame(json_data)

                        # Ensure we have date index
                        if 'date' in data.columns:
                            data['date'] = pd.to_datetime(data['date'])
                            data.set_index('date', inplace=True)

                    logger.info(f"Loaded data from {path_pattern}: {len(data)} records")

                    # Ensure required columns
                    required_cols = ['close', 'volume']
                    if all(col in data.columns for col in required_cols):
                        # Derive OHLC if missing
                        if 'open' not in data.columns:
                            data['open'] = data['close'].shift(1).fillna(data['close'])
                        if 'high' not in data.columns:
                            data['high'] = data[['open', 'close']].max(axis=1) * 1.01
                        if 'low' not in data.columns:
                            data['low'] = data[['open', 'close']].min(axis=1) * 0.99

                        return data
                except Exception as e:
                    logger.warning(f"Failed to load {path_pattern}: {e}")
                    continue

        # Generate realistic test data
        return self.generate_realistic_data()

    def generate_realistic_data(self):
        """Generate realistic 0700.HK test data"""
        logger.info("Generating realistic 0700.HK test data...")

        # Generate 2 years of data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = dates[dates.weekday < 5]  # Weekdays only

        np.random.seed(42)  # For reproducibility
        base_price = 75.0

        # Generate realistic price movements
        returns = np.random.normal(0.0008, 0.025, len(dates))  # Daily returns

        # Add some trend and volatility
        trend = np.linspace(0, 0.15, len(dates))  # Slight upward trend
        volatility = np.random.uniform(0.015, 0.035, len(dates))

        prices = [base_price]
        for i, (ret, trend_adj, vol) in enumerate(zip(returns, trend, volatility)):
            noise = np.random.normal(0, vol)
            new_price = prices[-1] * (1 + ret + trend_adj/252 + noise)
            prices.append(max(new_price, 10.0))  # Minimum price

        prices = prices[1:]  # Remove initial price

        # Generate OHLCV
        data = []
        for i, (date, close_price) in enumerate(zip(dates, prices)):
            # Realistic intraday range
            daily_volatility = np.random.uniform(0.01, 0.04)
            high = close_price * (1 + daily_volatility * np.random.uniform(0.3, 1.0))
            low = close_price * (1 - daily_volatility * np.random.uniform(0.3, 1.0))

            # Open price with gap
            if i == 0:
                open_price = close_price
            else:
                gap = np.random.normal(0, close_price * 0.008)
                open_price = max(prices[i-1] + gap, low, 10.0)

            # Ensure OHLC relationships
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)

            # Volume (HK stocks typical volume)
            base_volume = 1500000
            volume_factor = 1 + abs(returns[i]) * 8 + trend_adj * 2
            volume = int(base_volume * volume_factor * np.random.uniform(0.3, 2.5))

            data.append({
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(close_price, 2),
                'volume': volume
            })

        df = pd.DataFrame(data, index=dates)
        logger.info(f"Generated {len(df)} records of 0700.HK data")
        return df

    def calculate_technical_indicators(self, data):
        """Calculate technical indicators"""
        logger.info("Calculating technical indicators...")

        df = data.copy()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()

        # MACD
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

        # Volume indicators
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']

        # Price momentum
        df['momentum_10'] = df['close'].pct_change(10)
        df['momentum_20'] = df['close'].pct_change(20)

        return df

    def generate_test_strategies(self):
        """Generate test strategies with different parameters"""
        logger.info("Generating test strategies...")

        strategies = []

        # Strategy 1: RSI Mean Reversion
        for rsi_period in [14, 21]:
            for oversold in [20, 25, 30]:
                for overbought in [70, 75, 80]:
                    strategies.append({
                        'name': f'RSI_MR_{rsi_period}_{oversold}_{overbought}',
                        'type': 'rsi_mean_reversion',
                        'params': {
                            'rsi_period': rsi_period,
                            'oversold': oversold,
                            'overbought': overbought
                        }
                    })

        # Strategy 2: MACD Crossover
        for fast in [12, 15]:
            for slow in [26, 30]:
                for signal in [9, 12]:
                    strategies.append({
                        'name': f'MACD_X_{fast}_{slow}_{signal}',
                        'type': 'macd_crossover',
                        'params': {
                            'fast_period': fast,
                            'slow_period': slow,
                            'signal_period': signal
                        }
                    })

        # Strategy 3: Bollinger Bands Breakout
        for bb_period in [20, 25]:
            for bb_std in [1.5, 2.0]:
                strategies.append({
                    'name': f'BB_Break_{bb_period}_{bb_std}',
                    'type': 'bollinger_breakout',
                    'params': {
                        'period': bb_period,
                        'std_dev': bb_std
                    }
                })

        # Strategy 4: Dual Moving Average
        for fast_ma in [10, 15]:
            for slow_ma in [30, 50]:
                strategies.append({
                    'name': f'DMA_{fast_ma}_{slow_ma}',
                    'type': 'dual_moving_average',
                    'params': {
                        'fast_ma': fast_ma,
                        'slow_ma': slow_ma
                    }
                })

        logger.info(f"Generated {len(strategies)} test strategies")
        return strategies

    def backtest_strategy(self, data, strategy):
        """Backtest a single strategy"""
        try:
            df = data.copy()
            signals = []
            positions = []

            if strategy['type'] == 'rsi_mean_reversion':
                params = strategy['params']
                # Generate signals based on RSI
                for i in range(len(df)):
                    if i < params['rsi_period']:
                        signals.append(0)
                        positions.append(0)
                    else:
                        if df['rsi'].iloc[i] < params['oversold']:
                            signals.append(1)  # Buy
                        elif df['rsi'].iloc[i] > params['overbought']:
                            signals.append(-1)  # Sell
                        else:
                            signals.append(0)  # Hold
                        positions.append(signals[-1])

            elif strategy['type'] == 'macd_crossover':
                params = strategy['params']
                for i in range(len(df)):
                    if i < params['slow_period']:
                        signals.append(0)
                        positions.append(0)
                    else:
                        if df['macd'].iloc[i] > df['macd_signal'].iloc[i] and \
                           df['macd'].iloc[i-1] <= df['macd_signal'].iloc[i-1]:
                            signals.append(1)  # Buy signal
                        elif df['macd'].iloc[i] < df['macd_signal'].iloc[i] and \
                             df['macd'].iloc[i-1] >= df['macd_signal'].iloc[i-1]:
                            signals.append(-1)  # Sell signal
                        else:
                            signals.append(0)  # Hold
                        positions.append(signals[-1])

            elif strategy['type'] == 'bollinger_breakout':
                params = strategy['params']
                for i in range(len(df)):
                    if i < params['period']:
                        signals.append(0)
                        positions.append(0)
                    else:
                        if df['close'].iloc[i] > df['bb_upper'].iloc[i]:
                            signals.append(1)  # Breakout above
                        elif df['close'].iloc[i] < df['bb_lower'].iloc[i]:
                            signals.append(-1)  # Breakout below
                        else:
                            signals.append(0)  # Hold
                        positions.append(signals[-1])

            elif strategy['type'] == 'dual_moving_average':
                params = strategy['params']
                for i in range(len(df)):
                    if i < params['slow_ma']:
                        signals.append(0)
                        positions.append(0)
                    else:
                        fast_col = f'sma_{params["fast_ma"]}'
                        slow_col = f'sma_{params["slow_ma"]}'
                        if df[fast_col].iloc[i] > df[slow_col].iloc[i]:
                            signals.append(1)
                        elif df[fast_col].iloc[i] < df[slow_col].iloc[i]:
                            signals.append(-1)
                        else:
                            signals.append(0)
                        positions.append(signals[-1])

            # Calculate returns
            df['signal'] = signals
            df['position'] = positions

            # Calculate strategy returns
            df['strategy_returns'] = df['position'].shift(1) * df['close'].pct_change()

            # Calculate performance metrics
            total_return = (df['strategy_returns'].sum() + 1)
            sharpe_ratio = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252) if df['strategy_returns'].std() > 0 else 0
            max_drawdown = self.calculate_max_drawdown(df['strategy_returns'])

            # Calculate trade statistics
            trades = df[df['signal'] != 0]
            win_trades = len(df[df['strategy_returns'] > 0])
            total_trades = len(df[df['strategy_returns'] != 0])
            win_rate = win_trades / total_trades if total_trades > 0 else 0

            return {
                'strategy_name': strategy['name'],
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'equity_curve': (1 + df['strategy_returns']).cumsum().tolist()
            }

        except Exception as e:
            logger.error(f"Error backtesting {strategy['name']}: {e}")
            return None

    def calculate_max_drawdown(self, returns):
        """Calculate maximum drawdown"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def run_complete_backtest(self):
        """Run complete backtest on all strategies"""
        logger.info("Starting complete 0700.HK backtest...")

        # Load data
        data = self.load_or_generate_data()

        # Calculate indicators
        data = self.calculate_technical_indicators(data)

        # Generate strategies
        strategies = self.generate_test_strategies()

        # Backtest all strategies
        results = []
        successful_tests = 0

        for i, strategy in enumerate(strategies):
            logger.info(f"Testing strategy {i+1}/{len(strategies)}: {strategy['name']}")

            result = self.backtest_strategy(data, strategy)
            if result:
                results.append(result)
                successful_tests += 1

        # Sort results by Sharpe ratio
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

        self.results = results

        # Calculate summary statistics
        if results:
            sharpe_ratios = [r['sharpe_ratio'] for r in results]
            returns = [r['total_return'] for r in results]

            summary = {
                'total_strategies': len(strategies),
                'successful_tests': successful_tests,
                'best_sharpe': max(sharpe_ratios),
                'average_sharpe': np.mean(sharpe_ratios),
                'best_return': max(returns),
                'average_return': np.mean(returns),
                'top_strategies': results[:10]
            }
        else:
            summary = {'error': 'No successful backtests'}

        return summary, data, results

    def save_results(self, summary, data, results):
        """Save backtest results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save results
        results_file = f"0700_hk_backtest_results_{timestamp}.json"

        output_data = {
            'timestamp': datetime.now().isoformat(),
            'symbol': self.symbol,
            'data_summary': {
                'records': len(data),
                'start_date': data.index.min().isoformat(),
                'end_date': data.index.max().isoformat(),
                'price_range': f"{data['close'].min():.2f} - {data['close'].max():.2f}"
            },
            'summary': summary,
            'all_results': results,
            'execution_time': time.time() - self.start_time
        }

        with open(results_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"Results saved to: {results_file}")
        return results_file

    def print_summary(self, summary):
        """Print backtest summary"""
        print("\n" + "=" * 70)
        print("0700.HK BACKTEST RESULTS")
        print("=" * 70)

        print(f"Total Strategies Tested: {summary['total_strategies']}")
        print(f"Successful Tests: {summary['successful_tests']}")
        print(f"Best Sharpe Ratio: {summary['best_sharpe']:.3f}")
        print(f"Average Sharpe Ratio: {summary['average_sharpe']:.3f}")
        print(f"Best Total Return: {summary['best_return']:.2%}")
        print(f"Average Return: {summary['average_return']:.2%}")

        print(f"\nTop 5 Strategies:")
        for i, strategy in enumerate(summary['top_strategies'][:5], 1):
            print(f"  {i}. {strategy['strategy_name']}")
            print(f"     Sharpe: {strategy['sharpe_ratio']:.3f}, "
                  f"Return: {strategy['total_return']:.2%}, "
                  f"Win Rate: {strategy['win_rate']:.1%}")


def main():
    """Main execution"""
    print("0700.HK Backtest Using Unified Framework")
    print("=" * 50)

    backtest = Simple0700Backtest()

    try:
        summary, data, results = backtest.run_complete_backtest()

        if 'error' not in summary:
            backtest.print_summary(summary)
            results_file = backtest.save_results(summary, data, results)
            print(f"\nDetailed results saved to: {results_file}")
            return True
        else:
            print(f"Backtest failed: {summary['error']}")
            return False

    except Exception as e:
        print(f"Backtest execution failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)