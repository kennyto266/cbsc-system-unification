"""
異步HTTP客戶端 - Sprint 1核心實現

實現異步HTTP請求，支持：
- 連接池管理 (US - 002)
- 批量請求處理 (US - 003)
- 重試機制 (US - 004)
- Prometheus監控 (US - 005)
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import yaml
from aiohttp import ClientError, ClientTimeout
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Prometheus 監控指標
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)

HTTP_CONCURRENT_REQUESTS = Gauge(
    "http_concurrent_requests", "Number of concurrent HTTP requests", ["host"]
)

HTTP_CONNECTION_POOL_SIZE = Gauge("http_connection_pool_size", "Connection pool size")

HTTP_RETRIES_TOTAL = Counter(
    "http_retries_total", "Total HTTP retries", ["method", "endpoint", "error_type"]
)


class AsyncHTTPClient:
    """異步HTTP客戶端，支持連接池、重試、超時、監控等特性"""

    def __init__(
        self,
        max_connections: int = 1000,
        max_connections_per_host: int = 100,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff_factor: float = 2.0,
        config_path: Optional[str] = None,
    ):
        """
        初始化異步HTTP客戶端

        Args:
            max_connections: 總連接池大小
            max_connections_per_host: 每主機連接限制
            timeout: 請求超時（秒）
            max_retries: 最大重試次數
            retry_backoff_factor: 指數退避因子
            config_path: 配置文件路徑
        """
        self.max_connections = max_connections
        self.max_connections_per_host = max_connections_per_host
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        self._config = self._load_config(config_path) if config_path else {}

        # 連接池配置
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections_per_host,
            keepalive_timeout=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
            enable_cleanup_closed=True,
            loop=asyncio.get_event_loop(),
        )

        logger.info(
            f"HTTP Client initialized: pool={max_connections}, "
            f"per_host={max_connections_per_host}, timeout={timeout}s"
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加載配置文件"""
        try:
            with open(config_path, "r", encoding="utf - 8") as f:
                config = yaml.safe_load(f)
                logger.info(f"Config loaded from {config_path}")
                return config.get("http_client", {})
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
            return {}

    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()

    async def create_session(self):
        """創建HTTP會話"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=self.connector, timeout=self.timeout
            )
            logger.info("HTTP session created")
            HTTP_CONNECTION_POOL_SIZE.set(self.max_connections)

    async def close(self):
        """關閉HTTP會話"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("HTTP session closed")

    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        發送HTTP請求（內部方法）

        Args:
            method: HTTP方法
            url: 請求URL
            **kwargs: 其他參數

        Returns:
            響應數據字典
        """
        start_time = asyncio.get_event_loop().time()
        endpoint = url.split("?")[0]
        host = self._extract_host(url)

        # 獲取並發數計數器
        concurrent_counter = HTTP_CONCURRENT_REQUESTS.labels(host=host)
        concurrent_counter.inc()

        try:
            for attempt in range(self.max_retries + 1):
                try:
                    async with self.session.request(method, url, **kwargs) as response:
                        # 記錄響應時間
                        duration = asyncio.get_event_loop().time() - start_time
                        HTTP_REQUEST_DURATION.labels(
                            method=method, endpoint=endpoint
                        ).observe(duration)

                        # 記錄請求總數
                        status = "success" if 200 <= response.status < 300 else "error"
                        HTTP_REQUESTS_TOTAL.labels(
                            method=method, endpoint=endpoint, status=status
                        ).inc()

                        # 檢查響應狀態
                        response.raise_for_status()
                        data = await response.json()

                        logger.info(
                            f"Request successful: {method} {url} "
                            f"({duration:.3f}s, attempt {attempt + 1})"
                        )

                        return {
                            "status": response.status,
                            "data": data,
                            "headers": dict(response.headers),
                            "duration": duration,
                            "attempts": attempt + 1,
                            "success": True,
                        }

                except (ClientError, asyncio.TimeoutError) as e:
                    # 判斷是否應該重試
                    if attempt == self.max_retries:
                        HTTP_RETRIES_TOTAL.labels(
                            method=method,
                            endpoint=endpoint,
                            error_type=type(e).__name__,
                        ).inc()

                        logger.error(
                            f"Request failed after {attempt + 1} attempts: {e}"
                        )
                        return {
                            "success": False,
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "attempts": attempt + 1,
                        }

                    # 指數退避重試
                    wait_time = self.retry_backoff_factor ** attempt
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                        f"retrying in {wait_time}s: {e}"
                    )

                    HTTP_RETRIES_TOTAL.labels(
                        method=method, endpoint=endpoint, error_type=type(e).__name__
                    ).inc()

                    await asyncio.sleep(wait_time)

        finally:
            concurrent_counter.dec()

    def _extract_host(self, url: str) -> str:
        """提取URL的主機名"""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return "unknown"

    async def get(
        self, url: str, params: Optional[Dict] = None, **kwargs
    ) -> Dict[str, Any]:
        """GET請求"""
        return await self._make_request("GET", url, params=params, **kwargs)

    async def post(
        self,
        url: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """POST請求"""
        return await self._make_request("POST", url, data=data, json=json, **kwargs)

    async def batch_request(
        self, requests: List[Dict[str, Any]], max_concurrent: int = 100
    ) -> List[Dict[str, Any]]:
        """
        批量發送請求 (US - 003)

        Args:
            requests: 請求列表，每個元素包含 {'method', 'url', 'params': {}}
            max_concurrent: 最大併發數

        Returns:
            響應列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        start_time = asyncio.get_event_loop().time()

        async def bounded_request(req):
            async with semaphore:
                method = req.get("method", "GET")
                url = req["url"]
                params = req.get("params")
                json_data = req.get("json")
                return await self._make_request(
                    method, url, params=params, json=json_data
                )

        # 創建所有任務
        tasks = [bounded_request(req) for req in requests]

        # 執行所有任務
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 處理結果
        processed_results = []
        total_duration = asyncio.get_event_loop().time() - start_time

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch request {i} failed: {result}")
                processed_results.append(
                    {"success": False, "error": str(result), "request_index": i}
                )
            else:
                result["request_index"] = i
                processed_results.append(result)

        # 統計結果
        success_count = sum(1 for r in processed_results if r.get("success"))
        total_requests = len(requests)
        avg_duration = total_duration / max(total_requests, 1)

        logger.info(
            f"Batch request completed: {success_count}/{total_requests} successful, "
            f"total={total_duration:.3f}s, avg={avg_duration:.3f}s"
        )

        return processed_results

    async def get_pool_status(self) -> Dict[str, Any]:
        """獲取連接池狀態"""
        if not self.connector:
            return {"error": "Connector not initialized"}

        return {
            "total_connections": self.connector._limit,
            "max_per_host": self.connector._limit_per_host,
            "keepalive_timeout": getattr(self.connector, "_keepalive_timeout", 30),
            "dns_cache_ttl": getattr(self.connector, "_ttl_dns_cache", 300),
            "use_dns_cache": getattr(self.connector, "_use_dns_cache", True),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """獲取Prometheus指標"""
        return {
            "requests_total": (
                HTTP_REQUESTS_TOTAL._value._sum._value
                if hasattr(HTTP_REQUESTS_TOTAL, "_value")
                else 0
            ),
            "request_duration_seconds_sum": (
                HTTP_REQUEST_DURATION._sum._value
                if hasattr(HTTP_REQUEST_DURATION, "_sum")
                else 0
            ),
            "concurrent_requests": (
                HTTP_CONCURRENT_REQUESTS._value._value
                if hasattr(HTTP_CONCURRENT_REQUESTS, "_value")
                else 0
            ),
            "retries_total": (
                HTTP_RETRIES_TOTAL._value._sum._value
                if hasattr(HTTP_RETRIES_TOTAL, "_value")
                else 0
            ),
        }
