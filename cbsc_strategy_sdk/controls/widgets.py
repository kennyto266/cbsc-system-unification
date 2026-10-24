"""
Control Widgets Module

Provides a collection of specialized ipywidgets for strategy parameter control.
All widgets include proper styling, value display, and event handling.
"""

from typing import Any, List, Optional, Callable
import ipywidgets as widgets
from datetime import datetime


class ControlWidgets:
    """Collection of specialized control widgets for strategy parameters"""

    @staticmethod
    def slider(
        name: str,
        min_value: float,
        max_value: float,
        initial_value: float,
        step: float = 0.1,
        description: str = "",
        callback: Optional[Callable] = None
    ) -> widgets.FloatSlider:
        """
        Create parameter slider with value display

        Args:
            name: Widget name for identification
            min_value: Minimum slider value
            max_value: Maximum slider value
            initial_value: Starting value
            step: Step increment
            description: Widget label
            callback: Optional change callback

        Returns:
            Configured FloatSlider widget
        """
        slider_widget = widgets.FloatSlider(
            value=initial_value,
            min=min_value,
            max=max_value,
            step=step,
            description=description or name,
            continuous_update=False,
            readout=True,
            readout_format='.2f',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        if callback:
            slider_widget.observe(callback, names='value')

        slider_widget._control_name = name
        return slider_widget

    @staticmethod
    def int_slider(
        name: str,
        min_value: int,
        max_value: int,
        initial_value: int,
        step: int = 1,
        description: str = "",
        callback: Optional[Callable] = None
    ) -> widgets.IntSlider:
        """
        Create integer slider widget

        Args:
            name: Widget name
            min_value: Minimum value
            max_value: Maximum value
            initial_value: Starting value
            step: Step increment
            description: Widget label
            callback: Optional callback

        Returns:
            Configured IntSlider widget
        """
        int_slider = widgets.IntSlider(
            value=initial_value,
            min=min_value,
            max=max_value,
            step=step,
            description=description or name,
            continuous_update=False,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        if callback:
            int_slider.observe(callback, names='value')

        int_slider._control_name = name
        return int_slider

    @staticmethod
    def dropdown(
        name: str,
        options: List[Any],
        initial_value: Any,
        description: str = "",
        callback: Optional[Callable] = None
    ) -> widgets.Dropdown:
        """
        Create dropdown selector

        Args:
            name: Widget name
            options: List of options
            initial_value: Selected value
            description: Widget label
            callback: Optional callback

        Returns:
            Configured Dropdown widget
        """
        dropdown = widgets.Dropdown(
            options=options,
            value=initial_value,
            description=description or name,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        if callback:
            dropdown.observe(callback, names='value')

        dropdown._control_name = name
        return dropdown

    @staticmethod
    def text_input(
        name: str,
        initial_value: str = "",
        placeholder: str = "",
        description: str = "",
        callback: Optional[Callable] = None
    ) -> widgets.Text:
        """
        Create text input field

        Args:
            name: Widget name
            initial_value: Starting text
            placeholder: Placeholder text
            description: Widget label
            callback: Optional callback

        Returns:
            Configured Text widget
        """
        text = widgets.Text(
            value=initial_value,
            placeholder=placeholder,
            description=description or name,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        if callback:
            text.observe(callback, names='value')

        text._control_name = name
        return text

    @staticmethod
    def textarea(
        name: str,
        initial_value: str = "",
        placeholder: str = "",
        description: str = "",
        rows: int = 3,
        callback: Optional[Callable] = None
    ) -> widgets.Textarea:
        """
        Create textarea for multi-line input

        Args:
            name: Widget name
            initial_value: Starting text
            placeholder: Placeholder text
            description: Widget label
            rows: Number of rows
            callback: Optional callback

        Returns:
            Configured Textarea widget
        """
        textarea = widgets.Textarea(
            value=initial_value,
            placeholder=placeholder,
            description=description or name,
            rows=rows,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        if callback:
            textarea.observe(callback, names='value')

        textarea._control_name = name
        return textarea

    @staticmethod
    def checkbox(
        name: str,
        initial_value: bool = False,
        description: str = "",
        callback: Optional[Callable] = None
    ) -> widgets.Checkbox:
        """
        Create checkbox control

        Args:
            name: Widget name
            initial_value: Starting state
            description: Widget label
            callback: Optional callback

        Returns:
            Configured Checkbox widget
        """
        checkbox = widgets.Checkbox(
            value=initial_value,
            description=description or name,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='auto')
        )

        if callback:
            checkbox.observe(callback, names='value')

        checkbox._control_name = name
        return checkbox

    @staticmethod
    def toggle_buttons(
        name: str,
        options: List[Any],
        description: str = "",
        button_style: str = '',
        callback: Optional[Callable] = None
    ) -> widgets.ToggleButtons:
        """
        Create toggle buttons for mutually exclusive selection

        Args:
            name: Widget name
            options: List of options
            description: Widget label
            button_style: Style ('primary', 'success', 'info', 'warning', 'danger')
            callback: Optional callback

        Returns:
            Configured ToggleButtons widget
        """
        toggle = widgets.ToggleButtons(
            options=options,
            description=description or name,
            button_style=button_style,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='auto')
        )

        if callback:
            toggle.observe(callback, names='value')

        toggle._control_name = name
        return toggle

    @staticmethod
    def selection_slider(
        name: str,
        options: List[Any],
        initial_value: Any,
        description: str = "",
        callback: Optional[Callable] = None
    ) -> widgets.SelectionSlider:
        """
        Create selection slider for discrete options

        Args:
            name: Widget name
            options: List of options
            initial_value: Selected value
            description: Widget label
            callback: Optional callback

        Returns:
            Configured SelectionSlider widget
        """
        slider = widgets.SelectionSlider(
            options=options,
            value=initial_value,
            description=description or name,
            continuous_update=False,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        if callback:
            slider.observe(callback, names='value')

        slider._control_name = name
        return slider

    @staticmethod
    def bounded_float_text(
        name: str,
        min_value: float,
        max_value: float,
        initial_value: float,
        step: float = 0.1,
        description: str = "",
        callback: Optional[Callable] = None
    ) -> widgets.BoundedFloatText:
        """
        Create bounded float text input

        Args:
            name: Widget name
            min_value: Minimum value
            max_value: Maximum value
            initial_value: Starting value
            step: Step increment
            description: Widget label
            callback: Optional callback

        Returns:
            Configured BoundedFloatText widget
        """
        text = widgets.BoundedFloatText(
            value=initial_value,
            min=min_value,
            max=max_value,
            step=step,
            description=description or name,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        if callback:
            text.observe(callback, names='value')

        text._control_name = name
        return text

    @staticmethod
    def button(
        name: str,
        description: str = "",
        button_style: str = '',
        icon: str = '',
        callback: Optional[Callable] = None
    ) -> widgets.Button:
        """
        Create button widget

        Args:
            name: Widget name
            description: Button text
            button_style: Style ('primary', 'success', 'info', 'warning', 'danger')
            icon: Icon name (FontAwesome)
            callback: Click callback

        Returns:
            Configured Button widget
        """
        button = widgets.Button(
            description=description or name,
            button_style=button_style,
            icon=icon,
            layout=widgets.Layout(width='auto')
        )

        if callback:
            button.on_click(callback)

        button._control_name = name
        return button

    @staticmethod
    def label(
        text: str,
        style: str = ''
    ) -> widgets.HTML:
        """
        Create styled label/widget for display

        Args:
            text: Label text
            style: CSS style string

        Returns:
            HTML widget with styled text
        """
        style_attr = f' style="{style}"' if style else ''
        html = widgets.HTML(
            value=f'<span{style_attr}>{text}</span>',
            layout=widgets.Layout(width='auto')
        )
        return html

    @staticmethod
    def box(
        children: List[widgets.Widget],
        layout: Optional[widgets.Layout] = None
    ) -> widgets.Box:
        """
        Create container box for widgets

        Args:
            children: List of child widgets
            layout: Optional layout specification

        Returns:
            Box widget
        """
        return widgets.Box(
            children=children,
            layout=layout or widgets.Layout()
        )

    @staticmethod
    def vbox(
        children: List[widgets.Widget],
        layout: Optional[widgets.Layout] = None
    ) -> widgets.VBox:
        """
        Create vertical box layout

        Args:
            children: List of child widgets
            layout: Optional layout specification

        Returns:
            VBox widget
        """
        return widgets.VBox(
            children=children,
            layout=layout or widgets.Layout()
        )

    @staticmethod
    def hbox(
        children: List[widgets.Widget],
        layout: Optional[widgets.Layout] = None
    ) -> widgets.HBox:
        """
        Create horizontal box layout

        Args:
            children: List of child widgets
            layout: Optional layout specification

        Returns:
            HBox widget
        """
        return widgets.HBox(
            children=children,
            layout=layout or widgets.Layout()
        )
