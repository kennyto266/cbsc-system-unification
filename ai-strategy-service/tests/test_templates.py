"""
Tests for notebook template system
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from templates.notebook_templates import TemplateManager, NotebookTemplate


def test_template_manager_initialization():
    """Test template manager initializes with built-in templates"""
    manager = TemplateManager()

    templates = manager.list_templates()
    assert len(templates) >= 2

    template_names = [t['name'] for t in templates]
    assert 'breakout' in template_names
    assert 'mean_reversion' in template_names


def test_notebook_template_structure():
    """Test notebook template generates valid format"""
    template = NotebookTemplate("test", "Test template")
    template.add_cell("code", "print('hello')")

    notebook = template.to_notebook()

    assert notebook['nbformat'] == 4
    assert len(notebook['cells']) == 1
    assert notebook['cells'][0]['cell_type'] == 'code'


def test_breakout_template_content():
    """Test breakout template has required cells"""
    manager = TemplateManager()
    template = manager.get_template('breakout')

    assert template is not None
    assert len(template.cells) >= 6  # Should have at least 6 cells

    # Check for key cells
    cell_sources = [' '.join(cell['source']) for cell in template.cells]
    assert any('fetch_data' in source or 'fetch' in source for source in cell_sources)
    assert any('portfolio' in source.lower() or 'backtest' in source.lower() for source in cell_sources)
    assert any('matplotlib' in source or 'plot' in source for source in cell_sources)


def test_mean_reversion_template_content():
    """Test mean reversion template has required cells"""
    manager = TemplateManager()
    template = manager.get_template('mean_reversion')

    assert template is not None
    assert len(template.cells) >= 4

    # Check for key components
    cell_sources = [' '.join(cell['source']) for cell in template.cells]
    assert any('bollinger' in source.lower() for source in cell_sources)
    assert any('z_score' in source or 'z-score' in source for source in cell_sources)
    assert any('signal' in source.lower() for source in cell_sources)


def test_notebook_cell_types():
    """Test that cells have correct types"""
    template = NotebookTemplate("test", "Test")
    template.add_cell("markdown", "# Header")
    template.add_cell("code", "x = 1")

    cells = template.cells
    assert cells[0]['cell_type'] == 'markdown'
    assert cells[1]['cell_type'] == 'code'


def test_notebook_json_export():
    """Test notebook can be exported as JSON"""
    template = NotebookTemplate("test", "Test")
    template.add_cell("code", "print('test')")

    json_str = template.to_json()

    # Verify it's valid JSON
    import json
    parsed = json.loads(json_str)
    assert parsed['nbformat'] == 4
    assert len(parsed['cells']) == 1


def test_template_metadata():
    """Test template includes proper metadata"""
    manager = TemplateManager()
    template = manager.get_template('breakout')

    notebook = template.to_notebook()

    assert 'metadata' in notebook
    assert 'kernelspec' in notebook['metadata']
    assert notebook['metadata']['kernelspec']['language'] == 'python'
    assert 'language_info' in notebook['metadata']


def test_get_nonexistent_template():
    """Test getting non-existent template returns None"""
    manager = TemplateManager()
    template = manager.get_template('nonexistent')

    assert template is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
