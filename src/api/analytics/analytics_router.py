"""
FastAPI router for analytics endpoints
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import asyncio
import logging

from .models.analytics import (
    PerformanceMetrics,
    ReturnsData,
    PortfolioOverview,
    Timeframe,
    RealTimeUpdate
)
from .services.performance_service import (
    PerformanceCalculationService,
    PerformanceCacheService
)
from .services.portfolio_service import PortfolioAnalysisService
from .services.realtime_service import realtime_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# Initialize services
perf_service = PerformanceCalculationService()
perf_cache = PerformanceCacheService()
portfolio_service = PortfolioAnalysisService()


# Dependency for user authentication (placeholder)
async def get_current_user_id():
    """Get current authenticated user ID"""
    # In production, this would validate JWT token
    return 1  # Demo user ID


@router.get("/strategies/{strategy_id}/performance", response_model=PerformanceMetrics)
async def get_strategy_performance(
    strategy_id: str,
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    use_cache: bool = Query(True, description="Use cached metrics if available")
):
    """
    Get performance metrics for a strategy
    """
    try:
        # Check cache first
        if use_cache:
            cached = await perf_cache.get_cached_metrics(strategy_id, date.today())
            if cached:
                return cached

        # In production, fetch actual data from database
        # For demo, generate sample data
        sample_returns = _generate_sample_returns(strategy_id, start_date, end_date)
        sample_trades = _generate_sample_trades(strategy_id)

        # Calculate metrics
        metrics = await perf_service.calculate_performance_metrics(
            strategy_id=strategy_id,
            returns_data=sample_returns,
            trades_data=sample_trades
        )

        # Cache the results
        if use_cache:
            await perf_cache.cache_metrics(strategy_id, date.today(), metrics)

        return metrics

    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/{strategy_id}/returns", response_model=ReturnsData)
async def get_strategy_returns(
    strategy_id: str,
    timeframe: Timeframe = Query(Timeframe.DAY, description="Data timeframe"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date")
):
    """
    Get returns data for a strategy
    """
    try:
        # In production, fetch actual price data
        sample_prices = _generate_sample_prices(strategy_id, start_date, end_date)
        sample_benchmark = _generate_sample_benchmark(start_date, end_date)

        returns_data = await perf_service.generate_returns_series(
            strategy_id=strategy_id,
            price_data=sample_prices,
            benchmark_data=sample_benchmark,
            timeframe=timeframe
        )

        return returns_data

    except Exception as e:
        logger.error(f"Error generating returns data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{user_id}/overview", response_model=PortfolioOverview)
async def get_portfolio_overview(
    user_id: int = Depends(get_current_user_id),
    include_performance: bool = Query(True, description="Include performance data")
):
    """
    Get portfolio overview for a user
    """
    try:
        # In production, fetch actual holdings data
        sample_holdings = _generate_sample_holdings(user_id)
        cash_balance = 10000.0  # Demo cash balance

        overview = await portfolio_service.get_portfolio_overview(
            user_id=user_id,
            holdings=sample_holdings,
            cash_balance=10000.0
        )

        return overview

    except Exception as e:
        logger.error(f"Error generating portfolio overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{user_id}/risk")
async def get_portfolio_risk_metrics(
    user_id: int = Depends(get_current_user_id)
):
    """
    Get portfolio risk metrics
    """
    try:
        sample_holdings = _generate_sample_holdings(user_id)
        allocations, _ = portfolio_service._calculate_allocations(sample_holdings)

        # Simple volatilities for demo
        volatilities = [0.2] * len(allocations)  # 20% vol for all assets

        risk_metrics = await portfolio_service.calculate_portfolio_risk(
            allocations=allocations,
            volatilities=volatilities
        )

        return {
            "user_id": user_id,
            "risk_metrics": risk_metrics,
            "last_updated": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{user_id}/diversification")
async def get_portfolio_diversification(
    user_id: int = Depends(get_current_user_id)
):
    """
    Get portfolio diversification analysis
    """
    try:
        sample_holdings = _generate_sample_holdings(user_id)
        allocations, _ = portfolio_service._calculate_allocations(sample_holdings)

        diversification = await portfolio_service.analyze_diversification(allocations)

        return {
            "user_id": user_id,
            "diversification_metrics": diversification,
            "last_updated": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error analyzing diversification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/{user_id}/rebalance")
async def get_rebalancing_suggestions(
    user_id: int = Depends(get_current_user_id),
    target_allocations: Dict[str, float] = None
):
    """
    Get rebalancing suggestions for portfolio
    """
    try:
        if target_allocations is None:
            target_allocations = {
                "SPY": 40.0,
                "QQQ": 20.0,
                "VTI": 15.0,
                "BND": 15.0,
                "GLD": 10.0
            }

        sample_holdings = _generate_sample_holdings(user_id)
        allocations, _ = portfolio_service._calculate_allocations(sample_holdings)

        total_value = sum(h['value'] for h in sample_holdings)

        suggestions = await portfolio_service.generate_rebalancing_suggestions(
            current_allocations=allocations,
            target_allocations=target_allocations,
            total_portfolio_value=total_value
        )

        return {
            "user_id": user_id,
            "target_allocations": target_allocations,
            "suggestions": [
                {
                    "symbol": s.symbol,
                    "current_weight": s.current_weight,
                    "target_weight": s.target_weight,
                    "action": s.action,
                    "amount": float(s.amount)
                }
                for s in suggestions
            ],
            "generated_at": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error generating rebalancing suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket endpoint for real-time updates
@router.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time analytics updates
    """
    await websocket.accept()

    # Register connection
    connection_id = await realtime_service.register_connection(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            message_type = data.get("type")
            payload = data.get("payload", {})

            if message_type == "authenticate":
                user_id = payload.get("user_id")
                if user_id:
                    await realtime_service.authenticate_connection(connection_id, user_id)
                    await websocket.send_json({
                        "type": "authenticated",
                        "connection_id": connection_id
                    })

            elif message_type == "subscribe":
                strategy_id = payload.get("strategy_id")
                if strategy_id:
                    await realtime_service.subscribe_to_strategy(connection_id, strategy_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "strategy_id": strategy_id
                    })

            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await realtime_service.unregister_connection(connection_id)
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await realtime_service.unregister_connection(connection_id)


# Helper functions for demo data generation
def _generate_sample_returns(strategy_id: str, start_date: Optional[date], end_date: Optional[date]) -> List[tuple]:
    """Generate sample return data for demo"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    returns = []
    current_date = start_date

    # Generate daily returns with some randomness
    import random
    base_return = 0.0008  # Base daily return (~20% annual)

    while current_date <= end_date:
        # Skip weekends
        if current_date.weekday() < 5:
            daily_return = base_return + random.gauss(0, 0.02)  # 2% daily volatility
            returns.append((current_date, daily_return))
        current_date += timedelta(days=1)

    return returns


def _generate_sample_trades(strategy_id: str) -> List[Dict]:
    """Generate sample trade data for demo"""
    import random

    trades = []
    for i in range(100):  # 100 sample trades
        trade_return = random.gauss(0.001, 0.02)  # 2% std dev
        trades.append({
            "id": f"trade_{i}",
            "return": trade_return,
            "timestamp": datetime.now() - timedelta(days=random.randint(1, 365))
        })

    return trades


def _generate_sample_prices(strategy_id: str, start_date: Optional[date], end_date: Optional[date]) -> List[tuple]:
    """Generate sample price data for demo"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    prices = []
    current_date = start_date
    base_price = 100
    current_price = base_price

    import random

    while current_date <= end_date:
        if current_date.weekday() < 5:
            daily_return = random.gauss(0.0008, 0.02)
            current_price *= (1 + daily_return)
            prices.append((current_date, current_price))
        current_date += timedelta(days=1)

    return prices


def _generate_sample_benchmark(start_date: Optional[date], end_date: Optional[date]) -> List[tuple]:
    """Generate sample benchmark data"""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)

    benchmark = []
    current_date = start_date
    base_price = 100
    current_price = base_price

    import random

    while current_date <= end_date:
        if current_date.weekday() < 5:
            daily_return = random.gauss(0.0006, 0.015)  # Slightly lower vol
            current_price *= (1 + daily_return)
            benchmark.append((current_date, current_price))
        current_date += timedelta(days=1)

    return benchmark


def _generate_sample_holdings(user_id: int) -> List[Dict]:
    """Generate sample portfolio holdings"""
    return [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "quantity": 100,
            "value": 18500.0,
            "cost_basis": 170.0,
            "daily_return": 0.015
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "quantity": 50,
            "value": 18750.0,
            "cost_basis": 350.0,
            "daily_return": 0.008
        },
        {
            "symbol": "GOOGL",
            "name": "Alphabet Inc.",
            "quantity": 30,
            "value": 4500.0,
            "cost_basis": 140.0,
            "daily_return": -0.005
        },
        {
            "symbol": "SPY",
            "name": "SPDR S&P 500 ETF",
            "quantity": 25,
            "value": 11250.0,
            "cost_basis": 440.0,
            "daily_return": 0.002
        },
        {
            "symbol": "BTC",
            "name": "Bitcoin",
            "quantity": 0.5,
            "value": 21500.0,
            "cost_basis": 40000.0,
            "daily_return": 0.035
        }
    ]