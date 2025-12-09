"""Test CustomIndicator Model.

Tests for the CustomIndicator Pydantic model.
"""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from src.core.custom_indicator import CustomIndicator, OutputType, ParameterDefinition


class TestParameterDefinition:
    """Test suite for ParameterDefinition model."""

    def test_valid_parameter_definition(self):
        """Test creating a valid ParameterDefinition."""
        param_def = ParameterDefinition(
            type="int", default=14, min=2, max=100, description="計算週期"
        )

        assert param_def.type == "int"
        assert param_def.default == 14
        assert param_def.min == 2
        assert param_def.max == 100
        assert param_def.description == "計算週期"

    def test_default_none(self):
        """Test default=None for optional fields."""
        param_def = ParameterDefinition(type="float", description="測試參數")

        assert param_def.type == "float"
        assert param_def.default is None
        assert param_def.min is None
        assert param_def.max is None

    def test_type_validation(self):
        """Test type field validation."""
        # Valid types
        for param_type in ["int", "float", "str", "bool"]:
            param_def = ParameterDefinition(type=param_type)
            assert param_def.type == param_type

        # Invalid type
        with pytest.raises(ValueError):
            ParameterDefinition(type="invalid_type")

    def test_range_validation(self):
        """Test min and max validation."""
        # Valid ranges
        param_def = ParameterDefinition(type="int", min=0, max=100)
        assert param_def.min == 0
        assert param_def.max == 100

        # Invalid: min > max
        with pytest.raises(Exception):  # Pydantic validation error
            ParameterDefinition(type="int", min=100, max=0)


class TestCustomIndicator:
    """Test suite for CustomIndicator model."""

    def test_valid_custom_indicator(self):
        """Test creating a valid CustomIndicator instance."""
        user_id = uuid4()
        indicator = CustomIndicator(
            name="自定義RSI變體",
            description="基於成交量的RSI指標",
            code="def custom_rsi(close, volume, period=14):\\n    # 實現自定義RSI邏輯\\n    return rsi_values",
            parameters={
                "period": ParameterDefinition(
                    type="int", default=14, min=2, max=100, description="計算週期"
                ),
                "volume_weighted": ParameterDefinition(
                    type="bool", default=True, description="是否使用成交量加權"
                ),
            },
            output_type=OutputType.SERIES,
            user_id=user_id,
        )

        assert indicator.name == "自定義RSI變體"
        assert indicator.code.startswith("def custom_rsi")
        assert "period" in indicator.parameters
        assert indicator.output_type == OutputType.SERIES
        assert indicator.user_id == user_id

    def test_default_values(self):
        """Test default values for CustomIndicator."""
        user_id = uuid4()
        indicator = CustomIndicator(
            name="Test Indicator", code="def test():\n    pass", user_id=user_id
        )

        assert indicator.description == ""
        assert indicator.parameters == {}
        assert indicator.output_type == OutputType.SERIES
        assert indicator.is_valid is False
        assert indicator.validation_errors == []

    def test_output_type_validation(self):
        """Test output_type field validation."""
        user_id = uuid4()

        # Valid output types
        for output_type in [OutputType.SINGLE, OutputType.SERIES, OutputType.MULTIPLE]:
            indicator = CustomIndicator(
                name="Test",
                code="def test():\n    pass",
                output_type=output_type,
                user_id=user_id,
            )
            assert indicator.output_type == output_type

        # Valid string types (will be converted to OutputType)
        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            output_type="single",  # String value
            user_id=user_id,
        )
        assert indicator.output_type == OutputType.SINGLE

        # Invalid type
        with pytest.raises(ValueError):
            CustomIndicator(
                name="Test",
                code="def test():\n    pass",
                output_type="invalid_type",
                user_id=user_id,
            )

    def test_name_validation(self):
        """Test name field validation."""
        user_id = uuid4()

        # Valid names
        indicator = CustomIndicator(
            name="A", code="def test():\n    pass", user_id=user_id  # 1 character
        )
        assert indicator.name == "A"

        indicator = CustomIndicator(
            name="A" * 50,  # 50 characters
            code="def test():\n    pass",
            user_id=user_id,
        )
        assert len(indicator.name) == 50

        # Invalid: empty name
        with pytest.raises(ValueError):
            CustomIndicator(name="", code="def test():\n    pass", user_id=user_id)

        # Invalid: too long
        with pytest.raises(ValueError):
            CustomIndicator(
                name="A" * 51,  # 51 characters
                code="def test():\n    pass",
                user_id=user_id,
            )

    def test_code_validation(self):
        """Test code field validation."""
        user_id = uuid4()

        # Valid code
        valid_code = "def test():\n    pass"
        indicator = CustomIndicator(name="Test", code=valid_code, user_id=user_id)
        assert indicator.code == valid_code

        # Invalid: too short
        with pytest.raises(
            ValueError, match="Code must be at least 100 characters long"
        ):
            CustomIndicator(
                name="Test", code="short", user_id=user_id  # Only 5 characters
            )

        # Invalid: too long
        with pytest.raises(
            ValueError, match="Code must be less than 10000 characters long"
        ):
            CustomIndicator(
                name="Test", code="def test():\n    pass" + " " * 10001, user_id=user_id
            )

        # Invalid: no function definition
        with pytest.raises(ValueError, match="Code must contain a function definition"):
            CustomIndicator(name="Test", code="x = 1", user_id=user_id)  # No function

    def test_code_with_lambda(self):
        """Test code with lambda function."""
        user_id = uuid4()

        indicator = CustomIndicator(
            name="Test", code="lambda x: x * 2", user_id=user_id
        )
        assert indicator.code == "lambda x: x * 2"

    def test_validation_errors_validation(self):
        """Test validation_errors field validation."""
        user_id = uuid4()

        # Valid: list of strings
        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            validation_errors=["Error 1", "Error 2"],
        )
        assert len(indicator.validation_errors) == 2

        # Valid: empty list
        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            validation_errors=[],
        )
        assert indicator.validation_errors == []

        # Non - string values will be converted to strings
        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            validation_errors=[123, "Error"],
        )
        assert indicator.validation_errors == ["123", "Error"]

    def test_to_dict(self):
        """Test to_dict method."""
        user_id = uuid4()
        indicator = CustomIndicator(
            name="Test", code="def test():\n    pass", user_id=user_id
        )

        data = indicator.to_dict()
        assert isinstance(data, dict)
        assert data["name"] == "Test"
        assert "created_at" in data

    def test_to_json(self):
        """Test to_json method."""
        user_id = uuid4()
        indicator = CustomIndicator(
            name="Test", code="def test():\n    pass", user_id=user_id
        )

        json_str = indicator.to_json()
        assert isinstance(json_str, str)
        assert "Test" in json_str

    def test_from_json(self):
        """Test from_json class method."""
        user_id = uuid4()
        original = CustomIndicator(
            name="Test",
            description="Test description",
            code="def test():\n    pass",
            user_id=user_id,
        )

        json_str = original.to_json()
        restored = CustomIndicator.from_json(json_str)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.code == original.code

    def test_add_parameter(self):
        """Test add_parameter method."""
        user_id = uuid4()
        indicator = CustomIndicator(
            name="Test", code="def test():\n    pass", user_id=user_id
        )

        assert len(indicator.parameters) == 0

        param_def = ParameterDefinition(type="int", default=14, description="測試參數")

        indicator.add_parameter("period", param_def)

        assert "period" in indicator.parameters
        assert indicator.parameters["period"].default == 14

    def test_remove_parameter(self):
        """Test remove_parameter method."""
        user_id = uuid4()
        param_def = ParameterDefinition(type="int", default=14)
        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            parameters={"period": param_def},
        )

        assert len(indicator.parameters) == 1
        indicator.remove_parameter("period")
        assert len(indicator.parameters) == 0

    def test_get_parameter(self):
        """Test get_parameter method."""
        user_id = uuid4()
        param_def = ParameterDefinition(type="int", default=14, description="測試參數")

        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            parameters={"period": param_def},
        )

        result = indicator.get_parameter("period")
        assert result is not None
        assert result.default == 14

        result = indicator.get_parameter("nonexistent")
        assert result is None

    def test_get_default_parameters(self):
        """Test get_default_parameters method."""
        user_id = uuid4()
        param1 = ParameterDefinition(type="int", default=14)
        param2 = ParameterDefinition(type="float", default=3.14)
        param3 = ParameterDefinition(type="str", default="test")

        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            parameters={"period": param1, "value": param2, "name": param3},
        )

        defaults = indicator.get_default_parameters()
        assert defaults["period"] == 14
        assert defaults["value"] == 3.14
        assert defaults["name"] == "test"

    def test_get_parameter_schema(self):
        """Test get_parameter_schema method."""
        user_id = uuid4()
        param1 = ParameterDefinition(
            type="int", default=14, min=2, max=100, description="計算週期"
        )
        param2 = ParameterDefinition(type="bool", default=True, description="啟用選項")

        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            parameters={"period": param1, "enabled": param2},
        )

        schema = indicator.get_parameter_schema()

        assert "period" in schema
        assert "enabled" in schema
        assert schema["period"]["type"] == "int"
        assert schema["period"]["default"] == 14
        assert schema["period"]["minimum"] == 2
        assert schema["period"]["maximum"] == 100
        assert schema["enabled"]["type"] == "bool"
        assert schema["enabled"]["default"] is True

    def test_clone(self):
        """Test clone method."""
        user_id = uuid4()
        param_def = ParameterDefinition(type="int", default=14)

        original = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            parameters={"period": param_def},
            tags=["tag1"],
        )

        clone = original.clone()

        # Should have different indicator_id
        assert clone.indicator_id != original.indicator_id

        # Other attributes should be the same
        assert clone.name == original.name
        assert clone.code == original.code
        assert clone.user_id == original.user_id
        assert clone.parameters == original.parameters

    def test_is_valid_code(self):
        """Test is_valid_code method."""
        user_id = uuid4()

        # Valid code
        indicator1 = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            is_valid=True,
            validation_errors=[],
        )
        assert indicator1.is_valid_code() is True

        # Invalid: not marked as valid
        indicator2 = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            is_valid=False,
            validation_errors=[],
        )
        assert indicator2.is_valid_code() is False

        # Invalid: has validation errors
        indicator3 = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            is_valid=True,
            validation_errors=["Error 1"],
        )
        assert indicator3.is_valid_code() is False

    def test_get_function_name(self):
        """Test get_function_name method."""
        user_id = uuid4()

        # With def
        indicator1 = CustomIndicator(
            name="Test",
            code="def my_function(x, y):\n    return x + y",
            user_id=user_id,
        )
        assert indicator1.get_function_name() == "my_function"

        # With lambda
        indicator2 = CustomIndicator(
            name="Test", code="lambda x: x * 2", user_id=user_id
        )
        assert indicator2.get_function_name() is None  # Lambda doesn't have a name

        # Multiple functions
        indicator3 = CustomIndicator(
            name="Test",
            code="def helper():\n    pass\n\ndef main():\n    pass",
            user_id=user_id,
        )
        # Should return first function name
        assert indicator3.get_function_name() in ["helper", "main"]

    def test_to_python_code(self):
        """Test to_python_code method."""
        user_id = uuid4()
        code = "def test():\n    return 42"

        indicator = CustomIndicator(name="Test", code=code, user_id=user_id)

        assert indicator.to_python_code() == code

    def test_validate_parameter_value(self):
        """Test validate_parameter_value method."""
        user_id = uuid4()
        param_def = ParameterDefinition(type="int", default=14, min=2, max=100)

        indicator = CustomIndicator(
            name="Test",
            code="def test():\n    pass",
            user_id=user_id,
            parameters={"period": param_def},
        )

        # Valid values
        assert indicator.validate_parameter_value("period", 14) is True
        assert indicator.validate_parameter_value("period", 2) is True  # Min
        assert indicator.validate_parameter_value("period", 100) is True  # Max

        # Invalid: wrong type
        assert indicator.validate_parameter_value("period", "14") is False

        # Invalid: out of range
        assert indicator.validate_parameter_value("period", 1) is False  # Below min
        assert indicator.validate_parameter_value("period", 101) is False  # Above max

        # Invalid: nonexistent parameter
        assert indicator.validate_parameter_value("nonexistent", 14) is False

    def test_set_validation_result(self):
        """Test set_validation_result method."""
        user_id = uuid4()
        indicator = CustomIndicator(
            name="Test", code="def test():\n    pass", user_id=user_id
        )

        assert indicator.is_valid is False
        assert len(indicator.validation_errors) == 0

        indicator.set_validation_result(True, [])

        assert indicator.is_valid is True
        assert len(indicator.validation_errors) == 0

        indicator.set_validation_result(False, ["Error 1", "Error 2"])

        assert indicator.is_valid is False
        assert len(indicator.validation_errors) == 2

    def test_serialization_performance(self):
        """Test serialization performance (should be < 10ms)."""
        import time

        user_id = uuid4()
        indicator = CustomIndicator(
            name="自定義RSI變體",
            description="基於成交量的RSI指標",
            code="def custom_rsi(close, volume, period=14):\\n    # 實現自定義RSI邏輯\\n    return rsi_values",
            parameters={
                "period": ParameterDefinition(
                    type="int", default=14, min=2, max=100, description="計算週期"
                ),
                "volume_weighted": ParameterDefinition(
                    type="bool", default=True, description="是否使用成交量加權"
                ),
            },
            output_type=OutputType.SERIES,
            user_id=user_id,
        )

        # Test serialization
        start = time.perf_counter()
        json_str = indicator.to_json()
        serialize_time = (time.perf_counter() - start) * 1000

        assert serialize_time < 10, f"Serialization took {serialize_time:.2f}ms"

        # Test deserialization
        start = time.perf_counter()
        restored = CustomIndicator.from_json(json_str)
        deserialize_time = (time.perf_counter() - start) * 1000

        assert deserialize_time < 10, f"Deserialization took {deserialize_time:.2f}ms"
