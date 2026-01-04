"""
VectorBT Multiprocess API Integration
===================================

將VectorBT多進程回測引擎集成到CBSC系統API中

提供以下端點：
- POST /api/vectorbt/multiprocess/backtest - 多進程回測
- POST /api/vectorbt/multiprocess/optimize - 參數優化
- GET /api/vectorbt/multiprocess/status - 狀態查詢
- GET /api/vectorbt/multiprocess/results/{task_id} - 結果查詢
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, date
import asyncio
import json
import uuid
from enum import Enum

# Internal imports
from src.backtest.vectorbt_multiprocess_engine import (
    VectorBTMultiprocessEngine,
    VectorBTMultiprocessConfig,
    MultiprocessMode,
    run_vectorbt_multiprocess_backtest
)
from src.models.user import User
from src.dependencies import get_current_user, get_db_session

router = APIRouter(prefix="/api/vectorbt/multiprocess", tags=["VectorBT Multiprocess"])

# 全局任務存儲（生產環境建議使用Redis）
active_engines: Dict[str, VectorBTMultiprocessEngine] = {}
task_results: Dict[str, Dict[str, Any]] = {}


class ExecutionModeEnum(str, Enum):
    """執行模式枚舉"""
    PORTFOLIO = "portfolio"
    STRATEGY = "strategy"
    SYMBOL = "symbol"
    PARAMETER = "parameter"
    HYBRID = "hybrid"


class MultiprocessBacktestRequest(BaseModel):
    """多進程回測請求模型"""
    symbols: List[str] = Field(..., description="股票代碼列表")
    strategy_name: str = Field(..., description="策略名稱")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")
    initial_capital: float = Field(100000, description="初始資本")
    commission: float = Field(0.001, description="手續費率")

    # 多進程配置
    execution_mode: ExecutionModeEnum = Field(ExecutionModeEnum.PORTFOLIO, description="執行模式")
    max_workers: int = Field(8, description="最大工作進程數")
    chunk_size: int = Field(10, description="分塊大小")

    # VectorBT配置
    cache_data: bool = Field(True, description="是否緩存數據")
    optimize_memory: bool = Field(True, description="是否優化內存")

    # 策略參數
    strategy_parameters: Dict[str, Any] = Field(default_factory=dict, description="策略參數")

    # 輸出配置
    save_results: bool = Field(True, description="是否保存結果")
    generate_report: bool = Field(True, description="是否生成報告")


class ParameterOptimizationRequest(BaseModel):
    """參數優化請求模型"""
    symbols: List[str] = Field(..., description="股票代碼列表")
    strategy_name: str = Field(..., description="策略名稱")
    start_date: date = Field(..., description="開始日期")
    end_date: date = Field(..., description="結束日期")

    # 參數網格
    param_grid: Dict[str, List[Any]] = Field(..., description="參數網格")

    # 優化配置
    objective: str = Field("sharpe_ratio", description="優化目標")
    execution_mode: ExecutionModeEnum = Field(ExecutionModeEnum.PORTFOLIO, description="執行模式")
    max_workers: int = Field(8, description="最大工作進程數")


class TaskStatusResponse(BaseModel):
    """任務狀態響應模型"""
    task_id: str
    status: str
    progress: float = Field(0.0, ge=0.0, le=1.0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    engine_status: Optional[Dict[str, Any]] = None


class BacktestResultResponse(BaseModel):
    """回測結果響應模型"""
    task_id: str
    status: str
    individual_results: Dict[str, Any]
    aggregated_results: Dict[str, Any]
    execution_stats: Dict[str, Any]
    generated_at: datetime


def get_strategy_function(strategy_name: str) -> callable:
    """
    根據策略名稱獲取策略函數

    Args:
        strategy_name: 策略名稱

    Returns:
        策略函數
    """
    # 這裡需要實現策略函數映射
    # 可以從策略工廠或註冊表中獲取
    strategy_registry = {
        "rsi_mean_reversion": rsi_mean_reversion_strategy,
        "ma_crossover": ma_crossover_strategy,
        "bollinger_bands": bollinger_bands_strategy,
        "macd_crossover": macd_crossover_strategy,
        "dual_momentum": dual_momentum_strategy
    }

    if strategy_name not in strategy_registry:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    return strategy_registry[strategy_name]


# 示例策略函數（需要在實際系統中實現）
def rsi_mean_reversion_strategy(data: Dict, rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
    """RSI均值回歸策略"""
    import numpy as np

    close_prices = data['close'].values if hasattr(data, 'close') else data

    # 計算RSI
    delta = np.diff(close_prices)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.convolve(gain, np.ones(rsi_period)/rsi_period, mode='valid')
    avg_loss = np.convolve(loss, np.ones(rsi_period)/rsi_period, mode='valid')

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    # 生成信號
    entries = np.zeros(len(close_prices), dtype=bool)
    exits = np.zeros(len(close_prices), dtype=bool)

    # RSI信號邏輯
    rsi_extended = np.concatenate([np.full(rsi_period-1, 50), rsi])
    entries[rsi_extended < oversold] = True
    exits[rsi_extended > overbought] = True

    return entries, exits


def ma_crossover_strategy(data: Dict, short_period: int = 10, long_period: int = 30):
    """移動平均線交叉策略"""
    import numpy as np

    close_prices = data['close'].values if hasattr(data, 'close') else data

    # 計算移動平均線
    short_ma = np.convolve(close_prices, np.ones(short_period)/short_period, mode='same')
    long_ma = np.convolve(close_prices, np.ones(long_period)/long_period, mode='same')

    # 生成信號
    entries = np.zeros(len(close_prices), dtype=bool)
    exits = np.zeros(len(close_prices), dtype=bool)

    # MA交叉信號
    cross_above = (short_ma[:-1] <= long_ma[:-1]) & (short_ma[1:] > long_ma[1:])
    cross_below = (short_ma[:-1] >= long_ma[:-1]) & (short_ma[1:] < long_ma[1:])

    entries[1:][cross_above] = True
    exits[1:][cross_below] = True

    return entries, exits


def bollinger_bands_strategy(data: Dict, period: int = 20, std_dev: float = 2.0):
    """布林帶策略"""
    import numpy as np

    close_prices = data['close'].values if hasattr(data, 'close') else data

    # 計算布林帶
    middle_band = np.convolve(close_prices, np.ones(period)/period, mode='same')
    rolling_std = np.array([np.std(close_prices[max(0, i-period+1):i+1]) for i in range(len(close_prices))])
    upper_band = middle_band + std_dev * rolling_std
    lower_band = middle_band - std_dev * rolling_std

    # 生成信號
    entries = np.zeros(len(close_prices), dtype=bool)
    exits = np.zeros(len(close_prices), dtype=bool)

    # 布林帶突破信號
    entries[close_prices < lower_band] = True
    exits[close_prices > upper_band] = True

    return entries, exits


def macd_crossover_strategy(data: Dict, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
    """MACD交叉策略"""
    import numpy as np

    close_prices = data['close'].values if hasattr(data, 'close') else data

    # 計算MACD
    def ema(data, period):
        alpha = 2 / (period + 1)
        ema_values = np.zeros_like(data)
        ema_values[0] = data[0]
        for i in range(1, len(data)):
            ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i-1]
        return ema_values

    ema_fast = ema(close_prices, fast_period)
    ema_slow = ema(close_prices, slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal_period)

    # 生成信號
    entries = np.zeros(len(close_prices), dtype=bool)
    exits = np.zeros(len(close_prices), dtype=bool)

    # MACD交叉信號
    cross_above = (macd_line[:-1] <= signal_line[:-1]) & (macd_line[1:] > signal_line[1:])
    cross_below = (macd_line[:-1] >= signal_line[:-1]) & (macd_line[1:] < signal_line[1:])

    entries[1:][cross_above] = True
    exits[1:][cross_below] = True

    return entries, exits


def dual_momentum_strategy(data: Dict, lookback_period: int = 12, cash_weight: float = 0.6):
    """雙動量策略"""
    import numpy as np

    close_prices = data['close'].values if hasattr(data, 'close') else data

    # 計算動量信號
    returns = np.diff(close_prices) / close_prices[:-1]

    # 滾動回報計算
    momentum_signal = np.zeros(len(close_prices))
    for i in range(lookback_period, len(close_prices)):
        momentum_signal[i] = np.prod(1 + returns[i-lookback_period:i]) - 1

    # 生成信號
    entries = np.zeros(len(close_prices), dtype=bool)
    exits = np.zeros(len(close_prices), dtype=bool)

    # 動量信號邏輯
    entries[momentum_signal > 0] = True
    exits[momentum_signal <= 0] = True

    return entries, exits


async def run_backtest_background(
    task_id: str,
    request: MultiprocessBacktestRequest,
    user_id: int
):
    """
    後台運行回測任務

    Args:
        task_id: 任務ID
        request: 回測請求
        user_id: 用戶ID
    """
    try:
        # 獲取策略函數
        strategy_func = get_strategy_function(request.strategy_name)

        # 創建配置
        config = VectorBTMultiprocessConfig(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            commission=request.commission,
            execution_mode=MultiprocessMode(request.execution_mode.value),
            max_workers=request.max_workers,
            chunk_size=request.chunk_size,
            cache_data=request.cache_data,
            optimize_memory=request.optimize_memory,
            save_results=request.save_results,
            generate_report=request.generate_report
        )

        # 運行回測
        async with VectorBTMultiprocessEngine(config) as engine:
            active_engines[task_id] = engine

            # 運行投資組合回測
            results = await engine.run_portfolio_backtest(
                strategy_func=strategy_func,
                parameters=request.strategy_parameters
            )

            # 聚合結果
            aggregated = await engine.aggregate_results(results)

            # 保存結果
            await engine.save_results(aggregated)

            # 獲取引擎狀態
            engine_status = await engine.get_engine_status()

            # 存儲結果
            task_results[task_id] = {
                'status': 'completed',
                'individual_results': results,
                'aggregated_results': aggregated,
                'engine_status': engine_status,
                'completed_at': datetime.now().isoformat(),
                'user_id': user_id
            }

    except Exception as e:
        # 存儲錯誤信息
        task_results[task_id] = {
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now().isoformat(),
            'user_id': user_id
        }

    finally:
        # 清理引擎
        if task_id in active_engines:
            engine = active_engines[task_id]
            await engine.shutdown()
            del active_engines[task_id]


@router.post("/backtest", response_model=Dict[str, str])
async def start_multiprocess_backtest(
    request: MultiprocessBacktestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    啟動多進程回測任務
    """
    try:
        # 生成任務ID
        task_id = str(uuid.uuid4())[:8]

        # 啟動後台任務
        background_tasks.add_task(
            run_backtest_background,
            task_id,
            request,
            current_user.id
        )

        return {
            "task_id": task_id,
            "status": "started",
            "message": "Multiprocess backtest started successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start backtest: {str(e)}")


@router.post("/optimize", response_model=Dict[str, str])
async def start_parameter_optimization(
    request: ParameterOptimizationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    啟動參數優化任務
    """
    try:
        # 獲取策略函數
        strategy_func = get_strategy_function(request.strategy_name)

        # 生成任務ID
        task_id = f"opt_{str(uuid.uuid4())[:8]}"

        # 創建配置
        config = VectorBTMultiprocessConfig(
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            execution_mode=MultiprocessMode(request.execution_mode.value),
            max_workers=request.max_workers,
            save_results=True
        )

        # 後台運行優化
        async def run_optimization():
            try:
                async with VectorBTMultiprocessEngine(config) as engine:
                    active_engines[task_id] = engine

                    # 運行參數優化
                    optimization_result = await engine.run_parameter_optimization(
                        strategy_func=strategy_func,
                        param_grid=request.param_grid,
                        objective=request.objective
                    )

                    # 存儲結果
                    task_results[task_id] = {
                        'status': 'completed',
                        'optimization_result': optimization_result,
                        'completed_at': datetime.now().isoformat(),
                        'user_id': current_user.id,
                        'task_type': 'parameter_optimization'
                    }

            except Exception as e:
                task_results[task_id] = {
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.now().isoformat(),
                    'user_id': current_user.id,
                    'task_type': 'parameter_optimization'
                }

            finally:
                if task_id in active_engines:
                    engine = active_engines[task_id]
                    await engine.shutdown()
                    del active_engines[task_id]

        # 啟動後台任務
        background_tasks.add_task(run_optimization)

        return {
            "task_id": task_id,
            "status": "started",
            "message": "Parameter optimization started successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start optimization: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    獲取任務狀態
    """
    try:
        # 檢查任務是否存在
        if task_id not in task_results and task_id not in active_engines:
            raise HTTPException(status_code=404, detail="Task not found")

        # 獲取任務結果
        if task_id in task_results:
            result = task_results[task_id]
            return TaskStatusResponse(
                task_id=task_id,
                status=result['status'],
                progress=1.0,
                completed_at=datetime.fromisoformat(result.get('completed_at', '')) if result.get('completed_at') else None,
                error_message=result.get('error'),
                engine_status=result.get('engine_status')
            )

        # 任務仍在運行
        if task_id in active_engines:
            engine = active_engines[task_id]
            engine_status = await engine.get_engine_status()

            # 計算進度
            total_tasks = engine_status['tasks']['total']
            completed_tasks = engine_status['tasks']['completed']
            progress = completed_tasks / total_tasks if total_tasks > 0 else 0.0

            return TaskStatusResponse(
                task_id=task_id,
                status="running",
                progress=progress,
                engine_status=engine_status
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/results/{task_id}", response_model=BacktestResultResponse)
async def get_task_results(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    獲取任務結果
    """
    try:
        # 檢查任務是否存在
        if task_id not in task_results:
            raise HTTPException(status_code=404, detail="Task not found")

        result = task_results[task_id]

        # 檢查權限
        if result.get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 檢查任務狀態
        if result['status'] != 'completed':
            raise HTTPException(status_code=400, detail="Task not completed")

        # 構建響應
        if result.get('task_type') == 'parameter_optimization':
            # 參數優化結果
            return BacktestResultResponse(
                task_id=task_id,
                status=result['status'],
                individual_results={},
                aggregated_results=result['optimization_result'],
                execution_stats={'task_type': 'parameter_optimization'},
                generated_at=datetime.fromisoformat(result.get('completed_at', ''))
            )
        else:
            # 回測結果
            return BacktestResultResponse(
                task_id=task_id,
                status=result['status'],
                individual_results=result.get('individual_results', {}),
                aggregated_results=result.get('aggregated_results', {}),
                execution_stats=result.get('engine_status', {}).get('performance', {}),
                generated_at=datetime.fromisoformat(result.get('completed_at', ''))
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task results: {str(e)}")


@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_user_tasks(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    列出用戶的任務
    """
    try:
        # 過濾用戶任務
        user_tasks = []
        for task_id, result in task_results.items():
            if result.get('user_id') == current_user.id:
                user_tasks.append({
                    'task_id': task_id,
                    'status': result['status'],
                    'created_at': result.get('created_at', ''),
                    'completed_at': result.get('completed_at'),
                    'task_type': result.get('task_type', 'backtest')
                })

        # 排序和分頁
        user_tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        paginated_tasks = user_tasks[offset:offset + limit]

        return paginated_tasks

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    取消任務
    """
    try:
        # 檢查任務是否存在
        if task_id not in active_engines and task_id not in task_results:
            raise HTTPException(status_code=404, detail="Task not found")

        # 檢查權限
        if task_id in task_results and task_results[task_id].get('user_id') != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # 取消運行中的任務
        if task_id in active_engines:
            engine = active_engines[task_id]
            await engine.shutdown()
            del active_engines[task_id]

            # 更新結果狀態
            task_results[task_id] = {
                'status': 'cancelled',
                'completed_at': datetime.now().isoformat(),
                'user_id': current_user.id
            }

        return {"message": "Task cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.get("/engines/status")
async def get_all_engines_status(current_user: User = Depends(get_current_user)):
    """
    獲取所有引擎狀態（管理員功能）
    """
    try:
        # 檢查管理員權限
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        engine_statuses = {}
        for task_id, engine in active_engines.items():
            status = await engine.get_engine_status()
            engine_statuses[task_id] = status

        return {
            "active_engines": len(active_engines),
            "total_tasks": len(task_results),
            "engine_statuses": engine_statuses
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get engines status: {str(e)}")


@router.get("/strategies")
async def list_available_strategies():
    """
    列出可用的策略
    """
    try:
        strategies = [
            {
                "name": "rsi_mean_reversion",
                "display_name": "RSI均值回歸策略",
                "description": "基於RSI指標的均值回歸交易策略",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 50},
                    "oversold": {"type": "float", "default": 30, "min": 10, "max": 50},
                    "overbought": {"type": "float", "default": 70, "min": 50, "max": 90}
                }
            },
            {
                "name": "ma_crossover",
                "display_name": "移動平均線交叉策略",
                "description": "基於移動平均線交叉的趨勢跟隨策略",
                "parameters": {
                    "short_period": {"type": "int", "default": 10, "min": 5, "max": 20},
                    "long_period": {"type": "int", "default": 30, "min": 20, "max": 60}
                }
            },
            {
                "name": "bollinger_bands",
                "display_name": "布林帶策略",
                "description": "基於布林帶的波動率交易策略",
                "parameters": {
                    "period": {"type": "int", "default": 20, "min": 10, "max": 50},
                    "std_dev": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0}
                }
            },
            {
                "name": "macd_crossover",
                "display_name": "MACD交叉策略",
                "description": "基於MACD指標的動量交易策略",
                "parameters": {
                    "fast_period": {"type": "int", "default": 12, "min": 8, "max": 20},
                    "slow_period": {"type": "int", "default": 26, "min": 20, "max": 40},
                    "signal_period": {"type": "int", "default": 9, "min": 5, "max": 15}
                }
            },
            {
                "name": "dual_momentum",
                "display_name": "雙動量策略",
                "description": "結合絕對和相對動量的雙動量策略",
                "parameters": {
                    "lookback_period": {"type": "int", "default": 12, "min": 1, "max": 24},
                    "cash_weight": {"type": "float", "default": 0.6, "min": 0.0, "max": 1.0}
                }
            }
        ]

        return {"strategies": strategies}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")


# 健康檢查端點
@router.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "VectorBT Multiprocess API",
        "active_engines": len(active_engines),
        "total_tasks": len(task_results),
        "timestamp": datetime.now().isoformat()
    }