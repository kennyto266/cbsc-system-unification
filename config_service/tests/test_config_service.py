#!/usr/bin/env python3
"""
Configuration Service Tests
配置服務測試

DevOps Configuration Management Expert Implementation
"""

import os
import json
import pytest
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

import pytest_asyncio
from httpx import AsyncClient
from main import app, config_manager
from client import ConfigClient, ConfigClientError


class TestConfigurationService:
    """配置服務測試類"""

    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest_asyncio.fixture
    async def client(self):
        """測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest_asyncio.fixture
    async def config_client(self):
        """配置客戶端"""
        client = ConfigClient("http://test")
        await client.connect()
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """測試健康檢查"""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "redis" in data["services"]
        assert "database" in data["services"]

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """測試根端點"""
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "Configuration Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_set_and_get_config(self, config_client):
        """測試設置和獲取配置"""
        # 設置配置
        config_key = "test.database.url"
        config_value = "postgresql://localhost/test"

        result = await config_client.set_config(
            key=config_key,
            value=config_value,
            service="test_service",
            description="Test database URL"
        )

        assert result["message"] == "Configuration set successfully"
        assert result["config"]["key"] == config_key
        assert result["config"]["value"] == config_value

        # 獲取配置
        retrieved_value = await config_client.get_config(
            config_key,
            service="test_service"
        )

        assert retrieved_value == config_value

    @pytest.mark.asyncio
    async def test_update_config(self, config_client):
        """測試更新配置"""
        config_key = "test.update.value"
        initial_value = "initial_value"
        updated_value = "updated_value"

        # 設置初始配置
        await config_client.set_config(
            key=config_key,
            value=initial_value,
            service="test_service"
        )

        # 更新配置
        result = await config_client.update_config(
            key=config_key,
            value=updated_value,
            service="test_service",
            description="Updated configuration"
        )

        assert result["message"] == "Configuration updated successfully"
        assert result["config"]["value"] == updated_value
        assert result["config"]["version"] == 2  # Version should be incremented

        # 驗證更新
        retrieved_value = await config_client.get_config(
            config_key,
            service="test_service"
        )
        assert retrieved_value == updated_value

    @pytest.mark.asyncio
    async def test_delete_config(self, config_client):
        """測試刪除配置"""
        config_key = "test.delete.value"
        config_value = "to_be_deleted"

        # 設置配置
        await config_client.set_config(
            key=config_key,
            value=config_value,
            service="test_service"
        )

        # 刪除配置
        success = await config_client.delete_config(
            config_key,
            service="test_service"
        )
        assert success is True

        # 驗證已刪除
        with pytest.raises(ConfigClientError):
            await config_client.get_config(
                config_key,
                service="test_service"
            )

    @pytest.mark.asyncio
    async def test_list_configs(self, config_client):
        """測試列出配置"""
        service_name = "test_list_service"

        # 設置多個配置
        configs = {
            "test.list.config1": "value1",
            "test.list.config2": "value2",
            "test.list.config3": "value3"
        }

        for key, value in configs.items():
            await config_client.set_config(
                key=key,
                value=value,
                service=service_name
            )

        # 列出配置
        service_configs = await config_client.list_configs(service=service_name)

        assert len(service_configs) == 3

        # 驗證所有配置都在列表中
        returned_keys = {config["key"] for config in service_configs}
        expected_keys = set(configs.keys())
        assert returned_keys == expected_keys

    @pytest.mark.asyncio
    async def test_config_history(self, config_client):
        """測試配置歷史"""
        config_key = "test.history.value"
        service_name = "test_history_service"

        # 設置初始配置
        await config_client.set_config(
            key=config_key,
            value="initial",
            service=service_name
        )

        # 更新配置
        await config_client.update_config(
            key=config_key,
            value="updated",
            service=service_name
        )

        # 獲取歷史
        history = await config_client.get_config_history(
            config_key,
            service=service_name
        )

        assert len(history) >= 1

        # 檢查歷史記錄
        update_record = next(
            (h for h in history if h.new_value == "updated"),
            None
        )
        assert update_record is not None
        assert update_record.old_value == "initial"

    @pytest.mark.asyncio
    async def test_value_types(self, config_client):
        """測試不同值類型"""
        test_cases = [
            ("string_test", "test_string", "string"),
            ("int_test", 42, "int"),
            ("float_test", 3.14, "float"),
            ("bool_test", True, "bool"),
            ("json_test", {"key": "value"}, "json"),
        ]

        for key, value, expected_type in test_cases:
            # 設置配置
            await config_client.set_config(
                key=key,
                value=value,
                value_type=expected_type,
                service="type_test_service"
            )

            # 獲取並驗證
            retrieved_value = await config_client.get_config(
                key,
                service="type_test_service"
            )
            assert retrieved_value == value

    @pytest.mark.asyncio
    async def test_environment_isolation(self, config_client):
        """測試環境隔離"""
        config_key = "test.isolation.value"
        dev_value = "dev_value"
        prod_value = "prod_value"
        service_name = "isolation_test_service"

        # 在開發環境設置配置
        await config_client.set_config(
            key=config_key,
            value=dev_value,
            environment="development",
            service=service_name
        )

        # 在生產環境設置配置
        await config_client.set_config(
            key=config_key,
            value=prod_value,
            environment="production",
            service=service_name
        )

        # 驗證環境隔離
        dev_retrieved = await config_client.get_config(
            config_key,
            environment="development",
            service=service_name
        )
        assert dev_retrieved == dev_value

        prod_retrieved = await config_client.get_config(
            config_key,
            environment="production",
            service=service_name
        )
        assert prod_retrieved == prod_value

    @pytest.mark.asyncio
    async def test_encrypted_config(self, config_client):
        """測試加密配置"""
        config_key = "test.encrypted.value"
        sensitive_value = "sensitive_data"
        service_name = "encryption_test_service"

        # 設置加密配置
        await config_client.set_config(
            key=config_key,
            value=sensitive_value,
            service=service_name,
            encrypted=True,
            description="Sensitive configuration"
        )

        # 獲取配置
        retrieved_value = await config_client.get_config(
            config_key,
            service=service_name
        )
        assert retrieved_value == sensitive_value

    @pytest.mark.asyncio
    async def test_batch_operations(self, config_client):
        """測試批量操作"""
        service_name = "batch_test_service"

        # 批量設置配置
        configs_to_set = [
            {"key": "batch.config1", "value": "value1", "service": service_name},
            {"key": "batch.config2", "value": "value2", "service": service_name},
            {"key": "batch.config3", "value": "value3", "service": service_name},
        ]

        results = await config_client.batch_set_configs(configs_to_set)
        assert len(results) == 3
        assert all(result["success"] for result in results)

        # 批量獲取配置
        configs_to_get = [
            {"key": "batch.config1", "service": service_name},
            {"key": "batch.config2", "service": service_name},
            {"key": "batch.config3", "service": service_name},
        ]

        batch_results = await config_client.batch_get_configs(configs_to_get)
        assert len(batch_results) == 3
        assert all(result["error"] is None for result in batch_results.values())

    @pytest.mark.asyncio
    async def test_caching(self, config_client):
        """測試緩存功能"""
        config_key = "test.cache.value"
        config_value = "cached_value"
        service_name = "cache_test_service"

        # 設置配置
        await config_client.set_config(
            key=config_key,
            value=config_value,
            service=service_name
        )

        # 首次獲取（應該從數據庫）
        value1 = await config_client.get_config(
            config_key,
            service=service_name,
            use_cache=True
        )
        assert value1 == config_value

        # 第二次獲取（應該從緩存）
        value2 = await config_client.get_config(
            config_key,
            service=service_name,
            use_cache=True
        )
        assert value2 == config_value

        # 檢查緩存統計
        stats = config_client.get_cache_stats()
        assert stats["cache_size"] > 0

    @pytest.mark.asyncio
    async def test_metrics(self, client):
        """測試服務指標"""
        response = await client.get("/metrics")
        assert response.status_code == 200

        metrics = response.json()
        assert "total_configs" in metrics
        assert "configs_by_service" in metrics
        assert "configs_by_environment" in metrics
        assert "encrypted_configs" in metrics
        assert isinstance(metrics["total_configs"], int)

    @pytest.mark.asyncio
    async def test_error_handling(self, config_client):
        """測試錯誤處理"""
        # 嘗試獲取不存在的配置
        with pytest.raises(ConfigClientError):
            await config_client.get_config(
                "non.existent.config",
                service="non_existent_service"
            )

        # 嘗試刪除不存在的配置
        with pytest.raises(ConfigClientError):
            await config_client.delete_config(
                "non.existent.config",
                service="non_existent_service"
            )


class TestMigrationTools:
    """遷移工具測試"""

    @pytest.mark.asyncio
    async def test_json_migration(self, config_client, tmp_path):
        """測試JSON遷移"""
        from migration_tools import ConfigMigrator

        # 創建測試JSON文件
        test_config = {
            "database": {
                "url": "postgresql://localhost/test",
                "pool_size": 10
            },
            "cache": {
                "ttl": 300,
                "max_size": 1000
            }
        }

        json_file = tmp_path / "test_config.json"
        with open(json_file, 'w') as f:
            json.dump(test_config, f)

        # 執行遷移
        migrator = ConfigMigrator(config_client)
        result = await migrator.migrate_from_json_file(
            str(json_file),
            service="migration_test"
        )

        assert result.success
        assert result.migrated_configs == 4  # database.url, database.pool_size, cache.ttl, cache.max_size
        assert result.failed_configs == 0

        # 驗證遷移的配置
        db_url = await config_client.get_config(
            "database.url",
            service="migration_test"
        )
        assert db_url == "postgresql://localhost/test"

    @pytest.mark.asyncio
    async def test_yaml_migration(self, config_client, tmp_path):
        """測試YAML遷移"""
        from migration_tools import ConfigMigrator

        # 創建測試YAML文件
        test_config = """
api:
  timeout: 30
  retry_attempts: 3
security:
  jwt_secret: "secret_key"
  enabled: true
"""

        yaml_file = tmp_path / "test_config.yaml"
        with open(yaml_file, 'w') as f:
            f.write(test_config)

        # 執行遷移
        migrator = ConfigMigrator(config_client)
        result = await migrator.migrate_from_yaml_file(
            str(yaml_file),
            service="yaml_migration_test"
        )

        assert result.success
        assert result.migrated_configs == 4
        assert result.failed_configs == 0

        # 驗證遷移的配置
        api_timeout = await config_client.get_config(
            "api.timeout",
            service="yaml_migration_test"
        )
        assert api_timeout == 30


@pytest.mark.asyncio
async def test_service_lifecycle():
    """測試服務生命週期"""
    # 測試配置管理器初始化
    await config_manager.initialize()
    assert config_manager.redis_client is not None
    assert config_manager.db_pool is not None

    # 測試清理
    await config_manager.cleanup()
    assert config_manager.redis_client is None
    assert config_manager.db_pool is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])