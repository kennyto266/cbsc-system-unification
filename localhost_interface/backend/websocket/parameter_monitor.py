#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
參數優化WebSocket監控系統
Phase 4: 實時參數優化進度監控和數據廣播
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import websockets
from fastapi import WebSocket, WebSocketDisconnect

from shared.models.schemas import WebSocketMessage, OptimizationProgress, OptimizationResult

logger = logging.getLogger(__name__)

class SubscriptionType(str, Enum):
    """訂閱類型"""
    OPTIMIZATION_PROGRESS = "optimization_progress"
    OPTIMIZATION_RESULTS = "optimization_results"
    PARAMETER_UPDATES = "parameter_updates"
    SYSTEM_PERFORMANCE = "system_performance"
    BEST_PARAMETERS = "best_parameters"

class ParameterMonitor:
    """參數優化WebSocket監控器"""

    def __init__(self):
        # 活躍連接管理
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of request_ids
        self.subscription_types: Dict[str, Set[SubscriptionType]] = {}  # client_id -> set of subscription types

        # 性能統計
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }

        # 緩存系統
        self.progress_cache: Dict[str, OptimizationProgress] = {}
        self.results_cache: Dict[str, List[OptimizationResult]] = {}
        self.best_parameters_cache: Dict[str, Dict[str, Any]] = {}

        # 設置心跳機制
        self.heartbeat_interval = 30  # 30秒
        self.heartbeat_task = None

        logger.info("參數優化監控器初始化完成")

    async def connect(self, websocket: WebSocket, client_id: str):
        """接受新的WebSocket連接"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.client_subscriptions[client_id] = set()
            self.subscription_types[client_id] = set()

            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] += 1

            # 發送歡迎消息
            await self.send_personal_message({
                "type": "welcome",
                "client_id": client_id,
                "server_time": datetime.now().isoformat(),
                "available_subscriptions": [sub_type.value for sub_type in SubscriptionType],
                "message": "連接成功！歡迎使用參數優化監控系統"
            }, client_id)

            logger.info(f"客戶端 {client_id} 已連接，當前活躍連接: {len(self.active_connections)}")

            # 啟動心跳機制（如果尚未啟動）
            if self.heartbeat_task is None:
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        except Exception as e:
            logger.error(f"接受WebSocket連接失敗: {e}")
            raise

    async def disconnect(self, client_id: str):
        """斷開客戶端連接"""
        try:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

            if client_id in self.client_subscriptions:
                del self.client_subscriptions[client_id]

            if client_id in self.subscription_types:
                del self.subscription_types[client_id]

            self.connection_stats["active_connections"] -= 1

            logger.info(f"客戶端 {client_id} 已斷開連接，剩餘活躍連接: {len(self.active_connections)}")

        except Exception as e:
            logger.error(f"斷開客戶端連接失敗: {e}")

    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """發送個人消息給特定客戶端"""
        try:
            if client_id in self.active_connections:
                websocket = self.active_connections[client_id]

                # 添加時間戳
                message["timestamp"] = datetime.now().isoformat()
                message["client_id"] = client_id

                await websocket.send_text(json.dumps(message, ensure_ascii=False, default=str))
                self.connection_stats["messages_sent"] += 1

                logger.debug(f"發送個人消息給 {client_id}: {message.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"發送個人消息失敗 {client_id}: {e}")
            self.connection_stats["errors"] += 1

    async def broadcast_message(self, message: Dict[str, Any], subscription_type: SubscriptionType):
        """廣播消息給所有訂閱該類型的客戶端"""
        try:
            message["broadcast_type"] = subscription_type.value
            message["timestamp"] = datetime.now().isoformat()

            disconnected_clients = []

            for client_id, websocket in self.active_connections.items():
                try:
                    # 檢查客戶端是否訂閱了此類型
                    if client_id in self.subscription_types and subscription_type in self.subscription_types[client_id]:
                        await websocket.send_text(json.dumps(message, ensure_ascii=False, default=str))
                        self.connection_stats["messages_sent"] += 1

                except Exception as e:
                    logger.warning(f"廣播消息失敗 {client_id}: {e}")
                    disconnected_clients.append(client_id)
                    self.connection_stats["errors"] += 1

            # 清理斷開的連接
            for client_id in disconnected_clients:
                await self.disconnect(client_id)

            logger.debug(f"廣播 {subscription_type.value} 消息給 {len(self.active_connections) - len(disconnected_clients)} 個客戶端")

        except Exception as e:
            logger.error(f"廣播消息失敗: {e}")

    async def handle_client_message(self, client_id: str, message_data: Dict[str, Any]):
        """處理客戶端消息"""
        try:
            self.connection_stats["messages_received"] += 1

            message_type = message_data.get("type")
            data = message_data.get("data", {})

            if message_type == "subscribe":
                await self._handle_subscription(client_id, data)
            elif message_type == "unsubscribe":
                await self._handle_unsubscription(client_id, data)
            elif message_type == "ping":
                await self._handle_ping(client_id)
            elif message_type == "get_status":
                await self._handle_get_status(client_id)
            elif message_type == "get_best_parameters":
                await self._handle_get_best_parameters(client_id, data)
            elif message_type == "get_cached_results":
                await self._handle_get_cached_results(client_id, data)
            else:
                logger.warning(f"未知消息類型: {message_type}")
                await self.send_personal_message({
                    "type": "error",
                    "message": f"未知消息類型: {message_type}"
                }, client_id)

        except Exception as e:
            logger.error(f"處理客戶端消息失敗 {client_id}: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"處理消息失敗: {str(e)}"
            }, client_id)

    async def _handle_subscription(self, client_id: str, data: Dict[str, Any]):
        """處理訂閱請求"""
        try:
            subscription_type = data.get("subscription_type")
            request_id = data.get("request_id")

            if subscription_type:
                # 訂閱特定類型
                sub_type = SubscriptionType(subscription_type)
                if client_id not in self.subscription_types:
                    self.subscription_types[client_id] = set()
                self.subscription_types[client_id].add(sub_type)

                await self.send_personal_message({
                    "type": "subscription_confirmed",
                    "subscription_type": subscription_type,
                    "message": f"成功訂閱 {subscription_type}"
                }, client_id)

                # 如果是進度訂閱，發送緩存的進度數據
                if sub_type == SubscriptionType.OPTIMIZATION_PROGRESS:
                    await self._send_cached_progress(client_id)

                # 如果是結果訂閱，發送緩存的結果數據
                elif sub_type == SubscriptionType.OPTIMIZATION_RESULTS:
                    await self._send_cached_results(client_id)

            elif request_id:
                # 訂閱特定優化任務
                if client_id not in self.client_subscriptions:
                    self.client_subscriptions[client_id] = set()
                self.client_subscriptions[client_id].add(request_id)

                await self.send_personal_message({
                    "type": "subscription_confirmed",
                    "request_id": request_id,
                    "message": f"成功訂閱優化任務 {request_id}"
                }, client_id)

                # 發送該任務的緩存數據
                await self._send_task_specific_cache(client_id, request_id)

        except Exception as e:
            logger.error(f"處理訂閱失敗: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"訂閱失敗: {str(e)}"
            }, client_id)

    async def _handle_unsubscription(self, client_id: str, data: Dict[str, Any]):
        """處理取消訂閱請求"""
        try:
            subscription_type = data.get("subscription_type")
            request_id = data.get("request_id")

            if subscription_type:
                # 取消訂閱特定類型
                sub_type = SubscriptionType(subscription_type)
                if client_id in self.subscription_types:
                    self.subscription_types[client_id].discard(sub_type)

                await self.send_personal_message({
                    "type": "unsubscription_confirmed",
                    "subscription_type": subscription_type,
                    "message": f"取消訂閱 {subscription_type}"
                }, client_id)

            elif request_id:
                # 取消訂閱特定優化任務
                if client_id in self.client_subscriptions:
                    self.client_subscriptions[client_id].discard(request_id)

                await self.send_personal_message({
                    "type": "unsubscription_confirmed",
                    "request_id": request_id,
                    "message": f"取消訂閱優化任務 {request_id}"
                }, client_id)

        except Exception as e:
            logger.error(f"處理取消訂閱失敗: {e}")
            await self.send_personal_message({
                "type": "error",
                "message": f"取消訂閱失敗: {str(e)}"
            }, client_id)

    async def _handle_ping(self, client_id: str):
        """處理心跳檢查"""
        await self.send_personal_message({
            "type": "pong",
            "server_time": datetime.now().isoformat()
        }, client_id)

    async def _handle_get_status(self, client_id: str):
        """處理狀態查詢"""
        await self.send_personal_message({
            "type": "status_response",
            "server_status": {
                "active_connections": len(self.active_connections),
                "cached_tasks": len(self.progress_cache),
                "connection_stats": self.connection_stats
            }
        }, client_id)

    async def _handle_get_best_parameters(self, client_id: str, data: Dict[str, Any]):
        """處理最佳參數查詢"""
        symbol = data.get("symbol", "0700.HK")

        # 從緩存中獲取最佳參數
        best_params = self.best_parameters_cache.get(symbol)

        await self.send_personal_message({
            "type": "best_parameters_response",
            "symbol": symbol,
            "best_parameters": best_params
        }, client_id)

    async def _handle_get_cached_results(self, client_id: str, data: Dict[str, Any]):
        """處理緩存結果查詢"""
        request_id = data.get("request_id")

        if request_id and request_id in self.results_cache:
            results = self.results_cache[request_id]
            await self.send_personal_message({
                "type": "cached_results_response",
                "request_id": request_id,
                "results": [r.dict() for r in results]
            }, client_id)
        else:
            await self.send_personal_message({
                "type": "cached_results_response",
                "request_id": request_id,
                "results": [],
                "message": "未找到緩存結果"
            }, client_id)

    async def _send_cached_progress(self, client_id: str):
        """發送緩存的進度數據"""
        for request_id, progress in self.progress_cache.items():
            await self.send_personal_message({
                "type": "cached_progress",
                "request_id": request_id,
                "progress": progress.dict()
            }, client_id)

    async def _send_cached_results(self, client_id: str):
        """發送緩存的結果數據"""
        for request_id, results in self.results_cache.items():
            # 只發送前5個結果以避免數據過大
            top_results = sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)[:5]

            await self.send_personal_message({
                "type": "cached_results_summary",
                "request_id": request_id,
                "total_results": len(results),
                "top_results": [r.dict() for r in top_results]
            }, client_id)

    async def _send_task_specific_cache(self, client_id: str, request_id: str):
        """發送特定任務的緩存數據"""
        # 發送進度
        if request_id in self.progress_cache:
            await self.send_personal_message({
                "type": "cached_progress",
                "request_id": request_id,
                "progress": self.progress_cache[request_id].dict()
            }, client_id)

        # 發送結果摘要
        if request_id in self.results_cache:
            results = self.results_cache[request_id]
            top_results = sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)[:3]

            await self.send_personal_message({
                "type": "cached_results_summary",
                "request_id": request_id,
                "total_results": len(results),
                "top_results": [r.dict() for r in top_results]
            }, client_id)

    async def _heartbeat_loop(self):
        """心跳循環"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # 發送心跳消息給所有連接
                heartbeat_message = {
                    "type": "server_heartbeat",
                    "timestamp": datetime.now().isoformat(),
                    "active_connections": len(self.active_connections)
                }

                disconnected_clients = []
                for client_id, websocket in self.active_connections.items():
                    try:
                        await websocket.send_text(json.dumps(heartbeat_message, ensure_ascii=False))
                        self.connection_stats["messages_sent"] += 1
                    except Exception as e:
                        logger.warning(f"心跳發送失敗 {client_id}: {e}")
                        disconnected_clients.append(client_id)

                # 清理斷開的連接
                for client_id in disconnected_clients:
                    await self.disconnect(client_id)

                logger.debug(f"心跳檢查完成，活躍連接: {len(self.active_connections)}")

            except Exception as e:
                logger.error(f"心跳循環錯誤: {e}")

    # 公共接口方法
    async def update_progress(self, progress: OptimizationProgress):
        """更新優化進度"""
        try:
            # 緩存進度
            self.progress_cache[progress.request_id] = progress

            # 廣播進度更新
            await self.broadcast_message({
                "type": "optimization_progress_update",
                "request_id": progress.request_id,
                "progress": progress.dict()
            }, SubscriptionType.OPTIMIZATION_PROGRESS)

            # 如果有客戶端訂閱了特定任務，也發送給他們
            for client_id, subscribed_requests in self.client_subscriptions.items():
                if progress.request_id in subscribed_requests:
                    await self.send_personal_message({
                        "type": "optimization_progress_update",
                        "request_id": progress.request_id,
                        "progress": progress.dict()
                    }, client_id)

        except Exception as e:
            logger.error(f"更新進度失敗: {e}")

    async def add_result(self, request_id: str, result: OptimizationResult):
        """添加新的優化結果"""
        try:
            # 添加到緩存
            if request_id not in self.results_cache:
                self.results_cache[request_id] = []
            self.results_cache[request_id].append(result)

            # 限制緩存大小
            if len(self.results_cache[request_id]) > 1000:
                self.results_cache[request_id] = self.results_cache[request_id][-500:]

            # 廣播結果更新
            await self.broadcast_message({
                "type": "optimization_result_update",
                "request_id": request_id,
                "result": result.dict()
            }, SubscriptionType.OPTIMIZATION_RESULTS)

            # 更新最佳參數緩存
            await self._update_best_parameters_cache(request_id, result)

        except Exception as e:
            logger.error(f"添加結果失敗: {e}")

    async def _update_best_parameters_cache(self, request_id: str, result: OptimizationResult):
        """更新最佳參數緩存"""
        try:
            # 這裡需要從請求中獲取symbol信息
            # 簡化實現，假設都是0700.HK
            symbol = "0700.HK"

            if symbol not in self.best_parameters_cache:
                self.best_parameters_cache[symbol] = {
                    "best_sharpe": -999.0,
                    "best_combination": None,
                    "updated_at": None
                }

            current_best = self.best_parameters_cache[symbol]
            if result.sharpe_ratio > current_best["best_sharpe"]:
                self.best_parameters_cache[symbol] = {
                    "best_sharpe": result.sharpe_ratio,
                    "best_combination": result.dict(),
                    "request_id": request_id,
                    "updated_at": datetime.now().isoformat()
                }

                # 廣播最佳參數更新
                await self.broadcast_message({
                    "type": "best_parameters_update",
                    "symbol": symbol,
                    "best_parameters": self.best_parameters_cache[symbol]
                }, SubscriptionType.BEST_PARAMETERS)

        except Exception as e:
            logger.error(f"更新最佳參數緩存失敗: {e}")

    async def broadcast_system_performance(self, performance_data: Dict[str, Any]):
        """廣播系統性能數據"""
        try:
            await self.broadcast_message({
                "type": "system_performance_update",
                "performance": performance_data
            }, SubscriptionType.SYSTEM_PERFORMANCE)

        except Exception as e:
            logger.error(f"廣播系統性能失敗: {e}")

    async def get_connection_stats(self) -> Dict[str, Any]:
        """獲取連接統計信息"""
        return {
            **self.connection_stats,
            "active_connections": len(self.active_connections),
            "subscription_stats": {
                sub_type.value: sum(1 for subs in self.subscription_types.values() if sub_type in subs)
                for sub_type in SubscriptionType
            }
        }

# 全局監控器實例
parameter_monitor = ParameterMonitor()

async def get_parameter_monitor():
    """獲取參數監控器實例"""
    return parameter_monitor