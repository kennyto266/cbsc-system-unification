"""
分析API模块 - 提供技术分析相关接口
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
from backend.services.analysis_service import TechnicalAnalysisService

router = APIRouter()

# 初始化技术分析服务
analysis_service = TechnicalAnalysisService()

@router.post("/technical")
async def technical_analysis(request: Dict[str, Any]):
    """技术分析"""
    try:
        symbol = request.get("symbol")
        data = request.get("data", [])
        
        if not symbol or not data:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 转换为DataFrame
        df = pd.DataFrame(data)
        if df.empty:
            raise HTTPException(status_code=400, detail="数据为空")
        
        # 计算技术指标
        indicators = analysis_service.calculate_technical_indicators(data)
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "indicators": indicators,
                "analysis_time": datetime.now().isoformat()
            },
            "message": "技术分析完成",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"技术分析失败: {str(e)}")

@router.get("/indicators/{symbol}")
async def get_indicators(symbol: str, period: str = "1mo"):
    """获取技术指标"""
    try:
        # 这里应该从数据库获取历史数据
        # 暂时返回模拟数据
        indicators = {
            "sma_20": 100.5,
            "sma_50": 98.2,
            "ema_12": 101.2,
            "ema_26": 99.8,
            "rsi": 65.5,
            "macd": 1.4,
            "macd_signal": 1.2,
            "macd_histogram": 0.2,
            "bollinger_upper": 105.2,
            "bollinger_middle": 100.5,
            "bollinger_lower": 95.8,
            "atr": 2.1,
            "volume_sma": 1000000,
            "volume_ratio": 1.2
        }
        
        return {
            "success": True,
            "data": {
                "symbol": symbol,
                "period": period,
                "indicators": indicators,
                "timestamp": datetime.now().isoformat()
            },
            "message": "技术指标获取成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取技术指标失败: {str(e)}")

def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """计算技术指标"""
    if len(df) < 20:
        return {}
    
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    indicators = {}
    
    # 移动平均线
    indicators['sma_20'] = float(close.rolling(window=20).mean().iloc[-1])
    indicators['sma_50'] = float(close.rolling(window=50).mean().iloc[-1])
    
    # EMA
    indicators['ema_12'] = float(close.ewm(span=12).mean().iloc[-1])
    indicators['ema_26'] = float(close.ewm(span=26).mean().iloc[-1])
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    indicators['rsi'] = float(100 - (100 / (1 + rs)).iloc[-1])
    
    # MACD
    macd_line = indicators['ema_12'] - indicators['ema_26']
    signal_line = close.ewm(span=9).mean().iloc[-1]
    indicators['macd'] = float(macd_line)
    indicators['macd_signal'] = float(signal_line)
    indicators['macd_histogram'] = float(macd_line - signal_line)
    
    # 布林带
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    indicators['bollinger_upper'] = float((sma_20 + 2 * std_20).iloc[-1])
    indicators['bollinger_middle'] = float(sma_20.iloc[-1])
    indicators['bollinger_lower'] = float((sma_20 - 2 * std_20).iloc[-1])
    
    # ATR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    indicators['atr'] = float(true_range.rolling(window=14).mean().iloc[-1])
    
    # 成交量指标
    indicators['volume_sma'] = float(volume.rolling(window=20).mean().iloc[-1])
    indicators['volume_ratio'] = float(volume.iloc[-1] / indicators['volume_sma'])
    
    return indicators
