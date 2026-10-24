"""
Symbol Selector Module

Provides interactive symbol selection widget with search functionality
for trading symbols.
"""

from typing import List, Callable, Optional, Set
import ipywidgets as widgets
from IPython.display import display


class SymbolSelector:
    """Widget for selecting trading symbols with search functionality"""

    def __init__(
        self,
        available_symbols: List[str],
        max_selections: int = 10,
        placeholder: str = "Search symbols..."
    ):
        """
        Initialize symbol selector

        Args:
            available_symbols: List of available symbols
            max_selections: Maximum number of symbols that can be selected
            placeholder: Placeholder text for search box
        """
        self.available_symbols = sorted(set(available_symbols))
        self.max_selections = max_selections
        self.selected_symbols: Set[str] = set()
        self._callbacks: List[Callable] = []

        self._build_widget(placeholder)

    def _build_widget(self, placeholder: str):
        """Build selection UI with search"""
        # Search box
        self.search_box = widgets.Text(
            value='',
            placeholder=placeholder,
            description='Search:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='50%')
        )

        # Available symbols dropdown
        self.available_dropdown = widgets.Select(
            options=self.available_symbols,
            rows=10,
            description='Available:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='45%', height='200px')
        )

        # Selected symbols listbox
        self.selected_listbox = widgets.Select(
            options=[],
            rows=10,
            description='Selected:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='45%', height='200px')
        )

        # Control buttons
        self.add_button = widgets.Button(
            description='Add →',
            button_style='primary',
            layout=widgets.Layout(width='100px')
        )

        self.remove_button = widgets.Button(
            description='← Remove',
            button_style='warning',
            layout=widgets.Layout(width='100px')
        )

        self.add_all_button = widgets.Button(
            description='Add All →',
            layout=widgets.Layout(width='100px')
        )

        self.remove_all_button = widgets.Button(
            description='← Remove All',
            button_style='danger',
            layout=widgets.Layout(width='100px')
        )

        # Info label
        self.info_label = widgets.HTML(
            value=f'<span style="color: #666;">Selected: 0/{self.max_selections}</span>',
            layout=widgets.Layout(width='auto')
        )

        # Button layout
        button_box = widgets.VBox([
            widgets.HTML('<br>'),
            self.add_button,
            self.add_all_button,
            self.remove_button,
            self.remove_all_button
        ])

        # Symbol layout
        symbol_layout = widgets.HBox([
            widgets.VBox([self.available_dropdown]),
            button_box,
            widgets.VBox([self.selected_listbox])
        ])

        # Main layout
        self.widget = widgets.VBox([
            widgets.HTML('<h4>Symbol Selector</h4>'),
            self.search_box,
            self.info_label,
            symbol_layout
        ])

        # Wire up events
        self.search_box.observe(self._on_search, names='value')
        self.add_button.on_click(self._on_add)
        self.add_all_button.on_click(self._on_add_all)
        self.remove_button.on_click(self._on_remove)
        self.remove_all_button.on_click(self._on_remove_all)

    def _on_search(self, change):
        """Handle search box changes"""
        search_term = change['new'].upper()

        if not search_term:
            self.available_dropdown.options = self.available_symbols
        else:
            filtered = [
                s for s in self.available_symbols
                if search_term in s.upper()
            ]
            self.available_dropdown.options = filtered

    def _on_add(self, button):
        """Add selected symbol"""
        if self.available_dropdown.value:
            symbol = self.available_dropdown.value

            if len(self.selected_symbols) >= self.max_selections:
                self.info_label.value = (
                    f'<span style="color: red; font-weight: bold;">'
                    f'Maximum {self.max_selections} symbols allowed'
                    f'</span>'
                )
                return

            self.selected_symbols.add(symbol)
            self._update_selected_display()
            self._notify_callbacks()

    def _on_add_all(self, button):
        """Add all visible symbols"""
        available = list(self.available_dropdown.options)

        for symbol in available:
            if len(self.selected_symbols) >= self.max_selections:
                break
            self.selected_symbols.add(symbol)

        self._update_selected_display()
        self._notify_callbacks()

    def _on_remove(self, button):
        """Remove selected symbol"""
        if self.selected_listbox.value:
            symbol = self.selected_listbox.value
            self.selected_symbols.discard(symbol)
            self._update_selected_display()
            self._notify_callbacks()

    def _on_remove_all(self, button):
        """Remove all symbols"""
        self.selected_symbols.clear()
        self._update_selected_display()
        self._notify_callbacks()

    def _update_selected_display(self):
        """Update selected symbols display"""
        selected_list = sorted(self.selected_symbols)
        self.selected_listbox.options = selected_list

        count = len(self.selected_symbols)
        if count >= self.max_selections:
            self.info_label.value = (
                f'<span style="color: red; font-weight: bold;">'
                f'Selected: {count}/{self.max_selections} (maximum reached)'
                f'</span>'
            )
        else:
            self.info_label.value = (
                f'<span style="color: #666;">Selected: {count}/{self.max_selections}</span>'
            )

    def _notify_callbacks(self):
        """Notify all registered callbacks"""
        for callback in self._callbacks:
            callback(self.selected_symbols.copy())

    def on_selection_change(self, callback: Callable[[Set[str]], None]):
        """
        Register callback for selection changes

        Args:
            callback: Function to call when selection changes
                     Receives set of selected symbols
        """
        self._callbacks.append(callback)

    @property
    def selected(self) -> List[str]:
        """Get currently selected symbols as list"""
        return sorted(self.selected_symbols)

    def set_selection(self, symbols: List[str]):
        """
        Programmatically set selected symbols

        Args:
            symbols: List of symbols to select
        """
        valid_symbols = set(symbols) & set(self.available_symbols)

        if len(valid_symbols) > self.max_selections:
            valid_symbols = set(list(valid_symbols)[:self.max_selections])

        self.selected_symbols = valid_symbols
        self._update_selected_display()

    def clear_selection(self):
        """Clear all selected symbols"""
        self.selected_symbols.clear()
        self._update_selected_display()

    def update_available_symbols(self, symbols: List[str]):
        """
        Update available symbols list

        Args:
            symbols: New list of available symbols
        """
        self.available_symbols = sorted(set(symbols))
        self.search_box.value = ''  # Reset search
        self.available_dropdown.options = self.available_symbols

        # Remove any selected symbols that are no longer available
        self.selected_symbols &= set(self.available_symbols)
        self._update_selected_display()

    def display(self):
        """Display the widget"""
        display(self.widget)

    def __repr__(self) -> str:
        """String representation"""
        return f"SymbolSelector(available={len(self.available_symbols)}, selected={len(self.selected_symbols)})"


class QuickSymbolSelector:
    """Simplified symbol selector for quick single/multiple selection"""

    def __init__(
        self,
        available_symbols: List[str],
        description: str = "Symbols:",
        multi: bool = True
    ):
        """
        Initialize quick symbol selector

        Args:
            available_symbols: List of available symbols
            description: Widget description
            multi: Allow multiple selection
        """
        self.available_symbols = sorted(set(available_symbols))

        if multi:
            self.widget = widgets.SelectMultiple(
                options=self.available_symbols,
                description=description,
                rows=8,
                style={'description_width': 'initial'},
                layout=widgets.Layout(width='95%', height='200px')
            )
        else:
            self.widget = widgets.Dropdown(
                options=self.available_symbols,
                description=description,
                style={'description_width': 'initial'},
                layout=widgets.Layout(width='95%')
            )

    @property
    def selected(self) -> List[str]:
        """Get selected symbols"""
        value = self.widget.value
        if isinstance(value, tuple):
            return list(value)
        return [value] if value else []

    def set_selection(self, symbols: List[str]):
        """Set selected symbols"""
        if isinstance(self.widget, widgets.SelectMultiple):
            valid = [s for s in symbols if s in self.available_symbols]
            self.widget.value = tuple(valid)
        elif isinstance(self.widget, widgets.Dropdown):
            if symbols and symbols[0] in self.available_symbols:
                self.widget.value = symbols[0]

    def display(self):
        """Display the widget"""
        display(self.widget)

    def __repr__(self) -> str:
        """String representation"""
        return f"QuickSymbolSelector(selected={len(self.selected)})"
