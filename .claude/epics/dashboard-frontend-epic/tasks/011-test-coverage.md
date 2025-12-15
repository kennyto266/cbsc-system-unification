---
name: task-011-test-coverage
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: testing-frontend-team
phase: 4
estimated_hours: 64
priority: high
---

# Task #11: 測試覆蓋

## 📋 任務描述
建立 CBSC Dashboard 的完整測試體系，包括單元測試（>90%覆蓋率）、集成測試、E2E 測試和性能測試報告，確保代碼質量和系統穩定性。

## 🎯 具體要求

### 11.1 單元測試 (>90%覆蓋率)
- [ ] 組件測試（React Testing Library）
- [ ] Hook 測試自定義邏輯
- [ ] 工具函數測試
- [ ] API 服務測試
- [ ] Redux reducer 測試
- [ ] Mock 數據和服務

### 11.2 集成測試
- [ ] 組件間交互測試
- [ ] API 集成測試
- [ ] WebSocket 通信測試
- [ ] 狀態管理集成測試
- [ ] 路由導航測試
- [ ] 數據流測試

### 11.3 E2E 測試
- [ ] 用戶登錄流程
- [ ] 策略創建和管理
- [ ] 數據可視化交互
- [ ] 報告生成功能
- [ ] 響應式布局測試
- [ ] 錯誤處理測試

### 11.4 性能測試報告
- [ ] Lighthouse CI 集成
- [ ] 性能基準測試
- [ ] 內存泄漏檢測
- [ ] 渲染性能測試
- [ ] 網絡性能分析
- [ ] 性能回歸測試

## ✅ 驗收標準

1. **覆蓋率要求**
   - [ ] 語句覆蓋率 > 90%
   - [ ] 分支覆蓋率 > 85%
   - [ ] 函數覆蓋率 > 95%
   - [ ] 行覆蓋率 > 90%

2. **質量標準**
   - [ ] 所有关鍵路徑測試覆蓋
   - [ ] 測試通過率 100%
   - [ ] 測試執行時間 < 5 分鐘
   - [ ] 無測試偽陽性

3. **文檔要求**
   - [ ] 測試覆蓋率報告
   - [ ] 測試策略文檔
   - [ ] 測試用例文檔
   - [ ] 性能基準報告

## 🔧 技術要求

### 測試配置設置
```typescript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/test/setup.ts'],
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@components/(.*)$': '<rootDir>/src/components/$1',
    '^@pages/(.*)$': '<rootDir>/src/pages/$1',
    '^@hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/utils/$1'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/test/**/*',
    '!src/**/*.stories.tsx'
  ],
  coverageThreshold: {
    global: {
      branches: 85,
      functions: 95,
      lines: 90,
      statements: 90
    }
  },
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}',
    '<rootDir>/src/**/*.{test,spec}.{ts,tsx}'
  ],
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.test.json'
    }
  }
};

// src/test/setup.ts
import '@testing-library/jest-dom';
import { configure } from '@testing-library/react';
import { server } from './server';

// 配置 Testing Library
configure({ testIdAttribute: 'data-testid' });

// 啟動 Mock 服務器
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock Intersection Observer
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
};

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
```

### 組件測試示例
```typescript
// src/components/dashboard/WidgetGrid.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { WidgetGrid } from './WidgetGrid';
import { mockWidgets } from '@/test/mocks/data';

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('WidgetGrid', () => {
  it('renders all widgets correctly', () => {
    renderWithTheme(<WidgetGrid widgets={mockWidgets} />);

    mockWidgets.forEach(widget => {
      expect(screen.getByTestId(`widget-${widget.id}`)).toBeInTheDocument();
      expect(screen.getByText(widget.title)).toBeInTheDocument();
    });
  });

  it('handles widget drag and drop', async () => {
    const onLayoutChange = jest.fn();
    renderWithTheme(
      <WidgetGrid widgets={mockWidgets} onLayoutChange={onLayoutChange} />
    );

    const firstWidget = screen.getByTestId('widget-1');
    const secondWidget = screen.getByTestId('widget-2');

    // 模擬拖拽
    fireEvent.dragStart(firstWidget);
    fireEvent.dragEnter(secondWidget);
    fireEvent.drop(secondWidget);

    await waitFor(() => {
      expect(onLayoutChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ id: '2', x: 0, y: 0 }),
          expect.objectContaining({ id: '1', x: 0, y: 1 })
        ])
      );
    });
  });

  it('handles widget resize', async () => {
    const onLayoutChange = jest.fn();
    renderWithTheme(
      <WidgetGrid widgets={mockWidgets} onLayoutChange={onLayoutChange} />
    );

    const resizeHandle = screen.getByTestId('widget-1-resize');

    fireEvent.mouseDown(resizeHandle);
    fireEvent.mouseMove(resizeHandle, { clientX: 100, clientY: 100 });
    fireEvent.mouseUp(resizeHandle);

    await waitFor(() => {
      expect(onLayoutChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: '1',
            w: 3,
            h: 3
          })
        ])
      );
    });
  });

  it('maintains widget state on re-render', () => {
    const { rerender } = renderWithTheme(
      <WidgetGrid widgets={mockWidgets} />
    );

    // 修改 widget 狀態
    const widget = screen.getByTestId('widget-1');
    fireEvent.click(screen.getByTestId('widget-1-settings'));

    // 重新渲染
    rerender(
      <ThemeProvider>
        <WidgetGrid widgets={mockWidgets} />
      </ThemeProvider>
    );

    // 驗證狀態保持
    expect(screen.getByTestId('widget-1-settings-panel')).toBeInTheDocument();
  });
});

// 自定義 Hook 測試
// src/hooks/useWebSocket.test.ts
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';
import { createMockWebSocket } from '@/test/mocks/websocket';

describe('useWebSocket', () => {
  let mockWs: ReturnType<typeof createMockWebSocket>;

  beforeEach(() => {
    mockWs = createMockWebSocket();
    global.WebSocket = jest.fn(() => mockWs) as any;
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('connects on mount', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8080');
    expect(result.current.connectionState).toBe('connecting');
  });

  it('handles connection success', async () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

    act(() => {
      mockWs.open();
    });

    expect(result.current.connectionState).toBe('connected');
    expect(result.current.isConnected).toBe(true);
  });

  it('sends messages when connected', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

    act(() => {
      mockWs.open();
      result.current.sendMessage({ type: 'test', data: 'hello' });
    });

    expect(mockWs.send).toHaveBeenCalledWith(
      JSON.stringify({ type: 'test', data: 'hello', id: expect.any(String), timestamp: expect.any(Number) })
    );
  });

  it('queues messages when disconnected', () => {
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080', { autoConnect: false }));

    result.current.sendMessage({ type: 'test', data: 'queued' });

    // 連接後應發送排隊的消息
    act(() => {
      result.current.connect();
      mockWs.open();
    });

    expect(mockWs.send).toHaveBeenCalledWith(
      expect.stringContaining('queued')
    );
  });

  it('subscribes to channels', () => {
    const callback = jest.fn();
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

    act(() => {
      mockWs.open();
      const unsubscribe = result.current.subscribe('test-channel', callback);

      // 模擬接收消息
      mockWs.message({
        data: JSON.stringify({
          type: 'data',
          channel: 'test-channel',
          data: { value: 42 }
        })
      });

      unsubscribe();
    });

    expect(callback).toHaveBeenCalledWith({ value: 42 });
  });

  it('automatically reconnects on disconnect', () => {
    jest.useFakeTimers();
    const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

    act(() => {
      mockWs.open();
      mockWs.close();
    });

    // 應該嘗試重連
    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(global.WebSocket).toHaveBeenCalledTimes(2);

    jest.useRealTimers();
  });
});
```

### 集成測試示例
```typescript
// src/test/integration/strategyManagement.test.tsx
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { store } from '@/store';
import { StrategyManagement } from '@/pages/StrategyManagement';

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false }
  }
});

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = createTestQueryClient();

  return render(
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          {component}
        </BrowserRouter>
      </QueryClientProvider>
    </Provider>
  );
};

describe('Strategy Management Integration', () => {
  it('completes full strategy creation workflow', async () => {
    renderWithProviders(<StrategyManagement />);

    // 1. 點擊創建策略按鈕
    fireEvent.click(screen.getByText('創建策略'));

    // 2. 填寫基本信息
    fireEvent.change(screen.getByLabelText('策略名稱'), {
      target: { value: 'Test Strategy' }
    });
    fireEvent.change(screen.getByLabelText('描述'), {
      target: { value: 'Test description' }
    });

    // 3. 選擇策略類型
    fireEvent.click(screen.getByText('下一步'));
    fireEvent.selectEvent(screen.getByLabelText('策略類型'), '趨勢策略');

    // 4. 配置參數
    fireEvent.click(screen.getByText('下一步'));
    fireEvent.change(screen.getByLabelText('初始資金'), {
      target: { value: '10000' }
    });

    // 5. 保存策略
    fireEvent.click(screen.getByText('保存策略'));

    // 6. 驗證成功
    await waitFor(() => {
      expect(screen.getByText('策略創建成功')).toBeInTheDocument();
    });

    // 7. 驗證策略出現在列表中
    await waitFor(() => {
      expect(screen.getByText('Test Strategy')).toBeInTheDocument();
    });
  });

  it('handles real-time data updates', async () => {
    renderWithProviders(<StrategyManagement />);

    // 等待策略列表加載
    await waitFor(() => {
      expect(screen.getByTestId('strategy-list')).toBeInTheDocument();
    });

    // 模擬實時數據更新
    const updatedStrategy = {
      id: '1',
      name: 'Strategy 1',
      status: 'running',
      performance: { profit: 1500 }
    };

    fireEvent(
      window,
      new MessageEvent('message', {
        data: JSON.stringify({
          type: 'strategy_update',
          channel: 'strategies',
          data: updatedStrategy
        })
      })
    );

    // 驗證 UI 更新
    await waitFor(() => {
      expect(screen.getByText('1500')).toBeInTheDocument();
      expect(screen.getByTestId('status-running')).toBeInTheDocument();
    });
  });
});
```

### E2E 測試示例
```typescript
// e2e/tests/strategyManagement.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Strategy Management E2E', () => {
  test.beforeEach(async ({ page }) => {
    // 登錄
    await page.goto('/login');
    await page.fill('[data-testid=username]', 'testuser');
    await page.fill('[data-testid=password]', 'password123');
    await page.click('[data-testid=login-button]');

    // 等待登錄完成
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create and manage strategies', async ({ page }) => {
    // 導航到策略管理頁面
    await page.click('[data-testid=strategies-menu]');
    await expect(page).toHaveURL('/strategies');

    // 創建新策略
    await page.click('[data-testid=create-strategy-btn]');

    // 步驟 1: 基本信息
    await page.fill('[data-testid=strategy-name]', 'E2E Test Strategy');
    await page.fill('[data-testid=strategy-description]', 'Created by E2E test');
    await page.click('[data-testid=next-step]');

    // 步驟 2: 參數配置
    await page.selectOption('[data-testid=strategy-type]', 'trend');
    await page.fill('[data-testid=initial-capital]', '50000');
    await page.click('[data-testid=next-step]');

    // 步驟 3: 風險控制
    await page.fill('[data-testid=max-drawdown]', '20');
    await page.fill('[data-testid=stop-loss]', '10');
    await page.click('[data-testid=save-strategy]');

    // 驗證成功消息
    await expect(page.locator('[data-testid=success-message]')).toContainText('策略創建成功');

    // 返回列表並驗證策略存在
    await page.click('[data-testid=back-to-list]');
    await expect(page.locator('text=E2E Test Strategy')).toBeVisible();

    // 啟動策略
    await page.click('[data-testid=strategy-action-0]');
    await page.click('[data-testid=start-strategy]');

    // 驗證策略狀態更新
    await expect(page.locator('[data-testid=strategy-status-0]')).toHaveText('運行中');

    // 停止策略
    await page.click('[data-testid=strategy-action-0]');
    await page.click('[data-testid=stop-strategy]');

    // 驗證狀態更新
    await expect(page.locator('[data-testid=strategy-status-0]')).toHaveText('已停止');
  });

  test('should display real-time data updates', async ({ page }) => {
    await page.goto('/strategies');

    // 等待數據加載
    await page.waitForSelector('[data-testid=strategy-list]');

    // 獲取初始性能值
    const initialPerformance = await page.textContent('[data-testid=performance-0]');

    // 模擬 WebSocket 數據更新
    await page.evaluate(() => {
      window.wsMock.send(JSON.stringify({
        type: 'strategy_update',
        channel: 'strategies',
        data: {
          id: '0',
          performance: { profit: 2500 },
          status: 'running'
        }
      }));
    });

    // 驗證數據更新
    await expect(page.locator('[data-testid=performance-0]')).toContainText('2500');
    await expect(page.locator('[data-testid=status-0]')).toHaveText('運行中');
  });

  test('should generate and export reports', async ({ page }) => {
    await page.goto('/strategies/1/reports');

    // 選擇報告類型
    await page.selectOption('[data-testid=report-type]', 'performance');

    // 設置日期範圍
    await page.fill('[data-testid=start-date]', '2024-01-01');
    await page.fill('[data-testid=end-date]', '2024-01-31');

    // 生成報告
    await page.click('[data-testid=generate-report]');

    // 等待報告生成
    await expect(page.locator('[data-testid=report-preview]')).toBeVisible();

    // 導出 PDF
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid=export-pdf]');
    const download = await downloadPromise;

    // 驗證下載
    expect(download.suggestedFilename()).toMatch(/.*\.pdf$/);

    // 導出 Excel
    const downloadPromise2 = page.waitForEvent('download');
    await page.click('[data-testid=export-excel]');
    const download2 = await downloadPromise2;

    expect(download2.suggestedFilename()).toMatch(/.*\.xlsx$/);
  });
});
```

### 性能測試
```typescript
// src/test/performance/bundle.test.ts
import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { join } from 'path';

describe('Bundle Size Performance', () => {
  const BUNDLE_SIZE_LIMITS = {
    'main.js': 500 * 1024, // 500KB
    'vendor.js': 300 * 1024, // 300KB
    'charts.js': 200 * 1024 // 200KB
  };

  test('main bundle size should be within limit', () => {
    // 構建項目
    execSync('npm run build', { cwd: process.cwd() });

    // 讀取構建結果
    const manifestPath = join(process.cwd(), 'dist/manifest.json');
    const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));

    // 檢查每個 bundle 大小
    for (const [file, limit] of Object.entries(BUNDLE_SIZE_LIMITS)) {
      const filePath = join(process.cwd(), 'dist', manifest[file]);
      const stats = readFileSync(filePath);
      const size = stats.length;

      expect(size).toBeLessThan(limit);
      console.log(`${file}: ${formatBytes(size)} (limit: ${formatBytes(limit)})`);
    }
  });
});

// Lighthouse CI 配置
// .lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/dashboard'],
      startServerCommand: 'npm run preview',
      startServerReadyPattern: 'Local:',
      startServerReadyTimeout: 30000
    },
    assert: {
      assertions: {
        'categories:performance': ['warn', { minScore: 0.8 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['off'],
        'categories:pwa': 'off'
      }
    },
    upload: {
      target: 'temporary-public-storage'
    }
  }
};

// 性能回歸測試
// src/test/performance/render.test.tsx
import { render, screen } from '@testing-library/react';
import { Performance } from '../utils/performance';

describe('Render Performance', () => {
  test('Dashboard should render within performance budget', async () => {
    const renderTime = await Performance.measureAsync('dashboard-render', () => {
      render(<Dashboard />);
    });

    expect(renderTime).toBeLessThan(1000); // 1 second
  });

  test('Chart with large dataset should render efficiently', async () => {
    const largeDataset = Array.from({ length: 10000 }, (_, i) => ({
      x: i,
      y: Math.sin(i / 100) * 100
    }));

    const renderTime = await Performance.measureAsync('chart-render', () => {
      render(<LineChart data={largeDataset} />);
    });

    expect(renderTime).toBeLessThan(500); // 500ms
  });
});
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| 單元測試編寫 | 32小時 | 測試工程師 + 前端工程師 A |
| 集成測試設計 | 16小時 | 測試工程師 + 前端工程師 B |
| E2E 測試實施 | 8小時 | 測試工程師 |
| 性能測試配置 | 8小時 | 測試工程師 + 前端工程師 A |
| **總計** | **64小時** | |

## 🔗 依賴關係
- 前置任務：Task #10 (性能優化)
- 後續任務：Task #12 (安全加固)

## 📝 注意事項
1. 保持測試獨立性和可重複性
2. 定期更新測試用例
3. 監控測試執行時間
4. 確保測試數據的及時清理
5. 建立測試質量門檻

## 🧪 CI/CD 集成
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies
      run: npm ci

    - name: Run lint
      run: npm run lint

    - name: Run type check
      run: npm run type-check

    - name: Run unit tests
      run: npm run test:unit -- --coverage

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info

    - name: Run E2E tests
      run: npm run test:e2e

    - name: Run Lighthouse CI
      run: |
        npm run build
        npm run lhci
      env:
        LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

## 📚 相關文檔
- [Testing Library 文檔](https://testing-library.com/)
- [Jest 文檔](https://jestjs.io/)
- [Playwright 文檔](https://playwright.dev/)
- [Lighthouse CI 文檔](https://github.com/GoogleChrome/lighthouse-ci)
- [React Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)