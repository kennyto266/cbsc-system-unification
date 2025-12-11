/**
 * Enhanced CBSC Strategy Dashboard JavaScript
 * Personal Strategy Management System with advanced UI components
 * Integrates StrategyList, PerformanceCards, StatusIndicator, and StrategyToggle components
 */

// Import component classes (they should be loaded before this file)
// Assumes components are loaded as separate script files

// Main Dashboard Class
class EnhancedDashboard {
  constructor() {
    this.strategies = [];
    this.performanceData = [];
    this.isConnected = false;
    this.currentPage = 'dashboard';
    this.refreshInterval = null;
    this.charts = {};
    this.notifications = [];

    // Component instances
    this.strategyList = null;
    this.performanceCards = null;
    this.statusIndicators = new Map();

    // Configuration
    this.config = {
      apiUrl: 'http://localhost:3004',
      wsUrl: 'ws://localhost:3005/ws',
      refreshInterval: 30000, // 30 seconds
      retryAttempts: 3,
      retryDelay: 1000
    };

    // Enhanced mock data with more realistic metrics
    this.mockStrategies = [
      {
        id: 1,
        name: '月度低頻RSI策略',
        category: 'monthly_low_frequency',
        annualReturn: 0.156,
        sharpeRatio: 1.24,
        maxDrawdown: 0.087,
        winRate: 0.632,
        riskLevel: 'medium',
        grade: 'A-',
        description: '基於月度RSI信號的低頻交易策略',
        isActive: true,
        lastUpdate: new Date().toISOString(),
        totalTrades: 48,
        winningTrades: 30,
        profit: 0.145
      },
      {
        id: 2,
        name: '月度MACD趨勢策略',
        category: 'monthly_low_frequency',
        annualReturn: 0.142,
        sharpeRatio: 1.18,
        maxDrawdown: 0.093,
        winRate: 0.598,
        riskLevel: 'medium',
        grade: 'B+',
        description: '利用月度MACD指標識別趨勢轉折點',
        isActive: true,
        lastUpdate: new Date().toISOString(),
        totalTrades: 52,
        winningTrades: 31,
        profit: 0.128
      },
      {
        id: 3,
        name: '動量突破策略',
        category: 'monthly_low_frequency',
        annualReturn: 0.189,
        sharpeRatio: 1.45,
        maxDrawdown: 0.112,
        winRate: 0.654,
        riskLevel: 'medium',
        grade: 'A',
        description: '捕捉市場動量突破的月度交易策略',
        isActive: false,
        lastUpdate: new Date().toISOString(),
        totalTrades: 61,
        winningTrades: 40,
        profit: 0.176
      },
      {
        id: 4,
        name: '多策略驗證系統',
        category: 'multi_strategy_validation',
        annualReturn: 0.198,
        sharpeRatio: 1.67,
        maxDrawdown: 0.098,
        winRate: 0.682,
        riskLevel: 'low',
        grade: 'A+',
        description: '結合多種策略信號進行風險控制',
        isActive: true,
        lastUpdate: new Date().toISOString(),
        totalTrades: 73,
        winningTrades: 50,
        profit: 0.187
      },
      {
        id: 5,
        name: '五因子量化模型',
        category: 'multi_factor_model',
        annualReturn: 0.267,
        sharpeRatio: 2.14,
        maxDrawdown: 0.125,
        winRate: 0.723,
        riskLevel: 'medium',
        grade: 'A+',
        description: '基於五個市場因子的量化模型',
        isActive: true,
        lastUpdate: new Date().toISOString(),
        totalTrades: 89,
        winningTrades: 64,
        profit: 0.254
      }
    ];

    this.init();
  }

  /**
   * Initialize the enhanced dashboard
   */
  async init() {
    try {
      console.log('Initializing Enhanced CBSC Strategy Dashboard...');

      // Show loading screen
      this.showLoadingScreen();

      // Initialize components
      await this.initializeComponents();

      // Initialize event listeners
      this.initializeEventListeners();
      this.initializeNavigation();
      this.initializeWebSocket();

      // Load initial data
      await this.loadStrategies();
      await this.loadPerformanceData();

      // Update UI with new components
      this.updateComponents();

      // Start auto-refresh
      this.startAutoRefresh();

      // Hide loading screen and show app
      this.hideLoadingScreen();
      this.showApp();

      this.showNotification('增強版Dashboard載入成功', 'success');
      console.log('Enhanced Dashboard initialized successfully');

    } catch (error) {
      console.error('Enhanced Dashboard initialization failed:', error);
      this.handleError('系統載入失敗，請重新整理頁面', error);
      this.hideLoadingScreen();
    }
  }

  /**
   * Initialize UI components
   */
  async initializeComponents() {
    try {
      // Initialize Strategy List
      const strategyListContainer = document.getElementById('strategy-list');
      if (strategyListContainer && typeof StrategyList !== 'undefined') {
        this.strategyList = new StrategyList(strategyListContainer);

        // Listen to strategy list events
        strategyListContainer.addEventListener('strategy-list:toggle', (e) => {
          this.handleStrategyToggle(e.detail);
        });

        strategyListContainer.addEventListener('strategy-list:show-details', (e) => {
          this.showStrategyDetails(e.detail);
        });

        strategyListContainer.addEventListener('strategy-list:edit-strategy', (e) => {
          this.editStrategy(e.detail);
        });

        // Make strategy list globally accessible for button onclick handlers
        window.strategyList = this.strategyList;
      }

      // Initialize Performance Cards
      const performanceContainer = document.getElementById('performance-cards');
      if (performanceContainer && typeof PerformanceCards !== 'undefined') {
        this.performanceCards = new PerformanceCards(performanceContainer);
      }

      // Initialize Status Indicators for each strategy
      this.initializeStatusIndicators();

      console.log('UI Components initialized successfully');

    } catch (error) {
      console.error('Failed to initialize components:', error);
      throw error;
    }
  }

  /**
   * Initialize status indicators
   */
  initializeStatusIndicators() {
    // Create status indicator containers dynamically
    const statusContainer = document.getElementById('status-indicators');
    if (statusContainer) {
      statusContainer.innerHTML = '';

      this.mockStrategies.forEach(strategy => {
        const indicatorWrapper = document.createElement('div');
        indicatorWrapper.className = 'status-indicator-item';
        indicatorWrapper.id = `status-${strategy.id}`;
        statusContainer.appendChild(indicatorWrapper);

        if (typeof StatusIndicator !== 'undefined') {
          const indicator = new StatusIndicator(indicatorWrapper, {
            size: 'small',
            showText: true,
            showIcon: true,
            animated: true
          });

          // Set initial status
          indicator.setActive(
            strategy.isActive ? '運行中' : '已停止',
            {
              lastUpdate: strategy.lastUpdate,
              strategyId: strategy.id,
              performance: `${(strategy.annualReturn * 100).toFixed(2)}%`
            }
          );

          this.statusIndicators.set(strategy.id, indicator);
        }
      });
    }
  }

  /**
   * Update all components with current data
   */
  updateComponents() {
    // Update strategy list
    if (this.strategyList) {
      this.strategyList.setStrategies(this.strategies);
    }

    // Update performance cards
    if (this.performanceCards) {
      this.performanceCards.updateMetrics(this.strategies);
    }

    // Update status indicators
    this.statusIndicators.forEach((indicator, strategyId) => {
      const strategy = this.strategies.find(s => s.id === strategyId);
      if (strategy) {
        if (strategy.isActive) {
          indicator.setActive(
            '運行中',
            {
              lastUpdate: strategy.lastUpdate,
              strategyId: strategy.id,
              performance: `${(strategy.annualReturn * 100).toFixed(2)}%`,
              trades: `${strategy.winningTrades}/${strategy.totalTrades}`
            }
          );
        } else {
          indicator.setInactive(
            '已停止',
            {
              lastUpdate: strategy.lastUpdate,
              strategyId: strategy.id
            }
          );
        }
      }
    });

    // Update legacy stats summary for backward compatibility
    this.updateStatsSummary();
  }

  /**
   * Handle strategy toggle from strategy list
   */
  async handleStrategyToggle(data) {
    try {
      console.log('Toggling strategy:', data.id, 'from', data.currentState, 'to', data.newState);

      // Show loading notification
      this.showNotification(`正在${data.newState ? '啟用' : '停用'}策略...`, 'info');

      // Update local data
      const strategy = this.strategies.find(s => s.id === data.id);
      if (strategy) {
        strategy.isActive = data.newState;
        strategy.lastUpdate = new Date().toISOString();
      }

      // Update status indicator
      const indicator = this.statusIndicators.get(data.id);
      if (indicator) {
        if (data.newState) {
          indicator.setLoading('正在啟用策略...');
          // Simulate API call delay
          setTimeout(() => {
            indicator.setActive('策略已啟用', {
              lastUpdate: new Date().toISOString(),
              strategyId: data.id
            });
          }, 1000);
        } else {
          indicator.setLoading('正在停用策略...');
          setTimeout(() => {
            indicator.setInactive('策略已停用', {
              lastUpdate: new Date().toISOString(),
              strategyId: data.id
            });
          }, 1000);
        }
      }

      // Update strategy list
      if (this.strategyList) {
        this.strategyList.updateStrategyStatus(data.id, data.newState);
      }

      // Update performance cards
      if (this.performanceCards) {
        this.performanceCards.updateMetrics(this.strategies);
      }

      // Show success notification
      this.showNotification(
        `策略${data.newState ? '啟用' : '停用'}成功`,
        'success'
      );

      // TODO: Call actual API to update strategy state
      // await this.updateStrategyOnServer(data.id, data.newState);

    } catch (error) {
      console.error('Failed to toggle strategy:', error);
      this.showNotification('策略狀態更新失敗', 'error');

      // Revert UI state
      if (this.strategyList) {
        this.strategyList.updateStrategyStatus(data.id, data.currentState);
      }
    }
  }

  /**
   * Initialize event listeners
   */
  initializeEventListeners() {
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        this.refreshData();
      });
    }

    // Category filter
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter && this.strategyList) {
      categoryFilter.addEventListener('change', (e) => {
        this.strategyList.filterByCategory(e.target.value);
      });
    }

    // Timeframe selector
    const timeframeSelect = document.getElementById('timeframe-select');
    if (timeframeSelect) {
      timeframeSelect.addEventListener('change', (e) => {
        this.updateTimeframe(e.target.value);
      });
    }

    // Window events
    window.addEventListener('resize', this.debounce(() => {
      this.handleResize();
    }, 250));

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      this.handleKeyboardShortcuts(e);
    });
  }

  /**
   * Initialize navigation
   */
  initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');

    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.dataset.page;
        this.navigateToPage(page);
      });
    });
  }

  /**
   * Initialize WebSocket connection
   */
  initializeWebSocket() {
    try {
      // For now, simulate connection
      setTimeout(() => {
        this.updateConnectionStatus(true);
      }, 1000);

      // TODO: Implement actual WebSocket connection
      // this.connectWebSocket();

    } catch (error) {
      console.warn('WebSocket initialization failed:', error);
      this.updateConnectionStatus(false);
    }
  }

  /**
   * Load strategies data
   */
  async loadStrategies() {
    try {
      // In development, use mock data
      this.strategies = this.mockStrategies;

      // TODO: Replace with actual API call
      // const response = await fetch(`${this.config.apiUrl}/api/strategies`);
      // this.strategies = await response.json();

      console.log(`Loaded ${this.strategies.length} strategies`);

    } catch (error) {
      console.error('Failed to load strategies:', error);
      throw error;
    }
  }

  /**
   * Load performance data
   */
  async loadPerformanceData() {
    try {
      // Generate mock performance data
      this.performanceData = this.generatePerformanceData();

      // TODO: Replace with actual API call
      // const response = await fetch(`${this.config.apiUrl}/api/performance`);
      // this.performanceData = await response.json();

      console.log(`Loaded performance data with ${this.performanceData.length} points`);

    } catch (error) {
      console.error('Failed to load performance data:', error);
      throw error;
    }
  }

  /**
   * Generate mock performance data
   */
  generatePerformanceData() {
    const data = [];
    const days = 30;

    for (let i = days; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);

      const dataPoint = {
        date: date.toISOString().split('T')[0],
        benchmark: 100 * (1 + Math.sin(i * 0.1) * 0.05 + (days - i) * 0.001)
      };

      // Add data for active strategies
      this.strategies.filter(s => s.isActive).forEach((strategy, index) => {
        const baseValue = 100;
        const trend = strategy.annualReturn / 365;
        const noise = (Math.random() - 0.5) * 0.01;
        dataPoint[strategy.name] = baseValue * (1 + trend * (days - i) + noise);
      });

      data.push(dataPoint);
    }

    return data;
  }

  /**
   * Update statistics summary (legacy support)
   */
  updateStatsSummary() {
    if (!this.strategies.length) return;

    // Calculate statistics
    const totalStrategies = this.strategies.length;
    const avgReturn = this.strategies.reduce((sum, s) => sum + s.annualReturn, 0) / totalStrategies;
    const avgSharpe = this.strategies.reduce((sum, s) => sum + s.sharpeRatio, 0) / totalStrategies;
    const avgWinRate = this.strategies.reduce((sum, s) => sum + s.winRate, 0) / totalStrategies;

    // Update DOM
    this.updateElement('total-strategies', totalStrategies);
    this.updateElement('avg-return', `${(avgReturn * 100).toFixed(2)}%`);
    this.updateElement('avg-sharpe', avgSharpe.toFixed(2));
    this.updateElement('avg-winrate', `${(avgWinRate * 100).toFixed(1)}%`);
  }

  /**
   * Update connection status
   */
  updateConnectionStatus(connected) {
    this.isConnected = connected;

    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');

    if (indicator && text) {
      if (connected) {
        indicator.className = 'status-indicator connected';
        text.textContent = '已連接';
      } else {
        indicator.className = 'status-indicator disconnected';
        text.textContent = '連接中斷';
      }
    }
  }

  /**
   * Navigate to a page
   */
  navigateToPage(page) {
    // Hide all pages
    document.querySelectorAll('.page-content').forEach(p => {
      p.classList.remove('active');
    });

    // Show target page
    const targetPage = document.getElementById(`${page}-page`);
    if (targetPage) {
      targetPage.classList.add('active');
    }

    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
      if (link.dataset.page === page) {
        link.classList.add('active');
      }
    });

    this.currentPage = page;
  }

  /**
   * Refresh all data
   */
  async refreshData() {
    try {
      this.showNotification('正在更新數據...', 'info');

      await this.loadStrategies();
      await this.loadPerformanceData();

      this.updateComponents();

      this.showNotification('數據更新完成', 'success');

    } catch (error) {
      console.error('Data refresh failed:', error);
      this.showNotification('數據更新失敗', 'error');
    }
  }

  /**
   * Start auto-refresh
   */
  startAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }

    this.refreshInterval = setInterval(() => {
      if (!document.hidden) {
        this.refreshData();
      }
    }, this.config.refreshInterval);
  }

  /**
   * Stop auto-refresh
   */
  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }

  /**
   * Show notification
   */
  showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
      <div class="notification-content">
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
      </div>
    `;

    container.appendChild(notification);

    // Auto-remove after duration
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, duration);
  }

  /**
   * Show strategy details
   */
  showStrategyDetails(strategy) {
    this.showNotification(`查看策略詳情: ${strategy.name}`, 'info');
    // TODO: Implement strategy details modal or page
  }

  /**
   * Edit strategy
   */
  editStrategy(strategy) {
    this.showNotification(`編輯策略: ${strategy.name}`, 'info');
    // TODO: Implement strategy editing interface
  }

  /**
   * Update timeframe
   */
  updateTimeframe(timeframe) {
    console.log('Updating timeframe to:', timeframe);
    // TODO: Implement timeframe change logic
    this.showNotification(`時間範圍已更新為 ${timeframe}`, 'info');
  }

  /**
   * Handle window resize
   */
  handleResize() {
    // Re-render components if needed
    console.log('Window resized');
  }

  /**
   * Handle keyboard shortcuts
   */
  handleKeyboardShortcuts(e) {
    // Ctrl/Cmd + R: Refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
      e.preventDefault();
      this.refreshData();
    }

    // Escape: Close modals/notifications
    if (e.key === 'Escape') {
      document.querySelectorAll('.notification').forEach(n => n.remove());
    }
  }

  /**
   * Show loading screen
   */
  showLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.classList.remove('hidden');
    }
  }

  /**
   * Hide loading screen
   */
  hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.classList.add('hidden');
    }
  }

  /**
   * Show application
   */
  showApp() {
    const app = document.getElementById('app');
    if (app) {
      app.classList.add('loaded');
    }
  }

  /**
   * Handle errors
   */
  handleError(message, error) {
    console.error(message, error);
    this.showNotification(message, 'error');
  }

  /**
   * Update element content
   */
  updateElement(id, content) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = content;
    }
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
}

// Global functions for button onclick handlers (backward compatibility)
function addNewStrategy() {
  if (window.dashboard) {
    window.dashboard.showNotification('新增策略功能即將推出', 'info');
  }
}

function toggleChartType() {
  if (window.dashboard) {
    window.dashboard.showNotification('圖表類型切換功能即將推出', 'info');
  }
}

function exportReport() {
  if (window.dashboard) {
    window.dashboard.showNotification('導出報告功能即將推出', 'info');
  }
}

function optimizeStrategies() {
  if (window.dashboard) {
    window.dashboard.showNotification('策略優化功能即將推出', 'info');
  }
}

function runBacktest() {
  if (window.dashboard) {
    window.dashboard.showNotification('回測分析功能即將推出', 'info');
  }
}

function viewAlerts() {
  if (window.dashboard) {
    window.dashboard.showNotification('風險提醒功能即將推出', 'info');
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = EnhancedDashboard;
}