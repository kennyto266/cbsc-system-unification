"""
Layout management module for multi-panel visualizations.

Provides LayoutManager for organizing multiple charts and widgets
in flexible grid layouts.
"""

from typing import Optional, List, Dict, Any, Union
import pandas as pd

try:
    import ipywidgets as widgets
    from IPython.display import display
    IPYWIDGETS_AVAILABLE = True
except ImportError:
    IPYWIDGETS_AVAILABLE = False


class LayoutManager:
    """
    Create and manage flexible layouts for visualizations.

    Supports grid layouts, tabbed interfaces, and accordion-style
    organization of charts and controls.
    """

    def __init__(self):
        """Initialize LayoutManager."""
        if not IPYWIDGETS_AVAILABLE:
            raise ImportError(
                "ipywidgets is required for LayoutManager. "
                "Install with: pip install ipywidgets"
            )

        self._panels: Dict[str, any] = {}
        self._layout: Optional[any] = None

    def add_panel(
        self,
        name: str,
        panel: any,
    ) -> None:
        """
        Add a panel to the layout manager.

        Args:
            name: Panel identifier
            panel: Widget to add
        """
        self._panels[name] = panel

    def create_grid_layout(
        self,
        items: List[any],
        grid_template: str = "repeat(2, 1fr)",
        gap: str = "10px",
    ) -> any:
        """
        Create a grid layout for widgets.

        Args:
            items: List of widgets to arrange
            grid_template: CSS grid template (e.g., "repeat(2, 1fr)")
            gap: Gap between grid items

        Returns:
            GridBox widget with arranged items
        """
        layout = widgets.Layout(
            display='grid',
            grid_template_columns=grid_template,
            grid_gap=gap,
        )

        grid = widgets.GridBox(children=items, layout=layout)
        self._layout = grid

        return grid

    def create_two_column_layout(
        self,
        left: any,
        right: any,
        width_ratio: str = "1fr 1fr",
        gap: str = "10px",
    ) -> any:
        """
        Create a two-column layout.

        Args:
            left: Left column widget
            right: Right column widget
            width_ratio: Width ratio (e.g., "1fr 2fr" for 1:2 ratio)
            gap: Gap between columns

        Returns:
            HBox with two columns
        """
        left_layout = widgets.Layout(flex=f"1 1 {width_ratio.split()[0]}")
        right_layout = widgets.Layout(flex=f"1 1 {width_ratio.split()[1]}")

        left_box = widgets.Box([left], layout=left_layout)
        right_box = widgets.Box([right], layout=right_layout)

        hbox = widgets.HBox([left_box, right_box], layout=widgets.Layout(gap=gap))
        self._layout = hbox

        return hbox

    def create_three_column_layout(
        self,
        left: any,
        center: any,
        right: any,
        width_ratio: str = "1fr 1fr 1fr",
        gap: str = "10px",
    ) -> any:
        """
        Create a three-column layout.

        Args:
            left: Left column widget
            center: Center column widget
            right: Right column widget
            width_ratio: Width ratio for columns
            gap: Gap between columns

        Returns:
            HBox with three columns
        """
        ratios = width_ratio.split()
        left_layout = widgets.Layout(flex=f"1 1 {ratios[0]}")
        center_layout = widgets.Layout(flex=f"1 1 {ratios[1]}")
        right_layout = widgets.Layout(flex=f"1 1 {ratios[2]}")

        left_box = widgets.Box([left], layout=left_layout)
        center_box = widgets.Box([center], layout=center_layout)
        right_box = widgets.Box([right], layout=right_layout)

        hbox = widgets.HBox(
            [left_box, center_box, right_box],
            layout=widgets.Layout(gap=gap)
        )
        self._layout = hbox

        return hbox

    def create_sidebar_layout(
        self,
        sidebar: any,
        main: any,
        sidebar_width: str = "250px",
        gap: str = "10px",
    ) -> any:
        """
        Create a sidebar + main content layout.

        Args:
            sidebar: Sidebar widget (typically controls)
            main: Main content widget (typically charts)
            sidebar_width: Fixed width for sidebar
            gap: Gap between sidebar and main

        Returns:
            HBox with sidebar and main content
        """
        sidebar_layout = widgets.Layout(width=sidebar_width)
        main_layout = widgets.Layout(flex="1 1 auto")

        sidebar_box = widgets.Box([sidebar], layout=sidebar_layout)
        main_box = widgets.Box([main], layout=main_layout)

        hbox = widgets.HBox([sidebar_box, main_box], layout=widgets.Layout(gap=gap))
        self._layout = hbox

        return hbox

    def create_tabs(
        self,
        tabs: Dict[str, any],
    ) -> any:
        """
        Create a tabbed interface.

        Args:
            tabs: Dictionary mapping tab names to widgets

        Returns:
            Tab widget with multiple tabs
        """
        tab = widgets.Tab()
        tab.children = list(tabs.values())

        for i, title in enumerate(tabs.keys()):
            tab.set_title(i, title)

        self._layout = tab
        return tab

    def create_accordion(
        self,
        sections: Dict[str, any],
        opened_index: int = 0,
    ) -> any:
        """
        Create an accordion-style collapsible layout.

        Args:
            sections: Dictionary mapping section titles to widgets
            opened_index: Index of initially opened section

        Returns:
            Accordion widget with collapsible sections
        """
        accordion = widgets.Accordion()
        accordion.children = list(sections.values())

        for i, title in enumerate(sections.keys()):
            accordion.set_title(i, title)

        accordion.selected_index = opened_index
        self._layout = accordion

        return accordion

    def create_dashboard_layout(
        self,
        header: Optional[any] = None,
        sidebar: Optional[any] = None,
        main: Optional[any] = None,
        footer: Optional[any] = None,
        sidebar_width: str = "250px",
        header_height: str = "60px",
        footer_height: str = "40px",
    ) -> any:
        """
        Create a complete dashboard layout.

        Args:
            header: Optional header widget
            sidebar: Optional sidebar widget
            main: Main content widget
            footer: Optional footer widget
            sidebar_width: Width of sidebar
            header_height: Height of header
            footer_height: Height of footer

        Returns:
            VBox with complete dashboard layout
        """
        children = []

        # Header
        if header:
            header_layout = widgets.Layout(height=header_height)
            header_box = widgets.Box([header], layout=header_layout)
            children.append(header_box)

        # Main content area (sidebar + main)
        if sidebar or main:
            if sidebar and main:
                content = self.create_sidebar_layout(
                    sidebar=sidebar,
                    main=main,
                    sidebar_width=sidebar_width,
                )
            elif main:
                content = main
            else:
                content = sidebar

            content_layout = widgets.Layout(flex="1 1 auto")
            content_box = widgets.Box([content], layout=content_layout)
            children.append(content_box)

        # Footer
        if footer:
            footer_layout = widgets.Layout(height=footer_height)
            footer_box = widgets.Box([footer], layout=footer_layout)
            children.append(footer_box)

        # Create main container
        main_layout = widgets.Layout(
            height='100vh',
            display='flex',
            flex_flow='column',
        )

        vbox = widgets.VBox(children, layout=main_layout)
        self._layout = vbox

        return vbox

    def create_split_pane(
        self,
        top: any,
        bottom: any,
        height_ratio: str = "1fr 1fr",
        gap: str = "10px",
        orientation: str = "vertical",
    ) -> any:
        """
        Create a split pane layout.

        Args:
            top: Top (or left) widget
            bottom: Bottom (or right) widget
            height_ratio: Height ratio for vertical split
            gap: Gap between panes
            orientation: 'vertical' or 'horizontal'

        Returns:
            VBox (vertical) or HBox (horizontal)
        """
        ratios = height_ratio.split()
        top_layout = widgets.Layout(flex=f"1 1 {ratios[0]}")
        bottom_layout = widgets.Layout(flex=f"1 1 {ratios[1]}")

        top_box = widgets.Box([top], layout=top_layout)
        bottom_box = widgets.Box([bottom], layout=bottom_layout)

        if orientation == "horizontal":
            box = widgets.HBox([top_box, bottom_box], layout=widgets.Layout(gap=gap))
        else:
            box = widgets.VBox([top_box, bottom_box], layout=widgets.Layout(gap=gap))

        self._layout = box
        return box

    def display(self) -> None:
        """Display the current layout."""
        if self._layout is None:
            raise ValueError("No layout to display. Create a layout first.")
        display(self._layout)

    def get_layout(self) -> Optional[any]:
        """Get the current layout widget."""
        return self._layout

    def add_styling(
        self,
        style: Dict[str, str],
    ) -> None:
        """
        Add custom styling to the current layout.

        Args:
            style: Dictionary of CSS style properties
        """
        if self._layout is not None and hasattr(self._layout, 'layout'):
            current_layout = self._layout.layout
            for prop, value in style.items():
                setattr(current_layout, prop, value)


def create_chart_layout(
    chart_widget: any,
    controls: Optional[any] = None,
    position: str = "right",
) -> any:
    """
    Create a standard chart layout with optional controls.

    Args:
        chart_widget: The chart to display
        controls: Optional control panel
        position: Control position ('left', 'right', 'top', 'bottom')

    Returns:
        Box widget with chart and controls
    """
    if controls is None:
        return widgets.Box([chart_widget])

    chart_layout = widgets.Layout(flex="1 1 auto")
    chart_box = widgets.Box([chart_widget], layout=chart_layout)

    control_layout = widgets.Layout(width="300px")
    control_box = widgets.Box([controls], layout=control_layout)

    if position in ['left', 'right']:
        if position == 'left':
            box = widgets.HBox([control_box, chart_box])
        else:
            box = widgets.HBox([chart_box, control_box])
    else:
        control_layout = widgets.Layout(height="200px")
        control_box = widgets.Box([controls], layout=control_layout)

        if position == 'top':
            box = widgets.VBox([control_box, chart_box])
        else:
            box = widgets.VBox([chart_box, control_box])

    return box
