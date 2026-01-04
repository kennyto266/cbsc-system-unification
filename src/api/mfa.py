"""
MFA (Multi-Factor Authentication) API endpoints

This module provides RESTful API endpoints for managing multi-factor authentication:
- Enable/disable MFA
- TOTP setup and verification
- SMS verification
- Email verification
- Backup codes management
- Trusted devices management
- Security settings
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import logging

# Database
from src.core.database import get_db

# Authentication
from .auth import get_current_user, verify_token

# Services
from src.services.auth.email_verification import email_verification_service
from src.services.auth.totp_service import totp_service
from src.services.auth.sms_service import sms_service

# Models
from src.models.user import User
from src.models.mfa_models import (
    MFASession, MFATrustedDevice, UserSecuritySettings,
    MFAEnrollmentRequestSchema, MFAVerificationRequestSchema,
    MFADisableRequestSchema, MFAStatusResponseSchema,
    MFATrustedDeviceCreateSchema, MFATrustedDeviceResponseSchema,
    UserSecuritySettingsResponseSchema, UserSecuritySettingsUpdateSchema
)

# Utils
from src.utils.device_fingerprint import get_device_fingerprint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mfa", tags=["mfa"])
security = HTTPBearer()


def create_mfa_session(
    db: Session,
    user_id: str,
    mfa_type: str,
    ip_address: str = None,
    user_agent: str = None,
    expires_minutes: int = 10
) -> MFASession:
    """Create new MFA session"""
    session_token = f"mfa_{user_id}_{datetime.now(timezone.utc).timestamp()}"

    mfa_session = MFASession(
        user_id=user_id,
        session_token=session_token,
        mfa_type=mfa_type,
        status='pending',
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(mfa_session)
    db.commit()
    db.refresh(mfa_session)

    return mfa_session


@router.get("/status", response_model=MFAStatusResponseSchema)
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's MFA status"""
    try:
        # Get MFA status from services
        totp_status = totp_service.get_totp_status(current_user.id)
        sms_status = sms_service.get_sms_status(current_user.id)

        # Get security settings
        security_settings = db.query(UserSecuritySettings).filter(
            UserSecuritySettings.user_id == current_user.id
        ).first()

        # Count trusted devices
        trusted_devices_count = db.query(MFATrustedDevice).filter(
            MFATrustedDevice.user_id == current_user.id,
            MFATrustedDevice.is_active == True,
            MFATrustedDevice.expires_at > datetime.now(timezone.utc)
        ).count()

        # Get recent MFA attempts from audit log
        recent_attempts = db.query(MFASession).filter(
            MFASession.user_id == current_user.id,
            MFASession.created_at > datetime.now(timezone.utc) - timedelta(hours=24)
        ).count()

        response_data = {
            "mfa_enabled": current_user.mfa_enabled or False,
            "mfa_type": current_user.mfa_type,
            "phone_verified": bool(current_user.phone),
            "phone_display": (
                current_user.phone[:3] + "****" + current_user.phone[-4:]
                if current_user.phone and len(current_user.phone) > 7
                else None
            ),
            "backup_codes_available": (
                totp_status["data"]["remaining_backup_codes"]
                if totp_status["success"] and totp_status["data"].get("remaining_backup_codes")
                else 0
            ),
            "trusted_devices_count": trusted_devices_count,
            "recent_login_attempts": recent_attempts,
            "security_settings": {
                "require_mfa_for_login": security_settings.require_mfa_for_login if security_settings else False,
                "require_mfa_for_sensitive_operations": security_settings.require_mfa_for_sensitive_operations if security_settings else True,
                "enable_trusted_devices": security_settings.enable_trusted_devices if security_settings else True,
                "preferred_mfa_method": security_settings.preferred_mfa_method if security_settings else None
            }
        }

        return MFAStatusResponseSchema(**response_data)

    except Exception as e:
        logger.error(f"Error getting MFA status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get MFA status"
        )


@router.post("/enroll/totp")
async def enroll_totp(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Start TOTP enrollment process"""
    try:
        if current_user.mfa_enabled and current_user.mfa_type == "totp":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP is already enabled"
            )

        # Generate TOTP secret and QR code
        result = totp_service.generate_totp_secret(current_user.id)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to generate TOTP secret")
            )

        # Create audit log
        # TODO: Add audit log entry

        return {
            "success": True,
            "data": result["data"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling TOTP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start TOTP enrollment"
        )


@router.post("/enroll/totp/verify")
async def verify_totp_setup(
    verification_code: str,
    current_user: User = Depends(get_current_user)
):
    """Verify TOTP setup and enable MFA"""
    try:
        result = totp_service.verify_totp_setup(current_user.id, verification_code)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "TOTP verification failed")
            )

        # TODO: Add audit log entry

        return {
            "success": True,
            "message": "TOTP enabled successfully",
            "mfa_enabled": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying TOTP setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify TOTP setup"
        )


@router.post("/enroll/sms")
async def enroll_sms(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Start SMS MFA enrollment"""
    try:
        if current_user.mfa_enabled and current_user.mfa_type == "sms":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SMS verification is already enabled"
            )

        if not current_user.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number not set"
            )

        # Send OTP for enabling SMS MFA
        result = sms_service.send_otp(current_user.id, "mfa_enable")

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to send SMS")
            )

        return {
            "success": True,
            "message": "Verification code sent to your phone",
            "expires_at": result.get("expires_at"),
            "phone_display": result.get("phone_display")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enrolling SMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start SMS enrollment"
        )


@router.post("/enroll/sms/verify")
async def verify_sms_setup(
    verification_code: str,
    current_user: User = Depends(get_current_user)
):
    """Verify SMS setup and enable MFA"""
    try:
        result = sms_service.enable_sms_mfa(current_user.id, verification_code)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "SMS verification failed")
            )

        # TODO: Add audit log entry

        return {
            "success": True,
            "message": "SMS verification enabled successfully",
            "mfa_enabled": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying SMS setup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify SMS setup"
        )


@router.post("/verify")
async def verify_mfa(
    request: MFAVerificationRequestSchema,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify MFA during login or sensitive operation"""
    try:
        # Check if user has MFA enabled
        if not current_user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this user"
            )

        # Verify based on MFA type
        if current_user.mfa_type == "totp":
            if request.verification_code:
                result = totp_service.verify_totp_token(current_user.id, request.verification_code)
            elif request.backup_code:
                result = totp_service.verify_backup_code(current_user.id, request.backup_code)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification code or backup code is required"
                )

        elif current_user.mfa_type == "sms":
            result = sms_service.verify_otp(current_user.id, request.verification_code, "mfa_verify")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported MFA type: {current_user.mfa_type}"
            )

        if not result["success"]:
            # Update MFA session if provided
            if request.session_token:
                mfa_session = db.query(MFASession).filter(
                    MFASession.session_token == request.session_token,
                    MFASession.user_id == current_user.id,
                    MFASession.status == 'pending'
                ).first()

                if mfa_session:
                    mfa_session.increment_attempt()
                    db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "MFA verification failed")
            )

        # Add trusted device if requested
        if request.remember_device:
            device_fingerprint = get_device_fingerprint(http_request)
            if device_fingerprint:
                security_settings = db.query(UserSecuritySettings).filter(
                    UserSecuritySettings.user_id == current_user.id
                ).first()

                if security_settings and security_settings.enable_trusted_devices:
                    expires_at = datetime.now(timezone.utc) + timedelta(
                        days=security_settings.trusted_device_duration_days
                    )

                    trusted_device = MFATrustedDevice(
                        user_id=current_user.id,
                        device_fingerprint=device_fingerprint,
                        device_type="unknown",  # TODO: Detect device type
                        expires_at=expires_at,
                        ip_address=http_request.client.host,
                        user_agent=http_request.headers.get("user-agent")
                    )

                    db.add(trusted_device)
                    db.commit()

        # TODO: Add audit log entry

        return {
            "success": True,
            "message": "MFA verification successful",
            "verified": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MFA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA"
        )


@router.post("/disable")
async def disable_mfa(
    request: MFADisableRequestSchema,
    current_user: User = Depends(get_current_user)
):
    """Disable MFA for user"""
    try:
        if not current_user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled"
            )

        if not request.confirmation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation is required to disable MFA"
            )

        # Verify using appropriate method
        if current_user.mfa_type == "totp":
            result = totp_service.disable_totp(
                current_user.id,
                token=request.verification_code,
                backup_code=request.backup_code
            )
        elif current_user.mfa_type == "sms":
            result = sms_service.disable_sms_mfa(current_user.id, request.verification_code)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported MFA type: {current_user.mfa_type}"
            )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to disable MFA")
            )

        # TODO: Add audit log entry

        return {
            "success": True,
            "message": "MFA disabled successfully",
            "mfa_disabled": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling MFA: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )


@router.post("/backup-codes/regenerate")
async def regenerate_backup_codes(
    verification_code: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Regenerate backup codes"""
    try:
        if not current_user.mfa_enabled or current_user.mfa_type != "totp":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP must be enabled to generate backup codes"
            )

        result = totp_service.regenerate_backup_codes(current_user.id, verification_code)

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to regenerate backup codes")
            )

        # TODO: Add audit log entry

        return {
            "success": True,
            "message": "Backup codes regenerated successfully",
            "backup_codes": result["backup_codes"],
            "warning": result["warning"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating backup codes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate backup codes"
        )


@router.get("/trusted-devices", response_model=List[MFATrustedDeviceResponseSchema])
async def get_trusted_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trusted devices"""
    try:
        devices = db.query(MFATrustedDevice).filter(
            MFATrustedDevice.user_id == current_user.id,
            MFATrustedDevice.is_active == True
        ).all()

        return [
            MFATrustedDeviceResponseSchema(
                **device.__dict__,
                is_expired=device.is_expired()
            )
            for device in devices
        ]

    except Exception as e:
        logger.error(f"Error getting trusted devices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trusted devices"
        )


@router.delete("/trusted-devices/{device_id}")
async def revoke_trusted_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke trusted device"""
    try:
        device = db.query(MFATrustedDevice).filter(
            MFATrustedDevice.id == device_id,
            MFATrustedDevice.user_id == current_user.id
        ).first()

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trusted device not found"
            )

        device.is_active = False
        db.commit()

        return {
            "success": True,
            "message": "Trusted device revoked successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking trusted device: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke trusted device"
        )


@router.get("/security-settings", response_model=UserSecuritySettingsResponseSchema)
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's security settings"""
    try:
        settings = db.query(UserSecuritySettings).filter(
            UserSecuritySettings.user_id == current_user.id
        ).first()

        if not settings:
            # Create default settings
            settings = UserSecuritySettings(user_id=current_user.id)
            db.add(settings)
            db.commit()
            db.refresh(settings)

        return UserSecuritySettingsResponseSchema.from_orm(settings)

    except Exception as e:
        logger.error(f"Error getting security settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get security settings"
        )


@router.put("/security-settings", response_model=UserSecuritySettingsResponseSchema)
async def update_security_settings(
    settings_update: UserSecuritySettingsUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's security settings"""
    try:
        settings = db.query(UserSecuritySettings).filter(
            UserSecuritySettings.user_id == current_user.id
        ).first()

        if not settings:
            settings = UserSecuritySettings(user_id=current_user.id)
            db.add(settings)

        # Update settings
        update_data = settings_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)

        db.commit()
        db.refresh(settings)

        return UserSecuritySettingsResponseSchema.from_orm(settings)

    except Exception as e:
        logger.error(f"Error updating security settings: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update security settings"
        )