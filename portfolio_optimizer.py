#!/usr/bin/env python3
"""
Portfolio Optimizer
Optimizes strategy combinations and allocations for 500+ strategy portfolios
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import pickle
from pathlib import Path
from scipy.optimize import minimize, LinearConstraint, Bounds
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

# Import our framework components
from comprehensive_strategy_framework import (
    StrategyType, BacktestResult, StrategySignal
)
from strategy_registry import StrategyRegistry
from market_state_detector import MarketStateDetector, MarketState
from advanced_parameter_optimizer import OptimizationResult

logger = logging.getLogger(__name__)


class OptimizationObjective(Enum):
    """Portfolio optimization objectives"""
    MAXIMIZE_RETURN = "maximize_return"
    MINIMIZE_RISK = "minimize_risk"
    MAXIMIZE_SHARPE = "maximize_sharpe"
    MAXIMIZE_SORTINO = "maximize_sortino"
    MAXIMIZE_CALMAR = "maximize_calmar"
    EQUAL_RISK_CONTRIBUTION = "equal_risk_contribution"
    RISK_PARITY = "risk_parity"


@dataclass
class StrategyPerformance:
    """Strategy performance data for optimization"""
    name: str
    strategy_type: StrategyType
    expected_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    correlation_with_market: float = 0.0
    beta: float = 1.0
    reliability_score: float = 0.5
    market_state_performance: Dict[MarketState, float] = field(default_factory=dict)
    execution_cost: float = 0.001  # Estimated execution cost


@dataclass
class PortfolioAllocation:
    """Portfolio allocation result"""
    strategy_weights: Dict[str, float]
    expected_return: float
    portfolio_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    var_95: float  # 95% Value at Risk
    cvar_95: float  # 95% Conditional Value at Risk
    diversification_ratio: float
    turnover: float
    number_of_strategies: int
    concentration_ratio: float  # Herfindahl-Hirschman Index


@dataclass
class OptimizationConstraints:
    """Optimization constraints"""
    min_weight_per_strategy: float = 0.0
    max_weight_per_strategy: float = 0.3
    min_strategies: int = 1
    max_strategies: int = 20
    max_turnover: float = 0.5
    target_leverage: float = 1.0
    sector_constraints: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    strategy_type_constraints: Dict[StrategyType, Tuple[float, float]] = field(default_factory=dict)


class PortfolioOptimizer:
    """Advanced portfolio optimizer for strategy combinations"""

    def __init__(self, strategy_registry: StrategyRegistry = None, market_detector: MarketStateDetector = None):
        self.strategy_registry = strategy_registry
        self.market_detector = market_detector
        self.logger = logging.getLogger(__name__)

        # Storage for performance data
        self.strategy_performance: Dict[str, StrategyPerformance] = {}
        self.correlation_matrix: pd.DataFrame = pd.DataFrame()
        self.optimization_history: List[Dict[str, Any]] = []

        # Current market state
        self.current_market_state = MarketState.TRANSITION

    def load_strategy_performance(self, backtest_results: List[BacktestResult]) -> bool:
        """Load strategy performance from backtest results"""
        try:
            self.logger.info(f"Loading performance data for {len(backtest_results)} strategies")

            for result in backtest_results:
                performance = StrategyPerformance(
                    name=result.strategy_name,
                    strategy_type=self._infer_strategy_type(result.strategy_name),
                    expected_return=result.performance_metrics.get('total_return', 0),
                    volatility=result.performance_metrics.get('volatility', 0.02) or result.max_drawdown / 2,
                    sharpe_ratio=result.sharpe_ratio,
                    max_drawdown=result.max_drawdown,
                    win_rate=result.win_rate,
                    reliability_score=0.5  # Default, will be updated
                )

                # Calculate additional metrics if equity curve is available
                if result.equity_curve:
                    returns = pd.Series(result.equity_curve).pct_change().dropna()
                    if len(returns) > 1:
                        performance.volatility = returns.std()
                        performance.sortino_ratio = returns.mean() / returns[returns < 0].std() * np.sqrt(252) if returns[returns < 0].std() > 0 else 0
                        performance.calmar_ratio = performance.expected_return / abs(performance.max_drawdown) if performance.max_drawdown != 0 else 0

                self.strategy_performance[result.strategy_name] = performance

            self.logger.info(f"Loaded performance data for {len(self.strategy_performance)} strategies")
            return True

        except Exception as e:
            self.logger.error(f"Error loading strategy performance: {e}")
            return False

    def _infer_strategy_type(self, strategy_name: str) -> StrategyType:
        """Infer strategy type from name"""
        name_lower = strategy_name.lower()

        if 'rsi' in name_lower or 'mean_reversion' in name_lower or 'bb' in name_lower:
            return StrategyType.MEAN_REVERSION
        elif 'macd' in name_lower or 'ma' in name_lower or 'trend' in name_lower:
            return StrategyType.TREND_FOLLOWING
        elif 'volatility' in name_lower or 'atr' in name_lower:
            return StrategyType.VOLATILITY
        elif 'volume' in name_lower or 'vwap' in name_lower:
            return StrategyType.VOLUME
        elif 'cbsc' in name_lower or 'sentiment' in name_lower:
            return StrategyType.CBSC_SENTIMENT
        else:
            return StrategyType.PRICE_ACTION

    def calculate_correlation_matrix(self, backtest_results: List[BacktestResult]) -> pd.DataFrame:
        """Calculate correlation matrix between strategies"""
        try:
            self.logger.info("Calculating strategy correlation matrix")

            # Extract returns from equity curves
            returns_data = {}

            for result in backtest_results:
                if result.equity_curve and len(result.equity_curve) > 10:
                    returns = pd.Series(result.equity_curve).pct_change().dropna()
                    if len(returns) > 5:  # Only include if sufficient data
                        returns_data[result.strategy_name] = returns

            if len(returns_data) < 2:
                self.logger.warning("Insufficient data for correlation calculation")
                return pd.DataFrame()

            # Align data by date (assuming same time period)
            returns_df = pd.DataFrame(returns_data)
            correlation_matrix = returns_df.corr()

            # Handle missing values
            correlation_matrix = correlation_matrix.fillna(0)

            self.correlation_matrix = correlation_matrix
            self.logger.info(f"Calculated correlation matrix for {len(correlation_matrix)} strategies")
            return correlation_matrix

        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()

    def optimize_portfolio(self,
                          strategy_names: List[str],
                          constraints: OptimizationConstraints = None,
                          objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_SHARPE,
                          market_state: MarketState = None) -> PortfolioAllocation:
        """Optimize portfolio allocation"""
        try:
            if constraints is None:
                constraints = OptimizationConstraints()

            if market_state is None:
                market_state = self.current_market_state

            self.logger.info(f"Optimizing portfolio for {len(strategy_names)} strategies with objective: {objective.value}")

            # Filter available strategies
            available_strategies = [s for s in strategy_names if s in self.strategy_performance]

            if len(available_strategies) < constraints.min_strategies:
                raise ValueError(f"Only {len(available_strategies)} strategies available, need at least {constraints.min_strategies}")

            # Adjust for market state
            adjusted_performances = self._adjust_for_market_state(available_strategies, market_state)

            # Prepare optimization data
            expected_returns = np.array([adjusted_performances[s].expected_return for s in available_strategies])
            cov_matrix = self._prepare_covariance_matrix(available_strategies)

            # Run optimization
            result = self._run_optimization(
                available_strategies,
                expected_returns,
                cov_matrix,
                constraints,
                objective
            )

            # Calculate additional metrics
            result = self._calculate_additional_metrics(result, available_strategies)

            self.logger.info(f"Portfolio optimization completed: Return={result.expected_return:.2%}, "
                          f"Volatility={result.portfolio_volatility:.2%}, Sharpe={result.sharpe_ratio:.3f}")

            return result

        except Exception as e:
            self.logger.error(f"Error in portfolio optimization: {e}")
            # Return default allocation
            return PortfolioAllocation(
                strategy_weights={s: 1.0/len(strategy_names) for s in strategy_names},
                expected_return=0.0,
                portfolio_volatility=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                var_95=0.0,
                cvar_95=0.0,
                diversification_ratio=0.0,
                turnover=0.0,
                number_of_strategies=len(strategy_names),
                concentration_ratio=1.0
            )

    def _adjust_for_market_state(self, strategy_names: List[str], market_state: MarketState) -> Dict[str, StrategyPerformance]:
        """Adjust strategy expectations based on market state"""
        adjusted = {}

        for strategy_name in strategy_names:
            if strategy_name not in self.strategy_performance:
                continue

            original = self.strategy_performance[strategy_name]
            adjusted_performance = StrategyPerformance(
                name=original.name,
                strategy_type=original.strategy_type,
                expected_return=original.expected_return,
                volatility=original.volatility,
                sharpe_ratio=original.sharpe_ratio,
                max_drawdown=original.max_drawdown,
                win_rate=original.win_rate,
                correlation_with_market=original.correlation_with_market,
                beta=original.beta,
                reliability_score=original.reliability_score,
                execution_cost=original.execution_cost
            )

            # Market state adjustments
            if market_state == MarketState.BULL_MARKET:
                # Boost trend-following strategies
                if original.strategy_type in [StrategyType.TREND_FOLLOWING, StrategyType.MOMENTUM]:
                    adjusted_performance.expected_return *= 1.2
                    adjusted_performance.volatility *= 1.1
                # Reduce mean reversion strategies
                elif original.strategy_type == StrategyType.MEAN_REVERSION:
                    adjusted_performance.expected_return *= 0.7

            elif market_state == MarketState.BEAR_MARKET:
                # Boost volatility and short strategies
                if original.strategy_type == StrategyType.VOLATILITY:
                    adjusted_performance.expected_return *= 1.3
                    adjusted_performance.volatility *= 1.2
                # Reduce momentum strategies
                elif original.strategy_type == StrategyType.MOMENTUM:
                    adjusted_performance.expected_return *= 0.6

            elif market_state == MarketState.HIGH_VOLATILITY:
                # Boost volatility strategies, reduce others
                if original.strategy_type == StrategyType.VOLATILITY:
                    adjusted_performance.expected_return *= 1.4
                else:
                    adjusted_performance.expected_return *= 0.8
                    adjusted_performance.volatility *= 1.2

            elif market_state == MarketState.LOW_VOLATILITY:
                # Boost mean reversion, reduce volatility strategies
                if original.strategy_type == StrategyType.MEAN_REVERSION:
                    adjusted_performance.expected_return *= 1.1
                elif original.strategy_type == StrategyType.VOLATILITY:
                    adjusted_performance.expected_return *= 0.5

            adjusted[strategy_name] = adjusted_performance

        return adjusted

    def _prepare_covariance_matrix(self, strategy_names: List[str]) -> np.ndarray:
        """Prepare covariance matrix for optimization"""
        if self.correlation_matrix.empty:
            # Use identity matrix if no correlation data available
            return np.eye(len(strategy_names)) * 0.04  # 20% annual volatility assumption

        # Extract relevant correlations and volatilities
        available_correlations = self.correlation_matrix.loc[strategy_names, strategy_names]

        # Create covariance matrix
        cov_matrix = np.zeros((len(strategy_names), len(strategy_names)))

        for i, strategy1 in enumerate(strategy_names):
            for j, strategy2 in enumerate(strategy_names):
                if strategy1 in self.strategy_performance and strategy2 in self.strategy_performance:
                    vol1 = self.strategy_performance[strategy1].volatility
                    vol2 = self.strategy_performance[strategy2].volatility
                    correlation = available_correlations.loc[strategy1, strategy2] if strategy1 in available_correlations.index and strategy2 in available_correlations.columns else 0
                    cov_matrix[i, j] = vol1 * vol2 * correlation
                else:
                    cov_matrix[i, j] = 0.04 if i == j else 0  # Default values

        return cov_matrix

    def _run_optimization(self,
                         strategy_names: List[str],
                         expected_returns: np.ndarray,
                         cov_matrix: np.ndarray,
                         constraints: OptimizationConstraints,
                         objective: OptimizationObjective) -> PortfolioAllocation:
        """Run the portfolio optimization"""
        n_strategies = len(strategy_names)

        # Initial weights (equal weight)
        initial_weights = np.ones(n_strategies) / n_strategies

        # Constraints
        constraints_list = []

        # Sum of weights = 1
        constraints_list.append({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

        # Weight bounds
        bounds = Bounds(
            [constraints.min_weight_per_strategy] * n_strategies,
            [constraints.max_weight_per_strategy] * n_strategies
        )

        # Strategy type constraints
        strategy_type_constraints = []
        for strategy_type, (min_weight, max_weight) in constraints.strategy_type_constraints.items():
            type_indices = [i for i, s in enumerate(strategy_names)
                           if self.strategy_performance[s].strategy_type == strategy_type]
            if type_indices:
                constraints_list.append({
                    'type': 'ineq',
                    'fun': lambda x, indices=type_indices: np.sum(x[indices]) - max_weight,
                    'args': (type_indices,)
                })
                constraints_list.append({
                    'type': 'ineq',
                    'fun': lambda x, indices=type_indices: min_weight - np.sum(x[indices]),
                    'args': (type_indices,)
                })

        # Objective function
        if objective == OptimizationObjective.MAXIMIZE_SHARPE:
            objective_func = self._sharpe_objective
        elif objective == OptimizationObjective.MINIMIZE_RISK:
            objective_func = self._risk_objective
        elif objective == OptimizationObjective.MAXIMIZE_RETURN:
            objective_func = self._return_objective
        else:
            objective_func = self._sharpe_objective  # Default

        # Run optimization
        result = minimize(
            objective_func,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'ftol': 1e-9, 'disp': False, 'maxiter': 1000}
        )

        if result.success:
            optimal_weights = result.x
        else:
            self.logger.warning("Optimization failed, using equal weights")
            optimal_weights = initial_weights

        # Apply minimum number of strategies constraint
        significant_weights = [i for i, w in enumerate(optimal_weights) if w > 0.01]
        if len(significant_weights) < constraints.min_strategies:
            # Top-k approach
            top_indices = np.argsort(optimal_weights)[-constraints.min_strategies:]
            new_weights = np.zeros(n_strategies)
            new_weights[top_indices] = 1.0 / constraints.min_strategies
            optimal_weights = new_weights

        # Normalize weights
        optimal_weights = optimal_weights / np.sum(optimal_weights)

        # Create allocation result
        strategy_weights = {strategy_names[i]: optimal_weights[i] for i in range(n_strategies)}

        return PortfolioAllocation(
            strategy_weights=strategy_weights,
            expected_return=0.0,  # Will be calculated
            portfolio_volatility=0.0,  # Will be calculated
            sharpe_ratio=0.0,  # Will be calculated
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            max_drawdown=0.0,
            var_95=0.0,
            cvar_95=0.0,
            diversification_ratio=0.0,
            turnover=0.0,
            number_of_strategies=len(significant_weights),
            concentration_ratio=self._calculate_concentration_ratio(optimal_weights)
        )

    def _sharpe_objective(self, weights: np.ndarray) -> float:
        """Sharpe ratio objective function (negative for minimization)"""
        portfolio_return = np.sum(weights * np.array([self.strategy_performance[s].expected_return for s in self.strategy_performance.keys()]))
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self._prepare_covariance_matrix(list(self.strategy_performance.keys())), weights)))

        if portfolio_volatility > 0:
            return -portfolio_return / portfolio_volatility
        else:
            return -portfolio_return * 100  # Large negative penalty

    def _risk_objective(self, weights: np.ndarray) -> float:
        """Risk minimization objective"""
        cov_matrix = self._prepare_covariance_matrix(list(self.strategy_performance.keys()))
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return portfolio_volatility

    def _return_objective(self, weights: np.ndarray) -> float:
        """Return maximization objective (negative for minimization)"""
        portfolio_return = np.sum(weights * np.array([self.strategy_performance[s].expected_return for s in self.strategy_performance.keys()]))
        return -portfolio_return

    def _calculate_additional_metrics(self, allocation: PortfolioAllocation, strategy_names: List[str]) -> PortfolioAllocation:
        """Calculate additional portfolio metrics"""
        try:
            weights = np.array([allocation.strategy_weights[s] for s in strategy_names])

            # Expected return and volatility
            allocation.expected_return = np.sum(weights * np.array([self.strategy_performance[s].expected_return for s in strategy_names]))
            cov_matrix = self._prepare_covariance_matrix(strategy_names)
            allocation.portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            # Sharpe ratio
            if allocation.portfolio_volatility > 0:
                allocation.sharpe_ratio = allocation.expected_return / allocation.portfolio_volatility
            else:
                allocation.sharpe_ratio = 0

            # Sortino ratio (using downside deviation)
            returns = np.random.multivariate_normal(
                [self.strategy_performance[s].expected_return for s in strategy_names],
                cov_matrix,
                1000
            )
            downside_returns = returns[returns < np.mean(returns)]
            if len(downside_returns) > 0 and np.std(downside_returns) > 0:
                allocation.sortino_ratio = allocation.expected_return / np.std(downside_returns)
            else:
                allocation.sortino_ratio = 0

            # Calmar ratio
            max_dd = np.min([self.strategy_performance[s].max_drawdown for s in strategy_names])
            allocation.max_drawdown = max_dd
            allocation.calmar_ratio = allocation.expected_return / abs(max_dd) if max_dd != 0 else 0

            # VaR and CVaR
            if len(returns) > 0:
                allocation.var_95 = np.percentile(returns, 5)
                allocation.cvar_95 = returns[returns <= allocation.var_95].mean()
            else:
                allocation.var_95 = 0
                allocation.cvar_95 = 0

            # Diversification ratio
            individual_volatilities = [self.strategy_performance[s].volatility for s in strategy_names]
            weighted_individual_vol = np.sum(weights * np.array(individual_volatilities))
            allocation.diversification_ratio = weighted_individual_vol / allocation.portfolio_volatility if allocation.portfolio_volatility > 0 else 1

            # Concentration ratio (Herfindahl-Hirschman Index)
            allocation.concentration_ratio = self._calculate_concentration_ratio(weights)

        except Exception as e:
            self.logger.error(f"Error calculating additional metrics: {e}")

        return allocation

    def _calculate_concentration_ratio(self, weights: np.ndarray) -> float:
        """Calculate concentration ratio (Herfindahl-Hirschman Index)"""
        return np.sum(weights ** 2)

    def run_multi_objective_optimization(self,
                                         strategy_names: List[str],
                                         constraints: OptimizationConstraints = None) -> List[PortfolioAllocation]:
        """Run multi-objective optimization"""
        objectives = [
            OptimizationObjective.MAXIMIZE_SHARPE,
            OptimizationObjective.MINIMIZE_RISK,
            OptimizationObjective.EQUAL_RISK_CONTRIBUTION
        ]

        results = []
        for objective in objectives:
            try:
                result = self.optimize_portfolio(strategy_names, constraints, objective)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error in multi-objective optimization for {objective}: {e}")

        return results

    def generate_portfolio_report(self, allocation: PortfolioAllocation) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        try:
            # Sort strategies by weight
            sorted_strategies = sorted(allocation.strategy_weights.items(), key=lambda x: x[1], reverse=True)

            # Calculate risk contribution
            risk_contributions = self._calculate_risk_contributions(allocation)

            report = {
                'portfolio_summary': {
                    'expected_return': f"{allocation.expected_return:.2%}",
                    'volatility': f"{allocation.portfolio_volatility:.2%}",
                    'sharpe_ratio': f"{allocation.sharpe_ratio:.3f}",
                    'sortino_ratio': f"{allocation.sortino_ratio:.3f}",
                    'calmar_ratio': f"{allocation.calmar_ratio:.3f}",
                    'max_drawdown': f"{allocation.max_drawdown:.2%}",
                    'var_95': f"{allocation.var_95:.2%}",
                    'diversification_ratio': f"{allocation.diversification_ratio:.3f}",
                    'concentration_ratio': f"{allocation.concentration_ratio:.3f}"
                },
                'top_strategies': [
                    {
                        'name': name,
                        'weight': f"{weight:.2%}",
                        'risk_contribution': f"{risk_contributions.get(name, 0):.2%}",
                        'performance': self.strategy_performance.get(name).__dict__ if name in self.strategy_performance else {}
                    }
                    for name, weight in sorted_strategies[:10]
                ],
                'risk_analysis': {
                    'var_95': allocation.var_95,
                    'cvar_95': allocation.cvar_95,
                    'worst_case_scenario': allocation.cvar_95 * 1.5,  # Conservative estimate
                    'stress_test_scenarios': self._generate_stress_test_scenarios(allocation)
                },
                'recommendations': self._generate_recommendations(allocation)
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating portfolio report: {e}")
            return {}

    def _calculate_risk_contributions(self, allocation: PortfolioAllocation) -> Dict[str, float]:
        """Calculate risk contributions of each strategy"""
        try:
            strategy_names = list(allocation.strategy_weights.keys())
            weights = np.array([allocation.strategy_weights[s] for s in strategy_names])
            cov_matrix = self._prepare_covariance_matrix(strategy_names)

            # Marginal contribution to risk
            portfolio_volatility = allocation.portfolio_volatility
            if portfolio_volatility > 0:
                marginal_contrib = np.dot(cov_matrix, weights) / portfolio_volatility
                risk_contributions = weights * marginal_contrib
                total_risk = np.sum(risk_contributions)
                risk_contributions = risk_contributions / total_risk
            else:
                risk_contributions = {s: 1.0/len(strategy_names) for s in strategy_names}

            return {strategy_names[i]: risk_contributions[i] for i in range(len(strategy_names))}

        except Exception as e:
            self.logger.error(f"Error calculating risk contributions: {e}")
            return {}

    def _generate_stress_test_scenarios(self, allocation: PortfolioAllocation) -> Dict[str, float]:
        """Generate stress test scenarios"""
        scenarios = {
            'market_crash': -0.30,  # -30% market crash
            'high_volatility': -0.20,  # High volatility period
            'liquidity_crisis': -0.15,  # Liquidity crisis
            'correlation_breakdown': -0.10,  # Correlations breakdown
            'black_swan': -0.40  # Black swan event
        }

        return scenarios

    def _generate_recommendations(self, allocation: PortfolioAllocation) -> List[str]:
        """Generate portfolio recommendations"""
        recommendations = []

        # Risk-based recommendations
        if allocation.max_drawdown > 0.20:
            recommendations.append("Consider reducing position sizes - max drawdown exceeds 20%")

        if allocation.sharpe_ratio < 0.5:
            recommendations.append("Low Sharpe ratio - consider higher return strategies or risk reduction")

        if allocation.concentration_ratio > 0.4:
            recommendations.append("High concentration - diversify across more strategies")

        if allocation.diversification_ratio < 0.8:
            recommendations.append("Low diversification benefit - add less correlated strategies")

        if allocation.number_of_strategies < 5:
            recommendations.append("Low strategy count - consider adding more diverse strategies")

        if allocation.number_of_strategies > 15:
            recommendations.append("High strategy count - consider focusing on top performers")

        return recommendations


# Factory function
def create_portfolio_optimizer(strategy_registry: StrategyRegistry = None,
                                market_detector: MarketStateDetector = None) -> PortfolioOptimizer:
    """Factory function to create portfolio optimizer"""
    return PortfolioOptimizer(strategy_registry, market_detector)


# Main execution for testing
if __name__ == "__main__":
    print("Portfolio Optimizer Test")
    print("=" * 40)

    # Create test data
    np.random.seed(42)
    strategy_names = [
        'RSI_MR_14_25_70',
        'RSI_MR_21_25_70',
        'MACD_X_12_26_9',
        'BB_Break_20_2.0',
        'DMA_10_30',
        'Trend_5_20',
        'Volatility_ATR',
        'Volume_VWAP'
    ]

    # Create mock performance data
    mock_performance = {}
    for strategy_name in strategy_names:
        mock_performance[strategy_name] = StrategyPerformance(
            name=strategy_name,
            strategy_type=StrategyType.MEAN_REVERSION if 'RSI' in strategy_name else StrategyType.TREND_FOLLOWING,
            expected_return=np.random.uniform(0.1, 0.3),
            volatility=np.random.uniform(0.15, 0.4),
            sharpe_ratio=np.random.uniform(0.3, 1.5),
            max_drawdown=np.random.uniform(-0.1, -0.3),
            win_rate=np.random.uniform(0.4, 0.7),
            reliability_score=np.random.uniform(0.5, 0.9)
        )

    # Create optimizer
    optimizer = create_portfolio_optimizer()
    optimizer.strategy_performance = mock_performance

    # Create correlation matrix
    n_strategies = len(strategy_names)
    correlation_matrix = np.eye(n_strategies)
    for i in range(n_strategies):
        for j in range(i+1, n_strategies):
            correlation_matrix[i, j] = np.random.uniform(-0.3, 0.7)
            correlation_matrix[j, i] = correlation_matrix[i, j]

    optimizer.correlation_matrix = pd.DataFrame(
        correlation_matrix,
        index=strategy_names,
        columns=strategy_names
    )

    # Test optimization
    print(f"Testing portfolio optimization with {len(strategy_names)} strategies")

    constraints = OptimizationConstraints(
        min_weight_per_strategy=0.05,
        max_weight_per_strategy=0.4,
        min_strategies=3,
        max_strategies=6
    )

    try:
        allocation = optimizer.optimize_portfolio(strategy_names, constraints)

        print(f"\nOptimization Results:")
        print(f"Expected Return: {allocation.expected_return:.2%}")
        print(f"Portfolio Volatility: {allocation.portfolio_volatility:.2%}")
        print(f"Sharpe Ratio: {allocation.sharpe_ratio:.3f}")
        print(f"Number of Strategies: {allocation.number_of_strategies}")
        print(f"Concentration Ratio: {allocation.concentration_ratio:.3f}")

        print(f"\nTop Strategy Allocations:")
        sorted_strategies = sorted(allocation.strategy_weights.items(), key=lambda x: x[1], reverse=True)
        for name, weight in sorted_strategies[:5]:
            print(f"  {name}: {weight:.2%}")

        # Generate report
        report = optimizer.generate_portfolio_report(allocation)
        print(f"\nPortfolio Report:")
        print(f"  Summary: {report['portfolio_summary']}")

        if report['recommendations']:
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")

    except Exception as e:
        print(f"Error in optimization test: {e}")

    print("\nPortfolio optimizer test completed!")