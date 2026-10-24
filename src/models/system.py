"""
系統管理模型

定義系統配置、審計日誌、數據模式等相關的數據模型。
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Index, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pydantic import BaseModel, Field, validator
import enum

from .unified_base import UnifiedBaseModel, UnifiedSchema

class LogLevel(str, enum.Enum):
    """日誌級別"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ConfigType(str, enum.Enum):
    """配置類型"""
    SYSTEM = "system"
    DATABASE = "database"
    CACHE = "cache"
    API = "api"
    SECURITY = "security"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"

class SystemConfig(UnifiedBaseModel):
    """系統配置模型"""

    __tablename__ = 'system_configs'

    # 配置基本信息
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_name = Column(String(200), nullable=False)
    config_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # 配置值
    config_value = Column(JSONB, nullable=False)
    default_value = Column(JSONB, nullable=True)
    data_type = Column(String(20), nullable=False)  # string, integer, float, boolean, json, array

    # 配置屬性
    is_encrypted = Column(Boolean, default=False, nullable=False)
    is_readonly = Column(Boolean, default=False, nullable=False)
    is_required = Column(Boolean, default=False, nullable=False)
    requires_restart = Column(Boolean, default=False, nullable=False)

    # 配置分類和分組
    category = Column(String(50), nullable=True, index=True)
    group = Column(String(50), nullable=True, index=True)
    sort_order = Column(Integer, default=0, nullable=False)

    # 驗證和約束
    validation_rules = Column(JSONB, nullable=True)  # 驗證規則
    allowed_values = Column(JSONB, nullable=True)  # 允許的值列表
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)

    # 版本控制和環境
    version = Column(String(20), default="1.0", nullable=False)
    environment = Column(String(20), nullable=True)  # dev, staging, prod
    is_active = Column(Boolean, default=True, nullable=False)

    # 配置來源和同步
    source = Column(String(50), default="database", nullable=False)  # database, file, env, remote
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(String(20), default="synced", nullable=False)

    # 複合索引
    __table_args__ = (
        Index('idx_config_type_category', 'config_type', 'category'),
        Index('idx_config_active_env', 'is_active', 'environment'),
    )

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """驗證配置值"""
        if self.validation_rules is None:
            return True, None

        rules = self.validation_rules
        errors = []

        # 類型檢查
        if "type" in rules:
            expected_type = rules["type"]
            if expected_type == "integer" and not isinstance(value, int):
                errors.append("Value must be an integer")
            elif expected_type == "float" and not isinstance(value, (int, float)):
                errors.append("Value must be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append("Value must be a boolean")
            elif expected_type == "string" and not isinstance(value, str):
                errors.append("Value must be a string")
            elif expected_type == "json" and not isinstance(value, (dict, list)):
                errors.append("Value must be a JSON object or array")

        # 範圍檢查
        if "min" in rules and isinstance(value, (int, float)) and value < rules["min"]:
            errors.append(f"Value must be >= {rules['min']}")
        if "max" in rules and isinstance(value, (int, float)) and value > rules["max"]:
            errors.append(f"Value must be <= {rules['max']}")

        # 長度檢查
        if "min_length" in rules and isinstance(value, str) and len(value) < rules["min_length"]:
            errors.append(f"String length must be >= {rules['min_length']}")
        if "max_length" in rules and isinstance(value, str) and len(value) > rules["max_length"]:
            errors.append(f"String length must be <= {rules['max_length']}")

        # 允許值檢查
        if "allowed_values" in rules and value not in rules["allowed_values"]:
            errors.append(f"Value must be one of: {rules['allowed_values']}")

        # 正則表達式檢查
        if "pattern" in rules and isinstance(value, str):
            import re
            if not re.match(rules["pattern"], value):
                errors.append(f"Value does not match required pattern: {rules['pattern']}")

        return len(errors) == 0, "; ".join(errors) if errors else None

class AuditLog(UnifiedBaseModel):
    """審計日誌模型"""

    __tablename__ = 'audit_logs'

    # 操作基本信息
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)

    # 操作詳情
    action_description = Column(Text, nullable=True)
    operation_type = Column(String(50), nullable=False, index=True)  # create, read, update, delete, login, logout

    # 請求信息
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)

    # 變更信息
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    changed_fields = Column(JSONB, nullable=True)  # 變更的字段列表

    # 操作結果
    success = Column(Boolean, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # 風險和安全
    risk_level = Column(String(20), nullable=True, index=True)  # low, medium, high, critical
    security_flag = Column(Boolean, default=False, nullable=False)
    compliance_flag = Column(Boolean, default=False, nullable=False)

    # 系統信息
    service_name = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(200), nullable=True)
    method = Column(String(10), nullable=True)

    # 時間信息
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    correlation_id = Column(String(100), nullable=True, index=True)

    # 附加數據
    metadata = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)

    # 複合索引
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_resource_action', 'resource_type', 'action', 'timestamp'),
        Index('idx_audit_success_timestamp', 'success', 'timestamp'),
        Index('idx_audit_risk_timestamp', 'risk_level', 'timestamp'),
    )

class DataSchema(UnifiedBaseModel):
    """數據模式模型"""

    __tablename__ = 'data_schemas'

    # 模式基本信息
    schema_name = Column(String(100), unique=True, nullable=False, index=True)
    schema_version = Column(String(20), nullable=False)
    schema_type = Column(String(50), nullable=False, index=True)  # database, api, file, event
    description = Column(Text, nullable=True)

    # 模式定義
    schema_definition = Column(JSONB, nullable=False)  # 完整的模式定義
    table_definitions = Column(JSONB, nullable=True)  # 表結構定義
    field_definitions = Column(JSONB, nullable=True)  # 字段定義

    # 關聯和約束
    relationships = Column(JSONB, nullable=True)  # 關聯關係定義
    constraints = Column(JSONB, nullable=True)  # 約束條件
    indexes = Column(JSONB, nullable=True)  # 索引定義

    # 數據質量規則
    validation_rules = Column(JSONB, nullable=True)
    quality_checks = Column(JSONB, nullable=True)
    data_lineage = Column(JSONB, nullable=True)

    # 版本控制
    parent_schema_id = Column(String(36), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    is_deprecated = Column(Boolean, default=False, nullable=False)
    migration_path = Column(JSONB, nullable=True)

    # 兼容性
    backward_compatible = Column(Boolean, default=True, nullable=False)
    forward_compatible = Column(Boolean, default=False, nullable=False)
    breaking_changes = Column(JSONB, nullable=True)

    # 使用和部署
    is_active = Column(Boolean, default=False, nullable=False)
    deployment_status = Column(String(20), nullable=False)  # draft, testing, deployed, retired
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deployed_environments = Column(JSONB, nullable=True)

    # 統計信息
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    data_volume = Column(Integer, nullable=True)  # 預估數據量

    # 複合索引
    __table_args__ = (
        Index('idx_schema_name_version', 'schema_name', 'schema_version'),
        Index('idx_schema_type_active', 'schema_type', 'is_active'),
    )

class SystemHealth(UnifiedBaseModel):
    """系統健康模型"""

    __tablename__ = 'system_health'

    # 健康檢查基本信息
    service_name = Column(String(50), nullable=False, index=True)
    component_name = Column(String(100), nullable=False, index=True)
    check_type = Column(String(50), nullable=False, index=True)  # database, cache, external_api, disk, memory

    # 健康狀態
    status = Column(String(20), nullable=False, index=True)  # healthy, warning, critical, unknown
    health_score = Column(Float, nullable=False)  # 0-100

    # 檢查結果
    response_time_ms = Column(Integer, nullable=True)
    error_rate = Column(Float, nullable=True)
    availability_percent = Column(Float, nullable=True)
    last_check_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # 閾值配置
    warning_threshold = Column(Float, nullable=True)
    critical_threshold = Column(Float, nullable=True)

    # 詳細信息
    check_details = Column(JSONB, nullable=True)
    metrics = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    # 連續狀態
    consecutive_failures = Column(Integer, default=0, nullable=False)
    consecutive_successes = Column(Integer, default=0, nullable=False)
    last_failure_time = Column(DateTime(timezone=True), nullable=True)
    last_recovery_time = Column(DateTime(timezone=True), nullable=True)

    # 複合索引
    __table_args__ = (
        Index('idx_health_service_component', 'service_name', 'component_name'),
        Index('idx_health_status_time', 'status', 'last_check_time'),
    )

# Pydantic Schemas
class SystemConfigBaseSchema(UnifiedSchema):
    """系統配置基礎Schema"""
    config_key: str = Field(..., min_length=1, max_length=100, description="配置鍵")
    config_name: str = Field(..., min_length=1, max_length=200, description="配置名稱")
    config_type: ConfigType = Field(..., description="配置類型")
    description: Optional[str] = None
    config_value: Any = Field(..., description="配置值")
    data_type: str = Field(..., description="數據類型")
    category: Optional[str] = None

class SystemConfigCreateSchema(SystemConfigBaseSchema):
    """創建系統配置Schema"""
    default_value: Optional[Any] = None
    is_encrypted: bool = False
    is_readonly: bool = False
    is_required: bool = False
    requires_restart: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    allowed_values: Optional[List[Any]] = None

class SystemConfigResponseSchema(SystemConfigBaseSchema):
    """系統配置響應Schema"""
    is_encrypted: bool
    is_readonly: bool
    is_required: bool
    requires_restart: bool
    category: Optional[str] = None
    group: Optional[str] = None
    version: str
    environment: Optional[str] = None
    is_active: bool
    source: str
    last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AuditLogBaseSchema(UnifiedSchema):
    """審計日誌基礎Schema"""
    action: str = Field(..., min_length=1, max_length=100, description="操作動作")
    resource_type: str = Field(..., description="資源類型")
    operation_type: str = Field(..., description="操作類型")
    success: bool

class AuditLogResponseSchema(AuditLogBaseSchema):
    """審計日誌響應Schema"""
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
    action_description: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: Optional[int] = None
    risk_level: Optional[str] = None
    security_flag: bool
    compliance_flag: bool
    service_name: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    timestamp: datetime
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class DataSchemaBaseSchema(UnifiedSchema):
    """數據模式基礎Schema"""
    schema_name: str = Field(..., min_length=1, max_length=100, description="模式名稱")
    schema_version: str = Field(..., description="模式版本")
    schema_type: str = Field(..., description="模式類型")
    description: Optional[str] = None
    schema_definition: Dict[str, Any] = Field(..., description="模式定義")

class DataSchemaCreateSchema(DataSchemaBaseSchema):
    """創建數據模式Schema"""
    table_definitions: Optional[Dict[str, Any]] = None
    field_definitions: Optional[Dict[str, Any]] = None
    relationships: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    parent_schema_id: Optional[str] = None
    backward_compatible: bool = True

class DataSchemaResponseSchema(DataSchemaBaseSchema):
    """數據模式響應Schema"""
    table_definitions: Optional[Dict[str, Any]] = None
    field_definitions: Optional[Dict[str, Any]] = None
    relationships: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    parent_schema_id: Optional[str] = None
    is_current: bool
    is_deprecated: bool
    is_active: bool
    deployment_status: str
    deployed_at: Optional[datetime] = None
    usage_count: int
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SystemHealthBaseSchema(UnifiedSchema):
    """系統健康基礎Schema"""
    service_name: str = Field(..., description="服務名稱")
    component_name: str = Field(..., description="組件名稱")
    check_type: str = Field(..., description="檢查類型")
    status: str = Field(..., description="健康狀態")
    health_score: float = Field(..., ge=0, le=100, description="健康分數")

class SystemHealthResponseSchema(SystemHealthBaseSchema):
    """系統健康響應Schema"""
    response_time_ms: Optional[int] = None
    error_rate: Optional[float] = None
    availability_percent: Optional[float] = None
    last_check_time: datetime
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    check_details: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    consecutive_failures: int
    consecutive_successes: int
    last_failure_time: Optional[datetime] = None
    last_recovery_time: Optional[datetime] = None

    class Config:
        from_attributes = True