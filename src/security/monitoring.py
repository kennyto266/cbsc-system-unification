"""
Security Monitoring and Alerting System

This module provides real-time security monitoring, threat detection,
and automated response capabilities for the CBSC system.
"""

import os
import time
import asyncio
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from collections import defaultdict, deque
import redis
import smtplib
from functools import wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Security threat levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of security alerts"""
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_VIOLATION = "rate_limit_violation"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MALICIOUS_IP = "malicious_ip"
    UNUSUAL_LOGIN = "unusual_login"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ANOMALOUS_DATA_ACCESS = "anomalous_data_access"
    SYSTEM_COMPROMISE = "system_compromise"


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    id: str
    timestamp: str
    alert_type: AlertType
    threat_level: ThreatLevel
    user_id: Optional[str]
    ip_address: Optional[str]
    resource: Optional[str]
    description: str
    details: Dict[str, Any]
    status: str = "open"  # open, acknowledged, resolved, false_positive
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    mitigation_actions: List[str] = None

    def __post_init__(self):
        if self.mitigation_actions is None:
            self.mitigation_actions = []


@dataclass
class SecurityMetrics:
    """Security metrics for monitoring"""
    total_requests: int
    failed_logins: int
    rate_limit_violations: int
    security_alerts: int
    blocked_ips: int
    data_access_anomalies: int
    timestamp: str


class ThreatDetector:
    """Detects security threats based on patterns and anomalies"""

    def __init__(self):
        self.redis_client = None
        self._connect_redis()
        self._thresholds = self._load_thresholds()

    def _connect_redis(self):
        """Connect to Redis for storing patterns"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=int(os.getenv('REDIS_DB_SECURITY', '2')),
                decode_responses=True
            )
            self.redis_client.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis for threat detection: {e}")

    def _load_thresholds(self) -> Dict[str, Any]:
        """Load threat detection thresholds"""
        return {
            'failed_login_threshold': 5,  # 5 failed logins in 5 minutes
            'rate_limit_threshold': 10,  # 10 rate limit violations in 1 hour
            'concurrent_sessions_threshold': 10,  # More than 10 concurrent sessions
            'data_access_rate_threshold': 1000,  # Unusual data access rate
            'off_hours_access_threshold': 0.8,  # 80% of access outside business hours
            'unusual_location_threshold': 2,  # Login from 2+ new countries in 24h
        }

    async def detect_failed_login_pattern(self, user_id: str, ip_address: str) -> Optional[AlertType]:
        """Detect failed login patterns"""

        try:
            key = f"failed_logins:{user_id}"
            current_time = int(time.time())
            window_start = current_time - 300  # 5 minutes

            # Count failed attempts
            if self.redis_client:
                failed_count = self.redis_client.zcount(key, window_start, current_time)
            else:
                # Fallback to in-memory
                failed_count = 0  # Implement in-memory logic if needed

            if failed_count >= self._thresholds['failed_login_threshold']:
                return AlertType.UNAUTHORIZED_ACCESS

            return None

        except Exception as e:
            logger.error(f"Error detecting failed login pattern: {e}")
            return None

    async def detect_rate_limit_abuse(self, ip_address: str) -> Optional[AlertType]:
        """Detect rate limit abuse patterns"""

        try:
            key = f"rate_violations:{ip_address}"
            current_time = int(time.time())
            window_start = current_time - 3600  # 1 hour

            # Count violations
            if self.redis_client:
                violation_count = self.redis_client.zcount(key, window_start, current_time)
            else:
                violation_count = 0

            if violation_count >= self._thresholds['rate_limit_threshold']:
                return AlertType.RATE_LIMIT_VIOLATION

            return None

        except Exception as e:
            logger.error(f"Error detecting rate limit abuse: {e}")
            return None

    async def detect_anomalous_data_access(
        self,
        user_id: str,
        access_count: int,
        time_window: int = 300
    ) -> Optional[AlertType]:
        """Detect unusual data access patterns"""

        try:
            # Get user's baseline access pattern
            baseline_key = f"baseline_access:{user_id}"
            if self.redis_client:
                baseline = self.redis_client.get(baseline_key)
                if baseline:
                    baseline_count = json.loads(baseline).get('avg_access', 0)
                else:
                    baseline_count = 50  # Default baseline
            else:
                baseline_count = 50

            # Check if current access is significantly higher
            if access_count > baseline_count * 10:  # 10x increase
                return AlertType.ANOMALOUS_DATA_ACCESS

            return None

        except Exception as e:
            logger.error(f"Error detecting anomalous data access: {e}")
            return None

    async def detect_privilege_escalation(
        self,
        user_id: str,
        old_role: str,
        new_role: str
    ) -> Optional[AlertType]:
        """Detect suspicious privilege escalation"""

        try:
            # Define role hierarchy
            role_hierarchy = {
                'basic': 0,
                'premium': 1,
                'non_price_viewer': 2,
                'quant_analyst': 3,
                'non_price_analyst': 4,
                'institutional': 5,
                'non_price_admin': 6,
                'admin': 7
            }

            old_level = role_hierarchy.get(old_role, 0)
            new_level = role_hierarchy.get(new_role, 0)

            # Check for suspicious escalation (skipping levels)
            if new_level > old_level + 1:
                return AlertType.PRIVILEGE_ESCALATION

            return None

        except Exception as e:
            logger.error(f"Error detecting privilege escalation: {e}")
            return None


class SecurityMonitor:
    """Main security monitoring system"""

    def __init__(self):
        self.redis_client = None
        self.threat_detector = ThreatDetector()
        self.alert_handlers: Dict[AlertType, List[Callable]] = defaultdict(list)
        self._connect_redis()
        self._init_alert_handlers()

    def _connect_redis(self):
        """Connect to Redis for storing security data"""
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=int(os.getenv('REDIS_DB_SECURITY', '2')),
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Security monitor connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for security monitoring: {e}")

    def _init_alert_handlers(self):
        """Initialize default alert handlers"""
        self.alert_handlers[AlertType.UNAUTHORIZED_ACCESS].append(
            self._handle_unauthorized_access
        )
        self.alert_handlers[AlertType.RATE_LIMIT_VIOLATION].append(
            self._handle_rate_limit_violation
        )
        self.alert_handlers[AlertType.DATA_BREACH_ATTEMPT].append(
            self._handle_data_breach_attempt
        )

    async def create_alert(
        self,
        alert_type: AlertType,
        threat_level: ThreatLevel,
        description: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> SecurityAlert:
        """Create a new security alert"""

        alert_id = f"alert_{int(time.time())}_{alert_type.value}"
        alert = SecurityAlert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            alert_type=alert_type,
            threat_level=threat_level,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            description=description,
            details=details or {}
        )

        # Store alert
        await self._store_alert(alert)

        # Execute handlers
        handlers = self.alert_handlers.get(alert_type, [])
        for handler in handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

        # Send notifications for high/critical alerts
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            await self._send_alert_notification(alert)

        return alert

    async def _store_alert(self, alert: SecurityAlert):
        """Store alert in Redis"""
        if self.redis_client:
            try:
                key = f"security_alert:{alert.id}"
                self.redis_client.setex(
                    key,
                    86400 * 30,  # Keep for 30 days
                    json.dumps(asdict(alert), default=str)
                )

                # Add to alerts list
                self.redis_client.lpush(
                    "security_alerts",
                    alert.id
                )
                self.redis_client.expire("security_alerts", 86400 * 30)

                # Add to threat-specific list
                threat_key = f"alerts:{alert.alert_type.value}"
                self.redis_client.lpush(threat_key, alert.id)
                self.redis_client.expire(threat_key, 86400 * 30)

            except Exception as e:
                logger.error(f"Failed to store alert: {e}")

    async def get_active_alerts(
        self,
        alert_type: Optional[AlertType] = None,
        threat_level: Optional[ThreatLevel] = None,
        limit: int = 100
    ) -> List[SecurityAlert]:
        """Get active security alerts"""

        try:
            if alert_type:
                alert_ids = self.redis_client.lrange(
                    f"alerts:{alert_type.value}", 0, limit - 1
                )
            else:
                alert_ids = self.redis_client.lrange("security_alerts", 0, limit - 1)

            alerts = []
            for alert_id in alert_ids:
                alert_data = self.redis_client.get(f"security_alert:{alert_id}")
                if alert_data:
                    alert = json.loads(alert_data)
                    if not threat_level or alert['threat_level'] == threat_level.value:
                        alerts.append(SecurityAlert(**alert))

            return alerts

        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []

    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str
    ) -> bool:
        """Acknowledge a security alert"""

        try:
            key = f"security_alert:{alert_id}"
            alert_data = self.redis_client.get(key)

            if alert_data:
                alert = json.loads(alert_data)
                alert['status'] = 'acknowledged'
                alert['acknowledged_by'] = acknowledged_by
                alert['acknowledged_at'] = datetime.now().isoformat()

                self.redis_client.setex(
                    key,
                    86400 * 30,
                    json.dumps(alert, default=str)
                )

                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
            return False

    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """Resolve a security alert"""

        try:
            key = f"security_alert:{alert_id}"
            alert_data = self.redis_client.get(key)

            if alert_data:
                alert = json.loads(alert_data)
                alert['status'] = 'resolved'
                alert['resolved_by'] = resolved_by
                alert['resolved_at'] = datetime.now().isoformat()

                if resolution_notes:
                    alert['details']['resolution_notes'] = resolution_notes

                self.redis_client.setex(
                    key,
                    86400 * 30,
                    json.dumps(alert, default=str)
                )

                logger.info(f"Alert {alert_id} resolved by {resolved_by}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to resolve alert: {e}")
            return False

    async def _handle_unauthorized_access(self, alert: SecurityAlert):
        """Handle unauthorized access alerts"""
        mitigation_actions = []

        # Block IP if critical
        if alert.threat_level == ThreatLevel.CRITICAL:
            await self._block_ip_address(alert.ip_address, "Unauthorized access attempt")
            mitigation_actions.append(f"Blocked IP: {alert.ip_address}")

        # Suspend user if repeated violations
        if alert.user_id:
            violation_count = await self._get_user_violation_count(alert.user_id)
            if violation_count >= 3:
                await self._suspend_user_account(alert.user_id, "Repeated unauthorized access")
                mitigation_actions.append(f"Suspended user: {alert.user_id}")

        alert.mitigation_actions.extend(mitigation_actions)

    async def _handle_rate_limit_violation(self, alert: SecurityAlert):
        """Handle rate limit violation alerts"""
        if alert.threat_level == ThreatLevel.HIGH:
            # Temporarily reduce rate limits for the IP
            await self._apply_rate_limit_penalty(alert.ip_address, 0.5)
            alert.mitigation_actions.append(f"Applied rate limit penalty to IP: {alert.ip_address}")

    async def _handle_data_breach_attempt(self, alert: SecurityAlert):
        """Handle data breach attempt alerts"""
        # Immediately block IP
        await self._block_ip_address(alert.ip_address, "Data breach attempt")
        alert.mitigation_actions.append(f"Blocked IP: {alert.ip_address}")

        # Suspend user account
        if alert.user_id:
            await self._suspend_user_account(alert.user_id, "Data breach attempt")
            alert.mitigation_actions.append(f"Suspended user: {alert.user_id}")

        # Notify security team immediately
        await self._send_emergency_notification(alert)

    async def _block_ip_address(self, ip_address: str, reason: str, duration: int = 3600):
        """Block an IP address"""

        if self.redis_client:
            block_key = f"blocked_ip:{ip_address}"
            block_data = {
                "reason": reason,
                "blocked_at": datetime.now().isoformat(),
                "duration": duration
            }
            self.redis_client.setex(
                block_key,
                duration,
                json.dumps(block_data)
            )

        logger.warning(f"Blocked IP {ip_address} for {duration} seconds: {reason}")

    async def _suspend_user_account(self, user_id: str, reason: str):
        """Suspend a user account"""
        # This would integrate with your user management system
        logger.warning(f"Suspended user {user_id}: {reason}")

    async def _apply_rate_limit_penalty(self, ip_address: str, factor: float):
        """Apply rate limit penalty to IP"""
        penalty_key = f"rate_penalty:{ip_address}"
        if self.redis_client:
            self.redis_client.setex(penalty_key, 3600, str(factor))

    async def _get_user_violation_count(self, user_id: str) -> int:
        """Get count of violations for user"""
        # Implementation would query audit logs or Redis
        return 0

    async def _send_alert_notification(self, alert: SecurityAlert):
        """Send alert notification to configured channels"""
        # Implementation would send to Slack, email, etc.
        logger.warning(f"SECURITY ALERT: {alert.description}")

    async def _send_emergency_notification(self, alert: SecurityAlert):
        """Send emergency notification for critical threats"""
        # Implementation for immediate notification (SMS, phone call, etc.)
        logger.critical(f"EMERGENCY: {alert.description}")

    async def generate_security_metrics(self) -> SecurityMetrics:
        """Generate current security metrics"""
        # Implementation would aggregate metrics from various sources
        return SecurityMetrics(
            total_requests=0,
            failed_logins=0,
            rate_limit_violations=0,
            security_alerts=0,
            blocked_ips=0,
            data_access_anomalies=0,
            timestamp=datetime.now().isoformat()
        )

    async def start_monitoring(self):
        """Start continuous security monitoring"""
        logger.info("Security monitoring started")
        while True:
            try:
                # Run periodic checks
                await self._periodic_security_checks()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in security monitoring: {e}")
                await asyncio.sleep(60)

    async def _periodic_security_checks(self):
        """Run periodic security checks"""
        # Check for new threats
        # Update metrics
        # Clean old data
        pass


# Global security monitor instance
security_monitor = SecurityMonitor()


# Security event decorators
def monitor_security_event(event_type: str):
    """Decorator to monitor security events"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request context
            request = None
            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                    break

            user_id = getattr(request.state, 'user_id', None) if request else None
            ip_address = request.client.host if request else None

            # Log the event
            await security_monitor.create_alert(
                alert_type=AlertType.SUSPICIOUS_PATTERN,
                threat_level=ThreatLevel.MEDIUM,
                description=f"Security event: {event_type}",
                user_id=user_id,
                ip_address=ip_address,
                details={"event_type": event_type}
            )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Initialize security monitoring
async def initialize_security_monitoring():
    """Initialize security monitoring system"""
    # Start background monitoring
    asyncio.create_task(security_monitor.start_monitoring())
    logger.info("Security monitoring system initialized")