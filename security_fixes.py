"""
安全修复补丁 - QA审查后的安全改进
"""

import os
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Any, Optional
import logging

# 配置常量
SMA_SHORT_PERIOD = 20
SMA_LONG_PERIOD = 50
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2
ATR_PERIOD = 14

# 安全配置
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8001",
    "http://127.0.0.1:8001"
]

# 环境变量配置
API_BASE_URL = os.getenv('STOCK_API_URL', 'http://18.180.162.113:9191')
MAX_DURATION = int(os.getenv('MAX_DURATION', '3650'))
MIN_DURATION = int(os.getenv('MIN_DURATION', '1'))

class SecurityValidator:
    """安全验证器"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """验证股票代码格式"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # 允许的格式: AAPL, 0700.HK, 2800.HK等
        pattern = r'^[A-Z0-9\.]+$'
        return bool(re.match(pattern, symbol.upper()))
    
    @staticmethod
    def validate_duration(duration: int) -> bool:
        """验证持续时间范围"""
        return MIN_DURATION <= duration <= MAX_DURATION
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理输入文本"""
        if not text:
            return ""
        # 移除潜在危险字符
        return re.sub(r'[<>"\']', '', text.strip())

class SecureAPIClient:
    """安全的API客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get_stock_data(self, symbol: str, duration: int = 1825) -> Optional[List[Dict[str, Any]]]:
        """安全获取股票数据"""
        try:
            # 输入验证
            if not SecurityValidator.validate_symbol(symbol):
                raise ValueError(f"Invalid symbol format: {symbol}")
            
            if not SecurityValidator.validate_duration(duration):
                raise ValueError(f"Duration must be between {MIN_DURATION} and {MAX_DURATION}")
            
            # 清理输入
            clean_symbol = SecurityValidator.sanitize_input(symbol)
            
            url = f'{API_BASE_URL}/inst/getInst'
            params = {
                'symbol': clean_symbol.lower(),
                'duration': duration
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' not in data or not isinstance(data['data'], dict):
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
            
            return formatted_data
            
        except requests.RequestException as e:
            logging.error(f"Network error for {symbol}: {str(e)}")
            return None
        except ValueError as e:
            logging.error(f"Validation error for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error for {symbol}: {str(e)}")
            return None

class SecureTechnicalAnalysis:
    """安全的技术分析引擎"""
    
    @staticmethod
    def calculate_indicators(data: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算技术指标 - 带类型注解"""
        try:
            import pandas as pd
            import numpy as np
            
            if not data or len(data) < SMA_SHORT_PERIOD:
                return {}
            
            df = pd.DataFrame(data)
            
            # 验证必需列
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    return {}
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            if len(df) < SMA_SHORT_PERIOD:
                return {}
            
            close = df['close']
            indicators = {}
            
            # 移动平均线
            if len(close) >= SMA_SHORT_PERIOD:
                indicators['sma_20'] = float(close.rolling(window=SMA_SHORT_PERIOD).mean().iloc[-1])
            if len(close) >= SMA_LONG_PERIOD:
                indicators['sma_50'] = float(close.rolling(window=SMA_LONG_PERIOD).mean().iloc[-1])
            
            # RSI
            if len(close) >= RSI_PERIOD:
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
            
            # MACD
            if len(close) >= MACD_SLOW:
                ema_12 = close.ewm(span=MACD_FAST).mean()
                ema_26 = close.ewm(span=MACD_SLOW).mean()
                macd_line = ema_12 - ema_26
                signal_line = macd_line.ewm(span=MACD_SIGNAL).mean()
                indicators['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
                indicators['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
            
            # 布林带
            if len(close) >= BOLLINGER_PERIOD:
                sma_20 = close.rolling(window=BOLLINGER_PERIOD).mean()
                std_20 = close.rolling(window=BOLLINGER_PERIOD).std()
                indicators['bollinger_upper'] = float(sma_20.iloc[-1] + BOLLINGER_STD * std_20.iloc[-1])
                indicators['bollinger_middle'] = float(sma_20.iloc[-1])
                indicators['bollinger_lower'] = float(sma_20.iloc[-1] - BOLLINGER_STD * std_20.iloc[-1])
            
            return indicators
            
        except Exception as e:
            logging.error(f"Technical analysis error: {str(e)}")
            return {}

# 使用示例
if __name__ == "__main__":
    # 测试安全验证
    validator = SecurityValidator()
    print("Symbol validation tests:")
    print(f"AAPL: {validator.validate_symbol('AAPL')}")
    print(f"0700.HK: {validator.validate_symbol('0700.HK')}")
    print(f"Invalid: {validator.validate_symbol('invalid@symbol')}")
    
    print("\nDuration validation tests:")
    print(f"30 days: {validator.validate_duration(30)}")
    print(f"5000 days: {validator.validate_duration(5000)}")
    
    # 测试安全API客户端
    client = SecureAPIClient()
    print("\nTesting secure API client...")
    data = client.get_stock_data("0700.HK", 30)
    if data:
        print(f"Successfully fetched {len(data)} records")
    else:
        print("Failed to fetch data")
