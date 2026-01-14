"""
Date Range Picker Module

Provides interactive date range selection widget with preset options
for easy time period selection.
"""

from typing import Optional, List, Callable, Tuple
from datetime import datetime, timedelta
import ipywidgets as widgets
from IPython.display import display


class DateRangePicker:
    """Date range picker widget with preset options"""

    # Preset time periods
    PRESETS = {
        '1D': ('1 Day', lambda: (datetime.now() - timedelta(days=1), datetime.now())),
        '3D': ('3 Days', lambda: (datetime.now() - timedelta(days=3), datetime.now())),
        '1W': ('1 Week', lambda: (datetime.now() - timedelta(weeks=1), datetime.now())),
        '2W': ('2 Weeks', lambda: (datetime.now() - timedelta(weeks=2), datetime.now())),
        '1M': ('1 Month', lambda: (datetime.now() - timedelta(days=30), datetime.now())),
        '3M': ('3 Months', lambda: (datetime.now() - timedelta(days=90), datetime.now())),
        '6M': ('6 Months', lambda: (datetime.now() - timedelta(days=180), datetime.now())),
        'YTD': ('Year to Date', lambda: (
            datetime(datetime.now().year, 1, 1),
            datetime.now()
        )),
        '1Y': ('1 Year', lambda: (datetime.now() - timedelta(days=365), datetime.now())),
        'MAX': ('Maximum', lambda: (datetime(2020, 1, 1), datetime.now())),
        'CUSTOM': ('Custom', None),
    }

    def __init__(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        presets: Optional[List[str]] = None,
        callback: Optional[Callable] = None
    ):
        """
        Initialize date range picker

        Args:
            start_date: Initial start date
            end_date: Initial end date
            presets: List of preset keys to include (default: common presets)
            callback: Optional callback when date range changes
        """
        self._callbacks: List[Callable] = []
        self._custom_mode = False

        # Set default date range (1 month)
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        self.start_date = start_date
        self.end_date = end_date

        # Configure presets
        if presets is None:
            presets = ['1W', '2W', '1M', '3M', '6M', 'YTD', '1Y', 'CUSTOM']
        self.presets = [p for p in presets if p in self.PRESETS]

        self._build_widget()

        if callback:
            self.on_change(callback)

    def _build_widget(self):
        """Build date range picker UI"""
        # Preset buttons
        preset_buttons = []
        for preset_key in self.presets:
            label, _ = self.PRESETS[preset_key]
            btn = widgets.Button(
                description=label,
                layout=widgets.Layout(width='auto', padding='2px')
            )
            btn.on_click(lambda b, key=preset_key: self._on_preset_click(key))
            preset_buttons.append(btn)

        self.preset_buttons_box = widgets.HBox(
            preset_buttons,
            layout=widgets.Layout(
                flex_flow='row wrap',
                width='100%'
            )
        )

        # Date pickers
        self.start_picker = widgets.DatePicker(
            description='Start Date:',
            value=self.start_date.date(),
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='45%')
        )

        self.end_picker = widgets.DatePicker(
            description='End Date:',
            value=self.end_date.date(),
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='45%')
        )

        # Date display
        self.date_display = widgets.HTML(
            value=self._format_date_display(),
            layout=widgets.Layout(width='100%')
        )

        # Info label
        self.info_label = widgets.HTML(
            value=self._calculate_info(),
            layout=widgets.Layout(width='100%')
        )

        # Wire up events
        self.start_picker.observe(self._on_date_change, names='value')
        self.end_picker.observe(self._on_date_change, names='value')

        # Main layout
        self.widget = widgets.VBox([
            widgets.HTML('<h4>Date Range Selector</h4>'),
            widgets.HTML('<b>Quick Select:</b>'),
            self.preset_buttons_box,
            widgets.HTML('<br>'),
            widgets.HTML('<b>Custom Range:</b>'),
            widgets.HBox([self.start_picker, self.end_picker]),
            widgets.HTML('<br>'),
            self.date_display,
            self.info_label
        ])

    def _on_preset_click(self, preset_key: str):
        """Handle preset button click"""
        _, func = self.PRESETS[preset_key]

        if preset_key == 'CUSTOM':
            # Enable custom mode, don't change dates
            self._custom_mode = True
        elif func is not None:
            # Apply preset
            self._custom_mode = False
            start, end = func()
            self.start_date = start
            self.end_date = end
            self.start_picker.value = start.date()
            self.end_picker.value = end.date()

        self._update_display()
        self._notify_callbacks()

    def _on_date_change(self, change):
        """Handle date picker change"""
        start = self.start_picker.value
        end = self.end_picker.value

        if start and end:
            # Combine date with time
            self.start_date = datetime.combine(start, datetime.min.time())
            self.end_date = datetime.combine(end, datetime.max.time())
            self._custom_mode = True

            # Validate end >= start
            if self.end_date < self.start_date:
                self.end_date = self.start_date
                self.end_picker.value = self.start_picker.value

            self._update_display()
            self._notify_callbacks()

    def _update_display(self):
        """Update display widgets"""
        self.date_display.value = self._format_date_display()
        self.info_label.value = self._calculate_info()

    def _format_date_display(self) -> str:
        """Format date range for display"""
        start_str = self.start_date.strftime('%Y-%m-%d')
        end_str = self.end_date.strftime('%Y-%m-%d')

        return (
            f'<div style="font-size: 14px; padding: 8px; background: #f0f0f0; '
            f'border-radius: 4px; text-align: center;">'
            f'<b>Selected Range:</b> {start_str} to {end_str}'
            f'</div>'
        )

    def _calculate_info(self) -> str:
        """Calculate and display range info"""
        delta = self.end_date - self.start_date
        days = delta.days + 1

        # Calculate trading days (roughly 5/7 of calendar days)
        trading_days = int(days * 5 / 7)

        return (
            f'<div style="font-size: 12px; color: #666; text-align: center;">'
            f'Duration: {days} calendar days (~{trading_days} trading days)'
            f'</div>'
        )

    def _notify_callbacks(self):
        """Notify all registered callbacks"""
        for callback in self._callbacks:
            callback(self.start_date, self.end_date)

    def on_change(self, callback: Callable[[datetime, datetime], None]):
        """
        Register callback for date range changes

        Args:
            callback: Function to call when range changes
                     Receives (start_date, end_date)
        """
        self._callbacks.append(callback)

    @property
    def date_range(self) -> Tuple[datetime, datetime]:
        """Get current date range as tuple"""
        return self.start_date, self.end_date

    def set_date_range(self, start: datetime, end: datetime):
        """
        Programmatically set date range

        Args:
            start: Start date
            end: End date
        """
        if start > end:
            raise ValueError("Start date must be before end date")

        self.start_date = start
        self.end_date = end
        self.start_picker.value = start.date()
        self.end_picker.value = end.date()
        self._custom_mode = True
        self._update_display()

    def add_preset(self, key: str, label: str, days: int):
        """
        Add custom preset

        Args:
            key: Preset key identifier
            label: Display label
            days: Number of days from now
        """
        func = lambda: (datetime.now() - timedelta(days=days), datetime.now())
        self.PRESETS[key] = (label, func)

        # Rebuild widget to include new preset
        if key not in self.presets:
            self.presets.append(key)
            self._build_widget()

    def display(self):
        """Display the widget"""
        display(self.widget)

    def __repr__(self) -> str:
        """String representation"""
        return f"DateRangePicker({self.start_date.date()} to {self.end_date.date()})"


class QuickDateRangePicker:
    """Simplified date range picker with dropdown presets"""

    def __init__(
        self,
        presets: Optional[List[str]] = None,
        callback: Optional[Callable] = None
    ):
        """
        Initialize quick date range picker

        Args:
            presets: List of preset keys
            callback: Optional change callback
        """
        if presets is None:
            presets = ['1W', '1M', '3M', '6M', 'YTD', '1Y']

        self.presets = {k: v for k, v in DateRangePicker.PRESETS.items() if k in presets}
        self._callbacks: List[Callable] = []

        # Preset dropdown
        self.preset_dropdown = widgets.Dropdown(
            options=[label for _, label in self.presets.values()],
            description='Range:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='95%')
        )

        # Apply initial preset
        initial_key = list(self.presets.keys())[0]
        _, func = self.presets[initial_key]
        if func:
            self.start_date, self.end_date = func()

        # Wire up events
        self.preset_dropdown.observe(self._on_change, names='value')

        # Build widget
        self.widget = widgets.VBox([
            widgets.HTML('<h4>Date Range</h4>'),
            self.preset_dropdown
        ])

        if callback:
            self.on_change(callback)

    def _on_change(self, change):
        """Handle dropdown change"""
        label = change['new']

        # Find the preset key for this label
        for key, (l, func) in self.presets.items():
            if l == label and func:
                self.start_date, self.end_date = func()
                self._notify_callbacks()
                break

    def _notify_callbacks(self):
        """Notify callbacks"""
        for callback in self._callbacks:
            callback(self.start_date, self.end_date)

    def on_change(self, callback: Callable[[datetime, datetime], None]):
        """Register change callback"""
        self._callbacks.append(callback)

    @property
    def date_range(self) -> Tuple[datetime, datetime]:
        """Get current date range"""
        return self.start_date, self.end_date

    def display(self):
        """Display the widget"""
        display(self.widget)

    def __repr__(self) -> str:
        """String representation"""
        return f"QuickDateRangePicker({self.preset_dropdown.value})"
