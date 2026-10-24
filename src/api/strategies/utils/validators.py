"""
验证器工具
Validation Utilities

职责：
- 数据验证
- 参数验证
- 业务规则验证
"""

from typing import Any, Dict, List, Optional, Union
import re
from datetime import datetime, timedelta
from enum import Enum
import logging

from ..models import (
    Strategy, StrategyType, StrategyStatus, RiskLevel,
    ExecutionStatus, SignalType
)
from ..schemas import (
    StrategyCreate, StrategyUpdate, ExecutionRequest,
    UserPreferences
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """验证错误"""
    pass


class BaseValidator:
    """基础验证器"""

    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """验证必填字段"""
        if value is None or value == "":
            raise ValidationError(f"{field_name}是必填字段")

    @staticmethod
    def validate_length(value: str, min_len: int, max_len: int, field_name: str) -> None:
        """验证字符串长度"""
        if len(value) < min_len or len(value) > max_len:
            raise ValidationError(f"{field_name}长度必须在{min_len}-{max_len}之间")

    @staticmethod
    def validate_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], field_name: str) -> None:
        """验证数值范围"""
        if value < min_val or value > max_val:
            raise ValidationError(f"{field_name}必须在{min_val}-{max_val}之间")

    @staticmethod
    def validate_regex(value: str, pattern: str, field_name: str) -> None:
        """验证正则表达式"""
        if not re.match(pattern, value):
            raise ValidationError(f"{field_name}格式不正确")

    @staticmethod
    def validate_email(email: str) -> None:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        BaseValidator.validate_regex(email, pattern, "邮箱")

    @staticmethod
    def validate_positive_number(value: Union[int, float], field_name: str) -> None:
        """验证正数"""
        if value <= 0:
            raise ValidationError(f"{field_name}必须是正数")

    @staticmethod
    def validate_non_negative(value: Union[int, float], field_name: str) -> None:
        """验证非负数"""
        if value < 0:
            raise ValidationError(f"{field_name}不能为负数")

    @staticmethod
    def validate_percentage(value: float, field_name: str) -> None:
        """验证百分比（0-1之间）"""
        BaseValidator.validate_range(value, 0.0, 1.0, field_name)

    @staticmethod
    def validate_date_range(start_date: datetime, end_date: datetime) -> None:
        """验证日期范围"""
        if start_date >= end_date:
            raise ValidationError("开始日期必须早于结束日期")

        # 检查日期范围不能超过一年
        if end_date - start_date > timedelta(days=365):
            raise ValidationError("日期范围不能超过一年")


class StrategyValidator(BaseValidator):
    """策略验证器"""

    async def validate_create_request(self, request: StrategyCreate) -> None:
        """
        验证创建策略请求
        """
        # 验证名称
        self.validate_required(request.name, "策略名称")
        self.validate_length(request.name, 1, 100, "策略名称")
        self.validate_regex(request.name, r'^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$', "策略名称")

        # 验证描述
        self.validate_required(request.description, "策略描述")
        self.validate_length(request.description, 1, 500, "策略描述")

        # 验证策略类型
        if not isinstance(request.strategy_type, StrategyType):
            raise ValidationError("无效的策略类型")

        # 验证参数
        await self._validate_strategy_parameters(request.parameters, request.strategy_type)

        # 验证风险等级
        if not isinstance(request.risk_level, RiskLevel):
            raise ValidationError("无效的风险等级")

        # 验证模板（如果指定）
        if request.template_id:
            await self._validate_template(request.template_id, request.strategy_type)

    async def validate_update_request(self, request: StrategyUpdate, strategy: Strategy) -> None:
        """
        验证更新策略请求
        """
        # 验证名称（如果提供）
        if request.name:
            self.validate_length(request.name, 1, 100, "策略名称")
            self.validate_regex(request.name, r'^[a-zA-Z0-9_\-\u4e00-\u9fa5]+$', "策略名称")

        # 验证描述（如果提供）
        if request.description:
            self.validate_length(request.description, 1, 500, "策略描述")

        # 验证参数（如果提供）
        if request.parameters:
            await self._validate_strategy_parameters(request.parameters, strategy.strategy_type)

        # 验证状态转换
        if request.status:
            await self._validate_status_transition(strategy.status, request.status)

    async def _validate_strategy_parameters(
        self,
        parameters: Dict[str, Any],
        strategy_type: StrategyType
    ) -> None:
        """
        验证策略参数
        """
        if not isinstance(parameters, dict):
            raise ValidationError("参数必须是字典类型")

        # 根据策略类型验证参数
        if strategy_type == StrategyType.DIRECT_RSI:
            self._validate_rsi_parameters(parameters)
        elif strategy_type == StrategyType.DUAL_RSI:
            self._validate_dual_rsi_parameters(parameters)
        elif strategy_type == StrategyType.CUSTOM:
            # 自定义策略参数验证
            self._validate_custom_parameters(parameters)

    def _validate_rsi_parameters(self, parameters: Dict[str, Any]) -> None:
        """验证RSI策略参数"""
        # RSI周期
        if "rsi_period" in parameters:
            self.validate_range(parameters["rsi_period"], 2, 100, "RSI周期")

        # RSI超卖线
        if "rsi_oversold" in parameters:
            self.validate_range(parameters["rsi_oversold"], 0, 50, "RSI超卖线")

        # RSI超买线
        if "rsi_overbought" in parameters:
            self.validate_range(parameters["rsi_overbought"], 50, 100, "RSI超买线")

        # 检查超卖线 < 超买线
        if "rsi_oversold" in parameters and "rsi_overbought" in parameters:
            if parameters["rsi_oversold"] >= parameters["rsi_overbought"]:
                raise ValidationError("RSI超卖线必须小于超买线")

        # 止损
        if "stop_loss" in parameters:
            self.validate_percentage(parameters["stop_loss"], "止损比例")

        # 止盈
        if "take_profit" in parameters:
            self.validate_percentage(parameters["take_profit"], "止盈比例")

    def _validate_dual_rsi_parameters(self, parameters: Dict[str, Any]) -> None:
        """验证双RSI策略参数"""
        # 快速RSI周期
        if "fast_rsi_period" in parameters:
            self.validate_range(parameters["fast_rsi_period"], 2, 20, "快速RSI周期")

        # 慢速RSI周期
        if "slow_rsi_period" in parameters:
            self.validate_range(parameters["slow_rsi_period"], 10, 50, "慢速RSI周期")

        # 检查快速RSI < 慢速RSI
        if "fast_rsi_period" in parameters and "slow_rsi_period" in parameters:
            if parameters["fast_rsi_period"] >= parameters["slow_rsi_period"]:
                raise ValidationError("快速RSI周期必须小于慢速RSI周期")

        # 信号阈值
        if "signal_threshold" in parameters:
            self.validate_range(parameters["signal_threshold"], 0.5, 1.0, "信号阈值")

    def _validate_custom_parameters(self, parameters: Dict[str, Any]) -> None:
        """验证自定义策略参数"""
        # 基础验证
        if len(parameters) == 0:
            raise ValidationError("自定义策略必须至少有一个参数")

        # 验证参数名和值
        for key, value in parameters.items():
            # 参数名验证
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValidationError(f"参数名 '{key}' 格式不正确")

            # 参数值不能为None
            if value is None:
                raise ValidationError(f"参数 '{key}' 的值不能为空")

    async def _validate_template(self, template_id: str, strategy_type: StrategyType) -> None:
        """验证模板"""
        from ..models import StrategyTemplates
        template = StrategyTemplates.get_template(template_id)
        if not template:
            raise ValidationError(f"模板不存在: {template_id}")

        if template.strategy_type != strategy_type:
            raise ValidationError(f"模板类型与策略类型不匹配")

    async def _validate_status_transition(
        self,
        current_status: StrategyStatus,
        new_status: StrategyStatus
    ) -> None:
        """验证状态转换"""
        # 定义允许的状态转换
        allowed_transitions = {
            StrategyStatus.INACTIVE: [StrategyStatus.ACTIVE, StrategyStatus.ERROR],
            StrategyStatus.ACTIVE: [StrategyStatus.INACTIVE, StrategyStatus.PAUSED, StrategyStatus.ERROR],
            StrategyStatus.PAUSED: [StrategyStatus.ACTIVE, StrategyStatus.INACTIVE],
            StrategyStatus.ERROR: [StrategyStatus.INACTIVE]
        }

        if new_status not in allowed_transitions.get(current_status, []):
            raise ValidationError(f"不能从状态 {current_status.value} 转换到 {new_status.value}")


class ExecutionValidator(BaseValidator):
    """执行验证器"""

    async def validate_execution_request(
        self,
        request: ExecutionRequest,
        strategy: Strategy
    ) -> None:
        """
        验证执行请求
        """
        # 验证执行模式
        if request.execution_mode not in ["backtest", "real_time"]:
            raise ValidationError("无效的执行模式")

        # 验证日期范围（如果提供）
        if request.start_time and request.end_time:
            self.validate_date_range(request.start_time, request.end_time)

            # 回测的日期范围不能超过两年
            if request.execution_mode == "backtest":
                if request.end_time - request.start_time > timedelta(days=730):
                    raise ValidationError("回测时间范围不能超过两年")

        # 验证策略状态
        if not strategy.is_active:
            raise ValidationError("只能执行激活的策略")

        # 验证策略是否有参数
        if not strategy.parameters:
            raise ValidationError("策略缺少必要参数")

        # 验证参数覆盖（如果提供）
        if request.parameters_override:
            await self._validate_parameters_override(
                request.parameters_override,
                strategy.strategy_type
            )

    async def _validate_parameters_override(
        self,
        parameters_override: Dict[str, Any],
        strategy_type: StrategyType
    ) -> None:
        """
        验证参数覆盖
        """
        # 使用策略参数验证器验证
        strategy_validator = StrategyValidator()
        await strategy_validator._validate_strategy_parameters(
            parameters_override,
            strategy_type
        )


class PersonalDataValidator(BaseValidator):
    """个人数据验证器"""

    async def validate_preferences(self, preferences: UserPreferences) -> None:
        """
        验证用户偏好设置
        """
        # 验证刷新间隔
        if preferences.auto_refresh_interval:
            self.validate_range(
                preferences.auto_refresh_interval,
                5,
                300,
                "自动刷新间隔"
            )

        # 验证通知设置
        if preferences.notification_settings:
            self._validate_notification_settings(preferences.notification_settings)

        # 验证仪表板布局
        if preferences.dashboard_layout:
            self._validate_dashboard_layout(preferences.dashboard_layout)

    def _validate_notification_settings(self, settings: Dict[str, Any]) -> None:
        """
        验证通知设置
        """
        if not isinstance(settings, dict):
            raise ValidationError("通知设置必须是字典类型")

        # 验证通知类型
        valid_notification_types = [
            "email", "sms", "push", "strategy_alerts",
            "market_alerts", "system_updates"
        ]

        for key, value in settings.items():
            if key not in valid_notification_types:
                raise ValidationError(f"无效的通知类型: {key}")

            if not isinstance(value, bool):
                raise ValidationError(f"通知设置 '{key}' 必须是布尔值")

    def _validate_dashboard_layout(self, layout: Dict[str, Any]) -> None:
        """
        验证仪表板布局
        """
        if not isinstance(layout, dict):
            raise ValidationError("仪表板布局必须是字典类型")

        # 验证布局组件
        valid_components = [
            "chart_position", "table_position", "sidebar_position",
            "theme", "chart_type", "time_range"
        ]

        for key, value in layout.items():
            if key not in valid_components:
                raise ValidationError(f"无效的布局组件: {key}")

            # 验证特定组件的值
            if key.endswith("_position") and value not in ["left", "right", "top", "bottom"]:
                raise ValidationError(f"无效的位置设置: {value}")
            elif key == "theme" and value not in ["light", "dark", "auto"]:
                raise ValidationError(f"无效的主题设置: {value}")
            elif key == "chart_type" and value not in ["line", "candlestick", "area"]:
                raise ValidationError(f"无效的图表类型: {value}")


# 验证器工厂
class ValidatorFactory:
    """验证器工厂"""

    @staticmethod
    def get_validator(validator_type: str) -> BaseValidator:
        """
        获取验证器实例
        """
        validators = {
            "strategy": StrategyValidator(),
            "execution": ExecutionValidator(),
            "personal": PersonalDataValidator()
        }

        validator = validators.get(validator_type)
        if not validator:
            raise ValueError(f"未知的验证器类型: {validator_type}")

        return validator