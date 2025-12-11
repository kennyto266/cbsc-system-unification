/**
 * Strategy Toggle Component
 * Interactive toggle switch for enabling/disabling strategies
 */
class StrategyToggle {
  constructor(containerElement, strategyName, options = {}) {
    this.container = containerElement;
    this.strategyName = strategyName;
    this.options = {
      size: options.size || 'medium', // small, medium, large
      showLabel: options.showLabel !== false,
      showIcon: options.showIcon !== false,
      animated: options.animated !== false,
      confirmDisable: options.confirmDisable !== false,
      confirmMessage: options.confirmMessage || `確定要停用策略 "${strategyName}" 嗎？`,
      onToggle: options.onToggle || null,
      ...options
    };

    this.currentState = false;
    this.isLoading = false;
    this.isDisabled = false;
    this.toggleCallbacks = [];

    this.init();
  }

  /**
   * Initialize the toggle component
   */
  init() {
    this.createToggle();
    this.bindEvents();
  }

  /**
   * Create the toggle switch element
   */
  createToggle() {
    this.container.innerHTML = `
      <div class="strategy-toggle-wrapper ${this.options.size}" data-strategy="${this.strategyName}">
        ${this.options.showIcon ? `
          <div class="toggle-icon">
            <span class="icon-state off">⏸️</span>
            <span class="icon-state on">▶️</span>
            <span class="icon-state loading">⏳</span>
          </div>
        ` : ''}

        <div class="toggle-switch" role="switch" tabindex="0" aria-checked="${this.currentState}">
          <div class="toggle-track">
            <div class="toggle-thumb"></div>
          </div>
          ${this.options.animated ? '<div class="toggle-ripple"></div>' : ''}
        </div>

        ${this.options.showLabel ? `
          <div class="toggle-labels">
            <span class="label-off">停用</span>
            <span class="label-on">啟用</span>
          </div>
        ` : ''}

        <div class="toggle-status">
          <span class="status-text">${this.getStatusText()}</span>
        </div>
      </div>
    `;

    this.toggleElement = this.container.querySelector('.toggle-switch');
    this.thumbElement = this.container.querySelector('.toggle-thumb');
    this.statusText = this.container.querySelector('.status-text');
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Click handler
    this.toggleElement.addEventListener('click', (e) => {
      e.preventDefault();
      if (!this.isLoading && !this.isDisabled) {
        this.handleToggle();
      }
    });

    // Keyboard handlers (accessibility)
    this.toggleElement.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (!this.isLoading && !this.isDisabled) {
          this.handleToggle();
        }
      }
    });

    // Touch handlers for mobile
    this.toggleElement.addEventListener('touchstart', (e) => {
      if (!this.isLoading && !this.isDisabled) {
        e.preventDefault();
        this.addRippleEffect(e.touches[0]);
      }
    });

    this.toggleElement.addEventListener('touchend', (e) => {
      e.preventDefault();
      if (!this.isLoading && !this.isDisabled) {
        this.handleToggle();
      }
    });
  }

  /**
   * Handle toggle action
   */
  async handleToggle() {
    // Check for confirmation when disabling
    if (this.currentState && this.options.confirmDisable) {
      const confirmed = await this.showConfirmation();
      if (!confirmed) return;
    }

    // Execute toggle
    await this.toggle();
  }

  /**
   * Show confirmation dialog
   */
  showConfirmation() {
    return new Promise((resolve) => {
      // Create modal
      const modal = document.createElement('div');
      modal.className = 'confirmation-modal';
      modal.innerHTML = `
        <div class="modal-backdrop"></div>
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h3 class="modal-title">確認操作</h3>
            </div>
            <div class="modal-body">
              <p>${this.options.confirmMessage}</p>
              <div class="confirmation-impact">
                <h4>停用影響：</h4>
                <ul>
                  <li>策略將停止執行新交易</li>
                  <li>現有持倉將保持不變</li>
                  <li>監控和警報將繼續運作</li>
                </ul>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary" data-action="cancel">取消</button>
              <button class="btn btn-danger" data-action="confirm">確認停用</button>
            </div>
          </div>
        </div>
      `;

      // Add to DOM
      document.body.appendChild(modal);

      // Focus on confirm button for accessibility
      const confirmBtn = modal.querySelector('[data-action="confirm"]');
      confirmBtn.focus();

      // Handle button clicks
      modal.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const action = e.currentTarget.dataset.action;
          document.body.removeChild(modal);
          resolve(action === 'confirm');
        });
      });

      // Handle escape key
      const handleEscape = (e) => {
        if (e.key === 'Escape') {
          document.body.removeChild(modal);
          document.removeEventListener('keydown', handleEscape);
          resolve(false);
        }
      };
      document.addEventListener('keydown', handleEscape);
    });
  }

  /**
   * Toggle the switch state
   */
  async toggle() {
    if (this.isLoading) return;

    const newState = !this.currentState;

    try {
      // Set loading state
      this.setLoading(true);

      // Call toggle callback if provided
      if (this.options.onToggle) {
        const result = await this.options.onToggle(newState);
        if (result === false) {
          // Toggle was cancelled by callback
          this.setLoading(false);
          return;
        }
      }

      // Update state
      this.setState(newState);

      // Emit toggle event
      this.emitToggleEvent(newState);

    } catch (error) {
      console.error('Toggle failed:', error);
      // Revert state if toggle failed
      this.setLoading(false);
      this.emitErrorEvent(error);
    }
  }

  /**
   * Set the toggle state
   */
  setState(enabled, animate = true) {
    this.currentState = enabled;
    this.isLoading = false;

    // Update DOM
    this.updateVisualState(animate);

    // Update ARIA attribute
    this.toggleElement.setAttribute('aria-checked', enabled);

    // Update status text
    if (this.statusText) {
      this.statusText.textContent = this.getStatusText();
    }
  }

  /**
   * Update visual state with optional animation
   */
  updateVisualState(animate = true) {
    if (animate && this.options.animated) {
      this.animateToggleChange();
    } else {
      this.applyStateClasses();
    }
  }

  /**
   * Apply state classes to elements
   */
  applyStateClasses() {
    const wrapper = this.container.querySelector('.strategy-toggle-wrapper');

    // Remove all state classes
    wrapper.classList.remove('loading', 'disabled', 'active');
    this.toggleElement.classList.remove('loading', 'disabled', 'active');

    if (this.isLoading) {
      wrapper.classList.add('loading');
      this.toggleElement.classList.add('loading');
    } else if (this.isDisabled) {
      wrapper.classList.add('disabled');
      this.toggleElement.classList.add('disabled');
    } else if (this.currentState) {
      wrapper.classList.add('active');
      this.toggleElement.classList.add('active');
    }
  }

  /**
   * Animate the toggle change
   */
  animateToggleChange() {
    // Add transition class
    this.toggleElement.classList.add('transitioning');

    // Apply state classes
    this.applyStateClasses();

    // Remove transition class after animation completes
    setTimeout(() => {
      this.toggleElement.classList.remove('transitioning');
    }, 300);
  }

  /**
   * Set loading state
   */
  setLoading(isLoading) {
    this.isLoading = isLoading;
    this.applyStateClasses();

    if (this.statusText) {
      this.statusText.textContent = isLoading ? '處理中...' : this.getStatusText();
    }
  }

  /**
   * Set disabled state
   */
  setDisabled(disabled) {
    this.isDisabled = disabled;
    this.applyStateClasses();

    this.toggleElement.setAttribute('aria-disabled', disabled);
    this.toggleElement.setAttribute('tabindex', disabled ? '-1' : '0');
  }

  /**
   * Get status text based on current state
   */
  getStatusText() {
    if (this.isLoading) return '處理中...';
    if (this.isDisabled) return '不可用';
    return this.currentState ? '已啟用' : '已停用';
  }

  /**
   * Add ripple effect for touch interaction
   */
  addRippleEffect(touch) {
    if (!this.options.animated) return;

    const ripple = this.container.querySelector('.toggle-ripple');
    if (!ripple) return;

    const rect = this.toggleElement.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = touch.clientX - rect.left - size / 2;
    const y = touch.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.classList.add('active');

    setTimeout(() => {
      ripple.classList.remove('active');
    }, 600);
  }

  /**
   * Register toggle callback
   */
  onToggle(callback) {
    if (typeof callback === 'function') {
      this.toggleCallbacks.push(callback);
    }
  }

  /**
   * Remove toggle callback
   */
  offToggle(callback) {
    const index = this.toggleCallbacks.indexOf(callback);
    if (index > -1) {
      this.toggleCallbacks.splice(index, 1);
    }
  }

  /**
   * Emit toggle event
   */
  emitToggleEvent(newState) {
    const event = new CustomEvent('strategy-toggle', {
      detail: {
        strategyName: this.strategyName,
        oldState: !newState,
        newState: newState,
        timestamp: new Date().toISOString()
      }
    });

    this.container.dispatchEvent(event);

    // Call registered callbacks
    this.toggleCallbacks.forEach(callback => {
      try {
        callback(this.strategyName, newState);
      } catch (error) {
        console.error('Toggle callback error:', error);
      }
    });
  }

  /**
   * Emit error event
   */
  emitErrorEvent(error) {
    const event = new CustomEvent('strategy-toggle-error', {
      detail: {
        strategyName: this.strategyName,
        error: error.message,
        timestamp: new Date().toISOString()
      }
    });

    this.container.dispatchEvent(event);
  }

  /**
   * Get current state
   */
  getState() {
    return {
      enabled: this.currentState,
      loading: this.isLoading,
      disabled: this.isDisabled
    };
  }

  /**
   * Destroy the component
   */
  destroy() {
    // Remove event listeners
    this.toggleElement.removeEventListener('click', this.handleToggle);
    this.toggleElement.removeEventListener('keydown', this.handleToggle);
    this.toggleElement.removeEventListener('touchstart', this.addRippleEffect);
    this.toggleElement.removeEventListener('touchend', this.handleToggle);

    // Clear callbacks
    this.toggleCallbacks = [];

    // Clear DOM
    this.container.innerHTML = '';
  }
}

// Static factory method for creating multiple toggles
StrategyToggle.createToggles = function(container, strategies, options = {}) {
  const toggles = {};

  strategies.forEach(strategy => {
    const wrapper = document.createElement('div');
    wrapper.className = 'strategy-toggle-item';
    wrapper.innerHTML = `
      <div class="toggle-info">
        <h4 class="strategy-name">${strategy.name}</h4>
        <p class="strategy-description">${strategy.description || ''}</p>
      </div>
      <div class="toggle-container"></div>
    `;

    container.appendChild(wrapper);

    const toggleContainer = wrapper.querySelector('.toggle-container');
    const toggle = new StrategyToggle(toggleContainer, strategy.name, {
      ...options,
      onToggle: async (enabled) => {
        // Call global callback if provided
        if (options.onToggle) {
          return await options.onToggle(strategy.name, enabled);
        }
        return true;
      }
    });

    // Set initial state
    if (strategy.isActive !== undefined) {
      toggle.setState(strategy.isActive, false);
    }

    toggles[strategy.name] = toggle;
  });

  return toggles;
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StrategyToggle;
}