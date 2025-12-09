#!/usr / bin / env python3
"""
Integration Test
集成测试

Integration test for the authentication system
认证系统的集成测试
"""

import asyncio
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestAuthenticationSystemIntegration(unittest.TestCase):
    """认证系统集成测试"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            "version": "1.0.0",
            "authenticity_manager": {
                "max_history_size": 100,
                "default_timeout": 30.0,
                "parallel_execution": True,
            },
            "verifiers": {"test_verifier": {"enabled": True, "priority": 80}},
        }

    def test_config_manager_import(self):
        """测试配置管理器导入"""
        try:
            from config.config_manager import ConfigManager

            config_manager = ConfigManager()
            self.assertIsNotNone(config_manager)
            self.assertIsInstance(config_manager.get("version"), str)
        except Exception as e:
            self.fail(f"ConfigManager import failed: {e}")

    def test_rules_engine_import(self):
        """测试规则引擎导入"""
        try:
            from rules.rules_engine import RulesEngine

            rules_engine = RulesEngine(self.config)
            self.assertIsNotNone(rules_engine)
            self.assertEqual(rules_engine.get_statistics()["total_rules"], 0)
        except Exception as e:
            self.fail(f"RulesEngine import failed: {e}")

    def test_data_authenticity_manager_import(self):
        """测试数据真实性管理器导入"""
        try:
            from interfaces.data_authenticity_manager import DataAuthenticityManager

            auth_manager = DataAuthenticityManager(self.config)
            self.assertIsNotNone(auth_manager)
            self.assertEqual(len(auth_manager.get_registered_verifiers()), 0)
        except Exception as e:
            self.fail(f"DataAuthenticityManager import failed: {e}")

    def test_auth_result_import(self):
        """测试认证结果导入"""
        try:
            from interfaces.auth_result import AuthResult, AuthStatus, Verdict

            result = AuthResult(
                data_id="test",
                data_type="test_type",
                data_source="test_source",
                overall_verdict = Verdict.AUTHENTIC,
                overall_confidence = 0.9,
                status = AuthStatus.COMPLETED,
                total_execution_time_ms = 100.0,
            )
            self.assertEqual(result.data_id, "test")
            self.assertEqual(result.overall_verdict, Verdict.AUTHENTIC)
        except Exception as e:
            self.fail(f"AuthResult import failed: {e}")

    def test_rule_classes_import(self):
        """测试规则类导入"""
        try:
            from rules.rule import (
                ActionType,
                Rule,
                RuleAction,
                RuleCondition,
                RuleOperator,
                RulePriority,
            )

            # Create a simple rule
            rule = Rule(
                id="test_rule",
                name="Test Rule",
                description="Integration test rule",
                priority = RulePriority.NORMAL,
            )
            self.assertEqual(rule.id, "test_rule")
            self.assertTrue(rule.enabled)
        except Exception as e:
            self.fail(f"Rule classes import failed: {e}")

    def test_base_authenticator_import(self):
        """测试基础认证器导入"""
        try:
            from core.authenticator import BaseAuthenticator

            self.assertIsNotNone(BaseAuthenticator)
        except Exception as e:
            self.fail(f"BaseAuthenticator import failed: {e}")

    async def test_basic_workflow(self):
        """测试基本工作流"""
        try:
            from interfaces.auth_result import AuthStatus, Verdict
            from interfaces.data_authenticity_manager import DataAuthenticityManager

            # Initialize manager
            auth_manager = DataAuthenticityManager(self.config)

            # Test health check
            health = await auth_manager.health_check()
            self.assertIn("manager_status", health)

            # Test statistics
            stats = auth_manager.get_statistics()
            self.assertIn("total_verifications", stats)
            self.assertEqual(stats["total_verifications"], 0)

        except Exception as e:
            self.fail(f"Basic workflow test failed: {e}")

    def test_config_file_loading(self):
        """测试配置文件加载"""
        try:
            from config.config_manager import ConfigManager

            # Test with default config
            config_manager = ConfigManager()
            self.assertIsNotNone(config_manager.get("version"))

            # Test config validation
            validation = config_manager.validate_config()
            self.assertIn("valid", validation)

        except Exception as e:
            self.fail(f"Config file loading test failed: {e}")


class TestEndToEndWorkflow(unittest.TestCase):
    """端到端工作流测试"""

    async def test_hkma_data_scenario(self):
        """测试HKMA数据场景"""
        try:
            from interfaces.data_authenticity_manager import DataAuthenticityManager
            from rules.rules_engine import RulesEngine

            from config.config_manager import ConfigManager

            # Create mock HKMA data
            hibor_data = {
                "date": "2024 - 01 - 01",
                "overnight_rate": 3.15,
                "source": "hkma.gov.hk",
                "domain": "api.hkma.gov.hk",
                "type": "hibor_rate",
            }

            # Initialize components
            config_manager = ConfigManager()
            RulesEngine()
            auth_manager = DataAuthenticityManager(config_manager.get_all_config())

            # Test basic functionality
            self.assertIsNotNone(auth_manager)
            health = await auth_manager.health_check()
            self.assertEqual(health["manager_status"], "healthy")

        except Exception as e:
            self.fail(f"HKMA data scenario test failed: {e}")


def run_async_test(test_func):
    """运行异步测试的辅助函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(test_func())
    finally:
        loop.close()


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add synchronous tests
    suite.addTest(TestAuthenticationSystemIntegration("test_config_manager_import"))
    suite.addTest(TestAuthenticationSystemIntegration("test_rules_engine_import"))
    suite.addTest(
        TestAuthenticationSystemIntegration("test_data_authenticity_manager_import")
    )
    suite.addTest(TestAuthenticationSystemIntegration("test_auth_result_import"))
    suite.addTest(TestAuthenticationSystemIntegration("test_rule_classes_import"))
    suite.addTest(TestAuthenticationSystemIntegration("test_base_authenticator_import"))
    suite.addTest(TestAuthenticationSystemIntegration("test_config_file_loading"))

    # Run tests
    runner = unittest.TextTestRunner(verbosity = 2)
    result = runner.run(suite)

    # Run async tests
    async_tests = [
        TestAuthenticationSystemIntegration("test_basic_workflow"),
        TestEndToEndWorkflow("test_hkma_data_scenario"),
    ]

    for test_class, test_method in async_tests:
        try:
            instance = test_class()
            instance.setUp()
            run_async_test(lambda: getattr(instance, test_method)())
            print(f"✅ {test_class.__name__}.{test_method} PASSED")
        except Exception as e:
            print(f"❌ {test_class.__name__}.{test_method} FAILED: {e}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
