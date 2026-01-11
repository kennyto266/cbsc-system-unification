"""Strategy Control Panel for CBSC Strategy SDK.

Main control panel for managing strategy parameters in Jupyter notebooks.
"""

from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class StrategyControlPanel:
    """Main control panel for strategy parameter management.

    Provides a unified interface for managing strategy parameters,
    running backtests, and visualizing results.

    Example:
        >>> panel = StrategyControlPanel()
        >>> panel.add_parameter('rsi_period', 14, min_value=2, max_value=50)
        >>> panel.add_parameter('volume_threshold', 1000000)
        >>> panel.display()
    """

    def __init__(self) -> None:
        """Initialize the control panel."""
        self._parameters: dict[str, Any] = {}
        self._widgets: dict[str, Any] = {}

    def add_parameter(
        self,
        name: str,
        default_value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        description: Optional[str] = None,
    ) -> None:
        """Add a parameter to the control panel.

        Args:
            name: Parameter name
            default_value: Default value
            min_value: Minimum value (for numeric parameters)
            max_value: Maximum value (for numeric parameters)
            description: Parameter description
        """
        self._parameters[name] = {
            'default': default_value,
            'min': min_value,
            'max': max_value,
            'description': description,
            'value': default_value,
        }

    def get_parameters(self) -> dict[str, Any]:
        """Get current parameter values.

        Returns:
            Dictionary of parameter names to values
        """
        return {
            name: params['value']
            for name, params in self._parameters.items()
        }

    def set_parameter(self, name: str, value: Any) -> None:
        """Set a parameter value.

        Args:
            name: Parameter name
            value: New value
        """
        if name in self._parameters:
            self._parameters[name]['value'] = value
        else:
            raise ValueError(f"Unknown parameter: {name}")

    def reset_parameters(self) -> None:
        """Reset all parameters to default values."""
        for name, params in self._parameters.items():
            params['value'] = params['default']

    def display(self) -> None:
        """Display the control panel.

        In Jupyter: renders interactive widgets
        In script: prints current configuration
        """
        print("Strategy Control Panel")
        print("=" * 50)
        for name, params in self._parameters.items():
            value = params['value']
            desc = params.get('description', '')
            print(f"{name}: {value}")
            if desc:
                print(f"  ({desc})")

    def __repr__(self) -> str:
        """String representation of control panel."""
        return f"StrategyControlPanel(parameters={len(self._parameters)})"


# Legacy aliases for backward compatibility
ControlWidgets = StrategyControlPanel
