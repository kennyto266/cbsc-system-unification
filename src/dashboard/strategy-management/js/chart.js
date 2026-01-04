/**
 * 个人策略管理Dashboard - 图表基础类
 * Personal Strategy Management Dashboard - Chart Base Class
 */

import { CHART_CONFIG, THEMES } from './constants.js';

/**
 * 图表基类
 */
class BaseChart {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`Canvas element with id '${canvasId}' not found`);
        }

        this.chart = null;
        this.options = {
            responsive: true,
            maintainAspectRatio: false,
            ...CHART_CONFIG.COMMON,
            ...options
        };

        this.initTheme();
        this.setupContainer();
    }

    /**
     * 初始化主题
     */
    initTheme() {
        const currentTheme = document.body.getAttribute('data-theme') || THEMES.LIGHT;
        this.applyTheme(currentTheme);

        // Listen for theme changes
        if (typeof window !== 'undefined') {
            window.addEventListener('themeChanged', (e) => {
                this.applyTheme(e.detail.theme);
                if (this.chart) {
                    this.update();
                }
            });
        }
    }

    /**
     * 应用主题
     * @param {string} theme - 主题名称
     */
    applyTheme(theme) {
        const isDark = theme === THEMES.DARK;

        this.colors = {
            text: isDark ? '#e2e8f0' : '#2d3748',
            grid: isDark ? '#2d3748' : '#f7fafc',
            background: isDark ? '#1a202c' : '#ffffff',
            primary: CHART_CONFIG.COLORS[0],
            success: CHART_CONFIG.COLORS[1],
            warning: CHART_CONFIG.COLORS[2],
            error: CHART_CONFIG.COLORS[3],
            ...this.getCustomColors(isDark)
        };

        // Update Chart.js defaults
        if (typeof Chart !== 'undefined') {
            Chart.defaults.color = this.colors.text;
            Chart.defaults.borderColor = this.colors.grid;
        }
    }

    /**
     * 获取自定义颜色（子类可重写）
     * @param {boolean} isDark - 是否为深色主题
     * @returns {Object} 自定义颜色对象
     */
    getCustomColors(isDark) {
        return {};
    }

    /**
     * 设置容器
     */
    setupContainer() {
        // Add loading state class
        this.canvas.parentElement.classList.add('chart-container');
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        if (this.canvas.parentElement) {
            this.canvas.parentElement.classList.add('loading');
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        if (this.canvas.parentElement) {
            this.canvas.parentElement.classList.remove('loading');
        }
    }

    /**
     * 销毁图表
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    /**
     * 更新图表
     */
    update() {
        if (this.chart) {
            this.chart.update();
        }
    }

    /**
     * 导出图表为图片
     * @param {string} format - 图片格式
     * @param {number} quality - 图片质量
     * @returns {string} 图片URL
     */
    exportImage(format = 'png', quality = 1) {
        if (this.chart) {
            return this.chart.toBase64Image(format, quality);
        }
        return null;
    }

    /**
     * 获取图表数据URL
     * @returns {string} 数据URL
     */
    getDataURL() {
        if (this.chart) {
            return this.chart.toBase64Image();
        }
        return null;
    }

    /**
     * 设置图表标题
     * @param {string} title - 标题
     */
    setTitle(title) {
        if (this.chart && this.chart.options.plugins.title) {
            this.chart.options.plugins.title.text = title;
            this.update();
        }
    }

    /**
     * 添加数据集
     * @param {Object} dataset - 数据集配置
     */
    addDataset(dataset) {
        if (this.chart) {
            this.chart.data.datasets.push(dataset);
            this.update();
        }
    }

    /**
     * 移除数据集
     * @param {number} index - 数据集索引
     */
    removeDataset(index) {
        if (this.chart && this.chart.data.datasets.length > index) {
            this.chart.data.datasets.splice(index, 1);
            this.update();
        }
    }

    /**
     * 更新数据集
     * @param {number} index - 数据集索引
     * @param {Object} data - 新数据
     */
    updateDataset(index, data) {
        if (this.chart && this.chart.data.datasets[index]) {
            Object.assign(this.chart.data.datasets[index], data);
            this.update();
        }
    }

    /**
     * 重置缩放
     */
    resetZoom() {
        if (this.chart && this.chart.resetZoom) {
            this.chart.resetZoom();
        }
    }
}

/**
 * 线性图表类
 */
class LineChart extends BaseChart {
    constructor(canvasId, options = {}) {
        super(canvasId, {
            type: 'line',
            ...CHART_CONFIG.LINE_CHART,
            ...options
        });
    }

    render(data, labels = null, datasetOptions = {}) {
        this.showLoading();

        const defaultDataset = {
            borderWidth: 2,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderWidth: 2,
            borderColor: this.colors.primary,
            backgroundColor: this.hexToRgba(this.colors.primary, 0.1),
            ...datasetOptions
        };

        const datasets = Array.isArray(data.datasets)
            ? data.datasets.map(ds => ({ ...defaultDataset, ...ds }))
            : [{ ...defaultDataset, data }];

        this.destroy();

        this.chart = new Chart(this.canvas, {
            type: 'line',
            data: {
                labels: labels || data.labels || [],
                datasets
            },
            options: {
                ...this.options,
                scales: {
                    x: {
                        grid: {
                            color: this.colors.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.colors.text
                        }
                    },
                    y: {
                        grid: {
                            color: this.colors.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.colors.text,
                            callback: this.formatYAxis.bind(this)
                        }
                    }
                },
                plugins: {
                    ...this.options.plugins,
                    tooltip: {
                        ...this.options.plugins.tooltip,
                        callbacks: {
                            label: this.formatTooltip.bind(this)
                        }
                    }
                }
            }
        });

        this.hideLoading();
    }

    /**
     * 格式化Y轴标签（子类可重写）
     * @param {number} value - 值
     * @returns {string} 格式化后的标签
     */
    formatYAxis(value) {
        return value;
    }

    /**
     * 格式化工具提示（子类可重写）
     * @param {Object} context - 上下文
     * @returns {string} 格式化后的标签
     */
    formatTooltip(context) {
        return `${context.dataset.label}: ${context.parsed.y}`;
    }
}

/**
 * 柱状图类
 */
class BarChart extends BaseChart {
    constructor(canvasId, options = {}) {
        super(canvasId, {
            type: 'bar',
            ...options
        });
    }

    render(data, labels = null, datasetOptions = {}) {
        this.showLoading();

        const defaultDataset = {
            borderWidth: 0,
            borderRadius: 4,
            backgroundColor: this.colors.primary,
            ...datasetOptions
        };

        const datasets = Array.isArray(data.datasets)
            ? data.datasets.map(ds => ({ ...defaultDataset, ...ds }))
            : [{ ...defaultDataset, data }];

        this.destroy();

        this.chart = new Chart(this.canvas, {
            type: 'bar',
            data: {
                labels: labels || data.labels || [],
                datasets
            },
            options: {
                ...this.options,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: this.colors.text
                        }
                    },
                    y: {
                        grid: {
                            color: this.colors.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.colors.text,
                            callback: this.formatYAxis.bind(this)
                        }
                    }
                }
            }
        });

        this.hideLoading();
    }

    formatYAxis(value) {
        return value;
    }
}

/**
 * 饼图类
 */
class PieChart extends BaseChart {
    constructor(canvasId, options = {}) {
        super(canvasId, {
            type: 'pie',
            ...options
        });
    }

    render(data, labels = null, datasetOptions = {}) {
        this.showLoading();

        const defaultDataset = {
            borderWidth: 2,
            borderColor: this.colors.background,
            backgroundColor: CHART_CONFIG.COLORS,
            ...datasetOptions
        };

        this.destroy();

        this.chart = new Chart(this.canvas, {
            type: 'pie',
            data: {
                labels: labels || data.labels || [],
                datasets: [{ ...defaultDataset, data: data.data || data }]
            },
            options: {
                ...this.options,
                plugins: {
                    ...this.options.plugins,
                    legend: {
                        position: 'right',
                        labels: {
                            color: this.colors.text,
                            padding: 20,
                            usePointStyle: true
                        }
                    }
                }
            }
        });

        this.hideLoading();
    }
}

/**
 * 雷达图类
 */
class RadarChart extends BaseChart {
    constructor(canvasId, options = {}) {
        super(canvasId, {
            type: 'radar',
            ...options
        });
    }

    render(data, labels = null, datasetOptions = {}) {
        this.showLoading();

        const defaultDataset = {
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            backgroundColor: this.hexToRgba(this.colors.primary, 0.2),
            borderColor: this.colors.primary,
            ...datasetOptions
        };

        const datasets = Array.isArray(data.datasets)
            ? data.datasets.map(ds => ({ ...defaultDataset, ...ds }))
            : [{ ...defaultDataset, data }];

        this.destroy();

        this.chart = new Chart(this.canvas, {
            type: 'radar',
            data: {
                labels: labels || data.labels || [],
                datasets
            },
            options: {
                ...this.options,
                scales: {
                    r: {
                        angleLines: {
                            color: this.colors.grid
                        },
                        grid: {
                            color: this.colors.grid
                        },
                        pointLabels: {
                            color: this.colors.text
                        },
                        ticks: {
                            color: this.colors.text,
                            backdropColor: 'transparent'
                        }
                    }
                }
            }
        });

        this.hideLoading();
    }
}

// 工具函数
const ChartUtils = {
    /**
     * 十六进制颜色转RGBA
     * @param {string} hex - 十六进制颜色
     * @param {number} alpha - 透明度
     * @returns {string} RGBA颜色
     */
    hexToRgba(hex, alpha) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    },

    /**
     * 生成渐变色
     * @param {string} startColor - 起始颜色
     * @param {string} endColor - 结束颜色
     * @param {number} steps - 步数
     * @returns {Array} 渐变色数组
     */
    generateGradient(startColor, endColor, steps) {
        const start = this.hexToRgb(startColor);
        const end = this.hexToRgb(endColor);
        const gradient = [];

        for (let i = 0; i < steps; i++) {
            const ratio = i / (steps - 1);
            const r = Math.round(start.r + (end.r - start.r) * ratio);
            const g = Math.round(start.g + (end.g - start.g) * ratio);
            const b = Math.round(start.b + (end.b - start.b) * ratio);
            gradient.push(`rgb(${r}, ${g}, ${b})`);
        }

        return gradient;
    },

    /**
     * 十六进制颜色转RGB
     * @param {string} hex - 十六进制颜色
     * @returns {Object} RGB对象
     */
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    },

    /**
     * 格式化数字
     * @param {number} value - 数值
     * @param {number} decimals - 小数位数
     * @returns {string} 格式化后的数字
     */
    formatNumber(value, decimals = 2) {
        if (value === null || value === undefined) return '--';
        return Number(value).toFixed(decimals);
    },

    /**
     * 格式化百分比
     * @param {number} value - 小数值
     * @param {number} decimals - 小数位数
     * @returns {string} 百分比字符串
     */
    formatPercentage(value, decimals = 2) {
        if (value === null || value === undefined) return '--%';
        return `${(value * 100).toFixed(decimals)}%`;
    }
};

// 添加工具函数到基类原型
BaseChart.prototype.hexToRgba = ChartUtils.hexToRgba;

// 导出类和工具
export {
    BaseChart,
    LineChart,
    BarChart,
    PieChart,
    RadarChart,
    ChartUtils
};

export default {
    BaseChart,
    LineChart,
    BarChart,
    PieChart,
    RadarChart,
    ChartUtils
};