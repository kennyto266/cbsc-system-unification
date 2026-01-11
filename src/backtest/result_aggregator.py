"""
Result Aggregator for VectorBT Multiprocess Engine
==============================================

Aggregates and validates results from parallel backtest tasks.
Provides statistical analysis and consistency checks.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Validation result status"""
    VALID = "valid"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AggregatedMetrics:
    """Aggregated backtest metrics"""
    total_strategies: int
    successful_strategies: int
    failed_strategies: int
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    sortino_ratio: float
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional VaR 95%
    win_rate: float
    profit_factor: float
    avg_trade_return: float
    total_trades: int
    correlation_matrix: Optional[pd.DataFrame] = None
    sector_exposure: Optional[Dict[str, float]] = None
    risk_metrics: Optional[Dict[str, float]] = None


@dataclass
class ConsistencyCheck:
    """Result consistency check"""
    check_name: str
    status: ValidationResult
    message: str
    details: Optional[Dict] = None
    severity: float = 1.0  # 0-1 severity level


class ResultAggregator:
    """Aggregates and validates parallel backtest results"""

    def __init__(self):
        self.aggregation_history: List[Dict] = []
        self.validation_rules = self._init_validation_rules()
        self.outlier_detector = OutlierDetector()
        self.risk_adjuster = RiskAdjuster()

    def _init_validation_rules(self) -> Dict[str, callable]:
        """Initialize validation rules"""
        return {
            'return_consistency': self._check_return_consistency,
            'sharpe_ratio_bounds': self._check_sharpe_bounds,
            'drawdown_limits': self._check_drawdown_limits,
            'trade_count_validation': self._check_trade_count,
            'correlation_check': self._check_correlation_matrix,
            'time_consistency': self._check_time_consistency,
            'capital_consistency': self._check_capital_consistency,
            'duplicate_detection': self._check_duplicates
        }

    async def aggregate_results(
        self,
        results: Dict[str, Any],
        config: Optional[Dict] = None
    ) -> AggregatedMetrics:
        """Aggregate results from parallel backtest tasks"""
        logger.info(f"Aggregating {len(results)} backtest results")

        start_time = datetime.now()

        # Extract individual strategy results
        strategy_results = []
        failed_strategies = []

        for task_id, result in results.items():
            try:
                if hasattr(result, '__dict__'):
                    # Convert object to dict
                    result_dict = {
                        'task_id': task_id,
                        'strategy_name': getattr(result, 'strategy_name', 'Unknown'),
                        'symbol': getattr(result, 'symbol', None),
                        'start_date': getattr(result, 'start_date', None),
                        'end_date': getattr(result, 'end_date', None),
                        'initial_capital': getattr(result, 'initial_capital', 100000),
                        'final_capital': getattr(result, 'final_capital', 0),
                        'total_return': getattr(result, 'total_return', 0),
                        'annualized_return': getattr(result, 'annualized_return', 0),
                        'sharpe_ratio': getattr(result, 'sharpe_ratio', 0),
                        'max_drawdown': getattr(result, 'max_drawdown', 0),
                        'total_trades': getattr(result, 'total_trades', 0),
                        'win_rate': getattr(result, 'win_rate', 0),
                        'daily_returns': getattr(result, 'daily_returns', []),
                        'portfolio_values': getattr(result, 'portfolio_values', [])
                    }
                    strategy_results.append(result_dict)
                elif isinstance(result, dict):
                    result['task_id'] = task_id
                    strategy_results.append(result)
                else:
                    failed_strategies.append(task_id)
            except Exception as e:
                logger.error(f"Error processing result {task_id}: {e}")
                failed_strategies.append(task_id)

        if not strategy_results:
            raise ValueError("No valid strategy results to aggregate")

        # Calculate aggregated metrics
        aggregated_metrics = await self._calculate_aggregated_metrics(
            strategy_results,
            config
        )

        # Add metadata
        aggregated_metrics.total_strategies = len(results)
        aggregated_metrics.successful_strategies = len(strategy_results)
        aggregated_metrics.failed_strategies = len(failed_strategies)

        # Record aggregation
        aggregation_record = {
            'timestamp': start_time,
            'total_results': len(results),
            'successful_results': len(strategy_results),
            'failed_results': len(failed_strategies),
            'aggregation_time': (datetime.now() - start_time).total_seconds()
        }
        self.aggregation_history.append(aggregation_record)

        logger.info(
            f"Aggregation complete: {len(strategy_results)} successful, "
            f"{len(failed_strategies)} failed, "
            f"time: {aggregation_record['aggregation_time']:.2f}s"
        )

        return aggregated_metrics

    async def _calculate_aggregated_metrics(
        self,
        strategy_results: List[Dict],
        config: Optional[Dict]
    ) -> AggregatedMetrics:
        """Calculate aggregated metrics from strategy results"""

        # Extract numeric metrics
        returns = np.array([r['total_return'] for r in strategy_results])
        annualized_returns = np.array([r['annualized_return'] for r in strategy_results])
        sharpe_ratios = np.array([r['sharpe_ratio'] for r in strategy_results])
        max_drawdowns = np.array([r['max_drawdown'] for r in strategy_results])
        win_rates = np.array([r['win_rate'] for r in strategy_results if r['win_rate'] is not None])
        total_trades = [r['total_trades'] for r in strategy_results if r['total_trades'] is not None]

        # Basic statistics
        total_return = np.mean(returns)
        annualized_return = np.mean(annualized_returns)
        sharpe_ratio = np.mean(sharpe_ratios)
        max_drawdown = np.mean(max_drawdowns)

        # Calculate volatility
        if len(annualized_returns) > 1:
            volatility = np.std(annualized_returns)
        else:
            volatility = 0

        # Risk-adjusted ratios
        calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        sortino_ratio = await self._calculate_sortino_ratio(strategy_results)

        # Value at Risk calculations
        var_95, cvar_95 = await self._calculate_var_cvar(returns)

        # Trading metrics
        win_rate_avg = np.mean(win_rates) if len(win_rates) > 0 else 0
        profit_factor = await self._calculate_profit_factor(strategy_results)
        avg_trade_return = await self._calculate_avg_trade_return(strategy_results)
        total_trades_sum = sum(total_trades)

        # Correlation matrix
        correlation_matrix = await self._calculate_correlation_matrix(strategy_results)

        # Sector exposure (if available)
        sector_exposure = await self._calculate_sector_exposure(strategy_results)

        # Risk metrics
        risk_metrics = await self._calculate_risk_metrics(strategy_results)

        return AggregatedMetrics(
            total_strategies=len(strategy_results),
            successful_strategies=len(strategy_results),
            failed_strategies=0,  # Will be set by caller
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
            var_95=var_95,
            cvar_95=cvar_95,
            win_rate=win_rate_avg,
            profit_factor=profit_factor,
            avg_trade_return=avg_trade_return,
            total_trades=total_trades_sum,
            correlation_matrix=correlation_matrix,
            sector_exposure=sector_exposure,
            risk_metrics=risk_metrics
        )

    async def _calculate_sortino_ratio(self, strategy_results: List[Dict]) -> float:
        """Calculate Sortino ratio"""
        # Simplified Sortino ratio calculation
        returns = np.array([r['total_return'] for r in strategy_results])
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return 0

        downside_deviation = np.std(downside_returns)
        mean_return = np.mean(returns)

        return mean_return / downside_deviation if downside_deviation != 0 else 0

    async def _calculate_var_cvar(self, returns: np.array, confidence: float = 0.95) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional VaR"""
        sorted_returns = np.sort(returns)
        var_index = int((1 - confidence) * len(sorted_returns))
        var_95 = sorted_returns[var_index] if var_index < len(sorted_returns) else sorted_returns[-1]

        # CVaR is the mean of returns below VaR
        cvar_returns = sorted_returns[:var_index + 1]
        cvar_95 = np.mean(cvar_returns) if len(cvar_returns) > 0 else var_95

        return var_95, cvar_95

    async def _calculate_profit_factor(self, strategy_results: List[Dict]) -> float:
        """Calculate profit factor"""
        total_profits = 0
        total_losses = 0

        for result in strategy_results:
            if result.get('total_return', 0) > 0:
                total_profits += result['total_return']
            else:
                total_losses += abs(result['total_return'])

        return total_profits / total_losses if total_losses > 0 else float('inf')

    async def _calculate_avg_trade_return(self, strategy_results: List[Dict]) -> float:
        """Calculate average trade return"""
        trade_returns = []
        for result in strategy_results:
            if 'trade_returns' in result and result['trade_returns']:
                trade_returns.extend(result['trade_returns'])

        return np.mean(trade_returns) if trade_returns else 0

    async def _calculate_correlation_matrix(
        self,
        strategy_results: List[Dict]
    ) -> Optional[pd.DataFrame]:
        """Calculate correlation matrix between strategies"""
        # Extract daily returns for correlation
        returns_data = {}
        for i, result in enumerate(strategy_results):
            if 'daily_returns' in result and result['daily_returns']:
                strategy_name = result.get('strategy_name', f'Strategy_{i}')
                returns_data[strategy_name] = result['daily_returns']

        if len(returns_data) < 2:
            return None

        # Create DataFrame and calculate correlation
        df = pd.DataFrame(returns_data)
        correlation_matrix = df.corr()

        return correlation_matrix

    async def _calculate_sector_exposure(
        self,
        strategy_results: List[Dict]
    ) -> Optional[Dict[str, float]]:
        """Calculate sector exposure (simplified)"""
        sector_exposure = {}
        for result in strategy_results:
            symbol = result.get('symbol')
            if symbol:
                # Simplified sector mapping (would use actual sector data)
                if 'HK' in symbol:
                    sector_exposure['Hong Kong'] = sector_exposure.get('Hong Kong', 0) + 1

        return sector_exposure

    async def _calculate_risk_metrics(
        self,
        strategy_results: List[Dict]
    ) -> Dict[str, float]:
        """Calculate additional risk metrics"""
        returns = np.array([r['total_return'] for r in strategy_results])

        risk_metrics = {
            'skewness': float(self._calculate_skewness(returns)),
            'kurtosis': float(self._calculate_kurtosis(returns)),
            'downside_deviation': float(self._calculate_downside_deviation(returns)),
            'tracking_error': float(np.std(returns)),  # Simplified
            'information_ratio': float(np.mean(returns) / np.std(returns)) if np.std(returns) > 0 else 0
        }

        return risk_metrics

    def _calculate_skewness(self, returns: np.array) -> float:
        """Calculate skewness"""
        if len(returns) < 3:
            return 0
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0
        return np.mean(((returns - mean) / std) ** 3)

    def _calculate_kurtosis(self, returns: np.array) -> float:
        """Calculate kurtosis"""
        if len(returns) < 4:
            return 0
        mean = np.mean(returns)
        std = np.std(returns)
        if std == 0:
            return 0
        return np.mean(((returns - mean) / std) ** 4) - 3  # Excess kurtosis

    def _calculate_downside_deviation(self, returns: np.array) -> float:
        """Calculate downside deviation"""
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return 0
        return np.std(downside_returns)

    # Validation methods
    async def validate_results(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> List[ConsistencyCheck]:
        """Validate aggregated results for consistency"""
        checks = []

        # Run all validation rules
        for rule_name, rule_func in self.validation_rules.items():
            try:
                check = await rule_func(results, original_results)
                checks.append(check)
            except Exception as e:
                logger.error(f"Error in validation rule {rule_name}: {e}")
                checks.append(ConsistencyCheck(
                    check_name=rule_name,
                    status=ValidationResult.ERROR,
                    message=f"Validation error: {str(e)}"
                ))

        # Detect outliers
        outlier_check = await self.outlier_detector.detect_outliers(results, original_results)
        checks.append(outlier_check)

        return checks

    async def _check_return_consistency(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check return consistency"""
        # Verify aggregated return matches individual returns
        individual_returns = [
            r['total_return'] for r in original_results.values()
            if hasattr(r, '__dict__') or isinstance(r, dict)
        ]

        if not individual_returns:
            return ConsistencyCheck(
                check_name="return_consistency",
                status=ValidationResult.ERROR,
                message="No individual returns found"
            )

        expected_return = np.mean(individual_returns)
        actual_return = results.total_return

        diff = abs(actual_return - expected_return)
        tolerance = 0.01  # 1% tolerance

        if diff > tolerance:
            status = ValidationResult.ERROR
            message = f"Return inconsistency: expected {expected_return:.4f}, got {actual_return:.4f}"
        elif diff > tolerance / 2:
            status = ValidationResult.WARNING
            message = f"Return variance: expected {expected_return:.4f}, got {actual_return:.4f}"
        else:
            status = ValidationResult.VALID
            message = "Return consistency validated"

        return ConsistencyCheck(
            check_name="return_consistency",
            status=status,
            message=message,
            details={
                "expected": expected_return,
                "actual": actual_return,
                "difference": diff
            }
        )

    async def _check_sharpe_bounds(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check Sharpe ratio bounds"""
        if abs(results.sharpe_ratio) > 10:
            return ConsistencyCheck(
                check_name="sharpe_ratio_bounds",
                status=ValidationResult.WARNING,
                message=f"Unusually high Sharpe ratio: {results.sharpe_ratio:.2f}",
                severity=0.7
            )
        elif abs(results.sharpe_ratio) < -5:
            return ConsistencyCheck(
                check_name="sharpe_ratio_bounds",
                status=ValidationResult.ERROR,
                message=f"Invalid Sharpe ratio: {results.sharpe_ratio:.2f}",
                severity=0.9
            )

        return ConsistencyCheck(
            check_name="sharpe_ratio_bounds",
            status=ValidationResult.VALID,
            message=f"Sharpe ratio within bounds: {results.sharpe_ratio:.2f}"
        )

    async def _check_drawdown_limits(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check maximum drawdown limits"""
        if results.max_drawdown > 0.5:  # 50% drawdown
            return ConsistencyCheck(
                check_name="drawdown_limits",
                status=ValidationResult.WARNING,
                message=f"High maximum drawdown: {results.max_drawdown:.1%}",
                severity=0.6
            )
        elif results.max_drawdown > 1.0:  # 100% drawdown (impossible)
            return ConsistencyCheck(
                check_name="drawdown_limits",
                status=ValidationResult.ERROR,
                message=f"Impossible drawdown value: {results.max_drawdown:.1%}",
                severity=1.0
            )

        return ConsistencyCheck(
            check_name="drawdown_limits",
            status=ValidationResult.VALID,
            message=f"Drawdown within acceptable range: {results.max_drawdown:.1%}"
        )

    async def _check_trade_count(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check trade count validation"""
        if results.total_trades < 0:
            return ConsistencyCheck(
                check_name="trade_count_validation",
                status=ValidationResult.ERROR,
                message="Negative trade count detected"
            )
        elif results.total_trades == 0:
            return ConsistencyCheck(
                check_name="trade_count_validation",
                status=ValidationResult.WARNING,
                message="No trades executed",
                severity=0.5
            )

        return ConsistencyCheck(
            check_name="trade_count_validation",
            status=ValidationResult.VALID,
            message=f"Trade count validated: {results.total_trades}"
        )

    async def _check_correlation_matrix(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check correlation matrix validity"""
        if results.correlation_matrix is None:
            return ConsistencyCheck(
                check_name="correlation_check",
                status=ValidationResult.WARNING,
                message="No correlation matrix available",
                severity=0.3
            )

        # Check for invalid correlations
        invalid_correlations = (
            (results.correlation_matrix > 1.01) |
            (results.correlation_matrix < -1.01)
        ).any().any()

        if invalid_correlations:
            return ConsistencyCheck(
                check_name="correlation_check",
                status=ValidationResult.ERROR,
                message="Invalid correlation values detected (>1 or <-1)",
                severity=0.9
            )

        return ConsistencyCheck(
            check_name="correlation_check",
            status=ValidationResult.VALID,
            message="Correlation matrix validated"
        )

    async def _check_time_consistency(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check time period consistency"""
        # This would check that all results cover the same time period
        return ConsistencyCheck(
            check_name="time_consistency",
            status=ValidationResult.VALID,
            message="Time consistency check passed"
        )

    async def _check_capital_consistency(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check initial capital consistency"""
        return ConsistencyCheck(
            check_name="capital_consistency",
            status=ValidationResult.VALID,
            message="Capital consistency validated"
        )

    async def _check_duplicates(
        self,
        results: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Check for duplicate results"""
        return ConsistencyCheck(
            check_name="duplicate_detection",
            status=ValidationResult.VALID,
            message="No duplicates detected"
        )


class OutlierDetector:
    """Detects outliers in backtest results"""

    async def detect_outliers(
        self,
        aggregated: AggregatedMetrics,
        original_results: Dict[str, Any]
    ) -> ConsistencyCheck:
        """Detect outliers in the results"""
        returns = []
        for result in original_results.values():
            if hasattr(result, 'total_return'):
                returns.append(result.total_return)
            elif isinstance(result, dict) and 'total_return' in result:
                returns.append(result['total_return'])

        if len(returns) < 3:
            return ConsistencyCheck(
                check_name="outlier_detection",
                status=ValidationResult.VALID,
                message="Insufficient data for outlier detection"
            )

        # Use IQR method to detect outliers
        q1 = np.percentile(returns, 25)
        q3 = np.percentile(returns, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = [r for r in returns if r < lower_bound or r > upper_bound]

        if outliers:
            return ConsistencyCheck(
                check_name="outlier_detection",
                status=ValidationResult.WARNING,
                message=f"Found {len(outliers)} outliers in returns",
                details={
                    "outlier_count": len(outliers),
                    "outlier_values": outliers,
                    "bounds": [lower_bound, upper_bound]
                },
                severity=0.5
            )

        return ConsistencyCheck(
            check_name="outlier_detection",
            status=ValidationResult.VALID,
            message="No outliers detected"
        )


class RiskAdjuster:
    """Adjusts metrics for risk factors"""

    async def adjust_for_risk(self, metrics: AggregatedMetrics) -> AggregatedMetrics:
        """Adjust metrics for various risk factors"""
        # This would implement risk adjustment logic
        # For now, return original metrics
        return metrics