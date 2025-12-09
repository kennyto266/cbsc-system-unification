#!/usr / bin / env python3
"""
Phase 5: System Integration and Optimization
驗證系統統一入口點 - Verification System Integration

這個模塊將所有驗證系統組件整合為一個統一的高性能系統：
- Unified Verification Manager (三層驗證流水線)
- Integration Adapter (向後兼容性)
- Intelligent Cache (智能緩存系統)
- Async Processor (異步處理與並行優化)
- Monitoring Dashboard (監控儀表板)
- Telegram Alerts (警報系統)

使用方法:
    from simplified_system.src.verification import VerificationSystem

    # 創建驗證系統
    system = VerificationSystem()
    await system.start()

    # 使用驗證功能
    result = await system.verify_data(data, "test_data", "http://example.com")

    # 關閉系統
    await system.stop()
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .async_processor import (
    AsyncProcessor,
    TaskPriority,
    TaskStatus,
    get_processor_metrics,
    map_parallel,
    process_parallel,
    start_async_processor,
    stop_async_processor,
    submit_async_task,
)
from .integration_adapter import (
    BackwardCompatibilityLayer,
    VerificationEnabledGovernmentAPI,
    VerificationEnabledStockAPI,
    disable_system_verification,
    enable_system_verification,
    get_enhanced_government_api,
    get_enhanced_stock_api,
    initialize_verification_system,
)
from .intelligent_cache import (
    IntelligentCache,
    clear_cached,
    delete_cached,
    get_cache_stats,
    get_cached,
    set_cached,
)
from .monitoring_dashboard import (
    AlertManager,
    AlertRule,
    MetricsCollector,
    MonitoringDashboard,
    run_dashboard,
    setup_default_alert_rules,
    start_monitoring,
    stop_monitoring,
)
from .telegram_alerts import (
    AlertMessage,
    AlertTemplates,
    TelegramAlertBot,
    TelegramConfig,
    initialize_telegram_alerts,
    send_alert_resolution,
    send_verification_alert,
    shutdown_telegram_alerts,
)

# 導入所有驗證系統組件
from .unified_verification_manager import (
    UnifiedVerificationManager,
    VerificationResult,
    get_cache_statistics,
    get_system_metrics,
    verify_data_integrity,
    verify_government_data,
    verify_stock_data,
)

# Setup logging
logger = logging.getLogger(__name__)


class VerificationSystem:
    """統一驗證系統主類"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化驗證系統

        Args:
            config: 系統配置字典
        """
        self.config = config or self._get_default_config()
        self.is_started = False

        # 初始化各個組件
        self.verification_manager = UnifiedVerificationManager(
            self.config.get("verification_config")
        )
        self.cache = IntelligentCache(
            max_memory_mb = self.config.get("cache", {}).get("max_memory_mb", 512),
            max_entries = self.config.get("cache", {}).get("max_entries", 10000),
            enable_compression = self.config.get("cache", {}).get(
                "enable_compression", True
            ),
            enable_disk_cache = self.config.get("cache", {}).get(
                "enable_disk_cache", True
            ),
        )
        self.async_processor = AsyncProcessor(
            max_workers = self.config.get("async_processor", {}).get("max_workers", 32),
            thread_pools = self.config.get("async_processor", {}).get("thread_pools", 2),
            process_pools = self.config.get("async_processor", {}).get(
                "process_pools", 1
            ),
        )
        self.monitoring_dashboard = MonitoringDashboard(
            host = self.config.get("monitoring", {}).get("host", "0.0.0.0"),
            port = self.config.get("monitoring", {}).get("port", 8080),
        )
        self.telegram_bot = None

        # 向後兼容層
        self.compatibility_layer = BackwardCompatibilityLayer()

        # 系統統計信息
        self.start_time = None
        self.operation_count = 0

        logger.info("VerificationSystem initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "verification_config": {
                "verification_pipeline": {
                    "layers": {
                        "source_auth": {
                            "enabled": True,
                            "parallel_execution": True,
                            "cache_ttl": 300,
                        },
                        "content_validation": {
                            "enabled": True,
                            "parallel_execution": True,
                            "cache_ttl": 600,
                        },
                        "behavioral_analysis": {
                            "enabled": True,
                            "parallel_execution": False,
                            "cache_ttl": 1800,
                        },
                    }
                },
                "performance": {
                    "max_concurrent_verifications": 100,
                    "batch_size": 10,
                    "timeout_ms": 5000,
                },
                "alerts": {
                    "telegram_bot": True,
                    "severity_thresholds": {
                        "critical": 0.95,
                        "high": 0.85,
                        "medium": 0.70,
                        "low": 0.50,
                    },
                },
            },
            "cache": {
                "max_memory_mb": 512,
                "max_entries": 10000,
                "enable_compression": True,
                "enable_disk_cache": True,
                "enable_redis": False,
            },
            "async_processor": {
                "max_workers": 32,
                "thread_pools": 2,
                "process_pools": 1,
                "enable_monitoring": True,
            },
            "monitoring": {
                "host": "0.0.0.0",
                "port": 8080,
                "collection_interval": 10,
                "enable_alerts": True,
            },
            "telegram": {
                "enabled": False,
                "bot_token": None,
                "chat_ids": [],
                "alert_levels": ["critical", "high", "medium"],
            },
        }

    async def start(self):
        """啟動驗證系統"""
        if self.is_started:
            logger.warning("VerificationSystem is already started")
            return

        try:
            logger.info("Starting VerificationSystem...")

            # 啟動異步處理器
            await self.async_processor.start()
            logger.info("✅ Async processor started")

            # 啟動監控儀表板
            await self.monitoring_dashboard.start()
            logger.info("✅ Monitoring dashboard started")

            # 設置默認警報規則
            setup_default_alert_rules()
            logger.info("✅ Default alert rules configured")

            # 啟動Telegram警報（如果配置了）
            telegram_config = self.config.get("telegram", {})
            if telegram_config.get("enabled") and telegram_config.get("bot_token"):
                try:
                    self.telegram_bot = await initialize_telegram_alerts(
                        bot_token = telegram_config["bot_token"],
                        chat_ids = telegram_config["chat_ids"],
                        alert_levels = telegram_config["alert_levels"],
                    )
                    logger.info("✅ Telegram alerts started")
                except Exception as e:
                    logger.error(f"❌ Failed to start Telegram alerts: {e}")

            # 啟用向後兼容性
            if self.config.get("enable_backward_compatibility", True):
                self.compatibility_layer.enable_verification(
                    auto_verify = self.config.get("auto_verify", False)
                )
                logger.info("✅ Backward compatibility enabled")

            # 設置全局實例（為了便利函數）
            self._setup_global_instances()

            # 記錄啟動時間
            self.start_time = time.time()

            self.is_started = True
            logger.info("🚀 VerificationSystem started successfully")

            # 記錄啟動成功警報
            if self.telegram_bot:
                await send_verification_alert(
                    alert_id="system_startup",
                    title="Verification System Started",
                    message="All components started successfully",
                    severity="low",
                    metric_name="system.status",
                    current_value = 1,
                    threshold = 0,
                )

        except Exception as e:
            logger.error(f"❌ Failed to start VerificationSystem: {e}")
            await self.stop()
            raise

    async def stop(self):
        """停止驗證系統"""
        if not self.is_started:
            return

        try:
            logger.info("Stopping VerificationSystem...")

            # 記錄停止警報
            if self.telegram_bot:
                await send_verification_alert(
                    alert_id="system_shutdown",
                    title="Verification System Stopping",
                    message="System is shutting down",
                    severity="low",
                    metric_name="system.status",
                    current_value = 0,
                    threshold = 0,
                )

            # 停止各個組件
            if self.telegram_bot:
                await shutdown_telegram_alerts()
                logger.info("✅ Telegram alerts stopped")

            await self.monitoring_dashboard.stop()
            logger.info("✅ Monitoring dashboard stopped")

            await self.async_processor.stop()
            logger.info("✅ Async processor stopped")

            self.cache.shutdown()
            logger.info("✅ Cache system stopped")

            if self.verification_manager:
                await self.verification_manager.shutdown()
                logger.info("✅ Verification manager stopped")

            # 禁用向後兼容性
            self.compatibility_layer.disable_verification()
            logger.info("✅ Backward compatibility disabled")

            self.is_started = False
            logger.info("🛑 VerificationSystem stopped successfully")

        except Exception as e:
            logger.error(f"❌ Error stopping VerificationSystem: {e}")

    def _setup_global_instances(self):
        """設置全局實例"""
        import sys

        # 設置全局驗證管理器
        sys.modules[__name__].verification_manager = self.verification_manager

        # 設置全局緩存
        sys.modules[__name__].cache = self.cache

        # 設置全局異步處理器
        sys.modules[__name__].async_processor = self.async_processor

        # 設置全局監控儀表板
        sys.modules[__name__].monitoring_dashboard = self.monitoring_dashboard

        # 設置全局Telegram機器人
        sys.modules[__name__].telegram_bot = self.telegram_bot

    async def verify_data(
        self,
        data: Any,
        data_type: str,
        source_url: Optional[str] = None,
        historical_context: Optional[Dict] = None,
    ) -> VerificationResult:
        """驗證數據"""
        if not self.is_started:
            raise RuntimeError("VerificationSystem is not started")

        self.operation_count += 1

        # 使用異步處理器進行驗證
        task_id = await self.async_processor.submit_task(
            func = self.verification_manager.verify_data,
            args=(data, data_type, source_url, historical_context),
            priority = TaskPriority.NORMAL,
        )

        # 等待結果
        return await self.async_processor.scheduler.get_task_result(task_id)

    async def verify_batch(
        self,
        data_batch: List[Tuple[Any, str, Optional[str]]],
        historical_context: Optional[Dict] = None,
    ) -> List[VerificationResult]:
        """批量驗證數據"""
        if not self.is_started:
            raise RuntimeError("VerificationSystem is not started")

        # 創建批量任務
        tasks = []
        for data, data_type, source_url in data_batch:
            task_id = await self.async_processor.submit_task(
                func = self.verification_manager.verify_data,
                args=(data, data_type, source_url, historical_context),
                priority = TaskPriority.NORMAL,
            )
            tasks.append(task_id)

        # 等待所有結果
        results = []
        for task_id in tasks:
            result = await self.async_processor.scheduler.get_task_result(task_id)
            results.append(result)

        self.operation_count += len(data_batch)
        return results

    async def verify_government_data(
        self, data_type: str, days_back: int = 30
    ) -> VerificationResult:
        """驗證政府數據"""
        if not self.is_started:
            raise RuntimeError("VerificationSystem is not started")

        return await self.verification_manager.verify_government_data(
            data_type, days_back
        )

    async def verify_stock_data(
        self, symbol: str, duration_days: int = 1095
    ) -> VerificationResult:
        """驗證股票數據"""
        if not self.is_started:
            raise RuntimeError("VerificationSystem is not started")

        return await self.verification_manager.verify_stock_data(symbol, duration_days)

    async def process_data_parallel(
        self, data_items: List[Any], processor_func: Callable, max_concurrent: int = 50
    ) -> List[Any]:
        """並行處理數據"""
        if not self.is_started:
            raise RuntimeError("VerificationSystem is not started")

        return await self.async_processor.process_parallel(
            data_items = data_items,
            processor_func = processor_func,
            max_concurrent = max_concurrent,
        )

    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        uptime = time.time() - self.start_time if self.start_time else 0

        return {
            "is_started": self.is_started,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "operation_count": self.operation_count,
            "components": {
                "verification_manager": self.verification_manager is not None,
                "cache": self.cache is not None,
                "async_processor": self.async_processor is not None,
                "monitoring_dashboard": self.monitoring_dashboard is not None,
                "telegram_bot": self.telegram_bot is not None,
            },
            "dashboard_url": (
                f"http://{self.monitoring_dashboard.host}:{self.monitoring_dashboard.port}"
                if self.is_started
                else None
            ),
        }

    def _format_uptime(self, seconds: float) -> str:
        """格式化運行時間"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    async def run_health_check(self) -> Dict[str, Any]:
        """運行健康檢查"""
        health_status = {
            "overall_status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {},
        }

        try:
            # 檢查驗證管理器
            if self.verification_manager:
                metrics = self.verification_manager.get_metrics()
                health_status["components"]["verification_manager"] = {
                    "status": (
                        "healthy" if metrics.total_verifications >= 0 else "unhealthy"
                    ),
                    "metrics": metrics.__dict__,
                }

            # 檢查緩存系統
            if self.cache:
                cache_stats = self.cache.get_stats()
                health_status["components"]["cache"] = {
                    "status": (
                        "healthy"
                        if cache_stats.get("entries_count", 0) >= 0
                        else "unhealthy"
                    ),
                    "stats": cache_stats,
                }

            # 檢查異步處理器
            if self.async_processor:
                processor_metrics = self.async_processor.get_performance_metrics()
                health_status["components"]["async_processor"] = {
                    "status": "healthy" if processor_metrics else "unhealthy",
                    "metrics": processor_metrics,
                }

            # 檢查監控儀表板
            health_status["components"]["monitoring_dashboard"] = {
                "status": "healthy" if self.monitoring_dashboard else "unhealthy",
                "url": (
                    f"http://{self.monitoring_dashboard.host}:{self.monitoring_dashboard.port}"
                    if self.monitoring_dashboard
                    else None
                ),
            }

            # 檢查Telegram機器人
            health_status["components"]["telegram_bot"] = {
                "status": "healthy" if self.telegram_bot else "disabled"
            }

            # 確定整體狀態
            component_statuses = [
                comp["status"] for comp in health_status["components"].values()
            ]
            if all(status == "healthy" for status in component_statuses):
                health_status["overall_status"] = "healthy"
            elif any(status == "unhealthy" for status in component_statuses):
                health_status["overall_status"] = "unhealthy"
            else:
                health_status["overall_status"] = "degraded"

        except Exception as e:
            health_status["overall_status"] = "unhealthy"
            health_status["error"] = str(e)

        return health_status


# 全局系統實例
verification_system = None


async def create_verification_system(
    config: Optional[Dict[str, Any]] = None,
) -> VerificationSystem:
    """創建驗證系統實例"""
    global verification_system

    verification_system = VerificationSystem(config)
    return verification_system


async def start_verification_system(
    config: Optional[Dict[str, Any]] = None,
) -> VerificationSystem:
    """啟動驗證系統"""
    system = await create_verification_system(config)
    await system.start()
    return system


async def get_verification_system() -> Optional[VerificationSystem]:
    """獲取當前驗證系統實例"""
    return verification_system


# 便利函數
async def verify(
    data: Any, data_type: str, source_url: Optional[str] = None
) -> VerificationResult:
    """便利函數：驗證數據"""
    system = await get_verification_system()
    if not system:
        raise RuntimeError("Verification system is not initialized")

    return await system.verify_data(data, data_type, source_url)


async def verify_batch(
    data_batch: List[Tuple[Any, str, Optional[str]]],
) -> List[VerificationResult]:
    """便利函數：批量驗證數據"""
    system = await get_verification_system()
    if not system:
        raise RuntimeError("Verification system is not initialized")

    return await system.verify_batch(data_batch)


def get_system_info() -> Dict[str, Any]:
    """便利函數：獲取系統信息"""
    if verification_system:
        return verification_system.get_system_status()
    else:
        return {"is_started": False, "message": "Verification system not initialized"}


# 導出主要類和函數
__all__ = [
    # 主要類
    "VerificationSystem",
    "UnifiedVerificationManager",
    "VerificationEnabledGovernmentAPI",
    "VerificationEnabledStockAPI",
    "IntelligentCache",
    "AsyncProcessor",
    "MonitoringDashboard",
    "TelegramAlertBot",
    # 便利函數
    "create_verification_system",
    "start_verification_system",
    "get_verification_system",
    "verify",
    "verify_batch",
    "get_system_info",
    "verify_data_integrity",
    "verify_government_data",
    "verify_stock_data",
    # 配置和設置
    "initialize_verification_system",
    "enable_system_verification",
    "disable_system_verification",
    "start_monitoring",
    "stop_monitoring",
    "run_dashboard",
    # 全局實例
    "verification_system",
]

if __name__ == "__main__":

    async def test_verification_system():
        """測試完整驗證系統"""
        print("🚀 Testing Complete Verification System...")

        try:
            # 創建配置
            config = {
                "telegram": {
                    "enabled": False,  # 設置為True並提供真實的bot token來測試Telegram警報
                    "bot_token": None,
                    "chat_ids": [],
                },
                "monitoring": {"port": 8081},  # 使用不同的端口避免衝突
            }

            # 啟動系統
            print("\n1. Starting verification system...")
            system = await start_verification_system(config)

            # 顯示系統狀態
            print("\n2. System status:")
            status = system.get_system_status()
            for key, value in status.items():
                print(f"  {key}: {value}")

            # 測試數據驗證
            print("\n3. Testing data verification...")
            test_data = {
                "timestamp": "2025 - 01 - 01T00:00:00Z",
                "data": {"value": 100, "type": "test"},
                "source": "test_system",
            }

            result = await system.verify_data(
                test_data, "test_data", "http://example.com"
            )
            print(f"Verification result:")
            print(f"  Composite score: {result.composite_score:.3f}")
            print(f"  Verification time: {result.verification_time_ms:.2f}ms")
            print(f"  Alerts: {len(result.alerts)}")

            # 測試批量驗證
            print("\n4. Testing batch verification...")
            test_batch = [
                (test_data, "test_data_1", "http://example.com / 1"),
                (test_data, "test_data_2", "http://example.com / 2"),
                (test_data, "test_data_3", "http://example.com / 3"),
            ]

            batch_results = await system.verify_batch(test_batch)
            print(f"Batch verification completed: {len(batch_results)} results")
            for i, result in enumerate(batch_results):
                print(
                    f"  Result {i + 1}: score={result.composite_score:.3f}, time={result.verification_time_ms:.2f}ms"
                )

            # 運行健康檢查
            print("\n5. Running health check...")
            health = await system.run_health_check()
            print(f"Overall status: {health['overall_status']}")
            for component, status in health["components"].items():
                print(f"  {component}: {status['status']}")

            print(f"\n🌐 Dashboard available at: {status['dashboard_url']}")
            print("\n6. System is running... Press Ctrl + C to stop")

            # 保持系統運行
            try:
                while True:
                    await asyncio.sleep(10)
            except KeyboardInterrupt:
                print("\n\n7. Stopping verification system...")

        finally:
            # 停止系統
            if verification_system:
                await verification_system.stop()

        print("\n✅ Verification system test completed!")

    # 運行測試
    asyncio.run(test_verification_system())
