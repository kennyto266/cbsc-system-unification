/**
 * 个人策略管理Dashboard - 增强Sharpe比率分析图
 * Personal Strategy Management Dashboard - Enhanced Sharpe Ratio Analysis Chart
 */

import { LineChart, ChartUtils } from './chart.js';
import { CHART_CONFIG, API_CONFIG, BENCHMARK_TYPES, SHARPE_CONFIG } from './constants.js';
import { sharpeAnalysisService } from './sharpe-analysis-service.js';

/**
 * Sharpe比率图类
 */
class SharpeRatioChart extends LineChart {
    constructor(canvasId, options = {}) {
        super(canvasId, {
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#ddd',
                    borderWidth: 1,
                    cornerRadius: 8,
                    padding: 12,
                    callbacks: {
                        title: (context) => {
                            return `日期: ${context[0].label}`;
                        },
                        label: (context) => {
                            const label = context.dataset.label || 'Sharpe比率';
                            const value = context.parsed.y;
                            let extraInfo = '';

                            // Add benchmark comparison info if available
                            if (context.dataset.benchmarkComparison) {
                                const comparison = context.dataset.benchmarkComparison;
                                if (comparison.excessSharpe !== undefined) {
                                    extraInfo = ` (超额: ${comparison.excessSharpe.toFixed(2)})`;
                                }
                            }

                            return `${label}: ${value.toFixed(2)}${extraInfo}`;
                        },
                        afterBody: (context) => {
                            const dataset = context[0].dataset;
                            if (dataset.advancedMetrics) {
                                const metrics = dataset.advancedMetrics;
                                return [
                                    `信息比率: ${metrics.informationRatio?.toFixed(2) || 'N/A'}`,
                                    `跟踪误差: ${(metrics.trackingError * 100)?.toFixed(2) || 'N/A'}%`,
                                    `胜率: ${(metrics.winRate * 100)?.toFixed(1) || 'N/A'}%`
                                ];
                            }
                            return [];
                        }
                    }
                },
                zoom: {
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x',
                    },
                    pan: {
                        enabled: true,
                        mode: 'x',
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        displayFormats: {
                            day: 'MM/DD',
                            week: 'MM/DD',
                            month: 'YYYY-MM',
                            quarter: 'YYYY-[Q]Q',
                            year: 'YYYY'
                        }
                    },
                    grid: {
                        drawBorder: false,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    position: 'right',
                    grid: {
                        drawBorder: false,
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: (value) => {
                            return value.toFixed(1);
                        },
                        font: {
                            size: 11
                        }
                    },
                    suggestedMin: -1,
                    suggestedMax: 4
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            elements: {
                line: {
                    tension: 0.2
                }
            },
            ...options
        });

        // Enhanced properties for advanced Sharpe analysis
        this.strategies = new Map();
        this.benchmarks = new Map();
        this.rollingPeriod = SHARPE_CONFIG.DEFAULT_WINDOW;
        this.benchmarkLevel = 1.0;
        this.selectedBenchmarks = ['HSI'];
        this.advancedMetrics = new Map();
        this.distributionData = new Map();
        this.isLoading = false;
        this.analysisOptions = {
            riskFreeRate: SHARPE_CONFIG.DEFAULT_RISK_FREE_RATE,
            windowSize: SHARPE_CONFIG.DEFAULT_WINDOW,
            bootstrapSamples: SHARPE_CONFIG.BOOTSTRAP_SAMPLES,
            confidenceLevel: 0.95
        };
    }

    /**
     * 设置滚动周期
     * @param {number} days - 滚动天数
     */
    setRollingPeriod(days) {
        this.rollingPeriod = days;
        this.updateChart();
    }

    /**
     * 设置基准
     * @param {number} benchmark - 基准Sharpe比率
     */
    setBenchmark(benchmark) {
        this.benchmarkLevel = benchmark;
        this.updateAnnotation();
        this.update();
    }

    /**
     * 设置选择的基准
     * @param {Array} benchmarkNames - 基准名称数组
     */
    async setSelectedBenchmarks(benchmarkNames) {
        this.selectedBenchmarks = benchmarkNames;

        // Re-run analysis for all strategies with new benchmarks
        const analysisPromises = [];
        this.strategies.forEach((strategyInfo, strategyId) => {
            analysisPromises.push(this.runAdvancedAnalysis(strategyId));
        });

        try {
            await Promise.all(analysisPromises);
        } catch (error) {
            console.error('基准更新分析失败:', error);
        }
    }

    /**
     * 设置分析选项
     * @param {Object} options - 分析选项
     */
    setAnalysisOptions(options) {
        this.analysisOptions = { ...this.analysisOptions, ...options };

        // Re-run analysis with new options
        this.strategies.forEach((strategyInfo, strategyId) => {
            this.runAdvancedAnalysis(strategyId);
        });
    }

    /**
     * 运行高级Sharpe分析
     * @param {string} strategyId - 策略ID
     * @returns {Promise<Object>} 分析结果
     */
    async runAdvancedAnalysis(strategyId) {
        const strategyInfo = this.strategies.get(strategyId);
        if (!strategyInfo || !strategyInfo.originalData) {
            console.warn(`策略 ${strategyId} 数据不完整`);
            return null;
        }

        try {
            this.setLoading(true);

            // Extract returns from original data
            const returns = strategyInfo.originalData.map(d => d.daily_return || d.return || 0);

            // Run comprehensive analysis
            const analysisResult = await sharpeAnalysisService.comprehensiveAnalysis(returns, {
                benchmarkNames: this.selectedBenchmarks,
                riskFreeRate: this.analysisOptions.riskFreeRate,
                window: this.analysisOptions.windowSize,
                bootstrapSamples: this.analysisOptions.bootstrapSamples,
                confidenceLevel: this.analysisOptions.confidenceLevel
            });

            // Store advanced metrics
            this.advancedMetrics.set(strategyId, {
                basic: analysisResult.basic,
                benchmark: analysisResult.benchmark,
                rolling: analysisResult.rolling,
                distribution: analysisResult.distribution,
                timestamp: analysisResult.timestamp
            });

            // Update strategy data with new analysis
            this.updateStrategyWithAdvancedAnalysis(strategyId, analysisResult);

            // Add benchmark datasets
            await this.updateBenchmarkDatasets(analysisResult.benchmark);

            this.setLoading(false);
            return analysisResult;

        } catch (error) {
            console.error(`策略 ${strategyId} 高级分析失败:`, error);
            this.setLoading(false);
            throw error;
        }
    }

    /**
     * 使用高级分析结果更新策略数据
     * @param {string} strategyId - 策略ID
     * @param {Object} analysisResult - 分析结果
     */
    updateStrategyWithAdvancedAnalysis(strategyId, analysisResult) {
        const strategyInfo = this.strategies.get(strategyId);
        if (!strategyInfo) return;

        // Update rolling Sharpe data
        if (analysisResult.rolling && analysisResult.rolling.rolling_sharpe) {
            const rollingData = analysisResult.rolling.rolling_sharpe.map(item => ({
                x: item.date || item.timestamp,
                y: item.sharpe_ratio
            }));

            strategyInfo.dataset.data = rollingData;
            strategyInfo.dataset.advancedMetrics = {
                informationRatio: analysisResult.benchmark?.comparisons?.[this.selectedBenchmarks[0]]?.information_ratio,
                trackingError: analysisResult.benchmark?.comparisons?.[this.selectedBenchmarks[0]]?.tracking_error,
                winRate: analysisResult.benchmark?.comparisons?.[this.selectedBenchmarks[0]]?.win_rate
            };
        }

        // Update stats
        if (analysisResult.basic && analysisResult.basic.strategy_metrics) {
            const metrics = analysisResult.basic.strategy_metrics;
            strategyInfo.stats = {
                current: metrics.sharpe_ratio || 0,
                average: metrics.sharpe_ratio || 0, // For now, use current as average
                min: metrics.min_sharpe || 0,
                max: metrics.max_sharpe || 0,
                stdDev: metrics.sharpe_std || 0,
                above1: 0, // Would need distribution data
                above2: 0,
                below0: 0
            };
        }

        this.updateChart();
    }

    /**
     * 更新基准数据集
     * @param {Object} benchmarkData - 基准数据
     */
    async updateBenchmarkDatasets(benchmarkData) {
        if (!benchmarkData || !benchmarkData.comparisons) return;

        const existingDatasets = this.chart.data.datasets.filter(ds => ds.type === 'benchmark');
        const newDatasets = [];

        Object.entries(benchmarkData.comparisons).forEach(([benchmarkName, comparison]) => {
            const color = SHARPE_CONFIG.BENCHMARK_COLORS[benchmarkName] || '#999999';

            // Create benchmark dataset
            const benchmarkDataset = {
                label: `${benchmarkName} 基准`,
                data: [], // Would need time series data for benchmarks
                borderColor: color,
                backgroundColor: ChartUtils.hexToRgba(color, 0.1),
                borderWidth: 2,
                borderDash: [5, 5],
                tension: 0.2,
                pointRadius: 0,
                pointHoverRadius: 4,
                type: 'benchmark',
                benchmarkComparison: {
                    sharpeRatio: comparison.benchmark_sharpe,
                    excessSharpe: comparison.excess_sharpe
                }
            };

            // Add constant line for benchmark Sharpe ratio
            if (comparison.benchmark_sharpe) {
                const allTimestamps = new Set();
                this.strategies.forEach(strategyInfo => {
                    strategyInfo.dataset.data.forEach(item => {
                        if (item.x) allTimestamps.add(item.x);
                    });
                });

                const sortedTimestamps = Array.from(allTimestamps).sort();
                benchmarkDataset.data = sortedTimestamps.map(timestamp => ({
                    x: timestamp,
                    y: comparison.benchmark_sharpe
                }));
            }

            newDatasets.push(benchmarkDataset);
        });

        // Remove old benchmark datasets
        existingDatasets.forEach(ds => {
            const index = this.chart.data.datasets.indexOf(ds);
            if (index > -1) {
                this.chart.data.datasets.splice(index, 1);
            }
        });

        // Add new benchmark datasets
        this.chart.data.datasets.push(...newDatasets);
    }

    /**
     * 设置加载状态
     * @param {boolean} loading - 是否加载中
     */
    setLoading(loading) {
        this.isLoading = loading;

        // Show/hide loading indicator on canvas
        if (this.chart.canvas) {
            if (loading) {
                this.chart.canvas.style.opacity = '0.6';
            } else {
                this.chart.canvas.style.opacity = '1';
            }
        }

        // Trigger loading event
        const event = new CustomEvent('sharpeChartLoading', {
            detail: { loading, chart: this }
        });
        document.dispatchEvent(event);
    }

    /**
     * 获取策略高级指标
     * @param {string} strategyId - 策略ID
     * @returns {Object|null} 高级指标
     */
    getAdvancedMetrics(strategyId) {
        return this.advancedMetrics.get(strategyId) || null;
    }

    /**
     * 获取基准对比结果
     * @param {string} strategyId - 策略ID
     * @param {string} benchmarkName - 基准名称
     * @returns {Object|null} 对比结果
     */
    getBenchmarkComparison(strategyId, benchmarkName) {
        const metrics = this.advancedMetrics.get(strategyId);
        if (!metrics || !metrics.benchmark || !metrics.benchmark.comparisons) {
            return null;
        }
        return metrics.benchmark.comparisons[benchmarkName] || null;
    }

    /**
     * 获取分布分析结果
     * @param {string} strategyId - 策略ID
     * @returns {Object|null} 分布分析
     */
    getDistributionAnalysis(strategyId) {
        const metrics = this.advancedMetrics.get(strategyId);
        if (!metrics || !metrics.distribution) {
            return null;
        }
        return metrics.distribution;
    }

    /**
     * 添加策略数据
     * @param {string} strategyId - 策略ID
     * @param {Object} strategy - 策略对象
     * @param {Array} data - 策略数据（包含收益率）
     */
    async addStrategy(strategyId, strategy, data) {
        if (!data || !Array.isArray(data) || data.length < this.rollingPeriod) {
            console.warn(`Insufficient data for Sharpe ratio calculation: ${strategyId}`);
            return;
        }

        // Calculate rolling Sharpe ratio (local calculation as fallback)
        const sharpeData = this.calculateRollingSharpe(data);

        const color = this.getStrategyColor(strategyId);
        const dataset = {
            label: strategy.name || `策略 ${strategyId}`,
            data: sharpeData,
            borderColor: color,
            backgroundColor: ChartUtils.hexToRgba(color, 0.1),
            borderWidth: 2,
            tension: 0.2,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderWidth: 2
        };

        this.strategies.set(strategyId, {
            strategy,
            dataset,
            originalData: data,
            stats: this.calculateSharpeStats(sharpeData)
        });

        this.updateChart();

        // Run advanced analysis if data is sufficient
        if (data.length >= SHARPE_CONFIG.MIN_DATA_POINTS) {
            try {
                await this.runAdvancedAnalysis(strategyId);
            } catch (error) {
                console.warn(`策略 ${strategyId} 高级分析失败，使用基础分析:`, error);
            }
        }
    }

    /**
     * 移除策略
     * @param {string} strategyId - 策略ID
     */
    removeStrategy(strategyId) {
        this.strategies.delete(strategyId);
        this.updateChart();
    }

    /**
     * 更新策略数据
     * @param {string} strategyId - 策略ID
     * @param {Array} data - 新数据
     */
    updateStrategy(strategyId, data) {
        if (!data || !Array.isArray(data) || data.length < this.rollingPeriod) {
            return;
        }

        const strategyInfo = this.strategies.get(strategyId);
        if (strategyInfo) {
            // Recalculate Sharpe ratio
            const sharpeData = this.calculateRollingSharpe(data);

            strategyInfo.originalData = data;
            strategyInfo.dataset.data = sharpeData;
            strategyInfo.stats = this.calculateSharpeStats(sharpeData);

            this.updateChart();
        }
    }

    /**
     * 计算滚动Sharpe比率
     * @param {Array} data - 收益率数据
     * @returns {Array} Sharpe比率数据
     */
    calculateRollingSharpe(data) {
        if (!data || data.length < this.rollingPeriod) {
            return [];
        }

        const sharpeData = [];

        // 需要至少rollingPeriod个数据点才开始计算
        for (let i = this.rollingPeriod - 1; i < data.length; i++) {
            const window = data.slice(i - this.rollingPeriod + 1, i + 1);
            const returns = window.map(d => d.daily_return || d.return || 0);

            // Calculate Sharpe ratio
            const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
            const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
            const stdDev = Math.sqrt(variance);

            // Annualized Sharpe ratio (assuming 252 trading days)
            const annualizedMean = mean * 252;
            const annualizedStdDev = stdDev * Math.sqrt(252);
            const sharpe = annualizedStdDev !== 0 ? annualizedMean / annualizedStdDev : 0;

            sharpeData.push({
                x: data[i].timestamp || data[i].date,
                y: sharpe
            });
        }

        return sharpeData;
    }

    /**
     * 计算Sharpe比率统计
     * @param {Array} sharpeData - Sharpe比率数据
     * @returns {Object} 统计信息
     */
    calculateSharpeStats(sharpeData) {
        if (!sharpeData || sharpeData.length === 0) {
            return {
                current: 0,
                average: 0,
                min: 0,
                max: 0,
                stdDev: 0,
                above1: 0,
                above2: 0,
                below0: 0
            };
        }

        const values = sharpeData.map(d => d.y);
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
        const stdDev = Math.sqrt(variance);

        const current = values[values.length - 1];
        const min = Math.min(...values);
        const max = Math.max(...values);

        // Count values in different ranges
        const above1 = values.filter(v => v > 1).length;
        const above2 = values.filter(v => v > 2).length;
        const below0 = values.filter(v => v < 0).length;

        return {
            current,
            average: mean,
            min,
            max,
            stdDev,
            above1,
            above2,
            below0,
            above1Percent: (above1 / values.length) * 100,
            above2Percent: (above2 / values.length) * 100,
            below0Percent: (below0 / values.length) * 100
        };
    }

    /**
     * 获取策略颜色
     * @param {string} strategyId - 策略ID
     * @returns {string} 颜色值
     */
    getStrategyColor(strategyId) {
        const colors = CHART_CONFIG.COLORS;
        const index = Array.from(this.strategies.keys()).indexOf(strategyId);
        return colors[index % colors.length];
    }

    /**
     * 更新图表
     */
    updateChart() {
        if (!this.chart) return;

        const datasets = [];

        // Add all strategies
        this.strategies.forEach((strategyInfo) => {
            datasets.push(strategyInfo.dataset);
        });

        // Update chart data
        this.chart.data.datasets = datasets;

        // Get all timestamps
        const allTimestamps = new Set();
        this.strategies.forEach((strategyInfo) => {
            strategyInfo.dataset.data.forEach(item => {
                allTimestamps.add(item.x);
            });
        });

        // Sort timestamps
        const sortedTimestamps = Array.from(allTimestamps).sort();

        // Update chart labels
        this.chart.data.labels = sortedTimestamps;

        // Update annotation
        this.updateAnnotation();

        this.update();
    }

    /**
     * 更新基准线注释
     */
    updateAnnotation() {
        if (this.chart && this.chart.options.plugins.annotation) {
            // Clear existing annotations
            this.chart.options.plugins.annotation.annotations = {};

            // Add benchmark level line
            this.chart.options.plugins.annotation.annotations.benchmarkLine = {
                type: 'line',
                yMin: this.benchmarkLevel,
                yMax: this.benchmarkLevel,
                borderColor: '#ef4444',
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                    content: `基准线 = ${this.benchmarkLevel.toFixed(1)}`,
                    enabled: true,
                    position: 'end',
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    color: '#fff',
                    padding: 4,
                    borderRadius: 4,
                    font: {
                        size: 11
                    }
                }
            };

            // Add standard Sharpe ratio levels
            const levels = [1.0, 2.0];
            const colors = ['#fbbf24', '#10b981']; // Yellow for good, green for excellent

            levels.forEach((level, index) => {
                this.chart.options.plugins.annotation.annotations[`level${level}`] = {
                    type: 'line',
                    yMin: level,
                    yMax: level,
                    borderColor: colors[index],
                    borderWidth: 1,
                    borderDash: [3, 3],
                    label: {
                        content: `Sharpe = ${level.toFixed(1)}`,
                        enabled: true,
                        position: 'start',
                        backgroundColor: colors[index] + '99',
                        color: '#fff',
                        padding: 2,
                        borderRadius: 3,
                        font: {
                            size: 9
                        }
                    }
                };
            });
        }
    }

    /**
     * 获取当前Sharpe比率
     * @param {string} strategyId - 策略ID
     * @returns {number} 当前Sharpe比率
     */
    getCurrentSharpe(strategyId) {
        const strategyInfo = this.strategies.get(strategyId);
        return strategyInfo ? strategyInfo.stats.current : 0;
    }

    /**
     * 获取平均Sharpe比率
     * @param {string} strategyId - 策略ID
     * @returns {number} 平均Sharpe比率
     */
    getAverageSharpe(strategyId) {
        const strategyInfo = this.strategies.get(strategyId);
        return strategyInfo ? strategyInfo.stats.average : 0;
    }

    /**
     * 获取Sharpe比率统计
     * @param {string} strategyId - 策略ID
     * @returns {Object} 统计信息
     */
    getSharpeStats(strategyId = null) {
        if (strategyId) {
            const strategyInfo = this.strategies.get(strategyId);
            return strategyInfo ? strategyInfo.stats : null;
        }

        // Return stats for all strategies
        const allStats = {};
        this.strategies.forEach((strategyInfo, id) => {
            allStats[id] = {
                ...strategyInfo.stats,
                name: strategyInfo.strategy.name
            };
        });

        return allStats;
    }

    /**
     * 获取表现最佳的策略
     * @param {string} metric - 评价指标 ('current', 'average', 'max')
     * @returns {Object|null} 最佳策略信息
     */
    getBestStrategy(metric = 'average') {
        let bestStrategy = null;
        let bestValue = -Infinity;

        this.strategies.forEach((strategyInfo, strategyId) => {
            const value = strategyInfo.stats[metric] || 0;
            if (value > bestValue) {
                bestValue = value;
                bestStrategy = {
                    id: strategyId,
                    name: strategyInfo.strategy.name,
                    value,
                    stats: strategyInfo.stats
                };
            }
        });

        return bestStrategy;
    }

    /**
     * 获取表现最差的策略
     * @param {string} metric - 评价指标 ('current', 'average', 'min')
     * @returns {Object|null} 最差策略信息
     */
    getWorstStrategy(metric = 'average') {
        let worstStrategy = null;
        let worstValue = Infinity;

        this.strategies.forEach((strategyInfo, strategyId) => {
            const value = strategyInfo.stats[metric] || 0;
            if (value < worstValue) {
                worstValue = value;
                worstStrategy = {
                    id: strategyId,
                    name: strategyInfo.strategy.name,
                    value,
                    stats: strategyInfo.stats
                };
            }
        });

        return worstStrategy;
    }

    /**
     * 导出Sharpe比率数据为CSV
     * @returns {string} CSV字符串
     */
    exportToCSV() {
        const headers = ['Timestamp'];
        const datasets = [];

        // Collect datasets
        this.strategies.forEach((strategyInfo, strategyId) => {
            headers.push(strategyInfo.strategy.name);
            datasets.push({
                data: strategyInfo.dataset.data,
                name: strategyInfo.strategy.name
            });
        });

        // Add benchmark line
        headers.push('Benchmark');

        // Collect all timestamps
        const allTimestamps = new Set();
        datasets.forEach(dataset => {
            dataset.data.forEach(item => {
                allTimestamps.add(item.x);
            });
        });

        const sortedTimestamps = Array.from(allTimestamps).sort();

        // Build CSV
        let csv = headers.join(',') + '\n';

        sortedTimestamps.forEach(timestamp => {
            const row = [timestamp];
            datasets.forEach(dataset => {
                const dataPoint = dataset.data.find(item => item.x === timestamp);
                const value = dataPoint ? dataPoint.y.toFixed(2) : '';
                row.push(value);
            });
            row.push(this.benchmark.toFixed(2)); // Add benchmark value
            csv += row.join(',') + '\n';
        });

        return csv;
    }

    /**
     * 导出统计摘要为CSV
     * @returns {string} CSV字符串
     */
    exportStatsToCSV() {
        let csv = '策略名称,当前Sharpe,平均Sharpe,最小值,最大值,标准差,>1.0比例(%),>2.0比例(%),<0比例(%)\n';

        this.strategies.forEach((strategyInfo) => {
            const stats = strategyInfo.stats;
            csv += [
                strategyInfo.strategy.name,
                stats.current.toFixed(2),
                stats.average.toFixed(2),
                stats.min.toFixed(2),
                stats.max.toFixed(2),
                stats.stdDev.toFixed(2),
                stats.above1Percent.toFixed(1),
                stats.above2Percent.toFixed(1),
                stats.below0Percent.toFixed(1)
            ].join(',') + '\n';
        });

        // Add advanced metrics if available
        if (this.advancedMetrics.size > 0) {
            csv += '\n=== 高级指标 ===\n';
            csv += '策略名称,信息比率,跟踪误差(%),胜率(%),超额Sharpe,Bootstrap均值,Bootstrap标准差\n';

            this.strategies.forEach((strategyInfo, strategyId) => {
                const advancedMetrics = this.advancedMetrics.get(strategyId);
                const benchmarkComparison = this.getBenchmarkComparison(strategyId, this.selectedBenchmarks[0]);
                const distribution = this.getDistributionAnalysis(strategyId);

                csv += [
                    strategyInfo.strategy.name,
                    benchmarkComparison?.information_ratio?.toFixed(3) || 'N/A',
                    benchmarkComparison?.tracking_error ? (benchmarkComparison.tracking_error * 100).toFixed(2) : 'N/A',
                    benchmarkComparison?.win_rate ? (benchmarkComparison.win_rate * 100).toFixed(1) : 'N/A',
                    benchmarkComparison?.excess_sharpe?.toFixed(3) || 'N/A',
                    distribution?.distribution?.mean?.toFixed(3) || 'N/A',
                    distribution?.distribution?.std?.toFixed(3) || 'N/A'
                ].join(',') + '\n';
            });
        }

        return csv;
    }

    /**
     * 导出完整分析报告
     * @returns {Object} 完整报告数据
     */
    exportFullReport() {
        const report = {
            timestamp: new Date().toISOString(),
            analysisOptions: this.analysisOptions,
            selectedBenchmarks: this.selectedBenchmarks,
            strategies: [],
            benchmarks: {},
            summary: {
                totalStrategies: this.strategies.size,
                rollingPeriod: this.rollingPeriod,
                benchmarkLevel: this.benchmarkLevel
            }
        };

        // Add strategy details
        this.strategies.forEach((strategyInfo, strategyId) => {
            const strategyReport = {
                id: strategyId,
                name: strategyInfo.strategy.name,
                basicStats: strategyInfo.stats,
                advancedMetrics: this.getAdvancedMetrics(strategyId),
                benchmarkComparisons: {}
            };

            // Add benchmark comparisons
            this.selectedBenchmarks.forEach(benchmarkName => {
                const comparison = this.getBenchmarkComparison(strategyId, benchmarkName);
                if (comparison) {
                    strategyReport.benchmarkComparisons[benchmarkName] = comparison;
                }
            });

            report.strategies.push(strategyReport);
        });

        // Add benchmark information
        this.selectedBenchmarks.forEach(benchmarkName => {
            report.benchmarks[benchmarkName] = {
                name: benchmarkName,
                color: SHARPE_CONFIG.BENCHMARK_COLORS[benchmarkName] || '#999999'
            };
        });

        return report;
    }

    /**
     * 导出JSON格式数据
     * @returns {string} JSON字符串
     */
    exportToJSON() {
        const report = this.exportFullReport();
        return JSON.stringify(report, null, 2);
    }

    /**
     * 刷新分析数据
     * @returns {Promise<void>}
     */
    async refreshAnalysis() {
        const refreshPromises = [];
        this.strategies.forEach((strategyInfo, strategyId) => {
            refreshPromises.push(this.runAdvancedAnalysis(strategyId));
        });

        try {
            await Promise.all(refreshPromises);
            console.log('所有策略Sharpe分析数据已刷新');
        } catch (error) {
            console.error('刷新分析数据失败:', error);
            throw error;
        }
    }

    /**
     * 清除所有分析数据
     */
    clearAnalysis() {
        this.advancedMetrics.clear();
        this.distributionData.clear();
        this.benchmarks.clear();
        sharpeAnalysisService.clearCache();
        this.updateChart();
    }

    /**
     * 获取分析统计摘要
     * @returns {Object} 统计摘要
     */
    getAnalysisSummary() {
        const summary = {
            strategies: this.strategies.size,
            benchmarks: this.selectedBenchmarks.length,
            withAdvancedAnalysis: 0,
            averageSharpe: 0,
            bestStrategy: null,
            worstStrategy: null,
            analysisTimestamp: null
        };

        let totalSharpe = 0;
        let bestSharpe = -Infinity;
        let worstSharpe = Infinity;
        let bestStrategyId = null;
        let worstStrategyId = null;

        this.strategies.forEach((strategyInfo, strategyId) => {
            const sharpe = strategyInfo.stats.current;
            totalSharpe += sharpe;

            if (sharpe > bestSharpe) {
                bestSharpe = sharpe;
                bestStrategyId = strategyId;
            }

            if (sharpe < worstSharpe) {
                worstSharpe = sharpe;
                worstStrategyId = strategyId;
            }

            if (this.advancedMetrics.has(strategyId)) {
                summary.withAdvancedAnalysis++;
            }
        });

        summary.averageSharpe = this.strategies.size > 0 ? totalSharpe / this.strategies.size : 0;
        summary.bestStrategy = bestStrategyId ? {
            id: bestStrategyId,
            name: this.strategies.get(bestStrategyId)?.strategy?.name,
            sharpe: bestSharpe
        } : null;
        summary.worstStrategy = worstStrategyId ? {
            id: worstStrategyId,
            name: this.strategies.get(worstStrategyId)?.strategy?.name,
            sharpe: worstSharpe
        } : null;

        // Get latest analysis timestamp
        this.advancedMetrics.forEach((metrics) => {
            if (metrics.timestamp && (!summary.analysisTimestamp || metrics.timestamp > summary.analysisTimestamp)) {
                summary.analysisTimestamp = metrics.timestamp;
            }
        });

        return summary;
    }

    /**
     * 设置事件监听器
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    on(event, callback) {
        const events = {
            'loading': 'sharpeChartLoading',
            'updated': 'sharpeChartUpdated',
            'analysisComplete': 'sharpeChartAnalysisComplete'
        };

        const eventName = events[event];
        if (eventName) {
            document.addEventListener(eventName, callback);
        }
    }

    /**
     * 移除事件监听器
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    off(event, callback) {
        const events = {
            'loading': 'sharpeChartLoading',
            'updated': 'sharpeChartUpdated',
            'analysisComplete': 'sharpeChartAnalysisComplete'
        };

        const eventName = events[event];
        if (eventName) {
            document.removeEventListener(eventName, callback);
        }
    }

    /**
     * 触发自定义事件
     * @param {string} event - 事件名称
     * @param {Object} detail - 事件详情
     */
    _triggerEvent(event, detail = {}) {
        const eventName = `sharpeChart${event.charAt(0).toUpperCase() + event.slice(1)}`;
        const customEvent = new CustomEvent(eventName, { detail });
        document.dispatchEvent(customEvent);
    }
}

export default SharpeRatioChart;