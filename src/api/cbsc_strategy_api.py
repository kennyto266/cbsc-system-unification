#!/usr/bin/env python3
"""
CBSC核心策略管理API (Task #005)
CBSC Core Strategy Management API

統一的CBSC策略管理API，整合現有功能到新的統一架構中
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
import json
import uuid

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np

# 導入現有模型
from .strategy_management_api import (
    Strategy, StrategyType, StrategyStatus, StrategyParameters,
    StrategySignal, StrategyPerformance, StrategyExecutionRequest,
    StrategyExecutionResult, CreateStrategyRequest, UpdateStrategyRequest,
    DataCompatibilityAdapter, StrategyTemplates, CBSCStrategyTemplate
)

# 導入認證系統
try:
    from auth_simple import User, get_current_user
except ImportError:
    # 如果auth_simple不在當前目錄，嘗試從上層目錄導入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from auth_simple import User, get_current_user

logger = logging.getLogger(__name__)

# ============================================================================
# 路由器設置 (Router Setup)
# ============================================================================

router = APIRouter(prefix="/api/strategies", tags=["CBSC策略管理"])

# ============================================================================
# 核心數據模型 (Core Data Models)
# ============================================================================

class StrategyExecutionStatus(str, Enum):
    """策略執行狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class StrategyRiskMetrics(BaseModel):
    """策略風險指標"""
    var_95: float = Field(..., description="95% VaR")
    var_99: float = Field(..., description="99% VaR")
    volatility: float = Field(..., description="波動率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float = Field(..., description="索提諾比率")
    calmar_ratio: float = Field(..., description="卡瑪比率")
    beta: float = Field(..., description="Beta值")
    correlation_to_market: float = Field(..., description="與市場相關性")
    tracking_error: float = Field(..., description="跟踪誤差")

class StrategyRealTimeStatus(BaseModel):
    """策略實時狀態"""
    strategy_id: str
    is_running: bool
    current_position: Optional[str] = None
    last_signal: Optional[StrategySignal] = None
    current_pnl: float = 0.0
    daily_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    risk_metrics: Optional[StrategyRiskMetrics] = None
    last_updated: datetime
    execution_status: StrategyExecutionStatus

class StrategyConfigValidation(BaseModel):
    """策略配置驗證結果"""
    is_valid: bool
    validation_errors: List[str] = []
    validation_warnings: List[str] = []
    parameter_ranges: Dict[str, Dict[str, Any]] = {}
    recommended_parameters: Optional[StrategyParameters] = None

class StrategyExecutionReport(BaseModel):
    """策略執行報告"""
    execution_id: str
    strategy_id: str
    execution_period: Dict[str, datetime]
    total_signals: int
    executed_signals: int
    success_rate: float
    performance_summary: StrategyPerformance
    risk_analysis: StrategyRiskMetrics
    execution_log: List[Dict[str, Any]]
    created_at: datetime

# ============================================================================
# 策略管理服務 (Strategy Management Service)
# ============================================================================

class CBSCStrategyManager:
    """CBSC策略管理器"""

    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.strategy_statuses: Dict[str, StrategyRealTimeStatus] = {}
        self.execution_history: Dict[str, List[StrategyExecutionResult]] = {}
        self.strategy_templates: Dict[str, CBSCStrategyTemplate] = {}
        self.performance_cache: Dict[str, StrategyPerformance] = {}
        self.risk_metrics_cache: Dict[str, StrategyRiskMetrics] = {}

        # 初始化模板
        self._initialize_templates()

        # 初始化WebSocket管理器
        self.websocket_manager = None

    def _initialize_templates(self):
        """初始化策略模板"""
        templates = StrategyTemplates.get_all_templates()
        for template in templates:
            self.strategy_templates[template.id] = template
            logger.info(f"已加載策略模板: {template.name}")

    async def create_strategy(self, request: CreateStrategyRequest, user_id: int) -> Strategy:
        """創建新策略"""
        try:
            # 生成策略ID
            strategy_id = f"cbsc_{request.strategy_type.value}_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 基於模板創建策略
            template = None
            if request.template_id and request.template_id in self.strategy_templates:
                template = self.strategy_templates[request.template_id]
                parameters = template.default_parameters
                # 覆蓋用戶提供的參數
                if request.parameters:
                    parameters_dict = parameters.dict()
                    parameters_dict.update(request.parameters.dict())
                    parameters = StrategyParameters(**parameters_dict)
            else:
                parameters = request.parameters

            # 創建策略
            strategy = Strategy(
                id=strategy_id,
                name=request.name,
                description=request.description,
                strategy_type=request.strategy_type,
                parameters=parameters,
                status=StrategyStatus.INACTIVE,
                is_active=False
            )

            # 驗證策略配置
            validation_result = await self.validate_strategy_config(strategy)
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=400,
                    detail=f"策略配置驗證失敗: {'; '.join(validation_result.validation_errors)}"
                )

            # 保存策略
            self.strategies[strategy_id] = strategy

            # 初始化狀態
            self.strategy_statuses[strategy_id] = StrategyRealTimeStatus(
                strategy_id=strategy_id,
                is_running=False,
                current_pnl=0.0,
                daily_pnl=0.0,
                unrealized_pnl=0.0,
                last_updated=datetime.now(),
                execution_status=StrategyExecutionStatus.PENDING
            )

            # 初始化執行歷史
            self.execution_history[strategy_id] = []

            logger.info(f"用戶 {user_id} 創建策略成功: {strategy_id}")
            return strategy

        except Exception as e:
            logger.error(f"創建策略失敗: {e}")
            raise HTTPException(status_code=500, detail=f"創建策略失敗: {str(e)}")

    async def get_strategies(
        self,
        user_id: int,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> List[Strategy]:
        """獲取策略列表"""
        try:
            # 過濾用戶策略
            user_strategies = [
                strategy for strategy in self.strategies.values()
                if f"_{user_id}_" in strategy.id
            ]

            # 應用過濾條件
            if strategy_type:
                user_strategies = [s for s in user_strategies if s.strategy_type == strategy_type]

            if status:
                user_strategies = [s for s in user_strategies if s.status == status]

            if is_active is not None:
                user_strategies = [s for s in user_strategies if s.is_active == is_active]

            # 分頁
            start_index = (page - 1) * page_size
            end_index = start_index + page_size

            return user_strategies[start_index:end_index]

        except Exception as e:
            logger.error(f"獲取策略列表失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取策略列表失敗: {str(e)}")

    async def get_strategy(self, strategy_id: str, user_id: int) -> Strategy:
        """獲取策略詳情"""
        try:
            if strategy_id not in self.strategies:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise HTTPException(status_code=403, detail="無權限訪問此策略")

            return self.strategies[strategy_id]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"獲取策略詳情失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取策略詳情失敗: {str(e)}")

    async def update_strategy(
        self,
        strategy_id: str,
        request: UpdateStrategyRequest,
        user_id: int
    ) -> Strategy:
        """更新策略"""
        try:
            if strategy_id not in self.strategies:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise HTTPException(status_code=403, detail="無權限訪問此策略")

            strategy = self.strategies[strategy_id]

            # 更新字段
            if request.name is not None:
                strategy.name = request.name

            if request.description is not None:
                strategy.description = request.description

            if request.parameters is not None:
                strategy.parameters = request.parameters

            if request.status is not None:
                strategy.status = request.status

            if request.is_active is not None:
                strategy.is_active = request.is_active

            strategy.updated_at = datetime.now()

            # 重新驗證配置
            validation_result = await self.validate_strategy_config(strategy)
            if not validation_result.is_valid:
                logger.warning(f"策略配置驗證失敗: {validation_result.validation_errors}")

            logger.info(f"用戶 {user_id} 更新策略成功: {strategy_id}")
            return strategy

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新策略失敗: {e}")
            raise HTTPException(status_code=500, detail=f"更新策略失敗: {str(e)}")

    async def delete_strategy(self, strategy_id: str, user_id: int) -> bool:
        """刪除策略"""
        try:
            if strategy_id not in self.strategies:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise HTTPException(status_code=403, detail="無權限訪問此策略")

            # 檢查策略是否正在運行
            if strategy_id in self.strategy_statuses and self.strategy_statuses[strategy_id].is_running:
                raise HTTPException(status_code=400, detail="無法刪除正在運行的策略，請先停止策略")

            # 刪除策略數據
            del self.strategies[strategy_id]
            if strategy_id in self.strategy_statuses:
                del self.strategy_statuses[strategy_id]
            if strategy_id in self.execution_history:
                del self.execution_history[strategy_id]
            if strategy_id in self.performance_cache:
                del self.performance_cache[strategy_id]
            if strategy_id in self.risk_metrics_cache:
                del self.risk_metrics_cache[strategy_id]

            logger.info(f"用戶 {user_id} 刪除策略成功: {strategy_id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"刪除策略失敗: {e}")
            raise HTTPException(status_code=500, detail=f"刪除策略失敗: {str(e)}")

    async def execute_strategy(
        self,
        strategy_id: str,
        execution_request: StrategyExecutionRequest,
        user_id: int
    ) -> StrategyExecutionResult:
        """執行策略"""
        try:
            if strategy_id not in self.strategies:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise HTTPException(status_code=403, detail="無權限訪問此策略")

            strategy = self.strategies[strategy_id]

            # 生成執行ID
            execution_id = f"exec_{strategy_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 更新策略狀態
            strategy.status = StrategyStatus.ACTIVE
            strategy.is_active = True
            strategy.last_executed = datetime.now()

            # 更新實時狀態
            if strategy_id in self.strategy_statuses:
                self.strategy_statuses[strategy_id].is_running = True
                self.strategy_statuses[strategy_id].execution_status = StrategyExecutionStatus.RUNNING

            # 模擬執行結果（實際應該調用策略引擎）
            execution_result = await self._simulate_strategy_execution(
                execution_id, strategy, execution_request
            )

            # 保存執行歷史
            if strategy_id not in self.execution_history:
                self.execution_history[strategy_id] = []
            self.execution_history[strategy_id].append(execution_result)

            logger.info(f"用戶 {user_id} 執行策略成功: {strategy_id}")
            return execution_result

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"執行策略失敗: {e}")
            raise HTTPException(status_code=500, detail=f"執行策略失敗: {str(e)}")

    async def stop_strategy(self, strategy_id: str, user_id: int) -> bool:
        """停止策略執行"""
        try:
            if strategy_id not in self.strategies:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise HTTPException(status_code=403, detail="無權限訪問此策略")

            strategy = self.strategies[strategy_id]

            # 更新策略狀態
            strategy.status = StrategyStatus.INACTIVE
            strategy.is_active = False

            # 更新實時狀態
            if strategy_id in self.strategy_statuses:
                self.strategy_statuses[strategy_id].is_running = False
                self.strategy_statuses[strategy_id].execution_status = StrategyExecutionStatus.CANCELLED

            logger.info(f"用戶 {user_id} 停止策略成功: {strategy_id}")
            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"停止策略失敗: {e}")
            raise HTTPException(status_code=500, detail=f"停止策略失敗: {str(e)}")

    async def get_strategy_status(self, strategy_id: str, user_id: int) -> StrategyRealTimeStatus:
        """獲取策略狀態"""
        try:
            if strategy_id not in self.strategies:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise HTTPException(status_code=403, detail="無權限訪問此策略")

            return self.strategy_statuses.get(strategy_id, StrategyRealTimeStatus(
                strategy_id=strategy_id,
                is_running=False,
                last_updated=datetime.now(),
                execution_status=StrategyExecutionStatus.PENDING
            ))

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"獲取策略狀態失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取策略狀態失敗: {str(e)}")

    async def get_strategy_metrics(self, strategy_id: str, user_id: int) -> StrategyPerformance:
        """獲取策略性能指標"""
        try:
            if strategy_id not in self.strategies:
                raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

            # 驗證權限
            if f"_{user_id}_" not in strategy_id:
                raise HTTPException(status_code=403, detail="無權限訪問此策略")

            # 檢查緩存
            if strategy_id in self.performance_cache:
                return self.performance_cache[strategy_id]

            # 計算性能指標（實際應該從執行歷史計算）
            performance = await self._calculate_strategy_performance(strategy_id)

            # 緩存結果
            self.performance_cache[strategy_id] = performance

            return performance

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"獲取策略性能指標失敗: {e}")
            raise HTTPException(status_code=500, detail=f"獲取策略性能指標失敗: {str(e)}")

    async def validate_strategy_config(self, strategy: Strategy) -> StrategyConfigValidation:
        """驗證策略配置"""
        try:
            validation_errors = []
            validation_warnings = []

            # 參數範圍驗證
            params = strategy.parameters

            if params.rsi_period and (params.rsi_period < 2 or params.rsi_period > 50):
                validation_errors.append("RSI週期必須在2-50之間")

            if params.oversold_threshold and (params.oversold_threshold < 0 or params.oversold_threshold >= params.overbought_threshold):
                validation_errors.append("超賣閾值必須小於超買閾值")

            if params.fast_period and params.slow_period and params.fast_period >= params.slow_period:
                validation_errors.append("快速週期必須小於慢速週期")

            # 策略類型特定驗證
            if strategy.strategy_type == StrategyType.DIRECT_RSI:
                if not params.rsi_period or not params.oversold_threshold or not params.overbought_threshold:
                    validation_errors.append("直接RSI策略需要設置RSI週期、超賣和超買閾值")

            # 警告檢查
            if params.weight_sentiment and params.weight_sentiment > 0.8:
                validation_warnings.append("情緒權重過高可能增加策略風險")

            # 推薦參數
            recommended_parameters = None
            if validation_errors:
                template = self.strategy_templates.get(f"{strategy.strategy_type.value}_template")
                if template:
                    recommended_parameters = template.default_parameters

            return StrategyConfigValidation(
                is_valid=len(validation_errors) == 0,
                validation_errors=validation_errors,
                validation_warnings=validation_warnings,
                recommended_parameters=recommended_parameters
            )

        except Exception as e:
            logger.error(f"驗證策略配置失敗: {e}")
            return StrategyConfigValidation(
                is_valid=False,
                validation_errors=[f"驗證過程中發生錯誤: {str(e)}"]
            )

    async def get_strategy_templates(self) -> List[CBSCStrategyTemplate]:
        """獲取策略模板列表"""
        return list(self.strategy_templates.values())

    async def _simulate_strategy_execution(
        self,
        execution_id: str,
        strategy: Strategy,
        execution_request: StrategyExecutionRequest
    ) -> StrategyExecutionResult:
        """模擬策略執行（實際應該調用真實的策略引擎）"""
        try:
            # 模擬執行延遲
            await asyncio.sleep(0.1)

            # 生成模擬信號
            signals = []
            base_time = datetime.now() - timedelta(days=30)

            for i in range(10):  # 生成10個模擬信號
                signal = StrategySignal(
                    signal_id=f"{execution_id}_signal_{i+1:03d}",
                    strategy_type=strategy.strategy_type,
                    signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                    strength=75.0 + np.random.normal(0, 10),
                    confidence=80.0 + np.random.normal(0, 10),
                    timestamp=base_time + timedelta(days=i*3),
                    market_data={
                        "price": 150.0 + np.random.normal(0, 10),
                        "volume": 1000000 + np.random.normal(0, 100000),
                        "rsi": 50 + np.random.normal(0, 20)
                    },
                    parameters=strategy.parameters,
                    metadata={"execution_id": execution_id, "simulated": True}
                )
                signals.append(signal)

            # 計算模擬性能
            performance = StrategyPerformance(
                strategy_type=strategy.strategy_type,
                total_return=np.random.normal(0.05, 0.15),  # 5% +/- 15%
                annual_return=np.random.normal(0.08, 0.20),  # 8% +/- 20%
                sharpe_ratio=np.random.normal(1.2, 0.5),
                max_drawdown=abs(np.random.normal(0.10, 0.05)),  # 10% +/- 5%
                win_rate=np.random.uniform(0.4, 0.7),  # 40-70%
                profit_factor=np.random.uniform(1.1, 2.5),
                calmar_ratio=np.random.normal(0.8, 0.3),
                total_trades=len(signals),
                profit_trades=int(len(signals) * np.random.uniform(0.4, 0.7)),
                avg_profit=np.random.normal(0.02, 0.01),  # 2% +/- 1%
                avg_loss=np.random.normal(-0.015, 0.008),  # -1.5% +/- 0.8%
            )

            return StrategyExecutionResult(
                execution_id=execution_id,
                strategy_id=strategy.id,
                status="completed",
                start_time=execution_request.start_time or datetime.now() - timedelta(days=30),
                end_time=execution_request.end_time or datetime.now(),
                signals=signals,
                performance=performance,
                execution_metadata={
                    "execution_mode": execution_request.execution_mode,
                    "data_source": execution_request.data_source,
                    "simulated": True,
                    "total_processing_time": 0.1
                }
            )

        except Exception as e:
            logger.error(f"模擬策略執行失敗: {e}")
            return StrategyExecutionResult(
                execution_id=execution_id,
                strategy_id=strategy.id,
                status="failed",
                start_time=datetime.now(),
                error_message=f"執行失敗: {str(e)}",
                execution_metadata={"error": True}
            )

    async def _calculate_strategy_performance(self, strategy_id: str) -> StrategyPerformance:
        """計算策略性能指標"""
        try:
            execution_history = self.execution_history.get(strategy_id, [])

            if not execution_history:
                # 返回默認性能
                return StrategyPerformance(
                    strategy_type=StrategyType.DIRECT_RSI,
                    total_return=0.0,
                    annual_return=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    win_rate=0.0,
                    profit_factor=0.0,
                    calmar_ratio=0.0,
                    total_trades=0,
                    profit_trades=0,
                    avg_profit=0.0,
                    avg_loss=0.0,
                )

            # 聚合所有執行結果的性能
            total_return = 0.0
            total_trades = 0
            profit_trades = 0

            for result in execution_history:
                if result.performance:
                    total_return += result.performance.total_return
                    total_trades += result.performance.total_trades
                    profit_trades += result.performance.profit_trades

            # 計算平均性能
            avg_return = total_return / len(execution_history) if execution_history else 0.0
            win_rate = profit_trades / total_trades if total_trades > 0 else 0.0

            return StrategyPerformance(
                strategy_type=self.strategies[strategy_id].strategy_type,
                total_return=avg_return,
                annual_return=avg_return * 252 / 30,  # 簡單年化
                sharpe_ratio=np.random.normal(1.0, 0.3),  # 模擬值
                max_drawdown=abs(np.random.normal(0.08, 0.03)),  # 模擬值
                win_rate=win_rate,
                profit_factor=1.0 + win_rate,  # 簡化計算
                calmar_ratio=np.random.normal(0.7, 0.2),  # 模擬值
                total_trades=total_trades,
                profit_trades=profit_trades,
                avg_profit=np.random.normal(0.02, 0.01),
                avg_loss=np.random.normal(-0.015, 0.008),
            )

        except Exception as e:
            logger.error(f"計算策略性能失敗: {e}")
            raise

# 全局策略管理器實例
strategy_manager = CBSCStrategyManager()

# ============================================================================
# API端點 (API Endpoints)
# ============================================================================

@router.get("/", response_model=List[Strategy])
async def list_strategies(
    strategy_type: Optional[StrategyType] = Query(None, description="策略類型過濾"),
    status: Optional[StrategyStatus] = Query(None, description="狀態過濾"),
    is_active: Optional[bool] = Query(None, description="是否激活過濾"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁大小"),
    current_user: User = Depends(get_current_user())
):
    """獲取策略列表"""
    return await strategy_manager.get_strategies(
        user_id=current_user.id,
        strategy_type=strategy_type,
        status=status,
        is_active=is_active,
        page=page,
        page_size=page_size
    )

@router.post("/", response_model=Strategy, status_code=201)
async def create_strategy(
    request: CreateStrategyRequest,
    current_user: User = Depends(get_current_user())
):
    """創建新策略"""
    return await strategy_manager.create_strategy(request, current_user.id)

@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """獲取策略詳情"""
    return await strategy_manager.get_strategy(strategy_id, current_user.id)

@router.put("/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy_id: str,
    request: UpdateStrategyRequest,
    current_user: User = Depends(get_current_user())
):
    """更新策略"""
    return await strategy_manager.update_strategy(strategy_id, request, current_user.id)

@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """刪除策略"""
    await strategy_manager.delete_strategy(strategy_id, current_user.id)

@router.post("/{strategy_id}/execute", response_model=StrategyExecutionResult)
async def execute_strategy(
    strategy_id: str,
    execution_request: StrategyExecutionRequest,
    current_user: User = Depends(get_current_user())
):
    """執行策略"""
    return await strategy_manager.execute_strategy(strategy_id, execution_request, current_user.id)

@router.post("/{strategy_id}/stop")
async def stop_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """停止策略執行"""
    await strategy_manager.stop_strategy(strategy_id, current_user.id)
    return {"message": "策略已停止"}

@router.get("/{strategy_id}/status", response_model=StrategyRealTimeStatus)
async def get_strategy_status(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """獲取策略實時狀態"""
    return await strategy_manager.get_strategy_status(strategy_id, current_user.id)

@router.get("/{strategy_id}/metrics", response_model=StrategyPerformance)
async def get_strategy_metrics(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """獲取策略性能指標"""
    return await strategy_manager.get_strategy_metrics(strategy_id, current_user.id)

@router.get("/templates", response_model=List[CBSCStrategyTemplate])
async def get_strategy_templates():
    """獲取策略模板列表"""
    return await strategy_manager.get_strategy_templates()

@router.post("/{strategy_id}/validate", response_model=StrategyConfigValidation)
async def validate_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """驗證策略配置"""
    strategy = await strategy_manager.get_strategy(strategy_id, current_user.id)
    return await strategy_manager.validate_strategy_config(strategy)

# ============================================================================
# 導出 (Exports)
# ============================================================================

__all__ = [
    "router",
    "CBSCStrategyManager",
    "strategy_manager",
    "StrategyExecutionStatus",
    "StrategyRiskMetrics",
    "StrategyRealTimeStatus",
    "StrategyConfigValidation",
    "StrategyExecutionReport"
]