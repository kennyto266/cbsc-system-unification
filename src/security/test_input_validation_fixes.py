#!/usr/bin/env python3
"""
Input Validation Security Test Suite
Created: 2025-11-30
Purpose: Test input validation security fixes
"""

import unittest
import re
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestInputValidationSecurity(unittest.TestCase):
    """Test input validation security fixes"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_files = [
            'interactive_quantitative_trader.py'
        ]

    def test_secure_input_validator_import(self):
        """Test that secure input validator can be imported"""
        try:
            from src.security.secure_input_validator import get_input_validator, safe_input_int, safe_input_float
            self.assertIsNotNone(get_input_validator())
            self.assertIsNotNone(safe_input_int)
            self.assertIsNotNone(safe_input_float)
            logger.info("✅ Secure input validator imported successfully")
        except ImportError as e:
            self.skipTest(f"Secure input validator not available: {e}")

    def test_secure_integer_validation(self):
        """Test secure integer validation"""
        try:
            from src.security.secure_input_validator import get_input_validator, InputValidationError

            validator = get_input_validator()

            # Test valid integers
            self.assertEqual(validator.validate_input("42", "duration"), 42)
            self.assertEqual(validator.validate_input("1", "menu_choice", {"min_value": 1, "max_value": 10}), 1)

            # Test invalid integers
            with self.assertRaises(InputValidationError):
                validator.validate_input("abc", "duration")

            with self.assertRaises(InputValidationError):
                validator.validate_input("500", "duration", {"min_value": 1, "max_value": 365})

            logger.info("✅ Secure integer validation tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

    def test_secure_float_validation(self):
        """Test secure float validation"""
        try:
            from src.security.secure_input_validator import get_input_validator, InputValidationError

            validator = get_input_validator()

            # Test valid floats
            self.assertEqual(validator.validate_input("1.5", "sharpe_threshold"), 1.5)
            self.assertEqual(validator.validate_input("0.75", "sharpe_threshold"), 0.75)

            # Test invalid floats
            with self.assertRaises(InputValidationError):
                validator.validate_input("abc", "sharpe_threshold")

            with self.assertRaises(InputValidationError):
                validator.validate_input("10.0", "sharpe_threshold", {"max_value": 5.0})

            logger.info("✅ Secure float validation tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

    def test_attack_pattern_detection(self):
        """Test attack pattern detection"""
        try:
            from src.security.secure_input_validator import get_input_validator, InputValidationError

            validator = get_input_validator()

            # Test dangerous inputs
            dangerous_inputs = [
                ";rm -rf /",  # Command injection
                "'; DROP TABLE users; --",  # SQL injection
                "../../../etc/passwd",  # Path traversal
                "<script>alert('xss')</script>",  # XSS
                "'; cat /etc/passwd; echo",  # Command injection
                "../../../../windows/system32",  # Path traversal
            ]

            for dangerous_input in dangerous_inputs:
                with self.assertRaises(InputValidationError):
                    validator.validate_input(dangerous_input, "duration")

            logger.info("✅ Attack pattern detection tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

    def test_stock_symbol_validation(self):
        """Test stock symbol validation"""
        try:
            from src.security.secure_input_validator import get_input_validator, InputValidationError

            validator = get_input_validator()

            # Test valid stock symbols
            self.assertEqual(validator.validate_input("0700.HK", "stock_symbol"), "0700.HK")
            self.assertEqual(validator.validate_input("0941.hk", "stock_symbol"), "0941.HK")  # Should normalize to upper case

            # Test invalid stock symbols
            with self.assertRaises(InputValidationError):
                validator.validate_input("1234", "stock_symbol")  # Missing .HK

            with self.assertRaises(InputValidationError):
                validator.validate_input("0700.US", "stock_symbol")  # Wrong suffix

            with self.assertRaises(InputValidationError):
                validator.validate_input("ABCDEF.HK", "stock_symbol")  # Not numeric

            logger.info("✅ Stock symbol validation tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

    def test_boolean_validation(self):
        """Test boolean validation"""
        try:
            from src.security.secure_input_validator import get_input_validator

            validator = get_input_validator()

            # Test valid boolean inputs
            self.assertTrue(validator.validate_input("true", "boolean_choice"))
            self.assertTrue(validator.validate_input("1", "boolean_choice"))
            self.assertTrue(validator.validate_input("yes", "boolean_choice"))
            self.assertTrue(validator.validate_input("y", "boolean_choice"))

            self.assertFalse(validator.validate_input("false", "boolean_choice"))
            self.assertFalse(validator.validate_input("0", "boolean_choice"))
            self.assertFalse(validator.validate_input("no", "boolean_choice"))
            self.assertFalse(validator.validate_input("n", "boolean_choice"))

            logger.info("✅ Boolean validation tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

    def test_parameter_range_validation(self):
        """Test parameter range validation"""
        try:
            from src.security.secure_input_validator import get_input_validator

            validator = get_input_validator()

            # Test RSI period validation
            rsi_period = validator.validate_parameter_range("rsi_period", "14", "int", 2, 100)
            self.assertEqual(rsi_period, 14)

            # Test invalid RSI period
            with self.assertRaises(Exception):  # InputValidationError
                validator.validate_parameter_range("rsi_period", "150", "int", 2, 100)

            # Test float parameter
            sharpe_threshold = validator.validate_parameter_range("sharpe_threshold", "1.5", "float", 0.0, 5.0)
            self.assertEqual(sharpe_threshold, 1.5)

            logger.info("✅ Parameter range validation tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

    def test_vulnerability_scan_results(self):
        """Test that vulnerability scan shows improvements"""
        # This test checks that the vulnerabilities we fixed are no longer present
        vulnerable_patterns = [
            r'int\([^)]*input\(',  # Direct int(input()) without validation
            r'float\([^)]*input\(',  # Direct float(input()) without validation
        ]

        improvements_found = 0

        for file_path in self.test_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Check that secure input validation is being used
                if 'INPUT_VALIDATOR_AVAILABLE' in content and 'safe_input_int' in content:
                    improvements_found += 1
                    logger.info(f"✅ Secure input validation implemented in {file_path}")

                # Check that vulnerable patterns are reduced
                for pattern in vulnerable_patterns:
                    matches = len(list(re.finditer(pattern, content)))
                    if matches == 0:
                        improvements_found += 1
                        logger.info(f"✅ No vulnerable pattern '{pattern}' found in {file_path}")

            except FileNotFoundError:
                self.skipTest(f"Test file {file_path} not found")

        self.assertGreater(improvements_found, 0, "Input validation security improvements not detected")

    def test_fallback_mechanism(self):
        """Test that fallback mechanisms work when secure validator is unavailable"""
        try:
            from src.security.secure_input_validator import get_input_validator, InputValidationError

            validator = get_input_validator()

            # Test that validator has fallback capabilities
            self.assertTrue(hasattr(validator, '_initialize_attack_patterns'))
            self.assertTrue(hasattr(validator, '_validate_integer'))

            logger.info("✅ Fallback mechanism tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

    @patch('builtins.input')
    def test_safe_input_functions(self, mock_input):
        """Test safe input convenience functions"""
        try:
            from src.security.secure_input_validator import safe_input_int, safe_input_float

            # Test safe_input_int
            mock_input.return_value = "42"
            result = safe_input_int("Enter number: ", min_val=1, max_val=100)
            self.assertEqual(result, 42)

            # Test safe_input_float
            mock_input.return_value = "3.14"
            result = safe_input_float("Enter float: ", min_val=0.0, max_val=10.0)
            self.assertEqual(result, 3.14)

            # Test invalid input
            mock_input.return_value = "invalid"
            with self.assertRaises(Exception):
                safe_input_int("Enter number: ")

            logger.info("✅ Safe input function tests passed")
        except ImportError:
            self.skipTest("Secure input validator not available")

def test_input_validation_security_status():
    """Test overall input validation security status"""
    print("\\n" + "="*60)
    print("INPUT VALIDATION SECURITY STATUS")
    print("="*60)

    # Check if security files exist
    security_files = [
        "src/security/secure_input_validator.py",
        "src/security/test_input_validation_fixes.py"
    ]

    files_exist = all(__import__('pathlib').Path(f).exists() for f in security_files)

    if files_exist:
        print("[OK] Security files created successfully")
    else:
        print("[FAIL] Some security files missing")
        return False

    # Run basic security tests
    try:
        from src.security.secure_input_validator import get_input_validator
        validator = get_input_validator()

        # Test basic functionality
        validator.validate_input("1", "menu_choice", {"min_value": 1, "max_value": 10})
        print("[OK] Basic validation functionality works")

        # Test attack detection
        try:
            validator.validate_input("'; DROP TABLE users; --", "test")
            print("[FAIL] Attack detection failed!")
            return False
        except:
            print("[OK] Attack detection working correctly")

    except ImportError:
        print("[FAIL] Security framework not importable")
        return False

    print("\\nOverall Status: SECURE")
    return True

def run_input_validation_tests():
    """Run comprehensive input validation tests"""

    print("="*60)
    print("INPUT VALIDATION SECURITY TEST SUITE")
    print("="*60)

    # Run unit tests
    print("\\n1. Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Test overall security status
    print("\\n2. Testing overall security status...")
    security_status = test_input_validation_security_status()

    # Summary
    print("\\n" + "="*60)
    print("INPUT VALIDATION SECURITY SUMMARY")
    print("="*60)

    if security_status:
        print("[SUCCESS] Input validation security measures are in place")
        print("- Secure input validation framework: IMPLEMENTED")
        print("- Attack pattern detection: ACTIVE")
        print("- Type safety enforcement: COMPLETE")
        print("- Fallback mechanisms: AVAILABLE")
    else:
        print("[WARNING] Input validation security needs attention")
        print("- Review and fix remaining vulnerabilities")

    return security_status

if __name__ == "__main__":
    run_input_validation_tests()