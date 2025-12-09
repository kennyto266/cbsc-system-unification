#!/usr/bin/env python3
"""
Basic Security Test Script
Tests the core security fixes without special characters
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_syntax_fix():
    """Test that the syntax error in utils.py has been fixed"""
    logger.info("Testing syntax fix in tests/framework/utils.py")

    try:
        # Test compilation of the previously problematic file
        utils_path = project_root / "tests" / "framework" / "utils.py"

        if not utils_path.exists():
            logger.warning("tests/framework/utils.py not found")
            return False

        # Try to compile the file
        with open(utils_path, 'r', encoding='utf-8') as f:
            content = f.read()

        compile(content, str(utils_path), 'exec')
        logger.info("PASS: Syntax error fix verified")
        return True

    except SyntaxError as e:
        logger.error(f"FAIL: Syntax error still exists: {e}")
        return False
    except Exception as e:
        logger.error(f"FAIL: Error testing syntax fix: {e}")
        return False


def test_security_validator():
    """Test the SecurityValidator class"""
    logger.info("Testing SecurityValidator")

    try:
        # Import our security fixes
        sys.path.insert(0, str(project_root / "src"))
        from security.security_fixes import SecurityValidator

        # Test stock symbol validation
        valid_symbol = SecurityValidator.validate_stock_symbol("0700.HK")
        assert valid_symbol == "0700.HK", f"Expected '0700.HK', got {valid_symbol}"

        # Test SQL injection protection
        try:
            SecurityValidator.sanitize_sql_input("'; DROP TABLE users; --")
            logger.error("FAIL: SQL injection protection not working")
            return False
        except ValueError:
            pass  # Expected

        # Test filename validation
        try:
            SecurityValidator.validate_filename("../../../etc/passwd")
            logger.error("FAIL: Path traversal protection not working")
            return False
        except ValueError:
            pass  # Expected

        # Test numeric input validation
        valid_value = SecurityValidator.validate_numeric_input(0.5, min_val=0, max_val=1)
        assert valid_value == 0.5, f"Expected 0.5, got {valid_value}"

        try:
            SecurityValidator.validate_numeric_input(2, min_val=0, max_val=1)
            logger.error("FAIL: Numeric range validation not working")
            return False
        except ValueError:
            pass  # Expected

        logger.info("PASS: SecurityValidator tests passed")
        return True

    except ImportError as e:
        logger.error(f"FAIL: Failed to import SecurityValidator: {e}")
        return False
    except Exception as e:
        logger.error(f"FAIL: Error testing SecurityValidator: {e}")
        return False


def test_sharpe_calculator():
    """Test the standardized Sharpe calculator"""
    logger.info("Testing Sharpe Calculator")

    try:
        # Test import of the Sharpe calculator
        calculator_path = project_root / "simplified_system" / "src" / "backtest" / "standardized_sharpe_calculator.py"

        if not calculator_path.exists():
            logger.warning("Standardized Sharpe calculator not found")
            return False

        # Add to path and import
        sys.path.insert(0, str(project_root / "simplified_system"))
        from src.backtest.standardized_sharpe_calculator import StandardizedSharpeCalculator

        import numpy as np

        # Test with sample data
        np.random.seed(42)
        test_returns = np.random.normal(0.001, 0.02, 252)

        calculator = StandardizedSharpeCalculator()
        result = calculator.calculate_sharpe_ratio(test_returns, 'standard')

        # Validate results
        if not isinstance(result, dict) or 'sharpe_ratio' not in result:
            logger.error("FAIL: Sharpe calculator returning invalid format")
            return False

        sharpe = result['sharpe_ratio']
        if abs(sharpe) > 10:  # Unrealistic Sharpe ratio
            logger.error(f"FAIL: Unrealistic Sharpe ratio: {sharpe}")
            return False

        # Test risk-free rate and trading days
        assert calculator.risk_free_rate == 0.03, f"Expected 0.03, got {calculator.risk_free_rate}"
        assert calculator.trading_days == 252, f"Expected 252, got {calculator.trading_days}"

        logger.info(f"PASS: Sharpe Calculator tests passed (Sharpe: {sharpe:.3f})")
        return True

    except ImportError as e:
        logger.error(f"FAIL: Failed to import Sharpe calculator: {e}")
        return False
    except Exception as e:
        logger.error(f"FAIL: Error testing Sharpe calculator: {e}")
        return False


def test_security_config():
    """Test the security configuration"""
    logger.info("Testing Security Configuration")

    try:
        sys.path.insert(0, str(project_root / "src"))
        from security.security_config import SecurityConfig, validate_environment

        # Test environment validation
        env_validation = validate_environment()

        # Check if we have required environment variables
        if not env_validation['valid']:
            logger.warning(f"Environment validation warnings: {env_validation['missing_required']}")

        # Test password validation
        is_strong, issues = SecurityConfig.is_password_strong("weak")
        assert not is_strong, "Weak password should not pass validation"

        is_strong, issues = SecurityConfig.is_password_strong("StrongPassword123!")
        assert is_strong, "Strong password should pass validation"

        # Test encryption key generation
        key = SecurityConfig.get_encryption_key()
        assert len(key) > 0, "Encryption key should not be empty"

        logger.info("PASS: Security Configuration tests passed")
        return True

    except ImportError as e:
        logger.error(f"FAIL: Failed to import SecurityConfig: {e}")
        return False
    except Exception as e:
        logger.error(f"FAIL: Error testing Security Configuration: {e}")
        return False


def main():
    """Main test function"""
    print("Basic Security Test for Quantitative Trading System")
    print("=" * 60)

    tests = [
        ("Syntax Fix", test_syntax_fix),
        ("Security Validator", test_security_validator),
        ("Sharpe Calculator", test_sharpe_calculator),
        ("Security Configuration", test_security_config)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"FAIL: {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll security tests passed!")
        print("The system security fixes are working correctly.")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed.")
        print("Please review the errors above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())