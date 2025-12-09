"""
Result Aggregation and Analysis Framework for Unified Backtesting

Comprehensive result aggregation system that processes, analyzes, and visualizes
backtesting results from large-scale parameter optimization with intelligent
ranking, statistical analysis, and insight generation.

Key Features:
- Real-time result aggregation from multi-process execution
- Intelligent parameter ranking and selection algorithms
- Statistical analysis and performance attribution
- Risk-adjusted performance comparison
- Parameter sensitivity analysis
- Ensemble strategy generation
- Comprehensive reporting and visualization
- Performance validation and robustness testing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union, Iterator
from dataclasses import dataclass, asdict
import logging
import json
import time
from collections import defaultdict, Counter
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

from ..vectorbt_engine.engine import BacktestResult, BatchResult

logger = logging.getLogger(__name__)


@dataclass
class AggregatedResults:
    """Aggregated backtesting results structure"""
    total_combinations: int
    successful_combinations: int
    failed_combinations: int
    success_rate: float

    # Performance Statistics
    performance_stats: Dict[str, float]
    parameter_importance: Dict[str, float]
    correlation_matrix: pd.DataFrame

    # Top Performers
    top_sharpe_results: List[BacktestResult]
    top_return_results: List[BacktestResult]
    top_calmar_results: List[BacktestResult]

    # Risk Analysis
    risk_distribution: Dict[str, Any]
    drawdown_analysis: Dict[str, float]

    # Parameter Analysis
    parameter_sensitivity: Dict[str, Dict]
    optimal_parameters: Dict[str, Any]

    # Robustness Analysis
    stability_metrics: Dict[str, float]
    ensemble_candidates: List[Dict[str, Any]]

    # Metadata
    processing_time: float
    strategy_name: str
    config: Dict[str, Any]

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return asdict(self)


class ParameterRanker:
    """Advanced parameter ranking and selection algorithms"""

    def __init__(self):
        self.ranking_methods = {
            'sharpe_ratio': self._rank_by_sharpe,
            'composite_score': self._rank_by_composite,
            'risk_adjusted': self._rank_by_risk_adjusted,
            'stability_weighted': self._rank_by_stability,
            'ensemble_optimal': self._rank_for_ensemble
        }

    def rank_parameters(self, results: List[BacktestResult],
                       method: str = 'composite_score',
                       top_n: int = 10) -> List[BacktestResult]:
        """
        Rank parameters using specified method

        Args:
            results: List of backtest results
            method: Ranking method to use
            top_n: Number of top results to return

        Returns:
            Ranked list of backtest results
        """
        if method not in self.ranking_methods:
            raise ValueError(f"Unknown ranking method: {method}")

        # Filter successful results
        successful_results = [r for r in results if r.error is None]
        if not successful_results:
            return []

        # Apply ranking method
        ranking_func = self.ranking_methods[method]
        ranked_results = ranking_func(successful_results)

        return ranked_results[:top_n]

    def _rank_by_sharpe(self, results: List[BacktestResult]) -> List[BacktestResult]:
        """Rank by Sharpe ratio"""
        return sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)

    def _rank_by_composite(self, results: List[BacktestResult]) -> List[BacktestResult]:
        """Rank by composite score (multiple metrics)"""
        def composite_score(result):
            # Normalize metrics to 0-1 range
            sharpe_norm = min(max(result.sharpe_ratio / 3.0, 0), 1)  # Assuming 3.0 as excellent Sharpe
            return_norm = min(max(result.total_return / 2.0, 0), 1)  # Assuming 200% as excellent return
            calmar_norm = min(max(result.calmar_ratio / 2.0, 0), 1)  # Assuming 2.0 as excellent Calmar
            win_rate_norm = result.win_rate

            # Weighted composite score
            return (0.4 * sharpe_norm +
                   0.3 * return_norm +
                   0.2 * calmar_norm +
                   0.1 * win_rate_norm)

        return sorted(results, key=composite_score, reverse=True)

    def _rank_by_risk_adjusted(self, results: List[BacktestResult]) -> List[BacktestResult]:
        """Rank by risk-adjusted performance"""
        def risk_adjusted_score(result):
            # Penalize high drawdowns and volatility
            drawdown_penalty = max(0, result.max_drawdown / 0.3)  # 30% max drawdown threshold
            volatility_penalty = max(0, result.volatility / 0.4)  # 40% annual volatility threshold

            return (result.sharpe_ratio *
                   (1 - drawdown_penalty) *
                   (1 - volatility_penalty))

        return sorted(results, key=risk_adjusted_score, reverse=True)

    def _rank_by_stability(self, results: List[BacktestResult]) -> List[BacktestResult]:
        """Rank by stability and consistency"""
        def stability_score(result):
            # Favor strategies with more trades and higher win rates
            trade_count_factor = min(result.trades_count / 100, 1)  # Normalize to 100 trades
            win_rate_factor = result.win_rate
            profit_factor_factor = min(result.profit_factor / 2, 1)  # Normalize to 2.0

            return (trade_count_factor * 0.4 +
                   win_rate_factor * 0.3 +
                   profit_factor_factor * 0.3)

        return sorted(results, key=stability_score, reverse=True)

    def _rank_for_ensemble(self, results: List[BacktestResult]) -> List[BacktestResult]:
        """Rank for ensemble construction (diversification-focused)"""
        # Simple ranking for now - can be enhanced with correlation analysis
        return self._rank_by_composite(results)


class StatisticalAnalyzer:
    """Statistical analysis of backtesting results"""

    def analyze_performance_distribution(self, results: List[BacktestResult]) -> Dict[str, Any]:
        """Analyze performance metric distributions"""
        successful_results = [r for r in results if r.error is None]
        if not successful_results:
            return {}

        metrics = ['sharpe_ratio', 'total_return', 'max_drawdown', 'calmar_ratio', 'win_rate']
        analysis = {}

        for metric in metrics:
            values = [getattr(r, metric) for r in successful_results]
            analysis[metric] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'median': np.median(values),
                'percentile_25': np.percentile(values, 25),
                'percentile_75': np.percentile(values, 75),
                'skewness': stats.skew(values),
                'kurtosis': stats.kurtosis(values)
            }

        return analysis

    def calculate_parameter_importance(self, results: List[BacktestResult]) -> Dict[str, float]:
        """Calculate importance of each parameter for performance"""
        successful_results = [r for r in results if r.error is None]
        if not successful_results:
            return {}

        # Extract parameters and performance
        param_data = []
        performance_data = []

        for result in successful_results:
            param_dict = {}
            for key, value in result.parameters.items():
                if isinstance(value, (int, float)):
                    param_dict[key] = value
                else:
                    # Encode categorical parameters
                    param_dict[key] = hash(str(value)) % 1000

            param_data.append(list(param_dict.values()))
            performance_data.append(result.sharpe_ratio)  # Use Sharpe as target

        if not param_data:
            return {}

        # Calculate correlation between parameters and performance
        param_array = np.array(param_data)
        performance_array = np.array(performance_data)

        correlations = []
        for i in range(param_array.shape[1]):
            if np.std(param_array[:, i]) > 0:
                corr = np.corrcoef(param_array[:, i], performance_array)[0, 1]
                correlations.append(abs(corr) if not np.isnan(corr) else 0)
            else:
                correlations.append(0)

        # Map back to parameter names
        param_names = list(successful_results[0].parameters.keys())
        importance = dict(zip(param_names, correlations))

        return importance

    def analyze_correlations(self, results: List[BacktestResult]) -> pd.DataFrame:
        """Analyze correlations between performance metrics"""
        successful_results = [r for r in results if r.error is None]
        if len(successful_results) < 2:
            return pd.DataFrame()

        # Extract performance metrics
        metrics_data = []
        metric_names = ['sharpe_ratio', 'total_return', 'max_drawdown', 'calmar_ratio',
                       'win_rate', 'profit_factor', 'volatility', 'trades_count']

        for result in successful_results:
            metrics_data.append([getattr(result, metric) for metric in metric_names])

        metrics_df = pd.DataFrame(metrics_data, columns=metric_names)
        correlation_matrix = metrics_df.corr()

        return correlation_matrix


class ResultAggregator:
    """
    Comprehensive result aggregation and analysis system

    Processes and analyzes backtesting results from large-scale parameter
    optimization with intelligent ranking and statistical analysis.
    """

    def __init__(self, config=None):
        """Initialize result aggregator"""
        if config is None:
            from ..core.config import DEFAULT_CONFIG
            config = DEFAULT_CONFIG

        self.config = config
        self.ranker = ParameterRanker()
        self.analyzer = StatisticalAnalyzer()

        # Result storage
        self.all_results = []
        self.batch_results = []
        self.processing_start_time = None

        logger.info("Initialized ResultAggregator")

    def add_batch_result(self, batch_result: BatchResult):
        """Add batch result to aggregation"""
        self.batch_results.append(batch_result)
        self.all_results.extend(batch_result.results)

        logger.debug(f"Added batch {batch_result.batch_index}: "
                    f"{batch_result.successful_count}/{batch_result.total_combinations} successful")

    def start_aggregation(self, strategy_name: str):
        """Start result aggregation process"""
        self.processing_start_time = time.time()
        self.strategy_name = strategy_name
        logger.info(f"Started result aggregation for {strategy_name}")

    def finalize_aggregation(self) -> AggregatedResults:
        """Finalize aggregation and return comprehensive results"""
        if self.processing_start_time is None:
            raise ValueError("Aggregation not started")

        processing_time = time.time() - self.processing_start_time
        total_combinations = len(self.all_results)
        successful_combinations = len([r for r in self.all_results if r.error is None])
        failed_combinations = total_combinations - successful_combinations
        success_rate = successful_combinations / total_combinations if total_combinations > 0 else 0

        logger.info(f"Finalizing aggregation: {successful_combinations}/{total_combinations} successful "
                   f"({success_rate:.1%}) in {processing_time:.1f}s")

        # Generate comprehensive analysis
        performance_stats = self.analyzer.analyze_performance_distribution(self.all_results)
        parameter_importance = self.analyzer.calculate_parameter_importance(self.all_results)
        correlation_matrix = self.analyzer.analyze_correlations(self.all_results)

        # Get top performers
        top_sharpe = self.ranker.rank_parameters(self.all_results, 'sharpe_ratio', 10)
        top_return = self.ranker.rank_parameters(self.all_results, 'total_return', 10)
        top_calmar = self.ranker.rank_parameters(self.all_results, 'calmar_ratio', 10)

        # Risk analysis
        risk_distribution = self._analyze_risk_distribution()
        drawdown_analysis = self._analyze_drawdowns()

        # Parameter analysis
        parameter_sensitivity = self._analyze_parameter_sensitivity()
        optimal_parameters = self._find_optimal_parameters()

        # Robustness analysis
        stability_metrics = self._calculate_stability_metrics()
        ensemble_candidates = self._find_ensemble_candidates()

        return AggregatedResults(
            total_combinations=total_combinations,
            successful_combinations=successful_combinations,
            failed_combinations=failed_combinations,
            success_rate=success_rate,

            performance_stats=performance_stats,
            parameter_importance=parameter_importance,
            correlation_matrix=correlation_matrix,

            top_sharpe_results=top_sharpe,
            top_return_results=top_return,
            top_calmar_results=top_calmar,

            risk_distribution=risk_distribution,
            drawdown_analysis=drawdown_analysis,

            parameter_sensitivity=parameter_sensitivity,
            optimal_parameters=optimal_parameters,

            stability_metrics=stability_metrics,
            ensemble_candidates=ensemble_candidates,

            processing_time=processing_time,
            strategy_name=self.strategy_name,
            config=self.config.to_dict()
        )

    def _analyze_risk_distribution(self) -> Dict[str, Any]:
        """Analyze risk distribution across results"""
        successful_results = [r for r in self.all_results if r.error is None]
        if not successful_results:
            return {}

        max_drawdowns = [r.max_drawdown for r in successful_results]
        volatilities = [r.volatility for r in successful_results]

        return {
            'max_drawdown': {
                'mean': np.mean(max_drawdowns),
                'std': np.std(max_drawdowns),
                'percentile_95': np.percentile(max_drawdowns, 95),
                'worst_case': np.max(max_drawdowns)
            },
            'volatility': {
                'mean': np.mean(volatilities),
                'std': np.std(volatilities),
                'percentile_95': np.percentile(volatilities, 95)
            },
            'risk_categories': {
                'low_risk': len([r for r in successful_results if r.max_drawdown < 0.1 and r.volatility < 0.15]),
                'medium_risk': len([r for r in successful_results if 0.1 <= r.max_drawdown < 0.2 or 0.15 <= r.volatility < 0.25]),
                'high_risk': len([r for r in successful_results if r.max_drawdown >= 0.2 or r.volatility >= 0.25])
            }
        }

    def _analyze_drawdowns(self) -> Dict[str, float]:
        """Analyze drawdown characteristics"""
        successful_results = [r for r in self.all_results if r.error is None]
        if not successful_results:
            return {}

        max_drawdowns = [r.max_drawdown for r in successful_results]

        return {
            'average_max_drawdown': np.mean(max_drawdowns),
            'worst_max_drawdown': np.max(max_drawdowns),
            'drawdown_volatility': np.std(max_drawdowns),
            'percent_with_acceptable_drawdown': len([r for r in successful_results if r.max_drawdown < 0.2]) / len(successful_results)
        }

    def _analyze_parameter_sensitivity(self) -> Dict[str, Dict]:
        """Analyze parameter sensitivity to performance"""
        successful_results = [r for r in self.all_results if r.error is None]
        if not successful_results:
            return {}

        sensitivity = {}

        # Group results by each parameter value
        for param_name in successful_results[0].parameters.keys():
            param_values = defaultdict(list)
            performances = defaultdict(list)

            for result in successful_results:
                param_value = result.parameters.get(param_name)
                if param_value is not None:
                    param_values[param_value].append(param_value)
                    performances[param_value].append(result.sharpe_ratio)

            # Calculate sensitivity for each parameter value
            param_sensitivity = {}
            for value in performances:
                if len(performances[value]) > 1:
                    param_sensitivity[value] = {
                        'mean_performance': np.mean(performances[value]),
                        'performance_std': np.std(performances[value]),
                        'sample_count': len(performances[value]),
                        'coefficient_of_variation': np.std(performances[value]) / np.mean(performances[value]) if np.mean(performances[value]) != 0 else float('inf')
                    }

            sensitivity[param_name] = param_sensitivity

        return sensitivity

    def _find_optimal_parameters(self) -> Dict[str, Any]:
        """Find optimal parameter combinations"""
        top_results = self.ranker.rank_parameters(self.all_results, 'composite_score', 5)

        if not top_results:
            return {}

        best_result = top_results[0]

        # Analyze parameter patterns in top results
        param_frequency = defaultdict(Counter)
        for result in top_results:
            for param_name, param_value in result.parameters.items():
                param_frequency[param_name][param_value] += 1

        # Find most common parameter values
        common_params = {}
        for param_name, counter in param_frequency.items():
            if counter:
                most_common = counter.most_common(1)[0]
                common_params[param_name] = {
                    'value': most_common[0],
                    'frequency': most_common[1] / len(top_results)
                }

        return {
            'best_single': best_result.parameters,
            'best_performance': {
                'sharpe_ratio': best_result.sharpe_ratio,
                'total_return': best_result.total_return,
                'max_drawdown': best_result.max_drawdown
            },
            'common_patterns': common_params
        }

    def _calculate_stability_metrics(self) -> Dict[str, float]:
        """Calculate stability metrics for strategy robustness"""
        successful_results = [r for r in self.all_results if r.error is None]
        if len(successful_results) < 10:
            return {}

        sharpe_ratios = [r.sharpe_ratio for r in successful_results]

        return {
            'performance_consistency': 1 - (np.std(sharpe_ratios) / np.mean(sharpe_ratios)) if np.mean(sharpe_ratios) > 0 else 0,
            'success_rate_consistency': len([r for r in successful_results if r.sharpe_ratio > 1.0]) / len(successful_results),
            'parameter_space_coverage': len(set([frozenset(r.parameters.items()) for r in successful_results])) / len(successful_results)
        }

    def _find_ensemble_candidates(self) -> List[Dict[str, Any]]:
        """Find candidates for ensemble construction"""
        # Get diverse top performers
        top_diverse = self.ranker.rank_parameters(self.all_results, 'ensemble_optimal', 20)

        candidates = []
        for result in top_diverse[:10]:  # Top 10 for ensemble
            candidates.append({
                'parameters': result.parameters,
                'performance': {
                    'sharpe_ratio': result.sharpe_ratio,
                    'total_return': result.total_return,
                    'max_drawdown': result.max_drawdown,
                    'correlation_diversity_score': 0.5  # Placeholder - would need correlation analysis
                },
                'weight': 1.0 / 10  # Equal weight for now
            })

        return candidates

    def save_results(self, aggregated_results: AggregatedResults, filepath: str):
        """Save aggregated results to file"""
        # Convert correlation matrix to dict for JSON serialization
        results_dict = aggregated_results.to_dict()
        if 'correlation_matrix' in results_dict and results_dict['correlation_matrix'] is not None:
            results_dict['correlation_matrix'] = results_dict['correlation_matrix'].to_dict()

        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)

        logger.info(f"Saved aggregated results to {filepath}")

    def generate_summary_report(self, aggregated_results: AggregatedResults) -> str:
        """Generate comprehensive summary report"""
        report = f"""
# Unified Backtesting Results Summary

## Strategy: {aggregated_results.strategy_name}

### Execution Summary
- Total Parameter Combinations: {aggregated_results.total_combinations:,}
- Successful Combinations: {aggregated_results.successful_combinations:,}
- Failed Combinations: {aggregated_results.failed_combinations:,}
- Success Rate: {aggregated_results.success_rate:.1%}
- Processing Time: {aggregated_results.processing_time:.1f} seconds

### Top Performance Results

#### Best Sharpe Ratio
1. Sharpe: {aggregated_results.top_sharpe_results[0].sharpe_ratio:.3f}
   Return: {aggregated_results.top_sharpe_results[0].total_return:.1%}
   Max Drawdown: {aggregated_results.top_sharpe_results[0].max_drawdown:.1%}
   Parameters: {aggregated_results.top_sharpe_results[0].parameters}

#### Best Total Return
1. Return: {aggregated_results.top_return_results[0].total_return:.1%}
   Sharpe: {aggregated_results.top_return_results[0].sharpe_ratio:.3f}
   Max Drawdown: {aggregated_results.top_return_results[0].max_drawdown:.1%}
   Parameters: {aggregated_results.top_return_results[0].parameters}

### Performance Statistics
- Average Sharpe Ratio: {aggregated_results.performance_stats.get('sharpe_ratio', {}).get('mean', 0):.3f}
- Average Total Return: {aggregated_results.performance_stats.get('total_return', {}).get('mean', 0):.1%}
- Average Max Drawdown: {aggregated_results.performance_stats.get('max_drawdown', {}).get('mean', 0):.1%}

### Risk Analysis
- Average Max Drawdown: {aggregated_results.drawdown_analysis.get('average_max_drawdown', 0):.1%}
- Worst Case Drawdown: {aggregated_results.drawdown_analysis.get('worst_max_drawdown', 0):.1%}
- Acceptable Drawdown Rate: {aggregated_results.drawdown_analysis.get('percent_with_acceptable_drawdown', 0):.1%}

### Parameter Importance
"""

        # Add parameter importance
        for param, importance in sorted(aggregated_results.parameter_importance.items(),
                                      key=lambda x: x[1], reverse=True)[:5]:
            report += f"- {param}: {importance:.3f}\n"

        report += f"""
### Stability Metrics
- Performance Consistency: {aggregated_results.stability_metrics.get('performance_consistency', 0):.3f}
- Success Rate Consistency: {aggregated_results.stability_metrics.get('success_rate_consistency', 0):.1%}

### Optimal Parameters
{json.dumps(aggregated_results.optimal_parameters.get('best_single', {}), indent=2)}

### Ensemble Candidates
Found {len(aggregated_results.ensemble_candidates)} potential ensemble combinations
"""

        return report