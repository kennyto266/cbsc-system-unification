---
name: task-010-performance-optimization
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-team
phase: 3
estimated_hours: 48
priority: medium
---

# Task #10: 性能優化

## 📋 任務描述
對 CBSC Dashboard 進行全面的性能優化，包括代碼分割實施、圖片懶加載、虛擬滾動優化和緩存策略實施，確保應用在大數據量和複雜場景下的流暢運行。

## 🎯 具體要求

### 10.1 代碼分割實施
- [ ] 路由級代碼分割（React.lazy）
- [ ] 組件級動態導入
- [ ] 第三方庫單獨打包
- [ ] 公共依賴提取
- [ ] 預加載關鍵資源
- [ ] Service Worker 緩存策略

### 10.2 圖片懶加載
- [ ] Intersection Observer 實現
- [ ] 圖片預加載策略
- [ ] 響應式圖片處理
- [ ] WebP 格式支持
- [ ] 漸進式加載效果
- [ ] 錯誤處理機制

### 10.3 虛擬滾動優化
- [ ] 大列表虛擬化渲染
- [ ] 動態高度支持
- [ ] 雙向緩衝區實現
- [ ] 滾動位置保持
- [ ] 批量更新優化
- [ ] 內存回收機制

### 10.4 緩存策略實施
- [ ] 查詢結果緩存（React Query）
- [ ] 計算結果緩存（Memoization）
- [ ] 組件狀態緩存
- [ ] 本地存儲優化
- [ ] 緩存失效策略
- [ ] 緩存預熱機制

## ✅ 驗收標準

1. **性能指標**
   - [ ] FCP (首次內容繪製) < 1.5 秒
   - [ ] LCP (最大內容繪製) < 2.5 秒
   - [ ] FID (首次輸入延遲) < 100ms
   - [ ] CLS (累積佈局偏移) < 0.1
   - [ ] TTI (可交互時間) < 3.8 秒

2. **資源優化**
   - [ ] JS 包大小減少 40%
   - [ ] 圖片資源大小減少 30%
   - [ ] 緩存命中率 > 80%
   - [ ] 內存使用穩定無泄漏

3. **用戶體驗**
   - [ ] 頁面切換無卡頓
   - [ ] 大數據渲染流暢
   - [ ] 離線功能可用
   - [ ] 網絡條件適應

## 🔧 技術要求

### 代碼分割配置
```typescript
//路由級分割 - router/index.tsx
import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// 懶加載組件
const Dashboard = lazy(() => import('@/pages/Dashboard').then(module => ({
  default: module.Dashboard
})));

const Strategies = lazy(() => import('@/pages/Strategies').then(module => ({
  default: module.Strategies
})));

const Reports = lazy(() => import('@/pages/Reports').then(module => ({
  default: module.Reports
})));

// 預加載關鍵路由
const preloadRoute = (routePath: string) => {
  const componentMap: Record<string, () => Promise<any>> = {
    '/strategies': () => import('@/pages/Strategies'),
    '/reports': () => import('@/pages/Reports')
  };

  componentMap[routePath]?.();
};

export const AppRouter = () => {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/strategies/*" element={<Strategies />} />
        <Route path="/reports/*" element={<Reports />} />
      </Routes>
    </Suspense>
  );
};

// Vite 配置 - vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // 將第三方庫單獨打包
          'vendor': [
            'react',
            'react-dom',
            'react-router-dom',
            '@reduxjs/toolkit',
            'react-redux'
          ],
          // 圖表庫單獨打包
          'charts': [
            'chart.js',
            'react-chartjs-2',
            'plotly.js',
            'react-plotly.js'
          ],
          // UI 庫單獨打包
          'ui': [
            '@headlessui/react',
            '@heroicons/react',
            'tailwindcss'
          ]
        }
      }
    },
    // 啟用代碼壓縮和 Tree Shaking
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom'
    ]
  }
});

// 組件級動態導入
const HeavyComponent = lazy(() =>
  import('@/components/HeavyComponent').then(module => ({
    default: module.HeavyComponent
  }))
);

// 使用示例
export const PageWithHeavyComponent = () => {
  const [showComponent, setShowComponent] = useState(false);

  return (
    <div>
      <button onClick={() => setShowComponent(true)}>
        Load Heavy Component
      </button>

      {showComponent && (
        <Suspense fallback={<LoadingSpinner />}>
          <HeavyComponent />
        </Suspense>
      )}
    </div>
  );
};
```

### 高性能圖片組件
```typescript
// components/ui/OptimizedImage.tsx
interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  lazy?: boolean;
  webp?: boolean;
  placeholder?: 'blur' | 'empty';
  onLoad?: () => void;
  onError?: () => void;
}

export const OptimimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  className = '',
  lazy = true,
  webp = true,
  placeholder = 'blur',
  onLoad,
  onError
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(!lazy);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);
  const placeholderRef = useRef<HTMLDivElement>(null);

  // 生成圖片 URL
  const generateImageUrl = useCallback((originalSrc: string) => {
    if (!webp) return originalSrc;

    // 如果 WebP 支持，使用 WebP 格式
    if (supportsWebP()) {
      return originalSrc.replace(/\.(jpg|jpeg|png)$/i, '.webp');
    }
    return originalSrc;
  }, [webp]);

  // 檢查 WebP 支持
  const supportsWebP = useCallback(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1;
    canvas.height = 1;
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  }, []);

  // 創建模糊佔位符
  const createBlurPlaceholder = useCallback((width: number, height: number) => {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    if (ctx) {
      // 創建漸變背景
      const gradient = ctx.createLinearGradient(0, 0, width, height);
      gradient.addColorStop(0, '#f0f0f0');
      gradient.addColorStop(1, '#e0e0e0');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);
    }

    return canvas.toDataURL();
  }, []);

  // Intersection Observer 用於懶加載
  useEffect(() => {
    if (!lazy || isInView) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px' // 提前 50px 開始加載
      }
    );

    if (placeholderRef.current) {
      observer.observe(placeholderRef.current);
    }

    return () => observer.disconnect();
  }, [lazy, isInView]);

  // 預加載圖片
  useEffect(() => {
    if (!isInView || hasError) return;

    const img = new Image();
    img.src = generateImageUrl(src);

    img.onload = () => {
      setIsLoaded(true);
      onLoad?.();
    };

    img.onerror = () => {
      setHasError(true);
      onError?.();
    };

    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [src, isInView, generateImageUrl, onLoad, onError, hasError]);

  // 渲染佔位符
  const renderPlaceholder = () => {
    if (hasError) {
      return (
        <div className="flex items-center justify-center h-full bg-gray-100 dark:bg-gray-800">
          <PhotoIcon className="h-12 w-12 text-gray-400" />
        </div>
      );
    }

    if (placeholder === 'blur' && width && height) {
      return (
        <img
          src={createBlurPlaceholder(width, height)}
          alt=""
          className="transition-opacity duration-300"
        />
      );
    }

    return <div className="bg-gray-100 dark:bg-gray-800 animate-pulse" />;
  };

  return (
    <div ref={placeholderRef} className={`relative overflow-hidden ${className}`}>
      {isInView && (
        <img
          ref={imgRef}
          src={generateImageUrl(src)}
          alt={alt}
          width={width}
          height={height}
          loading={lazy ? 'lazy' : 'eager'}
          className={`
            transition-opacity duration-300
            ${isLoaded ? 'opacity-100' : 'opacity-0'}
          `}
          style={{
            objectFit: 'cover'
          }}
        />
      )}

      {!isLoaded && renderPlaceholder()}
    </div>
  );
};
```

### 虛擬滾動實現
```typescript
// hooks/useVirtualScroll.ts
interface VirtualScrollOptions<T> {
  items: T[];
  itemHeight: number | ((index: number, item: T) => number);
  containerHeight: number;
  overscan?: number;
  getItemKey?: (index: number, item: T) => string | number;
}

export const useVirtualScroll = <T>({
  items,
  itemHeight,
  containerHeight,
  overscan = 5,
  getItemKey = (_, index) => index
}: VirtualScrollOptions<T>) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const scrollTimeoutRef = useRef<NodeJS.Timeout>();

  // 計算項目高度
  const getItemHeightCalculated = useCallback((index: number, item: T) => {
    return typeof itemHeight === 'function' ? itemHeight(index, item) : itemHeight;
  }, [itemHeight]);

  // 緩存項目位置信息
  const itemPositions = useMemo(() => {
    const positions: number[] = [0];
    let totalHeight = 0;

    for (let i = 0; i < items.length; i++) {
      const height = getItemHeightCalculated(i, items[i]);
      totalHeight += height;
      positions.push(totalHeight);
    }

    return { positions, totalHeight };
  }, [items, getItemHeightCalculated]);

  // 二分查找當前可見項目範圍
  const findVisibleRange = useCallback((scrollTop: number) => {
    const { positions } = itemPositions;
    const containerTop = scrollTop;
    const containerBottom = scrollTop + containerHeight;

    // 查找第一個可見項目
    let startIndex = 0;
    let endIndex = items.length - 1;

    while (startIndex < endIndex) {
      const midIndex = Math.floor((startIndex + endIndex) / 2);
      const midPosition = positions[midIndex];

      if (midPosition < containerTop) {
        startIndex = midIndex + 1;
      } else {
        endIndex = midIndex;
      }
    }

    // 查找最後一個可見項目
    let lastVisibleIndex = startIndex;
    while (
      lastVisibleIndex < items.length &&
      positions[lastVisibleIndex] < containerBottom
    ) {
      lastVisibleIndex++;
    }

    // 添加過度渲染區域
    startIdx = Math.max(0, startIndex - overscan);
    endIdx = Math.min(items.length - 1, lastVisibleIndex + overscan);

    return { startIndex: startIdx, endIndex: endIdx };
  }, [itemPositions, items.length, containerHeight, overscan]);

  const { startIndex, endIndex } = findVisibleRange(scrollTop);

  // 處理滾動事件
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    const newScrollTop = e.currentTarget.scrollTop;
    setScrollTop(newScrollTop);

    setIsScrolling(true);

    // 清除之前的定時器
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // 設置滾動結束檢測
    scrollTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, 150);
  }, []);

  // 可見項目數據
  const visibleItems = useMemo(() => {
    return items.slice(startIndex, endIndex + 1).map((item, index) => ({
      item,
      index: startIndex + index,
      key: getItemKey(startIndex + index, item)
    }));
  }, [items, startIndex, endIndex, getItemKey]);

  // 頂部偏移量
  const offsetY = itemPositions.positions[startIndex] || 0;

  // 清理定時器
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return {
    visibleItems,
    totalHeight: itemPositions.totalHeight,
    offsetY,
    isScrolling,
    handleScroll,
    scrollElementProps: {
      onScroll: handleScroll,
      style: {
        height: containerHeight,
        overflow: 'auto'
      }
    }
  };
};

// 虛擬滾動組件
export const VirtualList = <T,>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  getItemKey,
  overscan = 5
}: VirtualListProps<T>) => {
  const {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll,
    scrollElementProps
  } = useVirtualScroll({
    items,
    itemHeight,
    containerHeight,
    overscan,
    getItemKey
  });

  return (
    <div {...scrollElementProps}>
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map(({ item, index, key }) => (
            <div key={key} style={{ height: typeof itemHeight === 'function' ? itemHeight(index, item) : itemHeight }}>
              {renderItem(item, index)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
```

### 緩存策略實現
```typescript
// cache/QueryCache.ts
export class QueryCache {
  private cache = new Map<string, CacheEntry>();
  private maxSize: number;
  private defaultTTL: number;

  constructor(maxSize: number = 100, defaultTTL: number = 5 * 60 * 1000) {
    this.maxSize = maxSize;
    this.defaultTTL = defaultTTL;
  }

  // 設置緩存
  set(key: string, value: any, ttl?: number): void {
    // 如果緩存已滿，刪除最舊的條目
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }

    this.cache.set(key, {
      value,
      timestamp: Date.now(),
      ttl: ttl || this.defaultTTL
    });
  }

  // 獲取緩存
  get(key: string): any | null {
    const entry = this.cache.get(key);

    if (!entry) return null;

    // 檢查是否過期
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    // LRU: 移到最後
    this.cache.delete(key);
    this.cache.set(key, entry);

    return entry.value;
  }

  // 清除緩存
  clear(): void {
    this.cache.clear();
  }

  // 刪除指定緩存
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  // 獲取緩存大小
  size(): number {
    return this.cache.size;
  }

  // 清理過期緩存
  cleanup(): number {
    let deleted = 0;
    const now = Date.now();

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key);
        deleted++;
      }
    }

    return deleted;
  }
}

// React Query 配置
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 分鐘
      cacheTime: 10 * 60 * 1000, // 10 分鐘
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000)
    },
    mutations: {
      retry: 1
    }
  }
});

// API 查詢封裝
export const useApiQuery = <T>(
  key: string | string[],
  fetcher: () => Promise<T>,
  options?: Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>
) => {
  return useQuery({
    queryKey: Array.isArray(key) ? key : [key],
    queryFn: fetcher,
    ...options
  });
};

// 計算結果緩存 Hook
export const useComputedCache = <T extends (...args: any[]) => any>(
  fn: T,
  deps: React.DependencyList
) => {
  const cacheRef = useRef(new Map<string, ReturnType<T>>());

  return useCallback((...args: Parameters<T>) => {
    const key = JSON.stringify(args);

    if (cacheRef.current.has(key)) {
      return cacheRef.current.get(key);
    }

    const result = fn(...args);
    cacheRef.current.set(key, result);
    return result;
  }, deps);
};

// 本地存儲優化
export class LocalStorageManager {
  private prefix: string;

  constructor(prefix: string = 'cbsc_') {
    this.prefix = prefix;
  }

  // 設置項目
  set<T>(key: string, value: T, ttl?: number): void {
    const item: StorageItem<T> = {
      value,
      timestamp: Date.now(),
      ttl
    };

    try {
      localStorage.setItem(this.prefix + key, JSON.stringify(item));
    } catch (error) {
      // 存儲空間不足，清理舊數據
      this.cleanup();
      // 重試
      try {
        localStorage.setItem(this.prefix + key, JSON.stringify(item));
      } catch (retryError) {
        console.error('Failed to save to localStorage:', retryError);
      }
    }
  }

  // 獲取項目
  get<T>(key: string): T | null {
    try {
      const itemStr = localStorage.getItem(this.prefix + key);
      if (!itemStr) return null;

      const item: StorageItem<T> = JSON.parse(itemStr);

      // 檢查是否過期
      if (item.ttl && Date.now() - item.timestamp > item.ttl) {
        localStorage.removeItem(this.prefix + key);
        return null;
      }

      return item.value;
    } catch (error) {
      console.error('Failed to read from localStorage:', error);
      return null;
    }
  }

  // 刪除項目
  remove(key: string): void {
    localStorage.removeItem(this.prefix + key);
  }

  // 清理所有項目
  clear(): void {
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => localStorage.removeItem(key));
  }

  // 清理過期項目
  cleanup(): void {
    const now = Date.now();

    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => {
        try {
          const item: StorageItem<any> = JSON.parse(localStorage.getItem(key) || '');
          if (item.ttl && now - item.timestamp > item.ttl) {
            localStorage.removeItem(key);
          }
        } catch {
          // 刪損壞的數據
          localStorage.removeItem(key);
        }
      });
  }

  // 獲取存儲大小
  getSize(): number {
    let size = 0;
    Object.keys(localStorage)
      .filter(key => key.startsWith(this.prefix))
      .forEach(key => {
        size += localStorage.getItem(key)?.length || 0;
      });
    return size;
  }
}

// 性能監控
export const PerformanceMonitor = {
  // 監控組件渲染性能
  measureRender: (componentName: string, renderFn: () => void) => {
    const startMark = `${componentName}-render-start`;
    const endMark = `${componentName}-render-end`;
    const measureName = `${componentName}-render`;

    performance.mark(startMark);
    renderFn();
    performance.mark(endMark);
    performance.measure(measureName, startMark, endMark);

    const measure = performance.getEntriesByName(measureName)[0];
    console.log(`${componentName} render time:`, measure.duration);

    // 清理標記
    performance.clearMarks(startMark);
    performance.clearMarks(endMark);
    performance.clearMeasures(measureName);
  },

  // 監控異步操作性能
  measureAsync: async <T>(operationName: string, asyncFn: () => Promise<T>): Promise<T> => {
    const start = performance.now();
    try {
      const result = await asyncFn();
      const duration = performance.now() - start;
      console.log(`${operationName} completed in:`, duration, 'ms');
      return result;
    } catch (error) {
      const duration = performance.now() - start;
      console.error(`${operationName} failed after:`, duration, 'ms', error);
      throw error;
    }
  }
};
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| 代碼分割實施 | 16小時 | 前端工程師 A |
| 圖片懶加載 | 8小時 | 前端工程師 B |
| 虛擬滾動優化 | 16小時 | 前端工程師 A |
| 緩存策略實施 | 8小時 | 前端工程師 B |
| **總計** | **48小時** | |

## 🔗 依賴關係
- 前置任務：Task #9 (移動端適配)
- 後續任務：Task #11 (測試覆蓋)

## 📝 注意事項
1. 定期監控和分析性能指標
2. 實施漸進式優化策略
3. 保持代碼可讀性和可維護性
4. 考慮不同設備的性能差異
5. 建立性能回歸測試

## 🧪 測試要求
```typescript
// __tests__/performance/VirtualList.test.tsx
describe('VirtualList', () => {
  const items = Array.from({ length: 1000 }, (_, i) => ({ id: i, value: `Item ${i}` }));

  test('renders only visible items', () => {
    const { container } = render(
      <VirtualList
        items={items}
        itemHeight={50}
        containerHeight={500}
        renderItem={(item) => <div>{item.value}</div>}
      />
    );

    // 只應渲染可見項目（約 10 個）
    expect(container.children.length).toBeLessThan(20);
  });

  test('handles dynamic item heights', () => {
    const { container } = render(
      <VirtualList
        items={items}
        itemHeight={(index) => (index % 2 === 0 ? 50 : 100)}
        containerHeight={500}
        renderItem={(item) => <div>{item.value}</div>}
      />
    );

    expect(container.children.length).toBeGreaterThan(0);
  });

  test('maintains scroll position', async () => {
    const { container } = render(
      <VirtualList
        items={items}
        itemHeight={50}
        containerHeight={500}
        renderItem={(item) => <div>{item.value}</div>}
      />
    );

    const scrollContainer = container.firstElementChild as HTMLElement;

    // 滾動到中間
    fireEvent.scroll(scrollContainer, { target: { scrollTop: 10000 } });

    // 重新渲染應保持滾動位置
    rerender(
      <VirtualList
        items={items}
        itemHeight={50}
        containerHeight={500}
        renderItem={(item) => <div>{item.value}</div>}
      />
    );

    expect(scrollContainer.scrollTop).toBe(10000);
  });
});
```

## 📚 相關文檔
- [Web Performance Metrics](https://web.dev/vitals/)
- [React.lazy Documentation](https://react.dev/reference/react/lazy)
- [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Web Workers API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API)