"""
Trading API Endpoints v2.0
RESTful API endpoints for real-time trading
Phase 5.1 - 實施回測引擎集成
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.trading_service_v2 import TradingServiceV2
from ...core.auth import get_current_user
from ...models.user import User
from ...models.strategy_models import StrategyInstance
from ...models.trading_models_v2 import (
    Portfolio, Order, Position, Trade, TradingSession,
    OrderStatus, PositionStatus
)

router = APIRouter(prefix="/trading", tags=["trading"])


def get_trading_service(db: Session = Depends(get_db)) -> TradingServiceV2:
    """Get trading service instance"""
    return TradingServiceV2(db)


@router.post("/sessions/{instance_id}", status_code=status.HTTP_201_CREATED)
async def initialize_trading_session(
    instance_id: UUID,
    broker_config: Dict[str, Any],
    initial_capital: Optional[float] = None,
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    Initialize trading session for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = trading_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Initialize trading session
        result = await trading_service.initialize_trading_session(
            instance_id,
            broker_config,
            initial_capital
        )

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sessions/{instance_id}/start", status_code=status.HTTP_200_OK)
async def start_trading(
    instance_id: UUID,
    market_data_config: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    Start live trading for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = trading_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Start trading
        result = await trading_service.start_trading(instance_id, market_data_config)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sessions/{instance_id}/stop", status_code=status.HTTP_200_OK)
async def stop_trading(
    instance_id: UUID,
    close_positions: bool = Query(True, description="Close all open positions"),
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    Stop live trading for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = trading_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Stop trading
        result = await trading_service.stop_trading(instance_id, close_positions)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/signals/{instance_id}/execute", status_code=status.HTTP_200_OK)
async def execute_signal(
    instance_id: UUID,
    signal: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    Execute trading signal from strategy
    """
    try:
        # Verify instance ownership
        instance = trading_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Execute signal
        result = await trading_service.execute_signal(instance_id, signal)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/market-data/{instance_id}", status_code=status.HTTP_200_OK)
async def update_market_prices(
    instance_id: UUID,
    prices: Dict[str, float],
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    Update market prices for open positions
    """
    try:
        # Verify instance ownership
        instance = trading_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Update prices
        result = await trading_service.update_market_prices(instance_id, prices)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/status/{instance_id}")
async def get_trading_status(
    instance_id: UUID,
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    Get current trading status for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = trading_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Get status
        result = await trading_service.get_trading_status(instance_id)

        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/portfolios", status_code=status.HTTP_200_OK)
async def list_portfolios(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    List all portfolios for the user
    """
    try:
        # Query user's portfolios
        query = trading_service.db.query(Portfolio).join(StrategyInstance).filter(
            StrategyInstance.user_id == current_user.id
        )

        if status_filter:
            query = query.filter(Portfolio.status == status_filter)

        portfolios = query.all()

        portfolio_list = []
        for portfolio in portfolios:
            portfolio_data = {
                "id": str(portfolio.id),
                "strategy_instance_id": str(portfolio.strategy_instance_id),
                "initial_capital": float(portfolio.initial_capital),
                "current_capital": float(portfolio.current_capital or 0),
                "total_pnl": float(portfolio.total_pnl or 0),
                "total_pnl_percent": float(portfolio.total_pnl_percent or 0),
                "unrealized_pnl": float(portfolio.unrealized_pnl or 0),
                "total_trades": portfolio.total_trades,
                "win_rate": float(portfolio.win_rate or 0),
                "status": portfolio.status,
                "created_at": portfolio.created_at.isoformat(),
                "trading_started_at": portfolio.trading_started_at.isoformat() if portfolio.trading_started_at else None,
                "stopped_at": portfolio.stopped_at.isoformat() if portfolio.stopped_at else None
            }
            portfolio_list.append(portfolio_data)

        return {
            "portfolios": portfolio_list,
            "total_count": len(portfolio_list)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/portfolios/{portfolio_id}", status_code=status.HTTP_200_OK)
async def get_portfolio_details(
    portfolio_id: UUID,
    include_positions: bool = Query(True, description="Include position details"),
    include_orders: bool = Query(True, description="Include recent orders"),
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    Get detailed portfolio information
    """
    try:
        # Verify portfolio ownership
        portfolio = trading_service.db.query(Portfolio).join(StrategyInstance).filter(
            Portfolio.id == portfolio_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )

        portfolio_data = {
            "id": str(portfolio.id),
            "strategy_instance_id": str(portfolio.strategy_instance_id),
            "initial_capital": float(portfolio.initial_capital),
            "current_capital": float(portfolio.current_capital or 0),
            "allocated_capital": float(portfolio.allocated_capital or 0),
            "available_capital": float(portfolio.available_capital or 0),
            "total_pnl": float(portfolio.total_pnl or 0),
            "total_pnl_percent": float(portfolio.total_pnl_percent or 0),
            "unrealized_pnl": float(portfolio.unrealized_pnl or 0),
            "realized_pnl": float(portfolio.realized_pnl or 0),
            "max_drawdown": float(portfolio.max_drawdown or 0),
            "total_positions": portfolio.total_positions,
            "total_exposure": float(portfolio.total_exposure or 0),
            "total_trades": portfolio.total_trades,
            "winning_trades": portfolio.winning_trades,
            "losing_trades": portfolio.losing_trades,
            "win_rate": float(portfolio.win_rate or 0),
            "status": portfolio.status,
            "created_at": portfolio.created_at.isoformat(),
            "trading_started_at": portfolio.trading_started_at.isoformat() if portfolio.trading_started_at else None,
            "last_trade_at": portfolio.last_trade_at.isoformat() if portfolio.last_trade_at else None
        }

        # Include positions
        if include_positions:
            positions = trading_service.db.query(Position).filter(
                Position.portfolio_id == portfolio_id
            ).all()

            portfolio_data["positions"] = []
            for position in positions:
                position_data = {
                    "id": str(position.id),
                    "symbol": position.symbol,
                    "quantity": float(position.quantity),
                    "entry_price": float(position.entry_price),
                    "current_price": float(position.current_price) if position.current_price else None,
                    "market_value": float(position.market_value) if position.market_value else None,
                    "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else None,
                    "unrealized_pnl_percent": float(position.unrealized_pnl_percent) if position.unrealized_pnl_percent else None,
                    "side": position.side,
                    "status": position.status,
                    "opened_at": position.opened_at.isoformat(),
                    "closed_at": position.closed_at.isoformat() if position.closed_at else None
                }
                portfolio_data["positions"].append(position_data)

        # Include recent orders
        if include_orders:
            orders = trading_service.db.query(Order).filter(
                Order.portfolio_id == portfolio_id
            ).order_by(Order.submitted_at.desc()).limit(10).all()

            portfolio_data["recent_orders"] = []
            for order in orders:
                order_data = {
                    "id": str(order.id),
                    "symbol": order.symbol,
                    "side": order.side,
                    "order_type": order.order_type,
                    "quantity": float(order.quantity),
                    "price": float(order.price) if order.price else None,
                    "status": order.status,
                    "filled_quantity": float(order.filled_quantity),
                    "average_fill_price": float(order.average_fill_price) if order.average_fill_price else None,
                    "commission": float(order.commission) if order.commission else None,
                    "submitted_at": order.submitted_at.isoformat(),
                    "filled_at": order.filled_at.isoformat() if order.filled_at else None
                }
                portfolio_data["recent_orders"].append(order_data)

        return portfolio_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/positions", status_code=status.HTTP_200_OK)
async def list_positions(
    instance_id: Optional[UUID] = Query(None, description="Filter by strategy instance"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    List all positions for the user
    """
    try:
        # Build query
        query = trading_service.db.query(Position).join(Portfolio).join(StrategyInstance).filter(
            StrategyInstance.user_id == current_user.id
        )

        if instance_id:
            query = query.filter(Portfolio.strategy_instance_id == instance_id)

        if status_filter:
            query = query.filter(Position.status == status_filter)

        positions = query.all()

        position_list = []
        for position in positions:
            position_data = {
                "id": str(position.id),
                "portfolio_id": str(position.portfolio_id),
                "symbol": position.symbol,
                "quantity": float(position.quantity),
                "entry_price": float(position.entry_price),
                "current_price": float(position.current_price) if position.current_price else None,
                "market_value": float(position.market_value) if position.market_value else None,
                "unrealized_pnl": float(position.unrealized_pnl) if position.unrealized_pnl else None,
                "unrealized_pnl_percent": float(position.unrealized_pnl_percent) if position.unrealized_pnl_percent else None,
                "total_pnl": float(position.total_pnl) if position.total_pnl else None,
                "side": position.side,
                "status": position.status,
                "leverage": float(position.leverage) if position.leverage else None,
                "opened_at": position.opened_at.isoformat(),
                "closed_at": position.closed_at.isoformat() if position.closed_at else None
            }
            position_list.append(position_data)

        return {
            "positions": position_list,
            "total_count": len(position_list)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/orders", status_code=status.HTTP_200_OK)
async def list_orders(
    instance_id: Optional[UUID] = Query(None, description="Filter by strategy instance"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of orders"),
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    List all orders for the user
    """
    try:
        # Build query
        query = trading_service.db.query(Order).join(Portfolio).join(StrategyInstance).filter(
            StrategyInstance.user_id == current_user.id
        )

        if instance_id:
            query = query.filter(Portfolio.strategy_instance_id == instance_id)

        if symbol:
            query = query.filter(Order.symbol == symbol)

        if status_filter:
            query = query.filter(Order.status == status_filter)

        orders = query.order_by(Order.submitted_at.desc()).limit(limit).all()

        order_list = []
        for order in orders:
            order_data = {
                "id": str(order.id),
                "portfolio_id": str(order.portfolio_id),
                "symbol": order.symbol,
                "side": order.side,
                "order_type": order.order_type,
                "quantity": float(order.quantity),
                "price": float(order.price) if order.price else None,
                "stop_price": float(order.stop_price) if order.stop_price else None,
                "status": order.status,
                "filled_quantity": float(order.filled_quantity),
                "remaining_quantity": float(order.remaining_quantity) if order.remaining_quantity else None,
                "average_fill_price": float(order.average_fill_price) if order.average_fill_price else None,
                "commission": float(order.commission) if order.commission else None,
                "total_cost": float(order.total_cost) if order.total_cost else None,
                "broker_order_id": order.broker_order_id,
                "submitted_at": order.submitted_at.isoformat(),
                "filled_at": order.filled_at.isoformat() if order.filled_at else None,
                "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None
            }
            order_list.append(order_data)

        return {
            "orders": order_list,
            "total_count": len(order_list)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/trades", status_code=status.HTTP_200_OK)
async def list_trades(
    instance_id: Optional[UUID] = Query(None, description="Filter by strategy instance"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of trades"),
    current_user: User = Depends(get_current_user),
    trading_service: TradingServiceV2 = Depends(get_trading_service)
):
    """
    List all completed trades for the user
    """
    try:
        # Build query
        query = trading_service.db.query(Trade).join(Portfolio).join(StrategyInstance).filter(
            StrategyInstance.user_id == current_user.id
        )

        if instance_id:
            query = query.filter(Portfolio.strategy_instance_id == instance_id)

        if symbol:
            query = query.filter(Trade.symbol == symbol)

        if start_date:
            query = query.filter(Trade.entry_date >= start_date)

        if end_date:
            query = query.filter(Trade.entry_date <= end_date)

        trades = query.order_by(Trade.executed_at.desc()).limit(limit).all()

        trade_list = []
        for trade in trades:
            trade_data = {
                "id": str(trade.id),
                "portfolio_id": str(trade.portfolio_id),
                "symbol": trade.symbol,
                "direction": trade.direction,
                "quantity": float(trade.quantity),
                "entry_price": float(trade.entry_price),
                "exit_price": float(trade.exit_price) if trade.exit_price else None,
                "gross_pnl": float(trade.gross_pnl) if trade.gross_pnl else None,
                "commission": float(trade.commission) if trade.commission else None,
                "net_pnl": float(trade.net_pnl) if trade.net_pnl else None,
                "net_pnl_percent": float(trade.net_pnl_percent) if trade.net_pnl_percent else None,
                "return_on_capital": float(trade.return_on_capital) if trade.return_on_capital else None,
                "entry_date": trade.entry_date.isoformat(),
                "exit_date": trade.exit_date.isoformat() if trade.exit_date else None,
                "duration_hours": trade.duration_hours,
                "status": trade.status,
                "executed_at": trade.executed_at.isoformat()
            }
            trade_list.append(trade_data)

        return {
            "trades": trade_list,
            "total_count": len(trade_list)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )