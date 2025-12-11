/**
 * CBSC Strategy Dashboard JavaScript
 * Personal Strategy Management System
 * Implements core functionality for the strategy dashboard
 */

// Main Dashboard Class
class Dashboard {
  constructor() {
    this.strategies = [];
    this.performanceData = [];
    this.isConnected = false;
    this.currentPage = 'dashboard';
    this.refreshInterval = null;
    this.charts = {};
    this.notifications = [];

    // Configuration
    this.config = {
      apiUrl: 'http://localhost:3004',
      wsUrl: 'ws://localhost:3005/ws',
      refreshInterval: 30000, // 30 seconds
      retryAttempts: 3,
      retryDelay: 1000
    };

    // Mock data for development
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
        lastUpdate: new Date().toISOString()
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
        lastUpdate: new Date().toISOString()
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
        lastUpdate: new Date().toISOString()
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
        lastUpdate: new Date().toISOString()
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
        lastUpdate: new Date().toISOString()
      }
    ];

    this.init();
  }

  /**
   * Initialize the dashboard
   */
  async init() {
    try {
      console.log('Initializing CBSC Strategy Dashboard...');

      // Show loading screen
      this.showLoadingScreen();

      // Initialize components
      this.initializeEventListeners();
      this.initializeNavigation();
      this.initializeWebSocket();

      // Load initial data
      await this.loadStrategies();
      await this.loadPerformanceData();

      // Update UI
      this.updateStatsSummary();
      this.renderStrategyList();

      // Start auto-refresh
      this.startAutoRefresh();

      // Hide loading screen and show app
      this.hideLoadingScreen();
      this.showApp();

      this.showNotification('Dashboard載入成功', 'success');
      console.log('Dashboard initialized successfully');

    } catch (error) {
      console.error('Dashboard initialization failed:', error);
      this.handleError('系統載入失敗，請重新整理頁面', error);
      this.hideLoadingScreen();
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
    if (categoryFilter) {
      categoryFilter.addEventListener('change', (e) => {
        this.filterStrategies(e.target.value);
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
   * Connect to WebSocket
   */
  async connectWebSocket() {
    try {
      const ws = new WebSocket(this.config.wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        this.updateConnectionStatus(true);
      };

      ws.onmessage = (event) => {
        this.handleWebSocketMessage(event.data);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.updateConnectionStatus(false);
        // Attempt to reconnect
        setTimeout(() => this.connectWebSocket(), 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.updateConnectionStatus(false);
      };

      this.ws = ws;

    } catch (error) {
      console.error('WebSocket connection failed:', error);
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

      // Add data for first 3 strategies
      this.strategies.slice(0, 3).forEach((strategy, index) => {
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
   * Update statistics summary
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
   * Render strategy list
   */
  renderStrategyList() {
    const container = document.getElementById('strategy-list');
    if (!container) return;

    const activeStrategies = this.strategies.filter(s => s.isActive);

    container.innerHTML = activeStrategies.map(strategy => `
      <div class="strategy-item" data-id="${strategy.id}">
        <div class="strategy-header">
          <h3 class="strategy-name">${strategy.name}</h3>
          <span class="strategy-grade ${strategy.grade.replace('+', '-plus')}">${strategy.grade}</span>
        </div>
        <p class="strategy-description">${strategy.description}</p>
        <div class="strategy-metrics">
          <div class="strategy-metric">
            <span class="metric-label">年化收益</span>
            <span class="metric-value">${(strategy.annualReturn * 100).toFixed(2)}%</span>
          </div>
          <div class="strategy-metric">
            <span class="metric-label">夏普比率</span>
            <span class="metric-value">${strategy.sharpeRatio.toFixed(2)}</span>
          </div>
          <div class="strategy-metric">
            <span class="metric-label">最大回撤</span>
            <span class="metric-value">${(strategy.maxDrawdown * 100).toFixed(2)}%</span>
          </div>
          <div class="strategy-metric">
            <span class="metric-label">勝率</span>
            <span class="metric-value">${(strategy.winRate * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    `).join('');

    // Add click handlers
    container.querySelectorAll('.strategy-item').forEach(item => {
      item.addEventListener('click', () => {
        const strategyId = parseInt(item.dataset.id);
        this.showStrategyDetails(strategyId);
      });
    });
  }

  /**
   * Filter strategies by category
   */
  filterStrategies(category) {
    let filtered = this.strategies;

    if (category !== 'all') {
      filtered = this.strategies.filter(s => s.category === category);
    }

    // Update strategy list
    const container = document.getElementById('strategy-list');
    container.innerHTML = filtered.map(strategy => `
      <div class="strategy-item" data-id="${strategy.id}">
        <!-- Strategy content -->
      </div>
    `).join('');

    this.showNotification(`已篩選 ${filtered.length} 個策略`, 'info');
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

      this.updateStatsSummary();
      this.renderStrategyList();

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
   * Pause dashboard activities
   */
  pause() {
    this.stopAutoRefresh();
    console.log('Dashboard paused');
  }

  /**
   * Resume dashboard activities
   */
  resume() {
    this.startAutoRefresh();
    this.refreshData();
    console.log('Dashboard resumed');
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
  showStrategyDetails(strategyId) {
    const strategy = this.strategies.find(s => s.id === strategyId);
    if (!strategy) return;

    this.showNotification(`查看策略詳情: ${strategy.name}`, 'info');
    // TODO: Implement strategy details modal or page
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
    // Re-render charts or adjust layout
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
   * Handle WebSocket messages
   */
  handleWebSocketMessage(data) {
    try {
      const message = JSON.parse(data);

      switch (message.type) {
        case 'strategy_update':
          this.handleStrategyUpdate(message.data);
          break;
        case 'performance_update':
          this.handlePerformanceUpdate(message.data);
          break;
        case 'system_alert':
          this.showNotification(message.message, message.level || 'warning');
          break;
        default:
          console.log('Unknown message type:', message.type);
      }

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Handle strategy update
   */
  handleStrategyUpdate(data) {
    // Update strategy in memory
    const index = this.strategies.findIndex(s => s.id === data.id);
    if (index !== -1) {
      this.strategies[index] = { ...this.strategies[index], ...data };
      this.renderStrategyList();
      this.updateStatsSummary();
    }
  }

  /**
   * Handle performance update
   */
  handlePerformanceUpdate(data) {
    // Update performance data
    // TODO: Implement performance update logic
    console.log('Performance update received:', data);
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

// Global functions for button onclick handlers
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