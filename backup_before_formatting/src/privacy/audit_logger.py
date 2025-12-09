"""
T105: 审计日志系统

实现结构化审计日志系统，支持：
- 五级日志: ERROR / WARN / INFO / DEBUG / TRACE
- JSON结构化输出
- 敏感数据自动脱敏
- 日志轮转和压缩
- 实时流式写入
"""

import gzip
import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class LogLevel(Enum):
    """日志级别"""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40


class AuditEvent:
    """审计事件数据类"""

    def __init__(
        self,
        event_id: str,
        level: Union[LogLevel, str],
        category: str,
        action: str,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration_ms: Optional[float] = None,
    ):
        self.event_id = event_id
        self.timestamp = datetime.utcnow()
        if isinstance(level, str):
            # 将字符串转换为LogLevel枚举
            level_map = {
                "trace": LogLevel.TRACE,
                "debug": LogLevel.DEBUG,
                "info": LogLevel.INFO,
                "warn": LogLevel.WARN,
                "warning": LogLevel.WARN,
                "error": LogLevel.ERROR,
            }
            self.level = level_map.get(level.lower(), LogLevel.INFO)
        else:
            self.level = level
        self.category = category
        self.action = action
        self.user_id = user_id
        self.source_ip = source_ip
        self.resource = resource
        self.details = details or {}
        self.success = success
        self.duration_ms = duration_ms

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "category": self.category,
            "action": self.action,
            "user_id": self.user_id,
            "source_ip": self.source_ip,
            "resource": self.resource,
            "details": self.details,
            "success": self.success,
            "duration_ms": self.duration_ms,
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class SensitiveDataMasker:
    """敏感数据脱敏器"""

    # 敏感数据模式
    PATTERNS = {
        "email": re.compile(r"\b[A - Za - z0 - 9._%+-]+@[A - Za - z0 - 9.-]+\.[A - Z|a - z]{2,}\b"),
        "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        "id_card": re.compile(r"\b\d{17}[\dX]\b"),
        "credit_card": re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "password": re.compile(r"password\s*[=:]\s*[^\s,}]+", re.IGNORECASE),
        "token": re.compile(r"(token|key|secret)\s*[=:]\s*[^\s,}]+", re.IGNORECASE),
    }

    @classmethod
    def mask_data(cls, data: str) -> str:
        """脱敏数据"""
        if not data:
            return data

        masked = data

        # 脱敏邮箱
        masked = cls.PATTERNS["email"].sub("***@***.***", masked)

        # 脱敏手机号
        masked = cls.PATTERNS["phone"].sub("***-***-****", masked)

        # 脱敏身份证
        masked = cls.PATTERNS["id_card"].sub("***********", masked)

        # 脱敏信用卡
        masked = cls.PATTERNS["credit_card"].sub("****-****-****-****", masked)

        # 脱敏密码
        masked = cls.PATTERNS["password"].sub("password=***", masked)

        # 脱敏令牌
        masked = cls.PATTERNS["token"].sub(r"\1=***", masked)

        return masked

    @classmethod
    def mask_dict(cls, obj: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏字典中的敏感数据"""
        if not isinstance(obj, dict):
            return obj

        masked = {}
        for key, value in obj.items():
            if isinstance(value, str):
                # 检查键名是否敏感
                if any(
                    sensitive in key.lower()
                    for sensitive in ["password", "secret", "key", "token", "auth"]
                ):
                    masked[key] = "***"
                else:
                    masked[key] = cls.mask_data(value)
            elif isinstance(value, dict):
                masked[key] = cls.mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [
                    (
                        cls.mask_dict(item)
                        if isinstance(item, dict)
                        else cls.mask_data(str(item)) if isinstance(item, str) else item
                    )
                    for item in value
                ]
            else:
                masked[key] = value

        return masked


class AuditLogger:
    """审计日志器"""

    def __init__(
        self,
        db_path: str = "logs / audit.db",
        log_dir: str = "logs / audit",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 10,
        compress: bool = True,
    ):
        """
        初始化审计日志器

        Args:
            db_path: SQLite数据库路径
            log_dir: 日志文件目录
            max_file_size: 单个日志文件最大大小
            backup_count: 保留的备份文件数量
            compress: 是否压缩历史日志
        """
        self.db_path = Path(db_path)
        self.log_dir = Path(log_dir)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.compress = compress

        # 创建目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_database()

        # 初始化日志记录器
        self.logger = logging.getLogger("hk_quant_system.audit")
        self.logger.setLevel(logging.DEBUG)

        # 添加自定义处理器
        if not self.logger.handlers:
            self._setup_handlers()

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="audit")

        # 事件队列
        self._lock = threading.Lock()

    def _init_database(self):
        """初始化SQLite数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    user_id TEXT,
                    source_ip TEXT,
                    resource TEXT,
                    details TEXT,
                    success INTEGER,
                    duration_ms REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # 创建索引
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                ON audit_logs(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_category
                ON audit_logs(category)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_user
                ON audit_logs(user_id)
            """
            )

            conn.commit()

    def _setup_handlers(self):
        """设置日志处理器"""
        # JSON文件处理器
        from logging.handlers import RotatingFileHandler

        handler = RotatingFileHandler(
            self.log_dir / "audit.json",
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding="utf - 8",
        )

        handler.setLevel(logging.DEBUG)
        handler.setFormatter(self._get_json_formatter())
        self.logger.addHandler(handler)

    def _get_json_formatter(self):
        """获取JSON格式化器"""

        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }

                # 添加异常信息
                if record.exc_info:
                    log_obj["exception"] = self.formatException(record.exc_info)

                return json.dumps(log_obj, ensure_ascii=False)

        return JsonFormatter()

    def log_event(self, event: AuditEvent) -> str:
        """
        记录审计事件

        Args:
            event: 审计事件对象

        Returns:
            事件ID
        """
        # 生成事件ID
        if not event.event_id:
            event.event_id = self._generate_event_id(event)

        # 脱敏数据
        event.details = SensitiveDataMasker.mask_dict(event.details)

        # 异步保存到数据库
        self.executor.submit(self._save_to_database, event)

        # 记录到日志文件
        self._write_to_log(event)

        return event.event_id

    def _generate_event_id(self, event: AuditEvent) -> str:
        """生成事件ID"""
        content = f"{event.category}:{event.action}:{event.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _save_to_database(self, event: AuditEvent):
        """保存到数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO audit_logs
                    (event_id, timestamp, level, category, action,
                     user_id, source_ip, resource, details, success, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event.event_id,
                        event.timestamp.isoformat(),
                        event.level.name,
                        event.category,
                        event.action,
                        event.user_id,
                        event.source_ip,
                        event.resource,
                        json.dumps(event.details, ensure_ascii=False),
                        1 if event.success else 0,
                        event.duration_ms,
                    ),
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save audit log to database: {e}")

    def _write_to_log(self, event: AuditEvent):
        """写入日志文件"""
        try:
            log_data = event.to_dict()

            # 脱敏
            log_data = SensitiveDataMasker.mask_dict(log_data)

            # 写入JSON日志
            with open(self.log_dir / "audit.json", "a", encoding="utf - 8") as f:
                f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")

    def query_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志

        Args:
            start_time: 开始时间
            end_time: 结束时间
            level: 日志级别
            category: 事件类别
            user_id: 用户ID
            limit: 限制数量

        Returns:
            日志列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            query = "SELECT * FROM audit_logs WHERE 1=1"
            params = []

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            if level:
                query += " AND level = ?"
                params.append(level.upper())

            if category:
                query += " AND category = ?"
                params.append(category)

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取审计统计信息

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # 基础条件
            where_clause = ""
            params = []

            if start_time and end_time:
                where_clause = "WHERE timestamp BETWEEN ? AND ?"
                params = [start_time.isoformat(), end_time.isoformat()]
            elif start_time:
                where_clause = "WHERE timestamp >= ?"
                params = [start_time.isoformat()]
            elif end_time:
                where_clause = "WHERE timestamp <= ?"
                params = [end_time.isoformat()]

            # 统计各种指标
            stats = {}

            # 总事件数
            cursor = conn.execute(
                f"SELECT COUNT(*) as count FROM audit_logs {where_clause}", params
            )
            stats["total_events"] = cursor.fetchone()["count"]

            # 按级别统计
            cursor = conn.execute(
                """
                SELECT level, COUNT(*) as count
                FROM audit_logs {where_clause}
                GROUP BY level
            """,
                params,
            )
            stats["by_level"] = {
                row["level"]: row["count"] for row in cursor.fetchall()
            }

            # 按类别统计
            cursor = conn.execute(
                """
                SELECT category, COUNT(*) as count
                FROM audit_logs {where_clause}
                GROUP BY category
            """,
                params,
            )
            stats["by_category"] = {
                row["category"]: row["count"] for row in cursor.fetchall()
            }

            # 成功率
            cursor = conn.execute(
                """
                SELECT
                    AVG(success) * 100 as success_rate,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count
                FROM audit_logs {where_clause}
            """,
                params,
            )
            result = cursor.fetchone()
            stats["success_rate"] = result["success_rate"] or 0
            stats["failure_count"] = result["failure_count"] or 0

            # 活跃用户数
            where_clause_users = where_clause
            if where_clause_users:
                where_clause_users += " AND user_id IS NOT NULL"
            else:
                where_clause_users = "WHERE user_id IS NOT NULL"
            cursor = conn.execute(
                """
                SELECT COUNT(DISTINCT user_id) as count
                FROM audit_logs {where_clause_users}
            """,
                params,
            )
            stats["active_users"] = cursor.fetchone()["count"]

            return stats

    def cleanup_old_logs(self, days: int = 90):
        """
        清理旧日志

        Args:
            days: 保留天数
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM audit_logs WHERE timestamp < ?", (cutoff_date.isoformat(),)
            )
            deleted_count = cursor.rowcount
            conn.commit()

        self.logger.info(f"Cleaned up {deleted_count} old audit logs")

        # 压缩历史日志
        if self.compress:
            self._compress_old_logs()

    def _compress_old_logs(self):
        """压缩旧日志文件"""
        try:
            log_files = list(self.log_dir.glob("audit.json*"))
            for log_file in log_files:
                if log_file.suffix != ".gz":
                    compressed_path = log_file.with_suffix(log_file.suffix + ".gz")
                    with open(log_file, "rb") as f_in:
                        with gzip.open(compressed_path, "wb") as f_out:
                            f_out.writelines(f_in)
                    log_file.unlink()
        except Exception as e:
            self.logger.error(f"Failed to compress logs: {e}")

    def export_logs(
        self,
        output_path: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = "json",
    ) -> str:
        """
        导出审计日志

        Args:
            output_path: 输出文件路径
            start_time: 开始时间
            end_time: 结束时间
            format: 格式 (json / csv)

        Returns:
            输出文件路径
        """
        logs = self.query_logs(
            start_time=start_time, end_time=end_time, limit=1000000  # 导出所有
        )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "json":
            with open(output_path, "w", encoding="utf - 8") as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        elif format.lower() == "csv":
            import csv

            with open(output_path, "w", newline="", encoding="utf - 8") as f:
                if logs:
                    writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                    writer.writeheader()
                    writer.writerows(logs)

        return str(output_path)

    def close(self):
        """关闭审计日志器"""
        self.executor.shutdown(wait=True)
        for handler in self.logger.handlers:
            handler.close()


# 便捷函数
def create_audit_logger(**kwargs) -> AuditLogger:
    """创建审计日志器"""
    return AuditLogger(**kwargs)


# 装饰器：自动记录函数调用
def audit_function(category: str, action: str):
    """审计函数装饰器"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = AuditLogger()
            event_id = logger.log_event(
                AuditEvent(
                    event_id="",
                    level="INFO",
                    category=category,
                    action=action,
                    details={
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200],
                    },
                )
            )
            try:
                result = func(*args, **kwargs)
                logger.log_event(
                    AuditEvent(
                        event_id="",
                        level="INFO",
                        category=category,
                        action=f"{action}_success",
                        details={"result": str(result)[:200]},
                    )
                )
                return result
            except Exception as e:
                logger.log_event(
                    AuditEvent(
                        event_id="",
                        level="ERROR",
                        category=category,
                        action=f"{action}_error",
                        details={"error": str(e)[:200]},
                        success=False,
                    )
                )
                raise
            finally:
                logger.close()

        return wrapper

    return decorator
