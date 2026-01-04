/**
 * 个人策略管理Dashboard - 事件总线
 * Personal Strategy Management Dashboard - Event Bus
 */

import { EVENTS } from './constants.js';

/**
 * 事件总线类
 */
class EventBus {
    constructor() {
        this.events = new Map();
        this.onceEvents = new Map();
        this.history = [];
        this.maxHistorySize = 100;
    }

    /**
     * 注册事件监听器
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     * @param {Object} options - 选项
     * @returns {Function} 取消监听的函数
     */
    on(event, callback, options = {}) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }

        const listener = {
            callback,
            once: false,
            context: options.context || null,
            priority: options.priority || 0,
            id: this.generateListenerId()
        };

        const listeners = this.events.get(event);
        listeners.push(listener);

        // Sort by priority (higher priority first)
        listeners.sort((a, b) => b.priority - a.priority);

        // Return unsubscribe function
        return () => this.off(event, callback);
    }

    /**
     * 注册一次性事件监听器
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     * @param {Object} options - 选项
     * @returns {Function} 取消监听的函数
     */
    once(event, callback, options = {}) {
        if (!this.onceEvents.has(event)) {
            this.onceEvents.set(event, []);
        }

        const listener = {
            callback,
            context: options.context || null,
            priority: options.priority || 0,
            id: this.generateListenerId()
        };

        const listeners = this.onceEvents.get(event);
        listeners.push(listener);

        // Sort by priority
        listeners.sort((a, b) => b.priority - a.priority);

        // Return unsubscribe function
        return () => this.offOnce(event, callback);
    }

    /**
     * 取消事件监听
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    off(event, callback) {
        const listeners = this.events.get(event);
        if (listeners) {
            const index = listeners.findIndex(l => l.callback === callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 取消一次性事件监听
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    offOnce(event, callback) {
        const listeners = this.onceEvents.get(event);
        if (listeners) {
            const index = listeners.findIndex(l => l.callback === callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 移除所有监听器
     * @param {string} event - 事件名称（可选）
     */
    removeAllListeners(event) {
        if (event) {
            this.events.delete(event);
            this.onceEvents.delete(event);
        } else {
            this.events.clear();
            this.onceEvents.clear();
        }
    }

    /**
     * 触发事件
     * @param {string} event - 事件名称
     * @param {any} data - 事件数据
     * @param {Object} options - 选项
     * @returns {Promise<Array>} 执行结果
     */
    async emit(event, data, options = {}) {
        const { async = false, timeout = 5000 } = options;

        // Record event in history
        this.recordEvent(event, data);

        // Get listeners
        const listeners = this.events.get(event) || [];
        const onceListeners = this.onceEvents.get(event) || [];

        // Combine all listeners
        const allListeners = [...listeners, ...onceListeners];

        if (allListeners.length === 0) {
            return [];
        }

        // Execute listeners
        const results = [];
        const errors = [];

        for (const listener of allListeners) {
            try {
                let result;

                if (async) {
                    // Execute with timeout
                    result = await this.executeWithTimeout(
                        () => listener.callback.call(listener.context, data),
                        timeout
                    );
                } else {
                    // Execute synchronously
                    result = listener.callback.call(listener.context, data);
                }

                results.push({
                    listenerId: listener.id,
                    result,
                    success: true
                });
            } catch (error) {
                errors.push({
                    listenerId: listener.id,
                    error,
                    success: false
                });

                // Log error but continue with other listeners
                console.error(`Error in event listener for ${event}:`, error);
            }
        }

        // Remove once listeners
        this.onceEvents.delete(event);

        // Return results
        if (errors.length > 0) {
            return [...results, ...errors];
        }

        return results;
    }

    /**
     * 带超时的执行函数
     * @param {Function} fn - 要执行的函数
     * @param {number} timeout - 超时时间
     * @returns {Promise} Promise对象
     */
    executeWithTimeout(fn, timeout) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                reject(new Error(`Listener execution timeout (${timeout}ms)`));
            }, timeout);

            Promise.resolve(fn()).then(
                result => {
                    clearTimeout(timer);
                    resolve(result);
                },
                error => {
                    clearTimeout(timer);
                    reject(error);
                }
            );
        });
    }

    /**
     * 记录事件历史
     * @param {string} event - 事件名称
     * @param {any} data - 事件数据
     */
    recordEvent(event, data) {
        const historyItem = {
            id: this.generateEventId(),
            event,
            data: typeof data === 'object' ? { ...data } : data,
            timestamp: Date.now(),
            listeners: (this.events.get(event) || []).length + (this.onceEvents.get(event) || []).length
        };

        this.history.unshift(historyItem);

        // Keep history size limited
        if (this.history.length > this.maxHistorySize) {
            this.history = this.history.slice(0, this.maxHistorySize);
        }
    }

    /**
     * 获取事件历史
     * @param {string} event - 事件名称（可选）
     * @param {number} limit - 限制数量
     * @returns {Array} 事件历史
     */
    getHistory(event, limit) {
        let history = this.history;

        if (event) {
            history = history.filter(item => item.event === event);
        }

        if (limit) {
            history = history.slice(0, limit);
        }

        return history;
    }

    /**
     * 清空事件历史
     */
    clearHistory() {
        this.history = [];
    }

    /**
     * 获取监听器统计
     * @returns {Object} 统计信息
     */
    getStats() {
        const stats = {
            totalEvents: this.events.size,
            totalOnceEvents: this.onceEvents.size,
            totalListeners: 0,
            eventDetails: {}
        };

        this.events.forEach((listeners, event) => {
            stats.totalListeners += listeners.length;
            stats.eventDetails[event] = {
                regular: listeners.length,
                once: (this.onceEvents.get(event) || []).length,
                total: listeners.length + (this.onceEvents.get(event) || []).length
            };
        });

        return stats;
    }

    /**
     * 检查是否有事件监听器
     * @param {string} event - 事件名称
     * @returns {boolean} 是否有监听器
     */
    hasListeners(event) {
        const regular = (this.events.get(event) || []).length;
        const once = (this.onceEvents.get(event) || []).length;
        return regular + once > 0;
    }

    /**
     * 获取事件监听器数量
     * @param {string} event - 事件名称
     * @returns {number} 监听器数量
     */
    getListenerCount(event) {
        const regular = (this.events.get(event) || []).length;
        const once = (this.onceEvents.get(event) || []).length;
        return regular + once;
    }

    /**
     * 生成监听器ID
     * @returns {string} 唯一ID
     */
    generateListenerId() {
        return `listener_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 生成事件ID
     * @returns {string} 唯一ID
     */
    generateEventId() {
        return `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 等待特定事件
     * @param {string} event - 事件名称
     * @param {number} timeout - 超时时间
     * @returns {Promise} Promise对象
     */
    waitFor(event, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                this.off(event, listener);
                reject(new Error(`Timeout waiting for event: ${event}`));
            }, timeout);

            const listener = (data) => {
                clearTimeout(timer);
                resolve(data);
            };

            this.once(event, listener);
        });
    }

    /**
     * 管道：将一个事件的输出作为下一个事件的输入
     * @param {...string} events - 事件名称列表
     * @returns {Function} 管道函数
     */
    pipe(...events) {
        return (initialData) => {
            return events.reduce(async (acc, event) => {
                const data = await acc;
                const results = await this.emit(event, data);
                return results[0]?.result || data;
            }, Promise.resolve(initialData));
        };
    }

    /**
     * 创建命名空间
     * @param {string} namespace - 命名空间
     * @returns {Object} 命名空间的事件总线
     */
    namespace(namespace) {
        return {
            on: (event, callback, options) => this.on(`${namespace}:${event}`, callback, options),
            once: (event, callback, options) => this.once(`${namespace}:${event}`, callback, options),
            off: (event, callback) => this.off(`${namespace}:${event}`, callback),
            emit: (event, data, options) => this.emit(`${namespace}:${event}`, data, options),
            removeAllListeners: (event) => this.removeAllListeners(
                event ? `${namespace}:${event}` : null
            ),
            waitFor: (event, timeout) => this.waitFor(`${namespace}:${event}`, timeout)
        };
    }
}

/**
 * 创建全局事件总线实例
 */
export const eventBus = new EventBus();

// 导出类和实例
export { EventBus };
export default eventBus;