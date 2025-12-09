#!/usr/bin/env python3
"""
Rules Engine
规则引擎

Authentication rules engine for executing complex conditional logic
用于执行复杂条件逻辑的认证规则引擎
"""

import json
import yaml
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from .rule import Rule, RulePriority, ActionType

# Setup logging
logger = logging.getLogger(__name__)


class RulesEngine:
    """认证规则引擎"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化规则引擎

        Args:
            config: 规则引擎配置
        """
        self.config = config or {}
        self.rules: Dict[str, Rule] = {}
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'rules_matched': 0
        }
        self.enabled = self.config.get('enabled', True)
        self.max_rules_per_execution = self.config.get('max_rules_per_execution', 100)
        self.execution_timeout = self.config.get('execution_timeout', 60.0)
        self.rule_files: List[str] = self.config.get('rule_files', [])

        # 加载规则文件
        self._load_rule_files()

        logger.info(f"RulesEngine initialized with {len(self.rules)} rules")

    def _load_rule_files(self):
        """加载规则文件"""
        for rule_file in self.rule_files:
            try:
                self._load_rule_file(rule_file)
            except Exception as e:
                logger.error(f"Failed to load rule file {rule_file}: {e}")

    def _load_rule_file(self, rule_file: str):
        """加载单个规则文件"""
        rule_path = Path(rule_file)

        if not rule_path.exists():
            logger.warning(f"Rule file not found: {rule_path}")
            return

        try:
            with open(rule_path, 'r', encoding='utf-8') as f:
                if rule_path.suffix.lower() in ['.yaml', '.yml']:
                    rules_data = yaml.safe_load(f)
                elif rule_path.suffix.lower() == '.json':
                    rules_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported rule file format: {rule_path.suffix}")

            # 解析规则
            if isinstance(rules_data, dict) and 'rules' in rules_data:
                rules_list = rules_data['rules']
            elif isinstance(rules_data, list):
                rules_list = rules_data
            else:
                raise ValueError("Invalid rule file format")

            for rule_data in rules_list:
                try:
                    rule = Rule.from_dict(rule_data)
                    self.add_rule(rule)
                except Exception as e:
                    logger.error(f"Failed to parse rule {rule_data.get('id', 'unknown')}: {e}")

            logger.info(f"Loaded {len(rules_list)} rules from {rule_path}")

        except Exception as e:
            logger.error(f"Error loading rule file {rule_path}: {e}")

    def add_rule(self, rule: Rule) -> bool:
        """
        添加规则

        Args:
            rule: 规则实例

        Returns:
            bool: 添加是否成功
        """
        try:
            # 检查规则ID是否已存在
            if rule.id in self.rules:
                logger.warning(f"Rule {rule.id} already exists, overwriting")

            self.rules[rule.id] = rule
            logger.info(f"Added rule: {rule.name} ({rule.id})")
            return True

        except Exception as e:
            logger.error(f"Failed to add rule {rule.id}: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """
        移除规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 移除是否成功
        """
        if rule_id in self.rules:
            rule_name = self.rules[rule_id].name
            del self.rules[rule_id]
            logger.info(f"Removed rule: {rule_name} ({rule_id})")
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则"""
        return self.rules.get(rule_id)

    def get_all_rules(self) -> Dict[str, Rule]:
        """获取所有规则"""
        return self.rules.copy()

    def get_rules_by_tag(self, tag: str) -> List[Rule]:
        """根据标签获取规则"""
        return [rule for rule in self.rules.values() if tag in rule.tags]

    def get_enabled_rules(self) -> List[Rule]:
        """获取启用的规则"""
        return [rule for rule in self.rules.values() if rule.enabled]

    def enable_rule(self, rule_id: str, enabled: bool = True) -> bool:
        """启用/禁用规则"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = enabled
            logger.info(f"Rule {rule_id} {'enabled' if enabled else 'disabled'}")
            return True
        return False

    async def evaluate_rules(
        self,
        context: Dict[str, Any],
        rule_ids: Optional[List[str]] = None,
        max_rules: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        评估规则

        Args:
            context: 评估上下文
            rule_ids: 指定要评估的规则ID列表，如果为None则评估所有规则
            max_rules: 最大执行规则数

        Returns:
            Dict[str, Any]: 评估结果
        """
        if not self.enabled:
            return {
                'executed': False,
                'reason': 'Rules engine is disabled',
                'results': []
            }

        start_time = datetime.now()

        try:
            # 确定要评估的规则
            if rule_ids:
                rules_to_evaluate = [self.rules[rid] for rid in rule_ids if rid in self.rules]
            else:
                rules_to_evaluate = list(self.rules.values())

            # 按优先级排序
            rules_to_evaluate.sort(key=lambda r: r.priority.value)

            # 限制规则数量
            max_rules = max_rules or self.max_rules_per_execution
            rules_to_evaluate = rules_to_evaluate[:max_rules]

            logger.info(f"Evaluating {len(rules_to_evaluate)} rules")

            # 执行规则评估
            results = []
            for rule in rules_to_evaluate:
                try:
                    result = await self._execute_rule_with_timeout(rule, context)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error executing rule {rule.id}: {e}")
                    results.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'error': str(e),
                        'executed': False
                    })

            # 更新统计信息
            self._update_stats(results)

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return {
                'executed': True,
                'execution_time_ms': execution_time,
                'total_rules': len(rules_to_evaluate),
                'rules_matched': sum(1 for r in results if r.get('matched', False)),
                'actions_executed': sum(r.get('actions_executed', 0) for r in results),
                'results': results
            }

        except Exception as e:
            logger.error(f"Rules engine evaluation failed: {e}")
            return {
                'executed': False,
                'error': str(e),
                'execution_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
                'results': []
            }

    async def _execute_rule_with_timeout(self, rule: Rule, context: Dict[str, Any]) -> Dict[str, Any]:
        """带超时的规则执行"""
        try:
            # 设置超时
            return await asyncio.wait_for(
                asyncio.to_thread(rule.execute, context),
                timeout=self.execution_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Rule {rule.id} execution timed out")
            return {
                'rule_id': rule.id,
                'rule_name': rule.name,
                'error': 'Execution timeout',
                'executed': False
            }

    def _update_stats(self, results: List[Dict[str, Any]]):
        """更新统计信息"""
        self.execution_stats['total_executions'] += len(results)
        self.execution_stats['rules_matched'] += sum(1 for r in results if r.get('matched', False))
        self.execution_stats['successful_executions'] += sum(
            1 for r in results if not r.get('error') and r.get('executed', False)
        )
        self.execution_stats['failed_executions'] += sum(
            1 for r in results if r.get('error') or not r.get('executed', False)
        )

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_rules = len(self.rules)
        enabled_rules = len(self.get_enabled_rules())
        rules_by_priority = {}

        for priority in RulePriority:
            count = sum(1 for rule in self.rules.values() if rule.priority == priority)
            rules_by_priority[priority.name] = count

        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': total_rules - enabled_rules,
            'rules_by_priority': rules_by_priority,
            'execution_stats': self.execution_stats.copy(),
            'success_rate': (
                self.execution_stats['successful_executions'] /
                max(1, self.execution_stats['total_executions'])
            )
        }

    def export_rules(self, export_path: str, format: str = 'yaml') -> bool:
        """
        导出规则

        Args:
            export_path: 导出路径
            format: 导出格式 ('yaml' 或 'json')

        Returns:
            bool: 导出是否成功
        """
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_rules': len(self.rules),
                'rules': [rule.to_dict() for rule in self.rules.values()]
            }

            export_path = Path(export_path)
            export_path.parent.mkdir(parents=True, exist_ok=True)

            with open(export_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(export_data, f, default_flow_style=False, allow_unicode=True)
                elif format.lower() == 'json':
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                else:
                    raise ValueError(f"Unsupported export format: {format}")

            logger.info(f"Rules exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export rules: {e}")
            return False

    def import_rules(self, import_path: str, overwrite: bool = False) -> bool:
        """
        导入规则

        Args:
            import_path: 导入路径
            overwrite: 是否覆盖现有规则

        Returns:
            bool: 导入是否成功
        """
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return False

            with open(import_path, 'r', encoding='utf-8') as f:
                if import_path.suffix.lower() in ['.yaml', '.yml']:
                    import_data = yaml.safe_load(f)
                elif import_path.suffix.lower() == '.json':
                    import_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported import format: {import_path.suffix}")

            imported_count = 0
            for rule_data in import_data.get('rules', []):
                try:
                    rule = Rule.from_dict(rule_data)
                    if overwrite or rule.id not in self.rules:
                        self.add_rule(rule)
                        imported_count += 1
                except Exception as e:
                    logger.error(f"Failed to import rule {rule_data.get('id', 'unknown')}: {e}")

            logger.info(f"Imported {imported_count} rules from {import_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to import rules: {e}")
            return False

    def validate_rules(self) -> Dict[str, Any]:
        """验证规则完整性"""
        issues = []
        warnings = []

        for rule in self.rules.values():
            rule_issues = []
            rule_warnings = []

            # 检查规则基本属性
            if not rule.id or not rule.name:
                rule_issues.append("Missing rule ID or name")

            # 检查条件
            if not rule.conditions:
                rule_warnings.append("Rule has no conditions")
            else:
                for i, condition in enumerate(rule.conditions):
                    if not condition.field:
                        rule_issues.append(f"Condition {i} has no field")

            # 检查动作
            if not rule.actions:
                rule_warnings.append("Rule has no actions")
            else:
                for i, action in enumerate(rule.actions):
                    if action.action_type == ActionType.REQUIRE_VERIFIER:
                        if not action.parameters.get('verifiers'):
                            rule_warnings.append(f"Action {i} requires verifiers list")

            if rule_issues:
                issues.append(f"Rule {rule.id}: {'; '.join(rule_issues)}")

            if rule_warnings:
                warnings.append(f"Rule {rule.id}: {'; '.join(rule_warnings)}")

        return {
            'valid': len(issues) == 0,
            'total_rules': len(self.rules),
            'issues': issues,
            'warnings': warnings
        }

    async def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up RulesEngine")
        self.rules.clear()
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'rules_matched': 0
        }