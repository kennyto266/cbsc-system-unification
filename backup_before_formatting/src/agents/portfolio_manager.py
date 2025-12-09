"""
港股量化交易 AI Agent 系统 - 投资组合经理Agent

负责构建投资组合、管理资产配置、监控绩效和风险暴露。
提供专业的投资组合管理能力，追求最优的风险调整收益。
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.optimize as opt
from scipy.stats import norm

from ..agents.base_agent import AgentConfig, BaseAgent
from ..agents.protocol import AgentProtocol, MessagePriority, MessageType
from ..core import SystemConfig, SystemConstants
from ..core.message_queue import Message, MessageQueue
from ..models.base import (
    BaseModel,
    Holding,
    MarketData,
    PerformanceMetrics,
    Portfolio,
    RiskMetrics,
    SignalType,
    TradingSignal,
)


class RebalancingFrequency(str, Enum):
    """再平衡频率"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class OptimizationMethod(str, Enum):
    """优化方法"""

    MEAN_VARIANCE = "mean_variance"
    RISK_PARITY = "risk_parity"
    MINIMUM_VARIANCE = "minimum_variance"
    MAXIMUM_SHARPE = "maximum_sharpe"
    BLACK_LITTERMAN = "black_litterman"


@dataclass
class AssetAllocation(BaseModel):
    """资产配置"""

    symbol: str
    target_weight: float
    current_weight: float
    market_value: float
    expected_return: float
    volatility: float
    beta: float
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RebalancingSignal(BaseModel):
    """再平衡信号"""

    symbol: str
    current_weight: float
    target_weight: float
    weight_change: float
    rebalancing_amount: float
    signal_type: str  # 'buy' or 'sell'
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioConstraints(BaseModel):
    """投资组合约束"""

    max_weight: float = 0.1  # 单个资产最大权重
    min_weight: float = 0.01  # 单个资产最小权重
    max_sector_weight: float = 0.3  # 单个行业最大权重
    max_turnover: float = 0.2  # 最大换手率
    min_liquidity: float = 1000000.0  # 最小流动性要求
    max_leverage: float = 1.0  # 最大杠杆倍数
    risk_budget: float = 0.02  # 风险预算


class PortfolioOptimizer:
    """投资组合优化器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.portfolio_manager.optimizer")

    def optimize_portfolio(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        method: OptimizationMethod = OptimizationMethod.MAXIMUM_SHARPE,
        constraints: Optional[PortfolioConstraints] = None,
        risk_free_rate: float = 0.03,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """优化投资组合"""

        try:
            n_assets = len(expected_returns)

            if method == OptimizationMethod.MAXIMUM_SHARPE:
                return self._maximize_sharpe_ratio(
                    expected_returns, covariance_matrix, constraints, risk_free_rate
                )
            elif method == OptimizationMethod.MINIMUM_VARIANCE:
                return self._minimize_variance(
                    expected_returns, covariance_matrix, constraints
                )
            elif method == OptimizationMethod.RISK_PARITY:
                return self._risk_parity_optimization(
                    expected_returns, covariance_matrix, constraints
                )
            elif method == OptimizationMethod.MEAN_VARIANCE:
                return self._mean_variance_optimization(
                    expected_returns, covariance_matrix, constraints
                )
            else:
                raise ValueError(f"不支持的优化方法: {method}")

        except Exception as e:
            self.logger.error(f"投资组合优化失败: {e}")
            # 返回等权重组合作为默认值
            equal_weights = np.ones(n_assets) / n_assets
            return equal_weights, {"error": str(e)}

    def _maximize_sharpe_ratio(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Optional[PortfolioConstraints],
        risk_free_rate: float,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """最大化夏普比率"""

        n_assets = len(expected_returns)

        # 定义目标函数（负夏普比率，因为要最大化）
        def negative_sharpe_ratio(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)

            if portfolio_volatility == 0:
                return -np.inf

            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
            return -sharpe_ratio

        # 约束条件
        constraints_list = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}  # 权重和为1
        ]

        # 添加权重约束
        if constraints:
            bounds = [
                (constraints.min_weight, constraints.max_weight)
                for _ in range(n_assets)
            ]
        else:
            bounds = [(0.0, 1.0) for _ in range(n_assets)]

        # 初始权重（等权重）
        x0 = np.ones(n_assets) / n_assets

        # 优化
        result = opt.minimize(
            negative_sharpe_ratio,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
            options={"ftol": 1e-9, "disp": False},
        )

        if result.success:
            optimal_weights = result.x
            portfolio_return = np.dot(optimal_weights, expected_returns)
            portfolio_variance = np.dot(
                optimal_weights, np.dot(covariance_matrix, optimal_weights)
            )
            portfolio_volatility = np.sqrt(portfolio_variance)
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility

            metrics = {
                "portfolio_return": portfolio_return,
                "portfolio_volatility": portfolio_volatility,
                "sharpe_ratio": sharpe_ratio,
                "optimization_success": True,
            }
        else:
            # 如果优化失败，返回等权重
            optimal_weights = x0
            metrics = {"optimization_success": False, "error": result.message}

        return optimal_weights, metrics

    def _minimize_variance(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Optional[PortfolioConstraints],
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """最小化方差"""

        n_assets = len(expected_returns)

        # 定义目标函数（方差）
        def portfolio_variance(weights):
            return np.dot(weights, np.dot(covariance_matrix, weights))

        # 约束条件
        constraints_list = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # 权重边界
        if constraints:
            bounds = [
                (constraints.min_weight, constraints.max_weight)
                for _ in range(n_assets)
            ]
        else:
            bounds = [(0.0, 1.0) for _ in range(n_assets)]

        # 初始权重
        x0 = np.ones(n_assets) / n_assets

        # 优化
        result = opt.minimize(
            portfolio_variance,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
        )

        if result.success:
            optimal_weights = result.x
            portfolio_variance = result.fun
            portfolio_volatility = np.sqrt(portfolio_variance)
            portfolio_return = np.dot(optimal_weights, expected_returns)

            metrics = {
                "portfolio_return": portfolio_return,
                "portfolio_volatility": portfolio_volatility,
                "portfolio_variance": portfolio_variance,
                "optimization_success": True,
            }
        else:
            optimal_weights = x0
            metrics = {"optimization_success": False, "error": result.message}

        return optimal_weights, metrics

    def _risk_parity_optimization(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Optional[PortfolioConstraints],
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """风险平价优化"""

        n_assets = len(expected_returns)

        # 定义目标函数（风险贡献的方差）
        def risk_parity_objective(weights):
            portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))
            risk_contributions = weights * np.dot(covariance_matrix, weights)
            risk_contributions = risk_contributions / portfolio_variance

            # 计算风险贡献的方差
            target_contribution = 1.0 / n_assets
            variance_of_contributions = np.sum(
                (risk_contributions - target_contribution) ** 2
            )

            return variance_of_contributions

        # 约束条件
        constraints_list = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # 权重边界
        if constraints:
            bounds = [
                (constraints.min_weight, constraints.max_weight)
                for _ in range(n_assets)
            ]
        else:
            bounds = [(0.0, 1.0) for _ in range(n_assets)]

        # 初始权重
        x0 = np.ones(n_assets) / n_assets

        # 优化
        result = opt.minimize(
            risk_parity_objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
        )

        if result.success:
            optimal_weights = result.x
            portfolio_return = np.dot(optimal_weights, expected_returns)
            portfolio_variance = np.dot(
                optimal_weights, np.dot(covariance_matrix, optimal_weights)
            )
            portfolio_volatility = np.sqrt(portfolio_variance)

            metrics = {
                "portfolio_return": portfolio_return,
                "portfolio_volatility": portfolio_volatility,
                "risk_parity_variance": result.fun,
                "optimization_success": True,
            }
        else:
            optimal_weights = x0
            metrics = {"optimization_success": False, "error": result.message}

        return optimal_weights, metrics

    def _mean_variance_optimization(
        self,
        expected_returns: np.ndarray,
        covariance_matrix: np.ndarray,
        constraints: Optional[PortfolioConstraints],
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """均值方差优化"""

        n_assets = len(expected_returns)

        # 定义目标函数（负期望收益 + 风险惩罚）
        def mean_variance_objective(weights):
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_variance = np.dot(weights, np.dot(covariance_matrix, weights))

            # 风险厌恶系数
            risk_aversion = 1.0
            return -(portfolio_return - risk_aversion * portfolio_variance)

        # 约束条件
        constraints_list = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        # 权重边界
        if constraints:
            bounds = [
                (constraints.min_weight, constraints.max_weight)
                for _ in range(n_assets)
            ]
        else:
            bounds = [(0.0, 1.0) for _ in range(n_assets)]

        # 初始权重
        x0 = np.ones(n_assets) / n_assets

        # 优化
        result = opt.minimize(
            mean_variance_objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
        )

        if result.success:
            optimal_weights = result.x
            portfolio_return = np.dot(optimal_weights, expected_returns)
            portfolio_variance = np.dot(
                optimal_weights, np.dot(covariance_matrix, optimal_weights)
            )
            portfolio_volatility = np.sqrt(portfolio_variance)

            metrics = {
                "portfolio_return": portfolio_return,
                "portfolio_volatility": portfolio_volatility,
                "portfolio_variance": portfolio_variance,
                "optimization_success": True,
            }
        else:
            optimal_weights = x0
            metrics = {"optimization_success": False, "error": result.message}

        return optimal_weights, metrics


class PerformanceAnalyzer:
    """绩效分析器"""

    def __init__(self):
        self.logger = logging.getLogger(
            "hk_quant_system.portfolio_manager.performance_analyzer"
        )

    def calculate_performance_metrics(
        self,
        portfolio_values: List[float],
        benchmark_values: Optional[List[float]] = None,
        risk_free_rate: float = 0.03,
    ) -> PerformanceMetrics:
        """计算绩效指标"""

        try:
            if len(portfolio_values) < 2:
                return PerformanceMetrics()

            # 转换为numpy数组
            portfolio_array = np.array(portfolio_values)

            # 计算收益率
            returns = np.diff(portfolio_array) / portfolio_array[:-1]

            # 基础统计
            total_return = (portfolio_array[-1] - portfolio_array[0]) / portfolio_array[
                0
            ]

            # 年化收益率
            days = len(portfolio_array)
            years = days / 252  # 假设一年252个交易日
            annualized_return = (
                (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0
            )

            # 波动率
            volatility = np.std(returns) * np.sqrt(252)

            # 夏普比率
            sharpe_ratio = (
                (annualized_return - risk_free_rate) / volatility
                if volatility > 0
                else 0.0
            )

            # 最大回撤
            max_drawdown = self._calculate_max_drawdown(portfolio_array)

            # 胜率
            win_rate = np.mean(returns > 0) if len(returns) > 0 else 0.0

            # 基准比较
            tracking_error = 0.0
            information_ratio = 0.0
            if benchmark_values and len(benchmark_values) == len(portfolio_values):
                benchmark_array = np.array(benchmark_values)
                benchmark_returns = np.diff(benchmark_array) / benchmark_array[:-1]

                # 跟踪误差
                excess_returns = returns - benchmark_returns
                tracking_error = np.std(excess_returns) * np.sqrt(252)

                # 信息比率
                information_ratio = (
                    np.mean(excess_returns) / np.std(excess_returns)
                    if np.std(excess_returns) > 0
                    else 0.0
                )

            return PerformanceMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=0.0,  # 需要更复杂的计算
                start_date=datetime.now() - timedelta(days=days),
                end_date=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"计算绩效指标失败: {e}")
            return PerformanceMetrics()

    def _calculate_max_drawdown(self, portfolio_values: np.ndarray) -> float:
        """计算最大回撤"""
        peak = portfolio_values[0]
        max_dd = 0.0

        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)

        return max_dd


class RebalancingEngine:
    """再平衡引擎"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.portfolio_manager.rebalancing")

    def calculate_rebalancing_signals(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        portfolio_value: float,
        constraints: Optional[PortfolioConstraints] = None,
    ) -> List[RebalancingSignal]:
        """计算再平衡信号"""

        signals = []

        try:
            # 获取所有资产
            all_symbols = set(current_weights.keys()) | set(target_weights.keys())

            for symbol in all_symbols:
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_weights.get(symbol, 0.0)

                # 计算权重变化
                weight_change = target_weight - current_weight

                # 检查是否需要再平衡
                rebalancing_threshold = 0.005  # 0.5 % 的阈值

                if abs(weight_change) > rebalancing_threshold:
                    # 计算再平衡金额
                    rebalancing_amount = weight_change * portfolio_value

                    # 确定信号类型
                    signal_type = "buy" if weight_change > 0 else "sell"

                    # 计算优先级（基于权重变化幅度）
                    priority = int(abs(weight_change) * 1000)

                    signal = RebalancingSignal(
                        symbol=symbol,
                        current_weight=current_weight,
                        target_weight=target_weight,
                        weight_change=weight_change,
                        rebalancing_amount=abs(rebalancing_amount),
                        signal_type=signal_type,
                        priority=priority,
                    )

                    signals.append(signal)

            # 按优先级排序
            signals.sort(key=lambda x: x.priority, reverse=True)

        except Exception as e:
            self.logger.error(f"计算再平衡信号失败: {e}")

        return signals

    def should_rebalance(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        frequency: RebalancingFrequency,
        last_rebalance: datetime,
        drift_threshold: float = 0.05,
    ) -> bool:
        """判断是否需要再平衡"""

        try:
            # 检查时间频率
            now = datetime.now()

            if frequency == RebalancingFrequency.DAILY:
                time_threshold = timedelta(days=1)
            elif frequency == RebalancingFrequency.WEEKLY:
                time_threshold = timedelta(weeks=1)
            elif frequency == RebalancingFrequency.MONTHLY:
                time_threshold = timedelta(days=30)
            elif frequency == RebalancingFrequency.QUARTERLY:
                time_threshold = timedelta(days=90)
            else:
                time_threshold = timedelta(days=1)

            # 检查时间是否到达
            if now - last_rebalance < time_threshold:
                return False

            # 检查权重漂移
            total_drift = 0.0
            all_symbols = set(current_weights.keys()) | set(target_weights.keys())

            for symbol in all_symbols:
                current_weight = current_weights.get(symbol, 0.0)
                target_weight = target_weights.get(symbol, 0.0)
                drift = abs(current_weight - target_weight)
                total_drift += drift

            # 如果总漂移超过阈值，需要再平衡
            return total_drift > drift_threshold

        except Exception as e:
            self.logger.error(f"判断再平衡需求失败: {e}")
            return False


class PortfolioManagerAgent(BaseAgent):
    """投资组合经理Agent"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        super().__init__(config, message_queue, system_config)

        # 初始化组件
        self.optimizer = PortfolioOptimizer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.rebalancing_engine = RebalancingEngine()

        # 投资组合数据
        self.current_portfolio: Optional[Portfolio] = None
        self.target_allocation: Dict[str, AssetAllocation] = {}
        self.performance_history: List[PerformanceMetrics] = []

        # 配置参数
        self.rebalancing_frequency = RebalancingFrequency.WEEKLY
        self.optimization_method = OptimizationMethod.MAXIMUM_SHARPE
        self.constraints = PortfolioConstraints()

        # 市场数据缓存
        self.market_data_cache: Dict[str, pd.DataFrame] = {}
        self.price_data: Dict[str, float] = {}

        # 协议
        self.protocol = AgentProtocol(config.agent_id, message_queue)

    async def initialize(self) -> bool:
        """初始化Agent"""
        try:
            # 初始化协议
            await self.protocol.initialize()

            # 注册消息处理器
            self.protocol.register_handler(MessageType.DATA, self._handle_market_data)
            self.protocol.register_handler(
                MessageType.SIGNAL, self._handle_trading_signal
            )
            self.protocol.register_handler(
                MessageType.CONTROL, self._handle_portfolio_control
            )

            # 初始化默认投资组合
            await self._initialize_default_portfolio()

            self.logger.info(f"投资组合经理Agent初始化成功: {self.config.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"投资组合经理Agent初始化失败: {e}")
            return False

    async def process_message(self, message: Message) -> bool:
        """处理消息"""
        try:
            await self.protocol.handle_incoming_message(message)
            return True

        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        self.logger.info("清理投资组合经理Agent资源")

        # 保存投资组合状态
        await self._save_portfolio_state()

    async def _handle_market_data(self, protocol_message):
        """处理市场数据"""
        try:
            data_type = protocol_message.payload.get("data_type")
            data = protocol_message.payload.get("data", {})

            if data_type == "market_data":
                symbol = data.get("symbol")
                market_data = data.get("market_data")

                if symbol and market_data:
                    await self._process_market_data(symbol, market_data)

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _handle_trading_signal(self, protocol_message):
        """处理交易信号"""
        try:
            signal_type = protocol_message.payload.get("signal_type")
            symbol = protocol_message.payload.get("symbol")
            confidence = protocol_message.payload.get("confidence", 0.0)

            # 根据信号调整目标配置
            if confidence >= 0.7:  # 高置信度信号
                await self._adjust_target_allocation(symbol, signal_type, confidence)

        except Exception as e:
            self.logger.error(f"处理交易信号失败: {e}")

    async def _handle_portfolio_control(self, protocol_message):
        """处理投资组合控制消息"""
        try:
            command = protocol_message.payload.get("command")
            parameters = protocol_message.payload.get("parameters", {})

            if command == "optimize_portfolio":
                await self._optimize_portfolio()

            elif command == "rebalance_portfolio":
                await self._rebalance_portfolio()

            elif command == "update_constraints":
                new_constraints = parameters.get("constraints", {})
                self._update_constraints(new_constraints)

            elif command == "set_rebalancing_frequency":
                frequency = parameters.get("frequency", "weekly")
                self.rebalancing_frequency = RebalancingFrequency(frequency)

        except Exception as e:
            self.logger.error(f"处理投资组合控制消息失败: {e}")

    async def _process_market_data(self, symbol: str, market_data: Dict[str, Any]):
        """处理市场数据"""
        try:
            # 更新价格数据
            self.price_data[symbol] = market_data["close_price"]

            # 转换为DataFrame格式
            df_data = {
                "timestamp": [datetime.fromisoformat(market_data["timestamp"])],
                "open": [market_data["open_price"]],
                "high": [market_data["high_price"]],
                "low": [market_data["low_price"]],
                "close": [market_data["close_price"]],
                "volume": [market_data["volume"]],
            }

            new_row = pd.DataFrame(df_data)

            # 更新缓存数据
            if symbol in self.market_data_cache:
                self.market_data_cache[symbol] = pd.concat(
                    [self.market_data_cache[symbol], new_row], ignore_index=True
                )
            else:
                self.market_data_cache[symbol] = new_row

            # 保持最近252个数据点（一年）
            if len(self.market_data_cache[symbol]) > 252:
                self.market_data_cache[symbol] = self.market_data_cache[symbol].tail(
                    252
                )

            # 更新投资组合价值
            await self._update_portfolio_value()

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _initialize_default_portfolio(self):
        """初始化默认投资组合"""
        try:
            # 创建默认投资组合
            self.current_portfolio = Portfolio(
                portfolio_id=f"portfolio_{self.config.agent_id}",
                name="港股量化投资组合",
                total_value=1000000.0,  # 100万初始资金
                cash_balance=1000000.0,
                holdings=[],
                created_date=datetime.now(),
                target_allocation={},
                actual_allocation={},
            )

            self.logger.info("默认投资组合初始化完成")

        except Exception as e:
            self.logger.error(f"初始化默认投资组合失败: {e}")

    async def _optimize_portfolio(self):
        """优化投资组合"""
        try:
            if not self.price_data or len(self.price_data) < 10:
                self.logger.warning("数据不足，无法优化投资组合")
                return

            # 计算预期收益和协方差矩阵
            symbols = list(self.price_data.keys())
            expected_returns, covariance_matrix = await self._calculate_risk_metrics(
                symbols
            )

            # 优化投资组合
            optimal_weights, metrics = self.optimizer.optimize_portfolio(
                expected_returns,
                covariance_matrix,
                self.optimization_method,
                self.constraints,
            )

            # 更新目标配置
            for i, symbol in enumerate(symbols):
                allocation = AssetAllocation(
                    symbol=symbol,
                    target_weight=optimal_weights[i],
                    current_weight=0.0,  # 将在更新时计算
                    market_value=0.0,
                    expected_return=expected_returns[i],
                    volatility=np.sqrt(covariance_matrix[i, i]),
                    beta=1.0,  # 简化处理
                )
                self.target_allocation[symbol] = allocation

            # 广播优化结果
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "portfolio_optimization": {
                        "optimal_weights": dict(zip(symbols, optimal_weights)),
                        "metrics": metrics,
                        "timestamp": datetime.now().isoformat(),
                    }
                },
            )

            self.logger.info(f"投资组合优化完成: {metrics}")

        except Exception as e:
            self.logger.error(f"投资组合优化失败: {e}")

    async def _calculate_risk_metrics(
        self, symbols: List[str]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """计算风险指标"""
        try:
            n_assets = len(symbols)
            returns_data = []

            # 计算每个资产的收益率
            for symbol in symbols:
                if (
                    symbol in self.market_data_cache
                    and len(self.market_data_cache[symbol]) > 1
                ):
                    prices = self.market_data_cache[symbol]["close"].values
                    returns = np.diff(prices) / prices[:-1]
                    returns_data.append(returns)
                else:
                    # 如果没有足够数据，使用默认值
                    returns_data.append(np.random.normal(0.0005, 0.02, 100))

            # 确保所有收益率序列长度相同
            min_length = min(len(returns) for returns in returns_data)
            returns_matrix = np.array(
                [returns[:min_length] for returns in returns_data]
            )

            # 计算预期收益和协方差矩阵
            expected_returns = np.mean(returns_matrix, axis=1) * 252  # 年化
            covariance_matrix = np.cov(returns_matrix) * 252  # 年化

            return expected_returns, covariance_matrix

        except Exception as e:
            self.logger.error(f"计算风险指标失败: {e}")
            # 返回默认值
            n_assets = len(symbols)
            expected_returns = np.random.normal(0.05, 0.01, n_assets)
            covariance_matrix = np.eye(n_assets) * 0.04
            return expected_returns, covariance_matrix

    async def _rebalance_portfolio(self):
        """再平衡投资组合"""
        try:
            if not self.current_portfolio or not self.target_allocation:
                self.logger.warning("投资组合或目标配置为空，无法再平衡")
                return

            # 计算当前权重
            current_weights = await self._calculate_current_weights()
            target_weights = {
                symbol: allocation.target_weight
                for symbol, allocation in self.target_allocation.items()
            }

            # 检查是否需要再平衡
            last_rebalance = (
                self.current_portfolio.last_rebalanced
                or self.current_portfolio.created_date
            )
            should_rebalance = self.rebalancing_engine.should_rebalance(
                current_weights,
                target_weights,
                self.rebalancing_frequency,
                last_rebalance,
            )

            if not should_rebalance:
                self.logger.info("无需再平衡")
                return

            # 计算再平衡信号
            rebalancing_signals = self.rebalancing_engine.calculate_rebalancing_signals(
                current_weights,
                target_weights,
                self.current_portfolio.total_value,
                self.constraints,
            )

            # 执行再平衡
            for signal in rebalancing_signals:
                await self._execute_rebalancing_signal(signal)

            # 更新最后再平衡时间
            self.current_portfolio.last_rebalanced = datetime.now()

            # 广播再平衡结果
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "portfolio_rebalancing": {
                        "signals": [signal.__dict__ for signal in rebalancing_signals],
                        "timestamp": datetime.now().isoformat(),
                    }
                },
            )

            self.logger.info(f"投资组合再平衡完成: {len(rebalancing_signals)} 个信号")

        except Exception as e:
            self.logger.error(f"投资组合再平衡失败: {e}")

    async def _calculate_current_weights(self) -> Dict[str, float]:
        """计算当前权重"""
        try:
            if not self.current_portfolio:
                return {}

            weights = {}
            total_value = self.current_portfolio.total_value

            for holding in self.current_portfolio.holdings:
                if holding.symbol in self.price_data:
                    current_price = self.price_data[holding.symbol]
                    market_value = holding.quantity * current_price
                    weight = market_value / total_value if total_value > 0 else 0.0
                    weights[holding.symbol] = weight

            return weights

        except Exception as e:
            self.logger.error(f"计算当前权重失败: {e}")
            return {}

    async def _execute_rebalancing_signal(self, signal: RebalancingSignal):
        """执行再平衡信号"""
        try:
            # 发送交易信号给交易员
            await self.protocol.send_signal(
                signal_type=(
                    SignalType.BUY if signal.signal_type == "buy" else SignalType.SELL
                ),
                symbol=signal.symbol,
                confidence=0.9,  # 再平衡信号高置信度
                reasoning=f"投资组合再平衡: {signal.signal_type} {signal.rebalancing_amount:.2f}",
            )

            self.logger.info(f"执行再平衡信号: {signal.symbol} {signal.signal_type}")

        except Exception as e:
            self.logger.error(f"执行再平衡信号失败: {e}")

    async def _adjust_target_allocation(
        self, symbol: str, signal_type: str, confidence: float
    ):
        """调整目标配置"""
        try:
            if symbol not in self.target_allocation:
                return

            allocation = self.target_allocation[symbol]

            # 根据信号调整目标权重
            adjustment_factor = confidence * 0.1  # 最大10 % 的调整

            if signal_type == SignalType.BUY:
                new_weight = min(
                    allocation.target_weight + adjustment_factor,
                    self.constraints.max_weight,
                )
            else:
                new_weight = max(
                    allocation.target_weight - adjustment_factor,
                    self.constraints.min_weight,
                )

            allocation.target_weight = new_weight
            allocation.last_updated = datetime.now()

            self.logger.info(f"调整目标配置: {symbol} -> {new_weight:.3f}")

        except Exception as e:
            self.logger.error(f"调整目标配置失败: {e}")

    async def _update_portfolio_value(self):
        """更新投资组合价值"""
        try:
            if not self.current_portfolio:
                return

            total_value = self.current_portfolio.cash_balance

            for holding in self.current_portfolio.holdings:
                if holding.symbol in self.price_data:
                    current_price = self.price_data[holding.symbol]
                    market_value = holding.quantity * current_price
                    total_value += market_value

                    # 更新持仓信息
                    holding.market_value = market_value
                    holding.unrealized_pnl = market_value - (
                        holding.quantity * holding.average_cost
                    )

            self.current_portfolio.total_value = total_value

        except Exception as e:
            self.logger.error(f"更新投资组合价值失败: {e}")

    def _update_constraints(self, new_constraints: Dict[str, Any]):
        """更新约束条件"""
        try:
            for key, value in new_constraints.items():
                if hasattr(self.constraints, key):
                    setattr(self.constraints, key, value)

            self.logger.info("投资组合约束已更新")

        except Exception as e:
            self.logger.error(f"更新约束条件失败: {e}")

    async def _save_portfolio_state(self):
        """保存投资组合状态"""
        try:
            # 这里可以保存到数据库
            self.logger.info("投资组合状态已保存")

        except Exception as e:
            self.logger.error(f"保存投资组合状态失败: {e}")

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取投资组合摘要"""
        return {
            "agent_id": self.config.agent_id,
            "portfolio_value": (
                self.current_portfolio.total_value if self.current_portfolio else 0.0
            ),
            "cash_balance": (
                self.current_portfolio.cash_balance if self.current_portfolio else 0.0
            ),
            "holdings_count": (
                len(self.current_portfolio.holdings) if self.current_portfolio else 0
            ),
            "target_allocations": len(self.target_allocation),
            "rebalancing_frequency": self.rebalancing_frequency.value,
            "optimization_method": self.optimization_method.value,
            "cached_symbols": list(self.price_data.keys()),
            "protocol_stats": self.protocol.get_protocol_stats(),
        }


# 导出主要组件
__all__ = [
    "PortfolioManagerAgent",
    "PortfolioOptimizer",
    "PerformanceAnalyzer",
    "RebalancingEngine",
    "AssetAllocation",
    "RebalancingSignal",
    "PortfolioConstraints",
]
