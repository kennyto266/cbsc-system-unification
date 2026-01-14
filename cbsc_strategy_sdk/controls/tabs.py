"""
Tabbed Controls Module

Provides tabbed interface for organizing control widgets.
"""

from typing import List, Dict, Optional, Any
import ipywidgets as widgets
from IPython.display import display


class TabbedControls:
    """Organize controls in tabbed interface"""

    def __init__(self, titles: Optional[List[str]] = None):
        """
        Initialize tabbed controls

        Args:
            titles: Optional list of tab titles to pre-create
        """
        self.tabs: Dict[str, widgets.VBox] = {}
        self.tab_indices: Dict[str, int] = {}

        self.tab_widget = widgets.Tab()
        self.tab_widget.layout = widgets.Layout(width='100%', height='auto')

        if titles:
            for title in titles:
                self.add_tab(title, [])

        # Wire up tab change observation
        self.tab_widget.observe(self._on_tab_change, names='selected_index')

    def _on_tab_change(self, change):
        """Handle tab change event"""
        # Can be used for lazy loading or other actions
        pass

    def add_tab(
        self,
        name: str,
        controls: List[widgets.Widget],
        title: Optional[str] = None
    ):
        """
        Add a tab with controls

        Args:
            name: Internal name for the tab
            controls: List of widgets to include in tab
            title: Display title (defaults to name)
        """
        if name in self.tabs:
            raise ValueError(f"Tab '{name}' already exists")

        # Create VBox for tab content
        tab_content = widgets.VBox(
            controls,
            layout=widgets.Layout(
                padding='10px',
                overflow_y='auto'
            )
        )

        # Add to tabs
        current_children = list(self.tab_widget.children)
        current_children.append(tab_content)
        self.tab_widget.children = tuple(current_children)

        # Set title
        index = len(current_children) - 1
        display_title = title or name
        self.tab_widget.set_title(index, display_title)

        # Store references
        self.tabs[name] = tab_content
        self.tab_indices[name] = index

    def remove_tab(self, name: str):
        """
        Remove a tab

        Args:
            name: Tab name to remove
        """
        if name not in self.tabs:
            raise ValueError(f"Tab '{name}' does not exist")

        # Get current children
        children_list = list(self.tab_widget.children)
        index = self.tab_indices[name]

        # Remove tab
        children_list.pop(index)
        self.tab_widget.children = tuple(children_list)

        # Update indices
        del self.tabs[name]
        del self.tab_indices[name]

        # Rebuild indices
        for i, tab_name in enumerate(self.tabs.keys()):
            self.tab_indices[tab_name] = i

    def add_control(self, tab_name: str, control: widgets.Widget):
        """
        Add a control to existing tab

        Args:
            tab_name: Tab to add control to
            control: Widget to add
        """
        if tab_name not in self.tabs:
            raise ValueError(f"Tab '{tab_name}' does not exist")

        tab_content = self.tabs[tab_name]
        children_list = list(tab_content.children)
        children_list.append(control)
        tab_content.children = tuple(children_list)

    def remove_control(self, tab_name: str, control: widgets.Widget):
        """
        Remove control from tab

        Args:
            tab_name: Tab to remove control from
            control: Widget to remove
        """
        if tab_name not in self.tabs:
            raise ValueError(f"Tab '{tab_name}' does not exist")

        tab_content = self.tabs[tab_name]
        children_list = list(tab_content.children)

        if control in children_list:
            children_list.remove(control)
            tab_content.children = tuple(children_list)

    def get_active_tab(self) -> str:
        """
        Get currently active tab name

        Returns:
            Tab name or empty string if no tabs
        """
        if not self.tabs:
            return ""

        index = self.tab_widget.selected_index
        for name, tab_index in self.tab_indices.items():
            if tab_index == index:
                return name
        return ""

    def set_active_tab(self, name: str):
        """
        Set active tab

        Args:
            name: Tab name to activate
        """
        if name not in self.tabs:
            raise ValueError(f"Tab '{name}' does not exist")

        self.tab_widget.selected_index = self.tab_indices[name]

    def get_tab_controls(self, name: str) -> List[widgets.Widget]:
        """
        Get controls in a tab

        Args:
            name: Tab name

        Returns:
            List of widgets in the tab
        """
        if name not in self.tabs:
            raise ValueError(f"Tab '{name}' does not exist")

        return list(self.tabs[name].children)

    def clear_tab(self, name: str):
        """
        Clear all controls from a tab

        Args:
            name: Tab name
        """
        if name not in self.tabs:
            raise ValueError(f"Tab '{name}' does not exist")

        self.tabs[name].children = tuple()

    def rename_tab(self, name: str, new_title: str):
        """
        Rename a tab

        Args:
            name: Current tab name
            new_title: New display title
        """
        if name not in self.tabs:
            raise ValueError(f"Tab '{name}' does not exist")

        index = self.tab_indices[name]
        self.tab_widget.set_title(index, new_title)

    @property
    def widget(self) -> widgets.Tab:
        """Return tab widget for display"""
        return self.tab_widget

    @property
    def tab_names(self) -> List[str]:
        """Get list of tab names"""
        return list(self.tabs.keys())

    @property
    def tab_count(self) -> int:
        """Get number of tabs"""
        return len(self.tabs)

    def display(self):
        """Display the widget"""
        display(self.tab_widget)

    def __repr__(self) -> str:
        """String representation"""
        active = self.get_active_tab()
        return f"TabbedControls(tabs={self.tab_count}, active='{active}')"


class AccordionControls:
    """Organize controls in accordion interface"""

    def __init__(self, titles: Optional[List[str]] = None):
        """
        Initialize accordion controls

        Args:
            titles: Optional list of section titles to pre-create
        """
        self.sections: Dict[str, widgets.VBox] = {}
        self.section_indices: Dict[str, int] = {}

        self.accordion = widgets.Accordion()
        self.accordion.layout = widgets.Layout(width='100%', height='auto')

        if titles:
            for title in titles:
                self.add_section(title, [])

        # Wire up selection change observation
        self.accordion.observe(self._on_selection_change, names='selected_index')

    def _on_selection_change(self, change):
        """Handle accordion selection change"""
        # Can be used for lazy loading
        pass

    def add_section(
        self,
        name: str,
        controls: List[widgets.Widget],
        title: Optional[str] = None,
        open: bool = False
    ):
        """
        Add a section with controls

        Args:
            name: Internal name for the section
            controls: List of widgets to include
            title: Display title (defaults to name)
            open: Whether to open this section initially
        """
        if name in self.sections:
            raise ValueError(f"Section '{name}' already exists")

        # Create VBox for section content
        section_content = widgets.VBox(
            controls,
            layout=widgets.Layout(
                padding='10px',
                overflow_y='auto'
            )
        )

        # Add to accordion
        current_children = list(self.accordion.children)
        current_children.append(section_content)
        self.accordion.children = tuple(current_children)

        # Set title
        index = len(current_children) - 1
        display_title = title or name
        self.accordion.set_title(index, display_title)
        self.accordion.selected_index = index if open else None

        # Store references
        self.sections[name] = section_content
        self.section_indices[name] = index

    def remove_section(self, name: str):
        """
        Remove a section

        Args:
            name: Section name to remove
        """
        if name not in self.sections:
            raise ValueError(f"Section '{name}' does not exist")

        # Get current children
        children_list = list(self.accordion.children)
        index = self.section_indices[name]

        # Remove section
        children_list.pop(index)
        self.accordion.children = tuple(children_list)

        # Update indices
        del self.sections[name]
        del self.section_indices[name]

        # Rebuild indices
        for i, section_name in enumerate(self.sections.keys()):
            self.section_indices[section_name] = i

    def add_control(self, section_name: str, control: widgets.Widget):
        """Add a control to existing section"""
        if section_name not in self.sections:
            raise ValueError(f"Section '{section_name}' does not exist")

        section_content = self.sections[section_name]
        children_list = list(section_content.children)
        children_list.append(control)
        section_content.children = tuple(children_list)

    def remove_control(self, section_name: str, control: widgets.Widget):
        """Remove control from section"""
        if section_name not in self.sections:
            raise ValueError(f"Section '{section_name}' does not exist")

        section_content = self.sections[section_name]
        children_list = list(section_content.children)

        if control in children_list:
            children_list.remove(control)
            section_content.children = tuple(children_list)

    def get_open_section(self) -> str:
        """Get currently open section name"""
        index = self.accordion.selected_index
        if index is None:
            return ""

        for name, section_index in self.section_indices.items():
            if section_index == index:
                return name
        return ""

    def open_section(self, name: str):
        """Open a specific section"""
        if name not in self.sections:
            raise ValueError(f"Section '{name}' does not exist")

        self.accordion.selected_index = self.section_indices[name]

    def close_all(self):
        """Close all sections"""
        self.accordion.selected_index = None

    @property
    def widget(self) -> widgets.Accordion:
        """Return accordion widget for display"""
        return self.accordion

    @property
    def section_names(self) -> List[str]:
        """Get list of section names"""
        return list(self.sections.keys())

    @property
    def section_count(self) -> int:
        """Get number of sections"""
        return len(self.sections)

    def display(self):
        """Display the widget"""
        display(self.accordion)

    def __repr__(self) -> str:
        """String representation"""
        open_section = self.get_open_section()
        return f"AccordionControls(sections={self.section_count}, open='{open_section}')"
