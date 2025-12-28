"""
Backtests resource for CBSC Trading API SDK
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models import Backtest, BacktestCreate, APIResponse
from ..client import CBSCClient


class BacktestsResource:
    """Resource for backtest operations"""

    def __init__(self, client: CBSCClient):
        self.client = client

    def create_backtest(self, backtest_data: BacktestCreate) -> Backtest:
        """
        Create a new backtest

        Args:
            backtest_data: Backtest creation data

        Returns:
            Backtest: Created backtest information
        """
        data = backtest_data.dict()
        # Convert datetime objects to ISO format strings
        if isinstance(data.get("start_date"), datetime):
            data["start_date"] = data["start_date"].isoformat()
        if isinstance(data.get("end_date"), datetime):
            data["end_date"] = data["end_date"].isoformat()

        response = self.client.post("/api/v1/backtests/", data=data)
        response_data = response.json()

        return Backtest(**response_data)

    def get_backtests(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> APIResponse:
        """
        Get list of backtests with pagination

        Args:
            skip: Number of backtests to skip
            limit: Maximum number of backtests to return
            status: Filter by backtest status

        Returns:
            APIResponse: List of backtests
        """
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status

        response = self.client.get("/api/v1/backtests/", params=params)
        response_data = response.json()

        # Convert backtest data to Backtest objects if needed
        if isinstance(response_data.get("data"), list):
            backtests = [Backtest(**backtest_data) for backtest_data in response_data["data"]]
            response_data["data"] = backtests

        return APIResponse(**response_data)

    def get_backtest(self, backtest_id: int) -> Backtest:
        """
        Get backtest by ID

        Args:
            backtest_id: Backtest ID

        Returns:
            Backtest: Backtest information
        """
        response = self.client.get(f"/api/v1/backtests/{backtest_id}")
        response_data = response.json()

        return Backtest(**response_data)

    def delete_backtest(self, backtest_id: int) -> bool:
        """
        Delete a backtest

        Args:
            backtest_id: Backtest ID

        Returns:
            bool: True if deletion successful
        """
        response = self.client.delete(f"/api/v1/backtests/{backtest_id}")
        return response.status_code == 200

    def cancel_backtest(self, backtest_id: int) -> Backtest:
        """
        Cancel a running backtest

        Args:
            backtest_id: Backtest ID

        Returns:
            Backtest: Updated backtest information
        """
        response = self.client.post(f"/api/v1/backtests/{backtest_id}/cancel")
        response_data = response.json()

        return Backtest(**response_data)

    def get_backtest_results(self, backtest_id: int) -> Dict[str, Any]:
        """
        Get detailed backtest results including trades

        Args:
            backtest_id: Backtest ID

        Returns:
            Dict: Detailed backtest results
        """
        response = self.client.get(f"/api/v1/backtests/{backtest_id}/results")
        return response.json()

    def get_backtest_trades(self, backtest_id: int) -> List[Dict[str, Any]]:
        """
        Get list of trades from a backtest

        Args:
            backtest_id: Backtest ID

        Returns:
            List[Dict]: List of trades
        """
        response = self.client.get(f"/api/v1/backtests/{backtest_id}/trades")
        response_data = response.json()

        if isinstance(response_data.get("data"), list):
            return response_data["data"]
        else:
            return [response_data]