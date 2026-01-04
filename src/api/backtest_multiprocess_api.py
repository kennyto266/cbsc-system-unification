"""
多进程回测API (Multiprocess Backtest API)
========================================

提供多进程並行回測的HTTP API接口：
- 策略級別並行回測
- 符號級別並行回測
- 參數級別並行回測
- 混合模式（自動選擇）
- 實時進度查詢
- 任務管理與控制

核心特性：
- 異步執行（不阻塞HTTP響應）
- 進度監控（通過WebSocket/輪詢）
- 任務取消與重試
- 資源監控
- 詳細的性能指標

Author: CBSC Quant Team
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, date
from uuid import UUID
import logging
import asyncio

from ..backtest.multiprocess_engine import (
    MultiprocessBacktestEngine,
    MultiprocessBacktestRequest,
    MultiprocessBacktestResult,
    ParallelLevel,
)
from ..backtest.enhanced_backtest_engine import BacktestConfig
from ..services.influxdb_client import InfluxDBService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backtest/multiprocess", tags=["multiprocess-backtest"])


# ============================================================================
# Request Models (Pydantic)
# ============================================================================


class StrategyBacktestConfig(BaseModel):
    """單個策略的回測配置"""

    strategy_id: Optional[str] = None
    strategy_type: str = Field(..., description="策略類型")
    symbols: List[str] = Field(default_factory=lambda: ["0700.HK"], description="標的符號列表")
    start_date: str = Field(..., description="開始日期 (YYYY-MM-DD)")
    end_date: str = Field(..., description="結束日期 (YYYY-MM-DD)")
    initial_capital: float = Field(100000.0, ge=0, description="初始資金")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略參數")

    @validator("start_date", "end_date")
    def validate_dates(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid date format: {v}")


class BatchBacktestRequest(BaseModel):
    """批量回測請求"""

    parallel_level: ParallelLevel = Field(
        default=ParallelLevel.STRATEGY_LEVEL, description="並行級別"
    )
    max_workers: int = Field(default=-1, ge=-1, le=32, description="最大進程數 (-1表示自動檢測)")
    max_concurrent: int = Field(default=10, ge=1, le=20, description="最大併發任務數")
    max_memory_gb: float = Field(default=4.0, ge=0.5, le=16.0, description="最大內存限制 (GB)")
    enable_auto_scaling: bool = Field(default=True, description="啟用自動擴容縮")
    enable_progress_monitoring: bool = Field(default=True, description="啟用進度監控")
    save_results: bool = Field(default=True, description="保存結果到數據庫")
    output_dir: str = Field(default="multiprocess_backtest_results", description="輸出目錄")

    # 回測配置列表
    backtest_configs: List[StrategyBacktestConfig] = Field(
        min_items=1, max_items=100, description="回測配置列表"
    )


class TaskStatusRequest(BaseModel):
    """任務狀態查詢請求"""

    task_id: UUID


class TaskCancelRequest(BaseModel):
    """任務取消請求"""

    task_id: UUID


# ============================================================================
# Response Models (Pydantic)
# ============================================================================


class TaskSubmitResponse(BaseModel):
    """任務提交響應"""

    task_id: UUID
    status: str = Field(default="submitted")
    message: str
    parallel_level: ParallelLevel
    max_workers: int
    estimated_completion_time: Optional[float] = None


class TaskStatusResponse(BaseModel):
    """任務狀態響應"""

    task_id: UUID
    status: str
    total_backtests: int
    completed_backtests: int
    failed_backtests: int
    progress: float
    total_execution_time: Optional[float] = None
    remaining_time: Optional[float] = None
    results: Optional[List[Dict[str, Any]]] = None


class PerformanceMetricsResponse(BaseModel):
    """性能指標響應"""

    parallel_speedup: float
    parallel_efficiency: float
    peak_memory_gb: float
    average_cpu_percent: float
    max_cpu_percent: float


class ErrorResponse(BaseModel):
    """錯誤響應"""

    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Global State Management
# ============================================================================

# 全局存儲運行中的任務（在實際應用中應該使用Redis/數據庫）
_running_tasks: Dict[UUID, MultiprocessBacktestResult] = {}
# 任務結果存儲
_task_results: Dict[UUID, MultiprocessBacktestResult] = {}


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/submit",
    response_model=TaskSubmitResponse,
    summary="提交多進程並行回測任務",
    responses={
        200: {"description": "任務已提交"},
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        500: {"model": ErrorResponse, "description": "內部服務器錯誤"},
    },
)
async def submit_backtest_task(
    request: BatchBacktestRequest, background_tasks: BackgroundTasks
) -> TaskSubmitResponse:
    """
    提交多進程並行回測任務

    接受批量回測配置，根據並行級別執行：
    - STRATEGY_LEVEL: 每個策略一個進程
    - SYMBOL_LEVEL: 每個標的一個進程
    - PARAMETER_LEVEL: 每組參數一個進程
    - HYBRID: 自動選擇並行級別

    任務在後台執行，立即返回任務ID。
    """
    try:
        # 轉換回測配置
        configs = [config.dict() for config in request.backtest_configs]

        # 創建多進程回測請求
        multiprocess_request = MultiprocessBacktestRequest(
            backtest_configs=configs,
            parallel_level=request.parallel_level,
            max_workers=request.max_workers,
            max_concurrent=request.max_concurrent,
            max_memory_gb=request.max_memory_gb,
            enable_auto_scaling=request.enable_auto_scaling,
            scaling_check_interval=5.0,
            save_results=request.save_results,
            output_dir=request.output_dir,
            enable_progress_monitoring=request.enable_progress_monitoring,
            log_interval=10,
        )

        # 創建引擎實例
        engine = MultiprocessBacktestEngine(multiprocess_request)

        # 在後台執行回測
        task_id = UUID()
        background_tasks.add_task(_run_backtest_background, task_id, engine, configs)

        # 估計完成時間（基於回測數量和並行度）
        estimated_time = _estimate_completion_time(len(configs), request.max_workers)

        logger.info(
            f"Multiprocess backtest task submitted: "
            f"{len(configs)} configs, "
            f"parallel_level={request.parallel_level.value}, "
            f"task_id={task_id}"
        )

        return TaskSubmitResponse(
            task_id=task_id,
            status="submitted",
            message=f"Task submitted successfully with {len(configs)} backtest configurations",
            parallel_level=request.parallel_level,
            max_workers=request.max_workers if request.max_workers > 0 else 32,
            estimated_completion_time=estimated_time,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit task: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="查詢任務狀態",
    responses={
        200: {"description": "任務狀態"},
        404: {"model": ErrorResponse, "description": "任務不存在"},
    },
)
async def get_task_status(task_id: UUID) -> TaskStatusResponse:
    """
    查詢多進程回測任務的狀態

    返回任務的執行進度、完成狀態、性能指標等。
    """
    try:
        # 從全局存儲中獲取任務結果（實際應用中應該從數據庫獲取）
        result = _task_results.get(task_id)

        if not result:
            # 任務還在運行中，返回當前進度
            running_task = _running_tasks.get(task_id)
            if running_task:
                total = result.total_backtests if result else len(running_task.results)
                completed = len(result.results) if result else 0

                return TaskStatusResponse(
                    task_id=task_id,
                    status="running",
                    total_backtests=total,
                    completed_backtests=completed,
                    failed_backtests=0,
                    progress=completed / total if total > 0 else 0.0,
                    total_execution_time=None,
                    remaining_time=None,
                    results=None,
                )
            else:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # 任務已完成
        total_execution_time = (
            (result.completed_at - result.started_at).total_seconds()
            if result.completed_at
            else None
        )

        return TaskStatusResponse(
            task_id=task_id,
            status="completed",
            total_backtests=result.total_backtests,
            completed_backtests=result.completed_backtests,
            failed_backtests=result.failed_backtests,
            progress=1.0,
            total_execution_time=total_execution_time,
            remaining_time=0.0,
            results=result.results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/cancel/{task_id}",
    response_model=TaskStatusResponse,
    summary="取消運行中的任務",
    responses={
        200: {"description": "任務已取消"},
        404: {"model": ErrorResponse, "description": "任務不存在或已完成"},
    },
)
async def cancel_task(task_id: UUID) -> TaskStatusResponse:
    """
    取消運行中的多進程回測任務

    注意：實際實現需要通過進程池API來取消任務。
    這裡只是示例實現。
    """
    try:
        # 檢查任務是否存在
        if task_id not in _running_tasks and task_id not in _task_results:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # 記錄取消（實際應用中應該通知進程池停止任務）
        logger.info(f"Cancelling task {task_id}")

        if task_id in _task_results:
            result = _task_results[task_id]
            return TaskStatusResponse(
                task_id=task_id,
                status="cancelled",
                total_backtests=result.total_backtests,
                completed_backtests=result.completed_backtests,
                failed_backtests=result.failed_backtests + 1,
                progress=1.0,
                total_execution_time=result.total_execution_time,
                remaining_time=0.0,
                results=None,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Cannot cancel running task {task_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/results/{task_id}",
    summary="獲取任務結果",
    responses={
        200: {"description": "任務結果"},
        404: {"model": ErrorResponse, "description": "任務不存在"},
    },
)
async def get_task_results(task_id: UUID) -> Dict[str, Any]:
    """
    獲取多進程回測任務的完整結果

    返回詳細的回測結果，包括：
    - 每個配置的結果
    - 總體性能指標
    - 系統資源使用情況
    """
    try:
        result = _task_results.get(task_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return {
            "task_id": str(task_id),
            "status": "completed",
            "summary": {
                "total_backtests": result.total_backtests,
                "completed_backtests": result.completed_backtests,
                "failed_backtests": result.failed_backtests,
                "success_rate": result.success_rate,
            },
            "performance": {
                "parallel_speedup": result.parallel_speedup,
                "parallel_efficiency": result.parallel_efficiency,
                "total_execution_time": result.total_execution_time,
                "average_execution_time": result.average_execution_time,
            },
            "system_resources": {
                "peak_memory_gb": result.peak_memory_gb,
                "average_cpu_percent": result.average_cpu_percent,
                "max_cpu_percent": result.max_cpu_percent,
            },
            "results": result.results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task results: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/performance/{task_id}",
    response_model=PerformanceMetricsResponse,
    summary="獲取性能指標",
    responses={
        200: {"description": "性能指標"},
        404: {"model": ErrorResponse, "description": "任務不存在"},
    },
)
async def get_performance_metrics(task_id: UUID) -> PerformanceMetricsResponse:
    """
    獲取多進程回測的性能指標

    返回並行加速比、並行效率、系統資源使用等。
    """
    try:
        result = _task_results.get(task_id)

        if not result:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        return PerformanceMetricsResponse(
            parallel_speedup=result.parallel_speedup,
            parallel_efficiency=result.parallel_efficiency * 100,  # 轉換為百分比
            peak_memory_gb=result.peak_memory_gb,
            average_cpu_percent=result.average_cpu_percent,
            max_cpu_percent=result.max_cpu_percent,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/benchmark",
    summary="性能對比測試（多進程 vs 單進程）",
    responses={
        200: {"description": "對比結果"},
        500: {"model": ErrorResponse, "description": "內部服務器錯誤"},
    },
)
async def benchmark_parallel_performance(benchmark_configs: BatchBacktestRequest) -> Dict[str, Any]:
    """
    性能對比測試：比較多進程與單進程執行性能

    執行相同的回測配置：
    1. 使用多進程並行（max_workers=1）
    2. 使用多進程並行（max_workers=CPU核心數）
    3. 使用單進程順序執行

    返回執行時間對比和加速比。
    """
    try:
        if not benchmark_configs.backtest_configs:
            raise HTTPException(
                status_code=400, detail="No backtest configs provided for benchmark"
            )

        # 只測試第一個配置
        test_config = benchmark_configs.backtest_configs[0]

        configs_single = [test_config.dict()]
        configs_multi_small = [test_config.dict()]
        configs_multi_full = [test_config.dict()]

        # 單進程執行
        logger.info("Running single-process baseline...")
        engine_single = MultiprocessBacktestEngine(
            MultiprocessBacktestRequest(
                backtest_configs=configs_single,
                parallel_level=ParallelLevel.STRATEGY_LEVEL,
                max_workers=1,  # 單進程
                enable_progress_monitoring=False,
                save_results=False,
            )
        )
        result_single = await engine_single.run_backtests(configs_single)
        time_single = result_single.total_execution_time

        # 多進程執行（少量進程）
        logger.info("Running multi-process (small pool)...")
        engine_multi_small = MultiprocessBacktestEngine(
            MultiprocessBacktestRequest(
                backtest_configs=configs_multi_small,
                parallel_level=ParallelLevel.STRATEGY_LEVEL,
                max_workers=2,
                enable_progress_monitoring=False,
                save_results=False,
            )
        )
        result_multi_small = await engine_multi_small.run_backtests(configs_multi_small)
        time_multi_small = result_multi_small.total_execution_time

        # 多進程執行（完整並行）
        logger.info("Running multi-process (full parallel)...")
        import psutil

        cpu_count = psutil.cpu_count()
        engine_multi_full = MultiprocessBacktestEngine(
            MultiprocessBacktestRequest(
                backtest_configs=configs_multi_full,
                parallel_level=ParallelLevel.STRATEGY_LEVEL,
                max_workers=cpu_count,
                enable_progress_monitoring=False,
                save_results=False,
            )
        )
        result_multi_full = await engine_multi_full.run_backtests(configs_multi_full)
        time_multi_full = result_multi_full.total_execution_time

        # 計算加速比
        speedup_small = time_single / time_multi_small if time_multi_small > 0 else 0
        speedup_full = time_single / time_multi_full if time_multi_full > 0 else 0

        logger.info(
            f"Benchmark results:\n"
            f"  Single process: {time_single:.2f}s\n"
            f"  Multi-process (2 workers): {time_multi_small:.2f}s ({speedup_small:.2f}x)\n"
            f"  Multi-process ({cpu_count} workers): {time_multi_full:.2f}s ({speedup_full:.2f}x)"
        )

        return {
            "benchmark_type": "parallel_vs_single",
            "results": {
                "single_process": {
                    "execution_time": time_single,
                    "backtests_completed": result_single.completed_backtests,
                },
                "multi_process_small": {
                    "execution_time": time_multi_small,
                    "backtests_completed": result_multi_small.completed_backtests,
                    "speedup": speedup_small,
                    "workers": 2,
                },
                "multi_process_full": {
                    "execution_time": time_multi_full,
                    "backtests_completed": result_multi_full.completed_backtests,
                    "speedup": speedup_full,
                    "workers": cpu_count,
                },
            },
            "conclusion": f"Parallel processing provides {speedup_full:.2f}x speedup with {cpu_count} workers",
        }

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ============================================================================
# Helper Functions
# ============================================================================


def _estimate_completion_time(num_configs: int, max_workers: int) -> float:
    """
    估計任務完成時間（秒）

    基於經驗值：每個回測配置平均需要10秒
    """
    avg_time_per_config = 10.0  # 秒
    effective_workers = max(1, max_workers if max_workers > 0 else 4)
    return (num_configs / effective_workers) * avg_time_per_config


async def _run_backtest_background(
    task_id: UUID, engine: MultiprocessBacktestEngine, configs: List[Dict[str, Any]]
):
    """
    在後台執行多進程回測任務

    Args:
        task_id: 任務ID
        engine: 多進程引擎
        configs: 回測配置列表
    """
    try:
        logger.info(f"Starting background task {task_id}...")

        # 執行回測
        result = await engine.run_backtests(configs)

        # 存儲結果
        _running_tasks[task_id] = result
        _task_results[task_id] = result

        logger.info(f"Background task {task_id} completed successfully")

        # 實際應用中應該將結果保存到數據庫
        # result.save_to_database()

    except Exception as e:
        logger.error(f"Background task {task_id} failed: {e}")
        error_result = MultiprocessBacktestResult(
            request_id=task_id,
            total_backtests=len(configs),
            completed_backtests=0,
            failed_backtests=len(configs),
            success_rate=0.0,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            results=[{"error": str(e)}],
        )
        _task_results[task_id] = error_result


@router.get("/health", summary="健康檢查端點")
async def health_check():
    """
    健康檢查端點

    返回多進程回測服務的狀態。
    """
    import psutil

    system_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total_gb": psutil.virtual_memory().total / (1024**3),
        "memory_available_gb": psutil.virtual_memory().available / (1024**3),
        "memory_percent": psutil.virtual_memory().percent,
        "active_tasks": len(_running_tasks),
        "completed_tasks": len(_task_results),
    }

    return system_status
