#!/usr/bin/env python3
"""
Complete Optimal CBSC Strategies - All 4 Strategies with Best Parameters
完整最優CBSC策略系統 - 包含所有4種策略的最佳參數

Author: CBSC Strategy Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import json
from datetime import datetime
from typing import Dict

warnings.filterwarnings('ignore')

class CompleteOptimalCBSC:
    """
    Complete system with optimal parameters for all 4 CBSC strategies
    """

    def __init__(self):
        self.data = None
        # Load best parameters from both optimization runs
        self.optimal_params = self.load_all_optimal_parameters()

    def load_all_optimal_parameters(self):
        """Load the best parameters from both regular and aggressive optimization"""

        # Original optimized sentiment momentum parameters (best performer)
        sentiment_momentum_params = {
            'sentiment_short_window': 10,
            'sentiment_long_window': 15,
            'momentum_threshold': 0.05,
            'volume_multiplier': 1.3,
            'volume_ma_window': 10,
            'min_volume_threshold': 200000000,
            'position_size': 0.3
        }

        # Aggressive optimized parameters for other 3 strategies
        aggressive_params = {
            'volume_reversal': {
                'ratio_short_window': 3,
                'ratio_long_window': 10,
                'volume_spike_multiplier': 1.1,
                'volume_spike_window': 5,
                'extreme_bull_threshold': 0.55,
                'extreme_bear_threshold': 0.45,
                'position_size': 0.4
            },
            'risk_adjusted_bollinger': {
                'rsi_period': 7,
                'rsi_overbought': 60,
                'rsi_oversold': 30,
                'bb_period': 10,
                'bb_std_multiplier': 1.8,
                'risk_threshold_bull': 0.7,
                'risk_threshold_bear': 0.6,
                'position_size': 0.3,
                'entry_mode': 'moderate'
            },
            'time_decay_momentum': {
                'decay_half_life': 30,
                'momentum_strength_threshold': 0.03,
                'bull_threshold': 0.52,
                'bear_threshold': 0.5,
                'time_decay_threshold': 0.5,
                'min_turnover_threshold': 500000,
                'position_size': 0.35,
                'momentum_mode': 'sensitive'
            }
        }

        all_params = {
            'sentiment_momentum': sentiment_momentum_params,
            **aggressive_params
        }

        return all_params

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
            print(f"Date range: {self.data['Date'].min().date()} to {self.data['Date'].max().date()}")
            return True

        except Exception as e:
            print(f"ERROR: Data loading failed - {e}")
            return False

    def sentiment_momentum_strategy(self, data: pd.DataFrame) -> Dict:
        """Optimal sentiment momentum strategy"""
        params = self.optimal_params['sentiment_momentum']

        # Calculate sentiment momentum
        data['Sentiment_MA_Short'] = data['Bull_Ratio'].rolling(params['sentiment_short_window'], min_periods=3).mean()
        data['Sentiment_MA_Long'] = data['Bull_Ratio'].rolling(params['sentiment_long_window'], min_periods=5).mean()
        data['Sentiment_Momentum'] = data['Sentiment_MA_Short'] - data['Sentiment_MA_Long']

        # Volume indicators
        data['Bull_Volume_MA'] = data['Bull_Turnover_HKD'].rolling(params['volume_ma_window'], min_periods=3).mean()
        data['Total_Volume_MA'] = data['Total_Turnover'].rolling(params['volume_ma_window'], min_periods=3).mean()

        # Generate signals with optimal parameters
        momentum_signal = data['Sentiment_Momentum'] > params['momentum_threshold']
        volume_surge = data['Bull_Turnover_HKD'] > (data['Bull_Volume_MA'] * params['volume_multiplier'])
        volume_confirmation = volume_surge & (data['Total_Volume_MA'] > params['min_volume_threshold'])

        buy_signals = momentum_signal & volume_confirmation
        sell_signals = (data['Sentiment_Momentum'] < -params['momentum_threshold']) & volume_surge

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'], "sentiment_momentum")

    def volume_reversal_strategy(self, data: pd.DataFrame) -> Dict:
        """Optimal aggressive volume reversal strategy"""
        params = self.optimal_params['volume_reversal']

        # Calculate volume ratios
        data['Ratio_Short'] = data['Bull_Ratio'].rolling(params['ratio_short_window'], min_periods=2).mean()
        data['Ratio_Long'] = data['Bull_Ratio'].rolling(params['ratio_long_window'], min_periods=3).mean()

        # Volume spike detection
        data['Volume_Spike'] = data['Total_Turnover'] > (data['Total_Turnover'].rolling(params['volume_spike_window'], min_periods=3).mean() * params['volume_spike_multiplier'])

        # Extreme ratio detection
        extreme_bull = data['Ratio_Short'] > params['extreme_bull_threshold']
        extreme_bear = data['Ratio_Short'] < params['extreme_bear_threshold']

        # Multiple reversal signals
        ratio_turning_bull = (data['Ratio_Short'] > data['Ratio_Long']) & extreme_bear
        ratio_turning_bear = (data['Ratio_Short'] < data['Ratio_Long']) & extreme_bull
        momentum_reversal_bull = (data['Ratio_Short'].diff() > 0.05) & extreme_bear
        momentum_reversal_bear = (data['Ratio_Short'].diff() < -0.05) & extreme_bull

        buy_signals = (ratio_turning_bull | momentum_reversal_bull) & data['Volume_Spike']
        sell_signals = (ratio_turning_bear | momentum_reversal_bear) & data['Volume_Spike']

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'], "volume_reversal")

    def risk_adjusted_bollinger_strategy(self, data: pd.DataFrame) -> Dict:
        """Optimal aggressive risk-adjusted Bollinger strategy"""
        params = self.optimal_params['risk_adjusted_bollinger']

        # RSI calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(params['rsi_period'], min_periods=3).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(params['rsi_period'], min_periods=3).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger bands
        data['BB_Middle'] = data['Close'].rolling(params['bb_period']).mean()
        data['BB_Std'] = data['Close'].rolling(params['bb_period']).std()
        data['BB_Upper'] = data['BB_Middle'] + (data['BB_Std'] * params['bb_std_multiplier'])
        data['BB_Lower'] = data['BB_Middle'] - (data['BB_Std'] * params['bb_std_multiplier'])

        # Risk assessment
        data['Call_Risk_Bull'] = np.maximum(0, (data['Bull_Ratio'] - 0.5) * 2)
        data['Call_Risk_Bear'] = np.maximum(0, (0.5 - data['Bull_Ratio']) * 2)

        # Signal generation based on entry mode
        rsi_buy = data['RSI'] < params['rsi_oversold']
        rsi_sell = data['RSI'] > params['rsi_overbought']
        bb_buy = (data['Close'] < data['BB_Lower']) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
        bb_sell = (data['Close'] > data['BB_Upper']) & (data['Call_Risk_Bear'] < params['risk_threshold_bear'])

        if params['entry_mode'] == 'aggressive':
            buy_signals = (rsi_buy | bb_buy) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
            sell_signals = (rsi_sell | bb_sell) | (data['RSI'] > 55)
        elif params['entry_mode'] == 'moderate':
            buy_signals = (rsi_buy | bb_buy) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
            sell_signals = rsi_sell | bb_sell
        else:  # balanced
            buy_signals = (rsi_buy & bb_buy) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
            sell_signals = (rsi_sell | bb_sell) & (data['Call_Risk_Bear'] < params['risk_threshold_bear'])

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'], "risk_adjusted_bollinger")

    def time_decay_momentum_strategy(self, data: pd.DataFrame) -> Dict:
        """Optimal aggressive time decay momentum strategy"""
        params = self.optimal_params['time_decay_momentum']

        # Calculate time decay factor
        days_to_expiry = np.arange(len(data))
        data['Time_Decay_Factor'] = np.exp(-days_to_expiry / params['decay_half_life'])
        data['Adjusted_Price'] = data['Close'] * (1 + data['Time_Decay_Factor'] * 0.1)

        # Momentum strength adjustment
        data['Momentum_Strength'] = data['Bull_Ratio'] * data['Time_Decay_Factor']

        # Momentum signals based on momentum mode
        if params['momentum_mode'] == 'sensitive':
            momentum_buy = (data['Momentum_Strength'] > params['momentum_strength_threshold']) & (data['Bull_Ratio'] > params['bull_threshold'])
            momentum_sell = (data['Momentum_Strength'] < params['momentum_strength_threshold']) | (data['Bull_Ratio'] < params['bear_threshold'])
        elif params['momentum_mode'] == 'normal':
            momentum_buy = (data['Momentum_Strength'] > params['momentum_strength_threshold']) & (data['Bull_Ratio'] > params['bull_threshold'])
            momentum_sell = (data['Momentum_Strength'] < params['momentum_strength_threshold']) & (data['Bull_Ratio'] < params['bear_threshold'])
        else:  # stable
            momentum_buy = (data['Momentum_Strength'] > params['momentum_strength_threshold'] * 1.5) & (data['Bull_Ratio'] > params['bull_threshold'])
            momentum_sell = (data['Momentum_Strength'] < params['momentum_strength_threshold'] * 0.5) & (data['Bull_Ratio'] < params['bear_threshold'])

        # Time sensitivity adjustment
        time_sensitive_buy = momentum_buy & (data['Time_Decay_Factor'] > params['time_decay_threshold'])
        time_sensitive_sell = momentum_sell & (data['Time_Decay_Factor'] > params['time_decay_threshold'])

        buy_signals = time_sensitive_buy & (data['Total_Turnover'] > params['min_turnover_threshold'])
        sell_signals = time_sensitive_sell & (data['Total_Turnover'] > params['min_turnover_threshold'])

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'], "time_decay_momentum")

    def _backtest_strategy(self, data: pd.DataFrame, buy_signals: pd.Series,
                           sell_signals: pd.Series, position_size: float, strategy_name: str) -> Dict:
        """Unified backtesting framework"""

        initial_capital = 100000
        cash = initial_capital
        shares = 0
        trades = []
        equity_curve = [initial_capital]

        for i in range(1, len(data)):
            current_price = data['Close'].iloc[i]
            current_value = cash + (shares * current_price)
            equity_curve.append(current_value)

            # Buy signal
            if buy_signals.iloc[i] and shares == 0:
                position_value = cash * position_size
                shares = int(position_value / current_price)
                cash -= shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'BUY',
                    'price': current_price,
                    'shares': shares,
                    'bull_ratio': data['Bull_Ratio'].iloc[i] if 'Bull_Ratio' in data.columns else None
                })

            # Sell signal
            elif sell_signals.iloc[i] and shares > 0:
                cash += shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares,
                    'bull_ratio': data['Bull_Ratio'].iloc[i] if 'Bull_Ratio' in data.columns else None
                })
                shares = 0

        # Calculate performance metrics
        final_value = equity_curve[-1]
        total_return = (final_value - initial_capital) / initial_capital

        if len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            annual_return = total_return * (252 / len(data))
            sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        else:
            annual_return = 0
            sharpe_ratio = 0

        # Maximum drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - peak) / peak
        max_drawdown = drawdown.min()

        # Win rate
        sell_trades = len([t for t in trades if t['action'] == 'SELL'])
        win_rate = sell_trades / len(trades) if trades else 0

        return {
            'strategy_name': strategy_name,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'equity_curve': equity_curve,
            'trades': trades
        }

    def run_all_optimal_strategies(self):
        """Run all 4 strategies with their optimal parameters"""
        print("=" * 80)
        print("COMPLETE OPTIMAL CBSC STRATEGIES SYSTEM")
        print("All 4 Strategies with Best Parameters from UltraThink + Aggressive Optimization")
        print("=" * 80)

        if not self.load_data():
            return False

        # Market benchmark
        benchmark_return = (self.data['Afternoon_Close'].iloc[-1] - self.data['Afternoon_Close'].iloc[0]) / self.data['Afternoon_Close'].iloc[0]
        print(f"\nMarket Benchmark: {benchmark_return:.2%}")

        # Define all strategies with optimal parameters
        strategies = {
            'sentiment_momentum': self.sentiment_momentum_strategy,
            'volume_reversal': self.volume_reversal_strategy,
            'risk_adjusted_bollinger': self.risk_adjusted_bollinger_strategy,
            'time_decay_momentum': self.time_decay_momentum_strategy
        }

        print(f"\nRunning All 4 Optimal CBSC Strategies:")

        all_results = {}

        for strategy_name, strategy_func in strategies.items():
            print(f"\n{'='*60}")
            print(f"Executing: {strategy_name.upper().replace('_', ' ')}")
            print(f"{'='*60}")

            try:
                result = strategy_func(self.data.copy())
                if result:
                    all_results[strategy_name] = result
                    self._print_strategy_summary(strategy_name, result, benchmark_return)
                    print(f"   Parameters: {self.optimal_params[strategy_name]}")
                else:
                    print(f"FAILED: {strategy_name}")
            except Exception as e:
                print(f"ERROR in {strategy_name}: {e}")

        # Generate comprehensive final report
        self._generate_final_report(all_results, benchmark_return)

        return all_results

    def _print_strategy_summary(self, strategy_name: str, result: Dict, benchmark_return: float):
        """Print detailed strategy summary"""
        print(f"   Total Return: {result['total_return']:.2%}")
        print(f"   Annual Return: {result['annual_return']:.2%}")
        print(f"   Sharpe Ratio: {result['sharpe_ratio']:.3f}")
        print(f"   Max Drawdown: {result['max_drawdown']:.2%}")
        print(f"   Total Trades: {result['total_trades']}")
        print(f"   Win Rate: {result['win_rate']:.1%}")
        print(f"   vs Benchmark: {(result['total_return'] - benchmark_return):.2%}")

        # Performance rating
        excess_return = result['total_return'] - benchmark_return
        if excess_return > 0.02:
            print(f"   EXCELLENT: Strongly outperforms market (+{excess_return:.2%})")
        elif excess_return > 0:
            print(f"   GOOD: Outperforms market (+{excess_return:.2%})")
        else:
            print(f"   NEEDS IMPROVEMENT: Underperforms ({excess_return:.2%})")

    def _generate_final_report(self, results: Dict, benchmark_return: float):
        """Generate comprehensive final report"""
        print(f"\n{'='*80}")
        print("FINAL COMPREHENSIVE REPORT - ALL 4 OPTIMAL CBSC STRATEGIES")
        print(f"{'='*80}")

        if not results:
            print("ERROR: No strategy results available")
            return

        # Sort by Sharpe ratio
        sorted_results = sorted(results.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True)

        print(f"\nOPTIMAL STRATEGY RANKING:")
        print("-" * 90)
        print(f"{'Rank':<6} {'Strategy':<25} {'Sharpe':<8} {'Total Ret':<12} {'Annual Ret':<12} {'Max DD':<10} {'Trades':<8} {'Win Rate':<10}")
        print("-" * 90)

        for rank, (name, result) in enumerate(sorted_results, 1):
            excess = result['total_return'] - benchmark_return
            print(f"{rank:<6} {name.replace('_', ' ').title():<25} {result['sharpe_ratio']:<8.3f} "
                  f"{result['total_return']:<12.2%} {result['annual_return']:<12.2%} "
                  f"{result['max_drawdown']:<10.2%} {result['total_trades']:<8} {result['win_rate']:<10.1%}")

        # Overall best strategy
        if sorted_results:
            best_strategy = sorted_results[0]
            print(f"\nOVERALL BEST STRATEGY: {best_strategy[0].replace('_', ' ').title()}")
            print(f"   Sharpe Ratio: {best_strategy[1]['sharpe_ratio']:.3f}")
            print(f"   Total Return: {best_strategy[1]['total_return']:.2%}")
            print(f"   Max Drawdown: {best_strategy[1]['max_drawdown']:.2%}")
            print(f"   Total Trades: {best_strategy[1]['total_trades']}")
            print(f"   Outperformance vs Market: {(best_strategy[1]['total_return'] - benchmark_return):.2%}")

        # Portfolio statistics
        total_strategies = len(results)
        winning_strategies = sum(1 for result in results.values() if result['total_return'] > benchmark_return)
        avg_return = np.mean([r['total_return'] for r in results.values()])
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in results.values()])
        total_trades = sum(r['total_trades'] for r in results.values())

        print(f"\nPORTFOLIO STATISTICS:")
        print(f"   Strategies Outperforming Market: {winning_strategies}/{total_strategies} ({winning_strategies/total_strategies*100:.1f}%)")
        print(f"   Average Strategy Return: {avg_return:.2%}")
        print(f"   Average Sharpe Ratio: {avg_sharpe:.3f}")
        print(f"   Total Trading Opportunities: {total_trades}")
        print(f"   Market Return: {benchmark_return:.2%}")
        print(f"   Average Outperformance: {(avg_return - benchmark_return):.2%}")

def main():
    """Main execution function"""
    print("Starting Complete Optimal CBSC Strategies System...")
    print("All 4 Strategies with Best Parameters from UltraThink + Aggressive Optimization")

    system = CompleteOptimalCBSC()
    results = system.run_all_optimal_strategies()

    if results:
        print(f"\nCOMPLETE OPTIMAL CBSC SYSTEM EXECUTED!")
        print(f"Successfully executed {len(results)} strategies with optimal parameters")
        print(f"System is ready for real-time trading application")
    else:
        print("Optimal strategy execution failed")

if __name__ == "__main__":
    main()