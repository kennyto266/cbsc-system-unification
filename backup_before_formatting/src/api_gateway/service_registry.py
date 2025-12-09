#!/usr / bin / env python3
"""
服務註冊中心
港股量化交易系統 - 微服務發現和管理

提供服務註冊、發現、健康檢查、負載均衡、
故障轉移等微服務治理功能。

主要功能:
- 服務註冊和發現
- 服務健康檢查
- 負載均衡
- 故障轉移
- 服務配置管理
- 服務監控和告警
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import httpx
import redis

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """服務狀態枚舉"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class LoadBalancingStrategy(str, Enum):
    """負載均衡策略"""

    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"


@dataclass
class ServiceInstance:
    """服務實例"""

    id: str
    name: str
    host: str
    port: int
    scheme: str = "http"
    weight: int = 1
    metadata: Dict[str, Any] = None

    @property
    def url(self) -> str:
        """獲取服務URL"""
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def health_check_url(self) -> str:
        """獲取健康檢查URL"""
        health_path = self.metadata.get("health_check_path", "/health")
        return urljoin(self.url, health_path)


@dataclass
class ServiceConfig:
    """服務配置"""

    name: str
    prefix: str = "/api / v1"
    health_check_path: str = "/health"
    health_check_interval: int = 30
    health_check_timeout: int = 5
    health_check_retries: int = 3
    timeout: int = 30
    retries: int = 3
    load_balancing: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    metadata: Dict[str, Any] = None


@dataclass
class ServiceStats:
    """服務統計"""

    name: str
    instance_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    consecutive_failures: int = 0
    is_circuit_open: bool = False
    circuit_open_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def error_rate(self) -> float:
        """錯誤率"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


class CircuitBreaker:
    """斷路器"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def call(self, func, *args, **kwargs):
        """執行函數並應用斷路器邏輯"""
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """是否應該嘗試重置斷路器"""
        return (
            self.last_failure_time
            and time.time() - self.last_failure_time >= self.timeout
        )

    def _on_success(self):
        """成功時的處理"""
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        """失敗時的處理"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class LoadBalancer:
    """負載均衡器"""

    def __init__(
        self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    ):
        self.strategy = strategy
        self.round_robin_index = 0
        self.instance_connections: Dict[str, int] = {}

    def select_instance(
        self, instances: List[ServiceInstance]
    ) -> Optional[ServiceInstance]:
        """選擇實例"""
        if not instances:
            return None

        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin(instances)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections(instances)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return self._random(instances)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin(instances)
        else:
            return instances[0]

    def _round_robin(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """輪詢選擇"""
        instance = instances[self.round_robin_index % len(instances)]
        self.round_robin_index += 1
        return instance

    def _least_connections(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """最少連接選擇"""
        return min(instances, key=lambda i: self.instance_connections.get(i.id, 0))

    def _random(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """隨機選擇"""
        import random

        return random.choice(instances)

    def _weighted_round_robin(
        self, instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """加權輪詢選擇"""
        weighted_instances = []
        for instance in instances:
            weighted_instances.extend([instance] * instance.weight)

        return self._round_robin(weighted_instances)

    def increment_connections(self, instance_id: str):
        """增加連接數"""
        self.instance_connections[instance_id] = (
            self.instance_connections.get(instance_id, 0) + 1
        )

    def decrement_connections(self, instance_id: str):
        """減少連接數"""
        current = self.instance_connections.get(instance_id, 0)
        if current > 0:
            self.instance_connections[instance_id] = current - 1


class HealthChecker:
    """健康檢查器"""

    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def check_health(
        self, instance: ServiceInstance, timeout: int = 5
    ) -> ServiceStatus:
        """檢查實例健康狀態"""
        try:
            response = await self.http_client.get(
                instance.health_check_url, timeout=timeout
            )

            if response.status_code == 200:
                try:
                    health_data = response.json()
                    status = health_data.get("status", "unknown")
                    if status == "healthy":
                        return ServiceStatus.HEALTHY
                    elif status == "degraded":
                        return ServiceStatus.DEGRADED
                    elif status == "maintenance":
                        return ServiceStatus.MAINTENANCE
                    else:
                        return ServiceStatus.UNHEALTHY
                except (json.JSONDecodeError, KeyError):
                    return ServiceStatus.HEALTHY
            else:
                return ServiceStatus.UNHEALTHY

        except Exception as e:
            logger.debug(f"健康檢查失敗 {instance.url}: {e}")
            return ServiceStatus.UNHEALTHY


class ServiceRegistry:
    """服務註冊中心"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.services: Dict[str, ServiceConfig] = {}
        self.instances: Dict[str, List[ServiceInstance]] = {}
        self.instance_stats: Dict[str, ServiceStats] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        self.health_checker = None
        self.load_balancers: Dict[str, LoadBalancer] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        # 初始化HTTP客戶端
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.health_checker = HealthChecker(self.http_client)

    def register_service(self, config: ServiceConfig):
        """註冊服務配置"""
        self.services[config.name] = config
        self.load_balancers[config.name] = LoadBalancer(config.load_balancing)

        if config.name not in self.instances:
            self.instances[config.name] = []

        logger.info(f"服務已註冊: {config.name}")

    def register_instance(self, instance: ServiceInstance):
        """註冊服務實例"""
        if instance.name not in self.instances:
            self.instances[instance.name] = []

        # 檢查是否已存在
        existing = next(
            (i for i in self.instances[instance.name] if i.id == instance.id), None
        )

        if existing:
            # 更新現有實例
            existing.host = instance.host
            existing.port = instance.port
            existing.metadata = instance.metadata
        else:
            # 添加新實例
            self.instances[instance.name].append(instance)

        # 初始化統計和斷路器
        if instance.id not in self.instance_stats:
            config = self.services.get(instance.name)
            if config:
                self.instance_stats[instance.id] = ServiceStats(
                    name=instance.name, instance_id=instance.id
                )
                self.circuit_breakers[instance.id] = CircuitBreaker(
                    failure_threshold=config.circuit_breaker_threshold,
                    timeout=config.circuit_breaker_timeout,
                )

        # 同步到Redis
        if self.redis_client:
            self._sync_to_redis()

        logger.info(f"服務實例已註冊: {instance.name}/{instance.id}")

    def unregister_instance(self, service_name: str, instance_id: str):
        """註銷服務實例"""
        if service_name in self.instances:
            self.instances[service_name] = [
                i for i in self.instances[service_name] if i.id != instance_id
            ]

            # 清理統計
            if instance_id in self.instance_stats:
                del self.instance_stats[instance_id]
            if instance_id in self.circuit_breakers:
                del self.circuit_breakers[instance_id]

            # 同步到Redis
            if self.redis_client:
                self._sync_to_redis()

            logger.info(f"服務實例已註銷: {service_name}/{instance_id}")

    def get_service_instances(self, service_name: str) -> List[ServiceInstance]:
        """獲取服務實例列表"""
        return self.instances.get(service_name, [])

    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """獲取健康的服務實例"""
        instances = self.get_service_instances(service_name)
        healthy_instances = []

        for instance in instances:
            stats = self.instance_stats.get(instance.id)
            if stats and not stats.is_circuit_open:
                # 檢查健康狀態
                status = self._get_instance_status(instance.id)
                if status in [ServiceStatus.HEALTHY, ServiceStatus.DEGRADED]:
                    healthy_instances.append(instance)

        return healthy_instances

    async def select_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """選擇服務實例"""
        healthy_instances = self.get_healthy_instances(service_name)

        if not healthy_instances:
            # 如果沒有健康實例，嘗試所有實例
            all_instances = self.get_service_instances(service_name)
            if all_instances:
                logger.warning(f"服務 {service_name} 沒有健康實例，使用降級策略")
                return all_instances[0]
            return None

        load_balancer = self.load_balancers.get(service_name)
        if not load_balancer:
            return healthy_instances[0]

        selected = load_balancer.select_instance(healthy_instances)
        if selected:
            load_balancer.increment_connections(selected.id)

        return selected

    async def call_service(
        self, service_name: str, path: str, method: str = "GET", **kwargs
    ) -> Tuple[httpx.Response, ServiceInstance]:
        """調用服務"""
        # 選擇實例
        instance = await self.select_instance(service_name)
        if not instance:
            raise Exception(f"服務 {service_name} 没有可用實例")

        # 構建URL
        url = urljoin(instance.url, path)
        config = self.services.get(service_name)

        try:
            # 獲取斷路器
            circuit_breaker = self.circuit_breakers.get(instance.id)
            if circuit_breaker:
                response = await circuit_breaker.call(
                    self._make_request,
                    method,
                    url,
                    config.timeout if config else 30,
                    **kwargs,
                )
            else:
                response = await self._make_request(
                    method, url, config.timeout if config else 30, **kwargs
                )

            # 更新統計
            self._update_stats(
                instance.id,
                True,
                response.elapsed.total_seconds() if hasattr(response, "elapsed") else 0,
            )

            return response, instance

        except Exception as e:
            # 更新統計
            self._update_stats(instance.id, False, 0)
            raise e
        finally:
            # 減少連接數
            load_balancer = self.load_balancers.get(service_name)
            if load_balancer:
                load_balancer.decrement_connections(instance.id)

    async def _make_request(
        self, method: str, url: str, timeout: int, **kwargs
    ) -> httpx.Response:
        """發送HTTP請求"""
        return await self.http_client.request(
            method=method, url=url, timeout=timeout, **kwargs
        )

    def _update_stats(self, instance_id: str, success: bool, response_time: float):
        """更新實例統計"""
        stats = self.instance_stats.get(instance_id)
        if not stats:
            return

        stats.total_requests += 1
        stats.last_request_time = datetime.utcnow()

        if success:
            stats.successful_requests += 1
            stats.consecutive_failures = 0

            # 更新平均響應時間
            total_time = (
                stats.avg_response_time * (stats.successful_requests - 1)
                + response_time
            )
            stats.avg_response_time = total_time / stats.successful_requests

        else:
            stats.failed_requests += 1
            stats.consecutive_failures += 1

            # 檢查是否需要打開斷路器
            circuit_breaker = self.circuit_breakers.get(instance_id)
            if (
                circuit_breaker
                and stats.consecutive_failures >= circuit_breaker.failure_threshold
            ):
                stats.is_circuit_open = True
                stats.circuit_open_time = datetime.utcnow()
                logger.warning(f"斷路器已打開: {instance_id}")

    def _get_instance_status(self, instance_id: str) -> ServiceStatus:
        """獲取實例狀態"""
        stats = self.instance_stats.get(instance_id)
        if not stats:
            return ServiceStatus.UNKNOWN

        if stats.is_circuit_open:
            return ServiceStatus.UNHEALTHY

        if stats.consecutive_failures > 0:
            return ServiceStatus.DEGRADED

        return ServiceStatus.HEALTHY

    async def start_health_check(self):
        """啟動健康檢查"""
        if self.health_check_task:
            return

        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("健康檢查已啟動")

    async def stop_health_check(self):
        """停止健康檢查"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
            self.health_check_task = None

        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
            self.cleanup_task = None

        logger.info("健康檢查已停止")

    async def _health_check_loop(self):
        """健康檢查循環"""
        while True:
            try:
                await self._check_all_services()
                await asyncio.sleep(30)  # 30秒檢查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康檢查循環錯誤: {e}")
                await asyncio.sleep(10)

    async def _check_all_services(self):
        """檢查所有服務"""
        check_tasks = []

        for service_name, instances in self.instances.items():
            config = self.services.get(service_name)
            if not config:
                continue

            for instance in instances:
                task = asyncio.create_task(self._check_instance(instance, config))
                check_tasks.append(task)

        if check_tasks:
            await asyncio.gather(*check_tasks, return_exceptions=True)

    async def _check_instance(self, instance: ServiceInstance, config: ServiceConfig):
        """檢查單個實例"""
        try:
            status = await self.health_checker.check_health(
                instance, config.health_check_timeout
            )

            # 更新實例狀態
            if instance.id not in self.instance_stats:
                self.instance_stats[instance.id] = ServiceStats(
                    name=instance.name, instance_id=instance.id
                )

            stats = self.instance_stats[instance.id]

            # 根據健康狀態更新斷路器
            circuit_breaker = self.circuit_breakers.get(instance.id)
            if circuit_breaker:
                if status == ServiceStatus.HEALTHY:
                    if stats.is_circuit_open:
                        # 嘗試關閉斷路器
                        stats.is_circuit_open = False
                        stats.circuit_open_time = None
                        circuit_breaker.failure_count = 0
                        circuit_breaker.state = "CLOSED"
                        logger.info(f"斷路器已關閉: {instance.id}")

        except Exception as e:
            logger.error(f"檢查實例失敗 {instance.id}: {e}")

    def _sync_to_redis(self):
        """同步數據到Redis"""
        if not self.redis_client:
            return

        try:
            # 同步服務配置
            services_data = {
                name: asdict(config) for name, config in self.services.items()
            }
            self.redis_client.set("services:configs", json.dumps(services_data))

            # 同步實例信息
            instances_data = {}
            for service_name, instances in self.instances.items():
                instances_data[service_name] = [
                    asdict(instance) for instance in instances
                ]

            self.redis_client.set("services:instances", json.dumps(instances_data))

            # 同步統計信息
            stats_data = {
                instance_id: asdict(stats)
                for instance_id, stats in self.instance_stats.items()
            }
            self.redis_client.set("services:stats", json.dumps(stats_data))

        except Exception as e:
            logger.error(f"同步到Redis失敗: {e}")

    async def load_from_redis(self):
        """從Redis加載數據"""
        if not self.redis_client:
            return

        try:
            # 加載服務配置
            services_data = self.redis_client.get("services:configs")
            if services_data:
                services_json = json.loads(services_data)
                for name, config_data in services_json.items():
                    config = ServiceConfig(**config_data)
                    self.register_service(config)

            # 加載實例信息
            instances_data = self.redis_client.get("services:instances")
            if instances_data:
                instances_json = json.loads(instances_data)
                for service_name, instances_list in instances_json.items():
                    for instance_data in instances_list:
                        instance = ServiceInstance(**instance_data)
                        self.register_instance(instance)

            # 加載統計信息
            stats_data = self.redis_client.get("services:stats")
            if stats_data:
                stats_json = json.loads(stats_data)
                for instance_id, stats_dict in stats_json.items():
                    # 轉換時間字符串
                    if stats_dict.get("last_request_time"):
                        stats_dict["last_request_time"] = datetime.fromisoformat(
                            stats_dict["last_request_time"]
                        )
                    if stats_dict.get("circuit_open_time"):
                        stats_dict["circuit_open_time"] = datetime.fromisoformat(
                            stats_dict["circuit_open_time"]
                        )

                    stats = ServiceStats(**stats_dict)
                    self.instance_stats[instance_id] = stats

            logger.info("從Redis加載服務數據完成")

        except Exception as e:
            logger.error(f"從Redis加載數據失敗: {e}")

    def get_service_status(self) -> Dict[str, Any]:
        """獲取所有服務狀態"""
        status = {
            "total_services": len(self.services),
            "total_instances": sum(
                len(instances) for instances in self.instances.values()
            ),
            "healthy_instances": 0,
            "unhealthy_instances": 0,
            "services": {},
        }

        for service_name, config in self.services.items():
            instances = self.get_service_instances(service_name)
            healthy_count = 0

            service_status = {
                "config": asdict(config),
                "instances": [],
                "stats": {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "avg_response_time": 0.0,
                    "success_rate": 0.0,
                },
            }

            total_requests = 0
            total_successful = 0
            total_response_time = 0.0

            for instance in instances:
                instance_stats = self.instance_stats.get(instance.id)
                instance_status = {
                    "instance": asdict(instance),
                    "status": self._get_instance_status(instance.id),
                    "stats": asdict(instance_stats) if instance_stats else None,
                }

                service_status["instances"].append(instance_status)

                if instance_stats:
                    total_requests += instance_stats.total_requests
                    total_successful += instance_stats.successful_requests
                    total_response_time += (
                        instance_stats.avg_response_time * instance_stats.total_requests
                    )

                    if self._get_instance_status(instance.id) == ServiceStatus.HEALTHY:
                        healthy_count += 1

            # 更新服務統計
            if total_requests > 0:
                service_status["stats"]["total_requests"] = total_requests
                service_status["stats"]["successful_requests"] = total_successful
                service_status["stats"]["failed_requests"] = (
                    total_requests - total_successful
                )
                service_status["stats"]["avg_response_time"] = (
                    total_response_time / total_requests
                )
                service_status["stats"]["success_rate"] = (
                    total_successful / total_requests
                )

            status["services"][service_name] = service_status
            status["healthy_instances"] += healthy_count

        status["unhealthy_instances"] = (
            status["total_instances"] - status["healthy_instances"]
        )

        return status

    async def close(self):
        """關閉服務註冊中心"""
        await self.stop_health_check()
        await self.http_client.aclose()
        logger.info("服務註冊中心已關閉")


# 便利函數
def create_service_registry(
    redis_client: Optional[redis.Redis] = None,
) -> ServiceRegistry:
    """創建服務註冊中心"""
    registry = ServiceRegistry(redis_client)

    # 註冊默認服務
    default_services = [
        ServiceConfig(
            name="dashboard",
            prefix="/api / v2",
            health_check_path="/health",
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN,
        ),
        ServiceConfig(
            name="analysis",
            prefix="/api / v1",
            health_check_path="/health",
            load_balancing=LoadBalancingStrategy.LEAST_CONNECTIONS,
        ),
        ServiceConfig(
            name="trading",
            prefix="/api / v1",
            health_check_path="/health",
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN,
        ),
        ServiceConfig(
            name="ml",
            prefix="/api / v1",
            health_check_path="/health",
            load_balancing=LoadBalancingStrategy.RANDOM,
        ),
        ServiceConfig(
            name="portfolio",
            prefix="/api / v1",
            health_check_path="/health",
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN,
        ),
        ServiceConfig(
            name="risk",
            prefix="/api / v1",
            health_check_path="/health",
            load_balancing=LoadBalancingStrategy.ROUND_ROBIN,
        ),
    ]

    for service_config in default_services:
        registry.register_service(service_config)

    return registry
