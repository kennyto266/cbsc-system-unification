"""Alert management system for real - time monitoring.

This module provides comprehensive alert management capabilities including
alert rules, notification channels, and automated alert processing.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from ..telegram.integration_manager import IntegrationManager


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts."""

    SYSTEM_PERFORMANCE = "system_performance"
    SYSTEM_HEALTH = "system_health"
    NETWORK_ISSUE = "network_issue"
    ANOMALY_DETECTED = "anomaly_detected"
    TRADING_RISK = "trading_risk"
    AGENT_FAILURE = "agent_failure"
    DATA_ISSUE = "data_issue"
    SECURITY_ISSUE = "security_issue"


class AlertStatus(str, Enum):
    """Alert status."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(str, Enum):
    """Notification channels."""

    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    LOG = "log"


class AlertRule(BaseModel):
    """Alert rule configuration."""

    rule_id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description")

    # Rule conditions
    alert_type: AlertType = Field(..., description="Alert type")
    level: AlertLevel = Field(..., description="Alert level")
    conditions: Dict[str, Any] = Field(..., description="Rule conditions")

    # Notification settings
    channels: List[NotificationChannel] = Field(
        default_factory=list, description="Notification channels"
    )
    recipients: List[str] = Field(default_factory=list, description="Alert recipients")

    # Rule settings
    enabled: bool = Field(True, description="Rule enabled status")
    cooldown: float = Field(300.0, description="Cooldown period (seconds)")
    max_frequency: int = Field(10, description="Maximum alerts per hour")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update time"
    )

    class Config:
        use_enum_values = True


class AlertAction(BaseModel):
    """Alert action configuration."""

    action_id: str = Field(..., description="Action identifier")
    name: str = Field(..., description="Action name")
    action_type: str = Field(..., description="Action type")

    # Action parameters
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )

    # Execution settings
    enabled: bool = Field(True, description="Action enabled status")
    timeout: float = Field(30.0, description="Action timeout (seconds)")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )

    class Config:
        use_enum_values = True


class Alert(BaseModel):
    """Alert model."""

    alert_id: str = Field(..., description="Alert identifier")
    rule_id: Optional[str] = Field(None, description="Triggering rule ID")

    # Alert details
    alert_type: AlertType = Field(..., description="Alert type")
    level: AlertLevel = Field(..., description="Alert level")
    message: str = Field(..., description="Alert message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Alert details")

    # Status and tracking
    status: AlertStatus = Field(AlertStatus.ACTIVE, description="Alert status")
    acknowledged_by: Optional[str] = Field(None, description="Acknowledged by user")
    resolved_by: Optional[str] = Field(None, description="Resolved by user")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.now, description="Creation time"
    )
    acknowledged_at: Optional[datetime] = Field(None, description="Acknowledgment time")
    resolved_at: Optional[datetime] = Field(None, description="Resolution time")

    # Notification tracking
    notifications_sent: List[Dict[str, Any]] = Field(
        default_factory=list, description="Sent notifications"
    )

    class Config:
        use_enum_values = True


class AlertManager:
    """Alert management system."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Alert storage
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_actions: Dict[str, AlertAction] = {}

        # Notification channels
        self.notification_channels: Dict[NotificationChannel, Any] = {}

        # Alert processing
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None

        # Statistics
        self.stats = {
            "alerts_created": 0,
            "alerts_acknowledged": 0,
            "alerts_resolved": 0,
            "notifications_sent": 0,
            "rules_triggered": 0,
        }

        # Rate limiting
        self.alert_counts: Dict[str, int] = {}
        self.last_alert_time: Dict[str, datetime] = {}

    async def initialize(self) -> bool:
        """Initialize the alert manager."""
        try:
            self.logger.info("Initializing alert manager...")

            # Initialize default rules
            await self._initialize_default_rules()

            # Initialize notification channels
            await self._initialize_notification_channels()

            # Start alert processing
            self.processing_task = asyncio.create_task(self._process_alert_queue())

            self.logger.info("Alert manager initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize alert manager: {e}")
            return False

    async def _initialize_default_rules(self) -> None:
        """Initialize default alert rules."""
        try:
            # System performance rules
            cpu_rule = AlertRule(
                rule_id="high_cpu_usage",
                name="High CPU Usage",
                description="Alert when CPU usage exceeds threshold",
                alert_type=AlertType.SYSTEM_PERFORMANCE,
                level=AlertLevel.WARNING,
                conditions={
                    "metric": "cpu_percent",
                    "threshold": 80.0,
                    "operator": ">",
                },
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.LOG],
                cooldown=300.0,
                max_frequency=5,
            )

            memory_rule = AlertRule(
                rule_id="high_memory_usage",
                name="High Memory Usage",
                description="Alert when memory usage exceeds threshold",
                alert_type=AlertType.SYSTEM_PERFORMANCE,
                level=AlertLevel.WARNING,
                conditions={
                    "metric": "memory_percent",
                    "threshold": 85.0,
                    "operator": ">",
                },
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.LOG],
                cooldown=300.0,
                max_frequency=5,
            )

            disk_rule = AlertRule(
                rule_id="high_disk_usage",
                name="High Disk Usage",
                description="Alert when disk usage exceeds threshold",
                alert_type=AlertType.SYSTEM_PERFORMANCE,
                level=AlertLevel.CRITICAL,
                conditions={
                    "metric": "disk_percent",
                    "threshold": 90.0,
                    "operator": ">",
                },
                channels=[
                    NotificationChannel.TELEGRAM,
                    NotificationChannel.EMAIL,
                    NotificationChannel.LOG,
                ],
                cooldown=600.0,
                max_frequency=3,
            )

            # Network rules
            latency_rule = AlertRule(
                rule_id="high_network_latency",
                name="High Network Latency",
                description="Alert when network latency exceeds threshold",
                alert_type=AlertType.NETWORK_ISSUE,
                level=AlertLevel.WARNING,
                conditions={
                    "metric": "network_latency",
                    "threshold": 100.0,
                    "operator": ">",
                },
                channels=[NotificationChannel.TELEGRAM, NotificationChannel.LOG],
                cooldown=300.0,
                max_frequency=5,
            )

            # Agent failure rules
            agent_rule = AlertRule(
                rule_id="agent_failure",
                name="Agent Failure",
                description="Alert when an agent fails or becomes unresponsive",
                alert_type=AlertType.AGENT_FAILURE,
                level=AlertLevel.CRITICAL,
                conditions={"component": "agent", "status": "failed"},
                channels=[
                    NotificationChannel.TELEGRAM,
                    NotificationChannel.EMAIL,
                    NotificationChannel.LOG,
                ],
                cooldown=60.0,
                max_frequency=10,
            )

            # Add rules
            self.alert_rules[cpu_rule.rule_id] = cpu_rule
            self.alert_rules[memory_rule.rule_id] = memory_rule
            self.alert_rules[disk_rule.rule_id] = disk_rule
            self.alert_rules[latency_rule.rule_id] = latency_rule
            self.alert_rules[agent_rule.rule_id] = agent_rule

            self.logger.info(f"Initialized {len(self.alert_rules)} default alert rules")

        except Exception as e:
            self.logger.error(f"Error initializing default rules: {e}")

    async def _initialize_notification_channels(self) -> None:
        """Initialize notification channels."""
        try:
            # Initialize Telegram channel
            # Note: In real implementation, this would initialize actual Telegram integration
            self.notification_channels[NotificationChannel.TELEGRAM] = {
                "type": "telegram",
                "enabled": True,
                "config": {},
            }

            # Initialize log channel
            self.notification_channels[NotificationChannel.LOG] = {
                "type": "log",
                "enabled": True,
                "config": {},
            }

            # Initialize email channel (placeholder)
            self.notification_channels[NotificationChannel.EMAIL] = {
                "type": "email",
                "enabled": False,
                "config": {},
            }

            self.logger.info(
                f"Initialized {len(self.notification_channels)} notification channels"
            )

        except Exception as e:
            self.logger.error(f"Error initializing notification channels: {e}")

    async def _process_alert_queue(self) -> None:
        """Process alerts from the queue."""
        while True:
            try:
                # Get alert from queue
                alert_data = await self.alert_queue.get()

                # Process alert
                await self._process_alert(alert_data)

                # Mark task as done
                self.alert_queue.task_done()

            except Exception as e:
                self.logger.error(f"Error processing alert: {e}")
                await asyncio.sleep(1)

    async def _process_alert(self, alert_data: Dict[str, Any]) -> None:
        """Process a single alert."""
        try:
            # Create alert object
            alert = Alert(
                alert_id=alert_data["id"],
                rule_id=alert_data.get("rule_id"),
                alert_type=AlertType(alert_data["type"]),
                level=AlertLevel(alert_data["level"]),
                message=alert_data["message"],
                details=alert_data.get("details", {}),
                status=AlertStatus.ACTIVE,
            )

            # Store alert
            self.alerts[alert.alert_id] = alert

            # Check if alert should be sent based on rules
            if await self._should_send_alert(alert):
                # Send notifications
                await self._send_notifications(alert)

                # Update statistics
                self.stats["alerts_created"] += 1
                self.stats["rules_triggered"] += 1

                self.logger.info(f"Alert processed: {alert.alert_id} - {alert.message}")
            else:
                self.logger.debug(
                    f"Alert suppressed: {alert.alert_id} - {alert.message}"
                )

        except Exception as e:
            self.logger.error(f"Error processing alert: {e}")

    async def _should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent based on rules and rate limiting."""
        try:
            # Find matching rules
            matching_rules = []
            for rule in self.alert_rules.values():
                if (
                    rule.enabled
                    and rule.alert_type == alert.alert_type
                    and rule.level == alert.level
                ):
                    matching_rules.append(rule)

            if not matching_rules:
                return False  # No matching rules

            # Check rate limiting for each rule
            for rule in matching_rules:
                rule_key = (
                    f"{rule.rule_id}_{alert.alert_type.value}_{alert.level.value}"
                )
                now = datetime.now()

                # Check cooldown
                if rule_key in self.last_alert_time:
                    time_since_last = (
                        now - self.last_alert_time[rule_key]
                    ).total_seconds()
                    if time_since_last < rule.cooldown:
                        continue  # Skip this rule due to cooldown

                # Check frequency limit
                hour_ago = now - timedelta(hours=1)
                recent_alerts = [
                    a
                    for a in self.alerts.values()
                    if (
                        a.alert_type == alert.alert_type
                        and a.level == alert.level
                        and a.created_at > hour_ago
                    )
                ]

                if len(recent_alerts) >= rule.max_frequency:
                    continue  # Skip this rule due to frequency limit

                # Update tracking
                self.last_alert_time[rule_key] = now
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking alert rules: {e}")
            return False

    async def _send_notifications(self, alert: Alert) -> None:
        """Send notifications for an alert."""
        try:
            # Find matching rules
            matching_rules = [
                rule
                for rule in self.alert_rules.values()
                if (
                    rule.enabled
                    and rule.alert_type == alert.alert_type
                    and rule.level == alert.level
                )
            ]

            if not matching_rules:
                return

            # Get channels from rules
            channels = set()
            for rule in matching_rules:
                channels.update(rule.channels)

            # Send to each channel
            for channel in channels:
                if channel in self.notification_channels:
                    await self._send_to_channel(alert, channel)

        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")

    async def _send_to_channel(
        self, alert: Alert, channel: NotificationChannel
    ) -> None:
        """Send alert to specific notification channel."""
        try:
            channel_config = self.notification_channels.get(channel)
            if not channel_config or not channel_config.get("enabled", False):
                return

            # Format alert message
            message = self._format_alert_message(alert)

            if channel == NotificationChannel.TELEGRAM:
                await self._send_telegram_notification(alert, message)
            elif channel == NotificationChannel.LOG:
                await self._send_log_notification(alert, message)
            elif channel == NotificationChannel.EMAIL:
                await self._send_email_notification(alert, message)
            elif channel == NotificationChannel.WEBHOOK:
                await self._send_webhook_notification(alert, message)

            # Track notification
            alert.notifications_sent.append(
                {
                    "channel": channel.value,
                    "timestamp": datetime.now().isoformat(),
                    "status": "sent",
                }
            )

            self.stats["notifications_sent"] += 1

        except Exception as e:
            self.logger.error(f"Error sending to channel {channel}: {e}")

    def _format_alert_message(self, alert: Alert) -> str:
        """Format alert message for notification."""
        try:
            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨",
            }.get(alert.level, "ℹ️")

            message = (
                f"{level_emoji} {alert.level.value.upper()} Alert\n\n"
                f"Type: {alert.alert_type.value.replace('_', ' ').title()}\n"
                f"Message: {alert.message}\n"
                f"Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Alert ID: {alert.alert_id}\n"
            )

            if alert.details:
                message += "\nDetails:\n"
                for key, value in alert.details.items():
                    message += f"• {key}: {value}\n"

            return message

        except Exception as e:
            self.logger.error(f"Error formatting alert message: {e}")
            return f"Alert: {alert.message}"

    async def _send_telegram_notification(self, alert: Alert, message: str) -> None:
        """Send Telegram notification."""
        try:
            # In real implementation, this would use the Telegram integration
            self.logger.info(f"Telegram notification: {message}")

        except Exception as e:
            self.logger.error(f"Error sending Telegram notification: {e}")

    async def _send_log_notification(self, alert: Alert, message: str) -> None:
        """Send log notification."""
        try:
            if alert.level == AlertLevel.CRITICAL:
                self.logger.critical(f"ALERT: {message}")
            elif alert.level == AlertLevel.ERROR:
                self.logger.error(f"ALERT: {message}")
            elif alert.level == AlertLevel.WARNING:
                self.logger.warning(f"ALERT: {message}")
            else:
                self.logger.info(f"ALERT: {message}")

        except Exception as e:
            self.logger.error(f"Error sending log notification: {e}")

    async def _send_email_notification(self, alert: Alert, message: str) -> None:
        """Send email notification."""
        try:
            # In real implementation, this would send actual email
            self.logger.info(f"Email notification: {message}")

        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")

    async def _send_webhook_notification(self, alert: Alert, message: str) -> None:
        """Send webhook notification."""
        try:
            # In real implementation, this would send HTTP webhook
            self.logger.info(f"Webhook notification: {message}")

        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")

    # Public methods
    async def send_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send alert to the processing queue."""
        try:
            await self.alert_queue.put(alert_data)
        except Exception as e:
            self.logger.error(f"Error queuing alert: {e}")

    async def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert."""
        try:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = user
                alert.acknowledged_at = datetime.now()

                self.stats["alerts_acknowledged"] += 1
                self.logger.info(f"Alert acknowledged: {alert_id} by {user}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {e}")
            return False

    async def resolve_alert(self, alert_id: str, user: str) -> bool:
        """Resolve an alert."""
        try:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_by = user
                alert.resolved_at = datetime.now()

                self.stats["alerts_resolved"] += 1
                self.logger.info(f"Alert resolved: {alert_id} by {user}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error resolving alert: {e}")
            return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return [
            alert
            for alert in self.alerts.values()
            if alert.status == AlertStatus.ACTIVE
        ]

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        alerts = list(self.alerts.values())
        alerts.sort(key=lambda x: x.created_at, reverse=True)
        return alerts[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get alert manager statistics."""
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(self.get_active_alerts()),
            "total_rules": len(self.alert_rules),
            "enabled_rules": len([r for r in self.alert_rules.values() if r.enabled]),
            "stats": self.stats.copy(),
        }

    async def shutdown(self) -> None:
        """Shutdown the alert manager."""
        try:
            self.logger.info("Shutting down alert manager...")

            # Cancel processing task
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Alert manager shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during alert manager shutdown: {e}")
