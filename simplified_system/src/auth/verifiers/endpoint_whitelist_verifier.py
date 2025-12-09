#!/usr / bin / env python3
"""
Endpoint Whitelist Verifier
端点白名单验证器

Task 9: Implement Endpoint Whitelist with DNS validation
任务9：实现端点白名单，支持DNS验证

Provides dynamic whitelist management with approval workflow, DNS record
validation for endpoint ownership, and endpoint health monitoring.
"""

import asyncio
import ipaddress
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import dns.exception
    import dns.resolver

    DNS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"DNS libraries not available: {e}")
    DNS_AVAILABLE = False

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Requests library not available: {e}")
    REQUESTS_AVAILABLE = False

from ..interfaces.auth_result import AuthResult, Verdict
from ..interfaces.verifier_interface import IVerifier

logger = logging.getLogger(__name__)


class EndpointWhitelistVerifier(IVerifier):
    """
    Endpoint Whitelist Verifier for API endpoint validation
    端点白名单验证器，用于API端点验证

    Features:
    - Dynamic whitelist management with approval workflow
    - DNS record validation for endpoint ownership
    - Integration with existing stock API and government data API
    - Endpoint health monitoring and anomaly detection
    """

    def __init__(
        self,
        name: str = "Endpoint Whitelist Verifier",
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(name, config)

        # Whitelist storage
        self.whitelist_path = self.config.get("whitelist_path", "config / whitelist.json")
        self.approval_queue_path = self.config.get(
            "approval_queue_path", "config / approval_queue.json"
        )

        # Default trusted endpoints
        self.default_trusted_endpoints = {
            # Hong Kong Government APIs
            "api.hkma.gov.hk": {
                "owner": "Hong Kong Monetary Authority",
                "purpose": "Financial data API",
                "approved": True,
                "added_date": "2024 - 01 - 01",
                "required_dns_records": ["A", "AAAA", "TXT"],
            },
            "data.gov.hk": {
                "owner": "Hong Kong Government",
                "purpose": "Open data portal",
                "approved": True,
                "added_date": "2024 - 01 - 01",
                "required_dns_records": ["A", "AAAA"],
            },
            # Internal APIs
            "18.180.162.113": {
                "owner": "Internal Stock API",
                "purpose": "Stock market data",
                "approved": True,
                "added_date": "2024 - 01 - 01",
                "required_dns_records": ["A"],
                "port_specific": {"9191": "Stock data API"},
            },
            # Local development
            "localhost": {
                "owner": "Local Development",
                "purpose": "Development and testing",
                "approved": True,
                "added_date": "2024 - 01 - 01",
                "localhost": True,
            },
            "127.0.0.1": {
                "owner": "Local Development",
                "purpose": "Development and testing",
                "approved": True,
                "added_date": "2024 - 01 - 01",
                "localhost": True,
            },
        }

        # Validation settings
        self.enable_dns_validation = self.config.get("enable_dns_validation", True)
        self.dns_timeout = self.config.get("dns_timeout", 5.0)
        self.health_check_interval = self.config.get(
            "health_check_interval", 300
        )  # 5 minutes
        self.max_redirects = self.config.get("max_redirects", 3)

        # Security settings
        self.block_private_ips = self.config.get("block_private_ips", True)
        self.block_suspicious_tlds = self.config.get("block_suspicious_tlds", True)
        self.suspicious_tlds = self.config.get(
            "suspicious_tlds",
            [".tk", ".ml", ".ga", ".cf", ".pw", ".top", ".click", ".xyz"],
        )

        # Load whitelist and approval queue
        self._load_whitelist()
        self._load_approval_queue()

        logger.info(
            f"Endpoint Whitelist Verifier initialized with {len(self.whitelist)} whitelisted endpoints"
        )

    def _load_whitelist(self):
        """Load endpoint whitelist from file"""
        try:
            whitelist_file = Path(self.whitelist_path)
            if whitelist_file.exists():
                with open(whitelist_file, "r", encoding="utf - 8") as f:
                    loaded_whitelist = json.load(f)
                    # Merge with defaults
                    self.whitelist = {
                        **self.default_trusted_endpoints,
                        **loaded_whitelist,
                    }
            else:
                self.whitelist = self.default_trusted_endpoints.copy()
                self._save_whitelist()

        except Exception as e:
            logger.error(f"Failed to load whitelist: {e}")
            self.whitelist = self.default_trusted_endpoints.copy()

    def _save_whitelist(self):
        """Save whitelist to file"""
        try:
            whitelist_file = Path(self.whitelist_path)
            whitelist_file.parent.mkdir(parents = True, exist_ok = True)

            with open(whitelist_file, "w", encoding="utf - 8") as f:
                json.dump(self.whitelist, f, indent = 2, ensure_ascii = False)

            logger.info("Whitelist saved successfully")

        except Exception as e:
            logger.error(f"Failed to save whitelist: {e}")

    def _load_approval_queue(self):
        """Load approval queue from file"""
        try:
            approval_file = Path(self.approval_queue_path)
            if approval_file.exists():
                with open(approval_file, "r", encoding="utf - 8") as f:
                    self.approval_queue = json.load(f)
            else:
                self.approval_queue = []

        except Exception as e:
            logger.error(f"Failed to load approval queue: {e}")
            self.approval_queue = []

    def _save_approval_queue(self):
        """Save approval queue to file"""
        try:
            approval_file = Path(self.approval_queue_path)
            approval_file.parent.mkdir(parents = True, exist_ok = True)

            with open(approval_file, "w", encoding="utf - 8") as f:
                json.dump(self.approval_queue, f, indent = 2, ensure_ascii = False)

        except Exception as e:
            logger.error(f"Failed to save approval queue: {e}")

    async def verify(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """
        Verify endpoint against whitelist

        Args:
            data: Endpoint data (URL, hostname, or connection info)
            data_id: Unique data identifier
            context: Verification context (request purpose, etc.)

        Returns:
            AuthResult: Verification result
        """
        start_time = time.time()

        result = AuthResult(
            data_id = data_id,
            overall_verdict = Verdict.UNKNOWN,
            overall_confidence = 0.0,
            metadata={"algorithm": "endpoint_whitelist", "verifier": self.name},
        )

        try:
            # Extract endpoint information
            endpoint_info = self._extract_endpoint_info(data, context)

            if not endpoint_info.get("hostname"):
                result.overall_verdict = Verdict.SUSPICIOUS
                result.overall_confidence = 0.2
                result.error_message = "No hostname or endpoint information provided"
                return result

            hostname = endpoint_info["hostname"]
            port = endpoint_info.get("port")

            # Perform basic endpoint validation
            basic_validation = await self._validate_endpoint_basic(hostname, port)
            if not basic_validation["valid"]:
                result.overall_verdict = Verdict.FALSIFIED
                result.overall_confidence = 0.9
                result.error_message = basic_validation["error"]
                result.metadata.update(basic_validation["metadata"])
                return result

            # Check whitelist
            whitelist_result = await self._check_whitelist(
                hostname, port, endpoint_info
            )
            result.overall_verdict = whitelist_result["verdict"]
            result.overall_confidence = whitelist_result["confidence"]
            result.metadata.update(whitelist_result["metadata"])

            # If whitelisted, perform DNS validation if required
            if (
                result.overall_verdict in [Verdict.AUTHENTIC, Verdict.SUSPICIOUS]
                and self.enable_dns_validation
                and DNS_AVAILABLE
            ):

                dns_result = await self._validate_dns_records(
                    hostname, whitelist_result["whitelist_entry"]
                )
                result.metadata["dns_validation"] = dns_result

                if dns_result["valid"]:
                    result.overall_confidence = min(
                        result.overall_confidence + 0.1, 1.0
                    )
                else:
                    result.overall_verdict = Verdict.SUSPICIOUS
                    result.overall_confidence = max(
                        result.overall_confidence - 0.2, 0.3
                    )

            # Perform health check if endpoint is approved
            if (
                result.overall_verdict == Verdict.AUTHENTIC
                and REQUESTS_AVAILABLE
                and endpoint_info.get("check_health", False)
            ):

                health_result = await self._check_endpoint_health(
                    hostname, port, endpoint_info
                )
                result.metadata["health_check"] = health_result

                if not health_result["healthy"]:
                    result.overall_confidence = max(
                        result.overall_confidence - 0.1, 0.6
                    )

            logger.info(
                f"Endpoint whitelist verification completed for {hostname}: {result.overall_verdict.value}"
            )

        except asyncio.TimeoutError:
            result.overall_verdict = Verdict.ERROR
            result.error_message = f"Endpoint verification timeout"

        except Exception as e:
            result.overall_verdict = Verdict.ERROR
            result.error_message = f"Endpoint whitelist verification failed: {str(e)}"
            logger.error(f"Endpoint verification error for {data_id}: {e}")

        finally:
            result.total_execution_time_ms = (time.time() - start_time) * 1000

        return result

    def _extract_endpoint_info(
        self, data: Any, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract endpoint information from data and context"""
        endpoint_info = {}

        # Handle URL
        if isinstance(data, str):
            if data.startswith("http://") or data.startswith("https://"):
                # Parse URL
                if data.startswith("https://"):
                    endpoint_info["protocol"] = "https"
                    url_part = data[8:]
                else:
                    endpoint_info["protocol"] = "http"
                    url_part = data[7:]

                # Extract hostname and port
                if "/" in url_part:
                    host_part = url_part.split("/")[0]
                else:
                    host_part = url_part

                if ":" in host_part:
                    endpoint_info["hostname"], endpoint_info["port"] = host_part.split(
                        ":"
                    )
                    endpoint_info["port"] = int(endpoint_info["port"])
                else:
                    endpoint_info["hostname"] = host_part
                    endpoint_info["port"] = (
                        443 if endpoint_info["protocol"] == "https" else 80
                    )
            else:
                # Raw hostname
                endpoint_info["hostname"] = data

        # Handle dict with endpoint info
        elif isinstance(data, dict):
            endpoint_info.update(data)

        # Add context information
        if context:
            endpoint_info.update(context)

        return endpoint_info

    async def _validate_endpoint_basic(
        self, hostname: str, port: Optional[int]
    ) -> Dict[str, Any]:
        """Perform basic endpoint validation"""
        try:
            # Check for private IPs (if blocking is enabled)
            if self.block_private_ips:
                try:
                    ip = ipaddress.ip_address(hostname)
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        if not any(
                            localhost in hostname
                            for localhost in ["localhost", "127.0.0.1"]
                        ):
                            return {
                                "valid": False,
                                "error": f"Private IP address not allowed: {hostname}",
                                "metadata": {
                                    "ip_type": "private",
                                    "ip_address": str(ip),
                                },
                            }
                except ValueError:
                    # Not an IP address, continue with hostname validation
                    pass

            # Check for suspicious TLDs
            if self.block_suspicious_tlds and "." in hostname:
                tld = "." + hostname.split(".")[-1]
                if tld in self.suspicious_tlds:
                    return {
                        "valid": False,
                        "error": f"Suspicious TLD not allowed: {tld}",
                        "metadata": {"suspicious_tld": tld},
                    }

            # Basic hostname format validation
            if not self._is_valid_hostname(hostname):
                return {
                    "valid": False,
                    "error": f"Invalid hostname format: {hostname}",
                    "metadata": {"hostname_format": "invalid"},
                }

            return {
                "valid": True,
                "metadata": {
                    "hostname": hostname,
                    "port": port,
                    "hostname_format": "valid",
                },
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Basic validation error: {str(e)}",
                "metadata": {},
            }

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Check if hostname format is valid"""
        if len(hostname) > 253:
            return False

        if hostname[-1] == ".":
            hostname = hostname[:-1]  # Remove trailing dot

        allowed = re.compile(
            r"^[a - zA - Z0 - 9]([a - zA - Z0 - 9\-]{0,61}[a - zA - Z0 - 9])?(\.[a - zA - Z0 - 9]([a - zA - Z0 - 9\-]{0,61}[a - zA - Z0 - 9])?)*$"
        )
        return allowed.match(hostname) is not None

    async def _check_whitelist(
        self, hostname: str, port: Optional[int], endpoint_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if endpoint is in whitelist"""
        try:
            # Check exact hostname match
            if hostname in self.whitelist:
                whitelist_entry = self.whitelist[hostname]

                if whitelist_entry.get("approved", False):
                    # Check port - specific rules
                    if port and "port_specific" in whitelist_entry:
                        if str(port) not in whitelist_entry["port_specific"]:
                            return {
                                "verdict": Verdict.SUSPICIOUS,
                                "confidence": 0.6,
                                "whitelist_entry": whitelist_entry,
                                "metadata": {
                                    "whitelist_status": "approved",
                                    "port_allowed": False,
                                    "allowed_ports": list(
                                        whitelist_entry["port_specific"].keys()
                                    ),
                                },
                            }

                    return {
                        "verdict": Verdict.AUTHENTIC,
                        "confidence": 0.9,
                        "whitelist_entry": whitelist_entry,
                        "metadata": {
                            "whitelist_status": "approved",
                            "owner": whitelist_entry.get("owner", "Unknown"),
                            "purpose": whitelist_entry.get("purpose", "Unknown"),
                        },
                    }
                else:
                    return {
                        "verdict": Verdict.SUSPICIOUS,
                        "confidence": 0.4,
                        "whitelist_entry": whitelist_entry,
                        "metadata": {
                            "whitelist_status": "pending_approval",
                            "reason": "Endpoint not yet approved",
                        },
                    }

            # Check for partial matches (subdomains, etc.)
            for whitelist_hostname, whitelist_entry in self.whitelist.items():
                if whitelist_entry.get("approved", False):
                    if whitelist_entry.get("localhost", False):
                        continue

                    # Check subdomain
                    if whitelist_hostname.startswith("*.") and hostname.endswith(
                        whitelist_hostname[1:]
                    ):
                        return {
                            "verdict": Verdict.AUTHENTIC,
                            "confidence": 0.8,
                            "whitelist_entry": whitelist_entry,
                            "metadata": {
                                "whitelist_status": "approved",
                                "match_type": "subdomain",
                                "parent_domain": whitelist_hostname,
                                "owner": whitelist_entry.get("owner", "Unknown"),
                            },
                        }

            # Endpoint not found in whitelist
            return {
                "verdict": Verdict.SUSPICIOUS,
                "confidence": 0.3,
                "whitelist_entry": None,
                "metadata": {
                    "whitelist_status": "not_found",
                    "action_required": "add_to_approval_queue",
                },
            }

        except Exception as e:
            return {
                "verdict": Verdict.ERROR,
                "confidence": 0.0,
                "whitelist_entry": None,
                "metadata": {"error": f"Whitelist check error: {str(e)}"},
            }

    async def _validate_dns_records(
        self, hostname: str, whitelist_entry: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate DNS records for endpoint ownership"""
        if not whitelist_entry or "required_dns_records" not in whitelist_entry:
            return {"valid": True, "note": "No DNS validation required"}

        try:
            required_records = whitelist_entry["required_dns_records"]
            validation_results = {}

            for record_type in required_records:
                try:
                    if record_type.upper() == "A":
                        answers = dns.resolver.resolve(hostname, "A")
                        validation_results["A"] = {
                            "valid": True,
                            "records": [str(answer) for answer in answers],
                            "count": len(answers),
                        }

                    elif record_type.upper() == "AAAA":
                        answers = dns.resolver.resolve(hostname, "AAAA")
                        validation_results["AAAA"] = {
                            "valid": True,
                            "records": [str(answer) for answer in answers],
                            "count": len(answers),
                        }

                    elif record_type.upper() == "TXT":
                        answers = dns.resolver.resolve(hostname, "TXT")
                        validation_results["TXT"] = {
                            "valid": True,
                            "records": [str(answer) for answer in answers],
                            "count": len(answers),
                        }

                    elif record_type.upper() == "MX":
                        answers = dns.resolver.resolve(hostname, "MX")
                        validation_results["MX"] = {
                            "valid": True,
                            "records": [str(answer) for answer in answers],
                            "count": len(answers),
                        }

                    else:
                        validation_results[record_type] = {
                            "valid": False,
                            "error": f"Unsupported record type: {record_type}",
                        }

                except dns.resolver.NXDOMAIN:
                    validation_results[record_type] = {
                        "valid": False,
                        "error": "Domain does not exist",
                    }
                except dns.resolver.NoAnswer:
                    validation_results[record_type] = {
                        "valid": False,
                        "error": f"No {record_type} records found",
                    }
                except Exception as e:
                    validation_results[record_type] = {"valid": False, "error": str(e)}

            # Overall validation result
            all_valid = all(
                result.get("valid", False) for result in validation_results.values()
            )

            return {
                "valid": all_valid,
                "required_records": required_records,
                "validation_results": validation_results,
                "hostname": hostname,
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"DNS validation error: {str(e)}",
                "hostname": hostname,
            }

    async def _check_endpoint_health(
        self, hostname: str, port: Optional[int], endpoint_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check endpoint health"""
        try:
            protocol = endpoint_info.get("protocol", "https")
            url = f"{protocol}://{hostname}"
            if port and port not in [80, 443]:
                url += f":{port}"

            # Simple health check
            try:
                response = requests.get(
                    url,
                    timeout = 5,
                    allow_redirects = True,
                    headers={"User - Agent": "EndpointHealthCheck / 1.0"},
                )

                return {
                    "healthy": response.status_code < 400,
                    "status_code": response.status_code,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "url": url,
                }

            except requests.exceptions.ConnectionError:
                return {"healthy": False, "error": "Connection failed", "url": url}
            except requests.exceptions.Timeout:
                return {"healthy": False, "error": "Request timeout", "url": url}

        except Exception as e:
            return {"healthy": False, "error": f"Health check error: {str(e)}"}

    def get_verifier_type(self) -> str:
        """Get verifier type identifier"""
        return "endpoint_whitelist"

    def get_supported_data_types(self) -> List[str]:
        """Get supported data types"""
        return [
            "url",
            "hostname",
            "api_endpoint",
            "connection_info",
            "endpoint_address",
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the endpoint whitelist verifier"""
        health_status = {
            "verifier": self.name,
            "type": self.get_verifier_type(),
            "enabled": self.enabled,
            "status": "healthy",
            "whitelist_size": len(self.whitelist),
            "approval_queue_size": len(self.approval_queue),
            "dns_available": DNS_AVAILABLE,
            "requests_available": REQUESTS_AVAILABLE,
        }

        # Test DNS resolution
        if DNS_AVAILABLE:
            try:
                # Test with a known domain
                dns.resolver.resolve("google.com", "A")
                health_status["dns_resolution_test"] = "passed"
            except Exception as e:
                health_status["dns_resolution_test"] = f"failed: {str(e)}"
                health_status["status"] = "degraded"

        # Test with a whitelisted endpoint
        try:
            test_result = await self._check_whitelist("api.hkma.gov.hk", None, {})
            if test_result["verdict"] == Verdict.AUTHENTIC:
                health_status["whitelist_test"] = "passed"
            else:
                health_status["whitelist_test"] = f"failed: unexpected result"
                health_status["status"] = "degraded"

        except Exception as e:
            health_status["whitelist_test"] = f"failed: {str(e)}"
            health_status["status"] = "unhealthy"

        return health_status

    async def cleanup(self):
        """Cleanup resources"""
        logger.info(f"Cleaning up {self.name}")
        self._save_whitelist()
        self._save_approval_queue()


# Import required modules
import re
