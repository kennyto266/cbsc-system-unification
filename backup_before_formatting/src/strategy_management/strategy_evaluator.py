"""Strategy evaluation system for Hong Kong quantitative trading.

This module provides comprehensive strategy evaluation capabilities including
performance analysis, risk assessment, and comparative evaluation.
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

from ..backtest.engine_interface import StrategyPerformance


class EvaluationMetrics(BaseModel):
    """Strategy evaluation metrics."""

    strategy_id: str = Field(..., description="Strategy identifier")
    evaluation_id: str = Field(..., description="Evaluation identifier")

    # Performance metrics
    total_return: float = Field(0.0, description="Total return")
    annualized_return: float = Field(0.0, description="Annualized return")
    volatility: float = Field(0.0, description="Volatility")
    sharpe_ratio: float = Field(0.0, description="Sharpe ratio")
    sortino_ratio: float = Field(0.0, description="Sortino ratio")
    calmar_ratio: float = Field(0.0, description="Calmar ratio")

    # Risk metrics
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    var_95: float = Field(0.0, description="Value at Risk (95%)")
    var_99: float = Field(0.0, description="Value at Risk (99%)")
    expected_shortfall: float = Field(0.0, description="Expected shortfall")
    downside_deviation: float = Field(0.0, description="Downside deviation")

    # Trading metrics
    win_rate: float = Field(0.0, description="Win rate")
    profit_factor: float = Field(0.0, description="Profit factor")
    average_win: float = Field(0.0, description="Average win")
    average_loss: float = Field(0.0, description="Average loss")
    largest_win: float = Field(0.0, description="Largest win")
    largest_loss: float = Field(0.0, description="Largest loss")

    # Additional metrics
    total_trades: int = Field(0, description="Total number of trades")
    winning_trades: int = Field(0, description="Number of winning trades")
    losing_trades: int = Field(0, description="Number of losing trades")
    consecutive_wins: int = Field(0, description="Maximum consecutive wins")
    consecutive_losses: int = Field(0, description="Maximum consecutive losses")

    # Timestamps
    evaluation_period_start: datetime = Field(
        ..., description="Evaluation period start"
    )
    evaluation_period_end: datetime = Field(..., description="Evaluation period end")
    evaluation_timestamp: datetime = Field(
        default_factory=datetime.now, description="Evaluation timestamp"
    )

    class Config:
        use_enum_values = True


class RiskMetrics(BaseModel):
    """Risk analysis metrics."""

    strategy_id: str = Field(..., description="Strategy identifier")

    # VaR metrics
    var_95_1d: float = Field(0.0, description="1 - day VaR (95%)")
    var_99_1d: float = Field(0.0, description="1 - day VaR (99%)")
    var_95_1w: float = Field(0.0, description="1 - week VaR (95%)")
    var_99_1w: float = Field(0.0, description="1 - week VaR (99%)")
    var_95_1m: float = Field(0.0, description="1 - month VaR (95%)")
    var_99_1m: float = Field(0.0, description="1 - month VaR (99%)")

    # Expected shortfall
    es_95_1d: float = Field(0.0, description="1 - day Expected Shortfall (95%)")
    es_99_1d: float = Field(0.0, description="1 - day Expected Shortfall (99%)")

    # Drawdown analysis
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    max_drawdown_duration: int = Field(
        0, description="Maximum drawdown duration (days)"
    )
    current_drawdown: float = Field(0.0, description="Current drawdown")
    drawdown_recovery_time: int = Field(
        0, description="Average drawdown recovery time (days)"
    )

    # Tail risk
    tail_ratio: float = Field(
        0.0, description="Tail ratio (95th percentile / 5th percentile)"
    )
    skewness: float = Field(0.0, description="Return skewness")
    kurtosis: float = Field(0.0, description="Return kurtosis")

    # Risk - adjusted returns
    risk_adjusted_return: float = Field(0.0, description="Risk - adjusted return")
    information_ratio: float = Field(0.0, description="Information ratio")
    treynor_ratio: float = Field(0.0, description="Treynor ratio")

    # Stress test results
    stress_test_results: Dict[str, float] = Field(
        default_factory=dict, description="Stress test results"
    )

    class Config:
        use_enum_values = True


class DrawdownAnalysis(BaseModel):
    """Drawdown analysis model."""

    strategy_id: str = Field(..., description="Strategy identifier")

    # Drawdown statistics
    max_drawdown: float = Field(0.0, description="Maximum drawdown")
    max_drawdown_date: Optional[datetime] = Field(
        None, description="Date of maximum drawdown"
    )
    max_drawdown_duration: int = Field(
        0, description="Maximum drawdown duration (days)"
    )

    # Drawdown distribution
    drawdown_percentiles: Dict[str, float] = Field(
        default_factory=dict, description="Drawdown percentiles"
    )
    average_drawdown: float = Field(0.0, description="Average drawdown")
    median_drawdown: float = Field(0.0, description="Median drawdown")

    # Recovery analysis
    recovery_times: List[int] = Field(
        default_factory=list, description="Drawdown recovery times"
    )
    average_recovery_time: float = Field(
        0.0, description="Average recovery time (days)"
    )
    recovery_rate: float = Field(0.0, description="Recovery rate")

    # Drawdown periods
    drawdown_periods: List[Dict[str, Any]] = Field(
        default_factory=list, description="Drawdown periods"
    )

    class Config:
        use_enum_values = True


class PerformanceComparison(BaseModel):
    """Performance comparison model."""

    strategy_id: str = Field(..., description="Strategy identifier")
    benchmark_id: str = Field(..., description="Benchmark identifier")

    # Relative performance
    excess_return: float = Field(0.0, description="Excess return over benchmark")
    tracking_error: float = Field(0.0, description="Tracking error")
    information_ratio: float = Field(0.0, description="Information ratio")
    beta: float = Field(0.0, description="Beta")
    alpha: float = Field(0.0, description="Alpha")

    # Risk comparison
    relative_volatility: float = Field(0.0, description="Relative volatility")
    relative_drawdown: float = Field(0.0, description="Relative drawdown")
    risk_adjusted_return_ratio: float = Field(
        0.0, description="Risk - adjusted return ratio"
    )

    # Correlation analysis
    correlation: float = Field(0.0, description="Correlation with benchmark")
    r_squared: float = Field(0.0, description="R - squared")

    # Performance attribution
    performance_attribution: Dict[str, float] = Field(
        default_factory=dict, description="Performance attribution"
    )

    class Config:
        use_enum_values = True


class StrategyEvaluator:
    """Strategy evaluation system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Evaluation state
        self.evaluation_history: List[EvaluationMetrics] = []
        self.risk_analyses: Dict[str, RiskMetrics] = {}
        self.drawdown_analyses: Dict[str, DrawdownAnalysis] = {}
        self.performance_comparisons: Dict[str, PerformanceComparison] = {}

        # Statistics
        self.stats = {
            "evaluations_performed": 0,
            "risk_analyses_performed": 0,
            "drawdown_analyses_performed": 0,
            "performance_comparisons_performed": 0,
            "start_time": None,
        }

    async def evaluate_strategy(
        self,
        strategy_performance: StrategyPerformance,
        evaluation_period_start: datetime,
        evaluation_period_end: datetime,
    ) -> EvaluationMetrics:
        """Evaluate strategy performance."""
        try:
            self.logger.info(f"Evaluating strategy {strategy_performance.strategy_id}")

            # Calculate performance metrics
            metrics = await self._calculate_performance_metrics(
                strategy_performance, evaluation_period_start, evaluation_period_end
            )

            # Store evaluation
            self.evaluation_history.append(metrics)
            self.stats["evaluations_performed"] += 1

            self.logger.info(f"Strategy evaluation completed: {metrics.strategy_id}")
            return metrics

        except Exception as e:
            self.logger.error(f"Error evaluating strategy: {e}")
            raise

    async def _calculate_performance_metrics(
        self,
        strategy_performance: StrategyPerformance,
        evaluation_period_start: datetime,
        evaluation_period_end: datetime,
    ) -> EvaluationMetrics:
        """Calculate comprehensive performance metrics."""
        try:
            # Extract returns data
            returns = strategy_performance.returns
            if not returns:
                # Generate sample data for demonstration
                returns = self._generate_sample_returns(
                    evaluation_period_start, evaluation_period_end
                )

            # Calculate basic metrics
            total_return = strategy_performance.total_return
            annualized_return = strategy_performance.annualized_return
            volatility = strategy_performance.volatility
            sharpe_ratio = strategy_performance.sharpe_ratio

            # Calculate additional performance metrics
            sortino_ratio = await self._calculate_sortino_ratio(returns)
            calmar_ratio = await self._calculate_calmar_ratio(
                annualized_return, strategy_performance.max_drawdown
            )

            # Calculate risk metrics
            var_95 = await self._calculate_var(returns, 0.95)
            var_99 = await self._calculate_var(returns, 0.99)
            expected_shortfall = await self._calculate_expected_shortfall(returns, 0.95)
            downside_deviation = await self._calculate_downside_deviation(returns)

            # Calculate trading metrics
            trading_metrics = await self._calculate_trading_metrics(returns)

            # Create evaluation metrics
            evaluation_metrics = EvaluationMetrics(
                strategy_id=strategy_performance.strategy_id,
                evaluation_id=f"eval_{int(datetime.now().timestamp())}_{strategy_performance.strategy_id[:8]}",
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                calmar_ratio=calmar_ratio,
                max_drawdown=strategy_performance.max_drawdown,
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                downside_deviation=downside_deviation,
                win_rate=trading_metrics["win_rate"],
                profit_factor=trading_metrics["profit_factor"],
                average_win=trading_metrics["average_win"],
                average_loss=trading_metrics["average_loss"],
                largest_win=trading_metrics["largest_win"],
                largest_loss=trading_metrics["largest_loss"],
                total_trades=trading_metrics["total_trades"],
                winning_trades=trading_metrics["winning_trades"],
                losing_trades=trading_metrics["losing_trades"],
                consecutive_wins=trading_metrics["consecutive_wins"],
                consecutive_losses=trading_metrics["consecutive_losses"],
                evaluation_period_start=evaluation_period_start,
                evaluation_period_end=evaluation_period_end,
            )

            return evaluation_metrics

        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            raise

    async def _calculate_sortino_ratio(self, returns: List[float]) -> float:
        """Calculate Sortino ratio."""
        try:
            if not returns:
                return 0.0

            # Calculate downside deviation
            downside_returns = [r for r in returns if r < 0]
            if not downside_returns:
                return float("inf") if returns else 0.0

            downside_deviation = statistics.stdev(downside_returns)
            if downside_deviation == 0:
                return float("inf") if returns else 0.0

            # Calculate Sortino ratio
            mean_return = statistics.mean(returns)
            sortino_ratio = mean_return / downside_deviation

            return sortino_ratio

        except Exception as e:
            self.logger.error(f"Error calculating Sortino ratio: {e}")
            return 0.0

    async def _calculate_calmar_ratio(
        self, annualized_return: float, max_drawdown: float
    ) -> float:
        """Calculate Calmar ratio."""
        try:
            if max_drawdown == 0:
                return float("inf") if annualized_return > 0 else 0.0

            return annualized_return / abs(max_drawdown)

        except Exception as e:
            self.logger.error(f"Error calculating Calmar ratio: {e}")
            return 0.0

    async def _calculate_var(
        self, returns: List[float], confidence_level: float
    ) -> float:
        """Calculate Value at Risk."""
        try:
            if not returns:
                return 0.0

            # Sort returns
            sorted_returns = sorted(returns)

            # Calculate VaR
            index = int((1 - confidence_level) * len(sorted_returns))
            index = max(0, min(index, len(sorted_returns) - 1))

            return sorted_returns[index]

        except Exception as e:
            self.logger.error(f"Error calculating VaR: {e}")
            return 0.0

    async def _calculate_expected_shortfall(
        self, returns: List[float], confidence_level: float
    ) -> float:
        """Calculate Expected Shortfall (Conditional VaR)."""
        try:
            if not returns:
                return 0.0

            # Calculate VaR
            var = await self._calculate_var(returns, confidence_level)

            # Calculate expected shortfall
            tail_returns = [r for r in returns if r <= var]
            if not tail_returns:
                return var

            return statistics.mean(tail_returns)

        except Exception as e:
            self.logger.error(f"Error calculating Expected Shortfall: {e}")
            return 0.0

    async def _calculate_downside_deviation(self, returns: List[float]) -> float:
        """Calculate downside deviation."""
        try:
            if not returns:
                return 0.0

            # Calculate downside returns
            downside_returns = [r for r in returns if r < 0]
            if not downside_returns:
                return 0.0

            # Calculate downside deviation
            return statistics.stdev(downside_returns)

        except Exception as e:
            self.logger.error(f"Error calculating downside deviation: {e}")
            return 0.0

    async def _calculate_trading_metrics(self, returns: List[float]) -> Dict[str, Any]:
        """Calculate trading - specific metrics."""
        try:
            if not returns:
                return {
                    "win_rate": 0.0,
                    "profit_factor": 0.0,
                    "average_win": 0.0,
                    "average_loss": 0.0,
                    "largest_win": 0.0,
                    "largest_loss": 0.0,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "consecutive_wins": 0,
                    "consecutive_losses": 0,
                }

            # Separate winning and losing trades
            winning_trades = [r for r in returns if r > 0]
            losing_trades = [r for r in returns if r < 0]

            # Calculate basic metrics
            total_trades = len(returns)
            winning_trades_count = len(winning_trades)
            losing_trades_count = len(losing_trades)

            win_rate = winning_trades_count / total_trades if total_trades > 0 else 0.0

            # Calculate profit factor
            total_wins = sum(winning_trades) if winning_trades else 0
            total_losses = abs(sum(losing_trades)) if losing_trades else 0
            profit_factor = (
                total_wins / total_losses if total_losses > 0 else float("inf")
            )

            # Calculate average win / loss
            average_win = statistics.mean(winning_trades) if winning_trades else 0.0
            average_loss = statistics.mean(losing_trades) if losing_trades else 0.0

            # Calculate largest win / loss
            largest_win = max(winning_trades) if winning_trades else 0.0
            largest_loss = min(losing_trades) if losing_trades else 0.0

            # Calculate consecutive wins / losses
            consecutive_wins = await self._calculate_consecutive_wins(returns)
            consecutive_losses = await self._calculate_consecutive_losses(returns)

            return {
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "average_win": average_win,
                "average_loss": average_loss,
                "largest_win": largest_win,
                "largest_loss": largest_loss,
                "total_trades": total_trades,
                "winning_trades": winning_trades_count,
                "losing_trades": losing_trades_count,
                "consecutive_wins": consecutive_wins,
                "consecutive_losses": consecutive_losses,
            }

        except Exception as e:
            self.logger.error(f"Error calculating trading metrics: {e}")
            return {}

    async def _calculate_consecutive_wins(self, returns: List[float]) -> int:
        """Calculate maximum consecutive wins."""
        try:
            if not returns:
                return 0

            max_consecutive = 0
            current_consecutive = 0

            for return_val in returns:
                if return_val > 0:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0

            return max_consecutive

        except Exception as e:
            self.logger.error(f"Error calculating consecutive wins: {e}")
            return 0

    async def _calculate_consecutive_losses(self, returns: List[float]) -> int:
        """Calculate maximum consecutive losses."""
        try:
            if not returns:
                return 0

            max_consecutive = 0
            current_consecutive = 0

            for return_val in returns:
                if return_val < 0:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0

            return max_consecutive

        except Exception as e:
            self.logger.error(f"Error calculating consecutive losses: {e}")
            return 0

    def _generate_sample_returns(
        self, start_date: datetime, end_date: datetime
    ) -> List[float]:
        """Generate sample returns for demonstration."""
        try:
            # Generate sample returns using normal distribution
            days = (end_date - start_date).days
            if days <= 0:
                days = 252  # Default to 1 year

            # Generate returns with some realistic characteristics
            np.random.seed(42)  # For reproducibility
            returns = np.random.normal(
                0.0005, 0.02, days
            )  # Mean 0.05% daily, 2% volatility

            return returns.tolist()

        except Exception as e:
            self.logger.error(f"Error generating sample returns: {e}")
            return []

    async def analyze_risk(self, strategy_id: str, returns: List[float]) -> RiskMetrics:
        """Perform comprehensive risk analysis."""
        try:
            self.logger.info(f"Analyzing risk for strategy {strategy_id}")

            # Calculate VaR metrics
            var_95_1d = await self._calculate_var(returns, 0.95)
            var_99_1d = await self._calculate_var(returns, 0.99)

            # Calculate weekly and monthly VaR (simplified)
            var_95_1w = var_95_1d * np.sqrt(5)  # Approximate weekly VaR
            var_99_1w = var_99_1d * np.sqrt(5)
            var_95_1m = var_95_1d * np.sqrt(21)  # Approximate monthly VaR
            var_99_1m = var_99_1d * np.sqrt(21)

            # Calculate Expected Shortfall
            es_95_1d = await self._calculate_expected_shortfall(returns, 0.95)
            es_99_1d = await self._calculate_expected_shortfall(returns, 0.99)

            # Calculate drawdown analysis
            drawdown_analysis = await self._analyze_drawdowns(returns)

            # Calculate tail risk metrics
            tail_ratio = await self._calculate_tail_ratio(returns)
            skewness = await self._calculate_skewness(returns)
            kurtosis = await self._calculate_kurtosis(returns)

            # Calculate risk - adjusted returns
            risk_adjusted_return = await self._calculate_risk_adjusted_return(returns)
            information_ratio = await self._calculate_information_ratio(returns)
            treynor_ratio = await self._calculate_treynor_ratio(returns)

            # Perform stress tests
            stress_test_results = await self._perform_stress_tests(returns)

            # Create risk metrics
            risk_metrics = RiskMetrics(
                strategy_id=strategy_id,
                var_95_1d=var_95_1d,
                var_99_1d=var_99_1d,
                var_95_1w=var_95_1w,
                var_99_1w=var_99_1w,
                var_95_1m=var_95_1m,
                var_99_1m=var_99_1m,
                es_95_1d=es_95_1d,
                es_99_1d=es_99_1d,
                max_drawdown=drawdown_analysis["max_drawdown"],
                max_drawdown_duration=drawdown_analysis["max_drawdown_duration"],
                current_drawdown=drawdown_analysis["current_drawdown"],
                drawdown_recovery_time=drawdown_analysis["recovery_time"],
                tail_ratio=tail_ratio,
                skewness=skewness,
                kurtosis=kurtosis,
                risk_adjusted_return=risk_adjusted_return,
                information_ratio=information_ratio,
                treynor_ratio=treynor_ratio,
                stress_test_results=stress_test_results,
            )

            # Store risk analysis
            self.risk_analyses[strategy_id] = risk_metrics
            self.stats["risk_analyses_performed"] += 1

            self.logger.info(f"Risk analysis completed for strategy {strategy_id}")
            return risk_metrics

        except Exception as e:
            self.logger.error(f"Error analyzing risk: {e}")
            raise

    async def _analyze_drawdowns(self, returns: List[float]) -> Dict[str, Any]:
        """Analyze drawdowns in returns."""
        try:
            if not returns:
                return {
                    "max_drawdown": 0.0,
                    "max_drawdown_duration": 0,
                    "current_drawdown": 0.0,
                    "recovery_time": 0,
                }

            # Calculate cumulative returns
            cumulative_returns = [1.0]
            for ret in returns:
                cumulative_returns.append(cumulative_returns[-1] * (1 + ret))

            # Calculate drawdowns
            peak = cumulative_returns[0]
            max_drawdown = 0.0
            max_drawdown_duration = 0
            current_drawdown = 0.0
            current_duration = 0
            max_duration = 0

            for i, cum_ret in enumerate(cumulative_returns[1:], 1):
                if cum_ret > peak:
                    peak = cum_ret
                    current_duration = 0
                else:
                    drawdown = (peak - cum_ret) / peak
                    max_drawdown = max(max_drawdown, drawdown)
                    current_drawdown = drawdown
                    current_duration += 1
                    max_duration = max(max_duration, current_duration)

            return {
                "max_drawdown": max_drawdown,
                "max_drawdown_duration": max_duration,
                "current_drawdown": current_drawdown,
                "recovery_time": max_duration,
            }

        except Exception as e:
            self.logger.error(f"Error analyzing drawdowns: {e}")
            return {}

    async def _calculate_tail_ratio(self, returns: List[float]) -> float:
        """Calculate tail ratio (95th percentile / 5th percentile)."""
        try:
            if not returns:
                return 0.0

            sorted_returns = sorted(returns)
            p95 = sorted_returns[int(0.95 * len(sorted_returns))]
            p5 = sorted_returns[int(0.05 * len(sorted_returns))]

            return p95 / p5 if p5 != 0 else float("inf")

        except Exception as e:
            self.logger.error(f"Error calculating tail ratio: {e}")
            return 0.0

    async def _calculate_skewness(self, returns: List[float]) -> float:
        """Calculate return skewness."""
        try:
            if not returns or len(returns) < 3:
                return 0.0

            mean_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)

            if std_return == 0:
                return 0.0

            skewness = sum(
                ((r - mean_return) / std_return) ** 3 for r in returns
            ) / len(returns)
            return skewness

        except Exception as e:
            self.logger.error(f"Error calculating skewness: {e}")
            return 0.0

    async def _calculate_kurtosis(self, returns: List[float]) -> float:
        """Calculate return kurtosis."""
        try:
            if not returns or len(returns) < 4:
                return 0.0

            mean_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)

            if std_return == 0:
                return 0.0

            kurtosis = (
                sum(((r - mean_return) / std_return) ** 4 for r in returns)
                / len(returns)
                - 3
            )
            return kurtosis

        except Exception as e:
            self.logger.error(f"Error calculating kurtosis: {e}")
            return 0.0

    async def _calculate_risk_adjusted_return(self, returns: List[float]) -> float:
        """Calculate risk - adjusted return."""
        try:
            if not returns:
                return 0.0

            mean_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)

            return mean_return / std_return if std_return != 0 else 0.0

        except Exception as e:
            self.logger.error(f"Error calculating risk - adjusted return: {e}")
            return 0.0

    async def _calculate_information_ratio(
        self, returns: List[float], benchmark_returns: Optional[List[float]] = None
    ) -> float:
        """Calculate information ratio."""
        try:
            if not returns:
                return 0.0

            if not benchmark_returns:
                # Use zero as benchmark
                excess_returns = returns
            else:
                if len(returns) != len(benchmark_returns):
                    return 0.0
                excess_returns = [r - b for r, b in zip(returns, benchmark_returns)]

            mean_excess = statistics.mean(excess_returns)
            std_excess = statistics.stdev(excess_returns)

            return mean_excess / std_excess if std_excess != 0 else 0.0

        except Exception as e:
            self.logger.error(f"Error calculating information ratio: {e}")
            return 0.0

    async def _calculate_treynor_ratio(
        self, returns: List[float], beta: float = 1.0
    ) -> float:
        """Calculate Treynor ratio."""
        try:
            if not returns or beta == 0:
                return 0.0

            mean_return = statistics.mean(returns)
            return mean_return / beta

        except Exception as e:
            self.logger.error(f"Error calculating Treynor ratio: {e}")
            return 0.0

    async def _perform_stress_tests(self, returns: List[float]) -> Dict[str, float]:
        """Perform stress tests on returns."""
        try:
            if not returns:
                return {}

            stress_tests = {}

            # Market crash scenario (worst 5% of returns)
            worst_returns = sorted(returns)[: max(1, len(returns) // 20)]
            stress_tests["market_crash"] = (
                statistics.mean(worst_returns) if worst_returns else 0.0
            )

            # Volatility spike scenario (highest volatility periods)
            # Simplified: use returns with highest absolute values
            high_vol_returns = sorted(returns, key=abs, reverse=True)[
                : max(1, len(returns) // 10)
            ]
            stress_tests["volatility_spike"] = (
                statistics.mean(high_vol_returns) if high_vol_returns else 0.0
            )

            # Liquidity crisis scenario (consecutive negative returns)
            consecutive_negative = await self._find_worst_consecutive_negative_returns(
                returns
            )
            stress_tests["liquidity_crisis"] = consecutive_negative

            return stress_tests

        except Exception as e:
            self.logger.error(f"Error performing stress tests: {e}")
            return {}

    async def _find_worst_consecutive_negative_returns(
        self, returns: List[float]
    ) -> float:
        """Find worst consecutive negative returns."""
        try:
            if not returns:
                return 0.0

            worst_consecutive = 0.0
            current_consecutive = 0.0

            for ret in returns:
                if ret < 0:
                    current_consecutive += ret
                    worst_consecutive = min(worst_consecutive, current_consecutive)
                else:
                    current_consecutive = 0.0

            return worst_consecutive

        except Exception as e:
            self.logger.error(f"Error finding worst consecutive negative returns: {e}")
            return 0.0

    # Public methods
    def get_evaluation_history(self, limit: int = 100) -> List[EvaluationMetrics]:
        """Get evaluation history."""
        return self.evaluation_history[-limit:] if self.evaluation_history else []

    def get_risk_analysis(self, strategy_id: str) -> Optional[RiskMetrics]:
        """Get risk analysis for strategy."""
        return self.risk_analyses.get(strategy_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Get evaluator statistics."""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            "uptime_seconds": uptime,
            "evaluation_history_count": len(self.evaluation_history),
            "risk_analyses_count": len(self.risk_analyses),
            "drawdown_analyses_count": len(self.drawdown_analyses),
            "performance_comparisons_count": len(self.performance_comparisons),
            "stats": self.stats.copy(),
        }
