"""
Device fingerprinting utility for MFA trusted devices

This module provides utilities to generate unique device fingerprints based on:
- User agent string
- IP address
- Browser characteristics
- Hardware information
"""

import hashlib
import json
from typing import Optional, Dict, Any
from fastapi import Request
import logging

logger = logging.getLogger(__name__)


def get_device_fingerprint(request: Request) -> Optional[str]:
    """
    Generate device fingerprint from request data

    Args:
        request: FastAPI Request object

    Returns:
        str: Device fingerprint or None if insufficient data
    """
    try:
        # Get request headers and client info
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""

        # Get common headers that might help identify the device
        accept_language = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")

        # Build fingerprint data
        fingerprint_data = {
            "user_agent": user_agent,
            "accept_language": accept_language,
            "accept_encoding": accept_encoding
        }

        # Try to get additional info from X-Forwarded headers if behind proxy
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            # Use the original IP if behind proxy
            ip_address = forwarded_for.split(",")[0].strip()

        fingerprint_data["ip_address"] = ip_address

        # Generate fingerprint hash
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        fingerprint_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()

        return fingerprint_hash

    except Exception as e:
        logger.error(f"Error generating device fingerprint: {str(e)}")
        return None


def parse_user_agent(user_agent: str) -> Dict[str, Any]:
    """
    Parse user agent string to extract device information

    Args:
        user_agent: User agent string from request headers

    Returns:
        Dict: Parsed device information
    """
    try:
        device_info = {
            "browser": "unknown",
            "version": "unknown",
            "os": "unknown",
            "device_type": "desktop"  # Default to desktop
        }

        user_agent_lower = user_agent.lower()

        # Detect browser
        if "chrome" in user_agent_lower and "edg" not in user_agent_lower:
            device_info["browser"] = "chrome"
            # Extract version
            try:
                version_start = user_agent_lower.find("chrome/") + 7
                version_end = user_agent_lower.find(" ", version_start)
                device_info["version"] = user_agent[version_start:version_end]
            except:
                pass
        elif "firefox" in user_agent_lower:
            device_info["browser"] = "firefox"
            try:
                version_start = user_agent_lower.find("firefox/") + 8
                device_info["version"] = user_agent[version_start:]
            except:
                pass
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            device_info["browser"] = "safari"
            try:
                version_start = user_agent_lower.find("version/") + 8
                version_end = user_agent_lower.find(" ", version_start)
                device_info["version"] = user_agent[version_start:version_end]
            except:
                pass
        elif "edg" in user_agent_lower:
            device_info["browser"] = "edge"
            try:
                version_start = user_agent_lower.find("edg/") + 4
                device_info["version"] = user_agent[version_start:]
            except:
                pass

        # Detect OS
        if "windows" in user_agent_lower:
            device_info["os"] = "windows"
        elif "mac os" in user_agent_lower or "macos" in user_agent_lower:
            device_info["os"] = "macos"
        elif "linux" in user_agent_lower:
            device_info["os"] = "linux"
        elif "android" in user_agent_lower:
            device_info["os"] = "android"
            device_info["device_type"] = "mobile"
        elif "ios" in user_agent_lower or "iphone" in user_agent_lower or "ipad" in user_agent_lower:
            device_info["os"] = "ios"
            if "iphone" in user_agent_lower:
                device_info["device_type"] = "mobile"
            elif "ipad" in user_agent_lower:
                device_info["device_type"] = "tablet"

        # Detect mobile devices
        if "mobile" in user_agent_lower:
            device_info["device_type"] = "mobile"
        elif "tablet" in user_agent_lower or "ipad" in user_agent_lower:
            device_info["device_type"] = "tablet"

        return device_info

    except Exception as e:
        logger.error(f"Error parsing user agent: {str(e)}")
        return {
            "browser": "unknown",
            "version": "unknown",
            "os": "unknown",
            "device_type": "desktop"
        }


def is_suspicious_device(fingerprint: str, user_agent: str, ip_address: str) -> bool:
    """
    Check if device appears suspicious based on patterns

    Args:
        fingerprint: Device fingerprint
        user_agent: User agent string
        ip_address: IP address

    Returns:
        bool: True if device appears suspicious
    """
    try:
        # Check for suspicious user agents
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper", "curl", "wget",
            "python-requests", "postman", "insomnia", "httpie"
        ]

        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if pattern in user_agent_lower:
                return True

        # Check for missing user agent
        if not user_agent or len(user_agent) < 10:
            return True

        # Check for suspicious IP ranges
        if ip_address:
            # TODO: Add more sophisticated IP validation
            # For now, just check if it's a valid format
            import ipaddress
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                return True

        return False

    except Exception as e:
        logger.error(f"Error checking suspicious device: {str(e)}")
        return False