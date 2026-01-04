"""
Unified Input Validation Framework
統一輸入驗證框架

Comprehensive input validation and security protection for CBSC trading system.
Includes XSS protection, CSRF protection, rate limiting, and input sanitization.
"""

import re
import html
import bleach
import secrets
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, validator, Field, ValidationError
from functools import wraps
import json

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base security error"""
    pass


class XSSDetectionError(SecurityError):
    """XSS attack detected"""
    pass


class CSRFError(SecurityError):
    """CSRF token validation failed"""
    pass


class RateLimitExceededError(SecurityError):
    """Rate limit exceeded"""
    pass


class InputValidationError(SecurityError):
    """Input validation failed"""
    pass


@dataclass
class ValidationResult:
    """Validation result"""
    is_valid: bool
    sanitized_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    security_score: int = 100  # 0-100, lower is more risky


class CBSCInputValidator:
    """
    CBSC Unified Input Validator

    Provides comprehensive input validation with:
    - Pattern-based validation
    - XSS detection and prevention
    - SQL injection detection
    - Data type validation
    - Range and length checks
    """

    # CBSC-specific validation patterns
    CBS_PATTERNS = {
        'strategy_name': r'^[a-zA-Z0-9_\-\u4e00-\u9fff]{1,50}$',
        'symbol': r'^[A-Z0-9]{1,10}$',
        'parameter_name': r'^[a-z_][a-z0-9_]*$',
        'numeric_range': r'^-?\d+(\.\d+)?$',
        'percentage': r'^(100(\.0+)?|\d{1,2}(\.\d+)?)%?$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'ip_address': r'^(\d{1,3}\.){3}\d{1,3}$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    }

    # Dangerous patterns for security scanning
    DANGEROUS_PATTERNS = [
        (r'<script[^>]*>.*?</script>', 'XSS: Script tag'),
        (r'javascript:', 'XSS: JavaScript protocol'),
        (r'on\w+\s*=', 'XSS: Event handler'),
        (r'eval\s*\(', 'XSS: eval function'),
        (r'expression\s*\(', 'XSS: CSS expression'),
        (r'@import', 'XSS: CSS import'),
        (r'union\s+select', 'SQL Injection: UNION SELECT'),
        (r'drop\s+table', 'SQL Injection: DROP TABLE'),
        (r'delete\s+from', 'SQL Injection: DELETE FROM'),
        (r'insert\s+into', 'SQL Injection: INSERT INTO'),
        (r'update\s+\w+\s+set', 'SQL Injection: UPDATE SET'),
        (r'exec\s*\(', 'Code Execution: exec function'),
        (r'system\s*\(', 'Code Execution: system function'),
        (r'__import__\s*\(', 'Code Execution: Python import'),
        (r'\${.*}', 'Template Injection'),
    ]

    # Max length limits
    MAX_LENGTHS = {
        'strategy_name': 100,
        'symbol': 20,
        'description': 1000,
        'notes': 5000,
        'json_data': 10000,
    }

    def __init__(self):
        self.bleach_allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'b', 'i']
        self.bleach_allowed_attributes = {}

    def validate_input(self, data: Dict[str, Any], schema: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate input data against schema and security rules

        Args:
            data: Input data to validate
            schema: Optional schema definition

        Returns:
            ValidationResult with sanitized data and errors
        """
        result = ValidationResult(is_valid=True, sanitized_data={})
        security_score = 100

        for key, value in data.items():
            try:
                # Check for dangerous patterns first
                security_check = self._check_security(value)
                if not security_check['is_safe']:
                    result.errors.append(f"{key}: {security_check['reason']}")
                    result.is_valid = False
                    security_score -= security_check['risk_penalty']
                    continue

                # Type-specific validation
                sanitized_value = self._sanitize_value(value, key)
                result.sanitized_data[key] = sanitized_value

                # Schema validation if provided
                if schema and key in schema:
                    schema_result = self._validate_against_schema(
                        key, sanitized_value, schema[key]
                    )
                    if not schema_result['is_valid']:
                        result.errors.extend(schema_result['errors'])
                        result.is_valid = False

            except Exception as e:
                result.errors.append(f"{key}: {str(e)}")
                result.is_valid = False
                security_score -= 10

        result.security_score = max(0, security_score)
        return result

    def _check_security(self, value: Any) -> Dict[str, Any]:
        """
        Check value for security threats

        Returns:
            Dict with 'is_safe', 'reason', and 'risk_penalty'
        """
        if value is None:
            return {'is_safe': True, 'reason': None, 'risk_penalty': 0}

        value_str = str(value)

        # Check against dangerous patterns
        for pattern, threat_type in self.DANGEROUS_PATTERNS:
            if re.search(pattern, value_str, re.IGNORECASE):
                return {
                    'is_safe': False,
                    'reason': f'Dangerous pattern detected: {threat_type}',
                    'risk_penalty': 50
                }

        return {'is_safe': True, 'reason': None, 'risk_penalty': 0}

    def _sanitize_value(self, value: Any, field_name: str) -> Any:
        """Sanitize value based on type and field name"""
        if isinstance(value, str):
            # Apply bleach for HTML/XSS sanitization
            sanitized = bleach.clean(
                value,
                tags=self.bleach_allowed_tags,
                attributes=self.bleach_allowed_attributes,
                strip=True
            )

            # Check max length
            max_len = self.MAX_LENGTHS.get(field_name, 1000)
            if len(sanitized) > max_len:
                sanitized = sanitized[:max_len]

            return sanitized

        elif isinstance(value, (int, float, bool)):
            return value

        elif isinstance(value, list):
            return [self._sanitize_value(v, field_name) for v in value]

        elif isinstance(value, dict):
            return {
                k: self._sanitize_value(v, f"{field_name}.{k}")
                for k, v in value.items()
            }

        return value

    def _validate_against_schema(self, key: str, value: Any, schema: Dict) -> Dict[str, Any]:
        """Validate value against schema definition"""
        result = {'is_valid': True, 'errors': []}

        # Pattern validation
        if 'pattern' in schema:
            pattern = schema['pattern']
            if not re.match(pattern, str(value)):
                result['errors'].append(
                    f"{key} does not match required pattern"
                )
                result['is_valid'] = False

        # Range validation
        if 'min' in schema and isinstance(value, (int, float)):
            if value < schema['min']:
                result['errors'].append(
                    f"{key} must be >= {schema['min']}"
                )
                result['is_valid'] = False

        if 'max' in schema and isinstance(value, (int, float)):
            if value > schema['max']:
                result['errors'].append(
                    f"{key} must be <= {schema['max']}"
                )
                result['is_valid'] = False

        # Length validation
        if 'min_length' in schema and isinstance(value, str):
            if len(value) < schema['min_length']:
                result['errors'].append(
                    f"{key} must be at least {schema['min_length']} characters"
                )
                result['is_valid'] = False

        if 'max_length' in schema and isinstance(value, str):
            if len(value) > schema['max_length']:
                result['errors'].append(
                    f"{key} must be at most {schema['max_length']} characters"
                )
                result['is_valid'] = False

        # Enum validation
        if 'enum' in schema:
            if value not in schema['enum']:
                result['errors'].append(
                    f"{key} must be one of {schema['enum']}"
                )
                result['is_valid'] = False

        return result

    def validate_strategy_input(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate strategy-specific input

        Args:
            data: Strategy input data

        Returns:
            ValidationResult
        """
        schema = {
            'strategy_name': {
                'pattern': self.CBS_PATTERNS['strategy_name'],
                'min_length': 1,
                'max_length': 50
            },
            'symbol': {
                'pattern': self.CBS_PATTERNS['symbol'],
                'max_length': 10
            },
            'risk_level': {
                'min': 0,
                'max': 100
            }
        }

        return self.validate_input(data, schema)

    def validate_parameters(self, params: Dict[str, Any]) -> ValidationResult:
        """
        Validate strategy parameters

        Args:
            params: Strategy parameters

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, sanitized_data={})

        for param_name, param_value in params.items():
            # Validate parameter name
            if not re.match(self.CBS_PATTERNS['parameter_name'], param_name):
                result.errors.append(
                    f"Invalid parameter name: {param_name}"
                )
                result.is_valid = False
                continue

            # Sanitize parameter value
            sanitized = self._sanitize_value(param_value, param_name)
            result.sanitized_data[param_name] = sanitized

        return result


class XSSProtection:
    """
    Cross-Site Scripting (XSS) Protection

    Provides XSS detection, prevention, and Content Security Policy (CSP)
    """

    # XSS attack patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<embed[^>]*>.*?</embed>',
        r'<object[^>]*>.*?</object>',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
    ]

    def __init__(self):
        self.bleach_allowed_tags = []
        self.bleach_allowed_attributes = {}

    def detect_xss(self, input_data: str) -> Tuple[bool, List[str]]:
        """
        Detect XSS attempts in input

        Args:
            input_data: Input string to check

        Returns:
            Tuple of (is_xss_detected, list of detected patterns)
        """
        detected_patterns = []

        for pattern in self.XSS_PATTERNS:
            matches = re.findall(pattern, input_data, re.IGNORECASE)
            if matches:
                detected_patterns.append(pattern)

        return (len(detected_patterns) > 0, detected_patterns)

    def sanitize_html(self, html_content: str) -> str:
        """
        Sanitize HTML content to prevent XSS

        Args:
            html_content: HTML content to sanitize

        Returns:
            Sanitized HTML string
        """
        return bleach.clean(
            html_content,
            tags=self.bleach_allowed_tags,
            attributes=self.bleach_allowed_attributes,
            strip=True
        )

    def get_csp_headers(self) -> Dict[str, str]:
        """
        Get Content Security Policy headers

        Returns:
            Dictionary of CSP headers
        """
        return {
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss:// ws://; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ),
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        }


class CSRFProtection:
    """
    Cross-Site Request Forgery (CSRF) Protection

    Provides CSRF token generation and validation
    """

    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.token_expiry = 3600  # 1 hour

    def generate_token(self, user_id: int, session_id: str = None) -> str:
        """
        Generate CSRF token

        Args:
            user_id: User ID
            session_id: Optional session ID

        Returns:
            CSRF token
        """
        timestamp = int(datetime.utcnow().timestamp())
        data = f"{user_id}:{session_id or ''}:{timestamp}"
        signature = hmac_sha256(self.secret_key, data)
        return f"{data}:{signature}"

    def validate_token(self, token: str, user_id: int, session_id: str = None) -> bool:
        """
        Validate CSRF token

        Args:
            token: CSRF token to validate
            user_id: User ID
            session_id: Optional session ID

        Returns:
            True if token is valid
        """
        try:
            parts = token.split(':')
            if len(parts) != 4:
                return False

            token_user_id, token_session, timestamp, signature = parts

            # Verify user ID
            if int(token_user_id) != user_id:
                return False

            # Verify session
            if session_id and token_session != session_id:
                return False

            # Verify timestamp (not expired)
            token_time = int(timestamp)
            if datetime.utcnow().timestamp() - token_time > self.token_expiry:
                return False

            # Verify signature
            data = f"{token_user_id}:{token_session}:{timestamp}"
            expected_signature = hmac_sha256(self.secret_key, data)

            return secrets.compare_digest(signature, expected_signature)

        except Exception:
            return False


class RateLimiter:
    """
    API Rate Limiter and DDoS Protection

    Provides rate limiting for API endpoints
    """

    def __init__(self):
        self.requests = {}  # In production, use Redis
        self.blocked_ips = {}

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Check if rate limit is exceeded

        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            Dict with 'allowed', 'remaining', 'reset_time'
        """
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > window_start
            ]
        else:
            self.requests[identifier] = []

        # Check if blocked
        if identifier in self.blocked_ips:
            block_expiry = self.blocked_ips[identifier]
            if now < block_expiry:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': block_expiry.timestamp(),
                    'blocked': True
                }
            else:
                del self.blocked_ips[identifier]

        # Check rate limit
        request_count = len(self.requests[identifier])

        if request_count >= max_requests:
            # Block for exponential time
            block_duration = min(300, 2 ** (request_count - max_requests + 1))
            self.blocked_ips[identifier] = now + timedelta(seconds=block_duration)

            return {
                'allowed': False,
                'remaining': 0,
                'reset_time': (now + timedelta(seconds=window_seconds)).timestamp(),
                'blocked': False
            }

        # Add current request
        self.requests[identifier].append(now)

        return {
            'allowed': True,
            'remaining': max_requests - request_count - 1,
            'reset_time': (now + timedelta(seconds=window_seconds)).timestamp(),
            'blocked': False
        }

    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is currently blocked"""
        if identifier not in self.blocked_ips:
            return False

        if datetime.utcnow() >= self.blocked_ips[identifier]:
            del self.blocked_ips[identifier]
            return False

        return True


class FileUploadSecurity:
    """
    File Upload Security

    Validates and sanitizes uploaded files
    """

    ALLOWED_EXTENSIONS = {
        'csv', 'json', 'txt', 'pdf', 'png', 'jpg', 'jpeg'
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    DANGEROUS_EXTENSIONS = {
        'exe', 'bat', 'sh', 'php', 'jsp', 'asp', 'js', 'vbs'
    }

    def validate_file(
        self,
        filename: str,
        file_size: int,
        content_type: str
    ) -> ValidationResult:
        """
        Validate uploaded file

        Args:
            filename: File name
            file_size: File size in bytes
            content_type: MIME type

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)

        # Check file extension
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        if file_ext in self.DANGEROUS_EXTENSIONS:
            result.errors.append(f"Dangerous file extension: {file_ext}")
            result.is_valid = False
            result.security_score -= 100

        if file_ext not in self.ALLOWED_EXTENSIONS:
            result.errors.append(f"File extension not allowed: {file_ext}")
            result.is_valid = False
            result.security_score -= 50

        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            result.errors.append(f"File too large: {file_size} bytes")
            result.is_valid = False
            result.security_score -= 30

        # Check for double extensions
        if filename.count('.') > 1:
            result.warnings.append("File has multiple extensions")
            result.security_score -= 10

        return result


class DLPProtection:
    """
    Data Leakage Protection (DLP)

    Detects and prevents sensitive data leakage
    """

    # Sensitive data patterns
    SENSITIVE_PATTERNS = {
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'api_key': r'\b(AIza[0-9A-Za-z_-]{35}|sk-[a-zA-Z0-9]{48})\b',
        'password': r'\b(password|passwd|pwd)\s*[:=]\s*\S+',
        'ip_address': r'\b(\d{1,3}\.){3}\d{1,3}\b',
    }

    def scan_for_sensitive_data(self, data: str) -> Dict[str, List[str]]:
        """
        Scan data for sensitive information

        Args:
            data: Data to scan

        Returns:
            Dict mapping sensitive data type to list of findings
        """
        findings = {}

        for data_type, pattern in self.SENSITIVE_PATTERNS.items():
            matches = re.findall(pattern, data, re.IGNORECASE)
            if matches:
                findings[data_type] = matches

        return findings

    def mask_sensitive_data(self, data: str, data_types: List[str] = None) -> str:
        """
        Mask sensitive data in output

        Args:
            data: Data to mask
            data_types: Types to mask (default: all)

        Returns:
            Data with sensitive info masked
        """
        if data_types is None:
            data_types = list(self.SENSITIVE_PATTERNS.keys())

        masked_data = data

        for data_type in data_types:
            if data_type == 'credit_card':
                # Mask all but last 4 digits
                def mask_card(match):
                    card = match.group(0).replace('-', '').replace(' ', '')
                    if len(card) == 16:
                        return '*' * 12 + card[-4:]
                    return match.group(0)

                masked_data = re.sub(
                    self.SENSITIVE_PATTERNS['credit_card'],
                    mask_card,
                    masked_data
                )

            elif data_type == 'email':
                # Mask all but first character
                def mask_email(match):
                    email = match.group(0)
                    parts = email.split('@')
                    if len(parts) == 2:
                        return parts[0][0] + '***@' + parts[1]
                    return email

                masked_data = re.sub(
                    self.SENSITIVE_PATTERNS['email'],
                    mask_email,
                    masked_data
                )

            elif data_type == 'ip_address':
                # Mask IP address
                masked_data = re.sub(
                    self.SENSITIVE_PATTERNS['ip_address'],
                    '***.***.***.***',
                    masked_data
                )

            elif data_type == 'api_key':
                # Show first 10 chars only
                def mask_api_key(match):
                    key = match.group(0)
                    if len(key) > 10:
                        return key[:10] + '...'
                    return key

                masked_data = re.sub(
                    self.SENSITIVE_PATTERNS['api_key'],
                    mask_api_key,
                    masked_data
                )

        return masked_data


def hmac_sha256(key: str, data: str) -> str:
    """Generate HMAC-SHA256 signature"""
    import hmac
    return hmac.new(
        key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


# Global instances
input_validator = CBSCInputValidator()
xss_protection = XSSProtection()
csrf_protection = CSRFProtection()
rate_limiter = RateLimiter()
file_upload_security = FileUploadSecurity()
dlp_protection = DLPProtection()
