/**
 * Dashboard WebSocket客戶端 - 實時數據更新機制
 * 提供專業級實時策略數據同步
 */

// ========== WebSocket配置常量 ==========
const WEBSOCKET_CONFIG = {
    // WebSocket服務器地址
    serverUrl: 'ws://localhost:3005',

    // 連接配置
    connectionTimeout: 5000,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,

    // 心跳配置
    heartbeatInterval: 30000,
    heartbeatTimeout: 5000,

    // 數據更新配置
    dataUpdateThrottle: 1000,
    maxDataRetries: 3,

    // 訂閱頻道
    channels: [
        'strategy_updates',
        'performance_updates',
        'signals_updates',
        'system_health'
    ]
};

// ========== WebSocket客戶端管理器 ==========
class DashboardWebSocketClient {
    constructor(options = {}) {
        this.config = { ...WEBSOCKET_CONFIG, ...options };
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.heartbeatTimer = null;
        this.heartbeatTimeoutTimer = null;
        this.dataUpdateBuffer = new Map();
        this.lastDataUpdate = {};

        // 事件回調
        this.callbacks = {
            onConnect: [],
            onDisconnect: [],
            onMessage: [],
            onError: [],
            onDataUpdate: []
        };

        // 連接狀態
        this.connectionState = 'disconnected'; // disconnected, connecting, connected, error

        // 數據緩存
        this.dataCache = {
            strategies: null,
            lastUpdate: null,
            systemHealth: null
        };

        // 性能監控
        this.performance = {
            connectionCount: 0,
            messagesReceived: 0,
            lastPingTime: null,
            averageLatency: 0
        };

        console.log('🔌 WebSocket客戶端已初始化');
    }

    /**
     * 連接到WebSocket服務器
     */
    async connect() {
        if (this.isConnected || this.connectionState === 'connecting') {
            console.warn('WebSocket已連接或正在連接中');
            return;
        }

        this.connectionState = 'connecting';
        console.log(`🔗 正在連接到WebSocket服務器: ${this.config.serverUrl}`);

        try {
            this.socket = new WebSocket(this.config.serverUrl);

            // 設置連接超時
            const connectionTimeout = setTimeout(() => {
                if (this.socket && this.socket.readyState === WebSocket.CONNECTING) {
                    this.socket.close();
                    this._handleError(new Error('連接超時'));
                }
            }, this.config.connectionTimeout);

            // 綁定事件處理器
            this.socket.onopen = (event) => {
                clearTimeout(connectionTimeout);
                this._handleConnect(event);
            };

            this.socket.onmessage = (event) => {
                this._handleMessage(event);
            };

            this.socket.onclose = (event) => {
                clearTimeout(connectionTimeout);
                this._handleDisconnect(event);
            };

            this.socket.onerror = (event) => {
                clearTimeout(connectionTimeout);
                this._handleError(new Error('WebSocket連接錯誤'));
            };

        } catch (error) {
            this.connectionState = 'error';
            console.error('WebSocket連接失敗:', error);
            this._handleError(error);
        }
    }

    /**
     * 斷開WebSocket連接
     */
    disconnect() {
        this.connectionState = 'disconnected';
        this.reconnectAttempts = 0;

        // 清理心跳
        this._clearHeartbeat();

        if (this.socket) {
            this.socket.close(1000, '客戶端主動斷開');
            this.socket = null;
        }

        this.isConnected = false;
        console.log('🔌 WebSocket已斷開連接');
    }

    /**
     * 發送消息到服務器
     */
    send(message) {
        if (!this.isConnected || !this.socket) {
            console.warn('WebSocket未連接，無法發送消息');
            return false;
        }

        try {
            const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
            this.socket.send(messageStr);
            return true;
        } catch (error) {
            console.error('發送WebSocket消息失敗:', error);
            return false;
        }
    }

    /**
     * 訂閱數據頻道
     */
    subscribe(channel) {
        if (!this.config.channels.includes(channel)) {
            console.warn(`未知頻道: ${channel}`);
            return false;
        }

        const message = {
            type: 'subscribe',
            data: { channel: channel },
            timestamp: new Date().toISOString()
        };

        return this.send(message);
    }

    /**
     * 取消訂閱數據頻道
     */
    unsubscribe(channel) {
        const message = {
            type: 'unsubscribe',
            data: { channel: channel },
            timestamp: new Date().toISOString()
        };

        return this.send(message);
    }

    /**
     * 添加事件監聽器
     */
    on(event, callback) {
        if (!this.callbacks[event]) {
            console.warn(`未知事件類型: ${event}`);
            return;
        }

        this.callbacks[event].push(callback);
    }

    /**
     * 移除事件監聽器
     */
    off(event, callback) {
        if (!this.callbacks[event]) {
            return;
        }

        const index = this.callbacks[event].indexOf(callback);
        if (index > -1) {
            this.callbacks[event].splice(index, 1);
        }
    }

    /**
     * 獲取連接狀態
     */
    getConnectionState() {
        return {
            state: this.connectionState,
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            performance: { ...this.performance }
        };
    }

    /**
     * 獲取緩存的數據
     */
    getCachedData() {
        return { ...this.dataCache };
    }

    /**
     * 處理連接成功
     */
    _handleConnect(event) {
        console.log('✅ WebSocket連接成功');

        this.isConnected = true;
        this.connectionState = 'connected';
        this.reconnectAttempts = 0;
        this.performance.connectionCount++;

        // 啟動心跳
        this._startHeartbeat();

        // 發送連接確認
        this._sendHeartbeat();

        // 觸發回調
        this._triggerCallbacks('onConnect', { event, performance: this.performance });

        // 訂閱所有頻道
        this.config.channels.forEach(channel => {
            this.subscribe(channel);
        });
    }

    /**
     * 處理接收到的消息
     */
    _handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.performance.messagesReceived++;

            // 處理心跳回應
            if (message.type === 'heartbeat_response') {
                this._handleHeartbeatResponse(message);
                return;
            }

            // 處理歡迎消息
            if (message.type === 'welcome') {
                console.log('🎉 收到服務器歡迎消息:', message.message);
                return;
            }

            // 處理數據消息
            this._processDataMessage(message);

            // 觸發通用消息回調
            this._triggerCallbacks('onMessage', message);

        } catch (error) {
            console.error('解析WebSocket消息失敗:', error);
        }
    }

    /**
     * 處理數據消息
     */
    _processDataMessage(message) {
        const { type, data, timestamp } = message;

        switch (type) {
            case 'strategy_data':
                this._updateStrategiesData(data);
                break;

            case 'performance_update':
                this._updatePerformanceData(data);
                break;

            case 'signals_update':
                this._updateSignalsData(data);
                break;

            case 'system_health':
                this._updateSystemHealth(data);
                break;

            default:
                console.log('收到未知類型消息:', type, data);
        }

        // 更新時間戳
        this.dataCache.lastUpdate = timestamp;
    }

    /**
     * 更新策略數據
     */
    _updateStrategiesData(data) {
        if (data.strategies) {
            this.dataCache.strategies = data.strategies;
            this._triggerCallbacks('onDataUpdate', {
                type: 'strategies',
                data: data.strategies,
                timestamp: data.timestamp
            });
        }
    }

    /**
     * 更新性能數據
     */
    _updatePerformanceData(data) {
        this._triggerCallbacks('onDataUpdate', {
            type: 'performance',
            data: data,
            timestamp: data.timestamp || new Date().toISOString()
        });
    }

    /**
     * 更新信號數據
     */
    _updateSignalsData(data) {
        this._triggerCallbacks('onDataUpdate', {
            type: 'signals',
            data: data,
            timestamp: data.timestamp || new Date().toISOString()
        });
    }

    /**
     * 更新系統健康狀態
     */
    _updateSystemHealth(data) {
        this.dataCache.systemHealth = data;
        this._triggerCallbacks('onDataUpdate', {
            type: 'system_health',
            data: data,
            timestamp: data.timestamp || new Date().toISOString()
        });
    }

    /**
     * 處理連接斷開
     */
    _handleDisconnect(event) {
        console.log('🔌 WebSocket連接已斷開', event.code, event.reason);

        this.isConnected = false;
        this.connectionState = 'disconnected';

        // 清理心跳
        this._clearHeartbeat();

        // 觸發回調
        this._triggerCallbacks('onDisconnect', { event, wasConnected: true });

        // 自動重連
        if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this._scheduleReconnect();
        } else {
            console.error('❌ 達到最大重連次數，停止重連');
            this._triggerCallbacks('onError', new Error('達到最大重連次數'));
        }
    }

    /**
     * 處理連接錯誤
     */
    _handleError(error) {
        console.error('❌ WebSocket連接錯誤:', error);

        this.connectionState = 'error';
        this._triggerCallbacks('onError', error);

        // 如果不是正在重連，則嘗試重連
        if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
            this._scheduleReconnect();
        }
    }

    /**
     * 安排重連
     */
    _scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = Math.min(this.config.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000);

        console.log(`⏰ ${delay}ms後嘗試第${this.reconnectAttempts}次重連...`);

        setTimeout(() => {
            if (this.connectionState !== 'connected') {
                this.connect();
            }
        }, delay);
    }

    /**
     * 啟動心跳機制
     */
    _startHeartbeat() {
        this._clearHeartbeat();

        this.heartbeatTimer = setInterval(() => {
            this._sendHeartbeat();
        }, this.config.heartbeatInterval);
    }

    /**
     * 清理心跳機制
     */
    _clearHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }

        if (this.heartbeatTimeoutTimer) {
            clearTimeout(this.heartbeatTimeoutTimer);
            this.heartbeatTimeoutTimer = null;
        }
    }

    /**
     * 發送心跳
     */
    _sendHeartbeat() {
        const startTime = Date.now();

        const message = {
            type: 'heartbeat',
            timestamp: new Date().toISOString()
        };

        if (this.send(message)) {
            // 設置心跳超時
            this.heartbeatTimeoutTimer = setTimeout(() => {
                console.warn('⚠️ 心跳超時，可能連接已斷開');
                this._handleError(new Error('心跳超時'));
            }, this.config.heartbeatTimeout);

            this.performance.lastPingTime = startTime;
        }
    }

    /**
     * 處理心跳回應
     */
    _handleHeartbeatResponse(message) {
        if (this.heartbeatTimeoutTimer) {
            clearTimeout(this.heartbeatTimeoutTimer);
            this.heartbeatTimeoutTimer = null;
        }

        // 計算延遲
        if (this.performance.lastPingTime) {
            const latency = Date.now() - this.performance.lastPingTime;
            this.performance.averageLatency =
                (this.performance.averageLatency * 0.8) + (latency * 0.2);
        }
    }

    /**
     * 觸發回調函數
     */
    _triggerCallbacks(event, data) {
        if (this.callbacks[event]) {
            this.callbacks[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`回調函數執行錯誤 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 節流數據更新
     */
    _throttleDataUpdate(type, data) {
        const key = type;
        const now = Date.now();

        if (this.dataUpdateBuffer.has(key)) {
            const lastUpdate = this.dataUpdateBuffer.get(key);
            if (now - lastUpdate < this.config.dataUpdateThrottle) {
                return false; // 節流，跳過此次更新
            }
        }

        this.dataUpdateBuffer.set(key, now);
        return true;
    }
}

// ========== 導出 ==========
window.DashboardWebSocketClient = DashboardWebSocketClient;
window.WEBSOCKET_CONFIG = WEBSOCKET_CONFIG;

// 全局WebSocket客戶端實例
window.dashboardWebSocket = null;

console.log('📡 Dashboard WebSocket客戶端模組已載入');