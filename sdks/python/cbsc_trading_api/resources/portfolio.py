"""
Portfolio resource for CBSC Trading API SDK
"""

from typing import Optional, List
from ..models import Portfolio, Position, Order, OrderCreate, APIResponse
from ..client import CBSCClient


class PortfolioResource:
    """Resource for portfolio management operations"""

    def __init__(self, client: CBSCClient):
        self.client = client

    def get_portfolio(self) -> Portfolio:
        """
        Get current portfolio information

        Returns:
            Portfolio: Portfolio information including positions and P&L
        """
        response = self.client.get("/api/v1/portfolio/")
        response_data = response.json()

        return Portfolio(**response_data)

    def get_positions(self) -> List[Position]:
        """
        Get current positions

        Returns:
            List[Position]: List of current positions
        """
        response = self.client.get("/api/v1/portfolio/positions")
        response_data = response.json()

        if isinstance(response_data.get("data"), list):
            positions = [Position(**pos_data) for pos_data in response_data["data"]]
            return positions
        else:
            return [Position(**response_data)]

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol

        Args:
            symbol: Trading symbol

        Returns:
            Optional[Position]: Position information or None if no position
        """
        try:
            response = self.client.get(f"/api/v1/portfolio/positions/{symbol}")
            response_data = response.json()
            return Position(**response_data)
        except Exception:
            return None

    def create_order(self, order_data: OrderCreate) -> Order:
        """
        Create a new order

        Args:
            order_data: Order creation data

        Returns:
            Order: Created order information
        """
        response = self.client.post("/api/v1/portfolio/orders", data=order_data.dict())
        response_data = response.json()

        return Order(**response_data)

    def get_orders(self, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> APIResponse:
        """
        Get list of orders with pagination

        Args:
            skip: Number of orders to skip
            limit: Maximum number of orders to return
            status: Filter by order status

        Returns:
            APIResponse: List of orders
        """
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status

        response = self.client.get("/api/v1/portfolio/orders", params=params)
        response_data = response.json()

        # Convert order data to Order objects if needed
        if isinstance(response_data.get("data"), list):
            orders = [Order(**order_data) for order_data in response_data["data"]]
            response_data["data"] = orders

        return APIResponse(**response_data)

    def get_order(self, order_id: int) -> Order:
        """
        Get order by ID

        Args:
            order_id: Order ID

        Returns:
            Order: Order information
        """
        response = self.client.get(f"/api/v1/portfolio/orders/{order_id}")
        response_data = response.json()

        return Order(**response_data)

    def cancel_order(self, order_id: int) -> Order:
        """
        Cancel an order

        Args:
            order_id: Order ID

        Returns:
            Order: Updated order information
        """
        response = self.client.delete(f"/api/v1/portfolio/orders/{order_id}")
        response_data = response.json()

        return Order(**response_data)