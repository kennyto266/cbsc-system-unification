/**
 * 增強版Chart.js圖表組件
 * 專為CBSC策略管理的專業級數據可視化
 */

// ========== 圖表配置和主題 ==========
const CHART_THEMES = {
    light: {
        backgroundColor: '#ffffff',
        gridColor: '#e0e0e0',
        textColor: '#2c3e50',
        colors: {
            primary: '#3498db',
            success: '#27ae60',
            danger: '#e74c3c',
            warning: '#f39c12',
            info: '#5dade2',
            purple: '#9b59b6'
        }
    },
    dark: {
        backgroundColor: '#2c3e50',
        gridColor: '#34495e',
        textColor: '#ecf0f1',
        colors: {
            primary: '#5dade2',
            success: '#52be80',
            danger: '#ec7063',
            warning: '#f4d03f',
            info: '#85c1e9',
            purple: '#af7ac5'
        }
    }
};

// ========== 全局Chart.js配置 ==========
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif';
Chart.defaults.color = CHART_THEMES.light.textColor;
Chart.defaults.borderColor = CHART_THEMES.light.gridColor;

// 响应式配置
const RESPONSIVE_CONFIG = {
    responsive: true,
    maintainAspectRatio: false,
    resizeDelay: 0,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                font: {
                    size: 12
                },
                padding: 15,
                usePointStyle: true
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleFont: {
                size: 14,
                weight: 'bold'
            },
            bodyFont: {
                size: 12
            },
            padding: 12,
            cornerRadius: 8,
            displayColors: true,
            callbacks: {
                label: function(context) {
                    let label = context.dataset.label || '';
                    if (label) {
                        label += ': ';
                    }

                    const value = context.parsed;
                    if (value !== null) {
                        // 根據圖表類型格式化數值
                        if (context.chart.config.type === 'line' && context.dataset.yAxisID === 'y_percentage') {
                            label += (value * 100).toFixed(1) + '%';
                        } else if (context.chart.config.type === 'bar' && context.dataset.yAxisID === 'y_percentage') {
                            label += (value * 100).toFixed(1) + '%';
                        } else if (typeof value === 'number') {
                            label += value.toFixed(3);
                        } else {
                            label += value;
                        }
                    }
                    return label;
                }
            }
        }
    },
    scales: {
        x: {
            grid: {
                display: true,
                color: CHART_THEMES.light.gridColor
            },
            ticks: {
                font: {
                    size: 11
                }
            }
        },
        y: {
            grid: {
                display: true,
                color: CHART_THEMES.light.gridColor
            },
            ticks: {
                font: {
                    size: 11
                }
            }
        }
    },
    animation: {
        duration: 1000,
        easing: 'easeInOutQuart'
    }
};

// ========== 夏普比率條形圖 ==========
class SharpeRatioChart {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.options = {
            ...RESPONSIVE_CONFIG,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const ctx = this.container.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: '夏普比率 (SR)',
                    data: [],
                    backgroundColor: [],
                    borderColor: [],
                    borderWidth: 2,
                    borderRadius: 6,
                    barPercentage: 0.7
                }]
            },
            options: {
                ...this.options,
                indexAxis: 'y',
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '策略',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: '夏普比率',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(2);
                            }
                        }
                    }
                },
                plugins: {
                    ...this.options.plugins,
                    tooltip: {
                        ...this.options.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.x;
                                return `SR: ${value.toFixed(3)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    update(strategies) {
        if (!this.chart) return;

        const labels = strategies.map(s => s.display_name || s.name);
        const data = strategies.map(s => s.performance?.sharpe_ratio || 0);
        const colors = data.map(value =>
            value >= 0 ? CHART_THEMES.light.colors.success : CHART_THEMES.light.colors.danger
        );
        const borderColors = data.map(value =>
            value >= 0 ? CHART_THEMES.light.colors.success : CHART_THEMES.light.colors.danger
        );

        this.chart.data.labels = labels;
        this.chart.data.datasets[0].data = data;
        this.chart.data.datasets[0].backgroundColor = colors.map(c => c + '20');
        this.chart.data.datasets[0].borderColor = borderColors;
        this.chart.update('active');
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// ========== 最大回撤折線圖 ==========
class MaxDrawdownChart {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.options = {
            ...RESPONSIVE_CONFIG,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const ctx = this.container.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                ...this.options,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: {
                                month: 'MMM YYYY'
                            }
                        },
                        title: {
                            display: true,
                            text: '時間',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 1,
                        title: {
                            display: true,
                            text: '最大回撤 (%)',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            callback: function(value) {
                                return (value * 100).toFixed(1) + '%';
                            }
                        },
                        yAxisID: 'y_percentage'
                    }
                },
                elements: {
                    line: {
                        tension: 0.4,
                        borderWidth: 3
                    },
                    point: {
                        radius: 5,
                        hoverRadius: 8,
                        borderWidth: 2,
                        backgroundColor: '#ffffff'
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    ...this.options.plugins,
                    tooltip: {
                        ...this.options.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                return `回撤: ${(value * 100).toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    update(historicalData) {
        if (!this.chart || !historicalData) return;

        // 生成歷史數據標籤（模擬30天）
        const labels = this.generateTimeLabels();

        // 為每個策略生成歷史回撤數據
        const datasets = historicalData.strategies.map((strategy, index) => {
            const baseDrawdown = Math.abs(strategy.performance?.max_drawdown || 0.2);
            const colors = [
                CHART_THEMES.light.colors.primary,
                CHART_THEMES.light.colors.success,
                CHART_THEMES.light.colors.warning,
                CHART_THEMES.light.colors.purple
            ];

            return {
                label: strategy.display_name || strategy.name,
                data: this.generateDrawdownData(labels.length, baseDrawdown, strategy.status),
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '10',
                borderWidth: 2,
                fill: false,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6
            };
        });

        this.chart.data.labels = labels;
        this.chart.data.datasets = datasets;
        this.chart.update('active');
    }

    generateTimeLabels() {
        const labels = [];
        const now = new Date();

        for (let i = 29; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            labels.push(date);
        }

        return labels;
    }

    generateDrawdownData(days, baseDrawdown, status) {
        const data = [];
        let currentDrawdown = baseDrawdown;

        for (let i = 0; i < days; i++) {
            // 模擬回撤數據，已停止的策略回撤變化較小
            const volatility = status === 'stopped' ? 0.01 : 0.05;
            currentDrawdown = Math.max(0,
                currentDrawdown + (Math.random() - 0.5) * volatility
            );

            data.push(currentDrawdown);
        }

        return data;
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// ========== 策略表現雷達圖 ==========
class StrategyRadarChart {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.options = {
            ...RESPONSIVE_CONFIG,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const ctx = this.container.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: [
                    '夏普比率',
                    '最大回撤',
                    '總收益率',
                    '勝率',
                    '信號強度'
                ],
                datasets: []
            },
            options: {
                ...this.options,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        min: 0,
                        ticks: {
                            stepSize: 20,
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        pointLabels: {
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: CHART_THEMES.light.gridColor
                        }
                    }
                },
                elements: {
                    line: {
                        borderWidth: 3
                    },
                    point: {
                        radius: 6,
                        hoverRadius: 8
                    }
                }
            }
        });
    }

    update(strategies) {
        if (!this.chart || !strategies) return;

        // 轉換策略數據為雷達圖格式
        const datasets = strategies.map((strategy, index) => {
            const performance = strategy.performance || {};
            const colors = [
                CHART_THEMES.light.colors.primary,
                CHART_THEMES.light.colors.success,
                CHART_THEMES.light.colors.warning,
                CHART_THEMES.light.colors.purple
            ];

            // 正規化數據到0-100範圍
            const normalizedData = [
                Math.min(100, Math.max(0, (performance.sharpe_ratio || 0) * 50 + 50)), // SR範圍[-1, 3] -> [0, 100]
                Math.max(0, 100 - Math.abs(performance.max_drawdown || 0) * 100), // MDD範圍[0, 1] -> [0, 100]
                Math.min(100, Math.max(0, (performance.total_return || 0) * 20 + 50)), // Return範圍[-1, 2] -> [0, 100]
                Math.min(100, (performance.win_rate || 0) * 100), // Win Rate範圍[0, 1] -> [0, 100]
                Math.min(100, (strategy.last_signal?.strength || 0) * 100) // Signal Strength範圍[0, 1] -> [0, 100]
            ];

            return {
                label: strategy.display_name || strategy.name,
                data: normalizedData,
                borderColor: colors[index % colors.length],
                backgroundColor: colors[index % colors.length] + '40',
                borderWidth: 2,
                pointBackgroundColor: colors[index % colors.length],
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: colors[index % colors.length]
            };
        });

        this.chart.data.datasets = datasets;
        this.chart.update('active');
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// ========== 策略組合圖表 ==========
class StrategyComparisonChart {
    constructor(containerId, type = 'bar', options = {}) {
        this.container = document.getElementById(containerId);
        this.chart = null;
        this.type = type;
        this.options = {
            ...RESPONSIVE_CONFIG,
            ...options
        };
        this.init();
    }

    init() {
        if (!this.container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const ctx = this.container.getContext('2d');
        this.chart = new Chart(ctx, {
            type: this.type,
            data: {
                labels: [],
                datasets: []
            },
            options: {
                ...this.options,
                scales: this.type === 'bar' ? this.getBarScales() : this.getLineScales(),
                plugins: {
                    ...this.options.plugins,
                    title: {
                        display: true,
                        text: '策略表現對比',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    }
                }
            }
        });
    }

    getBarScales() {
        return {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: '數值'
                }
            },
            x: {
                title: {
                    display: true,
                    text: '指標'
                }
            }
        };
    }

    getLineScales() {
        return {
            y: {
                title: {
                    display: true,
                    text: '數值'
                }
            },
            x: {
                title: {
                    display: true,
                    text: '策略'
                }
            }
        };
    }

    update(strategies, metric = 'all') {
        if (!this.chart || !strategies) return;

        if (metric === 'all') {
            this.updateMultiMetricChart(strategies);
        } else {
            this.updateSingleMetricChart(strategies, metric);
        }
    }

    updateMultiMetricChart(strategies) {
        const labels = strategies.map(s => s.display_name || s.name);

        const datasets = [
            {
                label: '夏普比率',
                data: strategies.map(s => s.performance?.sharpe_ratio || 0),
                backgroundColor: CHART_THEMES.light.colors.primary + '80',
                borderColor: CHART_THEMES.light.colors.primary,
                borderWidth: 2,
                yAxisID: 'y_sharpe'
            },
            {
                label: '最大回撤 (%)',
                data: strategies.map(s => Math.abs((s.performance?.max_drawdown || 0) * 100)),
                backgroundColor: CHART_THEMES.light.colors.danger + '80',
                borderColor: CHART_THEMES.light.colors.danger,
                borderWidth: 2,
                yAxisID: 'y_drawdown'
            },
            {
                label: '總收益率 (%)',
                data: strategies.map(s => (s.performance?.total_return || 0) * 100),
                backgroundColor: CHART_THEMES.light.colors.success + '80',
                borderColor: CHART_THEMES.light.colors.success,
                borderWidth: 2,
                yAxisID: 'y_return'
            },
            {
                label: '勝率 (%)',
                data: strategies.map(s => (s.performance?.win_rate || 0) * 100),
                backgroundColor: CHART_THEMES.light.colors.warning + '80',
                borderColor: CHART_THEMES.light.colors.warning,
                borderWidth: 2,
                yAxisID: 'y_percentage'
            }
        ];

        this.chart.data.labels = labels;
        this.chart.data.datasets = datasets;
        this.chart.update('active');
    }

    updateSingleMetricChart(strategies, metric) {
        const labels = strategies.map(s => s.display_name || s.name);
        const metricConfig = {
            'sharpe_ratio': {
                label: '夏普比率',
                data: strategies.map(s => s.performance?.sharpe_ratio || 0),
                backgroundColor: CHART_THEMES.light.colors.primary + '80',
                borderColor: CHART_THEMES.light.colors.primary
            },
            'max_drawdown': {
                label: '最大回撤 (%)',
                data: strategies.map(s => Math.abs((s.performance?.max_drawdown || 0) * 100)),
                backgroundColor: CHART_THEMES.light.colors.danger + '80',
                borderColor: CHART_THEMES.light.colors.danger
            },
            'total_return': {
                label: '總收益率 (%)',
                data: strategies.map(s => (s.performance?.total_return || 0) * 100),
                backgroundColor: CHART_THEMES.light.colors.success + '80',
                borderColor: CHART_THEMES.light.colors.success
            },
            'win_rate': {
                label: '勝率 (%)',
                data: strategies.map(s => (s.performance?.win_rate || 0) * 100),
                backgroundColor: CHART_THEMES.light.colors.warning + '80',
                borderColor: CHART_THEMES.light.colors.warning
            }
        };

        const config = metricConfig[metric] || metricConfig.sharpe_ratio;

        this.chart.data.labels = labels;
        this.chart.data.datasets = [{
            ...config,
            borderWidth: 2,
            borderRadius: 6,
            barPercentage: 0.8
        }];
        this.chart.update('active');
    }

    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

// ========== 圖表管理器 ==========
class ChartManager {
    constructor() {
        this.charts = {};
        this.currentTheme = 'light';
        this.init();
    }

    init() {
        // 初始化所有圖表
        this.initializeCharts();
        this.bindEvents();
    }

    initializeCharts() {
        // 夏普比率圖表
        this.charts.sharpeRatio = new SharpeRatioChart('sharpeRatioChart', {
            plugins: {
                title: {
                    display: true,
                    text: '夏普比率對比',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        });

        // 最大回撤圖表
        this.charts.maxDrawdown = new MaxDrawdownChart('maxDrawdownChart', {
            plugins: {
                title: {
                    display: true,
                    text: '歷史最大回撤趨勢',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        });

        // 雷達圖
        this.charts.radar = new StrategyRadarChart('radarChart', {
            plugins: {
                title: {
                    display: true,
                    text: '策略綜合表現',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        });

        // 組合對比圖表
        this.charts.comparison = new StrategyComparisonChart('comparisonChart', 'bar', {
            plugins: {
                title: {
                    display: true,
                    text: '策略表現綜合對比',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        });
    }

    bindEvents() {
        // 圖表切換按鈕事件
        const chartButtons = document.querySelectorAll('.chart-btn');
        chartButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchChart(e.target.dataset.chart);

                // 更新按鈕狀態
                chartButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }

    switchChart(chartType) {
        console.log(`切換到: ${chartType} 圖表`);

        // 顯示/隱藏對應圖表容器
        Object.keys(this.charts).forEach(key => {
            const container = this.charts[key].container;
            if (container) {
                container.style.display = key === chartType ? 'block' : 'none';
            }
        });

        // 可以在這裡添加圖表數據更新邏輯
        this.updateChartData(chartType);
    }

    updateChartData(chartType) {
        // 根據當前顯示的圖表更新數據
        // 這個方法會在Dashboard刷新時被調用
        console.log(`更新 ${chartType} 圖表數據`);
    }

    updateAllCharts(strategyData) {
        if (!strategyData || !strategyData.strategies) return;

        const strategies = strategyData.strategies;

        // 更新所有圖表
        if (this.charts.sharpeRatio) {
            this.charts.sharpeRatio.update(strategies);
        }

        if (this.charts.maxDrawdown) {
            this.charts.maxDrawdown.update(strategyData);
        }

        if (this.charts.radar) {
            this.charts.radar.update(strategies);
        }

        if (this.charts.comparison) {
            this.charts.comparison.update(strategies, 'all');
        }
    }

    switchTheme(theme) {
        this.currentTheme = theme;

        // 更新Chart.js默認認配置
        const themeConfig = CHART_THEMES[theme];
        Chart.defaults.color = themeConfig.textColor;
        Chart.defaults.borderColor = themeConfig.gridColor;

        // 重新渲染所有圖表以應用新主題
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.chart) {
                chart.chart.options.plugins.legend.labels.color = themeConfig.textColor;
                chart.chart.options.scales.x.grid.color = themeConfig.gridColor;
                chart.chart.options.scales.y.grid.color = themeConfig.gridColor;
                chart.chart.options.scales.x.ticks.color = themeConfig.textColor;
                chart.chart.options.scales.y.ticks.color = themeConfig.textColor;
                chart.chart.update();
            }
        });
    }

    resize() {
        // 調整所有圖表大小
        Object.values(this.charts).forEach(chart => {
            if (chart && chart.chart) {
                chart.chart.resize();
            }
        });
    }

    destroy() {
        // 銷毀所有圖表
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// 導出圖表組件
window.SharpeRatioChart = SharpeRatioChart;
window.MaxDrawdownChart = MaxDrawdownChart;
window.StrategyRadarChart = StrategyRadarChart;
window.StrategyComparisonChart = StrategyComparisonChart;
window.ChartManager = ChartManager;

// 創建全局圖表管理器實例
window.chartManager = new ChartManager();