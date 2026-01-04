/**
 * 个人策略管理Dashboard - API客户端
 * Personal Strategy Management Dashboard - API Client
 */

import { API_CONFIG, ERROR_MESSAGES, EVENTS } from './constants.js';
import { handleError, debounce } from './utils.js';

/**
 * API请求错误类
 */
class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

/**
 * API客户端类
 */
class APIClient {
    constructor(baseURL = API_CONFIG.BASE_URL) {
        this.baseURL = baseURL;
        this.timeout = API_CONFIG.TIMEOUT;
        this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS;
        this.retryDelay = API_CONFIG.RETRY_DELAY;
        this.eventListeners = new Map();
    }

    /**
     * 发送HTTP请求
     * @param {string} url - 请求URL
     * @param {Object} options - 请求选项
     * @returns {Promise<Object>} 响应数据
     */
    async request(url, options = {}) {
        const {
            method = 'GET',
            headers = {},
            body = null,
            timeout = this.timeout,
            retries = this.retryAttempts
        } = options;

        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...headers
            },
            body: body ? JSON.stringify(body) : null
        };

        let lastError;

        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                // Add attempt info to headers for debugging
                if (attempt > 0) {
                    config.headers['X-Retry-Attempt'] = attempt.toString();
                }

                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);

                const response = await fetch(`${this.baseURL}${url}`, {
                    ...config,
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                // Handle response
                const responseData = await this.handleResponse(response);

                // Emit success event
                this.emit('request:success', { url, method, attempt, data: responseData });

                return responseData;

            } catch (error) {
                lastError = error;

                // Don't retry on abort or client errors
                if (error.name === 'AbortError' || (error.status >= 400 && error.status < 500)) {
                    break;
                }

                // Wait before retry
                if (attempt < retries) {
                    await this.delay(this.retryDelay * Math.pow(2, attempt));
                }
            }
        }

        // Emit error event
        this.emit('request:error', { url, method, error: lastError });

        throw lastError || new APIError('Request failed', 500);
    }

    /**
     * 处理响应
     * @param {Response} response - Fetch响应对象
     * @returns {Promise<Object>} 响应数据
     */
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        const isJson = contentType && contentType.includes('application/json');

        let data;
        try {
            data = isJson ? await response.json() : await response.text();
        } catch (error) {
            throw new APIError('Invalid response format', response.status);
        }

        if (!response.ok) {
            const message = data?.message || data?.error || response.statusText;
            throw new APIError(message, response.status, data);
        }

        return data;
    }

    /**
     * 延迟函数
     * @param {number} ms - 延迟毫秒数
     * @returns {Promise} Promise对象
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
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
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    // ===== 策略相关API =====

    /**
     * 获取策略列表
     * @returns {Promise<Array>} 策略列表
     */
    async getStrategies() {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.STRATEGIES);
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'getStrategies');
        }
    }

    /**
     * 获取策略详情
     * @param {string} id - 策略ID
     * @returns {Promise<Object>} 策略详情
     */
    async getStrategyDetail(id) {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.STRATEGY_DETAIL(id));
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'getStrategyDetail');
        }
    }

    /**
     * 创建策略
     * @param {Object} strategyData - 策略数据
     * @returns {Promise<Object>} 创建的策略
     */
    async createStrategy(strategyData) {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.STRATEGIES, {
                method: 'POST',
                body: strategyData
            });
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'createStrategy');
        }
    }

    /**
     * 更新策略
     * @param {string} id - 策略ID
     * @param {Object} updates - 更新数据
     * @returns {Promise<Object>} 更新的策略
     */
    async updateStrategy(id, updates) {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.STRATEGY_DETAIL(id), {
                method: 'PUT',
                body: updates
            });
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'updateStrategy');
        }
    }

    /**
     * 删除策略
     * @param {string} id - 策略ID
     * @returns {Promise<boolean>} 是否成功
     */
    async deleteStrategy(id) {
        try {
            await this.request(API_CONFIG.ENDPOINTS.STRATEGY_DELETE(id), {
                method: 'POST'
            });
            return true;
        } catch (error) {
            throw handleError(error, 'deleteStrategy');
        }
    }

    /**
     * 启动策略
     * @param {string} id - 策略ID
     * @returns {Promise<Object>} 启动结果
     */
    async startStrategy(id) {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.STRATEGY_START(id), {
                method: 'POST'
            });
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'startStrategy');
        }
    }

    /**
     * 停止策略
     * @param {string} id - 策略ID
     * @returns {Promise<Object>} 停止结果
     */
    async stopStrategy(id) {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.STRATEGY_STOP(id), {
                method: 'POST'
            });
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'stopStrategy');
        }
    }

    /**
     * 获取策略性能数据
     * @param {string} id - 策略ID
     * @param {string} period - 时间周期
     * @returns {Promise<Object>} 性能数据
     */
    async getStrategyPerformance(id, period = '1m') {
        try {
            const response = await this.request(
                `${API_CONFIG.ENDPOINTS.STRATEGY_PERFORMANCE(id)}?period=${period}`
            );
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'getStrategyPerformance');
        }
    }

    // ===== 市场数据相关API =====

    /**
     * 获取市场数据
     * @param {Object} params - 查询参数
     * @returns {Promise<Object>} 市场数据
     */
    async getMarketData(params = {}) {
        try {
            const queryString = new URLSearchParams(params).toString();
            const url = queryString
                ? `${API_CONFIG.ENDPOINTS.MARKET_DATA}?${queryString}`
                : API_CONFIG.ENDPOINTS.MARKET_DATA;

            const response = await this.request(url);
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'getMarketData');
        }
    }

    /**
     * 获取市场状态
     * @returns {Promise<Object>} 市场状态
     */
    async getMarketStatus() {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.MARKET_STATUS);
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'getMarketStatus');
        }
    }

    // ===== 统计数据相关API =====

    /**
     * 获取统计数据
     * @returns {Promise<Object>} 统计数据
     */
    async getStatistics() {
        try {
            const response = await this.request(API_CONFIG.ENDPOINTS.STATISTICS);
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'getStatistics');
        }
    }

    /**
     * 获取组合统计数据
     * @param {string} portfolioId - 组合ID
     * @returns {Promise<Object>} 组合统计数据
     */
    async getPortfolioStats(portfolioId) {
        try {
            const url = portfolioId
                ? `${API_CONFIG.ENDPOINTS.PORTFOLIO_STATS}/${portfolioId}`
                : API_CONFIG.ENDPOINTS.PORTFOLIO_STATS;

            const response = await this.request(url);
            return response.data || response;
        } catch (error) {
            throw handleError(error, 'getPortfolioStats');
        }
    }

    // ===== 批量操作 =====

    /**
     * 批量获取策略数据
     * @param {Array<string>} ids - 策略ID列表
     * @param {string} period - 时间周期
     * @returns {Promise<Array>} 策略数据列表
     */
    async batchGetStrategies(ids, period = '1m') {
        const promises = ids.map(id =>
            this.getStrategyPerformance(id, period)
                .catch(error => ({ id, error: error.message }))
        );

        try {
            const results = await Promise.allSettled(promises);
            return results.map(result =>
                result.status === 'fulfilled' ? result.value : { error: result.reason }
            );
        } catch (error) {
            throw handleError(error, 'batchGetStrategies');
        }
    }

    /**
     * 批量操作策略
     * @param {Array<Object>} operations - 操作列表
     * @returns {Promise<Array>} 操作结果列表
     */
    async batchOperateStrategies(operations) {
        const promises = operations.map(({ id, action, data }) => {
            switch (action) {
                case 'start':
                    return this.startStrategy(id);
                case 'stop':
                    return this.stopStrategy(id);
                case 'delete':
                    return this.deleteStrategy(id);
                case 'update':
                    return this.updateStrategy(id, data);
                default:
                    throw new Error(`Unknown action: ${action}`);
            }
        });

        try {
            const results = await Promise.allSettled(promises);
            return results.map(result =>
                result.status === 'fulfilled' ? result.value : { error: result.reason }
            );
        } catch (error) {
            throw handleError(error, 'batchOperateStrategies');
        }
    }

    // ===== 健康检查和连接测试 =====

    /**
     * 检查API健康状态
     * @returns {Promise<boolean>} 是否健康
     */
    async healthCheck() {
        try {
            await this.request('/health', { timeout: 3000 });
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * 测试连接
     * @returns {Promise<Object>} 连接测试结果
     */
    async testConnection() {
        const startTime = Date.now();

        try {
            await this.healthCheck();
            const responseTime = Date.now() - startTime;

            return {
                connected: true,
                responseTime,
                message: '连接成功'
            };
        } catch (error) {
            const responseTime = Date.now() - startTime;

            return {
                connected: false,
                responseTime,
                message: handleError(error, 'testConnection')
            };
        }
    }
}

/**
 * 创建防抖的API客户端
 * @param {number} delay - 防抖延迟
 * @returns {Object} 防抖的API客户端
 */
export function createDebouncedClient(delay = 300) {
    const client = new APIClient();

    // Create debounced versions of commonly used methods
    client.debouncedGetStrategies = debounce(client.getStrategies.bind(client), delay);
    client.debouncedGetStatistics = debounce(client.getStatistics.bind(client), delay);
    client.debouncedGetMarketData = debounce(client.getMarketData.bind(client), delay);

    return client;
}

// Create default instance
export const apiClient = new APIClient();

// Export classes and default instance
export { APIClient, APIError };
export default apiClient;