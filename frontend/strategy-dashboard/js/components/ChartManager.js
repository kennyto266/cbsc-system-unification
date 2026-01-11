/**
 * 圖表管理器
 * 統一管理所有圖表實例，提供批量更新和同步功能
 */
class ChartManager {
    constructor(options = {}) {
        // 配置選項
        this.options = {
            autoRefresh: options.autoRefresh !== false,
            refreshInterval: options.refreshInterval || 10000, // 10秒
            enableWebSocket: options.enableWebSocket || false,
            wsEndpoint: options.wsEndpoint || null,
            colorScheme: options.colorScheme || 'default',
            animationDuration: options.animationDuration || 750,
            ...options
        };

        // 圖表實例註冊表
        this.charts = new Map();

        // 數據緩存
        this.dataCache = new Map();

        // WebSocket連接
        this.wsConnection = null;

        // 刷新計時器
        this.refreshTimer = null;

        // 事件監聽器
        this.eventListeners = new Map();

        // 初始化
        this._init();
    }

    /**
     * 初始化管理器
     */
    _init() {
        console.log('ChartManager: Initializing...');

        // 設置全局Chart.js默認配置
        this._setGlobalDefaults();

        // 啟動自動刷新
        if (this.options.autoRefresh) {
            this._startAutoRefresh();
        }

        // 初始化WebSocket連接
        if (this.options.enableWebSocket && this.options.wsEndpoint) {
            this._initWebSocket();
        }

        // 監聽頁面可見性變化
        document.addEventListener('visibilitychange', () => {
            this._handleVisibilityChange();
        });

        // 監聽窗口大小變化
        window.addEventListener('resize', () => {
            this._handleResize();
        });

        console.log('ChartManager: Initialized successfully');
    }

    /**
     * 設置Chart.js全局默認配置
     */
    _setGlobalDefaults() {
        // 確保Chart.js已加載
        if (typeof Chart === 'undefined') {
            console.warn('ChartManager: Chart.js not loaded');
            return;
        }

        // 設置主題配色
        const themes = {
            default: {
                font: {
                    family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
                    size: 12,
                    weight: 'normal'
                },
                color: '#2c3e50',
                borderColor: '#e0e0e0',
                gridColor: '#e0e0e0'
            },
            dark: {
                font: {
                    family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial',
                    size: 12,
                    weight: 'normal'
                },
                color: '#ecf0f1',
                borderColor: '#4a5568',
                gridColor: '#4a5568'
            }
        };

        const theme = themes[this.options.colorScheme] || themes.default;

        // 應用默認設置
        Chart.defaults.font.family = theme.font.family;
        Chart.defaults.font.size = theme.font.size;
        Chart.defaults.font.weight = theme.font.weight;
        Chart.defaults.color = theme.color;
        Chart.defaults.borderColor = theme.borderColor;

        // 響應式配置
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        Chart.defaults.plugins.legend.position = 'top';

        // 動畫配置
        Chart.defaults.animation.duration = this.options.animationDuration;

        // 保存主題到全局
        window.chartTheme = theme;
    }

    /**
     * 註冊圖表實例
     */
    registerChart(name, chartInstance, options = {}) {
        if (!chartInstance) {
            throw new Error('Chart instance is required');
        }

        const chartInfo = {
            instance: chartInstance,
            name: name,
            type: options.type || 'unknown',
            container: options.container || null,
            autoUpdate: options.autoUpdate !== false,
            dataProvider: options.dataProvider || null,
            updateInterval: options.updateInterval || this.options.refreshInterval,
            lastUpdate: null,
            isLoading: false,
            error: null
        };

        this.charts.set(name, chartInfo);

        console.log(`ChartManager: Registered chart "${name}"`);

        // 觸發註冊事件
        this._emit('chart:registered', { name, chartInfo });

        return chartInfo;
    }

    /**
     * 取消註冊圖表
     */
    unregisterChart(name) {
        const chartInfo = this.charts.get(name);
        if (!chartInfo) return false;

        // 銷毀圖表實例
        if (chartInfo.instance && typeof chartInfo.instance.destroy === 'function') {
            chartInfo.instance.destroy();
        }

        // 從註冊表中移除
        this.charts.delete(name);

        console.log(`ChartManager: Unregistered chart "${name}"`);

        // 觸發取消註冊事件
        this._emit('chart:unregistered', { name });

        return true;
    }

    /**
     * 獲取圖表實例
     */
    getChart(name) {
        const chartInfo = this.charts.get(name);
        return chartInfo ? chartInfo.instance : null;
    }

    /**
     * 更新單個圖表
     */
    async updateChart(name, data, options = {}) {
        const chartInfo = this.charts.get(name);
        if (!chartInfo) {
            throw new Error(`Chart "${name}" not found`);
        }

        // 防止重複更新
        if (chartInfo.isLoading && !options.force) {
            console.log(`ChartManager: Chart "${name}" is already loading`);
            return false;
        }

        try {
            chartInfo.isLoading = true;
            chartInfo.error = null;

            // 緩存數據
            if (data) {
                this.dataCache.set(name, {
                    data: data,
                    timestamp: Date.now()
                });
            }

            // 獲取數據（如果未提供）
            const chartData = data || (chartInfo.dataProvider
                ? await chartInfo.dataProvider()
                : null);

            if (!chartData) {
                throw new Error('No data available for update');
            }

            // 更新圖表
            if (typeof chartInfo.instance.updateChart === 'function') {
                chartInfo.instance.updateChart(chartData, options.animate);
            } else if (typeof chartInfo.instance.data !== 'undefined') {
                // 原生Chart.js更新
                chartInfo.instance.data = chartData;
                chartInfo.instance.update();
            }

            chartInfo.lastUpdate = new Date();

            console.log(`ChartManager: Updated chart "${name}"`);

            // 觸發更新事件
            this._emit('chart:updated', { name, data: chartData });

            return true;
        } catch (error) {
            console.error(`ChartManager: Failed to update chart "${name}"`, error);
            chartInfo.error = error;

            // 觸發錯誤事件
            this._emit('chart:error', { name, error });

            return false;
        } finally {
            chartInfo.isLoading = false;
        }
    }

    /**
     * 批量更新所有圖表
     */
    async updateAllCharts(dataMap = null, options = {}) {
        console.log('ChartManager: Updating all charts...');

        const promises = [];
        const results = new Map();

        // 獲取數據映射
        const dataSources = dataMap || await this._fetchAllData();

        // 並行更新所有圖表
        for (const [name, chartInfo] of this.charts) {
            if (!chartInfo.autoUpdate) continue;

            const promise = this.updateChart(name, dataSources.get(name), options)
                .then(success => {
                    results.set(name, success);
                })
                .catch(error => {
                    console.error(`Error updating chart ${name}:`, error);
                    results.set(name, false);
                });

            promises.push(promise);
        }

        // 等待所有更新完成
        await Promise.all(promises);

        const successCount = Array.from(results.values()).filter(v => v).length;
        const totalCount = results.size;

        console.log(`ChartManager: Updated ${successCount}/${totalCount} charts`);

        // 觸發批量更新事件
        this._emit('charts:batch-updated', {
            results,
            successCount,
            totalCount
        });

        return results;
    }

    /**
     * 獲取所有數據
     */
    async _fetchAllData() {
        const dataMap = new Map();

        // 從緩存獲取數據
        for (const [name, chartInfo] of this.charts) {
            const cached = this.dataCache.get(name);
            if (cached && this._isCacheValid(cached)) {
                dataMap.set(name, cached.data);
            } else if (chartInfo.dataProvider) {
                try {
                    const data = await chartInfo.dataProvider();
                    dataMap.set(name, data);
                } catch (error) {
                    console.error(`Failed to fetch data for ${name}:`, error);
                }
            }
        }

        return dataMap;
    }

    /**
     * 檢查緩存有效性
     */
    _isCacheValid(cached, ttl = 30000) { // 30秒TTL
        return Date.now() - cached.timestamp < ttl;
    }

    /**
     * 調整所有圖表大小
     */
    resizeAllCharts() {
        console.log('ChartManager: Resizing all charts...');

        for (const [name, chartInfo] of this.charts) {
            try {
                if (chartInfo.instance && typeof chartInfo.instance.resize === 'function') {
                    chartInfo.instance.resize();
                }
            } catch (error) {
                console.error(`Failed to resize chart ${name}:`, error);
            }
        }

        // 觸發調整大小事件
        this._emit('charts:resized');
    }

    /**
     * 銷毀所有圖表
     */
    destroyAllCharts() {
        console.log('ChartManager: Destroying all charts...');

        for (const [name, chartInfo] of this.charts) {
            try {
                if (chartInfo.instance && typeof chartInfo.instance.destroy === 'function') {
                    chartInfo.instance.destroy();
                }
            } catch (error) {
                console.error(`Failed to destroy chart ${name}:`, error);
            }
        }

        this.charts.clear();
        this.dataCache.clear();

        // 觸發銷毀事件
        this._emit('charts:destroyed');
    }

    /**
     * 導出所有圖表
     */
    async exportAllCharts(format = 'png') {
        const exports = new Map();

        for (const [name, chartInfo] of this.charts) {
            try {
                if (chartInfo.instance && typeof chartInfo.instance.exportImage === 'function') {
                    const imageData = chartInfo.instance.exportImage(format);
                    exports.set(name, imageData);
                }
            } catch (error) {
                console.error(`Failed to export chart ${name}:`, error);
            }
        }

        return exports;
    }

    /**
     * 啟動自動刷新
     */
    _startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(async () => {
            if (!document.hidden) {
                await this.updateAllCharts();
            }
        }, this.options.refreshInterval);

        console.log(`ChartManager: Auto refresh started (${this.options.refreshInterval}ms)`);
    }

    /**
     * 停止自動刷新
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('ChartManager: Auto refresh stopped');
        }
    }

    /**
     * 初始化WebSocket連接
     */
    _initWebSocket() {
        try {
            this.wsConnection = new WebSocket(this.options.wsEndpoint);

            this.wsConnection.onopen = () => {
                console.log('ChartManager: WebSocket connected');
                this._emit('ws:connected');
            };

            this.wsConnection.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this._handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.wsConnection.onclose = () => {
                console.log('ChartManager: WebSocket disconnected');
                this._emit('ws:disconnected');

                // 嘗試重連
                setTimeout(() => {
                    if (this.options.enableWebSocket) {
                        this._initWebSocket();
                    }
                }, 5000);
            };

            this.wsConnection.onerror = (error) => {
                console.error('WebSocket error:', error);
                this._emit('ws:error', error);
            };
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }

    /**
     * 處理WebSocket消息
     */
    _handleWebSocketMessage(data) {
        if (data.type === 'chart-update') {
            this.updateChart(data.chartName, data.data);
        } else if (data.type === 'batch-update') {
            this.updateAllCharts(data.dataMap);
        }
    }

    /**
     * 處理頁面可見性變化
     */
    _handleVisibilityChange() {
        if (document.hidden) {
            // 頁面隱藏時暫停更新
            this.stopAutoRefresh();
        } else {
            // 頁面顯示時恢復更新
            if (this.options.autoRefresh) {
                this._startAutoRefresh();
                // 立即更新一次
                this.updateAllCharts();
            }
        }
    }

    /**
     * 處理窗口大小變化
     */
    _handleResize() {
        clearTimeout(this.resizeTimer);
        this.resizeTimer = setTimeout(() => {
            this.resizeAllCharts();
        }, 250);
    }

    /**
     * 添加事件監聽器
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    /**
     * 移除事件監聽器
     */
    off(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }

    /**
     * 觸發事件
     */
    _emit(event, data = {}) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }

    /**
     * 獲取統計信息
     */
    getStatistics() {
        const stats = {
            totalCharts: this.charts.size,
            activeCharts: 0,
            loadingCharts: 0,
            errorCharts: 0,
            autoUpdateCharts: 0,
            cacheSize: this.dataCache.size,
            wsConnected: this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN
        };

        this.charts.forEach(chartInfo => {
            if (chartInfo.instance) stats.activeCharts++;
            if (chartInfo.isLoading) stats.loadingCharts++;
            if (chartInfo.error) stats.errorCharts++;
            if (chartInfo.autoUpdate) stats.autoUpdateCharts++;
        });

        return stats;
    }

    /**
     * 銷毀管理器
     */
    destroy() {
        console.log('ChartManager: Destroying...');

        // 停止自動刷新
        this.stopAutoRefresh();

        // 關閉WebSocket連接
        if (this.wsConnection) {
            this.wsConnection.close();
            this.wsConnection = null;
        }

        // 銷毀所有圖表
        this.destroyAllCharts();

        // 清理事件監聽器
        this.eventListeners.clear();

        console.log('ChartManager: Destroyed');
    }
}

// 創建全局圖表管理器實例
window.chartManager = new ChartManager({
    autoRefresh: true,
    refreshInterval: 10000,
    enableWebSocket: false, // 可以在需要時啟用
    colorScheme: 'default'
});

// 在窗口卸載時銷毀管理器
window.addEventListener('beforeunload', () => {
    if (window.chartManager) {
        window.chartManager.destroy();
    }
});