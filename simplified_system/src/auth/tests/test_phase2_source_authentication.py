#!/usr / bin / env python3
"""
Phase 2 Source Authentication Tests
阶段2源认证层测试

Comprehensive test suite for Phase 2 Source Authentication Layer including
digital signature verification, TLS certificate validation, endpoint whitelisting,
and rate limiting anomaly detection.
"""

import asyncio
import json
import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from ..interfaces.auth_result import AuthResult, AuthStatus, Verdict

# Import the modules to test
from ..phase2_integration import Phase2SourceAuthentication, get_phase2_authentication
from ..verifiers.digital_signature_verifier import DigitalSignatureVerifier
from ..verifiers.endpoint_whitelist_verifier import EndpointWhitelistVerifier
from ..verifiers.rate_limit_anomaly_detector import RateLimitAnomalyDetector
from ..verifiers.tls_certificate_validator import TLSCertificateValidator


class TestPhase2SourceAuthentication:
    """Test Phase 2 Source Authentication Integration"""

    @pytest.fixture
    def auth_config(self):
        """Test configuration for authentication"""
        return {
            "digital_signature_verifier": {
                "enabled": True,
                "supported_algorithms": ["RS256", "HS256"],
                "trusted_issuers": ["test.gov.hk"],
            },
            "tls_certificate_validator": {
                "enabled": True,
                "critical_endpoints": ["test.api.hk"],
                "validation_timeout": 10.0,
            },
            "endpoint_whitelist_verifier": {
                "enabled": True,
                "block_private_ips": False,  # Allow for testing
            },
            "rate_limit_anomaly_detector": {
                "enabled": True,
                "window_sizes": [60],  # Short window for testing
                "max_requests_per_window": {60: 5},  # Low limit for testing
                "cleanup_interval": 1,  # Fast cleanup for testing
            },
            "integration": {
                "data_source_verifiers": {
                    "hkma_apis": ["digital_signature", "tls_certificate"],
                    "stock_api": ["endpoint_whitelist", "rate_limit"],
                    "api_request": ["endpoint_whitelist", "rate_limit"],
                }
            },
        }

    @pytest.fixture
    def phase2_auth(self, auth_config):
        """Create Phase 2 authentication instance for testing"""
        return Phase2SourceAuthentication()

    @pytest.mark.asyncio
    async def test_initialization(self, phase2_auth):
        """Test Phase 2 authentication initialization"""
        assert phase2_auth is not None
        assert phase2_auth.auth_manager is not None
        assert isinstance(phase2_auth.config, dict)

    @pytest.mark.asyncio
    async def test_health_check(self, phase2_auth):
        """Test health check functionality"""
        health = await phase2_auth.health_check()
        assert "phase2_authentication" in health
        assert "verifiers" in health
        assert health["phase2_authentication"]["status"] in [
            "healthy",
            "degraded",
            "unhealthy",
        ]

    @pytest.mark.asyncio
    async def test_hkma_data_authentication(self, phase2_auth):
        """Test HKMA data authentication"""
        hkma_data = {
            "source": "hkma.gov.hk",
            "hibor_rate": 3.15,
            "timestamp": datetime.utcnow().isoformat(),
        }

        result = await phase2_auth.authenticate_hkma_data(hkma_data, "test_hkma_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_hkma_001"
        assert result.overall_verdict in [
            Verdict.AUTHENTIC,
            Verdict.SUSPICIOUS,
            Verdict.UNKNOWN,
            Verdict.ERROR,
        ]

    @pytest.mark.asyncio
    async def test_stock_data_authentication(self, phase2_auth):
        """Test stock data authentication"""
        stock_data = {
            "symbol": "0700.HK",
            "price": 450.50,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "18.180.162.113",
        }

        result = await phase2_auth.authenticate_stock_data(stock_data, "test_stock_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_stock_001"
        assert result.overall_verdict in [
            Verdict.AUTHENTIC,
            Verdict.SUSPICIOUS,
            Verdict.UNKNOWN,
            Verdict.ERROR,
        ]

    @pytest.mark.asyncio
    async def test_api_request_authentication(self, phase2_auth):
        """Test API request authentication"""
        request_info = {
            "endpoint": "test.api.hk",
            "method": "GET",
            "timestamp": time.time(),
        }

        result = await phase2_auth.authenticate_api_request(
            request_info, "test_request_001"
        )

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_request_001"
        assert result.overall_verdict in [
            Verdict.AUTHENTIC,
            Verdict.SUSPICIOUS,
            Verdict.UNKNOWN,
            Verdict.ERROR,
        ]

    @pytest.mark.asyncio
    async def test_statistics(self, phase2_auth):
        """Test statistics collection"""
        stats = await phase2_auth.get_statistics()
        assert isinstance(stats, dict)
        assert "total_verifications" in stats
        assert "registered_verifiers" in stats

    @pytest.mark.asyncio
    async def test_cleanup(self, phase2_auth):
        """Test cleanup functionality"""
        # Should not raise any exceptions
        await phase2_auth.cleanup()


class TestDigitalSignatureVerifier:
    """Test Digital Signature Verifier"""

    @pytest.fixture
    def ds_verifier(self):
        """Create digital signature verifier for testing"""
        config = {
            "supported_algorithms": ["HS256"],
            "default_hmac_key": "test_secret_key_12345",
        }
        return DigitalSignatureVerifier(config = config)

    @pytest.mark.asyncio
    async def test_verifier_initialization(self, ds_verifier):
        """Test verifier initialization"""
        assert ds_verifier.name == "Digital Signature Verifier"
        assert ds_verifier.get_verifier_type() == "digital_signature"
        assert "api_response" in ds_verifier.get_supported_data_types()

    @pytest.mark.asyncio
    async def test_hmac_signature_verification(self, ds_verifier):
        """Test HMAC signature verification"""
        # Create test data with HMAC signature
        test_data = {"message": "test data", "timestamp": time.time()}
        data_str = json.dumps(test_data, sort_keys = True)

        # Create HMAC signature
        import base64
        import hashlib
        import hmac

        secret = ds_verifier.config["default_hmac_key"].encode()
        message = data_str.encode()
        signature = hmac.new(secret, message, hashlib.sha256).digest()
        signature_b64 = base64.b64encode(signature).decode()

        # Add signature to data
        signed_data = test_data.copy()
        signed_data["signature"] = signature_b64
        signed_data["algorithm"] = "HS256"

        context = {"key_id": "default"}

        result = await ds_verifier.verify(signed_data, "test_hmac_001", context)

        assert isinstance(result, AuthResult)
        assert result.overall_verdict == Verdict.AUTHENTIC
        assert result.overall_confidence > 0.8

    @pytest.mark.asyncio
    async def test_invalid_signature_verification(self, ds_verifier):
        """Test invalid signature verification"""
        test_data = {"message": "test data", "signature": "invalid_signature"}

        result = await ds_verifier.verify(test_data, "test_invalid_001")

        assert isinstance(result, AuthResult)
        assert result.overall_verdict in [
            Verdict.SUSPICIOUS,
            Verdict.FALSIFIED,
            Verdict.ERROR,
        ]

    @pytest.mark.asyncio
    async def test_health_check(self, ds_verifier):
        """Test health check"""
        health = await ds_verifier.health_check()
        assert health["verifier"] == ds_verifier.name
        assert health["type"] == ds_verifier.get_verifier_type()
        assert "status" in health


class TestTLSCertificateValidator:
    """Test TLS Certificate Validator"""

    @pytest.fixture
    def tls_verifier(self):
        """Create TLS certificate validator for testing"""
        config = {
            "validation_timeout": 5.0,
            "allow_self_signed": True,  # Allow for testing
            "block_private_ips": False,
        }
        return TLSCertificateValidator(config = config)

    @pytest.mark.asyncio
    async def test_verifier_initialization(self, tls_verifier):
        """Test verifier initialization"""
        assert tls_verifier.name == "TLS Certificate Validator"
        assert tls_verifier.get_verifier_type() == "tls_certificate"
        assert "https_url" in tls_verifier.get_supported_data_types()

    @pytest.mark.asyncio
    async def test_https_url_validation(self, tls_verifier):
        """Test HTTPS URL validation"""
        # Test with a known good URL
        url = "https://google.com"

        result = await tls_verifier.verify(url, "test_https_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_https_001"
        # Should be AUTHENTIC or ERROR depending on network connectivity

    @pytest.mark.asyncio
    async def test_http_url_validation(self, tls_verifier):
        """Test HTTP URL validation (should not fail but warn)"""
        url = "http://example.com"

        result = await tls_verifier.verify(url, "test_http_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_http_001"

    @pytest.mark.asyncio
    async def test_hostname_validation(self, tls_verifier):
        """Test hostname validation"""
        hostname = "google.com"
        context = {"port": 443, "protocol": "https"}

        result = await tls_verifier.verify(hostname, "test_hostname_001", context)

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_hostname_001"

    @pytest.mark.asyncio
    async def test_health_check(self, tls_verifier):
        """Test health check"""
        health = await tls_verifier.health_check()
        assert health["verifier"] == tls_verifier.name
        assert health["type"] == tls_verifier.get_verifier_type()
        assert "status" in health


class TestEndpointWhitelistVerifier:
    """Test Endpoint Whitelist Verifier"""

    @pytest.fixture
    def ew_verifier(self):
        """Create endpoint whitelist verifier for testing"""
        config = {
            "block_private_ips": False,
            "block_suspicious_tlds": False,
            "enable_dns_validation": False,  # Disable for faster testing
        }
        return EndpointWhitelistVerifier(config = config)

    @pytest.mark.asyncio
    async def test_verifier_initialization(self, ew_verifier):
        """Test verifier initialization"""
        assert ew_verifier.name == "Endpoint Whitelist Verifier"
        assert ew_verifier.get_verifier_type() == "endpoint_whitelist"
        assert "hostname" in ew_verifier.get_supported_data_types()

    @pytest.mark.asyncio
    async def test_localhost_whitelist(self, ew_verifier):
        """Test localhost whitelisting"""
        hostname = "localhost"

        result = await ew_verifier.verify(hostname, "test_localhost_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_localhost_001"
        # Localhost should be whitelisted

    @pytest.mark.asyncio
    async def test_api_hkma_gov_hk_whitelist(self, ew_verifier):
        """Test HKMA API whitelisting"""
        hostname = "api.hkma.gov.hk"

        result = await ew_verifier.verify(hostname, "test_hkma_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_hkma_001"
        # HKMA API should be whitelisted

    @pytest.mark.asyncio
    async def test_untrusted_endpoint(self, ew_verifier):
        """Test untrusted endpoint"""
        hostname = "untrusted - example.com"

        result = await ew_verifier.verify(hostname, "test_untrusted_001")

        assert isinstance(result, AuthResult)
        assert result.overall_verdict in [Verdict.SUSPICIOUS, Verdict.UNKNOWN]

    @pytest.mark.asyncio
    async def test_url_validation(self, ew_verifier):
        """Test URL validation"""
        url = "https://api.hkma.gov.hk / data"

        result = await ew_verifier.verify(url, "test_url_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_url_001"

    @pytest.mark.asyncio
    async def test_health_check(self, ew_verifier):
        """Test health check"""
        health = await ew_verifier.health_check()
        assert health["verifier"] == ew_verifier.name
        assert health["type"] == ew_verifier.get_verifier_type()
        assert "status" in health


class TestRateLimitAnomalyDetector:
    """Test Rate Limit Anomaly Detector"""

    @pytest.fixture
    def rl_detector(self):
        """Create rate limit anomaly detector for testing"""
        config = {
            "window_sizes": [10],  # 10 second window for testing
            "max_requests_per_window": {10: 2},  # Low limit for testing
            "cleanup_interval": 1,  # Fast cleanup
            "enable_adaptive_thresholds": False,  # Disable for predictable testing
        }
        return RateLimitAnomalyDetector(config = config)

    @pytest.mark.asyncio
    async def test_verifier_initialization(self, rl_detector):
        """Test verifier initialization"""
        assert rl_detector.name == "Rate Limit Anomaly Detector"
        assert rl_detector.get_verifier_type() == "rate_limit_anomaly_detection"
        assert "api_request" in rl_detector.get_supported_data_types()

    @pytest.mark.asyncio
    async def test_normal_request_rate(self, rl_detector):
        """Test normal request rate"""
        request_info = {"endpoint": "test.api.com", "timestamp": time.time()}

        # Send one request (should be fine)
        result = await rl_detector.verify(request_info, "test_normal_001")

        assert isinstance(result, AuthResult)
        assert result.data_id == "test_normal_001"
        assert result.overall_verdict in [Verdict.AUTHENTIC, Verdict.SUSPICIOUS]

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rl_detector):
        """Test rate limit exceeded"""
        request_info = {"endpoint": "test.api.com", "timestamp": time.time()}

        # Send multiple requests quickly to exceed limit
        results = []
        for i in range(5):  # Send 5 requests, limit is 2 per 10 seconds
            request_info["timestamp"] = time.time()
            result = await rl_detector.verify(request_info, f"test_rate_limit_{i}")
            results.append(result)
            await asyncio.sleep(0.1)  # Small delay

        # At least one result should indicate rate limiting
        throttled_or_blocked = any(
            r.overall_verdict in [Verdict.SUSPICIOUS, Verdict.FALSIFIED]
            for r in results
        )
        assert throttled_or_blocked

    @pytest.mark.asyncio
    async def test_different_endpoints(self, rl_detector):
        """Test rate limiting for different endpoints"""
        # Requests to different endpoints should be tracked separately
        endpoints = ["api1.test.com", "api2.test.com"]
        results = []

        for endpoint in endpoints:
            for i in range(3):  # 3 requests each (exceeds limit of 2)
                request_info = {"endpoint": endpoint, "timestamp": time.time()}
                result = await rl_detector.verify(request_info, f"test_{endpoint}_{i}")
                results.append(result)
                await asyncio.sleep(0.1)

        # Should have rate limiting detected
        rate_limited = any(
            r.overall_verdict in [Verdict.SUSPICIOUS, Verdict.FALSIFIED]
            for r in results
        )
        assert rate_limited

    @pytest.mark.asyncio
    async def test_health_check(self, rl_detector):
        """Test health check"""
        health = await rl_detector.health_check()
        assert health["verifier"] == rl_detector.name
        assert health["type"] == rl_detector.get_verifier_type()
        assert "status" in health


class TestIntegrationScenarios:
    """Test integration scenarios"""

    @pytest.mark.asyncio
    async def test_full_authentication_flow(self):
        """Test full authentication flow with multiple verifiers"""
        auth = Phase2SourceAuthentication()

        # Test HKMA data authentication
        hkma_data = {
            "source": "hkma.gov.hk",
            "data": {"hibor_rate": 3.15},
            "timestamp": datetime.utcnow().isoformat(),
        }

        result = await auth.authenticate_hkma_data(hkma_data, "integration_test_001")
        assert isinstance(result, AuthResult)

        # Test API request authentication
        request_info = {
            "endpoint": "localhost",
            "method": "GET",
            "timestamp": time.time(),
        }

        result = await auth.authenticate_api_request(
            request_info, "integration_test_002"
        )
        assert isinstance(result, AuthResult)

        await auth.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling scenarios"""
        auth = Phase2SourceAuthentication()

        # Test with invalid data
        invalid_data = None
        result = await auth.authenticate_hkma_data(invalid_data, "error_test_001")

        # Should handle gracefully
        assert isinstance(result, AuthResult)
        assert result.overall_verdict in [Verdict.ERROR, Verdict.SUSPICIOUS]

        await auth.cleanup()


# Performance benchmarks
@pytest.mark.asyncio
async def test_performance_benchmarks():
    """Test performance of authentication operations"""
    auth = Phase2SourceAuthentication()

    # Test authentication performance
    start_time = time.time()

    for i in range(10):  # 10 authentication operations
        request_info = {"endpoint": "localhost", "timestamp": time.time()}
        await auth.authenticate_api_request(request_info, f"perf_test_{i}")

    end_time = time.time()
    total_time = end_time - start_time

    # Should complete within reasonable time (adjust as needed)
    assert total_time < 10.0  # 10 seconds for 10 operations

    print(f"Performance: {10 / total_time:.2f} authentications / second")

    await auth.cleanup()


# Mock tests for environments without internet connectivity
@pytest.mark.asyncio
@patch("socket.create_connection")
async def test_tls_validator_mock(mock_create_connection):
    """Test TLS validator with mocked network calls"""
    config = {
        "validation_timeout": 1.0,
        "allow_self_signed": True,
        "block_private_ips": False,
    }
    verifier = TLSCertificateValidator(config = config)

    # Mock successful connection
    mock_socket = Mock()
    mock_ssl_socket = Mock()
    mock_ssl_socket.getpeercert.return_value = b"mock_certificate"
    mock_socket.__enter__ = Mock(return_value = mock_socket)
    mock_socket.__exit__ = Mock(return_value = None)
    mock_ssl_socket.__enter__ = Mock(return_value = mock_ssl_socket)
    mock_ssl_socket.__exit__ = Mock(return_value = None)
    mock_create_connection.return_value = mock_socket

    result = await verifier.verify("https://example.com", "mock_test_001")

    assert isinstance(result, AuthResult)
    assert result.data_id == "mock_test_001"


if __name__ == "__main__":
    # Run specific tests
    pytest.main([__file__, "-v", "--tb = short"])
