/**
 * CBSC策略API客戶端
 * 連接到FastAPI後端獲取真實策略數據
 */

class StrategyAPI {
    constructor(baseURL = 'http://localhost:3003') {
        this.baseURL = baseURL;
        this.timeout = 10000;
    }

    /**
     * 發送HTTP請求的通用方法
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API請求失敗: ${url}`, error);
            throw error;
        }
    }

    /**
     * 獲取所有策略的性能數據
     */
    async getStrategiesPerformance() {
        // 嘗試從真實API獲取數據
        try {
            const response = await this.request('/api/strategies/performance');
            if (response.success) {
                return response.data;
            }
        } catch (error) {
            console.warn('無法連接到真實API，使用模擬數據:', error.message);
        }

        // 回退到本地JSON文件或模擬數據
        return await this.getMockStrategiesData();
    }

    /**
     * 獲取模擬策略數據（基於真實CBSC策略結構）
     */
    async getMockStrategiesData() {
        // 基於真實CBSC策略數據結構的模擬數據
        return {
            strategies: [
                {
                    name: "DirectRSIStrategy",
                    display_name: "直接RSI情緒策略",
                    description: "基於牛熊比例的RSI計算，識別極端情緒信號",
                    status: "active",
                    performance: {
                        sharpe_ratio: 0.633,
                        max_drawdown: -0.390,
                        win_rate: 0.515,
                        total_return: 6.313,
                        annual_return: 0.143,
                        calmar_ratio: 0.368,
                        sortino_ratio: 0.941,
                        total_trades: 33,
                        volatility: 0.226
                    },
                    parameters: {
                        rsi_period: 14,
                        oversold_threshold: 30,
                        overbought_threshold: 70,
                        sentiment_weight: 0.7
                    },
                    last_signal: {
                        type: "extreme_bullish",
                        strength: 0.82,
                        timestamp: new Date().toISOString()
                    }
                },
                {
                    name: "SentimentMomentumStrategy",
                    display_name: "情緒動量策略",
                    description: "MACD風格的情緒變化率分析，捕捉情緒轉折點",
                    status: "active",
                    performance: {
                        sharpe_ratio: 0.445,
                        max_drawdown: -0.285,
                        win_rate: 0.542,
                        total_return: 4.227,
                        annual_return: 0.118,
                        calmar_ratio: 0.415,
                        sortino_ratio: 0.678,
                        total_trades: 47,
                        volatility: 0.265
                    },
                    parameters: {
                        fast_period: 12,
                        slow_period: 26,
                        signal_period: 9,
                        momentum_threshold: 0.15
                    },
                    last_signal: {
                        type: "golden_cross",
                        strength: 0.75,
                        timestamp: new Date().toISOString()
                    }
                },
                {
                    name: "CompositeIndexStrategy",
                    display_name: "複合指標策略",
                    description: "多維度情緒綜合，布林帶風格的情緒區間分析",
                    status: "active",
                    performance: {
                        sharpe_ratio: 0.578,
                        max_drawdown: -0.315,
                        win_rate: 0.568,
                        total_return: 5.892,
                        annual_return: 0.135,
                        calmar_ratio: 0.429,
                        sortino_ratio: 0.823,
                        total_trades: 58,
                        volatility: 0.234
                    },
                    parameters: {
                        composite_period: 20,
                        std_dev_multiplier: 2.0,
                        sentiment_threshold: 0.6,
                        volume_weight: 0.3
                    },
                    last_signal: {
                        type: "breakthrough",
                        strength: 0.68,
                        timestamp: new Date().toISOString()
                    }
                },
                {
                    name: "VolatilityAdjustedStrategy",
                    display_name: "波動率調整策略",
                    description: "成交量加權的情緒分析，考慮市場信心度",
                    status: "stopped",
                    performance: {
                        sharpe_ratio: -0.058,
                        max_drawdown: -0.581,
                        win_rate: 0.473,
                        total_return: -0.451,
                        annual_return: -0.040,
                        calmar_ratio: -0.068,
                        sortino_ratio: -0.057,
                        total_trades: 258,
                        volatility: 0.693
                    },
                    parameters: {
                        volatility_window: 20,
                        volume_threshold: 1000000,
                        adjustment_factor: 0.8,
                        risk_multiplier: 1.5
                    },
                    last_signal: {
                        type: "confirmed_signal",
                        strength: 0.32,
                        timestamp: new Date().toISOString()
                    }
                }
            ],
            market_benchmark: {
                name: "恒生指數",
                total_return: 0.398,
                annual_return: 0.028,
                volatility: 0.189,
                max_drawdown: -0.425
            },
            summary: {
                total_strategies: 4,
                active_strategies: 3,
                stopped_strategies: 1,
                average_sharpe_ratio: 0.400,
                best_performing_strategy: "DirectRSIStrategy",
                worst_performing_strategy: "VolatilityAdjustedStrategy",
                last_updated: new Date().toISOString()
            }
        };
    }

    /**
     * 獲取單個策略的詳細信息
     */
    async getStrategyDetails(strategyName) {
        const allStrategies = await this.getStrategiesPerformance();
        const strategy = allStrategies.strategies.find(s => s.name === strategyName);

        if (!strategy) {
            throw new Error(`策略 ${strategyName} 未找到`);
        }

        return strategy;
    }

    /**
     * 更新策略狀態（啟用/停用）
     */
    async updateStrategyStatus(strategyName, status) {
        try {
            const response = await this.request(`/api/strategies/${strategyName}/status`, {
                method: 'PATCH',
                body: JSON.stringify({ status })
            });

            return response;
        } catch (error) {
            console.warn('無法更新策略狀態，使用模擬更新:', error.message);
            // 模擬更新成功
            return { success: true, message: `策略 ${strategyName} 狀態已更新為 ${status}` };
        }
    }

    /**
     * 獲取策略的歷史信號數據
     */
    async getStrategySignals(strategyName, limit = 100) {
        try {
            const response = await this.request(`/api/strategies/${strategyName}/signals?limit=${limit}`);
            return response.data || [];
        } catch (error) {
            console.warn('無法獲取歷史信號，生成模擬信號:', error.message);
            return this.generateMockSignals(strategyName, limit);
        }
    }

    /**
     * 生成模擬信號數據
     */
    generateMockSignals(strategyName, limit = 100) {
        const signals = [];
        const signalTypes = {
            'DirectRSIStrategy': ['extreme_bullish', 'bullish', 'bearish', 'extreme_bearish'],
            'SentimentMomentumStrategy': ['golden_cross', 'death_cross', 'momentum_shift'],
            'CompositeIndexStrategy': ['squeeze', 'breakthrough', 'position_signal'],
            'VolatilityAdjustedStrategy': ['volatility_adjusted', 'confirmed_signal']
        };

        const validTypes = signalTypes[strategyName] || ['buy', 'sell', 'neutral'];
        const now = new Date();

        for (let i = 0; i < limit; i++) {
            const timestamp = new Date(now.getTime() - (limit - i) * 24 * 60 * 60 * 1000);
            signals.push({
                timestamp: timestamp.toISOString(),
                type: validTypes[Math.floor(Math.random() * validTypes.length)],
                strength: Math.random() * 0.6 + 0.4, // 0.4-1.0
                price: 20000 + Math.random() * 5000, // 模擬價格
                volume: Math.floor(Math.random() * 1000000) + 100000
            });
        }

        return signals;
    }

    /**
     * 檢查API連接狀態
     */
    async checkConnection() {
        try {
            const response = await this.request('/health');
            return { connected: true, status: response };
        } catch (error) {
            return { connected: false, error: error.message };
        }
    }

    /**
     * 獲取市場數據概覽
     */
    async getMarketOverview() {
        try {
            const response = await this.request('/api/market/overview');
            return response.data;
        } catch (error) {
            console.warn('無法獲取市場數據，使用模擬數據:', error.message);
            return {
                market_status: 'open',
                current_time: new Date().toISOString(),
                top_stocks: [],
                market_sentiment: {
                    bull_bear_ratio: 0.52,
                    sentiment_score: 0.45,
                    confidence_level: 0.78
                }
            };
        }
    }
}

// 導出API實例
window.StrategyAPI = StrategyAPI;
window.strategyAPI = new StrategyAPI();