"""
Authentication Utilities
認證工具函數

Utility functions for device fingerprinting, security checks, and common auth operations
設備指紋識別、安全檢查和通用認證操作的工具函數
"""

import hashlib
import uuid
import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, HTTPException, status
from ua_parser import parse as parse_user_agent
# import geoip2.database
# import geoip2.errors

logger = logging.getLogger(__name__)

class DeviceFingerprinter:
    """Device fingerprinting utility"""

    @staticmethod
    def extract_device_info(request: Request) -> Dict[str, Any]:
        """Extract comprehensive device information"""
        user_agent_str = request.headers.get("user-agent", "")

        # Parse user agent
        user_agent = parse_user_agent(user_agent_str)

        # Collect browser characteristics
        accept_header = request.headers.get("accept", "")
        accept_lang = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")

        # Get client IP
        client_ip = DeviceFingerprinter.get_client_ip(request)

        # Build device info
        device_info = {
            "user_agent": user_agent_str,
            "browser": {
                "family": user_agent.browser.family,
                "version": user_agent.browser.version_string,
            },
            "os": {
                "family": user_agent.os.family,
                "version": user_agent.os.version_string,
            },
            "device": {
                "family": user_agent.device.family,
                "brand": user_agent.device.brand,
                "model": user_agent.device.model,
            },
            "accept_headers": {
                "accept": accept_header,
                "language": accept_lang,
                "encoding": accept_encoding,
            },
            "ip_address": client_ip,
            "screen_resolution": request.headers.get("x-screen-resolution"),
            "color_depth": request.headers.get("x-color-depth"),
            "timezone": request.headers.get("x-timezone"),
            "language": request.headers.get("x-language"),
            "platform": request.headers.get("x-platform"),
            "touch_support": request.headers.get("x-touch-support"),
        }

        # Generate fingerprint
        fingerprint_data = {
            "user_agent": user_agent_str,
            "accept": accept_header,
            "language": accept_lang,
            "encoding": accept_encoding,
            "platform": device_info["platform"],
            "screen": device_info["screen_resolution"],
            "timezone": device_info["timezone"],
        }

        device_info["fingerprint"] = DeviceFingerprinter.generate_fingerprint(
            fingerprint_data
        )

        return device_info

    @staticmethod
    def generate_fingerprint(data: Dict[str, Any]) -> str:
        """Generate device fingerprint from data"""
        # Create a deterministic string from the data
        fingerprint_str = "|".join(
            str(data.get(k, "")) for k in sorted(data.keys())
        )

        # Hash it
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get real client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct connection IP
        return request.client.host if request.client else "0.0.0.0"

class GeoLocationService:
    """IP geolocation service"""

    def __init__(self, geoip_db_path: Optional[str] = None):
        self.geoip_db_path = geoip_db_path
        self.reader = None

        if geoip_db_path:
            try:
                self.reader = geoip2.database.Reader(geoip_db_path)
            except Exception as e:
                logger.warning(f"Could not load GeoIP database: {e}")

    def get_location(self, ip_address: str) -> Dict[str, Any]:
        """Get location information for IP address"""
        location = {
            "ip": ip_address,
            "country": "Unknown",
            "city": "Unknown",
            "latitude": None,
            "longitude": None,
            "timezone": None,
        }

        if not self.reader:
            return location

        try:
            response = self.reader.city(ip_address)
            location.update({
                "country": response.country.name or "Unknown",
                "city": response.city.name or "Unknown",
                "latitude": response.location.latitude,
                "longitude": response.location.longitude,
                "timezone": response.location.time_zone,
            })
        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"IP {ip_address} not found in GeoIP database")
        except Exception as e:
            logger.error(f"GeoIP lookup error: {e}")

        return location

    def is_suspicious_location(self, ip_address: str, known_locations: list) -> bool:
        """Check if IP location is suspicious compared to known locations"""
        if not known_locations:
            return False

        current_location = self.get_location(ip_address)

        # Simple check: if country is different and not in known list
        known_countries = [loc.get("country") for loc in known_locations]
        if current_location["country"] not in known_countries:
            return True

        # TODO: Add more sophisticated checks (distance calculation, etc.)

        return False

class SecurityAnalyzer:
    """Security analysis utilities"""

    @staticmethod
    def analyze_login_patterns(attempts: list) -> Dict[str, Any]:
        """Analyze login attempt patterns"""
        if not attempts:
            return {"risk_score": 0, "warnings": []}

        risk_score = 0
        warnings = []

        # Check for rapid fire attempts
        recent_attempts = [
            a for a in attempts
            if a["timestamp"] > datetime.utcnow() - timedelta(minutes=5)
        ]

        if len(recent_attempts) > 5:
            risk_score += 30
            warnings.append("Multiple rapid login attempts")

        # Check for multiple IPs
        unique_ips = set(a["ip_address"] for a in attempts[-10:])
        if len(unique_ips) > 3:
            risk_score += 20
            warnings.append("Login attempts from multiple IPs")

        # Check for failure rate
        failures = sum(1 for a in attempts if not a["success"])
        if len(attempts) > 0 and (failures / len(attempts)) > 0.5:
            risk_score += 25
            warnings.append("High failure rate")

        return {
            "risk_score": min(risk_score, 100),
            "warnings": warnings,
            "recommendation": "Require additional verification" if risk_score > 50 else "Normal"
        }

    @staticmethod
    def check_ip_reputation(ip_address: str) -> Dict[str, Any]:
        """Check IP reputation (placeholder for external service integration)"""
        # TODO: Integrate with services like:
        # - AbuseIPDB
        # - IPQualityScore
        # - MaxMind minFraud

        # For now, just check if it's a private/internal IP
        private_patterns = [
            r"^10\.",
            r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
            r"^192\.168\.",
            r"^127\.",
            r"^169\.254\.",
            r"^::1$",
            r"^fc00:",
            r"^fe80:",
        ]

        is_private = any(re.match(pattern, ip_address) for pattern in private_patterns)

        return {
            "ip": ip_address,
            "is_private": is_private,
            "reputation": "safe" if is_private else "unknown",
            "threat_level": "low" if is_private else "unknown",
        }

class RateLimiter:
    """Rate limiting utility"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int,
        identifier: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if action is allowed based on rate limit

        Args:
            key: Rate limit key (e.g., "login", "password_reset")
            limit: Number of allowed requests
            window: Time window in seconds
            identifier: Unique identifier (IP, user ID, etc.)

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        if not self.redis:
            # If Redis is not available, allow all requests
            return True, {"remaining": limit, "reset_time": None}

        if identifier:
            rate_key = f"rate_limit:{key}:{identifier}"
        else:
            rate_key = f"rate_limit:{key}"

        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - window

        # Clean old entries
        self.redis.zremrangebyscore(rate_key, 0, window_start)

        # Count current entries
        current_count = self.redis.zcard(rate_key)

        if current_count >= limit:
            # Get when the limit will reset
            oldest = self.redis.zrange(rate_key, 0, 0, withscores=True)
            reset_time = int(oldest[0][1]) + window if oldest else current_time + window

            return False, {
                "remaining": 0,
                "reset_time": reset_time,
                "limit": limit,
                "window": window,
            }

        # Add current request
        self.redis.zadd(rate_key, {str(uuid.uuid4()): current_time})

        # Set expiration
        self.redis.expire(rate_key, window)

        return True, {
            "remaining": limit - current_count - 1,
            "reset_time": current_time + window,
            "limit": limit,
            "window": window,
        }

class PasswordValidator:
    """Password validation utilities"""

    @staticmethod
    def validate_complexity(password: str) -> Dict[str, Any]:
        """Validate password complexity and return detailed feedback"""
        result = {
            "is_valid": True,
            "score": 0,
            "requirements": {
                "length": len(password) >= 8,
                "uppercase": bool(re.search(r'[A-Z]', password)),
                "lowercase": bool(re.search(r'[a-z]', password)),
                "numbers": bool(re.search(r'\d', password)),
                "special": bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
                "no_common_patterns": True,
                "no_repeated_chars": True,
                "no_sequences": True,
            },
            "suggestions": [],
            "estimated_crack_time": None,
        }

        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'admin', 'welcome']
        if any(pattern in password.lower() for pattern in common_patterns):
            result["requirements"]["no_common_patterns"] = False
            result["suggestions"].append("Avoid common password patterns")

        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            result["requirements"]["no_repeated_chars"] = False
            result["suggestions"].append("Avoid repeating characters")

        # Check for sequences
        if re.search(r'(?:(?:012)|(?:abc)|(?:qwe))', password, re.I):
            result["requirements"]["no_sequences"] = False
            result["suggestions"].append("Avoid sequential characters")

        # Calculate score
        result["score"] = sum(result["requirements"].values())

        # Determine if password is acceptable
        result["is_valid"] = result["score"] >= 5

        # Add suggestions based on missing requirements
        if not result["requirements"]["length"]:
            result["suggestions"].append("Use at least 8 characters")
        if not result["requirements"]["uppercase"]:
            result["suggestions"].append("Include uppercase letters")
        if not result["requirements"]["lowercase"]:
            result["suggestions"].append("Include lowercase letters")
        if not result["requirements"]["numbers"]:
            result["suggestions"].append("Include numbers")
        if not result["requirements"]["special"]:
            result["suggestions"].append("Include special characters")

        # Estimate crack time (simplified)
        entropy = len(password) * 4  # Rough estimate
        if entropy < 28:
            result["estimated_crack_time"] = "Instantly"
        elif entropy < 36:
            result["estimated_crack_time"] = "Minutes"
        elif entropy < 44:
            result["estimated_crack_time"] = "Hours"
        elif entropy < 52:
            result["estimated_crack_time"] = "Days"
        elif entropy < 60:
            result["estimated_crack_time"] = "Years"
        else:
            result["estimated_crack_time"] = "Centuries"

        return result

class EmailService:
    """Email service for authentication notifications"""

    @staticmethod
    def send_verification_email(email: str, token: str):
        """Send email verification"""
        # TODO: Implement with actual email service
        # Could use:
        # - SendGrid
        # - AWS SES
        # - Mailgun
        # - SMTP

        logger.info(f"Verification email sent to {email} with token {token}")
        return True

    @staticmethod
    def send_password_reset_email(email: str, token: str):
        """Send password reset email"""
        logger.info(f"Password reset email sent to {email} with token {token}")
        return True

    @staticmethod
    def send_mfa_code_email(email: str, code: str):
        """Send MFA code via email"""
        logger.info(f"MFA code {code} sent to email {email}")
        return True

class AuditLogger:
    """Security audit logging"""

    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: Optional[int],
        ip_address: str,
        details: Dict[str, Any],
        risk_level: str = "low"
    ):
        """Log security event"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "details": details,
            "risk_level": risk_level,
        }

        logger.info(f"Security Event: {log_data}")

        # TODO: Send to SIEM or security monitoring system

# Initialize services
device_fingerprinter = DeviceFingerprinter()
# geoip_service = GeoLocationService("/path/to/GeoLite2-City.mmdb")  # Update path
security_analyzer = SecurityAnalyzer()
password_validator = PasswordValidator()
email_service = EmailService()
audit_logger = AuditLogger()

# Rate limiter requires Redis client
rate_limiter = None  # Will be initialized with Redis client in main app