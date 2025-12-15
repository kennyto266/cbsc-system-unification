---
name: task-009-mobile-adaptation
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-team
phase: 3
estimated_hours: 64
priority: medium
---

# Task #9: 移動端適配

## 📋 任務描述
將 CBSC Dashboard 進行移動端適配，包括響應式設計優化、觸摸手勢支持、移動端性能優化和 PWA 基礎功能，確保在移動設備上的良好用戶體驗。

## 🎯 具體要求

### 9.1 響應式設計優化
- [ ] 移動端專用佈局（單列、卡片式）
- [ ] 觸摸友好的交互元素（最小 44px）
- [ ] 優化的導航（底部標籤欄、漢堡菜單）
- [ ] 移動端優化的表格（橫向滑動、卡片視圖）
- [ ] 圖表響應式調整
- [ ] 字體和間距適配

### 9.2 觸摸手勢支持
- [ ] 滑動切換頁面/標籤
- [ ] 捏合縮放圖表
- [ ] 長按顯示菜單
- [ ] 左滑刪除/操作
- [ ] 下拉刷新
- [ ] 觸摸反饋動畫

### 9.3 移動端性能優化
- [ ] 圖片懶加載
- [ ] 虛擬滾動長列表
- [ ] 代碼分割和懶加載
- [ ] 減少動畫複雜度
- [ ] 優化觸摸響應
- [ ] 內存使用優化

### 9.4 PWA 基礎功能
- [ ] Service Worker 註冊
- [ ] 離線緩存策略
- [ ] App Manifest 配置
- [ ] 安裝提示橫幅
- [ ] 全屏模式支持
- [ ] 推送通知準備

## ✅ 驗收標準

1. **功能驗收**
   - [ ] 所有頁面在手機上正常顯示
   - [ ] 觸摸手勢流暢響應
   - [ ] PWA 功能正常工作
   - [ ] 離線模式基本可用

2. **性能標準**
   - [ ] 首次加載時間 < 3 秒（3G網絡）
   - [ ] 交互響應時間 < 100ms
   - [ ] 頁面切換動畫 60fps
   - [ ] 內存佔用 < 100MB

3. **兼容性標準**
   - [ ] 支持 iOS 12+ 和 Android 8+
   - [ ] 適配主流屏幕尺寸
   - [ ] 橫豎屏切換正常
   - [ ] 安全區域適配

## 🔧 技術要求

### 響應式佈局組件
```typescript
// components/layout/MobileLayout.tsx
export const MobileLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { isMobile } = useResponsive();

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* 頂部導航欄 */}
      <header className="sticky top-0 z-50 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between h-14 px-4">
          <button
            onClick={() => setIsMenuOpen(true)}
            className="p-2 -ml-2 text-gray-600 hover:text-gray-900 focus:outline-none"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>

          <h1 className="text-lg font-semibold">CBSC Dashboard</h1>

          <NotificationButton />
        </div>
      </header>

      {/* 側邊菜單 */}
      <MobileMenu
        isOpen={isMenuOpen}
        onClose={() => setIsMenuOpen(false)}
      />

      {/* 主內容區 */}
      <main className="flex-1 overflow-auto pb-16">
        {children}
      </main>

      {/* 底部導航 */}
      <BottomNavigation />
    </div>
  );
};

// 手勢處理 Hook
export const useSwipeGesture = (
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void
) => {
  const touchStart = useRef<number>(0);
  const touchEnd = useRef<number>(0);

  const minSwipeDistance = 50;

  const onTouchStart = (e: TouchEvent) => {
    touchEnd.current = 0;
    touchStart.current = e.targetTouches[0].clientX;
  };

  const onTouchMove = (e: TouchEvent) => {
    touchEnd.current = e.targetTouches[0].clientX;
  };

  const onTouchEnd = () => {
    if (!touchStart.current || !touchEnd.current) return;

    const distance = touchStart.current - touchEnd.current;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft();
    }
    if (isRightSwipe && onSwipeRight) {
      onSwipeRight();
    }
  };

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd
  };
};

// 移動端圖表組件
export const MobileChart: React.FC<MobileChartProps> = ({ data, type }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  // 捏合縮放手勢
  const handlers = useGesture({
    onPinch: ({ offset: [d] }) => {
      const newScale = Math.max(0.5, Math.min(3, 1 + d / 100));
      setScale(newScale);
    }
  });

  return (
    <div
      ref={chartRef}
      {...handlers()}
      className="relative overflow-hidden"
      style={{ touchAction: 'none' }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
          transition: 'transform 0.3s ease'
        }}
      >
        <Chart
          data={data}
          type={type}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                enabled: true,
                mode: 'nearest',
                intersect: false
              }
            },
            scales: {
              x: {
                ticks: {
                  maxTicksLimit: 5
                }
              },
              y: {
                ticks: {
                  maxTicksLimit: 5
                }
              }
            },
            interaction: {
              mode: 'nearest',
              axis: 'x',
              intersect: false
            }
          }}
        />
      </div>
    </div>
  );
};

// 移動端表格組件
export const MobileTable: React.FC<MobileTableProps> = ({ data, columns }) => {
  const [viewMode, setViewMode] = useState<'table' | 'card'>('card');

  if (viewMode === 'card') {
    return (
      <div className="space-y-4">
        {data.map((row, index) => (
          <Card key={index} className="p-4">
            {columns.map(column => (
              <div key={column.key} className="flex justify-between py-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {column.title}
                </span>
                <span className="text-sm font-medium text-right">
                  {column.render ? column.render(row[column.key]) : row[column.key]}
                </span>
              </div>
            ))}
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full">
        <thead>
          <tr>
            {columns.map(column => (
              <th
                key={column.key}
                className="sticky top-0 bg-white dark:bg-gray-800 px-4 py-2 text-left text-xs font-medium text-gray-600 dark:text-gray-400"
              >
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
              {columns.map(column => (
                <td key={column.key} className="px-4 py-2 text-sm">
                  {column.render ? column.render(row[column.key]) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

### PWA 配置
```typescript
// public/manifest.json
{
  "name": "CBSC Dashboard",
  "short_name": "CBSC",
  "description": "量化交易策略管理平台",
  "theme_color": "#3b82f6",
  "background_color": "#ffffff",
  "display": "standalone",
  "start_url": "/",
  "orientation": "portrait-primary",
  "scope": "/",
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}

// sw.ts - Service Worker
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { StaleWhileRevalidate } from 'workbox-strategies';

// 預緩存靜態資源
precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// API 緩存策略
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/strategies'),
  new StaleWhileRevalidate({
    cacheName: 'api-strategies',
    plugins: [{
      cacheKeyWillBeUsed: async ({ request }) => {
        return `${request.url}?cache=${Date.now()}`;
      }
    }]
  })
);

// 圖表數據緩存
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/charts'),
  new StaleWhileRevalidate({
    cacheName: 'api-charts',
    networkTimeoutSeconds: 3
  })
);

// 推送通知
self.addEventListener('push', (event) => {
  const options = {
    body: event.data?.text(),
    icon: '/icons/icon-192x192.png',
    badge: '/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: '查看詳情',
        icon: '/images/checkmark.png'
      },
      {
        action: 'close',
        title: '關閉',
        icon: '/images/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('CBSC Dashboard', options)
  );
});

// 異步導航支持
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// 網絡狀態處理
self.addEventListener('online', () => {
  console.log('App is now online');
});

self.addEventListener('offline', () => {
  console.log('App is now offline');
});
```

### 性能優化 Hook
```typescript
// hooks/useVirtualScroll.ts
export const useVirtualScroll = <T>(
  items: T[],
  itemHeight: number,
  containerHeight: number,
  overscan: number = 5
) => {
  const [scrollTop, setScrollTop] = useState(0);

  const visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const visibleEnd = Math.min(
    items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
  );

  const visibleItems = items.slice(visibleStart, visibleEnd);
  const offsetY = visibleStart * itemHeight;
  const totalHeight = items.length * itemHeight;

  const handleScroll = useCallback((e: React.UIEvent) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  return {
    visibleItems,
    offsetY,
    totalHeight,
    handleScroll
  };
};

// 圖片懶加載組件
export const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  placeholder,
  className
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px'
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const handleError = () => {
    setHasError(true);
  };

  const handleLoad = () => {
    setIsLoaded(true);
  };

  return (
    <div ref={imgRef} className={className}>
      {isInView && !hasError && (
        <img
          src={src}
          alt={alt}
          onLoad={handleLoad}
          onError={handleError}
          className={`
            transition-opacity duration-300
            ${isLoaded ? 'opacity-100' : 'opacity-0'}
          `}
        />
      )}
      {(!isLoaded || hasError) && (
        <div className="flex items-center justify-center h-full bg-gray-200 dark:bg-gray-700">
          {hasError ? (
            <PhotoIcon className="h-8 w-8 text-gray-400" />
          ) : (
            placeholder || <LoadingSpinner />
          )}
        </div>
      )}
    </div>
  );
};
```

### 響應式設計系統
```typescript
// hooks/useResponsive.ts
export const useResponsive = () => {
  const [windowSize, setWindowSize] = useState({
    width: 0,
    height: 0
  });

  const isMobile = useMemo(
    () => windowSize.width < 768,
    [windowSize.width]
  );

  const isTablet = useMemo(
    () => windowSize.width >= 768 && windowSize.width < 1024,
    [windowSize.width]
  );

  const isDesktop = useMemo(
    () => windowSize.width >= 1024,
    [windowSize.width]
  );

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    windowSize,
    isMobile,
    isTablet,
    isDesktop
  };
};

// utils/responsive.ts
export const responsive = {
  // 響應式間距
  spacing: {
    xs: (mobile: string, desktop?: string) => mobile,
    sm: (mobile: string, desktop?: string) => mobile,
    md: (mobile: string, desktop: string) => isMobile() ? mobile : desktop,
    lg: (mobile: string, desktop: string) => isMobile() ? mobile : desktop,
    xl: (mobile: string, desktop: string) => isMobile() ? mobile : desktop
  },

  // 響應式字體
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: isMobile() ? '1.25rem' : '1.5rem',
    '2xl': isMobile() ? '1.5rem' : '2rem',
    '3xl': isMobile() ? '1.875rem' : '3rem'
  },

  // 響應式布局
  layout: {
    container: isMobile() ? 'px-4' : 'px-6',
    section: isMobile() ? 'py-4' : 'py-8',
    card: isMobile() ? 'p-4' : 'p-6',
    button: 'min-h-[44px]' // 觸摸友好
  }
};

// CSS 工具類
export const mobileStyles = `
  @media (max-width: 768px) {
    .hide-mobile {
      display: none !important;
    }

    .mobile-full-width {
      width: 100% !important;
    }

    .mobile-stack {
      flex-direction: column !important;
    }

    .mobile-center {
      text-align: center !important;
    }

    /* 安全區域適配 */
    .safe-area-top {
      padding-top: env(safe-area-inset-top);
    }

    .safe-area-bottom {
      padding-bottom: env(safe-area-inset-bottom);
    }
  }
`;
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| 響應式設計優化 | 24小時 | 前端工程師 A |
| 觸摸手勢支持 | 16小時 | 前端工程師 B |
| 移動端性能優化 | 16小時 | 前端工程師 A |
| PWA 基礎功能 | 8小時 | 前端工程師 B |
| **總計** | **64小時** | |

## 🔗 依賴關係
- 前置任務：Task #4 (Dashboard主界面), Task #5 (實時數據可視化)
- 後續任務：Task #10 (性能優化)

## 📝 注意事項
1. 考慮不同設備的 DPI 差異
2. 處理橫豎屏切換的狀態保持
3. 實現適當的觸摸反饋
4. 考慮網絡條件下的加載策略
5. 測試真實設備上的表現

## 🧪 測試要求
```typescript
// components/__tests__/MobileLayout.test.tsx
describe('MobileLayout', () => {
  // 模擬移動端視口
  beforeAll(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 667
    });
  });

  test('renders mobile navigation correctly', () => {
    render(
      <MobileLayout>
        <div>Content</div>
      </MobileLayout>
    );

    expect(screen.getByRole('button', { name: /menu/i })).toBeInTheDocument();
    expect(screen.getByText('CBSC Dashboard')).toBeInTheDocument();
  });

  test('handles swipe gestures', () => {
    const onSwipeLeft = jest.fn();
    const { container } = render(
      <SwipeContainer onSwipeLeft={onSwipeLeft} />
    );

    // 模擬滑動
    fireEvent.touchStart(container, {
      touches: [{ clientX: 100 }]
    });
    fireEvent.touchMove(container, {
      touches: [{ clientX: 50 }]
    });
    fireEvent.touchEnd(container);

    expect(onSwipeLeft).toHaveBeenCalled();
  });

  test('lazy loads images when in view', async () => {
    render(<LazyImage src="test.jpg" alt="Test" />);

    expect(screen.queryByAltText('Test')).not.toBeInTheDocument();

    // 模擬進入視口
    const img = screen.getByTestId('lazy-image');
    fireEvent.intersection(img, { isIntersecting: true });

    await waitFor(() => {
      expect(screen.getByAltText('Test')).toBeInTheDocument();
    });
  });
});
```

## 📚 相關文檔
- [PWA Web.dev](https://web.dev/progressive-web-apps/)
- [Touch Events API](https://developer.mozilla.org/en-US/docs/Web/API/Touch_events)
- [CSS Media Queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries)
- [Workbox 文檔](https://developer.chrome.com/docs/workbox/)
- [React Virtualized](https://github.com/bvaughn/react-virtualized)