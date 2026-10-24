"""
Fixed Enhanced Personal Quant Trading System
With working Backtesting and Risk Assessment APIs
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

app = FastAPI()

# Backtesting Engine
class BacktestEngine:
    def __init__(self):
        self.initial_capital = 100000
        self.commission = 0.001
    
    def run_backtest(self, data, strategy):
        try:
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('date')
            
            portfolio = {
                'cash': self.initial_capital,
                'shares': 0,
                'value': self.initial_capital,
                'trades': []
            }
            
            for i in range(1, len(df)):
                current_data = df.iloc[:i+1]
                signal = strategy(current_data)
                
                if signal == 'BUY' and portfolio['cash'] > 0:
                    price = df.iloc[i]['close']
                    shares_to_buy = portfolio['cash'] / (price * (1 + self.commission))
                    cost = shares_to_buy * price * (1 + self.commission)
                    
                    if cost <= portfolio['cash']:
                        portfolio['shares'] += shares_to_buy
                        portfolio['cash'] -= cost
                        portfolio['trades'].append({
                            'date': df.iloc[i]['date'],
                            'action': 'BUY',
                            'price': price,
                            'shares': shares_to_buy,
                            'value': cost
                        })
                
                elif signal == 'SELL' and portfolio['shares'] > 0:
                    price = df.iloc[i]['close']
                    proceeds = portfolio['shares'] * price * (1 - self.commission)
                    
                    portfolio['cash'] += proceeds
                    portfolio['trades'].append({
                        'date': df.iloc[i]['date'],
                        'action': 'SELL',
                        'price': price,
                        'shares': portfolio['shares'],
                        'value': proceeds
                    })
                    portfolio['shares'] = 0
                
                current_price = df.iloc[i]['close']
                portfolio['value'] = portfolio['cash'] + portfolio['shares'] * current_price
            
            return self.calculate_metrics(portfolio, df)
            
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_metrics(self, portfolio, df):
        final_value = portfolio['value']
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        df['portfolio_value'] = df['close'] * portfolio['shares'] + portfolio['cash']
        df['daily_return'] = df['portfolio_value'].pct_change()
        
        volatility = df['daily_return'].std() * np.sqrt(252) * 100
        sharpe_ratio = (df['daily_return'].mean() * 252) / (df['daily_return'].std() * np.sqrt(252)) if df['daily_return'].std() > 0 else 0
        max_drawdown = self.calculate_max_drawdown(df['portfolio_value'])
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(portfolio['trades']),
            'trades': portfolio['trades'][-10:]
        }
    
    def calculate_max_drawdown(self, values):
        peak = values.expanding().max()
        drawdown = (values - peak) / peak
        return drawdown.min() * 100

# Risk Assessment Engine
class RiskAssessment:
    def assess_risk(self, data, indicators):
        try:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            var_95 = np.percentile(returns, 5) * 100
            
            risk_score = min(volatility / 2, 50) + min(abs(var_95) * 2, 30) + 20
            
            if risk_score <= 30:
                risk_level = 'LOW'
            elif risk_score <= 60:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'
            
            rsi = indicators.get('rsi', 50)
            if risk_level == 'LOW':
                if rsi < 30:
                    recommendation = "Strong Buy - Low risk, oversold"
                elif rsi > 70:
                    recommendation = "Hold - Low risk, overbought"
                else:
                    recommendation = "Buy - Low risk, good entry"
            elif risk_level == 'MEDIUM':
                if rsi < 30:
                    recommendation = "Buy - Medium risk, oversold"
                elif rsi > 70:
                    recommendation = "Sell - Medium risk, overbought"
                else:
                    recommendation = "Hold - Medium risk, wait for better entry"
            else:
                if rsi < 30:
                    recommendation = "Consider - High risk, oversold"
                elif rsi > 70:
                    recommendation = "Avoid - High risk, overbought"
                else:
                    recommendation = "Avoid - High risk, volatile"
            
            return {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'volatility': volatility,
                'var_95': var_95,
                'beta': 1.0,
                'recommendation': recommendation
            }
            
        except Exception as e:
            return {'error': str(e)}

# Trading Strategies
class TradingStrategies:
    @staticmethod
    def sma_crossover(data):
        if len(data) < 50:
            return 'HOLD'
        
        sma_20 = data['close'].rolling(window=20).mean().iloc[-1]
        sma_50 = data['close'].rolling(window=50).mean().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        if sma_20 > sma_50 and current_price > sma_20:
            return 'BUY'
        elif sma_20 < sma_50 and current_price < sma_20:
            return 'SELL'
        else:
            return 'HOLD'
    
    @staticmethod
    def rsi_strategy(data):
        if len(data) < 14:
            return 'HOLD'
        
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            return 'BUY'
        elif current_rsi > 70:
            return 'SELL'
        else:
            return 'HOLD'

# Initialize engines
backtest_engine = BacktestEngine()
risk_assessor = RiskAssessment()
strategies = TradingStrategies()

def get_stock_data(symbol):
    """Get stock data from API"""
    try:
        url = 'http://18.180.162.113:9191/inst/getInst'
        params = {'symbol': symbol.lower(), 'duration': 1825}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if 'data' not in data or not isinstance(data['data'], dict):
            return None
        
        # Convert data format
        time_series = data['data']
        timestamps = set()
        
        for key in time_series.keys():
            if key in ['open', 'high', 'low', 'close', 'volume']:
                timestamps.update(time_series[key].keys())
        
        timestamps = sorted(list(timestamps))
        formatted_data = []
        
        for ts in timestamps:
            row = {'timestamp': ts}
            for price_type in ['open', 'high', 'low', 'close', 'volume']:
                if price_type in time_series and ts in time_series[price_type]:
                    row[price_type] = time_series[price_type][ts]
                else:
                    row[price_type] = None
            
            if all(row[key] is not None for key in ['open', 'high', 'low', 'close', 'volume']):
                formatted_data.append(row)
        
        return formatted_data
        
    except Exception as e:
        return None

def calculate_indicators(data):
    """Calculate technical indicators"""
    try:
        df = pd.DataFrame(data)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        close = df['close']
        
        indicators = {}
        
        # Moving averages
        if len(close) >= 20:
            indicators['sma_20'] = float(close.rolling(window=20).mean().iloc[-1])
        if len(close) >= 50:
            indicators['sma_50'] = float(close.rolling(window=50).mean().iloc[-1])
        
        # RSI
        if len(close) >= 14:
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        
        # MACD
        if len(close) >= 26:
            ema_12 = close.ewm(span=12).mean()
            ema_26 = close.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            indicators['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
            indicators['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
            indicators['macd_histogram'] = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
        
        # Bollinger Bands
        if len(close) >= 20:
            sma_20 = close.rolling(window=20).mean()
            std_20 = close.rolling(window=20).std()
            indicators['bollinger_upper'] = float(sma_20.iloc[-1] + 2 * std_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
            indicators['bollinger_middle'] = float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
            indicators['bollinger_lower'] = float(sma_20.iloc[-1] - 2 * std_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
        
        return indicators
        
    except Exception as e:
        return {}

@app.get('/', response_class=HTMLResponse)
def read_root():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Quant Trading System</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            color: #2c3e50;
        }
        .header h1 { 
            margin: 0; 
            font-size: 2.5em;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #e1e8ed;
        }
        .tab {
            padding: 15px 30px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
            font-weight: bold;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .search-box { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 30px; 
            justify-content: center;
        }
        .search-box input { 
            flex: 1; 
            max-width: 400px;
            padding: 15px; 
            border: 2px solid #e1e8ed; 
            border-radius: 10px; 
            font-size: 16px; 
        }
        .search-box button { 
            padding: 15px 30px; 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-size: 16px; 
            font-weight: bold;
        }
        .results { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 30px; 
        }
        .chart-container { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #e1e8ed;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #e1e8ed;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .risk-indicator {
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            margin: 10px 0;
        }
        .risk-low { background: #d4edda; color: #155724; }
        .risk-medium { background: #fff3cd; color: #856404; }
        .risk-high { background: #f8d7da; color: #721c24; }
        .loading { 
            text-align: center; 
            padding: 40px; 
            color: #7f8c8d; 
            font-size: 18px;
        }
        .error { 
            color: #e74c3c; 
            background: #fdf2f2; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Enhanced Quant Trading System</h1>
            <p>Advanced Analysis with Backtesting & Risk Assessment</p>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('analysis')">Analysis</div>
            <div class="tab" onclick="switchTab('backtest')">Backtesting</div>
            <div class="tab" onclick="switchTab('risk')">Risk Assessment</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="stockInput" placeholder="Enter stock code (e.g., 0700.HK, 2800.HK)" />
            <button onclick="analyzeStock()">🔍 Analyze</button>
        </div>
        
        <div id="loading" class="loading" style="display: none;">
            <div>⏳ Processing...</div>
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
        
        <!-- Analysis Tab -->
        <div id="analysis" class="tab-content active">
            <div id="analysisResults" style="display: none;">
                <div class="results">
                    <div class="chart-container">
                        <h3>📊 Price Chart</h3>
                        <canvas id="priceChart" width="400" height="300"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>📈 Technical Indicators</h3>
                        <div id="indicatorsList"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Backtesting Tab -->
        <div id="backtest" class="tab-content">
            <div id="backtestResults" style="display: none;">
                <div class="metrics-grid" id="backtestMetrics"></div>
                <div class="chart-container">
                    <h3>📊 Portfolio Performance</h3>
                    <canvas id="backtestChart" width="400" height="300"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Risk Assessment Tab -->
        <div id="risk" class="tab-content">
            <div id="riskResults" style="display: none;">
                <div class="metrics-grid" id="riskMetrics"></div>
                <div id="riskRecommendation"></div>
            </div>
        </div>
    </div>

    <script>
        let priceChart = null;
        let backtestChart = null;
        let currentData = null;
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function analyzeStock() {
            const symbol = document.getElementById('stockInput').value.trim();
            if (!symbol) {
                showError('Please enter a stock code');
                return;
            }
            
            showLoading(true);
            hideError();
            hideAllResults();
            
            try {
                const response = await fetch(`/api/analysis/${symbol}`);
                const result = await response.json();
                
                if (result.success) {
                    currentData = result.data;
                    displayAnalysisResults(result.data);
                    await runBacktest(symbol);
                    await assessRisk(symbol);
                } else {
                    showError('Analysis failed: ' + result.message);
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                showLoading(false);
            }
        }
        
        function displayAnalysisResults(data) {
            displayChart(data.price_data);
            displayIndicators(data.indicators);
            document.getElementById('analysisResults').style.display = 'block';
        }
        
        function displayChart(priceData) {
            const ctx = document.getElementById('priceChart').getContext('2d');
            
            if (priceChart) {
                priceChart.destroy();
            }
            
            const recentData = priceData.slice(-50);
            const labels = recentData.map(item => new Date(item.timestamp).toLocaleDateString());
            const prices = recentData.map(item => item.close);
            
            priceChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Close Price',
                        data: prices,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }
        
        function displayIndicators(indicators) {
            const container = document.getElementById('indicatorsList');
            container.innerHTML = '';
            
            const indicatorItems = [
                { label: 'SMA(20)', value: indicators.sma_20 },
                { label: 'SMA(50)', value: indicators.sma_50 },
                { label: 'RSI', value: indicators.rsi },
                { label: 'MACD', value: indicators.macd },
                { label: 'MACD Signal', value: indicators.macd_signal },
                { label: 'Bollinger Upper', value: indicators.bollinger_upper },
                { label: 'Bollinger Middle', value: indicators.bollinger_middle },
                { label: 'Bollinger Lower', value: indicators.bollinger_lower }
            ];
            
            indicatorItems.forEach(item => {
                if (item.value !== null && item.value !== undefined) {
                    const div = document.createElement('div');
                    div.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;';
                    div.innerHTML = `
                        <span style="font-weight: bold; color: #2c3e50;">${item.label}</span>
                        <span style="color: #27ae60; font-weight: bold;">${item.value.toFixed(2)}</span>
                    `;
                    container.appendChild(div);
                }
            });
        }
        
        async function runBacktest(symbol) {
            try {
                const response = await fetch(`/api/backtest/${symbol}`);
                const result = await response.json();
                
                if (result.success) {
                    displayBacktestResults(result.data);
                }
            } catch (error) {
                console.error('Backtest error:', error);
            }
        }
        
        function displayBacktestResults(data) {
            const container = document.getElementById('backtestMetrics');
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.total_return.toFixed(2)}%</div>
                    <div class="metric-label">Total Return</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.volatility.toFixed(2)}%</div>
                    <div class="metric-label">Volatility</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sharpe_ratio.toFixed(2)}</div>
                    <div class="metric-label">Sharpe Ratio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.max_drawdown.toFixed(2)}%</div>
                    <div class="metric-label">Max Drawdown</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.total_trades}</div>
                    <div class="metric-label">Total Trades</div>
                </div>
            `;
            
            document.getElementById('backtestResults').style.display = 'block';
        }
        
        async function assessRisk(symbol) {
            try {
                const response = await fetch(`/api/risk/${symbol}`);
                const result = await response.json();
                
                if (result.success) {
                    displayRiskResults(result.data);
                }
            } catch (error) {
                console.error('Risk assessment error:', error);
            }
        }
        
        function displayRiskResults(data) {
            const container = document.getElementById('riskMetrics');
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.risk_level}</div>
                    <div class="metric-label">Risk Level</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.risk_score.toFixed(0)}</div>
                    <div class="metric-label">Risk Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.volatility.toFixed(2)}%</div>
                    <div class="metric-label">Volatility</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.var_95.toFixed(2)}%</div>
                    <div class="metric-label">VaR (95%)</div>
                </div>
            `;
            
            const riskDiv = document.getElementById('riskRecommendation');
            riskDiv.innerHTML = `
                <div class="risk-indicator risk-${data.risk_level.toLowerCase()}">
                    <h3>Investment Recommendation</h3>
                    <p>${data.recommendation}</p>
                </div>
            `;
            
            document.getElementById('riskResults').style.display = 'block';
        }
        
        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }
        
        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
        
        function hideAllResults() {
            document.getElementById('analysisResults').style.display = 'none';
            document.getElementById('backtestResults').style.display = 'none';
            document.getElementById('riskResults').style.display = 'none';
        }
        
        document.getElementById('stockInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeStock();
            }
        });
    </script>
</body>
</html>
    '''

@app.get('/api/analysis/{symbol}')
def analyze_stock(symbol: str):
    try:
        data = get_stock_data(symbol)
        if not data:
            return {'success': False, 'message': 'Failed to get stock data'}
        
        if len(data) < 20:
            return {'success': False, 'message': 'Insufficient data for analysis'}
        
        indicators = calculate_indicators(data)
        
        return {
            'success': True,
            'data': {
                'symbol': symbol,
                'price_data': data,
                'indicators': indicators,
                'current_price': float(pd.DataFrame(data)['close'].iloc[-1]),
                'data_count': len(data)
            }
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Analysis failed: {str(e)}'}

@app.get('/api/backtest/{symbol}')
def backtest_stock(symbol: str):
    try:
        data = get_stock_data(symbol)
        if not data:
            return {'success': False, 'message': 'Failed to get stock data'}
        
        if len(data) < 50:
            return {'success': False, 'message': 'Insufficient data for backtesting'}
        
        # Run backtests with different strategies
        sma_result = backtest_engine.run_backtest(data, strategies.sma_crossover)
        rsi_result = backtest_engine.run_backtest(data, strategies.rsi_strategy)
        
        # Find best strategy
        best_strategy = 'sma_crossover' if sma_result.get('total_return', -999) > rsi_result.get('total_return', -999) else 'rsi_strategy'
        best_result = sma_result if best_strategy == 'sma_crossover' else rsi_result
        
        return {
            'success': True,
            'data': {
                'symbol': symbol,
                'best_strategy': best_strategy,
                'results': best_result,
                'all_strategies': {
                    'sma_crossover': sma_result,
                    'rsi_strategy': rsi_result
                }
            }
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Backtest failed: {str(e)}'}

@app.get('/api/risk/{symbol}')
def assess_risk(symbol: str):
    try:
        data = get_stock_data(symbol)
        if not data:
            return {'success': False, 'message': 'Failed to get stock data'}
        
        if len(data) < 20:
            return {'success': False, 'message': 'Insufficient data for risk assessment'}
        
        indicators = calculate_indicators(data)
        risk_result = risk_assessor.assess_risk(data, indicators)
        
        return {
            'success': True,
            'data': risk_result
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Risk assessment failed: {str(e)}'}

if __name__ == "__main__":
    print("Starting Fixed Enhanced Quant Trading System...")
    print("Features: Analysis, Backtesting, Risk Assessment")
    print("Access: http://localhost:8001")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
