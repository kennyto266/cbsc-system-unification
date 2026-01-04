/**
 * 个人策略管理Dashboard - Sharpe比率分析服务
 * Personal Strategy Management Dashboard - Sharpe Ratio Analysis Service
 */

import { API_CONFIG, SHARPE_CONFIG } from './constants.js';

/**
 * Sharpe比率分析服务类
 * 提供与后端回测系统Sharpe分析API的集成
 */
class SharpeAnalysisService {
    constructor() {
        this.baseURL = API_CONFIG.BASE_URL;
        this.timeout = API_CONFIG.TIMEOUT;
        this.cache = new Map();
        this.cacheExpiry = 5 * 60 * 1000; // 5分钟缓存
    }

    /**
     * 生成缓存键
     * @param {string} method - 方法名
     * @param {Object} params - 参数
     * @returns {string} 缓存键
     */
    _getCacheKey(method, params) {
        return `${method}_${JSON.stringify(params)}`;
    }

    /**
     * 检查缓存是否有效
     * @param {string} key - 缓存键
     * @returns {boolean} 是否有效
     */
    _isCacheValid(key) {
        const cached = this.cache.get(key);
        if (!cached) return false;
        return Date.now() - cached.timestamp < this.cacheExpiry;
    }

    /**
     * 获取缓存数据
     * @param {string} key - 缓存键
     * @returns {any|null} 缓存数据
     */
    _getCache(key) {
        if (this._isCacheValid(key)) {
            return this.cache.get(key).data;
        }
        this.cache.delete(key);
        return null;
    }

    /**
     * 设置缓存数据
     * @param {string} key - 缓存键
     * @param {any} data - 数据
     */
    _setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    /**
     * 发送API请求
     * @param {string} endpoint - API端点
     * @param {Object} options - 请求选项
     * @returns {Promise<Object>} 响应数据
     */
    async _request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error?.message || 'API返回错误');
            }

            return data;
        } catch (error) {
            console.error(`Sharpe分析API错误 [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * 执行基础Sharpe比率分析
     * @param {Array} strategyReturns - 策略收益率数组
     * @param {Object} options - 分析选项
     * @returns {Promise<Object>} 分析结果
     */
    async analyzeSharpeRatio(strategyReturns, options = {}) {
        const cacheKey = this._getCacheKey('analyzeSharpeRatio', { strategyReturns, options });
        const cached = this._getCache(cacheKey);
        if (cached) return cached;

        const requestBody = {
            strategy_returns: strategyReturns,
            risk_free_rate: options.riskFreeRate || SHARPE_CONFIG.DEFAULT_RISK_FREE_RATE,
            benchmark_type: options.benchmarkType || 'market',
            benchmark_name: options.benchmarkName,
            window_size: options.windowSize || SHARPE_CONFIG.DEFAULT_WINDOW
        };

        const response = await this._request(API_CONFIG.ENDPOINTS.SHARPE_ANALYSIS, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });

        this._setCache(cacheKey, response.data);
        return response.data;
    }

    /**
     * 执行多基准对比分析
     * @param {Array} strategyReturns - 策略收益率数组
     * @param {Array} benchmarkNames - 基准名称数组
     * @param {Object} options - 分析选项
     * @returns {Promise<Object>} 对比分析结果
     */
    async compareWithBenchmarks(strategyReturns, benchmarkNames, options = {}) {
        const cacheKey = this._getCacheKey('compareWithBenchmarks', { strategyReturns, benchmarkNames, options });
        const cached = this._getCache(cacheKey);
        if (cached) return cached;

        const requestBody = {
            strategy_returns: strategyReturns,
            benchmark_names: benchmarkNames,
            risk_free_rate: options.riskFreeRate || SHARPE_CONFIG.DEFAULT_RISK_FREE_RATE,
            window_size: options.windowSize || SHARPE_CONFIG.DEFAULT_WINDOW
        };

        const response = await this._request(API_CONFIG.ENDPOINTS.BENCHMARK_COMPARISON, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });

        this._setCache(cacheKey, response.data);
        return response.data;
    }

    /**
     * 计算滚动Sharpe比率
     * @param {Array} strategyReturns - 策略收益率数组
     * @param {number} window - 滚动窗口大小
     * @param {Object} options - 分析选项
     * @returns {Promise<Object>} 滚动Sharpe比率数据
     */
    async calculateRollingSharpe(strategyReturns, window, options = {}) {
        const cacheKey = this._getCacheKey('calculateRollingSharpe', { strategyReturns, window, options });
        const cached = this._getCache(cacheKey);
        if (cached) return cached;

        const requestBody = {
            strategy_returns: strategyReturns,
            window: window || SHARPE_CONFIG.DEFAULT_WINDOW,
            risk_free_rate: options.riskFreeRate || SHARPE_CONFIG.DEFAULT_RISK_FREE_RATE
        };

        const response = await this._request(API_CONFIG.ENDPOINTS.ROLLING_SHARPE, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });

        this._setCache(cacheKey, response.data);
        return response.data;
    }

    /**
     * 执行Sharpe比率分布分析（Bootstrap）
     * @param {Array} strategyReturns - 策略收益率数组
     * @param {Object} options - 分析选项
     * @returns {Promise<Object>} 分布分析结果
     */
    async analyzeSharpeDistribution(strategyReturns, options = {}) {
        const cacheKey = this._getCacheKey('analyzeSharpeDistribution', { strategyReturns, options });
        const cached = this._getCache(cacheKey);
        if (cached) return cached;

        const requestBody = {
            strategy_returns: strategyReturns,
            risk_free_rate: options.riskFreeRate || SHARPE_CONFIG.DEFAULT_RISK_FREE_RATE,
            bootstrap_samples: options.bootstrapSamples || SHARPE_CONFIG.BOOTSTRAP_SAMPLES,
            confidence_level: options.confidenceLevel || 0.95
        };

        const response = await this._request(API_CONFIG.ENDPOINTS.SHARPE_DISTRIBUTION, {
            method: 'POST',
            body: JSON.stringify(requestBody)
        });

        this._setCache(cacheKey, response.data);
        return response.data;
    }

    /**
     * 获取可用基准列表
     * @returns {Promise<Array>} 基准列表
     */
    async getAvailableBenchmarks() {
        const cacheKey = 'availableBenchmarks';
        const cached = this._getCache(cacheKey);
        if (cached) return cached;

        try {
            const response = await this._request(API_CONFIG.ENDPOINTS.BENCHMARK_LIST);
            this._setCache(cacheKey, response.data);
            return response.data;
        } catch (error) {
            console.warn('获取基准列表失败，使用默认列表:', error);
            // 返回默认基准列表
            const defaultBenchmarks = [
                { code: 'HSI', name: '恒生指数', description: '香港市场基准' },
                { code: 'SP500', name: '标普500', description: '美国市场基准' },
                { code: 'SSE', name: '上证综指', description: 'A股市场基准' },
                { code: 'NASDAQ', name: '纳斯达克', description: '科技股基准' },
                { code: 'FTSE', name: '富时100', description: '英国市场基准' }
            ];
            this._setCache(cacheKey, defaultBenchmarks);
            return defaultBenchmarks;
        }
    }

    /**
     * 综合分析 - 一次性获取所有分析结果
     * @param {Array} strategyReturns - 策略收益率数组
     * @param {Object} options - 分析选项
     * @returns {Promise<Object>} 综合分析结果
     */
    async comprehensiveAnalysis(strategyReturns, options = {}) {
        const benchmarkNames = options.benchmarkNames || ['HSI'];
        const window = options.window || SHARPE_CONFIG.DEFAULT_WINDOW;

        try {
            // 并行执行所有分析
            const [
                basicAnalysis,
                benchmarkComparison,
                rollingSharpe,
                sharpeDistribution
            ] = await Promise.all([
                this.analyzeSharpeRatio(strategyReturns, {
                    riskFreeRate: options.riskFreeRate,
                    benchmarkType: options.benchmarkType,
                    benchmarkName: benchmarkNames[0],
                    windowSize: window
                }),
                this.compareWithBenchmarks(strategyReturns, benchmarkNames, {
                    riskFreeRate: options.riskFreeRate,
                    windowSize: window
                }),
                this.calculateRollingSharpe(strategyReturns, window, {
                    riskFreeRate: options.riskFreeRate
                }),
                this.analyzeSharpeDistribution(strategyReturns, {
                    riskFreeRate: options.riskFreeRate,
                    bootstrapSamples: options.bootstrapSamples,
                    confidenceLevel: options.confidenceLevel
                })
            ]);

            return {
                basic: basicAnalysis,
                benchmark: benchmarkComparison,
                rolling: rollingSharpe,
                distribution: sharpeDistribution,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('综合Sharpe分析失败:', error);
            throw error;
        }
    }

    /**
     * 格式化分析结果为图表数据
     * @param {Object} analysisResult - 分析结果
     * @returns {Object} 格式化的图表数据
     */
    formatForChart(analysisResult) {
        const chartData = {
            rollingSharpe: [],
            benchmarkComparison: {},
            distribution: null
        };

        // 处理滚动Sharpe比率数据
        if (analysisResult.rolling && analysisResult.rolling.rolling_sharpe) {
            chartData.rollingSharpe = analysisResult.rolling.rolling_sharpe.map(item => ({
                x: item.date || item.timestamp,
                y: item.sharpe_ratio
            }));
        }

        // 处理基准对比数据
        if (analysisResult.benchmark && analysisResult.benchmark.comparisons) {
            Object.entries(analysisResult.benchmark.comparisons).forEach(([benchmark, data]) => {
                chartData.benchmarkComparison[benchmark] = {
                    sharpeRatio: data.benchmark_sharpe,
                    excessSharpe: data.excess_sharpe,
                    informationRatio: data.information_ratio,
                    trackingError: data.tracking_error,
                    winRate: data.win_rate
                };
            });
        }

        // 处理分布数据
        if (analysisResult.distribution && analysisResult.distribution.distribution) {
            chartData.distribution = {
                mean: analysisResult.distribution.distribution.mean,
                std: analysisResult.distribution.distribution.std,
                percentiles: analysisResult.distribution.distribution.percentiles,
                confidenceIntervals: analysisResult.distribution.confidence_intervals
            };
        }

        return chartData;
    }

    /**
     * 清除缓存
     * @param {string} key - 特定缓存键，不提供则清除所有
     */
    clearCache(key = null) {
        if (key) {
            this.cache.delete(key);
        } else {
            this.cache.clear();
        }
    }

    /**
     * 获取缓存统计
     * @returns {Object} 缓存统计信息
     */
    getCacheStats() {
        const now = Date.now();
        let validCount = 0;
        let expiredCount = 0;

        this.cache.forEach((value, key) => {
            if (now - value.timestamp < this.cacheExpiry) {
                validCount++;
            } else {
                expiredCount++;
            }
        });

        return {
            total: this.cache.size,
            valid: validCount,
            expired: expiredCount,
            size: JSON.stringify([...this.cache.entries()]).length
        };
    }
}

// 创建全局服务实例
export const sharpeAnalysisService = new SharpeAnalysisService();

export default SharpeAnalysisService;