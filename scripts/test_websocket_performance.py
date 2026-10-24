#!/usr/bin/env python3
"""
WebSocket连接池性能测试脚本
WebSocket Pool Performance Testing Script

测试WebSocket连接池在不同负载下的性能表现：
- 连接并发测试
- 消息吞吐量测试
- 内存使用测试
- 延迟测试
- 稳定性测试
"""

import asyncio
import json
import time
import statistics
import psutil
import websockets
import aiohttp
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
import queue

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebSocketPerformanceTester:
    """WebSocket性能测试器"""

    def __init__(self, base_url: str = "ws://localhost:8000/ws-pool/connect"):
        self.base_url = base_url
        self.api_base = "http://localhost:8000/ws-pool"
        self.results = {}
        self.process = psutil.Process()

    async def create_connection(self, token: str, channel: str = "default") -> Tuple[str, float]:
        """创建WebSocket连接并测量延迟"""
        start_time = time.time()

        try:
            uri = f"{self.base_url}?token={token}&channel={channel}"
            websocket = await websockets.connect(uri)

            # 接收欢迎消息
            welcome_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_message)

            connection_id = welcome_data["data"]["connection_id"]
            latency = (time.time() - start_time) * 1000  # 转换为毫秒

            return connection_id, latency, websocket

        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return None, float('inf'), None

    async def test_connection_concurrency(self, max_connections: int = 1000) -> Dict[str, Any]:
        """测试连接并发性能"""
        logger.info(f"Testing connection concurrency with {max_connections} connections...")

        results = {
            "total_connections": max_connections,
            "successful_connections": 0,
            "failed_connections": 0,
            "connection_latencies": [],
            "connection_time": 0,
            "memory_usage_mb": 0,
            "cpu_usage_percent": 0
        }

        # 记录初始资源使用
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = self.process.cpu_percent()

        start_time = time.time()

        # 创建连接任务
        tasks = []
        for i in range(max_connections):
            token = f"perf-test-token-{i}"
            task = asyncio.create_task(self.create_connection(token, f"perf_test_{i % 10}"))
            tasks.append(task)

        # 等待所有连接完成
        connection_results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        results["connection_time"] = end_time - start_time

        # 统计结果
        connections = []
        for result in connection_results:
            if isinstance(result, tuple):
                connection_id, latency, websocket = result
                if connection_id:
                    results["successful_connections"] += 1
                    results["connection_latencies"].append(latency)
                    connections.append(websocket)
                else:
                    results["failed_connections"] += 1
            else:
                results["failed_connections"] += 1

        # 记录资源使用
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = self.process.cpu_percent()

        results["memory_usage_mb"] = final_memory - initial_memory
        results["cpu_usage_percent"] = final_cpu - initial_cpu

        # 计算统计信息
        if results["connection_latencies"]:
            results["avg_latency_ms"] = statistics.mean(results["connection_latencies"])
            results["p95_latency_ms"] = np.percentile(results["connection_latencies"], 95)
            results["p99_latency_ms"] = np.percentile(results["connection_latencies"], 99)

        results["connections_per_second"] = results["successful_connections"] / results["connection_time"]

        # 清理连接
        for websocket in connections:
            if websocket:
                await websocket.close()

        logger.info(f"Concurrency test completed: {results['successful_connections']}/{max_connections} successful")
        return results

    async def test_message_throughput(self, num_connections: int = 100, messages_per_connection: int = 100) -> Dict[str, Any]:
        """测试消息吞吐量"""
        logger.info(f"Testing message throughput: {num_connections} connections, {messages_per_connection} messages each...")

        results = {
            "num_connections": num_connections,
            "messages_per_connection": messages_per_connection,
            "total_messages": num_connections * messages_per_connection,
            "sent_messages": 0,
            "received_messages": 0,
            "message_latencies": [],
            "test_duration": 0,
            "throughput_mps": 0
        }

        # 创建连接
        connections = []
        for i in range(num_connections):
            token = f"throughput-token-{i}"
            connection_id, latency, websocket = await self.create_connection(token, "throughput_test")
            if websocket:
                connections.append((websocket, connection_id))

        if not connections:
            logger.error("No connections created for throughput test")
            return results

        logger.info(f"Created {len(connections)} connections for throughput test")

        # 消息发送和接收
        start_time = time.time()

        async def send_receive_messages(websocket: websockets.WebSocketServerProtocol,
                                      connection_id: str, message_count: int):
            """发送和接收消息的协程"""
            local_sent = 0
            local_received = 0
            local_latencies = []

            for i in range(message_count):
                try:
                    # 发送消息
                    message = {
                        "type": "ping",
                        "data": {"index": i, "timestamp": datetime.now().isoformat()}
                    }
                    send_start = time.time()
                    await websocket.send(json.dumps(message))

                    # 接收响应
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    receive_time = time.time()

                    local_sent += 1
                    local_received += 1
                    local_latencies.append((receive_time - send_start) * 1000)  # ms

                except Exception as e:
                    logger.warning(f"Message error for connection {connection_id}: {e}")
                    break

            return local_sent, local_received, local_latencies

        # 并发发送消息
        tasks = []
        for websocket, connection_id in connections:
            task = asyncio.create_task(
                send_receive_messages(websocket, connection_id, messages_per_connection)
            )
            tasks.append(task)

        # 等待所有任务完成
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        results["test_duration"] = end_time - start_time

        # 统计结果
        for result in task_results:
            if isinstance(result, tuple):
                sent, received, latencies = result
                results["sent_messages"] += sent
                results["received_messages"] += received
                results["message_latencies"].extend(latencies)

        # 计算吞吐量
        results["throughput_mps"] = results["received_messages"] / results["test_duration"]

        # 计算延迟统计
        if results["message_latencies"]:
            results["avg_latency_ms"] = statistics.mean(results["message_latencies"])
            results["p95_latency_ms"] = np.percentile(results["message_latencies"], 95)
            results["p99_latency_ms"] = np.percentile(results["message_latencies"], 99)

        # 清理连接
        for websocket, _ in connections:
            await websocket.close()

        logger.info(f"Throughput test completed: {results['received_messages']} messages in {results['test_duration']:.2f}s")
        return results

    async def test_broadcast_performance(self, num_connections: int = 500, num_broadcasts: int = 100) -> Dict[str, Any]:
        """测试广播性能"""
        logger.info(f"Testing broadcast performance: {num_connections} connections, {num_broadcasts} broadcasts...")

        results = {
            "num_connections": num_connections,
            "num_broadcasts": num_broadcasts,
            "total_expected_messages": num_connections * num_broadcasts,
            "received_messages": 0,
            "broadcast_latencies": [],
            "test_duration": 0,
            "broadcast_throughput_mps": 0
        }

        # 创建连接
        connections = []
        for i in range(num_connections):
            token = f"broadcast-token-{i}"
            connection_id, latency, websocket = await self.create_connection(token, "broadcast_test")
            if websocket:
                connections.append(websocket)

        if not connections:
            logger.error("No connections created for broadcast test")
            return results

        logger.info(f"Created {len(connections)} connections for broadcast test")

        # 启动消息接收任务
        received_count = 0
        receive_lock = asyncio.Lock()

        async def receive_messages(websocket: websockets.WebSocketServerProtocol):
            """持续接收消息的协程"""
            nonlocal received_count

            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    async with receive_lock:
                        received_count += 1
            except asyncio.TimeoutError:
                pass  # 测试结束
            except Exception as e:
                logger.warning(f"Receive error: {e}")

        # 启动接收任务
        receive_tasks = []
        for websocket in connections:
            task = asyncio.create_task(receive_messages(websocket))
            receive_tasks.append(task)

        # 等待一小段时间确保接收任务启动
        await asyncio.sleep(0.5)

        # 执行广播测试
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            for i in range(num_broadcasts):
                broadcast_start = time.time()

                async with session.post(
                    f"{self.api_base}/broadcast",
                    json={
                        "channel": "broadcast_test",
                        "message": {
                            "type": "broadcast_test",
                            "index": i,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                ) as response:
                    if response.status == 200:
                        broadcast_latency = (time.time() - broadcast_start) * 1000
                        results["broadcast_latencies"].append(broadcast_latency)

                # 小间隔避免过载
                await asyncio.sleep(0.01)

        # 等待消息接收完成
        await asyncio.sleep(2.0)

        end_time = time.time()
        results["test_duration"] = end_time - start_time
        results["received_messages"] = received_count
        results["broadcast_throughput_mps"] = received_count / results["test_duration"]

        # 取消接收任务
        for task in receive_tasks:
            task.cancel()

        # 清理连接
        for websocket in connections:
            await websocket.close()

        logger.info(f"Broadcast test completed: {received_count} messages received")
        return results

    async def test_memory_leak(self, duration_minutes: int = 10) -> Dict[str, Any]:
        """测试内存泄漏"""
        logger.info(f"Testing memory leak for {duration_minutes} minutes...")

        results = {
            "duration_minutes": duration_minutes,
            "memory_samples": [],
            "connection_counts": [],
            "memory_growth_mb": 0,
            "avg_memory_mb": 0,
            "peak_memory_mb": 0
        }

        start_time = time.time()
        sample_interval = 30  # 每30秒采样一次

        # 创建初始连接
        initial_connections = 50
        connections = []

        for i in range(initial_connections):
            token = f"leak-test-token-{i}"
            connection_id, latency, websocket = await self.create_connection(token, "leak_test")
            if websocket:
                connections.append(websocket)

        # 定期采样
        while time.time() - start_time < duration_minutes * 60:
            # 记录内存使用
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            results["memory_samples"].append(memory_mb)
            results["connection_counts"].append(len(connections))

            # 随机添加/移除连接
            if len(connections) > 100 and np.random.random() < 0.3:
                # 移除一些连接
                remove_count = min(10, len(connections) - 50)
                for _ in range(remove_count):
                    if connections:
                        websocket = connections.pop()
                        await websocket.close()
            elif len(connections) < 200 and np.random.random() < 0.3:
                # 添加一些连接
                add_count = min(10, 200 - len(connections))
                for i in range(add_count):
                    token = f"leak-test-token-{len(connections)+i}"
                    connection_id, latency, websocket = await self.create_connection(token, "leak_test")
                    if websocket:
                        connections.append(websocket)

            await asyncio.sleep(sample_interval)

        # 清理连接
        for websocket in connections:
            await websocket.close()

        # 计算内存增长
        if len(results["memory_samples"]) >= 2:
            initial_memory = results["memory_samples"][0]
            final_memory = results["memory_samples"][-1]
            results["memory_growth_mb"] = final_memory - initial_memory
            results["avg_memory_mb"] = statistics.mean(results["memory_samples"])
            results["peak_memory_mb"] = max(results["memory_samples"])

        logger.info(f"Memory leak test completed: {results['memory_growth_mb']:.2f} MB growth")
        return results

    async def test_stability(self, duration_minutes: int = 30) -> Dict[str, Any]:
        """测试稳定性"""
        logger.info(f"Testing stability for {duration_minutes} minutes...")

        results = {
            "duration_minutes": duration_minutes,
            "error_count": 0,
            "reconnection_count": 0,
            "message_success_rate": 0,
            "uptime_percentage": 0,
            "performance_samples": []
        }

        start_time = time.time()
        end_time = start_time + duration_minutes * 60

        # 维护稳定的连接池
        target_connections = 100
        connections = {}

        async def maintain_connections():
            """维护连接池"""
            while time.time() < end_time:
                try:
                    # 检查连接数量
                    current_count = len(connections)

                    if current_count < target_connections:
                        # 添加连接
                        for i in range(target_connections - current_count):
                            token = f"stability-token-{int(time.time())}-{i}"
                            connection_id, latency, websocket = await self.create_connection(token, "stability_test")
                            if websocket:
                                connections[connection_id] = websocket

                    elif current_count > target_connections:
                        # 移除连接
                        remove_count = min(10, current_count - target_connections)
                        connection_ids = list(connections.keys())[:remove_count]
                        for conn_id in connection_ids:
                            websocket = connections.pop(conn_id)
                            await websocket.close()

                    await asyncio.sleep(5)

                except Exception as e:
                    logger.error(f"Connection maintenance error: {e}")
                    results["error_count"] += 1

        async def send_test_messages():
            """发送测试消息"""
            message_count = 0
            success_count = 0

            while time.time() < end_time:
                try:
                    # 发送心跳消息
                    for connection_id, websocket in list(connections.items()):
                        try:
                            message = {"type": "ping", "timestamp": datetime.now().isoformat()}
                            await websocket.send(json.dumps(message))
                            message_count += 1
                            success_count += 1
                        except Exception:
                            # 连接可能已断开，移除
                            connections.pop(connection_id, None)
                            message_count += 1

                    # 记录性能样本
                    if connections:
                        sample = {
                            "timestamp": time.time(),
                            "connection_count": len(connections),
                            "memory_mb": self.process.memory_info().rss / 1024 / 1024
                        }
                        results["performance_samples"].append(sample)

                    await asyncio.sleep(10)

                except Exception as e:
                    logger.error(f"Message sending error: {e}")
                    results["error_count"] += 1

            if message_count > 0:
                results["message_success_rate"] = (success_count / message_count) * 100

        # 启动维护和消息任务
        maintenance_task = asyncio.create_task(maintain_connections())
        message_task = asyncio.create_task(send_test_messages())

        # 等待测试完成
        await maintenance_task
        await message_task

        # 清理连接
        for websocket in connections.values():
            await websocket.close()

        # 计算稳定性指标
        actual_duration = time.time() - start_time
        results["uptime_percentage"] = (actual_duration / (duration_minutes * 60)) * 100

        logger.info(f"Stability test completed: {results['error_count']} errors, {results['message_success_rate']:.2f}% success rate")
        return results

    def generate_report(self, output_file: str = "websocket_performance_report.html"):
        """生成性能测试报告"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WebSocket Pool Performance Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .section { margin-bottom: 30px; }
                .metric { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
                .good { background: #d4edda; }
                .warning { background: #fff3cd; }
                .error { background: #f8d7da; }
                table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>WebSocket连接池性能测试报告</h1>
            <p>生成时间: {timestamp}</p>

            <div class="section">
                <h2>测试概览</h2>
                <div class="metric">
                    <strong>测试环境:</strong> {environment}
                </div>
                <div class="metric">
                    <strong>测试持续时间:</strong> {total_duration} 分钟
                </div>
            </div>

            <div class="section">
                <h2>连接并发测试</h2>
                {concurrency_results}
            </div>

            <div class="section">
                <h2>消息吞吐量测试</h2>
                {throughput_results}
            </div>

            <div class="section">
                <h2>广播性能测试</h2>
                {broadcast_results}
            </div>

            <div class="section">
                <h2>内存泄漏测试</h2>
                {memory_results}
            </div>

            <div class="section">
                <h2>稳定性测试</h2>
                {stability_results}
            </div>

            <div class="section">
                <h2>性能建议</h2>
                <ul>
                    {recommendations}
                </ul>
            </div>
        </body>
        </html>
        """

        # 填充模板数据
        concurrency_html = self._format_concurrency_results()
        throughput_html = self._format_throughput_results()
        broadcast_html = self._format_broadcast_results()
        memory_html = self._format_memory_results()
        stability_html = self._format_stability_results()
        recommendations = self._generate_recommendations()

        html_content = html_content.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            environment="Development",
            total_duration=sum(self.results.get(r, {}).get("duration_minutes", 0) for r in self.results),
            concurrency_results=concurrency_html,
            throughput_results=throughput_html,
            broadcast_results=broadcast_html,
            memory_results=memory_html,
            stability_results=stability_html,
            recommendations="\n".join(f"<li>{rec}</li>" for rec in recommendations)
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Performance report generated: {output_file}")

    def _format_concurrency_results(self) -> str:
        """格式化并发测试结果"""
        if "concurrency" not in self.results:
            return "<p>未执行并发测试</p>"

        data = self.results["concurrency"]
        success_rate = (data["successful_connections"] / data["total_connections"]) * 100

        status_class = "good" if success_rate >= 95 else "warning" if success_rate >= 80 else "error"

        return f"""
        <div class="metric {status_class}">
            <strong>连接成功率:</strong> {success_rate:.2f}% ({data["successful_connections"]}/{data["total_connections"]})
        </div>
        <div class="metric">
            <strong>平均连接延迟:</strong> {data.get("avg_latency_ms", 0):.2f} ms
        </div>
        <div class="metric">
            <strong>P95连接延迟:</strong> {data.get("p95_latency_ms", 0):.2f} ms
        </div>
        <div class="metric">
            <strong>连接速度:</strong> {data.get("connections_per_second", 0):.2f} 连接/秒
        </div>
        <div class="metric">
            <strong>内存使用:</strong> {data.get("memory_usage_mb", 0):.2f} MB
        </div>
        """

    def _format_throughput_results(self) -> str:
        """格式化吞吐量测试结果"""
        if "throughput" not in self.results:
            return "<p>未执行吞吐量测试</p>"

        data = self.results["throughput"]
        success_rate = (data["received_messages"] / data["total_messages"]) * 100 if data["total_messages"] > 0 else 0

        status_class = "good" if success_rate >= 95 else "warning" if success_rate >= 80 else "error"

        return f"""
        <div class="metric {status_class}">
            <strong>消息成功率:</strong> {success_rate:.2f}% ({data["received_messages"]}/{data["total_messages"]})
        </div>
        <div class="metric">
            <strong>消息吞吐量:</strong> {data.get("throughput_mps", 0):.2f} 消息/秒
        </div>
        <div class="metric">
            <strong>平均消息延迟:</strong> {data.get("avg_latency_ms", 0):.2f} ms
        </div>
        <div class="metric">
            <strong>P95消息延迟:</strong> {data.get("p95_latency_ms", 0):.2f} ms
        </div>
        """

    def _format_broadcast_results(self) -> str:
        """格式化广播测试结果"""
        if "broadcast" not in self.results:
            return "<p>未执行广播测试</p>"

        data = self.results["broadcast"]
        success_rate = (data["received_messages"] / data["total_expected_messages"]) * 100 if data["total_expected_messages"] > 0 else 0

        status_class = "good" if success_rate >= 95 else "warning" if success_rate >= 80 else "error"

        return f"""
        <div class="metric {status_class}">
            <strong>广播消息接收率:</strong> {success_rate:.2f}% ({data["received_messages"]}/{data["total_expected_messages"]})
        </div>
        <div class="metric">
            <strong>广播吞吐量:</strong> {data.get("broadcast_throughput_mps", 0):.2f} 消息/秒
        </div>
        <div class="metric">
            <strong>平均广播延迟:</strong> {statistics.mean(data.get("broadcast_latencies", [0])):.2f} ms
        </div>
        """

    def _format_memory_results(self) -> str:
        """格式化内存测试结果"""
        if "memory_leak" not in self.results:
            return "<p>未执行内存泄漏测试</p>"

        data = self.results["memory_leak"]
        status_class = "good" if data["memory_growth_mb"] < 50 else "warning" if data["memory_growth_mb"] < 100 else "error"

        return f"""
        <div class="metric {status_class}">
            <strong>内存增长:</strong> {data["memory_growth_mb"]:.2f} MB
        </div>
        <div class="metric">
            <strong>平均内存使用:</strong> {data.get("avg_memory_mb", 0):.2f} MB
        </div>
        <div class="metric">
            <strong>峰值内存使用:</strong> {data.get("peak_memory_mb", 0):.2f} MB
        </div>
        """

    def _format_stability_results(self) -> str:
        """格式化稳定性测试结果"""
        if "stability" not in self.results:
            return "<p>未执行稳定性测试</p>"

        data = self.results["stability"]
        status_class = "good" if data["message_success_rate"] >= 99 else "warning" if data["message_success_rate"] >= 95 else "error"

        return f"""
        <div class="metric {status_class}">
            <strong>消息成功率:</strong> {data["message_success_rate"]:.2f}%
        </div>
        <div class="metric">
            <strong>运行时间百分比:</strong> {data["uptime_percentage"]:.2f}%
        </div>
        <div class="metric">
            <strong>错误数量:</strong> {data["error_count"]}
        </div>
        <div class="metric">
            <strong>重连次数:</strong> {data["reconnection_count"]}
        </div>
        """

    def _generate_recommendations(self) -> List[str]:
        """生成性能建议"""
        recommendations = []

        # 检查并发测试结果
        if "concurrency" in self.results:
            data = self.results["concurrency"]
            success_rate = (data["successful_connections"] / data["total_connections"]) * 100
            if success_rate < 95:
                recommendations.append("连接成功率较低，建议增加服务器资源或优化连接处理逻辑")

            if data.get("avg_latency_ms", 0) > 100:
                recommendations.append("连接延迟较高，建议优化网络配置或使用连接复用")

        # 检查吞吐量测试结果
        if "throughput" in self.results:
            data = self.results["throughput"]
            if data.get("throughput_mps", 0) < 1000:
                recommendations.append("消息吞吐量较低，建议优化消息处理算法或增加处理线程")

            if data.get("avg_latency_ms", 0) > 50:
                recommendations.append("消息延迟较高，建议实现消息队列或异步处理")

        # 检查内存测试结果
        if "memory_leak" in self.results:
            data = self.results["memory_leak"]
            if data["memory_growth_mb"] > 100:
                recommendations.append("检测到内存增长过快，建议检查内存泄漏并优化对象生命周期管理")

        # 检查稳定性测试结果
        if "stability" in self.results:
            data = self.results["stability"]
            if data["message_success_rate"] < 99:
                recommendations.append("消息成功率不足99%，建议加强错误处理和重连机制")

            if data["error_count"] > 100:
                recommendations.append("错误数量较多，建议检查系统稳定性并实现更好的错误恢复机制")

        if not recommendations:
            recommendations.append("所有性能指标均表现良好，系统运行正常")

        return recommendations

    async def run_all_tests(self):
        """运行所有性能测试"""
        logger.info("Starting WebSocket performance tests...")

        try:
            # 并发测试
            logger.info("Running connection concurrency test...")
            self.results["concurrency"] = await self.test_connection_concurrency(500)

            # 吞吐量测试
            logger.info("Running message throughput test...")
            self.results["throughput"] = await self.test_message_throughput(100, 50)

            # 广播测试
            logger.info("Running broadcast performance test...")
            self.results["broadcast"] = await self.test_broadcast_performance(200, 50)

            # 内存泄漏测试（缩短时间用于演示）
            logger.info("Running memory leak test...")
            self.results["memory_leak"] = await self.test_memory_leak(2)

            # 稳定性测试（缩短时间用于演示）
            logger.info("Running stability test...")
            self.results["stability"] = await self.test_stability(2)

            # 生成报告
            self.generate_report()

            logger.info("All performance tests completed!")

        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            raise


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="WebSocket连接池性能测试")
    parser.add_argument("--url", default="ws://localhost:8000/ws-pool/connect",
                       help="WebSocket服务器URL")
    parser.add_argument("--test", choices=["all", "concurrency", "throughput", "broadcast", "memory", "stability"],
                       default="all", help="要执行的测试类型")
    parser.add_argument("--report", default="websocket_performance_report.html",
                       help="报告输出文件")

    args = parser.parse_args()

    # 创建测试器
    tester = WebSocketPerformanceTester(args.url)

    try:
        if args.test == "all":
            await tester.run_all_tests()
        elif args.test == "concurrency":
            tester.results["concurrency"] = await tester.test_connection_concurrency(500)
        elif args.test == "throughput":
            tester.results["throughput"] = await tester.test_message_throughput(100, 100)
        elif args.test == "broadcast":
            tester.results["broadcast"] = await tester.test_broadcast_performance(200, 100)
        elif args.test == "memory":
            tester.results["memory_leak"] = await tester.test_memory_leak(5)
        elif args.test == "stability":
            tester.results["stability"] = await tester.test_stability(5)

        # 生成报告
        tester.generate_report(args.report)

    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        raise


if __name__ == "__main__":
    # 运行性能测试
    asyncio.run(main())