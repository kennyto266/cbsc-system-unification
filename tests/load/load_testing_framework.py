"""
Load Testing Framework
Comprehensive load testing and concurrent request testing for CBSC platform
"""

import asyncio
import aiohttp
import time
import statistics
import json
import logging
import signal
import sys
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import psutil
import gc
from collections import defaultdict, deque
import tracemalloc

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LoadTestType(Enum):
    """Types of load tests"""
    SMOKE_TEST = "smoke_test"                    # Light load, short duration
    LOAD_TEST = "load_test"                      # Normal load, sustained
    STRESS_TEST = "stress_test"                  # High load, find breaking point
    SPIKE_TEST = "spike_test"                    # Sudden load spikes
    ENDURANCE_TEST = "endurance_test"            # Long duration, normal load
    VOLUME_TEST = "volume_test"                  # Large data volume
    CONCURRENCY_TEST = "concurrency_test"        # High concurrency
    SCALABILITY_TEST = "scalability_test"        # Variable load levels


class LoadPattern(Enum):
    """Load patterns for testing"""
    CONSTANT = "constant"                        # Steady load
    RAMP_UP = "ramp_up"                         # Gradual increase
    RAMP_DOWN = "ramp_down"                     # Gradual decrease
    SINE_WAVE = "sine_wave"                      # Sinusoidal variation
    STEP_FUNCTION = "step_function"              # Step changes
    RANDOM_BURSTS = "random_bursts"              # Random bursts
    REALISTIC = "realistic"                      # Real user behavior simulation


@dataclass
class LoadTestConfig:
    """Load test configuration"""
    name: str
    test_type: LoadTestType
    load_pattern: LoadPattern = LoadPattern.CONSTANT

    # Basic load parameters
    duration_seconds: int = 300                  # 5 minutes default
    concurrent_users: int = 50
    requests_per_second: float = 100
    total_requests: Optional[int] = None        # Override duration if set

    # Ramp parameters
    ramp_up_seconds: int = 30
    ramp_down_seconds: int = 30

    # Think time (simulates user think time between requests)
    min_think_time_ms: int = 100
    max_think_time_ms: int = 1000

    # Request parameters
    target_endpoints: List[str] = field(default_factory=lambda: ["/health"])
    request_methods: List[str] = field(default_factory=lambda: ["GET"])
    request_payloads: List[Dict] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)

    # Failure handling
    max_failures: int = 100                      # Stop if more failures
    failure_rate_threshold: float = 0.05         # 5% failure rate threshold

    # Monitoring
    monitoring_interval: float = 1.0             # Seconds
    resource_monitoring: bool = True
    network_monitoring: bool = True

    # Advanced options
    distributed_testing: bool = False
    user_agent_rotation: bool = True
    cookie_jar: bool = True
    follow_redirects: bool = True

    # Realistic simulation
    realistic_behavior: bool = False
    session_simulation: bool = False
    cache_simulation: bool = True


@dataclass
class LoadTestResult:
    """Load test execution result"""
    config_name: str
    test_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0

    # Response time metrics (seconds)
    avg_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    p50_response_time: float = 0.0
    p90_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # Throughput metrics
    requests_per_second: float = 0.0
    peak_rps: float = 0.0
    min_rps: float = 0.0

    # Resource metrics
    avg_cpu_usage: float = 0.0
    max_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0
    max_memory_usage: float = 0.0
    avg_network_io: float = 0.0

    # Error analysis
    error_rate: float = 0.0
    errors_by_status: Dict[int, int] = field(default_factory=dict)
    errors_by_endpoint: Dict[str, int] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)

    # Time series data
    response_times_series: List[float] = field(default_factory=list)
    rps_series: List[float] = field(default_factory=list)
    cpu_series: List[float] = field(default_factory=list)
    memory_series: List[float] = field(default_factory=list)

    # Status
    completed: bool = True
    stopped_early: bool = False
    stop_reason: Optional[str] = None


class UserBehaviorSimulator:
    """Simulates realistic user behavior"""

    def __init__(self, endpoints: List[str], realistic_behavior: bool = False):
        self.endpoints = endpoints
        self.realistic_behavior = realistic_behavior

        # Realistic user session patterns
        self.session_patterns = {
            "new_user": [
                ("/health", 0.1),                 # 10% chance
                ("/api/strategies/v2/", 0.3),     # 30% chance
                ("/api/market/data", 0.4),        # 40% chance
                ("/api/portfolio", 0.2)           # 20% chance
            ],
            "returning_user": [
                ("/health", 0.05),
                ("/api/portfolio", 0.5),
                ("/api/strategies/v2/", 0.3),
                ("/api/backtest/v2/status/", 0.15)
            ],
            "active_trader": [
                ("/api/portfolio", 0.25),
                ("/api/market/data", 0.35),
                ("/api/strategies/v2/", 0.2),
                ("/api/backtest/v2/submit", 0.15),
                ("/health", 0.05)
            ]
        }

        # Think time patterns (milliseconds)
        self.think_time_patterns = {
            "quick_check": (50, 200),
            "normal_browsing": (200, 2000),
            "detailed_analysis": (1000, 5000),
            "complex_operation": (2000, 10000)
        }

    def get_next_endpoint(self, user_type: str = "new_user") -> str:
        """Get next endpoint based on user behavior pattern"""
        if not self.realistic_behavior:
            return random.choice(self.endpoints)

        pattern = self.session_patterns.get(user_type, self.session_patterns["new_user"])
        endpoints, probabilities = zip(*pattern)
        return np.random.choice(endpoints, p=probabilities)

    def get_think_time(self, operation_type: str = "normal_browsing") -> float:
        """Get think time in seconds"""
        min_ms, max_ms = self.think_time_patterns.get(
            operation_type, self.think_time_patterns["normal_browsing"]
        )
        return random.uniform(min_ms, max_ms) / 1000


class ResourceMonitor:
    """Monitor system resources during load testing"""

    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.monitor_thread = None
        self.data_queue = queue.Queue()
        self.process = psutil.Process()

        # Network I/O tracking
        self.last_network_io = self.process.io_counters()

    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

    def _monitor_loop(self):
        """Resource monitoring loop"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = self.process.cpu_percent()

                # Memory usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024

                # Network I/O
                current_io = self.process.io_counters()
                network_delta = (current_io.read_bytes - self.last_network_io.read_bytes +
                               current_io.write_bytes - self.last_network_io.write_bytes) / 1024 / 1024  # MB
                self.last_network_io = current_io

                # Put data in queue
                self.data_queue.put({
                    "timestamp": time.time(),
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_mb,
                    "network_mb": network_delta
                })

                time.sleep(self.sampling_interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    def get_metrics(self) -> Dict[str, List[float]]:
        """Get collected metrics"""
        metrics = {
            "cpu": [],
            "memory": [],
            "network": []
        }

        while not self.data_queue.empty():
            try:
                data = self.data_queue.get_nowait()
                metrics["cpu"].append(data["cpu_percent"])
                metrics["memory"].append(data["memory_mb"])
                metrics["network"].append(data["network_mb"])
            except queue.Empty:
                break

        return metrics


class LoadGenerator:
    """Generates load for testing"""

    def __init__(self, config: LoadTestConfig, user_simulator: UserBehaviorSimulator):
        self.config = config
        self.user_simulator = user_simulator
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
        ]

        # Statistics tracking
        self.request_stats = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "timeouts": 0,
            "response_times": [],
            "errors_by_status": defaultdict(int),
            "errors_by_endpoint": defaultdict(int),
            "error_messages": []
        }

        # Time series tracking
        self.time_series_data = {
            "timestamps": [],
            "response_times": [],
            "requests_per_second": []
        }

        self.stop_event = threading.Event()

    async def setup(self):
        """Setup load generator"""
        # Create HTTP session with appropriate configuration
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_users * 2,
            limit_per_host=self.config.concurrent_users,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        timeout = aiohttp.ClientTimeout(
            total=30.0,
            connect=10.0,
            sock_read=20.0
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if self.config.user_agent_rotation:
            headers["User-Agent"] = random.choice(self.user_agents)

        headers.update(self.config.headers)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            cookie_jar=aiohttp.CookieJar(unsafe=self.config.cookie_jar) if self.config.cookie_jar else None
        )

    async def cleanup(self):
        """Cleanup load generator"""
        if self.session:
            await self.session.close()

    async def generate_load(self) -> LoadTestResult:
        """Generate load according to configuration"""
        start_time = datetime.utcnow()

        # Setup
        await self.setup()

        # Start resource monitoring
        resource_monitor = ResourceMonitor(self.config.monitoring_interval)
        if self.config.resource_monitoring:
            resource_monitor.start_monitoring()

        # Start time series tracking
        time_series_thread = threading.Thread(target=self._track_time_series)
        time_series_thread.daemon = True
        time_series_thread.start()

        try:
            # Execute load test based on pattern
            if self.config.load_pattern == LoadPattern.CONSTANT:
                await self._constant_load()
            elif self.config.load_pattern == LoadPattern.RAMP_UP:
                await self._ramp_up_load()
            elif self.config.load_pattern == LoadPattern.SINE_WAVE:
                await self._sine_wave_load()
            elif self.config.load_pattern == LoadPattern.STEP_FUNCTION:
                await self._step_function_load()
            elif self.config.load_pattern == LoadPattern.RANDOM_BURSTS:
                await self._random_bursts_load()
            elif self.config.load_pattern == LoadPattern.REALISTIC:
                await self._realistic_load()
            else:
                await self._constant_load()  # Default to constant

        except Exception as e:
            logger.error(f"Load generation error: {str(e)}")
        finally:
            # Stop monitoring
            if self.config.resource_monitoring:
                resource_monitor.stop_monitoring()

            # Cleanup
            await self.cleanup()

            # Generate result
            end_time = datetime.utcnow()
            result = self._generate_result(start_time, end_time, resource_monitor)

        return result

    async def _constant_load(self):
        """Generate constant load"""
        # Create worker tasks
        tasks = []
        for i in range(self.config.concurrent_users):
            task = asyncio.create_task(
                self._constant_load_worker(f"worker_{i}")
            )
            tasks.append(task)

        # Wait for completion or stop
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.duration_seconds
            )
        except asyncio.TimeoutError:
            # Normal completion due to timeout
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _constant_load_worker(self, worker_id: str):
        """Constant load worker"""
        end_time = time.time() + self.config.duration_seconds
        request_count = 0

        while time.time() < end_time and not self.stop_event.is_set():
            # Calculate timing for rate limiting
            if self.config.requests_per_second > 0:
                interval = 1.0 / (self.config.requests_per_second / self.config.concurrent_users)
                request_start = time.time()

            # Execute request
            await self._execute_request(worker_id, request_count)
            request_count += 1

            # Rate limiting and think time
            if self.config.requests_per_second > 0:
                elapsed = time.time() - request_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            # Think time
            think_time = random.uniform(
                self.config.min_think_time_ms / 1000,
                self.config.max_think_time_ms / 1000
            )
            await asyncio.sleep(think_time)

    async def _execute_request(self, worker_id: str, request_id: int):
        """Execute a single request"""
        request_start = time.time()

        try:
            # Select endpoint and method
            if self.config.realistic_behavior:
                endpoint = self.user_simulator.get_next_endpoint()
            else:
                endpoint = random.choice(self.config.target_endpoints)

            method = random.choice(self.config.request_methods)

            # Prepare request
            url = f"http://localhost:3003{endpoint}"
            params = {}

            # Add realistic parameters
            if "market/data" in endpoint:
                params = {"symbol": random.choice(["AAPL", "GOOGL", "MSFT", "AMZN"]), "limit": 100}
            elif "strategies" in endpoint and "?" in endpoint:
                pass  # Already has ID
            elif "backtest" in endpoint:
                params = {"status": "running"}

            # Execute request
            response_time_start = time.time()

            if method == "GET":
                async with self.session.get(url, params=params) as response:
                    response_data = await response.read()
                    status_code = response.status
            elif method == "POST":
                payload = random.choice(self.config.request_payloads) if self.config.request_payloads else {}
                async with self.session.post(url, json=payload) as response:
                    response_data = await response.read()
                    status_code = response.status
            else:
                # Default to GET
                async with self.session.get(url, params=params) as response:
                    response_data = await response.read()
                    status_code = response.status

            response_time = time.time() - response_time_start
            total_time = time.time() - request_start

            # Record metrics
            self.request_stats["total"] += 1
            self.request_stats["response_times"].append(response_time)

            if 200 <= status_code < 300:
                self.request_stats["successful"] += 1
            else:
                self.request_stats["failed"] += 1
                self.request_stats["errors_by_status"][status_code] += 1
                self.request_stats["errors_by_endpoint"][endpoint] += 1

                if len(self.request_stats["error_messages"]) < 10:
                    self.request_stats["error_messages"].append(
                        f"{worker_id}: {method} {endpoint} - {status_code}"
                    )

        except asyncio.TimeoutError:
            self.request_stats["total"] += 1
            self.request_stats["timeouts"] += 1
            self.request_stats["failed"] += 1
            self.request_stats["response_times"].append(30.0)  # Max timeout

            if len(self.request_stats["error_messages"]) < 10:
                self.request_stats["error_messages"].append(f"{worker_id}: Request timeout")

        except Exception as e:
            self.request_stats["total"] += 1
            self.request_stats["failed"] += 1
            self.request_stats["response_times"].append(0.0)

            if len(self.request_stats["error_messages"]) < 10:
                self.request_stats["error_messages"].append(f"{worker_id}: {str(e)}")

    async def _ramp_up_load(self):
        """Generate ramp-up load pattern"""
        ramp_steps = 10
        step_duration = self.config.ramp_up_seconds / ramp_steps
        users_per_step = self.config.concurrent_users / ramp_steps

        for step in range(ramp_steps):
            current_users = int(users_per_step * (step + 1))
            logger.info(f"Ramp-up step {step + 1}: {current_users} users")

            # Create tasks for current users
            tasks = []
            for i in range(current_users):
                task = asyncio.create_task(
                    self._ramp_load_worker(f"worker_{step}_{i}", step_duration)
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _ramp_load_worker(self, worker_id: str, duration: float):
        """Worker for ramp-based load"""
        end_time = time.time() + duration

        while time.time() < end_time and not self.stop_event.is_set():
            await self._execute_request(worker_id, 0)
            await asyncio.sleep(1.0 / max(1, self.config.requests_per_second))

    async def _sine_wave_load(self):
        """Generate sine wave load pattern"""
        period = 60  # 1 minute period
        steps = int(self.config.duration_seconds / 5)  # Sample every 5 seconds

        for step in range(steps):
            # Calculate load factor using sine wave
            phase = (step / steps) * 2 * np.pi
            load_factor = (np.sin(phase) + 1) / 2  # Normalize to 0-1
            current_users = int(self.config.concurrent_users * load_factor)

            if current_users == 0:
                await asyncio.sleep(5)
                continue

            logger.info(f"Sine wave step {step}: {current_users} users ({load_factor:.2f})")

            # Execute for 5 seconds with current load
            tasks = []
            for i in range(current_users):
                task = asyncio.create_task(
                    self._sine_wave_worker(f"worker_{step}_{i}", 5.0)
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _sine_wave_worker(self, worker_id: str, duration: float):
        """Worker for sine wave load"""
        end_time = time.time() + duration

        while time.time() < end_time and not self.stop_event.is_set():
            await self._execute_request(worker_id, 0)
            await asyncio.sleep(0.1)  # High frequency during active period

    async def _step_function_load(self):
        """Generate step function load pattern"""
        steps = 5
        step_duration = self.config.duration_seconds / steps
        load_levels = [0.2, 0.5, 1.0, 0.7, 0.3]  # Load levels as fractions

        for step, load_level in enumerate(load_levels):
            current_users = int(self.config.concurrent_users * load_level)
            logger.info(f"Step {step + 1}: {current_users} users ({load_level:.1f}x)")

            if current_users == 0:
                await asyncio.sleep(step_duration)
                continue

            # Create workers for this step
            tasks = []
            for i in range(current_users):
                task = asyncio.create_task(
                    self._step_worker(f"worker_{step}_{i}", step_duration)
                )
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

    async def _step_worker(self, worker_id: str, duration: float):
        """Worker for step function load"""
        end_time = time.time() + duration

        while time.time() < end_time and not self.stop_event.is_set():
            await self._execute_request(worker_id, 0)
            await asyncio.sleep(1.0 / max(1, self.config.requests_per_second))

    async def _random_bursts_load(self):
        """Generate random burst load pattern"""
        base_users = self.config.concurrent_users // 4
        burst_users = self.config.concurrent_users
        duration = self.config.duration_seconds

        current_time = 0
        while current_time < duration and not self.stop_event.is_set():
            # Random burst decision
            if random.random() < 0.3:  # 30% chance of burst
                burst_duration = random.uniform(5, 15)  # 5-15 second burst
                logger.info(f"Burst start: {burst_users} users for {burst_duration:.1f}s")

                # Create burst workers
                tasks = []
                for i in range(burst_users):
                    task = asyncio.create_task(
                        self._burst_worker(f"burst_worker_{i}", burst_duration)
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)
                current_time += burst_duration
            else:
                # Normal load period
                normal_duration = random.uniform(10, 30)  # 10-30 seconds
                logger.info(f"Normal load: {base_users} users for {normal_duration:.1f}s")

                tasks = []
                for i in range(base_users):
                    task = asyncio.create_task(
                        self._normal_worker(f"normal_worker_{i}", normal_duration)
                    )
                    tasks.append(task)

                await asyncio.gather(*tasks, return_exceptions=True)
                current_time += normal_duration

    async def _burst_worker(self, worker_id: str, duration: float):
        """Worker for burst load"""
        end_time = time.time() + duration

        while time.time() < end_time and not self.stop_event.is_set():
            await self._execute_request(worker_id, 0)
            await asyncio.sleep(0.05)  # High frequency during burst

    async def _normal_worker(self, worker_id: str, duration: float):
        """Worker for normal load"""
        end_time = time.time() + duration

        while time.time() < end_time and not self.stop_event.is_set():
            await self._execute_request(worker_id, 0)
            await asyncio.sleep(1.0 / max(1, self.config.requests_per_second))

    async def _realistic_load(self):
        """Generate realistic user behavior load"""
        # Create different user types
        user_types = ["new_user", "returning_user", "active_trader"]
        user_distribution = [0.3, 0.5, 0.2]  # 30% new, 50% returning, 20% active

        # Calculate users per type
        users_per_type = []
        remaining = self.config.concurrent_users
        for i, dist in enumerate(user_distribution[:-1]):
            count = int(self.config.concurrent_users * dist)
            users_per_type.append((user_types[i], count))
            remaining -= count
        users_per_type.append((user_types[-1], remaining))

        # Create user sessions
        tasks = []
        user_id = 0
        for user_type, count in users_per_type:
            logger.info(f"Creating {count} {user_type} sessions")

            for i in range(count):
                task = asyncio.create_task(
                    self._realistic_user_session(
                        f"{user_type}_user_{user_id}",
                        user_type
                    )
                )
                tasks.append(task)
                user_id += 1

        # Run all sessions
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _realistic_user_session(self, user_id: str, user_type: str):
        """Simulate realistic user session"""
        session_start = time.time()
        session_duration = random.uniform(300, 1800)  # 5-30 minutes
        operations_per_session = random.randint(5, 20)

        for operation in range(operations_per_session):
            # Check if test should end
            if (time.time() - session_start) > min(session_duration, self.config.duration_seconds):
                break
            if self.stop_event.is_set():
                break

            # Get next endpoint and think time
            endpoint = self.user_simulator.get_next_endpoint(user_type)
            think_time = self.user_simulator.get_think_time("normal_browsing")

            # Execute request
            await self._execute_realistic_request(user_id, endpoint)

            # Think time
            await asyncio.sleep(think_time)

    async def _execute_realistic_request(self, user_id: str, endpoint: str):
        """Execute realistic request"""
        request_start = time.time()

        try:
            # Prepare request with realistic parameters
            url = f"http://localhost:3003{endpoint}"
            params = {}

            if "market/data" in endpoint:
                symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "FB", "NVDA"]
                params = {
                    "symbol": random.choice(symbols),
                    "limit": random.randint(50, 200),
                    "interval": random.choice(["1m", "5m", "1h", "1d"])
                }
            elif "strategies" in endpoint and "?" not in endpoint:
                params = {
                    "page": random.randint(1, 5),
                    "limit": random.randint(10, 50),
                    "type": random.choice(["momentum", "mean_reversion", "arbitrage"])
                }

            # Execute request
            response_time_start = time.time()
            async with self.session.get(url, params=params) as response:
                if response.content_type == 'application/json':
                    await response.json()
                else:
                    await response.read()
                status_code = response.status

            response_time = time.time() - response_time_start

            # Record metrics
            self.request_stats["total"] += 1
            self.request_stats["response_times"].append(response_time)

            if 200 <= status_code < 300:
                self.request_stats["successful"] += 1
            else:
                self.request_stats["failed"] += 1
                self.request_stats["errors_by_status"][status_code] += 1
                self.request_stats["errors_by_endpoint"][endpoint] += 1

        except Exception as e:
            self.request_stats["total"] += 1
            self.request_stats["failed"] += 1
            self.request_stats["response_times"].append(0.0)

    def _track_time_series(self):
        """Track time series data during test"""
        start_time = time.time()
        last_requests = 0
        last_time = start_time

        while not self.stop_event.is_set():
            current_time = time.time()
            elapsed = current_time - start_time

            if elapsed > self.config.duration_seconds:
                break

            # Calculate current RPS
            current_requests = self.request_stats["total"]
            time_delta = current_time - last_time

            if time_delta > 0:
                current_rps = (current_requests - last_requests) / time_delta
            else:
                current_rps = 0

            # Record data point
            self.time_series_data["timestamps"].append(elapsed)
            self.time_series_data["requests_per_second"].append(current_rps)

            # Calculate average response time for recent requests
            if self.request_stats["response_times"]:
                recent_times = self.request_stats["response_times"][-100:]  # Last 100 requests
                avg_time = statistics.mean(recent_times)
                self.time_series_data["response_times"].append(avg_time)
            else:
                self.time_series_data["response_times"].append(0.0)

            # Update counters
            last_requests = current_requests
            last_time = current_time

            time.sleep(self.config.monitoring_interval)

    def _generate_result(self, start_time: datetime, end_time: datetime,
                        resource_monitor: ResourceMonitor) -> LoadTestResult:
        """Generate load test result"""
        duration = (end_time - start_time).total_seconds()

        result = LoadTestResult(
            config_name=self.config.name,
            test_type=self.config.test_type.value,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration
        )

        # Basic metrics
        result.total_requests = self.request_stats["total"]
        result.successful_requests = self.request_stats["successful"]
        result.failed_requests = self.request_stats["failed"]
        result.timeout_requests = self.request_stats["timeouts"]

        # Error metrics
        if result.total_requests > 0:
            result.error_rate = result.failed_requests / result.total_requests

        result.errors_by_status = dict(self.request_stats["errors_by_status"])
        result.errors_by_endpoint = dict(self.request_stats["errors_by_endpoint"])
        result.error_messages = self.request_stats["error_messages"]

        # Response time metrics
        if self.request_stats["response_times"]:
            response_times = [rt for rt in self.request_stats["response_times"] if rt > 0]
            if response_times:
                result.avg_response_time = statistics.mean(response_times)
                result.min_response_time = min(response_times)
                result.max_response_time = max(response_times)
                result.p50_response_time = np.percentile(response_times, 50)
                result.p90_response_time = np.percentile(response_times, 90)
                result.p95_response_time = np.percentile(response_times, 95)
                result.p99_response_time = np.percentile(response_times, 99)

        # Throughput metrics
        if duration > 0:
            result.requests_per_second = result.total_requests / duration

        if self.time_series_data["requests_per_second"]:
            result.peak_rps = max(self.time_series_data["requests_per_second"])
            result.min_rps = min(self.time_series_data["requests_per_second"])

        # Resource metrics
        if self.config.resource_monitoring:
            metrics = resource_monitor.get_metrics()
            if metrics["cpu"]:
                result.avg_cpu_usage = statistics.mean(metrics["cpu"])
                result.max_cpu_usage = max(metrics["cpu"])
            if metrics["memory"]:
                result.avg_memory_usage = statistics.mean(metrics["memory"])
                result.max_memory_usage = max(metrics["memory"])
            if metrics["network"]:
                result.avg_network_io = statistics.mean(metrics["network"])

        # Time series data
        result.response_times_series = self.time_series_data["response_times"]
        result.rps_series = self.time_series_data["requests_per_second"]
        result.cpu_series = resource_monitor.get_metrics().get("cpu", [])
        result.memory_series = resource_monitor.get_metrics().get("memory", [])

        # Status
        result.completed = not self.stop_event.is_set()
        result.stopped_early = self.stop_event.is_set()
        if self.stop_event.is_set():
            result.stop_reason = "Manual stop or failure threshold reached"

        return result


class LoadTestingFramework:
    """Comprehensive load testing framework"""

    def __init__(self):
        self.test_results: List[LoadTestResult] = []
        self.current_test: Optional[LoadGenerator] = None

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, stopping load test...")
        if self.current_test:
            self.current_test.stop_event.set()

    async def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """Run a single load test"""
        logger.info(f"Starting load test: {config.name}")

        # Create user simulator
        user_simulator = UserBehaviorSimulator(
            config.target_endpoints,
            config.realistic_behavior
        )

        # Create load generator
        self.current_test = LoadGenerator(config, user_simulator)

        try:
            # Run the test
            result = await self.current_test.generate_load()
            self.test_results.append(result)

            # Log results
            self._log_test_results(result)

            return result

        except Exception as e:
            logger.error(f"Load test failed: {str(e)}")
            # Create failed result
            result = LoadTestResult(
                config_name=config.name,
                test_type=config.test_type.value,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_seconds=0,
                completed=False,
                stop_reason=str(e)
            )
            return result

        finally:
            self.current_test = None

    async def run_load_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive load test suite"""
        logger.info("Starting comprehensive load test suite...")

        # Define test configurations
        test_configs = [
            # Smoke test - quick sanity check
            LoadTestConfig(
                name="smoke_test",
                test_type=LoadTestType.SMOKE_TEST,
                duration_seconds=30,
                concurrent_users=10,
                requests_per_second=20,
                target_endpoints=["/health"],
                failure_rate_threshold=0.01
            ),

            # Load test - normal operating conditions
            LoadTestConfig(
                name="normal_load_test",
                test_type=LoadTestType.LOAD_TEST,
                duration_seconds=300,
                concurrent_users=50,
                requests_per_second=100,
                target_endpoints=["/health", "/api/strategies/v2/", "/api/market/data"],
                failure_rate_threshold=0.02
            ),

            # Stress test - find breaking point
            LoadTestConfig(
                name="stress_test",
                test_type=LoadTestType.STRESS_TEST,
                duration_seconds=180,
                concurrent_users=500,
                requests_per_second=1000,
                target_endpoints=["/health", "/api/strategies/v2/", "/api/market/data"],
                failure_rate_threshold=0.10  # Allow higher failure rate for stress test
            ),

            # Spike test - sudden load spikes
            LoadTestConfig(
                name="spike_test",
                test_type=LoadTestType.SPIKE_TEST,
                load_pattern=LoadPattern.RANDOM_BURSTS,
                duration_seconds=240,
                concurrent_users=200,
                requests_per_second=500,
                target_endpoints=["/health", "/api/market/data"],
                failure_rate_threshold=0.05
            ),

            # Concurrency test - high concurrency
            LoadTestConfig(
                name="concurrency_test",
                test_type=LoadTestType.CONCURRENCY_TEST,
                duration_seconds=120,
                concurrent_users=1000,
                requests_per_second=2000,
                target_endpoints=["/health"],  # Simple endpoint for high concurrency
                failure_rate_threshold=0.05
            ),

            # Realistic user behavior test
            LoadTestConfig(
                name="realistic_behavior_test",
                test_type=LoadTestType.LOAD_TEST,
                load_pattern=LoadPattern.REALISTIC,
                duration_seconds=600,  # 10 minutes
                concurrent_users=100,
                requests_per_second=50,
                target_endpoints=["/health", "/api/strategies/v2/", "/api/market/data", "/api/portfolio"],
                realistic_behavior=True,
                session_simulation=True,
                failure_rate_threshold=0.03
            )
        ]

        # Run tests
        results = []
        for config in test_configs:
            logger.info(f"Running test: {config.name}")
            result = await self.run_load_test(config)
            results.append(result)

            # Rest between tests
            await asyncio.sleep(10)

        # Generate comprehensive report
        report = await self.generate_load_test_report(results)

        return report

    def _log_test_results(self, result: LoadTestResult):
        """Log test results"""
        logger.info(f"Test completed: {result.config_name}")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s")
        logger.info(f"  Requests: {result.total_requests} total, {result.successful_requests} successful, {result.failed_requests} failed")
        logger.info(f"  Error rate: {result.error_rate:.2%}")
        logger.info(f"  Response time: avg {result.avg_response_time:.3f}s, p95 {result.p95_response_time:.3f}s")
        logger.info(f"  Throughput: {result.requests_per_second:.1f} RPS (peak: {result.peak_rps:.1f})")

        if result.resource_monitoring:
            logger.info(f"  Resources: CPU {result.avg_cpu_usage:.1f}%, Memory {result.avg_memory_usage:.1f}MB")

        if result.stopped_early:
            logger.warning(f"  Test stopped early: {result.stop_reason}")

    async def generate_load_test_report(self, results: List[LoadTestResult]) -> Dict[str, Any]:
        """Generate comprehensive load test report"""
        logger.info("Generating load test report...")

        # Aggregate metrics
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.completed)
        failed_tests = total_tests - successful_tests

        # Performance summary
        all_rps = [r.requests_per_second for r in results if r.requests_per_second > 0]
        all_response_times = [r.avg_response_time for r in results if r.avg_response_time > 0]
        all_error_rates = [r.error_rate for r in results]

        # System resource summary
        cpu_usage = [r.avg_cpu_usage for r in results if r.avg_cpu_usage > 0]
        memory_usage = [r.avg_memory_usage for r in results if r.avg_memory_usage > 0]

        # Performance analysis
        performance_analysis = self._analyze_performance_patterns(results)

        # Recommendations
        recommendations = self._generate_load_test_recommendations(results)

        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "test_duration_total": sum(r.duration_seconds for r in results)
            },
            "performance_summary": {
                "avg_requests_per_second": statistics.mean(all_rps) if all_rps else 0,
                "peak_requests_per_second": max(all_rps) if all_rps else 0,
                "avg_response_time": statistics.mean(all_response_times) if all_response_times else 0,
                "p95_response_time": statistics.mean([r.p95_response_time for r in results]) if results else 0,
                "avg_error_rate": statistics.mean(all_error_rates) if all_error_rates else 0
            },
            "system_resources": {
                "avg_cpu_usage": statistics.mean(cpu_usage) if cpu_usage else 0,
                "max_cpu_usage": max(cpu_usage) if cpu_usage else 0,
                "avg_memory_usage": statistics.mean(memory_usage) if memory_usage else 0,
                "max_memory_usage": max(memory_usage) if memory_usage else 0
            },
            "test_results": [
                {
                    "name": r.config_name,
                    "type": r.test_type,
                    "duration": r.duration_seconds,
                    "completed": r.completed,
                    "total_requests": r.total_requests,
                    "successful_requests": r.successful_requests,
                    "failed_requests": r.failed_requests,
                    "error_rate": r.error_rate,
                    "avg_response_time": r.avg_response_time,
                    "p95_response_time": r.p95_response_time,
                    "requests_per_second": r.requests_per_second,
                    "peak_rps": r.peak_rps,
                    "avg_cpu_usage": r.avg_cpu_usage,
                    "avg_memory_usage": r.avg_memory_usage,
                    "errors_by_status": r.errors_by_status,
                    "stop_reason": r.stop_reason
                }
                for r in results
            ],
            "performance_analysis": performance_analysis,
            "recommendations": recommendations,
            "capacity_analysis": self._analyze_capacity(results)
        }

        return report

    def _analyze_performance_patterns(self, results: List[LoadTestResult]) -> Dict[str, Any]:
        """Analyze performance patterns across tests"""
        analysis = {
            "scaling_behavior": {},
            "performance_bottlenecks": [],
            "error_patterns": {},
            "resource_utilization": {}
        }

        # Analyze scaling behavior
        load_tests = [r for r in results if r.test_type == LoadTestType.LOAD_TEST.value]
        if len(load_tests) > 1:
            load_tests.sort(key=lambda x: x.concurrent_users)

            response_time_trend = []
            throughput_trend = []

            for i, test in enumerate(load_tests):
                response_time_trend.append(test.avg_response_time)
                throughput_trend.append(test.requests_per_second)

            # Calculate degradation
            if len(response_time_trend) > 1:
                rt_degradation = (response_time_trend[-1] - response_time_trend[0]) / response_time_trend[0]
                throughput_scaling = throughput_trend[-1] / throughput_trend[0] if throughput_trend[0] > 0 else 0

                analysis["scaling_behavior"] = {
                    "response_time_degradation": rt_degradation,
                    "throughput_scaling_efficiency": throughput_scaling,
                    "optimal_load": load_tests[0].config_name  # Simplified
                }

        # Identify bottlenecks
        for result in results:
            if result.avg_response_time > 2.0:
                analysis["performance_bottlenecks"].append({
                    "test": result.config_name,
                    "issue": "High response time",
                    "value": result.avg_response_time
                })

            if result.error_rate > 0.05:
                analysis["performance_bottlenecks"].append({
                    "test": result.config_name,
                    "issue": "High error rate",
                    "value": result.error_rate
                })

            if result.avg_cpu_usage > 80:
                analysis["performance_bottlenecks"].append({
                    "test": result.config_name,
                    "issue": "High CPU usage",
                    "value": result.avg_cpu_usage
                })

        # Error pattern analysis
        all_status_errors = {}
        for result in results:
            for status, count in result.errors_by_status.items():
                all_status_errors[status] = all_status_errors.get(status, 0) + count

        analysis["error_patterns"] = {
            "most_common_error": max(all_status_errors.items(), key=lambda x: x[1]) if all_status_errors else None,
            "error_distribution": all_status_errors
        }

        return analysis

    def _analyze_capacity(self, results: List[LoadTestResult]) -> Dict[str, Any]:
        """Analyze system capacity"""
        capacity_analysis = {
            "max_sustainable_load": 0,
            "breaking_point": None,
            "performance_tiers": {}
        }

        # Find maximum sustainable load (error rate < 5%, response time < 2s)
        sustainable_tests = [
            r for r in results
            if r.error_rate < 0.05 and r.avg_response_time < 2.0 and r.completed
        ]

        if sustainable_tests:
            max_load = max(r.requests_per_second for r in sustainable_tests)
            capacity_analysis["max_sustainable_load"] = max_load

        # Find breaking point
        stress_tests = [r for r in results if r.test_type == LoadTestType.STRESS_TEST.value]
        if stress_tests:
            for test in stress_tests:
                if test.error_rate > 0.1 or not test.completed:
                    capacity_analysis["breaking_point"] = {
                        "test": test.config_name,
                        "load": test.requests_per_second,
                        "reason": "High error rate or test failure"
                    }
                    break

        # Performance tiers
        for result in results:
            tier = "unknown"
            if result.requests_per_second > 1000:
                tier = "high_performance"
            elif result.requests_per_second > 500:
                tier = "medium_performance"
            elif result.requests_per_second > 100:
                tier = "standard_performance"
            else:
                tier = "low_performance"

            if tier not in capacity_analysis["performance_tiers"]:
                capacity_analysis["performance_tiers"][tier] = []
            capacity_analysis["performance_tiers"][tier].append(result.config_name)

        return capacity_analysis

    def _generate_load_test_recommendations(self, results: List[LoadTestResult]) -> List[str]:
        """Generate load test recommendations"""
        recommendations = []

        # Analyze response times
        slow_tests = [r for r in results if r.avg_response_time > 2.0]
        if slow_tests:
            recommendations.append(f"Optimize response times - {len(slow_tests)} tests showed avg response time > 2s")

        # Analyze error rates
        high_error_tests = [r for r in results if r.error_rate > 0.05]
        if high_error_tests:
            recommendations.append(f"Address error handling - {len(high_error_tests)} tests had error rate > 5%")

        # Analyze throughput
        low_throughput_tests = [r for r in results if r.requests_per_second < 50 and r.concurrent_users > 10]
        if low_throughput_tests:
            recommendations.append("Improve throughput - consider caching, optimization, or scaling")

        # Analyze resource usage
        high_cpu_tests = [r for r in results if r.avg_cpu_usage > 80]
        if high_cpu_tests:
            recommendations.append("Optimize CPU usage - algorithm optimization or horizontal scaling")

        high_memory_tests = [r for r in results if r.avg_memory_usage > 1000]  # > 1GB
        if high_memory_tests:
            recommendations.append("Optimize memory usage - profile and fix memory leaks")

        # Capacity recommendations
        completed_tests = [r for r in results if r.completed]
        if completed_tests:
            max_rps = max(r.requests_per_second for r in completed_tests)
            if max_rps < 100:
                recommendations.append("System shows limited scalability - investigate bottlenecks")
            elif max_rps > 1000:
                recommendations.append("System demonstrates good scalability - consider production load testing")

        # Stress test specific recommendations
        stress_tests = [r for r in results if r.test_type == LoadTestType.STRESS_TEST.value]
        if stress_tests:
            failed_stress = [r for r in stress_tests if not r.completed]
            if failed_stress:
                recommendations.append("System fails under stress - implement better error handling and graceful degradation")

        if not recommendations:
            recommendations.append("Load testing results indicate acceptable performance")

        return recommendations


if __name__ == "__main__":
    # Run load test suite
    async def main():
        framework = LoadTestingFramework()
        report = await framework.run_load_test_suite()

        print("\n" + "="*60)
        print("LOAD TESTING FRAMEWORK REPORT")
        print("="*60)

        metadata = report["report_metadata"]
        print(f"Test Suite: {metadata['total_tests']} tests ({metadata['successful_tests']} successful)")
        print(f"Total Duration: {metadata['test_duration_total']:.1f}s")

        summary = report["performance_summary"]
        print(f"\nPerformance Summary:")
        print(f"  Average RPS: {summary['avg_requests_per_second']:.1f}")
        print(f"  Peak RPS: {summary['peak_requests_per_second']:.1f}")
        print(f"  Average Response Time: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response Time: {summary['p95_response_time']:.3f}s")
        print(f"  Average Error Rate: {summary['avg_error_rate']:.2%}")

        resources = report["system_resources"]
        print(f"\nSystem Resources:")
        print(f"  Average CPU: {resources['avg_cpu_usage']:.1f}% (max: {resources['max_cpu_usage']:.1f}%)")
        print(f"  Average Memory: {resources['avg_memory_usage']:.1f}MB (max: {resources['max_memory_usage']:.1f}MB)")

        capacity = report["capacity_analysis"]
        print(f"\nCapacity Analysis:")
        print(f"  Max Sustainable Load: {capacity['max_sustainable_load']:.1f} RPS")
        if capacity["breaking_point"]:
            bp = capacity["breaking_point"]
            print(f"  Breaking Point: {bp['load']:.1f} RPS ({bp['reason']})")

        print(f"\nPerformance Tiers:")
        for tier, tests in capacity["performance_tiers"].items():
            print(f"  {tier.replace('_', ' ').title()}: {len(tests)} tests")

        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

        print("="*60)

        # Save detailed report
        report_path = f"load_test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nDetailed report saved to: {report_path}")

    asyncio.run(main())