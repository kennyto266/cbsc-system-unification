"""
WebSocket实时通信
WebSocket Real-time Communication

职责：
- 实时数据推送
- 策略状态更新
- 市场数据广播
- 连接管理
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Optional, Set
import json
import asyncio
import logging
from datetime import datetime

from .services.websocket_service import WebSocketService
from .utils.permissions import authenticate_websocket
from .utils.cache import cache_manager
from .models import User

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# ============================================================================
# WebSocket端点 (WebSocket Endpoints)
# ============================================================================

@router.websocket("/realtime/{user_id}")
async def websocket_realtime_endpoint(
    websocket: WebSocket,
    user_id: int,
    websocket_service: WebSocketService = Depends()
):
    """
    实时数据WebSocket端点

    为用户提供实时数据推送，包括：
    - 策略状态更新
    - 新信号通知
    - 性能数据变化
    - 个人告警
    """
    try:
        # 认证WebSocket连接
        user = await authenticate_websocket(websocket, user_id=user_id)
        if not user:
            return

        # 处理连接
        await websocket_service.handle_connection(websocket, user_id, "realtime")

    except WebSocketDisconnect:
        logger.info(f"用户 {user_id} 断开实时数据连接")
    except Exception as e:
        logger.error(f"实时数据WebSocket错误: {e}")
        await websocket.close(code=4000)


@router.websocket("/strategy/{strategy_id}")
async def websocket_strategy_updates(
    websocket: WebSocket,
    strategy_id: str,
    websocket_service: WebSocketService = Depends()
):
    """
    策略特定更新WebSocket端点

    为特定策略提供实时更新，包括：
    - 执行状态变化
    - 实时信号生成
    - 性能指标更新
    """
    try:
        # 认证WebSocket连接
        user = await authenticate_websocket(websocket, strategy_id=strategy_id)
        if not user:
            return

        # 验证用户是否有权限访问该策略
        if not await websocket_service.check_strategy_permission(user, strategy_id):
            await websocket.close(code=4003, reason="无权限访问策略")
            return

        # 处理连接
        await websocket_service.handle_connection(websocket, user.id, "strategy", strategy_id=strategy_id)

    except WebSocketDisconnect:
        logger.info(f"策略 {strategy_id} WebSocket断开连接")
    except Exception as e:
        logger.error(f"策略WebSocket错误: {e}")
        await websocket.close(code=4000)


@router.websocket("/market-data")
async def websocket_market_data(
    websocket: WebSocket,
    websocket_service: WebSocketService = Depends()
):
    """
    市场数据WebSocket端点

    提供实时市场数据推送：
    - 价格变动
    - 成交量变化
    - 市场指标
    """
    try:
        # 认证WebSocket连接
        user = await authenticate_websocket(websocket)
        if not user:
            return

        # 处理连接
        await websocket_service.handle_connection(websocket, user.id, "market")

    except WebSocketDisconnect:
        logger.info("市场数据WebSocket断开连接")
    except Exception as e:
        logger.error(f"市场数据WebSocket错误: {e}")
        await websocket.close(code=4000)


@router.websocket("/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket,
    user_id: int,
    websocket_service: WebSocketService = Depends()
):
    """
    通知WebSocket端点

    为用户推送实时通知：
    - 系统通知
    - 策略告警
    - 交易提醒
    """
    try:
        # 认证WebSocket连接
        user = await authenticate_websocket(websocket, user_id=user_id)
        if not user:
            return

        # 处理连接
        await websocket_service.handle_connection(websocket, user_id, "notifications")

    except WebSocketDisconnect:
        logger.info(f"用户 {user_id} 通知WebSocket断开连接")
    except Exception as e:
        logger.error(f"通知WebSocket错误: {e}")
        await websocket.close(code=4000)


# ============================================================================
# WebSocket管理端点 (WebSocket Management Endpoints)
# ============================================================================

@router.get("/websocket/status", response_model=dict)
async def get_websocket_status():
    """
    获取WebSocket服务状态
    """
    from .services.websocket_service import websocket_manager

    stats = websocket_manager.get_connection_stats()
    return {
        "status": "running",
        "connections": stats,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/broadcast/{message_type}")
async def broadcast_message(
    message_type: str,
    message_data: dict,
    target_users: Optional[List[int]] = None
):
    """
    广播消息

    向指定用户或所有用户广播消息
    """
    from .services.websocket_service import websocket_manager

    message = {
        "type": message_type,
        "data": message_data,
        "timestamp": datetime.now().isoformat()
    }

    if target_users:
        # 发送给指定用户
        success_count = await websocket_manager.broadcast_to_users(target_users, message)
        return {
            "success": True,
            "message": f"消息已发送给 {success_count}/{len(target_users)} 个用户",
            "target_users": len(target_users),
            "sent_count": success_count
        }
    else:
        # 发送给所有用户
        success_count = await websocket_manager.broadcast_to_all(message)
        return {
            "success": True,
            "message": f"消息已广播给 {success_count} 个用户",
            "sent_count": success_count
        }


@router.post("/strategy/{strategy_id}/notify")
async def notify_strategy_update(
    strategy_id: str,
    update_data: dict,
    websocket_service: WebSocketService = Depends()
):
    """
    通知策略更新

    向订阅了该策略的所有用户发送更新
    """
    message = {
        "type": "strategy_update",
        "strategy_id": strategy_id,
        "data": update_data,
        "timestamp": datetime.now().isoformat()
    }

    sent_count = await websocket_service.notify_strategy_subscribers(strategy_id, message)

    return {
        "success": True,
        "message": f"策略更新已发送给 {sent_count} 个订阅者",
        "strategy_id": strategy_id,
        "sent_count": sent_count
    }


@router.post("/market-data/update")
async def update_market_data(
    market_data: dict,
    websocket_service: WebSocketService = Depends()
):
    """
    更新市场数据

    向所有市场数据订阅者推送最新市场数据
    """
    message = {
        "type": "market_data_update",
        "data": market_data,
        "timestamp": datetime.now().isoformat()
    }

    sent_count = await websocket_service.broadcast_to_channel("market", message)

    return {
        "success": True,
        "message": f"市场数据已推送给 {sent_count} 个订阅者",
        "sent_count": sent_count
    }


@router.post("/notifications/send")
async def send_notification(
    user_id: int,
    notification: dict,
    websocket_service: WebSocketService = Depends()
):
    """
    发送个人通知

    向指定用户发送个人通知
    """
    message = {
        "type": "notification",
        "data": notification,
        "timestamp": datetime.now().isoformat()
    }

    sent = await websocket_service.send_to_user(user_id, message)

    return {
        "success": sent,
        "message": "通知已发送" if sent else "用户未连接",
        "user_id": user_id
    }


# ============================================================================
# WebSocket历史和统计端点 (WebSocket History & Statistics)
# ============================================================================

@router.get("/websocket/history/{user_id}", response_model=dict)
async def get_websocket_message_history(
    user_id: int,
    limit: int = 100
):
    """
    获取WebSocket消息历史

    获取用户的历史消息记录
    """
    # 从缓存获取历史消息
    cache_key = f"websocket:history:{user_id}"
    history = await cache_manager.get(cache_key) or []

    # 返回最新的消息
    return {
        "user_id": user_id,
        "messages": history[-limit:] if history else [],
        "total_count": len(history),
        "limit": limit
    }


@router.get("/websocket/analytics", response_model=dict)
async def get_websocket_analytics():
    """
    获取WebSocket分析数据

    获取WebSocket服务的分析统计信息
    """
    from .services.websocket_service import websocket_manager

    stats = websocket_manager.get_connection_stats()
    analytics = websocket_manager.get_analytics()

    return {
        "current_stats": stats,
        "analytics": analytics,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# 测试端点 (Test Endpoints)
# ============================================================================

@router.post("/test/message")
async def test_websocket_message(
    message_type: str,
    message_data: dict,
    target_user: Optional[int] = None,
    websocket_service: WebSocketService = Depends()
):
    """
    测试WebSocket消息

    用于测试WebSocket消息发送
    """
    test_message = {
        "type": "test",
        "test_type": message_type,
        "data": message_data,
        "timestamp": datetime.now().isoformat()
    }

    if target_user:
        sent = await websocket_service.send_to_user(target_user, test_message)
        return {
            "success": sent,
            "message": f"测试消息已发送给用户 {target_user}" if sent else f"用户 {target_user} 未连接",
            "target_user": target_user
        }
    else:
        sent_count = await websocket_manager.broadcast_to_all(test_message)
        return {
            "success": True,
            "message": f"测试消息已广播给 {sent_count} 个用户",
            "sent_count": sent_count
        }


@router.get("/test/connections", response_model=dict)
async def test_websocket_connections():
    """
    测试WebSocket连接状态

    返回当前的WebSocket连接统计
    """
    from .services.websocket_service import websocket_manager

    connections = websocket_manager.get_all_connections()
    connection_info = []

    for conn_id, conn_info in connections.items():
        connection_info.append({
            "connection_id": conn_id,
            "user_id": conn_info.get("user_id"),
            "channel": conn_info.get("channel"),
            "connected_at": conn_info.get("connected_at"),
            "last_activity": conn_info.get("last_activity")
        })

    return {
        "total_connections": len(connection_info),
        "connections": connection_info,
        "timestamp": datetime.now().isoformat()
    }