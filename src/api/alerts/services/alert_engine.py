"""
Alert rule engine for evaluating conditions and triggering alerts
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import json

from ..models.alerts import (
    AlertRule,
    Alert,
    AlertCondition,
    AlertType,
    AlertSeverity,
    NotificationType,
    AlertRuleDB,
    AlertDB
)

logger = logging.getLogger(__name__)


class MetricProvider:
    """Abstract class for providing metric data"""

    async def get_metric_value(self, strategy_id: str, metric: str, time_window: Optional[int] = None) -> Optional[float]:
        """Get the current value of a metric"""
        raise NotImplementedError


class DefaultMetricProvider(MetricProvider):
    """Default implementation using analytics service"""

    def __init__(self, analytics_service=None):
        self.analytics_service = analytics_service

    async def get_metric_value(self, strategy_id: str, metric: str, time_window: Optional[int] = None) -> Optional[float]:
        """
        Get metric value from analytics service

        Args:
            strategy_id: Strategy identifier
            metric: Metric name
            time_window: Time window in minutes (optional)

        Returns:
            Metric value or None if not available
        """
        # In production, this would call the analytics service
        # For demo, return mock values
        mock_values = {
            "drawdown": -0.05,
            "return": 0.12,
            "volatility": 0.15,
            "sharpe_ratio": 1.2,
            "win_rate": 0.65,
            "max_position_size": 0.25,
            "daily_pnl": 1000,
            "exposure": 0.8
        }

        # Add some randomness
        import random
        base_value = mock_values.get(metric, 0)
        if base_value != 0:
            value = base_value * (1 + random.gauss(0, 0.1))
        else:
            value = random.uniform(-0.1, 0.1)

        return value


class AlertEngine:
    """Main alert rule engine"""

    def __init__(self, metric_provider: Optional[MetricProvider] = None):
        self.metric_provider = metric_provider or DefaultMetricProvider()
        self.cooldown_tracker: Dict[str, datetime] = {}

    async def evaluate_rules(
        self,
        strategy_id: str,
        rules: List[AlertRule],
        force: bool = False
    ) -> List[Alert]:
        """
        Evaluate all rules for a strategy

        Args:
            strategy_id: Strategy identifier
            rules: List of alert rules to evaluate
            force: Force evaluation ignoring cooldowns

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        for rule in rules:
            if not rule.enabled:
                continue

            # Check if strategy_id matches
            if rule.strategy_id and rule.strategy_id != strategy_id:
                continue

            # Check cooldown
            if not force and not self._should_check_rule(rule):
                continue

            # Evaluate conditions
            should_trigger, metadata = await self._evaluate_rule(rule, strategy_id)

            if should_trigger:
                alert = await self._create_alert(rule, strategy_id, metadata)
                triggered_alerts.append(alert)

                # Update cooldown
                self._update_cooldown(rule)

                # Update rule metadata
                rule.last_triggered = datetime.utcnow()
                rule.trigger_count += 1

        return triggered_alerts

    async def _evaluate_rule(self, rule: AlertRule, strategy_id: str) -> tuple[bool, Dict[str, Any]]:
        """
        Evaluate a single alert rule

        Returns:
            Tuple of (should_trigger, metadata)
        """
        if rule.alert_type == AlertType.THRESHOLD:
            return await self._evaluate_threshold_conditions(rule, strategy_id)
        elif rule.alert_type == AlertType.EVENT:
            return await self._evaluate_event_conditions(rule, strategy_id)
        elif rule.alert_type == AlertType.SCHEDULED:
            return await self._evaluate_scheduled_conditions(rule, strategy_id)
        else:
            logger.warning(f"Unsupported alert type: {rule.alert_type}")
            return False, {}

    async def _evaluate_threshold_conditions(
        self,
        rule: AlertRule,
        strategy_id: str
    ) -> tuple[bool, Dict[str, Any]]:
        """Evaluate threshold-based conditions"""
        results = []

        for condition in rule.conditions:
            value = await self.metric_provider.get_metric_value(
                strategy_id=strategy_id,
                metric=condition.metric,
                time_window=condition.time_window
            )

            if value is None:
                logger.warning(f"Could not get value for metric {condition.metric}")
                continue

            # Evaluate condition
            triggered = self._evaluate_condition(value, condition)
            results.append({
                "condition": condition,
                "value": value,
                "triggered": triggered
            })

        # All conditions must be true to trigger alert
        all_triggered = all(r["triggered"] for r in results)

        metadata = {
            "conditions": results,
            "evaluated_at": datetime.utcnow().isoformat()
        }

        return all_triggered, metadata

    async def _evaluate_event_conditions(
        self,
        rule: AlertRule,
        strategy_id: str
    ) -> tuple[bool, Dict[str, Any]]:
        """Evaluate event-based conditions"""
        # For demo purposes, simulate random events
        import random

        # Simulate strategy events
        events = [
            {"type": "strategy_started", "probability": 0.1},
            {"type": "strategy_stopped", "probability": 0.05},
            {"type": "strategy_error", "probability": 0.02},
            {"type": "new_high", "probability": 0.15},
            {"type": "new_low", "probability": 0.1}
        ]

        for event in events:
            if random.random() < event["probability"]:
                return True, {
                    "event": event["type"],
                    "strategy_id": strategy_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

        return False, {}

    async def _evaluate_scheduled_conditions(
        self,
        rule: AlertRule,
        strategy_id: str
    ) -> tuple[bool, Dict[str, Any]]:
        """Evaluate scheduled conditions"""
        if not rule.schedule_cron:
            return False, {}

        # For demo purposes, check if it's time to run
        from croniter import croniter

        cron = croniter(rule.schedule_cron, datetime.utcnow())
        next_run = cron.get_next(datetime)

        # If next run is within the next minute, trigger
        if (next_run - datetime.utcnow()).total_seconds() < 60:
            return True, {
                "scheduled_run": True,
                "next_run": next_run.isoformat()
            }

        return False, {}

    def _evaluate_condition(self, value: float, condition: AlertCondition) -> bool:
        """Evaluate a single condition"""
        threshold = condition.threshold

        if condition.operator == "gt":
            return value > threshold
        elif condition.operator == "gte":
            return value >= threshold
        elif condition.operator == "lt":
            return value < threshold
        elif condition.operator == "lte":
            return value <= threshold
        elif condition.operator == "eq":
            return abs(value - threshold) < 0.0001
        elif condition.operator == "ne":
            return abs(value - threshold) >= 0.0001
        else:
            logger.warning(f"Unknown operator: {condition.operator}")
            return False

    def _should_check_rule(self, rule: AlertRule) -> bool:
        """Check if rule should be evaluated based on cooldown"""
        if rule.cooldown_minutes <= 0:
            return True

        rule_key = f"{rule.id}"
        last_check = self.cooldown_tracker.get(rule_key)

        if not last_check:
            return True

        time_since_last = datetime.utcnow() - last_check
        return time_since_last.total_seconds() > rule.cooldown_minutes * 60

    def _update_cooldown(self, rule: AlertRule):
        """Update cooldown tracker for a rule"""
        rule_key = f"{rule.id}"
        self.cooldown_tracker[rule_key] = datetime.utcnow()

    async def _create_alert(
        self,
        rule: AlertRule,
        strategy_id: str,
        metadata: Dict[str, Any]
    ) -> Alert:
        """Create an alert instance"""
        title = f"[{rule.severity.upper()}] {rule.name}"

        # Format message based on conditions
        if rule.alert_type == AlertType.THRESHOLD and "conditions" in metadata:
            condition_text = self._format_condition_message(metadata["conditions"])
            message = f"Strategy {strategy_id} triggered alert: {condition_text}"
        else:
            message = f"Alert triggered for strategy {strategy_id}: {rule.description or rule.name}"

        alert = Alert(
            rule_id=rule.id,
            rule_name=rule.name,
            user_id=rule.user_id,
            strategy_id=strategy_id,
            severity=rule.severity,
            title=title,
            message=message,
            metadata=metadata
        )

        return alert

    def _format_condition_message(self, condition_results: List[Dict]) -> str:
        """Format condition results into readable message"""
        messages = []

        for result in condition_results:
            condition = result["condition"]
            value = result["value"]

            # Format value based on metric type
            if condition.metric in ["return", "drawdown"]:
                formatted_value = f"{value:.2%}"
            elif condition.metric in ["volatility", "win_rate"]:
                formatted_value = f"{value:.1%}"
            else:
                formatted_value = f"{value:.2f}"

            messages.append(
                f"{condition.metric} is {formatted_value} (threshold: {condition.operator} {condition.threshold})"
            )

        return "; ".join(messages)

    async def get_active_rules(
        self,
        user_id: Optional[int] = None,
        strategy_id: Optional[str] = None
    ) -> List[AlertRule]:
        """
        Get active alert rules

        Args:
            user_id: Optional user filter
            strategy_id: Optional strategy filter

        Returns:
            List of active rules
        """
        # In production, this would query the database
        # For demo, return sample rules
        sample_rules = [
            AlertRule(
                user_id=user_id or 1,
                strategy_id=strategy_id,
                name="High Drawdown Alert",
                description="Alert when strategy drawdown exceeds threshold",
                alert_type=AlertType.THRESHOLD,
                conditions=[
                    AlertCondition(
                        metric="drawdown",
                        operator="lt",
                        threshold=-0.1
                    )
                ],
                severity=AlertSeverity.HIGH,
                notification_channels=[NotificationType.EMAIL, NotificationType.BROWSER_PUSH]
            ),
            AlertRule(
                user_id=user_id or 1,
                strategy_id=strategy_id,
                name="Daily Performance Summary",
                description="Send daily performance summary",
                alert_type=AlertType.SCHEDULED,
                conditions=[],
                severity=AlertSeverity.LOW,
                notification_channels=[NotificationType.EMAIL],
                schedule_cron="0 17 * * *"  # 5 PM daily
            )
        ]

        return sample_rules


# Helper functions for integration with database
async def save_alert(alert: Alert, db_session):
    """Save alert to database"""
    alert_db = AlertDB(
        id=alert.id,
        rule_id=alert.rule_id,
        user_id=alert.user_id,
        strategy_id=alert.strategy_id,
        severity=alert.severity,
        title=alert.title,
        message=alert.message,
        metadata=alert.metadata,
        acknowledged=alert.acknowledged,
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by=alert.acknowledged_by,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at
    )

    db_session.add(alert_db)
    await db_session.commit()

    return alert_db


async def update_rule_last_triggered(rule_id: str, db_session):
    """Update rule's last triggered timestamp"""
    # In production, update the rule in database
    pass