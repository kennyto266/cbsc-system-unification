#!/usr/bin/env python3
"""
智能警報和通知系統
Intelligent Alerting and Notification System

實現智能警報管理、通知渠道集成、警報抑制和升級機制
"""

import time
import json
import logging
import asyncio
import aiohttp
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict, deque
import hashlib
import re

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """警報嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """警報狀態"""
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"
    SUPPRESSED = "suppressed"

class NotificationChannel(Enum):
    """通知渠道"""
    EMAIL = "email"
    TELEGRAM = "telegram"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"

@dataclass
class Alert:
    """警報定義"""
    alert_id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    details: Dict[str, Any]

    # 時間信息
    starts_at: float
    ends_at: Optional[float] = None
    last_sent_at: Optional[float] = None

    # 抑制和升級
    suppressed: bool = False
    suppressed_until: Optional[float] = None
    escalation_level: int = 0

    # 標籤
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)

    # 通知記錄
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AlertRule:
    """警報規則"""
    rule_id: str
    name: str
    description: str

    # 查詢條件
    query: str
    query_type: str  # promql, threshold, pattern

    # 條件
    severity: AlertSeverity
    threshold_value: Optional[float] = None
    comparison_operator: str = "gt"  # gt, lt, eq, ne

    # 時間窗口
    evaluation_interval: int = 60  # 秒
    for_duration: int = 0  # 持續時間(秒)

    # 抑制配置
    group_by: List[str] = field(default_factory=list)
    silence_duration: int = 3600  # 小時

    # 通知配置
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    notification_recipients: List[str] = field(default_factory=list)

    # 升級配置
    escalation_enabled: bool = False
    escalation_intervals: List[int] = field(default_factory=list)
    escalation_channels: List[NotificationChannel] = field(default_factory=list)

    enabled: bool = True
    last_evaluation: Optional[float] = None
    last_triggered: Optional[float] = None

@dataclass
class NotificationTemplate:
    """通知模板"""
    template_id: str
    name: str
    channel: NotificationChannel

    # 模板內容
    subject_template: str = ""
    body_template: str = ""
    webhook_url: str = ""

    # 格式
    format_type: str = "text"  # text, html, markdown

    # 變數映射
    variable_mapping: Dict[str, str] = field(default_factory=dict)

class IntelligentAlertingSystem:
    """智能警報系統"""

    def __init__(self):
        """初始化警報系統"""
        self.active_rules = {}
        self.active_alerts = {}
        self.alert_history = deque(maxlen=10000)
        self.notification_templates = {}

        # 抑制和去重
        self.suppression_rules = {}
        self.alert_fingerprints = set()
        self.recent_alerts = deque(maxlen=1000)

        # 通知配置
        self.notification_config = {
            "email": {
                "smtp_server": "localhost",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_address": "alerts@quantitative-trading.com"
            },
            "telegram": {
                "bot_token": "",
                "chat_id": ""
            },
            "slack": {
                "webhook_url": "",
                "channel": "#alerts"
            },
            "webhook": {
                "timeout": 30,
                "retry_count": 3
            }
        }

        # 運行狀態
        self.running = False
        self.evaluation_thread = None

        # 性能統計
        self.stats = {
            "alerts_generated": 0,
            "notifications_sent": 0,
            "alerts_suppressed": 0,
            "false_positives": 0
        }

        logger.info("Intelligent alerting system initialized")

    def add_alert_rule(self, rule: AlertRule) -> bool:
        """
        添加警報規則

        Args:
            rule: 警報規則

        Returns:
            bool: 是否添加成功
        """
        try:
            # 驗證規則
            self._validate_alert_rule(rule)

            self.active_rules[rule.rule_id] = rule
            logger.info(f"Alert rule added: {rule.name} ({rule.rule_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to add alert rule {rule.rule_id}: {e}")
            return False

    def remove_alert_rule(self, rule_id: str) -> bool:
        """
        移除警報規則

        Args:
            rule_id: 規則ID

        Returns:
            bool: 是否移除成功
        """
        if rule_id in self.active_rules:
            del self.active_rules[rule_id]
            logger.info(f"Alert rule removed: {rule_id}")
            return True
        return False

    def add_notification_template(self, template: NotificationTemplate):
        """
        添加通知模板

        Args:
            template: 通知模板
        """
        self.notification_templates[template.template_id] = template
        logger.info(f"Notification template added: {template.name}")

    def evaluate_rules(self) -> List[Alert]:
        """
        評估所有警報規則

        Returns:
            List[Alert]: 觸發的警報列表
        """
        triggered_alerts = []
        current_time = time.time()

        for rule_id, rule in self.active_rules.items():
            if not rule.enabled:
                continue

            try:
                # 檢查評評估間隔
                if (rule.last_evaluation and
                    current_time - rule.last_evaluation < rule.evaluation_interval):
                    continue

                # 評估規則
                alerts = self._evaluate_rule(rule, current_time)
                triggered_alerts.extend(alerts)

                rule.last_evaluation = current_time

            except Exception as e:
                logger.error(f"Error evaluating rule {rule_id}: {e}")

        return triggered_alerts

    def _evaluate_rule(self, rule: AlertRule, current_time: float) -> List[Alert]:
        """評估單個警報規則"""
        alerts = []

        try:
            if rule.query_type == "promql":
                alerts = self._evaluate_promql_rule(rule, current_time)
            elif rule.query_type == "threshold":
                alerts = self._evaluate_threshold_rule(rule, current_time)
            elif rule.query_type == "pattern":
                alerts = self._evaluate_pattern_rule(rule, current_time)
            else:
                logger.warning(f"Unknown rule query type: {rule.query_type}")

        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")

        return alerts

    def _evaluate_promql_rule(self, rule: AlertRule, current_time: float) -> List[Alert]:
        """評估PromQL規則"""
        # 這裡需要與Prometheus集成
        # 簡化實現，實際應用中需要查詢Prometheus API
        alerts = []

        # 模擬Prometheus查詢結果
        try:
            # 應該實現實際的Prometheus查詢
            # result = self._query_prometheus(rule.query)
            result = self._mock_prometheus_query(rule.query)

            if result:
                for series in result:
                    if self._should_trigger_alert(series, rule):
                        alert = self._create_alert(rule, series, current_time)
                        alerts.append(alert)

        except Exception as e:
            logger.error(f"PromQL query error for rule {rule.rule_id}: {e}")

        return alerts

    def _evaluate_threshold_rule(self, rule: AlertRule, current_time: float) -> List[Alert]:
        """評估閾值規則"""
        alerts = []

        try:
            # 模擬閾值檢查
            current_value = self._get_metric_value(rule.query)

            if self._check_threshold(current_value, rule):
                series_data = {
                    "metric": {"__name__": rule.query.split()[0]},
                    "value": [current_time, current_value]
                }
                alert = self._create_alert(rule, series_data, current_time)
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Threshold rule evaluation error for {rule.rule_id}: {e}")

        return alerts

    def _evaluate_pattern_rule(self, rule: AlertRule, current_time: float) -> List[Alert]:
        """評估模式規則"""
        alerts = []

        try:
            # 模擬模式檢測
            pattern_detected = self._detect_pattern(rule.query)

            if pattern_detected:
                series_data = {
                    "metric": {"__name__": "pattern_detection"},
                    "value": [current_time, 1]
                }
                alert = self._create_alert(rule, series_data, current_time)
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Pattern rule evaluation error for {rule.rule_id}: {e}")

        return alerts

    def _create_alert(self, rule: AlertRule, series_data: Dict[str, Any],
                     current_time: float) -> Alert:
        """創建警報"""
        # 生成警報指紋
        fingerprint = self._generate_alert_fingerprint(rule, series_data)

        # 檢查是否已存在相同警報
        if fingerprint in self.active_alerts:
            existing_alert = self.active_alerts[fingerprint]
            existing_alert.last_sent_at = current_time
            return existing_alert

        # 創建新警報
        alert = Alert(
            alert_id=str(int(current_time)) + "_" + fingerprint[:8],
            name=rule.name,
            severity=rule.severity,
            status=AlertStatus.FIRING,
            message=self._format_alert_message(rule, series_data),
            details={
                "rule_id": rule.rule_id,
                "series": series_data,
                "evaluation_time": current_time
            },
            starts_at=current_time,
            labels=series_data.get("metric", {}),
            annotations=rule.annotations.copy()
        )

        # 添加到活躍警報
        self.active_alerts[fingerprint] = alert
        self.alert_history.append(alert)
        self.stats["alerts_generated"] += 1

        logger.info(f"Alert created: {alert.name} ({alert.alert_id})")
        return alert

    def process_alert(self, alert: Alert) -> bool:
        """
        處理警報

        Args:
            alert: 警報

        Returns:
            bool: 是否處理成功
        """
        try:
            # 檢查抑制規則
            if self._should_suppress_alert(alert):
                alert.suppressed = True
                alert.status = AlertStatus.SUPPRESSED
                self.stats["alerts_suppressed"] += 1
                return True

            # 檢查去重
            if self._is_duplicate_alert(alert):
                return True

            # 發送通知
            rule = self.active_rules.get(alert.details.get("rule_id"))
            if rule:
                self._send_notifications(alert, rule)

                # 檢查升級
                if rule.escalation_enabled:
                    self._check_alert_escalation(alert, rule)

            # 添加到歷史記錄
            self.recent_alerts.append(alert.alert_id)

            return True

        except Exception as e:
            logger.error(f"Error processing alert {alert.alert_id}: {e}")
            return False

    def _send_notifications(self, alert: Alert, rule: AlertRule):
        """發送通知"""
        for channel in rule.notification_channels:
            try:
                success = self._send_notification_to_channel(alert, channel, rule)
                if success:
                    self.stats["notifications_sent"] += 1
                    alert.notifications_sent.append({
                        "channel": channel.value,
                        "timestamp": time.time(),
                        "success": True
                    })
                else:
                    alert.notifications_sent.append({
                        "channel": channel.value,
                        "timestamp": time.time(),
                        "success": False
                    })
            except Exception as e:
                logger.error(f"Error sending notification to {channel.value}: {e}")

    def _send_notification_to_channel(self, alert: Alert, channel: NotificationChannel,
                                    rule: AlertRule) -> bool:
        """發送通知到指定渠道"""
        try:
            if channel == NotificationChannel.EMAIL:
                return self._send_email_notification(alert, rule)
            elif channel == NotificationChannel.TELEGRAM:
                return self._send_telegram_notification(alert, rule)
            elif channel == NotificationChannel.SLACK:
                return self._send_slack_notification(alert, rule)
            elif channel == NotificationChannel.WEBHOOK:
                return self._send_webhook_notification(alert, rule)
            else:
                logger.warning(f"Unsupported notification channel: {channel.value}")
                return False

        except Exception as e:
            logger.error(f"Error sending notification to {channel.value}: {e}")
            return False

    async def _send_email_notification(self, alert: Alert, rule: AlertRule) -> bool:
        """發送郵件通知"""
        try:
            config = self.notification_config["email"]
            template = self._get_notification_template(NotificationChannel.EMAIL)

            # 準備郵件內容
            subject = self._format_template(template.subject_template, alert, rule)
            body = self._format_template(template.body_template, alert, rule)

            # 創建郵件
            msg = MimeMultipart()
            msg['From'] = config["from_address"]
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain' if template.format_type == "text" else 'html'))

            # 發送郵件
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
                if config["username"]:
                    server.starttls()
                    server.login(config["username"], config["password"])

                for recipient in rule.notification_recipients:
                    msg['To'] = recipient
                    server.send_message(msg)
                    del msg['To']

            logger.info(f"Email notification sent for alert {alert.alert_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    async def _send_telegram_notification(self, alert: Alert, rule: AlertRule) -> bool:
        """發送Telegram通知"""
        try:
            config = self.notification_config["telegram"]
            template = self._get_notification_template(NotificationChannel.TELEGRAM)

            # 準備消息內容
            message = self._format_template(template.body_template, alert, rule)

            # 發送Telegram消息
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            payload = {
                "chat_id": config["chat_id"],
                "text": message,
                "parse_mode": "HTML" if template.format_type == "html" else None
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Telegram notification sent for alert {alert.alert_id}")
                        return True
                    else:
                        logger.error(f"Telegram API error: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    def _send_slack_notification(self, alert: Alert, rule: AlertRule) -> bool:
        """發送Slack通知"""
        try:
            config = self.notification_config["slack"]
            template = self._get_notification_template(NotificationChannel.SLACK)

            # 準備Slack消息
            message = self._format_template(template.body_template, alert, rule)

            color_map = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.ERROR: "danger",
                AlertSeverity.CRITICAL: "danger"
            }

            payload = {
                "channel": config["channel"],
                "attachments": [{
                    "color": color_map.get(alert.severity, "warning"),
                    "title": alert.name,
                    "text": message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {"title": "Started", "value": datetime.fromtimestamp(alert.starts_at).strftime('%Y-%m-%d %H:%M:%S'), "short": True}
                    ],
                    "footer": "Quantitative Trading Alerts",
                    "ts": int(alert.starts_at)
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(config["webhook_url"], json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert {alert.alert_id}")
                        return True
                    else:
                        logger.error(f"Slack webhook error: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def _send_webhook_notification(self, alert: Alert, rule: AlertRule) -> bool:
        """發送Webhook通知"""
        try:
            template = self._get_notification_template(NotificationChannel.WEBHOOK)

            # 準備Webhook負載
            payload = {
                "alert_id": alert.alert_id,
                "name": alert.name,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "message": alert.message,
                "starts_at": alert.starts_at,
                "labels": alert.labels,
                "annotations": alert.annotations,
                "details": alert.details
            }

            if template.webhook_url:
                url = template.webhook_url
            else:
                # 使用默認webhook URL
                url = f"http://localhost:8004/webhooks/alerts"

            config = self.notification_config["webhook"]

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config["timeout"])) as session:
                for attempt in range(config["retry_count"]):
                    try:
                        async with session.post(url, json=payload) as response:
                            if response.status == 200:
                                logger.info(f"Webhook notification sent for alert {alert.alert_id}")
                                return True
                            else:
                                logger.warning(f"Webhook attempt {attempt + 1} failed: {response.status}")

                    except Exception as e:
                        logger.warning(f"Webhook attempt {attempt + 1} error: {e}")
                        if attempt < config["retry_count"] - 1:
                            await asyncio.sleep(2 ** attempt)  # 指數退避

            return False

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """
        解決警報

        Args:
            alert_id: 警報ID

        Returns:
            bool: 是否解決成功
        """
        try:
            # 查找警報
            alert = None
            fingerprint = None

            for fp, a in self.active_alerts.items():
                if a.alert_id == alert_id:
                    alert = a
                    fingerprint = fp
                    break

            if not alert:
                logger.warning(f"Alert not found: {alert_id}")
                return False

            # 更新警報狀態
            alert.status = AlertStatus.RESOLVED
            alert.ends_at = time.time()

            # 從活躍警報中移除
            if fingerprint in self.active_alerts:
                del self.active_alerts[fingerprint]

            # 發送解決通知
            rule = self.active_rules.get(alert.details.get("rule_id"))
            if rule:
                resolved_alert = Alert(
                    alert_id=alert.alert_id + "_resolved",
                    name=f"{alert.name} - RESOLVED",
                    severity=AlertSeverity.INFO,
                    status=AlertStatus.RESOLVED,
                    message=f"Alert resolved: {alert.message}",
                    details=alert.details,
                    starts_at=alert.ends_at,
                    labels=alert.labels,
                    annotations={"resolved_at": str(datetime.fromtimestamp(time.time()))}
                )
                self._send_notifications(resolved_alert, rule)

            logger.info(f"Alert resolved: {alert_id}")
            return True

        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False

    def get_alert_summary(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        獲取警報摘要

        Args:
            time_window_hours: 時間窗口(小時)

        Returns:
            Dict[str, Any]: 警報摘要
        """
        cutoff_time = time.time() - (time_window_hours * 3600)

        recent_alerts = [
            alert for alert in self.alert_history
            if alert.starts_at > cutoff_time
        ]

        # 統計警報
        severity_counts = {sev.value: 0 for sev in AlertSeverity}
        status_counts = {st.value: 0 for st in AlertStatus}

        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1
            status_counts[alert.status.value] += 1

        # 計算趨勢
        hourly_counts = defaultdict(int)
        for alert in recent_alerts:
            hour = int(alert.starts_at // 3600)
            hourly_counts[hour] += 1

        return {
            "time_window_hours": time_window_hours,
            "timestamp": time.time(),
            "total_alerts": len(recent_alerts),
            "active_alerts": len(self.active_alerts),
            "severity_distribution": severity_counts,
            "status_distribution": status_counts,
            "hourly_trend": dict(hourly_counts),
            "statistics": self.stats.copy()
        }

    # 輔助方法
    def _validate_alert_rule(self, rule: AlertRule):
        """驗證警報規則"""
        if not rule.name or not rule.query:
            raise ValueError("Rule name and query are required")

        if rule.evaluation_interval <= 0:
            raise ValueError("Evaluation interval must be positive")

        if not rule.notification_channels and not rule.escalation_enabled:
            logger.warning(f"Rule {rule.rule_id} has no notification channels")

    def _generate_alert_fingerprint(self, rule: AlertRule, series_data: Dict[str, Any]) -> str:
        """生成警報指紋"""
        fingerprint_data = {
            "rule_id": rule.rule_id,
            "labels": series_data.get("metric", {}),
            "group_by": rule.group_by
        }

        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()

    def _should_trigger_alert(self, series_data: Dict[str, Any], rule: AlertRule) -> bool:
        """檢查是否應觸發警報"""
        if rule.threshold_value is None:
            return True

        value = float(series_data.get("value", [0, 0])[1])

        if rule.comparison_operator == "gt":
            return value > rule.threshold_value
        elif rule.comparison_operator == "lt":
            return value < rule.threshold_value
        elif rule.comparison_operator == "eq":
            return abs(value - rule.threshold_value) < 0.001
        elif rule.comparison_operator == "ne":
            return abs(value - rule.threshold_value) >= 0.001

        return False

    def _check_threshold(self, value: float, rule: AlertRule) -> bool:
        """檢查閾值"""
        if rule.threshold_value is None:
            return False

        if rule.comparison_operator == "gt":
            return value > rule.threshold_value
        elif rule.comparison_operator == "lt":
            return value < rule.threshold_value
        elif rule.comparison_operator == "eq":
            return abs(value - rule.threshold_value) < 0.001
        elif rule.comparison_operator == "ne":
            return abs(value - rule.threshold_value) >= 0.001

        return False

    def _format_alert_message(self, rule: AlertRule, series_data: Dict[str, Any]) -> str:
        """格式化警報消息"""
        value = series_data.get("value", [0, 0])[1]
        metric_name = series_data.get("metric", {}).get("__name__", "unknown")

        return f"{rule.description}: {metric_name} = {value}"

    def _format_template(self, template_str: str, alert: Alert, rule: AlertRule) -> str:
        """格式化通知模板"""
        variables = {
            "alert_name": alert.name,
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "message": alert.message,
            "starts_at": datetime.fromtimestamp(alert.starts_at).strftime('%Y-%m-%d %H:%M:%S'),
            "rule_name": rule.name,
            "rule_description": rule.description
        }

        # 添加標籤變數
        for key, value in alert.labels.items():
            variables[f"label_{key}"] = str(value)

        # 替換模板變數
        result = template_str
        for var, value in variables.items():
            result = result.replace(f"${{{var}}}", str(value))

        return result

    def _get_notification_template(self, channel: NotificationChannel) -> NotificationTemplate:
        """獲取通知模板"""
        template_id = f"{channel.value}_default"
        return self.notification_templates.get(template_id, self._get_default_template(channel))

    def _get_default_template(self, channel: NotificationChannel) -> NotificationTemplate:
        """獲取默認模板"""
        if channel == NotificationChannel.EMAIL:
            return NotificationTemplate(
                template_id="email_default",
                name="Default Email Template",
                channel=channel,
                subject_template="[${severity}] ${alert_name}",
                body_template="""Alert: ${alert_name}
Severity: ${severity}
Message: ${message}
Started: ${starts_at}

Rule: ${rule_name}
Description: ${rule_description}

Labels:
${labels}
""",
                format_type="text"
            )
        elif channel == NotificationChannel.TELEGRAM:
            return NotificationTemplate(
                template_id="telegram_default",
                name="Default Telegram Template",
                channel=channel,
                body_template="""🚨 <b>${severity.upper()}</b>
<b>${alert_name}</b>

${message}

<b>Started:</b> ${starts_at}
<b>Rule:</b> ${rule_name}""",
                format_type="html"
            )
        else:
            return NotificationTemplate(
                template_id=f"{channel.value}_default",
                name=f"Default {channel.value} Template",
                channel=channel,
                body_template="${alert_name}: ${message} (${severity})",
                format_type="text"
            )

    def _should_suppress_alert(self, alert: Alert) -> bool:
        """檢查是否應抑制警報"""
        # 檢查時間窗口內的相似警報
        cutoff_time = time.time() - 300  # 5分鐘

        for recent_alert in self.recent_alerts:
            if recent_alert == alert.alert_id:
                continue

            # 簡化的抑制邏輯
            if (time.time() - alert.starts_at) < 60:  # 1分鐘內
                return True

        return False

    def _is_duplicate_alert(self, alert: Alert) -> bool:
        """檢查是否重複警報"""
        return alert.alert_id in self.recent_alerts

    def _check_alert_escalation(self, alert: Alert, rule: AlertRule):
        """檢查警報升級"""
        if not rule.escalation_enabled or not rule.escalation_intervals:
            return

        current_time = time.time()
        escalation_duration = current_time - alert.starts_at

        # 檢查是否需要升級
        for i, interval in enumerate(rule.escalation_intervals):
            if escalation_duration > interval and alert.escalation_level <= i:
                alert.escalation_level = i + 1

                # 發送升級通知
                for channel in rule.escalation_channels:
                    self._send_notification_to_channel(alert, channel, rule)

                logger.info(f"Alert escalated to level {alert.escalation_level}: {alert.alert_id}")

    # 模擬方法 (實際實現需要真實的數據源)
    def _mock_prometheus_query(self, query: str) -> List[Dict[str, Any]]:
        """模擬Prometheus查詢"""
        # 簡化實現，實際應用中需要真實的Prometheus查詢
        if "up" in query:
            return [{
                "metric": {"job": "quantitative-data-service", "instance": "localhost:8001"},
                "value": [time.time(), 1]
            }]
        return []

    def _get_metric_value(self, metric_name: str) -> float:
        """獲取指標值"""
        # 簡化實現
        return 0.0

    def _detect_pattern(self, pattern: str) -> bool:
        """檢測模式"""
        # 簡化實現
        return False

    def start_monitoring(self):
        """啟動監控"""
        if self.running:
            return

        self.running = True
        self.evaluation_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.evaluation_thread.start()
        logger.info("Alert monitoring started")

    def stop_monitoring(self):
        """停止監控"""
        self.running = False
        if self.evaluation_thread:
            self.evaluation_thread.join(timeout=5)
        logger.info("Alert monitoring stopped")

    def _monitoring_loop(self):
        """監控循環"""
        while self.running:
            try:
                # 評估規則
                triggered_alerts = self.evaluate_rules()

                # 處理警報
                for alert in triggered_alerts:
                    self.process_alert(alert)

                # 清理已解決的警報
                self._cleanup_resolved_alerts()

                # 等待下次評估
                time.sleep(30)  # 30秒評估間隔

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # 錯誤後短暫等待

    def _cleanup_resolved_alerts(self):
        """清理已解決的警報"""
        current_time = time.time()
        resolved_alerts = []

        for fingerprint, alert in self.active_alerts.items():
            if (alert.status == AlertStatus.RESOLVED and
                current_time - (alert.ends_at or alert.starts_at) > 3600):  # 1小時後清理
                resolved_alerts.append(fingerprint)

        for fingerprint in resolved_alerts:
            del self.active_alerts[fingerprint]

# 全局警報系統實例
alerting_system = IntelligentAlertingSystem()

def get_alerting_system() -> IntelligentAlertingSystem:
    """獲取警報系統實例"""
    return alerting_system

if __name__ == "__main__":
    async def main():
        """測試警報系統功能"""
        alert_system = IntelligentAlertingSystem()

        print("Testing intelligent alerting system...")

        # 添加默認通知模板
        email_template = NotificationTemplate(
            template_id="email_default",
            name="Default Email Template",
            channel=NotificationChannel.EMAIL,
            subject_template="[${severity}] ${alert_name}",
            body_template="${message}\n\nStarted: ${starts_at}"
        )
        alert_system.add_notification_template(email_template)

        # 添加測試規則
        test_rule = AlertRule(
            rule_id="test_high_cpu",
            name="High CPU Usage",
            description="CPU usage is above threshold",
            query="system_cpu_usage_percent",
            query_type="threshold",
            severity=AlertSeverity.WARNING,
            threshold_value=80,
            comparison_operator="gt",
            evaluation_interval=60,
            notification_channels=[NotificationChannel.EMAIL],
            notification_recipients=["admin@example.com"]
        )
        alert_system.add_alert_rule(test_rule)

        # 測試警報評估
        print("\n=== Alert Rule Evaluation ===")
        triggered_alerts = alert_system.evaluate_rules()
        print(f"Triggered alerts: {len(triggered_alerts)}")

        # 模擬處理警報
        for alert in triggered_alerts:
            print(f"Processing alert: {alert.name}")
            # 注意：實際發送通知需要配置SMTP等
            # alert_system.process_alert(alert)

        # 獲取警報摘要
        print("\n=== Alert Summary ===")
        summary = alert_system.get_alert_summary(24)
        print(f"Total alerts: {summary['total_alerts']}")
        print(f"Active alerts: {summary['active_alerts']}")
        print(f"Statistics: {summary['statistics']}")

        print("\nIntelligent alerting system test completed!")

    # 需要運行異步代碼
    import asyncio
    asyncio.run(main())