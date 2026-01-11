/**
 * Status Indicator Component
 * Provides visual status indicators with animations and tooltips
 */
class StatusIndicator {
  constructor(containerElement, options = {}) {
    this.container = containerElement;
    this.options = {
      size: options.size || 'medium', // small, medium, large
      showText: options.showText !== false,
      showIcon: options.showIcon !== false,
      animated: options.animated !== false,
      ...options
    };

    this.currentStatus = 'loading';
    this.message = '';
    this.details = {};
    this.tooltip = null;

    this.init();
  }

  /**
   * Initialize the status indicator
   */
  init() {
    this.createIndicator();
    this.setupEventListeners();
  }

  /**
   * Create the status indicator element
   */
  createIndicator() {
    this.container.innerHTML = `
      <div class="status-indicator-wrapper ${this.options.size}">
        <div class="status-indicator" data-status="${this.currentStatus}">
          ${this.options.showIcon ? `<span class="status-icon"></span>` : ''}
          ${this.options.animated ? '<div class="status-pulse"></div>' : ''}
        </div>
        ${this.options.showText ? `
          <div class="status-text-container">
            <span class="status-label">${this.getStatusLabel(this.currentStatus)}</span>
            <span class="status-message">${this.message}</span>
          </div>
        ` : ''}
        <div class="status-tooltip" role="tooltip">
          <div class="tooltip-content">
            <div class="tooltip-title">狀態詳情</div>
            <div class="tooltip-body"></div>
          </div>
          <div class="tooltip-arrow"></div>
        </div>
      </div>
    `;

    this.indicatorElement = this.container.querySelector('.status-indicator');
    this.iconElement = this.container.querySelector('.status-icon');
    this.labelElement = this.container.querySelector('.status-label');
    this.messageElement = this.container.querySelector('.status-message');
    this.tooltipElement = this.container.querySelector('.status-tooltip');
  }

  /**
   * Setup event listeners for tooltips and interactions
   */
  setupEventListeners() {
    const wrapper = this.container.querySelector('.status-indicator-wrapper');

    if (wrapper && this.tooltipElement) {
      // Show tooltip on hover
      wrapper.addEventListener('mouseenter', () => {
        this.showTooltip();
      });

      wrapper.addEventListener('mouseleave', () => {
        this.hideTooltip();
      });

      // Show tooltip on focus (accessibility)
      wrapper.addEventListener('focus', () => {
        this.showTooltip();
      });

      wrapper.addEventListener('blur', () => {
        this.hideTooltip();
      });

      // Make wrapper focusable
      wrapper.setAttribute('tabindex', '0');
      wrapper.setAttribute('role', 'button');
      wrapper.setAttribute('aria-label', '狀態指示器');
    }

    // Click handler for status actions
    wrapper.addEventListener('click', () => {
      this.handleStatusClick();
    });
  }

  /**
   * Set the status with optional message and details
   */
  setStatus(status, message = '', details = {}) {
    const oldStatus = this.currentStatus;
    this.currentStatus = status;
    this.message = message;
    this.details = details;

    // Update visual elements
    this.updateVisuals(oldStatus, status);

    // Update text
    this.updateText();

    // Update tooltip content
    this.updateTooltip();

    // Emit status change event
    this.emitStatusChange(oldStatus, status, details);
  }

  /**
   * Update visual elements
   */
  updateVisuals(oldStatus, newStatus) {
    // Update indicator class
    this.indicatorElement.setAttribute('data-status', newStatus);
    this.indicatorElement.className = `status-indicator ${newStatus} ${this.options.animated ? 'animated' : ''}`;

    // Update icon
    if (this.iconElement) {
      this.iconElement.textContent = this.getStatusIcon(newStatus);
    }

    // Animate status change
    if (this.options.animated && oldStatus !== newStatus) {
      this.animateStatusChange(oldStatus, newStatus);
    }
  }

  /**
   * Update text elements
   */
  updateText() {
    if (this.labelElement) {
      this.labelElement.textContent = this.getStatusLabel(this.currentStatus);
    }

    if (this.messageElement) {
      this.messageElement.textContent = this.message;
    }
  }

  /**
   * Animate status change
   */
  animateStatusChange(oldStatus, newStatus) {
    // Remove and re-add animation class
    this.indicatorElement.classList.remove('status-change');
    void this.indicatorElement.offsetWidth; // Trigger reflow
    this.indicatorElement.classList.add('status-change');

    // Add pulse effect
    if (this.options.animated) {
      this.addPulseEffect();
    }
  }

  /**
   * Add pulse effect for status changes
   */
  addPulseEffect() {
    const pulseElement = this.indicatorElement.querySelector('.status-pulse');
    if (pulseElement) {
      pulseElement.style.animation = 'none';
      void pulseElement.offsetWidth; // Trigger reflow
      pulseElement.style.animation = 'statusPulse 1s ease-out';
    }
  }

  /**
   * Get status icon
   */
  getStatusIcon(status) {
    const icons = {
      loading: '⏳',
      active: '✅',
      running: '🟢',
      success: '✅',
      completed: '✅',
      inactive: '⏸️',
      stopped: '⏹️',
      disabled: '🔴',
      error: '❌',
      failed: '❌',
      warning: '⚠️',
      caution: '⚠️',
      info: 'ℹ️',
      neutral: '⚪',
      unknown: '❓'
    };

    return icons[status] || icons.unknown;
  }

  /**
   * Get status label in Chinese
   */
  getStatusLabel(status) {
    const labels = {
      loading: '載入中',
      active: '運行中',
      running: '運行中',
      success: '成功',
      completed: '已完成',
      inactive: '非活躍',
      stopped: '已停止',
      disabled: '已停用',
      error: '錯誤',
      failed: '失敗',
      warning: '警告',
      caution: '注意',
      info: '信息',
      neutral: '中性',
      unknown: '未知'
    };

    return labels[status] || labels.unknown;
  }

  /**
   * Show tooltip
   */
  showTooltip() {
    if (!this.tooltipElement || !Object.keys(this.details).length) return;

    this.tooltipElement.classList.add('visible');
    this.positionTooltip();
  }

  /**
   * Hide tooltip
   */
  hideTooltip() {
    if (!this.tooltipElement) return;

    this.tooltipElement.classList.remove('visible');
  }

  /**
   * Position tooltip relative to container
   */
  positionTooltip() {
    const wrapper = this.container.querySelector('.status-indicator-wrapper');
    const rect = wrapper.getBoundingClientRect();
    const tooltipRect = this.tooltipElement.getBoundingClientRect();

    // Position above the indicator
    let top = rect.top - tooltipRect.height - 10;
    let left = rect.left + (rect.width - tooltipRect.width) / 2;

    // Adjust if tooltip goes off screen
    if (top < 10) {
      top = rect.bottom + 10;
    }

    if (left < 10) {
      left = 10;
    } else if (left + tooltipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tooltipRect.width - 10;
    }

    this.tooltipElement.style.top = `${top}px`;
    this.tooltipElement.style.left = `${left}px`;
  }

  /**
   * Update tooltip content
   */
  updateTooltip() {
    if (!this.tooltipElement) return;

    const tooltipBody = this.tooltipElement.querySelector('.tooltip-body');
    if (!tooltipBody) return;

    let content = '';

    // Add basic status info
    content += `
      <div class="tooltip-row">
        <span class="tooltip-label">狀態:</span>
        <span class="tooltip-value">${this.getStatusLabel(this.currentStatus)}</span>
      </div>
    `;

    // Add message if provided
    if (this.message) {
      content += `
        <div class="tooltip-row">
          <span class="tooltip-label">信息:</span>
          <span class="tooltip-value">${this.message}</span>
        </div>
      `;
    }

    // Add timestamp
    content += `
      <div class="tooltip-row">
        <span class="tooltip-label">更新時間:</span>
        <span class="tooltip-value">${new Date().toLocaleString('zh-TW')}</span>
      </div>
    `;

    // Add custom details
    Object.entries(this.details).forEach(([key, value]) => {
      const label = this.formatDetailLabel(key);
      const formattedValue = this.formatDetailValue(key, value);
      content += `
        <div class="tooltip-row">
          <span class="tooltip-label">${label}:</span>
          <span class="tooltip-value">${formattedValue}</span>
        </div>
      `;
    });

    tooltipBody.innerHTML = content;
  }

  /**
   * Format detail label for display
   */
  formatDetailLabel(key) {
    const labels = {
      lastUpdate: '最後更新',
      duration: '持續時間',
      progress: '進度',
      remaining: '剩餘時間',
      attempts: '嘗試次數',
      errorCode: '錯誤代碼',
      strategyId: '策略ID',
      tradeCount: '交易次數',
      profit: '收益',
      performance: '表現'
    };

    return labels[key] || key;
  }

  /**
   * Format detail value for display
   */
  formatDetailValue(key, value) {
    // Handle different value types
    if (typeof value === 'number') {
      if (key.includes('Rate') || key.includes('ratio')) {
        return `${(value * 100).toFixed(2)}%`;
      } else if (key.includes('profit') || key.includes('return')) {
        return `${value.toFixed(2)}%`;
      } else if (key.includes('time') || key.includes('duration')) {
        return this.formatDuration(value);
      } else {
        return value.toLocaleString();
      }
    } else if (value instanceof Date) {
      return value.toLocaleString('zh-TW');
    } else if (typeof value === 'boolean') {
      return value ? '是' : '否';
    } else {
      return String(value);
    }
  }

  /**
   * Format duration in seconds to human readable format
   */
  formatDuration(seconds) {
    if (seconds < 60) {
      return `${seconds}秒`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      return `${minutes}分鐘`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}小時${minutes}分鐘`;
    }
  }

  /**
   * Handle status click
   */
  handleStatusClick() {
    // Emit click event
    this.container.dispatchEvent(new CustomEvent('status-click', {
      detail: {
        status: this.currentStatus,
        message: this.message,
        details: this.details
      }
    }));
  }

  /**
   * Emit status change event
   */
  emitStatusChange(oldStatus, newStatus, details) {
    this.container.dispatchEvent(new CustomEvent('status-change', {
      detail: {
        oldStatus,
        newStatus,
        message: this.message,
        details
      }
    }));
  }

  /**
   * Show loading state
   */
  setLoading(message = '正在載入...', details = {}) {
    this.setStatus('loading', message, details);
  }

  /**
   * Show success state
   */
  setSuccess(message = '操作成功', details = {}) {
    this.setStatus('success', message, details);
  }

  /**
   * Show error state
   */
  setError(message = '發生錯誤', details = {}) {
    this.setStatus('error', message, details);
  }

  /**
   * Show warning state
   */
  setWarning(message = '注意', details = {}) {
    this.setStatus('warning', message, details);
  }

  /**
   * Show active state
   */
  setActive(message = '運行中', details = {}) {
    this.setStatus('active', message, details);
  }

  /**
   * Show inactive state
   */
  setInactive(message = '已停止', details = {}) {
    this.setStatus('inactive', message, details);
  }

  /**
   * Destroy the component
   */
  destroy() {
    this.hideTooltip();

    // Remove event listeners
    const wrapper = this.container.querySelector('.status-indicator-wrapper');
    if (wrapper) {
      wrapper.removeEventListener('mouseenter', this.showTooltip);
      wrapper.removeEventListener('mouseleave', this.hideTooltip);
      wrapper.removeEventListener('focus', this.showTooltip);
      wrapper.removeEventListener('blur', this.hideTooltip);
      wrapper.removeEventListener('click', this.handleStatusClick);
    }

    // Clear content
    this.container.innerHTML = '';
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StatusIndicator;
}