"""
港股量化交易 AI Agent 系统 - 对冲策略引擎

实现自动对冲策略、动态对冲比例计算和多种对冲工具管理。
确保投资组合在市场波动中保持风险中性。
"""

import asyncio
import logging
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ...models.base import BaseModel


class HedgeType(str, Enum):
    """对冲类型"""

    DELTA_HEDGE = "delta_hedge"
    BETA_HEDGE = "beta_hedge"
    VARIANCE_HEDGE = "variance_hedge"
    OPTIONS_HEDGE = "options_hedge"
    CURRENCY_HEDGE = "currency_hedge"
    SECTOR_HEDGE = "sector_hedge"


class HedgeInstrument(str, Enum):
    """对冲工具"""

    FUTURES = "futures"
    OPTIONS = "options"
    SWAPS = "swaps"
    ETFS = "etfs"
    CASH = "cash"


@dataclass
class HedgeConfig:
    """对冲配置"""

    # 对冲策略配置
    hedge_type: HedgeType = HedgeType.DELTA_HEDGE
    hedge_frequency: int = 60  # 对冲频率（分钟）
    hedge_threshold: float = 0.02  # 对冲触发阈值

    # 风险控制参数
    max_hedge_ratio: float = 1.5  # 最大对冲比例
    min_hedge_ratio: float = 0.0  # 最小对冲比例
    hedge_tolerance: float = 0.01  # 对冲容忍度

    # 成本控制
    transaction_cost_rate: float = 0.001  # 交易成本率
    max_daily_cost: float = 10000.0  # 每日最大对冲成本
    cost_benefit_threshold: float = 0.5  # 成本效益阈值

    # 计算参数
    lookback_period: int = 30  # 回望期（天）
    correlation_window: int = 60  # 相关性计算窗口
    volatility_window: int = 30  # 波动率计算窗口

    # 对冲工具配置
    preferred_instruments: List[HedgeInstrument] = field(
        default_factory=lambda: [HedgeInstrument.FUTURES, HedgeInstrument.ETFS]
    )

    # 市场条件过滤
    min_volume_threshold: float = 1000000.0  # 最小成交量阈值
    max_spread_threshold: float = 0.005  # 最大价差阈值


@dataclass
class HedgePosition(BaseModel):
    """对冲头寸"""

    instrument_symbol: str
    instrument_type: HedgeInstrument
    position_size: float
    hedge_ratio: float
    cost_basis: float
    current_price: float
    unrealized_pnl: float
    hedge_effectiveness: float
    entry_time: datetime
    last_updated: datetime


@dataclass
class HedgeResult(BaseModel):
    """对冲结果"""

    portfolio_id: str
    timestamp: datetime
    hedge_type: HedgeType
    target_hedge_ratio: float
    current_hedge_ratio: float
    hedge_recommendations: List[Dict[str, Any]]
    hedge_positions: List[HedgePosition]
    portfolio_delta: float
    portfolio_beta: float
    hedge_effectiveness: float
    total_hedge_cost: float
    risk_reduction: float
    status: str
    message: str


class HedgeStrategy(ABC):
    """对冲策略基类"""

    def __init__(self, config: HedgeConfig):
        self.config = config
        self.logger = logging.getLogger(
            f"hk_quant_system.hedge_engine.{self.__class__.__name__}"
        )

    @abstractmethod
    async def calculate_hedge_ratio(
        self,
        portfolio_data: pd.DataFrame,
        market_data: pd.DataFrame,
        current_positions: List[HedgePosition],
    ) -> float:
        """计算对冲比例"""
        pass

    @abstractmethod
    async def generate_hedge_recommendations(
        self,
        target_ratio: float,
        current_ratio: float,
        market_data: pd.DataFrame,
        available_instruments: List[str],
    ) -> List[Dict[str, Any]]:
        """生成对冲建议"""
        pass


class DeltaHedge(HedgeStrategy):
    """Delta对冲策略"""

    async def calculate_hedge_ratio(
        self,
        portfolio_data: pd.DataFrame,
        market_data: pd.DataFrame,
        current_positions: List[HedgePosition],
    ) -> float:
        """计算Delta对冲比例"""

        try:
            # 计算投资组合的Delta
            portfolio_delta = self._calculate_portfolio_delta(portfolio_data)

            # 计算基准指数的Delta
            benchmark_delta = self._calculate_benchmark_delta(market_data)

            # 计算对冲比例
            if abs(benchmark_delta) > 1e-6:
                hedge_ratio = -portfolio_delta / benchmark_delta
                hedge_ratio = np.clip(
                    hedge_ratio,
                    self.config.min_hedge_ratio,
                    self.config.max_hedge_ratio,
                )
            else:
                hedge_ratio = 0.0

            self.logger.info(f"Delta对冲比例计算: {hedge_ratio:.4f}")
            return hedge_ratio

        except Exception as exc:
            self.logger.error(f"Delta对冲比例计算失败: {exc}")
            return 0.0

    def _calculate_portfolio_delta(self, portfolio_data: pd.DataFrame) -> float:
        """计算投资组合Delta"""

        # 简化的Delta计算：基于价格变化对投资组合价值的影响
        if len(portfolio_data) < 2:
            return 0.0

        portfolio_returns = portfolio_data["portfolio_value"].pct_change().dropna()
        market_returns = portfolio_data["benchmark_price"].pct_change().dropna()

        if len(portfolio_returns) < 2:
            return 0.0

        # 计算Beta作为Delta的近似
        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)

        if market_variance > 0:
            beta = covariance / market_variance
            return beta

        return 0.0

    def _calculate_benchmark_delta(self, market_data: pd.DataFrame) -> float:
        """计算基准Delta"""

        if len(market_data) < 2:
            return 1.0

        # 基准指数的Delta通常为1.0（相对于自身）
        return 1.0

    async def generate_hedge_recommendations(
        self,
        target_ratio: float,
        current_ratio: float,
        market_data: pd.DataFrame,
        available_instruments: List[str],
    ) -> List[Dict[str, Any]]:
        """生成Delta对冲建议"""

        recommendations = []
        ratio_diff = target_ratio - current_ratio

        if abs(ratio_diff) < self.config.hedge_tolerance:
            return recommendations

        # 寻找合适的对冲工具
        for instrument in available_instruments:
            if instrument.startswith("HSI") or instrument.startswith(
                "2800"
            ):  # 恒指相关
                recommendation = {
                    "instrument": instrument,
                    "action": "buy" if ratio_diff > 0 else "sell",
                    "quantity": abs(ratio_diff),
                    "reason": f"Delta对冲调整: {ratio_diff:.4f}",
                    "priority": "high",
                    "estimated_cost": abs(ratio_diff)
                    * market_data[instrument].iloc[-1]
                    * self.config.transaction_cost_rate,
                }
                recommendations.append(recommendation)

        return recommendations


class BetaHedge(HedgeStrategy):
    """Beta对冲策略"""

    async def calculate_hedge_ratio(
        self,
        portfolio_data: pd.DataFrame,
        market_data: pd.DataFrame,
        current_positions: List[HedgePosition],
    ) -> float:
        """计算Beta对冲比例"""

        try:
            # 计算投资组合Beta
            portfolio_beta = self._calculate_portfolio_beta(portfolio_data, market_data)

            # 目标Beta（通常为0，即市场中性）
            target_beta = 0.0

            # 计算对冲比例
            hedge_ratio = target_beta - portfolio_beta
            hedge_ratio = np.clip(
                hedge_ratio, self.config.min_hedge_ratio, self.config.max_hedge_ratio
            )

            self.logger.info(
                f"Beta对冲比例计算: {hedge_ratio:.4f}, 当前Beta: {portfolio_beta:.4f}"
            )
            return hedge_ratio

        except Exception as exc:
            self.logger.error(f"Beta对冲比例计算失败: {exc}")
            return 0.0

    def _calculate_portfolio_beta(
        self, portfolio_data: pd.DataFrame, market_data: pd.DataFrame
    ) -> float:
        """计算投资组合Beta"""

        if len(portfolio_data) < 2 or len(market_data) < 2:
            return 1.0

        # 计算收益率
        portfolio_returns = portfolio_data["portfolio_value"].pct_change().dropna()
        market_returns = market_data["benchmark_price"].pct_change().dropna()

        # 对齐数据
        min_length = min(len(portfolio_returns), len(market_returns))
        portfolio_returns = portfolio_returns.tail(min_length)
        market_returns = market_returns.tail(min_length)

        if len(portfolio_returns) < 2:
            return 1.0

        # 计算Beta
        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)

        if market_variance > 0:
            return covariance / market_variance

        return 1.0

    async def generate_hedge_recommendations(
        self,
        target_ratio: float,
        current_ratio: float,
        market_data: pd.DataFrame,
        available_instruments: List[str],
    ) -> List[Dict[str, Any]]:
        """生成Beta对冲建议"""

        recommendations = []
        ratio_diff = target_ratio - current_ratio

        if abs(ratio_diff) < self.config.hedge_tolerance:
            return recommendations

        # 寻找Beta为1的工具（如指数ETF）
        for instrument in available_instruments:
            if instrument in ["2800.HK", "HSI.HK"]:  # 恒指ETF
                recommendation = {
                    "instrument": instrument,
                    "action": "buy" if ratio_diff > 0 else "sell",
                    "quantity": abs(ratio_diff),
                    "reason": f"Beta对冲调整: {ratio_diff:.4f}",
                    "priority": "high",
                    "estimated_cost": abs(ratio_diff)
                    * market_data[instrument].iloc[-1]
                    * self.config.transaction_cost_rate,
                }
                recommendations.append(recommendation)

        return recommendations


class VarianceHedge(HedgeStrategy):
    """方差对冲策略"""

    async def calculate_hedge_ratio(
        self,
        portfolio_data: pd.DataFrame,
        market_data: pd.DataFrame,
        current_positions: List[HedgePosition],
    ) -> float:
        """计算方差对冲比例"""

        try:
            # 计算投资组合波动率
            portfolio_vol = self._calculate_portfolio_volatility(portfolio_data)

            # 计算市场波动率
            market_vol = self._calculate_market_volatility(market_data)

            # 目标波动率（基于风险预算）
            target_vol = self.config.hedge_threshold * 2  # 简化的目标波动率

            # 计算对冲比例
            vol_diff = portfolio_vol - target_vol
            hedge_ratio = vol_diff / market_vol if market_vol > 0 else 0.0
            hedge_ratio = np.clip(
                hedge_ratio, self.config.min_hedge_ratio, self.config.max_hedge_ratio
            )

            self.logger.info(
                f"方差对冲比例计算: {hedge_ratio:.4f}, 组合波动率: {portfolio_vol:.4f}"
            )
            return hedge_ratio

        except Exception as exc:
            self.logger.error(f"方差对冲比例计算失败: {exc}")
            return 0.0

    def _calculate_portfolio_volatility(self, portfolio_data: pd.DataFrame) -> float:
        """计算投资组合波动率"""

        if len(portfolio_data) < 2:
            return 0.0

        returns = portfolio_data["portfolio_value"].pct_change().dropna()
        if len(returns) < 2:
            return 0.0

        return returns.std() * np.sqrt(252)  # 年化波动率

    def _calculate_market_volatility(self, market_data: pd.DataFrame) -> float:
        """计算市场波动率"""

        if len(market_data) < 2:
            return 0.0

        returns = market_data["benchmark_price"].pct_change().dropna()
        if len(returns) < 2:
            return 0.0

        return returns.std() * np.sqrt(252)  # 年化波动率

    async def generate_hedge_recommendations(
        self,
        target_ratio: float,
        current_ratio: float,
        market_data: pd.DataFrame,
        available_instruments: List[str],
    ) -> List[Dict[str, Any]]:
        """生成方差对冲建议"""

        recommendations = []
        ratio_diff = target_ratio - current_ratio

        if abs(ratio_diff) < self.config.hedge_tolerance:
            return recommendations

        # 寻找波动率相关的对冲工具
        for instrument in available_instruments:
            if "VIX" in instrument or "volatility" in instrument.lower():
                recommendation = {
                    "instrument": instrument,
                    "action": "buy" if ratio_diff > 0 else "sell",
                    "quantity": abs(ratio_diff),
                    "reason": f"方差对冲调整: {ratio_diff:.4f}",
                    "priority": "medium",
                    "estimated_cost": abs(ratio_diff)
                    * market_data[instrument].iloc[-1]
                    * self.config.transaction_cost_rate,
                }
                recommendations.append(recommendation)

        return recommendations


class HedgeEngine:
    """对冲策略引擎主类"""

    def __init__(self, config: HedgeConfig):
        self.config = config
        self.logger = logging.getLogger("hk_quant_system.hedge_engine")
        self.strategies = self._initialize_strategies()
        self.hedge_positions: List[HedgePosition] = []
        self.hedge_history: List[HedgeResult] = []

    def _initialize_strategies(self) -> Dict[HedgeType, HedgeStrategy]:
        """初始化对冲策略"""

        strategies = {
            HedgeType.DELTA_HEDGE: DeltaHedge(self.config),
            HedgeType.BETA_HEDGE: BetaHedge(self.config),
            HedgeType.VARIANCE_HEDGE: VarianceHedge(self.config),
        }

        return strategies

    async def calculate_hedge_requirements(
        self,
        portfolio_id: str,
        portfolio_data: pd.DataFrame,
        market_data: pd.DataFrame,
        available_instruments: List[str],
    ) -> HedgeResult:
        """计算对冲需求"""

        try:
            # 获取当前对冲策略
            strategy = self.strategies.get(self.config.hedge_type)
            if not strategy:
                raise ValueError(f"未知的对冲策略: {self.config.hedge_type}")

            # 计算目标对冲比例
            target_ratio = await strategy.calculate_hedge_ratio(
                portfolio_data, market_data, self.hedge_positions
            )

            # 计算当前对冲比例
            current_ratio = self._calculate_current_hedge_ratio()

            # 生成对冲建议
            hedge_recommendations = await strategy.generate_hedge_recommendations(
                target_ratio, current_ratio, market_data, available_instruments
            )

            # 计算投资组合风险指标
            portfolio_delta = self._calculate_portfolio_delta(portfolio_data)
            portfolio_beta = self._calculate_portfolio_beta(portfolio_data, market_data)

            # 计算对冲有效性
            hedge_effectiveness = self._calculate_hedge_effectiveness()

            # 计算总对冲成本
            total_cost = sum(
                rec.get("estimated_cost", 0) for rec in hedge_recommendations
            )

            # 计算风险降低程度
            risk_reduction = self._calculate_risk_reduction(target_ratio, current_ratio)

            # 创建对冲结果
            result = HedgeResult(
                id=f"hedge_result_{portfolio_id}_{datetime.now().timestamp()}",
                portfolio_id=portfolio_id,
                timestamp=datetime.now(),
                hedge_type=self.config.hedge_type,
                target_hedge_ratio=target_ratio,
                current_hedge_ratio=current_ratio,
                hedge_recommendations=hedge_recommendations,
                hedge_positions=self.hedge_positions.copy(),
                portfolio_delta=portfolio_delta,
                portfolio_beta=portfolio_beta,
                hedge_effectiveness=hedge_effectiveness,
                total_hedge_cost=total_cost,
                risk_reduction=risk_reduction,
                status="success",
                message=f"对冲计算完成: 目标比例 {target_ratio:.4f}, 当前比例 {current_ratio:.4f}",
            )

            # 添加到历史记录
            self.hedge_history.append(result)

            self.logger.info(
                f"对冲需求计算完成: {portfolio_id}, "
                f"目标比例: {target_ratio:.4f}, 当前比例: {current_ratio:.4f}, "
                f"建议数量: {len(hedge_recommendations)}"
            )

            return result

        except Exception as exc:
            self.logger.error(f"对冲需求计算失败: {exc}")

            # 返回错误结果
            return HedgeResult(
                id=f"hedge_error_{datetime.now().timestamp()}",
                portfolio_id=portfolio_id,
                timestamp=datetime.now(),
                hedge_type=self.config.hedge_type,
                target_hedge_ratio=0.0,
                current_hedge_ratio=0.0,
                hedge_recommendations=[],
                hedge_positions=[],
                portfolio_delta=0.0,
                portfolio_beta=1.0,
                hedge_effectiveness=0.0,
                total_hedge_cost=0.0,
                risk_reduction=0.0,
                status="error",
                message=str(exc),
            )

    def _calculate_current_hedge_ratio(self) -> float:
        """计算当前对冲比例"""

        if not self.hedge_positions:
            return 0.0

        total_hedge_value = sum(
            pos.position_size * pos.current_price for pos in self.hedge_positions
        )
        # 这里需要投资组合总价值，暂时使用简化的计算
        portfolio_value = 10000000  # 假设投资组合价值

        return total_hedge_value / portfolio_value if portfolio_value > 0 else 0.0

    def _calculate_portfolio_delta(self, portfolio_data: pd.DataFrame) -> float:
        """计算投资组合Delta"""

        if len(portfolio_data) < 2:
            return 0.0

        # 简化的Delta计算
        portfolio_returns = portfolio_data["portfolio_value"].pct_change().dropna()
        if len(portfolio_returns) < 2:
            return 0.0

        # 使用历史波动率作为Delta的近似
        return portfolio_returns.std() * np.sqrt(252)

    def _calculate_portfolio_beta(
        self, portfolio_data: pd.DataFrame, market_data: pd.DataFrame
    ) -> float:
        """计算投资组合Beta"""

        if len(portfolio_data) < 2 or len(market_data) < 2:
            return 1.0

        portfolio_returns = portfolio_data["portfolio_value"].pct_change().dropna()
        market_returns = market_data["benchmark_price"].pct_change().dropna()

        min_length = min(len(portfolio_returns), len(market_returns))
        portfolio_returns = portfolio_returns.tail(min_length)
        market_returns = market_returns.tail(min_length)

        if len(portfolio_returns) < 2:
            return 1.0

        covariance = np.cov(portfolio_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)

        return covariance / market_variance if market_variance > 0 else 1.0

    def _calculate_hedge_effectiveness(self) -> float:
        """计算对冲有效性"""

        if len(self.hedge_history) < 2:
            return 0.0

        # 简化的对冲有效性计算
        recent_results = self.hedge_history[-10:]  # 最近10次对冲结果

        risk_reductions = [
            result.risk_reduction
            for result in recent_results
            if result.risk_reduction > 0
        ]

        if not risk_reductions:
            return 0.0

        return np.mean(risk_reductions)

    def _calculate_risk_reduction(
        self, target_ratio: float, current_ratio: float
    ) -> float:
        """计算风险降低程度"""

        # 简化的风险降低计算
        ratio_diff = abs(target_ratio - current_ratio)
        return min(ratio_diff * 0.5, 1.0)  # 最大风险降低50%

    def update_hedge_positions(self, new_positions: List[HedgePosition]):
        """更新对冲头寸"""

        self.hedge_positions = new_positions
        self.logger.info(f"对冲头寸已更新: {len(new_positions)} 个头寸")

    def get_hedge_statistics(self) -> Dict[str, Any]:
        """获取对冲统计信息"""

        if not self.hedge_history:
            return {}

        recent_results = self.hedge_history[-30:]  # 最近30次结果

        return {
            "total_hedge_operations": len(self.hedge_history),
            "average_hedge_cost": np.mean([r.total_hedge_cost for r in recent_results]),
            "average_hedge_effectiveness": np.mean(
                [r.hedge_effectiveness for r in recent_results]
            ),
            "average_risk_reduction": np.mean(
                [r.risk_reduction for r in recent_results]
            ),
            "current_hedge_positions": len(self.hedge_positions),
            "success_rate": len([r for r in recent_results if r.status == "success"])
            / len(recent_results),
        }


__all__ = [
    "HedgeEngine",
    "HedgeStrategy",
    "HedgeConfig",
    "HedgeResult",
    "HedgePosition",
    "HedgeType",
    "HedgeInstrument",
    "DeltaHedge",
    "BetaHedge",
    "VarianceHedge",
]
