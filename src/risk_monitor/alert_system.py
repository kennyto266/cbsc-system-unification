"""
Risk Alert System

This module implements a comprehensive risk alert system including:
- Customizable risk thresholds
- Multi-level alert mechanism (Info, Warning, Error, Critical)
- Real-time risk monitoring
- Alert history and analytics
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from collections import deque
import json

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert categories"""
    VAR_BREACH = "var_breach"
    MAX_DRAWDOWN = "max_drawdown"
    VOLATILITY_SPIKE = "volatility_spike"
    CONCENTRATION_RISK = "concentration_risk"
    CORRELATION_RISK = "correlation_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    POSITION_LIMIT = "position_limit"
    SYSTEM_ERROR = "system_error"
    PERFORMANCE_DEGRADATION = "performance_degradation"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    level: AlertLevel
    type: AlertType
    title: str
    message: str
    timestamp: datetime
    source: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    asset_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        data = asdict(self)
        # Convert datetime to string
        data["timestamp"] = self.timestamp.isoformat() if self.timestamp else None
        data["acknowledged_at"] = self.acknowledged_at.isoformat() if self.acknowledged_at else None
        data["resolved_at"] = self.resolved_at.isoformat() if self.resolved_at else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Alert":
        """Create alert from dictionary"""
        # Convert string to datetime
        if data.get("timestamp"):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if data.get("acknowledged_at"):
            data["acknowledged_at"] = datetime.fromisoformat(data["acknowledged_at"])
        if data.get("resolved_at"):
            data["resolved_at"] = datetime.fromisoformat(data["resolved_at"])

        # Convert string enums
        if isinstance(data.get("level"), str):
            data["level"] = AlertLevel(data["level"])
        if isinstance(data.get("type"), str):
            data["type"] = AlertType(data["type"])

        return cls(**data)


class AlertThreshold:
    """Alert threshold configuration"""

    def __init__(
        self,
        name: str,
        metric_type: AlertType,
        warning_threshold: Optional[float] = None,
        error_threshold: Optional[float] = None,
        critical_threshold: Optional[float] = None,
        comparison_operator: str = "greater_than",
        cooldown_period: int = 60,
        enabled: bool = True
    ):
        """
        Initialize alert threshold

        Args:
            name: Threshold name
            metric_type: Type of metric
            warning_threshold: Warning level threshold
            error_threshold: Error level threshold
            critical_threshold: Critical level threshold
            comparison_operator: "greater_than", "less_than", "equal"
            cooldown_period: Cooldown period in seconds
            enabled: Whether threshold is enabled
        """
        self.name = name
        self.metric_type = metric_type
        self.warning_threshold = warning_threshold
        self.error_threshold = error_threshold
        self.critical_threshold = critical_threshold
        self.comparison_operator = comparison_operator
        self.cooldown_period = cooldown_period
        self.enabled = enabled
        self.last_triggered = {}  # Track last trigger time for each level

    def check_threshold(
        self,
        value: float,
        asset_id: Optional[str] = None,
        portfolio_id: Optional[str] = None
    ) -> Optional[AlertLevel]:
        """
        Check if value exceeds threshold

        Args:
            value: Current metric value
            asset_id: Asset identifier
            portfolio_id: Portfolio identifier

        Returns:
            Alert level if threshold exceeded, None otherwise
        """
        if not self.enabled:
            return None

        current_time = datetime.now()

        # Check cooldown period
        for level in [AlertLevel.CRITICAL, AlertLevel.ERROR, AlertLevel.WARNING]:
            threshold = getattr(self, f"{level.value}_threshold")
            if threshold is None:
                continue

            # Check if recently triggered
            key = f"{level.value}_{asset_id}_{portfolio_id}"
            if key in self.last_triggered:
                time_diff = (current_time - self.last_triggered[key]).total_seconds()
                if time_diff < self.cooldown_period:
                    continue

            # Check threshold
            if self._compare_value(value, threshold):
                self.last_triggered[key] = current_time
                return level

        return None

    def _compare_value(self, value: float, threshold: float) -> bool:
        """Compare value with threshold based on operator"""
        if self.comparison_operator == "greater_than":
            return value > threshold
        elif self.comparison_operator == "less_than":
            return value < threshold
        elif self.comparison_operator == "equal":
            return abs(value - threshold) < 1e-6
        elif self.comparison_operator == "greater_equal":
            return value >= threshold
        elif self.comparison_operator == "less_equal":
            return value <= threshold
        else:
            raise ValueError(f"Unknown operator: {self.comparison_operator}")


class AlertSystem:
    """Main alert system implementation"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize alert system

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.alert_id_counter = 0

        # Initialize default thresholds
        self._initialize_default_thresholds()

    def _initialize_default_thresholds(self):
        """Initialize default alert thresholds"""
        default_thresholds = [
            AlertThreshold(
                name="var_95",
                metric_type=AlertType.VAR_BREACH,
                warning_threshold=0.02,  # 2%
                error_threshold=0.05,     # 5%
                critical_threshold=0.10,  # 10%
                comparison_operator="greater_than"
            ),
            AlertThreshold(
                name="var_99",
                metric_type=AlertType.VAR_BREACH,
                warning_threshold=0.03,  # 3%
                error_threshold=0.07,    # 7%
                critical_threshold=0.15, # 15%
                comparison_operator="greater_than"
            ),
            AlertThreshold(
                name="max_drawdown",
                metric_type=AlertType.MAX_DRAWDOWN,
                warning_threshold=0.10,  # 10%
                error_threshold=0.20,    # 20%
                critical_threshold=0.30, # 30%
                comparison_operator="greater_than"
            ),
            AlertThreshold(
                name="volatility",
                metric_type=AlertType.VOLATILITY_SPIKE,
                warning_threshold=0.25,  # 25%
                error_threshold=0.40,    # 40%
                critical_threshold=0.60, # 60%
                comparison_operator="greater_than"
            ),
            AlertThreshold(
                name="concentration",
                metric_type=AlertType.CONCENTRATION_RISK,
                warning_threshold=0.30,  # 30%
                error_threshold=0.50,    # 50%
                critical_threshold=0.70, # 70%
                comparison_operator="greater_than"
            ),
            AlertThreshold(
                name="single_position",
                metric_type=AlertType.POSITION_LIMIT,
                warning_threshold=0.20,  # 20%
                error_threshold=0.30,    # 30%
                critical_threshold=0.40, # 40%
                comparison_operator="greater_than"
            )
        ]

        for threshold in default_thresholds:
            self.thresholds[threshold.name] = threshold

    def check_metrics(
        self,
        metrics: Dict[str, float],
        asset_id: Optional[str] = None,
        portfolio_id: Optional[str] = None
    ) -> List[Alert]:
        """
        Check metrics against thresholds and generate alerts

        Args:
            metrics: Dictionary of metric names and values
            asset_id: Asset identifier
            portfolio_id: Portfolio identifier

        Returns:
            List of generated alerts
        """
        alerts = []

        for metric_name, value in metrics.items():
            if metric_name not in self.thresholds:
                continue

            threshold = self.thresholds[metric_name]
            alert_level = threshold.check_threshold(value, asset_id, portfolio_id)

            if alert_level:
                alert = self._create_alert(
                    level=alert_level,
                    alert_type=threshold.metric_type,
                    metric_name=metric_name,
                    metric_value=value,
                    threshold_value=getattr(threshold, f"{alert_level.value}_threshold"),
                    asset_id=asset_id,
                    portfolio_id=portfolio_id
                )
                alerts.append(alert)
                self._process_alert(alert)

        return alerts

    def create_custom_alert(
        self,
        level: AlertLevel,
        alert_type: AlertType,
        title: str,
        message: str,
        source: str = "manual",
        asset_id: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """
        Create a custom alert

        Args:
            level: Alert severity level
            alert_type: Alert category
            title: Alert title
            message: Alert message
            source: Alert source
            asset_id: Asset identifier
            portfolio_id: Portfolio identifier
            metadata: Additional metadata

        Returns:
            Created alert
        """
        alert = self._create_alert(
            level=level,
            alert_type=alert_type,
            title=title,
            message=message,
            source=source,
            asset_id=asset_id,
            portfolio_id=portfolio_id,
            metadata=metadata
        )

        self._process_alert(alert)
        return alert

    def _create_alert(
        self,
        level: AlertLevel,
        alert_type: AlertType,
        title: Optional[str] = None,
        message: Optional[str] = None,
        source: str = "risk_monitor",
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        asset_id: Optional[str] = None,
        portfolio_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a new alert"""
        self.alert_id_counter += 1
        alert_id = f"alert_{self.alert_id_counter}_{int(datetime.now().timestamp())}"

        # Generate default title and message if not provided
        if title is None:
            title = f"{alert_type.value.replace('_', ' ').title()} Alert"
        if message is None:
            if metric_name and metric_value is not None and threshold_value is not None:
                message = f"{metric_name} is {metric_value:.2%}, exceeding {level.value} threshold of {threshold_value:.2%}"
            else:
                message = f"{level.value.upper()}: {alert_type.value}"

        alert = Alert(
            id=alert_id,
            level=level,
            type=alert_type,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_value=threshold_value,
            asset_id=asset_id,
            portfolio_id=portfolio_id,
            metadata=metadata
        )

        return alert

    def _process_alert(self, alert: Alert):
        """Process a new alert"""
        # Add to active alerts
        self.active_alerts[alert.id] = alert

        # Add to history
        self.alert_history.append(alert)

        # Log the alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }.get(alert.level, logging.INFO)

        logger.log(
            log_level,
            f"Alert [{alert.level.value.upper()}] {alert.title}: {alert.message}"
        )

        # Trigger handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str = "system"
    ) -> bool:
        """
        Acknowledge an alert

        Args:
            alert_id: Alert ID
            acknowledged_by: Who acknowledged the alert

        Returns:
            True if successful, False if alert not found
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        return False

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str = "system"
    ) -> bool:
        """
        Resolve an alert

        Args:
            alert_id: Alert ID
            resolved_by: Who resolved the alert

        Returns:
            True if successful, False if alert not found
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            logger.info(f"Alert {alert_id} resolved by {resolved_by}")

            # Remove from active alerts
            del self.active_alerts[alert_id]
            return True
        return False

    def get_active_alerts(
        self,
        level: Optional[AlertLevel] = None,
        alert_type: Optional[AlertType] = None,
        asset_id: Optional[str] = None,
        portfolio_id: Optional[str] = None
    ) -> List[Alert]:
        """
        Get active alerts with optional filters

        Args:
            level: Filter by alert level
            alert_type: Filter by alert type
            asset_id: Filter by asset ID
            portfolio_id: Filter by portfolio ID

        Returns:
            Filtered list of active alerts
        """
        alerts = list(self.active_alerts.values())

        # Apply filters
        if level:
            alerts = [a for a in alerts if a.level == level]
        if alert_type:
            alerts = [a for a in alerts if a.type == alert_type]
        if asset_id:
            alerts = [a for a in alerts if a.asset_id == asset_id]
        if portfolio_id:
            alerts = [a for a in alerts if a.portfolio_id == portfolio_id]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        return alerts

    def get_alert_history(
        self,
        hours: Optional[int] = None,
        level: Optional[AlertLevel] = None,
        alert_type: Optional[AlertType] = None,
        limit: Optional[int] = None
    ) -> List[Alert]:
        """
        Get alert history with optional filters

        Args:
            hours: Filter by last N hours
            level: Filter by alert level
            alert_type: Filter by alert type
            limit: Maximum number of alerts to return

        Returns:
            Filtered list of historical alerts
        """
        alerts = list(self.alert_history)

        # Filter by time
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            alerts = [a for a in alerts if a.timestamp >= cutoff_time]

        # Apply other filters
        if level:
            alerts = [a for a in alerts if a.level == level]
        if alert_type:
            alerts = [a for a in alerts if a.type == alert_type]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        if limit:
            alerts = alerts[:limit]

        return alerts

    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        Get alert statistics

        Returns:
            Dictionary with alert statistics
        """
        # Count alerts by level
        level_counts = {level.value: 0 for level in AlertLevel}
        for alert in self.active_alerts.values():
            level_counts[alert.level.value] += 1

        # Count alerts by type
        type_counts = {alert_type.value: 0 for alert_type in AlertType}
        for alert in self.active_alerts.values():
            type_counts[alert.type.value] += 1

        # Recent alerts (last 24 hours)
        recent_alerts = self.get_alert_history(hours=24)
        recent_level_counts = {level.value: 0 for level in AlertLevel}
        for alert in recent_alerts:
            recent_level_counts[alert.level.value] += 1

        return {
            "active_alerts": len(self.active_alerts),
            "active_by_level": level_counts,
            "active_by_type": type_counts,
            "last_24_hours": {
                "total": len(recent_alerts),
                "by_level": recent_level_counts
            },
            "unacknowledged": len([a for a in self.active_alerts.values() if not a.acknowledged]),
            "critical_count": level_counts[AlertLevel.CRITICAL.value],
            "error_count": level_counts[AlertLevel.ERROR.value]
        }

    def add_threshold(self, threshold: AlertThreshold):
        """Add a new alert threshold"""
        self.thresholds[threshold.name] = threshold
        logger.info(f"Added alert threshold: {threshold.name}")

    def remove_threshold(self, name: str):
        """Remove an alert threshold"""
        if name in self.thresholds:
            del self.thresholds[name]
            logger.info(f"Removed alert threshold: {name}")

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
        logger.info("Added alert handler")

    def export_alerts(
        self,
        file_path: str,
        format: str = "json",
        hours: Optional[int] = None
    ):
        """
        Export alerts to file

        Args:
            file_path: Output file path
            format: Export format ("json", "csv")
            hours: Export alerts from last N hours
        """
        alerts = self.get_alert_history(hours=hours)

        if format == "json":
            data = {
                "exported_at": datetime.now().isoformat(),
                "alerts": [alert.to_dict() for alert in alerts]
            }
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            # Convert to DataFrame and export
            df_data = []
            for alert in alerts:
                df_data.append({
                    "id": alert.id,
                    "level": alert.level.value,
                    "type": alert.type.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "metric_name": alert.metric_name,
                    "metric_value": alert.metric_value,
                    "threshold_value": alert.threshold_value,
                    "asset_id": alert.asset_id,
                    "portfolio_id": alert.portfolio_id,
                    "acknowledged": alert.acknowledged,
                    "resolved": alert.resolved
                })
            df = pd.DataFrame(df_data)
            df.to_csv(file_path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        logger.info(f"Exported {len(alerts)} alerts to {file_path}")