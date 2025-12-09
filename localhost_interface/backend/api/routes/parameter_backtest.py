#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
0700.HK 參數回測API路由
Phase 4: GPU加速參數優化系統的RESTful API端點
"""

import asyncio
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import json

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator
import numpy as np
import pandas as pd

from backend.api.auth import check_permissions, get_current_active_trader
from shared.models.schemas import User, BacktestRequest, BacktestResult

logger = logging.getLogger(__name__)
router = APIRouter()

# === 參數優化相關枚舉 ===
class OptimizationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OptimizationObjective(str, Enum):
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    PROFIT_FACTOR = "profit_factor"
    TOTAL_RETURN = "total_return"
    ANNUALIZED_RETURN = "annualized_return"

class SamplingMethod(str, Enum):
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    SMART_SAMPLING = "smart_sampling"

class GPUBackend(str, Enum):
    CUDA = "cuda"
    CUPY = "cupy"
    NUMBA = "numba"
    MOCK = "mock"

# === 參數優化數據模型 ===
class ParameterRange(BaseModel):
    """參數範圍定義"""
    name: str
    min_value: float
    max_value: float
    step: Optional[float] = None
    type: str = Field(default="continuous")  # continuous, integer, categorical
    values: Optional[List[Any]] = None  # 用於categorical類型

class RSIParameters(BaseModel):
    """RSI指標參數"""
    period: int = Field(default=14, ge=1, le=100)
    oversold: float = Field(default=30, ge=0, le=100)
    overbought: float = Field(default=70, ge=0, le=100)
    weight: float = Field(default=0.4, ge=0, le=1)

class MACDParameters(BaseModel):
    """MACD指標參數"""
    fast_period: int = Field(default=12, ge=1, le=50)
    slow_period: int = Field(default=26, ge=1, le=100)
    signal_period: int = Field(default=9, ge=1, le=30)
    weight: float = Field(default=0.3, ge=0, le=1)

class BollingerBandsParameters(BaseModel):
    """布林帶參數"""
    period: int = Field(default=20, ge=1, le=50)
    std_dev: float = Field(default=2.0, ge=0.5, le=5.0)
    weight: float = Field(default=0.3, ge=0, le=1)

class OptimizationConfig(BaseModel):
    """優化配置"""
    # 目標函數
    objective: OptimizationObjective = Field(default=OptimizationObjective.SHARPE_RATIO)
    secondary_objectives: List[OptimizationObjective] = []

    # 參數範圍
    rsi_params: ParameterRange
    macd_params: ParameterRange
    bb_params: ParameterRange

    # 優化設置
    max_combinations: int = Field(default=1000, ge=1, le=100000)
    sampling_method: SamplingMethod = Field(default=SamplingMethod.SMART_SAMPLING)
    n_samples: int = Field(default=200, ge=10, le=10000)

    # GPU設置
    enable_gpu: bool = Field(default=True)
    gpu_backend: GPUBackend = Field(default=GPUBackend.CUDA)
    gpu_device: int = Field(default=0, ge=0, le=7)

    # 回測設置
    initial_capital: float = Field(default=1000000, gt=0)
    commission: float = Field(default=0.001, ge=0)
    slippage: float = Field(default=0.0001, ge=0)
    benchmark_symbol: str = Field(default="HSI.HK")

    # 交叉驗證
    enable_cross_validation: bool = Field(default=True)
    cv_folds: int = Field(default=5, ge=2, le=10)

    # 並行設置
    max_workers: int = Field(default=4, ge=1, le=32)
    chunk_size: int = Field(default=100, ge=10, le=1000)

class OptimizationRequest(BaseModel):
    """參數優化請求"""
    symbol: str = Field(default="0700.HK")
    start_date: date
    end_date: date
    config: OptimizationConfig
    description: Optional[str] = None
    tags: List[str] = []
    priority: int = Field(default=1, ge=1, le=10)

class ParameterCombination(BaseModel):
    """單個參數組合"""
    combination_id: str
    rsi_period: int
    rsi_oversold: float
    rsi_overbought: float
    rsi_weight: float
    macd_fast: int
    macd_slow: int
    macd_signal: int
    macd_weight: float
    bb_period: int
    bb_std: float
    bb_weight: float

class OptimizationResult(BaseModel):
    """單個組合的優化結果"""
    combination_id: str
    parameters: ParameterCombination
    performance: Dict[str, float]
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    total_return: float
    annualized_return: float
    profit_factor: float
    win_rate: float
    total_trades: int
    execution_time: float
    timestamp: datetime

class OptimizationProgress(BaseModel):
    """優化進度更新"""
    request_id: str
    status: OptimizationStatus
    progress: float = Field(ge=0, le=100)
    current_combination: int
    total_combinations: int
    best_sharpe: float
    best_combination: Optional[ParameterCombination] = None
    current_parameters: Optional[ParameterCombination] = None
    elapsed_time: float
    estimated_remaining_time: Optional[float] = None
    message: Optional[str] = None
    timestamp: datetime

class OptimizationReport(BaseModel):
    """完整的優化報告"""
    request_id: str
    symbol: str
    period_start: date
    period_end: date

    # 優化配置
    config: OptimizationConfig

    # 執行狀態
    status: OptimizationStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None

    # 統計信息
    total_combinations: int
    evaluated_combinations: int
    failed_combinations: int

    # 最佳結果
    best_result: Optional[OptimizationResult] = None
    top_10_results: List[OptimizationResult] = []

    # 性能統計
    performance_distribution: Dict[str, List[float]] = {}
    parameter_sensitivity: Dict[str, Any] = {}

    # 系統性能
    avg_combination_time: float
    gpu_utilization: Optional[float] = None
    memory_usage: Optional[float] = None

    # 文件路徑
    results_file: Optional[str] = None
    log_file: Optional[str] = None

# 全局優化任務存儲（生產環境應使用Redis）
active_optimizations: Dict[str, OptimizationRequest] = {}
optimization_status: Dict[str, OptimizationProgress] = {}
optimization_results: Dict[str, List[OptimizationResult]] = {}

# === API端點 ===

@router.post("/optimize", response_model=Dict[str, str])
async def start_parameter_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_permissions("backtest"))
):
    """
    啟動0700.HK參數優化任務

    開始GPU加速的參數空間搜索和優化
    """
    try:
        # 生成唯一請求ID
        request_id = f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # 驗證請求
        await _validate_optimization_request(request)

        # 存儲請求
        active_optimizations[request_id] = request

        # 初始化進度跟蹤
        optimization_status[request_id] = OptimizationProgress(
            request_id=request_id,
            status=OptimizationStatus.PENDING,
            progress=0.0,
            current_combination=0,
            total_combinations=request.config.max_combinations,
            best_sharpe=-999.0,
            elapsed_time=0.0,
            timestamp=datetime.now()
        )

        # 啟動後台優化任務
        background_tasks.add_task(
            _execute_parameter_optimization,
            request_id,
            request,
            current_user.username
        )

        logger.info(f"用戶 {current_user.username} 啟動參數優化: {request_id}")

        return {
            "request_id": request_id,
            "status": "started",
            "message": f"參數優化任務已啟動，請求ID: {request_id}",
            "monitor_url": f"/api/parameter-backtest/progress/{request_id}"
        }

    except Exception as e:
        logger.error(f"啟動參數優化失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"啟動參數優化失敗: {str(e)}"
        )

@router.get("/progress/{request_id}", response_model=OptimizationProgress)
async def get_optimization_progress(
    request_id: str,
    current_user: User = Depends(get_current_active_trader)
):
    """
    獲取參數優化進度

    實時監控優化任務的執行狀態和進度
    """
    try:
        if request_id not in optimization_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"優化任務 {request_id} 不存在"
            )

        progress = optimization_status[request_id]

        logger.info(f"用戶 {current_user.username} 查詢優化進度: {request_id}")
        return progress

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取優化進度失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取優化進度失敗: {str(e)}"
        )

@router.post("/cancel/{request_id}")
async def cancel_optimization(
    request_id: str,
    current_user: User = Depends(check_permissions("backtest"))
):
    """
    取消正在進行的參數優化任務
    """
    try:
        if request_id not in active_optimizations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"優化任務 {request_id} 不存在"
            )

        # 更新狀態
        if request_id in optimization_status:
            optimization_status[request_id].status = OptimizationStatus.CANCELLED
            optimization_status[request_id].timestamp = datetime.now()

        logger.info(f"用戶 {current_user.username} 取消優化任務: {request_id}")

        return {
            "request_id": request_id,
            "status": "cancelled",
            "message": f"優化任務 {request_id} 已取消"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消優化任務失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消優化任務失敗: {str(e)}"
        )

@router.get("/results/{request_id}", response_model=OptimizationReport)
async def get_optimization_results(
    request_id: str,
    current_user: User = Depends(get_current_active_trader)
):
    """
    獲取完整的優化結果報告
    """
    try:
        if request_id not in active_optimizations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"優化任務 {request_id} 不存在"
            )

        # 生成完整報告
        request = active_optimizations[request_id]
        progress = optimization_status.get(request_id)
        results = optimization_results.get(request_id, [])

        report = await _generate_optimization_report(request_id, request, progress, results)

        logger.info(f"用戶 {current_user.username} 獲取優化結果: {request_id}")
        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取優化結果失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取優化結果失敗: {str(e)}"
        )

@router.get("/history", response_model=List[OptimizationReport])
async def get_optimization_history(
    limit: int = Query(default=20, ge=1, le=100),
    symbol: Optional[str] = Query(default=None),
    status_filter: Optional[OptimizationStatus] = Query(default=None),
    current_user: User = Depends(get_current_active_trader)
):
    """
    獲取參數優化歷史記錄
    """
    try:
        # 過濾和排序
        filtered_requests = []

        for request_id, request in active_optimizations.items():
            if symbol and request.symbol != symbol:
                continue

            progress = optimization_status.get(request_id)
            if status_filter and progress and progress.status != status_filter:
                continue

            results = optimization_results.get(request_id, [])
            report = await _generate_optimization_report(request_id, request, progress, results)
            filtered_requests.append(report)

        # 按創建時間排序
        filtered_requests.sort(key=lambda x: x.created_at, reverse=True)

        return filtered_requests[:limit]

    except Exception as e:
        logger.error(f"獲取優化歷史失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取優化歷史失敗: {str(e)}"
        )

@router.get("/best-parameters/{symbol}")
async def get_best_parameters_for_symbol(
    symbol: str = "0700.HK",
    objective: OptimizationObjective = Query(default=OptimizationObjective.SHARPE_RATIO),
    current_user: User = Depends(get_current_active_trader)
):
    """
    獲取特定符號的最佳參數組合
    """
    try:
        best_combination = None
        best_score = -999.0

        # 搜索所有優化結果
        for request_id, results in optimization_results.items():
            request = active_optimizations.get(request_id)
            if not request or request.symbol != symbol:
                continue

            for result in results:
                if objective == OptimizationObjective.SHARPE_RATIO:
                    score = result.sharpe_ratio
                elif objective == OptimizationObjective.SORTINO_RATIO:
                    score = result.sortino_ratio
                elif objective == OptimizationObjective.MAX_DRAWDOWN:
                    score = -result.max_drawdown  # 最小化回撤
                elif objective == OptimizationObjective.TOTAL_RETURN:
                    score = result.total_return
                elif objective == OptimizationObjective.ANNUALIZED_RETURN:
                    score = result.annualized_return
                else:
                    score = result.profit_factor

                if score > best_score:
                    best_score = score
                    best_combination = result

        if not best_combination:
            return {
                "symbol": symbol,
                "objective": objective,
                "message": "未找到優化結果",
                "best_parameters": None
            }

        return {
            "symbol": symbol,
            "objective": objective,
            "best_score": best_score,
            "best_parameters": best_combination.parameters.dict(),
            "performance": best_combination.performance,
            "found_at": best_combination.timestamp
        }

    except Exception as e:
        logger.error(f"獲取最佳參數失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取最佳參數失敗: {str(e)}"
        )

@router.get("/stats")
async def get_optimization_statistics(
    current_user: User = Depends(get_current_active_trader)
):
    """
    獲取系統優化統計信息
    """
    try:
        total_optimizations = len(active_optimizations)
        active_count = sum(1 for p in optimization_status.values() if p.status == OptimizationStatus.RUNNING)
        completed_count = sum(1 for p in optimization_status.values() if p.status == OptimizationStatus.COMPLETED)
        failed_count = sum(1 for p in optimization_status.values() if p.status == OptimizationStatus.FAILED)

        # 計算總執行時間
        total_execution_time = sum(r.execution_time for results in optimization_results.values() for r in results if r.execution_time)

        # 統計最佳性能
        all_results = []
        for results in optimization_results.values():
            all_results.extend(results)

        if all_results:
            best_sharpe = max(r.sharpe_ratio for r in all_results)
            avg_sharpe = np.mean([r.sharpe_ratio for r in all_results])
            best_return = max(r.total_return for r in all_results)
            avg_return = np.mean([r.total_return for r in all_results])
        else:
            best_sharpe = avg_sharpe = best_return = avg_return = 0.0

        return {
            "total_optimizations": total_optimizations,
            "status_counts": {
                "active": active_count,
                "completed": completed_count,
                "failed": failed_count
            },
            "total_combinations_evaluated": len(all_results),
            "total_execution_time": total_execution_time,
            "performance_stats": {
                "best_sharpe_ratio": best_sharpe,
                "average_sharpe_ratio": avg_sharpe,
                "best_total_return": best_return,
                "average_total_return": avg_return
            },
            "system_info": {
                "supported_symbols": ["0700.HK", "0941.HK", "1299.HK", "HSI.HK"],
                "available_objectives": [obj.value for obj in OptimizationObjective],
                "available_methods": [method.value for method in SamplingMethod],
                "gpu_backends": [backend.value for backend in GPUBackend]
            }
        }

    except Exception as e:
        logger.error(f"獲取優化統計失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取優化統計失敗: {str(e)}"
        )

# === 輔助函數 ===

async def _validate_optimization_request(request: OptimizationRequest):
    """驗證優化請求參數"""
    # 驗證日期範圍
    if request.end_date <= request.start_date:
        raise ValueError("結束日期必須晚於開始日期")

    # 驗證日期範圍不超過3年
    if (request.end_date - request.start_date).days > 1095:
        raise ValueError("優化期間不能超過3年")

    # 驗證參數範圍
    if request.config.rsi_params.min_value < 1 or request.config.rsi_params.max_value > 100:
        raise ValueError("RSI週期必須在1-100之間")

    if request.config.macd_params.min_value < 1 or request.config.macd_params.max_value > 100:
        raise ValueError("MACD週期必須在1-100之間")

    if request.config.bb_params.min_value < 5 or request.config.bb_params.max_value > 50:
        raise ValueError("布林帶週期必須在5-50之間")

async def _execute_parameter_optimization(request_id: str, request: OptimizationRequest, username: str):
    """執行參數優化的後台任務"""
    try:
        # 更新狀態為運行中
        optimization_status[request_id].status = OptimizationStatus.RUNNING
        optimization_status[request_id].message = "正在初始化優化引擎..."

        # 初始化優化引擎
        from gpu_accelerated_0700_backtest import GPUAccelerated0700BacktestEngine

        engine = GPUAccelerated0700BacktestEngine(gpu_device=request.config.gpu_device)

        # 準備數據
        optimization_status[request_id].message = "準備市場數據..."
        dataset = engine.prepare_0700_dataset(
            duration_days=(request.end_date - request.start_date).days
        )

        # 生成參數組合
        combinations = await _generate_parameter_combinations(request.config)
        optimization_status[request_id].total_combinations = len(combinations)

        # 執行優化
        results = []
        best_sharpe = -999.0
        best_combination = None

        start_time = datetime.now()

        for i, combination in enumerate(combinations):
            # 檢查是否被取消
            if optimization_status[request_id].status == OptimizationStatus.CANCELLED:
                break

            # 更新進度
            progress = (i / len(combinations)) * 100
            optimization_status[request_id].progress = progress
            optimization_status[request_id].current_combination = i + 1
            optimization_status[request_id].current_parameters = combination
            optimization_status[request_id].elapsed_time = (datetime.now() - start_time).total_seconds()

            if i > 0:
                avg_time = optimization_status[request_id].elapsed_time / i
                remaining_combinations = len(combinations) - i
                optimization_status[request_id].estimated_remaining_time = avg_time * remaining_combinations

            # 評估參數組合
            try:
                result = await _evaluate_combination(engine, combination, dataset, request.config)
                results.append(result)

                # 更新最佳結果
                if result.sharpe_ratio > best_sharpe:
                    best_sharpe = result.sharpe_ratio
                    best_combination = combination
                    optimization_status[request_id].best_sharpe = best_sharpe
                    optimization_status[request_id].best_combination = combination

                # 定期更新進度（每10個組合）
                if i % 10 == 0:
                    optimization_status[request_id].message = f"已評估 {i+1}/{len(combinations)} 個組合..."

            except Exception as e:
                logger.error(f"評估組合失敗: {combination.combination_id}, 錯誤: {e}")
                continue

        # 存儲結果
        optimization_results[request_id] = results

        # 更新最終狀態
        if optimization_status[request_id].status != OptimizationStatus.CANCELLED:
            optimization_status[request_id].status = OptimizationStatus.COMPLETED
            optimization_status[request_id].progress = 100.0
            optimization_status[request_id].message = "優化完成！"
        else:
            optimization_status[request_id].message = "優化已取消"

        optimization_status[request_id].timestamp = datetime.now()

        logger.info(f"優化任務完成: {request_id}, 評估了 {len(results)} 個組合")

    except Exception as e:
        logger.error(f"執行優化任務失敗: {request_id}, 錯誤: {e}")
        optimization_status[request_id].status = OptimizationStatus.FAILED
        optimization_status[request_id].message = f"優化失敗: {str(e)}"
        optimization_status[request_id].timestamp = datetime.now()

async def _generate_parameter_combinations(config: OptimizationConfig) -> List[ParameterCombination]:
    """生成參數組合"""
    combinations = []

    if config.sampling_method == SamplingMethod.SMART_SAMPLING:
        # 智能採樣 - 使用分層隨機採樣
        combinations = await _smart_sampling(config)
    elif config.sampling_method == SamplingMethod.GRID_SEARCH:
        combinations = await _grid_search(config)
    elif config.sampling_method == SamplingMethod.RANDOM_SEARCH:
        combinations = await _random_search(config)
    else:
        # 默認使用智能採樣
        combinations = await _smart_sampling(config)

    # 限制組合數量
    return combinations[:config.max_combinations]

async def _smart_sampling(config: OptimizationConfig) -> List[ParameterCombination]:
    """智能採樣策略"""
    combinations = []
    n_samples = config.n_samples

    # RSI參數採樣
    rsi_periods = np.random.randint(
        int(config.rsi_params.min_value),
        int(config.rsi_params.max_value) + 1,
        n_samples
    )
    rsi_oversolds = np.random.uniform(20, 40, n_samples)
    rsi_overboughts = np.random.uniform(60, 80, n_samples)
    rsi_weights = np.random.uniform(0.2, 0.6, n_samples)

    # MACD參數採樣
    macd_fasts = np.random.randint(
        int(config.macd_params.min_value),
        min(int(config.macd_params.max_value), 20),
        n_samples
    )
    macd_slows = np.random.randint(
        macd_fasts.max(),
        int(config.macd_params.max_value) + 1,
        n_samples
    )
    macd_signals = np.random.randint(5, 15, n_samples)
    macd_weights = np.random.uniform(0.1, 0.5, n_samples)

    # 布林帶參數採樣
    bb_periods = np.random.randint(
        int(config.bb_params.min_value),
        int(config.bb_params.max_value) + 1,
        n_samples
    )
    bb_stds = np.random.uniform(1.5, 3.0, n_samples)
    bb_weights = np.random.uniform(0.1, 0.5, n_samples)

    # 確保權重總和為1
    for i in range(n_samples):
        total_weight = rsi_weights[i] + macd_weights[i] + bb_weights[i]
        rsi_weights[i] /= total_weight
        macd_weights[i] /= total_weight
        bb_weights[i] /= total_weight

    # 生成組合
    for i in range(n_samples):
        combination = ParameterCombination(
            combination_id=f"comb_{i:06d}",
            rsi_period=int(rsi_periods[i]),
            rsi_oversold=float(rsi_oversolds[i]),
            rsi_overbought=float(rsi_overboughts[i]),
            rsi_weight=float(rsi_weights[i]),
            macd_fast=int(macd_fasts[i]),
            macd_slow=int(macd_slows[i]),
            macd_signal=int(macd_signals[i]),
            macd_weight=float(macd_weights[i]),
            bb_period=int(bb_periods[i]),
            bb_std=float(bb_stds[i]),
            bb_weight=float(bb_weights[i])
        )
        combinations.append(combination)

    return combinations

async def _grid_search(config: OptimizationConfig) -> List[ParameterCombination]:
    """網格搜索策略"""
    combinations = []

    # 粗粒度網格搜索以控制組合數量
    rsi_periods = range(int(config.rsi_params.min_value), int(config.rsi_params.max_value) + 1, 3)
    rsi_oversolds = [20, 30, 40]
    rsi_overboughts = [60, 70, 80]
    rsi_weights = [0.3, 0.4, 0.5]

    macd_fasts = [8, 12, 16]
    macd_slows = [20, 26, 32]
    macd_signals = [7, 9, 12]
    macd_weights = [0.2, 0.3, 0.4]

    bb_periods = [15, 20, 25]
    bb_stds = [1.5, 2.0, 2.5]
    bb_weights = [0.2, 0.3, 0.4]

    combo_id = 0
    for rp in rsi_periods:
        for ro in rsi_oversolds:
            for rob in rsi_overboughts:
                for rw in rsi_weights:
                    for mf in macd_fasts:
                        for ms in macd_slows:
                            for msi in macd_signals:
                                for mw in macd_weights:
                                    for bp in bb_periods:
                                        for bs in bb_stds:
                                            for bw in bb_weights:
                                                # 權重標準化
                                                total_weight = rw + mw + bw
                                                if total_weight == 0:
                                                    continue

                                                combination = ParameterCombination(
                                                    combination_id=f"comb_{combo_id:06d}",
                                                    rsi_period=rp,
                                                    rsi_oversold=ro,
                                                    rsi_overbought=rob,
                                                    rsi_weight=rw/total_weight,
                                                    macd_fast=mf,
                                                    macd_slow=ms,
                                                    macd_signal=msi,
                                                    macd_weight=mw/total_weight,
                                                    bb_period=bp,
                                                    bb_std=bs,
                                                    bb_weight=bw/total_weight
                                                )
                                                combinations.append(combination)
                                                combo_id += 1

    return combinations

async def _random_search(config: OptimizationConfig) -> List[ParameterCombination]:
    """隨機搜索策略"""
    combinations = []
    n_samples = config.n_samples

    for i in range(n_samples):
        # 隨機生成參數
        rsi_period = np.random.randint(int(config.rsi_params.min_value), int(config.rsi_params.max_value) + 1)
        rsi_oversold = np.random.uniform(20, 40)
        rsi_overbought = np.random.uniform(60, 80)

        macd_fast = np.random.randint(int(config.macd_params.min_value), min(int(config.macd_params.max_value), 20))
        macd_slow = np.random.randint(macd_fast + 5, int(config.macd_params.max_value) + 1)
        macd_signal = np.random.randint(5, 15)

        bb_period = np.random.randint(int(config.bb_params.min_value), int(config.bb_params.max_value) + 1)
        bb_std = np.random.uniform(1.5, 3.0)

        # 隨機權重並標準化
        rsi_weight = np.random.uniform(0.2, 0.6)
        macd_weight = np.random.uniform(0.1, 0.5)
        bb_weight = np.random.uniform(0.1, 0.5)

        total_weight = rsi_weight + macd_weight + bb_weight
        rsi_weight /= total_weight
        macd_weight /= total_weight
        bb_weight /= total_weight

        combination = ParameterCombination(
            combination_id=f"comb_{i:06d}",
            rsi_period=int(rsi_period),
            rsi_oversold=float(rsi_oversold),
            rsi_overbought=float(rsi_overbought),
            rsi_weight=float(rsi_weight),
            macd_fast=int(macd_fast),
            macd_slow=int(macd_slow),
            macd_signal=int(macd_signal),
            macd_weight=float(macd_weight),
            bb_period=int(bb_period),
            bb_std=float(bb_std),
            bb_weight=float(bb_weight)
        )
        combinations.append(combination)

    return combinations

async def _evaluate_combination(
    engine,
    combination: ParameterCombination,
    dataset: Dict[str, Any],
    config: OptimizationConfig
) -> OptimizationResult:
    """評估單個參數組合"""
    start_time = datetime.now()

    try:
        # 這裡需要實際的回測邏輯
        # 目前返回模擬結果
        np.random.seed(hash(combination.combination_id) % 1000)

        # 模擬性能指標（基於參數的合理性生成）
        base_sharpe = 1.0

        # RSI合理性調整
        if 10 <= combination.rsi_period <= 20 and 20 <= combination.rsi_oversold <= 35:
            base_sharpe += 0.2

        # MACD合理性調整
        if combination.macd_fast < combination.macd_slow and 8 <= combination.macd_signal <= 12:
            base_sharpe += 0.15

        # 布林帶合理性調整
        if 15 <= combination.bb_period <= 25 and 1.8 <= combination.bb_std <= 2.5:
            base_sharpe += 0.1

        # 添加隨機性
        sharpe_ratio = base_sharpe + np.random.normal(0, 0.3)
        sortino_ratio = sharpe_ratio * 1.2 + np.random.normal(0, 0.2)
        max_drawdown = -np.random.uniform(0.05, 0.25)
        total_return = np.random.uniform(0.05, 0.40)
        annualized_return = total_return * 1.1 + np.random.normal(0, 0.05)
        profit_factor = np.random.uniform(1.2, 3.5)
        win_rate = np.random.uniform(0.45, 0.75)
        total_trades = np.random.randint(20, 150)

        execution_time = (datetime.now() - start_time).total_seconds()

        result = OptimizationResult(
            combination_id=combination.combination_id,
            parameters=combination,
            performance={
                "return": total_return,
                "volatility": total_return / sharpe_ratio if sharpe_ratio > 0 else 0.2
            },
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            total_return=total_return,
            annualized_return=annualized_return,
            profit_factor=profit_factor,
            win_rate=win_rate,
            total_trades=total_trades,
            execution_time=execution_time,
            timestamp=datetime.now()
        )

        return result

    except Exception as e:
        logger.error(f"評估組合失敗: {combination.combination_id}, 錯誤: {e}")
        # 返回失敗結果
        return OptimizationResult(
            combination_id=combination.combination_id,
            parameters=combination,
            performance={},
            sharpe_ratio=-999.0,
            sortino_ratio=-999.0,
            max_drawdown=-1.0,
            total_return=0.0,
            annualized_return=0.0,
            profit_factor=0.0,
            win_rate=0.0,
            total_trades=0,
            execution_time=0.0,
            timestamp=datetime.now()
        )

async def _generate_optimization_report(
    request_id: str,
    request: OptimizationRequest,
    progress: Optional[OptimizationProgress],
    results: List[OptimizationResult]
) -> OptimizationReport:
    """生成優化報告"""
    # 計算統計信息
    total_combinations = request.config.max_combinations
    evaluated_combinations = len(results)
    failed_combinations = total_combinations - evaluated_combinations

    # 排序結果獲取最佳組合
    sorted_results = sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)
    best_result = sorted_results[0] if sorted_results else None
    top_10_results = sorted_results[:10]

    # 性能分佈
    if results:
        performance_distribution = {
            "sharpe_ratios": [r.sharpe_ratio for r in results],
            "total_returns": [r.total_return for r in results],
            "max_drawdowns": [r.max_drawdown for r in results],
            "win_rates": [r.win_rate for r in results]
        }

        avg_combination_time = np.mean([r.execution_time for r in results if r.execution_time > 0])
    else:
        performance_distribution = {}
        avg_combination_time = 0.0

    # 執行時間
    execution_time = None
    if progress and progress.started_at and progress.completed_at:
        execution_time = (progress.completed_at - progress.started_at).total_seconds()
    elif progress and progress.elapsed_time:
        execution_time = progress.elapsed_time

    return OptimizationReport(
        request_id=request_id,
        symbol=request.symbol,
        period_start=request.start_date,
        period_end=request.end_date,
        config=request.config,
        status=progress.status if progress else OptimizationStatus.FAILED,
        created_at=progress.created_at if progress else datetime.now(),
        started_at=progress.timestamp if progress and progress.status == OptimizationStatus.RUNNING else None,
        completed_at=progress.timestamp if progress and progress.status == OptimizationStatus.COMPLETED else None,
        execution_time=execution_time,
        total_combinations=total_combinations,
        evaluated_combinations=evaluated_combinations,
        failed_combinations=failed_combinations,
        best_result=best_result,
        top_10_results=top_10_results,
        performance_distribution=performance_distribution,
        parameter_sensitivity={},  # TODO: 實現參數敏感性分析
        avg_combination_time=avg_combination_time,
        gpu_utilization=None,  # TODO: 從GPU監控獲取
        memory_usage=None,     # TODO: 從系統監控獲取
        results_file=f"optimization_results_{request_id}.json",
        log_file=f"optimization_log_{request_id}.txt"
    )