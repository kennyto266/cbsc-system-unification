"""
Authentication Utility Functions
JWT handling, password management, and security utilities
"""

import jwt
import hashlib
import secrets
import string
import pytz
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
from passlib.context import CryptContext
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import pyotp
import re
import ipaddress
import user_agents
from email_validator import validate_email, EmailNotValidError

# Import custom exceptions
try:
    from .exceptions import TokenInvalidError, TokenExpiredError
except ImportError:
    # Fallback for standalone usage
    class TokenInvalidError(Exception):
        pass
    class TokenExpiredError(Exception):
        pass


# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
argon2_hasher = PasswordHasher()

# JWT Configuration
JWT_ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS = 24
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 2

# Password policy
PASSWORD_MIN_LENGTH = 8
_PASSWORD_HISTORY_COUNT = 5
_LOCKOUT_ATTEMPTS = 5
_LOCKOUT_MINUTES = 30

# Common passwords to reject
COMMON_PASSWORDS = {
    'password', '123456', '123456789', 'qwerty', 'abc123',
    'password123', 'admin', 'letmein', 'welcome', 'monkey',
    '1234567890', 'password1', 'qwerty123', 'starwars',
    'football', 'whatever', 'iloveyou', '123123', '1234'
}


def generate_rsa_keys() -> Tuple[str, str]:
    """Generate RSA key pair for JWT signing"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem.decode('utf-8'), public_pem.decode('utf-8')


def hash_password(password: str) -> str:
    """
    Hash password using Argon2id

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    try:
        return argon2_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def generate_jwt_tokens(
    user_id: str,
    username: str,
    private_key: str,
    permissions: List[str] = None,
    roles: List[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate JWT access and refresh tokens

    Args:
        user_id: User UUID
        username: Username
        private_key: RSA private key for signing
        permissions: List of user permissions
        roles: List of user roles

    Returns:
        Tuple of (access_token, refresh_token, payload)
    """
    now = datetime.utcnow()

    # Access token payload
    access_payload = {
        "sub": username,
        "user_id": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "permissions": permissions or [],
        "roles": roles or []
    }

    # Refresh token payload
    refresh_payload = {
        "sub": username,
        "user_id": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": secrets.token_urlsafe(32)  # Unique identifier
    }

    # Sign tokens with RSA private key
    access_token = jwt.encode(access_payload, private_key, algorithm=JWT_ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, private_key, algorithm=JWT_ALGORITHM)

    return access_token, refresh_token, access_payload


def verify_jwt_token(token: str, public_key: str, token_type: str = "access") -> Dict[str, Any]:
    """
    Verify and decode JWT token

    Args:
        token: JWT token string
        public_key: RSA public key for verification
        token_type: Expected token type (access or refresh)

    Returns:
        Token payload

    Raises:
        TokenInvalidError: If token is invalid
        TokenExpiredError: If token has expired
    """
    try:
        payload = jwt.decode(token, public_key, algorithms=[JWT_ALGORITHM])

        # Check token type
        if payload.get("type") != token_type:
            raise jwt.InvalidTokenError(f"Invalid token type. Expected {token_type}")

        return payload

    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")


def generate_password_reset_token(user_id: str, user_email: str) -> str:
    """
    Generate secure password reset token

    Args:
        user_id: User UUID
        user_email: User email for verification

    Returns:
        Secure token string
    """
    # Create token with user info and timestamp
    timestamp = str(int(datetime.utcnow().timestamp()))
    data = f"{user_id}:{user_email}:{timestamp}:{secrets.token_urlsafe(32)}"

    # Hash the data to create token
    token = hashlib.sha256(data.encode()).hexdigest()

    # Store the raw data for verification (in a secure way)
    return base64.urlsafe_b64encode(f"{token}:{timestamp}".encode()).decode()


def verify_password_reset_token(token: str, user_email: str, max_age_hours: int = PASSWORD_RESET_TOKEN_EXPIRE_HOURS) -> Optional[str]:
    """
    Verify password reset token and return user_id if valid

    Args:
        token: Password reset token
        user_email: User email to verify
        max_age_hours: Maximum age in hours

    Returns:
        User ID if valid, None otherwise
    """
    try:
        # Decode token
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        token_hash, timestamp = decoded.split(':')

        # Check age
        token_time = datetime.fromtimestamp(int(timestamp))
        if datetime.utcnow() - token_time > timedelta(hours=max_age_hours):
            return None

        # Note: In production, you'd store the actual token mapping in database
        # This is a simplified version for demonstration
        return token_hash  # Would return user_id in real implementation

    except (ValueError, KeyError):
        return None


def generate_email_verification_token(user_id: str, user_email: str) -> str:
    """
    Generate email verification token

    Args:
        user_id: User UUID
        user_email: User email

    Returns:
        Verification token string
    """
    data = f"{user_id}:{user_email}:{secrets.token_urlsafe(32)}"
    token = hashlib.sha256(data.encode()).hexdigest()

    # Return base64 encoded token with timestamp
    timestamp = str(int(datetime.utcnow().timestamp()))
    return base64.urlsafe_b64encode(f"{token}:{timestamp}".encode()).decode()


def verify_email_token(token: str, user_email: str, max_age_hours: int = EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS) -> bool:
    """
    Verify email verification token

    Args:
        token: Email verification token
        user_email: User email to verify
        max_age_hours: Maximum age in hours

    Returns:
        True if valid, False otherwise
    """
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        token_hash, timestamp = decoded.split(':')

        # Check age
        token_time = datetime.fromtimestamp(int(timestamp))
        if datetime.utcnow() - token_time > timedelta(hours=max_age_hours):
            return False

        # In production, verify against database
        return True

    except (ValueError, KeyError):
        return False


def validate_password_strength(password: str, username: str = None, email: str = None) -> Dict[str, Any]:
    """
    Validate password strength against security policies

    Args:
        password: Password to validate
        username: Username to check against
        email: Email to check against

    Returns:
        Dictionary with validation results
    """
    requirements = {
        'length': len(password) >= PASSWORD_MIN_LENGTH,
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'lowercase': bool(re.search(r'[a-z]', password)),
        'numbers': bool(re.search(r'\d', password)),
        'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
        'not_common': password.lower() not in COMMON_PASSWORDS,
        'not_username': not username or password.lower() != username.lower(),
        'not_email': not email or password.lower() not in email.lower(),
        'no_repeating': not re.search(r'(.)\1{2,}', password),  # No 3+ repeating chars
    }

    # Calculate score
    score = sum(requirements.values())

    # Determine strength level
    if score <= 3:
        strength = "weak"
    elif score <= 6:
        strength = "fair"
    elif score <= 8:
        strength = "good"
    else:
        strength = "strong"

    # Generate feedback
    feedback = []
    if not requirements['length']:
        feedback.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if not requirements['uppercase']:
        feedback.append("Include uppercase letters")
    if not requirements['lowercase']:
        feedback.append("Include lowercase letters")
    if not requirements['numbers']:
        feedback.append("Include numbers")
    if not requirements['special']:
        feedback.append("Include special characters")
    if not requirements['not_common']:
        feedback.append("Choose a less common password")
    if not requirements['not_username'] and username:
        feedback.append("Password cannot be same as username")
    if not requirements['not_email'] and email:
        feedback.append("Password cannot contain email")
    if not requirements['no_repeating']:
        feedback.append("Avoid repeating characters")

    return {
        'is_valid': score >= 6,  # Require at least 6 requirements
        'score': score,
        'strength': strength,
        'requirements': requirements,
        'feedback': feedback
    }


def generate_secure_password(length: int = 16) -> str:
    """
    Generate a secure random password

    Args:
        length: Password length

    Returns:
        Secure password string
    """
    # Use all character types
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Ensure at least one of each type
    password = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*()")
    ]

    # Fill the rest
    for _ in range(length - 4):
        password.append(secrets.choice(alphabet))

    # Shuffle
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def generate_mfa_secret() -> str:
    """
    Generate MFA secret key

    Returns:
        Base32 encoded secret key
    """
    return pyotp.random_base32()


def generate_mfa_qr_code(user_email: str, secret: str, issuer: str = "CBSC") -> str:
    """
    Generate QR code for MFA setup

    Args:
        user_email: User email
        secret: MFA secret
        issuer: Application name

    Returns:
        Base64 encoded QR code image
    """
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name=issuer
    )

    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.getvalue()).decode()


def verify_mfa_token(secret: str, token: str, valid_window: int = 1) -> bool:
    """
    Verify MFA token

    Args:
        secret: MFA secret key
        token: 6-digit token
        valid_window: Time window for valid tokens (default 1)

    Returns:
        True if token is valid
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(token, valid_window=valid_window)


def extract_device_info(user_agent_string: str, ip_address: str) -> Dict[str, Any]:
    """
    Extract device information from user agent and IP

    Args:
        user_agent_string: User agent string
        ip_address: Client IP address

    Returns:
        Device information dictionary
    """
    # Parse user agent
    ua = user_agents.parse(user_agent_string)

    device_info = {
        'device_name': f"{ua.browser.family} on {ua.os.family}",
        'device_type': 'mobile' if ua.is_mobile else 'tablet' if ua.is_tablet else 'desktop',
        'browser': ua.browser.family,
        'browser_version': ua.browser.version_string,
        'os': ua.os.family,
        'os_version': ua.os.version_string,
        'device_brand': ua.device.brand,
        'device_model': ua.device.model
    }

    # Parse IP address
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        device_info['is_private'] = ip_obj.is_private
        device_info['is_loopback'] = ip_obj.is_loopback
        device_info['ip_version'] = ip_obj.version
    except ValueError:
        device_info['is_private'] = True
        device_info['is_loopback'] = False
        device_info['ip_version'] = None

    return device_info


def generate_device_fingerprint(user_agent: str, ip_address: str) -> str:
    """
    Generate device fingerprint for tracking

    Args:
        user_agent: User agent string
        ip_address: Client IP address

    Returns:
        Unique device fingerprint
    """
    data = f"{user_agent}:{ip_address}"
    return hashlib.sha256(data.encode()).hexdigest()


def validate_email_format(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        True if valid
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def get_client_ip(request) -> str:
    """
    Get client IP address from request

    Args:
        request: FastAPI request object

    Returns:
        Client IP address
    """
    # Check for proxy headers
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Get the first IP in the list
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    # Fall back to direct connection
    return request.client.host if request.client else "127.0.0.1"


def calculate_lockout_time(failed_attempts: int, max_attempts: int = _LOCKOUT_ATTEMPTS) -> Optional[datetime]:
    """
    Calculate lockout time based on failed attempts

    Args:
        failed_attempts: Number of failed attempts
        max_attempts: Maximum allowed attempts

    Returns:
        Lockout expiry time or None if not locked
    """
    if failed_attempts < max_attempts:
        return None

    # Exponential backoff: 30min, 1hr, 2hr, 4hr, 8hr max
    excess_attempts = failed_attempts - max_attempts + 1
    lockout_hours = min(30 * (2 ** excess_attempts), 8 * 60)

    return datetime.utcnow() + timedelta(minutes=lockout_hours)


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS

    Args:
        text: Input text

    Returns:
        Sanitized text
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove potential script injections
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)

    return text.strip()


def generate_session_id() -> str:
    """
    Generate secure session ID

    Returns:
        Session ID string
    """
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    """
    Generate CSRF token

    Returns:
        CSRF token string
    """
    return secrets.token_urlsafe(32)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data like passwords or tokens

    Args:
        data: Data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to leave visible at end

    Returns:
        Masked data string
    """
    if len(data) <= visible_chars:
        return mask_char * len(data)

    return mask_char * (len(data) - visible_chars) + data[-visible_chars:]