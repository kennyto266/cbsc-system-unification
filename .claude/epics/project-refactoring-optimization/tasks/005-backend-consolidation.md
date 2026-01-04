---
name: backend-consolidation
title: 後端 API 統一與數據模型整合
status: in-progress
phase: 3
priority: P0
created: 2025-12-24T12:05:52Z
updated: 2025-12-25T00:10:00Z
estimated_hours: 96
actual_hours: 6
progress: 40%
assignee: TBD
dependencies: ["003-dev-environment"]
github:
  issue: 77
  url: https://github.com/kennyto266/cbsc-system-unification/issues/77
---

# Task 005: 後端 API 統一與數據模型整合

## 概述

合併 backend/ 和 src/api/ 的重複 API 實現，整合數據模型定義，建立清晰的 API 分層架構。

## 詳細描述

### 新後端結構

```
backend/
├── api/                          # API 層 (端點)
│   ├── v1/                       # API v1 (向後兼容)
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── strategies/
│   │   ├── backtests/
│   │   └── users/
│   └── v2/                       # API v2 (新架構)
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── routes.py
│       │   └── schemas.py
│       ├── strategies/
│       │   ├── __init__.py
│       │   ├── routes.py
│       │   └── schemas.py
│       └── backtests/
├── core/                         # 核心配置
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   └── security.py
├── models/                       # 數據模型 (統一)
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── strategy.py
│   ├── backtest.py
│   └── portfolio.py
├── services/                     # 服務層 (業務邏輯)
│   ├── __init__.py
│   ├── auth_service.py
│   ├── strategy_service.py
│   ├── backtest_service.py
│   └── data_service.py
├── schemas/                      # 請求/響應模式
│   ├── __init__.py
│   ├── auth.py
│   ├── strategy.py
│   └── common.py
├── middleware/                   # 中間件
│   ├── __init__.py
│   ├── auth.py
│   ├── rate_limit.py
│   └── error_handler.py
├── utils/                        # 工具函數
│   ├── __init__.py
│   ├── validators.py
│   └── helpers.py
└── main.py                       # 應用入口

src/
├── strategies/                   # 策略實現 (保持)
├── backtest/                     # 回測引擎 (保持)
├── trading/                      # 交易執行 (保持)
└── websocket/                    # WebSocket (保持)
```

### API 端點統一

#### 1. 端點映射表

| 舊端點 (backend/) | 舊端點 (src/api/) | 新端點 (v1) | 新端點 (v2) | 狀態 |
|-------------------|-------------------|-------------|-------------|------|
| `/api/auth/login` | `/auth/login` | `/api/v1/auth/login` | `/api/v2/auth/login` | 合併 |
| `/api/strategies` | `/strategies/v2/` | `/api/v1/strategies` | `/api/v2/strategies` | 合併 |
| `/api/backtests` | - | `/api/v1/backtests` | `/api/v2/backtests` | 保留 |
| - | `/api/data/` | - | `/api/v2/data` | 遷移 |

#### 2. API v1 實現 (向後兼容)

```python
# backend/api/v1/auth/routes.py
from fastapi import APIRouter, HTTPException, Depends
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/login", response_model=TokenResponse)
async def login_v1(
    credentials: LoginRequest,
    service: AuthService = Depends(lambda: auth_service)
):
    """Legacy v1 login endpoint - redirects to v2 service"""
    return await service.login(credentials.username, credentials.password)

@router.post("/refresh")
async def refresh_v1(token: str):
    """Legacy v1 refresh endpoint"""
    return await auth_service.refresh_token(token)
```

#### 3. API v2 實現 (新架構)

```python
# backend/api/v2/auth/routes.py
from fastapi import APIRouter, Depends, status
from backend.schemas.auth import LoginRequest, TokenResponse, UserResponse
from backend.services.auth_service import AuthService
from backend.middleware.auth import get_current_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_v2(
    credentials: LoginRequest,
    service: AuthService = Depends()
) -> TokenResponse:
    """
    Authenticate user and return access token

    - **username**: User username or email
    - **password**: User password
    """
    return await service.login(credentials.username, credentials.password)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_v2(
    refresh_token: str,
    service: AuthService = Depends()
) -> TokenResponse:
    """Refresh access token using refresh token"""
    return await service.refresh_token(refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user"""
    return current_user
```

### 數據模型整合

#### 1. 基礎模型類

```python
# backend/models/base.py
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Base model for all database models"""
    pass

class TimestampMixin:
    """Mixin for adding timestamp fields"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

#### 2. 用戶模型

```python
# backend/models/user.py
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
```

#### 3. 策略模型

```python
# backend/models/strategy.py
from sqlalchemy import String, Integer, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.models.base import Base, TimestampMixin
from backend.models.user import User

class Strategy(Base, TimestampMixin):
    """Strategy model"""
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    # Relationships
    user: Mapped[User] = relationship("User", backref="strategies")

    def __repr__(self) -> str:
        return f"<Strategy(id={self.id}, name='{self.name}', status='{self.status}')>"
```

### 服務層設計

```python
# backend/services/strategy_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.strategy import Strategy
from backend.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyResponse

class StrategyService:
    """Strategy business logic service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: int,
        data: StrategyCreate
    ) -> StrategyResponse:
        """Create a new strategy"""
        strategy = Strategy(
            user_id=user_id,
            name=data.name,
            description=data.description,
            config=data.config,
            status="draft"
        )
        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)
        return StrategyResponse.model_validate(strategy)

    async def get_by_id(
        self,
        strategy_id: int,
        user_id: int
    ) -> Optional[StrategyResponse]:
        """Get strategy by ID with user ownership check"""
        strategy = await self.db.get(Strategy, strategy_id)
        if strategy and strategy.user_id == user_id:
            return StrategyResponse.model_validate(strategy)
        return None

    async def list(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[StrategyResponse]:
        """List user's strategies"""
        from sqlalchemy import select
        result = await self.db.execute(
            select(Strategy)
            .where(Strategy.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        strategies = result.scalars().all()
        return [StrategyResponse.model_validate(s) for s in strategies]
```

## 驗收標準

### 交付物

- [ ] **統一的 API 結構**
  - backend/api/v1/ (向後兼容)
  - backend/api/v2/ (新架構)
  - API 路由註冊

- [ ] **整合的數據模型**
  - backend/models/ (統一模型)
  - 遷移腳本 (從 src/models/)

- [ ] **服務層實現**
  - backend/services/ (業務邏輯)
  - 依賴注入配置

- [ ] **API 文檔**
  - OpenAPI/Swagger 文檔
  - 端點映射表

### 質量門檻

- API 測試覆蓋 > 80%
- 無端點衝突
- 數據模型一致性
- 向後兼容性保證

## 技術實現

### FastAPI 應用配置

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1 import auth as auth_v1
from backend.api.v2 import auth as auth_v2, strategies as strategies_v2

app = FastAPI(
    title="CBSC Trading API",
    description="CBSC Quantitative Trading Strategy Management System",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 (legacy - backward compatibility)
app.include_router(
    auth_v1.router,
    prefix="/api/v1/auth",
    tags=["Authentication v1"]
)

# API v2 (new architecture)
app.include_router(
    auth_v2.router,
    prefix="/api/v2/auth",
    tags=["Authentication v2"]
)
app.include_router(
    strategies_v2.router,
    prefix="/api/v2/strategies",
    tags=["Strategies v2"]
)
```

## 依賴關係

### 前置任務
- Task 003: 開發環境設置

### 並行任務
- Task 004: 前端統一 (可並行)

### 後續任務
- Task 006: 依賴注入實現

## 執行步驟

1. **第 1-3 天: API 結構設計**
   - 設計 API v1/v2 結構
   - 創建端點映射表
   - 配置路由註冊

2. **第 4-7 天: 數據模型整合**
   - 合併 backend/models/ 和 src/models/
   - 創建遷移腳本
   - 更新服務層引用

3. **第 8-12 天: 服務層實現**
   - 實現核心服務
   - 配置依賴注入
   - 編寫服務測試

4. **第 13-15 天: 測試和文檔**
   - API 測試
   - OpenAPI 文檔生成
   - 性能測試

## 風險與緩解

| 風險 | 緩解措施 |
|------|----------|
| 端點衝突 | 版本前綴隔離，路由驗證 |
| 數據模型不一致 | 遷移腳本驗證，回歸測試 |
| 向後兼容性破壞 | API v1 保持不變，客戶端遷移指南 |

## 執行進度 (2025-12-24)

### 已完成 ✅

1. **API 結構設計** ✅
   - 創建 API v1/v2 目錄結構
   - 定義端點映射和版本策略

2. **核心配置層** ✅
   - `core/config.py` - Pydantic settings
   - `core/database.py` - Async database 連接
   - `core/security.py` - JWT 和密碼管理

3. **數據模型層** ✅
   - `models/base.py` - 基礎模型類
   - `models/user.py` - 用戶模型
   - `models/strategy.py` - 策略模型
   - `models/backtest.py` - 回測模型

4. **Schema 定義** ✅
   - `schemas/common.py` - 通用 schema
   - `schemas/auth.py` - 認證 schema
   - `schemas/strategy.py` - 策略 schema
   - `schemas/backtest.py` - 回測 schema

5. **服務層** ✅
   - `services/auth_service.py` - 認證業務邏輯
   - `services/strategy_service.py` - 策略業務邏輯
   - `services/backtest_service.py` - 回測業務邏輯

6. **API v2 路由** ✅
   - `api/v2/auth/routes.py` - 認證端點
   - `api/v2/strategies/routes.py` - 策略端點
   - `api/v2/backtests/routes.py` - 回測端點

7. **API v1 路由** ✅
   - `api/v1/auth/routes.py` - 向後兼容認證端點
   - `api/v1/strategies/routes.py` - 向後兼容策略端點

8. **中間件** ✅
   - `middleware/auth.py` - JWT 認證中間件

9. **統一入口** ✅
   - `main_v2.py` - 統一應用入口 (整合 v1/v2 + WebSocket)

### 待完成 ⏳

1. **數據庫遷移** (P0)
   - 創建 Alembic 遷移腳本
   - 從 src/models/ 遷移數據

2. **依賴安裝** (P0)
   - 安裝新依賴: pydantic-settings, python-jose, passlib, aiosqlite

3. **API 測試** (P1)
   - 單元測試
   - 集成測試
   - 端點測試

4. **文檔** (P2)
   - OpenAPI 文檔
   - 遷移指南
