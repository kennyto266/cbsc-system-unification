"""
Enhanced Alert System
Advanced multi-level alert system with intelligent processing and escalation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque, defaultdict
import numpy as np
from uuid import uuid4

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertCategory(str, Enum):
    """Alert categories"""
    MARKET_RISK = "market_risk"
    CREDIT_RISK = "credit_risk"
    OPERATIONAL_RISK = "operational_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    CONCENTRATION_RISK = "concentration_risk"
    MODEL_RISK = "model_risk"
    COUNTERPARTY_RISK = "counterparty_risk"
    REGULATORY_RISK = "regulatory_risk"
    SYSTEM_RISK = "system_risk"


class AlertStatus(str, Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ESCALATED = "escalated"


class AlertAction(str, Enum):
    """Alert action types"""
    NOTIFY = "notify"
    STOP_TRADING = "stop_trading"
    REDUCE_POSITIONS = "reduce_positions"
    INCREASE_MARGIN = "increase_margin"
    MANUAL_REVIEW = "manual_review"
    EXECUTE_HEDGE = "execute_hedge"


@dataclass
class AlertCondition:
    """Alert condition definition"""
    name: str
    metric: str
    operator: str  # gt, lt, gte, lte, eq, ne
    threshold: float
    duration: int = 0  # Seconds condition must persist
    severity: AlertSeverity = AlertSeverity.WARNING
    category: AlertCategory = AlertCategory.MARKET_RISK
    cooldown: int = 300  # Seconds between repeated alerts
    enabled: bool = True
    tags: List[str] = None
    actions: List[AlertAction] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.actions is None:
            self.actions = [AlertAction.NOTIFY]


@dataclass
class Alert:
    """Alert instance"""
    id: str
    condition: AlertCondition
    instance_id: str
    user_id: str
    current_value: float
    threshold_value: float
    deviation: float
    timestamp: datetime
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    message: str = ""
    context: Dict[str, Any] = None
    escalation_level: int = 0

    def __post_init__(self):
        if self.context is None:
            self.context = {}


class AlertPattern:
    """Pattern matching for complex alert conditions"""

    def __init__(self):
        self.patterns = []

    def add_pattern(
        self,
        name: str,
        conditions: List[Dict],
        time_window: int = 300,
        min_occurrences: int = 1
    ):
        """Add a pattern to match"""
        self.patterns.append({
            "name": name,
            "conditions": conditions,
            "time_window": time_window,
            "min_occurrences": min_occurrences
        })

    def check_patterns(
        self,
        alerts_history: deque,
        max_history: int = 1000
    ) -> List[Dict]:
        """Check if any patterns are matched"""
        matched_patterns = []

        for pattern in self.patterns:
            # Get recent alerts within time window
            cutoff_time = datetime.utcnow() - timedelta(seconds=pattern["time_window"])
            recent_alerts = [
                alert for alert in alerts_history
                if alert["timestamp"] > cutoff_time
            ]

            # Count matching conditions
            condition_matches = 0
            for condition in pattern["conditions"]:
                for alert in recent_alerts:
                    if self._matches_condition(alert, condition):
                        condition_matches += 1
                        break

            # Check if pattern is matched
            if condition_matches >= pattern["min_occurrences"]:
                matched_patterns.append({
                    "pattern_name": pattern["name"],
                    "matches": condition_matches,
                    "time_window": pattern["time_window"],
                    "alerts": recent_alerts[-10:]  # Last 10 matching alerts
                })

        return matched_patterns

    def _matches_condition(self, alert: Dict, condition: Dict) -> bool:
        """Check if alert matches condition"""
        # Check severity
        if "severity" in condition and alert["severity"] != condition["severity"]:
            return False

        # Check category
        if "category" in condition and alert["category"] != condition["category"]:
            return False

        # Check tags
        if "tags" in condition:
            alert_tags = set(alert.get("tags", []))
            condition_tags = set(condition["tags"])
            if not condition_tags.issubset(alert_tags):
                return False

        # Check message content
        if "message_contains" in condition:
            if condition["message_contains"].lower() not in alert["message"].lower():
                return False

        return True


class AlertEscalation:
    """Alert escalation manager"""

    def __init__(self):
        self.escalation_rules = {}
        self.escalation_history = defaultdict(list)

    def add_escalation_rule(
        self,
        condition_name: str,
        levels: List[Dict]
    ):
        """Add escalation rule for a condition"""
        self.escalation_rules[condition_name] = levels

    def check_escalation(
        self,
        alert: Alert,
        unresolved_count: int = 0
    ) -> Optional[Dict]:
        """Check if alert should be escalated"""
        condition_name = alert.condition.name

        if condition_name not in self.escalation_rules:
            return None

        # Get escalation levels for this condition
        levels = self.escalation_rules[condition_name]

        # Find appropriate escalation level
        for i, level in enumerate(levels):
            # Check time-based escalation
            if "time_threshold" in level:
                time_since = datetime.utcnow() - alert.timestamp
                if time_since.total_seconds() > level["time_threshold"]:
                    return {
                        "level": i + 1,
                        "severity": level.get("severity", AlertSeverity.ERROR),
                        "actions": level.get("actions", []),
                        "notify": level.get("notify", []),
                        "reason": f"Alert unresolved for {time_since}"
                    }

            # Check count-based escalation
            if "count_threshold" in level:
                if unresolved_count >= level["count_threshold"]:
                    return {
                        "level": i + 1,
                        "severity": level.get("severity", AlertSeverity.ERROR),
                        "actions": level.get("actions", []),
                        "notify": level.get("notify", []),
                        "reason": f"Multiple occurrences: {unresolved_count}"
                    }

        return None

    def execute_escalation(
        self,
        alert: Alert,
        escalation: Dict,
        notification_handlers: Dict[str, Callable]
    ):
        """Execute escalation actions"""
        # Update alert
        alert.escalation_level = escalation["level"]
        alert.severity = escalation["severity"]

        # Log escalation
        escalation_record = {
            "alert_id": alert.id,
            "escalation_level": escalation["level"],
            "timestamp": datetime.utcnow(),
            "reason": escalation["reason"]
        }
        self.escalation_history[alert.condition.name].append(escalation_record)

        # Execute actions
        for action in escalation["actions"]:
            if action == AlertAction.NOTIFY:
                # Notify specified channels
                for channel in escalation.get("notify", []):
                    if channel in notification_handlers:
                        asyncio.create_task(
                            notification_handlers[channel](alert, escalation)
                        )

            elif action == AlertAction.STOP_TRADING:
                # Execute stop trading logic
                logger.critical(f"EXECUTING STOP TRADING for alert {alert.id}")

            elif action == AlertAction.MANUAL_REVIEW:
                # Create manual review task
                logger.warning(f"CREATING MANUAL REVIEW for alert {alert.id}")

        logger.info(
            f"Escalated alert {alert.id} to level {escalation['level']}: "
            f"{escalation['reason']}"
        )


class EnhancedAlertSystem:
    """Enhanced alert system with advanced features"""

    def __init__(self, max_history: int = 10000):
        """Initialize enhanced alert system"""
        self.conditions: Dict[str, AlertCondition] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=max_history)
        self.suppressed_alerts: Set[str] = set()

        # Alert tracking
        self.alert_counts: Dict[str, int] = defaultdict(int)
        self.last_alert_times: Dict[str, datetime] = {}

        # Pattern matching
        self.pattern_matcher = AlertPattern()

        # Escalation
        self.escalation_manager = AlertEscalation()

        # Notification handlers
        self.notification_handlers: Dict[str, Callable] = {}

        # Statistics
        self.stats = {
            "total_alerts": 0,
            "alerts_by_severity": defaultdict(int),
            "alerts_by_category": defaultdict(int),
            "alerts_by_condition": defaultdict(int),
            "average_resolution_time": 0
        }

        # Initialize default escalation rules
        self._initialize_escalation_rules()

    def _initialize_escalation_rules(self):
        """Initialize default escalation rules"""
        # VaR breach escalation
        self.escalation_manager.add_escalation_rule(
            "var_breach",
            [
                {
                    "time_threshold": 300,  # 5 minutes
                    "severity": AlertSeverity.ERROR,
                    "notify": ["email", "slack"],
                    "actions": [AlertAction.NOTIFY]
                },
                {
                    "time_threshold": 900,  # 15 minutes
                    "severity": AlertSeverity.CRITICAL,
                    "notify": ["email", "slack", "sms"],
                    "actions": [AlertAction.REDUCE_POSITIONS, AlertAction.NOTIFY]
                },
                {
                    "time_threshold": 1800,  # 30 minutes
                    "severity": AlertSeverity.EMERGENCY,
                    "notify": ["email", "slack", "sms", "phone"],
                    "actions": [AlertAction.STOP_TRADING, AlertAction.NOTIFY]
                }
            ]
        )

        # Drawdown escalation
        self.escalation_manager.add_escalation_rule(
            "drawdown_breach",
            [
                {
                    "count_threshold": 3,
                    "severity": AlertSeverity.ERROR,
                    "notify": ["email"],
                    "actions": [AlertAction.MANUAL_REVIEW, AlertAction.NOTIFY]
                }
            ]
        )

    def add_condition(self, condition: AlertCondition) -> str:
        """Add an alert condition"""
        condition_id = str(uuid4())
        self.conditions[condition_id] = condition
        return condition_id

    def remove_condition(self, condition_id: str) -> bool:
        """Remove an alert condition"""
        if condition_id in self.conditions:
            del self.conditions[condition_id]
            return True
        return False

    def check_metrics(
        self,
        metrics: Dict[str, float],
        instance_id: str,
        user_id: str,
        context: Optional[Dict] = None
    ) -> List[Alert]:
        """Check metrics against all conditions and generate alerts"""
        alerts = []
        current_time = datetime.utcnow()

        for condition_id, condition in self.conditions.items():
            if not condition.enabled:
                continue

            # Check if metric exists
            if condition.metric not in metrics:
                continue

            # Check if condition is met
            if self._evaluate_condition(
                metrics[condition.metric],
                condition.operator,
                condition.threshold
            ):
                # Check cooldown
                last_time = self.last_alert_times.get(condition_id)
                if last_time and (current_time - last_time).total_seconds() < condition.cooldown:
                    continue

                # Check if already suppressed
                if condition_id in self.suppressed_alerts:
                    continue

                # Create alert
                alert = Alert(
                    id=str(uuid4()),
                    condition=condition,
                    instance_id=instance_id,
                    user_id=user_id,
                    current_value=metrics[condition.metric],
                    threshold_value=condition.threshold,
                    deviation=self._calculate_deviation(
                        metrics[condition.metric],
                        condition.threshold,
                        condition.operator
                    ),
                    timestamp=current_time,
                    message=self._generate_alert_message(condition, metrics[condition.metric]),
                    context=context or {}
                )

                alerts.append(alert)

                # Update tracking
                self.active_alerts[alert.id] = alert
                self.alert_history.append(asdict(alert))
                self.alert_counts[condition_id] += 1
                self.last_alert_times[condition_id] = current_time

                # Update statistics
                self.stats["total_alerts"] += 1
                self.stats["alerts_by_severity"][condition.severity.value] += 1
                self.stats["alerts_by_category"][condition.category.value] += 1
                self.stats["alerts_by_condition"][condition.name] += 1

                # Check for escalation
                unresolved_count = self.alert_counts[condition_id]
                escalation = self.escalation_manager.check_escalation(
                    alert, unresolved_count
                )

                if escalation:
                    self.escalation_manager.execute_escalation(
                        alert, escalation, self.notification_handlers
                    )

                # Send notifications
                asyncio.create_task(self._send_notifications(alert))

        # Check patterns
        await self._check_alert_patterns()

        return alerts

    def _evaluate_condition(
        self,
        value: float,
        operator: str,
        threshold: float
    ) -> bool:
        """Evaluate if condition is met"""
        if operator == "gt":
            return value > threshold
        elif operator == "gte":
            return value >= threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "eq":
            return abs(value - threshold) < 1e-9
        elif operator == "ne":
            return abs(value - threshold) >= 1e-9
        else:
            raise ValueError(f"Unknown operator: {operator}")

    def _calculate_deviation(
        self,
        value: float,
        threshold: float,
        operator: str
    ) -> float:
        """Calculate deviation from threshold"""
        if operator in ["gt", "gte"]:
            return (value - threshold) / threshold if threshold != 0 else 0
        elif operator in ["lt", "lte"]:
            return (threshold - value) / threshold if threshold != 0 else 0
        else:
            return 0

    def _generate_alert_message(self, condition: AlertCondition, value: float) -> str:
        """Generate alert message"""
        operator_text = {
            "gt": "exceeds",
            "gte": "exceeds or equals",
            "lt": "below",
            "lte": "below or equals",
            "eq": "equals",
            "ne": "not equal to"
        }.get(condition.operator, "compared to")

        return (
            f"Alert: {condition.name} - {condition.metric} {operator_text} "
            f"threshold. Current: {value:.4f}, Threshold: {condition.threshold:.4f}"
        )

    async def _send_notifications(self, alert: Alert):
        """Send notifications for alert"""
        for action in alert.condition.actions:
            if action == AlertAction.NOTIFY:
                # Send to all default channels
                for channel in ["email", "slack"]:
                    if channel in self.notification_handlers:
                        try:
                            await self.notification_handlers[channel](alert)
                        except Exception as e:
                            logger.error(f"Failed to send {channel} notification: {e}")

    async def _check_alert_patterns(self):
        """Check for alert patterns"""
        matched_patterns = self.pattern_matcher.check_patterns(self.alert_history)

        for pattern in matched_patterns:
            # Create pattern alert
            pattern_alert = Alert(
                id=str(uuid4()),
                condition=AlertCondition(
                    name=f"Pattern: {pattern['pattern_name']}",
                    metric="pattern_match",
                    operator="eq",
                    threshold=1,
                    severity=AlertSeverity.WARNING,
                    category=AlertCategory.SYSTEM_RISK
                ),
                instance_id="system",
                user_id="system",
                current_value=pattern["matches"],
                threshold_value=1,
                deviation=pattern["matches"] - 1,
                timestamp=datetime.utcnow(),
                message=f"Pattern detected: {pattern['pattern_name']} ({pattern['matches']} matches)",
                context={"pattern": pattern}
            )

            self.alert_history.append(asdict(pattern_alert))

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            return True
        return False

    def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            if resolution_notes:
                alert.context["resolution_notes"] = resolution_notes

            # Update resolution time statistics
            resolution_time = alert.resolved_at - alert.timestamp
            self._update_resolution_time_stats(resolution_time)

            # Remove from active alerts
            del self.active_alerts[alert_id]
            return True
        return False

    def suppress_alert(
        self,
        condition_id: str,
        duration: int = 3600
    ) -> bool:
        """Suppress alerts for a condition"""
        if condition_id in self.conditions:
            self.suppressed_alerts.add(condition_id)

            # Auto-unsuppress after duration
            asyncio.create_task(self._unsuppress_after(condition_id, duration))
            return True
        return False

    async def _unsuppress_after(self, condition_id: str, duration: int):
        """Unsuppress condition after duration"""
        await asyncio.sleep(duration)
        self.suppressed_alerts.discard(condition_id)
        logger.info(f"Unsuppressed alerts for condition {condition_id}")

    def _update_resolution_time_stats(self, resolution_time: timedelta):
        """Update resolution time statistics"""
        current_avg = self.stats["average_resolution_time"]
        current_count = self.stats["total_resolved"] if "total_resolved" in self.stats else 0

        if current_count == 0:
            self.stats["average_resolution_time"] = resolution_time.total_seconds()
        else:
            # Running average
            self.stats["average_resolution_time"] = (
                (current_avg * current_count + resolution_time.total_seconds()) /
                (current_count + 1)
            )

        self.stats["total_resolved"] = current_count + 1

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert system summary"""
        return {
            "total_conditions": len(self.conditions),
            "active_alerts": len(self.active_alerts),
            "suppressed_conditions": len(self.suppressed_alerts),
            "statistics": dict(self.stats),
            "recent_alerts": [
                {
                    "id": alert["id"],
                    "condition": alert["condition"]["name"],
                    "severity": alert["severity"],
                    "timestamp": alert["timestamp"]
                }
                for alert in list(self.alert_history)[-10:]
            ]
        }

    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        category: Optional[AlertCategory] = None
    ) -> List[Dict]:
        """Get active alerts with optional filters"""
        alerts = []

        for alert in self.active_alerts.values():
            if severity and alert.condition.severity != severity:
                continue
            if category and alert.condition.category != category:
                continue

            alerts.append({
                "id": alert.id,
                "condition": alert.condition.name,
                "severity": alert.condition.severity.value,
                "category": alert.condition.category.value,
                "message": alert.message,
                "current_value": alert.current_value,
                "threshold": alert.threshold_value,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status.value,
                "escalation_level": alert.escalation_level
            })

        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)