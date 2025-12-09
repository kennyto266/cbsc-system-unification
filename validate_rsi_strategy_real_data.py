#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI策略真實數據驗證系統
使用3740天真實數據驗證RSI激進策略的統計顯著性
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class RSIStrategyValidator:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.risk_free_rate = 0.025  # 2.5%無風險利率

    def load_real_cbsc_data(self, filename=None):
        """加載真實CBSC數據"""
        if filename is None:
            import glob
            cbsc_files = glob.glob('acquired_data/cbsc_real_data_*.csv')
            if not cbsc_files:
                raise FileNotFoundError("No CBSC data files found in acquired_data/")
            filename = cbsc_files[0]

        print(f"Loading CBSC data from: {filename}")
        data = pd.read_csv(filename, index_col=0, parse_dates=True)

        print(f"[OK] Loaded {len(data)} records")
        print(f"Date range: {data.index.min().date()} to {data.index.max().date()}")

        return data

    def implement_rsi_strategy(self, data, rsi_period=14, overbought=70, oversold=30):
        """實施RSI策略在真實數據上"""
        print(f"\nImplementing RSI Strategy (period={rsi_period}, overbought={overbought}, oversold={oversold})")

        # 計算RSI
        def calculate_rsi(prices, period):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi

        # 使用HSIF期貨價格計算RSI
        data['RSI'] = calculate_rsi(data['HSIF_Close'], rsi_period)

        # 生成交易信號
        data['signal'] = 0
        data.loc[data['RSI'] < oversold, 'signal'] = 1   # 超賣買入
        data.loc[data['RSI'] > overbought, 'signal'] = -1  # 超買賣出

        # 移除連續相同信號（減少頻繁交易）
        data['signal'] = data['signal'].replace(0, np.nan).ffill().fillna(0)

        # 計算策略收益
        data['strategy_returns'] = data['HSIF_Return'] * data['signal'].shift(1)

        print(f"[OK] RSI strategy implemented")
        print(f"  Total signals generated: {data['signal'].abs().sum():.0f}")
        print(f"  Buy signals: {(data['signal'] == 1).sum()}")
        print(f"  Sell signals: {(data['signal'] == -1).sum()}")

        return data

    def calculate_performance_metrics(self, data):
        """計算策略性能指標"""
        returns = data['strategy_returns']

        # 基礎指標
        total_return = (1 + returns).prod() - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1

        # 風險指標
        volatility = returns.std() * np.sqrt(252)

        # 夏普比率
        excess_returns = returns - self.risk_free_rate / 252
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

        # 最大回撤
        cumulative = (1 + returns).cumprod()
        peak = cumulative.expanding(min_periods=1).max()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()

        # Calmar比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 勝率
        win_rate = (returns > 0).mean()

        # Sortino比率
        downside_returns = returns[returns < 0]
        sortino_ratio = (returns.mean() - self.risk_free_rate/252) / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0

        # 交易統計
        total_trades = data['signal'].abs().sum()

        # 交易成本（真實成本模型）
        trading_costs_pct = 0.002  # 0.2%的交易成本
        trading_costs = total_trades * self.initial_capital * trading_costs_pct
        net_return = total_return - trading_costs / self.initial_capital

        return {
            'total_return': total_return,
            'net_return': net_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': int(total_trades),
            'trading_costs': trading_costs,
            'total_days': len(returns),
            'years_tested': len(returns) / 252
        }

    def test_statistical_significance(self, data):
        """統計顯著性檢驗"""
        returns = data['strategy_returns']
        n = len(returns)

        # t檢驗
        mean_return = returns.mean()
        std_return = returns.std()
        t_statistic = mean_return / (std_return / np.sqrt(n))

        # p值
        p_value = 2 * (1 - stats.t.cdf(abs(t_statistic), df=n-1))

        # 95%信賴區間
        t_critical = stats.t.ppf(1 - (1-0.95)/2, df=n-1)
        margin_error = t_critical * (std_return / np.sqrt(n))
        confidence_interval = (mean_return - margin_error, mean_return + margin_error)

        # 計算年化統計量
        annual_mean = mean_return * 252
        annual_std = std_return * np.sqrt(252)
        annual_t_stat = annual_mean / annual_std

        # 最小樣本量檢驗
        min_sample_size_95 = (1.96 * std_return / 0.001) ** 2  # 年化收益0.1%的精度
        min_sample_size_90 = (1.645 * std_return / 0.001) ** 2

        return {
            't_statistic': t_statistic,
            'annual_t_statistic': annual_t_stat,
            'p_value': p_value,
            'is_significant_95': p_value < 0.05,
            'is_significant_90': p_value < 0.1,
            'confidence_interval_95': confidence_interval,
            'sample_size': n,
            'min_required_sample_size_95': max(252, int(min_sample_size_95)),
            'min_required_sample_size_90': max(252, int(min_sample_size_90)),
            'adequate_sample_size_95': n >= max(252, int(min_sample_size_95)),
            'adequate_sample_size_90': n >= max(252, int(min_sample_size_90)),
            'daily_return_mean': mean_return,
            'daily_return_std': std_return,
            'annual_return_mean': annual_mean,
            'annual_return_std': annual_std
        }

    def monte_carlo_simulation(self, data, n_simulations=10000):
        """蒙特卡洛模擬"""
        returns = data['strategy_returns']
        n_days = len(returns)

        print(f"Running Monte Carlo simulation with {n_simulations} iterations...")

        # 基於歷史收益率的隨機抽樣
        simulated_returns = []

        for i in range(n_simulations):
            # 隨機抽樣構建模擬路徑
            simulated_daily_returns = np.random.choice(returns, n_days, replace=True)
            cumulative_return = (1 + simulated_daily_returns).prod() - 1
            simulated_returns.append(cumulative_return)

            if (i + 1) % 1000 == 0:
                print(f"  Progress: {i+1}/{n_simulations} ({(i+1)/n_simulations*100:.0f}%)")

        simulated_returns = np.array(simulated_returns)

        # 計算統計量
        percentiles = np.percentile(simulated_returns, [5, 25, 50, 75, 95])

        # 實際策略在模擬中的百分位
        actual_return = (1 + returns).prod() - 1
        # 修正：將實際收益轉換為百分位
        actual_percentile = (simulated_returns < actual_return).mean() * 100

        # 概率分析
        prob_positive = (simulated_returns > 0).mean()
        prob_beat_market = None
        if 'HSIF_Return' in data.columns:
            benchmark_return = (1 + data['HSIF_Return']).prod() - 1
            prob_beat_market = (simulated_returns > benchmark_return).mean()

        return {
            'mean_simulated_return': simulated_returns.mean(),
            'std_simulated_return': simulated_returns.std(),
            'percentile_5': percentiles[0],
            'percentile_25': percentiles[1],
            'percentile_50': percentiles[2],
            'percentile_75': percentiles[3],
            'percentile_95': percentiles[4],
            'actual_return_percentile': actual_percentile,
            'prob_positive_return': prob_positive,
            'prob_beat_market': prob_beat_market,
            'n_simulations': n_simulations
        }

    def analyze_market_regimes(self, data):
        """市場環境分析"""
        returns = data['strategy_returns']

        # 識別市場環境
        volatility = returns.rolling(20).std()
        trend = returns.rolling(60).mean()

        # 分類市場環境
        regimes = []
        for i in range(len(returns)):
            if pd.isna(volatility.iloc[i]) or pd.isna(trend.iloc[i]):
                regimes.append('unknown')
            elif volatility.iloc[i] > volatility.quantile(0.75):
                regimes.append('high_volatility')
            elif trend.iloc[i] > trend.quantile(0.75):
                regimes.append('bull_market')
            elif trend.iloc[i] < trend.quantile(0.25):
                regimes.append('bear_market')
            else:
                regimes.append('sideways')

        # 計算各環境下的表現
        regime_performance = {}
        for regime in set(regimes):
            mask = [r == regime for r in regimes]
            regime_returns = returns[mask]
            if len(regime_returns) > 0:
                regime_performance[regime] = {
                    'annual_return': (1 + regime_returns.mean()) ** 252 - 1,
                    'volatility': regime_returns.std() * np.sqrt(252),
                    'sharpe_ratio': regime_returns.mean() / regime_returns.std() * np.sqrt(252) if regime_returns.std() > 0 else 0,
                    'win_rate': (regime_returns > 0).mean(),
                    'days': len(regime_returns)
                }

        return {
            'regime_performance': regime_performance,
            'regime_distribution': pd.Series(regimes).value_counts().to_dict(),
            'best_regime': max(regime_performance.keys(), key=lambda x: regime_performance[x]['sharpe_ratio']) if regime_performance else None,
            'worst_regime': min(regime_performance.keys(), key=lambda x: regime_performance[x]['sharpe_ratio']) if regime_performance else None
        }

    def evaluate_production_readiness(self, metrics, statistical_tests, monte_carlo):
        """生產就緒性評估"""
        scores = {}

        # 表現評分 (0-25分)
        if metrics['annual_return'] > 0.20:
            scores['performance'] = 25
        elif metrics['annual_return'] > 0.15:
            scores['performance'] = 20
        elif metrics['annual_return'] > 0.10:
            scores['performance'] = 15
        elif metrics['annual_return'] > 0.05:
            scores['performance'] = 10
        elif metrics['annual_return'] > 0:
            scores['performance'] = 5
        else:
            scores['performance'] = 0

        # 夏普比率評分 (0-25分)
        if metrics['sharpe_ratio'] > 1.5:
            scores['sharpe'] = 25
        elif metrics['sharpe_ratio'] > 1.0:
            scores['sharpe'] = 20
        elif metrics['sharpe_ratio'] > 0.8:
            scores['sharpe'] = 15
        elif metrics['sharpe_ratio'] > 0.5:
            scores['sharpe'] = 10
        elif metrics['sharpe_ratio'] > 0.2:
            scores['sharpe'] = 5
        else:
            scores['sharpe'] = 0

        # 統計顯著性評分 (0-25分)
        if statistical_tests['is_significant_95']:
            scores['significance'] = 25
        elif statistical_tests['is_significant_90']:
            scores['significance'] = 20
        elif statistical_tests['p_value'] < 0.2:
            scores['significance'] = 15
        elif statistical_tests['p_value'] < 0.3:
            scores['significance'] = 10
        else:
            scores['significance'] = 0

        # 蒙特卡洛穩健性評分 (0-25分)
        prob_positive = monte_carlo['prob_positive_return']
        if prob_positive > 0.8:
            scores['robustness'] = 25
        elif prob_positive > 0.7:
            scores['robustness'] = 20
        elif prob_positive > 0.6:
            scores['robustness'] = 15
        elif prob_positive > 0.5:
            scores['robustness'] = 10
        elif prob_positive > 0.4:
            scores['robustness'] = 5
        else:
            scores['robustness'] = 0

        # 綜合評分
        total_score = sum(scores.values()) / 4

        # 評級
        if total_score >= 85:
            grade = 'A+ (Excellent)'
        elif total_score >= 75:
            grade = 'A (Very Good)'
        elif total_score >= 65:
            grade = 'B (Good)'
        elif total_score >= 55:
            grade = 'C (Fair)'
        else:
            grade = 'D (Poor)'

        # 生產就緒性
        is_production_ready = (
            total_score >= 65 and
            statistical_tests['adequate_sample_size_95'] and
            metrics['max_drawdown'] > -0.5  # 最大回撤小於50%
        )

        return {
            'individual_scores': scores,
            'total_score': total_score,
            'grade': grade,
            'is_production_ready': is_production_ready,
            'recommendations': self._generate_recommendations(scores, metrics, statistical_tests)
        }

    def _generate_recommendations(self, scores, metrics, statistical_tests):
        """生成建議"""
        recommendations = []

        if scores['performance'] < 15:
            recommendations.append("Consider optimizing strategy parameters to improve returns")

        if scores['sharpe'] < 15:
            recommendations.append("Risk-adjusted returns need improvement - consider better risk management")

        if scores['significance'] < 20:
            recommendations.append("Statistical significance is marginal - need more data or better strategy")

        if not statistical_tests['adequate_sample_size_95']:
            recommendations.append("Insufficient sample size for reliable conclusions")

        if metrics['max_drawdown'] < -0.4:
            recommendations.append("High drawdown risk - implement stricter risk controls")

        if metrics['total_trades'] > 100:  # 過度交易
            recommendations.append("High trading frequency may erode returns - consider reducing trade frequency")

        return recommendations

    def generate_validation_report(self, results):
        """生成驗證報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            'strategy_name': 'RSI_Aggressive_Real_Data_Validation',
            'validation_date': datetime.now().isoformat(),
            'data_source': 'acheng_sharpe_results.csv (Enhanced CBSC Data)',
            'summary': {
                'grade': results['production_readiness']['grade'],
                'total_score': results['production_readiness']['total_score'],
                'is_production_ready': results['production_readiness']['is_production_ready']
            },
            'performance_metrics': results['performance'],
            'statistical_significance': results['statistical_tests'],
            'monte_carlo_simulation': results['monte_carlo'],
            'market_regime_analysis': results['market_regimes'],
            'production_readiness': results['production_readiness']
        }

        # 保存報告
        filename = f"rsi_validation_report_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n[SAVE] Validation report saved: {filename}")
        return report, filename

def main():
    """主執行函數"""
    print("RSI Strategy Real Data Validation System")
    print("=" * 60)

    try:
        # 初始化驗證器
        validator = RSIStrategyValidator()

        # 加載真實數據
        print("Step 1: Loading real CBSC data...")
        data = validator.load_real_cbsc_data()

        # 實施RSI策略
        print("\nStep 2: Implementing RSI strategy...")
        strategy_data = validator.implement_rsi_strategy(data)

        # 計算性能指標
        print("\nStep 3: Calculating performance metrics...")
        performance_metrics = validator.calculate_performance_metrics(strategy_data)

        # 統計顯著性檢驗
        print("\nStep 4: Testing statistical significance...")
        statistical_tests = validator.test_statistical_significance(strategy_data)

        # 蒙特卡洛模擬
        print("\nStep 5: Running Monte Carlo simulation...")
        monte_carlo_results = validator.monte_carlo_simulation(strategy_data)

        # 市場環境分析
        print("\nStep 6: Analyzing market regimes...")
        market_regimes = validator.analyze_market_regimes(strategy_data)

        # 生產就緒性評估
        print("\nStep 7: Evaluating production readiness...")
        production_readiness = validator.evaluate_production_readiness(
            performance_metrics, statistical_tests, monte_carlo_results
        )

        # 生成報告
        print("\nStep 8: Generating validation report...")
        report, filename = validator.generate_validation_report({
            'performance': performance_metrics,
            'statistical_tests': statistical_tests,
            'monte_carlo': monte_carlo_results,
            'market_regimes': market_regimes,
            'production_readiness': production_readiness
        })

        # 打印關鍵結果
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS SUMMARY")
        print("=" * 80)

        print(f"\n[PERFORMANCE]")
        print(f"  Total Return: {performance_metrics['total_return']:.2%}")
        print(f"  Annual Return: {performance_metrics['annual_return']:.2%}")
        print(f"  Sharpe Ratio: {performance_metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown: {performance_metrics['max_drawdown']:.2%}")
        print(f"  Win Rate: {performance_metrics['win_rate']:.2%}")
        print(f"  Total Trades: {performance_metrics['total_trades']}")

        print(f"\n[STATISTICAL SIGNIFICANCE]")
        print(f"  T-Statistic: {statistical_tests['t_statistic']:.3f}")
        print(f"  P-Value: {statistical_tests['p_value']:.4f}")
        print(f"  Significant (95%): {'Yes' if statistical_tests['is_significant_95'] else 'No'}")
        print(f"  Sample Size: {statistical_tests['sample_size']} days")
        print(f"  Min Required: {statistical_tests['min_required_sample_size_95']} days")
        print(f"  Adequate Sample: {'Yes' if statistical_tests['adequate_sample_size_95'] else 'No'}")

        print(f"\n[MONTE CARLO]")
        print(f"  Prob Positive Return: {monte_carlo_results['prob_positive_return']:.1%}")
        print(f"  Actual Percentile: {monte_carlo_results['actual_return_percentile']:.1f}")
        print(f"  Simulations Run: {monte_carlo_results['n_simulations']}")

        print(f"\n[PRODUCTION READINESS]")
        print(f"  Grade: {production_readiness['grade']}")
        print(f"  Total Score: {production_readiness['total_score']:.1f}/100")
        print(f"  Ready for Production: {'Yes' if production_readiness['is_production_ready'] else 'No'}")

        if production_readiness['recommendations']:
            print(f"\n[RECOMMENDATIONS]")
            for i, rec in enumerate(production_readiness['recommendations'], 1):
                print(f"  {i}. {rec}")

        print(f"\n[DETAILED REPORT]")
        print(f"  Full report saved: {filename}")

        return report

    except Exception as e:
        print(f"ERROR: Validation failed - {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()