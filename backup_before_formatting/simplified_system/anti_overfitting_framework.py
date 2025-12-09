#!/usr/bin/env python3
"""
Anti-Overfitting Strategy Validation Framework
抗过度拟合策略验证框架 - 解决策略统计可靠性问题

基于Walk-Forward分析结果，建立科学的策略验证体系
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import time
import warnings
from scipy import stats
from sklearn.model_selection import TimeSeriesSplit
warnings.filterwarnings('ignore')

class ValidationLevel(Enum):
    """验证等级"""
    BASIC = "basic"           # 基础验证
    STANDARD = "standard"     # 标准验证
    RIGOROUS = "rigorous"     # 严格验证
    INSTITUTIONAL = "institutional"  # 机构级验证

class OverfittingRisk(Enum):
    """过拟合风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ValidationConfig:
    """验证配置"""
    validation_level: ValidationLevel
    walk_forward_windows: int = 28
    min_trades_per_window: int = 5
    stability_threshold: float = 0.7
    statistical_significance: float = 0.05
    out_of_sample_ratio: float = 0.3
    max_correlation_with_others: float = 0.8

@dataclass
class StrategyMetrics:
    """策略指标"""
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades_count: int
    volatility: float
    calmar_ratio: float
    sortino_ratio: float
    profit_factor: float

@dataclass
class ValidationResults:
    """验证结果"""
    strategy_name: str
    in_sample_metrics: StrategyMetrics
    out_of_sample_metrics: StrategyMetrics
    walk_forward_results: Dict
    statistical_tests: Dict
    overfitting_risk: OverfittingRisk
    validation_score: float
    is_accepted: bool

class AntiOverfittingFramework:
    """抗过拟合框架核心类"""

    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig(ValidationLevel.STANDARD)
        self.validation_history = []
        self.benchmark_metrics = None

    def validate_strategy(self, strategy_data: pd.DataFrame,
                         strategy_name: str,
                         benchmark_data: pd.DataFrame = None) -> ValidationResults:
        """
        策略验证主函数
        """
        print(f"Starting validation for strategy: {strategy_name}")
        start_time = time.time()

        # 数据分割
        train_data, test_data = self._split_data(strategy_data)

        # 计算训练集和测试集指标
        in_sample_metrics = self._calculate_strategy_metrics(train_data)
        out_sample_metrics = self._calculate_strategy_metrics(test_data)

        # Walk-Forward分析
        walk_forward_results = self._walk_forward_analysis(strategy_data)

        # 统计检验
        statistical_tests = self._statistical_validation(
            train_data, test_data, walk_forward_results
        )

        # 过拟合风险评估
        overfitting_risk = self._assess_overfitting_risk(
            in_sample_metrics, out_sample_metrics, walk_forward_results, statistical_tests
        )

        # 综合验证评分
        validation_score = self._calculate_validation_score(
            in_sample_metrics, out_sample_metrics, walk_forward_results,
            statistical_tests, overfitting_risk
        )

        # 验证决策
        is_accepted = self._make_validation_decision(
            validation_score, overfitting_risk, statistical_tests
        )

        results = ValidationResults(
            strategy_name=strategy_name,
            in_sample_metrics=in_sample_metrics,
            out_of_sample_metrics=out_sample_metrics,
            walk_forward_results=walk_forward_results,
            statistical_tests=statistical_tests,
            overfitting_risk=overfitting_risk,
            validation_score=validation_score,
            is_accepted=is_accepted
        )

        validation_time = time.time() - start_time
        print(f"SUCCESS Validation completed in {validation_time:.2f}s")
        print(f"INFO Validation Score: {validation_score:.3f}")
        print(f"INFO Overfitting Risk: {overfitting_risk.value}")
        print(f"RESULT: {'ACCEPTED' if is_accepted else 'REJECTED'}")

        self.validation_history.append(results)
        return results

    def _split_data(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """时间序列数据分割"""
        split_idx = int(len(data) * (1 - self.config.out_of_sample_ratio))
        train_data = data.iloc[:split_idx]
        test_data = data.iloc[split_idx:]

        print(f"INFO Data split: Train={len(train_data)}, Test={len(test_data)}")
        return train_data, test_data

    def _calculate_strategy_metrics(self, data: pd.DataFrame) -> StrategyMetrics:
        """计算策略指标"""
        if len(data) < 2:
            # 返回默认指标
            return StrategyMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)

        # 计算日收益率
        returns = data['close'].pct_change().dropna()

        # 基础指标
        total_return = (data['close'].iloc[-1] / data['close'].iloc[0]) - 1
        volatility = returns.std() * np.sqrt(252)

        # Sharpe比率 (无风险利率3%)
        excess_returns = returns - 0.03/252
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

        # 最大回撤
        rolling_max = data['close'].expanding().max()
        drawdowns = (data['close'] - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()

        # 胜率
        winning_days = (returns > 0).sum()
        win_rate = winning_days / len(returns)

        # 交易次数估算
        trades_count = self._estimate_trades_count(data)

        # Calmar比率
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Sortino比率
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        sortino_ratio = excess_returns.mean() / downside_std * np.sqrt(252) if downside_std > 0 else 0

        # 利润因子
        winning_returns = returns[returns > 0].sum()
        losing_returns = abs(returns[returns < 0].sum())
        profit_factor = winning_returns / losing_returns if losing_returns > 0 else float('inf')

        return StrategyMetrics(
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            trades_count=trades_count,
            volatility=volatility,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            profit_factor=profit_factor
        )

    def _estimate_trades_count(self, data: pd.DataFrame) -> int:
        """估算交易次数"""
        if len(data) < 20:
            return 0

        # 简单的交易信号检测（基于价格变化）
        returns = data['close'].pct_change().dropna()

        # 假设交易信号基于显著价格变化
        threshold = returns.std() * 0.5
        signals = abs(returns) > threshold

        return signals.sum()

    def _walk_forward_analysis(self, data: pd.DataFrame) -> Dict:
        """Walk-Forward分析"""
        print("Running Walk-Forward Analysis...")

        results = {
            'window_results': [],
            'stability_metrics': {},
            'performance_degradation': 0,
            'trade_frequency': 0,
            'successful_windows': 0
        }

        n_windows = self.config.walk_forward_windows
        window_size = len(data) // (n_windows + 1)

        successful_windows = 0
        trade_counts = []
        performance_scores = []

        for i in range(n_windows):
            # 定义窗口
            train_start = i * window_size
            train_end = (i + 1) * window_size
            test_start = train_end
            test_end = test_start + window_size // 4  # 测试窗口为训练窗口的1/4

            if test_end > len(data):
                break

            train_window = data.iloc[train_start:train_end]
            test_window = data.iloc[test_start:test_end]

            # 计算窗口指标
            train_metrics = self._calculate_strategy_metrics(train_window)
            test_metrics = self._calculate_strategy_metrics(test_window)

            # 记录窗口结果
            window_result = {
                'window': i + 1,
                'train_metrics': asdict(train_metrics),
                'test_metrics': asdict(test_metrics),
                'train_size': len(train_window),
                'test_size': len(test_window)
            }
            results['window_results'].append(window_result)

            # 检查窗口是否成功
            if (test_metrics.trades_count >= self.config.min_trades_per_window and
                test_metrics.sharpe_ratio > 0):
                successful_windows += 1

            trade_counts.append(test_metrics.trades_count)
            if train_metrics.sharpe_ratio > 0:
                performance_scores.append(test_metrics.sharpe_ratio / train_metrics.sharpe_ratio)

        # 计算汇总指标
        results['successful_windows'] = successful_windows
        results['trade_frequency'] = np.mean(trade_counts) if trade_counts else 0

        # 稳定性指标
        if len(performance_scores) > 1:
            stability = 1 - np.std(performance_scores) / np.mean(performance_scores)
            results['stability_metrics']['performance_stability'] = max(0, stability)
        else:
            results['stability_metrics']['performance_stability'] = 0

        # 性能衰减
        if len(results['window_results']) > 0:
            first_performance = results['window_results'][0]['test_metrics']['sharpe_ratio']
            last_performance = results['window_results'][-1]['test_metrics']['sharpe_ratio']

            if first_performance > 0:
                degradation = (first_performance - last_performance) / first_performance
                results['performance_degradation'] = max(0, degradation)

        print(f"SUCCESS Walk-Forward Analysis: {successful_windows}/{n_windows} windows successful")
        return results

    def _statistical_validation(self, train_data: pd.DataFrame, test_data: pd.DataFrame,
                               walk_forward_results: Dict) -> Dict:
        """统计验证"""
        print("Running Statistical Validation...")

        tests = {}

        # 计算收益率序列
        train_returns = train_data['close'].pct_change().dropna()
        test_returns = test_data['close'].pct_change().dropna()

        if len(train_returns) > 10 and len(test_returns) > 10:
            # 1. Sharpe比率显著性检验
            train_sharpe = self._calculate_sharpe_significance(train_returns)
            test_sharpe = self._calculate_sharpe_significance(test_returns)

            tests['sharpe_significance'] = {
                'train': train_sharpe,
                'test': test_sharpe,
                'degradation': (train_sharpe - test_sharpe) / train_sharpe if train_sharpe > 0 else 0
            }

            # 2. 收益率分布稳定性检验 (Kolmogorov-Smirnov test)
            ks_stat, ks_pvalue = stats.ks_2samp(train_returns, test_returns)
            tests['distribution_stability'] = {
                'ks_statistic': ks_stat,
                'p_value': ks_pvalue,
                'is_stable': ks_pvalue > self.config.statistical_significance
            }

            # 3. 自相关性检验
            train_autocorr = self._calculate_autocorrelation(train_returns)
            test_autocorr = self._calculate_autocorrelation(test_returns)

            tests['autocorrelation'] = {
                'train': train_autocorr,
                'test': test_autocorr,
                'stability': 1 - abs(train_autocorr - test_autocorr)
            }

        # 4. Walk-Forward稳定性统计
        if walk_forward_results['window_results']:
            sharpe_scores = [w['test_metrics']['sharpe_ratio']
                           for w in walk_forward_results['window_results']
                           if w['test_metrics']['sharpe_ratio'] > 0]

            if len(sharpe_scores) > 1:
                tests['walk_forward_stability'] = {
                    'mean_sharpe': np.mean(sharpe_scores),
                    'sharpe_std': np.std(sharpe_scores),
                    'coefficient_of_variation': np.std(sharpe_scores) / np.mean(sharpe_scores),
                    'stability_score': 1 - (np.std(sharpe_scores) / np.mean(sharpe_scores))
                }

        # 5. 过拟合检测指标
        tests['overfitting_indicators'] = {
            'trade_frequency': walk_forward_results['trade_frequency'],
            'successful_window_ratio': walk_forward_results['successful_windows'] / len(walk_forward_results['window_results']),
            'performance_degradation': walk_forward_results['performance_degradation']
        }

        print("SUCCESS Statistical Validation completed")
        return tests

    def _calculate_sharpe_significance(self, returns: pd.Series) -> float:
        """计算Sharpe比率的显著性"""
        if len(returns) < 2 or returns.std() == 0:
            return 0

        excess_returns = returns - 0.03/252
        sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

        # 简化的t统计量
        t_stat = sharpe * np.sqrt(len(returns))

        return abs(t_stat)

    def _calculate_autocorrelation(self, returns: pd.Series, lag: int = 1) -> float:
        """计算自相关系数"""
        if len(returns) <= lag:
            return 0

        return returns.autocorr(lag=lag) or 0

    def _assess_overfitting_risk(self, in_sample: StrategyMetrics,
                               out_sample: StrategyMetrics,
                               walk_forward: Dict,
                               statistical_tests: Dict) -> OverfittingRisk:
        """评估过拟合风险"""
        risk_score = 0

        # 1. 样本外表现衰减
        if in_sample.sharpe_ratio > 0:
            sharpe_degradation = (in_sample.sharpe_ratio - out_sample.sharpe_ratio) / in_sample.sharpe_ratio
            if sharpe_degradation > 0.5:
                risk_score += 3
            elif sharpe_degradation > 0.3:
                risk_score += 2
            elif sharpe_degradation > 0.1:
                risk_score += 1

        # 2. Walk-Forward成功率
        successful_ratio = walk_forward['successful_windows'] / len(walk_forward['window_results'])
        if successful_ratio < 0.3:
            risk_score += 3
        elif successful_ratio < 0.5:
            risk_score += 2
        elif successful_ratio < 0.7:
            risk_score += 1

        # 3. 交易频率
        if walk_forward['trade_frequency'] < 2:
            risk_score += 3
        elif walk_forward['trade_frequency'] < 5:
            risk_score += 2
        elif walk_forward['trade_frequency'] < 10:
            risk_score += 1

        # 4. 性能稳定性
        stability = walk_forward['stability_metrics'].get('performance_stability', 0)
        if stability < 0.3:
            risk_score += 2
        elif stability < 0.5:
            risk_score += 1

        # 5. 统计显著性
        if 'distribution_stability' in statistical_tests:
            if not statistical_tests['distribution_stability']['is_stable']:
                risk_score += 2

        # 风险等级判定
        if risk_score >= 8:
            return OverfittingRisk.CRITICAL
        elif risk_score >= 6:
            return OverfittingRisk.HIGH
        elif risk_score >= 3:
            return OverfittingRisk.MEDIUM
        else:
            return OverfittingRisk.LOW

    def _calculate_validation_score(self, in_sample: StrategyMetrics,
                                   out_sample: StrategyMetrics,
                                   walk_forward: Dict,
                                   statistical_tests: Dict,
                                   overfitting_risk: OverfittingRisk) -> float:
        """计算综合验证评分"""
        score = 0

        # 基础分：样本外Sharpe比率
        score += min(out_sample.sharpe_ratio / 2, 20)  # 最高20分

        # 稳定性加分
        stability = walk_forward['stability_metrics'].get('performance_stability', 0)
        score += stability * 15  # 最高15分

        # Walk-Forward成功率加分
        success_ratio = walk_forward['successful_windows'] / len(walk_forward['window_results'])
        score += success_ratio * 20  # 最高20分

        # 交易频率加分
        trade_freq = min(walk_forward['trade_frequency'] / 20, 1)
        score += trade_freq * 10  # 最高10分

        # 统计稳定性加分
        if 'walk_forward_stability' in statistical_tests:
            stat_stability = statistical_tests['walk_forward_stability']['stability_score']
            score += stat_stability * 15  # 最高15分

        # 过拟合风险扣分
        risk_penalties = {
            OverfittingRisk.LOW: 0,
            OverfittingRisk.MEDIUM: 10,
            OverfittingRisk.HIGH: 25,
            OverfittingRisk.CRITICAL: 50
        }
        score -= risk_penalties[overfitting_risk]

        return max(0, min(100, score))

    def _make_validation_decision(self, validation_score: float,
                                overfitting_risk: OverfittingRisk,
                                statistical_tests: Dict) -> bool:
        """验证决策"""
        # 基于验证等级的决策阈值
        thresholds = {
            ValidationLevel.BASIC: 40,
            ValidationLevel.STANDARD: 60,
            ValidationLevel.RIGOROUS: 75,
            ValidationLevel.INSTITUTIONAL: 85
        }

        threshold = thresholds[self.config.validation_level]

        # 如果过拟合风险过高，直接拒绝
        if overfitting_risk in [OverfittingRisk.HIGH, OverfittingRisk.CRITICAL]:
            return False

        # 检查基本统计要求
        if 'overfitting_indicators' in statistical_tests:
            indicators = statistical_tests['overfitting_indicators']
            if indicators['successful_window_ratio'] < 0.3:
                return False
            if indicators['trade_frequency'] < 2:
                return False

        return validation_score >= threshold

    def generate_validation_report(self, results: ValidationResults) -> str:
        """生成验证报告"""
        report = "="*80 + "\n"
        report += f"ANTI-OVERFITTING VALIDATION REPORT\n"
        report += f"Strategy: {results.strategy_name}\n"
        report += f"Validation Level: {self.config.validation_level.value}\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "="*80 + "\n\n"

        # 验证结果摘要
        report += "VALIDATION SUMMARY:\n"
        report += "-"*30 + "\n"
        report += f"Validation Score: {results.validation_score:.2f}/100\n"
        report += f"Overfitting Risk: {results.overfitting_risk.value.upper()}\n"
        report += f"Final Decision: {'✅ ACCEPTED' if results.is_accepted else '❌ REJECTED'}\n\n"

        # 性能对比
        report += "PERFORMANCE COMPARISON:\n"
        report += "-"*30 + "\n"
        report += f"{'Metric':<20} {'In-Sample':<15} {'Out-of-Sample':<15}\n"
        report += f"{'-'*50}\n"

        metrics_to_compare = [
            ('Total Return', 'total_return'),
            ('Sharpe Ratio', 'sharpe_ratio'),
            ('Max Drawdown', 'max_drawdown'),
            ('Win Rate', 'win_rate'),
            ('Trades Count', 'trades_count')
        ]

        for metric_name, metric_attr in metrics_to_compare:
            in_val = getattr(results.in_sample_metrics, metric_attr)
            out_val = getattr(results.out_of_sample_metrics, metric_attr)

            if metric_attr in ['total_return', 'max_drawdown', 'win_rate']:
                in_fmt = f"{in_val:.2%}"
                out_fmt = f"{out_val:.2%}"
            else:
                in_fmt = f"{in_val:.3f}"
                out_fmt = f"{out_val:.3f}"

            report += f"{metric_name:<20} {in_fmt:<15} {out_fmt:<15}\n"

        # Walk-Forward结果
        report += f"\nWALK-FORWARD ANALYSIS:\n"
        report += "-"*30 + "\n"
        wf = results.walk_forward_results
        report += f"Total Windows: {len(wf['window_results'])}\n"
        report += f"Successful Windows: {wf['successful_windows']} ({wf['successful_windows']/len(wf['window_results']):.1%})\n"
        report += f"Average Trades per Window: {wf['trade_frequency']:.1f}\n"
        report += f"Performance Stability: {wf['stability_metrics'].get('performance_stability', 0):.3f}\n"
        report += f"Performance Degradation: {wf['performance_degradation']:.2%}\n"

        # 统计检验结果
        report += f"\nSTATISTICAL TESTS:\n"
        report += "-"*30 + "\n"

        if 'distribution_stability' in results.statistical_tests:
            ds = results.statistical_tests['distribution_stability']
            report += f"Distribution Stability (KS Test): {'STABLE' if ds['is_stable'] else 'UNSTABLE'}\n"
            report += f"  KS Statistic: {ds['ks_statistic']:.4f}\n"
            report += f"  P-Value: {ds['p_value']:.4f}\n"

        if 'overfitting_indicators' in results.statistical_tests:
            oi = results.statistical_tests['overfitting_indicators']
            report += f"\nOverfitting Indicators:\n"
            report += f"  Trade Frequency: {oi['trade_frequency']:.1f} trades/window\n"
            report += f"  Success Window Ratio: {oi['successful_window_ratio']:.1%}\n"
            report += f"  Performance Degradation: {oi['performance_degradation']:.2%}\n"

        # 建议和结论
        report += f"\nRECOMMENDATIONS:\n"
        report += "-"*30 + "\n"

        if not results.is_accepted:
            if results.overfitting_risk == OverfittingRisk.CRITICAL:
                report += "CRITICAL: Strategy shows severe overfitting symptoms\n"
                report += "   Recommendation: Discard strategy completely\n"
            elif results.overfitting_risk == OverfittingRisk.HIGH:
                report += "HIGH RISK: Strategy likely overfitted\n"
                report += "   Recommendation: Major redesign required\n"
            else:
                report += "MEDIUM RISK: Strategy needs improvement\n"
                report += "   Recommendation: Optimize parameters and retest\n"
        else:
            if results.overfitting_risk == OverfittingRisk.LOW:
                report += "EXCELLENT: Strategy passes validation with low risk\n"
                report += "   Recommendation: Ready for production deployment\n"
            else:
                report += "ACCEPTABLE: Strategy passes validation\n"
                report += "   Recommendation: Deploy with monitoring\n"

        return report

    def save_validation_results(self, results: ValidationResults, filename: str = None):
        """保存验证结果"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"anti_overfitting_validation_{timestamp}.json"

        # 转换为可序列化格式
        serializable_data = {
            'strategy_name': results.strategy_name,
            'validation_level': self.config.validation_level.value,
            'validation_timestamp': datetime.now().isoformat(),
            'in_sample_metrics': asdict(results.in_sample_metrics),
            'out_of_sample_metrics': asdict(results.out_of_sample_metrics),
            'walk_forward_results': results.walk_forward_results,
            'statistical_tests': results.statistical_tests,
            'overfitting_risk': results.overfitting_risk.value,
            'validation_score': results.validation_score,
            'is_accepted': results.is_accepted,
            'validation_config': asdict(self.config)
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"SUCCESS Validation results saved to: {filename}")
        return filename

def main():
    """主函数 - 演示抗过拟合框架"""
    print("Starting Anti-Overfitting Framework Demo...")

    # 创建框架实例
    config = ValidationConfig(
        validation_level=ValidationLevel.STANDARD,
        walk_forward_windows=20,
        min_trades_per_window=3
    )

    framework = AntiOverfittingFramework(config)

    # 生成模拟策略数据
    np.random.seed(42)
    dates = pd.date_range('2022-01-01', '2024-12-31', freq='D')

    # 模拟不同质量的策略
    strategies = {
        'good_strategy': generate_strategy_data(dates, quality='good'),
        'medium_strategy': generate_strategy_data(dates, quality='medium'),
        'poor_strategy': generate_strategy_data(dates, quality='poor')
    }

    print(f"INFO Generated {len(strategies)} test strategies")

    # 验证每个策略
    results = {}
    for strategy_name, data in strategies.items():
        print(f"\n{'='*60}")
        validation_result = framework.validate_strategy(data, strategy_name)

        # 生成报告
        report = framework.generate_validation_report(validation_result)
        # 保存报告而不是打印
        with open(f"validation_report_{strategy_name}.txt", "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved for {strategy_name}")

        # 保存结果
        filename = framework.save_validation_results(validation_result)
        results[strategy_name] = {
            'validation_result': validation_result,
            'report_file': filename
        }

    # 汇总结果
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY:")
    print("="*60)

    for strategy_name, result_data in results.items():
        validation = result_data['validation_result']
        status = "ACCEPTED" if validation.is_accepted else "REJECTED"
        risk = validation.overfitting_risk.value.upper()
        score = validation.validation_score

        print(f"{strategy_name:<20}: {score:>6.1f} | {risk:<12} | {status}")

    print(f"Total strategies validated: {len(results)}")
    accepted_count = sum(1 for r in results.values() if r['validation_result'].is_accepted)
    print(f"Strategies accepted: {accepted_count}/{len(results)} ({accepted_count/len(results):.1%})")

    return framework, results

def generate_strategy_data(dates, quality='good'):
    """生成模拟策略数据"""
    np.random.seed(hash(quality) % 10000)

    base_price = 100
    n_days = len(dates)

    if quality == 'good':
        # 好策略：稳定增长，低波动率
        trend = np.linspace(0, 0.5, n_days)
        noise = np.random.randn(n_days) * 0.01
        returns = trend + noise
    elif quality == 'medium':
        # 中等策略：中等表现，不稳定
        trend = np.linspace(0, 0.2, n_days)
        noise = np.random.randn(n_days) * 0.02
        regime_change = np.random.choice([0, -0.1], n_days, p=[0.9, 0.1])
        returns = trend + noise + regime_change
    else:
        # 差策略：过拟合，高波动率
        trend = np.linspace(0, -0.1, n_days)
        noise = np.random.randn(n_days) * 0.03
        random_jumps = np.random.choice([0, 0.1, -0.1], n_days, p=[0.85, 0.075, 0.075])
        returns = trend + noise + random_jumps

    # 计算价格
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, n_days)
    }, index=dates)

    return df

if __name__ == "__main__":
    framework, results = main()