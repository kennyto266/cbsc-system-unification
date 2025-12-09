"""
Risk Assessment Engine Implementation
風險評估引擎實現

Enhanced risk assessment engine with comprehensive risk metrics,
stress testing, and portfolio risk management capabilities.
增強的風險評估引擎，包含全面的風險指標、壓力測試和投資組合風險管理功能。
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from ..base.base_engine import BaseEngine, EngineConfig, EngineResult
from ...core.logging import log_performance


class RiskLevel(Enum):
    """Risk level classification."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    EXTREME = "extreme"


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics."""

    # Market Risk
    var_1day_95: float = 0.0
    var_1day_99: float = 0.0
    var_10day_95: float = 0.0
    cvar_95: float = 0.0
    beta: float = 0.0
    correlation_with_market: float = 0.0

    # Volatility Risk
    volatility_daily: float = 0.0
    volatility_annualized: float = 0.0
    volatility_ranking: str = "UNKNOWN"

    # Drawdown Risk
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    drawdown_duration: int = 0
    recovery_time: int = 0

    # Concentration Risk
    sector_concentration: float = 0.0
    single_stock_risk: float = 0.0
    geographic_concentration: float = 0.0

    # Liquidity Risk
    average_daily_volume: float = 0.0
    liquidity_score: float = 0.0
    market_impact_estimate: float = 0.0

    # Overall Risk
    risk_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_risk": {
                "var_1day_95": self.var_1day_95,
                "var_1day_99": self.var_1day_99,
                "var_10day_95": self.var_10day_95,
                "cvar_95": self.cvar_95,
                "beta": self.beta,
                "correlation_with_market": self.correlation_with_market
            },
            "volatility_risk": {
                "daily": self.volatility_daily,
                "annualized": self.volatility_annualized,
                "ranking": self.volatility_ranking
            },
            "drawdown_risk": {
                "current": self.current_drawdown,
                "maximum": self.max_drawdown,
                "duration_days": self.drawdown_duration,
                "recovery_time_days": self.recovery_time
            },
            "concentration_risk": {
                "sector": self.sector_concentration,
                "single_stock": self.single_stock_risk,
                "geographic": self.geographic_concentration
            },
            "liquidity_risk": {
                "average_daily_volume": self.average_daily_volume,
                "score": self.liquidity_score,
                "market_impact_estimate": self.market_impact_estimate
            },
            "overall_risk": {
                "score": self.risk_score,
                "level": self.risk_level.value
            }
        }


@dataclass
class RiskAlert:
    """Risk alert notification."""

    alert_type: str
    severity: str
    message: str
    threshold_breached: float
    current_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)


class RiskAssessmentEngine(BaseEngine):
    """
    Enhanced Risk Assessment Engine

    Provides comprehensive risk assessment capabilities including:
    - Value at Risk (VaR) calculations
    - Conditional VaR (CVaR)
    - Stress testing scenarios
    - Concentration risk analysis
    - Liquidity risk assessment
    - Correlation analysis
    - Risk alerts and recommendations
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize risk assessment engine.

        Args:
            config: Engine configuration
        """
        if config is None:
            config = EngineConfig(
                name="risk_assessment",
                version="2.0.0",
                timeout_seconds=30,
                cache_enabled=True,
                cache_ttl=600  # 10 minutes cache for risk metrics
            )

        super().__init__(config)

        # Risk calculation parameters
        self.risk_parameters = {
            "var_confidence_levels": [0.95, 0.99],
            "var_time_horizons": [1, 10],  # days
            "stress_scenarios": [
                "market_crash_20_percent",
                "volatility_spike_2x",
                "correlation_breakdown",
                "liquidity_crisis"
            ],
            "concentration_thresholds": {
                "single_stock_max": 0.10,  # 10%
                "sector_max": 0.30,        # 30%
                "geographic_max": 0.40     # 40%
            },
            "liquidity_thresholds": {
                "minimum_volume": 1000000,  # $1M daily volume
                "max_position_pct_of_volume": 0.05  # 5% of daily volume
            }
        }

        # Historical risk data for comparison
        self.historical_volatility_benchmarks = {
            "low": 0.15,    # 15% annualized
            "medium": 0.25, # 25% annualized
            "high": 0.40    # 40% annualized
        }

        self.logger.info(
            "Risk Assessment Engine initialized",
            parameters=self.risk_parameters
        )

    async def _analyze(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment.

        Args:
            data: Portfolio and market data
            **kwargs: Additional parameters
                - portfolio: Current portfolio holdings
                - market_data: Historical price data
                - benchmark_data: Benchmark data for comparison
                - include_stress_test: Whether to include stress testing
                - risk_tolerance: User's risk tolerance level

        Returns:
            Comprehensive risk assessment results
        """
        if not await self.validate_input(data):
            raise ValueError("Invalid input data for risk assessment")

        portfolio = data.get("portfolio", {})
        market_data = data.get("market_data", {})
        benchmark_data = data.get("benchmark_data", {})
        include_stress_test = kwargs.get("include_stress_test", True)
        risk_tolerance = kwargs.get("risk_tolerance", "medium")

        self.logger.info(
            "Starting risk assessment",
            portfolio_size=len(portfolio),
            include_stress_test=include_stress_test
        )

        # Calculate comprehensive risk metrics
        risk_metrics = await self._calculate_comprehensive_risk(
            portfolio, market_data, benchmark_data
        )

        # Perform stress testing if requested
        stress_test_results = {}
        if include_stress_test:
            stress_test_results = await self._perform_stress_testing(
                portfolio, market_data
            )

        # Generate risk alerts
        risk_alerts = await self._generate_risk_alerts(risk_metrics, risk_tolerance)

        # Provide risk recommendations
        recommendations = await self._generate_risk_recommendations(
            risk_metrics, risk_alerts, risk_tolerance
        )

        # Create comprehensive report
        assessment_results = {
            "risk_metrics": risk_metrics.to_dict(),
            "stress_test_results": stress_test_results,
            "risk_alerts": [self._serialize_alert(alert) for alert in risk_alerts],
            "recommendations": recommendations,
            "portfolio_summary": {
                "total_value": self._calculate_portfolio_value(portfolio),
                "number_of_positions": len(portfolio),
                "risk_level": risk_metrics.risk_level.value,
                "risk_score": risk_metrics.risk_score
            },
            "assessment_timestamp": datetime.now().isoformat(),
            "risk_tolerance": risk_tolerance
        }

        self.logger.info(
            "Risk assessment completed",
            risk_level=risk_metrics.risk_level.value,
            risk_score=risk_metrics.risk_score,
            alerts_generated=len(risk_alerts)
        )

        return assessment_results

    async def _calculate_comprehensive_risk(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any],
        benchmark_data: Dict[str, Any]
    ) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        risk_metrics = RiskMetrics()

        # Calculate returns for risk calculations
        portfolio_returns = self._calculate_portfolio_returns(portfolio, market_data)

        if not portfolio_returns.empty:
            # Market Risk (VaR and CVaR)
            market_risk = await self._calculate_market_risk(portfolio_returns)
            risk_metrics.var_1day_95 = market_risk["var_1d_95"]
            risk_metrics.var_1day_99 = market_risk["var_1d_99"]
            risk_metrics.var_10day_95 = market_risk["var_10d_95"]
            risk_metrics.cvar_95 = market_risk["cvar_95"]

            # Volatility Risk
            volatility_risk = await self._calculate_volatility_risk(portfolio_returns)
            risk_metrics.volatility_daily = volatility_risk["daily"]
            risk_metrics.volatility_annualized = volatility_risk["annualized"]
            risk_metrics.volatility_ranking = volatility_risk["ranking"]

            # Drawdown Risk
            drawdown_risk = await self._calculate_drawdown_risk(portfolio_returns)
            risk_metrics.current_drawdown = drawdown_risk["current"]
            risk_metrics.max_drawdown = drawdown_risk["maximum"]
            risk_metrics.drawdown_duration = drawdown_risk["duration"]
            risk_metrics.recovery_time = drawdown_risk["recovery_time"]

            # Correlation with benchmark
            if benchmark_data:
                correlation_risk = await self._calculate_correlation_risk(
                    portfolio_returns, benchmark_data
                )
                risk_metrics.beta = correlation_risk["beta"]
                risk_metrics.correlation_with_market = correlation_risk["correlation"]

        # Concentration Risk
        concentration_risk = await self._calculate_concentration_risk(portfolio)
        risk_metrics.sector_concentration = concentration_risk["sector"]
        risk_metrics.single_stock_risk = concentration_risk["single_stock"]
        risk_metrics.geographic_concentration = concentration_risk["geographic"]

        # Liquidity Risk
        liquidity_risk = await self._calculate_liquidity_risk(portfolio, market_data)
        risk_metrics.average_daily_volume = liquidity_risk["avg_volume"]
        risk_metrics.liquidity_score = liquidity_risk["score"]
        risk_metrics.market_impact_estimate = liquidity_risk["impact_estimate"]

        # Overall Risk Score
        risk_metrics.risk_score = self._calculate_overall_risk_score(risk_metrics)
        risk_metrics.risk_level = self._determine_risk_level(risk_metrics.risk_score)

        return risk_metrics

    async def _calculate_market_risk(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate market risk metrics (VaR, CVaR)."""
        try:
            # Daily VaR calculations
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)

            # 10-day VaR (assuming independence and sqrt scaling)
            var_10d_95 = var_95 * np.sqrt(10)

            # Conditional VaR (Expected Shortfall)
            var_95_threshold = var_95
            cvar_95 = returns[returns <= var_95_threshold].mean()

            return {
                "var_1d_95": round(var_95 * 100, 2),  # Convert to percentage
                "var_1d_99": round(var_99 * 100, 2),
                "var_10d_95": round(var_10d_95 * 100, 2),
                "cvar_95": round(cvar_95 * 100, 2)
            }

        except Exception as e:
            self.logger.error(f"Market risk calculation failed: {e}")
            return {
                "var_1d_95": 0.0,
                "var_1d_99": 0.0,
                "var_10d_95": 0.0,
                "cvar_95": 0.0
            }

    async def _calculate_volatility_risk(self, returns: pd.Series) -> Dict[str, Any]:
        """Calculate volatility-related risk metrics."""
        try:
            daily_vol = returns.std()
            annualized_vol = daily_vol * np.sqrt(252)

            # Determine volatility ranking
            if annualized_vol <= self.historical_volatility_benchmarks["low"]:
                ranking = "LOW"
            elif annualized_vol <= self.historical_volatility_benchmarks["medium"]:
                ranking = "MEDIUM"
            elif annualized_vol <= self.historical_volatility_benchmarks["high"]:
                ranking = "HIGH"
            else:
                ranking = "VERY_HIGH"

            return {
                "daily": round(daily_vol, 6),
                "annualized": round(annualized_vol * 100, 2),  # Convert to percentage
                "ranking": ranking
            }

        except Exception as e:
            self.logger.error(f"Volatility risk calculation failed: {e}")
            return {"daily": 0.0, "annualized": 0.0, "ranking": "UNKNOWN"}

    async def _calculate_drawdown_risk(self, returns: pd.Series) -> Dict[str, Any]:
        """Calculate drawdown-related risk metrics."""
        try:
            # Calculate cumulative returns
            cum_returns = (1 + returns).cumprod()
            running_max = cum_returns.expanding().max()
            drawdown = (cum_returns - running_max) / running_max

            current_drawdown = drawdown.iloc[-1] if not drawdown.empty else 0.0
            max_drawdown = drawdown.min()

            # Calculate drawdown duration
            in_drawdown = drawdown < 0
            drawdown_periods = []
            start_idx = None

            for idx, is_dd in enumerate(in_drawdown):
                if is_dd and start_idx is None:
                    start_idx = idx
                elif not is_dd and start_idx is not None:
                    drawdown_periods.append(start_idx, idx)
                    start_idx = None

            max_duration = max((end - start) for start, end in drawdown_periods) if drawdown_periods else 0

            # Estimate recovery time (days to recover from current drawdown)
            recovery_time = 0
            if current_drawdown < 0:
                recovery_periods = []
                for i in range(1, len(drawdown)):
                    if drawdown.iloc[i-1] < 0 and drawdown.iloc[i] >= 0:
                        recovery_periods.append(i)

                if recovery_periods:
                    recovery_time = int(np.mean(recovery_periods))

            return {
                "current": round(current_drawdown * 100, 2),
                "maximum": round(abs(max_drawdown) * 100, 2),
                "duration": max_duration,
                "recovery_time": recovery_time
            }

        except Exception as e:
            self.logger.error(f"Drawdown risk calculation failed: {e}")
            return {"current": 0.0, "maximum": 0.0, "duration": 0, "recovery_time": 0}

    async def _calculate_correlation_risk(
        self,
        portfolio_returns: pd.Series,
        benchmark_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate correlation risk with benchmark."""
        try:
            # Convert benchmark data to returns
            benchmark_df = pd.DataFrame(benchmark_data)
            benchmark_returns = benchmark_df["close"].pct_change().dropna()

            # Align the returns series
            common_index = portfolio_returns.index.intersection(benchmark_returns.index)
            if len(common_index) < 30:  # Need at least 30 data points
                return {"beta": 0.0, "correlation": 0.0}

            portfolio_aligned = portfolio_returns.loc[common_index]
            benchmark_aligned = benchmark_returns.loc[common_index]

            # Calculate correlation
            correlation = portfolio_aligned.corr(benchmark_aligned)

            # Calculate beta (covariance / variance of market)
            covariance = portfolio_aligned.cov(benchmark_aligned)
            market_variance = benchmark_aligned.var()
            beta = covariance / market_variance if market_variance != 0 else 0.0

            return {
                "beta": round(beta, 3),
                "correlation": round(correlation, 3)
            }

        except Exception as e:
            self.logger.error(f"Correlation risk calculation failed: {e}")
            return {"beta": 0.0, "correlation": 0.0}

    async def _calculate_concentration_risk(self, portfolio: Dict[str, Any]) -> Dict[str, float]:
        """Calculate concentration risk metrics."""
        try:
            total_value = self._calculate_portfolio_value(portfolio)
            if total_value <= 0:
                return {"sector": 0.0, "single_stock": 0.0, "geographic": 0.0}

            # Single stock concentration (largest position)
            position_values = []
            for symbol, holding in portfolio.items():
                if isinstance(holding, dict) and "value" in holding:
                    position_values.append(holding["value"])
                elif isinstance(holding, (int, float)):
                    position_values.append(holding)

            if position_values:
                max_position = max(position_values)
                single_stock_concentration = (max_position / total_value) * 100
            else:
                single_stock_concentration = 0.0

            # For sector and geographic concentration, we'd need sector/geo data
            # Using simplified assumptions here
            sector_concentration = min(single_stock_concentration * 2, 100)  # Simplified
            geographic_concentration = 50.0  # Assumed 50% concentration in home market

            return {
                "sector": round(sector_concentration, 2),
                "single_stock": round(single_stock_concentration, 2),
                "geographic": round(geographic_concentration, 2)
            }

        except Exception as e:
            self.logger.error(f"Concentration risk calculation failed: {e}")
            return {"sector": 0.0, "single_stock": 0.0, "geographic": 0.0}

    async def _calculate_liquidity_risk(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate liquidity risk metrics."""
        try:
            total_volume = 0.0
            total_positions = 0
            high_liquidity_positions = 0

            for symbol, holding in portfolio.items():
                position_value = 0.0
                if isinstance(holding, dict) and "value" in holding:
                    position_value = holding["value"]
                elif isinstance(holding, (int, float)):
                    position_value = holding

                if position_value > 0:
                    total_positions += 1

                    # Get volume data (simplified - using market data if available)
                    if symbol in market_data:
                        df = pd.DataFrame(market_data[symbol])
                        if "volume" in df.columns:
                            avg_volume = df["volume"].tail(20).mean()  # 20-day average
                            total_volume += avg_volume

                            # Check if position is less than 5% of daily volume
                            position_shares = position_value / df["close"].iloc[-1]
                            volume_ratio = position_shares / max(avg_volume, 1)

                            if volume_ratio <= 0.05:  # Less than 5% of daily volume
                                high_liquidity_positions += 1

            # Calculate liquidity score
            if total_positions > 0:
                liquidity_score = (high_liquidity_positions / total_positions) * 100
            else:
                liquidity_score = 0.0

            # Estimate market impact (simplified)
            market_impact = max(0, 100 - liquidity_score) * 0.1  # Up to 10% impact

            return {
                "avg_volume": round(total_volume / max(total_positions, 1), 0),
                "score": round(liquidity_score, 1),
                "impact_estimate": round(market_impact, 2)
            }

        except Exception as e:
            self.logger.error(f"Liquidity risk calculation failed: {e}")
            return {"avg_volume": 0.0, "score": 0.0, "impact_estimate": 0.0}

    def _calculate_portfolio_value(self, portfolio: Dict[str, Any]) -> float:
        """Calculate total portfolio value."""
        total = 0.0
        for symbol, holding in portfolio.items():
            if isinstance(holding, dict) and "value" in holding:
                total += holding["value"]
            elif isinstance(holding, (int, float)):
                total += holding
        return total

    def _calculate_portfolio_returns(self, portfolio: Dict[str, Any], market_data: Dict[str, Any]) -> pd.Series:
        """Calculate portfolio returns from market data."""
        try:
            # This is a simplified implementation
            # In practice, you'd calculate weighted returns based on portfolio holdings
            all_returns = []

            for symbol, holding in portfolio.items():
                if symbol in market_data:
                    df = pd.DataFrame(market_data[symbol])
                    if "close" in df.columns:
                        returns = df["close"].pct_change().dropna()
                        all_returns.append(returns)

            if all_returns:
                # Combine returns (simplified equal weighting)
                portfolio_returns = pd.concat(all_returns, axis=1).mean(axis=1)
                return portfolio_returns
            else:
                return pd.Series([])

        except Exception as e:
            self.logger.error(f"Portfolio returns calculation failed: {e}")
            return pd.Series([])

    def _calculate_overall_risk_score(self, risk_metrics: RiskMetrics) -> float:
        """Calculate overall risk score from individual metrics."""
        try:
            # Weight different risk components
            weights = {
                "market_risk": 0.25,      # VaR, CVaR
                "volatility": 0.20,       # Volatility metrics
                "drawdown": 0.20,         # Drawdown metrics
                "concentration": 0.20,    # Concentration risk
                "liquidity": 0.15         # Liquidity risk
            }

            # Normalize individual scores (0-100 scale)
            market_score = min(abs(risk_metrics.var_1day_95) * 2, 100)
            volatility_score = min(risk_metrics.volatility_annualized * 2.5, 100)
            drawdown_score = min(abs(risk_metrics.current_drawdown) * 2, 100)
            concentration_score = max(risk_metrics.sector_concentration, risk_metrics.single_stock_risk)
            liquidity_score = max(0, 100 - risk_metrics.liquidity_score)

            # Calculate weighted average
            overall_score = (
                market_score * weights["market_risk"] +
                volatility_score * weights["volatility"] +
                drawdown_score * weights["drawdown"] +
                concentration_score * weights["concentration"] +
                liquidity_score * weights["liquidity"]
            )

            return round(overall_score, 1)

        except Exception as e:
            self.logger.error(f"Overall risk score calculation failed: {e}")
            return 50.0  # Default to medium risk

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from risk score."""
        if risk_score <= 20:
            return RiskLevel.VERY_LOW
        elif risk_score <= 40:
            return RiskLevel.LOW
        elif risk_score <= 60:
            return RiskLevel.MEDIUM
        elif risk_score <= 80:
            return RiskLevel.HIGH
        elif risk_score <= 90:
            return RiskLevel.VERY_HIGH
        else:
            return RiskLevel.EXTREME

    async def _perform_stress_testing(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform stress testing scenarios."""
        stress_results = {}

        for scenario in self.risk_parameters["stress_scenarios"]:
            try:
                if scenario == "market_crash_20_percent":
                    # Simulate 20% market decline
                    portfolio_loss = self._calculate_portfolio_value(portfolio) * 0.20
                    stress_results[scenario] = {
                        "portfolio_loss_percent": 20.0,
                        "portfolio_loss_amount": portfolio_loss,
                        "impact": "SEVERE"
                    }

                elif scenario == "volatility_spike_2x":
                    # Simulate 2x volatility increase
                    current_vol = 0.25  # Assumed current volatility
                    stressed_vol = current_vol * 2
                    stress_results[scenario] = {
                        "volatility_multiplier": 2.0,
                        "stressed_volatility": stressed_vol,
                        "impact": "HIGH"
                    }

                # Add more stress scenarios as needed

            except Exception as e:
                self.logger.error(f"Stress test failed for scenario {scenario}: {e}")
                stress_results[scenario] = {"error": str(e)}

        return stress_results

    async def _generate_risk_alerts(
        self,
        risk_metrics: RiskMetrics,
        risk_tolerance: str
    ) -> List[RiskAlert]:
        """Generate risk alerts based on metrics and tolerance."""
        alerts = []

        try:
            # Define tolerance thresholds
            tolerance_thresholds = {
                "low": {"risk_score": 30, "drawdown": 10, "concentration": 20},
                "medium": {"risk_score": 60, "drawdown": 20, "concentration": 30},
                "high": {"risk_score": 80, "drawdown": 30, "concentration": 40}
            }

            thresholds = tolerance_thresholds.get(risk_tolerance, tolerance_thresholds["medium"])

            # Check overall risk score
            if risk_metrics.risk_score > thresholds["risk_score"]:
                alerts.append(RiskAlert(
                    alert_type="HIGH_RISK_SCORE",
                    severity="HIGH",
                    message=f"Risk score ({risk_metrics.risk_score}) exceeds tolerance threshold",
                    threshold_breached=thresholds["risk_score"],
                    current_value=risk_metrics.risk_score,
                    recommendations=["Consider reducing position sizes", "Rebalance portfolio"]
                ))

            # Check drawdown
            if abs(risk_metrics.current_drawdown) > thresholds["drawdown"]:
                alerts.append(RiskAlert(
                    alert_type="EXCESSIVE_DRAWDOWN",
                    severity="HIGH",
                    message=f"Current drawdown ({abs(risk_metrics.current_drawdown)}%) exceeds threshold",
                    threshold_breached=thresholds["drawdown"],
                    current_value=abs(risk_metrics.current_drawdown),
                    recommendations=["Consider reducing exposure", "Review stop-loss levels"]
                ))

            # Check concentration risk
            if risk_metrics.single_stock_risk > thresholds["concentration"]:
                alerts.append(RiskAlert(
                    alert_type="HIGH_CONCENTRATION",
                    severity="MEDIUM",
                    message=f"Single stock concentration ({risk_metrics.single_stock_risk}%) exceeds threshold",
                    threshold_breached=thresholds["concentration"],
                    current_value=risk_metrics.single_stock_risk,
                    recommendations=["Diversify holdings", "Reduce largest position"]
                ))

            return alerts

        except Exception as e:
            self.logger.error(f"Risk alert generation failed: {e}")
            return []

    async def _generate_risk_recommendations(
        self,
        risk_metrics: RiskMetrics,
        risk_alerts: List[RiskAlert],
        risk_tolerance: str
    ) -> List[str]:
        """Generate risk management recommendations."""
        recommendations = []

        try:
            # Based on overall risk level
            if risk_metrics.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH, RiskLevel.EXTREME]:
                recommendations.extend([
                    "Consider reducing overall portfolio exposure",
                    "Implement stricter risk controls",
                    "Review and diversify holdings"
                ])

            # Based on specific metrics
            if risk_metrics.volatility_ranking == "VERY_HIGH":
                recommendations.append("Consider adding low-volatility assets to reduce portfolio volatility")

            if risk_metrics.liquidity_score < 50:
                recommendations.append("Increase allocation to more liquid assets")

            if risk_metrics.max_drawdown > 25:
                recommendations.append("Implement more robust stop-loss mechanisms")

            # Based on alerts
            for alert in risk_alerts:
                recommendations.extend(alert.recommendations)

            # Remove duplicates
            recommendations = list(set(recommendations))

            # If no specific issues, provide general guidance
            if not recommendations:
                recommendations.append("Portfolio risk is within acceptable levels")

            return recommendations

        except Exception as e:
            self.logger.error(f"Risk recommendations generation failed: {e}")
            return ["Unable to generate specific recommendations"]

    def _serialize_alert(self, alert: RiskAlert) -> Dict[str, Any]:
        """Serialize risk alert to dictionary."""
        return {
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "threshold_breached": alert.threshold_breached,
            "current_value": alert.current_value,
            "timestamp": alert.timestamp.isoformat(),
            "recommendations": alert.recommendations
        }

    async def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data for risk assessment."""
        if not await super().validate_input(data):
            return False

        # Check for portfolio data
        if "portfolio" not in data:
            self.logger.warning("No portfolio data provided for risk assessment")
            return False

        portfolio = data["portfolio"]
        if not isinstance(portfolio, dict) or not portfolio:
            self.logger.warning("Invalid portfolio data format")
            return False

        return True