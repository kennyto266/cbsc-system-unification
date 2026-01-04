/**
 * 个人策略管理Dashboard - 本地存储管理
 * Personal Strategy Management Dashboard - Local Storage Management
 */

import { STORAGE_KEYS, CACHE_CONFIG } from './constants.js';
import { safeJsonParse } from './utils.js';

/**
 * 本地存储管理类
 */
class LocalStorage {
    constructor(prefix = '') {
        this.prefix = prefix;
        this.cache = new Map();
        this.cacheTimeouts = new Map();
    }

    /**
     * 设置存储项
     * @param {string} key - 存储键
     * @param {any} value - 存储值
     * @param {number} ttl - 过期时间（毫秒）
     */
    set(key, value, ttl) {
        try {
            const fullKey = this.getFullKey(key);
            const item = {
                value,
                timestamp: Date.now(),
                ttl: ttl || null
            };

            localStorage.setItem(fullKey, JSON.stringify(item));

            // Update memory cache
            this.cache.set(fullKey, item);

            // Set timeout for cache invalidation
            if (ttl) {
                const timeoutId = setTimeout(() => {
                    this.remove(key);
                    this.cache.delete(fullKey);
                }, ttl);
                this.cacheTimeouts.set(fullKey, timeoutId);
            }

            return true;
        } catch (error) {
            console.warn('LocalStorage set error:', error);
            return false;
        }
    }

    /**
     * 获取存储项
     * @param {string} key - 存储键
     * @param {any} defaultValue - 默认值
     * @returns {any} 存储的值或默认值
     */
    get(key, defaultValue = null) {
        try {
            const fullKey = this.getFullKey(key);

            // Check memory cache first
            if (this.cache.has(fullKey)) {
                const item = this.cache.get(fullKey);
                if (this.isItemValid(item)) {
                    return item.value;
                }
                this.cache.delete(fullKey);
            }

            // Check localStorage
            const stored = localStorage.getItem(fullKey);
            if (stored === null) {
                return defaultValue;
            }

            const item = safeJsonParse(stored);
            if (!item || !this.isItemValid(item)) {
                this.remove(key);
                return defaultValue;
            }

            // Update memory cache
            this.cache.set(fullKey, item);
            return item.value;
        } catch (error) {
            console.warn('LocalStorage get error:', error);
            return defaultValue;
        }
    }

    /**
     * 删除存储项
     * @param {string} key - 存储键
     */
    remove(key) {
        try {
            const fullKey = this.getFullKey(key);

            // Remove from localStorage
            localStorage.removeItem(fullKey);

            // Remove from memory cache
            this.cache.delete(fullKey);

            // Clear timeout
            const timeoutId = this.cacheTimeouts.get(fullKey);
            if (timeoutId) {
                clearTimeout(timeoutId);
                this.cacheTimeouts.delete(fullKey);
            }

            return true;
        } catch (error) {
            console.warn('LocalStorage remove error:', error);
            return false;
        }
    }

    /**
     * 清空所有存储项
     * @param {string} pattern - 键模式（可选）
     */
    clear(pattern = null) {
        try {
            // Clear all timeouts
            this.cacheTimeouts.forEach(timeoutId => clearTimeout(timeoutId));
            this.cacheTimeouts.clear();

            // Clear memory cache
            this.cache.clear();

            // Clear localStorage
            if (pattern) {
                const regex = new RegExp(`^${this.prefix}${pattern}`);
                Object.keys(localStorage).forEach(key => {
                    if (regex.test(key)) {
                        localStorage.removeItem(key);
                    }
                });
            } else {
                // Only clear items with this prefix
                Object.keys(localStorage).forEach(key => {
                    if (key.startsWith(this.prefix)) {
                        localStorage.removeItem(key);
                    }
                });
            }

            return true;
        } catch (error) {
            console.warn('LocalStorage clear error:', error);
            return false;
        }
    }

    /**
     * 检查存储项是否存在
     * @param {string} key - 存储键
     * @returns {boolean} 是否存在
     */
    has(key) {
        try {
            const fullKey = this.getFullKey(key);

            // Check memory cache first
            if (this.cache.has(fullKey)) {
                const item = this.cache.get(fullKey);
                return this.isItemValid(item);
            }

            // Check localStorage
            const stored = localStorage.getItem(fullKey);
            if (stored === null) {
                return false;
            }

            const item = safeJsonParse(stored);
            if (!item || !this.isItemValid(item)) {
                this.remove(key);
                return false;
            }

            return true;
        } catch (error) {
            console.warn('LocalStorage has error:', error);
            return false;
        }
    }

    /**
     * 获取所有键
     * @param {string} pattern - 键模式（可选）
     * @returns {string[]} 键列表
     */
    keys(pattern = null) {
        try {
            const keys = [];
            const prefix = this.prefix;

            Object.keys(localStorage).forEach(key => {
                if (key.startsWith(prefix)) {
                    const itemKey = key.substring(prefix.length);

                    // Apply pattern filter if provided
                    if (pattern && !new RegExp(pattern).test(itemKey)) {
                        return;
                    }

                    // Check if item is valid
                    const stored = localStorage.getItem(key);
                    const item = safeJsonParse(stored);
                    if (item && this.isItemValid(item)) {
                        keys.push(itemKey);
                    }
                }
            });

            return keys;
        } catch (error) {
            console.warn('LocalStorage keys error:', error);
            return [];
        }
    }

    /**
     * 获取存储大小
     * @returns {number} 存储大小（字节）
     */
    size() {
        try {
            let size = 0;
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith(this.prefix)) {
                    size += localStorage.getItem(key).length;
                }
            });
            return size;
        } catch (error) {
            console.warn('LocalStorage size error:', error);
            return 0;
        }
    }

    /**
     * 获取完整的存储键
     * @param {string} key - 原始键
     * @returns {string} 完整的键
     */
    getFullKey(key) {
        return `${this.prefix}${key}`;
    }

    /**
     * 检查存储项是否有效
     * @param {Object} item - 存储项对象
     * @returns {boolean} 是否有效
     */
    isItemValid(item) {
        if (!item || typeof item !== 'object') {
            return false;
        }

        // Check if item has expired
        if (item.ttl && Date.now() - item.timestamp > item.ttl) {
            return false;
        }

        return true;
    }

    /**
     * 清理过期项
     */
    cleanup() {
        try {
            const now = Date.now();
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith(this.prefix)) {
                    const stored = localStorage.getItem(key);
                    const item = safeJsonParse(stored);

                    if (item && item.ttl && now - item.timestamp > item.ttl) {
                        localStorage.removeItem(key);
                        this.cache.delete(key);

                        const timeoutId = this.cacheTimeouts.get(key);
                        if (timeoutId) {
                            clearTimeout(timeoutId);
                            this.cacheTimeouts.delete(key);
                        }
                    }
                }
            });
        } catch (error) {
            console.warn('LocalStorage cleanup error:', error);
        }
    }
}

/**
 * 缓存管理类
 */
class CacheManager {
    constructor(storage, maxSize = CACHE_CONFIG.MAX_CACHE_SIZE) {
        this.storage = storage;
        this.maxSize = maxSize;
        this.accessOrder = new Map(); // LRU tracking
    }

    /**
     * 设置缓存项
     * @param {string} key - 缓存键
     * @param {any} value - 缓存值
     * @param {number} ttl - 过期时间
     */
    set(key, value, ttl) {
        // Check cache size limit
        if (this.accessOrder.size >= this.maxSize) {
            this.evictLRU();
        }

        const cacheKey = `cache_${key}`;
        const success = this.storage.set(cacheKey, value, ttl);

        if (success) {
            this.accessOrder.set(key, Date.now());
        }

        return success;
    }

    /**
     * 获取缓存项
     * @param {string} key - 缓存键
     * @param {any} defaultValue - 默认值
     * @returns {any} 缓存值或默认值
     */
    get(key, defaultValue = null) {
        const cacheKey = `cache_${key}`;
        const value = this.storage.get(cacheKey, defaultValue);

        if (value !== defaultValue) {
            this.accessOrder.set(key, Date.now());
        }

        return value;
    }

    /**
     * 删除缓存项
     * @param {string} key - 缓存键
     */
    remove(key) {
        const cacheKey = `cache_${key}`;
        this.storage.remove(cacheKey);
        this.accessOrder.delete(key);
    }

    /**
     * 清空缓存
     */
    clear() {
        this.storage.clear('cache_');
        this.accessOrder.clear();
    }

    /**
     * 检查缓存项是否存在
     * @param {string} key - 缓存键
     * @returns {boolean} 是否存在
     */
    has(key) {
        const cacheKey = `cache_${key}`;
        return this.storage.has(cacheKey);
    }

    /**
     * 获取缓存统计
     * @returns {Object} 缓存统计信息
     */
    getStats() {
        return {
            size: this.accessOrder.size,
            maxSize: this.maxSize,
            keys: Array.from(this.accessOrder.keys())
        };
    }

    /**
     * LRU淘汰策略
     */
    evictLRU() {
        let oldestKey = null;
        let oldestTime = Date.now();

        this.accessOrder.forEach((time, key) => {
            if (time < oldestTime) {
                oldestTime = time;
                oldestKey = key;
            }
        });

        if (oldestKey) {
            this.remove(oldestKey);
        }
    }
}

/**
 * 数据库操作封装
 */
class Database {
    constructor(storage) {
        this.storage = storage;
    }

    /**
     * 创建表
     * @param {string} tableName - 表名
     * @param {Object} schema - 表结构
     */
    createTable(tableName, schema) {
        const tableKey = `table_${tableName}`;
        const table = {
            name: tableName,
            schema,
            data: [],
            indexes: {},
            created: Date.now()
        };

        this.storage.set(tableKey, table);
        return table;
    }

    /**
     * 获取表
     * @param {string} tableName - 表名
     * @returns {Object|null} 表对象
     */
    getTable(tableName) {
        const tableKey = `table_${tableName}`;
        return this.storage.get(tableKey);
    }

    /**
     * 删除表
     * @param {string} tableName - 表名
     */
    dropTable(tableName) {
        const tableKey = `table_${tableName}`;
        this.storage.remove(tableKey);
    }

    /**
     * 插入数据
     * @param {string} tableName - 表名
     * @param {Object} record - 记录
     * @returns {Object} 插入的记录
     */
    insert(tableName, record) {
        const table = this.getTable(tableName);
        if (!table) {
            throw new Error(`Table ${tableName} does not exist`);
        }

        const newRecord = {
            id: this.generateId(),
            ...record,
            created: Date.now(),
            updated: Date.now()
        };

        table.data.push(newRecord);
        this.updateTable(tableName, table);

        return newRecord;
    }

    /**
     * 查询数据
     * @param {string} tableName - 表名
     * @param {Function} filter - 过滤函数
     * @returns {Array} 查询结果
     */
    select(tableName, filter = null) {
        const table = this.getTable(tableName);
        if (!table) {
            return [];
        }

        let results = table.data;

        if (filter) {
            results = results.filter(filter);
        }

        return results;
    }

    /**
     * 更新数据
     * @param {string} tableName - 表名
     * @param {string|Function} condition - 更新条件
     * @param {Object} updates - 更新数据
     * @returns {number} 更新的记录数
     */
    update(tableName, condition, updates) {
        const table = this.getTable(tableName);
        if (!table) {
            return 0;
        }

        let count = 0;
        table.data = table.data.map(record => {
            const shouldUpdate = typeof condition === 'string'
                ? record.id === condition
                : condition(record);

            if (shouldUpdate) {
                count++;
                return {
                    ...record,
                    ...updates,
                    updated: Date.now()
                };
            }

            return record;
        });

        this.updateTable(tableName, table);
        return count;
    }

    /**
     * 删除数据
     * @param {string} tableName - 表名
     * @param {string|Function} condition - 删除条件
     * @returns {number} 删除的记录数
     */
    delete(tableName, condition) {
        const table = this.getTable(tableName);
        if (!table) {
            return 0;
        }

        const originalLength = table.data.length;

        table.data = table.data.filter(record => {
            const shouldDelete = typeof condition === 'string'
                ? record.id !== condition
                : !condition(record);
            return shouldDelete;
        });

        const deletedCount = originalLength - table.data.length;
        this.updateTable(tableName, table);

        return deletedCount;
    }

    /**
     * 生成ID
     * @returns {string} 唯一ID
     */
    generateId() {
        return `id_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * 更新表
     * @param {string} tableName - 表名
     * @param {Object} table - 表对象
     */
    updateTable(tableName, table) {
        const tableKey = `table_${tableName}`;
        this.storage.set(tableKey, table);
    }
}

// Create default instances
const defaultStorage = new LocalStorage('strategy-dashboard-');
const cache = new CacheManager(defaultStorage);
const db = new Database(defaultStorage);

// Cleanup expired items on load
defaultStorage.cleanup();

// Export classes and instances
export {
    LocalStorage,
    CacheManager,
    Database,
    defaultStorage as storage,
    cache,
    db
};

export default {
    LocalStorage,
    CacheManager,
    Database,
    storage: defaultStorage,
    cache,
    db
};