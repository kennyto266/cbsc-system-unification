import { WebSocketMessage, Strategy, PerformanceMetrics } from '../types/index';

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private messageQueue: any[] = [];
  private isConnected = false;

  // 事件監聽器
  private listeners: { [key: string]: ((data: any) => void)[] } = {
    message: [],
    connect: [],
    disconnect: [],
    error: []
  };

  constructor(private url: string = 'ws://localhost:3004/ws') {
    this.connect();
  }

  // 連接WebSocket
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startHeartbeat();

          // 發送積壓的消息
          this.flushMessageQueue();

          this.emit('connect', { status: 'connected' });
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.stopHeartbeat();
          this.emit('disconnect', { status: 'disconnected' });
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.emit('error', { error });
          reject(error);
        };
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        reject(error);
      }
    });
  }

  // 處理接收到的消息
  private handleMessage(message: WebSocketMessage) {
    console.log('Received WebSocket message:', message.type);

    switch (message.type) {
      case 'strategy_update':
        this.emit('message', { type: 'strategy_update', data: message.strategy });
        break;
      case 'performance_update':
        this.emit('message', { type: 'performance_update', data: message.performance });
        break;
      case 'signals_update':
        this.emit('message', { type: 'signals_update', data: message.signals });
        break;
      case 'heartbeat':
        this.handleHeartbeat();
        break;
      case 'error':
        this.emit('message', { type: 'error', data: message.data });
        break;
      default:
        this.emit('message', message);
    }
  }

  // 發送消息
  send(message: any) {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      // 連接未就緒時，將消息加入隊列
      this.messageQueue.push(message);
      console.warn('WebSocket not connected, message queued');
    }
  }

  // 清空消息隊列
  private flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  // 心跳機制
  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'heartbeat', timestamp: Date.now() });
    }, 30000); // 每30秒發送一次心跳
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private handleHeartbeat() {
    // 收到服務器心跳響應
    console.log('Heartbeat received from server');
  }

  // 自動重連機制
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.emit('error', { message: 'Failed to reconnect after maximum attempts' });
    }
  }

  // 事件監聽器管理
  on(event: string, callback: (data: any) => void) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event: string, callback: (data: any) => void) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  private emit(event: string, data: any) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  // 獲取連接狀態
  getConnectionStatus(): 'connecting' | 'connected' | 'disconnected' {
    if (!this.ws) return 'disconnected';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      default:
        return 'disconnected';
    }
  }

  // 手動斷開連接
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  // 訂閱特定策略更新
  subscribeToStrategy(strategyId: string) {
    this.send({
      type: 'subscribe',
      data: {
        channel: 'strategy_updates',
        strategy_id: strategyId
      }
    });
  }

  // 訂閱性能指標更新
  subscribeToPerformance() {
    this.send({
      type: 'subscribe',
      data: {
        channel: 'performance_updates'
      }
    });
  }

  // 訂閱交易信號
  subscribeToSignals() {
    this.send({
      type: 'subscribe',
      data: {
        channel: 'signals_updates'
      }
    });
  }

  // 取消訂閱
  unsubscribe(channel: string) {
    this.send({
      type: 'unsubscribe',
      data: {
        channel
      }
    });
  }

  // 請求當前狀態
  requestCurrentState() {
    this.send({
      type: 'request_state',
      timestamp: Date.now()
    });
  }
}

// 創建單例實例
let websocketService: WebSocketService | null = null;

export const getWebSocketService = (): WebSocketService => {
  if (!websocketService) {
    websocketService = new WebSocketService();
  }
  return websocketService;
};

export default WebSocketService;