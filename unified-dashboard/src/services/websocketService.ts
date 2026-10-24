/**
 * WebSocket Service for Real-time Data Updates
 * 為個人策略管理Dashboard提供實時數據更新服務
 */

import { store } from '../store';
import {
  setWebSocketStatus,
  updateStrategyData,
  updatePerformanceMetrics,
  addNewSignal,
  updateSystemHealth
} from '../store/slices/uiSlice';

export interface WebSocketMessage {
  type: 'strategy_update' | 'performance_update' | 'signals_update' | 'system_health' | 'initial_state' | 'heartbeat_response';
  data: any;
  timestamp: string;
}

export interface ConnectionStatus {
  connected: boolean;
  reconnecting: boolean;
  lastError?: string;
  reconnectAttempts: number;
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 2000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private messageQueue: any[] = [];
  private subscriptions: Set<string> = new Set();

  public connectionStatus: ConnectionStatus = {
    connected: false,
    reconnecting: false,
    reconnectAttempts: 0
  };

  constructor(url: string = 'ws://localhost:3004/ws') {
    this.url = url;
  }

  /**
   * 建立WebSocket連接
   */
  async connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 構建WebSocket URL，支持token認證
        const wsUrl = token ? `${this.url}?token=${token}` : this.url;
        this.ws = new WebSocket(wsUrl);

        // 連接成功
        this.ws.onopen = () => {
          console.log('🔗 WebSocket connected');
          this.connectionStatus.connected = true;
          this.connectionStatus.reconnecting = false;
          this.connectionStatus.reconnectAttempts = 0;

          // 更新Redux狀態
          store.dispatch(setWebSocketStatus({
            connected: true,
            reconnecting: false
          }));

          // 開始心跳機制
          this.startHeartbeat();

          // 發送積壓的消息
          this.flushMessageQueue();

          // 訂閱頻道
          this.subscribeToChannels();

          resolve();
        };

        // 接收消息
        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        // 連接關閉
        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket disconnected:', event.code, event.reason);
          this.connectionStatus.connected = false;

          // 更新Redux狀態
          store.dispatch(setWebSocketStatus({
            connected: false,
            reconnecting: true
          }));

          // 停止心跳
          this.stopHeartbeat();

          // 嘗試重連
          if (!event.wasClean) {
            this.attemptReconnect();
          }
        };

        // 連接錯誤
        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.connectionStatus.lastError = 'WebSocket connection error';

          store.dispatch(setWebSocketStatus({
            connected: false,
            reconnecting: false,
            lastError: 'Connection error'
          }));

          reject(error);
        };

      } catch (error) {
        console.error('❌ Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  /**
   * 處理接收到的消息
   */
  private handleMessage(data: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(data);
      console.log('📨 WebSocket message received:', message.type);

      switch (message.type) {
        case 'initial_state':
          this.handleInitialState(message.data);
          break;

        case 'strategy_update':
          this.handleStrategyUpdate(message.data);
          break;

        case 'performance_update':
          this.handlePerformanceUpdate(message.data);
          break;

        case 'signals_update':
          this.handleSignalsUpdate(message.data);
          break;

        case 'system_health':
          this.handleSystemHealth(message.data);
          break;

        case 'heartbeat_response':
          // 心跳響應，更新連接狀態
          break;

        default:
          console.warn('⚠️ Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('❌ Failed to parse WebSocket message:', error);
    }
  }

  /**
   * 處理初始狀態
   */
  private handleInitialState(data: any): void {
    console.log('📊 Received initial state:', data);

    if (data.strategies) {
      store.dispatch(updateStrategyData(data.strategies));
    }

    if (data.system_info) {
      store.dispatch(updateSystemHealth(data.system_info));
    }
  }

  /**
   * 處理策略更新
   */
  private handleStrategyUpdate(data: any): void {
    console.log('🔄 Strategy update received:', data);
    store.dispatch(updateStrategyData(data.updated_strategies || data));
  }

  /**
   * 處理性能更新
   */
  private handlePerformanceUpdate(data: any): void {
    console.log('📈 Performance update received:', data);
    store.dispatch(updatePerformanceMetrics(data));
  }

  /**
   * 處理信號更新
   */
  private handleSignalsUpdate(data: any): void {
    console.log('📡 Signals update received:', data);

    // 將信號轉換為標準格式並添加到store
    const signals = Object.entries(data).map(([category, signalData]: [string, any]) => ({
      id: `${category}_${Date.now()}`,
      category,
      ...signalData,
      timestamp: new Date(signalData.timestamp)
    }));

    signals.forEach(signal => {
      store.dispatch(addNewSignal(signal));
    });
  }

  /**
   * 處理系統健康狀態
   */
  private handleSystemHealth(data: any): void {
    console.log('🏥 System health update received:', data);
    store.dispatch(updateSystemHealth(data));
  }

  /**
   * 發送消息
   */
  send(message: any): void {
    if (this.isConnected()) {
      this.ws!.send(JSON.stringify(message));
    } else {
      // 連接未就緒時，將消息加入隊列
      this.messageQueue.push(message);
      console.warn('⚠️ WebSocket not connected, message queued');
    }
  }

  /**
   * 清空消息隊列
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * 訂閱頻道
   */
  private subscribeToChannels(): void {
    const channels = ['strategy_updates', 'performance_updates', 'signals_updates', 'system_health'];

    channels.forEach(channel => {
      this.subscribe(channel);
    });
  }

  /**
   * 訂閱特定頻道
   */
  subscribe(channel: string): void {
    this.subscriptions.add(channel);
    this.send({
      type: 'subscribe',
      data: { channel }
    });
  }

  /**
   * 取消訂閱頻道
   */
  unsubscribe(channel: string): void {
    this.subscriptions.delete(channel);
    this.send({
      type: 'unsubscribe',
      data: { channel }
    });
  }

  /**
   * 心跳機制
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({
          type: 'heartbeat',
          timestamp: Date.now()
        });
      }
    }, 30000); // 每30秒發送一次心跳
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 自動重連機制
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      store.dispatch(setWebSocketStatus({
        connected: false,
        reconnecting: false,
        lastError: 'Failed to reconnect after maximum attempts'
      }));
      return;
    }

    this.reconnectAttempts++;
    this.connectionStatus.reconnecting = true;
    this.connectionStatus.reconnectAttempts = this.reconnectAttempts;

    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);

    console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);

    this.reconnectTimeout = setTimeout(() => {
      this.connect().catch(error => {
        console.error('❌ Reconnection failed:', error);
        this.connectionStatus.lastError = 'Reconnection failed';
        this.attemptReconnect(); // 繼續嘗試重連
      });
    }, delay);
  }

  /**
   * 檢查連接狀態
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * 獲取連接狀態
   */
  getConnectionStatus(): ConnectionStatus {
    return { ...this.connectionStatus };
  }

  /**
   * 請求當前狀態
   */
  requestCurrentState(): void {
    this.send({
      type: 'request_state',
      timestamp: Date.now()
    });
  }

  /**
   * 手動斷開連接
   */
  disconnect(): void {
    console.log('🔌 Manually disconnecting WebSocket');

    // 停止重連機制
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // 停止心跳
    this.stopHeartbeat();

    // 關閉連接
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }

    // 更新狀態
    this.connectionStatus.connected = false;
    this.connectionStatus.reconnecting = false;
    this.connectionStatus.reconnectAttempts = 0;

    store.dispatch(setWebSocketStatus({
      connected: false,
      reconnecting: false
    }));
  }

  /**
   * 清理資源
   */
  cleanup(): void {
    this.disconnect();
    this.messageQueue = [];
    this.subscriptions.clear();
  }
}

// 創建單例實例
let webSocketService: WebSocketService | null = null;

export const getWebSocketService = (): WebSocketService => {
  if (!webSocketService) {
    webSocketService = new WebSocketService();
  }
  return webSocketService;
};

export default WebSocketService;