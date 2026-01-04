"""
Error handling monitoring endpoints for the CBSC Trading System.

Provides health check and status endpoints for error handling components.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/error-handling", tags=["Error Handling Monitoring"])


@router.get("/stats")
async def get_error_handling_stats() -> Dict[str, Any]:
    """
    Get comprehensive error handling statistics.

    Returns:
        Dictionary with retry, circuit breaker, and error statistics
    """
    try:
        # Import here to avoid circular imports
        from utils.circuit_breaker import get_all_circuit_breaker_stats
        from utils.retry_manager import get_default_manager

        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "operational",
            "circuit_breakers": get_all_circuit_breaker_stats(),
            "retry_stats": get_default_manager().get_stats()
        }

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"Failed to get error handling stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve error handling statistics"
        )


@router.get("/health")
async def error_handling_health() -> Dict[str, Any]:
    """
    Health check for error handling subsystems.

    Returns:
        Health status with component details
    """
    try:
        from utils.circuit_breaker import get_all_circuit_breaker_stats

        breaker_stats = get_all_circuit_breaker_stats()
        unhealthy_services = []

        for service, stats in breaker_stats.items():
            if stats["state"] == "open":
                unhealthy_services.append({
                    "service": service,
                    "state": "open",
                    "last_failure": stats["last_failure_time"],
                    "open_count": stats["open_count"]
                })

        is_healthy = len(unhealthy_services) == 0

        return {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "circuit_breakers": {
                    "status": "healthy" if is_healthy else "degraded",
                    "unhealthy_services": unhealthy_services
                },
                "retry_manager": {
                    "status": "operational"
                }
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@router.post("/reset")
async def reset_error_handling() -> Dict[str, Any]:
    """
    Reset error handling components (for recovery).

    Returns:
        Reset status
    """
    try:
        from utils.circuit_breaker import reset_all_circuit_breakers, get_all_circuit_breaker_stats
        from utils.retry_manager import get_default_manager

        # Reset circuit breakers
        reset_all_circuit_breakers()

        # Reset retry stats
        manager = get_default_manager()
        manager.reset_stats()

        return {
            "success": True,
            "message": "Error handling components reset successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "circuit_breakers": get_all_circuit_breaker_stats(),
            "retry_stats": manager.get_stats()
        }

    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset error handling components: {str(e)}"
        )
