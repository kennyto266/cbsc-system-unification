/**
 * Enhanced Strategy Components - 增強版策略組件
 * 為個人策略管理Dashboard提供專業的UI組件
 * 支持策略列表、性能指標、狀態管理等
 */

// ========== Strategy List Component ==========
class EnhancedStrategyList {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.strategies = [];
        this.filteredStrategies = [];
        this.sortField = 'sharpeRatio';
        this.sortDirection = 'desc';
        this.filterStatus = 'all';
        this.isLoading = false;

        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        if (!this.container) {
            console.error(`Container with id ${containerId} not found`);
            return;
        }

        this.createStructure();
        this.bindEvents();
    }

    /**
     * Create component structure
     */
    createStructure() {
        this.container.innerHTML = `
            <div class="enhanced-strategy-list">
                <!-- Header with filters and controls -->
                <div class="strategy-list-header">
                    <div class="header-left">
                        <h3 class="section-title">
                            <span class="title-icon">📊</span>
                            策略監控面板
                        </h3>
                        <div class="strategy-stats">
                            <span class="stat-item">
                                <span class="stat-label">總策略:</span>
                                <span class="stat-value" id="totalStrategies">0</span>
                            </span>
                            <span class="stat-item">
                                <span class="stat-label">運行中:</span>
                                <span class="stat-value active" id="activeStrategies">0</span>
                            </span>
                        </div>
                    </div>
                    <div class="header-controls">
                        <div class="filter-group">
                            <label class="filter-label">狀態篩選:</label>
                            <div class="filter-buttons">
                                <button class="filter-btn active" data-status="all">全部</button>
                                <button class="filter-btn" data-status="active">運行中</button>
                                <button class="filter-btn" data-status="disabled">已停用</button>
                                <button class="filter-btn" data-status="error">錯誤</button>
                            </div>
                        </div>
                        <div class="sort-group">
                            <select class="sort-select" id="sortSelect">
                                <option value="sharpeRatio">按夏普比率排序</option>
                                <option value="maxDrawdown">按最大回撤排序</option>
                                <option value="totalReturn">按總收益率排序</option>
                                <option value="winRate">按勝率排序</option>
                                <option value="name">按名稱排序</option>
                            </select>
                        </div>
                    </div>
                </div>

                <!-- Loading indicator -->
                <div class="loading-overlay" id="loadingOverlay" style="display: none;">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">正在加載策略數據...</div>
                </div>

                <!-- Strategy table -->
                <div class="strategy-table-wrapper">
                    <table class="strategy-table">
                        <thead>
                            <tr>
                                <th class="col-name">策略名稱</th>
                                <th class="col-status">狀態</th>
                                <th class="col-sharpe">夏普比率</th>
                                <th class="col-drawdown">最大回撤</th>
                                <th class="col-return">總收益率</th>
                                <th class="col-winrate">勝率</th>
                                <th class="col-trades">交易次數</th>
                                <th class="col-signal">最新信號</th>
                                <th class="col-actions">操作</th>
                            </tr>
                        </thead>
                        <tbody id="strategyTableBody">
                            <!-- Strategy rows will be inserted here -->
                        </tbody>
                    </table>
                </div>

                <!-- Empty state -->
                <div class="empty-state" id="emptyState" style="display: none;">
                    <div class="empty-icon">📭</div>
                    <div class="empty-title">暫無策略數據</div>
                    <div class="empty-desc">請檢查API連接或稍後重試</div>
                </div>
            </div>
        `;
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Filter buttons
        this.container.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterStatus = btn.dataset.status;
                this.applyFiltersAndSort();
            });
        });

        // Sort select
        const sortSelect = this.container.querySelector('#sortSelect');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.sortField = e.target.value;
                this.applyFiltersAndSort();
            });
        }
    }

    /**
     * Update strategies data
     */
    updateStrategies(strategies) {
        this.strategies = strategies || [];
        this.applyFiltersAndSort();
        this.updateStats();
    }

    /**
     * Apply filters and sorting
     */
    applyFiltersAndSort() {
        // Apply filters
        this.filteredStrategies = this.strategies.filter(strategy => {
            if (this.filterStatus === 'all') return true;
            return strategy.status === this.filterStatus;
        });

        // Apply sorting
        this.filteredStrategies.sort((a, b) => {
            let aValue = a[this.sortField];
            let bValue = b[this.sortField];

            // Handle string sorting
            if (typeof aValue === 'string') {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }

            if (this.sortDirection === 'asc') {
                return aValue > bValue ? 1 : -1;
            } else {
                return aValue < bValue ? 1 : -1;
            }
        });

        this.render();
    }

    /**
     * Render strategy table
     */
    render() {
        const tbody = this.container.querySelector('#strategyTableBody');
        const emptyState = this.container.querySelector('#emptyState');
        const tableWrapper = this.container.querySelector('.strategy-table-wrapper');

        if (this.filteredStrategies.length === 0) {
            tbody.innerHTML = '';
            emptyState.style.display = 'flex';
            tableWrapper.style.display = 'none';
            return;
        }

        emptyState.style.display = 'none';
        tableWrapper.style.display = 'block';

        tbody.innerHTML = this.filteredStrategies.map(strategy => this.createStrategyRow(strategy)).join('');

        // Bind row events
        this.bindRowEvents();
    }

    /**
     * Create strategy row HTML
     */
    createStrategyRow(strategy) {
        const statusClass = this.getStatusClass(strategy.status);
        const signalType = strategy.lastSignal?.type || 'neutral';
        const signalClass = this.getSignalClass(signalType);

        return `
            <tr class="strategy-row" data-strategy-name="${strategy.name}">
                <td class="col-name">
                    <div class="strategy-name-cell">
                        <div class="strategy-icon">📈</div>
                        <div class="strategy-info">
                            <div class="strategy-name">${strategy.displayName || strategy.name}</div>
                            <div class="strategy-desc">${strategy.description || 'CBSC量化策略'}</div>
                        </div>
                    </div>
                </td>
                <td class="col-status">
                    <div class="status-indicator ${statusClass}">
                        <span class="status-dot"></span>
                        <span class="status-text">${this.getStatusText(strategy.status)}</span>
                    </div>
                </td>
                <td class="col-sharpe">
                    <div class="metric-value ${strategy.sharpeRatio >= 0 ? 'positive' : 'negative'}">
                        ${strategy.sharpeRatio ? strategy.sharpeRatio.toFixed(3) : '0.000'}
                    </div>
                </td>
                <td class="col-drawdown">
                    <div class="metric-value negative">
                        ${strategy.maxDrawdown ? (Math.abs(strategy.maxDrawdown) * 100).toFixed(1) + '%' : '0.0%'}
                    </div>
                </td>
                <td class="col-return">
                    <div class="metric-value ${strategy.totalReturn >= 0 ? 'positive' : 'negative'}">
                        ${strategy.totalReturn ? (strategy.totalReturn * 100).toFixed(1) + '%' : '0.0%'}
                    </div>
                </td>
                <td class="col-winrate">
                    <div class="metric-value">
                        ${strategy.winRate ? (strategy.winRate * 100).toFixed(1) + '%' : '0.0%'}
                    </div>
                </td>
                <td class="col-trades">
                    <div class="metric-value">
                        ${strategy.totalTrades || 0}
                    </div>
                </td>
                <td class="col-signal">
                    <div class="signal-indicator ${signalClass}">
                        ${this.getSignalIcon(signalType)}
                        <span class="signal-text">${this.getSignalText(signalType)}</span>
                    </div>
                </td>
                <td class="col-actions">
                    <div class="action-buttons">
                        <button class="action-btn toggle-btn"
                                onclick="window.enhancedStrategyList.toggleStrategy('${strategy.name}')"
                                title="${strategy.status === 'active' ? '暫停策略' : '啟動策略'}">
                            ${strategy.status === 'active' ? '⏸️' : '▶️'}
                        </button>
                        <button class="action-btn view-btn"
                                onclick="window.enhancedStrategyList.viewStrategyDetails('${strategy.name}')"
                                title="查看詳情">
                            👁️
                        </button>
                        <button class="action-btn edit-btn"
                                onclick="window.enhancedStrategyList.editStrategy('${strategy.name}')"
                                title="編輯策略">
                            ✏️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Bind events for table rows
     */
    bindRowEvents() {
        const rows = this.container.querySelectorAll('.strategy-row');
        rows.forEach(row => {
            // Add hover effect
            row.addEventListener('mouseenter', () => {
                row.classList.add('hover');
            });

            row.addEventListener('mouseleave', () => {
                row.classList.remove('hover');
            });

            // Add click handler for row (except action buttons)
            row.addEventListener('click', (e) => {
                if (!e.target.closest('.col-actions')) {
                    const strategyName = row.dataset.strategyName;
                    this.viewStrategyDetails(strategyName);
                }
            });
        });
    }

    /**
     * Update statistics
     */
    updateStats() {
        const totalStrategies = this.strategies.length;
        const activeStrategies = this.strategies.filter(s => s.status === 'active').length;

        const totalElement = this.container.querySelector('#totalStrategies');
        const activeElement = this.container.querySelector('#activeStrategies');

        if (totalElement) totalElement.textContent = totalStrategies;
        if (activeElement) activeElement.textContent = activeStrategies;
    }

    /**
     * Toggle strategy status
     */
    async toggleStrategy(strategyName) {
        const strategy = this.strategies.find(s => s.name === strategyName);
        if (!strategy) return;

        try {
            // Call API to toggle strategy
            if (window.strategyAPI) {
                const updated = await window.strategyAPI.toggleStrategy(strategyName);

                // Update local data
                Object.assign(strategy, updated);
                this.applyFiltersAndSort();

                // Show success message
                if (window.dashboard) {
                    window.dashboard.showMessage(
                        `策略 ${strategyName} 已${strategy.status === 'active' ? '啟動' : '暫停'}`,
                        'success'
                    );
                }
            }
        } catch (error) {
            console.error('Toggle strategy failed:', error);
            if (window.dashboard) {
                window.dashboard.showMessage('切換策略狀態失敗', 'error');
            }
        }
    }

    /**
     * View strategy details
     */
    async viewStrategyDetails(strategyName) {
        if (window.strategyComponents) {
            window.strategyComponents.viewStrategyDetails(strategyName);
        }
    }

    /**
     * Edit strategy
     */
    editStrategy(strategyName) {
        if (window.dashboard) {
            window.dashboard.handleEditStrategy(strategyName);
        }
    }

    /**
     * Show loading state
     */
    showLoading() {
        this.isLoading = true;
        const loadingOverlay = this.container.querySelector('#loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        this.isLoading = false;
        const loadingOverlay = this.container.querySelector('#loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    /**
     * Helper methods
     */
    getStatusClass(status) {
        const statusMap = {
            'active': 'running',
            'enabled': 'running',
            'disabled': 'stopped',
            'inactive': 'stopped',
            'error': 'error',
            'paused': 'paused'
        };
        return statusMap[status] || 'unknown';
    }

    getStatusText(status) {
        const statusMap = {
            'active': '運行中',
            'enabled': '運行中',
            'disabled': '已停用',
            'inactive': '已停用',
            'error': '錯誤',
            'paused': '已暫停'
        };
        return statusMap[status] || '未知';
    }

    getSignalClass(signalType) {
        const signalMap = {
            'buy': 'buy',
            'sell': 'sell',
            'hold': 'hold',
            'neutral': 'neutral'
        };
        return signalMap[signalType] || 'neutral';
    }

    getSignalIcon(signalType) {
        const iconMap = {
            'buy': '🟢',
            'sell': '🔴',
            'hold': '🟡',
            'neutral': '⚪'
        };
        return iconMap[signalType] || '⚪';
    }

    getSignalText(signalType) {
        const textMap = {
            'buy': '買入',
            'sell': '賣出',
            'hold': '持有',
            'neutral': '中性'
        };
        return textMap[signalType] || '中性';
    }
}

// ========== Performance Cards Component ==========
class PerformanceCards {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.metrics = {};
        this.init();
    }

    /**
     * Initialize component
     */
    init() {
        if (!this.container) {
            console.error(`Container with id ${containerId} not found`);
            return;
        }

        this.createStructure();
    }

    /**
     * Create component structure
     */
    createStructure() {
        this.container.innerHTML = `
            <div class="performance-cards">
                <h3 class="section-title">
                    <span class="title-icon">📊</span>
                    性能指標總覽
                </h3>
                <div class="cards-grid">
                    <!-- Average Sharpe Ratio Card -->
                    <div class="perf-card primary">
                        <div class="card-header">
                            <div class="card-icon">📈</div>
                            <div class="card-title">平均夏普比率</div>
                        </div>
                        <div class="card-metric">
                            <span class="metric-value" id="avgSharpeRatio">0.000</span>
                        </div>
                        <div class="card-change" id="avgSharpeChange">
                            <span class="change-icon">➡️</span>
                            <span class="change-text">無變化</span>
                        </div>
                    </div>

                    <!-- Average Max Drawdown Card -->
                    <div class="perf-card danger">
                        <div class="card-header">
                            <div class="card-icon">📉</div>
                            <div class="card-title">平均最大回撤</div>
                        </div>
                        <div class="card-metric">
                            <span class="metric-value" id="avgMaxDrawdown">0.0%</span>
                        </div>
                        <div class="card-change" id="avgDrawdownChange">
                            <span class="change-icon">➡️</span>
                            <span class="change-text">無變化</span>
                        </div>
                    </div>

                    <!-- Total Return Card -->
                    <div class="perf-card success">
                        <div class="card-header">
                            <div class="card-icon">💰</div>
                            <div class="card-title">總體收益率</div>
                        </div>
                        <div class="card-metric">
                            <span class="metric-value" id="totalReturn">0.0%</span>
                        </div>
                        <div class="card-change" id="totalReturnChange">
                            <span class="change-icon">➡️</span>
                            <span class="change-text">無變化</span>
                        </div>
                    </div>

                    <!-- Win Rate Card -->
                    <div class="perf-card info">
                        <div class="card-header">
                            <div class="card-icon">🎯</div>
                            <div class="card-title">平均勝率</div>
                        </div>
                        <div class="card-metric">
                            <span class="metric-value" id="avgWinRate">0.0%</span>
                        </div>
                        <div class="card-change" id="avgWinRateChange">
                            <span class="change-icon">➡️</span>
                            <span class="change-text">無變化</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Update metrics data
     */
    updateMetrics(strategies) {
        if (!strategies || strategies.length === 0) {
            this.setDefaultValues();
            return;
        }

        // Calculate metrics
        const activeStrategies = strategies.filter(s => s.status === 'active');

        const avgSharpeRatio = this.calculateAverage(activeStrategies, 'sharpeRatio');
        const avgMaxDrawdown = this.calculateAverage(activeStrategies, 'maxDrawdown');
        const totalReturn = this.calculateTotalReturn(activeStrategies);
        const avgWinRate = this.calculateAverage(activeStrategies, 'winRate');

        // Update UI with animation
        this.animateValue('avgSharpeRatio', avgSharpeRatio, 3);
        this.animateValue('avgMaxDrawdown', Math.abs(avgMaxDrawdown) * 100, 1, '%');
        this.animateValue('totalReturn', totalReturn * 100, 1, '%');
        this.animateValue('avgWinRate', avgWinRate * 100, 1, '%');

        // Update change indicators
        this.updateChangeIndicators(activeStrategies);
    }

    /**
     * Calculate average value
     */
    calculateAverage(strategies, field) {
        if (strategies.length === 0) return 0;

        const sum = strategies.reduce((acc, strategy) => acc + (strategy[field] || 0), 0);
        return sum / strategies.length;
    }

    /**
     * Calculate total return
     */
    calculateTotalReturn(strategies) {
        if (strategies.length === 0) return 0;

        // Simple average of returns for now
        // Could be modified to calculate portfolio return
        const sum = strategies.reduce((acc, strategy) => acc + (strategy.totalReturn || 0), 0);
        return sum / strategies.length;
    }

    /**
     * Animate value change
     */
    animateValue(elementId, endValue, decimals = 2, suffix = '') {
        const element = document.getElementById(elementId);
        if (!element) return;

        const startValue = parseFloat(element.textContent.replace(/[^0-9.-]/g, '')) || 0;
        const duration = 1000; // 1 second
        const steps = 30;
        const increment = (endValue - startValue) / steps;
        let currentStep = 0;

        const timer = setInterval(() => {
            currentStep++;
            const value = startValue + (increment * currentStep);
            element.textContent = value.toFixed(decimals) + suffix;

            if (currentStep >= steps) {
                clearInterval(timer);
                element.textContent = endValue.toFixed(decimals) + suffix;
            }
        }, duration / steps);
    }

    /**
     * Update change indicators
     */
    updateChangeIndicators(strategies) {
        // This would compare with previous values to show trends
        // For now, just set neutral indicators
        const changeElements = [
            'avgSharpeChange',
            'avgDrawdownChange',
            'totalReturnChange',
            'avgWinRateChange'
        ];

        changeElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.querySelector('.change-icon').textContent = '➡️';
                element.querySelector('.change-text').textContent = '無變化';
            }
        });
    }

    /**
     * Set default values when no data
     */
    setDefaultValues() {
        const defaults = {
            'avgSharpeRatio': '0.000',
            'avgMaxDrawdown': '0.0%',
            'totalReturn': '0.0%',
            'avgWinRate': '0.0%'
        };

        Object.entries(defaults).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });
    }
}

// Export components
window.EnhancedStrategyList = EnhancedStrategyList;
window.PerformanceCards = PerformanceCards;