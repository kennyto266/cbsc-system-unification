#!/usr/bin/env python3
"""
Configuration Service Client SDK
配置服務客戶端SDK

DevOps Configuration Management Expert Implementation
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import aiohttp
import websockets
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConfigClientError(Exception):
    """配置客戶端錯誤"""
    pass


class ConfigSubscription:
    """配置訂閱類"""
    def __init__(self, key: str, environment: str, service: str, callback):
        self.key = key
        self.environment = environment
        self.service = service
        self.callback = callback
        self.active = True


class ConfigClient:
    """配置服務客戶端"""

    def __init__(self, base_url: str = "http://localhost:8005",
                 auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.subscriptions: Dict[str, ConfigSubscription] = {}
        self._local_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5分鐘

    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close()

    async def connect(self):
        """連接到配置服務"""
        if not self.session:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            self.session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )

        logger.info(f"Connected to Configuration Service at {self.base_url}")

    async def close(self):
        """關閉連接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

        if self.session:
            await self.session.close()
            self.session = None

        logger.info("Disconnected from Configuration Service")

    def _get_cache_key(self, key: str, environment: str, service: str) -> str:
        """獲取緩存鍵"""
        return f"{service}:{environment}:{key}"

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """檢查緩存是否有效"""
        if not cached_data:
            return False

        cached_time = datetime.fromisoformat(cached_data.get("cached_at", ""))
        current_time = datetime.now(timezone.utc)
        return (current_time - cached_time).total_seconds() < self._cache_ttl

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """發送HTTP請求"""
        if not self.session:
            await self.connect()

        try:
            url = f"{self.base_url}{endpoint}"
            async with self.session.request(method, url, **kwargs) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise ConfigClientError(f"Request failed: {response.status} - {error_text}")

                return await response.json()

        except aiohttp.ClientError as e:
            raise ConfigClientError(f"Connection error: {e}")

    async def get_config(self, key: str, environment: str = "development",
                        service: str = "global", use_cache: bool = True) -> Any:
        """獲取配置值"""
        cache_key = self._get_cache_key(key, environment, service)

        # 檢查本地緩存
        if use_cache and cache_key in self._local_cache:
            cached_data = self._local_cache[cache_key]
            if self._is_cache_valid(cached_data):
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data["value"]

        try:
            response = await self._make_request(
                "GET",
                f"/config/{key}",
                params={"environment": environment, "service": service}
            )

            value = self._convert_value(response["value"], response["value_type"])

            # 更新本地緩存
            if use_cache:
                self._local_cache[cache_key] = {
                    "value": value,
                    "cached_at": datetime.now(timezone.utc).isoformat()
                }

            return value

        except Exception as e:
            # 如果有緩存的舊值，返回緩存值
            if cache_key in self._local_cache:
                logger.warning(f"Using cached value for {cache_key} due to error: {e}")
                return self._local_cache[cache_key]["value"]
            raise

    async def set_config(self, key: str, value: Any, environment: str = "development",
                        service: str = "global", value_type: str = "auto",
                        encrypted: bool = False, description: str = None,
                        tags: List[str] = None) -> Dict[str, Any]:
        """設置配置值"""
        if value_type == "auto":
            value_type = self._detect_value_type(value)

        config_data = {
            "key": key,
            "value": value,
            "value_type": value_type,
            "environment": environment,
            "service": service,
            "encrypted": encrypted,
            "description": description,
            "tags": tags or []
        }

        response = await self._make_request("POST", "/config", json=config_data)

        # 清除本地緩存
        cache_key = self._get_cache_key(key, environment, service)
        if cache_key in self._local_cache:
            del self._local_cache[cache_key]

        return response

    async def update_config(self, key: str, value: Any, environment: str = "development",
                           service: str = "global", description: str = None) -> Dict[str, Any]:
        """更新配置值"""
        update_data = {
            "value": value,
            "description": description,
            "updated_by": "config_client"
        }

        response = await self._make_request(
            "PUT",
            f"/config/{key}",
            params={"environment": environment, "service": service},
            json=update_data
        )

        # 清除本地緩存
        cache_key = self._get_cache_key(key, environment, service)
        if cache_key in self._local_cache:
            del self._local_cache[cache_key]

        return response

    async def delete_config(self, key: str, environment: str = "development",
                           service: str = "global") -> bool:
        """刪除配置"""
        await self._make_request(
            "DELETE",
            f"/config/{key}",
            params={"environment": environment, "service": service}
        )

        # 清除本地緩存
        cache_key = self._get_cache_key(key, environment, service)
        if cache_key in self._local_cache:
            del self._local_cache[cache_key]

        return True

    async def list_configs(self, environment: str = None, service: str = None,
                          tags: List[str] = None) -> List[Dict[str, Any]]:
        """列出配置"""
        params = {}
        if environment:
            params["environment"] = environment
        if service:
            params["service"] = service
        if tags:
            params["tags"] = ",".join(tags)

        response = await self._make_request("GET", "/configs", params=params)
        return response["configs"]

    async def get_config_history(self, key: str, environment: str = "development",
                               service: str = "global", limit: int = 50) -> List[Dict[str, Any]]:
        """獲取配置歷史"""
        response = await self._make_request(
            "GET",
            f"/config/{key}/history",
            params={"environment": environment, "service": service, "limit": limit}
        )
        return response["history"]

    async def get_service_health(self) -> Dict[str, Any]:
        """獲取配置服務健康狀態"""
        return await self._make_request("GET", "/health")

    async def get_metrics(self) -> Dict[str, Any]:
        """獲取服務指標"""
        return await self._make_request("GET", "/metrics")

    async def subscribe_to_changes(self, callback):
        """訂閱配置變更通知"""
        try:
            ws_url = f"{self.base_url.replace('http', 'ws')}/ws"
            self.websocket = await websockets.connect(ws_url)

            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "config_change":
                        await callback(data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error processing change notification: {e}")

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise

    async def subscribe_to_config(self, key: str, environment: str, service: str, callback):
        """訂閱特定配置的變更"""
        subscription_key = self._get_cache_key(key, environment, service)

        # 創建訂閱
        subscription = ConfigSubscription(key, environment, service, callback)
        self.subscriptions[subscription_key] = subscription

        # 如果WebSocket未連接，則連接
        if not self.websocket:
            await self.subscribe_to_changes(self._handle_config_change)

    async def unsubscribe_from_config(self, key: str, environment: str, service: str):
        """取消訂閱配置變更"""
        subscription_key = self._get_cache_key(key, environment, service)
        if subscription_key in self.subscriptions:
            del self.subscriptions[subscription_key]

    async def _handle_config_change(self, change_data: Dict[str, Any]):
        """處理配置變更通知"""
        key = change_data.get("key")
        environment = change_data.get("environment")
        service = change_data.get("service")
        action = change_data.get("action")

        subscription_key = self._get_cache_key(key, environment, service)
        if subscription_key in self.subscriptions:
            subscription = self.subscriptions[subscription_key]
            if subscription.active:
                await subscription.callback(change_data)

        # 清除相關緩存
        cache_key = self._get_cache_key(key, environment, service)
        if cache_key in self._local_cache:
            del self._local_cache[cache_key]

    def _detect_value_type(self, value: Any) -> str:
        """自動檢測值類型"""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, dict) or isinstance(value, list):
            return "json"
        elif isinstance(value, str):
            # 檢查是否為JSON或YAML
            try:
                json.loads(value)
                return "json"
            except:
                try:
                    yaml.safe_load(value)
                    return "yaml"
                except:
                    pass
        return "string"

    def _convert_value(self, value: Any, value_type: str) -> Any:
        """轉換配置值到正確類型"""
        if value_type == "string":
            return str(value)
        elif value_type == "int":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "bool":
            return bool(value)
        elif value_type == "json":
            if isinstance(value, str):
                return json.loads(value)
            return value
        elif value_type == "yaml":
            import yaml
            if isinstance(value, str):
                return yaml.safe_load(value)
            return value
        else:
            return value

    async def batch_get_configs(self, configs: List[Dict[str, str]]) -> Dict[str, Any]:
        """批量獲取配置"""
        results = {}
        tasks = []

        for config in configs:
            key = config["key"]
            environment = config.get("environment", "development")
            service = config.get("service", "global")

            task = self.get_config(key, environment, service)
            tasks.append((f"{service}:{environment}:{key}", task))

        # 並行執行所有請求
        for cache_key, task in tasks:
            try:
                value = await task
                results[cache_key] = {"value": value, "error": None}
            except Exception as e:
                results[cache_key] = {"value": None, "error": str(e)}

        return results

    async def batch_set_configs(self, configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量設置配置"""
        results = []
        tasks = []

        for config in configs:
            task = self.set_config(
                key=config["key"],
                value=config["value"],
                environment=config.get("environment", "development"),
                service=config.get("service", "global"),
                value_type=config.get("value_type", "auto"),
                encrypted=config.get("encrypted", False),
                description=config.get("description"),
                tags=config.get("tags", [])
            )
            tasks.append(task)

        # 並行執行所有設置操作
        for task in tasks:
            try:
                result = await task
                results.append({"success": True, "result": result, "error": None})
            except Exception as e:
                results.append({"success": False, "result": None, "error": str(e)})

        return results

    def clear_cache(self):
        """清除本地緩存"""
        self._local_cache.clear()
        logger.info("Local cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        return {
            "cache_size": len(self._local_cache),
            "subscriptions": len(self.subscriptions),
            "cache_ttl": self._cache_ttl
        }


class ServiceConfigMixin:
    """服務配置混入類"""

    def __init__(self, service_name: str, config_client: ConfigClient):
        self.service_name = service_name
        self.config_client = config_client
        self._config_cache: Dict[str, Any] = {}

    async def load_service_config(self, environment: str = "development") -> Dict[str, Any]:
        """加載服務配置"""
        try:
            configs = await self.config_client.list_configs(
                environment=environment,
                service=self.service_name
            )

            service_config = {}
            for config in configs:
                key = config["key"]
                value = config["value"]
                service_config[key] = value

            self._config_cache = service_config
            return service_config

        except Exception as e:
            logger.error(f"Failed to load service config: {e}")
            return {}

    async def get_service_config(self, key: str, default: Any = None,
                               environment: str = "development") -> Any:
        """獲取服務配置值"""
        try:
            # 先從緩存獲取
            if key in self._config_cache:
                return self._config_cache[key]

            # 從配置服務獲取
            value = await self.config_client.get_config(
                key, environment, self.service_name
            )

            # 更新緩存
            self._config_cache[key] = value
            return value

        except Exception as e:
            logger.error(f"Failed to get service config {key}: {e}")
            return default

    async def set_service_config(self, key: str, value: Any,
                               environment: str = "development",
                               description: str = None) -> Dict[str, Any]:
        """設置服務配置值"""
        try:
            result = await self.config_client.set_config(
                key=key,
                value=value,
                environment=environment,
                service=self.service_name,
                description=description
            )

            # 更新緩存
            self._config_cache[key] = value
            return result

        except Exception as e:
            logger.error(f"Failed to set service config {key}: {e}")
            raise

    async def subscribe_to_service_changes(self, callback):
        """訂閱服務配置變更"""
        await self.config_client.subscribe_to_changes(
            lambda data: self._filter_service_changes(data, callback)
        )

    async def _filter_service_changes(self, change_data: Dict[str, Any], callback):
        """過濾服務相關的配置變更"""
        if change_data.get("service") == self.service_name:
            await callback(change_data)


# 便捷函數
async def create_config_client(base_url: str = "http://localhost:8005",
                             auth_token: Optional[str] = None) -> ConfigClient:
    """創建配置客戶端"""
    client = ConfigClient(base_url, auth_token)
    await client.connect()
    return client


# 使用示例
async def example_usage():
    """使用示例"""

    # 創建配置客戶端
    async with create_config_client() as client:

        # 設置配置
        await client.set_config(
            key="database.url",
            value="postgresql://localhost/mydb",
            service="analytics",
            description="Analytics database connection"
        )

        # 獲取配置
        db_url = await client.get_config(
            "database.url",
            service="analytics"
        )
        print(f"Database URL: {db_url}")

        # 列出配置
        configs = await client.list_configs(service="analytics")
        print(f"Analytics configs: {len(configs)}")

        # 訂閱配置變更
        async def on_config_change(change_data):
            print(f"Config changed: {change_data}")

        await client.subscribe_to_config(
            "database.url",
            "development",
            "analytics",
            on_config_change
        )


if __name__ == "__main__":
    asyncio.run(example_usage())