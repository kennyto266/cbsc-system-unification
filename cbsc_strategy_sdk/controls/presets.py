"""
Preset Management Module

Provides save/load functionality for strategy parameter presets.
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import ipywidgets as widgets
from IPython.display import display


class PresetManager:
    """Manage parameter presets for strategies"""

    def __init__(self, storage_path: str = "./strategy_presets.json"):
        """
        Initialize preset manager

        Args:
            storage_path: Path to JSON file for preset storage
        """
        self.storage_path = Path(storage_path)
        self.presets: Dict[str, Dict] = self._load_presets()

    def _load_presets(self) -> Dict[str, Dict]:
        """Load presets from storage file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load presets: {e}")
                return {}
        return {}

    def _save_presets(self):
        """Save presets to storage file"""
        try:
            # Create directory if it doesn't exist
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.storage_path, 'w') as f:
                json.dump(self.presets, f, indent=2, default=str)
        except Exception as e:
            print(f"Error: Could not save presets: {e}")

    def save_preset(
        self,
        name: str,
        parameters: Dict[str, Any],
        description: str = "",
        tags: Optional[List[str]] = None
    ):
        """
        Save current parameters as preset

        Args:
            name: Preset name
            parameters: Parameter dictionary
            description: Optional description
            tags: Optional list of tags for categorization
        """
        self.presets[name] = {
            'parameters': parameters,
            'description': description,
            'tags': tags or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self._save_presets()

    def load_preset(self, name: str) -> Dict[str, Any]:
        """
        Load preset by name

        Args:
            name: Preset name

        Returns:
            Parameter dictionary

        Raises:
            KeyError: If preset not found
        """
        if name not in self.presets:
            raise KeyError(f"Preset '{name}' not found")

        return self.presets[name]['parameters'].copy()

    def delete_preset(self, name: str):
        """
        Delete preset

        Args:
            name: Preset name

        Raises:
            KeyError: If preset not found
        """
        if name not in self.presets:
            raise KeyError(f"Preset '{name}' not found")

        del self.presets[name]
        self._save_presets()

    def list_presets(self) -> List[str]:
        """
        List available preset names

        Returns:
            List of preset names sorted alphabetically
        """
        return sorted(self.presets.keys())

    def get_preset_info(self, name: str) -> Dict[str, Any]:
        """
        Get preset metadata

        Args:
            name: Preset name

        Returns:
            Dictionary with description, tags, created_at, updated_at
        """
        if name not in self.presets:
            raise KeyError(f"Preset '{name}' not found")

        preset = self.presets[name]
        return {
            'description': preset.get('description', ''),
            'tags': preset.get('tags', []),
            'created_at': preset.get('created_at', ''),
            'updated_at': preset.get('updated_at', '')
        }

    def update_preset(
        self,
        name: str,
        parameters: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """
        Update existing preset

        Args:
            name: Preset name
            parameters: New parameter values (optional)
            description: New description (optional)
            tags: New tags (optional)
        """
        if name not in self.presets:
            raise KeyError(f"Preset '{name}' not found")

        if parameters is not None:
            self.presets[name]['parameters'] = parameters

        if description is not None:
            self.presets[name]['description'] = description

        if tags is not None:
            self.presets[name]['tags'] = tags

        self.presets[name]['updated_at'] = datetime.now().isoformat()
        self._save_presets()

    def find_presets_by_tag(self, tag: str) -> List[str]:
        """
        Find presets with specific tag

        Args:
            tag: Tag to search for

        Returns:
            List of preset names with the tag
        """
        return [
            name for name, preset in self.presets.items()
            if tag in preset.get('tags', [])
        ]

    def import_presets(self, file_path: str, merge: bool = True):
        """
        Import presets from JSON file

        Args:
            file_path: Path to JSON file
            merge: If True, merge with existing presets; if False, replace
        """
        with open(file_path, 'r') as f:
            imported = json.load(f)

        if merge:
            self.presets.update(imported)
        else:
            self.presets = imported

        self._save_presets()

    def export_presets(self, file_path: str, names: Optional[List[str]] = None):
        """
        Export presets to JSON file

        Args:
            file_path: Destination file path
            names: List of preset names to export (None = all)
        """
        if names is None:
            to_export = self.presets
        else:
            to_export = {name: self.presets[name] for name in names if name in self.presets}

        with open(file_path, 'w') as f:
            json.dump(to_export, f, indent=2, default=str)

    def to_widget(
        self,
        on_load: Optional[callable] = None,
        on_save: Optional[callable] = None
    ) -> widgets.VBox:
        """
        Create preset management widget

        Args:
            on_load: Callback when preset is loaded (receives parameters)
            on_save: Callback when preset is saved (receives parameters)

        Returns:
            VBox widget with preset management UI
        """
        # Preset selector
        self.preset_dropdown = widgets.Dropdown(
            options=[],
            description='Preset:',
            style={'description_width': 'initial'},
            layout=widgets.Layout(width='70%')
        )

        # Refresh button
        self.refresh_btn = widgets.Button(
            description='Refresh',
            icon='refresh',
            layout=widgets.Layout(width='28%')
        )

        # Action buttons
        self.load_btn = widgets.Button(
            description='Load',
            button_style='primary',
            icon='upload',
            layout=widgets.Layout(width='32%')
        )

        self.save_btn = widgets.Button(
            description='Save',
            button_style='success',
            icon='download',
            layout=widgets.Layout(width='32%')
        )

        self.delete_btn = widgets.Button(
            description='Delete',
            button_style='danger',
            icon='trash',
            layout=widgets.Layout(width='32%')
        )

        # New preset section
        self.new_preset_name = widgets.Text(
            placeholder='Preset name...',
            layout=widgets.Layout(width='60%')
        )

        self.new_preset_desc = widgets.Text(
            placeholder='Description (optional)...',
            layout=widgets.Layout(width='60%')
        )

        self.new_preset_tags = widgets.Text(
            placeholder='Tags (comma separated)...',
            layout=widgets.Layout(width='60%')
        )

        # Info display
        self.info_display = widgets.HTML(
            value='<i>Select a preset or create a new one</i>',
            layout=widgets.Layout(width='100%')
        )

        # Wire up events
        self.refresh_btn.on_click(self._refresh_list)
        self.load_btn.on_click(lambda b: self._on_load(on_load))
        self.save_btn.on_click(lambda b: self._on_save(on_save))
        self.delete_btn.on_click(self._on_delete)
        self.preset_dropdown.observe(self._on_selection_change, names='value')

        # Initial load
        self._refresh_list(None)

        # Build layout
        widget = widgets.VBox([
            widgets.HTML('<h4>Preset Management</h4>'),
            widgets.HBox([self.preset_dropdown, self.refresh_btn]),
            widgets.HBox([self.load_btn, self.save_btn, self.delete_btn]),
            widgets.HTML('<hr>'),
            widgets.HTML('<b>Save New Preset:</b>'),
            self.new_preset_name,
            self.new_preset_desc,
            self.new_preset_tags,
            widgets.HTML('<br>'),
            self.info_display
        ])

        self.widget = widget
        return widget

    def _refresh_list(self, button):
        """Refresh preset list"""
        self.preset_dropdown.options = self.list_presets()

    def _on_selection_change(self, change):
        """Handle preset selection change"""
        name = change['new']
        if name and name in self.presets:
            info = self.get_preset_info(name)
            tags_str = ', '.join(info['tags']) if info['tags'] else 'None'

            html = f"""
            <b>Preset: {name}</b><br>
            Description: {info['description'] or 'None'}<br>
            Tags: {tags_str}<br>
            Created: {info['created_at'][:10] if info['created_at'] else 'N/A'}<br>
            Updated: {info['updated_at'][:10] if info['updated_at'] else 'N/A'}
            """
            self.info_display.value = html

    def _on_load(self, callback):
        """Handle load button click"""
        name = self.preset_dropdown.value
        if not name:
            self.info_display.value = '<span style="color: red;">No preset selected</span>'
            return

        try:
            params = self.load_preset(name)
            if callback:
                callback(params)
            self.info_display.value = f'<span style="color: green;">✓ Loaded preset: {name}</span>'
        except Exception as e:
            self.info_display.value = f'<span style="color: red;">Error loading preset: {e}</span>'

    def _on_save(self, callback):
        """Handle save button click"""
        name = self.new_preset_name.value.strip()
        if not name:
            self.info_display.value = '<span style="color: red;">Enter a preset name</span>'
            return

        try:
            # Get parameters from callback
            if callback:
                params = callback()
            else:
                params = {}

            desc = self.new_preset_desc.value.strip()
            tags = [t.strip() for t in self.new_preset_tags.value.split(',') if t.strip()]

            self.save_preset(name, params, desc, tags)
            self._refresh_list(None)
            self.preset_dropdown.value = name

            # Clear inputs
            self.new_preset_name.value = ''
            self.new_preset_desc.value = ''
            self.new_preset_tags.value = ''

            self.info_display.value = f'<span style="color: green;">✓ Saved preset: {name}</span>'
        except Exception as e:
            self.info_display.value = f'<span style="color: red;">Error saving preset: {e}</span>'

    def _on_delete(self, button):
        """Handle delete button click"""
        name = self.preset_dropdown.value
        if not name:
            self.info_display.value = '<span style="color: red;">No preset selected</span>'
            return

        try:
            self.delete_preset(name)
            self._refresh_list(None)
            self.info_display.value = f'<span style="color: orange;">Deleted preset: {name}</span>'
        except Exception as e:
            self.info_display.value = f'<span style="color: red;">Error deleting preset: {e}</span>'

    def display(self):
        """Display the widget"""
        if hasattr(self, 'widget'):
            display(self.widget)
        else:
            display(self.to_widget())

    def __repr__(self) -> str:
        """String representation"""
        return f"PresetManager(presets={len(self.presets)}, path={self.storage_path})"
