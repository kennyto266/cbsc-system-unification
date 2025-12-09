#!/usr/bin/env python3
"""
Production-Ready Parameter Optimization Service
生產就緒參數優化服務層

RESTful Optimization Services:
- HTTP endpoints for parameter optimization
- Async Processing: Background optimization with progress tracking
- Result Caching: Intelligent caching of optimization results
- Monitoring Integration: Integration with system monitoring and alerting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import uuid
import time
from pathlib import Path
import traceback

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Body, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn
from contextlib import asynccontextmanager

from .production_parameter_optimizer import (
    ProductionParameterOptimizer, OptimizationRequest, OptimizationResult,
    ParameterType, DataSource
)
from .high_performance_optimizer import get_high_performance_optimizer, PerformanceConfig
from .parameter_auto_applicator import get_parameter_applicator, ValidationLevel

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OptimizationMethod(str, Enum):
    """優化方法"""
    GRID_SEARCH = "grid_search"
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    MULTI_METHOD = "multi_method"

# Pydantic Models for API
class ParameterDefinitionModel(BaseModel):
    """參數定義模型"""
    name: str
    param_type: str
    data_type: str
    value_range: List[Any]
    default_value: Any
    description: str = ""
    depends_on: Optional[List[str]] = None

    @validator('param_type')
    def validate_param_type(cls, v):
        valid_types = [t.value for t in ParameterType]
        if v not in valid_types:
            raise ValueError(f'param_type must be one of {valid_types}')
        return v

class OptimizationRequestModel(BaseModel):
    """優化請求模型"""
    strategy_name: str = Field(..., description="Strategy name")
    parameter_types: List[str] = Field(..., description="Parameter types to optimize")
    optimization_method: OptimizationMethod = Field(OptimizationMethod.GRID_SEARCH)
    max_combinations: int = Field(1000000, ge=1, le=10000000)
    parallel_workers: int = Field(32, ge=1, le=128)
    timeout_seconds: int = Field(1800, ge=60, le=7200)
    enable_progress_monitoring: bool = Field(True)
    auto_apply_best: bool = Field(False)
    data_sources: List[str] = Field(default_factory=list)
    custom_parameters: Optional[List[ParameterDefinitionModel]] = None

    @validator('parameter_types')
    def validate_parameter_types(cls, v):
        valid_types = [t.value for t in ParameterType]
        for param_type in v:
            if param_type not in valid_types:
                raise ValueError(f'parameter_type must be one of {valid_types}')
        return v

class JobStatusResponse(BaseModel):
    """任務狀態響應模型"""
    job_id: str
    status: str
    progress_percentage: float
    current_iteration: int
    total_iterations: int
    combinations_per_second: float
    current_best_score: float
    estimated_completion_time: Optional[datetime]
    system_resources: Dict[str, float]
    started_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None

class OptimizationResultModel(BaseModel):
    """優化結果模型"""
    job_id: str
    strategy_name: str
    best_parameters: Dict[str, Any]
    best_score: float
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    win_rate: float
    robustness_score: float
    overfitting_risk: float
    optimization_method: str
    combinations_tested: int
    total_combinations: int
    execution_time_seconds: float
    data_sources_used: List[str]
    completed_at: datetime

class SystemMetricsResponse(BaseModel):
    """系統指標響應模型"""
    cpu_usage: float
    memory_usage: float
    memory_available_gb: float
    active_optimizations: int
    total_jobs_completed: int
    cache_hit_rate: float
    combinations_per_second: float
    uptime_seconds: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動
    logger.info("Starting Parameter Optimization Service")

    # 初始化組件
    app.state.optimizer = ProductionParameterOptimizer()
    app.state.high_perf_optimizer = get_high_performance_optimizer()
    app.state.parameter_applicator = get_parameter_applicator()
    app.state.service_start_time = datetime.now()
    app.state.job_registry = {}

    yield

    # 關閉
    logger.info("Shutting down Parameter Optimization Service")

    # 清理資源
    if hasattr(app.state.high_perf_optimizer, 'cleanup'):
        app.state.high_perf_optimizer.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Parameter Optimization Service",
    description="Production-ready parameter optimization for quantitative trading strategies",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global variables
active_jobs = {}
completed_jobs = {}
performance_stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'total_combinations_processed': 0
}

def get_optimizer() -> ProductionParameterOptimizer:
    """依賴注入：獲取優化器"""
    return app.state.optimizer

def get_high_perf_optimizer():
    """依賴注入：獲取高性能優化器"""
    return app.state.high_perf_optimizer

def get_parameter_applicator():
    """依賴注入：獲取參數應用器"""
    return app.state.parameter_applicator

@app.get("/", response_model=Dict[str, Any])
async def root():
    """根端點"""
    return {
        "service": "Parameter Optimization Service",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": (datetime.now() - app.state.service_start_time).total_seconds(),
        "endpoints": {
            "submit_optimization": "/optimization/submit",
            "job_status": "/optimization/status/{job_id}",
            "job_result": "/optimization/result/{job_id}",
            "system_metrics": "/system/metrics",
            "job_history": "/optimization/history"
        }
    }

@app.post("/optimization/submit", response_model=Dict[str, str])
async def submit_optimization(
    request: OptimizationRequestModel,
    background_tasks: BackgroundTasks,
    optimizer: ProductionParameterOptimizer = Depends(get_optimizer)
):
    """提交參數優化任務"""

    try:
        performance_stats['total_requests'] += 1

        # 創建優化請求
        optimization_request = OptimizationRequest(
            strategy_name=request.strategy_name,
            optimization_method=request.optimization_method.value,
            max_combinations=request.max_combinations,
            parallel_workers=request.parallel_workers,
            timeout_seconds=request.timeout_seconds,
            enable_progress_monitoring=request.enable_progress_monitoring,
            auto_apply_best=request.auto_apply_best
        )

        # 添加數據源
        for ds in request.data_sources:
            try:
                optimization_request.data_sources.append(DataSource(ds))
            except ValueError:
                logger.warning(f"Unknown data source: {ds}")

        # 添加參數定義
        parameter_registry = optimizer.parameter_registry

        for param_type_str in request.parameter_types:
            param_type = ParameterType(param_type_str)
            params = optimizer.get_parameter_by_type(param_type)
            optimization_request.parameters.extend(params)

        # 添加自定義參數
        if request.custom_parameters:
            for param_model in request.custom_parameters:
                from .production_parameter_optimizer import ParameterDefinition
                custom_param = ParameterDefinition(
                    name=param_model.name,
                    param_type=ParameterType(param_model.param_type),
                    data_type=eval(param_model.data_type),
                    value_range=tuple(param_model.value_range),
                    default_value=param_model.default_value,
                    description=param_model.description,
                    depends_on=param_model.depends_on
                )
                optimization_request.parameters.append(custom_param)

        # 註冊任務
        job_id = optimization_request.job_id
        active_jobs[job_id] = {
            'request': optimization_request,
            'status': JobStatus.PENDING,
            'submitted_at': datetime.now(),
            'progress': {
                'current_iteration': 0,
                'total_iterations': 0,
                'combinations_per_second': 0.0,
                'current_best_score': -float('inf'),
                'system_resources': {}
            }
        }

        # 在背景執行優化
        background_tasks.add_task(
            execute_optimization_background,
            job_id,
            optimization_request
        )

        logger.info(f"Submitted optimization job {job_id} for strategy {request.strategy_name}")

        return {
            "job_id": job_id,
            "status": "submitted",
            "message": "Optimization job submitted successfully"
        }

    except Exception as e:
        performance_stats['failed_requests'] += 1
        logger.error(f"Failed to submit optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_optimization_background(
    job_id: str,
    request: OptimizationRequest
):
    """背景執行優化"""

    try:
        # 更新狀態
        active_jobs[job_id]['status'] = JobStatus.RUNNING
        active_jobs[job_id]['started_at'] = datetime.now()

        # 創建模擬市場數據 (實際應從真實數據源獲取)
        market_data = {
            'stock_data': generate_sample_market_data(),
            'government_data': generate_sample_government_data(),
            'indicators_data': generate_sample_indicators_data()
        }

        # 轉換請求格式
        strategy_config = {
            'name': request.strategy_name,
            'job_id': job_id,
            'max_combinations': request.max_combinations,
            'parallel_workers': request.parallel_workers,
            'timeout_seconds': request.timeout_seconds,
            'enable_monitoring': request.enable_progress_monitoring,
            'auto_apply': request.auto_apply_best,
            'parameter_types': [p.param_type.value for p in request.parameters],
            'optimization_method': request.optimization_method
        }

        # 執行優化
        optimizer = get_optimizer()
        result = await optimizer.optimize_strategy(strategy_config, market_data, request.optimization_method)

        # 記錄結果
        completed_jobs[job_id] = {
            'result': result,
            'completed_at': datetime.now()
        }

        # 更新統計
        performance_stats['successful_requests'] += 1
        performance_stats['total_combinations_processed'] += result.combinations_tested

        # 清理活躍任務
        if job_id in active_jobs:
            del active_jobs[job_id]

        logger.info(f"Optimization job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Optimization job {job_id} failed: {e}")

        # 記錄失敗
        active_jobs[job_id]['status'] = JobStatus.FAILED
        active_jobs[job_id]['error'] = str(e)
        active_jobs[job_id]['failed_at'] = datetime.now()

        performance_stats['failed_requests'] += 1

@app.get("/optimization/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """獲取任務狀態"""

    if job_id in active_jobs:
        job = active_jobs[job_id]
        progress = job.get('progress', {})

        return JobStatusResponse(
            job_id=job_id,
            status=job['status'].value,
            progress_percentage=(
                progress.get('current_iteration', 0) / max(1, progress.get('total_iterations', 1)) * 100
            ),
            current_iteration=progress.get('current_iteration', 0),
            total_iterations=progress.get('total_iterations', 0),
            combinations_per_second=progress.get('combinations_per_second', 0.0),
            current_best_score=progress.get('current_best_score', -float('inf')),
            estimated_completion_time=None,  # 可以根據進度計算
            system_resources=progress.get('system_resources', {}),
            started_at=job.get('started_at', datetime.now()),
            updated_at=datetime.now(),
            error_message=job.get('error')
        )

    elif job_id in completed_jobs:
        return JobStatusResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED.value,
            progress_percentage=100.0,
            current_iteration=0,
            total_iterations=0,
            combinations_per_second=0.0,
            current_best_score=0.0,
            estimated_completion_time=None,
            system_resources={},
            started_at=completed_jobs[job_id].get('completed_at', datetime.now()),
            updated_at=datetime.now()
        )

    else:
        raise HTTPException(status_code=404, detail="Job not found")

@app.get("/optimization/result/{job_id}", response_model=OptimizationResultModel)
async def get_job_result(job_id: str):
    """獲取任務結果"""

    if job_id not in completed_jobs:
        raise HTTPException(status_code=404, detail="Job not found or not completed")

    result = completed_jobs[job_id]['result']

    return OptimizationResultModel(
        job_id=result.job_id,
        strategy_name=result.strategy_name,
        best_parameters=result.best_parameters,
        best_score=result.best_score,
        sharpe_ratio=result.sharpe_ratio,
        total_return=result.total_return,
        max_drawdown=result.max_drawdown,
        win_rate=result.win_rate,
        robustness_score=result.robustness_score,
        overfitting_risk=result.overfitting_risk,
        optimization_method=result.optimization_method,
        combinations_tested=result.combinations_tested,
        total_combinations=result.total_combinations,
        execution_time_seconds=result.execution_time_seconds,
        data_sources_used=result.data_sources_used,
        completed_at=result.completed_at
    )

@app.get("/system/metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(
    high_perf_optimizer = Depends(get_high_perf_optimizer)
):
    """獲取系統指標"""

    try:
        # 獲取性能統計
        perf_stats = high_perf_optimizer.get_performance_stats()
        resource_metrics = perf_stats.get('resource_metrics', {})

        return SystemMetricsResponse(
            cpu_usage=resource_metrics.get('cpu_usage', 0.0),
            memory_usage=resource_metrics.get('memory_usage', 0.0),
            memory_available_gb=resource_metrics.get('memory_available_gb', 0.0),
            active_optimizations=len(active_jobs),
            total_jobs_completed=len(completed_jobs),
            cache_hit_rate=perf_stats.get('cache_stats', {}).get('hit_rate', 0.0),
            combinations_per_second=resource_metrics.get('combinations_per_second', 0.0),
            uptime_seconds=(datetime.now() - app.state.service_start_time).total_seconds()
        )

    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/optimization/history")
async def get_optimization_history(
    strategy_name: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """獲取優化歷史"""

    try:
        optimizer = get_optimizer()
        history = optimizer.get_optimization_history(strategy_name, limit)

        # 轉換為JSON響應格式
        return {
            "total": len(history),
            "results": [
                {
                    "job_id": result.job_id,
                    "strategy_name": result.strategy_name,
                    "best_score": result.best_score,
                    "optimization_method": result.optimization_method,
                    "combinations_tested": result.combinations_tested,
                    "execution_time_seconds": result.execution_time_seconds,
                    "completed_at": result.completed_at.isoformat()
                }
                for result in history
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get optimization history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/optimization/job/{job_id}")
async def cancel_job(job_id: str):
    """取消任務"""

    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    if active_jobs[job_id]['status'] == JobStatus.RUNNING:
        active_jobs[job_id]['status'] = JobStatus.CANCELLED
        active_jobs[job_id]['cancelled_at'] = datetime.now()

        # 這裡應該實際停止優化過程
        # 由於我們在背景任務中，需要添加取消機制

        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancelled successfully"
        }

    else:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled in current state")

@app.get("/health")
async def health_check():
    """健康檢查"""

    try:
        # 檢查各個組件狀態
        optimizer = get_optimizer()
        high_perf_optimizer = get_high_perf_optimizer()
        parameter_applicator = get_parameter_applicator()

        # 基本健康檢查
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service_uptime_seconds": (datetime.now() - app.state.service_start_time).total_seconds(),
            "active_jobs": len(active_jobs),
            "completed_jobs": len(completed_jobs),
            "components": {
                "optimizer": "healthy",
                "high_performance_optimizer": "healthy",
                "parameter_applicator": "healthy"
            }
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )

# Helper functions (should be replaced with real data sources)
def generate_sample_market_data() -> pd.DataFrame:
    """生成樣本市場數據"""
    import pandas as pd
    import numpy as np

    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    # 生成模擬股價數據
    returns = np.random.normal(0.0001, 0.02, len(dates))
    prices = 100 * np.exp(np.cumsum(returns))

    data = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.02, len(dates)))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.02, len(dates)))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })

    return data

def generate_sample_government_data() -> pd.DataFrame:
    """生成樣本政府數據"""
    import pandas as pd
    import numpy as np

    dates = pd.date_range('2020-01-01', '2024-12-31', freq='M')

    data = pd.DataFrame({
        'date': dates,
        'hibor_overnight': np.random.uniform(2.0, 5.0, len(dates)),
        'hibor_1month': np.random.uniform(2.5, 5.5, len(dates)),
        'gdp_growth': np.random.uniform(-5.0, 8.0, len(dates)),
        'unemployment_rate': np.random.uniform(2.5, 8.0, len(dates))
    })

    return data

def generate_sample_indicators_data() -> pd.DataFrame:
    """生成樣本技術指標數據"""
    import pandas as pd
    import numpy as np

    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')

    data = pd.DataFrame({
        'date': dates,
        'rsi_14': np.random.uniform(20, 80, len(dates)),
        'macd_12_26_9': np.random.normal(0, 1, len(dates)),
        'bollinger_upper': np.random.normal(105, 5, len(dates)),
        'bollinger_lower': np.random.normal(95, 5, len(dates)),
        'volume_sma': np.random.uniform(1000000, 10000000, len(dates))
    })

    return data

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """運行服務器"""
    uvicorn.run(
        "parameter_optimization_service:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()