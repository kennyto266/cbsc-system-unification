"""
Parameter Validation Module

Provides validation system for strategy parameters with error reporting.
"""

from typing import Any, Dict, List, Callable, Optional
import ipywidgets as widgets
from datetime import datetime


class ValidationResult:
    """Result of parameter validation"""

    def __init__(
        self,
        is_valid: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ):
        """
        Initialize validation result

        Args:
            is_valid: Whether validation passed
            errors: List of error messages
            warnings: List of warning messages
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def to_widget(self) -> widgets.HTML:
        """
        Convert validation result to display widget

        Returns:
            HTML widget with formatted validation status
        """
        if self.is_valid and not self.warnings:
            html = '<div style="color: green; font-weight: bold;">✓ All parameters valid</div>'
        elif self.is_valid and self.warnings:
            warning_html = '<br>'.join([f'⚠ {w}' for w in self.warnings])
            html = f'<div style="color: orange;">{warning_html}</div>'
        else:
            error_html = '<br>'.join([f'✗ {e}' for e in self.errors])
            html = f'<div style="color: red; font-weight: bold;">{error_html}</div>'

        return widgets.HTML(value=html)

    def __str__(self) -> str:
        """String representation of validation result"""
        if self.is_valid:
            if self.warnings:
                return f"Valid with warnings: {', '.join(self.warnings)}"
            return "Valid"
        return f"Invalid: {', '.join(self.errors)}"

    def __repr__(self) -> str:
        """Developer representation"""
        return f"ValidationResult(is_valid={self.is_valid}, errors={len(self.errors)}, warnings={len(self.warnings)})"


class ParameterValidator:
    """Validate parameter values against defined rules"""

    def __init__(self):
        """Initialize validator with empty rule set"""
        self.rules: Dict[str, List[Dict]] = {}

    def add_rule(
        self,
        parameter: str,
        validator: Callable[[Any], bool],
        error_message: str
    ):
        """
        Add validation rule for parameter

        Args:
            parameter: Parameter name
            validator: Function that takes value and returns bool
            error_message: Error message if validation fails
        """
        if parameter not in self.rules:
            self.rules[parameter] = []

        self.rules[parameter].append({
            'validator': validator,
            'error_message': error_message
        })

    def add_range_rule(
        self,
        parameter: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ):
        """
        Add range validation rule

        Args:
            parameter: Parameter name
            min_value: Minimum allowed value (None for no minimum)
            max_value: Maximum allowed value (None for no maximum)
        """
        def validator(value):
            if min_value is not None and value < min_value:
                return False
            if max_value is not None and value > max_value:
                return False
            return True

        error_parts = []
        if min_value is not None:
            error_parts.append(f"≥ {min_value}")
        if max_value is not None:
            error_parts.append(f"≤ {max_value}")

        error_message = f"{parameter} must be {' and '.join(error_parts)}"
        self.add_rule(parameter, validator, error_message)

    def add_choice_rule(
        self,
        parameter: str,
        choices: List[Any]
    ):
        """
        Add choice validation rule

        Args:
            parameter: Parameter name
            choices: List of valid choices
        """
        def validator(value):
            return value in choices

        error_message = f"{parameter} must be one of: {', '.join(map(str, choices))}"
        self.add_rule(parameter, validator, error_message)

    def add_type_rule(
        self,
        parameter: str,
        expected_type: type
    ):
        """
        Add type validation rule

        Args:
            parameter: Parameter name
            expected_type: Expected type
        """
        def validator(value):
            return isinstance(value, expected_type)

        error_message = f"{parameter} must be of type {expected_type.__name__}"
        self.add_rule(parameter, validator, error_message)

    def add_custom_rule(
        self,
        parameter: str,
        rule_name: str,
        validator: Callable[[Any], bool],
        error_message: str
    ):
        """
        Add custom validation rule with named rule

        Args:
            parameter: Parameter name
            rule_name: Name for the rule
            validator: Validation function
            error_message: Error message
        """
        if parameter not in self.rules:
            self.rules[parameter] = []

        self.rules[parameter].append({
            'name': rule_name,
            'validator': validator,
            'error_message': error_message
        })

    def validate(
        self,
        params: Dict[str, Any],
        validate_unknown: bool = False
    ) -> ValidationResult:
        """
        Validate all parameters

        Args:
            params: Parameter dictionary
            validate_unknown: Whether to flag unknown parameters

        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        warnings = []

        # Check for unknown parameters
        if validate_unknown:
            known_params = set(self.rules.keys())
            unknown_params = set(params.keys()) - known_params
            if unknown_params:
                warnings.append(f"Unknown parameters: {', '.join(unknown_params)}")

        # Validate each parameter
        for param, value in params.items():
            if param in self.rules:
                for rule in self.rules[param]:
                    try:
                        if not rule['validator'](value):
                            errors.append(rule['error_message'])
                    except Exception as e:
                        errors.append(f"{param} validation error: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def validate_parameter(
        self,
        parameter: str,
        value: Any
    ) -> ValidationResult:
        """
        Validate a single parameter

        Args:
            parameter: Parameter name
            value: Parameter value

        Returns:
            ValidationResult for this parameter
        """
        if parameter not in self.rules:
            return ValidationResult(is_valid=True)

        errors = []
        for rule in self.rules[parameter]:
            try:
                if not rule['validator'](value):
                    errors.append(rule['error_message'])
            except Exception as e:
                errors.append(f"Validation error: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def clear_rules(self, parameter: Optional[str] = None):
        """
        Clear validation rules

        Args:
            parameter: Specific parameter to clear, or None for all
        """
        if parameter is None:
            self.rules.clear()
        elif parameter in self.rules:
            del self.rules[parameter]

    def get_rules(self, parameter: str) -> List[Dict]:
        """
        Get rules for a parameter

        Args:
            parameter: Parameter name

        Returns:
            List of rule dictionaries
        """
        return self.rules.get(parameter, [])

    def has_rules(self, parameter: str) -> bool:
        """
        Check if parameter has validation rules

        Args:
            parameter: Parameter name

        Returns:
            True if parameter has rules
        """
        return parameter in self.rules and len(self.rules[parameter]) > 0


# Predefined validators for common use cases

class CommonValidators:
    """Collection of common validation functions"""

    @staticmethod
    def positive_number(value: Any) -> bool:
        """Validate value is a positive number"""
        return isinstance(value, (int, float)) and value > 0

    @staticmethod
    def non_negative_number(value: Any) -> bool:
        """Validate value is non-negative"""
        return isinstance(value, (int, float)) and value >= 0

    @staticmethod
    def percentage(value: Any) -> bool:
        """Validate value is between 0 and 100"""
        return isinstance(value, (int, float)) and 0 <= value <= 100

    @staticmethod
    def valid_date(value: Any) -> bool:
        """Validate value is a valid date"""
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return True
            except ValueError:
                return False
        return False

    @staticmethod
    def non_empty_string(value: Any) -> bool:
        """Validate value is a non-empty string"""
        return isinstance(value, str) and len(value.strip()) > 0

    @staticmethod
    def valid_symbol(value: Any) -> bool:
        """Validate value is a valid symbol format"""
        if not isinstance(value, str):
            return False
        # Basic symbol format: alphanumeric with optional dots
        return bool(value) and all(c.isalnum() or c in '.-' for c in value)

    @staticmethod
    def integer_in_range(min_val: int, max_val: int) -> Callable[[Any], bool]:
        """Create validator for integer in range"""
        def validator(value):
            return isinstance(value, int) and min_val <= value <= max_val
        return validator

    @staticmethod
    def float_in_range(min_val: float, max_val: float) -> Callable[[Any], bool]:
        """Create validator for float in range"""
        def validator(value):
            return isinstance(value, (int, float)) and min_val <= value <= max_val
        return validator

    @staticmethod
    def list_length(min_len: int = 0, max_len: Optional[int] = None) -> Callable[[Any], bool]:
        """Create validator for list length"""
        def validator(value):
            if not isinstance(value, (list, tuple)):
                return False
            if len(value) < min_len:
                return False
            if max_len is not None and len(value) > max_len:
                return False
            return True
        return validator
