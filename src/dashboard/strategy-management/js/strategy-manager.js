/**
 * 个人策略管理Dashboard - 策略管理器
 * Personal Strategy Management Dashboard - Strategy Manager
 */

import { STRATEGY_TYPES, STRATEGY_STATUS, DEFAULT_VALUES } from './constants.js';
import { validate, deepClone } from './utils.js';

/**
 * 策略管理器类
 */
class StrategyManager {
    constructor(apiClient, storage, eventBus) {
        this.apiClient = apiClient;
        this.storage = storage;
        this.eventBus = eventBus;
        this.strategies = new Map();
        this.maxStrategies = 4;
        this.isLoading = false;

        // Load strategies from cache
        this.loadFromCache();
    }

    /**
     * 加载策略列表
     * @returns {Promise<Array>} 策略列表
     */
    async loadStrategies() {
        this.isLoading = true;

        try {
            // Try to load from API first
            const apiStrategies = await this.apiClient.getStrategies();

            // Update local strategies
            this.strategies.clear();
            apiStrategies.forEach(strategy => {
                this.strategies.set(strategy.id, strategy);
            });

            // Cache the strategies
            this.cacheStrategies();

            // Emit success event
            this.eventBus.emit('strategies:loaded', Array.from(this.strategies.values()));

            return Array.from(this.strategies.values());

        } catch (error) {
            console.warn('Failed to load strategies from API, using cache:', error);

            // Fallback to cached strategies
            const cachedStrategies = this.getCachedStrategies();
            if (cachedStrategies && cachedStrategies.length > 0) {
                this.strategies.clear();
                cachedStrategies.forEach(strategy => {
                    this.strategies.set(strategy.id, strategy);
                });

                this.eventBus.emit('strategies:loadedFromCache', Array.from(this.strategies.values()));
                return Array.from(this.strategies.values());
            }

            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 添加新策略
     * @param {Object} strategyData - 策略数据
     * @returns {Promise<Object>} 创建的策略
     */
    async addStrategy(strategyData) {
        // Check strategy limit
        if (this.strategies.size >= this.maxStrategies) {
            throw new Error(`最多支持${this.maxStrategies}个策略`);
        }

        // Validate strategy data
        const validation = this.validateStrategyData(strategyData);
        if (!validation.valid) {
            throw new Error(validation.errors.join(', '));
        }

        this.isLoading = true;

        try {
            // Set default values
            const completeData = {
                ...DEFAULT_VALUES.STRATEGY,
                ...strategyData,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };

            // Create strategy via API
            const newStrategy = await this.apiClient.createStrategy(completeData);

            // Add to local strategies
            this.strategies.set(newStrategy.id, newStrategy);

            // Cache strategies
            this.cacheStrategies();

            // Emit events
            this.eventBus.emit('strategy:added', newStrategy);
            this.eventBus.emit('strategies:updated', Array.from(this.strategies.values()));

            return newStrategy;

        } catch (error) {
            this.eventBus.emit('strategy:addError', error);
            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 更新策略
     * @param {string} id - 策略ID
     * @param {Object} updates - 更新数据
     * @returns {Promise<Object>} 更新的策略
     */
    async updateStrategy(id, updates) {
        const strategy = this.strategies.get(id);
        if (!strategy) {
            throw new Error('策略不存在');
        }

        // Validate updates
        const validation = this.validateStrategyData(updates, false);
        if (!validation.valid) {
            throw new Error(validation.errors.join(', '));
        }

        this.isLoading = true;

        try {
            // Prepare update data
            const updateData = {
                ...updates,
                updated_at: new Date().toISOString()
            };

            // Update via API
            const updatedStrategy = await this.apiClient.updateStrategy(id, updateData);

            // Update local strategy
            this.strategies.set(id, updatedStrategy);

            // Cache strategies
            this.cacheStrategies();

            // Emit events
            this.eventBus.emit('strategy:updated', updatedStrategy);
            this.eventBus.emit('strategies:updated', Array.from(this.strategies.values()));

            return updatedStrategy;

        } catch (error) {
            this.eventBus.emit('strategy:updateError', error);
            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 删除策略
     * @param {string} id - 策略ID
     * @returns {Promise<boolean>} 是否成功
     */
    async deleteStrategy(id) {
        const strategy = this.strategies.get(id);
        if (!strategy) {
            throw new Error('策略不存在');
        }

        this.isLoading = true;

        try {
            // Delete via API
            await this.apiClient.deleteStrategy(id);

            // Remove from local strategies
            this.strategies.delete(id);

            // Cache strategies
            this.cacheStrategies();

            // Emit events
            this.eventBus.emit('strategy:deleted', { id, strategy });
            this.eventBus.emit('strategies:updated', Array.from(this.strategies.values()));

            return true;

        } catch (error) {
            this.eventBus.emit('strategy:deleteError', error);
            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 启动策略
     * @param {string} id - 策略ID
     * @returns {Promise<Object>} 启动结果
     */
    async startStrategy(id) {
        const strategy = this.strategies.get(id);
        if (!strategy) {
            throw new Error('策略不存在');
        }

        if (strategy.status === STRATEGY_STATUS.RUNNING.value) {
            return strategy; // Already running
        }

        this.isLoading = true;

        try {
            // Start via API
            const result = await this.apiClient.startStrategy(id);

            // Update local strategy status
            const updatedStrategy = {
                ...strategy,
                status: STRATEGY_STATUS.RUNNING.value,
                updated_at: new Date().toISOString()
            };
            this.strategies.set(id, updatedStrategy);

            // Cache strategies
            this.cacheStrategies();

            // Emit events
            this.eventBus.emit('strategy:started', updatedStrategy);
            this.eventBus.emit('strategies:updated', Array.from(this.strategies.values()));

            return updatedStrategy;

        } catch (error) {
            this.eventBus.emit('strategy:startError', error);
            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 停止策略
     * @param {string} id - 策略ID
     * @returns {Promise<Object>} 停止结果
     */
    async stopStrategy(id) {
        const strategy = this.strategies.get(id);
        if (!strategy) {
            throw new Error('策略不存在');
        }

        if (strategy.status === STRATEGY_STATUS.STOPPED.value) {
            return strategy; // Already stopped
        }

        this.isLoading = true;

        try {
            // Stop via API
            const result = await this.apiClient.stopStrategy(id);

            // Update local strategy status
            const updatedStrategy = {
                ...strategy,
                status: STRATEGY_STATUS.STOPPED.value,
                updated_at: new Date().toISOString()
            };
            this.strategies.set(id, updatedStrategy);

            // Cache strategies
            this.cacheStrategies();

            // Emit events
            this.eventBus.emit('strategy:stopped', updatedStrategy);
            this.eventBus.emit('strategies:updated', Array.from(this.strategies.values()));

            return updatedStrategy;

        } catch (error) {
            this.eventBus.emit('strategy:stopError', error);
            throw error;
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 批量操作策略
     * @param {Array} operations - 操作列表
     * @returns {Promise<Array>} 操作结果
     */
    async batchOperateStrategies(operations) {
        const results = [];

        for (const operation of operations) {
            try {
                let result;
                switch (operation.action) {
                    case 'start':
                        result = await this.startStrategy(operation.id);
                        break;
                    case 'stop':
                        result = await this.stopStrategy(operation.id);
                        break;
                    case 'delete':
                        result = await this.deleteStrategy(operation.id);
                        break;
                    default:
                        throw new Error(`Unknown action: ${operation.action}`);
                }
                results.push({ success: true, id: operation.id, action: operation.action, result });
            } catch (error) {
                results.push({ success: false, id: operation.id, action: operation.action, error: error.message });
            }
        }

        return results;
    }

    /**
     * 获取策略列表
     * @param {Function} filter - 过滤函数
     * @returns {Array} 策略列表
     */
    getStrategies(filter = null) {
        const strategies = Array.from(this.strategies.values());
        return filter ? strategies.filter(filter) : strategies;
    }

    /**
     * 获取单个策略
     * @param {string} id - 策略ID
     * @returns {Object|null} 策略对象
     */
    getStrategyById(id) {
        return this.strategies.get(id) || null;
    }

    /**
     * 获取运行中的策略
     * @returns {Array} 运行中的策略列表
     */
    getRunningStrategies() {
        return this.getStrategies(strategy => strategy.status === STRATEGY_STATUS.RUNNING.value);
    }

    /**
     * 获取已停止的策略
     * @returns {Array} 已停止的策略列表
     */
    getStoppedStrategies() {
        return this.getStrategies(strategy => strategy.status === STRATEGY_STATUS.STOPPED.value);
    }

    /**
     * 获取策略统计
     * @returns {Object} 统计信息
     */
    getStats() {
        const strategies = Array.from(this.strategies.values());
        const running = this.getRunningStrategies();
        const stopped = this.getStoppedStrategies();

        // Calculate performance stats
        const totalReturn = strategies.reduce((sum, s) => sum + (s.current_return || 0), 0);
        const avgSharpe = strategies.length > 0
            ? strategies.reduce((sum, s) => sum + (s.sharpe_ratio || 0), 0) / strategies.length
            : 0;
        const maxDrawdown = strategies.length > 0
            ? Math.max(...strategies.map(s => s.max_drawdown || 0))
            : 0;

        return {
            total: strategies.length,
            running: running.length,
            stopped: stopped.length,
            maxStrategies: this.maxStrategies,
            available: this.maxStrategies - strategies.length,
            totalReturn,
            avgSharpe,
            maxDrawdown,
            isLoading: this.isLoading
        };
    }

    /**
     * 验证策略数据
     * @param {Object} data - 策略数据
     * @param {boolean} isRequired - 是否必填字段
     * @returns {Object} 验证结果
     */
    validateStrategyData(data, isRequired = true) {
        const rules = {};

        if (isRequired || data.name !== undefined) {
            rules.name = {
                required: isRequired,
                minLength: 2,
                maxLength: 50,
                pattern: /^[a-zA-Z0-9\u4e00-\u9fa5\s\-_]+$/,
                message: '策略名称必须是2-50个字符，支持中英文、数字、空格、横线和下划线'
            };
        }

        if (isRequired || data.initial_capital !== undefined) {
            rules.initial_capital = {
                required: isRequired,
                type: 'number',
                min: 10000,
                max: 100000000,
                message: '初始资金必须在10,000-100,000,000之间'
            };
        }

        if (isRequired || data.risk_limit !== undefined) {
            rules.risk_limit = {
                required: isRequired,
                type: 'number',
                min: 0.01,
                max: 1.0,
                message: '风险限制必须在1%-100%之间'
            };
        }

        if (data.description !== undefined) {
            rules.description = {
                maxLength: 500,
                message: '策略描述不能超过500个字符'
            };
        }

        return validate(data, rules);
    }

    /**
     * 缓存策略数据
     */
    cacheStrategies() {
        const strategies = Array.from(this.strategies.values());
        this.storage.set('strategies', strategies);
        this.storage.set('strategies_timestamp', Date.now());
    }

    /**
     * 从缓存加载策略
     * @returns {Array|null} 缓存的策略列表
     */
    getCachedStrategies() {
        const timestamp = this.storage.get('strategies_timestamp');
        const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

        // Check if cache is valid
        if (!timestamp || Date.now() - timestamp > CACHE_DURATION) {
            return null;
        }

        return this.storage.get('strategies') || null;
    }

    /**
     * 从缓存加载策略（内部方法）
     */
    loadFromCache() {
        const cachedStrategies = this.getCachedStrategies();
        if (cachedStrategies && cachedStrategies.length > 0) {
            this.strategies.clear();
            cachedStrategies.forEach(strategy => {
                this.strategies.set(strategy.id, strategy);
            });
        }
    }

    /**
     * 清空缓存
     */
    clearCache() {
        this.storage.remove('strategies');
        this.storage.remove('strategies_timestamp');
    }

    /**
     * 导出策略数据
     * @returns {string} JSON字符串
     */
    exportStrategies() {
        const strategies = Array.from(this.strategies.values());
        return JSON.stringify(strategies, null, 2);
    }

    /**
     * 导入策略数据
     * @param {string} jsonStr - JSON字符串
     * @returns {Promise<number>} 导入的策略数量
     */
    async importStrategies(jsonStr) {
        try {
            const strategies = JSON.parse(jsonStr);
            if (!Array.isArray(strategies)) {
                throw new Error('Invalid format');
            }

            let imported = 0;
            for (const strategyData of strategies) {
                try {
                    await this.addStrategy(strategyData);
                    imported++;
                } catch (error) {
                    console.warn(`Failed to import strategy ${strategyData.name || 'unknown'}:`, error);
                }
            }

            this.eventBus.emit('strategies:imported', { total: strategies.length, imported });
            return imported;

        } catch (error) {
            this.eventBus.emit('strategies:importError', error);
            throw error;
        }
    }

    /**
     * 搜索策略
     * @param {Object} criteria - 搜索条件
     * @returns {Array} 匹配的策略列表
     */
    searchStrategies(criteria) {
        const strategies = Array.from(this.strategies.values());

        return strategies.filter(strategy => {
            // Name search
            if (criteria.name && !strategy.name.toLowerCase().includes(criteria.name.toLowerCase())) {
                return false;
            }

            // Status search
            if (criteria.status && strategy.status !== criteria.status) {
                return false;
            }

            // Type search
            if (criteria.type && strategy.strategy_type !== criteria.type) {
                return false;
            }

            // Date range search
            if (criteria.dateFrom) {
                const createdDate = new Date(strategy.created_at);
                const fromDate = new Date(criteria.dateFrom);
                if (createdDate < fromDate) {
                    return false;
                }
            }

            if (criteria.dateTo) {
                const createdDate = new Date(strategy.created_at);
                const toDate = new Date(criteria.dateTo);
                if (createdDate > toDate) {
                    return false;
                }
            }

            return true;
        });
    }
}

export default StrategyManager;