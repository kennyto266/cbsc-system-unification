"""
CBSC Integration Service

Integrates AI-generated strategies with the existing CBSC (量化交易策略管理系统).
Handles deployment, parameter extraction, and synchronization with the personal dashboard.
"""
from typing import Dict, Any, Optional
import httpx
import os
import json
import re
from pathlib import Path


class CBSCIntegration:
    """Integrate generated strategies with existing CBSC system"""

    def __init__(self):
        # CBSC API URL - defaults to port 3003 where CBSC system runs
        self.cbsc_api_url = os.getenv('CBSC_API_URL', 'http://localhost:3003')
        self.cbsc_api_key = os.getenv('CBSC_API_KEY', '')
        self.client = httpx.AsyncClient(timeout=30.0)

    async def deploy_strategy(
        self,
        notebook_path: str,
        strategy_name: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Deploy a notebook strategy to CBSC system

        Args:
            notebook_path: Path to the strategy notebook
            strategy_name: Name for the strategy
            user_id: User ID who created the strategy

        Returns:
            Deployment result with strategy ID
        """

        # 1. Extract strategy parameters from notebook
        params = await self._extract_parameters(notebook_path)

        # 2. Create strategy configuration compatible with CBSC
        strategy_config = {
            "name": strategy_name,
            "type": "personal",
            "category": "other",
            "description": params.get("description", "Created with AI Assistant"),
            "parameters": {
                **params,
                "created_with_ai": True,
                "source_notebook": notebook_path
            },
            "personalConfig": {
                "userId": user_id,
                "riskTolerance": params.get("risk_tolerance", "moderate"),
                "capitalAllocation": params.get("capital", 10000),
                "maxPositionSize": params.get("max_position", 0.1),
                "stopLoss": params.get("stop_loss", 0.03),
                "takeProfit": params.get("take_profit", 0.1),
                "autoTrading": False
            }
        }

        # 3. Register with CBSC API
        headers = {"Content-Type": "application/json"}
        if self.cbsc_api_key:
            headers["Authorization"] = f"Bearer {self.cbsc_api_key}"

        response = await self.client.post(
            f"{self.cbsc_api_url}/api/strategies",
            json=strategy_config,
            headers=headers
        )

        response.raise_for_status()
        result = response.json()

        return {
            "success": True,
            "strategy_id": result.get("id"),
            "message": "Strategy deployed successfully"
        }

    async def _extract_parameters(self, notebook_path: str) -> Dict[str, Any]:
        """Extract strategy parameters from notebook

        Parses notebook cells to find common parameter definitions like:
        - SYMBOL, LOOKBACK, THRESHOLD
        - START_DATE, END_DATE
        - Risk management parameters

        Args:
            notebook_path: Path to the notebook file

        Returns:
            Dictionary of extracted parameters with proper type conversion
        """
        with open(notebook_path, 'r') as f:
            notebook = json.load(f)

        params = {}

        # Parameter type mapping for conversion
        int_params = {'lookback', 'capital'}
        float_params = {'threshold', 'stop_loss', 'take_profit', 'max_position'}

        # Look for parameter definitions in code cells
        for cell in notebook.get('cells', []):
            if cell['cell_type'] == 'code':
                source = ''.join(cell.get('source', []))

                # Extract common parameters using regex
                # Variable assignment patterns
                param_patterns = {
                    'SYMBOL': r'SYMBOL\s*=\s*["\']([\w\-]+)["\']',
                    'START_DATE': r'START_DATE\s*=\s*["\']([\d\-]+)["\']',
                    'END_DATE': r'END_DATE\s*=\s*["\']([\d\-]+)["\']',
                    'LOOKBACK': r'LOOKBACK\s*=\s*(\d+)',
                    'THRESHOLD': r'THRESHOLD\s*=\s*([\d.]+)',
                    'RISK_TOLERANCE': r'RISK_TOLERANCE\s*=\s*["\'](\w+)["\']',
                    'CAPITAL': r'CAPITAL\s*=\s*(\d+)',
                    'STOP_LOSS': r'STOP_LOSS\s*=\s*([\d.]+)',
                    'TAKE_PROFIT': r'TAKE_PROFIT\s*=\s*([\d.]+)',
                    'MAX_POSITION': r'MAX_POSITION\s*=\s*([\d.]+)',
                }

                for param_name, pattern in param_patterns.items():
                    match = re.search(pattern, source)
                    if match:
                        # Convert parameter name to lowercase
                        param_key = param_name.lower()
                        value = match.group(1)

                        # Type conversion
                        if param_key in int_params:
                            value = int(value)
                        elif param_key in float_params:
                            value = float(value)

                        params[param_key] = value

        return params

    async def sync_to_dashboard(self, user_id: str) -> Dict[str, Any]:
        """Sync strategies to PersonalStrategyDashboard

        Fetches all strategies for a user from the CBSC system.

        Args:
            user_id: User ID to sync strategies for

        Returns:
            Sync result with strategy count and list
        """

        headers = {}
        if self.cbsc_api_key:
            headers["Authorization"] = f"Bearer {self.cbsc_api_key}"

        response = await self.client.get(
            f"{self.cbsc_api_url}/api/users/{user_id}/strategies",
            headers=headers
        )

        response.raise_for_status()
        return response.json()

    async def validate_strategy_before_deployment(
        self,
        notebook_path: str
    ) -> Dict[str, Any]:
        """Validate strategy before deployment

        Performs validation checks on the notebook:
        - Valid JSON structure
        - Has required cells
        - Parameters are defined
        - No syntax errors

        Args:
            notebook_path: Path to the notebook

        Returns:
            Validation result with success status and errors
        """
        errors = []
        warnings = []

        try:
            # 1. Check file exists
            if not Path(notebook_path).exists():
                return {
                    "valid": False,
                    "errors": [f"Notebook file not found: {notebook_path}"]
                }

            # 2. Parse JSON
            with open(notebook_path, 'r') as f:
                notebook = json.load(f)

            # 3. Check nbformat version
            if notebook.get('nbformat') != 4:
                errors.append('Not a valid nbformat v4 notebook')

            # 4. Check for required cells
            cells = notebook.get('cells', [])
            if len(cells) == 0:
                errors.append('Notebook has no cells')

            # 5. Check for parameter definitions
            params = await self._extract_parameters(notebook_path)
            if len(params) == 0:
                warnings.append('No parameters found in notebook')
            else:
                # Check for essential parameters
                essential_params = ['symbol']
                missing_params = [p for p in essential_params if p not in params]
                if missing_params:
                    warnings.append(f'Missing essential parameters: {missing_params}')

            # 6. Validate Python syntax in code cells
            for i, cell in enumerate(cells):
                if cell['cell_type'] == 'code':
                    source = ''.join(cell.get('source', []))
                    if not source.strip():
                        continue

                    try:
                        compile(source, f'<cell {i}>', 'exec')
                    except SyntaxError as e:
                        errors.append(f'Cell {i}: {e}')

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "parameters_found": len(params)
            }

        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "errors": [f'Invalid JSON: {e}']
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f'Validation error: {e}']
            }

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Singleton instance for use in routers
cbsc_integration = CBSCIntegration()
