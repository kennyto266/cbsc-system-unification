"""
隐私与安全配置

此文件包含所有隐私和安全模块的配置选项
"""

from pathlib import Path
from typing import Any, Dict, Optional

# 审计日志配置
AUDIT_CONFIG = {
    "db_path": "logs / privacy / audit.db",
    "log_dir": "logs / privacy / audit",
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "backup_count": 10,
    "compress": True,
}

# 访问跟踪配置
ACCESS_TRACKING_CONFIG = {
    "db_path": "logs / privacy / access_tracking.db",
    "enable_anomaly_detection": True,
    "anomaly_config": {
        "max_requests_per_hour": 100,
        "max_unique_resources": 50,
        "suspicious_ips": set(),  # 可疑IP列表
    },
}

# 合规报告配置
COMPLIANCE_CONFIG = {
    "templates_dir": "templates / compliance",
    "output_dir": "reports / compliance",
    "supported_standards": ["gdpr", "ccpa"],
    "auto_generate": False,  # 是否自动生成报告
    "report_frequency": "monthly",  # 报告频率: daily, weekly, monthly
}

# 安全仪表板配置
DASHBOARD_CONFIG = {
    "host": "0.0.0.0",
    "port": 8005,
    "static_dir": "static / privacy_dashboard",
    "templates_dir": "templates / privacy_dashboard",
}

# 数据脱敏配置
MASKING_CONFIG = {
    "email": {"enabled": True, "mask_char": "*", "reveal_chars": 3},
    "phone": {"enabled": True, "mask_char": "*", "format": "***-***-****"},
    "id_card": {"enabled": True, "mask_char": "*", "reveal_chars": 4},
    "credit_card": {"enabled": True, "mask_char": "*", "format": "****-****-****-****"},
}

# 告警配置
ALERT_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "webhook_url": None,  # 告警webhook URL
    "email_notifications": False,
    "email_recipients": [],
    "severity_thresholds": {"critical": 1, "high": 5, "medium": 10, "low": 20},
}

# 指标配置
METRICS_CONFIG = {
    "collection_interval": 60,  # 指标收集间隔（秒）
    "retention_hours": 24 * 7,  # 指标保留时间（小时）
    "thresholds": {
        "failure_rate": 10.0,  # 失败率阈值
        "unauthorized_rate": 5.0,  # 未授权率阈值
        "sensitive_access_rate": 20.0,  # 敏感数据访问率阈值
    },
}

# 完整的隐私安全配置
PRIVACY_SECURITY_CONFIG = {
    "audit": AUDIT_CONFIG,
    "access_tracking": ACCESS_TRACKING_CONFIG,
    "compliance": COMPLIANCE_CONFIG,
    "dashboard": DASHBOARD_CONFIG,
    "masking": MASKING_CONFIG,
    "alerts": ALERT_CONFIG,
    "metrics": METRICS_CONFIG,
}


def get_config(config_type: Optional[str] = None) -> Dict[str, Any]:
    """
    获取配置

    Args:
        config_type: 配置类型 (audit / access_tracking / compliance / dashboard / all)

    Returns:
        配置字典
    """
    if config_type is None or config_type == "all":
        return PRIVACY_SECURITY_CONFIG
    elif config_type in PRIVACY_SECURITY_CONFIG:
        return PRIVACY_SECURITY_CONFIG[config_type]
    else:
        raise ValueError(f"Unknown config type: {config_type}")


def update_config(config_type: str, **kwargs: Any) -> None:
    """
    更新配置

    Args:
        config_type: 配置类型
        **kwargs: 配置项
    """
    if config_type in PRIVACY_SECURITY_CONFIG:
        PRIVACY_SECURITY_CONFIG[config_type].update(kwargs)
    else:
        raise ValueError(f"Unknown config type: {config_type}")
