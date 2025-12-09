#!/usr/bin/env python3
"""
COMPLETE CBSC REAL DATA BACKTEST
Using ALL Available Real Data - No Simulation, No Mock Data
Principal: Use however long the data is, backtest that much time
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

class CompleteCBSCBacktest:
    def __init__(self):
        self.data = None
        self.price_data = None
        self.sentiment_data = None
        self.results = {}

    def load_complete_dataset(self):
        """Load ALL available CBSC data"""
        print("=" * 80)
        print("COMPLETE CBSC REAL DATA BACKTEST SYSTEM")
        print("Using ALL Available Real Data - No Simulation")
        print("=" * 80)

        # Load merged dataset (complete available data)
        data_file = "CODEX--/warrant_sentiment_merged.csv"

        if not Path(data_file).exists():
            print(f"ERROR: Data file not found: {data_file}")
            return False

        try:
            self.data = pd.read_csv(data_file)
            print(f"\n✓ LOADED COMPLETE DATASET: {len(self.data)} records")

            # Data cleaning and preparation
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            self.data = self.data.dropna(subset=['Afternoon_Close', 'Date'])

            # Remove duplicates and sort
            self.data = self.data.drop_duplicates(subset=['Date'], keep='last')
            self.data = self.data.sort_values('Date')

            print(f"✓ CLEANED DATA: {len(self.data)} unique trading days")
            print(f"✓ DATE RANGE: {self.data['Date'].min().date()} to {self.data['Date'].max().date()}")
            print(f"✓ TOTAL PERIOD: {(self.data['Date'].max() - self.data['Date'].min()).days} calendar days")

            # Analyze data completeness
            unique_dates = self.data['Date'].nunique()
            date_span = (self.data['Date'].max() - self.data['Date'].min()).days + 1
            coverage_pct = (unique_dates / date_span) * 100

            print(f"✓ DATA COVERAGE: {unique_dates}/{date_span} days ({coverage_pct:.1f}%)")

            return True

        except Exception as e:
            print(f"ERROR: Data loading failed - {e}")
            return False

    def analyze_data_characteristics(self):
        """Analyze the complete dataset characteristics"""
        print(f"\n" + "=" * 60)
        print("COMPLETE DATASET ANALYSIS")
        print("=" * 60)

        # Price analysis
        price_stats = {
            'start_price': self.data['Afternoon_Close'].iloc[0],
            'end_price': self.data['Afternoon_Close'].iloc[-1],
            'min_price': self.data['Afternoon_Close'].min(),
            'max_price': self.data['Afternoon_Close'].max(),
            'total_return': (self.data['Afternoon_Close'].iloc[-1] - self.data['Afternoon_Close'].iloc[0]) / self.data['Afternoon_Close'].iloc[0]
        }

        print(f"📈 HANG SENG INDEX PERFORMANCE:")
        print(f"   Starting Level: {price_stats['start_price']:,.2f}")
        print(f"   Ending Level: {price_stats['end_price']:,.2f}")
        print(f"   Price Range: {price_stats['min_price']:,.2f} - {price_stats['max_price']:,.2f}")
        print(f"   Total Return: {price_stats['total_return']:.2%}")

        # Sentiment analysis
        sentiment_stats = {
            'total_bull_turnover': self.data['Bull_Turnover_HKD'].sum(),
            'total_bear_turnover': self.data['Bear_Turnover_HKD'].sum(),
            'avg_bull_ratio': self.data['Bull_Ratio'].mean(),
            'avg_bull_bear_ratio': self.data['Bull_Bear_Ratio'].mean(),
            'buy_signals': (self.data['Signal'] == 1).sum(),
            'sell_signals': (self.data['Signal'] == -1).sum(),
            'hold_signals': (self.data['Signal'] == 0).sum()
        }

        total_turnover = sentiment_stats['total_bull_turnover'] + sentiment_stats['total_bear_turnover']

        print(f"\n📊 CBSC SENTIMENT ANALYSIS:")
        print(f"   Total Bull Turnover: {sentiment_stats['total_bull_turnover']:,.0f} HKD")
        print(f"   Total Bear Turnover: {sentiment_stats['total_bear_turnover']:,.0f} HKD")
        print(f"   Total CBSC Volume: {total_turnover:,.0f} HKD")
        print(f"   Average Bull Ratio: {sentiment_stats['avg_bull_ratio']:.3f}")
        print(f"   Buy Signals: {sentiment_stats['buy_signals']} ({sentiment_stats['buy_signals']/len(self.data)*100:.1f}%)")
        print(f"   Sell Signals: {sentiment_stats['sell_signals']} ({sentiment_stats['sell_signals']/len(self.data)*100:.1f}%)")
        print(f"   Hold Signals: {sentiment_stats['hold_signals']} ({sentiment_stats['hold_signals']/len(self.data)*100:.1f}%)")

        # Volatility analysis
        if 'Daily_Return' in self.data.columns:
            daily_returns = self.data['Daily_Return'].dropna()
            if not daily_returns.empty:
                volatility = daily_returns.std() * np.sqrt(252)
                max_daily_gain = daily_returns.max()
                max_daily_loss = daily_returns.min()

                print(f"\n📊 VOLATILITY ANALYSIS:")
                print(f"   Annualized Volatility: {volatility:.2%}")
                print(f"   Best Single Day: {max_daily_gain:.2%}")
                print(f"   Worst Single Day: {max_daily_loss:.2%}")

        return price_stats, sentiment_stats

    def run_multiple_strategies(self):
        """Run multiple trading strategies on complete dataset"""
        print(f"\n" + "=" * 60)
        print("MULTI-STRATEGY BACKTESTING ON COMPLETE DATA")
        print("=" * 60)

        strategies = {
            'sentiment_follow': self.sentiment_follow_strategy,
            'mean_reversion': self.mean_reversion_strategy,
            'momentum': self.momentum_strategy,
            'volatility_breakout': self.volatility_breakout_strategy,
            'combined_signals': self.combined_signals_strategy
        }

        for strategy_name, strategy_func in strategies.items():
            print(f"\n🎯 TESTING: {strategy_name.upper()}")
            try:
                result = strategy_func()
                if result:
                    self.results[strategy_name] = result
                    self.print_strategy_results(strategy_name, result)
                else:
                    print(f"   ❌ Strategy failed to generate results")
            except Exception as e:
                print(f"   ❌ Strategy error: {e}")

    def sentiment_follow_strategy(self):
        """Strategy 1: Follow sentiment signals directly"""
        data = self.data.copy().reset_index(drop=True)

        initial_capital = 100000
        cash = initial_capital
        shares = 0
        trades = []
        equity_curve = [initial_capital]

        for i in range(1, len(data)):
            current_price = data['Afternoon_Close'].iloc[i]
            current_signal = data['Signal'].iloc[i]
            prev_signal = data['Signal'].iloc[i-1]

            # Buy on positive signal change
            if current_signal == 1 and prev_signal != 1 and shares == 0:
                position_value = cash * 0.25  # 25% position
                shares = int(position_value / current_price)
                cash -= shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'sentiment_buy'
                })

            # Sell on negative signal change
            elif current_signal == -1 and prev_signal != -1 and shares > 0:
                cash += shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'sentiment_sell'
                })
                shares = 0

            # Update equity
            current_value = cash + (shares * current_price)
            equity_curve.append(current_value)

        return self.calculate_performance_metrics(equity_curve, trades, "Sentiment Follow")

    def mean_reversion_strategy(self):
        """Strategy 2: Mean reversion using Bollinger Bands"""
        data = self.data.copy().reset_index(drop=True)

        # Calculate Bollinger Bands
        window = min(10, len(data) // 3)  # Adaptive window
        data['SMA'] = data['Afternoon_Close'].rolling(window).mean()
        data['Std'] = data['Afternoon_Close'].rolling(window).std()
        data['Upper_Band'] = data['SMA'] + (data['Std'] * 2)
        data['Lower_Band'] = data['SMA'] - (data['Std'] * 2)

        initial_capital = 100000
        cash = initial_capital
        shares = 0
        trades = []
        equity_curve = [initial_capital]

        for i in range(window, len(data)):
            current_price = data['Afternoon_Close'].iloc[i]
            lower_band = data['Lower_Band'].iloc[i]
            upper_band = data['Upper_Band'].iloc[i]

            # Buy at lower band
            if current_price <= lower_band and shares == 0:
                position_value = cash * 0.3
                shares = int(position_value / current_price)
                cash -= shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'mean_reversion_buy'
                })

            # Sell at upper band
            elif current_price >= upper_band and shares > 0:
                cash += shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'mean_reversion_sell'
                })
                shares = 0

            # Update equity
            current_value = cash + (shares * current_price)
            equity_curve.append(current_value)

        return self.calculate_performance_metrics(equity_curve, trades, "Mean Reversion")

    def momentum_strategy(self):
        """Strategy 3: Momentum based on price trends"""
        data = self.data.copy().reset_index(drop=True)

        # Calculate momentum indicators
        data['Return_3d'] = data['Afternoon_Close'].pct_change(3)
        data['Return_5d'] = data['Afternoon_Close'].pct_change(5)

        initial_capital = 100000
        cash = initial_capital
        shares = 0
        trades = []
        equity_curve = [initial_capital]

        for i in range(5, len(data)):
            current_price = data['Afternoon_Close'].iloc[i]
            momentum_3d = data['Return_3d'].iloc[i]
            momentum_5d = data['Return_5d'].iloc[i]

            # Strong momentum buy signal
            if momentum_3d > 0.01 and momentum_5d > 0.02 and shares == 0:
                position_value = cash * 0.35
                shares = int(position_value / current_price)
                cash -= shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'momentum_buy'
                })

            # Momentum sell signal
            elif momentum_3d < -0.01 and shares > 0:
                cash += shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'momentum_sell'
                })
                shares = 0

            # Update equity
            current_value = cash + (shares * current_price)
            equity_curve.append(current_value)

        return self.calculate_performance_metrics(equity_curve, trades, "Momentum")

    def volatility_breakout_strategy(self):
        """Strategy 4: Volatility breakout"""
        data = self.data.copy().reset_index(drop=True)

        # Calculate volatility
        data['Volatility'] = data['Daily_Return'].rolling(5).std().fillna(0)
        data['Vol_MA'] = data['Volatility'].rolling(10).mean().fillna(data['Volatility'].mean())

        initial_capital = 100000
        cash = initial_capital
        shares = 0
        trades = []
        equity_curve = [initial_capital]

        for i in range(10, len(data)):
            current_price = data['Afternoon_Close'].iloc[i]
            current_vol = data['Volatility'].iloc[i]
            vol_ma = data['Vol_MA'].iloc[i]

            # Volatility breakout buy
            if current_vol > vol_ma * 1.5 and shares == 0:
                position_value = cash * 0.2
                shares = int(position_value / current_price)
                cash -= shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'vol_breakout_buy'
                })

            # Take profit after 5 days or on volatility drop
            elif shares > 0 and (i >= len(data) - 5 or current_vol < vol_ma * 0.8):
                cash += shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'vol_breakout_sell'
                })
                shares = 0

            # Update equity
            current_value = cash + (shares * current_price)
            equity_curve.append(current_value)

        return self.calculate_performance_metrics(equity_curve, trades, "Volatility Breakout")

    def combined_signals_strategy(self):
        """Strategy 5: Combined sentiment and technical signals"""
        data = self.data.copy().reset_index(drop=True)

        # Calculate technical indicators
        window = min(10, len(data) // 3)
        data['SMA'] = data['Afternoon_Close'].rolling(window).mean()
        data['RSI'] = self.calculate_rsi(data['Afternoon_Close'], min(14, len(data) // 4))

        initial_capital = 100000
        cash = initial_capital
        shares = 0
        trades = []
        equity_curve = [initial_capital]

        for i in range(max(window, 14), len(data)):
            current_price = data['Afternoon_Close'].iloc[i]
            sentiment = data['Signal'].iloc[i]
            sma = data['SMA'].iloc[i]
            rsi = data['RSI'].iloc[i]

            # Combined buy signal
            buy_condition = (
                sentiment == 1 and  # Positive sentiment
                current_price > sma and  # Price above SMA
                rsi < 70  # Not overbought
            )

            if buy_condition and shares == 0:
                position_value = cash * 0.4  # Larger position for high confidence
                shares = int(position_value / current_price)
                cash -= shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'combined_buy'
                })

            # Combined sell signal
            sell_condition = (
                sentiment == -1 or  # Negative sentiment
                rsi > 80 or  # Overbought
                current_price < sma * 0.95  # Price below SMA
            )

            if sell_condition and shares > 0:
                cash += shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'signal': 'combined_sell'
                })
                shares = 0

            # Update equity
            current_value = cash + (shares * current_price)
            equity_curve.append(current_value)

        return self.calculate_performance_metrics(equity_curve, trades, "Combined Signals")

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return pd.Series([50] * len(prices))

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    def calculate_performance_metrics(self, equity_curve, trades, strategy_name):
        """Calculate comprehensive performance metrics"""
        if not equity_curve:
            return None

        initial_capital = equity_curve[0]
        final_value = equity_curve[-1]

        # Basic returns
        total_return = (final_value - initial_capital) / initial_capital

        # Daily returns
        equity_series = pd.Series(equity_curve)
        daily_returns = equity_series.pct_change().dropna()

        # Annualized metrics (adjusted for actual period)
        trading_days = len(equity_curve) - 1
        if trading_days > 0:
            annual_return = total_return * (252 / trading_days)
            volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        else:
            annual_return = 0
            volatility = 0
            sharpe_ratio = 0

        # Maximum drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min()

        # Win rate
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        buy_trades = [t for t in trades if t['action'] == 'BUY']

        win_rate = len(sell_trades) / len(trades) if trades else 0

        return {
            'strategy_name': strategy_name,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'win_rate': win_rate,
            'initial_capital': initial_capital,
            'final_value': final_value,
            'trading_days': trading_days,
            'equity_curve': equity_curve,
            'trades': trades
        }

    def print_strategy_results(self, strategy_name, result):
        """Print strategy results in a formatted way"""
        print(f"   📊 Total Return: {result['total_return']:.2%}")
        print(f"   📈 Annual Return: {result['annual_return']:.2%}")
        print(f"   📊 Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        print(f"   📉 Max Drawdown: {result['max_drawdown']:.2%}")
        print(f"   💰 Total Trades: {result['total_trades']}")
        print(f"   🎯 Win Rate: {result['win_rate']:.1%}")

    def generate_comparison_report(self):
        """Generate comprehensive comparison report"""
        print(f"\n" + "=" * 80)
        print("COMPREHENSIVE STRATEGY COMPARISON REPORT")
        print("=" * 80)

        if not self.results:
            print("❌ No strategy results to compare")
            return

        # Calculate benchmark (Buy and Hold HSI)
        hsi_return = (self.data['Afternoon_Close'].iloc[-1] - self.data['Afternoon_Close'].iloc[0]) / self.data['Afternoon_Close'].iloc[0]

        print(f"📊 BENCHMARK PERFORMANCE:")
        print(f"   Buy and Hold HSI: {hsi_return:.2%}")
        print(f"   Period: {(self.data['Date'].max() - self.data['Date'].min()).days} days")
        print(f"")

        # Strategy comparison table
        print(f"🎯 STRATEGY RANKINGS:")
        print("-" * 80)
        print(f"{'Strategy':<20} {'Total Ret':<12} {'Ann Ret':<12} {'Sharpe':<10} {'Max DD':<10} {'Trades':<8} {'Win Rate':<10}")
        print("-" * 80)

        sorted_results = sorted(self.results.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True)

        for rank, (name, result) in enumerate(sorted_results, 1):
            vs_benchmark = result['total_return'] - hsi_return
            print(f"{result['strategy_name']:<20} {result['total_return']:<12.2%} {result['annual_return']:<12.2%} "
                  f"{result['sharpe_ratio']:<10.3f} {result['max_drawdown']:<10.2%} {result['total_trades']:<8} "
                  f"{result['win_rate']:<10.1%}")

        # Best and worst performers
        best_strategy = sorted_results[0]
        worst_strategy = sorted_results[-1] if len(sorted_results) > 1 else None

        print(f"\n🏆 BEST PERFORMER: {best_strategy[1]['strategy_name']}")
        print(f"   Sharpe Ratio: {best_strategy[1]['sharpe_ratio']:.3f}")
        print(f"   Total Return: {best_strategy[1]['total_return']:.2%}")
        print(f"   vs Benchmark: {(best_strategy[1]['total_return'] - hsi_return):.2%}")

        if worst_strategy:
            print(f"\n⚠️  WORST PERFORMER: {worst_strategy[1]['strategy_name']}")
            print(f"   Sharpe Ratio: {worst_strategy[1]['sharpe_ratio']:.3f}")
            print(f"   Total Return: {worst_strategy[1]['total_return']:.2%}")

    def run_complete_analysis(self):
        """Run the complete analysis pipeline"""
        # Load all data
        if not self.load_complete_dataset():
            return False

        # Analyze data characteristics
        price_stats, sentiment_stats = self.analyze_data_characteristics()

        # Run all strategies
        self.run_multiple_strategies()

        # Generate comparison report
        self.generate_comparison_report()

        print(f"\n" + "=" * 80)
        print("COMPLETE CBSC REAL DATA BACKTEST - SUMMARY")
        print("=" * 80)
        print(f"✓ Data Period: {(self.data['Date'].max() - self.data['Date'].min()).days + 1} days")
        print(f"✓ Strategies Tested: {len(self.results)}")
        print(f"✓ 100% Real Data: No simulation, no mock prices")
        print(f"✓ Market: Hang Seng Index with CBSC sentiment integration")

        return True

def main():
    """Main execution function"""
    backtest = CompleteCBSCBacktest()
    success = backtest.run_complete_analysis()
    return success

if __name__ == "__main__":
    main()