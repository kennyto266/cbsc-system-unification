---
name: testing-validation
title: 測試覆蓋與質量保證
status: backlog
phase: 6
priority: P0
created: 2025-12-24T12:05:52Z
updated: 2025-12-24T12:16:04Z
estimated_hours: 48
assignee: TBD
dependencies: ["004-frontend-structure", "005-backend-consolidation", "006-dependency-optimization", "007-config-management"]
github:
  issue: 80
  url: https://github.com/kennyto266/cbsc-system-unification/issues/80
---

# Task 008: 測試覆蓋與質量保證

## 概述

為重構後的系統建立完整的測試框架，包括單元測試、集成測試、E2E 測試，確保系統質量。

## 詳細描述

### 測試策略

```yaml
測試金字塔:
  E2E 測試:      10% (關鍵用戶旅程)
    - 用戶註冊/登錄流程
    - 策略創建和管理
    - 回測執行和查看
    - 實時數據顯示

  集成測試:     30% (API 和服務集成)
    - API 端點測試
    - 服務層測試
    - 數據庫操作測試
    - WebSocket 通信測試

  單元測試:     60% (業務邏輯和組件)
    - React 組件測試
    - Hooks 測試
    - 工具函數測試
    - 服務類測試
```

### 前端測試

#### 1. 組件測試 (Vitest + Testing Library)

```typescript
// frontend/src/features/strategies/components/__tests__/StrategyList.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { StrategyList } from '../StrategyList';
import { store } from '@/store';
import { strategiesApi } from '@/shared/services/api';

// Mock API
vi.mock('@/shared/services/api', () => ({
  strategiesApi: {
    useListStrategiesQuery: vi.fn(),
  },
}));

describe('StrategyList', () => {
  const wrapper = ({ children }) => (
    <Provider store={store}>
      <BrowserRouter>{children}</BrowserRouter>
    </Provider>
  );

  it('renders loading state', () => {
    vi.mocked(strategiesApi.useListStrategiesQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<StrategyList />, { wrapper });
    expect(screen.getByTestId('strategy-list-loading')).toBeInTheDocument();
  });

  it('renders strategy list', async () => {
    const mockStrategies = [
      { id: 1, name: 'MA Crossover', status: 'active' },
      { id: 2, name: 'RSI Strategy', status: 'draft' },
    ];

    vi.mocked(strategiesApi.useListStrategiesQuery).mockReturnValue({
      data: mockStrategies,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    } as any);

    render(<StrategyList />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('MA Crossover')).toBeInTheDocument();
      expect(screen.getByText('RSI Strategy')).toBeInTheDocument();
    });
  });

  it('handles error state', () => {
    vi.mocked(strategiesApi.useListStrategiesQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: { message: 'Failed to fetch strategies' },
      refetch: vi.fn(),
    } as any);

    render(<StrategyList />, { wrapper });
    expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
  });
});
```

#### 2. Hooks 測試

```typescript
// frontend/src/shared/hooks/__tests__/useWebSocket.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('connects to WebSocket on mount', async () => {
    const mockWs = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.OPEN,
    };

    global.WebSocket = vi.fn(() => mockWs) as any;

    const { result } = renderHook(() => useWebSocket('ws://localhost:3004'));

    await waitFor(() => {
      expect(WebSocket).toHaveBeenCalledWith('ws://localhost:3004');
      expect(result.current.connected).toBe(true);
    });
  });

  it('reconnects on connection loss', async () => {
    const mockWs = {
      addEventListener: vi.fn((event, handler) => {
        if (event === 'open') {
          setTimeout(() => handler(), 100);
        }
      }),
      removeEventListener: vi.fn(),
      send: vi.fn(),
      close: vi.fn(),
      readyState: WebSocket.CLOSED,
    };

    global.WebSocket = vi.fn(() => mockWs) as any;

    const { result } = renderHook(() =>
      useWebSocket('ws://localhost:3004', { reconnect: true })
    );

    // Simulate connection loss
    mockWs.readyState = WebSocket.CLOSED;
    mockWs.addEventListener.mockImplementation((event, handler) => {
      if (event === 'close') handler();
    });

    await waitFor(() => {
      expect(mockWs.addEventListener).toHaveBeenCalledWith('close', expect.any(Function));
    });
  });
});
```

### 後端測試

#### 1. API 端點測試

```python
# backend/tests/api/v2/test_auth_routes.py
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.database import get_db
from backend.tests.conftest import TestDatabase

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_database():
    """Override database with test database"""
    def get_test_db():
        db = TestDatabase()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_test_db
    yield
    app.dependency_overrides.clear()

class TestAuthRoutes:
    """Test authentication routes"""

    def test_login_success(self, test_user):
        """Test successful login"""
        response = client.post("/api/v2/auth/login", json={
            "username": test_user.username,
            "password": "testpass123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, test_user):
        """Test login with invalid credentials"""
        response = client.post("/api/v2/auth/login", json={
            "username": test_user.username,
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "detail" in response.json()

    def test_refresh_token(self, test_user, auth_tokens):
        """Test token refresh"""
        response = client.post("/api/v2/auth/refresh", json={
            "refresh_token": auth_tokens["refresh_token"]
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_get_current_user(self, auth_tokens):
        """Test getting current user"""
        response = client.get(
            "/api/v2/auth/me",
            headers={"Authorization": f"Bearer {auth_tokens['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data

    def test_get_current_user_unauthorized(self):
        """Test getting current user without token"""
        response = client.get("/api/v2/auth/me")

        assert response.status_code == 401
```

#### 2. 服務層測試

```python
# backend/tests/services/test_strategy_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from backend.services.strategy_service import StrategyService
from backend.schemas.strategy import StrategyCreate

class TestStrategyService:
    """Test strategy service"""

    @pytest.fixture
    def service(self, test_db):
        """Create service instance with test database"""
        return StrategyService(test_db)

    @pytest.fixture
    def strategy_data(self):
        """Sample strategy data"""
        return StrategyCreate(
            name="Test Strategy",
            description="A test strategy",
            config={"type": "ma_crossover", "short_period": 5, "long_period": 20}
        )

    @pytest.mark.asyncio
    async def test_create_strategy(self, service, test_user, strategy_data):
        """Test creating a strategy"""
        result = await service.create(
            user_id=test_user.id,
            data=strategy_data
        )

        assert result.id is not None
        assert result.name == "Test Strategy"
        assert result.user_id == test_user.id
        assert result.status == "draft"

    @pytest.mark.asyncio
    async def test_get_strategy_by_id(self, service, test_user, strategy_data):
        """Test getting strategy by ID"""
        created = await service.create(test_user.id, strategy_data)
        result = await service.get_by_id(created.id, test_user.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Test Strategy"

    @pytest.mark.asyncio
    async def test_get_strategy_unauthorized(self, service, test_user, other_user, strategy_data):
        """Test getting strategy with wrong user"""
        created = await service.create(test_user.id, strategy_data)
        result = await service.get_by_id(created.id, other_user.id)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_strategies(self, service, test_user):
        """Test listing user strategies"""
        # Create multiple strategies
        for i in range(3):
            await service.create(test_user.id, StrategyCreate(
                name=f"Strategy {i}",
                description=f"Test strategy {i}",
                config={}
            ))

        result = await service.list(test_user.id)

        assert len(result) == 3
        assert all(s.user_id == test_user.id for s in result)

    @pytest.mark.asyncio
    async def test_delete_strategy(self, service, test_user, strategy_data):
        """Test deleting a strategy"""
        created = await service.create(test_user.id, strategy_data)
        deleted = await service.delete(created.id, test_user.id)

        assert deleted is True

        # Verify deletion
        result = await service.get_by_id(created.id, test_user.id)
        assert result is None
```

### E2E 測試

```typescript
// frontend/e2e/strategies.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Strategy Management E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('http://localhost:3000/login');
    await page.fill('[name="username"]', 'testuser');
    await page.fill('[name="password"]', 'testpass123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('http://localhost:3000/');
  });

  test('should create a new strategy', async ({ page }) => {
    await page.click('text=Strategies');
    await page.click('button:has-text("New Strategy")');

    await page.fill('[name="name"]', 'E2E Test Strategy');
    await page.fill('[name="description"]', 'Created by E2E test');
    await page.selectOption('[name="type"]', 'ma_crossover');

    await page.fill('[name="config.short_period"]', '5');
    await page.fill('[name="config.long_period"]', '20');

    await page.click('button:has-text("Create")');

    // Verify success
    await expect(page.locator('text=Strategy created successfully')).toBeVisible();
    await expect(page.locator('text=E2E Test Strategy')).toBeVisible();
  });

  test('should edit existing strategy', async ({ page }) => {
    await page.click('text=Strategies');
    await page.click('text=E2E Test Strategy');

    await page.click('button:has-text("Edit")');
    await page.fill('[name="name"]', 'Updated E2E Strategy');
    await page.click('button:has-text("Save")');

    await expect(page.locator('text=Strategy updated successfully')).toBeVisible();
    await expect(page.locator('text=Updated E2E Strategy')).toBeVisible();
  });

  test('should run backtest', async ({ page }) => {
    await page.click('text=Strategies');
    await page.click('text=E2E Test Strategy');
    await page.click('button:has-text("Run Backtest")');

    // Configure backtest
    await page.fill('[name="start_date"]', '2023-01-01');
    await page.fill('[name="end_date"]', '2023-12-31');
    await page.click('button:has-text("Start")');

    // Wait for backtest to complete
    await expect(page.locator('[data-testid="backtest-status"]')).toHaveText(
      /completed|failed/,
      { timeout: 60000 }
    );
  });
});
```

### 測試配置

#### Vitest 配置

```typescript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/tests/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'src/main.tsx',
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80,
      },
    },
  },
});
```

#### Pytest 配置

```ini
# backend/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=backend
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests

asyncio_mode = auto
```

## 驗收標準

### 交付物

- [ ] **測試框架**
  - Vitest 配置
  - Pytest 配置
  - Playwright 配置

- [ ] **測試套件**
  - 前端組件測試 (>80% 覆蓋)
  - 後端服務測試 (>85% 覆蓋)
  - E2E 測試 (關鍵流程)

- [ ] **測試輔助工具**
  - 測試數據工廠
  - Mock 服務
  - 測試 fixtures

### 質量門檻

- 單元測試覆蓋率 >80%
- 關鍵路徑覆蓋率 100%
- 所有測試通過
- CI/CD 集成完成

## 依賴關係

### 前置任務
- Task 004: 前端結構統一
- Task 005: 後端 API 統一
- Task 006: 依賴優化
- Task 007: 配置統一

### 後續任務
- Task 009: 文檔交付

## 執行步驟

1. **第 1-5 天: 單元測試**
   - React 組件測試
   - Hooks 測試
   - 服務層測試

2. **第 6-9 天: 集成測試**
   - API 端點測試
   - 數據庫測試
   - WebSocket 測試

3. **第 10-14 天: E2E 測試**
   - 關鍵流程測試
   - 交叉瀏覽器測試
   - 性能測試
