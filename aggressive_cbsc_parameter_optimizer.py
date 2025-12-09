#!/usr/bin/env python3
"""
Aggressive CBSC Parameter Optimizer - 激進參數優化
針對其他3種策略進行激進調整，增加交易機會和獲利潛力

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
import random

warnings.filterwarnings('ignore')

class AggressiveCBSCOptimizer:
    """
    Aggressive parameter optimization for CBSC strategies
    """

    def __init__(self):
        self.data = None
        self.optimization_results = {}

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

    def define_aggressive_parameter_space(self) -> Dict[str, Dict]:
        """
        Define AGGRESSIVE parameter space for 3 underperforming strategies
        目標：大幅增加交易機會
        """
        parameter_space = {
            'volume_reversal': {
                # 更激進的極端閾值 - 更容易觸發
                'ratio_short_window': [3, 5, 7],                    # 更短週期
                'ratio_long_window': [8, 10, 12, 15],               # 大幅縮短長週期
                'volume_spike_multiplier': [1.1, 1.2, 1.3],         # 降低成交量要求
                'volume_spike_window': [3, 5, 7],                   # 更短時間窗口
                'extreme_bull_threshold': [0.55, 0.6, 0.65],       # 降低極端閾值
                'extreme_bear_threshold': [0.35, 0.4, 0.45],       # 降低極端閾值
                'position_size': [0.2, 0.25, 0.3, 0.4],            # 更大倉位
                'min_trades_target': [3, 5, 7]                      # 目標交易次數
            },
            'risk_adjusted_bollinger': {
                # 更激進的進出場點
                'rsi_period': [5, 7, 10],                          # 更短RSI週期
                'rsi_overbought': [60, 65, 70, 75],               # 降低超買閾值
                'rsi_oversold': [25, 30, 35, 40],                 # 提高超賣閾值
                'bb_period': [10, 12, 15],                         # 更短布林週期
                'bb_std_multiplier': [1.2, 1.5, 1.8, 2.0],        # 更緊的布林帶
                'risk_threshold_bull': [0.6, 0.7, 0.8],            # 放寬風險閾值
                'risk_threshold_bear': [0.6, 0.7, 0.8],            # 放寬風險閾值
                'position_size': [0.15, 0.2, 0.25, 0.3],            # 更大倉位
                'entry_mode': ['aggressive', 'moderate', 'balanced'] # 進場模式
            },
            'time_decay_momentum': {
                # 更激進的時間衰減設定
                'decay_half_life': [15, 20, 30, 45],                # 更短的半衰期
                'momentum_strength_threshold': [0.01, 0.02, 0.03],  # 降低動量門檻
                'bull_threshold': [0.5, 0.52, 0.55],               # 降低看漲門檻
                'bear_threshold': [0.45, 0.48, 0.5],               # 降低看跌門檻
                'time_decay_threshold': [0.5, 0.6, 0.7],            # 降低時間衰減門檻
                'min_turnover_threshold': [100000, 500000, 1000000], # 大幅降低成交量要求
                'position_size': [0.2, 0.25, 0.3, 0.35],           # 更大倉位
                'momentum_mode': ['sensitive', 'normal', 'stable']   # 動量敏感度
            }
        }

        return parameter_space

    def aggressive_volume_reversal_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """激進成交量反轉策略"""

        # Calculate volume ratios
        data['Ratio_Short'] = data['Bull_Ratio'].rolling(params['ratio_short_window'], min_periods=2).mean()
        data['Ratio_Long'] = data['Bull_Ratio'].rolling(params['ratio_long_window'], min_periods=3).mean()

        # Volume spike detection - 降低要求
        data['Volume_Spike'] = data['Total_Turnover'] > (data['Total_Turnover'].rolling(params['volume_spike_window'], min_periods=3).mean() * params['volume_spike_multiplier'])

        # Extreme ratio detection - 更容易觸發
        extreme_bull = data['Ratio_Short'] > params['extreme_bull_threshold']
        extreme_bear = data['Ratio_Short'] < params['extreme_bear_threshold']

        # 多重反轉信號 - 增加交易機會
        ratio_turning_bull = (data['Ratio_Short'] > data['Ratio_Long']) & extreme_bear
        ratio_turning_bear = (data['Ratio_Short'] < data['Ratio_Long']) & extreme_bull

        # 添加額外的反轉信號
        momentum_reversal_bull = (data['Ratio_Short'].diff() > 0.05) & extreme_bear  # 動量反轉
        momentum_reversal_bear = (data['Ratio_Short'].diff() < -0.05) & extreme_bull

        buy_signals = (ratio_turning_bull | momentum_reversal_bull) & data['Volume_Spike']
        sell_signals = (ratio_turning_bear | momentum_reversal_bear) & data['Volume_Spike']

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'])

    def aggressive_risk_adjusted_bollinger_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """激進風險調整布林帶策略"""

        # RSI calculation - 更短週期
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(params['rsi_period'], min_periods=3).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(params['rsi_period'], min_periods=3).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))

        # Bollinger bands - 更緊的帶
        data['BB_Middle'] = data['Close'].rolling(params['bb_period']).mean()
        data['BB_Std'] = data['Close'].rolling(params['bb_period']).std()
        data['BB_Upper'] = data['BB_Middle'] + (data['BB_Std'] * params['bb_std_multiplier'])
        data['BB_Lower'] = data['BB_Middle'] - (data['BB_Std'] * params['bb_std_multiplier'])

        # Risk assessment - 更寬鬆的風險閾值
        data['Call_Risk_Bull'] = np.maximum(0, (data['Bull_Ratio'] - 0.5) * 2)
        data['Call_Risk_Bear'] = np.maximum(0, (0.5 - data['Bull_Ratio']) * 2)

        # 更激進的信號生成
        rsi_buy = data['RSI'] < params['rsi_oversold']
        rsi_sell = data['RSI'] > params['rsi_overbought']
        bb_buy = (data['Close'] < data['BB_Lower']) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
        bb_sell = (data['Close'] > data['BB_Upper']) & (data['Call_Risk_Bear'] < params['risk_threshold_bear'])

        # 根據進場模式調整
        if params['entry_mode'] == 'aggressive':
            # 激進模式：更多交易機會
            buy_signals = (rsi_buy | bb_buy) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
            sell_signals = (rsi_sell | bb_sell) | (data['RSI'] > 55)  # 更早賣出
        elif params['entry_mode'] == 'moderate':
            # 適度模式：平衡
            buy_signals = (rsi_buy | bb_buy) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
            sell_signals = rsi_sell | bb_sell
        else:  # balanced
            # 平衡模式：保守一點
            buy_signals = (rsi_buy & bb_buy) & (data['Call_Risk_Bull'] < params['risk_threshold_bull'])
            sell_signals = (rsi_sell | bb_sell) & (data['Call_Risk_Bear'] < params['risk_threshold_bear'])

        return self._backtest_strategy(data, buy_signals, sell_signals, params['position_size'])

    def aggressive_time_decay_momentum_strategy(self, data: pd.DataFrame, params: Dict) -> Dict:
        """激進時衰減動量策略"""

        # Calculate time decay factor - 更快的衰減
        days_to_expiry = np.arange(len(data))
        data['Time_Decay_Factor'] = np.exp(-days_to_expiry / params['decay_half_life'])
        data['Adjusted_Price'] = data['Close'] * (1 + data['Time_Decay_Factor'] * 0.1)

        # Momentum strength adjustment - 更敏感的動量
        data['Momentum_Strength'] = data['Bull_Ratio'] * data['Time_Decay_Factor']

        # 根據動量模式調整
        if params['momentum_mode'] == 'sensitive':
            # 高敏感模式：更多信號
            momentum_buy = (data['Momentum_Strength'] > params['momentum_strength_threshold']) & (data['Bull_Ratio'] > params['bull_threshold'])
            momentum_sell = (data['Momentum_Strength'] < params['momentum_strength_threshold']) | (data['Bull_Ratio'] < params['bear_threshold'])
        elif params['momentum_mode'] == 'normal':
            # 正常模式
            momentum_buy = (data['Momentum_Strength'] > params['momentum_strength_threshold']) & (data['Bull_Ratio'] > params['bull_threshold'])
            momentum_sell = (data['Momentum_Strength'] < params['momentum_strength_threshold']) & (data['Bull_Ratio'] < params['bear_threshold'])
        else:  # stable
            # 穩定模式：更嚴格的條件
            momentum_buy = (data['Momentum_Strength'] > params['momentum_strength_threshold'] * 1.5) & (data['Bull_Ratio'] > params['bull_threshold'])
            momentum_sell = (data['Momentum_Strength'] < params['momentum_strength_threshold'] * 0.5) & (data['Bull_Ratio'] < params['bear_threshold'])

        # Time sensitivity adjustment - 降低門檻
        time_sensitive_buy = momentum_buy & (data['Time_Decay_Factor'] > params['time_decay_threshold'])
        time_sensitive_sell = momentum_sell & (data['Time_Decay_Factor'] > params['time_decay_threshold'])

        # 大幅降低成交量要求
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

    def calculate_aggressive_score(self, result: Dict) -> float:
        """
        Calculate aggressive score focused on trading opportunities and returns
        """
        # Base score from Sharpe ratio
        sharpe_score = result['sharpe_ratio']

        # Strong return bonus (positive returns get higher bonus)
        return_bonus = max(0, result['total_return']) * 20  # 提高回報獎勵

        # Drawdown penalty (lower drawdown is better)
        drawdown_penalty = max(0, result['max_drawdown']) * -3  # 降低回撤懲罰

        # Trading frequency bonus (更多交易機會是目標)
        if result['total_trades'] >= 5:
            trade_bonus = 1.0
        elif result['total_trades'] >= 3:
            trade_bonus = 0.5
        elif result['total_trades'] > 0:
            trade_bonus = 0.2
        else:
            trade_bonus = -2.0  # 無交易嚴重懲罰

        # Win rate bonus
        if result['win_rate'] > 0.5:
            win_rate_bonus = 0.5
        elif result['win_rate'] > 0:
            win_rate_bonus = 0.2
        else:
            win_rate_bonus = -0.5

        composite_score = sharpe_score + return_bonus + drawdown_penalty + trade_bonus + win_rate_bonus

        return composite_score

    def optimize_aggressive_strategy(self, strategy_name: str, strategy_func,
                                   parameter_space: Dict, max_combinations: int = 200) -> Dict:
        """
        Optimize strategy with aggressive parameters
        """
        print(f"\n{'='*70}")
        print(f"AGGRESSIVE OPTIMIZATION: {strategy_name}")
        print(f"{'='*70}")

        # Generate parameter combinations
        param_names = [k for k in parameter_space.keys() if k != 'min_trades_target']
        param_values = [v for k, v in parameter_space.items() if k != 'min_trades_target']

        # Increase combinations for aggressive search
        total_combinations = np.prod([len(values) for values in param_values])

        if total_combinations > max_combinations:
            print(f"Total combinations: {total_combinations:,} - sampling {max_combinations}")
            combinations = []
            for _ in range(max_combinations):
                combo = {}
                for name, values in zip(param_names, param_values):
                    combo[name] = random.choice(values)
                combinations.append(combo)
        else:
            combinations = list(product(*param_values))
            combinations = [dict(zip(param_names, combo)) for combo in combinations]
            print(f"Testing all {len(combinations)} parameter combinations")

        best_result = None
        best_score = -float('inf')
        tested_combinations = 0

        for i, params in enumerate(combinations):
            tested_combinations += 1

            if tested_combinations % 20 == 0:
                print(f"Progress: {tested_combinations}/{len(combinations)} ({tested_combinations/len(combinations)*100:.1f}%)")

            try:
                result = strategy_func(self.data.copy(), params)
                result['parameters'] = params

                # Evaluate using aggressive score
                score = self.calculate_aggressive_score(result)

                if score > best_score:
                    best_score = score
                    best_result = result

            except Exception as e:
                continue  # Skip invalid parameter combinations

        print(f"\nBest aggressive result for {strategy_name}:")
        print(f"   Aggressive Score: {best_score:.4f}")
        print(f"   Sharpe Ratio: {best_result['sharpe_ratio']:.4f}")
        print(f"   Total Return: {best_result['total_return']:.2%}")
        print(f"   Max Drawdown: {best_result['max_drawdown']:.2%}")
        print(f"   Total Trades: {best_result['total_trades']}")
        print(f"   Win Rate: {best_result['win_rate']:.1%}")

        print(f"\nBest Aggressive Parameters:")
        for param, value in best_result['parameters'].items():
            print(f"   {param}: {value}")

        return best_result

    def run_aggressive_optimization(self):
        """
        Run aggressive optimization for all 3 underperforming strategies
        """
        print("=" * 80)
        print("AGGRESSIVE CBSC PARAMETER OPTIMIZATION")
        print("Optimizing 3 Underperforming Strategies with Aggressive Parameters")
        print("=" * 80)

        if not self.load_real_data():
            return False

        # Market benchmark
        benchmark_return = (self.data['Afternoon_Close'].iloc[-1] - self.data['Afternoon_Close'].iloc[0]) / self.data['Afternoon_Close'].iloc[0]
        print(f"\nMarket Benchmark: {benchmark_return:.2%}")

        # Define aggressive strategies
        strategies = {
            'volume_reversal': self.aggressive_volume_reversal_strategy,
            'risk_adjusted_bollinger': self.aggressive_risk_adjusted_bollinger_strategy,
            'time_decay_momentum': self.aggressive_time_decay_momentum_strategy
        }

        # Get aggressive parameter space
        parameter_space = self.define_aggressive_parameter_space()

        # Optimize each strategy aggressively
        all_results = {}

        for strategy_name, strategy_func in strategies.items():
            try:
                result = self.optimize_aggressive_strategy(
                    strategy_name,
                    strategy_func,
                    parameter_space[strategy_name]
                )
                if result:
                    all_results[strategy_name] = result
            except Exception as e:
                print(f"ERROR optimizing {strategy_name}: {e}")

        # Generate comprehensive aggressive report
        self._generate_aggressive_report(all_results, benchmark_return)

        # Save aggressive results
        self._save_aggressive_results(all_results)

        return all_results

    def _generate_aggressive_report(self, results: Dict, benchmark_return: float):
        """Generate comprehensive aggressive optimization report"""

        print(f"\n{'='*80}")
        print("AGGRESSIVE OPTIMIZATION REPORT")
        print("=" * 80)

        if not results:
            print("ERROR: No aggressive optimization results available")
            return

        # Sort by aggressive score
        sorted_results = sorted(results.items(),
                              key=lambda x: self.calculate_aggressive_score(x[1]),
                              reverse=True)

        print(f"\nAGGRESSIVELY OPTIMIZED STRATEGY RANKING:")
        print("-" * 80)
        print(f"{'Strategy':<25} {'Aggressive':<10} {'Sharpe':<8} {'Return':<10} {'Trades':<8} {'Win Rate':<10}")
        print("-" * 80)

        for rank, (name, result) in enumerate(sorted_results, 1):
            score = self.calculate_aggressive_score(result)
            print(f"{rank}. {name:<25} {score:<10.3f} {result['sharpe_ratio']:<8.3f} "
                  f"{result['total_return']:<10.2%} {result['total_trades']:<8} {result['win_rate']:<10.1%}")

        # Overall best aggressive strategy
        if sorted_results:
            best_strategy = sorted_results[0]
            print(f"\nBEST AGGRESSIVE STRATEGY: {best_strategy[0]}")
            print(f"   Aggressive Score: {self.calculate_aggressive_score(best_strategy[1]):.4f}")
            print(f"   Sharpe Ratio: {best_strategy[1]['sharpe_ratio']:.4f}")
            print(f"   Total Return: {best_strategy[1]['total_return']:.2%}")
            print(f"   Max Drawdown: {best_strategy[1]['max_drawdown']:.2%}")
            print(f"   Total Trades: {best_strategy[1]['total_trades']}")
            print(f"   Outperformance vs Market: {(best_strategy[1]['total_return'] - benchmark_return):.2%}")

        # Detailed parameter insights
        print(f"\nAGGRESSIVE PARAMETER INSIGHTS:")
        for name, result in results.items():
            print(f"\n{name}:")
            for param, value in result['parameters'].items():
                print(f"   {param}: {value}")

    def _save_aggressive_results(self, results: Dict):
        """Save aggressive optimization results to file"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"aggressive_cbsc_optimization_results_{timestamp}.json"

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
                'aggressive_score': self.calculate_aggressive_score(result)
            }

        try:
            with open(filename, 'w') as f:
                json.dump(json_results, f, indent=2)
            print(f"\nAggressive optimization results saved to: {filename}")
        except Exception as e:
            print(f"ERROR saving results: {e}")

def main():
    """Main execution function"""
    print("Starting Aggressive CBSC Parameter Optimization...")
    print("Optimizing 3 Underperforming Strategies with Aggressive Parameters")

    optimizer = AggressiveCBSCOptimizer()
    results = optimizer.run_aggressive_optimization()

    if results:
        print(f"\nAGGRESSIVE OPTIMIZATION COMPLETE!")
        print(f"Successfully optimized {len(results)} CBSC strategies")
        print(f"Results have been saved to JSON file")
        print(f"Strategies now have more trading opportunities and profit potential")
    else:
        print("ERROR: Aggressive parameter optimization failed")

if __name__ == "__main__":
    main()