#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生產級CBSC回測驗證框架
包含統計顯著性檢驗、蒙特卡洛模擬、風險控制
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class ProductionBacktestFramework:
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.risk_free_rate = 0.025  # 2.5% 無風險利率

    def comprehensive_strategy_validation(self, strategy_data, benchmark_data=None):
        """全面策略驗證"""
        print(f"🔍 開始生產級策略驗證...")

        validation_results = {
            'basic_metrics': self._calculate_basic_metrics(strategy_data),
            'statistical_significance': self._test_statistical_significance(strategy_data),
            'monte_carlo_simulation': self._run_monte_carlo_simulation(strategy_data),
            'market_regime_analysis': self._analyze_market_regimes(strategy_data),
            'risk_assessment': self._assess_risk_metrics(strategy_data),
            'production_readiness': self._evaluate_production_readiness(strategy_data)
        }

        return validation_results

    def _calculate_basic_metrics(self, strategy_data):
        """計算基礎指標"""
        returns = strategy_data['strategy_returns']

        # 基礎收益指標
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

        # 收益分布
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'win_rate': win_rate,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'total_days': len(returns),
            'trading_days_per_year': 252
        }

    def _test_statistical_significance(self, strategy_data):
        """統計顯著性檢驗"""
        returns = strategy_data['strategy_returns']
        n = len(returns)

        # 計算t統計量
        mean_return = returns.mean()
        std_return = returns.std()
        t_statistic = mean_return / (std_return / np.sqrt(n))

        # 計算p值（單尾檢驗）
        from scipy import stats
        p_value = 1 - stats.t.cdf(t_statistic, df=n-1)

        # 95%信賴區間
        confidence_level = 0.95
        t_critical = stats.t.ppf(1 - (1 - confidence_level)/2, df=n-1)
        margin_error = t_critical * (std_return / np.sqrt(n))
        confidence_interval = (mean_return - margin_error, mean_return + margin_error)

        # 計算信息比率
        information_ratio = mean_return / std_return * np.sqrt(252)

        # 計算Alpha和Beta（如果有基準數據）
        alpha = None
        beta = None
        if 'benchmark_returns' in strategy_data:
            benchmark_returns = strategy_data['benchmark_returns']
            # 簡單回歸計算Alpha和Beta
            covariance = np.cov(returns, benchmark_returns)[0,1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
            alpha = mean_return - beta * benchmark_returns.mean()

        # 最小樣本量要求
        min_sample_size = self._calculate_min_sample_size(
            mean_return, std_return, confidence_level=0.95, margin_error=0.001
        )

        return {
            't_statistic': t_statistic,
            'p_value': p_value,
            'is_significant': p_value < 0.05,
            'confidence_interval_95': confidence_interval,
            'information_ratio': information_ratio,
            'alpha': alpha,
            'beta': beta,
            'sample_size': n,
            'min_required_sample_size': min_sample_size,
            'adequate_sample_size': n >= min_sample_size
        }

    def _calculate_min_sample_size(self, mean_return, std_return, confidence_level=0.95, margin_error=0.001):
        """計算最小樣本量要求"""
        from scipy import stats
        z_critical = stats.norm.ppf(1 - (1 - confidence_level)/2)
        n = (z_critical * std_return / margin_error) ** 2
        return max(252, int(n))  # 至少需要1年數據

    def _run_monte_carlo_simulation(self, strategy_data, n_simulations=10000):
        """蒙特卡洛模擬"""
        returns = strategy_data['strategy_returns']
        n_days = len(returns)

        # 基於歷史收益率的隨機抽樣
        simulated_returns = []

        for _ in range(n_simulations):
            # 帶替換的隨機抽樣
            simulated_daily_returns = np.random.choice(returns, n_days, replace=True)
            cumulative_return = (1 + simulated_daily_returns).prod() - 1
            simulated_returns.append(cumulative_return)

        simulated_returns = np.array(simulated_returns)

        # 計算統計量
        percentiles = np.percentile(simulated_returns, [5, 25, 50, 75, 95])

        # 實際策略在模擬中的百分位
        actual_return = (1 + returns).prod() - 1
        percentile = np.percentile(simulated_returns, actual_return)

        # 概率分析
        prob_positive = (simulated_returns > 0).mean()
        prob_beat_market = None
        if 'benchmark_returns' in strategy_data:
            benchmark_return = (1 + strategy_data['benchmark_returns']).prod() - 1
            prob_beat_market = (simulated_returns > benchmark_return).mean()

        return {
            'mean_simulated_return': simulated_returns.mean(),
            'std_simulated_return': simulated_returns.std(),
            'percentile_5': percentiles[0],
            'percentile_25': percentiles[1],
            'percentile_50': percentiles[2],
            'percentile_75': percentiles[3],
            'percentile_95': percentiles[4],
            'actual_return_percentile': percentile,
            'prob_positive_return': prob_positive,
            'prob_beat_market': prob_beat_market,
            'n_simulations': n_simulations
        }

    def _analyze_market_regimes(self, strategy_data):
        """市場環境分析"""
        returns = strategy_data['strategy_returns']

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

    def _assess_risk_metrics(self, strategy_data):
        """風險指標評估"""
        returns = strategy_data['strategy_returns']

        # VaR和CVaR計算
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        cvar_95 = returns[returns <= var_95].mean()
        cvar_99 = returns[returns <= var_99].mean()

        # 最大連續虧損期
        cumulative_returns = (1 + returns).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns - peak) / peak

        # 計算連續虧損期
        drawdown_periods = []
        in_drawdown = False
        current_period = 0

        for dd in drawdown:
            if dd < 0 and not in_drawdown:
                in_drawdown = True
                current_period = 1
            elif dd < 0 and in_drawdown:
                current_period += 1
            elif dd >= 0 and in_drawdown:
                drawdown_periods.append(current_period)
                in_drawdown = False
                current_period = 0

        if in_drawdown:
            drawdown_periods.append(current_period)

        max_drawdown_duration = max(drawdown_periods) if drawdown_periods else 0
        avg_drawdown_duration = np.mean(drawdown_periods) if drawdown_periods else 0

        # 波動率分析
        rolling_vol = returns.rolling(20).std() * np.sqrt(252)
        volatility_regime = {
            'low_volatility_days': (rolling_vol < rolling_vol.quantile(0.33)).sum(),
            'normal_volatility_days': ((rolling_vol >= rolling_vol.quantile(0.33)) &
                                      (rolling_vol <= rolling_vol.quantile(0.67))).sum(),
            'high_volatility_days': (rolling_vol > rolling_vol.quantile(0.67)).sum()
        }

        return {
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'max_drawdown_duration_days': max_drawdown_duration,
            'avg_drawdown_duration_days': avg_drawdown_duration,
            'volatility_regime': volatility_regime,
            'tail_ratio': abs(var_99) / abs(var_95) if var_95 != 0 else np.inf
        }

    def _evaluate_production_readiness(self, strategy_data):
        """生產就緒性評估"""
        basic_metrics = self._calculate_basic_metrics(strategy_data)
        statistical_tests = self._test_statistical_significance(strategy_data)
        monte_carlo = self._run_monte_carlo_simulation(strategy_data, 1000)  # 較少模擬次數

        # 評分標準
        scores = {
            'performance_score': self._score_performance(basic_metrics),
            'risk_score': self._score_risk(basic_metrics),
            'statistical_score': self._score_statistical_significance(statistical_tests),
            'robustness_score': self._score_robustness(monte_carlo),
            'sample_size_score': self._score_sample_size(statistical_tests)
        }

        # 綜合評分
        total_score = sum(scores.values()) / len(scores)

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

        # 建議
        recommendations = self._generate_recommendations(scores, basic_metrics, statistical_tests)

        return {
            'individual_scores': scores,
            'total_score': total_score,
            'grade': grade,
            'is_production_ready': total_score >= 65,
            'recommendations': recommendations
        }

    def _score_performance(self, metrics):
        """評分表現指標"""
        score = 0

        # 年化收益評分 (0-25分)
        if metrics['annual_return'] > 0.20:
            score += 25
        elif metrics['annual_return'] > 0.15:
            score += 20
        elif metrics['annual_return'] > 0.10:
            score += 15
        elif metrics['annual_return'] > 0.05:
            score += 10
        elif metrics['annual_return'] > 0:
            score += 5

        # 夏普比率評分 (0-25分)
        if metrics['sharpe_ratio'] > 1.5:
            score += 25
        elif metrics['sharpe_ratio'] > 1.0:
            score += 20
        elif metrics['sharpe_ratio'] > 0.8:
            score += 15
        elif metrics['sharpe_ratio'] > 0.5:
            score += 10
        elif metrics['sharpe_ratio'] > 0.2:
            score += 5

        # Calmar比率評分 (0-25分)
        if metrics['calmar_ratio'] > 1.0:
            score += 25
        elif metrics['calmar_ratio'] > 0.5:
            score += 20
        elif metrics['calmar_ratio'] > 0.3:
            score += 15
        elif metrics['calmar_ratio'] > 0.1:
            score += 10
        elif metrics['calmar_ratio'] > 0:
            score += 5

        # 勝率評分 (0-25分)
        if metrics['win_rate'] > 0.6:
            score += 25
        elif metrics['win_rate'] > 0.55:
            score += 20
        elif metrics['win_rate'] > 0.5:
            score += 15
        elif metrics['win_rate'] > 0.45:
            score += 10
        elif metrics['win_rate'] > 0.4:
            score += 5

        return score

    def _score_risk(self, metrics):
        """評分風險指標"""
        score = 0

        # 最大回撤評分 (0-50分)
        if abs(metrics['max_drawdown']) < 0.1:
            score += 50
        elif abs(metrics['max_drawdown']) < 0.15:
            score += 40
        elif abs(metrics['max_drawdown']) < 0.2:
            score += 30
        elif abs(metrics['max_drawdown']) < 0.3:
            score += 20
        elif abs(metrics['max_drawdown']) < 0.4:
            score += 10

        # 波動率評分 (0-50分)
        if metrics['volatility'] < 0.1:
            score += 50
        elif metrics['volatility'] < 0.15:
            score += 40
        elif metrics['volatility'] < 0.2:
            score += 30
        elif metrics['volatility'] < 0.25:
            score += 20
        elif metrics['volatility'] < 0.3:
            score += 10

        return score

    def _score_statistical_significance(self, statistical_tests):
        """評分統計顯著性"""
        score = 0

        # p值評分 (0-50分)
        if statistical_tests['p_value'] < 0.01:
            score += 50
        elif statistical_tests['p_value'] < 0.05:
            score += 40
        elif statistical_tests['p_value'] < 0.1:
            score += 30
        elif statistical_tests['p_value'] < 0.2:
            score += 20
        else:
            score += 0

        # 樣本量評分 (0-50分)
        if statistical_tests['adequate_sample_size']:
            score += 50
        else:
            ratio = statistical_tests['sample_size'] / statistical_tests['min_required_sample_size']
            if ratio > 0.8:
                score += 30
            elif ratio > 0.5:
                score += 20
            elif ratio > 0.3:
                score += 10
            else:
                score += 0

        return score

    def _score_robustness(self, monte_carlo):
        """評分穩健性"""
        score = 0

        # 模擬表現評分 (0-50分)
        prob_positive = monte_carlo['prob_positive_return']
        if prob_positive > 0.8:
            score += 50
        elif prob_positive > 0.7:
            score += 40
        elif prob_positive > 0.6:
            score += 30
        elif prob_positive > 0.5:
            score += 20
        elif prob_positive > 0.4:
            score += 10

        # 實際表現百分位評分 (0-50分)
        percentile = monte_carlo['actual_return_percentile']
        if percentile > 80:
            score += 50
        elif percentile > 70:
            score += 40
        elif percentile > 60:
            score += 30
        elif percentile > 50:
            score += 20
        elif percentile > 40:
            score += 10

        return score

    def _score_sample_size(self, statistical_tests):
        """評分樣本量充足性"""
        sample_size = statistical_tests['sample_size']

        if sample_size >= 1000:
            return 100
        elif sample_size >= 500:
            return 80
        elif sample_size >= 252:  # 1年交易日
            return 60
        elif sample_size >= 100:
            return 40
        elif sample_size >= 50:
            return 20
        else:
            return 0

    def _generate_recommendations(self, scores, metrics, statistical_tests):
        """生成建議"""
        recommendations = []

        if scores['sample_size_score'] < 60:
            recommendations.append("需要更多數據 - 當前樣本量不足，建議至少收集1年交易日數據")

        if scores['statistical_score'] < 50:
            recommendations.append("統計顯著性不足 - 需要更長時間或更好的策略表現來證明有效性")

        if scores['risk_score'] < 40:
            recommendations.append("風險過高 - 最大回撤或波動率過大，需要改進風險管理")

        if scores['performance_score'] < 40:
            recommendations.append("表現不佳 - 建議優化策略參數或考慮其他策略")

        if metrics['sharpe_ratio'] < 0.5:
            recommendations.append("夏普比率偏低 - 風險調整後收益不理想，需要改善收益風險比")

        if statistical_tests.get('adequate_sample_size', False) == False:
            recommendations.append("樣本量不符合最小要求 - 當前數據無法提供可靠的統計推斷")

        return recommendations

    def generate_validation_report(self, validation_results, strategy_name):
        """生成驗證報告"""
        report = {
            'strategy_name': strategy_name,
            'validation_date': datetime.now().isoformat(),
            'summary': {
                'grade': validation_results['production_readiness']['grade'],
                'total_score': validation_results['production_readiness']['total_score'],
                'is_production_ready': validation_results['production_readiness']['is_production_ready']
            },
            'detailed_results': validation_results
        }

        # 保存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_report_{strategy_name}_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        return report, filename

# 使用示例
def main():
    """主函數示例"""
    print("🚀 生產級回測驗證框架")
    print("=" * 50)

    # 創建驗證框架
    validator = ProductionBacktestFramework()

    # 這裡需要實際的策略數據
    # strategy_data = {
    #     'strategy_returns': pd.Series([...]),
    #     'benchmark_returns': pd.Series([...])
    # }

    # validation_results = validator.comprehensive_strategy_validation(strategy_data)
    # report, filename = validator.generate_validation_report(validation_results, "RSI_Aggressive")

    print("✅ 生產級驗證框架已準備就緒")
    print("📋 使用指南：")
    print("1. 準備策略收益數據 (strategy_returns)")
    print("2. 可選準備基準數據 (benchmark_returns)")
    print("3. 調用 comprehensive_strategy_validation()")
    print("4. 查看詳細驗證報告和生產就緒性評級")

if __name__ == "__main__":
    main()