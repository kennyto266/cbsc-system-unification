#!/usr / bin / env python3
"""
API網關主程序
港股量化交易系統 - 統一API網關入口

啟動和配置統一API網關，加載所有必要的中間件、
服務註冊中心、路由等組件。

使用方法:
    python main.py [--config config.yaml] [--host 0.0.0.0] [--port 7777]
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
import yaml
from fastapi import FastAPI

from .api_standards import APISecurity, APIVersioning
from .middleware import create_middleware_chain
from .service_registry import ServiceRegistry, create_service_registry
from .unified_gateway import APIGateway

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("api_gateway.log"),
    ],
)

logger = logging.getLogger(__name__)


class GatewayManager:
    """網關管理器"""

    def __init__(self):
        self.gateway: Optional[APIGateway] = None
        self.service_registry: Optional[ServiceRegistry] = None
        self.config: Dict[str, Any] = {}
        self.shutdown_event = asyncio.Event()

    async def initialize(self, config_path: Optional[str] = None):
        """初始化網關"""
        logger.info("初始化API網關...")

        # 加載配置
        self.config = self._load_config(config_path)

        # 初始化服務註冊中心
        await self._initialize_service_registry()

        # 初始化API網關
        await self._initialize_gateway()

        # 設置信號處理
        self._setup_signal_handlers()

        logger.info("API網關初始化完成")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加載配置文件"""
        if not config_path:
            # 嘗試默認配置文件
            default_configs = [
                "config / gateway.yaml",
                "config / gateway.yml",
                "gateway_config.yaml",
                "gateway_config.yml",
            ]

            for default_config in default_configs:
                if Path(default_config).exists():
                    config_path = default_config
                    break

        if config_path and Path(config_path).exists():
            logger.info(f"加載配置文件: {config_path}")

            with open(config_path, "r", encoding="utf - 8") as f:
                if config_path.endswith((".yaml", ".yml")):
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)

        else:
            logger.warning("未找到配置文件，使用默認配置")
            config = self._get_default_config()

        # 處理環境變量覆蓋
        config = self._apply_env_overrides(config)

        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "server": {"host": "0.0.0.0", "port": 7777, "log_level": "info"},
            "gateway": {"name": "HK Quant API Gateway", "version": "1.0.0"},
            "auth": {
                "jwt": {
                    "enabled": True,
                    "secret": "your - secret - key - change - in - production",
                    "algorithm": "HS256",
                }
            },
            "cors": {"enabled": True, "allow_origins": ["*"]},
            "rate_limiting": {"enabled": False, "default_limit": 1000},
            "caching": {"enabled": False, "default_ttl": 300},
            "redis": {"enabled": False, "url": "redis://localhost:6379 / 0"},
            "monitoring": {"enabled": True, "metrics": True, "health_check": True},
        }

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """應用環境變量覆蓋"""
        env_mappings = {
            "API_GATEWAY_HOST": ("server", "host"),
            "API_GATEWAY_PORT": ("server", "port"),
            "LOG_LEVEL": ("server", "log_level"),
            "JWT_SECRET": ("auth", "jwt", "secret"),
            "REDIS_URL": ("redis", "url"),
            "ENABLE_CORS": ("cors", "enabled"),
            "ENABLE_RATE_LIMITING": ("rate_limiting", "enabled"),
            "ENABLE_CACHING": ("caching", "enabled"),
        }

        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 轉換類型
                if env_value.lower() in ("true", "false"):
                    env_value = env_value.lower() == "true"
                elif env_value.isdigit():
                    env_value = int(env_value)

                # 應用配置
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]

                current[config_path[-1]] = env_value
                logger.info(f"環境變量覆蓋: {env_var} = {env_value}")

        return config

    async def _initialize_service_registry(self):
        """初始化服務註冊中心"""
        logger.info("初始化服務註冊中心...")

        # 檢查Redis配置
        redis_client = None
        if self.config.get("redis", {}).get("enabled"):
            try:
                import redis

                redis_url = self.config["redis"]["url"]
                redis_client = redis.from_url(redis_url)
                logger.info(f"Redis連接成功: {redis_url}")
            except Exception as e:
                logger.error(f"Redis連接失敗: {e}")

        # 創建服務註冊中心
        self.service_registry = create_service_registry(redis_client)

        # 註冊服務配置
        services_config = self.config.get("service_registry", {}).get("services", {})
        for service_name, service_config in services_config.items():
            from .service_registry import ServiceConfig

            config = ServiceConfig(
                name=service_name,
                prefix=service_config.get("prefix", f"/api / v1/{service_name}"),
                health_check_path=service_config.get("health_check_path", "/health"),
                health_check_interval=service_config.get("health_check_interval", 30),
                health_check_timeout=service_config.get("health_check_timeout", 5),
                health_check_retries=service_config.get("health_check_retries", 3),
                timeout=service_config.get("timeout", 30),
                retries=service_config.get("retries", 3),
                metadata=service_config.get("metadata", {}),
            )

            self.service_registry.register_service(config)

        # 啟動健康檢查
        await self.service_registry.start_health_check()

        logger.info("服務註冊中心初始化完成")

    async def _initialize_gateway(self):
        """初始化API網關"""
        logger.info("初始化API網關...")

        # 創建網關配置
        gateway_config = {
            "cors_origins": self.config.get("cors", {}).get("allow_origins", ["*"]),
            "jwt_secret": self.config.get("auth", {}).get("jwt", {}).get("secret"),
            "redis_client": getattr(self.service_registry, "redis_client", None),
            "rate_limits": self.config.get("rate_limiting", {}).get("limits"),
        }

        # 權限映射
        permissions = self.config.get("auth", {}).get("permissions", {})
        if permissions:
            gateway_config["permissions_map"] = permissions

        # 創建API網關
        self.gateway = APIGateway(gateway_config)

        # 創建FastAPI應用
        app = self.gateway.create_app()

        # 添加中間件
        middlewares_config = self._prepare_middleware_config()
        middlewares = create_middleware_chain(app, middlewares_config)

        # 添加自定義路由
        self._add_custom_routes(app)

        logger.info("API網關初始化完成")

    def _prepare_middleware_config(self) -> Dict[str, Any]:
        """準備中間件配置"""
        return {
            "security_enabled": self.config.get("security", {}).get("enabled", True),
            "rate_limit_enabled": self.config.get("rate_limiting", {}).get(
                "enabled", False
            ),
            "auth_enabled": self.config.get("auth", {})
            .get("jwt", {})
            .get("enabled", True),
            "cache_enabled": self.config.get("caching", {}).get("enabled", False),
            "performance_monitoring_enabled": self.config.get("monitoring", {}).get(
                "enabled", True
            ),
            "response_formatting_enabled": True,
            "redis_client": getattr(self.service_registry, "redis_client", None),
            "jwt_secret": self.config.get("auth", {}).get("jwt", {}).get("secret"),
            "rate_limits": self.config.get("rate_limiting", {}).get("limits"),
            "permissions_map": self.config.get("auth", {}).get("permissions"),
            "cache_duration": self.config.get("caching", {}).get("default_ttl", 300),
        }

    def _add_custom_routes(self, app: FastAPI):
        """添加自定義路由"""

        # 服務狀態端點
        @app.get("/api / v1 / services / status", tags=["系統"])
        async def get_services_status():
            """獲取所有服務狀態"""
            if self.service_registry:
                return {
                    "success": True,
                    "data": self.service_registry.get_service_status(),
                }
            return {"success": False, "error": {"message": "服務註冊中心未初始化"}}

        # 配置信息端點
        @app.get("/api / v1 / gateway / config", tags=["系統"])
        async def get_gateway_config():
            """獲取網關配置信息"""
            # 返回安全配置信息（不包含敏感數據）
            safe_config = {
                "gateway": self.config.get("gateway", {}),
                "server": self.config.get("server", {}),
                "api_version": APIVersioning.CURRENT_VERSION,
                "cors": {
                    "enabled": self.config.get("cors", {}).get("enabled"),
                    "allow_origins": self.config.get("cors", {}).get(
                        "allow_origins", []
                    ),
                },
                "monitoring": {
                    "enabled": self.config.get("monitoring", {}).get("enabled")
                },
            }

            return {"success": True, "data": safe_config}

    def _setup_signal_handlers(self):
        """設置信號處理"""

        def signal_handler(signum, frame):
            logger.info(f"收到信號 {signum}，開始優雅關閉...")
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self, host: str = "0.0.0.0", port: int = 7777):
        """運行網關"""
        if not self.gateway:
            raise RuntimeError("網關未初始化")

        app = self.gateway.app

        # 打印啟動信息
        self._print_startup_info(host, port)

        # 創建uvicorn配置
        uvicorn_config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level=self.config.get("server", {}).get("log_level", "info"),
            access_log=self.config.get("server", {}).get("access_log", True),
            reload=self.config.get("server", {}).get("reload", False),
        )

        server = uvicorn.Server(uvicorn_config)

        # 運行服務器
        try:
            await server.serve()
        except Exception as e:
            logger.error(f"服務器運行錯誤: {e}")
        finally:
            await self.cleanup()

    def _print_startup_info(self, host: str, port: int):
        """打印啟動信息"""
        gateway_info = self.config.get("gateway", {})
        version = gateway_info.get("version", "1.0.0")
        name = gateway_info.get("name", "API Gateway")

        print(
            """
╔══════════════════════════════════════════════════════════════╗
║           {name:^58} ║
╠══════════════════════════════════════════════════════════════╣
║ 版本: {version:>55} ║
║ 地址: http://{host}:{port:<40} ║
║ 文檔: http://{host}:{port}/docs{"":36} ║
║ 狀態: http://{host}:{port}/health{"":36} ║
║ 監控: http://{host}:{port}/metrics{"":35} ║
╚══════════════════════════════════════════════════════════════╝

        🚀 統一API網關已啟動 🚀
        配置文件: {self.config.get('config_file', '默認配置')}
        服務註冊: {'啟用' if self.service_registry else '禁用'}
        Redis: {'啟用' if self.config.get('redis', {}).get('enabled') else '禁用'}
        限流: {'啟用' if self.config.get('rate_limiting', {}).get('enabled') else '禁用'}
        緩存: {'啟用' if self.config.get('caching', {}).get('enabled') else '禁用'}

        按下 Ctrl + C 停止服務器
        """
        )

    async def cleanup(self):
        """清理資源"""
        logger.info("開始清理資源...")

        if self.service_registry:
            await self.service_registry.close()

        if (
            self.gateway
            and hasattr(self.gateway, "redis_client")
            and self.gateway.redis_client
        ):
            await self.gateway.redis_client.close()

        logger.info("資源清理完成")


async def main():
    """主函數"""
    # 解析命令行參數
    parser = argparse.ArgumentParser(description="港股量化交易系統 - 統一API網關")
    parser.add_argument("--config", help="配置文件路徑")
    parser.add_argument("--host", default="0.0.0.0", help="綁定主機地址")
    parser.add_argument("--port", type=int, default=7777, help="綁定端口")
    parser.add_argument("--log - level", default="INFO", help="日誌級別")

    args = parser.parse_args()

    # 設置日誌級別
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))

    try:
        # 創建網關管理器
        manager = GatewayManager()

        # 初始化網關
        await manager.initialize(args.config)

        # 運行網關
        await manager.run(args.host, args.port)

    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉...")
    except Exception as e:
        logger.error(f"網關運行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
