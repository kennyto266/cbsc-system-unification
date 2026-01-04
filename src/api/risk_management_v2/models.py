"""
Risk Management API v2 - Data Models
=====================================

Pydantic models for risk management API requests and responses.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import numpy as np


class RiskMetricType(str, Enum):
    """Risk metric types"""
    VAR = "var"
    EXPECTED_SHORTFALL = "expected_shortfall"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    BETA = "beta"
    CORRELATION = "correlation"
    CONCENTRATION = "concentration"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class ReportFormat(str, Enum):
    """Report export formats"""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    EXCEL = "excel"


class AdjustmentType(str, Enum):
    """Risk adjustment types"""
    POSITION_SCALING = "position_scaling"
    VOLATILITY_TARGETING = "volatility_targeting"
    STOP_LOSS = "stop_loss"
    REBALANCING = "rebalancing"
    EMERGENCY_EXIT = "emergency_exit"


class TimeHorizon(str, Enum):
    """Analysis time horizons"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


# Base Models

class BaseRiskModel(BaseModel):
    """Base model for risk data"""
    timestamp: datetime = Field(..., description="Timestamp of the risk calculation")
    portfolio_id: Optional[str] = Field(None, description="Portfolio identifier")
    strategy_id: Optional[str] = Field(None, description="Strategy identifier")


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=1000, description="Page size")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("desc", regex="^(asc|desc)$", description="Sort order")


# Risk Metrics Models

class VaRMetrics(BaseModel):
    """Value at Risk metrics"""
    confidence_95_historical: float = Field(..., description="95% VaR (historical)")
    confidence_95_parametric: float = Field(..., description="95% VaR (parametric)")
    confidence_99_historical: float = Field(..., description="99% VaR (historical)")
    confidence_99_parametric: float = Field(..., description="99% VaR (parametric)")

    @validator('confidence_95_historical', 'confidence_95_parametric')
    def validate_var_95(cls, v):
        if not -1 <= v <= 0:
            raise ValueError('VaR must be between -1 and 0')
        return v

    @validator('confidence_99_historical', 'confidence_99_parametric')
    def validate_var_99(cls, v):
        if not -1 <= v <= 0:
            raise ValueError('VaR must be between -1 and 0')
        return v


class ExpectedShortfallMetrics(BaseModel):
    """Expected Shortfall metrics"""
    confidence_95_historical: float = Field(..., description="95% ES (historical)")
    confidence_95_parametric: float = Field(..., description="95% ES (parametric)")
    confidence_99_historical: float = Field(..., description="99% ES (historical)")
    confidence_99_parametric: float = Field(..., description="99% ES (parametric)")


class DrawdownMetrics(BaseModel):
    """Drawdown metrics"""
    max_drawdown: float = Field(..., description="Maximum drawdown")
    current_drawdown: float = Field(..., description="Current drawdown")
    max_drawdown_duration: int = Field(..., description="Maximum drawdown duration (days)")
    avg_drawdown: float = Field(..., description="Average drawdown")
    recovery_time: Optional[int] = Field(None, description="Current recovery time (days)")


class VolatilityMetrics(BaseModel):
    """Volatility metrics"""
    daily: float = Field(..., description="Daily volatility")
    monthly: float = Field(..., description="Monthly volatility")
    annualized: float = Field(..., description="Annualized volatility")
    regime: str = Field(..., description="Volatility regime (low/medium/high)")


class CorrelationMetrics(BaseModel):
    """Correlation metrics"""
    average_correlation: float = Field(..., description="Average correlation")
    max_correlation: float = Field(..., description="Maximum correlation")
    effective_positions: float = Field(..., description="Effective number of positions")
    concentration_ratio: float = Field(..., description="Concentration ratio")


class RiskMetricsResponse(BaseRiskModel):
    """Comprehensive risk metrics response"""
    var_metrics: VaRMetrics
    expected_shortfall: ExpectedShortfallMetrics
    drawdown_metrics: DrawdownMetrics
    volatility_metrics: VolatilityMetrics
    correlation_metrics: CorrelationMetrics
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    sortino_ratio: Optional[float] = Field(None, description="Sortino ratio")
    calmar_ratio: Optional[float] = Field(None, description="Calmar ratio")
    information_ratio: Optional[float] = Field(None, description="Information ratio")
    beta: Optional[float] = Field(None, description="Beta relative to market")
    tail_ratio: Optional[float] = Field(None, description="Tail ratio")
    skewness: Optional[float] = Field(None, description="Skewness")
    excess_kurtosis: Optional[float] = Field(None, description="Excess kurtosis")


class RiskMetricsList(BaseModel):
    """List of risk metrics with pagination"""
    items: List[RiskMetricsResponse]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Alert Models

class AlertConfiguration(BaseModel):
    """Alert configuration"""
    name: str = Field(..., description="Alert name")
    metric_type: RiskMetricType = Field(..., description="Risk metric type")
    threshold_warning: Optional[float] = Field(None, description="Warning threshold")
    threshold_error: Optional[float] = Field(None, description="Error threshold")
    threshold_critical: Optional[float] = Field(None, description="Critical threshold")
    comparison_operator: str = Field("greater_than", regex="^(greater_than|less_than|equals)$")
    cooldown_period: int = Field(300, description="Cooldown period in seconds")
    enabled: bool = Field(True, description="Whether alert is enabled")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")


class AlertResponse(BaseModel):
    """Alert response"""
    id: str = Field(..., description="Alert ID")
    configuration: AlertConfiguration
    level: AlertLevel
    status: AlertStatus
    message: str = Field(..., description="Alert message")
    current_value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Threshold that was breached")
    created_at: datetime = Field(..., description="Alert creation time")
    updated_at: datetime = Field(..., description="Alert update time")
    resolved_at: Optional[datetime] = Field(None, description="Alert resolution time")
    portfolio_id: Optional[str] = Field(None, description="Portfolio ID")
    strategy_id: Optional[str] = Field(None, description="Strategy ID")
    action_taken: Optional[str] = Field(None, description="Action taken for the alert")


class AlertList(BaseModel):
    """List of alerts with pagination"""
    items: List[AlertResponse]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Report Models

class ReportRequest(BaseModel):
    """Risk report generation request"""
    portfolio_id: Optional[str] = Field(None, description="Portfolio ID")
    strategy_id: Optional[str] = Field(None, description="Strategy ID")
    report_type: str = Field(..., description="Report type")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    metrics: List[RiskMetricType] = Field(default_factory=list, description="Metrics to include")
    format: ReportFormat = Field(ReportFormat.JSON, description="Export format")
    include_charts: bool = Field(True, description="Include charts in report")
    include_recommendations: bool = Field(True, description="Include recommendations")

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class ReportResponse(BaseModel):
    """Risk report response"""
    id: str = Field(..., description="Report ID")
    status: str = Field(..., description="Report status")
    created_at: datetime = Field(..., description="Report creation time")
    completed_at: Optional[datetime] = Field(None, description="Report completion time")
    file_path: Optional[str] = Field(None, description="Report file path")
    download_url: Optional[str] = Field(None, description="Download URL")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    expires_at: Optional[datetime] = Field(None, description="Report expiry time")


class ReportList(BaseModel):
    """List of reports with pagination"""
    items: List[ReportResponse]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Adjustment Models

class AdjustmentRule(BaseModel):
    """Dynamic adjustment rule"""
    name: str = Field(..., description="Rule name")
    trigger_condition: Dict[str, Any] = Field(..., description="Trigger condition")
    adjustment_type: AdjustmentType = Field(..., description="Adjustment type")
    parameters: Dict[str, Any] = Field(..., description="Adjustment parameters")
    enabled: bool = Field(True, description="Whether rule is enabled")


class PositionAdjustment(BaseModel):
    """Position adjustment suggestion"""
    asset: str = Field(..., description="Asset identifier")
    current_size: float = Field(..., description="Current position size")
    suggested_size: float = Field(..., description="Suggested position size")
    adjustment_reason: str = Field(..., description="Reason for adjustment")
    risk_impact: float = Field(..., description="Risk impact score")
    expected_return_impact: float = Field(..., description="Expected return impact")
    priority: int = Field(..., description="Adjustment priority")


class AdjustmentRequest(BaseModel):
    """Dynamic adjustment request"""
    portfolio_id: str = Field(..., description="Portfolio ID")
    current_positions: Dict[str, float] = Field(..., description="Current positions")
    risk_budget: float = Field(0.02, description="Daily risk budget")
    target_leverage: float = Field(1.0, description="Target leverage")
    adjustment_type: AdjustmentType = Field(AdjustmentType.POSITION_SCALING)
    max_adjustment_pct: float = Field(0.3, description="Maximum adjustment percentage")


class AdjustmentResponse(BaseModel):
    """Dynamic adjustment response"""
    request_id: str = Field(..., description="Request ID")
    portfolio_id: str = Field(..., description="Portfolio ID")
    adjustments: List[PositionAdjustment]
    summary: Dict[str, Any] = Field(..., description="Adjustment summary")
    created_at: datetime = Field(..., description="Response timestamp")


class AdjustmentHistory(BaseModel):
    """Adjustment history record"""
    id: str = Field(..., description="Record ID")
    portfolio_id: str = Field(..., description="Portfolio ID")
    adjustment_type: AdjustmentType = Field(..., description="Adjustment type")
    trigger: Dict[str, Any] = Field(..., description="Adjustment trigger")
    adjustments: List[PositionAdjustment]
    executed_at: datetime = Field(..., description="Execution time")
    execution_status: str = Field(..., description="Execution status")
    pre_adjustment_risk: Dict[str, float] = Field(..., description="Risk before adjustment")
    post_adjustment_risk: Dict[str, float] = Field(..., description="Risk after adjustment")


class AdjustmentHistoryList(BaseModel):
    """List of adjustment history with pagination"""
    items: List[AdjustmentHistory]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# WebSocket Models

class WebSocketMessage(BaseModel):
    """WebSocket message base"""
    type: str = Field(..., description="Message type")
    timestamp: datetime = Field(..., description="Message timestamp")
    data: Dict[str, Any] = Field(..., description="Message data")


class RiskUpdateMessage(WebSocketMessage):
    """Real-time risk update message"""
    type: str = Field("risk_update", const=True)
    portfolio_id: str = Field(..., description="Portfolio ID")
    risk_metrics: RiskMetricsResponse


class AlertMessage(WebSocketMessage):
    """Real-time alert message"""
    type: str = Field("alert", const=True)
    alert: AlertResponse


class AdjustmentMessage(WebSocketMessage):
    """Real-time adjustment message"""
    type: str = Field("adjustment", const=True)
    portfolio_id: str = Field(..., description="Portfolio ID")
    adjustment: AdjustmentResponse


# Recommendation Models

class RiskRecommendation(BaseModel):
    """Risk management recommendation"""
    id: str = Field(..., description="Recommendation ID")
    type: str = Field(..., description="Recommendation type")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    priority: str = Field(..., regex="^(low|medium|high|critical)$")
    impact: str = Field(..., regex="^(low|medium|high)$")
    effort: str = Field(..., regex="^(low|medium|high)$")
    metrics: List[RiskMetricType] = Field(..., description="Related metrics")
    actions: List[str] = Field(..., description="Recommended actions")
    expected_benefit: str = Field(..., description="Expected benefit")
    created_at: datetime = Field(..., description="Creation time")


class RecommendationList(BaseModel):
    """List of recommendations"""
    items: List[RiskRecommendation]
    total: int = Field(..., description="Total number of items")


# API Response Models

class APIResponse(BaseModel):
    """Standard API response"""
    success: bool = Field(..., description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = Field(False, const=True)
    error: Dict[str, Any] = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")