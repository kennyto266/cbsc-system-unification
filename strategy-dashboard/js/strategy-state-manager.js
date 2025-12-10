/**
 * 策略狀態管理器 - 專業級策略啟用/禁用切換功能
 * 提供確認對話框、批量操作、狀態持久化等高級功能
 */

// ========== 策略狀態管理器 ==========
class StrategyStateManager {
    constructor(dashboardManager) {
        this.dashboard = dashboardManager;
        this.storageKey = 'cbsc_strategy_states';
        this.operationQueue = [];
        this.isProcessing = false;

        // 策略狀態緩存
        this.strategyStates = this.loadStrategyStates();

        // UI組件緩存
        this.modalElement = null;
        this.batchModalElement = null;

        // 綁定上下文
        this.handleConfirm = this.handleConfirm.bind(this);
        this.handleBatchConfirm = this.handleBatchConfirm.bind(this);

        console.log('⚙️ 策略狀態管理器已初始化');
    }

    /**
     * 增強的策略切換操作（帶確認對話框）
     */
    async toggleStrategyWithConfirm(strategyName, currentStatus, strategyElement = null) {
        const action = currentStatus === 'active' ? '停止' : '啟動';
        const actionType = currentStatus === 'active' ? 'stop' : 'start';

        // 顯示確認對話框
        this.showConfirmDialog({
            title: `${action}策略確認`,
            strategyName: strategyName,
            action: action,
            actionType: actionType,
            currentStatus: currentStatus,
            onConfirm: () => this.executeStrategyToggle(strategyName, currentStatus, strategyElement),
            onCancel: () => this.showMessage('操作已取消', 'info')
        });
    }

    /**
     * 執行策略切換操作
     */
    async executeStrategyToggle(strategyName, currentStatus, strategyElement = null) {
        const newStatus = currentStatus === 'active' ? 'stopped' : 'active';
        const action = newStatus === 'active' ? '啟動' : '停止';

        try {
            // 顯示操作進度
            this.dashboard.showLoading(`${action}策略 ${strategyName} 中...`);

            // 更新本地狀態（樂觀更新）
            this.updateLocalStrategyState(strategyName, newStatus);

            // 更新UI狀態
            if (strategyElement) {
                this.updateStrategyUIState(strategyElement, newStatus);
            }

            // 調用API（如果可用）
            if (window.strategyAPI && window.strategyAPI.updateStrategyStatus) {
                await window.strategyAPI.updateStrategyStatus(strategyName, newStatus);
            } else {
                // 模擬API調用延遲
                await this.simulateAPICall();
            }

            // 保存狀態到本地存儲
            this.saveStrategyStates();

            // 顯示成功消息
            this.dashboard.showMessage(`策略 ${strategyName} 已成功${action}`, 'success');

            // 如果有WebSocket，通知服務器
            if (this.dashboard.websocketClient && this.dashboard.websocketClient.isConnected) {
                this.notifyServerStrategyChange(strategyName, newStatus);
            }

            // 更新統計信息
            this.updateStrategyStatistics();

        } catch (error) {
            console.error(`策略${action}失敗:`, error);

            // 回滾本地狀態
            this.updateLocalStrategyState(strategyName, currentStatus);
            if (strategyElement) {
                this.updateStrategyUIState(strategyElement, currentStatus);
            }

            this.dashboard.showMessage(`策略${action}失敗: ${error.message}`, 'error');
        } finally {
            this.dashboard.hideLoading();
        }
    }

    /**
     * 顯示確認對話框
     */
    showConfirmDialog(options) {
        const {
            title,
            strategyName,
            action,
            actionType,
            currentStatus,
            onConfirm,
            onCancel
        } = options;

        // 創建模態框HTML
        const modalHTML = `
            <div class="strategy-confirm-modal" id="strategyConfirmModal">
                <div class="modal-backdrop"></div>
                <div class="modal-container">
                    <div class="modal-header">
                        <h3 class="modal-title">${title}</h3>
                        <button class="modal-close" id="modalClose">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="strategy-info">
                            <h4 class="strategy-name">${strategyName}</h4>
                            <div class="status-change">
                                <span class="current-status status-${currentStatus}">
                                    ${currentStatus === 'active' ? '運行中' : '已停止'}
                                </span>
                                <span class="arrow">→</span>
                                <span class="new-status status-${actionType === 'start' ? 'active' : 'stopped'}">
                                    ${action}
                                </span>
                            </div>
                        </div>
                        <div class="warning-message">
                            <div class="warning-icon">⚠️</div>
                            <div class="warning-text">
                                ${actionType === 'stop' ?
                                    '停止策略將不再生成新的交易信號，現有持倉將保持不變。' :
                                    '啟動策略將開始監控市場並生成交易信號。'
                                }
                            </div>
                        </div>
                        <div class="impact-list">
                            <h5>操作影響：</h5>
                            <ul>
                                ${actionType === 'stop' ?
                                    '<li>停止生成新的交易信號</li><li>保留歷史數據和統計信息</li><li>可隨時重新啟動</li>' :
                                    '<li>開始實時市場監控</li><li>根據策略邏輯生成信號</li><li>消耗計算資源</li>'
                                }
                            </ul>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="modalCancel">取消</button>
                        <button class="btn btn-${actionType === 'stop' ? 'danger' : 'success'}" id="modalConfirm">
                            確認${action}
                        </button>
                    </div>
                </div>
            </div>
        `;

        // 添加到DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.modalElement = document.getElementById('strategyConfirmModal');

        // 綁定事件
        const confirmBtn = document.getElementById('modalConfirm');
        const cancelBtn = document.getElementById('modalCancel');
        const closeBtn = document.getElementById('modalClose');
        const backdrop = this.modalElement.querySelector('.modal-backdrop');

        confirmBtn.addEventListener('click', () => {
            this.closeConfirmDialog();
            onConfirm();
        });

        cancelBtn.addEventListener('click', () => {
            this.closeConfirmDialog();
            onCancel();
        });

        closeBtn.addEventListener('click', () => {
            this.closeConfirmDialog();
            onCancel();
        });

        backdrop.addEventListener('click', () => {
            this.closeConfirmDialog();
            onCancel();
        });

        // 防止ESC鍵關閉（要求明確認選）
        document.addEventListener('keydown', this.handleEscapeKey, { once: true });

        // 顯示模態框（添加動畫）
        setTimeout(() => {
            this.modalElement.classList.add('show');
        }, 10);
    }

    /**
     * 關閉確認對話框
     */
    closeConfirmDialog() {
        if (this.modalElement) {
            this.modalElement.classList.remove('show');
            setTimeout(() => {
                this.modalElement.remove();
                this.modalElement = null;
            }, 300);
        }
        document.removeEventListener('keydown', this.handleEscapeKey);
    }

    /**
     * 處理ESC鍵（阻止默認行為）
     */
    handleEscapeKey(event) {
        if (event.key === 'Escape') {
            event.preventDefault();
            event.stopPropagation();
        }
    }

    /**
     * 批量操作策略
     */
    async batchToggleStrategies(strategyNames, targetStatus) {
        const action = targetStatus === 'active' ? '啟動' : '停止';
        const actionType = targetStatus === 'active' ? 'start' : 'stop';

        // 顯示批量確認對話框
        this.showBatchConfirmDialog({
            title: `批量${action}策略`,
            strategyNames: strategyNames,
            action: action,
            targetStatus: targetStatus,
            actionType: actionType,
            onConfirm: () => this.executeBatchToggle(strategyNames, targetStatus),
            onCancel: () => this.showMessage('批量操作已取消', 'info')
        });
    }

    /**
     * 顯示批量確認對話框
     */
    showBatchConfirmDialog(options) {
        const {
            title,
            strategyNames,
            action,
            targetStatus,
            actionType,
            onConfirm,
            onCancel
        } = options;

        const strategyListHTML = strategyNames.map(name =>
            `<li class="batch-strategy-item">
                <span class="strategy-name">${name}</span>
                <span class="action-badge badge-${actionType}">${action}</span>
            </li>`
        ).join('');

        const modalHTML = `
            <div class="strategy-confirm-modal batch-modal" id="batchConfirmModal">
                <div class="modal-backdrop"></div>
                <div class="modal-container">
                    <div class="modal-header">
                        <h3 class="modal-title">${title}</h3>
                        <button class="modal-close" id="batchModalClose">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="batch-summary">
                            <div class="summary-icon">📊</div>
                            <div class="summary-text">
                                將要<span class="action-text">${action}</span>
                                <span class="strategy-count">${strategyNames.length}</span>個策略
                            </div>
                        </div>
                        <div class="strategy-list">
                            <h5>策略列表：</h5>
                            <ul>${strategyListHTML}</ul>
                        </div>
                        <div class="warning-message">
                            <div class="warning-icon">⚠️</div>
                            <div class="warning-text">
                                批量操作將影響所有選中的策略，請確認操作正確。
                                操作完成後將刷新所有相關數據。
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" id="batchModalCancel">取消</button>
                        <button class="btn btn-${actionType === 'stop' ? 'danger' : 'success'}" id="batchModalConfirm">
                            確認批量${action}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.batchModalElement = document.getElementById('batchConfirmModal');

        // 綁定事件
        const confirmBtn = document.getElementById('batchModalConfirm');
        const cancelBtn = document.getElementById('batchModalCancel');
        const closeBtn = document.getElementById('batchModalClose');
        const backdrop = this.batchModalElement.querySelector('.modal-backdrop');

        confirmBtn.addEventListener('click', () => {
            this.closeBatchConfirmDialog();
            onConfirm();
        });

        cancelBtn.addEventListener('click', () => {
            this.closeBatchConfirmDialog();
            onCancel();
        });

        closeBtn.addEventListener('click', () => {
            this.closeBatchConfirmDialog();
            onCancel();
        });

        backdrop.addEventListener('click', () => {
            this.closeBatchConfirmDialog();
            onCancel();
        });

        setTimeout(() => {
            this.batchModalElement.classList.add('show');
        }, 10);
    }

    /**
     * 關閉批量確認對話框
     */
    closeBatchConfirmDialog() {
        if (this.batchModalElement) {
            this.batchModalElement.classList.remove('show');
            setTimeout(() => {
                this.batchModalElement.remove();
                this.batchModalElement = null;
            }, 300);
        }
    }

    /**
     * 執行批量切換
     */
    async executeBatchToggle(strategyNames, targetStatus) {
        const action = targetStatus === 'active' ? '啟動' : '停止';
        let successCount = 0;
        let errorCount = 0;

        this.dashboard.showLoading(`正在批量${action}策略...`);

        try {
            for (const strategyName of strategyNames) {
                try {
                    const currentStatus = this.getStrategyState(strategyName);
                    if (currentStatus !== targetStatus) {
                        await this.executeStrategyToggle(strategyName, currentStatus);
                        successCount++;
                    }
                } catch (error) {
                    console.error(`策略 ${strategyName} ${action}失敗:`, error);
                    errorCount++;
                }
            }

            // 顯示批量操作結果
            const message = errorCount === 0 ?
                `批量${action}完成！成功${action} ${successCount} 個策略` :
                `批量${action}完成！成功 ${successCount} 個，失敗 ${errorCount} 個`;

            this.dashboard.showMessage(message, errorCount === 0 ? 'success' : 'warning');

        } catch (error) {
            this.dashboard.showMessage(`批量${action}失敗: ${error.message}`, 'error');
        } finally {
            this.dashboard.hideLoading();
        }
    }

    /**
     * 更新策略UI狀態
     */
    updateStrategyUIState(strategyElement, newStatus) {
        if (!strategyElement) return;

        // 更新CSS類
        strategyElement.classList.remove('active', 'stopped');
        strategyElement.classList.add(newStatus);

        // 更新狀態指示器
        const statusIndicator = strategyElement.querySelector('.status-indicator');
        const statusText = strategyElement.querySelector('.status-text');
        const toggleBtn = strategyElement.querySelector('[title*="啟動"], [title*="暫停"], [title*="停止"]');

        if (statusIndicator) {
            statusIndicator.classList.remove('active', 'stopped');
            statusIndicator.classList.add(newStatus);
        }

        if (statusText) {
            statusText.textContent = newStatus === 'active' ? '運行中' : '已停止';
        }

        // 更新切換按鈕
        if (toggleBtn) {
            const isToggleBtn = toggleBtn.getAttribute('title')?.includes('啟動') ||
                              toggleBtn.getAttribute('title')?.includes('暫停') ||
                              toggleBtn.getAttribute('title')?.includes('停止');

            if (isToggleBtn) {
                toggleBtn.setAttribute('title', newStatus === 'active' ? '暫停' : '啟動');
                toggleBtn.textContent = newStatus === 'active' ? '⏸️' : '▶️';
            }
        }

        // 添加動畫效果
        strategyElement.style.transition = 'all 0.3s ease';
        strategyElement.style.transform = 'scale(1.02)';
        setTimeout(() => {
            strategyElement.style.transform = 'scale(1)';
        }, 200);
    }

    /**
     * 更新本地策略狀態
     */
    updateLocalStrategyState(strategyName, status) {
        this.strategyStates[strategyName] = status;
    }

    /**
     * 獲取策略狀態
     */
    getStrategyState(strategyName) {
        return this.strategyStates[strategyName] || 'active'; // 默認為活躍
    }

    /**
     * 保存策略狀態到本地存儲
     */
    saveStrategyStates() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.strategyStates));
        } catch (error) {
            console.warn('保存策略狀態失敗:', error);
        }
    }

    /**
     * 從本地存儲加載策略狀態
     */
    loadStrategyStates() {
        try {
            const saved = localStorage.getItem(this.storageKey);
            return saved ? JSON.parse(saved) : {};
        } catch (error) {
            console.warn('加載策略狀態失敗:', error);
            return {};
        }
    }

    /**
     * 模擬API調用延遲
     */
    simulateAPICall() {
        return new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 700));
    }

    /**
     * 通知服務器策略變更
     */
    notifyServerStrategyChange(strategyName, status) {
        if (this.dashboard.websocketClient) {
            const message = {
                type: 'strategy_status_change',
                data: {
                    strategy_name: strategyName,
                    new_status: status,
                    timestamp: new Date().toISOString()
                }
            };
            this.dashboard.websocketClient.send(message);
        }
    }

    /**
     * 更新策略統計信息
     */
    updateStrategyStatistics() {
        const stats = {
            total: Object.keys(this.strategyStates).length,
            active: Object.values(this.strategyStates).filter(s => s === 'active').length,
            stopped: Object.values(this.strategyStates).filter(s => s === 'stopped').length
        };

        // 更新UI統計數據
        const activeStrategiesElement = document.querySelector('.perf-card.primary .metric-value');
        if (activeStrategiesElement) {
            activeStrategiesElement.textContent = stats.active;
        }

        // 觸發統計更新事件
        this.dashboard.showMessage(
            `當前活躍策略: ${stats.active}/${stats.total}`,
            'info'
        );
    }

    /**
     * 獲取所有選中的策略
     */
    getSelectedStrategies() {
        const checkboxes = document.querySelectorAll('.strategy-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.dataset.strategyName);
    }

    /**
     * 顯示消息（委托給dashboard）
     */
    showMessage(message, type = 'info') {
        if (this.dashboard && this.dashboard.showMessage) {
            this.dashboard.showMessage(message, type);
        }
    }

    /**
     * 獲取策略狀態報告
     */
    getStrategyStateReport() {
        const total = Object.keys(this.strategyStates).length;
        const active = Object.values(this.strategyStates).filter(s => s === 'active').length;
        const stopped = total - active;

        return {
            total,
            active,
            stopped,
            active_rate: total > 0 ? (active / total * 100).toFixed(1) : 0,
            strategies: this.strategyStates
        };
    }

    /**
     * 重置所有策略狀態
     */
    resetAllStrategyStates() {
        this.strategyStates = {};
        this.saveStrategyStates();
        this.updateStrategyStatistics();
    }
}

// ========== 導出 ==========
window.StrategyStateManager = StrategyStateManager;

console.log('🎛️ 策略狀態管理器模組已載入');