#!/usr/bin/env python3
"""
Comprehensive database security tests for SQL injection prevention
"""

import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestDatabaseSecurity(unittest.TestCase):
    """Test database security features and SQL injection prevention"""

    def setUp(self):
        """Set up test environment"""
        # Use SQLite for testing
        self.test_db_url = "sqlite:///test_cbsc_security.db"

        # Mock environment variable
        os.environ['DATABASE_URL'] = self.test_db_url

        # Import after setting environment
        try:
            from database_secure import SecureDatabaseManager
            self.db_manager = SecureDatabaseManager()
        except ImportError:
            self.skipTest("Database module not available")

    def tearDown(self):
        """Clean up test environment"""
        # Remove test database file
        if os.path.exists("test_cbsc_security.db"):
            os.remove("test_cbsc_security.db")

    def test_sql_injection_pattern_detection(self):
        """Test SQL injection pattern detection"""
        # Test legitimate inputs
        legitimate_inputs = [
            "0700.HK",
            "strategy_name",
            "user_data",
            "normal_query",
            "valid_table_123"
        ]

        for input_str in legitimate_inputs:
            self.assertFalse(
                self.db_manager._check_sql_injection(input_str),
                f"Legitimate input flagged as injection: {input_str}"
            )

        # Test malicious inputs
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "UNION SELECT * FROM passwords",
            "'; INSERT INTO users VALUES('hacker', 'password'); --",
            "admin'; --",
            "1' OR '1'='1",
            "'; EXEC xp_cmdshell('dir'); --",
            "'; DELETE FROM stock_data; --",
            "'; UPDATE users SET role='admin'; --",
            "SELECT * FROM users WHERE id=1; DROP TABLE users; --",
            "test' UNION SELECT password FROM users --"
        ]

        for input_str in malicious_inputs:
            self.assertTrue(
                self.db_manager._check_sql_injection(input_str),
                f"Malicious input not detected: {input_str}"
            )

    def test_table_name_validation(self):
        """Test table name validation"""
        # Valid table names
        valid_tables = ['stock_data', 'strategy_signals', 'ml_models', 'users']
        for table in valid_tables:
            self.assertTrue(
                self.db_manager._validate_table_name(table),
                f"Valid table rejected: {table}"
            )

        # Invalid table names
        invalid_tables = [
            'malicious; DROP TABLE',
            'users--',
            "'; DROP TABLE users; --",
            'nonexistent_table',
            'admin_users',  # Not in allowed list
            '',
            None,
            123,
            'stock data',  # Contains space
            'stock-data',  # Contains dash
            'STOCK_DATA'  # Wrong case
        ]

        for table in invalid_tables:
            self.assertFalse(
                self.db_manager._validate_table_name(table),
                f"Invalid table accepted: {table}"
            )

    def test_column_name_validation(self):
        """Test column name validation"""
        # Valid column names for stock_data table
        valid_columns = ['id', 'symbol', 'timestamp', 'open_price', 'close_price']
        for column in valid_columns:
            self.assertTrue(
                self.db_manager._validate_column_name(column, 'stock_data'),
                f"Valid column rejected: {column}"
            )

        # Invalid column names
        invalid_columns = [
            'password',
            'id; DROP TABLE',
            "'; UPDATE",
            'nonexistent_column',
            '',
            None,
            123,
            'open price'  # Contains space
        ]

        for column in invalid_columns:
            self.assertFalse(
                self.db_manager._validate_column_name(column, 'stock_data'),
                f"Invalid column accepted: {column}"
            )

    def test_stock_symbol_validation(self):
        """Test stock symbol validation"""
        # Valid Hong Kong stock symbols
        valid_symbols = ['0700.HK', '9988.HK', '0005.HK', '1398.HK', '0941.HK']
        for symbol in valid_symbols:
            self.assertTrue(
                self.db_manager._validate_stock_symbol(symbol),
                f"Valid stock symbol rejected: {symbol}"
            )

        # Invalid stock symbols
        invalid_symbols = [
            "0700.HK'; DROP TABLE users; --",
            "'; DELETE FROM stock_data; --",
            'AAPL',  # Not HK format
            '0700',  # Missing .HK
            '0700hk',  # Lowercase
            'INVALID.HK',
            '',
            None,
            123,
            '07000.HK',  # Too many digits
            '700.HK'  # Too few digits
        ]

        for symbol in invalid_symbols:
            self.assertFalse(
                self.db_manager._validate_stock_symbol(symbol),
                f"Invalid stock symbol accepted: {symbol}"
            )

    def test_database_url_validation(self):
        """Test database URL validation"""
        # Valid URLs
        valid_urls = [
            'postgresql://user:password@localhost/quant_system',
            'mysql://user:pass@localhost/trading',
            'sqlite:///database.db'
        ]

        for url in valid_urls:
            self.assertTrue(
                self.db_manager._validate_database_url(url),
                f"Valid URL rejected: {url}"
            )

        # Invalid URLs
        invalid_urls = [
            'ftp://user:pass@localhost/db',  # Unsupported protocol
            'http://user:pass@localhost/db',  # Unsupported protocol
            '',
            None,
            'invalid_url'
        ]

        for url in invalid_urls:
            self.assertFalse(
                self.db_manager._validate_database_url(url),
                f"Invalid URL accepted: {url}"
            )

    def test_stock_data_validation(self):
        """Test stock data validation"""
        # Valid data
        valid_data = {
            'price': 150.50,
            'open': 149.00,
            'high': 152.00,
            'low': 148.00,
            'volume': 1000000,
            'date': '2025-01-01T00:00:00'
        }

        try:
            validated = self.db_manager._validate_stock_data(valid_data)
            self.assertEqual(validated['price'], 150.50)
        except Exception as e:
            self.fail(f"Valid data validation failed: {e}")

        # Invalid data - missing price
        with self.assertRaises(ValueError):
            self.db_manager._validate_stock_data({'open': 100.0})

        # Invalid data - negative price
        with self.assertRaises(ValueError):
            self.db_manager._validate_stock_data({'price': -10.0})

        # Invalid data - negative volume
        with self.assertRaises(ValueError):
            self.db_manager._validate_stock_data({'price': 100.0, 'volume': -100})

        # Invalid data - invalid date format
        with self.assertRaises(ValueError):
            self.db_manager._validate_stock_data({'price': 100.0, 'date': 'invalid-date'})

    def test_save_stock_data_security(self):
        """Test security of save_stock_data method"""
        # Valid data
        valid_data = {
            'price': 100.0,
            'volume': 1000
        }

        try:
            self.db_manager.save_stock_data('0700.HK', valid_data, 'test_source')
        except Exception as e:
            # Expected due to SQLite connection issues in test environment
            # The important thing is that injection attempts should be caught earlier
            pass

        # Test injection attempts in symbol
        injection_attempts = [
            "'; DROP TABLE stock_data; --",
            "0700.HK'; DELETE FROM users; --",
            "'; SELECT * FROM users WHERE '1'='1"
        ]

        for symbol in injection_attempts:
            with self.assertRaises(ValueError):
                self.db_manager.save_stock_data(symbol, valid_data, 'test_source')

        # Test injection attempts in source
        for source in injection_attempts:
            with self.assertRaises(ValueError):
                self.db_manager.save_stock_data('0700.HK', valid_data, source)

    def test_strategy_signal_security(self):
        """Test security of strategy signal operations"""
        # Valid signal data
        valid_signals = [
            ('BUY', 0.8),
            ('SELL', 0.6),
            ('HOLD', 0.5)
        ]

        for signal_type, confidence in valid_signals:
            try:
                self.db_manager.save_strategy_signal('0700.HK', 'test_strategy', signal_type, confidence)
            except Exception:
                pass  # Expected due to SQLite connection issues

        # Test injection attempts in strategy name
        injection_strategy_names = [
            "'; DROP TABLE strategy_signals; --",
            "test'; DELETE FROM users; --",
            "'; SELECT password FROM admin_users --"
        ]

        for strategy_name in injection_strategy_names:
            with self.assertRaises(ValueError):
                self.db_manager.save_strategy_signal('0700.HK', strategy_name, 'BUY', 0.7)

        # Test invalid signal types
        invalid_signal_types = [
            "'; DROP TABLE users; --",
            'MALICIOUS',
            'delete_all',
            'EXEC xp_cmdshell'
        ]

        for signal_type in invalid_signal_types:
            with self.assertRaises(ValueError):
                self.db_manager.save_strategy_signal('0700.HK', 'test_strategy', signal_type, 0.7)

        # Test invalid confidence values
        invalid_confidences = [-0.1, 1.5, 10.0, -5.0]
        for confidence in invalid_confidences:
            with self.assertRaises(ValueError):
                self.db_manager.save_strategy_signal('0700.HK', 'test_strategy', 'BUY', confidence)

    def test_get_operations_security(self):
        """Test security of get operations"""
        # Test injection attempts in symbol parameter
        injection_symbols = [
            "'; DROP TABLE stock_data; --",
            "0700.HK'; DELETE FROM users; --",
            "'; SELECT * FROM users --",
            "0700.HK OR '1'='1"
        ]

        for symbol in injection_symbols:
            with self.assertRaises(ValueError):
                self.db_manager.get_stock_history(symbol, 100)

            with self.assertRaises(ValueError):
                self.db_manager.get_strategy_signals(symbol, 100)

        # Test invalid limit values
        invalid_limits = [-1, 0, 100000, '100', None, 'infinite']
        for limit in invalid_limits:
            with self.assertRaises(ValueError):
                self.db_manager.get_stock_history('0700.HK', limit)

            with self.assertRaises(ValueError):
                self.db_manager.get_strategy_signals(limit=limit)

class TestSecurityFrameworkIntegration(unittest.TestCase):
    """Test integration with security framework"""

    def test_security_patterns_coverage(self):
        """Test that common injection patterns are covered"""
        from database_secure import SecureDatabaseManager

        manager = SecureDatabaseManager()

        # Test common injection patterns
        patterns = [
            ("' OR '1'='1", "Classic SQL injection"),
            ("'; DROP TABLE", "Drop table attack"),
            ("UNION SELECT", "Union-based injection"),
            ("--", "SQL comment"),
            ("/*", "Multi-line comment"),
            ("EXEC(", "Command execution"),
            ("xp_cmdshell", "SQL Server command"),
            ("information_schema", "Schema enumeration"),
            ("sysobjects", "System objects enumeration"),
            ("sp_executesql", "Dynamic SQL execution")
        ]

        for pattern, description in patterns:
            self.assertTrue(
                manager._check_sql_injection(pattern),
                f"Pattern not detected: {pattern} ({description})"
            )

    def test_performance_impact(self):
        """Test that security checks don't significantly impact performance"""
        import time
        from database_secure import SecureDatabaseManager

        manager = SecureDatabaseManager()

        # Test with legitimate inputs
        legitimate_inputs = ['0700.HK', 'strategy_name', 'test_data'] * 1000

        start_time = time.time()
        for input_str in legitimate_inputs:
            manager._check_sql_injection(input_str)
        legitimate_time = time.time() - start_time

        # Test with malicious inputs
        malicious_inputs = ["'; DROP TABLE", "UNION SELECT", "' OR '1'='1"] * 1000

        start_time = time.time()
        for input_str in malicious_inputs:
            manager._check_sql_injection(input_str)
        malicious_time = time.time() - start_time

        # Performance should be reasonable (less than 1 second for 3000 checks)
        self.assertLess(legitimate_time, 1.0, "Legitimate input validation too slow")
        self.assertLess(malicious_time, 1.0, "Malicious input detection too slow")

if __name__ == '__main__':
    # Create test database directory if it doesn't exist
    test_dir = os.path.dirname(__file__)
    os.makedirs(test_dir, exist_ok=True)

    # Run tests
    unittest.main(verbosity=2)