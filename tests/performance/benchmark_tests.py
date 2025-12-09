"""
港股量化交易 AI Agent 系统 - 性能基准测试

测试系统性能、负载能力和稳定性，确保系统能够满足高频交易的要求。
"""

import asyncio
import logging
import pytest
import pytest_asyncio
import time
import statistics
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import uuid
import numpy as np
import pandas as pd

from src.core.message_queue import MessageQueue, Message
from src.models.base import MarketData, TradingSignal, Portfolio, RiskMetrics
from src.agents.coordinator import AgentCoordinator
from src.agents.base_agent import AgentConfig
from src.agents.quantitative_analyst import QuantitativeAnalystAgent
from src.agents.quantitative_trader import QuantitativeTraderAgent
from src.agents.portfolio_manager import PortfolioManagerAgent
from src.agents.risk_analyst import RiskAnalystAgent
from src.agents.data_scientist import DataScientistAgent
from src.agents.quantitative_engineer import QuantitativeEngineerAgent
from src.agents.research_analyst import ResearchAnalystAgent


class PerformanceMetrics:
    """性能指标收集器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.end_time = None
    
    def start_timing(self):
        """开始计时"""
        self.start_time = time.perf_counter()
    
    def end_timing(self):
        """结束计时"""
        self.end_time = time.perf_counter()
        if self.start_time:
            self.metrics['duration'] = self.end_time - self.start_time
    
    def record_metric(self, name: str, value: float):
        """记录性能指标"""
        self.metrics[name] = value
    
    def get_metrics(self) -> Dict[str, float]:
        """获取所有指标"""
        return self.metrics.copy()


class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_cpu = 0.0
        self.baseline_memory = 0.0
    
    def get_baseline(self):
        """获取基线资源使用"""
        self.baseline_cpu = self.process.cpu_percent()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def get_current_usage(self) -> Dict[str, float]:
        """获取当前资源使用"""
        cpu_percent = self.process.cpu_percent()
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        return {
            'cpu_percent': cpu_percent,
            'memory_mb': memory_mb,
            'cpu_delta': cpu_percent - self.baseline_cpu,
            'memory_delta_mb': memory_mb - self.baseline_memory
        }


class TestSystemPerformance:
    """系统性能测试类"""
    
    @pytest.fixture
    def resource_monitor(self):
        """资源监控器fixture"""
        monitor = SystemResourceMonitor()
        monitor.get_baseline()
        return monitor
    
    @pytest.fixture
    def performance_metrics(self):
        """性能指标fixture"""
        return PerformanceMetrics()
    
    @pytest_asyncio.fixture
    async def message_queue(self):
        """消息队列fixture"""
        queue = MessageQueue()
        await queue.initialize()
        yield queue
        await queue.cleanup()
    
    @pytest_asyncio.fixture
    async def coordinator(self, message_queue):
        """协调器fixture"""
        coordinator = AgentCoordinator(message_queue)
        await coordinator.initialize()
        yield coordinator
        await coordinator.cleanup()
    
    def generate_market_data(self, count: int) -> List[MarketData]:
        """生成市场数据"""
        data = []
        base_time = datetime.now()
        
        for i in range(count):
            # 模拟股价波动
            base_price = 25.0 + np.random.normal(0, 0.5)
            
            data.append(MarketData(
                id=str(uuid.uuid4()),
                symbol="2800.HK",
                timestamp=base_time + timedelta(seconds=i),
                open_price=base_price,
                high_price=base_price + np.random.uniform(0, 0.2),
                low_price=base_price - np.random.uniform(0, 0.2),
                close_price=base_price + np.random.normal(0, 0.1),
                volume=int(np.random.uniform(500000, 2000000)),
                vwap=base_price + np.random.normal(0, 0.05)
            ))
        
        return data
    
    def generate_trading_signals(self, count: int) -> List[TradingSignal]:
        """生成交易信号"""
        signals = []
        base_time = datetime.now()
        
        for i in range(count):
            signal_type = np.random.choice(["BUY", "SELL", "HOLD"])
            strength = np.random.uniform(0.5, 1.0)
            
            signals.append(TradingSignal(
                id=str(uuid.uuid4()),
                symbol="2800.HK",
                signal_type=signal_type,
                strength=strength,
                price=25.0 + np.random.normal(0, 0.5),
                timestamp=base_time + timedelta(seconds=i),
                confidence=np.random.uniform(0.6, 0.95),
                reasoning=f"算法信号 {i}"
            ))
        
        return signals
    
    @pytest.mark.asyncio
    async def test_message_queue_throughput(self, message_queue, performance_metrics, resource_monitor):
        """测试消息队列吞吐量"""
        
        performance_metrics.start_timing()
        
        # 生成大量消息
        message_count = 10000
        messages = []
        
        for i in range(message_count):
            message = Message(
                id=str(uuid.uuid4()),
                sender_id="benchmark_sender",
                receiver_id="benchmark_receiver",
                message_type="BENCHMARK_MESSAGE",
                payload={"sequence": i, "data": f"test_data_{i}"},
                timestamp=datetime.now(),
                priority="NORMAL"
            )
            messages.append(message)
        
        # 发送消息
        send_tasks = []
        for message in messages:
            task = asyncio.create_task(message_queue.publish_message(message))
            send_tasks.append(task)
        
        await asyncio.gather(*send_tasks)
        
        performance_metrics.end_timing()
        
        # 记录指标
        duration = performance_metrics.metrics.get('duration', 0)
        throughput = message_count / duration if duration > 0 else 0
        
        performance_metrics.record_metric('message_count', message_count)
        performance_metrics.record_metric('throughput_messages_per_second', throughput)
        
        # 记录资源使用
        resource_usage = resource_monitor.get_current_usage()
        performance_metrics.record_metric('cpu_usage_percent', resource_usage['cpu_percent'])
        performance_metrics.record_metric('memory_usage_mb', resource_usage['memory_mb'])
        
        # 性能断言
        assert throughput > 1000, f"消息队列吞吐量不足: {throughput:.2f} msg/s"
        assert resource_usage['memory_delta_mb'] < 500, f"内存使用过多: {resource_usage['memory_delta_mb']:.2f} MB"
        
        print(f"消息队列吞吐量: {throughput:.2f} msg/s")
        print(f"CPU使用率: {resource_usage['cpu_percent']:.2f}%")
        print(f"内存使用: {resource_usage['memory_mb']:.2f} MB")
    
    @pytest.mark.asyncio
    async def test_agent_message_processing_latency(self, message_queue, performance_metrics):
        """测试Agent消息处理延迟"""
        
        # 创建测试Agent
        config = AgentConfig(
            agent_id="benchmark_agent",
            agent_type="QuantitativeAnalyst",
            status="active"
        )
        
        agent = QuantitativeAnalystAgent(config, message_queue)
        await agent.initialize()
        
        try:
            # 生成测试消息
            message_count = 1000
            messages = self.generate_market_data(message_count)
            
            latencies = []
            
            for market_data in messages:
                message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="benchmark_sender",
                    receiver_id="benchmark_agent",
                    message_type="MARKET_DATA",
                    payload=market_data.dict(),
                    timestamp=datetime.now(),
                    priority="NORMAL"
                )
                
                # 测量处理延迟
                start_time = time.perf_counter()
                await agent.process_message(message)
                end_time = time.perf_counter()
                
                latency = (end_time - start_time) * 1000  # 转换为毫秒
                latencies.append(latency)
            
            # 计算延迟统计
            avg_latency = statistics.mean(latencies)
            p95_latency = np.percentile(latencies, 95)
            p99_latency = np.percentile(latencies, 99)
            max_latency = max(latencies)
            
            performance_metrics.record_metric('avg_latency_ms', avg_latency)
            performance_metrics.record_metric('p95_latency_ms', p95_latency)
            performance_metrics.record_metric('p99_latency_ms', p99_latency)
            performance_metrics.record_metric('max_latency_ms', max_latency)
            
            # 性能断言
            assert avg_latency < 100, f"平均延迟过高: {avg_latency:.2f} ms"
            assert p95_latency < 200, f"95%延迟过高: {p95_latency:.2f} ms"
            assert p99_latency < 500, f"99%延迟过高: {p99_latency:.2f} ms"
            
            print(f"平均延迟: {avg_latency:.2f} ms")
            print(f"95%延迟: {p95_latency:.2f} ms")
            print(f"99%延迟: {p99_latency:.2f} ms")
            print(f"最大延迟: {max_latency:.2f} ms")
            
        finally:
            await agent.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_performance(self, message_queue, performance_metrics, resource_monitor):
        """测试并发Agent性能"""
        
        # 创建多个Agent
        agent_count = 10
        agents = []
        
        for i in range(agent_count):
            config = AgentConfig(
                agent_id=f"concurrent_agent_{i}",
                agent_type="QuantitativeAnalyst",
                status="active"
            )
            
            agent = QuantitativeAnalystAgent(config, message_queue)
            await agent.initialize()
            agents.append(agent)
        
        try:
            performance_metrics.start_timing()
            
            # 为每个Agent生成消息
            messages_per_agent = 100
            total_messages = agent_count * messages_per_agent
            
            # 创建并发任务
            tasks = []
            for i, agent in enumerate(agents):
                agent_messages = self.generate_market_data(messages_per_agent)
                
                for market_data in agent_messages:
                    message = Message(
                        id=str(uuid.uuid4()),
                        sender_id=f"concurrent_sender_{i}",
                        receiver_id=agent.config.agent_id,
                        message_type="MARKET_DATA",
                        payload=market_data.dict(),
                        timestamp=datetime.now(),
                        priority="NORMAL"
                    )
                    
                    task = asyncio.create_task(agent.process_message(message))
                    tasks.append(task)
            
            # 等待所有任务完成
            await asyncio.gather(*tasks, return_exceptions=True)
            
            performance_metrics.end_timing()
            
            # 记录指标
            duration = performance_metrics.metrics.get('duration', 0)
            throughput = total_messages / duration if duration > 0 else 0
            
            performance_metrics.record_metric('concurrent_agent_count', agent_count)
            performance_metrics.record_metric('total_messages', total_messages)
            performance_metrics.record_metric('concurrent_throughput_messages_per_second', throughput)
            
            # 记录资源使用
            resource_usage = resource_monitor.get_current_usage()
            performance_metrics.record_metric('concurrent_cpu_usage_percent', resource_usage['cpu_percent'])
            performance_metrics.record_metric('concurrent_memory_usage_mb', resource_usage['memory_mb'])
            
            # 性能断言
            assert throughput > 500, f"并发吞吐量不足: {throughput:.2f} msg/s"
            assert resource_usage['cpu_percent'] < 90, f"CPU使用率过高: {resource_usage['cpu_percent']:.2f}%"
            
            print(f"并发Agent数量: {agent_count}")
            print(f"总消息数: {total_messages}")
            print(f"并发吞吐量: {throughput:.2f} msg/s")
            print(f"CPU使用率: {resource_usage['cpu_percent']:.2f}%")
            
        finally:
            for agent in agents:
                await agent.cleanup()
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, message_queue, performance_metrics):
        """测试负载下的内存使用"""
        
        # 创建Agent
        config = AgentConfig(
            agent_id="memory_test_agent",
            agent_type="DataScientist",
            status="active"
        )
        
        agent = DataScientistAgent(config, message_queue)
        await agent.initialize()
        
        try:
            # 获取初始内存使用
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            # 发送大量数据
            message_count = 5000
            for i in range(message_count):
                # 创建较大的数据负载
                large_data = {
                    "features": np.random.rand(1000).tolist(),
                    "matrix": np.random.rand(100, 100).tolist(),
                    "sequence": i,
                    "timestamp": datetime.now().isoformat()
                }
                
                message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="memory_test_sender",
                    receiver_id="memory_test_agent",
                    message_type="LARGE_DATA",
                    payload=large_data,
                    timestamp=datetime.now(),
                    priority="NORMAL"
                )
                
                await agent.process_message(message)
                
                # 每1000条消息检查一次内存
                if i % 1000 == 0 and i > 0:
                    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                    memory_delta = current_memory - initial_memory
                    
                    print(f"消息 {i}: 内存增量 {memory_delta:.2f} MB")
            
            # 最终内存检查
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            total_memory_delta = final_memory - initial_memory
            
            performance_metrics.record_metric('initial_memory_mb', initial_memory)
            performance_metrics.record_metric('final_memory_mb', final_memory)
            performance_metrics.record_metric('total_memory_delta_mb', total_memory_delta)
            performance_metrics.record_metric('memory_per_message_kb', (total_memory_delta * 1024) / message_count)
            
            # 内存使用断言
            assert total_memory_delta < 1000, f"内存使用过多: {total_memory_delta:.2f} MB"
            assert (total_memory_delta * 1024) / message_count < 200, f"每条消息内存使用过多"
            
            print(f"初始内存: {initial_memory:.2f} MB")
            print(f"最终内存: {final_memory:.2f} MB")
            print(f"内存增量: {total_memory_delta:.2f} MB")
            print(f"每条消息内存: {(total_memory_delta * 1024) / message_count:.2f} KB")
            
            # 强制垃圾回收
            gc.collect()
            
        finally:
            await agent.cleanup()
    
    @pytest.mark.asyncio
    async def test_sustained_performance(self, message_queue, performance_metrics):
        """测试持续性能"""
        
        # 创建Agent
        config = AgentConfig(
            agent_id="sustained_test_agent",
            agent_type="QuantitativeTrader",
            status="active"
        )
        
        agent = QuantitativeTraderAgent(config, message_queue)
        await agent.initialize()
        
        try:
            # 持续运行测试
            test_duration = 60  # 60秒
            start_time = time.time()
            message_count = 0
            throughput_samples = []
            
            while time.time() - start_time < test_duration:
                batch_start = time.time()
                
                # 发送一批消息
                batch_size = 100
                batch_messages = self.generate_trading_signals(batch_size)
                
                tasks = []
                for signal in batch_messages:
                    message = Message(
                        id=str(uuid.uuid4()),
                        sender_id="sustained_test_sender",
                        receiver_id="sustained_test_agent",
                        message_type="TRADING_SIGNAL",
                        payload=signal.dict(),
                        timestamp=datetime.now(),
                        priority="HIGH"
                    )
                    
                    task = asyncio.create_task(agent.process_message(message))
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                batch_end = time.time()
                batch_duration = batch_end - batch_start
                batch_throughput = batch_size / batch_duration if batch_duration > 0 else 0
                throughput_samples.append(batch_throughput)
                
                message_count += batch_size
                
                # 短暂休息
                await asyncio.sleep(0.1)
            
            # 计算持续性能指标
            total_duration = time.time() - start_time
            avg_throughput = statistics.mean(throughput_samples)
            min_throughput = min(throughput_samples)
            max_throughput = max(throughput_samples)
            throughput_stability = 1 - (statistics.stdev(throughput_samples) / avg_throughput) if avg_throughput > 0 else 0
            
            performance_metrics.record_metric('test_duration_seconds', total_duration)
            performance_metrics.record_metric('total_messages_sustained', message_count)
            performance_metrics.record_metric('avg_throughput_sustained', avg_throughput)
            performance_metrics.record_metric('min_throughput_sustained', min_throughput)
            performance_metrics.record_metric('max_throughput_sustained', max_throughput)
            performance_metrics.record_metric('throughput_stability', throughput_stability)
            
            # 持续性能断言
            assert avg_throughput > 100, f"持续平均吞吐量不足: {avg_throughput:.2f} msg/s"
            assert min_throughput > 50, f"持续最小吞吐量不足: {min_throughput:.2f} msg/s"
            assert throughput_stability > 0.8, f"吞吐量稳定性不足: {throughput_stability:.3f}"
            
            print(f"测试持续时间: {total_duration:.2f} 秒")
            print(f"总消息数: {message_count}")
            print(f"平均吞吐量: {avg_throughput:.2f} msg/s")
            print(f"最小吞吐量: {min_throughput:.2f} msg/s")
            print(f"最大吞吐量: {max_throughput:.2f} msg/s")
            print(f"吞吐量稳定性: {throughput_stability:.3f}")
            
        finally:
            await agent.cleanup()
    
    @pytest.mark.asyncio
    async def test_system_scalability(self, message_queue, performance_metrics):
        """测试系统可扩展性"""
        
        scalability_results = {}
        
        # 测试不同数量的Agent
        agent_counts = [1, 5, 10, 20]
        
        for agent_count in agent_counts:
            print(f"\n测试 {agent_count} 个Agent的可扩展性...")
            
            # 创建Agent
            agents = []
            for i in range(agent_count):
                config = AgentConfig(
                    agent_id=f"scalability_agent_{i}",
                    agent_type="QuantitativeAnalyst",
                    status="active"
                )
                
                agent = QuantitativeAnalystAgent(config, message_queue)
                await agent.initialize()
                agents.append(agent)
            
            try:
                # 性能测试
                messages_per_agent = 100
                total_messages = agent_count * messages_per_agent
                
                start_time = time.perf_counter()
                
                # 创建并发任务
                tasks = []
                for i, agent in enumerate(agents):
                    agent_messages = self.generate_market_data(messages_per_agent)
                    
                    for market_data in agent_messages:
                        message = Message(
                            id=str(uuid.uuid4()),
                            sender_id=f"scalability_sender_{i}",
                            receiver_id=agent.config.agent_id,
                            message_type="MARKET_DATA",
                            payload=market_data.dict(),
                            timestamp=datetime.now(),
                            priority="NORMAL"
                        )
                        
                        task = asyncio.create_task(agent.process_message(message))
                        tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
                
                end_time = time.perf_counter()
                duration = end_time - start_time
                throughput = total_messages / duration if duration > 0 else 0
                
                # 记录结果
                scalability_results[agent_count] = {
                    'throughput': throughput,
                    'duration': duration,
                    'messages_per_second_per_agent': throughput / agent_count if agent_count > 0 else 0
                }
                
                print(f"Agent数量: {agent_count}, 吞吐量: {throughput:.2f} msg/s")
                print(f"每Agent吞吐量: {throughput / agent_count:.2f} msg/s")
                
            finally:
                for agent in agents:
                    await agent.cleanup()
        
        # 分析可扩展性
        throughputs = [results['throughput'] for results in scalability_results.values()]
        per_agent_throughputs = [results['messages_per_second_per_agent'] for results in scalability_results.values()]
        
        # 计算可扩展性指标
        scalability_score = 0
        if len(per_agent_throughputs) > 1:
            # 计算吞吐量随Agent数量增长的比例
            base_throughput = per_agent_throughputs[0]
            for i in range(1, len(per_agent_throughputs)):
                if base_throughput > 0:
                    ratio = per_agent_throughputs[i] / base_throughput
                    scalability_score += ratio
        
        performance_metrics.record_metric('scalability_score', scalability_score)
        performance_metrics.record_metric('max_throughput_achieved', max(throughputs))
        
        # 可扩展性断言
        assert max(throughputs) > 1000, f"最大吞吐量不足: {max(throughputs):.2f} msg/s"
        assert scalability_score > 2, f"可扩展性不足: {scalability_score:.2f}"
        
        print(f"\n可扩展性得分: {scalability_score:.2f}")
        print(f"最大吞吐量: {max(throughputs):.2f} msg/s")
    
    @pytest.mark.asyncio
    async def test_error_recovery_performance(self, message_queue, performance_metrics):
        """测试错误恢复性能"""
        
        # 创建Agent
        config = AgentConfig(
            agent_id="error_recovery_agent",
            agent_type="RiskAnalyst",
            status="active"
        )
        
        agent = RiskAnalystAgent(config, message_queue)
        await agent.initialize()
        
        try:
            # 正常消息处理
            normal_messages = self.generate_market_data(100)
            normal_start = time.perf_counter()
            
            for market_data in normal_messages:
                message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="normal_sender",
                    receiver_id="error_recovery_agent",
                    message_type="MARKET_DATA",
                    payload=market_data.dict(),
                    timestamp=datetime.now(),
                    priority="NORMAL"
                )
                await agent.process_message(message)
            
            normal_end = time.perf_counter()
            normal_duration = normal_end - normal_start
            
            # 错误消息处理
            error_messages = []
            for i in range(100):
                error_message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="error_sender",
                    receiver_id="error_recovery_agent",
                    message_type="ERROR",
                    payload={
                        "error_type": "data_error",
                        "error_message": f"测试错误 {i}",
                        "malformed_data": {"invalid": "data"}
                    },
                    timestamp=datetime.now(),
                    priority="URGENT"
                )
                error_messages.append(error_message)
            
            error_start = time.perf_counter()
            
            for error_message in error_messages:
                await agent.process_message(error_message)
            
            error_end = time.perf_counter()
            error_duration = error_end - error_start
            
            # 错误恢复后的正常处理
            recovery_messages = self.generate_market_data(100)
            recovery_start = time.perf_counter()
            
            for market_data in recovery_messages:
                message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="recovery_sender",
                    receiver_id="error_recovery_agent",
                    message_type="MARKET_DATA",
                    payload=market_data.dict(),
                    timestamp=datetime.now(),
                    priority="NORMAL"
                )
                await agent.process_message(message)
            
            recovery_end = time.perf_counter()
            recovery_duration = recovery_end - recovery_start
            
            # 计算性能指标
            normal_throughput = 100 / normal_duration if normal_duration > 0 else 0
            error_throughput = 100 / error_duration if error_duration > 0 else 0
            recovery_throughput = 100 / recovery_duration if recovery_duration > 0 else 0
            
            performance_degradation = (normal_throughput - recovery_throughput) / normal_throughput if normal_throughput > 0 else 0
            
            performance_metrics.record_metric('normal_throughput', normal_throughput)
            performance_metrics.record_metric('error_throughput', error_throughput)
            performance_metrics.record_metric('recovery_throughput', recovery_throughput)
            performance_metrics.record_metric('performance_degradation_percent', performance_degradation * 100)
            
            # 错误恢复断言
            assert agent.running is True, "Agent在错误处理后停止运行"
            assert performance_degradation < 0.5, f"错误恢复后性能下降过多: {performance_degradation * 100:.2f}%"
            
            print(f"正常处理吞吐量: {normal_throughput:.2f} msg/s")
            print(f"错误处理吞吐量: {error_throughput:.2f} msg/s")
            print(f"恢复后吞吐量: {recovery_throughput:.2f} msg/s")
            print(f"性能下降: {performance_degradation * 100:.2f}%")
            
        finally:
            await agent.cleanup()


class TestLoadTesting:
    """负载测试类"""
    
    @pytest.mark.asyncio
    async def test_high_load_scenario(self, message_queue):
        """测试高负载场景"""
        
        # 创建多个Agent模拟高负载
        agent_count = 50
        agents = []
        
        for i in range(agent_count):
            config = AgentConfig(
                agent_id=f"load_test_agent_{i}",
                agent_type="QuantitativeAnalyst",
                status="active"
            )
            
            agent = QuantitativeAnalystAgent(config, message_queue)
            await agent.initialize()
            agents.append(agent)
        
        try:
            # 高负载测试
            messages_per_agent = 200
            total_messages = agent_count * messages_per_agent
            
            start_time = time.perf_counter()
            
            # 创建大量并发任务
            tasks = []
            for i, agent in enumerate(agents):
                agent_messages = []
                for j in range(messages_per_agent):
                    market_data = MarketData(
                        id=str(uuid.uuid4()),
                        symbol="2800.HK",
                        timestamp=datetime.now(),
                        open_price=25.0 + np.random.normal(0, 0.5),
                        high_price=25.2 + np.random.normal(0, 0.3),
                        low_price=24.8 + np.random.normal(0, 0.3),
                        close_price=25.0 + np.random.normal(0, 0.4),
                        volume=int(np.random.uniform(500000, 2000000)),
                        vwap=25.0 + np.random.normal(0, 0.2)
                    )
                    agent_messages.append(market_data)
                
                for market_data in agent_messages:
                    message = Message(
                        id=str(uuid.uuid4()),
                        sender_id=f"load_test_sender_{i}",
                        receiver_id=agent.config.agent_id,
                        message_type="MARKET_DATA",
                        payload=market_data.dict(),
                        timestamp=datetime.now(),
                        priority="NORMAL"
                    )
                    
                    task = asyncio.create_task(agent.process_message(message))
                    tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            throughput = total_messages / duration if duration > 0 else 0
            
            # 检查错误率
            errors = [r for r in results if isinstance(r, Exception)]
            error_rate = len(errors) / len(results) if results else 0
            
            # 高负载断言
            assert throughput > 1000, f"高负载吞吐量不足: {throughput:.2f} msg/s"
            assert error_rate < 0.01, f"错误率过高: {error_rate * 100:.2f}%"
            
            print(f"高负载测试 - Agent数量: {agent_count}")
            print(f"总消息数: {total_messages}")
            print(f"吞吐量: {throughput:.2f} msg/s")
            print(f"错误率: {error_rate * 100:.2f}%")
            
        finally:
            for agent in agents:
                await agent.cleanup()
    
    @pytest.mark.asyncio
    async def test_stress_testing(self, message_queue):
        """压力测试"""
        
        # 创建Agent
        config = AgentConfig(
            agent_id="stress_test_agent",
            agent_type="DataScientist",
            status="active"
        )
        
        agent = DataScientistAgent(config, message_queue)
        await agent.initialize()
        
        try:
            # 压力测试：发送异常大的消息
            stress_messages = []
            
            for i in range(100):
                # 创建非常大的数据负载
                large_data = {
                    "large_array": np.random.rand(10000).tolist(),
                    "large_matrix": np.random.rand(1000, 1000).tolist(),
                    "nested_data": {
                        "level1": {
                            "level2": {
                                "level3": [f"data_{j}" for j in range(1000)]
                            }
                        }
                    },
                    "sequence": i,
                    "timestamp": datetime.now().isoformat()
                }
                
                message = Message(
                    id=str(uuid.uuid4()),
                    sender_id="stress_test_sender",
                    receiver_id="stress_test_agent",
                    message_type="STRESS_DATA",
                    payload=large_data,
                    timestamp=datetime.now(),
                    priority="NORMAL"
                )
                stress_messages.append(message)
            
            start_time = time.perf_counter()
            
            # 并发发送压力消息
            tasks = []
            for message in stress_messages:
                task = asyncio.create_task(agent.process_message(message))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # 检查错误
            errors = [r for r in results if isinstance(r, Exception)]
            error_rate = len(errors) / len(results) if results else 0
            
            # 压力测试断言
            assert agent.running is True, "Agent在压力测试中崩溃"
            assert error_rate < 0.1, f"压力测试错误率过高: {error_rate * 100:.2f}%"
            
            print(f"压力测试 - 大消息数量: {len(stress_messages)}")
            print(f"处理时间: {duration:.2f} 秒")
            print(f"错误率: {error_rate * 100:.2f}%")
            
        finally:
            await agent.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
