"""
Comprehensive API Test Suite
Tests all API endpoints with comprehensive validation
"""

import asyncio
import aiohttp
import pytest
import json
import time
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HTTPMethod(Enum):
    """HTTP methods enumeration"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class TestCategory(Enum):
    """Test categories"""
    AUTHENTICATION = "authentication"
    STRATEGIES = "strategies"
    BACKTEST = "backtest"
    MARKET_DATA = "market_data"
    PORTFOLIO = "portfolio"
    RISK_MANAGEMENT = "risk_management"
    WEBSOCKET = "websocket"
    MONITORING = "monitoring"


@dataclass
class APIEndpoint:
    """API endpoint definition"""
    name: str
    path: str
    method: HTTPMethod
    category: TestCategory
    auth_required: bool = True
    expected_status: int = 200
    timeout: float = 30.0
    request_schema: Optional[Dict] = None
    response_schema: Optional[Dict] = None
    rate_limit: Optional[int] = None  # requests per minute
    test_data: Optional[Dict] = None


@dataclass
class TestResult:
    """Test result data structure"""
    endpoint: str
    method: str
    success: bool
    status_code: Optional[int] = None
    response_time: float = 0.0
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class APITestConfig:
    """API test configuration"""
    base_url: str = "http://localhost:3003"
    api_version: str = "v2"
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    concurrent_requests: int = 10
    performance_threshold: float = 2.0  # seconds


class APITestValidator:
    """API response validator"""

    @staticmethod
    def validate_json_schema(data: Dict, schema: Dict) -> List[str]:
        """Validate JSON schema"""
        errors = []

        def validate_field(value, field_schema, path=""):
            if "type" in field_schema:
                expected_type = field_schema["type"]
                if expected_type == "string" and not isinstance(value, str):
                    errors.append(f"{path}: Expected string, got {type(value).__name__}")
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"{path}: Expected number, got {type(value).__name__}")
                elif expected_type == "boolean" and not isinstance(value, bool):
                    errors.append(f"{path}: Expected boolean, got {type(value).__name__}")
                elif expected_type == "array" and not isinstance(value, list):
                    errors.append(f"{path}: Expected array, got {type(value).__name__}")
                elif expected_type == "object" and not isinstance(value, dict):
                    errors.append(f"{path}: Expected object, got {type(value).__name__}")

            if "required" in field_schema:
                for required_field in field_schema["required"]:
                    if required_field not in value:
                        errors.append(f"{path}: Missing required field '{required_field}'")

            if "properties" in field_schema and isinstance(value, dict):
                for prop_name, prop_schema in field_schema["properties"].items():
                    if prop_name in value:
                        validate_field(
                            value[prop_name],
                            prop_schema,
                            f"{path}.{prop_name}" if path else prop_name
                        )

        validate_field(data, schema)
        return errors

    @staticmethod
    def validate_response_structure(response_data: Dict, endpoint: APIEndpoint) -> List[str]:
        """Validate response structure"""
        errors = []

        # Check for standard API response structure
        if "success" not in response_data:
            errors.append("Missing 'success' field in response")

        if response_data.get("success"):
            if "data" not in response_data:
                errors.append("Missing 'data' field in successful response")
        else:
            if "error" not in response_data:
                errors.append("Missing 'error' field in failed response")

        # Validate timestamp
        if "timestamp" not in response_data:
            errors.append("Missing 'timestamp' field in response")
        else:
            try:
                datetime.fromisoformat(response_data["timestamp"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                errors.append("Invalid timestamp format")

        # Validate endpoint-specific schema
        if endpoint.response_schema and response_data.get("success"):
            schema_errors = APITestValidator.validate_json_schema(
                response_data.get("data", {}),
                endpoint.response_schema
            )
            errors.extend(schema_errors)

        return errors


class ComprehensiveAPITestSuite:
    """Comprehensive API test suite"""

    def __init__(self, config: APITestConfig = None):
        self.config = config or APITestConfig()
        self.test_user = {
            "username": f"api_test_user_{uuid.uuid4().hex[:8]}",
            "email": f"api_test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "TestPassword123!",
            "role": "trader"
        }
        self.auth_token: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None

        # Define all API endpoints to test
        self.endpoints = self._define_api_endpoints()

    def _define_api_endpoints(self) -> List[APIEndpoint]:
        """Define all API endpoints to test"""

        # Response schemas for validation
        strategy_response_schema = {
            "type": "object",
            "required": ["id", "name", "type", "parameters", "created_at"],
            "properties": {
                "id": {"type": "number"},
                "name": {"type": "string"},
                "type": {"type": "string"},
                "description": {"type": "string"},
                "parameters": {"type": "object"},
                "created_at": {"type": "string"},
                "updated_at": {"type": "string"}
            }
        }

        backtest_response_schema = {
            "type": "object",
            "required": ["backtest_id", "status", "strategy_id"],
            "properties": {
                "backtest_id": {"type": "string"},
                "status": {"type": "string"},
                "strategy_id": {"type": "number"},
                "progress": {"type": "number"},
                "created_at": {"type": "string"}
            }
        }

        market_data_response_schema = {
            "type": "object",
            "required": ["symbol", "data"],
            "properties": {
                "symbol": {"type": "string"},
                "data": {"type": "array"},
                "metadata": {"type": "object"}
            }
        }

        endpoints = [
            # Authentication endpoints
            APIEndpoint(
                name="User Registration",
                path="/api/auth/register",
                method=HTTPMethod.POST,
                category=TestCategory.AUTHENTICATION,
                auth_required=False,
                expected_status=201,
                test_data={
                    "username": "new_user",
                    "email": "new@example.com",
                    "password": "Password123!",
                    "role": "trader"
                }
            ),
            APIEndpoint(
                name="User Login",
                path="/api/auth/login",
                method=HTTPMethod.POST,
                category=TestCategory.AUTHENTICATION,
                auth_required=False,
                expected_status=200,
                test_data={
                    "username": self.test_user["username"],
                    "password": self.test_user["password"]
                }
            ),
            APIEndpoint(
                name="Token Refresh",
                path="/api/auth/refresh",
                method=HTTPMethod.POST,
                category=TestCategory.AUTHENTICATION,
                auth_required=True,
                expected_status=200
            ),
            APIEndpoint(
                name="User Logout",
                path="/api/auth/logout",
                method=HTTPMethod.POST,
                category=TestCategory.AUTHENTICATION,
                auth_required=True,
                expected_status=200
            ),

            # Strategy management endpoints
            APIEndpoint(
                name="List Strategies",
                path="/api/strategies/v2/",
                method=HTTPMethod.GET,
                category=TestCategory.STRATEGIES,
                auth_required=True,
                expected_status=200
            ),
            APIEndpoint(
                name="Create Strategy",
                path="/api/strategies/v2/",
                method=HTTPMethod.POST,
                category=TestCategory.STRATEGIES,
                auth_required=True,
                expected_status=201,
                response_schema=strategy_response_schema,
                test_data={
                    "name": "test_momentum_strategy",
                    "type": "momentum",
                    "description": "Test momentum strategy",
                    "parameters": {
                        "lookback_period": 20,
                        "threshold": 0.02,
                        "symbols": ["AAPL", "GOOGL"]
                    }
                }
            ),
            APIEndpoint(
                name="Get Strategy",
                path="/api/strategies/v2/1",
                method=HTTPMethod.GET,
                category=TestCategory.STRATEGIES,
                auth_required=True,
                expected_status=200,
                response_schema=strategy_response_schema
            ),
            APIEndpoint(
                name="Update Strategy",
                path="/api/strategies/v2/1",
                method=HTTPMethod.PUT,
                category=TestCategory.STRATEGIES,
                auth_required=True,
                expected_status=200,
                test_data={
                    "description": "Updated strategy description",
                    "parameters": {
                        "lookback_period": 25,
                        "threshold": 0.025
                    }
                }
            ),
            APIEndpoint(
                name="Delete Strategy",
                path="/api/strategies/v2/999",
                method=HTTPMethod.DELETE,
                category=TestCategory.STRATEGIES,
                auth_required=True,
                expected_status=404
            ),

            # Backtest endpoints
            APIEndpoint(
                name="Submit Backtest",
                path="/api/backtest/v2/submit",
                method=HTTPMethod.POST,
                category=TestCategory.BACKTEST,
                auth_required=True,
                expected_status=202,
                response_schema=backtest_response_schema,
                test_data={
                    "strategy_id": 1,
                    "start_date": "2024-01-01T00:00:00Z",
                    "end_date": "2024-03-01T00:00:00Z",
                    "initial_capital": 100000,
                    "commission": 0.001
                }
            ),
            APIEndpoint(
                name="Get Backtest Status",
                path="/api/backtest/v2/status/test_backtest_123",
                method=HTTPMethod.GET,
                category=TestCategory.BACKTEST,
                auth_required=True,
                expected_status=200
            ),
            APIEndpoint(
                name="Get Backtest Results",
                path="/api/backtest/v2/results/test_backtest_123",
                method=HTTPMethod.GET,
                category=TestCategory.BACKTEST,
                auth_required=True,
                expected_status=404  # Not found for test ID
            ),

            # Market data endpoints
            APIEndpoint(
                name="Get Market Data",
                path="/api/market/data",
                method=HTTPMethod.GET,
                category=TestCategory.MARKET_DATA,
                auth_required=True,
                expected_status=200,
                response_schema=market_data_response_schema
            ),
            APIEndpoint(
                name="Get Technical Indicators",
                path="/api/market/indicators",
                method=HTTPMethod.POST,
                category=TestCategory.MARKET_DATA,
                auth_required=True,
                expected_status=200,
                test_data={
                    "symbol": "AAPL",
                    "indicators": ["SMA", "RSI", "MACD"],
                    "periods": [20, 14, 12]
                }
            ),

            # Portfolio endpoints
            APIEndpoint(
                name="Get Portfolio",
                path="/api/portfolio",
                method=HTTPMethod.GET,
                category=TestCategory.PORTFOLIO,
                auth_required=True,
                expected_status=200
            ),
            APIEndpoint(
                name="Get Portfolio Performance",
                path="/api/portfolio/performance",
                method=HTTPMethod.GET,
                category=TestCategory.PORTFOLIO,
                auth_required=True,
                expected_status=200
            ),

            # Risk management endpoints
            APIEndpoint(
                name="Get Risk Metrics",
                path="/api/risk/metrics",
                method=HTTPMethod.GET,
                category=TestCategory.RISK_MANAGEMENT,
                auth_required=True,
                expected_status=200
            ),
            APIEndpoint(
                name="Update Risk Settings",
                path="/api/risk/settings",
                method=HTTPMethod.PUT,
                category=TestCategory.RISK_MANAGEMENT,
                auth_required=True,
                expected_status=200,
                test_data={
                    "max_position_size": 0.1,
                    "max_portfolio_risk": 0.15,
                    "stop_loss_percentage": 0.05
                }
            ),

            # Monitoring endpoints
            APIEndpoint(
                name="System Health",
                path="/health",
                method=HTTPMethod.GET,
                category=TestCategory.MONITORING,
                auth_required=False,
                expected_status=200,
                timeout=5.0
            ),
            APIEndpoint(
                name="API Metrics",
                path="/api/monitoring/metrics",
                method=HTTPMethod.GET,
                category=TestCategory.MONITORING,
                auth_required=True,
                expected_status=200
            )
        ]

        return endpoints

    async def setup(self):
        """Setup test environment"""
        logger.info("Setting up API test environment...")

        # Create HTTP session
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_requests * 2,
            limit_per_host=self.config.concurrent_requests,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

        # Register and authenticate test user
        await self._setup_test_user()

    async def cleanup(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        logger.info("API test environment cleaned up")

    async def _setup_test_user(self):
        """Setup and authenticate test user"""
        try:
            # Register test user
            register_data = {
                **self.test_user,
                "confirm_password": self.test_user["password"]
            }

            async with self.session.post(
                f"{self.config.base_url}/api/auth/register",
                json=register_data
            ) as response:
                if response.status not in [201, 409]:  # 409 if user already exists
                    logger.warning(f"User registration failed: {response.status}")

            # Login and get auth token
            login_data = {
                "username": self.test_user["username"],
                "password": self.test_user["password"]
            }

            async with self.session.post(
                f"{self.config.base_url}/api/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    login_result = await response.json()
                    self.auth_token = login_result.get("access_token")
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    logger.info("Test user authenticated successfully")
                else:
                    logger.error(f"Test user login failed: {response.status}")

        except Exception as e:
            logger.error(f"Test user setup error: {str(e)}")

    async def execute_endpoint_test(self, endpoint: APIEndpoint) -> TestResult:
        """Execute single endpoint test"""
        result = TestResult(
            endpoint=endpoint.name,
            method=endpoint.method.value
        )

        try:
            # Prepare request
            url = f"{self.config.base_url}{endpoint.path}"
            headers = {}

            # Add authentication if required
            if endpoint.auth_required and not self.auth_token:
                result.success = False
                result.error_message = "Authentication required but no token available"
                return result

            if not endpoint.auth_required:
                # Remove authorization header for public endpoints
                headers = {k: v for k, v in self.session.headers.items() if k != "Authorization"}

            start_time = time.time()

            # Execute request based on method
            if endpoint.method == HTTPMethod.GET:
                async with self.session.get(url, headers=headers) as response:
                    result.status_code = response.status
                    result.response_data = await response.json()
            elif endpoint.method == HTTPMethod.POST:
                async with self.session.post(
                    url,
                    json=endpoint.test_data,
                    headers=headers
                ) as response:
                    result.status_code = response.status
                    result.response_data = await response.json()
            elif endpoint.method == HTTPMethod.PUT:
                async with self.session.put(
                    url,
                    json=endpoint.test_data,
                    headers=headers
                ) as response:
                    result.status_code = response.status
                    result.response_data = await response.json()
            elif endpoint.method == HTTPMethod.DELETE:
                async with self.session.delete(url, headers=headers) as response:
                    result.status_code = response.status
                    result.response_data = await response.json() if response.content_type == 'application/json' else {}
            else:
                raise ValueError(f"Unsupported HTTP method: {endpoint.method}")

            result.response_time = time.time() - start_time

            # Validate status code
            if result.status_code == endpoint.expected_status:
                result.success = True
            else:
                result.success = False
                result.error_message = f"Expected status {endpoint.expected_status}, got {result.status_code}"

            # Validate response structure
            if result.success and endpoint.response_schema:
                validator = APITestValidator()
                validation_errors = validator.validate_response_structure(
                    result.response_data,
                    endpoint
                )
                if validation_errors:
                    result.validation_errors = validation_errors
                    logger.warning(f"Validation errors for {endpoint.name}: {validation_errors}")

        except asyncio.TimeoutError:
            result.success = False
            result.error_message = f"Request timeout after {endpoint.timeout}s"
            result.response_time = endpoint.timeout

        except aiohttp.ClientError as e:
            result.success = False
            result.error_message = f"Client error: {str(e)}"

        except json.JSONDecodeError as e:
            result.success = False
            result.error_message = f"JSON decode error: {str(e)}"

        except Exception as e:
            result.success = False
            result.error_message = f"Unexpected error: {str(e)}"

        return result

    async def test_endpoint_with_retry(self, endpoint: APIEndpoint) -> TestResult:
        """Test endpoint with retry logic"""
        last_result = None

        for attempt in range(self.config.max_retries + 1):
            result = await self.execute_endpoint_test(endpoint)

            if result.success or not self._should_retry(result.status_code):
                return result

            if attempt < self.config.max_retries:
                logger.warning(f"Retrying {endpoint.name} (attempt {attempt + 1})")
                await asyncio.sleep(self.config.retry_delay)

            last_result = result

        return last_result

    def _should_retry(self, status_code: Optional[int]) -> bool:
        """Determine if request should be retried based on status code"""
        if status_code is None:
            return True
        # Retry on server errors and rate limiting
        return status_code in [429, 500, 502, 503, 504] or status_code >= 500

    async def run_category_tests(self, category: TestCategory) -> List[TestResult]:
        """Run all tests for a specific category"""
        logger.info(f"Running {category.value} tests...")

        category_endpoints = [
            ep for ep in self.endpoints if ep.category == category
        ]

        # Execute tests concurrently
        tasks = [
            self.test_endpoint_with_retry(endpoint)
            for endpoint in category_endpoints
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for endpoint, result in zip(category_endpoints, results):
            if isinstance(result, Exception):
                processed_results.append(TestResult(
                    endpoint=endpoint.name,
                    method=endpoint.method.value,
                    success=False,
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive API test suite"""
        logger.info("Starting comprehensive API test suite...")

        await self.setup()

        try:
            all_results = {}
            category_stats = {}

            # Run tests by category
            for category in TestCategory:
                if category == TestCategory.WEBSOCKET:
                    # Skip WebSocket tests in this suite
                    continue

                results = await self.run_category_tests(category)
                all_results[category.value] = results

                # Calculate category statistics
                successful = sum(1 for r in results if r.success)
                total = len(results)
                avg_response_time = sum(r.response_time for r in results) / total if total > 0 else 0

                category_stats[category.value] = {
                    "total": total,
                    "successful": successful,
                    "failed": total - successful,
                    "success_rate": (successful / total * 100) if total > 0 else 0,
                    "avg_response_time": avg_response_time
                }

            # Generate comprehensive report
            report = self._generate_test_report(all_results, category_stats)

            return report

        finally:
            await self.cleanup()

    def _generate_test_report(self, all_results: Dict, category_stats: Dict) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_endpoints = sum(stats["total"] for stats in category_stats.values())
        total_successful = sum(stats["successful"] for stats in category_stats.values())
        total_failed = total_endpoints - total_successful

        # Performance analysis
        all_response_times = []
        failed_tests = []

        for category, results in all_results.items():
            for result in results:
                all_response_times.append(result.response_time)
                if not result.success:
                    failed_tests.append({
                        "category": category,
                        "endpoint": result.endpoint,
                        "error": result.error_message,
                        "status_code": result.status_code
                    })

        avg_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        max_response_time = max(all_response_times) if all_response_times else 0

        # Performance bottlenecks
        slow_endpoints = [
            result for results in all_results.values()
            for result in results
            if result.response_time > self.config.performance_threshold
        ]

        report = {
            "test_summary": {
                "total_endpoints": total_endpoints,
                "successful": total_successful,
                "failed": total_failed,
                "success_rate": (total_successful / total_endpoints * 100) if total_endpoints > 0 else 0,
                "overall_success": total_failed == 0
            },
            "performance_metrics": {
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "performance_threshold": self.config.performance_threshold,
                "slow_endpoints_count": len(slow_endpoints),
                "slow_endpoints": [
                    {
                        "endpoint": result.endpoint,
                        "response_time": result.response_time,
                        "method": result.method
                    }
                    for result in slow_endpoints
                ]
            },
            "category_results": category_stats,
            "failed_tests": failed_tests,
            "test_timestamp": datetime.utcnow().isoformat(),
            "api_version": self.config.api_version,
            "recommendations": self._generate_recommendations(
                total_failed, avg_response_time, len(slow_endpoints)
            )
        }

        return report

    def _generate_recommendations(self, failed_count: int, avg_response_time: float,
                                slow_endpoints_count: int) -> List[str]:
        """Generate performance and reliability recommendations"""
        recommendations = []

        if failed_count > 0:
            recommendations.append(f"Fix {failed_count} failing endpoint(s) - check error messages for details")

        if avg_response_time > self.config.performance_threshold:
            recommendations.append("Optimize API performance - average response time exceeds threshold")

        if slow_endpoints_count > 0:
            recommendations.append(f"Investigate {slow_endpoints_count} slow endpoint(s) for optimization opportunities")

        success_rate = ((self._get_total_endpoints() - failed_count) / self._get_total_endpoints() * 100)
        if success_rate < 95:
            recommendations.append("Improve API reliability - success rate below 95%")

        if not recommendations:
            recommendations.append("All API endpoints are performing within acceptable thresholds")

        return recommendations

    def _get_total_endpoints(self) -> int:
        """Get total number of endpoints"""
        return len([ep for ep in self.endpoints if ep.category != TestCategory.WEBSOCKET])


# Pytest integration
@pytest.fixture
async def api_test_suite():
    """Create API test suite fixture"""
    config = APITestConfig(
        base_url="http://localhost:3003",
        concurrent_requests=5,
        performance_threshold=2.0
    )
    suite = ComprehensiveAPITestSuite(config)
    yield suite
    # Cleanup is handled by the suite itself


@pytest.mark.asyncio
async def test_all_api_endpoints(api_test_suite):
    """Test all API endpoints"""
    report = await api_test_suite.run_all_tests()

    # Assertions
    assert report["test_summary"]["success_rate"] >= 90, \
        f"API success rate too low: {report['test_summary']['success_rate']}%"

    assert report["performance_metrics"]["avg_response_time"] <= api_test_suite.config.performance_threshold, \
        f"Average response time too high: {report['performance_metrics']['avg_response_time']:.2f}s"

    # Log results
    logger.info(f"API Test Results: {report['test_summary']['successful']}/{report['test_summary']['total_endpoints']} passed")
    logger.info(f"Average response time: {report['performance_metrics']['avg_response_time']:.2f}s")

    if report["failed_tests"]:
        logger.warning("Failed tests:")
        for test in report["failed_tests"]:
            logger.warning(f"  - {test['category']}.{test['endpoint']}: {test['error']}")


@pytest.mark.asyncio
async def test_api_authentication_flow(api_test_suite):
    """Test authentication endpoints specifically"""
    await api_test_suite.setup()

    try:
        auth_endpoints = [
            ep for ep in api_test_suite.endpoints
            if ep.category == TestCategory.AUTHENTICATION
        ]

        results = []
        for endpoint in auth_endpoints:
            result = await api_test_suite.test_endpoint_with_retry(endpoint)
            results.append(result)

        successful = sum(1 for r in results if r.success)
        assert successful >= len(auth_endpoints) - 1, "Too many authentication endpoints failed"

        logger.info(f"Authentication tests: {successful}/{len(auth_endpoints)} passed")

    finally:
        await api_test_suite.cleanup()


if __name__ == "__main__":
    # Run tests directly
    async def main():
        suite = ComprehensiveAPITestSuite()
        report = await suite.run_all_tests()

        print("\n" + "="*50)
        print("COMPREHENSIVE API TEST RESULTS")
        print("="*50)
        print(f"Total Endpoints: {report['test_summary']['total_endpoints']}")
        print(f"Successful: {report['test_summary']['successful']}")
        print(f"Failed: {report['test_summary']['failed']}")
        print(f"Success Rate: {report['test_summary']['success_rate']:.1f}%")
        print(f"Average Response Time: {report['performance_metrics']['avg_response_time']:.3f}s")
        print(f"Max Response Time: {report['performance_metrics']['max_response_time']:.3f}s")

        if report["performance_metrics"]["slow_endpoints"]:
            print(f"\nSlow Endpoints ({report['performance_metrics']['slow_endpoints_count']}):")
            for endpoint in report["performance_metrics"]["slow_endpoints"]:
                print(f"  - {endpoint['endpoint']}: {endpoint['response_time']:.3f}s")

        if report["failed_tests"]:
            print(f"\nFailed Tests ({len(report['failed_tests'])}):")
            for test in report["failed_tests"]:
                print(f"  - {test['category']}.{test['endpoint']}: {test['error']}")

        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")

        print("="*50)

    asyncio.run(main())