#!/usr / bin / env python3
"""
Performance Monitoring Demo

This script demonstrates the usage of the performance metrics middleware
and decorators in a FastAPI application.
"""

import asyncio
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import performance monitoring components
from src.api.middleware.performance import (
    PerformanceMetricsMiddleware,
    performance_monitor,
    get_performance_api_routes,
    get_performance_profiler,
    monitor_backtest_performance,
    monitor_optimization_performance
)
from src.observability.metrics_registry import get_metrics_registry, MetricNames
from src.observability.structured_logger import get_observability_logger

# Pydantic models
class BacktestRequest(BaseModel):
    symbol: str
    strategy: str
    start_date: str
    end_date: str

class BacktestResponse(BaseModel):
    symbol: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    trades: int

class OptimizationRequest(BaseModel):
    symbol: str
    strategy_type: str
    parameters: dict

# Create FastAPI app
app = FastAPI(
    title="Performance Monitoring Demo",
    description="港股量化交易系統 - 性能監控演示",
    version="1.0.0"
)

# Add performance middleware
app.add_middleware(PerformanceMetricsMiddleware, collect_detailed=True)

# Add performance API routes
app.include_router(get_performance_api_routes())

# Logger
logger = get_observability_logger("demo")


# Simulate data fetching
@performance_monitor(threshold_ms=500)
async def fetch_market_data(symbol: str, days: int = 365):
    """Simulate fetching market data with performance monitoring"""
    await asyncio.sleep(0.1)  # Simulate API call
    return {
        "symbol": symbol,
        "data_points": days,
        "status": "success"
    }


# Simulate backtest execution
@monitor_backtest_performance
async def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """Simulate backtest execution with performance monitoring"""
    logger.info(f"Starting backtest for {request.symbol}", extra={
        "symbol": request.symbol,
        "strategy": request.strategy
    })

    # Simulate backtest computation
    await asyncio.sleep(0.2)

    # Simulate results
    import random
    result = BacktestResponse(
        symbol=request.symbol,
        total_return=random.uniform(10, 30),
        sharpe_ratio=random.uniform(0.8, 2.0),
        max_drawdown=random.uniform(5, 15),
        win_rate=random.uniform(40, 70),
        trades=random.randint(50, 200)
    )

    logger.info(f"Backtest completed for {request.symbol}", extra={
        "symbol": request.symbol,
        "total_return": result.total_return,
        "sharpe_ratio": result.sharpe_ratio
    })

    return result


# Simulate strategy optimization
@monitor_optimization_performance
async def optimize_strategy(request: OptimizationRequest):
    """Simulate strategy optimization with performance monitoring"""
    logger.info(f"Starting optimization for {request.symbol}", extra={
        "symbol": request.symbol,
        "strategy_type": request.strategy_type
    })

    # Simulate optimization (parameter search)
    await asyncio.sleep(0.3)

    # Simulate optimized parameters
    return {
        "symbol": request.symbol,
        "best_parameters": {
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "bb_period": 20
        },
        "best_sharpe": 1.85,
        "optimizations_tested": 100
    }


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "港股量化交易系統 - 性能監控演示",
        "endpoints": {
            "health": "/api / health",
            "backtest": "/api / backtest",
            "optimize": "/api / optimize",
            "performance": "/api / v1 / performance"
        }
    }


@app.get("/api / health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.post("/api / backtest")
async def backtest_endpoint(request: BacktestRequest):
    """Run a backtest with performance monitoring"""
    result = await run_backtest(request)
    return result


@app.post("/api / optimize")
async def optimize_endpoint(request: OptimizationRequest):
    """Optimize strategy with performance monitoring"""
    result = await optimize_strategy(request)
    return result


@app.get("/api / data/{symbol}")
async def get_data_endpoint(symbol: str):
    """Get market data with performance monitoring"""
    data = await fetch_market_data(symbol)
    return data


@app.get("/api / slow")
async def slow_endpoint():
    """Intentionally slow endpoint for testing"""
    await asyncio.sleep(2.0)
    return {"message": "This was slow!"}


@app.get("/api / memory - intensive")
async def memory_intensive_endpoint():
    """Memory - intensive endpoint for testing"""
    # Allocate some memory
    data = [i for i in range(1000000)]
    return {
        "message": "Memory intensive operation",
        "allocated": len(data)
    }


@app.get("/api / error")
async def error_endpoint():
    """Error endpoint for testing"""
    raise HTTPException(status_code=500, detail="Simulated error")


# Test endpoints to generate performance data
@app.get("/api / test / load")
async def test_load_endpoint(count: int = 10):
    """Generate test load for performance monitoring"""
    results = []
    for i in range(count):
        data = await fetch_market_data(f"0700.HK.{i}", days=100)
        results.append(data)
    return {
        "generated": len(results),
        "total_requests": count
    }


# Background task to simulate continuous monitoring
@app.post("/api / simulate - load")
async def simulate_load(background_tasks: BackgroundTasks, duration: int = 30):
    """Simulate continuous load for testing"""
    metrics = get_metrics_registry()

    async def generate_load():
        end_time = time.time() + duration
        request_count = 0

        while time.time() < end_time:
            # Simulate API request
            await fetch_market_data("0700.HK", days=30)
            request_count += 1

            # Add some random delays
            await asyncio.sleep(random.uniform(0.1, 0.5))

        logger.info("Load simulation completed", extra={
            "total_requests": request_count,
            "duration_seconds": duration
        })

    background_tasks.add_task(generate_load)

    return {
        "status": "load_simulation_started",
        "duration": duration,
        "message": f"Generating load for {duration} seconds"
    }


# Example of using the profiler programmatically
@app.get("/api / performance / detailed")
async def get_detailed_performance():
    """Get detailed performance analysis"""
    profiler = get_performance_profiler()
    summary = profiler.get_performance_summary()

    # Get bottlenecks
    bottlenecks = profiler.get_bottlenecks()

    return {
        "summary": summary,
        "bottlenecks": {
            "count": len(bottlenecks),
            "items": bottlenecks
        },
        "recommendations": [
            "Monitor endpoints with high p95 latency",
            "Consider caching for frequently accessed data",
            "Optimize memory - intensive operations"
        ]
    }


# Export metrics to file
@app.post("/api / performance / export")
async def export_performance_metrics():
    """Export performance metrics to JSON file"""
    metrics = get_metrics_registry()
    metrics.export_to_json_file("performance_metrics_export.json")

    return {
        "status": "success",
        "message": "Metrics exported to performance_metrics_export.json"
    }


# Get current metrics snapshot
@app.get("/api / performance / metrics")
async def get_metrics():
    """Get current metrics snapshot"""
    metrics = get_metrics_registry()
    return metrics.get_all_metrics()


if __name__ == "__main__":
    import random

    print("=" * 80)
    print("港股量化交易系統 - 性能監控演示")
    print("=" * 80)
    print("\n性能監控功能:")
    print("  ✓ 自動記錄請求執行時間")
    print("  ✓ 監控內存使用量")
    print("  ✓ 追蹤 CPU 使用率")
    print("  ✓ 檢測性能瓶頸")
    print("  ✓ 結構化日誌記錄")
    print("  ✓ 分佈式追蹤 (Trace ID)")
    print("  ✓ 性能指標 API")
    print("\nAPI 端點:")
    print("  • GET  /                    - 首頁")
    print("  • GET  /api / health          - 健康檢查")
    print("  • POST /api / backtest        - 運行回測")
    print("  • POST /api / optimize        - 策略優化")
    print("  • GET  /api / data/{symbol}   - 獲取市場數據")
    print("  • GET  /api / slow            - 慢請求測試")
    print("  • GET  /api / memory - intensive - 內存密集型測試")
    print("  • GET  /api / test / load       - 生成測試負載")
    print("  • GET  /api / v1 / performance / summary  - 性能摘要")
    print("  • GET  /api / v1 / performance / bottlenecks - 性能瓶頸")
    print("  • GET  /api / v1 / performance / metrics  - 指標詳情")
    print("\n" + "=" * 80)
    print("\n🚀 啟動服務器...")
    print("   訪問: http://localhost:8000")
    print("   API 文檔: http://localhost:8000 / docs")
    print("=" * 80 + "\n")

    uvicorn.run(
        "demo_performance_monitoring:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
