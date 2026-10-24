"""
Market data resource for CBSC Trading API SDK
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from ..models import Symbol, Quote, APIResponse
from ..client import CBSCClient


class MarketDataResource:
    """Resource for market data operations"""

    def __init__(self, client: CBSCClient):
        self.client = client

    def get_symbols(self, skip: int = 0, limit: int = 100) -> APIResponse:
        """
        Get list of available trading symbols

        Args:
            skip: Number of symbols to skip
            limit: Maximum number of symbols to return

        Returns:
            APIResponse: List of symbols
        """
        params = {"skip": skip, "limit": limit}
        response = self.client.get("/api/v1/market/symbols", params=params)
        response_data = response.json()

        # Convert symbol data to Symbol objects if needed
        if isinstance(response_data.get("data"), list):
            symbols = [Symbol(**symbol_data) for symbol_data in response_data["data"]]
            response_data["data"] = symbols

        return APIResponse(**response_data)

    def get_symbol(self, symbol: str) -> Symbol:
        """
        Get symbol information

        Args:
            symbol: Trading symbol

        Returns:
            Symbol: Symbol information
        """
        response = self.client.get(f"/api/v1/market/symbols/{symbol}")
        response_data = response.json()

        return Symbol(**response_data)

    def get_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get detailed data for a symbol

        Args:
            symbol: Trading symbol

        Returns:
            Dict: Detailed symbol data
        """
        response = self.client.get(f"/api/v1/market/symbols/{symbol}/data")
        return response.json()

    def get_symbol_quote(self, symbol: str) -> Quote:
        """
        Get real-time quote for a symbol

        Args:
            symbol: Trading symbol

        Returns:
            Quote: Real-time quote information
        """
        response = self.client.get(f"/api/v1/market/symbols/{symbol}/quote")
        response_data = response.json()

        return Quote(**response_data)

    def search_symbols(self, query: str, limit: int = 20) -> APIResponse:
        """
        Search for symbols by name or code

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            APIResponse: List of matching symbols
        """
        params = {"q": query, "limit": limit}
        response = self.client.get("/api/v1/market/symbols/search", params=params)
        response_data = response.json()

        # Convert symbol data to Symbol objects if needed
        if isinstance(response_data.get("data"), list):
            symbols = [Symbol(**symbol_data) for symbol_data in response_data["data"]]
            response_data["data"] = symbols

        return APIResponse(**response_data)

    def get_historical_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "1d",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get historical price data for a symbol

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval (1m, 5m, 15m, 1h, 1d, 1w, 1M)
            limit: Maximum number of data points

        Returns:
            List[Dict]: Historical price data
        """
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "interval": interval,
        }
        if limit:
            params["limit"] = limit

        response = self.client.get(f"/api/v1/market/symbols/{symbol}/historical", params=params)
        response_data = response.json()

        if isinstance(response_data.get("data"), list):
            return response_data["data"]
        else:
            return [response_data]