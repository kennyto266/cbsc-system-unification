"""
用户管理API模块 - 提供用户管理相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import hashlib

router = APIRouter()

# 模拟用户数据
MOCK_USERS = [
    {
        "id": "user_1",
        "username": "admin",
        "email": "admin@cbsc.com",
        "full_name": "系统管理员",
        "role": "admin",
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "last_login": "2024-01-20T09:15:00Z",
        "api_usage": {
            "total_requests": 15000,
            "requests_this_month": 2500,
            "last_request": "2024-01-22T14:30:00Z"
        }
    },
    {
        "id": "user_2",
        "username": "developer001",
        "email": "dev001@company.com",
        "full_name": "张三",
        "role": "developer",
        "is_active": True,
        "created_at": "2024-01-05T00:00:00Z",
        "updated_at": "2024-01-18T16:45:00Z",
        "last_login": "2024-01-21T11:20:00Z",
        "api_usage": {
            "total_requests": 8500,
            "requests_this_month": 1200,
            "last_request": "2024-01-22T13:45:00Z"
        }
    },
    {
        "id": "user_3",
        "username": "trader001",
        "email": "trader001@firm.com",
        "full_name": "李四",
        "role": "user",
        "is_active": True,
        "created_at": "2024-01-10T00:00:00Z",
        "updated_at": "2024-01-12T09:30:00Z",
        "last_login": "2024-01-22T08:00:00Z",
        "api_usage": {
            "total_requests": 3200,
            "requests_this_month": 450,
            "last_request": "2024-01-22T12:15:00Z"
        }
    }
]

@router.get("/users")
async def get_users(role: Optional[str] = None, is_active: Optional[bool] = None, skip: int = 0, limit: int = 50):
    """获取用户列表"""
    users = MOCK_USERS.copy()

    # 过滤条件
    if role:
        users = [u for u in users if u["role"] == role]
    if is_active is not None:
        users = [u for u in users if u["is_active"] == is_active]

    # 分页
    total = len(users)
    users = users[skip:skip + limit]

    return {
        "success": True,
        "data": {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        },
        "message": "用户列表获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """获取用户详情"""
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "success": True,
        "data": user,
        "message": "用户详情获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/users")
async def create_user(request: Dict[str, Any]):
    """创建用户"""
    try:
        username = request.get("username")
        email = request.get("email")
        password = request.get("password")
        full_name = request.get("full_name", "")
        role = request.get("role", "user")

        # 验证必填字段
        if not all([username, email, password]):
            raise HTTPException(status_code=400, detail="用户名、邮箱和密码不能为空")

        # 检查用户名是否已存在
        if any(u["username"] == username for u in MOCK_USERS):
            raise HTTPException(status_code=409, detail="用户名已存在")

        # 检查邮箱是否已存在
        if any(u["email"] == email for u in MOCK_USERS):
            raise HTTPException(status_code=409, detail="邮箱已存在")

        # 创建新用户
        new_user = {
            "id": f"user_{uuid.uuid4().hex[:8]}",
            "username": username,
            "email": email,
            "full_name": full_name,
            "role": role,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_login": None,
            "api_usage": {
                "total_requests": 0,
                "requests_this_month": 0,
                "last_request": None
            }
        }

        MOCK_USERS.append(new_user)

        # 返回时不包含密码
        user_response = new_user.copy()

        return {
            "success": True,
            "data": user_response,
            "message": "用户创建成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")

@router.put("/users/{user_id}")
async def update_user(user_id: str, request: Dict[str, Any]):
    """更新用户信息"""
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    try:
        # 更新用户信息
        if "email" in request:
            # 检查邮箱是否已被其他用户使用
            if any(u["email"] == request["email"] and u["id"] != user_id for u in MOCK_USERS):
                raise HTTPException(status_code=409, detail="邮箱已被使用")
            user["email"] = request["email"]

        if "full_name" in request:
            user["full_name"] = request["full_name"]

        if "role" in request:
            user["role"] = request["role"]

        if "is_active" in request:
            user["is_active"] = request["is_active"]

        user["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "data": user,
            "message": "用户信息更新成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新用户信息失败: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """删除用户"""
    global MOCK_USERS
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能删除管理员用户
    if user["role"] == "admin":
        raise HTTPException(status_code=403, detail="不能删除管理员用户")

    MOCK_USERS = [u for u in MOCK_USERS if u["id"] != user_id]

    return {
        "success": True,
        "message": "用户删除成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/users/{user_id}/activate")
async def activate_user(user_id: str):
    """激活用户"""
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user["is_active"]:
        raise HTTPException(status_code=400, detail="用户已经激活")

    user["is_active"] = True
    user["updated_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "data": user,
        "message": "用户激活成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str):
    """停用用户"""
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if not user["is_active"]:
        raise HTTPException(status_code=400, detail="用户已经停用")

    # 不能停用管理员用户
    if user["role"] == "admin":
        raise HTTPException(status_code=403, detail="不能停用管理员用户")

    user["is_active"] = False
    user["updated_at"] = datetime.now().isoformat()

    return {
        "success": True,
        "data": user,
        "message": "用户停用成功",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/users/{user_id}/api-usage")
async def get_user_api_usage(user_id: str):
    """获取用户API使用统计"""
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "success": True,
        "data": user.get("api_usage", {}),
        "message": "用户API使用统计获取成功",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, request: Dict[str, Any]):
    """重置用户密码"""
    user = next((u for u in MOCK_USERS if u["id"] == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    try:
        new_password = request.get("new_password")
        if not new_password or len(new_password) < 8:
            raise HTTPException(status_code=400, detail="新密码长度至少8位")

        # 在实际应用中，这里应该对密码进行哈希处理
        # 这里只是模拟，不存储实际密码
        user["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "message": "密码重置成功",
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置密码失败: {str(e)}")

@router.get("/users/stats")
async def get_users_stats():
    """获取用户统计信息"""
    total_users = len(MOCK_USERS)
    active_users = len([u for u in MOCK_USERS if u["is_active"]])

    # 计算今日新增用户（模拟）
    today = datetime.now().date()
    new_users_today = len([
        u for u in MOCK_USERS
        if datetime.fromisoformat(u["created_at"]).date() == today
    ])

    # 按角色分组统计
    users_by_role = {}
    for user in MOCK_USERS:
        role = user["role"]
        users_by_role[role] = users_by_role.get(role, 0) + 1

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "new_users_today": new_users_today,
        "users_by_role": users_by_role
    }

    return {
        "success": True,
        "data": stats,
        "message": "用户统计信息获取成功",
        "timestamp": datetime.now().isoformat()
    }