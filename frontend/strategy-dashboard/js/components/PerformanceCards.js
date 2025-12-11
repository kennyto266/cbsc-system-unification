/**
 * Performance Cards Component
 * Displays performance metrics with animated values and trend indicators
 */
class PerformanceCards {
  constructor(containerElement) {
    this.container = containerElement;
    this.metrics = {};
    this.trends = {};
    this.animationDuration = 1000;
    this.updateQueue = [];
    this.isAnimating = false;

    this.init();
  }

  /**
   * Initialize the performance cards component
   */
  init() {
    this.createCardsStructure();
    this.setupAnimations();
  }

  /**
   * Create the cards structure
   */
  createCardsStructure() {
    this.container.innerHTML = `
      <div class="performance-cards-grid">
        <!-- Overall Performance Card -->
        <div class="performance-card primary" id="overall-card">
          <div class="card-header">
            <h3 class="card-title">總體表現</h3>
            <span class="card-icon">📊</span>
          </div>
          <div class="card-content">
            <div class="main-metric">
              <span class="metric-value" id="overall-score">-</span>
              <span class="metric-label">綜合評分</span>
            </div>
            <div class="trend-indicator" id="overall-trend">
              <span class="trend-icon"></span>
              <span class="trend-text"></span>
            </div>
          </div>
        </div>

        <!-- Sharpe Ratio Card -->
        <div class="performance-card success" id="sharpe-card">
          <div class="card-header">
            <h3 class="card-title">夏普比率</h3>
            <span class="card-icon">📈</span>
          </div>
          <div class="card-content">
            <div class="main-metric">
              <span class="metric-value" id="sharpe-value">-</span>
              <span class="metric-label">平均SR</span>
            </div>
            <div class="sub-metrics">
              <div class="sub-metric">
                <span class="sub-value" id="sharpe-best">-</span>
                <span class="sub-label">最高</span>
              </div>
              <div class="sub-metric">
                <span class="sub-value" id="sharpe-worst">-</span>
                <span class="sub-label">最低</span>
              </div>
            </div>
            <div class="trend-indicator" id="sharpe-trend">
              <span class="trend-icon"></span>
              <span class="trend-text"></span>
            </div>
          </div>
        </div>

        <!-- Max Drawdown Card -->
        <div class="performance-card warning" id="drawdown-card">
          <div class="card-header">
            <h3 class="card-title">最大回撤</h3>
            <span class="card-icon">📉</span>
          </div>
          <div class="card-content">
            <div class="main-metric">
              <span class="metric-value" id="drawdown-value">-</span>
              <span class="metric-label">平均MDD</span>
            </div>
            <div class="risk-gauge" id="risk-gauge">
              <div class="gauge-bar">
                <div class="gauge-fill" id="gauge-fill"></div>
              </div>
              <span class="gauge-label" id="risk-level">低風險</span>
            </div>
            <div class="trend-indicator" id="drawdown-trend">
              <span class="trend-icon"></span>
              <span class="trend-text"></span>
            </div>
          </div>
        </div>

        <!-- Win Rate Card -->
        <div class="performance-card info" id="winrate-card">
          <div class="card-header">
            <h3 class="card-title">勝率</h3>
            <span class="card-icon">🎯</span>
          </div>
          <div class="card-content">
            <div class="main-metric">
              <span class="metric-value" id="winrate-value">-</span>
              <span class="metric-label">平均勝率</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" id="winrate-progress"></div>
            </div>
            <div class="sub-metrics">
              <div class="sub-metric">
                <span class="sub-value" id="winrate-total">-</span>
                <span class="sub-label">總交易</span>
              </div>
              <div class="sub-metric">
                <span class="sub-value" id="winrate-wins">-</span>
                <span class="sub-label">獲勝</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Active Strategies Card -->
        <div class="performance-card" id="active-card">
          <div class="card-header">
            <h3 class="card-title">策略狀態</h3>
            <span class="card-icon">⚡</span>
          </div>
          <div class="card-content">
            <div class="status-breakdown">
              <div class="status-item active">
                <span class="status-indicator"></span>
                <span class="status-count" id="active-count">-</span>
                <span class="status-label">運行中</span>
              </div>
              <div class="status-item inactive">
                <span class="status-indicator"></span>
                <span class="status-count" id="inactive-count">-</span>
                <span class="status-label">已停止</span>
              </div>
              <div class="status-item">
                <span class="status-indicator"></span>
                <span class="status-count" id="total-count">-</span>
                <span class="status-label">總計</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Performance Trend Card -->
        <div class="performance-card trend-card" id="trend-card">
          <div class="card-header">
            <h3 class="card-title">近期表現</h3>
            <span class="card-icon">📊</span>
          </div>
          <div class="card-content">
            <div class="trend-chart">
              <canvas id="mini-trend-chart" width="200" height="60"></canvas>
            </div>
            <div class="trend-summary">
              <div class="trend-stat">
                <span class="trend-label">7日</span>
                <span class="trend-value" id="trend-7d">-</span>
              </div>
              <div class="trend-stat">
                <span class="trend-label">30日</span>
                <span class="trend-value" id="trend-30d">-</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Setup animation observers
   */
  setupAnimations() {
    // Intersection Observer for scroll animations
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
        }
      });
    }, { threshold: 0.1 });

    this.container.querySelectorAll('.performance-card').forEach(card => {
      observer.observe(card);
    });
  }

  /**
   * Update all metrics from strategies data
   */
  updateMetrics(strategies) {
    if (!strategies || strategies.length === 0) return;

    // Calculate metrics
    const activeStrategies = strategies.filter(s => s.isActive);
    const metrics = this.calculateMetrics(strategies);

    // Update overall score
    this.updateMetric('overall-score', metrics.overallScore);
    this.updateTrend('overall-trend', metrics.overallTrend);

    // Update Sharpe ratio
    this.updateMetric('sharpe-value', metrics.avgSharpe, true);
    this.updateMetric('sharpe-best', metrics.maxSharpe, true);
    this.updateMetric('sharpe-worst', metrics.minSharpe, true);
    this.updateTrend('sharpe-trend', metrics.sharpeTrend);

    // Update drawdown
    this.updateMetric('drawdown-value', metrics.avgDrawdown, true, true);
    this.updateRiskGauge(metrics.avgDrawdown);
    this.updateTrend('drawdown-trend', metrics.drawdownTrend);

    // Update win rate
    this.updateMetric('winrate-value', metrics.avgWinRate, true);
    this.updateProgressBar('winrate-progress', metrics.avgWinRate);
    this.updateMetric('winrate-total', metrics.totalTrades);
    this.updateMetric('winrate-wins', metrics.winningTrades);

    // Update strategy status
    this.updateMetric('active-count', activeStrategies.length);
    this.updateMetric('inactive-count', strategies.length - activeStrategies.length);
    this.updateMetric('total-count', strategies.length);

    // Update trend chart
    this.updateMiniChart(metrics.recentPerformance);

    // Store metrics for comparison
    this.metrics = metrics;
  }

  /**
   * Calculate performance metrics from strategies
   */
  calculateMetrics(strategies) {
    const activeStrategies = strategies.filter(s => s.isActive);

    if (strategies.length === 0) {
      return this.getDefaultMetrics();
    }

    // Basic metrics
    const avgSharpe = strategies.reduce((sum, s) => sum + s.sharpeRatio, 0) / strategies.length;
    const maxSharpe = Math.max(...strategies.map(s => s.sharpeRatio));
    const minSharpe = Math.min(...strategies.map(s => s.sharpeRatio));
    const avgDrawdown = strategies.reduce((sum, s) => sum + s.maxDrawdown, 0) / strategies.length;
    const avgWinRate = strategies.reduce((sum, s) => sum + s.winRate, 0) / strategies.length;

    // Overall score (0-100)
    const sharpeScore = Math.min(avgSharpe * 25, 50); // Max 50 points for SR > 2
    const drawdownScore = Math.max(50 - avgDrawdown * 200, 0); // Max 50 points for MDD < 25%
    const overallScore = Math.round(sharpeScore + drawdownScore);

    // Simulate trends (in real app, would use historical data)
    const trends = {
      overall: this.simulateTrend(0.02),
      sharpe: this.simulateTrend(0.05),
      drawdown: this.simulateTrend(-0.03)
    };

    // Recent performance (last 7 days)
    const recentPerformance = this.generateRecentPerformance();

    return {
      overallScore,
      overallTrend: trends.overall,
      avgSharpe,
      maxSharpe,
      minSharpe,
      sharpeTrend: trends.sharpe,
      avgDrawdown,
      drawdownTrend: trends.drawdown,
      avgWinRate,
      totalTrades: Math.round(strategies.reduce((sum, s) => sum + (s.totalTrades || 100), 0)),
      winningTrades: Math.round(strategies.reduce((sum, s) => sum + (s.winningTrades || 65), 0)),
      recentPerformance
    };
  }

  /**
   * Get default metrics when no data available
   */
  getDefaultMetrics() {
    return {
      overallScore: 0,
      overallTrend: { direction: 'neutral', value: 0 },
      avgSharpe: 0,
      maxSharpe: 0,
      minSharpe: 0,
      sharpeTrend: { direction: 'neutral', value: 0 },
      avgDrawdown: 0,
      drawdownTrend: { direction: 'neutral', value: 0 },
      avgWinRate: 0,
      totalTrades: 0,
      winningTrades: 0,
      recentPerformance: []
    };
  }

  /**
   * Simulate trend data
   */
  simulateTrend(baseValue) {
    const value = baseValue + (Math.random() - 0.5) * 0.02;
    return {
      direction: value > 0.01 ? 'up' : value < -0.01 ? 'down' : 'neutral',
      value: value * 100
    };
  }

  /**
   * Generate recent performance data
   */
  generateRecentPerformance() {
    const data = [];
    for (let i = 7; i >= 0; i--) {
      data.push({
        date: new Date(Date.now() - i * 24 * 60 * 60 * 1000),
        value: 100 + (Math.random() - 0.5) * 10 + (7 - i) * 0.5
      });
    }
    return data;
  }

  /**
   * Update a single metric with animation
   */
  updateMetric(elementId, value, isDecimal = false, isPercentage = false) {
    const element = document.getElementById(elementId);
    if (!element) return;

    let displayValue = value;
    if (isDecimal && isPercentage) {
      displayValue = (value * 100).toFixed(2) + '%';
    } else if (isDecimal) {
      displayValue = value.toFixed(2);
    } else if (isPercentage) {
      displayValue = value + '%';
    } else {
      displayValue = Math.round(value);
    }

    // Animate the change
    this.animateValueChange(element, element.textContent, displayValue);
  }

  /**
   * Animate value change with counting effect
   */
  animateValueChange(element, oldValue, newValue) {
    const oldNum = parseFloat(oldValue) || 0;
    const newNum = parseFloat(newValue) || 0;

    if (Math.abs(newNum - oldNum) < 0.01) {
      element.textContent = newValue;
      return;
    }

    const duration = this.animationDuration;
    const steps = 30;
    const increment = (newNum - oldNum) / steps;
    let current = oldNum;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      current += increment;

      if (step >= steps) {
        current = newNum;
        clearInterval(timer);
      }

      const displayValue = newValue.includes('%') ? current.toFixed(2) + '%' :
                          newValue.includes('.') ? current.toFixed(2) : Math.round(current);
      element.textContent = displayValue;

    }, duration / steps);
  }

  /**
   * Update trend indicator
   */
  updateTrend(elementId, trend) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const icon = element.querySelector('.trend-icon');
    const text = element.querySelector('.trend-text');

    // Set direction class
    element.className = `trend-indicator ${trend.direction}`;

    // Set icon
    if (icon) {
      icon.textContent = trend.direction === 'up' ? '📈' :
                        trend.direction === 'down' ? '📉' : '➡️';
    }

    // Set text
    if (text) {
      text.textContent = trend.direction === 'neutral' ? '持平' :
                        `${Math.abs(trend.value).toFixed(1)}%`;
    }
  }

  /**
   * Update risk gauge
   */
  updateRiskGauge(drawdown) {
    const gaugeFill = document.getElementById('gauge-fill');
    const riskLevel = document.getElementById('risk-level');

    if (!gaugeFill || !riskLevel) return;

    // Calculate fill percentage (0% at 0% drawdown, 100% at 25% drawdown)
    const fillPercent = Math.min(drawdown * 4, 100);
    gaugeFill.style.width = `${fillPercent}%`;

    // Set risk level
    let level, className;
    if (drawdown < 0.05) {
      level = '低風險';
      className = 'low';
    } else if (drawdown < 0.10) {
      level = '中風險';
      className = 'medium';
    } else if (drawdown < 0.15) {
      level = '高風險';
      className = 'high';
    } else {
      level = '極高風險';
      className = 'critical';
    }

    riskLevel.textContent = level;
    riskLevel.className = `gauge-label ${className}`;
    gaugeFill.className = `gauge-fill ${className}`;
  }

  /**
   * Update progress bar
   */
  updateProgressBar(elementId, value) {
    const progressBar = document.getElementById(elementId);
    if (!progressBar) return;

    const percent = Math.min(value * 100, 100);
    progressBar.style.width = `${percent}%`;
  }

  /**
   * Update mini trend chart
   */
  updateMiniChart(data) {
    const canvas = document.getElementById('mini-trend-chart');
    if (!canvas || !data.length) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Find min and max values
    const values = data.map(d => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const range = maxValue - minValue || 1;

    // Draw chart
    ctx.strokeStyle = '#3498db';
    ctx.lineWidth = 2;
    ctx.beginPath();

    data.forEach((point, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((point.value - minValue) / range) * height;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(52, 152, 219, 0.3)');
    gradient.addColorStop(1, 'rgba(52, 152, 219, 0)');

    ctx.fillStyle = gradient;
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fill();

    // Update trend summary
    const trend7d = this.calculateTrend(data.slice(-7));
    const trend30d = this.calculateTrend(data);

    this.updateMetric('trend-7d', trend7d, false, true);
    this.updateMetric('trend-30d', trend30d, false, true);
  }

  /**
   * Calculate trend percentage
   */
  calculateTrend(data) {
    if (data.length < 2) return 0;
    const first = data[0].value;
    const last = data[data.length - 1].value;
    return ((last - first) / first) * 100;
  }

  /**
   * Refresh all animations
   */
  refreshAnimations() {
    this.container.querySelectorAll('.performance-card').forEach(card => {
      card.classList.remove('animate-in');
      void card.offsetWidth; // Trigger reflow
      card.classList.add('animate-in');
    });
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PerformanceCards;
}