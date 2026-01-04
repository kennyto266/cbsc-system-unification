"""
Unit Tests for Enhanced Secure SQL Framework
安全 SQL 查詢框架單元測試

測試 SQL 注入防護機制
"""

import unittest
import pytest
from datetime import datetime
from src.security.secure_sql_framework_v2 import (
    EnhancedSecureSQLFramework,
    AdvancedInjectionDetector,
    CBSCQueryValidator,
    SecurityError,
    SQLOperationType,
    get_secure_framework
)


class TestAdvancedInjectionDetector(unittest.TestCase):
    """測試高級 SQL 注入檢測器"""

    def setUp(self):
        """設置測試環境"""
        self.detector = AdvancedInjectionDetector()

    def test_detect_sql_comment_injection(self):
        """測試檢測 SQL 註釋注入"""
        malicious_inputs = [
            "admin'--",
            "test'--",
            "user' /* comment */",
            "data'*/",
        ]

        for input_str in malicious_inputs:
            with self.subTest(input=input_str):
                self.assertTrue(
                    self.detector.detect(input_str),
                    f"Should detect injection in: {input_str}"
                )

    def test_detect_union_select_injection(self):
        """測試檢測 UNION SELECT 注入"""
        malicious_inputs = [
            "1' UNION SELECT * FROM users--",
            "admin' UNION SELECT password FROM users--",
            "' OR 1=1 UNION SELECT * FROM users--",
        ]

        for input_str in malicious_inputs:
            with self.subTest(input=input_str):
                self.assertTrue(
                    self.detector.detect(input_str),
                    f"Should detect UNION injection in: {input_str}"
                )

    def test_detect_drop_table_injection(self):
        """測試檢測 DROP TABLE 注入"""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "data'; DROP TABLE strategy_signals; --",
            "'; DROP TABLE *; --",
        ]

        for input_str in malicious_inputs:
            with self.subTest(input=input_str):
                self.assertTrue(
                    self.detector.detect(input_str),
                    f"Should detect DROP TABLE injection in: {input_str}"
                )

    def test_detect_time_based_blind_injection(self):
        """測試檢測基於時間的盲注"""
        malicious_inputs = [
            "1'; WAITFOR DELAY '00:00:10'--",
            "admin'; SLEEP(10)--",
            "'; BENCHMARK(1000000, MD5(1))--",
        ]

        for input_str in malicious_inputs:
            with self.subTest(input=input_str):
                self.assertTrue(
                    self.detector.detect(input_str),
                    f"Should detect time-based injection in: {input_str}"
                )

    def test_detect_system_table_access(self):
        """測試檢測系統表訪問"""
        malicious_inputs = [
            "'; SELECT * FROM information_schema.tables--",
            "' UNION SELECT * FROM sysobjects--",
            "' UNION SELECT * FROM syscolumns--",
        ]

        for input_str in malicious_inputs:
            with self.subTest(input=input_str):
                self.assertTrue(
                    self.detector.detect(input_str),
                    f"Should detect system table access in: {input_str}"
                )

    def test_safe_inputs_pass_detection(self):
        """測試安全輸入通過檢測"""
        safe_inputs = [
            "john.doe@example.com",
            "strategy_signal_2025_01",
            "user_12345",
            "normal-data-value",
            "table_name_20250125",
        ]

        for input_str in safe_inputs:
            with self.subTest(input=input_str):
                self.assertFalse(
                    self.detector.detect(input_str),
                    f"Safe input should pass: {input_str}"
                )

    def test_scan_query_with_injection(self):
        """測試掃描包含注入的查詢"""
        malicious_query = "SELECT * FROM users WHERE username = 'admin' UNION SELECT * FROM passwords--"
        result = self.detector.scan_query(malicious_query)

        self.assertFalse(result['is_safe'])
        self.assertEqual(result['risk_level'], 'HIGH')
        self.assertTrue(len(result['detected_patterns']) > 0)
        self.assertTrue(len(result['recommendations']) > 0)

    def test_scan_safe_query(self):
        """測試掃描安全查詢"""
        safe_query = "SELECT * FROM users WHERE id = %s AND status = %s"
        result = self.detector.scan_query(safe_query)

        self.assertTrue(result['is_safe'])
        self.assertEqual(result['risk_level'], 'LOW')


class TestEnhancedSecureSQLFramework(unittest.TestCase):
    """測試增強版安全 SQL 框架"""

    def setUp(self):
        """設置測試環境"""
        self.framework = EnhancedSecureSQLFramework()

    def test_validate_allowed_table_name(self):
        """測試驗證允許的表名"""
        allowed_tables = [
            'strategy_results',
            'cbsc_sentiment_data',
            'user_strategies',
            'users',
            'audit_logs',
        ]

        for table in allowed_tables:
            with self.subTest(table=table):
                self.assertTrue(
                    self.framework.validate_table_name(table),
                    f"Table should be valid: {table}"
                )

    def test_validate_invalid_table_name(self):
        """測試驗證無效表名拋出異常"""
        invalid_tables = [
            "'; DROP TABLE users; --",
            "malicious_table'; --",
            "users; DROP TABLE *; --",
            "unknown_table",
        ]

        for table in invalid_tables:
            with self.subTest(table=table):
                with self.assertRaises(SecurityError):
                    self.framework.validate_table_name(table)

    def test_validate_partition_table_name(self):
        """測試驗證分區表名"""
        valid_partitions = [
            'strategy_signals_2025_01',
            'stock_data_2025_02',
            'backtest_results_20250125',
        ]

        for partition in valid_partitions:
            with self.subTest(partition=partition):
                self.assertTrue(
                    self.framework.validate_table_name(partition),
                    f"Partition should be valid: {partition}"
                )

    def test_validate_invalid_partition_name(self):
        """測試驗證無效分區名"""
        invalid_partitions = [
            'strategy_signals_injected; DROP TABLE--',
            'data_25_25_25',  # Invalid format
            'table malicious_suffix',
        ]

        for partition in invalid_partitions:
            with self.subTest(partition=partition):
                with self.assertRaises(SecurityError):
                    self.framework.validate_table_name(partition)

    def test_validate_allowed_column_name(self):
        """測試驗證允許的列名"""
        self.framework.validate_column_name('users', 'username')
        self.framework.validate_column_name('users', 'email')
        self.framework.validate_column_name('strategy_results', 'sharpe_ratio')

    def test_validate_invalid_column_name(self):
        """測試驗證無效列名拋出異常"""
        with self.assertRaises(SecurityError):
            self.framework.validate_column_name('users', 'password'; DROP TABLE--')

        with self.assertRaises(SecurityError):
            self.framework.validate_column_name('users', 'nonexistent_column')

    def test_validate_input_with_injection(self):
        """測試檢測注入輸入"""
        malicious_inputs = [
            "admin' OR '1'='1",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users--",
        ]

        for value in malicious_inputs:
            with self.subTest(value=value):
                with self.assertRaises(SecurityError):
                    self.framework.validate_input(value)

    def test_validate_safe_input(self):
        """測試驗證安全輸入"""
        safe_inputs = [
            "normal_value",
            "user@example.com",
            123,
            45.67,
            True,
        ]

        for value in safe_inputs:
            with self.subTest(value=value):
                self.assertTrue(self.framework.validate_input(value))

    def test_validate_input_with_rules(self):
        """測試根據規則驗證輸入"""
        # Test bull_bear_ratio validation (min: 0, max: 10)
        self.framework.validate_input(5.0, 'bull_bear_ratio', 'cbsc_sentiment_data')
        self.framework.validate_input(0.0, 'bull_bear_ratio', 'cbsc_sentiment_data')
        self.framework.validate_input(10.0, 'bull_bear_ratio', 'cbsc_sentiment_data')

        # Test out of range
        with self.assertRaises(SecurityError):
            self.framework.validate_input(15.0, 'bull_bear_ratio', 'cbsc_sentiment_data')

        with self.assertRaises(SecurityError):
            self.framework.validate_input(-1.0, 'bull_bear_ratio', 'cbsc_sentiment_data')

        # Test sentiment_score validation (min: -1, max: 1)
        self.framework.validate_input(0.5, 'sentiment_score', 'cbsc_sentiment_data')
        self.framework.validate_input(-1.0, 'sentiment_score', 'cbsc_sentiment_data')
        self.framework.validate_input(1.0, 'sentiment_score', 'cbsc_sentiment_data')

        with self.assertRaises(SecurityError):
            self.framework.validate_input(2.0, 'sentiment_score', 'cbsc_sentiment_data')

    def test_create_secure_select_query(self):
        """測試創建安全 SELECT 查詢"""
        query, params = self.framework.create_secure_query(
            table='users',
            operation=SQLOperationType.SELECT,
            columns=['id', 'username', 'email'],
            where_clause='is_active = %s',
            where_params={'is_active': True},
            limit=100
        )

        self.assertIn('SELECT', query)
        self.assertIn('FROM users', query)
        self.assertIn('WHERE', query)
        self.assertIn('LIMIT', query)
        self.assertEqual(params, [True])

    def test_create_secure_insert_query(self):
        """測試創建安全 INSERT 查詢"""
        query, params = self.framework.create_secure_query(
            table='users',
            operation=SQLOperationType.INSERT,
            columns=['username', 'email'],
            where_params={'username': 'testuser', 'email': 'test@example.com'}
        )

        self.assertIn('INSERT INTO users', query)
        self.assertIn('VALUES', query)
        self.assertEqual(params, ['testuser', 'test@example.com'])

    def test_create_secure_query_with_invalid_table(self):
        """測試創建查詢時表名驗證失敗"""
        with self.assertRaises(SecurityError):
            self.framework.create_secure_query(
                table="'; DROP TABLE users; --",
                operation=SQLOperationType.SELECT
            )

    def test_create_secure_query_with_invalid_column(self):
        """測試創建查詢時列名驗證失敗"""
        with self.assertRaises(SecurityError):
            self.framework.create_secure_query(
                table='users',
                operation=SQLOperationType.SELECT,
                columns=['id', "password'; DROP TABLE--"]
            )


class TestPartitionNameValidation(unittest.TestCase):
    """測試分區名驗證"""

    def setUp(self):
        """設置測試環境"""
        self.framework = EnhancedSecureSQLFramework()

    def test_valid_monthly_partition_suffix(self):
        """測試有效的月份分區後綴"""
        valid_suffixes = [
            '2025_01',
            '2024_12',
            '2023_06',
        ]

        for suffix in valid_suffixes:
            with self.subTest(suffix=suffix):
                self.assertTrue(
                    self.framework._is_valid_partition_suffix(suffix),
                    f"Suffix should be valid: {suffix}"
                )

    def test_valid_daily_partition_suffix(self):
        """測試有效的日期分區後綴"""
        valid_suffixes = [
            '20250125',
            '20241231',
            '20230215',
        ]

        for suffix in valid_suffixes:
            with self.subTest(suffix=suffix):
                self.assertTrue(
                    self.framework._is_valid_partition_suffix(suffix),
                    f"Suffix should be valid: {suffix}"
                )

    def test_invalid_partition_suffix(self):
        """測試無效分區後綴"""
        invalid_suffixes = [
            '2025-01',  # Wrong separator
            '25_01',    # Wrong year format
            '2025_1',   # Wrong month format
            'drop_table',  # Malicious
            '2025_13',  # Invalid month
            '20250132',  # Invalid day
        ]

        for suffix in invalid_suffixes:
            with self.subTest(suffix=suffix):
                self.assertFalse(
                    self.framework._is_valid_partition_suffix(suffix),
                    f"Suffix should be invalid: {suffix}"
                )


class TestCBSCQueryValidator(unittest.TestCase):
    """測試 CBSC 查詢驗證器"""

    def setUp(self):
        """設置測試環境"""
        from src.security.secure_sql_framework_v2 import EnhancedSecureSQLFramework
        schema = EnhancedSecureSQLFramework.CBSC_SECURE_SCHEMA
        self.validator = CBSCQueryValidator(schema)

    def test_validate_select_query_success(self):
        """測試驗證有效的 SELECT 查詢"""
        result = self.validator.validate_select_query(
            table='users',
            columns=['id', 'username', 'email'],
            limit=100
        )

        self.assertTrue(result)

    def test_validate_select_query_invalid_table(self):
        """測試無效表名拋出異常"""
        with self.assertRaises(SecurityError):
            self.validator.validate_select_query(
                table='nonexistent_table',
                columns=['id']
            )

    def test_validate_select_query_invalid_column(self):
        """測試無效列名拋出異常"""
        with self.assertRaises(SecurityError):
            self.validator.validate_select_query(
                table='users',
                columns=['id', 'password', 'nonexistent_column']
            )

    def test_validate_select_query_invalid_limit(self):
        """測試無效 LIMIT 拋出異常"""
        with self.assertRaises(SecurityError):
            self.validator.validate_select_query(
                table='users',
                columns=['id'],
                limit=-1
            )

        with self.assertRaises(SecurityError):
            self.validator.validate_select_query(
                table='users',
                columns=['id'],
                limit=20000  # Too large
            )


class TestSingletonPattern(unittest.TestCase):
    """測試單例模式"""

    def test_get_secure_framework_singleton(self):
        """測試獲取安全框架單例"""
        framework1 = get_secure_framework()
        framework2 = get_secure_framework()

        self.assertIs(framework1, framework2)
        self.assertIsInstance(framework1, EnhancedSecureSQLFramework)


class TestIntegrationScenarios(unittest.TestCase):
    """集成測試場景"""

    def setUp(self):
        """設置測試環境"""
        self.framework = EnhancedSecureSQLFramework()

    def test_secure_partition_workflow(self):
        """測試安全分區工作流程"""
        # 模擬創建分區的完整流程
        table_name = 'strategy_signals'
        partition_date = datetime(2025, 1, 1)
        partition_name = f"{table_name}_{partition_date.strftime('%Y_%m')}"

        # 1. 驗證表名
        self.framework.validate_table_name(table_name)

        # 2. 驗證分區名
        self.framework.validate_table_name(partition_name)

        # 3. 驗證後綴格式
        suffix = partition_date.strftime('%Y_%m')
        self.assertTrue(self.framework._is_valid_partition_suffix(suffix))

    def test_attack_scenario_prevention(self):
        """測試防禦攻擊場景"""
        attack_scenarios = [
            # 嘗試注入惡意表名
            {
                'table': "users; DROP TABLE strategy_signals--",
                'expected': 'raise'
            },
            # 嘗試注入惡意分區名
            {
                'partition': "strategy_signals_'; DROP TABLE users--",
                'expected': 'raise'
            },
            # 嘗試在參數中注入
            {
                'input': "admin' OR '1'='1",
                'expected': 'raise'
            },
        ]

        for scenario in attack_scenarios:
            with self.subTest(scenario=scenario):
                if 'table' in scenario:
                    with self.assertRaises(SecurityError):
                        self.framework.validate_table_name(scenario['table'])

                if 'partition' in scenario:
                    with self.assertRaises(SecurityError):
                        self.framework.validate_table_name(scenario['partition'])

                if 'input' in scenario:
                    with self.assertRaises(SecurityError):
                        self.framework.validate_input(scenario['input'])


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
