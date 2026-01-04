/**
 * 个人策略管理Dashboard - 主类
 * Personal Strategy Management Dashboard - Main Class
 */

import { API_CONFIG, THEMES, DEFAULT_VALUES, EVENTS } from './constants.js';
import { formatPercentage, debounce } from './utils.js';
import { APIClient } from './api.js';
import { storage } from './storage.js';
import { eventBus } from './event-bus.js';
import { errorHandler } from './error-handler.js';
import NetValueChart from './net-value-chart.js';
import DrawdownChart from './drawdown-chart.js';
import SharpeRatioChart from './sharpe-chart.js';
import MonthlyHeatmap from './heatmap.js';
import StrategyManager from './strategy-manager.js';
import StrategyList from './strategy-list.js';
import StrategyForm from './strategy-form.js';
import SharpeAnalysisControls from './sharpe-analysis-controls.js';

/**
 * Dashboard主类
 */
class Dashboard {
    constructor() {
        // Core components
        this.apiClient = new APIClient(API_CONFIG.BASE_URL);
        this.strategyManager = new StrategyManager(this.apiClient, storage, eventBus);
        this.eventBus = eventBus;
        this.storage = storage;

        // State
        this.isLoading = false;
        this.currentTheme = storage.get('theme') || THEMES.LIGHT;
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;

        // Charts
        this.charts = {
            netValue: null,
            drawdown: null,
            sharpeRatio: null,
            heatmap: null
        };

        // UI Components
        this.strategyList = null;
        this.strategyForm = null;
        this.sharpeAnalysisControls = null;

        // Performance data cache
        this.performanceData = new Map();
        this.lastUpdateTime = null;

        // Initialize
        this.init();
    }

    /**
     * 初始化Dashboard
     */
    async init() {
        try {
            console.log('Initializing Dashboard...');

            // Setup event listeners
            this.setupEventListeners();

            // Setup theme
            this.setupTheme();

            // Load strategies
            await this.loadStrategies();

            // Initialize components
            this.initializeComponents();

            // Setup auto refresh
            this.startAutoRefresh();

            // Hide loading
            this.hideLoading();

            // Emit ready event
            this.eventBus.emit('dashboard:ready');

            console.log('Dashboard initialized successfully');

        } catch (error) {
            console.error('Failed to initialize Dashboard:', error);
            this.handleError(error, 'Dashboard initialization');
            this.showError('初始化失败，请刷新页面重试');
        }
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // Navigation actions
        const refreshBtn = document.getElementById('refresh-btn');
        const themeToggle = document.getElementById('theme-toggle');
        const addStrategyBtn = document.getElementById('add-strategy-btn');

        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        if (addStrategyBtn) {
            addStrategyBtn.addEventListener('click', () => this.showAddStrategyForm());
        }

        // Chart controls
        const netValuePeriod = document.getElementById('net-value-period');
        const drawdownStrategy = document.getElementById('drawdown-strategy');
        const heatmapHelp = document.getElementById('heatmap-help');
        const closeHeatmapHelp = document.getElementById('close-heatmap-help');

        if (netValuePeriod) {
            netValuePeriod.addEventListener('change', (e) => {
                this.updateNetValueChart(e.target.value);
            });
        }

        if (drawdownStrategy) {
            drawdownStrategy.addEventListener('change', (e) => {
                this.updateDrawdownChart(e.target.value);
            });
        }

        if (heatmapHelp) {
            heatmapHelp.addEventListener('click', () => this.showHeatmapHelp());
        }

        if (closeHeatmapHelp) {
            closeHeatmapHelp.addEventListener('click', () => this.hideHeatmapHelp());
        }

        // Window resize
        window.addEventListener('resize', debounce(() => {
            this.handleResize();
        }, 250));

        // Visibility change
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });

        // Strategy events
        this.setupStrategyEventListeners();
    }

    /**
     * 设置策略相关事件监听器
     */
    setupStrategyEventListeners() {
        // Strategy list events
        this.eventBus.on('strategy:view', (strategy) => {
            this.showStrategyDetail(strategy);
        });

        this.eventBus.on('strategy:edit', (strategy) => {
            this.showEditStrategyForm(strategy);
        });

        this.eventBus.on('strategy:selected', (strategy) => {
            this.handleStrategySelection(strategy);
        });

        // Form events
        this.eventBus.on('form:hidden', () => {
            this.hideModal();
        });

        // Notification events
        this.eventBus.on('notification', (notification) => {
            this.showNotification(notification);
        });

        // Error events
        this.eventBus.on('error', (error) => {
            this.handleError(error, 'Unknown context');
        });

        // Heatmap events
        this.eventBus.on('heatmap:cellClick', (data) => {
            this.handleHeatmapCellClick(data);
        });
    }

    /**
     * 设置主题
     */
    setupTheme() {
        this.setTheme(this.currentTheme);
    }

    /**
     * 设置主题
     * @param {string} theme - 主题名称
     */
    setTheme(theme) {
        // Update body class
        document.body.setAttribute('data-theme', theme);

        // Update storage
        this.storage.set('theme', theme);

        // Update theme icons
        const moonIcon = document.querySelector('.icon-moon');
        const sunIcon = document.querySelector('.icon-sun');

        if (moonIcon && sunIcon) {
            if (theme === THEMES.DARK) {
                moonIcon.style.display = 'none';
                sunIcon.style.display = 'inline';
            } else {
                moonIcon.style.display = 'inline';
                sunIcon.style.display = 'none';
            }
        }

        // Update current theme
        this.currentTheme = theme;

        // Emit theme change event
        this.eventBus.emit('themeChanged', { theme });
    }

    /**
     * 切换主题
     */
    toggleTheme() {
        const newTheme = this.currentTheme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT;
        this.setTheme(newTheme);
    }

    /**
     * 加载策略
     */
    async loadStrategies() {
        try {
            this.showLoading();
            await this.strategyManager.loadStrategies();
            this.updateOverview();
        } catch (error) {
            console.error('Failed to load strategies:', error);
            throw error;
        }
    }

    /**
     * 初始化组件
     */
    initializeComponents() {
        // Initialize strategy list
        const strategyListContainer = document.getElementById('strategy-list-container');
        if (strategyListContainer) {
            this.strategyList = new StrategyList(strategyListContainer, this.strategyManager, this.eventBus);
        }

        // Initialize strategy form
        const formContainer = document.getElementById('strategy-form-modal').querySelector('.modal-content');
        if (formContainer) {
            this.strategyForm = new StrategyForm(formContainer, this.strategyManager, this.eventBus);
        }

        // Initialize charts
        this.initializeCharts();

        // Update strategy selector in drawdown chart
        this.updateDrawdownStrategySelector();
    }

    /**
     * 初始化图表
     */
    initializeCharts() {
        try {
            // Net value chart
            const netValueCanvas = document.getElementById('net-value-chart');
            if (netValueCanvas) {
                this.charts.netValue = new NetValueChart('net-value-chart');
            }

            // Drawdown chart
            const drawdownCanvas = document.getElementById('drawdown-chart');
            if (drawdownCanvas) {
                this.charts.drawdown = new DrawdownChart('drawdown-chart');
            }

            // Enhanced Sharpe ratio chart
            const sharpeCanvas = document.getElementById('sharpe-chart');
            if (sharpeCanvas) {
                this.charts.sharpeRatio = new SharpeRatioChart('sharpe-chart', {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        },
                        annotation: {
                            annotations: {}
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
                    }
                });
            }

            // Monthly heatmap
            const heatmapContainer = document.getElementById('monthly-heatmap');
            if (heatmapContainer) {
                this.charts.heatmap = new MonthlyHeatmap('monthly-heatmap');
            }

            // Initialize Sharpe Analysis Controls
            this.initializeSharpeAnalysisControls();

        } catch (error) {
            console.error('Failed to initialize charts:', error);
        }
    }

    /**
     * 初始化Sharpe分析控制面板
     */
    initializeSharpeAnalysisControls() {
        try {
            const controlsContainer = document.getElementById('sharpe-controls-container');
            if (controlsContainer && this.charts.sharpeRatio) {
                this.sharpeAnalysisControls = new SharpeAnalysisControls('sharpe-controls-container', this.charts.sharpeRatio);

                // Setup toggle button
                const toggleBtn = document.getElementById('sharpe-analysis-toggle');
                if (toggleBtn) {
                    toggleBtn.addEventListener('click', () => {
                        controlsContainer.classList.toggle('hidden');
                    });
                }
            }
        } catch (error) {
            console.error('Failed to initialize Sharpe analysis controls:', error);
        }
    }

    /**
     * 更新概览信息
     */
    updateOverview() {
        const strategies = this.strategyManager.getStrategies();
        const runningStrategies = strategies.filter(s => s.status === 'running');

        // Calculate metrics
        const stats = this.calculateOverviewStats(strategies);

        // Update DOM
        this.updateOverviewCards(stats);
        this.updateStrategyStatusInfo(runningStrategies.length, strategies.length - runningStrategies.length);

        // Load performance data for charts
        this.loadPerformanceData();
    }

    /**
     * 计算概览统计
     * @param {Array} strategies - 策略列表
     * @returns {Object} 统计数据
     */
    calculateOverviewStats(strategies) {
        if (strategies.length === 0) {
            return {
                totalReturn: 0,
                avgSharpe: 0,
                maxDrawdown: 0
            };
        }

        const totalReturn = strategies.reduce((sum, s) => sum + (s.current_return || 0), 0);
        const avgSharpe = strategies.reduce((sum, s) => sum + (s.sharpe_ratio || 0), 0) / strategies.length;
        const maxDrawdown = Math.max(...strategies.map(s => s.max_drawdown || 0));

        return {
            totalReturn,
            avgSharpe,
            maxDrawdown
        };
    }

    /**
     * 更新概览卡片
     * @param {Object} stats - 统计数据
     */
    updateOverviewCards(stats) {
        // Total return
        const totalReturnEl = document.getElementById('total-return');
        if (totalReturnEl) {
            totalReturnEl.textContent = formatPercentage(stats.totalReturn);
            this.updateChangeIndicator('total-return-change', stats.totalReturn);
        }

        // Average Sharpe ratio
        const avgSharpeEl = document.getElementById('avg-sharpe');
        if (avgSharpeEl) {
            avgSharpeEl.textContent = stats.avgSharpe.toFixed(2);
        }

        // Max drawdown
        const maxDrawdownEl = document.getElementById('max-drawdown');
        if (maxDrawdownEl) {
            maxDrawdownEl.textContent = formatPercentage(Math.abs(stats.maxDrawdown));
        }
    }

    /**
     * 更新策略状态信息
     * @param {number} runningCount - 运行中数量
     * @param {number} stoppedCount - 已停止数量
     */
    updateStrategyStatusInfo(runningCount, stoppedCount) {
        const runningStrategiesEl = document.getElementById('running-strategies');
        if (runningStrategiesEl) {
            runningStrategiesEl.textContent = `${runningCount}/4`;
        }

        const runningCountEl = document.getElementById('running-count');
        if (runningCountEl) {
            runningCountEl.textContent = runningCount;
        }

        const stoppedCountEl = document.getElementById('stopped-count');
        if (stoppedCountEl) {
            stoppedCountEl.textContent = stoppedCount;
        }
    }

    /**
     * 更新变化指示器
     * @param {string} elementId - 元素ID
     * @param {number} value - 当前值
     */
    updateChangeIndicator(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const changeValueEl = element.querySelector('.change-value');
        if (changeValueEl) {
            const formattedValue = value >= 0 ? `+${formatPercentage(value)}` : formatPercentage(value);
            changeValueEl.textContent = formattedValue;

            // Update color
            element.className = value >= 0 ? 'card-change positive' : 'card-change negative';
        }
    }

    /**
     * 加载性能数据
     */
    async loadPerformanceData() {
        const strategies = this.strategyManager.getStrategies();
        const period = document.getElementById('net-value-period')?.value || '1m';

        try {
            // Load performance data for each strategy
            for (const strategy of strategies) {
                const key = `${strategy.id}-${period}`;
                if (!this.performanceData.has(key)) {
                    try {
                        const performanceData = await this.apiClient.getStrategyPerformance(strategy.id, period);
                        this.performanceData.set(key, performanceData);

                        // Update charts
                        this.updateChartsWithStrategyData(strategy, performanceData);
                    } catch (error) {
                        console.warn(`Failed to load performance data for strategy ${strategy.id}:`, error);
                    }
                }
            }

            // Update heatmap
            if (this.charts.heatmap) {
                strategies.forEach(strategy => {
                    const key = `${strategy.id}-all`;
                    const data = this.performanceData.get(key);
                    if (data) {
                        this.charts.heatmap.addStrategy(strategy.id, strategy, data.daily_returns || []);
                    }
                });
            }

        } catch (error) {
            console.error('Failed to load performance data:', error);
        }
    }

    /**
     * 使用策略数据更新图表
     * @param {Object} strategy - 策略对象
     * @param {Object} data - 性能数据
     */
    updateChartsWithStrategyData(strategy, data) {
        // Net value chart
        if (this.charts.netValue && data.cumulative_returns) {
            const chartData = data.cumulative_returns.map((value, index) => ({
                timestamp: data.timestamps[index],
                net_value: value
            }));
            this.charts.netValue.addStrategy(strategy.id, strategy, chartData);
        }

        // Drawdown chart
        if (this.charts.drawdown && data.drawdowns) {
            const chartData = data.drawdowns.map((value, index) => ({
                timestamp: data.timestamps[index],
                daily_return: value
            }));
            this.charts.drawdown.addStrategy(strategy.id, strategy, chartData);
        }

        // Enhanced Sharpe ratio chart
        if (this.charts.sharpeRatio && data.returns) {
            const sharpeChartData = data.returns.map((value, index) => ({
                timestamp: data.timestamps[index],
                daily_return: value
            }));

            // Add strategy to Sharpe chart (will trigger advanced analysis)
            this.charts.sharpeRatio.addStrategy(strategy.id, strategy, sharpeChartData);
        }
    }

    /**
     * 更新净值图表
     * @param {string} period - 时间周期
     */
    async updateNetValueChart(period) {
        if (!this.charts.netValue) return;

        this.charts.netValue.setPeriod(period);

        // Reload performance data with new period
        await this.loadPerformanceData();
    }

    /**
     * 更新回撤图表
     * @param {string} strategyId - 策略ID（空表示所有策略）
     */
    updateDrawdownChart(strategyId) {
        if (!this.charts.drawdown) return;

        this.charts.drawdown.setCurrentStrategy(strategyId);
    }

    /**
     * 更新回撤图表策略选择器
     */
    updateDrawdownStrategySelector() {
        const select = document.getElementById('drawdown-strategy');
        if (!select) return;

        const strategies = this.strategyManager.getStrategies();

        // Keep "All strategies" option
        select.innerHTML = '<option value="">所有策略</option>';

        // Add strategy options
        strategies.forEach(strategy => {
            const option = document.createElement('option');
            option.value = strategy.id;
            option.textContent = strategy.name;
            select.appendChild(option);
        });
    }

    /**
     * 刷新数据
     */
    async refreshData() {
        const refreshBtn = document.getElementById('refresh-btn');
        const btnText = refreshBtn?.querySelector('.btn-text');

        try {
            // Show loading state
            if (refreshBtn) {
                refreshBtn.classList.add('loading');
            }
            if (btnText) {
                btnText.textContent = '刷新中...';
            }

            // Reload strategies
            await this.loadStrategies();

            // Clear performance cache to force reload
            this.performanceData.clear();

            // Reload performance data
            await this.loadPerformanceData();

            // Update last update time
            this.lastUpdateTime = new Date();

            this.showSuccess('数据刷新成功');

        } catch (error) {
            console.error('Failed to refresh data:', error);
            this.showError(`刷新失败: ${error.message}`);
        } finally {
            // Hide loading state
            if (refreshBtn) {
                refreshBtn.classList.remove('loading');
            }
            if (btnText) {
                btnText.textContent = '刷新数据';
            }
        }
    }

    /**
     * 启动自动刷新
     */
    startAutoRefresh() {
        if (!this.autoRefreshEnabled) return;

        // Clear existing interval
        this.stopAutoRefresh();

        // Start new interval
        this.refreshInterval = setInterval(() => {
            if (!document.hidden) {
                this.refreshData();
            }
        }, DEFAULT_VALUES.AUTO_REFRESH_INTERVAL);
    }

    /**
     * 停止自动刷新
     */
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * 显示添加策略表单
     */
    showAddStrategyForm() {
        if (this.strategyForm) {
            this.strategyForm.show('add');
            this.showModal('strategy-form-modal');
        }
    }

    /**
     * 显示编辑策略表单
     * @param {Object} strategy - 策略对象
     */
    showEditStrategyForm(strategy) {
        if (this.strategyForm) {
            this.strategyForm.show('edit', strategy);
            this.showModal('strategy-form-modal');
        }
    }

    /**
     * 显示策略详情
     * @param {Object} strategy - 策略对象
     */
    showStrategyDetail(strategy) {
        // Create detail view
        const detailHtml = this.createStrategyDetailView(strategy);

        // Show in modal
        const modal = document.getElementById('strategy-detail-modal');
        const modalContent = modal?.querySelector('.modal-content');
        if (modalContent) {
            modalContent.innerHTML = detailHtml;
            this.showModal('strategy-detail-modal');
        }
    }

    /**
     * 创建策略详情视图
     * @param {Object} strategy - 策略对象
     * @returns {string} HTML字符串
     */
    createStrategyDetailView(strategy) {
        const strategyType = STRATEGY_TYPES[strategy.strategy_type.toUpperCase()] || STRATEGY_TYPES.MOMENTUM;
        const statusConfig = strategy.status ?
            Object.values(STRATEGY_STATUS).find(s => s.value === strategy.status) : null;

        return `
            <div class="form-header">
                <h2>策略详情</h2>
                <button class="btn-close" onclick="dashboard.hideModal()">&times;</button>
            </div>
            <div class="form-container">
                <div class="detail-section">
                    <h3>基本信息</h3>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>名称</label>
                            <span>${strategy.name}</span>
                        </div>
                        <div class="detail-item">
                            <label>类型</label>
                            <span>${strategyType.label}</span>
                        </div>
                        <div class="detail-item">
                            <label>状态</label>
                            <span class="status ${statusConfig?.value || ''}">${statusConfig?.label || strategy.status}</span>
                        </div>
                        <div class="detail-item">
                            <label>创建时间</label>
                            <span>${formatDate(strategy.created_at)}</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h3>描述</h3>
                    <p>${strategy.description || '暂无描述'}</p>
                </div>

                <div class="detail-section">
                    <h3>资金配置</h3>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>初始资金</label>
                            <span>¥${strategy.initial_capital.toLocaleString()}</span>
                        </div>
                        <div class="detail-item">
                            <label>风险限制</label>
                            <span>${(strategy.risk_limit * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                </div>

                <div class="detail-section">
                    <h3>性能指标</h3>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>当前收益率</label>
                            <span class="${strategy.current_return >= 0 ? 'text-success' : 'text-danger'}">
                                ${formatPercentage(strategy.current_return)}
                            </span>
                        </div>
                        <div class="detail-item">
                            <label>Sharpe比率</label>
                            <span>${strategy.sharpe_ratio ? strategy.sharpe_ratio.toFixed(2) : '--'}</span>
                        </div>
                        <div class="detail-item">
                            <label>最大回撤</label>
                            <span class="text-danger">${formatPercentage(Math.abs(strategy.max_drawdown))}</span>
                        </div>
                    </div>
                </div>

                <div class="form-actions">
                    <button class="btn btn-secondary" onclick="dashboard.hideModal()">
                        关闭
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 显示模态框
     * @param {string} modalId - 模态框ID
     */
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    /**
     * 隐藏模态框
     */
    hideModal() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }

    /**
     * 处理策略选择
     * @param {Object} strategy - 选中的策略
     */
    handleStrategySelection(strategy) {
        // Update charts to highlight selected strategy
        if (this.charts.drawdown) {
            this.updateDrawdownChart(strategy.id);
        }

        // Update selector
        const selector = document.getElementById('drawdown-strategy');
        if (selector) {
            selector.value = strategy.id;
        }
    }

    /**
     * 显示热力图帮助
     */
    showHeatmapHelp() {
        this.showModal('heatmap-help-modal');
    }

    /**
     * 隐藏热力图帮助
     */
    hideHeatmapHelp() {
        this.hideModal();
    }

    /**
     * 处理热力图单元格点击
     * @param {Object} data - 单元格数据
     */
    handleHeatmapCellClick(data) {
        console.log('Heatmap cell clicked:', data);
        // 可以在这里显示更详细的信息
    }

    /**
     * 处理窗口大小变化
     */
    handleResize() {
        // Update charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.update === 'function') {
                chart.update();
            }
        });
    }

    /**
     * 处理可见性变化
     */
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden, pause auto refresh
            this.stopAutoRefresh();
        } else {
            // Page is visible, resume auto refresh
            this.startAutoRefresh();
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        this.isLoading = true;
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    }

    /**
     * 隐藏加载状态
     */
    hideLoading() {
        this.isLoading = false;
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    /**
     * 显示成功消息
     * @param {string} message - 消息内容
     */
    showSuccess(message) {
        this.showNotification({ type: 'success', message });
    }

    /**
     * 显示错误消息
     * @param {string} message - 消息内容
     */
    showError(message) {
        this.showNotification({ type: 'error', message });
    }

    /**
     * 显示通知
     * @param {Object} notification - 通知对象
     */
    showNotification(notification) {
        const container = document.getElementById('notifications');
        if (!container) return;

        const notificationEl = document.createElement('div');
        notificationEl.className = `notification notification-${notification.type}`;
        notificationEl.textContent = notification.message;

        container.appendChild(notificationEl);

        // Auto remove after duration
        setTimeout(() => {
            notificationEl.remove();
        }, notification.duration || 3000);
    }

    /**
     * 处理错误
     * @param {Error} error - 错误对象
     * @param {string} context - 错误上下文
     */
    handleError(error, context) {
        errorHandler.handle(error, context);
    }

    /**
     * 格式化日期
     * @param {string} dateStr - 日期字符串
     * @returns {string} 格式化后的日期
     */
    formatDate(dateStr) {
        return formatDate(dateStr, 'datetime');
    }

    /**
     * 销毁Dashboard
     */
    destroy() {
        // Stop auto refresh
        this.stopAutoRefresh();

        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });

        // Clear performance data
        this.performanceData.clear();
    }
}

// 全局Dashboard实例
let dashboardInstance = null;

// 应用启动
document.addEventListener('DOMContentLoaded', () => {
    dashboardInstance = new Dashboard();

    // 暴露到全局用于模态框关闭等操作
    window.dashboard = dashboardInstance;
});

// 页面卸载时清理
window.addEventListener('beforeunload', () => {
    if (dashboardInstance) {
        dashboardInstance.destroy();
    }
});

export default Dashboard;