"""
Enhanced Backtest API Service v2.0
==================================

Advanced RESTful API for strategy backtesting with integrated risk management,
asyncious task processing, and comprehensive analytics.

Author: CBSC Quant Team
Version: 2.0.0
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import Page, add_pagination, paginate
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
import asyncio
import uuid
import json
import logging
import hashlib
import numpy as np
import pandas as pd
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import backtest engine
try:
    from ..backtest.enhanced_backtest_engine import (
        EnhancedBacktestEngine,
        BacktestConfig,
        BacktestMode,
        BacktestResult
    )
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backtest.enhanced_backtest_engine import (
        EnhancedBacktestEngine,
        BacktestConfig,
        BacktestMode,
        BacktestResult
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="CBSC Backtest API v2",
    description="Advanced backtesting service with risk management and analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3004"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add pagination
add_pagination(app)


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestType(str, Enum):
    """Backtest execution types"""
    STANDARD = "standard"
    RISK_MANAGED = "risk_managed"
    STRESS_TEST = "stress_test"
    MONTE_CARLO = "monte_carlo"
    PARAMETER_SWEEP = "parameter_sweep"


class Priority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# Pydantic Models
class StrategyConfig(BaseModel):
    """Strategy configuration"""
    name: str = Field(..., description="Strategy name")
    type: str = Field(..., description="Strategy type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")
    code: Optional[str] = Field(None, description="Custom strategy code")
    symbols: List[str] = Field(..., description="Trading symbols")

    @validator('symbols')
    def validate_symbols(cls, v):
        if not v:
            raise ValueError("At least one symbol must be specified")
        return v


class BacktestRequest(BaseModel):
    """Backtest execution request"""
    strategy: StrategyConfig
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: Decimal = Field(Decimal('1000000'), description="Initial capital")
    commission_rate: Decimal = Field(Decimal('0.001'), description="Commission rate")
    slippage_rate: Decimal = Field(Decimal('0.0005'), description="Slippage rate")

    # Risk management settings
    enable_risk_management: bool = Field(True, description="Enable risk management")
    var_limit: Decimal = Field(Decimal('0.02'), description="Daily VaR limit")
    max_drawdown_limit: Decimal = Field(Decimal('0.15'), description="Max drawdown limit")
    leverage_limit: Decimal = Field(Decimal('2.0'), description="Leverage limit")
    position_size_limit: Decimal = Field(Decimal('0.3'), description="Max position size")

    # Advanced settings
    backtest_type: BacktestType = Field(BacktestType.RISK_MANAGED, description="Backtest type")
    enable_stress_testing: bool = Field(True, description="Enable stress testing")
    enable_monte_carlo: bool = Field(False, description="Enable Monte Carlo simulation")
    monte_carlo_simulations: int = Field(1000, description="Number of Monte Carlo simulations")

    # Execution settings
    priority: Priority = Field(Priority.NORMAL, description="Task priority")
    callback_url: Optional[str] = Field(None, description="Callback URL for completion notification")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError("End date must be after start date")
        return v


class BatchBacktestRequest(BaseModel):
    """Batch backtest request"""
    requests: List[BacktestRequest] = Field(..., description="List of backtest requests")
    parallel_execution: bool = Field(True, description="Execute in parallel")
    max_concurrent: int = Field(5, description="Maximum concurrent tasks")

    @validator('requests')
    def validate_requests(cls, v):
        if len(v) > 100:
            raise ValueError("Maximum 100 backtests allowed in batch")
        return v


class BacktestTemplate(BaseModel):
    """Backtest template for reuse"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    strategy_template: Dict[str, Any] = Field(..., description="Strategy template")
    default_parameters: Dict[str, Any] = Field(..., description="Default parameters")
    risk_settings: Dict[str, Any] = Field(..., description="Risk management settings")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    created_by: str = Field(..., description="Creator ID")
    is_public: bool = Field(False, description="Public template")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Update time")


class TaskInfo(BaseModel):
    """Task execution information"""
    task_id: str
    status: TaskStatus
    progress: float = Field(0.0, ge=0.0, le=1.0)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_id: Optional[str] = None
    estimated_completion: Optional[datetime] = None


class BacktestSummary(BaseModel):
    """Backtest result summary"""
    result_id: str
    task_id: str
    strategy_name: str
    symbols: List[str]
    backtest_type: str
    period: Tuple[datetime, datetime]

    # Performance metrics
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float

    # Risk metrics
    var_95: float
    var_99: float
    expected_shortfall_95: float

    # Trade statistics
    total_trades: int
    win_rate: float
    profit_factor: float

    # Execution info
    execution_time: float
    created_at: datetime

    class Config:
        from_attributes = True


# In-memory storage (replace with database in production)
tasks: Dict[str, TaskInfo] = {}
results: Dict[str, BacktestResult] = {}
templates: Dict[str, BacktestTemplate] = {}
user_backtests: Dict[str, List[str]] = {}  # user_id -> [task_id, ...]

# Global task executor
task_executor = ThreadPoolExecutor(max_workers=20)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "CBSC Backtest API v2",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
@limiter.limit("100/minute")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "tasks": {
            "pending": sum(1 for t in tasks.values() if t.status == TaskStatus.PENDING),
            "running": sum(1 for t in tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in tasks.values() if t.status == TaskStatus.COMPLETED)
        }
    }


@app.post("/api/v2/backtest", response_model=TaskInfo)
@limiter.limit("10/minute")
async def create_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User ID")
):
    """
    Create a new backtest task

    Rate limit: 10 requests per minute per user
    """
    # Validate user permissions (simplified)
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    # Generate task ID
    task_id = str(uuid.uuid4())

    # Create task info
    task_info = TaskInfo(
        task_id=task_id,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
        estimated_completion=datetime.utcnow() + timedelta(minutes=10)
    )

    # Store task
    tasks[task_id] = task_info

    # Track user backtests
    if user_id not in user_backtests:
        user_backtests[user_id] = []
    user_backtests[user_id].append(task_id)

    # Queue background task
    background_tasks.add_task(
        execute_backtest,
        task_id,
        request,
        user_id
    )

    return task_info


@app.post("/api/v2/backtest/batch", response_model=List[TaskInfo])
@limiter.limit("2/minute")
async def create_batch_backtest(
    request: BatchBacktestRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User ID")
):
    """
    Create multiple backtest tasks

    Rate limit: 2 requests per minute per user
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")

    task_infos = []

    # Create tasks
    for i, backtest_request in enumerate(request.requests):
        # Limit concurrent execution
        if request.parallel_execution and i >= request.max_concurrent:
            break

        task_id = str(uuid.uuid4())

        task_info = TaskInfo(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            estimated_completion=datetime.utcnow() + timedelta(minutes=20)
        )

        tasks[task_id] = task_info
        task_infos.append(task_info)

        # Track user backtests
        if user_id not in user_backtests:
            user_backtests[user_id] = []
        user_backtests[user_id].append(task_id)

        # Queue background task
        background_tasks.add_task(
            execute_backtest,
            task_id,
            backtest_request,
            user_id
        )

    return task_infos


@app.get("/api/v2/backtest/{task_id}", response_model=TaskInfo)
@limiter.limit("60/minute")
async def get_task_status(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Query(..., description="User ID")
):
    """Get task execution status"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check user permission
    if task_id not in user_backtests.get(user_id, []):
        raise HTTPException(status_code=403, detail="Access denied")

    return tasks[task_id]


@app.get("/api/v2/backtest/{task_id}/status")
@limiter.limit("60/minute")
async def get_task_progress(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Query(..., description="User ID")
):
    """Get detailed task progress"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_id not in user_backtests.get(user_id, []):
        raise HTTPException(status_code=403, detail="Access denied")

    task = tasks[task_id]

    # Calculate progress based on status
    if task.status == TaskStatus.PENDING:
        progress = 0.0
    elif task.status == TaskStatus.RUNNING:
        # Estimate progress based on time elapsed
        if task.started_at:
            elapsed = (datetime.utcnow() - task.started_at).total_seconds()
            progress = min(0.9, elapsed / 600)  # Assume 10 minutes total
        else:
            progress = 0.1
    elif task.status == TaskStatus.COMPLETED:
        progress = 1.0
    else:
        progress = task.progress

    return {
        "task_id": task_id,
        "status": task.status,
        "progress": progress,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "completed_at": task.completed_at,
        "estimated_completion": task.estimated_completion,
        "error_message": task.error_message,
        "current_step": _get_current_step(task.status)
    }


@app.delete("/api/v2/backtest/{task_id}")
@limiter.limit("20/minute")
async def cancel_task(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Query(..., description="User ID")
):
    """Cancel a running backtest task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_id not in user_backtests.get(user_id, []):
        raise HTTPException(status_code=403, detail="Access denied")

    task = tasks[task_id]

    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")

    # Update task status
    task.status = TaskStatus.CANCELLED
    task.completed_at = datetime.utcnow()

    return {
        "message": "Task cancelled successfully",
        "task_id": task_id
    }


@app.get("/api/v2/backtest/{task_id}/result")
@limiter.limit("30/minute")
async def get_backtest_result(
    task_id: str = Path(..., description="Task ID"),
    user_id: str = Query(..., description="User ID"),
    include_details: bool = Query(False, description="Include detailed results"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size")
):
    """Get backtest results"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_id not in user_backtests.get(user_id, []):
        raise HTTPException(status_code=403, detail="Access denied")

    task = tasks[task_id]

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Backtest not completed")

    if task.result_id not in results:
        raise HTTPException(status_code=404, detail="Result not found")

    result = results[task.result_id]

    # Create summary
    summary = BacktestSummary(
        result_id=task.result_id,
        task_id=task_id,
        strategy_name="Strategy",  # Get from request metadata
        symbols=[],  # Get from request metadata
        backtest_type="risk_managed",
        period=(task.created_at, task.completed_at),
        total_return=result.total_return,
        annualized_return=result.annualized_return,
        volatility=result.volatility,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        calmar_ratio=result.calmar_ratio,
        var_95=result.var_95,
        var_99=result.var_99,
        expected_shortfall_95=result.expected_shortfall_95,
        total_trades=result.total_trades,
        win_rate=result.win_rate,
        profit_factor=result.profit_factor,
        execution_time=(task.completed_at - task.started_at).total_seconds() if task.started_at else 0,
        created_at=task.created_at
    )

    response = {
        "summary": summary.dict(),
        "task_info": task.dict()
    }

    # Include detailed results if requested
    if include_details:
        response["details"] = {
            "equity_curve": result.equity_curve.to_dict() if result.equity_curve is not None else None,
            "returns": result.returns.to_dict() if result.returns is not None else None,
            "positions": [pos.__dict__ for pos in result.positions] if result.positions else None,
            "trades": [trade.__dict__ for trade in result.trades] if result.trades else None,
            "risk_metrics": result.risk_metrics.__dict__ if result.risk_metrics else None,
            "stress_test_results": result.stress_test_results
        }

    return response


@app.get("/api/v2/backtest/templates", response_model=Page[BacktestTemplate])
@limiter.limit("60/minute")
async def get_backtest_templates(
    user_id: str = Query(..., description="User ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    public_only: bool = Query(False, description="Show only public templates")
):
    """Get available backtest templates"""
    filtered_templates = []

    for template in templates.values():
        # Filter by user access
        if not template.is_public and template.created_by != user_id:
            if not public_only:
                continue

        # Filter by category
        if category and template.strategy_template.get("category") != category:
            continue

        # Filter by tags
        if tags and not any(tag in template.tags for tag in tags):
            continue

        filtered_templates.append(template)

    return paginate(filtered_templates)


@app.post("/api/v2/backtest/templates", response_model=BacktestTemplate)
@limiter.limit("10/minute")
async def create_backtest_template(
    template: BacktestTemplate,
    user_id: str = Query(..., description="User ID")
):
    """Create a new backtest template"""
    # Validate user ID
    if template.created_by != user_id:
        raise HTTPException(status_code=403, detail="Creator ID mismatch")

    # Generate ID if not provided
    if not template.id:
        template.id = str(uuid.uuid4())

    # Set timestamps
    template.created_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()

    # Store template
    templates[template.id] = template

    return template


@app.get("/api/v2/backtest/user/{user_id}", response_model=Page[TaskInfo])
@limiter.limit("30/minute")
async def get_user_backtests(
    user_id: str = Path(..., description="User ID"),
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Results per page")
):
    """Get user's backtest history"""
    if user_id not in user_backtests:
        return paginate([])

    task_ids = user_backtests[user_id]
    user_tasks = [tasks[tid] for tid in task_ids if tid in tasks]

    # Filter by status
    if status:
        user_tasks = [t for t in user_tasks if t.status == status]

    # Sort by creation date (newest first)
    user_tasks.sort(key=lambda x: x.created_at, reverse=True)

    return paginate(user_tasks)


@app.get("/api/v2/backtest/statistics")
@limiter.limit("30/minute")
async def get_backtest_statistics(
    user_id: str = Query(..., description="User ID"),
    period: str = Query("30d", description="Period (7d, 30d, 90d, 1y)")
):
    """Get backtest statistics and analytics"""
    # Calculate period start
    now = datetime.utcnow()
    if period == "7d":
        start = now - timedelta(days=7)
    elif period == "30d":
        start = now - timedelta(days=30)
    elif period == "90d":
        start = now - timedelta(days=90)
    else:  # 1y
        start = now - timedelta(days=365)

    # Get user tasks
    user_tasks = []
    if user_id in user_backtests:
        for task_id in user_backtests[user_id]:
            if task_id in tasks and tasks[task_id].created_at >= start:
                user_tasks.append(tasks[task_id])

    # Calculate statistics
    total_tasks = len(user_tasks)
    completed_tasks = sum(1 for t in user_tasks if t.status == TaskStatus.COMPLETED)
    failed_tasks = sum(1 for t in user_tasks if t.status == TaskStatus.FAILED)

    # Calculate performance metrics for completed tasks
    performance_metrics = []
    for task in user_tasks:
        if task.status == TaskStatus.COMPLETED and task.result_id in results:
            result = results[task.result_id]
            performance_metrics.append({
                "total_return": result.total_return,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown
            })

    avg_return = np.mean([m["total_return"] for m in performance_metrics]) if performance_metrics else 0
    avg_sharpe = np.mean([m["sharpe_ratio"] for m in performance_metrics]) if performance_metrics else 0
    avg_drawdown = np.mean([m["max_drawdown"] for m in performance_metrics]) if performance_metrics else 0

    return {
        "period": period,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "failed_tasks": failed_tasks,
        "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
        "performance_metrics": {
            "avg_total_return": avg_return,
            "avg_sharpe_ratio": avg_sharpe,
            "avg_max_drawdown": avg_drawdown
        },
        "task_types": {
            "standard": sum(1 for t in user_tasks),
            "risk_managed": sum(1 for t in user_tasks),
            "stress_test": sum(1 for t in user_tasks),
            "monte_carlo": sum(1 for t in user_tasks)
        }
    }


# Background task execution
async def execute_backtest(task_id: str, request: BacktestRequest, user_id: str):
    """Execute backtest in background"""
    try:
        # Update task status
        task = tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        # Create backtest configuration
        config = BacktestConfig(
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=float(request.initial_capital),
            commission_rate=float(request.commission_rate),
            slippage_rate=float(request.slippage_rate),
            enable_risk_management=request.enable_risk_management,
            var_limit=float(request.var_limit),
            max_drawdown_limit=float(request.max_drawdown_limit),
            leverage_limit=float(request.leverage_limit),
            position_size_limit=float(request.position_size_limit),
            enable_dynamic_adjustments=True,
            enable_stress_testing=request.enable_stress_testing,
            enable_real_time_monitoring=True
        )

        # Create backtest engine
        engine = EnhancedBacktestEngine(config)

        # Load market data (placeholder - implement data loading)
        market_data = await load_market_data(request.strategy.symbols, request.start_date, request.end_date)

        # Create strategy function based on configuration
        strategy_func = create_strategy_function(request.strategy)

        # Execute backtest based on type
        if request.backtest_type == BacktestType.STANDARD:
            mode = BacktestMode.STANDARD
        elif request.backtest_type == BacktestType.RISK_MANAGED:
            mode = BacktestMode.RISK_MANAGED
        elif request.backtest_type == BacktestType.STRESS_TEST:
            mode = BacktestMode.STRESS_TEST
        elif request.backtest_type == BacktestType.MONTE_CARLO:
            mode = BacktestMode.MONTE_CARLO
        else:
            mode = BacktestMode.RISK_MANAGED

        # Update progress
        task.progress = 0.3

        # Run backtest
        result = engine.run_backtest(
            strategy=strategy_func,
            data=market_data,
            mode=mode
        )

        # Update progress
        task.progress = 0.9

        # Store result
        result_id = str(uuid.uuid4())
        results[result_id] = result
        task.result_id = result_id

        # Update task completion
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.progress = 1.0

        # Send callback if provided
        if request.callback_url:
            await send_completion_callback(request.callback_url, task_id, result_id)

        logger.info(f"Backtest completed: {task_id}")

    except Exception as e:
        logger.error(f"Backtest failed: {task_id}, error: {str(e)}")
        task.status = TaskStatus.FAILED
        task.completed_at = datetime.utcnow()
        task.error_message = str(e)


# Helper functions
async def load_market_data(symbols: List[str], start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Load market data for symbols"""
    # This is a placeholder - implement actual data loading
    # For now, generate random data
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    data = {}

    for symbol in symbols:
        # Generate random price data
        np.random.seed(hash(symbol) % 2**32)
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
        data[symbol] = prices

    return pd.DataFrame(data, index=dates)


def create_strategy_function(strategy_config: StrategyConfig) -> callable:
    """Create strategy function from configuration"""
    # This is a placeholder - implement actual strategy creation
    def example_strategy(date: datetime, market_data: pd.Series, portfolio_state: Dict[str, Any]) -> Dict[str, float]:
        positions = {}

        for symbol in strategy_config.symbols:
            if symbol in market_data and not pd.isna(market_data[symbol]):
                # Simple buy and hold strategy
                target_value = portfolio_state["portfolio_value"] * 0.8 / len(strategy_config.symbols)
                positions[symbol] = target_value / market_data[symbol]

        return positions

    return example_strategy


def _get_current_step(status: TaskStatus) -> str:
    """Get current step description based on status"""
    steps = {
        TaskStatus.PENDING: "Waiting in queue",
        TaskStatus.RUNNING: "Executing backtest",
        TaskStatus.COMPLETED: "Backtest completed",
        TaskStatus.FAILED: "Backtest failed",
        TaskStatus.CANCELLED: "Task cancelled"
    }
    return steps.get(status, "Unknown")


async def send_completion_callback(callback_url: str, task_id: str, result_id: str):
    """Send completion notification to callback URL"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                callback_url,
                json={
                    "event": "backtest_completed",
                    "task_id": task_id,
                    "result_id": result_id,
                    "timestamp": datetime.utcnow().isoformat()
                },
                timeout=10
            )
    except Exception as e:
        logger.error(f"Failed to send callback: {e}")


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backtest_api_v2:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )