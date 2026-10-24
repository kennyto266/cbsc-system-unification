#!/usr/bin/env python3
"""
Phase 4: 负载测试和高压力测试
Load and Stress Testing System for GPU-to-CPU Migration

This module provides comprehensive load testing and stress testing capabilities
to validate system performance under extreme conditions and high workloads.

Key Features:
- Multi-level load testing (light, moderate, heavy, extreme)
- Stress testing with resource exhaustion scenarios
- Concurrent user simulation
- Memory and CPU stress testing
- Performance degradation analysis
- System resilience validation
- Breakpoint identification and threshold testing
"""

import logging
import time
import threading
import queue
import json
import psutil
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from collections import defaultdict, deque
import multiprocessing
import gc
import os
import signal
import resource
import random
from enum import Enum

logger = logging.getLogger(__name__)

class LoadLevel(Enum):
    """负载级别"""
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"
    EXTREME = "extreme"

class StressType(Enum):
    """压力测试类型"""
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    IO_STRESS = "io_stress"
    NETWORK_STRESS = "network_stress"
    CONCURRENT_USERS = "concurrent_users"
    MIXED_STRESS = "mixed_stress"

@dataclass
class LoadTestProfile:
    """负载测试配置"""
    level: LoadLevel
    duration_seconds: int
    concurrent_users: int
    requests_per_second: int
    data_size_multiplier: float
    memory_pressure_gb: float
    cpu_usage_target: float
    expected_response_time_ms: float
    error_rate_threshold: float

@dataclass
class StressTestMetrics:
    """压力测试指标"""
    test_id: str
    test_type: str
    start_time: float
    end_time: float
    duration_seconds: float
    max_cpu_usage: float
    avg_cpu_usage: float
    max_memory_usage_mb: float
    avg_memory_usage_mb: float
    peak_memory_usage_mb: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time_ms: float
    max_response_time_ms: float
    throughput_requests_per_sec: float
    system_stability_score: float
    resilience_score: float

@dataclass
class SystemResourceMetrics:
    """系统资源指标"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    open_files: int
    threads_count: int
    processes_count: int

class LoadGenerator:
    """负载生成器"""

    def __init__(self):
        self.active_generators = []
        self.stop_events = []

    def generate_cpu_load(self, target_usage: float, duration_seconds: int, cores: int = None) -> threading.Thread:
        """生成CPU负载"""
        if cores is None:
            cores = multiprocessing.cpu_count()

        stop_event = threading.Event()

        def cpu_stress_worker():
            """CPU压力工作线程"""
            while not stop_event.is_set():
                # CPU密集型计算
                _ = [i**2 for i in range(1000000)]
                time.sleep(0.001)

        # 启动多个工作线程
        threads = []
        for _ in range(cores):
            thread = threading.Thread(target=cpu_stress_worker, daemon=True)
            thread.start()
            threads.append(thread)

        self.active_generators.extend(threads)
        self.stop_events.append(stop_event)

        return threads[0]

    def generate_memory_load(self, target_gb: float, duration_seconds: int) -> threading.Thread:
        """生成内存负载"""
        stop_event = threading.Event()
        memory_blocks = []

        def memory_stress_worker():
            """内存压力工作线程"""
            try:
                # 分配内存块
                block_size_mb = 100
                num_blocks = int(target_gb * 1024 / block_size_mb)

                for i in range(num_blocks):
                    if stop_event.is_set():
                        break
                    # 分配内存块
                    block = np.random.rand(block_size_mb * 1024 * 256)  # 100MB的随机数组
                    memory_blocks.append(block)

                # 定期访问内存以保持占用
                while not stop_event.is_set():
                    for block in memory_blocks[:10]:  # 访问前10个块
                        _ = np.sum(block)
                    time.sleep(0.1)

            except MemoryError:
                logger.warning("Memory allocation failed during stress test")

        thread = threading.Thread(target=memory_stress_worker, daemon=True)
        thread.start()

        self.active_generators.append(thread)
        self.stop_events.append(stop_event)

        return thread

    def generate_io_load(self, duration_seconds: int, file_size_mb: int = 100) -> threading.Thread:
        """生成IO负载"""
        stop_event = threading.Event()
        temp_dir = Path("stress_test_temp")
        temp_dir.mkdir(exist_ok=True)

        def io_stress_worker():
            """IO压力工作线程"""
            try:
                while not stop_event.is_set():
                    # 写入文件
                    test_file = temp_dir / f"io_stress_{time.time()}.tmp"
                    data = np.random.rand(file_size_mb * 1024 * 256)  # 生成随机数据
                    np.save(test_file, data)

                    # 读取文件
                    _ = np.load(test_file)

                    # 删除文件
                    test_file.unlink()

                    time.sleep(0.1)

            except Exception as e:
                logger.error(f"IO stress test error: {e}")

        thread = threading.Thread(target=io_stress_worker, daemon=True)
        thread.start()

        self.active_generators.append(thread)
        self.stop_events.append(stop_event)

        return thread

    def stop_all_loads(self):
        """停止所有负载生成器"""
        for stop_event in self.stop_events:
            stop_event.set()

        # 等待线程结束
        for thread in self.active_generators:
            if thread.is_alive():
                thread.join(timeout=2.0)

        # 清理
        self.active_generators.clear()
        self.stop_events.clear()

        # 删除临时文件
        temp_dir = Path("stress_test_temp")
        if temp_dir.exists():
            for file in temp_dir.glob("*.tmp"):
                file.unlink()
            temp_dir.rmdir()

class LoadStressTester:
    """负载和压力测试器"""

    def __init__(
        self,
        output_dir: str = "load_stress_test_results",
        max_duration_seconds: int = 3600,
        memory_limit_gb: float = 8.0
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.max_duration_seconds = max_duration_seconds
        self.memory_limit_gb = memory_limit_gb
        self.memory_limit_bytes = memory_limit_gb * 1024 * 1024 * 1024

        # 组件初始化
        self.load_generator = LoadGenerator()
        self.system_monitor = None
        self.monitoring_active = False

        # 测试状态
        self.current_test_id = None
        self.test_results = []
        self.resource_metrics_history = deque(maxlen=10000)

        # 测试配置
        self.load_profiles = self._initialize_load_profiles()

        logger.info("Load and Stress Tester initialized")

    def _initialize_load_profiles(self) -> Dict[LoadLevel, LoadTestProfile]:
        """初始化负载测试配置"""
        return {
            LoadLevel.LIGHT: LoadTestProfile(
                level=LoadLevel.LIGHT,
                duration_seconds=300,  # 5分钟
                concurrent_users=10,
                requests_per_second=50,
                data_size_multiplier=1.0,
                memory_pressure_gb=1.0,
                cpu_usage_target=30.0,
                expected_response_time_ms=100.0,
                error_rate_threshold=0.01
            ),
            LoadLevel.MODERATE: LoadTestProfile(
                level=LoadLevel.MODERATE,
                duration_seconds=600,  # 10分钟
                concurrent_users=50,
                requests_per_second=200,
                data_size_multiplier=2.0,
                memory_pressure_gb=2.0,
                cpu_usage_target=60.0,
                expected_response_time_ms=200.0,
                error_rate_threshold=0.02
            ),
            LoadLevel.HEAVY: LoadTestProfile(
                level=LoadLevel.HEAVY,
                duration_seconds=900,  # 15分钟
                concurrent_users=100,
                requests_per_second=500,
                data_size_multiplier=5.0,
                memory_pressure_gb=4.0,
                cpu_usage_target=80.0,
                expected_response_time_ms=500.0,
                error_rate_threshold=0.05
            ),
            LoadLevel.EXTREME: LoadTestProfile(
                level=LoadLevel.EXTREME,
                duration_seconds=1200,  # 20分钟
                concurrent_users=200,
                requests_per_second=1000,
                data_size_multiplier=10.0,
                memory_pressure_gb=6.0,
                cpu_usage_target=95.0,
                expected_response_time_ms=1000.0,
                error_rate_threshold=0.10
            )
        }

    def run_load_test(self, level: LoadLevel) -> StressTestMetrics:
        """运行负载测试"""
        logger.info(f"Starting {level.value} load test...")

        test_id = f"load_test_{level.value}_{int(time.time())}"
        profile = self.load_profiles[level]

        # 验证系统资源
        if not self._validate_system_resources(profile):
            raise RuntimeError(f"Insufficient system resources for {level.value} load test")

        # 开始测试
        start_time = time.time()

        try:
            # 启动系统监控
            self._start_system_monitoring()

            # 生成负载
            load_threads = self._generate_load(profile)

            # 运行测试工作负载
            workload_results = self._execute_workload(profile)

            # 停止负载生成
            self.load_generator.stop_all_loads()

            # 停止监控
            self._stop_system_monitoring()

            end_time = time.time()
            duration = end_time - start_time

            # 计算测试指标
            metrics = self._calculate_test_metrics(test_id, "load_test", start_time, end_time, workload_results)

            # 保存测试结果
            self._save_test_results(metrics)

            logger.info(f"Load test completed: {metrics.throughput_requests_per_sec:.2f} req/s, "
                       f"Error rate: {metrics.error_rate:.2%}")

            return metrics

        except Exception as e:
            self.load_generator.stop_all_loads()
            self._stop_system_monitoring()
            logger.error(f"Load test failed: {e}")
            raise

    def run_stress_test(self, stress_type: StressType, intensity: float = 1.0) -> StressTestMetrics:
        """运行压力测试"""
        logger.info(f"Starting {stress_type.value} stress test...")

        test_id = f"stress_test_{stress_type.value}_{int(time.time())}"
        start_time = time.time()

        try:
            # 启动系统监控
            self._start_system_monitoring()

            # 执行压力测试
            if stress_type == StressType.CPU_STRESS:
                test_results = self._run_cpu_stress_test(intensity)
            elif stress_type == StressType.MEMORY_STRESS:
                test_results = self._run_memory_stress_test(intensity)
            elif stress_type == StressType.IO_STRESS:
                test_results = self._run_io_stress_test(intensity)
            elif stress_type == StressType.CONCURRENT_USERS:
                test_results = self._run_concurrent_users_test(intensity)
            elif stress_type == StressType.MIXED_STRESS:
                test_results = self._run_mixed_stress_test(intensity)
            else:
                raise ValueError(f"Unsupported stress type: {stress_type}")

            end_time = time.time()

            # 停止监控
            self._stop_system_monitoring()

            # 计算测试指标
            metrics = self._calculate_test_metrics(test_id, stress_type.value, start_time, end_time, test_results)

            # 保存测试结果
            self._save_test_results(metrics)

            logger.info(f"Stress test completed: {stress_type.value}")

            return metrics

        except Exception as e:
            self.load_generator.stop_all_loads()
            self._stop_system_monitoring()
            logger.error(f"Stress test failed: {e}")
            raise

    def run_breakpoint_test(self) -> Dict[str, Any]:
        """运行断点测试，找出系统极限"""
        logger.info("Starting breakpoint test...")

        test_id = f"breakpoint_test_{int(time.time())}"
        results = {
            'test_id': test_id,
            'breakpoints': {},
            'system_limits': {}
        }

        try:
            # CPU断点测试
            cpu_breakpoint = self._find_cpu_breakpoint()
            results['breakpoints']['cpu_max_concurrent'] = cpu_breakpoint

            # 内存断点测试
            memory_breakpoint = self._find_memory_breakpoint()
            results['breakpoints']['memory_max_gb'] = memory_breakpoint

            # 并发断点测试
            concurrent_breakpoint = self._find_concurrent_breakpoint()
            results['breakpoints']['max_concurrent_operations'] = concurrent_breakpoint

            # 数据量断点测试
            data_breakpoint = self._find_data_size_breakpoint()
            results['breakpoints']['max_data_size_mb'] = data_breakpoint

            # 记录系统限制
            results['system_limits'] = {
                'cpu_cores': multiprocessing.cpu_count(),
                'total_memory_gb': psutil.virtual_memory().total / (1024**3),
                'available_memory_gb': psutil.virtual_memory().available / (1024**3),
                'disk_space_gb': psutil.disk_usage('/').free / (1024**3)
            }

            # 保存断点测试结果
            self._save_breakpoint_results(results)

            logger.info(f"Breakpoint test completed: {results['breakpoints']}")
            return results

        except Exception as e:
            logger.error(f"Breakpoint test failed: {e}")
            raise

    def _validate_system_resources(self, profile: LoadTestProfile) -> bool:
        """验证系统资源是否足够"""
        available_memory_gb = psutil.virtual_memory().available / (1024**3)

        if profile.memory_pressure_gb > available_memory_gb * 0.9:  # 留10%安全边际
            logger.warning(f"Insufficient memory: need {profile.memory_pressure_gb}GB, "
                         f"available {available_memory_gb}GB")
            return False

        if profile.cpu_usage_target > 95:  # CPU使用率目标过高
            logger.warning(f"CPU usage target too high: {profile.cpu_usage_target}%")
            return False

        return True

    def _generate_load(self, profile: LoadTestProfile) -> List[threading.Thread]:
        """生成测试负载"""
        threads = []

        # CPU负载
        if profile.cpu_usage_target > 30:
            cpu_thread = self.load_generator.generate_cpu_load(
                target_usage=profile.cpu_usage_target,
                duration_seconds=profile.duration_seconds
            )
            threads.append(cpu_thread)

        # 内存负载
        if profile.memory_pressure_gb > 0:
            memory_thread = self.load_generator.generate_memory_load(
                target_gb=profile.memory_pressure_gb,
                duration_seconds=profile.duration_seconds
            )
            threads.append(memory_thread)

        # IO负载（用于heavy和extreme测试）
        if profile.level in [LoadLevel.HEAVY, LoadLevel.EXTREME]:
            io_thread = self.load_generator.generate_io_load(
                duration_seconds=profile.duration_seconds
            )
            threads.append(io_thread)

        return threads

    def _execute_workload(self, profile: LoadTestProfile) -> Dict[str, Any]:
        """执行工作负载"""
        workload_results = {
            'requests': [],
            'start_time': time.time(),
            'end_time': None
        }

        # 模拟并发用户请求
        def user_request(user_id: int):
            """模拟用户请求"""
            request_start = time.time()

            try:
                # 模拟计算任务
                data_size = int(1000 * profile.data_size_multiplier)
                computation_time = random.uniform(0.01, 0.1)  # 10-100ms计算时间

                # 执行计算
                result = sum([i**2 for i in range(data_size)])
                time.sleep(computation_time)

                request_end = time.time()
                response_time = (request_end - request_start) * 1000  # 毫秒

                return {
                    'user_id': user_id,
                    'success': True,
                    'response_time_ms': response_time,
                    'timestamp': request_start
                }

            except Exception as e:
                request_end = time.time()
                return {
                    'user_id': user_id,
                    'success': False,
                    'response_time_ms': (request_end - request_start) * 1000,
                    'timestamp': request_start,
                    'error': str(e)
                }

        # 使用线程池模拟并发用户
        with ThreadPoolExecutor(max_workers=profile.concurrent_users) as executor:
            futures = []

            # 生成请求
            total_requests = profile.requests_per_second * profile.duration_seconds
            request_interval = 1.0 / profile.requests_per_second

            for i in range(int(total_requests)):
                user_id = i % profile.concurrent_users
                future = executor.submit(user_request, user_id)
                futures.append(future)

                # 控制请求频率
                time.sleep(request_interval)

            # 收集结果
            for future in as_completed(futures, timeout=profile.duration_seconds + 60):
                try:
                    result = future.result()
                    workload_results['requests'].append(result)
                except Exception as e:
                    logger.warning(f"Request failed: {e}")

        workload_results['end_time'] = time.time()
        return workload_results

    def _run_cpu_stress_test(self, intensity: float) -> Dict[str, Any]:
        """运行CPU压力测试"""
        duration = int(300 * intensity)  # 5分钟基础，按强度调整
        target_usage = min(95, 50 * intensity)  # 50%基础，按强度调整

        # 启动CPU压力
        cpu_thread = self.load_generator.generate_cpu_load(
            target_usage=target_usage,
            duration_seconds=duration
        )

        # 执行计算任务
        test_results = {
            'computation_tasks': [],
            'start_time': time.time()
        }

        for i in range(100):
            task_start = time.time()

            # 执行CPU密集型任务
            result = sum([j**2 for j in range(100000)])

            task_end = time.time()
            test_results['computation_tasks'].append({
                'task_id': i,
                'execution_time_ms': (task_end - task_start) * 1000,
                'success': True,
                'timestamp': task_start
            })

        test_results['end_time'] = time.time()
        return test_results

    def _run_memory_stress_test(self, intensity: float) -> Dict[str, Any]:
        """运行内存压力测试"""
        target_memory_gb = min(6, 2 * intensity)  # 2GB基础，按强度调整
        duration = int(300 * intensity)

        # 启动内存压力
        memory_thread = self.load_generator.generate_memory_load(
            target_gb=target_memory_gb,
            duration_seconds=duration
        )

        # 执行内存密集型任务
        test_results = {
            'memory_tasks': [],
            'start_time': time.time()
        }

        try:
            # 分配大数组
            large_arrays = []
            for i in range(10):
                array = np.random.rand(1000000)  # 1百万个随机数
                large_arrays.append(array)

                task_start = time.time()
                # 对数组进行操作
                result = np.sum(array)
                task_end = time.time()

                test_results['memory_tasks'].append({
                    'task_id': i,
                    'execution_time_ms': (task_end - task_start) * 1000,
                    'success': True,
                    'timestamp': task_start,
                    'array_size_mb': array.nbytes / (1024 * 1024)
                })

        except MemoryError:
            logger.warning("Memory stress test hit memory limit")

        test_results['end_time'] = time.time()
        return test_results

    def _run_io_stress_test(self, intensity: float) -> Dict[str, Any]:
        """运行IO压力测试"""
        duration = int(300 * intensity)

        # 启动IO压力
        io_thread = self.load_generator.generate_io_load(
            duration_seconds=duration
        )

        # 执行IO密集型任务
        test_results = {
            'io_tasks': [],
            'start_time': time.time()
        }

        temp_dir = Path("io_stress_test_temp")
        temp_dir.mkdir(exist_ok=True)

        try:
            for i in range(50):
                task_start = time.time()

                # 文件读写操作
                test_file = temp_dir / f"io_test_{i}.dat"
                data = np.random.rand(100000)  # 100k数据点

                # 写入
                np.save(test_file, data)

                # 读取
                loaded_data = np.load(test_file)

                # 验证
                is_valid = np.allclose(data, loaded_data)

                # 删除
                test_file.unlink()

                task_end = time.time()
                test_results['io_tasks'].append({
                    'task_id': i,
                    'execution_time_ms': (task_end - task_start) * 1000,
                    'success': is_valid,
                    'timestamp': task_start,
                    'data_size_kb': data.nbytes / 1024
                })

        except Exception as e:
            logger.error(f"IO stress test error: {e}")

        finally:
            # 清理临时目录
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    file.unlink()
                temp_dir.rmdir()

        test_results['end_time'] = time.time()
        return test_results

    def _run_concurrent_users_test(self, intensity: float) -> Dict[str, Any]:
        """运行并发用户测试"""
        concurrent_users = int(50 * intensity)
        duration = int(300 * intensity)

        # 模拟并发用户
        test_results = {
            'user_sessions': [],
            'start_time': time.time()
        }

        def user_session(user_id: int):
            """模拟用户会话"""
            session_start = time.time()

            try:
                # 模拟用户操作序列
                operations = ['login', 'query', 'compute', 'save', 'logout']
                session_results = []

                for operation in operations:
                    op_start = time.time()

                    # 模拟操作延迟
                    time.sleep(random.uniform(0.05, 0.2))

                    op_end = time.time()
                    session_results.append({
                        'operation': operation,
                        'execution_time_ms': (op_end - op_start) * 1000,
                        'success': True
                    })

                session_end = time.time()
                return {
                    'user_id': user_id,
                    'session_duration_ms': (session_end - session_start) * 1000,
                    'operations': session_results,
                    'success': True
                }

            except Exception as e:
                session_end = time.time()
                return {
                    'user_id': user_id,
                    'session_duration_ms': (session_end - session_start) * 1000,
                    'operations': [],
                    'success': False,
                    'error': str(e)
                }

        # 使用线程池模拟并发用户
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(user_session, user_id)
                for user_id in range(concurrent_users)
            ]

            for future in as_completed(futures, timeout=duration + 60):
                try:
                    session_result = future.result()
                    test_results['user_sessions'].append(session_result)
                except Exception as e:
                    logger.warning(f"User session failed: {e}")

        test_results['end_time'] = time.time()
        return test_results

    def _run_mixed_stress_test(self, intensity: float) -> Dict[str, Any]:
        """运行混合压力测试"""
        duration = int(300 * intensity)
        test_results = {
            'mixed_tasks': [],
            'start_time': time.time()
        }

        # 启动各种负载
        cpu_thread = self.load_generator.generate_cpu_load(
            target_usage=60 * intensity,
            duration_seconds=duration
        )
        memory_thread = self.load_generator.generate_memory_load(
            target_gb=2 * intensity,
            duration_seconds=duration
        )
        io_thread = self.load_generator.generate_io_load(
            duration_seconds=duration
        )

        # 执行混合任务
        for i in range(50):
            task_start = time.time()

            try:
                # CPU任务
                cpu_result = sum([j**2 for j in range(50000)])

                # 内存任务
                memory_array = np.random.rand(100000)
                memory_result = np.sum(memory_array)

                # IO任务（简化版）
                temp_file = Path("mixed_test.tmp")
                temp_file.write_text(f"test_data_{i}_{cpu_result}_{memory_result}")
                file_content = temp_file.read_text()
                temp_file.unlink()

                task_end = time.time()
                test_results['mixed_tasks'].append({
                    'task_id': i,
                    'execution_time_ms': (task_end - task_start) * 1000,
                    'success': True,
                    'timestamp': task_start
                })

            except Exception as e:
                task_end = time.time()
                test_results['mixed_tasks'].append({
                    'task_id': i,
                    'execution_time_ms': (task_end - task_start) * 1000,
                    'success': False,
                    'timestamp': task_start,
                    'error': str(e)
                })

        test_results['end_time'] = time.time()
        return test_results

    def _find_cpu_breakpoint(self) -> int:
        """找出CPU断点"""
        logger.info("Finding CPU breakpoint...")

        max_concurrent = multiprocessing.cpu_count() * 4
        breakpoint = multiprocessing.cpu_count()  # 从核心数开始测试

        for concurrent_processes in range(multiprocessing.cpu_count(), max_concurrent + 1):
            try:
                # 启动系统监控
                self._start_system_monitoring()

                # 启动CPU负载
                threads = []
                for _ in range(concurrent_processes):
                    thread = self.load_generator.generate_cpu_load(
                        target_usage=100,
                        duration_seconds=30
                    )
                    threads.append(thread)

                time.sleep(20)  # 等待负载稳定

                # 检查系统响应性
                start_time = time.time()
                _ = sum([i**2 for i in range(10000)])
                response_time = time.time() - start_time

                self.load_generator.stop_all_loads()
                self._stop_system_monitoring()

                # 如果响应时间超过阈值，达到断点
                if response_time > 1.0:  # 1秒响应时间阈值
                    breakpoint = concurrent_processes - 1
                    break

                breakpoint = concurrent_processes

            except Exception as e:
                logger.warning(f"CPU breakpoint test failed at {concurrent_processes}: {e}")
                self.load_generator.stop_all_loads()
                self._stop_system_monitoring()
                breakpoint = concurrent_processes - 1
                break

        return breakpoint

    def _find_memory_breakpoint(self) -> float:
        """找出内存断点"""
        logger.info("Finding memory breakpoint...")

        available_memory_gb = psutil.virtual_memory().available / (1024**3)
        test_step = 0.5  # 0.5GB步进
        max_memory_gb = min(available_memory_gb * 0.9, 7.0)  # 最多7GB，保留90%安全边际
        breakpoint = 0.0

        for memory_gb in np.arange(test_step, max_memory_gb + test_step, test_step):
            try:
                # 启动内存负载
                memory_thread = self.load_generator.generate_memory_load(
                    target_gb=memory_gb,
                    duration_seconds=30
                )

                time.sleep(20)  # 等待内存分配稳定

                # 检查系统响应性
                start_time = time.time()
                test_array = np.random.rand(1000)
                _ = np.sum(test_array)
                response_time = time.time() - start_time

                self.load_generator.stop_all_loads()

                # 如果响应时间过长或出现内存错误，达到断点
                if response_time > 2.0:  # 2秒响应时间阈值
                    breakpoint = memory_gb - test_step
                    break

                breakpoint = memory_gb

            except Exception as e:
                logger.warning(f"Memory breakpoint test failed at {memory_gb}GB: {e}")
                self.load_generator.stop_all_loads()
                breakpoint = memory_gb - test_step
                break

        return max(0, breakpoint)

    def _find_concurrent_breakpoint(self) -> int:
        """找出并发断点"""
        logger.info("Finding concurrent operations breakpoint...")

        # 从较低的并发数开始测试
        test_concurrent_values = [10, 20, 50, 100, 200, 500, 1000]
        breakpoint = 0

        for concurrent_ops in test_concurrent_values:
            try:
                # 模拟并发操作
                def dummy_operation(op_id):
                    start_time = time.time()
                    result = sum([i**2 for i in range(10000)])
                    return {
                        'op_id': op_id,
                        'execution_time_ms': (time.time() - start_time) * 1000,
                        'success': True
                    }

                with ThreadPoolExecutor(max_workers=concurrent_ops) as executor:
                    futures = [
                        executor.submit(dummy_operation, i)
                        for i in range(concurrent_ops)
                    ]

                    # 等待所有操作完成
                    start_time = time.time()
                    results = []
                    for future in as_completed(futures, timeout=60):
                        try:
                            result = future.result()
                            results.append(result)
                        except Exception as e:
                            logger.warning(f"Operation failed: {e}")

                    total_time = time.time() - start_time

                # 计算平均响应时间
                if results:
                    avg_response_time = np.mean([r['execution_time_ms'] for r in results])

                    # 如果平均响应时间超过阈值，达到断点
                    if avg_response_time > 500:  # 500ms平均响应时间阈值
                        breakpoint = concurrent_ops // 2
                        break

                    breakpoint = concurrent_ops
                else:
                    breakpoint = concurrent_ops // 2
                    break

            except Exception as e:
                logger.warning(f"Concurrent breakpoint test failed at {concurrent_ops}: {e}")
                breakpoint = concurrent_ops // 2
                break

        return breakpoint

    def _find_data_size_breakpoint(self) -> int:
        """找出数据量断点"""
        logger.info("Finding data size breakpoint...")

        test_sizes_mb = [100, 200, 500, 1000, 2000, 5000, 10000]  # MB
        breakpoint = 0

        for size_mb in test_sizes_mb:
            try:
                # 检查可用内存
                available_memory_mb = psutil.virtual_memory().available / (1024 * 1024)
                if size_mb > available_memory_mb * 0.8:  # 保留20%安全边际
                    break

                # 生成测试数据
                data_size = size_mb * 1024 * 256  # MB -> number of double values
                test_data = np.random.rand(data_size)

                # 执行计算任务
                start_time = time.time()
                result = np.sum(test_data)
                execution_time = time.time() - start_time

                # 清理内存
                del test_data
                gc.collect()

                # 如果执行时间超过阈值，达到断点
                if execution_time > 10.0:  # 10秒执行时间阈值
                    breakpoint = size_mb // 2
                    break

                breakpoint = size_mb

            except Exception as e:
                logger.warning(f"Data size breakpoint test failed at {size_mb}MB: {e}")
                gc.collect()
                breakpoint = size_mb // 2
                break

        return breakpoint

    def _start_system_monitoring(self):
        """启动系统监控"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()

    def _stop_system_monitoring(self):
        """停止系统监控"""
        self.monitoring_active = False
        if hasattr(self, 'monitor_thread') and self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring_active:
            try:
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()

                metrics = SystemResourceMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_available_mb=memory.available / (1024 * 1024),
                    disk_usage_percent=disk.percent,
                    disk_io_read_mb=0,  # 需要差值计算
                    disk_io_write_mb=0,
                    network_sent_mb=network.bytes_sent / (1024 * 1024),
                    network_recv_mb=network.bytes_recv / (1024 * 1024),
                    open_files=len(psutil.Process().open_files()),
                    threads_count=psutil.Process().num_threads(),
                    processes_count=len(psutil.pids())
                )

                self.resource_metrics_history.append(metrics)
                time.sleep(1.0)

            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                time.sleep(1.0)

    def _calculate_test_metrics(
        self,
        test_id: str,
        test_type: str,
        start_time: float,
        end_time: float,
        test_results: Dict[str, Any]
    ) -> StressTestMetrics:
        """计算测试指标"""
        duration = end_time - start_time

        # 获取资源使用历史
        if self.resource_metrics_history:
            cpu_values = [m.cpu_percent for m in self.resource_metrics_history]
            memory_values = [m.memory_percent for m in self.resource_metrics_history]
            memory_mb_values = [m.memory_available_mb for m in self.resource_metrics_history]

            max_cpu = max(cpu_values) if cpu_values else 0
            avg_cpu = np.mean(cpu_values) if cpu_values else 0
            max_memory_mb = (100 - min(memory_mb_values)) if memory_mb_values else 0
            avg_memory_mb = (100 - np.mean(memory_mb_values)) if memory_mb_values else 0
            peak_memory_mb = max_memory_mb
        else:
            max_cpu = avg_cpu = max_memory_mb = avg_memory_mb = peak_memory_mb = 0

        # 分析测试结果
        if test_type == "load_test":
            requests = test_results.get('requests', [])
            total_requests = len(requests)
            successful_requests = len([r for r in requests if r.get('success', False)])
            failed_requests = total_requests - successful_requests

            if successful_requests > 0:
                response_times = [r['response_time_ms'] for r in requests if r.get('success', False)]
                avg_response_time = np.mean(response_times)
                max_response_time = max(response_times)
            else:
                avg_response_time = max_response_time = 0

        else:
            # 其他测试类型的处理
            total_requests = successful_requests = failed_requests = 0
            avg_response_time = max_response_time = 0

        # 计算其他指标
        error_rate = failed_requests / max(total_requests, 1)
        throughput = successful_requests / max(duration, 1)
        stability_score = self._calculate_stability_score()
        resilience_score = self._calculate_resilience_score(test_results)

        return StressTestMetrics(
            test_id=test_id,
            test_type=test_type,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            max_cpu_usage=max_cpu,
            avg_cpu_usage=avg_cpu,
            max_memory_usage_mb=max_memory_mb,
            avg_memory_usage_mb=avg_memory_mb,
            peak_memory_usage_mb=peak_memory_mb,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            error_rate=error_rate,
            avg_response_time_ms=avg_response_time,
            max_response_time_ms=max_response_time,
            throughput_requests_per_sec=throughput,
            system_stability_score=stability_score,
            resilience_score=resilience_score
        )

    def _calculate_stability_score(self) -> float:
        """计算系统稳定性分数"""
        if len(self.resource_metrics_history) < 10:
            return 1.0

        # 计算CPU和内存使用的稳定性
        cpu_values = [m.cpu_percent for m in self.resource_metrics_history]
        memory_values = [m.memory_percent for m in self.resource_metrics_history]

        cpu_stability = 1.0 - (np.std(cpu_values) / max(np.mean(cpu_values), 1))
        memory_stability = 1.0 - (np.std(memory_values) / max(np.mean(memory_values), 1))

        # 综合稳定性分数
        stability_score = (cpu_stability + memory_stability) / 2
        return max(0.0, min(1.0, stability_score))

    def _calculate_resilience_score(self, test_results: Dict[str, Any]) -> float:
        """计算系统韧性分数"""
        # 基于错误率计算韧性分数
        if isinstance(test_results, dict):
            if 'requests' in test_results:
                requests = test_results['requests']
                if requests:
                    error_rate = len([r for r in requests if not r.get('success', False)]) / len(requests)
                    resilience_score = 1.0 - error_rate
                    return max(0.0, resilience_score)

        # 默认韧性分数
        return 0.9

    def _save_test_results(self, metrics: StressTestMetrics):
        """保存测试结果"""
        try:
            result_file = self.output_dir / f"{metrics.test_id}.json"
            with open(result_file, 'w') as f:
                json.dump(asdict(metrics), f, indent=2, default=str)

            logger.info(f"Test results saved to {result_file}")

        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

    def _save_breakpoint_results(self, results: Dict[str, Any]):
        """保存断点测试结果"""
        try:
            result_file = self.output_dir / f"{results['test_id']}.json"
            with open(result_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Breakpoint test results saved to {result_file}")

        except Exception as e:
            logger.error(f"Failed to save breakpoint results: {e}")

    def generate_stress_test_report(self, test_results: List[StressTestMetrics]) -> Dict[str, Any]:
        """生成压力测试报告"""
        if not test_results:
            return {}

        report = {
            'executive_summary': {
                'total_tests': len(test_results),
                'test_types': list(set([t.test_type for t in test_results])),
                'total_duration_hours': sum([t.duration_seconds for t in test_results]) / 3600,
                'avg_cpu_usage': np.mean([t.avg_cpu_usage for t in test_results]),
                'peak_memory_usage_gb': max([t.peak_memory_usage_mb for t in test_results]) / 1024,
                'avg_stability_score': np.mean([t.system_stability_score for t in test_results]),
                'avg_resilience_score': np.mean([t.resilience_score for t in test_results])
            },
            'performance_analysis': {
                'throughput_analysis': {
                    'avg_throughput': np.mean([t.throughput_requests_per_sec for t in test_results if t.throughput_requests_per_sec > 0]),
                    'max_throughput': max([t.throughput_requests_per_sec for t in test_results if t.throughput_requests_per_sec > 0]),
                    'throughput_variance': np.var([t.throughput_requests_per_sec for t in test_results if t.throughput_requests_per_sec > 0])
                },
                'error_analysis': {
                    'avg_error_rate': np.mean([t.error_rate for t in test_results]),
                    'max_error_rate': max([t.error_rate for t in test_results]),
                    'total_failed_requests': sum([t.failed_requests for t in test_results]),
                    'total_successful_requests': sum([t.successful_requests for t in test_results])
                },
                'resource_utilization': {
                    'cpu_efficiency': np.mean([t.avg_cpu_usage for t in test_results]) / 100,
                    'memory_efficiency': 1.0 - (np.mean([t.avg_memory_usage_mb for t in test_results]) / 8192),  # 相对于8GB
                    'peak_cpu_usage': max([t.max_cpu_usage for t in test_results]),
                    'peak_memory_usage_gb': max([t.peak_memory_usage_mb for t in test_results]) / 1024
                }
            },
            'recommendations': self._generate_stress_test_recommendations(test_results)
        }

        return report

    def _generate_stress_test_recommendations(self, test_results: List[StressTestMetrics]) -> List[str]:
        """生成压力测试建议"""
        recommendations = []

        avg_cpu = np.mean([t.avg_cpu_usage for t in test_results])
        peak_memory = max([t.peak_memory_usage_mb for t in test_results]) / 1024
        avg_error_rate = np.mean([t.error_rate for t in test_results])
        avg_stability = np.mean([t.system_stability_score for t in test_results])

        if avg_cpu > 80:
            recommendations.append("Consider CPU optimization or horizontal scaling to handle high CPU loads")

        if peak_memory > 6:
            recommendations.append("Implement memory optimization strategies and consider memory monitoring")

        if avg_error_rate > 0.05:
            recommendations.append("Improve error handling and system resilience to reduce error rates")

        if avg_stability < 0.8:
            recommendations.append("Address system stability issues and improve resource management")

        recommendations.append("Implement comprehensive monitoring and alerting for production environments")
        recommendations.append("Establish performance baselines and SLAs based on test results")

        return recommendations

# 全局测试实例
_global_load_stress_tester = None

def get_load_stress_tester() -> LoadStressTester:
    """获取负载压力测试器实例"""
    global _global_load_stress_tester
    if _global_load_stress_tester is None:
        _global_load_stress_tester = LoadStressTester()
    return _global_load_stress_tester

def run_load_test(level: LoadLevel = LoadLevel.MODERATE) -> StressTestMetrics:
    """运行负载测试（简化接口）"""
    tester = get_load_stress_tester()
    return tester.run_load_test(level)

def run_stress_test(stress_type: StressType = StressType.CPU_STRESS, intensity: float = 1.0) -> StressTestMetrics:
    """运行压力测试（简化接口）"""
    tester = get_load_stress_tester()
    return tester.run_stress_test(stress_type, intensity)