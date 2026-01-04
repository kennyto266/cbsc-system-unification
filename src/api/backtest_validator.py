"""
Backtest Configuration Validator
=================================

Comprehensive validation for backtest configurations including
strategy parameters, risk settings, and data requirements.

Author: CBSC Quant Team
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
import re
import logging
from pydantic import BaseModel, ValidationError
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Validation result with details"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_errors: Dict[str, List[str]]

    def add_error(self, field: str, message: str):
        """Add field-specific error"""
        if field not in self.field_errors:
            self.field_errors[field] = []
        self.field_errors[field].append(message)
        self.errors.append(f"{field}: {message}")

    def add_warning(self, message: str):
        """Add warning"""
        self.warnings.append(message)


class BacktestConfigValidator:
    """Comprehensive backtest configuration validator"""

    # Valid symbols patterns
    STOCK_PATTERN = re.compile(r'^[A-Z0-9]{1,5}(\.[A-Z]{1,3})?$')  # e.g., AAPL, 0700.HK
    CRYPTO_PATTERN = re.compile(r'^[A-Z]{2,20}-USD$')  # e.g., BTC-USD
    FUTURES_PATTERN = re.compile(r'^[A-Z]{1,5}\d{2}$')  # e.g., ES2024

    # Strategy parameters templates
    STRATEGY_TEMPLATES = {
        "ma_cross": {
            "required": ["short_period", "long_period"],
            "optional": {
                "signal_threshold": {"type": float, "default": 0.0, "min": 0.0, "max": 0.1},
                "volume_filter": {"type": bool, "default": False}
            },
            "constraints": {
                "short_period": {"type": int, "min": 5, "max": 50},
                "long_period": {"type": int, "min": 20, "max": 200}
            }
        },
        "rsi_oversold": {
            "required": ["rsi_period", "oversold_level", "overbought_level"],
            "optional": {
                "signal_cooldown": {"type": int, "default": 5, "min": 1, "max": 20}
            },
            "constraints": {
                "rsi_period": {"type": int, "min": 5, "max": 30},
                "oversold_level": {"type": float, "min": 10, "max": 40},
                "overbought_level": {"type": float, "min": 60, "max": 90}
            }
        },
        "bollinger_bands": {
            "required": ["period", "std_dev"],
            "optional": {
                "position_size": {"type": float, "default": 1.0, "min": 0.1, "max": 2.0}
            },
            "constraints": {
                "period": {"type": int, "min": 10, "max": 50},
                "std_dev": {"type": float, "min": 1.0, "max": 3.0}
            }
        },
        "mean_reversion": {
            "required": ["lookback_period", "entry_threshold", "exit_threshold"],
            "optional": {
                "stop_loss": {"type": float, "default": 0.05, "min": 0.01, "max": 0.2},
                "position_scaling": {"type": bool, "default": False}
            },
            "constraints": {
                "lookback_period": {"type": int, "min": 10, "max": 100},
                "entry_threshold": {"type": float, "min": 0.5, "max": 3.0},
                "exit_threshold": {"type": float, "min": 0.1, "max": 2.0}
            }
        },
        "momentum": {
            "required": ["momentum_period", "momentum_threshold"],
            "optional": {
                "risk_adjusted": {"type": bool, "default": True},
                "sector_neutral": {"type": bool, "default": False}
            },
            "constraints": {
                "momentum_period": {"type": int, "min": 20, "max": 250},
                "momentum_threshold": {"type": float, "min": 0.01, "max": 0.5}
            }
        }
    }

    # Risk limits
    RISK_LIMITS = {
        "var_limit": {"min": 0.005, "max": 0.10, "default": 0.02},  # 0.5% - 10%
        "max_drawdown_limit": {"min": 0.05, "max": 0.50, "default": 0.15},  # 5% - 50%
        "leverage_limit": {"min": 1.0, "max": 5.0, "default": 2.0},
        "position_size_limit": {"min": 0.05, "max": 0.50, "default": 0.30},  # 5% - 50%
        "commission_rate": {"min": 0.0, "max": 0.01, "default": 0.001},  # 0% - 1%
        "slippage_rate": {"min": 0.0, "max": 0.01, "default": 0.0005}  # 0% - 1%
    }

    # Capital limits
    CAPITAL_LIMITS = {
        "min_initial_capital": 10000,  # $10,000
        "max_initial_capital": 1000000000,  # $1B
        "recommended_min": 100000  # $100,000
    }

    def __init__(self):
        """Initialize validator with custom settings"""
        self.custom_validators = {}
        self.data_provider = None  # Optional data provider for validation

    def validate_strategy_config(self, strategy: Dict[str, Any]) -> ValidationResult:
        """
        Validate strategy configuration

        Args:
            strategy: Strategy configuration dictionary

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(True, [], [], {})

        # Validate required fields
        required_fields = ["name", "type", "symbols"]
        for field in required_fields:
            if field not in strategy:
                result.add_error(field, f"Required field '{field}' is missing")

        # Validate strategy name
        if "name" in strategy:
            name = strategy["name"]
            if not isinstance(name, str) or len(name.strip()) == 0:
                result.add_error("name", "Strategy name must be a non-empty string")
            elif len(name) > 100:
                result.add_warning("Strategy name is very long")

        # Validate strategy type
        if "type" in strategy:
            strategy_type = strategy["type"]
            if strategy_type not in self.STRATEGY_TEMPLATES:
                valid_types = list(self.STRATEGY_TEMPLATES.keys())
                result.add_error(
                    "type",
                    f"Invalid strategy type '{strategy_type}'. Valid types: {valid_types}"
                )
            else:
                # Validate strategy parameters
                self._validate_strategy_parameters(strategy_type, strategy.get("parameters", {}), result)

        # Validate symbols
        if "symbols" in strategy:
            self._validate_symbols(strategy["symbols"], result)

        # Validate custom strategy code if provided
        if "code" in strategy and strategy["code"]:
            self._validate_strategy_code(strategy["code"], result)

        return result

    def validate_backtest_request(self, request: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete backtest request

        Args:
            request: Full backtest request dictionary

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(True, [], [], {})

        # Validate strategy config
        if "strategy" not in request:
            result.add_error("strategy", "Strategy configuration is required")
        else:
            strategy_result = self.validate_strategy_config(request["strategy"])
            result.errors.extend(strategy_result.errors)
            result.warnings.extend(strategy_result.warnings)

        # Validate date range
        self._validate_date_range(request, result)

        # Validate capital
        self._validate_capital(request, result)

        # Validate risk settings
        self._validate_risk_settings(request, result)

        # Validate execution settings
        self._validate_execution_settings(request, result)

        # Check data availability if data provider is set
        if self.data_provider and "strategy" in request:
            self._validate_data_availability(request["strategy"], request.get("start_date"), request.get("end_date"), result)

        # Check for potential issues
        self._check_potential_issues(request, result)

        result.is_valid = len(result.errors) == 0
        return result

    def validate_batch_request(self, batch_request: Dict[str, Any]) -> ValidationResult:
        """
        Validate batch backtest request

        Args:
            batch_request: Batch request dictionary

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(True, [], [], {})

        # Check requests field
        if "requests" not in batch_request:
            result.add_error("requests", "Batch requests field is required")
            return result

        requests = batch_request["requests"]
        if not isinstance(requests, list):
            result.add_error("requests", "Must be a list of backtest requests")
            return result

        # Validate number of requests
        if len(requests) > 100:
            result.add_error("requests", "Maximum 100 backtests allowed in batch")
        elif len(requests) == 0:
            result.add_error("requests", "At least one backtest request is required")

        # Validate each request
        total_capital = 0
        for i, req in enumerate(requests):
            req_result = self.validate_backtest_request(req)

            # Add index to field errors for clarity
            for field, errors in req_result.field_errors.items():
                for error in errors:
                    result.add_error(f"requests[{i}].{field}", error)

            result.warnings.extend(req_result.warnings)

            # Track total capital
            if "initial_capital" in req:
                try:
                    total_capital += float(req["initial_capital"])
                except:
                    pass

        # Validate batch settings
        if "max_concurrent" in batch_request:
            max_concurrent = batch_request["max_concurrent"]
            if not isinstance(max_concurrent, int) or max_concurrent < 1 or max_concurrent > 20:
                result.add_error("max_concurrent", "Must be an integer between 1 and 20")

        # Warning for large batches
        if len(requests) > 50:
            result.add_warning(f"Large batch of {len(requests)} backtests may take significant time to complete")

        # Warning for total capital
        if total_capital > 100000000:  # $100M
            result.add_warning(f"Large total capital requested: ${total_capital:,.0f}")

        result.is_valid = len(result.errors) == 0
        return result

    def _validate_strategy_parameters(self, strategy_type: str, parameters: Dict[str, Any], result: ValidationResult):
        """Validate strategy-specific parameters"""
        template = self.STRATEGY_TEMPLATES.get(strategy_type, {})

        # Check required parameters
        for param in template.get("required", []):
            if param not in parameters:
                result.add_error(f"parameters.{param}", f"Required parameter '{param}' is missing")

        # Validate parameter values
        constraints = template.get("constraints", {})
        optional = template.get("optional", {})

        for param, value in parameters.items():
            if param in constraints:
                constraint = constraints[param]
                self._validate_parameter_value(param, value, constraint, result)
            elif param in optional:
                opt_constraint = optional[param]
                self._validate_parameter_value(param, value, opt_constraint, result)
            else:
                result.add_warning(f"Unknown strategy parameter: {param}")

    def _validate_parameter_value(self, param_name: str, value: Any, constraint: Dict[str, Any], result: ValidationResult):
        """Validate individual parameter value"""
        # Check type
        expected_type = constraint.get("type")
        if expected_type and not isinstance(value, expected_type):
            result.add_error(
                f"parameters.{param_name}",
                f"Must be of type {expected_type.__name__}, got {type(value).__name__}"
            )

        # Check range
        if isinstance(value, (int, float)):
            min_val = constraint.get("min")
            max_val = constraint.get("max")
            if min_val is not None and value < min_val:
                result.add_error(
                    f"parameters.{param_name}",
                    f"Value {value} is below minimum {min_val}"
                )
            if max_val is not None and value > max_val:
                result.add_error(
                    f"parameters.{param_name}",
                    f"Value {value} is above maximum {max_val}"
                )

        # Check choices
        choices = constraint.get("choices")
        if choices and value not in choices:
            result.add_error(
                f"parameters.{param_name}",
                f"Value '{value}' not in valid choices: {choices}"
            )

    def _validate_symbols(self, symbols: List[str], result: ValidationResult):
        """Validate trading symbols"""
        if not isinstance(symbols, list):
            result.add_error("symbols", "Must be a list of symbols")
            return

        if len(symbols) == 0:
            result.add_error("symbols", "At least one symbol is required")
        elif len(symbols) > 100:
            result.add_error("symbols", "Maximum 100 symbols allowed")

        # Check each symbol
        valid_symbols = 0
        for symbol in symbols:
            if not isinstance(symbol, str):
                result.add_error(f"symbols.{symbol}", "Symbol must be a string")
                continue

            # Check symbol format
            if self.STOCK_PATTERN.match(symbol) or self.CRYPTO_PATTERN.match(symbol):
                valid_symbols += 1
            else:
                result.add_warning(f"Unusual symbol format: {symbol}")

        if valid_symbols == 0:
            result.add_error("symbols", "No valid symbols found")

    def _validate_strategy_code(self, code: str, result: ValidationResult):
        """Validate custom strategy code"""
        if len(code) > 10000:
            result.add_warning("Strategy code is very long and may impact performance")

        # Basic code validation (can be enhanced with actual Python linting)
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            result.add_error("code", f"Syntax error in strategy code: {e}")

        # Check for dangerous functions
        dangerous_patterns = [
            "eval(", "exec(", "compile(", "open(", "file(",
            "import os", "import sys", "subprocess", "__import__"
        ]
        for pattern in dangerous_patterns:
            if pattern in code:
                result.add_error("code", f"Use of dangerous function: {pattern}")

    def _validate_date_range(self, request: Dict[str, Any], result: ValidationResult):
        """Validate backtest date range"""
        start_date = request.get("start_date")
        end_date = request.get("end_date")

        if not start_date or not end_date:
            result.add_error("date_range", "Both start_date and end_date are required")
            return

        # Parse dates
        try:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError as e:
            result.add_error("date_range", f"Invalid date format: {e}")
            return

        # Check date order
        if end_date <= start_date:
            result.add_error("date_range", "end_date must be after start_date")

        # Check range length
        duration = end_date - start_date
        min_days = timedelta(days=7)
        max_days = timedelta(days=3650)  # 10 years

        if duration < min_days:
            result.add_error("date_range", "Minimum backtest period is 7 days")
        elif duration > max_days:
            result.add_error("date_range", "Maximum backtest period is 10 years")

        # Check if dates are in the past
        now = datetime.utcnow()
        if start_date > now:
            result.add_error("start_date", "Start date cannot be in the future")
        if end_date > now + timedelta(days=1):
            result.add_warning("end_date", "End date is in the future")

    def _validate_capital(self, request: Dict[str, Any], result: ValidationResult):
        """Validate initial capital"""
        capital = request.get("initial_capital")

        if capital is None:
            result.add_error("initial_capital", "Initial capital is required")
            return

        try:
            capital_value = float(capital)
        except (ValueError, TypeError):
            result.add_error("initial_capital", "Must be a valid number")
            return

        # Check limits
        if capital_value < self.CAPITAL_LIMITS["min_initial_capital"]:
            result.add_error(
                "initial_capital",
                f"Minimum capital is ${self.CAPITAL_LIMITS['min_initial_capital']:,.0f}"
            )
        elif capital_value > self.CAPITAL_LIMITS["max_initial_capital"]:
            result.add_error(
                "initial_capital",
                f"Maximum capital is ${self.CAPITAL_LIMITS['max_initial_capital']:,.0f}"
            )
        elif capital_value < self.CAPITAL_LIMITS["recommended_min"]:
            result.add_warning(
                f"Low capital (${capital_value:,.0f}). Recommended minimum is "
                f"${self.CAPITAL_LIMITS['recommended_min']:,.0f}"
            )

    def _validate_risk_settings(self, request: Dict[str, Any], result: ValidationResult):
        """Validate risk management settings"""
        for param, limits in self.RISK_LIMITS.items():
            value = request.get(param)

            if value is not None:
                try:
                    value_float = float(value)
                    if value_float < limits["min"] or value_float > limits["max"]:
                        result.add_error(
                            param,
                            f"Must be between {limits['min']:.3f} and {limits['max']:.3f}"
                        )
                except (ValueError, TypeError):
                    result.add_error(param, "Must be a valid number")

    def _validate_execution_settings(self, request: Dict[str, Any], result: ValidationResult):
        """Validate execution and advanced settings"""
        # Validate backtest type
        backtest_type = request.get("backtest_type")
        if backtest_type:
            valid_types = ["standard", "risk_managed", "stress_test", "monte_carlo", "parameter_sweep"]
            if backtest_type not in valid_types:
                result.add_error(
                    "backtest_type",
                    f"Invalid type. Valid options: {valid_types}"
                )

        # Validate Monte Carlo settings
        if request.get("enable_monte_carlo", False):
            simulations = request.get("monte_carlo_simulations", 0)
            if not isinstance(simulations, int) or simulations < 100 or simulations > 10000:
                result.add_error(
                    "monte_carlo_simulations",
                    "Must be an integer between 100 and 10000 for Monte Carlo"
                )

        # Validate priority
        priority = request.get("priority")
        if priority:
            valid_priorities = ["low", "normal", "high", "urgent"]
            if priority not in valid_priorities:
                result.add_error(
                    "priority",
                    f"Invalid priority. Valid options: {valid_priorities}"
                )

    def _validate_data_availability(self, strategy: Dict[str, Any], start_date: datetime, end_date: datetime, result: ValidationResult):
        """Validate data availability for symbols and date range"""
        # This would integrate with actual data provider
        # For now, just add a warning
        result.add_warning("Data availability not verified")

    def _check_potential_issues(self, request: Dict[str, Any], result: ValidationResult):
        """Check for potential performance and configuration issues"""
        # Check for very long backtests
        if "start_date" in request and "end_date" in request:
            try:
                start = request["start_date"]
                end = request["end_date"]
                if isinstance(start, str):
                    start = datetime.fromisoformat(start.replace('Z', '+00:00'))
                if isinstance(end, str):
                    end = datetime.fromisoformat(end.replace('Z', '+00:00'))

                duration = end - start
                if duration.days > 365 * 5:  # 5 years
                    result.add_warning("Very long backtest period may take significant time")
            except:
                pass

        # Check for many symbols
        strategy = request.get("strategy", {})
        symbols = strategy.get("symbols", [])
        if len(symbols) > 50:
            result.add_warning(f"Large number of symbols ({len(symbols)}) may impact performance")

        # Check for high leverage
        leverage = request.get("leverage_limit", 1.0)
        try:
            leverage_float = float(leverage)
            if leverage_float > 3.0:
                result.add_warning("High leverage increases risk significantly")
        except:
            pass

        # Check for very tight risk limits
        var_limit = request.get("var_limit", 0.02)
        try:
            var_float = float(var_limit)
            if var_float < 0.005:  # 0.5%
                result.add_warning("Very low VaR limit may result in frequent position reductions")
        except:
            pass


def create_validator() -> BacktestConfigValidator:
    """Create and return a configured validator instance"""
    validator = BacktestConfigValidator()

    # Add custom validators if needed
    # validator.custom_validators["custom_strategy"] = validate_custom_strategy

    return validator


# Example usage
if __name__ == "__main__":
    # Create validator
    validator = create_validator()

    # Example backtest request
    example_request = {
        "strategy": {
            "name": "MA Crossover Strategy",
            "type": "ma_cross",
            "symbols": ["AAPL", "GOOGL", "MSFT"],
            "parameters": {
                "short_period": 20,
                "long_period": 50,
                "signal_threshold": 0.01
            }
        },
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 1000000,
        "commission_rate": 0.001,
        "var_limit": 0.02,
        "max_drawdown_limit": 0.15,
        "backtest_type": "risk_managed"
    }

    # Validate request
    result = validator.validate_backtest_request(example_request)

    # Print results
    print(f"Validation Result: {'✅ Valid' if result.is_valid else '❌ Invalid'}")
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")