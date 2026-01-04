#!/usr/bin/env python3
"""
Task 9.2: Real-time Data Push - Notification Manager Module
實時數據推送 - 通知管理模塊
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import redis.asyncio as redis
from collections import defaultdict, deque
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .unified_websocket_manager import (
    UnifiedWebSocketManager,
    StreamType,
    MessageType,
    StreamMessage
)

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """通知類型"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class NotificationChannel(str, Enum):
    """通知渠道"""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"

class NotificationPriority(str, Enum):
    """通知優先級"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class NotificationRecipient:
    """通知接收者"""
    user_id: str
    channels: Set[NotificationChannel] = field(default_factory=lambda: {NotificationChannel.WEBSOCKET})
    email: Optional[str] = None
    phone: Optional[str] = None
    webhook_url: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Notification:
    """通知消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NotificationType = NotificationType.INFO
    title: str = ""
    message: str = ""
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    delay_until: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "retry_count": self.retry_count
        }

@dataclass
class NotificationRule:
    """通知規則"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationSender:
    """通知發送器基類"""

    def __init__(self, channel: NotificationChannel, config: Dict[str, Any]):
        self.channel = channel
        self.config = config
        self.is_available = True

    async def send(self,
                  notification: Notification,
                  recipient: NotificationRecipient) -> bool:
        """發送通知"""
        raise NotImplementedError

    async def check_availability(self) -> bool:
        """檢查發送器是否可用"""
        return self.is_available

class WebSocketNotificationSender(NotificationSender):
    """WebSocket通知發送器"""

    def __init__(self, ws_manager: UnifiedWebSocketManager, config: Dict[str, Any]):
        super().__init__(NotificationChannel.WEBSOCKET, config)
        self.ws_manager = ws_manager

    async def send(self,
                  notification: Notification,
                  recipient: NotificationRecipient) -> bool:
        """通過WebSocket發送通知"""
        try:
            # 創建StreamMessage
            message = StreamMessage(
                stream_type=StreamType.SYSTEM_NOTIFICATIONS,
                message_type=MessageType.REALTIME_UPDATE,
                data={
                    "notification": notification.to_dict(),
                    "user_id": recipient.user_id
                }
            )

            # 發送給特定用戶
            sent_count = await self.ws_manager.broadcast_to_stream(
                stream_type=StreamType.SYSTEM_NOTIFICATIONS.value,
                raw_data=message.to_dict()["data"],
                target_users=[recipient.user_id]
            )

            return sent_count > 0

        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {e}")
            return False

class EmailNotificationSender(NotificationSender):
    """郵件通知發送器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(NotificationChannel.EMAIL, config)
        self.smtp_server = config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        self.from_email = config.get("from_email")

    async def send(self,
                  notification: Notification,
                  recipient: NotificationRecipient) -> bool:
        """發送郵件通知"""
        if not recipient.email:
            return False

        try:
            # 創建郵件
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient.email
            msg['Subject'] = f"[{notification.type.value.upper()}] {notification.title}"

            # 郵件內容
            body = f"""
            <html>
                <body>
                    <h2>{notification.title}</h2>
                    <p><strong>類型:</strong> {notification.type.value}</p>
                    <p><strong>優先級:</strong> {notification.priority.value}</p>
                    <p><strong>時間:</strong> {notification.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <hr>
                    <p>{notification.message}</p>
                    {self._format_data(notification.data)}
                </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))

            # 發送郵件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info(f"Email notification sent to {recipient.email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False

    def _format_data(self, data: Dict[str, Any]) -> str:
        """格式化數據為HTML"""
        if not data:
            return ""

        html = "<h3>詳細信息:</h3><ul>"
        for key, value in data.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        return html

class WebhookNotificationSender(NotificationSender):
    """Webhook通知發送器"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(NotificationChannel.WEBHOOK, config)
        self.timeout = config.get("timeout", 10)
        self.headers = config.get("headers", {})

    async def send(self,
                  notification: Notification,
                  recipient: NotificationRecipient) -> bool:
        """發送Webhook通知"""
        webhook_url = recipient.webhook_url or self.config.get("default_url")
        if not webhook_url:
            return False

        try:
            import aiohttp

            payload = {
                "notification": notification.to_dict(),
                "recipient": {
                    "user_id": recipient.user_id,
                    "channels": [c.value for c in recipient.channels]
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status < 400:
                        logger.info(f"Webhook notification sent to {webhook_url}")
                        return True
                    else:
                        logger.error(f"Webhook failed with status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False

class NotificationManager:
    """通知管理器"""

    def __init__(self,
                 ws_manager: UnifiedWebSocketManager,
                 redis_client: Optional[redis.Redis] = None,
                 config: Dict[str, Any] = None):
        """
        初始化通知管理器

        Args:
            ws_manager: WebSocket管理器
            redis_client: Redis客戶端
            config: 配置信息
        """
        self.ws_manager = ws_manager
        self.redis_client = redis_client
        self.config = config or {}

        # 通知發送器
        self.senders: Dict[NotificationChannel, NotificationSender] = {}
        self._initialize_senders()

        # 接收者管理
        self.recipients: Dict[str, NotificationRecipient] = {}

        # 通知規則
        self.rules: Dict[str, NotificationRule] = {}

        # 通知隊列
        self.pending_notifications: deque = deque(maxlen=10000)
        self.retry_queue: deque = deque(maxlen=1000)

        # 統計信息
        self.stats = {
            "total_sent": 0,
            "total_failed": 0,
            "by_channel": defaultdict(int),
            "by_type": defaultdict(int),
            "by_priority": defaultdict(int),
            "last_reset": datetime.now(timezone.utc)
        }

        # 啟動後台任務
        self._background_tasks: Set[asyncio.Task] = set()
        self._start_background_tasks()

    def _initialize_senders(self):
        """初始化通知發送器"""
        # WebSocket發送器
        self.senders[NotificationChannel.WEBSOCKET] = WebSocketNotificationSender(
            self.ws_manager,
            self.config.get("websocket", {})
        )

        # 郵件發送器
        if self.config.get("email"):
            self.senders[NotificationChannel.EMAIL] = EmailNotificationSender(
                self.config["email"]
            )

        # Webhook發送器
        if self.config.get("webhook"):
            self.senders[NotificationChannel.WEBHOOK] = WebhookNotificationSender(
                self.config["webhook"]
            )

    def _start_background_tasks(self):
        """啟動後台任務"""
        # 通知處理任務
        task = asyncio.create_task(self._process_notifications())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # 重試任務
        task = asyncio.create_task(self._retry_failed_notifications())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # 清理任務
        task = asyncio.create_task(self._cleanup_task())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def register_recipient(self, recipient: NotificationRecipient):
        """註冊通知接收者"""
        self.recipients[recipient.user_id] = recipient
        logger.info(f"Registered notification recipient: {recipient.user_id}")

    async def unregister_recipient(self, user_id: str):
        """註銷通知接收者"""
        self.recipients.pop(user_id, None)
        logger.info(f"Unregistered notification recipient: {user_id}")

    async def add_rule(self, rule: NotificationRule):
        """添加通知規則"""
        self.rules[rule.id] = rule
        logger.info(f"Added notification rule: {rule.name}")

    async def remove_rule(self, rule_id: str):
        """移除通知規則"""
        self.rules.pop(rule_id, None)
        logger.info(f"Removed notification rule: {rule_id}")

    async def send_notification(self,
                              notification: Notification,
                              target_users: Optional[List[str]] = None,
                              channels: Optional[List[NotificationChannel]] = None) -> Dict[str, bool]:
        """
        發送通知

        Args:
            notification: 通知內容
            target_users: 目標用戶列表（None表示所有用戶）
            channels: 通知渠道列表（None表示使用接收者配置的渠道）

        Returns:
            Dict[str, bool]: 每個用戶的發送結果
        """
        results = {}

        # 確定目標用戶
        if target_users is None:
            target_users = list(self.recipients.keys())

        # 檢查通知規則
        if not await self._check_rules(notification):
            return results

        # 為每個用戶發送通知
        for user_id in target_users:
            recipient = self.recipients.get(user_id)
            if not recipient:
                continue

            # 確定發送渠道
            send_channels = channels or list(recipient.channels)
            user_result = False

            # 遍歷每個渠道發送
            for channel in send_channels:
                sender = self.senders.get(channel)
                if not sender:
                    logger.warning(f"No sender for channel: {channel}")
                    continue

                # 檢查發送器可用性
                if not await sender.check_availability():
                    logger.warning(f"Sender not available for channel: {channel}")
                    continue

                # 發送通知
                try:
                    success = await sender.send(notification, recipient)
                    if success:
                        user_result = True
                        self._update_stats("sent", channel, notification.type, notification.priority)
                    else:
                        self._update_stats("failed", channel, notification.type, notification.priority)

                        # 添加到重試隊列
                        if notification.retry_count < notification.max_retries:
                            notification.retry_count += 1
                            notification.delay_until = datetime.now(timezone.utc) + timedelta(minutes=2 ** notification.retry_count)
                            self.retry_queue.append(notification)

                except Exception as e:
                    logger.error(f"Error sending notification via {channel}: {e}")
                    self._update_stats("failed", channel, notification.type, notification.priority)

            results[user_id] = user_result

        # 存儲通知記錄
        if self.redis_client:
            await self._store_notification_record(notification, results)

        return results

    async def broadcast_system_notification(self,
                                          title: str,
                                          message: str,
                                          type: NotificationType = NotificationType.INFO,
                                          priority: NotificationPriority = NotificationPriority.NORMAL,
                                          data: Optional[Dict[str, Any]] = None) -> int:
        """
        廣播系統通知

        Args:
            title: 通知標題
            message: 通知內容
            type: 通知類型
            priority: 優先級
            data: 附加數據

        Returns:
            int: 成功發送的用戶數
        """
        notification = Notification(
            type=type,
            title=title,
            message=message,
            priority=priority,
            data=data or {}
        )

        results = await self.send_notification(notification)
        success_count = sum(1 for success in results.values() if success)

        logger.info(f"System notification broadcasted to {success_count} users")
        return success_count

    async def send_strategy_alert(self,
                                strategy_id: str,
                                alert_type: str,
                                message: str,
                                user_id: str,
                                data: Optional[Dict[str, Any]] = None) -> bool:
        """
        發送策略警報

        Args:
            strategy_id: 策略ID
            alert_type: 警報類型
            message: 警報消息
            user_id: 用戶ID
            data: 附加數據

        Returns:
            bool: 發送是否成功
        """
        notification = Notification(
            type=NotificationType.WARNING,
            title=f"策略警報 - {strategy_id}",
            message=message,
            priority=NotificationPriority.HIGH,
            data={
                "strategy_id": strategy_id,
                "alert_type": alert_type,
                **(data or {})
            }
        )

        results = await self.send_notification(notification, [user_id])
        return results.get(user_id, False)

    async def send_risk_alert(self,
                            portfolio_id: str,
                            risk_level: str,
                            message: str,
                            user_id: str,
                            data: Optional[Dict[str, Any]] = None) -> bool:
        """
        發送風險警報

        Args:
            portfolio_id: 投資組合ID
            risk_level: 風險級別
            message: 警報消息
            user_id: 用戶ID
            data: 附加數據

        Returns:
            bool: 發送是否成功
        """
        # 根據風險級別設置通知類型和優先級
        risk_mapping = {
            "low": (NotificationType.INFO, NotificationPriority.LOW),
            "medium": (NotificationType.WARNING, NotificationPriority.NORMAL),
            "high": (NotificationType.WARNING, NotificationPriority.HIGH),
            "critical": (NotificationType.CRITICAL, NotificationPriority.URGENT)
        }

        notif_type, priority = risk_mapping.get(risk_level, (NotificationType.WARNING, NotificationPriority.NORMAL))

        notification = Notification(
            type=notif_type,
            title=f"風險警報 - {portfolio_id}",
            message=message,
            priority=priority,
            data={
                "portfolio_id": portfolio_id,
                "risk_level": risk_level,
                **(data or {})
            }
        )

        results = await self.send_notification(notification, [user_id])
        return results.get(user_id, False)

    async def get_notification_history(self,
                                     user_id: str,
                                     limit: int = 50,
                                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        獲取通知歷史

        Args:
            user_id: 用戶ID
            limit: 返回數量限制
            offset: 偏移量

        Returns:
            List[Dict]: 通知歷史列表
        """
        if not self.redis_client:
            return []

        try:
            key = f"notifications:history:{user_id}"
            notifications = await self.redis_client.lrange(key, offset, offset + limit - 1)

            return [json.loads(notif) for notif in notifications]
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            **self.stats,
            "recipients_count": len(self.recipients),
            "rules_count": len(self.rules),
            "pending_notifications": len(self.pending_notifications),
            "retry_queue_size": len(self.retry_queue),
            "available_channels": [
                {
                    "channel": channel.value,
                    "available": sender.is_available
                }
                for channel, sender in self.senders.items()
            ]
        }

    async def _check_rules(self, notification: Notification) -> bool:
        """檢查通知規則"""
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # 檢查條件
            if self._match_conditions(notification, rule.conditions):
                # 執行動作
                await self._execute_rule_actions(notification, rule.actions)

                # 如果規則阻止了通知，返回False
                if rule.actions.get("block", False):
                    return False

        return True

    def _match_conditions(self, notification: Notification, conditions: Dict[str, Any]) -> bool:
        """匹配通知條件"""
        # 簡單的條件匹配邏輯
        if "type" in conditions and notification.type.value not in conditions["type"]:
            return False

        if "priority" in conditions and notification.priority.value not in conditions["priority"]:
            return False

        if "title_contains" in conditions:
            for keyword in conditions["title_contains"]:
                if keyword.lower() not in notification.title.lower():
                    return False

        return True

    async def _execute_rule_actions(self, notification: Notification, actions: List[Dict[str, Any]]):
        """執行規則動作"""
        for action in actions:
            action_type = action.get("type")

            if action_type == "modify_priority":
                notification.priority = NotificationPriority(action.get("value", notification.priority))

            elif action_type == "add_channels":
                for user_id in self.recipients:
                    for channel in action.get("channels", []):
                        self.recipients[user_id].channels.add(NotificationChannel(channel))

            elif action_type == "send_webhook":
                # 發送額外的webhook通知
                webhook_url = action.get("url")
                if webhook_url:
                    webhook_sender = WebhookNotificationSender({"default_url": webhook_url})
                    # 為所有相關用戶發送webhook
                    for recipient in self.recipients.values():
                        await webhook_sender.send(notification, recipient)

    async def _process_notifications(self):
        """處理待發送通知"""
        while True:
            try:
                if self.pending_notifications:
                    notification = self.pending_notifications.popleft()
                    await self.send_notification(notification)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing notifications: {e}")
                await asyncio.sleep(1)

    async def _retry_failed_notifications(self):
        """重試失敗的通知"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)
                retry_items = []

                # 收集需要重試的通知
                while self.retry_queue:
                    notification = self.retry_queue[0]
                    if notification.delay_until and current_time >= notification.delay_until:
                        retry_items.append(self.retry_queue.popleft())
                    else:
                        break

                # 重試發送
                for notification in retry_items:
                    await self.send_notification(notification)

                await asyncio.sleep(10)  # 10秒檢查一次

            except Exception as e:
                logger.error(f"Error retrying notifications: {e}")
                await asyncio.sleep(30)

    async def _cleanup_task(self):
        """清理任務"""
        while True:
            try:
                current_time = datetime.now(timezone.utc)

                # 清理過期通知
                self.pending_notifications = deque(
                    (n for n in self.pending_notifications
                     if not n.expires_at or n.expires_at > current_time),
                    maxlen=10000
                )

                # 重置統計（每天一次）
                if current_time - self.stats["last_reset"] > timedelta(days=1):
                    self.stats = {
                        "total_sent": 0,
                        "total_failed": 0,
                        "by_channel": defaultdict(int),
                        "by_type": defaultdict(int),
                        "by_priority": defaultdict(int),
                        "last_reset": current_time
                    }

                await asyncio.sleep(3600)  # 1小時清理一次

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)

    def _update_stats(self,
                     status: str,
                     channel: NotificationChannel,
                     notif_type: NotificationType,
                     priority: NotificationPriority):
        """更新統計信息"""
        if status == "sent":
            self.stats["total_sent"] += 1
        else:
            self.stats["total_failed"] += 1

        self.stats["by_channel"][channel.value] += 1
        self.stats["by_type"][notif_type.value] += 1
        self.stats["by_priority"][priority.value] += 1

    async def _store_notification_record(self,
                                        notification: Notification,
                                        results: Dict[str, bool]):
        """存儲通知記錄到Redis"""
        if not self.redis_client:
            return

        try:
            # 存儲到每個用戶的歷史記錄
            for user_id, success in results.items():
                key = f"notifications:history:{user_id}"
                record = {
                    "notification": notification.to_dict(),
                    "success": success,
                    "sent_at": datetime.now(timezone.utc).isoformat()
                }

                # 添加到列表（保持最新的100條）
                await self.redis_client.lpush(key, json.dumps(record))
                await self.redis_client.ltrim(key, 0, 99)
                await self.redis_client.expire(key, 86400 * 30)  # 30天過期

        except Exception as e:
            logger.error(f"Error storing notification record: {e}")

# 創建全局通知管理器實例
notification_manager: Optional[NotificationManager] = None

async def get_notification_manager(ws_manager: UnifiedWebSocketManager,
                                 redis_client: Optional[redis.Redis] = None,
                                 config: Dict[str, Any] = None) -> NotificationManager:
    """獲取或創建通知管理器實例"""
    global notification_manager

    if notification_manager is None:
        notification_manager = NotificationManager(ws_manager, redis_client, config)

    return notification_manager