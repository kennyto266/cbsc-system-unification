"""
Risk Models and Data Structures
風險模型和數據結構

Data models and enums used by the risk assessment engine.
風險評估引擎使用的數據模型和枚舉。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Import RiskLevel and RiskMetrics from risk_assessment_engine
from .risk_assessment_engine import RiskLevel, RiskMetrics


class RiskAlertType(Enum):
    """Risk alert type enumeration."""
    HIGH_RISK_SCORE = "high_risk_score"
    EXCESSIVE_DRAWDOWN = "excessive_drawdown"
    HIGH_CONCENTRATION = "high_concentration"
    LIQUIDITY_RISK = "liquidity_risk"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    MARKET_RISK = "market_risk"
    CREDIT_RISK = "credit_risk"
    OPERATIONAL_RISK = "operational_risk"


class RiskSeverity(Enum):
    """Risk severity level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAlert:
    """Risk alert data structure."""

    alert_type: str
    severity: str
    message: str
    threshold_breached: float
    current_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "threshold_breached": self.threshold_breached,
            "current_value": self.current_value,
            "timestamp": self.timestamp.isoformat(),
            "recommendations": self.recommendations
        }


@dataclass
class StressTestResult:
    """Stress test result data structure."""

    scenario_name: str
    scenario_description: str
    portfolio_impact_percent: float
    portfolio_impact_amount: float
    confidence_interval: Optional[tuple] = None
    assumptions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "scenario_name": self.scenario_name,
            "scenario_description": self.scenario_description,
            "portfolio_impact_percent": self.portfolio_impact_percent,
            "portfolio_impact_amount": self.portfolio_impact_amount,
            "confidence_interval": self.confidence_interval,
            "assumptions": self.assumptions,
            "recommendations": self.recommendations
        }


@dataclass
class RiskLimit:
    """Risk limit configuration."""

    limit_name: str
    limit_type: str  # absolute, percentage, ratio
    threshold_value: float
    warning_threshold: float  # Warning level (usually < threshold)
    current_value: float = 0.0
    is_breached: bool = False
    is_warning: bool = False
    last_checked: datetime = field(default_factory=datetime.now)

    def check_breach(self, current_value: float) -> tuple[bool, bool]:
        """Check if limit is breached or at warning level."""
        self.current_value = current_value
        self.last_checked = datetime.now()

        self.is_warning = current_value >= self.warning_threshold
        self.is_breached = current_value >= self.threshold_value

        return self.is_breached, self.is_warning


@dataclass
class RiskReport:
    """Comprehensive risk report data structure."""

    report_id: str
    generated_at: datetime = field(default_factory=datetime.now)
    portfolio_id: str
    risk_metrics: RiskMetrics = field(default_factory=RiskMetrics)
    risk_alerts: List[RiskAlert] = field(default_factory=list)
    stress_test_results: List[StressTestResult] = field(default_factory=list)
    risk_limits: List[RiskLimit] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    overall_risk_level: RiskLevel = RiskLevel.MEDIUM
    compliance_status: str = "COMPLIANT"  # COMPLIANT, WARNING, BREACH

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "portfolio_id": self.portfolio_id,
            "risk_metrics": self.risk_metrics.to_dict(),
            "risk_alerts": [alert.to_dict() for alert in self.risk_alerts],
            "stress_test_results": [result.to_dict() for result in self.stress_test_results],
            "risk_limits": [
                {
                    "name": limit.limit_name,
                    "type": limit.limit_type,
                    "threshold": limit.threshold_value,
                    "current_value": limit.current_value,
                    "is_breached": limit.is_breached,
                    "is_warning": limit.is_warning,
                    "last_checked": limit.last_checked.isoformat()
                }
                for limit in self.risk_limits
            ],
            "recommendations": self.recommendations,
            "overall_risk_level": self.overall_risk_level.value,
            "compliance_status": self.compliance_status
        }


@dataclass
class RiskToleranceProfile:
    """Investor risk tolerance profile."""

    profile_id: str
    investor_id: str
    risk_tolerance: str  # VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    investment_horizon: int  # years
    liquidity_needs: str  # LOW, MEDIUM, HIGH
    experience_level: str  # BEGINNER, INTERMEDIATE, ADVANCED
    age: int
    income_stability: str  # LOW, MEDIUM, HIGH
    financial_goals: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "profile_id": self.profile_id,
            "investor_id": self.investor_id,
            "risk_tolerance": self.risk_tolerance,
            "investment_horizon": self.investment_horizon,
            "liquidity_needs": self.liquidity_needs,
            "experience_level": self.experience_level,
            "age": self.age,
            "income_stability": self.income_stability,
            "financial_goals": self.financial_goals,
            "constraints": self.constraints,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class VaRResult:
    """Value at Risk calculation result."""

    confidence_level: float  # e.g., 0.95 for 95% VaR
    time_horizon: int  # days
    var_amount: float  # monetary amount
    var_percentage: float  # percentage of portfolio value
    cvar_amount: float = 0.0  # Conditional VaR
    cvar_percentage: float = 0.0
    expected_shortfall: float = 0.0
    calculation_method: str = "historical"  # historical, parametric, monte_carlo
    data_points_used: int = 0
    confidence_interval: Optional[tuple] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "confidence_level": self.confidence_level,
            "time_horizon": self.time_horizon,
            "var_amount": self.var_amount,
            "var_percentage": self.var_percentage,
            "cvar_amount": self.cvar_amount,
            "cvar_percentage": self.cvar_percentage,
            "expected_shortfall": self.expected_shortfall,
            "calculation_method": self.calculation_method,
            "data_points_used": self.data_points_used,
            "confidence_interval": self.confidence_interval
        }


# Utility functions for risk calculations
def calculate_risk_score_from_level(risk_level: RiskLevel) -> float:
    """Convert risk level to numerical score (0-100)."""
    level_scores = {
        RiskLevel.VERY_LOW: 10,
        RiskLevel.LOW: 25,
        RiskLevel.MEDIUM: 50,
        RiskLevel.HIGH: 75,
        RiskLevel.VERY_HIGH: 90,
        RiskLevel.EXTREME: 95
    }
    return level_scores.get(risk_level, 50)


def get_risk_level_from_score(score: float) -> RiskLevel:
    """Convert numerical score to risk level."""
    if score <= 20:
        return RiskLevel.VERY_LOW
    elif score <= 40:
        return RiskLevel.LOW
    elif score <= 60:
        return RiskLevel.MEDIUM
    elif score <= 80:
        return RiskLevel.HIGH
    elif score <= 90:
        return RiskLevel.VERY_HIGH
    else:
        return RiskLevel.EXTREME