""" 修改 auth.py 添加免密用户在 MOCK_USERS 列表中添加以下用户："""

MOCK_USERS = [ # ... 现有用户 ...

    {
        "id": "user_3",
        "username": "guest",
        "email": "guest@cbsc.com",
        "password_hash": "",  # 空密码 - 免密登录
        "full_name": "访客用户（免密）",
        "role": UserRole.USER,
        "is_active": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "last_login": None
    }

]

# 然后修改登录逻辑，允许空密码
