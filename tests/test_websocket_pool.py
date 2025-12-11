"""
WebSocket连接池单元测试
WebSocket Pool Unit Tests

测试WebSocket连接池的各项功能：
- 连接管理
- 消息发送和接收
- 订阅和取消订阅
- 健康检查
- 指标收集
- 错误处理
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from src.services.websocket_pool import (
    WebSocketConnectionPool, ConnectionPoolConfig, ConnectionInfo,
    ConnectionStatus, MessageType
)


class MockWebSocket:
    """模拟WebSocket连接"""

    def __init__(self, connection_id: str = "test-conn"):
        self.connection_id = connection_id
        self.messages_sent = []
        self.closed = False
        self.close_code = None
        self.close_reason = None
        self.client_state = Mock()
        self.client_state.name = "CONNECTED"

    async def send_text(self, data: str):
        """模拟发送文本消息"""
        if self.closed:
            raise ConnectionError("WebSocket is closed")
        self.messages_sent.append(json.loads(data))

    async def close(self, code: int = 1000, reason: str = ""):
        """模拟关闭连接"""
        self.closed = True
        self.close_code = code
        self.close_reason = reason


@pytest.fixture
def pool_config():
    """测试用的连接池配置"""
    return ConnectionPoolConfig(
        max_connections_per_user=3,
        max_total_connections=10,
        heartbeat_interval=1,
        idle_timeout=5,
        health_check_interval=2
    )


@pytest.fixture
async def websocket_pool(pool_config):
    """创建WebSocket连接池实例"""
    pool = WebSocketConnectionPool(pool_config)
    yield pool
    # 清理
    await pool.shutdown()


@pytest.fixture
def mock_websocket():
    """创建模拟WebSocket"""
    return MockWebSocket()


class TestWebSocketConnectionPool:
    """WebSocket连接池测试"""

    @pytest.mark.asyncio
    async def test_add_connection_success(self, websocket_pool, mock_websocket):
        """测试成功添加连接"""
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1",
            channel="test"
        )

        assert success is True
        assert connection_id in websocket_pool.connections
        assert connection_id in websocket_pool.user_connections[1]
        assert connection_id in websocket_pool.channel_subscriptions["test"]

        connection_info = websocket_pool.connections[connection_id]
        assert connection_info.user_id == 1
        assert connection_info.client_ip == "127.0.0.1"
        assert connection_info.channel == "test"
        assert connection_info.status == ConnectionStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_add_connection_user_limit(self, websocket_pool):
        """测试用户连接数限制"""
        # 添加最大数量的连接
        connections = []
        for i in range(3):  # max_connections_per_user = 3
            ws = MockWebSocket(f"conn-{i}")
            success, conn_id = await websocket_pool.add_connection(
                websocket=ws,
                user_id=1,
                client_ip="127.0.0.1"
            )
            assert success is True
            connections.append(conn_id)

        # 尝试添加超出限制的连接
        ws_extra = MockWebSocket("conn-extra")
        success, conn_id = await websocket_pool.add_connection(
            websocket=ws_extra,
            user_id=1,
            client_ip="127.0.0.1"
        )

        assert success is False
        assert conn_id == "Connection limit exceeded"

    @pytest.mark.asyncio
    async def test_add_connection_total_limit(self, websocket_pool):
        """测试总连接数限制"""
        # 添加最大数量的连接（不同用户）
        connections = []
        for i in range(10):  # max_total_connections = 10
            ws = MockWebSocket(f"conn-{i}")
            success, conn_id = await websocket_pool.add_connection(
                websocket=ws,
                user_id=i,
                client_ip="127.0.0.1"
            )
            assert success is True
            connections.append(conn_id)

        # 尝试添加超出限制的连接
        ws_extra = MockWebSocket("conn-extra")
        success, conn_id = await websocket_pool.add_connection(
            websocket=ws_extra,
            user_id=100,
            client_ip="127.0.0.1"
        )

        assert success is False
        assert conn_id == "Connection limit exceeded"

    @pytest.mark.asyncio
    async def test_remove_connection(self, websocket_pool, mock_websocket):
        """测试移除连接"""
        # 先添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1",
            channel="test"
        )
        assert success is True

        # 移除连接
        removed = await websocket_pool.remove_connection(connection_id)
        assert removed is True
        assert connection_id not in websocket_pool.connections
        assert connection_id not in websocket_pool.user_connections[1]
        assert connection_id not in websocket_pool.channel_subscriptions["test"]

        # WebSocket应该被关闭
        assert mock_websocket.closed is True

    @pytest.mark.asyncio
    async def test_remove_nonexistent_connection(self, websocket_pool):
        """测试移除不存在的连接"""
        removed = await websocket_pool.remove_connection("nonexistent")
        assert removed is False

    @pytest.mark.asyncio
    async def test_send_message_success(self, websocket_pool, mock_websocket):
        """测试成功发送消息"""
        # 添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1"
        )
        assert success is True

        # 发送消息
        message = {"test": "data"}
        sent = await websocket_pool.send_message(connection_id, message)

        assert sent is True
        assert len(mock_websocket.messages_sent) == 1

        sent_message = mock_websocket.messages_sent[0]
        assert sent_message["type"] == MessageType.DATA.value
        assert sent_message["data"] == message

    @pytest.mark.asyncio
    async def test_send_message_nonexistent_connection(self, websocket_pool):
        """测试向不存在的连接发送消息"""
        sent = await websocket_pool.send_message("nonexistent", {"test": "data"})
        assert sent is False

    @pytest.mark.asyncio
    async def test_send_message_closed_websocket(self, websocket_pool, mock_websocket):
        """测试向已关闭的WebSocket发送消息"""
        # 添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1"
        )
        assert success is True

        # 关闭WebSocket
        mock_websocket.closed = True

        # 尝试发送消息
        sent = await websocket_pool.send_message(connection_id, {"test": "data"})
        assert sent is False

        # 连接应该被移除
        assert connection_id not in websocket_pool.connections

    @pytest.mark.asyncio
    async def test_send_to_user(self, websocket_pool):
        """测试向用户发送消息"""
        # 为用户1添加多个连接
        user_id = 1
        connections = []
        for i in range(3):
            ws = MockWebSocket(f"conn-{i}")
            success, conn_id = await websocket_pool.add_connection(
                websocket=ws,
                user_id=user_id,
                client_ip="127.0.0.1"
            )
            assert success is True
            connections.append((conn_id, ws))

        # 发送消息给用户
        message = {"user_message": "test"}
        sent_count = await websocket_pool.send_to_user(user_id, message)

        assert sent_count == 3

        # 验证所有连接都收到了消息
        for conn_id, ws in connections:
            assert len(ws.messages_sent) == 1
            assert ws.messages_sent[0]["data"] == message

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, websocket_pool):
        """测试向频道广播消息"""
        # 添加连接到不同频道
        channel1_connections = []
        channel2_connections = []

        for i in range(3):
            # 添加到channel1
            ws1 = MockWebSocket(f"ch1-conn-{i}")
            success, conn_id = await websocket_pool.add_connection(
                websocket=ws1,
                user_id=i,
                client_ip="127.0.0.1",
                channel="channel1"
            )
            channel1_connections.append((conn_id, ws1))

            # 添加到channel2
            ws2 = MockWebSocket(f"ch2-conn-{i}")
            success, conn_id = await websocket_pool.add_connection(
                websocket=ws2,
                user_id=i+10,
                client_ip="127.0.0.1",
                channel="channel2"
            )
            channel2_connections.append((conn_id, ws2))

        # 向channel1广播消息
        message = {"broadcast": "test"}
        sent_count = await websocket_pool.broadcast_to_channel("channel1", message)

        assert sent_count == 3

        # 验证只有channel1的连接收到了消息
        for conn_id, ws in channel1_connections:
            assert len(ws.messages_sent) == 1
            assert ws.messages_sent[0]["data"] == message

        for conn_id, ws in channel2_connections:
            assert len(ws.messages_sent) == 0

    @pytest.mark.asyncio
    async def test_subscribe_to_channel(self, websocket_pool, mock_websocket):
        """测试订阅频道"""
        # 添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1",
            channel="default"
        )
        assert success is True

        # 订阅新频道
        subscribed = await websocket_pool.subscribe_to_channel(connection_id, "new_channel")
        assert subscribed is True

        # 验证订阅状态
        connection_info = websocket_pool.connections[connection_id]
        assert "new_channel" in connection_info.subscriptions
        assert connection_info.channel == "new_channel"
        assert connection_id in websocket_pool.channel_subscriptions["new_channel"]

    @pytest.mark.asyncio
    async def test_unsubscribe_from_channel(self, websocket_pool, mock_websocket):
        """测试取消订阅频道"""
        # 添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1",
            channel="test_channel"
        )
        assert success is True

        # 取消订阅
        unsubscribed = await websocket_pool.unsubscribe_from_channel(connection_id, "test_channel")
        assert unsubscribed is True

        # 验证取消订阅状态
        connection_info = websocket_pool.connections[connection_id]
        assert "test_channel" not in connection_info.subscriptions
        assert connection_id not in websocket_pool.channel_subscriptions.get("test_channel", set())

    @pytest.mark.asyncio
    async def test_broadcast_to_strategy_subscribers(self, websocket_pool):
        """测试向策略订阅者广播"""
        strategy_id = "test_strategy"
        connections = []

        # 添加策略订阅连接
        for i in range(3):
            ws = MockWebSocket(f"strategy-conn-{i}")
            success, conn_id = await websocket_pool.add_connection(
                websocket=ws,
                user_id=i,
                client_ip="127.0.0.1",
                strategy_ids=[strategy_id]
            )
            assert success is True
            connections.append((conn_id, ws))

        # 添加非策略订阅连接
        ws_other = MockWebSocket("other-conn")
        success, other_conn_id = await websocket_pool.add_connection(
            websocket=ws_other,
            user_id=100,
            client_ip="127.0.0.1"
        )
        connections.append((other_conn_id, ws_other))

        # 向策略订阅者广播
        message = {"strategy_update": "test"}
        sent_count = await websocket_pool.broadcast_to_strategy_subscribers(strategy_id, message)

        assert sent_count == 3

        # 验证只有策略订阅者收到了消息
        for i in range(3):
            conn_id, ws = connections[i]
            assert len(ws.messages_sent) == 1
            assert ws.messages_sent[0]["data"] == message

        # 非策略订阅者不应该收到消息
        assert len(connections[3][1].messages_sent) == 0

    def test_get_pool_stats(self, websocket_pool):
        """测试获取连接池统计"""
        stats = websocket_pool.get_pool_stats()

        assert "total_connections" in stats
        assert "active_connections" in stats
        assert "peak_connections" in stats
        assert "total_messages_sent" in stats
        assert "start_time" in stats
        assert "config" in stats
        assert "connections_by_user" in stats
        assert "channels" in stats
        assert "strategies" in stats

    def test_get_connection_details(self, websocket_pool, mock_websocket):
        """测试获取连接详细信息"""
        # 添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1",
            channel="test"
        )
        assert success is True

        # 获取连接详情
        details = websocket_pool.get_connection_details(connection_id)

        assert details is not None
        assert details["connection_id"] == connection_id
        assert details["user_id"] == 1
        assert details["client_ip"] == "127.0.0.1"
        assert details["status"] == ConnectionStatus.CONNECTED.value
        assert details["channel"] == "test"

    def test_get_connection_details_nonexistent(self, websocket_pool):
        """测试获取不存在连接的详细信息"""
        details = websocket_pool.get_connection_details("nonexistent")
        assert details is None

    @pytest.mark.asyncio
    async def test_event_handlers(self, websocket_pool, mock_websocket):
        """测试事件处理器"""
        events = []

        async def on_connection_added(connection_info):
            events.append(("added", connection_info.connection_id))

        async def on_connection_removed(connection_info):
            events.append(("removed", connection_info.connection_id))

        # 添加事件处理器
        websocket_pool.add_event_handler("connection_added", on_connection_added)
        websocket_pool.add_event_handler("connection_removed", on_connection_removed)

        # 添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1"
        )

        # 等待事件处理
        await asyncio.sleep(0.1)

        # 移除连接
        await websocket_pool.remove_connection(connection_id)

        # 等待事件处理
        await asyncio.sleep(0.1)

        # 验证事件
        assert len(events) == 2
        assert events[0] == ("added", connection_id)
        assert events[1] == ("removed", connection_id)

    @pytest.mark.asyncio
    async def test_metrics_collection(self, websocket_pool, mock_websocket):
        """测试指标收集"""
        # 添加连接
        success, connection_id = await websocket_pool.add_connection(
            websocket=mock_websocket,
            user_id=1,
            client_ip="127.0.0.1"
        )
        assert success is True

        # 发送多条消息
        for i in range(5):
            await websocket_pool.send_message(connection_id, {"message": i})

        # 检查连接指标
        connection_info = websocket_pool.connections[connection_id]
        assert connection_info.metrics.messages_sent == 5
        assert connection_info.metrics.bytes_sent > 0

        # 检查连接池指标
        stats = websocket_pool.get_pool_stats()
        assert stats["total_messages_sent"] == 5

    @pytest.mark.asyncio
    async def test_connection_timeout_cleanup(self, websocket_pool, mock_websocket):
        """测试连接超时清理"""
        # 使用短超时的配置
        pool = WebSocketConnectionPool(ConnectionPoolConfig(
            idle_timeout=1,  # 1秒超时
            health_check_interval=1  # 1秒检查
        ))

        try:
            # 添加连接
            success, connection_id = await pool.add_connection(
                websocket=mock_websocket,
                user_id=1,
                client_ip="127.0.0.1"
            )
            assert success is True

            # 修改最后活动时间为超时
            connection_info = pool.connections[connection_id]
            connection_info.metrics.last_activity = datetime.now() - timedelta(seconds=2)

            # 等待健康检查
            await asyncio.sleep(1.5)

            # 连接应该被清理
            assert connection_id not in pool.connections

        finally:
            await pool.shutdown()


@pytest.mark.asyncio
async def test_get_connection_pool():
    """测试获取全局连接池实例"""
    from src.services.websocket_pool import get_connection_pool, cleanup_connection_pool

    # 获取连接池
    pool1 = get_connection_pool()
    pool2 = get_connection_pool()

    # 应该是同一个实例
    assert pool1 is pool2

    # 清理
    await cleanup_connection_pool()


class TestConnectionPoolConfig:
    """连接池配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = ConnectionPoolConfig()

        assert config.max_connections_per_user == 5
        assert config.max_total_connections == 1000
        assert config.heartbeat_interval == 30
        assert config.idle_timeout == 300
        assert config.health_check_interval == 60

    def test_custom_config(self):
        """测试自定义配置"""
        config = ConnectionPoolConfig(
            max_connections_per_user=10,
            max_total_connections=2000,
            heartbeat_interval=15
        )

        assert config.max_connections_per_user == 10
        assert config.max_total_connections == 2000
        assert config.heartbeat_interval == 15
        assert config.idle_timeout == 300  # 默认值

    def test_config_validation(self):
        """测试配置验证"""
        # 测试无效值
        with pytest.raises(ValueError):
            ConnectionPoolConfig(max_connections_per_user=0)

        with pytest.raises(ValueError):
            ConnectionPoolConfig(max_total_connections=-1)

        with pytest.raises(ValueError):
            ConnectionPoolConfig(heartbeat_interval=0)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])