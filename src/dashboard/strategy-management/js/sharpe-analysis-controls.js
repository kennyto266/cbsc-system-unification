/**
 * 个人策略管理Dashboard - Sharpe比率分析控制面板
 * Personal Strategy Management Dashboard - Sharpe Ratio Analysis Control Panel
 */

import { BENCHMARK_TYPES, SHARPE_CONFIG, PERFORMANCE_METRICS } from './constants.js';

/**
 * Sharpe分析控制面板类
 */
class SharpeAnalysisControls {
    constructor(containerId, chartInstance) {
        this.container = document.getElementById(containerId);
        this.chart = chartInstance;
        this.isVisible = true;
        this.selectedBenchmarks = ['HSI'];
        this.analysisOptions = {
            riskFreeRate: SHARPE_CONFIG.DEFAULT_RISK_FREE_RATE,
            windowSize: SHARPE_CONFIG.DEFAULT_WINDOW,
            bootstrapSamples: SHARPE_CONFIG.BOOTSTRAP_SAMPLES,
            confidenceLevel: 0.95
        };

        this.init();
    }

    /**
     * 初始化控制面板
     */
    init() {
        this.createControlPanel();
        this.bindEvents();
        this.setupChartListeners();
    }

    /**
     * 创建控制面板UI
     */
    createControlPanel() {
        this.container.innerHTML = `
            <div class="sharpe-analysis-controls bg-white rounded-lg shadow-lg p-6 mb-6">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-lg font-semibold text-gray-800">Sharpe比率分析控制</h3>
                    <div class="flex space-x-2">
                        <button id="toggle-controls" class="text-gray-500 hover:text-gray-700">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                            </svg>
                        </button>
                    </div>
                </div>

                <div id="controls-content" class="space-y-6">
                    <!-- Benchmark Selection -->
                    <div class="control-section">
                        <label class="block text-sm font-medium text-gray-700 mb-2">基准选择</label>
                        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                            ${this.renderBenchmarkOptions()}
                        </div>
                    </div>

                    <!-- Analysis Parameters -->
                    <div class="control-section">
                        <label class="block text-sm font-medium text-gray-700 mb-2">分析参数</label>
                        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <div>
                                <label class="block text-xs text-gray-600 mb-1">无风险利率 (%)</label>
                                <input type="number" id="risk-free-rate"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    value="${this.analysisOptions.riskFreeRate * 100}"
                                    step="0.1" min="0" max="20">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-600 mb-1">滚动窗口 (天)</label>
                                <select id="rolling-window"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                    ${SHARPE_CONFIG.ROLLING_WINDOWS.map(days =>
                                        `<option value="${days}" ${days === this.analysisOptions.windowSize ? 'selected' : ''}>
                                            ${days >= 252 ? `${days/252}年` : `${Math.round(days/21)}个月`}
                                        </option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs text-gray-600 mb-1">Bootstrap样本数</label>
                                <input type="number" id="bootstrap-samples"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    value="${this.analysisOptions.bootstrapSamples}"
                                    step="100" min="100" max="10000">
                            </div>
                            <div>
                                <label class="block text-xs text-gray-600 mb-1">置信水平</label>
                                <select id="confidence-level"
                                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                                    <option value="0.90" ${this.analysisOptions.confidenceLevel === 0.90 ? 'selected' : ''}>90%</option>
                                    <option value="0.95" ${this.analysisOptions.confidenceLevel === 0.95 ? 'selected' : ''}>95%</option>
                                    <option value="0.99" ${this.analysisOptions.confidenceLevel === 0.99 ? 'selected' : ''}>99%</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="control-section">
                        <div class="flex flex-wrap gap-3">
                            <button id="run-analysis" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                                运行分析
                            </button>
                            <button id="refresh-analysis" class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
                                刷新数据
                            </button>
                            <button id="export-csv" class="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors">
                                导出CSV
                            </button>
                            <button id="export-json" class="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors">
                                导出JSON
                            </button>
                            <button id="clear-analysis" class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors">
                                清除分析
                            </button>
                        </div>
                    </div>

                    <!-- Loading Indicator -->
                    <div id="analysis-loading" class="hidden bg-blue-50 border border-blue-200 rounded-md p-4">
                        <div class="flex items-center">
                            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                            <span class="text-blue-700">正在运行Sharpe比率分析...</span>
                        </div>
                    </div>

                    <!-- Summary Statistics -->
                    <div id="analysis-summary" class="bg-gray-50 rounded-md p-4 hidden">
                        <h4 class="text-sm font-medium text-gray-700 mb-3">分析摘要</h4>
                        <div id="summary-content" class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <!-- Summary will be populated here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 渲染基准选项
     */
    renderBenchmarkOptions() {
        let options = '';

        // Market indices
        BENCHMARK_TYPES.MARKET.benchmarks.forEach(benchmark => {
            const isChecked = this.selectedBenchmarks.includes(benchmark.code);
            const color = SHARPE_CONFIG.BENCHMARK_COLORS[benchmark.code] || '#999999';
            options += `
                <label class="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                    <input type="checkbox"
                        class="benchmark-checkbox w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        value="${benchmark.code}"
                        ${isChecked ? 'checked' : ''}>
                    <span class="w-3 h-3 rounded-full" style="background-color: ${color}"></span>
                    <span class="text-sm">${benchmark.name}</span>
                </label>
            `;
        });

        // Add Buy & Hold and Custom options
        options += `
            <label class="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                <input type="checkbox" class="benchmark-checkbox w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    value="buy_and_hold" ${this.selectedBenchmarks.includes('buy_and_hold') ? 'checked' : ''}>
                <span class="text-sm">买入持有</span>
            </label>
            <label class="flex items-center space-x-2 cursor-pointer hover:bg-gray-50 p-2 rounded">
                <input type="checkbox" class="benchmark-checkbox w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    value="custom" ${this.selectedBenchmarks.includes('custom') ? 'checked' : ''}>
                <span class="text-sm">自定义基准</span>
            </label>
        `;

        return options;
    }

    /**
     * 绑定事件处理器
     */
    bindEvents() {
        // Toggle controls visibility
        const toggleBtn = document.getElementById('toggle-controls');
        const controlsContent = document.getElementById('controls-content');

        toggleBtn.addEventListener('click', () => {
            this.isVisible = !this.isVisible;
            controlsContent.classList.toggle('hidden');

            const icon = toggleBtn.querySelector('svg');
            icon.style.transform = this.isVisible ? 'rotate(0deg)' : 'rotate(-90deg)';
            icon.style.transition = 'transform 0.2s';
        });

        // Benchmark selection
        const benchmarkCheckboxes = this.container.querySelectorAll('.benchmark-checkbox');
        benchmarkCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBenchmarkSelection();
            });
        });

        // Parameter changes
        const riskFreeRateInput = document.getElementById('risk-free-rate');
        const rollingWindowSelect = document.getElementById('rolling-window');
        const bootstrapSamplesInput = document.getElementById('bootstrap-samples');
        const confidenceLevelSelect = document.getElementById('confidence-level');

        riskFreeRateInput.addEventListener('change', () => {
            this.analysisOptions.riskFreeRate = parseFloat(riskFreeRateInput.value) / 100;
            this.updateChartOptions();
        });

        rollingWindowSelect.addEventListener('change', () => {
            this.analysisOptions.windowSize = parseInt(rollingWindowSelect.value);
            this.updateChartOptions();
        });

        bootstrapSamplesInput.addEventListener('change', () => {
            this.analysisOptions.bootstrapSamples = parseInt(bootstrapSamplesInput.value);
            this.updateChartOptions();
        });

        confidenceLevelSelect.addEventListener('change', () => {
            this.analysisOptions.confidenceLevel = parseFloat(confidenceLevelSelect.value);
            this.updateChartOptions();
        });

        // Action buttons
        document.getElementById('run-analysis').addEventListener('click', () => {
            this.runAnalysis();
        });

        document.getElementById('refresh-analysis').addEventListener('click', () => {
            this.refreshAnalysis();
        });

        document.getElementById('export-csv').addEventListener('click', () => {
            this.exportToCSV();
        });

        document.getElementById('export-json').addEventListener('click', () => {
            this.exportToJSON();
        });

        document.getElementById('clear-analysis').addEventListener('click', () => {
            this.clearAnalysis();
        });
    }

    /**
     * 设置图表事件监听器
     */
    setupChartListeners() {
        if (this.chart) {
            this.chart.on('loading', (event) => {
                this.setLoading(event.detail.loading);
            });

            this.chart.on('analysisComplete', (event) => {
                this.updateSummary();
            });
        }
    }

    /**
     * 更新基准选择
     */
    updateBenchmarkSelection() {
        const checkboxes = this.container.querySelectorAll('.benchmark-checkbox:checked');
        this.selectedBenchmarks = Array.from(checkboxes).map(cb => cb.value);

        if (this.selectedBenchmarks.length === 0) {
            // Ensure at least one benchmark is selected
            this.selectedBenchmarks = ['HSI'];
            this.container.querySelector('input[value="HSI"]').checked = true;
        }

        this.updateChartOptions();
    }

    /**
     * 更新图表选项
     */
    async updateChartOptions() {
        if (this.chart) {
            try {
                await this.chart.setSelectedBenchmarks(this.selectedBenchmarks);
                await this.chart.setAnalysisOptions(this.analysisOptions);
            } catch (error) {
                console.error('更新图表选项失败:', error);
                this.showError('更新图表选项失败: ' + error.message);
            }
        }
    }

    /**
     * 运行分析
     */
    async runAnalysis() {
        if (!this.chart) {
            this.showError('图表实例未找到');
            return;
        }

        this.setLoading(true);

        try {
            await this.chart.refreshAnalysis();
            this.showSuccess('分析完成');
            this.updateSummary();
        } catch (error) {
            console.error('运行分析失败:', error);
            this.showError('分析失败: ' + error.message);
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 刷新分析
     */
    async refreshAnalysis() {
        if (!this.chart) return;

        this.setLoading(true);

        try {
            await this.chart.refreshAnalysis();
            this.showSuccess('数据已刷新');
            this.updateSummary();
        } catch (error) {
            console.error('刷新失败:', error);
            this.showError('刷新失败: ' + error.message);
        } finally {
            this.setLoading(false);
        }
    }

    /**
     * 导出CSV
     */
    exportToCSV() {
        if (!this.chart) return;

        try {
            const csvData = this.chart.exportStatsToCSV();
            this.downloadFile(csvData, 'sharpe-analysis-stats.csv', 'text/csv');
            this.showSuccess('CSV文件已导出');
        } catch (error) {
            console.error('导出CSV失败:', error);
            this.showError('导出失败: ' + error.message);
        }
    }

    /**
     * 导出JSON
     */
    exportToJSON() {
        if (!this.chart) return;

        try {
            const jsonData = this.chart.exportToJSON();
            this.downloadFile(jsonData, 'sharpe-analysis-report.json', 'application/json');
            this.showSuccess('JSON文件已导出');
        } catch (error) {
            console.error('导出JSON失败:', error);
            this.showError('导出失败: ' + error.message);
        }
    }

    /**
     * 清除分析
     */
    clearAnalysis() {
        if (!this.chart) return;

        if (confirm('确定要清除所有分析数据吗？')) {
            this.chart.clearAnalysis();
            this.updateSummary();
            this.showSuccess('分析数据已清除');
        }
    }

    /**
     * 设置加载状态
     */
    setLoading(loading) {
        const loadingIndicator = document.getElementById('analysis-loading');
        if (loading) {
            loadingIndicator.classList.remove('hidden');
        } else {
            loadingIndicator.classList.add('hidden');
        }
    }

    /**
     * 更新摘要信息
     */
    updateSummary() {
        if (!this.chart) return;

        const summary = this.chart.getAnalysisSummary();
        const summaryContent = document.getElementById('summary-content');
        const summarySection = document.getElementById('analysis-summary');

        summaryContent.innerHTML = `
            <div>
                <div class="text-gray-500">策略数量</div>
                <div class="font-semibold">${summary.strategies}</div>
            </div>
            <div>
                <div class="text-gray-500">基准数量</div>
                <div class="font-semibold">${summary.benchmarks}</div>
            </div>
            <div>
                <div class="text-gray-500">平均Sharpe</div>
                <div class="font-semibold">${summary.averageSharpe.toFixed(2)}</div>
            </div>
            <div>
                <div class="text-gray-500">高级分析</div>
                <div class="font-semibold">${summary.withAdvancedAnalysis}/${summary.strategies}</div>
            </div>
        `;

        if (summary.strategies > 0) {
            summarySection.classList.remove('hidden');
        } else {
            summarySection.classList.add('hidden');
        }
    }

    /**
     * 下载文件
     */
    downloadFile(content, filename, contentType) {
        const blob = new Blob([content], { type: contentType });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
    }

    /**
     * 显示成功消息
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * 显示错误消息
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 transform transition-all duration-300 translate-x-full`;

        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-white',
            info: 'bg-blue-500 text-white'
        };

        notification.className += ' ' + colors[type];
        notification.innerHTML = `
            <div class="flex items-center">
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Slide in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto remove
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    }

    /**
     * 获取当前配置
     */
    getConfig() {
        return {
            selectedBenchmarks: [...this.selectedBenchmarks],
            analysisOptions: { ...this.analysisOptions }
        };
    }

    /**
     * 设置配置
     */
    setConfig(config) {
        if (config.selectedBenchmarks) {
            this.selectedBenchmarks = [...config.selectedBenchmarks];
            // Update checkboxes
            this.container.querySelectorAll('.benchmark-checkbox').forEach(checkbox => {
                checkbox.checked = this.selectedBenchmarks.includes(checkbox.value);
            });
        }

        if (config.analysisOptions) {
            this.analysisOptions = { ...config.analysisOptions };
            // Update form fields
            document.getElementById('risk-free-rate').value = this.analysisOptions.riskFreeRate * 100;
            document.getElementById('rolling-window').value = this.analysisOptions.windowSize;
            document.getElementById('bootstrap-samples').value = this.analysisOptions.bootstrapSamples;
            document.getElementById('confidence-level').value = this.analysisOptions.confidenceLevel;
        }

        this.updateChartOptions();
    }

    /**
     * 销毁控制面板
     */
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

export default SharpeAnalysisControls;