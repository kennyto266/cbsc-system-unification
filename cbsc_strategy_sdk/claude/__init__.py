"""
CBSC Strategy SDK - Claude AI Integration Module

This module provides integration with Anthropic's Claude API for
intelligent trading strategy code generation, optimization, and error analysis.

Classes:
    ClaudeCodeAssistant: Main assistant class for code generation
    ClaudeClient: Async Anthropic API client wrapper
    StrategyTemplate: Base class for strategy templates
    PromptBuilder: Construct prompts for Claude API
    CodeValidator: Validate generated code

Example:
    >>> from cbsc_strategy_sdk.claude import ClaudeCodeAssistant
    >>> assistant = ClaudeCodeAssistant(api_key="your-key")
    >>> code = assistant.generate_strategy(
    ...     "Moving average crossover strategy",
    ...     StrategyType.MOMENTUM
    ... )
"""

from .assistant import ClaudeCodeAssistant
from .client import ClaudeClient
from .templates import (
    StrategyTemplate,
    StrategyType,
    MomentumTemplate,
    MeanReversionTemplate,
    ArbitrageTemplate,
    PairTradingTemplate,
    MLStrategyTemplate,
)
from .prompt_builder import PromptBuilder
from .validators import CodeValidator

__all__ = [
    # Main classes
    "ClaudeCodeAssistant",
    "ClaudeClient",
    "PromptBuilder",
    "CodeValidator",
    # Templates
    "StrategyTemplate",
    "StrategyType",
    "MomentumTemplate",
    "MeanReversionTemplate",
    "ArbitrageTemplate",
    "PairTradingTemplate",
    "MLStrategyTemplate",
]

__version__ = "0.1.0"
