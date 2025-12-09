"""
Secure Parameter Parser - Replaces dangerous eval() functions
Created: 2025-11-30
Purpose: Provide safe parameter parsing without remote code execution risks
"""

import ast
import re
from typing import Dict, List, Union, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SecureParameterParser:
    """Safe parameter parsing without eval() vulnerabilities"""

    # Whitelist of allowed functions and their safe implementations
    SAFE_FUNCTIONS = {
        'range': range,
        'list': list,
        'int': int,
        'float': float,
        'str': str,
        'len': len,
        'min': min,
        'max': max,
        'sum': sum,
        'sorted': sorted,
        'enumerate': enumerate,
        'zip': zip,
    }

    # Regex patterns for safe parsing
    RANGE_PATTERN = re.compile(r'^range\(\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)$')
    LIST_PATTERN = re.compile(r'^\[\s*(.*?)\s*\]$')

    @staticmethod
    def parse_parameter_ranges(range_dict: Dict[str, str]) -> Optional[Dict[str, List[Any]]]:
        """
        Safely parse parameter ranges without using eval()

        Args:
            range_dict: Dictionary with parameter names and range strings

        Returns:
            Parsed ranges or None if parsing fails
        """
        try:
            parsed_ranges = {}

            for param, range_str in range_dict.items():
                # Validate parameter name
                if not SecureParameterParser._validate_identifier(param):
                    logger.warning(f"Invalid parameter name: {param}")
                    return None

                # Parse the range string safely
                parsed_value = SecureParameterParser._parse_range_string(range_str)
                if parsed_value is None:
                    logger.warning(f"Failed to parse range for parameter {param}: {range_str}")
                    return None

                parsed_ranges[param] = parsed_value

            return parsed_ranges

        except Exception as e:
            logger.error(f"Parameter range parsing failed: {e}")
            return None

    @staticmethod
    def _validate_identifier(identifier: str) -> bool:
        """Validate parameter identifier is safe"""
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier))

    @staticmethod
    def _parse_range_string(range_str: str) -> Optional[List[Any]]:
        """
        Parse range string safely without eval()

        Supported formats:
        - range(10, 31, 2)
        - [20, 25, 30, 35]
        - Single values: "25"
        """
        range_str = range_str.strip()

        if range_str.startswith('range'):
            return SecureParameterParser._parse_range_function(range_str)
        elif range_str.startswith('['):
            return SecureParameterParser._parse_list_literal(range_str)
        else:
            # Single value
            return SecureParameterParser._parse_single_value(range_str)

    @staticmethod
    def _parse_range_function(range_str: str) -> Optional[List[int]]:
        """Parse range() function safely"""
        match = SecureParameterParser.RANGE_PATTERN.match(range_str)
        if not match:
            return None

        try:
            start = int(match.group(1))
            end = int(match.group(2))
            step = int(match.group(3)) if match.group(3) else 1

            # Validate range parameters
            if start < 0 or end < 0 or step <= 0:
                logger.warning(f"Invalid range parameters: start={start}, end={end}, step={step}")
                return None

            if start >= end:
                logger.warning(f"Range start must be less than end: start={start}, end={end}")
                return None

            # Limit range size to prevent resource exhaustion
            range_size = (end - start + step - 1) // step
            if range_size > 10000:
                logger.warning(f"Range too large: {range_size} elements")
                return None

            return list(range(start, end, step))

        except ValueError as e:
            logger.warning(f"Invalid range parameters: {e}")
            return None

    @staticmethod
    def _parse_list_literal(list_str: str) -> Optional[List[Any]]:
        """Parse list literal safely"""
        match = SecureParameterParser.LIST_PATTERN.match(list_str)
        if not match:
            return None

        try:
            content = match.group(1).strip()
            if not content:
                return []

            # Parse comma-separated values
            values = []
            for value_str in content.split(','):
                value_str = value_str.strip()
                if not value_str:
                    continue

                parsed_value = SecureParameterParser._parse_single_value(value_str)
                if parsed_value is None:
                    return None
                values.append(parsed_value)

            # Limit list size
            if len(values) > 1000:
                logger.warning(f"List too large: {len(values)} elements")
                return None

            return values

        except Exception as e:
            logger.warning(f"List parsing failed: {e}")
            return None

    @staticmethod
    def _parse_single_value(value_str: str) -> Optional[Any]:
        """Parse single value safely"""
        value_str = value_str.strip()

        if not value_str:
            return None

        # Try integer
        if re.match(r'^-?\d+$', value_str):
            try:
                return int(value_str)
            except ValueError:
                pass

        # Try float
        if re.match(r'^-?\d*\.\d+$', value_str):
            try:
                return float(value_str)
            except ValueError:
                pass

        # Try string (quoted)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]  # Remove quotes

        # Unquoted string (validate safety)
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value_str):
            return value_str

        logger.warning(f"Invalid value format: {value_str}")
        return None

    @staticmethod
    def evaluate_safe_expression(expression: str, allowed_variables: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        Safely evaluate mathematical expressions without eval()

        Args:
            expression: Mathematical expression to evaluate
            allowed_variables: Dictionary of allowed variables and their values

        Returns:
            Evaluated result or None if evaluation fails
        """
        try:
            # Parse expression using AST
            tree = ast.parse(expression, mode='eval')

            # Create safe evaluator
            evaluator = SafeExpressionEvaluator(allowed_variables or {})

            # Evaluate expression
            result = evaluator.evaluate(tree.body)

            return result

        except Exception as e:
            logger.warning(f"Expression evaluation failed: {expression}, error: {e}")
            return None

class SafeExpressionEvaluator:
    """Safe AST-based expression evaluator"""

    def __init__(self, variables: Dict[str, Any]):
        self.variables = variables
        self.allowed_binops = {
            ast.Add: lambda x, y: x + y,
            ast.Sub: lambda x, y: x - y,
            ast.Mult: lambda x, y: x * y,
            ast.Div: lambda x, y: x / y,
            ast.FloorDiv: lambda x, y: x // y,
            ast.Mod: lambda x, y: x % y,
            ast.Pow: lambda x, y: x ** y,
        }

        self.allowed_unops = {
            ast.UAdd: lambda x: +x,
            ast.USub: lambda x: -x,
        }

    def evaluate(self, node: ast.AST) -> Any:
        """Evaluate AST node safely"""
        if isinstance(node, ast.BinOp):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)

            op_type = type(node.op)
            if op_type not in self.allowed_binops:
                raise ValueError(f"Operation not allowed: {op_type}")

            result = self.allowed_binops[op_type](left, right)

            # Check for reasonable result bounds
            if isinstance(result, (int, float)):
                if abs(result) > 1e10:
                    raise ValueError(f"Result too large: {result}")

            return result

        elif isinstance(node, ast.UnaryOp):
            operand = self.evaluate(node.operand)

            op_type = type(node.op)
            if op_type not in self.allowed_unops:
                raise ValueError(f"Unary operation not allowed: {op_type}")

            return self.allowed_unops[op_type](operand)

        elif isinstance(node, ast.Num):
            return node.n

        elif isinstance(node, ast.Constant):
            return node.value

        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            elif node.id in SecureParameterParser.SAFE_FUNCTIONS:
                return SecureParameterParser.SAFE_FUNCTIONS[node.id]
            else:
                raise ValueError(f"Variable not allowed: {node.id}")

        elif isinstance(node, ast.Call):
            # Only allow calls to safe functions
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in SecureParameterParser.SAFE_FUNCTIONS:
                    raise ValueError(f"Function not allowed: {func_name}")

                func = SecureParameterParser.SAFE_FUNCTIONS[func_name]
                args = [self.evaluate(arg) for arg in node.args]

                # Additional validation for range() calls
                if func_name == 'range':
                    if len(args) not in [1, 2, 3]:
                        raise ValueError("Invalid number of arguments for range()")

                    # Validate range parameters
                    for arg in args:
                        if not isinstance(arg, int) or arg < 0:
                            raise ValueError(f"Invalid range argument: {arg}")

                    # Limit range size
                    if len(args) >= 2:
                        start, stop = args[0], args[1]
                        step = args[2] if len(args) == 3 else 1
                        range_size = max(0, (stop - start + step - 1) // step)
                        if range_size > 10000:
                            raise ValueError(f"Range too large: {range_size}")

                return func(*args)
            else:
                raise ValueError("Complex function calls not allowed")

        else:
            raise ValueError(f"Expression type not allowed: {type(node)}")

# Convenience function for direct usage
def parse_parameter_ranges_safe(range_dict: Dict[str, str]) -> Optional[Dict[str, List[Any]]]:
    """Convenience function for safe parameter parsing"""
    return SecureParameterParser.parse_parameter_ranges(range_dict)