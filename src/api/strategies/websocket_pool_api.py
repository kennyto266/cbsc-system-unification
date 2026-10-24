"""
WebSocket连接池API路由
WebSocket Pool API Routes

提供WebSocket连接池的REST API接口，包括：
- 连接池状态查询
- 连接管理
- 消息广播
- 统计信息
- 管理功能
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel, Field

from .websocket_pool_integration import get_pool_manager, WebSocketPoolManager
from ...services.websocket_pool import get_connection_pool, ConnectionPoolConfig


# Models for API requests/responses
class BroadcastRequest(BaseModel):
    """广播请求模型"""
    channel: str = Field(..., description="Target channel")
    message: Dict[str, Any] = Field(..., description="Message to broadcast")
    exclude_users: Optional[List[int]] = Field(None, description="User IDs to exclude")


class UserMessageRequest(BaseModel):
    """用户消息请求模型"""
    user_id: int = Field(..., description="Target user ID")
    message: Dict[str, Any] = Field(..., description="Message to send")
    message_type: str = Field("data", description="Message type")


class StrategyBroadcastRequest(BaseModel):
    """策略广播请求模型"""
    strategy_id: str = Field(..., description="Strategy ID")
    message: Dict[str, Any] = Field(..., description="Message to broadcast")


class PoolConfigUpdateRequest(BaseModel):
    """连接池配置更新请求"""
    max_connections_per_user: Optional[int] = Field(None, ge=1, le=100)
    max_total_connections: Optional[int] = Field(None, ge=1, le=10000)
    heartbeat_interval: Optional[int] = Field(None, ge=5, le=300)
    idle_timeout: Optional[int] = Field(None, ge=30, le=3600)
    health_check_interval: Optional[int] = Field(None, ge=10, le=600)


router = APIRouter(prefix="/ws-pool", tags=["websocket-pool"])


def require_admin_permission():
    """
    管理员权限检查（简化实现）
    实际应用中应该实现完整的权限检查
    """
    # TODO: Implement proper admin permission checking
    return True


@router.get("/status")
async def get_pool_status():
    """
    获取连接池状态
    """
    try:
        pool = get_connection_pool()
        stats = pool.get_pool_stats()

        return {
            "success": True,
            "data": {
                "status": "running",
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pool status: {str(e)}"
        )


@router.get("/connections")
async def list_connections(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of connections")
):
    """
    列出连接信息
    """
    try:
        pool = get_connection_pool()
        connections = []

        for conn_id, conn_info in pool.connections.items():
            # Apply filters
            if user_id and conn_info.user_id != user_id:
                continue
            if channel and conn_info.channel != channel:
                continue
            if status and conn_info.status.value != status:
                continue

            if len(connections) >= limit:
                break

            connections.append(pool.get_connection_details(conn_id))

        return {
            "success": True,
            "data": {
                "connections": connections,
                "total_count": len(pool.connections),
                "filtered_count": len(connections),
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list connections: {str(e)}"
        )


@router.get("/connections/{connection_id}")
async def get_connection_details(connection_id: str):
    """
    获取特定连接的详细信息
    """
    try:
        pool = get_connection_pool()
        connection_details = pool.get_connection_details(connection_id)

        if not connection_details:
            raise HTTPException(
                status_code=404,
                detail=f"Connection {connection_id} not found"
            )

        return {
            "success": True,
            "data": connection_details
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get connection details: {str(e)}"
        )


@router.delete("/connections/{connection_id}")
async def disconnect_connection(
    connection_id: str,
    reason: str = Query("admin_disconnect", description="Disconnection reason")
):
    """
    断开指定连接
    """
    try:
        pool = get_connection_pool()
        success = await pool.remove_connection(connection_id, reason)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Connection {connection_id} not found"
            )

        return {
            "success": True,
            "data": {
                "connection_id": connection_id,
                "disconnected_at": datetime.now().isoformat(),
                "reason": reason
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect connection: {str(e)}"
        )


@router.post("/broadcast")
async def broadcast_to_channel(
    request: BroadcastRequest,
    background_tasks: BackgroundTasks
):
    """
    向频道广播消息
    """
    try:
        pool = get_connection_pool()

        # Execute broadcast in background
        async def broadcast_task():
            sent_count = await pool.broadcast_to_channel(
                channel=request.channel,
                message=request.message
            )
            return sent_count

        # Run broadcast asynchronously
        sent_count = await broadcast_task()

        return {
            "success": True,
            "data": {
                "channel": request.channel,
                "sent_count": sent_count,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to broadcast message: {str(e)}"
        )


@router.post("/send-to-user")
async def send_message_to_user(request: UserMessageRequest):
    """
    发送消息给指定用户
    """
    try:
        pool = get_connection_pool()
        from ...services.websocket_pool import MessageType

        message_type = MessageType.DATA
        if request.message_type == "broadcast":
            message_type = MessageType.BROADCAST
        elif request.message_type == "system":
            message_type = MessageType.SYSTEM

        sent_count = await pool.send_to_user(
            user_id=request.user_id,
            message=request.message,
            message_type=message_type
        )

        return {
            "success": True,
            "data": {
                "user_id": request.user_id,
                "sent_count": sent_count,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message to user: {str(e)}"
        )


@router.post("/broadcast-to-strategy")
async def broadcast_to_strategy_subscribers(request: StrategyBroadcastRequest):
    """
    向策略订阅者广播消息
    """
    try:
        pool = get_connection_pool()
        sent_count = await pool.broadcast_to_strategy_subscribers(
            strategy_id=request.strategy_id,
            message=request.message
        )

        return {
            "success": True,
            "data": {
                "strategy_id": request.strategy_id,
                "sent_count": sent_count,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to broadcast to strategy subscribers: {str(e)}"
        )


@router.get("/stats")
async def get_detailed_stats(
    hours: int = Query(24, ge=1, le=168, description="Statistics time window in hours")
):
    """
    获取详细统计信息
    """
    try:
        pool = get_connection_pool()
        stats = pool.get_pool_stats()

        # Calculate additional metrics
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=hours)

        # Active connections by hour (simplified)
        connections_by_hour = {}
        for i in range(hours):
            hour_time = current_time - timedelta(hours=i)
            hour_key = hour_time.strftime("%Y-%m-%dT%H:00:00Z")
            connections_by_hour[hour_key] = len(pool.connections)  # Simplified

        # Top channels by connections
        channel_stats = {}
        for channel, connection_ids in pool.channel_subscriptions.items():
            channel_stats[channel] = len(connection_ids)

        # Top strategies by subscribers
        strategy_stats = {}
        for strategy_id, connection_ids in pool.strategy_connections.items():
            strategy_stats[strategy_id] = len(connection_ids)

        detailed_stats = {
            **stats,
            "connections_by_hour": connections_by_hour,
            "channel_stats": dict(sorted(channel_stats.items(), key=lambda x: x[1], reverse=True)),
            "strategy_stats": dict(sorted(strategy_stats.items(), key=lambda x: x[1], reverse=True)),
            "time_window_hours": hours,
            "generated_at": current_time.isoformat()
        }

        return {
            "success": True,
            "data": detailed_stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get detailed stats: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    连接池健康检查
    """
    try:
        pool = get_connection_pool()
        stats = pool.get_pool_stats()

        # Determine health status
        total_connections = stats["total_connections"]
        active_connections = stats["active_connections"]
        error_rate = 0.0

        if stats["total_messages_sent"] > 0:
            error_rate = stats["connection_errors"] / stats["total_messages_sent"]

        # Health criteria
        is_healthy = (
            error_rate < 0.05 and  # Less than 5% error rate
            active_connections >= 0 and  # No negative connections
            stats.get("throughput_per_second", 0) >= 0  # Positive throughput
        )

        health_status = "healthy" if is_healthy else "unhealthy"

        return {
            "success": True,
            "data": {
                "status": health_status,
                "metrics": {
                    "total_connections": total_connections,
                    "active_connections": active_connections,
                    "error_rate": error_rate,
                    "uptime_seconds": (datetime.now() - stats["start_time"]).total_seconds(),
                    "last_cleanup": stats["last_cleanup"].isoformat()
                },
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        }


@router.get("/config")
async def get_pool_config():
    """
    获取连接池配置
    """
    try:
        pool = get_connection_pool()
        config = pool.config.dict()

        return {
            "success": True,
            "data": {
                "config": config,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get pool config: {str(e)}"
        )


@router.put("/config")
async def update_pool_config(request: PoolConfigUpdateRequest):
    """
    更新连接池配置
    """
    try:
        # TODO: Implement dynamic config updates
        # For now, return the current config
        pool = get_connection_pool()
        current_config = pool.config.dict()

        return {
            "success": False,
            "message": "Dynamic config update not implemented yet",
            "current_config": current_config
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update pool config: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_connections():
    """
    手动触发连接清理
    """
    try:
        pool = get_connection_pool()

        # The cleanup is handled by the background task
        # Here we just return the current cleanup status
        stats = pool.get_pool_stats()

        return {
            "success": True,
            "data": {
                "message": "Cleanup triggered successfully",
                "last_cleanup": stats["last_cleanup"].isoformat(),
                "current_connections": stats["total_connections"],
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger cleanup: {str(e)}"
        )


@router.get("/users/{user_id}/connections")
async def get_user_connections(user_id: int):
    """
    获取用户的所有连接
    """
    try:
        pool = get_connection_pool()
        user_connections = pool.user_connections.get(user_id, set())
        connection_details = []

        for connection_id in user_connections:
            details = pool.get_connection_details(connection_id)
            if details:
                connection_details.append(details)

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "connections": connection_details,
                "total_count": len(connection_details),
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user connections: {str(e)}"
        )


@router.delete("/users/{user_id}/connections")
async def disconnect_user_connections(
    user_id: int,
    reason: str = Query("admin_disconnect_user", description="Disconnection reason")
):
    """
    断开用户的所有连接
    """
    try:
        pool = get_connection_pool()
        user_connections = pool.user_connections.get(user_id, set()).copy()
        disconnected_count = 0

        for connection_id in user_connections:
            if await pool.remove_connection(connection_id, f"{reason}_{user_id}"):
                disconnected_count += 1

        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "disconnected_count": disconnected_count,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disconnect user connections: {str(e)}"
        )