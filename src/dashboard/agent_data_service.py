"""
策略管理Dashboard - 数据服务

负责收集和聚合策略系统数据，为仪表板提供统一的数据访问层。
集成策略监控、参数优化和回测分析模块的数据。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class DataServiceConfig:
    """数据服务配置"""
    update_interval: int = 5  # 数据更新间隔（秒）
    max_history_size: int = 1000  # 最大历史数据条数
    cache_ttl: int = 30  # 缓存TTL（秒）
    enable_real_time: bool = True  # 是否启用实时更新


class StrategyDataService:
    """策略数据服务"""

    def __init__(
        self,
        config: DataServiceConfig = None
    ):
        self.config = config or DataServiceConfig()
        self.logger = logging.getLogger("strategy_dashboard.data_service")

        self._strategy_data_cache: Dict[str, Any] = {}
        self._last_update: Dict[str, datetime] = {}
        self._update_callbacks: List[Callable[[str, Any], None]] = []
        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.logger.info("初始化策略数据服务...")
            self._running = True

            # 启动后台更新任务
            if self.config.enable_real_time:
                self._update_task = asyncio.create_task(self._update_loop())

            self.logger.info("策略数据服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"初始化策略数据服务失败: {e}")
            return False

    async def start(self) -> None:
        """启动服务"""
        await self.initialize()

    async def stop(self) -> None:
        """停止服务"""
        self.logger.info("正在停止策略数据服务...")
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        self.logger.info("策略数据服务已停止")

    async def _update_loop(self) -> None:
        """后台更新循环"""
        while self._running:
            try:
                await self._collect_strategy_data()
                await asyncio.sleep(self.config.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"数据更新循环错误: {e}")
                await asyncio.sleep(self.config.update_interval)

    async def _collect_strategy_data(self) -> None:
        """收集策略数据"""
        try:
            # 模拟策略数据收集
            current_time = datetime.now()

            # 这里可以集成实际的策略数据源
            strategy_data = {
                "timestamp": current_time,
                "active_strategies": 4,
                "total_signals": 156,
                "performance": {
                    "daily_return": 0.0234,
                    "sharpe_ratio": 1.45,
                    "max_drawdown": -0.0876
                },
                "market_status": "active"
            }

            # 更新缓存
            cache_key = "strategy_summary"
            self._strategy_data_cache[cache_key] = strategy_data
            self._last_update[cache_key] = current_time

            # 通知回调
            for callback in self._update_callbacks:
                try:
                    callback(cache_key, strategy_data)
                except Exception as e:
                    self.logger.error(f"回调执行错误: {e}")

        except Exception as e:
            self.logger.error(f"收集策略数据失败: {e}")

    def get_strategy_data(self, key: str) -> Optional[Any]:
        """获取策略数据"""
        data = self._strategy_data_cache.get(key)
        if data:
            # 检查缓存是否过期
            last_update = self._last_update.get(key)
            if last_update:
                age = (datetime.now() - last_update).total_seconds()
                if age < self.config.cache_ttl:
                    return data

        return None

    def register_callback(self, callback: Callable[[str, Any], None]) -> None:
        """注册数据更新回调"""
        self._update_callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[str, Any], None]) -> None:
        """取消注册数据更新回调"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "service_running": self._running,
            "cache_size": len(self._strategy_data_cache),
            "update_callbacks": len(self._update_callbacks),
            "last_update": max(self._last_update.values()) if self._last_update else None,
            "config": {
                "update_interval": self.config.update_interval,
                "max_history_size": self.config.max_history_size,
                "cache_ttl": self.config.cache_ttl,
                "enable_real_time": self.config.enable_real_time
            }
        }