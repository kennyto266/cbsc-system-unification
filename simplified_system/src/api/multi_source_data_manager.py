#!/usr/bin/env python3
"""
多數據源管理器 - 高可用架構核心組件
Multi-Source Data Manager - High Availability Architecture Core Component

解決單點故障風險，提供99.9%可用性的數據獲取服務
"""

import asyncio
import aiohttp
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
import hashlib

# Setup logging
logger = logging.getLogger(__name__)

class DataSourceStatus(Enum):
    """數據源狀態枚舉"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DISABLED = "disabled"

class DataSourcePriority(Enum):
    """數據源優先級枚舉"""
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3
    FALLBACK = 4

@dataclass
class DataSourceConfig:
    """數據源配置"""
    name: str
    url: str
    priority: DataSourcePriority
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    enabled: bool = True
    api_key: Optional[str] = None
    rate_limit: int = 100  # requests per minute
    data_format: str = "json"  # json, csv, xml
    required_headers: Dict[str, str] = None
    health_check_interval: int = 60  # seconds

    def __post_init__(self):
        if self.required_headers is None:
            self.required_headers = {}

@dataclass
class HealthCheckResult:
    """健康檢查結果"""
    source_name: str
    status: DataSourceStatus
    response_time: float
    success_rate: float
    last_check: datetime
    error_message: Optional[str] = None
    data_quality_score: Optional[float] = None

@dataclass
class DataFetchResult:
    """數據獲取結果"""
    success: bool
    data: Optional[Dict[str, Any]]
    source_name: str
    response_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    cached: bool = False
    data_quality_score: Optional[float] = None

class EnhancedCacheManager:
    """增強的緩存管理器 - 支持多層緩存策略"""

    def __init__(self, cache_dir: str = "cache", redis_url: Optional[str] = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # 內存緩存 (L1)
        self.memory_cache: Dict[str, Dict] = {}
        self.memory_cache_ttl = 300  # 5 minutes

        # 磁盤緩存 (L2)
        self.disk_cache_ttl = 3600  # 1 hour

        # Redis緩存 (L3) - 可選
        self.redis_client = None
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Redis cache connected successfully")
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}")

        logger.info("Enhanced cache manager initialized")

    def _get_cache_key(self, symbol: str, duration: int, source: str = None) -> str:
        """生成緩存鍵"""
        key_data = f"{symbol}_{duration}_{source or 'any'}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_cache_valid(self, cache_data: Dict, ttl: int) -> bool:
        """檢查緩存是否有效"""
        if not cache_data or 'timestamp' not in cache_data:
            return False
        return (time.time() - cache_data['timestamp']) < ttl

    async def get(self, symbol: str, duration: int, source: str = None) -> Optional[Dict[str, Any]]:
        """多層緩存獲取數據"""
        cache_key = self._get_cache_key(symbol, duration, source)

        # L1: 內存緩存
        if cache_key in self.memory_cache:
            if self._is_cache_valid(self.memory_cache[cache_key], self.memory_cache_ttl):
                logger.debug(f"L1 cache hit for {cache_key}")
                return self.memory_cache[cache_key]['data']
            else:
                del self.memory_cache[cache_key]

        # L2: 磁盤緩存
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    if self._is_cache_valid(cache_data, self.disk_cache_ttl):
                        # 提升到L1緩存
                        self.memory_cache[cache_key] = cache_data
                        logger.debug(f"L2 cache hit for {cache_key}")
                        return cache_data['data']
                    else:
                        cache_file.unlink()  # 刪除過期緩存
            except Exception as e:
                logger.warning(f"Disk cache read error: {e}")
                if cache_file.exists():
                    cache_file.unlink()

        # L3: Redis緩存
        if self.redis_client:
            try:
                redis_data = self.redis_client.get(cache_key)
                if redis_data:
                    cache_data = json.loads(redis_data)
                    if self._is_cache_valid(cache_data, self.disk_cache_ttl):
                        # 提升到L1和L2緩存
                        self.memory_cache[cache_key] = cache_data
                        self._save_to_disk(cache_key, cache_data)
                        logger.debug(f"L3 cache hit for {cache_key}")
                        return cache_data['data']
            except Exception as e:
                logger.warning(f"Redis cache read error: {e}")

        return None

    async def set(self, symbol: str, duration: int, data: Dict[str, Any],
                  source: str = None, quality_score: float = None):
        """多層緩存設置數據"""
        cache_key = self._get_cache_key(symbol, duration, source)
        cache_data = {
            'data': data,
            'timestamp': time.time(),
            'source': source,
            'quality_score': quality_score
        }

        # L1: 內存緩存
        self.memory_cache[cache_key] = cache_data

        # L2: 磁盤緩存
        self._save_to_disk(cache_key, cache_data)

        # L3: Redis緩存
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    self.disk_cache_ttl,
                    json.dumps(cache_data, default=str)
                )
            except Exception as e:
                logger.warning(f"Redis cache write error: {e}")

    def _save_to_disk(self, cache_key: str, cache_data: Dict):
        """保存到磁盤緩存"""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Disk cache write error: {e}")

    def clear_expired(self):
        """清理過期緩存"""
        current_time = time.time()

        # 清理內存緩存
        expired_keys = [
            key for key, data in self.memory_cache.items()
            if not self._is_cache_valid(data, self.memory_cache_ttl)
        ]
        for key in expired_keys:
            del self.memory_cache[key]

        # 清理磁盤緩存
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    if not self._is_cache_valid(cache_data, self.disk_cache_ttl):
                        cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error cleaning cache file {cache_file}: {e}")
                if cache_file.exists():
                    cache_file.unlink()

        logger.info(f"Cleaned {len(expired_keys)} expired memory cache entries")

class DataSourceHealthMonitor:
    """數據源健康監控器"""

    def __init__(self, data_sources: Dict[str, DataSourceConfig]):
        self.data_sources = data_sources
        self.health_status: Dict[str, HealthCheckResult] = {}
        self.health_check_task = None
        self.running = False

    async def start_monitoring(self):
        """開始健康監控"""
        self.running = True
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Health monitoring started")

    async def stop_monitoring(self):
        """停止健康監控"""
        self.running = False
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")

    async def _health_check_loop(self):
        """健康檢查循環"""
        while self.running:
            try:
                await self._check_all_sources()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)

    async def _check_all_sources(self):
        """檢查所有數據源健康狀態"""
        tasks = []
        for name, config in self.data_sources.items():
            if config.enabled:
                tasks.append(self._check_source_health(name, config))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Health check error: {result}")

    async def _check_source_health(self, name: str, config: DataSourceConfig) -> HealthCheckResult:
        """檢查單個數據源健康狀態"""
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 發送健康檢查請求
                health_url = config.url

                # 根據數據源類型調整健康檢查
                if "18.180.162.113" in config.url:
                    # 中央API健康檢查
                    health_url = f"{config.url}/health"
                elif "api.hkma.gov.hk" in config.url:
                    # HKMA API健康檢查 - 使用最小參數
                    if "hibor" in config.url:
                        health_url = f"{config.url}?offset=0&pagesize=1"

                headers = config.required_headers.copy()
                if config.api_key:
                    headers['Authorization'] = f"Bearer {config.api_key}"

                response_time = (time.time() - start_time) * 1000

                async with session.get(health_url, headers=headers) as response:
                    if response.status == 200:
                        status = DataSourceStatus.HEALTHY
                        success_rate = 1.0
                        error_message = None
                        data_quality_score = await self._assess_data_quality(response, config)
                    else:
                        status = DataSourceStatus.UNHEALTHY
                        success_rate = 0.0
                        error_message = f"HTTP {response.status}"
                        data_quality_score = 0.0

        except asyncio.TimeoutError:
            status = DataSourceStatus.UNHEALTHY
            response_time = config.timeout * 1000
            success_rate = 0.0
            error_message = "Timeout"
            data_quality_score = 0.0

        except Exception as e:
            status = DataSourceStatus.UNHEALTHY
            response_time = (time.time() - start_time) * 1000
            success_rate = 0.0
            error_message = str(e)
            data_quality_score = 0.0

        health_result = HealthCheckResult(
            source_name=name,
            status=status,
            response_time=response_time,
            success_rate=success_rate,
            last_check=datetime.now(),
            error_message=error_message,
            data_quality_score=data_quality_score
        )

        self.health_status[name] = health_result

        logger.debug(f"Health check for {name}: {status.value} ({response_time:.2f}ms)")

        return health_result

    async def _assess_data_quality(self, response: aiohttp.ClientResponse,
                                  config: DataSourceConfig) -> float:
        """評估數據質量"""
        try:
            if response.content_length == 0:
                return 0.0

            # 簡單的數據質量評估
            data = await response.json()

            if isinstance(data, dict):
                # 檢查是否有數據
                if "data" in data or "result" in data or "records" in data:
                    return 0.9  # Good quality
                else:
                    return 0.5  # Medium quality
            else:
                return 0.3  # Low quality

        except Exception:
            return 0.0  # Very poor quality

    def get_healthy_sources(self) -> List[Tuple[str, DataSourceConfig]]:
        """獲取健康的數據源列表，按優先級排序"""
        healthy_sources = []

        for name, config in self.data_sources.items():
            if not config.enabled:
                continue

            health_status = self.health_status.get(name)
            if health_status and health_status.status == DataSourceStatus.HEALTHY:
                healthy_sources.append((name, config))

        # 按優先級排序
        healthy_sources.sort(key=lambda x: x[1].priority.value)
        return healthy_sources

    def get_source_status(self, name: str) -> Optional[HealthCheckResult]:
        """獲取指定數據源的狀態"""
        return self.health_status.get(name)

class MultiSourceDataManager:
    """多數據源管理器 - 核心組件"""

    def __init__(self, cache_dir: str = "cache", redis_url: Optional[str] = None):
        # 初始化數據源配置
        self.data_sources = self._initialize_data_sources()

        # 初始化組件
        self.cache_manager = EnhancedCacheManager(cache_dir, redis_url)
        self.health_monitor = DataSourceHealthMonitor(self.data_sources)

        # 性能統計
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'cache_hits': 0,
            'failover_count': 0,
            'average_response_time': 0.0
        }

        # 故障轉移配置
        self.failover_enabled = True
        self.max_failover_attempts = 3

        logger.info("Multi-source data manager initialized")

    def _initialize_data_sources(self) -> Dict[str, DataSourceConfig]:
        """初始化數據源配置"""
        return {
            "primary_central_api": DataSourceConfig(
                name="Primary Central API",
                url="http://18.180.162.113:9191",
                priority=DataSourcePriority.PRIMARY,
                timeout=30,
                max_retries=3,
                health_check_interval=60
            ),

            "secondary_binance": DataSourceConfig(
                name="Binance API",
                url="https://api.binance.com/api/v3",
                priority=DataSourcePriority.SECONDARY,
                timeout=20,
                max_retries=2,
                rate_limit=1200,
                required_headers={"User-Agent": "QuantSystem/1.0"}
            ),

            "fallback_alpha_vantage": DataSourceConfig(
                name="Alpha Vantage",
                url="https://www.alphavantage.co/query",
                priority=DataSourcePriority.FALLBACK,
                timeout=45,
                max_retries=1,
                api_key=None,  # Set via environment variable
                rate_limit=5  # Free tier limit
            ),

            "hkma_hibor": DataSourceConfig(
                name="HKMA HIBOR",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
                priority=DataSourcePriority.SECONDARY,
                timeout=30,
                max_retries=2,
                required_headers={"Accept": "application/json"}
            ),

            "hkma_monetary_base": DataSourceConfig(
                name="HKMA Monetary Base",
                url="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
                priority=DataSourcePriority.SECONDARY,
                timeout=30,
                max_retries=2,
                required_headers={"Accept": "application/json"}
            )
        }

    async def start(self):
        """啟動多數據源管理器"""
        await self.health_monitor.start_monitoring()

        # 清理過期緩存
        self.cache_manager.clear_expired()

        logger.info("Multi-source data manager started")

    async def stop(self):
        """停止多數據源管理器"""
        await self.health_monitor.stop_monitoring()
        logger.info("Multi-source data manager stopped")

    async def get_stock_data(self, symbol: str, duration_days: int = 1095) -> DataFetchResult:
        """
        獲取股票數據 - 支持自動故障轉移

        Args:
            symbol: 股票代碼 (e.g., "0700.hk")
            duration_days: 數據天數

        Returns:
            DataFetchResult: 包含數據和元信息的結果對象
        """
        self.request_stats['total_requests'] += 1
        start_time = time.time()

        # 首先嘗試從緩存獲取
        cached_data = await self.cache_manager.get(symbol, duration_days)
        if cached_data:
            self.request_stats['cache_hits'] += 1
            return DataFetchResult(
                success=True,
                data=cached_data,
                source_name="cache",
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now(),
                cached=True
            )

        # 獲取健康的數據源列表
        healthy_sources = self.health_monitor.get_healthy_sources()

        if not healthy_sources:
            # 如果沒有健康的數據源，嘗試所有啟用的數據源
            logger.warning("No healthy sources available, trying all enabled sources")
            healthy_sources = [(name, config) for name, config in self.data_sources.items()
                             if config.enabled]
            healthy_sources.sort(key=lambda x: x[1].priority.value)

        # 嘗試從每個數據源獲取數據
        for source_name, config in healthy_sources:
            try:
                result = await self._fetch_from_source(source_name, config, symbol, duration_days)

                if result.success:
                    # 成功獲取數據，更新緩存
                    await self.cache_manager.set(
                        symbol, duration_days, result.data,
                        source_name, result.data_quality_score
                    )

                    # 更新統計
                    self.request_stats['successful_requests'] += 1
                    response_time = (time.time() - start_time) * 1000
                    self._update_response_time(response_time)

                    logger.info(f"Successfully fetched {symbol} from {source_name}")
                    return result
                else:
                    logger.warning(f"Failed to fetch {symbol} from {source_name}: {result.error_message}")

            except Exception as e:
                logger.error(f"Error fetching {symbol} from {source_name}: {e}")
                continue

        # 所有數據源都失敗
        error_msg = f"All data sources failed for {symbol}"
        logger.error(error_msg)

        return DataFetchResult(
            success=False,
            data=None,
            source_name="none",
            response_time=(time.time() - start_time) * 1000,
            timestamp=datetime.now(),
            error_message=error_msg
        )

    async def _fetch_from_source(self, source_name: str, config: DataSourceConfig,
                                symbol: str, duration_days: int) -> DataFetchResult:
        """從指定數據源獲取數據"""
        start_time = time.time()

        try:
            timeout = aiohttp.ClientTimeout(total=config.timeout)
            headers = config.required_headers.copy()

            if config.api_key:
                headers['Authorization'] = f"Bearer {config.api_key}"

            async with aiohttp.ClientSession(timeout=timeout) as session:
                # 根據數據源類型構建請求
                url, params = self._build_request_url(config, symbol, duration_days)

                async with session.get(url, params=params, headers=headers) as response:
                    response_time = (time.time() - start_time) * 1000

                    if response.status == 200:
                        data = await response.json()

                        # 數據質量評估
                        quality_score = await self._assess_data_quality(data, config)

                        return DataFetchResult(
                            success=True,
                            data=data,
                            source_name=source_name,
                            response_time=response_time,
                            timestamp=datetime.now(),
                            data_quality_score=quality_score
                        )
                    else:
                        return DataFetchResult(
                            success=False,
                            data=None,
                            source_name=source_name,
                            response_time=response_time,
                            timestamp=datetime.now(),
                            error_message=f"HTTP {response.status}"
                        )

        except asyncio.TimeoutError:
            return DataFetchResult(
                success=False,
                data=None,
                source_name=source_name,
                response_time=config.timeout * 1000,
                timestamp=datetime.now(),
                error_message="Request timeout"
            )

        except Exception as e:
            return DataFetchResult(
                success=False,
                data=None,
                source_name=source_name,
                response_time=(time.time() - start_time) * 1000,
                timestamp=datetime.now(),
                error_message=str(e)
            )

    def _build_request_url(self, config: DataSourceConfig, symbol: str,
                          duration_days: int) -> Tuple[str, Dict]:
        """根據數據源配置構建請求URL和參數"""
        if "18.180.162.113" in config.url:
            # 中央API
            return f"{config.url}/inst/getInst", {
                "symbol": symbol.lower(),
                "duration": duration_days
            }

        elif "binance.com" in config.url:
            # Binance API
            return f"{config.url}/ticker/24hr", {
                "symbol": symbol.replace(".hk", "").upper() + "USDT"
            }

        elif "alphavantage.co" in config.url:
            # Alpha Vantage API
            return config.url, {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol.replace(".hk", ""),
                "outputsize": "compact",
                "apikey": config.api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
            }

        else:
            # HKMA APIs (不需要參數)
            return config.url, {}

    async def _assess_data_quality(self, data: Any, config: DataSourceConfig) -> float:
        """評估數據質量"""
        try:
            if not data or not isinstance(data, dict):
                return 0.0

            # 檢查數據完整性
            completeness = 0.0
            if "data" in data and data["data"]:
                completeness = min(len(data["data"]) / 100, 1.0)  # 假設100條為完整數據
            elif "records" in data and data["records"]:
                completeness = min(len(data["records"]) / 100, 1.0)
            elif "Time Series (Daily)" in data:
                completeness = min(len(data["Time Series (Daily)"]) / 100, 1.0)

            # 檢查數據結構
            structure_score = 0.0
            required_fields = ["close", "open", "high", "low"]
            if "data" in data and isinstance(data["data"], dict):
                for field in required_fields:
                    if field in data["data"]:
                        structure_score += 0.25

            # 檢查數據新鮮度
            freshness_score = 0.0
            # 這裡可以添加檢查數據時間戳的邏輯

            return (completeness * 0.5 + structure_score * 0.3 + freshness_score * 0.2)

        except Exception as e:
            logger.warning(f"Data quality assessment error: {e}")
            return 0.5  # 默認中等質量

    def _update_response_time(self, response_time: float):
        """更新平均響應時間"""
        current_avg = self.request_stats['average_response_time']
        total_requests = self.request_stats['total_requests']

        new_avg = (current_avg * (total_requests - 1) + response_time) / total_requests
        self.request_stats['average_response_time'] = new_avg

    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        healthy_sources = self.health_monitor.get_healthy_sources()

        return {
            "total_data_sources": len(self.data_sources),
            "healthy_data_sources": len(healthy_sources),
            "enabled_data_sources": len([s for s in self.data_sources.values() if s.enabled]),
            "request_statistics": self.request_stats.copy(),
            "cache_hit_rate": (
                self.request_stats['cache_hits'] / max(self.request_stats['total_requests'], 1)
            ),
            "success_rate": (
                self.request_stats['successful_requests'] / max(self.request_stats['total_requests'], 1)
            ),
            "average_response_time": self.request_stats['average_response_time'],
            "failover_enabled": self.failover_enabled,
            "health_status": {
                name: asdict(status) for name, status in self.health_monitor.health_status.items()
            }
        }

    def get_data_source_health(self) -> Dict[str, HealthCheckResult]:
        """獲取所有數據源的健康狀態"""
        return self.health_monitor.health_status.copy()

    async def force_health_check(self, source_name: str = None):
        """強制執行健康檢查"""
        if source_name:
            if source_name in self.data_sources:
                config = self.data_sources[source_name]
                return await self.health_monitor._check_source_health(source_name, config)
            else:
                raise ValueError(f"Unknown data source: {source_name}")
        else:
            await self.health_monitor._check_all_sources()
            return self.health_monitor.health_status

# Global instance for backward compatibility
_data_manager: Optional[MultiSourceDataManager] = None

async def get_data_manager() -> MultiSourceDataManager:
    """獲取全局數據管理器實例"""
    global _data_manager
    if _data_manager is None:
        _data_manager = MultiSourceDataManager()
        await _data_manager.start()
    return _data_manager

async def get_stock_data_robust(symbol: str, duration_days: int = 1095) -> DataFetchResult:
    """獲取股票數據的便捷函數"""
    manager = await get_data_manager()
    return await manager.get_stock_data(symbol, duration_days)