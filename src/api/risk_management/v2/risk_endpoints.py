"""
Risk Management API Endpoints v2.0
RESTful API endpoints for real-time risk monitoring
Phase 5.1 - 實施回測引擎集成
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ...database import get_db
from ...services.risk_management_service_v2 import RiskManagementServiceV2
from ...core.auth import get_current_user
from ...models.user import User
from ...models.strategy_models import StrategyInstance

router = APIRouter(prefix="/risk", tags=["risk-management"])


def get_risk_service(db: Session = Depends(get_db)) -> RiskManagementServiceV2:
    """Get risk management service instance"""
    return RiskManagementServiceV2(db)


@router.post("/monitoring/{instance_id}", status_code=status.HTTP_201_CREATED)
async def start_risk_monitoring(
    instance_id: UUID,
    config: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Start real-time risk monitoring for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = risk_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Initialize monitoring
        result = await risk_service.initialize_risk_monitoring(instance_id, config)

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


@router.delete("/monitoring/{instance_id}", status_code=status.HTTP_200_OK)
async def stop_risk_monitoring(
    instance_id: UUID,
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Stop real-time risk monitoring for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = risk_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Stop monitoring
        result = await risk_service.stop_risk_monitoring(instance_id)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/metrics/{instance_id}")
async def get_risk_metrics(
    instance_id: UUID,
    force_refresh: bool = Query(False, description="Force recalculation of metrics"),
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Get real-time risk metrics for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = risk_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Get metrics
        result = await risk_service.get_real_time_risk_metrics(instance_id, force_refresh)

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


@router.put("/positions/{instance_id}", status_code=status.HTTP_200_OK)
async def update_portfolio_positions(
    instance_id: UUID,
    position_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Update portfolio positions for risk monitoring
    """
    try:
        # Verify instance ownership
        instance = risk_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Validate input
        if "positions" not in position_data or "total_value" not in position_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: positions, total_value"
            )

        # Update positions
        result = await risk_service.update_portfolio_positions(
            instance_id,
            position_data["positions"],
            position_data["total_value"]
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


@router.post("/alerts/{instance_id}/configure", status_code=status.HTTP_200_OK)
async def configure_risk_alerts(
    instance_id: UUID,
    alert_config: Dict[str, Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Configure risk alerts for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = risk_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Configure alerts
        result = await risk_service.configure_risk_alerts(instance_id, alert_config)

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


@router.get("/report/{instance_id}")
async def get_risk_report(
    instance_id: UUID,
    hours: int = Query(24, ge=1, le=168, description="Hours of historical data"),
    format: str = Query("json", regex="^(json|csv)$", description="Report format"),
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Generate risk report for a strategy instance
    """
    try:
        # Verify instance ownership
        instance = risk_service.db.query(StrategyInstance).filter(
            StrategyInstance.id == instance_id,
            StrategyInstance.user_id == current_user.id
        ).first()

        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Strategy instance not found"
            )

        # Generate report
        result = await risk_service.get_risk_report(instance_id, hours, format)

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


@router.get("/monitoring/status")
async def get_monitoring_status(
    instance_id: Optional[UUID] = Query(None, description="Specific instance ID"),
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Get monitoring status for strategy instances
    """
    try:
        # Get user's instances
        user_instances = risk_service.db.query(StrategyInstance.id).filter(
            StrategyInstance.user_id == current_user.id
        ).all()

        user_instance_ids = [inst.id for inst in user_instances]

        if instance_id:
            # Verify ownership
            if instance_id not in user_instance_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Strategy instance not found"
                )

        # Get status
        result = await risk_service.get_monitoring_status(instance_id)

        if instance_id:
            # Already verified ownership
            return result
        else:
            # Filter results to user's instances only
            if "instances" in result:
                user_instances = [
                    inst for inst in result["instances"]
                    if UUID(inst["instance_id"]) in user_instance_ids
                ]
                result["instances"] = user_instances
                result["total_user_active"] = len(user_instances)

            return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/dashboard", status_code=status.HTTP_200_OK)
async def get_risk_dashboard(
    current_user: User = Depends(get_current_user),
    risk_service: RiskManagementServiceV2 = Depends(get_risk_service)
):
    """
    Get risk management dashboard data
    """
    try:
        # Get all user instances
        user_instances = risk_service.db.query(StrategyInstance).filter(
            StrategyInstance.user_id == current_user.id
        ).all()

        # Get monitoring status
        status_result = await risk_service.get_monitoring_status()

        # Filter to user's instances
        active_monitoring = []
        if "instances" in status_result:
            user_instance_ids = [str(inst.id) for inst in user_instances]
            active_monitoring = [
                inst for inst in status_result["instances"]
                if inst["instance_id"] in user_instance_ids
            ]

        # Compile dashboard data
        dashboard_data = {
            "total_instances": len(user_instances),
            "active_monitoring": len(active_monitoring),
            "monitoring_instances": active_monitoring,
            "instances": []
        }

        # Add instance details
        for instance in user_instances:
            instance_key = str(instance.id)
            risk_metrics = None

            # Get current risk metrics if monitoring is active
            if instance_key in [inst["instance_id"] for inst in active_monitoring]:
                metrics_result = await risk_service.get_real_time_risk_metrics(instance.id)
                if metrics_result["status"] == "success":
                    risk_metrics = metrics_result.get("metrics", {})

            dashboard_data["instances"].append({
                "id": str(instance.id),
                "name": instance.name,
                "strategy_id": str(instance.strategy_id),
                "status": instance.status,
                "created_at": instance.created_at.isoformat(),
                "monitoring_active": instance_key in [inst["instance_id"] for inst in active_monitoring],
                "risk_metrics": risk_metrics
            })

        return dashboard_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.websocket("/ws/{instance_id}")
async def websocket_risk_updates(
    websocket: WebSocket,
    instance_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time risk updates
    """
    # TODO: Implement WebSocket authentication and connection management
    # This would integrate with the RiskWebSocketHandler in the risk engine

    await websocket.accept()

    try:
        while True:
            # This would receive updates from the risk engine
            # and broadcast to connected clients
            await websocket.receive_text()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1000)