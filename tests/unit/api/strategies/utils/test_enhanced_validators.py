"""
Unit tests for Enhanced Validators
Tests input validation and custom validation rules
"""

import pytest
from datetime import datetime, date
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.api.strategies.utils.enhanced_validators import (
    ValidationContext,
    ValidationRule,
    FieldValidator,
    ValidatorFactory,
    BatchOperationValidator,
    StrategyValidator,
    ParameterValidator
)
from src.api.strategies.utils.errors import ValidationError, ErrorCode
from src.api.strategies.models import StrategyType, StrategyStatus, RiskLevel


class TestValidationContext:
    """Test suite for ValidationContext"""

    def test_validation_context_initialization(self):
        """Test ValidationContext initialization"""
        # Arrange & Act
        context = ValidationContext(
            user_id=1,
            strategy_id="strategy_123",
            operation="create"
        )

        # Assert
        assert context.user_id == 1
        assert context.strategy_id == "strategy_123"
        assert context.operation == "create"
        assert context.errors == []
        assert context.warnings == []

    def test_add_error(self):
        """Test adding validation error"""
        # Arrange
        context = ValidationContext()

        # Act
        context.add_error(
            field="name",
            message="Name is required",
            code=ErrorCode.VALIDATION_FAILED,
            value=""
        )

        # Assert
        assert len(context.errors) == 1
        error = context.errors[0]
        assert error["field"] == "name"
        assert error["message"] == "Name is required"
        assert error["code"] == ErrorCode.VALIDATION_FAILED.value
        assert error["value"] == ""
        assert "timestamp" in error

    def test_add_warning(self):
        """Test adding validation warning"""
        # Arrange
        context = ValidationContext()

        # Act
        context.add_warning(
            field="risk_level",
            message="High risk level detected",
            value="high"
        )

        # Assert
        assert len(context.warnings) == 1
        warning = context.warnings[0]
        assert warning["field"] == "risk_level"
        assert warning["message"] == "High risk level detected"
        assert warning["value"] == "high"
        assert "timestamp" in warning

    def test_has_errors(self):
        """Test has_errors method"""
        # Arrange
        context = ValidationContext()

        # Assert initially no errors
        assert not context.has_errors()

        # Act - Add an error
        context.add_error("field", "Error message")

        # Assert - Now has errors
        assert context.has_errors()

    def test_get_errors_and_warnings(self):
        """Test retrieving errors and warnings"""
        # Arrange
        context = ValidationContext()
        context.add_error("field1", "Error 1")
        context.add_error("field2", "Error 2")
        context.add_warning("field1", "Warning 1")
        context.add_warning("field3", "Warning 2")

        # Act
        errors = context.get_errors()
        warnings = context.get_warnings()

        # Assert
        assert len(errors) == 2
        assert len(warnings) == 2
        assert errors[0]["field"] == "field1"
        assert warnings[0]["field"] == "field1"


class TestFieldValidator:
    """Test suite for FieldValidator"""

    def test_field_validator_initialization(self):
        """Test FieldValidator initialization"""
        # Arrange & Act
        validator = FieldValidator("test_field")

        # Assert
        assert validator.field_name == "test_field"
        assert validator.rules == []

    def test_add_required_rule(self):
        """Test adding required rule"""
        # Arrange
        validator = FieldValidator("name")

        # Act
        validator.required()

        # Assert
        assert len(validator.rules) == 1
        assert validator.rules[0][0] == ValidationRule.REQUIRED

    def test_add_format_rule(self):
        """Test adding format rule"""
        # Arrange
        validator = FieldValidator("email")

        # Act
        validator.format("email")

        # Assert
        assert len(validator.rules) == 1
        assert validator.rules[0][0] == ValidationRule.FORMAT
        assert validator.rules[0][1] == "email"

    def test_add_range_rule(self):
        """Test adding range rule"""
        # Arrange
        validator = FieldValidator("age")

        # Act
        validator.range(min_value=18, max_value=100)

        # Assert
        assert len(validator.rules) == 1
        assert validator.rules[0][0] == ValidationRule.RANGE
        assert validator.rules[0][1] == {"min": 18, "max": 100}

    def test_add_length_rule(self):
        """Test adding length rule"""
        # Arrange
        validator = FieldValidator("password")

        # Act
        validator.length(min_length=8, max_length=128)

        # Assert
        assert len(validator.rules) == 1
        assert validator.rules[0][0] == ValidationRule.LENGTH
        assert validator.rules[0][1] == {"min": 8, "max": 128}

    def test_add_pattern_rule(self):
        """Test adding pattern rule"""
        # Arrange
        validator = FieldValidator("phone")

        # Act
        validator.pattern(r"^\+?1?\d{9,15}$")

        # Assert
        assert len(validator.rules) == 1
        assert validator.rules[0][0] == ValidationRule.PATTERN

    def test_add_custom_rule(self):
        """Test adding custom validation rule"""
        # Arrange
        validator = FieldValidator("custom_field")
        custom_func = lambda x: x == "valid"

        # Act
        validator.custom(custom_func, "Custom validation failed")

        # Assert
        assert len(validator.rules) == 1
        assert validator.rules[0][0] == ValidationRule.CUSTOM
        assert callable(validator.rules[0][1]["func"])
        assert validator.rules[0][1]["message"] == "Custom validation failed"

    @pytest.mark.parametrize("value,expected", [
        ("valid@email.com", True),
        ("invalid-email", False),
        ("", False),
        ("@domain.com", False),
        ("user@", False)
    ])
    def test_validate_email_format(self, value, expected):
        """Test email format validation"""
        # Arrange
        validator = FieldValidator("email")
        validator.format("email")
        context = ValidationContext()

        # Act
        result = validator.validate(value, context)

        # Assert
        assert result == expected
        if not expected and value:  # Don't expect error for empty string (required check)
            assert context.has_errors()

    @pytest.mark.parametrize("value,min_val,max_val,expected", [
        (25, 18, 100, True),
        (17, 18, 100, False),
        (101, 18, 100, False),
        (18, 18, 100, True),
        (100, 18, 100, True)
    ])
    def test_validate_range(self, value, min_val, max_val, expected):
        """Test range validation"""
        # Arrange
        validator = FieldValidator("age")
        validator.range(min_val, max_val)
        context = ValidationContext()

        # Act
        result = validator.validate(value, context)

        # Assert
        assert result == expected
        if not expected:
            assert context.has_errors()
            assert "range" in context.get_errors()[0]["message"].lower()

    @pytest.mark.parametrize("value,min_len,max_len,expected", [
        ("password123", 8, 128, True),
        ("pass", 8, 128, False),
        ("a" * 129, 8, 128, False),
        ("12345678", 8, 128, True),
        ("a" * 128, 8, 128, True)
    ])
    def test_validate_length(self, value, min_len, max_len, expected):
        """Test length validation"""
        # Arrange
        validator = FieldValidator("password")
        validator.length(min_len, max_len)
        context = ValidationContext()

        # Act
        result = validator.validate(value, context)

        # Assert
        assert result == expected
        if not expected:
            assert context.has_errors()

    def test_validate_multiple_rules(self):
        """Test field with multiple validation rules"""
        # Arrange
        validator = FieldValidator("username")
        validator.required()
        validator.length(min=3, max=20)
        validator.pattern(r"^[a-zA-Z0-9_]+$")
        context = ValidationContext()

        # Act & Assert - Valid case
        assert validator.validate("valid_user123", context) is True
        assert not context.has_errors()

        # Reset context for invalid case
        context = ValidationContext()

        # Act & Assert - Invalid case (too short)
        assert validator.validate("ab", context) is False
        assert context.has_errors()


class TestValidatorFactory:
    """Test suite for ValidatorFactory"""

    def test_get_strategy_validator(self):
        """Test getting strategy validator"""
        # Act
        validator = ValidatorFactory.get_strategy_validator()

        # Assert
        assert isinstance(validator, StrategyValidator)

    def test_get_execution_validator(self):
        """Test getting execution validator"""
        # Act
        validator = ValidatorFactory.get_validator("execution")

        # Assert
        # Should return appropriate validator type based on implementation
        assert validator is not None

    def test_get_validator_cache(self):
        """Test that validators are cached"""
        # Act
        validator1 = ValidatorFactory.get_strategy_validator()
        validator2 = ValidatorFactory.get_strategy_validator()

        # Assert
        assert validator1 is validator2  # Should be same instance (cached)


class TestBatchOperationValidator:
    """Test suite for BatchOperationValidator"""

    def test_validate_batch_operation_success(self):
        """Test successful batch operation validation"""
        # Arrange
        validator = BatchOperationValidator()
        operation_data = {
            "strategy_ids": [1, 2, 3, 4, 5],
            "operation": "activate",
            "config": {
                "batch_size": 10,
                "max_retries": 3,
                "continue_on_error": True
            }
        }

        # Act
        result = validator.validate(operation_data)

        # Assert
        assert result is True

    def test_validate_batch_operation_invalid_operation(self):
        """Test batch operation with invalid operation type"""
        # Arrange
        validator = BatchOperationValidator()
        operation_data = {
            "strategy_ids": [1, 2, 3],
            "operation": "invalid_operation",
            "config": {}
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(operation_data)

        assert "Invalid operation" in str(exc_info.value)

    def test_validate_batch_operation_empty_strategy_ids(self):
        """Test batch operation with empty strategy IDs"""
        # Arrange
        validator = BatchOperationValidator()
        operation_data = {
            "strategy_ids": [],
            "operation": "activate",
            "config": {}
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(operation_data)

        assert "strategy_ids" in str(exc_info.value).lower()

    def test_validate_batch_operation_too_many_ids(self):
        """Test batch operation with too many strategy IDs"""
        # Arrange
        validator = BatchOperationValidator()
        operation_data = {
            "strategy_ids": list(range(1, 1001)),  # 1000 IDs (exceeds limit)
            "operation": "activate",
            "config": {}
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(operation_data)

        assert "too many" in str(exc_info.value).lower()

    def test_validate_batch_config(self):
        """Test batch configuration validation"""
        # Arrange
        validator = BatchOperationValidator()

        # Test valid config
        valid_config = {
            "batch_size": 50,
            "max_retries": 3,
            "timeout_per_item": 5.0,
            "continue_on_error": True
        }
        assert validator._validate_config(valid_config) is True

        # Test invalid batch_size
        invalid_config = {
            "batch_size": 0,  # Invalid
            "max_retries": 3
        }
        with pytest.raises(ValidationError):
            validator._validate_config(invalid_config)


class TestStrategyValidator:
    """Test suite for StrategyValidator"""

    def test_validate_strategy_creation_success(self):
        """Test successful strategy creation validation"""
        # Arrange
        validator = StrategyValidator()
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test strategy",
            "strategy_type": "momentum",
            "parameters": {
                "timeframe": "1h",
                "risk_level": "medium",
                "max_position": 10000
            }
        }

        # Act
        result = validator.validate_create(strategy_data)

        # Assert
        assert result is True

    def test_validate_strategy_creation_missing_required_fields(self):
        """Test strategy creation with missing required fields"""
        # Arrange
        validator = StrategyValidator()
        strategy_data = {
            "description": "Missing name and type"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_create(strategy_data)

        assert "required" in str(exc_info.value).lower()

    def test_validate_strategy_type(self):
        """Test strategy type validation"""
        # Arrange
        validator = StrategyValidator()

        # Test valid types
        for valid_type in ["momentum", "mean_reversion", "arbitrage"]:
            assert validator._validate_strategy_type(valid_type) is True

        # Test invalid type
        with pytest.raises(ValidationError):
            validator._validate_strategy_type("invalid_type")

    def test_validate_strategy_parameters(self):
        """Test strategy parameters validation"""
        # Arrange
        validator = StrategyValidator()

        # Valid parameters
        valid_params = {
            "timeframe": "1h",
            "risk_level": "medium",
            "max_position": 10000
        }
        assert validator._validate_parameters(valid_params) is True

        # Invalid parameters (negative position)
        invalid_params = {
            "max_position": -1000
        }
        with pytest.raises(ValidationError):
            validator._validate_parameters(invalid_params)

    def test_validate_strategy_update(self):
        """Test strategy update validation"""
        # Arrange
        validator = StrategyValidator()
        update_data = {
            "name": "Updated Strategy",
            "status": "inactive"
        }

        # Act
        result = validator.validate_update(update_data)

        # Assert
        assert result is True

    def test_validate_strategy_update_with_invalid_fields(self):
        """Test strategy update with invalid fields"""
        # Arrange
        validator = StrategyValidator()
        update_data = {
            "id": 123,  # Should not be updatable
            "created_at": "2023-01-01"  # Should not be updatable
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_update(update_data)

        assert "cannot be updated" in str(exc_info.value).lower()


class TestParameterValidator:
    """Test suite for ParameterValidator"""

    def test_validate_numeric_parameter(self):
        """Test numeric parameter validation"""
        # Arrange
        validator = ParameterValidator()

        # Test valid numeric values
        assert validator.validate_numeric(100, min_value=0, max_value=1000) is True
        assert validator.validate_numeric(0.5, min_value=0, max_value=1) is True

        # Test invalid numeric values
        with pytest.raises(ValidationError):
            validator.validate_numeric(-100, min_value=0)
        with pytest.raises(ValidationError):
            validator.validate_numeric(1500, max_value=1000)

    def test_validate_string_parameter(self):
        """Test string parameter validation"""
        # Arrange
        validator = ParameterValidator()

        # Test valid strings
        assert validator.validate_string("hello", min_length=1, max_length=100) is True
        assert validator.validate_string("", required=False) is True

        # Test invalid strings
        with pytest.raises(ValidationError):
            validator.validate_string("", required=True)
        with pytest.raises(ValidationError):
            validator.validate_string("a" * 101, max_length=100)

    def test_validate_list_parameter(self):
        """Test list parameter validation"""
        # Arrange
        validator = ParameterValidator()

        # Test valid lists
        assert validator.validate_list([1, 2, 3], min_items=1, max_items=10) is True
        assert validator.validate_list([], required=False) is True

        # Test invalid lists
        with pytest.raises(ValidationError):
            validator.validate_list([], required=True)
        with pytest.raises(ValidationError):
            validator.validate_list([1] * 11, max_items=10)

    def test_validate_date_parameter(self):
        """Test date parameter validation"""
        # Arrange
        validator = ParameterValidator()

        # Test valid dates
        assert validator.validate_date("2023-12-01") is True
        assert validator.validate_date(date.today()) is True

        # Test invalid dates
        with pytest.raises(ValidationError):
            validator.validate_date("2023-13-01")  # Invalid month
        with pytest.raises(ValidationError):
            validator.validate_date("not_a_date")

    def test_validate_enum_parameter(self):
        """Test enum parameter validation"""
        # Arrange
        validator = ParameterValidator()
        valid_values = ["low", "medium", "high"]

        # Test valid enum values
        assert validator.validate_enum("medium", valid_values) is True

        # Test invalid enum values
        with pytest.raises(ValidationError):
            validator.validate_enum("very_high", valid_values)


class TestCustomValidationRules:
    """Test suite for custom validation rules"""

    def test_custom_risk_assessment_rule(self):
        """Test custom risk assessment validation rule"""
        # Arrange
        validator = StrategyValidator()
        high_risk_params = {
            "leverage": 100,
            "max_drawdown": 0.5,
            "position_size": 0.9
        }

        # Act
        context = ValidationContext()
        validator._assess_risk_level(high_risk_params, context)

        # Assert
        assert context.has_warnings()
        assert any("high risk" in w["message"].lower() for w in context.get_warnings())

    def test_custom_performance_validation_rule(self):
        """Test custom performance validation rule"""
        # Arrange
        validator = StrategyValidator()
        unrealistic_performance = {
            "annual_return": 5.0,  # 500% annual return
            "sharpe_ratio": 10.0,
            "max_drawdown": 0.0001
        }

        # Act
        context = ValidationContext()
        validator._validate_performance_metrics(unrealistic_performance, context)

        # Assert
        assert context.has_warnings()
        assert any("unrealistic" in w["message"].lower() for w in context.get_warnings())

    def test_custom_correlation_validation_rule(self):
        """Test custom correlation validation rule"""
        # Arrange
        validator = StrategyValidator()
        correlated_strategies = [
            {"id": 1, "correlation": 0.95},
            {"id": 2, "correlation": 0.98}
        ]

        # Act
        context = ValidationContext()
        validator._check_strategy_correlation(correlated_strategies, context)

        # Assert
        assert context.has_warnings()
        assert any("correlation" in w["message"].lower() for w in context.get_warnings())


# Integration Tests

class TestValidatorIntegration:
    """Integration tests for validators"""

    @pytest.mark.integration
    def test_full_strategy_validation_workflow(self):
        """Test complete strategy validation workflow"""
        # Arrange
        factory = ValidatorFactory()
        strategy_validator = factory.get_strategy_validator()

        strategy_data = {
            "name": "Comprehensive Test Strategy",
            "description": "Testing all validation rules",
            "strategy_type": "momentum",
            "parameters": {
                "timeframe": "1h",
                "risk_level": "medium",
                "max_position": 50000,
                "leverage": 2.0,
                "stop_loss": 0.02
            },
            "performance_targets": {
                "annual_return": 0.25,
                "sharpe_ratio": 1.5,
                "max_drawdown": 0.1
            }
        }

        # Act
        context = ValidationContext(user_id=1, operation="create")
        result = strategy_validator.validate_create(strategy_data, context)

        # Assert
        assert result is True
        assert not context.has_errors()

        # Check for any warnings
        warnings = context.get_warnings()
        # May have warnings about risk level or performance targets
        assert isinstance(warnings, list)

    @pytest.mark.integration
    @pytest.mark.error_handling
    def test_validation_error_accumulation(self):
        """Test that multiple validation errors are accumulated"""
        # Arrange
        validator = StrategyValidator()
        invalid_strategy = {
            # Missing required fields
            "description": "No name or type",
            "parameters": {
                "max_position": -1000,  # Invalid negative value
                "leverage": 1000,  # Unrealistically high
                "timeframe": "invalid_timeframe"  # Invalid format
            }
        }

        # Act
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_create(invalid_strategy)

        # Assert
        # Should have multiple errors accumulated
        error_message = str(exc_info.value)
        assert "name" in error_message.lower()
        assert "strategy_type" in error_message.lower()
        assert "max_position" in error_message.lower() or "negative" in error_message.lower()