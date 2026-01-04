"""
Alert Manager
告警管理器

提供多級告警機制和多渠道告警通知功能。

Usage:
    ```python
    from src.logging_utils import get_alert_manager, AlertLevel, AlertChannel

    alert_mgr = get_alert_manager(config={
        "smtp": {"host": "smtp.example.com", "port": 587},
        "alert_recipients": {
            "email": ["admin@example.com"]
        }
    })

    # Add alert rule
    alert_mgr.add_rule(AlertRule(
        name="high_response_time",
        condition="$avg_response_time > 1000",
        level=AlertLevel.WARNING,
        duration=300,
        channels=[AlertChannel.EMAIL, AlertChannel.DINGTALK]
    ))
    ```
"""

import asyncio
import time
import smtplib
import json
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AlertLevel(Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertChannel(Enum):
    """告警渠道"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DINGTALK = "dingtalk"
    WECHAT = "wechat"


class AlertStatus(Enum):
    """告警狀態"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass
class AlertRule:
    """告警規則"""
    name: str
    condition: str  # 告警條件表達式
    level: AlertLevel
    duration: int  # 持續時間（秒）
    channels: List[AlertChannel]
    enabled: bool = True
    cooldown: int = 300  # 冷卻時間（秒）
    description: str = ""


@dataclass
class Alert:
    """告警事件"""
    rule_name: str
    level: AlertLevel
    message: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.ACTIVE
    alert_id: str = ""


@dataclass
class NotificationResult:
    """通知結果"""
    channel: AlertChannel
    success: bool
    error: str = ""
    timestamp: float = field(default_factory=time.time)


class AlertManager:
    """
    告警管理器

    提供多級告警機制和多渠道告警通知功能，包括：
    - 告警規則管理
    - 告警觸發和解析
    - 多渠道通知（郵件、短信、Webhook、釘釘、企業微信）
    - 告警降噪和升級

    Attributes:
        config: 告警配置
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_notifications: Dict[str, float] = {}
        self.notification_results: List[NotificationResult] = []

        # Alert handlers
        self.handlers = {
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.SMS: self._send_sms_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert,
            AlertChannel.DINGTALK: self._send_dingtalk_alert,
            AlertChannel.WECHAT: self._send_wechat_alert
        }

    def add_rule(self, rule: AlertRule):
        """
        添加告警規則

        Args:
            rule: 告警規則對象
        """
        self.rules[rule.name] = rule

    def remove_rule(self, rule_name: str):
        """
        移除告警規則

        Args:
            rule_name: 規則名稱
        """
        if rule_name in self.rules:
            del self.rules[rule_name]

    def enable_rule(self, rule_name: str):
        """啟用告警規則"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True

    def disable_rule(self, rule_name: str):
        """禁用告警規則"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False

    async def check_metrics(self, metrics: Dict[str, float]):
        """
        檢查指標並觸發告警

        Args:
            metrics: 指標字典
        """
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue

            try:
                # 評估告警條件
                if self._evaluate_condition(rule.condition, metrics):
                    await self._trigger_alert(rule_name, rule, metrics)
                else:
                    await self._resolve_alert(rule_name)

            except Exception as e:
                # Log error but continue checking other rules
                print(f"Error checking rule {rule_name}: {str(e)}")

    def _evaluate_condition(self, condition: str, metrics: Dict[str, float]) -> bool:
        """
        評估告警條件

        Args:
            condition: 條件表達式
            metrics: 指標字典

        Returns:
            是否觸發告警
        """
        try:
            # 替換指標變量
            for key, value in metrics.items():
                condition = condition.replace(f"${key}", str(value))

            # 安全評估表達式
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "max": max,
                "min": min,
                "round": round,
                "sum": sum
            }

            return eval(condition, allowed_names, {})
        except Exception:
            return False

    async def _trigger_alert(self, rule_name: str, rule: AlertRule, metrics: Dict[str, Any]):
        """
        觸發告警

        Args:
            rule_name: 規則名稱
            rule: 告警規則
            metrics: 當前指標
        """
        current_time = time.time()

        # 檢查冷卻時間
        if rule_name in self.last_notifications:
            if current_time - self.last_notifications[rule_name] < rule.cooldown:
                return

        # 檢查是否已有活躍告警
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            # 更新持續時間
            if current_time - alert.timestamp >= rule.duration:
                await self._send_notifications(alert, rule)
                self.last_notifications[rule_name] = current_time
        else:
            # 創建新告警
            alert = Alert(
                alert_id=f"{rule_name}-{int(current_time)}",
                rule_name=rule_name,
                level=rule.level,
                message=f"告警規則 {rule_name} 被觸發: {rule.description or rule.condition}",
                timestamp=current_time,
                details=metrics.copy()
            )
            self.active_alerts[rule_name] = alert

            # 立即發送緊急告警
            if rule.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
                await self._send_notifications(alert, rule)
                self.last_notifications[rule_name] = current_time

    async def _resolve_alert(self, rule_name: str):
        """
        解決告警

        Args:
            rule_name: 規則名稱
        """
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.RESOLVED
            self.alert_history.append(alert)
            del self.active_alerts[rule_name]

    async def _send_notifications(self, alert: Alert, rule: AlertRule):
        """
        發送告警通知

        Args:
            alert: 告警對象
            rule: 告警規則
        """
        for channel in rule.channels:
            try:
                handler = self.handlers.get(channel)
                if handler:
                    result = await handler(alert)
                    self.notification_results.append(result)
            except Exception as e:
                self.notification_results.append(NotificationResult(
                    channel=channel,
                    success=False,
                    error=str(e)
                ))

    # Notification handlers
    async def _send_email_alert(self, alert: Alert) -> NotificationResult:
        """
        發送郵件告警

        Args:
            alert: 告警對象

        Returns:
            通知結果
        """
        smtp_config = self.config.get("smtp", {})
        recipients = self.config.get("alert_recipients", {}).get("email", [])

        if not recipients or not smtp_config.get("host"):
            return NotificationResult(channel=AlertChannel.EMAIL, success=False, error="No SMTP config")

        subject = f"[{alert.level.value.upper()}] {alert.message}"
        body = self._format_alert_message(alert)

        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get("from_email", "alerts@cbsc.com")
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html', 'utf-8'))

            with smtplib.SMTP(smtp_config["host"], smtp_config.get("port", 587)) as server:
                server.starttls()
                if "username" in smtp_config:
                    server.login(smtp_config["username"], smtp_config.get("password", ""))
                server.send_message(msg)

            return NotificationResult(channel=AlertChannel.EMAIL, success=True)
        except Exception as e:
            return NotificationResult(channel=AlertChannel.EMAIL, success=False, error=str(e))

    async def _send_dingtalk_alert(self, alert: Alert) -> NotificationResult:
        """
        發送釘釘告警

        Args:
            alert: 告警對象

        Returns:
            通知結果
        """
        if not REQUESTS_AVAILABLE:
            return NotificationResult(channel=AlertChannel.DINGTALK, success=False, error="requests not installed")

        webhook_url = self.config.get("dingtalk", {}).get("webhook_url")
        if not webhook_url:
            return NotificationResult(channel=AlertChannel.DINGTALK, success=False, error="No webhook URL")

        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"CBSC系統告警 - {alert.level.value.upper()}",
                "text": self._format_dingtalk_message(alert)
            }
        }

        try:
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            return NotificationResult(channel=AlertChannel.DINGTALK, success=True)
        except Exception as e:
            return NotificationResult(channel=AlertChannel.DINGTALK, success=False, error=str(e))

    async def _send_webhook_alert(self, alert: Alert) -> NotificationResult:
        """
        發送 Webhook 告警

        Args:
            alert: 告警對象

        Returns:
            通知結果
        """
        if not REQUESTS_AVAILABLE:
            return NotificationResult(channel=AlertChannel.WEBHOOK, success=False, error="requests not installed")

        webhook_url = self.config.get("webhook_url")
        if not webhook_url:
            return NotificationResult(channel=AlertChannel.WEBHOOK, success=False, error="No webhook URL")

        payload = {
            "alert_id": alert.alert_id,
            "alert_name": alert.rule_name,
            "level": alert.level.value,
            "message": alert.message,
            "timestamp": alert.timestamp,
            "details": alert.details
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            return NotificationResult(channel=AlertChannel.WEBHOOK, success=True)
        except Exception as e:
            return NotificationResult(channel=AlertChannel.WEBHOOK, success=False, error=str(e))

    async def _send_sms_alert(self, alert: Alert) -> NotificationResult:
        """
        發送短信告警

        Args:
            alert: 告警對象

        Returns:
            通知結果
        """
        # Implement SMS sending logic based on your SMS provider
        return NotificationResult(channel=AlertChannel.SMS, success=False, error="Not implemented")

    async def _send_wechat_alert(self, alert: Alert) -> NotificationResult:
        """
        發送企業微信告警

        Args:
            alert: 告警對象

        Returns:
            通知結果
        """
        # Implement WeChat Work sending logic
        return NotificationResult(channel=AlertChannel.WECHAT, success=False, error="Not implemented")

    # Formatting methods
    def _format_alert_message(self, alert: Alert) -> str:
        """格式化告警消息（HTML）"""
        details_text = json.dumps(alert.details, indent=2, ensure_ascii=False)

        return f"""
        <html>
        <body>
            <h2>CBSC量化交易系統告警</h2>
            <p><strong>告警級別:</strong> {alert.level.value.upper()}</p>
            <p><strong>告警規則:</strong> {alert.rule_name}</p>
            <p><strong>告警消息:</strong> {alert.message}</p>
            <p><strong>發生時間:</strong> {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}</p>
            <h3>詳細信息:</h3>
            <pre>{details_text}</pre>
        </body>
        </html>
        """

    def _format_dingtalk_message(self, alert: Alert) -> str:
        """格式化釘釘消息（Markdown）"""
        details_text = "\n".join([f"- {k}: {v}" for k, v in alert.details.items()])

        return f"""
        ## 🔔 CBSC系統告警

        **告警級別**: {alert.level.value.upper()}

        **告警規則**: {alert.rule_name}

        **告警消息**: {alert.message}

        **發生時間**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert.timestamp))}

        **詳細信息**:
        {details_text}
        """

    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        獲取告警統計信息

        Returns:
            告警統計
        """
        total_alerts = len(self.alert_history)
        active_alerts = len(self.active_alerts)

        level_counts = {}
        for alert in self.alert_history:
            level = alert.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        # Notification success rate
        if self.notification_results:
            successful = sum(1 for r in self.notification_results if r.success)
            success_rate = successful / len(self.notification_results)
        else:
            success_rate = 1.0

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "alert_levels": level_counts,
            "active_rules": len([r for r in self.rules.values() if r.enabled]),
            "notification_success_rate": success_rate,
            "recent_notifications": [
                {
                    "channel": r.channel.value,
                    "success": r.success,
                    "timestamp": r.timestamp
                }
                for r in self.notification_results[-10:]
            ]
        }


# Global singleton
_alert_manager: Optional[AlertManager] = None


def get_alert_manager(config: Dict[str, Any] = None) -> AlertManager:
    """獲取全局告警管理器單例"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(config)
    return _alert_manager


# Predefined alert rules
class AlertRuleBuilder:
    """告警規則構建器"""

    @staticmethod
    def high_response_time() -> AlertRule:
        """高響應時間告警"""
        return AlertRule(
            name="high_response_time",
            condition="$avg_response_time > 1000",
            level=AlertLevel.WARNING,
            duration=300,
            channels=[AlertChannel.EMAIL, AlertChannel.DINGTALK],
            description="API 平均響應時間超過 1 秒"
        )

    @staticmethod
    def high_error_rate() -> AlertRule:
        """高錯誤率告警"""
        return AlertRule(
            name="high_error_rate",
            condition="$error_rate > 0.05",
            level=AlertLevel.CRITICAL,
            duration=60,
            channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.DINGTALK],
            description="錯誤率超過 5%"
        )

    @staticmethod
    def memory_usage_high() -> AlertRule:
        """內存使用率過高告警"""
        return AlertRule(
            name="memory_usage_high",
            condition="$memory_usage > 85",
            level=AlertLevel.WARNING,
            duration=180,
            channels=[AlertChannel.EMAIL, AlertChannel.DINGTALK],
            description="內存使用率超過 85%"
        )

    @staticmethod
    def database_connection_failure() -> AlertRule:
        """數據庫連接失敗告警"""
        return AlertRule(
            name="database_connection_failure",
            condition="$db_connections_active == 0",
            level=AlertLevel.EMERGENCY,
            duration=30,
            channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.DINGTALK],
            description="數據庫連接失敗"
        )

    @staticmethod
    def suspicious_activity() -> AlertRule:
        """可疑活動告警"""
        return AlertRule(
            name="suspicious_activity",
            condition="$suspicious_activity_count > 0",
            level=AlertLevel.CRITICAL,
            duration=0,
            channels=[AlertChannel.EMAIL, AlertChannel.SMS],
            description="檢測到可疑活動"
        )
