#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非价格策略API端点 - Non-Price Strategy API Endpoints
提供HKMA宏观数据、情绪分析和策略集成的RESTful API端点
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import json
import logging

from .models.non_price_responses import (
    BaseResponse,
    HIBORResponse,
    MonetaryBaseResponse,
    ExchangeRateResponse,
    LiquidityResponse,
    HistoricalDataResponse,
    SentimentAnalysisResponse,
    StrategiesListResponse,
    StrategyPerformanceResponse,
    SignalsResponse,
    SignalUpdateMessage,
    MacroUpdateMessage,
    SubscriptionStatusMessage,
    PaginationInfo,
    DateRangeFilter,
    SignalFilter,
    SignalType,
    DataSource,
    TrendDirection
)

from .services.non_price_service import get_non_price_service, NonPriceAPIService
from .cache_service import cache_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/non-price", tags=["非价格策略"])

# WebSocket connection manager
class NonPriceWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # connection_id -> list of subscriptions

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = []

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.subscriptions:
            del self.subscriptions[connection_id]

    async def send_message(self, connection_id: str, message: dict):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast_to_subscribers(self, message_type: str, data: dict):
        message = {
            "message_type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }

        for connection_id, subscriptions in self.subscriptions.items():
            if message_type in subscriptions:
                await self.send_message(connection_id, message)

    async def subscribe(self, connection_id: str, subscription_type: str):
        if connection_id in self.subscriptions:
            if subscription_type not in self.subscriptions[connection_id]:
                self.subscriptions[connection_id].append(subscription_type)

                # Send subscription confirmation
                await self.send_message(connection_id, {
                    "message_type": "subscription_status",
                    "subscription_id": subscription_type,
                    "status": "subscribed",
                    "message": f"Successfully subscribed to {subscription_type}"
                })

    async def unsubscribe(self, connection_id: str, subscription_type: str):
        if connection_id in self.subscriptions and subscription_type in self.subscriptions[connection_id]:
            self.subscriptions[connection_id].remove(subscription_type)

            # Send unsubscription confirmation
            await self.send_message(connection_id, {
                "message_type": "subscription_status",
                "subscription_id": subscription_type,
                "status": "unsubscribed",
                "message": f"Successfully unsubscribed from {subscription_type}"
            })


# Global WebSocket manager
ws_manager = NonPriceWebSocketManager()

# Dependency injection
def get_service() -> NonPriceAPIService:
    return get_non_price_service()


# HKMA Macro Data Endpoints
@router.get("/hkma/hibor/latest", response_model=HIBORResponse)
async def get_latest_hibor_rates(service: NonPriceAPIService = Depends(get_service)):
    """获取最新HIBOR利率数据"""
    try:
        # Try to get from cache first
        cache_key = "non_price:hkma:hibor:latest"
        cached_data = await cache_service.get(cache_key)

        if cached_data:
            logger.info("Returning cached HIBOR data")
            return HIBORResponse(
                success=True,
                message="从缓存获取HIBOR数据",
                data=cached_data
            )

        # Fetch fresh data
        data = await service.get_latest_hibor_rates()

        # Cache for 5 minutes
        await cache_service.set(cache_key, data, ttl=300)

        return HIBORResponse(
            success=True,
            message="成功获取最新HIBOR利率数据",
            data=data
        )
    except Exception as e:
        logger.error(f"Failed to get HIBOR rates: {e}")
        raise HTTPException(status_code=500, detail=f"获取HIBOR数据失败: {str(e)}")


@router.get("/hkma/monetary-base/latest", response_model=MonetaryBaseResponse)
async def get_latest_monetary_base(service: NonPriceAPIService = Depends(get_service)):
    """获取最新货币基础数据"""
    try:
        cache_key = "non_price:hkma:monetary_base:latest"
        cached_data = await cache_service.get(cache_key)

        if cached_data:
            return MonetaryBaseResponse(
                success=True,
                message="从缓存获取货币基础数据",
                data=cached_data
            )

        data = await service.get_latest_monetary_base()
        await cache_service.set(cache_key, data, ttl=300)

        return MonetaryBaseResponse(
            success=True,
            message="成功获取最新货币基础数据",
            data=data
        )
    except Exception as e:
        logger.error(f"Failed to get monetary base: {e}")
        raise HTTPException(status_code=500, detail=f"获取货币基础数据失败: {str(e)}")


@router.get("/hkma/exchange-rate/latest", response_model=ExchangeRateResponse)
async def get_latest_exchange_rate(
    currency_pair: str = Query("USD/HKD", description="货币对，如USD/HKD"),
    service: NonPriceAPIService = Depends(get_service)
):
    """获取最新汇率数据"""
    try:
        cache_key = f"non_price:hkma:exchange_rate:{currency_pair}:latest"
        cached_data = await cache_service.get(cache_key)

        if cached_data:
            return ExchangeRateResponse(
                success=True,
                message="从缓存获取汇率数据",
                data=cached_data
            )

        data = await service.get_latest_exchange_rate(currency_pair)
        await cache_service.set(cache_key, data, ttl=300)

        return ExchangeRateResponse(
            success=True,
            message="成功获取最新汇率数据",
            data=data
        )
    except Exception as e:
        logger.error(f"Failed to get exchange rate: {e}")
        raise HTTPException(status_code=500, detail=f"获取汇率数据失败: {str(e)}")


@router.get("/hkma/liquidity/latest", response_model=LiquidityResponse)
async def get_latest_liquidity_data(service: NonPriceAPIService = Depends(get_service)):
    """获取最新流动性数据"""
    try:
        cache_key = "non_price:hkma:liquidity:latest"
        cached_data = await cache_service.get(cache_key)

        if cached_data:
            return LiquidityResponse(
                success=True,
                message="从缓存获取流动性数据",
                data=cached_data
            )

        data = await service.get_latest_liquidity_data()
        await cache_service.set(cache_key, data, ttl=300)

        return LiquidityResponse(
            success=True,
            message="成功获取最新流动性数据",
            data=data
        )
    except Exception as e:
        logger.error(f"Failed to get liquidity data: {e}")
        raise HTTPException(status_code=500, detail=f"获取流动性数据失败: {str(e)}")


@router.get("/hkma/historical", response_model=HistoricalDataResponse)
async def get_historical_hkma_data(
    data_type: str = Query(..., description="数据类型: hibor, monetary_base, exchange_rate"),
    start_date: datetime = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="结束日期 (YYYY-MM-DD)"),
    service: NonPriceAPIService = Depends(get_service)
):
    """获取HKMA历史数据"""
    try:
        # Validate date range
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

        # Limit date range to 1 year
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="日期范围不能超过1年")

        cache_key = f"non_price:hkma:historical:{data_type}:{start_date.date()}:{end_date.date()}"
        cached_data = await cache_service.get(cache_key)

        if cached_data:
            return HistoricalDataResponse(
                success=True,
                message="从缓存获取历史数据",
                data_type=data_type,
                data_points=cached_data,
                total_count=len(cached_data)
            )

        data_points = await service.get_historical_data(data_type, start_date, end_date)

        # Cache for 1 hour
        await cache_service.set(cache_key, data_points, ttl=3600)

        return HistoricalDataResponse(
            success=True,
            message="成功获取历史数据",
            data_type=data_type,
            data_points=data_points,
            total_count=len(data_points)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get historical data: {e}")
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")


# Sentiment Analysis Endpoints
@router.get("/sentiment/latest/{symbol}", response_model=SentimentAnalysisResponse)
async def get_latest_sentiment(
    symbol: str = Path(..., description="交易标的代码"),
    service: NonPriceAPIService = Depends(get_service)
):
    """获取指定标的的最新情绪分析"""
    try:
        signals = await service.get_sentiment_signals(symbol)

        if not signals:
            raise HTTPException(status_code=404, detail=f"未找到{symbol}的情绪数据")

        main_signal = signals[0]

        return SentimentAnalysisResponse(
            success=True,
            message="成功获取情绪分析数据",
            symbol=symbol,
            sentiment_score=main_signal.sentiment_score,
            sentiment_label=main_signal.sentiment_label,
            signals=signals,
            analysis_timestamp=main_signal.timestamp
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=f"获取情绪分析失败: {str(e)}")


@router.get("/sentiment/signals/{symbol}", response_model=SignalsResponse)
async def get_sentiment_signals(
    symbol: str = Path(..., description="交易标的代码"),
    service: NonPriceAPIService = Depends(get_service)
):
    """获取指定标的的情绪信号列表"""
    try:
        signals = await service.get_sentiment_signals(symbol)

        return SignalsResponse(
            success=True,
            message="成功获取情绪信号",
            signals=signals,
            total_count=len(signals),
            filters_applied={"symbol": symbol}
        )
    except Exception as e:
        logger.error(f"Failed to get sentiment signals: {e}")
        raise HTTPException(status_code=500, detail=f"获取情绪信号失败: {str(e)}")


@router.post("/sentiment/analyze")
async def analyze_sentiment(
    symbol: str = Query(..., description="交易标的代码"),
    service: NonPriceAPIService = Depends(get_service)
):
    """触发情绪分析（异步）"""
    try:
        # Start async sentiment analysis
        asyncio.create_task(_perform_sentiment_analysis(symbol, service))

        return {
            "success": True,
            "message": "情绪分析已启动",
            "symbol": symbol,
            "analysis_id": f"analysis_{symbol}_{int(datetime.utcnow().timestamp())}"
        }
    except Exception as e:
        logger.error(f"Failed to start sentiment analysis: {e}")
        raise HTTPException(status_code=500, detail=f"启动情绪分析失败: {str(e)}")


async def _perform_sentiment_analysis(symbol: str, service: NonPriceAPIService):
    """执行情绪分析（后台任务）"""
    try:
        signals = await service.get_sentiment_signals(symbol)

        # Broadcast results via WebSocket
        if signals:
            await ws_manager.broadcast_to_subscribers("sentiment_update", {
                "symbol": symbol,
                "signal": signals[0].dict()
            })
    except Exception as e:
        logger.error(f"Background sentiment analysis failed: {e}")


# Strategy Integration Endpoints
@router.get("/strategies/available", response_model=StrategiesListResponse)
async def get_available_strategies(service: NonPriceAPIService = Depends(get_service)):
    """获取可用的非价格策略列表"""
    try:
        strategies = await service.get_available_strategies()

        return StrategiesListResponse(
            success=True,
            message="成功获取可用策略列表",
            strategies=strategies,
            total_count=len(strategies)
        )
    except Exception as e:
        logger.error(f"Failed to get available strategies: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略列表失败: {str(e)}")


@router.get("/strategies/performance/{strategy_id}", response_model=StrategyPerformanceResponse)
async def get_strategy_performance(
    strategy_id: str = Path(..., description="策略ID"),
    service: NonPriceAPIService = Depends(get_service)
):
    """获取指定策略的表现数据"""
    try:
        performance = await service.get_strategy_performance(strategy_id)

        if performance is None:
            raise HTTPException(status_code=404, detail=f"未找到策略{strategy_id}的表现数据")

        return StrategyPerformanceResponse(
            success=True,
            message="成功获取策略表现数据",
            strategy_id=strategy_id,
            performance=performance
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy performance: {e}")
        raise HTTPException(status_code=500, detail=f"获取策略表现失败: {str(e)}")


@router.post("/strategies/optimize")
async def optimize_strategy(
    strategy_id: str = Query(..., description="策略ID"),
    optimization_period: int = Query(30, description="优化周期（天）"),
    service: NonPriceAPIService = Depends(get_service)
):
    """启动策略优化（异步）"""
    try:
        # Start async optimization
        asyncio.create_task(_perform_strategy_optimization(strategy_id, optimization_period, service))

        return {
            "success": True,
            "message": "策略优化已启动",
            "strategy_id": strategy_id,
            "optimization_period": optimization_period,
            "estimated_completion": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start strategy optimization: {e}")
        raise HTTPException(status_code=500, detail=f"启动策略优化失败: {str(e)}")


async def _perform_strategy_optimization(strategy_id: str, period: int, service: NonPriceAPIService):
    """执行策略优化（后台任务）"""
    try:
        # Simulate optimization process
        await asyncio.sleep(2)  # Simulate processing time

        # Broadcast completion via WebSocket
        await ws_manager.broadcast_to_subscribers("optimization_complete", {
            "strategy_id": strategy_id,
            "status": "completed",
            "completion_time": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Background strategy optimization failed: {e}")


# WebSocket Endpoints
@router.websocket("/ws/signals/{symbol}")
async def websocket_signals_endpoint(websocket: WebSocket, symbol: str):
    """实时信号WebSocket端点"""
    connection_id = f"signals_{symbol}_{int(datetime.utcnow().timestamp())}"

    try:
        await ws_manager.connect(websocket, connection_id)
        await ws_manager.subscribe(connection_id, f"signal_{symbol}")

        # Send initial data
        service = get_non_price_service()
        signals = await service.get_sentiment_signals(symbol)

        if signals:
            await ws_manager.send_message(connection_id, {
                "message_type": "initial_signals",
                "symbol": symbol,
                "signals": [signal.dict() for signal in signals]
            })

        # Keep connection alive
        while True:
            try:
                # Wait for client messages or ping
                data = await websocket.receive_text()

                # Handle client messages if needed
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await ws_manager.send_message(connection_id, {"type": "pong"})
                except json.JSONDecodeError:
                    pass

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(connection_id)


@router.websocket("/ws/macro-updates")
async def websocket_macro_updates_endpoint(websocket: WebSocket):
    """宏观数据更新WebSocket端点"""
    connection_id = f"macro_{int(datetime.utcnow().timestamp())}"

    try:
        await ws_manager.connect(websocket, connection_id)
        await ws_manager.subscribe(connection_id, "macro_updates")

        # Send initial macro data
        service = get_non_price_service()

        hibor_data = await service.get_latest_hibor_rates()
        monetary_base = await service.get_latest_monetary_base()
        liquidity_data = await service.get_latest_liquidity_data()

        await ws_manager.send_message(connection_id, {
            "message_type": "initial_macro_data",
            "data": {
                "hibor": [rate.dict() for rate in hibor_data],
                "monetary_base": monetary_base.dict(),
                "liquidity": [item.dict() for item in liquidity_data]
            }
        })

        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await ws_manager.send_message(connection_id, {"type": "pong"})
                except json.JSONDecodeError:
                    pass

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(connection_id)


@router.websocket("/ws/sentiment-stream")
async def websocket_sentiment_stream_endpoint(websocket: WebSocket):
    """情绪分析流WebSocket端点"""
    connection_id = f"sentiment_{int(datetime.utcnow().timestamp())}"

    try:
        await ws_manager.connect(websocket, connection_id)
        await ws_manager.subscribe(connection_id, "sentiment_stream")

        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)

                    if message.get("type") == "ping":
                        await ws_manager.send_message(connection_id, {"type": "pong"})
                    elif message.get("type") == "subscribe_symbol":
                        symbol = message.get("symbol")
                        if symbol:
                            await ws_manager.subscribe(connection_id, f"sentiment_{symbol}")

                except json.JSONDecodeError:
                    pass

            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(connection_id)


# Utility Endpoints
@router.get("/health")
async def non_price_health_check():
    """非价格服务健康检查"""
    try:
        service = get_non_price_service()

        # Test service availability
        hibor_available = True
        try:
            await service.get_latest_hibor_rates()
        except:
            hibor_available = False

        return {
            "success": True,
            "status": "healthy",
            "services": {
                "hkma_api": "healthy" if hibor_available else "degraded",
                "sentiment_service": "healthy",
                "websocket_manager": "healthy"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"服务不健康: {str(e)}")


@router.get("/info")
async def get_api_info():
    """获取API信息"""
    return {
        "success": True,
        "api_name": "CBSC Non-Price Strategy API",
        "version": "1.0.0",
        "description": "非价格策略API，提供HKMA宏观数据、情绪分析和策略集成",
        "endpoints": {
            "hkma_data": [
                "/api/non-price/hkma/hibor/latest",
                "/api/non-price/hkma/monetary-base/latest",
                "/api/non-price/hkma/exchange-rate/latest",
                "/api/non-price/hkma/liquidity/latest",
                "/api/non-price/hkma/historical"
            ],
            "sentiment": [
                "/api/non-price/sentiment/latest/{symbol}",
                "/api/non-price/sentiment/signals/{symbol}",
                "/api/non-price/sentiment/analyze"
            ],
            "strategies": [
                "/api/non-price/strategies/available",
                "/api/non-price/strategies/performance/{strategy_id}",
                "/api/non-price/strategies/optimize"
            ],
            "websocket": [
                "/api/non-price/ws/signals/{symbol}",
                "/api/non-price/ws/macro-updates",
                "/api/non-price/ws/sentiment-stream"
            ]
        },
        "documentation": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }


# Export router for main app
__all__ = ["router", "ws_manager"]