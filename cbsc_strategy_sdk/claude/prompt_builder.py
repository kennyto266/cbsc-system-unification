"""
Prompt Builder for Claude API

Constructs optimized prompts for various code generation tasks
including strategy generation, parameter optimization, and error analysis.
"""

from typing import Any, Optional
from .templates.base import StrategyType, TemplateContext


class PromptBuilder:
    """
    Build prompts for Claude API interactions.

    Creates structured, context-aware prompts for different
    code generation and analysis tasks.

    Example:
        >>> builder = PromptBuilder()
        >>> prompt = builder.build_generation_prompt(
        ...     "Moving average crossover",
        ...     MomentumTemplate()
        ... )
    """

    def __init__(self):
        """Initialize prompt builder."""
        self._system_prompt = self._get_default_system_prompt()

    def build_generation_prompt(
        self,
        description: str,
        strategy_type: StrategyType,
        context: Optional[dict[str, Any]] = None,
        examples: Optional[list[str]] = None,
    ) -> str:
        """
        Build prompt for strategy code generation.

        Args:
            description: Natural language description of desired strategy
            strategy_type: Type of strategy to generate
            context: Additional context (parameters, indicators, etc.)
            examples: Optional code examples for few-shot learning

        Returns:
            Complete prompt for code generation
        """
        sections = []

        # Task description
        sections.append(self._format_section("Task", description))

        # Strategy type
        sections.append(
            self._format_section(
                "Strategy Type",
                f"Generate a {strategy_type.value.replace('_', ' ')} strategy."
            )
        )

        # Requirements
        requirements = self._get_generation_requirements(strategy_type)
        sections.append(self._format_section("Requirements", requirements))

        # Code standards
        sections.append(
            self._format_section(
                "Code Standards",
                self._get_code_standards()
            )
        )

        # Context if provided
        if context:
            context_str = self._format_context(context)
            sections.append(self._format_section("Context", context_str))

        # Examples if provided
        if examples:
            examples_str = self._format_examples(examples)
            sections.append(self._format_section("Examples", examples_str))

        # Output format
        sections.append(
            self._format_section(
                "Output Format",
                "Provide complete, executable Python code that can be run immediately."
            )
        )

        return "\n\n".join(sections)

    def build_optimization_prompt(
        self,
        code: str,
        performance_metrics: dict[str, Any],
        constraints: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Build prompt for parameter optimization.

        Args:
            code: Current strategy code
            performance_metrics: Dictionary of current performance metrics
            constraints: Optional constraints for optimization

        Returns:
            Prompt for parameter optimization
        """
        sections = []

        # Task description
        sections.append(
            self._format_section(
                "Task",
                "Analyze the trading strategy and suggest parameter optimizations "
                "to improve performance while managing risk."
            )
        )

        # Current code
        sections.append(
            self._format_section("Current Strategy Code", code)
        )

        # Performance metrics
        metrics_str = self._format_metrics(performance_metrics)
        sections.append(
            self._format_section("Current Performance", metrics_str)
        )

        # Constraints if provided
        if constraints:
            constraints_str = self._format_constraints(constraints)
            sections.append(
                self._format_section("Optimization Constraints", constraints_str)
            )

        # Analysis requirements
        sections.append(
            self._format_section(
                "Analysis Required",
                """
1. Identify parameters that can be optimized
2. Suggest specific parameter values with rationale
3. Explain expected impact on performance
4. Highlight any potential risks or trade-offs
5. Provide confidence level for each suggestion
"""
            )
        )

        return "\n\n".join(sections)

    def build_analysis_prompt(
        self,
        code: str,
        error_message: str,
        stack_trace: Optional[str] = None,
    ) -> str:
        """
        Build prompt for error analysis.

        Args:
            code: Code that caused the error
            error_message: Error message received
            stack_trace: Optional stack trace

        Returns:
            Prompt for error analysis
        """
        sections = []

        # Task description
        sections.append(
            self._format_section(
                "Task",
                "Analyze the error and provide a fix for the trading strategy code."
            )
        )

        # Error details
        error_section = f"Error: {error_message}"
        if stack_trace:
            error_section += f"\n\nStack Trace:\n```\n{stack_trace}\n```"
        sections.append(self._format_section("Error Details", error_section))

        # Problematic code
        sections.append(self._format_section("Code", code))

        # Fix requirements
        sections.append(
            self._format_section(
                "Fix Required",
                """
1. Identify the root cause of the error
2. Provide corrected code
3. Explain the fix in clear terms
4. Suggest how to prevent similar errors
5. Ensure the fix maintains strategy logic
"""
            )
        )

        return "\n\n".join(sections)

    def build_refactor_prompt(
        self,
        code: str,
        refactoring_goals: list[str],
    ) -> str:
        """
        Build prompt for code refactoring.

        Args:
            code: Code to refactor
            refactoring_goals: List of refactoring objectives

        Returns:
            Prompt for code refactoring
        """
        sections = []

        # Task description
        sections.append(
            self._format_section(
                "Task",
                "Refactor the trading strategy code to improve quality, "
                "maintainability, and performance."
            )
        )

        # Current code
        sections.append(self._format_section("Current Code", code))

        # Refactoring goals
        goals_str = "\n".join(f"- {goal}" for goal in refactoring_goals)
        sections.append(
            self._format_section("Refactoring Goals", goals_str)
        )

        # Refactoring guidelines
        sections.append(
            self._format_section(
                "Guidelines",
                """
- Preserve the original strategy logic
- Follow PEP 8 style guidelines
- Add type hints where appropriate
- Improve code readability
- Add helpful comments
- Consider performance optimizations
"""
            )
        )

        return "\n\n".join(sections)

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for Claude."""
        return """You are an expert quantitative trading strategy developer specializing in Python.

Your role is to generate, analyze, and optimize trading strategy code following CBSC best practices.

Core Principles:
- Code should be immediately executable
- Use type hints for all function signatures
- Include comprehensive docstrings
- Follow PEP 8 formatting
- Handle edge cases and errors gracefully
- Prioritize code clarity and maintainability
- Use modern Python patterns (dataclasses, type hints, etc.)"""

    def _get_generation_requirements(self, strategy_type: StrategyType) -> str:
        """Get requirements for specific strategy type."""
        base_requirements = """
- Complete, executable Python class
- Type hints on all methods
- Comprehensive docstrings
- Proper error handling
- generate_signals() method
- backtest() method with performance metrics
"""

        type_specific = {
            StrategyType.MOMENTUM: "- Momentum calculation based on price changes\n- Threshold-based signal generation",
            StrategyType.MEAN_REVERSION: "- Mean and standard deviation calculations\n- Z-score based signals",
            StrategyType.ARBITRAGE: "- Spread calculation between assets\n- Hedge ratio calculation",
            StrategyType.PAIR_TRADING: "- Cointegration testing\n- Spread trading signals",
            StrategyType.ML_STRATEGY: "- Feature engineering\n- Model training\n- Prediction-based signals",
        }

        return base_requirements + type_specific.get(
            strategy_type,
            "- Clear entry and exit logic\n- Risk management considerations"
        )

    def _get_code_standards(self) -> str:
        """Get CBSC code standards."""
        return """
```python
# Import required libraries
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class StrategyName:
    \"\"\"
    Clear, concise description of strategy.

    Args:
        param1: Description
        param2: Description
    \"\"\"

    def __init__(self, param1: type, param2: type):
        \"\"\"Initialize strategy with parameters.\"\"\"
        self.param1 = param1
        self.param2 = param2

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        \"\"\"
        Generate trading signals.

        Args:
            data: OHLCV data DataFrame

        Returns:
            Series of signals (1=long, -1=short, 0=neutral)
        \"\"\"
        # Implementation
        pass

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000
    ) -> Dict[str, Any]:
        \"\"\"
        Run backtest on historical data.

        Returns:
            Dictionary with performance metrics
        \"\"\"
        # Implementation
        pass
```
"""

    def _format_section(self, title: str, content: str) -> str:
        """Format a prompt section."""
        return f"## {title}\n\n{content}"

    def _format_context(self, context: dict[str, Any]) -> str:
        """Format context dictionary."""
        lines = []
        for key, value in context.items():
            if isinstance(value, (list, dict)):
                lines.append(f"- **{key}**: {value}")
            else:
                lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)

    def _format_examples(self, examples: list[str]) -> str:
        """Format code examples."""
        formatted = []
        for i, example in enumerate(examples, 1):
            formatted.append(f"### Example {i}\n```python\n{example}\n```")
        return "\n\n".join(formatted)

    def _format_metrics(self, metrics: dict[str, Any]) -> str:
        """Format performance metrics."""
        lines = []
        for key, value in metrics.items():
            if isinstance(value, float):
                lines.append(f"- **{key}**: {value:.4f}")
            else:
                lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)

    def _format_constraints(self, constraints: dict[str, Any]) -> str:
        """Format optimization constraints."""
        lines = []
        for key, value in constraints.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)

    def get_system_prompt(self) -> str:
        """Get the system prompt for API calls."""
        return self._system_prompt

    def set_system_prompt(self, prompt: str):
        """Set custom system prompt."""
        self._system_prompt = prompt
