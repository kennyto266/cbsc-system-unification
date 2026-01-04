/**
 * 个人策略管理Dashboard - 净值曲线图
 * Personal Strategy Management Dashboard - Net Value Chart
 */

import { LineChart, ChartUtils } from './chart.js';
import { CHART_CONFIG, TIME_PERIODS } from './constants.js';

/**
 * 净值曲线图类
 */
class NetValueChart extends LineChart {
    constructor(canvasId, options = {}) {
        super(canvasId, {
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
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
                            const label = context.dataset.label || '净值';
                            const value = context.parsed.y;
                            const percentage = (value * 100).toFixed(2);
                            return `${label}: ${percentage}%`;
                        }
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
                        drawBorder: false
                    }
                },
                y: {
                    position: 'right',
                    grid: {
                        drawBorder: false
                    },
                    ticks: {
                        callback: (value) => {
                            return `${(value * 100).toFixed(1)}%`;
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            },
            ...options
        });

        this.strategies = new Map();
        this.benchmark = null;
        this.period = TIME_PERIODS.ONE_MONTH.value;
    }

    /**
     * 设置时间周期
     * @param {string} period - 时间周期
     */
    setPeriod(period) {
        this.period = period;
        this.update();
    }

    /**
     * 添加策略数据
     * @param {string} strategyId - 策略ID
     * @param {Object} strategy - 策略对象
     * @param {Array} data - 净值数据
     */
    addStrategy(strategyId, strategy, data) {
        if (!data || !Array.isArray(data)) {
            console.warn(`Invalid net value data for strategy ${strategyId}`);
            return;
        }

        const color = this.getStrategyColor(strategyId);
        const dataset = {
            label: strategy.name || `策略 ${strategyId}`,
            data: this.processData(data),
            borderColor: color,
            backgroundColor: ChartUtils.hexToRgba(color, 0.1),
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderWidth: 2,
            hidden: false
        };

        this.strategies.set(strategyId, {
            strategy,
            dataset,
            originalData: data
        });

        this.updateChart();
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
        const strategyInfo = this.strategies.get(strategyId);
        if (strategyInfo && data) {
            strategyInfo.originalData = data;
            strategyInfo.dataset.data = this.processData(data);
            this.updateChart();
        }
    }

    /**
     * 设置基准数据
     * @param {Array} data - 基准数据
     * @param {string} label - 基准标签
     */
    setBenchmark(data, label = '基准') {
        if (data && Array.isArray(data)) {
            this.benchmark = {
                label,
                data: this.processData(data),
                borderColor: '#999',
                backgroundColor: 'transparent',
                borderWidth: 2,
                borderDash: [5, 5],
                tension: 0,
                pointRadius: 0
            };
            this.updateChart();
        }
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
     * 处理数据
     * @param {Array} data - 原始数据
     * @returns {Array} 处理后的数据
     */
    processData(data) {
        if (!data || data.length === 0) return [];

        // Filter data based on period
        const filteredData = this.filterDataByPeriod(data);

        // Convert to chart format
        return filteredData.map(item => ({
            x: item.timestamp || item.date,
            y: item.net_value || item.cumulative_return || item.value || 0
        }));
    }

    /**
     * 根据周期过滤数据
     * @param {Array} data - 原始数据
     * @returns {Array} 过滤后的数据
     */
    filterDataByPeriod(data) {
        if (this.period === TIME_PERIODS.ALL.value) {
            return data;
        }

        const periodConfig = Object.values(TIME_PERIODS).find(p => p.value === this.period);
        if (!periodConfig || !periodConfig.days) {
            return data;
        }

        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - periodConfig.days);

        return data.filter(item => {
            const itemDate = new Date(item.timestamp || item.date);
            return itemDate >= cutoffDate;
        });
    }

    /**
     * 更新图表
     */
    updateChart() {
        if (!this.chart) return;

        const datasets = [];

        // Add strategies
        this.strategies.forEach((strategyInfo) => {
            datasets.push(strategyInfo.dataset);
        });

        // Add benchmark if exists
        if (this.benchmark) {
            datasets.push(this.benchmark);
        }

        // Update chart data
        this.chart.data.datasets = datasets;

        // Get all timestamps from strategies
        const allTimestamps = new Set();
        this.strategies.forEach((strategyInfo) => {
            strategyInfo.originalData.forEach(item => {
                allTimestamps.add(item.timestamp || item.date);
            });
        });

        // Sort timestamps
        const sortedTimestamps = Array.from(allTimestamps).sort();

        // Update chart labels
        this.chart.data.labels = sortedTimestamps;

        this.update();
    }

    /**
     * 格式化Y轴标签
     * @param {number} value - 值
     * @returns {string} 格式化后的标签
     */
    formatYAxis(value) {
        return `${(value * 100).toFixed(1)}%`;
    }

    /**
     * 获取最新净值
     * @param {string} strategyId - 策略ID
     * @returns {number|null} 最新净值
     */
    getLatestValue(strategyId) {
        const strategyInfo = this.strategies.get(strategyId);
        if (strategyInfo && strategyInfo.originalData.length > 0) {
            const lastItem = strategyInfo.originalData[strategyInfo.originalData.length - 1];
            return lastItem.net_value || lastItem.cumulative_return || lastItem.value || 0;
        }
        return null;
    }

    /**
     * 获取期间收益率
     * @param {string} strategyId - 策略ID
     * @returns {number|null} 期间收益率
     */
    getPeriodReturn(strategyId) {
        const strategyInfo = this.strategies.get(strategyId);
        if (!strategyInfo || strategyInfo.originalData.length < 2) {
            return null;
        }

        const data = this.filterDataByPeriod(strategyInfo.originalData);
        if (data.length < 2) return null;

        const firstValue = data[0].net_value || data[0].cumulative_return || data[0].value || 0;
        const lastValue = data[data.length - 1].net_value || data[data.length - 1].cumulative_return || data[data.length - 1].value || 0;

        return lastValue - firstValue;
    }

    /**
     * 获取最大回撤
     * @param {string} strategyId - 策略ID
     * @returns {number} 最大回撤
     */
    getMaxDrawdown(strategyId) {
        const strategyInfo = this.strategies.get(strategyId);
        if (!strategyInfo || strategyInfo.originalData.length < 2) {
            return 0;
        }

        const data = this.filterDataByPeriod(strategyInfo.originalData);
        let maxDrawdown = 0;
        let peak = data[0].net_value || data[0].cumulative_return || data[0].value || 1;

        for (let i = 1; i < data.length; i++) {
            const value = data[i].net_value || data[i].cumulative_return || data[i].value || 1;

            if (value > peak) {
                peak = value;
            } else {
                const drawdown = (peak - value) / peak;
                if (drawdown > maxDrawdown) {
                    maxDrawdown = drawdown;
                }
            }
        }

        return maxDrawdown;
    }

    /**
     * 获取统计信息
     * @returns {Object} 统计信息
     */
    getStats() {
        const stats = {
            strategies: {},
            benchmark: null
        };

        // Strategy stats
        this.strategies.forEach((strategyInfo, strategyId) => {
            stats.strategies[strategyId] = {
                latestValue: this.getLatestValue(strategyId),
                periodReturn: this.getPeriodReturn(strategyId),
                maxDrawdown: this.getMaxDrawdown(strategyId),
                dataPoints: strategyInfo.originalData.length
            };
        });

        // Benchmark stats
        if (this.benchmark) {
            // Calculate benchmark stats similar to strategies
            stats.benchmark = {
                periodReturn: 0, // Would need calculation
                maxDrawdown: 0,   // Would need calculation
                dataPoints: this.benchmark.data.length
            };
        }

        return stats;
    }

    /**
     * 导出数据为CSV
     * @returns {string} CSV字符串
     */
    exportToCSV() {
        const headers = ['Timestamp'];
        const datasets = [];

        // Collect all datasets
        this.strategies.forEach((strategyInfo, strategyId) => {
            headers.push(strategyInfo.strategy.name);
            datasets.push({
                data: strategyInfo.originalData,
                name: strategyInfo.strategy.name
            });
        });

        if (this.benchmark) {
            headers.push(this.benchmark.label);
            datasets.push({
                data: this.benchmark.data,
                name: this.benchmark.label
            });
        }

        // Collect all timestamps
        const allTimestamps = new Set();
        datasets.forEach(dataset => {
            dataset.data.forEach(item => {
                allTimestamps.add(item.timestamp || item.date);
            });
        });

        const sortedTimestamps = Array.from(allTimestamps).sort();

        // Build CSV
        let csv = headers.join(',') + '\n';

        sortedTimestamps.forEach(timestamp => {
            const row = [timestamp];
            datasets.forEach(dataset => {
                const dataPoint = dataset.data.find(item =>
                    (item.timestamp || item.date) === timestamp
                );
                const value = dataPoint
                    ? (dataPoint.net_value || dataPoint.cumulative_return || dataPoint.value || 0)
                    : '';
                row.push(value);
            });
            csv += row.join(',') + '\n';
        });

        return csv;
    }
}

export default NetValueChart;