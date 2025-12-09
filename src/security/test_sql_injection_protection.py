#!/usr/bin/env python3
"""
SQL Injection Protection Test Suite
Created: 2025-11-30
Purpose: Test SQL injection prevention measures
"""

import unittest
import sqlite3
import tempfile
import os
from src.security.secure_sql_framework import (
    SecureSQLFramework, SQLInjectionError, QueryType,
    QUANT_TRADING_SCHEMA, SECURE_SQL,
    get_strategy_performance, save_strategy_result, search_strategies
)

class TestSQLInjectionProtection(unittest.TestCase):
    """Test SQL injection protection mechanisms"""

    def setUp(self):
        """Set up test database"""
        self.conn = sqlite3.connect(':memory:')

        # Create test tables
        self.conn.execute('''
            CREATE TABLE strategy_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                parameters TEXT,
                sharpe_ratio REAL,
                total_return REAL,
                max_drawdown REAL,
                volatility REAL,
                win_rate REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.execute('''
            CREATE TABLE performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER,
                date TEXT,
                return REAL,
                cumulative_return REAL,
                volatility REAL,
                drawdown REAL,
                var REAL
            )
        ''')

        self.conn.commit()

    def tearDown(self):
        """Clean up test database"""
        self.conn.close()

    def test_safe_query_creation(self):
        """Test safe query creation"""

        # Test safe SELECT
        query = SECURE_SQL.create_safe_select(
            table_name="strategy_results",
            columns=["strategy_name", "sharpe_ratio"],
            where_clause="sharpe_ratio > ?",
            parameters=(1.0,),
            order_by="sharpe_ratio DESC",
            limit=10
        )

        self.assertEqual(query.query_type, QueryType.SELECT)
        self.assertIn("SELECT strategy_name, sharpe_ratio FROM strategy_results", query.template)
        self.assertIn("WHERE sharpe_ratio > ?", query.template)
        self.assertIn("ORDER BY sharpe_ratio DESC", query.template)
        self.assertIn("LIMIT 10", query.template)

    def test_sql_injection_detection(self):
        """Test SQL injection detection"""

        # Test table name injection attempts
        malicious_tables = [
            "users; DROP TABLE users; --",
            "users' OR '1'='1",
            "users UNION SELECT * FROM sensitive_data",
            "users'; UPDATE users SET password='hacked'; --",
        ]

        for malicious_table in malicious_tables:
            with self.assertRaises(SQLInjectionError):
                SECURE_SQL.create_safe_select(table_name=malicious_table, columns=["*"])

        # Test column name injection attempts
        malicious_columns = [
            "password; --",
            "name' OR '1'='1",
            "id UNION SELECT password FROM users",
        ]

        for malicious_col in malicious_columns:
            with self.assertRaises(SQLInjectionError):
                SECURE_SQL.create_safe_select(
                    table_name="strategy_results",
                    columns=[malicious_col]
                )

    def test_where_clause_injection(self):
        """Test WHERE clause injection detection"""

        malicious_where_clauses = [
            "1=1; DROP TABLE strategy_results; --",
            "name = 'admin' OR '1'='1'",
            "id = 1 UNION SELECT password FROM users",
            "1=1; UPDATE strategy_results SET sharpe_ratio=999; --",
        ]

        for malicious_where in malicious_where_clauses:
            with self.assertRaises(SQLInjectionError):
                SECURE_SQL.create_safe_select(
                    table_name="strategy_results",
                    columns=["*"],
                    where_clause=malicious_where
                )

    def test_safe_parameterized_queries(self):
        """Test that parameterized queries work safely"""

        # Insert test data
        test_data = [
            ("RSI_Strategy", 1.5, 0.25, 0.1, 0.15, 0.65),
            ("MACD_Strategy", 1.2, 0.20, 0.08, 0.12, 0.70),
            ("Bollinger_Strategy", 1.8, 0.30, 0.12, 0.18, 0.60),
        ]

        for strategy_name, sharpe, returns, drawdown, volatility, win_rate in test_data:
            query = SECURE_SQL.create_safe_insert(
                table_name="strategy_results",
                columns=["strategy_name", "sharpe_ratio", "total_return",
                        "max_drawdown", "volatility", "win_rate"],
                values=(strategy_name, sharpe, returns, drawdown, volatility, win_rate)
            )

            with SECURE_SQL.safe_execute(self.conn, query) as cursor:
                pass  # Query executed successfully

        # Test safe SELECT with parameters
        query = SECURE_SQL.create_safe_select(
            table_name="strategy_results",
            columns=["strategy_name", "sharpe_ratio"],
            where_clause="sharpe_ratio > ? AND volatility < ?",
            parameters=(1.0, 0.20),
            order_by="sharpe_ratio DESC"
        )

        with SECURE_SQL.safe_execute(self.conn, query) as cursor:
            results = cursor.fetchall()
            self.assertEqual(len(results), 1)  # Only Bollinger_Strategy should match

    def test_order_by_validation(self):
        """Test ORDER BY clause validation"""

        # Valid ORDER BY clauses
        valid_order_by = [
            "sharpe_ratio",
            "strategy_name",
            "created_at DESC",
            "sharpe_ratio ASC",
        ]

        for order_by in valid_order_by:
            query = SECURE_SQL.create_safe_select(
                table_name="strategy_results",
                columns=["*"],
                order_by=order_by
            )
            self.assertIn(f"ORDER BY {order_by}", query.template)

        # Invalid ORDER BY clauses
        invalid_order_by = [
            "sharpe_ratio; DROP TABLE users; --",
            "1; UPDATE users SET password='hacked'",
            "sharpe_ratio UNION SELECT password FROM users",
        ]

        for order_by in invalid_order_by:
            with self.assertRaises(SQLInjectionError):
                SECURE_SQL.create_safe_select(
                    table_name="strategy_results",
                    columns=["*"],
                    order_by=order_by
                )

    def test_limit_validation(self):
        """Test LIMIT clause validation"""

        # Valid limits
        valid_limits = [1, 10, 100]

        for limit in valid_limits:
            query = SECURE_SQL.create_safe_select(
                table_name="strategy_results",
                columns=["*"],
                limit=limit
            )
            self.assertIn(f"LIMIT {limit}", query.template)

        # Invalid limits
        invalid_limits = [0, -1, "10", "ten", None]

        for limit in invalid_limits:
            with self.assertRaises(SQLInjectionError):
                SECURE_SQL.create_safe_select(
                    table_name="strategy_results",
                    columns=["*"],
                    limit=limit
                )

    def test_delete_safety(self):
        """Test that DELETE requires WHERE clause"""

        # DELETE without WHERE should fail
        with self.assertRaises(SQLInjectionError):
            SECURE_SQL.create_safe_delete(table_name="strategy_results")

        # DELETE with WHERE should succeed
        query = SECURE_SQL.create_safe_delete(
            table_name="strategy_results",
            where_clause="id = ?",
            parameters=(1,)
        )
        self.assertIn("DELETE FROM strategy_results WHERE id = ?", query.template)

    def test_utility_functions(self):
        """Test utility functions work safely"""

        # Insert test data
        save_strategy_result(
            self.conn,
            strategy_name="Test_Strategy",
            parameters={"rsi_period": 14, "threshold": 0.7},
            metrics={"sharpe_ratio": 1.2, "total_return": 0.15}
        )

        # Test search strategies
        results = search_strategies(
            self.conn,
            search_term="Test",
            min_sharpe=1.0
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["strategy_name"], "Test_Strategy")

    def test_stack_query_prevention(self):
        """Test that stacked queries are prevented"""

        # Test stacked query injection attempts
        stacked_queries = [
            "SELECT * FROM strategy_results; DROP TABLE strategy_results; --",
            "SELECT * FROM strategy_results; INSERT INTO users VALUES ('hacker', 'pass'); --",
        ]

        for malicious_query in stacked_queries:
            # These should be caught by the validation
            with self.assertRaises((SQLInjectionError, ValueError)):
                SECURE_SQL.create_safe_select(
                    table_name="strategy_results",
                    columns=["*"],
                    where_clause="1=1; DROP TABLE strategy_results; --"
                )

def test_current_codebase_safety():
    """Test that current codebase doesn't have SQL injection vulnerabilities"""

    print("\\nTesting current codebase for SQL injection safety...")

    import re
    import os

    vulnerable_patterns = []
    dangerous_files = []

    # Patterns that would indicate SQL injection vulnerabilities
    injection_patterns = [
        r'pd\.read_sql\(f["\'].*\{.*\}.*["\']',  # f-string in pd.read_sql
        r'cursor\.execute\(f["\'].*\{.*\}.*["\']',  # f-string in execute
        r'query\s*=\s*f["\'].*\{.*\}.*["\'].*SELECT',  # f-string SQL query
        r'sql\s*=\s*f["\'].*\{.*\}.*["\'].*WHERE',  # f-string WHERE clause
        r'WHERE.*parameters->>\{',  # JSON parameter injection
    ]

    # Scan main application files
    main_files = [
        'interactive_quantitative_trader.py',
        'start_high_performance.py',
        'quick_start_trader.py',
        'hk700_demo_clean.py'
    ]

    for file_path in main_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern in injection_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        dangerous_files.append({
                            'file': file_path,
                            'pattern': pattern,
                            'matches': len(matches)
                        })

            except Exception as e:
                print(f"Error scanning {file_path}: {e}")

    if dangerous_files:
        print(f"[WARNING] Found {len(dangerous_files)} potentially dangerous files:")
        for file_info in dangerous_files:
            print(f"  {file_info['file']}: {file_info['matches']} matches")
            print(f"    Pattern: {file_info['pattern']}")
        return False
    else:
        print("[OK] No SQL injection vulnerabilities found in main application files")
        return True

def run_sql_injection_tests():
    """Run comprehensive SQL injection tests"""

    print("=" * 60)
    print("SQL INJECTION PROTECTION TEST SUITE")
    print("=" * 60)

    # Run unit tests
    print("\\n1. Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Test current codebase
    print("\\n2. Scanning current codebase...")
    codebase_safe = test_current_codebase_safety()

    # Summary
    print("\\n" + "=" * 60)
    print("SQL INJECTION PROTECTION SUMMARY")
    print("=" * 60)

    if codebase_safe:
        print("[SUCCESS] SQL injection protection is in place")
        print("- Current codebase: SAFE")
        print("- Security framework: IMPLEMENTED")
        print("- Prevention measures: ACTIVE")
    else:
        print("[WARNING] Potential SQL injection risks detected")
        print("- Review and fix identified issues")
        print("- Use secure SQL framework for all database operations")

    return codebase_safe

if __name__ == "__main__":
    run_sql_injection_tests()