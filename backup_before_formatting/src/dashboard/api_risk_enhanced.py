"""
增強版風險管理API
提供5個風險管理端點：指標、VaR計算、告警、限額、報告
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from ..data_adapters.base_adapter import BaseAdapter
from .models.api_response import APIResponse

# ========== Pydantic 模型 ==========


class RiskMetricResponse(BaseModel):
    """風險指標響應"""

    metric_name: str
    current_value: float
    threshold: float
    status: str  # "normal", "warning", "critical"
    change_1d: float
    change_1w: float
    change_1m: float
    percentile: float


class VaRCalculationRequest(BaseModel):
    """VaR計算請求"""

    symbols: List[str]
    portfolio_value: float
    confidence_level: float = Field(default=0.95, ge=0.90, le=0.99)
    time_horizon: int = Field(default=1, ge=1, le=10, description="時間範圍 (天)")
    method: str = Field(default="historical", description="計算方法")


class VaRResult(BaseModel):
    """VaR結果"""

    symbol: str
    var_value: float
    var_pct: float
    confidence_level: float
    time_horizon: int
    method: str


class VaRResponse(BaseModel):
    """VaR響應"""

    portfolio_var: VaRResult
    individual_vars: List[VaRResult]
    expected_shortfall: float
    diversification_benefit: float
    tail_risk: float
    calculation_date: datetime


class RiskAlertRequest(BaseModel):
    """風險告警請求"""

    alert_type: str = Field(..., description="告警類型")
    threshold: float = Field(..., description="閾值")
    action: str = Field(..., description="行動")


class RiskAlertResponse(BaseModel):
    """風險告警響應"""

    alert_id: str
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    message: str
    triggered_at: datetime
    status: str  # "active", "acknowledged", "resolved"
    symbol: Optional[str] = None
    metric: Optional[str] = None


class RiskLimitRequest(BaseModel):
    """風險限額請求"""

    limit_type: str = Field(..., description="限額類型")
    symbol: Optional[str] = Field(None, description="股票代碼")
    max_exposure: float = Field(..., gt=0, description="最大敞口")
    max_loss: float = Field(..., gt=0, description="最大損失")


class RiskLimitResponse(BaseModel):
    """風險限額響應"""

    limit_id: str
    limit_type: str
    symbol: Optional[str] = None
    max_value: float
    current_value: float
    utilization_pct: float
    status: str  # "ok", "warning", "breached"
    created_at: datetime


class RiskReportRequest(BaseModel):
    """風險報告請求"""

    report_type: str = Field(..., description="報告類型")
    period: str = Field(default="1D", description="期間")
    symbols: Optional[List[str]] = Field(None, description="股票列表")
    format: str = Field(default="json", description="格式")


class RiskReportResponse(BaseModel):
    """風險報告響應"""

    report_id: str
    report_type: str
    period: str
    generated_at: datetime
    summary: Dict[str, Any]
    details: Dict[str, Any]
    download_url: Optional[str] = None


# ========== 風險管理器 ==========


class RiskManager:
    """風險管理器"""

    def __init__(self, data_adapter: BaseAdapter):
        self.data_adapter = data_adapter
        self.logger = logging.getLogger("hk_quant_system.risk_manager")

    async def get_risk_metrics(self) -> List[RiskMetricResponse]:
        """獲取風險指標"""
        metrics = [
            RiskMetricResponse(
                metric_name="組合波動率",
                current_value=18.5,
                threshold=25.0,
                status="normal",
                change_1d=-0.5,
                change_1w=1.2,
                change_1m=3.5,
                percentile=65.0,
            ),
            RiskMetricResponse(
                metric_name="最大回撤",
                current_value=8.2,
                threshold=15.0,
                status="normal",
                change_1d=0.3,
                change_1w=-0.8,
                change_1m=2.1,
                percentile=45.0,
            ),
            RiskMetricResponse(
                metric_name="VaR (95%)",
                current_value=75000,
                threshold=100000,
                status="normal",
                change_1d=2000,
                change_1w=-3000,
                change_1m=5000,
                percentile=55.0,
            ),
            RiskMetricResponse(
                metric_name="集中度風險",
                current_value=35.0,
                threshold=30.0,
                status="warning",
                change_1d=0.5,
                change_1w=2.0,
                change_1m=5.0,
                percentile=78.0,
            ),
            RiskMetricResponse(
                metric_name="流動性風險",
                current_value=12.0,
                threshold=20.0,
                status="normal",
                change_1d=-1.0,
                change_1w=0.5,
                change_1m=-2.0,
                percentile=40.0,
            ),
        ]
        return metrics

    async def calculate_var(self, request: VaRCalculationRequest) -> VaRResponse:
        """計算VaR"""
        try:
            # 模擬歷史數據 VaR 計算
            portfolio_var = VaRResult(
                symbol="PORTFOLIO",
                var_value=100000.0 * (1 - request.confidence_level),
                var_pct=(1 - request.confidence_level) * 100,
                confidence_level=request.confidence_level,
                time_horizon=request.time_horizon,
                method=request.method,
            )

            # 個股 VaR
            individual_vars = []
            for symbol in request.symbols:
                symbol_var = VaRResult(
                    symbol=symbol,
                    var_value=100000.0 * 0.05,  # 假設5%
                    var_pct=5.0,
                    confidence_level=request.confidence_level,
                    time_horizon=request.time_horizon,
                    method=request.method,
                )
                individual_vars.append(symbol_var)

            # 期望短缺
            expected_shortfall = portfolio_var.var_value * 1.3

            # 分散化收益
            diversification_benefit = 0.15  # 15%

            # 尾部風險
            tail_risk = 0.08  # 8%

            return VaRResponse(
                portfolio_var=portfolio_var,
                individual_vars=individual_vars,
                expected_shortfall=expected_shortfall,
                diversification_benefit=diversification_benefit,
                tail_risk=tail_risk,
                calculation_date=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"VaR計算失敗: {str(e)}")
            raise

    async def get_risk_alerts(self) -> List[RiskAlertResponse]:
        """獲取風險告警"""
        alerts = [
            RiskAlertResponse(
                alert_id="ALERT001",
                alert_type="concentration",
                severity="warning",
                message="單一持倉權重超過30%",
                triggered_at=datetime.now() - timedelta(hours=2),
                status="active",
                symbol="0700.hk",
                metric="position_weight",
            ),
            RiskAlertResponse(
                alert_id="ALERT002",
                alert_type="volatility",
                severity="medium",
                message="組合波動率快速上升",
                triggered_at=datetime.now() - timedelta(hours=5),
                status="acknowledged",
                metric="volatility",
            ),
        ]
        return alerts

    async def create_alert(self, request: RiskAlertRequest) -> RiskAlertResponse:
        """創建風險告警"""
        alert = RiskAlertResponse(
            alert_id=f"ALERT{datetime.now().strftime('%Y % m % d % H % M % S')}",
            alert_type=request.alert_type,
            severity="medium",
            message=f"告警已創建：{request.alert_type} 閾值 {request.threshold}",
            triggered_at=datetime.now(),
            status="active",
        )
        return alert

    async def get_risk_limits(self) -> List[RiskLimitResponse]:
        """獲取風險限額"""
        limits = [
            RiskLimitResponse(
                limit_id="LIMIT001",
                limit_type="position_limit",
                symbol="0700.hk",
                max_value=500000,
                current_value=350000,
                utilization_pct=70.0,
                status="ok",
                created_at=datetime.now() - timedelta(days=30),
            ),
            RiskLimitResponse(
                limit_id="LIMIT002",
                limit_type="sector_limit",
                max_value=750000,
                current_value=680000,
                utilization_pct=90.7,
                status="warning",
                created_at=datetime.now() - timedelta(days=30),
            ),
            RiskLimitResponse(
                limit_id="LIMIT003",
                limit_type="daily_loss_limit",
                max_value=50000,
                current_value=35000,
                utilization_pct=70.0,
                status="ok",
                created_at=datetime.now() - timedelta(days=30),
            ),
        ]
        return limits

    async def set_risk_limit(self, request: RiskLimitRequest) -> RiskLimitResponse:
        """設置風險限額"""
        limit = RiskLimitResponse(
            limit_id=f"LIMIT{datetime.now().strftime('%Y % m % d % H % M % S')}",
            limit_type=request.limit_type,
            symbol=request.symbol,
            max_value=request.max_exposure,
            current_value=0.0,
            utilization_pct=0.0,
            status="ok",
            created_at=datetime.now(),
        )
        return limit

    async def generate_risk_report(
        self, request: RiskReportRequest
    ) -> RiskReportResponse:
        """生成風險報告"""
        report_id = f"RPT{datetime.now().strftime('%Y % m % d % H % M % S')}"

        summary = {
            "total_value": 1500000.0,
            "total_risk_score": 65,
            "risk_level": "Medium",
            "active_alerts": 2,
            "breached_limits": 0,
            "var_95": 75000,
            "max_drawdown": 8.2,
        }

        details = {
            "position_concentration": {
                "top_5_holdings": 65.0,
                "largest_position": 32.0,
                "diversification_ratio": 1.85,
            },
            "risk_metrics": {
                "volatility": 18.5,
                "sharpe_ratio": 1.2,
                "calmar_ratio": 0.85,
                "sortino_ratio": 1.5,
            },
            "sector_allocation": {
                "technology": 35.0,
                "finance": 30.0,
                "industrial": 20.0,
                "others": 15.0,
            },
        }

        return RiskReportResponse(
            report_id=report_id,
            report_type=request.report_type,
            period=request.period,
            generated_at=datetime.now(),
            summary=summary,
            details=details,
            download_url=f"/api / v2 / risk / reports/{report_id}/download",
        )


# ========== FastAPI 路由 ==========


def create_risk_enhanced_router(data_adapter: BaseAdapter) -> APIRouter:
    """創建增強風險管理路由"""
    router = APIRouter(prefix="/api / v2 / risk", tags=["enhanced_risk"])
    logger = logging.getLogger("hk_quant_system.risk_enhanced_api")

    # 風險管理器
    risk_manager = RiskManager(data_adapter)

    @router.get("/metrics", response_model=APIResponse)
    async def get_risk_metrics():
        """風險指標"""
        try:
            metrics = await risk_manager.get_risk_metrics()
            return APIResponse(
                success=True,
                data={
                    "metrics": [m.dict() for m in metrics],
                    "total_count": len(metrics),
                },
                message="風險指標查詢成功",
            )
        except Exception as e:
            logger.error(f"風險指標查詢失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/var", response_model=APIResponse)
    async def calculate_var_endpoint(request: VaRCalculationRequest):
        """VaR計算"""
        try:
            result = await risk_manager.calculate_var(request)
            return APIResponse(success=True, data=result.dict(), message="VaR計算完成")
        except Exception as e:
            logger.error(f"VaR計算失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/alerts", response_model=APIResponse)
    async def get_risk_alerts():
        """風險告警"""
        try:
            alerts = await risk_manager.get_risk_alerts()
            return APIResponse(
                success=True,
                data={
                    "alerts": [a.dict() for a in alerts],
                    "active_count": len([a for a in alerts if a.status == "active"]),
                },
                message="風險告警查詢成功",
            )
        except Exception as e:
            logger.error(f"風險告警查詢失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/alerts", response_model=APIResponse)
    async def create_alert_endpoint(request: RiskAlertRequest):
        """創建風險告警"""
        try:
            alert = await risk_manager.create_alert(request)
            return APIResponse(
                success=True, data=alert.dict(), message="風險告警創建成功"
            )
        except Exception as e:
            logger.error(f"創建風險告警失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/limits", response_model=APIResponse)
    async def get_risk_limits():
        """風險限額"""
        try:
            limits = await risk_manager.get_risk_limits()
            return APIResponse(
                success=True,
                data={
                    "limits": [l.dict() for l in limits],
                    "total_count": len(limits),
                    "active_limits": len(
                        [l for l in limits if l.status in ["ok", "warning"]]
                    ),
                },
                message="風險限額查詢成功",
            )
        except Exception as e:
            logger.error(f"風險限額查詢失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/limits", response_model=APIResponse)
    async def set_risk_limit_endpoint(request: RiskLimitRequest):
        """設置風險限額"""
        try:
            limit = await risk_manager.set_risk_limit(request)
            return APIResponse(
                success=True, data=limit.dict(), message="風險限額設置成功"
            )
        except Exception as e:
            logger.error(f"設置風險限額失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/reports", response_model=APIResponse)
    async def generate_risk_report_endpoint(request: RiskReportRequest):
        """生成風險報告"""
        try:
            report = await risk_manager.generate_risk_report(request)
            return APIResponse(
                success=True, data=report.dict(), message="風險報告生成成功"
            )
        except Exception as e:
            logger.error(f"生成風險報告失敗: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
