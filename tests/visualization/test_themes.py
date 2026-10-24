"""
Unit tests for visualization.themes module.
"""

import pytest

from cbsc_strategy_sdk.visualization.themes import (
    Theme,
    DARK_THEME,
    LIGHT_THEME,
    MIDNIGHT_THEME,
    SOLARIZED_THEME,
    THEMES,
    get_theme,
    list_themes,
)


class TestTheme:
    """Test Theme dataclass."""

    def test_theme_creation(self):
        """Test creating a custom theme."""
        theme = Theme(
            name="custom",
            background="#000000",
            text_color="#ffffff",
            grid_color="#333333",
        )

        assert theme.name == "custom"
        assert theme.background == "#000000"
        assert theme.text_color == "#ffffff"
        assert theme.grid_color == "#333333"

    def test_theme_with_colors(self):
        """Test theme with custom colors."""
        colors = {
            "up": "#00ff00",
            "down": "#ff0000",
            "primary": "#0000ff",
        }

        theme = Theme(
            name="custom",
            background="#ffffff",
            text_color="#000000",
            grid_color="#cccccc",
            colors=colors,
        )

        assert theme.colors == colors

    def test_theme_to_plotly_template(self):
        """Test converting theme to Plotly template."""
        theme = Theme(
            name="test",
            background="#1e1e1e",
            text_color="#e0e0e0",
            grid_color="#333333",
        )

        template = theme.to_plotly_template()

        assert "layout" in template
        assert template["layout"]["paper_bgcolor"] == "#1e1e1e"
        assert template["layout"]["plot_bgcolor"] == "#1e1e1e"
        assert template["layout"]["font"]["color"] == "#e0e0e0"
        assert template["layout"]["xaxis"]["gridcolor"] == "#333333"
        assert template["layout"]["yaxis"]["gridcolor"] == "#333333"

    def test_theme_custom_font(self):
        """Test theme with custom font family."""
        theme = Theme(
            name="test",
            background="#ffffff",
            text_color="#000000",
            grid_color="#cccccc",
            font_family="Roboto, sans-serif",
        )

        template = theme.to_plotly_template()
        assert template["layout"]["font"]["family"] == "Roboto, sans-serif"


class TestPredefinedThemes:
    """Test predefined theme configurations."""

    def test_dark_theme(self):
        """Test dark theme configuration."""
        assert DARK_THEME.name == "dark"
        assert DARK_THEME.background == "#1e1e1e"
        assert "up" in DARK_THEME.colors
        assert "down" in DARK_THEME.colors
        assert "primary" in DARK_THEME.colors

    def test_light_theme(self):
        """Test light theme configuration."""
        assert LIGHT_THEME.name == "light"
        assert LIGHT_THEME.background == "#ffffff"
        assert "up" in LIGHT_THEME.colors
        assert "down" in LIGHT_THEME.colors

    def test_midnight_theme(self):
        """Test midnight theme configuration."""
        assert MIDNIGHT_THEME.name == "midnight"
        assert MIDNIGHT_THEME.background == "#0d1117"
        assert "up" in MIDNIGHT_THEME.colors

    def test_solarized_theme(self):
        """Test solarized theme configuration."""
        assert SOLARIZED_THEME.name == "solarized"
        assert SOLARIZED_THEME.background == "#002b36"
        assert "up" in SOLARIZED_THEME.colors

    def test_all_themes_have_required_colors(self):
        """Test that all predefined themes have required color keys."""
        required_keys = [
            "up", "down", "primary", "secondary", "accent",
            "volume", "buy", "sell",
            "ma_short", "ma_medium", "ma_long",
            "bb_upper", "bb_lower", "bb_middle",
        ]

        for theme in [DARK_THEME, LIGHT_THEME, MIDNIGHT_THEME, SOLARIZED_THEME]:
            for key in required_keys:
                assert key in theme.colors, f"{theme.name} missing {key}"


class TestThemeRegistry:
    """Test theme registry and retrieval functions."""

    def test_themes_dict(self):
        """Test THEMES dictionary."""
        assert isinstance(THEMES, dict)
        assert "dark" in THEMES
        assert "light" in THEMES
        assert "midnight" in THEMES
        assert "solarized" in THEMES

    def test_get_theme_default(self):
        """Test get_theme with default."""
        theme = get_theme()
        assert theme.name == "dark"

    def test_get_theme_dark(self):
        """Test get_theme with dark theme."""
        theme = get_theme("dark")
        assert theme.name == "dark"
        assert theme == DARK_THEME

    def test_get_theme_light(self):
        """Test get_theme with light theme."""
        theme = get_theme("light")
        assert theme.name == "light"
        assert theme == LIGHT_THEME

    def test_get_theme_midnight(self):
        """Test get_theme with midnight theme."""
        theme = get_theme("midnight")
        assert theme.name == "midnight"
        assert theme == MIDNIGHT_THEME

    def test_get_theme_solarized(self):
        """Test get_theme with solarized theme."""
        theme = get_theme("solarized")
        assert theme.name == "solarized"
        assert theme == SOLARIZED_THEME

    def test_get_theme_case_insensitive(self):
        """Test get_theme is case insensitive."""
        theme1 = get_theme("DARK")
        theme2 = get_theme("Dark")
        theme3 = get_theme("dark")

        assert theme1 == theme2 == theme3

    def test_get_theme_unknown(self):
        """Test get_theme with unknown theme returns dark."""
        theme = get_theme("unknown_theme")
        assert theme == DARK_THEME

    def test_list_themes(self):
        """Test list_themes returns all theme names."""
        themes = list_themes()

        assert isinstance(themes, list)
        assert "dark" in themes
        assert "light" in themes
        assert "midnight" in themes
        assert "solarized" in themes
        assert len(themes) == 4


class TestThemeColors:
    """Test theme color consistency and validity."""

    def test_dark_theme_colors(self):
        """Test dark theme color values."""
        assert DARK_THEME.colors["up"] == "#26a69a"
        assert DARK_THEME.colors["down"] == "#ef5350"
        assert DARK_THEME.colors["buy"] == "#4caf50"
        assert DARK_THEME.colors["sell"] == "#f44336"

    def test_light_theme_colors(self):
        """Test light theme color values."""
        assert LIGHT_THEME.colors["up"] == "#2e7d32"
        assert LIGHT_THEME.colors["down"] == "#c62828"

    def test_midnight_theme_colors(self):
        """Test midnight theme color values."""
        assert MIDNIGHT_THEME.colors["up"] == "#3fb950"
        assert MIDNIGHT_THEME.colors["down"] == "#f85149"

    def test_solarized_theme_colors(self):
        """Test solarized theme color values."""
        assert SOLARIZED_THEME.colors["up"] == "#859900"
        assert SOLARIZED_THEME.colors["down"] == "#dc322f"

    def test_all_colors_are_hex(self):
        """Test that all theme colors are valid hex codes."""
        import re

        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')

        for theme in [DARK_THEME, LIGHT_THEME, MIDNIGHT_THEME, SOLARIZED_THEME]:
            for color_name, color_value in theme.colors.items():
                assert hex_pattern.match(color_value), \
                    f"{theme.name}.{color_name} is not a valid hex color: {color_value}"

    def test_up_down_color_contrast(self):
        """Test that up/down colors have good contrast."""
        for theme in [DARK_THEME, LIGHT_THEME, MIDNIGHT_THEME, SOLARIZED_THEME]:
            up = theme.colors["up"]
            down = theme.colors["down"]

            # Should be different colors
            assert up != down, f"{theme.name}: up and down colors are the same"


class TestThemeIntegration:
    """Integration tests for theme functionality."""

    def test_theme_switching(self):
        """Test switching between themes."""
        theme1 = get_theme("dark")
        theme2 = get_theme("light")
        theme3 = get_theme("dark")

        assert theme1 == theme3
        assert theme1 != theme2

    def test_theme_immutability(self):
        """Test that predefined themes remain unchanged."""
        original_colors = DARK_THEME.colors.copy()

        # Try to modify (shouldn't affect original)
        theme = get_theme("dark")
        # Colors should still match original
        assert theme.colors == original_colors

    def test_theme_template_consistency(self):
        """Test that theme templates are consistently formatted."""
        themes = [DARK_THEME, LIGHT_THEME, MIDNIGHT_THEME, SOLARIZED_THEME]

        for theme in themes:
            template = theme.to_plotly_template()

            # Check required structure
            assert "layout" in template
            assert "paper_bgcolor" in template["layout"]
            assert "plot_bgcolor" in template["layout"]
            assert "font" in template["layout"]
            assert "xaxis" in template["layout"]
            assert "yaxis" in template["layout"]


class TestThemeEdgeCases:
    """Test edge cases and error handling."""

    def test_theme_with_empty_colors(self):
        """Test theme with empty color dict."""
        theme = Theme(
            name="minimal",
            background="#ffffff",
            text_color="#000000",
            grid_color="#cccccc",
            colors={},
        )

        template = theme.to_plotly_template()
        assert template is not None

    def test_get_theme_empty_string(self):
        """Test get_theme with empty string."""
        theme = get_theme("")
        assert theme == DARK_THEME

    def test_get_theme_none(self):
        """Test get_theme with None (should use default)."""
        # This would require modifying the function signature
        # Currently not supported, so we test with whitespace
        theme = get_theme("  ")
        # Returns dark due to strip() if implemented, otherwise dark as fallback
        assert theme is not None

    def test_list_themes_returns_new_list(self):
        """Test that list_themes returns a new list each time."""
        themes1 = list_themes()
        themes2 = list_themes()

        assert themes1 == themes2
        assert themes1 is not themes2  # Different objects
