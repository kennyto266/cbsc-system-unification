"""
Comprehensive Audit Logging System

This module provides extensive audit logging for all security-relevant events
in the CBSC system, particularly for non-price strategy access and modifications.
Ensures compliance with financial regulations and security best practices.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import sqlite3
import aiofiles
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""

    # Authentication events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"

    # Authorization events
    ROLE_CHANGE = "role_change"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"
    API_ACCESS = "api_access"
    STRATEGY_ACCESS = "strategy_access"
    DATA_ACCESS = "data_access"

    # Strategy events
    STRATEGY_EXECUTION = "strategy_execution"
    STRATEGY_CREATION = "strategy_creation"
    STRATEGY_MODIFICATION = "strategy_modification"
    STRATEGY_DELETION = "strategy_deletion"
    PARAMETER_CHANGE = "parameter_change"

    # Non-price strategy specific
    MACRO_DATA_ACCESS = "macro_data_access"
    SENTIMENT_DATA_ACCESS = "sentiment_data_access"
    HKMA_API_CALL = "hkma_api_call"
    NON_PRICE_STRATEGY_EXECUTION = "non_price_strategy_execution"

    # Data operations
    DATA_EXPORT = "data_export"
    DATA_IMPORT = "data_import"
    DATA_BACKUP = "data_backup"
    DATA_RESTORE = "data_restore"

    # Configuration changes
    CONFIGURATION_CHANGE = "configuration_change"
    API_KEY_CREATION = "api_key_creation"
    API_KEY_DELETION = "api_key_deletion"
    API_KEY_USAGE = "api_key_usage"

    # Security events
    SECURITY_VIOLATION = "security_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    ERROR_OCCURRED = "error_occurred"
    SERVICE_UNAVAILABLE = "service_unavailable"


class EventSeverity(Enum):
    """Severity levels for audit events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """Single audit log entry"""
    timestamp: str
    event_type: AuditEventType
    severity: EventSeverity
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    resource: Optional[str]
    action: Optional[str]
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class AuditLogger:
    """Comprehensive audit logging system"""

    def __init__(self, db_path: str = "audit_logs.db"):
        self.db_path = db_path
        self.logger = logging.getLogger('audit')
        self.buffer: List[AuditEntry] = []
        self.buffer_size = 1000
        self.flush_interval = 300  # 5 minutes
        self._lock = asyncio.Lock()
        self._initialize_database()

    def _initialize_database(self):
        """Initialize audit database with proper schema"""

        try:
            # Create database directory if it doesn't exist
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Create audit logs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        user_id TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        session_id TEXT,
                        request_id TEXT,
                        resource TEXT,
                        action TEXT,
                        details TEXT,  -- JSON string
                        success BOOLEAN,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for efficient queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                    ON audit_logs(timestamp)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_user_timestamp
                    ON audit_logs(user_id, timestamp)
                """)

                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_audit_event_timestamp
                    ON audit_logs(event_type, timestamp)
                """)

                conn.commit()
                self.logger.info("Audit database initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize audit database: {e}")
            raise

    async def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        severity: Optional[EventSeverity] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> None:
        """Log an audit event"""

        try:
            # Determine severity if not provided
            if not severity:
                severity = self._determine_severity(event_type, success, details)

            # Create audit entry
            entry = AuditEntry(
                timestamp=datetime.now().isoformat(),
                event_type=event_type,
                severity=severity,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                request_id=request_id,
                resource=resource,
                action=action,
                details=details or {},
                success=success,
                error_message=error_message
            )

            # Add to buffer
            async with self._lock:
                self.buffer.append(entry)

                # Log immediately for critical events
                if severity in [EventSeverity.CRITICAL, EventSeverity.HIGH]:
                    await self._flush_to_storage([entry])

                # Flush buffer if it's full
                if len(self.buffer) >= self.buffer_size:
                    await self._flush_buffer()

        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")

    def _determine_severity(
        self,
        event_type: AuditEventType,
        success: bool,
        details: Optional[Dict[str, Any]]
    ) -> EventSeverity:
        """Determine event severity based on type and context"""

        critical_events = {
            AuditEventType.SECURITY_VIOLATION,
            AuditEventType.DATA_BREACH_ATTEMPT,
            AuditEventType.UNAUTHORIZED_ACCESS,
            AuditEventType.SYSTEM_SHUTDOWN,
        }

        high_severity_events = {
            AuditEventType.ROLE_CHANGE,
            AuditEventType.PERMISSION_DENIED,
            AuditEventType.CONFIGURATION_CHANGE,
            AuditEventType.DATA_EXPORT,
            AuditEventType.API_KEY_DELETION,
            AuditEventType.RATE_LIMIT_EXCEEDED,
        }

        medium_severity_events = {
            AuditEventType.LOGIN_FAILED,
            AuditEventType.PASSWORD_CHANGE,
            AuditEventType.STRATEGY_DELETION,
            AuditEventType.DATA_RESTORE,
            AuditEventType.SUSPICIOUS_ACTIVITY,
        }

        if event_type in critical_events:
            return EventSeverity.CRITICAL
        elif event_type in high_severity_events:
            return EventSeverity.HIGH
        elif not success or event_type in medium_severity_events:
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW

    async def _flush_buffer(self) -> None:
        """Flush audit buffer to storage"""

        if not self.buffer:
            return

        # Copy buffer and clear
        entries_to_flush = self.buffer.copy()
        self.buffer.clear()

        await self._flush_to_storage(entries_to_flush)

    async def _flush_to_storage(self, entries: List[AuditEntry]) -> None:
        """Flush audit entries to database storage"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                for entry in entries:
                    # Convert entry to database format
                    cursor.execute("""
                        INSERT INTO audit_logs (
                            timestamp, event_type, severity, user_id,
                            ip_address, user_agent, session_id, request_id,
                            resource, action, details, success, error_message
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.timestamp,
                        entry.event_type.value,
                        entry.severity.value,
                        entry.user_id,
                        entry.ip_address,
                        entry.user_agent,
                        entry.session_id,
                        entry.request_id,
                        entry.resource,
                        entry.action,
                        json.dumps(entry.details),
                        entry.success,
                        entry.error_message
                    ))

                conn.commit()

            # Also log to system logger for critical events
            for entry in entries:
                if entry.severity in [EventSeverity.CRITICAL, EventSeverity.HIGH]:
                    self.logger.warning(
                        f"Critical Audit: {entry.event_type.value} - "
                        f"User: {entry.user_id} - IP: {entry.ip_address} - "
                        f"Details: {entry.details}"
                    )

        except Exception as e:
            self.logger.error(f"Failed to flush audit entries: {e}")

    async def search_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        severity: Optional[EventSeverity] = None,
        success: Optional[bool] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search audit logs with filters"""

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build query
                query = "SELECT * FROM audit_logs WHERE 1=1"
                params = []

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())

                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())

                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)

                if event_type:
                    query += " AND event_type = ?"
                    params.append(event_type.value)

                if severity:
                    query += " AND severity = ?"
                    params.append(severity.value)

                if success is not None:
                    query += " AND success = ?"
                    params.append(success)

                # Add ordering and pagination
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])

                # Execute query
                cursor.execute(query, params)
                rows = cursor.fetchall()

                # Convert to list of dictionaries
                columns = [desc[0] for desc in cursor.description]
                results = []

                for row in rows:
                    entry = dict(zip(columns, row))
                    # Parse JSON details
                    if entry['details']:
                        entry['details'] = json.loads(entry['details'])
                    results.append(entry)

                return results

        except Exception as e:
            self.logger.error(f"Failed to search audit logs: {e}")
            return []

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_type: str = "security"
    ) -> Dict[str, Any]:
        """Generate compliance report for audit period"""

        try:
            # Fetch all audit logs for the period
            audit_logs = await self.search_audit_logs(
                start_date=start_date,
                end_date=end_date,
                limit=100000  # Large limit for comprehensive report
            )

            # Generate report based on type
            if report_type == "security":
                return self._generate_security_report(audit_logs, start_date, end_date)
            elif report_type == "access":
                return self._generate_access_report(audit_logs, start_date, end_date)
            elif report_type == "data":
                return self._generate_data_access_report(audit_logs, start_date, end_date)
            elif report_type == "non_price_strategies":
                return self._generate_non_price_strategy_report(audit_logs, start_date, end_date)
            else:
                return self._generate_general_report(audit_logs, start_date, end_date)

        except Exception as e:
            self.logger.error(f"Failed to generate compliance report: {e}")
            return {"error": str(e)}

    def _generate_security_report(
        self,
        audit_logs: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate security-focused compliance report"""

        # Filter security events
        security_events = [
            log for log in audit_logs
            if log.get('severity') in ['critical', 'high']
        ]

        security_violations = [
            log for log in security_events
            if log.get('event_type') == 'security_violation'
        ]

        failed_logins = [
            log for log in audit_logs
            if log.get('event_type') == 'login_failed'
        ]

        unauthorized_access = [
            log for log in audit_logs
            if log.get('event_type') == 'unauthorized_access'
        ]

        return {
            "report_type": "security",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_events": len(audit_logs),
                "security_events": len(security_events),
                "security_violations": len(security_violations),
                "failed_logins": len(failed_logins),
                "unauthorized_access": len(unauthorized_access)
            },
            "details": {
                "security_violations_by_type": self._group_by_field(
                    security_violations, "details.violation_type"
                ),
                "failed_login_ips": list(set(
                    log.get("ip_address") for log in failed_logins if log.get("ip_address")
                )),
                "unauthorized_endpoints": list(set(
                    log.get("resource") for log in unauthorized_access if log.get("resource")
                )),
                "high_risk_activities": [
                    log for log in security_events
                    if log.get("severity") == "critical"
                ]
            },
            "recommendations": self._generate_security_recommendations(security_violations)
        }

    def _generate_non_price_strategy_report(
        self,
        audit_logs: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate report specific to non-price strategy activities"""

        # Filter non-price strategy events
        macro_data_access = [
            log for log in audit_logs
            if log.get('event_type') == 'macro_data_access'
        ]

        sentiment_data_access = [
            log for log in audit_logs
            if log.get('event_type') == 'sentiment_data_access'
        ]

        hkma_api_calls = [
            log for log in audit_logs
            if log.get('event_type') == 'hkma_api_call'
        ]

        non_price_executions = [
            log for log in audit_logs
            if log.get('event_type') == 'non_price_strategy_execution'
        ]

        return {
            "report_type": "non_price_strategies",
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "macro_data_access": len(macro_data_access),
                "sentiment_data_access": len(sentiment_data_access),
                "hkma_api_calls": len(hkma_api_calls),
                "non_price_executions": len(non_price_executions)
            },
            "usage_by_user": {
                "macro_data": self._count_by_user(macro_data_access),
                "sentiment_data": self._count_by_user(sentiment_data_access),
                "non_price_executions": self._count_by_user(non_price_executions)
            },
            "api_usage": {
                "hkma_calls_by_endpoint": self._group_by_field(hkma_api_calls, "resource"),
                "success_rate": self._calculate_success_rate(hkma_api_calls)
            },
            "compliance": {
                "all_accesses_authorized": all(
                    log.get('success', False) for log in macro_data_access + sentiment_data_access
                ),
                "data_access_patterns": self._analyze_access_patterns(audit_logs)
            }
        }

    def _group_by_field(self, items: List[Dict], field_path: str) -> Dict[str, int]:
        """Group items by a nested field"""

        groups = {}
        for item in items:
            try:
                # Navigate nested field path
                value = item
                for field in field_path.split('.'):
                    if isinstance(value, dict) and field in value:
                        value = value[field]
                    else:
                        value = None
                        break

                if value:
                    groups[str(value)] = groups.get(str(value), 0) + 1

            except Exception:
                continue

        return groups

    def _count_by_user(self, items: List[Dict]) -> Dict[str, int]:
        """Count items by user ID"""
        counts = {}
        for item in items:
            user_id = item.get('user_id', 'unknown')
            counts[user_id] = counts.get(user_id, 0) + 1
        return counts

    def _calculate_success_rate(self, items: List[Dict]) -> float:
        """Calculate success rate percentage"""
        if not items:
            return 0.0
        success_count = sum(1 for item in items if item.get('success', False))
        return (success_count / len(items)) * 100

    def _analyze_access_patterns(self, audit_logs: List[Dict]) -> Dict[str, Any]:
        """Analyze data access patterns for anomalies"""

        # Group by hour of day
        hourly_access = {}
        for log in audit_logs:
            if log.get('event_type') in ['macro_data_access', 'sentiment_data_access']:
                timestamp = datetime.fromisoformat(log['timestamp'])
                hour = timestamp.hour
                hourly_access[hour] = hourly_access.get(hour, 0) + 1

        # Find unusual access hours
        business_hours = range(9, 18)
        after_hours_access = sum(
            count for hour, count in hourly_access.items()
            if hour not in business_hours
        )

        return {
            "hourly_distribution": hourly_access,
            "after_hours_access": after_hours_access,
            "peak_access_hour": max(hourly_access.items(), key=lambda x: x[1])[0] if hourly_access else None,
            "weekend_access": len([
                log for log in audit_logs
                if datetime.fromisoformat(log['timestamp']).weekday() >= 5
                and log.get('event_type') in ['macro_data_access', 'sentiment_data_access']
            ])
        }

    def _generate_security_recommendations(self, violations: List[Dict]) -> List[str]:
        """Generate security recommendations based on violations"""

        recommendations = []
        violation_types = set()

        for violation in violations:
            if 'details' in violation:
                violation_type = violation['details'].get('violation_type')
                if violation_type:
                    violation_types.add(violation_type)

        # Generate recommendations
        if 'unauthorized_access' in violation_types:
            recommendations.append("Review and strengthen access control policies")
        if 'data_exfiltration' in violation_types:
            recommendations.append("Implement data loss prevention (DLP) measures")
        if 'suspicious_activity' in violation_types:
            recommendations.append("Implement real-time behavioral analysis")
        if 'rate_limit_exceeded' in violation_types:
            recommendations.append("Review and adjust rate limiting thresholds")

        if not recommendations:
            recommendations.append("Continue monitoring security events")

        return recommendations

    async def start_background_flusher(self) -> None:
        """Start background task to flush audit buffer periodically"""

        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()

            except Exception as e:
                self.logger.error(f"Background audit flusher error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def cleanup_old_logs(self, retention_days: int = 365) -> int:
        """Clean up audit logs older than retention period"""

        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM audit_logs WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                deleted_count = cursor.rowcount
                conn.commit()

            self.logger.info(f"Cleaned up {deleted_count} old audit log entries")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup old audit logs: {e}")
            return 0


# Global audit logger instance
audit_logger = AuditLogger()


# Convenience functions for common audit events
async def log_security_event(
    event_type: AuditEventType,
    user_id: Optional[str] = None,
    **kwargs
):
    """Log a security-related event"""
    await audit_logger.log_event(
        event_type=event_type,
        user_id=user_id,
        severity=EventSeverity.HIGH,
        **kwargs
    )


async def log_strategy_access(
    user_id: str,
    strategy_type: str,
    strategy_id: Optional[str] = None,
    **kwargs
):
    """Log strategy access event"""
    await audit_logger.log_event(
        event_type=AuditEventType.STRATEGY_ACCESS,
        user_id=user_id,
        resource=strategy_type,
        details={
            "strategy_type": strategy_type,
            "strategy_id": strategy_id,
            **kwargs
        },
        **kwargs
    )


async def log_non_price_strategy_execution(
    user_id: str,
    strategy_name: str,
    execution_details: Dict[str, Any],
    **kwargs
):
    """Log non-price strategy execution"""
    await audit_logger.log_event(
        event_type=AuditEventType.NON_PRICE_STRATEGY_EXECUTION,
        user_id=user_id,
        resource="non_price_strategy",
        action="execute",
        details={
            "strategy_name": strategy_name,
            "execution_details": execution_details,
            **kwargs.get('details', {})
        },
        **kwargs
    )