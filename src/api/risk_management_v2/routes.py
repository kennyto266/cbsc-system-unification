"""
Risk Management API v2 - Routes
================================

FastAPI routes for risk management endpoints.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from .models import (
    RiskMetricsResponse, RiskMetricsList, RiskMetricType,
    AlertConfiguration, AlertResponse, AlertLevel, AlertStatus, AlertList,
    ReportRequest, ReportResponse, ReportList, ReportFormat,
    AdjustmentRequest, AdjustmentResponse, AdjustmentHistoryList, AdjustmentType,
    RiskRecommendation, RecommendationList,
    APIResponse, ErrorResponse, PaginationParams
)
from .services import (
    RiskMetricsService, AlertService, ReportService, AdjustmentService
)
from .dependencies import get_risk_engine, get_database, get_current_user
from ..middleware import rate_limit, require_permissions

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v2/risk",
    tags=["Risk Management"],
    responses={404: {"description": "Not found"}}
)


# Risk Metrics Endpoints

@router.get(
    "/portfolio/{portfolio_id}",
    response_model=RiskMetricsResponse,
    summary="Get portfolio risk metrics",
    description="Retrieve the latest comprehensive risk metrics for a specific portfolio"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_portfolio_risk_metrics(
    portfolio_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Get latest risk metrics for a portfolio"""
    try:
        service = RiskMetricsService(db, risk_engine)
        metrics = await service.get_portfolio_risk_metrics(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date
        )
        return metrics

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting portfolio risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/strategy/{strategy_id}",
    response_model=List[RiskMetricsResponse],
    summary="Get strategy risk metrics",
    description="Retrieve risk metrics for all portfolios within a strategy"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_strategy_risk_metrics(
    strategy_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Get risk metrics for a strategy"""
    try:
        service = RiskMetricsService(db, risk_engine)
        metrics = await service.get_strategy_risk_metrics(
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date
        )
        return metrics[:limit]

    except Exception as e:
        logger.error(f"Error getting strategy risk metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/metrics",
    response_model=List[str],
    summary="Get available risk metrics",
    description="List all available risk metric types"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_available_metrics(
    current_user=Depends(get_current_user)
):
    """Get available risk metrics"""
    return [metric.value for metric in RiskMetricType]


@router.get(
    "/history",
    response_model=RiskMetricsList,
    summary="Get historical risk data",
    description="Retrieve historical risk metrics for analysis"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_risk_history(
    portfolio_id: str = Query(..., description="Portfolio ID"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=1000, description="Page size"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Get historical risk data"""
    try:
        service = RiskMetricsService(db, risk_engine)
        pagination = PaginationParams(
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        metrics, total = await service.get_risk_metrics_history(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            pagination=pagination
        )

        pages = (total + size - 1) // size

        return RiskMetricsList(
            items=metrics,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        logger.error(f"Error getting risk history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Alert Configuration Endpoints

@router.get(
    "/alerts",
    response_model=AlertList,
    summary="Get alert configurations",
    description="Retrieve all alert configurations"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_alerts(
    portfolio_id: Optional[str] = Query(None, description="Filter by portfolio ID"),
    strategy_id: Optional[str] = Query(None, description="Filter by strategy ID"),
    enabled_only: bool = Query(False, description="Only return enabled alerts"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=1000, description="Page size"),
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Get alert configurations"""
    try:
        service = AlertService(db, risk_engine)
        alerts = await service.get_alert_configurations(
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            enabled_only=enabled_only
        )

        # Apply pagination
        start = (page - 1) * size
        end = start + size
        paginated_alerts = alerts[start:end]

        return AlertList(
            items=paginated_alerts,
            total=len(alerts),
            page=page,
            size=size,
            pages=(len(alerts) + size - 1) // size
        )

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/alerts",
    response_model=APIResponse,
    summary="Create alert configuration",
    description="Create a new risk alert configuration"
)
@rate_limit("50/hour")
@require_permissions("risk:write")
async def create_alert(
    config: AlertConfiguration,
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Create alert configuration"""
    try:
        service = AlertService(db, risk_engine)
        alert_id = await service.create_alert_configuration(config, current_user.id)

        return APIResponse(
            success=True,
            message="Alert configuration created successfully",
            data={"alert_id": alert_id}
        )

    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put(
    "/alerts/{alert_id}",
    response_model=APIResponse,
    summary="Update alert configuration",
    description="Update an existing alert configuration"
)
@rate_limit("50/hour")
@require_permissions("risk:write")
async def update_alert(
    alert_id: str,
    updates: dict,
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Update alert configuration"""
    try:
        service = AlertService(db, risk_engine)
        success = await service.update_alert_configuration(alert_id, updates)

        if not success:
            raise HTTPException(status_code=404, detail="Alert configuration not found")

        return APIResponse(
            success=True,
            message="Alert configuration updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/alerts/{alert_id}",
    response_model=APIResponse,
    summary="Delete alert configuration",
    description="Delete an alert configuration"
)
@rate_limit("50/hour")
@require_permissions("risk:write")
async def delete_alert(
    alert_id: str,
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Delete alert configuration"""
    try:
        service = AlertService(db, risk_engine)
        success = await service.delete_alert_configuration(alert_id)

        if not success:
            raise HTTPException(status_code=404, detail="Alert configuration not found")

        return APIResponse(
            success=True,
            message="Alert configuration deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Report Generation Endpoints

@router.get(
    "/reports",
    response_model=ReportList,
    summary="Get reports list",
    description="Retrieve a list of generated risk reports"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_reports(
    portfolio_id: Optional[str] = Query(None, description="Filter by portfolio ID"),
    strategy_id: Optional[str] = Query(None, description="Filter by strategy ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=1000, description="Page size"),
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get reports list"""
    try:
        service = ReportService(db)
        pagination = PaginationParams(page=page, size=size)

        reports, total = await service.get_reports(
            portfolio_id=portfolio_id,
            strategy_id=strategy_id,
            pagination=pagination
        )

        pages = (total + size - 1) // size

        return ReportList(
            items=reports,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        logger.error(f"Error getting reports: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/reports",
    response_model=APIResponse,
    summary="Generate risk report",
    description="Generate a comprehensive risk report"
)
@rate_limit("20/hour")
@require_permissions("risk:read")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Generate risk report"""
    try:
        service = ReportService(db)
        report_id = await service.generate_report(request, current_user.id)

        return APIResponse(
            success=True,
            message="Report generation started",
            data={"report_id": report_id}
        )

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/reports/{report_id}",
    response_model=ReportResponse,
    summary="Get report details",
    description="Get details and status of a specific report"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_report(
    report_id: str,
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get report details"""
    try:
        service = ReportService(db)
        report = await service.get_report(report_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/reports/{report_id}/download",
    summary="Download report file",
    description="Download a generated report file"
)
@rate_limit("50/hour")
@require_permissions("risk:read")
async def download_report(
    report_id: str,
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Download report file"""
    try:
        service = ReportService(db)
        report = await service.get_report(report_id)

        if not report:
            raise HTTPException(status_code=404, detail="Report not found")

        if report.status != "completed":
            raise HTTPException(status_code=400, detail="Report not ready for download")

        if not report.file_path:
            raise HTTPException(status_code=404, detail="Report file not found")

        return FileResponse(
            path=report.file_path,
            filename=f"risk_report_{report_id}.{report.format}",
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Dynamic Risk Adjustment Endpoints

@router.get(
    "/adjustments",
    response_model=AdjustmentHistoryList,
    summary="Get adjustment history",
    description="Retrieve history of risk adjustments"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_adjustments(
    portfolio_id: str = Query(..., description="Portfolio ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=1000, description="Page size"),
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Get adjustment history"""
    try:
        service = AdjustmentService(db, risk_engine)
        pagination = PaginationParams(page=page, size=size)

        adjustments, total = await service.get_adjustment_history(
            portfolio_id=portfolio_id,
            pagination=pagination
        )

        pages = (total + size - 1) // size

        return AdjustmentHistoryList(
            items=adjustments,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        logger.error(f"Error getting adjustments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/adjustments",
    response_model=AdjustmentResponse,
    summary="Execute risk adjustment",
    description="Evaluate and execute dynamic risk adjustments"
)
@rate_limit("20/hour")
@require_permissions("risk:write")
async def execute_adjustment(
    request: AdjustmentRequest,
    db=Depends(get_database),
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Execute risk adjustment"""
    try:
        service = AdjustmentService(db, risk_engine)
        adjustment = await service.evaluate_adjustments(request)

        return adjustment

    except Exception as e:
        logger.error(f"Error executing adjustment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/recommendations",
    response_model=RecommendationList,
    summary="Get risk recommendations",
    description="Get AI-powered risk management recommendations"
)
@rate_limit("100/hour")
@require_permissions("risk:read")
async def get_recommendations(
    portfolio_id: Optional[str] = Query(None, description="Filter by portfolio ID"),
    strategy_id: Optional[str] = Query(None, description="Filter by strategy ID"),
    priority: Optional[str] = Query(None, regex="^(low|medium|high|critical)$", description="Filter by priority"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of recommendations"),
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get risk recommendations"""
    try:
        # Mock recommendations - in production, this would query the database
        recommendations = [
            RiskRecommendation(
                id="rec_001",
                type="volatility_reduction",
                title="Reduce portfolio volatility",
                description="Current portfolio volatility exceeds target. Consider reducing exposure to high-volatility assets.",
                priority="high",
                impact="high",
                effort="medium",
                metrics=[RiskMetricType.VOLATILITY],
                actions=["Reduce position size in high-beta assets", "Increase allocation to low-volatility assets"],
                expected_benefit="Reduce portfolio volatility by 15-20%",
                created_at=datetime.now()
            ),
            RiskRecommendation(
                id="rec_002",
                type="diversification",
                title="Improve portfolio diversification",
                description="Portfolio shows high concentration risk. Add more uncorrelated assets.",
                priority="medium",
                impact="medium",
                effort="high",
                metrics=[RiskMetricType.CONCENTRATION],
                actions=["Add assets from different sectors", "Consider international exposure"],
                expected_benefit="Reduce concentration ratio from 0.6 to 0.4",
                created_at=datetime.now()
            )
        ]

        return RecommendationList(
            items=recommendations[:limit],
            total=len(recommendations)
        )

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health and Status Endpoints

@router.get(
    "/health",
    summary="Health check",
    description="Check the health of the risk management service"
)
async def health_check():
    """Health check endpoint"""
    return APIResponse(
        success=True,
        message="Risk Management API is healthy",
        data={"version": "2.0.0"}
    )


@router.get(
    "/status",
    summary="Get service status",
    description="Get detailed status of the risk management service"
)
@require_permissions("risk:read")
async def get_status(
    risk_engine=Depends(get_risk_engine),
    current_user=Depends(get_current_user)
):
    """Get service status"""
    try:
        summary = risk_engine.get_risk_summary()

        return APIResponse(
            success=True,
            message="Service status retrieved successfully",
            data=summary
        )

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")