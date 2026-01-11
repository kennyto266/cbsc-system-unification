"""
Theme management for Dash dashboard.

Provides ThemeManager class for switching between dark and light themes
with customizable color schemes for Dash components.
"""

from typing import Dict, Any, Optional


class ThemeManager:
    """
    Manage dashboard themes for Dash applications.

    Supports dark and light themes with customizable color schemes.
    Integrates with dash-bootstrap-components for consistent styling.
    """

    # Dark theme color scheme
    DARK_THEME = {
        'background': '#1e1e1e',
        'surface': '#2d2d2d',
        'primary': '#42a5f5',
        'secondary': '#ab47bc',
        'success': '#66bb6a',
        'warning': '#ffa726',
        'danger': '#ef5350',
        'info': '#26c6da',
        'text': '#e0e0e0',
        'text_secondary': '#b0b0b0',
        'border': '#404040',
        'grid': '#333333',
        'up': '#26a69a',
        'down': '#ef5350',
    }

    # Light theme color scheme
    LIGHT_THEME = {
        'background': '#ffffff',
        'surface': '#f5f5f5',
        'primary': '#1976d2',
        'secondary': '#7b1fa2',
        'success': '#388e3c',
        'warning': '#f57c00',
        'danger': '#d32f2f',
        'info': '#0288d1',
        'text': '#212121',
        'text_secondary': '#757575',
        'border': '#e0e0e0',
        'grid': '#eeeeee',
        'up': '#2e7d32',
        'down': '#c62828',
    }

    def __init__(self, initial_theme: str = "dark"):
        """
        Initialize ThemeManager.

        Args:
            initial_theme: Initial theme name ('dark' or 'light')
        """
        if initial_theme not in ["dark", "light"]:
            raise ValueError(f"Invalid theme: {initial_theme}. Use 'dark' or 'light'")

        self.theme = initial_theme
        self._themes = {
            "dark": self.DARK_THEME,
            "light": self.LIGHT_THEME
        }

    def get_colors(self) -> Dict[str, str]:
        """
        Get current theme color scheme.

        Returns:
            Dictionary of color names to hex values
        """
        return self._themes[self.theme].copy()

    def get_color(self, name: str) -> str:
        """
        Get a specific color from current theme.

        Args:
            name: Color name (e.g., 'primary', 'background')

        Returns:
            Hex color string
        """
        return self._themes[self.theme].get(name, '#000000')

    def toggle_theme(self) -> str:
        """
        Toggle between dark and light themes.

        Returns:
            New theme name ('dark' or 'light')
        """
        self.theme = "light" if self.theme == "dark" else "dark"
        return self.theme

    def set_theme(self, theme: str) -> None:
        """
        Set specific theme.

        Args:
            theme: Theme name ('dark' or 'light')
        """
        if theme not in ["dark", "light"]:
            raise ValueError(f"Invalid theme: {theme}. Use 'dark' or 'light'")
        self.theme = theme

    def get_stylesheet_url(self) -> str:
        """
        Get bootstrap stylesheet URL for current theme.

        Returns:
            URL to bootstrap CDN stylesheet
        """
        if self.theme == "dark":
            return "https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/darkly/bootstrap.min.css"
        else:
            return "https://cdn.jsdelivr.net/npm/bootswatch@5.3.0/dist/flatly/bootstrap.min.css"

    def get_plotly_template(self) -> Dict[str, Any]:
        """
        Get Plotly layout template for current theme.

        Returns:
            Dictionary with Plotly layout settings
        """
        colors = self.get_colors()

        return {
            'layout': {
                'paper_bgcolor': colors['background'],
                'plot_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']
                },
                'xaxis': {
                    'gridcolor': colors['grid'],
                    'linecolor': colors['border'],
                    'tickcolor': colors['border'],
                },
                'yaxis': {
                    'gridcolor': colors['grid'],
                    'linecolor': colors['border'],
                    'tickcolor': colors['border'],
                },
                'colorway': [
                    colors['primary'],
                    colors['secondary'],
                    colors['success'],
                    colors['warning'],
                    colors['info'],
                ]
            }
        }

    def get_card_style(self) -> Dict[str, str]:
        """
        Get card styling for current theme.

        Returns:
            Dictionary with CSS style properties
        """
        colors = self.get_colors()
        return {
            'backgroundColor': colors['surface'],
            'color': colors['text'],
            'border': f'1px solid {colors["border"]}',
            'borderRadius': '8px',
            'padding': '20px',
        }

    def get_metric_card_style(self, is_positive: bool = True) -> Dict[str, str]:
        """
        Get metric card styling with delta indicator.

        Args:
            is_positive: Whether metric is positive (affects color)

        Returns:
            Dictionary with CSS style properties
        """
        colors = self.get_colors()
        delta_color = colors['success'] if is_positive else colors['danger']

        return {
            'backgroundColor': colors['surface'],
            'color': colors['text'],
            'borderLeft': f'4px solid {delta_color}',
            'borderRadius': '8px',
            'padding': '15px',
            'margin': '10px 0',
        }

    @property
    def current_theme(self) -> str:
        """Get current theme name."""
        return self.theme

    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark."""
        return self.theme == "dark"

    @property
    def is_light(self) -> bool:
        """Check if current theme is light."""
        return self.theme == "light"
