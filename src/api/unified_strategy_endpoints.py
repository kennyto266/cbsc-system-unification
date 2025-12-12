#!/usr/bin/env python3
"""
統一策略管理API端點
Unified Strategy Management API Endpoints

提供完整的策略CRUD操作和實時監控功能
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# 導入統一策略服務
from .unified_strategy_service import (
    get_unified_strategy_manager,
    StrategyExecutionRequest,
    StrategyMetrics,
    StrategyTemplate
)

# 導入數據模型
from ..models.strategy import (
    StrategyCreateSchema,
    StrategyUpdateSchema,
    StrategyResponseSchema,
    StrategyConfigCreateSchema,
    StrategyConfigResponseSchema
)

# 導入認證系統
try:
    from auth_simple import User, get_current_user
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from auth_simple import User, get_current_user

logger = logging.getLogger(__name__)

# ============================================================================
# 路由器設置
# ============================================================================

router = APIRouter(prefix="/api/v1/strategies", tags=["統一策略管理"])

# ============================================================================
# 請求/響應模型
# ============================================================================

class StrategyListResponse(BaseModel):
    """策略列表響應"""
    strategies: List[StrategyResponseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int

class StrategyExecutionResponse(BaseModel):
    """策略執行響應"""
    success: bool
    execution_id: str
    message: str
    details: Optional[Dict[str, Any]] = None

class StrategyStatusResponse(BaseModel):
    """策略狀態響應"""
    strategy_id: str
    status: str
    execution_state: str
    is_running: bool
    last_executed: Optional[datetime] = None
    total_return: float = 0.0
    current_pnl: float = 0.0

class StrategyValidationResponse(BaseModel):
    """策略驗證響應"""
    is_valid: bool
    validation_errors: List[str] = []
    validation_warnings: List[str] = []

class StrategyTemplateListResponse(BaseModel):
    """策略模板列表響應"""
    templates: List[StrategyTemplate]
    total: int

# ============================================================================
# 策略CRUD端點
# ============================================================================

@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    strategy_type: Optional[str] = Query(None, description="策略類型過濾"),
    status: Optional[str] = Query(None, description="狀態過濾"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁大小"),
    current_user: User = Depends(get_current_user())
):
    """
    獲取策略列表

    - **strategy_type**: 策略類型過濾 (direct_rsi, sentiment_momentum, composite_index)
    - **status**: 狀態過濾 (active, inactive, testing, error, stopped)
    - **page**: 頁碼，從1開始
    - **page_size**: 每頁大小，最大100
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        # 獲取策略列表
        strategies = await strategy_manager.get_strategies(
            user_id=current_user.id,
            strategy_type=strategy_type,
            status=status,
            page=page,
            page_size=page_size
        )

        # 計算總數（簡化實現，實際應該從數據庫查詢）
        total = len(strategies)

        response = StrategyListResponse(
            strategies=strategies,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

        logger.info(f"用戶 {current_user.id} 獲取策略列表成功，共 {len(strategies)} 個策略")
        return response

    except Exception as e:
        logger.error(f"獲取策略列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取策略列表失敗: {str(e)}")

@router.post("/", response_model=StrategyResponseSchema, status_code=201)
async def create_strategy(
    request: StrategyCreateSchema,
    current_user: User = Depends(get_current_user())
):
    """
    創建新策略

    - **name**: 策略名稱 (必需，3-200字符)
    - **code**: 策略代碼 (必需，3-100字符，系統會自動生成)
    - **description**: 策略描述 (可選)
    - **strategy_type**: 策略類型 (必需)
    - **risk_level**: 風險等級 (low, medium, high, extreme)
    - **default_parameters**: 默認參數 (可選)
    - **required_indicators**: 必需指標列表 (可選)
    - **supported_timeframes**: 支持的時間週期 (可選)
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        # 驗證策略配置
        validation_result = await strategy_manager.validate_strategy_config(request.dict())
        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"策略配置驗證失敗: {'; '.join(validation_result['validation_errors'])}"
            )

        # 創建策略
        strategy = await strategy_manager.create_strategy(request, current_user.id)

        logger.info(f"用戶 {current_user.id} 創建策略成功: {strategy.id}")
        return strategy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建策略失敗: {str(e)}")

@router.get("/{strategy_id}", response_model=StrategyResponseSchema)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """
    獲取策略詳情

    - **strategy_id**: 策略唯一標識符
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        strategy = await strategy_manager.get_strategy(strategy_id, current_user.id)

        logger.info(f"用戶 {current_user.id} 獲取策略詳情成功: {strategy_id}")
        return strategy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取策略詳情失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取策略詳情失敗: {str(e)}")

@router.put("/{strategy_id}", response_model=StrategyResponseSchema)
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdateSchema,
    current_user: User = Depends(get_current_user())
):
    """
    更新策略

    - **strategy_id**: 策略唯一標識符
    - **name**: 策略名稱 (可選)
    - **description**: 策略描述 (可選)
    - **status**: 策略狀態 (可選)
    - **default_parameters**: 默認參數 (可選)
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        # 驗證更新數據
        if request.default_parameters:
            update_data = request.dict(exclude_unset=True)
            validation_result = await strategy_manager.validate_strategy_config(update_data)
            if not validation_result["is_valid"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"策略配置驗證失敗: {'; '.join(validation_result['validation_errors'])}"
                )

        strategy = await strategy_manager.update_strategy(strategy_id, request, current_user.id)

        logger.info(f"用戶 {current_user.id} 更新策略成功: {strategy_id}")
        return strategy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新策略失敗: {str(e)}")

@router.delete("/{strategy_id}", status_code=204)
async def delete_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """
    刪除策略

    - **strategy_id**: 策略唯一標識符

    注意：無法刪除正在運行的策略
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        await strategy_manager.delete_strategy(strategy_id, current_user.id)

        logger.info(f"用戶 {current_user.id} 刪除策略成功: {strategy_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除策略失敗: {str(e)}")

# ============================================================================
# 策略執行控制端點
# ============================================================================

@router.post("/{strategy_id}/execute", response_model=StrategyExecutionResponse)
async def execute_strategy(
    strategy_id: str,
    execution_request: StrategyExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user())
):
    """
    執行策略

    - **strategy_id**: 策略唯一標識符
    - **start_time**: 開始時間 (可選)
    - **end_time**: 結束時間 (可選)
    - **execution_mode**: 執行模式 (backtest, live)
    - **data_source**: 數據源 (可選)
    - **parameters**: 覆蓋參數 (可選)
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        # 執行策略
        result = await strategy_manager.execute_strategy(
            strategy_id, execution_request, current_user.id
        )

        response = StrategyExecutionResponse(
            success=result["status"] == "completed",
            execution_id=result["execution_id"],
            message="策略執行成功" if result["status"] == "completed" else "策略執行失敗",
            details=result
        )

        logger.info(f"用戶 {current_user.id} 執行策略成功: {strategy_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"執行策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"執行策略失敗: {str(e)}")

@router.post("/{strategy_id}/stop", response_model=Dict[str, str])
async def stop_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """
    停止策略執行

    - **strategy_id**: 策略唯一標識符
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        await strategy_manager.stop_strategy(strategy_id, current_user.id)

        logger.info(f"用戶 {current_user.id} 停止策略成功: {strategy_id}")
        return {"message": "策略已停止", "strategy_id": strategy_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止策略失敗: {str(e)}")

# ============================================================================
# 策略監控端點
# ============================================================================

@router.get("/{strategy_id}/status", response_model=StrategyStatusResponse)
async def get_strategy_status(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """
    獲取策略實時狀態

    - **strategy_id**: 策略唯一標識符

    返回策略的當前執行狀態、性能指標等實時信息
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        status_data = await strategy_manager.get_strategy_status(strategy_id, current_user.id)

        response = StrategyStatusResponse(**status_data)

        logger.info(f"用戶 {current_user.id} 獲取策略狀態成功: {strategy_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取策略狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取策略狀態失敗: {str(e)}")

@router.get("/{strategy_id}/metrics", response_model=StrategyMetrics)
async def get_strategy_metrics(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """
    獲取策略性能指標

    - **strategy_id**: 策略唯一標識符

    返回策略的詳細性能指標，包括收益率、夏普比率、最大回撤等
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        metrics = await strategy_manager.get_strategy_metrics(strategy_id, current_user.id)

        logger.info(f"用戶 {current_user.id} 獲取策略性能指標成功: {strategy_id}")
        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取策略性能指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取策略性能指標失敗: {str(e)}")

# ============================================================================
# 策略配置和驗證端點
# ============================================================================

@router.post("/{strategy_id}/validate", response_model=StrategyValidationResponse)
async def validate_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user())
):
    """
    驗證策略配置

    - **strategy_id**: 策略唯一標識符

    驗證策略參數的合理性和風險
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        # 獲取策略數據
        strategy = await strategy_manager.get_strategy(strategy_id, current_user.id)

        # 驗證配置
        validation_result = await strategy_manager.validate_strategy_config(strategy.dict())

        response = StrategyValidationResponse(**validation_result)

        logger.info(f"用戶 {current_user.id} 驗證策略配置成功: {strategy_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"驗證策略配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"驗證策略配置失敗: {str(e)}")

@router.get("/templates", response_model=StrategyTemplateListResponse)
async def get_strategy_templates():
    """
    獲取策略模板列表

    返回所有可用的策略模板，包括默認參數和配置說明
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        templates = await strategy_manager.get_strategy_templates()

        response = StrategyTemplateListResponse(
            templates=templates,
            total=len(templates)
        )

        logger.info(f"獲取策略模板列表成功，共 {len(templates)} 個模板")
        return response

    except Exception as e:
        logger.error(f"獲取策略模板列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取策略模板列表失敗: {str(e)}")

@router.post("/validate-parameters", response_model=StrategyValidationResponse)
async def validate_strategy_parameters(
    parameters: Dict[str, Any],
    current_user: User = Depends(get_current_user())
):
    """
    驗證策略參數

    - **parameters**: 策略參數字典

    在創建或更新策略之前驗證參數的合理性
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        validation_result = await strategy_manager.validate_strategy_config(parameters)

        response = StrategyValidationResponse(**validation_result)

        logger.info(f"用戶 {current_user.id} 驗證策略參數成功")
        return response

    except Exception as e:
        logger.error(f"驗證策略參數失敗: {e}")
        raise HTTPException(status_code=500, detail=f"驗證策略參數失敗: {str(e)}")

# ============================================================================
# 批量操作端點
# ============================================================================

@router.post("/batch/stop", response_model=Dict[str, Any])
async def batch_stop_strategies(
    strategy_ids: List[str],
    current_user: User = Depends(get_current_user())
):
    """
    批量停止策略

    - **strategy_ids**: 策略ID列表

    同時停止多個策略的執行
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        results = []
        for strategy_id in strategy_ids:
            try:
                await strategy_manager.stop_strategy(strategy_id, current_user.id)
                results.append({"strategy_id": strategy_id, "success": True})
            except Exception as e:
                results.append({"strategy_id": strategy_id, "success": False, "error": str(e)})

        success_count = sum(1 for r in results if r["success"])

        logger.info(f"用戶 {current_user.id} 批量停止策略完成: {success_count}/{len(strategy_ids)} 成功")
        return {
            "total": len(strategy_ids),
            "success_count": success_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"批量停止策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批量停止策略失敗: {str(e)}")

@router.post("/batch/execute", response_model=Dict[str, Any])
async def batch_execute_strategies(
    strategy_ids: List[str],
    execution_request: StrategyExecutionRequest,
    current_user: User = Depends(get_current_user())
):
    """
    批量執行策略

    - **strategy_ids**: 策略ID列表
    - **execution_request**: 執行請求參數

    使用相同參數同時執行多個策略
    """
    try:
        strategy_manager = get_unified_strategy_manager()

        results = []
        for strategy_id in strategy_ids:
            try:
                result = await strategy_manager.execute_strategy(
                    strategy_id, execution_request, current_user.id
                )
                results.append({"strategy_id": strategy_id, "success": True, "execution_id": result.get("execution_id")})
            except Exception as e:
                results.append({"strategy_id": strategy_id, "success": False, "error": str(e)})

        success_count = sum(1 for r in results if r["success"])

        logger.info(f"用戶 {current_user.id} 批量執行策略完成: {success_count}/{len(strategy_ids)} 成功")
        return {
            "total": len(strategy_ids),
            "success_count": success_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"批量執行策略失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批量執行策略失敗: {str(e)}")

# ============================================================================
# 導出
# ============================================================================

__all__ = ["router"]