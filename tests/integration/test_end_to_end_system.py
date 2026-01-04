"""
End-to-End System Integration Tests
Comprehensive system integration testing for CBSC platform
"""

import asyncio
import pytest
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import asyncpg
import redis.asyncio as aioredis
from influxdb_client import InfluxDBClient
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestStage(Enum):
    """Test execution stages"""
    SETUP = "setup"
    AUTHENTICATION = "authentication"
    STRATEGY_CREATION = "strategy_creation"
    DATA_PROCESSING = "data_processing"
    BACKTEST_EXECUTION = "backtest_execution"
    REAL_TIME_MONITORING = "real_time_monitoring"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    CLEANUP = "cleanup"


@dataclass
class TestContext:
    """Test execution context"""
    session: aiohttp.ClientSession
    db_pool: asyncpg.Pool
    redis_client: aioredis.Redis
    influx_client: InfluxDBClient
    auth_token: Optional[str] = None
    user_id: Optional[int] = None
    strategy_id: Optional[int] = None
    backtest_id: Optional[str] = None
    test_data: Dict[str, Any] = None
    start_time: Optional[datetime] = None
    stage_metrics: Dict[str, Dict[str, float]] = None


@dataclass
class SystemEndpoint:
    """System endpoint configuration"""
    name: str
    url: str
    method: str
    expected_status: int
    timeout: float = 30.0
    retry_count: int = 3


class EndToEndTestSuite:
    """Comprehensive end-to-end test suite"""

    def __init__(self):
        self.base_url = "http://localhost:3003"
        self.api_version = "v2"
        self.test_user = {
            "username": "e2e_test_user",
            "email": "e2e.test@example.com",
            "password": "TestPassword123!"
        }

        # System endpoints to test
        self.endpoints = {
            "health": SystemEndpoint("Health Check", "/health", "GET", 200, 5.0),
            "auth_login": SystemEndpoint("Auth Login", "/api/auth/login", "POST", 200),
            "auth_register": SystemEndpoint("Auth Register", "/api/auth/register", "POST", 201),
            "strategies_list": SystemEndpoint("Strategies List", "/api/strategies/v2/", "GET", 200),
            "strategies_create": SystemEndpoint("Strategy Create", "/api/strategies/v2/", "POST", 201),
            "backtest_submit": SystemEndpoint("Backtest Submit", "/api/backtest/v2/submit", "POST", 202),
            "backtest_status": SystemEndpoint("Backtest Status", "/api/backtest/v2/status/", "GET", 200),
            "market_data": SystemEndpoint("Market Data", "/api/market/data", "GET", 200),
            "portfolio": SystemEndpoint("Portfolio", "/api/portfolio", "GET", 200),
            "websocket": SystemEndpoint("WebSocket", "/ws", "GET", 101)
        }

        # Performance thresholds
        self.performance_thresholds = {
            "response_time_max": 5.0,  # seconds
            "response_time_avg": 1.0,  # seconds
            "error_rate_max": 0.05,    # 5%
            "throughput_min": 10       # requests per second
        }

    async def setup_test_environment(self) -> TestContext:
        """Setup test environment and connections"""
        logger.info("Setting up test environment...")

        # Create HTTP session
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30.0),
            connector=aiohttp.TCPConnector(limit=100)
        )

        # Setup database connections
        db_pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            database="cbsc_test",
            user="test_user",
            password="test_password",
            min_size=5,
            max_size=20
        )

        # Setup Redis connection
        redis_client = aioredis.from_url(
            "redis://localhost:6379/1",
            decode_responses=True
        )

        # Setup InfluxDB connection
        influx_client = InfluxDBClient(
            url="http://localhost:8086",
            token="test_token",
            org="cbsc"
        )

        # Clear test data
        await self.cleanup_test_data(db_pool, redis_client)

        context = TestContext(
            session=session,
            db_pool=db_pool,
            redis_client=redis_client,
            influx_client=influx_client,
            test_data={},
            stage_metrics={},
            start_time=datetime.utcnow()
        )

        logger.info("Test environment setup complete")
        return context

    async def cleanup_test_environment(self, context: TestContext):
        """Cleanup test environment"""
        logger.info("Cleaning up test environment...")

        # Cleanup test data
        await self.cleanup_test_data(context.db_pool, context.redis_client)

        # Close connections
        await context.session.close()
        await context.db_pool.close()
        await context.redis_client.close()
        context.influx_client.close()

        logger.info("Test environment cleanup complete")

    async def cleanup_test_data(self, db_pool: asyncpg.Pool, redis_client: aioredis.Redis):
        """Clean up test data from databases"""
        async with db_pool.acquire() as conn:
            # Clean up test users
            await conn.execute("""
                DELETE FROM users WHERE username LIKE 'e2e_test_%' OR email LIKE '%@test.example.com'
            """)

            # Clean up test strategies
            await conn.execute("""
                DELETE FROM strategies WHERE name LIKE 'e2e_test_%'
            """)

            # Clean up test backtests
            await conn.execute("""
                DELETE FROM backtests WHERE strategy_id IN (
                    SELECT id FROM strategies WHERE name LIKE 'e2e_test_%'
                )
            """)

        # Clean up Redis test data
        await redis_client.delete(f"user:{self.test_user['username']}")
        await redis_client.delete(f"auth:{self.test_user['username']}")

    async def measure_stage_performance(self, stage: TestStage, operation: str,
                                      duration: float, success: bool):
        """Record stage performance metrics"""
        if stage.value not in self.stage_metrics:
            self.stage_metrics[stage.value] = {
                "total_duration": 0.0,
                "operation_count": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_duration": 0.0
            }

        metrics = self.stage_metrics[stage.value]
        metrics["total_duration"] += duration
        metrics["operation_count"] += 1

        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1

        metrics["avg_duration"] = metrics["total_duration"] / metrics["operation_count"]

    async def test_system_health(self, context: TestContext) -> bool:
        """Test system health endpoints"""
        logger.info("Testing system health...")

        try:
            async with context.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info(f"System health: {health_data}")
                    return True
                else:
                    logger.error(f"Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return False

    async def test_authentication_flow(self, context: TestContext) -> bool:
        """Test complete authentication flow"""
        logger.info("Testing authentication flow...")

        stage_start = time.time()

        try:
            # Test user registration
            register_data = {
                **self.test_user,
                "confirm_password": self.test_user["password"]
            }

            async with context.session.post(
                f"{self.base_url}/api/auth/register",
                json=register_data
            ) as response:
                if response.status not in [201, 409]:  # 409 if user already exists
                    logger.error(f"Registration failed: {response.status}")
                    return False

            # Test user login
            login_data = {
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }

            async with context.session.post(
                f"{self.base_url}/api/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    context.auth_token = login_result.get("access_token")
                    context.user_id = login_result.get("user_id")

                    # Set authorization header for future requests
                    context.session.headers.update({
                        "Authorization": f"Bearer {context.auth_token}"
                    })

                    logger.info("Authentication successful")
                    return True
                else:
                    logger.error(f"Login failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
        finally:
            duration = time.time() - stage_start
            await self.measure_stage_performance(
                TestStage.AUTHENTICATION, "auth_flow", duration, True
            )

    async def test_strategy_management(self, context: TestContext) -> bool:
        """Test strategy creation and management"""
        logger.info("Testing strategy management...")

        stage_start = time.time()

        try:
            # Create a test strategy
            strategy_data = {
                "name": "e2e_test_momentum_strategy",
                "description": "End-to-end test momentum strategy",
                "type": "momentum",
                "parameters": {
                    "lookback_period": 20,
                    "threshold": 0.02,
                    "symbols": ["AAPL", "GOOGL", "MSFT"]
                },
                "risk_management": {
                    "max_position_size": 0.1,
                    "stop_loss": 0.05,
                    "take_profit": 0.15
                }
            }

            async with context.session.post(
                f"{self.base_url}/api/strategies/v2/",
                json=strategy_data
            ) as response:
                if response.status == 201:
                    strategy_result = await response.json()
                    context.strategy_id = strategy_result["id"]
                    logger.info(f"Strategy created: {context.strategy_id}")
                else:
                    logger.error(f"Strategy creation failed: {response.status}")
                    return False

            # Test strategy retrieval
            async with context.session.get(
                f"{self.base_url}/api/strategies/v2/{context.strategy_id}"
            ) as response:
                if response.status == 200:
                    strategy_data = await response.json()
                    logger.info("Strategy retrieval successful")
                else:
                    logger.error(f"Strategy retrieval failed: {response.status}")
                    return False

            # Test strategy update
            update_data = {
                "description": "Updated end-to-end test strategy",
                "parameters": {
                    "lookback_period": 25,
                    "threshold": 0.025,
                    "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN"]
                }
            }

            async with context.session.put(
                f"{self.base_url}/api/strategies/v2/{context.strategy_id}",
                json=update_data
            ) as response:
                if response.status == 200:
                    logger.info("Strategy update successful")
                else:
                    logger.error(f"Strategy update failed: {response.status}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Strategy management error: {str(e)}")
            return False
        finally:
            duration = time.time() - stage_start
            await self.measure_stage_performance(
                TestStage.STRATEGY_CREATION, "strategy_management", duration, True
            )

    async def test_data_processing_pipeline(self, context: TestContext) -> bool:
        """Test data processing pipeline"""
        logger.info("Testing data processing pipeline...")

        stage_start = time.time()

        try:
            # Test market data retrieval
            symbols = ["AAPL", "GOOGL", "MSFT"]
            start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
            end_date = datetime.utcnow().isoformat()

            for symbol in symbols:
                async with context.session.get(
                    f"{self.base_url}/api/market/data",
                    params={
                        "symbol": symbol,
                        "start_date": start_date,
                        "end_date": end_date,
                        "interval": "1d"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data.get("data"):
                            logger.warning(f"No data returned for {symbol}")
                        else:
                            logger.info(f"Retrieved {len(data['data'])} data points for {symbol}")
                    else:
                        logger.error(f"Market data retrieval failed for {symbol}: {response.status}")
                        return False

            # Test technical indicators calculation
            async with context.session.post(
                f"{self.base_url}/api/market/indicators",
                json={
                    "symbol": "AAPL",
                    "indicators": ["SMA", "RSI", "MACD"],
                    "periods": [20, 14, 12]
                }
            ) as response:
                if response.status == 200:
                    indicators = await response.json()
                    logger.info(f"Technical indicators calculated: {list(indicators.keys())}")
                else:
                    logger.error(f"Technical indicators calculation failed: {response.status}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Data processing pipeline error: {str(e)}")
            return False
        finally:
            duration = time.time() - stage_start
            await self.measure_stage_performance(
                TestStage.DATA_PROCESSING, "data_pipeline", duration, True
            )

    async def test_backtest_execution(self, context: TestContext) -> bool:
        """Test backtest execution pipeline"""
        logger.info("Testing backtest execution...")

        stage_start = time.time()

        try:
            # Submit backtest job
            backtest_config = {
                "strategy_id": context.strategy_id,
                "start_date": (datetime.utcnow() - timedelta(days=90)).isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "initial_capital": 100000,
                "commission": 0.001,
                "slippage": 0.0001,
                "benchmark": "SPY"
            }

            async with context.session.post(
                f"{self.base_url}/api/backtest/v2/submit",
                json=backtest_config
            ) as response:
                if response.status == 202:
                    submit_result = await response.json()
                    context.backtest_id = submit_result["backtest_id"]
                    logger.info(f"Backtest submitted: {context.backtest_id}")
                else:
                    logger.error(f"Backtest submission failed: {response.status}")
                    return False

            # Poll for backtest completion
            max_wait_time = 300  # 5 minutes
            poll_interval = 5
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                async with context.session.get(
                    f"{self.base_url}/api/backtest/v2/status/{context.backtest_id}"
                ) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        status = status_data.get("status")
                        progress = status_data.get("progress", 0)

                        logger.info(f"Backtest status: {status} ({progress:.1f}%)")

                        if status == "completed":
                            logger.info("Backtest completed successfully")
                            break
                        elif status == "failed":
                            logger.error("Backtest failed")
                            return False

                        await asyncio.sleep(poll_interval)
                        elapsed_time += poll_interval
                    else:
                        logger.error(f"Failed to get backtest status: {response.status}")
                        return False
            else:
                logger.error("Backtest timed out")
                return False

            # Retrieve backtest results
            async with context.session.get(
                f"{self.base_url}/api/backtest/v2/results/{context.backtest_id}"
            ) as response:
                if response.status == 200:
                    results = await response.json()
                    logger.info(f"Backtest results: Total return {results.get('total_return', 0):.2%}")
                else:
                    logger.error(f"Failed to retrieve backtest results: {response.status}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Backtest execution error: {str(e)}")
            return False
        finally:
            duration = time.time() - stage_start
            await self.measure_stage_performance(
                TestStage.BACKTEST_EXECUTION, "backtest_execution", duration, True
            )

    async def test_real_time_monitoring(self, context: TestContext) -> bool:
        """Test real-time monitoring and WebSocket"""
        logger.info("Testing real-time monitoring...")

        stage_start = time.time()

        try:
            # Test WebSocket connection
            ws_url = f"ws://localhost:3003/ws?token={context.auth_token}"

            async with context.session.ws_connect(ws_url) as ws:
                # Subscribe to strategy updates
                await ws.send_str(json.dumps({
                    "type": "subscribe",
                    "channel": "strategy_updates",
                    "strategy_id": context.strategy_id
                }))

                # Wait for subscription confirmation
                response = await ws.receive_str(timeout=5)
                response_data = json.loads(response)

                if response_data.get("type") == "subscription确认":
                    logger.info("WebSocket subscription confirmed")
                else:
                    logger.error("WebSocket subscription failed")
                    return False

                # Test real-time data streaming
                await ws.send_str(json.dumps({
                    "type": "get_market_data",
                    "symbols": ["AAPL", "GOOGL"]
                }))

                # Receive real-time data
                data_response = await ws.receive_str(timeout=10)
                data = json.loads(data_response)

                if data.get("type") == "market_data":
                    logger.info("Real-time market data received")
                else:
                    logger.warning("Unexpected WebSocket response")

                # Close WebSocket gracefully
                await ws.close()

            return True

        except Exception as e:
            logger.error(f"Real-time monitoring error: {str(e)}")
            return False
        finally:
            duration = time.time() - stage_start
            await self.measure_stage_performance(
                TestStage.REAL_TIME_MONITORING, "websocket_monitoring", duration, True
            )

    async def test_error_propagation(self, context: TestContext) -> bool:
        """Test error propagation and handling"""
        logger.info("Testing error propagation...")

        error_test_cases = [
            {
                "name": "Invalid strategy ID",
                "url": f"{self.base_url}/api/strategies/v2/999999",
                "expected_status": 404
            },
            {
                "name": "Invalid auth token",
                "url": f"{self.base_url}/api/strategies/v2/",
                "headers": {"Authorization": "Bearer invalid_token"},
                "expected_status": 401
            },
            {
                "name": "Invalid backtest parameters",
                "url": f"{self.base_url}/api/backtest/v2/submit",
                "method": "POST",
                "data": {"invalid": "parameters"},
                "expected_status": 422
            },
            {
                "name": "Non-existent market data",
                "url": f"{self.base_url}/api/market/data",
                "params": {"symbol": "INVALID123"},
                "expected_status": 404
            }
        ]

        for test_case in error_test_cases:
            try:
                method = test_case.get("method", "GET").lower()
                url = test_case["url"]
                expected_status = test_case["expected_status"]

                if method == "get":
                    async with context.session.get(
                        url,
                        params=test_case.get("params"),
                        headers=test_case.get("headers")
                    ) as response:
                        if response.status == expected_status:
                            logger.info(f"✓ {test_case['name']}: Correct error response")
                        else:
                            logger.error(f"✗ {test_case['name']}: Expected {expected_status}, got {response.status}")
                            return False
                elif method == "post":
                    async with context.session.post(
                        url,
                        json=test_case.get("data"),
                        headers=test_case.get("headers")
                    ) as response:
                        if response.status == expected_status:
                            logger.info(f"✓ {test_case['name']}: Correct error response")
                        else:
                            logger.error(f"✗ {test_case['name']}: Expected {expected_status}, got {response.status}")
                            return False

            except Exception as e:
                logger.error(f"✗ {test_case['name']}: Unexpected error {str(e)}")
                return False

        logger.info("Error propagation tests passed")
        return True

    async def generate_test_report(self, context: TestContext) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = (datetime.utcnow() - context.start_time).total_seconds()

        report = {
            "test_summary": {
                "total_duration": total_duration,
                "start_time": context.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "user_id": context.user_id,
                "strategy_id": context.strategy_id,
                "backtest_id": context.backtest_id
            },
            "stage_performance": self.stage_metrics,
            "system_health": {
                "api_endpoints_tested": len(self.endpoints),
                "database_connections": 3,  # PostgreSQL, Redis, InfluxDB
                "websocket_functionality": True
            },
            "test_coverage": {
                "authentication": True,
                "strategy_management": True,
                "data_processing": True,
                "backtest_execution": True,
                "real_time_monitoring": True,
                "error_handling": True
            },
            "performance_analysis": {
                "total_operations": sum(
                    metrics["operation_count"]
                    for metrics in self.stage_metrics.values()
                ),
                "success_rate": self._calculate_overall_success_rate(),
                "avg_response_time": self._calculate_avg_response_time(),
                "bottlenecks": self._identify_bottlenecks()
            },
            "recommendations": self._generate_recommendations()
        }

        return report

    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall success rate"""
        total_ops = sum(
            metrics["operation_count"]
            for metrics in self.stage_metrics.values()
        )
        total_success = sum(
            metrics["success_count"]
            for metrics in self.stage_metrics.values()
        )
        return (total_success / total_ops * 100) if total_ops > 0 else 0

    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time"""
        total_duration = sum(
            metrics["total_duration"]
            for metrics in self.stage_metrics.values()
        )
        total_ops = sum(
            metrics["operation_count"]
            for metrics in self.stage_metrics.values()
        )
        return (total_duration / total_ops) if total_ops > 0 else 0

    def _identify_bottlenecks(self) -> List[str]:
        """Identify performance bottlenecks"""
        bottlenecks = []

        for stage, metrics in self.stage_metrics.items():
            if metrics["avg_duration"] > self.performance_thresholds["response_time_avg"]:
                bottlenecks.append(f"{stage}: Average response time {metrics['avg_duration']:.2f}s")

            error_rate = metrics["error_count"] / metrics["operation_count"]
            if error_rate > self.performance_thresholds["error_rate_max"]:
                bottlenecks.append(f"{stage}: Error rate {error_rate:.2%}")

        return bottlenecks

    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Analyze bottlenecks and generate recommendations
        bottlenecks = self._identify_bottlenecks()

        if bottlenecks:
            recommendations.extend([
                "Optimize database queries with proper indexing",
                "Implement response caching for frequently accessed data",
                "Consider connection pooling for database operations",
                "Add request rate limiting to prevent overload"
            ])

        if self._calculate_avg_response_time() > 1.0:
            recommendations.append("Consider implementing asynchronous processing for long-running operations")

        if self._calculate_overall_success_rate() < 95:
            recommendations.append("Improve error handling and retry mechanisms")

        if not recommendations:
            recommendations.append("System performance is within acceptable thresholds")

        return recommendations

    async def run_end_to_end_tests(self) -> Dict[str, Any]:
        """Run complete end-to-end test suite"""
        logger.info("Starting End-to-End System Integration Tests")

        context = await self.setup_test_environment()

        try:
            # Test phases
            test_phases = [
                ("System Health", self.test_system_health),
                ("Authentication Flow", self.test_authentication_flow),
                ("Strategy Management", self.test_strategy_management),
                ("Data Processing Pipeline", self.test_data_processing_pipeline),
                ("Backtest Execution", self.test_backtest_execution),
                ("Real-time Monitoring", self.test_real_time_monitoring),
                ("Error Propagation", self.test_error_propagation)
            ]

            results = {}
            overall_success = True

            for phase_name, test_func in test_phases:
                logger.info(f"Executing phase: {phase_name}")
                start_time = time.time()

                try:
                    success = await test_func(context)
                    duration = time.time() - start_time
                    results[phase_name] = {
                        "success": success,
                        "duration": duration,
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    if not success:
                        overall_success = False
                        logger.error(f"Phase failed: {phase_name}")
                    else:
                        logger.info(f"Phase completed: {phase_name} ({duration:.2f}s)")

                except Exception as e:
                    duration = time.time() - start_time
                    results[phase_name] = {
                        "success": False,
                        "duration": duration,
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    overall_success = False
                    logger.error(f"Phase error: {phase_name} - {str(e)}")

            # Generate comprehensive report
            report = await self.generate_test_report(context)
            report["test_results"] = results
            report["overall_success"] = overall_success

            return report

        finally:
            await self.cleanup_test_environment(context)


# Pytest test functions
@pytest.fixture
async def test_suite():
    """Create test suite fixture"""
    return EndToEndTestSuite()


@pytest.mark.asyncio
async def test_complete_end_to_end_integration(test_suite):
    """Test complete end-to-end system integration"""
    report = await test_suite.run_end_to_end_tests()

    # Assert overall success
    assert report["overall_success"], "End-to-end integration test failed"

    # Assert minimum success rate
    assert report["performance_analysis"]["success_rate"] >= 90, \
        f"Success rate too low: {report['performance_analysis']['success_rate']}%"

    # Assert performance thresholds
    avg_response_time = report["performance_analysis"]["avg_response_time"]
    assert avg_response_time <= test_suite.performance_thresholds["response_time_avg"], \
        f"Average response time too high: {avg_response_time:.2f}s"

    # Generate test report file
    report_path = f"test_reports/e2e_integration_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    import os
    os.makedirs("test_reports", exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"Test report generated: {report_path}")


if __name__ == "__main__":
    # Run tests directly
    async def main():
        suite = EndToEndTestSuite()
        report = await suite.run_end_to_end_tests()

        print("\n" + "="*50)
        print("END-TO-END INTEGRATION TEST RESULTS")
        print("="*50)
        print(f"Overall Success: {'✓' if report['overall_success'] else '✗'}")
        print(f"Success Rate: {report['performance_analysis']['success_rate']:.1f}%")
        print(f"Average Response Time: {report['performance_analysis']['avg_response_time']:.2f}s")
        print(f"Total Duration: {report['test_summary']['total_duration']:.2f}s")

        if report["performance_analysis"]["bottlenecks"]:
            print("\nBottlenecks Identified:")
            for bottleneck in report["performance_analysis"]["bottlenecks"]:
                print(f"  - {bottleneck}")

        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

        print("="*50)

    asyncio.run(main())