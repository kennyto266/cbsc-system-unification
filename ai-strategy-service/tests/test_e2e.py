"""
End-to-End Integration Tests for AI Strategy Development Tool

This module tests the complete workflow:
1. Strategy Generation (GLM AI)
2. Notebook Creation
3. Strategy Execution
4. CBSC Deployment
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch


class TestE2E:
    """End-to-end tests for the complete workflow"""

    @pytest.mark.asyncio
    async def test_complete_workflow_generate_to_execute(self):
        """Test: Generate Strategy → Save Notebook → Execute"""

        # Step 1: Generate strategy using GLM service
        from services.glm_service import GLMService, GLMMessage

        # Mock GLM API response for testing
        mock_strategy_code = """
# Cell 1: Imports
import pandas as pd
import numpy as np

# Cell 2: Configuration
SYMBOL = "AAPL"
LOOKBACK = 20

# Cell 3: Data Fetching
def fetch_data(symbol):
    return pd.DataFrame({'price': [100, 102, 101, 103]})

# Cell 4: Signal Generation
data = fetch_data(SYMBOL)
data['signal'] = np.where(data['price'] > data['price'].rolling(LOOKBACK).mean(), 1, -1)

# Cell 5: Backtesting
print(f"Total signals: {data['signal'].abs().sum()}")
"""

        with patch('services.glm_service.httpx.AsyncClient') as mock_client_class:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": mock_strategy_code
                    }
                }]
            }

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Execute strategy generation
            glm_service = GLMService()
            glm_service.client = mock_client

            system_prompt = GLMMessage(
                role="system",
                content="Generate a simple moving average crossover strategy."
            )
            user_prompt = GLMMessage(
                role="user",
                content="Create a basic moving average crossover strategy"
            )

            response = await glm_service.chat([system_prompt, user_prompt])

            assert response is not None
            assert len(response) > 0
            assert "import pandas" in response

            await glm_service.close()

        # Step 2: Save to notebook file
        notebook_data = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# Moving Average Crossover Strategy\n"]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": mock_strategy_code.strip().split('\n')
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

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook_data, f, indent=2)
            notebook_path = f.name

        try:
            # Step 3: Validate notebook structure
            from services.jupyter_service import jupyter_service

            validation = jupyter_service.validate_notebook(notebook_path)

            assert validation['valid'] == True, f"Validation failed: {validation['errors']}"
            assert len(validation['errors']) == 0

            # Step 4: Verify notebook can be loaded
            with open(notebook_path, 'r') as f:
                loaded_notebook = json.load(f)

            assert loaded_notebook['nbformat'] == 4
            assert len(loaded_notebook['cells']) >= 1
            assert loaded_notebook['cells'][0]['cell_type'] == 'markdown'

        finally:
            # Cleanup
            Path(notebook_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_template_to_execution_flow(self):
        """Test: Template Selection → Generate Notebook → Execute"""

        from templates.notebook_templates import TemplateManager

        # Step 1: Get built-in template
        manager = TemplateManager()
        template = manager.get_template('breakout')

        assert template is not None
        assert template.name == 'breakout'
        assert len(template.cells) > 0

        # Step 2: Convert to notebook
        notebook = template.to_notebook()

        assert notebook['nbformat'] == 4
        assert len(notebook['cells']) > 0

        # Step 3: Save and validate
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(notebook, f, indent=2)
            template_path = f.name

        try:
            from services.jupyter_service import jupyter_service

            validation = jupyter_service.validate_notebook(template_path)

            assert validation['valid'] == True, f"Template validation failed: {validation['errors']}"

            # Verify key cells exist
            with open(template_path, 'r') as f:
                template_data = json.load(f)

            cell_sources = [' '.join(cell.get('source', [])) for cell in template_data['cells']]

            # Check for critical components
            assert any('import' in source for source in cell_sources), "Missing imports cell"
            assert any('fetch_data' in source or 'data' in source for source in cell_sources), "Missing data fetching"
            assert any('signal' in source for source in cell_sources), "Missing signal generation"

        finally:
            Path(template_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('services.cbsc_integration.httpx.AsyncClient')
    async def test_ai_generation_to_cbsc_deployment(self, mock_client_class):
        """Test: AI Generation → Parameter Extraction → CBSC Deployment"""

        # Setup mock CBSC API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "strategy-test-123",
            "name": "AI Generated Strategy",
            "status": "created"
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Step 1: Create test notebook with parameters
        test_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": [
                        "SYMBOL = 'AAPL'\n",
                        "LOOKBACK = 20\n",
                        "THRESHOLD = 0.02\n",
                        "STOP_LOSS = 0.03\n",
                        "TAKE_PROFIT = 0.10\n"
                    ]
                },
                {
                    "cell_type": "code",
                    "source": [
                        "# Strategy logic here\n",
                        "def generate_signals(data):\n",
                        "    return signals\n"
                    ]
                }
            ],
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(test_notebook, f)
            notebook_path = f.name

        try:
            # Step 2: Extract parameters
            from services.cbsc_integration import CBSCIntegration

            integration = CBSCIntegration()
            integration.client = mock_client

            params = await integration._extract_parameters(notebook_path)

            assert 'symbol' in params
            assert params['symbol'] == 'AAPL'
            assert 'lookback' in params
            assert params['lookback'] == '20'

            # Step 3: Deploy to CBSC
            result = await integration.deploy_strategy(
                notebook_path=notebook_path,
                strategy_name="E2E Test Strategy",
                user_id="test-user-123"
            )

            assert result['success'] == True
            assert result['strategy_id'] == 'strategy-test-123'

            await integration.close()

        finally:
            Path(notebook_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_strategy_api_end_to_end(self):
        """Test: API Request → Strategy Generation → Response Format"""

        from fastapi.testclient import TestClient
        from main import app
        from unittest.mock import AsyncMock, Mock, patch

        with patch('services.glm_service.httpx.AsyncClient') as mock_client_class:
            # Mock GLM API
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{
                    "message": {
                        "content": """
```python
# Cell 1: Imports
import pandas as pd
```
```python
# Cell 2: Strategy
def strategy():
    pass
```
"""
                    }
                }]
            }

            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Test API endpoint
            client = TestClient(app)

            response = client.post(
                "/api/strategy/generate",
                json={
                    "description": "Simple momentum strategy",
                    "market": "stock",
                    "timeframe": "daily",
                    "risk_level": "medium"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "code" in data
            assert "explanation" in data
            assert "parameters" in data
            assert "Cell" in data["code"]  # Cell markers present

    def test_notebook_validation_comprehensive(self):
        """Test comprehensive notebook validation"""

        from services.jupyter_service import jupyter_service

        # Test valid notebook
        valid_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["import pandas as pd\n", "x = 1\n"]
                }
            ],
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(valid_notebook, f)
            valid_path = f.name

        try:
            result = jupyter_service.validate_notebook(valid_path)
            assert result['valid'] == True
            assert len(result['errors']) == 0
        finally:
            Path(valid_path).unlink(missing_ok=True)

        # Test invalid notebook (syntax error)
        invalid_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "source": ["import pandas as pd\n", "if True\n", "    x = 1\n"]  # Syntax error
                }
            ],
            "nbformat": 4,
            "nbformat_minor": 4
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            json.dump(invalid_notebook, f)
            invalid_path = f.name

        try:
            result = jupyter_service.validate_notebook(invalid_path)
            assert result['valid'] == False
            assert len(result['errors']) > 0
        finally:
            Path(invalid_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_parameter_extraction_edge_cases(self):
        """Test parameter extraction with various edge cases"""

        from services.cbsc_integration import CBSCIntegration

        integration = CBSCIntegration()

        # Test with multiple parameter formats
        test_cases = [
            {
                "name": "Standard parameters",
                "source": "SYMBOL = 'AAPL'\nLOOKBACK = 20\nTHRESHOLD = 0.02",
                "expected": {"symbol": "AAPL", "lookback": "20", "threshold": "0.02"}
            },
            {
                "name": "String parameters",
                "source": 'START_DATE = "2023-01-01"\nEND_DATE = "2024-01-01"',
                "expected": {"start_date": "2023-01-01", "end_date": "2024-01-01"}
            },
            {
                "name": "Float parameters",
                "source": "STOP_LOSS = 0.03\nTAKE_PROFIT = 0.10",
                "expected": {"stop_loss": "0.03", "take_profit": "0.10"}
            }
        ]

        for test_case in test_cases:
            notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "source": [test_case["source"]]
                    }
                ],
                "nbformat": 4,
                "nbformat_minor": 4
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
                json.dump(notebook, f)
                temp_path = f.name

            try:
                params = await integration._extract_parameters(temp_path)

                for key, value in test_case["expected"].items():
                    assert key in params, f"{test_case['name']}: Missing {key}"
                    assert params[key] == value, f"{test_case['name']}: Wrong value for {key}"

            finally:
                Path(temp_path).unlink(missing_ok=True)


@pytest.mark.integration
class TestE2EWithRealServices:
    """Integration tests that may require actual services

    These tests can be skipped in CI/CD if services are not available
    """

    @pytest.mark.asyncio
    async def test_real_jupyter_execution(self):
        """Test actual Jupyter notebook execution

        This test requires Jupyter to be installed
        """
        import subprocess

        # Check if Jupyter is available
        try:
            result = subprocess.run(
                ['jupyter', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            jupyter_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            jupyter_available = False

        if not jupyter_available:
            pytest.skip("Jupyter not installed")

        # Create a simple test notebook
        test_notebook = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["print('Hello from Jupyter!')\n"]
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
            json.dump(test_notebook, f)
            notebook_path = f.name

        try:
            from services.jupyter_service import jupyter_service

            result = await jupyter_service.execute_notebook(notebook_path)

            assert result['success'] == True
            assert 'Hello from Jupyter!' in result['output']

        finally:
            Path(notebook_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('services.cbsc_integration.httpx.AsyncClient')
    async def test_cbsc_integration_with_mock(self, mock_client_class):
        """Test CBSC integration flow (mocked)"""

        import os

        if not os.getenv('CBSC_API_URL'):
            pytest.skip("CBSC_API_URL not configured")

        # Mock successful CBSC response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "test-strategy-123"}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        from services.cbsc_integration import cbsc_integration
        cbsc_integration.client = mock_client

        # Test sync endpoint
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/strategy/sync/test-user-123")

        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
