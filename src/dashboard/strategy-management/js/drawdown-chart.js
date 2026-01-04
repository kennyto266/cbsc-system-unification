/**
 * 个人策略管理Dashboard - 回撤曲线图
 * Personal Strategy Management Dashboard - Drawdown Chart
 */

import { LineChart, ChartUtils } from './chart.js';
import { CHART_CONFIG } from './constants.js';

/**
 * 回撤曲线图类
 */
class DrawdownChart extends LineChart {
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
                            const label = context.dataset.label || '回撤';
                            const value = context.parsed.y;
                            const percentage = Math.abs(value * 100).toFixed(2);
                            return `${label}: -${percentage}%`;
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
                    min: 0,
                    max: 0,
                    reverse: true,
                    grid: {
                        drawBorder: false
                    },
                    ticks: {
                        callback: (value) => {
                            return `${Math.abs(value * 100).toFixed(1)}%`;
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
        this.currentStrategyId = null;
        this.maxDrawdowns = new Map();
    }

    /**
     * 设置当前策略
     * @param {string} strategyId - 策略ID（null表示所有策略）
     */
    setCurrentStrategy(strategyId) {
        this.currentStrategyId = strategyId;
        this.updateChart();
    }

    /**
     * 添加策略数据
     * @param {string} strategyId - 策略ID
     * @param {Object} strategy - 策略对象
     * @param {Array} data - 净值数据
     */
    addStrategy(strategyId, strategy, data) {
        if (!data || !Array.isArray(data) || data.length < 2) {
            console.warn(`Invalid data for drawdown calculation: ${strategyId}`);
            return;
        }

        // Calculate drawdown
        const drawdownData = this.calculateDrawdown(data);
        const maxDrawdown = Math.max(...drawdownData.map(d => Math.abs(d.y)));

        const color = this.getStrategyColor(strategyId);
        const dataset = {
            label: strategy.name || `策略 ${strategyId}`,
            data: drawdownData,
            borderColor: color,
            backgroundColor: ChartUtils.hexToRgba(color, 0.2),
            borderWidth: 2,
            fill: true,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderWidth: 2,
            hidden: strategyId !== this.currentStrategyId && this.currentStrategyId !== null
        };

        this.strategies.set(strategyId, {
            strategy,
            dataset,
            maxDrawdown,
            originalData: data
        });

        this.maxDrawdowns.set(strategyId, maxDrawdown);

        // Update Y-axis max
        this.updateYAxisRange();

        this.updateChart();
    }

    /**
     * 移除策略
     * @param {string} strategyId - 策略ID
     */
    removeStrategy(strategyId) {
        this.strategies.delete(strategyId);
        this.maxDrawdowns.delete(strategyId);
        this.updateYAxisRange();
        this.updateChart();
    }

    /**
     * 更新策略数据
     * @param {string} strategyId - 策略ID
     * @param {Array} data - 新数据
     */
    updateStrategy(strategyId, data) {
        if (!data || !Array.isArray(data) || data.length < 2) {
            return;
        }

        const strategyInfo = this.strategies.get(strategyId);
        if (strategyInfo) {
            // Recalculate drawdown
            const drawdownData = this.calculateDrawdown(data);
            const maxDrawdown = Math.max(...drawdownData.map(d => Math.abs(d.y)));

            strategyInfo.originalData = data;
            strategyInfo.dataset.data = drawdownData;
            strategyInfo.maxDrawdown = maxDrawdown;

            this.maxDrawdowns.set(strategyId, maxDrawdown);

            // Update Y-axis range
            this.updateYAxisRange();

            this.updateChart();
        }
    }

    /**
     * 计算回撤
     * @param {Array} data - 净值数据
     * @returns {Array} 回撤数据
     */
    calculateDrawdown(data) {
        if (!data || data.length < 2) return [];

        const drawdown = [];
        let peak = data[0].net_value || data[0].cumulative_return || data[0].value || 1;

        data.forEach(item => {
            const value = item.net_value || item.cumulative_return || item.value || 1;
            const timestamp = item.timestamp || item.date;

            // Update peak if we have a new high
            if (value > peak) {
                peak = value;
            }

            // Calculate drawdown (as a negative percentage)
            const currentDrawdown = (peak - value) / peak;

            drawdown.push({
                x: timestamp,
                y: -currentDrawdown // Negative because chart is reversed
            });
        });

        return drawdown;
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

        // Show selected strategy or all strategies
        if (this.currentStrategyId) {
            const strategyInfo = this.strategies.get(this.currentStrategyId);
            if (strategyInfo) {
                datasets.push(strategyInfo.dataset);
            }
        } else {
            // Show all strategies
            this.strategies.forEach((strategyInfo) => {
                datasets.push({
                    ...strategyInfo.dataset,
                    hidden: false
                });
            });
        }

        // Update chart data
        this.chart.data.datasets = datasets;

        // Get all timestamps from selected strategies
        const allTimestamps = new Set();
        const strategiesToShow = this.currentStrategyId
            ? [this.currentStrategyId]
            : Array.from(this.strategies.keys());

        strategiesToShow.forEach(strategyId => {
            const strategyInfo = this.strategies.get(strategyId);
            if (strategyInfo) {
                strategyInfo.originalData.forEach(item => {
                    allTimestamps.add(item.timestamp || item.date);
                });
            }
        });

        // Sort timestamps
        const sortedTimestamps = Array.from(allTimestamps).sort();

        // Update chart labels
        this.chart.data.labels = sortedTimestamps;

        this.update();
    }

    /**
     * 更新Y轴范围
     */
    updateYAxisRange() {
        if (!this.chart) return;

        let maxDrawdown = 0;
        const strategiesToShow = this.currentStrategyId
            ? [this.currentStrategyId]
            : Array.from(this.strategies.keys());

        strategiesToShow.forEach(strategyId => {
            const dd = this.maxDrawdowns.get(strategyId);
            if (dd > maxDrawdown) {
                maxDrawdown = dd;
            }
        });

        // Set Y-axis range with some padding
        if (this.chart.options.scales.y) {
            this.chart.options.scales.y.max = 0;
            this.chart.options.scales.y.min = -Math.min(maxDrawdown * 1.1, 0.5); // Max 50% drawdown display
        }
    }

    /**
     * 获取最大回撤
     * @param {string} strategyId - 策略ID
     * @returns {number} 最大回撤
     */
    getMaxDrawdown(strategyId = null) {
        if (strategyId) {
            return this.maxDrawdowns.get(strategyId) || 0;
        }

        // Get maximum drawdown across all strategies
        let max = 0;
        this.maxDrawdowns.forEach((dd) => {
            if (dd > max) max = dd;
        });
        return max;
    }

    /**
     * 获取当前回撤
     * @param {string} strategyId - 策略ID
     * @returns {number} 当前回撤
     */
    getCurrentDrawdown(strategyId) {
        const strategyInfo = this.strategies.get(strategyId);
        if (!strategyInfo || strategyInfo.originalData.length < 2) {
            return 0;
        }

        const data = strategyInfo.originalData;
        const lastValue = data[data.length - 1].net_value || data[data.length - 1].cumulative_return || data[data.length - 1].value || 1;
        let peak = lastValue;

        // Find the peak in the data
        for (let i = data.length - 1; i >= 0; i--) {
            const value = data[i].net_value || data[i].cumulative_return || data[i].value || 1;
            if (value > peak) {
                peak = value;
            }
        }

        return (peak - lastValue) / peak;
    }

    /**
     * 获取回撤统计
     * @param {string} strategyId - 策略ID
     * @returns {Object} 回撤统计
     */
    getDrawdownStats(strategyId = null) {
        const stats = {};

        const strategiesToAnalyze = strategyId
            ? [strategyId]
            : Array.from(this.strategies.keys());

        strategiesToAnalyze.forEach(id => {
            const strategyInfo = this.strategies.get(id);
            if (strategyInfo) {
                const drawdownData = strategyInfo.dataset.data;
                const drawdowns = drawdownData.map(d => Math.abs(d.y));

                stats[id] = {
                    maxDrawdown: Math.max(...drawdowns),
                    currentDrawdown: this.getCurrentDrawdown(id),
                    averageDrawdown: drawdowns.reduce((a, b) => a + b, 0) / drawdowns.length,
                    timeInDrawdown: this.calculateTimeInDrawdown(drawdowns),
                    maxDrawdownDuration: this.calculateMaxDrawdownDuration(drawdowns),
                    strategyName: strategyInfo.strategy.name
                };
            }
        });

        return strategyId ? stats[strategyId] : stats;
    }

    /**
     * 计算在回撤中的时间比例
     * @param {Array} drawdowns - 回撤数据
     * @returns {number} 时间比例（0-1）
     */
    calculateTimeInDrawdown(drawdowns) {
        if (drawdowns.length === 0) return 0;

        const timeInDrawdown = drawdowns.filter(dd => dd > 0.001).length; // > 0.1%
        return timeInDrawdown / drawdowns.length;
    }

    /**
     * 计算最大回撤持续时间
     * @param {Array} drawdowns - 回撤数据
     * @returns {number} 最大持续时间（天数）
     */
    calculateMaxDrawdownDuration(drawdowns) {
        if (drawdowns.length === 0) return 0;

        let maxDuration = 0;
        let currentDuration = 0;

        drawdowns.forEach(dd => {
            if (dd > 0.001) { // > 0.1%
                currentDuration++;
            } else {
                if (currentDuration > maxDuration) {
                    maxDuration = currentDuration;
                }
                currentDuration = 0;
            }
        });

        return Math.max(maxDuration, currentDuration);
    }

    /**
     * 导出回撤数据为CSV
     * @returns {string} CSV字符串
     */
    exportToCSV() {
        const headers = ['Timestamp'];
        const datasets = [];

        // Collect datasets
        const strategiesToShow = this.currentStrategyId
            ? [this.currentStrategyId]
            : Array.from(this.strategies.keys());

        strategiesToShow.forEach(strategyId => {
            const strategyInfo = this.strategies.get(strategyId);
            if (strategyInfo) {
                headers.push(strategyInfo.strategy.name);
                datasets.push({
                    data: strategyInfo.dataset.data,
                    name: strategyInfo.strategy.name
                });
            }
        });

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
                const value = dataPoint ? Math.abs(dataPoint.y * 100).toFixed(2) : '';
                row.push(value);
            });
            csv += row.join(',') + '\n';
        });

        return csv;
    }
}

export default DrawdownChart;