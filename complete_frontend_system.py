"""
完整前端量化交易系统 - 包含所有核心功能模块
技术分析 · 策略回测 · 风险评估 · 市场情绪
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import json
import time
import logging
import os
import re
from typing import Dict, List, Any, Optional

# 安全配置
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8001", 
    "http://127.0.0.1:8001",
    "http://127.0.0.1:3000"
]

API_BASE_URL = os.getenv('STOCK_API_URL', 'http://18.180.162.113:9191')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Complete Quant Trading System",
    description="Complete quantitative trading analysis platform with all features",
    version="7.2.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 输入验证函数
def validate_symbol(symbol: str) -> bool:
    """验证股票代码格式"""
    pattern = r'^[A-Z0-9\.]+$'
    return bool(re.match(pattern, symbol.upper()))

def sanitize_input(input_text: str) -> str:
    """清理输入内容"""
    result = re.sub(r'[<>\"\';\\\\]', '', input_text.strip())
    return result

# 数据获取函数
@lru_cache(maxsize=128)
def fetch_stock_data(symbol: str) -> Dict:
    """获取股票数据"""
    try:
        url = f"{API_BASE_URL}/api/stocks/{symbol}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return {"error": str(e)}

def calculate_technical_indicators(data: List[Dict]) -> Dict:
    """计算技术指标"""
    if not data or len(data) < 20:
        return {"error": "数据不足，无法计算技术指标"}
    
    try:
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        # 计算技术指标
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()
        
        # RSI计算
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD计算
        df['macd'] = df['ema_12'] - df['ema_26']
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # 布林带
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        
        # 获取最新数据
        latest = df.iloc[-1]
        
        return {
            "sma_20": round(latest['sma_20'], 2),
            "sma_50": round(latest['sma_50'], 2),
            "ema_12": round(latest['ema_12'], 2),
            "ema_26": round(latest['ema_26'], 2),
            "rsi": round(latest['rsi'], 2),
            "macd": round(latest['macd'], 4),
            "macd_signal": round(latest['macd_signal'], 4),
            "macd_histogram": round(latest['macd_histogram'], 4),
            "bb_upper": round(latest['bb_upper'], 2),
            "bb_middle": round(latest['bb_middle'], 2),
            "bb_lower": round(latest['bb_lower'], 2),
            "current_price": round(latest['close'], 2),
            "volume": int(latest['volume'])
        }
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return {"error": str(e)}

def backtest_strategy(data: List[Dict], strategy: str = "SMA_CROSSOVER") -> Dict:
    """策略回测"""
    if not data or len(data) < 50:
        return {"error": "数据不足，无法进行回测"}
    
    try:
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        df['date'] = pd.to_datetime(df['date'])
        
        # 计算移动平均线
        df['sma_short'] = df['close'].rolling(window=10).mean()
        df['sma_long'] = df['close'].rolling(window=30).mean()
        
        # 生成交易信号
        df['signal'] = 0
        df.loc[df['sma_short'] > df['sma_long'], 'signal'] = 1  # 买入
        df.loc[df['sma_short'] < df['sma_long'], 'signal'] = -1  # 卖出
        
        # 计算收益
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']
        
        # 计算指标
        total_return = (1 + df['strategy_returns']).prod() - 1
        volatility = df['strategy_returns'].std() * np.sqrt(252)
        sharpe_ratio = df['strategy_returns'].mean() / df['strategy_returns'].std() * np.sqrt(252) if df['strategy_returns'].std() != 0 else 0
        
        # 最大回撤
        cumulative = (1 + df['strategy_returns']).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        return {
            "strategy": strategy,
            "total_return": round(total_return * 100, 2),
            "volatility": round(volatility * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "total_trades": int((df['signal'].diff() != 0).sum()),
            "win_rate": round((df['strategy_returns'] > 0).mean() * 100, 2)
        }
    except Exception as e:
        logger.error(f"Error in backtesting: {e}")
        return {"error": str(e)}

def assess_risk(data: List[Dict]) -> Dict:
    """风险评估"""
    if not data or len(data) < 30:
        return {"error": "数据不足，无法进行风险评估"}
    
    try:
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        df['returns'] = df['close'].pct_change()
        
        # 计算风险指标
        volatility = df['returns'].std() * np.sqrt(252)
        var_95 = np.percentile(df['returns'], 5)
        var_99 = np.percentile(df['returns'], 1)
        
        # 风险等级
        if volatility < 0.15:
            risk_level = "LOW"
            risk_score = 3
        elif volatility < 0.25:
            risk_level = "MEDIUM"
            risk_score = 6
        else:
            risk_level = "HIGH"
            risk_score = 9
        
        return {
            "volatility": round(volatility * 100, 2),
            "var_95": round(var_95 * 100, 2),
            "var_99": round(var_99 * 100, 2),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "recommendation": "保守投资" if risk_level == "LOW" else "适度投资" if risk_level == "MEDIUM" else "谨慎投资"
        }
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        return {"error": str(e)}

def analyze_market_sentiment(data: List[Dict]) -> Dict:
    """市场情绪分析"""
    if not data or len(data) < 10:
        return {"error": "数据不足，无法进行情绪分析"}
    
    try:
        df = pd.DataFrame(data)
        df['close'] = pd.to_numeric(df['close'])
        
        # 计算价格变化
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
        
        # 情绪分数 (0-100)
        if price_change > 0.05:
            sentiment_score = 80
            sentiment_level = "非常乐观"
        elif price_change > 0.02:
            sentiment_score = 65
            sentiment_level = "乐观"
        elif price_change > -0.02:
            sentiment_score = 50
            sentiment_level = "中性"
        elif price_change > -0.05:
            sentiment_score = 35
            sentiment_level = "悲观"
        else:
            sentiment_score = 20
            sentiment_level = "非常悲观"
        
        return {
            "sentiment_score": sentiment_score,
            "sentiment_level": sentiment_level,
            "price_change": round(price_change * 100, 2),
            "trend_strength": "强" if abs(price_change) > 0.03 else "中" if abs(price_change) > 0.01 else "弱"
        }
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {"error": str(e)}

# API端点
@app.get('/', response_class=HTMLResponse)
def read_root():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>完整量化交易系统 v7.2</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container { 
            max-width: 1400px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .header { 
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 { 
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        
        .tab {
            flex: 1;
            padding: 15px 20px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #6c757d;
            transition: all 0.3s;
            border-bottom: 3px solid transparent;
        }
        
        .tab.active {
            color: #667eea;
            background: white;
            border-bottom-color: #667eea;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .tab-content {
            display: none;
            padding: 30px;
            min-height: 500px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .search-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .search-box { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 20px;
            align-items: center;
        }
        
        .search-box input { 
            flex: 1;
            padding: 12px 15px; 
            border: 2px solid #e1e8ed; 
            border-radius: 8px; 
            font-size: 16px;
        }
        
        .search-box input:focus { 
            outline: none; 
            border-color: #667eea; 
        }
        
        .search-box button { 
            padding: 12px 25px; 
            background: linear-gradient(45deg, #667eea, #764ba2); 
            color: white; 
            border: none; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: bold;
        }
        
        .search-box button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .result-card {
            background: white;
            border: 1px solid #e1e8ed;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .result-card h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 8px 0;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: #6c757d;
        }
        
        .metric-value {
            font-weight: bold;
            color: #2c3e50;
        }
        
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #6c757d; }
        
        .chart-container {
            margin-top: 20px;
            height: 300px;
            position: relative;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-success { background: #28a745; }
        .status-warning { background: #ffc107; }
        .status-danger { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 完整量化交易系统 v7.2</h1>
            <p>技术分析 · 策略回测 · 风险评估 · 市场情绪 · 完整功能</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('technical')">📊 技术分析</button>
            <button class="tab" onclick="switchTab('backtest')">🔄 策略回测</button>
            <button class="tab" onclick="switchTab('risk')">⚠️ 风险评估</button>
            <button class="tab" onclick="switchTab('sentiment')">😊 市场情绪</button>
        </div>
        
        <!-- 技术分析标签页 -->
        <div id="technical" class="tab-content active">
            <div class="search-section">
                <div class="search-box">
                    <input type="text" id="symbolInput" placeholder="输入股票代码 (如: 0700.HK, 2800.HK)" value="0700.HK">
                    <button onclick="analyzeStock()">🔍 技术分析</button>
                </div>
            </div>
            <div id="technicalResults"></div>
        </div>
        
        <!-- 策略回测标签页 -->
        <div id="backtest" class="tab-content">
            <div class="search-section">
                <div class="search-box">
                    <input type="text" id="backtestSymbol" placeholder="输入股票代码进行回测" value="0700.HK">
                    <button onclick="runBacktest()">🔄 开始回测</button>
                </div>
            </div>
            <div id="backtestResults"></div>
        </div>
        
        <!-- 风险评估标签页 -->
        <div id="risk" class="tab-content">
            <div class="search-section">
                <div class="search-box">
                    <input type="text" id="riskSymbol" placeholder="输入股票代码进行风险评估" value="0700.HK">
                    <button onclick="assessRisk()">⚠️ 风险评估</button>
                </div>
            </div>
            <div id="riskResults"></div>
        </div>
        
        <!-- 市场情绪标签页 -->
        <div id="sentiment" class="tab-content">
            <div class="search-section">
                <div class="search-box">
                    <input type="text" id="sentimentSymbol" placeholder="输入股票代码进行情绪分析" value="0700.HK">
                    <button onclick="analyzeSentiment()">😊 情绪分析</button>
                </div>
            </div>
            <div id="sentimentResults"></div>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            // 隐藏所有标签页内容
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 移除所有标签的激活状态
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // 显示选中的标签页
            document.getElementById(tabName).classList.add('active');
            
            // 激活对应的标签按钮
            event.target.classList.add('active');
        }
        
        async function analyzeStock() {
            const symbol = document.getElementById('symbolInput').value.trim();
            if (!symbol) {
                alert('请输入股票代码');
                return;
            }
            
            const resultsDiv = document.getElementById('technicalResults');
            resultsDiv.innerHTML = '<div class="loading">⏳ 正在分析中...</div>';
            
            try {
                const response = await fetch(`/api/analysis/${symbol}`);
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">❌ 分析失败: ${data.error}</div>`;
                    return;
                }
                
                resultsDiv.innerHTML = `
                    <div class="success">✅ 技术分析完成</div>
                    <div class="results-grid">
                        <div class="result-card">
                            <h3>📈 移动平均线</h3>
                            <div class="metric">
                                <span class="metric-label">SMA 20日</span>
                                <span class="metric-value">${data.sma_20 || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">SMA 50日</span>
                                <span class="metric-value">${data.sma_50 || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">EMA 12日</span>
                                <span class="metric-value">${data.ema_12 || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">EMA 26日</span>
                                <span class="metric-value">${data.ema_26 || 'N/A'}</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>📊 技术指标</h3>
                            <div class="metric">
                                <span class="metric-label">RSI (14日)</span>
                                <span class="metric-value ${data.rsi > 70 ? 'negative' : data.rsi < 30 ? 'positive' : 'neutral'}">${data.rsi || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">MACD</span>
                                <span class="metric-value">${data.macd || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">MACD信号线</span>
                                <span class="metric-value">${data.macd_signal || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">MACD柱状图</span>
                                <span class="metric-value ${data.macd_histogram > 0 ? 'positive' : 'negative'}">${data.macd_histogram || 'N/A'}</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>📉 布林带</h3>
                            <div class="metric">
                                <span class="metric-label">上轨</span>
                                <span class="metric-value">${data.bb_upper || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">中轨</span>
                                <span class="metric-value">${data.bb_middle || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">下轨</span>
                                <span class="metric-value">${data.bb_lower || 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">当前价格</span>
                                <span class="metric-value positive">${data.current_price || 'N/A'}</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>📊 交易信息</h3>
                            <div class="metric">
                                <span class="metric-label">成交量</span>
                                <span class="metric-value">${data.volume ? data.volume.toLocaleString() : 'N/A'}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">分析时间</span>
                                <span class="metric-value">${new Date().toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                `;
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">❌ 请求失败: ${error.message}</div>`;
            }
        }
        
        async function runBacktest() {
            const symbol = document.getElementById('backtestSymbol').value.trim();
            if (!symbol) {
                alert('请输入股票代码');
                return;
            }
            
            const resultsDiv = document.getElementById('backtestResults');
            resultsDiv.innerHTML = '<div class="loading">⏳ 正在回测中...</div>';
            
            try {
                const response = await fetch(`/api/backtest/${symbol}`);
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">❌ 回测失败: ${data.error}</div>`;
                    return;
                }
                
                resultsDiv.innerHTML = `
                    <div class="success">✅ 策略回测完成</div>
                    <div class="results-grid">
                        <div class="result-card">
                            <h3>📈 收益指标</h3>
                            <div class="metric">
                                <span class="metric-label">总收益率</span>
                                <span class="metric-value ${data.total_return > 0 ? 'positive' : 'negative'}">${data.total_return}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">年化波动率</span>
                                <span class="metric-value">${data.volatility}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">夏普比率</span>
                                <span class="metric-value ${data.sharpe_ratio > 1 ? 'positive' : data.sharpe_ratio > 0 ? 'neutral' : 'negative'}">${data.sharpe_ratio}</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>⚠️ 风险指标</h3>
                            <div class="metric">
                                <span class="metric-label">最大回撤</span>
                                <span class="metric-value negative">${data.max_drawdown}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">总交易次数</span>
                                <span class="metric-value">${data.total_trades}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">胜率</span>
                                <span class="metric-value ${data.win_rate > 50 ? 'positive' : 'negative'}">${data.win_rate}%</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>📊 策略信息</h3>
                            <div class="metric">
                                <span class="metric-label">策略类型</span>
                                <span class="metric-value">${data.strategy}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">回测时间</span>
                                <span class="metric-value">${new Date().toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                `;
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">❌ 请求失败: ${error.message}</div>`;
            }
        }
        
        async function assessRisk() {
            const symbol = document.getElementById('riskSymbol').value.trim();
            if (!symbol) {
                alert('请输入股票代码');
                return;
            }
            
            const resultsDiv = document.getElementById('riskResults');
            resultsDiv.innerHTML = '<div class="loading">⏳ 正在评估风险中...</div>';
            
            try {
                const response = await fetch(`/api/risk/${symbol}`);
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">❌ 风险评估失败: ${data.error}</div>`;
                    return;
                }
                
                const riskColor = data.risk_level === 'LOW' ? 'positive' : data.risk_level === 'MEDIUM' ? 'neutral' : 'negative';
                const riskIcon = data.risk_level === 'LOW' ? '🟢' : data.risk_level === 'MEDIUM' ? '🟡' : '🔴';
                
                resultsDiv.innerHTML = `
                    <div class="success">✅ 风险评估完成</div>
                    <div class="results-grid">
                        <div class="result-card">
                            <h3>⚠️ 风险等级</h3>
                            <div class="metric">
                                <span class="metric-label">风险等级</span>
                                <span class="metric-value ${riskColor}">${riskIcon} ${data.risk_level}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">风险评分</span>
                                <span class="metric-value ${riskColor}">${data.risk_score}/10</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">投资建议</span>
                                <span class="metric-value">${data.recommendation}</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>📊 风险指标</h3>
                            <div class="metric">
                                <span class="metric-label">年化波动率</span>
                                <span class="metric-value">${data.volatility}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">VaR (95%)</span>
                                <span class="metric-value negative">${data.var_95}%</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">VaR (99%)</span>
                                <span class="metric-value negative">${data.var_99}%</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>💡 风险说明</h3>
                            <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 14px; line-height: 1.6;">
                                <p><strong>VaR (Value at Risk)</strong> 表示在给定置信度下，投资组合在特定时间内的最大预期损失。</p>
                                <p><strong>波动率</strong> 衡量价格变动的剧烈程度，数值越高风险越大。</p>
                                <p><strong>风险等级</strong> 基于历史数据计算，仅供参考，不构成投资建议。</p>
                            </div>
                        </div>
                    </div>
                `;
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">❌ 请求失败: ${error.message}</div>`;
            }
        }
        
        async function analyzeSentiment() {
            const symbol = document.getElementById('sentimentSymbol').value.trim();
            if (!symbol) {
                alert('请输入股票代码');
                return;
            }
            
            const resultsDiv = document.getElementById('sentimentResults');
            resultsDiv.innerHTML = '<div class="loading">⏳ 正在分析市场情绪中...</div>';
            
            try {
                const response = await fetch(`/api/sentiment/${symbol}`);
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">❌ 情绪分析失败: ${data.error}</div>`;
                    return;
                }
                
                const sentimentColor = data.sentiment_score > 60 ? 'positive' : data.sentiment_score < 40 ? 'negative' : 'neutral';
                const sentimentIcon = data.sentiment_score > 60 ? '😊' : data.sentiment_score < 40 ? '😟' : '😐';
                
                resultsDiv.innerHTML = `
                    <div class="success">✅ 市场情绪分析完成</div>
                    <div class="results-grid">
                        <div class="result-card">
                            <h3>😊 情绪指标</h3>
                            <div class="metric">
                                <span class="metric-label">情绪分数</span>
                                <span class="metric-value ${sentimentColor}">${sentimentIcon} ${data.sentiment_score}/100</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">情绪等级</span>
                                <span class="metric-value ${sentimentColor}">${data.sentiment_level}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">价格变化</span>
                                <span class="metric-value ${data.price_change > 0 ? 'positive' : 'negative'}">${data.price_change}%</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>📈 趋势分析</h3>
                            <div class="metric">
                                <span class="metric-label">趋势强度</span>
                                <span class="metric-value">${data.trend_strength}</span>
                            </div>
                            <div class="metric">
                                <span class="metric-label">分析时间</span>
                                <span class="metric-value">${new Date().toLocaleString()}</span>
                            </div>
                        </div>
                        
                        <div class="result-card">
                            <h3>💡 情绪说明</h3>
                            <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 14px; line-height: 1.6;">
                                <p><strong>情绪分数</strong> 基于价格变化计算，分数越高表示市场越乐观。</p>
                                <p><strong>趋势强度</strong> 反映价格变动的持续性，强趋势通常伴随高情绪分数。</p>
                                <p><strong>投资提示</strong> 情绪分析仅供参考，请结合其他指标综合判断。</p>
                            </div>
                        </div>
                    </div>
                `;
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">❌ 请求失败: ${error.message}</div>`;
            }
        }
        
        // 页面加载完成后自动分析默认股票
        window.onload = function() {
            analyzeStock();
        };
    </script>
</body>
</html>
    '''

# API端点
@app.get('/api/analysis/{symbol}')
async def get_analysis(symbol: str):
    """获取技术分析"""
    if not validate_symbol(symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format")
    
    symbol = sanitize_input(symbol)
    data = fetch_stock_data(symbol)
    
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    
    if "data" not in data:
        raise HTTPException(status_code=404, detail="No data found")
    
    indicators = calculate_technical_indicators(data["data"])
    return indicators

@app.get('/api/backtest/{symbol}')
async def get_backtest(symbol: str):
    """获取策略回测"""
    if not validate_symbol(symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format")
    
    symbol = sanitize_input(symbol)
    data = fetch_stock_data(symbol)
    
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    
    if "data" not in data:
        raise HTTPException(status_code=404, detail="No data found")
    
    backtest_result = backtest_strategy(data["data"])
    return backtest_result

@app.get('/api/risk/{symbol}')
async def get_risk_assessment(symbol: str):
    """获取风险评估"""
    if not validate_symbol(symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format")
    
    symbol = sanitize_input(symbol)
    data = fetch_stock_data(symbol)
    
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    
    if "data" not in data:
        raise HTTPException(status_code=404, detail="No data found")
    
    risk_result = assess_risk(data["data"])
    return risk_result

@app.get('/api/sentiment/{symbol}')
async def get_sentiment_analysis(symbol: str):
    """获取市场情绪分析"""
    if not validate_symbol(symbol):
        raise HTTPException(status_code=400, detail="Invalid symbol format")
    
    symbol = sanitize_input(symbol)
    data = fetch_stock_data(symbol)
    
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    
    if "data" not in data:
        raise HTTPException(status_code=404, detail="No data found")
    
    sentiment_result = analyze_market_sentiment(data["data"])
    return sentiment_result

@app.get('/api/health')
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "7.2.0",
        "features": ["technical_analysis", "backtesting", "risk_assessment", "market_sentiment"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info("启动完整量化交易系统 v7.2")
    uvicorn.run(app, host="0.0.0.0", port=8001)
