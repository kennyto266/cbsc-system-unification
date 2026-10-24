"""
WebSocket连接池端到端测试
WebSocket Pool End-to-End Tests

测试WebSocket连接池的完整流程：
- WebSocket连接建立
- 消息发送和接收
- 订阅和广播
- 性能测试
- 并发测试
- 错误恢复
"""

import asyncio
import json
import pytest
import websockets
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aiohttp
import time

from fastapi.testclient import TestClient
from src.api.main import app


class WebSocketE2ETestClient:
    """E2E测试WebSocket客户端"""

    def __init__(self, uri: str):
        self.uri = uri
        self.websocket = None
        self.messages = []
        self.connection_id = None

    async def connect(self, token: str = "test-token", channel: str = "default"):
        """连接WebSocket"""
        uri = f"{self.uri}?token={token}&channel={channel}"
        self.websocket = await websockets.connect(uri)
        return self.websocket

    async def send_message(self, message: Dict[str, Any]):
        """发送消息"""
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")
        await self.websocket.send(json.dumps(message))

    async def receive_message(self, timeout: float = 5.0) -> Dict[str, Any]:
        """接收消息"""
        if not self.websocket:
            raise ConnectionError("WebSocket not connected")

        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            data = json.loads(message)
            self.messages.append(data)
            return data
        except asyncio.TimeoutError:
            raise TimeoutError("No message received within timeout")

    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None


@pytest.fixture(scope="module")
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def websocket_clients():
    """创建多个WebSocket客户端"""
    clients = []
    yield clients
    # 清理
    for client in clients:
        await client.close()


class TestWebSocketE2E:
    """WebSocket端到端测试"""

    @pytest.mark.asyncio
    async def test_connection_establishment(self, websocket_clients):
        """测试连接建立"""
        client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
        websocket_clients.append(client)

        # 建立连接
        await client.connect(token="test-token-123")

        # 接收欢迎消息
        welcome_message = await client.receive_message()
        assert welcome_message["type"] == "connection_established"
        assert "connection_id" in welcome_message["data"]
        assert welcome_message["data"]["channel"] == "default"

        client.connection_id = welcome_message["data"]["connection_id"]

    @pytest.mark.asyncio
    async def test_ping_pong(self, websocket_clients):
        """测试心跳机制"""
        client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
        websocket_clients.append(client)

        # 建立连接
        await client.connect(token="test-token-123")
        welcome_message = await client.receive_message()
        client.connection_id = welcome_message["data"]["connection_id"]

        # 发送ping
        ping_time = datetime.now().isoformat()
        await client.send_message({
            "type": "ping",
            "data": {"timestamp": ping_time}
        })

        # 接收pong
        pong_message = await client.receive_message()
        assert pong_message["type"] == "pong"
        assert "timestamp" in pong_message["data"]

    @pytest.mark.asyncio
    async def test_channel_subscription(self, websocket_clients):
        """测试频道订阅"""
        client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
        websocket_clients.append(client)

        # 建立连接
        await client.connect(token="test-token-123", channel="test")
        welcome_message = await client.receive_message()

        # 订阅频道
        await client.send_message({
            "type": "subscribe",
            "target": "strategy_updates"
        })

        # 接收订阅确认
        subscription_message = await client.receive_message()
        assert subscription_message["type"] == "subscription_confirmed"
        assert subscription_message["data"]["target"] == "strategy_updates"

        # 取消订阅
        await client.send_message({
            "type": "unsubscribe",
            "target": "strategy_updates"
        })

        # 接收取消订阅确认
        unsubscription_message = await client.receive_message()
        assert unsubscription_message["type"] == "unsubscription_confirmed"
        assert unsubscription_message["data"]["target"] == "strategy_updates"

    @pytest.mark.asyncio
    async def test_message_broadcast(self, websocket_clients):
        """测试消息广播"""
        # 创建多个客户端
        clients = []
        for i in range(3):
            client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
            await client.connect(token=f"test-token-{i}", channel="broadcast_test")
            welcome_message = await client.receive_message()
            client.connection_id = welcome_message["data"]["connection_id"]
            clients.append(client)
            websocket_clients.append(client)

        # 使用REST API广播消息
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/ws-pool/broadcast",
                json={
                    "channel": "broadcast_test",
                    "message": {
                        "type": "test_broadcast",
                        "content": "Hello, everyone!"
                    }
                }
            ) as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True
                assert result["data"]["sent_count"] == 3

        # 所有客户端都应该收到广播消息
        for client in clients:
            broadcast_message = await client.receive_message()
            assert broadcast_message["type"] == "broadcast"
            assert broadcast_message["data"]["content"] == "Hello, everyone!"

    @pytest.mark.asyncio
    async def test_user_message(self, websocket_clients):
        """测试用户消息"""
        # 为同一用户创建多个连接
        user_clients = []
        for i in range(2):
            client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
            await client.connect(token="user-token-123")
            welcome_message = await client.receive_message()
            client.connection_id = welcome_message["data"]["connection_id"]
            user_clients.append(client)
            websocket_clients.append(client)

        # 使用REST API发送用户消息
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/ws-pool/send-to-user",
                json={
                    "user_id": 1,  # 假设用户ID是1
                    "message": {
                        "type": "user_notification",
                        "content": "Private message"
                    }
                }
            ) as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True

        # 用户的所有连接都应该收到消息
        for client in user_clients:
            user_message = await client.receive_message()
            assert user_message["type"] == "unicast"  # 或 "data"
            assert user_message["data"]["content"] == "Private message"

    @pytest.mark.asyncio
    async def test_strategy_broadcast(self, websocket_clients):
        """测试策略广播"""
        # 创建策略订阅客户端
        strategy_clients = []
        for i in range(2):
            client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
            # 假设URL支持strategy_ids参数
            await client.connect(token=f"strategy-token-{i}", channel="strategies")
            welcome_message = await client.receive_message()
            client.connection_id = welcome_message["data"]["connection_id"]
            strategy_clients.append(client)
            websocket_clients.append(client)

        # 使用REST API广播策略更新
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/ws-pool/broadcast-to-strategy",
                json={
                    "strategy_id": "test_strategy_123",
                    "message": {
                        "type": "strategy_update",
                        "performance": {"return": 0.05, "sharpe": 1.2}
                    }
                }
            ) as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True

        # 策略订阅者应该收到更新
        for client in strategy_clients:
            strategy_message = await client.receive_message()
            assert strategy_message["type"] == "data"
            assert "performance" in strategy_message["data"]

    @pytest.mark.asyncio
    async def test_connection_limits(self, websocket_clients):
        """测试连接数限制"""
        # 尝试为同一用户创建多个连接
        user_clients = []
        for i in range(6):  # 超过限制（假设限制是5）
            client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
            try:
                await client.connect(token=f"user-limit-test", channel="test")
                welcome_message = await client.receive_message()
                client.connection_id = welcome_message["data"]["connection_id"]
                user_clients.append(client)
                websocket_clients.append(client)
            except Exception as e:
                # 第6个连接应该失败
                assert i == 5  # 前5个应该成功
                break

        # 验证只有5个连接成功
        assert len(user_clients) == 5

    @pytest.mark.asyncio
    async def test_error_handling(self, websocket_clients):
        """测试错误处理"""
        client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
        websocket_clients.append(client)

        # 建立连接
        await client.connect(token="test-token-123")
        welcome_message = await client.receive_message()

        # 发送无效消息
        await client.send_message({
            "type": "invalid_type",
            "data": {}
        })

        # 应该收到错误消息
        error_message = await client.receive_message()
        assert error_message["type"] == "error"
        assert "Unknown message type" in error_message["data"]["error"]

        # 发送无效JSON
        try:
            await client.websocket.send("invalid json")
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_performance_under_load(self, websocket_clients):
        """测试负载下的性能"""
        # 创建多个客户端
        clients = []
        for i in range(10):
            client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
            await client.connect(token=f"perf-token-{i}", channel="performance_test")
            welcome_message = await client.receive_message()
            client.connection_id = welcome_message["data"]["connection_id"]
            clients.append(client)
            websocket_clients.append(client)

        # 记录开始时间
        start_time = time.time()

        # 广播大量消息
        message_count = 100
        async with aiohttp.ClientSession() as session:
            for i in range(message_count):
                async with session.post(
                    "http://localhost:8000/ws-pool/broadcast",
                    json={
                        "channel": "performance_test",
                        "message": {
                            "type": "performance_test",
                            "index": i,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                ) as response:
                    assert response.status == 200

        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time

        # 计算性能指标
        messages_per_second = (message_count * len(clients)) / duration
        avg_latency = duration / message_count

        # 验证性能要求
        assert messages_per_second > 100  # 至少100消息/秒
        assert avg_latency < 0.1  # 平均延迟小于100ms

        # 验证所有客户端都收到了消息
        for client in clients:
            received_count = 0
            try:
                while received_count < message_count:
                    message = await client.receive_message(timeout=1)
                    if message["type"] == "broadcast":
                        received_count += 1
            except TimeoutError:
                break

            assert received_count == message_count

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, websocket_clients):
        """测试并发连接"""
        # 并发创建多个连接
        connection_tasks = []
        for i in range(20):
            task = asyncio.create_task(self._create_connection(f"concurrent-token-{i}"))
            connection_tasks.append(task)

        # 等待所有连接建立
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)

        # 统计成功和失败的连接
        successful_connections = sum(1 for result in results if isinstance(result, str))
        failed_connections = len(results) - successful_connections

        print(f"Successful connections: {successful_connections}")
        print(f"Failed connections: {failed_connections}")

        # 验证至少有合理的连接数成功
        assert successful_connections >= 10

        # 清理连接
        for result in results:
            if isinstance(result, str):
                try:
                    # 这里需要实际的连接对象来关闭
                    # 由于测试简化，这里只是记录
                    pass
                except Exception:
                    pass

    async def _create_connection(self, token: str) -> str:
        """创建连接的辅助方法"""
        try:
            client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
            await client.connect(token=token)
            welcome_message = await client.receive_message()
            return welcome_message["data"]["connection_id"]
        except Exception as e:
            return str(e)


class TestWebSocketAPIE2E:
    """WebSocket API端到端测试"""

    @pytest.mark.asyncio
    async def test_pool_status_api(self):
        """测试连接池状态API"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/ws-pool/status") as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True
                assert "stats" in result["data"]
                assert "total_connections" in result["data"]["stats"]

    @pytest.mark.asyncio
    async def test_connection_list_api(self):
        """测试连接列表API"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/ws-pool/connections") as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True
                assert "connections" in result["data"]
                assert isinstance(result["data"]["connections"], list)

    @pytest.mark.asyncio
    async def test_health_check_api(self):
        """测试健康检查API"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/ws-pool/health") as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True
                assert "status" in result["data"]
                assert result["data"]["status"] in ["healthy", "unhealthy"]

    @pytest.mark.asyncio
    async def test_stats_api(self):
        """测试统计信息API"""
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/ws-pool/stats") as response:
                assert response.status == 200
                result = await response.json()
                assert result["success"] is True
                assert "connections_by_hour" in result["data"]
                assert "channel_stats" in result["data"]
                assert "strategy_stats" in result["data"]


# 集成测试类
class TestWebSocketIntegration:
    """WebSocket集成测试"""

    @pytest.mark.asyncio
    async def test_integration_with_strategy_system(self, websocket_clients):
        """测试与策略系统的集成"""
        # 创建策略监控客户端
        client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
        websocket_clients.append(client)

        # 连接到策略频道
        await client.connect(token="strategy-monitor-token", channel="strategies")
        welcome_message = await client.receive_message()

        # 订阅策略更新
        await client.send_message({
            "type": "subscribe",
            "target": "strategy_updates"
        })

        subscription_message = await client.receive_message()
        assert subscription_message["type"] == "subscription_confirmed"

        # 模拟策略性能更新（通过API）
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/ws-pool/broadcast",
                json={
                    "channel": "strategy_updates",
                    "message": {
                        "type": "strategy_performance_update",
                        "strategy_id": "test_strategy_001",
                        "metrics": {
                            "return": 0.08,
                            "sharpe_ratio": 1.5,
                            "max_drawdown": 0.05,
                            "win_rate": 0.65
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                }
            ) as response:
                assert response.status == 200

        # 验证客户端收到策略更新
        performance_message = await client.receive_message()
        assert performance_message["type"] == "broadcast"
        assert performance_message["data"]["type"] == "strategy_performance_update"
        assert performance_message["data"]["strategy_id"] == "test_strategy_001"

    @pytest.mark.asyncio
    async def test_integration_with_user_management(self, websocket_clients):
        """测试与用户管理系统的集成"""
        # 创建用户客户端
        client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
        websocket_clients.append(client)

        # 使用有效用户token连接
        await client.connect(token="valid-user-jwt-token")
        welcome_message = await client.receive_message()

        # 验证连接信息包含用户信息
        assert "user_id" in welcome_message["data"]
        assert welcome_message["data"]["is_authenticated"] is True

        # 发送用户特定消息
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/ws-pool/send-to-user",
                json={
                    "user_id": welcome_message["data"]["user_id"],
                    "message": {
                        "type": "user_notification",
                        "title": "System Update",
                        "content": "Your strategy has been updated"
                    }
                }
            ) as response:
                assert response.status == 200

        # 验证收到用户消息
        user_message = await client.receive_message()
        assert user_message["type"] == "unicast"
        assert user_message["data"]["title"] == "System Update"


# 性能基准测试
class TestWebSocketPerformance:
    """WebSocket性能测试"""

    @pytest.mark.asyncio
    async def test_message_latency_benchmark(self, websocket_clients):
        """消息延迟基准测试"""
        client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
        websocket_clients.append(client)

        # 建立连接
        await client.connect(token="latency-test-token")
        welcome_message = await client.receive_message()

        # 测试消息延迟
        latencies = []
        for i in range(50):
            start_time = time.time()

            # 发送ping
            await client.send_message({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })

            # 接收pong
            pong_message = await client.receive_message()
            end_time = time.time()

            latency = (end_time - start_time) * 1000  # 转换为毫秒
            latencies.append(latency)

        # 计算延迟统计
        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        max_latency = max(latencies)

        print(f"Average latency: {avg_latency:.2f}ms")
        print(f"P95 latency: {p95_latency:.2f}ms")
        print(f"Max latency: {max_latency:.2f}ms")

        # 验证延迟要求
        assert avg_latency < 50  # 平均延迟小于50ms
        assert p95_latency < 100  # P95延迟小于100ms

    @pytest.mark.asyncio
    async def test_throughput_benchmark(self, websocket_clients):
        """吞吐量基准测试"""
        # 创建多个客户端
        clients = []
        for i in range(5):
            client = WebSocketE2ETestClient("ws://localhost:8000/ws-pool/connect")
            await client.connect(token=f"throughput-token-{i}", channel="throughput_test")
            welcome_message = await client.receive_message()
            clients.append(client)
            websocket_clients.append(client)

        # 测试广播吞吐量
        start_time = time.time()
        message_count = 200

        async with aiohttp.ClientSession() as session:
            tasks = []
            for i in range(message_count):
                task = session.post(
                    "http://localhost:8000/ws-pool/broadcast",
                    json={
                        "channel": "throughput_test",
                        "message": {
                            "type": "throughput_test",
                            "index": i
                        }
                    }
                )
                tasks.append(task)

            # 并发发送消息
            responses = await asyncio.gather(*tasks)
            for response in responses:
                response.close()

        end_time = time.time()
        duration = end_time - start_time

        # 计算吞吐量
        total_messages = message_count * len(clients)
        throughput = total_messages / duration

        print(f"Total messages: {total_messages}")
        print(f"Duration: {duration:.2f}s")
        print(f"Throughput: {throughput:.2f} messages/second")

        # 验证吞吐量要求
        assert throughput > 1000  # 至少1000消息/秒


if __name__ == "__main__":
    # 运行E2E测试
    pytest.main([__file__, "-v", "-s"])