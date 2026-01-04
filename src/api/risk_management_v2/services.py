"""
Risk Management API v2 - Business Services
==========================================

Service layer for risk management business logic.

Author: CBSC Risk Management Team
Version: 2.0.0
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
import pandas as pd
import numpy as np

from .models import (
    RiskMetricsResponse, VaRMetrics, ExpectedShortfallMetrics,
    DrawdownMetrics, VolatilityMetrics, CorrelationMetrics,
    AlertConfiguration, AlertResponse, AlertLevel, AlertStatus,
    ReportRequest, ReportResponse, ReportFormat,
    AdjustmentRequest, AdjustmentResponse, PositionAdjustment,
    AdjustmentHistory, AdjustmentType,
    RiskRecommendation, APIResponse, ErrorResponse,
    PaginationParams, WebSocketMessage
)
from .database import (
    RiskMetrics as DBRiskMetrics,
    AlertConfiguration as DBAlertConfiguration,
    Alert as DBAlert,
    RiskReport as DBRiskReport,
    RiskAdjustment as DBRiskAdjustment,
    RiskRecommendation as DBRiskRecommendation
)
from ..risk_monitor.risk_engine import RiskEngine
from ..risk_monitor.config import RiskConfig

logger = logging.getLogger(__name__)


class RiskMetricsService:
    """Service for managing risk metrics"""

    def __init__(self, db: Session, risk_engine: RiskEngine):
        self.db = db
        self.risk_engine = risk_engine

    async def get_portfolio_risk_metrics(
        self,
        portfolio_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> RiskMetricsResponse:
        """Get latest risk metrics for a portfolio"""
        try:
            # Get latest metrics from database
            query = self.db.query(DBRiskMetrics).filter(
                DBRiskMetrics.portfolio_id == portfolio_id
            )

            if end_date:
                query = query.filter(DBRiskMetrics.timestamp <= end_date)

            latest_metric = query.order_by(desc(DBRiskMetrics.timestamp)).first()

            if not latest_metric:
                # Try to calculate from risk engine
                try:
                    metrics = await self.risk_engine.run_risk_calculation(
                        portfolio_id=portfolio_id,
                        force_refresh=True
                    )
                    return self._convert_engine_metrics(metrics, portfolio_id)
                except Exception as e:
                    logger.error(f"Failed to calculate risk metrics: {e}")
                    raise ValueError(f"No risk metrics found for portfolio {portfolio_id}")

            return self._convert_db_metrics(latest_metric)

        except Exception as e:
            logger.error(f"Error getting portfolio risk metrics: {e}")
            raise

    async def get_strategy_risk_metrics(
        self,
        strategy_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[RiskMetricsResponse]:
        """Get risk metrics for a strategy"""
        try:
            query = self.db.query(DBRiskMetrics).filter(
                DBRiskMetrics.strategy_id == strategy_id
            )

            if start_date:
                query = query.filter(DBRiskMetrics.timestamp >= start_date)
            if end_date:
                query = query.filter(DBRiskMetrics.timestamp <= end_date)

            metrics = query.order_by(desc(DBRiskMetrics.timestamp)).limit(100).all()

            return [self._convert_db_metrics(m) for m in metrics]

        except Exception as e:
            logger.error(f"Error getting strategy risk metrics: {e}")
            raise

    async def get_risk_metrics_history(
        self,
        portfolio_id: str,
        start_date: datetime,
        end_date: datetime,
        pagination: PaginationParams
    ) -> Tuple[List[RiskMetricsResponse], int]:
        """Get historical risk metrics with pagination"""
        try:
            query = self.db.query(DBRiskMetrics).filter(
                and_(
                    DBRiskMetrics.portfolio_id == portfolio_id,
                    DBRiskMetrics.timestamp >= start_date,
                    DBRiskMetrics.timestamp <= end_date
                )
            )

            # Get total count
            total = query.count()

            # Apply pagination
            if pagination.sort_by:
                order_column = getattr(DBRiskMetrics, pagination.sort_by, DBRiskMetrics.timestamp)
                if pagination.sort_order == "desc":
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(asc(order_column))
            else:
                query = query.order_by(desc(DBRiskMetrics.timestamp))

            query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)

            metrics = query.all()

            return [self._convert_db_metrics(m) for m in metrics], total

        except Exception as e:
            logger.error(f"Error getting risk metrics history: {e}")
            raise

    def _convert_db_metrics(self, db_metric: DBRiskMetrics) -> RiskMetricsResponse:
        """Convert database metric to response model"""
        return RiskMetricsResponse(
            timestamp=db_metric.timestamp,
            portfolio_id=db_metric.portfolio_id,
            strategy_id=db_metric.strategy_id,
            var_metrics=VaRMetrics(
                confidence_95_historical=db_metric.var_95_historical,
                confidence_95_parametric=db_metric.var_95_parametric,
                confidence_99_historical=db_metric.var_99_historical,
                confidence_99_parametric=db_metric.var_99_parametric
            ),
            expected_shortfall=ExpectedShortfallMetrics(
                confidence_95_historical=db_metric.es_95_historical,
                confidence_95_parametric=db_metric.es_95_parametric,
                confidence_99_historical=db_metric.es_99_historical,
                confidence_99_parametric=db_metric.es_99_parametric
            ),
            drawdown_metrics=DrawdownMetrics(
                max_drawdown=db_metric.max_drawdown,
                current_drawdown=db_metric.current_drawdown,
                max_drawdown_duration=db_metric.max_drawdown_duration,
                avg_drawdown=db_metric.avg_drawdown,
                recovery_time=db_metric.recovery_time
            ),
            volatility_metrics=VolatilityMetrics(
                daily=db_metric.volatility_daily,
                monthly=db_metric.volatility_monthly,
                annualized=db_metric.volatility_annualized,
                regime=db_metric.volatility_regime
            ),
            correlation_metrics=CorrelationMetrics(
                average_correlation=db_metric.avg_correlation,
                max_correlation=db_metric.max_correlation,
                effective_positions=db_metric.effective_positions,
                concentration_ratio=db_metric.concentration_ratio
            ),
            sharpe_ratio=db_metric.sharpe_ratio,
            sortino_ratio=db_metric.sortino_ratio,
            calmar_ratio=db_metric.calmar_ratio,
            information_ratio=db_metric.information_ratio,
            beta=db_metric.beta,
            tail_ratio=db_metric.tail_ratio,
            skewness=db_metric.skewness,
            excess_kurtosis=db_metric.excess_kurtosis
        )

    def _convert_engine_metrics(self, metrics: Dict[str, float], portfolio_id: str) -> RiskMetricsResponse:
        """Convert risk engine metrics to response model"""
        # Extract and map engine metrics to response format
        var_metrics = VaRMetrics(
            confidence_95_historical=metrics.get("var_95_historical", 0),
            confidence_95_parametric=metrics.get("var_95_parametric", 0),
            confidence_99_historical=metrics.get("var_99_historical", 0),
            confidence_99_parametric=metrics.get("var_99_parametric", 0)
        )

        es_metrics = ExpectedShortfallMetrics(
            confidence_95_historical=metrics.get("es_95_historical", 0),
            confidence_95_parametric=metrics.get("es_95_parametric", 0),
            confidence_99_historical=metrics.get("es_99_historical", 0),
            confidence_99_parametric=metrics.get("es_99_parametric", 0)
        )

        drawdown_metrics = DrawdownMetrics(
            max_drawdown=metrics.get("max_drawdown", 0),
            current_drawdown=metrics.get("current_drawdown", 0),
            max_drawdown_duration=metrics.get("drawdown_duration", 0),
            avg_drawdown=metrics.get("avg_drawdown", 0)
        )

        volatility_metrics = VolatilityMetrics(
            daily=metrics.get("volatility_1d", 0),
            monthly=metrics.get("volatility_21d", 0),
            annualized=metrics.get("volatility_252d", 0),
            regime=metrics.get("volatility_regime", "medium")
        )

        correlation_metrics = CorrelationMetrics(
            average_correlation=metrics.get("avg_correlation", 0),
            max_correlation=metrics.get("max_correlation", 0),
            effective_positions=metrics.get("effective_positions", 1),
            concentration_ratio=metrics.get("concentration_ratio", 1)
        )

        return RiskMetricsResponse(
            timestamp=datetime.now(),
            portfolio_id=portfolio_id,
            var_metrics=var_metrics,
            expected_shortfall=es_metrics,
            drawdown_metrics=drawdown_metrics,
            volatility_metrics=volatility_metrics,
            correlation_metrics=correlation_metrics,
            sharpe_ratio=metrics.get("sharpe_ratio"),
            sortino_ratio=metrics.get("sortino_ratio"),
            calmar_ratio=metrics.get("calmar_ratio"),
            beta=metrics.get("beta")
        )


class AlertService:
    """Service for managing risk alerts"""

    def __init__(self, db: Session, risk_engine: RiskEngine):
        self.db = db
        self.risk_engine = risk_engine

    async def create_alert_configuration(self, config: AlertConfiguration, user_id: str) -> str:
        """Create a new alert configuration"""
        try:
            db_config = DBAlertConfiguration(
                name=config.name,
                metric_type=config.metric_type.value,
                portfolio_id=config.portfolio_id,
                strategy_id=config.strategy_id,
                threshold_warning=config.threshold_warning,
                threshold_error=config.threshold_error,
                threshold_critical=config.threshold_critical,
                comparison_operator=config.comparison_operator,
                cooldown_period=config.cooldown_period,
                enabled=config.enabled,
                notification_channels=config.notification_channels,
                created_by=user_id
            )

            self.db.add(db_config)
            self.db.commit()

            # Configure alert thresholds in risk engine
            if config.enabled:
                thresholds = {
                    config.name: {
                        "type": config.metric_type.value,
                        "warning": config.threshold_warning,
                        "error": config.threshold_error,
                        "critical": config.threshold_critical,
                        "operator": config.comparison_operator,
                        "cooldown": config.cooldown_period
                    }
                }
                self.risk_engine.configure_alert_thresholds(thresholds)

            return str(db_config.id)

        except Exception as e:
            logger.error(f"Error creating alert configuration: {e}")
            self.db.rollback()
            raise

    async def update_alert_configuration(
        self,
        config_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update an existing alert configuration"""
        try:
            db_config = self.db.query(DBAlertConfiguration).filter(
                DBAlertConfiguration.id == config_id
            ).first()

            if not db_config:
                return False

            # Update fields
            for key, value in updates.items():
                if hasattr(db_config, key):
                    setattr(db_config, key, value)

            db_config.updated_at = datetime.utcnow()
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error updating alert configuration: {e}")
            self.db.rollback()
            return False

    async def delete_alert_configuration(self, config_id: str) -> bool:
        """Delete an alert configuration"""
        try:
            db_config = self.db.query(DBAlertConfiguration).filter(
                DBAlertConfiguration.id == config_id
            ).first()

            if not db_config:
                return False

            self.db.delete(db_config)
            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error deleting alert configuration: {e}")
            self.db.rollback()
            return False

    async def get_alert_configurations(
        self,
        portfolio_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[AlertResponse]:
        """Get alert configurations"""
        try:
            query = self.db.query(DBAlertConfiguration)

            if portfolio_id:
                query = query.filter(DBAlertConfiguration.portfolio_id == portfolio_id)
            if strategy_id:
                query = query.filter(DBAlertConfiguration.strategy_id == strategy_id)
            if enabled_only:
                query = query.filter(DBAlertConfiguration.enabled == True)

            configs = query.all()

            # Convert to response models (without actual alerts)
            responses = []
            for config in configs:
                response = AlertResponse(
                    id=str(config.id),
                    configuration=AlertConfiguration(
                        name=config.name,
                        metric_type=config.metric_type,
                        portfolio_id=config.portfolio_id,
                        strategy_id=config.strategy_id,
                        threshold_warning=config.threshold_warning,
                        threshold_error=config.threshold_error,
                        threshold_critical=config.threshold_critical,
                        comparison_operator=config.comparison_operator,
                        cooldown_period=config.cooldown_period,
                        enabled=config.enabled,
                        notification_channels=config.notification_channels or []
                    ),
                    level=AlertLevel.LOW,  # Default for configuration
                    status=AlertStatus.ACTIVE if config.enabled else AlertStatus.SUPPRESSED,
                    message="Configuration active",
                    current_value=0.0,
                    threshold=0.0,
                    created_at=config.created_at,
                    updated_at=config.updated_at,
                    portfolio_id=config.portfolio_id,
                    strategy_id=config.strategy_id
                )
                responses.append(response)

            return responses

        except Exception as e:
            logger.error(f"Error getting alert configurations: {e}")
            raise

    async def get_active_alerts(
        self,
        portfolio_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        level: Optional[AlertLevel] = None,
        limit: int = 50
    ) -> List[AlertResponse]:
        """Get active alerts"""
        try:
            query = self.db.query(DBAlert).filter(
                DBAlert.status == "active"
            )

            if portfolio_id:
                query = query.filter(DBAlert.portfolio_id == portfolio_id)
            if strategy_id:
                query = query.filter(DBAlert.strategy_id == strategy_id)
            if level:
                query = query.filter(DBAlert.level == level.value)

            alerts = query.order_by(desc(DBAlert.created_at)).limit(limit).all()

            return [self._convert_db_alert(alert) for alert in alerts]

        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            raise

    async def resolve_alert(self, alert_id: str, user_id: str) -> bool:
        """Resolve an alert"""
        try:
            alert = self.db.query(DBAlert).filter(
                DBAlert.id == alert_id
            ).first()

            if not alert:
                return False

            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            alert.action_required = False

            self.db.commit()

            return True

        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            self.db.rollback()
            return False

    def _convert_db_alert(self, db_alert: DBAlert) -> AlertResponse:
        """Convert database alert to response model"""
        return AlertResponse(
            id=str(db_alert.id),
            configuration=AlertConfiguration(
                name=db_alert.configuration.name,
                metric_type=db_alert.configuration.metric_type,
                threshold_warning=db_alert.configuration.threshold_warning,
                threshold_error=db_alert.configuration.threshold_error,
                threshold_critical=db_alert.configuration.threshold_critical,
                comparison_operator=db_alert.configuration.comparison_operator,
                cooldown_period=db_alert.configuration.cooldown_period,
                enabled=db_alert.configuration.enabled
            ),
            level=AlertLevel(db_alert.level),
            status=AlertStatus(db_alert.status),
            message=db_alert.message,
            current_value=db_alert.current_value,
            threshold=db_alert.threshold,
            created_at=db_alert.created_at,
            updated_at=db_alert.updated_at,
            resolved_at=db_alert.resolved_at,
            portfolio_id=db_alert.portfolio_id,
            strategy_id=db_alert.strategy_id,
            action_taken=db_alert.action_taken
        )


class ReportService:
    """Service for generating risk reports"""

    def __init__(self, db: Session):
        self.db = db

    async def generate_report(self, request: ReportRequest, user_id: str) -> str:
        """Generate a risk report"""
        try:
            # Create report record
            report = DBRiskReport(
                portfolio_id=request.portfolio_id,
                strategy_id=request.strategy_id,
                report_type=request.report_type,
                start_date=request.start_date,
                end_date=request.end_date,
                metrics=[m.value for m in request.metrics],
                format=request.format.value,
                status="processing",
                created_by=user_id,
                include_charts=request.include_charts,
                include_recommendations=request.include_recommendations
            )

            self.db.add(report)
            self.db.commit()

            # Queue report generation in background
            # This would typically use a task queue like Celery
            asyncio.create_task(self._generate_report_async(str(report.id), request))

            return str(report.id)

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            self.db.rollback()
            raise

    async def get_report(self, report_id: str) -> Optional[ReportResponse]:
        """Get report details"""
        try:
            report = self.db.query(DBRiskReport).filter(
                DBRiskReport.id == report_id
            ).first()

            if not report:
                return None

            return ReportResponse(
                id=str(report.id),
                status=report.status,
                created_at=report.created_at,
                completed_at=report.completed_at,
                file_path=report.file_path,
                download_url=report.download_url,
                file_size=report.file_size,
                expires_at=report.expires_at
            )

        except Exception as e:
            logger.error(f"Error getting report: {e}")
            raise

    async def get_reports(
        self,
        portfolio_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        pagination: PaginationParams = None
    ) -> Tuple[List[ReportResponse], int]:
        """Get reports with pagination"""
        try:
            query = self.db.query(DBRiskReport)

            if portfolio_id:
                query = query.filter(DBRiskReport.portfolio_id == portfolio_id)
            if strategy_id:
                query = query.filter(DBRiskReport.strategy_id == strategy_id)

            # Get total count
            total = query.count()

            # Apply pagination
            if pagination:
                query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)

            reports = query.order_by(desc(DBRiskReport.created_at)).all()

            responses = [
                ReportResponse(
                    id=str(r.id),
                    status=r.status,
                    created_at=r.created_at,
                    completed_at=r.completed_at,
                    file_path=r.file_path,
                    download_url=r.download_url,
                    file_size=r.file_size,
                    expires_at=r.expires_at
                )
                for r in reports
            ]

            return responses, total

        except Exception as e:
            logger.error(f"Error getting reports: {e}")
            raise

    async def _generate_report_async(self, report_id: str, request: ReportRequest):
        """Generate report in background"""
        try:
            # Get risk metrics for the period
            # This would typically query the risk metrics database
            # For now, generate mock data

            report_content = {
                "portfolio_id": request.portfolio_id,
                "strategy_id": request.strategy_id,
                "period": {
                    "start": request.start_date.isoformat(),
                    "end": request.end_date.isoformat()
                },
                "metrics": {},
                "recommendations": [],
                "charts": []
            }

            # Update report with content
            report = self.db.query(DBRiskReport).filter(
                DBRiskReport.id == report_id
            ).first()

            if report:
                report.status = "completed"
                report.completed_at = datetime.utcnow()
                report.content = report_content if request.format == ReportFormat.JSON else None

                # Set expiry (24 hours from now)
                report.expires_at = datetime.utcnow() + timedelta(hours=24)

                self.db.commit()

        except Exception as e:
            logger.error(f"Error generating report {report_id}: {e}")
            # Update status to failed
            report = self.db.query(DBRiskReport).filter(
                DBRiskReport.id == report_id
            ).first()
            if report:
                report.status = "failed"
                self.db.commit()


class AdjustmentService:
    """Service for dynamic risk adjustments"""

    def __init__(self, db: Session, risk_engine: RiskEngine):
        self.db = db
        self.risk_engine = risk_engine

    async def evaluate_adjustments(self, request: AdjustmentRequest) -> AdjustmentResponse:
        """Evaluate and suggest dynamic adjustments"""
        try:
            # Get current risk metrics
            current_metrics = await self.risk_engine.run_risk_calculation(
                portfolio_id=request.portfolio_id,
                force_refresh=True
            )

            # Generate adjustment suggestions
            adjustments = self._generate_adjustment_suggestions(
                current_positions=request.current_positions,
                risk_metrics=current_metrics,
                risk_budget=request.risk_budget,
                target_leverage=request.target_leverage
            )

            # Store adjustment request
            adjustment_record = DBRiskAdjustment(
                portfolio_id=request.portfolio_id,
                request_id=str(uuid.uuid4()),
                adjustment_type=request.adjustment_type.value,
                trigger={
                    "risk_budget": request.risk_budget,
                    "target_leverage": request.target_leverage,
                    "current_risk": current_metrics
                },
                adjustments=[adj.dict() for adj in adjustments],
                pre_adjustment_risk=current_metrics
            )

            self.db.add(adjustment_record)
            self.db.commit()

            # Calculate summary
            total_adjustment = sum([adj.suggested_size - adj.current_size for adj in adjustments])
            risk_reduction = sum([abs(adj.risk_impact) for adj in adjustments])

            summary = {
                "total_adjustment_count": len(adjustments),
                "net_leverage_change": total_adjustment,
                "risk_reduction_estimate": risk_reduction,
                "execution_priority": "high" if risk_reduction > 0.1 else "medium"
            }

            return AdjustmentResponse(
                request_id=adjustment_record.request_id,
                portfolio_id=request.portfolio_id,
                adjustments=adjustments,
                summary=summary,
                created_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Error evaluating adjustments: {e}")
            raise

    async def get_adjustment_history(
        self,
        portfolio_id: str,
        pagination: PaginationParams
    ) -> Tuple[List[AdjustmentHistory], int]:
        """Get adjustment history"""
        try:
            query = self.db.query(DBRiskAdjustment).filter(
                DBRiskAdjustment.portfolio_id == portfolio_id
            )

            # Get total count
            total = query.count()

            # Apply pagination
            query = query.order_by(desc(DBRiskAdjustment.created_at))
            query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)

            adjustments = query.all()

            responses = [
                AdjustmentHistory(
                    id=str(adj.id),
                    portfolio_id=adj.portfolio_id,
                    adjustment_type=AdjustmentType(adj.adjustment_type),
                    trigger=adj.trigger,
                    adjustments=[PositionAdjustment(**a) for a in adj.adjustments],
                    executed_at=adj.executed_at,
                    execution_status=adj.execution_status,
                    pre_adjustment_risk=adj.pre_adjustment_risk or {},
                    post_adjustment_risk=adj.post_adjustment_risk or {}
                )
                for adj in adjustments
            ]

            return responses, total

        except Exception as e:
            logger.error(f"Error getting adjustment history: {e}")
            raise

    def _generate_adjustment_suggestions(
        self,
        current_positions: Dict[str, float],
        risk_metrics: Dict[str, float],
        risk_budget: float,
        target_leverage: float
    ) -> List[PositionAdjustment]:
        """Generate adjustment suggestions"""
        adjustments = []

        # Simple risk parity adjustment logic
        current_vol = risk_metrics.get("volatility_21d", 0.02)
        if current_vol > risk_budget:
            # Reduce positions proportionally
            reduction_factor = risk_budget / current_vol
            reduction_factor = max(0.5, reduction_factor)  # Cap reduction at 50%

            for asset, size in current_positions.items():
                suggested_size = size * reduction_factor
                adjustments.append(PositionAdjustment(
                    asset=asset,
                    current_size=size,
                    suggested_size=suggested_size,
                    adjustment_reason=f"Volatility reduction: {current_vol:.2%} > {risk_budget:.2%}",
                    risk_impact=size - suggested_size,
                    expected_return_impact=-0.001,  # Simplified
                    priority=1 if abs(size - suggested_size) > 0.1 else 2
                ))

        return adjustments