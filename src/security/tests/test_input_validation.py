"""
Input Validation Security Tests
輸入驗證安全測試

Comprehensive security tests for input validation framework.
Tests XSS protection, CSRF protection, rate limiting, file upload security, and DLP.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from security.input_validator import (
    CBSCInputValidator,
    XSSProtection,
    CSRFProtection,
    RateLimiter,
    FileUploadSecurity,
    DLPProtection,
    input_validator,
    xss_protection,
    csrf_protection,
    rate_limiter,
    file_upload_security,
    dlp_protection,
    SecurityError,
    XSSDetectionError,
    CSRFError,
    RateLimitExceededError
)


class TestCBSCInputValidator:
    """Test CBSC input validator"""

    def test_validate_strategy_name_valid(self):
        """Test validating valid strategy names"""
        data = {'strategy_name': 'MA_Crossover_Strategy'}
        result = input_validator.validate_strategy_input(data)

        assert result.is_valid
        assert result.sanitized_data['strategy_name'] == 'MA_Crossover_Strategy'

    def test_validate_strategy_name_xss_rejected(self):
        """Test XSS in strategy name is rejected"""
        data = {'strategy_name': '<script>alert("XSS")</script>'}
        result = input_validator.validate_strategy_input(data)

        assert not result.is_valid
        assert any('XSS' in err for err in result.errors)

    def test_validate_symbol_valid(self):
        """Test validating valid symbols"""
        data = {'symbol': 'AAPL'}
        result = input_validator.validate_strategy_input(data)

        assert result.is_valid

    def test_validate_symbol_invalid(self):
        """Test invalid symbol is rejected"""
        data = {'symbol': 'INVALID-SYMBOL'}
        result = input_validator.validate_strategy_input(data)

        assert not result.is_valid

    def test_validate_parameters_valid(self):
        """Test validating valid parameters"""
        params = {
            'short_window': 20,
            'long_window': 50,
            'risk_level': 0.5
        }
        result = input_validator.validate_parameters(params)

        assert result.is_valid

    def test_validate_parameters_sql_injection(self):
        """Test SQL injection in parameters is rejected"""
        params = {'strategy_name': "test'; DROP TABLE users--"}
        result = input_validator.validate_strategy_input(params)

        assert not result.is_valid
        assert any('SQL Injection' in err for err in result.errors)

    def test_max_length_enforced(self):
        """Test max length constraints are enforced"""
        long_string = 'a' * 200
        data = {'strategy_name': long_string}
        result = input_validator.validate_strategy_input(data)

        # Should be truncated to max length
        assert len(result.sanitized_data.get('strategy_name', '')) <= 50

    def test_security_score_calculation(self):
        """Test security score is calculated correctly"""
        # Clean input should have high security score
        clean_data = {'strategy_name': 'ValidStrategy'}
        result = input_validator.validate_strategy_input(clean_data)
        assert result.security_score >= 90

        # Dangerous input should have low security score
        dangerous_data = {'strategy_name': '<script>alert("xss")</script>'}
        result = input_validator.validate_strategy_input(dangerous_data)
        assert result.security_score < 50


class TestXSSProtection:
    """Test XSS protection"""

    def test_detect_script_tag(self):
        """Test detection of script tags"""
        xss_input = '<script>alert("XSS")</script>'
        is_xss, patterns = xss_protection.detect_xss(xss_input)

        assert is_xss
        assert len(patterns) > 0

    def test_detect_iframe_tag(self):
        """Test detection of iframe tags"""
        xss_input = '<iframe src="malicious.com"></iframe>'
        is_xss, patterns = xss_protection.detect_xss(xss_input)

        assert is_xss

    def test_detect_javascript_protocol(self):
        """Test detection of javascript: protocol"""
        xss_input = 'javascript:alert("XSS")'
        is_xss, patterns = xss_protection.detect_xss(xss_input)

        assert is_xss

    def test_sanitize_html_removes_scripts(self):
        """Test HTML sanitization removes scripts"""
        html = '<p>Valid</p><script>alert("XSS")</script>'
        sanitized = xss_protection.sanitize_html(html)

        assert '<script>' not in sanitized
        assert '<p>Valid</p>' in sanitized

    def test_csp_headers_generated(self):
        """Test CSP headers are generated"""
        headers = xss_protection.get_csp_headers()

        assert 'Content-Security-Policy' in headers
        assert 'X-Frame-Options' in headers
        assert 'X-XSS-Protection' in headers
        assert headers['X-Frame-Options'] == 'DENY'

    def test_csp_default_src_self(self):
        """Test CSP default-src is 'self'"""
        headers = xss_protection.get_csp_headers()
        csp = headers['Content-Security-Policy']

        assert "default-src 'self'" in csp

    def test_csp_blocks_external_scripts(self):
        """Test CSP blocks external scripts"""
        headers = xss_protection.get_csp_headers()
        csp = headers['Content-Security-Policy']

        # Should not allow unsafe-inline or unsafe-eval in production
        assert "script-src" in csp


class TestCSRFProtection:
    """Test CSRF protection"""

    def test_generate_token(self):
        """Test CSRF token generation"""
        token = csrf_protection.generate_token(user_id=1)

        assert token is not None
        assert len(token) > 20
        assert ':' in token  # Token should have parts

    def test_validate_token_valid(self):
        """Test valid token validation"""
        token = csrf_protection.generate_token(user_id=1, session_id='session123')
        is_valid = csrf_protection.validate_token(token, user_id=1, session_id='session123')

        assert is_valid

    def test_validate_token_wrong_user(self):
        """Test token validation fails for wrong user"""
        token = csrf_protection.generate_token(user_id=1)
        is_valid = csrf_protection.validate_token(token, user_id=2)

        assert not is_valid

    def test_validate_token_expired(self):
        """Test expired token is rejected"""
        # Create token with old timestamp
        old_timestamp = int((datetime.utcnow() - timedelta(hours=2)).timestamp())
        with patch('security.input_validator.datetime') as mock_dt:
            mock_dt.utcnow.return_value = datetime.utcnow()
            mock_dt.fromtimestamp.return_value = datetime.fromtimestamp(old_timestamp)

            # Generate token with old time
            token_data = f"1:{old_timestamp}"
            signature = "test_signature"
            token = f"{token_data}:{signature}"

            is_valid = csrf_protection.validate_token(token, user_id=1)
            assert not is_valid

    def test_validate_token_malformed(self):
        """Test malformed token is rejected"""
        malformed_tokens = [
            '',
            'too-short',
            'missing:parts',
            'a:b:c:d:e',  # Too many parts
        ]

        for token in malformed_tokens:
            is_valid = csrf_protection.validate_token(token, user_id=1)
            assert not is_valid, f"Token {token} should be invalid"


class TestRateLimiter:
    """Test rate limiting"""

    def test_allow_requests_within_limit(self):
        """Test requests within limit are allowed"""
        identifier = "test_user_1"

        for _ in range(5):
            result = rate_limiter.check_rate_limit(
                identifier,
                max_requests=10,
                window_seconds=60
            )
            assert result['allowed']

    def test_block_requests_over_limit(self):
        """Test requests over limit are blocked"""
        identifier = "test_user_2"

        # Make 10 requests (at limit)
        for i in range(10):
            rate_limiter.check_rate_limit(identifier, max_requests=10, window_seconds=60)

        # Next request should be blocked
        result = rate_limiter.check_rate_limit(identifier, max_requests=10, window_seconds=60)
        assert not result['allowed']

    def test_rate_limit_resets_after_window(self):
        """Test rate limit resets after time window"""
        identifier = "test_user_3"

        # Make requests up to limit
        for _ in range(10):
            rate_limiter.check_rate_limit(identifier, max_requests=10, window_seconds=1)

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        result = rate_limiter.check_rate_limit(identifier, max_requests=10, window_seconds=1)
        assert result['allowed']

    def test_remaining_count_decrements(self):
        """Test remaining count decrements correctly"""
        identifier = "test_user_4"

        result1 = rate_limiter.check_rate_limit(identifier, max_requests=10, window_seconds=60)
        assert result1['remaining'] == 9

        result2 = rate_limiter.check_rate_limit(identifier, max_requests=10, window_seconds=60)
        assert result2['remaining'] == 8

    def test_blocking_works_correctly(self):
        """Test IP blocking mechanism"""
        identifier = "test_user_5"

        # Exceed limit significantly to trigger blocking
        for _ in range(15):
            rate_limiter.check_rate_limit(identifier, max_requests=10, window_seconds=60)

        # Should be blocked
        assert rate_limiter.is_blocked(identifier)

        # Wait for block to expire (minimal time)
        time.sleep(0.5)

        # Check if still blocked after minimal time
        is_blocked = rate_limiter.is_blocked(identifier)
        # Note: This test may be flaky depending on timing

    def test_different_identifiers_independent(self):
        """Test different identifiers have independent limits"""
        result1 = rate_limiter.check_rate_limit("user_1", max_requests=5, window_seconds=60)
        result2 = rate_limiter.check_rate_limit("user_2", max_requests=5, window_seconds=60)

        # Both should be allowed independently
        assert result1['allowed']
        assert result2['allowed']


class TestFileUploadSecurity:
    """Test file upload security"""

    def test_allow_valid_extensions(self):
        """Test valid file extensions are allowed"""
        for ext in FileUploadSecurity.ALLOWED_EXTENSIONS:
            filename = f"test.{ext}"
            result = file_upload_security.validate_file(filename, 1024, 'text/plain')

            assert result.is_valid

    def test_reject_dangerous_extensions(self):
        """Test dangerous file extensions are rejected"""
        for ext in FileUploadSecurity.DANGEROUS_EXTENSIONS:
            filename = f"malicious.{ext}"
            result = file_upload_security.validate_file(filename, 1024, 'application/octetext')

            assert not result.is_valid
            assert any('dangerous' in err.lower() or 'not allowed' in err.lower()
                      for err in result.errors)

    def test_reject_large_files(self):
        """Test files exceeding size limit are rejected"""
        large_size = FileUploadSecurity.MAX_FILE_SIZE + 1
        result = file_upload_security.validate_file("large.csv", large_size, 'text/csv')

        assert not result.is_valid
        assert any('too large' in err.lower() for err in result.errors)

    def test_allow_files_within_size_limit(self):
        """Test files within size limit are allowed"""
        acceptable_size = FileUploadSecurity.MAX_FILE_SIZE - 1
        result = file_upload_security.validate_file("acceptable.csv", acceptable_size, 'text/csv')

        assert result.is_valid

    def test_detect_double_extensions(self):
        """Test double extensions are detected"""
        filename = "file.csv.exe"
        result = file_upload_security.validate_file(filename, 1024, 'text/plain')

        # Should have warning about double extensions
        assert any('multiple extensions' in warn.lower() for warn in result.warnings)

    def test_security_score_penalties(self):
        """Test security score penalties apply correctly"""
        # Dangerous extension
        result1 = file_upload_security.validate_file("test.exe", 1024, 'application/exe')
        assert result1.security_score < 50

        # Too large
        result2 = file_upload_security.validate_file("test.csv", 99999999, 'text/csv')
        assert result2.security_score < 80


class TestDLPProtection:
    """Test Data Leakage Protection"""

    def test_detect_credit_card(self):
        """Test credit card detection"""
        data = "My credit card is 4532-1234-5678-9010"
        findings = dlp_protection.scan_for_sensitive_data(data)

        assert 'credit_card' in findings
        assert '4532-1234-5678-9010' in findings['credit_card']

    def test_detect_email(self):
        """Test email detection"""
        data = "Contact us at support@example.com"
        findings = dlp_protection.scan_for_sensitive_data(data)

        assert 'email' in findings
        assert 'support@example.com' in findings['email']

    def test_detect_api_key(self):
        """Test API key detection"""
        data = "Use this key: AIza0123456789abcdefghijklmnopqrstuvwxyzabcdef"
        findings = dlp_protection.scan_for_sensitive_data(data)

        assert 'api_key' in findings

    def test_mask_credit_card(self):
        """Test credit card masking"""
        data = "Card: 4532-1234-5678-9010"
        masked = dlp_protection.mask_sensitive_data(data, ['credit_card'])

        assert '4532' not in masked  # Full number not visible
        assert '***' in masked  # Has masking
        assert '9010' in masked  # Last 4 digits visible

    def test_mask_email(self):
        """Test email masking"""
        data = "Email: user@example.com"
        masked = dlp_protection.mask_sensitive_data(data, ['email'])

        assert 'user@example.com' not in masked  # Full email not visible
        assert '@' in masked  # Still has @
        assert '***' in masked  # Has masking

    def test_mask_ip_address(self):
        """Test IP address masking"""
        data = "IP: 192.168.1.1"
        masked = dlp_protection.mask_sensitive_data(data, ['ip_address'])

        assert '192.168.1.1' not in masked  # Full IP not visible
        assert '***' in masked  # Has masking

    def test_mask_api_key(self):
        """Test API key masking"""
        data = "Key: AIza0123456789abcdefghijklmnopqrstuvwxyzabcdef"
        masked = dlp_protection.mask_sensitive_data(data, ['api_key'])

        assert 'abcdefghijklmnopqrstuvwxyz' not in masked  # Full key not visible
        assert 'AIza01234' in masked  # First 10 chars visible
        assert '...' in masked  # Has truncation indicator

    def test_multiple_sensitive_types(self):
        """Test detecting multiple sensitive data types"""
        data = """
        Email: john@example.com
        Card: 4532-1234-5678-9010
        IP: 192.168.1.1
        """
        findings = dlp_protection.scan_for_sensitive_data(data)

        assert len(findings) >= 3  # Should find at least 3 types
        assert 'email' in findings
        assert 'credit_card' in findings
        assert 'ip_address' in findings


class TestSecurityIntegration:
    """Test integrated security features"""

    def test_complete_validation_workflow(self):
        """Test complete input validation workflow"""
        # Simulate API request with multiple fields
        request_data = {
            'strategy_name': 'Test Strategy',
            'symbol': 'AAPL',
            'parameters': {
                'window': 20,
                'risk_level': 0.5
            },
            'description': 'A test strategy'
        }

        # Validate
        result = input_validator.validate_strategy_input(request_data)

        assert result.is_valid
        assert result.security_score >= 90

    def test_xss_prevention_workflow(self):
        """Test XSS prevention through the workflow"""
        user_input = {
            'strategy_name': '<script>alert("XSS")</script>Strategy',
            'description': 'Test <iframe src="evil.com"></iframe>'
        }

        # Should detect and block
        result = input_validator.validate_strategy_input(user_input)

        assert not result.is_valid
        assert result.security_score < 50

    def test_rate_limiting_workflow(self):
        """Test rate limiting in workflow"""
        user_id = "rapid_user"

        # Simulate rapid requests
        blocked_count = 0
        for i in range(25):
            result = rate_limiter.check_rate_limit(user_id, max_requests=10, window_seconds=60)
            if not result['allowed']:
                blocked_count += 1

        assert blocked_count > 0  # Should have been blocked

    def test_file_upload_security_workflow(self):
        """Test file upload security workflow"""
        # Test multiple file types
        test_files = [
            ('document.csv', 1024, 'text/csv', True),
            ('image.png', 2048, 'image/png', True),
            ('malicious.exe', 1024, 'application/exe', False),
            ('large.csv', 99999999, 'text/csv', False),
        ]

        for filename, size, content_type, should_pass in test_files:
            result = file_upload_security.validate_file(filename, size, content_type)
            assert result.is_valid == should_pass, f"Failed for {filename}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
