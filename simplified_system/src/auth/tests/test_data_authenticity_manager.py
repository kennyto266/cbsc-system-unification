#!/usr / bin / env python3
"""
DataAuthenticityManager Tests
数据真实性管理器测试

Unit tests for the data authenticity manager
数据真实性管理器的单元测试
"""

import asyncio
import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from interfaces.auth_result import AuthResult, AuthStatus, Verdict
from interfaces.data_authenticity_manager import DataAuthenticityManager


class MockVerifier:
    """模拟验证器"""

    def __init__(
        self,
        name: str,
        verifier_type: str,
        supported_types: list,
        verdict: Verdict = Verdict.AUTHENTIC,
        confidence: float = 0.8,
    ):
        self.name = name
        self.verifier_type = verifier_type
        self.supported_types = supported_types
        self.verdict = verdict
        self.confidence = confidence
        self.enabled = True
        self.priority = 50

    async def verify(self, data, data_id, context = None):
        """模拟验证方法"""
        from interfaces.auth_result import AuthResult

        return AuthResult(
            data_id = data_id,
            data_type = context.get("data_type", "unknown") if context else "unknown",
            data_source = context.get("data_source", "unknown") if context else "unknown",
            overall_verdict = self.verdict,
            overall_confidence = self.confidence,
            status = AuthStatus.COMPLETED,
            total_execution_time_ms = 10.0,
        )

    def get_verifier_type(self):
        return self.verifier_type

    def get_supported_data_types(self):
        return self.supported_types

    def is_enabled(self):
        return self.enabled

    def get_name(self):
        return self.name

    async def health_check(self):
        return {
            "verifier": self.name,
            "type": self.verifier_type,
            "enabled": self.enabled,
            "status": "healthy",
        }


class TestDataAuthenticityManager(unittest.TestCase):
    """数据真实性管理器测试类"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            "max_history_size": 100,
            "default_timeout": 30.0,
            "parallel_execution": True,
        }
        self.manager = DataAuthenticityManager(self.config)

        # 创建模拟验证器
        self.mock_verifier1 = MockVerifier(
            "Test Verifier 1",
            "test_verifier",
            ["json", "api_data"],
            Verdict.AUTHENTIC,
            0.9,
        )

        self.mock_verifier2 = MockVerifier(
            "Test Verifier 2",
            "another_verifier",
            ["json", "csv"],
            Verdict.SUSPICIOUS,
            0.6,
        )

        # 注册验证器
        self.manager.register_verifier(self.mock_verifier1)
        self.manager.register_verifier(self.mock_verifier2)

    def test_verifier_registration(self):
        """测试验证器注册"""
        # 测试获取已注册验证器
        verifiers = self.manager.get_registered_verifiers()
        self.assertEqual(len(verifiers), 2)
        self.assertIn("test_verifier", verifiers)
        self.assertIn("another_verifier", verifiers)

        # 测试验证器类型列表
        verifier_types = self.manager.get_verifier_types()
        self.assertEqual(len(verifier_types), 2)

        # 测试注销验证器
        success = self.manager.unregister_verifier("test_verifier")
        self.assertTrue(success)

        verifiers = self.manager.get_registered_verifiers()
        self.assertEqual(len(verifiers), 1)

    async def test_verify_data(self):
        """测试数据验证"""
        test_data = {"source": "hkma.gov.hk", "value": 100}
        data_id = "test_data_001"
        data_type = "json"
        data_source = "api.hkma.gov.hk"

        result = await self.manager.verify_data(
            data = test_data,
            data_id = data_id,
            data_type = data_type,
            data_source = data_source,
        )

        # 验证结果结构
        self.assertIsInstance(result, AuthResult)
        self.assertEqual(result.data_id, data_id)
        self.assertEqual(result.data_type, data_type)
        self.assertEqual(result.data_source, data_source)
        self.assertEqual(result.status, AuthStatus.COMPLETED)

        # 验证验证层
        self.assertEqual(len(result.layers), 2)  # 两个验证器都应该执行

        # 验证综合结果
        self.assertIn(result.overall_verdict, [Verdict.AUTHENTIC, Verdict.SUSPICIOUS])
        self.assertGreaterEqual(result.overall_confidence, 0.0)
        self.assertLessEqual(result.overall_confidence, 1.0)

    async def test_verify_with_specific_verifiers(self):
        """测试使用指定验证器验证"""
        test_data = {"source": "hkma.gov.hk", "value": 100}

        result = await self.manager.verify_data(
            data = test_data,
            data_id="test_002",
            data_type="json",
            data_source="api.hkma.gov.hk",
            verifier_types=["test_verifier"],  # 只使用第一个验证器
        )

        # 应该只有一个验证层
        self.assertEqual(len(result.layers), 1)
        self.assertEqual(result.layers[0].layer_type, "test_verifier")

    async def test_verify_batch(self):
        """测试批量验证"""
        data_list = [
            {
                "data": {"source": "hkma.gov.hk", "value": 100},
                "data_id": "batch_001",
                "data_type": "json",
                "data_source": "api.hkma.gov.hk",
            },
            {
                "data": {"source": "test.source", "value": 200},
                "data_id": "batch_002",
                "data_type": "json",
                "data_source": "api.test.com",
            },
        ]

        results = await self.manager.verify_batch(data_list)

        # 验证批量结果
        self.assertEqual(len(results), 2)

        for result in results:
            self.assertIsInstance(result, AuthResult)
            self.assertEqual(result.status, AuthStatus.COMPLETED)
            self.assertGreater(len(result.layers), 0)

    def test_verification_history(self):
        """测试验证历史记录"""
        # 初始状态应该没有历史记录
        history = self.manager.get_verification_history()
        self.assertEqual(len(history), 0)

    def test_statistics(self):
        """测试统计信息"""
        stats = self.manager.get_statistics()

        # 验证统计结构
        self.assertIn("total_verifications", stats)
        self.assertIn("registered_verifiers", stats)
        self.assertIn("success_rate", stats)

        # 初始状态
        self.assertEqual(stats["total_verifications"], 0)
        self.assertEqual(stats["registered_verifiers"], 2)

    async def test_health_check(self):
        """测试健康检查"""
        health = await self.manager.health_check()

        self.assertIn("manager_status", health)
        self.assertIn("registered_verifiers", health)
        self.assertIn("verifier_health", health)

        self.assertEqual(health["manager_status"], "healthy")
        self.assertEqual(health["registered_verifiers"], 2)

    async def test_overall_result_calculation(self):
        """测试综合结果计算"""
        # 创建一个确定结果的测试
        confident_verifier = MockVerifier(
            "Confident Verifier",
            "confident_verifier",
            ["json"],
            Verdict.AUTHENTIC,
            0.95,
        )

        self.manager.register_verifier(confident_verifier)

        test_data = {"source": "hkma.gov.hk", "value": 100}

        result = await self.manager.verify_data(
            data = test_data,
            data_id="test_calculation",
            data_type="json",
            data_source="api.hkma.gov.hk",
        )

        # 高置信度的验证器应该影响整体结果
        self.assertGreater(result.overall_confidence, 0.8)
        self.assertEqual(result.overall_verdict, Verdict.AUTHENTIC)

    def test_verifier_selection_by_data_type(self):
        """测试根据数据类型选择验证器"""
        # 创建支持不同数据类型的验证器
        json_verifier = MockVerifier("JSON Verifier", "json_verifier", ["json"])
        csv_verifier = MockVerifier("CSV Verifier", "csv_verifier", ["csv"])

        self.manager.register_verifier(json_verifier)
        self.manager.register_verifier(csv_verifier)

        # 模拟选择过程
        json_data_verifiers = self.manager._select_verifiers(None, "json")
        csv_data_verifiers = self.manager._select_verifiers(None, "csv")

        # 验证选择结果
        json_verifier_types = [v.get_verifier_type() for v in json_data_verifiers]
        csv_verifier_types = [v.get_verifier_type() for v in csv_data_verifiers]

        self.assertIn("json_verifier", json_verifier_types)
        self.assertIn("csv_verifier", csv_verifier_types)

    async def test_error_handling(self):
        """测试错误处理"""

        # 创建一个会抛出异常的验证器
        class FailingVerifier:
            def __init__(self):
                self.name = "Failing Verifier"
                self.enabled = True
                self.priority = 50

            async def verify(self, data, data_id, context = None):
                raise Exception("Test error")

            def get_verifier_type(self):
                return "failing_verifier"

            def get_supported_data_types(self):
                return ["json"]

            def is_enabled(self):
                return self.enabled

            def get_name(self):
                return self.name

        failing_verifier = FailingVerifier()
        self.manager.register_verifier(failing_verifier)

        test_data = {"source": "test", "value": 100}

        # 验证应该处理错误并继续
        result = await self.manager.verify_data(
            data = test_data,
            data_id="error_test",
            data_type="json",
            data_source="test.source",
        )

        # 结果应该包含错误层
        error_layers = [
            layer for layer in result.layers if layer.verdict == Verdict.ERROR
        ]
        self.assertGreater(len(error_layers), 0)


class TestIntegrationWorkflow(unittest.TestCase):
    """集成工作流测试"""

    def setUp(self):
        """测试前准备"""
        self.manager = DataAuthenticityManager()

    async def test_complete_workflow(self):
        """测试完整工作流"""
        # 注册多个验证器
        verifiers = [
            MockVerifier(
                "Domain Verifier", "domain", ["api_data"], Verdict.AUTHENTIC, 0.9
            ),
            MockVerifier(
                "Signature Verifier", "signature", ["api_data"], Verdict.AUTHENTIC, 0.85
            ),
            MockVerifier(
                "Integrity Verifier", "integrity", ["api_data"], Verdict.SUSPICIOUS, 0.6
            ),
        ]

        for verifier in verifiers:
            self.manager.register_verifier(verifier)

        # 模拟政府数据验证
        hibor_data = {
            "date": "2024 - 01 - 01",
            "overnight_rate": 3.15,
            "source": "hkma.gov.hk",
        }

        result = await self.manager.verify_data(
            data = hibor_data,
            data_id="hibor_20240101",
            data_type="api_data",
            data_source="api.hkma.gov.hk",
        )

        # 验证工作流结果
        self.assertEqual(result.status, AuthStatus.COMPLETED)
        self.assertEqual(len(result.layers), 3)
        self.assertGreater(result.get_success_rate(), 0.5)

        # 验证统计信息更新
        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_verifications"], 1)


if __name__ == "__main__":
    # 运行异步测试
    def run_async_test(test_func):
        """运行异步测试的辅助函数"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_func())
        finally:
            loop.close()

    # 运行异步测试方法
    test_methods = [
        "test_verify_data",
        "test_verify_with_specific_verifiers",
        "test_verify_batch",
        "test_health_check",
        "test_overall_result_calculation",
        "test_error_handling",
        "test_complete_workflow",
    ]

    for method_name in test_methods:

        def create_test_method(method):
            def test(self):
                run_async_test(lambda: getattr(self, method)())

            return test

        setattr(
            TestDataAuthenticityManager, method_name, create_test_method(method_name)
        )
        setattr(TestIntegrationWorkflow, method_name, create_test_method(method_name))

    unittest.main()
