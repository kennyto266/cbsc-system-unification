/**
 * Dashboard Main Logic - 主要邏輯模塊
 * 個人策略管理Dashboard的核心功能實現
 * 負責數據管理、狀態控制、UI更新和自動刷新
 */

/**
 * Main Dashboard Class
 */
class Dashboard {
    constructor() {
        // Data storage
        this.strategies = new Map(); // StrategyPerformance instances
        this.configurations = new Map(); // StrategyConfig instances
        this.macroData = null;

        // State management
        this.isLoading = false;
        this.lastUpdateTime = null;
        this.error = null;
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;

        // Configuration
        this.config = {
            refreshInterval: 10000, // 10 seconds
            retryAttempts: 3,
            retryDelay: 2000,
            maxRetries: 5
        };

        // Event listeners
        this.eventListeners = new Map();

        // Performance metrics
        this.metrics = {
            totalStrategies: 0,
            activeStrategies: 0,
            averageReturn: 0,
            totalReturn: 0,
            bestPerformer: null,
            worstPerformer: null
        };

        // Initialize
        this.init();
    }

    /**
     * Initialize dashboard
     */
    async init() {
        try {
            console.log('Initializing Strategy Dashboard...');

            // Set up error handlers
            this.setupErrorHandlers();

            // Load initial data
            await this.loadInitialData();

            // Set up auto-refresh
            this.setupAutoRefresh();

            // Set up event listeners
            this.setupEventListeners();

            console.log('Dashboard initialized successfully');
            this.emit('initialized');

        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.setError(error);
            this.emit('error', error);
        }
    }

    /**
     * Load initial data from API
     */
    async loadInitialData() {
        this.setLoading(true);
        this.clearError();

        try {
            console.log('Loading initial data...');

            // Load data in parallel
            const [performanceData, configData, macroData] = await Promise.allSettled([
                this.retryOperation(() => strategyAPI.getStrategyPerformance()),
                this.retryOperation(() => strategyAPI.getStrategyList()),
                this.retryOperation(() => strategyAPI.getMacroData()).catch(() => null)
            ]);

            // Process results
            if (performanceData.status === 'fulfilled') {
                this.processPerformanceData(performanceData.value);
            } else {
                console.error('Failed to load performance data:', performanceData.reason);
            }

            if (configData.status === 'fulfilled') {
                this.processConfigData(configData.value);
            } else {
                console.error('Failed to load config data:', configData.reason);
            }

            if (macroData.status === 'fulfilled' && macroData.value) {
                this.macroData = macroData.value;
                console.log('Macro data loaded:', this.macroData);
            }

            // Update metrics
            this.updateMetrics();

            // Update last update time
            this.lastUpdateTime = new Date();

            console.log('Initial data loaded successfully');
            this.emit('dataLoaded');

        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.setError(error);
            throw error;
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * Process performance data
     * @private
     */
    processPerformanceData(data) {
        if (!Array.isArray(data)) {
            console.warn('Performance data is not an array:', data);
            return;
        }

        this.strategies.clear();

        data.forEach(item => {
            try {
                const strategy = new window.StrategyPerformance(
                    item.name,
                    item.sharpeRatio,
                    item.maxDrawdown,
                    item.totalReturn,
                    item.winRate,
                    item.status
                );

                // Update additional properties
                if (item.annualReturn) strategy.annualReturn = item.annualReturn;
                if (item.profitFactor) strategy.profitFactor = item.profitFactor;
                if (item.calmarRatio) strategy.calmarRatio = item.calmarRatio;
                if (item.totalTrades) strategy.totalTrades = item.totalTrades;
                if (item.profitTrades) strategy.profitTrades = item.profitTrades;

                this.strategies.set(item.name, strategy);

            } catch (error) {
                console.error(`Failed to process strategy performance for ${item.name}:`, error);
            }
        });

        console.log(`Processed ${this.strategies.size} strategy performance records`);
    }

    /**
     * Process configuration data
     * @private
     */
    processConfigData(data) {
        if (!Array.isArray(data)) {
            console.warn('Configuration data is not an array:', data);
            return;
        }

        this.configurations.clear();

        data.forEach(item => {
            try {
                const config = new window.StrategyConfig(
                    item.name,
                    item.enabled,
                    item.parameters,
                    item.description
                );

                // Update additional properties
                if (item.strategyType) config.strategyType = item.strategyType;
                if (item.category) config.category = item.category;
                if (item.riskLevel) config.riskLevel = item.riskLevel;

                this.configurations.set(item.name, config);

            } catch (error) {
                console.error(`Failed to process strategy config for ${item.name}:`, error);
            }
        });

        console.log(`Processed ${this.configurations.size} strategy configurations`);
    }

    /**
     * Refresh all data
     */
    async refreshData() {
        if (this.isLoading) {
            console.log('Refresh skipped: already loading');
            return;
        }

        console.log('Refreshing dashboard data...');

        try {
            await this.loadInitialData();
            this.emit('refreshed');
        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.emit('refreshError', error);
        }
    }

    /**
     * Toggle strategy enabled/disabled status
     * @param {string} strategyName - Strategy name
     * @returns {Promise<boolean>} New status
     */
    async toggleStrategy(strategyName) {
        try {
            console.log(`Toggling strategy: ${strategyName}`);

            // Update optimistically
            const config = this.configurations.get(strategyName);
            if (config) {
                const newStatus = config.toggle();
                this.emit('strategyToggled', { name: strategyName, enabled: newStatus });
            }

            // Call API
            const updatedConfig = await this.retryOperation(() =>
                strategyAPI.toggleStrategy(strategyName)
            );

            // Update with server response
            if (updatedConfig) {
                this.configurations.set(strategyName, new window.StrategyConfig(
                    updatedConfig.name,
                    updatedConfig.enabled,
                    updatedConfig.parameters,
                    updatedConfig.description
                ));

                // Update corresponding performance data
                const performance = this.strategies.get(strategyName);
                if (performance) {
                    performance.status = updatedConfig.enabled ? 'enabled' : 'disabled';
                }

                console.log(`Strategy ${strategyName} toggled successfully`);
                this.emit('strategyUpdated', { name: strategyName, config: updatedConfig });
            }

            return updatedConfig ? updatedConfig.enabled : false;

        } catch (error) {
            console.error(`Failed to toggle strategy ${strategyName}:`, error);

            // Revert optimistic update
            const config = this.configurations.get(strategyName);
            if (config) {
                config.toggle();
                this.emit('strategyToggleFailed', { name: strategyName, error });
            }

            throw error;
        }
    }

    /**
     * Get strategy details
     * @param {string} strategyName - Strategy name
     * @returns {Promise<Object>} Strategy details
     */
    async getStrategyDetails(strategyName) {
        try {
            const details = await this.retryOperation(() =>
                strategyAPI.getStrategyDetails(strategyName)
            );

            console.log(`Retrieved details for strategy: ${strategyName}`);
            return details;

        } catch (error) {
            console.error(`Failed to get strategy details for ${strategyName}:`, error);
            throw error;
        }
    }

    /**
     * Update performance metrics
     * @private
     */
    updateMetrics() {
        const strategies = Array.from(this.strategies.values());

        if (strategies.length === 0) {
            this.metrics = {
                totalStrategies: 0,
                activeStrategies: 0,
                averageReturn: 0,
                totalReturn: 0,
                bestPerformer: null,
                worstPerformer: null
            };
            return;
        }

        const activeStrategies = strategies.filter(s => s.status === 'enabled' || s.status === 'active');
        const returns = strategies.map(s => s.totalReturn);
        const bestPerformer = strategies.reduce((best, current) =>
            current.totalReturn > best.totalReturn ? current : best
        );
        const worstPerformer = strategies.reduce((worst, current) =>
            current.totalReturn < worst.totalReturn ? current : worst
        );

        this.metrics = {
            totalStrategies: strategies.length,
            activeStrategies: activeStrategies.length,
            averageReturn: returns.reduce((sum, r) => sum + r, 0) / returns.length,
            totalReturn: returns.reduce((sum, r) => sum + r, 0),
            bestPerformer: bestPerformer,
            worstPerformer: worstPerformer
        };

        console.log('Updated metrics:', this.metrics);
        this.emit('metricsUpdated', this.metrics);
    }

    /**
     * Setup auto-refresh
     * @private
     */
    setupAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => {
                this.refreshData();
            }, this.config.refreshInterval);

            console.log(`Auto-refresh enabled: ${this.config.refreshInterval}ms`);
        }
    }

    /**
     * Setup event listeners
     * @private
     */
    setupEventListeners() {
        // Listen for visibility changes to pause/resume refresh
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoRefresh();
            } else {
                this.resumeAutoRefresh();
            }
        });

        // Listen for online/offline events
        window.addEventListener('online', () => {
            console.log('Network online - resuming operations');
            this.refreshData();
        });

        window.addEventListener('offline', () => {
            console.log('Network offline - pausing operations');
            this.setError(new Error('Network connection lost'));
        });
    }

    /**
     * Setup error handlers
     * @private
     */
    setupErrorHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            this.setError(event.error);
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.setError(event.reason);
        });
    }

    /**
     * Retry operation with exponential backoff
     * @private
     */
    async retryOperation(operation, attempt = 1) {
        try {
            return await operation();
        } catch (error) {
            if (attempt < this.config.maxRetries && this.shouldRetry(error)) {
                const delay = this.config.retryDelay * Math.pow(2, attempt - 1);
                console.log(`Retrying operation (attempt ${attempt + 1}/${this.config.maxRetries}) after ${delay}ms`);
                await new Promise(resolve => setTimeout(resolve, delay));
                return this.retryOperation(operation, attempt + 1);
            }
            throw error;
        }
    }

    /**
     * Determine if error should be retried
     * @private
     */
    shouldRetry(error) {
        // Don't retry on client errors (4xx) or abort errors
        if (error.status >= 400 && error.status < 500) return false;
        if (error.name === 'AbortError') return false;

        // Retry on network errors and server errors (5xx)
        return true;
    }

    /**
     * Event emitter methods
     */
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    emit(event, data) {
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
     * State management methods
     */
    setLoading(loading) {
        this.isLoading = loading;
        this.emit('loadingChanged', loading);
    }

    setError(error) {
        this.error = error;
        this.emit('errorChanged', error);
    }

    clearError() {
        this.error = null;
        this.emit('errorCleared');
    }

    /**
     * Auto-refresh control
     */
    pauseAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
        this.emit('autoRefreshPaused');
    }

    resumeAutoRefresh() {
        this.setupAutoRefresh();
        this.emit('autoRefreshResumed');
    }

    setAutoRefresh(enabled) {
        this.autoRefreshEnabled = enabled;
        if (enabled) {
            this.setupAutoRefresh();
        } else {
            this.pauseAutoRefresh();
        }
        this.emit('autoRefreshChanged', enabled);
    }

    /**
     * Getters for data access
     */
    getStrategies() {
        return Array.from(this.strategies.values());
    }

    getConfigurations() {
        return Array.from(this.configurations.values());
    }

    getStrategy(name) {
        return this.strategies.get(name);
    }

    getConfiguration(name) {
        return this.configurations.get(name);
    }

    getMetrics() {
        return { ...this.metrics };
    }

    getMacroData() {
        return this.macroData;
    }

    getStatus() {
        return {
            isLoading: this.isLoading,
            error: this.error,
            lastUpdateTime: this.lastUpdateTime,
            autoRefreshEnabled: this.autoRefreshEnabled
        };
    }

    /**
     * Cleanup method
     */
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.eventListeners.clear();
        this.strategies.clear();
        this.configurations.clear();
        console.log('Dashboard destroyed');
    }
}

/**
 * Create global dashboard instance
 */
window.dashboard = new Dashboard();

/**
 * Export for module usage
 */
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Dashboard;
}