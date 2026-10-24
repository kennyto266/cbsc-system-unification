"""
Personal Quant Trading System
Complete working version without Chinese characters
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import requests
import pandas as pd
import json

# Create FastAPI app
app = FastAPI()

@app.get('/', response_class=HTMLResponse)
def read_root():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Quant Trading System</title>
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
            max-width: 1200px; 
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
        .indicators { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #e1e8ed;
        }
        .indicator-item { 
            display: flex; 
            justify-content: space-between; 
            padding: 12px 0; 
            border-bottom: 1px solid #e1e8ed; 
            transition: background-color 0.2s;
        }
        .indicator-item:hover {
            background-color: #f0f2f5;
        }
        .indicator-label { 
            font-weight: bold; 
            color: #2c3e50; 
        }
        .indicator-value { 
            color: #27ae60; 
            font-weight: bold;
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
        .stock-info {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .stock-info h2 {
            margin: 0 0 10px 0;
            font-size: 1.8em;
        }
        .stock-info p {
            margin: 5px 0;
            opacity: 0.9;
        }
        .trend { 
            padding: 15px; 
            border-radius: 10px; 
            margin: 15px 0; 
            text-align: center; 
            font-weight: bold; 
            font-size: 18px;
        }
        .trend.uptrend { 
            background: linear-gradient(45deg, #d4edda, #c3e6cb); 
            color: #155724; 
        }
        .trend.downtrend { 
            background: linear-gradient(45deg, #f8d7da, #f5c6cb); 
            color: #721c24; 
        }
        .trend.sideways { 
            background: linear-gradient(45deg, #fff3cd, #ffeaa7); 
            color: #856404; 
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Personal Quant Trading System</h1>
            <p>Professional HK Stock Quantitative Analysis Tool</p>
        </div>
        
        <div class="search-box">
            <input type="text" id="stockInput" placeholder="Enter stock code (e.g., 0700.HK, 2800.HK, 1299.HK)" />
            <button onclick="analyzeStock()">🔍 Analyze Stock</button>
        </div>
        
        <div id="loading" class="loading" style="display: none;">
            <div>⏳ Analyzing stock data...</div>
            <div style="margin-top: 10px; font-size: 14px; color: #95a5a6;">Please wait, this may take a few seconds</div>
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
        
        <div id="results" style="display: none;">
            <div id="stockInfo" class="stock-info" style="display: none;"></div>
            
            <div class="results">
                <div class="chart-container">
                    <h3>📊 Price Chart</h3>
                    <canvas id="priceChart" width="400" height="300"></canvas>
                </div>
                
                <div class="indicators">
                    <h3>📈 Technical Indicators</h3>
                    <div id="indicatorsList"></div>
                    
                    <div id="trendAnalysis"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let priceChart = null;
        
        async function analyzeStock() {
            const symbol = document.getElementById('stockInput').value.trim();
            if (!symbol) {
                showError('Please enter a stock code');
                return;
            }
            
            showLoading(true);
            hideError();
            hideResults();
            
            try {
                const response = await fetch(`/api/analysis/${symbol}`);
                const result = await response.json();
                
                if (result.success) {
                    displayResults(result.data);
                } else {
                    showError('Analysis failed: ' + result.message);
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                showLoading(false);
            }
        }
        
        function displayResults(data) {
            displayStockInfo(data);
            displayChart(data.price_data);
            displayIndicators(data.indicators);
            displayTrend(data.trend, data.current_price);
            showResults();
        }
        
        function displayStockInfo(data) {
            const container = document.getElementById('stockInfo');
            container.innerHTML = `
                <h2>${data.symbol}</h2>
                <p>Current Price: <strong>${data.current_price.toFixed(2)}</strong></p>
                <p>Data Points: ${data.data_count} records</p>
            `;
            container.style.display = 'block';
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
                    scales: {
                        y: { 
                            beginAtZero: false,
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        }
                    },
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
                { label: 'SMA(20)', value: indicators.sma_20, unit: '' },
                { label: 'SMA(50)', value: indicators.sma_50, unit: '' },
                { label: 'RSI', value: indicators.rsi, unit: '' },
                { label: 'MACD', value: indicators.macd, unit: '' },
                { label: 'MACD Signal', value: indicators.macd_signal, unit: '' },
                { label: 'Bollinger Upper', value: indicators.bollinger_upper, unit: '' },
                { label: 'Bollinger Middle', value: indicators.bollinger_middle, unit: '' },
                { label: 'Bollinger Lower', value: indicators.bollinger_lower, unit: '' }
            ];
            
            indicatorItems.forEach(item => {
                if (item.value !== null && item.value !== undefined) {
                    const div = document.createElement('div');
                    div.className = 'indicator-item';
                    div.innerHTML = `
                        <span class="indicator-label">${item.label}</span>
                        <span class="indicator-value">${item.value.toFixed(2)}${item.unit}</span>
                    `;
                    container.appendChild(div);
                }
            });
        }
        
        function displayTrend(trend, currentPrice) {
            const container = document.getElementById('trendAnalysis');
            const trendText = {
                'uptrend': '📈 Uptrend',
                'downtrend': '📉 Downtrend',
                'sideways': '↔️ Sideways',
                'insufficient_data': '❓ Insufficient Data'
            };
            
            container.innerHTML = `
                <div class="trend ${trend}">
                    <div>${trendText[trend] || trend}</div>
                </div>
            `;
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
        
        function showResults() {
            document.getElementById('results').style.display = 'block';
        }
        
        function hideResults() {
            document.getElementById('results').style.display = 'none';
        }
        
        // Enter key search
        document.getElementById('stockInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeStock();
            }
        });
        
        // Page load completion
        window.addEventListener('load', function() {
            console.log('Personal Quant Trading System loaded');
            console.log('Supports any HK stock code input, e.g., 0700.HK, 2800.HK, 1299.HK');
        });
    </script>
</body>
</html>
    '''

@app.get('/api/analysis/{symbol}')
def analyze_stock(symbol: str):
    try:
        # Get stock data
        url = 'http://18.180.162.113:9191/inst/getInst'
        params = {'symbol': symbol.lower(), 'duration': 1825}
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return {'success': False, 'message': f'API call failed: {response.status_code}'}
        
        data = response.json()
        
        if 'data' not in data or not isinstance(data['data'], dict):
            return {'success': False, 'message': 'Invalid data format'}
        
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
        
        if len(formatted_data) < 20:
            return {'success': False, 'message': 'Insufficient data for analysis'}
        
        # Calculate technical indicators
        df = pd.DataFrame(formatted_data)
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
        
        # Trend analysis
        trend = 'insufficient_data'
        if len(close) >= 50:
            sma_20 = close.rolling(window=20).mean()
            sma_50 = close.rolling(window=50).mean()
            current_price = close.iloc[-1]
            sma_20_current = sma_20.iloc[-1]
            sma_50_current = sma_50.iloc[-1]
            
            if current_price > sma_20_current > sma_50_current:
                trend = 'uptrend'
            elif current_price < sma_20_current < sma_50_current:
                trend = 'downtrend'
            else:
                trend = 'sideways'
        
        return {
            'success': True,
            'data': {
                'symbol': symbol,
                'price_data': formatted_data,
                'indicators': indicators,
                'trend': trend,
                'current_price': float(close.iloc[-1]),
                'data_count': len(formatted_data)
            }
        }
        
    except Exception as e:
        return {'success': False, 'message': f'Analysis failed: {str(e)}'}

if __name__ == "__main__":
    print("Starting Personal Quant Trading System...")
    print("Access: http://localhost:8001")
    print("Supports any HK stock code input")
    print("Examples: 0700.HK, 2800.HK, 1299.HK, 0941.HK, 0388.HK")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
