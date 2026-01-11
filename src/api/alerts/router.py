"""
Alert and notification API router
"""
from datetime import datetime, time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from .models.alerts import (
    AlertRule,
    Alert,
    Notification,
    AlertType,
    AlertSeverity,
    NotificationType,
    NotificationStatus,
    NotificationPreferences
)
from .services.alert_engine import AlertEngine, save_alert
from .services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts", "notifications"])

# Initialize services
alert_engine = AlertEngine()

# Mock database
db_alert_rules = {}
db_alerts = {}
db_notifications = {}
db_preferences = {}


# Dependency for user authentication
async def get_current_user_id():
    """Get current authenticated user ID"""
    # In production, validate JWT token
    return 1  # Demo user ID


@router.post("/rules", response_model=AlertRule)
async def create_alert_rule(
    rule: AlertRule,
    user_id: int = Depends(get_current_user_id)
):
    """Create a new alert rule"""
    try:
        rule.user_id = user_id
        rule.id = rule.id or datetime.utcnow().timestamp()

        # Store in database
        db_alert_rules[str(rule.id)] = rule

        logger.info(f"Created alert rule {rule.id} for user {user_id}")
        return rule

    except Exception as e:
        logger.error(f"Failed to create alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules", response_model=List[AlertRule])
async def get_alert_rules(
    user_id: int = Depends(get_current_user_id),
    strategy_id: Optional[str] = Query(None),
    enabled_only: bool = Query(True)
):
    """Get alert rules for user"""
    try:
        rules = []

        for rule in db_alert_rules.values():
            if rule.user_id != user_id:
                continue

            if strategy_id and rule.strategy_id != strategy_id:
                continue

            if enabled_only and not rule.enabled:
                continue

            rules.append(rule)

        return rules

    except Exception as e:
        logger.error(f"Failed to get alert rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}", response_model=AlertRule)
async def update_alert_rule(
    rule_id: str,
    rule_update: AlertRule,
    user_id: int = Depends(get_current_user_id)
):
    """Update an alert rule"""
    try:
        if rule_id not in db_alert_rules:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        rule = db_alert_rules[rule_id]

        if rule.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        # Update fields
        rule.name = rule_update.name
        rule.description = rule_update.description
        rule.conditions = rule_update.conditions
        rule.severity = rule_update.severity
        rule.enabled = rule_update.enabled
        rule.notification_channels = rule_update.notification_channels
        rule.updated_at = datetime.utcnow()

        logger.info(f"Updated alert rule {rule_id}")
        return rule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """Delete an alert rule"""
    try:
        if rule_id not in db_alert_rules:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        rule = db_alert_rules[rule_id]

        if rule.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        del db_alert_rules[rule_id]

        logger.info(f"Deleted alert rule {rule_id}")
        return {"message": "Alert rule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    user_id: int = Depends(get_current_user_id),
    strategy_id: Optional[str] = Query(None),
    acknowledged: Optional[bool] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0)
):
    """Get alerts for user"""
    try:
        alerts = []

        # Filter alerts
        for alert in db_alerts.values():
            if alert.user_id != user_id:
                continue

            if strategy_id and alert.strategy_id != strategy_id:
                continue

            if acknowledged is not None and alert.acknowledged != acknowledged:
                continue

            if severity and alert.severity != severity:
                continue

            alerts.append(alert)

        # Sort by created_at descending
        alerts.sort(key=lambda x: x.created_at, reverse=True)

        # Pagination
        total = len(alerts)
        alerts = alerts[offset:offset + limit]

        return alerts

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """Acknowledge an alert"""
    try:
        if alert_id not in db_alerts:
            raise HTTPException(status_code=404, detail="Alert not found")

        alert = db_alerts[alert_id]

        if alert.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        alert.acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = user_id

        logger.info(f"Acknowledged alert {alert_id}")
        return {"message": "Alert acknowledged successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", response_model=List[Notification])
async def get_notifications(
    user_id: int = Depends(get_current_user_id),
    type: Optional[NotificationType] = Query(None),
    status: Optional[NotificationStatus] = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0)
):
    """Get notifications for user"""
    try:
        notifications = []

        # Get in-app notifications
        in_app_channel = notification_service.channels.get(NotificationType.IN_APP)
        if in_app_channel:
            in_app_notifs = in_app_channel.get_user_notifications(user_id, unread_only)

            for notif in in_app_notifs:
                if type and notif.get('type') != type.value:
                    continue

                notification = Notification(
                    alert_id=notif.get('alert_id', ''),
                    user_id=user_id,
                    type=NotificationType.IN_APP,
                    title=notif['title'],
                    content=notif['content'],
                    recipient=str(user_id),
                    status=NotificationStatus.SENT,
                    metadata={'read': notif['read']},
                    created_at=datetime.fromisoformat(notif['timestamp'])
                )
                notifications.append(notification)

        # Get other notifications from database
        for notif in db_notifications.values():
            if notif.user_id != user_id:
                continue

            if type and notif.type != type:
                continue

            if status and notif.status != status:
                continue

            notifications.append(notif)

        # Sort by created_at descending
        notifications.sort(key=lambda x: x.created_at, reverse=True)

        # Pagination
        total = len(notifications)
        notifications = notifications[offset:offset + limit]

        return notifications

    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: int = Depends(get_current_user_id)
):
    """Mark notification as read"""
    try:
        # Mark in-app notification as read
        in_app_channel = notification_service.channels.get(NotificationType.IN_APP)
        if in_app_channel:
            in_app_channel.mark_as_read(user_id, notification_id)

        # Update other notifications in database
        if notification_id in db_notifications:
            notif = db_notifications[notification_id]

            if notif.user_id != user_id:
                raise HTTPException(status_code=403, detail="Not authorized")

            notif.metadata['read'] = True

        logger.info(f"Marked notification {notification_id} as read")
        return {"message": "Notification marked as read"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    user_id: int = Depends(get_current_user_id)
):
    """Mark all notifications as read"""
    try:
        # Mark in-app notifications as read
        in_app_channel = notification_service.channels.get(NotificationType.IN_APP)
        if in_app_channel:
            in_app_channel.mark_all_as_read(user_id)

        # Update other notifications in database
        for notif in db_notifications.values():
            if notif.user_id == user_id:
                notif.metadata['read'] = True

        logger.info(f"Marked all notifications as read for user {user_id}")
        return {"message": "All notifications marked as read"}

    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    user_id: int = Depends(get_current_user_id)
):
    """Get notification preferences for user"""
    try:
        if user_id not in db_preferences:
            # Create default preferences
            preferences = NotificationPreferences(user_id=user_id)
            db_preferences[user_id] = preferences

        return db_preferences[user_id]

    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    user_id: int = Depends(get_current_user_id)
):
    """Update notification preferences for user"""
    try:
        preferences.user_id = user_id
        db_preferences[user_id] = preferences

        logger.info(f"Updated notification preferences for user {user_id}")
        return preferences

    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def test_notification(
    channel: NotificationType,
    title: str,
    message: str,
    user_id: int = Depends(get_current_user_id)
):
    """Send a test notification"""
    try:
        # Get preferences
        preferences = db_preferences.get(user_id, NotificationPreferences(user_id=user_id))

        # Create test alert
        test_alert = Alert(
            rule_id="test",
            rule_name="Test Alert",
            user_id=user_id,
            title=title,
            content=message,
            severity=AlertSeverity.LOW,
            metadata={'test': True}
        )

        # Send notification
        notifications = await notification_service.send_notifications(
            alert=test_alert,
            preferences=preferences,
            channels=[channel]
        )

        if notifications:
            return {
                "message": "Test notification sent",
                "notification_id": str(notifications[0].id),
                "status": notifications[0].status.value
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send test notification")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-rules")
async def trigger_rule_evaluation(
    strategy_id: Optional[str] = None,
    user_id: int = Depends(get_current_user_id),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Manually trigger rule evaluation for testing"""
    try:
        # Get user's rules
        rules = [r for r in db_alert_rules.values() if r.user_id == user_id and r.enabled]

        # Evaluate rules
        triggered_alerts = await alert_engine.evaluate_rules(strategy_id or "test", rules, force=True)

        # Save alerts and send notifications
        for alert in triggered_alerts:
            # Save to database
            db_alerts[str(alert.id)] = alert

            # Get preferences and send notifications
            preferences = db_preferences.get(user_id, NotificationPreferences(user_id=user_id))

            background_tasks.add_task(
                send_alert_notifications,
                alert,
                preferences
            )

        return {
            "message": f"Rule evaluation completed. Triggered {len(triggered_alerts)} alerts.",
            "alerts": [
                {
                    "id": str(alert.id),
                    "title": alert.title,
                    "severity": alert.severity.value,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in triggered_alerts
            ]
        }

    except Exception as e:
        logger.error(f"Failed to trigger rule evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def send_alert_notifications(alert: Alert, preferences: NotificationPreferences):
    """Background task to send notifications for an alert"""
    try:
        notifications = await notification_service.send_notifications(
            alert=alert,
            preferences=preferences,
            channels=alert.metadata.get('notification_channels', preferences.channels.keys())
        )

        # Save notifications to database
        for notif in notifications:
            db_notifications[str(notif.id)] = notif

        logger.info(f"Sent {len(notifications)} notifications for alert {alert.id}")

    except Exception as e:
        logger.error(f"Failed to send notifications for alert {alert.id}: {e}")


# Initialize with sample data
def init_sample_data():
    """Initialize with sample data for testing"""
    global db_alert_rules, db_preferences

    # Sample alert rules
    sample_rules = [
        AlertRule(
            user_id=1,
            strategy_id="test_strategy",
            name="High Drawdown Alert",
            description="Alert when drawdown exceeds 10%",
            alert_type=AlertType.THRESHOLD,
            conditions=[{
                "metric": "drawdown",
                "operator": "lt",
                "threshold": -0.1,
                "time_window": 60
            }],
            severity=AlertSeverity.HIGH,
            notification_channels=[NotificationType.EMAIL, NotificationType.BROWSER_PUSH]
        ),
        AlertRule(
            user_id=1,
            strategy_id="test_strategy",
            name="Daily Performance Report",
            description="Send daily performance summary",
            alert_type=AlertType.SCHEDULED,
            conditions=[],
            severity=AlertSeverity.LOW,
            notification_channels=[NotificationType.EMAIL],
            schedule_cron="0 17 * * *"
        )
    ]

    for rule in sample_rules:
        rule.id = str(hash(rule.name + str(rule.user_id)))
        db_alert_rules[rule.id] = rule

    # Sample preferences
    db_preferences[1] = NotificationPreferences(
        user_id=1,
        channels={
            NotificationType.EMAIL: True,
            NotificationType.BROWSER_PUSH: True,
            NotificationType.IN_APP: True,
            NotificationType.SMS: False,
            NotificationType.WEBHOOK: False
        },
        quiet_hours_enabled=True,
        quiet_hours_start=time(22, 0),
        quiet_hours_end=time(8, 0)
    )


# Initialize sample data on module import
init_sample_data()