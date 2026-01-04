"""
Backtest API Service
====================

RESTful API endpoints for the Universal Backtest Engine.
Provides endpoints for submitting, monitoring, and retrieving backtest results.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio
import json
import logging
from contextlib import asynccontextmanager

from ..backtest.universal_backtest_engine import (
    UniversalBacktestEngine,
    BacktestTask,
    BacktestType,
    TaskPriority,
    BacktestResult,
    BacktestStatus
)

logger = logging.getLogger(__name__)


# Pydantic models for API
class BacktestRequest(BaseModel):
    """Backtest request model"""
    strategy_id: str = Field(..., description="Strategy ID")
    strategy_name: str = Field(..., description="Strategy name")
    strategy_config: Dict[str, Any] = Field(..., description="Strategy configuration")
    backtest_type: BacktestType = Field(BacktestType.STANDARD, description="Backtest type")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    initial_capital: float = Field(1000000.0, gt=0, description="Initial capital")
    commission_rate: float = Field(0.001, ge=0, le=0.01, description="Commission rate")
    slippage_rate: float = Field(0.0005, ge=0, le=0.01, description="Slippage rate")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="Task priority")
    max_runtime: Optional[int] = Field(None, description="Maximum runtime in seconds")
    tags: List[str] = Field(default_factory=list, description="Tags")
    monte_carlo_config: Optional[Dict[str, Any]] = Field(None, description="Monte Carlo config")
    stress_scenarios: List[str] = Field(default_factory=list, description="Stress test scenarios")
    optimization_params: Optional[Dict[str, Any]] = Field(None, description="Optimization parameters")


class BacktestStatusResponse(BaseModel):
    """Backtest status response"""
    task_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[float] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None


class BacktestResultResponse(BaseModel):
    """Backtest result response"""
    task_id: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Performance metrics
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0

    # Risk metrics
    var_95: float = 0.0
    var_99: float = 0.0
    expected_shortfall_95: float = 0.0
    expected_shortfall_99: float = 0.0

    # Trade statistics
    total_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0

    # Special results
    monte_carlo_summary: Optional[Dict[str, Any]] = None
    stress_test_summary: Optional[Dict[str, Any]] = None
    optimization_summary: Optional[Dict[str, Any]] = None

    # Error info
    error_message: Optional[str] = None


class BatchBacktestRequest(BaseModel):
    """Batch backtest request"""
    backtests: List[BacktestRequest] = Field(..., description="List of backtest requests")
    parallel: bool = Field(True, description="Run in parallel")


class StatisticsResponse(BaseModel):
    """Engine statistics response"""
    active_tasks: int
    queue_size: int
    completed_tasks: int
    failed_tasks: int
    cache_hits: int
    cache_misses: int
    workers: int
    memory_results: int


# Global engine instance
engine: Optional[UniversalBacktestEngine] = None
active_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global engine

    # Initialize engine
    engine = UniversalBacktestEngine(
        postgres_dsn="postgresql://cbsc_user:cbsc_password@localhost:5432/cbsc_backtest",
        influxdb_url="http://localhost:8086",
        redis_url="redis://localhost:6379/0",
        max_workers=4,
        enable_caching=True
    )

    if await engine.initialize():
        logger.info("Backtest engine initialized successfully")

        # Start background workers
        for i in range(engine.max_workers):
            asyncio.create_task(engine.run_worker())

        logger.info(f"Started {engine.max_workers} backtest workers")
    else:
        logger.error("Failed to initialize backtest engine")
        raise RuntimeError("Failed to initialize backtest engine")

    yield

    # Cleanup
    if engine:
        await engine.cleanup()


# Create FastAPI app
app = FastAPI(
    title="CBSC Backtest API",
    description="API for running and managing backtests",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Keep connection alive and respond to pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_update(message: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients"""
    for connection in active_connections.copy():
        try:
            await connection.send_text(json.dumps(message))
        except:
            # Remove disconnected clients
            active_connections.remove(connection)


# API Endpoints
@app.post("/api/v1/backtest", response_model=Dict[str, str])
async def submit_backtest(request: BacktestRequest):
    """
    Submit a new backtest task

    Returns:
        task_id: The ID of the submitted task
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    try:
        # Convert dates
        start_date = datetime.combine(request.start_date, datetime.min.time())
        end_date = datetime.combine(request.end_date, datetime.min.time())

        # Submit task
        task_id = await engine.submit_backtest(
            strategy_config=request.strategy_config,
            backtest_type=request.backtest_type,
            start_date=start_date,
            end_date=end_date,
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            slippage_rate=request.slippage_rate,
            priority=request.priority,
            max_runtime=request.max_runtime,
            tags=request.tags,
            monte_carlo_config=request.monte_carlo_config,
            stress_scenarios=request.stress_scenarios,
            optimization_params=request.optimization_params
        )

        # Broadcast new task
        await broadcast_update({
            "type": "task_submitted",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })

        return {"task_id": task_id}

    except Exception as e:
        logger.error(f"Failed to submit backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backtest/batch", response_model=Dict[str, List[str]])
async def submit_batch_backtest(request: BatchBacktestRequest):
    """
    Submit multiple backtest tasks

    Returns:
        task_ids: List of submitted task IDs
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    task_ids = []

    try:
        for backtest_request in request.backtests:
            # Convert dates
            start_date = datetime.combine(backtest_request.start_date, datetime.min.time())
            end_date = datetime.combine(backtest_request.end_date, datetime.min.time())

            # Submit task
            task_id = await engine.submit_backtest(
                strategy_config=backtest_request.strategy_config,
                backtest_type=backtest_request.backtest_type,
                start_date=start_date,
                end_date=end_date,
                initial_capital=backtest_request.initial_capital,
                commission_rate=backtest_request.commission_rate,
                slippage_rate=backtest_request.slippage_rate,
                priority=backtest_request.priority,
                max_runtime=backtest_request.max_runtime,
                tags=backtest_request.tags,
                monte_carlo_config=backtest_request.monte_carlo_config,
                stress_scenarios=backtest_request.stress_scenarios,
                optimization_params=backtest_request.optimization_params
            )

            task_ids.append(task_id)

        # Broadcast batch submission
        await broadcast_update({
            "type": "batch_submitted",
            "task_ids": task_ids,
            "count": len(task_ids),
            "timestamp": datetime.now().isoformat()
        })

        return {"task_ids": task_ids}

    except Exception as e:
        logger.error(f"Failed to submit batch backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backtest/{task_id}/status", response_model=BacktestStatusResponse)
async def get_backtest_status(task_id: str):
    """
    Get the status of a backtest task

    Args:
        task_id: The ID of the task

    Returns:
        Current status of the task
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    try:
        result = await engine.get_task_status(task_id)

        if not result:
            raise HTTPException(status_code=404, detail="Task not found")

        return BacktestStatusResponse(
            task_id=result.task_id,
            status=result.status.value,
            started_at=result.started_at,
            completed_at=result.completed_at,
            error_message=result.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backtest/{task_id}/result", response_model=BacktestResultResponse)
async def get_backtest_result(task_id: str):
    """
    Get the result of a backtest task

    Args:
        task_id: The ID of the task

    Returns:
        Backtest result if completed
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    try:
        result = await engine.get_task_status(task_id)

        if not result:
            raise HTTPException(status_code=404, detail="Task not found")

        if result.status != BacktestStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Task not completed")

        return BacktestResultResponse(
            task_id=result.task_id,
            status=result.status.value,
            started_at=result.started_at,
            completed_at=result.completed_at,
            total_return=result.total_return,
            annualized_return=result.annualized_return,
            volatility=result.volatility,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            calmar_ratio=result.calmar_ratio,
            var_95=result.var_95,
            var_99=result.var_99,
            expected_shortfall_95=result.expected_shortfall_95,
            expected_shortfall_99=result.expected_shortfall_99,
            total_trades=result.total_trades,
            win_rate=result.win_rate,
            avg_win=result.avg_win,
            avg_loss=result.avg_loss,
            profit_factor=result.profit_factor,
            monte_carlo_summary=result.monte_carlo_results.__dict__ if result.monte_carlo_results else None,
            stress_test_summary=result.stress_test_results,
            optimization_summary=result.optimization_results,
            error_message=result.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task result: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backtest/{task_id}/equity-curve")
async def get_equity_curve(task_id: str):
    """
    Get the equity curve data for a backtest

    Args:
        task_id: The ID of the task

    Returns:
        Equity curve data as JSON
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    try:
        result = await engine.get_task_status(task_id)

        if not result:
            raise HTTPException(status_code=404, detail="Task not found")

        if result.status != BacktestStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Task not completed")

        if not result.equity_curve:
            raise HTTPException(status_code=404, detail="No equity curve data")

        # Convert to JSON-serializable format
        equity_data = [
            {"date": date.isoformat(), "value": float(value)}
            for date, value in result.equity_curve.items()
        ]

        return {"equity_curve": equity_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get equity curve: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/backtest/{task_id}")
async def cancel_backtest(task_id: str):
    """
    Cancel a running backtest task

    Args:
        task_id: The ID of the task

    Returns:
        Success message
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    try:
        success = await engine.cancel_task(task_id)

        if not success:
            raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")

        # Broadcast cancellation
        await broadcast_update({
            "type": "task_cancelled",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        })

        return {"message": "Task cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/backtest", response_model=List[BacktestStatusResponse])
async def list_backtests(
    status: Optional[str] = None,
    strategy_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List backtest tasks with optional filtering

    Args:
        status: Filter by status
        strategy_id: Filter by strategy ID
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of backtest tasks
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    try:
        # This would require adding a list method to the engine
        # For now, return empty list
        return []

    except Exception as e:
        logger.error(f"Failed to list backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/statistics", response_model=StatisticsResponse)
async def get_engine_statistics():
    """
    Get engine statistics

    Returns:
        Engine statistics
    """
    if not engine:
        raise HTTPException(status_code=503, detail="Backtest engine not initialized")

    try:
        stats = await engine.get_statistics()

        return StatisticsResponse(
            active_tasks=stats['active_tasks'],
            queue_size=stats['queue_size'],
            completed_tasks=stats['stats']['completed_tasks'],
            failed_tasks=stats['stats']['failed_tasks'],
            cache_hits=stats['stats']['cache_hits'],
            cache_misses=stats['stats']['cache_misses'],
            workers=stats['workers'],
            memory_results=stats['memory_results']
        )

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/backtest/validate")
async def validate_backtest_config(request: BacktestRequest):
    """
    Validate a backtest configuration without running it

    Returns:
        Validation result
    """
    # Basic validation
    errors = []

    if request.start_date >= request.end_date:
        errors.append("Start date must be before end date")

    if request.initial_capital <= 0:
        errors.append("Initial capital must be positive")

    if not request.strategy_id:
        errors.append("Strategy ID is required")

    if request.backtest_type == BacktestType.MONTE_CARLO and not request.monte_carlo_config:
        errors.append("Monte Carlo configuration is required for Monte Carlo backtest")

    if request.backtest_type == BacktestType.STRESS_TEST and not request.stress_scenarios:
        errors.append("Stress scenarios are required for stress test backtest")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        Health status
    """
    if not engine:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Engine not initialized"}
        )

    try:
        stats = await engine.get_statistics()
        return {
            "status": "healthy",
            "engine": "running",
            "active_tasks": stats['active_tasks'],
            "queue_size": stats['queue_size']
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": str(e)}
        )


# Add WebSocket route
app.websocket("/ws")(websocket_endpoint)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_error"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "server_error"
            }
        }
    )


# Main entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backtest_api:app",
        host="0.0.0.0",
        port=3004,
        reload=True,
        log_level="info"
    )