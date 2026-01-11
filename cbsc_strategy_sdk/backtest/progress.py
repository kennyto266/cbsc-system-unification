"""
Progress tracking for backtest operations.

This module provides real-time progress tracking with callback support
and Jupyter widget integration.
"""

import time
from typing import Callable, List, Optional

from ..exceptions import StrategyWorkspaceError


class BacktestProgress:
    """Track backtest progress with callbacks and Jupyter widget support.

    This class provides a flexible progress tracking system that can:
    - Call registered callbacks on progress updates
    - Display progress in Jupyter notebooks with ipywidgets
    - Track progress percentage and step information

    Attributes:
        total_steps: Total number of steps in the backtest
        current_step: Current step number
        callbacks: List of registered callback functions

    Example:
        >>> progress = BacktestProgress(total_steps=100)
        >>>
        >>> # Add callback for logging
        >>> def log_progress(pct: float, msg: str):
        ...     print(f"Progress: {pct:.1f}% - {msg}")
        >>> progress.add_callback(log_progress)
        >>>
        >>> # Update progress
        >>> progress.update(50, "Processing data")
        >>> progress.update(100, "Complete")
    """

    def __init__(self, total_steps: int = 100) -> None:
        """Initialize progress tracker.

        Args:
            total_steps: Total number of steps for the backtest
        """
        if total_steps <= 0:
            raise ValueError("total_steps must be positive")

        self.total_steps: int = total_steps
        self.current_step: int = 0
        self._callbacks: List[Callable[[float, str], None]] = []
        self._start_time: Optional[float] = None
        self._last_update: Optional[float] = None

    @property
    def progress_percent(self) -> float:
        """Get current progress as percentage (0-100)."""
        if self.total_steps == 0:
            return 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100.0)

    @property
    def is_complete(self) -> bool:
        """Check if progress is complete."""
        return self.current_step >= self.total_steps

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time since first update."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def add_callback(self, callback: Callable[[float, str], None]) -> None:
        """Add a progress callback function.

        The callback will be called with two arguments:
        - progress_percent: Float from 0-100
        - message: Current step description

        Args:
            callback: Function to call on progress updates

        Example:
            >>> def my_callback(progress: float, message: str):
            ...     print(f"{progress:.1f}%: {message}")
            >>> progress.add_callback(my_callback)
        """
        if not callable(callback):
            raise TypeError("callback must be callable")

        self._callbacks.append(callback)

    def update(self, step: int, message: str = "") -> None:
        """Update progress and notify callbacks.

        Args:
            step: Current step number
            message: Optional message describing current step

        Raises:
            StrategyWorkspaceError: If step exceeds total_steps
        """
        if step < 0:
            raise StrategyWorkspaceError("Step cannot be negative")

        if step > self.total_steps:
            raise StrategyWorkspaceError(
                f"Step {step} exceeds total_steps {self.total_steps}",
                details={"step": step, "total_steps": self.total_steps},
            )

        # Initialize start time on first update
        if self._start_time is None:
            self._start_time = time.time()

        # Update current step
        self.current_step = step
        self._last_update = time.time()

        # Notify all callbacks
        progress_pct = self.progress_percent
        for callback in self._callbacks:
            try:
                callback(progress_pct, message)
            except Exception as e:
                # Log but don't raise to avoid breaking progress tracking
                print(f"Warning: Progress callback failed: {e}")

    def increment(self, delta: int = 1, message: str = "") -> None:
        """Increment progress by delta steps.

        Args:
            delta: Number of steps to increment (default 1)
            message: Optional message for this increment
        """
        self.update(self.current_step + delta, message)

    def reset(self) -> None:
        """Reset progress to zero."""
        self.current_step = 0
        self._start_time = None
        self._last_update = None

    def to_widget(self):
        """Create Jupyter progress bar widget.

        Returns:
            ipywidgets.Progress widget if ipywidgets is available
            None otherwise

        Example:
            >>> progress = BacktestProgress(total_steps=100)
            >>> widget = progress.to_widget()
            >>> display(widget)
            >>>
            >>> # Later updates will automatically update the widget
            >>> progress.update(50)
        """
        try:
            import ipywidgets as widgets

            bar = widgets.Progress(
                value=0,
                min=0,
                max=100,
                step=1,
                description='Progress:',
                bar_style='info',
            )

            def update_widget(progress_pct: float, message: str) -> None:
                bar.value = int(progress_pct)
                if message:
                    bar.description = message[:50]  # Truncate long messages

            # Register widget update callback
            self.add_callback(update_widget)

            return bar

        except ImportError:
            # ipywidgets not available
            return None

    def estimate_remaining(self) -> Optional[float]:
        """Estimate remaining time in seconds.

        Returns:
            Estimated seconds remaining, or None if cannot estimate

        Example:
            >>> progress.update(50)
            >>> print(f"ETA: {progress.estimate_remaining():.0f} seconds")
        """
        if self._start_time is None or self.progress_percent == 0:
            return None

        elapsed = self.elapsed_seconds
        progress_pct = self.progress_percent

        # Calculate remaining time based on current rate
        remaining_fraction = (100.0 - progress_pct) / 100.0
        total_estimated = elapsed / (progress_pct / 100.0)
        remaining = total_estimated - elapsed

        return max(0.0, remaining)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"BacktestProgress(step={self.current_step}/{self.total_steps}, "
            f"progress={self.progress_percent:.1f}%)"
        )


class ProgressCallback:
    """Helper class for creating progress callbacks.

    This class provides several common callback patterns for
    progress tracking.

    Example:
        >>> # Create a logging callback
        >>> logger = ProgressCallback.logger()
        >>> progress.add_callback(logger)
        >>>
        >>> # Create a callback that prints with timestamps
        >>> timed = ProgressCallback.timed_printer()
        >>> progress.add_callback(timed)
    """

    @staticmethod
    def logger(prefix: str = "Backtest") -> Callable[[float, str], None]:
        """Create a logging callback.

        Args:
            prefix: Prefix for log messages

        Returns:
            Callback function that logs progress
        """
        def callback(progress: float, message: str) -> None:
            print(f"[{prefix}] {progress:.1f}%: {message}")

        return callback

    @staticmethod
    def timed_printer() -> Callable[[float, str], None]:
        """Create a callback that prints progress with timestamps.

        Returns:
            Callback function with timestamp output
        """
        def callback(progress: float, message: str) -> None:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {progress:.1f}%: {message}")

        return callback

    @staticmethod
    def silent() -> Callable[[float, str], None]:
        """Create a silent callback (no output).

        Useful for suppressing progress output.

        Returns:
            No-op callback function
        """
        def callback(progress: float, message: str) -> None:
            pass

        return callback
