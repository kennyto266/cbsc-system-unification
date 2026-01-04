"""
VectorBT Multiprocess WebSocket Notifier
======================================

實時推送VectorBT多進程回測的狀態更新和結果通知

功能：
- 實時任務進度推送
- 結果完成通知
- 錯誤狀態警報
- 系統資源監控
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from .websocket_server import WebSocketManager
from src.backtest.vectorbt_multiprocess_engine import VectorBTMultiprocessEngine

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """通知類型"""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    ENGINE_STATUS = "engine_status"
    SYSTEM_ALERT = "system_alert"
    RESOURCE_WARNING = "resource_warning"


@dataclass
class VectorBTNotification:
    """VectorBT通知消息"""
    notification_id: str
    type: NotificationType
    task_id: Optional[str] = None
    user_id: Optional[int] = None
    timestamp: datetime = None
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = None
    severity: str = "info"  # info, warning, error, success

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['type'] = self.type.value
        return result


class VectorBTMultiprocessNotifier:
    """
    VectorBT多進程WebSocket通知器

    負責監控VectorBT多進程引擎狀態並推送實時通知
    """

    def __init__(self, websocket_manager: WebSocketManager):
        """
        初始化通知器

        Args:
            websocket_manager: WebSocket管理器
        """
        self.websocket_manager = websocket_manager
        self.active_engines: Dict[str, VectorBTMultiprocessEngine] = {}
        self.subscribed_users: Set[int] = set()
        self.notification_history: List[VectorBTNotification] = []

        # 監控配置
        self.monitoring_interval = 2.0  # 秒
        self.max_history_size = 1000
        self.resource_thresholds = {
            'cpu_usage': 90.0,      # CPU使用率警報閾值
            'memory_usage': 85.0,   # 內存使用率警報閾值
            'disk_usage': 90.0,     # 磁盤使用率警報閾值
            'active_tasks': 50      # 活躍任務數量警報閾值
        }

        # 監控任務
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False

        logger.info("VectorBT Multiprocess Notifier initialized")

    async def start_monitoring(self):
        """啟動監控"""
        if self.is_running:
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("VectorBT monitoring started")

    async def stop_monitoring(self):
        """停止監控"""
        if not self.is_running:
            return

        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("VectorBT monitoring stopped")

    def register_engine(self, task_id: str, engine: VectorBTMultiprocessEngine, user_id: int):
        """
        註冊監控引擎

        Args:
            task_id: 任務ID
            engine: VectorBT引擎
            user_id: 用戶ID
        """
        self.active_engines[task_id] = {
            'engine': engine,
            'user_id': user_id,
            'registered_at': datetime.now()
        }

        # 發送任務開始通知
        notification = VectorBTNotification(
            notification_id=f"start_{task_id}",
            type=NotificationType.TASK_STARTED,
            task_id=task_id,
            user_id=user_id,
            title="多進程回測開始",
            message=f"任務 {task_id} 已開始執行",
            severity="info"
        )

        asyncio.create_task(self._broadcast_notification(notification))

    def unregister_engine(self, task_id: str):
        """
        註銷引擎

        Args:
            task_id: 任務ID
        """
        if task_id in self.active_engines:
            del self.active_engines[task_id]
            logger.info(f"Engine {task_id} unregistered from monitoring")

    async def subscribe_user(self, user_id: int):
        """
        訂閱用戶通知

        Args:
            user_id: 用戶ID
        """
        self.subscribed_users.add(user_id)

        # 發送歷史通知（最近10條）
        recent_notifications = self.notification_history[-10:]
        for notification in recent_notifications:
            if notification.user_id == user_id or notification.user_id is None:
                await self._send_notification_to_user(notification, user_id)

        logger.info(f"User {user_id} subscribed to VectorBT notifications")

    async def unsubscribe_user(self, user_id: int):
        """
        取消訂閱用戶通知

        Args:
            user_id: 用戶ID
        """
        self.subscribed_users.discard(user_id)
        logger.info(f"User {user_id} unsubscribed from VectorBT notifications")

    async def _monitoring_loop(self):
        """主監控循環"""
        while self.is_running:
            try:
                # 監控所有活躍引擎
                for task_id, engine_info in list(self.active_engines.items()):
                    engine = engine_info['engine']
                    user_id = engine_info['user_id']

                    try:
                        # 獲取引擎狀態
                        status = await engine.get_engine_status()

                        # 檢查進度更新
                        await self._check_progress_update(task_id, status, user_id)

                        # 檢查資源使用
                        await self._check_resource_usage(task_id, status, user_id)

                        # 檢查錯誤狀態
                        await self._check_error_status(task_id, status, user_id)

                    except Exception as e:
                        logger.warning(f"Error monitoring engine {task_id}: {e}")

                # 檢查系統級別資源
                await self._check_system_resources()

                # 等待下次檢查
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5.0)  # 出錯時等待更長時間

    async def _check_progress_update(self, task_id: str, status: Dict[str, Any], user_id: int):
        """檢查進度更新"""
        tasks_info = status.get('tasks', {})
        total_tasks = tasks_info.get('total', 0)
        completed_tasks = tasks_info.get('completed', 0)
        failed_tasks = tasks_info.get('failed', 0)

        if total_tasks > 0:
            progress = completed_tasks / total_tasks

            # 發送進度更新（每10%發送一次）
            if int(progress * 100) % 10 == 0:
                notification = VectorBTNotification(
                    notification_id=f"progress_{task_id}_{int(progress * 100)}",
                    type=NotificationType.TASK_PROGRESS,
                    task_id=task_id,
                    user_id=user_id,
                    title="任務進度更新",
                    message=f"任務 {task_id} 進度: {progress:.1%} ({completed_tasks}/{total_tasks})",
                    data={
                        'progress': progress,
                        'completed_tasks': completed_tasks,
                        'failed_tasks': failed_tasks,
                        'total_tasks': total_tasks
                    },
                    severity="info"
                )

                await self._broadcast_notification(notification)

    async def _check_resource_usage(self, task_id: str, status: Dict[str, Any], user_id: int):
        """檢查資源使用情況"""
        system_resources = status.get('system_resources', {})

        # 檢查CPU使用率
        cpu_usage = system_resources.get('cpu_usage', 0)
        if cpu_usage > self.resource_thresholds['cpu_usage']:
            notification = VectorBTNotification(
                notification_id=f"cpu_warning_{task_id}",
                type=NotificationType.RESOURCE_WARNING,
                task_id=task_id,
                user_id=user_id,
                title="CPU使用率警告",
                message=f"任務 {task_id} CPU使用率過高: {cpu_usage:.1f}%",
                data={
                    'resource_type': 'cpu',
                    'usage': cpu_usage,
                    'threshold': self.resource_thresholds['cpu_usage']
                },
                severity="warning"
            )

            await self._broadcast_notification(notification)

        # 檢查內存使用率
        memory_usage = system_resources.get('memory_usage', 0)
        if memory_usage > self.resource_thresholds['memory_usage']:
            notification = VectorBTNotification(
                notification_id=f"memory_warning_{task_id}",
                type=NotificationType.RESOURCE_WARNING,
                task_id=task_id,
                user_id=user_id,
                title="內存使用率警告",
                message=f"任務 {task_id} 內存使用率過高: {memory_usage:.1f}%",
                data={
                    'resource_type': 'memory',
                    'usage': memory_usage,
                    'threshold': self.resource_thresholds['memory_usage']
                },
                severity="warning"
            )

            await self._broadcast_notification(notification)

    async def _check_error_status(self, task_id: str, status: Dict[str, Any], user_id: int):
        """檢查錯誤狀態"""
        tasks_info = status.get('tasks', {})
        failed_tasks = tasks_info.get('failed', 0)

        # 如果有失敗任務，發送警報
        if failed_tasks > 0:
            total_tasks = tasks_info.get('total', 0)
            notification = VectorBTNotification(
                notification_id=f"error_{task_id}",
                type=NotificationType.TASK_FAILED,
                task_id=task_id,
                user_id=user_id,
                title="任務執行錯誤",
                message=f"任務 {task_id} 檢測到 {failed_tasks} 個失敗子任務",
                data={
                    'failed_tasks': failed_tasks,
                    'total_tasks': total_tasks
                },
                severity="error"
            )

            await self._broadcast_notification(notification)

    async def _check_system_resources(self):
        """檢查系統級別資源"""
        try:
            import psutil

            # 檢查系統CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.resource_thresholds['cpu_usage']:
                notification = VectorBTNotification(
                    notification_id=f"system_cpu_{datetime.now().timestamp()}",
                    type=NotificationType.SYSTEM_ALERT,
                    title="系統CPU使用率警告",
                    message=f"系統CPU使用率過高: {cpu_percent:.1f}%",
                    data={
                        'resource_type': 'system_cpu',
                        'usage': cpu_percent,
                        'threshold': self.resource_thresholds['cpu_usage']
                    },
                    severity="warning"
                )

                await self._broadcast_notification(notification)

            # 檢查系統內存
            memory = psutil.virtual_memory()
            if memory.percent > self.resource_thresholds['memory_usage']:
                notification = VectorBTNotification(
                    notification_id=f"system_memory_{datetime.now().timestamp()}",
                    type=NotificationType.SYSTEM_ALERT,
                    title="系統內存使用率警告",
                    message=f"系統內存使用率過高: {memory.percent:.1f}%",
                    data={
                        'resource_type': 'system_memory',
                        'usage': memory.percent,
                        'threshold': self.resource_thresholds['memory_usage']
                    },
                    severity="warning"
                )

                await self._broadcast_notification(notification)

            # 檢查磁盤使用
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self.resource_thresholds['disk_usage']:
                notification = VectorBTNotification(
                    notification_id=f"system_disk_{datetime.now().timestamp()}",
                    type=NotificationType.SYSTEM_ALERT,
                    title="系統磁盤使用率警告",
                    message=f"系統磁盤使用率過高: {disk_percent:.1f}%",
                    data={
                        'resource_type': 'system_disk',
                        'usage': disk_percent,
                        'threshold': self.resource_thresholds['disk_usage']
                    },
                    severity="warning"
                )

                await self._broadcast_notification(notification)

        except ImportError:
            logger.warning("psutil not available for system monitoring")
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")

    async def notify_task_completion(self, task_id: str, result: Dict[str, Any], user_id: int):
        """
        通知任務完成

        Args:
            task_id: 任務ID
            result: 任務結果
            user_id: 用戶ID
        """
        notification = VectorBTNotification(
            notification_id=f"completed_{task_id}",
            type=NotificationType.TASK_COMPLETED,
            task_id=task_id,
            user_id=user_id,
            title="多進程回測完成",
            message=f"任務 {task_id} 已成功完成",
            data=result,
            severity="success"
        )

        await self._broadcast_notification(notification)

        # 註銷引擎
        self.unregister_engine(task_id)

    async def notify_task_failure(self, task_id: str, error: str, user_id: int):
        """
        通知任務失敗

        Args:
            task_id: 任務ID
            error: 錯誤信息
            user_id: 用戶ID
        """
        notification = VectorBTNotification(
            notification_id=f"failed_{task_id}",
            type=NotificationType.TASK_FAILED,
            task_id=task_id,
            user_id=user_id,
            title="多進程回測失敗",
            message=f"任務 {task_id} 執行失敗: {error}",
            data={'error': error},
            severity="error"
        )

        await self._broadcast_notification(notification)

        # 註銷引擎
        self.unregister_engine(task_id)

    async def notify_task_cancellation(self, task_id: str, user_id: int):
        """
        通知任務取消

        Args:
            task_id: 任務ID
            user_id: 用戶ID
        """
        notification = VectorBTNotification(
            notification_id=f"cancelled_{task_id}",
            type=NotificationType.TASK_CANCELLED,
            task_id=task_id,
            user_id=user_id,
            title="多進程回測已取消",
            message=f"任務 {task_id} 已被用戶取消",
            severity="info"
        )

        await self._broadcast_notification(notification)

        # 註銷引擎
        self.unregister_engine(task_id)

    async def _broadcast_notification(self, notification: VectorBTNotification):
        """
        廣播通知

        Args:
            notification: 通知消息
        """
        try:
            # 添加到歷史記錄
            self.notification_history.append(notification)
            if len(self.notification_history) > self.max_history_size:
                self.notification_history.pop(0)

            # 轉換為JSON
            message = json.dumps({
                'type': 'vectorbt_notification',
                'data': notification.to_dict()
            })

            # 廣播給訂閱的用戶
            if notification.user_id:
                # 特定用戶通知
                await self.websocket_manager.send_to_user(notification.user_id, message)
            else:
                # 全局通知
                for user_id in self.subscribed_users:
                    await self.websocket_manager.send_to_user(user_id, message)

        except Exception as e:
            logger.error(f"Error broadcasting notification: {e}")

    async def _send_notification_to_user(self, notification: VectorBTNotification, user_id: int):
        """
        發送通知給特定用戶

        Args:
            notification: 通知消息
            user_id: 用戶ID
        """
        try:
            message = json.dumps({
                'type': 'vectorbt_notification',
                'data': notification.to_dict()
            })

            await self.websocket_manager.send_to_user(user_id, message)

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")

    async def get_user_notifications(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        獲取用戶通知歷史

        Args:
            user_id: 用戶ID
            limit: 返回數量限制

        Returns:
            通知列表
        """
        user_notifications = [
            notification.to_dict()
            for notification in self.notification_history
            if notification.user_id == user_id or notification.user_id is None
        ]

        # 按時間倒序排列
        user_notifications.sort(
            key=lambda x: x['timestamp'],
            reverse=True
        )

        return user_notifications[:limit]

    async def clear_user_notifications(self, user_id: int):
        """
        清除用戶通知歷史

        Args:
            user_id: 用戶ID
        """
        self.notification_history = [
            notification for notification in self.notification_history
            if notification.user_id != user_id
        ]

        logger.info(f"Cleared notifications for user {user_id}")

    async def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態

        Returns:
            系統狀態信息
        """
        return {
            'active_engines': len(self.active_engines),
            'subscribed_users': len(self.subscribed_users),
            'notification_history_size': len(self.notification_history),
            'monitoring_active': self.is_running,
            'monitoring_interval': self.monitoring_interval,
            'resource_thresholds': self.resource_thresholds
        }