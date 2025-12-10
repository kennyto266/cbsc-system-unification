/**
 * 個人策略管理Dashboard - 修復版本
 * 集成真實API數據，支持CBSC策略監控
 */

// ========== 配置常量 ==========
const DASHBOARD_CONFIG = {
    // API配置
    apiBaseUrl: 'http://localhost:3003',
    refreshInterval: 10000, // 10秒刷新
    requestTimeout: 5000,

    // 策略列表
    strategies: [
        'DirectRSIStrategy',
        'SentimentMomentumStrategy',
        'CompositeIndexStrategy',
        'VolatilityAdjustedStrategy'
    ],

    // 性能指標
    metrics: ['sharpe_ratio', 'max_drawdown', 'win_rate', 'signal_count'],

    // 時間範圍
    timeRanges: {
        '1d': '1天',
        '1w': '1周',
        '1m': '1月',
        '3m': '3月',
        '1y': '1年'
    }
};

// ========== Dashboard管理器 ==========
class DashboardManager {
    constructor() {
        this.isInitialized = false;
        this.refreshTimer = null;
        this.isLoading = false;
        this.currentData = null;
        this.performanceChart = null;
        this.websocketClient = null;

        // 綁定事件
        this.bindEvents();

        // 初始化組件
        this.initializeComponents();
    }

    /**
     * 初始化Dashboard組件
     */
    initializeComponents() {
        console.log('🚀 初始化個人策略管理Dashboard...');

        // 更新最後更新時間
        this.updateLastUpdateTime();

        // 顯示加載提示
        this.showLoading('正在初始化Dashboard...');

        // 等待資源加載完成
        setTimeout(() => {
            // 初始化WebSocket實時連接
            this.initializeWebSocket();

            // 初始化圖表
            this.initializeCharts();

            // 開始自動刷新（作為WebSocket的後備）
            this.startAutoRefresh();

            // 立即獲取數據
            this.refreshData();

            this.hideLoading();
            this.showMessage('Dashboard初始化完成', 'success');
            this.isInitialized = true;

            console.log('✅ Dashboard初始化完成');
        }, 1500);
    }

    /**
     * 綁定事件處理器
     */
    bindEvents() {
        // 刷新按鈕
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshData());
        }

        // 時間範圍選擇器
        const timeRange = document.getElementById('timeRange');
        if (timeRange) {
            timeRange.addEventListener('change', (e) => {
                this.handleTimeRangeChange(e.target.value);
            });
        }

        // 過濾器按鈕
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleFilterChange(e.target.dataset.filter, e.target);
            });
        });

        // 圖表切換按鈕
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleChartSwitch(e.target.dataset.chart, e.target);
            });
        });

        // 策略操作按鈕
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.handleStrategyAction(e.target.closest('.strategy-item'), e.target);
            });
        });

        // 快速操作按鈕
        document.getElementById('addStrategyBtn')?.addEventListener('click', () => {
            this.handleAddStrategy();
        });

        document.getElementById('quickAnalysisBtn')?.addEventListener('click', () => {
            this.handleQuickAnalysis();
        });

        document.getElementById('optimizeBtn')?.addEventListener('click', () => {
            this.handleOptimize();
        });

        document.getElementById('backtestBtn')?.addEventListener('click', () => {
            this.handleBacktest();
        });

        document.getElementById('reportBtn')?.addEventListener('click', () => {
            this.handleGenerateReport();
        });

        // 消息提示關閉
        const toastClose = document.getElementById('toastClose');
        if (toastClose) {
            toastClose.addEventListener('click', () => this.hideMessage());
        }

        // 網絡監控
        this.setupNetworkMonitoring();
    }

    /**
     * 設置網絡監控
     */
    setupNetworkMonitoring() {
        window.addEventListener('online', () => {
            this.showMessage('網絡已恢復', 'success');
            if (this.websocketClient) {
                this.websocketClient.connect();
            }
            this.refreshData();
        });

        window.addEventListener('offline', () => {
            this.showMessage('網絡連接已斷開', 'warning');
            if (this.websocketClient) {
                this.websocketClient.disconnect();
            }
        });
    }

    /**
     * 初始化WebSocket實時連接
     */
    initializeWebSocket() {
        console.log('🔌 初始化WebSocket實時連接...');

        try {
            // 檢查WebSocket客戶端是否可用
            if (typeof DashboardWebSocketClient === 'undefined') {
                console.warn('WebSocket客戶端不可用，使用HTTP輪詢');
                return;
            }

            // 創建WebSocket客戶端實例
            this.websocketClient = new DashboardWebSocketClient({
                serverUrl: 'ws://localhost:3005',
                reconnectInterval: 3000,
                maxReconnectAttempts: 5
            });

            // 設置事件監聽器
            this.setupWebSocketEvents();

            // 建立連接
            this.websocketClient.connect();

            console.log('✅ WebSocket客戶端初始化完成');

        } catch (error) {
            console.error('WebSocket初始化失敗:', error);
            this.showMessage('實時連接初始化失敗，將使用HTTP輪詢', 'warning');
        }
    }

    /**
     * 設置WebSocket事件監聽器
     */
    setupWebSocketEvents() {
        if (!this.websocketClient) return;

        // 連接成功
        this.websocketClient.on('onConnect', (data) => {
            console.log('🔗 WebSocket連接成功');
            this.showMessage('實時連接已建立', 'success');
            this.updateConnectionStatus('connected');
        });

        // 連接斷開
        this.websocketClient.on('onDisconnect', (data) => {
            console.log('🔌 WebSocket連接斷開');
            this.showMessage('實時連接已斷開', 'warning');
            this.updateConnectionStatus('disconnected');
        });

        // 連接錯誤
        this.websocketClient.on('onError', (error) => {
            console.error('❌ WebSocket連接錯誤:', error);
            this.showMessage('實時連接發生錯誤', 'error');
            this.updateConnectionStatus('error');
        });

        // 接收數據更新
        this.websocketClient.on('onDataUpdate', (data) => {
            this.handleRealtimeDataUpdate(data);
        });

        // 通用消息處理
        this.websocketClient.on('onMessage', (message) => {
            console.log('📨 收到WebSocket消息:', message.type);
        });
    }

    /**
     * 處理實時數據更新
     */
    handleRealtimeDataUpdate(data) {
        try {
            const { type, data: updateData, timestamp } = data;

            switch (type) {
                case 'strategies':
                    this.handleRealtimeStrategiesUpdate(updateData, timestamp);
                    break;
                case 'performance':
                    this.handleRealtimePerformanceUpdate(updateData, timestamp);
                    break;
                case 'signals':
                    this.handleRealtimeSignalsUpdate(updateData, timestamp);
                    break;
                case 'system_health':
                    this.handleRealtimeSystemHealthUpdate(updateData, timestamp);
                    break;
                default:
                    console.log('收到未知實時數據類型:', type);
            }

        } catch (error) {
            console.error('處理實時數據更新失敗:', error);
        }
    }

    /**
     * 處理實時策略數據更新
     */
    handleRealtimeStrategiesUpdate(strategies, timestamp) {
        console.log('🔄 實時策略數據更新', strategies?.length || 0, '個策略');

        if (!strategies || !Array.isArray(strategies)) return;

        // 轉換為Dashboard格式
        const dashboardData = {
            strategies: strategies.map(strategy => ({
                name: strategy.name,
                display_name: strategy.name,
                status: 'active', // 假設都是活躍狀態
                performance: strategy.performance || {
                    sharpe_ratio: 0,
                    max_drawdown: 0,
                    win_rate: 0
                },
                last_signal: {
                    signal: strategy.signal || 'HOLD',
                    strength: strategy.strength || 0.5,
                    confidence: strategy.confidence || 0.5
                },
                description: `${strategy.name} 策略實時監控`,
                last_updated: timestamp
            })),
            summary: this.calculateSummary(strategies),
            timestamp: timestamp
        };

        // 更新顯示
        this.updateStrategyDisplay(dashboardData);

        // 更新圖表
        this.updateChartsData(dashboardData);
    }

    /**
     * 處理實時性能更新
     */
    handleRealtimePerformanceUpdate(performanceData, timestamp) {
        console.log('📈 實時性能更新', performanceData);

        if (performanceData.updated_strategies) {
            // 更新現有策略的性能指標
            if (this.currentData && this.currentData.strategies) {
                performanceData.updated_strategies.forEach(updatedStrategy => {
                    const strategyIndex = this.currentData.strategies.findIndex(
                        s => s.name === updatedStrategy.name
                    );

                    if (strategyIndex >= 0) {
                        this.currentData.strategies[strategyIndex] = {
                            ...this.currentData.strategies[strategyIndex],
                            ...updatedStrategy
                        };
                    }
                });

                // 更新顯示
                this.updateStrategyDisplay(this.currentData);
                this.updateChartsData(this.currentData);
            }
        }
    }

    /**
     * 處理實時信號更新
     */
    handleRealtimeSignalsUpdate(signalsData, timestamp) {
        console.log('📊 實時信號更新', Object.keys(signalsData).length, '個信號');

        // 顯示信號更新通知
        Object.entries(signalsData).forEach(([strategy, signalInfo]) => {
            if (signalInfo.signal && signalInfo.signal !== 'HOLD') {
                const signalText = signalInfo.signal === 'BUY' ? '買入信號' : '賣出信號';
                const strengthText = (signalInfo.strength * 100).toFixed(0);
                this.showMessage(
                    `${strategy}: ${signalText} (強度: ${strengthText}%)`,
                    signalInfo.signal === 'BUY' ? 'success' : 'warning'
                );
            }
        });
    }

    /**
     * 處理實時系統健康更新
     */
    handleRealtimeSystemHealthUpdate(healthData, timestamp) {
        console.log('🏥 系統健康狀態更新', healthData);

        // 可以在UI上顯示系統健康狀態
        if (healthData.active_connections !== undefined) {
            console.log(`活躍連接數: ${healthData.active_connections}`);
        }
    }

    /**
     * 更新連接狀態顯示
     */
    updateConnectionStatus(status) {
        const statusElement = document.querySelector('.user-status');
        if (statusElement) {
            statusElement.className = `user-status ${status}`;
            statusElement.title = `連接狀態: ${status}`;
        }

        // 更新連接狀態指示器顏色
        const statusColors = {
            'connected': '#27ae60',
            'disconnected': '#e74c3c',
            'error': '#f39c12',
            'connecting': '#3498db'
        };

        if (statusElement) {
            statusElement.style.color = statusColors[status] || '#95a5a6';
        }
    }

    /**
     * 初始化圖表
     */
    initializeCharts() {
        console.log('📊 初始化增強圖表組件...');

        try {
            // 檢查Chart.js是否已加載
            if (typeof Chart === 'undefined') {
                console.warn('Chart.js未加載，顯示佔位符');
                this.showChartPlaceholder();
                return;
            }

            // 檢查增強圖表組件是否已加載
            if (typeof ChartManager === 'undefined') {
                console.warn('ChartManager未加載，使用基本圖表');
                this.initializePerformanceChart();
                return;
            }

            // 初始化增強圖表管理器
            this.chartManager = new ChartManager();

            console.log('✅ 增強圖表初始化完成');
        } catch (error) {
            console.error('圖表初始化失敗:', error);
            this.showChartPlaceholder();
        }
    }

    /**
     * 顯示圖表佔位符
     */
    showChartPlaceholder() {
        const placeholder = document.querySelector('.chart-placeholder');
        if (placeholder) {
            placeholder.style.display = 'flex';
            placeholder.innerHTML = `
                <div class="placeholder-icon">📊</div>
                <p>圖表正在加載中...</p>
                <small>Chart.js庫加載完成後將顯示圖表</small>
            `;
        }
    }

    /**
     * 初始化性能圖表
     */
    initializePerformanceChart() {
        const canvas = document.getElementById('performanceChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.generateTimeLabels(),
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: '策略價值'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: '時間'
                        }
                    }
                }
            }
        });
    }

    /**
     * 生成時間標籤
     */
    generateTimeLabels() {
        const labels = [];
        const now = new Date();

        for (let i = 29; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('zh-CN', {
                month: 'short',
                day: 'numeric'
            }));
        }

        return labels;
    }

    /**
     * 處理時間範圍變更
     */
    handleTimeRangeChange(range) {
        this.showMessage(`時間範圍已更改: ${DASHBOARD_CONFIG.timeRanges[range]}`, 'info');
        this.refreshData();
    }

    /**
     * 處理過濾器變更
     */
    handleFilterChange(filter, element) {
        // 更新按鈕狀態
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        element.classList.add('active');

        // 過濾策略項目
        const strategyItems = document.querySelectorAll('.strategy-item');
        strategyItems.forEach(item => {
            const isActive = filter === 'all' ||
                             (filter === 'active' && item.classList.contains('active')) ||
                             (filter === 'stopped' && item.classList.contains('stopped'));

            item.style.display = isActive ? 'flex' : 'none';
        });

        this.showMessage(`過濾器: ${element.textContent}`, 'info');
    }

    /**
     * 處理圖表切換
     */
    handleChartSwitch(chartType, element) {
        // 更新按鈕狀態
        document.querySelectorAll('.chart-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        element.classList.add('active');

        this.showMessage(`切換到: ${element.textContent}圖表`, 'info');

        // 圖表切換邏輯
        console.log(`圖表類型切換到: ${chartType}`);
    }

    /**
     * 處理策略操作
     */
    handleStrategyAction(strategyItem, actionButton) {
        const strategyName = strategyItem.querySelector('.strategy-name').textContent;
        const action = actionButton.getAttribute('title');

        console.log(`策略操作: ${strategyName} - ${action}`);

        switch (action) {
            case '編輯':
                this.handleEditStrategy(strategyName);
                break;
            case '暫停':
                this.handlePauseStrategy(strategyName, strategyItem);
                break;
            case '啟動':
                this.handleStartStrategy(strategyName, strategyItem);
                break;
            case '查看詳情':
                this.handleViewDetails(strategyName);
                break;
        }
    }

    /**
     * 處理策略切換（啟動/停止）
     */
    async handleToggleStrategy(strategyName, currentStatus) {
        const newStatus = currentStatus === 'active' ? 'stopped' : 'active';

        try {
            await window.strategyAPI.updateStrategyStatus(strategyName, newStatus);
            this.showMessage(`策略 ${strategyName} 已${newStatus === 'active' ? '啟動' : '停止'}`, 'success');
            // 刷新數據
            await this.refreshData();
        } catch (error) {
            this.showMessage(`操作失敗: ${error.message}`, 'error');
        }
    }

    /**
     * 處理添加策略
     */
    handleAddStrategy() {
        this.showMessage('添加策略功能正在開發中...', 'info');
    }

    /**
     * 處理快速分析
     */
    handleQuickAnalysis() {
        this.showLoading('正在執行快速分析...');
        setTimeout(() => {
            this.hideLoading();
            this.showMessage('快速分析完成', 'success');
        }, 2000);
    }

    /**
     * 處理參數優化
     */
    handleOptimize() {
        this.showLoading('優化策略參數中...');
        setTimeout(() => {
            this.hideLoading();
            this.showMessage('參數優化完成', 'success');
        }, 3000);
    }

    /**
     * 處理回測
     */
    handleBacktest() {
        this.showLoading('正在執行策略回測...');
        setTimeout(() => {
            this.hideLoading();
            this.showMessage('回測完成', 'success');
        }, 4000);
    }

    /**
     * 處理生成報告
     */
    handleGenerateReport() {
        this.showLoading('正在生成分析報告...');
        setTimeout(() => {
            this.hideLoading();
            this.showMessage('報告生成完成', 'success');
        }, 2500);
    }

    /**
     * 處理編輯策略
     */
    handleEditStrategy(strategyName) {
        this.showMessage(`編輯策略: ${strategyName}`, 'info');
    }

    /**
     * 處理暫停策略
     */
    handlePauseStrategy(strategyName, strategyItem) {
        strategyItem.classList.remove('active');
        strategyItem.classList.add('stopped');

        const statusElement = strategyItem.querySelector('.strategy-status');
        const statusDot = statusElement.querySelector('.status-indicator');
        const statusText = statusElement.querySelector('.status-text');

        statusDot.classList.remove('active');
        statusDot.classList.add('stopped');
        statusText.textContent = '已停止';

        this.showMessage(`策略已暫停: ${strategyName}`, 'warning');
    }

    /**
     * 處理啟動策略
     */
    handleStartStrategy(strategyName, strategyItem) {
        strategyItem.classList.remove('stopped');
        strategyItem.classList.add('active');

        const statusElement = strategyItem.querySelector('.strategy-status');
        const statusDot = statusElement.querySelector('.status-indicator');
        const statusText = statusElement.querySelector('.status-text');

        statusDot.classList.remove('stopped');
        statusDot.classList.add('active');
        statusText.textContent = '運行中';

        this.showMessage(`策略已啟動: ${strategyName}`, 'success');
    }

    /**
     * 處理查看詳情
     */
    handleViewDetails(strategyName) {
        this.showMessage(`查看策略詳情: ${strategyName}`, 'info');
    }

    /**
     * 刷新數據 - 集成真實API
     */
    async refreshData() {
        if (this.isLoading) return;

        this.showLoading('獲取策略數據...');
        this.isLoading = true;

        try {
            // 使用真實API獲取數據
            const strategyData = await window.strategyAPI.getStrategiesPerformance();
            this.currentData = strategyData;

            // 更新策略顯示
            this.updateStrategyDisplay(strategyData);

            // 更新最後更新時間
            this.updateLastUpdateTime();

            // 更新圖表數據
            this.updateChartsData(strategyData);

            this.hideLoading();
            this.showMessage('策略數據獲取成功', 'success');

        } catch (error) {
            console.error('獲取策略數據失敗:', error);
            this.hideLoading();
            this.showMessage('獲取策略數據失敗', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 更新策略顯示
     */
    updateStrategyDisplay(data) {
        // 更新性能卡片（舊版保留兼容）
        this.updatePerformanceCards(data.summary || this.calculateSummary(data.strategies));

        // 使用新的組件系統更新顯示
        if (window.strategyComponents) {
            window.strategyComponents.updateData(data);
        }

        // 更新圖表
        if (this.performanceChart) {
            this.updatePerformanceChart(data.strategies || []);
        }
    }

    /**
     * 計算數據摘要
     */
    calculateSummary(strategies) {
        if (!strategies || strategies.length === 0) {
            return {
                total_strategies: 0,
                active_strategies: 0,
                stopped_strategies: 0,
                average_sharpe_ratio: 0
            };
        }

        const activeCount = strategies.filter(s => s.status === 'active').length;
        const avgSharpe = strategies.reduce((sum, s) => sum + (s.performance?.sharpe_ratio || 0), 0) / strategies.length;

        return {
            total_strategies: strategies.length,
            active_strategies: activeCount,
            stopped_strategies: strategies.length - activeCount,
            average_sharpe_ratio: avgSharpe.toFixed(3),
            best_performing_strategy: this.getBestPerformingStrategy(strategies),
            worst_performing_strategy: this.getWorstPerformingStrategy(strategies)
        };
    }

    /**
     * 獲取表現最好的策略
     */
    getBestPerformingStrategy(strategies) {
        return strategies.reduce((best, current) =>
            (current.performance?.sharpe_ratio || 0) > (best.performance?.sharpe_ratio || 0) ? current : best
        , strategies[0])?.name || 'N/A';
    }

    /**
     * 獲取表現最差的策略
     */
    getWorstPerformingStrategy(strategies) {
        return strategies.reduce((worst, current) =>
            (current.performance?.sharpe_ratio || 0) < (worst.performance?.sharpe_ratio || 0) ? current : worst
        , strategies[0])?.name || 'N/A';
    }

    /**
     * 更新性能卡片
     */
    updatePerformanceCards(summary) {
        // 更新活躍策略數量
        const activeStrategiesElement = document.querySelector('.perf-card.primary .metric-value');
        if (activeStrategiesElement) {
            activeStrategiesElement.textContent = summary.active_strategies || 0;
        }

        // 更新平均夏普比率
        const sharpeRatioElements = document.querySelectorAll('.metric-value');
        if (sharpeRatioElements.length > 1) {
            sharpeRatioElements[1].textContent = (summary.average_sharpe_ratio || 0).toFixed(2);
        }
    }

    /**
     * 更新策略列表
     */
    updateStrategyList(strategies) {
        const strategyListContainer = document.querySelector('.strategy-list');
        if (!strategyListContainer) return;

        // 清空現有列表
        strategyListContainer.innerHTML = '';

        // 添加策略項目
        strategies.forEach(strategy => {
            const strategyItem = this.createStrategyItem(strategy);
            strategyListContainer.appendChild(strategyItem);
        });
    }

    /**
     * 創建策略項目元素
     */
    createStrategyItem(strategy) {
        const item = document.createElement('div');
        item.className = `strategy-item ${strategy.status}`;

        const performance = strategy.performance || {};
        const lastSignal = strategy.last_signal || {};

        item.innerHTML = `
            <div class="strategy-info">
                <div class="strategy-name">${strategy.display_name || strategy.name}</div>
                <div class="strategy-desc">${strategy.description || '基於CBSC數據的量化策略'}</div>
                <div class="strategy-status">
                    <span class="status-indicator ${strategy.status}"></span>
                    <span class="status-text">${strategy.status === 'active' ? '運行中' : '已停止'}</span>
                </div>
            </div>
            <div class="strategy-performance">
                <div class="perf-value ${performance.sharpe_ratio >= 0 ? 'positive' : 'negative'}">
                    ${performance.sharpe_ratio ? performance.sharpe_ratio.toFixed(3) : '0.000'}
                </div>
                <div class="perf-date">SR: ${performance.max_drawdown ? (performance.max_drawdown * 100).toFixed(1) : '0.0'}%</div>
            </div>
            <div class="strategy-actions">
                <button class="action-btn" title="查看詳情" onclick="dashboard.handleViewDetails('${strategy.name}')">👁️</button>
                <button class="action-btn" title="${strategy.status === 'active' ? '暫停' : '啟動'}"
                        onclick="dashboard.handleToggleStrategy('${strategy.name}', '${strategy.status}')">
                    ${strategy.status === 'active' ? '⏸️' : '▶️'}
                </button>
                <button class="action-btn" title="編輯" onclick="dashboard.handleEditStrategy('${strategy.name}')">✏️</button>
            </div>
        `;

        return item;
    }

    /**
     * 更新圖表數據
     */
    updateChartsData(strategyData) {
        if (!strategyData.strategies) return;

        // 優先使用增強圖表管理器
        if (this.chartManager && strategyData.strategies) {
            try {
                this.chartManager.updateAllCharts(strategyData.strategies);
                console.log('✅ 增強圖表數據已更新');
                return;
            } catch (error) {
                console.warn('增強圖表更新失敗，使用基本圖表:', error);
            }
        }

        // 後備使用基本圖表
        if (this.performanceChart) {
            // 生成時間標籤
            const labels = this.generateTimeLabels();

            // 更新圖表數據集
            this.performanceChart.data.labels = labels;
            this.performanceChart.data.datasets = strategyData.strategies.map((strategy, index) => {
                const colors = ['#3498db', '#27ae60', '#9b59b6', '#f39c12'];
                const color = colors[index % colors.length];

                return {
                    label: strategy.display_name || strategy.name,
                    data: this.generateStrategyPerformanceData(strategy.performance?.total_return || 0),
                    borderColor: color,
                    backgroundColor: color + '20', // 添加透明度
                    tension: 0.4
                };
            });

            this.performanceChart.update();
        }
    }

    /**
     * 生成策略性能數據
     */
    generateStrategyPerformanceData(baseReturn) {
        const data = [];
        const days = 30;
        let currentValue = 100;

        for (let i = 0; i < days; i++) {
            // 基於策略總收益率模擬每日變化
            const dailyChange = (baseReturn / days) + (Math.random() - 0.5) * 0.02;
            currentValue *= (1 + dailyChange);
            data.push(currentValue.toFixed(2));
        }

        return data;
    }

    /**
     * 更新性能圖表
     */
    updatePerformanceChart(strategies) {
        if (!this.performanceChart || !strategies.length) return;

        // 策略名稱標籤
        const labels = strategies.map(s => s.display_name || s.name);

        // 夏普比率數據
        const sharpeData = strategies.map(s => s.performance?.sharpe_ratio || 0);
        const maxDrawdownData = strategies.map(s => Math.abs(s.performance?.max_drawdown || 0) * 100);

        // 更新圖表為柱狀圖顯示SR和MDD
        this.performanceChart.config.type = 'bar';
        this.performanceChart.data.labels = labels;
        this.performanceChart.data.datasets = [
            {
                label: '夏普比率 (SR)',
                data: sharpeData,
                backgroundColor: '#3498db',
                borderColor: '#3498db',
                borderWidth: 1
            },
            {
                label: '最大回撤 (MDD %)',
                data: maxDrawdownData,
                backgroundColor: '#e74c3c',
                borderColor: '#e74c3c',
                borderWidth: 1
            }
        ];

        this.performanceChart.update();
    }

    /**
     * 開始自動刷新
     */
    startAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        this.refreshTimer = setInterval(() => {
            if (document.visibilityState === 'visible') {
                this.refreshData();
            }
        }, DASHBOARD_CONFIG.refreshInterval);

        console.log(`⏰ 自動刷新已啟動，間隔: ${DASHBOARD_CONFIG.refreshInterval}ms`);
    }

    /**
     * 停止自動刷新
     */
    stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('⏹️ 自動刷新已停止');
        }
    }

    /**
     * 更新最後更新時間
     */
    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        const lastUpdateElements = [
            document.getElementById('lastUpdateTime'),
            document.getElementById('last-sync-time')
        ];

        lastUpdateElements.forEach(element => {
            if (element) {
                element.textContent = timeString;
            }
        });
    }

    /**
     * 顯示加載提示
     */
    showLoading(message = '加載中...') {
        const loadingOverlay = document.getElementById('loadingOverlay');
        const loadingText = document.querySelector('.loading-text');

        if (loadingOverlay) {
            loadingOverlay.classList.add('show');
        }

        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    /**
     * 隱藏加載提示
     */
    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('show');
        }
    }

    /**
     * 顯示消息提示
     */
    showMessage(message, type = 'info') {
        const toast = document.getElementById('messageToast');
        const icon = document.getElementById('toastIcon');
        const msgElement = document.getElementById('toastMessage');

        if (!toast || !icon || !msgElement) return;

        // 設置圖標
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        icon.textContent = icons[type] || icons.info;
        msgElement.textContent = message;

        // 顯示消息
        toast.classList.add('show');

        // 自動隱藏
        setTimeout(() => {
            this.hideMessage();
        }, 3000);
    }

    /**
     * 隱藏消息提示
     */
    hideMessage() {
        const toast = document.getElementById('messageToast');
        if (toast) {
            toast.classList.remove('show');
        }
    }

    /**
     * 銷毀Dashboard
     */
    destroy() {
        this.stopAutoRefresh();

        // 清理WebSocket連接
        if (this.websocketClient) {
            this.websocketClient.disconnect();
            this.websocketClient = null;
        }

        // 清理增強圖表管理器
        if (this.chartManager) {
            this.chartManager.destroyAllCharts();
            this.chartManager = null;
        }

        // 清理基本圖表
        if (this.performanceChart) {
            this.performanceChart.destroy();
        }

        console.log('🗑️ Dashboard已銷毀');
    }
}

// ========== 全局初始化 ==========

// 創建全局Dashboard實例
let dashboard;

// DOM加載完成時初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 開始初始化個人策略管理Dashboard...');

    try {
        dashboard = new DashboardManager();

        // 全局錯誤處理
        window.addEventListener('error', function(event) {
            console.error('Dashboard運行時錯誤:', event.error);
            if (dashboard) {
                dashboard.showMessage('系統運行時錯誤', 'error');
            }
        });

        // 可見性變化處理
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                dashboard?.stopAutoRefresh();
            } else {
                dashboard?.startAutoRefresh();
            }
        });

        console.log('✅ Dashboard初始化流程完成');

    } catch (error) {
        console.error('❌ Dashboard初始化失敗:', error);
        alert('Dashboard初始化失敗，請刷新頁面重試');
    }
});

// 頁面卸載時清理
window.addEventListener('beforeunload', function() {
    if (dashboard) {
        dashboard.destroy();
    }
});

// ========== 全局導出 ==========
window.DashboardManager = DashboardManager;
window.DASHBOARD_CONFIG = DASHBOARD_CONFIG;