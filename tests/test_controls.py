"""
Unit Tests for Controls Module

Comprehensive tests for all control widgets and functionality.
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Fix import path to avoid httpx dependency in main SDK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct imports from controls subpackage
from cbsc_strategy_sdk.controls.widgets import ControlWidgets
from cbsc_strategy_sdk.controls.validator import (
    ParameterValidator,
    ValidationResult,
    CommonValidators
)
from cbsc_strategy_sdk.controls.symbol_selector import SymbolSelector, QuickSymbolSelector
from cbsc_strategy_sdk.controls.date_picker import DateRangePicker, QuickDateRangePicker
from cbsc_strategy_sdk.controls.presets import PresetManager
from cbsc_strategy_sdk.controls.refresh import AutoRefreshManager, SimpleRefreshManager
from cbsc_strategy_sdk.controls.tabs import TabbedControls, AccordionControls
from cbsc_strategy_sdk.controls.panel import StrategyControlPanel, QuickControlPanel


# ============================================================================
# ControlWidgets Tests
# ============================================================================

class TestControlWidgets:
    """Test ControlWidgets static methods"""

    def test_slider_creation(self):
        """Test slider widget creation"""
        widget = ControlWidgets.slider(
            name="test_param",
            min_value=0,
            max_value=100,
            initial_value=50
        )
        assert widget.value == 50
        assert widget.min == 0
        assert widget.max == 100
        assert widget.step == 0.1
        assert widget._control_name == "test_param"

    def test_int_slider_creation(self):
        """Test integer slider creation"""
        widget = ControlWidgets.int_slider(
            name="int_param",
            min_value=0,
            max_value=10,
            initial_value=5
        )
        assert widget.value == 5
        assert widget.min == 0
        assert widget.max == 10
        assert isinstance(widget.value, int)

    def test_dropdown_creation(self):
        """Test dropdown widget creation"""
        options = ["Option A", "Option B", "Option C"]
        widget = ControlWidgets.dropdown(
            name="choice_param",
            options=options,
            initial_value=options[1]
        )
        assert widget.value == "Option B"
        assert len(widget.options) == 3

    def test_text_input_creation(self):
        """Test text input widget creation"""
        widget = ControlWidgets.text_input(
            name="text_param",
            initial_value="test value"
        )
        assert widget.value == "test value"

    def test_checkbox_creation(self):
        """Test checkbox widget creation"""
        widget = ControlWidgets.checkbox(
            name="bool_param",
            initial_value=True
        )
        assert widget.value is True

    def test_bounded_float_text_creation(self):
        """Test bounded float text widget creation"""
        widget = ControlWidgets.bounded_float_text(
            name="bounded_param",
            min_value=0,
            max_value=1,
            initial_value=0.5
        )
        assert widget.value == 0.5
        assert widget.min == 0
        assert widget.max == 1


# ============================================================================
# ParameterValidator Tests
# ============================================================================

class TestParameterValidator:
    """Test ParameterValidator class"""

    def test_validation_result_valid(self):
        """Test ValidationResult for valid input"""
        result = ValidationResult(is_valid=True, errors=[])
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid input"""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"]
        )
        assert result.is_valid is False
        assert len(result.errors) == 2

    def test_validation_result_to_widget(self):
        """Test ValidationResult widget conversion"""
        result = ValidationResult(is_valid=True)
        widget = result.to_widget()
        assert "green" in widget.value or "Valid" in widget.value

    def test_add_rule(self):
        """Test adding validation rule"""
        validator = ParameterValidator()
        validator.add_rule(
            parameter="test",
            validator=lambda x: x > 0,
            error_message="Must be positive"
        )
        assert validator.has_rules("test")

    def test_validate_positive(self):
        """Test validation with positive value"""
        validator = ParameterValidator()
        validator.add_rule(
            parameter="value",
            validator=lambda x: x > 0,
            error_message="Must be positive"
        )
        result = validator.validate({"value": 5})
        assert result.is_valid is True

    def test_validate_negative(self):
        """Test validation with negative value"""
        validator = ParameterValidator()
        validator.add_rule(
            parameter="value",
            validator=lambda x: x > 0,
            error_message="Must be positive"
        )
        result = validator.validate({"value": -5})
        assert result.is_valid is False
        assert "Must be positive" in result.errors[0]

    def test_add_range_rule(self):
        """Test range validation rule"""
        validator = ParameterValidator()
        validator.add_range_rule("value", min_value=0, max_value=100)

        result = validator.validate({"value": 50})
        assert result.is_valid is True

        result = validator.validate({"value": 150})
        assert result.is_valid is False

    def test_add_choice_rule(self):
        """Test choice validation rule"""
        validator = ParameterValidator()
        validator.add_choice_rule("choice", choices=["A", "B", "C"])

        result = validator.validate({"choice": "B"})
        assert result.is_valid is True

        result = validator.validate({"choice": "D"})
        assert result.is_valid is False

    def test_clear_rules(self):
        """Test clearing validation rules"""
        validator = ParameterValidator()
        validator.add_rule("test", lambda x: True, "Error")
        assert validator.has_rules("test")

        validator.clear_rules("test")
        assert not validator.has_rules("test")


class TestCommonValidators:
    """Test CommonValidators class"""

    def test_positive_number(self):
        """Test positive number validator"""
        assert CommonValidators.positive_number(5) is True
        assert CommonValidators.positive_number(0) is False
        assert CommonValidators.positive_number(-1) is False

    def test_percentage(self):
        """Test percentage validator"""
        assert CommonValidators.percentage(50) is True
        assert CommonValidators.percentage(0) is True
        assert CommonValidators.percentage(100) is True
        assert CommonValidators.percentage(101) is False

    def test_non_empty_string(self):
        """Test non-empty string validator"""
        assert CommonValidators.non_empty_string("test") is True
        assert CommonValidators.non_empty_string("") is False
        assert CommonValidators.non_empty_string("   ") is False

    def test_valid_symbol(self):
        """Test symbol format validator"""
        assert CommonValidators.valid_symbol("AAPL") is True
        assert CommonValidators.valid_symbol("BTC-USD") is True
        assert CommonValidators.valid_symbol("") is False
        assert CommonValidators.valid_symbol("123$") is False


# ============================================================================
# SymbolSelector Tests
# ============================================================================

class TestSymbolSelector:
    """Test SymbolSelector class"""

    @pytest.fixture
    def symbols(self):
        """Sample symbols for testing"""
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"]

    @pytest.fixture
    def selector(self, symbols):
        """Create SymbolSelector instance"""
        return SymbolSelector(symbols, max_selections=3)

    def test_initialization(self, selector, symbols):
        """Test selector initialization"""
        assert len(selector.available_symbols) == len(symbols)
        assert len(selector.selected_symbols) == 0
        assert selector.max_selections == 3

    def test_selected_property(self, selector):
        """Test selected property"""
        selector.selected_symbols.add("AAPL")
        selector.selected_symbols.add("MSFT")
        selected = selector.selected
        assert "AAPL" in selected
        assert "MSFT" in selected
        assert selected == sorted(selected)

    def test_set_selection(self, selector):
        """Test set_selection method"""
        selector.set_selection(["AAPL", "MSFT"])
        assert "AAPL" in selector.selected_symbols
        assert "MSFT" in selector.selected_symbols

    def test_clear_selection(self, selector):
        """Test clear_selection method"""
        selector.selected_symbols.add("AAPL")
        selector.clear_selection()
        assert len(selector.selected_symbols) == 0

    def test_max_selections_limit(self, selector):
        """Test maximum selections limit"""
        selector.set_selection(["AAPL", "MSFT", "GOOGL", "AMZN"])
        # Should only keep first 3
        assert len(selector.selected_symbols) == 3


class TestQuickSymbolSelector:
    """Test QuickSymbolSelector class"""

    @pytest.fixture
    def selector(self):
        """Create QuickSymbolSelector instance"""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        return QuickSymbolSelector(symbols, multi=True)

    def test_initialization(self, selector):
        """Test selector initialization"""
        assert len(selector.available_symbols) == 4

    def test_selected_property(self, selector):
        """Test selected property"""
        selector.widget.value = ("AAPL", "MSFT")
        selected = selector.selected
        assert "AAPL" in selected
        assert "MSFT" in selected


# ============================================================================
# DateRangePicker Tests
# ============================================================================

class TestDateRangePicker:
    """Test DateRangePicker class"""

    @pytest.fixture
    def picker(self):
        """Create DateRangePicker instance"""
        return DateRangePicker()

    def test_initialization(self, picker):
        """Test picker initialization"""
        assert picker.start_date is not None
        assert picker.end_date is not None
        assert picker.start_date < picker.end_date

    def test_date_range_property(self, picker):
        """Test date_range property"""
        start, end = picker.date_range
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)

    def test_set_date_range(self, picker):
        """Test set_date_range method"""
        new_start = datetime(2024, 1, 1)
        new_end = datetime(2024, 12, 31)
        picker.set_date_range(new_start, new_end)
        assert picker.start_date == new_start
        assert picker.end_date == new_end

    def test_set_date_range_validation(self, picker):
        """Test set_date_range validation"""
        with pytest.raises(ValueError):
            picker.set_date_range(
                datetime(2024, 12, 31),
                datetime(2024, 1, 1)
            )


class TestQuickDateRangePicker:
    """Test QuickDateRangePicker class"""

    @pytest.fixture
    def picker(self):
        """Create QuickDateRangePicker instance"""
        return QuickDateRangePicker()

    def test_initialization(self, picker):
        """Test picker initialization"""
        assert picker.start_date is not None
        assert picker.end_date is not None

    def test_date_range_property(self, picker):
        """Test date_range property"""
        start, end = picker.date_range
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)


# ============================================================================
# PresetManager Tests
# ============================================================================

class TestPresetManager:
    """Test PresetManager class"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create PresetManager instance with temp file"""
        storage_path = tmp_path / "test_presets.json"
        return PresetManager(str(storage_path))

    @pytest.fixture
    def sample_params(self):
        """Sample parameters for testing"""
        return {
            "rsi_period": 14,
            "bb_period": 20,
            "symbols": ["AAPL", "MSFT"]
        }

    def test_save_preset(self, manager, sample_params):
        """Test saving preset"""
        manager.save_preset(
            "test_preset",
            sample_params,
            description="Test preset",
            tags=["test"]
        )
        assert "test_preset" in manager.presets

    def test_load_preset(self, manager, sample_params):
        """Test loading preset"""
        manager.save_preset("test_preset", sample_params)
        loaded = manager.load_preset("test_preset")
        assert loaded == sample_params

    def test_load_nonexistent_preset(self, manager):
        """Test loading non-existent preset"""
        with pytest.raises(KeyError):
            manager.load_preset("nonexistent")

    def test_delete_preset(self, manager, sample_params):
        """Test deleting preset"""
        manager.save_preset("test_preset", sample_params)
        manager.delete_preset("test_preset")
        assert "test_preset" not in manager.presets

    def test_list_presets(self, manager, sample_params):
        """Test listing presets"""
        manager.save_preset("preset1", sample_params)
        manager.save_preset("preset2", sample_params)
        presets = manager.list_presets()
        assert "preset1" in presets
        assert "preset2" in presets
        assert len(presets) == 2

    def test_update_preset(self, manager, sample_params):
        """Test updating preset"""
        manager.save_preset("test_preset", sample_params)
        manager.update_preset(
            "test_preset",
            description="Updated description"
        )
        info = manager.get_preset_info("test_preset")
        assert info["description"] == "Updated description"

    def test_find_presets_by_tag(self, manager, sample_params):
        """Test finding presets by tag"""
        manager.save_preset(
            "preset1",
            sample_params,
            tags=["strategy", "momentum"]
        )
        manager.save_preset(
            "preset2",
            sample_params,
            tags=["strategy", "mean_reversion"]
        )

        momentum_presets = manager.find_presets_by_tag("momentum")
        assert "preset1" in momentum_presets
        assert "preset2" not in momentum_presets


# ============================================================================
# TabbedControls Tests
# ============================================================================

class TestTabbedControls:
    """Test TabbedControls class"""

    @pytest.fixture
    def tabs(self):
        """Create TabbedControls instance"""
        return TabbedControls()

    def test_initialization(self, tabs):
        """Test tabs initialization"""
        assert tabs.tab_count == 0

    def test_add_tab(self, tabs):
        """Test adding tab"""
        from ipywidgets import HTML
        tabs.add_tab("Test", [HTML("Test content")])
        assert tabs.tab_count == 1
        assert "Test" in tabs.tab_names

    def test_remove_tab(self, tabs):
        """Test removing tab"""
        from ipywidgets import HTML
        tabs.add_tab("Test", [HTML("Test content")])
        tabs.remove_tab("Test")
        assert tabs.tab_count == 0

    def test_get_active_tab(self, tabs):
        """Test getting active tab"""
        from ipywidgets import HTML
        tabs.add_tab("Tab1", [HTML("Content 1")])
        tabs.add_tab("Tab2", [HTML("Content 2")])
        # First tab should be active by default
        active = tabs.get_active_tab()
        assert active in ["Tab1", "Tab2"]

    def test_set_active_tab(self, tabs):
        """Test setting active tab"""
        from ipywidgets import HTML
        tabs.add_tab("Tab1", [HTML("Content 1")])
        tabs.add_tab("Tab2", [HTML("Content 2")])
        tabs.set_active_tab("Tab2")
        assert tabs.get_active_tab() == "Tab2"


class TestAccordionControls:
    """Test AccordionControls class"""

    @pytest.fixture
    def accordion(self):
        """Create AccordionControls instance"""
        return AccordionControls()

    def test_initialization(self, accordion):
        """Test accordion initialization"""
        assert accordion.section_count == 0

    def test_add_section(self, accordion):
        """Test adding section"""
        from ipywidgets import HTML
        accordion.add_section("Test", [HTML("Test content")])
        assert accordion.section_count == 1

    def test_open_section(self, accordion):
        """Test opening section"""
        from ipywidgets import HTML
        accordion.add_section("Section1", [HTML("Content 1")])
        accordion.add_section("Section2", [HTML("Content 2")])
        accordion.open_section("Section2")
        assert accordion.get_open_section() == "Section2"


# ============================================================================
# QuickControlPanel Tests
# ============================================================================

class TestQuickControlPanel:
    """Test QuickControlPanel class"""

    @pytest.fixture
    def parameters(self):
        """Sample parameters configuration"""
        return {
            "param1": {
                "type": "slider",
                "min": 0,
                "max": 100,
                "initial": 50,
                "description": "Parameter 1"
            },
            "param2": {
                "type": "dropdown",
                "choices": ["A", "B", "C"],
                "initial": "B",
                "description": "Parameter 2"
            },
            "param3": {
                "type": "checkbox",
                "initial": True,
                "description": "Parameter 3"
            }
        }

    @pytest.fixture
    def panel(self, parameters):
        """Create QuickControlPanel instance"""
        return QuickControlPanel(parameters)

    def test_initialization(self, panel):
        """Test panel initialization"""
        assert len(panel.controls) == 3
        assert "param1" in panel.controls
        assert "param2" in panel.controls
        assert "param3" in panel.controls

    def test_get_values(self, panel):
        """Test getting parameter values"""
        values = panel.get_values()
        assert "param1" in values
        assert "param2" in values
        assert "param3" in values

    def test_set_values(self, panel):
        """Test setting parameter values"""
        panel.set_values({"param1": 75, "param2": "C", "param3": False})
        assert panel.controls["param1"].value == 75
        assert panel.controls["param2"].value == "C"
        assert panel.controls["param3"].value is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestControlsIntegration:
    """Integration tests for controls working together"""

    def test_panel_with_validation(self):
        """Test control panel with parameter validation"""
        panel = StrategyControlPanel(auto_refresh=False)

        # Add parameters
        panel.add_parameter_control(
            "rsi_period",
            "int_slider",
            options={"min": 2, "max": 50, "initial": 14}
        )

        panel.add_parameter_control(
            "symbol",
            "dropdown",
            options={"choices": ["AAPL", "MSFT", "GOOGL"], "initial": "AAPL"}
        )

        # Add validation
        panel.add_validation_rule(
            "rsi_period",
            lambda x: x >= 2,
            "RSI period must be at least 2"
        )

        # Get parameters
        params = panel.get_parameters()
        assert params["rsi_period"] == 14
        assert params["symbol"] == "AAPL"

    def test_panel_with_presets(self, tmp_path):
        """Test control panel with preset management"""
        panel = StrategyControlPanel(auto_refresh=False)

        # Add parameter
        panel.add_parameter_control(
            "test_param",
            "slider",
            options={"min": 0, "max": 100, "initial": 50}
        )

        # Save preset
        panel.save_preset("test", description="Test preset")

        # Load preset
        panel.set_parameter("test_param", 75)
        panel.load_preset("test")
        assert panel.get_parameter("test_param") == 50

    def test_symbol_selector_with_date_range(self):
        """Test symbol selector combined with date range picker"""
        symbols = ["AAPL", "MSFT", "GOOGL"]
        selector = SymbolSelector(symbols)
        picker = DateRangePicker()

        # Select symbols
        selector.set_selection(["AAPL", "MSFT"])
        assert len(selector.selected) == 2

        # Set date range
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        picker.set_date_range(start, end)
        assert picker.start_date == start
        assert picker.end_date == end


# ============================================================================
# Async Tests
# ============================================================================

@pytest.mark.asyncio
class TestAutoRefreshManager:
    """Test AutoRefreshManager with async"""

    @pytest.fixture
    def refresh_count(self):
        """Track refresh count"""
        return {"count": 0}

    @pytest.fixture
    def refresh_callback(self, refresh_count):
        """Create refresh callback"""
        def callback():
            refresh_count["count"] += 1
        return callback

    @pytest.fixture
    def manager(self, refresh_callback):
        """Create AutoRefreshManager instance"""
        return AutoRefreshManager(
            refresh_callback=refresh_callback,
            refresh_interval=0.5
        )

    async def test_start_stop(self, manager):
        """Test starting and stopping refresh"""
        assert not manager._enabled

        await manager.start()
        assert manager._enabled

        manager.stop()
        assert not manager._enabled

    async def test_trigger_refresh(self, manager, refresh_count):
        """Test triggering refresh"""
        await manager.start()

        # Trigger refresh
        manager.trigger_refresh()

        # Wait a bit for refresh to happen
        await asyncio.sleep(1)

        assert refresh_count["count"] > 0

        manager.stop()

    def test_get_stats(self, manager):
        """Test getting statistics"""
        stats = manager.get_stats()
        assert "enabled" in stats
        assert "refresh_count" in stats
        assert "error_count" in stats

    def test_set_interval(self, manager):
        """Test setting refresh interval"""
        manager.set_interval(2.0)
        assert manager.refresh_interval == 2.0

        with pytest.raises(ValueError):
            manager.set_interval(0.05)  # Too small
