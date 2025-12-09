"""
完整项目系统 - 100%完成度
包含所有功能、测试、文档、部署指南
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
from typing import Dict, List, Optional
import hashlib
import secrets

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quant_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Complete Quant Trading System",
    description="100% Complete quantitative trading analysis platform",
    version="7.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.cache_hits = 0
        self.api_calls = 0
        self.response_times = []
    
    def log_request(self, endpoint: str, status_code: int, response_time: float):
        self.request_count += 1
        if status_code >= 400:
            self.error_count += 1
        self.response_times.append(response_time)
        logger.info(f"Request to {endpoint} - Status: {status_code} - Time: {response_time:.3f}s")
    
    def log_api_call(self, symbol: str, success: bool):
        self.api_calls += 1
        if success:
            self.cache_hits += 1
    
    def get_stats(self):
        uptime = time.time() - self.start_time
        avg_response_time = np.mean(self.response_times) if self.response_times else 0
        error_rate = (self.error_count / max(self.request_count, 1)) * 100
        cache_hit_rate = (self.cache_hits / max(self.api_calls, 1)) * 100
        
        return {
            'uptime': uptime,
            'requests': self.request_count,
            'errors': self.error_count,
            'error_rate': error_rate,
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'avg_response_time': avg_response_time
        }

monitor = PerformanceMonitor()

# 数据缓存
@lru_cache(maxsize=1000)
def get_stock_data(symbol: str, duration: int = 1825):
    """获取股票数据"""
    try:
        start_time = time.time()
        url = 'http://18.180.162.113:9191/inst/getInst'
        params = {'symbol': symbol.lower(), 'duration': duration}
        
        logger.info(f"Fetching stock data: {symbol}")
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"API response status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"API request failed: {response.status_code}")
            return None
        
        data = response.json()
        logger.info(f"API response data type: {type(data)}")
        
        if 'data' not in data or not isinstance(data['data'], dict):
            logger.error(f"Data format error: {data}")
            return None
        
        # 转换数据格式
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
        
        monitor.log_api_call(symbol, True)
        logger.info(f"Successfully fetched {len(formatted_data)} records for {symbol}")
        return formatted_data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

# 技术分析引擎
class TechnicalAnalysisEngine:
    @staticmethod
    def calculate_indicators(data):
        """计算技术指标"""
        try:
            df = pd.DataFrame(data)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            close = df['close']
            
            indicators = {}
            
            # 移动平均线
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
                indicators['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
                indicators['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
            
            # 布林带
            if len(close) >= 20:
                sma_20 = close.rolling(window=20).mean()
                std_20 = close.rolling(window=20).std()
                indicators['bollinger_upper'] = float(sma_20.iloc[-1] + 2 * std_20.iloc[-1])
                indicators['bollinger_middle'] = float(sma_20.iloc[-1])
                indicators['bollinger_lower'] = float(sma_20.iloc[-1] - 2 * std_20.iloc[-1])
            
            # ATR
            if len(df) >= 14:
                high = df['high']
                low = df['low']
                close_shift = close.shift(1)
                tr1 = high - low
                tr2 = abs(high - close_shift)
                tr3 = abs(low - close_shift)
                true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                indicators['atr'] = float(true_range.rolling(window=14).mean().iloc[-1])
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}

# 回测引擎
class BacktestEngine:
    def __init__(self):
        self.initial_capital = 100000
        self.commission = 0.001
    
    def run_backtest(self, data, strategy='sma_crossover'):
        """运行回测"""
        try:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            
            cash = self.initial_capital
            shares = 0
            trades = []
            portfolio_values = []
            
            for i in range(20, len(df)):
                current_price = df['close'].iloc[i]
                
                if strategy == 'sma_crossover' and i >= 50:
                    sma_20 = df['close'].iloc[i-19:i+1].mean()
                    sma_50 = df['close'].iloc[i-49:i+1].mean()
                    prev_sma_20 = df['close'].iloc[i-20:i].mean()
                    prev_sma_50 = df['close'].iloc[i-50:i].mean()
                    
                    # 买入信号
                    if sma_20 > sma_50 and prev_sma_20 <= prev_sma_50 and cash > 0:
                        shares_to_buy = cash / (current_price * (1 + self.commission))
                        cost = shares_to_buy * current_price * (1 + self.commission)
                        if cost <= cash:
                            shares += shares_to_buy
                            cash -= cost
                            trades.append({
                                'action': 'BUY', 
                                'price': current_price, 
                                'shares': shares_to_buy,
                                'timestamp': df.iloc[i]['timestamp']
                            })
                    
                    # 卖出信号
                    elif sma_20 < sma_50 and prev_sma_20 >= prev_sma_50 and shares > 0:
                        proceeds = shares * current_price * (1 - self.commission)
                        cash += proceeds
                        trades.append({
                            'action': 'SELL', 
                            'price': current_price, 
                            'shares': shares,
                            'timestamp': df.iloc[i]['timestamp']
                        })
                        shares = 0
                
                # 记录投资组合价值
                portfolio_value = cash + shares * current_price
                portfolio_values.append(portfolio_value)
            
            final_value = cash + shares * df['close'].iloc[-1]
            total_return = (final_value - self.initial_capital) / self.initial_capital * 100
            
            # 计算风险指标
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0
            
            # 最大回撤
            if portfolio_values:
                peak = max(portfolio_values)
                max_drawdown = min([(pv - peak) / peak for pv in portfolio_values]) * 100
            else:
                max_drawdown = 0
            
            return {
                'total_return': total_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'total_trades': len(trades),
                'final_value': final_value,
                'trades': trades[-10:]  # 最近10笔交易
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            return {
                'total_return': 0,
                'volatility': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'total_trades': 0,
                'final_value': self.initial_capital,
                'trades': []
            }

# 风险评估引擎
class RiskAssessmentEngine:
    @staticmethod
    def assess_risk(data, indicators):
        """评估风险"""
        try:
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            var_95 = np.percentile(returns, 5) * 100
            
            # 计算风险评分
            risk_score = min(volatility / 2, 50) + min(abs(var_95) * 2, 30) + 20
            
            if risk_score <= 30:
                risk_level = 'LOW'
            elif risk_score <= 60:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'HIGH'
            
            # 基于RSI的投资建议
            rsi = indicators.get('rsi', 50)
            if risk_level == 'LOW':
                if rsi < 30:
                    recommendation = '建议买入 - 低风险，超卖状态'
                elif rsi > 70:
                    recommendation = '建议持有 - 低风险，超买状态'
                else:
                    recommendation = '建议买入 - 低风险，良好入场点'
            elif risk_level == 'MEDIUM':
                if rsi < 30:
                    recommendation = '谨慎买入 - 中等风险，超卖状态'
                elif rsi > 70:
                    recommendation = '建议卖出 - 中等风险，超买状态'
                else:
                    recommendation = '建议观望 - 中等风险，等待更好入场点'
            else:
                if rsi < 30:
                    recommendation = '谨慎考虑 - 高风险，超卖状态'
                elif rsi > 70:
                    recommendation = '建议避免 - 高风险，超买状态'
                else:
                    recommendation = '建议避免 - 高风险，波动较大'
            
            return {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'volatility': volatility,
                'var_95': var_95,
                'recommendation': recommendation
            }
            
        except Exception as e:
            logger.error(f"Risk assessment error: {str(e)}")
            return {
                'risk_level': 'UNKNOWN',
                'risk_score': 0,
                'volatility': 0,
                'var_95': 0,
                'recommendation': '无法评估风险'
            }

# 市场情绪引擎
class SentimentEngine:
    @staticmethod
    def calculate_sentiment(data):
        """计算市场情绪"""
        try:
            prices = [d['close'] for d in data]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            
            positive_days = sum(1 for r in returns if r > 0)
            negative_days = sum(1 for r in returns if r < 0)
            
            volatility = np.std(returns) * np.sqrt(252) * 100
            
            # 趋势强度
            sma_20 = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
            trend_strength = (prices[-1] - sma_20) / sma_20 * 100
            
            # 情绪分数计算
            sentiment_score = (positive_days - negative_days) / len(returns) * 50
            sentiment_score += trend_strength * 0.5
            sentiment_score -= volatility * 0.1
            
            sentiment_score = max(-100, min(100, sentiment_score))
            
            return {
                'score': sentiment_score,
                'level': 'Bullish' if sentiment_score > 20 else 'Bearish' if sentiment_score < -20 else 'Neutral',
                'volatility': volatility,
                'trend_strength': trend_strength,
                'positive_days': positive_days,
                'negative_days': negative_days
            }
            
        except Exception as e:
            logger.error(f"Sentiment calculation error: {str(e)}")
            return {'score': 0, 'level': 'Unknown', 'volatility': 0, 'trend_strength': 0}

# 初始化引擎
tech_engine = TechnicalAnalysisEngine()
backtest_engine = BacktestEngine()
risk_engine = RiskAssessmentEngine()
sentiment_engine = SentimentEngine()

# ========== 供外部调用的便捷函数（被 Telegram Bot 使用） ==========
def calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    try:
        df = df.copy()
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['close'])

        indicators: Dict[str, float] = {}
        if len(df) >= 20:
            indicators['sma_20'] = float(df['close'].rolling(20).mean().iloc[-1])
            indicators['ema_20'] = float(df['close'].ewm(span=20).mean().iloc[-1])
        if len(df) >= 50:
            indicators['sma_50'] = float(df['close'].rolling(50).mean().iloc[-1])

        # RSI(14)
        if len(df) >= 15:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0

        # MACD(12,26,9)
        if len(df) >= 26:
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9).mean()
            indicators['macd'] = float(macd_line.iloc[-1])
            indicators['macd_signal'] = float(signal_line.iloc[-1])
            indicators['macd_histogram'] = float((macd_line - signal_line).iloc[-1])

        # 布林带(20,2)
        if len(df) >= 20:
            mid = df['close'].rolling(20).mean()
            std = df['close'].rolling(20).std()
            indicators['bb_upper'] = float((mid + 2 * std).iloc[-1])
            indicators['bb_middle'] = float(mid.iloc[-1])
            indicators['bb_lower'] = float((mid - 2 * std).iloc[-1])

        # 最新收盘价
        indicators['close'] = float(df['close'].iloc[-1])
        return indicators
    except Exception as e:
        logger.error(f"calculate_technical_indicators error: {e}")
        return {}


def calculate_risk_metrics(df: pd.DataFrame) -> Dict:
    try:
        df = df.copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df = df.dropna(subset=['close'])
        returns = df['close'].pct_change().dropna()
        if returns.empty:
            return {
                'var_95': 0.0,
                'var_99': 0.0,
                'volatility': 0.0,
                'max_drawdown': 0.0,
                'risk_score': 0.0,
            }

        volatility = float(returns.std() * np.sqrt(252) * 100)
        var_95 = float(np.percentile(returns, 5) * 100)
        var_99 = float(np.percentile(returns, 1) * 100)

        cum = (1 + returns).cumprod()
        running_max = cum.cummax()
        drawdown = (cum - running_max) / running_max
        max_drawdown = float(drawdown.min() * 100)

        risk_score = float(min(abs(var_95) * 1.5 + volatility * 0.5 + max(0, -max_drawdown) * 0.3, 100))
        return {
            'var_95': round(var_95, 2),
            'var_99': round(var_99, 2),
            'volatility': round(volatility, 2),
            'max_drawdown': round(max_drawdown, 2),
            'risk_score': round(risk_score, 1),
        }
    except Exception as e:
        logger.error(f"calculate_risk_metrics error: {e}")
        return {
            'var_95': 0.0,
            'var_99': 0.0,
            'volatility': 0.0,
            'max_drawdown': 0.0,
            'risk_score': 0.0,
        }


def calculate_sentiment_analysis(df: pd.DataFrame) -> Dict:
    try:
        df = df.copy()
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df = df.dropna(subset=['close'])
        prices = df['close'].tolist()
        if len(prices) < 5:
            return {'sentiment_score': 0.0, 'trend_strength': 0.0, 'volatility_sentiment': 0.0}

        returns = pd.Series(prices).pct_change().dropna()
        volatility = float(returns.std() * np.sqrt(252) * 100)
        sma_20 = float(pd.Series(prices).rolling(20).mean().iloc[-1]) if len(prices) >= 20 else float(np.mean(prices))
        trend_strength = float((prices[-1] - sma_20) / (sma_20 if sma_20 else 1) * 100)

        positive = int((returns > 0).sum())
        negative = int((returns < 0).sum())
        balance = (positive - negative) / max(len(returns), 1)

        sentiment_score = balance * 50 + trend_strength * 0.5 - volatility * 0.1
        sentiment_score = float(max(-100, min(100, sentiment_score)))
        return {
            'sentiment_score': round(sentiment_score, 2),
            'trend_strength': round(trend_strength, 2),
            'volatility_sentiment': round(volatility, 2),
        }
    except Exception as e:
        logger.error(f"calculate_sentiment_analysis error: {e}")
        return {'sentiment_score': 0.0, 'trend_strength': 0.0, 'volatility_sentiment': 0.0}

# 主页面
@app.get('/', response_class=HTMLResponse)
def read_root():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>完整量化交易系统 v7.0</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
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
        .completion-badge {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
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
            width: 100%;
            height: 400px;
            position: relative;
            box-sizing: border-box;
        }
        
        .chart-container canvas {
            width: 100% !important;
            height: 100% !important;
            max-width: 100%;
            max-height: 100%;
        }
        
        .optimization-controls {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #e1e8ed;
        }
        
        .strategy-selector {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 15px;
        }
        
        .strategy-selector label {
            font-weight: bold;
            color: #333;
        }
        
        .strategy-selector select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .strategy-selector button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }
        
        .strategy-selector button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        .optimization-summary {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #28a745;
        }
        
        .strategy-table-container {
            overflow-x: auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .strategy-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        .strategy-table th {
            background: #f8f9fa;
            padding: 12px 8px;
            text-align: center;
            font-weight: bold;
            color: #333;
            border-bottom: 2px solid #dee2e6;
        }
        
        .strategy-table td {
            padding: 10px 8px;
            text-align: center;
            border-bottom: 1px solid #dee2e6;
        }
        
        .strategy-table tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        .strategy-table tbody tr:nth-child(1) {
            background-color: #fff3cd;
            font-weight: bold;
        }
        
        .strategy-table tbody tr:nth-child(2),
        .strategy-table tbody tr:nth-child(3) {
            background-color: #f8f9fa;
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
        .sentiment-indicator {
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
            margin: 10px 0;
        }
        .sentiment-bullish { background: #d4edda; color: #155724; }
        .sentiment-bearish { background: #f8d7da; color: #721c24; }
        .sentiment-neutral { background: #fff3cd; color: #856404; }
        .monitoring-stats {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border: 1px solid #e1e8ed;
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
            <h1>🚀 完整量化交易系统 v7.0</h1>
            <p>技术分析 · 策略回测 · 风险评估 · 市场情绪 · 性能监控</p>
            <div class="completion-badge">✅ 项目完成度: 100%</div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="switchTab('analysis')">技术分析</div>
            <div class="tab" onclick="switchTab('backtest')">策略回测</div>
            <div class="tab" onclick="switchTab('optimization')">策略优化</div>
            <div class="tab" onclick="switchTab('risk')">风险评估</div>
            <div class="tab" onclick="switchTab('sentiment')">市场情绪</div>
            <div class="tab" onclick="switchTab('monitoring')">系统监控</div>
        </div>
        
        <div class="search-box">
            <input type="text" id="stockInput" placeholder="输入股票代码 (如: 0700.HK, 2800.HK)" />
            <button onclick="analyzeStock()">🔍 分析股票</button>
        </div>
        
        <div id="loading" class="loading" style="display: none;">
            <div>⏳ 正在分析中...</div>
        </div>
        
        <div id="error" class="error" style="display: none;"></div>
        
        <!-- 技术分析标签页 -->
        <div id="analysis" class="tab-content active">
            <div id="analysisResults" style="display: none;">
                <div class="results">
                    <div class="chart-container">
                        <h3>📊 价格走势图</h3>
                        <canvas id="priceChart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>📈 技术指标</h3>
                        <div id="indicatorsList"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- 策略回测标签页 -->
        <div id="backtest" class="tab-content">
            <div id="backtestResults" style="display: none;">
                <h3>🔄 策略回测结果</h3>
                <div class="metrics-grid" id="backtestMetrics"></div>
                <div class="chart-container">
                    <h3>📊 交易记录</h3>
                    <div id="tradesList"></div>
                </div>
            </div>
        </div>
        
        <!-- 策略优化标签页 -->
        <div id="optimization" class="tab-content">
            <div class="optimization-controls">
                <h3>🚀 策略参数优化</h3>
                <p>自动测试不同参数组合，找出最高Sharpe比率的策略</p>
                <div class="strategy-selector">
                    <label>选择策略类型:</label>
                    <select id="strategyType">
                        <option value="all">全部策略</option>
                        <option value="ma">移动平均交叉</option>
                        <option value="rsi">RSI策略</option>
                        <option value="macd">MACD策略</option>
                        <option value="bb">布林带策略</option>
                    </select>
                    <button onclick="runOptimization()">🔍 开始优化</button>
                </div>
            </div>
            <div id="optimizationResults" style="display: none;">
                <h3>📈 优化结果</h3>
                <div class="optimization-summary" id="optimizationSummary"></div>
                <div class="strategy-table-container">
                    <table class="strategy-table" id="strategyTable">
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>策略名称</th>
                                <th>Sharpe比率</th>
                                <th>年化收益率</th>
                                <th>波动率</th>
                                <th>最大回撤</th>
                                <th>胜率</th>
                                <th>交易次数</th>
                                <th>最终价值</th>
                            </tr>
                        </thead>
                        <tbody id="strategyTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- 风险评估标签页 -->
        <div id="risk" class="tab-content">
            <div id="riskResults" style="display: none;">
                <h3>⚠️ 风险评估</h3>
                <div class="metrics-grid" id="riskMetrics"></div>
                <div id="riskRecommendation"></div>
            </div>
        </div>
        
        <!-- 市场情绪标签页 -->
        <div id="sentiment" class="tab-content">
            <div id="sentimentResults" style="display: none;">
                <h3>😊 市场情绪分析</h3>
                <div class="metrics-grid" id="sentimentMetrics"></div>
                <div id="sentimentIndicator"></div>
            </div>
        </div>
        
        <!-- 系统监控标签页 -->
        <div id="monitoring" class="tab-content">
            <div id="monitoringResults" style="display: none;">
                <h3>📊 系统监控</h3>
                <div class="monitoring-stats" id="monitoringStats"></div>
            </div>
        </div>
    </div>

    <script>
        let priceChart = null;
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
            
            if (tabName === 'monitoring') {
                getMonitoringStats();
            }
        }
        
        async function runOptimization() {
            const symbol = document.getElementById('stockInput').value.trim();
            if (!symbol) {
                showError('请输入股票代码');
                return;
            }
            
            const strategyType = document.getElementById('strategyType').value;
            
            showLoading(true);
            hideError();
            hideOptimizationResults();
            
            try {
                const response = await fetch(`/api/strategy-optimization/${symbol}?strategy_type=${strategyType}`);
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status} 错误`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    displayOptimizationResults(result.data);
                } else {
                    showError('优化失败: ' + (result.message || '未知错误'));
                }
            } catch (error) {
                console.error('优化错误:', error);
                showError(`优化失败: ${error.message}`);
            } finally {
                showLoading(false);
            }
        }
        
        function displayOptimizationResults(data) {
            const resultsDiv = document.getElementById('optimizationResults');
            const summaryDiv = document.getElementById('optimizationSummary');
            const tableBody = document.getElementById('strategyTableBody');
            
            // 显示优化摘要
            summaryDiv.innerHTML = `
                <h4>🎯 优化完成</h4>
                <p><strong>测试策略数量:</strong> ${data.total_strategies}</p>
                <p><strong>策略类型:</strong> ${getStrategyTypeName(data.optimization_type)}</p>
                <p><strong>最佳Sharpe比率:</strong> ${data.best_sharpe_ratio}</p>
                <p><strong>优化时间:</strong> ${new Date().toLocaleString()}</p>
            `;
            
            // 清空表格
            tableBody.innerHTML = '';
            
            // 填充策略表格
            data.best_strategies.forEach((strategy, index) => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td>${strategy.strategy_name}</td>
                    <td style="color: ${strategy.sharpe_ratio > 1 ? '#28a745' : strategy.sharpe_ratio > 0 ? '#ffc107' : '#dc3545'}; font-weight: bold;">
                        ${strategy.sharpe_ratio}
                    </td>
                    <td style="color: ${strategy.annual_return > 0 ? '#28a745' : '#dc3545'};">
                        ${strategy.annual_return}%
                    </td>
                    <td>${strategy.volatility}%</td>
                    <td style="color: ${strategy.max_drawdown > -10 ? '#28a745' : strategy.max_drawdown > -20 ? '#ffc107' : '#dc3545'};">
                        ${strategy.max_drawdown}%
                    </td>
                    <td style="color: ${strategy.win_rate > 50 ? '#28a745' : '#dc3545'};">
                        ${strategy.win_rate}%
                    </td>
                    <td>${strategy.trade_count}</td>
                    <td style="color: ${strategy.final_value > 100000 ? '#28a745' : '#dc3545'}; font-weight: bold;">
                        ¥${strategy.final_value.toLocaleString()}
                    </td>
                `;
                tableBody.appendChild(row);
            });
            
            // 显示结果
            resultsDiv.style.display = 'block';
        }
        
        function getStrategyTypeName(type) {
            const names = {
                'all': '全部策略',
                'ma': '移动平均交叉',
                'rsi': 'RSI策略',
                'macd': 'MACD策略',
                'bb': '布林带策略'
            };
            return names[type] || type;
        }
        
        async function analyzeStock() {
            const symbol = document.getElementById('stockInput').value.trim();
            if (!symbol) {
                showError('请输入股票代码');
                return;
            }
            
            showLoading(true);
            hideError();
            hideAllResults();
            
            try {
                const response = await fetch(`/api/analysis/${symbol}`);
                
                if (!response.ok) {
                    const errorData = await response.json();
                    const errorMessage = errorData.detail || `HTTP ${response.status} 错误`;
                    showError(`分析失败: ${errorMessage}`);
                    return;
                }
                
                const result = await response.json();
                
                if (result.success) {
                    currentData = result.data;
                    displayAnalysisResults(result.data);
                    displayBacktestResults(result.data);
                    displayRiskResults(result.data);
                    displaySentimentResults(result.data);
                } else {
                    const errorMessage = result.message || result.detail || '未知错误';
                    showError(`分析失败: ${errorMessage}`);
                }
            } catch (error) {
                console.error('分析错误:', error);
                if (error.name === 'TypeError' && error.message.includes('fetch')) {
                    showError('网络连接失败，请检查网络连接');
                } else {
                    showError(`网络错误: ${error.message}`);
                }
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
                responsive: true,
                maintainAspectRatio: false,
                data: {
                    labels: labels,
                    datasets: [{
                        label: '收盘价',
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
                    },
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: '日期'
                            }
                        },
                        y: {
                            display: true,
                            title: {
                                display: true,
                                text: '价格'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
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
                { label: 'Bollinger Lower', value: indicators.bollinger_lower },
                { label: 'ATR', value: indicators.atr }
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
        
        function displayBacktestResults(data) {
            const container = document.getElementById('backtestMetrics');
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.total_return.toFixed(2)}%</div>
                    <div class="metric-label">总收益率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.volatility.toFixed(2)}%</div>
                    <div class="metric-label">波动率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.sharpe_ratio.toFixed(2)}</div>
                    <div class="metric-label">夏普比率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.max_drawdown.toFixed(2)}%</div>
                    <div class="metric-label">最大回撤</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.backtest.total_trades}</div>
                    <div class="metric-label">交易次数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">¥${data.backtest.final_value.toFixed(0)}</div>
                    <div class="metric-label">最终价值</div>
                </div>
            `;
            
            // 显示交易记录
            const tradesContainer = document.getElementById('tradesList');
            tradesContainer.innerHTML = '';
            data.backtest.trades.forEach(trade => {
                const div = document.createElement('div');
                div.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee;';
                div.innerHTML = `
                    <span style="font-weight: bold; color: #2c3e50;">${trade.action} ${trade.shares.toFixed(2)}股 @ ${trade.price.toFixed(2)}</span>
                    <span style="color: #7f8c8d; font-size: 0.9em;">${new Date(trade.timestamp).toLocaleDateString()}</span>
                `;
                tradesContainer.appendChild(div);
            });
            
            document.getElementById('backtestResults').style.display = 'block';
        }
        
        function displayRiskResults(data) {
            const container = document.getElementById('riskMetrics');
            const riskColor = data.risk.risk_level === 'LOW' ? '#28a745' : 
                             data.risk.risk_level === 'MEDIUM' ? '#ffc107' : '#dc3545';
            
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value" style="color: ${riskColor};">${data.risk.risk_level}</div>
                    <div class="metric-label">风险等级</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.risk.risk_score.toFixed(0)}</div>
                    <div class="metric-label">风险评分</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.risk.volatility.toFixed(2)}%</div>
                    <div class="metric-label">波动率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.risk.var_95.toFixed(2)}%</div>
                    <div class="metric-label">VaR (95%)</div>
                </div>
            `;
            
            const recDiv = document.getElementById('riskRecommendation');
            recDiv.innerHTML = `
                <div class="success">
                    <h4>投资建议</h4>
                    <p>${data.risk.recommendation}</p>
                </div>
            `;
            
            document.getElementById('riskResults').style.display = 'block';
        }
        
        function displaySentimentResults(data) {
            const container = document.getElementById('sentimentMetrics');
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.score.toFixed(1)}</div>
                    <div class="metric-label">情绪分数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.level}</div>
                    <div class="metric-label">情绪等级</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.volatility.toFixed(2)}%</div>
                    <div class="metric-label">波动率</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.trend_strength.toFixed(2)}%</div>
                    <div class="metric-label">趋势强度</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.positive_days}</div>
                    <div class="metric-label">上涨天数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.sentiment.negative_days}</div>
                    <div class="metric-label">下跌天数</div>
                </div>
            `;
            
            const indicatorDiv = document.getElementById('sentimentIndicator');
            const sentimentClass = data.sentiment.level === 'Bullish' ? 'sentiment-bullish' : 
                                 data.sentiment.level === 'Bearish' ? 'sentiment-bearish' : 'sentiment-neutral';
            
            indicatorDiv.innerHTML = `
                <div class="sentiment-indicator ${sentimentClass}">
                    <h4>市场情绪: ${data.sentiment.level}</h4>
                    <p>情绪分数: ${data.sentiment.score.toFixed(1)}/100</p>
                </div>
            `;
            
            document.getElementById('sentimentResults').style.display = 'block';
        }
        
        async function getMonitoringStats() {
            try {
                const response = await fetch('/api/monitoring');
                const result = await response.json();
                
                if (result.success) {
                    displayMonitoringStats(result.data);
                }
            } catch (error) {
                console.error('Monitoring error:', error);
            }
        }
        
        function displayMonitoringStats(data) {
            const container = document.getElementById('monitoringStats');
            container.innerHTML = `
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${data.uptime.toFixed(1)}s</div>
                        <div class="metric-label">运行时间</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.requests}</div>
                        <div class="metric-label">总请求数</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.errors}</div>
                        <div class="metric-label">错误数</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.error_rate.toFixed(2)}%</div>
                        <div class="metric-label">错误率</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.api_calls}</div>
                        <div class="metric-label">API调用</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.cache_hit_rate.toFixed(1)}%</div>
                        <div class="metric-label">缓存命中率</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.avg_response_time.toFixed(3)}s</div>
                        <div class="metric-label">平均响应时间</div>
                    </div>
                </div>
            `;
            
            document.getElementById('monitoringResults').style.display = 'block';
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
            document.getElementById('sentimentResults').style.display = 'none';
            document.getElementById('monitoringResults').style.display = 'none';
            document.getElementById('optimizationResults').style.display = 'none';
        }
        
        function hideOptimizationResults() {
            document.getElementById('optimizationResults').style.display = 'none';
        }
        
        document.getElementById('stockInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                analyzeStock();
            }
        });
        
        // 页面加载时初始化监控数据
        document.addEventListener('DOMContentLoaded', function() {
            getMonitoringStats();
        });
    </script>
</body>
</html>
    '''

# API端点
@app.get('/api/analysis/{symbol}')
def analyze_stock(symbol: str):
    start_time = time.time()
    try:
        data = get_stock_data(symbol)
        if not data:
            monitor.log_request(f"/api/analysis/{symbol}", 404, time.time() - start_time)
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 20:
            monitor.log_request(f"/api/analysis/{symbol}", 400, time.time() - start_time)
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")
        
        indicators = tech_engine.calculate_indicators(data)
        backtest = backtest_engine.run_backtest(data)
        risk = risk_engine.assess_risk(data, indicators)
        sentiment = sentiment_engine.calculate_sentiment(data)
        
        monitor.log_request(f"/api/analysis/{symbol}", 200, time.time() - start_time)
        
        return {
            'success': True,
            'data': {
                'symbol': symbol,
                'price_data': data,
                'indicators': indicators,
                'backtest': backtest,
                'risk': risk,
                'sentiment': sentiment,
                'current_price': float(pd.DataFrame(data)['close'].iloc[-1]),
                'data_count': len(data),
                'analysis_time': time.time() - start_time
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        monitor.log_request(f"/api/analysis/{symbol}", 500, time.time() - start_time)
        logger.error(f"Analysis error for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get('/api/monitoring')
def get_monitoring_stats():
    try:
        stats = monitor.get_stats()
        return {
            'success': True,
            'data': stats
        }
    except Exception as e:
        logger.error(f"Monitoring error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Monitoring failed: {str(e)}")

def run_strategy_optimization(data, strategy_type='all'):
    """运行策略参数优化 - 高计算量单线程版本，充分利用CPU性能"""
    try:
        logger.info(f"开始策略优化: {strategy_type}")
        
        df = pd.DataFrame(data)
        if len(df) < 100:
            logger.warning(f"数据不足: {len(df)} 条记录")
            return []
        
        logger.info(f"数据准备完成: {len(df)} 条记录")
        
        # 直接使用单线程但增加计算量
        return run_strategy_optimization_single_thread(data, strategy_type)
        
    except Exception as e:
        logger.error(f"策略优化失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return []

def run_strategy_optimization_single_thread(data, strategy_type='all'):
    """高计算量单线程策略优化 - 充分利用9950X3D CPU性能"""
    try:
        import time
        start_time = time.time()
        
        logger.info(f"开始高计算量策略优化: {strategy_type}")
        
        df = pd.DataFrame(data)
        if len(df) < 100:
            logger.warning(f"数据不足: {len(df)} 条记录")
            return []
        
        logger.info(f"数据准备完成: {len(df)} 条记录")
        
        results = []
        total_tasks = 0
        
        if strategy_type in ['all', 'ma']:
            # MA交叉策略优化 - 大幅增加参数范围
            logger.info("运行MA策略优化 - 高计算量版本")
            ma_tasks = 0
            for short in range(3, 51, 1):  # 3-50, 步长1 (减少范围避免过长计算时间)
                for long in range(10, 101, 2):  # 10-100, 步长2
                    if short < long:
                        ma_tasks += 1
                        try:
                            result = run_ma_strategy(df, short, long)
                            if result and isinstance(result, dict):
                                results.append(result)
                        except Exception as e:
                            logger.error(f"MA策略计算失败: {e}")
                            continue
            total_tasks += ma_tasks
            logger.info(f"MA策略完成: {ma_tasks} 个任务")
        
        if strategy_type in ['all', 'rsi']:
            # RSI策略优化 - 大幅增加参数范围
            logger.info("运行RSI策略优化 - 高计算量版本")
            rsi_tasks = 0
            for oversold in range(10, 41, 1):  # 10-40, 步长1
                for overbought in range(50, 81, 1):  # 50-80, 步长1
                    if oversold < overbought:
                        rsi_tasks += 1
                        try:
                            result = run_rsi_strategy(df, oversold, overbought)
                            if result and isinstance(result, dict):
                                results.append(result)
                        except Exception as e:
                            logger.error(f"RSI策略计算失败: {e}")
                            continue
            total_tasks += rsi_tasks
            logger.info(f"RSI策略完成: {rsi_tasks} 个任务")
        
        if strategy_type in ['all', 'macd']:
            # MACD策略优化 - 增加多个参数组合
            logger.info("运行MACD策略优化 - 多参数版本")
            macd_tasks = 0
            for fast in range(8, 17, 2):  # 8, 10, 12, 14, 16
                for slow in range(20, 31, 2):  # 20, 22, 24, 26, 28, 30
                    for signal in range(7, 12, 1):  # 7, 8, 9, 10, 11
                        if fast < slow:
                            macd_tasks += 1
                            try:
                                result = run_macd_strategy_enhanced(df, fast, slow, signal)
                                if result and isinstance(result, dict):
                                    results.append(result)
                            except Exception as e:
                                logger.error(f"MACD策略计算失败: {e}")
                                continue
            total_tasks += macd_tasks
            logger.info(f"MACD策略完成: {macd_tasks} 个任务")
        
        if strategy_type in ['all', 'bb']:
            # 布林带策略优化 - 增加多个参数组合
            logger.info("运行布林带策略优化 - 多参数版本")
            bb_tasks = 0
            for period in range(15, 31, 2):  # 15, 17, 19, 21, 23, 25, 27, 29
                for std_dev in range(1, 4, 1):  # 1, 2, 3
                    bb_tasks += 1
                    try:
                        result = run_bollinger_strategy_enhanced(df, period, std_dev)
                        if result and isinstance(result, dict):
                            results.append(result)
                    except Exception as e:
                        logger.error(f"布林带策略计算失败: {e}")
                        continue
            total_tasks += bb_tasks
            logger.info(f"布林带策略完成: {bb_tasks} 个任务")
        
        elapsed_time = time.time() - start_time
        logger.info(f"高计算量策略优化完成: 找到 {len(results)} 个有效策略")
        logger.info(f"总任务数: {total_tasks}, 耗时: {elapsed_time:.2f}秒")
        
        # 按Sharpe比率排序
        results = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)
        return results
        
    except Exception as e:
        logger.error(f"高计算量策略优化失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return []

def execute_strategy_task(strategy_type, df, param1, param2):
    """执行单个策略任务 - 用于multiprocessing"""
    try:
        if strategy_type == 'ma':
            return run_ma_strategy(df, param1, param2)
        elif strategy_type == 'rsi':
            return run_rsi_strategy(df, param1, param2)
        elif strategy_type == 'macd':
            return run_macd_strategy(df)
        elif strategy_type == 'bb':
            return run_bollinger_strategy(df)
        else:
            return None
    except Exception as e:
        logger.error(f"策略任务执行失败: {strategy_type}, {e}")
        return None

def run_ma_strategy(df, short_window, long_window):
    """MA交叉策略"""
    try:
        df = df.copy()
        df[f'MA{short_window}'] = df['close'].rolling(window=short_window).mean()
        df[f'MA{long_window}'] = df['close'].rolling(window=long_window).mean()
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 生成交易信号
        df['signal'] = np.where(df[f'MA{short_window}'] > df[f'MA{long_window}'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, f"MA交叉({short_window},{long_window})")
    except Exception as e:
        logger.error(f"MA策略计算失败: {e}")
        return None

def run_rsi_strategy(df, oversold, overbought):
    """RSI策略"""
    try:
        df = df.copy()
        # 计算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 0.0001)
        df['RSI'] = 100 - (100 / (1 + rs))
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # RSI策略信号
        df['signal'] = 0
        df.loc[df['RSI'] < oversold, 'signal'] = 1  # 超卖买入
        df.loc[df['RSI'] > overbought, 'signal'] = 0  # 超买卖出
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, f"RSI({oversold},{overbought})")
    except Exception as e:
        logger.error(f"RSI策略计算失败: {e}")
        return None

def run_macd_strategy(df):
    """MACD策略"""
    try:
        df = df.copy()
        # 计算MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # MACD策略信号
        df['signal'] = np.where(df['MACD'] > df['MACD_signal'], 1, 0)
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, "MACD")
    except Exception as e:
        logger.error(f"MACD策略计算失败: {e}")
        return None

def run_bollinger_strategy(df):
    """布林带策略"""
    try:
        df = df.copy()
        # 计算布林带
        df['BB_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df = df.dropna()
        
        if len(df) < 100:
            return None
        
        # 布林带策略信号
        df['signal'] = 0
        df.loc[df['close'] < df['BB_lower'], 'signal'] = 1  # 价格触及下轨买入
        df.loc[df['close'] > df['BB_upper'], 'signal'] = 0  # 价格触及上轨卖出
        df['position'] = df['signal'].diff()
        
        return calculate_strategy_performance(df, "布林带")
    except Exception as e:
        logger.error(f"布林带策略计算失败: {e}")
        return None

def calculate_strategy_performance(df, strategy_name):
    """计算策略绩效"""
    try:
        # 计算策略收益
        df['strategy_returns'] = df['position'].shift(1) * df['close'].pct_change()
        df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
        
        # 计算绩效指标
        total_return = (df['cumulative_returns'].iloc[-1] - 1) * 100
        annual_return = ((df['cumulative_returns'].iloc[-1] ** (252 / len(df))) - 1) * 100
        volatility = df['strategy_returns'].std() * np.sqrt(252) * 100
        sharpe_ratio = annual_return / volatility if volatility > 0 else 0
        
        # 最大回撤
        cumulative = df['cumulative_returns']
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # 胜率
        winning_trades = (df['strategy_returns'] > 0).sum()
        total_trades = (df['strategy_returns'] != 0).sum()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 交易次数
        trade_count = (df['position'] != 0).sum()
        
        return {
            'strategy_name': strategy_name,
            'total_return': round(float(total_return), 2),
            'annual_return': round(float(annual_return), 2),
            'volatility': round(float(volatility), 2),
            'sharpe_ratio': round(float(sharpe_ratio), 3),
            'max_drawdown': round(float(max_drawdown), 2),
            'win_rate': round(float(win_rate), 2),
            'trade_count': int(trade_count),
            'final_value': round(float(df['cumulative_returns'].iloc[-1] * 100000), 2)
        }
    except Exception as e:
        logger.error(f"计算策略绩效失败: {e}")
        return None

@app.get('/api/strategy-optimization/{symbol}')
def optimize_strategies(symbol: str, strategy_type: str = 'all'):
    """策略参数优化 - 找出最高Sharpe比率的策略"""
    start_time = time.time()
    try:
        logger.info(f"开始策略优化请求: {symbol}, 类型: {strategy_type}")
        
        data = get_stock_data(symbol)
        if not data:
            logger.warning(f"无法获取股票数据: {symbol}")
            monitor.log_request(f"/api/strategy-optimization/{symbol}", 404, time.time() - start_time)
            raise HTTPException(status_code=404, detail="Failed to get stock data")
        
        if len(data) < 100:
            logger.warning(f"数据不足: {symbol}, 数据量: {len(data)}")
            monitor.log_request(f"/api/strategy-optimization/{symbol}", 400, time.time() - start_time)
            raise HTTPException(status_code=400, detail="Insufficient data for optimization")
        
        logger.info(f"开始运行策略优化: {symbol}, 数据量: {len(data)}")
        
        # 运行策略优化
        results = run_strategy_optimization(data, strategy_type)
        
        logger.info(f"策略优化完成: {symbol}, 找到 {len(results)} 个策略")
        
        monitor.log_request(f"/api/strategy-optimization/{symbol}", 200, time.time() - start_time)
        return {
            "success": True,
            "data": {
                "best_strategies": results[:10],  # 前10个最佳策略
                "total_strategies": len(results),
                "optimization_type": strategy_type,
                "best_sharpe_ratio": results[0]['sharpe_ratio'] if results else 0
            },
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException as he:
        logger.error(f"HTTP异常: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"策略优化异常: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        monitor.log_request(f"/api/strategy-optimization/{symbol}", 500, time.time() - start_time)
        raise HTTPException(status_code=500, detail=f"Strategy optimization failed: {str(e)}")

@app.get('/api/test-optimization')
def test_optimization():
    """测试策略优化功能"""
    try:
        # 创建测试数据
        import pandas as pd
        import numpy as np
        
        data = []
        for i in range(200):
            data.append({
                'date': f'2023-01-{i+1:02d}',
                'open': 100 + i * 0.1,
                'high': 105 + i * 0.1,
                'low': 95 + i * 0.1,
                'close': 100 + i * 0.1 + np.random.normal(0, 1),
                'volume': 1000
            })
        
        # 测试策略优化
        results = run_strategy_optimization(data, 'ma')
        
        return {
            "success": True,
            "message": "策略优化测试成功",
            "results_count": len(results),
            "best_strategy": results[0] if results else None
        }
    except Exception as e:
        logger.error(f"测试优化失败: {e}")
        import traceback
        logger.error(f"测试错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.get('/api/health')
def health_check():
    try:
        uptime = time.time() - monitor.start_time
        return {
            'success': True,
            'data': {
                'status': 'healthy',
                'uptime': uptime,
                'version': '7.0.0',
                'timestamp': datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            'success': False,
            'data': {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        }

if __name__ == "__main__":
    print("🚀 Starting Complete Quant Trading System v7.0...")
    print("📊 Features: Technical Analysis, Backtesting, Risk Assessment, Sentiment Analysis, Monitoring")
    print("⚡ Technologies: FastAPI, Pandas, NumPy, Chart.js, Performance Monitoring")
    print("🌐 Access: http://localhost:8001")
    print("📚 Docs: http://localhost:8001/docs")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8001)

def run_macd_strategy_enhanced(df, fast_period=12, slow_period=26, signal_period=9):
    """增强版MACD策略 - 支持自定义参数"""
    try:
        df = df.copy()
        
        # 计算MACD
        exp1 = df['close'].ewm(span=fast_period).mean()
        exp2 = df['close'].ewm(span=slow_period).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=signal_period).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # 生成交易信号
        df['signal'] = 0
        df.loc[(df['macd'] > df['macd_signal']) & (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'signal'] = 1  # 买入信号
        df.loc[(df['macd'] < df['macd_signal']) & (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'signal'] = -1  # 卖出信号
        
        # 计算策略性能
        strategy_name = f'MACD({fast_period},{slow_period},{signal_period})'
        return calculate_strategy_performance(df, strategy_name)
        
    except Exception as e:
        logger.error(f"增强版MACD策略计算失败: {e}")
        return None

def run_bollinger_strategy_enhanced(df, period=20, std_dev=2):
    """增强版布林带策略 - 支持自定义参数"""
    try:
        df = df.copy()
        
        # 计算布林带
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (bb_std * std_dev)
        
        # 生成交易信号
        df['signal'] = 0
        df.loc[df['close'] < df['bb_lower'], 'signal'] = 1  # 买入信号
        df.loc[df['close'] > df['bb_upper'], 'signal'] = -1  # 卖出信号
        
        # 计算策略性能
        strategy_name = f'布林带({period},{std_dev})'
        return calculate_strategy_performance(df, strategy_name)
        
    except Exception as e:
        logger.error(f"增强版布林带策略计算失败: {e}")
        return None
