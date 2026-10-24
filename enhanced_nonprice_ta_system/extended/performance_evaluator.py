#!/usr/bin/env python3
"""
Phase 3.3: Performance Evaluation Framework
性能評估框架

Comprehensive performance evaluation system with multi-objective optimization,
overfitting detection, and detailed reporting
"""

import json
import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta
from scipy import stats
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指標數據類"""
    # 收益指標
    total_return: float = 0.0
    annualized_return: float = 0.0
    cagr: float = 0.0  # 複合年增長率

    # 風險指標
    volatility: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0  # 回報/最大回撤

    # 風險調整後收益指標
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0  # 只考慮下行波動率的夏普比率
    information_ratio: float = 0.0

    # 交易統計
    win_rate: float = 0.0
    profit_factor: float = 0.0  # 獲利因子
    avg_trade_return: float = 0.0
    trades_count: int = 0

    # 統計指標
    skewness: float = 0.0
    kurtosis: float = 0.0
    var_95: float = 0.0  # 95%置信區間風險值
    cvar_95: float = 0.0  # 條件風險值

    # 穩定性指標
    stability_score: float = 0.0
    consistency_score: float = 0.0

    # 原始數據
    raw_returns: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    benchmark_returns: List[float] = field(default_factory=list)

@dataclass
class OverfittingDetection:
    """過擬合檢測結果"""
    is_overfitted: bool = False
    overfitting_score: float = 0.0  # 0-1，越高越可能過擬合
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

@dataclass
class EvaluationResult:
    """評估結果"""
    indicator_name: str
    parameters: Dict[str, Any]
    performance_metrics: PerformanceMetrics
    overfitting_detection: OverfittingDetection
    composite_score: float = 0.0
    rank: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

class MultiObjectiveOptimizer:
    """多目標優化器"""

    def __init__(self,
                 objectives: List[Tuple[str, float, str]],  # (metric_name, weight, direction)
                 pareto_frontier_size: int = 50):
        """
        Args:
            objectives: 優化目標列表
                metric_name: 指標名稱
                weight: 權重
                direction: 'maximize' 或 'minimize'
            pareto_frontier_size: 帕累托前沿大小
        """
        self.objectives = objectives
        self.pareto_frontier_size = pareto_frontier_size

    def calculate_composite_score(self, metrics: PerformanceMetrics) -> float:
        """計算綜合得分"""
        score = 0.0
        total_weight = sum(weight for _, weight, _ in self.objectives)

        for metric_name, weight, direction in self.objectives:
            metric_value = getattr(metrics, metric_name, 0)

            if direction == 'maximize':
                # 正向指標，越大越好
                normalized_value = max(0, metric_value)
            else:
                # 負向指標，越小越好（如最大回撤）
                normalized_value = max(0, -metric_value)

            # 使用標準化避免量級差異
            score += (weight / total_weight) * normalized_value

        return score

    def find_pareto_optimal(self, results: List[EvaluationResult]) -> List[EvaluationResult]:
        """尋找帕累托最優解"""
        pareto_optimal = []

        for result in results:
            is_pareto_optimal = True

            for other in results:
                if other == result:
                    continue

                # 檢查是否被其他解支配
                if self._dominates(other, result):
                    is_pareto_optimal = False
                    break

            if is_pareto_optimal:
                pareto_optimal.append(result)

        # 限制前沿大小
        if len(pareto_optimal) > self.pareto_frontier_size:
            # 按綜合得分排序
            pareto_optimal.sort(key=lambda x: x.composite_score, reverse=True)
            pareto_optimal = pareto_optimal[:self.pareto_frontier_size]

        return pareto_optimal

    def _dominates(self, result1: EvaluationResult, result2: EvaluationResult) -> bool:
        """檢查result1是否支配result2"""
        metrics1 = result1.performance_metrics
        metrics2 = result2.performance_metrics

        at_least_one_better = False

        for metric_name, _, direction in self.objectives:
            value1 = getattr(metrics1, metric_name, 0)
            value2 = getattr(metrics2, metric_name, 0)

            if direction == 'maximize':
                if value1 < value2:
                    return False
                if value1 > value2:
                    at_least_one_better = True
            else:
                if value1 > value2:
                    return False
                if value1 < value2:
                    at_least_one_better = True

        return at_least_one_better

class PerformanceEvaluator:
    """性能評估器"""

    def __init__(self,
                 risk_free_rate: float = 0.03,
                 benchmark_return: float = 0.08,
                 enable_overfitting_detection: bool = True,
                 min_trades_for_evaluation: int = 30):
        """
        Args:
            risk_free_rate: 無風險利率（年化）
            benchmark_return: 基準回報率（年化）
            enable_overfitting_detection: 是否啟用過擬合檢測
            min_trades_for_evaluation: 評估所需的最少交易次數
        """
        self.risk_free_rate = risk_free_rate
        self.benchmark_return = benchmark_return
        self.enable_overfitting_detection = enable_overfitting_detection
        self.min_trades_for_evaluation = min_trades_for_evaluation

        # 初始化多目標優化器
        self.multi_objective_optimizer = MultiObjectiveOptimizer([
            ("sharpe_ratio", 0.4, "maximize"),
            ("total_return", 0.25, "maximize"),
            ("max_drawdown", 0.2, "minimize"),
            ("stability_score", 0.15, "maximize")
        ])

    def evaluate_strategy(self,
                         indicator_name: str,
                         parameters: Dict[str, Any],
                         returns_data: List[float],
                         benchmark_data: List[float] = None,
                         trades_data: List[Dict] = None) -> EvaluationResult:
        """
        評估策略性能

        Args:
            indicator_name: 指標名稱
            parameters: 參數配置
            returns_data: 收益序列
            benchmark_data: 基準收益序列
            trades_data: 交易數據列表

        Returns:
            評估結果
        """
        if len(returns_data) < 10:
            logger.warning(f"Insufficient data for evaluation: {len(returns_data)} returns")
            return self._create_invalid_result(indicator_name, parameters)

        # 計算性能指標
        performance_metrics = self._calculate_performance_metrics(
            returns_data, benchmark_data, trades_data
        )

        # 過擬合檢測
        overfitting_detection = OverfittingDetection()
        if self.enable_overfitting_detection:
            overfitting_detection = self._detect_overfitting(
                indicator_name, parameters, performance_metrics, returns_data
            )

        # 計算綜合得分
        composite_score = self.multi_objective_optimizer.calculate_composite_score(
            performance_metrics
        )

        return EvaluationResult(
            indicator_name=indicator_name,
            parameters=parameters,
            performance_metrics=performance_metrics,
            overfitting_detection=overfitting_detection,
            composite_score=composite_score
        )

    def _calculate_performance_metrics(self,
                                     returns_data: List[float],
                                     benchmark_data: List[float] = None,
                                     trades_data: List[Dict] = None) -> PerformanceMetrics:
        """計算性能指標"""
        if not returns_data:
            return PerformanceMetrics()

        returns = np.array(returns_data)
        equity_curve = np.cumprod(1 + returns)

        # 基本收益指標
        total_return = (equity_curve[-1] - 1)
        annualized_return = total_return * (252 / len(returns))  # 假設252個交易日

        # CAGR (複合年增長率)
        years = len(returns) / 252.0
        cagr = (equity_curve[-1] ** (1/years) - 1) if years > 0 else 0

        # 風險指標
        volatility = np.std(returns) * np.sqrt(252)
        rolling_max = np.maximum.accumulate(equity_curve)
        drawdowns = (equity_curve - rolling_max) / rolling_max
        max_drawdown = np.min(drawdowns)
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # 風險調整後收益指標
        excess_return = annualized_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0

        # Sortino Ratio (只考慮下行波動)
        downside_returns = returns[returns < 0]
        downside_volatility = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
        sortino_ratio = excess_return / downside_volatility if downside_volatility > 0 else 0

        # Information Ratio
        if benchmark_data:
            benchmark = np.array(benchmark_data)
            excess_returns = returns - benchmark
            tracking_error = np.std(excess_returns) * np.sqrt(252)
            information_ratio = np.mean(excess_returns) * 252 / tracking_error if tracking_error > 0 else 0
        else:
            information_ratio = 0

        # 交易統計
        win_rate = 0
        profit_factor = 0
        avg_trade_return = 0
        trades_count = 0

        if trades_data:
            trades_returns = [trade.get('return', 0) for trade in trades_data]
            trades_count = len(trades_returns)

            if trades_count > 0:
                winning_trades = [r for r in trades_returns if r > 0]
                losing_trades = [r for r in trades_returns if r < 0]

                win_rate = len(winning_trades) / trades_count
                avg_trade_return = np.mean(trades_returns)

                total_wins = sum(winning_trades) if winning_trades else 0
                total_losses = abs(sum(losing_trades)) if losing_trades else 0
                profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        # 統計指標
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        var_95 = np.percentile(returns, 5)
        cvar_95 = np.mean(returns[returns <= var_95]) if len(returns[returns <= var_95]) > 0 else 0

        # 穩定性指標
        stability_score = self._calculate_stability_score(returns)
        consistency_score = self._calculate_consistency_score(returns)

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            cagr=cagr,
            volatility=volatility,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            information_ratio=information_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_trade_return=avg_trade_return,
            trades_count=trades_count,
            skewness=skewness,
            kurtosis=kurtosis,
            var_95=var_95,
            cvar_95=cvar_95,
            stability_score=stability_score,
            consistency_score=consistency_score,
            raw_returns=returns.tolist(),
            equity_curve=equity_curve.tolist(),
            benchmark_returns=benchmark_data if benchmark_data else []
        )

    def _calculate_stability_score(self, returns: List[float]) -> float:
        """計算穩定性得分"""
        if len(returns) < 20:
            return 0.0

        returns_array = np.array(returns)

        # 滾動窗口夏普比率
        window = min(30, len(returns) // 4)
        rolling_sharpe = []

        for i in range(window, len(returns_array)):
            window_returns = returns_array[i-window:i]
            excess_return = np.mean(window_returns) * 252 - self.risk_free_rate
            volatility = np.std(window_returns) * np.sqrt(252)
            sharpe = excess_return / volatility if volatility > 0 else 0
            rolling_sharpe.append(sharpe)

        if len(rolling_sharpe) == 0:
            return 0.0

        # 穩定性 = 1 - 滾動夏普比率的標準差
        sharpe_std = np.std(rolling_sharpe)
        stability = max(0, 1 - sharpe_std)

        return stability

    def _calculate_consistency_score(self, returns: List[float]) -> float:
        """計算一致性得分"""
        if len(returns) < 10:
            return 0.0

        returns_array = np.array(returns)

        # 正收益比例
        positive_returns = np.sum(returns_array > 0)
        consistency = positive_returns / len(returns_array)

        # 考慮收益分布的穩定性
        if len(returns_array) >= 20:
            # 分為兩半，檢查前後一致性
            mid = len(returns_array) // 2
            first_half = returns_array[:mid]
            second_half = returns_array[mid:]

            first_mean = np.mean(first_half)
            second_mean = np.mean(second_half)

            # 一致性懲罰前後差異
            mean_diff = abs(first_mean - second_mean)
            consistency -= min(mean_diff * 10, 0.5)  # 懲罰最多0.5

        return max(0, consistency)

    def _detect_overfitting(self,
                           indicator_name: str,
                           parameters: Dict[str, Any],
                           metrics: PerformanceMetrics,
                           returns_data: List[float]) -> OverfittingDetection:
        """檢測過擬合"""
        detection = OverfittingDetection()
        warnings_list = []
        recommendations = []

        # 檢查1: 交易次數過少
        if metrics.trades_count < self.min_trades_for_evaluation:
            warnings_list.append(f"交易次數過少 ({metrics.trades_count} < {self.min_trades_for_evaluation})")
            recommendations.append("增加數據長度或調整參數以增加交易頻率")
            detection.overfitting_score += 0.3

        # 檢查2: 夏普比率異常高
        if metrics.sharpe_ratio > 3.0:
            warnings_list.append(f"夏普比率異常高 ({metrics.sharpe_ratio:.2f})")
            recommendations.append("檢查是否有前視偏差或數據窺探")
            detection.overfitting_score += 0.25

        # 檢查3: 最大回撤異常小
        if metrics.max_drawdown > -0.05:  # 回撤小於5%
            warnings_list.append(f"最大回撤異常小 ({metrics.max_drawdown:.2%})")
            recommendations.append("可能存在過度擬合風險，建議使用更長的回測期")
            detection.overfitting_score += 0.2

        # 檢查4: 參數過多或過於精細
        param_complexity = 0
        for param_name, param_value in parameters.items():
            if isinstance(param_value, float):
                if abs(param_value) < 0.01:  # 非常精細的浮點參數
                    param_complexity += 0.1
            elif isinstance(param_value, int):
                if param_value > 100 or param_value < 5:  # 極端參數
                    param_complexity += 0.1

        if param_complexity > 0.2:
            warnings_list.append("參數配置過於複雜")
            recommendations.append("簡化參數配置，使用更常見的數值")
            detection.overfitting_score += param_complexity

        # 檢查5: 收益分布異常
        if len(returns_data) >= 20:
            returns_array = np.array(returns_data)

            # 檢查偏度和峰度
            if abs(metrics.skewness) > 3:
                warnings_list.append(f"收益偏度異常 ({metrics.skewness:.2f})")
                detection.overfitting_score += 0.15

            if metrics.kurtosis > 5:
                warnings_list.append(f"收益峰度異常 ({metrics.kurtosis:.2f})")
                detection.overfitting_score += 0.15

        # 檢查6: 穩定性得分低
        if metrics.stability_score < 0.3:
            warnings_list.append(f"策略穩定性較低 ({metrics.stability_score:.2f})")
            recommendations.append("考慮使用樣本外測試驗證策略穩定性")
            detection.overfitting_score += 0.2

        # 確定是否過擬合
        detection.is_overfitted = detection.overfitting_score > 0.5
        detection.warnings = warnings_list
        detection.recommendations = recommendations

        return detection

    def _create_invalid_result(self, indicator_name: str, parameters: Dict[str, Any]) -> EvaluationResult:
        """創建無效評估結果"""
        return EvaluationResult(
            indicator_name=indicator_name,
            parameters=parameters,
            performance_metrics=PerformanceMetrics(),
            overfitting_detection=OverfittingDetection(
                is_overfitted=True,
                overfitting_score=1.0,
                warnings=["數據不足無法評估"],
                recommendations=["增加數據長度"]
            ),
            composite_score=0.0
        )

    def rank_results(self, results: List[EvaluationResult]) -> List[EvaluationResult]:
        """對結果進行排名"""
        # 過濾掉無效結果
        valid_results = [r for r in results if r.performance_metrics.sharpe_ratio > -999]

        # 按綜合得分排序
        valid_results.sort(key=lambda x: x.composite_score, reverse=True)

        # 分配排名
        for i, result in enumerate(valid_results, 1):
            result.rank = i

        return valid_results

    def get_pareto_frontier(self, results: List[EvaluationResult]) -> List[EvaluationResult]:
        """獲取帕累托前沿"""
        valid_results = [r for r in results if r.performance_metrics.sharpe_ratio > -999]
        return self.multi_objective_optimizer.find_pareto_optimal(valid_results)

    def generate_evaluation_report(self,
                                 results: List[EvaluationResult],
                                 output_file: str = None) -> str:
        """生成評估報告"""
        if not results:
            logger.warning("No results to generate report")
            return ""

        # 有效結果統計
        valid_results = [r for r in results if r.performance_metrics.sharpe_ratio > -999]
        overfitted_results = [r for r in valid_results if r.overfitting_detection.is_overfitted]

        # 創建報告
        report = {
            "summary": {
                "total_results": len(results),
                "valid_results": len(valid_results),
                "overfitted_results": len(overfitted_results),
                "evaluation_time": datetime.now().isoformat()
            },
            "top_strategies": [],
            "performance_statistics": {},
            "overfitting_analysis": {},
            "pareto_frontier": []
        }

        # Top 10 策略
        top_strategies = self.rank_results(valid_results)[:10]
        for result in top_strategies:
            report["top_strategies"].append({
                "rank": result.rank,
                "indicator": result.indicator_name,
                "parameters": result.parameters,
                "composite_score": result.composite_score,
                "sharpe_ratio": result.performance_metrics.sharpe_ratio,
                "total_return": result.performance_metrics.total_return,
                "max_drawdown": result.performance_metrics.max_drawdown,
                "is_overfitted": result.overfitting_detection.is_overfitted
            })

        # 性能統計
        if valid_results:
            sharpe_ratios = [r.performance_metrics.sharpe_ratio for r in valid_results]
            total_returns = [r.performance_metrics.total_return for r in valid_results]
            max_drawdowns = [r.performance_metrics.max_drawdown for r in valid_results]

            report["performance_statistics"] = {
                "sharpe_ratio": {
                    "mean": np.mean(sharpe_ratios),
                    "std": np.std(sharpe_ratios),
                    "min": np.min(sharpe_ratios),
                    "max": np.max(sharpe_ratios),
                    "median": np.median(sharpe_ratios)
                },
                "total_return": {
                    "mean": np.mean(total_returns),
                    "std": np.std(total_returns),
                    "min": np.min(total_returns),
                    "max": np.max(total_returns),
                    "median": np.median(total_returns)
                },
                "max_drawdown": {
                    "mean": np.mean(max_drawdowns),
                    "std": np.std(max_drawdowns),
                    "min": np.min(max_drawdowns),
                    "max": np.max(max_drawdowns),
                    "median": np.median(max_drawdowns)
                }
            }

        # 過擬合分析
        if overfitted_results:
            overfitting_scores = [r.overfitting_detection.overfitting_score for r in overfitted_results]
            common_warnings = {}

            for result in overfitted_results:
                for warning in result.overfitting_detection.warnings:
                    common_warnings[warning] = common_warnings.get(warning, 0) + 1

            report["overfitting_analysis"] = {
                "overfitting_rate": len(overfitted_results) / len(valid_results),
                "avg_overfitting_score": np.mean(overfitting_scores),
                "common_warnings": common_warnings
            }

        # 帕累托前沿
        pareto_results = self.get_pareto_frontier(valid_results)
        for result in pareto_results:
            report["pareto_frontier"].append({
                "indicator": result.indicator_name,
                "parameters": result.parameters,
                "composite_score": result.composite_score,
                "sharpe_ratio": result.performance_metrics.sharpe_ratio,
                "total_return": result.performance_metrics.total_return,
                "max_drawdown": result.performance_metrics.max_drawdown
            })

        # 保存報告
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"evaluation_report_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Evaluation report generated: {output_file}")
        return output_file

if __name__ == "__main__":
    # 測試代碼
    logging.basicConfig(level=logging.INFO)

    # 創建評估器
    evaluator = PerformanceEvaluator(risk_free_rate=0.03)

    # 模擬數據
    np.random.seed(42)
    returns_data = np.random.normal(0.001, 0.02, 252).tolist()  # 一年交易日
    benchmark_data = np.random.normal(0.0005, 0.015, 252).tolist()

    # 模擬交易數據
    trades_data = [
        {"return": 0.05, "date": "2024-01-01"},
        {"return": -0.02, "date": "2024-01-15"},
        {"return": 0.03, "date": "2024-02-01"},
        {"return": 0.08, "date": "2024-02-15"}
    ]

    # 評估策略
    result = evaluator.evaluate_strategy(
        indicator_name="RSI",
        parameters={"period": 14, "oversold": 30, "overbought": 70},
        returns_data=returns_data,
        benchmark_data=benchmark_data,
        trades_data=trades_data
    )

    print("Performance Evaluation Result:")
    print(f"Indicator: {result.indicator_name}")
    print(f"Sharpe Ratio: {result.performance_metrics.sharpe_ratio:.3f}")
    print(f"Total Return: {result.performance_metrics.total_return:.3f}")
    print(f"Max Drawdown: {result.performance_metrics.max_drawdown:.3f}")
    print(f"Composite Score: {result.composite_score:.3f}")
    print(f"Overfitted: {result.overfitting_detection.is_overfitted}")
    print(f"Overfitting Score: {result.overfitting_detection.overfitting_score:.3f}")

    if result.overfitting_detection.warnings:
        print("Warnings:")
        for warning in result.overfitting_detection.warnings:
            print(f"  - {warning}")