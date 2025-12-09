#!/usr / bin / env python3
"""
Rule Classes
规则类

Define rule structures for the authentication rules engine
定义认证规则引擎的规则结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class RulePriority(Enum):
    """规则优先级"""

    CRITICAL = 1  # 关键规则，必须执行
    HIGH = 2  # 高优先级
    NORMAL = 3  # 普通优先级
    LOW = 4  # 低优先级
    INFO = 5  # 信息规则，仅记录


class RuleOperator(Enum):
    """规则操作符"""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_EQUAL = "ge"
    LESS_THAN = "lt"
    LESS_EQUAL = "le"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    MATCHES = "matches"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    BETWEEN = "between"


class LogicalOperator(Enum):
    """逻辑操作符"""

    AND = "and"
    OR = "or"
    NOT = "not"


class ActionType(Enum):
    """规则动作类型"""

    REQUIRE_VERIFIER = "require_verifier"  # 要求特定验证器
    EXCLUDE_VERIFIER = "exclude_verifier"  # 排除特定验证器
    SET_PRIORITY = "set_priority"  # 设置优先级
    ADJUST_TIMEOUT = "adjust_timeout"  # 调整超时时间
    LOG_WARNING = "log_warning"  # 记录警告
    LOG_INFO = "log_info"  # 记录信息
    REJECT_DATA = "reject_data"  # 拒绝数据
    APPROVE_DATA = "approve_data"  # 批准数据
    REQUIRE_ADDITIONAL_CHECK = "require_additional_check"  # 要求额外检查
    MODIFY_CONTEXT = "modify_context"  # 修改上下文
    CACHE_RESULT = "cache_result"  # 缓存结果


@dataclass
class RuleCondition:
    """规则条件"""

    field: str  # 字段路径，如 "data.source" 或 "verification.result"
    operator: RuleOperator  # 操作符
    value: Optional[Union[str, int, float, bool, List]] = None  # 比较值
    logical_op: LogicalOperator = LogicalOperator.AND  # 逻辑操作符

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        评估条件

        Args:
            context: 评估上下文

        Returns:
            bool: 条件是否满足
        """
        try:
            # 获取字段值
            field_value = self._get_field_value(context, self.field)

            # 根据操作符评估
            if self.operator == RuleOperator.EQUALS:
                return field_value == self.value
            elif self.operator == RuleOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == RuleOperator.GREATER_THAN:
                return float(field_value) > float(self.value)
            elif self.operator == RuleOperator.GREATER_EQUAL:
                return float(field_value) >= float(self.value)
            elif self.operator == RuleOperator.LESS_THAN:
                return float(field_value) < float(self.value)
            elif self.operator == RuleOperator.LESS_EQUAL:
                return float(field_value) <= float(self.value)
            elif self.operator == RuleOperator.CONTAINS:
                return str(self.value) in str(field_value)
            elif self.operator == RuleOperator.NOT_CONTAINS:
                return str(self.value) not in str(field_value)
            elif self.operator == RuleOperator.IN:
                return (
                    field_value in self.value if isinstance(self.value, list) else False
                )
            elif self.operator == RuleOperator.NOT_IN:
                return (
                    field_value not in self.value
                    if isinstance(self.value, list)
                    else True
                )
            elif self.operator == RuleOperator.MATCHES:
                import re

                return bool(re.match(str(self.value), str(field_value)))
            elif self.operator == RuleOperator.STARTS_WITH:
                return str(field_value).startswith(str(self.value))
            elif self.operator == RuleOperator.ENDS_WITH:
                return str(field_value).endswith(str(self.value))
            elif self.operator == RuleOperator.IS_NULL:
                return field_value is None
            elif self.operator == RuleOperator.IS_NOT_NULL:
                return field_value is not None
            elif self.operator == RuleOperator.BETWEEN:
                if isinstance(self.value, list) and len(self.value) == 2:
                    return (
                        float(self.value[0])
                        <= float(field_value)
                        <= float(self.value[1])
                    )
                return False
            else:
                return False

        except Exception:
            return False

    def _get_field_value(self, context: Dict[str, Any], field_path: str) -> Any:
        """获取字段值"""
        keys = field_path.split(".")
        value = context

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None

        return value


@dataclass
class RuleAction:
    """规则动作"""

    action_type: ActionType  # 动作类型
    parameters: Dict[str, Any] = field(default_factory = dict)  # 动作参数
    delay_ms: Optional[int] = None  # 延迟执行时间（毫秒）

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行动作

        Args:
            context: 执行上下文

        Returns:
            Dict[str, Any]: 执行结果
        """
        result = {
            "action_type": self.action_type.value,
            "executed": False,
            "result": None,
            "error": None,
        }

        try:
            if self.action_type == ActionType.REQUIRE_VERIFIER:
                result["result"] = {
                    "required_verifiers": self.parameters.get("verifiers", [])
                }
                result["executed"] = True

            elif self.action_type == ActionType.EXCLUDE_VERIFIER:
                result["result"] = {
                    "excluded_verifiers": self.parameters.get("verifiers", [])
                }
                result["executed"] = True

            elif self.action_type == ActionType.SET_PRIORITY:
                result["result"] = {
                    "verifier": self.parameters.get("verifier"),
                    "priority": self.parameters.get("priority"),
                }
                result["executed"] = True

            elif self.action_type == ActionType.ADJUST_TIMEOUT:
                result["result"] = {
                    "timeout_seconds": self.parameters.get("timeout", 30)
                }
                result["executed"] = True

            elif self.action_type == ActionType.LOG_WARNING:
                result["result"] = {
                    "message": self.parameters.get("message", "Rule warning triggered")
                }
                result["executed"] = True

            elif self.action_type == ActionType.LOG_INFO:
                result["result"] = {
                    "message": self.parameters.get("message", "Rule info triggered")
                }
                result["executed"] = True

            elif self.action_type == ActionType.REJECT_DATA:
                result["result"] = {
                    "reason": self.parameters.get("reason", "Rule rejection")
                }
                result["executed"] = True

            elif self.action_type == ActionType.APPROVE_DATA:
                result["result"] = {
                    "auto_approve": True,
                    "confidence": self.parameters.get("confidence", 0.8),
                }
                result["executed"] = True

            elif self.action_type == ActionType.REQUIRE_ADDITIONAL_CHECK:
                result["result"] = {
                    "additional_checks": self.parameters.get("checks", []),
                    "timeout": self.parameters.get("timeout", 60),
                }
                result["executed"] = True

            elif self.action_type == ActionType.MODIFY_CONTEXT:
                context_updates = self.parameters.get("updates", {})
                context.update(context_updates)
                result["result"] = {"context_updates": context_updates}
                result["executed"] = True

            elif self.action_type == ActionType.CACHE_RESULT:
                result["result"] = {
                    "cache_key": self.parameters.get("cache_key"),
                    "ttl_seconds": self.parameters.get("ttl", 3600),
                }
                result["executed"] = True

        except Exception as e:
            result["error"] = str(e)

        return result


@dataclass
class Rule:
    """认证规则"""

    id: str  # 规则唯一标识
    name: str  # 规则名称
    description: str  # 规则描述
    priority: RulePriority  # 规则优先级
    enabled: bool = True  # 是否启用
    conditions: List[RuleCondition] = field(default_factory = list)  # 条件列表
    actions: List[RuleAction] = field(default_factory = list)  # 动作列表
    created_at: datetime = field(default_factory = datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory = datetime.now)  # 更新时间
    tags: List[str] = field(default_factory = list)  # 标签
    execution_count: int = 0  # 执行次数
    last_executed: Optional[datetime] = None  # 最后执行时间

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        评估规则

        Args:
            context: 评估上下文

        Returns:
            bool: 规则是否匹配
        """
        if not self.enabled or not self.conditions:
            return False

        try:
            # 评估所有条件
            condition_results = []
            for condition in self.conditions:
                result = condition.evaluate(context)
                condition_results.append(result)

            # 简化的逻辑处理：所有条件都必须为真（AND逻辑）
            return all(condition_results)

        except Exception as e:
            # 规则评估错误，返回False
            return False

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行规则

        Args:
            context: 执行上下文

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 更新执行统计
        self.execution_count += 1
        self.last_executed = datetime.now()

        execution_result = {
            "rule_id": self.id,
            "rule_name": self.name,
            "matched": False,
            "actions_executed": 0,
            "action_results": [],
            "execution_time_ms": 0,
            "error": None,
        }

        try:
            start_time = datetime.now()

            # 评估规则是否匹配
            if self.evaluate(context):
                execution_result["matched"] = True

                # 执行所有动作
                for action in self.actions:
                    action_result = action.execute(context)
                    execution_result["action_results"].append(action_result)

                    if action_result["executed"]:
                        execution_result["actions_executed"] += 1

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            execution_result["execution_time_ms"] = execution_time

        except Exception as e:
            execution_result["error"] = str(e)

        return execution_result

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "conditions": [
                {
                    "field": cond.field,
                    "operator": cond.operator.value,
                    "value": cond.value,
                    "logical_op": cond.logical_op.value,
                }
                for cond in self.conditions
            ],
            "actions": [
                {
                    "action_type": action.action_type.value,
                    "parameters": action.parameters,
                    "delay_ms": action.delay_ms,
                }
                for action in self.actions
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "execution_count": self.execution_count,
            "last_executed": (
                self.last_executed.isoformat() if self.last_executed else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        """从字典创建规则实例"""
        rule = cls(
            id = data["id"],
            name = data["name"],
            description = data["description"],
            priority = RulePriority(data["priority"]),
            enabled = data.get("enabled", True),
        )

        # 添加条件
        for cond_data in data.get("conditions", []):
            condition = RuleCondition(
                field = cond_data["field"],
                operator = RuleOperator(cond_data["operator"]),
                value = cond_data.get("value"),
                logical_op = LogicalOperator(cond_data.get("logical_op", "and")),
            )
            rule.conditions.append(condition)

        # 添加动作
        for action_data in data.get("actions", []):
            action = RuleAction(
                action_type = ActionType(action_data["action_type"]),
                parameters = action_data.get("parameters", {}),
                delay_ms = action_data.get("delay_ms"),
            )
            rule.actions.append(action)

        # 其他属性
        rule.tags = data.get("tags", [])
        rule.execution_count = data.get("execution_count", 0)

        if data.get("last_executed"):
            rule.last_executed = datetime.fromisoformat(data["last_executed"])

        return rule

    def update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()
