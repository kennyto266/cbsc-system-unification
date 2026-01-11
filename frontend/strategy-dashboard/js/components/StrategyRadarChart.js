/**
 * 策略雷達圖組件
 * 多維度策略性能對比
 */
class StrategyRadarChart {
    constructor(containerElement, options = {}) {
        this.container = typeof containerElement === 'string'
            ? document.querySelector(containerElement)
            : containerElement;

        if (!this.container) {
            throw new Error('Container element not found');
        }

        // 默認配置
        this.options = {
            height: options.height || 450,
            animated: options.animated !== false,
            showPoints: options.showPoints !== false,
            fillArea: options.fillArea !== false,
            showLegend: options.showLegend !== false,
            maxStrategies: options.maxStrategies || 5,
            colorScheme: options.colorScheme || 'default',
            metrics: options.metrics || [
                'sharpeRatio',
                'maxDrawdown',
                'winRate',
                'profitFactor',
                'volatilityControl'
            ],
            onStrategySelect: options.onStrategySelect || null,
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

        // 指標配置
        this.metricConfig = {
            sharpeRatio: {
                label: 'Sharpe比率',
                weight: 25,
                scale: { min: 0, max: 100 },
                transform: (value) => Math.min(value * 25, 100),
                description: '風險調整後收益'
            },
            maxDrawdown: {
                label: '回撤控制',
                weight: 20,
                scale: { min: 0, max: 100 },
                transform: (value) => (1 - value) * 100,
                description: '最大回撤控制能力'
            },
            winRate: {
                label: '勝率',
                weight: 20,
                scale: { min: 0, max: 100 },
                transform: (value) => value * 100,
                description: '交易成功率'
            },
            profitFactor: {
                label: '盈利因子',
                weight: 20,
                scale: { min: 0, max: 100 },
                transform: (value) => Math.min(value * 20, 100),
                description: '總盈利/總虧損'
            },
            volatilityControl: {
                label: '波動率控制',
                weight: 15,
                scale: { min: 0, max: 100 },
                transform: (value) => value * 100,
                description: '波動率穩定性'
            }
        };

        // 創建圖表容器
        this._createContainer();
    }

    /**
     * 創建圖表容器結構
     */
    _createContainer() {
        this.container.innerHTML = `
            <div class="strategy-radar-chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">策略多維度性能對比</h3>
                    <div class="chart-controls">
                        <button class="btn btn-sm btn-secondary" id="metrics-btn">
                            <span class="icon">⚙️</span>
                            指標設置
                        </button>
                        <button class="btn btn-sm btn-secondary" id="compare-btn">
                            <span class="icon">📊</span>
                            對比模式
                        </button>
                        <button class="btn btn-sm btn-secondary" id="refresh-btn">
                            <span class="icon">🔄</span>
                            刷新
                        </button>
                    </div>
                </div>
                <div class="chart-wrapper" style="height: ${this.options.height}px;">
                    <canvas id="strategy-radar-chart"></canvas>
                </div>
                <div class="chart-footer">
                    <div class="strategy-selector">
                        <span class="selector-label">選擇策略（最多${this.options.maxStrategies}個）:</span>
                        <div class="selector-chips" id="strategy-chips">
                            <!-- 策略選擇器將在這裡生成 -->
                        </div>
                    </div>
                    <div class="radar-info">
                        <div class="info-grid">
                            <div class="info-item">
                                <span class="info-label">綜合評分:</span>
                                <span class="info-value" id="overall-score">-</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">最佳策略:</span>
                                <span class="info-value" id="best-strategy">-</span>
                            </div>
                            <div class="info-item">
                                <span class="info-label">更新時間:</span>
                                <span class="info-value" id="update-time">-</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="metrics-panel" id="metrics-panel" style="display: none;">
                    <div class="panel-header">
                        <h4>指標配置</h4>
                        <button class="close-btn" id="close-metrics">✕</button>
                    </div>
                    <div class="panel-content">
                        <div class="metrics-list" id="metrics-list">
                            <!-- 指標列表將在這裡生成 -->
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 綁定事件
        this._bindEvents();

        // 創建指標列表
        this._createMetricsList();
    }

    /**
     * 綁定事件監聽器
     */
    _bindEvents() {
        const metricsBtn = this.container.querySelector('#metrics-btn');
        const compareBtn = this.container.querySelector('#compare-btn');
        const refreshBtn = this.container.querySelector('#refresh-btn');
        const closeMetricsBtn = this.container.querySelector('#close-metrics');

        if (metricsBtn) {
            metricsBtn.addEventListener('click', () => {
                this._toggleMetricsPanel();
            });
        }

        if (compareBtn) {
            compareBtn.addEventListener('click', () => {
                this._toggleCompareMode();
            });
        }

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refresh();
            });
        }

        if (closeMetricsBtn) {
            closeMetricsBtn.addEventListener('click', () => {
                this._toggleMetricsPanel();
            });
        }
    }

    /**
     * 創建指標列表
     */
    _createMetricsList() {
        const container = this.container.querySelector('#metrics-list');
        container.innerHTML = '';

        this.options.metrics.forEach(metric => {
            const config = this.metricConfig[metric];
            if (!config) return;

            const item = document.createElement('div');
            item.className = 'metric-item';
            item.innerHTML = `
                <label class="metric-checkbox">
                    <input type="checkbox"
                           value="${metric}"
                           checked
                           data-metric="${metric}">
                    <span class="metric-label">${config.label}</span>
                    <span class="metric-desc">${config.description}</span>
                    <span class="metric-weight">權重: ${config.weight}%</span>
                </label>
            `;

            const checkbox = item.querySelector('input');
            checkbox.addEventListener('change', (e) => {
                this._updateMetrics(e.target.value, e.target.checked);
            });

            container.appendChild(item);
        });
    }

    /**
     * 創建Chart.js實例
     */
    createChart(strategies) {
        const canvas = this.container.querySelector('#strategy-radar-chart');
        const ctx = canvas.getContext('2d');

        // 準備圖表數據
        const chartData = this._prepareChartData(strategies);

        // 配置選項
        const config = {
            type: 'radar',
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
                        display: this.options.showLegend,
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
                            label: (context) => {
                                const metric = context.label;
                                const value = context.parsed.r;
                                const config = this.metricConfig[metric.replace(/\s+/g, '')];

                                if (config) {
                                    return [
                                        `${metric}: ${value.toFixed(1)}`,
                                        `原始值: ${this._getOriginalValue(metric, strategies[context.datasetIndex]).toFixed(3)}`
                                    ];
                                }
                                return `${metric}: ${value.toFixed(1)}`;
                            },
                            afterLabel: (context) => {
                                const datasetIndex = context.datasetIndex;
                                const strategy = strategies[datasetIndex];
                                return `\n綜合評分: ${this._calculateOverallScore(strategy).toFixed(1)}`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        angleLines: {
                            color: this.theme.grid,
                            lineDash: [3, 3]
                        },
                        grid: {
                            color: this.theme.grid,
                            lineDash: [3, 3]
                        },
                        pointLabels: {
                            color: this.theme.dark,
                            font: {
                                size: 13,
                                weight: 'bold'
                            },
                            padding: 15
                        },
                        ticks: {
                            display: false,
                            stepSize: 20
                        }
                    }
                },
                elements: {
                    line: {
                        borderWidth: 2,
                        tension: 0.1
                    },
                    point: {
                        radius: this.options.showPoints ? 5 : 0,
                        hoverRadius: 7,
                        hitRadius: 10
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0 && this.options.onStrategySelect) {
                        const index = elements[0].datasetIndex;
                        const strategy = strategies[index];
                        this.options.onStrategySelect(strategy, index);
                    }
                },
                onHover: (event, elements) => {
                    canvas.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                    if (elements.length > 0 && this.options.onHover) {
                        const index = elements[0].datasetIndex;
                        const strategy = strategies[index];
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

        // 創建策略選擇器
        this._createStrategySelector(strategies);

        // 更新統計信息
        this._updateStatistics(strategies);

        // 保存數據
        this.strategies = strategies;
        this.selectedStrategies = strategies.slice(0, this.options.maxStrategies);
    }

    /**
     * 準備圖表數據
     */
    _prepareChartData(strategies) {
        const labels = this.options.metrics.map(metric =>
            this.metricConfig[metric].label
        );

        const datasets = strategies.slice(0, this.options.maxStrategies).map((strategy, index) => {
            // 獲取或生成策略顏色
            let color = this.strategyColors.get(strategy.name);
            if (!color) {
                color = this._getStrategyColor(index);
                this.strategyColors.set(strategy.name, color);
            }

            const data = this.options.metrics.map(metric => {
                const config = this.metricConfig[metric];
                const value = strategy[metric] || 0;
                return config.transform(value);
            });

            return {
                label: strategy.name,
                data: data,
                borderColor: color,
                backgroundColor: this.options.fillArea ? color + '30' : 'transparent',
                borderWidth: 2,
                pointBackgroundColor: color,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: color,
                pointHoverBorderWidth: 3
            };
        });

        return { labels, datasets };
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
            this.theme.info
        ];
        return colors[index % colors.length];
    }

    /**
     * 創建策略選擇器
     */
    _createStrategySelector(strategies) {
        const container = this.container.querySelector('#strategy-chips');
        container.innerHTML = '';

        strategies.forEach((strategy, index) => {
            const isSelected = index < this.options.maxStrategies;
            const color = this.strategyColors.get(strategy.name);

            const chip = document.createElement('div');
            chip.className = `strategy-chip ${isSelected ? 'selected' : ''}`;
            chip.innerHTML = `
                <div class="chip-color" style="background: ${color}"></div>
                <span class="chip-label">${strategy.name}</span>
                <span class="chip-score">${this._calculateOverallScore(strategy).toFixed(1)}</span>
            `;

            chip.addEventListener('click', () => {
                this._toggleStrategy(strategy, chip);
            });

            container.appendChild(chip);
        });
    }

    /**
     * 切換策略選擇
     */
    _toggleStrategy(strategy, chipElement) {
        const isSelected = chipElement.classList.contains('selected');
        const selectedCount = this.container.querySelectorAll('.strategy-chip.selected').length;

        if (isSelected) {
            // 取消選擇
            chipElement.classList.remove('selected');
            this.selectedStrategies = this.selectedStrategies.filter(s => s.name !== strategy.name);
        } else {
            // 檢查是否超過最大限制
            if (selectedCount >= this.options.maxStrategies) {
                this._showNotification(`最多只能選擇${this.options.maxStrategies}個策略進行對比`);
                return;
            }
            // 選擇
            chipElement.classList.add('selected');
            this.selectedStrategies.push(strategy);
        }

        // 更新圖表
        if (this.chart && this.strategies) {
            this.createChart(this.strategies);
        }
    }

    /**
     * 計算綜合評分
     */
    _calculateOverallScore(strategy) {
        let totalScore = 0;
        let totalWeight = 0;

        this.options.metrics.forEach(metric => {
            const config = this.metricConfig[metric];
            if (config) {
                const value = strategy[metric] || 0;
                const transformedValue = config.transform(value);
                totalScore += transformedValue * config.weight;
                totalWeight += config.weight;
            }
        });

        return totalWeight > 0 ? totalScore / totalWeight : 0;
    }

    /**
     * 獲取原始值
     */
    _getOriginalValue(metricLabel, strategy) {
        // 根據標籤找到對應的指標
        const metric = Object.entries(this.metricConfig).find(([k, v]) =>
            v.label === metricLabel
        );

        if (metric) {
            return strategy[metric[0]] || 0;
        }

        return 0;
    }

    /**
     * 更新統計信息
     */
    _updateStatistics(strategies) {
        let maxScore = 0;
        let bestStrategy = null;

        strategies.slice(0, this.options.maxStrategies).forEach(strategy => {
            const score = this._calculateOverallScore(strategy);
            if (score > maxScore) {
                maxScore = score;
                bestStrategy = strategy;
            }
        });

        const avgScore = strategies.length > 0
            ? strategies.slice(0, this.options.maxStrategies)
                .reduce((sum, s) => sum + this._calculateOverallScore(s), 0) /
              Math.min(strategies.length, this.options.maxStrategies)
            : 0;

        this.container.querySelector('#overall-score').textContent = avgScore.toFixed(1);
        this.container.querySelector('#best-strategy').textContent = bestStrategy ? bestStrategy.name : '-';
        this.container.querySelector('#update-time').textContent = new Date().toLocaleTimeString();
    }

    /**
     * 切換指標面板
     */
    _toggleMetricsPanel() {
        const panel = this.container.querySelector('#metrics-panel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }

    /**
     * 切換對比模式
     */
    _toggleCompareMode() {
        this.options.fillArea = !this.options.fillArea;

        if (this.chart) {
            this.chart.data.datasets.forEach(dataset => {
                dataset.backgroundColor = this.options.fillArea
                    ? dataset.borderColor + '30'
                    : 'transparent';
            });
            this.chart.update();
        }

        const btn = this.container.querySelector('#compare-btn');
        const icon = btn.querySelector('.icon');
        icon.textContent = this.options.fillArea ? '📈' : '📊';
    }

    /**
     * 更新指標
     */
    _updateMetrics(metric, enabled) {
        if (enabled) {
            if (!this.options.metrics.includes(metric)) {
                this.options.metrics.push(metric);
            }
        } else {
            const index = this.options.metrics.indexOf(metric);
            if (index > -1) {
                this.options.metrics.splice(index, 1);
            }
        }

        // 重新創建圖表
        if (this.strategies) {
            this.createChart(this.strategies);
        }
    }

    /**
     * 顯示通知
     */
    _showNotification(message) {
        // 創建通知元素
        const notification = document.createElement('div');
        notification.className = 'chart-notification';
        notification.textContent = message;

        this.container.appendChild(notification);

        // 自動移除
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    /**
     * 更新圖表數據
     */
    updateChart(strategies, animate = true) {
        if (!this.chart) {
            this.createChart(strategies);
            return;
        }

        const chartData = this._prepareChartData(strategies);

        // 更新數據
        this.chart.data = chartData;
        this.strategies = strategies;

        // 更新統計
        this._updateStatistics(strategies);

        // 重新創建選擇器
        this._createStrategySelector(strategies);

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
            if (this.strategies) {
                console.log('Refreshing radar chart data...');
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
    .strategy-radar-chart-container {
        background: #fff;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        position: relative;
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

    .chart-wrapper {
        padding: 20px;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .chart-footer {
        padding: 16px 20px;
        background: #fafafa;
        border-top: 1px solid #e0e0e0;
    }

    .strategy-selector {
        margin-bottom: 16px;
    }

    .selector-label {
        font-size: 13px;
        color: #666;
        display: block;
        margin-bottom: 8px;
    }

    .selector-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
    }

    .strategy-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border: 2px solid #e0e0e0;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.2s;
        background: #fff;
        font-size: 13px;
    }

    .strategy-chip:hover {
        border-color: #bbb;
        transform: translateY(-1px);
    }

    .strategy-chip.selected {
        border-color: currentColor;
        background: #f8f9fa;
    }

    .chip-color {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }

    .chip-label {
        font-weight: 500;
    }

    .chip-score {
        font-size: 12px;
        color: #666;
    }

    .radar-info {
        border-top: 1px solid #e0e0e0;
        padding-top: 16px;
    }

    .info-grid {
        display: flex;
        gap: 24px;
    }

    .info-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
    }

    .info-label {
        color: #666;
    }

    .info-value {
        font-weight: 600;
        color: #2c3e50;
    }

    .metrics-panel {
        position: absolute;
        top: 60px;
        right: 20px;
        width: 300px;
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 100;
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #e0e0e0;
        background: #f8f9fa;
    }

    .panel-header h4 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
    }

    .close-btn {
        background: none;
        border: none;
        font-size: 16px;
        cursor: pointer;
        color: #666;
        padding: 4px;
    }

    .close-btn:hover {
        color: #333;
    }

    .panel-content {
        padding: 12px 16px;
        max-height: 300px;
        overflow-y: auto;
    }

    .metrics-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .metric-item {
        padding: 8px 0;
    }

    .metric-checkbox {
        display: flex;
        flex-direction: column;
        gap: 4px;
        cursor: pointer;
    }

    .metric-label {
        font-weight: 500;
        color: #2c3e50;
    }

    .metric-desc {
        font-size: 12px;
        color: #666;
    }

    .metric-weight {
        font-size: 11px;
        color: #999;
    }

    .chart-notification {
        position: absolute;
        top: 80px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: #fff;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 13px;
        z-index: 200;
        animation: fadeInOut 3s ease-in-out;
    }

    @keyframes fadeInOut {
        0% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
        10% { opacity: 1; transform: translateX(-50%) translateY(0); }
        90% { opacity: 1; transform: translateX(-50%) translateY(0); }
        100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
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