#!/usr / bin / env python3
"""
Risk Management Framework
Phase 3.3: Risk Management Framework Implementation

Implements risk budgeting, constraints, stress testing, scenario analysis,
risk monitoring, and alerting systems for comprehensive risk management.
"""

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from .professional_risk_metrics import (
    RiskCalculator,
    RiskMetrics,
    create_default_stress_scenarios,
    stress_test_returns,
)

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of risk alerts"""

    VOLATILITY_SPIKE = "volatility_spike"
    DRAWDOWN_EXCEEDED = "drawdown_exceeded"
    VAR_BREACH = "var_breach"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    CONCENTRATION_RISK = "concentration_risk"
    LIQUIDITY_RISK = "liquidity_risk"


@dataclass
class RiskBudget:
    """Risk budget allocation"""

    max_portfolio_volatility: float = 0.15
    max_position_size: float = 0.20
    max_sector_exposure: float = 0.40
    max_drawdown_limit: float = 0.15
    var_limit_95: float = 0.02
    var_limit_99: float = 0.04
    concentration_limit: float = 0.10


@dataclass
class RiskAlert:
    """Risk alert information"""

    alert_type: AlertType
    severity: RiskLevel
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    symbol: Optional[str] = None
    recommendations: List[str] = field(default_factory = list)


@dataclass
class RiskConstraints:
    """Portfolio risk constraints"""

    position_limits: Dict[str, float]
    sector_limits: Dict[str, float]
    turnover_limit: float = 0.05
    leverage_limit: float = 1.0
    liquidity_requirements: Dict[str, float]


class RiskBudgeting:
    """Risk budgeting and allocation management"""

    def __init__(self, risk_budget: RiskBudget):
        """
        Initialize risk budgeting

        Args:
            risk_budget: Risk budget constraints
        """
        self.risk_budget = risk_budget
        self.risk_calculator = RiskCalculator()

    def calculate_risk_budget_weights(
        self, returns: pd.DataFrame, views: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Calculate weights based on risk budget allocation

        Args:
            returns: Asset returns matrix
            views: Optional investor views for Black - Litterman model

        Returns:
            Dictionary of risk - budgeted weights
        """

        returns.shape[1]
        assets = returns.columns.tolist()

        # Calculate covariance matrix
        cov_matrix = returns.cov() * 252  # Annualized

        if views is not None:
            # Use Black - Litterman model
            weights = self._black_litterman_weights(returns, views, cov_matrix)
        else:
            # Use risk parity approach
            weights = self._risk_parity_weights(cov_matrix, assets)

        # Apply constraints
        weights = self._apply_risk_constraints(weights, assets)

        return weights

    def _risk_parity_weights(
        self, cov_matrix: pd.DataFrame, assets: List[str]
    ) -> Dict[str, float]:
        """Calculate risk parity weights"""
        n_assets = len(assets)

        def risk_parity_objective(weights):
            portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib / portfolio_var

            target_risk_contrib = 1 / n_assets
            return np.sum((risk_contrib - target_risk_contrib) ** 2)

        # Constraints and bounds
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0, self.risk_budget.max_position_size) for _ in range(n_assets)]

        # Initial guess
        initial_weights = np.array([1 / n_assets] * n_assets)

        # Optimization
        result = self._solve_optimization(
            risk_parity_objective, initial_weights, bounds, constraints
        )

        weights = result.x if result.success else initial_weights
        return dict(zip(assets, weights))

    def _black_litterman_weights(
        self, returns: pd.DataFrame, views: Dict[str, float], cov_matrix: pd.DataFrame
    ) -> Dict[str, float]:
        """Simplified Black - Litterman model implementation"""

        assets = returns.columns.tolist()
        n_assets = len(assets)

        # Market equilibrium returns (simplified)
        market_weights = np.array([1 / n_assets] * n_assets)
        risk_aversion = 3.0
        pi = risk_aversion * np.dot(cov_matrix, market_weights)

        # Views matrix
        P = np.zeros((len(views), n_assets))
        q = np.zeros(len(views))

        for i, (asset, view) in enumerate(views.items()):
            if asset in assets:
                P[i, assets.index(asset)] = 1
                q[i] = view

        # Black - Litterman parameters
        tau = 0.025
        omega = tau * np.dot(np.dot(P, cov_matrix), P.T)

        # Calculate posterior returns
        inv_tau_sigma = np.linalg.inv(tau * cov_matrix)
        inv_omega = np.linalg.inv(omega)

        posterior_sigma = np.linalg.inv(
            inv_tau_sigma + np.dot(np.dot(P.T, inv_omega), P)
        )

        posterior_mu = np.dot(
            posterior_sigma,
            np.dot(inv_tau_sigma, pi) + np.dot(np.dot(P.T, inv_omega), q),
        )

        # Optimize weights for maximum utility
        def utility_objective(weights):
            portfolio_return = np.dot(weights, posterior_mu)
            portfolio_var = np.dot(weights.T, np.dot(posterior_sigma, weights))
            return -(portfolio_return - 0.5 * risk_aversion * portfolio_var)

        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
        bounds = [(0, self.risk_budget.max_position_size) for _ in range(n_assets)]

        initial_weights = np.array([1 / n_assets] * n_assets)
        result = self._solve_optimization(
            utility_objective, initial_weights, bounds, constraints
        )

        weights = result.x if result.success else initial_weights
        return dict(zip(assets, weights))

    def _apply_risk_constraints(
        self, weights: Dict[str, float], assets: List[str]
    ) -> Dict[str, float]:
        """Apply risk budget constraints"""
        # Apply position size limits
        weights = {
            k: min(v, self.risk_budget.max_position_size) for k, v in weights.items()
        }

        # Re - normalize
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        return weights

    def _solve_optimization(self, objective, initial_weights, bounds, constraints):
        """Solve optimization problem"""
        from scipy.optimize import minimize

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = minimize(
                objective,
                initial_weights,
                method="SLSQP",
                bounds = bounds,
                constraints = constraints,
                options={"ftol": 1e - 9, "disp": False},
            )
        return result


class StressTesting:
    """Stress testing and scenario analysis"""

    def __init__(self, risk_budget: RiskBudget):
        """
        Initialize stress testing

        Args:
            risk_budget: Risk budget constraints
        """
        self.risk_budget = risk_budget
        self.risk_calculator = RiskCalculator()
        self.scenarios = create_default_stress_scenarios()

    def add_custom_scenario(self, name: str, scenario_params: Dict[str, float]):
        """Add custom stress scenario"""
        self.scenarios[name] = scenario_params

    def run_stress_tests(
        self, portfolio_returns: pd.Series, positions: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run comprehensive stress tests

        Args:
            portfolio_returns: Portfolio return series
            positions: Current portfolio positions

        Returns:
            Dictionary with stress test results
        """

        results = {}
        base_metrics = self._calculate_base_metrics(portfolio_returns)

        for scenario_name, params in self.scenarios.items():
            scenario_results = self._test_scenario(
                portfolio_returns, scenario_name, params, base_metrics
            )
            results[scenario_name] = scenario_results

        return results

    def _calculate_base_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate baseline metrics"""
        return {
            "volatility": returns.std() * np.sqrt(252),
            "var_95": np.percentile(returns, 5),
            "var_99": np.percentile(returns, 1),
            "cvar_95": returns[returns <= np.percentile(returns, 5)].mean(),
            "cvar_99": returns[returns <= np.percentile(returns, 1)].mean(),
        }

    def _test_scenario(
        self,
        returns: pd.Series,
        scenario_name: str,
        params: Dict[str, float],
        base_metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """Test individual stress scenario"""

        # Apply scenario to returns
        stressed_returns = returns.copy()

        if "shock" in params:
            stressed_returns = stressed_returns + params["shock"]

        if "volatility_multiplier" in params:
            stressed_returns = stressed_returns * params["volatility_multiplier"]

        # Calculate stressed metrics
        stressed_volatility = stressed_returns.std() * np.sqrt(252)
        stressed_var_95 = np.percentile(stressed_returns, 5)
        stressed_cvar_95 = stressed_returns[stressed_returns <= stressed_var_95].mean()

        # Calculate portfolio value impact
        cumulative_returns = (1 + stressed_returns).cumprod()
        max_decline = 1 - cumulative_returns.min()

        return {
            "scenario_name": scenario_name,
            "parameters": params,
            "stressed_metrics": {
                "volatility": stressed_volatility,
                "var_95": stressed_var_95,
                "cvar_95": stressed_cvar_95,
            },
            "impact_analysis": {
                "volatility_increase": (
                    stressed_volatility / base_metrics["volatility"]
                )
                - 1,
                "var_deterioration": stressed_var_95 / base_metrics["var_95"] - 1,
                "max_portfolio_decline": max_decline,
            },
            "risk_assessment": self._assess_scenario_risk(
                max_decline, stressed_volatility
            ),
        }

    def _assess_scenario_risk(
        self, max_decline: float, volatility: float
    ) -> Dict[str, Any]:
        """Assess risk level for scenario"""
        risk_level = RiskLevel.LOW
        alerts = []

        if max_decline > self.risk_budget.max_drawdown_limit:
            risk_level = RiskLevel.CRITICAL
            alerts.append("Maximum drawdown limit exceeded")
        elif max_decline > self.risk_budget.max_drawdown_limit * 0.7:
            risk_level = RiskLevel.HIGH
            alerts.append("High drawdown risk")

        if volatility > self.risk_budget.max_portfolio_volatility * 1.5:
            if risk_level.value < RiskLevel.CRITICAL.value:
                risk_level = RiskLevel.HIGH
            alerts.append("Excessive volatility under stress")

        return {"risk_level": risk_level, "alerts": alerts}


class RiskMonitoring:
    """Real - time risk monitoring and alerting"""

    def __init__(
        self,
        risk_budget: RiskBudget,
        alert_callback: Optional[Callable[[RiskAlert], None]] = None,
    ):
        """
        Initialize risk monitoring

        Args:
            risk_budget: Risk budget constraints
            alert_callback: Optional callback function for alerts
        """
        self.risk_budget = risk_budget
        self.risk_calculator = RiskCalculator()
        self.alert_callback = alert_callback
        self.active_alerts = []
        self.alert_history = []

    def monitor_portfolio_risk(
        self,
        portfolio_returns: pd.Series,
        portfolio_value: float,
        positions: Dict[str, float],
        current_prices: Dict[str, float],
    ) -> List[RiskAlert]:
        """
        Monitor portfolio risk and generate alerts

        Args:
            portfolio_returns: Recent portfolio returns
            portfolio_value: Current portfolio value
            positions: Current positions
            current_prices: Current asset prices

        Returns:
            List of risk alerts
        """

        alerts = []
        current_time = datetime.now()

        # Calculate current risk metrics
        risk_metrics = self.risk_calculator.calculate_comprehensive_metrics(
            pd.Series([portfolio_value], index=[current_time])
        )

        # Check drawdown
        if abs(risk_metrics.max_drawdown) > self.risk_budget.max_drawdown_limit:
            alerts.append(
                RiskAlert(
                    alert_type = AlertType.DRAWDOWN_EXCEEDED,
                    severity = RiskLevel.HIGH,
                    message = f"Drawdown {risk_metrics.max_drawdown:.2%} exceeds limit {self.risk_budget.max_drawdown_limit:.2%}",
                    current_value = abs(risk_metrics.max_drawdown),
                    threshold = self.risk_budget.max_drawdown_limit,
                    timestamp = current_time,
                    recommendations=[
                        "Consider reducing position sizes",
                        "Review risk tolerance",
                    ],
                )
            )

        # Check VaR
        recent_returns = portfolio_returns.tail(252)  # Last year
        if len(recent_returns) > 30:
            current_var_95 = np.percentile(recent_returns, 5)
            if current_var_95 < -self.risk_budget.var_limit_95:
                alerts.append(
                    RiskAlert(
                        alert_type = AlertType.VAR_BREACH,
                        severity = RiskLevel.MEDIUM,
                        message = f"VaR 95% {current_var_95:.3f} exceeds limit {-self.risk_budget.var_limit_95:.3f}",
                        current_value = current_var_95,
                        threshold = -self.risk_budget.var_limit_95,
                        timestamp = current_time,
                        recommendations=[
                            "Review portfolio volatility",
                            "Consider hedging strategies",
                        ],
                    )
                )

        # Check concentration risk
        for symbol, position in positions.items():
            position_weight = (
                position * current_prices.get(symbol, 0)
            ) / portfolio_value
            if position_weight > self.risk_budget.concentration_limit:
                alerts.append(
                    RiskAlert(
                        alert_type = AlertType.CONCENTRATION_RISK,
                        severity = RiskLevel.MEDIUM,
                        message = f"Position {symbol} weight {position_weight:.2%} exceeds limit {self.risk_budget.concentration_limit:.2%}",
                        current_value = position_weight,
                        threshold = self.risk_budget.concentration_limit,
                        timestamp = current_time,
                        symbol = symbol,
                        recommendations=[
                            "Consider reducing position size",
                            "Diversify exposure",
                        ],
                    )
                )

        # Update alert tracking
        for alert in alerts:
            self.active_alerts.append(alert)
            self.alert_history.append(alert)
            if self.alert_callback:
                self.alert_callback(alert)

        return alerts

    def get_active_alerts(self) -> List[RiskAlert]:
        """Get currently active alerts"""
        return self.active_alerts.copy()

    def clear_alerts(self, alert_type: Optional[AlertType] = None):
        """Clear alerts"""
        if alert_type is None:
            self.active_alerts.clear()
        else:
            self.active_alerts = [
                alert for alert in self.active_alerts if alert.alert_type != alert_type
            ]

    def get_risk_summary(self) -> Dict[str, Any]:
        """Get summary of current risk status"""
        alert_counts = {}
        for alert in self.active_alerts:
            alert_counts[alert.alert_type.value] = (
                alert_counts.get(alert.alert_type.value, 0) + 1
            )

        severity_counts = {}
        for alert in self.active_alerts:
            severity_counts[alert.severity.value] = (
                severity_counts.get(alert.severity.value, 0) + 1
            )

        return {
            "total_active_alerts": len(self.active_alerts),
            "alerts_by_type": alert_counts,
            "alerts_by_severity": severity_counts,
            "risk_level": self._calculate_overall_risk_level(),
            "last_updated": datetime.now(),
        }

    def _calculate_overall_risk_level(self) -> RiskLevel:
        """Calculate overall risk level from active alerts"""
        if not self.active_alerts:
            return RiskLevel.LOW

        critical_alerts = [
            a for a in self.active_alerts if a.severity == RiskLevel.CRITICAL
        ]
        if critical_alerts:
            return RiskLevel.CRITICAL

        high_alerts = [a for a in self.active_alerts if a.severity == RiskLevel.HIGH]
        if high_alerts:
            return RiskLevel.HIGH

        medium_alerts = [
            a for a in self.active_alerts if a.severity == RiskLevel.MEDIUM
        ]
        if medium_alerts:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW


class IntegratedRiskManager:
    """Integrated risk management system"""

    def __init__(
        self,
        risk_budget: RiskBudget,
        alert_callback: Optional[Callable[[RiskAlert], None]] = None,
    ):
        """
        Initialize integrated risk manager

        Args:
            risk_budget: Risk budget constraints
            alert_callback: Optional callback for risk alerts
        """
        self.risk_budget = risk_budget
        self.risk_budgeting = RiskBudgeting(risk_budget)
        self.stress_testing = StressTesting(risk_budget)
        self.risk_monitoring = RiskMonitoring(risk_budget, alert_callback)

    def generate_risk_report(
        self,
        portfolio_returns: pd.Series,
        positions: Dict[str, float],
        current_prices: Dict[str, float],
        portfolio_value: float,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive risk report

        Args:
            portfolio_returns: Portfolio return series
            positions: Current positions
            current_prices: Current prices
            portfolio_value: Current portfolio value

        Returns:
            Comprehensive risk report
        """

        # Calculate risk metrics
        risk_calculator = RiskCalculator()
        risk_metrics = risk_calculator.calculate_comprehensive_metrics(
            pd.Series([portfolio_value], index=[datetime.now()])
        )

        # Monitor current risk
        current_alerts = self.risk_monitoring.monitor_portfolio_risk(
            portfolio_returns, portfolio_value, positions, current_prices
        )

        # Run stress tests
        stress_results = self.stress_testing.run_stress_tests(portfolio_returns)

        # Generate report
        report = {
            "timestamp": datetime.now(),
            "portfolio_value": portfolio_value,
            "risk_metrics": risk_metrics,
            "risk_budget_compliance": self._check_budget_compliance(risk_metrics),
            "current_alerts": [
                {
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "symbol": alert.symbol,
                }
                for alert in current_alerts
            ],
            "stress_test_summary": self._summarize_stress_tests(stress_results),
            "risk_monitoring_summary": self.risk_monitoring.get_risk_summary(),
            "recommendations": self._generate_recommendations(
                risk_metrics, current_alerts, stress_results
            ),
        }

        return report

    def _check_budget_compliance(self, risk_metrics: RiskMetrics) -> Dict[str, bool]:
        """Check compliance with risk budget"""
        return {
            "volatility_limit": risk_metrics.volatility
            <= self.risk_budget.max_portfolio_volatility,
            "max_drawdown_limit": abs(risk_metrics.max_drawdown)
            <= self.risk_budget.max_drawdown_limit,
            "var_95_limit": abs(risk_metrics.var_95) <= self.risk_budget.var_limit_95,
            "concentration_limit": True,  # Would need position data to check
        }

    def _summarize_stress_tests(self, stress_results: Dict) -> Dict[str, Any]:
        """Summarize stress test results"""
        worst_case_decline = 0
        worst_case_scenario = None

        for scenario_name, results in stress_results.items():
            max_decline = results["impact_analysis"]["max_portfolio_decline"]
            if max_decline > worst_case_decline:
                worst_case_decline = max_decline
                worst_case_scenario = scenario_name

        return {
            "scenarios_tested": len(stress_results),
            "worst_case_decline": worst_case_decline,
            "worst_case_scenario": worst_case_scenario,
            "high_risk_scenarios": [
                name
                for name, results in stress_results.items()
                if results["risk_assessment"]["risk_level"]
                in [RiskLevel.HIGH, RiskLevel.CRITICAL]
            ],
        }

    def _generate_recommendations(
        self,
        risk_metrics: RiskMetrics,
        alerts: List[RiskAlert],
        stress_results: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        """Generate risk management recommendations"""

        recommendations = []

        # Check drawdown
        if abs(risk_metrics.max_drawdown) > self.risk_budget.max_drawdown_limit * 0.7:
            recommendations.append(
                "Consider reducing overall portfolio risk due to high drawdown"
            )

        # Check Sharpe ratio
        if risk_metrics.sharpe_ratio < 0.5:
            recommendations.append(
                "Portfolio Sharpe ratio is low - consider strategy review"
            )

        # Check concentration
        concentration_alerts = [
            a for a in alerts if a.alert_type == AlertType.CONCENTRATION_RISK
        ]
        if concentration_alerts:
            recommendations.append("Reduce concentration in large positions")

        # Check stress test results
        high_risk_scenarios = [
            name
            for name, results in stress_results.items()
            if results["risk_assessment"]["risk_level"]
            in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
        if high_risk_scenarios:
            recommendations.append(
                f"High risk under stress scenarios: {', '.join(high_risk_scenarios)}"
            )

        # General recommendations
        if risk_metrics.volatility > self.risk_budget.max_portfolio_volatility * 0.8:
            recommendations.append("Monitor portfolio volatility - approaching limits")

        return recommendations


# Utility functions


def create_default_risk_budget() -> RiskBudget:
    """Create default risk budget"""
    return RiskBudget(
        max_portfolio_volatility = 0.15,  # 15% annual volatility
        max_position_size = 0.20,  # 20% max per position
        max_sector_exposure = 0.40,  # 40% max per sector
        max_drawdown_limit = 0.15,  # 15% max drawdown
        var_limit_95 = 0.02,  # 2% daily VaR 95%
        var_limit_99 = 0.04,  # 4% daily VaR 99%
        concentration_limit = 0.10,  # 10% concentration limit
    )


def example_risk_alert_callback(alert: RiskAlert):
    """Example callback function for risk alerts"""
    logger.warning(f"RISK ALERT: {alert.alert_type.value} - {alert.message}")
    print(f"🚨 Risk Alert: {alert.severity.value.upper()} - {alert.message}")


# Example usage
def test_integrated_risk_management():
    """Test integrated risk management system"""
    logger.info("Testing integrated risk management...")

    # Create test data
    dates = pd.date_range("2023 - 01 - 01", periods = 252, freq="D")
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.0005, 0.02, 252), index = dates)

    # Initialize risk manager
    risk_budget = create_default_risk_budget()
    risk_manager = IntegratedRiskManager(risk_budget, example_risk_alert_callback)

    # Create test positions and prices
    positions = {"STOCK_A": 1000, "STOCK_B": 500}
    current_prices = {"STOCK_A": 100, "STOCK_B": 200}
    portfolio_value = 200000

    # Generate risk report
    risk_report = risk_manager.generate_risk_report(
        returns, positions, current_prices, portfolio_value
    )

    logger.info(
        f"Risk report generated with {len(risk_report['current_alerts'])} alerts"
    )
    logger.info(
        f"Overall risk level: {risk_report['risk_monitoring_summary']['risk_level']}"
    )

    return risk_report


if __name__ == "__main__":
    # Test integrated risk management
    test_integrated_risk_management()
