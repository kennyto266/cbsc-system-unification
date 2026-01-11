/**
 * API Client Module - API客戶端模塊
 * 策略管理系統API接口封裝
 * 支持價格策略和非價格策略的統一數據獲取
 */

// API Configuration
const API_CONFIG = {
    BASE_URL: 'http://localhost:3004',
    ENDPOINTS: {
        // CBSC策略管理API端點
        STRATEGIES: '/api/strategies',
        STRATEGY_PERFORMANCE: '/api/strategies/performance',
        STRATEGY_LIST: '/api/strategies/list',
        STRATEGY_TOGGLE: '/api/strategies/{strategy_name}/toggle',
        STRATEGY_DETAILS: '/api/strategies/{strategy_name}/details',
        STRATEGY_STATUS: '/api/strategies/{strategy_id}/status',
        STRATEGY_METRICS: '/api/strategies/{strategy_id}/metrics',

        // 非價格策略API端點
        NON_PRICE_STRATEGIES: '/api/non-price/strategies/available',
        NON_PRICE_PERFORMANCE: '/api/non-price/strategies/performance/{strategy_id}',
        NON_PRICE_SENTIMENT: '/api/non-price/sentiment/latest/{symbol}',
        NON_PRICE_SIGNALS: '/api/non-price/sentiment/signals/{symbol}',

        // HKMA宏觀數據端點
        HKMA_HIBOR: '/api/non-price/hkma/hibor/latest',
        HKMA_MONETARY: '/api/non-price/hkma/monetary-base/latest',
        HKMA_LIQUIDITY: '/api/non-price/hkma/liquidity/latest'
    },
    TIMEOUT: 5000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000,
    CACHE_TTL: 10000 // 10 seconds
};

// Cache implementation
class APICache {
    constructor() {
        this.cache = new Map();
        this.timers = new Map();
    }

    // Set cache with TTL
    set(key, data, ttl = API_CONFIG.CACHE_TTL) {
        // Clear existing timer if any
        if (this.timers.has(key)) {
            clearTimeout(this.timers.get(key));
        }

        // Set cache data
        this.cache.set(key, {
            data: data,
            timestamp: Date.now(),
            ttl: ttl
        });

        // Set expiration timer
        const timer = setTimeout(() => {
            this.delete(key);
        }, ttl);
        this.timers.set(key, timer);
    }

    // Get cached data
    get(key) {
        const cached = this.cache.get(key);
        if (!cached) {
            return null;
        }

        // Check if expired
        if (Date.now() - cached.timestamp > cached.ttl) {
            this.delete(key);
            return null;
        }

        return cached.data;
    }

    // Delete cache entry
    delete(key) {
        this.cache.delete(key);
        if (this.timers.has(key)) {
            clearTimeout(this.timers.get(key));
            this.timers.delete(key);
        }
    }

    // Clear all cache
    clear() {
        this.cache.clear();
        this.timers.forEach(timer => clearTimeout(timer));
        this.timers.clear();
    }
}

// Error handling
class APIError extends Error {
    constructor(message, status = null, data = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

// Main API Client class
class APIClient {
    constructor() {
        this.cache = new APICache();
        this.baseURL = API_CONFIG.BASE_URL;
        this.timeout = API_CONFIG.TIMEOUT;
        this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS;
        this.retryDelay = API_CONFIG.RETRY_DELAY;
    }

    /**
     * Generic HTTP request method with error handling and retry
     * @param {string} url - Request URL
     * @param {Object} options - Fetch options
     * @param {boolean} useCache - Whether to use cache
     * @param {string} cacheKey - Cache key override
     * @returns {Promise} Response data
     */
    async request(url, options = {}, useCache = true, cacheKey = null) {
        const fullUrl = url.startsWith('http') ? url : `${this.baseURL}${url}`;
        const key = cacheKey || `${fullUrl}_${JSON.stringify(options)}`;

        // Try cache first
        if (useCache && options.method !== 'POST' && options.method !== 'PUT' && options.method !== 'DELETE') {
            const cached = this.cache.get(key);
            if (cached) {
                console.log(`Cache hit for: ${key}`);
                return cached;
            }
        }

        let lastError;

        // Retry mechanism
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.timeout);

                const response = await fetch(fullUrl, {
                    ...options,
                    signal: controller.signal,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        ...options.headers
                    }
                });

                clearTimeout(timeoutId);

                // Handle HTTP errors
                if (!response.ok) {
                    const errorData = await response.json().catch(() => null);
                    throw new APIError(
                        errorData?.error?.message || errorData?.message || `HTTP ${response.status}: ${response.statusText}`,
                        response.status,
                        errorData
                    );
                }

                // Parse response
                const data = await response.json();

                // Cache successful GET requests
                if (useCache && options.method !== 'POST' && options.method !== 'PUT' && options.method !== 'DELETE') {
                    this.cache.set(key, data);
                }

                console.log(`API request successful: ${fullUrl} (attempt ${attempt})`);
                return data;

            } catch (error) {
                lastError = error;

                // Don't retry on abort or client errors (4xx)
                if (error.name === 'AbortError' || (error.status >= 400 && error.status < 500)) {
                    break;
                }

                // Log retry attempt
                if (attempt < this.retryAttempts) {
                    console.warn(`API request failed (attempt ${attempt}/${this.retryAttempts}): ${error.message}. Retrying in ${this.retryDelay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                }
            }
        }

        // All attempts failed
        console.error(`API request failed after ${this.retryAttempts} attempts: ${fullUrl}`, lastError);
        throw lastError;
    }

    /**
     * GET request convenience method
     */
    async get(url, params = {}, useCache = true) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;

        return this.request(fullUrl, { method: 'GET' }, useCache);
    }

    /**
     * POST request convenience method
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        }, false);
    }

    /**
     * PUT request convenience method
     */
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        }, false);
    }

    /**
     * DELETE request convenience method
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' }, false);
    }
}

// Strategy API client extending base API client
class StrategyAPI extends APIClient {
    constructor() {
        super();
        this.endpoints = API_CONFIG.ENDPOINTS;
    }

    /**
     * Get strategy performance data
     * @returns {Promise<Array>} Array of strategy performance objects
     */
    async getStrategyPerformance() {
        try {
            const response = await this.get(this.endpoints.STRATEGY_PERFORMANCE);

            // Handle different response formats
            if (response.success && response.data) {
                return response.data.map(this.formatStrategyPerformance);
            } else if (Array.isArray(response)) {
                return response.map(this.formatStrategyPerformance);
            } else {
                console.warn('Unexpected response format for strategy performance:', response);
                return [];
            }
        } catch (error) {
            console.error('Failed to get strategy performance:', error);
            throw error;
        }
    }

    /**
     * Get strategy list
     * @returns {Promise<Array>} Array of strategy objects
     */
    async getStrategyList() {
        try {
            const response = await this.get(this.endpoints.STRATEGY_LIST);

            // Handle different response formats
            if (response.success && response.data) {
                return response.data.map(this.formatStrategyConfig);
            } else if (Array.isArray(response)) {
                return response.map(this.formatStrategyConfig);
            } else {
                console.warn('Unexpected response format for strategy list:', response);
                return [];
            }
        } catch (error) {
            console.error('Failed to get strategy list:', error);
            throw error;
        }
    }

    /**
     * Toggle strategy enabled/disabled status
     * @param {string} strategyName - Strategy name
     * @returns {Promise<Object>} Updated strategy configuration
     */
    async toggleStrategy(strategyName) {
        try {
            const url = this.endpoints.STRATEGY_TOGGLE.replace('{strategy_name}', strategyName);
            const response = await this.post(url);

            if (response.success) {
                return this.formatStrategyConfig(response.data);
            } else {
                throw new APIError(response.error?.message || 'Failed to toggle strategy');
            }
        } catch (error) {
            console.error(`Failed to toggle strategy ${strategyName}:`, error);
            throw error;
        }
    }

    /**
     * Get strategy details
     * @param {string} strategyName - Strategy name
     * @returns {Promise<Object>} Strategy details object
     */
    async getStrategyDetails(strategyName) {
        try {
            const url = this.endpoints.STRATEGY_DETAILS.replace('{strategy_name}', strategyName);
            const response = await this.get(url);

            if (response.success && response.data) {
                return this.formatStrategyDetails(response.data);
            } else {
                throw new APIError('Strategy not found');
            }
        } catch (error) {
            console.error(`Failed to get strategy details for ${strategyName}:`, error);
            throw error;
        }
    }

    /**
     * Get non-price strategies
     * @returns {Promise<Array>} Array of non-price strategy objects
     */
    async getNonPriceStrategies() {
        try {
            const response = await this.get(this.endpoints.NON_PRICE_STRATEGIES);

            if (response.success && response.data) {
                return response.data.strategies || [];
            } else {
                console.warn('Unexpected response format for non-price strategies:', response);
                return [];
            }
        } catch (error) {
            console.error('Failed to get non-price strategies:', error);
            throw error;
        }
    }

    /**
     * Get HKMA macro data
     * @returns {Promise<Object>} Macro data object
     */
    async getMacroData() {
        try {
            const [hibor, monetary, liquidity] = await Promise.all([
                this.get(this.endpoints.HKMA_HIBOR),
                this.get(this.endpoints.HKMA_MONETARY),
                this.get(this.endpoints.HKMA_LIQUIDITY)
            ]);

            return {
                hibor: hibor.success ? hibor.data : null,
                monetary: monetary.success ? monetary.data : null,
                liquidity: liquidity.success ? liquidity.data : null,
                lastUpdated: new Date().toISOString()
            };
        } catch (error) {
            console.error('Failed to get macro data:', error);
            throw error;
        }
    }

    /**
     * Format strategy performance data
     * @private
     */
    formatStrategyPerformance(data) {
        return {
            name: data.name || data.strategy_name,
            sharpeRatio: parseFloat(data.sharpe_ratio || data.sharpeRatio || 0),
            maxDrawdown: parseFloat(data.max_drawdown || data.maxDrawdown || 0),
            totalReturn: parseFloat(data.total_return || data.totalReturn || 0),
            winRate: parseFloat(data.win_rate || data.winRate || 0),
            status: data.status || 'unknown',
            lastUpdated: new Date().toISOString(),
            // Additional metrics
            annualReturn: parseFloat(data.annual_return || data.annualReturn || data.total_return || 0),
            profitFactor: parseFloat(data.profit_factor || data.profitFactor || 0),
            calmarRatio: parseFloat(data.calmar_ratio || data.calmarRatio || 0),
            totalTrades: parseInt(data.total_trades || data.totalTrades || 0),
            profitTrades: parseInt(data.profit_trades || data.profitTrades || 0)
        };
    }

    /**
     * Format strategy configuration data
     * @private
     */
    formatStrategyConfig(data) {
        return {
            name: data.name || data.strategy_name,
            enabled: data.enabled !== undefined ? data.enabled : data.is_active,
            parameters: data.parameters || {},
            description: data.description || '',
            strategyType: data.strategy_type || data.strategyType || 'unknown',
            category: data.category || 'default',
            riskLevel: data.risk_level || data.riskLevel || 'medium',
            lastUpdated: data.last_updated || data.lastUpdate || new Date().toISOString()
        };
    }

    /**
     * Format strategy details data
     * @private
     */
    formatStrategyDetails(data) {
        return {
            name: data.name || data.strategy_name,
            parameters: data.parameters || {},
            lastSignal: data.last_signal || data.lastSignal || null,
            performance: data.performance || null,
            configuration: data.configuration || {},
            metadata: data.metadata || {},
            lastUpdated: new Date().toISOString()
        };
    }
}

// Export instances and classes
const apiClient = new APIClient();
const strategyAPI = new StrategyAPI();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        APIClient,
        StrategyAPI,
        APIError,
        APICache,
        apiClient,
        strategyAPI,
        API_CONFIG
    };
}

// Global assignment for browser
window.StrategyAPI = StrategyAPI;
window.strategyAPI = strategyAPI;
window.APIClient = APIClient;
window.apiClient = apiClient;
window.API_CONFIG = API_CONFIG;