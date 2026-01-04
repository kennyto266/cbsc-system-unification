"""
Security Audit Manager
安全審計管理器

提供全面的安全審計日誌記錄和異常行為檢測功能。

Usage:
    ```python
    from src.logging_utils import get_audit_manager

    audit = get_audit_manager()

    # Audit user action
    audit.audit_user_action(
        user_id="123",
        action="view_strategy",
        resource="strategy:momentum-001",
        result="success",
        user_ip="192.168.1.1",
        session_id="abc-123"
    )

    # Detect suspicious activity
    suspicious = audit.detect_suspicious_activity(user_logs)
    ```
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum

try:
    from .structured_logger import StructuredLogger, SecurityAuditLog, SecurityEventType
except ImportError:
    # Fallback for direct import
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from logging.structured_logger import StructuredLogger, SecurityAuditLog, SecurityEventType


class RiskLevel(Enum):
    """風險級別"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SuspiciousActivity:
    """可疑活動"""
    pattern_name: str
    risk_score: float
    risk_level: RiskLevel
    detected_at: float
    details: Dict[str, Any]
    user_id: str


class SecurityAuditManager:
    """
    安全審計管理器

    提供全面的安全審計日誌記錄功能，包括：
    - 用戶操作審計
    - 異常行為檢測
    - 風險評分計算
    - 審計報表生成

    Attributes:
        logger: 結構化日誌記錄器
    """

    def __init__(self, logger: StructuredLogger = None):
        self.logger = logger
        self.suspicious_patterns = []
        self._setup_suspicious_patterns()

        # User activity tracking
        self._user_activities: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._user_login_attempts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self._failed_logins: Dict[str, int] = defaultdict(int)

        # Risk thresholds
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.7,
            RiskLevel.CRITICAL: 0.9
        }

    def _setup_suspicious_patterns(self):
        """設置可疑行為模式"""
        self.suspicious_patterns = [
            {
                "name": "frequent_failed_logins",
                "description": "頻繁登錄失敗",
                "condition": self._check_frequent_failed_logins,
                "risk_score": 0.8
            },
            {
                "name": "abnormal_location",
                "description": "異常登錄地點",
                "condition": self._check_abnormal_location,
                "risk_score": 0.7
            },
            {
                "name": "sensitive_data_access",
                "description": "敏感數據訪問",
                "condition": self._check_sensitive_data_access,
                "risk_score": 0.6
            },
            {
                "name": "bulk_operations",
                "description": "批量操作",
                "condition": self._check_bulk_operations,
                "risk_score": 0.5
            },
            {
                "name": "privilege_escalation",
                "description": "權限提升",
                "condition": self._check_privilege_escalation,
                "risk_score": 0.9
            },
            {
                "name": "unusual_time_access",
                "description": "異常時間訪問",
                "condition": self._check_unusual_time_access,
                "risk_score": 0.4
            }
        ]

    def audit_user_action(self,
                          user_id: str,
                          action: str,
                          resource: str,
                          result: str,
                          user_ip: str,
                          session_id: str,
                          details: Dict[str, Any] = None):
        """
        審計用戶操作

        Args:
            user_id: 用戶 ID
            action: 操作類型
            resource: 資源標識
            result: 操作結果
            user_ip: 用戶 IP
            session_id: 會話 ID
            details: 額外詳情
        """
        audit_log = SecurityAuditLog(
            timestamp=time.time(),
            event_type=SecurityEventType.DATA_ACCESS,
            user_id=user_id,
            user_ip=user_ip,
            action=action,
            resource=resource,
            result=result,
            details=details or {},
            session_id=session_id,
            risk_score=self._calculate_risk_score(user_id, action, resource)
        )

        if self.logger:
            self.logger.log_security_event(audit_log)

        # Track activity
        self._user_activities[user_id].append({
            "timestamp": audit_log.timestamp,
            "action": action,
            "resource": resource,
            "result": result,
            "user_ip": user_ip
        })

        # Clean old activities (> 24 hours)
        cutoff = time.time() - 86400
        self._user_activities[user_id] = [
            a for a in self._user_activities[user_id]
            if a["timestamp"] > cutoff
        ]

    def audit_login_attempt(self,
                            user_id: str,
                            user_ip: str,
                            success: bool,
                            user_agent: str = None,
                            session_id: str = None,
                            location: str = None):
        """
        審計登錄嘗試

        Args:
            user_id: 用戶 ID
            user_ip: 用戶 IP
            success: 是否成功
            user_agent: 用戶代理
            session_id: 會話 ID
            location: 地理位置
        """
        audit_log = SecurityAuditLog(
            timestamp=time.time(),
            event_type=SecurityEventType.LOGIN_ATTEMPT,
            user_id=user_id,
            user_ip=user_ip,
            action="login",
            resource="auth_service",
            result="success" if success else "failed",
            details={
                "user_agent": user_agent,
                "location": location,
                "success": success
            },
            session_id=session_id or "",
            risk_score=0.0 if success else 0.5
        )

        if self.logger:
            self.logger.log_security_event(audit_log)

        # Track login attempts
        self._user_login_attempts[user_id].append({
            "timestamp": audit_log.timestamp,
            "success": success,
            "user_ip": user_ip,
            "location": location
        })

        if not success:
            self._failed_logins[user_id] += 1
        else:
            # Reset failed login count on successful login
            self._failed_logins[user_id] = 0

        # Clean old attempts (> 1 hour)
        cutoff = time.time() - 3600
        self._user_login_attempts[user_id] = [
            a for a in self._user_login_attempts[user_id]
            if a["timestamp"] > cutoff
        ]

    def audit_strategy_access(self,
                               user_id: str,
                               strategy_id: str,
                               action: str,
                               result: str,
                               user_ip: str,
                               session_id: str):
        """
        審計策略訪問

        Args:
            user_id: 用戶 ID
            strategy_id: 策略 ID
            action: 操作類型
            result: 操作結果
            user_ip: 用戶 IP
            session_id: 會話 ID
        """
        self.audit_user_action(
            user_id=user_id,
            action=action,
            resource=f"strategy:{strategy_id}",
            result=result,
            user_ip=user_ip,
            session_id=session_id,
            details={"strategy_id": strategy_id}
        )

    def audit_trade_execution(self,
                              user_id: str,
                              symbol: str,
                              side: str,
                              quantity: float,
                              price: float,
                              strategy_id: str,
                              user_ip: str,
                              session_id: str):
        """
        審計交易執行

        Args:
            user_id: 用戶 ID
            symbol: 交易標的
            side: 買賣方向
            quantity: 數量
            price: 價格
            strategy_id: 策略 ID
            user_ip: 用戶 IP
            session_id: 會話 ID
        """
        self.audit_user_action(
            user_id=user_id,
            action="execute_trade",
            resource=f"trade:{symbol}",
            result="success",
            user_ip=user_ip,
            session_id=session_id,
            details={
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "strategy_id": strategy_id,
                "value": quantity * price
            }
        )

    def detect_suspicious_activity(self,
                                    user_id: str,
                                    check_last_hours: int = 24) -> List[SuspiciousActivity]:
        """
        檢測可疑活動

        Args:
            user_id: 用戶 ID
            check_last_hours: 檢查過去幾小時的活動

        Returns:
            可疑活動列表
        """
        suspicious_activities = []
        cutoff_time = time.time() - (check_last_hours * 3600)

        # Get recent activities
        user_logs = [
            log for log in self._user_activities.get(user_id, [])
            if log["timestamp"] > cutoff_time
        ]

        # Check each pattern
        for pattern in self.suspicious_patterns:
            try:
                if pattern["condition"](user_id, user_logs):
                    risk_score = pattern["risk_score"]
                    risk_level = self._get_risk_level(risk_score)

                    suspicious_activities.append(SuspiciousActivity(
                        pattern_name=pattern["name"],
                        risk_score=risk_score,
                        risk_level=risk_level,
                        detected_at=time.time(),
                        details={
                            "description": pattern["description"],
                            "user_id": user_id,
                            "check_period_hours": check_last_hours
                        },
                        user_id=user_id
                    ))
            except Exception as e:
                # Continue checking other patterns
                pass

        return suspicious_activities

    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """
        獲取用戶審計摘要

        Args:
            user_id: 用戶 ID

        Returns:
            用戶審計摘要
        """
        activities = self._user_activities.get(user_id, [])
        login_attempts = self._user_login_attempts.get(user_id, [])

        # Calculate statistics
        total_actions = len(activities)
        failed_logins = self._failed_logins.get(user_id, 0)

        # Recent activities (last 24 hours)
        cutoff = time.time() - 86400
        recent_activities = [a for a in activities if a["timestamp"] > cutoff]

        # Unique IPs
        unique_ips = set(a["user_ip"] for a in activities)

        # Action breakdown
        action_counts: Dict[str, int] = defaultdict(int)
        for activity in activities:
            action_counts[activity["action"]] += 1

        return {
            "user_id": user_id,
            "total_actions": total_actions,
            "recent_actions_24h": len(recent_activities),
            "failed_login_attempts": failed_logins,
            "unique_ips": len(unique_ips),
            "action_breakdown": dict(action_counts),
            "last_activity": activities[-1]["timestamp"] if activities else None
        }

    def get_audit_report(self,
                         start_time: float = None,
                         end_time: float = None) -> Dict[str, Any]:
        """
        生成審計報表

        Args:
            start_time: 開始時間
            end_time: 結束時間

        Returns:
            審計報表
        """
        if start_time is None:
            start_time = time.time() - 86400  # Default: last 24 hours
        if end_time is None:
            end_time = time.time()

        # Filter activities by time range
        all_activities = []
        for user_id, activities in self._user_activities.items():
            for activity in activities:
                if start_time <= activity["timestamp"] <= end_time:
                    all_activities.append({
                        "user_id": user_id,
                        **activity
                    })

        # Calculate statistics
        total_users = len(self._user_activities)
        total_actions = len(all_activities)

        # Action breakdown
        action_counts: Dict[str, int] = defaultdict(int)
        for activity in all_activities:
            action_counts[activity["action"]] += 1

        # Result breakdown
        result_counts: Dict[str, int] = defaultdict(int)
        for activity in all_activities:
            result_counts[activity["result"]] += 1

        return {
            "report_period": {
                "start_time": start_time,
                "end_time": end_time,
                "duration_hours": (end_time - start_time) / 3600
            },
            "summary": {
                "total_users": total_users,
                "total_actions": total_actions,
                "actions_per_user": total_actions / total_users if total_users > 0 else 0
            },
            "action_breakdown": dict(action_counts),
            "result_breakdown": dict(result_counts),
            "top_users": self._get_top_users(all_activities, limit=10)
        }

    # Pattern checking methods
    def _check_frequent_failed_logins(self, user_id: str, logs: List[Dict]) -> bool:
        """檢查頻繁登錄失敗"""
        return self._failed_logins.get(user_id, 0) >= 5

    def _check_abnormal_location(self, user_id: str, logs: List[Dict]) -> bool:
        """檢查異常登錄地點"""
        # Get unique IPs in last 24 hours
        recent_ips = set(
            log["user_ip"] for log in logs
            if time.time() - log["timestamp"] < 86400
        )
        return len(recent_ips) > 3

    def _check_sensitive_data_access(self, user_id: str, logs: List[Dict]) -> bool:
        """檢查敏感數據訪問"""
        sensitive_resources = ["user_data", "trading_config", "api_keys", "admin"]
        return any(
            any(r in log["resource"].lower() for r in sensitive_resources)
            for log in logs
            if time.time() - log["timestamp"] < 3600  # Last hour
        )

    def _check_bulk_operations(self, user_id: str, logs: List[Dict]) -> bool:
        """檢查批量操作"""
        # Count operations in last 5 minutes
        cutoff = time.time() - 300
        recent_ops = [log for log in logs if log["timestamp"] > cutoff]
        return len(recent_ops) > 50

    def _check_privilege_escalation(self, user_id: str, logs: List[Dict]) -> bool:
        """檢查權限提升"""
        privileged_actions = ["change_role", "grant_permission", "modify_admin"]
        return any(
            log["action"] in privileged_actions
            for log in logs
            if time.time() - log["timestamp"] < 3600
        )

    def _check_unusual_time_access(self, user_id: str, logs: List[Dict]) -> bool:
        """檢查異常時間訪問"""
        import datetime
        unusual_hours = range(0, 6)  # Midnight to 6 AM

        for log in logs:
            hour = datetime.datetime.fromtimestamp(log["timestamp"]).hour
            if hour in unusual_hours:
                return True
        return False

    # Helper methods
    def _calculate_risk_score(self, user_id: str, action: str, resource: str) -> float:
        """計算風險評分"""
        base_score = 0.1

        # Sensitive operations
        sensitive_actions = ["delete", "modify", "export", "download", "admin"]
        if any(action.startswith(s) for s in sensitive_actions):
            base_score += 0.3

        # Sensitive resources
        sensitive_resources = ["config", "admin", "system", "security", "api_keys"]
        if any(r in resource.lower() for r in sensitive_resources):
            base_score += 0.4

        # Failed login history
        if self._failed_logins.get(user_id, 0) > 0:
            base_score += 0.2 * min(self._failed_logins[user_id], 5)

        return min(base_score, 1.0)

    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """根據風險評分獲取風險級別"""
        if risk_score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif risk_score >= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _get_top_users(self, activities: List[Dict], limit: int = 10) -> List[Dict[str, Any]]:
        """獲取活躍用戶排行"""
        user_counts: Dict[str, int] = defaultdict(int)
        for activity in activities:
            user_counts[activity["user_id"]] += 1

        sorted_users = sorted(
            [{"user_id": uid, "action_count": count} for uid, count in user_counts.items()],
            key=lambda x: x["action_count"],
            reverse=True
        )

        return sorted_users[:limit]


# Global singleton
_audit_manager: Optional[SecurityAuditManager] = None


def get_audit_manager(logger: StructuredLogger = None) -> SecurityAuditManager:
    """獲取全局安全審計管理器單例"""
    global _audit_manager
    if _audit_manager is None:
        _audit_manager = SecurityAuditManager(logger)
    return _audit_manager
