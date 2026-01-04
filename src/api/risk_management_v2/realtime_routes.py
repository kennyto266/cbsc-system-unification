"""
Real-time Risk Management API Routes
Enhanced endpoints for real-time risk monitoring and position management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
import logging

from ..services.enhanced_risk_management_service import (
    EnhancedRiskManagementService,
    RiskLimitType,
    PositionSizeMethod,
    PositionSizingConfig,
    RiskLimit
)
from ..dependencies import get_database, get_current_user
from ..middleware import rate_limit, require_permissions
from ...models.risk_models_v2 import RiskPosition
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Create router
realtime_router = APIRouter(
    prefix="/api/v2/risk/realtime",
    tags=["Real-time Risk Management"],
    responses={404: {"description": "Not found"}}
)


# Pydantic models for request/response

class RiskLimitConfig(BaseModel):
    """Risk limit configuration model"""
    limit_type: RiskLimitType
    limit_value: float = Field(..., gt=0, description="Limit value")
    strategy_instance_id: Optional[str] = None
    warning_threshold: float = Field(0.8, ge=0.5, le=1.0, description="Warning threshold (0.5-1.0)")


class PositionSizingRequest(BaseModel):
    """Position sizing configuration request"""
    method: PositionSizeMethod
    base_amount: float = Field(..., gt=0, description="Base amount for calculations")
    risk_factor: float = Field(0.02, ge=0.001, le=0.1, description="Risk factor (0.1% - 10%)")
    max_position_pct: float = Field(0.10, ge=0.01, le=0.5, description="Max position percentage (1% - 50%)")
    volatility_lookback: int = Field(20, ge=5, le=252, description="Volatility lookback period")
    confidence_level: float = Field(0.95, ge=0.8, le=0.999, description="Confidence level")

    # Method-specific parameters
    fixed_amount: Optional[float] = Field(None, gt=0, description="Fixed amount for fixed sizing")
    percentage_of_capital: Optional[float] = Field(None, gt=0, le=1, description="Percentage of capital")
    target_volatility: Optional[float] = Field(None, gt=0, le=1, description="Target volatility")
    kelly_fraction: Optional[float] = Field(0.25, ge=0.1, le=0.5, description="Kelly fraction")


class PositionUpdate(BaseModel):
    """Position update model"""
    symbol: str = Field(..., description="Trading symbol")
    quantity: float = Field(..., description="Position quantity")
    price: Optional[float] = Field(None, description="Current price")
    sector: Optional[str] = Field(None, description="Sector classification")
    asset_type: Optional[str] = Field(None, description="Asset type")


# WebSocket connection manager
class WebSocketManager:
    """Manages WebSocket connections for real-time risk updates"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, user_id: str):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                self.disconnect(user_id)


ws_manager = WebSocketManager()


# Real-time Monitoring Endpoints

@realtime_router.get(
    "/dashboard",
    response_model=Dict[str, Any],
    summary="Get real-time risk dashboard",
    description="Retrieve comprehensive real-time risk metrics and status"
)
@rate_limit("60/minute")
@require_permissions("risk:read")
async def get_realtime_dashboard(
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get real-time risk dashboard"""
    try:
        risk_service = EnhancedRiskManagementService(db)
        dashboard = await risk_service.get_real_time_risk_dashboard(current_user.id)

        return {
            "success": True,
            "data": dashboard
        }

    except Exception as e:
        logger.error(f"Error getting risk dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@realtime_router.get(
    "/metrics/{strategy_instance_id}",
    summary="Get real-time risk metrics",
    description="Get current risk metrics for a specific strategy instance"
)
@rate_limit("120/minute")
@require_permissions("risk:read")
async def get_realtime_metrics(
    strategy_instance_id: str,
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get real-time risk metrics for a strategy"""
    try:
        risk_service = EnhancedRiskManagementService(db)
        metrics = await risk_service._calculate_portfolio_metrics(
            strategy_instance_id,
            await risk_service._get_current_positions(strategy_instance_id)
        )

        return {
            "success": True,
            "data": {
                "instance_id": strategy_instance_id,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error getting realtime metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@realtime_router.post(
    "/positions/update",
    summary="Update positions",
    description="Update portfolio positions for risk monitoring"
)
@rate_limit("200/minute")
@require_permissions("risk:write")
async def update_positions(
    strategy_instance_id: str,
    positions: List[PositionUpdate],
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Update portfolio positions"""
    try:
        risk_service = EnhancedRiskManagementService(db)

        # Update positions in database
        for pos in positions:
            # Check if position exists
            db_position = db.query(RiskPosition).filter(
                RiskPosition.strategy_instance_id == strategy_instance_id,
                RiskPosition.symbol == pos.symbol
            ).first()

            if db_position:
                # Update existing position
                db_position.quantity = pos.quantity
                db_position.current_price = pos.price or db_position.current_price
                db_position.sector = pos.sector or db_position.sector
                db_position.asset_type = pos.asset_type or db_position.asset_type
                db_position.last_updated = datetime.utcnow()

                # Recalculate market value and PnL
                if db_position.current_price:
                    db_position.market_value = db_position.quantity * db_position.current_price
                    if db_position.avg_cost_price:
                        db_position.unrealized_pnl = (
                            (db_position.current_price - db_position.avg_cost_price) *
                            db_position.quantity
                        )
            else:
                # Create new position
                db_position = RiskPosition(
                    strategy_instance_id=strategy_instance_id,
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    current_price=pos.price or 0,
                    avg_cost_price=pos.price or 0,
                    market_value=pos.quantity * (pos.price or 0),
                    sector=pos.sector,
                    asset_type=pos.asset_type,
                    opened_at=datetime.utcnow(),
                    last_updated=datetime.utcnow()
                )
                db.add(db_position)

        db.commit()

        # Trigger risk recalculation
        await risk_service._process_instance_risk_by_id(strategy_instance_id)

        return {
            "success": True,
            "message": f"Updated {len(positions)} positions",
            "instance_id": strategy_instance_id
        }

    except Exception as e:
        logger.error(f"Error updating positions: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


# Risk Limits Endpoints

@realtime_router.get(
    "/limits",
    response_model=List[Dict],
    summary="Get risk limits",
    description="Get all configured risk limits for the user"
)
@rate_limit("60/minute")
@require_permissions("risk:read")
async def get_risk_limits(
    strategy_instance_id: Optional[str] = Query(None, description="Filter by strategy instance"),
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get risk limits"""
    try:
        risk_service = EnhancedRiskManagementService(db)
        limits = []

        for key, limit in risk_service.risk_limits.items():
            if str(limit.user_id) == str(current_user.id) or limit.user_id == UUID('00000000-0000-0000-0000-000000000000'):
                if not strategy_instance_id or str(limit.strategy_instance_id) == strategy_instance_id:
                    limits.append({
                        "limit_type": limit.limit_type.value,
                        "limit_value": limit.limit_value,
                        "current_value": limit.current_value,
                        "utilization_percent": limit.utilization_percent,
                        "warning_threshold": limit.warning_threshold,
                        "is_active": limit.is_active
                    })

        return {
            "success": True,
            "data": limits
        }

    except Exception as e:
        logger.error(f"Error getting risk limits: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@realtime_router.post(
    "/limits",
    response_model=Dict,
    summary="Set risk limit",
    description="Set a custom risk limit"
)
@rate_limit("20/minute")
@require_permissions("risk:write")
async def set_risk_limit(
    config: RiskLimitConfig,
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Set a risk limit"""
    try:
        risk_service = EnhancedRiskManagementService(db)

        success = await risk_service.set_risk_limit(
            user_id=current_user.id,
            limit_type=config.limit_type,
            limit_value=config.limit_value,
            strategy_instance_id=UUID(config.strategy_instance_id) if config.strategy_instance_id else None
        )

        if success:
            return {
                "success": True,
                "message": f"Risk limit set: {config.limit_type.value} = {config.limit_value}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to set risk limit")

    except Exception as e:
        logger.error(f"Error setting risk limit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Position Sizing Endpoints

@realtime_router.get(
    "/sizing/{strategy_instance_id}",
    response_model=Dict,
    summary="Get position sizing recommendations",
    description="Get current position sizing recommendations for a strategy"
)
@rate_limit("60/minute")
@require_permissions("risk:read")
async def get_position_sizing(
    strategy_instance_id: str,
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get position sizing recommendations"""
    try:
        risk_service = EnhancedRiskManagementService(db)

        # Get current config
        config = risk_service.position_configs.get(UUID(strategy_instance_id))
        if not config:
            # Return default config
            config = PositionSizingConfig(
                method=PositionSizeMethod.PERCENTAGE_CAPITAL,
                base_amount=100000
            )

        # Get current recommendations
        positions = await risk_service._get_current_positions(strategy_instance_id)
        metrics = await risk_service._calculate_portfolio_metrics(strategy_instance_id, positions)

        instance = db.query(StrategyInstance).filter(
            StrategyInstance.id == strategy_instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(status_code=404, detail="Strategy instance not found")

        recommendations = await risk_service._calculate_position_sizing(
            instance, positions, metrics
        )

        return {
            "success": True,
            "data": {
                "instance_id": strategy_instance_id,
                "config": {
                    "method": config.method.value,
                    "base_amount": config.base_amount,
                    "risk_factor": config.risk_factor,
                    "max_position_pct": config.max_position_pct
                },
                "recommendations": recommendations
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position sizing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@realtime_router.post(
    "/sizing/{strategy_instance_id}",
    response_model=Dict,
    summary="Configure position sizing",
    description="Configure position sizing method for a strategy"
)
@rate_limit("20/minute")
@require_permissions("risk:write")
async def configure_position_sizing(
    strategy_instance_id: str,
    request: PositionSizingRequest,
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Configure position sizing"""
    try:
        # Verify ownership
        instance = db.query(StrategyInstance).filter(
            StrategyInstance.id == strategy_instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(status_code=404, detail="Strategy instance not found")

        risk_service = EnhancedRiskManagementService(db)

        config = PositionSizingConfig(
            method=request.method,
            base_amount=request.base_amount,
            risk_factor=request.risk_factor,
            max_position_pct=request.max_position_pct,
            volatility_lookback=request.volatility_lookback,
            confidence_level=request.confidence_level,
            fixed_amount=request.fixed_amount,
            percentage_of_capital=request.percentage_of_capital,
            target_volatility=request.target_volatility,
            kelly_fraction=request.kelly_fraction
        )

        success = await risk_service.configure_position_sizing(
            UUID(strategy_instance_id),
            config
        )

        if success:
            return {
                "success": True,
                "message": f"Position sizing configured: {request.method.value}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to configure position sizing")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring position sizing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Recommendations Endpoint

@realtime_router.get(
    "/recommendations",
    response_model=Dict,
    summary="Get risk recommendations",
    description="Get AI-powered risk management recommendations"
)
@rate_limit("30/minute")
@require_permissions("risk:read")
async def get_recommendations(
    priority: Optional[str] = Query(None, regex="^(low|medium|high|critical)$", description="Filter by priority"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of recommendations"),
    db=Depends(get_database),
    current_user=Depends(get_current_user)
):
    """Get risk recommendations"""
    try:
        risk_service = EnhancedRiskManagementService(db)
        recommendations = await risk_service.get_portfolio_recommendations(current_user.id)

        # Filter by priority if specified
        if priority:
            recommendations = [r for r in recommendations if r.get("priority") == priority]

        # Apply limit
        recommendations = recommendations[:limit]

        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "total": len(recommendations),
                "filters": {
                    "priority": priority,
                    "limit": limit
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# WebSocket Endpoint for real-time updates

@realtime_router.websocket("/updates/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    db=Depends(get_database)
):
    """WebSocket endpoint for real-time risk updates"""
    await ws_manager.connect(websocket, user_id)

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle subscription requests
            if message.get("type") == "subscribe":
                # Subscribe to specific updates
                await websocket.send_text(json.dumps({
                    "type": "subscription_ack",
                    "subscriptions": message.get("subscriptions", [])
                }))

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(user_id)


# Health check for real-time monitoring

@realtime_router.get(
    "/health",
    summary="Health check",
    description="Check the health of real-time risk monitoring"
)
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "Real-time risk monitoring is healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_connections": len(ws_manager.active_connections)
    }