/**
 * Enhanced Dashboard Integration
 * Integrates enhanced components with the main dashboard
 * Connects API data to UI components
 */

// Enhanced Dashboard Manager
class EnhancedDashboardManager {
    constructor() {
        this.enhancedStrategyList = null;
        this.performanceCards = null;
        this.refreshInterval = null;
        this.isInitialized = false;
    }

    /**
     * Initialize enhanced dashboard
     */
    async initialize() {
        console.log('🚀 Initializing Enhanced Dashboard...');

        try {
            // Initialize components
            this.initializeComponents();

            // Load initial data
            await this.loadInitialData();

            // Start auto-refresh
            this.startAutoRefresh();

            this.isInitialized = true;
            console.log('✅ Enhanced Dashboard initialized successfully');

            if (window.dashboard) {
                window.dashboard.showMessage('增強版組件已加載', 'success');
            }
        } catch (error) {
            console.error('❌ Failed to initialize Enhanced Dashboard:', error);
            if (window.dashboard) {
                window.dashboard.showMessage('組件初始化失敗', 'error');
            }
        }
    }

    /**
     * Initialize components
     */
    initializeComponents() {
        // Initialize enhanced strategy list
        this.enhancedStrategyList = new EnhancedStrategyList('strategyListContainer');

        // Initialize performance cards
        this.performanceCards = new PerformanceCards('performanceMetricsContainer');

        // Make components globally accessible
        window.enhancedStrategyList = this.enhancedStrategyList;
        window.enhancedPerformanceCards = this.performanceCards;
    }

    /**
     * Load initial data from API
     */
    async loadInitialData() {
        if (!window.strategyAPI) {
            console.warn('Strategy API not available, using mock data');
            this.loadMockData();
            return;
        }

        try {
            // Show loading
            this.enhancedStrategyList.showLoading();

            // Fetch strategy data
            const [performanceData, listData] = await Promise.all([
                window.strategyAPI.getStrategyPerformance(),
                window.strategyAPI.getStrategyList()
            ]);

            // Merge data
            const mergedData = this.mergeStrategyData(performanceData, listData);

            // Update components
            this.updateComponents(mergedData);

            // Hide loading
            this.enhancedStrategyList.hideLoading();
        } catch (error) {
            console.error('Failed to load strategy data:', error);
            this.enhancedStrategyList.hideLoading();

            // Use mock data as fallback
            this.loadMockData();
        }
    }

    /**
     * Load mock data for demonstration
     */
    loadMockData() {
        console.log('Using mock strategy data...');

        const mockData = [
            {
                name: 'DirectRSIStrategy',
                displayName: '直接RSI情緒策略',
                description: '基於牛熊比例的RSI情緒分析策略',
                status: 'active',
                sharpeRatio: 1.234,
                maxDrawdown: -0.152,
                totalReturn: 0.256,
                winRate: 0.653,
                totalTrades: 142,
                profitTrades: 93,
                lastSignal: {
                    type: 'buy',
                    strength: 0.78,
                    timestamp: new Date().toISOString()
                }
            },
            {
                name: 'SentimentMomentumStrategy',
                displayName: '情緒動量策略',
                description: 'MACD風格的情緒變化率分析',
                status: 'active',
                sharpeRatio: 0.987,
                maxDrawdown: -0.189,
                totalReturn: 0.178,
                winRate: 0.582,
                totalTrades: 238,
                profitTrades: 138,
                lastSignal: {
                    type: 'hold',
                    strength: 0.45,
                    timestamp: new Date().toISOString()
                }
            },
            {
                name: 'CompositeIndexStrategy',
                displayName: '複合指標策略',
                description: '多維度情緒布林帶分析',
                status: 'disabled',
                sharpeRatio: 0.756,
                maxDrawdown: -0.221,
                totalReturn: 0.089,
                winRate: 0.523,
                totalTrades: 89,
                profitTrades: 46,
                lastSignal: {
                    type: 'sell',
                    strength: 0.62,
                    timestamp: new Date(Date.now() - 86400000).toISOString()
                }
            },
            {
                name: 'VolatilityAdjustedStrategy',
                displayName: '波動率調整策略',
                description: '成交量加權的情緒分析',
                status: 'active',
                sharpeRatio: 1.445,
                maxDrawdown: -0.134,
                totalReturn: 0.312,
                winRate: 0.712,
                totalTrades: 198,
                profitTrades: 141,
                lastSignal: {
                    type: 'buy',
                    strength: 0.83,
                    timestamp: new Date().toISOString()
                }
            }
        ];

        this.updateComponents(mockData);
    }

    /**
     * Merge performance and list data
     */
    mergeStrategyData(performanceData, listData) {
        const strategyMap = new Map();

        // Add performance data
        performanceData.forEach(strategy => {
            strategyMap.set(strategy.name, strategy);
        });

        // Add/merge list data
        listData.forEach(strategy => {
            if (strategyMap.has(strategy.name)) {
                Object.assign(strategyMap.get(strategy.name), strategy);
            } else {
                strategyMap.set(strategy.name, strategy);
            }
        });

        return Array.from(strategyMap.values());
    }

    /**
     * Update all components with new data
     */
    updateComponents(data) {
        if (this.enhancedStrategyList) {
            this.enhancedStrategyList.updateStrategies(data);
        }

        if (this.performanceCards) {
            this.performanceCards.updateMetrics(data);
        }
    }

    /**
     * Start auto-refresh
     */
    startAutoRefresh() {
        // Clear existing interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        // Set new interval (10 seconds)
        this.refreshInterval = setInterval(async () => {
            try {
                await this.refreshData();
            } catch (error) {
                console.error('Auto-refresh failed:', error);
            }
        }, 10000);
    }

    /**
     * Refresh data
     */
    async refreshData() {
        if (!window.strategyAPI) {
            console.warn('API not available, skipping refresh');
            return;
        }

        try {
            const [performanceData, listData] = await Promise.all([
                window.strategyAPI.getStrategyPerformance(),
                window.strategyAPI.getStrategyList()
            ]);

            const mergedData = this.mergeStrategyData(performanceData, listData);
            this.updateComponents(mergedData);

            console.log('📊 Data refreshed successfully');
        } catch (error) {
            console.error('Failed to refresh data:', error);
        }
    }

    /**
     * Stop auto-refresh
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Handle strategy toggle
     */
    async handleStrategyToggle(strategyName) {
        if (!window.strategyAPI) {
            console.warn('API not available');
            return;
        }

        try {
            const result = await window.strategyAPI.toggleStrategy(strategyName);
            await this.refreshData();

            if (window.dashboard) {
                window.dashboard.showMessage(
                    `策略 ${strategyName} 已${result.enabled ? '啟用' : '停用'}`,
                    'success'
                );
            }
        } catch (error) {
            console.error('Failed to toggle strategy:', error);
            if (window.dashboard) {
                window.dashboard.showMessage('切換策略失敗', 'error');
            }
        }
    }

    /**
     * Get strategy details
     */
    async getStrategyDetails(strategyName) {
        if (!window.strategyAPI) {
            console.warn('API not available');
            return null;
        }

        try {
            return await window.strategyAPI.getStrategyDetails(strategyName);
        } catch (error) {
            console.error('Failed to get strategy details:', error);
            return null;
        }
    }
}

// Initialize enhanced dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Wait for basic dashboard to initialize
    setTimeout(() => {
        if (window.dashboard && window.dashboard.isInitialized) {
            window.enhancedDashboard = new EnhancedDashboardManager();
            window.enhancedDashboard.initialize();
        } else {
            console.warn('Basic dashboard not initialized, retrying...');
            // Retry after delay
            setTimeout(() => {
                if (window.dashboard) {
                    window.enhancedDashboard = new EnhancedDashboardManager();
                    window.enhancedDashboard.initialize();
                } else {
                    console.error('Cannot initialize enhanced dashboard');
                }
            }, 2000);
        }
    }, 1000);
});

// Export for global access
window.EnhancedDashboardManager = EnhancedDashboardManager;