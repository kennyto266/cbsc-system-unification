"""
Interactive widgets module using ipywidgets.

Provides ControlPanel class for creating interactive controls
for charts and data visualization in Jupyter notebooks.
"""

from typing import Optional, List, Dict, Any, Callable
import pandas as pd

try:
    import ipywidgets as widgets
    from IPython.display import display
    IPYWIDGETS_AVAILABLE = True
except ImportError:
    IPYWIDGETS_AVAILABLE = False

from .themes import list_themes, get_theme


class ControlPanel:
    """
    Create interactive control panels for Jupyter notebooks.

    Provides widgets for theme selection, data filtering,
    parameter adjustment, and real-time chart updates.
    """

    def __init__(self, update_callback: Optional[Callable] = None):
        """
        Initialize ControlPanel.

        Args:
            update_callback: Function to call when any control changes
        """
        if not IPYWIDGETS_AVAILABLE:
            raise ImportError(
                "ipywidgets is required for ControlPanel. "
                "Install with: pip install ipywidgets"
            )

        self.update_callback = update_callback
        self.widgets: Dict[str, any] = {}
        self.output = widgets.Output()
        self._panel: Optional[widgets.Box] = None

    def create_theme_selector(self, default: str = "dark") -> any:
        """
        Create a theme selection dropdown.

        Args:
            default: Default theme name

        Returns:
            Dropdown widget with theme options
        """
        theme_selector = widgets.Dropdown(
            options=list_themes(),
            value=default,
            description='Theme:',
            style={'description_width': 'initial'},
        )

        def on_change(change):
            if self.update_callback:
                with self.output:
                    self.update_callback(theme=change['new'])

        theme_selector.observe(on_change, names='value')
        self.widgets['theme'] = theme_selector

        return theme_selector

    def create_date_range_selector(
        self,
        min_date: pd.Timestamp,
        max_date: pd.Timestamp,
        default_start: Optional[pd.Timestamp] = None,
        default_end: Optional[pd.Timestamp] = None,
    ) -> any:
        """
        Create date range selection widgets.

        Args:
            min_date: Minimum selectable date
            max_date: Maximum selectable date
            default_start: Default start date
            default_end: Default end date

        Returns:
            VBox containing date range widgets
        """
        if default_start is None:
            default_start = min_date
        if default_end is None:
            default_end = max_date

        start_date = widgets.DatePicker(
            value=default_start,
            description='Start Date:',
            style={'description_width': 'initial'},
            min=min_date.date() if hasattr(min_date, 'date') else min_date,
            max=max_date.date() if hasattr(max_date, 'date') else max_date,
        )

        end_date = widgets.DatePicker(
            value=default_end,
            description='End Date:',
            style={'description_width': 'initial'},
            min=min_date.date() if hasattr(min_date, 'date') else min_date,
            max=max_date.date() if hasattr(max_date, 'date') else max_date,
        )

        def on_change(change):
            if self.update_callback:
                with self.output:
                    self.update_callback(
                        start_date=start_date.value,
                        end_date=end_date.value,
                    )

        start_date.observe(on_change, names='value')
        end_date.observe(on_change, names='value')

        self.widgets['start_date'] = start_date
        self.widgets['end_date'] = end_date

        return widgets.VBox([start_date, end_date])

    def create_slider(
        self,
        name: str,
        min_value: float,
        max_value: float,
        default: float,
        step: float = 1.0,
        description: Optional[str] = None,
    ) -> any:
        """
        Create a numeric slider control.

        Args:
            name: Widget identifier name
            min_value: Minimum value
            max_value: Maximum value
            default: Default value
            step: Step size
            description: Widget description label

        Returns:
            FloatSlider widget
        """
        if description is None:
            description = name.replace('_', ' ').title()

        slider = widgets.FloatSlider(
            value=default,
            min=min_value,
            max=max_value,
            step=step,
            description=description + ':',
            style={'description_width': 'initial'},
            continuous_update=False,
        )

        def on_change(change):
            if self.update_callback:
                with self.output:
                    kwargs = {name: change['new']}
                    self.update_callback(**kwargs)

        slider.observe(on_change, names='value')
        self.widgets[name] = slider

        return slider

    def create_checkbox(
        self,
        name: str,
        default: bool = False,
        description: Optional[str] = None,
    ) -> any:
        """
        Create a checkbox control.

        Args:
            name: Widget identifier name
            default: Default checked state
            description: Widget description label

        Returns:
            Checkbox widget
        """
        if description is None:
            description = name.replace('_', ' ').title()

        checkbox = widgets.Checkbox(
            value=default,
            description=description,
            style={'description_width': 'initial'},
        )

        def on_change(change):
            if self.update_callback:
                with self.output:
                    kwargs = {name: change['new']}
                    self.update_callback(**kwargs)

        checkbox.observe(on_change, names='value')
        self.widgets[name] = checkbox

        return checkbox

    def create_multi_select(
        self,
        name: str,
        options: List[str],
        default: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> any:
        """
        Create a multi-select dropdown.

        Args:
            name: Widget identifier name
            options: List of selectable options
            default: Default selected values
            description: Widget description label

        Returns:
            SelectMultiple widget
        """
        if description is None:
            description = name.replace('_', ' ').title()

        if default is None:
            default = []

        multi_select = widgets.SelectMultiple(
            options=options,
            value=default,
            description=description + ':',
            style={'description_width': 'initial'},
        )

        def on_change(change):
            if self.update_callback:
                with self.output:
                    kwargs = {name: list(change['new'])}
                    self.update_callback(**kwargs)

        multi_select.observe(on_change, names='value')
        self.widgets[name] = multi_select

        return multi_select

    def create_button(
        self,
        text: str,
        callback: Optional[Callable] = None,
        button_style: str = '',
    ) -> any:
        """
        Create an action button.

        Args:
            text: Button text
            callback: Function to call on click
            button_style: Button style ('primary', 'success', 'info', 'warning', 'danger')

        Returns:
            Button widget
        """
        button = widgets.Button(
            description=text,
            button_style=button_style,
        )

        def on_click(b):
            if callback:
                with self.output:
                    callback()

        button.on_click(on_click)
        self.widgets[text.lower().replace(' ', '_')] = button

        return button

    def create_text_input(
        self,
        name: str,
        default: str = '',
        description: Optional[str] = None,
        placeholder: str = '',
    ) -> any:
        """
        Create a text input field.

        Args:
            name: Widget identifier name
            default: Default text value
            description: Widget description label
            placeholder: Placeholder text

        Returns:
            Text widget
        """
        if description is None:
            description = name.replace('_', ' ').title()

        text = widgets.Text(
            value=default,
            placeholder=placeholder,
            description=description + ':',
            style={'description_width': 'initial'},
        )

        def on_change(change):
            if self.update_callback:
                with self.output:
                    kwargs = {name: change['new']}
                    self.update_callback(**kwargs)

        text.observe(on_change, names='value')
        self.widgets[name] = text

        return text

    def create_controls(
        self,
        controls: Optional[Dict[str, Any]] = None,
    ) -> any:
        """
        Create a complete control panel with multiple widgets.

        Args:
            controls: Dictionary of control configurations

        Returns:
            Box widget containing all controls

        Example controls dict:
            {
                'theme': 'dropdown',
                'show_volume': 'checkbox',
                'ma_period': 'slider',
                'strategies': 'multi_select',
            }
        """
        if controls is None:
            controls = {
                'theme': 'dropdown',
            }

        widget_list = []

        for name, control_type in controls.items():
            if control_type == 'dropdown' and name == 'theme':
                widget_list.append(self.create_theme_selector())
            elif control_type == 'checkbox':
                widget_list.append(self.create_checkbox(name))
            elif control_type == 'slider':
                widget_list.append(self.create_slider(
                    name=name,
                    min_value=1,
                    max_value=100,
                    default=20,
                ))
            elif control_type == 'text':
                widget_list.append(self.create_text_input(name))
            elif control_type == 'multi_select':
                widget_list.append(self.create_multi_select(
                    name=name,
                    options=['Option 1', 'Option 2', 'Option 3'],
                ))

        # Add output area for updates
        widget_list.append(self.output)

        self._panel = widgets.VBox(widget_list)
        return self._panel

    def display(self) -> None:
        """Display the control panel in the notebook."""
        if self._panel is None:
            self.create_controls()
        display(self._panel)

    def get_values(self) -> Dict[str, Any]:
        """
        Get current values of all widgets.

        Returns:
            Dictionary mapping widget names to their values
        """
        values = {}
        for name, widget in self.widgets.items():
            if isinstance(widget, widgets.Dropdown):
                values[name] = widget.value
            elif isinstance(widget, widgets.Checkbox):
                values[name] = widget.value
            elif isinstance(widget, widgets.FloatSlider):
                values[name] = widget.value
            elif isinstance(widget, widgets.Text):
                values[name] = widget.value
            elif isinstance(widget, widgets.SelectMultiple):
                values[name] = list(widget.value)
            elif isinstance(widget, widgets.DatePicker):
                values[name] = widget.value
        return values

    def set_values(self, values: Dict[str, Any]) -> None:
        """
        Set values for multiple widgets.

        Args:
            values: Dictionary mapping widget names to values
        """
        for name, value in values.items():
            if name in self.widgets:
                widget = self.widgets[name]
                if hasattr(widget, 'value'):
                    widget.value = value

    def clear_output(self) -> None:
        """Clear the output area."""
        self.output.clear_output()

    def disable(self) -> None:
        """Disable all widgets."""
        for widget in self.widgets.values():
            widget.disabled = True

    def enable(self) -> None:
        """Enable all widgets."""
        for widget in self.widgets.values():
            widget.disabled = False


def create_strategy_controls(
    update_callback: Callable,
    theme: str = "dark",
) -> any:
    """
    Create standard controls for strategy visualization.

    Args:
        update_callback: Function to call on control changes
        theme: Default theme

    Returns:
        VBox with standard strategy controls
    """
    panel = ControlPanel(update_callback)

    theme_selector = panel.create_theme_selector(theme)
    show_volume = panel.create_checkbox('show_volume', default=True)
    show_ma = panel.create_checkbox('show_ma', default=False)
    ma_period = panel.create_slider(
        name='ma_period',
        min_value=5,
        max_value=50,
        default=20,
        description='MA Period'
    )
    show_bb = panel.create_checkbox('show_bb', default=False)
    bb_period = panel.create_slider(
        name='bb_period',
        min_value=5,
        max_value=50,
        default=20,
        description='BB Period'
    )
    bb_std = panel.create_slider(
        name='bb_std',
        min_value=0.5,
        max_value=4.0,
        default=2.0,
        step=0.1,
        description='BB Std Dev'
    )

    controls = widgets.VBox([
        widgets.HTML('<h3>Chart Controls</h3>'),
        theme_selector,
        show_volume,
        show_ma,
        ma_period,
        show_bb,
        bb_period,
        bb_std,
        panel.output,
    ])

    return controls
