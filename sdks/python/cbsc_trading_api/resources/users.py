"""
Users resource for CBSC Trading API SDK
"""

from typing import Optional, List
from ..models import User, UserCreate, APIResponse
from ..client import CBSCClient


class UsersResource:
    """Resource for user management operations"""

    def __init__(self, client: CBSCClient):
        self.client = client

    def get_users(self, skip: int = 0, limit: int = 100) -> APIResponse:
        """
        Get list of users with pagination

        Args:
            skip: Number of users to skip
            limit: Maximum number of users to return

        Returns:
            APIResponse: List of users
        """
        params = {"skip": skip, "limit": limit}
        response = self.client.get("/api/v1/users/", params=params)
        response_data = response.json()

        # Convert user data to User objects if needed
        if isinstance(response_data.get("data"), list):
            users = [User(**user_data) for user_data in response_data["data"]]
            response_data["data"] = users

        return APIResponse(**response_data)

    def get_user(self, user_id: int) -> User:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User: User information
        """
        response = self.client.get(f"/api/v1/users/{user_id}")
        response_data = response.json()

        return User(**response_data)

    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user

        Args:
            user_data: User creation data

        Returns:
            User: Created user information
        """
        response = self.client.post("/api/v1/users/", data=user_data.dict())
        response_data = response.json()

        return User(**response_data)

    def update_user(self, user_id: int, user_data: dict) -> User:
        """
        Update user information

        Args:
            user_id: User ID
            user_data: Updated user data

        Returns:
            User: Updated user information
        """
        response = self.client.put(f"/api/v1/users/{user_id}", data=user_data)
        response_data = response.json()

        return User(**response_data)

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user

        Args:
            user_id: User ID

        Returns:
            bool: True if deletion successful
        """
        response = self.client.delete(f"/api/v1/users/{user_id}")
        return response.status_code == 200