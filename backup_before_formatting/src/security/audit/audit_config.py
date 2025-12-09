"""
審計日誌配置管理
定義審計日誌系統的各種配置選項
"""

import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AuditConfig(BaseModel):
    """審計日誌配置"""

    # 基本設置
    audit_enabled: bool = Field(default=True, description="是否啟用審計日誌")
    log_level: str = Field(default="INFO", description="日誌級別")

    # 日誌文件設置
    log_directory: str = Field(
        default="/c / Users / Penguin8n / CODEX--/logs / audit", description="日誌目錄"
    )
    log_file_prefix: str = Field(default="audit", description="日誌文件前綴")
    log_rotation_size: int = Field(default=100, description="日誌輪轉大小(MB)")
    log_retention_days: int = Field(default=2555, description="日誌保留天數(7年)")

    # 安全設置
    enable_hash_chain: bool = Field(default=True, description="啟用哈希鏈防篡改")
    enable_encryption: bool = Field(default=True, description="啟用日誌加密")
    encrypt_key: Optional[str] = Field(default=None, description="加密密鑰")

    # 合規設置
    gdpr_compliance: bool = Field(default=True, description="GDPR合規")
    pdpa_compliance: bool = Field(default=True, description="PDPA合規")
    iso27001_compliance: bool = Field(default=True, description="ISO 27001合規")
    hkma_compliance: bool = Field(default=True, description="HKMA合規")

    # 監控設置
    enable_real_time_monitoring: bool = Field(default=True, description="啟用實時監控")
    enable_alerts: bool = Field(default=True, description="啟用告警")
    alert_threshold: int = Field(default=10, description="告警閾值(事件數 / 分鐘)")

    # 敏感數據過濾
    sensitive_fields: List[str] = Field(
        default=[
            "password",
            "passwd",
            "token",
            "secret",
            "key",
            "ssn",
            "credit_card",
            "api_key",
            "private_key",
        ],
        description="敏感字段列表",
    )

    # 需要審計的事件類型
    audited_events: Dict[str, List[str]] = Field(
        default={
            "authentication": [
                "login",
                "logout",
                "failed_login",
                "password_change",
                "mfa_enabled",
                "mfa_disabled",
                "account_locked",
            ],
            "authorization": [
                "role_change",
                "permission_grant",
                "permission_revoke",
                "access_denied",
                "privilege_escalation",
            ],
            "data_access": [
                "read",
                "create",
                "update",
                "delete",
                "export",
                "import",
                "download",
                "upload",
                "bulk_access",
            ],
            "system_events": [
                "startup",
                "shutdown",
                "error",
                "warning",
                "config_change",
                "backup",
                "restore",
                "maintenance",
            ],
            "trading": [
                "order_placed",
                "order_cancelled",
                "trade_executed",
                "position_opened",
                "position_closed",
                "margin_call",
            ],
            "api_calls": ["get", "post", "put", "patch", "delete", "graphql"],
        },
        description="需要審計的事件類型",
    )

    # 數據保留策略
    data_retention_policies: Dict[str, int] = Field(
        default={
            "authentication": 2555,  # 7年
            "authorization": 2555,
            "data_access": 2555,
            "system_events": 1095,  # 3年
            "trading": 2555,
            "api_calls": 365,  # 1年
        },
        description="數據保留策略(天數)",
    )

    class Config:
        env_prefix = "AUDIT_"


# 默認配置實例
default_config = AuditConfig()


def load_config() -> AuditConfig:
    """從環境變量加載配置"""
    return default_config
