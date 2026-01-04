# Backend 项目知识库

**Generated:** 2025-01-03 **System:** FastAPI 用户管理系统

## OVERVIEW

FastAPI后端系统，提供用户管理、身份认证、JWT授权、数据库操作等核心API服务。使用PostgreSQL持久化，Redis缓存，支持WebSocket实时通信。

## STRUCTURE

```
backend/
├── 📡 API路由
│   └── api/                                        # FastAPI路由
│       ├── users/                                    # 用户CRUD
│       ├── auth/                                     # 认证端点
│       └── strategies/                               # 策略管理
├── 🔐 核心模块
│   └── core/                                       # 核心业务逻辑
│       ├── security/                                 # JWT、密码哈希
│       ├── dependencies/                              # 依赖注入
│       └── config/                                   # 配置管理
├── 🗄️ 数据模型
│   └── models/                                     # SQLAlchemy ORM
│       ├── user.py                                   # 用户模型
│       ├── role.py                                   # 角色模型
│       └── strategy.py                               # 策略模型
├── 📋 数据架构
│   └── schemas/                                    # Pydantic schemas
│       ├── user.py                                   # 用户请求/响应
│       └── auth.py                                   # 认证schemas
├── 🔧 配置
│   └── config/                                     # 环境配置
├── 🔌 中间件
│   └── middleware/                                 # 自定义中间件
├── 🧪 测试
│   └── tests/                                      # pytest测试
│       ├── unit/                                    # 单元测试
│       └── integration/                             # 集成测试
└── 🗂️ 数据库迁移
    └── alembic/                                    # Alembic迁移
```

## WHERE TO LOOK

| Task             | Location            | Notes                |
| ---------------- | ------------------- | -------------------- |
| API端点          | `api/`              | FastAPI路由定义      |
| 业务逻辑         | `core/`             | 核心服务层           |
| 数据模型         | `models/`           | SQLAlchemy表定义     |
| 请求/响应schemas | `schemas/`          | Pydantic验证         |
| 配置             | `config/`           | 环境变量、数据库配置 |
| 认证逻辑         | `core/security/`    | JWT、密码哈希        |
| 数据库迁移       | `alembic/versions/` | 迁移脚本             |
| 测试             | `tests/`            | pytest测试套件       |

## CONVENTIONS

**API设计：**

- RESTful风格：`GET /api/users`, `POST /api/auth/login`
- 统一响应格式：`{success, data/error, message, timestamp}`
- 状态码：200(成功), 201(创建), 400(验证错误), 401(未认证), 403(禁止),
  404(未找到), 500(服务器错误)
- 异常处理：自定义HTTPException，详细错误信息

**代码风格：**

- FastAPI 0.104+
- SQLAlchemy 2.0+ (异步)
- Pydantic V2 (严格模式)
- 类型提示：所有函数必须有类型提示
- 异步编程：async/await优先

**命名规范：**

- 路由函数：`router_name_endpoint` (例：`get_user_by_id`)
- 模型类：PascalCase (例：`User`, `Strategy`)
- Pydantic schemas：PascalCase + 后缀 (例：`UserCreate`, `UserResponse`)
- 变量/函数：snake_case (例：`get_user_id`)

## ANTI-PATTERNS (THIS PROJECT)

- ❌ **不要**在路由函数中直接操作数据库 - 使用依赖注入和service层
- ❌ **不要**暴露敏感信息 - 密码、token等必须在响应中过滤
- ❌ **不要**使用同步数据库操作 - 必须使用异步SQLAlchemy
- ❌ **不要**硬编码配置 - 必须使用环境变量
- ❌ **不要**忽略异常 - 必须记录日志并返回用户友好错误

## UNIQUE STYLES

**认证流程：**

```python
# 1. 用户登录
POST /api/auth/login
Request: {username, password}
Response: {access_token, refresh_token, user_info}

# 2. JWT验证
Header: Authorization: Bearer {access_token}
Middleware验证token有效性和权限

# 3. Token刷新
POST /api/auth/refresh
Request: {refresh_token}
Response: {new_access_token}
```

**依赖注入：**

```python
from core.dependencies import get_db, get_current_user

@router.get("/users/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return UserResponse.from_orm(current_user)
```

**统一响应格式：**

```python
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    # 创建用户...
    return {
        "success": True,
        "data": user_response,
        "message": "用户创建成功",
        "timestamp": datetime.utcnow()
    }
```

## COMMANDS

```bash
# 启动开发服务器
uvicorn main:app --reload --port 3004

# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成测试覆盖率
pytest --cov=backend --cov=src --cov-report=html

# 数据库迁移
alembic upgrade head

# 创建新迁移
alembic revision --autogenerate -m "description"

# 代码格式化
black backend/
isort backend/

# 类型检查
mypy backend/
```

## NOTES

**关键配置：**

- 数据库：PostgreSQL (asyncpg驱动)
- 缓存：Redis (用于session和缓存)
- JWT：RS256签名，access_token有效期15分钟，refresh_token7天
- CORS：允许指定origin (生产环境严格配置)

**数据库连接：**

- 连接池：SQLAlchemy引擎配置
- 异步会话：`AsyncSession`
- 事务：`async with db:` 自动提交/回滚

**安全考虑：**

- 密码：Argon2id哈希
- JWT：密钥存储在环境变量
- CORS：限制允许的来源
- 输入验证：Pydantic schemas强制验证
- SQL注入防护：SQLAlchemy ORM参数化查询

**测试策略：**

- 单元测试：mock数据库，测试业务逻辑
- 集成测试：使用测试数据库（testcontainers或本地PostgreSQL）
- API测试：TestClient模拟HTTP请求

**与前端集成：**

- API base URL：`http://localhost:3004`
- WebSocket：`ws://localhost:3004/ws`
- 文档：自动生成Swagger UI (`/docs`)

**日志：**

- 使用Python logging模块
- 分级：DEBUG, INFO, WARNING, ERROR, CRITICAL
- 输出：文件 + 控制台（开发环境）
