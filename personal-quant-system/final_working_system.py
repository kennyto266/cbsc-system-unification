"""
个人量化交易系统 - 最终工作版本
集成真实股票数据API，正确处理数据格式
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

# 创建FastAPI应用
app = FastAPI(
    title="个人量化交易系统",
    description="为个人投资者提供专业级的港股量化分析工具",
    version="1.0.0"
)

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 股票数据API配置
STOCK_API_BASE = "http://18.180.162.113:9191"

def get_stock_data(symbol: str, duration: int = 1825) -> Dict[str, Any]:
    """获取股票数据并转换为标准格式"""
    try:
        url = f"{STOCK_API_BASE}/inst/getInst"
        params = {
            "symbol": symbol.lower(),
            "duration": duration
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        raw_data = response.json()
        
        # 转换数据格式
        if 'data' in raw_data and isinstance(raw_data['data'], dict):
            time_series_data = raw_data['data']
            
            # 提取所有时间戳
            timestamps = set()
            for key in time_series_data.keys():
                if key in ['open', 'high', 'low', 'close', 'volume']:
                    timestamps.update(time_series_data[key].keys())
            
            timestamps = sorted(list(timestamps))
            
            # 构建标准格式的数据
            formatted_data = []
            for ts in timestamps:
                row = {'timestamp': ts}
                
                for price_type in ['open', 'high', 'low', 'close', 'volume']:
                    if price_type in time_series_data and ts in time_series_data[price_type]:
                        row[price_type] = time_series_data[price_type][ts]
                    else:
                        row[price_type] = None
                
                # 只添加有完整数据的行
                if all(row[key] is not None for key in ['open', 'high', 'low', 'close', 'volume']):
                    formatted_data.append(row)
            
            return {
                'symbol': symbol,
                'data': formatted_data,
                'count': len(formatted_data),
                'timestamp': raw_data.get('ts', None)
            }
        else:
            return None
            
    except Exception as e:
        print(f"获取股票数据失败 {symbol}: {e}")
        return None

def calculate_technical_indicators(data: List[Dict]) -> Dict[str, Any]:
    """计算技术指标"""
    if not data or len(data) < 20:
        return {}
    
    try:
        # 转换为DataFrame
        df = pd.DataFrame(data)
        
        # 确保数据类型正确
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 删除包含NaN的行
        df = df.dropna()
        
        if len(df) < 20:
            return {}
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
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
            histogram = macd_line - signal_line
            
            indicators['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
            indicators['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
            indicators['macd_histogram'] = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
        
        # 布林带
        if len(close) >= 20:
            sma_20 = close.rolling(window=20).mean()
            std_20 = close.rolling(window=20).std()
            indicators['bollinger_upper'] = float(sma_20.iloc[-1] + 2 * std_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
            indicators['bollinger_middle'] = float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
            indicators['bollinger_lower'] = float(sma_20.iloc[-1] - 2 * std_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
        
        return indicators
        
    except Exception as e:
        print(f"计算技术指标失败: {e}")
        return {}

def analyze_trend(data: List[Dict]) -> Dict[str, Any]:
    """分析趋势"""
    try:
        if not data or len(data) < 50:
            return {"trend": "insufficient_data", "strength": 0}
        
        df = pd.DataFrame(data)
        
        # 确保数据类型正确
        for col in ['close']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df.dropna()
        close = df['close']
        
        if len(close) < 50:
            return {"trend": "insufficient_data", "strength": 0}
        
        # 计算移动平均线
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        
        if len(sma_20) < 2 or len(sma_50) < 2:
            return {"trend": "insufficient_data", "strength": 0}
        
        current_price = close.iloc[-1]
        sma_20_current = sma_20.iloc[-1]
        sma_50_current = sma_50.iloc[-1]
        
        if current_price > sma_20_current > sma_50_current:
            trend = "uptrend"
            strength = min(100, ((current_price - sma_50_current) / sma_50_current) * 100)
        elif current_price < sma_20_current < sma_50_current:
            trend = "downtrend"
            strength = min(100, ((sma_50_current - current_price) / sma_50_current) * 100)
        else:
            trend = "sideways"
            strength = 0
        
        return {
            "trend": trend,
            "strength": round(strength, 2),
            "current_price": float(current_price),
            "sma_20": float(sma_20_current),
            "sma_50": float(sma_50_current)
        }
        
    except Exception as e:
        print(f"分析趋势失败: {e}")
        return {"trend": "error", "strength": 0}

# API端点
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "个人量化交易系统运行正常",
        "status": "healthy",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "stocks": "/api/stocks",
            "stock_data": "/api/stocks/{symbol}/data",
            "analysis": "/api/stocks/{symbol}/analysis"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "个人量化交易系统运行正常"}

@app.get("/api/stocks")
async def get_stocks():
    """获取股票列表"""
    stocks = [
        {"symbol": "0700.HK", "name": "腾讯控股", "sector": "科技"},
        {"symbol": "2800.HK", "name": "盈富基金", "sector": "金融"},
        {"symbol": "1299.HK", "name": "友邦保险", "sector": "保险"},
        {"symbol": "0941.HK", "name": "中国移动", "sector": "电信"},
        {"symbol": "0388.HK", "name": "香港交易所", "sector": "金融"}
    ]
    
    return {
        "success": True,
        "data": stocks,
        "message": "股票列表获取成功"
    }

@app.get("/api/stocks/{symbol}/data")
async def get_stock_data_api(symbol: str, duration: int = 1825):
    """获取股票数据"""
    try:
        data = get_stock_data(symbol, duration)
        
        if not data:
            raise HTTPException(status_code=404, detail="未找到股票数据")
        
        return {
            "success": True,
            "data": data,
            "message": f"股票 {symbol} 数据获取成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票数据失败: {str(e)}")

@app.get("/api/stocks/{symbol}/analysis")
async def get_stock_analysis(symbol: str, duration: int = 1825):
    """获取股票技术分析"""
    try:
        # 获取股票数据
        stock_data = get_stock_data(symbol, duration)
        
        if not stock_data:
            raise HTTPException(status_code=404, detail="未找到股票数据")
        
        # 提取价格数据
        price_data = stock_data.get('data', [])
        
        if not price_data:
            raise HTTPException(status_code=400, detail="数据格式错误")
        
        # 计算技术指标
        indicators = calculate_technical_indicators(price_data)
        
        # 分析趋势
        trend_analysis = analyze_trend(price_data)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "indicators": indicators,
                "trend_analysis": trend_analysis,
                "data_count": len(price_data),
                "analysis_time": datetime.now().isoformat()
            },
            "message": f"股票 {symbol} 技术分析完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"技术分析失败: {str(e)}")

@app.get("/api/test")
async def test_api():
    """测试API"""
    return {
        "success": True,
        "message": "API测试成功",
        "data": {
            "system": "个人量化交易系统",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    }

if __name__ == "__main__":
    print("🚀 启动个人量化交易系统...")
    print("📊 访问地址: http://localhost:8001")
    print("📚 API文档: http://localhost:8001/docs")
    print("🔍 健康检查: http://localhost:8001/health")
    print("📈 股票数据API: http://18.180.162.113:9191")
    print("=" * 50)
    
    uvicorn.run(
        "final_working_system:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
