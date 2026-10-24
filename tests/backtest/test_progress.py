"""
Unit tests for BacktestProgress.

Tests progress tracking, callbacks, and widget integration.
"""

from unittest.mock import MagicMock, patch

import pytest

from cbsc_strategy_sdk.backtest.progress import BacktestProgress, ProgressCallback
from cbsc_strategy_sdk.exceptions import StrategyWorkspaceError


class TestBacktestProgress:
    """Test suite for BacktestProgress class."""

    def test_initialization(self):
        """Test progress initializes correctly."""
        progress = BacktestProgress(total_steps=100)

        assert progress.total_steps == 100
        assert progress.current_step == 0
        assert progress.progress_percent == 0.0
        assert progress.is_complete is False

    def test_initialization_invalid_steps(self):
        """Test initialization with invalid step count."""
        with pytest.raises(ValueError, match="must be positive"):
            BacktestProgress(total_steps=0)

        with pytest.raises(ValueError, match="must be positive"):
            BacktestProgress(total_steps=-10)

    def test_update_progress(self):
        """Test updating progress."""
        progress = BacktestProgress(total_steps=100)

        progress.update(50, "Halfway there")

        assert progress.current_step == 50
        assert progress.progress_percent == 50.0
        assert progress.is_complete is False

    def test_update_to_completion(self):
        """Test updating to completion."""
        progress = BacktestProgress(total_steps=100)

        progress.update(100, "Complete")

        assert progress.current_step == 100
        assert progress.progress_percent == 100.0
        assert progress.is_complete is True

    def test_update_invalid_step_negative(self):
        """Test updating with negative step."""
        progress = BacktestProgress(total_steps=100)

        with pytest.raises(StrategyWorkspaceError, match="cannot be negative"):
            progress.update(-10)

    def test_update_invalid_step_exceeds_total(self):
        """Test updating with step exceeding total."""
        progress = BacktestProgress(total_steps=100)

        with pytest.raises(StrategyWorkspaceError, match="exceeds total_steps"):
            progress.update(150)

    def test_increment(self):
        """Test incrementing progress."""
        progress = BacktestProgress(total_steps=100)

        progress.increment(10, "Processing batch 1")
        assert progress.current_step == 10

        progress.increment(20, "Processing batch 2")
        assert progress.current_step == 30

        # Default increment by 1
        progress.increment()
        assert progress.current_step == 31

    def test_reset(self):
        """Test resetting progress."""
        progress = BacktestProgress(total_steps=100)

        progress.update(50)
        progress.reset()

        assert progress.current_step == 0
        assert progress.progress_percent == 0.0
        assert progress.is_complete is False

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        progress = BacktestProgress(total_steps=100)

        # Before any updates
        assert progress.elapsed_seconds == 0.0

        # After first update (time starts)
        progress.update(50)
        elapsed = progress.elapsed_seconds
        assert elapsed >= 0.0

    def test_estimate_remaining(self):
        """Test remaining time estimation."""
        progress = BacktestProgress(total_steps=100)

        # Before any updates, cannot estimate
        assert progress.estimate_remaining() is None

        # At 0% progress, cannot estimate
        progress.update(0)
        assert progress.estimate_remaining() is None

        # At 50% progress, can estimate
        progress.update(50)
        remaining = progress.estimate_remaining()
        assert remaining is not None
        assert remaining >= 0.0

    def test_callbacks(self):
        """Test progress callbacks."""
        progress = BacktestProgress(total_steps=100)

        callback_values = []

        def my_callback(progress_pct: float, message: str) -> None:
            callback_values.append((progress_pct, message))

        progress.add_callback(my_callback)

        # Update should trigger callback
        progress.update(25, "Quarter done")

        assert len(callback_values) == 1
        assert callback_values[0] == (25.0, "Quarter done")

    def test_multiple_callbacks(self):
        """Test multiple callbacks."""
        progress = BacktestProgress(total_steps=100)

        callback1_called = []
        callback2_called = []

        def callback1(pct: float, msg: str) -> None:
            callback1_called.append(True)

        def callback2(pct: float, msg: str) -> None:
            callback2_called.append(True)

        progress.add_callback(callback1)
        progress.add_callback(callback2)

        progress.update(50)

        assert len(callback1_called) == 1
        assert len(callback2_called) == 1

    def test_callback_failure_handling(self):
        """Test that callback failures don't break progress tracking."""
        progress = BacktestProgress(total_steps=100)

        def failing_callback(pct: float, msg: str) -> None:
            raise ValueError("Callback failed!")

        progress.add_callback(failing_callback)

        # Should not raise exception
        progress.update(50)

        assert progress.current_step == 50

    def test_invalid_callback(self):
        """Test adding non-callable callback."""
        progress = BacktestProgress(total_steps=100)

        with pytest.raises(TypeError, match="must be callable"):
            progress.add_callback("not a function")

    def test_to_widget(self):
        """Test Jupyter widget creation."""
        progress = BacktestProgress(total_steps=100)

        widget = progress.to_widget()

        if widget is not None:
            # ipywidgets available
            assert hasattr(widget, "value")
            assert widget.value == 0

            # Update should change widget
            progress.update(50)
            assert widget.value == 50
        else:
            # ipywidgets not available
            assert widget is None

    def test_widget_integration(self):
        """Test widget receives updates."""
        progress = BacktestProgress(total_steps=100)

        widget = progress.to_widget()

        if widget is not None:
            # Add widget callback implicitly through to_widget()
            progress.update(25, "First step")
            progress.update(50, "Second step")
            progress.update(75, "Third step")
            progress.update(100, "Complete")

            assert widget.value == 100

    def test_repr(self):
        """Test string representation."""
        progress = BacktestProgress(total_steps=100)
        progress.update(25)

        repr_str = repr(progress)

        assert "BacktestProgress" in repr_str
        assert "25/100" in repr_str
        assert "25.0%" in repr_str


class TestProgressCallback:
    """Test suite for ProgressCallback helpers."""

    def test_logger_callback(self, capsys):
        """Test logger callback creation."""
        callback = ProgressCallback.logger(prefix="Test")

        callback(50.0, "Halfway")

        captured = capsys.readouterr()
        assert "[Test]" in captured.out
        assert "50.0%" in captured.out
        assert "Halfway" in captured.out

    def test_timed_printer_callback(self, capsys):
        """Test timed printer callback."""
        callback = ProgressCallback.timed_printer()

        callback(75.0, "Almost done")

        captured = capsys.readouterr()
        # Should contain timestamp
        assert "[" in captured.out
        assert "75.0%" in captured.out
        assert "Almost done" in captured.out

    def test_silent_callback(self, capsys):
        """Test silent callback produces no output."""
        callback = ProgressCallback.silent()

        callback(100.0, "Complete")

        captured = capsys.readouterr()
        assert captured.out == ""
