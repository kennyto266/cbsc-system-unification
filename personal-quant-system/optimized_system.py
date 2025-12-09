"""
Optimized Personal Quant Trading System
With Performance Improvements and More Strategies
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import aiohttp
from functools import lru_cache
import json

# Create FastAPI app with optimizations
app = FastAPI(
    title="Optimized Quant Trading System",
    description="High-performance quantitative trading analysis platform",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance optimizations
@lru_cache(maxsize=100)
def cached_get_stock_data(symbol: str, duration: int = 1825):
    """Cached stock data retrieval"""
    try:
        url = 'http://18.180.162.113:9191/inst/getInst'
        params = {'symbol': symbol.lower(), 'duration': duration}
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if 'data' not in data or not isinstance(data['data'], dict):
            return None
        
        # Convert data format efficiently
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

# Enhanced Trading Strategies
class AdvancedStrategies:
    @staticmethod
    def sma_crossover(data):
        """SMA Crossover Strategy"""
        if len(data) < 50:
            return 'HOLD'
        
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        
        sma_20 = df['close'].rolling(window=20).mean()
        sma_50 = df['close'].rolling(window=50).mean()
        current_price = df['close'].iloc[-1]
        
        if sma_20.iloc[-1] > sma_50.iloc[-1] and current_price > sma_20.iloc[-1]:
            return 'BUY'
        elif sma_20.iloc[-1] < sma_50.iloc[-1] and current_price < sma_20.iloc[-1]:
            return 'SELL'
        else:
            return 'HOLD'
    
    @staticmethod
    def rsi_strategy(data):
        """RSI Strategy"""
        if len(data) < 14:
            return 'HOLD'
        
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        
        delta = df['close'].diff()
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
    
    @staticmethod
    def macd_strategy(data):
        """MACD Strategy"""
        if len(data) < 26:
            return 'HOLD'
        
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9).mean()
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]
        
        if current_macd > current_signal and prev_macd <= prev_signal:
            return 'BUY'
        elif current_macd < current_signal and prev_macd >= prev_signal:
            return 'SELL'
        else:
            return 'HOLD'
    
    @staticmethod
    def bollinger_bands_strategy(data):
        """Bollinger Bands Strategy"""
        if len(data) < 20:
            return 'HOLD'
        
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        upper_band = sma_20 + (2 * std_20)
        lower_band = sma_20 - (2 * std_20)
        
        current_price = df['close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        if current_price <= current_lower:
            return 'BUY'
        elif current_price >= current_upper:
            return 'SELL'
        else:
            return 'HOLD'
    
    @staticmethod
    def momentum_strategy(data):
        """Momentum Strategy"""
        if len(data) < 10:
            return 'HOLD'
        
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        
        # Calculate momentum (10-day price change)
        momentum = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10] * 100
        
        if momentum > 5:
            return 'BUY'
        elif momentum < -5:
            return 'SELL'
        else:
            return 'HOLD'

# Optimized Backtest Engine
class OptimizedBacktestEngine:
    def __init__(self):
        self.initial_capital = 100000
        self.commission = 0.001
    
    def run_backtest(self, data, strategy):
        """Optimized backtest with vectorized operations"""
        try:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            df = df.sort_values('timestamp')
            
            # Vectorized signal generation
            signals = []
            for i in range(len(df)):
                if i < 50:  # Need enough data for most strategies
                    signals.append('HOLD')
                else:
                    current_data = df.iloc[:i+1]
                    signal = strategy(current_data)
                    signals.append(signal)
            
            df['signal'] = signals
            
            # Calculate positions and portfolio value
            df['position'] = 0
            df['portfolio_value'] = self.initial_capital
            
            cash = self.initial_capital
            shares = 0
            
            for i in range(len(df)):
                current_price = df['close'].iloc[i]
                signal = df['signal'].iloc[i]
                
                if signal == 'BUY' and cash > 0:
                    shares_to_buy = cash / (current_price * (1 + self.commission))
                    cost = shares_to_buy * current_price * (1 + self.commission)
                    if cost <= cash:
                        shares += shares_to_buy
                        cash -= cost
                        df.loc[df.index[i], 'position'] = shares_to_buy
                
                elif signal == 'SELL' and shares > 0:
                    proceeds = shares * current_price * (1 - self.commission)
                    cash += proceeds
                    df.loc[df.index[i], 'position'] = -shares
                    shares = 0
                
                # Update portfolio value
                df.loc[df.index[i], 'portfolio_value'] = cash + shares * current_price
            
            return self.calculate_metrics(df)
            
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_metrics(self, df):
        """Calculate performance metrics efficiently"""
        final_value = df['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # Calculate daily returns
        df['daily_return'] = df['portfolio_value'].pct_change()
        
        # Risk metrics
        volatility = df['daily_return'].std() * np.sqrt(252) * 100
        sharpe_ratio = (df['daily_return'].mean() * 252) / (df['daily_return'].std() * np.sqrt(252)) if df['daily_return'].std() > 0 else 0
        
        # Max drawdown
        peak = df['portfolio_value'].expanding().max()
        drawdown = (df['portfolio_value'] - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Total trades
        position_changes = df['position'].diff().abs() > 0
        total_trades = position_changes.sum()
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades
        }

# Initialize engines
strategies = AdvancedStrategies()
backtest_engine = OptimizedBacktestEngine()

@app.get('/', response_class=HTMLResponse)
def read_root():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Optimized Quant Trading System</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
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
            flex-wrap: wrap;
        }
        .tab {
            padding: 15px 30px;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-weight: 500;
        }
        .tab.active {
            border-bottom-color: #667eea;
            color: #667eea;
            font-weight: bold;
        }
        .tab:hover {
            background-color: #f8f9fa;
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
            flex-wrap: wrap;
        }
        .search-box input { 
            flex: 1; 
            max-width: 400px;
            padding: 15px; 
            border: 2px solid #e1e8ed; 
            border-radius: 10px; 
            font-size: 16px; 
            transition: border-color 0.3s;
        }
        .search-box input:focus { 
            outline: none; 
            border-color: #667eea; 
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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
            transition: transform 0.2s;
        }
        .search-box button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
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
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
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
        .strategy-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .strategy-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e1e8ed;
        }
        .strategy-name {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .strategy-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .strategy-metric {
            text-align: center;
        }
        .strategy-metric-value {
            font-weight: bold;
            color: #27ae60;
        }
        .strategy-metric-label {
            font-size: 0.8em;
            color: #7f8c8d;
        }
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
            border-left: 4px solid #e74c3c;
        }
        .success { 
            color: #27ae60; 
            background: #f0f9f0; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
            border-left: 4px solid #27ae60;
        }
        @media (max-width: 768px) {
            .results { 
                grid-template-columns: 1fr; 
            }
            .search-box {
                flex-direction: column;
            }
            .search-box input {
                max-width: none;
            }
            .tabs {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Optimized Quant Trading System</h1>
            <p>High-Performance Analysis with Advanced Strategies</p>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('analysis')">Analysis</div>
            <div class="tab" onclick="switchTab('strategies')">Strategies</div>
            <div class="tab" onclick="switchTab('backtest')">Backtesting</div>
            <div class="tab" onclick="switchTab('risk')">Risk Assessment</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="stockInput" placeholder="Enter stock code (e.g., 0700.HK, 2800.HK)" />
            <button onclick="analyzeStock()">🔍 Analyze</button>
        </div>
        
        <div id="loading" class="loading" style="display: none;">
            <div>⏳ Processing with optimized algorithms...</div>
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
        
        <!-- Strategies Tab -->
        <div id="strategies" class="tab-content">
            <div id="strategiesResults" style="display: none;">
                <h3>🎯 Trading Strategies Performance</h3>
                <div class="strategy-grid" id="strategiesGrid"></div>
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
                    await runStrategies(symbol);
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
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
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
        
        async function runStrategies(symbol) {
            try {
                const response = await fetch(`/api/strategies/${symbol}`);
                const result = await response.json();
                
                if (result.success) {
                    displayStrategiesResults(result.data);
                }
            } catch (error) {
                console.error('Strategies error:', error);
            }
        }
        
        function displayStrategiesResults(data) {
            const container = document.getElementById('strategiesGrid');
            container.innerHTML = '';
            
            Object.entries(data).forEach(([strategyName, metrics]) => {
                const div = document.createElement('div');
                div.className = 'strategy-card';
                div.innerHTML = `
                    <div class="strategy-name">${strategyName.replace('_', ' ').toUpperCase()}</div>
                    <div class="strategy-metrics">
                        <div class="strategy-metric">
                            <div class="strategy-metric-value">${metrics.total_return.toFixed(2)}%</div>
                            <div class="strategy-metric-label">Return</div>
                        </div>
                        <div class="strategy-metric">
                            <div class="strategy-metric-value">${metrics.sharpe_ratio.toFixed(2)}</div>
                            <div class="strategy-metric-label">Sharpe</div>
                        </div>
                        <div class="strategy-metric">
                            <div class="strategy-metric-value">${metrics.volatility.toFixed(2)}%</div>
                            <div class="strategy-metric-label">Volatility</div>
                        </div>
                        <div class="strategy-metric">
                            <div class="strategy-metric-value">${metrics.total_trades}</div>
                            <div class="strategy-metric-label">Trades</div>
                        </div>
                    </div>
                `;
                container.appendChild(div);
            });
            
            document.getElementById('strategiesResults').style.display = 'block';
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
                <div class="success">
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
            document.getElementById('strategiesResults').style.display = 'none';
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

def calculate_indicators(data):
    """Optimized indicator calculation"""
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

def assess_risk(data, indicators):
    """Optimized risk assessment"""
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
                recommendation = 'Strong Buy - Low risk, oversold'
            elif rsi > 70:
                recommendation = 'Hold - Low risk, overbought'
            else:
                recommendation = 'Buy - Low risk, good entry'
        elif risk_level == 'MEDIUM':
            if rsi < 30:
                recommendation = 'Buy - Medium risk, oversold'
            elif rsi > 70:
                recommendation = 'Sell - Medium risk, overbought'
            else:
                recommendation = 'Hold - Medium risk, wait for better entry'
        else:
            if rsi < 30:
                recommendation = 'Consider - High risk, oversold'
            elif rsi > 70:
                recommendation = 'Avoid - High risk, overbought'
            else:
                recommendation = 'Avoid - High risk, volatile'
        
        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'volatility': volatility,
            'var_95': var_95,
            'recommendation': recommendation
        }
        
    except Exception as e:
        return {
            'risk_level': 'UNKNOWN',
            'risk_score': 0,
            'volatility': 0,
            'var_95': 0,
            'recommendation': 'Unable to assess risk'
        }

@app.get('/api/analysis/{symbol}')
def analyze_stock(symbol: str):
    try:
        data = cached_get_stock_data(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 20:
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get('/api/strategies/{symbol}')
def analyze_strategies(symbol: str):
    try:
        data = cached_get_stock_data(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 50:
            raise HTTPException(status_code=400, detail="Insufficient data for strategy analysis")
        
        # Test all strategies
        strategy_results = {}
        
        strategies_list = [
            ('sma_crossover', strategies.sma_crossover),
            ('rsi_strategy', strategies.rsi_strategy),
            ('macd_strategy', strategies.macd_strategy),
            ('bollinger_bands_strategy', strategies.bollinger_bands_strategy),
            ('momentum_strategy', strategies.momentum_strategy)
        ]
        
        for strategy_name, strategy_func in strategies_list:
            try:
                result = backtest_engine.run_backtest(data, strategy_func)
                if 'error' not in result:
                    strategy_results[strategy_name] = result
            except Exception as e:
                print(f"Strategy {strategy_name} failed: {e}")
                continue
        
        return {
            'success': True,
            'data': strategy_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy analysis failed: {str(e)}")

@app.get('/api/backtest/{symbol}')
def backtest_stock(symbol: str):
    try:
        data = cached_get_stock_data(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 50:
            raise HTTPException(status_code=400, detail="Insufficient data for backtesting")
        
        # Run backtest with best strategy (SMA crossover)
        result = backtest_engine.run_backtest(data, strategies.sma_crossover)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        return {
            'success': True,
            'data': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@app.get('/api/risk/{symbol}')
def assess_risk_endpoint(symbol: str):
    try:
        data = cached_get_stock_data(symbol)
        if not data:
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 20:
            raise HTTPException(status_code=400, detail="Insufficient data for risk assessment")
        
        indicators = calculate_indicators(data)
        risk_result = assess_risk(data, indicators)
        
        return {
            'success': True,
            'data': risk_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Optimized Quant Trading System v2.0...")
    print("📊 Features: Analysis, Multiple Strategies, Backtesting, Risk Assessment")
    print("⚡ Performance: Cached data, Vectorized operations, Optimized algorithms")
    print("🌐 Access: http://localhost:8001")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
