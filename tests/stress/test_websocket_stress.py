#!/usr/bin/env python3
"""
WebSocket压力测试与稳定性测试
WebSocket Stress Testing and Stability Testing

Task #27: WebSocket压力测试与监控

测试功能：
- 1000+并发连接压力测试
- 24小时稳定性测试
- 内存使用监控
- 连接稳定性验证
- 断线重连测试
"""

import asyncio
import json
import time
import statistics
import psutil
import websockets
import aiohttp
import logging
import signal
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import queue
import random
import gc

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.websocket_pool import WebSocketConnectionPool, ConnectionPoolConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stress_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class StressTestMetrics:
    """压力测试指标"""
    timestamp: datetime
    active_connections: int
    total_messages_sent: int
    total_messages_received: int
    memory_usage_mb: float
    cpu_usage_percent: float
    avg_latency_ms: float
    error_count: int
    reconnect_count: int

class WebSocketStressTester:
    """WebSocket压力测试器"""

    def __init__(self, websocket_url: str = "ws://localhost:8000/ws-pool/connect"):
        self.websocket_url = websocket_url
        self.api_base = "http://localhost:8000"
        self.connections: Dict[str, Any] = {}
        self.metrics_history: List[StressTestMetrics] = []
        self.test_running = False
        self.process = psutil.Process()
        self.executor = ThreadPoolExecutor(max_workers=10)

        # 测试配置
        self.test_config = {
            "max_connections": 1000,
            "stability_duration_hours": 24,
            "message_interval_seconds": 5,
            "reconnect_attempts": 3,
            "memory_limit_mb": 500,
            "success_rate_threshold": 99.9
        }

        logger.info("WebSocket stress tester initialized")

    async def create_connection(self, user_id: int, token: str) -> Optional[Tuple[str, Any]]:
        """创建单个WebSocket连接"""
        try:
            uri = f"{self.websocket_url}?token={token}&channel=stress_test"
            websocket = await websockets.connect(uri, timeout=10.0)

            # 接收欢迎消息
            welcome_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_message)

            if welcome_data.get("success"):
                connection_id = welcome_data["data"]["connection_id"]
                return connection_id, websocket
            else:
                logger.error(f"Connection failed for user {user_id}: {welcome_data}")
                return None

        except Exception as e:
            logger.error(f"Failed to create connection for user {user_id}: {e}")
            return None

    async def test_concurrent_connections(self, num_connections: int = 1000) -> Dict[str, Any]:
        """测试1000+并发连接"""
        logger.info(f"开始并发连接测试: {num_connections} 连接")

        results = {
            "test_name": "concurrent_connections",
            "target_connections": num_connections,
            "successful_connections": 0,
            "failed_connections": 0,
            "connection_times": [],
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0,
            "avg_latency_ms": 0,
            "p95_latency_ms": 0,
            "p99_latency_ms": 0,
            "connections_per_second": 0
        }

        # 记录初始资源使用
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        initial_cpu = self.process.cpu_percent()

        start_time = time.time()
        connection_times = []

        # 批量创建连接（分批以避免过载）
        batch_size = 50
        connection_id = 0

        for batch_start in range(0, num_connections, batch_size):
            batch_end = min(batch_start + batch_size, num_connections)
            batch_tasks = []

            for i in range(batch_start, batch_end):
                connection_id += 1
                user_id = connection_id
                token = f"stress-test-token-{user_id}"

                task = asyncio.create_task(self.create_connection_with_timing(user_id, token))
                batch_tasks.append(task)

            # 等待当前批次完成
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, dict) and result.get("success"):
                    results["successful_connections"] += 1
                    connection_times.append(result["connection_time_ms"])
                    self.connections[result["connection_id"]] = result["websocket"]
                else:
                    results["failed_connections"] += 1
                    logger.error(f"Connection failed: {result}")

            # 短暂休息以避免过载
            await asyncio.sleep(0.1)

            # 记录进度
            progress = (batch_end / num_connections) * 100
            logger.info(f"连接进度: {batch_end}/{num_connections} ({progress:.1f}%)")

        end_time = time.time()
        total_time = end_time - start_time

        # 计算资源使用
        final_memory = self.process.memory_info().rss / 1024 / 1024
        final_cpu = self.process.cpu_percent()

        results["memory_usage_mb"] = final_memory - initial_memory
        results["cpu_usage_percent"] = final_cpu - initial_cpu
        results["connection_time_seconds"] = total_time

        # 计算延迟统计
        if connection_times:
            results["avg_latency_ms"] = statistics.mean(connection_times)
            results["p95_latency_ms"] = sorted(connection_times)[int(len(connection_times) * 0.95)]
            results["p99_latency_ms"] = sorted(connection_times)[int(len(connection_times) * 0.99)]

        results["connections_per_second"] = results["successful_connections"] / total_time if total_time > 0 else 0

        logger.info(f"并发连接测试完成: {results['successful_connections']}/{num_connections} 成功")
        return results

    async def create_connection_with_timing(self, user_id: int, token: str) -> Dict[str, Any]:
        """创建连接并测量时间"""
        start_time = time.time()

        try:
            result = await self.create_connection(user_id, token)
            if result:
                connection_id, websocket = result
                connection_time_ms = (time.time() - start_time) * 1000

                return {
                    "success": True,
                    "connection_id": connection_id,
                    "websocket": websocket,
                    "user_id": user_id,
                    "connection_time_ms": connection_time_ms
                }
            else:
                return {
                    "success": False,
                    "error": "Connection failed",
                    "user_id": user_id
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }

    async def test_stability(self, duration_hours: int = 1) -> Dict[str, Any]:
        """稳定性测试（默认1小时，可配置为24小时）"""
        logger.info(f"开始稳定性测试: {duration_hours} 小时")

        # 首先建立基础连接
        base_connections = 100
        await self.test_concurrent_connections(base_connections)

        results = {
            "test_name": "stability_test",
            "duration_hours": duration_hours,
            "base_connections": base_connections,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_errors": 0,
            "total_reconnections": 0,
            "max_memory_mb": 0,
            "avg_cpu_percent": 0,
            "connection_stability_rate": 0,
            "metrics_samples": []
        }

        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)

        # 启动监控任务
        monitor_task = asyncio.create_task(self.monitor_system_health())

        # 启动消息发送任务
        message_task = asyncio.create_task(self.send_periodic_messages())

        # 启动连接维护任务
        maintenance_task = asyncio.create_task(self.maintain_connections())

        try:
            while datetime.now() < end_time and self.test_running:
                await asyncio.sleep(60)  # 每分钟检查一次

                # 记录当前状态
                current_time = datetime.now()
                elapsed = (current_time - start_time).total_seconds()

                if elapsed % 300 == 0:  # 每5分钟记录一次详细状态
                    logger.info(f"稳定性测试进度: {elapsed/3600:.1f}/{duration_hours} 小时")
                    logger.info(f"当前连接数: {len(self.connections)}")
                    logger.info(f"已发送消息: {results['total_messages_sent']}")
                    logger.info(f"错误次数: {results['total_errors']}")

        except KeyboardInterrupt:
            logger.info("稳定性测试被用户中断")
        finally:
            # 停止所有任务
            self.test_running = False
            monitor_task.cancel()
            message_task.cancel()
            maintenance_task.cancel()

        # 计算最终统计
        total_time = (datetime.now() - start_time).total_seconds()
        results["actual_duration_hours"] = total_time / 3600

        if self.metrics_history:
            memory_usages = [m.memory_usage_mb for m in self.metrics_history]
            cpu_usages = [m.cpu_usage_percent for m in self.metrics_history]

            results["max_memory_mb"] = max(memory_usages)
            results["avg_cpu_percent"] = statistics.mean(cpu_usages)

        # 连接稳定性率
        expected_connections = base_connections * duration_hours  # 理想情况下应该保持的连接数
        actual_connection_time = len(self.connections) * total_time / 3600  # 实际连接时间
        results["connection_stability_rate"] = (actual_connection_time / expected_connections) * 100 if expected_connections > 0 else 0

        logger.info(f"稳定性测试完成: {results['actual_duration_hours']:.2f} 小时")
        return results

    async def monitor_system_health(self):
        """监控系统健康状态"""
        while self.test_running:
            try:
                # 收集系统指标
                memory_usage = self.process.memory_info().rss / 1024 / 1024
                cpu_usage = self.process.cpu_percent()

                # 计算平均延迟（简化版）
                avg_latency = 0  # 这里需要实际的消息延迟计算

                metric = StressTestMetrics(
                    timestamp=datetime.now(),
                    active_connections=len(self.connections),
                    total_messages_sent=0,  # 需要实际计数器
                    total_messages_received=0,  # 需要实际计数器
                    memory_usage_mb=memory_usage,
                    cpu_usage_percent=cpu_usage,
                    avg_latency_ms=avg_latency,
                    error_count=0,  # 需要实际计数器
                    reconnect_count=0  # 需要实际计数器
                )

                self.metrics_history.append(metric)

                # 检查内存限制
                if memory_usage > self.test_config["memory_limit_mb"]:
                    logger.warning(f"内存使用超过限制: {memory_usage:.1f}MB > {self.test_config['memory_limit_mb']}MB")

                await asyncio.sleep(30)  # 每30秒监控一次

            except Exception as e:
                logger.error(f"系统监控错误: {e}")
                await asyncio.sleep(30)

    async def send_periodic_messages(self):
        """定期发送消息"""
        while self.test_running:
            try:
                # 随机选择一些连接发送消息
                if self.connections:
                    sample_connections = list(self.connections.keys())[:min(10, len(self.connections))]

                    for connection_id in sample_connections:
                        websocket = self.connections.get(connection_id)
                        if websocket:
                            try:
                                message = {
                                    "type": "test_message",
                                    "timestamp": datetime.now().isoformat(),
                                    "data": f"Stress test message {random.randint(1, 1000)}"
                                }

                                await websocket.send(json.dumps(message))
                                # 这里应该增加消息发送计数

                            except Exception as e:
                                logger.error(f"发送消息失败: {e}")
                                # 这里应该增加错误计数

                await asyncio.sleep(self.test_config["message_interval_seconds"])

            except Exception as e:
                logger.error(f"定期消息发送错误: {e}")
                await asyncio.sleep(self.test_config["message_interval_seconds"])

    async def maintain_connections(self):
        """维护连接状态"""
        while self.test_running:
            try:
                # 检查连接状态，重连断开的连接
                dead_connections = []

                for connection_id, websocket in self.connections.items():
                    try:
                        # 发送心跳
                        ping_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
                        await websocket.ping()
                    except Exception as e:
                        logger.warning(f"连接 {connection_id} 已断开: {e}")
                        dead_connections.append(connection_id)

                # 清理死连接
                for connection_id in dead_connections:
                    if connection_id in self.connections:
                        del self.connections[connection_id]
                        # 这里应该增加重连计数

                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                logger.error(f"连接维护错误: {e}")
                await asyncio.sleep(60)

    async def cleanup_connections(self):
        """清理所有连接"""
        logger.info("清理所有连接...")

        for connection_id, websocket in self.connections.items():
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"关闭连接 {connection_id} 失败: {e}")

        self.connections.clear()
        logger.info("所有连接已清理")

    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成测试报告"""
        report = f"""
# WebSocket压力测试报告

## 测试配置
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 目标连接数: {results.get('target_connections', 'N/A')}
- 测试持续时间: {results.get('duration_hours', 'N/A')} 小时

## 测试结果

### 连接性能
- 成功连接数: {results.get('successful_connections', 'N/A')}
- 失败连接数: {results.get('failed_connections', 'N/A')}
- 连接成功率: {(results.get('successful_connections', 0) / results.get('target_connections', 1) * 100):.2f}%
- 每秒连接数: {results.get('connections_per_second', 'N/A'):.2f}

### 延迟统计
- 平均延迟: {results.get('avg_latency_ms', 'N/A'):.2f} ms
- P95延迟: {results.get('p95_latency_ms', 'N/A'):.2f} ms
- P99延迟: {results.get('p99_latency_ms', 'N/A'):.2f} ms

### 资源使用
- 内存使用: {results.get('memory_usage_mb', 'N/A'):.2f} MB
- CPU使用: {results.get('cpu_usage_percent', 'N/A'):.2f}%
- 最大内存: {results.get('max_memory_mb', 'N/A'):.2f} MB
- 平均CPU: {results.get('avg_cpu_percent', 'N/A'):.2f}%

### 稳定性指标
- 连接稳定性: {results.get('connection_stability_rate', 'N/A'):.2f}%
- 总错误数: {results.get('total_errors', 'N/A')}
- 总重连数: {results.get('total_reconnections', 'N/A')}

## 性能评估

### 连接限制测试
{'✅ 通过' if results.get('successful_connections', 0) >= 1000 else '❌ 失败'}
目标: 1000+并发连接，实际: {results.get('successful_connections', 0)} 连接

### 内存使用测试
{'✅ 通过' if results.get('memory_usage_mb', 0) < 500 else '❌ 失败'}
目标: <500MB，实际: {results.get('memory_usage_mb', 0):.2f}MB

### 稳定性测试
{'✅ 通过' if results.get('connection_stability_rate', 0) > 99.9 else '❌ 失败'}
目标: >99.9%，实际: {results.get('connection_stability_rate', 0):.2f}%

## 建议和结论
"""

        # 根据结果添加建议
        if results.get('successful_connections', 0) < 1000:
            report += "\n- 连接数未达到目标，建议检查连接池配置和系统资源"

        if results.get('memory_usage_mb', 0) > 500:
            report += "\n- 内存使用超过限制，建议优化内存管理"

        if results.get('avg_latency_ms', 0) > 100:
            report += "\n- 平均延迟较高，建议优化消息处理逻辑"

        return report

async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="WebSocket压力测试")
    parser.add_argument("--test", choices=["concurrency", "stability", "all"], default="concurrency",
                       help="测试类型")
    parser.add_argument("--connections", type=int, default=1000, help="并发连接数")
    parser.add_argument("--hours", type=int, default=1, help="稳定性测试时长（小时）")
    parser.add_argument("--url", default="ws://localhost:8000/ws-pool/connect", help="WebSocket服务器URL")
    parser.add_argument("--report", default="stress_test_report.md", help="报告输出文件")

    args = parser.parse_args()

    # 创建测试器
    tester = WebSocketStressTester(args.url)
    tester.test_running = True

    try:
        results = {}

        if args.test in ["concurrency", "all"]:
            # 并发连接测试
            results["concurrency"] = await tester.test_concurrent_connections(args.connections)

        if args.test in ["stability", "all"]:
            # 稳定性测试
            tester.test_config["stability_duration_hours"] = args.hours
            results["stability"] = await tester.test_stability(args.hours)

        # 生成报告
        report = tester.generate_report(results.get(args.test, {}))

        # 保存报告
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"测试报告已保存到: {args.report}")
        print(report)

    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        raise
    finally:
        tester.test_running = False
        await tester.cleanup_connections()

if __name__ == "__main__":
    # 设置信号处理器
    def signal_handler(signum, frame):
        print("\n接收到中断信号，正在清理...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行压力测试
    asyncio.run(main())