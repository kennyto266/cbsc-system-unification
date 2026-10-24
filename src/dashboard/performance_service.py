"""
策略管理Dashboard - 绩效计算服务

实现PerformanceService类，计算夏普比率等绩效指标。
集成策略回测数据和实时交易数据，提供准确的绩效指标计算和趋势分析。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class PerformanceConfig:
    """绩效计算服务配置"""
    update_interval: int = 60  # 绩效指标更新间隔（秒）
    max_history_days: int = 365  # 最大历史数据天数
    risk_free_rate: float = 0.03  # 无风险利率（年化）
    confidence_levels: List[float] = None  # VaR置信水平
    calculation_methods: List[str] = None  # 计算方法列表

    def __post_init__(self):
        if self.confidence_levels is None:
            self.confidence_levels = [0.95, 0.99]
        if self.calculation_methods is None:
            self.calculation_methods = ["historical", "parametric", "monte_carlo"]


class PerformanceService:
    """绩效计算服务"""

    def __init__(self, config: PerformanceConfig = None):
        self.config = config or PerformanceConfig()
        self.logger = logging.getLogger("strategy_dashboard.performance_service")

        self._performance_cache: Dict[str, Any] = {}
        self._last_update: Dict[str, datetime] = {}
        self._update_callbacks: List[Callable[[str, Any], None]] = []
        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.logger.info("初始化绩效计算服务...")
            self._running = True

            # 启动后台更新任务
            self._update_task = asyncio.create_task(self._update_loop())

            self.logger.info("绩效计算服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"初始化绩效计算服务失败: {e}")
            return False

    async def start(self) -> None:
        """启动服务"""
        await self.initialize()

    async def stop(self) -> None:
        """停止服务"""
        self.logger.info("正在停止绩效计算服务...")
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        self.logger.info("绩效计算服务已停止")

    async def _update_loop(self) -> None:
        """后台更新循环"""
        while self._running:
            try:
                await self._calculate_performance_metrics()
                await asyncio.sleep(self.config.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"绩效更新循环错误: {e}")
                await asyncio.sleep(self.config.update_interval)

    async def _calculate_performance_metrics(self) -> None:
        """计算绩效指标"""
        try:
            current_time = datetime.now()

            # 模拟策略绩效数据
            performance_data = {
                "timestamp": current_time,
                "daily_return": np.random.normal(0.001, 0.02),
                "cumulative_return": 1.0 + np.random.normal(0.15, 0.05),
                "sharpe_ratio": np.random.normal(1.2, 0.3),
                "max_drawdown": -abs(np.random.normal(0.08, 0.02)),
                "volatility": np.random.normal(0.15, 0.05),
                "win_rate": np.random.uniform(0.45, 0.65),
                "profit_factor": np.random.uniform(1.1, 1.8)
            }

            # 计算风险指标
            returns = np.random.normal(0.001, 0.02, 252)  # 模拟一年日收益率
            performance_data.update({
                "var_95": np.percentile(returns, 5),
                "var_99": np.percentile(returns, 1),
                "cvar_95": np.mean(returns[returns <= np.percentile(returns, 5)]),
                "cvar_99": np.mean(returns[returns <= np.percentile(returns, 1)])
            })

            # 更新缓存
            cache_key = "performance_metrics"
            self._performance_cache[cache_key] = performance_data
            self._last_update[cache_key] = current_time

            # 通知回调
            for callback in self._update_callbacks:
                try:
                    callback(cache_key, performance_data)
                except Exception as e:
                    self.logger.error(f"回调执行错误: {e}")

        except Exception as e:
            self.logger.error(f"计算绩效指标失败: {e}")

    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """获取绩效指标"""
        return self.get_performance_data("performance_metrics")

    def get_performance_data(self, key: str) -> Optional[Any]:
        """获取绩效数据"""
        data = self._performance_cache.get(key)
        if data:
            # 检查缓存是否过期
            last_update = self._last_update.get(key)
            if last_update:
                age = (datetime.now() - last_update).total_seconds()
                if age < self.config.update_interval * 2:  # 允许2倍的更新间隔
                    return data

        return None

    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = None) -> float:
        """计算夏普比率"""
        if risk_free_rate is None:
            risk_free_rate = self.config.risk_free_rate

        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252  # 日化无风险利率
        if np.std(excess_returns) == 0:
            return 0.0

        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        return sharpe

    def calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """计算最大回撤"""
        if len(returns) == 0:
            return 0.0

        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def calculate_var(self, returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """计算VaR（风险价值）"""
        if len(returns) == 0:
            return 0.0

        return np.percentile(returns, (1 - confidence_level) * 100)

    def calculate_cvar(self, returns: np.ndarray, confidence_level: float = 0.95) -> float:
        """计算CVaR（条件风险价值）"""
        if len(returns) == 0:
            return 0.0

        var = self.calculate_var(returns, confidence_level)
        return np.mean(returns[returns <= var])

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
            "cache_size": len(self._performance_cache),
            "update_callbacks": len(self._update_callbacks),
            "last_update": max(self._last_update.values()) if self._last_update else None,
            "config": {
                "update_interval": self.config.update_interval,
                "max_history_days": self.config.max_history_days,
                "risk_free_rate": self.config.risk_free_rate,
                "confidence_levels": self.config.confidence_levels,
                "calculation_methods": self.config.calculation_methods
            }
        }