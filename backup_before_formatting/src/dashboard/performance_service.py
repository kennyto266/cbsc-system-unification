"""
港股量化交易 AI Agent 系统 - 绩效计算服务

实现PerformanceService类，计算夏普比率等绩效指标。
集成历史数据和实时交易数据，提供准确的绩效指标计算和趋势分析。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ..agents.coordinator import AgentCoordinator
from ..core import SystemConfig
from ..core.message_queue import Message, MessageQueue
from ..models.agent_dashboard import (
    BacktestMetrics,
    PerformanceMetrics,
    PerformancePeriod,
)


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

    def __init__(
        self,
        coordinator: AgentCoordinator,
        message_queue: MessageQueue,
        config: PerformanceConfig = None,
    ):
        self.coordinator = coordinator
        self.message_queue = message_queue
        self.config = config or PerformanceConfig()
        self.logger = logging.getLogger("hk_quant_system.performance_service")

        # 数据缓存
        self._agent_returns: Dict[str, pd.DataFrame] = {}
        self._performance_cache: Dict[str, PerformanceMetrics] = {}
        self._performance_history: Dict[str, List[PerformanceMetrics]] = {}
        self._last_calculation: Dict[str, datetime] = {}
        self._update_callbacks: List[Callable[[str, PerformanceMetrics], None]] = []

        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.logger.info("正在初始化绩效计算服务...")

            # 订阅绩效相关消息
            await self._subscribe_to_performance_updates()

            # 启动后台计算任务
            self._running = True
            self._update_task = asyncio.create_task(self._background_calculation_loop())

            self.logger.info("绩效计算服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"绩效计算服务初始化失败: {e}")
            return False

    async def _subscribe_to_performance_updates(self):
        """订阅绩效更新消息"""
        try:
            # 订阅交易数据消息
            await self.message_queue.subscribe("trade_data", self._handle_trade_data)

            # 订阅投资组合更新消息
            await self.message_queue.subscribe(
                "portfolio_updates", self._handle_portfolio_update
            )

            # 订阅风险指标消息
            await self.message_queue.subscribe(
                "risk_metrics", self._handle_risk_metrics
            )

            self.logger.info("已订阅绩效更新消息")

        except Exception as e:
            self.logger.error(f"订阅绩效更新消息失败: {e}")

    async def _handle_trade_data(self, message: Message):
        """处理交易数据消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            trade_data = payload.get("trade_data")

            if agent_id and trade_data:
                await self._update_agent_returns(agent_id, trade_data)

        except Exception as e:
            self.logger.error(f"处理交易数据消息失败: {e}")

    async def _handle_portfolio_update(self, message: Message):
        """处理投资组合更新消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            portfolio_data = payload.get("portfolio")

            if agent_id and portfolio_data:
                await self._update_portfolio_performance(agent_id, portfolio_data)

        except Exception as e:
            self.logger.error(f"处理投资组合更新消息失败: {e}")

    async def _handle_risk_metrics(self, message: Message):
        """处理风险指标消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            risk_data = payload.get("risk_metrics")

            if agent_id and risk_data:
                await self._update_risk_metrics(agent_id, risk_data)

        except Exception as e:
            self.logger.error(f"处理风险指标消息失败: {e}")

    async def _background_calculation_loop(self):
        """后台绩效计算循环"""
        while self._running:
            try:
                # 获取所有Agent ID
                agent_statuses = await self.coordinator.get_all_agent_statuses()

                # 计算每个Agent的绩效指标
                for agent_id in agent_statuses.keys():
                    await self._calculate_agent_performance(agent_id)

                # 等待下次计算
                await asyncio.sleep(self.config.update_interval)

            except Exception as e:
                self.logger.error(f"后台绩效计算循环错误: {e}")
                await asyncio.sleep(self.config.update_interval)

    async def _update_agent_returns(self, agent_id: str, trade_data: Dict[str, Any]):
        """更新Agent的收益数据"""
        try:
            # 解析交易数据
            timestamp = datetime.fromisoformat(
                trade_data.get("timestamp", datetime.utcnow().isoformat())
            )
            pnl = trade_data.get("pnl", 0.0)

            # 初始化DataFrame（如果不存在）
            if agent_id not in self._agent_returns:
                self._agent_returns[agent_id] = pd.DataFrame(
                    columns=["timestamp", "pnl", "return"]
                )

            # 添加新数据
            new_row = pd.DataFrame(
                {
                    "timestamp": [timestamp],
                    "pnl": [pnl],
                    "return": [pnl / 1000000.0],  # 假设初始资金100万
                }
            )

            self._agent_returns[agent_id] = pd.concat(
                [self._agent_returns[agent_id], new_row], ignore_index=True
            )

            # 限制历史数据长度
            max_rows = self.config.max_history_days
            if len(self._agent_returns[agent_id]) > max_rows:
                self._agent_returns[agent_id] = self._agent_returns[agent_id].tail(
                    max_rows
                )

            # 标记需要重新计算绩效
            self._last_calculation[agent_id] = datetime.min

        except Exception as e:
            self.logger.error(f"更新Agent收益数据失败 {agent_id}: {e}")

    async def _update_portfolio_performance(
        self, agent_id: str, portfolio_data: Dict[str, Any]
    ):
        """更新投资组合绩效数据"""
        try:
            # 从投资组合数据中提取绩效信息
            total_value = portfolio_data.get("total_value", 0.0)
            initial_value = portfolio_data.get("initial_value", 1000000.0)

            # 计算总收益率
            total_return = (total_value - initial_value) / initial_value

            # 更新收益数据
            await self._update_agent_returns(
                agent_id,
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "pnl": total_value - initial_value,
                    "total_value": total_value,
                },
            )

        except Exception as e:
            self.logger.error(f"更新投资组合绩效失败 {agent_id}: {e}")

    async def _update_risk_metrics(self, agent_id: str, risk_data: Dict[str, Any]):
        """更新风险指标"""
        try:
            # 从风险数据中提取VaR等信息
            var_95 = risk_data.get("var_95", 0.0)
            var_99 = risk_data.get("var_99", 0.0)
            cvar_95 = risk_data.get("cvar_95", 0.0)

            # 更新缓存中的绩效指标
            if agent_id in self._performance_cache:
                self._performance_cache[agent_id].var_95 = var_95
                self._performance_cache[agent_id].var_99 = var_99
                self._performance_cache[agent_id].cvar_95 = cvar_95

        except Exception as e:
            self.logger.error(f"更新风险指标失败 {agent_id}: {e}")

    async def _calculate_agent_performance(self, agent_id: str):
        """计算指定Agent的绩效指标"""
        try:
            # 检查是否需要重新计算
            if agent_id in self._last_calculation:
                last_calc = self._last_calculation[agent_id]
                if (
                    datetime.utcnow() - last_calc
                ).total_seconds() < self.config.update_interval:
                    return  # 计算间隔未到，跳过

            # 检查是否有足够的数据
            if (
                agent_id not in self._agent_returns
                or len(self._agent_returns[agent_id]) < 2
            ):
                return

            # 获取收益数据
            returns_df = self._agent_returns[agent_id]
            returns = returns_df["return"].dropna()

            if len(returns) < 2:
                return

            # 计算绩效指标
            performance_metrics = await self._calculate_performance_metrics(
                agent_id, returns
            )

            # 更新缓存
            self._performance_cache[agent_id] = performance_metrics
            self._last_calculation[agent_id] = datetime.utcnow()

            # 添加到历史记录
            await self._add_performance_to_history(agent_id, performance_metrics)

            # 通知回调函数
            for callback in self._update_callbacks:
                try:
                    callback(agent_id, performance_metrics)
                except Exception as e:
                    self.logger.error(f"执行绩效更新回调失败: {e}")

        except Exception as e:
            self.logger.error(f"计算Agent绩效失败 {agent_id}: {e}")

    async def _calculate_performance_metrics(
        self, agent_id: str, returns: pd.Series
    ) -> PerformanceMetrics:
        """计算绩效指标"""
        try:
            # 基础统计
            total_return = (1 + returns).prod() - 1
            annualized_return = (1 + returns.mean()) ** 252 - 1
            volatility = returns.std() * np.sqrt(252)

            # 夏普比率
            excess_return = annualized_return - self.config.risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0.0

            # 最大回撤
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(drawdown.min())

            # 交易统计
            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]
            win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0.0

            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0.0
            avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0.0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

            # 风险指标
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            cvar_95 = (
                returns[returns <= var_95].mean()
                if len(returns[returns <= var_95]) > 0
                else 0.0
            )

            # Beta和Alpha（相对于基准）
            beta = 1.0  # 默认值，实际应该相对于基准计算
            alpha = annualized_return - (
                self.config.risk_free_rate + beta * (0.08 - self.config.risk_free_rate)
            )  # 假设基准收益8%

            # 其他指标
            calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0.0
            sortino_ratio = (
                excess_return / (negative_returns.std() * np.sqrt(252))
                if len(negative_returns) > 0
                else 0.0
            )
            treynor_ratio = excess_return / beta if beta != 0 else 0.0

            # 时间范围
            period_start = (
                returns.index.min()
                if hasattr(returns.index, "min")
                else datetime.utcnow() - timedelta(days=30)
            )
            period_end = (
                returns.index.max()
                if hasattr(returns.index, "max")
                else datetime.utcnow()
            )

            return PerformanceMetrics(
                agent_id=agent_id,
                calculation_period=PerformancePeriod.DAILY,
                sharpe_ratio=sharpe_ratio,
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                trades_count=len(returns),
                avg_win=avg_win,
                avg_loss=avg_loss,
                var_95=var_95,
                var_99=var_99,
                cvar_95=cvar_95,
                beta=beta,
                alpha=alpha,
                calculation_date=datetime.utcnow(),
                period_start=period_start,
                period_end=period_end,
                benchmark_return=0.08,  # 假设基准收益8%
                excess_return=annualized_return - 0.08,
                information_ratio=excess_return / volatility if volatility > 0 else 0.0,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                treynor_ratio=treynor_ratio,
            )

        except Exception as e:
            self.logger.error(f"计算绩效指标失败 {agent_id}: {e}")
            # 返回默认绩效指标
            return PerformanceMetrics(
                agent_id=agent_id,
                calculation_period=PerformancePeriod.DAILY,
                sharpe_ratio=0.0,
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                max_drawdown=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                trades_count=0,
                avg_win=0.0,
                avg_loss=0.0,
                var_95=0.0,
                var_99=0.0,
                cvar_95=0.0,
                beta=1.0,
                alpha=0.0,
                calculation_date=datetime.utcnow(),
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
            )

    async def _add_performance_to_history(
        self, agent_id: str, performance_metrics: PerformanceMetrics
    ):
        """添加绩效指标到历史记录"""
        try:
            if agent_id not in self._performance_history:
                self._performance_history[agent_id] = []

            self._performance_history[agent_id].append(performance_metrics)

            # 限制历史记录数量
            max_history = 100
            if len(self._performance_history[agent_id]) > max_history:
                self._performance_history[agent_id] = self._performance_history[
                    agent_id
                ][-max_history:]

        except Exception as e:
            self.logger.error(f"添加绩效历史记录失败 {agent_id}: {e}")

    async def get_agent_performance(
        self, agent_id: str
    ) -> Optional[PerformanceMetrics]:
        """获取指定Agent的绩效指标"""
        try:
            # 检查缓存
            if agent_id in self._performance_cache:
                return self._performance_cache[agent_id]

            # 如果缓存中没有，立即计算
            await self._calculate_agent_performance(agent_id)
            return self._performance_cache.get(agent_id)

        except Exception as e:
            self.logger.error(f"获取Agent绩效指标失败 {agent_id}: {e}")
            return None

    async def get_all_performance(self) -> Dict[str, PerformanceMetrics]:
        """获取所有Agent的绩效指标"""
        try:
            # 获取所有Agent ID
            agent_statuses = await self.coordinator.get_all_agent_statuses()

            # 确保所有Agent的绩效都已计算
            for agent_id in agent_statuses.keys():
                if agent_id not in self._performance_cache:
                    await self._calculate_agent_performance(agent_id)

            return self._performance_cache.copy()

        except Exception as e:
            self.logger.error(f"获取所有绩效指标失败: {e}")
            return {}

    async def get_performance_history(self, agent_id: str) -> List[PerformanceMetrics]:
        """获取Agent的绩效历史记录"""
        try:
            return self._performance_history.get(agent_id, [])
        except Exception as e:
            self.logger.error(f"获取绩效历史记录失败 {agent_id}: {e}")
            return []

    async def calculate_strategy_performance(
        self,
        strategy_id: str,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
    ) -> BacktestMetrics:
        """计算策略的绩效指标"""
        try:
            if len(returns) < 2:
                return await self._get_default_backtest_metrics()

            # 基础统计
            total_return = (1 + returns).prod() - 1
            annualized_return = (1 + returns.mean()) ** 252 - 1
            volatility = returns.std() * np.sqrt(252)

            # 夏普比率
            excess_return = annualized_return - self.config.risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0.0

            # 最大回撤
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = abs(drawdown.min())

            # 交易统计
            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]
            win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0.0

            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0.0
            avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0.0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

            # 基准比较
            benchmark_return = None
            alpha = None
            beta = None
            information_ratio = None

            if benchmark_returns is not None and len(benchmark_returns) > 0:
                benchmark_return = (1 + benchmark_returns).prod() - 1

                # 计算Beta
                if len(returns) == len(benchmark_returns):
                    covariance = np.cov(returns, benchmark_returns)[0, 1]
                    benchmark_variance = np.var(benchmark_returns)
                    beta = (
                        covariance / benchmark_variance
                        if benchmark_variance > 0
                        else 1.0
                    )

                    # 计算Alpha
                    alpha = annualized_return - (
                        self.config.risk_free_rate
                        + beta * (benchmark_return * 252 - self.config.risk_free_rate)
                    )

                    # 计算信息比率
                    excess_returns = returns - benchmark_returns
                    tracking_error = excess_returns.std() * np.sqrt(252)
                    information_ratio = (
                        excess_returns.mean() * 252 / tracking_error
                        if tracking_error > 0
                        else 0.0
                    )

            return BacktestMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                trades_count=len(returns),
                avg_trade_duration=30.0,  # 假设平均持仓30天
                backtest_period_start=(
                    returns.index.min().date()
                    if hasattr(returns.index, "min")
                    else datetime.now().date()
                ),
                backtest_period_end=(
                    returns.index.max().date()
                    if hasattr(returns.index, "max")
                    else datetime.now().date()
                ),
                benchmark_return=benchmark_return,
                alpha=alpha,
                beta=beta,
                information_ratio=information_ratio,
            )

        except Exception as e:
            self.logger.error(f"计算策略绩效失败 {strategy_id}: {e}")
            return await self._get_default_backtest_metrics()

    async def _get_default_backtest_metrics(self) -> BacktestMetrics:
        """获取默认回测指标"""
        return BacktestMetrics(
            total_return=0.0,
            annualized_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            trades_count=0,
            avg_trade_duration=0.0,
            backtest_period_start=datetime.now().date(),
            backtest_period_end=datetime.now().date(),
        )

    def add_update_callback(self, callback: Callable[[str, PerformanceMetrics], None]):
        """添加绩效更新回调函数"""
        self._update_callbacks.append(callback)

    def remove_update_callback(
        self, callback: Callable[[str, PerformanceMetrics], None]
    ):
        """移除绩效更新回调函数"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理绩效计算服务...")

            self._running = False

            if self._update_task:
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass

            # 清理缓存
            self._agent_returns.clear()
            self._performance_cache.clear()
            self._performance_history.clear()
            self._last_calculation.clear()
            self._update_callbacks.clear()

            self.logger.info("绩效计算服务清理完成")

        except Exception as e:
            self.logger.error(f"清理绩效计算服务失败: {e}")


__all__ = [
    "PerformanceConfig",
    "PerformanceService",
]
