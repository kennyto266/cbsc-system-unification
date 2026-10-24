#!/usr/bin/env python3
"""
Quantitative Trading Microservices - Configuration Service
量化交易微服務系統 - 配置服務

DevOps Configuration Management Expert Implementation
DevOps配置管理專家實現

Port: 8005
"""

import os
import json
import yaml
import asyncio
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import redis
import asyncpg
import aioredis
from cryptography.fernet import Fernet

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局變量
redis_client: Optional[aioredis.Redis] = None
db_pool: Optional[asyncpg.Pool] = None
encryption_key: Optional[bytes] = None
config_service_state: Dict[str, Any] = {}


class ConfigValue(BaseModel):
    """配置值模型"""
    key: str = Field(..., description="配置鍵名")
    value: Any = Field(..., description="配置值")
    value_type: str = Field(default="string", description="值類型: string, int, float, bool, json, yaml")
    environment: str = Field(default="development", description="環境: development, staging, production")
    service: str = Field(..., description="服務名稱: data, analytics, backtest, notification, config")
    version: int = Field(default=1, description="配置版本")
    encrypted: bool = Field(default=False, description="是否加密")
    description: Optional[str] = Field(None, description="配置描述")
    tags: List[str] = Field(default_factory=list, description="標籤")
    created_by: str = Field(default="system", description="創建者")
    updated_by: str = Field(default="system", description="更新者")

    @validator('value_type')
    def validate_value_type(cls, v):
        allowed_types = ['string', 'int', 'float', 'bool', 'json', 'yaml']
        if v not in allowed_types:
            raise ValueError(f'Value type must be one of: {allowed_types}')
        return v

    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of: {allowed_envs}')
        return v

    @validator('service')
    def validate_service(cls, v):
        allowed_services = ['data', 'analytics', 'backtest', 'notification', 'config', 'global']
        if v not in allowed_services:
            raise ValueError(f'Service must be one of: {allowed_services}')
        return v


class ConfigUpdate(BaseModel):
    """配置更新模型"""
    value: Any = Field(..., description="新配置值")
    description: Optional[str] = Field(None, description="更新描述")
    updated_by: str = Field(default="system", description="更新者")


class ConfigTemplate(BaseModel):
    """配置模板模型"""
    name: str = Field(..., description="模板名稱")
    service: str = Field(..., description="適用服務")
    environment: str = Field(..., description="適用環境")
    config_schema: Dict[str, Any] = Field(..., description="配置架構")
    default_values: Dict[str, Any] = Field(..., description="默認值")
    description: Optional[str] = Field(None, description="模板描述")
    version: str = Field(default="1.0.0", description="模板版本")


class ConfigHistory(BaseModel):
    """配置歷史記錄"""
    id: int
    config_key: str
    old_value: Any
    new_value: Any
    changed_by: str
    change_time: datetime
    change_reason: Optional[str]


class ConfigServiceMetrics(BaseModel):
    """配置服務指標"""
    total_configs: int
    configs_by_service: Dict[str, int]
    configs_by_environment: Dict[str, int]
    encrypted_configs: int
    last_update: Optional[datetime]
    cache_hits: int
    cache_misses: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時初始化
    await initialize_services()
    logger.info("Configuration Service started successfully")

    yield

    # 關閉時清理
    await cleanup_services()
    logger.info("Configuration Service shutdown completed")


# 創建FastAPI應用
app = FastAPI(
    title="Configuration Service",
    description="集中化配置管理服務 - Quantitative Trading Microservices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 中間件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全認證
security = HTTPBearer(auto_error=False)


class ConfigurationManager:
    """配置管理器核心類"""

    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.cipher_suite = None
        self.websocket_connections = set()
        self.metrics = {
            "total_configs": 0,
            "configs_by_service": {},
            "configs_by_environment": {},
            "encrypted_configs": 0,
            "last_update": None,
            "cache_hits": 0,
            "cache_misses": 0
        }

    async def initialize(self):
        """初始化配置管理器"""
        try:
            # 初始化Redis連接
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis_client = await aioredis.from_url(redis_url, decode_responses=True)
            logger.info("Redis connected successfully")

            # 初始化PostgreSQL連接
            db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/config_service")
            self.db_pool = await asyncpg.create_pool(
                db_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("PostgreSQL connected successfully")

            # 初始化加密
            encryption_key_env = os.getenv("CONFIG_ENCRYPTION_KEY")
            if encryption_key_env:
                self.cipher_suite = Fernet(encryption_key_env.encode())
                logger.info("Encryption initialized")
            else:
                logger.warning("No encryption key provided, sensitive configs will not be encrypted")

            # 初始化數據庫表
            await self.init_database_tables()

            # 加載指標
            await self.load_metrics()

            logger.info("Configuration Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Configuration Manager: {e}")
            raise

    async def init_database_tables(self):
        """初始化數據庫表"""
        async with self.db_pool.acquire() as conn:
            # 配置表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS configs (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(255) NOT NULL,
                    value JSONB NOT NULL,
                    value_type VARCHAR(20) NOT NULL DEFAULT 'string',
                    environment VARCHAR(20) NOT NULL DEFAULT 'development',
                    service VARCHAR(50) NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    encrypted BOOLEAN NOT NULL DEFAULT FALSE,
                    description TEXT,
                    tags TEXT[],
                    created_by VARCHAR(100) DEFAULT 'system',
                    updated_by VARCHAR(100) DEFAULT 'system',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(key, environment, service)
                )
            """)

            # 配置歷史表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config_history (
                    id SERIAL PRIMARY KEY,
                    config_key VARCHAR(255) NOT NULL,
                    environment VARCHAR(20) NOT NULL,
                    service VARCHAR(50) NOT NULL,
                    old_value JSONB,
                    new_value JSONB,
                    changed_by VARCHAR(100) DEFAULT 'system',
                    change_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    change_reason TEXT
                )
            """)

            # 配置模板表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS config_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    service VARCHAR(50) NOT NULL,
                    environment VARCHAR(20) NOT NULL,
                    config_schema JSONB NOT NULL,
                    default_values JSONB NOT NULL,
                    description TEXT,
                    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # 創建索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_configs_key_env_service
                ON configs(key, environment, service)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_configs_service
                ON configs(service)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_configs_environment
                ON configs(environment)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_config_history_config_key
                ON config_history(config_key)
            """)

            logger.info("Database tables initialized successfully")

    async def get_config(self, key: str, environment: str = "development",
                        service: str = "global") -> Optional[Dict[str, Any]]:
        """獲取配置值"""
        cache_key = f"config:{service}:{environment}:{key}"

        try:
            # 先從緩存獲取
            cached_value = await self.redis_client.get(cache_key)
            if cached_value:
                self.metrics["cache_hits"] += 1
                return json.loads(cached_value)

            # 從數據庫獲取
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM configs
                    WHERE key = $1 AND environment = $2 AND service = $3
                    """,
                    key, environment, service
                )

            if row:
                config_data = {
                    "key": row["key"],
                    "value": row["value"],
                    "value_type": row["value_type"],
                    "environment": row["environment"],
                    "service": row["service"],
                    "version": row["version"],
                    "encrypted": row["encrypted"],
                    "description": row["description"],
                    "tags": row["tags"] or [],
                    "created_by": row["created_by"],
                    "updated_by": row["updated_by"]
                }

                # 解密配置值
                if row["encrypted"] and self.cipher_suite:
                    config_data["value"] = await self.decrypt_value(config_data["value"])

                # 緩存配置
                await self.redis_client.setex(
                    cache_key,
                    300,  # 5分鐘TTL
                    json.dumps(config_data, default=str)
                )

                self.metrics["cache_misses"] += 1
                return config_data

            return None

        except Exception as e:
            logger.error(f"Error getting config {key}: {e}")
            raise

    async def set_config(self, config: ConfigValue) -> Dict[str, Any]:
        """設置配置值"""
        try:
            # 加密敏感配置
            final_value = config.value
            if config.encrypted and self.cipher_suite:
                final_value = await self.encrypt_value(config.value)

            async with self.db_pool.acquire() as conn:
                # 檢查配置是否已存在
                existing = await conn.fetchrow(
                    """
                    SELECT * FROM configs
                    WHERE key = $1 AND environment = $2 AND service = $3
                    """,
                    config.key, config.environment, config.service
                )

                if existing:
                    # 更新現有配置
                    old_value = existing["value"] if not existing["encrypted"] else await self.decrypt_value(existing["value"])

                    await conn.execute(
                        """
                        UPDATE configs
                        SET value = $1, value_type = $2, version = version + 1,
                            encrypted = $3, description = $4, tags = $5,
                            updated_by = $6, updated_at = NOW()
                        WHERE key = $7 AND environment = $8 AND service = $9
                        """,
                        final_value, config.value_type, config.encrypted,
                        config.description, config.tags, config.updated_by,
                        config.key, config.environment, config.service
                    )

                    # 記錄歷史
                    await conn.execute(
                        """
                        INSERT INTO config_history
                        (config_key, environment, service, old_value, new_value, changed_by, change_reason)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        config.key, config.environment, config.service,
                        old_value, config.value, config.updated_by, "Configuration update"
                    )

                else:
                    # 創建新配置
                    await conn.execute(
                        """
                        INSERT INTO configs
                        (key, value, value_type, environment, service, encrypted,
                         description, tags, created_by, updated_by)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """,
                        config.key, final_value, config.value_type, config.environment,
                        config.service, config.encrypted, config.description,
                        config.tags, config.created_by, config.updated_by
                    )

            # 清除緩存
            cache_key = f"config:{config.service}:{config.environment}:{config.key}"
            await self.redis_client.delete(cache_key)

            # 更新指標
            await self.update_metrics()

            # 通知WebSocket客戶端
            await self.notify_config_change(config.key, config.environment, config.service, "update")

            logger.info(f"Configuration {config.key} set successfully for {config.service}/{config.environment}")

            return await self.get_config(config.key, config.environment, config.service)

        except Exception as e:
            logger.error(f"Error setting config {config.key}: {e}")
            raise

    async def delete_config(self, key: str, environment: str = "development",
                          service: str = "global") -> bool:
        """刪除配置"""
        try:
            async with self.db_pool.acquire() as conn:
                # 獲取配置信息記錄歷史
                existing = await conn.fetchrow(
                    """
                    SELECT * FROM configs
                    WHERE key = $1 AND environment = $2 AND service = $3
                    """,
                    key, environment, service
                )

                if existing:
                    # 記錄刪除歷史
                    await conn.execute(
                        """
                        INSERT INTO config_history
                        (config_key, environment, service, old_value, new_value, changed_by, change_reason)
                        VALUES ($1, $2, $3, $4, NULL, $5, $6)
                        """,
                        key, environment, service, existing["value"], "system", "Configuration deleted"
                    )

                    # 刪除配置
                    await conn.execute(
                        """
                        DELETE FROM configs
                        WHERE key = $1 AND environment = $2 AND service = $3
                        """,
                        key, environment, service
                    )

                    # 清除緩存
                    cache_key = f"config:{service}:{environment}:{key}"
                    await self.redis_client.delete(cache_key)

                    # 更新指標
                    await self.update_metrics()

                    # 通知WebSocket客戶端
                    await self.notify_config_change(key, environment, service, "delete")

                    logger.info(f"Configuration {key} deleted successfully for {service}/{environment}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Error deleting config {key}: {e}")
            raise

    async def list_configs(self, environment: str = None, service: str = None,
                          tags: List[str] = None) -> List[Dict[str, Any]]:
        """列出配置"""
        try:
            async with self.db_pool.acquire() as conn:
                query = "SELECT * FROM configs WHERE 1=1"
                params = []

                if environment:
                    query += " AND environment = $1"
                    params.append(environment)

                if service:
                    query += f" AND service = ${len(params) + 1}"
                    params.append(service)

                if tags:
                    # 標籤搜索
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append(f"${len(params) + 1} = ANY(tags)")
                        params.append(tag)
                    if tag_conditions:
                        query += f" AND ({' OR '.join(tag_conditions)})"

                query += " ORDER BY service, environment, key"

                rows = await conn.fetch(query, *params)

                configs = []
                for row in rows:
                    config_data = {
                        "key": row["key"],
                        "value": row["value"],
                        "value_type": row["value_type"],
                        "environment": row["environment"],
                        "service": row["service"],
                        "version": row["version"],
                        "encrypted": row["encrypted"],
                        "description": row["description"],
                        "tags": row["tags"] or [],
                        "created_by": row["created_by"],
                        "updated_by": row["updated_by"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"]
                    }

                    # 解密配置值
                    if row["encrypted"] and self.cipher_suite:
                        config_data["value"] = await self.decrypt_value(config_data["value"])

                    configs.append(config_data)

                return configs

        except Exception as e:
            logger.error(f"Error listing configs: {e}")
            raise

    async def get_config_history(self, key: str, environment: str = "development",
                               service: str = "global", limit: int = 50) -> List[ConfigHistory]:
        """獲取配置歷史"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM config_history
                    WHERE config_key = $1 AND environment = $2 AND service = $3
                    ORDER BY change_time DESC
                    LIMIT $4
                    """,
                    key, environment, service, limit
                )

                history = []
                for row in rows:
                    history.append(ConfigHistory(
                        id=row["id"],
                        config_key=row["config_key"],
                        old_value=row["old_value"],
                        new_value=row["new_value"],
                        changed_by=row["changed_by"],
                        change_time=row["change_time"],
                        change_reason=row["change_reason"]
                    ))

                return history

        except Exception as e:
            logger.error(f"Error getting config history for {key}: {e}")
            raise

    async def get_metrics(self) -> ConfigServiceMetrics:
        """獲取配置服務指標"""
        return ConfigServiceMetrics(**self.metrics)

    async def update_metrics(self):
        """更新服務指標"""
        try:
            async with self.db_pool.acquire() as conn:
                # 統計配置數量
                total_result = await conn.fetchval("SELECT COUNT(*) FROM configs")
                self.metrics["total_configs"] = total_result

                # 按服務統計
                service_stats = await conn.fetch(
                    "SELECT service, COUNT(*) as count FROM configs GROUP BY service"
                )
                self.metrics["configs_by_service"] = {
                    row["service"]: row["count"] for row in service_stats
                }

                # 按環境統計
                env_stats = await conn.fetch(
                    "SELECT environment, COUNT(*) as count FROM configs GROUP BY environment"
                )
                self.metrics["configs_by_environment"] = {
                    row["environment"]: row["count"] for row in env_stats
                }

                # 加密配置統計
                encrypted_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM configs WHERE encrypted = TRUE"
                )
                self.metrics["encrypted_configs"] = encrypted_count

                # 最後更新時間
                last_update = await conn.fetchval(
                    "SELECT MAX(updated_at) FROM configs"
                )
                self.metrics["last_update"] = last_update

        except Exception as e:
            logger.error(f"Error updating metrics: {e}")

    async def load_metrics(self):
        """加載指標"""
        await self.update_metrics()

    async def encrypt_value(self, value: Any) -> str:
        """加密配置值"""
        if not self.cipher_suite:
            raise ValueError("Encryption not initialized")

        json_value = json.dumps(value, default=str)
        encrypted_value = self.cipher_suite.encrypt(json_value.encode())
        return encrypted_value.decode()

    async def decrypt_value(self, encrypted_value: str) -> Any:
        """解密配置值"""
        if not self.cipher_suite:
            raise ValueError("Encryption not initialized")

        decrypted_bytes = self.cipher_suite.decrypt(encrypted_value.encode())
        return json.loads(decrypted_bytes.decode())

    async def notify_config_change(self, key: str, environment: str, service: str, action: str):
        """通知配置變更"""
        message = {
            "type": "config_change",
            "key": key,
            "environment": environment,
            "service": service,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 通知所有WebSocket連接
        disconnected = set()
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                disconnected.add(websocket)

        # 清理斷開的連接
        self.websocket_connections -= disconnected


# 全局配置管理器實例
config_manager = ConfigurationManager()


# 依賴注入函數
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """獲取當前用戶（簡化認證）"""
    if credentials:
        return {"username": "authenticated_user", "roles": ["user"]}
    return {"username": "anonymous", "roles": ["readonly"]}


# API端點
@app.get("/")
async def root():
    """根端點"""
    return {
        "service": "Configuration Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }

    try:
        # 檢查Redis連接
        if config_manager.redis_client:
            await config_manager.redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "disconnected"

        # 檢查數據庫連接
        if config_manager.db_pool:
            async with config_manager.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_status["services"]["database"] = "healthy"
        else:
            health_status["services"]["database"] = "disconnected"

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)

    return health_status


@app.get("/config/{key}")
async def get_config(key: str, environment: str = "development", service: str = "global"):
    """獲取配置值"""
    try:
        config = await config_manager.get_config(key, environment, service)
        if not config:
            raise HTTPException(status_code=404, detail=f"Configuration {key} not found")
        return config
    except Exception as e:
        logger.error(f"Error getting config {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config")
async def set_config(config: ConfigValue, user: dict = Depends(get_current_user)):
    """設置配置值"""
    try:
        if "admin" not in user["roles"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        result = await config_manager.set_config(config)
        return {"message": "Configuration set successfully", "config": result}
    except Exception as e:
        logger.error(f"Error setting config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/config/{key}")
async def update_config(key: str, update: ConfigUpdate,
                       environment: str = "development", service: str = "global",
                       user: dict = Depends(get_current_user)):
    """更新配置值"""
    try:
        if "admin" not in user["roles"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        # 獲取現有配置
        existing = await config_manager.get_config(key, environment, service)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Configuration {key} not found")

        # 創建更新配置
        config_update = ConfigValue(
            key=key,
            value=update.value,
            value_type=existing["value_type"],
            environment=environment,
            service=service,
            version=existing["version"] + 1,
            encrypted=existing["encrypted"],
            description=update.description or existing["description"],
            tags=existing["tags"],
            created_by=existing["created_by"],
            updated_by=update.updated_by
        )

        result = await config_manager.set_config(config_update)
        return {"message": "Configuration updated successfully", "config": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/config/{key}")
async def delete_config(key: str, environment: str = "development", service: str = "global",
                       user: dict = Depends(get_current_user)):
    """刪除配置"""
    try:
        if "admin" not in user["roles"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        success = await config_manager.delete_config(key, environment, service)
        if not success:
            raise HTTPException(status_code=404, detail=f"Configuration {key} not found")
        return {"message": "Configuration deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting config {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/configs")
async def list_configs(environment: str = None, service: str = None, tags: str = None):
    """列出配置"""
    try:
        tag_list = tags.split(",") if tags else None
        configs = await config_manager.list_configs(environment, service, tag_list)
        return {"configs": configs, "total": len(configs)}
    except Exception as e:
        logger.error(f"Error listing configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config/{key}/history")
async def get_config_history(key: str, environment: str = "development",
                           service: str = "global", limit: int = 50):
    """獲取配置歷史"""
    try:
        history = await config_manager.get_config_history(key, environment, service, limit)
        return {"history": history, "total": len(history)}
    except Exception as e:
        logger.error(f"Error getting config history for {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """獲取服務指標"""
    try:
        metrics = await config_manager.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端點用於實時配置變更通知"""
    await websocket.accept()
    config_manager.websocket_connections.add(websocket)

    try:
        while True:
            # 保持連接活躍
            await websocket.receive_text()
    except WebSocketDisconnect:
        config_manager.websocket_connections.discard(websocket)


async def initialize_services():
    """初始化服務"""
    await config_manager.initialize()
    config_service_state["initialized"] = True
    config_service_state["start_time"] = datetime.now(timezone.utc)


async def cleanup_services():
    """清理服務"""
    if config_manager.redis_client:
        await config_manager.redis_client.close()
    if config_manager.db_pool:
        await config_manager.db_pool.close()
    config_service_state["initialized"] = False


if __name__ == "__main__":
    # 啟動配置服務
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=False,
        log_level="info"
    )