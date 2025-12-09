/**
 * 个人量化交易系统 - 主JavaScript文件
 */

// 全局变量
let currentPage = 'dashboard';
let priceChart = null;
let currentStock = null;

// API基础URL
const API_BASE = '';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 初始化应用
 */
function initializeApp() {
    // 设置导航事件
    setupNavigation();
    
    // 设置默认日期
    setDefaultDates();
    
    // 加载投资组合列表
    loadPortfolios();
    
    // 显示欢迎消息
    showMessage('欢迎使用个人量化交易系统！', 'success');
}

/**
 * 设置导航功能
 */
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            switchPage(page);
        });
    });
}

/**
 * 切换页面
 */
function switchPage(page) {
    // 隐藏所有页面
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    
    // 移除所有导航项的活动状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 显示目标页面
    document.getElementById(page).classList.add('active');
    
    // 设置导航项活动状态
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    currentPage = page;
    
    // 页面特定的初始化
    switch(page) {
        case 'analysis':
            initializeAnalysisPage();
            break;
        case 'backtest':
            initializeBacktestPage();
            break;
        case 'portfolio':
            loadPortfolios();
            break;
    }
}

/**
 * 初始化分析页面
 */
function initializeAnalysisPage() {
    // 设置搜索事件
    const searchInput = document.getElementById('stock-search');
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchStock();
        }
    });
}

/**
 * 初始化回测页面
 */
function initializeBacktestPage() {
    // 设置默认日期
    setDefaultDates();
}

/**
 * 设置默认日期
 */
function setDefaultDates() {
    const today = new Date();
    const oneYearAgo = new Date(today.getFullYear() - 1, today.getMonth(), today.getDate());
    
    document.getElementById('start-date').value = oneYearAgo.toISOString().split('T')[0];
    document.getElementById('end-date').value = today.toISOString().split('T')[0];
}

/**
 * 显示加载状态
 */
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

/**
 * 显示消息
 */
function showMessage(text, type = 'info') {
    const messageEl = document.getElementById('message');
    const messageTextEl = document.getElementById('message-text');
    
    messageTextEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');
    
    // 3秒后自动隐藏
    setTimeout(() => {
        hideMessage();
    }, 3000);
}

/**
 * 隐藏消息
 */
function hideMessage() {
    document.getElementById('message').classList.add('hidden');
}

/**
 * 快速分析功能
 */
function startQuickAnalysis() {
    switchPage('analysis');
    // 可以预设一些热门股票
    document.getElementById('stock-search').value = '0700.HK';
    searchStock();
}

/**
 * 开始回测功能
 */
function startBacktest() {
    switchPage('backtest');
}

/**
 * 查看投资组合功能
 */
function viewPortfolio() {
    switchPage('portfolio');
}

/**
 * 搜索股票
 */
async function searchStock() {
    const query = document.getElementById('stock-search').value.trim();
    if (!query) {
        showMessage('请输入股票代码或名称', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/data/stocks/search?q=${encodeURIComponent(query)}`);
        const result = await response.json();
        
        if (result.success && result.data.length > 0) {
            const stock = result.data[0];
            currentStock = stock;
            await loadStockData(stock.symbol);
        } else {
            showMessage('未找到相关股票', 'warning');
        }
    } catch (error) {
        console.error('搜索股票失败:', error);
        showMessage('搜索失败，请稍后重试', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * 加载股票数据
 */
async function loadStockData(symbol) {
    showLoading();
    
    try {
        const timeRange = document.getElementById('time-range').value;
        const response = await fetch(`${API_BASE}/api/data/stocks/${symbol}/data?period=${timeRange}`);
        const result = await response.json();
        
        if (result.success) {
            displayStockChart(result.data.data);
            await loadTechnicalIndicators(symbol);
        } else {
            showMessage('加载股票数据失败', 'error');
        }
    } catch (error) {
        console.error('加载股票数据失败:', error);
        showMessage('加载数据失败，请稍后重试', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * 显示股票图表
 */
function displayStockChart(data) {
    const ctx = document.getElementById('price-chart').getContext('2d');
    
    // 销毁现有图表
    if (priceChart) {
        priceChart.destroy();
    }
    
    const labels = data.map(item => new Date(item.timestamp).toLocaleDateString());
    const prices = data.map(item => item.close);
    
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '收盘价',
                data: prices,
                borderColor: '#1e40af',
                backgroundColor: 'rgba(30, 64, 175, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: `${currentStock.name} (${currentStock.symbol}) 价格走势`
                }
            }
        }
    });
}

/**
 * 加载技术指标
 */
async function loadTechnicalIndicators(symbol) {
    try {
        const response = await fetch(`${API_BASE}/api/analysis/indicators/${symbol}`);
        const result = await response.json();
        
        if (result.success) {
            displayTechnicalIndicators(result.data.indicators);
        }
    } catch (error) {
        console.error('加载技术指标失败:', error);
    }
}

/**
 * 显示技术指标
 */
function displayTechnicalIndicators(indicators) {
    const container = document.getElementById('indicators-display');
    
    const indicatorsHtml = `
        <div class="indicator-grid">
            <div class="indicator-item">
                <span class="indicator-label">SMA(20)</span>
                <span class="indicator-value">${indicators.sma_20?.toFixed(2) || 'N/A'}</span>
            </div>
            <div class="indicator-item">
                <span class="indicator-label">SMA(50)</span>
                <span class="indicator-value">${indicators.sma_50?.toFixed(2) || 'N/A'}</span>
            </div>
            <div class="indicator-item">
                <span class="indicator-label">RSI</span>
                <span class="indicator-value">${indicators.rsi?.toFixed(2) || 'N/A'}</span>
            </div>
            <div class="indicator-item">
                <span class="indicator-label">MACD</span>
                <span class="indicator-value">${indicators.macd?.toFixed(2) || 'N/A'}</span>
            </div>
            <div class="indicator-item">
                <span class="indicator-label">布林带上轨</span>
                <span class="indicator-value">${indicators.bollinger_upper?.toFixed(2) || 'N/A'}</span>
            </div>
            <div class="indicator-item">
                <span class="indicator-label">布林带下轨</span>
                <span class="indicator-value">${indicators.bollinger_lower?.toFixed(2) || 'N/A'}</span>
            </div>
        </div>
    `;
    
    container.innerHTML = indicatorsHtml;
}

/**
 * 运行回测
 */
async function runBacktest() {
    const strategy = document.getElementById('strategy-select').value;
    const symbol = document.getElementById('backtest-symbol').value.trim();
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    if (!symbol) {
        showMessage('请输入股票代码', 'warning');
        return;
    }
    
    if (!startDate || !endDate) {
        showMessage('请选择回测期间', 'warning');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/backtest/strategy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol,
                strategy: { name: strategy },
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayBacktestResults(result.data);
        } else {
            showMessage('回测失败', 'error');
        }
    } catch (error) {
        console.error('回测失败:', error);
        showMessage('回测失败，请稍后重试', 'error');
    } finally {
        hideLoading();
    }
}

/**
 * 显示回测结果
 */
function displayBacktestResults(data) {
    const container = document.getElementById('backtest-results');
    
    const resultsHtml = `
        <h3>回测结果</h3>
        <div class="backtest-metrics">
            <div class="metric-item">
                <span class="metric-label">总收益率</span>
                <span class="metric-value ${data.total_return >= 0 ? 'text-success' : 'text-error'}">
                    ${data.total_return?.toFixed(2) || 'N/A'}%
                </span>
            </div>
            <div class="metric-item">
                <span class="metric-label">年化收益率</span>
                <span class="metric-value ${data.annual_return >= 0 ? 'text-success' : 'text-error'}">
                    ${data.annual_return?.toFixed(2) || 'N/A'}%
                </span>
            </div>
            <div class="metric-item">
                <span class="metric-label">最大回撤</span>
                <span class="metric-value text-error">
                    ${data.max_drawdown?.toFixed(2) || 'N/A'}%
                </span>
            </div>
            <div class="metric-item">
                <span class="metric-label">夏普比率</span>
                <span class="metric-value">
                    ${data.sharpe_ratio?.toFixed(2) || 'N/A'}
                </span>
            </div>
            <div class="metric-item">
                <span class="metric-label">胜率</span>
                <span class="metric-value">
                    ${data.win_rate?.toFixed(1) || 'N/A'}%
                </span>
            </div>
            <div class="metric-item">
                <span class="metric-label">总交易次数</span>
                <span class="metric-value">
                    ${data.total_trades || 'N/A'}
                </span>
            </div>
        </div>
    `;
    
    container.innerHTML = resultsHtml;
}

/**
 * 加载投资组合列表
 */
async function loadPortfolios() {
    try {
        const response = await fetch(`${API_BASE}/api/portfolio/portfolios`);
        const result = await response.json();
        
        if (result.success) {
            displayPortfolios(result.data);
        }
    } catch (error) {
        console.error('加载投资组合失败:', error);
        showMessage('加载投资组合失败', 'error');
    }
}

/**
 * 显示投资组合列表
 */
function displayPortfolios(portfolios) {
    const container = document.getElementById('portfolios-list');
    
    if (portfolios.length === 0) {
        container.innerHTML = '<p>暂无投资组合，点击"创建投资组合"开始管理您的投资。</p>';
        return;
    }
    
    const portfoliosHtml = portfolios.map(portfolio => `
        <div class="portfolio-item">
            <h3>${portfolio.name}</h3>
            <p>${portfolio.description || '暂无描述'}</p>
            <div class="portfolio-stats">
                <div class="portfolio-stat">
                    <div class="label">总价值</div>
                    <div class="value">¥${portfolio.total_value?.toLocaleString() || '0'}</div>
                </div>
                <div class="portfolio-stat">
                    <div class="label">总收益率</div>
                    <div class="value ${portfolio.total_return >= 0 ? 'text-success' : 'text-error'}">
                        ${portfolio.total_return?.toFixed(2) || '0'}%
                    </div>
                </div>
                <div class="portfolio-stat">
                    <div class="label">持仓数量</div>
                    <div class="value">${portfolio.holdings?.length || 0}</div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = portfoliosHtml;
}

/**
 * 创建投资组合
 */
async function createPortfolio() {
    const name = prompt('请输入投资组合名称:');
    if (!name) return;
    
    const description = prompt('请输入投资组合描述 (可选):') || '';
    
    try {
        const response = await fetch(`${API_BASE}/api/portfolio/portfolios`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('投资组合创建成功', 'success');
            loadPortfolios();
        } else {
            showMessage('创建失败', 'error');
        }
    } catch (error) {
        console.error('创建投资组合失败:', error);
        showMessage('创建失败，请稍后重试', 'error');
    }
}

/**
 * 刷新投资组合列表
 */
function refreshPortfolios() {
    loadPortfolios();
    showMessage('投资组合列表已刷新', 'success');
}

// 添加样式到页面
const style = document.createElement('style');
style.textContent = `
    .indicator-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
    }
    
    .indicator-item {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem;
        background: #f9fafb;
        border-radius: 0.375rem;
    }
    
    .indicator-label {
        font-weight: 500;
        color: #6b7280;
    }
    
    .indicator-value {
        font-weight: 600;
        color: #111827;
    }
    
    .backtest-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .metric-item {
        display: flex;
        justify-content: space-between;
        padding: 1rem;
        background: #f9fafb;
        border-radius: 0.375rem;
    }
    
    .metric-label {
        font-weight: 500;
        color: #6b7280;
    }
    
    .metric-value {
        font-weight: 600;
        font-size: 1.125rem;
    }
`;
document.head.appendChild(style);
