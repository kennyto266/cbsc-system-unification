"""
投資組合管理API
提供6個投資組合相關端點：概覽、配置、優化、風險、調倉、歷史
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..data_adapters.base_adapter import BaseAdapter
from .models.api_response import APIResponse

# ========== Pydantic 模型 ==========


class PortfolioOverviewResponse(BaseModel):
    """組合概覽響應"""

    total_value: float
    total_cost: float
    total_pnl: float
    total_pnl_pct: float
    day_change: float
    day_change_pct: float
    cash: float
    invested: float
    position_count: int
    cash_ratio: float


class AssetAllocationResponse(BaseModel):
    """資產配置響應"""

    symbol: str
    quantity: float
    market_value: float
    weight: float
    avg_cost: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    day_change: float


class OptimizeRequest(BaseModel):
    """優化請求"""

    symbols: List[str] = Field(..., description="股票列表")
    target_return: Optional[float] = Field(None, description="目標收益率")
    max_risk: Optional[float] = Field(None, description="最大風險")
    constraints: Optional[Dict[str, Any]] = Field(None, description="約束條件")


class OptimizationResult(BaseModel):
    """優化結果"""

    allocation: Dict[str, float]
    expected_return: float
    expected_risk: float
    sharpe_ratio: float
    diversification_ratio: float
    turnover: float


class RiskMetricsResponse(BaseModel):
    """風險指標響應"""

    portfolio_value: float
    volatility: float
    var_95: float
    var_99: float
    expected_shortfall: float
    beta: Optional[float] = None
    correlation: Dict[str, float] = {}
    concentration_risk: float
    max_single_position: float


class RebalanceRequest(BaseModel):
    """重新平衡請求"""

    target_weights: Dict[str, float]
    tolerance: float = Field(default=0.02, description="容忍度")
    min_trade_size: float = Field(default=1000, description="最小交易金額")


class RebalanceResult(BaseModel):
    """重新平衡結果"""

    trades: List[Dict[str, Any]]
    total_turnover: float
    estimated_cost: float
    new_weights: Dict[str, float]


class HistoryRequest(BaseModel):
    """歷史記錄請求"""

    period: str = Field(default="1Y", description="期間")
    benchmark: Optional[str] = Field(None, description="基準")


class HistoryResponse(BaseModel):
    """歷史記錄響應"""

    dates: List[str]
    portfolio_values: List[float]
    benchmark_values: Optional[List[float]] = None
    returns: List[float]
    drawdowns: List[float]


# ========== 投資組合管理器 ==========


class PortfolioManager:
    """投資組合管理器"""

    def __init__(self, data_adapter: BaseAdapter):
        self.data_adapter = data_adapter
        self.logger = logging.getLogger("hk_quant_system.portfolio_manager")

    async def get_portfolio_overview(self) -> PortfolioOverviewResponse:
        """獲取組合概覽"""
        # 模擬數據 (實際中會從數據庫獲取)
        total_value = 1500000.0
        total_cost = 1200000.0
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost) * 100
        day_change = 5000.0
        day_change_pct = 0.33
        cash = 300000.0
        invested = total_value - cash
        position_count = 5
        cash_ratio = (cash / total_value) * 100

        return PortfolioOverviewResponse(
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            day_change=day_change,
            day_change_pct=day_change_pct,
            cash=cash,
            invested=invested,
            position_count=position_count,
            cash_ratio=cash_ratio,
        )

    async def get_asset_allocation(self) -> List[AssetAllocationResponse]:
        """獲取資產配置"""
        # 模擬持倉數據
        positions = [
            {"symbol": "0700.hk", "quantity": 2000, "price": 350, "avg_cost": 320},
            {"symbol": "0388.hk", "quantity": 1500, "price": 280, "avg_cost": 260},
            {"symbol": "1398.hk", "quantity": 3000, "price": 45, "avg_cost": 42},
            {"symbol": "0939.hk", "quantity": 2500, "price": 55, "avg_cost": 50},
            {"symbol": "2318.hk", "quantity": 1000, "price": 420, "avg_cost": 380},
        ]

        total_value = sum(p["quantity"] * p["price"] for p in positions)

        allocations = []
        for pos in positions:
            market_value = pos["quantity"] * pos["price"]
            weight = (market_value / total_value) * 100
            unrealized_pnl = (pos["price"] - pos["avg_cost"]) * pos["quantity"]
            unrealized_pnl_pct = (
                (pos["price"] - pos["avg_cost"]) / pos["avg_cost"]
            ) * 100
            day_change = market_value * 0.01  # 假設1 % 日變化

            allocations.append(
                AssetAllocationResponse(
                    symbol=pos["symbol"],
                    quantity=pos["quantity"],
                    market_value=market_value,
                    weight=weight,
                    avg_cost=pos["avg_cost"],
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_pct=unrealized_pnl_pct,
                    day_change=day_change,
                )
            )

        return sorted(allocations, key=lambda x: x.weight, reverse=True)

    async def optimize_portfolio(self, request: OptimizeRequest) -> OptimizationResult:
        """優化投資組合"""
        # 簡化的優化算法 (實際中會使用馬科維茨優化等)
        n_assets = len(request.symbols)

        # 隨機分配權重
        weights = np.random.dirichlet(np.ones(n_assets))
        allocation = {
            symbol: float(weight) for symbol, weight in zip(request.symbols, weights)
        }

        # 計算預期收益和風險
        expected_return = 0.08  # 8% 年化收益
        expected_risk = 0.15  # 15% 波動率
        sharpe_ratio = expected_return / expected_risk
        diversification_ratio = 1.0 / np.sqrt(n_assets)
        turnover = 0.05  # 5% 周轉率

        return OptimizationResult(
            allocation=allocation,
            expected_return=expected_return * 100,
            expected_risk=expected_risk * 100,
            sharpe_ratio=sharpe_ratio,
            diversification_ratio=diversification_ratio,
            turnover=turnover,
        )

    async def get_risk_metrics(self) -> RiskMetricsResponse:
        """獲取風險指標"""
        portfolio_value = 1500000.0
        volatility = 0.18  # 18% 年化波動率
        var_95 = portfolio_value * 0.05  # 5% VaR
        var_99 = portfolio_value * 0.08  # 8% VaR
        expected_shortfall = portfolio_value * 0.06  # 期望短缺

        correlation = {
            "0700.hk": 1.0,
            "0388.hk": 0.75,
            "1398.hk": 0.65,
            "0939.hk": 0.70,
            "2318.hk": 0.80,
        }

        concentration_risk = 0.35  # 最大權重
        max_single_position = 0.30  # 30%

        return RiskMetricsResponse(
            portfolio_value=portfolio_value,
            volatility=volatility * 100,
            var_95=var_95,
            var_99=var_99,
            expected_shortfall=expected_shortfall,
            beta=1.2,  # 相對市場Beta
            correlation=correlation,
            concentration_risk=concentration_risk,
            max_single_position=max_single_position,
        )

    async def rebalance_portfolio(self, request: RebalanceRequest) -> RebalanceResult:
        """重新平衡投資組合"""
        # 模擬當前權重
        current_weights = {
            "0700.hk": 0.32,
            "0388.hk": 0.28,
            "1398.hk": 0.22,
            "0939.hk": 0.18,
        }

        # 計算需要調整的交易
        trades = []
        total_turnover = 0.0

        for symbol, target_weight in request.target_weights.items():
            current_weight = current_weights.get(symbol, 0.0)
            diff = target_weight - current_weight

            if abs(diff) > request.tolerance:
                trade_value = diff * 1500000  # 假設組合價值150萬
                trades.append(
                    {
                        "symbol": symbol,
                        "action": "buy" if diff > 0 else "sell",
                        "current_weight": current_weight * 100,
                        "target_weight": target_weight * 100,
                        "weight_change": diff * 100,
                        "trade_value": trade_value,
                    }
                )
                total_turnover += abs(diff)

        estimated_cost = total_turnover * 1500000 * 0.001  # 0.1 % 交易成本

        return RebalanceResult(
            trades=trades,
            total_turnover=total_turnover,
            estimated_cost=estimated_cost,
            new_weights=request.target_weights,
        )

    async def get_portfolio_history(self, request: HistoryRequest) -> HistoryResponse:
        """獲取投資組合歷史"""
        # 生成模擬歷史數據
        dates = (
            pd.date_range(end=datetime.now(), periods=252, freq="D")  # 一年交易日
            .strftime("%Y-%m-%d")
            .tolist()
        )

        # 模擬組合價值變化 (隨機遊走)
        portfolio_values = []
        value = 1000000
        for i in range(len(dates)):
            daily_return = np.random.normal(0.0005, 0.01)  # 平均日收益和波動率
            value *= 1 + daily_return
            portfolio_values.append(value)

        # 基準數據 (可選)
        benchmark_values = None
        if request.benchmark:
            benchmark_values = []
            bench_value = 1000000
            for i in range(len(dates)):
                bench_daily_return = np.random.normal(0.0003, 0.012)
                bench_value *= 1 + bench_daily_return
                benchmark_values.append(bench_value)

        # 計算收益率
        returns = [0] + [
            (portfolio_values[i] / portfolio_values[i - 1] - 1)
            for i in range(1, len(portfolio_values))
        ]

        # 計算回撤
        peak = np.maximum.accumulate(portfolio_values)
        drawdowns = [
            (portfolio_values[i] - peak[i]) / peak[i]
            for i in range(len(portfolio_values))
        ]

        return HistoryResponse(
            dates=dates,
            portfolio_values=portfolio_values,
            benchmark_values=benchmark_values,
            returns=returns,
            drawdowns=drawdowns,
        )


# ========== FastAPI 路由 ==========


def create_portfolio_router(data_adapter: BaseAdapter) -> APIRouter:
    """創建投資組合路由"""
    router = APIRouter(prefix="/api / v2 / portfolio", tags=["portfolio"])
    logger = logging.getLogger("hk_quant_system.portfolio_api")

    # 投資組合管理器
    portfolio_manager = PortfolioManager(data_adapter)

    @router.get("/overview", response_model=APIResponse)
    async def get_portfolio_overview():
        """組合概覽"""
        try:
            overview = await portfolio_manager.get_portfolio_overview()
            return APIResponse(
                success=True, data=overview.dict(), message="組合概覽查詢成功"
            )
        except Exception as e:
            logger.error(f"組合概覽查詢失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/allocation", response_model=APIResponse)
    async def get_asset_allocation():
        """資產配置"""
        try:
            allocations = await portfolio_manager.get_asset_allocation()
            return APIResponse(
                success=True,
                data={
                    "allocations": [a.dict() for a in allocations],
                    "total_value": sum(a.market_value for a in allocations),
                },
                message="資產配置查詢成功",
            )
        except Exception as e:
            logger.error(f"資產配置查詢失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/optimize", response_model=APIResponse)
    async def optimize_portfolio(request: OptimizeRequest):
        """組合優化"""
        try:
            result = await portfolio_manager.optimize_portfolio(request)
            return APIResponse(success=True, data=result.dict(), message="組合優化完成")
        except Exception as e:
            logger.error(f"組合優化失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/risk", response_model=APIResponse)
    async def get_portfolio_risk():
        """風險指標"""
        try:
            risk = await portfolio_manager.get_risk_metrics()
            return APIResponse(
                success=True, data=risk.dict(), message="風險指標查詢成功"
            )
        except Exception as e:
            logger.error(f"風險指標查詢失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/rebalance", response_model=APIResponse)
    async def rebalance_portfolio_endpoint(request: RebalanceRequest):
        """重新平衡"""
        try:
            result = await portfolio_manager.rebalance_portfolio(request)
            return APIResponse(success=True, data=result.dict(), message="重新平衡完成")
        except Exception as e:
            logger.error(f"重新平衡失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/history", response_model=APIResponse)
    async def get_portfolio_history(
        period: str = "1Y", benchmark: Optional[str] = None
    ):
        """歷史記錄"""
        try:
            request = HistoryRequest(period=period, benchmark=benchmark)
            history = await portfolio_manager.get_portfolio_history(request)
            return APIResponse(
                success=True, data=history.dict(), message="歷史記錄查詢成功"
            )
        except Exception as e:
            logger.error(f"歷史記錄查詢失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
