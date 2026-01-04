"""
Performance Benchmark Suite
Comprehensive performance testing and benchmarking for CBSC platform
"""

import asyncio
import aiohttp
import time
import psutil
import statistics
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading
import resource
import gc
import tracemalloc
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of performance benchmarks"""
    API_RESPONSE_TIME = "api_response_time"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DATABASE_PERFORMANCE = "database_performance"
    CACHE_PERFORMANCE = "cache_performance"
    ALGORITHM_PERFORMANCE = "algorithm_performance"
    CONCURRENT_REQUESTS = "concurrent_requests"
    SCALABILITY = "scalability"
    RESOURCE_EFFICIENCY = "resource_efficiency"


@dataclass
class BenchmarkConfig:
    """Benchmark configuration"""
    name: str
    benchmark_type: BenchmarkType
    target_endpoint: Optional[str] = None
    target_function: Optional[Callable] = None
    duration_seconds: int = 60
    concurrent_users: int = 10
    requests_per_second: int = 100
    warmup_seconds: int = 10
    cooldown_seconds: int = 5
    memory_profiling: bool = True
    cpu_profiling: bool = True
    response_time_threshold: float = 2.0
    throughput_threshold: float = 50.0  # requests per second
    error_rate_threshold: float = 0.01  # 1%
    percentile_thresholds: Dict[int, float] = field(default_factory=lambda: {
        50: 1.0,   # 50th percentile: 1 second
        90: 2.0,   # 90th percentile: 2 seconds
        95: 3.0,   # 95th percentile: 3 seconds
        99: 5.0    # 99th percentile: 5 seconds
    })


@dataclass
class BenchmarkResult:
    """Single benchmark execution result"""
    config_name: str
    benchmark_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float

    # Performance metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    error_rate: float = 0.0

    # Response time metrics (in seconds)
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

    # Resource usage metrics
    avg_cpu_usage: float = 0.0
    max_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0
    max_memory_usage: float = 0.0
    memory_leak_detected: bool = False

    # System metrics
    thread_count: int = 0
    process_count: int = 0

    # Detailed data
    response_times: List[float] = field(default_factory=list)
    cpu_usage_samples: List[float] = field(default_factory=list)
    memory_usage_samples: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Status
    passed: bool = True
    violations: List[str] = field(default_factory=list)


class SystemResourceMonitor:
    """Monitor system resources during benchmark execution"""

    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.monitoring = False
        self.cpu_samples = []
        self.memory_samples = []
        self.process = psutil.Process()
        self.monitor_thread = None

    def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring = True
        self.cpu_samples.clear()
        self.memory_samples.clear()
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
                self.cpu_samples.append(cpu_percent)

                # Memory usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.memory_samples.append(memory_mb)

                time.sleep(self.sampling_interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

    def get_stats(self) -> Dict[str, float]:
        """Get monitoring statistics"""
        return {
            "avg_cpu": statistics.mean(self.cpu_samples) if self.cpu_samples else 0.0,
            "max_cpu": max(self.cpu_samples) if self.cpu_samples else 0.0,
            "avg_memory": statistics.mean(self.memory_samples) if self.memory_samples else 0.0,
            "max_memory": max(self.memory_samples) if self.memory_samples else 0.0
        }


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite"""

    def __init__(self):
        self.base_url = "http://localhost:3003"
        self.influx_config = {
            "url": "http://localhost:8086",
            "token": "benchmark_token",
            "org": "cbsc",
            "bucket": "performance_benchmarks"
        }

        # Historical baseline data
        self.baseline_thresholds = {
            "api_endpoints": {
                "health_check": {"avg_response_time": 0.1, "p95_response_time": 0.2},
                "strategies_list": {"avg_response_time": 0.5, "p95_response_time": 1.0},
                "market_data": {"avg_response_time": 1.0, "p95_response_time": 2.0},
                "backtest_submit": {"avg_response_time": 2.0, "p95_response_time": 4.0}
            },
            "algorithms": {
                "momentum_calculation": {"avg_time_ms": 10, "p95_time_ms": 20},
                "risk_assessment": {"avg_time_ms": 50, "p95_time_ms": 100},
                "portfolio_optimization": {"avg_time_ms": 100, "p95_time_ms": 200}
            },
            "database": {
                "market_data_query": {"avg_time_ms": 5, "p95_time_ms": 10},
                "strategy_insert": {"avg_time_ms": 20, "p95_time_ms": 50},
                "backtest_query": {"avg_time_ms": 50, "p95_time_ms": 100}
            }
        }

    async def run_api_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run API performance benchmark"""
        logger.info(f"Running API benchmark: {config.name}")

        result = BenchmarkResult(
            config_name=config.name,
            benchmark_type=config.benchmark_type.value,
            start_time=datetime.utcnow()
        )

        # Start resource monitoring
        resource_monitor = SystemResourceMonitor()
        if config.cpu_profiling or config.memory_profiling:
            resource_monitor.start_monitoring()

        # Start memory profiling if enabled
        if config.memory_profiling:
            tracemalloc.start()

        session = None
        try:
            # Create HTTP session
            connector = aiohttp.TCPConnector(
                limit=config.concurrent_users * 2,
                limit_per_host=config.concurrent_users
            )
            timeout = aiohttp.ClientTimeout(total=10.0)
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            # Warmup phase
            logger.info(f"Warming up for {config.warmup_seconds} seconds...")
            await self._warmup_phase(session, config, resource_monitor)

            # Benchmark phase
            logger.info(f"Running benchmark for {config.duration_seconds} seconds...")
            benchmark_start = time.time()

            # Create concurrent workers
            tasks = []
            for i in range(config.concurrent_users):
                task = asyncio.create_task(
                    self._api_worker(session, config, benchmark_start, result, f"worker_{i}")
                )
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            # Cooldown phase
            logger.info(f"Cooldown for {config.cooldown_seconds} seconds...")
            await asyncio.sleep(config.cooldown_seconds)

        except Exception as e:
            logger.error(f"API benchmark error: {str(e)}")
            result.errors.append(f"Benchmark execution error: {str(e)}")
        finally:
            if session:
                await session.close()

            # Stop monitoring
            if config.cpu_profiling or config.memory_profiling:
                resource_monitor.stop_monitoring()
                resource_stats = resource_monitor.get_stats()
                result.avg_cpu_usage = resource_stats["avg_cpu"]
                result.max_cpu_usage = resource_stats["max_cpu"]
                result.avg_memory_usage = resource_stats["avg_memory"]
                result.max_memory_usage = resource_stats["max_memory"]

            # Memory profiling results
            if config.memory_profiling and tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                # Check for memory leaks (peak much higher than current)
                if peak > current * 1.5 and current > 1024 * 1024:  # >1MB current
                    result.memory_leak_detected = True
                    result.violations.append("Potential memory leak detected")

            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - result.start_time).total_seconds()

            # Calculate final metrics
            self._calculate_benchmark_metrics(result, config)

            # Validate against thresholds
            self._validate_benchmark_result(result, config)

        return result

    async def _warmup_phase(self, session: aiohttp.ClientSession,
                           config: BenchmarkConfig, monitor: SystemResourceMonitor):
        """Execute warmup phase"""
        warmup_end = time.time() + config.warmup_seconds

        while time.time() < warmup_end:
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        await response.json()
            except Exception:
                pass  # Ignore errors during warmup

            await asyncio.sleep(0.1)  # Small delay between requests

    async def _api_worker(self, session: aiohttp.ClientSession,
                         config: BenchmarkConfig, start_time: float,
                         result: BenchmarkResult, worker_id: str):
        """Individual API worker task"""
        request_count = 0
        error_count = 0

        while time.time() - start_time < config.duration_seconds:
            try:
                request_start = time.time()

                # Execute request based on target endpoint
                if config.target_endpoint == "/health":
                    async with session.get(f"{self.base_url}/health") as response:
                        await response.json()
                elif config.target_endpoint == "/api/strategies/v2/":
                    async with session.get(f"{self.base_url}/api/strategies/v2/") as response:
                        await response.json()
                elif config.target_endpoint == "/api/market/data":
                    async with session.get(
                        f"{self.base_url}/api/market/data",
                        params={"symbol": "AAPL", "limit": 100}
                    ) as response:
                        await response.json()
                else:
                    # Default to health check
                    async with session.get(f"{self.base_url}{config.target_endpoint}") as response:
                        if response.content_type == 'application/json':
                            await response.json()

                request_time = time.time() - request_start
                result.response_times.append(request_time)
                request_count += 1

            except Exception as e:
                error_count += 1
                if len(result.errors) < 10:  # Limit error messages
                    result.errors.append(f"{worker_id}: {str(e)}")

            # Rate limiting
            if config.requests_per_second > 0:
                delay = 1.0 / (config.requests_per_second / config.concurrent_users)
                await asyncio.sleep(max(0, delay))

        # Update result counters (thread-safe would be better, but OK for demo)
        result.total_requests += request_count
        result.failed_requests += error_count

    async def run_database_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run database performance benchmark"""
        logger.info(f"Running database benchmark: {config.name}")

        result = BenchmarkResult(
            config_name=config.name,
            benchmark_type=config.benchmark_type.value,
            start_time=datetime.utcnow()
        )

        # Import here to avoid dependencies
        import asyncpg

        try:
            # Database connection
            conn = await asyncpg.connect(
                host="localhost",
                port=5432,
                database="cbsc_test",
                user="test_user",
                password="test_password"
            )

            # Warmup queries
            await self._database_warmup(conn, config)

            # Benchmark queries
            query_times = []

            for i in range(config.total_requests or 1000):
                query_start = time.time()

                if "market_data" in config.name.lower():
                    await conn.fetch("""
                        SELECT * FROM market_data
                        WHERE symbol = $1
                        ORDER BY timestamp DESC
                        LIMIT 100
                    """, "AAPL")
                elif "strategies" in config.name.lower():
                    await conn.fetch("""
                        SELECT * FROM strategies
                        WHERE is_active = true
                        ORDER BY created_at DESC
                        LIMIT 50
                    """)
                else:
                    # Generic query
                    await conn.fetchval("SELECT COUNT(*) FROM users")

                query_time = time.time() - query_start
                query_times.append(query_time)

                result.response_times.append(query_time)

            await conn.close()

            # Calculate metrics
            result.total_requests = len(query_times)
            result.response_times = query_times
            self._calculate_benchmark_metrics(result, config)

        except Exception as e:
            logger.error(f"Database benchmark error: {str(e)}")
            result.errors.append(f"Database benchmark error: {str(e)}")
            result.passed = False

        result.end_time = datetime.utcnow()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()

        return result

    async def _database_warmup(self, conn: asyncpg.Connection, config: BenchmarkConfig):
        """Execute database warmup queries"""
        for _ in range(min(10, config.total_requests // 10 if config.total_requests else 10)):
            try:
                await conn.fetchval("SELECT 1")
            except Exception:
                pass

    async def run_algorithm_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run algorithm performance benchmark"""
        logger.info(f"Running algorithm benchmark: {config.name}")

        result = BenchmarkResult(
            config_name=config.name,
            benchmark_type=config.benchmark_type.value,
            start_time=datetime.utcnow()
        )

        try:
            # Generate test data
            if "momentum" in config.name.lower():
                await self._benchmark_momentum_algorithm(result, config)
            elif "risk" in config.name.lower():
                await self._benchmark_risk_algorithm(result, config)
            elif "portfolio" in config.name.lower():
                await self._benchmark_portfolio_algorithm(result, config)
            else:
                await self._benchmark_generic_algorithm(result, config)

            self._calculate_benchmark_metrics(result, config)

        except Exception as e:
            logger.error(f"Algorithm benchmark error: {str(e)}")
            result.errors.append(f"Algorithm benchmark error: {str(e)}")
            result.passed = False

        result.end_time = datetime.utcnow()
        result.duration_seconds = (result.end_time - result.start_time).total_seconds()

        return result

    async def _benchmark_momentum_algorithm(self, result: BenchmarkResult, config: BenchmarkConfig):
        """Benchmark momentum calculation algorithm"""
        import numpy as np

        iterations = config.total_requests or 1000
        data_size = 1000  # Number of data points

        for _ in range(iterations):
            # Generate test data
            prices = np.random.randn(data_size).cumsum() + 100
            timestamps = pd.date_range('2024-01-01', periods=data_size, freq='1D')

            algorithm_start = time.time()

            # Simulate momentum calculation
            returns = np.diff(prices) / prices[:-1]
            momentum_score = np.mean(returns[-20:]) if len(returns) >= 20 else 0
            volatility = np.std(returns[-20:]) if len(returns) >= 20 else 0

            execution_time = time.time() - algorithm_start
            result.response_times.append(execution_time)

    async def _benchmark_risk_algorithm(self, result: BenchmarkResult, config: BenchmarkConfig):
        """Benchmark risk assessment algorithm"""
        import numpy as np

        iterations = config.total_requests or 500
        portfolio_size = 100  # Number of positions

        for _ in range(iterations):
            # Generate test portfolio data
            positions = np.random.rand(portfolio_size)
            weights = positions / positions.sum()
            returns = np.random.randn(portfolio_size) * 0.02  # 2% daily vol
            correlation_matrix = np.random.rand(portfolio_size, portfolio_size)
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
            np.fill_diagonal(correlation_matrix, 1.0)

            algorithm_start = time.time()

            # Simulate risk calculation
            portfolio_return = np.dot(weights, returns)
            portfolio_variance = np.dot(weights, np.dot(correlation_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            var_95 = portfolio_return - 1.96 * portfolio_volatility  # 95% VaR

            execution_time = time.time() - algorithm_start
            result.response_times.append(execution_time)

    async def _benchmark_portfolio_algorithm(self, result: BenchmarkResult, config: BenchmarkConfig):
        """Benchmark portfolio optimization algorithm"""
        import numpy as np
        from scipy.optimize import minimize

        iterations = config.total_requests or 100
        num_assets = 50

        for _ in range(iterations):
            # Generate test data
            returns = np.random.randn(num_assets, 252) * 0.02  # Daily returns for 1 year
            expected_returns = np.mean(returns, axis=1)
            cov_matrix = np.cov(returns)

            algorithm_start = time.time()

            # Simulate portfolio optimization
            def portfolio_variance(weights):
                return np.dot(weights.T, np.dot(cov_matrix, weights))

            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(num_assets))
            initial_weights = np.array([1/num_assets] * num_assets)

            # Simple optimization (not full Markowitz)
            result_opt = minimize(
                portfolio_variance,
                initial_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )

            execution_time = time.time() - algorithm_start
            result.response_times.append(execution_time)

    async def _benchmark_generic_algorithm(self, result: BenchmarkResult, config: BenchmarkConfig):
        """Benchmark generic algorithm"""
        iterations = config.total_requests or 1000

        for _ in range(iterations):
            algorithm_start = time.time()

            # Simulate computational work
            result_sum = sum(i * i for i in range(1000))
            factorial = 1
            for i in range(1, 21):
                factorial *= i

            execution_time = time.time() - algorithm_start
            result.response_times.append(execution_time)

    def _calculate_benchmark_metrics(self, result: BenchmarkResult, config: BenchmarkConfig):
        """Calculate final benchmark metrics"""
        if result.response_times:
            # Response time metrics
            result.avg_response_time = statistics.mean(result.response_times)
            result.min_response_time = min(result.response_times)
            result.max_response_time = max(result.response_times)
            result.p50_response_time = np.percentile(result.response_times, 50)
            result.p90_response_time = np.percentile(result.response_times, 90)
            result.p95_response_time = np.percentile(result.response_times, 95)
            result.p99_response_time = np.percentile(result.response_times, 99)

        # Request metrics
        result.successful_requests = result.total_requests - result.failed_requests
        if result.total_requests > 0:
            result.error_rate = result.failed_requests / result.total_requests

        # Throughput metrics
        if result.duration_seconds > 0:
            result.requests_per_second = result.total_requests / result.duration_seconds

        # Peak RPS calculation (simplified)
        if result.response_times:
            avg_time_per_request = statistics.mean(result.response_times)
            if avg_time_per_request > 0:
                result.peak_rps = 1.0 / avg_time_per_request

    def _validate_benchmark_result(self, result: BenchmarkResult, config: BenchmarkConfig):
        """Validate benchmark result against thresholds"""
        violations = []

        # Response time validation
        if result.avg_response_time > config.response_time_threshold:
            violations.append(f"Average response time ({result.avg_response_time:.3f}s) exceeds threshold ({config.response_time_threshold}s)")

        # Percentile validation
        for percentile, threshold in config.percentile_thresholds.items():
            actual_percentile = getattr(result, f"p{percentile}_response_time", 0)
            if actual_percentile > threshold:
                violations.append(f"P{percentile} response time ({actual_percentile:.3f}s) exceeds threshold ({threshold}s)")

        # Throughput validation
        if result.requests_per_second < config.throughput_threshold:
            violations.append(f"Throughput ({result.requests_per_second:.1f} RPS) below threshold ({config.throughput_threshold} RPS)")

        # Error rate validation
        if result.error_rate > config.error_rate_threshold:
            violations.append(f"Error rate ({result.error_rate:.2%}) exceeds threshold ({config.error_rate_threshold:.2%})")

        # Baseline comparison
        if config.benchmark_type == BenchmarkType.API_RESPONSE_TIME:
            baseline = self.baseline_thresholds["api_endpoints"].get(config.name.split("_")[0], {})
            if baseline:
                if result.avg_response_time > baseline.get("avg_response_time", float('inf')):
                    violations.append(f"Response time regression vs baseline (avg: {result.avg_response_time:.3f}s vs {baseline['avg_response_time']:.3f}s)")
                if result.p95_response_time > baseline.get("p95_response_time", float('inf')):
                    violations.append(f"P95 response time regression vs baseline ({result.p95_response_time:.3f}s vs {baseline['p95_response_time']:.3f}s)")

        result.violations = violations
        result.passed = len(violations) == 0

    async def run_scalability_test(self, config: BenchmarkConfig) -> Dict[str, Any]:
        """Run scalability test with varying load levels"""
        logger.info(f"Running scalability test: {config.name}")

        scalability_results = {}
        load_levels = [1, 5, 10, 20, 50, 100]  # Concurrent users

        for load_level in load_levels:
            logger.info(f"Testing with {load_level} concurrent users...")

            # Create config for this load level
            load_config = BenchmarkConfig(
                name=f"{config.name}_load_{load_level}",
                benchmark_type=config.benchmark_type,
                target_endpoint=config.target_endpoint,
                duration_seconds=30,  # Shorter for scalability test
                concurrent_users=load_level,
                requests_per_second=config.requests_per_second,
                warmup_seconds=5,
                response_time_threshold=config.response_time_threshold * (1 + load_level * 0.1),  # Relax threshold with load
                throughput_threshold=config.throughput_threshold
            )

            # Run benchmark
            if config.benchmark_type == BenchmarkType.API_RESPONSE_TIME:
                result = await self.run_api_benchmark(load_config)
            else:
                continue  # Skip other types for scalability test

            scalability_results[load_level] = {
                "avg_response_time": result.avg_response_time,
                "p95_response_time": result.p95_response_time,
                "requests_per_second": result.requests_per_second,
                "error_rate": result.error_rate,
                "passed": result.passed
            }

        # Analyze scalability
        scalability_report = {
            "test_name": config.name,
            "load_levels": scalability_results,
            "scalability_score": self._calculate_scalability_score(scalability_results),
            "bottleneck_detected": self._detect_scalability_bottleneck(scalability_results),
            "max_sustainable_load": self._find_max_sustainable_load(scalability_results)
        }

        return scalability_report

    def _calculate_scalability_score(self, results: Dict[int, Dict]) -> float:
        """Calculate scalability score (0-100)"""
        if len(results) < 2:
            return 100.0

        load_levels = sorted(results.keys())
        throughputs = [results[level]["requests_per_second"] for level in load_levels]

        # Calculate linear scaling efficiency
        max_load = max(load_levels)
        min_load = min(load_levels)
        max_throughput = max(throughputs)
        min_throughput = min(throughputs)

        if min_throughput == 0:
            return 0.0

        expected_throughput = min_throughput * (max_load / min_load)
        if expected_throughput == 0:
            return 100.0

        scaling_efficiency = max_throughput / expected_throughput
        return min(100.0, scaling_efficiency * 100)

    def _detect_scalability_bottleneck(self, results: Dict[int, Dict]) -> bool:
        """Detect if scalability bottleneck exists"""
        if len(results) < 3:
            return False

        load_levels = sorted(results.keys())
        response_times = [results[level]["avg_response_time"] for level in load_levels]
        error_rates = [results[level]["error_rate"] for level in load_levels]

        # Check for response time degradation
        rt_degradation = response_times[-1] / response_times[0] if response_times[0] > 0 else 1

        # Check for error rate increase
        error_increase = error_rates[-1] - error_rates[0]

        return rt_degradation > 5.0 or error_increase > 0.05  # 5x slower or 5% more errors

    def _find_max_sustainable_load(self, results: Dict[int, Dict]) -> int:
        """Find maximum sustainable load level"""
        sustainable_loads = [
            level for level, metrics in results.items()
            if metrics["passed"] and metrics["error_rate"] < 0.01
        ]

        return max(sustainable_loads) if sustainable_loads else 0

    async def generate_performance_report(self, benchmark_results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        logger.info("Generating performance report...")

        # Aggregate metrics
        total_benchmarks = len(benchmark_results)
        passed_benchmarks = sum(1 for r in benchmark_results if r.passed)
        failed_benchmarks = total_benchmarks - passed_benchmarks

        # Performance summary
        avg_response_times = [r.avg_response_time for r in benchmark_results if r.avg_response_time > 0]
        p95_response_times = [r.p95_response_time for r in benchmark_results if r.p95_response_time > 0]
        throughputs = [r.requests_per_second for r in benchmark_results if r.requests_per_second > 0]

        # System resource summary
        cpu_usage = [r.avg_cpu_usage for r in benchmark_results if r.avg_cpu_usage > 0]
        memory_usage = [r.avg_memory_usage for r in benchmark_results if r.avg_memory_usage > 0]
        memory_leaks = sum(1 for r in benchmark_results if r.memory_leak_detected)

        # Performance trends
        performance_trends = self._analyze_performance_trends(benchmark_results)

        # Recommendations
        recommendations = self._generate_performance_recommendations(benchmark_results)

        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_benchmarks": total_benchmarks,
                "passed_benchmarks": passed_benchmarks,
                "failed_benchmarks": failed_benchmarks,
                "pass_rate": (passed_benchmarks / total_benchmarks * 100) if total_benchmarks > 0 else 0
            },
            "performance_summary": {
                "avg_response_time": statistics.mean(avg_response_times) if avg_response_times else 0,
                "p95_response_time": statistics.mean(p95_response_times) if p95_response_times else 0,
                "avg_throughput": statistics.mean(throughputs) if throughputs else 0,
                "peak_throughput": max(throughputs) if throughputs else 0
            },
            "system_resources": {
                "avg_cpu_usage": statistics.mean(cpu_usage) if cpu_usage else 0,
                "max_cpu_usage": max(cpu_usage) if cpu_usage else 0,
                "avg_memory_usage": statistics.mean(memory_usage) if memory_usage else 0,
                "max_memory_usage": max(memory_usage) if memory_usage else 0,
                "memory_leaks_detected": memory_leaks
            },
            "benchmark_details": [
                {
                    "name": r.config_name,
                    "type": r.benchmark_type,
                    "passed": r.passed,
                    "duration": r.duration_seconds,
                    "requests": r.total_requests,
                    "avg_response_time": r.avg_response_time,
                    "p95_response_time": r.p95_response_time,
                    "throughput": r.requests_per_second,
                    "error_rate": r.error_rate,
                    "violations": r.violations,
                    "errors": r.errors[:5]  # Limit errors
                }
                for r in benchmark_results
            ],
            "performance_trends": performance_trends,
            "recommendations": recommendations,
            "baseline_comparison": self._compare_with_baselines(benchmark_results)
        }

        return report

    def _analyze_performance_trends(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze performance trends across benchmarks"""
        trends = {}

        # Group by benchmark type
        by_type = {}
        for result in results:
            if result.benchmark_type not in by_type:
                by_type[result.benchmark_type] = []
            by_type[result.benchmark_type].append(result)

        # Analyze trends for each type
        for benchmark_type, type_results in by_type.items():
            if len(type_results) < 2:
                continue

            response_times = [r.avg_response_time for r in type_results]
            throughputs = [r.requests_per_second for r in type_results]

            trends[benchmark_type] = {
                "response_time_trend": "improving" if response_times[-1] < response_times[0] else "degrading",
                "throughput_trend": "improving" if throughputs[-1] > throughputs[0] else "degrading",
                "response_time_change": ((response_times[-1] - response_times[0]) / response_times[0] * 100) if response_times[0] > 0 else 0,
                "throughput_change": ((throughputs[-1] - throughputs[0]) / throughputs[0] * 100) if throughputs[0] > 0 else 0
            }

        return trends

    def _generate_performance_recommendations(self, results: List[BenchmarkResult]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []

        # Response time recommendations
        slow_endpoints = [
            r for r in results
            if r.benchmark_type == BenchmarkType.API_RESPONSE_TIME.value
            and r.avg_response_time > 2.0
        ]

        if slow_endpoints:
            recommendations.append(f"Optimize {len(slow_endpoints)} slow API endpoints - consider caching, query optimization, or async processing")

        # Throughput recommendations
        low_throughput = [
            r for r in results
            if r.requests_per_second < 10
        ]

        if low_throughput:
            recommendations.append(f"Improve throughput for {len(low_throughput)} benchmarks - consider load balancing or horizontal scaling")

        # Memory usage recommendations
        high_memory = [
            r for r in results
            if r.max_memory_usage > 1000  # > 1GB
        ]

        if high_memory:
            recommendations.append("Address high memory usage - implement memory profiling and optimization")

        # Memory leak recommendations
        memory_leaks = [r for r in results if r.memory_leak_detected]
        if memory_leaks:
            recommendations.append(f"Fix memory leaks in {len(memory_leaks)} components")

        # CPU usage recommendations
        high_cpu = [
            r for r in results
            if r.avg_cpu_usage > 80  # > 80%
        ]

        if high_cpu:
            recommendations.append("Optimize CPU-intensive operations - consider algorithm improvements or parallelization")

        # Error rate recommendations
        high_errors = [
            r for r in results
            if r.error_rate > 0.05  # > 5%
        ]

        if high_errors:
            recommendations.append(f"Reduce error rates in {len(high_errors)} benchmarks - improve error handling and resilience")

        if not recommendations:
            recommendations.append("Performance is within acceptable thresholds")

        return recommendations

    def _compare_with_baselines(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Compare results with baseline performance"""
        baseline_comparison = {
            "improvements": [],
            "regressions": [],
            "no_baseline": []
        }

        for result in results:
            if result.benchmark_type == BenchmarkType.API_RESPONSE_TIME.value:
                endpoint_name = result.config_name.split("_")[0]
                baseline = self.baseline_thresholds["api_endpoints"].get(endpoint_name)

                if baseline:
                    if result.avg_response_time < baseline.get("avg_response_time", float('inf')):
                        baseline_comparison["improvements"].append({
                            "benchmark": result.config_name,
                            "metric": "avg_response_time",
                            "current": result.avg_response_time,
                            "baseline": baseline["avg_response_time"],
                            "improvement_percent": ((baseline["avg_response_time"] - result.avg_response_time) / baseline["avg_response_time"] * 100)
                        })
                    elif result.avg_response_time > baseline.get("avg_response_time", float('inf')) * 1.2:  # 20% regression threshold
                        baseline_comparison["regressions"].append({
                            "benchmark": result.config_name,
                            "metric": "avg_response_time",
                            "current": result.avg_response_time,
                            "baseline": baseline["avg_response_time"],
                            "regression_percent": ((result.avg_response_time - baseline["avg_response_time"]) / baseline["avg_response_time"] * 100)
                        })
                else:
                    baseline_comparison["no_baseline"].append(result.config_name)

        return baseline_comparison

    async def run_comprehensive_benchmark_suite(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite"""
        logger.info("Starting comprehensive performance benchmark suite...")

        # Define benchmark configurations
        benchmark_configs = [
            # API benchmarks
            BenchmarkConfig(
                name="health_check_api",
                benchmark_type=BenchmarkType.API_RESPONSE_TIME,
                target_endpoint="/health",
                duration_seconds=60,
                concurrent_users=20,
                requests_per_second=100,
                response_time_threshold=0.5,
                throughput_threshold=100
            ),
            BenchmarkConfig(
                name="strategies_api",
                benchmark_type=BenchmarkType.API_RESPONSE_TIME,
                target_endpoint="/api/strategies/v2/",
                duration_seconds=60,
                concurrent_users=10,
                requests_per_second=50,
                response_time_threshold=1.0,
                throughput_threshold=50
            ),
            BenchmarkConfig(
                name="market_data_api",
                benchmark_type=BenchmarkType.API_RESPONSE_TIME,
                target_endpoint="/api/market/data",
                duration_seconds=60,
                concurrent_users=15,
                requests_per_second=30,
                response_time_threshold=2.0,
                throughput_threshold=30
            ),

            # Database benchmarks
            BenchmarkConfig(
                name="market_data_db",
                benchmark_type=BenchmarkType.DATABASE_PERFORMANCE,
                duration_seconds=60,
                total_requests=1000,
                response_time_threshold=0.1
            ),
            BenchmarkConfig(
                name="strategies_db",
                benchmark_type=BenchmarkType.DATABASE_PERFORMANCE,
                duration_seconds=60,
                total_requests=500,
                response_time_threshold=0.05
            ),

            # Algorithm benchmarks
            BenchmarkConfig(
                name="momentum_algorithm",
                benchmark_type=BenchmarkType.ALGORITHM_PERFORMANCE,
                duration_seconds=60,
                total_requests=1000,
                response_time_threshold=0.1
            ),
            BenchmarkConfig(
                name="risk_assessment",
                benchmark_type=BenchmarkType.ALGORITHM_PERFORMANCE,
                duration_seconds=60,
                total_requests=500,
                response_time_threshold=0.2
            ),
            BenchmarkConfig(
                name="portfolio_optimization",
                benchmark_type=BenchmarkType.ALGORITHM_PERFORMANCE,
                duration_seconds=60,
                total_requests=100,
                response_time_threshold=1.0
            )
        ]

        # Run benchmarks
        benchmark_results = []

        for config in benchmark_configs:
            logger.info(f"Running benchmark: {config.name}")

            if config.benchmark_type == BenchmarkType.API_RESPONSE_TIME:
                result = await self.run_api_benchmark(config)
            elif config.benchmark_type == BenchmarkType.DATABASE_PERFORMANCE:
                result = await self.run_database_benchmark(config)
            elif config.benchmark_type == BenchmarkType.ALGORITHM_PERFORMANCE:
                result = await self.run_algorithm_benchmark(config)
            else:
                continue

            benchmark_results.append(result)

            # Short break between benchmarks
            await asyncio.sleep(2)

        # Run scalability test
        scalability_test = BenchmarkConfig(
            name="api_scalability",
            benchmark_type=BenchmarkType.SCALABILITY,
            target_endpoint="/health"
        )
        scalability_results = await self.run_scalability_test(scalability_test)

        # Generate comprehensive report
        report = await self.generate_performance_report(benchmark_results)
        report["scalability_results"] = scalability_results

        # Log to InfluxDB
        await self._log_benchmark_results(report)

        logger.info(f"Benchmark suite complete: {report['report_metadata']['passed_benchmarks']}/{report['report_metadata']['total_benchmarks']} passed")

        return report

    async def _log_benchmark_results(self, report: Dict[str, Any]):
        """Log benchmark results to InfluxDB"""
        try:
            client = InfluxDBClient(**self.influx_config)
            write_api = client.write_api(write_options=SYNCHRONOUS)

            # Log summary metrics
            point = Point("performance_benchmark_summary") \
                .tag("test_run", report["report_metadata"]["generated_at"]) \
                .field("total_benchmarks", report["report_metadata"]["total_benchmarks"]) \
                .field("passed_benchmarks", report["report_metadata"]["passed_benchmarks"]) \
                .field("pass_rate", report["report_metadata"]["pass_rate"]) \
                .field("avg_response_time", report["performance_summary"]["avg_response_time"]) \
                .field("p95_response_time", report["performance_summary"]["p95_response_time"]) \
                .field("avg_throughput", report["performance_summary"]["avg_throughput"]) \
                .field("avg_cpu_usage", report["system_resources"]["avg_cpu_usage"]) \
                .field("avg_memory_usage", report["system_resources"]["avg_memory_usage"]) \
                .time(datetime.utcnow())

            write_api.write(bucket=self.influx_config["bucket"], record=point)
            client.close()

        except Exception as e:
            logger.error(f"Failed to log benchmark results to InfluxDB: {str(e)}")


if __name__ == "__main__":
    # Run benchmark suite
    async def main():
        suite = PerformanceBenchmarkSuite()
        report = await suite.run_comprehensive_benchmark_suite()

        print("\n" + "="*60)
        print("PERFORMANCE BENCHMARK SUITE REPORT")
        print("="*60)

        metadata = report["report_metadata"]
        print(f"Test Run: {metadata['generated_at']}")
        print(f"Total Benchmarks: {metadata['total_benchmarks']}")
        print(f"Passed: {metadata['passed_benchmarks']}")
        print(f"Failed: {metadata['failed_benchmarks']}")
        print(f"Pass Rate: {metadata['pass_rate']:.1f}%")

        summary = report["performance_summary"]
        print(f"\nPerformance Summary:")
        print(f"  Average Response Time: {summary['avg_response_time']:.3f}s")
        print(f"  P95 Response Time: {summary['p95_response_time']:.3f}s")
        print(f"  Average Throughput: {summary['avg_throughput']:.1f} RPS")
        print(f"  Peak Throughput: {summary['peak_throughput']:.1f} RPS")

        resources = report["system_resources"]
        print(f"\nSystem Resources:")
        print(f"  Average CPU Usage: {resources['avg_cpu_usage']:.1f}%")
        print(f"  Max CPU Usage: {resources['max_cpu_usage']:.1f}%")
        print(f"  Average Memory Usage: {resources['avg_memory_usage']:.1f} MB")
        print(f"  Max Memory Usage: {resources['max_memory_usage']:.1f} MB")
        print(f"  Memory Leaks Detected: {resources['memory_leaks_detected']}")

        scalability = report["scalability_results"]
        print(f"\nScalability Results:")
        print(f"  Scalability Score: {scalability['scalability_score']:.1f}/100")
        print(f"  Bottleneck Detected: {scalability['bottleneck_detected']}")
        print(f"  Max Sustainable Load: {scalability['max_sustainable_load']} concurrent users")

        baseline = report["baseline_comparison"]
        if baseline["improvements"]:
            print(f"\nPerformance Improvements:")
            for improvement in baseline["improvements"]:
                print(f"  ✓ {improvement['benchmark']}: {improvement['improvement_percent']:.1f}% better")

        if baseline["regressions"]:
            print(f"\nPerformance Regressions:")
            for regression in baseline["regressions"]:
                print(f"  ✗ {regression['benchmark']}: {regression['regression_percent']:.1f}% worse")

        print(f"\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

        print("="*60)

        # Save detailed report to file
        report_path = f"benchmark_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nDetailed report saved to: {report_path}")

    asyncio.run(main())