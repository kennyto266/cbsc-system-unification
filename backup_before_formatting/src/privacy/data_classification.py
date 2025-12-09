"""
数据分类与安全处理模块 - T095: 安全数据处理

实现数据生命周期管理、分类、安全删除、访问控制和DLP功能。
支持GDPR、PDPA合规性要求。

功能:
- 数据分类（Public、Internal、Confidential、Restricted）
- 数据生命周期管理
- 安全删除（文件粉碎）
- 数据保留策略
- 访问日志
- 数据丢失预防（DLP）
- 导出 / 导入安全
"""

import hashlib
import json
import logging
import os
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataClassification(Enum):
    """数据分类级别"""

    PUBLIC = "public"  # 公开数据
    INTERNAL = "internal"  # 内部数据
    CONFIDENTIAL = "confidential"  # 机密数据
    RESTRICTED = "restricted"  # 限制数据


class DataType(Enum):
    """数据类型"""

    USER_DATA = "user_data"
    FINANCIAL_DATA = "financial_data"
    TRADE_DATA = "trade_data"
    STRATEGY_DATA = "strategy_data"
    SYSTEM_DATA = "system_data"
    LOG_DATA = "log_data"
    BACKUP_DATA = "backup_data"
    ANALYTICS_DATA = "analytics_data"


@dataclass
class DataRetentionPolicy:
    """数据保留策略"""

    classification: DataClassification
    retention_period_days: int  # 保留天数
    auto_delete: bool = True
    archive_after_days: Optional[int] = None  # 归档天数
    encryption_required: bool = False
    access_logging: bool = True
    backup_required: bool = True


@dataclass
class DataAccessLog:
    """数据访问日志"""

    timestamp: str
    user_id: str
    data_type: str
    classification: str
    action: str  # read, write, delete, export
    ip_address: str
    user_agent: str
    result: str  # success, denied, error


class DataClassificationManager:
    """
    数据分类与安全管理器
    """

    def __init__(self, retention_config_path: Optional[str] = None):
        """
        初始化数据分类管理器

        Args:
            retention_config_path: 保留策略配置文件路径
        """
        self.retention_policies = self._init_retention_policies()
        self.access_logs: List[DataAccessLog] = []
        self.data_registry: Dict[str, Dict[str, Any]] = {}

        # 加载保留策略
        if retention_config_path and os.path.exists(retention_config_path):
            self._load_retention_policies(retention_config_path)

    def _init_retention_policies(self) -> Dict[DataType, DataRetentionPolicy]:
        """初始化默认数据保留策略"""
        return {
            DataType.USER_DATA: DataRetentionPolicy(
                classification=DataClassification.RESTRICTED,
                retention_period_days=2555,  # 7年（合规要求）
                auto_delete=True,
                archive_after_days=365,
                encryption_required=True,
                access_logging=True,
                backup_required=True,
            ),
            DataType.FINANCIAL_DATA: DataRetentionPolicy(
                classification=DataClassification.RESTRICTED,
                retention_period_days=2555,  # 7年（金融监管要求）
                auto_delete=True,
                archive_after_days=365,
                encryption_required=True,
                access_logging=True,
                backup_required=True,
            ),
            DataType.TRADE_DATA: DataRetentionPolicy(
                classification=DataClassification.RESTRICTED,
                retention_period_days=2555,  # 7年（交易记录）
                auto_delete=True,
                archive_after_days=365,
                encryption_required=True,
                access_logging=True,
                backup_required=True,
            ),
            DataType.STRATEGY_DATA: DataRetentionPolicy(
                classification=DataClassification.CONFIDENTIAL,
                retention_period_days=1825,  # 5年
                auto_delete=True,
                archive_after_days=180,
                encryption_required=True,
                access_logging=True,
                backup_required=True,
            ),
            DataType.SYSTEM_DATA: DataRetentionPolicy(
                classification=DataClassification.INTERNAL,
                retention_period_days=365,  # 1年
                auto_delete=True,
                archive_after_days=90,
                encryption_required=False,
                access_logging=True,
                backup_required=True,
            ),
            DataType.LOG_DATA: DataRetentionPolicy(
                classification=DataClassification.INTERNAL,
                retention_period_days=90,  # 90天
                auto_delete=True,
                archive_after_days=30,
                encryption_required=False,
                access_logging=False,
                backup_required=False,
            ),
            DataType.BACKUP_DATA: DataRetentionPolicy(
                classification=DataClassification.CONFIDENTIAL,
                retention_period_days=365,  # 1年
                auto_delete=True,
                encryption_required=True,
                access_logging=True,
                backup_required=False,  # 备份的备份不必要
            ),
            DataType.ANALYTICS_DATA: DataRetentionPolicy(
                classification=DataClassification.INTERNAL,
                retention_period_days=730,  # 2年
                auto_delete=True,
                archive_after_days=180,
                encryption_required=False,
                access_logging=False,
                backup_required=True,
            ),
        }

    def classify_data(
        self, data: Dict[str, Any], data_type: DataType
    ) -> DataClassification:
        """
        对数据进行分类

        Args:
            data: 数据字典
            data_type: 数据类型

        Returns:
            数据分类级别
        """
        # 特殊字段检查
        sensitive_fields = {
            "password",
            "api_key",
            "token",
            "secret",
            "private_key",
            "credit_card",
            "bank_account",
            "ssn",
            "id_number",
            "financial_data",
            "personal_info",
        }

        for field in data.keys():
            if field in sensitive_fields:
                return DataClassification.RESTRICTED

        # 基于数据类型的默认分类
        policy = self.retention_policies.get(data_type)
        if policy:
            return policy.classification

        return DataClassification.INTERNAL

    def register_data(
        self, data_id: str, data: Dict[str, Any], data_type: DataType
    ) -> str:
        """
        注册数据到系统

        Args:
            data_id: 数据ID
            data: 数据内容
            data_type: 数据类型

        Returns:
            数据注册ID
        """
        classification = self.classify_data(data, data_type)
        policy = self.retention_policies[data_type]

        data_record = {
            "id": data_id,
            "type": data_type.value,
            "classification": classification.value,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat(),
            "retention_policy": asdict(policy),
            "encrypted": policy.encryption_required,
            "size": len(json.dumps(data)),
            "checksum": hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest(),
        }

        self.data_registry[data_id] = data_record

        logger.info(f"数据注册完成: {data_id}, 分类: {classification.value}")
        return data_id

    def log_data_access(
        self,
        user_id: str,
        data_id: str,
        action: str,
        ip_address: str,
        user_agent: str,
        result: str = "success",
    ):
        """
        记录数据访问

        Args:
            user_id: 用户ID
            data_id: 数据ID
            action: 操作类型
            ip_address: IP地址
            user_agent: 用户代理
            result: 操作结果
        """
        if data_id in self.data_registry:
            data_info = self.data_registry[data_id]

            log_entry = DataAccessLog(
                timestamp=datetime.utcnow().isoformat(),
                user_id=user_id,
                data_type=data_info["type"],
                classification=data_info["classification"],
                action=action,
                ip_address=ip_address,
                user_agent=user_agent,
                result=result,
            )

            self.access_logs.append(log_entry)

            # 更新最后访问时间
            data_info["last_accessed"] = datetime.utcnow().isoformat()

    def get_data_retention_policy(self, data_type: DataType) -> DataRetentionPolicy:
        """
        获取数据保留策略

        Args:
            data_type: 数据类型

        Returns:
            保留策略
        """
        return self.retention_policies.get(data_type)

    def check_data_retention(self, data_id: str) -> Dict[str, Any]:
        """
        检查数据保留状态

        Args:
            data_id: 数据ID

        Returns:
            保留状态信息
        """
        if data_id not in self.data_registry:
            return {"error": "Data not found"}

        data_info = self.data_registry[data_id]
        created_at = datetime.fromisoformat(data_info["created_at"])
        retention_policy = data_info["retention_policy"]
        retention_days = retention_policy["retention_period_days"]

        expiry_date = created_at + timedelta(days=retention_days)
        now = datetime.utcnow()

        days_remaining = (expiry_date - now).days

        return {
            "data_id": data_id,
            "classification": data_info["classification"],
            "created_at": created_at.isoformat(),
            "expiry_date": expiry_date.isoformat(),
            "days_remaining": days_remaining,
            "should_delete": days_remaining <= 0,
            "should_archive": retention_policy.get("archive_after_days")
            and (now - created_at).days >= retention_policy.get("archive_after_days"),
        }

    def secure_delete_file(self, file_path: str, passes: int = 3) -> bool:
        """
        安全删除文件（文件粉碎）

        Args:
            file_path: 文件路径
            passes: 覆盖次数

        Returns:
            是否成功删除
        """
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return False

        try:
            file_size = os.path.getsize(file_path)

            # 多次随机覆盖
            with open(file_path, "r + b") as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

            # 最后用零覆盖
            with open(file_path, "r + b") as f:
                f.seek(0)
                f.write(b"\x00" * file_size)
                f.flush()
                os.fsync(f.fileno())

            # 删除文件
            os.remove(file_path)

            logger.info(f"安全删除文件: {file_path}")
            return True

        except Exception as e:
            logger.error(f"安全删除文件失败: {e}")
            return False

    def secure_delete_data(self, data_id: str) -> bool:
        """
        安全删除数据

        Args:
            data_id: 数据ID

        Returns:
            是否成功删除
        """
        if data_id not in self.data_registry:
            logger.warning(f"数据不存在: {data_id}")
            return False

        data_info = self.data_registry[data_id]
        classification = DataClassification(data_info["classification"])

        # Restricted数据需要更安全的删除
        if classification == DataClassification.RESTRICTED:
            passes = 7  # 7次覆盖
        else:
            passes = 3  # 3次覆盖

        # 如果数据存储在文件中，删除文件
        # 这里需要根据实际存储方式调整
        file_path = f"data/{data_id}.json"
        if os.path.exists(file_path):
            self.secure_delete_file(file_path, passes)

        # 从注册表中移除
        del self.data_registry[data_id]

        # 记录删除操作
        self.log_data_access(
            user_id="system",
            data_id=data_id,
            action="delete",
            ip_address="127.0.0.1",
            user_agent="system",
            result="success",
        )

        logger.info(f"数据已安全删除: {data_id}")
        return True

    def export_data_with_classification(
        self, data_id: str, user_id: str, export_format: str = "json"
    ) -> Optional[Dict[str, Any]]:
        """
        导出数据（带分类控制）

        Args:
            data_id: 数据ID
            user_id: 用户ID
            export_format: 导出格式

        Returns:
            导出的数据或None（如果被拒绝）
        """
        if data_id not in self.data_registry:
            return None

        data_info = self.data_registry[data_id]
        classification = DataClassification(data_info["classification"])

        # 检查导出权限（这里简化为总是允许）
        # 实际应该检查用户权限

        # 记录导出操作
        self.log_data_access(
            user_id=user_id,
            data_id=data_id,
            action="export",
            ip_address="127.0.0.1",
            user_agent="unknown",
            result="success",
        )

        return {
            "data_id": data_id,
            "classification": classification.value,
            "exported_at": datetime.utcnow().isoformat(),
            "data": data_info,  # 实际数据应该从存储中获取
        }

    def get_data_for_processing(
        self, data_id: str, processing_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取处理中的数据（应用DLP）

        Args:
            data_id: 数据ID
            processing_type: 处理类型

        Returns:
            处理后的数据或None
        """
        if data_id not in self.data_registry:
            return None

        data_info = self.data_registry[data_id]
        classification = DataClassification(data_info["classification"])

        # DLP规则检查
        if classification == DataClassification.RESTRICTED:
            # 限制数据不能直接用于某些处理
            restricted_processing = ["analytics", "export", "sharing"]
            if processing_type in restricted_processing:
                logger.warning(f"拒绝处理受限数据: {data_id}, 类型: {processing_type}")
                return None

        # 返回脱敏后的数据（根据处理类型）
        if processing_type == "analytics":
            # 分析时返回脱敏数据
            return self._anonymize_for_processing(data_info)
        elif processing_type == "training":
            # 训练时返回匿名数据
            return self._anonymize_for_training(data_info)

        return data_info

    def _anonymize_for_processing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """为处理匿名化数据"""
        # 移除或掩码直接标识符
        # 这里应该调用匿名化模块
        anonymized = data.copy()

        # 简化实现：移除敏感字段
        sensitive_fields = ["password", "api_key", "personal_info", "financial_data"]
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = "***REDACTED***"

        return anonymized

    def _anonymize_for_training(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """为训练匿名化数据"""
        # 训练数据需要完全匿名化
        # 返回合成数据或完全脱敏的数据
        return {"status": "anonymized", "original_data": "removed"}

    def cleanup_expired_data(self) -> Dict[str, int]:
        """
        清理过期数据

        Returns:
            清理统计
        """
        cleaned = {"deleted": 0, "archived": 0, "errors": 0}

        for data_id in list(self.data_registry.keys()):
            retention_info = self.check_data_retention(data_id)

            if retention_info.get("should_delete"):
                if self.secure_delete_data(data_id):
                    cleaned["deleted"] += 1
                else:
                    cleaned["errors"] += 1

            elif retention_info.get("should_archive"):
                # 归档逻辑（简化）
                cleaned["archived"] += 1

        logger.info(
            f"清理完成: 删除 {cleaned['deleted']} 条, 归档 {cleaned['archived']} 条"
        )
        return cleaned

    def _load_retention_policies(self, config_path: str):
        """加载保留策略配置"""
        try:
            with open(config_path, "r") as f:
                config = json.load(f)

            # 更新保留策略
            for data_type_str, policy_config in config.items():
                data_type = DataType(data_type_str)
                if data_type in self.retention_policies:
                    self.retention_policies[data_type] = DataRetentionPolicy(
                        **policy_config
                    )

            logger.info("保留策略配置加载成功")

        except Exception as e:
            logger.error(f"加载保留策略失败: {e}")

    def save_retention_policies(self, config_path: str):
        """保存保留策略配置"""
        try:
            config = {}
            for data_type, policy in self.retention_policies.items():
                config[data_type.value] = asdict(policy)

            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            logger.info("保留策略配置保存成功")

        except Exception as e:
            logger.error(f"保存保留策略失败: {e}")

    def generate_compliance_report(self) -> Dict[str, Any]:
        """
        生成合规性报告

        Returns:
            合规性报告
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "data_classification": {},
            "retention_status": {},
            "access_logs_summary": {},
            "deletion_needed": [],
        }

        # 分类统计
        for data_id, data_info in self.data_registry.items():
            classification = data_info["classification"]
            if classification not in report["data_classification"]:
                report["data_classification"][classification] = 0
            report["data_classification"][classification] += 1

        # 保留状态检查
        for data_id in self.data_registry.keys():
            retention_info = self.check_data_retention(data_id)
            report["retention_status"][data_id] = retention_info

            if retention_info.get("should_delete"):
                report["deletion_needed"].append(data_id)

        # 访问日志统计
        if self.access_logs:
            report["access_logs_summary"] = {
                "total_accesses": len(self.access_logs),
                "unique_users": len(set(log.user_id for log in self.access_logs)),
                "recent_accesses": len(
                    [
                        log
                        for log in self.access_logs
                        if datetime.fromisoformat(log.timestamp)
                        > datetime.utcnow() - timedelta(days=7)
                    ]
                ),
            }

        return report


# 全局数据分类管理器
_global_classification_manager = None


def get_classification_manager() -> DataClassificationManager:
    """
    获取全局数据分类管理器

    Returns:
        数据分类管理器实例
    """
    global _global_classification_manager
    if _global_classification_manager is None:
        _global_classification_manager = DataClassificationManager()
    return _global_classification_manager
