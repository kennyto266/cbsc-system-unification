---
name: task-004-dashboard-main-interface
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-team
phase: 2
estimated_hours: 80
priority: high
---

# Task #4: Dashboard主界面

## 📋 任務描述
設計和實現 CBSC Dashboard 的主界面，包括響應式 Dashboard 佈局、實時數據卡片組件、快速操作面板和個人化小部件系統，為用戶提供直觀高效的數據監控和管理界面。

## 🎯 具體要求

### 4.1 響應式 Dashboard 佈局
- [ ] 實現 Header 導航欄（包含用戶信息、通知、設置）
- [ ] 設計 Sidebar 側邊欄（導航菜單、快速統計）
- [ ] 創建響應式主內容區域
- [ ] 實現摺疊/展開側邊欄功能
- [ ] 移動端適配（漢堡菜單、底部導航）

### 4.2 實時數據卡片組件
- [ ] 策略總覽卡片（運行中/已停止/總數）
- [ ] 績效指標卡片（今日盈虧、收益率）
- [ ] 風險監控卡片（風險等級、警報數）
- [ ] 市場概覽卡片（主要指數、行情）
- [ ] 實時數據更新動畫

### 4.3 快速操作面板
- [ ] 策略快速啟動/停止按鈕
- [ ] 緊急停止全部策略功能
- [ ] 快速參數調整入口
- [ ] 一鍵生成報告按鈕
- [ ] 常用功能快捷方式

### 4.4 個人化小部件系統
- [ ] 可拖拽的小部件佈局
- [ ] 小部件大小調整功能
- [ ] 小部件顯示/隱藏控制
- [ ] 個人化佈局保存
- [ ] 預設佈局模板

## ✅ 驗收標準

1. **功能驗收**
   - [ ] 所有佈局在不同屏幕尺寸下正確顯示
   - [ ] 實時數據更新頻率達到秒級
   - [ ] 小部件可以自由拖拽和調整
   - [ ] 個人化設置可以持久保存

2. **性能標準**
   - [ ] 初始加載時間 < 2 秒
   - [ ] 數據更新延遲 < 100ms
   - [ ] 拖拽操作流暢度 > 60fps
   - [ ] 內存佔用 < 50MB

3. **用戶體驗**
   - [ ] 界面響應時間 < 200ms
   - [ ] 動畫過渡流暢自然
   - [ ] 操作邏輯直觀易懂
   - [ ] WCAG 2.1 AA 級無障礙

## 🔧 技術要求

### Dashboard 佈局組件
```typescript
// components/layout/DashboardLayout.tsx
interface DashboardLayoutProps {
  children: React.ReactNode;
  sidebarCollapsed?: boolean;
  onSidebarToggle?: () => void;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  sidebarCollapsed = false,
  onSidebarToggle
}) => {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className={`
        ${sidebarCollapsed ? 'w-16' : 'w-64'}
        transition-all duration-300 ease-in-out
        bg-white dark:bg-gray-800
        border-r border-gray-200 dark:border-gray-700
        fixed lg:relative h-full z-40
      `}>
        <Sidebar collapsed={sidebarCollapsed} />
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <Header onMenuClick={onSidebarToggle} />
        </header>

        {/* Main Area */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};
```

### 實時數據卡片組件
```typescript
// components/dashboard/DataCard.tsx
interface DataCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease' | 'neutral';
  };
  icon?: React.ReactNode;
  loading?: boolean;
  realtime?: boolean;
  className?: string;
}

export const DataCard: React.FC<DataCardProps> = ({
  title,
  value,
  change,
  icon,
  loading = false,
  realtime = false,
  className = ''
}) => {
  const [currentValue, setCurrentValue] = useState(value);
  const [isAnimating, setIsAnimating] = useState(false);

  // 實時數據更新動畫
  useEffect(() => {
    if (realtime && currentValue !== value) {
      setIsAnimating(true);
      const timer = setTimeout(() => {
        setCurrentValue(value);
        setIsAnimating(false);
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [value, currentValue, realtime]);

  return (
    <div className={`
      bg-white dark:bg-gray-800
      rounded-lg shadow-sm p-6
      border border-gray-200 dark:border-gray-700
      ${className}
    `}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </p>
          <div className={`
            mt-2 text-3xl font-bold text-gray-900 dark:text-white
            transition-all duration-150
            ${isAnimating ? 'scale-110 text-primary-500' : ''}
          `}>
            {loading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              currentValue
            )}
          </div>
          {change && (
            <div className={`
              mt-2 flex items-center text-sm
              ${change.type === 'increase' ? 'text-green-600' : ''}
              ${change.type === 'decrease' ? 'text-red-600' : ''}
              ${change.type === 'neutral' ? 'text-gray-600' : ''}
            `}>
              {change.type === 'increase' && <ArrowTrendingUpIcon className="h-4 w-4 mr-1" />}
              {change.type === 'decrease' && <ArrowTrendingDownIcon className="h-4 w-4 mr-1" />}
              {change.value}%
            </div>
          )}
        </div>
        {icon && (
          <div className="p-3 bg-primary-50 dark:bg-primary-900/20 rounded-lg">
            {icon}
          </div>
        )}
      </div>
      {realtime && (
        <div className="mt-3 flex items-center text-xs text-gray-500">
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse mr-2" />
          Real-time
        </div>
      )}
    </div>
  );
};
```

### 可拖拽小部件系統
```typescript
// components/dashboard/WidgetGrid.tsx
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface DraggableWidgetProps {
  id: string;
  children: React.ReactNode;
}

const DraggableWidget: React.FC<DraggableWidgetProps> = ({ id, children }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="relative group"
      {...attributes}
    >
      <div className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <button
          {...listeners}
          className="p-1 bg-gray-600 text-white rounded cursor-move hover:bg-gray-700"
        >
          <ArrowsUpDownIcon className="h-4 w-4" />
        </button>
      </div>
      {children}
    </div>
  );
};

export const WidgetGrid: React.FC = () => {
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (active.id !== over?.id) {
      setWidgets((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over?.id);

        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragEnd={handleDragEnd}
    >
      <SortableContext items={widgets.map(w => w.id)}>
        <ResponsiveGridLayout
          className="layout"
          layouts={{ lg: widgets }}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={30}
          onLayoutChange={handleLayoutChange}
        >
          {widgets.map((widget) => (
            <div key={widget.id} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4">
              <DraggableWidget id={widget.id}>
                <WidgetComponent type={widget.type} data={widget.data} />
              </DraggableWidget>
            </div>
          ))}
        </ResponsiveGridLayout>
      </SortableContext>
    </DndContext>
  );
};
```

### 實時數據 Hook
```typescript
// hooks/useRealTimeData.ts
export const useRealTimeData = <T>(endpoint: string, interval: number = 1000) => {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    let intervalId: NodeJS.Timeout;

    const fetchData = async () => {
      try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('Failed to fetch data');
        const result = await response.json();

        if (isMounted) {
          setData(result);
          setError(null);
          setIsLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Unknown error');
          setIsLoading(false);
        }
      }
    };

    // 立即獲取數據
    fetchData();

    // 設置定時更新
    if (interval > 0) {
      intervalId = setInterval(fetchData, interval);
    }

    return () => {
      isMounted = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [endpoint, interval]);

  return { data, error, isLoading, refetch: fetchData };
};
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| 響應式佈局系統 | 24小時 | 前端工程師 A |
| Header/Sidebar 組件 | 16小時 | 前端工程師 B |
| 實時數據卡片 | 16小時 | 前端工程師 A |
| 快速操作面板 | 12小時 | 前端工程師 B |
| 個人化小部件系統 | 12小時 | 前端工程師 A |
| **總計** | **80小時** | |

## 🔗 依賴關係
- 前置任務：Task #1 (項目初始化), Task #2 (設計系統), Task #3 (認證系統)
- 後續任務：Task #5 (實時數據可視化)

## 📝 注意事項
1. 確保所有組件支持主題切換
2. 實現優雅的加載和錯誤狀態
3. 考慮網絡中斷時的離線體驗
4. 實現鍵盤導航支持
5. 確保高對比度模式下的可訪問性

## 🧪 測試要求
```typescript
// components/dashboard/__tests__/DataCard.test.tsx
describe('DataCard', () => {
  test('renders card with correct data', () => {
    render(
      <DataCard
        title="Total Strategies"
        value={42}
        change={{ value: 12.5, type: 'increase' }}
        icon={<ChartBarIcon />}
      />
    );

    expect(screen.getByText('Total Strategies')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('12.5%')).toBeInTheDocument();
  });

  test('shows loading state', () => {
    render(
      <DataCard
        title="Loading"
        value={0}
        loading={true}
      />
    );

    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  test('displays real-time indicator', () => {
    render(
      <DataCard
        title="Real-time Data"
        value={100}
        realtime={true}
      />
    );

    expect(screen.getByText('Real-time')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveClass('bg-green-500');
  });
});
```

## 📚 相關文檔
- [React DnD 文檔](https://react-dnd.github.io/react-dnd/)
- [React Grid Layout 文檔](https://github.com/react-grid-layout/react-grid-layout)
- [React Window 文檔](https://react-window.vercel.app/)
- [CSS Grid 布局指南](https://css-tricks.com/snippets/css/complete-guide-grid/)