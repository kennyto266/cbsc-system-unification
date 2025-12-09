#!/usr/bin/env python3
"""
CBSC Parameter Optimizer - Complete Parameter Search and Backtesting System
找出最佳進場參數的完整回測系統

Author: CBSC Strategy Team
Date: 2025-12-04
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from typing import Dict, List, Tuple, Any
from itertools import product
import json
from datetime import datetime

warnings.filterwarnings('ignore')

class CBSCParameterOptimizer:
    """
    Complete CBSC parameter optimization system
    """

    def __init__(self):
        self.data = None
        self.optimization_results = {}
        self.best_parameters = {}

    def load_real_data(self):
        """Load real CBSC data"""
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

            # Add required columns
            self.data['Close'] = self.data['Afternoon_Close']
            self.data['Total_Turnover'] = self.data['Bull_Turnover_HKD'] + self.data['Bear_Turnover_HKD']

            print(f"SUCCESS: Loaded {len(self.data)} days of real CBSC data")
            return True

        except Exception as e:
            print(f"ERROR: Data loading failed - {e}")
            return False

    def define_parameter_space(self) -> Dict[str, Dict]:
        """
        Define comprehensive parameter space for all 4 CBSC strategies
        """
        parameter_space = {
            'sentiment_momentum': {
                'sentiment_short_window': [3, 5, 7, 10],
                'sentiment_long_window': [10, 15, 20, 25],
                'momentum_threshold': [0.05, 0.1, 0.15, 0.2],
                'volume_multiplier': [1.2, 1.3, 1.5, 1.8, 2.0],
                'volume_ma_window': [3, 5, 7, 10],
                'min_volume_threshold': [50000000, 100000000, 200000000],
                'position_size': [0.1, 0.2, 0.25, 0.3]
            },
            'volume_reversal': {
                'ratio_short_window': [3, 5, 7, 10],
                'ratio_long_window': [15, 20, 25, 30],
                'volume_spike_multiplier': [1.3, 1.5, 1.8, 2.0],
                'volume_spike_window': [5, 7, 10, 15],
                'extreme_bull_threshold': [0.65, 0.7, 0.75, 0.8],
                'extreme_bear_threshold': [0.2, 0.25, 0.3, 0.35],
                'position_size': [0.15, 0.2, 0.25, 0.35]
            },
            'risk_adjusted_bollinger': {
                'rsi_period': [7, 10, 14, 21],
                'rsi_overbought': [65, 70, 75, 80],
                'rsi_oversold': [20, 25, 30, 35],
                'bb_period': [10, 15, 20, 25],
                'bb_std_multiplier': [1.5, 2.0, 2.5],
                'risk_threshold_bull': [0.3, 0.4, 0.5],
                'risk_threshold_bear': [0.3, 0.4, 0.5],
                'position_size': [0.1, 0.15, 0.2, 0.25]
            },
            'time_decay_momentum': {
                'decay_half_life': [30, 45, 60, 90],
                'momentum_strength_threshold': [0.03, 0.05, 0.07, 0.1],
                'bull_threshold': [0.55, 0.6, 0.65, 0.7],
                'bear_threshold': [0.3, 0.35, 0.4, 0.45],
                'time_decay_threshold': [0.7, 0.8, 0.85, 0.9],
                'min_turnover_threshold': [300000, 500000, 1000000, 2000000],
                'position_size': [0.1, 0.15, 0.2, 0.25, 0.3]
            }
        }

        return parameter_space

    def sentiment_momentum_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Sentiment momentum strategy with custom parameters"""

        # Calculate sentiment momentum
        data['Sentiment_MA_Short'] = data['Bull_Ratio'].rolling(params['sentiment_short_window'], min_periods=3).mean()
        data['Sentiment_MA_Long'] = data['Bull_Ratio'].rolling(params['sentiment_long_window'], min_periods=5).mean()
        data['Sentiment_Momentum'] = data['Sentiment_MA_Short'] - data['Sentiment_MA_Long']

        # Volume indicators
        data['Bull_Volume_MA'] = data['Bull_Turnover_HKD'].rolling(params['volume_ma_window'], min_periods=3).mean()
        data['Total_Volume_MA'] = data['Total_Turnover'].rolling(params['volume_ma_window'], min_periods=3).mean()

        # Signal generation
        momentum_signal = data['Sentiment_Momentum'] > params['momentum_threshold']
        volume_surge = data['Bull_Turnover_HKD'] > (data['Bull_Volume_MA'] * params['volume_multiplier'])
        volume_confirmation = volume_surge & (data['Total_Volume_MA'] > params['min_volume_threshold'])

        buy_signals = momentum_signal & volume_confirmation
        sell_signals = (data['Sentiment_Momentum'] < -params['momentum_threshold']) & volume_surge

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'])

    def volume_reversal_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Volume reversal strategy with custom parameters"""

        # Calculate volume ratios
        data['Ratio_Short'] = data['Bull_Ratio'].rolling(params['ratio_short_window'], min_periods=3).mean()
        data['Ratio_Long'] = data['Bull_Ratio'].rolling(params['ratio_long_window'], min_periods=5).mean()

        # Volume spike detection
        data['Volume_Spike'] = data['Total_Turnover'] > (data['Total_Turnover'].rolling(params['volume_spike_window'], min_periods=5).mean() * params['volume_spike_multiplier'])

        # Extreme ratio detection
        extreme_bull = data['Ratio_Short'] > params['extreme_bull_threshold']
        extreme_bear = data['Ratio_Short'] < params['extreme_bear_threshold']

        # Reversal signals
        ratio_turning_bull = (data['Ratio_Short'] > data['Ratio_Long']) & extreme_bear
        ratio_turning_bear = (data['Ratio_Short'] < data['Ratio_Long']) & extreme_bull

        buy_signals = ratio_turning_bull & data['Volume_Spike']
        sell_signals = ratio_turning_bear & data['Volume_Spike']

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'])

    def risk_adjusted_bollinger_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Risk-adjusted Bollinger strategy with custom parameters"""

        # RSI calculation
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(params['rsi_period'], min_periods=7).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(params['rsi_period'], min_periods=7).mean()
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

        # Signal generation
        rsi_buy = data['RSI'] < params['rsi_oversold']
        rsi_sell = data['RSI'] > params['rsi_overbought']
        bb_buy = (data['Close'] < data['BB_Lower']) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
        bb_sell = (data['Close'] > data['BB_Upper']) & (data['Call_Risk_Bear'] < params['risk_threshold_bear'])

        buy_signals = (rsi_buy | bb_buy) & (data['Call_Risk_Bull'] < 0.5)
        sell_signals = (rsi_sell | bb_sell) & (data['Call_Risk_Bear'] < 0.5)

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'])

    def time_decay_momentum_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """Time decay momentum strategy with custom parameters"""

        # Calculate time decay factor
        days_to_expiry = np.arange(len(data))
        data['Time_Decay_Factor'] = np.exp(-days_to_expiry / params['decay_half_life'])
        data['Adjusted_Price'] = data['Close'] * (1 + data['Time_Decay_Factor'] * 0.1)

        # Momentum strength adjustment
        data['Momentum_Strength'] = data['Bull_Ratio'] * data['Time_Decay_Factor']

        # Time decay momentum signals
        momentum_buy = (data['Momentum_Strength'] > params['momentum_strength_threshold']) & (data['Bull_Ratio'] > params['bull_threshold'])
        momentum_sell = (data['Momentum_Strength'] < params['momentum_strength_threshold']) & (data['Bull_Ratio'] < params['bear_threshold'])

        # Time sensitivity adjustment
        time_sensitive_buy = momentum_buy & (data['Time_Decay_Factor'] > params['time_decay_threshold'])
        time_sensitive_sell = momentum_sell & (data['Time_Decay_Factor'] > params['time_decay_threshold'])

        buy_signals = time_sensitive_buy & (data['Total_Turnover'] > params['min_turnover_threshold'])
        sell_signals = time_sensitive_sell & (data['Total_Turnover'] > params['min_turnover_threshold'])

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'])

    def _backtest_strategy(self, data: pd.DataFrame, buy_signals: pd.Series,
                           sell_signals: pd.Series, position_size: float) -> Dict:
        """Unified backtesting framework with custom position size"""

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
                    'shares': shares
                })

            # Sell signal
            elif sell_signals.iloc[i] and shares > 0:
                cash += shares * current_price
                trades.append({
                    'date': data['Date'].iloc[i],
                    'action': 'SELL',
                    'price': current_price,
                    'shares': shares
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
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'equity_curve': equity_curve,
            'trades': trades
        }

    def optimize_single_strategy(self, strategy_name: str, strategy_func,
                                 parameter_space: Dict, max_combinations: int = 100) -> Dict:
        """
        Optimize a single strategy using grid search
        """
        print(f"\n{'='*60}")
        print(f"Optimizing Strategy: {strategy_name}")
        print(f"{'='*60}")

        # Generate parameter combinations
        param_names = list(parameter_space.keys())
        param_values = list(parameter_space.values())

        # Limit combinations to avoid excessive computation
        total_combinations = np.prod([len(values) for values in param_values])
        if total_combinations > max_combinations:
            print(f"Total combinations: {total_combinations:,} - limiting to {max_combinations}")
            # Random sampling for large parameter spaces
            combinations = []
            import random
            for _ in range(min(max_combinations, total_combinations)):
                combo = {}
                for name, values in zip(param_names, param_values):
                    combo[name] = random.choice(values)
                combinations.append(combo)
        else:
            combinations = list(product(*param_values))
            combinations = [dict(zip(param_names, combo)) for combo in combinations]
            print(f"Testing all {len(combinations)} parameter combinations")

        best_result = None
        best_sharpe = -float('inf')
        tested_combinations = 0

        for i, params in enumerate(combinations):
            tested_combinations += 1

            if tested_combinations % 20 == 0:
                print(f"Progress: {tested_combinations}/{len(combinations)} ({tested_combinations/len(combinations)*100:.1f}%)")

            try:
                result = strategy_func(self.data.copy(), params)
                result['parameters'] = params

                # Evaluate based on multiple criteria
                score = self._calculate_composite_score(result)

                if score > best_sharpe:
                    best_sharpe = score
                    best_result = result

            except Exception as e:
                continue  # Skip invalid parameter combinations

        print(f"\nBest result for {strategy_name}:")
        print(f"   Composite Score: {best_sharpe:.4f}")
        print(f"   Sharpe Ratio: {best_result['sharpe_ratio']:.4f}")
        print(f"   Total Return: {best_result['total_return']:.2%}")
        print(f"   Max Drawdown: {best_result['max_drawdown']:.2%}")
        print(f"   Total Trades: {best_result['total_trades']}")
        print(f"   Win Rate: {best_result['win_rate']:.1%}")

        print(f"\nBest Parameters:")
        for param, value in best_result['parameters'].items():
            print(f"   {param}: {value}")

        return best_result

    def _calculate_composite_score(self, result: Dict) -> float:
        """
        Calculate composite score for parameter evaluation
        Considers Sharpe ratio, returns, drawdown, and trade frequency
        """
        # Base score from Sharpe ratio
        sharpe_score = result['sharpe_ratio']

        # Return bonus (positive returns get bonus)
        return_bonus = max(0, result['total_return']) * 10

        # Drawdown penalty (lower drawdown is better)
        drawdown_penalty = max(0, result['max_drawdown']) * -5

        # Trade frequency bonus (reasonable number of trades is preferred)
        if 5 <= result['total_trades'] <= 20:
            trade_bonus = 0.5
        elif result['total_trades'] > 0:
            trade_bonus = 0.2
        else:
            trade_bonus = -0.5

        composite_score = sharpe_score + return_bonus + drawdown_penalty + trade_bonus

        return composite_score

    def run_complete_optimization(self):
        """
        Run complete optimization for all 4 CBSC strategies
        """
        print("=" * 80)
        print("COMPLETE CBSC PARAMETER OPTIMIZATION SYSTEM")
        print("Finding Best Entry Parameters for All Strategies")
        print("=" * 80)

        if not self.load_real_data():
            return False

        # Market benchmark
        benchmark_return = (self.data['Afternoon_Close'].iloc[-1] - self.data['Afternoon_Close'].iloc[0]) / self.data['Afternoon_Close'].iloc[0]
        print(f"\nMarket Benchmark: {benchmark_return:.2%}")

        # Define strategies
        strategies = {
            'sentiment_momentum': self.sentiment_momentum_strategy,
            'volume_reversal': self.volume_reversal_strategy,
            'risk_adjusted_bollinger': self.risk_adjusted_bollinger_strategy,
            'time_decay_momentum': self.time_decay_momentum_strategy
        }

        # Get parameter space
        parameter_space = self.define_parameter_space()

        # Optimize each strategy
        all_results = {}

        for strategy_name, strategy_func in strategies.items():
            try:
                result = self.optimize_single_strategy(
                    strategy_name,
                    strategy_func,
                    parameter_space[strategy_name]
                )
                if result:
                    all_results[strategy_name] = result
            except Exception as e:
                print(f"ERROR optimizing {strategy_name}: {e}")

        # Generate comprehensive report
        self._generate_optimization_report(all_results, benchmark_return)

        # Save results
        self._save_optimization_results(all_results)

        return all_results

    def _generate_optimization_report(self, results: Dict, benchmark_return: float):
        """Generate comprehensive optimization report"""

        print(f"\n{'='*80}")
        print("COMPREHENSIVE OPTIMIZATION REPORT")
        print(f"{'='*80}")

        if not results:
            print("ERROR: No optimization results available")
            return

        # Sort by composite score (using our composite score calculation)
        sorted_results = sorted(results.items(),
                              key=lambda x: self._calculate_composite_score(x[1]),
                              reverse=True)

        print(f"\nOPTIMIZED STRATEGY RANKING:")
        print("-" * 80)
        print(f"{'Strategy':<25} {'Sharpe':<8} {'Return':<10} {'Max DD':<10} {'Trades':<8} {'Win Rate':<10} {'Score':<8}")
        print("-" * 80)

        for rank, (name, result) in enumerate(sorted_results, 1):
            score = self._calculate_composite_score(result)
            print(f"{rank}. {name:<25} {result['sharpe_ratio']:<8.3f} "
                  f"{result['total_return']:<10.2%} {result['max_drawdown']:<10.2%} "
                  f"{result['total_trades']:<8} {result['win_rate']:<10.1%} {score:<8.3f}")

        # Overall best strategy
        if sorted_results:
            best_strategy = sorted_results[0]
            print(f"\nOVERALL BEST STRATEGY: {best_strategy[0]}")
            print(f"   Composite Score: {self._calculate_composite_score(best_strategy[1]):.4f}")
            print(f"   Sharpe Ratio: {best_strategy[1]['sharpe_ratio']:.4f}")
            print(f"   Total Return: {best_strategy[1]['total_return']:.2%}")
            print(f"   Max Drawdown: {best_strategy[1]['max_drawdown']:.2%}")
            print(f"   Outperformance vs Market: {(best_strategy[1]['total_return'] - benchmark_return):.2%}")

        # Parameter insights
        print(f"\nKEY PARAMETER INSIGHTS:")
        for name, result in results.items():
            print(f"\n{name}:")
            for param, value in result['parameters'].items():
                print(f"   {param}: {value}")

    def _save_optimization_results(self, results: Dict):
        """Save optimization results to file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cbsc_optimization_results_{timestamp}.json"

        # Prepare results for JSON serialization
        json_results = {}
        for strategy_name, result in results.items():
            json_results[strategy_name] = {
                'total_return': result['total_return'],
                'annual_return': result['annual_return'],
                'sharpe_ratio': result['sharpe_ratio'],
                'max_drawdown': result['max_drawdown'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate'],
                'parameters': result['parameters'],
                'composite_score': self._calculate_composite_score(result)
            }

        try:
            with open(filename, 'w') as f:
                json.dump(json_results, f, indent=2)
            print(f"\nOptimization results saved to: {filename}")
        except Exception as e:
            print(f"ERROR saving results: {e}")

def main():
    """Main execution function"""
    print("Starting Complete CBSC Parameter Optimization...")
    print("Finding Best Entry Parameters for All 4 Strategies")

    optimizer = CBSCParameterOptimizer()
    results = optimizer.run_complete_optimization()

    if results:
        print(f"\nOPTIMIZATION COMPLETE!")
        print(f"Successfully optimized {len(results)} CBSC strategies")
        print(f"Results have been saved to JSON file")
    else:
        print("ERROR: Parameter optimization failed")

if __name__ == "__main__":
    main()