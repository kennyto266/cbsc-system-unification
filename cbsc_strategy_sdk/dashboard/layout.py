"""
Dashboard layout components for Dash applications.

Provides DashboardLayout class for creating reusable UI components
including headers, metric cards, chart panels, and control panels.
"""

from typing import Optional, List, Dict, Any, Union
import pandas as pd

try:
    import dash
    from dash import html, dcc, dash_table
    import dash_bootstrap_components as dbc
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

from .theme import ThemeManager


class DashboardLayout:
    """
    Layout builder for dashboard components.

    Creates reusable UI components for Dash applications including
    headers, metric cards, chart panels, control panels, and data tables.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        """
        Initialize DashboardLayout.

        Args:
            theme_manager: Optional ThemeManager for consistent styling
        """
        if not DASH_AVAILABLE:
            raise ImportError(
                "Dash and dash-bootstrap-components are required. "
                "Install with: pip install dash dash-bootstrap-components"
            )

        self.theme = theme_manager or ThemeManager()

    def header(
        self,
        title: str,
        subtitle: str = "",
        show_theme_toggle: bool = True,
    ) -> html.Div:
        """
        Create dashboard header.

        Args:
            title: Main title text
            subtitle: Optional subtitle text
            show_theme_toggle: Whether to show theme toggle button

        Returns:
            Dash html.Div component
        """
        colors = self.theme.get_colors()

        header_content = [
            html.H1(
                title,
                className="display-6 fw-bold",
                style={'color': colors['text'], 'marginBottom': '0px'}
            ),
        ]

        if subtitle:
            header_content.append(
                html.P(
                    subtitle,
                    className="lead",
                    style={'color': colors['text_secondary'], 'marginTop': '5px'}
                )
            )

        if show_theme_toggle:
            header_content.append(
                html.Div(
                    [
                        dbc.Button(
                            "🌙 Light" if self.theme.is_dark else "☀️ Dark",
                            id="theme-toggle-btn",
                    color="outline-secondary",
                            size="sm",
                            className="ms-2",
                        )
                    ],
                    className="d-flex justify-content-end",
                )
            )

        return html.Div(
            header_content,
            className="mb-4",
            style={'borderBottom': f'1px solid {colors["border"]}', 'paddingBottom': '15px'}
        )

    def metric_card(
        self,
        title: str,
        value: Union[str, int, float],
        delta: Optional[float] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
    ) -> dbc.Card:
        """
        Create metric display card.

        Args:
            title: Metric title
            value: Metric value to display
            delta: Optional change value (shows as +/- indicator)
            icon: Optional icon name (using Bootstrap icons)
            color: Optional color override

        Returns:
            Dash Bootstrap Card component
        """
        colors = self.theme.get_colors()

        # Determine color based on delta
        if color is None and delta is not None:
            color = colors['success'] if delta >= 0 else colors['danger']
        elif color is None:
            color = colors['primary']

        # Build card body
        card_content = [
            html.H6(
                title,
                className="text-muted mb-2",
                style={'fontSize': '0.875rem', 'color': colors['text_secondary']}
            ),
        ]

        # Value with optional icon
        if icon:
            card_content.append(
                html.Div(
                    [
                        html.I(className=f"bi bi-{icon} me-2"),
                        html.H3(
                            str(value),
                            className="mb-0 d-inline-block",
                            style={
                                'color': colors['text'],
                                'fontSize': '1.75rem',
                                'fontWeight': 'bold'
                            }
                        ),
                    ],
                    className="d-flex align-items-center"
                )
            )
        else:
            card_content.append(
                html.H3(
                    str(value),
                    style={
                        'color': colors['text'],
                        'fontSize': '1.75rem',
                        'fontWeight': 'bold'
                    }
                )
            )

        # Delta indicator
        if delta is not None:
            delta_color = colors['success'] if delta >= 0 else colors['danger']
            delta_icon = "↑" if delta >= 0 else "↓"
            card_content.append(
                html.Small(
                    f"{delta_icon} {abs(delta):.2f}%",
                    className="text-muted",
                    style={'color': delta_color}
                )
            )

        card_body = dbc.CardBody(card_content)

        return dbc.Card(
            card_body,
            style=self.theme.get_card_style(),
        )

    def chart_panel(
        self,
        title: str,
        figure_id: str,
        controls: Optional[List[Any]] = None,
        height: str = "500px",
    ) -> html.Div:
        """
        Create chart panel with optional controls.

        Args:
            title: Panel title
            figure_id: ID for the dcc.Graph component
            controls: Optional list of control components
            height: Panel height

        Returns:
            Dash html.Div component
        """
        colors = self.theme.get_colors()

        # Header with title
        header = html.H5(
            title,
            className="card-title mb-3",
            style={'color': colors['text']}
        )

        # Chart component
        chart = dcc.Graph(
            id=figure_id,
            style={'height': height}
        )

        # Build panel content
        panel_content = [header]

        if controls:
            panel_content.append(
                html.Div(
                    controls,
                    className="mb-3 d-flex gap-2"
                )
            )

        panel_content.append(chart)

        return html.Div(
            panel_content,
            className="card-body",
            style=self.theme.get_card_style(),
        )

    def control_panel(
        self,
        controls: List[Any],
        title: str = "Controls",
        width: int = 3,
    ) -> html.Div:
        """
        Create controls sidebar.

        Args:
            controls: List of control components
            title: Panel title
            width: Column width (1-12)

        Returns:
            Dash html.Div component
        """
        colors = self.theme.get_colors()

        return html.Div(
            [
                html.H5(
                    title,
                    className="mb-3",
                    style={'color': colors['text']}
                ),
                html.Div(controls, className="d-grid gap-3"),
            ],
            className=f"col-md-{width}",
            style={
                'padding': '20px',
                'backgroundColor': colors['surface'],
                'borderRadius': '8px',
                'height': '100%',
            }
        )

    def data_table(
        self,
        df: pd.DataFrame,
        table_id: str,
        page_size: int = 20,
        sortable: bool = True,
        filterable: bool = True,
    ) -> dash_table.DataTable:
        """
        Create interactive data table.

        Args:
            df: DataFrame to display
            table_id: Component ID
            page_size: Number of rows per page
            sortable: Enable sorting
            filterable: Enable filtering

        Returns:
            Dash DataTable component
        """
        colors = self.theme.get_colors()

        return dash_table.DataTable(
            id=table_id,
            columns=[{"name": str(col), "id": str(col)} for col in df.columns],
            data=df.to_dict('records'),
            page_size=page_size,
            sortable=sortable,
            filterable=filterable,
            filter_action="native",
            sort_action="native",
            sort_mode="multi",
            page_action="native",
            style_table={
                'overflowX': 'auto',
            },
            style_cell={
                'backgroundColor': colors['surface'],
                'color': colors['text'],
                'fontSize': '14px',
                'padding': '10px',
                'textAlign': 'left',
                'border': f'1px solid {colors["border"]}',
            },
            style_header={
                'backgroundColor': colors['primary'],
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'left',
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': colors['background'],
                }
            ],
        )

    def create_row(
        self,
        components: List[Any],
        col_widths: Optional[List[int]] = None,
    ) -> html.Div:
        """
        Create a row layout with specified columns.

        Args:
            components: List of components to place in columns
            col_widths: Optional list of column widths (default: equal width)

        Returns:
            Dash html.Div with row layout
        """
        if col_widths is None:
            col_widths = [12 // len(components)] * len(components)

        columns = []
        for component, width in zip(components, col_widths):
            columns.append(
                html.Div(component, className=f"col-md-{width}", style={'padding': '10px'})
            )

        return html.Div(columns, className="row")

    def create_tabs(
        self,
        tabs: List[Dict[str, Any]],
        tab_id: str,
    ) -> dbc.Tabs:
        """
        Create tabbed interface.

        Args:
            tabs: List of tab dictionaries with 'label' and 'content' keys
            tab_id: Component ID

        Returns:
            Dash Bootstrap Tabs component
        """
        tab_items = [
            dbc.Tab(
                tab['content'],
                label=tab['label'],
                tab_id=tab.get('tab_id', f"tab-{i}"),
            )
            for i, tab in enumerate(tabs)
        ]

        return dbc.Tabs(
            tab_items,
            id=tab_id,
            active_tab=tabs[0].get('tab_id', 'tab-0') if tabs else 'tab-0',
        )

    def create_alert(
        self,
        message: str,
        alert_type: str = "info",
        dismissable: bool = True,
    ) -> dbc.Alert:
        """
        Create alert message component.

        Args:
            message: Alert message text
            alert_type: Alert type (primary, secondary, success, danger, warning, info, light, dark)
            dismissable: Whether alert can be dismissed

        Returns:
            Dash Bootstrap Alert component
        """
        return dbc.Alert(
            message,
            color=alert_type,
            dismissable=dismissable,
            className="mb-3",
        )

    def create_loading_spinner(
        self,
        text: str = "Loading...",
        spinner_id: str = "loading-spinner",
    ) -> html.Div:
        """
        Create loading spinner component.

        Args:
            text: Loading text
            spinner_id: Component ID

        Returns:
            Dash html.Div with spinner
        """
        return html.Div(
            [
                dbc.Spinner(
                    color="primary",
                    size="sm",
                    type="grow",
                ),
                html.Span(text, className="ms-2"),
            ],
            id=spinner_id,
            className="d-flex justify-content-center align-items-center p-5",
        )
