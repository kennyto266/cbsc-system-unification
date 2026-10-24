#!/usr/bin/env python3
"""
WebSocket连接池基础验证测试
Basic WebSocket Pool Validation

Task #27快速验证核心功能
"""

import asyncio
import json
import time
import psutil
import logging
from typing import Dict, List, Any
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.websocket_pool import WebSocketConnectionPool, ConnectionPoolConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockClientState:
    """模拟WebSocket客户端状态"""
    def __init__(self):
        self.name = "CONNECTED"

class SimpleMockWebSocket:
    """简化的模拟WebSocket"""

    def __init__(self, connection_id: str):
        self.connection_id = connection_id
        self.client_ip = "127.0.0.1"
        self.messages = []
        self.client_state = MockClientState()
        self.closed = False

    async def send_text(self, message: str):
        if not self.closed:
            self.messages.append(message)
            return True
        return False

    async def recv(self):
        if not self.closed:
            return '{"ping": "pong"}'
        return None

    async def ping(self):
        if not self.closed:
            return True
        return False

    async def close(self, code=1000, reason=None):
        self.closed = True
        self.client_state.name = "CLOSED"

async def main():
    """主测试函数"""
    logger.info("开始WebSocket连接池基础验证")

    # 1. 创建连接池配置
    config = ConnectionPoolConfig(
        max_connections_per_user=5,
        max_total_connections=50,
        heartbeat_interval=30,
        health_check_interval=60,
        idle_timeout=300
    )

    # 2. 创建连接池
    pool = WebSocketConnectionPool(config)
    logger.info("✅ WebSocket连接池创建成功")

    # 3. 测试连接限制
    logger.info("测试连接限制...")
    user_id = 1
    connections = []

    # 尝试创建7个连接（超过5个限制）
    for i in range(7):
        mock_ws = SimpleMockWebSocket(f"test_conn_{i}")
        success, conn_id = await pool.add_connection(
            websocket=mock_ws,
            user_id=user_id,
            client_ip="127.0.0.1",
            channel="test"
        )

        if success:
            connections.append((conn_id, mock_ws))
            logger.info(f"连接 {i+1}: 成功 (ID: {conn_id})")
        else:
            logger.info(f"连接 {i+1}: 被拒绝 (符合限制)")

    # 验证只有5个连接成功
    assert len(connections) == 5, f"期望5个连接，实际{len(connections)}个"
    logger.info("✅ 连接限制验证通过")

    # 4. 测试消息发送
    logger.info("测试消息发送...")
    if connections:
        conn_id, websocket = connections[0]
        test_message = {"type": "test", "content": "Hello WebSocket!"}
        success = await pool.send_message(conn_id, test_message)

        assert success, "消息发送失败"
        logger.info("✅ 消息发送验证通过")

    # 5. 测试广播
    logger.info("测试消息广播...")
    broadcast_message = {"type": "broadcast", "content": "Broadcast test"}
    sent_count = await pool.broadcast_to_channel("test", broadcast_message)

    assert sent_count == len(connections), f"广播失败，期望{len(connections)}，实际{sent_count}"
    logger.info("✅ 消息广播验证通过")

    # 6. 测试订阅功能
    logger.info("测试订阅功能...")
    if connections:
        conn_id, _ = connections[0]
        success = await pool.subscribe_to_channel(conn_id, "test_channel")
        assert success, "订阅失败"

        # 验证频道订阅
        pool_stats = pool.get_pool_stats()
        logger.info("✅ 订阅功能验证通过")

    # 7. 测试统计信息
    logger.info("测试统计信息...")
    stats = pool.get_pool_stats()

    logger.info(f"统计信息: {stats}")
    logger.info(f"活跃连接数: {stats.get('active_connections', 0)}")
    logger.info(f"总连接数: {stats.get('total_connections', 0)}")

    # 验证连接池有活动连接
    assert stats.get('active_connections', 0) > 0, "没有活跃连接"
    logger.info("✅ 统计信息验证通过")

    # 8. 测试连接移除
    logger.info("测试连接移除...")
    for conn_id, websocket in connections:
        success = await pool.remove_connection(conn_id)
        assert success, f"移除连接 {conn_id} 失败"
        await websocket.close()

    # 验证所有连接已移除
    final_stats = pool.get_pool_stats()
    assert final_stats["active_connections"] == 0, "连接未完全移除"
    logger.info("✅ 连接移除验证通过")

    # 9. 测试内存使用
    logger.info("检查内存使用...")
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"当前内存使用: {memory_mb:.1f} MB")

    # 验证内存使用在合理范围内（<100MB，考虑到只是测试）
    assert memory_mb < 100, f"内存使用过高: {memory_mb:.1f}MB"
    logger.info("✅ 内存使用验证通过")

    # 10. 生成验证报告
    validation_results = {
        "validation_time": datetime.now().isoformat(),
        "connection_pool_creation": "✅ 通过",
        "connection_limits": "✅ 通过",
        "message_sending": "✅ 通过",
        "message_broadcast": "✅ 通过",
        "subscription_system": "✅ 通过",
        "statistics_tracking": "✅ 通过",
        "connection_removal": "✅ 通过",
        "memory_usage": f"✅ 通过 ({memory_mb:.1f}MB)",
        "overall_status": "✅ 所有验证通过"
    }

    # 保存报告
    with open("websocket_basic_validation.json", "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    logger.info("="*50)
    logger.info("WEBSOCKET连接池基础验证完成")
    logger.info("="*50)

    for test_name, result in validation_results.items():
        logger.info(f"{test_name}: {result}")

    logger.info("✅ WebSocket连接池已准备好进行大规模压力测试")

if __name__ == "__main__":
    asyncio.run(main())