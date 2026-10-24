"""
Secure Input Validator - Comprehensive Input Validation Framework
Created: 2025-11-30
Purpose: Prevent input validation vulnerabilities and attacks
"""

import re
import logging
import numbers
from typing import Any, Optional, List, Union, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class InputValidationError(Exception):
    """Input validation related error"""
    pass

class InputType(Enum):
    """Supported input types"""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    FILE_PATH = "file_path"
    STOCK_SYMBOL = "stock_symbol"
    PARAMETER_RANGE = "parameter_range"
    DATE = "date"
    EMAIL = "email"
    URL = "url"

@dataclass
class ValidationRule:
    """Input validation rule definition"""
    name: str
    input_type: InputType
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[str]] = None
    pattern: Optional[str] = None
    required: bool = True
    allow_empty: bool = False
    max_length: Optional[int] = None
    custom_validator: Optional[callable] = None

class SecureInputValidator:
    """Secure input validation framework"""

    def __init__(self):
        """Initialize the secure input validator"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.validation_rules = self._initialize_default_rules()
        self.attack_patterns = self._initialize_attack_patterns()

    def _initialize_default_rules(self) -> Dict[str, ValidationRule]:
        """Initialize default validation rules"""
        return {
            # Stock symbol validation
            "stock_symbol": ValidationRule(
                name="stock_symbol",
                input_type=InputType.STRING,
                pattern=r'^[0-9]{4}\.HK$',
                max_length=10,
                required=True,
                custom_validator=self._validate_stock_symbol
            ),

            # Menu choice validation
            "menu_choice": ValidationRule(
                name="menu_choice",
                input_type=InputType.INTEGER,
                min_value=1,
                max_value=10,
                required=True,
                custom_validator=self._validate_menu_choice
            ),

            # Duration validation (days)
            "duration": ValidationRule(
                name="duration",
                input_type=InputType.INTEGER,
                min_value=1,
                max_value=3650,
                required=True,
                custom_validator=self._validate_duration
            ),

            # RSI parameter validation
            "rsi_period": ValidationRule(
                name="rsi_period",
                input_type=InputType.INTEGER,
                min_value=2,
                max_value=100,
                required=True,
                custom_validator=self._validate_rsi_parameter
            ),

            # MACD parameter validation
            "macd_fast": ValidationRule(
                name="macd_fast",
                input_type=InputType.INTEGER,
                min_value=1,
                max_value=50,
                required=True,
                custom_validator=self._validate_macd_parameter
            ),

            # Sharpe ratio threshold
            "sharpe_threshold": ValidationRule(
                name="sharpe_threshold",
                input_type=InputType.FLOAT,
                min_value=0.0,
                max_value=5.0,
                required=True,
                custom_validator=self._validate_sharpe_threshold
            ),

            # Boolean yes/no validation
            "boolean_choice": ValidationRule(
                name="boolean_choice",
                input_type=InputType.BOOLEAN,
                required=True,
                custom_validator=self._validate_boolean_choice
            ),

            # File path validation
            "file_path": ValidationRule(
                name="file_path",
                input_type=InputType.FILE_PATH,
                required=True,
                max_length=260,
                custom_validator=self._validate_file_path
            ),

            # Date validation
            "date": ValidationRule(
                name="date",
                input_type=InputType.DATE,
                pattern=r'^\\d{4}-\\d{2}-\\d{2}$',
                required=True,
                custom_validator=self._validate_date
            ),

            # Email validation
            "email": ValidationRule(
                name="email",
                input_type=InputType.EMAIL,
                pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
                max_length=254,
                required=True,
                custom_validator=self._validate_email
            )
        }

    def _initialize_attack_patterns(self) -> List[str]:
        """Initialize patterns for detecting injection attacks"""
        return [
            # Command injection patterns
            r';.*rm.*',
            r';.*cat.*',
            r';.*ls.*',
            r';.*echo.*',
            r'&.*rm.*',
            r'\\|.*rm.*',
            r'`.*rm.*',

            # SQL injection patterns
            r'--',
            r'/\\*',
            r'\\*/',
            r'UNION.*SELECT',
            r'DROP.*TABLE',
            r'INSERT.*INTO',
            r'UPDATE.*SET',
            r'DELETE.*FROM',

            # Path traversal patterns
            r'\\.\\./.*',
            r'\\.\\.\\\\',
            r'%2e%2e%2f',
            r'%2e%2e\\\\',

            # XSS patterns
            r'<script.*>',
            r'onload=',
            r'onerror=',
            r'javascript:',

            # File system patterns
            r'/etc/passwd',
            r'/etc/shadow',
            r'\\\\windows\\\\system32',
            r'%windir%',
        ]

    def validate_input(self, user_input: str, rule_name: str,
                       context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Validate user input against specific rule

        Args:
            user_input: Input to validate
            rule_name: Name of validation rule to apply
            context: Additional context for validation

        Returns:
            Validated and converted input

        Raises:
            InputValidationError: If validation fails
        """
        try:
            # Get validation rule
            rule = self._get_rule(rule_name)

            # Convert to string and strip whitespace
            if isinstance(user_input, (int, float)):
                user_input_str = str(user_input)
            else:
                user_input_str = str(user_input).strip()

            # Check for attack patterns
            self._check_attack_patterns(user_input_str)

            # Empty input validation
            if not user_input_str and not rule.allow_empty:
                raise InputValidationError(f"Input cannot be empty for rule: {rule_name}")

            # Type-specific validation
            if user_input_str:  # Skip empty values if allowed
                validated_value = self._validate_by_type(user_input_str, rule, context)
            else:
                validated_value = None

            # Custom validation
            if rule.custom_validator:
                validated_value = rule.custom_validator(validated_value, context)

            self.logger.debug(f"Input validated successfully: {rule_name}")
            return validated_value

        except InputValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Input validation failed for rule {rule_name}: {e}")
            raise InputValidationError(f"Validation failed: {e}")

    def validate_menu_choice(self, user_input: str,
                             valid_options: Optional[List[str]] = None,
                             min_val: int = 1, max_val: int = 10,
                             context: Optional[Dict[str, Any]] = None) -> int:
        """Validate menu choice input"""
        try:
            # Check if it's a numeric choice
            if valid_options and all(option.isdigit() for option in valid_options):
                return self.validate_input(user_input, "menu_choice",
                                           {"min_value": min_val, "max_value": max_val,
                                            "valid_options": valid_options})

            # Check if it's a text choice
            elif valid_options and any(not option.isdigit() for option in valid_options):
                if user_input.strip() in valid_options:
                    return valid_options.index(user_input.strip()) + 1
                else:
                    raise InputValidationError(f"Invalid choice. Valid options: {valid_options}")

            # Numeric range validation
            else:
                return self.validate_input(user_input, "menu_choice",
                                           {"min_value": min_val, "max_value": max_val})

        except Exception as e:
            raise InputValidationError(f"Menu choice validation failed: {e}")

    def validate_stock_symbol(self, user_input: str,
                             context: Optional[Dict[str, Any]] = None) -> str:
        """Validate stock symbol input"""
        return self.validate_input(user_input, "stock_symbol", context)

    def validate_parameter_range(self, param_name: str, user_input: str,
                                 param_type: str = "int",
                                 min_val: Optional[Union[int, float]] = None,
                                 max_val: Optional[Union[int, float]] = None,
                                 context: Optional[Dict[str, Any]] = None) -> Union[int, float]:
        """Validate parameter range input"""
        try:
            if param_type == "int":
                rule_name = "integer_parameter"
                custom_rule = ValidationRule(
                    name=rule_name,
                    input_type=InputType.INTEGER,
                    min_value=min_val,
                    max_value=max_val,
                    required=True,
                    custom_validator=self._validate_parameter
                )
            else:  # float
                rule_name = "float_parameter"
                custom_rule = ValidationRule(
                    name=rule_name,
                    input_type=InputType.FLOAT,
                    min_value=min_val,
                    max_value=max_val,
                    required=True,
                    custom_validator=self._validate_parameter
                )

            # Temporarily add custom rule
            self.validation_rules[rule_name] = custom_rule

            try:
                result = self.validate_input(user_input, rule_name, context)
                return result
            finally:
                # Clean up temporary rule
                if rule_name in self.validation_rules:
                    del self.validation_rules[rule_name]

        except Exception as e:
            raise InputValidationError(f"Parameter range validation failed: {e}")

    def _get_rule(self, rule_name: str) -> ValidationRule:
        """Get validation rule by name"""
        if rule_name not in self.validation_rules:
            raise InputValidationError(f"Unknown validation rule: {rule_name}")
        return self.validation_rules[rule_name]

    def _check_attack_patterns(self, input_str: str) -> None:
        """Check for potential attack patterns"""
        for pattern in self.attack_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                self.logger.warning(f"Potential attack pattern detected: {pattern}")
                raise InputValidationError(f"Input contains potentially dangerous content")

    def _validate_by_type(self, input_str: str, rule: ValidationRule,
                          context: Optional[Dict[str, Any]] = None) -> Any:
        """Validate input based on type"""
        if rule.input_type == InputType.INTEGER:
            return self._validate_integer(input_str, rule, context)
        elif rule.input_type == InputType.FLOAT:
            return self._validate_float(input_str, rule, context)
        elif rule.input_type == InputType.STRING:
            return self._validate_string(input_str, rule, context)
        elif rule.input_type == InputType.BOOLEAN:
            return self._validate_boolean(input_str, rule, context)
        elif rule.input_type == InputType.FILE_PATH:
            return self._validate_file_path_str(input_str, rule, context)
        elif rule.input_type == InputType.STOCK_SYMBOL:
            return self._validate_stock_symbol_str(input_str, rule, context)
        elif rule.input_type == InputType.DATE:
            return self._validate_date_str(input_str, rule, context)
        elif rule.input_type == InputType.EMAIL:
            return self._validate_email_str(input_str, rule, context)
        else:
            raise InputValidationError(f"Unsupported input type: {rule.input_type}")

    def _validate_integer(self, input_str: str, rule: ValidationRule,
                         context: Optional[Dict[str, Any]] = None) -> int:
        """Validate integer input"""
        try:
            value = int(input_str)

            if rule.min_value is not None and value < rule.min_value:
                raise InputValidationError(f"Value {value} is below minimum {rule.min_value}")

            if rule.max_value is not None and value > rule.max_value:
                raise InputValidationError(f"Value {value} is above maximum {rule.max_value}")

            if rule.allowed_values and str(value) not in rule.allowed_values:
                raise InputValidationError(f"Value {value} not in allowed values: {rule.allowed_values}")

            return value

        except ValueError:
            raise InputValidationError(f"Invalid integer: {input_str}")

    def _validate_float(self, input_str: str, rule: ValidationRule,
                        context: Optional[Dict[str, Any]] = None) -> float:
        """Validate float input"""
        try:
            value = float(input_str)

            if rule.min_value is not None and value < rule.min_value:
                raise InputValidationError(f"Value {value} is below minimum {rule.min_value}")

            if rule.max_value is not None and value > rule.max_value:
                raise InputValidationError(f"Value {value} is above maximum {rule.max_value}")

            return value

        except ValueError:
            raise InputValidationError(f"Invalid float: {input_str}")

    def _validate_string(self, input_str: str, rule: ValidationRule,
                        context: Optional[Dict[str, Any]] = None) -> str:
        """Validate string input"""
        if rule.max_length and len(input_str) > rule.max_length:
            raise InputValidationError(f"Input too long: {len(input_str)} > {rule.max_length}")

        if rule.pattern and not re.match(rule.pattern, input_str):
            raise InputValidationError(f"Input does not match required pattern: {rule.pattern}")

        if rule.allowed_values and input_str not in rule.allowed_values:
            raise InputValidationError(f"Input not in allowed values: {rule.allowed_values}")

        return input_str

    def _validate_boolean(self, input_str: str, rule: ValidationRule,
                         context: Optional[Dict[str, Any]] = None) -> bool:
        """Validate boolean input"""
        input_str = input_str.lower().strip()

        true_values = ['true', '1', 'yes', 'y', 'on']
        false_values = ['false', '0', 'no', 'n', 'off']

        if input_str in true_values:
            return True
        elif input_str in false_values:
            return False
        else:
            raise InputValidationError(f"Invalid boolean: {input_str}. Use: {true_values + false_values}")

    def _validate_file_path_str(self, input_str: str, rule: ValidationRule,
                                context: Optional[Dict[str, Any]] = None) -> str:
        """Validate file path input"""
        # Path traversal protection
        if '..' in input_str or input_str.startswith('/') or ':' in input_str:
            raise InputValidationError(f"Invalid file path: {input_str}")

        # Check file extension if specified
        if context and 'allowed_extensions' in context:
            file_path = Path(input_str)
            if file_path.suffix.lower() not in context['allowed_extensions']:
                raise InputValidationError(f"File extension not allowed: {file_path.suffix}")

        return input_str

    def _validate_stock_symbol_str(self, input_str: str, rule: ValidationRule,
                                  context: Optional[Dict[str, Any]] = None) -> str:
        """Validate stock symbol input"""
        input_str = input_str.upper().strip()

        # Basic HK stock symbol pattern
        if not re.match(r'^[0-9]{4}\\.HK$', input_str):
            raise InputValidationError(f"Invalid HK stock symbol: {input_str}. Format: 1234.HK")

        # Known HK symbols list (optional)
        if context and 'allowed_symbols' in context:
            if input_str not in context['allowed_symbols']:
                self.logger.warning(f"Stock symbol not in allowed list: {input_str}")

        return input_str

    def _validate_date_str(self, input_str: str, rule: ValidationRule,
                          context: Optional[Dict[str, Any]] = None) -> str:
        """Validate date input"""
        from datetime import datetime

        try:
            # Try to parse the date
            datetime.strptime(input_str, '%Y-%m-%d')
            return input_str
        except ValueError:
            raise InputValidationError(f"Invalid date format: {input_str}. Use: YYYY-MM-DD")

    def _validate_email_str(self, input_str: str, rule: ValidationRule,
                           context: Optional[Dict[str, Any]] = None) -> str:
        """Validate email input"""
        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', input_str):
            raise InputValidationError(f"Invalid email format: {input_str}")

        return input_str.lower()

    # Custom validators
    def _validate_stock_symbol(self, value: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Custom stock symbol validator"""
        if isinstance(value, str):
            return self._validate_stock_symbol_str(value, None, context)
        return str(value)

    def _validate_menu_choice(self, value: Union[int, str], context: Optional[Dict[str, Any]] = None) -> int:
        """Custom menu choice validator"""
        if isinstance(value, str) and context and 'valid_options' in context:
            if value in context['valid_options']:
                return context['valid_options'].index(value) + 1
            else:
                raise InputValidationError(f"Invalid choice: {value}")
        return int(value)

    def _validate_duration(self, value: int, context: Optional[Dict[str, Any]] = None) -> int:
        """Custom duration validator"""
        if value <= 0:
            raise InputValidationError("Duration must be positive")
        if value > 3650:  # 10 years max
            raise InputValidationError("Duration too long (max 10 years)")
        return value

    def _validate_rsi_parameter(self, value: Union[int, float], context: Optional[Dict[str, Any]] = None) -> int:
        """Custom RSI parameter validator"""
        value = int(value)
        if value < 2 or value > 100:
            raise InputValidationError("RSI period must be between 2 and 100")
        return value

    def _validate_macd_parameter(self, value: Union[int, float], context: Optional[Dict[str, Any]] = None) -> int:
        """Custom MACD parameter validator"""
        value = int(value)
        if value < 1 or value > 50:
            raise InputValidationError("MACD period must be between 1 and 50")
        return value

    def _validate_sharpe_threshold(self, value: float, context: Optional[Dict[str, Any]] = None) -> float:
        """Custom Sharpe ratio threshold validator"""
        if value < 0 or value > 5:
            raise InputValidationError("Sharpe ratio threshold must be between 0 and 5")
        return float(value)

    def _validate_boolean_choice(self, value: bool, context: Optional[Dict[str, Any]] = None) -> bool:
        """Custom boolean choice validator"""
        return bool(value)

    def _validate_file_path(self, value: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Custom file path validator"""
        return self._validate_file_path_str(value, None, context)

    def _validate_date(self, value: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Custom date validator"""
        return self._validate_date_str(value, None, context)

    def _validate_email(self, value: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Custom email validator"""
        return self._validate_email_str(value, None, context)

    def _validate_parameter(self, value: Union[int, float], context: Optional[Dict[str, Any]] = None) -> Union[int, float]:
        """Custom parameter validator"""
        return value

# Global validator instance
_validator: Optional[SecureInputValidator] = None

def get_input_validator() -> SecureInputValidator:
    """Get global input validator instance"""
    global _validator
    if _validator is None:
        _validator = SecureInputValidator()
    return _validator

# Convenience functions
def safe_input_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """Safely get integer input"""
    validator = get_input_validator()
    user_input = input(prompt).strip()

    rule_name = "temp_integer"
    rule = ValidationRule(
        name=rule_name,
        input_type=InputType.INTEGER,
        min_value=min_val,
        max_value=max_val,
        required=True
    )

    validator.validation_rules[rule_name] = rule
    try:
        result = validator.validate_input(user_input, rule_name)
        del validator.validation_rules[rule_name]
        return result
    except:
        del validator.validation_rules[rule_name]
        raise

def safe_input_float(prompt: str, min_val: float = None, max_val: float = None) -> float:
    """Safely get float input"""
    validator = get_input_validator()
    user_input = input(prompt).strip()

    rule_name = "temp_float"
    rule = ValidationRule(
        name=rule_name,
        input_type=InputType.FLOAT,
        min_value=min_val,
        max_value=max_val,
        required=True
    )

    validator.validation_rules[rule_name] = rule
    try:
        result = validator.validate_input(user_input, rule_name)
        del validator.validation_rules[rule_name]
        return result
    except:
        del validator.validation_rules[rule_name]
        raise

def safe_input_choice(prompt: str, valid_options: List[str]) -> str:
    """Safely get choice input"""
    validator = get_input_validator()
    user_input = input(prompt).strip()

    if user_input not in valid_options:
        raise InputValidationError(f"Invalid choice. Valid options: {valid_options}")

    return user_input