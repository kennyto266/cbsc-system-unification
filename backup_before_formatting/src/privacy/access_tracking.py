"""
T106: 数据访问跟踪系统

实现数据访问跟踪功能，包括：
- 数据访问事件记录
- 用户操作追踪
- 异常访问检测
- 访问模式分析
- 未授权访问告警
"""

import hashlib
import json
import logging
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .audit_logger import AuditEvent, LogLevel


class AccessType(Enum):
    """访问类型"""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXPORT = "export"
    LOGIN = "login"
    LOGOUT = "logout"


class AccessStatus(Enum):
    """访问状态"""

    SUCCESS = "success"
    DENIED = "denied"
    FAILED = "failed"


class AccessEvent:
    """数据访问事件"""

    def __init__(
        self,
        event_id: str,
        user_id: str,
        resource: str,
        access_type: AccessType,
        status: AccessStatus,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        data_size: Optional[int] = None,
        sensitive_data: bool = False,
        location: Optional[str] = None,
        duration_ms: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.event_id = event_id
        self.timestamp = datetime.utcnow()
        self.user_id = user_id
        self.resource = resource
        self.access_type = (
            access_type
            if isinstance(access_type, AccessType)
            else AccessType(access_type)
        )
        self.status = (
            status if isinstance(status, AccessStatus) else AccessStatus(status)
        )
        self.source_ip = source_ip
        self.user_agent = user_agent
        self.data_size = data_size
        self.sensitive_data = sensitive_data
        self.location = location
        self.duration_ms = duration_ms
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "resource": self.resource,
            "access_type": self.access_type.value,
            "status": self.status.value,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent,
            "data_size": self.data_size,
            "sensitive_data": self.sensitive_data,
            "location": self.location,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class AccessPattern:
    """访问模式分析"""

    def __init__(self):
        self.user_patterns = defaultdict(list)
        self.resource_patterns = defaultdict(list)
        self.ip_patterns = defaultdict(list)
        self.time_patterns = defaultdict(list)

    def add_access(self, event: AccessEvent):
        """添加访问记录"""
        # 用户访问模式
        self.user_patterns[event.user_id].append(event)

        # 资源访问模式
        self.resource_patterns[event.resource].append(event)

        # IP访问模式
        if event.source_ip:
            self.ip_patterns[event.source_ip].append(event)

        # 时间访问模式
        hour = event.timestamp.hour
        self.time_patterns[hour].append(event)

    def get_user_frequency(self, user_id: str, hours: int = 24) -> int:
        """获取用户访问频率"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        accesses = [e for e in self.user_patterns[user_id] if e.timestamp >= cutoff]
        return len(accesses)

    def get_user_accessed_resources(self, user_id: str, hours: int = 24) -> Set[str]:
        """获取用户访问的资源"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        accesses = [e for e in self.user_patterns[user_id] if e.timestamp >= cutoff]
        return {e.resource for e in accesses}

    def get_resource_accessors(self, resource: str, hours: int = 24) -> Set[str]:
        """获取访问特定资源的用户"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        accesses = [
            e for e in self.resource_patterns[resource] if e.timestamp >= cutoff
        ]
        return {e.user_id for e in accesses}

    def get_peak_hours(self) -> List[int]:
        """获取访问高峰时段"""
        hourly_counts = {
            hour: len(events) for hour, events in self.time_patterns.items()
        }
        sorted_hours = sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, count in sorted_hours[:3]]


class AnomalyDetector:
    """异常检测器"""

    def __init__(
        self,
        access_pattern: AccessPattern,
        max_requests_per_hour: int = 100,
        max_unique_resources: int = 50,
        suspicious_ips: Optional[Set[str]] = None,
    ):
        self.pattern = access_pattern
        self.max_requests_per_hour = max_requests_per_hour
        self.max_unique_resources = max_unique_resources
        self.suspicious_ips = suspicious_ips or set()
        self.alert_callbacks = []
        self.logger = logging.getLogger("hk_quant_system.access_anomaly")

    def add_alert_callback(self, callback):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def check_event(self, event: AccessEvent) -> List[Dict[str, Any]]:
        """
        检查访问事件是否异常

        Returns:
            异常列表
        """
        anomalies = []

        # 检查高频访问
        if event.user_id:
            user_freq = self.pattern.get_user_frequency(event.user_id, hours=1)
            if user_freq > self.max_requests_per_hour:
                anomalies.append(
                    {
                        "type": "high_frequency",
                        "severity": "high",
                        "message": f"User {event.user_id} has {user_freq} requests in the last hour",
                        "event": event,
                    }
                )

        # 检查异常资源访问
        if event.user_id:
            resources = self.pattern.get_user_accessed_resources(event.user_id, hours=1)
            if len(resources) > self.max_unique_resources:
                anomalies.append(
                    {
                        "type": "excessive_resources",
                        "severity": "medium",
                        "message": f"User {event.user_id} accessed {len(resources)} resources in the last hour",
                        "event": event,
                    }
                )

        # 检查可疑IP
        if event.source_ip in self.suspicious_ips:
            anomalies.append(
                {
                    "type": "suspicious_ip",
                    "severity": "critical",
                    "message": f"Access from suspicious IP: {event.source_ip}",
                    "event": event,
                }
            )

        # 检查失败尝试
        if event.status == AccessStatus.DENIED:
            # 获取用户最近的失败尝试
            recent_failures = [
                e
                for e in self.pattern.user_patterns[event.user_id]
                if e.timestamp >= datetime.utcnow() - timedelta(hours=1)
                and e.status == AccessStatus.DENIED
            ]
            if len(recent_failures) > 5:
                anomalies.append(
                    {
                        "type": "excessive_failures",
                        "severity": "high",
                        "message": f"User {event.user_id} has {len(recent_failures)} failed attempts in the last hour",
                        "event": event,
                    }
                )

        # 检查敏感数据访问
        if event.sensitive_data and event.status == AccessStatus.SUCCESS:
            # 如果之前没有访问过这个敏感资源
            user_resources = self.pattern.get_user_accessed_resources(
                event.user_id, hours=24
            )
            if event.resource not in user_resources:
                anomalies.append(
                    {
                        "type": "new_sensitive_access",
                        "severity": "medium",
                        "message": f"User {event.user_id} first accessed sensitive resource: {event.resource}",
                        "event": event,
                    }
                )

        # 位置异常检查
        if event.location:
            # 获取用户最近的位置
            recent_accesses = [
                e
                for e in self.pattern.user_patterns[event.user_id]
                if e.location and e.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ]
            if recent_accesses:
                last_location = recent_accesses[-1].location
                if last_location != event.location:
                    # 简单检查：如果是跨洲访问（这里简化处理）
                    if self._is_suspicious_location_change(
                        last_location, event.location
                    ):
                        anomalies.append(
                            {
                                "type": "impossible_travel",
                                "severity": "high",
                                "message": f"User {event.user_id} accessed from {event.location} after {last_location}",
                                "event": event,
                            }
                        )

        # 触发告警
        for anomaly in anomalies:
            self._trigger_alert(anomaly)

        return anomalies

    def _is_suspicious_location_change(self, location1: str, location2: str) -> bool:
        """检查位置变化是否可疑"""
        # 简化实现：假设不同国家代码为可疑
        return location1 != location2

    def _trigger_alert(self, anomaly: Dict[str, Any]):
        """触发告警"""
        self.logger.warning(
            f"Anomaly detected: {anomaly['type']} - {anomaly['message']}"
        )

        # 调用告警回调
        for callback in self.alert_callbacks:
            try:
                callback(anomaly)
            except Exception as e:
                self.logger.error(f"Alert callback failed: {e}")


class AccessTracker:
    """数据访问跟踪器"""

    def __init__(
        self,
        db_path: str = "logs / access_tracking.db",
        enable_anomaly_detection: bool = True,
        anomaly_config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化访问跟踪器

        Args:
            db_path: 数据库路径
            enable_anomaly_detection: 是否启用异常检测
            anomaly_config: 异常检测配置
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

        # 访问模式分析
        self.pattern = AccessPattern()

        # 异常检测
        self.anomaly_config = anomaly_config or {}
        self.anomaly_detector = AnomalyDetector(self.pattern, **self.anomaly_config)

        self.logger = logging.getLogger("hk_quant_system.access_tracking")

    def _init_database(self):
        """初始化SQLite数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS access_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    access_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    source_ip TEXT,
                    user_agent TEXT,
                    data_size INTEGER,
                    sensitive_data INTEGER,
                    location TEXT,
                    duration_ms REAL,
                    details TEXT,
                    anomalies TEXT
                )
            """
            )

            # 创建索引
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_access_timestamp
                ON access_events(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_access_user
                ON access_events(user_id)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_access_resource
                ON access_events(resource)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_access_type
                ON access_events(access_type)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_access_status
                ON access_events(status)
            """
            )

            conn.commit()

    def track_access(self, event: AccessEvent) -> str:
        """
        记录数据访问事件

        Args:
            event: 访问事件对象

        Returns:
            事件ID
        """
        # 生成事件ID
        if not event.event_id:
            event.event_id = self._generate_event_id(event)

        # 保存到数据库
        self._save_to_database(event)

        # 更新访问模式
        self.pattern.add_access(event)

        # 异常检测
        anomalies = self.anomaly_detector.check_event(event)

        return event.event_id

    def _generate_event_id(self, event: AccessEvent) -> str:
        """生成事件ID"""
        content = f"{event.user_id}:{event.resource}:{event.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _save_to_database(self, event: AccessEvent):
        """保存到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO access_events
                    (event_id, timestamp, user_id, resource, access_type, status,
                     source_ip, user_agent, data_size, sensitive_data, location,
                     duration_ms, details, anomalies)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.event_id,
                        event.timestamp.isoformat(),
                        event.user_id,
                        event.resource,
                        event.access_type.value,
                        event.status.value,
                        event.source_ip,
                        event.user_agent,
                        event.data_size,
                        1 if event.sensitive_data else 0,
                        event.location,
                        event.duration_ms,
                        json.dumps(event.details, ensure_ascii=False),
                        "",  # anomalies will be updated separately
                    ),
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save access event: {e}")

    def query_access(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        access_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        查询访问记录

        Args:
            start_time: 开始时间
            end_time: 结束时间
            user_id: 用户ID
            resource: 资源
            access_type: 访问类型
            status: 状态
            limit: 限制数量

        Returns:
            访问记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM access_events WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            if resource:
                query += " AND resource = ?"
                params.append(resource)

            if access_type:
                query += " AND access_type = ?"
                params.append(access_type)

            if status:
                query += " AND status = ?"
                params.append(status)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_user_statistics(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取用户访问统计

        Args:
            user_id: 用户ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息
        """
        accesses = self.query_access(
            user_id=user_id, start_time=start_time, end_time=end_time, limit=1000000
        )

        if not accesses:
            return {}

        stats = {
            "user_id": user_id,
            "total_accesses": len(accesses),
        }

        # 按类型统计
        type_counts = Counter(a["access_type"] for a in accesses)
        stats["by_type"] = dict(type_counts)

        # 按状态统计
        status_counts = Counter(a["status"] for a in accesses)
        stats["by_status"] = dict(status_counts)

        # 访问的资源
        resources = set(a["resource"] for a in accesses)
        stats["unique_resources"] = len(resources)
        stats["resources"] = list(resources)

        # 数据传输量
        data_sizes = [a["data_size"] for a in accesses if a["data_size"]]
        if data_sizes:
            stats["total_data_transferred"] = sum(data_sizes)
            stats["avg_data_per_request"] = statistics.mean(data_sizes)

        # 时间分布
        hours = [datetime.fromisoformat(a["timestamp"]).hour for a in accesses]
        stats["peak_hours"] = sorted(
            Counter(hours).items(), key=lambda x: x[1], reverse=True
        )[:3]

        # 成功率
        success_count = len([a for a in accesses if a["status"] == "success"])
        stats["success_rate"] = (success_count / len(accesses)) * 100

        return stats

    def get_resource_statistics(
        self,
        resource: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取资源访问统计

        Args:
            resource: 资源名称
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息
        """
        accesses = self.query_access(
            resource=resource, start_time=start_time, end_time=end_time, limit=1000000
        )

        if not accesses:
            return {}

        stats = {
            "resource": resource,
            "total_accesses": len(accesses),
        }

        # 用户统计
        users = set(a["user_id"] for a in accesses)
        stats["unique_users"] = len(users)
        stats["users"] = list(users)

        # 按类型统计
        type_counts = Counter(a["access_type"] for a in accesses)
        stats["by_type"] = dict(type_counts)

        # 按状态统计
        status_counts = Counter(a["status"] for a in accesses)
        stats["by_status"] = dict(status_counts)

        # 时间分布
        hours = [datetime.fromisoformat(a["timestamp"]).hour for a in accesses]
        stats["peak_hours"] = sorted(
            Counter(hours).items(), key=lambda x: x[1], reverse=True
        )[:3]

        # 敏感数据访问
        sensitive_accesses = [a for a in accesses if a["sensitive_data"]]
        stats["sensitive_accesses"] = len(sensitive_accesses)
        stats["sensitive_rate"] = (len(sensitive_accesses) / len(accesses)) * 100

        return stats

    def get_system_statistics(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取系统级统计信息

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息
        """
        accesses = self.query_access(
            start_time=start_time, end_time=end_time, limit=1000000
        )

        if not accesses:
            return {}

        stats = {
            "total_accesses": len(accesses),
        }

        # 用户统计
        users = set(a["user_id"] for a in accesses)
        stats["unique_users"] = len(users)

        # 资源统计
        resources = set(a["resource"] for a in accesses)
        stats["unique_resources"] = len(resources)

        # 访问类型分布
        type_counts = Counter(a["access_type"] for a in accesses)
        stats["by_type"] = dict(type_counts)

        # 状态分布
        status_counts = Counter(a["status"] for a in accesses)
        stats["by_status"] = dict(status_counts)

        # 成功率
        success_count = len([a for a in accesses if a["status"] == "success"])
        stats["success_rate"] = (success_count / len(accesses)) * 100

        # 敏感数据访问
        sensitive_accesses = [a for a in accesses if a["sensitive_data"]]
        stats["sensitive_accesses"] = len(sensitive_accesses)
        stats["sensitive_rate"] = (len(sensitive_accesses) / len(accesses)) * 100

        # 时间分布
        hours = [datetime.fromisoformat(a["timestamp"]).hour for a in accesses]
        stats["peak_hours"] = sorted(
            Counter(hours).items(), key=lambda x: x[1], reverse=True
        )[:3]

        # IP统计
        ips = [a["source_ip"] for a in accesses if a["source_ip"]]
        ip_counts = Counter(ips)
        stats["top_ips"] = dict(ip_counts.most_common(10))

        return stats

    def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        检测异常访问

        Args:
            hours: 检测时间范围（小时）

        Returns:
            异常列表
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        accesses = self.query_access(start_time=cutoff, limit=1000000)

        anomalies = []

        for access in accesses:
            # 重新检查异常（这里简化实现）
            # 实际应用中应该使用更复杂的机器学习模型
            pass

        return anomalies

    def cleanup_old_data(self, days: int = 90):
        """
        清理旧访问记录

        Args:
            days: 保留天数
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM access_events WHERE timestamp < ?",
                (cutoff_date.isoformat(),),
            )
            deleted_count = cursor.rowcount
            conn.commit()

        self.logger.info(f"Cleaned up {deleted_count} old access events")


# 便捷函数
def create_access_tracker(**kwargs) -> AccessTracker:
    """创建访问跟踪器"""
    return AccessTracker(**kwargs)
