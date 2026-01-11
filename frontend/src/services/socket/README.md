# WebSocket Service Implementation

本 WebSocket 服務提供了完整的實時通信解決方案，包括自動重連、錯誤處理、性能優化和數據緩存等功能。

## 功能特性

### 連接管理
- ✅ 自動建立連接
- ✅ 斷線自動重連（指數退避策略）
- ✅ 連接狀態實時監控
- ✅ 多 URL 支持和故障轉移
- ✅ 心跳檢測機制

### 數據處理
- ✅ 實時價格數據推送
- ✅ 策略執行通知
- ✅ 系統警報消息
- ✅ 用戶活動更新
- ✅ 消息過濾和轉換
- ✅ 批量數據處理

### 性能優化
- ✅ 數據緩存機制
- ✅ 節流和防抖支持
- ✅ 內存管理優化
- ✅ 消息隊列管理
- ✅ 連接池管理（高級版）

### 開發體驗
- ✅ 完整的 TypeScript 類型定義
- ✅ React Hook 集成
- ✅ Redux 狀態管理
- ✅ 調試和監控工具
- ✅ 單元測試覆蓋

## 安裝和配置

### 依賴要求

```json
{
  "socket.io-client": "^4.7.4",
  "uuid": "^9.0.1",
  "lodash": "^4.17.21"
}
```

### 環境變量

```env
REACT_APP_WEBSOCKET_URL=ws://localhost:3004
REACT_APP_WEBSOCKET_DEBUG=true
```

## 基本使用

### 1. 使用 React Hook（推薦）

```tsx
import { useWebSocket } from '@/hooks/useWebSocket';
import { MessageType } from '@/types/socket';

function MyComponent() {
  const {
    isConnected,
    connectionState,
    subscribe,
    send,
    metrics
  } = useWebSocket({
    url: 'ws://localhost:3004',
    autoConnect: true,
    reconnectAttempts: 5,
  });

  // 訂閱價格更新
  useEffect(() => {
    if (isConnected) {
      const subscriptionId = subscribe(
        MessageType.PRICE_UPDATE,
        (message) => {
          console.log('收到價格更新:', message.data);
        },
        {
          throttle: 100, // 節流 100ms
          filter: (msg) => msg.data.symbol === 'BTC', // 只看 BTC
        }
      );

      return () => {
        // 取消訂閱
        unsubscribe(subscriptionId);
      };
    }
  }, [isConnected, subscribe]);

  return (
    <div>
      <p>連接狀態: {connectionState}</p>
      <p>延遲: {metrics.latency}ms</p>
    </div>
  );
}
```

### 2. 直接使用 WebSocket 服務

```typescript
import { createWebSocketService, MessageType } from '@/services/socket';
import { ConnectionState } from '@/types/socket';

// 創建服務實例
const wsService = createWebSocketService({
  url: 'ws://localhost:3004',
  token: 'your-auth-token',
  reconnectAttempts: 5,
  reconnectDelay: 1000,
  heartbeatInterval: 30000,
  debug: true,
});

// 監聽連接事件
wsService.on('connect', () => {
  console.log('WebSocket 已連接');
});

wsService.on('disconnect', () => {
  console.log('WebSocket 已斷開');
});

wsService.on('error', (error) => {
  console.error('WebSocket 錯誤:', error);
});

// 連接
await wsService.connect();

// 訂閱消息
const subscriptionId = wsService.subscribe(
  MessageType.PRICE_UPDATE,
  (message) => {
    console.log('價格更新:', message);
  },
  {
    filter: (msg) => msg.data.symbol === 'ETH',
    throttle: 500,
  }
);

// 發送消息
wsService.send(MessageType.HEARTBEAT, {
  timestamp: Date.now(),
  clientId: 'my-client',
});
```

### 3. 使用高級 Hook

```tsx
import { useWebSocketAdvanced } from '@/hooks/useWebSocketAdvanced';

function AdvancedComponent() {
  const {
    isConnected,
    subscribe,
    send,
    broadcast,
    getMessageHistory,
    getCachedData,
    setCachedData,
  } = useWebSocketAdvanced({
    autoConnect: true,
    enableCaching: true,
    enableThrottling: true,
    throttleDelay: 100,
    cacheSize: 100,
  });

  // 訂閱並緩存數據
  useEffect(() => {
    if (isConnected) {
      subscribe(
        MessageType.STRATEGY_SIGNAL,
        (message) => {
          // 處理策略信號
        },
        {
          cache: true,
          cacheKey: 'strategy_signals',
          debounce: 300,
        }
      );
    }
  }, [isConnected, subscribe]);

  // 獲取緩存的數據
  const cachedSignals = getCachedData('strategy_signals');

  return <div>{/* UI 內容 */}</div>;
}
```

## 高級功能

### 1. 多連接管理

```typescript
import { createWebSocketManager } from '@/services/websocket-manager';

const manager = createWebSocketManager({
  defaultConnection: {
    url: 'ws://primary-server:3004',
  },
  connections: {
    backup: {
      url: 'ws://backup-server:3004',
    },
    marketData: {
      url: 'ws://market-data-server:3004',
    },
  },
  enableLoadBalancing: true,
  enableConnectionPooling: true,
});

// 使用特定連接
const primaryService = manager.getConnection();
const backupService = manager.getConnection('backup');

// 負載均衡發送
manager.send(MessageType.PRICE_REQUEST, { symbols: ['BTC', 'ETH'] });

// 廣播到所有連接
manager.broadcast(MessageType.SYSTEM_ALERT, {
  level: 'warning',
  message: '系統維護通知',
});
```

### 2. 自定義消息處理

```typescript
// 創建自定義消息類型
enum CustomMessageType {
  CHART_UPDATE = 'chart_update',
  TRADE_EXECUTION = 'trade_execution',
}

// 定義消息接口
interface ChartUpdateMessage {
  symbol: string;
  timeframe: string;
  candles: Array<{
    timestamp: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

// 訂閱並處理自定義消息
wsService.subscribe<ChartUpdateMessage>(
  CustomMessageType.CHART_UPDATE,
  (message) => {
    // 處理圖表更新
    updateChart(message.data);
  },
  {
    transform: (message) => {
      // 轉換數據格式
      return {
        ...message,
        data: {
          ...message.data,
          candles: message.data.candles.map(candle => ({
            ...candle,
            date: new Date(candle.timestamp),
          })),
        },
      };
    },
  }
);
```

### 3. 性能監控

```typescript
// 獲取連接指標
const metrics = wsService.getConnectionMetrics();
console.log('連接統計:', {
  uptime: metrics.connectedAt ? Date.now() - metrics.connectedAt : 0,
  messagesReceived: metrics.messagesReceived,
  messagesSent: metrics.messagesSent,
  averageLatency: metrics.averageLatency,
  reconnectCount: metrics.reconnectCount,
  errorCount: metrics.errors.length,
});

// 監控健康狀態
const health = manager.getHealthStatus();
if (health.status === 'unhealthy') {
  console.error('連接不健康:', health.issues);
  // 實施故障恢復策略
}
```

## 錯誤處理

### 連接錯誤

```typescript
import { WebSocketServiceError, WebSocketError } from '@/types/socket';

try {
  await wsService.connect();
} catch (error) {
  if (error instanceof WebSocketServiceError) {
    switch (error.code) {
      case WebSocketError.CONNECTION_FAILED:
        console.error('連接失敗:', error.message);
        break;
      case WebSocketError.AUTHENTICATION_FAILED:
        console.error('認證失敗:', error.message);
        break;
      case WebSocketError.MAX_RECONNECT_ATTEMPTS:
        console.error('達到最大重連次數');
        break;
    }
  }
}
```

### 處理網絡中斷

```typescript
wsService.on('disconnect', (reason) => {
  if (reason === 'io server disconnect') {
    // 服務器主動斷開，需要手動重連
    wsService.connect();
  } else {
    // 網絡中斷，自動重連會處理
    console.log('網絡中斷，正在重連...');
  }
});
```

## 測試

### 單元測試示例

```typescript
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

// Mock WebSocket
jest.mock('socket.io-client');

describe('useWebSocket', () => {
  it('should connect on mount when autoConnect is true', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ autoConnect: true })
    );

    expect(result.current.connectionState).toBe('connecting');

    await act(async () => {
      // 等待連接完成
    });

    expect(result.current.isConnected).toBe(true);
  });
});
```

## 最佳實踐

### 1. 連接管理

```typescript
// 在應用級別初始化 WebSocket
// App.tsx
function App() {
  // 創建全局 WebSocket 服務
  const wsService = useMemo(() => {
    return createWebSocketService({
      url: process.env.REACT_APP_WEBSOCKET_URL!,
      token: getAuthToken(),
      reconnectAttempts: 5,
    });
  }, []);

  return (
    <WebSocketProvider service={wsService}>
      <Router>
        <Routes>
          {/* 路由配置 */}
        </Routes>
      </Router>
    </WebSocketProvider>
  );
}
```

### 2. 組件級訂閱

```typescript
// 使用自定義 Hook 封裝訂閱邏輯
function usePriceUpdates(symbols: string[]) {
  const { subscribe } = useWebSocket();
  const [prices, setPrices] = useState({});

  useEffect(() => {
    const subscriptions = symbols.map(symbol =>
      subscribe(
        MessageType.PRICE_UPDATE,
        (message) => {
          if (message.data.symbol === symbol) {
            setPrices(prev => ({
              ...prev,
              [symbol]: message.data,
            }));
          }
        }
      )
    );

    return () => {
      subscriptions.forEach(unsubscribe);
    };
  }, [symbols, subscribe]);

  return prices;
}
```

### 3. 內存優化

```typescript
// 清理舊數據
useEffect(() => {
  const interval = setInterval(() => {
    // 清理超過 1 小時的緩存數據
    clearOldCache();
    // 清理超過 1000 條的歷史消息
    trimMessageHistory();
  }, 60000); // 每分鐘執行一次

  return () => clearInterval(interval);
}, []);
```

## 故障排除

### 常見問題

1. **連接失敗**
   - 檢查 URL 是否正確
   - 確認服務器是否運行
   - 檢查防火牆設置

2. **認證失敗**
   - 驗證 token 是否有效
   - 檢查 token 過期時間
   - 確認 token 格式

3. **消息丟失**
   - 檢查網絡連接
   - 驗證消息格式
   - 查看服務器日誌

4. **性能問題**
   - 啟用消息節流
   - 使用緩存機制
   - 監控內存使用

### 調試技巧

```typescript
// 啟用詳細日誌
const wsService = createWebSocketService({
  url: 'ws://localhost:3004',
  debug: true,
  logLevel: 'debug',
});

// 監控所有消息
wsService.on('message', (message) => {
  console.debug('WebSocket Message:', message);
});
```

## 版本歷史

- **v1.0.0** (2024-01-15)
  - 初始版本發布
  - 基本連接和消息功能
  - 自動重連機制

- **v1.1.0** (2024-01-20)
  - 添加性能優化
  - 實現緩存機制
  - 支持消息過濾

- **v1.2.0** (2024-01-25)
  - 多連接管理
  - 負載均衡支持
  - 增強錯誤處理

## 貢獻指南

歡迎提交 Issue 和 Pull Request。請確保：

1. 所有新功能都有相應的測試
2. 遵循現有的代碼風格
3. 更新相關文檔
4. 通過所有 CI 檢查

## 許可證

MIT License