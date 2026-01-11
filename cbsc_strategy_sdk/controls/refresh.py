"""
Auto-Refresh Module

Provides automatic data refresh functionality for strategy controls.
"""

import asyncio
from typing import Optional, Callable, Dict, Any
import ipywidgets as widgets
from datetime import datetime


class AutoRefreshManager:
    """Manage auto-refresh for strategy controls"""

    def __init__(
        self,
        refresh_callback: Callable,
        refresh_interval: float = 1.0,
        debounce_interval: float = 0.5
    ):
        """
        Initialize auto-refresh manager

        Args:
            refresh_callback: Function to call for refresh
            refresh_interval: Minimum time between refreshes (seconds)
            debounce_interval: Delay after parameter change before refresh (seconds)
        """
        self.refresh_callback = refresh_callback
        self.refresh_interval = refresh_interval
        self.debounce_interval = debounce_interval

        self._enabled = False
        self._refresh_task: Optional[asyncio.Task] = None
        self._last_refresh: Optional[datetime] = None
        self._pending_refresh = False
        self._debounce_task: Optional[asyncio.Task] = None

        # Statistics
        self._refresh_count = 0
        self._error_count = 0
        self._last_error: Optional[str] = None

        # Status display
        self.status_label = widgets.HTML(
            value='<span style="color: #666;">Auto-refresh: OFF</span>',
            layout=widgets.Layout(width='auto')
        )

        self.control_widget = self._build_control_widget()

    def _build_control_widget(self) -> widgets.HBox:
        """Build control widget for auto-refresh"""
        # Enable/disable toggle
        self.enable_checkbox = widgets.Checkbox(
            value=False,
            description='Auto-refresh',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='auto')
        )

        # Interval slider
        self.interval_slider = widgets.FloatSlider(
            value=self.refresh_interval,
            min=0.1,
            max=10.0,
            step=0.1,
            description='Interval (s):',
            continuous_update=False,
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='200px')
        )

        # Manual refresh button
        self.refresh_button = widgets.Button(
            description='Refresh Now',
            icon='refresh',
            button_style='info',
            layout=widgets.Layout(width='auto')
        )

        # Statistics display
        self.stats_label = widgets.HTML(
            value='<span style="color: #666; font-size: 11px;">Refreshes: 0 | Errors: 0</span>',
            layout=widgets.Layout(width='auto')
        )

        # Wire up events
        self.enable_checkbox.observe(self._on_toggle, names='value')
        self.interval_slider.observe(self._on_interval_change, names='value')
        self.refresh_button.on_click(self._on_manual_refresh)

        return widgets.HBox([
            self.status_label,
            self.enable_checkbox,
            self.interval_slider,
            self.refresh_button,
            self.stats_label
        ])

    def _on_toggle(self, change):
        """Handle enable/disable toggle"""
        if change['new']:
            self.start()
        else:
            self.stop()

    def _on_interval_change(self, change):
        """Handle interval slider change"""
        self.refresh_interval = change['new']
        if self._enabled:
            self.status_label.value = (
                f'<span style="color: green;">Auto-refresh: ON ({self.refresh_interval}s)</span>'
            )

    def _on_manual_refresh(self, button):
        """Handle manual refresh button"""
        asyncio.create_task(self._do_refresh())

    async def start(self):
        """Start auto-refresh loop"""
        if self._enabled:
            return

        self._enabled = True
        self.enable_checkbox.value = True
        self.status_label.value = (
            f'<span style="color: green;">Auto-refresh: ON ({self.refresh_interval}s)</span>'
        )

        # Start refresh loop
        self._refresh_task = asyncio.create_task(self._refresh_loop())

    def stop(self):
        """Stop auto-refresh loop"""
        if not self._enabled:
            return

        self._enabled = False
        self.enable_checkbox.value = False
        self.status_label.value = '<span style="color: #666;">Auto-refresh: OFF</span>'

        # Cancel tasks
        if self._refresh_task:
            self._refresh_task.cancel()
            self._refresh_task = None

        if self._debounce_task:
            self._debounce_task.cancel()
            self._debounce_task = None

    def set_interval(self, interval: float):
        """
        Change refresh interval

        Args:
            interval: New interval in seconds
        """
        if interval < 0.1:
            raise ValueError("Interval must be at least 0.1 seconds")

        self.refresh_interval = interval
        self.interval_slider.value = interval

    async def _refresh_loop(self):
        """Background refresh loop"""
        try:
            while self._enabled:
                # Check if we need to refresh
                if self._pending_refresh:
                    await self._do_refresh()

                # Wait for next interval
                await asyncio.sleep(self.refresh_interval)

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass

    async def _do_refresh(self):
        """Perform actual refresh"""
        self._pending_refresh = False

        # Check minimum interval
        if self._last_refresh:
            elapsed = (datetime.now() - self._last_refresh).total_seconds()
            if elapsed < self.refresh_interval:
                return

        try:
            # Call refresh callback
            if asyncio.iscoroutinefunction(self.refresh_callback):
                await self.refresh_callback()
            else:
                self.refresh_callback()

            self._last_refresh = datetime.now()
            self._refresh_count += 1
            self._update_stats()

        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            self._update_stats()
            self.status_label.value = (
                f'<span style="color: red;">Auto-refresh error: {str(e)[:50]}</span>'
            )

    def _update_stats(self):
        """Update statistics display"""
        self.stats_label.value = (
            f'<span style="color: #666; font-size: 11px;">'
            f'Refreshes: {self._refresh_count} | Errors: {self._error_count}'
            f'</span>'
        )

    async def _on_parameter_change(self, change):
        """Handle parameter change event"""
        if self._enabled:
            self._pending_refresh = True

            # Cancel existing debounce task
            if self._debounce_task:
                self._debounce_task.cancel()

            # Start new debounce task
            self._debounce_task = asyncio.create_task(
                self._debounce_refresh()
            )

    async def _debounce_refresh(self):
        """Wait for debounce interval before allowing refresh"""
        try:
            await asyncio.sleep(self.debounce_interval)
            # Refresh will happen on next loop iteration
        except asyncio.CancelledError:
            # Debounce was cancelled (new parameter change)
            pass

    def trigger_refresh(self):
        """Manually trigger a refresh (from outside)"""
        if self._enabled:
            self._pending_refresh = True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get refresh statistics

        Returns:
            Dictionary with stats
        """
        return {
            'enabled': self._enabled,
            'refresh_count': self._refresh_count,
            'error_count': self._error_count,
            'last_error': self._last_error,
            'last_refresh': self._last_refresh.isoformat() if self._last_refresh else None,
            'refresh_interval': self.refresh_interval
        }

    def reset_stats(self):
        """Reset refresh statistics"""
        self._refresh_count = 0
        self._error_count = 0
        self._last_error = None
        self._last_refresh = None
        self._update_stats()

    @property
    def widget(self) -> widgets.HBox:
        """Get control widget for display"""
        return self.control_widget

    def __repr__(self) -> str:
        """String representation"""
        status = "ON" if self._enabled else "OFF"
        return f"AutoRefreshManager({status}, interval={self.refresh_interval}s)"


class SimpleRefreshManager:
    """Simplified refresh manager without async complexity"""

    def __init__(
        self,
        refresh_callback: Callable,
        debounce_interval: float = 0.5
    ):
        """
        Initialize simple refresh manager

        Args:
            refresh_callback: Function to call for refresh
            debounce_interval: Delay before refresh after change
        """
        self.refresh_callback = refresh_callback
        self.debounce_interval = debounce_interval
        self._callbacks = []

        # Manual refresh button
        self.refresh_button = widgets.Button(
            description='Refresh',
            icon='refresh',
            button_style='info',
            layout=widgets.Layout(width='auto')
        )

        # Status display
        self.status_label = widgets.HTML(
            value='<span style="color: #666;">Ready</span>',
            layout=widgets.Layout(width='auto')
        )

        # Wire up events
        self.refresh_button.on_click(self._on_refresh)

    def _on_refresh(self, button):
        """Handle refresh button click"""
        try:
            self.refresh_callback()
            self.status_label.value = '<span style="color: green;">✓ Refreshed</span>'
        except Exception as e:
            self.status_label.value = f'<span style="color: red;">Error: {e}</span>'

    def observe_parameter(self, widget: widgets.Widget):
        """
        Observe widget for changes and trigger refresh

        Args:
            widget: Widget to observe
        """
        def on_change(change):
            self.status_label.value = '<span style="color: orange;">Refreshing...</span>'
            try:
                self.refresh_callback()
                self.status_label.value = '<span style="color: green;">✓ Refreshed</span>'
            except Exception as e:
                self.status_label.value = f'<span style="color: red;">Error: {e}</span>'

        widget.observe(on_change, names='value')
        self._callbacks.append((widget, on_change))

    @property
    def widget(self) -> widgets.HBox:
        """Get control widget"""
        return widgets.HBox([
            self.status_label,
            self.refresh_button
        ])

    def __repr__(self) -> str:
        """String representation"""
        return f"SimpleRefreshManager(callbacks={len(self._callbacks)})"
