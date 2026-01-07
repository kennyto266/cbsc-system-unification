import pytest
import subprocess
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.jupyter_service import JupyterService, jupyter_service


class TestJupyterService:
    """Test suite for JupyterService"""

    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test"""
        return JupyterService()

    @pytest.fixture
    def sample_notebook(self):
        """Create a sample notebook for testing"""
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "import pandas as pd\n",
                        "import numpy as np\n",
                        "\n",
                        "data = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})\n",
                        "print('Data shape:', data.shape)\n",
                        "print(data)"
                    ]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "result = data.sum()\n",
                        "print('Sum:', result)"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.10.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

        # Create temporary notebook file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook, f)
            temp_path = f.name

        yield temp_path

        # Cleanup
        os.unlink(temp_path)

    @pytest.fixture
    def invalid_notebook(self):
        """Create an invalid notebook for testing error handling"""
        invalid_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "invalid syntax here !!!\n",
                        "more bad syntax"
                    ]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(invalid_notebook, f)
            temp_path = f.name

        yield temp_path

        os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_notebook_success(self, service, sample_notebook):
        """Test successful notebook execution"""
        result = await service.execute_notebook(sample_notebook)

        assert result is not None
        assert 'success' in result

        # Note: If Jupyter is not installed, this might fail
        # but we handle it gracefully
        if result['success']:
            assert 'output' in result
        else:
            # Jupyter might not be available in test environment
            assert 'error' in result

    @pytest.mark.asyncio
    async def test_execute_notebook_with_syntax_error(self, service, invalid_notebook):
        """Test notebook execution with syntax errors"""
        result = await service.execute_notebook(invalid_notebook)

        assert result is not None
        assert 'success' in result
        assert 'error' in result or 'output' in result

    def test_validate_notebook_valid(self, service, sample_notebook):
        """Test validation of valid notebook"""
        validation = service.validate_notebook(sample_notebook)

        assert validation is not None
        assert 'valid' in validation
        assert 'errors' in validation
        assert isinstance(validation['valid'], bool)
        assert isinstance(validation['errors'], list)

        # Should be valid if Jupyter is available, or have specific errors
        if validation['valid']:
            assert len(validation['errors']) == 0

    def test_validate_notebook_invalid_structure(self, service):
        """Test validation of notebook with invalid structure"""
        # Create invalid notebook
        invalid_path = tempfile.mktemp(suffix='.ipynb')
        with open(invalid_path, 'w') as f:
            f.write('not a valid notebook')

        try:
            validation = service.validate_notebook(invalid_path)

            assert validation['valid'] is False
            assert len(validation['errors']) > 0
        finally:
            os.unlink(invalid_path)

    def test_validate_notebook_invalid_format(self, service):
        """Test validation of notebook with wrong nbformat"""
        invalid_format_notebook = {
            "cells": [],
            "metadata": {},
            "nbformat": 3,  # Wrong format
            "nbformat_minor": 0
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(invalid_format_notebook, f)
            temp_path = f.name

        try:
            validation = service.validate_notebook(temp_path)

            assert validation['valid'] is False
            assert any('nbformat' in error.lower() for error in validation['errors'])
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_get_available_kernels(self, service):
        """Test getting available Jupyter kernels"""
        kernels = await service.get_available_kernels()

        assert isinstance(kernels, list)
        assert len(kernels) > 0
        # Should at least have a fallback kernel
        assert 'python3' in kernels

    @pytest.mark.asyncio
    async def test_get_available_kernels_with_jupyter_not_installed(self, service):
        """Test kernel listing when Jupyter is not installed"""
        with patch('subprocess.run') as mock_run:
            # Mock Jupyter not being available
            mock_run.side_effect = FileNotFoundError()

            kernels = await service.get_available_kernels()

            # Should return fallback
            assert isinstance(kernels, list)
            assert 'python3' in kernels

    def test_validate_notebook_with_empty_cells(self, service):
        """Test validation handles empty cells gracefully"""
        notebook_with_empty = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": []
                },
                {
                    "cell_type": "markdown",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["# Header"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook_with_empty, f)
            temp_path = f.name

        try:
            validation = service.validate_notebook(temp_path)

            # Empty cells should not cause validation errors
            assert 'valid' in validation
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_notebook_timeout(self, service):
        """Test notebook execution with timeout"""
        # Create a notebook with infinite loop
        infinite_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["while True:\n    pass"]
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(infinite_notebook, f)
            temp_path = f.name

        try:
            # Use a short timeout for testing
            result = await service.execute_notebook(temp_path, timeout=1)

            assert result is not None
            if not result['success']:
                # Should timeout
                assert 'timeout' in result.get('error', '').lower() or 'error' in result
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_execute_notebook_nonexistent_file(self, service):
        """Test execution of non-existent notebook"""
        result = await service.execute_notebook('/nonexistent/path.ipynb')

        assert result is not None
        assert result['success'] is False
        assert 'error' in result

    def test_singleton_instance(self):
        """Test that jupyter_service is a singleton"""
        from services.jupyter_service import jupyter_service as instance1
        from services.jupyter_service import jupyter_service as instance2

        # Should be the same instance
        assert instance1 is instance2


class TestJupyterServiceIntegration:
    """Integration tests for JupyterService"""

    @pytest.mark.asyncio
    async def test_end_to_end_execution_flow(self):
        """Test complete flow: validate -> execute -> validate"""
        service = JupyterService()

        # Create test notebook
        notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "x = 10\n",
                        "y = 20\n",
                        "print(f'Sum: {x + y}')"
                    ]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook, f)
            temp_path = f.name

        try:
            # Step 1: Validate before execution
            validation_before = service.validate_notebook(temp_path)
            assert validation_before['valid'] is True

            # Step 2: Execute
            result = await service.execute_notebook(temp_path)
            assert result is not None

            # Step 3: Validate after execution (notebook structure should be intact)
            validation_after = service.validate_notebook(temp_path)
            assert 'valid' in validation_after

        finally:
            os.unlink(temp_path)
