"""
Control Panel Module

Main control panel for managing strategy parameters with interactive widgets.
"""

from typing import Dict, Any, Optional, Callable, List
import ipywidgets as widgets
from IPython.display import display

from .widgets import ControlWidgets
from .validator import ParameterValidator, ValidationResult
from .refresh import AutoRefreshManager, SimpleRefreshManager
from .presets import PresetManager
from .tabs import TabbedControls


class StrategyControlPanel:
    """Interactive control panel for strategy parameters"""

    def __init__(
        self,
        workspace: Optional['StrategyWorkspace'] = None,
        auto_refresh: bool = True,
        refresh_interval: float = 1.0
    ):
        """
        Initialize control panel

        Args:
            workspace: Optional StrategyWorkspace instance
            auto_refresh: Enable auto-refresh on parameter change
            refresh_interval: Refresh interval in seconds
        """
        self.workspace = workspace
        self.controls: Dict[str, widgets.Widget] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.groups: Dict[str, List[str]] = {}

        # Validation
        self.validator = ParameterValidator()

        # Refresh manager
        if auto_refresh:
            self.refresh_manager = AutoRefreshManager(
                refresh_callback=self._on_refresh,
                refresh_interval=refresh_interval
            )
        else:
            self.refresh_manager = SimpleRefreshManager(
                refresh_callback=self._on_refresh
            )

        # Preset manager
        self.preset_manager = PresetManager()

        # Tabbed interface
        self.tabs = TabbedControls()

        # Validation display
        self.validation_display = widgets.HTML(
            value='<span style="color: green;">✓ All parameters valid</span>',
            layout=widgets.Layout(width='100%')
        )

        # Build main layout
        self._build_main_layout()

    def _build_main_layout(self):
        """Build main control panel layout"""
        # Status section
        self.status_box = widgets.VBox([
            self.validation_display,
            self.refresh_manager.widget
        ])

        # Main panel
        self.panel = widgets.VBox([
            widgets.HTML('<h3>Strategy Control Panel</h3>'),
            self.status_box,
            widgets.HTML('<hr>'),
            self.tabs.widget
        ])

    def add_parameter_control(
        self,
        name: str,
        control_type: str,
        options: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None,
        group: str = "General"
    ):
        """
        Add a parameter control widget

        Args:
            name: Parameter name
            control_type: Type of control ('slider', 'dropdown', 'text', 'checkbox', etc.)
            options: Widget-specific options (min, max, choices, etc.)
            callback: Optional callback for value changes
            group: Group name for tab organization
        """
        options = options or {}

        # Create widget based on type
        if control_type == 'slider':
            widget = ControlWidgets.slider(
                name=name,
                min_value=options.get('min', 0),
                max_value=options.get('max', 100),
                initial_value=options.get('initial', options.get('min', 0)),
                step=options.get('step', 0.1),
                callback=self._create_change_callback(name, callback)
            )

        elif control_type == 'int_slider':
            widget = ControlWidgets.int_slider(
                name=name,
                min_value=options.get('min', 0),
                max_value=options.get('max', 100),
                initial_value=options.get('initial', options.get('min', 0)),
                step=options.get('step', 1),
                callback=self._create_change_callback(name, callback)
            )

        elif control_type == 'dropdown':
            widget = ControlWidgets.dropdown(
                name=name,
                options=options.get('choices', []),
                initial_value=options.get('initial', options.get('choices', [None])[0]),
                callback=self._create_change_callback(name, callback)
            )

        elif control_type == 'text':
            widget = ControlWidgets.text_input(
                name=name,
                initial_value=options.get('initial', ''),
                placeholder=options.get('placeholder', ''),
                callback=self._create_change_callback(name, callback)
            )

        elif control_type == 'checkbox':
            widget = ControlWidgets.checkbox(
                name=name,
                initial_value=options.get('initial', False),
                callback=self._create_change_callback(name, callback)
            )

        elif control_type == 'bounded_float':
            widget = ControlWidgets.bounded_float_text(
                name=name,
                min_value=options.get('min', 0),
                max_value=options.get('max', 100),
                initial_value=options.get('initial', 0),
                step=options.get('step', 0.1),
                callback=self._create_change_callback(name, callback)
            )

        else:
            raise ValueError(f"Unknown control type: {control_type}")

        # Store control
        self.controls[name] = widget

        # Add to group
        if group not in self.groups:
            self.groups[group] = []
        self.groups[group].append(name)

        # Add to tab (create if doesn't exist)
        if group not in self.tabs.tab_names:
            self.tabs.add_tab(group, [])

        self.tabs.add_control(group, widget)

        return widget

    def _create_change_callback(
        self,
        name: str,
        user_callback: Optional[Callable]
    ) -> Callable:
        """Create callback for parameter changes"""
        def callback(change):
            # Call user callback if provided
            if user_callback:
                user_callback(change)

            # Call any registered callbacks
            for cb in self.callbacks.get(name, []):
                cb(change)

            # Trigger refresh if enabled
            if isinstance(self.refresh_manager, SimpleRefreshManager):
                self.refresh_manager.refresh_button.click()
            else:
                self.refresh_manager.trigger_refresh()

            # Validate
            self._validate_parameters()

        return callback

    def _validate_parameters(self):
        """Validate all parameters"""
        params = self.get_parameters()
        result = self.validator.validate(params)

        self.validation_display.value = result.to_widget().value

        return result

    def _on_refresh(self):
        """Handle refresh event"""
        if self.workspace:
            # Update workspace with current parameters
            params = self.get_parameters()
            # This would trigger workspace update
            # workspace.update_parameters(params)

            # Invalidate caches and trigger recalculation
            pass

    def remove_parameter_control(self, name: str):
        """
        Remove a parameter control

        Args:
            name: Parameter name to remove
        """
        if name not in self.controls:
            raise ValueError(f"Control '{name}' not found")

        # Remove from all groups
        for group_name, controls in self.groups.items():
            if name in controls:
                controls.remove(name)
                self.tabs.remove_control(group_name, self.controls[name])

        # Delete control
        del self.controls[name]
        del self.callbacks[name]

        # Remove validation rules
        self.validator.clear_rules(name)

    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current parameter values

        Returns:
            Dictionary of parameter names to values
        """
        params = {}
        for name, widget in self.controls.items():
            params[name] = widget.value
        return params

    def set_parameters(self, params: Dict[str, Any]):
        """
        Set parameter values

        Args:
            params: Dictionary of parameter names to values
        """
        for name, value in params.items():
            if name in self.controls:
                self.controls[name].value = value

        self._validate_parameters()

    def get_parameter(self, name: str) -> Any:
        """
        Get single parameter value

        Args:
            name: Parameter name

        Returns:
            Parameter value
        """
        if name not in self.controls:
            raise ValueError(f"Parameter '{name}' not found")
        return self.controls[name].value

    def set_parameter(self, name: str, value: Any):
        """
        Set single parameter value

        Args:
            name: Parameter name
            value: New value
        """
        if name not in self.controls:
            raise ValueError(f"Parameter '{name}' not found")
        self.controls[name].value = value
        self._validate_parameters()

    def on_parameter_change(self, name: str, callback: Callable):
        """
        Register callback for parameter changes

        Args:
            name: Parameter name
            callback: Function to call on change
        """
        if name not in self.callbacks:
            self.callbacks[name] = []
        self.callbacks[name].append(callback)

    def add_validation_rule(
        self,
        parameter: str,
        validator: Callable[[Any], bool],
        error_message: str
    ):
        """
        Add validation rule for parameter

        Args:
            parameter: Parameter name
            validator: Validation function
            error_message: Error message if validation fails
        """
        self.validator.add_rule(parameter, validator, error_message)

    def enable_auto_refresh(self, interval: float = 1.0):
        """
        Enable automatic refresh on parameter change

        Args:
            interval: Refresh interval in seconds
        """
        if isinstance(self.refresh_manager, SimpleRefreshManager):
            # Switch to auto-refresh manager
            self.refresh_manager = AutoRefreshManager(
                refresh_callback=self._on_refresh,
                refresh_interval=interval
            )
        else:
            self.refresh_manager.set_interval(interval)
            self.refresh_manager.start()

        self._build_main_layout()

    def disable_auto_refresh(self):
        """Disable automatic refresh"""
        if isinstance(self.refresh_manager, AutoRefreshManager):
            self.refresh_manager.stop()

    def save_preset(
        self,
        name: str,
        description: str = "",
        tags: Optional[List[str]] = None
    ):
        """
        Save current parameters as preset

        Args:
            name: Preset name
            description: Optional description
            tags: Optional tags
        """
        params = self.get_parameters()
        self.preset_manager.save_preset(name, params, description, tags)

    def load_preset(self, name: str):
        """
        Load preset by name

        Args:
            name: Preset name
        """
        params = self.preset_manager.load_preset(name)
        self.set_parameters(params)

    def add_preset_tab(self):
        """Add preset management tab"""
        preset_widget = self.preset_manager.to_widget(
            on_load=lambda p: self.set_parameters(p),
            on_save=lambda: self.get_parameters()
        )
        self.tabs.add_tab("Presets", [preset_widget])

    def _build_layout(self) -> widgets.Box:
        """Build control panel layout"""
        return self.panel

    @property
    def widget(self) -> widgets.Box:
        """Return panel widget for display"""
        return self.panel

    def display(self):
        """Display the control panel"""
        display(self.panel)

    def __repr__(self) -> str:
        """String representation"""
        return f"StrategyControlPanel(parameters={len(self.controls)}, groups={len(self.groups)})"


class QuickControlPanel:
    """Simplified control panel for quick parameter setup"""

    def __init__(
        self,
        parameters: Dict[str, Dict[str, Any]],
        on_change: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Initialize quick control panel

        Args:
            parameters: Dictionary of parameter configs
                       {name: {'type': 'slider', 'min': 0, 'max': 100, 'initial': 50}}
            on_change: Callback when any parameter changes
        """
        self.parameters = parameters
        self.on_change = on_change
        self.controls: Dict[str, widgets.Widget] = {}

        self._build_controls()

    def _build_controls(self):
        """Build control widgets"""
        control_widgets = []

        for name, config in self.parameters.items():
            control_type = config.get('type', 'slider')

            if control_type == 'slider':
                widget = ControlWidgets.slider(
                    name=name,
                    min_value=config.get('min', 0),
                    max_value=config.get('max', 100),
                    initial_value=config.get('initial', 0),
                    step=config.get('step', 0.1),
                    description=config.get('description', name)
                )

            elif control_type == 'dropdown':
                widget = ControlWidgets.dropdown(
                    name=name,
                    options=config.get('choices', []),
                    initial_value=config.get('initial'),
                    description=config.get('description', name)
                )

            elif control_type == 'checkbox':
                widget = ControlWidgets.checkbox(
                    name=name,
                    initial_value=config.get('initial', False),
                    description=config.get('description', name)
                )

            else:
                # Default to text input
                widget = ControlWidgets.text_input(
                    name=name,
                    initial_value=config.get('initial', ''),
                    description=config.get('description', name)
                )

            self.controls[name] = widget
            control_widgets.append(widget)

        self.widget = widgets.VBox(control_widgets)

    def get_values(self) -> Dict[str, Any]:
        """Get all parameter values"""
        return {name: widget.value for name, widget in self.controls.items()}

    def set_values(self, values: Dict[str, Any]):
        """Set parameter values"""
        for name, value in values.items():
            if name in self.controls:
                self.controls[name].value = value

    def display(self):
        """Display the panel"""
        display(self.widget)

    def __repr__(self) -> str:
        """String representation"""
        return f"QuickControlPanel(parameters={len(self.parameters)})"
