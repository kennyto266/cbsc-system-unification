"""
Enhanced Authentication Service
Comprehensive user management and security service
"""

import os
import json
import smtplib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import logging

# Local imports
from .models import (
    User, Role, Permission, UserRole, RolePermission,
    UserSession, UserDevice, LoginHistory, PasswordHistory, AuditLog
)
from .schemas import (
    UserCreate, UserUpdate, UserResponse, RoleCreate, RoleUpdate,
    PasswordStrengthResult, LoginHistoryResponse, AuditLogResponse,
    PasswordPolicy
)
from .utils import (
    hash_password, verify_password, generate_jwt_tokens, verify_jwt_token,
    generate_password_reset_token, verify_password_reset_token,
    generate_email_verification_token, verify_email_token,
    validate_password_strength, generate_secure_password,
    generate_mfa_secret, generate_mfa_qr_code, verify_mfa_token,
    extract_device_info, generate_device_fingerprint, validate_email_format,
    get_client_ip, calculate_lockout_time, sanitize_input,
    generate_session_id, mask_sensitive_data
)
from .exceptions import (
    AuthenticationError, InvalidCredentialsError, UserNotFoundError,
    UserInactiveError, UserNotVerifiedError, UserLockedError,
    TokenExpiredError, TokenInvalidError, PasswordTooWeakError,
    PasswordAlreadyUsedError, EmailVerificationError, MFATokenError,
    MFARequiredError, RateLimitExceededError, EmailSendError,
    UserAlreadyExistsError, RoleAlreadyExistsError, PermissionDeniedError,
    DatabaseError, ConfigurationError
)

# Configure logging
logger = logging.getLogger(__name__)


class AuthService:
    """Enhanced authentication service with enterprise-grade features"""

    def __init__(self, database_url: str = None, config: Dict[str, Any] = None):
        """
        Initialize authentication service

        Args:
            database_url: Database connection URL
            config: Configuration dictionary
        """
        self.database_url = database_url or os.getenv("DATABASE_URL", "postgresql://localhost/cbsc")
        self.config = config or {}

        # JWT Keys
        self.jwt_private_key = self.config.get("JWT_PRIVATE_KEY") or self._load_jwt_keys()
        self.jwt_public_key = self.config.get("JWT_PUBLIC_KEY") or self._load_jwt_keys(public=True)

        # Email configuration
        self.smtp_host = self.config.get("SMTP_HOST", os.getenv("SMTP_HOST"))
        self.smtp_port = self.config.get("SMTP_PORT", 587)
        self.smtp_username = self.config.get("SMTP_USERNAME", os.getenv("SMTP_USERNAME"))
        self.smtp_password = self.config.get("SMTP_PASSWORD", os.getenv("SMTP_PASSWORD"))
        self.smtp_use_tls = self.config.get("SMTP_USE_TLS", True)
        self.from_email = self.config.get("FROM_EMAIL", os.getenv("FROM_EMAIL", "noreply@cbsc.com"))

        # Security settings
        self.password_policy = PasswordPolicy(**self.config.get("PASSWORD_POLICY", {}))
        self.rate_limit_enabled = self.config.get("RATE_LIMIT_ENABLED", True)
        self.mfa_required = self.config.get("MFA_REQUIRED", False)

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                echo=self.config.get("DEBUG", False)
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError("Database connection failed", "init_database")

    def _load_jwt_keys(self, public: bool = False) -> Optional[str]:
        """
        Load JWT keys from environment or files

        Args:
            public: Load public key if True, private key if False

        Returns:
            Key string or None
        """
        if public:
            key_path = self.config.get("JWT_PUBLIC_KEY_PATH") or os.getenv("JWT_PUBLIC_KEY_PATH")
            if key_path and os.path.exists(key_path):
                with open(key_path, 'r') as f:
                    return f.read()
            return os.getenv("JWT_PUBLIC_KEY")
        else:
            key_path = self.config.get("JWT_PRIVATE_KEY_PATH") or os.getenv("JWT_PRIVATE_KEY_PATH")
            if key_path and os.path.exists(key_path):
                with open(key_path, 'r') as f:
                    return f.read()
            return os.getenv("JWT_PRIVATE_KEY")

    def get_db(self) -> Session:
        """Get database session"""
        return self.SessionLocal()

    def create_user(self, user_data: UserCreate, db: Session = None) -> UserResponse:
        """
        Create new user

        Args:
            user_data: User creation data
            db: Database session

        Returns:
            Created user response

        Raises:
            UserAlreadyExistsError: If user already exists
            PasswordTooWeakError: If password is too weak
        """
        if db is None:
            db = self.get_db()

        try:
            # Check if user exists
            if db.query(User).filter(
                or_(
                    User.username == user_data.username,
                    User.email == user_data.email
                )
            ).first():
                field = "username" if db.query(User).filter(User.username == user_data.username).first() else "email"
                value = getattr(user_data, field)
                raise UserAlreadyExistsError(field, value)

            # Validate password strength
            validation = validate_password_strength(
                user_data.password,
                user_data.username,
                user_data.email
            )
            if not validation['is_valid']:
                raise PasswordTooWeakError(
                    "Password does not meet security requirements",
                    validation['requirements']
                )

            # Hash password
            password_hash = hash_password(user_data.password)

            # Create user
            user = User(
                username=user_data.username,
                email=user_data.email,
                password_hash=password_hash,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                display_name=user_data.display_name or f"{user_data.first_name} {user_data.last_name}".strip(),
                phone=user_data.phone,
                timezone=user_data.timezone,
                language=user_data.language,
                theme=user_data.theme,
                is_premium=user_data.is_premium,
                mfa_enabled=self.mfa_required
            )

            db.add(user)
            db.flush()  # Get user ID

            # Add default role (viewer)
            default_role = db.query(Role).filter(Role.name == "viewer").first()
            if default_role:
                user_role = UserRole(
                    user_id=user.id,
                    role_id=default_role.id,
                    is_active=True
                )
                db.add(user_role)

            # Create initial device record
            device = UserDevice(
                user_id=user.id,
                device_name="Registration Device",
                device_type="desktop",
                is_trusted=True
            )
            db.add(device)

            # Commit all changes
            db.commit()

            # Send verification email
            self._send_verification_email(user.email, str(user.id))

            # Log user creation
            self._log_audit(
                db=db,
                user_id=user.id,
                action="user.create",
                resource_type="user",
                resource_id=user.id,
                status="success",
                new_values={
                    "username": user.username,
                    "email": user.email
                }
            )

            logger.info(f"User created: {user.username}")
            return UserResponse.from_orm(user)

        except IntegrityError as e:
            db.rollback()
            logger.error(f"User creation failed (integrity): {e}")
            raise UserAlreadyExistsError("user", user_data.username)
        except Exception as e:
            db.rollback()
            logger.error(f"User creation failed: {e}")
            raise
        finally:
            if db is None:
                db.close()

    def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str = None,
        user_agent: str = None,
        device_fingerprint: str = None,
        db: Session = None
    ) -> Tuple[User, Dict[str, Any]]:
        """
        Authenticate user and create session

        Args:
            username: Username or email
            password: Plain password
            ip_address: Client IP address
            user_agent: User agent string
            device_fingerprint: Device fingerprint
            db: Database session

        Returns:
            Tuple of (user, session_data)

        Raises:
            InvalidCredentialsError: If credentials are invalid
            UserLockedError: If account is locked
            MFARequiredError: If MFA is required
        """
        if db is None:
            db = self.get_db()

        try:
            # Find user
            user = db.query(User).filter(
                or_(
                    User.username == username,
                    User.email == username
                )
            ).first()

            # Record login attempt
            success = False
            failure_reason = None

            if not user:
                failure_reason = "User not found"
                self._record_login_attempt(
                    db, None, username, ip_address, user_agent,
                    False, failure_reason, device_fingerprint
                )
                raise InvalidCredentialsError()

            # Check if account is locked
            if user.is_locked:
                self._record_login_attempt(
                    db, user.id, username, ip_address, user_agent,
                    False, "Account locked", device_fingerprint
                )
                raise UserLockedError(
                    "Account is temporarily locked",
                    user.locked_until.isoformat() if user.locked_until else None
                )

            # Check if account is active
            if not user.is_active:
                failure_reason = "Account inactive"
                self._record_login_attempt(
                    db, user.id, username, ip_address, user_agent,
                    False, failure_reason, device_fingerprint
                )
                raise UserInactiveError()

            # Check if email is verified
            if not user.is_verified:
                failure_reason = "Email not verified"
                self._record_login_attempt(
                    db, user.id, username, ip_address, user_agent,
                    False, failure_reason, device_fingerprint
                )
                raise UserNotVerifiedError()

            # Verify password
            if not verify_password(password, user.password_hash):
                # Increment failed attempts
                user.failed_login_attempts += 1

                # Check if should lock account
                if user.failed_login_attempts >= self.password_policy.lockout_attempts:
                    user.locked_until = calculate_lockout_time(user.failed_login_attempts)
                    failure_reason = f"Account locked for {self.password_policy.lockout_minutes} minutes"
                else:
                    failure_reason = "Invalid password"

                self._record_login_attempt(
                    db, user.id, username, ip_address, user_agent,
                    False, failure_reason, device_fingerprint
                )
                db.commit()
                raise InvalidCredentialsError()

            # Successful authentication
            success = True
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address

            # Record successful login
            self._record_login_attempt(
                db, user.id, username, ip_address, user_agent,
                True, None, device_fingerprint
            )

            # Get or create device
            device = self._get_or_create_device(
                db, user.id, device_fingerprint, user_agent, ip_address
            )

            # Generate tokens
            access_token, refresh_token, payload = generate_jwt_tokens(
                str(user.id),
                user.username,
                self.jwt_private_key,
                user.permissions,
                user.role_names
            )

            # Create session
            session = UserSession(
                user_id=user.id,
                session_token=access_token,
                refresh_token=refresh_token,
                device_id=device.id if device else None,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(minutes=30)
            )
            db.add(session)

            # Update device usage
            if device:
                device.last_seen_at = datetime.utcnow()
                device.usage_count += 1

            db.commit()

            # Prepare session data
            session_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 30 * 60,  # 30 minutes
                "user": UserResponse.from_orm(user),
                "permissions": user.permissions,
                "roles": user.role_names,
                "session_id": str(session.id)
            }

            # Log successful login
            self._log_audit(
                db=db,
                user_id=user.id,
                action="auth.login",
                status="success",
                ip_address=ip_address,
                user_agent=user_agent
            )

            logger.info(f"User authenticated: {user.username}")
            return user, session_data

        except Exception as e:
            if not isinstance(e, AuthenticationError):
                logger.error(f"Authentication error: {e}")
                raise InvalidCredentialsError()
            raise
        finally:
            if db is None:
                db.close()

    def refresh_token(self, refresh_token: str, db: Session = None) -> Dict[str, Any]:
        """
        Refresh access token

        Args:
            refresh_token: Refresh token
            db: Database session

        Returns:
            New token data

        Raises:
            TokenInvalidError: If token is invalid
            TokenExpiredError: If token is expired
        """
        if db is None:
            db = self.get_db()

        try:
            # Verify refresh token
            payload = verify_jwt_token(refresh_token, self.jwt_public_key, "refresh")

            # Find session
            session = db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True
            ).first()

            if not session:
                raise TokenInvalidError("Session not found")

            # Check if session is expired
            if session.expires_at < datetime.utcnow():
                session.is_active = False
                db.commit()
                raise TokenExpiredError("Session expired")

            # Get user
            user = db.query(User).filter(User.id == payload["user_id"]).first()
            if not user or not user.is_active:
                raise TokenInvalidError("User not found or inactive")

            # Generate new tokens
            access_token, new_refresh_token, _ = generate_jwt_tokens(
                str(user.id),
                user.username,
                self.jwt_private_key,
                user.permissions,
                user.role_names
            )

            # Update session
            session.session_token = access_token
            session.refresh_token = new_refresh_token
            session.last_accessed_at = datetime.utcnow()
            session.expires_at = datetime.utcnow() + timedelta(minutes=30)

            db.commit()

            return {
                "access_token": access_token,
                "refresh_token": new_refresh_token,
                "expires_in": 30 * 60
            }

        except Exception as e:
            if not isinstance(e, AuthenticationError):
                logger.error(f"Token refresh error: {e}")
                raise TokenInvalidError("Token refresh failed")
            raise
        finally:
            if db is None:
                db.close()

    def logout_user(self, session_token: str, db: Session = None) -> bool:
        """
        Logout user by revoking session

        Args:
            session_token: Session token
            db: Database session

        Returns:
            True if successful
        """
        if db is None:
            db = self.get_db()

        try:
            # Find session
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            ).first()

            if session:
                # Revoke session
                session.is_active = False
                session.revoked_at = datetime.utcnow()

                # Log logout
                self._log_audit(
                    db=db,
                    user_id=session.user_id,
                    action="auth.logout",
                    status="success",
                    session_id=session.id
                )

                db.commit()
                logger.info(f"User logged out: session {session.id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Logout error: {e}")
            db.rollback()
            return False
        finally:
            if db is None:
                db.close()

    def _record_login_attempt(
        self,
        db: Session,
        user_id: Optional[UUID],
        username: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        failure_reason: str = None,
        device_fingerprint: str = None
    ):
        """Record login attempt in history"""
        try:
            # Extract device info
            device_info = {}
            if user_agent:
                device_info = extract_device_info(user_agent, ip_address or "")

            login_history = LoginHistory(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=device_info,
                success=success,
                failure_reason=failure_reason
            )

            db.add(login_history)
            db.commit()

        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
            db.rollback()

    def _get_or_create_device(
        self,
        db: Session,
        user_id: UUID,
        device_fingerprint: str,
        user_agent: str,
        ip_address: str
    ) -> Optional[UserDevice]:
        """Get or create device record"""
        if not device_fingerprint:
            return None

        try:
            # Try to find existing device
            device = db.query(UserDevice).filter(
                UserDevice.user_id == user_id,
                UserDevice.device_fingerprint == device_fingerprint
            ).first()

            if device:
                return device

            # Create new device
            device_info = extract_device_info(user_agent or "", ip_address or "")
            device = UserDevice(
                user_id=user_id,
                device_name=device_info.get('device_name', 'Unknown Device'),
                device_type=device_info.get('device_type', 'desktop'),
                device_fingerprint=device_fingerprint,
                platform=device_info.get('os'),
                browser=device_info.get('browser'),
                browser_version=device_info.get('browser_version'),
                last_ip=ip_address
            )
            db.add(device)
            return device

        except Exception as e:
            logger.error(f"Failed to get/create device: {e}")
            return None

    def _send_verification_email(self, email: str, user_id: str):
        """Send email verification"""
        try:
            if not self.smtp_host:
                logger.warning("SMTP not configured, skipping email verification")
                return

            # Generate verification token
            token = generate_email_verification_token(user_id, email)

            # Create email
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = email
            msg['Subject'] = "Verify your CBSC account"

            # HTML body
            html = f"""
            <html>
                <body>
                    <h2>Welcome to CBSC!</h2>
                    <p>Please click the link below to verify your email:</p>
                    <p><a href="https://cbsc.com/auth/verify?token={token}">Verify Email</a></p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you did not create this account, please ignore this email.</p>
                </body>
            </html>
            """

            msg.attach(MimeText(html, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Verification email sent to: {email}")

        except Exception as e:
            logger.error(f"Failed to send verification email: {e}")
            raise EmailSendError("Failed to send verification email", email)

    def _log_audit(
        self,
        db: Session,
        user_id: Optional[UUID],
        action: str,
        resource_type: str = None,
        resource_id: UUID = None,
        status: str = "success",
        status_code: int = None,
        error_message: str = None,
        old_values: Dict = None,
        new_values: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        session_id: UUID = None,
        request_id: str = None,
        metadata: Dict = None
    ):
        """Log audit event"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                status_code=status_code,
                error_message=error_message,
                old_values=old_values,
                new_values=new_values,
                session_id=session_id,
                request_id=request_id,
                metadata=metadata
            )

            db.add(audit_log)
            db.commit()

        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
            db.rollback()

    def get_user_by_id(self, user_id: str, db: Session = None) -> Optional[User]:
        """Get user by ID"""
        if db is None:
            db = self.get_db()

        try:
            return db.query(User).filter(
                User.id == UUID(user_id),
                User.is_deleted == False
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
        finally:
            if db is None:
                db.close()

    def update_user(self, user_id: str, user_data: UserUpdate, db: Session = None) -> UserResponse:
        """Update user information"""
        if db is None:
            db = self.get_db()

        try:
            user = db.query(User).filter(User.id == UUID(user_id)).first()
            if not user:
                raise UserNotFoundError()

            # Store old values for audit
            old_values = {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "display_name": user.display_name
            }

            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)

            user.updated_at = datetime.utcnow()

            db.commit()

            # Log update
            self._log_audit(
                db=db,
                user_id=user.id,
                action="user.update",
                resource_type="user",
                resource_id=user.id,
                old_values=old_values,
                new_values=update_data
            )

            return UserResponse.from_orm(user)

        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            db.rollback()
            raise
        finally:
            if db is None:
                db.close()

    # Additional methods would go here for:
    # - Password reset flow
    # - Email verification
    # - MFA setup/verification
    # - Role management
    # - Permission checking
    # - User listing with filters
    # - Session management
    # - Audit log retrieval