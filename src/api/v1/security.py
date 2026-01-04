"""
Security API endpoints
安全相關API端點

提供安全監控、審計和限流狀態查詢功能
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from middleware.rate_limit_middleware import get_rate_limiter
from security.audit_logger import audit_logger, AuditEventType
from security.anomaly_detector import get_anomaly_detector

router = APIRouter(prefix="/security", tags=["Security"])
security = HTTPBearer(auto_error=False)


@router.get("/rate-limit/status")
async def get_rate_limit_status(
    identifier: Optional[str] = Query(None, description="User ID or IP to check"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get rate limiting status for user or IP"""
    rate_limiter = get_rate_limiter()

    if not identifier:
        # Try to get from token
        if credentials and credentials.credentials:
            # In a real implementation, decode JWT to get user_id
            identifier = "demo_user"

    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier required"
        )

    try:
        # Get stats for all windows
        stats = await rate_limiter.get_rate_limit_stats(identifier)

        return {
            "success": True,
            "identifier": identifier,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting rate limit status: {str(e)}"
        )


@router.get("/audit/events")
async def get_audit_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get audit events with filtering"""
    # Convert string event_type to enum if provided
    event_type_enum = None
    if event_type:
        try:
            from security.audit_logger import AuditEventType
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event_type: {event_type}"
            )

    try:
        events = await audit_logger.search_audit_logs(
            limit=limit,
            offset=offset,
            user_id=user_id,
            event_type=event_type_enum,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "data": events,
            "count": len(events),
            "filters": {
                "user_id": user_id,
                "event_type": event_type,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit events: {str(e)}"
        )


@router.get("/audit/user/{user_id}/summary")
async def get_user_activity_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get activity summary for a specific user"""
    try:
        summary = await audit_logger.get_user_activity_summary(user_id, days)

        return {
            "success": True,
            "user_id": user_id,
            "period_days": days,
            "summary": summary,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating user summary: {str(e)}"
        )


@router.get("/anomalies/recent")
async def get_recent_anomalies(
    limit: int = Query(50, ge=1, le=500),
    hours: int = Query(24, ge=1, le=168),  # Up to 7 days
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get recent security anomalies"""
    try:
        import redis.asyncio as redis
        from core.config import settings
        import json

        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        anomalies = []

        # Get anomalies from multiple days if needed
        current_date = datetime.utcnow()
        for day_offset in range(0, min(7, (hours // 24) + 1)):
            date = current_date - timedelta(days=day_offset)
            anomaly_key = f"security:anomalies:{date.strftime('%Y-%m-%d')}"

            day_anomalies = await redis_client.lrange(anomaly_key, 0, limit - len(anomalies))
            for anomaly_json in day_anomalies:
                anomaly = json.loads(anomaly_json)
                anomaly_date = datetime.fromisoformat(anomaly['detected_at'])

                # Check if within hours window
                if (current_date - anomaly_date).total_seconds() <= hours * 3600:
                    anomalies.append(anomaly)

                if len(anomalies) >= limit:
                    break

            if len(anomalies) >= limit:
                break

        # Sort by detection time (newest first)
        anomalies.sort(key=lambda x: x['detected_at'], reverse=True)

        return {
            "success": True,
            "data": anomalies[:limit],
            "count": len(anomalies),
            "hours_window": hours,
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving anomalies: {str(e)}"
        )


@router.get("/risk/assessment/{user_id}")
async def get_user_risk_assessment(
    user_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get comprehensive risk assessment for a user"""
    try:
        detector = get_anomaly_detector()
        risk_data = await detector.get_user_risk_score(user_id)

        # Get additional context
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=30)
        recent_events = await audit_logger.search_audit_logs(
            user_id=user_id,
            start_date=start_date,
            limit=100
        )

        # Calculate risk factors from events
        failed_logins = sum(1 for e in recent_events if 'login_failed' in e.get('event_type', ''))
        security_events = sum(1 for e in recent_events if e.get('severity') in ['critical', 'high'])
        unique_ips = len(set(e.get('ip_address') for e in recent_events if e.get('ip_address')))

        risk_data['additional_context'] = {
            'recent_failed_logins': failed_logins,
            'recent_security_events': security_events,
            'unique_ips_used': unique_ips,
            'total_recent_events': len(recent_events)
        }

        return {
            "success": True,
            "user_id": user_id,
            "risk_assessment": risk_data,
            "assessed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating risk assessment: {str(e)}"
        )


@router.post("/compliance/report")
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    report_type: str = Query("security", enum=["security", "access", "data", "non_price_strategies"]),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Generate compliance report for specified period"""
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    if (end_date - start_date).days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report period cannot exceed 90 days"
        )

    try:
        report = await audit_logger.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )

        return {
            "success": True,
            "report": report,
            "generated_at": datetime.utcnow().isoformat(),
            "parameters": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "report_type": report_type
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating compliance report: {str(e)}"
        )


@router.get("/metrics/security")
async def get_security_metrics(
    hours: int = Query(24, ge=1, le=168),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get security metrics for monitoring dashboard"""
    try:
        import redis.asyncio as redis
        from core.config import settings
        import json

        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        current_time = datetime.utcnow()

        # Get recent events
        start_time = current_time - timedelta(hours=hours)
        events = await audit_logger.search_audit_logs(
            start_date=start_time,
            limit=10000
        )

        # Calculate metrics
        metrics = {
            "total_events": len(events),
            "failed_logins": sum(1 for e in events if 'login_failed' in e.get('event_type', '')),
            "security_violations": sum(1 for e in events if 'security_violation' in e.get('event_type', '')),
            "suspicious_activities": sum(1 for e in events if 'suspicious_activity' in e.get('event_type', '')),
            "unique_users": len(set(e.get('user_id') for e in events if e.get('user_id'))),
            "unique_ips": len(set(e.get('ip_address') for e in events if e.get('ip_address'))),
            "high_risk_events": sum(1 for e in events if e.get('severity') in ['critical', 'high']),
            "event_types": {},
            "hourly_distribution": {}
        }

        # Event type distribution
        for event in events:
            event_type = event.get('event_type', 'unknown')
            metrics['event_types'][event_type] = metrics['event_types'].get(event_type, 0) + 1

        # Hourly distribution
        for hour_offset in range(hours):
            hour = current_time - timedelta(hours=hour_offset)
            hour_key = hour.strftime('%Y-%m-%d:%H')
            hour_events = [
                e for e in events
                if datetime.fromisoformat(e['timestamp']).hour == hour.hour
            ]
            metrics['hourly_distribution'][hour_key] = len(hour_events)

        # Get rate limit metrics
        rate_limiter = get_rate_limiter()
        rate_metrics = {
            "blocked_ips": 0,
            "active_penalties": 0
        }

        if redis_client:
            # Count blocked IPs
            blocked_keys = await redis_client.keys("rate_penalty:*")
            for key in blocked_keys:
                penalty_data = await redis_client.get(key)
                if penalty_data:
                    penalty = json.loads(penalty_data)
                    if penalty.get('factor', 1.0) < 1.0:
                        rate_metrics['active_penalties'] += 1

        metrics['rate_limiting'] = rate_metrics

        return {
            "success": True,
            "metrics": metrics,
            "period": {
                "hours": hours,
                "start": start_time.isoformat(),
                "end": current_time.isoformat()
            },
            "generated_at": current_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating security metrics: {str(e)}"
        )