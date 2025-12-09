#!/usr / bin / env python3
"""
Phase 2: Source Authentication Layer Integration
阶段2：源认证层集成

Integrates all Phase 2 verifiers with the DataAuthenticityManager and
provides unified authentication for the simplified system.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .interfaces.auth_result import AuthResult, AuthStatus, Verdict
from .interfaces.data_authenticity_manager import DataAuthenticityManager
from .verifiers.digital_signature_verifier import DigitalSignatureVerifier
from .verifiers.endpoint_whitelist_verifier import EndpointWhitelistVerifier
from .verifiers.rate_limit_anomaly_detector import RateLimitAnomalyDetector
from .verifiers.tls_certificate_validator import TLSCertificateValidator

logger = logging.getLogger(__name__)


class Phase2SourceAuthentication:
    """
    Phase 2 Source Authentication Layer
    阶段2源认证层

    Integrates digital signature verification, TLS certificate validation,
    endpoint whitelisting, and rate limiting for comprehensive source authentication.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Phase 2 Source Authentication

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.auth_manager = DataAuthenticityManager(self.config.get("integration", {}))

        # Initialize verifiers
        self.verifiers = {}
        self._initialize_verifiers()

        logger.info("Phase 2 Source Authentication initialized")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            if config_path is None:
                # Default config path
                config_path = (
                    Path(__file__).parent
                    / "config"
                    / "phase2_authentication_config.yaml"
                )

            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, "r", encoding="utf - 8") as f:
                    return yaml.safe_load(f)
            else:
                logger.warning(f"Configuration file not found: {config_path}")
                return {}

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}

    def _initialize_verifiers(self):
        """Initialize all Phase 2 verifiers"""
        try:
            # Digital Signature Verifier (Task 5)
            if self.config.get("digital_signature_verifier", {}).get("enabled", False):
                ds_config = self.config.get("digital_signature_verifier", {})
                ds_verifier = DigitalSignatureVerifier(config = ds_config)
                self.verifiers["digital_signature"] = ds_verifier
                self.auth_manager.register_verifier(ds_verifier)
                logger.info("Digital Signature Verifier initialized")

            # TLS Certificate Validator (Task 7)
            if self.config.get("tls_certificate_validator", {}).get("enabled", False):
                tls_config = self.config.get("tls_certificate_validator", {})
                tls_verifier = TLSCertificateValidator(config = tls_config)
                self.verifiers["tls_certificate"] = tls_verifier
                self.auth_manager.register_verifier(tls_verifier)
                logger.info("TLS Certificate Validator initialized")

            # Endpoint Whitelist Verifier (Task 9)
            if self.config.get("endpoint_whitelist_verifier", {}).get("enabled", False):
                ew_config = self.config.get("endpoint_whitelist_verifier", {})
                ew_verifier = EndpointWhitelistVerifier(config = ew_config)
                self.verifiers["endpoint_whitelist"] = ew_verifier
                self.auth_manager.register_verifier(ew_verifier)
                logger.info("Endpoint Whitelist Verifier initialized")

            # Rate Limit Anomaly Detector (Task 10)
            if self.config.get("rate_limit_anomaly_detector", {}).get("enabled", False):
                rl_config = self.config.get("rate_limit_anomaly_detector", {})
                rl_verifier = RateLimitAnomalyDetector(config = rl_config)
                self.verifiers["rate_limit"] = rl_verifier
                self.auth_manager.register_verifier(rl_verifier)
                logger.info("Rate Limit Anomaly Detector initialized")

        except Exception as e:
            logger.error(f"Failed to initialize verifiers: {e}")

    async def authenticate_hkma_data(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """
        Authenticate HKMA government data

        Args:
            data: Data to authenticate
            data_id: Unique data identifier
            context: Authentication context

        Returns:
            AuthResult: Authentication result
        """
        try:
            # Determine appropriate verifiers for HKMA data
            verifier_types = self._get_verifiers_for_data_source("hkma_apis")

            # Add HKMA - specific context
            hkma_context = {
                **(context or {}),
                "data_source": "hkma_api",
                "expected_issuer": "hkma.gov.hk",
                "require_signature": True,
                "require_tls": True,
            }

            # Perform authentication
            result = await self.auth_manager.verify_data(
                data = data,
                data_id = data_id,
                data_type="government_financial_data",
                data_source="hkma.gov.hk",
                verifier_types = verifier_types,
                context = hkma_context,
            )

            # Log authentication attempt
            await self._log_authentication_attempt("hkma_data", data_id, result)

            return result

        except Exception as e:
            logger.error(f"HKMA data authentication failed: {e}")
            return AuthResult(
                data_id = data_id,
                overall_verdict = Verdict.ERROR,
                overall_confidence = 0.0,
                error_message = f"HKMA authentication error: {str(e)}",
            )

    async def authenticate_stock_data(
        self, data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
    ) -> AuthResult:
        """
        Authenticate stock data from central API

        Args:
            data: Data to authenticate
            data_id: Unique data identifier
            context: Authentication context

        Returns:
            AuthResult: Authentication result
        """
        try:
            # Determine appropriate verifiers for stock data
            verifier_types = self._get_verifiers_for_data_source("stock_api")

            # Add stock API specific context
            stock_context = {
                **(context or {}),
                "data_source": "stock_api",
                "endpoint": "18.180.162.113:9191",
                "protocol": "http",  # SECURITY ISSUE: Unencrypted
                "security_risk": "HTTP_ONLY_UNENCRYPTED",
            }

            # Perform authentication
            result = await self.auth_manager.verify_data(
                data = data,
                data_id = data_id,
                data_type="stock_market_data",
                data_source="18.180.162.113",
                verifier_types = verifier_types,
                context = stock_context,
            )

            # Add security warning for HTTP usage
            if result.metadata:
                result.metadata["security_warning"] = "Stock API uses unencrypted HTTP"
                result.metadata["recommendation"] = (
                    "Upgrade to HTTPS for secure transmission"
                )

            # Log authentication attempt
            await self._log_authentication_attempt("stock_data", data_id, result)

            return result

        except Exception as e:
            logger.error(f"Stock data authentication failed: {e}")
            return AuthResult(
                data_id = data_id,
                overall_verdict = Verdict.ERROR,
                overall_confidence = 0.0,
                error_message = f"Stock authentication error: {str(e)}",
            )

    async def authenticate_api_request(
        self, request_info: Dict[str, Any], request_id: str
    ) -> AuthResult:
        """
        Authenticate API request for rate limiting and endpoint validation

        Args:
            request_info: Request information (endpoint, headers, etc.)
            request_id: Unique request identifier

        Returns:
            AuthResult: Authentication result
        """
        try:
            # Determine appropriate verifiers for API requests
            verifier_types = self._get_verifiers_for_data_source("api_request")

            # Add request - specific context
            request_context = {
                **request_info,
                "data_type": "api_request",
                "check_rate_limit": True,
                "check_endpoint_whitelist": True,
            }

            # Perform authentication
            result = await self.auth_manager.verify_data(
                data = request_info,
                data_id = request_id,
                data_type="api_request",
                data_source = request_info.get("endpoint", "unknown"),
                verifier_types = verifier_types,
                context = request_context,
            )

            # Log authentication attempt
            await self._log_authentication_attempt("api_request", request_id, result)

            return result

        except Exception as e:
            logger.error(f"API request authentication failed: {e}")
            return AuthResult(
                data_id = request_id,
                overall_verdict = Verdict.ERROR,
                overall_confidence = 0.0,
                error_message = f"API request authentication error: {str(e)}",
            )

    def _get_verifiers_for_data_source(self, data_source: str) -> List[str]:
        """Get appropriate verifiers for a data source"""
        integration_config = self.config.get("integration", {})
        data_source_mapping = integration_config.get("data_source_verifiers", {})

        return data_source_mapping.get(data_source, [])

    async def _log_authentication_attempt(
        self, auth_type: str, data_id: str, result: AuthResult
    ):
        """Log authentication attempt for audit trail"""
        try:
            audit_config = self.config.get("compliance", {})
            if audit_config.get("enable_audit_trail", True):
                audit_entry = {
                    "timestamp": time.time(),
                    "auth_type": auth_type,
                    "data_id": data_id,
                    "verdict": result.overall_verdict.value,
                    "confidence": result.overall_confidence,
                    "execution_time_ms": result.total_execution_time_ms,
                    "status": result.status.value,
                    "error_message": result.error_message,
                }

                # Log to file (in production, use proper audit logging system)
                logger.info(f"AUDIT: {json.dumps(audit_entry)}")

        except Exception as e:
            logger.error(f"Failed to log authentication attempt: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            health_status = {
                "phase2_authentication": {
                    "status": "healthy",
                    "enabled_verifiers": len(self.verifiers),
                    "timestamp": time.time(),
                },
                "verifiers": {},
            }

            # Check each verifier
            for verifier_name, verifier in self.verifiers.items():
                try:
                    verifier_health = await verifier.health_check()
                    health_status["verifiers"][verifier_name] = verifier_health

                    # Update overall status if any verifier is unhealthy
                    if verifier_health.get("status") != "healthy":
                        health_status["phase2_authentication"]["status"] = "degraded"

                except Exception as e:
                    health_status["verifiers"][verifier_name] = {
                        "status": "unhealthy",
                        "error": str(e),
                    }
                    health_status["phase2_authentication"]["status"] = "unhealthy"

            # Check authentication manager
            manager_health = await self.auth_manager.health_check()
            health_status["authentication_manager"] = manager_health

            return health_status

        except Exception as e:
            return {
                "phase2_authentication": {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": time.time(),
                }
            }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive authentication statistics"""
        try:
            statistics = {
                "phase2_statistics": {
                    "total_verifications": 0,
                    "authentic_count": 0,
                    "suspicious_count": 0,
                    "falsified_count": 0,
                    "error_count": 0,
                    "average_confidence": 0.0,
                    "average_execution_time_ms": 0.0,
                    "verifier_specific": {},
                }
            }

            # Get statistics from authentication manager
            manager_stats = self.auth_manager.get_statistics()
            statistics.update(manager_stats)

            # Get verifier - specific statistics
            for verifier_name, verifier in self.verifiers.items():
                if hasattr(verifier, "get_statistics"):
                    try:
                        verifier_stats = verifier.get_statistics()
                        statistics["phase2_statistics"]["verifier_specific"][
                            verifier_name
                        ] = verifier_stats
                    except Exception as e:
                        logger.error(
                            f"Failed to get statistics for {verifier_name}: {e}"
                        )

            return statistics

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    async def cleanup(self):
        """Cleanup all resources"""
        try:
            logger.info("Cleaning up Phase 2 Source Authentication")

            # Cleanup authentication manager
            await self.auth_manager.cleanup()

            # Cleanup individual verifiers
            for verifier in self.verifiers.values():
                if hasattr(verifier, "cleanup"):
                    try:
                        await verifier.cleanup()
                    except Exception as e:
                        logger.error(f"Error cleaning up verifier: {e}")

            self.verifiers.clear()
            logger.info("Phase 2 Source Authentication cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global instance for easy access
_phase2_auth_instance = None


def get_phase2_authentication(
    config_path: Optional[str] = None,
) -> Phase2SourceAuthentication:
    """Get or create Phase 2 authentication instance"""
    global _phase2_auth_instance
    if _phase2_auth_instance is None:
        _phase2_auth_instance = Phase2SourceAuthentication(config_path)
    return _phase2_auth_instance


# Convenience functions for common authentication tasks
async def authenticate_hkma_data(
    data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
) -> AuthResult:
    """Convenience function for HKMA data authentication"""
    auth = get_phase2_authentication()
    return await auth.authenticate_hkma_data(data, data_id, context)


async def authenticate_stock_data(
    data: Any, data_id: str, context: Optional[Dict[str, Any]] = None
) -> AuthResult:
    """Convenience function for stock data authentication"""
    auth = get_phase2_authentication()
    return await auth.authenticate_stock_data(data, data_id, context)


async def authenticate_api_request(
    request_info: Dict[str, Any], request_id: str
) -> AuthResult:
    """Convenience function for API request authentication"""
    auth = get_phase2_authentication()
    return await auth.authenticate_api_request(request_info, request_id)


if __name__ == "__main__":
    # Demo usage
    async def demo_phase2_authentication():
        print("🔐 Phase 2 Source Authentication Layer Demo")
        print("=" * 60)

        # Initialize authentication
        auth = Phase2SourceAuthentication()

        # Health check
        print("\n📊 Health Check:")
        health = await auth.health_check()
        print(json.dumps(health, indent = 2))

        # Test HKMA data authentication
        print("\n🏛️ HKMA Data Authentication Test:")
        hkma_data = {
            "source": "hkma.gov.hk",
            "hibor_rate": 3.15,
            "timestamp": "2024 - 01 - 01T12:00:00Z",
        }
        hkma_result = await auth.authenticate_hkma_data(hkma_data, "test_hkma_001")
        print(
            f"Result: {hkma_result.overall_verdict.value} (confidence: {hkma_result.overall_confidence:.3f})"
        )

        # Test stock data authentication
        print("\n📈 Stock Data Authentication Test:")
        stock_data = {
            "symbol": "0700.HK",
            "price": 450.50,
            "timestamp": "2024 - 01 - 01T12:00:00Z",
            "source": "18.180.162.113",
        }
        stock_result = await auth.authenticate_stock_data(stock_data, "test_stock_001")
        print(
            f"Result: {stock_result.overall_verdict.value} (confidence: {stock_result.overall_confidence:.3f})"
        )

        # Test API request authentication
        print("\n🌐 API Request Authentication Test:")
        request_info = {
            "endpoint": "api.hkma.gov.hk",
            "method": "GET",
            "user_agent": "TestClient / 1.0",
        }
        request_result = await auth.authenticate_api_request(
            request_info, "test_request_001"
        )
        print(
            f"Result: {request_result.overall_verdict.value} (confidence: {request_result.overall_confidence:.3f})"
        )

        # Statistics
        print("\n📈 Authentication Statistics:")
        stats = await auth.get_statistics()
        print(json.dumps(stats, indent = 2))

        # Cleanup
        await auth.cleanup()
        print("\n✅ Demo completed successfully!")

    # Run demo
    asyncio.run(demo_phase2_authentication())
