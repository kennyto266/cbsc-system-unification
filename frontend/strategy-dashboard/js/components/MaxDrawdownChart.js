/**
 * 最大回撤折線圖組件
 * 展示策略的風險趨勢
 */
class MaxDrawdownChart {
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
            showDataPoints: options.showDataPoints !== false,
            fillArea: options.fillArea !== false,
            showGrid: options.showGrid !== false,
            colorScheme: options.colorScheme || 'default',
            onStrategyToggle: options.onStrategyToggle || null,
            onTimeRangeChange: options.onTimeRangeChange || null,
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

        // 策略顏色映射
        this.strategyColors = new Map();

        // 創建圖表容器
        this._createContainer();
    }

    /**
     * 創建圖表容器結構
     */
    _createContainer() {
        this.container.innerHTML = `
            <div class="max-drawdown-chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">策略最大回撤趨勢</h3>
                    <div class="chart-controls">
                        <select class="time-range-select" id="time-range-select">
                            <option value="1M">1個月</option>
                            <option value="3M">3個月</option>
                            <option value="6M">6個月</option>
                            <option value="1Y" selected>1年</option>
                            <option value="ALL">全部</option>
                        </select>
                        <button class="btn btn-sm btn-secondary" id="toggle-points-btn">
                            <span class="icon">⬤</span>
                            數據點
                        </button>
                        <button class="btn btn-sm btn-secondary" id="refresh-btn">
                            <span class="icon">🔄</span>
                            刷新
                        </button>
                    </div>
                </div>
                <div class="chart-wrapper" style="height: ${this.options.height}px;">
                    <canvas id="max-drawdown-chart"></canvas>
                </div>
                <div class="chart-footer">
                    <div class="strategy-toggles" id="strategy-toggles">
                        <!-- 策略切換按鈕將在這裡生成 -->
                    </div>
                    <div class="chart-info">
                        <span class="info-item">
                            <span class="info-label">平均回撤:</span>
                            <span class="info-value" id="avg-drawdown">-</span>
                        </span>
                        <span class="info-item">
                            <span class="info-label">最大回撤:</span>
                            <span class="info-value" id="max-drawdown">-</span>
                        </span>
                        <span class="info-item">
                            <span class="info-label">更新時間:</span>
                            <span class="info-value" id="update-time">-</span>
                        </span>
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
        const timeRangeSelect = this.container.querySelector('#time-range-select');
        const togglePointsBtn = this.container.querySelector('#toggle-points-btn');
        const refreshBtn = this.container.querySelector('#refresh-btn');

        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', (e) => {
                this._handleTimeRangeChange(e.target.value);
            });
        }

        if (togglePointsBtn) {
            togglePointsBtn.addEventListener('click', () => {
                this._toggleDataPoints();
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
    createChart(historicalData) {
        const canvas = this.container.querySelector('#max-drawdown-chart');
        const ctx = canvas.getContext('2d');

        // 準備圖表數據
        const chartData = this._prepareChartData(historicalData);

        // 配置選項
        const config = {
            type: 'line',
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
                        display: false
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            color: this.theme.dark,
                            font: {
                                size: 12
                            }
                        }
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
                            title: (context) => {
                                const date = context[0].label;
                                return `日期: ${date}`;
                            },
                            label: (context) => {
                                const value = context.parsed.y;
                                const strategyName = context.dataset.label;
                                return [
                                    `${strategyName}: ${(value * 100).toFixed(2)}%`,
                                    `風險等級: ${this._getRiskLevel(value)}`
                                ];
                            },
                            afterBody: (context) => {
                                const index = context[0].dataIndex;
                                const additionalInfo = this._getAdditionalInfo(index);
                                if (additionalInfo) {
                                    return [`\n市場狀況: ${additionalInfo}`];
                                }
                                return [];
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: this.options.showGrid,
                            color: this.theme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.theme.dark,
                            font: {
                                size: 11
                            },
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            display: this.options.showGrid,
                            color: this.theme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: this.theme.dark,
                            font: {
                                size: 12
                            },
                            callback: (value) => `${(value * 100).toFixed(1)}%`
                        },
                        title: {
                            display: true,
                            text: '最大回撤',
                            color: this.theme.dark,
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        }
                    }
                },
                elements: {
                    line: {
                        tension: 0.4,
                        borderWidth: 2
                    },
                    point: {
                        radius: this.options.showDataPoints ? 4 : 0,
                        hoverRadius: 6,
                        hitRadius: 10
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const datasetIndex = elements[0].datasetIndex;
                        const index = elements[0].index;
                        const dataset = chartData.datasets[datasetIndex];
                        const date = chartData.labels[index];
                        const value = dataset.data[index];

                        // 觸發點擊事件
                        if (this.options.onClick) {
                            this.options.onClick({
                                strategyName: dataset.label,
                                date: date,
                                drawdown: value,
                                datasetIndex,
                                index
                            });
                        }
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                    if (elements.length > 0 && this.options.onHover) {
                        const datasetIndex = elements[0].datasetIndex;
                        const index = elements[0].index;
                        const dataset = chartData.datasets[datasetIndex];
                        const date = chartData.labels[index];
                        const value = dataset.data[index];

                        this.options.onHover({
                            strategyName: dataset.label,
                            date: date,
                            drawdown: value
                        });
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

        // 創建策略切換按鈕
        this._createStrategyToggles(chartData.datasets);

        // 更新統計信息
        this._updateStatistics(chartData.datasets);

        // 保存數據
        this.historicalData = historicalData;
        this.currentTimeRange = '1Y';
    }

    /**
     * 準備圖表數據
     */
    _prepareChartData(historicalData) {
        const datasets = historicalData.strategies.map((strategy, index) => {
            // 獲取或生成策略顏色
            let color = this.strategyColors.get(strategy.name);
            if (!color) {
                color = this._getStrategyColor(index);
                this.strategyColors.set(strategy.name, color);
            }

            return {
                label: strategy.name,
                data: strategy.drawdowns.map(d => d / 100), // 轉換為小數
                borderColor: color,
                backgroundColor: this.options.fillArea ? color + '20' : 'transparent',
                fill: this.options.fillArea,
                borderWidth: 2,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                hidden: false
            };
        });

        return {
            labels: historicalData.dates,
            datasets: datasets
        };
    }

    /**
     * 獲取策略顏色
     */
    _getStrategyColor(index) {
        const colors = [
            this.theme.primary,
            this.theme.success,
            this.theme.warning,
            this.theme.danger,
            this.theme.info,
            '#e67e22',
            '#3498db',
            '#2ecc71'
        ];
        return colors[index % colors.length];
    }

    /**
     * 創建策略切換按鈕
     */
    _createStrategyToggles(datasets) {
        const container = this.container.querySelector('#strategy-toggles');
        container.innerHTML = '';

        datasets.forEach((dataset, index) => {
            const toggle = document.createElement('label');
            toggle.className = 'strategy-toggle';
            toggle.innerHTML = `
                <input type="checkbox"
                       class="toggle-checkbox"
                       ${!dataset.hidden ? 'checked' : ''}
                       data-dataset-index="${index}">
                <span class="toggle-indicator" style="background: ${dataset.borderColor}"></span>
                <span class="toggle-label">${dataset.label}</span>
            `;

            toggle.addEventListener('change', (e) => {
                this._toggleDataset(index, e.target.checked);
            });

            container.appendChild(toggle);
        });
    }

    /**
     * 切換數據集顯示
     */
    _toggleDataset(index, visible) {
        if (this.chart) {
            const dataset = this.chart.data.datasets[index];
            dataset.hidden = !visible;
            this.chart.update();
        }
    }

    /**
     * 獲取風險等級
     */
    _getRiskLevel(drawdown) {
        const percentage = drawdown * 100;
        if (percentage < 5) return '低風險';
        if (percentage < 10) return '中等風險';
        if (percentage < 20) return '高風險';
        return '極高風險';
    }

    /**
     * 獲取額外信息
     */
    _getAdditionalInfo(index) {
        // 這裡可以根據日期獲取市場事件等額外信息
        const events = {
            '2024-01-15': '市場震盪',
            '2024-03-10': '政策調整',
            '2024-06-20': '季末波動',
            '2024-09-05': '技術調整',
            '2024-11-15': '年底效應'
        };

        return events[this.chart.data.labels[index]] || null;
    }

    /**
     * 更新統計信息
     */
    _updateStatistics(datasets) {
        let totalDrawdown = 0;
        let maxDrawdown = 0;
        let count = 0;

        datasets.forEach(dataset => {
            if (!dataset.hidden) {
                dataset.data.forEach(value => {
                    totalDrawdown += value;
                    maxDrawdown = Math.max(maxDrawdown, value);
                    count++;
                });
            }
        });

        const avgDrawdown = count > 0 ? totalDrawdown / count : 0;

        this.container.querySelector('#avg-drawdown').textContent = `${(avgDrawdown * 100).toFixed(2)}%`;
        this.container.querySelector('#max-drawdown').textContent = `${(maxDrawdown * 100).toFixed(2)}%`;
        this.container.querySelector('#update-time').textContent = new Date().toLocaleTimeString();
    }

    /**
     * 處理時間範圍變化
     */
    _handleTimeRangeChange(range) {
        this.currentTimeRange = range;

        // 過濾數據
        const filteredData = this._filterDataByTimeRange(this.historicalData, range);

        // 更新圖表
        if (this.chart) {
            this.chart.data.labels = filteredData.dates;
            this.chart.data.datasets.forEach((dataset, index) => {
                dataset.data = filteredData.strategies[index].drawdowns.map(d => d / 100);
            });
            this.chart.update();
        }

        // 觸發回調
        if (this.options.onTimeRangeChange) {
            this.options.onTimeRangeChange(range, filteredData);
        }
    }

    /**
     * 根據時間範圍過濾數據
     */
    _filterDataByTimeRange(data, range) {
        const now = new Date();
        let startDate = new Date();

        switch (range) {
            case '1M':
                startDate.setMonth(now.getMonth() - 1);
                break;
            case '3M':
                startDate.setMonth(now.getMonth() - 3);
                break;
            case '6M':
                startDate.setMonth(now.getMonth() - 6);
                break;
            case '1Y':
                startDate.setFullYear(now.getFullYear() - 1);
                break;
            case 'ALL':
                return data;
        }

        // 找到開始索引
        const startIndex = data.dates.findIndex(date => new Date(date) >= startDate);

        if (startIndex === -1) return data;

        // 過濾數據
        const filteredDates = data.dates.slice(startIndex);
        const filteredStrategies = data.strategies.map(strategy => ({
            name: strategy.name,
            drawdowns: strategy.drawdowns.slice(startIndex)
        }));

        return {
            dates: filteredDates,
            strategies: filteredStrategies
        };
    }

    /**
     * 切換數據點顯示
     */
    _toggleDataPoints() {
        this.options.showDataPoints = !this.options.showDataPoints;

        const btn = this.container.querySelector('#toggle-points-btn');
        const icon = btn.querySelector('.icon');

        if (this.options.showDataPoints) {
            icon.style.opacity = '1';
            this.chart.data.datasets.forEach(dataset => {
                dataset.pointRadius = 4;
            });
        } else {
            icon.style.opacity = '0.3';
            this.chart.data.datasets.forEach(dataset => {
                dataset.pointRadius = 0;
            });
        }

        this.chart.update();
    }

    /**
     * 更新圖表數據
     */
    updateChart(newData, animate = true) {
        if (!this.chart) {
            this.createChart(newData);
            return;
        }

        const chartData = this._prepareChartData(newData);

        // 更新數據
        this.chart.data = chartData;
        this.historicalData = newData;

        // 更新統計
        this._updateStatistics(chartData.datasets);

        // 重新創建切換按鈕
        this._createStrategyToggles(chartData.datasets);

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
    addStrategy(strategyData) {
        if (!this.historicalData) return;

        this.historicalData.strategies.push(strategyData);
        this.updateChart(this.historicalData);
    }

    /**
     * 移除策略
     */
    removeStrategy(strategyName) {
        if (!this.historicalData) return;

        const index = this.historicalData.strategies.findIndex(s => s.name === strategyName);
        if (index !== -1) {
            this.historicalData.strategies.splice(index, 1);
            this.updateChart(this.historicalData);
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
            if (this.historicalData) {
                // 這裡應該調用API獲取最新數據
                console.log('Refreshing max drawdown data...');
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
        this.strategyColors.clear();
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

// 添加樣式
const style = document.createElement('style');
style.textContent = `
    .max-drawdown-chart-container {
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
        gap: 12px;
        align-items: center;
    }

    .time-range-select {
        padding: 6px 10px;
        border: 1px solid #ddd;
        border-radius: 6px;
        background: #fff;
        color: #666;
        font-size: 13px;
        cursor: pointer;
    }

    .chart-wrapper {
        padding: 20px;
        position: relative;
    }

    .chart-footer {
        padding: 16px 20px;
        background: #fafafa;
        border-top: 1px solid #e0e0e0;
    }

    .strategy-toggles {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 16px;
    }

    .strategy-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        font-size: 13px;
        color: #666;
    }

    .toggle-checkbox {
        cursor: pointer;
    }

    .toggle-indicator {
        width: 12px;
        height: 12px;
        border-radius: 2px;
        border: 2px solid #fff;
        box-shadow: 0 0 0 1px #ddd;
        transition: all 0.2s;
    }

    .toggle-checkbox:checked + .toggle-indicator {
        box-shadow: 0 0 0 1px #999;
    }

    .toggle-checkbox:not(:checked) + .toggle-indicator {
        opacity: 0.3;
    }

    .chart-info {
        display: flex;
        gap: 24px;
        font-size: 13px;
    }

    .info-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .info-label {
        color: #666;
    }

    .info-value {
        font-weight: 600;
        color: #2c3e50;
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

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);