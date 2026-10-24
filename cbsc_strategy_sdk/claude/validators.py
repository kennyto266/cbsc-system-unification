"""
Code Validators

Validate generated trading strategy code for syntax,
imports, structure, and CBSC compliance.
"""

import ast
import re
from typing import Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    suggestions: list[str]

    def __bool__(self) -> bool:
        return self.is_valid


class CodeValidator:
    """
    Validate generated trading strategy code.

    Checks for:
    - Syntax errors
    - Required imports
    - Class structure
    - Required methods
    - Type hints
    - Common patterns

    Example:
        >>> validator = CodeValidator()
        >>> result = validator.validate(code)
        >>> if result:
        ...     print("Code is valid!")
    """

    # Required imports for trading strategies
    REQUIRED_IMPORTS = {
        "pandas",
        "numpy",
    }

    # Required methods for strategy classes
    REQUIRED_METHODS = {
        "generate_signals",
        "backtest",
    }

    # Recommended patterns
    RECOMMENDED_PATTERNS = [
        r"def generate_signals\(self, data: pd\.DataFrame\)",
        r"def backtest\(self",
        r": pd\.Series",
        r": Dict\[str, Any\]",
        r"\"\"\"",
    ]

    def __init__(self):
        """Initialize code validator."""
        self.errors = []
        self.warnings = []
        self.suggestions = []

    def validate(self, code: str) -> ValidationResult:
        """
        Validate generated code.

        Args:
            code: Python code to validate

        Returns:
            ValidationResult with details
        """
        self.errors = []
        self.warnings = []
        self.suggestions = []

        # Check syntax
        self._check_syntax(code)

        # If syntax errors exist, skip further checks
        if self.errors:
            return ValidationResult(
                is_valid=False,
                errors=self.errors,
                warnings=self.warnings,
                suggestions=self.suggestions,
            )

        # Check imports
        self._check_imports(code)

        # Check class structure
        self._check_class_structure(code)

        # Check required methods
        self._check_required_methods(code)

        # Check type hints
        self._check_type_hints(code)

        # Check docstrings
        self._check_docstrings(code)

        # Check for common issues
        self._check_common_issues(code)

        is_valid = len(self.errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            suggestions=self.suggestions,
        )

    def _check_syntax(self, code: str):
        """Check for syntax errors."""
        try:
            ast.parse(code)
        except SyntaxError as e:
            self.errors.append(
                f"Syntax error at line {e.lineno}: {e.msg}"
            )

    def _check_imports(self, code: str):
        """Check for required imports."""
        try:
            tree = ast.parse(code)
            imports_found = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_found.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports_found.add(node.module.split(".")[0])

            missing = self.REQUIRED_IMPORTS - imports_found
            if missing:
                self.errors.append(
                    f"Missing required imports: {', '.join(missing)}"
                )

        except Exception:
            # Syntax errors already reported
            pass

    def _check_class_structure(self, code: str):
        """Check for proper class structure."""
        try:
            tree = ast.parse(code)
            classes_found = [
                node.name for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            ]

            if not classes_found:
                self.errors.append(
                    "No class definition found. "
                    "Strategy code should define a class."
                )
                return

            # Check for __init__ method
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    has_init = any(
                        n.name == "__init__"
                        for n in node.body
                        if isinstance(n, ast.FunctionDef)
                    )
                    if not has_init:
                        self.warnings.append(
                            f"Class '{node.name}' missing __init__ method"
                        )

        except Exception:
            pass

    def _check_required_methods(self, code: str):
        """Check for required methods in strategy classes."""
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods_found = {
                        n.name for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    }

                    missing = self.REQUIRED_METHODS - methods_found
                    if missing:
                        self.errors.append(
                            f"Class '{node.name}' missing required methods: "
                            f"{', '.join(missing)}"
                        )

        except Exception:
            pass

    def _check_type_hints(self, code: str):
        """Check for type hints on functions."""
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for method in node.body:
                        if isinstance(method, ast.FunctionDef):
                            # Check return type annotation
                            if method.returns is None and method.name != "__init__":
                                self.suggestions.append(
                                    f"Method '{node.name}.{method.name}' "
                                    "missing return type hint"
                                )

                            # Check parameter type annotations
                            for arg in method.args.args:
                                if arg.arg != "self" and arg.annotation is None:
                                    self.suggestions.append(
                                        f"Parameter '{arg.arg}' in "
                                        f"'{node.name}.{method.name}' "
                                        "missing type hint"
                                    )

        except Exception:
            pass

    def _check_docstrings(self, code: str):
        """Check for docstrings."""
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        self.warnings.append(
                            f"Class '{node.name}' missing docstring"
                        )

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if not ast.get_docstring(item):
                                self.suggestions.append(
                                    f"Method '{node.name}.{item.name}' "
                                    "missing docstring"
                                )

        except Exception:
            pass

    def _check_common_issues(self, code: str):
        """Check for common code issues."""
        # Check for hardcoded values
        if re.search(r"\b(def|class)\s+\w+\s*\([^)]*123[^)]*\)", code):
            self.suggestions.append(
                "Avoid hardcoded values (e.g., '123') in function signatures"
            )

        # Check for print statements in production code
        if re.search(r"^\s*print\(", code, re.MULTILINE):
            self.warnings.append(
                "Consider using logging instead of print statements"
            )

        # Check for bare except clauses
        if re.search(r"except\s*:", code):
            self.warnings.append(
                "Avoid bare 'except:' clauses. "
                "Specify exception types."
            )

        # Check for TODO comments
        if re.search(r"#\s*TODO|#\s*FIXME", code, re.IGNORECASE):
            self.suggestions.append(
                "Code contains TODO/FIXME comments that should be addressed"
            )


class ParameterValidator:
    """
    Validate strategy parameters.

    Ensures parameters are within valid ranges and types.
    """

    @staticmethod
    def validate_parameter(
        name: str,
        value: Any,
        constraints: Optional[dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a single parameter.

        Args:
            name: Parameter name
            value: Parameter value
            constraints: Optional validation constraints

        Returns:
            Tuple of (is_valid, error_message)
        """
        if constraints is None:
            constraints = {}

        # Type validation
        expected_type = constraints.get("type")
        if expected_type and not isinstance(value, expected_type):
            return False, f"{name} must be {expected_type.__name__}, got {type(value).__name__}"

        # Range validation
        if "min" in constraints and value < constraints["min"]:
            return False, f"{name} must be >= {constraints['min']}"

        if "max" in constraints and value > constraints["max"]:
            return False, f"{name} must be <= {constraints['max']}"

        # Choices validation
        if "choices" in constraints and value not in constraints["choices"]:
            return False, f"{name} must be one of {constraints['choices']}"

        return True, None

    @staticmethod
    def validate_parameters(
        parameters: dict[str, Any],
        schema: dict[str, dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate multiple parameters.

        Args:
            parameters: Parameter dictionary
            schema: Validation schema

        Returns:
            ValidationResult with details
        """
        errors = []
        warnings = []
        suggestions = []

        # Check required parameters
        required = set(
            k for k, v in schema.items()
            if v.get("required", False)
        )
        missing = required - set(parameters.keys())

        if missing:
            errors.append(
                f"Missing required parameters: {', '.join(missing)}"
            )

        # Validate each parameter
        for name, value in parameters.items():
            if name not in schema:
                warnings.append(f"Unknown parameter: {name}")
                continue

            is_valid, error = ParameterValidator.validate_parameter(
                name, value, schema[name]
            )

            if not is_valid:
                errors.append(error)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )
