---
name: task-007-websocket-realtime-communication
status: open
created: 2025-12-13T09:33:34Z
updated: 2025-12-13T09:33:34Z
assignee: frontend-team
phase: 2
estimated_hours: 64
priority: high
---

# Task #7: WebSocket實時通信

## 📋 任務描述
實現 CBSC Dashboard 的 WebSocket 實時通信系統，包括 WebSocket 客戶端封裝、自動重連機制、數據緩存策略和連接狀態管理，確保實時數據的穩定傳輸和高效處理。

## 🎯 具體要求

### 7.1 WebSocket 客戶端封裝
- [ ] WebSocket 連接管理
- [ ] 消息發送和接收
- [ ] 事件訂閱/取消訂閱
- [ ] 消息隊列管理
- [ ] 心跳檢測機制
- [ ] 連接池管理

### 7.2 自動重連機制
- [ ] 指數退避重連策略
- [ ] 最大重連次數限制
- [ ] 重連狀態通知
- [ ] 網絡狀態檢測
- [ ] 手動重連觸發
- [ ] 重連成功恢復訂閱

### 7.3 數據緩存策略
- [ ] 內存緩存實現
- [ ] 數據過期管理
- [ ] 緩存大小限制
- [ ] 緩存持久化
- [ ] 緩存預熱機制
- [ ] 緩存同步策略

### 7.4 連接狀態管理
- [ ] 連接狀態枚舉
- [ ] 狀態變化通知
- [ ] 連接質量監控
- [ ] 延遲統計
- [ ] 錯誤處理和恢復
- [ ] 性能指標收集

## ✅ 驗收標準

1. **功能驗收**
   - [ ] WebSocket 連接穩定建立
   - [ ] 消息收發功能正常
   - [ ] 斷線自動重連成功
   - [ ] 緩存機制有效工作

2. **性能標準**
   - [ ] 連接建立時間 < 1 秒
   - [ ] 消息延遲 < 100ms
   - [ ] 重連時間 < 5 秒
   - [ ] 支持 1000+ 併發訂閱

3. **可靠性標準**
   - [ ] 重連成功率 > 99%
   - [ ] 消息丟失率 < 0.1%
   - [ ] 內存泄漏為 0
   - [ ] 錯誤恢復時間 < 1 秒

## 🔧 技術要求

### WebSocket 服務核心實現
```typescript
// services/websocket/WebSocketService.ts
export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error'
}

export interface WebSocketMessage {
  id: string;
  type: string;
  channel: string;
  data: any;
  timestamp: number;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
  enableCache?: boolean;
  cacheSize?: number;
  cacheTTL?: number;
}

export class WebSocketService extends EventEmitter {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private state: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private subscribers = new Map<string, Set<Function>>();
  private messageQueue: WebSocketMessage[] = [];
  private cache = new Map<string, { data: any; timestamp: number }>();
  private stats = {
    messagesReceived: 0,
    messagesSent: 0,
    reconnections: 0,
    lastPing: 0,
    averageLatency: 0
  };

  constructor(config: WebSocketConfig) {
    super();
    this.config = {
      protocols: [],
      reconnectAttempts: 5,
      reconnectDelay: 1000,
      heartbeatInterval: 30000,
      enableCache: true,
      cacheSize: 1000,
      cacheTTL: 60000,
      ...config
    };

    // 網絡狀態監聽
    this.setupNetworkListeners();
  }

  // 連接 WebSocket
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.state === ConnectionState.CONNECTED || this.state === ConnectionState.CONNECTING) {
        resolve();
        return;
      }

      this.setState(ConnectionState.CONNECTING);

      try {
        this.ws = new WebSocket(this.config.url, this.config.protocols);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.setState(ConnectionState.CONNECTED);
          this.startHeartbeat();
          this.flushMessageQueue();
          this.restoreSubscriptions();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket closed:', event.code, event.reason);
          this.stopHeartbeat();
          this.setState(ConnectionState.DISCONNECTED);
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.setState(ConnectionState.ERROR);
          reject(error);
        };

        // 設置連接超時
        setTimeout(() => {
          if (this.state === ConnectionState.CONNECTING) {
            this.ws?.close();
            reject(new Error('Connection timeout'));
          }
        }, 5000);

      } catch (error) {
        this.setState(ConnectionState.ERROR);
        reject(error);
      }
    });
  }

  // 斷開連接
  disconnect(): void {
    this.clearReconnectTimer();
    this.stopHeartbeat();
    this.setState(ConnectionState.DISCONNECTED);

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.subscribers.clear();
    this.messageQueue.length = 0;
    this.cache.clear();
  }

  // 發送消息
  send(message: Omit<WebSocketMessage, 'id' | 'timestamp'>): void {
    const fullMessage: WebSocketMessage = {
      ...message,
      id: generateId(),
      timestamp: Date.now()
    };

    if (this.state === ConnectionState.CONNECTED && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(fullMessage));
      this.stats.messagesSent++;
    } else {
      // 連接未就緒時加入隊列
      this.messageQueue.push(fullMessage);
      console.warn('WebSocket not connected, message queued');
    }
  }

  // 訂閱頻道
  subscribe(channel: string, callback: Function): () => void {
    if (!this.subscribers.has(channel)) {
      this.subscribers.set(channel, new Set());
    }

    this.subscribers.get(channel)!.add(callback);

    // 發送訂閱消息
    this.send({
      type: 'subscribe',
      channel,
      data: null
    });

    // 返回取消訂閱函數
    return () => this.unsubscribe(channel, callback);
  }

  // 取消訂閱
  unsubscribe(channel: string, callback?: Function): void {
    const subscribers = this.subscribers.get(channel);
    if (!subscribers) return;

    if (callback) {
      subscribers.delete(callback);
    } else {
      subscribers.clear();
    }

    // 如果沒有訂閱者了，發送取消訂閱消息
    if (subscribers.size === 0) {
      this.subscribers.delete(channel);
      this.send({
        type: 'unsubscribe',
        channel,
        data: null
      });
    }
  }

  // 獲取緩存數據
  getCachedData(channel: string): any | null {
    if (!this.config.enableCache) return null;

    const cached = this.cache.get(channel);
    if (!cached) return null;

    // 檢查是否過期
    if (Date.now() - cached.timestamp > this.config.cacheTTL) {
      this.cache.delete(channel);
      return null;
    }

    return cached.data;
  }

  // 設置緩存數據
  setCachedData(channel: string, data: any): void {
    if (!this.config.enableCache) return;

    // 檢查緩存大小限制
    if (this.cache.size >= this.config.cacheSize) {
      // 刪除最舊的條目
      const oldestKey = Array.from(this.cache.entries())
        .sort(([, a], [, b]) => a.timestamp - b.timestamp)[0][0];
      this.cache.delete(oldestKey);
    }

    this.cache.set(channel, {
      data,
      timestamp: Date.now()
    });
  }

  // 處理接收到的消息
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.stats.messagesReceived++;

      // 處理心跳響應
      if (message.type === 'pong') {
        this.stats.lastPing = Date.now();
        this.stats.averageLatency = (this.stats.averageLatency + (Date.now() - message.data.timestamp)) / 2;
        return;
      }

      // 更新緩存
      this.setCachedData(message.channel, message.data);

      // 通知訂閱者
      const subscribers = this.subscribers.get(message.channel);
      if (subscribers) {
        subscribers.forEach(callback => {
          try {
            callback(message.data);
          } catch (error) {
            console.error('Subscriber callback error:', error);
          }
        });
      }

      // 觸發消息事件
      this.emit('message', message);

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  // 自動重連
  private handleReconnect(): void {
    if (this.reconnectAttempts >= this.config.reconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.setState(ConnectionState.ERROR);
      this.emit('reconnectFailed');
      return;
    }

    this.reconnectAttempts++;
    this.stats.reconnections++;
    this.setState(ConnectionState.RECONNECTING);

    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000
    );

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(() => {
        this.handleReconnect();
      });
    }, delay);

    this.emit('reconnecting', { attempt: this.reconnectAttempts, delay });
  }

  // 清除重連定時器
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // 開始心跳
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({
          type: 'ping',
          channel: 'system',
          data: { timestamp: Date.now() }
        });
      }
    }, this.config.heartbeatInterval);
  }

  // 停止心跳
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // 設置連接狀態
  private setState(state: ConnectionState): void {
    if (this.state !== state) {
      const oldState = this.state;
      this.state = state;
      this.emit('stateChange', { from: oldState, to: state });
    }
  }

  // 刷新消息隊列
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0 && this.ws?.readyState === WebSocket.OPEN) {
      const message = this.messageQueue.shift()!;
      this.ws.send(JSON.stringify(message));
    }
  }

  // 恢復訂閱
  private restoreSubscriptions(): void {
    for (const channel of this.subscribers.keys()) {
      this.send({
        type: 'subscribe',
        channel,
        data: null
      });
    }
  }

  // 設置網絡監聽器
  private setupNetworkListeners(): void {
    window.addEventListener('online', () => {
      if (this.state === ConnectionState.DISCONNECTED) {
        console.log('Network restored, attempting to reconnect');
        this.reconnectAttempts = 0;
        this.connect().catch(console.error);
      }
    });

    window.addEventListener('offline', () => {
      console.log('Network lost');
      this.setState(ConnectionState.DISCONNECTED);
    });
  }

  // 獲取統計信息
  getStats() {
    return {
      ...this.stats,
      state: this.state,
      subscribersCount: Array.from(this.subscribers.values())
        .reduce((sum, set) => sum + set.size, 0),
      cacheSize: this.cache.size,
      queueSize: this.messageQueue.length
    };
  }
}
```

### React Hook 封裝
```typescript
// hooks/useWebSocket.ts
export interface UseWebSocketOptions {
  autoConnect?: boolean;
  reconnectOnMount?: boolean;
  includeConnectionState?: boolean;
}

export interface UseWebSocketReturn {
  sendMessage: (message: any) => void;
  lastMessage: WebSocketMessage | null;
  connectionState: ConnectionState;
  readyState: number;
  getWebSocket: () => WebSocketService | null;
  subscribe: (channel: string, callback: Function) => () => void;
  stats: any;
}

export const useWebSocket = (
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    autoConnect = true,
    reconnectOnMount = true,
    includeConnectionState = true
  } = options;

  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [stats, setStats] = useState<any>(null);

  const wsRef = useRef<WebSocketService | null>(null);

  // 初始化 WebSocket 服務
  useEffect(() => {
    if (!url) return;

    wsRef.current = new WebSocketService({
      url,
      reconnectAttempts: 5,
      heartbeatInterval: 30000
    });

    const ws = wsRef.current;

    // 事件監聽
    const handleMessage = (message: WebSocketMessage) => {
      setLastMessage(message);
    };

    const handleStateChange = ({ to }: { to: ConnectionState }) => {
      setConnectionState(to);
    };

    ws.on('message', handleMessage);
    ws.on('stateChange', handleStateChange);

    // 定期更新統計信息
    const statsInterval = setInterval(() => {
      if (ws) {
        setStats(ws.getStats());
      }
    }, 1000);

    // 自動連接
    if (autoConnect) {
      ws.connect().catch(console.error);
    }

    return () => {
      ws.off('message', handleMessage);
      ws.off('stateChange', handleStateChange);
      clearInterval(statsInterval);
      ws.disconnect();
    };
  }, [url, autoConnect]);

  // 重連邏輯
  useEffect(() => {
    if (reconnectOnMount && wsRef.current && connectionState === ConnectionState.DISCONNECTED) {
      wsRef.current.connect().catch(console.error);
    }
  }, [reconnectOnMount, connectionState]);

  const sendMessage = useCallback((message: any) => {
    wsRef.current?.send(message);
  }, []);

  const subscribe = useCallback((channel: string, callback: Function) => {
    return wsRef.current?.subscribe(channel, callback) || (() => {});
  }, []);

  const getWebSocket = useCallback(() => wsRef.current, []);

  return {
    sendMessage,
    lastMessage,
    connectionState: includeConnectionState ? connectionState : ConnectionState.DISCONNECTED,
    readyState: wsRef.current?.ws?.readyState ?? WebSocket.CLOSED,
    getWebSocket,
    subscribe,
    stats
  };
};

// 特定頻道 Hook
export const useWebSocketChannel = <T = any>(
  url: string,
  channel: string,
  callback: (data: T) => void,
  options: UseWebSocketOptions = {}
) => {
  const { subscribe, ...wsReturn } = useWebSocket(url, options);

  useEffect(() => {
    const unsubscribe = subscribe(channel, callback);
    return unsubscribe;
  }, [channel, callback, subscribe]);

  return wsReturn;
};
```

### Context Provider
```typescript
// contexts/WebSocketContext.tsx
interface WebSocketContextValue {
  wsService: WebSocketService | null;
  isConnected: boolean;
  subscribe: (channel: string, callback: Function) => () => void;
  send: (message: any) => void;
  stats: any;
}

export const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export const WebSocketProvider: React.FC<{
  url: string;
  children: React.ReactNode;
}> = ({ url, children }) => {
  const [wsService, setWsService] = useState<WebSocketService | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const service = new WebSocketService({
      url,
      reconnectAttempts: 5,
      enableCache: true
    });

    service.on('stateChange', ({ to }) => {
      setIsConnected(to === ConnectionState.CONNECTED);
    });

    // 定期更新統計
    const statsInterval = setInterval(() => {
      setStats(service.getStats());
    }, 1000);

    service.connect();

    setWsService(service);

    return () => {
      clearInterval(statsInterval);
      service.disconnect();
    };
  }, [url]);

  const subscribe = useCallback((channel: string, callback: Function) => {
    return wsService?.subscribe(channel, callback) || (() => {});
  }, [wsService]);

  const send = useCallback((message: any) => {
    wsService?.send(message);
  }, [wsService]);

  const value = {
    wsService,
    isConnected,
    subscribe,
    send,
    stats
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// 使用 Hook
export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
};
```

## 📊 預估工作量
| 子任務 | 預估時間 | 負責人 |
|--------|----------|--------|
| WebSocket 客戶端封裝 | 24小時 | 前端工程師 A |
| 自動重連機制 | 16小時 | 前端工程師 B |
| 數據緩存策略 | 12小時 | 前端工程師 A |
| 連接狀態管理 | 12小時 | 前端工程師 B |
| **總計** | **64小時** | |

## 🔗 依賴關係
- 前置任務：Task #3 (認證與授權系統)
- 後續任務：Task #5 (實時數據可視化), Task #6 (策略管理界面)

## 📝 注意事項
1. 實現消息壓縮以減少帶寬使用
2. 處理大量數據的流式傳輸
3. 實現消息優先級機制
4. 考慮使用 Service Worker 後台同步
5. 實現WebSocket安全認證

## 🧪 測試要求
```typescript
// services/websocket/__tests__/WebSocketService.test.ts
describe('WebSocketService', () => {
  let wsService: WebSocketService;
  let mockWebSocket: jest.Mocked<WebSocket>;

  beforeEach(() => {
    // Mock WebSocket
    global.WebSocket = jest.fn(() => ({
      readyState: WebSocket.OPEN,
      send: jest.fn(),
      close: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    })) as any;

    mockWebSocket = (global.WebSocket as any).mock.results[0].value;

    wsService = new WebSocketService({
      url: 'ws://localhost:8080'
    });
  });

  afterEach(() => {
    wsService.disconnect();
    jest.clearAllMocks();
  });

  test('connects successfully', async () => {
    const connectPromise = wsService.connect();

    // Simulate successful connection
    mockWebSocket.onopen?.(new Event('open'));

    await expect(connectPromise).resolves.toBeUndefined();
    expect(wsService.getStats().state).toBe('connected');
  });

  test('handles message correctly', () => {
    const callback = jest.fn();
    wsService.subscribe('test-channel', callback);

    // Simulate message
    mockWebSocket.onmessage?.({
      data: JSON.stringify({
        id: '1',
        type: 'data',
        channel: 'test-channel',
        data: { value: 42 },
        timestamp: Date.now()
      })
    });

    expect(callback).toHaveBeenCalledWith({ value: 42 });
  });

  test('queues messages when disconnected', () => {
    wsService.send({
      type: 'test',
      channel: 'test',
      data: null
    });

    expect(wsService.getStats().queueSize).toBe(1);
  });

  test('reconnects on connection loss', (done) => {
    wsService.connect().then(() => {
      // Simulate disconnection
      mockWebSocket.onclose?.(new CloseEvent('close'));

      // Check reconnection attempt
      setTimeout(() => {
        expect(wsService.getStats().reconnections).toBe(1);
        done();
      }, 1000);
    });
  });

  test('caches data correctly', () => {
    wsService.setCachedData('test', { value: 42 });
    const cached = wsService.getCachedData('test');

    expect(cached).toEqual({ value: 42 });
  });
});
```

## 📚 相關文檔
- [WebSocket MDN 文檔](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Socket.io 文檔](https://socket.io/docs/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [Real-time Web Technologies](https://www.html5rocks.com/en/tutorials/websockets/basics/)