"""
Trading API v2.0
增強版交易API

Provides REST endpoints for the enhanced trading system with:
- Real-time order execution
- Advanced order types
- Risk management
- Performance monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

from ...trading.real_time_trading_engine import RealTimeTradingEngine
from ...trading.execution_service import ExecutionAlgorithm, ExecutionPriority
from ...models.trading_models_v2 import Order, OrderType, OrderSide
from ...core.database import get_db_session
from ...auth_middleware import get_current_user


# Request models
class CreateOrderRequest(BaseModel):
    """創建訂單請求"""
    portfolio_id: UUID
    symbol: str = Field(..., min_length=1, max_length=20)
    side: OrderSide
    order_type: OrderType
    quantity: Decimal = Field(..., gt=0)
    price: Optional[Decimal] = None
    time_in_force: Optional[str] = "DAY"
    algorithm: Optional[ExecutionAlgorithm] = ExecutionAlgorithm.MARKET
    priority: Optional[ExecutionPriority] = ExecutionPriority.NORMAL
    price_tolerance: Optional[float] = Field(None, ge=0, le=10)
    max_participation_rate: Optional[float] = Field(None, gt=0, le=1)


class CancelOrderRequest(BaseModel):
    """取消訂單請求"""
    order_id: UUID
    reason: Optional[str] = "User request"


class CreateTradingSessionRequest(BaseModel):
    """創建交易會話請求"""
    strategy_instance_id: UUID
    broker_config: Dict[str, Any]
    initial_capital: Decimal = Field(..., gt=0)
    risk_config: Optional[Dict[str, Any]] = None


# Response models
class OrderResponse(BaseModel):
    """訂單響應"""
    order_id: UUID
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal]
    status: str
    filled_quantity: Optional[Decimal]
    average_price: Optional[Decimal]
    created_at: datetime
    updated_at: Optional[datetime]


class TradingSessionResponse(BaseModel):
    """交易會話響應"""
    session_id: UUID
    status: str
    initial_capital: Decimal
    current_capital: Optional[Decimal]
    created_at: datetime
    trading_started_at: Optional[datetime]


# Create router
router = APIRouter(prefix="/api/v2/trading", tags=["Trading v2"])

# Initialize trading engine (in production, this would be singleton)
trading_engine: Optional[RealTimeTradingEngine] = None


def get_trading_engine() -> RealTimeTradingEngine:
    """獲取交易引擎實例"""
    global trading_engine
    if not trading_engine:
        # Initialize with configuration
        config = {
            'max_retries': 3,
            'order_timeout_seconds': 300,
            'max_position_size': 1000000,
            'default_rate_limit': 10
        }
        trading_engine = RealTimeTradingEngine(config)
    return trading_engine


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """創建並提交訂單"""
    try:
        engine = get_trading_engine()

        # Create order object
        order = Order(
            portfolio_id=request.portfolio_id,
            symbol=request.symbol,
            side=request.side.value,
            order_type=request.order_type.value,
            quantity=request.quantity,
            price=request.price,
            time_in_force=request.time_in_force
        )

        # Submit order
        success = await engine.submit_order(
            order,
            algorithm=request.algorithm,
            priority=request.priority,
            price_tolerance=request.price_tolerance
        )

        if success:
            return OrderResponse(
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                status=order.status.value,
                filled_quantity=order.filled_quantity,
                average_price=order.average_fill_price,
                created_at=order.created_at,
                updated_at=order.updated_at
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to submit order")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders/cancel")
async def cancel_order(
    request: CancelOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    """取消訂單"""
    try:
        engine = get_trading_engine()

        success = await engine.cancel_order(
            request.order_id,
            reason=request.reason
        )

        if success:
            return {"success": True, "message": "Order cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel order")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    portfolio_id: Optional[UUID] = None,
    status: Optional[str] = None,
    symbol: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """獲取訂單列表"""
    try:
        engine = get_trading_engine()

        # Query orders with filters
        async with get_db_session() as db:
            query = db.query(Order)

            if portfolio_id:
                query = query.filter(Order.portfolio_id == portfolio_id)
            if status:
                query = query.filter(Order.status == status)
            if symbol:
                query = query.filter(Order.symbol == symbol)

            orders = await query.offset(offset).limit(limit).all()

            return [
                OrderResponse(
                    order_id=order.id,
                    symbol=order.symbol,
                    side=order.side,
                    order_type=order.order_type,
                    quantity=order.quantity,
                    price=order.price,
                    status=order.status.value,
                    filled_quantity=order.filled_quantity,
                    average_price=order.average_fill_price,
                    created_at=order.created_at,
                    updated_at=order.updated_at
                )
                for order in orders
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """獲取訂單詳情"""
    try:
        async with get_db_session() as db:
            order = await db.query(Order).filter(Order.id == order_id).first()

            if not order:
                raise HTTPException(status_code=404, detail="Order not found")

            return OrderResponse(
                order_id=order.id,
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=order.quantity,
                price=order.price,
                status=order.status.value,
                filled_quantity=order.filled_quantity,
                average_price=order.average_fill_price,
                created_at=order.created_at,
                updated_at=order.updated_at
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions", response_model=TradingSessionResponse)
async def create_trading_session(
    request: CreateTradingSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """創建交易會話"""
    try:
        engine = get_trading_engine()

        session_id = await engine.create_trading_session(
            strategy_instance_id=request.strategy_instance_id,
            broker_config=request.broker_config,
            initial_capital=request.initial_capital,
            risk_config=request.risk_config
        )

        # Get session details
        session = engine.active_sessions.get(session_id)

        return TradingSessionResponse(
            session_id=session_id,
            status=session.status if session else "UNKNOWN",
            initial_capital=request.initial_capital,
            current_capital=session.available_capital if session else None,
            created_at=session.created_at if session else datetime.utcnow(),
            trading_started_at=session.trading_started_at if session else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/start")
async def start_trading_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """啟動交易會話"""
    try:
        engine = get_trading_engine()

        success = await engine.start_trading_session(session_id)

        if success:
            return {"success": True, "message": "Trading session started"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start session")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/stop")
async def stop_trading_session(
    session_id: UUID,
    emergency: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """停止交易會話"""
    try:
        engine = get_trading_engine()

        success = await engine.close_trading_session(
            session_id,
            emergency=emergency
        )

        if success:
            return {"success": True, "message": "Trading session stopped"}
        else:
            raise HTTPException(status_code=400, detail="Failed to stop session")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engine/status")
async def get_engine_status(
    current_user: dict = Depends(get_current_user)
):
    """獲取交易引擎狀態"""
    try:
        engine = get_trading_engine()

        status = engine.get_engine_status()

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/engine/metrics")
async def get_engine_metrics(
    current_user: dict = Depends(get_current_user)
):
    """獲取交易引擎指標"""
    try:
        engine = get_trading_engine()

        # Get metrics from all components
        order_metrics = engine.order_manager.get_metrics()
        position_metrics = engine.position_manager.get_metrics()

        return {
            "order_manager": order_metrics,
            "position_manager": position_metrics,
            "engine_status": {
                "status": engine.status.value,
                "active_sessions": len(engine.active_sessions),
                "queue_size": engine.signal_queue.qsize()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{portfolio_id}/positions")
async def get_portfolio_positions(
    portfolio_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """獲取投資組合倉位"""
    try:
        engine = get_trading_engine()

        positions = await engine.position_manager.get_positions(portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": float(pos.quantity),
                    "side": pos.side,
                    "market_value": float(pos.market_value) if pos.market_value else None,
                    "unrealized_pnl": float(pos.unrealized_pnl) if pos.unrealized_pnl else None,
                    "unrealized_pnl_percent": float(pos.unrealized_pnl_percent) if pos.unrealized_pnl_percent else None,
                    "average_price": float(pos.average_price) if pos.average_price else None,
                    "current_price": float(pos.current_price) if pos.current_price else None
                }
                for pos in positions
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{portfolio_id}/risk")
async def get_portfolio_risk(
    portfolio_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """獲取投資組合風險指標"""
    try:
        engine = get_trading_engine()

        risk_metrics = await engine.risk_manager.get_risk_metrics(portfolio_id)
        risk_summary = await engine.risk_manager.get_risk_summary(portfolio_id)

        return {
            "portfolio_id": portfolio_id,
            "risk_metrics": risk_metrics.__dict__ if risk_metrics else {},
            "risk_summary": risk_summary,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/execution/algorithms")
async def list_execution_algorithms():
    """獲取可用的執行算法列表"""
    return {
        "algorithms": [
            {
                "name": ExecutionAlgorithm.MARKET.value,
                "description": "Market Order - Immediate execution at current market price"
            },
            {
                "name": ExecutionAlgorithm.LIMIT.value,
                "description": "Limit Order - Execute only at specified price or better"
            },
            {
                "name": ExecutionAlgorithm.TWAP.value,
                "description": "Time-Weighted Average Price - Execute evenly over time"
            },
            {
                "name": ExecutionAlgorithm.VWAP.value,
                "description": "Volume-Weighted Average Price - Execute based on volume profile"
            },
            {
                "name": ExecutionAlgorithm.ICEBERG.value,
                "description": "Iceberg - Hide large order size by slicing"
            }
        ]
    }