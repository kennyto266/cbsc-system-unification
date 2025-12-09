"""
Redis連接管理器
港股量化交易系統 - Redis集成

提供Redis連接管理、連接池和Redis緩存集成。

主要功能:
- Redis連接管理
- 連接池配置
- Redis適配器
- 連接健康檢查
- 自動重連機制
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    """
    Redis連接管理器

    管理Redis連接、連接池和重連機制。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化Redis連接管理器

        Args:
            config: Redis配置
        """
        self.config = config
        self.client = None
        self.pool = None
        self.is_connected = False
        self.last_health_check = None
        self.connection_attempts = 0
        self.max_attempts = config.get("max_attempts", 3)

        # 連接配置
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 6379)
        self.password = config.get("password", None)
        self.db = config.get("db", 0)
        self.ssl = config.get("ssl", False)
        self.decode_responses = config.get("decode_responses", True)

        # 連接池配置
        self.max_connections = config.get("max_connections", 10)
        self.connection_timeout = config.get("connection_timeout", 5)
        self.socket_timeout = config.get("socket_timeout", 5)
        self.socket_connect_timeout = config.get("socket_connect_timeout", 5)
        self.socket_keepalive = config.get("socket_keepalive", True)
        self.socket_keepalive_options = config.get("socket_keepalive_options", {})

        # 重連配置
        self.retry_delay = config.get("retry_delay", 1)
        self.max_retry_delay = config.get("max_retry_delay", 60)

    async def connect(self) -> bool:
        """
        連接Redis

        Returns:
            連接是否成功
        """
        try:
            # 嘗試導入redis模塊
            try:
                import redis.asyncio as aioredis
            except ImportError:
                logger.error("Redis模塊未安裝，請運行: pip install redis")
                return False

            # 創建連接URL
            if self.password:
                url = f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
            else:
                url = f"redis://{self.host}:{self.port}/{self.db}"

            # 連接配置
            connection_kwargs = {
                "url": url,
                "ssl": self.ssl,
                "decode_responses": self.decode_responses,
                "socket_timeout": self.socket_timeout,
                "socket_connect_timeout": self.socket_connect_timeout,
                "socket_keepalive": self.socket_keepalive,
                "socket_keepalive_options": self.socket_keepalive_options,
                "retry_on_timeout": True,
                "health_check_interval": 30,
            }

            # 創建連接池
            self.pool = aioredis.ConnectionPool.from_url(
                url, max_connections=self.max_connections, **connection_kwargs
            )

            # 創建Redis客戶端
            self.client = aioredis.Redis(connection_pool=self.pool, **connection_kwargs)

            # 測試連接
            await self.client.ping()

            self.is_connected = True
            self.connection_attempts = 0
            logger.info(f"Redis連接成功: {self.host}:{self.port}")

            return True

        except Exception as e:
            logger.error(f"Redis連接失敗: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """斷開Redis連接"""
        try:
            if self.client:
                await self.client.close()
            if self.pool:
                await self.pool.disconnect()
            self.is_connected = False
            logger.info("Redis連接已斷開")
        except Exception as e:
            logger.error(f"Redis斷開連接失敗: {e}")

    async def reconnect(self) -> bool:
        """
        重新連接Redis

        Returns:
            連接是否成功
        """
        if self.connection_attempts >= self.max_attempts:
            logger.error(f"超過最大重連次數: {self.max_attempts}")
            return False

        self.connection_attempts += 1
        delay = min(
            self.retry_delay * (2 ** (self.connection_attempts - 1)),
            self.max_retry_delay,
        )

        logger.info(f"第 {self.connection_attempts} 次重連Redis，等待 {delay} 秒...")
        await asyncio.sleep(delay)

        # 斷開舊連接
        if self.is_connected:
            await self.disconnect()

        # 嘗試重新連接
        success = await self.connect()

        if not success and self.connection_attempts < self.max_attempts:
            return await self.reconnect()

        return success

    async def health_check(self) -> bool:
        """
        檢查Redis連接健康狀態

        Returns:
            連接是否健康
        """
        if not self.is_connected or not self.client:
            return False

        try:
            # 執行ping命令
            await self.client.ping()

            # 更新最後健康檢查時間
            self.last_health_check = datetime.now()

            return True

        except Exception as e:
            logger.warning(f"Redis健康檢查失敗: {e}")
            self.is_connected = False

            # 嘗試自動重連
            logger.info("嘗試自動重連...")
            return await self.reconnect()

    def get_client(self):
        """
        獲取Redis客戶端

        Returns:
            Redis客戶端實例
        """
        if not self.is_connected:
            logger.warning("Redis未連接，返回None")
            return None

        return self.client

    async def execute_command(self, command: str, *args, **kwargs):
        """
        執行Redis命令

        Args:
            command: Redis命令
            *args: 命令參數
            **kwargs: 命令選項

        Returns:
            命令執行結果
        """
        if not self.is_connected:
            raise RuntimeError("Redis未連接")

        try:
            # 獲取命令方法
            method = getattr(self.client, command.lower(), None)
            if not method or not callable(method):
                raise ValueError(f"不支持的Redis命令: {command}")

            # 執行命令
            result = await method(*args, **kwargs)
            return result

        except Exception as e:
            logger.error(f"執行Redis命令失敗: {e}")
            raise

    def is_healthy(self) -> bool:
        """
        檢查連接是否健康

        Returns:
            連接是否健康
        """
        if not self.is_connected:
            return False

        # 檢查最後健康檢查時間
        if self.last_health_check:
            time_diff = datetime.now() - self.last_health_check
            if time_diff > timedelta(minutes=5):
                logger.info("健康檢查超時，執行檢查...")
                return False  # 會在下一次健康檢查時重新檢查

        return True

    def get_info(self) -> Dict[str, Any]:
        """
        獲取連接信息

        Returns:
            連接信息字典
        """
        return {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "is_connected": self.is_connected,
            "is_healthy": self.is_healthy(),
            "connection_attempts": self.connection_attempts,
            "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
            "max_connections": self.max_connections,
            "ssl": self.ssl,
        }


class RedisAdapter:
    """
    Redis適配器

    將Redis操作封裝為簡單易用的接口。
    """

    def __init__(self, connection_manager: RedisConnectionManager):
        """
        初始化Redis適配器

        Args:
            connection_manager: Redis連接管理器
        """
        self.cm = connection_manager

    async def get(self, key: str) -> Optional[Any]:
        """
        獲取值

        Args:
            key: 緩存鍵

        Returns:
            緩存值
        """
        try:
            client = self.cm.get_client()
            if not client:
                return None

            value = await client.get(key)
            if value is None:
                return None

            # 嘗試解析JSON
            try:
                import json

                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        設置值

        Args:
            key: 緩存鍵
            value: 緩存值
            ttl: 生存時間（秒）

        Returns:
            設置是否成功
        """
        try:
            client = self.cm.get_client()
            if not client:
                return False

            # 序列化为JSON
            try:
                import json

                serialized_value = json.dumps(value)
            except (TypeError, ValueError):
                # 如果序列化失败，尝试使用字符串
                serialized_value = str(value)

            if ttl:
                await client.setex(key, ttl, serialized_value)
            else:
                await client.set(key, serialized_value)

            return True

        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        刪除值

        Args:
            key: 緩存鍵

        Returns:
            刪除是否成功
        """
        try:
            client = self.cm.get_client()
            if not client:
                return False

            result = await client.delete(key)
            return result > 0

        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        檢查鍵是否存在

        Args:
            key: 緩存鍵

        Returns:
            鍵是否存在
        """
        try:
            client = self.cm.get_client()
            if not client:
                return False

            result = await client.exists(key)
            return result > 0

        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def clear(self, pattern: str = "*") -> int:
        """
        清空緩存

        Args:
            pattern: 鍵匹配模式，默認清空所有

        Returns:
            刪除的鍵數量
        """
        try:
            client = self.cm.get_client()
            if not client:
                return 0

            # 查找匹配的鍵
            keys = await client.keys(pattern)

            if not keys:
                return 0

            # 刪除鍵
            result = await client.delete(*keys)
            return result

        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        設置過期時間

        Args:
            key: 緩存鍵
            ttl: 生存時間（秒）

        Returns:
            設置是否成功
        """
        try:
            client = self.cm.get_client()
            if not client:
                return False

            result = await client.expire(key, ttl)
            return result

        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        獲取剩餘生存時間

        Args:
            key: 緩存鍵

        Returns:
            剩餘生存時間（秒），-1表示無過期時間，-2表示鍵不存在
        """
        try:
            client = self.cm.get_client()
            if not client:
                return -2

            result = await client.ttl(key)
            return result

        except Exception as e:
            logger.error(f"Redis ttl error: {e}")
            return -2


# 便利函數
async def create_redis_connection(
    host: str = "localhost",
    port: int = 6379,
    password: Optional[str] = None,
    db: int = 0,
    max_connections: int = 10,
    **kwargs,
) -> RedisAdapter:
    """
    創建Redis連接的便利函數

    Args:
        host: Redis主機
        port: Redis端口
        password: 密碼
        db: 數據庫編號
        max_connections: 最大連接數
        **kwargs: 其他配置參數

    Returns:
        RedisAdapter實例
    """
    config = {
        "host": host,
        "port": port,
        "password": password,
        "db": db,
        "max_connections": max_connections,
        **kwargs,
    }

    # 創建連接管理器
    cm = RedisConnectionManager(config)

    # 連接Redis
    success = await cm.connect()
    if not success:
        raise RuntimeError("Redis連接失敗")

    # 創建適配器
    adapter = RedisAdapter(cm)

    logger.info(f"Redis連接創建成功: {host}:{port}")
    return adapter


if __name__ == "__main__":
    # 測試示例
    async def test_redis():
        try:
            # 創建Redis連接
            adapter = await create_redis_connection(host="localhost", port=6379, db=0)

            # 測試設置和獲取
            await adapter.set("test_key", {"name": "test", "value": 123}, ttl=60)
            result = await adapter.get("test_key")
            print(f"Redis測試結果: {result}")

            # 測試是否存在
            exists = await adapter.exists("test_key")
            print(f"鍵是否存在: {exists}")

            # 測試TTL
            ttl = await adapter.ttl("test_key")
            print(f"剩餘生存時間: {ttl}秒")

            # 獲取連接信息
            info = adapter.cm.get_info()
            print(f"連接信息: {info}")

            # 清理
            await adapter.delete("test_key")
            print("測試完成")

        except Exception as e:
            print(f"Redis測試失敗: {e}")

    # 運行測試
    asyncio.run(test_redis())
