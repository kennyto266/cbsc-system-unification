"""
港股量化交易 AI Agent 系统 - 风险分析师Agent

负责风险计算、监控、预警和控制。
提供全面的风险管理能力，包括VaR计算、压力测试、风险指标监控等。
"""

import asyncio
import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import scipy.stats as stats
from scipy.optimize import minimize

from ..agents.base_agent import AgentConfig, BaseAgent
from ..agents.protocol import AgentProtocol, MessagePriority, MessageType
from ..core import SystemConfig, SystemConstants
from ..core.message_queue import Message, MessageQueue
from ..models.base import BaseModel, MarketData, Portfolio, RiskMetrics, TradingSignal


class RiskLevel(str, Enum):
    """风险等级"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VaRMethod(str, Enum):
    """VaR计算方法"""

    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


class StressTestScenario(str, Enum):
    """压力测试情景"""

    MARKET_CRASH = "market_crash"
    INTEREST_RATE_SHOCK = "interest_rate_shock"
    CURRENCY_CRISIS = "currency_crisis"
    SECTOR_DECLINE = "sector_decline"
    LIQUIDITY_CRISIS = "liquidity_crisis"


@dataclass
class RiskAlert(BaseModel):
    """风险预警"""

    alert_id: str
    risk_type: str
    risk_level: RiskLevel
    symbol: Optional[str] = None
    portfolio_id: Optional[str] = None
    current_value: float = 0.0
    threshold_value: float = 0.0
    deviation: float = 0.0
    description: str = ""
    recommendation: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False


@dataclass
class StressTestResult(BaseModel):
    """压力测试结果"""

    scenario: StressTestScenario
    portfolio_loss: float
    loss_percentage: float
    var_impact: float
    expected_shortfall: float
    recovery_time_days: int
    worst_case_loss: float
    confidence_level: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskLimit(BaseModel):
    """风险限制"""

    risk_type: str
    limit_value: float
    current_value: float
    utilization: float  # 当前值 / 限制值的比例
    status: str  # 'safe', 'warning', 'breach'
    last_updated: datetime = field(default_factory=datetime.now)


class VaRCalculator:
    """VaR计算器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.risk_analyst.var_calculator")

    def calculate_var(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        method: VaRMethod = VaRMethod.HISTORICAL,
        holding_period: int = 1,
    ) -> Dict[str, float]:
        """计算VaR"""

        try:
            if len(returns) == 0:
                return {"var": 0.0, "expected_shortfall": 0.0}

            if method == VaRMethod.HISTORICAL:
                return self._historical_var(returns, confidence_level, holding_period)
            elif method == VaRMethod.PARAMETRIC:
                return self._parametric_var(returns, confidence_level, holding_period)
            elif method == VaRMethod.MONTE_CARLO:
                return self._monte_carlo_var(returns, confidence_level, holding_period)
            else:
                raise ValueError(f"不支持的VaR方法: {method}")

        except Exception as e:
            self.logger.error(f"VaR计算失败: {e}")
            return {"var": 0.0, "expected_shortfall": 0.0}

    def _historical_var(
        self, returns: np.ndarray, confidence_level: float, holding_period: int
    ) -> Dict[str, float]:
        """历史模拟法VaR"""

        # 调整持有期
        adjusted_returns = returns * np.sqrt(holding_period)

        # 计算VaR
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(adjusted_returns, var_percentile)

        # 计算期望损失（CVaR）
        var_threshold = var
        tail_returns = adjusted_returns[adjusted_returns <= var_threshold]
        expected_shortfall = np.mean(tail_returns) if len(tail_returns) > 0 else var

        return {
            "var": abs(var),
            "expected_shortfall": abs(expected_shortfall),
            "method": "historical",
        }

    def _parametric_var(
        self, returns: np.ndarray, confidence_level: float, holding_period: int
    ) -> Dict[str, float]:
        """参数法VaR"""

        # 计算统计参数
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # 调整持有期
        mean_return *= holding_period
        std_return *= np.sqrt(holding_period)

        # 计算VaR（假设正态分布）
        z_score = stats.norm.ppf(1 - confidence_level)
        var = abs(mean_return + z_score * std_return)

        # 计算期望损失
        expected_shortfall = abs(
            mean_return + std_return * stats.norm.pdf(z_score) / (1 - confidence_level)
        )

        return {
            "var": var,
            "expected_shortfall": expected_shortfall,
            "method": "parametric",
        }

    def _monte_carlo_var(
        self,
        returns: np.ndarray,
        confidence_level: float,
        holding_period: int,
        simulations: int = 10000,
    ) -> Dict[str, float]:
        """蒙特卡洛法VaR"""

        # 估计分布参数
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # 生成模拟收益
        simulated_returns = np.random.normal(mean_return, std_return, simulations)

        # 调整持有期
        simulated_returns *= np.sqrt(holding_period)

        # 计算VaR
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(simulated_returns, var_percentile)

        # 计算期望损失
        var_threshold = var
        tail_returns = simulated_returns[simulated_returns <= var_threshold]
        expected_shortfall = np.mean(tail_returns) if len(tail_returns) > 0 else var

        return {
            "var": abs(var),
            "expected_shortfall": abs(expected_shortfall),
            "method": "monte_carlo",
        }


class StressTester:
    """压力测试器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.risk_analyst.stress_tester")

    def run_stress_test(
        self,
        portfolio_holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        scenario: StressTestScenario,
        confidence_level: float = 0.95,
    ) -> StressTestResult:
        """运行压力测试"""

        try:
            if scenario == StressTestScenario.MARKET_CRASH:
                return self._market_crash_scenario(
                    portfolio_holdings, market_data, confidence_level
                )
            elif scenario == StressTestScenario.INTEREST_RATE_SHOCK:
                return self._interest_rate_shock_scenario(
                    portfolio_holdings, market_data, confidence_level
                )
            elif scenario == StressTestScenario.CURRENCY_CRISIS:
                return self._currency_crisis_scenario(
                    portfolio_holdings, market_data, confidence_level
                )
            elif scenario == StressTestScenario.SECTOR_DECLINE:
                return self._sector_decline_scenario(
                    portfolio_holdings, market_data, confidence_level
                )
            elif scenario == StressTestScenario.LIQUIDITY_CRISIS:
                return self._liquidity_crisis_scenario(
                    portfolio_holdings, market_data, confidence_level
                )
            else:
                raise ValueError(f"不支持的压力测试情景: {scenario}")

        except Exception as e:
            self.logger.error(f"压力测试失败: {e}")
            return self._create_default_result(scenario)

    def _market_crash_scenario(
        self,
        portfolio_holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        confidence_level: float,
    ) -> StressTestResult:
        """市场崩盘情景"""

        # 市场崩盘：所有股票下跌20 - 50%
        crash_scenarios = [0.2, 0.3, 0.4, 0.5]  # 20%, 30%, 40%, 50 % 下跌

        portfolio_losses = []
        for crash_rate in crash_scenarios:
            total_loss = 0.0
            for symbol, position_value in portfolio_holdings.items():
                if symbol in market_data:
                    # 计算该资产的损失
                    asset_loss = position_value * crash_rate
                    total_loss += asset_loss
            portfolio_losses.append(total_loss)

        # 计算统计指标
        portfolio_loss = np.mean(portfolio_losses)
        worst_case_loss = np.max(portfolio_losses)
        loss_percentage = (
            portfolio_loss / sum(portfolio_holdings.values())
            if portfolio_holdings
            else 0.0
        )

        # 估算恢复时间（基于历史数据）
        recovery_time = self._estimate_recovery_time(market_data, "market_crash")

        return StressTestResult(
            scenario=StressTestScenario.MARKET_CRASH,
            portfolio_loss=portfolio_loss,
            loss_percentage=loss_percentage,
            var_impact=portfolio_loss * 1.5,  # VaR影响通常是损失的1.5倍
            expected_shortfall=worst_case_loss,
            recovery_time_days=recovery_time,
            worst_case_loss=worst_case_loss,
            confidence_level=confidence_level,
        )

    def _interest_rate_shock_scenario(
        self,
        portfolio_holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        confidence_level: float,
    ) -> StressTestResult:
        """利率冲击情景"""

        # 利率上升2 - 5 % 的影响
        rate_shocks = [0.02, 0.03, 0.04, 0.05]

        portfolio_losses = []
        for rate_shock in rate_shocks:
            total_loss = 0.0
            for symbol, position_value in portfolio_holdings.items():
                if symbol in market_data:
                    # 简化：利率敏感资产下跌
                    # 实际应用中需要根据资产的利率敏感性计算
                    sensitivity = 0.5  # 假设平均利率敏感性为0.5
                    asset_loss = position_value * rate_shock * sensitivity
                    total_loss += asset_loss
            portfolio_losses.append(total_loss)

        portfolio_loss = np.mean(portfolio_losses)
        worst_case_loss = np.max(portfolio_losses)
        loss_percentage = (
            portfolio_loss / sum(portfolio_holdings.values())
            if portfolio_holdings
            else 0.0
        )

        recovery_time = self._estimate_recovery_time(market_data, "interest_rate_shock")

        return StressTestResult(
            scenario=StressTestScenario.INTEREST_RATE_SHOCK,
            portfolio_loss=portfolio_loss,
            loss_percentage=loss_percentage,
            var_impact=portfolio_loss * 1.2,
            expected_shortfall=worst_case_loss,
            recovery_time_days=recovery_time,
            worst_case_loss=worst_case_loss,
            confidence_level=confidence_level,
        )

    def _currency_crisis_scenario(
        self,
        portfolio_holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        confidence_level: float,
    ) -> StressTestResult:
        """货币危机情景"""

        # 港币贬值10 - 30%
        devaluation_rates = [0.1, 0.15, 0.2, 0.3]

        portfolio_losses = []
        for deval_rate in devaluation_rates:
            total_loss = 0.0
            for symbol, position_value in portfolio_holdings.items():
                if symbol in market_data:
                    # 货币贬值对港股的影响
                    # 通常港股会下跌，因为外资流出
                    asset_loss = position_value * deval_rate * 0.8  # 80 % 的汇率影响
                    total_loss += asset_loss
            portfolio_losses.append(total_loss)

        portfolio_loss = np.mean(portfolio_losses)
        worst_case_loss = np.max(portfolio_losses)
        loss_percentage = (
            portfolio_loss / sum(portfolio_holdings.values())
            if portfolio_holdings
            else 0.0
        )

        recovery_time = self._estimate_recovery_time(market_data, "currency_crisis")

        return StressTestResult(
            scenario=StressTestScenario.CURRENCY_CRISIS,
            portfolio_loss=portfolio_loss,
            loss_percentage=loss_percentage,
            var_impact=portfolio_loss * 1.3,
            expected_shortfall=worst_case_loss,
            recovery_time_days=recovery_time,
            worst_case_loss=worst_case_loss,
            confidence_level=confidence_level,
        )

    def _sector_decline_scenario(
        self,
        portfolio_holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        confidence_level: float,
    ) -> StressTestResult:
        """行业衰退情景"""

        # 特定行业下跌30 - 60%
        sector_declines = [0.3, 0.4, 0.5, 0.6]

        portfolio_losses = []
        for decline_rate in sector_declines:
            total_loss = 0.0
            for symbol, position_value in portfolio_holdings.items():
                if symbol in market_data:
                    # 假设50 % 的资产属于受影响行业
                    sector_exposure = 0.5
                    asset_loss = position_value * decline_rate * sector_exposure
                    total_loss += asset_loss
            portfolio_losses.append(total_loss)

        portfolio_loss = np.mean(portfolio_losses)
        worst_case_loss = np.max(portfolio_losses)
        loss_percentage = (
            portfolio_loss / sum(portfolio_holdings.values())
            if portfolio_holdings
            else 0.0
        )

        recovery_time = self._estimate_recovery_time(market_data, "sector_decline")

        return StressTestResult(
            scenario=StressTestScenario.SECTOR_DECLINE,
            portfolio_loss=portfolio_loss,
            loss_percentage=loss_percentage,
            var_impact=portfolio_loss * 1.4,
            expected_shortfall=worst_case_loss,
            recovery_time_days=recovery_time,
            worst_case_loss=worst_case_loss,
            confidence_level=confidence_level,
        )

    def _liquidity_crisis_scenario(
        self,
        portfolio_holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
        confidence_level: float,
    ) -> StressTestResult:
        """流动性危机情景"""

        # 流动性危机导致额外的交易成本
        liquidity_impacts = [0.05, 0.1, 0.15, 0.2]  # 5%, 10%, 15%, 20 % 的额外成本

        portfolio_losses = []
        for impact in liquidity_impacts:
            total_loss = 0.0
            for symbol, position_value in portfolio_holdings.items():
                if symbol in market_data:
                    # 流动性危机导致的额外损失
                    asset_loss = position_value * impact
                    total_loss += asset_loss
            portfolio_losses.append(total_loss)

        portfolio_loss = np.mean(portfolio_losses)
        worst_case_loss = np.max(portfolio_losses)
        loss_percentage = (
            portfolio_loss / sum(portfolio_holdings.values())
            if portfolio_holdings
            else 0.0
        )

        recovery_time = self._estimate_recovery_time(market_data, "liquidity_crisis")

        return StressTestResult(
            scenario=StressTestScenario.LIQUIDITY_CRISIS,
            portfolio_loss=portfolio_loss,
            loss_percentage=loss_percentage,
            var_impact=portfolio_loss * 1.1,
            expected_shortfall=worst_case_loss,
            recovery_time_days=recovery_time,
            worst_case_loss=worst_case_loss,
            confidence_level=confidence_level,
        )

    def _estimate_recovery_time(
        self, market_data: Dict[str, pd.DataFrame], scenario_type: str
    ) -> int:
        """估算恢复时间"""

        # 基于历史数据的简化估算
        recovery_times = {
            "market_crash": 180,  # 6个月
            "interest_rate_shock": 90,  # 3个月
            "currency_crisis": 120,  # 4个月
            "sector_decline": 150,  # 5个月
            "liquidity_crisis": 60,  # 2个月
        }

        return recovery_times.get(scenario_type, 90)

    def _create_default_result(self, scenario: StressTestScenario) -> StressTestResult:
        """创建默认结果"""
        return StressTestResult(
            scenario=scenario,
            portfolio_loss=0.0,
            loss_percentage=0.0,
            var_impact=0.0,
            expected_shortfall=0.0,
            recovery_time_days=90,
            worst_case_loss=0.0,
            confidence_level=0.95,
        )


class RiskMonitor:
    """风险监控器"""

    def __init__(self):
        self.logger = logging.getLogger("hk_quant_system.risk_analyst.risk_monitor")
        self.risk_limits: Dict[str, RiskLimit] = {}
        self.active_alerts: List[RiskAlert] = []

    def set_risk_limits(self, limits_config: Dict[str, Dict[str, float]]):
        """设置风险限制"""
        try:
            for risk_type, config in limits_config.items():
                limit = RiskLimit(
                    risk_type=risk_type,
                    limit_value=config.get("limit_value", 0.0),
                    current_value=0.0,
                    utilization=0.0,
                    status="safe",
                )
                self.risk_limits[risk_type] = limit

            self.logger.info(f"设置了 {len(self.risk_limits)} 个风险限制")

        except Exception as e:
            self.logger.error(f"设置风险限制失败: {e}")

    def update_risk_metrics(
        self,
        portfolio_value: float,
        holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
    ) -> List[RiskAlert]:
        """更新风险指标并生成预警"""

        alerts = []

        try:
            # 更新各种风险指标
            self._update_var_metrics(portfolio_value, holdings, market_data)
            self._update_concentration_risk(holdings)
            self._update_liquidity_risk(holdings, market_data)
            self._update_volatility_risk(holdings, market_data)

            # 检查风险限制
            alerts = self._check_risk_limits()

            # 更新活跃预警列表
            self.active_alerts.extend(alerts)

        except Exception as e:
            self.logger.error(f"更新风险指标失败: {e}")

        return alerts

    def _update_var_metrics(
        self,
        portfolio_value: float,
        holdings: Dict[str, float],
        market_data: Dict[str, pd.DataFrame],
    ):
        """更新VaR指标"""
        try:
            if "var_daily" not in self.risk_limits:
                return

            # 计算投资组合的日VaR
            total_var = 0.0
            for symbol, position_value in holdings.items():
                if symbol in market_data and len(market_data[symbol]) > 30:
                    returns = market_data[symbol]["close"].pct_change().dropna()
                    if len(returns) > 0:
                        var_calculator = VaRCalculator()
                        var_result = var_calculator.calculate_var(
                            returns.values, method=VaRMethod.HISTORICAL
                        )
                        position_var = position_value * var_result["var"]
                        total_var += position_var

            # 更新VaR限制
            var_limit = self.risk_limits["var_daily"]
            var_limit.current_value = total_var
            var_limit.utilization = (
                total_var / var_limit.limit_value if var_limit.limit_value > 0 else 0.0
            )

            if var_limit.utilization > 1.0:
                var_limit.status = "breach"
            elif var_limit.utilization > 0.8:
                var_limit.status = "warning"
            else:
                var_limit.status = "safe"

            var_limit.last_updated = datetime.now()

        except Exception as e:
            self.logger.error(f"更新VaR指标失败: {e}")

    def _update_concentration_risk(self, holdings: Dict[str, float]):
        """更新集中度风险"""
        try:
            if not holdings:
                return

            total_value = sum(holdings.values())
            if total_value == 0:
                return

            # 计算最大单一持仓权重
            max_weight = max(holdings.values()) / total_value

            # 更新集中度风险限制
            if "concentration_risk" in self.risk_limits:
                concentration_limit = self.risk_limits["concentration_risk"]
                concentration_limit.current_value = max_weight
                concentration_limit.utilization = (
                    max_weight / concentration_limit.limit_value
                )

                if concentration_limit.utilization > 1.0:
                    concentration_limit.status = "breach"
                elif concentration_limit.utilization > 0.8:
                    concentration_limit.status = "warning"
                else:
                    concentration_limit.status = "safe"

                concentration_limit.last_updated = datetime.now()

        except Exception as e:
            self.logger.error(f"更新集中度风险失败: {e}")

    def _update_liquidity_risk(
        self, holdings: Dict[str, float], market_data: Dict[str, pd.DataFrame]
    ):
        """更新流动性风险"""
        try:
            if "liquidity_risk" not in self.risk_limits:
                return

            # 计算流动性风险（基于交易量）
            total_illiquid_value = 0.0
            for symbol, position_value in holdings.items():
                if symbol in market_data and len(market_data[symbol]) > 0:
                    # 获取最近的平均交易量
                    recent_volume = market_data[symbol]["volume"].tail(10).mean()

                    # 如果交易量太小，认为流动性不足
                    if recent_volume < 1000000:  # 100万港元
                        total_illiquid_value += position_value

            total_value = sum(holdings.values())
            illiquid_ratio = (
                total_illiquid_value / total_value if total_value > 0 else 0.0
            )

            # 更新流动性风险限制
            liquidity_limit = self.risk_limits["liquidity_risk"]
            liquidity_limit.current_value = illiquid_ratio
            liquidity_limit.utilization = (
                illiquid_ratio / liquidity_limit.limit_value
                if liquidity_limit.limit_value > 0
                else 0.0
            )

            if liquidity_limit.utilization > 1.0:
                liquidity_limit.status = "breach"
            elif liquidity_limit.utilization > 0.8:
                liquidity_limit.status = "warning"
            else:
                liquidity_limit.status = "safe"

            liquidity_limit.last_updated = datetime.now()

        except Exception as e:
            self.logger.error(f"更新流动性风险失败: {e}")

    def _update_volatility_risk(
        self, holdings: Dict[str, float], market_data: Dict[str, pd.DataFrame]
    ):
        """更新波动率风险"""
        try:
            if "volatility_risk" not in self.risk_limits:
                return

            # 计算投资组合波动率
            portfolio_volatility = 0.0
            total_value = sum(holdings.values())

            if total_value > 0:
                for symbol, position_value in holdings.items():
                    if symbol in market_data and len(market_data[symbol]) > 30:
                        returns = market_data[symbol]["close"].pct_change().dropna()
                        if len(returns) > 0:
                            asset_volatility = returns.std() * np.sqrt(
                                252
                            )  # 年化波动率
                            weight = position_value / total_value
                            portfolio_volatility += (weight * asset_volatility) ** 2

                portfolio_volatility = np.sqrt(portfolio_volatility)

            # 更新波动率风险限制
            volatility_limit = self.risk_limits["volatility_risk"]
            volatility_limit.current_value = portfolio_volatility
            volatility_limit.utilization = (
                portfolio_volatility / volatility_limit.limit_value
                if volatility_limit.limit_value > 0
                else 0.0
            )

            if volatility_limit.utilization > 1.0:
                volatility_limit.status = "breach"
            elif volatility_limit.utilization > 0.8:
                volatility_limit.status = "warning"
            else:
                volatility_limit.status = "safe"

            volatility_limit.last_updated = datetime.now()

        except Exception as e:
            self.logger.error(f"更新波动率风险失败: {e}")

    def _check_risk_limits(self) -> List[RiskAlert]:
        """检查风险限制并生成预警"""
        alerts = []

        try:
            for risk_type, limit in self.risk_limits.items():
                if limit.status in ["warning", "breach"]:
                    risk_level = (
                        RiskLevel.HIGH if limit.status == "breach" else RiskLevel.MEDIUM
                    )

                    alert = RiskAlert(
                        alert_id=f"risk_alert_{risk_type}_{datetime.now().timestamp()}",
                        risk_type=risk_type,
                        risk_level=risk_level,
                        current_value=limit.current_value,
                        threshold_value=limit.limit_value,
                        deviation=limit.utilization - 1.0,
                        description=f"{risk_type}风险超过限制",
                        recommendation=self._get_risk_recommendation(risk_type, limit),
                        timestamp=datetime.now(),
                    )

                    alerts.append(alert)

        except Exception as e:
            self.logger.error(f"检查风险限制失败: {e}")

        return alerts

    def _get_risk_recommendation(self, risk_type: str, limit: RiskLimit) -> str:
        """获取风险建议"""
        recommendations = {
            "var_daily": "建议减少仓位或增加对冲",
            "concentration_risk": "建议分散投资，减少单一持仓",
            "liquidity_risk": "建议增加流动性好的资产",
            "volatility_risk": "建议降低投资组合波动率",
        }

        base_recommendation = recommendations.get(risk_type, "建议调整投资组合配置")

        if limit.status == "breach":
            return f"紧急：{base_recommendation}"
        else:
            return f"预警：{base_recommendation}"


class RiskAnalystAgent(BaseAgent):
    """风险分析师Agent"""

    def __init__(
        self,
        config: AgentConfig,
        message_queue: MessageQueue,
        system_config: SystemConfig = None,
    ):
        super().__init__(config, message_queue, system_config)

        # 初始化组件
        self.var_calculator = VaRCalculator()
        self.stress_tester = StressTester()
        self.risk_monitor = RiskMonitor()

        # 风险数据缓存
        self.market_data_cache: Dict[str, pd.DataFrame] = {}
        self.portfolio_data: Dict[str, Any] = {}
        self.risk_metrics_history: List[RiskMetrics] = []

        # 默认风险限制配置
        self.default_risk_limits = {
            "var_daily": {"limit_value": 0.02},  # 日VaR限制2%
            "concentration_risk": {"limit_value": 0.1},  # 最大单一持仓10%
            "liquidity_risk": {"limit_value": 0.2},  # 流动性不足资产最多20%
            "volatility_risk": {"limit_value": 0.25},  # 年化波动率限制25%
        }

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
                MessageType.SIGNAL, self._handle_portfolio_update
            )
            self.protocol.register_handler(
                MessageType.CONTROL, self._handle_risk_control
            )

            # 设置默认风险限制
            self.risk_monitor.set_risk_limits(self.default_risk_limits)

            self.logger.info(f"风险分析师Agent初始化成功: {self.config.agent_id}")
            return True

        except Exception as e:
            self.logger.error(f"风险分析师Agent初始化失败: {e}")
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
        self.logger.info("清理风险分析师Agent资源")

        # 保存风险数据
        await self._save_risk_data()

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

    async def _handle_portfolio_update(self, protocol_message):
        """处理投资组合更新"""
        try:
            update_type = protocol_message.payload.get("update_type")
            portfolio_data = protocol_message.payload.get("portfolio_data", {})

            if update_type == "portfolio_update":
                await self._process_portfolio_update(portfolio_data)

        except Exception as e:
            self.logger.error(f"处理投资组合更新失败: {e}")

    async def _handle_risk_control(self, protocol_message):
        """处理风险控制消息"""
        try:
            command = protocol_message.payload.get("command")
            parameters = protocol_message.payload.get("parameters", {})

            if command == "run_stress_test":
                scenario = parameters.get("scenario", "market_crash")
                await self._run_stress_test(scenario)

            elif command == "update_risk_limits":
                new_limits = parameters.get("risk_limits", {})
                self.risk_monitor.set_risk_limits(new_limits)

            elif command == "calculate_var":
                method = parameters.get("method", "historical")
                await self._calculate_portfolio_var(method)

        except Exception as e:
            self.logger.error(f"处理风险控制消息失败: {e}")

    async def _process_market_data(self, symbol: str, market_data: Dict[str, Any]):
        """处理市场数据"""
        try:
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

            # 如果有投资组合数据，更新风险指标
            if self.portfolio_data:
                await self._update_risk_metrics()

        except Exception as e:
            self.logger.error(f"处理市场数据失败: {e}")

    async def _process_portfolio_update(self, portfolio_data: Dict[str, Any]):
        """处理投资组合更新"""
        try:
            self.portfolio_data = portfolio_data

            # 更新风险指标
            await self._update_risk_metrics()

        except Exception as e:
            self.logger.error(f"处理投资组合更新失败: {e}")

    async def _update_risk_metrics(self):
        """更新风险指标"""
        try:
            if not self.portfolio_data or not self.market_data_cache:
                return

            portfolio_value = self.portfolio_data.get("total_value", 0.0)
            holdings = self.portfolio_data.get("holdings", {})

            # 更新风险指标并获取预警
            alerts = self.risk_monitor.update_risk_metrics(
                portfolio_value, holdings, self.market_data_cache
            )

            # 发送预警
            for alert in alerts:
                await self._send_risk_alert(alert)

            # 计算VaR指标
            await self._calculate_portfolio_var()

        except Exception as e:
            self.logger.error(f"更新风险指标失败: {e}")

    async def _calculate_portfolio_var(self, method: str = "historical"):
        """计算投资组合VaR"""
        try:
            if not self.portfolio_data or not self.market_data_cache:
                return

            holdings = self.portfolio_data.get("holdings", {})
            total_var = 0.0
            var_details = {}

            for symbol, position_value in holdings.items():
                if (
                    symbol in self.market_data_cache
                    and len(self.market_data_cache[symbol]) > 30
                ):
                    returns = (
                        self.market_data_cache[symbol]["close"].pct_change().dropna()
                    )
                    if len(returns) > 0:
                        var_result = self.var_calculator.calculate_var(
                            returns.values, method=VaRMethod(method)
                        )
                        position_var = position_value * var_result["var"]
                        total_var += position_var

                        var_details[symbol] = {
                            "position_value": position_value,
                            "var": var_result["var"],
                            "position_var": position_var,
                        }

            # 创建风险指标记录
            risk_metrics = RiskMetrics(
                metric_id=f"var_{datetime.now().timestamp()}",
                portfolio_id=self.portfolio_data.get("portfolio_id", "default"),
                value_at_risk=total_var,
                expected_shortfall=total_var * 1.2,  # 简化处理
                sharpe_ratio=0.0,  # 需要更复杂的计算
                max_drawdown=0.0,
                timestamp=datetime.now(),
            )

            self.risk_metrics_history.append(risk_metrics)

            # 广播VaR结果
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "risk_metrics": {
                        "total_var": total_var,
                        "var_details": var_details,
                        "method": method,
                        "timestamp": datetime.now().isoformat(),
                    }
                },
            )

            self.logger.info(f"投资组合VaR计算完成: {total_var:.2f}")

        except Exception as e:
            self.logger.error(f"计算投资组合VaR失败: {e}")

    async def _run_stress_test(self, scenario: str):
        """运行压力测试"""
        try:
            if not self.portfolio_data or not self.market_data_cache:
                self.logger.warning("数据不足，无法运行压力测试")
                return

            holdings = self.portfolio_data.get("holdings", {})
            scenario_enum = StressTestScenario(scenario)

            # 运行压力测试
            stress_result = self.stress_tester.run_stress_test(
                holdings, self.market_data_cache, scenario_enum
            )

            # 广播压力测试结果
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "stress_test_result": {
                        "scenario": scenario,
                        "portfolio_loss": stress_result.portfolio_loss,
                        "loss_percentage": stress_result.loss_percentage,
                        "recovery_time_days": stress_result.recovery_time_days,
                        "worst_case_loss": stress_result.worst_case_loss,
                        "timestamp": datetime.now().isoformat(),
                    }
                },
            )

            self.logger.info(
                f"压力测试完成: {scenario}, 损失: {stress_result.portfolio_loss:.2f}"
            )

        except Exception as e:
            self.logger.error(f"运行压力测试失败: {e}")

    async def _send_risk_alert(self, alert: RiskAlert):
        """发送风险预警"""
        try:
            await self.protocol.broadcast_message(
                message_type=MessageType.DATA,
                payload={
                    "risk_alert": {
                        "alert_id": alert.alert_id,
                        "risk_type": alert.risk_type,
                        "risk_level": alert.risk_level.value,
                        "current_value": alert.current_value,
                        "threshold_value": alert.threshold_value,
                        "deviation": alert.deviation,
                        "description": alert.description,
                        "recommendation": alert.recommendation,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                },
            )

            self.logger.warning(f"风险预警: {alert.risk_type} - {alert.description}")

        except Exception as e:
            self.logger.error(f"发送风险预警失败: {e}")

    async def _save_risk_data(self):
        """保存风险数据"""
        try:
            # 这里可以保存到数据库
            self.logger.info(f"保存风险数据: {len(self.risk_metrics_history)} 条记录")

        except Exception as e:
            self.logger.error(f"保存风险数据失败: {e}")

    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要"""
        return {
            "agent_id": self.config.agent_id,
            "risk_limits_count": len(self.risk_monitor.risk_limits),
            "active_alerts_count": len(self.risk_monitor.active_alerts),
            "risk_metrics_history_count": len(self.risk_metrics_history),
            "cached_symbols": list(self.market_data_cache.keys()),
            "portfolio_data_available": bool(self.portfolio_data),
            "protocol_stats": self.protocol.get_protocol_stats(),
        }


# 导出主要组件
__all__ = [
    "RiskAnalystAgent",
    "VaRCalculator",
    "StressTester",
    "RiskMonitor",
    "RiskAlert",
    "StressTestResult",
    "RiskLimit",
]
