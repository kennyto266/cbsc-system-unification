"""
Users API Routes
用戶 API 路由

User management endpoints
用戶管理端點
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from core.logging import logger

router = APIRouter()


class UserBase(BaseModel):
    """Base user model"""
    username: str
    email: str
    is_active: bool = True


class UserCreate(UserBase):
    """User creation model"""
    password: str


class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """User response model"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Mock data storage
mock_users = [
    {
        "id": 1,
        "username": "admin",
        "email": "admin@cbsc.example.com",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    {
        "id": 2,
        "username": "trader1",
        "email": "trader1@cbsc.example.com",
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]


@router.get("/", response_model=List[User])
async def get_users():
    """
    Get all users
    獲取所有用戶
    """
    logger.info("Getting all users")
    return [User(**user) for user in mock_users]


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int):
    """
    Get a specific user by ID
    根據ID獲取特定用戶
    """
    logger.info(f"Getting user: {user_id}")

    user = next((u for u in mock_users if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return User(**user)


@router.post("/", response_model=User)
async def create_user(user: UserCreate):
    """
    Create a new user
    創建新用戶
    """
    logger.info(f"Creating user: {user.username}")

    # Check if username already exists
    if any(u["username"] == user.username for u in mock_users):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email already exists
    if any(u["email"] == user.email for u in mock_users):
        raise HTTPException(status_code=400, detail="Email already exists")

    new_id = max(u["id"] for u in mock_users) + 1
    new_user = {
        "id": new_id,
        **user.dict(exclude={"password"}),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    mock_users.append(new_user)
    return User(**new_user)


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate):
    """
    Update an existing user
    更新現有用戶
    """
    logger.info(f"Updating user: {user_id}")

    user_index = next((i for i, u in enumerate(mock_users) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user
    for field, value in user.dict(exclude_unset=True).items():
        mock_users[user_index][field] = value
    mock_users[user_index]["updated_at"] = datetime.now()

    return User(**mock_users[user_index])


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """
    Delete a user
    刪除用戶
    """
    logger.info(f"Deleting user: {user_id}")

    user_index = next((i for i, u in enumerate(mock_users) if u["id"] == user_id), None)
    if user_index is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_id == 1:  # Don't delete admin user
        raise HTTPException(status_code=400, detail="Cannot delete admin user")

    mock_users.pop(user_index)
    return {"success": True, "message": "User deleted successfully"}