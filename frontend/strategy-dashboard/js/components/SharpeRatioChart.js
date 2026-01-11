/**
 * Sharpe比率條形圖組件
 * 顯示各策略的Sharpe比率排名
 */
class SharpeRatioChart {
    constructor(containerElement, options = {}) {
        this.container = typeof containerElement === 'string'
            ? document.querySelector(containerElement)
            : containerElement;

        if (!this.container) {
            throw new Error('Container element not found');
        }

        // 默認配置
        this.options = {
            height: options.height || 400,
            animated: options.animated !== false,
            showValues: options.showValues !== false,
            colorScheme: options.colorScheme || 'default',
            onClick: options.onClick || null,
            onHover: options.onHover || null,
            ...options
        };

        // Chart.js實例
        this.chart = null;

        // 主題配色方案
        this.themes = {
            default: {
                primary: '#3498db',
                success: '#27ae60',
                warning: '#f39c12',
                danger: '#e74c3c',
                info: '#9b59b6',
                dark: '#34495e',
                light: '#ecf0f1',
                grid: '#e0e0e0'
            },
            dark: {
                primary: '#5dade2',
                success: '#52c77e',
                warning: '#f5b041',
                danger: '#ec7063',
                info: '#af7ac5',
                dark: '#ecf0f1',
                light: '#34495e',
                grid: '#4a5568'
            }
        };

        this.theme = this.themes[this.options.colorScheme] || this.themes.default;

        // 創建圖表容器
        this._createContainer();
    }

    /**
     * 創建圖表容器結構
     */
    _createContainer() {
        this.container.innerHTML = `
            <div class="sharpe-ratio-chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">策略Sharpe比率排名</h3>
                    <div class="chart-controls">
                        <button class="btn btn-sm btn-secondary" id="sort-btn">
                            <span class="icon">↕</span>
                            排序
                        </button>
                        <button class="btn btn-sm btn-secondary" id="refresh-btn">
                            <span class="icon">🔄</span>
                            刷新
                        </button>
                    </div>
                </div>
                <div class="chart-wrapper" style="height: ${this.options.height}px;">
                    <canvas id="sharpe-ratio-chart"></canvas>
                </div>
                <div class="chart-legend">
                    <div class="legend-item">
                        <span class="legend-color" style="background: ${this.theme.success}"></span>
                        <span class="legend-text">優秀 (SR ≥ 1.0)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color" style="background: ${this.theme.warning}"></span>
                        <span class="legend-text">良好 (SR ≥ 0.5)</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color" style="background: ${this.theme.danger}"></span>
                        <span class="legend-text">需改善 (SR < 0.5)</span>
                    </div>
                </div>
            </div>
        `;

        // 綁定控制按鈕事件
        this._bindEvents();
    }

    /**
     * 綁定事件監聽器
     */
    _bindEvents() {
        const sortBtn = this.container.querySelector('#sort-btn');
        const refreshBtn = this.container.querySelector('#refresh-btn');

        if (sortBtn) {
            sortBtn.addEventListener('click', () => {
                this._toggleSort();
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refresh();
            });
        }
    }

    /**
     * 創建Chart.js實例
     */
    createChart(data) {
        const canvas = this.container.querySelector('#sharpe-ratio-chart');
        const ctx = canvas.getContext('2d');

        // 準備圖表數據
        const chartData = this._prepareChartData(data);

        // 配置選項
        const config = {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: this.options.animated ? 750 : 0,
                    easing: 'easeInOutQuart'
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: false // 標題在HTML中已顯示
                    },
                    legend: {
                        display: false // 使用自定義圖例
                    },
                    tooltip: {
                        enabled: true,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: this.theme.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return [
                                    `Sharpe比率: ${value.toFixed(3)}`,
                                    `評級: ${this._getSharpeRating(value)}`
                                ];
                            },
                            afterLabel: (context) => {
                                const index = context.dataIndex;
                                const strategy = data[index];
                                if (strategy) {
                                    return [
                                        `勝率: ${(strategy.winRate * 100).toFixed(1)}%`,
                                        `最大回撤: ${(strategy.maxDrawdown * 100).toFixed(1)}%`
                                    ];
                                }
                                return [];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: this.theme.dark,
                            font: {
                                size: 12,
                                weight: 'normal'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: this.theme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.theme.dark,
                            font: {
                                size: 12
                            },
                            callback: (value) => value.toFixed(1)
                        },
                        title: {
                            display: true,
                            text: 'Sharpe比率',
                            color: this.theme.dark,
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0 && this.options.onClick) {
                        const index = elements[0].index;
                        const strategy = data[index];
                        this.options.onClick(strategy, index);
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                    if (elements.length > 0 && this.options.onHover) {
                        const index = elements[0].index;
                        const strategy = data[index];
                        this.options.onHover(strategy, index);
                    }
                }
            }
        };

        // 銷毀舊圖表
        if (this.chart) {
            this.chart.destroy();
        }

        // 創建新圖表
        this.chart = new Chart(ctx, config);

        // 保存原始數據
        this.originalData = [...data];
        this.currentData = data;
        this.sortOrder = 'desc'; // 默認降序排列
    }

    /**
     * 準備圖表數據
     */
    _prepareChartData(data) {
        const labels = data.map(s => s.name || s.strategyName);
        const values = data.map(s => s.sharpeRatio || 0);
        const colors = data.map(s => this._getSharpeColor(s.sharpeRatio || 0));

        return {
            labels: labels,
            datasets: [{
                label: 'Sharpe比率',
                data: values,
                backgroundColor: colors.map(c => c + '99'), // 添加透明度
                borderColor: colors,
                borderWidth: 2,
                borderRadius: 6,
                barPercentage: 0.7,
                categoryPercentage: 0.8
            }]
        };
    }

    /**
     * 根據Sharpe比率獲取顏色
     */
    _getSharpeColor(sharpeRatio) {
        if (sharpeRatio >= 1.0) return this.theme.success;
        if (sharpeRatio >= 0.5) return this.theme.warning;
        return this.theme.danger;
    }

    /**
     * 獲取Sharpe比率評級
     */
    _getSharpeRating(sharpeRatio) {
        if (sharpeRatio >= 1.5) return '卓越';
        if (sharpeRatio >= 1.0) return '優秀';
        if (sharpeRatio >= 0.5) return '良好';
        return '需改善';
    }

    /**
     * 切換排序
     */
    _toggleSort() {
        if (!this.currentData) return;

        const sortBtn = this.container.querySelector('#sort-btn');
        const icon = sortBtn.querySelector('.icon');

        // 切換排序順序
        this.sortOrder = this.sortOrder === 'desc' ? 'asc' : 'desc';

        // 更新按鈕圖標
        icon.textContent = this.sortOrder === 'desc' ? '↓' : '↑';

        // 排序數據
        const sortedData = [...this.currentData].sort((a, b) => {
            const valueA = a.sharpeRatio || 0;
            const valueB = b.sharpeRatio || 0;
            return this.sortOrder === 'desc' ? valueB - valueA : valueA - valueB;
        });

        // 更新圖表
        this.updateChart(sortedData, false); // 不動畫以保持排序可見
    }

    /**
     * 更新圖表數據
     */
    updateChart(data, animate = true) {
        if (!this.chart) {
            this.createChart(data);
            return;
        }

        const chartData = this._prepareChartData(data);

        // 更新數據
        this.chart.data = chartData;
        this.currentData = data;

        // 更新動畫設置
        if (!animate) {
            this.chart.options.animation.duration = 0;
        }

        // 渲染圖表
        this.chart.update();

        // 恢復動畫設置
        if (!animate) {
            this.chart.options.animation.duration = this.options.animated ? 750 : 0;
        }
    }

    /**
     * 添加新策略
     */
    addStrategy(strategy) {
        if (!this.currentData) {
            this.currentData = [];
        }

        this.currentData.push(strategy);
        this.updateChart(this.currentData);
    }

    /**
     * 移除策略
     */
    removeStrategy(strategyId) {
        if (!this.currentData) return;

        const index = this.currentData.findIndex(s =>
            s.id === strategyId || s.strategyId === strategyId
        );

        if (index !== -1) {
            this.currentData.splice(index, 1);
            this.updateChart(this.currentData);
        }
    }

    /**
     * 刷新圖表
     */
    async refresh() {
        const refreshBtn = this.container.querySelector('#refresh-btn');
        const icon = refreshBtn.querySelector('.icon');

        // 添加旋轉動畫
        icon.style.animation = 'spin 1s linear infinite';

        try {
            // 觸發刷新回調
            if (this.options.onRefresh) {
                await this.options.onRefresh();
            }

            // 模擬數據刷新
            if (this.currentData) {
                // 添加小的隨機變化以模擬實時更新
                const refreshedData = this.currentData.map(strategy => ({
                    ...strategy,
                    sharpeRatio: strategy.sharpeRatio + (Math.random() - 0.5) * 0.01
                }));

                this.updateChart(refreshedData);
            }
        } catch (error) {
            console.error('Failed to refresh chart:', error);
        } finally {
            // 移除動畫
            icon.style.animation = '';
        }
    }

    /**
     * 銷毀圖表
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    /**
     * 調整圖表大小
     */
    resize() {
        if (this.chart) {
            this.chart.resize();
        }
    }

    /**
     * 導出圖表為圖片
     */
    exportImage(format = 'png') {
        if (!this.chart) return null;

        return this.chart.toBase64Image(`image/${format}`);
    }
}

// 添加旋轉動畫樣式
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .sharpe-ratio-chart-container {
        background: #fff;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid #e0e0e0;
        background: #fafafa;
    }

    .chart-title {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #2c3e50;
    }

    .chart-controls {
        display: flex;
        gap: 8px;
    }

    .chart-wrapper {
        padding: 20px;
        position: relative;
    }

    .chart-legend {
        display: flex;
        justify-content: center;
        gap: 24px;
        padding: 16px 20px;
        background: #fafafa;
        border-top: 1px solid #e0e0e0;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: #666;
    }

    .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 2px;
    }

    .btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border: 1px solid #ddd;
        border-radius: 6px;
        background: #fff;
        color: #666;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .btn:hover {
        background: #f5f5f5;
        border-color: #999;
    }

    .btn-sm {
        padding: 4px 8px;
        font-size: 12px;
    }

    .btn-secondary {
        background: #f8f9fa;
        border-color: #dee2e6;
        color: #6c757d;
    }

    .btn-secondary:hover {
        background: #e9ecef;
        border-color: #adb5bd;
    }

    .icon {
        font-size: 14px;
    }
`;
document.head.appendChild(style);