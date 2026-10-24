"""
Base Strategy Template

Abstract base class for all strategy templates.
Ensures consistent interface and code generation patterns.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass


class StrategyType(Enum):
    """Enumeration of supported strategy types."""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"
    PAIR_TRADING = "pair_trading"
    ML_STRATEGY = "ml_strategy"


@dataclass
class TemplateContext:
    """Context information for template rendering."""
    strategy_name: str
    description: str
    parameters: dict[str, Any]
    indicators: dict[str, Any]
    additional_context: Optional[dict[str, Any]] = None


class StrategyTemplate(ABC):
    """
    Abstract base class for strategy code templates.

    All concrete strategy templates must inherit from this class
    and implement the required methods.

    Example:
        >>> class MyTemplate(StrategyTemplate):
        ...     @property
        ...     def strategy_type(self) -> StrategyType:
        ...         return StrategyType.MOMENTUM
        ...
        ...     def generate_code(self, parameters, indicators) -> str:
        ...         return "class MyStrategy: ..."
    """

    @classmethod
    @abstractmethod
    def get_strategy_type(cls) -> StrategyType:
        """
        Return the strategy type enum value.

        Returns:
            StrategyType enum value for this template
        """
        pass

    @classmethod
    @abstractmethod
    def get_required_parameters(cls) -> list[str]:
        """
        List of required parameter names for this strategy type.

        Returns:
            List of parameter names that must be provided
        """
        pass

    @classmethod
    @abstractmethod
    def get_optional_parameters(cls) -> list[str]:
        """
        List of optional parameter names for this strategy type.

        Returns:
            List of optional parameter names
        """
        pass

    @classmethod
    def get_all_parameters(cls) -> list[str]:
        """Get all parameter names (required + optional)."""
        return cls.get_required_parameters() + cls.get_optional_parameters()

    @abstractmethod
    def generate_code(
        self,
        parameters: dict[str, Any],
        indicators: dict[str, Any],
    ) -> str:
        """
        Generate strategy code from template.

        Args:
            parameters: Strategy parameters
            indicators: Technical indicators and their configurations

        Returns:
            Complete, executable Python code as string
        """
        pass

    def validate_parameters(self, parameters: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate that all required parameters are present and valid.

        Args:
            parameters: Parameter dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        required = self.get_required_parameters()

        for param in required:
            if param not in parameters:
                return False, f"Missing required parameter: {param}"

        return self._validate_parameter_values(parameters)

    def _validate_parameter_values(
        self,
        parameters: dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate parameter values (override in subclasses for custom validation).

        Args:
            parameters: Parameter dictionary to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None

    def get_imports(self) -> list[str]:
        """
        Get list of required imports for this strategy type.

        Returns:
            List of import statements as strings
        """
        return [
            "import pandas as pd",
            "import numpy as np",
            "from typing import Optional, Dict, Any",
        ]

    def get_base_class(self) -> str:
        """
        Get the base class name for strategy inheritance.

        Returns:
            Base class name (e.g., "BaseStrategy")
        """
        return "BaseStrategy"

    def render_template(self, context: TemplateContext) -> str:
        """
        Render template with given context.

        Args:
            context: TemplateContext with rendering information

        Returns:
            Rendered code string
        """
        return self.generate_code(context.parameters, context.indicators)

    def get_documentation_template(self) -> str:
        """
        Get documentation template for this strategy type.

        Returns:
            Documentation string template
        """
        return f"""
# {self.get_strategy_type().value.replace('_', ' ').title()} Strategy

## Overview
[Strategy description]

## Parameters
{self._get_parameter_docs()}

## Signals
[Signal generation logic]

## Risk Management
[Risk management approach]
"""

    def _get_parameter_docs(self) -> str:
        """Generate parameter documentation."""
        lines = []
        for param in self.get_all_parameters():
            lines.append(f"- **{param}**: [Description]")
        return "\n".join(lines)


class TemplateFactory:
    """
    Factory class for creating strategy templates.

    Example:
        >>> factory = TemplateFactory()
        >>> template = factory.get_template(StrategyType.MOMENTUM)
        >>> code = template.generate_code(params, indicators)
    """

    _templates: dict[StrategyType, type[StrategyTemplate]] = {}

    @classmethod
    def register(cls, template_class: type[StrategyTemplate]):
        """Register a template class."""
        strategy_type = template_class.get_strategy_type()
        cls._templates[strategy_type] = template_class

    @classmethod
    def get_template(cls, strategy_type: StrategyType) -> StrategyTemplate:
        """
        Get template instance for given strategy type.

        Args:
            strategy_type: Type of strategy template

        Returns:
            StrategyTemplate instance

        Raises:
            ValueError: If strategy type not found
        """
        template_class = cls._templates.get(strategy_type)

        if template_class is None:
            available = ", ".join(t.value for t in cls._templates.keys())
            raise ValueError(
                f"Unknown strategy type: {strategy_type.value}. "
                f"Available: {available}"
            )

        return template_class()

    @classmethod
    def get_available_types(cls) -> list[StrategyType]:
        """Get list of available strategy types."""
        return list(cls._templates.keys())

    @classmethod
    def is_registered(cls, strategy_type: StrategyType) -> bool:
        """Check if a strategy type is registered."""
        return strategy_type in cls._templates
