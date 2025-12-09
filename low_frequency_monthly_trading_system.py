#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低頻率月度交易策略系統
設計專門為月度或更低頻率交易的策略
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class LowFrequencyTradingSystem:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.strategies = {}

    def load_real_data(self):
        """加載真實數據"""
        try:
            import glob
            cbsc_files = glob.glob('acquired_data/cbsc_real_data_*.csv')
            if not cbsc_files:
                raise FileNotFoundError("No CBSC data files found")

            data = pd.read_csv(cbsc_files[0], index_col=0, parse_dates=True)
            print(f"[OK] Loaded {len(data)} records")
            return data

        except Exception as e:
            print(f"[ERROR] Failed to load data: {e}")
            return None

    def register_monthly_strategy(self, name, implementation_func, params=None):
        """註冊月度策略"""
        self.strategies[name] = {
            'implementation': implementation_func,
            'params': params or {},
            'name': name
        }
        print(f"[OK] Registered monthly strategy: {name}")

    def implement_monthly_momentum_strategy(self, data, params=None):
        """月度動量策略"""
        params = params or {'lookback_months': 6, 'momentum_threshold': 0.02}

        # 計算月度動量
        monthly_returns = data['HSIF_Close'].resample('M').last().pct_change()
        data['monthly_momentum'] = monthly_returns.rolling(window=params['lookback_months']).mean()

        # 每月初更新信號
        monthly_dates = data.resample('M').first().index
        data['momentum_signal'] = 0

        for date in monthly_dates:
            if date in data.index and not pd.isna(data.loc[date, 'monthly_momentum']):
                momentum = data.loc[date, 'monthly_momentum']
                if momentum > params['momentum_threshold']:
                    data.loc[date:, 'momentum_signal'] = 1  # 買漲動量
                elif momentum < -params['momentum_threshold']:
                    data.loc[date:, 'momentum_signal'] = -1  # 跌跌動量
                else:
                    data.loc[date:, 'momentum_signal'] = 0  # 中性

        return data

    def implement_quarterly_reversal_strategy(self, data, params=None):
        """季度均值回歸策略"""
        params = params or {'lookback_quarters': 8, 'reversal_threshold': 0.15}

        # 計算季度回歸
        quarterly_prices = data['HSIF_Close'].resample('Q').last()
        quarterly_returns = quarterly_prices.pct_change()
        rolling_mean = quarterly_prices.rolling(window=params['lookback_quarters']).mean()

        data['quarterly_mean'] = rolling_mean.reindex(data.index, method='ffill')
        data['quarterly_deviation'] = (data['HSIF_Close'] - data['quarterly_mean']) / data['quarterly_mean']

        # 每季度初檢查回歸信號
        quarterly_dates = data.resample('Q').first().index
        data['reversal_signal'] = 0

        for date in quarterly_dates:
            if date in data.index and not pd.isna(data.loc[date, 'quarterly_deviation']):
                deviation = data.loc[date, 'quarterly_deviation']
                if deviation > params['reversal_threshold']:
                    data.loc[date:, 'reversal_signal'] = -1  # 高估，賣出
                elif deviation < -params['reversal_threshold']:
                    data.loc[date:, 'reversal_signal'] = 1   # 低估，買入
                else:
                    data.loc[date:, 'reversal_signal'] = 0  # 合理區間

        return data

    def implement_seasonal_strategy(self, data, params=None):
        """季節性交易策略"""
        params = params or {'months_to_buy': [1, 4, 7, 10], 'holding_period': 3}  # 每季度初買入

        data['month'] = data.index.month
        data['seasonal_signal'] = 0

        # 基於季節性模式的信號
        for month in params['months_to_buy']:
            # 每個季節月份的第一個交易日發出買入信號
            month_start = data[data['month'] == month]
            if len(month_start) > 0:
                buy_date = month_start.index[0]
                data.loc[buy_date:, 'seasonal_signal'] = 1

                # 持有period個月後賣出
                hold_end = buy_date + pd.DateOffset(months=params['holding_period'])
                if hold_end <= data.index[-1]:
                    data.loc[hold_end:, 'seasonal_signal'] = 0

        return data

    def implement_valuation_based_strategy(self, data, params=None):
        """估值基礎策略"""
        params = params or {'pe_threshold': 15, 'valuation_periods': 12}

        # 基於歷史估值的模擬（實際應用中需要真實的PE、PB等數據）
        # 這裡使用價格趨勢作為估值代理
        price_trend = data['HSIF_Close'].pct_change(params['valuation_periods'] * 20)  # 週期轉換
        valuation_ratio = price_trend.rolling(params['valuation_periods']).mean()

        data['valuation_signal'] = 0
        data['valuation_ratio'] = valuation_ratio.reindex(data.index, method='ffill')

        # 月度更新信號
        monthly_dates = data.resample('M').first().index

        for date in monthly_dates:
            if date in data.index and not pd.isna(data.loc[date, 'valuation_ratio']):
                valuation = data.loc[date, 'valuation_ratio']
                if valuation < -params['pe_threshold'] / 100:  # 低估值（下跌趨勢）
                    data.loc[date:, 'valuation_signal'] = 1
                elif valuation > params['pe_threshold'] / 100:  # 高估值（上漲趨勢）
                    data.loc[date:, 'valuation_signal'] = -1
                else:
                    data.loc[date:, 'valuation_signal'] = 0

        return data

    def implement_dividend_yield_strategy(self, data, params=None):
        """股息率策略"""
        params = params or {'yield_threshold': 0.04, 'rebalance_frequency': 'Q'}

        # 模擬股息率（實際應用中需要真實的股息數據）
        # 基於價格變動模擬股息率
        data['simulated_yield'] = 0.03 + 0.02 * np.random.random(len(data))

        data['dividend_signal'] = 0

        # 根據重新平衡頻率更新信號
        if params['rebalance_frequency'] == 'Q':
            rebalance_dates = data.resample('Q').first().index
        elif params['rebalance_frequency'] == 'M':
            rebalance_dates = data.resample('M').first().index
        else:
            rebalance_dates = data.resample('A').first().index

        for date in rebalance_dates:
            if date in data.index:
                if data.loc[date, 'simulated_yield'] > params['yield_threshold']:
                    data.loc[date:, 'dividend_signal'] = 1
                else:
                    data.loc[date:, 'dividend_signal'] = 0

        return data

    def implement_risk_parity_strategy(self, data, params=None):
        """風險平價策略"""
        params = params or {'lookback_period': 60, 'risk_threshold': 0.3}

        # 計算風險指標（基於波動率）
        data['rolling_volatility'] = data['HSIF_Return'].rolling(window=params['lookback_period']).std() * np.sqrt(252)
        data['risk_score'] = data['rolling_volatility'].rolling(window=30).mean()

        data['risk_parity_signal'] = 0

        # 月度更新信號
        monthly_dates = data.resample('M').first().index

        for date in monthly_dates:
            if date in data.index and not pd.isna(data.loc[date, 'risk_score']):
                risk = data.loc[date, 'risk_score']
                if risk < (1 - params['risk_threshold']):  # 低風險
                    data.loc[date:, 'risk_parity_signal'] = 1
                elif risk > (1 + params['risk_threshold']):  # 高風險
                    data.loc[date:, 'risk_parity_signal'] = -1
                else:
                    data.loc[date:, 'risk_parity_signal'] = 0

        return data

    def calculate_monthly_performance(self, data, strategy_name):
        """計算月度策略性能"""
        # 獲取信號列
        signal_col = None
        for col in data.columns:
            if 'signal' in col and col != 'signal':
                signal_col = col
                break

        if signal_col is None:
            raise ValueError(f"No signal column found for strategy {strategy_name}")

        # 計算策略收益
        returns = data['HSIF_Return'] * data[signal_col].shift(1)

        # 月度重採樣性能計算
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)

        # 年化收益
        annual_return = monthly_returns.mean() * 12

        # 年化波動率
        annual_volatility = monthly_returns.std() * np.sqrt(12)

        # 夏普比率
        risk_free_rate = 0.025
        excess_return = annual_return - risk_free_rate
        sharpe_ratio = excess_return / annual_volatility if annual_volatility > 0 else 0

        # 最大回撤
        cumulative = (1 + monthly_returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()

        # 勝率
        win_rate = (monthly_returns > 0).mean()

        # 交易統計
        monthly_signals = data[signal_col].resample('M').first()
        total_trades = monthly_signals.abs().sum()
        trades_per_year = total_trades / len(monthly_returns) * 12

        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        return {
            'strategy_name': strategy_name,
            'total_return': (1 + monthly_returns).prod() - 1,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'total_trades': int(total_trades),
            'trades_per_year': trades_per_year,
            'monthly_periods': len(monthly_returns),
            'years_tested': len(monthly_returns) / 12,
            'average_monthly_return': monthly_returns.mean(),
            'best_month': monthly_returns.max(),
            'worst_month': monthly_returns.min()
        }

    def run_monthly_strategies(self):
        """運行所有月度策略"""
        print("Low Frequency Monthly Trading System")
        print("=" * 50)

        # 加載數據
        data = self.load_real_data()
        if data is None:
            return None

        # 註冊月度策略
        self.register_monthly_strategy("Monthly_Momentum", self.implement_monthly_momentum_strategy,
                                       {'lookback_months': 6, 'momentum_threshold': 0.02})
        self.register_monthly_strategy("Quarterly_Reversal", self.implement_quarterly_reversal_strategy,
                                       {'lookback_quarters': 8, 'reversal_threshold': 0.15})
        self.register_monthly_strategy("Seasonal_Quarterly", self.implement_seasonal_strategy,
                                       {'months_to_buy': [1, 4, 7, 10], 'holding_period': 3})
        self.register_monthly_strategy("Valuation_Based", self.implement_valuation_based_strategy,
                                       {'pe_threshold': 15, 'valuation_periods': 12})
        self.register_monthly_strategy("Dividend_Yield", self.implement_dividend_yield_strategy,
                                       {'yield_threshold': 0.04, 'rebalance_frequency': 'Q'})
        self.register_monthly_strategy("Risk_Parity", self.implement_risk_parity_strategy,
                                       {'lookback_period': 60, 'risk_threshold': 0.3})

        results = {}

        for strategy_name, strategy_info in self.strategies.items():
            print(f"\n{'='*20} {strategy_name} {'='*20}")

            try:
                # 實施策略
                strategy_data = strategy_info['implementation'](data.copy(), strategy_info['params'])

                # 計算月度性能
                performance = self.calculate_monthly_performance(strategy_data, strategy_name)

                # 綜合評分
                score = self._calculate_monthly_score(performance)

                results[strategy_name] = {
                    **performance,
                    'score': score,
                    'grade': self._get_grade(score)
                }

                # 打印結果
                print(f"  Total Return: {performance['total_return']:.2%}")
                print(f"  Annual Return: {performance['annual_return']:.2%}")
                print(f"  Sharpe Ratio: {performance['sharpe_ratio']:.3f}")
                print(f"  Max Drawdown: {performance['max_drawdown']:.2%}")
                print(f"  Win Rate: {performance['win_rate']:.2%}")
                print(f"  Trades/Year: {performance['trades_per_year']:.1f}")
                print(f"  Monthly Periods: {performance['monthly_periods']}")
                print(f"  Score: {score:.1f}/100 ({self._get_grade(score)})")

            except Exception as e:
                print(f"  ERROR: Strategy failed - {e}")
                results[strategy_name] = {
                    'error': str(e),
                    'score': 0,
                    'grade': 'F'
                }

        # 生成對比報告
        self._generate_monthly_comparison_report(results)

        return results

    def _calculate_monthly_score(self, performance):
        """計算月度策略評分"""
        score = 0

        # 年化收益評分 (0-25分)
        if performance['annual_return'] > 0.20:
            score += 25
        elif performance['annual_return'] > 0.15:
            score += 20
        elif performance['annual_return'] > 0.10:
            score += 15
        elif performance['annual_return'] > 0.05:
            score += 10
        elif performance['annual_return'] > 0:
            score += 5

        # 夏普比率評分 (0-25分)
        if performance['sharpe_ratio'] > 1.0:
            score += 25
        elif performance['sharpe_ratio'] > 0.8:
            score += 20
        elif performance['sharpe_ratio'] > 0.6:
            score += 15
        elif performance['sharpe_ratio'] > 0.4:
            score += 10
        elif performance['sharpe_ratio'] > 0.2:
            score += 5

        # 最大回撤評分 (0-20分)
        if performance['max_drawdown'] > -0.1:
            score += 20
        elif performance['max_drawdown'] > -0.2:
            score += 15
        elif performance['max_drawdown'] > -0.3:
            score += 10
        elif performance['max_drawdown'] > -0.4:
            score += 5

        # 交易頻率評分 (0-15分)
        if performance['trades_per_year'] < 6:
            score += 15
        elif performance['trades_per_year'] < 12:
            score += 10
        elif performance['trades_per_year'] < 18:
            score += 5

        # 勝率評分 (0-10分)
        if performance['win_rate'] > 0.6:
            score += 10
        elif performance['win_rate'] > 0.55:
            score += 8
        elif performance['win_rate'] > 0.5:
            score += 6
        elif performance['win_rate'] > 0.45:
            score += 4
        elif performance['win_rate'] > 0.4:
            score += 2

        # Calmar比率評分 (0-5分)
        if performance['calmar_ratio'] > 1.0:
            score += 5
        elif performance['calmar_ratio'] > 0.5:
            score += 4
        elif performance['calmar_ratio'] > 0.3:
            score += 3
        elif performance['calmar_ratio'] > 0.1:
            score += 2
        elif performance['calmar_ratio'] > 0:
            score += 1

        return min(100, score)

    def _get_grade(self, score):
        """獲取評級"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        elif score >= 30:
            return 'D+'
        elif score >= 20:
            return 'D'
        else:
            return 'F'

    def _generate_monthly_comparison_report(self, results):
        """生成月度策略對比報告"""
        print(f"\n{'='*80}")
        print("MONTHLY STRATEGY COMPARISON REPORT")
        print(f"{'='*80}")

        # 排除錯誤的策略
        valid_results = {k: v for k, v in results.items() if 'error' not in v}

        if not valid_results:
            print("No valid monthly strategies found!")
            return

        # 按評分排序
        sorted_results = sorted(valid_results.items(), key=lambda x: x[1]['score'], reverse=True)

        print(f"\n{'Rank':<8} {'Strategy':<20} {'Score':<8} {'Grade':<8} {'Annual Return':<15} {'Sharpe':<10} {'Trades/Year':<12} {'Win Rate':<10}")
        print("-" * 95)

        for i, (name, result) in enumerate(sorted_results, 1):
            print(f"{i:<8} {name:<20} {result['score']:<8.1f} {result['grade']:<8} "
                  f"{result['annual_return']:<15.2%} {result['sharpe_ratio']:<10.3f} "
                  f"{result['trades_per_year']:<12.1f} {result['win_rate']:<10.2%}")

        # 月度表現統計
        print(f"\nMonthly Performance Statistics:")
        all_returns = [r['average_monthly_return'] for r in valid_results.values()]
        all_sharpes = [r['sharpe_ratio'] for r in valid_results.values()]
        all_drawdowns = [r['max_drawdown'] for r in valid_results.values()]

        print(f"  Average Monthly Return: {np.mean(all_returns):.2%}")
        print(f"  Average Sharpe Ratio: {np.mean(all_sharpes):.3f}")
        print(f"  Average Max Drawdown: {np.mean(all_drawdowns):.2%}")
        print(f"  Best Monthly Return: {max(r['best_month'] for r in valid_results.values()):.2%}")
        print(f"  Worst Monthly Return: {min(r['worst_month'] for r in valid_results.values()):.2%}")

        # 保存結果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            'analysis_date': datetime.now().isoformat(),
            'strategy_type': 'Monthly Low Frequency',
            'total_strategies': len(self.strategies),
            'valid_strategies': len(valid_results),
            'rankings': sorted_results,
            'best_strategy': sorted_results[0] if sorted_results else None,
            'average_score': sum(r['score'] for r in valid_results.values()) / len(valid_results),
            'statistics': {
                'avg_monthly_return': float(np.mean(all_returns)),
                'avg_sharpe_ratio': float(np.mean(all_sharpes)),
                'avg_max_drawdown': float(np.mean(all_drawdowns)),
                'best_monthly_return': float(max(r['best_month'] for r in valid_results.values())),
                'worst_monthly_return': float(min(r['worst_month'] for r in valid_results.values()))
            }
        }

        filename = f"monthly_strategy_report_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] Monthly report saved: {filename}")

def main():
    """主執行函數"""
    trading_system = LowFrequencyTradingSystem()
    results = trading_system.run_monthly_strategies()
    return results

if __name__ == "__main__":
    main()