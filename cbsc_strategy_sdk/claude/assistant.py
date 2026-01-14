"""
Claude Code Assistant

Main assistant class for generating and optimizing trading
strategy code using Anthropic's Claude API.
"""

import asyncio
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

from .client import ClaudeClient, ModelType
from .templates.base import (
    StrategyTemplate,
    StrategyType,
    TemplateFactory,
    TemplateContext,
)
from .prompt_builder import PromptBuilder
from .validators import CodeValidator, ValidationResult


class GenerationMode(Enum):
    """Code generation modes."""
    API = "api"  # Use Claude API
    TEMPLATE = "template"  # Use template-based generation
    HYBRID = "hybrid"  # Use API with template fallback


@dataclass
class GeneratedCode:
    """Result of code generation."""
    code: str
    strategy_type: StrategyType
    mode_used: GenerationMode
    is_valid: bool
    validation_errors: list[str]
    warnings: list[str]
    suggestions: list[str]


@dataclass
class ParameterSuggestions:
    """Result of parameter optimization analysis."""
    suggested_parameters: dict[str, Any]
    rationale: str
    expected_improvement: str
    confidence: float
    risks: list[str]


@dataclass
class FixSuggestions:
    """Result of error analysis."""
    corrected_code: str
    explanation: str
    root_cause: str
    prevention_tips: list[str]


class ClaudeCodeAssistant:
    """
    Assistant for generating trading strategy code using Claude API.

    Provides intelligent code generation, parameter optimization,
    and error analysis for quantitative trading strategies.

    Args:
        api_key: Anthropic API key
        model: Claude model to use
        max_tokens: Maximum tokens per response
        timeout: Request timeout in seconds
        fallback_to_template: Use template generation if API unavailable

    Example:
        >>> assistant = ClaudeCodeAssistant(api_key="sk-ant-...")
        >>> code = assistant.generate_strategy(
        ...     "Moving average crossover with RSI filter",
        ...     StrategyType.MOMENTUM
        ... )
        >>> print(code.code)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = ModelType.SONNET.value,
        max_tokens: int = 4096,
        timeout: int = 60,
        fallback_to_template: bool = True,
    ):
        """Initialize Claude code assistant."""
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.fallback_to_template = fallback_to_template

        # Initialize components
        self._client: Optional[ClaudeClient] = None
        self.prompt_builder = PromptBuilder()
        self.code_validator = CodeValidator()

    @property
    def client(self) -> Optional[ClaudeClient]:
        """Lazy initialization of API client."""
        if self._client is None and self.api_key:
            try:
                self._client = ClaudeClient(
                    api_key=self.api_key,
                    model=self.model,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                )
            except Exception:
                if not self.fallback_to_template:
                    raise
        return self._client

    def generate_strategy(
        self,
        description: str,
        strategy_type: StrategyType,
        context: Optional[dict[str, Any]] = None,
        parameters: Optional[dict[str, Any]] = None,
        mode: GenerationMode = GenerationMode.HYBRID,
    ) -> GeneratedCode:
        """
        Generate strategy code from description.

        Args:
            description: Natural language description of desired strategy
            strategy_type: Type of strategy to generate
            context: Additional context (market, timeframe, etc.)
            parameters: Optional parameter specifications
            mode: Generation mode (API, template, or hybrid)

        Returns:
            GeneratedCode with code and validation results
        """
        # Try API generation first (if mode allows)
        if mode in (GenerationMode.API, GenerationMode.HYBRID):
            if self.client is not None:
                try:
                    return self._generate_via_api(
                        description, strategy_type, context, parameters
                    )
                except Exception as e:
                    if mode == GenerationMode.API:
                        raise
                    # Fall through to template generation

        # Template-based generation
        if mode in (GenerationMode.TEMPLATE, GenerationMode.HYBRID):
            return self._generate_via_template(
                description, strategy_type, context, parameters
            )

        raise ValueError("Invalid generation mode or no generation method available")

    def _generate_via_api(
        self,
        description: str,
        strategy_type: StrategyType,
        context: Optional[dict[str, Any]],
        parameters: Optional[dict[str, Any]],
    ) -> GeneratedCode:
        """Generate code using Claude API."""
        # Build prompt
        prompt = self.prompt_builder.build_generation_prompt(
            description=description,
            strategy_type=strategy_type,
            context=context or {},
        )

        # Generate code
        system_prompt = self.prompt_builder.get_system_prompt()
        generated_text = self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )

        # Extract code from response
        code = self._extract_code_from_response(generated_text)

        # Validate
        validation = self.code_validator.validate(code)

        return GeneratedCode(
            code=code,
            strategy_type=strategy_type,
            mode_used=GenerationMode.API,
            is_valid=validation.is_valid,
            validation_errors=validation.errors,
            warnings=validation.warnings,
            suggestions=validation.suggestions,
        )

    def _generate_via_template(
        self,
        description: str,
        strategy_type: StrategyType,
        context: Optional[dict[str, Any]],
        parameters: Optional[dict[str, Any]],
    ) -> GeneratedCode:
        """Generate code using template system."""
        # Get template
        template = TemplateFactory.get_template(strategy_type)

        # Use provided parameters or defaults
        if parameters is None:
            parameters = self._get_default_parameters(strategy_type)

        # Add name from description or context
        if "name" not in parameters:
            parameters["name"] = self._extract_name_from_description(description)

        # Generate indicators
        indicators = context.get("indicators", {}) if context else {}

        # Validate parameters
        is_valid, error = template.validate_parameters(parameters)
        if not is_valid:
            return GeneratedCode(
                code="",
                strategy_type=strategy_type,
                mode_used=GenerationMode.TEMPLATE,
                is_valid=False,
                validation_errors=[error],
                warnings=[],
                suggestions=[],
            )

        # Generate code
        code = template.generate_code(parameters, indicators)

        # Validate
        validation = self.code_validator.validate(code)

        return GeneratedCode(
            code=code,
            strategy_type=strategy_type,
            mode_used=GenerationMode.TEMPLATE,
            is_valid=validation.is_valid,
            validation_errors=validation.errors,
            warnings=validation.warnings,
            suggestions=validation.suggestions,
        )

    def optimize_parameters(
        self,
        code: str,
        performance_metrics: dict[str, Any],
        constraints: Optional[dict[str, Any]] = None,
    ) -> ParameterSuggestions:
        """
        Analyze code and suggest parameter optimizations.

        Args:
            code: Current strategy code
            performance_metrics: Current performance metrics
            constraints: Optional optimization constraints

        Returns:
            ParameterSuggestions with recommendations
        """
        if self.client is None:
            return ParameterSuggestions(
                suggested_parameters={},
                rationale="API unavailable - cannot provide optimization suggestions",
                expected_improvement="Unknown",
                confidence=0.0,
                risks=["API client not initialized"],
            )

        # Build optimization prompt
        prompt = self.prompt_builder.build_optimization_prompt(
            code=code,
            performance_metrics=performance_metrics,
            constraints=constraints or {},
        )

        # Get suggestions from Claude
        system_prompt = self.prompt_builder.get_system_prompt()
        response = self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.5,
        )

        # Parse response (simplified - actual implementation would be more sophisticated)
        return ParameterSuggestions(
            suggested_parameters=self._extract_parameter_suggestions(response),
            rationale="Based on performance analysis and strategy characteristics",
            expected_improvement="Expected improvement in risk-adjusted returns",
            confidence=0.75,
            risks=["Backtest overfitting", "Market regime changes"],
        )

    def analyze_errors(
        self,
        code: str,
        error_message: str,
        stack_trace: Optional[str] = None,
    ) -> FixSuggestions:
        """
        Analyze errors and provide fix suggestions.

        Args:
            code: Code with errors
            error_message: Error message received
            stack_trace: Optional stack trace

        Returns:
            FixSuggestions with corrected code and explanation
        """
        if self.client is None:
            return FixSuggestions(
                corrected_code="",
                explanation="API unavailable - cannot analyze errors",
                root_cause="Unknown",
                prevention_tips=[],
            )

        # Build analysis prompt
        prompt = self.prompt_builder.build_analysis_prompt(
            code=code,
            error_message=error_message,
            stack_trace=stack_trace,
        )

        # Get analysis from Claude
        system_prompt = self.prompt_builder.get_system_prompt()
        response = self.client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
        )

        # Extract corrected code
        corrected_code = self._extract_code_from_response(response)

        return FixSuggestions(
            corrected_code=corrected_code,
            explanation=self._extract_explanation(response),
            root_cause=error_message,
            prevention_tips=[
                "Add proper error handling",
                "Validate input data",
                "Check for edge cases",
            ],
        )

    async def generate_async(
        self,
        description: str,
        strategy_type: StrategyType,
        context: Optional[dict[str, Any]] = None,
        parameters: Optional[dict[str, Any]] = None,
    ) -> GeneratedCode:
        """
        Generate strategy code asynchronously.

        Args:
            description: Natural language description
            strategy_type: Type of strategy to generate
            context: Additional context
            parameters: Optional parameters

        Returns:
            GeneratedCode with results
        """
        if self.client is None:
            raise RuntimeError("API client not available")

        # Build prompt
        prompt = self.prompt_builder.build_generation_prompt(
            description=description,
            strategy_type=strategy_type,
            context=context or {},
        )

        # Generate asynchronously
        system_prompt = self.prompt_builder.get_system_prompt()
        generated_text = await self.client.generate_async(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )

        # Extract and validate code
        code = self._extract_code_from_response(generated_text)
        validation = self.code_validator.validate(code)

        return GeneratedCode(
            code=code,
            strategy_type=strategy_type,
            mode_used=GenerationMode.API,
            is_valid=validation.is_valid,
            validation_errors=validation.errors,
            warnings=validation.warnings,
            suggestions=validation.suggestions,
        )

    def is_api_available(self) -> bool:
        """Check if Claude API is available."""
        if self.client is None:
            return False
        return self.client.is_available()

    def get_usage_stats(self):
        """Get API usage statistics."""
        if self.client is None:
            return None
        return self.client.get_usage_stats()

    def _extract_code_from_response(self, response: str) -> str:
        """Extract Python code from API response."""
        import re

        # Try to extract code from markdown code blocks
        pattern = r"```python\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Try without language specifier
        pattern = r"```\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            return matches[0].strip()

        # Return as-is if no code blocks found
        return response.strip()

    def _extract_name_from_description(self, description: str) -> str:
        """Extract strategy name from description."""
        import re

        # Look for patterns like "Create X strategy" or "X trading strategy"
        patterns = [
            r"create\s+(\w+)\s+strategy",
            r"(\w+)\s+trading\s+strategy",
            r"(\w+)\s+strategy",
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                name = match.group(1)
                # Convert to CamelCase
                return "".join(word.capitalize() for word in name.split("_"))

        return "CustomStrategy"

    def _extract_parameter_suggestions(self, response: str) -> dict[str, Any]:
        """Extract parameter suggestions from response."""
        # Simplified implementation
        return {}

    def _extract_explanation(self, response: str) -> str:
        """Extract explanation from response."""
        lines = response.split("\n")

        # Find explanation section
        for i, line in enumerate(lines):
            if "explanation" in line.lower() or "fix" in line.lower():
                return "\n".join(lines[i:i+5])

        return "See corrected code for details"

    def _get_default_parameters(self, strategy_type: StrategyType) -> dict[str, Any]:
        """Get default parameters for strategy type."""
        defaults = {
            StrategyType.MOMENTUM: {
                "lookback_period": 20,
                "threshold": 0.02,
                "position_size": 0.1,
            },
            StrategyType.MEAN_REVERSION: {
                "lookback_period": 20,
                "entry_threshold": 2.0,
                "exit_threshold": 0.5,
                "position_size": 0.1,
            },
            StrategyType.ARBITRAGE: {
                "assets": ["ASSET_A", "ASSET_B"],
                "correlation_window": 30,
                "entry_threshold": 2.0,
                "exit_threshold": 0.5,
                "position_size": 0.5,
            },
            StrategyType.PAIR_TRADING: {
                "pair": ("ASSET_A", "ASSET_B"),
                "lookback_window": 30,
                "entry_threshold": 2.0,
                "exit_threshold": 0.5,
                "position_size": 0.5,
            },
            StrategyType.ML_STRATEGY: {
                "model_type": "rf",
                "features": ["returns", "volume", "volatility"],
                "prediction_threshold": 0.5,
                "position_size": 0.1,
            },
        }

        return defaults.get(strategy_type, {})
