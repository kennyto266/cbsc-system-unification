"""
非價格策略認證API端點
Non-Price Strategy Authentication API Endpoints

Extended authentication endpoints for non-price strategy access control,
including role management, permission checks, and security monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..security.rbac import (
    UserRole, Permission, StrategyType, rbac_manager,
    require_permission
)
from ..security.audit_logger import (
    audit_logger, AuditEventType, EventSeverity,
    log_security_event, log_strategy_access
)
from ..security.encryption import encryption_service
from ..security.monitoring import (
    security_monitor, AlertType, ThreatLevel
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auth/non-price", tags=["非價格策略認證"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Pydantic models
class RoleAssignment(BaseModel):
    """Role assignment request"""
    user_id: str
    role: UserRole
    reason: str
    duration_days: Optional[int] = None  # Temporary role assignment


class PermissionCheck(BaseModel):
    """Permission check request"""
    permission: Permission
    strategy_type: Optional[StrategyType] = None
    resource_id: Optional[str] = None


class UserPermissionsResponse(BaseModel):
    """User permissions response"""
    user_id: str
    role: str
    permissions: List[str]
    strategy_access: List[str]
    data_access_level: str
    rate_limits: Dict[str, int]


class SecurityMetricsResponse(BaseModel):
    """Security metrics response"""
    active_alerts: int
    failed_logins_today: int
    rate_limit_violations_today: int
    blocked_ips: int
    last_updated: str


# Dependencies
async def get_current_user_with_role(token: str = Depends(oauth2_scheme)):
    """Get current user with role information"""
    # This would integrate with your existing authentication system
    # For now, return a mock user
    from auth_simple import auth_service
    user = auth_service.get_current_user(token)

    # Add role from RBAC manager
    user.role = rbac_manager.user_roles.get(str(user.id), UserRole.BASIC_USER)

    return user


async def require_admin_role(current_user = Depends(get_current_user_with_role)):
    """Require admin role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.NON_PRICE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Role management endpoints
@router.post("/roles/assign")
async def assign_role(
    role_assignment: RoleAssignment,
    current_user = Depends(require_admin_role),
    request: Request
):
    """Assign role to user for non-price strategy access"""
    try:
        # Validate role assignment
        if role_assignment.role not in [
            UserRole.NON_PRICE_VIEWER,
            UserRole.NON_PRICE_ANALYST,
            UserRole.NON_PRICE_ADMIN
        ] and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign this role"
            )

        # Assign role
        success = rbac_manager.assign_role(
            user_id=role_assignment.user_id,
            role=role_assignment.role,
            assigned_by=current_user.username
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to assign role"
            )

        # Log role assignment
        await audit_logger.log_event(
            event_type=AuditEventType.ROLE_CHANGE,
            user_id=role_assignment.user_id,
            ip_address=request.client.host,
            details={
                "new_role": role_assignment.role.value,
                "assigned_by": current_user.username,
                "reason": role_assignment.reason,
                "duration_days": role_assignment.duration_days
            }
        )

        logger.info(
            f"Role {role_assignment.role.value} assigned to user {role_assignment.user_id} "
            f"by {current_user.username}"
        )

        return {
            "message": "Role assigned successfully",
            "user_id": role_assignment.user_id,
            "role": role_assignment.role.value,
            "assigned_by": current_user.username
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Role assignment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign role"
        )


@router.get("/users/{user_id}/permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: str,
    current_user = Depends(get_current_user_with_role),
    request: Request
):
    """Get user permissions for non-price strategies"""
    try:
        # Check if user can view permissions (admin or self)
        if user_id != str(current_user.id) and current_user.role not in [
            UserRole.ADMIN, UserRole.NON_PRICE_ADMIN
        ]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other users' permissions"
            )

        # Get user permissions
        permissions = rbac_manager.get_user_permissions(user_id)
        if not permissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or has no permissions"
            )

        # Log permission view
        await audit_logger.log_event(
            event_type=AuditEventType.PERMISSION_GRANTED,
            user_id=str(current_user.id),
            ip_address=request.client.host,
            resource="user_permissions",
            action="view",
            details={
                "target_user": user_id,
                "permissions_shown": True
            }
        )

        return UserPermissionsResponse(**permissions)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve permissions"
        )


@router.post("/check-permission")
async def check_permission(
    permission_check: PermissionCheck,
    current_user = Depends(get_current_user_with_role),
    request: Request
):
    """Check if current user has specific permission"""
    try:
        user_id = str(current_user.id)

        # Check permission
        has_permission = rbac_manager.check_permission(
            user_id=user_id,
            permission=permission_check.permission,
            strategy_type=permission_check.strategy_type
        )

        # Log permission check
        await audit_logger.log_event(
            event_type=AuditEventType.PERMISSION_GRANTED if has_permission else AuditEventType.PERMISSION_DENIED,
            user_id=user_id,
            ip_address=request.client.host,
            resource=permission_check.strategy_type.value if permission_check.strategy_type else None,
            action="check_permission",
            details={
                "permission": permission_check.permission.value,
                "granted": has_permission,
                "resource_id": permission_check.resource_id
            },
            success=has_permission
        )

        # Create security alert for denied permissions
        if not has_permission:
            await security_monitor.create_alert(
                alert_type=AlertType.UNAUTHORIZED_ACCESS,
                threat_level=ThreatLevel.MEDIUM,
                description=f"Permission denied: {permission_check.permission.value}",
                user_id=user_id,
                ip_address=request.client.host,
                resource=permission_check.strategy_type.value if permission_check.strategy_type else None,
                details={
                    "permission": permission_check.permission.value,
                    "attempted_resource": permission_check.resource_id
                }
            )

        return {
            "has_permission": has_permission,
            "permission": permission_check.permission.value,
            "strategy_type": permission_check.strategy_type.value if permission_check.strategy_type else None,
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission check failed"
        )


@router.get("/strategies/accessible")
async def get_accessible_strategies(
    current_user = Depends(get_current_user_with_role)
):
    """Get list of strategies accessible to current user"""
    try:
        user_id = str(current_user.id)
        strategies = rbac_manager.get_accessible_strategies(user_id)

        return {
            "user_id": user_id,
            "accessible_strategies": [s.value for s in strategies],
            "total_count": len(strategies)
        }

    except Exception as e:
        logger.error(f"Failed to get accessible strategies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accessible strategies"
        )


# Security monitoring endpoints
@router.get("/security/metrics", response_model=SecurityMetricsResponse)
async def get_security_metrics(
    current_user = Depends(require_admin_role)
):
    """Get current security metrics"""
    try:
        # Get metrics from security monitor
        metrics = await security_monitor.generate_security_metrics()

        # Get additional metrics
        active_alerts = await security_monitor.get_active_alerts()
        failed_logins = await audit_logger.search_audit_logs(
            start_date=datetime.now().replace(hour=0, minute=0, second=0),
            event_type=AuditEventType.LOGIN_FAILED
        )
        rate_violations = await audit_logger.search_audit_logs(
            start_date=datetime.now().replace(hour=0, minute=0, second=0),
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED
        )

        return SecurityMetricsResponse(
            active_alerts=len(active_alerts),
            failed_logins_today=len(failed_logins),
            rate_limit_violations_today=len(rate_violations),
            blocked_ips=0,  # Implement if tracking blocked IPs
            last_updated=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security metrics"
        )


@router.get("/security/alerts")
async def get_security_alerts(
    alert_type: Optional[str] = None,
    threat_level: Optional[str] = None,
    limit: int = 100,
    current_user = Depends(require_admin_role)
):
    """Get security alerts"""
    try:
        # Convert string enums
        alert_type_enum = AlertType(alert_type) if alert_type else None
        threat_level_enum = ThreatLevel(threat_level) if threat_level else None

        # Get alerts
        alerts = await security_monitor.get_active_alerts(
            alert_type=alert_type_enum,
            threat_level=threat_level_enum,
            limit=limit
        )

        return {
            "alerts": [alert.__dict__ for alert in alerts],
            "total_count": len(alerts)
        }

    except Exception as e:
        logger.error(f"Failed to get security alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security alerts"
        )


@router.post("/security/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user = Depends(require_admin_role)
):
    """Acknowledge a security alert"""
    try:
        success = await security_monitor.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=current_user.username
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )

        return {
            "message": "Alert acknowledged",
            "alert_id": alert_id,
            "acknowledged_by": current_user.username
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )


# Audit endpoints
@router.get("/audit/logs")
async def get_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 1000,
    current_user = Depends(require_admin_role)
):
    """Get audit logs"""
    try:
        # Convert string enum
        event_type_enum = AuditEventType(event_type) if event_type else None

        # Get logs
        logs = await audit_logger.search_audit_logs(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            event_type=event_type_enum,
            limit=limit
        )

        return {
            "logs": logs,
            "total_count": len(logs)
        }

    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.post("/audit/reports")
async def generate_compliance_report(
    start_date: datetime,
    end_date: datetime,
    report_type: str = "security",
    current_user = Depends(require_admin_role)
):
    """Generate compliance report"""
    try:
        report = await audit_logger.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            report_type=report_type
        )

        return {
            "report": report,
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user.username
        }

    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )


# Strategy access logging
@router.post("/strategies/{strategy_id}/access")
async def log_strategy_access_endpoint(
    strategy_id: str,
    access_type: str = "view",
    current_user = Depends(get_current_user_with_role),
    request: Request
):
    """Log strategy access for audit"""
    try:
        await log_strategy_access(
            user_id=str(current_user.id),
            strategy_type=access_type,
            strategy_id=strategy_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )

        return {
            "message": "Access logged",
            "strategy_id": strategy_id,
            "access_type": access_type,
            "user_id": str(current_user.id)
        }

    except Exception as e:
        logger.error(f"Failed to log strategy access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log access"
        )