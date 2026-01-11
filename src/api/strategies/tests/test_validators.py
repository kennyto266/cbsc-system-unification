"""
驗證器測試 - 簡化版本
Validators Tests - Simplified Version
"""

import pytest
from datetime import datetime, timedelta

from ..utils.validators import StrategyValidator, ValidationError
from ..schemas import StrategyCreate, StrategyUpdate, ExecutionRequest
from ..models import (
    Strategy, StrategyType, StrategyStatus, RiskLevel, ExecutionStatus
)


class TestStrategyValidator:
    """策略驗證器測試類"""

    @pytest.fixture
    def validator(self):
        """創建驗證器fixture"""
        return StrategyValidator()

    @pytest.fixture
    def sample_strategy(self):
        """示例策略對象"""
        return Strategy(
            id="test_strategy_001",
            name="測試策略",
            description="測試用策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={},
            status=StrategyStatus.INACTIVE,
            is_active=False,
            user_id=1,
            risk_level=RiskLevel.MEDIUM
        )

    @pytest.mark.asyncio
    async def test_validate_create_request_valid(self, validator):
        """測試驗證有效的創建請求"""
        request = StrategyCreate(
            name="測試策略",
            description="這是一個測試策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70
            },
            risk_level=RiskLevel.MEDIUM
        )

        # 不應該拋出異常
        await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_empty_name(self, validator):
        """測試驗證空名稱的創建請求"""
        # 策略Create在创建时就会验证名称长度
        with pytest.raises(Exception):  # 捕获Pydantic验证错误
            request = StrategyCreate(
                name="",  # 空名稱
                description="測試策略",
                strategy_type=StrategyType.DIRECT_RSI,
                risk_level=RiskLevel.MEDIUM
            )
            await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_long_name(self, validator):
        """測試驗證過長名稱的創建請求"""
        long_name = "a" * 101  # 超過100字符限制
        request = StrategyCreate(
            name=long_name,
            description="測試策略",
            strategy_type=StrategyType.DIRECT_RSI,
            risk_level=RiskLevel.MEDIUM
        )

        with pytest.raises(ValidationError, match="策略名称长度必须在1-100之间"):
            await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_empty_description(self, validator):
        """測試驗證空描述的創建請求"""
        request = StrategyCreate(
            name="測試策略",
            description="",  # 空描述
            strategy_type=StrategyType.DIRECT_RSI,
            risk_level=RiskLevel.MEDIUM
        )

        with pytest.raises(ValidationError, match="策略描述是必填字段"):
            await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_long_description(self, validator):
        """測試驗證過長描述的創建請求"""
        long_desc = "a" * 501  # 超過500字符限制
        request = StrategyCreate(
            name="測試策略",
            description=long_desc,
            strategy_type=StrategyType.DIRECT_RSI,
            risk_level=RiskLevel.MEDIUM
        )

        with pytest.raises(ValidationError, match="策略描述长度必须在1-500之间"):
            await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_invalid_name_format(self, validator):
        """測試驗證無效名稱格式"""
        request = StrategyCreate(
            name="策略@#$",  # 包含特殊字符
            description="測試策略",
            strategy_type=StrategyType.DIRECT_RSI,
            risk_level=RiskLevel.MEDIUM
        )

        with pytest.raises(ValidationError, match="策略名称格式不正确"):
            await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_valid_chinese_name(self, validator):
        """測試驗證有效的中文策略名稱"""
        request = StrategyCreate(
            name="RSI策略測試",
            description="這是一個測試策略",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={"rsi_period": 14},
            risk_level=RiskLevel.MEDIUM
        )

        # 不應該拋出異常
        await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_create_request_valid_english_name(self, validator):
        """測試驗證有效的英文策略名稱"""
        request = StrategyCreate(
            name="RSI-Strategy_Test",
            description="Test strategy for RSI",
            strategy_type=StrategyType.DIRECT_RSI,
            parameters={"rsi_period": 14},
            risk_level=RiskLevel.MEDIUM
        )

        # 不應該拋出異常
        await validator.validate_create_request(request)

    @pytest.mark.asyncio
    async def test_validate_update_request_valid(self, validator, sample_strategy):
        """測試驗證有效的更新請求"""
        request = StrategyUpdate(
            name="更新後的策略名稱",
            description="更新後的策略描述",
            parameters={"rsi_period": 20}
        )

        # 不應該拋出異常
        await validator.validate_update_request(request, sample_strategy)

    @pytest.mark.asyncio
    async def test_validate_update_request_empty_name(self, validator, sample_strategy):
        """測試驗證空名稱的更新請求"""
        request = StrategyUpdate(name="")

        with pytest.raises(ValidationError, match="策略名称长度必须在1-100之间"):
            await validator.validate_update_request(request, sample_strategy)

    @pytest.mark.asyncio
    async def test_validate_update_request_long_name(self, validator, sample_strategy):
        """測試驗證過長名稱的更新請求"""
        long_name = "a" * 101
        request = StrategyUpdate(name=long_name)

        with pytest.raises(ValidationError, match="策略名称长度必须在1-100之间"):
            await validator.validate_update_request(request, sample_strategy)

    @pytest.mark.asyncio
    async def test_validate_update_request_invalid_name_format(self, validator, sample_strategy):
        """測試驗證無效名稱格式的更新請求"""
        request = StrategyUpdate(name="策略@#$")

        with pytest.raises(ValidationError, match="策略名称格式不正确"):
            await validator.validate_update_request(request, sample_strategy)

    @pytest.mark.asyncio
    async def test_validate_update_request_long_description(self, validator, sample_strategy):
        """測試驗證過長描述的更新請求"""
        long_desc = "a" * 501
        request = StrategyUpdate(description=long_desc)

        with pytest.raises(ValidationError, match="策略描述长度必须在1-500之间"):
            await validator.validate_update_request(request, sample_strategy)

    @pytest.mark.asyncio
    async def test_validate_execution_request_valid(self, validator):
        """測試驗證有效的執行請求"""
        request = ExecutionRequest(
            strategy_id="test_strategy_001",
            execution_mode="backtest",
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now()
        )

        # 不應該拋出異常
        await validator.validate_execution_request(request)

    @pytest.mark.asyncio
    async def test_validate_execution_request_invalid_mode(self, validator):
        """測試驗證無效的執行模式"""
        request = ExecutionRequest(
            strategy_id="test_strategy_001",
            execution_mode="invalid_mode"  # 無效模式
        )

        with pytest.raises(ValidationError, match="无效的执行模式"):
            await validator.validate_execution_request(request)

    @pytest.mark.asyncio
    async def test_validate_execution_request_start_after_end(self, validator):
        """測試驗證開始時間晚於結束時間"""
        request = ExecutionRequest(
            strategy_id="test_strategy_001",
            execution_mode="backtest",
            start_time=datetime.now(),
            end_time=datetime.now() - timedelta(days=30)  # 結束時間早於開始時間
        )

        with pytest.raises(ValidationError, match="开始日期必须早于结束日期"):
            await validator.validate_execution_request(request)

    @pytest.mark.asyncio
    async def test_validate_execution_request_too_long_period(self, validator):
        """測試驗證過長的執行時間範圍"""
        request = ExecutionRequest(
            strategy_id="test_strategy_001",
            execution_mode="backtest",
            start_time=datetime.now() - timedelta(days=400),  # 超過1年
            end_time=datetime.now()
        )

        with pytest.raises(ValidationError, match="日期范围不能超过1年"):
            await validator.validate_execution_request(request)

    @pytest.mark.asyncio
    async def test_validate_execution_request_future_start_time(self, validator):
        """測試驗證未來的開始時間"""
        request = ExecutionRequest(
            strategy_id="test_strategy_001",
            execution_mode="backtest",
            start_time=datetime.now() + timedelta(days=30),  # 未來時間
            end_time=datetime.now() + timedelta(days=60)
        )

        with pytest.raises(ValidationError, match="开始日期不能是未来时间"):
            await validator.validate_execution_request(request)


class TestBaseValidator:
    """基礎驗證器測試類"""

    @pytest.fixture
    def validator(self):
        """創建基礎驗證器fixture"""
        from ..utils.validators import BaseValidator
        return BaseValidator()

    def test_validate_required_success(self, validator):
        """測試驗證必填字段成功"""
        # 不應該拋出異常
        validator.validate_required("test_value", "測試字段")

    def test_validate_required_failure_none(self, validator):
        """測試驗證必填字段失敗 - None值"""
        with pytest.raises(ValidationError, match="测试字段是必填字段"):
            validator.validate_required(None, "測試字段")

    def test_validate_required_failure_empty(self, validator):
        """測試驗證必填字段失敗 - 空字符串"""
        with pytest.raises(ValidationError, match="测试字段是必填字段"):
            validator.validate_required("", "測試字段")

    def test_validate_length_success(self, validator):
        """測試驗證字符串長度成功"""
        # 不應該拋出異常
        validator.validate_length("test", 2, 10, "測試字段")

    def test_validate_length_too_short(self, validator):
        """測試驗證字符串過短"""
        with pytest.raises(ValidationError, match="測試字段長度必須在2-10之間"):
            validator.validate_length("t", 2, 10, "測試字段")

    def test_validate_length_too_long(self, validator):
        """測試驗證字符串過長"""
        long_str = "a" * 11
        with pytest.raises(ValidationError, match="測試字段長度必須在2-10之間"):
            validator.validate_length(long_str, 2, 10, "測試字段")

    def test_validate_range_success(self, validator):
        """測試驗證範圍成功"""
        # 不應該拋出異常
        validator.validate_range(5, 1, 10, "測試字段")

    def test_validate_range_too_low(self, validator):
        """測試驗證數值過小"""
        with pytest.raises(ValidationError, match="測試字段必須在1-10之間"):
            validator.validate_range(0, 1, 10, "測試字段")

    def test_validate_range_too_high(self, validator):
        """測試驗證數值過大"""
        with pytest.raises(ValidationError, match="測試字段必須在1-10之間"):
            validator.validate_range(11, 1, 10, "測試字段")

    def test_validate_regex_success(self, validator):
        """測試驗證正則表達式成功"""
        # 不應該拋出異常
        validator.validate_regex("test123", r'^[a-z0-9]+$', "測試字段")

    def test_validate_regex_failure(self, validator):
        """測試驗證正則表達式失敗"""
        with pytest.raises(ValidationError, match="测试字段格式不正确"):
            validator.validate_regex("test@#$", r'^[a-z0-9]+$', "測試字段")

    def test_validate_email_success(self, validator):
        """測試驗證郵箱成功"""
        # 不應該拋出異常
        validator.validate_email("test@example.com")

    def test_validate_email_invalid(self, validator):
        """測試驗證無效郵箱"""
        with pytest.raises(ValidationError, match="邮箱格式不正确"):
            validator.validate_email("invalid_email")

    def test_validate_positive_number_success(self, validator):
        """測試驗證正數成功"""
        # 不應該拋出異常
        validator.validate_positive_number(5, "測試字段")

    def test_validate_positive_number_zero(self, validator):
        """測試驗證零值"""
        with pytest.raises(ValidationError, match="測試字段必須是正數"):
            validator.validate_positive_number(0, "測試字段")

    def test_validate_positive_number_negative(self, validator):
        """測試驗證負數"""
        with pytest.raises(ValidationError, match="測試字段必須是正數"):
            validator.validate_positive_number(-5, "測試字段")

    def test_validate_non_negative_success(self, validator):
        """測試驗證非負數成功"""
        # 不應該拋出異常
        validator.validate_non_negative(0, "測試字段")
        validator.validate_non_negative(5, "測試字段")

    def test_validate_non_negative_failure(self, validator):
        """測試驗證負數失敗"""
        with pytest.raises(ValidationError, match="测试字段不能是负数"):
            validator.validate_non_negative(-5, "測試字段")

    def test_validate_percentage_success(self, validator):
        """測試驗證百分比成功"""
        # 不應該拋出異常
        validator.validate_percentage(0.5, "測試字段")
        validator.validate_percentage(0.0, "測試字段")
        validator.validate_percentage(1.0, "測試字段")

    def test_validate_percentage_negative(self, validator):
        """測試驗證負數百分比"""
        with pytest.raises(ValidationError, match="測試字段必須在0.0-1.0之間"):
            validator.validate_percentage(-0.1, "測試字段")

    def test_validate_percentage_too_high(self, validator):
        """測試驗證過高百分比"""
        with pytest.raises(ValidationError, match="測試字段必須在0.0-1.0之間"):
            validator.validate_percentage(1.1, "測試字段")

    def test_validate_date_range_success(self, validator):
        """測試驗證日期範圍成功"""
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()

        # 不應該拋出異常
        validator.validate_date_range(start_date, end_date)

    def test_validate_date_range_start_after_end(self, validator):
        """測試驗證開始日期晚於結束日期"""
        start_date = datetime.now()
        end_date = datetime.now() - timedelta(days=30)

        with pytest.raises(ValidationError, match="开始日期必须早于结束日期"):
            validator.validate_date_range(start_date, end_date)


if __name__ == "__main__":
    # 運行測試
    import asyncio
    asyncio.run(pytest.main([__file__, "-v"]))