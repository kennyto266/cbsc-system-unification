"""
Jupyter Service for notebook execution and management

This service provides functionality to:
- Execute Jupyter notebooks programmatically
- Validate notebook structure and syntax
- Manage available Jupyter kernels
- Handle execution timeouts and errors
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class JupyterService:
    """
    Service for interacting with Jupyter notebooks

    Provides notebook execution, validation, and kernel management.
    Integrates with local Jupyter installation.
    """

    def __init__(self, jupyter_path: str = 'jupyter'):
        """
        Initialize Jupyter service

        Args:
            jupyter_path: Path to jupyter executable (default: 'jupyter')
        """
        self.jupyter_path = jupyter_path
        self.default_timeout = 60  # seconds

    async def execute_notebook(
        self,
        notebook_path: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a Jupyter notebook and return results

        Converts notebook to Python script and executes it.
        This approach is more reliable than direct kernel communication.

        Args:
            notebook_path: Path to the .ipynb file
            timeout: Execution timeout in seconds (default: 60)

        Returns:
            Dict with keys:
                - success: bool - Whether execution succeeded
                - output: str - Standard output from execution
                - error: str - Error message if execution failed
        """
        timeout = timeout or self.default_timeout

        try:
            # Validate notebook exists
            if not os.path.exists(notebook_path):
                return {
                    'success': False,
                    'error': f'Notebook not found: {notebook_path}'
                }

            # Read notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)

            # Extract and combine code cells
            code_cells = self._extract_code_cells(notebook)

            if not code_cells:
                return {
                    'success': True,
                    'output': 'No code cells to execute'
                }

            # Create temporary Python script
            script_path = self._create_temp_script(code_cells)

            try:
                # Execute the script
                result = subprocess.run(
                    ['python', script_path],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=os.path.dirname(notebook_path)
                )

                # Clean up script
                Path(script_path).unlink(missing_ok=True)

                # Return results
                if result.returncode != 0:
                    return {
                        'success': False,
                        'error': result.stderr,
                        'output': result.stdout
                    }

                return {
                    'success': True,
                    'output': result.stdout
                }

            except subprocess.TimeoutExpired:
                # Clean up script on timeout
                Path(script_path).unlink(missing_ok=True)
                return {
                    'success': False,
                    'error': f'Execution timeout after {timeout} seconds'
                }

        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid notebook format (not valid JSON)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Execution failed: {str(e)}'
            }

    def _extract_code_cells(self, notebook: Dict) -> List[str]:
        """
        Extract code cells from notebook

        Args:
            notebook: Parsed notebook dictionary

        Returns:
            List of code cell contents
        """
        code_cells = []

        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])

                # Source can be string or list of strings
                if isinstance(source, str):
                    code = source
                else:
                    code = ''.join(source)

                # Skip empty cells
                if code.strip():
                    code_cells.append(code)

        return code_cells

    def _create_temp_script(self, code_cells: List[str]) -> str:
        """
        Create a temporary Python script from code cells

        Args:
            code_cells: List of code cell contents

        Returns:
            Path to temporary script file
        """
        # Combine cells with separators
        script = '\n\n# --- Cell Separator ---\n\n'.join(code_cells)

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(script)
            return f.name

    async def get_available_kernels(self) -> List[str]:
        """
        Get list of available Jupyter kernels

        Returns:
            List of kernel names (e.g., ['python3', 'python2'])
        """
        try:
            result = subprocess.run(
                [self.jupyter_path, 'kernelspec', 'list', '--json'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return ['python3']  # Fallback

            specs = json.loads(result.stdout)
            kernelspecs = specs.get('kernelspecs', {})
            return list(kernelspecs.keys())

        except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
            # Jupyter not available or error
            return ['python3']  # Always provide fallback

    def validate_notebook(self, notebook_path: str) -> Dict[str, Any]:
        """
        Validate notebook structure and syntax

        Checks:
        - Valid JSON format
        - Correct nbformat version
        - Cell structure integrity
        - Python syntax in code cells

        Args:
            notebook_path: Path to the notebook file

        Returns:
            Dict with keys:
                - valid: bool - Overall validation status
                - errors: List[str] - Validation errors found
                - warnings: List[str] - Validation warnings
        """
        errors = []
        warnings = []

        try:
            # Check file exists
            if not os.path.exists(notebook_path):
                return {
                    'valid': False,
                    'errors': [f'File not found: {notebook_path}'],
                    'warnings': warnings
                }

            # Read and parse notebook
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)

            # Check nbformat version
            nbformat = notebook.get('nbformat')
            if nbformat != 4:
                errors.append(f'Invalid nbformat: {nbformat} (expected 4)')

            # Check cells structure
            if 'cells' not in notebook:
                errors.append('Missing cells array')
                return {
                    'valid': False,
                    'errors': errors,
                    'warnings': warnings
                }

            cells = notebook['cells']
            if not isinstance(cells, list):
                errors.append('Cells must be an array')
                return {
                    'valid': False,
                    'errors': errors,
                    'warnings': warnings
                }

            # Validate each cell
            for i, cell in enumerate(cells):
                cell_errors = self._validate_cell(cell, i)
                errors.extend(cell_errors)

            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }

        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'errors': [f'Invalid JSON: {str(e)}'],
                'warnings': warnings
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'Validation error: {str(e)}'],
                'warnings': warnings
            }

    def _validate_cell(self, cell: Dict, index: int) -> List[str]:
        """
        Validate a single notebook cell

        Args:
            cell: Cell dictionary
            index: Cell index

        Returns:
            List of validation errors
        """
        errors = []

        # Check cell_type
        cell_type = cell.get('cell_type')
        if not cell_type:
            errors.append(f'Cell {index}: missing cell_type')
            return errors

        if cell_type not in ['code', 'markdown', 'raw']:
            errors.append(f'Cell {index}: invalid cell_type "{cell_type}"')

        # Validate code cells
        if cell_type == 'code':
            source = cell.get('source', [])

            # Extract source string
            if isinstance(source, str):
                code = source
            elif isinstance(source, list):
                code = ''.join(source)
            else:
                errors.append(f'Cell {index}: invalid source type')
                return errors

            # Skip empty cells
            if not code.strip():
                return errors

            # Check Python syntax
            try:
                compile(code, f'<cell {index}>', 'exec')
            except SyntaxError as e:
                errors.append(f'Cell {index}: {e.msg} at line {e.lineno}')

        return errors

    def get_notebook_metadata(self, notebook_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from notebook

        Args:
            notebook_path: Path to notebook

        Returns:
            Notebook metadata dict or None if error
        """
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)
            return notebook.get('metadata', {})
        except Exception:
            return None

    def count_cells(self, notebook_path: str) -> Dict[str, int]:
        """
        Count cells by type in notebook

        Args:
            notebook_path: Path to notebook

        Returns:
            Dict with counts for each cell type
        """
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                notebook = json.load(f)

            counts = {'code': 0, 'markdown': 0, 'raw': 0}

            for cell in notebook.get('cells', []):
                cell_type = cell.get('cell_type')
                if cell_type in counts:
                    counts[cell_type] += 1

            return counts

        except Exception:
            return {'code': 0, 'markdown': 0, 'raw': 0}


# Singleton instance for application-wide use
jupyter_service = JupyterService()
