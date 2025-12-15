---
name: task-011-testing-infrastructure
title: Task 011: 测试体系建设
description: 编写单元测试和集成测试、实施端到端测试、配置持续集成流程
status: open
priority: P1
assigned_to: qa-team
created: 2025-12-14T03:34:13Z
updated: 2025-12-14T03:34:13Z
start_date: 2025-12-18
due_date: 2025-12-25
estimated_hours: 100
tags: [testing, quality-assurance, ci-cd, automation]
epic: square-ui-integration
depends_on: [task-009, task-010]
---

## Task 011: 测试体系建设

### 任务概述
建立完整的测试体系，包括单元测试、集成测试、端到端测试和持续集成流程，确保代码质量和系统稳定性，支持快速迭代和可靠交付。

### 详细任务

#### 1. 单元测试框架建设

**Jest和React Testing Library配置**
```typescript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$':
      '<rootDir>/src/test/__mocks__/fileMock.js'
  },
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/test/**',
    '!src/**/*.stories.tsx'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

**测试工具集配置**
```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { server } from './server';

// Mock API server
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
});

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn()
}));
```

**单元测试示例**
```typescript
// src/components/__tests__/UserList.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserList } from '../UserList';
import { mockUsers } from '../../test/mocks/data';

describe('UserList', () => {
  it('renders user list correctly', () => {
    render(<UserList users={mockUsers} />);

    expect(screen.getByText('用户列表')).toBeInTheDocument();
    mockUsers.forEach(user => {
      expect(screen.getByText(user.username)).toBeInTheDocument();
    });
  });

  it('handles user selection', () => {
    const onSelectUser = jest.fn();
    render(<UserList users={mockUsers} onSelectUser={onSelectUser} />);

    fireEvent.click(screen.getByText(mockUsers[0].username));
    expect(onSelectUser).toHaveBeenCalledWith(mockUsers[0]);
  });

  it('filters users based on search term', async () => {
    render(<UserList users={mockUsers} />);

    const searchInput = screen.getByPlaceholderText('搜索用户...');
    fireEvent.change(searchInput, { target: { value: 'john' } });

    await waitFor(() => {
      expect(screen.getByText('john_doe')).toBeInTheDocument();
      expect(screen.queryByText('jane_doe')).not.toBeInTheDocument();
    });
  });

  it('shows loading state', () => {
    render(<UserList users={[]} loading />);

    expect(screen.getByTestId('user-list-skeleton')).toBeInTheDocument();
    expect(screen.queryByText('用户列表')).not.toBeInTheDocument();
  });
});
```

#### 2. 集成测试实施

**API集成测试**
```typescript
// src/api/__tests__/userApi.test.ts
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { userApi } from '../userApi';
import { mockUserResponse } from '../../test/mocks/api';

const server = setupServer(
  rest.get('/api/users', (req, res, ctx) => {
    return res(ctx.json(mockUserResponse));
  }),
  rest.post('/api/users', (req, res, ctx) => {
    return res(ctx.status(201), ctx.json({ success: true }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('User API Integration', () => {
  it('fetches users successfully', async () => {
    const response = await userApi.getUsers();

    expect(response.data).toEqual(mockUserResponse);
  });

  it('handles API errors gracefully', async () => {
    server.use(
      rest.get('/api/users', (req, res, ctx) => {
        return res(ctx.status(500));
      })
    );

    await expect(userApi.getUsers()).rejects.toThrow();
  });
});
```

**组件集成测试**
```typescript
// src/pages/__tests__/UserManagement.test.tsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { store } from '../../store';
import { UserManagement } from '../UserManagement';

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <Provider store={store}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </Provider>
  );
};

describe('User Management Integration', () => {
  it('loads and displays users', async () => {
    renderWithProviders(<UserManagement />);

    expect(screen.getByText('加载中...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('用户管理')).toBeInTheDocument();
      expect(screen.getByTestId('user-list')).toBeInTheDocument();
    });
  });

  it('navigates to user detail page', async () => {
    renderWithProviders(<UserManagement />);

    await waitFor(() => {
      expect(screen.getByText('john_doe')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('john_doe'));

    await waitFor(() => {
      expect(screen.getByText('用户详情')).toBeInTheDocument();
    });
  });
});
```

#### 3. 端到端测试自动化

**Playwright配置**
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] }
    }
  ],
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    port: 3000
  }
});
```

**E2E测试用例**
```typescript
// e2e/user-management.spec.ts
import { test, expect } from '@playwright/test';

test.describe('User Management E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create, edit and delete user', async ({ page }) => {
    // Navigate to user management
    await page.click('[data-testid="nav-users"]');
    await expect(page).toHaveURL('/admin/users');

    // Create new user
    await page.click('[data-testid="create-user-button"]');
    await page.fill('[data-testid="user-username"]', 'testuser');
    await page.fill('[data-testid="user-email"]', 'test@example.com');
    await page.fill('[data-testid="user-password"]', 'TestPass123!');
    await page.click('[data-testid="submit-button"]');

    // Verify user created
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    await expect(page.locator('text=testuser')).toBeVisible();

    // Edit user
    await page.click('[data-testid="edit-user-testuser"]');
    await page.fill('[data-testid="user-email"]', 'updated@example.com');
    await page.click('[data-testid="submit-button"]');

    // Verify user updated
    await expect(page.locator('text=updated@example.com')).toBeVisible();

    // Delete user
    await page.click('[data-testid="delete-user-testuser"]');
    await page.click('[data-testid="confirm-delete"]');

    // Verify user deleted
    await expect(page.locator('text=testuser')).not.toBeVisible();
  });

  test('should handle pagination', async ({ page }) => {
    await page.goto('/admin/users');

    // Check if pagination exists
    const pagination = page.locator('[data-testid="pagination"]');
    if (await pagination.isVisible()) {
      await page.click('[data-testid="next-page"]');
      await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
    }
  });

  test('should filter users', async ({ page }) => {
    await page.goto('/admin/users');

    // Test search filter
    await page.fill('[data-testid="search-input"]', 'admin');
    await page.press('[data-testid="search-input"]', 'Enter');

    await expect(page.locator('text=admin')).toBeVisible();

    // Test status filter
    await page.selectOption('[data-testid="status-filter"]', 'active');
    await expect(page.locator('[data-testid="user-list"]')).toBeVisible();
  });
});
```

#### 4. 持续集成流程配置

**GitHub Actions工作流**
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        node-version: [18.x, 20.x]

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v4

    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run linting
      run: npm run lint

    - name: Run type checking
      run: npm run type-check

    - name: Run unit tests
      run: npm run test:unit

    - name: Run integration tests
      run: npm run test:integration
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info
        flags: unittests
        name: codecov-umbrella

  e2e-test:
    runs-on: ubuntu-latest
    needs: test

    steps:
    - uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20.x'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Install Playwright browsers
      run: npx playwright install --with-deps

    - name: Build application
      run: npm run build

    - name: Run E2E tests
      run: npm run test:e2e
      env:
        E2E_BASE_URL: http://localhost:3000

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: playwright-report
        path: playwright-report/
```

**预提交钩子配置**
```json
// .husky/pre-commit
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

# Run linting
npm run lint
# Run type checking
npm run type-check
# Run unit tests
npm run test:unit
# Check for console.log statements
npm run check:console
```

```json
// .husky/pre-push
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

# Run full test suite
npm run test:ci
```

#### 5. 测试数据管理

**Mock数据和Factory**
```typescript
// src/test/mocks/factory/userFactory.ts
import { faker } from '@faker-js/faker';
import { User } from '@/types/user';

export class UserFactory {
  static create(overrides: Partial<User> = {}): User {
    return {
      id: faker.datatype.number(),
      username: faker.internet.userName(),
      email: faker.internet.email(),
      firstName: faker.name.firstName(),
      lastName: faker.name.lastName(),
      isActive: faker.datatype.boolean(),
      roles: [],
      createdAt: faker.date.past(),
      updatedAt: faker.date.recent(),
      ...overrides
    };
  }

  static createMany(count: number, overrides: Partial<User> = {}): User[] {
    return Array.from({ length: count }, () => this.create(overrides));
  }

  static createWithRole(roleName: string): User {
    return this.create({
      roles: [{ id: 1, name: roleName, permissions: [] }]
    });
  }
}
```

**测试数据库管理**
```typescript
// src/test/setup/database.ts
import { execSync } from 'child_process';
import { Pool } from 'pg';

export class TestDatabase {
  private static pool: Pool;

  static async setup() {
    // Create test database
    execSync('createdb test_db_e2e', { stdio: 'ignore' });

    this.pool = new Pool({
      user: 'postgres',
      host: 'localhost',
      database: 'test_db_e2e',
      password: 'postgres',
      port: 5432
    });

    // Run migrations
    execSync('npm run migrate:test', { stdio: 'inherit' });
  }

  static async teardown() {
    if (this.pool) {
      await this.pool.end();
    }
    execSync('dropdb test_db_e2e', { stdio: 'ignore' });
  }

  static async reset() {
    await this.pool.query('TRUNCATE TABLE users, roles, user_roles RESTART IDENTITY CASCADE');
  }

  static async seed() {
    const users = UserFactory.createMany(10);
    for (const user of users) {
      await this.pool.query(
        'INSERT INTO users (username, email, first_name, last_name, is_active) VALUES ($1, $2, $3, $4, $5)',
        [user.username, user.email, user.firstName, user.lastName, user.isActive]
      );
    }
  }
}
```

### 测试策略和最佳实践

#### 1. 测试金字塔
- **单元测试 (70%)**: 快速、隔离的组件和函数测试
- **集成测试 (20%)**: 模块间交互测试
- **E2E测试 (10%)**: 关键用户流程测试

#### 2. 测试覆盖率要求
- 核心业务逻辑: 95%
- UI组件: 85%
- 工具函数: 90%
- 整体覆盖率: 80%

#### 3. 测试命名规范
```typescript
describe('ComponentName', () => {
  describe('when [condition]', () => {
    it('should [expected behavior]', () => {});
  });
});
```

### 性能测试

#### 1. 组件性能测试
```typescript
// src/test/performance/UserList.performance.test.tsx
import { render } from '@testing-library/react';
import { UserList } from '@/components/UserList';
import { Performance } from '@/test/utils/performance';

describe('UserList Performance', () => {
  it('renders large list efficiently', () => {
    const users = UserFactory.createMany(1000);

    const performance = new Performance();
    performance.start();

    render(<UserList users={users} />);

    const duration = performance.end();
    expect(duration).toBeLessThan(100); // 100ms threshold
  });
});
```

#### 2. 负载测试脚本
```typescript
// scripts/load-test.js
import { check } from 'k6';
import http from 'k6/http';

export let options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 0 }
  ]
};

export default function() {
  let response = http.get('http://localhost:3000/api/users');
  check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500
  });
}
```

### 验收标准

#### 1. 测试覆盖率
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试覆盖关键流程
- [ ] E2E测试覆盖核心用户场景

#### 2. 测试质量
- [ ] 所有测试用例通过
- [ ] 测试执行时间合理
- [ ] 测试环境稳定可靠

#### 3. CI/CD集成
- [ ] 自动化测试流水线配置
- [ ] 代码提交触发测试
- [ ] 测试失败阻止合并

#### 4. 报告和监控
- [ ] 测试报告自动生成
- [ ] 覆盖率趋势监控
- [ ] 性能回归检测

### 风险评估

#### 1. 技术风险
- **风险**: 测试环境不稳定
- **缓解**: 容器化测试环境
- **应急**: 本地测试环境备份

#### 2. 维护风险
- **风险**: 测试代码与实现不同步
- **缓解**: 代码审查和自动化检测
- **应急**: 定期测试更新计划

#### 3. 性能风险
- **风险**: E2E测试执行时间过长
- **缓解**: 并行执行和智能选择
- **应急**: 分级测试策略

### 交付物

1. **测试代码**
   - 单元测试用例
   - 集成测试场景
   - E2E测试脚本

2. **配置文件**
   - Jest配置
   - Playwright配置
   - CI/CD流水线

3. **工具和脚本**
   - Mock数据工厂
   - 测试数据库管理
   - 性能测试工具

### 后续工作

1. **测试增强**
   - 视觉回归测试
   - 可访问性测试
   - 安全漏洞扫描

2. **自动化改进**
   - 智能测试选择
   - 并行测试优化
   - 测试数据生成

3. **监控提升**
   - 实时测试状态
   - 测试质量分析
   - 缺陷趋势追踪

---

### 进度追踪

| 里程碑 | 预期日期 | 状态 | 备注 |
|--------|----------|------|------|
| 测试框架搭建 | 2025-12-18 | 待开始 | |
| 单元测试编写 | 2025-12-20 | 待开始 | |
| 集成测试实施 | 2025-12-21 | 待开始 | |
| E2E测试开发 | 2025-12-22 | 待开始 | |
| CI/CD配置 | 2025-12-23 | 待开始 | |
| 性能测试 | 2025-12-24 | 待开始 | |
| 文档和培训 | 2025-12-25 | 待开始 | |

### 相关资源

- [Jest测试框架](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright E2E测试](https://playwright.dev/)
- [GitHub Actions文档](https://docs.github.com/en/actions)
- [测试金字塔最佳实践](https://martinfowler.com/bliki/TestPyramid.html)