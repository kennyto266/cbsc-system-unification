"""
增强验证器模块
Enhanced Validators Module

职责：
- 提供全面的输入验证
- 支持策略参数验证
- 业务规则验证
- 数据合规性检查
"""

from typing import Any, Dict, List, Optional, Union, Callable, Type
from datetime import datetime, date
from enum import Enum
import re
import json
from pydantic import BaseModel, ValidationError
from fastapi import HTTPException

from ..models import StrategyType, StrategyStatus, RiskLevel
from ..schemas import StrategyCreate, StrategyUpdate
from .errors import ValidationError as BusinessValidationError, ErrorCode


class ValidationRule(str, Enum):
    """验证规则类型"""
    REQUIRED = "required"
    OPTIONAL = "optional"
    FORMAT = "format"
    RANGE = "range"
    LENGTH = "length"
    PATTERN = "pattern"
    CUSTOM = "custom"


class ValidationContext:
    """验证上下文"""

    def __init__(
        self,
        user_id: Optional[int] = None,
        strategy_id: Optional[str] = None,
        operation: Optional[str] = None
    ):
        self.user_id = user_id
        self.strategy_id = strategy_id
        self.operation = operation
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def add_error(
        self,
        field: str,
        message: str,
        code: Optional[ErrorCode] = None,
        value: Any = None
    ):
        """添加验证错误"""
        self.errors.append({
            "field": field,
            "message": message,
            "code": code.value if code else None,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })

    def add_warning(
        self,
        field: str,
        message: str,
        value: Any = None
    ):
        """添加验证警告"""
        self.warnings.append({
            "field": field,
            "message": message,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    def get_errors(self) -> List[Dict[str, Any]]:
        """获取所有错误"""
        return self.errors

    def get_warnings(self) -> List[Dict[str, Any]]:
        """获取所有警告"""
        return self.warnings


class FieldValidator:
    """字段验证器"""

    def __init__(self, field_name: str):
        self.field_name = field_name
        self.rules: List[Tuple[ValidationRule, Any]] = []

    def required(self) -> 'FieldValidator':
        """必填字段"""
        self.rules.append((ValidationRule.REQUIRED, True))
        return self

    def optional(self) -> 'FieldValidator':
        """可选字段"""
        self.rules.append((ValidationRule.OPTIONAL, True))
        return self

    def min_length(self, min_len: int) -> 'FieldValidator':
        """最小长度"""
        self.rules.append((ValidationRule.LENGTH, {"min": min_len}))
        return self

    def max_length(self, max_len: int) -> 'FieldValidator':
        """最大长度"""
        self.rules.append((ValidationRule.LENGTH, {"max": max_len}))
        return self

    def length_range(self, min_len: int, max_len: int) -> 'FieldValidator':
        """长度范围"""
        self.rules.append((ValidationRule.LENGTH, {"min": min_len, "max": max_len}))
        return self

    def pattern(self, pattern: str) -> 'FieldValidator':
        """正则表达式"""
        self.rules.append((ValidationRule.PATTERN, pattern))
        return self

    def email(self) -> 'FieldValidator':
        """邮箱格式"""
        self.rules.append((ValidationRule.FORMAT, "email"))
        return self

    def numeric(self) -> 'FieldValidator':
        """数字"""
        self.rules.append((ValidationRule.FORMAT, "numeric"))
        return self

    def integer(self) -> 'FieldValidator':
        """整数"""
        self.rules.append((ValidationRule.FORMAT, "integer"))
        return self

    def positive(self) -> 'FieldValidator':
        """正数"""
        self.rules.append((ValidationRule.RANGE, {"min": 0}))
        return self

    def range(self, min_val: Any, max_val: Any) -> 'FieldValidator':
        """数值范围"""
        self.rules.append((ValidationRule.RANGE, {"min": min_val, "max": max_val}))
        return self

    def one_of(self, values: List[Any]) -> 'FieldValidator':
        """枚举值"""
        self.rules.append((ValidationRule.CUSTOM, {"type": "enum", "values": values}))
        return self

    def custom(self, validator: Callable[[Any], bool], message: str) -> 'FieldValidator':
        """自定义验证"""
        self.rules.append((ValidationRule.CUSTOM, {"type": "custom", "validator": validator, "message": message}))
        return self

    async def validate(self, value: Any, context: ValidationContext) -> bool:
        """执行验证"""
        is_valid = True

        for rule_type, rule_config in self.rules:
            try:
                if rule_type == ValidationRule.REQUIRED:
                    if value is None or (isinstance(value, str) and not value.strip()):
                        context.add_error(
                            self.field_name,
                            f"{self.field_name}是必填字段",
                            ErrorCode.VALIDATION_ERROR,
                            value
                        )
                        is_valid = False

                elif rule_type == ValidationRule.LENGTH:
                    if isinstance(value, (str, list)):
                        length = len(value)
                        if "min" in rule_config and length < rule_config["min"]:
                            context.add_error(
                                self.field_name,
                                f"{self.field_name}长度不能小于{rule_config['min']}",
                                ErrorCode.VALIDATION_ERROR,
                                value
                            )
                            is_valid = False
                        if "max" in rule_config and length > rule_config["max"]:
                            context.add_error(
                                self.field_name,
                                f"{self.field_name}长度不能大于{rule_config['max']}",
                                ErrorCode.VALIDATION_ERROR,
                                value
                            )
                            is_valid = False

                elif rule_type == ValidationRule.PATTERN:
                    if isinstance(value, str) and not re.match(rule_config, value):
                        context.add_error(
                            self.field_name,
                            f"{self.field_name}格式不正确",
                            ErrorCode.VALIDATION_ERROR,
                            value
                        )
                        is_valid = False

                elif rule_type == ValidationRule.FORMAT:
                    if rule_config == "email" and isinstance(value, str):
                        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
                            context.add_error(
                                self.field_name,
                                f"{self.field_name}必须是有效的邮箱地址",
                                ErrorCode.VALIDATION_ERROR,
                                value
                            )
                            is_valid = False
                    elif rule_config == "numeric" and not isinstance(value, (int, float)):
                        context.add_error(
                            self.field_name,
                            f"{self.field_name}必须是数字",
                            ErrorCode.VALIDATION_ERROR,
                            value
                        )
                        is_valid = False
                    elif rule_config == "integer" and not isinstance(value, int):
                        context.add_error(
                            self.field_name,
                            f"{self.field_name}必须是整数",
                            ErrorCode.VALIDATION_ERROR,
                            value
                        )
                        is_valid = False

                elif rule_type == ValidationRule.RANGE:
                    if isinstance(value, (int, float)):
                        if "min" in rule_config and value < rule_config["min"]:
                            context.add_error(
                                self.field_name,
                                f"{self.field_name}不能小于{rule_config['min']}",
                                ErrorCode.VALIDATION_ERROR,
                                value
                            )
                            is_valid = False
                        if "max" in rule_config and value > rule_config["max"]:
                            context.add_error(
                                self.field_name,
                                f"{self.field_name}不能大于{rule_config['max']}",
                                ErrorCode.VALIDATION_ERROR,
                                value
                            )
                            is_valid = False

                elif rule_type == ValidationRule.CUSTOM:
                    if rule_config["type"] == "enum":
                        if value not in rule_config["values"]:
                            context.add_error(
                                self.field_name,
                                f"{self.field_name}必须是以下值之一: {rule_config['values']}",
                                ErrorCode.VALIDATION_ERROR,
                                value
                            )
                            is_valid = False
                    elif rule_config["type"] == "custom":
                        if not rule_config["validator"](value):
                            context.add_error(
                                self.field_name,
                                rule_config["message"],
                                ErrorCode.VALIDATION_ERROR,
                                value
                            )
                            is_valid = False

            except Exception as e:
                context.add_error(
                    self.field_name,
                    f"验证{self.field_name}时发生错误: {str(e)}",
                    ErrorCode.INTERNAL_SERVER_ERROR,
                    value
                )
                is_valid = False

        return is_valid


class EnhancedStrategyValidator:
    """增强策略验证器"""

    def __init__(self):
        self.parameter_validators: Dict[StrategyType, Dict[str, FieldValidator]] = {}
        self._setup_parameter_validators()

    def _setup_parameter_validators(self):
        """设置参数验证器"""
        # 技术分析策略参数验证
        self.parameter_validators[StrategyType.TECHNICAL] = {
            "symbols": FieldValidator("symbols").required().min_length(1),
            "timeframe": FieldValidator("timeframe").required().one_of(["1m", "5m", "15m", "1h", "4h", "1d"]),
            "indicators": FieldValidator("indicators").required(),
            "stop_loss": FieldValidator("stop_loss").optional().positive(),
            "take_profit": FieldValidator("take_profit").optional().positive(),
        }

        # 量化策略参数验证
        self.parameter_validators[StrategyType.QUANTITATIVE] = {
            "universe": FieldValidator("universe").required(),
            "lookback_period": FieldValidator("lookback_period").required().positive().integer(),
            "rebalance_frequency": FieldValidator("rebalance_frequency").required().one_of(["daily", "weekly", "monthly"]),
            "max_position_size": FieldValidator("max_position_size").optional().positive().range(0, 1),
        }

        # 套利策略参数验证
        self.parameter_validators[StrategyType.ARBITRAGE] = {
            "pairs": FieldValidator("pairs").required().min_length(1),
            "min_spread": FieldValidator("min_spread").required().positive(),
            "max_exposure": FieldValidator("max_exposure").optional().positive(),
        }

    async def validate_create_request(
        self,
        request: StrategyCreate,
        context: Optional[ValidationContext] = None
    ) -> ValidationContext:
        """验证创建策略请求"""
        if context is None:
            context = ValidationContext()

        # 验证基础字段
        await self._validate_basic_fields(request, context)

        # 验证策略类型
        await self._validate_strategy_type(request.strategy_type, context)

        # 验证参数
        await self._validate_strategy_parameters(
            request.parameters,
            request.strategy_type,
            context
        )

        # 验证风险级别
        await self._validate_risk_level(request.risk_level, context)

        # 业务规则验证
        await self._validate_business_rules(request, context)

        return context

    async def validate_update_request(
        self,
        request: StrategyUpdate,
        existing_strategy: Any,
        context: Optional[ValidationContext] = None
    ) -> ValidationContext:
        """验证更新策略请求"""
        if context is None:
            context = ValidationContext(strategy_id=existing_strategy.id)

        # 验证基础字段
        if request.name is not None:
            name_validator = FieldValidator("name").required().min_length(1).max_length(100)
            await name_validator.validate(request.name, context)

        if request.description is not None:
            desc_validator = FieldValidator("description").optional().max_length(500)
            await desc_validator.validate(request.description, context)

        # 验证参数更新
        if request.parameters is not None:
            await self._validate_strategy_parameters(
                request.parameters,
                existing_strategy.strategy_type,
                context
            )

        # 验证风险级别更新
        if request.risk_level is not None:
            await self._validate_risk_level(request.risk_level, context)

        # 验证状态转换
        if request.status is not None:
            await self._validate_status_transition(
                existing_strategy.status,
                request.status,
                context
            )

        return context

    async def _validate_basic_fields(
        self,
        request: StrategyCreate,
        context: ValidationContext
    ):
        """验证基础字段"""
        # 名称验证
        name_validator = FieldValidator("name").required().min_length(1).max_length(100).pattern(r'^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$')
        await name_validator.validate(request.name, context)

        # 描述验证
        desc_validator = FieldValidator("description").optional().max_length(500)
        await desc_validator.validate(request.description, context)

    async def _validate_strategy_type(
        self,
        strategy_type: StrategyType,
        context: ValidationContext
    ):
        """验证策略类型"""
        if strategy_type not in StrategyType:
            context.add_error(
                "strategy_type",
                f"无效的策略类型: {strategy_type}",
                ErrorCode.STRATEGY_INVALID_PARAMETERS,
                strategy_type
            )

    async def _validate_strategy_parameters(
        self,
        parameters: Dict[str, Any],
        strategy_type: StrategyType,
        context: ValidationContext
    ):
        """验证策略参数"""
        if not isinstance(parameters, dict):
            context.add_error(
                "parameters",
                "参数必须是字典格式",
                ErrorCode.STRATEGY_INVALID_PARAMETERS,
                parameters
            )
            return

        # 获取对应的参数验证器
        validators = self.parameter_validators.get(strategy_type, {})

        # 验证每个参数
        for param_name, value in parameters.items():
            validator = validators.get(param_name)
            if validator:
                await validator.validate(value, context)
            else:
                # 未知参数，添加警告
                context.add_warning(
                    "parameters",
                    f"未知参数: {param_name}",
                    param_name
                )

        # 检查必需参数
        for param_name, validator in validators.items():
            if param_name not in parameters:
                # 检查是否是必需参数
                is_required = any(
                    rule[0] == ValidationRule.REQUIRED
                    for rule in validator.rules
                )
                if is_required:
                    context.add_error(
                        "parameters",
                        f"缺少必需参数: {param_name}",
                        ErrorCode.STRATEGY_INVALID_PARAMETERS
                    )

    async def _validate_risk_level(
        self,
        risk_level: RiskLevel,
        context: ValidationContext
    ):
        """验证风险级别"""
        if risk_level not in RiskLevel:
            context.add_error(
                "risk_level",
                f"无效的风险级别: {risk_level}",
                ErrorCode.STRATEGY_INVALID_PARAMETERS,
                risk_level
            )

    async def _validate_business_rules(
        self,
        request: StrategyCreate,
        context: ValidationContext
    ):
        """验证业务规则"""
        # 规则1: 名称不能包含特殊字符
        if "_" in request.name and len(request.name.split("_")) > 5:
            context.add_warning(
                "name",
                "策略名称包含过多下划线，可能影响可读性"
            )

        # 规则2: 检查参数合理性
        if request.strategy_type == StrategyType.TECHNICAL:
            if "stop_loss" in request.parameters and "take_profit" in request.parameters:
                stop_loss = request.parameters["stop_loss"]
                take_profit = request.parameters["take_profit"]
                if isinstance(stop_loss, (int, float)) and isinstance(take_profit, (int, float)):
                    if stop_loss >= take_profit:
                        context.add_error(
                            "parameters",
                            "止损价格必须小于止盈价格",
                            ErrorCode.STRATEGY_INVALID_PARAMETERS
                        )

    async def _validate_status_transition(
        self,
        from_status: StrategyStatus,
        to_status: StrategyStatus,
        context: ValidationContext
    ):
        """验证状态转换"""
        # 定义允许的状态转换
        allowed_transitions = {
            StrategyStatus.INACTIVE: [StrategyStatus.ACTIVE, StrategyStatus.TESTING],
            StrategyStatus.ACTIVE: [StrategyStatus.INACTIVE, StrategyStatus.PAUSED],
            StrategyStatus.PAUSED: [StrategyStatus.ACTIVE, StrategyStatus.INACTIVE],
            StrategyStatus.TESTING: [StrategyStatus.ACTIVE, StrategyStatus.INACTIVE],
        }

        if from_status not in allowed_transitions:
            context.add_error(
                "status",
                f"无效的源状态: {from_status}",
                ErrorCode.STRATEGY_INVALID_STATUS
            )
            return

        if to_status not in allowed_transitions[from_status]:
            context.add_error(
                "status",
                f"不允许从 {from_status} 转换到 {to_status}",
                ErrorCode.STRATEGY_INVALID_STATUS
            )


class BatchOperationValidator:
    """批量操作验证器"""

    async def validate_batch_operation(
        self,
        strategy_ids: List[str],
        operation: str,
        user_id: int,
        context: ValidationContext
    ) -> ValidationContext:
        """验证批量操作"""
        # 验证策略ID列表
        if not strategy_ids:
            context.add_error(
                "strategy_ids",
                "策略ID列表不能为空",
                ErrorCode.VALIDATION_ERROR
            )
            return context

        if len(strategy_ids) > 1000:
            context.add_error(
                "strategy_ids",
                "批量操作策略数量不能超过1000",
                ErrorCode.VALIDATION_ERROR
            )

        # 验证操作类型
        valid_operations = ["activate", "deactivate", "delete", "update", "execute", "stop"]
        if operation not in valid_operations:
            context.add_error(
                "operation",
                f"无效的操作类型: {operation}",
                ErrorCode.STRATEGY_INVALID_STATUS
            )

        # 验证策略ID格式
        id_validator = FieldValidator("strategy_id").pattern(r'^[a-zA-Z0-9_\-\:]+$')
        for strategy_id in strategy_ids:
            await id_validator.validate(strategy_id, context)

        return context


# 验证器工厂
class ValidatorFactory:
    """验证器工厂"""

    @staticmethod
    def get_strategy_validator() -> EnhancedStrategyValidator:
        """获取策略验证器"""
        return EnhancedStrategyValidator()

    @staticmethod
    def get_batch_validator() -> BatchOperationValidator:
        """获取批量操作验证器"""
        return BatchOperationValidator()

    @staticmethod
    def get_validator(validator_type: str) -> Union[EnhancedStrategyValidator, BatchOperationValidator]:
        """获取验证器"""
        validators = {
            "strategy": ValidatorFactory.get_strategy_validator(),
            "batch": ValidatorFactory.get_batch_validator()
        }
        return validators.get(validator_type)


# 验证装饰器
def validate_request(validator_class: Type, context_key: str = "validation_context"):
    """请求验证装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取验证上下文
            context = kwargs.get(context_key)
            if not context:
                context = ValidationContext()
                kwargs[context_key] = context

            # 执行验证
            validator = validator_class()
            if hasattr(validator, 'validate'):
                context = await validator.validate(**kwargs)

            # 检查验证结果
            if context.has_errors():
                raise HTTPException(
                    status_code=400,
                    detail={
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "请求验证失败",
                            "details": context.get_errors()
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                )

            # 继续执行函数
            return await func(*args, **kwargs)
        return wrapper
    return decorator