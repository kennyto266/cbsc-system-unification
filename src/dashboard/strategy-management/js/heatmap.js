/**
 * 个人策略管理Dashboard - 月度收益热力图
 * Personal Strategy Management Dashboard - Monthly Heatmap
 */

import { CHART_CONFIG, THEMES } from './constants.js';
import { formatDate, ChartUtils } from './utils.js';

/**
 * 月度收益热力图类
 */
class MonthlyHeatmap {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container element with id '${containerId}' not found`);
        }

        this.options = {
            // Color thresholds (for returns)
            excellent: 0.05,    // > 5%
            good: 0.0,          // 0% - 5%
            warning: -0.02,     // -2% - 0%
            poor: null,         // < -2%

            // Colors
            colors: {
                excellent: '#22c55e', // green-500
                good: '#84cc16',      // lime-500
                warning: '#eab308',   // yellow-500
                poor: '#ef4444'       // red-500
            },

            // Display options
            showLabels: true,
            showValues: true,
            cellPadding: 2,
            fontSize: 11,

            ...options
        };

        this.data = new Map();
        this.years = new Set();
        this.months = ['一月', '二月', '三月', '四月', '五月', '六月',
                      '七月', '八月', '九月', '十月', '十一月', '十二月'];

        this.initTheme();
        this.render();
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
                this.render();
            });
        }
    }

    /**
     * 应用主题
     * @param {string} theme - 主题名称
     */
    applyTheme(theme) {
        const isDark = theme === THEMES.DARK;

        this.theme = {
            background: isDark ? '#1a202c' : '#ffffff',
            border: isDark ? '#4a5568' : '#e2e8f0',
            text: isDark ? '#e2e8f0' : '#2d3748',
            textMuted: isDark ? '#a0aec0' : '#718096',
            hover: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.05)'
        };
    }

    /**
     * 添加策略数据
     * @param {string} strategyId - 策略ID
     * @param {Object} strategy - 策略对象
     * @param {Array} data - 收益率数据（包含日期和收益率）
     */
    addStrategy(strategyId, strategy, data) {
        if (!data || !Array.isArray(data)) {
            console.warn(`Invalid data for heatmap: ${strategyId}`);
            return;
        }

        // Process data into monthly format
        const monthlyData = this.processMonthlyData(data);
        this.data.set(strategyId, {
            strategy,
            data: monthlyData,
            color: this.getStrategyColor(strategyId)
        });

        // Update years set
        Object.keys(monthlyData).forEach(monthKey => {
            const year = monthKey.split('-')[0];
            this.years.add(year);
        });

        this.render();
    }

    /**
     * 移除策略
     * @param {string} strategyId - 策略ID
     */
    removeStrategy(strategyId) {
        this.data.delete(strategyId);

        // Recalculate years
        this.years.clear();
        this.data.forEach((item) => {
            Object.keys(item.data).forEach(monthKey => {
                const year = monthKey.split('-')[0];
                this.years.add(year);
            });
        });

        this.render();
    }

    /**
     * 处理数据为月度格式
     * @param {Array} data - 日度数据
     * @returns {Object} 月度数据
     */
    processMonthlyData(data) {
        const monthlyData = {};

        data.forEach(item => {
            const date = new Date(item.timestamp || item.date);
            const year = date.getFullYear();
            const month = date.getMonth(); // 0-11
            const monthKey = `${year}-${String(month + 1).padStart(2, '0')}`;

            if (!monthlyData[monthKey]) {
                monthlyData[monthKey] = {
                    returns: [],
                    count: 0,
                    total: 0
                };
            }

            const returnRate = item.daily_return || item.return || 0;
            monthlyData[monthKey].returns.push(returnRate);
            monthlyData[monthKey].count++;
        });

        // Calculate monthly returns
        Object.keys(monthlyData).forEach(monthKey => {
            const monthData = monthlyData[monthKey];

            if (monthData.returns.length > 0) {
                // Calculate cumulative return for the month
                const cumulativeReturn = monthData.returns.reduce((acc, r) => {
                    return (1 + acc) * (1 + r) - 1;
                }, 0);

                monthlyData[monthKey].monthlyReturn = cumulativeReturn;
                monthlyData[monthKey].avgDailyReturn =
                    monthData.returns.reduce((a, b) => a + b, 0) / monthData.returns.length;
                monthlyData[monthKey].volatility =
                    Math.sqrt(monthData.returns.reduce((sum, r) => {
                        const mean = monthData.avgDailyReturn;
                        return sum + Math.pow(r - mean, 2);
                    }, 0) / monthData.returns.length);
            }
        });

        return monthlyData;
    }

    /**
     * 获取策略颜色
     * @param {string} strategyId - 策略ID
     * @returns {string} 颜色值
     */
    getStrategyColor(strategyId) {
        const colors = CHART_CONFIG.COLORS;
        const index = Array.from(this.data.keys()).indexOf(strategyId);
        return colors[index % colors.length];
    }

    /**
     * 渲染热力图
     */
    render() {
        if (!this.container) return;

        const sortedYears = Array.from(this.years).sort();

        if (sortedYears.length === 0) {
            this.container.innerHTML = this.createEmptyState();
            return;
        }

        let html = `
            <div class="heatmap-container">
                ${this.options.showLabels ? this.createHeader(sortedYears) : ''}
                <div class="heatmap-grid-wrapper">
                    <div class="heatmap-grid" style="grid-template-columns: ${this.options.showLabels ? '60px' : ''} repeat(${sortedYears.length}, 1fr);">
        `;

        // Create rows
        this.months.forEach((month, monthIndex) => {
            html += `<div class="heatmap-row">`;

            // Month label
            if (this.options.showLabels) {
                html += `<div class="heatmap-label">${month}</div>`;
            }

            // Month cells for each year
            sortedYears.forEach(year => {
                const monthKey = `${year}-${String(monthIndex + 1).padStart(2, '0')}`;
                const cellData = this.getCellData(monthKey);
                html += this.createCell(monthKey, cellData);
            });

            html += `</div>`;
        });

        html += `
                    </div>
                </div>
                ${this.createLegend()}
                ${this.createStats()}
            </div>
        `;

        this.container.innerHTML = html;
        this.bindEvents();
    }

    /**
     * 创建标题行
     * @param {Array} years - 年份数组
     * @returns {string} HTML字符串
     */
    createHeader(years) {
        let html = '<div class="heatmap-header">';

        // Empty corner cell
        html += '<div class="heatmap-corner"></div>';

        // Year labels
        years.forEach(year => {
            html += `<div class="heatmap-label">${year}</div>`;
        });

        html += '</div>';
        return html;
    }

    /**
     * 获取单元格数据
     * @param {string} monthKey - 月份键
     * @returns {Object} 单元格数据
     */
    getCellData(monthKey) {
        const cellData = {
            monthlyReturns: [],
            avgReturn: 0,
            hasData: false
        };

        this.data.forEach((strategyInfo) => {
            const monthlyData = strategyInfo.data[monthKey];
            if (monthlyData && monthlyData.monthlyReturn !== undefined) {
                cellData.monthlyReturns.push({
                    value: monthlyData.monthlyReturn,
                    strategyId: Array.from(this.data.keys()).find(id =>
                        this.data.get(id) === strategyInfo
                    ),
                    strategyName: strategyInfo.strategy.name,
                    color: strategyInfo.color,
                    volatility: monthlyData.volatility
                });
            }
        });

        if (cellData.monthlyReturns.length > 0) {
            cellData.avgReturn = cellData.monthlyReturns.reduce((sum, r) => sum + r.value, 0) / cellData.monthlyReturns.length;
            cellData.hasData = true;
        }

        return cellData;
    }

    /**
     * 创建单元格
     * @param {string} monthKey - 月份键
     * @param {Object} cellData - 单元格数据
     * @returns {string} HTML字符串
     */
    createCell(monthKey, cellData) {
        if (!cellData.hasData) {
            return `<div class="heatmap-cell empty" data-month="${monthKey}"></div>`;
        }

        const returnRate = cellData.avgReturn;
        const color = this.getColorForValue(returnRate);
        const formattedValue = (returnRate * 100).toFixed(1);

        let content = '';
        if (this.options.showValues) {
            content = `<span class="heatmap-value">${formattedValue}%</span>`;
        }

        // Tooltip content
        const tooltipContent = this.createTooltipContent(monthKey, cellData);

        return `
            <div class="heatmap-cell ${this.getColorClass(returnRate)}"
                 data-month="${monthKey}"
                 style="background-color: ${color};"
                 title="${tooltipContent}">
                ${content}
            </div>
        `;
    }

    /**
     * 根据值获取颜色
     * @param {number} value - 收益率
     * @returns {string} 颜色
     */
    getColorForValue(value) {
        if (value > this.options.excellent) {
            return this.options.colors.excellent;
        } else if (value > this.options.good) {
            return this.options.colors.good;
        } else if (value > this.options.warning) {
            return this.options.colors.warning;
        } else {
            return this.options.colors.poor;
        }
    }

    /**
     * 获取颜色类名
     * @param {number} value - 收益率
     * @returns {string} 类名
     */
    getColorClass(value) {
        if (value > this.options.excellent) {
            return 'return-excellent';
        } else if (value > this.options.good) {
            return 'return-good';
        } else if (value > this.options.warning) {
            return 'return-warning';
        } else {
            return 'return-poor';
        }
    }

    /**
     * 创建工具提示内容
     * @param {string} monthKey - 月份键
     * @param {Object} cellData - 单元格数据
     * @returns {string} HTML字符串
     */
    createTooltipContent(monthKey, cellData) {
        const [year, month] = monthKey.split('-');
        const monthName = this.months[parseInt(month) - 1];

        let content = `${year}年${monthName}\n`;
        content += `平均收益: ${(cellData.avgReturn * 100).toFixed(2)}%\n`;
        content += `策略数量: ${cellData.monthlyReturns.length}\n\n`;

        if (cellData.monthlyReturns.length > 0) {
            content += '各策略收益:\n';
            cellData.monthlyReturns.forEach(r => {
                const formattedReturn = (r.value * 100).toFixed(2);
                content += `• ${r.strategyName}: ${formattedReturn}%\n`;
            });
        }

        return content;
    }

    /**
     * 创建图例
     * @returns {string} HTML字符串
     */
    createLegend() {
        return `
            <div class="heatmap-legend">
                <div class="legend-title">月度收益率</div>
                <div class="legend-items">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.options.colors.excellent}"></div>
                        <span>&gt; 5%</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.options.colors.good}"></div>
                        <span>0% - 5%</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.options.colors.warning}"></div>
                        <span>-2% - 0%</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: ${this.options.colors.poor}"></div>
                        <span>&lt; -2%</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 创建统计信息
     * @returns {string} HTML字符串
     */
    createStats() {
        const stats = this.calculateStats();

        return `
            <div class="heatmap-stats">
                <div class="stat-item">
                    <div class="stat-label">正收益月份</div>
                    <div class="stat-value">${stats.positiveMonths}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">负收益月份</div>
                    <div class="stat-value">${stats.negativeMonths}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">最佳月份</div>
                    <div class="stat-value">${(stats.bestMonth * 100).toFixed(1)}%</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">最差月份</div>
                    <div class="stat-value">${(stats.worstMonth * 100).toFixed(1)}%</div>
                </div>
            </div>
        `;
    }

    /**
     * 计算统计信息
     * @returns {Object} 统计数据
     */
    calculateStats() {
        let positiveMonths = 0;
        let negativeMonths = 0;
        let bestMonth = -Infinity;
        let worstMonth = Infinity;

        this.years.forEach(year => {
            this.months.forEach((month, monthIndex) => {
                const monthKey = `${year}-${String(monthIndex + 1).padStart(2, '0')}`;
                const cellData = this.getCellData(monthKey);

                if (cellData.hasData) {
                    if (cellData.avgReturn > 0) {
                        positiveMonths++;
                    } else {
                        negativeMonths++;
                    }

                    if (cellData.avgReturn > bestMonth) {
                        bestMonth = cellData.avgReturn;
                    }

                    if (cellData.avgReturn < worstMonth) {
                        worstMonth = cellData.avgReturn;
                    }
                }
            });
        });

        return {
            positiveMonths,
            negativeMonths,
            bestMonth: bestMonth === -Infinity ? 0 : bestMonth,
            worstMonth: worstMonth === Infinity ? 0 : worstMonth
        };
    }

    /**
     * 创建空状态
     * @returns {string} HTML字符串
     */
    createEmptyState() {
        return `
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <path d="M3 9h18M9 3v18"/>
                </svg>
                <h3>暂无数据</h3>
                <p>请添加策略以查看月度收益热力图</p>
            </div>
        `;
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        const cells = this.container.querySelectorAll('.heatmap-cell:not(.empty)');

        cells.forEach(cell => {
            cell.addEventListener('click', (e) => {
                const monthKey = e.currentTarget.dataset.month;
                if (monthKey) {
                    this.onCellClick(monthKey, e);
                }
            });

            cell.addEventListener('mouseenter', (e) => {
                e.currentTarget.style.transform = 'scale(1.1)';
                e.currentTarget.style.zIndex = '10';
            });

            cell.addEventListener('mouseleave', (e) => {
                e.currentTarget.style.transform = 'scale(1)';
                e.currentTarget.style.zIndex = '1';
            });
        });
    }

    /**
     * 单元格点击事件处理
     * @param {string} monthKey - 月份键
     * @param {Event} event - 事件对象
     */
    onCellClick(monthKey, event) {
        const cellData = this.getCellData(monthKey);

        // Emit event with month details
        if (typeof window !== 'undefined' && window.eventBus) {
            window.eventBus.emit('heatmap:cellClick', {
                monthKey,
                cellData,
                timestamp: Date.now()
            });
        }
    }

    /**
     * 导出数据为CSV
     * @returns {string} CSV字符串
     */
    exportToCSV() {
        const sortedYears = Array.from(this.years).sort();
        let csv = '月份,' + sortedYears.join(',') + '\n';

        this.months.forEach((month, monthIndex) => {
            const row = [month];
            sortedYears.forEach(year => {
                const monthKey = `${year}-${String(monthIndex + 1).padStart(2, '0')}`;
                const cellData = this.getCellData(monthKey);
                const value = cellData.hasData ? (cellData.avgReturn * 100).toFixed(2) : '';
                row.push(value);
            });
            csv += row.join(',') + '\n';
        });

        return csv;
    }

    /**
     * 更新颜色阈值
     * @param {Object} thresholds - 新的阈值
     */
    updateThresholds(thresholds) {
        Object.assign(this.options, thresholds);
        this.render();
    }

    /**
     * 切换数值显示
     */
    toggleValues() {
        this.options.showValues = !this.options.showValues;
        this.render();
    }

    /**
     * 切换标签显示
     */
    toggleLabels() {
        this.options.showLabels = !this.options.showLabels;
        this.render();
    }
}

export default MonthlyHeatmap;