/**
 * 策略列表和數值顯示組件
 * 提供專業的策略管理UI組件，包括詳細的數值顯示和交互功能
 */

// ========== 策略列表組件 ==========
class StrategyListComponent {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.strategies = [];
        this.sortField = 'sharpe_ratio';
        this.sortDirection = 'desc';
        this.filterStatus = 'all';

        this.init();
    }

    /**
     * 初始化組件
     */
    init() {
        this.createHeader();
        this.createListContainer();
        this.bindEvents();
    }

    /**
     * 創建列表頭部
     */
    createHeader() {
        const header = document.createElement('div');
        header.className = 'strategy-list-header';
        header.innerHTML = `
            <div class="list-title">
                <h3>📊 策略列表</h3>
                <span class="strategy-count">共 <span id="strategyCount">0</span> 個策略</span>
            </div>
            <div class="list-controls">
                <select id="sortSelect" class="sort-select">
                    <option value="sharpe_ratio">按夏普比率排序</option>
                    <option value="max_drawdown">按最大回撤排序</option>
                    <option value="total_return">按總收益率排序</option>
                    <option value="win_rate">按勝率排序</option>
                    <option value="name">按名稱排序</option>
                </select>
                <div class="filter-buttons">
                    <button class="filter-btn active" data-filter="all">全部</button>
                    <button class="filter-btn" data-filter="active">運行中</button>
                    <button class="filter-btn" data-filter="stopped">已停止</button>
                </div>
            </div>
        `;

        if (this.container) {
            this.container.appendChild(header);
        }
    }

    /**
     * 創建列表容器
     */
    createListContainer() {
        const listContainer = document.createElement('div');
        listContainer.className = 'strategy-list-container';
        listContainer.innerHTML = `
            <div class="strategy-grid">
                <!-- 策略卡片將在這裡動態生成 -->
            </div>
        `;

        if (this.container) {
            this.container.appendChild(listContainer);
            this.gridContainer = listContainer.querySelector('.strategy-grid');
        }
    }

    /**
     * 綁定事件
     */
    bindEvents() {
        // 排序選擇
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortField = e.target.value;
                this.render();
            });
        }

        // 過濾按鈕
        const filterButtons = document.querySelectorAll('.filter-btn');
        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                filterButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterStatus = btn.dataset.filter;
                this.render();
            });
        });
    }

    /**
     * 更新策略數據
     */
    updateStrategies(strategies) {
        this.strategies = strategies || [];
        this.render();
    }

    /**
     * 渲染策略列表
     */
    render() {
        if (!this.gridContainer) return;

        // 過濾策略
        const filteredStrategies = this.filterStrategies();

        // 排序策略
        const sortedStrategies = this.sortStrategies(filteredStrategies);

        // 更新計數
        this.updateStrategyCount(sortedStrategies.length);

        // 清空並重新渲染
        this.gridContainer.innerHTML = '';

        sortedStrategies.forEach(strategy => {
            const card = this.createStrategyCard(strategy);
            this.gridContainer.appendChild(card);
        });
    }

    /**
     * 過濾策略
     */
    filterStrategies() {
        if (this.filterStatus === 'all') {
            return this.strategies;
        }
        return this.strategies.filter(strategy =>
            strategy.status === this.filterStatus
        );
    }

    /**
     * 排序策略
     */
    sortStrategies(strategies) {
        return [...strategies].sort((a, b) => {
            let aValue = this.getSortValue(a, this.sortField);
            let bValue = this.getSortValue(b, this.sortField);

            if (this.sortField === 'name') {
                return this.sortDirection === 'asc'
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            }

            return this.sortDirection === 'asc'
                ? aValue - bValue
                : bValue - aValue;
        });
    }

    /**
     * 獲取排序值
     */
    getSortValue(strategy, field) {
        if (field === 'name') {
            return strategy.display_name || strategy.name;
        }
        return strategy.performance?.[field] || 0;
    }

    /**
     * 更新策略計數
     */
    updateStrategyCount(count) {
        const countElement = document.getElementById('strategyCount');
        if (countElement) {
            countElement.textContent = count;
        }
    }

    /**
     * 創建策略卡片
     */
    createStrategyCard(strategy) {
        const card = document.createElement('div');
        card.className = `strategy-card ${strategy.status}`;
        card.dataset.strategyName = strategy.name;

        const performance = strategy.performance || {};
        const lastSignal = strategy.last_signal || {};

        card.innerHTML = `
            <div class="strategy-card-header">
                <div class="strategy-info">
                    <h4 class="strategy-name">${strategy.display_name || strategy.name}</h4>
                    <p class="strategy-desc">${strategy.description || '基於CBSC數據的量化策略'}</p>
                    <div class="strategy-status ${strategy.status}">
                        <span class="status-indicator ${strategy.status}"></span>
                        <span class="status-text">${this.getStatusText(strategy.status)}</span>
                    </div>
                </div>
                <div class="strategy-actions">
                    <button class="action-btn primary" onclick="strategyComponents.toggleStrategy('${strategy.name}')">
                        ${strategy.status === 'active' ? '⏸️' : '▶️'}
                    </button>
                    <button class="action-btn" onclick="strategyComponents.viewStrategyDetails('${strategy.name}')">
                        👁️
                    </button>
                    <button class="action-btn" onclick="strategyComponents.editStrategy('${strategy.name}')">
                        ✏️
                    </button>
                </div>
            </div>

            <div class="strategy-metrics">
                <div class="metrics-row">
                    <div class="metric-item primary">
                        <div class="metric-label">夏普比率</div>
                        <div class="metric-value ${performance.sharpe_ratio >= 0 ? 'positive' : 'negative'}">
                            ${performance.sharpe_ratio ? performance.sharpe_ratio.toFixed(3) : '0.000'}
                        </div>
                    </div>
                    <div class="metric-item danger">
                        <div class="metric-label">最大回撤</div>
                        <div class="metric-value">
                            ${performance.max_drawdown ? (Math.abs(performance.max_drawdown) * 100).toFixed(1) : '0.0'}%
                        </div>
                    </div>
                    <div class="metric-item success">
                        <div class="metric-label">總收益率</div>
                        <div class="metric-value ${performance.total_return >= 0 ? 'positive' : 'negative'}">
                            ${performance.total_return ? (performance.total_return * 100).toFixed(1) : '0.0'}%
                        </div>
                    </div>
                </div>

                <div class="metrics-row">
                    <div class="metric-item info">
                        <div class="metric-label">勝率</div>
                        <div class="metric-value">
                            ${performance.win_rate ? (performance.win_rate * 100).toFixed(1) : '0.0'}%
                        </div>
                    </div>
                    <div class="metric-item warning">
                        <div class="metric-label">交易次數</div>
                        <div class="metric-value">
                            ${performance.total_trades || 0}
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">最後信號</div>
                        <div class="metric-value signal-type ${lastSignal.type || 'neutral'}">
                            ${this.getSignalTypeText(lastSignal.type)}
                        </div>
                    </div>
                </div>
            </div>

            ${lastSignal.timestamp ? `
            <div class="strategy-footer">
                <span class="last-update">最後更新: ${new Date(lastSignal.timestamp).toLocaleString('zh-CN')}</span>
                <span class="signal-strength">信號強度: ${lastSignal.strength ? (lastSignal.strength * 100).toFixed(0) : 0}%</span>
            </div>
            ` : ''}
        `;

        // 添加點擊事件顯示詳細信息
        card.addEventListener('click', (e) => {
            if (!e.target.closest('.strategy-actions')) {
                this.showStrategyDetails(strategy);
            }
        });

        return card;
    }

    /**
     * 獲取狀態文本
     */
    getStatusText(status) {
        const statusMap = {
            'active': '運行中',
            'stopped': '已停止',
            'paused': '已暫停',
            'error': '錯誤'
        };
        return statusMap[status] || '未知';
    }

    /**
     * 獲取信號類型文本
     */
    getSignalTypeText(signalType) {
        const signalMap = {
            'extreme_bullish': '強烈看漲',
            'bullish': '看漲',
            'bearish': '看跌',
            'extreme_bearish': '強烈看跌',
            'golden_cross': '金叉',
            'death_cross': '死叉',
            'momentum_shift': '動量轉變',
            'breakthrough': '突破',
            'squeeze': '擠壓',
            'confirmed_signal': '確認信號',
            'neutral': '中性'
        };
        return signalMap[signalType] || '中性';
    }

    /**
     * 顯示策略詳細信息
     */
    showStrategyDetails(strategy) {
        const modal = document.getElementById('strategyModal');
        if (!modal) {
            this.createDetailsModal();
        }

        this.populateModal(strategy);
        document.getElementById('strategyModal').classList.add('show');
    }
}

// ========== 數值顯示組件 ==========
class PerformanceMetricsComponent {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.data = null;
        this.init();
    }

    /**
     * 初始化組件
     */
    init() {
        this.createMetricsGrid();
    }

    /**
     * 創建性能指標網格
     */
    createMetricsGrid() {
        if (!this.container) return;

        this.container.innerHTML = `
            <div class="metrics-grid">
                <div class="metric-card primary">
                    <div class="metric-header">
                        <h3 class="metric-title">活躍策略</h3>
                        <span class="metric-icon">🚀</span>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value" id="activeStrategiesCount">0</div>
                        <div class="metric-label">個策略</div>
                    </div>
                </div>

                <div class="metric-card success">
                    <div class="metric-header">
                        <h3 class="metric-title">平均夏普比率</h3>
                        <span class="metric-icon">📈</span>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value" id="averageSharpeRatio">0.000</div>
                        <div class="metric-label">SR</div>
                    </div>
                </div>

                <div class="metric-card danger">
                    <div class="metric-header">
                        <h3 class="metric-title">最大回撤</h3>
                        <span class="metric-icon">📉</span>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value" id="maxDrawdownValue">0.0%</div>
                        <div class="metric-label">MDD</div>
                    </div>
                </div>

                <div class="metric-card info">
                    <div class="metric-header">
                        <h3 class="metric-title">總收益率</h3>
                        <span class="metric-icon">💰</span>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value" id="totalReturnValue">0.0%</div>
                        <div class="metric-label">Return</div>
                    </div>
                </div>

                <div class="metric-card warning">
                    <div class="metric-header">
                        <h3 class="metric-title">平均勝率</h3>
                        <span class="metric-icon">🎯</span>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value" id="averageWinRate">0.0%</div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-header">
                        <h3 class="metric-title">最佳策略</h3>
                        <span class="metric-icon">🏆</span>
                    </div>
                    <div class="metric-content">
                        <div class="metric-value" id="bestStrategy">-</div>
                        <div class="metric-label">Top Performer</div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 更新性能指標
     */
    updateMetrics(strategyData) {
        if (!strategyData || !strategyData.strategies) return;

        const strategies = strategyData.strategies;
        const summary = strategyData.summary || this.calculateSummary(strategies);

        // 更新活躍策略數量
        this.updateElement('activeStrategiesCount', summary.active_strategies);

        // 更新平均夏普比率
        const avgSharpe = summary.average_sharpe_ratio || 0;
        this.updateElement('averageSharpeRatio', avgSharpe.toFixed(3));

        // 更新最大回撤
        const maxDrawdown = this.getMaxDrawdown(strategies);
        this.updateElement('maxDrawdownValue', `${Math.abs(maxDrawdown * 100).toFixed(1)}%`);

        // 更新總收益率
        const totalReturn = this.getAverageReturn(strategies);
        this.updateElement('totalReturnValue', `${(totalReturn * 100).toFixed(1)}%`);

        // 更新平均勝率
        const avgWinRate = this.getAverageWinRate(strategies);
        this.updateElement('averageWinRate', `${(avgWinRate * 100).toFixed(1)}%`);

        // 更新最佳策略
        const bestStrategy = summary.best_performing_strategy || this.getBestStrategy(strategies);
        this.updateElement('bestStrategy', this.truncateName(bestStrategy, 12));
    }

    /**
     * 更新元素內容
     */
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    /**
     * 計算摘要數據
     */
    calculateSummary(strategies) {
        if (!strategies || strategies.length === 0) {
            return {
                active_strategies: 0,
                average_sharpe_ratio: 0,
                max_drawdown: 0,
                total_return: 0,
                win_rate: 0
            };
        }

        const activeCount = strategies.filter(s => s.status === 'active').length;
        const avgSharpe = strategies.reduce((sum, s) => sum + (s.performance?.sharpe_ratio || 0), 0) / strategies.length;

        return {
            active_strategies: activeCount,
            average_sharpe_ratio: avgSharpe
        };
    }

    /**
     * 獲取最大回撤
     */
    getMaxDrawdown(strategies) {
        if (!strategies.length) return 0;
        return Math.max(...strategies.map(s => Math.abs(s.performance?.max_drawdown || 0)));
    }

    /**
     * 獲取平均收益率
     */
    getAverageReturn(strategies) {
        if (!strategies.length) return 0;
        const totalReturn = strategies.reduce((sum, s) => sum + (s.performance?.total_return || 0), 0);
        return totalReturn / strategies.length;
    }

    /**
     * 獲取平均勝率
     */
    getAverageWinRate(strategies) {
        if (!strategies.length) return 0;
        const totalWinRate = strategies.reduce((sum, s) => sum + (s.performance?.win_rate || 0), 0);
        return totalWinRate / strategies.length;
    }

    /**
     * 獲取最佳策略
     */
    getBestStrategy(strategies) {
        if (!strategies.length) return '-';
        return strategies.reduce((best, current) =>
            (current.performance?.sharpe_ratio || 0) > (best.performance?.sharpe_ratio || 0) ? current : best
        , strategies[0])?.display_name || strategies[0]?.name || '-';
    }

    /**
     * 截斷名稱
     */
    truncateName(name, maxLength) {
        if (!name) return '-';
        return name.length > maxLength ? name.substring(0, maxLength) + '...' : name;
    }
}

// ========== 策略詳情模態框組件 ==========
class StrategyDetailsModal {
    constructor() {
        this.modal = null;
        this.currentStrategy = null;
        this.init();
    }

    /**
     * 初始化模態框
     */
    init() {
        this.createModal();
        this.bindEvents();
    }

    /**
     * 創建模態框
     */
    createModal() {
        const modalHtml = `
            <div id="strategyModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modalTitle">策略詳情</h3>
                        <button class="modal-close" onclick="strategyComponents.closeModal()">×</button>
                    </div>
                    <div class="modal-body">
                        <div id="modalContent">
                            <!-- 策略詳細信息將在這裡顯示 -->
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="strategyComponents.closeModal()">關閉</button>
                        <button class="btn btn-primary" onclick="strategyComponents.editCurrentStrategy()">編輯策略</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);
        this.modal = document.getElementById('strategyModal');
    }

    /**
     * 綁定事件
     */
    bindEvents() {
        // 點擊模態框外部關閉
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });

        // ESC鍵關閉
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('show')) {
                this.closeModal();
            }
        });
    }

    /**
     * 顯示策略詳情
     */
    show(strategy) {
        this.currentStrategy = strategy;
        this.populateModal(strategy);
        this.modal.classList.add('show');
    }

    /**
     * 關閉模態框
     */
    closeModal() {
        this.modal.classList.remove('show');
        this.currentStrategy = null;
    }

    /**
     * 填充模態框內容
     */
    populateModal(strategy) {
        const title = document.getElementById('modalTitle');
        const content = document.getElementById('modalContent');

        if (title) {
            title.textContent = `${strategy.display_name || strategy.name} - 詳細信息`;
        }

        if (content) {
            const performance = strategy.performance || {};
            const parameters = strategy.parameters || {};
            const lastSignal = strategy.last_signal || {};

            content.innerHTML = `
                <div class="strategy-details-grid">
                    <div class="detail-section">
                        <h4>基本信息</h4>
                        <div class="detail-row">
                            <span class="detail-label">策略名稱:</span>
                            <span class="detail-value">${strategy.display_name || strategy.name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">描述:</span>
                            <span class="detail-value">${strategy.description || '基於CBSC數據的量化策略'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">狀態:</span>
                            <span class="detail-value strategy-status ${strategy.status}">
                                <span class="status-indicator ${strategy.status}"></span>
                                ${strategy.status === 'active' ? '運行中' : '已停止'}
                            </span>
                        </div>
                    </div>

                    <div class="detail-section">
                        <h4>性能指標</h4>
                        <div class="detail-row">
                            <span class="detail-label">夏普比率:</span>
                            <span class="detail-value ${performance.sharpe_ratio >= 0 ? 'positive' : 'negative'}">
                                ${performance.sharpe_ratio ? performance.sharpe_ratio.toFixed(3) : '0.000'}
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">最大回撤:</span>
                            <span class="detail-value">
                                ${performance.max_drawdown ? (Math.abs(performance.max_drawdown) * 100).toFixed(1) : '0.0'}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">總收益率:</span>
                            <span class="detail-value ${performance.total_return >= 0 ? 'positive' : 'negative'}">
                                ${performance.total_return ? (performance.total_return * 100).toFixed(1) : '0.0'}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">年化收益率:</span>
                            <span class="detail-value ${performance.annual_return >= 0 ? 'positive' : 'negative'}">
                                ${performance.annual_return ? (performance.annual_return * 100).toFixed(1) : '0.0'}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">勝率:</span>
                            <span class="detail-value">
                                ${performance.win_rate ? (performance.win_rate * 100).toFixed(1) : '0.0'}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Calmar比率:</span>
                            <span class="detail-value">
                                ${performance.calmar_ratio ? performance.calmar_ratio.toFixed(3) : '0.000'}
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">交易次數:</span>
                            <span class="detail-value">${performance.total_trades || 0}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">波動率:</span>
                            <span class="detail-value">
                                ${performance.volatility ? (performance.volatility * 100).toFixed(1) : '0.0'}%
                            </span>
                        </div>
                    </div>

                    <div class="detail-section">
                        <h4>策略參數</h4>
                        ${Object.keys(parameters).length > 0 ?
                            Object.entries(parameters).map(([key, value]) => `
                                <div class="detail-row">
                                    <span class="detail-label">${this.formatParameterName(key)}:</span>
                                    <span class="detail-value">${value}</span>
                                </div>
                            `).join('') :
                            '<div class="detail-row"><span class="detail-value">無參數配置</span></div>'
                        }
                    </div>

                    <div class="detail-section">
                        <h4>最新信號</h4>
                        <div class="detail-row">
                            <span class="detail-label">信號類型:</span>
                            <span class="detail-value signal-type ${lastSignal.type || 'neutral'}">
                                ${this.getSignalTypeText(lastSignal.type)}
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">信號強度:</span>
                            <span class="detail-value">
                                ${lastSignal.strength ? (lastSignal.strength * 100).toFixed(0) : 0}%
                            </span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">生成時間:</span>
                            <span class="detail-value">
                                ${lastSignal.timestamp ? new Date(lastSignal.timestamp).toLocaleString('zh-CN') : '無'}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }
    }

    /**
     * 格式化參數名稱
     */
    formatParameterName(key) {
        const paramMap = {
            'rsi_period': 'RSI週期',
            'buy_threshold': '買入閾值',
            'sell_threshold': '賣出閾值',
            'fast_period': '快線週期',
            'slow_period': '慢線週期',
            'signal_period': '信號週期',
            'volatility_window': '波動率窗口',
            'volume_threshold': '成交量閾值'
        };
        return paramMap[key] || key;
    }

    /**
     * 獲取信號類型文本
     */
    getSignalTypeText(signalType) {
        const signalMap = {
            'extreme_bullish': '強烈看漲',
            'bullish': '看漲',
            'bearish': '看跌',
            'extreme_bearish': '強烈看跌',
            'golden_cross': '金叉',
            'death_cross': '死叉',
            'momentum_shift': '動量轉變',
            'breakthrough': '突破',
            'squeeze': '擠壓',
            'confirmed_signal': '確認信號',
            'neutral': '中性'
        };
        return signalMap[signalType] || '中性';
    }

    /**
     * 編輯當前策略
     */
    editCurrentStrategy() {
        if (this.currentStrategy) {
            window.dashboard?.handleEditStrategy(this.currentStrategy.name);
            this.closeModal();
        }
    }
}

// ========== 組件管理器 ==========
class StrategyComponentsManager {
    constructor() {
        this.strategyList = null;
        this.performanceMetrics = null;
        this.detailsModal = null;
        this.init();
    }

    /**
     * 初始化所有組件
     */
    init() {
        // 初始化策略列表
        this.strategyList = new StrategyListComponent('strategyListContainer');

        // 初始化性能指標
        this.performanceMetrics = new PerformanceMetricsComponent('performanceMetricsContainer');

        // 初始化詳情模態框
        this.detailsModal = new StrategyDetailsModal();
    }

    /**
     * 更新所有組件數據
     */
    updateData(strategyData) {
        if (this.strategyList) {
            this.strategyList.updateStrategies(strategyData.strategies);
        }

        if (this.performanceMetrics) {
            this.performanceMetrics.updateMetrics(strategyData);
        }
    }

    /**
     * 切換策略狀態
     */
    async toggleStrategy(strategyName) {
        if (window.dashboard) {
            return window.dashboard.handleToggleStrategy(strategyName, 'active'); // 會在內部獲取當前狀態
        }
    }

    /**
     * 查看策略詳情
     */
    viewStrategyDetails(strategyName) {
        if (window.strategyAPI) {
            window.strategyAPI.getStrategyDetails(strategyName)
                .then(strategy => {
                    if (this.detailsModal) {
                        this.detailsModal.show(strategy);
                    }
                })
                .catch(error => {
                    console.error('獲取策略詳情失敗:', error);
                    if (window.dashboard) {
                        window.dashboard.showMessage('獲取策略詳情失敗', 'error');
                    }
                });
        }
    }

    /**
     * 編輯策略
     */
    editStrategy(strategyName) {
        if (window.dashboard) {
            window.dashboard.handleEditStrategy(strategyName);
        }
    }

    /**
     * 關閉模態框
     */
    closeModal() {
        if (this.detailsModal) {
            this.detailsModal.closeModal();
        }
    }

    /**
     * 編輯當前策略（由模態框調用）
     */
    editCurrentStrategy() {
        if (this.detailsModal) {
            this.detailsModal.editCurrentStrategy();
        }
    }
}

// 導出組件管理器
window.StrategyListComponent = StrategyListComponent;
window.PerformanceMetricsComponent = PerformanceMetricsComponent;
window.StrategyDetailsModal = StrategyDetailsModal;
window.StrategyComponentsManager = StrategyComponentsManager;

// 創建全局實例
window.strategyComponents = new StrategyComponentsManager();