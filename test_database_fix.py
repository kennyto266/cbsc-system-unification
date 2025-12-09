#!/usr/bin/env python3
"""
Test script to verify the database.py security fixes
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database_import():
    """Test that database module can be imported without syntax errors"""
    try:
        from database import SecureDatabaseManager, db_manager
        print("Database module imported successfully")
        return True
    except SyntaxError as e:
        print(f"Syntax error in database.py: {e}")
        return False
    except ImportError as e:
        print(f"Import error in database.py: {e}")
        return False
    except Exception as e:
        print(f"Other error in database.py: {e}")
        return False

def test_database_manager_initialization():
    """Test that SecureDatabaseManager can be initialized"""
    try:
        from database import SecureDatabaseManager

        # Mock environment variable for testing
        os.environ['DATABASE_URL'] = 'sqlite:///test.db'

        manager = SecureDatabaseManager()
        print("SecureDatabaseManager initialized successfully")

        # Test validation methods
        assert manager._validate_stock_symbol('0700.HK') == True
        assert manager._validate_stock_symbol('INVALID') == False
        print("Stock symbol validation working correctly")

        return True
    except Exception as e:
        print(f"Database manager initialization failed: {e}")
        return False

def test_secure_sql_framework():
    """Test that the secure SQL framework is properly integrated"""
    try:
        from database import SecureDatabaseManager

        os.environ['DATABASE_URL'] = 'sqlite:///test.db'
        manager = SecureDatabaseManager()

        # Test table validation
        assert manager.secure_sql.validate_table_name('stock_data') == True
        assert manager.secure_sql.validate_table_name('malicious; DROP TABLE') == False
        print("SQL injection protection working correctly")

        return True
    except Exception as e:
        print(f"Secure SQL framework test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing CBSC Database Security Fixes")
    print("=" * 50)

    tests = [
        test_database_import,
        test_database_manager_initialization,
        test_secure_sql_framework
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        print(f"\nRunning {test.__name__}...")
        if test():
            passed += 1
        else:
            print(f"{test.__name__} failed")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed! Database security fixes are working correctly.")
        return 0
    else:
        print("Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)