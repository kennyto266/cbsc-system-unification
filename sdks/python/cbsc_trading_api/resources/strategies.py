"""
Strategies resource for CBSC Trading API SDK
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models import Strategy, StrategyCreate, Backtest, APIResponse
from ..client import CBSCClient


class StrategiesResource:
    """Resource for strategy management operations"""

    def __init__(self, client: CBSCClient):
        self.client = client

    def get_strategies(self, skip: int = 0, limit: int = 100) -> APIResponse:
        """
        Get list of strategies with pagination

        Args:
            skip: Number of strategies to skip
            limit: Maximum number of strategies to return

        Returns:
            APIResponse: List of strategies
        """
        params = {"skip": skip, "limit": limit}
        response = self.client.get("/api/v1/strategies/", params=params)
        response_data = response.json()

        # Convert strategy data to Strategy objects if needed
        if isinstance(response_data.get("data"), list):
            strategies = [Strategy(**strategy_data) for strategy_data in response_data["data"]]
            response_data["data"] = strategies

        return APIResponse(**response_data)

    def get_strategy(self, strategy_id: int) -> Strategy:
        """
        Get strategy by ID

        Args:
            strategy_id: Strategy ID

        Returns:
            Strategy: Strategy information
        """
        response = self.client.get(f"/api/v1/strategies/{strategy_id}")
        response_data = response.json()

        return Strategy(**response_data)

    def create_strategy(self, strategy_data: StrategyCreate) -> Strategy:
        """
        Create a new strategy

        Args:
            strategy_data: Strategy creation data

        Returns:
            Strategy: Created strategy information
        """
        response = self.client.post("/api/v1/strategies/", data=strategy_data.dict())
        response_data = response.json()

        return Strategy(**response_data)

    def update_strategy(self, strategy_id: int, strategy_data: dict) -> Strategy:
        """
        Update strategy information

        Args:
            strategy_id: Strategy ID
            strategy_data: Updated strategy data

        Returns:
            Strategy: Updated strategy information
        """
        response = self.client.put(f"/api/v1/strategies/{strategy_id}", data=strategy_data)
        response_data = response.json()

        return Strategy(**response_data)

    def delete_strategy(self, strategy_id: int) -> bool:
        """
        Delete a strategy

        Args:
            strategy_id: Strategy ID

        Returns:
            bool: True if deletion successful
        """
        response = self.client.delete(f"/api/v1/strategies/{strategy_id}")
        return response.status_code == 200

    def backtest_strategy(
        self,
        strategy_id: int,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
        config: Optional[Dict[str, Any]] = None,
    ) -> Backtest:
        """
        Run backtest for a strategy

        Args:
            strategy_id: Strategy ID
            symbol: Trading symbol
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital for backtest
            config: Additional backtest configuration

        Returns:
            Backtest: Backtest results
        """
        backtest_data = {
            "symbol": symbol,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "initial_capital": initial_capital,
            "config": config or {},
        }

        response = self.client.post(f"/api/v1/strategies/{strategy_id}/backtest", data=backtest_data)
        response_data = response.json()

        return Backtest(**response_data)

    def get_strategy_performance(self, strategy_id: int) -> Dict[str, Any]:
        """
        Get strategy performance metrics

        Args:
            strategy_id: Strategy ID

        Returns:
            Dict: Performance metrics
        """
        response = self.client.get(f"/api/v1/strategies/{strategy_id}/performance")
        return response.json()