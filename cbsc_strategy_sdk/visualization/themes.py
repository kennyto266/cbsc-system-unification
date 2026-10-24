"""
Theme configurations for visualization module.

Provides color schemes and styling options for charts and widgets.
"""

from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class Theme:
    """Base theme configuration for visualizations."""

    name: str
    background: str
    text_color: str
    grid_color: str
    colors: Dict[str, str] = field(default_factory=dict)
    font_family: str = "Arial, sans-serif"

    def to_plotly_template(self) -> Dict[str, Any]:
        """Convert theme to Plotly template format."""
        return {
            "layout": {
                "paper_bgcolor": self.background,
                "plot_bgcolor": self.background,
                "font": {
                    "color": self.text_color,
                    "family": self.font_family
                },
                "xaxis": {
                    "gridcolor": self.grid_color,
                    "zerolinecolor": self.grid_color,
                },
                "yaxis": {
                    "gridcolor": self.grid_color,
                    "zerolinecolor": self.grid_color,
                },
            }
        }


# Predefined themes
DARK_THEME = Theme(
    name="dark",
    background="#1e1e1e",
    text_color="#e0e0e0",
    grid_color="#333333",
    colors={
        "up": "#26a69a",
        "down": "#ef5350",
        "primary": "#42a5f5",
        "secondary": "#ab47bc",
        "accent": "#ffca28",
        "volume": "#78909c",
        "buy": "#4caf50",
        "sell": "#f44336",
        "ma_short": "#29b6f6",
        "ma_medium": "#66bb6a",
        "ma_long": "#ffa726",
        "bb_upper": "#ef5350",
        "bb_lower": "#26a69a",
        "bb_middle": "#78909c",
    }
)

LIGHT_THEME = Theme(
    name="light",
    background="#ffffff",
    text_color="#212121",
    grid_color="#e0e0e0",
    colors={
        "up": "#2e7d32",
        "down": "#c62828",
        "primary": "#1976d2",
        "secondary": "#7b1fa2",
        "accent": "#f57f17",
        "volume": "#546e7a",
        "buy": "#388e3c",
        "sell": "#d32f2f",
        "ma_short": "#0288d1",
        "ma_medium": "#43a047",
        "ma_long": "#fb8c00",
        "bb_upper": "#d32f2f",
        "bb_lower": "#388e3c",
        "bb_middle": "#546e7a",
    }
)

MIDNIGHT_THEME = Theme(
    name="midnight",
    background="#0d1117",
    text_color="#c9d1d9",
    grid_color="#21262d",
    colors={
        "up": "#3fb950",
        "down": "#f85149",
        "primary": "#58a6ff",
        "secondary": "#bc8cff",
        "accent": "#d29922",
        "volume": "#8b949e",
        "buy": "#2ea043",
        "sell": "#da3633",
        "ma_short": "#79c0ff",
        "ma_medium": "#56d364",
        "ma_long": "#e3b341",
        "bb_upper": "#ff7b72",
        "bb_lower": "#3fb950",
        "bb_middle": "#8b949e",
    }
)

SOLARIZED_THEME = Theme(
    name="solarized",
    background="#002b36",
    text_color="#839496",
    grid_color="#073642",
    colors={
        "up": "#859900",
        "down": "#dc322f",
        "primary": "#268bd2",
        "secondary": "#6c71c4",
        "accent": "#b58900",
        "volume": "#586e75",
        "buy": "#859900",
        "sell": "#dc322f",
        "ma_short": "#2aa198",
        "ma_medium": "#859900",
        "ma_long": "#b58900",
        "bb_upper": "#dc322f",
        "bb_lower": "#859900",
        "bb_middle": "#586e75",
    }
)

# Theme registry
THEMES: Dict[str, Theme] = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "midnight": MIDNIGHT_THEME,
    "solarized": SOLARIZED_THEME,
}


def get_theme(name: str = "dark") -> Theme:
    """Get a theme by name. Returns dark theme if not found."""
    return THEMES.get(name.lower(), DARK_THEME)


def list_themes() -> list[str]:
    """List all available theme names."""
    return list(THEMES.keys())
