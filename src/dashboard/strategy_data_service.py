"""
港股量化交易 AI Agent 系统 - 策略数据服务

负责收集和展示交易策略信息，从各个Agent获取当前策略参数和回测结果。
提供策略信息的统一访问接口，支持策略变更历史和实时策略状态监控。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..core import SystemConfig
from ..core.message_queue import MessageQueue, Message
from ..agents.coordinator import AgentCoordinator
from ..models.agent_dashboard import (
    StrategyInfo, 
    StrategyType, 
    StrategyStatus,
    StrategyParameter,
    BacktestMetrics,
    LiveMetrics
)


@dataclass
class StrategyDataConfig:
    """策略数据服务配置"""
    update_interval: int = 10  # 策略数据更新间隔（秒）
    max_strategy_history: int = 100  # 最大策略历史记录数
    cache_ttl: int = 60  # 缓存TTL（秒）
    enable_strategy_monitoring: bool = True  # 是否启用策略监控


class StrategyDataService:
    """策略数据服务"""
    
    def __init__(
        self, 
        coordinator: AgentCoordinator,
        message_queue: MessageQueue,
        config: StrategyDataConfig = None
    ):
        self.coordinator = coordinator
        self.message_queue = message_queue
        self.config = config or StrategyDataConfig()
        self.logger = logging.getLogger("hk_quant_system.strategy_data_service")
        
        # 策略数据缓存
        self._agent_strategies: Dict[str, StrategyInfo] = {}
        self._strategy_history: Dict[str, List[StrategyInfo]] = {}
        self._last_update: Dict[str, datetime] = {}
        self._update_callbacks: List[Callable[[str, StrategyInfo], None]] = []
        
        # 后台任务
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def initialize(self) -> bool:
        """初始化服务"""
        try:
            self.logger.info("正在初始化策略数据服务...")
            
            # 订阅策略相关消息
            await self._subscribe_to_strategy_updates()
            
            # 启动后台更新任务
            if self.config.enable_strategy_monitoring:
                self._running = True
                self._update_task = asyncio.create_task(self._background_update_loop())
            
            self.logger.info("策略数据服务初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"策略数据服务初始化失败: {e}")
            return False
    
    async def _subscribe_to_strategy_updates(self):
        """订阅策略更新消息"""
        try:
            # 订阅策略变更消息
            await self.message_queue.subscribe(
                "strategy_updates",
                self._handle_strategy_update
            )
            
            # 订阅策略性能更新消息
            await self.message_queue.subscribe(
                "strategy_performance",
                self._handle_strategy_performance_update
            )
            
            # 订阅回测结果消息
            await self.message_queue.subscribe(
                "backtest_results",
                self._handle_backtest_result
            )
            
            self.logger.info("已订阅策略更新消息")
            
        except Exception as e:
            self.logger.error(f"订阅策略更新消息失败: {e}")
    
    async def _handle_strategy_update(self, message: Message):
        """处理策略更新消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            strategy_data = payload.get("strategy")
            
            if agent_id and strategy_data:
                # 创建策略信息对象
                strategy_info = await self._parse_strategy_data(strategy_data)
                
                # 更新策略信息
                await self._update_agent_strategy(agent_id, strategy_info)
                
        except Exception as e:
            self.logger.error(f"处理策略更新消息失败: {e}")
    
    async def _handle_strategy_performance_update(self, message: Message):
        """处理策略性能更新消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            performance_data = payload.get("performance")
            
            if agent_id and agent_id in self._agent_strategies:
                # 更新策略的实时性能指标
                live_metrics = await self._parse_live_metrics(performance_data)
                self._agent_strategies[agent_id].live_metrics = live_metrics
                self._agent_strategies[agent_id].last_updated = datetime.utcnow()
                
        except Exception as e:
            self.logger.error(f"处理策略性能更新消息失败: {e}")
    
    async def _handle_backtest_result(self, message: Message):
        """处理回测结果消息"""
        try:
            payload = message.payload
            agent_id = payload.get("agent_id")
            backtest_data = payload.get("backtest")
            
            if agent_id and agent_id in self._agent_strategies:
                # 更新策略的回测指标
                backtest_metrics = await self._parse_backtest_metrics(backtest_data)
                self._agent_strategies[agent_id].backtest_metrics = backtest_metrics
                self._agent_strategies[agent_id].last_backtest = datetime.utcnow()
                
        except Exception as e:
            self.logger.error(f"处理回测结果消息失败: {e}")
    
    async def _background_update_loop(self):
        """后台策略数据更新循环"""
        while self._running:
            try:
                # 获取所有Agent ID
                agent_statuses = await self.coordinator.get_all_agent_statuses()
                
                # 更新每个Agent的策略信息
                for agent_id in agent_statuses.keys():
                    await self._update_agent_strategy_data(agent_id)
                
                # 等待下次更新
                await asyncio.sleep(self.config.update_interval)
                
            except Exception as e:
                self.logger.error(f"后台策略更新循环错误: {e}")
                await asyncio.sleep(self.config.update_interval)
    
    async def _update_agent_strategy_data(self, agent_id: str):
        """更新指定Agent的策略数据"""
        try:
            # 检查缓存是否过期
            if agent_id in self._last_update:
                cache_age = datetime.utcnow() - self._last_update[agent_id]
                if cache_age.total_seconds() < self.config.cache_ttl:
                    return  # 缓存未过期，跳过更新
            
            # 根据Agent类型获取策略信息
            agent_status = await self.coordinator.get_agent_status(agent_id)
            if not agent_status:
                return
            
            agent_type = agent_status.get("agent_type", "")
            
            # 获取对应Agent类型的策略信息
            strategy_info = await self._get_agent_strategy_info(agent_id, agent_type)
            
            if strategy_info:
                await self._update_agent_strategy(agent_id, strategy_info)
                
        except Exception as e:
            self.logger.error(f"更新Agent策略数据失败 {agent_id}: {e}")
    
    async def _get_agent_strategy_info(self, agent_id: str, agent_type: str) -> Optional[StrategyInfo]:
        """根据Agent类型获取策略信息"""
        try:
            # 根据不同的Agent类型获取相应的策略信息
            if "QuantitativeAnalyst" in agent_type:
                return await self._get_quantitative_analyst_strategy(agent_id)
            elif "QuantitativeTrader" in agent_type:
                return await self._get_quantitative_trader_strategy(agent_id)
            elif "PortfolioManager" in agent_type:
                return await self._get_portfolio_manager_strategy(agent_id)
            elif "DataScientist" in agent_type:
                return await self._get_data_scientist_strategy(agent_id)
            elif "RiskAnalyst" in agent_type:
                return await self._get_risk_analyst_strategy(agent_id)
            else:
                # 默认策略信息
                return await self._get_default_strategy_info(agent_id, agent_type)
                
        except Exception as e:
            self.logger.error(f"获取Agent策略信息失败 {agent_id}: {e}")
            return None
    
    async def _get_quantitative_analyst_strategy(self, agent_id: str) -> StrategyInfo:
        """获取量化分析师的策略信息"""
        return StrategyInfo(
            strategy_id=f"qa_strategy_{agent_id}",
            strategy_name="技术分析策略",
            strategy_type=StrategyType.TREND_FOLLOWING,
            status=StrategyStatus.ACTIVE,
            description="基于技术指标的趋势跟踪策略",
            parameters=[
                StrategyParameter(
                    name="sma_short_period",
                    value=20,
                    type="number",
                    description="短期移动平均线周期",
                    min_value=5,
                    max_value=50
                ),
                StrategyParameter(
                    name="sma_long_period",
                    value=50,
                    type="number", 
                    description="长期移动平均线周期",
                    min_value=20,
                    max_value=200
                ),
                StrategyParameter(
                    name="rsi_threshold",
                    value=70,
                    type="number",
                    description="RSI超买超卖阈值",
                    min_value=50,
                    max_value=90
                )
            ],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="medium",
            max_position_size=0.15
        )
    
    async def _get_quantitative_trader_strategy(self, agent_id: str) -> StrategyInfo:
        """获取量化交易员的策略信息"""
        return StrategyInfo(
            strategy_id=f"qt_strategy_{agent_id}",
            strategy_name="高频交易策略",
            strategy_type=StrategyType.MARKET_MAKING,
            status=StrategyStatus.ACTIVE,
            description="基于市场微观结构的高频交易策略",
            parameters=[
                StrategyParameter(
                    name="order_size",
                    value=1000,
                    type="number",
                    description="单笔订单大小",
                    min_value=100,
                    max_value=10000
                ),
                StrategyParameter(
                    name="spread_threshold",
                    value=0.01,
                    type="number",
                    description="最小价差阈值",
                    min_value=0.001,
                    max_value=0.1
                ),
                StrategyParameter(
                    name="max_positions",
                    value=5,
                    type="number",
                    description="最大持仓数量",
                    min_value=1,
                    max_value=20
                )
            ],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="high",
            max_position_size=0.05
        )
    
    async def _get_portfolio_manager_strategy(self, agent_id: str) -> StrategyInfo:
        """获取投资组合经理的策略信息"""
        return StrategyInfo(
            strategy_id=f"pm_strategy_{agent_id}",
            strategy_name="多因子投资组合策略",
            strategy_type=StrategyType.STATISTICAL_ARBITRAGE,
            status=StrategyStatus.ACTIVE,
            description="基于多因子模型的投资组合优化策略",
            parameters=[
                StrategyParameter(
                    name="rebalance_frequency",
                    value="weekly",
                    type="string",
                    description="再平衡频率",
                    options=["daily", "weekly", "monthly"]
                ),
                StrategyParameter(
                    name="target_volatility",
                    value=0.12,
                    type="number",
                    description="目标波动率",
                    min_value=0.05,
                    max_value=0.30
                ),
                StrategyParameter(
                    name="max_weight",
                    value=0.20,
                    type="number",
                    description="单只股票最大权重",
                    min_value=0.01,
                    max_value=0.50
                )
            ],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="medium",
            max_position_size=0.25
        )
    
    async def _get_data_scientist_strategy(self, agent_id: str) -> StrategyInfo:
        """获取数据科学家的策略信息"""
        return StrategyInfo(
            strategy_id=f"ds_strategy_{agent_id}",
            strategy_name="机器学习预测策略",
            strategy_type=StrategyType.MACHINE_LEARNING,
            status=StrategyStatus.ACTIVE,
            description="基于机器学习的股票价格预测策略",
            parameters=[
                StrategyParameter(
                    name="model_type",
                    value="LSTM",
                    type="string",
                    description="模型类型",
                    options=["LSTM", "RandomForest", "XGBoost", "Transformer"]
                ),
                StrategyParameter(
                    name="lookback_days",
                    value=60,
                    type="number",
                    description="回望天数",
                    min_value=10,
                    max_value=252
                ),
                StrategyParameter(
                    name="prediction_horizon",
                    value=5,
                    type="number",
                    description="预测时间跨度（天）",
                    min_value=1,
                    max_value=30
                )
            ],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="high",
            max_position_size=0.10
        )
    
    async def _get_risk_analyst_strategy(self, agent_id: str) -> StrategyInfo:
        """获取风险分析师的策略信息"""
        return StrategyInfo(
            strategy_id=f"ra_strategy_{agent_id}",
            strategy_name="风险控制策略",
            strategy_type=StrategyType.MEAN_REVERSION,
            status=StrategyStatus.ACTIVE,
            description="基于风险指标的对冲和风险控制策略",
            parameters=[
                StrategyParameter(
                    name="var_threshold",
                    value=0.02,
                    type="number",
                    description="VaR阈值",
                    min_value=0.005,
                    max_value=0.05
                ),
                StrategyParameter(
                    name="correlation_threshold",
                    value=0.7,
                    type="number",
                    description="相关性阈值",
                    min_value=0.3,
                    max_value=0.95
                ),
                StrategyParameter(
                    name="hedge_ratio",
                    value=0.8,
                    type="number",
                    description="对冲比例",
                    min_value=0.1,
                    max_value=1.0
                )
            ],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="low",
            max_position_size=0.30
        )
    
    async def _get_default_strategy_info(self, agent_id: str, agent_type: str) -> StrategyInfo:
        """获取默认策略信息"""
        return StrategyInfo(
            strategy_id=f"default_strategy_{agent_id}",
            strategy_name=f"{agent_type}默认策略",
            strategy_type=StrategyType.MOMENTUM,
            status=StrategyStatus.ACTIVE,
            description=f"{agent_type}的默认交易策略",
            parameters=[],
            version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            risk_level="medium",
            max_position_size=0.10
        )
    
    async def _parse_strategy_data(self, strategy_data: Dict[str, Any]) -> StrategyInfo:
        """解析策略数据"""
        try:
            return StrategyInfo(
                strategy_id=strategy_data.get("strategy_id", ""),
                strategy_name=strategy_data.get("strategy_name", ""),
                strategy_type=StrategyType(strategy_data.get("strategy_type", "momentum")),
                status=StrategyStatus(strategy_data.get("status", "active")),
                description=strategy_data.get("description"),
                parameters=[
                    StrategyParameter(**param) for param in strategy_data.get("parameters", [])
                ],
                version=strategy_data.get("version", "1.0.0"),
                created_at=datetime.fromisoformat(strategy_data.get("created_at", datetime.utcnow().isoformat())),
                last_updated=datetime.fromisoformat(strategy_data.get("last_updated", datetime.utcnow().isoformat())),
                risk_level=strategy_data.get("risk_level", "medium"),
                max_position_size=strategy_data.get("max_position_size", 0.1)
            )
        except Exception as e:
            self.logger.error(f"解析策略数据失败: {e}")
            return await self._get_default_strategy_info("unknown", "Unknown")
    
    async def _parse_live_metrics(self, performance_data: Dict[str, Any]) -> LiveMetrics:
        """解析实时性能指标"""
        try:
            return LiveMetrics(
                current_return=performance_data.get("current_return", 0.0),
                daily_pnl=performance_data.get("daily_pnl", 0.0),
                unrealized_pnl=performance_data.get("unrealized_pnl", 0.0),
                realized_pnl=performance_data.get("realized_pnl", 0.0),
                current_drawdown=performance_data.get("current_drawdown", 0.0),
                positions_count=performance_data.get("positions_count", 0),
                exposure_ratio=performance_data.get("exposure_ratio", 0.0),
                last_trade_time=datetime.fromisoformat(performance_data["last_trade_time"]) if performance_data.get("last_trade_time") else None,
                live_period_start=datetime.fromisoformat(performance_data.get("live_period_start", datetime.utcnow().isoformat()))
            )
        except Exception as e:
            self.logger.error(f"解析实时性能指标失败: {e}")
            return LiveMetrics(
                current_return=0.0,
                daily_pnl=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                current_drawdown=0.0,
                positions_count=0,
                exposure_ratio=0.0,
                live_period_start=datetime.utcnow()
            )
    
    async def _parse_backtest_metrics(self, backtest_data: Dict[str, Any]) -> BacktestMetrics:
        """解析回测指标"""
        try:
            return BacktestMetrics(
                total_return=backtest_data.get("total_return", 0.0),
                annualized_return=backtest_data.get("annualized_return", 0.0),
                volatility=backtest_data.get("volatility", 0.0),
                sharpe_ratio=backtest_data.get("sharpe_ratio", 0.0),
                max_drawdown=backtest_data.get("max_drawdown", 0.0),
                win_rate=backtest_data.get("win_rate", 0.0),
                profit_factor=backtest_data.get("profit_factor", 0.0),
                trades_count=backtest_data.get("trades_count", 0),
                avg_trade_duration=backtest_data.get("avg_trade_duration", 0.0),
                backtest_period_start=datetime.fromisoformat(backtest_data.get("backtest_period_start", "2023-01-01")).date(),
                backtest_period_end=datetime.fromisoformat(backtest_data.get("backtest_period_end", "2023-12-31")).date(),
                benchmark_return=backtest_data.get("benchmark_return"),
                alpha=backtest_data.get("alpha"),
                beta=backtest_data.get("beta"),
                information_ratio=backtest_data.get("information_ratio")
            )
        except Exception as e:
            self.logger.error(f"解析回测指标失败: {e}")
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
                backtest_period_end=datetime.now().date()
            )
    
    async def _update_agent_strategy(self, agent_id: str, strategy_info: StrategyInfo):
        """更新Agent的策略信息"""
        try:
            # 检查策略是否有变化
            if agent_id in self._agent_strategies:
                old_strategy = self._agent_strategies[agent_id]
                if old_strategy.strategy_id != strategy_info.strategy_id:
                    # 策略发生变化，记录历史
                    await self._add_strategy_to_history(agent_id, old_strategy)
            
            # 更新当前策略
            self._agent_strategies[agent_id] = strategy_info
            self._last_update[agent_id] = datetime.utcnow()
            
            # 通知回调函数
            for callback in self._update_callbacks:
                try:
                    callback(agent_id, strategy_info)
                except Exception as e:
                    self.logger.error(f"执行策略更新回调失败: {e}")
                    
        except Exception as e:
            self.logger.error(f"更新Agent策略失败 {agent_id}: {e}")
    
    async def _add_strategy_to_history(self, agent_id: str, strategy_info: StrategyInfo):
        """添加策略到历史记录"""
        try:
            if agent_id not in self._strategy_history:
                self._strategy_history[agent_id] = []
            
            self._strategy_history[agent_id].append(strategy_info)
            
            # 限制历史记录数量
            if len(self._strategy_history[agent_id]) > self.config.max_strategy_history:
                self._strategy_history[agent_id] = self._strategy_history[agent_id][-self.config.max_strategy_history:]
                
        except Exception as e:
            self.logger.error(f"添加策略历史记录失败 {agent_id}: {e}")
    
    async def get_agent_strategy(self, agent_id: str) -> Optional[StrategyInfo]:
        """获取指定Agent的策略信息"""
        try:
            # 检查缓存
            if agent_id in self._agent_strategies:
                return self._agent_strategies[agent_id]
            
            # 如果缓存中没有，立即更新
            await self._update_agent_strategy_data(agent_id)
            return self._agent_strategies.get(agent_id)
            
        except Exception as e:
            self.logger.error(f"获取Agent策略信息失败 {agent_id}: {e}")
            return None
    
    async def get_all_strategies(self) -> Dict[str, StrategyInfo]:
        """获取所有Agent的策略信息"""
        try:
            # 获取所有Agent ID
            agent_statuses = await self.coordinator.get_all_agent_statuses()
            
            # 确保所有Agent的策略信息都已更新
            for agent_id in agent_statuses.keys():
                if agent_id not in self._agent_strategies:
                    await self._update_agent_strategy_data(agent_id)
            
            return self._agent_strategies.copy()
            
        except Exception as e:
            self.logger.error(f"获取所有策略信息失败: {e}")
            return {}
    
    async def get_strategy_history(self, agent_id: str) -> List[StrategyInfo]:
        """获取Agent的策略历史记录"""
        try:
            return self._strategy_history.get(agent_id, [])
        except Exception as e:
            self.logger.error(f"获取策略历史记录失败 {agent_id}: {e}")
            return []
    
    async def get_strategies_by_type(self, strategy_type: StrategyType) -> List[StrategyInfo]:
        """根据策略类型获取策略列表"""
        try:
            all_strategies = await self.get_all_strategies()
            return [strategy for strategy in all_strategies.values() if strategy.strategy_type == strategy_type]
        except Exception as e:
            self.logger.error(f"根据类型获取策略失败 {strategy_type}: {e}")
            return []
    
    def add_update_callback(self, callback: Callable[[str, StrategyInfo], None]):
        """添加策略更新回调函数"""
        self._update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable[[str, StrategyInfo], None]):
        """移除策略更新回调函数"""
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
    
    async def cleanup(self):
        """清理资源"""
        try:
            self.logger.info("正在清理策略数据服务...")
            
            self._running = False
            
            if self._update_task:
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass
            
            # 清理缓存
            self._agent_strategies.clear()
            self._strategy_history.clear()
            self._last_update.clear()
            self._update_callbacks.clear()
            
            self.logger.info("策略数据服务清理完成")
            
        except Exception as e:
            self.logger.error(f"清理策略数据服务失败: {e}")


__all__ = [
    "StrategyDataConfig",
    "StrategyDataService",
]
