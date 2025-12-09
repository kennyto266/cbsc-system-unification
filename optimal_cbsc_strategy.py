#!/usr/bin/env python3
"""
Optimal CBSC Strategy - Using Best Parameters from Optimization
基於最佳參數的CBSC最優策略應用

Author: CBSC Strategy Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime

warnings.filterwarnings('ignore')

class OptimalCBSCStrategy:
    """
    Apply the optimal parameters found during optimization
    """

    def __init__(self):
        self.data = None
        # Load optimal parameters
        self.optimal_params = self.load_optimal_parameters()

    def load_optimal_parameters(self):
        """Load the best parameters from optimization results"""
        try:
            # Try to load the most recent optimization results
            import glob
            result_files = glob.glob("cbsc_optimization_results_*.json")
            if not result_files:
                print("WARNING: No optimization results found, using default parameters")
                return self.get_default_parameters()

            latest_file = max(result_files)
            with open(latest_file, 'r') as f:
                results = json.load(f)

            # Get sentiment_momentum parameters (best performing strategy)
            return results['sentiment_momentum']['parameters']

        except Exception as e:
            print(f"WARNING: Could not load optimal parameters: {e}")
            return self.get_default_parameters()

    def get_default_parameters(self):
        """Fallback parameters"""
        return {
            'sentiment_short_window': 10,
            'sentiment_long_window': 15,
            'momentum_threshold': 0.05,
            'volume_multiplier': 1.3,
            'volume_ma_window': 10,
            'min_volume_threshold': 200000000,
            'position_size': 0.3
        }

    def load_data(self):
        """Load CBSC data"""
        data_file = "CODEX--/warrant_sentiment_merged.csv"

        if not Path(data_file).exists():
            print(f"ERROR: Data file not found: {data_file}")
            return False

        try:
            self.data = pd.read_csv(data_file)
            self.data['Date'] = pd.to_datetime(self.data['Date'])
            self.data = self.data.dropna(subset=['Afternoon_Close', 'Date'])
            self.data = self.data.drop_duplicates(subset=['Date'], keep='last')
            self.data = self.data.sort_values('Date')
            self.data['Close'] = self.data['Afternoon_Close']
            self.data['Total_Turnover'] = self.data['Bull_Turnover_HKD'] + self.data['Bear_Turnover_HKD']

            print(f"SUCCESS: Loaded {len(self.data)} days of CBSC data")
            return True

        except Exception as e:
            print(f"ERROR: Data loading failed - {e}")
            return False

    def apply_optimal_strategy(self):
        """Apply the optimal sentiment momentum strategy"""
        print("=" * 60)
        print("APPLYING OPTIMAL CBSC STRATEGY")
        print("=" * 60)

        params = self.optimal_params
        print(f"Using optimal parameters:")
        for param, value in params.items():
            print(f"  {param}: {value}")

        # Calculate indicators with optimal parameters
        self.data['Sentiment_MA_Short'] = self.data['Bull_Ratio'].rolling(params['sentiment_short_window'], min_periods=3).mean()
        self.data['Sentiment_MA_Long'] = self.data['Bull_Ratio'].rolling(params['sentiment_long_window'], min_periods=5).mean()
        self.data['Sentiment_Momentum'] = self.data['Sentiment_MA_Short'] - self.data['Sentiment_MA_Long']

        # Volume indicators
        self.data['Bull_Volume_MA'] = self.data['Bull_Turnover_HKD'].rolling(params['volume_ma_window'], min_periods=3).mean()
        self.data['Total_Volume_MA'] = self.data['Total_Turnover'].rolling(params['volume_ma_window'], min_periods=3).mean()

        # Generate signals with optimal parameters
        momentum_signal = self.data['Sentiment_Momentum'] > params['momentum_threshold']
        volume_surge = self.data['Bull_Turnover_HKD'] > (self.data['Bull_Volume_MA'] * params['volume_multiplier'])
        volume_confirmation = volume_surge & (self.data['Total_Volume_MA'] > params['min_volume_threshold'])

        self.data['Buy_Signal'] = momentum_signal & volume_confirmation
        self.data['Sell_Signal'] = (self.data['Sentiment_Momentum'] < -params['momentum_threshold']) & volume_surge

        # Backtest with optimal parameters
        result = self.backtest_optimal_strategy(params['position_size'])

        # Display results
        self.display_strategy_results(result)

        return result

    def backtest_optimal_strategy(self, position_size):
        """Backtest with optimal parameters"""

        initial_capital = 100000
        cash = initial_capital
        shares = 0
        trades = []
        equity_curve = [initial_capital]
        positions = []

        for i in range(1, len(self.data)):
            current_price = self.data['Close'].iloc[i]
            current_value = cash + (shares * current_price)
            equity_curve.append(current_value)

            # Buy signal
            if self.data['Buy_Signal'].iloc[i] and shares == 0:
                position_value = cash * position_size
                shares = int(position_value / current_price)
                cash -= shares * current_price

                trade_info = {
                    'date': self.data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'position_value': position_value,
                    'bull_ratio': self.data['Bull_Ratio'].iloc[i],
                    'sentiment_momentum': self.data['Sentiment_Momentum'].iloc[i],
                    'volume_ratio': self.data['Total_Turnover'].iloc[i] / self.data['Total_Volume_MA'].iloc[i] if self.data['Total_Volume_MA'].iloc[i] > 0 else 0
                }
                trades.append(trade_info)
                positions.append(trade_info)

            # Sell signal
            elif self.data['Sell_Signal'].iloc[i] and shares > 0:
                cash += shares * current_price

                trade_info = {
                    'date': self.data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'position_value': shares * current_price,
                    'bull_ratio': self.data['Bull_Ratio'].iloc[i],
                    'sentiment_momentum': self.data['Sentiment_Momentum'].iloc[i],
                    'volume_ratio': self.data['Total_Turnover'].iloc[i] / self.data['Total_Volume_MA'].iloc[i] if self.data['Total_Volume_MA'].iloc[i] > 0 else 0
                }
                trades.append(trade_info)
                positions[-1]['sell_date'] = self.data['Date'].iloc[i]
                positions[-1]['sell_price'] = current_price
                positions[-1]['return'] = (current_price - positions[-1]['price']) / positions[-1]['price']

                shares = 0

        # Calculate metrics
        final_value = equity_curve[-1]
        total_return = (final_value - initial_capital) / initial_capital

        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            annual_return = total_return * (252 / len(self.data))
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        else:
            annual_return = 0
            sharpe_ratio = 0

        # Maximum drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min()

        # Win rate
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        winning_trades = [p for p in positions if 'return' in p and p['return'] > 0]
        win_rate = len(winning_trades) / len(positions) if positions else 0

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'positions': positions,
            'equity_curve': equity_curve,
            'trades': trades
        }

    def display_strategy_results(self, result):
        """Display detailed strategy results"""

        print(f"\n{'='*60}")
        print("OPTIMAL STRATEGY PERFORMANCE")
        print(f"{'='*60}")

        print(f"\nKey Performance Metrics:")
        print(f"   Total Return: {result['total_return']:.2%}")
        print(f"   Annual Return: {result['annual_return']:.2%}")
        print(f"   Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        print(f"   Max Drawdown: {result['max_drawdown']:.2%}")
        print(f"   Total Trades: {result['total_trades']}")
        print(f"   Win Rate: {result['win_rate']:.1%}")

        # Market comparison
        benchmark_return = (self.data['Afternoon_Close'].iloc[-1] - self.data['Afternoon_Close'].iloc[0]) / self.data['Afternoon_Close'].iloc[0]
        outperformance = result['total_return'] - benchmark_return
        print(f"   Market Return: {benchmark_return:.2%}")
        print(f"   Outperformance: {outperformance:.2%}")

        # Detailed trades
        print(f"\nDetailed Trading History:")
        print("-" * 80)
        print(f"{'Date':<12} {'Action':<6} {'Price':<10} {'Shares':<8} {'Bull Ratio':<10} {'Momentum':<10} {'Volume':<8}")
        print("-" * 80)

        for trade in result['trades']:
            momentum_val = trade.get('sentiment_momentum', 0)
            volume_val = trade.get('volume_ratio', 0)
            print(f"{trade['date'].strftime('%Y-%m-%d'):<12} {trade['action']:<6} "
                  f"{trade['price']:<10.2f} {trade['shares']:<8} {trade.get('bull_ratio', 0):<10.3f} "
                  f"{momentum_val:<10.3f} {volume_val:<8.1f}")

        # Position analysis
        if result['positions']:
            print(f"\nPosition Analysis:")
            avg_return = np.mean([p['return'] for p in result['positions'] if 'return' in p])
            print(f"   Average Trade Return: {avg_return:.2%}")
            print(f"   Best Trade: {max([p['return'] for p in result['positions'] if 'return' in p]):.2%}")
            print(f"   Worst Trade: {min([p['return'] for p in result['positions'] if 'return' in p]):.2%}")

        # Current market sentiment
        latest_data = self.data.iloc[-1]
        print(f"\nCurrent Market Sentiment:")
        print(f"   Date: {latest_data['Date'].strftime('%Y-%m-%d')}")
        print(f"   HSI Close: {latest_data['Close']:,.2f}")
        print(f"   Bull Ratio: {latest_data['Bull_Ratio']:.3f}")
        print(f"   Total Turnover: {latest_data['Total_Turnover']:,.0f} HKD")

        # Current signal
        current_signal = "HOLD"
        if latest_data['Buy_Signal']:
            current_signal = "BUY"
        elif latest_data['Sell_Signal']:
            current_signal = "SELL"

        print(f"   Current Signal: {current_signal}")

    def generate_trading_signals(self, days_forward=5):
        """Generate trading signals for next few days"""
        print(f"\nTrading Signals for Next {days_forward} Days:")
        print("-" * 40)

        # Get the most recent sentiment trend
        recent_sentiment = self.data['Bull_Ratio'].tail(10)
        recent_momentum = self.data['Sentiment_Momentum'].tail(10)

        current_trend = "NEUTRAL"
        if recent_sentiment.is_monotonic_increasing and recent_momentum.iloc[-1] > 0:
            current_trend = "BULLISH"
        elif recent_sentiment.is_monotonic_decreasing and recent_momentum.iloc[-1] < 0:
            current_trend = "BEARISH"

        print(f"Current Trend: {current_trend}")
        print(f"Latest Sentiment: {self.data['Bull_Ratio'].iloc[-1]:.3f}")
        print(f"Latest Momentum: {self.data['Sentiment_Momentum'].iloc[-1]:.3f}")

        # Recommendation
        if current_trend == "BULLISH" and self.data['Total_Turnover'].iloc[-1] > self.optimal_params['min_volume_threshold']:
            print("Recommendation: CONSIDER BUYING on next signal confirmation")
        elif current_trend == "BEARISH":
            print("Recommendation: WAIT FOR CLEAR BUY SIGNAL")
        else:
            print("Recommendation: HOLD CURRENT POSITION")

def main():
    """Main execution function"""
    print("Starting Optimal CBSC Strategy Application...")
    print("Using Best Parameters from UltraThink Optimization")

    strategy = OptimalCBSCStrategy()

    if not strategy.load_data():
        print("ERROR: Could not load data")
        return

    result = strategy.apply_optimal_strategy()
    strategy.generate_trading_signals()

    print(f"\nOptimal Strategy Analysis Complete!")
    print(f"Best performing strategy: Sentiment Momentum")
    print(f"Ready for real-time trading application")

if __name__ == "__main__":
    main()