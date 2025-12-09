"""
Phase 3.3: Walk Forward Analysis System
Implement rolling window optimization and out-of-sample testing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

from phase3_parameter_space_optimizer import ParameterSpace, ParameterRange, ParameterSpaceGenerator
from phase3_multi_objective_optimizer import (
    OptimizationObjective,
    WeightedSumOptimizer,
    PerformanceMetricsCalculator,
    OptimizationResult
)

@dataclass
class WalkForwardWindow:
    """Single walk-forward analysis window"""
    window_id: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_size: int
    test_size: int
    overlap_days: int

@dataclass
class WindowResult:
    """Results for a single walk-forward window"""
    window: WalkForwardWindow
    train_results: List[OptimizationResult]
    test_metrics: Any  # Performance metrics on test data
    selected_parameters: Dict[str, Any]
    train_score: float
    test_score: float
    out_of_sample_performance: float
    parameter_stability: float

@dataclass
class WalkForwardSummary:
    """Summary of walk-forward analysis results"""
    total_windows: int
    successful_windows: int
    avg_train_score: float
    avg_test_score: float
    out_of_sample_ratio: float  # test_score / train_score
    parameter_stability_score: float
    best_parameters: Dict[str, Any]
    performance_consistency: float
    windows: List[WindowResult]

class WalkForwardAnalyzer:
    """Walk Forward Analysis implementation"""

    def __init__(self,
                 train_window_size: int = 252,  # 1 year
                 test_window_size: int = 63,   # 3 months
                 step_size: int = 63,          # 3 months
                 min_train_size: int = 126):   # 6 months minimum
        """
        Initialize Walk Forward Analyzer

        Parameters:
        -----------
        train_window_size : int
            Training window size in days
        test_window_size : int
            Test window size in days
        step_size : int
            Step size for rolling windows in days
        min_train_size : int
            Minimum training window size
        """
        self.train_window_size = train_window_size
        self.test_window_size = test_window_size
        self.step_size = step_size
        self.min_train_size = min_train_size

        self.parameter_space_generator = ParameterSpaceGenerator()
        self.optimizer = WeightedSumOptimizer()
        self.metrics_calculator = PerformanceMetricsCalculator()

    def create_walk_forward_windows(self, data: pd.DataFrame) -> List[WalkForwardWindow]:
        """
        Create walk-forward analysis windows

        Parameters:
        -----------
        data : pd.DataFrame
            Price data with datetime index

        Returns:
        --------
        List[WalkForwardWindow]
            List of analysis windows
        """
        windows = []
        total_data_points = len(data)

        # Calculate number of windows
        max_window_start = total_data_points - self.train_window_size - self.test_window_size
        window_id = 0

        for train_start in range(0, max_window_start + 1, self.step_size):
            train_end = train_start + self.train_window_size
            test_end = train_end + self.test_window_size

            if test_end > total_data_points:
                break

            # Ensure minimum training size
            if train_end - train_start < self.min_train_size:
                continue

            window = WalkForwardWindow(
                window_id=window_id,
                train_start=data.index[train_start],
                train_end=data.index[train_end - 1],
                test_start=data.index[train_end],
                test_end=data.index[test_end - 1],
                train_size=train_end - train_start,
                test_size=test_end - train_end,
                overlap_days=max(0, self.train_window_size - self.step_size)
            )

            windows.append(window)
            window_id += 1

        return windows

    def analyze_window(self,
                      window: WalkForwardWindow,
                      data: pd.DataFrame,
                      parameter_space: ParameterSpace,
                      objectives: List[OptimizationObjective],
                      evaluation_function: Callable) -> WindowResult:
        """
        Analyze a single walk-forward window

        Parameters:
        -----------
        window : WalkForwardWindow
            Analysis window
        data : pd.DataFrame
            Full price data
        parameter_space : ParameterSpace
            Parameter space to explore
        objectives : List[OptimizationObjective]
            Optimization objectives
        evaluation_function : Callable
            Strategy evaluation function

        Returns:
        --------
        WindowResult
            Results for this window
        """
        print(f"Analyzing Window {window.window_id}: {window.train_start.date()} to {window.test_end.date()}")

        try:
            # Split data for this window
            train_data = data.loc[window.train_start:window.train_end]
            test_data = data.loc[window.test_start:window.test_end]

            if len(train_data) < self.min_train_size or len(test_data) < 10:
                print(f"  [SKIPPED] Insufficient data: Train={len(train_data)}, Test={len(test_data)}")
                return None

            print(f"  Training: {len(train_data)} days, Testing: {len(test_data)} days")

            # Phase 1: In-sample optimization on training data
            parameter_combinations = self.parameter_space_generator.generate_parameter_combinations(
                parameter_space, max_combinations=50  # Limit for efficiency
            )

            print(f"  Optimizing {len(parameter_combinations)} parameter combinations...")

            # Modify evaluation function to use training data
            def train_evaluation_function(params):
                return evaluation_function(params, train_data)

            # Perform in-sample optimization
            train_results = self.optimizer.optimize(
                parameter_combinations, objectives, train_evaluation_function
            )

            if not train_results:
                print(f"  [FAILED] No successful optimizations")
                return None

            # Select best parameters from training
            best_train_result = max(train_results, key=lambda x: x.composite_score)
            selected_parameters = best_train_result.parameters
            train_score = best_train_result.composite_score

            print(f"  Best train score: {train_score:.4f}")

            # Phase 2: Out-of-sample testing on test data
            def test_evaluation_function(params):
                return evaluation_function(params, test_data)

            test_result = test_evaluation_function(selected_parameters)

            # Calculate test metrics
            if isinstance(test_result, dict):
                if 'returns' in test_result:
                    test_metrics = self.metrics_calculator.calculate_metrics(test_result['returns'])
                else:
                    test_metrics = self._create_metrics_from_dict(test_result)
            else:
                test_metrics = test_result

            # Calculate test score using same objectives
            test_objective_scores = self.optimizer._calculate_objective_scores(test_metrics, objectives)
            test_score = self.optimizer._calculate_weighted_score(test_objective_scores, objectives)

            print(f"  Test score: {test_score:.4f}")

            # Calculate performance degradation
            if train_score > 0:
                out_of_sample_performance = test_score / train_score
            else:
                out_of_sample_performance = 0

            print(f"  Out-of-sample ratio: {out_of_sample_performance:.3f}")

            # Calculate parameter stability (compare with other good solutions)
            parameter_stability = self._calculate_parameter_stability(
                selected_parameters, train_results[:min(5, len(train_results))]
            )

            # Create window result
            window_result = WindowResult(
                window=window,
                train_results=train_results,
                test_metrics=test_metrics,
                selected_parameters=selected_parameters,
                train_score=train_score,
                test_score=test_score,
                out_of_sample_performance=out_of_sample_performance,
                parameter_stability=parameter_stability
            )

            print(f"  [SUCCESS] Window {window.window_id} completed")
            return window_result

        except Exception as e:
            print(f"  [ERROR] Window {window.window_id} failed: {e}")
            return None

    def _create_metrics_from_dict(self, result_dict: Dict[str, Any]) -> Any:
        """Create PerformanceMetrics from dictionary"""
        from phase3_multi_objective_optimizer import PerformanceMetrics
        return PerformanceMetrics(
            sharpe_ratio=result_dict.get('sharpe_ratio', 0),
            total_return=result_dict.get('total_return', 0),
            max_drawdown=result_dict.get('max_drawdown', 0),
            win_rate=result_dict.get('win_rate', 0.5),
            profit_factor=result_dict.get('profit_factor', 1.0),
            sortino_ratio=result_dict.get('sortino_ratio', 0),
            calmar_ratio=result_dict.get('calmar_ratio', 0),
            num_trades=result_dict.get('num_trades', 0),
            avg_trade_duration=result_dict.get('avg_trade_duration', 0),
            volatility=result_dict.get('volatility', 0.02)
        )

    def _calculate_parameter_stability(self,
                                     selected_params: Dict[str, Any],
                                     top_results: List[OptimizationResult]) -> float:
        """
        Calculate parameter stability score

        Parameters:
        -----------
        selected_params : Dict[str, Any]
            Best parameters
        top_results : List[OptimizationResult]
            Top optimization results

        Returns:
        --------
        float
            Stability score (0-1, higher is better)
        """
        if not top_results:
            return 1.0

        stability_scores = []
        for result in top_results[:5]:  # Compare with top 5 results
            param_stability = 0
            total_params = 0

            for param_name, selected_value in selected_params.items():
                if param_name in result.parameters:
                    result_value = result.parameters[param_name]
                    # Normalize stability based on parameter type
                    if isinstance(selected_value, (int, float)):
                        # For numeric parameters, use relative difference
                        if selected_value != 0:
                            diff = abs(selected_value - result_value) / abs(selected_value)
                            stability = max(0, 1 - diff)
                        else:
                            stability = 1.0 if result_value == 0 else 0.0
                    else:
                        # For categorical parameters, exact match
                        stability = 1.0 if selected_value == result_value else 0.0

                    param_stability += stability
                    total_params += 1

            if total_params > 0:
                stability_scores.append(param_stability / total_params)

        return np.mean(stability_scores) if stability_scores else 1.0

    def run_walk_forward_analysis(self,
                                 data: pd.DataFrame,
                                 parameter_space: ParameterSpace,
                                 objectives: List[OptimizationObjective],
                                 evaluation_function: Callable) -> WalkForwardSummary:
        """
        Run complete walk-forward analysis

        Parameters:
        -----------
        data : pd.DataFrame
            Price data with datetime index
        parameter_space : ParameterSpace
            Parameter space to explore
        objectives : List[OptimizationObjective]
            Optimization objectives
        evaluation_function : Callable
            Strategy evaluation function

        Returns:
        --------
        WalkForwardSummary
            Complete analysis summary
        """
        print("=" * 80)
        print("WALK FORWARD ANALYSIS")
        print("=" * 80)

        start_time = time.time()

        # Create analysis windows
        windows = self.create_walk_forward_windows(data)
        total_windows = len(windows)

        print(f"Created {total_windows} walk-forward windows")
        print(f"Train size: {self.train_window_size} days")
        print(f"Test size: {self.test_window_size} days")
        print(f"Step size: {self.step_size} days")

        # Analyze each window
        window_results = []
        successful_windows = 0

        for i, window in enumerate(windows):
            print(f"\nWindow {i+1}/{total_windows}")
            print("-" * 40)

            result = self.analyze_window(
                window, data, parameter_space, objectives, evaluation_function
            )

            if result:
                window_results.append(result)
                successful_windows += 1

        # Calculate summary statistics
        summary = self._calculate_summary(window_results)

        total_time = time.time() - start_time
        print(f"\nWalk Forward Analysis completed in {total_time:.2f}s")
        print(f"Successful windows: {successful_windows}/{total_windows}")

        return summary

    def _calculate_summary(self, window_results: List[WindowResult]) -> WalkForwardSummary:
        """Calculate walk-forward analysis summary"""
        if not window_results:
            return WalkForwardSummary(
                total_windows=0,
                successful_windows=0,
                avg_train_score=0,
                avg_test_score=0,
                out_of_sample_ratio=0,
                parameter_stability_score=0,
                best_parameters={},
                performance_consistency=0,
                windows=[]
            )

        train_scores = [r.train_score for r in window_results]
        test_scores = [r.test_score for r in window_results]
        oos_ratios = [r.out_of_sample_performance for r in window_results]
        stability_scores = [r.parameter_stability for r in window_results]

        # Find most common best parameters
        from collections import Counter
        param_counter = Counter()
        for result in window_results:
            # Convert parameters to hashable tuple
            param_tuple = tuple(sorted(result.selected_parameters.items()))
            param_counter[param_tuple] += 1

        most_common_params = param_counter.most_common(1)[0][0] if param_counter else ()
        best_parameters = dict(most_common_params)

        # Calculate performance consistency (coefficient of variation)
        if np.mean(test_scores) > 0:
            performance_consistency = 1 - (np.std(test_scores) / np.mean(test_scores))
        else:
            performance_consistency = 0

        return WalkForwardSummary(
            total_windows=len(window_results),
            successful_windows=len(window_results),
            avg_train_score=np.mean(train_scores),
            avg_test_score=np.mean(test_scores),
            out_of_sample_ratio=np.mean([r for r in oos_ratios if 0 <= r <= 10]),  # Filter extreme values
            parameter_stability_score=np.mean(stability_scores),
            best_parameters=best_parameters,
            performance_consistency=max(0, performance_consistency),
            windows=window_results
        )

    def generate_report(self, summary: WalkForwardSummary) -> str:
        """Generate comprehensive walk-forward analysis report"""
        report = []
        report.append("=" * 80)
        report.append("WALK FORWARD ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Overall statistics
        report.append("OVERALL STATISTICS")
        report.append("-" * 40)
        report.append(f"Total Windows: {summary.total_windows}")
        report.append(f"Successful Windows: {summary.successful_windows}")
        report.append(f"Success Rate: {summary.successful_windows/summary.total_windows*100:.1f}%")
        report.append("")

        # Performance metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append(f"Avg In-Sample Score: {summary.avg_train_score:.4f}")
        report.append(f"Avg Out-of-Sample Score: {summary.avg_test_score:.4f}")
        report.append(f"Out-of-Sample Ratio: {summary.out_of_sample_ratio:.3f}")
        report.append(f"Parameter Stability: {summary.parameter_stability_score:.3f}")
        report.append(f"Performance Consistency: {summary.performance_consistency:.3f}")
        report.append("")

        # Best parameters
        report.append("ROBUST BEST PARAMETERS")
        report.append("-" * 40)
        if summary.best_parameters:
            for param, value in summary.best_parameters.items():
                report.append(f"{param}: {value}")
        else:
            report.append("No consistent best parameters found")
        report.append("")

        # Quality assessment
        report.append("QUALITY ASSESSMENT")
        report.append("-" * 40)

        # Assess overfitting
        oos_ratio = summary.out_of_sample_ratio
        if oos_ratio >= 0.8:
            overfitting_assessment = "LOW RISK - Good out-of-sample performance"
        elif oos_ratio >= 0.6:
            overfitting_assessment = "MODERATE - Some performance degradation"
        else:
            overfitting_assessment = "HIGH RISK - Significant overfitting detected"

        report.append(f"Overfitting Risk: {overfitting_assessment}")
        report.append(f"Parameter Stability: {'HIGH' if summary.parameter_stability_score >= 0.7 else 'MODERATE' if summary.parameter_stability_score >= 0.5 else 'LOW'}")
        report.append(f"Performance Consistency: {'HIGH' if summary.performance_consistency >= 0.7 else 'MODERATE' if summary.performance_consistency >= 0.5 else 'LOW'}")

        # Overall recommendation
        report.append("")
        report.append("RECOMMENDATION")
        report.append("-" * 40)

        if (oos_ratio >= 0.7 and
            summary.parameter_stability_score >= 0.6 and
            summary.performance_consistency >= 0.5):
            recommendation = "STRONG - Strategy shows robust performance across time periods"
        elif (oos_ratio >= 0.5 and
              summary.parameter_stability_score >= 0.4 and
              summary.performance_consistency >= 0.3):
            recommendation = "ACCEPTABLE - Strategy shows reasonable performance, monitor closely"
        else:
            recommendation = "WEAK - Strategy shows poor stability, consider redesign"

        report.append(recommendation)

        return "\n".join(report)

# Predefined parameter spaces for common strategies
def get_rsi_walk_forward_space() -> ParameterSpace:
    """Get RSI parameter space for walk-forward analysis"""
    return ParameterSpace(
        name="RSI_WalkForward",
        description="RSI strategy parameter space for walk-forward analysis",
        parameters=[
            ParameterRange('period', 5, 30, 1, 'int'),      # RSI period
            ParameterRange('oversold', 15, 35, 5, 'int'),   # Oversold level
            ParameterRange('overbought', 65, 85, 5, 'int')  # Overbought level
        ],
        constraints=[]
    )

def get_ma_crossover_space() -> ParameterSpace:
    """Get moving average crossover parameter space"""
    return ParameterSpace(
        name="MA_Crossover_WalkForward",
        description="Moving average crossover parameter space for walk-forward analysis",
        parameters=[
            ParameterRange('short_period', 5, 20, 1, 'int'),
            ParameterRange('long_period', 21, 50, 1, 'int')
        ],
        constraints=[]
    )

if __name__ == "__main__":
    # Demo walk-forward analysis
    print("Walk Forward Analysis Demo")
    print("=" * 50)

    # Create sample data
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    n_days = len(dates)
    np.random.seed(42)

    # Generate realistic price series
    returns = np.random.normal(0.0005, 0.02, n_days)
    prices = 100 * np.cumprod(1 + returns)
    data = pd.DataFrame({'close': prices}, index=dates)

    # Define objectives
    objectives = [
        OptimizationObjective("Sharpe Ratio", "Risk-adjusted return", maximize=True, weight=0.6),
        OptimizationObjective("Total Return", "Total return", maximize=True, weight=0.4)
    ]

    # Mock evaluation function
    def mock_strategy_evaluation(params, data):
        """Mock strategy evaluation"""
        np.random.seed(hash(str(params)) % 1000)

        # Generate mock returns based on parameters
        n_periods = len(data)
        base_returns = np.random.normal(0.0005, 0.02, n_periods)

        # Adjust performance based on parameters
        if 'period' in params:
            # Prefer RSI periods around 14
            period_factor = 1 - abs(params['period'] - 14) / 20
            base_returns *= max(0.5, period_factor)

        returns_series = pd.Series(base_returns, index=data.index)

        return {
            'returns': returns_series,
            'sharpe_ratio': np.random.normal(0.5, 0.2),
            'total_return': np.random.normal(0.1, 0.05),
            'max_drawdown': -np.random.uniform(0.05, 0.2),
            'volatility': 0.2
        }

    # Run walk-forward analysis
    analyzer = WalkForwardAnalyzer(
        train_window_size=252,  # 1 year
        test_window_size=63,    # 3 months
        step_size=63           # 3 months
    )

    parameter_space = get_rsi_walk_forward_space()

    summary = analyzer.run_walk_forward_analysis(
        data, parameter_space, objectives, mock_strategy_evaluation
    )

    # Generate and print report
    report = analyzer.generate_report(summary)
    print("\n" + report)