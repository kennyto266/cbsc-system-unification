"""
Alerts and Notification System
"""

from .router import router
from .services.alert_engine import AlertEngine, MetricProvider
from .services.notification_service import (
    NotificationService,
    notification_service,
    EmailNotificationChannel,
    BrowserPushNotificationChannel,
    InAppNotificationChannel,
    SMSNotificationChannel,
    WebhookNotificationChannel
)
from .models.alerts import (
    AlertRule,
    Alert,
    Notification,
    NotificationPreferences,
    AlertType,
    AlertSeverity,
    NotificationType,
    NotificationStatus
)

__all__ = [
    # Router
    "router",

    # Services
    "AlertEngine",
    "MetricProvider",
    "NotificationService",
    "notification_service",
    "EmailNotificationChannel",
    "BrowserPushNotificationChannel",
    "InAppNotificationChannel",
    "SMSNotificationChannel",
    "WebhookNotificationChannel",

    # Models
    "AlertRule",
    "Alert",
    "Notification",
    "NotificationPreferences",
    "AlertType",
    "AlertSeverity",
    "NotificationType",
    "NotificationStatus"
]