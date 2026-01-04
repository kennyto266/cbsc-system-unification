/**
 * 个人策略管理Dashboard - 策略表单组件
 * Personal Strategy Management Dashboard - Strategy Form Component
 */

import { STRATEGY_TYPES, DEFAULT_VALUES, VALIDATION_RULES } from './constants.js';
import { validate, formatDate } from './utils.js';

/**
 * 策略表单组件类
 */
class StrategyForm {
    constructor(container, strategyManager, eventBus) {
        this.container = container;
        this.strategyManager = strategyManager;
        this.eventBus = eventBus;
        this.mode = 'add'; // 'add' or 'edit'
        this.strategy = null;
        this.formData = {};
        this.errors = {};

        this.init();
    }

    /**
     * 初始化组件
     */
    init() {
        this.bindEvents();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // Listen to form events
        this.eventBus.on('strategy:edit', (strategy) => {
            this.show('edit', strategy);
        });

        this.eventBus.on('strategy:add', () => {
            this.show('add');
        });
    }

    /**
     * 显示表单
     * @param {string} mode - 模式 ('add' 或 'edit')
     * @param {Object} strategy - 策略对象（编辑模式需要）
     */
    show(mode, strategy = null) {
        this.mode = mode;
        this.strategy = strategy;
        this.errors = {};

        // Reset form data
        this.formData = mode === 'edit' && strategy
            ? { ...strategy }
            : { ...DEFAULT_VALUES.STRATEGY };

        this.render();
        this.bindFormEvents();
    }

    /**
     * 隐藏表单
     */
    hide() {
        this.container.innerHTML = '';
        this.container.style.display = 'none';
        this.eventBus.emit('form:hidden');
    }

    /**
     * 渲染表单
     */
    render() {
        const title = this.mode === 'edit' ? '编辑策略' : '添加新策略';
        const submitText = this.mode === 'edit' ? '更新' : '创建';

        const html = `
            <div class="form-container">
                <div class="form-header">
                    <h2>${title}</h2>
                    <button class="btn-close" id="close-form" title="关闭">&times;</button>
                </div>

                <form id="strategy-form" class="strategy-form">
                    <div class="form-row">
                        <div class="form-group" style="flex: 2;">
                            <label for="strategy-name">
                                策略名称 <span class="required">*</span>
                            </label>
                            <input type="text"
                                   id="strategy-name"
                                   name="name"
                                   class="form-control ${this.errors.name ? 'is-invalid' : ''}"
                                   value="${this.escapeHtml(this.formData.name || '')}"
                                   placeholder="请输入策略名称"
                                   required>
                            ${this.errors.name ? `<div class="error-text">${this.errors.name}</div>` : ''}
                        </div>

                        <div class="form-group" style="flex: 1;">
                            <label for="strategy-type">
                                策略类型 <span class="required">*</span>
                            </label>
                            <select id="strategy-type"
                                    name="strategy_type"
                                    class="form-control ${this.errors.strategy_type ? 'is-invalid' : ''}"
                                    required>
                                ${Object.values(STRATEGY_TYPES).map(type => `
                                    <option value="${type.value}"
                                            ${this.formData.strategy_type === type.value ? 'selected' : ''}>
                                        ${type.label}
                                    </option>
                                `).join('')}
                            </select>
                            ${this.errors.strategy_type ? `<div class="error-text">${this.errors.strategy_type}</div>` : ''}
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="strategy-description">策略描述</label>
                        <textarea id="strategy-description"
                                  name="description"
                                  class="form-control ${this.errors.description ? 'is-invalid' : ''}"
                                  rows="3"
                                  placeholder="请输入策略描述（可选）">${this.escapeHtml(this.formData.description || '')}</textarea>
                        ${this.errors.description ? `<div class="error-text">${this.errors.description}</div>` : ''}
                        <div class="form-help">${(this.formData.description || '').length}/500 字符</div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="initial-capital">
                                初始资金 (¥) <span class="required">*</span>
                            </label>
                            <input type="number"
                                   id="initial-capital"
                                   name="initial_capital"
                                   class="form-control ${this.errors.initial_capital ? 'is-invalid' : ''}"
                                   value="${this.formData.initial_capital || DEFAULT_VALUES.STRATEGY.initial_capital}"
                                   min="10000"
                                   max="100000000"
                                   step="10000"
                                   required>
                            ${this.errors.initial_capital ? `<div class="error-text">${this.errors.initial_capital}</div>` : ''}
                            <div class="form-help">10,000 - 100,000,000</div>
                        </div>

                        <div class="form-group">
                            <label for="risk-limit">
                                风险限制 (%) <span class="required">*</span>
                            </label>
                            <input type="number"
                                   id="risk-limit"
                                   name="risk_limit"
                                   class="form-control ${this.errors.risk_limit ? 'is-invalid' : ''}"
                                   value="${(this.formData.risk_limit || DEFAULT_VALUES.STRATEGY.risk_limit) * 100}"
                                   min="1"
                                   max="100"
                                   step="1"
                                   required>
                            ${this.errors.risk_limit ? `<div class="error-text">${this.errors.risk_limit}</div>` : ''}
                            <div class="form-help">1% - 100%</div>
                        </div>
                    </div>

                    <div class="form-section">
                        <h3>高级设置</h3>
                        <div class="advanced-settings">
                            <div class="form-group">
                                <label for="max-positions">
                                    最大持仓数
                                </label>
                                <input type="number"
                                       id="max-positions"
                                       name="max_positions"
                                       class="form-control"
                                       value="${this.formData.max_positions || 10}"
                                       min="1"
                                       max="100"
                                       step="1">
                                <div class="form-help">同时持有的最大股票数量</div>
                            </div>

                            <div class="form-group">
                                <label for="stop-loss">
                                    止损比例 (%)
                                </label>
                                <input type="number"
                                       id="stop-loss"
                                       name="stop_loss"
                                       class="form-control"
                                       value="${(this.formData.stop_loss || 0.05) * 100}"
                                       min="0"
                                       max="50"
                                       step="0.1">
                                <div class="form-help">0% - 50%</div>
                            </div>

                            <div class="form-group">
                                <label for="take-profit">
                                    止盈比例 (%)
                                </label>
                                <input type="number"
                                       id="take-profit"
                                       name="take_profit"
                                       class="form-control"
                                       value="${(this.formData.take_profit || 0.10) * 100}"
                                       min="0"
                                       max="100"
                                       step="0.1">
                                <div class="form-help">0% - 100%</div>
                            </div>
                        </div>
                    </div>

                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" id="cancel-form">
                            取消
                        </button>
                        <button type="submit" class="btn btn-primary" id="submit-form">
                            <span class="btn-text">${submitText}策略</span>
                            <span class="btn-spinner" style="display: none;"></span>
                        </button>
                    </div>
                </form>
            </div>
        `;

        this.container.innerHTML = html;
        this.container.style.display = 'block';

        // Update textarea character count
        this.updateCharCount();
    }

    /**
     * 绑定表单事件
     */
    bindFormEvents() {
        const form = document.getElementById('strategy-form');
        const closeBtn = document.getElementById('close-form');
        const cancelBtn = document.getElementById('cancel-form');

        // Form submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleSubmit();
        });

        // Close button
        closeBtn.addEventListener('click', () => {
            this.hide();
        });

        // Cancel button
        cancelBtn.addEventListener('click', () => {
            this.hide();
        });

        // Character count for description
        const descriptionTextarea = document.getElementById('strategy-description');
        if (descriptionTextarea) {
            descriptionTextarea.addEventListener('input', () => {
                this.updateCharCount();
            });
        }

        // Risk limit input change (convert to decimal)
        const riskLimitInput = document.getElementById('risk-limit');
        if (riskLimitInput) {
            riskLimitInput.addEventListener('change', () => {
                // Convert percentage to decimal for internal storage
                const value = parseFloat(riskLimitInput.value);
                if (!isNaN(value)) {
                    this.formData.risk_limit = value / 100;
                }
            });
        }

        // Stop loss input change
        const stopLossInput = document.getElementById('stop-loss');
        if (stopLossInput) {
            stopLossInput.addEventListener('change', () => {
                const value = parseFloat(stopLossInput.value);
                if (!isNaN(value)) {
                    this.formData.stop_loss = value / 100;
                }
            });
        }

        // Take profit input change
        const takeProfitInput = document.getElementById('take-profit');
        if (takeProfitInput) {
            takeProfitInput.addEventListener('change', () => {
                const value = parseFloat(takeProfitInput.value);
                if (!isNaN(value)) {
                    this.formData.take_profit = value / 100;
                }
            });
        }
    }

    /**
     * 更新字符计数
     */
    updateCharCount() {
        const textarea = document.getElementById('strategy-description');
        const helpText = textarea?.nextElementSibling;
        if (textarea && helpText && helpText.classList.contains('form-help')) {
            const length = textarea.value.length;
            helpText.textContent = `${length}/500 字符`;
            helpText.style.color = length > 500 ? '#ef4444' : '#718096';
        }
    }

    /**
     * 处理表单提交
     */
    async handleSubmit() {
        // Clear previous errors
        this.errors = {};
        this.clearErrors();

        // Collect form data
        const formData = new FormData(document.getElementById('strategy-form'));
        const data = Object.fromEntries(formData.entries());

        // Convert percentage fields to decimal
        data.risk_limit = parseFloat(data.risk_limit) / 100;
        data.stop_loss = parseFloat(data.stop_loss) / 100;
        data.take_profit = parseFloat(data.take_profit) / 100;

        // Validate form
        const validation = this.validateForm(data);
        if (!validation.valid) {
            this.errors = validation.errors;
            this.showErrors();
            return;
        }

        // Show loading state
        this.setLoading(true);

        try {
            if (this.mode === 'edit' && this.strategy) {
                await this.strategyManager.updateStrategy(this.strategy.id, data);
                this.showNotification('策略更新成功', 'success');
            } else {
                await this.strategyManager.addStrategy(data);
                this.showNotification('策略创建成功', 'success');
            }

            this.hide();

        } catch (error) {
            this.showNotification(error.message, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 验证表单
     * @param {Object} data - 表单数据
     * @returns {Object} 验证结果
     */
    validateForm(data) {
        const rules = {
            name: VALIDATION_RULES.STRATEGY_NAME,
            strategy_type: {
                required: true,
                message: '请选择策略类型'
            },
            description: {
                maxLength: 500,
                message: '策略描述不能超过500个字符'
            },
            initial_capital: {
                required: true,
                type: 'number',
                min: 10000,
                max: 100000000,
                message: '初始资金必须在10,000-100,000,000之间'
            },
            risk_limit: {
                required: true,
                type: 'number',
                min: 0.01,
                max: 1.0,
                message: '风险限制必须在1%-100%之间'
            }
        };

        return validate(data, rules);
    }

    /**
     * 显示错误
     */
    showErrors() {
        Object.keys(this.errors).forEach(field => {
            const input = document.getElementById(field);
            const errorDiv = input?.parentElement?.querySelector('.error-text');

            if (input) {
                input.classList.add('is-invalid');
            }

            if (errorDiv) {
                errorDiv.textContent = this.errors[field];
            }
        });
    }

    /**
     * 清除错误
     */
    clearErrors() {
        const inputs = document.querySelectorAll('.is-invalid');
        const errors = document.querySelectorAll('.error-text');

        inputs.forEach(input => {
            input.classList.remove('is-invalid');
        });

        errors.forEach(error => {
            error.textContent = '';
        });
    }

    /**
     * 设置加载状态
     * @param {boolean} loading - 是否加载中
     */
    setLoading(loading) {
        const submitBtn = document.getElementById('submit-form');
        const btnText = submitBtn?.querySelector('.btn-text');
        const btnSpinner = submitBtn?.querySelector('.btn-spinner');

        if (submitBtn) {
            submitBtn.disabled = loading;
        }

        if (btnText) {
            btnText.style.display = loading ? 'none' : 'inline';
        }

        if (btnSpinner) {
            btnSpinner.style.display = loading ? 'inline-block' : 'none';
        }
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
     * 转义HTML
     * @param {string} str - 字符串
     * @returns {string} 转义后的字符串
     */
    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    /**
     * 重置表单
     */
    reset() {
        this.formData = { ...DEFAULT_VALUES.STRATEGY };
        this.errors = {};
        this.render();
    }

    /**
     * 获取表单数据
     * @returns {Object} 表单数据
     */
    getData() {
        return { ...this.formData };
    }

    /**
     * 设置表单数据
     * @param {Object} data - 表单数据
     */
    setData(data) {
        this.formData = { ...this.formData, ...data };
    }
}

export default StrategyForm;