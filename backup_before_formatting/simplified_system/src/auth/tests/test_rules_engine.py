#!/usr/bin/env python3
"""
RulesEngine Tests
规则引擎测试

Unit tests for the rules engine
规则引擎的单元测试
"""

import unittest
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from rules.rules_engine import RulesEngine
from rules.rule import Rule, RulePriority, RuleCondition, RuleAction, RuleOperator, ActionType


class TestRulesEngine(unittest.TestCase):
    """规则引擎测试类"""

    def setUp(self):
        """测试前准备"""
        self.config = {
            'enabled': True,
            'max_rules_per_execution': 10,
            'execution_timeout': 30.0
        }
        self.rules_engine = RulesEngine(self.config)

        # 创建测试规则
        self.test_rule = Rule(
            id="test_rule_1",
            name="Test Rule",
            description="A test rule for unit testing",
            priority=RulePriority.NORMAL,
            enabled=True,
            conditions=[
                RuleCondition(
                    field="data.source",
                    operator=RuleOperator.EQUALS,
                    value="hkma.gov.hk"
                )
            ],
            actions=[
                RuleAction(
                    action_type=ActionType.REQUIRE_VERIFIER,
                    parameters={"verifiers": ["digital_signature"]}
                )
            ]
        )

    def test_add_remove_rule(self):
        """测试添加和移除规则"""
        # 添加规则
        success = self.rules_engine.add_rule(self.test_rule)
        self.assertTrue(success)
        self.assertEqual(len(self.rules_engine.rules), 1)

        # 获取规则
        retrieved_rule = self.rules_engine.get_rule("test_rule_1")
        self.assertIsNotNone(retrieved_rule)
        self.assertEqual(retrieved_rule.name, "Test Rule")

        # 移除规则
        success = self.rules_engine.remove_rule("test_rule_1")
        self.assertTrue(success)
        self.assertEqual(len(self.rules_engine.rules), 0)

    def test_rule_conditions(self):
        """测试规则条件"""
        rule = self.test_rule

        # 测试匹配条件
        matching_context = {
            "data": {
                "source": "hkma.gov.hk"
            }
        }
        self.assertTrue(rule.evaluate(matching_context))

        # 测试不匹配条件
        non_matching_context = {
            "data": {
                "source": "untrusted.source"
            }
        }
        self.assertFalse(rule.evaluate(non_matching_context))

    def test_rule_actions(self):
        """测试规则动作"""
        context = {
            "data": {
                "source": "hkma.gov.hk"
            }
        }

        result = self.test_rule.execute(context)

        self.assertTrue(result['matched'])
        self.assertEqual(result['actions_executed'], 1)
        self.assertEqual(len(result['action_results']), 1)

        action_result = result['action_results'][0]
        self.assertTrue(action_result['executed'])
        self.assertEqual(action_result['action_type'], ActionType.REQUIRE_VERIFIER.value)

    async def test_evaluate_rules(self):
        """测试规则评估"""
        self.rules_engine.add_rule(self.test_rule)

        context = {
            "data": {
                "source": "hkma.gov.hk"
            }
        }

        evaluation_result = await self.rules_engine.evaluate_rules(context)

        self.assertTrue(evaluation_result['executed'])
        self.assertEqual(evaluation_result['total_rules'], 1)
        self.assertEqual(evaluation_result['rules_matched'], 1)
        self.assertEqual(evaluation_result['actions_executed'], 1)

    def test_rule_priority_sorting(self):
        """测试规则优先级排序"""
        # 创建不同优先级的规则
        high_priority_rule = Rule(
            id="high_priority",
            name="High Priority Rule",
            description="High priority test rule",
            priority=RulePriority.HIGH
        )

        low_priority_rule = Rule(
            id="low_priority",
            name="Low Priority Rule",
            description="Low priority test rule",
            priority=RulePriority.LOW
        )

        # 按随机顺序添加规则
        self.rules_engine.add_rule(low_priority_rule)
        self.rules_engine.add_rule(high_priority_rule)
        self.rules_engine.add_rule(self.test_rule)  # NORMAL priority

        context = {"data": {"source": "test"}}

        # 评估规则应该按优先级排序执行
        evaluation_result = asyncio.run(self.rules_engine.evaluate_rules(context))

        self.assertEqual(evaluation_result['total_rules'], 3)
        # 结果应该按优先级排序（HIGH, NORMAL, LOW）
        results = evaluation_result['results']
        self.assertEqual(results[0]['rule_id'], 'high_priority')
        self.assertEqual(results[1]['rule_id'], 'test_rule_1')
        self.assertEqual(results[2]['rule_id'], 'low_priority')

    def test_rules_statistics(self):
        """测试规则统计"""
        # 添加测试规则
        self.rules_engine.add_rule(self.test_rule)

        stats = self.rules_engine.get_statistics()

        self.assertEqual(stats['total_rules'], 1)
        self.assertEqual(stats['enabled_rules'], 1)
        self.assertEqual(stats['disabled_rules'], 0)

        # 执行规则以更新统计
        context = {"data": {"source": "hkma.gov.hk"}}
        asyncio.run(self.rules_engine.evaluate_rules(context))

        updated_stats = self.rules_engine.get_statistics()
        self.assertGreater(updated_stats['execution_stats']['total_executions'], 0)

    def test_rules_validation(self):
        """测试规则验证"""
        # 添加有效规则
        self.rules_engine.add_rule(self.test_rule)

        validation_result = self.rules_engine.validate_rules()

        self.assertTrue(validation_result['valid'])
        self.assertEqual(validation_result['total_rules'], 1)
        self.assertEqual(len(validation_result['issues']), 0)

    def test_export_import_rules(self):
        """测试规则导出和导入"""
        import tempfile
        import os

        # 添加测试规则
        self.rules_engine.add_rule(self.test_rule)

        # 导出到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name

        try:
            success = self.rules_engine.export_rules(export_path, 'json')
            self.assertTrue(success)

            # 创建新的规则引擎并导入规则
            new_rules_engine = RulesEngine()
            success = new_rules_engine.import_rules(export_path, overwrite=True)
            self.assertTrue(success)

            # 验证导入的规则
            imported_rule = new_rules_engine.get_rule("test_rule_1")
            self.assertIsNotNone(imported_rule)
            self.assertEqual(imported_rule.name, "Test Rule")

        finally:
            os.unlink(export_path)

    def test_multiple_conditions(self):
        """测试多条件规则"""
        complex_rule = Rule(
            id="complex_rule",
            name="Complex Rule",
            description="Rule with multiple conditions",
            priority=RulePriority.NORMAL,
            conditions=[
                RuleCondition(
                    field="data.source",
                    operator=RuleOperator.EQUALS,
                    value="hkma.gov.hk"
                ),
                RuleCondition(
                    field="data.type",
                    operator=RuleOperator.IN,
                    value=["hibor", "exchange_rate"]
                ),
                RuleCondition(
                    field="verification.confidence",
                    operator=RuleOperator.GREATER_EQUAL,
                    value=0.8
                )
            ],
            actions=[
                RuleAction(
                    action_type=ActionType.APPROVE_DATA,
                    parameters={"confidence": 0.9}
                )
            ]
        )

        # 测试所有条件匹配
        matching_context = {
            "data": {
                "source": "hkma.gov.hk",
                "type": "hibor"
            },
            "verification": {
                "confidence": 0.85
            }
        }

        result = complex_rule.execute(matching_context)
        self.assertTrue(result['matched'])

        # 测试部分条件不匹配
        non_matching_context = {
            "data": {
                "source": "hkma.gov.hk",
                "type": "unauthorized_type"
            },
            "verification": {
                "confidence": 0.85
            }
        }

        result = complex_rule.execute(non_matching_context)
        self.assertFalse(result['matched'])


class TestRuleOperators(unittest.TestCase):
    """规则操作符测试"""

    def test_string_operators(self):
        """测试字符串操作符"""
        context = {"data": {"domain": "api.hkma.gov.hk"}}

        # 测试包含操作符
        condition = RuleCondition(
            field="data.domain",
            operator=RuleOperator.CONTAINS,
            value="hkma"
        )
        self.assertTrue(condition.evaluate(context))

        # 测试开始操作符
        condition = RuleCondition(
            field="data.domain",
            operator=RuleOperator.STARTS_WITH,
            value="api"
        )
        self.assertTrue(condition.evaluate(context))

        # 测试结束操作符
        condition = RuleCondition(
            field="data.domain",
            operator=RuleOperator.ENDS_WITH,
            value="gov.hk"
        )
        self.assertTrue(condition.evaluate(context))

    def test_numeric_operators(self):
        """测试数值操作符"""
        context = {"verification": {"confidence": 0.85}}

        # 测试大于操作符
        condition = RuleCondition(
            field="verification.confidence",
            operator=RuleOperator.GREATER_THAN,
            value=0.8
        )
        self.assertTrue(condition.evaluate(context))

        # 测试区间操作符
        condition = RuleCondition(
            field="verification.confidence",
            operator=RuleOperator.BETWEEN,
            value=[0.8, 0.9]
        )
        self.assertTrue(condition.evaluate(context))

    def test_list_operators(self):
        """测试列表操作符"""
        context = {"data": {"source": "hibor"}}

        # 测试包含操作符
        condition = RuleCondition(
            field="data.source",
            operator=RuleOperator.IN,
            value=["hibor", "exchange_rate", "monetary_base"]
        )
        self.assertTrue(condition.evaluate(context))

        # 测试不包含操作符
        condition = RuleCondition(
            field="data.source",
            operator=RuleOperator.NOT_IN,
            value=["untrusted", "suspicious"]
        )
        self.assertTrue(condition.evaluate(context))


if __name__ == '__main__':
    unittest.main()