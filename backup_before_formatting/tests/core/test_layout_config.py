"""Test LayoutConfig Model.

Tests for the LayoutConfig Pydantic model.
"""

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest

from src.core.layout_config import (
    GridConfig,
    LayoutConfig,
    LayoutData,
    ThemeConfig,
    WidgetConfig,
)


class TestGridConfig:
    """Test suite for GridConfig model."""

    def test_valid_grid_config(self):
        """Test creating a valid GridConfig."""
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        assert grid.width == 12
        assert grid.height == 8
        assert grid.cell_width == 100
        assert grid.cell_height == 80

    def test_width_height_bounds(self):
        """Test width and height constraints."""
        # Valid ranges
        grid = GridConfig(width=1, height=1, cell_width=100, cell_height=80)
        assert grid.width == 1

        grid = GridConfig(width=50, height=50, cell_width=100, cell_height=80)
        assert grid.width == 50

        # Invalid: width < 1
        with pytest.raises(ValueError):
            GridConfig(width=0, height=8, cell_width=100, cell_height=80)

        # Invalid: width > 50
        with pytest.raises(ValueError):
            GridConfig(width=51, height=8, cell_width=100, cell_height=80)

    def test_cell_size_bounds(self):
        """Test cell_width and cell_height constraints."""
        # Valid ranges
        grid = GridConfig(width=12, height=8, cell_width=10, cell_height=10)
        assert grid.cell_width == 10

        grid = GridConfig(width=12, height=8, cell_width=500, cell_height=500)
        assert grid.cell_width == 500

        # Invalid: too small
        with pytest.raises(ValueError):
            GridConfig(width=12, height=8, cell_width=9, cell_height=80)

        # Invalid: too large
        with pytest.raises(ValueError):
            GridConfig(width=12, height=8, cell_width=501, cell_height=80)


class TestWidgetConfig:
    """Test suite for WidgetConfig model."""

    def test_valid_widget_config(self):
        """Test creating a valid WidgetConfig."""
        widget = WidgetConfig(
            id="widget - 1",
            type="price - chart",
            x=0,
            y=0,
            w=6,
            h=4,
            config={"symbol": "0700.HK", "timeframe": "1d", "show_volume": True},
        )

        assert widget.id == "widget - 1"
        assert widget.type == "price - chart"
        assert widget.x == 0
        assert widget.y == 0
        assert widget.w == 6
        assert widget.h == 4
        assert widget.config["symbol"] == "0700.HK"

    def test_type_validation(self):
        """Test type field validation."""
        # Valid types
        valid_types = [
            "price - chart",
            "performance - chart",
            "heatmap",
            "scatter",
            "config - panel",
            "toolbar",
            "watchlist",
            "news - feed",
            "order - book",
            "trade - history",
        ]

        for widget_type in valid_types:
            widget = WidgetConfig(id="widget - 1", type=widget_type, x=0, y=0, w=1, h=1)
            assert widget.type == widget_type

        # Invalid type
        with pytest.raises(ValueError):
            WidgetConfig(id="widget - 1", type="invalid_type", x=0, y=0, w=1, h=1)

    def test_size_validation(self):
        """Test w and h constraints."""
        # Valid sizes
        widget = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)
        assert widget.w == 1
        assert widget.h == 1

        widget = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=50, h=50)
        assert widget.w == 50

        # Invalid: w < 1
        with pytest.raises(ValueError):
            WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=0, h=1)

        # Invalid: h < 1
        with pytest.raises(ValueError):
            WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=0)

    def test_coordinate_validation(self):
        """Test x and y constraints."""
        # Valid coordinates
        widget = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)
        assert widget.x == 0
        assert widget.y == 0

        widget = WidgetConfig(id="widget - 1", type="price - chart", x=100, y=200, w=1, h=1)
        assert widget.x == 100

        # Invalid: x < 0
        with pytest.raises(ValueError):
            WidgetConfig(id="widget - 1", type="price - chart", x=-1, y=0, w=1, h=1)

        # Invalid: y < 0
        with pytest.raises(ValueError):
            WidgetConfig(id="widget - 1", type="price - chart", x=0, y=-1, w=1, h=1)

    def test_to_dict(self):
        """Test to_dict method."""
        widget = WidgetConfig(
            id="widget - 1",
            type="price - chart",
            x=0,
            y=0,
            w=6,
            h=4,
            config={"symbol": "0700.HK"},
        )

        data = widget.to_dict()
        assert isinstance(data, dict)
        assert data["id"] == "widget - 1"
        assert data["type"] == "price - chart"


class TestThemeConfig:
    """Test suite for ThemeConfig model."""

    def test_valid_theme_config(self):
        """Test creating a valid ThemeConfig."""
        theme = ThemeConfig(
            mode="dark",
            primary_color="#3b82f6",
            background_color="#1f2937",
            text_color="#f9fafb",
            font_family="Inter",
            font_size=14,
        )

        assert theme.mode == "dark"
        assert theme.primary_color == "#3b82f6"
        assert theme.font_family == "Inter"
        assert theme.font_size == 14

    def test_default_values(self):
        """Test default values for ThemeConfig."""
        theme = ThemeConfig()

        assert theme.mode == "light"
        assert theme.primary_color == "#3b82f6"
        assert theme.background_color == "#ffffff"
        assert theme.text_color == "#000000"
        assert theme.font_family == "Arial"
        assert theme.font_size == 14

    def test_mode_validation(self):
        """Test mode field validation."""
        # Valid modes
        theme1 = ThemeConfig(mode="dark")
        assert theme1.mode == "dark"

        theme2 = ThemeConfig(mode="light")
        assert theme2.mode == "light"

        # Invalid mode
        with pytest.raises(ValueError):
            ThemeConfig(mode="blue")

    def test_color_validation(self):
        """Test color field validation."""
        # Valid colors
        theme = ThemeConfig(
            primary_color="#fffff", background_color="#000000", text_color="#123456"
        )
        assert theme.primary_color == "#ffffff"

        # Invalid: not hex format
        with pytest.raises(ValueError):
            ThemeConfig(primary_color="white")

        # Invalid: wrong length
        with pytest.raises(ValueError):
            ThemeConfig(primary_color="#ffffffa")

        # Invalid: not starting with #
        with pytest.raises(ValueError):
            ThemeConfig(primary_color="ffffff")

    def test_font_size_bounds(self):
        """Test font_size constraints."""
        # Valid range
        theme1 = ThemeConfig(font_size=10)
        assert theme1.font_size == 10

        theme2 = ThemeConfig(font_size=24)
        assert theme2.font_size == 24

        # Invalid: too small
        with pytest.raises(ValueError):
            ThemeConfig(font_size=9)

        # Invalid: too large
        with pytest.raises(ValueError):
            ThemeConfig(font_size=25)


class TestLayoutData:
    """Test suite for LayoutData model."""

    def test_valid_layout_data(self):
        """Test creating a valid LayoutData."""
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        widgets = [WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=6, h=4)]

        layout_data = LayoutData(grid=grid, widgets=widgets)

        assert layout_data.grid.width == 12
        assert len(layout_data.widgets) == 1
        assert layout_data.widgets[0].id == "widget - 1"

    def test_max_widgets_limit(self):
        """Test max_length constraint for widgets."""
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        # Create 20 widgets (max allowed)
        widgets = [
            WidgetConfig(id=f"widget-{i}", type="price - chart", x=0, y=0, w=1, h=1)
            for i in range(20)
        ]

        layout_data = LayoutData(grid=grid, widgets=widgets)
        assert len(layout_data.widgets) == 20


class TestLayoutConfig:
    """Test suite for LayoutConfig model."""

    def test_valid_layout_config(self):
        """Test creating a valid LayoutConfig instance."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        widgets = [WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=6, h=4)]

        layout_data = LayoutData(grid=grid, widgets=widgets)
        theme = ThemeConfig(mode="dark")

        config = LayoutConfig(
            name="我的工作區",
            user_id=user_id,
            layout_data=layout_data,
            theme=theme,
            is_default=True,
        )

        assert config.name == "我的工作區"
        assert config.user_id == user_id
        assert config.layout_data.grid.width == 12
        assert config.theme.mode == "dark"
        assert config.is_default is True

    def test_default_values(self):
        """Test default values for LayoutConfig."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        config = LayoutConfig(
            name="Test Layout", user_id=user_id, layout_data=layout_data
        )

        assert config.is_default is False
        assert config.theme.mode == "light"

    def test_name_validation(self):
        """Test name field validation."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        # Valid names
        config1 = LayoutConfig(
            name="A", user_id=user_id, layout_data=layout_data  # 1 character
        )
        assert config1.name == "A"

        config2 = LayoutConfig(
            name="A" * 50, user_id=user_id, layout_data=layout_data  # 50 characters
        )
        assert len(config2.name) == 50

        # Invalid: empty name
        with pytest.raises(ValueError):
            LayoutConfig(name="", user_id=user_id, layout_data=layout_data)

        # Invalid: too long
        with pytest.raises(ValueError):
            LayoutConfig(
                name="A" * 51, user_id=user_id, layout_data=layout_data  # 51 characters
            )

    def test_to_dict(self):
        """Test to_dict method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        data = config.to_dict()
        assert isinstance(data, dict)
        assert data["name"] == "Test"
        assert "created_at" in data

    def test_to_json(self):
        """Test to_json method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        json_str = config.to_json()
        assert isinstance(json_str, str)
        assert "Test" in json_str

    def test_from_json(self):
        """Test from_json class method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        original = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        json_str = original.to_json()
        restored = LayoutConfig.from_json(json_str)

        assert restored.name == original.name
        assert restored.user_id == original.user_id

    def test_add_widget(self):
        """Test add_widget method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        assert len(config.layout_data.widgets) == 0

        widget = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)

        config.add_widget(widget)

        assert len(config.layout_data.widgets) == 1
        assert config.layout_data.widgets[0].id == "widget - 1"

    def test_add_duplicate_widget(self):
        """Test adding duplicate widget ID raises error."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        widget1 = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)

        widget2 = WidgetConfig(
            id="widget - 1", type="price - chart", x=1, y=0, w=1, h=1  # Same ID
        )

        layout_data = LayoutData(grid=grid, widgets=[widget1])
        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        with pytest.raises(ValueError, match="Widget with id widget - 1 already exists"):
            config.add_widget(widget2)

    def test_remove_widget(self):
        """Test remove_widget method."""
        user_id = uuid4()
        widget1 = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)
        widget2 = WidgetConfig(id="widget - 2", type="price - chart", x=1, y=0, w=1, h=1)

        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[widget1, widget2])

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        assert len(config.layout_data.widgets) == 2

        config.remove_widget("widget - 1")

        assert len(config.layout_data.widgets) == 1
        assert config.layout_data.widgets[0].id == "widget - 2"

    def test_get_widget(self):
        """Test get_widget method."""
        user_id = uuid4()
        widget1 = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)

        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[widget1])

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        retrieved = config.get_widget("widget - 1")
        assert retrieved is not None
        assert retrieved.id == "widget - 1"

        retrieved = config.get_widget("nonexistent")
        assert retrieved is None

    def test_update_widget(self):
        """Test update_widget method."""
        user_id = uuid4()
        widget = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)

        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[widget])

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        config.update_widget("widget - 1", {"x": 5, "y": 3})

        updated = config.get_widget("widget - 1")
        assert updated.x == 5
        assert updated.y == 3

    def test_set_as_default(self):
        """Test set_as_default method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        assert config.is_default is False
        config.set_as_default()
        assert config.is_default is True

    def test_clone(self):
        """Test clone method."""
        user_id = uuid4()
        widget = WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=1, h=1)

        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[widget])

        original = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        clone = original.clone()

        # Should have different config_id
        assert clone.config_id != original.config_id

        # Should have different widget IDs
        assert clone.layout_data.widgets[0].id != original.layout_data.widgets[0].id

        # Other attributes should be the same
        assert clone.name == original.name
        assert clone.user_id == original.user_id
        assert clone.layout_data.grid.width == original.layout_data.grid.width

    def test_is_valid(self):
        """Test is_valid method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)
        layout_data = LayoutData(grid=grid, widgets=[])

        # Valid config
        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)
        assert config.is_valid() is True

    def test_get_widget_count(self):
        """Test get_widget_count method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        widgets = [
            WidgetConfig(id=f"widget-{i}", type="price - chart", x=0, y=0, w=1, h=1)
            for i in range(5)
        ]

        layout_data = LayoutData(grid=grid, widgets=widgets)

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        assert config.get_widget_count() == 5

    def test_get_widgets_by_type(self):
        """Test get_widgets_by_type method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        widgets = [
            WidgetConfig(
                id=f"widget-{i}",
                type="price - chart" if i % 2 == 0 else "config - panel",
                x=0,
                y=i,
                w=1,
                h=1,
            )
            for i in range(4)
        ]

        layout_data = LayoutData(grid=grid, widgets=widgets)

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        price_widgets = config.get_widgets_by_type("price - chart")
        assert len(price_widgets) == 2

        config_widgets = config.get_widgets_by_type("config - panel")
        assert len(config_widgets) == 2

    def test_get_layout_bounds(self):
        """Test get_layout_bounds method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        widgets = [
            WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=6, h=4),
            WidgetConfig(id="widget - 2", type="price - chart", x=6, y=4, w=4, h=2),
        ]

        layout_data = LayoutData(grid=grid, widgets=widgets)

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        bounds = config.get_layout_bounds()

        assert bounds["w"] == 10  # max_x = 6 + 4 or 0 + 6
        assert bounds["h"] == 6  # max_y = 4 + 2 or 0 + 4

    def test_check_collisions(self):
        """Test check_collisions method."""
        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        # Widget 1: (0, 0) size (6, 4)
        # Widget 2: (3, 2) size (5, 3) - Overlaps with widget 1
        # Widget 3: (7, 0) size (3, 3) - No overlap

        widgets = [
            WidgetConfig(id="widget - 1", type="price - chart", x=0, y=0, w=6, h=4),
            WidgetConfig(id="widget - 2", type="price - chart", x=3, y=2, w=5, h=3),
            WidgetConfig(id="widget - 3", type="price - chart", x=7, y=0, w=3, h=3),
        ]

        layout_data = LayoutData(grid=grid, widgets=widgets)

        config = LayoutConfig(name="Test", user_id=user_id, layout_data=layout_data)

        collisions = config.check_collisions()

        assert len(collisions) == 2  # widget - 1 overlaps with widget - 2

    def test_serialization_performance(self):
        """Test serialization performance (should be < 10ms)."""
        import time

        user_id = uuid4()
        grid = GridConfig(width=12, height=8, cell_width=100, cell_height=80)

        widgets = [
            WidgetConfig(
                id=f"widget-{i}",
                type="price - chart",
                x=i * 2,
                y=0,
                w=2,
                h=2,
                config={"symbol": f"070{i}.HK"},
            )
            for i in range(5)
        ]

        layout_data = LayoutData(grid=grid, widgets=widgets)
        theme = ThemeConfig(mode="dark")

        config = LayoutConfig(
            name="我的工作區", user_id=user_id, layout_data=layout_data, theme=theme
        )

        # Test serialization
        start = time.perf_counter()
        json_str = config.to_json()
        serialize_time = (time.perf_counter() - start) * 1000

        assert serialize_time < 10, f"Serialization took {serialize_time:.2f}ms"

        # Test deserialization
        start = time.perf_counter()
        restored = LayoutConfig.from_json(json_str)
        deserialize_time = (time.perf_counter() - start) * 1000

        assert deserialize_time < 10, f"Deserialization took {deserialize_time:.2f}ms"
