/**
 * 个人策略管理Dashboard - WebSocket客户端
 * Personal Strategy Management Dashboard - WebSocket Client
 */

import { WEBSOCKET_CONFIG, EVENTS } from './constants.js';
import { handleError, debounce } from './utils.js';

/**
 * WebSocket客户端类
 */
class WebSocketClient {
    constructor(url = WEBSOCKET_CONFIG.URL) {
        this.url = url;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = WEBSOCKET_CONFIG.MAX_RECONNECT_ATTEMPTS;
        this.reconnectInterval = WEBSOCKET_CONFIG.RECONNECT_INTERVAL;
        this.heartbeatInterval = WEBSOCKET_CONFIG.HEARTBEAT_INTERVAL;
        this.heartbeatTimer = null;
        this.reconnectTimer = null;
        this.eventListeners = new Map();
        this.isConnected = false;
        this.messageQueue = [];
        this.subscriptions = new Set();
    }

    /**
     * 连接WebSocket
     * @returns {Promise<boolean>} 是否连接成功
     */
    connect() {
        return new Promise((resolve, reject) => {
            try {
                this.ws = new WebSocket(this.url);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.startHeartbeat();
                    this.processMessageQueue();
                    this.emit('connected');
                    resolve(true);
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.isConnected = false;
                    this.stopHeartbeat();
                    this.emit('disconnected');
                    this.attemptReconnect();
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.isConnected = false;
                    this.emit('error', error);
                    reject(error);
                };

            } catch (error) {
                console.error('Failed to create WebSocket connection:', error);
                reject(error);
            }
        });
    }

    /**
     * 断开连接
     */
    disconnect() {
        this.clearReconnectTimer();
        this.stopHeartbeat();

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.close();
        }

        this.ws = null;
        this.isConnected = false;
        this.messageQueue = [];
        this.subscriptions.clear();
    }

    /**
     * 发送消息
     * @param {Object} message - 消息对象
     */
    send(message) {
        const data = JSON.stringify({
            id: this.generateMessageId(),
            timestamp: Date.now(),
            ...message
        });

        if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        } else {
            // Queue message for when connection is restored
            this.messageQueue.push(data);
            console.log('Message queued:', message);
        }
    }

    /**
     * 订阅事件
     * @param {string} channel - 频道名称
     * @param {Object} filters - 过滤条件
     */
    subscribe(channel, filters = {}) {
        const subscription = {
            channel,
            filters,
            id: this.generateSubscriptionId()
        };

        this.subscriptions.add(subscription);

        this.send({
            type: 'subscribe',
            data: subscription
        });

        return subscription.id;
    }

    /**
     * 取消订阅
     * @param {string} subscriptionId - 订阅ID
     */
    unsubscribe(subscriptionId) {
        const subscription = Array.from(this.subscriptions)
            .find(sub => sub.id === subscriptionId);

        if (subscription) {
            this.subscriptions.delete(subscription);

            this.send({
                type: 'unsubscribe',
                data: { subscriptionId }
            });
        }
    }

    /**
     * 订阅策略更新
     * @param {Array<string>} strategyIds - 策略ID列表
     */
    subscribeStrategyUpdates(strategyIds = []) {
        return this.subscribe('strategy_updates', {
            strategy_ids: strategyIds
        });
    }

    /**
     * 订阅市场数据
     * @param {Array<string>} symbols - 交易对列表
     */
    subscribeMarketData(symbols = []) {
        return this.subscribe('market_data', {
            symbols
        });
    }

    /**
     * 订阅性能指标更新
     */
    subscribePerformanceUpdates() {
        return this.subscribe('performance_updates');
    }

    /**
     * 处理接收到的消息
     * @param {MessageEvent} event - 消息事件
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'ping':
                    this.handlePing();
                    break;
                case 'pong':
                    this.handlePong();
                    break;
                case 'strategy_update':
                    this.emit('strategy:update', data.data);
                    break;
                case 'market_data':
                    this.emit('market:data', data.data);
                    break;
                case 'performance_update':
                    this.emit('performance:update', data.data);
                    break;
                case 'error':
                    this.emit('server:error', data.data);
                    break;
                default:
                    this.emit('message', data);
            }
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }

    /**
     * 处理ping消息
     */
    handlePing() {
        this.send({ type: 'pong' });
    }

    /**
     * 处理pong消息
     */
    handlePong() {
        this.lastPongTime = Date.now();
    }

    /**
     * 开始心跳
     */
    startHeartbeat() {
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping' });

                // Check if pong was received
                setTimeout(() => {
                    const timeSinceLastPong = Date.now() - (this.lastPongTime || Date.now());
                    if (timeSinceLastPong > this.heartbeatInterval * 2) {
                        console.warn('Heartbeat timeout, reconnecting...');
                        this.ws.close();
                    }
                }, this.heartbeatInterval);
            }
        }, this.heartbeatInterval);
    }

    /**
     * 停止心跳
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * 尝试重新连接
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.emit('reconnect_failed');
            return;
        }

        this.reconnectAttempts++;

        this.clearReconnectTimer();

        this.reconnectTimer = setTimeout(() => {
            console.log(`Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            this.connect().catch(error => {
                console.error('Reconnection failed:', error);
            });
        }, this.reconnectInterval * this.reconnectAttempts);
    }

    /**
     * 清除重连定时器
     */
    clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    /**
     * 处理消息队列
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.ws.send(message);
        }
    }

    /**
     * 添加事件监听器
     * @param {string} event - 事件名称
     * @param {Function} listener - 监听器函数
     */
    on(event, listener) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(listener);
    }

    /**
     * 移除事件监听器
     * @param {string} event - 事件名称
     * @param {Function} listener - 监听器函数
     */
    off(event, listener) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(listener);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 触发事件
     * @param {string} event - 事件名称
     * @param {any} data - 事件数据
     */
    emit(event, data) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(listener => {
                try {
                    listener(data);
                } catch (error) {
                    console.error(`Error in WebSocket event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * 生成消息ID
     * @returns {string} 唯一ID
     */
    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 生成订阅ID
     * @returns {string} 唯一ID
     */
    generateSubscriptionId() {
        return `sub_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 获取连接状态
     * @returns {Object} 连接状态信息
     */
    getStatus() {
        return {
            connected: this.isConnected,
            readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
            reconnectAttempts: this.reconnectAttempts,
            subscriptions: Array.from(this.subscriptions),
            queuedMessages: this.messageQueue.length
        };
    }

    /**
     * 启用自动重连
     * @param {boolean} enabled - 是否启用
     */
    setAutoReconnect(enabled) {
        if (!enabled) {
            this.maxReconnectAttempts = 0;
        } else {
            this.maxReconnectAttempts = WEBSOCKET_CONFIG.MAX_RECONNECT_ATTEMPTS;
        }
    }
}

/**
 * 创建WebSocket客户端的工厂函数
 * @param {string} url - WebSocket URL
 * @param {Object} options - 配置选项
 * @returns {WebSocketClient} WebSocket客户端实例
 */
export function createWebSocketClient(url, options = {}) {
    const client = new WebSocketClient(url);

    // Apply options
    if (options.autoReconnect !== undefined) {
        client.setAutoReconnect(options.autoReconnect);
    }

    if (options.heartbeatInterval) {
        client.heartbeatInterval = options.heartbeatInterval;
    }

    if (options.reconnectInterval) {
        client.reconnectInterval = options.reconnectInterval;
    }

    return client;
}

/**
 * 管理WebSocket连接的单例
 */
class WebSocketManager {
    constructor() {
        this.clients = new Map();
    }

    /**
     * 获取或创建WebSocket客户端
     * @param {string} name - 客户端名称
     * @param {string} url - WebSocket URL
     * @param {Object} options - 配置选项
     * @returns {WebSocketClient} WebSocket客户端实例
     */
    getClient(name, url, options = {}) {
        if (!this.clients.has(name)) {
            const client = createWebSocketClient(url, options);
            this.clients.set(name, client);
        }
        return this.clients.get(name);
    }

    /**
     * 断开所有客户端
     */
    disconnectAll() {
        this.clients.forEach(client => {
            client.disconnect();
        });
        this.clients.clear();
    }

    /**
     * 获取所有客户端状态
     * @returns {Object} 所有客户端状态
     */
    getAllStatus() {
        const status = {};
        this.clients.forEach((client, name) => {
            status[name] = client.getStatus();
        });
        return status;
    }
}

// Create default instances
export const wsManager = new WebSocketManager();
export const defaultClient = createWebSocketClient();

// Export classes and instances
export { WebSocketClient, WebSocketManager };
export default defaultClient;