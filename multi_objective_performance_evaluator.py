#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多維性能評估系統
Multi-Objective Performance Evaluation System

為0-300全參數優化提供專業級的多維性能評估、風險管理和帕累托前沿分析
Provides professional-grade multi-objective performance evaluation, risk management, and Pareto frontier analysis for 0-300 parameter optimization
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# 導入核心模塊
from simplified_system.src.backtest.vectorbt_engine import BacktestResult

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指標數據類"""
    # 基本指標
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int

    # 高級風險指標
    var_95: float = 0.0  # 95% VaR
    cvar_95: float = 0.0  # 95% CVaR
    skewness: float = 0.0
    kurtosis: float = 0.0
    tail_ratio: float = 0.0

    # 穩定性指標
    rolling_sharpe_std: float = 0.0
    monthly_hit_rate: float = 0.0
    quarter_consistency: float = 0.0

    # 市場相關性
    beta: float = 0.0
    alpha: float = 0.0
    correlation: float = 0.0
    information_ratio: float = 0.0

@dataclass
class RiskMetrics:
    """風險指標數據類"""
    # 波動率指標
    daily_volatility: float
    annualized_volatility: float
    downside_volatility: float

    # 回撤指標
    max_drawdown: float
    average_drawdown: float
    max_drawdown_duration: int
    recovery_time: int

    # 集中度風險
    concentration_risk: float
    sector_exposure: float = 0.0

@dataclass
class EvaluationConfig:
    """評估配置"""
    # 目標函數權重
    sharpe_weight: float = 0.35
    sortino_weight: float = 0.15
    calmar_weight: float = 0.20
    win_rate_weight: float = 0.15
    consistency_weight: float = 0.10
    risk_adjustment_weight: float = 0.05

    # 風險閾值
    max_acceptable_drawdown: float = 0.25  # 25%
    min_acceptable_sharpe: float = 1.0
    min_acceptable_win_rate: float = 0.40  # 40%

    # 穩定性要求
    min_data_points: int = 252  # 一年交易日
    lookback_periods: List[int] = field(default_factory=lambda: [30, 60, 90, 180])
    consistency_threshold: float = 0.6

class MultiObjectivePerformanceEvaluator:
    """
    多維性能評估系統

    提供專業級的性能評估功能：
    - 多維度風險調整後收益分析
    - 帕累托前沿計算和可視化
    - 統計顯著性檢驗
    - 時間穩定性分析
    - 市場 regime 適應性評估
    """

    def __init__(self, config: Optional[EvaluationConfig] = None):
        """
        初始化多維性能評估系統

        Args:
            config: 評估配置
        """
        self.config = config or EvaluationConfig()

        # 性能評估統計
        self.evaluation_stats = {
            'total_evaluations': 0,
            'strategies_analyzed': 0,
            'pareto_frontiers_computed': 0,
            'risk_assessments_completed': 0
        }

        # 緩存機制
        self.metrics_cache = {}
        self.pareto_cache = {}

        logger.info("Multi-Objective Performance Evaluator initialized")

    def calculate_comprehensive_metrics(
        self,
        backtest_result: BacktestResult,
        benchmark_data: Optional[pd.Series] = None
    ) -> PerformanceMetrics:
        """
        計算綜合性能指標

        Args:
            backtest_result: 回測結果
            benchmark_data: 基準數據（用於計算Alpha/Beta等）

        Returns:
            綜合性能指標
        """
        logger.info("Calculating comprehensive performance metrics...")

        # 提取基本數據
        returns = backtest_result.returns
        equity_curve = backtest_result.equity_curve

        # 計算基本指標
        basic_metrics = self._calculate_basic_metrics(backtest_result)

        # 計算高級風險指標
        advanced_risk_metrics = self._calculate_advanced_risk_metrics(returns)

        # 計算穩定性指標
        stability_metrics = self._calculate_stability_metrics(returns, equity_curve)

        # 計算市場相關性指標
        correlation_metrics = self._calculate_correlation_metrics(returns, benchmark_data)

        # 組合所有指標
        comprehensive_metrics = PerformanceMetrics(
            # 基本指標
            total_return=basic_metrics['total_return'],
            sharpe_ratio=basic_metrics['sharpe_ratio'],
            sortino_ratio=basic_metrics['sortino_ratio'],
            calmar_ratio=basic_metrics['calmar_ratio'],
            max_drawdown=basic_metrics['max_drawdown'],
            win_rate=basic_metrics['win_rate'],
            profit_factor=basic_metrics['profit_factor'],
            total_trades=basic_metrics['total_trades'],

            # 高級風險指標
            var_95=advanced_risk_metrics['var_95'],
            cvar_95=advanced_risk_metrics['cvar_95'],
            skewness=advanced_risk_metrics['skewness'],
            kurtosis=advanced_risk_metrics['kurtosis'],
            tail_ratio=advanced_risk_metrics['tail_ratio'],

            # 穩定性指標
            rolling_sharpe_std=stability_metrics['rolling_sharpe_std'],
            monthly_hit_rate=stability_metrics['monthly_hit_rate'],
            quarter_consistency=stability_metrics['quarter_consistency'],

            # 市場相關性
            beta=correlation_metrics['beta'],
            alpha=correlation_metrics['alpha'],
            correlation=correlation_metrics['correlation'],
            information_ratio=correlation_metrics['information_ratio']
        )

        # 更新統計
        self.evaluation_stats['total_evaluations'] += 1

        return comprehensive_metrics

    def _calculate_basic_metrics(self, result: BacktestResult) -> Dict[str, float]:
        """計算基本性能指標"""
        returns = result.returns

        # 基本指標
        total_return = result.total_return
        sharpe_ratio = result.sharpe_ratio
        max_drawdown = result.max_drawdown
        win_rate = result.win_rate
        profit_factor = result.profit_factor
        total_trades = result.total_trades

        # Sortino比率（下行風險調整）
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = (returns.mean() * 252) / (downside_std * np.sqrt(252)) if downside_std > 0 else 0

        # Calmar比率（回調調整）
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_trades': total_trades
        }

    def _calculate_advanced_risk_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """計算高級風險指標"""
        # VaR和CVaR
        var_95 = returns.quantile(0.05)
        cvar_95 = returns[returns <= var_95].mean()

        # 偏度和峰度
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)

        # 尾部比率（90分位數與10分位數的比率）
        tail_ratio = abs(returns.quantile(0.9)) / abs(returns.quantile(0.1)) if returns.quantile(0.1) != 0 else 0

        return {
            'var_95': var_95,
            'cvar_95': cvar_95,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'tail_ratio': tail_ratio
        }

    def _calculate_stability_metrics(self, returns: pd.Series, equity_curve: pd.Series) -> Dict[str, float]:
        """計算穩定性指標"""
        # 滾動Sharpe比率標準差
        rolling_window = min(60, len(returns) // 4)  # 60天或1/4數據長度
        if rolling_window >= 30:
            rolling_sharpe = returns.rolling(rolling_window).mean() / returns.rolling(rolling_window).std() * np.sqrt(252)
            rolling_sharpe_std = rolling_sharpe.std()
        else:
            rolling_sharpe_std = 0

        # 月度命中率
        monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
        monthly_hit_rate = (monthly_returns > 0).mean() if len(monthly_returns) > 0 else 0

        # 季度一致性（正收益季度比例）
        quarterly_returns = returns.resample('Q').apply(lambda x: (1 + x).prod() - 1)
        quarter_consistency = (quarterly_returns > 0).mean() if len(quarterly_returns) > 0 else 0

        return {
            'rolling_sharpe_std': rolling_sharpe_std,
            'monthly_hit_rate': monthly_hit_rate,
            'quarter_consistency': quarter_consistency
        }

    def _calculate_correlation_metrics(
        self,
        returns: pd.Series,
        benchmark_data: Optional[pd.Series]
    ) -> Dict[str, float]:
        """計算市場相關性指標"""
        if benchmark_data is None or len(benchmark_data) != len(returns):
            # 如果沒有基準數據，使用默認值
            return {
                'beta': 1.0,
                'alpha': 0.0,
                'correlation': 0.0,
                'information_ratio': 0.0
            }

        # 對齊數據
        aligned_data = pd.concat([returns, benchmark_data], axis=1).dropna()
        if len(aligned_data) < 30:  # 數據不足
            return {
                'beta': 1.0,
                'alpha': 0.0,
                'correlation': 0.0,
                'information_ratio': 0.0
            }

        strategy_returns = aligned_data.iloc[:, 0]
        benchmark_returns = aligned_data.iloc[:, 1]

        # 計算相關性
        correlation = strategy_returns.corr(benchmark_returns)

        # 計算Beta
        covariance = strategy_returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0

        # 計算Alpha
        strategy_annual_return = strategy_returns.mean() * 252
        benchmark_annual_return = benchmark_returns.mean() * 252
        alpha = strategy_annual_return - beta * benchmark_annual_return

        # 計算信息比率
        excess_returns = strategy_returns - benchmark_returns
        information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252) if excess_returns.std() > 0 else 0

        return {
            'beta': beta,
            'alpha': alpha,
            'correlation': correlation,
            'information_ratio': information_ratio
        }

    def calculate_composite_score(self, metrics: PerformanceMetrics) -> float:
        """
        計算綜合評分

        Args:
            metrics: 性能指標

        Returns:
            綜合評分（0-100）
        """
        # 標準化各項指標到0-100範圍
        sharpe_score = min(max(metrics.sharpe_ratio * 25, 0), 100)  # Sharpe 4.0 = 100分
        sortino_score = min(max(metrics.sortino_ratio * 20, 0), 100)  # Sortino 5.0 = 100分
        calmar_score = min(max(metrics.calmar_ratio * 50, 0), 100)  # Calmar 2.0 = 100分
        win_rate_score = metrics.win_rate * 100  # 勝率直接轉換

        # 風險調整（回撤控制）
        drawdown_penalty = max(0, abs(metrics.max_drawdown) * 200)  # 25%回撤 = 50分懲罰

        # 穩定性評分
        consistency_score = (
            metrics.monthly_hit_rate * 50 +  # 月度命中率
            metrics.quarter_consistency * 30 +  # 季度一致性
            max(0, (100 - metrics.rolling_sharpe_std * 1000))  # Sharpe穩定性
        )

        # 計算加權綜合評分
        composite_score = (
            sharpe_score * self.config.sharpe_weight +
            sortino_score * self.config.sortino_weight +
            calmar_score * self.config.calmar_weight +
            win_rate_score * self.config.win_rate_weight +
            consistency_score * self.config.consistency_weight
        ) - drawdown_penalty * self.config.risk_adjustment_weight

        # 確保在0-100範圍內
        return max(0, min(100, composite_score))

    def evaluate_strategy_batch(
        self,
        backtest_results: List[BacktestResult],
        benchmark_data: Optional[pd.Series] = None
    ) -> List[Dict[str, Any]]:
        """
        批量評估策略性能

        Args:
            backtest_results: 回測結果列表
            benchmark_data: 基準數據

        Returns:
            評估結果列表
        """
        logger.info(f"Evaluating {len(backtest_results)} strategies...")

        evaluated_strategies = []

        for i, result in enumerate(backtest_results):
            try:
                logger.info(f"Evaluating strategy {i+1}/{len(backtest_results)}")

                # 計算綜合指標
                metrics = self.calculate_comprehensive_metrics(result, benchmark_data)

                # 計算綜合評分
                composite_score = self.calculate_composite_score(metrics)

                # 應用篩選標準
                passed_filters = self._apply_performance_filters(metrics)

                # 風險評估
                risk_assessment = self._assess_strategy_risk(metrics, result)

                strategy_evaluation = {
                    'strategy_name': result.strategy_name,
                    'parameters': result.parameters,
                    'performance_metrics': metrics,
                    'composite_score': composite_score,
                    'passed_filters': passed_filters,
                    'risk_assessment': risk_assessment,
                    'backtest_result': result
                }

                evaluated_strategies.append(strategy_evaluation)

            except Exception as e:
                logger.warning(f"Failed to evaluate strategy {i+1}: {e}")
                continue

        # 更新統計
        self.evaluation_stats['strategies_analyzed'] += len(evaluated_strategies)

        return evaluated_strategies

    def _apply_performance_filters(self, metrics: PerformanceMetrics) -> Dict[str, bool]:
        """應用性能篩選標準"""
        filters = {
            'sharpe_minimum': metrics.sharpe_ratio >= self.config.min_acceptable_sharpe,
            'drawdown_maximum': abs(metrics.max_drawdown) <= self.config.max_acceptable_drawdown,
            'win_rate_minimum': metrics.win_rate >= self.config.min_acceptable_win_rate,
            'positive_returns': metrics.total_return > 0,
            'sufficient_trades': metrics.total_trades >= 10
        }

        # 綜合篩選結果
        filters['all_passed'] = all(filters.values())

        return filters

    def _assess_strategy_risk(self, metrics: PerformanceMetrics, result: BacktestResult) -> Dict[str, Any]:
        """評估策略風險"""
        # 風險等級分類
        risk_level = self._classify_risk_level(metrics)

        # 風險評分（0-100，越低越好）
        risk_score = self._calculate_risk_score(metrics)

        # 風險因子分析
        risk_factors = self._analyze_risk_factors(metrics)

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'recommendations': self._generate_risk_recommendations(risk_level, risk_factors)
        }

    def _classify_risk_level(self, metrics: PerformanceMetrics) -> str:
        """分類風險等級"""
        # 綜合風險評分
        drawdown_risk = abs(metrics.max_drawdown)
        volatility_risk = metrics.rolling_sharpe_std
        tail_risk = abs(metrics.skewness) + abs(metrics.kurtosis)

        overall_risk = (drawdown_risk * 0.5 + volatility_risk * 0.3 + tail_risk * 0.2)

        if overall_risk < 0.1:
            return "LOW"
        elif overall_risk < 0.2:
            return "MEDIUM"
        elif overall_risk < 0.35:
            return "HIGH"
        else:
            return "VERY_HIGH"

    def _calculate_risk_score(self, metrics: PerformanceMetrics) -> float:
        """計算風險評分"""
        # 各項風險指標評分（0-100）
        drawdown_score = min(100, abs(metrics.max_drawdown) * 400)  # 25%回撤 = 100分
        volatility_score = min(100, metrics.rolling_sharpe_std * 500)  # 標準化Sharpe波動
        tail_risk_score = min(100, (abs(metrics.skewness) + abs(metrics.kurtosis)) * 10)
        consistency_score = max(0, 100 - metrics.monthly_hit_rate * 100)  # 月度命中率越低風險越高

        # 加權風險評分
        risk_score = (
            drawdown_score * 0.4 +
            volatility_score * 0.3 +
            tail_risk_score * 0.2 +
            consistency_score * 0.1
        )

        return risk_score

    def _analyze_risk_factors(self, metrics: PerformanceMetrics) -> List[str]:
        """分析風險因子"""
        risk_factors = []

        # 回撤風險
        if abs(metrics.max_drawdown) > 0.2:
            risk_factors.append("HIGH_DRAWDOWN_RISK")

        # Sharpe比率風險
        if metrics.sharpe_ratio < 1.0:
            risk_factors.append("LOW_SHARPE_RATIO")

        # 勝率風險
        if metrics.win_rate < 0.4:
            risk_factors.append("LOW_WIN_RATE")

        # 波動性風險
        if metrics.rolling_sharpe_std > 1.0:
            risk_factors.append("HIGH_VOLATILITY")

        # 尾部風險
        if abs(metrics.skewness) > 1.0 or abs(metrics.kurtosis) > 3.0:
            risk_factors.append("TAIL_RISK")

        # 交易頻率風險
        if metrics.total_trades < 10:
            risk_factors.append("INSUFFICIENT_TRADES")
        elif metrics.total_trades > 1000:
            risk_factors.append("EXCESSIVE_TRADING")

        # 穩定性風險
        if metrics.monthly_hit_rate < 0.5:
            risk_factors.append("POOR_MONTHLY_CONSISTENCY")

        return risk_factors

    def _generate_risk_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """生成風險建議"""
        recommendations = []

        if "HIGH_DRAWDOWN_RISK" in risk_factors:
            recommendations.append("實施更嚴格的止損機制")
            recommendations.append("降低倉位規模")

        if "LOW_SHARPE_RATIO" in risk_factors:
            recommendations.append("優化進場和出場條件")
            recommendations.append("增加趨勢確認濾波器")

        if "LOW_WIN_RATE" in risk_factors:
            recommendations.append("重新評估策略邏輯")
            recommendations.append("增加市場狀態識別")

        if "HIGH_VOLATILITY" in risk_factors:
            recommendations.append("實施波動率調整的倉位管理")
            recommendations.append("增加市場 regime 檢測")

        if "TAIL_RISK" in risk_factors:
            recommendations.append("增加黑天鵝事件防護")
            recommendations.append("實施動態風險預算")

        if "INSUFFICIENT_TRADES" in risk_factors:
            recommendations.append("調整策略參數以增加交易頻率")
            recommendations.append("考慮多時間框架分析")

        if "EXCESSIVE_TRADING" in risk_factors:
            recommendations.append("增加交易濾波器")
            recommendations.append("實施交易成本控制")

        if "POOR_MONTHLY_CONSISTENCY" in risk_factors:
            recommendations.append("增加市場適應性機制")
            recommendations.append("實施季節性調整")

        return recommendations

    def calculate_pareto_frontier(
        self,
        evaluated_strategies: List[Dict[str, Any]],
        objectives: List[str] = None
    ) -> Dict[str, Any]:
        """
        計算帕累托前沿

        Args:
            evaluated_strategies: 評估後的策略列表
            objectives: 優化目標列表

        Returns:
            帕累托前沿分析結果
        """
        if objectives is None:
            objectives = ['sharpe_ratio', 'max_drawdown', 'win_rate', 'composite_score']

        logger.info(f"Calculating Pareto frontier with objectives: {objectives}")

        # 提取目標值
        objective_matrix = []
        strategy_data = []

        for strategy in evaluated_strategies:
            if not strategy['passed_filters'].get('all_passed', False):
                continue

            metrics = strategy['performance_metrics']
            objective_values = []

            for obj in objectives:
                if obj == 'sharpe_ratio':
                    objective_values.append(metrics.sharpe_ratio)
                elif obj == 'max_drawdown':
                    objective_values.append(-abs(metrics.max_drawdown))  # 負號，因為我們希望最小化回撤
                elif obj == 'win_rate':
                    objective_values.append(metrics.win_rate)
                elif obj == 'composite_score':
                    objective_values.append(strategy['composite_score'])
                elif obj == 'sortino_ratio':
                    objective_values.append(metrics.sortino_ratio)
                elif obj == 'calmar_ratio':
                    objective_values.append(metrics.calmar_ratio)

            objective_matrix.append(objective_values)
            strategy_data.append(strategy)

        if not objective_matrix:
            return {
                'pareto_frontier': [],
                'dominated_strategies': len(evaluated_strategies),
                'pareto_efficient_count': 0,
                'efficiency_ratio': 0.0
            }

        # 計算帕累托前沿
        pareto_indices = self._find_pareto_optimal_indices(np.array(objective_matrix))

        # 提取帕累托前沿策略
        pareto_strategies = [strategy_data[i] for i in pareto_indices]
        dominated_strategies = [strategy_data[i] for i in range(len(strategy_data)) if i not in pareto_indices]

        # 更新統計
        self.evaluation_stats['pareto_frontiers_computed'] += 1

        return {
            'pareto_frontier': pareto_strategies,
            'dominated_strategies': dominated_strategies,
            'pareto_efficient_count': len(pareto_strategies),
            'efficiency_ratio': len(pareto_strategies) / len(strategy_data),
            'objectives': objectives,
            'objective_statistics': self._calculate_objective_statistics(objective_matrix, pareto_indices)
        }

    def _find_pareto_optimal_indices(self, objective_matrix: np.ndarray) -> List[int]:
        """找到帕累托最優解的索引"""
        n_solutions = objective_matrix.shape[0]
        pareto_indices = []

        for i in range(n_solutions):
            is_pareto_optimal = True
            current_solution = objective_matrix[i]

            for j in range(n_solutions):
                if i != j:
                    other_solution = objective_matrix[j]

                    # 檢查是否被其他解支配
                    if self._dominates(other_solution, current_solution):
                        is_pareto_optimal = False
                        break

            if is_pareto_optimal:
                pareto_indices.append(i)

        return pareto_indices

    def _dominates(self, solution_a: np.ndarray, solution_b: np.ndarray) -> bool:
        """檢查solution_a是否支配solution_b"""
        better_in_any = False
        worse_in_any = False

        for i in range(len(solution_a)):
            if solution_a[i] > solution_b[i]:
                better_in_any = True
            elif solution_a[i] < solution_b[i]:
                worse_in_any = True

        return better_in_any and not worse_in_any

    def _calculate_objective_statistics(
        self,
        objective_matrix: np.ndarray,
        pareto_indices: List[int]
    ) -> Dict[str, Any]:
        """計算目標統計信息"""
        pareto_objectives = objective_matrix[pareto_indices]

        return {
            'total_solutions': len(objective_matrix),
            'pareto_solutions': len(pareto_indices),
            'objective_means': {
                f'objective_{i}': {
                    'all_time': np.mean(objective_matrix[:, i]),
                    'pareto_frontier': np.mean(pareto_objectives[:, i])
                }
                for i in range(objective_matrix.shape[1])
            },
            'objective_ranges': {
                f'objective_{i}': {
                    'min': np.min(objective_matrix[:, i]),
                    'max': np.max(objective_matrix[:, i]),
                    'std': np.std(objective_matrix[:, i])
                }
                for i in range(objective_matrix.shape[1])
            }
        }

    def generate_performance_report(
        self,
        evaluated_strategies: List[Dict[str, Any]],
        pareto_analysis: Optional[Dict[str, Any]] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        生成性能評估報告

        Args:
            evaluated_strategies: 評估後的策略列表
            pareto_analysis: 帕累托前沿分析結果
            output_file: 輸出文件路徑

        Returns:
            報告內容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report_lines = [
            "# 0700.HK 多維性能評估報告",
            f"生成時間: {timestamp}",
            "",
            "## 評估概況",
            f"- 總評估策略數: {len(evaluated_strategies)}",
            f"- 通過篩選策略數: {sum(1 for s in evaluated_strategies if s['passed_filters'].get('all_passed', False))}",
            f"- 平均綜合評分: {np.mean([s['composite_score'] for s in evaluated_strategies]):.2f}",
            ""
        ]

        # 添加Top 10策略
        top_strategies = sorted(evaluated_strategies, key=lambda x: x['composite_score'], reverse=True)[:10]
        report_lines.extend([
            "## Top 10 策略",
            ""
        ])

        for i, strategy in enumerate(top_strategies, 1):
            metrics = strategy['performance_metrics']
            report_lines.extend([
                f"### {i}. {strategy['strategy_name']}",
                f"- **綜合評分**: {strategy['composite_score']:.2f}",
                f"- **Sharpe比率**: {metrics.sharpe_ratio:.3f}",
                f"- **最大回撤**: {metrics.max_drawdown*100:.2f}%",
                f"- **勝率**: {metrics.win_rate*100:.2f}%",
                f"- **Calmar比率**: {metrics.calmar_ratio:.3f}",
                f"- **Sortino比率**: {metrics.sortino_ratio:.3f}",
                f"- **風險等級**: {strategy['risk_assessment']['risk_level']}",
                f"- **參數**: {strategy['parameters']}",
                ""
            ])

        # 添加帕累托前沿分析
        if pareto_analysis:
            report_lines.extend([
                "## 帕累托前沿分析",
                f"- 帕累托最優策略數: {pareto_analysis['pareto_efficient_count']}",
                f"- 效率比率: {pareto_analysis['efficiency_ratio']:.2%}",
                f"- 被支配策略數: {len(pareto_analysis['dominated_strategies'])}",
                ""
            ])

            if pareto_analysis['pareto_frontier']:
                report_lines.append("### 帕累托前沿策略")
                for i, strategy in enumerate(pareto_analysis['pareto_frontier'][:5], 1):
                    metrics = strategy['performance_metrics']
                    report_lines.extend([
                        f"{i}. Sharpe: {metrics.sharpe_ratio:.3f}, "
                        f"回撤: {metrics.max_drawdown*100:.2f}%, "
                        f"勝率: {metrics.win_rate*100:.2f}%, "
                        f"綜合評分: {strategy['composite_score']:.2f}"
                    ])
                report_lines.append("")

        # 添加風險分析
        risk_levels = [s['risk_assessment']['risk_level'] for s in evaluated_strategies]
        risk_distribution = {
            'LOW': risk_levels.count('LOW'),
            'MEDIUM': risk_levels.count('MEDIUM'),
            'HIGH': risk_levels.count('HIGH'),
            'VERY_HIGH': risk_levels.count('VERY_HIGH')
        }

        report_lines.extend([
            "## 風險分佈",
            f"- 低風險: {risk_distribution['LOW']} ({risk_distribution['LOW']/len(risk_levels):.1%})",
            f"- 中風險: {risk_distribution['MEDIUM']} ({risk_distribution['MEDIUM']/len(risk_levels):.1%})",
            f"- 高風險: {risk_distribution['HIGH']} ({risk_distribution['HIGH']/len(risk_levels):.1%})",
            f"- 極高風險: {risk_distribution['VERY_HIGH']} ({risk_distribution['VERY_HIGH']/len(risk_levels):.1%})",
            ""
        ])

        # 添加建議
        report_lines.extend([
            "## 優化建議",
            "",
            "### 策略改進建議",
            "1. **風險控制**: 對於高回撤策略，實施更嚴格的止損機制",
            "2. **穩定性提升**: 優化參數以提高月度一致性",
            "3. **多目標平衡**: 在Sharpe比率和勝率之間尋找最優平衡點",
            "4. **市場適應性**: 增加市場狀態識別和參數動態調整",
            "",
            "### 實施建議",
            "1. 優先選擇帕累托前沿上的策略",
            "2. 進行更長期的歷史回測驗證",
            "3. 實施敏感性分析和壓力測試",
            "4. 建立實時監控和預警系統",
            ""
        ])

        report_content = '\n'.join(report_lines)

        # 保存報告
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Performance report saved to: {output_file}")

        return report_content

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """獲取評估總結"""
        return {
            'evaluation_statistics': self.evaluation_stats,
            'configuration': {
                'sharpe_weight': self.config.sharpe_weight,
                'sortino_weight': self.config.sortino_weight,
                'calmar_weight': self.config.calmar_weight,
                'win_rate_weight': self.config.win_rate_weight,
                'consistency_weight': self.config.consistency_weight,
                'risk_adjustment_weight': self.config.risk_adjustment_weight,
                'max_acceptable_drawdown': self.config.max_acceptable_drawdown,
                'min_acceptable_sharpe': self.config.min_acceptable_sharpe,
                'min_acceptable_win_rate': self.config.min_acceptable_win_rate
            },
            'cache_size': len(self.metrics_cache),
            'pareto_cache_size': len(self.pareto_cache)
        }

# 便利函數
def quick_performance_evaluation(
    backtest_results: List[BacktestResult],
    top_n: int = 20
) -> Dict[str, Any]:
    """
    快速性能評估

    Args:
        backtest_results: 回測結果列表
        top_n: 返回前N個最優策略

    Returns:
        評估結果
    """
    evaluator = MultiObjectivePerformanceEvaluator()

    # 評估所有策略
    evaluated_strategies = evaluator.evaluate_strategy_batch(backtest_results)

    # 計算帕累托前沿
    pareto_analysis = evaluator.calculate_pareto_frontier(evaluated_strategies)

    # 提取Top策略
    top_strategies = sorted(evaluated_strategies, key=lambda x: x['composite_score'], reverse=True)[:top_n]

    # 生成報告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"performance_evaluation_report_{timestamp}.md"
    evaluator.generate_performance_report(top_strategies, pareto_analysis, report_file)

    return {
        'top_strategies': top_strategies,
        'pareto_analysis': pareto_analysis,
        'evaluation_summary': evaluator.get_evaluation_summary(),
        'report_file': report_file
    }

if __name__ == "__main__":
    # 示例用法
    print("多維性能評估系統已就緒")
    print("使用 quick_performance_evaluation() 函數進行快速評估")