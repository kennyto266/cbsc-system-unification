# CBSC 交易系統測試計劃

**創建日期**: 2025-12-24T12:26:09Z
**狀態**: 草案
**版本**: 1.0

---

## 1. 測試概述

### 1.1 測試目標

- 驗證重構後系統功能完整性
- 確保向後兼容性
- 驗證性能基準
- 確保數據完整性
- 驗證安全合規性

### 1.2 測試範圍

| 層級 | 範圍 | 優先級 |
|------|------|--------|
| **單元測試** | 所有 Python 和 TypeScript 模組 | P0 |
| **集成測試** | API 端點、數據庫、外部服務 | P0 |
| **端到端測試** | 關鍵業務流程 | P0 |
| **性能測試** | API 響應、併發、負載 | P1 |
| **安全測試** | 認證、授權、數據保護 | P0 |
| **兼容性測試** | 舊 API 版本兼容性 | P1 |

### 1.3 測試目標

| 指標 | 目標 | 測量方法 |
|------|------|----------|
| **代碼覆蓋率 (後端)** | > 85% | pytest-cov |
| **代碼覆蓋率 (前端)** | > 80% | Vitest |
| **API 測試覆蓋** | 100% | Postman/Newman |
| **關鍵流程覆蓋** | 100% | Playwright |
| **缺陷密度** | < 5/KLOC | Bug 追蹤 |

---

## 2. 測試環境

### 2.1 環境配置

```
┌─────────────────────────────────────────────────────────────┐
│                     測試環境架構                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  開發環境    │    │  測試環境    │    │  預生產環境   │  │
│  │  (Development)│   │  (Staging)   │    │  (Pre-prod)   │  │
│  │              │    │              │    │              │  │
│  │  - 本地運行  │    │  - CI/CD    │    │  - 生產配置   │  │
│  │  - 熱重載    │    │  - 自動測試 │    │  - 性能測試   │  │
│  │  - 調試工具  │    │  - 模擬數據 │    │  - 壓力測試   │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 環境變量配置

```bash
# tests/.env.test
# 測試環境配置

# Database
DB_URL=postgresql://localhost:5432/cbsc_test
DB_HOST=localhost
DB_PORT=5432
DB_USER=cbsc_test
DB_PASSWORD=test_password
DB_NAME=cbsc_test

# Redis
REDIS_URL=redis://localhost:6379/1
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1

# API
API_PORT=3005
API_HOST=127.0.0.1
API_WORKERS=1

# Testing
TEST_MODE=true
LOG_LEVEL=DEBUG
LOG_FILE_PATH=tests/logs/test.log

# External Services (Mocked)
MOCK_EXTERNAL_SERVICES=true
```

### 2.3 Docker 測試環境

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  postgres-test:
    image: postgres:15
    environment:
      POSTGRES_DB: cbsc_test
      POSTGRES_USER: cbsc_test
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cbsc_test"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  test-runner:
    build:
      context: .
      dockerfile: docker/Dockerfile.test
    environment:
      - DB_URL=postgresql://postgres-test:5432/cbsc_test
      - REDIS_URL=redis://redis-test:6379/1
    depends_on:
      postgres-test:
        condition: service_healthy
      redis-test:
        condition: service_healthy
    volumes:
      - ./tests:/app/tests
      - ./src:/app/src
    command: pytest tests/ -v --cov=src
```

---

## 3. 單元測試

### 3.1 後端單元測試

#### 3.1.1 測試框架

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.models.base import Base
from src.core.database import get_db

# 測試數據庫引擎
TEST_DATABASE_URL = "postgresql://localhost:5432/cbsc_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """創建測試數據庫會話"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """創建測試客戶端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

@pytest.fixture
def test_user(db_session):
    """創建測試用戶"""
    from src.models.user import User
    from src.utils.auth import hash_password

    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        is_active=True,
        email_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
```

#### 3.1.2 測試用例示例

```python
# tests/api/v2/test_auth.py
import pytest
from fastapi.testclient import TestClient

def test_login_success(client: TestClient, test_user):
    """測試成功登入"""
    response = client.post("/api/v2/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]

def test_login_invalid_credentials(client: TestClient):
    """測試無效憑證登入"""
    response = client.post("/api/v2/auth/login", json={
        "username": "nonexistent",
        "password": "wrongpass"
    })

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "error" in data

def test_register_new_user(client: TestClient):
    """測試新用戶註冊"""
    response = client.post("/api/v2/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "newpass123"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "newuser"

def test_register_duplicate_username(client: TestClient, test_user):
    """測試重複用戶名註冊"""
    response = client.post("/api/v2/auth/register", json={
        "username": "testuser",
        "email": "another@example.com",
        "password": "pass123"
    })

    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "username" in data["error"]["details"].lower()

def test_refresh_token(client: TestClient, test_user):
    """測試刷新令牌"""
    # 先登入
    login_response = client.post("/api/v2/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    refresh_token = login_response.json()["data"]["refresh_token"]

    # 刷新令牌
    response = client.post("/api/v2/auth/refresh", json={
        "refresh_token": refresh_token
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

def test_logout(client: TestClient, test_user):
    """測試登出"""
    # 先登入
    login_response = client.post("/api/v2/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    token = login_response.json()["data"]["access_token"]

    # 登出
    response = client.post("/api/v2/auth/logout", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

#### 3.1.3 策略模組測試

```python
# tests/strategies/test_enhanced_factory_v2.py
import pytest
from src.strategies.enhanced_factory_v2 import EnhancedStrategyFactoryV2

class TestEnhancedStrategyFactoryV2:
    """測試增強策略工廠 V2"""

    @pytest.fixture
    def factory(self):
        return EnhancedStrategyFactoryV2()

    def test_create_momentum_strategy(self, factory):
        """測試創建動量策略"""
        strategy = factory.create_strategy(
            type="momentum",
            config={
                "name": "test_momentum",
                "parameters": {
                    "period": 14,
                    "threshold": 0.02
                }
            }
        )

        assert strategy is not None
        assert strategy.type == "momentum"
        assert strategy.config["parameters"]["period"] == 14

    def test_create_fundamental_strategy(self, factory):
        """測試創建基本面策略"""
        strategy = factory.create_strategy(
            type="fundamental",
            config={
                "name": "test_fundamental",
                "parameters": {
                    "indicator": "GDP",
                    "threshold": 2.5
                }
            }
        )

        assert strategy is not None
        assert strategy.type == "fundamental"

    def test_invalid_strategy_type(self, factory):
        """測試無效策略類型"""
        with pytest.raises(ValueError, match="Unknown strategy type"):
            factory.create_strategy(
                type="invalid_type",
                config={}
            )

    def test_strategy_execution(self, factory):
        """測試策略執行"""
        strategy = factory.create_strategy(
            type="momentum",
            config={
                "name": "test_momentum",
                "parameters": {"period": 14}
            }
        )

        # 模擬數據
        import pandas as pd
        data = pd.DataFrame({
            "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
            "volume": [1000] * 11
        })

        signals = strategy.generate_signals(data)

        assert signals is not None
        assert "signal" in signals.columns
        assert "strength" in signals.columns
```

### 3.2 前端單元測試

#### 3.2.1 測試配置

```typescript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
      ],
    },
  },
});
```

#### 3.2.2 測試用例示例

```typescript
// frontend/src/components/__tests__/Dashboard.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import Dashboard from '../Dashboard';
import { apiSlice } from '../../store/slices/apiSlice';

const mockStore = configureStore({
  reducer: {
    [apiSlice.reducerPath]: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(apiSlice.middleware),
});

const renderWithStore = (component: React.ReactElement) => {
  return render(
    <Provider store={mockStore}>
      {component}
    </Provider>
  );
};

describe('Dashboard Component', () => {
  it('renders dashboard header', () => {
    renderWithStore(<Dashboard />);
    expect(screen.getByText('策略儀表板')).toBeInTheDocument();
  });

  it('displays strategy statistics', async () => {
    // Mock API 響應
    vi.mock('../../services/api/strategies', () => ({
      getStrategies: vi.fn().mockResolvedValue({
        data: { items: [], total: 0 }
      }),
    }));

    renderWithStore(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('策略總數')).toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    renderWithStore(<Dashboard />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

#### 3.2.3 Redux 測試

```typescript
// frontend/src/store/slices/__tests__/authSlice.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import authReducer, {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
} from '../authSlice';

describe('authSlice', () => {
  const initialState = {
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
    error: null,
  };

  it('should handle initial state', () => {
    expect(authReducer(undefined, { type: 'unknown' })).toEqual(initialState);
  });

  it('should handle loginStart', () => {
    const actual = authReducer(initialState, loginStart());
    expect(actual.isLoading).toBe(true);
    expect(actual.error).toBeNull();
  });

  it('should handle loginSuccess', () => {
    const mockUser = { id: 1, username: 'testuser' };
    const mockToken = 'mock-jwt-token';

    const actual = authReducer(
      initialState,
      loginSuccess({ user: mockUser, token: mockToken })
    );

    expect(actual.isLoading).toBe(false);
    expect(actual.isAuthenticated).toBe(true);
    expect(actual.user).toEqual(mockUser);
    expect(actual.token).toBe(mockToken);
  });

  it('should handle loginFailure', () => {
    const mockError = 'Invalid credentials';

    const actual = authReducer(
      initialState,
      loginFailure(mockError)
    );

    expect(actual.isLoading).toBe(false);
    expect(actual.error).toBe(mockError);
  });

  it('should handle logout', () => {
    const loggedInState = {
      ...initialState,
      isAuthenticated: true,
      user: { id: 1, username: 'testuser' },
      token: 'mock-token',
    };

    const actual = authReducer(loggedInState, logout());

    expect(actual).toEqual(initialState);
  });
});
```

---

## 4. 集成測試

### 4.1 API 集成測試

#### 4.1.1 測試框架設置

```python
# tests/integration/conftest.py
import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base

# 測試 API 基礎 URL
API_BASE_URL = "http://localhost:3005/api/v2"

@pytest.fixture(scope="session")
def test_db():
    """創建測試數據庫"""
    engine = create_engine("postgresql://localhost:5432/cbsc_test")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def auth_token():
    """獲取測試認證令牌"""
    # 註冊測試用戶
    requests.post(f"{API_BASE_URL}/auth/register", json={
        "username": "integration_test_user",
        "email": "integration@test.com",
        "password": "testpass123"
    })

    # 登入獲取令牌
    response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": "integration_test_user",
        "password": "testpass123"
    })

    return response.json()["data"]["access_token"]

@pytest.fixture
def authenticated_client(auth_token):
    """創建已認證的測試客戶端"""
    class AuthenticatedClient:
        def __init__(self, base_url, token):
            self.base_url = base_url
            self.headers = {"Authorization": f"Bearer {token}"}

        def get(self, endpoint, **kwargs):
            return requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                **kwargs
            )

        def post(self, endpoint, **kwargs):
            return requests.post(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                **kwargs
            )

        def put(self, endpoint, **kwargs):
            return requests.put(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                **kwargs
            )

        def delete(self, endpoint, **kwargs):
            return requests.delete(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                **kwargs
            )

    return AuthenticatedClient(API_BASE_URL, auth_token)
```

#### 4.1.2 策略 API 集成測試

```python
# tests/integration/test_strategies_api.py
import pytest

class TestStrategiesAPI:
    """策略 API 集成測試"""

    def test_create_strategy(self, authenticated_client):
        """測試創建策略"""
        response = authenticated_client.post("/strategies", json={
            "name": "Integration Test Strategy",
            "description": "Test strategy for integration testing",
            "type": "momentum",
            "config": {
                "parameters": {
                    "period": 14,
                    "threshold": 0.02
                }
            }
        })

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Integration Test Strategy"

    def test_list_strategies(self, authenticated_client):
        """測試列出策略"""
        response = authenticated_client.get("/strategies")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert "total" in data["data"]

    def test_get_strategy_detail(self, authenticated_client):
        """測試獲取策略詳情"""
        # 先創建策略
        create_response = authenticated_client.post("/strategies", json={
            "name": "Detail Test Strategy",
            "type": "momentum",
            "config": {"parameters": {"period": 14}}
        })
        strategy_id = create_response.json()["data"]["id"]

        # 獲取詳情
        response = authenticated_client.get(f"/strategies/{strategy_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == strategy_id

    def test_update_strategy(self, authenticated_client):
        """測試更新策略"""
        # 創建策略
        create_response = authenticated_client.post("/strategies", json={
            "name": "Update Test Strategy",
            "type": "momentum",
            "config": {"parameters": {"period": 14}}
        })
        strategy_id = create_response.json()["data"]["id"]

        # 更新策略
        response = authenticated_client.put(f"/strategies/{strategy_id}", json={
            "name": "Updated Strategy Name",
            "description": "Updated description"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Strategy Name"

    def test_delete_strategy(self, authenticated_client):
        """測試刪除策略"""
        # 創建策略
        create_response = authenticated_client.post("/strategies", json={
            "name": "Delete Test Strategy",
            "type": "momentum",
            "config": {"parameters": {"period": 14}}
        })
        strategy_id = create_response.json()["data"]["id"]

        # 刪除策略
        response = authenticated_client.delete(f"/strategies/{strategy_id}")

        assert response.status_code == 204

        # 驗證已刪除
        get_response = authenticated_client.get(f"/strategies/{strategy_id}")
        assert get_response.status_code == 404

    def test_activate_strategy(self, authenticated_client):
        """測試激活策略"""
        # 創建策略
        create_response = authenticated_client.post("/strategies", json={
            "name": "Activate Test Strategy",
            "type": "momentum",
            "config": {"parameters": {"period": 14}}
        })
        strategy_id = create_response.json()["data"]["id"]

        # 激活策略
        response = authenticated_client.post(f"/strategies/{strategy_id}/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["is_active"] is True
```

### 4.2 數據庫集成測試

```python
# tests/integration/test_database.py
import pytest
from sqlalchemy import text
from src.models.user import User
from src.models.strategy import Strategy

class TestDatabaseIntegration:
    """數據庫集成測試"""

    def test_user_crud(self, db_session):
        """測試用戶 CRUD"""
        # Create
        user = User(
            username="dbtest",
            email="dbtest@example.com",
            password_hash="hashed_password",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None

        # Read
        retrieved_user = db_session.query(User).filter_by(
            username="dbtest"
        ).first()
        assert retrieved_user is not None
        assert retrieved_user.email == "dbtest@example.com"

        # Update
        retrieved_user.email = "updated@example.com"
        db_session.commit()
        assert retrieved_user.email == "updated@example.com"

        # Delete
        db_session.delete(retrieved_user)
        db_session.commit()
        assert db_session.query(User).filter_by(
            username="dbtest"
        ).first() is None

    def test_foreign_key_constraint(self, db_session):
        """測試外鍵約束"""
        # 創建用戶
        user = User(
            username="fktest",
            email="fktest@example.com",
            password_hash="hashed"
        )
        db_session.add(user)
        db_session.commit()

        # 創建關聯策略
        strategy = Strategy(
            user_id=user.id,
            name="FK Test Strategy",
            type="momentum",
            config={}
        )
        db_session.add(strategy)
        db_session.commit()

        # 驗證關聯
        assert strategy.user.username == "fktest"

        # 測試級聯刪除
        db_session.delete(user)
        db_session.commit()

        # 策略應該被刪除
        assert db_session.query(Strategy).filter_by(
            id=strategy.id
        ).first() is None

    def test_transaction_rollback(self, db_session):
        """測試事務回滾"""
        from sqlalchemy.exc import IntegrityError

        initial_count = db_session.query(User).count()

        # 嘗試插入重複用戶
        user1 = User(username="transact", email="transact@example.com", password_hash="hash")
        user2 = User(username="transact", email="transact2@example.com", password_hash="hash")

        db_session.add(user1)
        db_session.add(user2)

        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()

        # 驗證沒有用戶被添加
        final_count = db_session.query(User).count()
        assert final_count == initial_count
```

---

## 5. 端到端測試

### 5.1 E2E 測試框架

```typescript
// frontend/e2e/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### 5.2 關鍵業務流程測試

```typescript
// frontend/e2e/strategy-management.spec.ts
import { test, expect } from '@playwright/test';

test.describe('策略管理流程', () => {
  test.beforeEach(async ({ page }) => {
    // 登入
    await page.goto('/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('創建新策略', async ({ page }) => {
    // 導航到策略頁面
    await page.click('text=策略管理');
    await expect(page).toHaveURL('/strategies');

    // 點擊創建按鈕
    await page.click('button:has-text("創建策略")');

    // 填寫策略表單
    await page.fill('input[name="name"]', 'E2E Test Strategy');
    await page.selectOption('select[name="type"]', 'momentum');

    // 配置參數
    await page.fill('input[name="period"]', '14');
    await page.fill('input[name="threshold"]', '0.02');

    // 提交
    await page.click('button:has-text("創建")');

    // 驗證成功消息
    await expect(page.locator('text=策略創建成功')).toBeVisible();

    // 驗證策略出現在列表中
    await expect(page.locator('text=E2E Test Strategy')).toBeVisible();
  });

  test('編輯現有策略', async ({ page }) => {
    await page.goto('/strategies');

    // 選擇第一個策略
    await page.click('.strategy-item:first-child button:has-text("編輯")');

    // 修改名稱
    await page.fill('input[name="name"]', 'Updated Strategy Name');
    await page.click('button:has-text("保存")');

    // 驗證成功
    await expect(page.locator('text=策略更新成功')).toBeVisible();
    await expect(page.locator('text=Updated Strategy Name')).toBeVisible();
  });

  test('刪除策略', async ({ page }) => {
    await page.goto('/strategies');

    // 獲取初始策略數量
    const initialCount = await page.locator('.strategy-item').count();

    // 刪除第一個策略
    await page.click('.strategy-item:first-child button:has-text("刪除")');
    await page.click('button:has-text("確認")');

    // 驗證刪除
    await expect(page.locator('text=策略刪除成功')).toBeVisible();
    const finalCount = await page.locator('.strategy-item').count();
    expect(finalCount).toBe(initialCount - 1);
  });

  test('激活和停用策略', async ({ page }) => {
    await page.goto('/strategies');

    // 激活策略
    await page.click('.strategy-item:first-child button:has-text("啟動")');
    await expect(page.locator('text=策略已啟動')).toBeVisible();

    // 驗證狀態
    await expect(page.locator('.strategy-item:first-child .status-active')).toBeVisible();

    // 停用策略
    await page.click('.strategy-item:first-child button:has-text("停止")');
    await expect(page.locator('text=策略已停止')).toBeVisible();
  });
});

test.describe('回測流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
  });

  test('運行回測', async ({ page }) => {
    await page.goto('/backtest');

    // 選擇策略
    await page.selectOption('select[name="strategy_id"]', '1');

    // 設置回測參數
    await page.fill('input[name="start_date"]', '2024-01-01');
    await page.fill('input[name="end_date"]', '2024-12-31');
    await page.fill('input[name="initial_capital"]', '100000');

    // 運行回測
    await page.click('button:has-text("運行回測")');

    // 等待完成
    await expect(page.locator('text=回測完成')).toBeVisible({ timeout: 60000 });

    // 驗證結果
    await expect(page.locator('.backtest-results')).toBeVisible();
    await expect(page.locator('text=總收益率')).toBeVisible();
  });

  test('查看回測報告', async ({ page }) => {
    await page.goto('/backtest');

    // 點擊歷史回測
    await page.click('text=查看歷史');
    await page.click('.backtest-item:first-child');

    // 驗證報告內容
    await expect(page.locator('.backtest-report')).toBeVisible();
    await expect(page.locator('canvas')).toHaveCount(2); // 性能圖表
  });
});
```

---

## 6. 性能測試

### 6.1 API 性能測試

```python
# tests/performance/test_api_performance.py
import pytest
import time
import requests
from concurrent.futures import ThreadPoolExecutor

API_BASE_URL = "http://localhost:3004/api/v2"

class TestAPIPerformance:
    """API 性能測試"""

    def test_strategies_list_response_time(self, auth_token):
        """測試策略列表響應時間"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        start_time = time.time()
        response = requests.get(
            f"{API_BASE_URL}/strategies",
            headers=headers
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # 轉換為毫秒

        assert response.status_code == 200
        assert response_time < 200  # P95 響應時間 < 200ms
        print(f"響應時間: {response_time:.2f}ms")

    def test_concurrent_requests(self, auth_token):
        """測試併發請求"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        def make_request():
            start = time.time()
            response = requests.get(
                f"{API_BASE_URL}/strategies",
                headers=headers
            )
            elapsed = time.time() - start
            return response.status_code, elapsed

        # 併發 10 個請求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        successful = sum(1 for r in results if r[0] == 200)
        avg_response_time = sum(r[1] for r in results) / len(results) * 1000

        assert successful >= 9  # 至少 90% 成功率
        assert avg_response_time < 500  # 平均響應時間 < 500ms
        print(f"成功率: {successful/10*100}%")
        print(f"平均響應時間: {avg_response_time:.2f}ms")

    def test_large_payload(self, auth_token):
        """測試大負載響應"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        start_time = time.time()
        response = requests.get(
            f"{API_BASE_URL}/strategies?page=1&page_size=100",
            headers=headers
        )
        end_time = time.time()

        response_time = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time < 1000  # 大數據響應 < 1秒
        print(f"大負載響應時間: {response_time:.2f}ms")
```

### 6.2 Locust 負載測試

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import json

class CBSCTradingUser(HttpUser):
    """CBSC 交易系統負載測試用戶"""

    wait_time = between(1, 3)
    host = "http://localhost:3004"

    def on_start(self):
        """每個用戶啟動時執行"""
        # 登入獲取令牌
        response = self.client.post("/api/v2/auth/login", json={
            "username": "testuser",
            "password": "testpass123"
        })

        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(3)
    def view_strategies(self):
        """查看策略列表 (最高頻率)"""
        if self.token:
            self.client.get("/api/v2/strategies", headers=self.headers)

    @task(2)
    def view_portfolio(self):
        """查看投資組合"""
        if self.token:
            self.client.get("/api/v2/portfolio", headers=self.headers)

    @task(1)
    def view_backtests(self):
        """查看回測結果"""
        if self.token:
            self.client.get("/api/v2/backtests", headers=self.headers)

    @task(1)
    def get_market_data(self):
        """獲取市場數據"""
        self.client.get("/api/v2/market-data?symbol=AAPL")
```

運行負載測試:

```bash
# 運行 Locust 測試
locust -f tests/performance/locustfile.py --users 100 --spawn-rate 10

# 無頭模式
locust -f tests/performance/locustfile.py --users 100 --spawn-rate 10 --headless
```

---

## 7. 安全測試

### 7.1 認證授權測試

```python
# tests/security/test_auth.py
import pytest
import requests

API_BASE_URL = "http://localhost:3004/api/v2"

class TestAuthenticationSecurity:
    """認證安全測試"""

    def test_sql_injection_login(self):
        """測試 SQL 注入防護"""
        response = requests.post(f"{API_BASE_URL}/auth/login", json={
            "username": "admin' OR '1'='1",
            "password": "anything"
        })

        assert response.status_code == 401
        assert "Invalid" in response.json()["error"]["message"]

    def test_brute_force_protection(self):
        """測試暴力破解防護"""
        for i in range(6):  # 嘗試 6 次
            response = requests.post(f"{API_BASE_URL}/auth/login", json={
                "username": "testuser",
                "password": "wrongpassword"
            })

        # 第 6 次應該被阻止
        assert response.status_code == 429  # Too Many Requests

    def test_token_expiration(self):
        """測試令牌過期"""
        # 使用過期的令牌
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired"

        response = requests.get(
            f"{API_BASE_URL}/strategies",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    def test_invalid_token(self):
        """測試無效令牌"""
        response = requests.get(
            f"{API_BASE_URL}/strategies",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_protected_endpoint_without_auth(self):
        """測試未授權訪問"""
        response = requests.get(f"{API_BASE_URL}/strategies")

        assert response.status_code == 401
```

### 7.2 輸入驗證測試

```python
# tests/security/test_input_validation.py
import pytest
import requests

class TestInputValidation:
    """輸入驗證測試"""

    def test_xss_in_strategy_name(self, auth_token):
        """測試 XSS 防護"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        xss_payload = "<script>alert('XSS')</script>"

        response = requests.post(
            f"{API_BASE_URL}/strategies",
            headers=headers,
            json={
                "name": xss_payload,
                "type": "momentum",
                "config": {}
            }
        )

        # API 應該接受但轉義輸入
        # 或拒絕包含 HTML 的輸入
        assert response.status_code in [201, 400]

    def test_invalid_json(self):
        """測試無效 JSON 輸入"""
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422  # Unprocessable Entity

    def test_large_payload(self, auth_token):
        """測試超大負載"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        large_name = "A" * 10000  # 10KB 名稱

        response = requests.post(
            f"{API_BASE_URL}/strategies",
            headers=headers,
            json={
                "name": large_name,
                "type": "momentum",
                "config": {}
            }
        )

        # 應該拒絕超大輸入
        assert response.status_code == 422
```

---

## 8. 測試執行計劃

### 8.1 CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Test Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: cbsc_test
          POSTGRES_USER: cbsc_test
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run unit tests
        working-directory: ./frontend
        run: npm run test:unit -- --coverage

      - name: Run E2E tests
        working-directory: ./frontend
        run: npm run test:e2e

  security-scan:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: bandit -r src/

      - name: Run Safety
        run: safety check

      - name: Run npm audit
        working-directory: ./frontend
        run: npm audit --audit-level=high
```

### 8.2 測試執行順序

```
1. 快速單元測試 (5 分鐘)
   ├─ 後端單元測試
   └─ 前端單元測試

2. 集成測試 (15 分鐘)
   ├─ API 集成測試
   ├─ 數據庫集成測試
   └─ 外部服務集成測試

3. E2E 測試 (20 分鐘)
   ├─ 關鍵業務流程
   └─ 用戶場景測試

4. 性能測試 (30 分鐘)
   ├─ API 性能基準
   └─ 負載測試

5. 安全掃描 (10 分鐘)
   ├─ 靜態代碼分析
   ├─ 依賴漏洞掃描
   └─ 認證授權測試
```

---

## 9. 測試報告

### 9.1 測試結果模板

```markdown
# 測試執行報告 - [日期]

## 測試概要
- **執行時間**: YYYY-MM-DD HH:MM:SS
- **執行人**: [姓名]
- **測試環境**: [環境名稱]
- **測試版本**: [版本號]

## 測試結果統計
| 類型 | 總數 | 通過 | 失敗 | 跳過 | 通過率 |
|------|------|------|------|------|--------|
| 單元測試 | 500 | 495 | 3 | 2 | 99% |
| 集成測試 | 150 | 145 | 5 | 0 | 97% |
| E2E 測試 | 50 | 48 | 2 | 0 | 96% |
| 性能測試 | 20 | 18 | 2 | 0 | 90% |
| 安全測試 | 30 | 30 | 0 | 0 | 100% |
| **總計** | **750** | **736** | **12** | **2** | **98%** |

## 失敗測試詳情
### 1. [測試名稱]
- **文件**: [文件路徑]
- **錯誤**: [錯誤信息]
- **嚴重程度**: High/Medium/Low
- **負責人**: [姓名]

## 覆蓋率報告
- **後端代碼覆蓋率**: 87%
- **前端代碼覆蓋率**: 82%
- **API 端點覆蓋率**: 100%

## 性能基準
- **API P95 響應時間**: 145ms (目標: <200ms) ✅
- **併發 100 用戶成功率**: 98% (目標: >95%) ✅
- **數據庫查詢時間**: 45ms (目標: <100ms) ✅

## 安全掃描結果
- **高危漏洞**: 0
- **中危漏洞**: 2
- **低危漏洞**: 5

## 結論
[通過/不通過]

## 後續行動
- [ ] 修復失敗測試
- [ ] 提高覆蓋率
- [ ] 修復中危漏洞
```

---

## 10. 附錄

### 10.1 測試命令速查

```bash
# 運行所有測試
pytest tests/ -v

# 運行特定類型測試
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# 運行特定測試文件
pytest tests/api/test_auth.py -v

# 運行並生成覆蓋率報告
pytest tests/ --cov=src --cov-report=html

# 運行前端測試
cd frontend
npm test
npm run test:e2e

# 運行性能測試
locust -f tests/performance/locustfile.py

# 運行安全掃描
bandit -r src/
safety check
```

### 10.2 測試數據管理

```python
# tests/fixtures/test_data.py
"""測試數據夾具"""

@pytest.fixture
def sample_strategy_data():
    """示例策略數據"""
    return {
        "name": "Test Strategy",
        "description": "A test strategy",
        "type": "momentum",
        "config": {
            "parameters": {
                "period": 14,
                "threshold": 0.02
            }
        }
    }

@pytest.fixture
def sample_backtest_data():
    """示例回測數據"""
    return {
        "strategy_id": 1,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000,
        "config": {}
    }
```

---

**文檔版本**: 1.0
**最後更新**: 2025-12-24T12:26:09Z
**審視周期**: 每次迭代前
