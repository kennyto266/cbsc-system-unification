from functools import wraps
"""
连接池系统

提供完整的连接池管理：
- HTTP连接池
- 数据库连接池
- 连接复用
- 连接健康检查
- 自动重连
- 连接超时管理
- 负载均衡
"""

import asyncio

import aiohttp

try:
    import asyncpg
except ImportError:
    asyncpg = None
import json
import logging
import ssl
import threading
import time
import weakref
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """连接统计"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_used: float = field(default_factory=time.time)


@dataclass
class PoolConfig:
    """连接池配置"""

    min_size: int = 5
    max_size: int = 20
    max_idle_time: float = 300  # 秒
    connection_timeout: float = 10.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 60
    enable_health_check: bool = True
    ssl_verify: bool = True


class Connection:
    """
    连接基类
    """

    def __init__(self, pool_ref, config: PoolConfig):
        self.pool_ref = weakref.ref(pool_ref)
        self.config = config
        self.created_at = time.time()
        self.last_used = time.time()
        self.used_count = 0
        self.is_active = False
        self._lock = threading.RLock()

    def mark_used(self):
        """标记连接被使用"""
        with self._lock:
            self.last_used = time.time()
            self.used_count += 1
            self.is_active = True

    def mark_idle(self):
        """标记连接空闲"""
        with self._lock:
            self.is_active = False

    def is_stale(self) -> bool:
        """检查连接是否过期"""
        idle_time = time.time() - self.last_used
        return idle_time > self.config.max_idle_time

    def age(self) -> float:
        """获取连接年龄"""
        return time.time() - self.created_at

    def is_healthy(self) -> bool:
        """检查连接是否健康"""
        return not self.is_stale()

    async def health_check(self) -> bool:
        """健康检查（子类实现）"""
        raise NotImplementedError

    async def close(self):
        """关闭连接（子类实现）"""
        raise NotImplementedError


class HTTPConnection(Connection):
    """HTTP连接封装"""

    def __init__(self, pool_ref, config: PoolConfig, session: aiohttp.ClientSession):
        super().__init__(pool_ref, config)
        self.session = session
        self._response_times: deque = deque(maxlen=100)  # 保留最近100次响应时间

    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """发起HTTP请求"""
        self.mark_used()

        start_time = time.perf_counter()
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response_time = time.perf_counter() - start_time
                self._response_times.append(response_time)
                self.mark_idle()
                return response
        except Exception as e:
            self.mark_idle()
            raise

    async def health_check(self) -> bool:
        """HTTP连接健康检查"""
        try:
            # 简单健康检查：发起HEAD请求
            start_time = time.perf_counter()
            async with self.session.head("http://httpbin.org / status / 200") as response:
                response_time = time.perf_counter() - start_time
                self._response_times.append(response_time)
                return response.status == 200
        except Exception as e:
            logger.debug(f"HTTP健康检查失败: {e}")
            return False

    async def close(self):
        """关闭连接"""
        if not self.session.closed:
            await self.session.close()


class DatabaseConnection(Connection):
    """数据库连接封装"""

    def __init__(self, pool_ref, config: PoolConfig, conn: Any):
        super().__init__(pool_ref, config)
        self.conn = conn

    async def execute(self, query: str, *args) -> str:
        """执行SQL"""
        self.mark_used()
        result = await self.conn.execute(query, *args)
        self.mark_idle()
        return result

    async def fetch(self, query: str, *args) -> List[Any]:
        """查询数据"""
        self.mark_used()
        result = await self.conn.fetch(query, *args)
        self.mark_idle()
        return result

    async def fetchrow(self, query: str, *args) -> Optional[Any]:
        """查询单行"""
        self.mark_used()
        result = await self.conn.fetchrow(query, *args)
        self.mark_idle()
        return result

    async def fetchval(self, query: str, *args) -> Any:
        """查询单值"""
        self.mark_used()
        result = await self.conn.fetchval(query, *args)
        self.mark_idle()
        return result

    async def health_check(self) -> bool:
        """数据库连接健康检查"""
        try:
            start_time = time.perf_counter()
            result = await self.conn.fetchval("SELECT 1")
            response_time = time.perf_counter() - start_time
            # 记录响应时间（如果有地方记录的话）
            return result == 1
        except Exception as e:
            logger.debug(f"数据库健康检查失败: {e}")
            return False

    async def close(self):
        """关闭连接"""
        if not self.conn.is_closed():
            await self.conn.close()


class ConnectionPool:
    """
    连接池基类
    """

    def __init__(self, config: PoolConfig):
        self.config = config
        self._connections: List[Connection] = []
        self._idle_queue: deque = deque()
        self._active_connections: set = set()
        self._lock = threading.RLock()
        self._closed = False
        self._stats = ConnectionStats()
        self._health_check_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """初始化连接池"""
        if self._closed:
            raise ValueError("连接池已关闭")

        # 创建最小连接数
        for _ in range(self.config.min_size):
            conn = await self._create_connection()
            if conn:
                self._connections.append(conn)
                self._idle_queue.append(conn)

        logger.info(f"连接池初始化完成，最小连接数: {self.config.min_size}")

        # 启动健康检查
        if self.config.enable_health_check:
            asyncio.create_task(self._health_check_loop())

    async def _create_connection(self) -> Optional[Connection]:
        """创建连接（子类实现）"""
        raise NotImplementedError

    @asynccontextmanager
    async def acquire(self):
        """获取连接"""
        conn = await self.get_connection()
        try:
            yield conn
        finally:
            self.release_connection(conn)

    async def get_connection(self) -> Connection:
        """获取连接"""
        if self._closed:
            raise ValueError("连接池已关闭")

        with self._lock:
            # 尝试从空闲队列获取
            while self._idle_queue:
                conn = self._idle_queue.popleft()
                if conn.is_healthy():
                    self._active_connections.add(conn)
                    return conn
                else:
                    # 连接已过期，移除
                    await self._remove_connection(conn)

            # 如果未达到最大连接数，创建新连接
            if len(self._connections) < self.config.max_size:
                conn = await self._create_connection()
                if conn:
                    self._connections.append(conn)
                    self._active_connections.add(conn)
                    return conn

        # 等待空闲连接
        logger.warning("连接池已满，等待空闲连接")
        await asyncio.sleep(0.1)
        return await self.get_connection()

    def release_connection(self, conn: Connection):
        """释放连接"""
        with self._lock:
            if conn in self._active_connections:
                self._active_connections.remove(conn)
                conn.mark_idle()

                if conn.is_healthy() and not self._closed:
                    self._idle_queue.append(conn)
                else:
                    # 移除不健康的连接
                    asyncio.create_task(self._remove_connection(conn))

    async def _remove_connection(self, conn: Connection):
        """移除连接"""
        with self._lock:
            if conn in self._connections:
                self._connections.remove(conn)
            if conn in self._active_connections:
                self._active_connections.remove(conn)

        await conn.close()

    async def _health_check_loop(self):
        """健康检查循环"""
        while not self._closed:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
            except Exception as e:
                logger.error(f"健康检查错误: {e}")

    async def _perform_health_check(self):
        """执行健康检查"""
        with self._lock:
            connections_to_check = list(self._connections)

        for conn in connections_to_check:
            if not await conn.health_check():
                logger.warning("发现不健康的连接，移除")
                await self._remove_connection(conn)

                # 创建新连接
                new_conn = await self._create_connection()
                if new_conn:
                    with self._lock:
                        self._connections.append(new_conn)
                        self._idle_queue.append(new_conn)

    async def close(self):
        """关闭连接池"""
        if self._closed:
            return

        self._closed = True

        # 取消健康检查任务
        if self._health_check_task:
            self._health_check_task.cancel()

        # 关闭所有连接
        with self._lock:
            connections = self._connections.copy()

        for conn in connections:
            await self._remove_connection(conn)

        self._idle_queue.clear()
        self._active_connections.clear()

        logger.info("连接池已关闭")

    def get_stats(self) -> ConnectionStats:
        """获取连接池统计"""
        with self._lock:
            self._stats.total_connections = len(self._connections)
            self._stats.active_connections = len(self._active_connections)
            self._stats.idle_connections = len(self._idle_queue)
            return ConnectionStats(**self._stats.__dict__)


class HTTPConnectionPool(ConnectionPool):
    """
    HTTP连接池

    支持：
    - 连接复用
    - 连接池管理
    - 负载均衡
    - 健康检查
    """

    def __init__(
        self, base_url: str, config: Optional[PoolConfig] = None, **session_kwargs
    ):
        config = config or PoolConfig()
        super().__init__(config)
        self.base_url = base_url
        self.session_kwargs = session_kwargs
        self._sessions: List[aiohttp.ClientSession] = []

    async def _create_connection(self) -> Optional[HTTPConnection]:
        """创建HTTP连接"""
        # 创建session
        if not hasattr(self, "_session_counter"):
            self._session_counter = 0

        timeout = aiohttp.ClientTimeout(total=self.config.connection_timeout)
        session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(
                limit=self.config.max_size,
                limit_per_host=self.config.max_size // 2,
                ssl=ssl.create_default_context() if self.config.ssl_verify else False,
            ),
            **self.session_kwargs,
        )
        self._sessions.append(session)

        # 创建连接对象
        conn = HTTPConnection(
            pool_ref=weakref.ref(self), config=self.config, session=session
        )

        return conn

    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        发起HTTP请求

        Args:
            method: HTTP方法
            url: 相对或绝对URL
            **kwargs: 请求参数

        Returns:
            HTTP响应
        """
        # 补全URL
        if url.startswith("http"):
            full_url = url
        else:
            full_url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"

        async with self.acquire() as conn:
            return await conn.request(method, full_url, **kwargs)

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """GET请求"""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """POST请求"""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """PUT请求"""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """DELETE请求"""
        return await self.request("DELETE", url, **kwargs)

    async def close(self):
        """关闭连接池"""
        # 关闭所有session
        for session in self._sessions:
            if not session.closed:
                await session.close()

        await super().close()


class DatabaseConnectionPool(ConnectionPool):
    """
    数据库连接池

    支持：
    - PostgreSQL连接池
    - 连接复用
    - 事务管理
    """

    def __init__(self, dsn: str, config: Optional[PoolConfig] = None):
        config = config or PoolConfig()
        super().__init__(config)
        self.dsn = dsn
        self._connections: List[DatabaseConnection] = []

    async def _create_connection(self) -> Optional[DatabaseConnection]:
        """创建数据库连接"""
        try:
            conn = await asyncpg.connect(
                self.dsn, server_settings={"application_name": "hk_quant_system"}
            )

            # 设置连接参数
            await conn.execute(
                "SET statement_timeout = %s",
                f"{int(self.config.connection_timeout * 1000)}ms",
            )

            database_conn = DatabaseConnection(
                pool_ref=weakref.ref(self), config=self.config, conn=conn
            )

            return database_conn

        except Exception as e:
            logger.error(f"创建数据库连接失败: {e}")
            return None

    @asynccontextmanager
    async def transaction(self):
        """事务上下文管理器"""
        async with self.acquire() as conn:
            async with conn.conn.transaction():
                yield conn

    async def execute(self, query: str, *args) -> str:
        """执行SQL"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[Any]:
        """查询数据"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[Any]:
        """查询单行"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """查询单值"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def executemany(self, query: str, args_list: List[Tuple]) -> str:
        """批量执行"""
        async with self.acquire() as conn:
            return await conn.conn.executemany(query, args_list)


class ConnectionManager:
    """
    连接管理器

    统一管理多个连接池：
    - HTTP连接池
    - 数据库连接池
    - 自动负载均衡
    - 连接池监控
    """

    def __init__(self):
        self._pools: Dict[str, ConnectionPool] = {}
        self._lock = threading.RLock()
        self._stats_history: List[Dict[str, Any]] = []
        self._stats_lock = threading.RLock()

    def create_http_pool(
        self,
        name: str,
        base_url: str,
        config: Optional[PoolConfig] = None,
        **session_kwargs,
    ) -> HTTPConnectionPool:
        """
        创建HTTP连接池

        Args:
            name: 连接池名称
            base_url: 基础URL
            config: 连接池配置
            **session_kwargs: session参数

        Returns:
            HTTP连接池
        """
        with self._lock:
            if name in self._pools:
                logger.warning(f"连接池 {name} 已存在，将覆盖")

            pool = HTTPConnectionPool(base_url, config, **session_kwargs)
            self._pools[name] = pool
            logger.info(f"创建HTTP连接池: {name}, base_url: {base_url}")
            return pool

    def create_database_pool(
        self, name: str, dsn: str, config: Optional[PoolConfig] = None
    ) -> DatabaseConnectionPool:
        """
        创建数据库连接池

        Args:
            name: 连接池名称
            dsn: 数据库连接字符串
            config: 连接池配置

        Returns:
            数据库连接池
        """
        with self._lock:
            if name in self._pools:
                logger.warning(f"连接池 {name} 已存在，将覆盖")

            pool = DatabaseConnectionPool(dsn, config)
            self._pools[name] = pool
            logger.info(f"创建数据库连接池: {name}, dsn: {dsn}")
            return pool

    def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """获取连接池"""
        return self._pools.get(name)

    def get_all_pools(self) -> Dict[str, ConnectionPool]:
        """获取所有连接池"""
        with self._lock:
            return self._pools.copy()

    async def initialize_all(self):
        """初始化所有连接池"""
        tasks = []
        for name, pool in self._pools.items():
            tasks.append(self._initialize_pool(name, pool))

        await asyncio.gather(*tasks)

    async def _initialize_pool(self, name: str, pool: ConnectionPool):
        """初始化单个连接池"""
        try:
            await pool.initialize()
            logger.info(f"连接池 {name} 初始化完成")
        except Exception as e:
            logger.error(f"连接池 {name} 初始化失败: {e}")

    async def close_all(self):
        """关闭所有连接池"""
        tasks = []
        for name, pool in self._pools.items():
            tasks.append(pool.close())

        await asyncio.gather(*tasks)
        self._pools.clear()
        logger.info("所有连接池已关闭")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接池统计"""
        with self._lock:
            return {
                name: pool.get_stats().__dict__ for name, pool in self._pools.items()
            }

    def record_request(self, pool_name: str, success: bool, response_time: float):
        """记录请求统计"""
        with self._stats_lock:
            self._stats_history.append(
                {
                    "pool_name": pool_name,
                    "success": success,
                    "response_time": response_time,
                    "timestamp": time.time(),
                }
            )

            # 只保留最近10000条记录
            if len(self._stats_history) > 10000:
                self._stats_history = self._stats_history[-10000:]

    def get_performance_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        with self._stats_lock:
            if not self._stats_history:
                return {"message": "没有请求统计"}

            # 按连接池分组
            pools_stats = {}
            for record in self._stats_history:
                pool_name = record["pool_name"]
                if pool_name not in pools_stats:
                    pools_stats[pool_name] = {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "response_times": [],
                    }

                stats = pools_stats[pool_name]
                stats["total_requests"] += 1
                stats["response_times"].append(record["response_time"])

                if record["success"]:
                    stats["successful_requests"] += 1
                else:
                    stats["failed_requests"] += 1

            # 计算统计数据
            report = {}
            for pool_name, stats in pools_stats.items():
                response_times = stats["response_times"]
                if response_times:
                    stats["avg_response_time"] = sum(response_times) / len(
                        response_times
                    )
                    stats["min_response_time"] = min(response_times)
                    stats["max_response_time"] = max(response_times)
                    stats["median_response_time"] = sorted(response_times)[
                        len(response_times) // 2
                    ]
                    stats["success_rate"] = (
                        stats["successful_requests"] / stats["total_requests"]
                        if stats["total_requests"] > 0
                        else 0
                    )
                else:
                    stats["avg_response_time"] = 0
                    stats["min_response_time"] = 0
                    stats["max_response_time"] = 0
                    stats["median_response_time"] = 0
                    stats["success_rate"] = 0

                del stats["response_times"]  # 删除详细响应时间列表
                report[pool_name] = stats

            return report


# 全局连接管理器实例
_global_connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """获取全局连接管理器"""
    return _global_connection_manager


def create_http_pool(
    name: str, base_url: str, config: Optional[PoolConfig] = None, **session_kwargs
) -> HTTPConnectionPool:
    """创建HTTP连接池（便捷函数）"""
    return _global_connection_manager.create_http_pool(
        name, base_url, config, **session_kwargs
    )


def create_database_pool(
    name: str, dsn: str, config: Optional[PoolConfig] = None
) -> DatabaseConnectionPool:
    """创建数据库连接池（便捷函数）"""
    return _global_connection_manager.create_database_pool(name, dsn, config)


# 连接池装饰器
def with_connection(pool_name: str, pool_type: str = "auto"):
    """
    连接池装饰器

    Args:
        pool_name: 连接池名称
        pool_type: 连接池类型 ('http', 'database', 'auto')

    Usage:
        @with_connection('api_pool')
        async def fetch_data():
            async with connection_manager.get_pool('api_pool').acquire() as conn:
                return await conn.get('/api / data')
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            connection_manager = get_connection_manager()
            pool = connection_manager.get_pool(pool_name)

            if not pool:
                raise ValueError(f"连接池 {pool_name} 不存在")

            async with pool.acquire() as conn:
                # 将连接添加到函数参数
                kwargs["connection"] = conn
                return await func(*args, **kwargs)

        return wrapper

    return decorator
