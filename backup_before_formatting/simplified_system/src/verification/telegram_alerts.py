#!/usr/bin/env python3
"""
Phase 5: System Integration and Optimization
Telegram警報系統與分級警報機制 - Telegram Alerts System

提供智能化的警報通知和管理功能：
- Telegram Bot集成
- 分級警報機制
- 警報聚合和去重
- 自定義警報模板
- 警報歷史和分析
- 雙向交互支持
"""

import asyncio
import time
import logging
import json
import threading
import hashlib
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from pathlib import Path
import urllib.parse

# Telegram Bot API
import telegram
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# 導入驗證系統組件
from .monitoring_dashboard import AlertRule, AlertManager

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class TelegramConfig:
    """Telegram配置"""
    bot_token: str
    chat_ids: List[str] = field(default_factory=list)
    enabled: bool = True
    alert_levels: List[str] = field(default_factory=lambda: ['critical', 'high', 'medium'])
    cooldown_minutes: int = 5
    max_alerts_per_hour: int = 20
    enable_interactive: bool = True
    enable_acknowledgment: bool = True
    custom_emoji: Dict[str, str] = field(default_factory=dict)

@dataclass
class AlertMessage:
    """警報消息"""
    alert_id: str
    title: str
    message: str
    severity: str
    timestamp: float
    source: str
    metric_name: str
    current_value: float
    threshold: float
    acknowledgment_required: bool = True
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AlertTemplates:
    """警報模板管理器"""

    def __init__(self):
        self.templates = {
            'critical': {
                'title': '🚨 CRITICAL ALERT',
                'emoji': '🚨',
                'color': 'red',
                'template': '''🚨 *CRITICAL ALERT* 🚨

*{title}*

📊 *Metric:* {metric_name}
📈 *Current Value:* {current_value}
⚠️ *Threshold:* {threshold} {operator}
⏰ *Time:* {timestamp}

📝 *Description:* {description}

🔧 *Recommended Action:* {action}

*Acknowledge this alert:* /ack_{alert_id}
'''
            },
            'high': {
                'title': '⚠️ HIGH SEVERITY ALERT',
                'emoji': '⚠️',
                'color': 'orange',
                'template': '''⚠️ *HIGH SEVERITY ALERT* ⚠️

*{title}*

📊 *Metric:* {metric_name}
📈 *Current Value:* {current_value}
⚠️ *Threshold:* {threshold} {operator}
⏰ *Time:* {timestamp}

📝 *Description:* {description}

*Acknowledge this alert:* /ack_{alert_id}
'''
            },
            'medium': {
                'title': '⚡ MEDIUM PRIORITY ALERT',
                'emoji': '⚡',
                'color': 'yellow',
                'template': '''⚡ *MEDIUM PRIORITY ALERT* ⚡

*{title}*

📊 *Metric:* {metric_name}
📈 *Current Value:* {current_value}
⚠️ *Threshold:* {threshold} {operator}
⏰ *Time:* {timestamp}

📝 *Description:* {description}
'''
            },
            'low': {
                'title': 'ℹ️ LOW PRIORITY ALERT',
                'emoji': 'ℹ️',
                'color': 'blue',
                'template': '''ℹ️ *LOW PRIORITY ALERT* ℹ️

*{title}*

📊 *Metric:* {metric_name}
📈 *Current Value:* {current_value}
⚠️ *Threshold:* {threshold} {operator}
⏰ *Time:* {timestamp}

📝 *Description:* {description}
'''
            },
            'resolved': {
                'title': '✅ ALERT RESOLVED',
                'emoji': '✅',
                'color': 'green',
                'template': '''✅ *ALERT RESOLVED* ✅

*{title}*

📊 *Metric:* {metric_name}
✅ *Resolved at:* {resolved_time}
⏰ *Duration:* {duration}
👤 *Acknowledged by:* {acknowledged_by}

*Alert is now back to normal*
'''
            }
        }

        # 自定義建議操作
        self.action_suggestions = {
            'high_response_time': [
                'Check system load and CPU usage',
                'Verify database connectivity',
                'Review recent code deployments',
                'Check network latency'
            ],
            'low_success_rate': [
                'Review error logs',
                'Check data source connectivity',
                'Verify API endpoints availability',
                'Review recent system changes'
            ],
            'low_cache_hit_rate': [
                'Check cache configuration',
                'Review cache TTL settings',
                'Verify cache size limits',
                'Check cache key patterns'
            ],
            'high_cpu_usage': [
                'Identify CPU-intensive processes',
                'Check for memory leaks',
                'Review recent system load',
                'Consider scaling resources'
            ],
            'high_memory_usage': [
                'Check for memory leaks',
                'Review cache memory usage',
                'Identify memory-intensive tasks',
                'Consider garbage collection'
            ],
            'high_error_rate': [
                'Review error logs immediately',
                'Check system dependencies',
                'Verify data integrity',
                'Review recent configuration changes'
            ]
        }

    def get_template(self, severity: str) -> Dict[str, Any]:
        """獲取警報模板"""
        return self.templates.get(severity, self.templates['medium'])

    def format_message(self, alert: AlertMessage, template: Dict[str, Any]) -> str:
        """格式化警報消息"""
        # 獲取建議操作
        suggestions = self.action_suggestions.get(alert.metric_name, ['Investigate the issue', 'Check system logs'])
        action_text = '\n'.join(f'• {suggestion}' for suggestion in suggestions)

        # 格式化模板
        formatted_message = template['template'].format(
            title=alert.title,
            metric_name=alert.metric_name,
            current_value=alert.current_value,
            threshold=alert.threshold,
            operator='>',  # 可以從alert.metadata中獲取
            timestamp=datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            description=alert.message,
            action=action_text,
            alert_id=alert.alert_id,
            resolved_time=datetime.fromtimestamp(alert.resolved_at).strftime('%Y-%m-%d %H:%M:%S') if alert.resolved_at else 'N/A',
            duration=self._calculate_duration(alert),
            acknowledged_by=alert.acknowledged_by or 'N/A'
        )

        return formatted_message

    def _calculate_duration(self, alert: AlertMessage) -> str:
        """計算警報持續時間"""
        if not alert.acknowledged_at:
            return 'N/A'

        duration_seconds = alert.acknowledged_at - alert.timestamp
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)

        if hours > 0:
            return f'{hours}h {minutes}m'
        else:
            return f'{minutes}m'

class AlertAggregator:
    """警報聚合器"""

    def __init__(self, aggregation_window: int = 300):  # 5分鐘窗口
        self.aggregation_window = aggregation_window
        self.pending_alerts = defaultdict(list)
        self.aggregated_alerts = {}
        self.cleanup_interval = 600  # 10分鐘清理一次
        self.last_cleanup = time.time()

    def add_alert(self, alert: AlertMessage) -> Optional[AlertMessage]:
        """添加警報，返回聚合後的警報（如果需要）"""
        current_time = time.time()

        # 清理過期警報
        self._cleanup_expired_alerts(current_time)

        # 創建聚合鍵
        aggregation_key = self._create_aggregation_key(alert)

        # 檢查是否有相似的警報在窗口內
        similar_alerts = self.pending_alerts[aggregation_key]

        if similar_alerts:
            # 更新最新警報信息
            latest_alert = similar_alerts[-1]
            latest_alert.current_value = alert.current_value
            latest_alert.timestamp = alert.timestamp
            latest_alert.metadata.update(alert.metadata)

            # 檢查是否需要發送聚合警報
            if self._should_send_aggregated_alert(similar_alerts):
                return self._create_aggregated_alert(similar_alerts)
        else:
            # 新警報，直接返回
            self.pending_alerts[aggregation_key].append(alert)
            return alert

        return None

    def _cleanup_expired_alerts(self, current_time: float):
        """清理過期警報"""
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        cutoff_time = current_time - self.aggregation_window

        for key in list(self.pending_alerts.keys()):
            alerts = self.pending_alerts[key]
            self.pending_alerts[key] = [alert for alert in alerts if alert.timestamp > cutoff_time]

            if not self.pending_alerts[key]:
                del self.pending_alerts[key]

        self.last_cleanup = current_time

    def _create_aggregation_key(self, alert: AlertMessage) -> str:
        """創建聚合鍵"""
        key_components = [
            alert.source,
            alert.metric_name,
            alert.severity
        ]
        return '|'.join(key_components)

    def _should_send_aggregated_alert(self, alerts: List[AlertMessage]) -> bool:
        """檢查是否應該發送聚合警報"""
        # 如果警報數量超過閾值，發送聚合警報
        return len(alerts) >= 3

    def _create_aggregated_alert(self, alerts: List[AlertMessage]) -> AlertMessage:
        """創建聚合警報"""
        if not alerts:
            raise ValueError("Cannot create aggregated alert from empty list")

        # 使用最新的警報作為基礎
        latest_alert = alerts[-1]

        # 創建聚合警報
        aggregated_alert = AlertMessage(
            alert_id=f"agg_{latest_alert.alert_id}",
            title=f"📊 AGGREGATED: {latest_alert.title}",
            message=f"Multiple similar alerts detected ({len(alerts)} occurrences)\n\nLatest: {latest_alert.message}",
            severity=latest_alert.severity,
            timestamp=latest_alert.timestamp,
            source=latest_alert.source,
            metric_name=latest_alert.metric_name,
            current_value=latest_alert.current_value,
            threshold=latest_alert.threshold,
            acknowledgment_required=True,
            metadata={
                'aggregated_count': len(alerts),
                'first_occurrence': alerts[0].timestamp,
                'occurrences': [alert.timestamp for alert in alerts]
            }
        )

        # 清理待聚合的警報
        aggregation_key = self._create_aggregation_key(latest_alert)
        self.pending_alerts[aggregation_key] = [latest_alert]

        return aggregated_alert

class TelegramAlertBot:
    """Telegram警報機器人"""

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.bot = Bot(token=config.bot_token) if config.bot_token else None
        self.templates = AlertTemplates()
        self.aggregator = AlertAggregator()

        # 警報歷史和統計
        self.alert_history = deque(maxlen=1000)
        self.sent_alerts = defaultdict(list)  # chat_id -> alerts
        self.acknowledgments = {}

        # 頻率限制
        self.rate_limits = defaultdict(list)  # chat_id -> timestamps

        # Bot命令處理器
        self.updater = None
        self.dispatcher = None

        # 自定義回調
        self.alert_callbacks = []

        logger.info(f"TelegramAlertBot initialized - Enabled: {config.enabled}")

    async def initialize(self):
        """初始化機器人"""
        if not self.config.enabled or not self.bot:
            return

        try:
            # 測試Bot連接
            me = await self.bot.get_me()
            logger.info(f"Telegram Bot initialized: @{me.username}")

            # 設置命令處理器
            self.updater = Updater(token=self.config.bot_token)
            self.dispatcher = self.updater.dispatcher

            # 註冊命令處理器
            self.dispatcher.add_handler(CommandHandler("start", self.cmd_start))
            self.dispatcher.add_handler(CommandHandler("status", self.cmd_status))
            self.dispatcher.add_handler(CommandHandler("alerts", self.cmd_alerts))
            self.dispatcher.add_handler(CommandHandler("ack", self.cmd_acknowledge))
            self.dispatcher.add_handler(CommandHandler("help", self.cmd_help))

            # 註冊回調查詢處理器
            self.dispatcher.add_handler(CallbackQueryHandler(self.cmd_callback))

            # 啟動機器人
            self.updater.start_polling()
            logger.info("Telegram Bot polling started")

        except Exception as e:
            logger.error(f"Failed to initialize Telegram Bot: {e}")
            self.config.enabled = False

    async def shutdown(self):
        """關閉機器人"""
        if self.updater:
            self.updater.stop()
            logger.info("Telegram Bot stopped")

    async def send_alert(self, alert: AlertMessage) -> bool:
        """發送警報"""
        if not self.config.enabled or not self.bot:
            return False

        try:
            # 檢查警報級別
            if alert.severity not in self.config.alert_levels:
                return False

            # 檢查頻率限制
            if not self._check_rate_limit():
                logger.warning("Rate limit exceeded for alert sending")
                return False

            # 警報聚合
            aggregated_alert = self.aggregator.add_alert(alert)
            if aggregated_alert is None:
                # 警報被聚合，暫不發送
                return True

            # 使用聚合後的警報
            send_alert = aggregated_alert

            # 格式化消息
            template = self.templates.get_template(send_alert.severity)
            formatted_message = self.templates.format_message(send_alert, template)

            # 創建交互式按鈕
            reply_markup = None
            if self.config.enable_interactive and send_alert.acknowledgment_required:
                keyboard = [
                    [InlineKeyboardButton("✅ Acknowledge", callback_data=f"ack_{send_alert.alert_id}")],
                    [InlineKeyboardButton("📊 Details", callback_data=f"details_{send_alert.alert_id}")],
                    [InlineKeyboardButton("🔕 Mute", callback_data=f"mute_{send_alert.alert_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

            # 發送到所有聊 天
            success_count = 0
            for chat_id in self.config.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=formatted_message,
                        parse_mode='Markdown',
                        reply_markup=reply_markup
                    )
                    success_count += 1

                    # 記錄發送的警報
                    self.sent_alerts[chat_id].append({
                        'alert_id': send_alert.alert_id,
                        'sent_at': time.time(),
                        'severity': send_alert.severity
                    })

                    # 清理舊記錄
                    if len(self.sent_alerts[chat_id]) > 100:
                        self.sent_alerts[chat_id] = self.sent_alerts[chat_id][-50:]

                except Exception as e:
                    logger.error(f"Failed to send alert to chat {chat_id}: {e}")

            # 記錄警報歷史
            self.alert_history.append({
                'alert_id': send_alert.alert_id,
                'sent_at': time.time(),
                'severity': send_alert.severity,
                'success_count': success_count,
                'total_chats': len(self.config.chat_ids)
            })

            logger.info(f"Alert sent to {success_count}/{len(self.config.chat_ids)} chats: {send_alert.alert_id}")
            return success_count > 0

        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False

    async def send_resolution(self, alert: AlertMessage):
        """發送警報解決通知"""
        if not self.config.enabled or not self.bot:
            return

        try:
            # 創建解決消息
            template = self.templates.get_template('resolved')
            resolved_message = self.templates.format_message(alert, template)

            # 發送到所有聊 天
            for chat_id in self.config.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=resolved_message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to send resolution to chat {chat_id}: {e}")

            logger.info(f"Resolution notification sent: {alert.alert_id}")

        except Exception as e:
            logger.error(f"Error sending resolution: {e}")

    def _check_rate_limit(self) -> bool:
        """檢查發送頻率限制"""
        current_time = time.time()
        hour_ago = current_time - 3600

        # 清理過期記錄
        for chat_id in list(self.rate_limits.keys()):
            self.rate_limits[chat_id] = [
                timestamp for timestamp in self.rate_limits[chat_id]
                if timestamp > hour_ago
            ]
            if not self.rate_limits[chat_id]:
                del self.rate_limits[chat_id]

        # 檢查每個聊天的限制
        for chat_id in self.config.chat_ids:
            if len(self.rate_limits[chat_id]) >= self.config.max_alerts_per_hour:
                return False

        # 記錄當前發送
        for chat_id in self.config.chat_ids:
            self.rate_limits[chat_id].append(current_time)

        return True

    # Bot命令處理器
    async def cmd_start(self, update: Update, context):
        """處理 /start 命令"""
        await update.message.reply_text(
            "🤖 *Verification System Alert Bot* 🤖\n\n"
            "I monitor your verification system and send alerts when issues arise.\n\n"
            "*Commands:*\n"
            "/status - System status overview\n"
            "/alerts - Recent alerts summary\n"
            "/ack_<alert_id> - Acknowledge an alert\n"
            "/help - Show this help message",
            parse_mode='Markdown'
        )

    async def cmd_status(self, update: Update, context):
        """處理 /status 命令"""
        try:
            from .monitoring_dashboard import get_system_metrics

            metrics = get_system_metrics()

            status_message = (
                "📊 *System Status Overview* 📊\n\n"
                f"🔍 *Total Verifications:* {metrics.total_verifications}\n"
                f"✅ *Success Rate:* {(metrics.successful_verifications/metrics.total_verifications*100):.1f}%\n"
                f"⏱️ *Avg Response Time:* {metrics.avg_response_time_ms:.1f}ms\n"
                f"💾 *Cache Hit Rate:* {(metrics.cache_hit_rate*100):.1f}%\n"
                f"📈 *Throughput:* {metrics.throughput_per_second:.1f} req/s\n"
                f"❌ *Error Rate:* {(metrics.error_rate*100):.2f}%"
            )

            await update.message.reply_text(status_message, parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text(f"❌ Error getting system status: {e}")

    async def cmd_alerts(self, update: Update, context):
        """處理 /alerts 命令"""
        try:
            recent_alerts = list(self.alert_history)[-10:]  # 最近10個警報

            if not recent_alerts:
                await update.message.reply_text("🎉 *No recent alerts!*", parse_mode='Markdown')
                return

            message = "📋 *Recent Alerts* 📋\n\n"

            for alert in recent_alerts:
                severity_emoji = {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '⚡',
                    'low': 'ℹ️'
                }.get(alert['severity'], '📢')

                time_str = datetime.fromtimestamp(alert['sent_at']).strftime('%H:%M')

                message += f"{severity_emoji} *{alert['severity'].title()}* - {time_str}\n"
                message += f"   📊 {alert['alert_id']}\n"
                message += f"   📈 Sent to {alert['success_count']}/{alert['total_chats']} chats\n\n"

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            await update.message.reply_text(f"❌ Error getting alerts: {e}")

    async def cmd_acknowledge(self, update: Update, context):
        """處理 /ack 命令"""
        if len(context.args) == 0:
            await update.message.reply_text("❌ Please provide an alert ID: /ack_<alert_id>")
            return

        alert_id = context.args[0]
        user = update.effective_user

        # 記錄確認
        self.acknowledgments[alert_id] = {
            'acknowledged_by': user.full_name or user.username,
            'acknowledged_at': time.time(),
            'chat_id': update.message.chat_id
        }

        await update.message.reply_text(
            f"✅ Alert `{alert_id}` acknowledged by {user.full_name or user.username}",
            parse_mode='Markdown'
        )

    async def cmd_help(self, update: Update, context):
        """處理 /help 命令"""
        help_message = (
            "🤖 *Alert Bot Help* 🤖\n\n"
            "*Commands:*\n"
            "/start - Welcome message and introduction\n"
            "/status - Current system performance metrics\n"
            "/alerts - Recent alerts summary (last 10)\n"
            "/ack_<alert_id> - Acknowledge a specific alert\n"
            "/help - Show this help message\n\n"
            "*Alert Severity Levels:*\n"
            "🚨 *Critical* - System-critical issues requiring immediate attention\n"
            "⚠️ *High* - Important issues that should be investigated soon\n"
            "⚡ *Medium* - Moderate issues that should be monitored\n"
            "ℹ️ *Low* - Informational alerts for awareness\n\n"
            "*Interactive Features:*\n"
            "• Click buttons in alert messages for quick actions\n"
            "• Acknowledge alerts to notify team members\n"
            "• View detailed alert information on demand"
        )

        await update.message.reply_text(help_message, parse_mode='Markdown')

    async def cmd_callback(self, update: Update, context):
        """處理回調查詢"""
        query = update.callback_query
        await query.answer()  # 立即回答回調查詢

        data = query.data

        if data.startswith('ack_'):
            alert_id = data[4:]
            user = query.from_user

            # 記錄確認
            self.acknowledgments[alert_id] = {
                'acknowledged_by': user.full_name or user.username,
                'acknowledged_at': time.time(),
                'chat_id': query.message.chat_id
            }

            # 更新消息
            await query.edit_message_text(
                text=f"{query.message.text}\n\n✅ *Acknowledged by* {user.full_name or user.username} *at* {datetime.now().strftime('%H:%M:%S')}",
                parse_mode='Markdown'
            )

        elif data.startswith('details_'):
            alert_id = data[8:]
            # 顯示詳細信息
            details_message = f"📊 *Alert Details*\n\nAlert ID: `{alert_id}`\n\n*More detailed information can be viewed in the monitoring dashboard.*"
            await query.message.reply_text(details_message, parse_mode='Markdown')

        elif data.startswith('mute_'):
            alert_id = data[5:]
            # 靜音警報
            await query.edit_message_text(
                text=f"{query.message.text}\n\n🔕 *Alert muted - You won't receive further notifications about this alert.*"
            )

    def add_alert_callback(self, callback: Callable[[AlertMessage], None]):
        """添加警報回調"""
        self.alert_callbacks.append(callback)

# 全局Telegram警報實例
telegram_alert_bot = None

async def initialize_telegram_alerts(bot_token: str, chat_ids: List[str],
                                   alert_levels: List[str] = None) -> TelegramAlertBot:
    """初始化Telegram警報系統"""
    global telegram_alert_bot

    config = TelegramConfig(
        bot_token=bot_token,
        chat_ids=chat_ids,
        alert_levels=alert_levels or ['critical', 'high', 'medium'],
        enabled=True
    )

    telegram_alert_bot = TelegramAlertBot(config)
    await telegram_alert_bot.initialize()

    logger.info("Telegram alerts system initialized")
    return telegram_alert_bot

async def send_verification_alert(alert_id: str, title: str, message: str, severity: str,
                                metric_name: str, current_value: float, threshold: float) -> bool:
    """發送驗證系統警報"""
    if not telegram_alert_bot:
        logger.warning("Telegram alerts not initialized")
        return False

    alert = AlertMessage(
        alert_id=alert_id,
        title=title,
        message=message,
        severity=severity,
        timestamp=time.time(),
        source="verification_system",
        metric_name=metric_name,
        current_value=current_value,
        threshold=threshold
    )

    return await telegram_alert_bot.send_alert(alert)

async def send_alert_resolution(alert_id: str, title: str):
    """發送警報解決通知"""
    if not telegram_alert_bot:
        return False

    # 查找原始警報
    for alert_data in telegram_alert_bot.alert_history:
        if alert_data['alert_id'] == alert_id:
            # 創建解決警報消息
            alert = AlertMessage(
                alert_id=f"{alert_id}_resolved",
                title=f"RESOLVED: {title}",
                message="Alert has been resolved and is back to normal",
                severity="resolved",
                timestamp=time.time(),
                source="verification_system",
                metric_name="",
                current_value=0,
                threshold=0,
                acknowledgment_required=False,
                resolved_at=time.time()
            )

            return await telegram_alert_bot.send_resolution(alert)

    return False

async def shutdown_telegram_alerts():
    """關閉Telegram警報系統"""
    global telegram_alert_bot

    if telegram_alert_bot:
        await telegram_alert_bot.shutdown()
        telegram_alert_bot = None
        logger.info("Telegram alerts system shutdown")

if __name__ == "__main__":
    async def test_telegram_alerts():
        """測試Telegram警報系統"""
        print("Testing Telegram Alerts System...")

        # 這裡需要真實的bot token和chat_id
        bot_token = "YOUR_BOT_TOKEN_HERE"
        chat_ids = ["YOUR_CHAT_ID_HERE"]

        if bot_token == "YOUR_BOT_TOKEN_HERE":
            print("⚠️  Please set real bot token and chat IDs to test Telegram alerts")
            return

        try:
            # 初始化警報系統
            bot = await initialize_telegram_alerts(bot_token, chat_ids)

            # 測試發送警報
            print("\n1. Testing critical alert...")
            success = await send_verification_alert(
                alert_id="test_critical_001",
                title="Test Critical Alert",
                message="This is a test critical alert",
                severity="critical",
                metric_name="verification.response_time",
                current_value=150.5,
                threshold=100.0
            )
            print(f"Critical alert sent: {success}")

            # 等待一段時間
            await asyncio.sleep(5)

            # 測試發送高級別警報
            print("\n2. Testing high severity alert...")
            success = await send_verification_alert(
                alert_id="test_high_001",
                title="Test High Alert",
                message="This is a test high severity alert",
                severity="high",
                metric_name="verification.success_rate",
                current_value=0.85,
                threshold=0.90
            )
            print(f"High alert sent: {success}")

            # 等待一段時間
            await asyncio.sleep(5)

            # 測試解決通知
            print("\n3. Testing resolution notification...")
            success = await send_alert_resolution("test_critical_001", "Test Critical Alert")
            print(f"Resolution notification sent: {success}")

            # 保持運行一段時間以接收交互
            print("\n4. Bot is running... Send /help to the bot for commands")
            print("Press Ctrl+C to stop")

            try:
                while True:
                    await asyncio.sleep(10)
            except KeyboardInterrupt:
                print("\nShutting down...")

        finally:
            # 關閉警報系統
            await shutdown_telegram_alerts()
            print("Telegram alerts test completed!")

    # 運行測試
    asyncio.run(test_telegram_alerts())