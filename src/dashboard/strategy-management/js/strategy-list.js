/**
 * 个人策略管理Dashboard - 策略列表组件
 * Personal Strategy Management Dashboard - Strategy List Component
 */

import { STRATEGY_STATUS, STRATEGY_TYPES } from './constants.js';
import { formatPercentage, formatCurrency } from './utils.js';

/**
 * 策略列表组件类
 */
class StrategyList {
    constructor(container, strategyManager, eventBus) {
        this.container = container;
        this.strategyManager = strategyManager;
        this.eventBus = eventBus;
        this.strategies = [];
        this.selectedStrategyId = null;
        this.sortBy = 'created_at';
        this.sortOrder = 'desc';
        this.filterStatus = 'all';

        this.init();
    }

    /**
     * 初始化组件
     */
    init() {
        this.render();
        this.bindEvents();
        this.loadStrategies();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // Listen to strategy events
        this.eventBus.on('strategies:loaded', () => {
            this.loadStrategies();
        });

        this.eventBus.on('strategies:updated', () => {
            this.loadStrategies();
        });

        this.eventBus.on('strategy:added', () => {
            this.loadStrategies();
        });

        this.eventBus.on('strategy:updated', () => {
            this.loadStrategies();
        });

        this.eventBus.on('strategy:deleted', () => {
            this.loadStrategies();
        });

        // Listen to filter/sort changes
        this.eventBus.on('strategyList:filter', (filter) => {
            this.setFilter(filter);
        });

        this.eventBus.on('strategyList:sort', (sort) => {
            this.setSort(sort.by, sort.order);
        });
    }

    /**
     * 加载策略列表
     */
    loadStrategies() {
        this.strategies = this.strategyManager.getStrategies();
        this.applyFilterAndSort();
        this.render();
    }

    /**
     * 应用过滤和排序
     */
    applyFilterAndSort() {
        // Apply filter
        if (this.filterStatus !== 'all') {
            this.strategies = this.strategies.filter(strategy =>
                strategy.status === this.filterStatus
            );
        }

        // Apply sort
        this.strategies.sort((a, b) => {
            let valueA = a[this.sortBy];
            let valueB = b[this.sortBy];

            // Handle string comparison
            if (typeof valueA === 'string') {
                valueA = valueA.toLowerCase();
                valueB = valueB.toLowerCase();
            }

            // Handle date comparison
            if (this.sortBy.includes('_at')) {
                valueA = new Date(valueA);
                valueB = new Date(valueB);
            }

            let result = 0;
            if (valueA > valueB) result = 1;
            if (valueA < valueB) result = -1;

            return this.sortOrder === 'asc' ? result : -result;
        });
    }

    /**
     * 渲染组件
     */
    render() {
        if (this.strategies.length === 0) {
            this.renderEmptyState();
            return;
        }

        const html = `
            <div class="strategy-list-header">
                <div class="list-controls">
                    <select class="form-select filter-select" id="status-filter">
                        <option value="all">所有状态</option>
                        <option value="running">运行中</option>
                        <option value="stopped">已停止</option>
                        <option value="error">错误</option>
                    </select>
                    <select class="form-select sort-select" id="sort-select">
                        <option value="created_at-desc">创建时间（新到旧）</option>
                        <option value="created_at-asc">创建时间（旧到新）</option>
                        <option value="name-asc">名称（A-Z）</option>
                        <option value="name-desc">名称（Z-A）</option>
                        <option value="current_return-desc">收益率（高到低）</option>
                        <option value="current_return-asc">收益率（低到高）</option>
                    </select>
                </div>
            </div>
            <div class="strategy-cards" id="strategy-cards">
                ${this.strategies.map(strategy => this.createStrategyCard(strategy)).join('')}
            </div>
        `;

        this.container.innerHTML = html;
        this.bindCardEvents();
    }

    /**
     * 渲染空状态
     */
    renderEmptyState() {
        const html = `
            <div class="strategy-list-header">
                <div class="list-controls">
                    <select class="form-select filter-select" id="status-filter" disabled>
                        <option value="all">所有状态</option>
                    </select>
                    <select class="form-select sort-select" id="sort-select" disabled>
                        <option value="created_at-desc">创建时间（新到旧）</option>
                    </select>
                </div>
            </div>
            <div class="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="9" y1="9" x2="15" y2="9"/>
                    <line x1="9" y1="12" x2="15" y2="12"/>
                    <line x1="9" y1="15" x2="11" y2="15"/>
                </svg>
                <h3>暂无策略</h3>
                <p>点击"添加策略"按钮创建您的第一个交易策略</p>
            </div>
        `;

        this.container.innerHTML = html;
    }

    /**
     * 创建策略卡片
     * @param {Object} strategy - 策略对象
     * @returns {string} HTML字符串
     */
    createStrategyCard(strategy) {
        const statusClass = this.getStatusClass(strategy.status);
        const statusText = this.getStatusText(strategy.status);
        const returnClass = strategy.current_return >= 0 ? 'return-positive' : 'return-negative';
        const strategyType = STRATEGY_TYPES[strategy.strategy_type.toUpperCase()] || STRATEGY_TYPES.MOMENTUM;

        return `
            <div class="strategy-card ${this.selectedStrategyId === strategy.id ? 'selected' : ''}"
                 data-id="${strategy.id}">
                <div class="card-header">
                    <div class="card-title-wrapper">
                        <h3>${strategy.name}</h3>
                        <span class="strategy-type" title="${strategyType.description}">
                            ${strategyType.label}
                        </span>
                    </div>
                    <span class="status ${statusClass}" title="${statusText}">
                        ${statusText}
                    </span>
                </div>

                <div class="card-description">
                    ${strategy.description || '暂无描述'}
                </div>

                <div class="card-metrics">
                    <div class="metric">
                        <span class="label">收益率</span>
                        <span class="value ${returnClass}">
                            ${formatPercentage(strategy.current_return)}
                        </span>
                    </div>
                    <div class="metric">
                        <span class="label">Sharpe比率</span>
                        <span class="value">
                            ${strategy.sharpe_ratio ? strategy.sharpe_ratio.toFixed(2) : '--'}
                        </span>
                    </div>
                    <div class="metric">
                        <span class="label">最大回撤</span>
                        <span class="value">
                            ${formatPercentage(strategy.max_drawdown)}
                        </span>
                    </div>
                    <div class="metric">
                        <span class="label">初始资金</span>
                        <span class="value">
                            ${formatCurrency(strategy.initial_capital)}
                        </span>
                    </div>
                </div>

                <div class="card-footer">
                    <div class="card-info">
                        <span class="info-label">创建时间:</span>
                        <span class="info-value">${this.formatDate(strategy.created_at)}</span>
                    </div>
                    ${strategy.updated_at !== strategy.created_at ? `
                        <div class="card-info">
                            <span class="info-label">更新时间:</span>
                            <span class="info-value">${this.formatDate(strategy.updated_at)}</span>
                        </div>
                    ` : ''}
                </div>

                <div class="card-actions">
                    <button class="btn btn-sm btn-primary" data-action="view" data-id="${strategy.id}">
                        查看详情
                    </button>
                    <button class="btn btn-sm ${strategy.status === 'running' ? 'btn-warning' : 'btn-success'}"
                            data-action="${strategy.status === 'running' ? 'stop' : 'start'}"
                            data-id="${strategy.id}">
                        ${strategy.status === 'running' ? '停止' : '启动'}
                    </button>
                    <button class="btn btn-sm btn-secondary" data-action="edit" data-id="${strategy.id}">
                        编辑
                    </button>
                    <button class="btn btn-sm btn-danger" data-action="delete" data-id="${strategy.id}">
                        删除
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 绑定卡片事件
     */
    bindCardEvents() {
        // Filter and sort controls
        const statusFilter = this.container.querySelector('#status-filter');
        const sortSelect = this.container.querySelector('#sort-select');

        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => {
                this.setFilter(e.target.value);
            });
        }

        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                const [by, order] = e.target.value.split('-');
                this.setSort(by, order);
            });
        }

        // Card actions
        this.container.addEventListener('click', (e) => {
            const button = e.target.closest('button');
            if (!button) return;

            const action = button.dataset.action;
            const id = button.dataset.id;
            const strategy = this.strategyManager.getStrategyById(id);

            if (!strategy) {
                this.showNotification('策略不存在', 'error');
                return;
            }

            switch (action) {
                case 'view':
                    this.viewStrategy(id);
                    break;
                case 'start':
                    this.startStrategy(id);
                    break;
                case 'stop':
                    this.stopStrategy(id);
                    break;
                case 'edit':
                    this.editStrategy(id);
                    break;
                case 'delete':
                    this.deleteStrategy(id);
                    break;
            }
        });

        // Card selection
        this.container.addEventListener('click', (e) => {
            const card = e.target.closest('.strategy-card');
            if (card && !e.target.closest('button')) {
                this.selectStrategy(card.dataset.id);
            }
        });
    }

    /**
     * 查看策略详情
     * @param {string} id - 策略ID
     */
    viewStrategy(id) {
        const strategy = this.strategyManager.getStrategyById(id);
        if (strategy) {
            this.eventBus.emit('strategy:view', strategy);
        }
    }

    /**
     * 启动策略
     * @param {string} id - 策略ID
     */
    async startStrategy(id) {
        try {
            await this.strategyManager.startStrategy(id);
            this.showNotification('策略启动成功', 'success');
        } catch (error) {
            this.showNotification(`启动策略失败: ${error.message}`, 'error');
        }
    }

    /**
     * 停止策略
     * @param {string} id - 策略ID
     */
    async stopStrategy(id) {
        try {
            await this.strategyManager.stopStrategy(id);
            this.showNotification('策略停止成功', 'success');
        } catch (error) {
            this.showNotification(`停止策略失败: ${error.message}`, 'error');
        }
    }

    /**
     * 编辑策略
     * @param {string} id - 策略ID
     */
    editStrategy(id) {
        const strategy = this.strategyManager.getStrategyById(id);
        if (strategy) {
            this.eventBus.emit('strategy:edit', strategy);
        }
    }

    /**
     * 删除策略
     * @param {string} id - 策略ID
     */
    async deleteStrategy(id) {
        const strategy = this.strategyManager.getStrategyById(id);
        if (!strategy) return;

        if (!confirm(`确定要删除策略"${strategy.name}"吗？`)) {
            return;
        }

        try {
            await this.strategyManager.deleteStrategy(id);
            this.showNotification('策略删除成功', 'success');
        } catch (error) {
            this.showNotification(`删除策略失败: ${error.message}`, 'error');
        }
    }

    /**
     * 选择策略
     * @param {string} id - 策略ID
     */
    selectStrategy(id) {
        // Remove previous selection
        if (this.selectedStrategyId) {
            const prevCard = this.container.querySelector(`[data-id="${this.selectedStrategyId}"]`);
            if (prevCard) {
                prevCard.classList.remove('selected');
            }
        }

        // Add new selection
        this.selectedStrategyId = id;
        const card = this.container.querySelector(`[data-id="${id}"]`);
        if (card) {
            card.classList.add('selected');
        }

        // Emit selection event
        const strategy = this.strategyManager.getStrategyById(id);
        this.eventBus.emit('strategy:selected', strategy);
    }

    /**
     * 设置过滤器
     * @param {string} status - 状态过滤
     */
    setFilter(status) {
        this.filterStatus = status;
        this.loadStrategies();
    }

    /**
     * 设置排序
     * @param {string} by - 排序字段
     * @param {string} order - 排序顺序
     */
    setSort(by, order) {
        this.sortBy = by;
        this.sortOrder = order;
        this.loadStrategies();
    }

    /**
     * 获取状态类名
     * @param {string} status - 状态值
     * @returns {string} 类名
     */
    getStatusClass(status) {
        const statusConfig = STRATEGY_STATUS[status.toUpperCase()];
        return statusConfig ? statusConfig.value : status;
    }

    /**
     * 获取状态文本
     * @param {string} status - 状态值
     * @returns {string} 状态文本
     */
    getStatusText(status) {
        const statusConfig = STRATEGY_STATUS[status.toUpperCase()];
        return statusConfig ? statusConfig.label : status;
    }

    /**
     * 格式化日期
     * @param {string} dateStr - 日期字符串
     * @returns {string} 格式化后的日期
     */
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('zh-CN');
    }

    /**
     * 显示通知
     * @param {string} message - 消息内容
     * @param {string} type - 通知类型
     */
    showNotification(message, type = 'info') {
        this.eventBus.emit('notification', {
            type,
            message,
            duration: type === 'error' ? 5000 : 3000
        });
    }

    /**
     * 刷新列表
     */
    refresh() {
        this.loadStrategies();
    }

    /**
     * 获取选中的策略
     * @returns {Object|null} 选中的策略
     */
    getSelectedStrategy() {
        return this.selectedStrategyId
            ? this.strategyManager.getStrategyById(this.selectedStrategyId)
            : null;
    }

    /**
     * 清除选择
     */
    clearSelection() {
        if (this.selectedStrategyId) {
            const card = this.container.querySelector(`[data-id="${this.selectedStrategyId}"]`);
            if (card) {
                card.classList.remove('selected');
            }
            this.selectedStrategyId = null;
        }
    }
}

export default StrategyList;