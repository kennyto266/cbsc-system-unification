"""
Security Audit Logging Service
Comprehensive audit trail for security events and compliance.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

try:
    from models.unified_models import UserActivity
    from config.api_config import settings
except ImportError:
    # Fallback settings
    class settings:
        AUDIT_LOG_RETENTION_DAYS = 90
        AUDIT_LOG_ASYNC = True
        AUDIT_LOG_SENSITIVE_DATA_MASKING = True


class AuditEventType(str, Enum):
    """Audit event types"""
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_PASSWORD_CHANGE = "auth.password.change"
    AUTH_PASSWORD_RESET = "auth.password.reset"
    AUTH_MFA_ENABLED = "auth.mfa.enabled"
    AUTH_MFA_DISABLED = "auth.mfa.disabled"
    AUTH_SESSION_CREATED = "auth.session.created"
    AUTH_SESSION_REVOKED = "auth.session.revoked"

    # Authorization events
    AUTHZ_ROLE_GRANTED = "authz.role.granted"
    AUTHZ_ROLE_REVOKED = "authz.role.revoked"
    AUTHZ_PERMISSION_GRANTED = "authz.permission.granted"
    AUTHZ_PERMISSION_REVOKED = "authz.permission.revoked"

    # User management events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_SUSPENDED = "user.suspended"
    USER_UNSUSPENDED = "user.unsuspended"

    # Data access events
    DATA_ACCESS = "data.access"
    DATA_EXPORT = "data.export"
    DATA_DELETE = "data.delete"
    DATA_MODIFY = "data.modify"

    # API events
    API_KEY_CREATED = "api_key.created"
    API_KEY_DELETED = "api_key.deleted"
    API_KEY_REGENERATED = "api_key.regenerated"

    # Configuration events
    CONFIG_UPDATED = "config.updated"
    CONFIG_ROLLED_BACK = "config.rolled_back"

    # Security events
    SECURITY_ALERT = "security.alert"
    SECURITY_INCIDENT = "security.incident"
    SECURITY_BRUTE_FORCE = "security.brute_force"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"


class EventSeverity(str, Enum):
    """Event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_type: AuditEventType
    user_id: Optional[int]
    username: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: EventSeverity = EventSeverity.INFO
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: bool = True
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to strings
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class AuditLogger:
    """
    Security Audit Logging Service
    Provides comprehensive audit trail for security events.
    """

    def __init__(self):
        self._events: List[AuditEvent] = []
        self._logger = logging.getLogger(__name__)
        self._retention_days = settings.AUDIT_LOG_RETENTION_DAYS

    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in audit logs"""
        if not settings.AUDIT_LOG_SENSITIVE_DATA_MASKING:
            return data

        masked = data.copy()
        sensitive_keys = [
            'password', 'token', 'secret', 'key', 'api_key',
            'access_token', 'refresh_token', 'session_token',
            'credit_card', 'ssn', 'social_security'
        ]

        for key in masked:
            for sensitive in sensitive_keys:
                if sensitive in key.lower():
                    masked[key] = "***MASKED***"
                    break

        return masked

    def _hash_pii(self, value: str) -> str:
        """Hash PII data for privacy"""
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int],
        username: Optional[str],
        ip_address: str,
        user_agent: str,
        severity: EventSeverity = EventSeverity.INFO,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User ID (None for anonymous)
            username: Username (None for anonymous)
            ip_address: Client IP address
            user_agent: User agent string
            severity: Event severity
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            success: Whether operation succeeded
            details: Event details
            metadata: Additional metadata

        Returns:
            Created AuditEvent
        """
        # Mask sensitive data
        safe_details = self._mask_sensitive_data(details or {})
        safe_metadata = self._mask_sensitive_data(metadata or {})

        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            details=safe_details,
            metadata=safe_metadata
        )

        # Store event
        self._events.append(event)

        # Log to standard logger
        log_level = {
            EventSeverity.INFO: logging.INFO,
            EventSeverity.WARNING: logging.WARNING,
            EventSeverity.ERROR: logging.ERROR,
            EventSeverity.CRITICAL: logging.CRITICAL
        }[severity]

        self._logger.log(
            log_level,
            f"Audit: {event_type.value} - user={username or 'N/A'} - ip={ip_address}",
            extra={"audit_event": event.to_dict()}
        )

        # TODO: Persist to database in production
        # await self._persist_to_database(event)

        return event

    async def log_auth_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[int],
        username: Optional[str],
        ip_address: str,
        user_agent: str,
        success: bool = True,
        failure_reason: Optional[str] = None
    ) -> AuditEvent:
        """
        Log authentication event.

        Args:
            event_type: Type of auth event
            user_id: User ID
            username: Username
            ip_address: Client IP
            user_agent: User agent
            success: Whether succeeded
            failure_reason: Reason for failure (if any)

        Returns:
            Created AuditEvent
        """
        severity = EventSeverity.INFO if success else EventSeverity.WARNING

        return await self.log_event(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            success=success,
            details={"failure_reason": failure_reason} if failure_reason else None
        )

    async def log_authorization_event(
        self,
        event_type: AuditEventType,
        admin_user_id: int,
        admin_username: str,
        target_user_id: int,
        target_username: str,
        role: str,
        ip_address: str,
        user_agent: str
    ) -> AuditEvent:
        """
        Log authorization change event.

        Args:
            event_type: Type of authz event
            admin_user_id: Admin making the change
            admin_username: Admin username
            target_user_id: Target user ID
            target_username: Target username
            role: Role being granted/revoked
            ip_address: Client IP
            user_agent: User agent

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type=event_type,
            user_id=admin_user_id,
            username=admin_username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type="user",
            resource_id=str(target_user_id),
            details={
                "target_user_id": target_user_id,
                "target_username": target_username,
                "role": role
            }
        )

    async def log_data_access(
        self,
        user_id: int,
        username: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str,
        user_agent: str
    ) -> AuditEvent:
        """
        Log data access event.

        Args:
            user_id: User ID
            username: Username
            resource_type: Type of resource
            resource_id: Resource ID
            action: Action performed
            ip_address: Client IP
            user_agent: User agent

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details={"action": action}
        )

    async def log_security_event(
        self,
        event_type: AuditEventType,
        severity: EventSeverity,
        description: str,
        ip_address: str,
        user_agent: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Log security event.

        Args:
            event_type: Type of security event
            severity: Event severity
            description: Event description
            ip_address: Client IP
            user_agent: User agent
            user_id: User ID (if applicable)
            username: Username (if applicable)
            details: Additional details

        Returns:
            Created AuditEvent
        """
        return await self.log_event(
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            severity=severity,
            details={"description": description, **(details or {})}
        )

    async def get_user_events(
        self,
        user_id: int,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get audit events for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of events

        Returns:
            List of audit events
        """
        user_events = [
            e for e in self._events
            if e.user_id == user_id
        ]
        return sorted(user_events, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_events_by_type(
        self,
        event_type: AuditEventType,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Get audit events by type.

        Args:
            event_type: Event type to filter
            limit: Maximum number of events

        Returns:
            List of audit events
        """
        filtered = [
            e for e in self._events
            if e.event_type == event_type
        ]
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """
        Get audit events within date range.

        Args:
            start_date: Start of range
            end_date: End of range
            limit: Maximum number of events

        Returns:
            List of audit events
        """
        filtered = [
            e for e in self._events
            if start_date <= e.timestamp <= end_date
        ]
        return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def get_failed_login_attempts(
        self,
        hours: int = 24
    ) -> Dict[str, List[AuditEvent]]:
        """
        Get failed login attempts grouped by IP.

        Args:
            hours: Number of hours to look back

        Returns:
            Dictionary mapping IP to list of failed attempts
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        failed_logins = [
            e for e in self._events
            if e.event_type == AuditEventType.AUTH_LOGIN_FAILED
            and e.timestamp > cutoff
        ]

        # Group by IP
        by_ip: Dict[str, List[AuditEvent]] = {}
        for event in failed_logins:
            if event.ip_address not in by_ip:
                by_ip[event.ip_address] = []
            by_ip[event.ip_address].append(event)

        return by_ip

    async def cleanup_old_events(self) -> int:
        """
        Remove events older than retention period.

        Returns:
            Number of events removed
        """
        cutoff = datetime.utcnow() - timedelta(days=self._retention_days)
        original_count = len(self._events)

        self._events = [
            e for e in self._events
            if e.timestamp > cutoff
        ]

        removed = original_count - len(self._events)
        if removed > 0:
            self._logger.info(f"Cleaned up {removed} old audit events")

        return removed

    async def generate_audit_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate audit report for date range.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Audit report data
        """
        events = await self.get_events_by_date_range(start_date, end_date, limit=10000)

        # Generate statistics
        stats = {
            "total_events": len(events),
            "by_type": {},
            "by_severity": {},
            "by_user": {},
            "failed_logins": 0,
            "successful_logins": 0
        }

        for event in events:
            # Count by type
            event_type = event.event_type.value
            stats["by_type"][event_type] = stats["by_type"].get(event_type, 0) + 1

            # Count by severity
            severity = event.severity.value
            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1

            # Count by user
            if event.username:
                stats["by_user"][event.username] = stats["by_user"].get(event.username, 0) + 1

            # Count auth events
            if event.event_type == AuditEventType.AUTH_LOGIN_SUCCESS:
                stats["successful_logins"] += 1
            elif event.event_type == AuditEventType.AUTH_LOGIN_FAILED:
                stats["failed_logins"] += 1

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "statistics": stats,
            "events": [e.to_dict() for e in events[:100]]  # Include first 100 events
        }

    async def check_security_thresholds(self) -> List[Dict[str, Any]]:
        """
        Check for security threshold violations.

        Returns:
            List of security alerts
        """
        alerts = []

        # Check for brute force attacks
        failed_logins = await self.get_failed_login_attempts(hours=1)
        for ip, attempts in failed_logins.items():
            if len(attempts) > 10:
                alerts.append({
                    "type": "brute_force_detected",
                    "severity": "high",
                    "ip_address": ip,
                    "attempts": len(attempts),
                    "message": f"More than 10 failed login attempts from {ip} in the last hour"
                })

        # Check for suspicious activity patterns
        # TODO: Add more sophisticated anomaly detection

        return alerts


# Global audit logger instance
audit_logger = AuditLogger()


__all__ = [
    'AuditLogger',
    'audit_logger',
    'AuditEvent',
    'AuditEventType',
    'EventSeverity',
]
