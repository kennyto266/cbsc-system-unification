/**
 * Strategy List Component
 * Renders and manages the strategy list table with sorting and filtering
 */
class StrategyList {
  constructor(containerElement) {
    this.container = containerElement;
    this.strategies = [];
    this.filteredStrategies = [];
    this.sortField = 'sharpeRatio';
    this.sortDirection = 'desc';
    this.selectedCategory = 'all';
    this.eventListeners = new Map();

    this.init();
  }

  /**
   * Initialize the strategy list component
   */
  init() {
    this.createTableStructure();
    this.bindEvents();
  }

  /**
   * Create table structure
   */
  createTableStructure() {
    this.container.innerHTML = `
      <div class="strategy-list-wrapper">
        <div class="table-controls">
          <div class="search-box">
            <input type="text" id="strategy-search" placeholder="搜索策略名稱..." />
            <span class="search-icon">🔍</span>
          </div>
          <div class="view-options">
            <button class="btn btn-sm view-btn active" data-view="table">
              <span>📋</span> 表格
            </button>
            <button class="btn btn-sm view-btn" data-view="cards">
              <span>🎴</span> 卡片
            </button>
          </div>
        </div>

        <div class="strategy-table-container">
          <table class="strategy-table" id="strategy-table">
            <thead>
              <tr>
                <th class="sortable" data-field="name">
                  策略名稱
                  <span class="sort-indicator ${this.sortField === 'name' ? this.sortDirection : ''}">
                    ${this.getSortIcon('name')}
                  </span>
                </th>
                <th class="sortable" data-field="sharpeRatio">
                  夏普比率
                  <span class="sort-indicator ${this.sortField === 'sharpeRatio' ? this.sortDirection : ''}">
                    ${this.getSortIcon('sharpeRatio')}
                  </span>
                </th>
                <th class="sortable" data-field="maxDrawdown">
                  最大回撤
                  <span class="sort-indicator ${this.sortField === 'maxDrawdown' ? this.sortDirection : ''}">
                    ${this.getSortIcon('maxDrawdown')}
                  </span>
                </th>
                <th class="sortable" data-field="winRate">
                  勝率
                  <span class="sort-indicator ${this.sortField === 'winRate' ? this.sortDirection : ''}">
                    ${this.getSortIcon('winRate')}
                  </span>
                </th>
                <th>狀態</th>
                <th class="sortable" data-field="grade">
                  評級
                  <span class="sort-indicator ${this.sortField === 'grade' ? this.sortDirection : ''}">
                    ${this.getSortIcon('grade')}
                  </span>
                </th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody id="strategy-tbody">
              <!-- Strategy rows will be dynamically added here -->
            </tbody>
          </table>
        </div>

        <div class="strategy-cards-container" id="strategy-cards" style="display: none;">
          <!-- Strategy cards will be dynamically added here -->
        </div>

        <div class="table-footer">
          <div class="pagination">
            <span class="pagination-info">
              顯示 <span id="showing-count">0</span> / <span id="total-count">0</span> 策略
            </span>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Get sort icon for field
   */
  getSortIcon(field) {
    if (this.sortField !== field) return '⇅';
    return this.sortDirection === 'asc' ? '↑' : '↓';
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Sort functionality
    this.container.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', (e) => {
        const field = e.currentTarget.dataset.field;
        this.sortStrategies(field);
      });
    });

    // Search functionality
    const searchInput = this.container.querySelector('#strategy-search');
    if (searchInput) {
      searchInput.addEventListener('input', this.debounce((e) => {
        this.searchStrategies(e.target.value);
      }, 300));
    }

    // View toggle
    this.container.querySelectorAll('.view-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = e.currentTarget.dataset.view;
        this.switchView(view);
      });
    });
  }

  /**
   * Set strategies data
   */
  setStrategies(strategies) {
    this.strategies = strategies;
    this.applyFilters();
  }

  /**
   * Apply filters (category and search)
   */
  applyFilters() {
    this.filteredStrategies = this.strategies.filter(strategy => {
      // Category filter
      if (this.selectedCategory !== 'all' && strategy.category !== this.selectedCategory) {
        return false;
      }

      // Search filter
      const searchTerm = this.container.querySelector('#strategy-search')?.value || '';
      if (searchTerm && !strategy.name.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      return true;
    });

    this.render();
  }

  /**
   * Sort strategies by field
   */
  sortStrategies(field) {
    if (this.sortField === field) {
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortField = field;
      this.sortDirection = 'desc';
    }

    this.filteredStrategies.sort((a, b) => {
      let aVal = a[field];
      let bVal = b[field];

      // Handle string comparison
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      let result = 0;
      if (aVal > bVal) result = 1;
      if (aVal < bVal) result = -1;

      return this.sortDirection === 'asc' ? result : -result;
    });

    this.render();
  }

  /**
   * Search strategies
   */
  searchStrategies(searchTerm) {
    this.applyFilters();
  }

  /**
   * Filter strategies by category
   */
  filterByCategory(category) {
    this.selectedCategory = category;
    this.applyFilters();
  }

  /**
   * Switch view between table and cards
   */
  switchView(view) {
    const tableView = this.container.querySelector('.strategy-table-container');
    const cardsView = this.container.querySelector('.strategy-cards-container');
    const viewButtons = this.container.querySelectorAll('.view-btn');

    viewButtons.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });

    if (view === 'table') {
      tableView.style.display = 'block';
      cardsView.style.display = 'none';
    } else {
      tableView.style.display = 'none';
      cardsView.style.display = 'block';
      this.renderCards();
    }
  }

  /**
   * Render the strategy list
   */
  render() {
    this.renderTable();
    this.updatePagination();
  }

  /**
   * Render table view
   */
  renderTable() {
    const tbody = this.container.querySelector('#strategy-tbody');
    if (!tbody) return;

    if (this.filteredStrategies.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="no-data">
            <div class="no-data-content">
              <span class="no-data-icon">📭</span>
              <p>沒有找到匹配的策略</p>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = this.filteredStrategies.map(strategy => `
      <tr class="strategy-row ${strategy.isActive ? 'active' : 'inactive'}" data-id="${strategy.id}">
        <td class="strategy-name-cell">
          <div class="strategy-info">
            <h4 class="strategy-name">${strategy.name}</h4>
            <p class="strategy-category">${this.getCategoryLabel(strategy.category)}</p>
          </div>
        </td>
        <td class="metric-cell">
          <span class="metric-value ${this.getMetricClass(strategy.sharpeRatio, 1.5)}">
            ${strategy.sharpeRatio.toFixed(2)}
          </span>
        </td>
        <td class="metric-cell">
          <span class="metric-value ${this.getMetricClass(-strategy.maxDrawdown, -0.1)}">
            ${(strategy.maxDrawdown * 100).toFixed(2)}%
          </span>
        </td>
        <td class="metric-cell">
          <span class="metric-value ${this.getMetricClass(strategy.winRate, 0.6)}">
            ${(strategy.winRate * 100).toFixed(1)}%
          </span>
        </td>
        <td class="status-cell">
          <div class="strategy-status" data-status="${strategy.isActive ? 'active' : 'inactive'}">
            <span class="status-indicator"></span>
            <span class="status-text">${strategy.isActive ? '運行中' : '已停止'}</span>
          </div>
        </td>
        <td class="grade-cell">
          <span class="grade-badge ${strategy.grade.replace('+', '-plus')}">${strategy.grade}</span>
        </td>
        <td class="actions-cell">
          <div class="action-buttons">
            <button class="btn btn-sm btn-icon toggle-btn" onclick="window.strategyList.toggleStrategy(${strategy.id})" title="${strategy.isActive ? '停用策略' : '啟用策略'}">
              ${strategy.isActive ? '⏸️' : '▶️'}
            </button>
            <button class="btn btn-sm btn-icon details-btn" onclick="window.strategyList.showStrategyDetails(${strategy.id})" title="查看詳情">
              📊
            </button>
            <button class="btn btn-sm btn-icon edit-btn" onclick="window.strategyList.editStrategy(${strategy.id})" title="編輯策略">
              ✏️
            </button>
          </div>
        </td>
      </tr>
    `).join('');

    // Add row hover effects
    tbody.querySelectorAll('.strategy-row').forEach(row => {
      row.addEventListener('mouseenter', (e) => {
        e.currentTarget.classList.add('hover');
      });
      row.addEventListener('mouseleave', (e) => {
        e.currentTarget.classList.remove('hover');
      });
    });
  }

  /**
   * Render cards view
   */
  renderCards() {
    const cardsContainer = this.container.querySelector('#strategy-cards');
    if (!cardsContainer) return;

    if (this.filteredStrategies.length === 0) {
      cardsContainer.innerHTML = `
        <div class="no-data">
          <span class="no-data-icon">📭</span>
          <p>沒有找到匹配的策略</p>
        </div>
      `;
      return;
    }

    cardsContainer.innerHTML = `
      <div class="strategy-cards-grid">
        ${this.filteredStrategies.map(strategy => this.createStrategyCard(strategy)).join('')}
      </div>
    `;
  }

  /**
   * Create strategy card HTML
   */
  createStrategyCard(strategy) {
    return `
      <div class="strategy-card ${strategy.isActive ? 'active' : 'inactive'}" data-id="${strategy.id}">
        <div class="card-header">
          <h3 class="card-title">${strategy.name}</h3>
          <span class="grade-badge ${strategy.grade.replace('+', '-plus')}">${strategy.grade}</span>
        </div>

        <div class="card-body">
          <p class="card-description">${strategy.description}</p>

          <div class="metrics-grid">
            <div class="metric-item">
              <span class="metric-label">夏普比率</span>
              <span class="metric-value ${this.getMetricClass(strategy.sharpeRatio, 1.5)}">
                ${strategy.sharpeRatio.toFixed(2)}
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">最大回撤</span>
              <span class="metric-value ${this.getMetricClass(-strategy.maxDrawdown, -0.1)}">
                ${(strategy.maxDrawdown * 100).toFixed(2)}%
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">勝率</span>
              <span class="metric-value ${this.getMetricClass(strategy.winRate, 0.6)}">
                ${(strategy.winRate * 100).toFixed(1)}%
              </span>
            </div>
            <div class="metric-item">
              <span class="metric-label">年化收益</span>
              <span class="metric-value ${this.getMetricClass(strategy.annualReturn, 0.15)}">
                ${(strategy.annualReturn * 100).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        <div class="card-footer">
          <div class="card-status">
            <span class="status-indicator ${strategy.isActive ? 'active' : 'inactive'}"></span>
            <span class="status-text">${strategy.isActive ? '運行中' : '已停止'}</span>
          </div>
          <div class="card-actions">
            <button class="btn btn-sm toggle-btn" onclick="window.strategyList.toggleStrategy(${strategy.id})">
              ${strategy.isActive ? '停用' : '啟用'}
            </button>
            <button class="btn btn-sm btn-secondary" onclick="window.strategyList.showStrategyDetails(${strategy.id})">
              詳情
            </button>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Get category label in Chinese
   */
  getCategoryLabel(category) {
    const labels = {
      'monthly_low_frequency': '月度低頻',
      'multi_strategy_validation': '多策略驗證',
      'multi_factor_model': '多因子模型',
      'core_cbsc_technical': '技術分析',
      'core_cbsc_sentiment': '情緒分析',
      'core_cbsc_aggressive': '激進策略'
    };
    return labels[category] || category;
  }

  /**
   * Get metric class for coloring
   */
  getMetricClass(value, threshold) {
    if (typeof threshold === 'number') {
      if (threshold > 0) {
        return value >= threshold ? 'positive' : value >= threshold * 0.7 ? 'neutral' : 'negative';
      } else {
        return value <= threshold ? 'positive' : value <= threshold * 0.7 ? 'neutral' : 'negative';
      }
    }
    return 'neutral';
  }

  /**
   * Update pagination info
   */
  updatePagination() {
    const showingCount = this.container.querySelector('#showing-count');
    const totalCount = this.container.querySelector('#total-count');

    if (showingCount) showingCount.textContent = this.filteredStrategies.length;
    if (totalCount) totalCount.textContent = this.strategies.length;
  }

  /**
   * Toggle strategy active status
   */
  async toggleStrategy(strategyId) {
    try {
      const strategy = this.strategies.find(s => s.id === strategyId);
      if (!strategy) return;

      // Emit event for parent to handle
      this.emit('strategy-toggle', {
        id: strategyId,
        currentState: strategy.isActive,
        newState: !strategy.isActive
      });

    } catch (error) {
      console.error('Failed to toggle strategy:', error);
      this.emit('error', '策略狀態切換失敗');
    }
  }

  /**
   * Update strategy status
   */
  updateStrategyStatus(strategyId, enabled) {
    const strategy = this.strategies.find(s => s.id === strategyId);
    if (strategy) {
      strategy.isActive = enabled;
      this.render();
    }
  }

  /**
   * Show strategy details
   */
  showStrategyDetails(strategyId) {
    const strategy = this.strategies.find(s => s.id === strategyId);
    if (strategy) {
      this.emit('show-details', strategy);
    }
  }

  /**
   * Edit strategy
   */
  editStrategy(strategyId) {
    const strategy = this.strategies.find(s => s.id === strategyId);
    if (strategy) {
      this.emit('edit-strategy', strategy);
    }
  }

  /**
   * Event emitter
   */
  emit(eventName, data) {
    const event = new CustomEvent(`strategy-list:${eventName}`, {
      detail: data
    });
    this.container.dispatchEvent(event);
  }

  /**
   * Debounce function
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Update sort indicators
   */
  updateSortIndicators() {
    this.container.querySelectorAll('th.sortable .sort-indicator').forEach(indicator => {
      const field = indicator.closest('th').dataset.field;
      indicator.className = `sort-indicator ${this.sortField === field ? this.sortDirection : ''}`;
      indicator.textContent = this.getSortIcon(field);
    });
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StrategyList;
}