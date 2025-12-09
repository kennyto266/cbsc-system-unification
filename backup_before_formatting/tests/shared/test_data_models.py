"""
測試共享數據模型
"""

from datetime import datetime

import pytest
from shared.config.data_models import (
    CustomIndicator,
    LayoutConfig,
    OptimizationMethod,
    OptimizationResult,
    ParameterRange,
    StrategyTemplate,
    StrategyType,
    UserConfig,
)


class TestDataModels:
    """數據模型測試類"""

    def test_user_config_creation(self):
        """測試用戶配置創建"""
        config = UserConfig(
            username="test_user",
            email="test@example.com",
            risk_tolerance=0.7,
        )
        assert config.username == "test_user"
        assert config.email == "test@example.com"
        assert config.risk_tolerance == 0.7
        assert config.user_id is not None
        assert isinstance(config.created_at, datetime)

    def test_parameter_range_generation(self):
        """測試參數範圍生成"""
        param_range = ParameterRange(
            name="period",
            min_value=5,
            max_value=20,
            step=5,
            param_type="int",
        )
        values = param_range.generate_values()
        assert values == [5, 10, 15, 20]

    def test_parameter_range_float(self):
        """測試浮點數參數範圍"""
        param_range = ParameterRange(
            name="threshold",
            min_value=0.1,
            max_value=0.9,
            step=0.2,
            param_type="float",
        )
        values = param_range.generate_values()
        assert 0.1 in values
        assert 0.9 in values

    def test_strategy_template_creation(self):
        """測試策略模板創建"""
        template = StrategyTemplate(
            name="KDJ策略",
            description="隨機指標策略",
            strategy_type=StrategyType.KDJ,
            parameters={"k_period": 9, "d_period": 3},
        )
        assert template.name == "KDJ策略"
        assert template.strategy_type == StrategyType.KDJ
        assert template.parameters["k_period"] == 9

    def test_strategy_template_parameter_combinations(self):
        """測試策略參數組合生成"""
        template = StrategyTemplate(
            name="測試策略",
            strategy_type=StrategyType.MA,
        )
        template.parameter_ranges = [
            ParameterRange("period", 5, 15, 5, "int"),
            ParameterRange("threshold", 0.1, 0.3, 0.1, "float"),
        ]
        combinations = template.get_parameter_combinations()
        # period: [5, 10, 15] (3個值) * threshold: [0.1, 0.2] (2個值) = 6個組合
        assert len(combinations) == 6
        assert all("period" in combo for combo in combinations)
        assert all("threshold" in combo for combo in combinations)

    def test_optimization_result_creation(self):
        """測試優化結果創建"""
        result = OptimizationResult(
            strategy_template_id="test_strategy",
            total_combinations=100,
            evaluated_combinations=50,
        )
        assert result.total_combinations == 100
        assert result.evaluated_combinations == 50
        assert result.status == "running"
        assert result.progress == 50.0

    def test_optimization_result_completion(self):
        """測試優化完成"""
        result = OptimizationResult(
            total_combinations=100,
            evaluated_combinations=100,
        )
        result.status = "completed"
        result.completed_at = datetime.now()
        assert result.is_completed
        assert result.progress == 100.0

    def test_custom_indicator_creation(self):
        """測試自定義指標創建"""
        indicator = CustomIndicator(
            name="自定義指標",
            description="測試自定義指標",
            category="trend",
            calculation_code="def calculate(data):\n    return data['close']",
        )
        assert indicator.name == "自定義指標"
        assert indicator.category == "trend"
        assert indicator.indicator_id is not None

    def test_custom_indicator_validation(self):
        """測試自定義指標驗證"""
        indicator = CustomIndicator(
            name="",
            description="",
        )
        errors = indicator.validate()
        assert len(errors) > 0
        assert "指標名稱不能為空" in errors

    def test_layout_config_creation(self):
        """測試佈局配置創建"""
        layout = LayoutConfig(
            name="默認儀表板",
            layout_type="dashboard",
            components=[
                {"id": "chart1", "type": "line_chart"},
                {"id": "table1", "type": "data_table"},
            ],
        )
        assert layout.name == "默認儀表板"
        assert layout.layout_type == "dashboard"
        assert len(layout.components) == 2

    def test_layout_config_get_component(self):
        """測試獲取佈局組件"""
        layout = LayoutConfig(
            components=[
                {"id": "chart1", "type": "line_chart", "title": "K線圖"},
            ],
        )
        component = layout.get_component_by_id("chart1")
        assert component is not None
        assert component["type"] == "line_chart"

    def test_data_model_registry(self):
        """測試數據模型註冊表"""
        from shared.config.data_models import (
            create_model,
            get_model_class,
        )

        model_class = get_model_class("UserConfig")
        assert model_class == UserConfig

        model = create_model(
            "StrategyTemplate",
            name="測試策略",
            strategy_type=StrategyType.MA,
        )
        assert isinstance(model, StrategyTemplate)
        assert model.name == "測試策略"

    def test_invalid_model_creation(self):
        """測試無效模型創建"""
        from shared.config.data_models import create_model

        with pytest.raises(ValueError):
            create_model("NonExistentModel")


class TestEnums:
    """枚舉類測試"""

    def test_strategy_type_enum(self):
        """測試策略類型枚舉"""
        assert StrategyType.MA.value == "moving_average"
        assert StrategyType.RSI.value == "rsi"
        assert StrategyType.CUSTOM.value == "custom"

    def test_optimization_method_enum(self):
        """測試優化方法枚舉"""
        assert OptimizationMethod.GRID_SEARCH.value == "grid_search"
        assert OptimizationMethod.BAYESIAN.value == "bayesian"
