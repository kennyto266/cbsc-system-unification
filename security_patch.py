"""
安全补丁 - 修复CORS和输入验证问题
立即应用的安全修复
"""

import re
import os
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

# 安全配置常量
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8001", 
    "http://127.0.0.1:8001",
    "http://127.0.0.1:3000"
]

# 环境变量配置
API_BASE_URL = os.getenv('STOCK_API_URL', 'http://18.180.162.113:9191')
MAX_DURATION = int(os.getenv('MAX_DURATION', '3650'))
MIN_DURATION = int(os.getenv('MIN_DURATION', '1'))

class SecurityValidator:
    """安全验证器 - 修复输入验证问题"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """验证股票代码格式 - 防止注入攻击"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # 只允许字母、数字和点号，防止注入
        pattern = r'^[A-Z0-9\.]+$'
        return bool(re.match(pattern, symbol.upper()))
    
    @staticmethod
    def validate_duration(duration: int) -> bool:
        """验证持续时间范围 - 防止恶意请求"""
        return MIN_DURATION <= duration <= MAX_DURATION
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理输入文本 - 移除危险字符"""
        if not text:
            return ""
        # 移除潜在危险字符
        return re.sub(r'[<>"\';\\]', '', text.strip())
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """验证API密钥格式"""
        if not api_key:
            return False
        # 简单的API密钥格式验证
        return len(api_key) >= 8 and re.match(r'^[a-zA-Z0-9_-]+$', api_key)

def create_secure_cors_middleware():
    """创建安全的CORS中间件 - 修复CORS安全问题"""
    return CORSMiddleware(
        app=None,  # 将在应用中使用
        allow_origins=ALLOWED_ORIGINS,  # 限制允许的域名
        allow_credentials=True,
        allow_methods=["GET", "POST"],  # 只允许必要的方法
        allow_headers=["Content-Type", "Authorization"],  # 限制允许的头部
        expose_headers=["X-Total-Count"],  # 只暴露必要的头部
    )

def apply_security_patch(app: FastAPI) -> FastAPI:
    """应用安全补丁到FastAPI应用"""
    
    # 1. 修复CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["X-Total-Count"]
    )
    
    # 2. 添加安全头部中间件
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
    
    return app

def secure_get_stock_data(symbol: str, duration: int = 1825) -> Optional[List[Dict[str, Any]]]:
    """安全的股票数据获取函数 - 修复输入验证问题"""
    try:
        # 1. 输入验证
        if not SecurityValidator.validate_symbol(symbol):
            raise ValueError(f"Invalid symbol format: {symbol}")
        
        if not SecurityValidator.validate_duration(duration):
            raise ValueError(f"Duration must be between {MIN_DURATION} and {MAX_DURATION}")
        
        # 2. 清理输入
        clean_symbol = SecurityValidator.sanitize_input(symbol)
        
        # 3. 构建安全的URL
        url = f'{API_BASE_URL}/inst/getInst'
        params = {
            'symbol': clean_symbol.lower(),
            'duration': duration
        }
        
        # 4. 安全的API调用
        import requests
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 5. 验证响应数据
        if 'data' not in data or not isinstance(data['data'], dict):
            return None
        
        # 6. 安全的数据处理
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

def secure_api_endpoint(symbol: str, duration: int = 1825):
    """安全的API端点包装器"""
    try:
        # 输入验证
        if not SecurityValidator.validate_symbol(symbol):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid symbol format. Expected format: [A-Z0-9.]+"
            )
        
        if not SecurityValidator.validate_duration(duration):
            raise HTTPException(
                status_code=400,
                detail=f"Duration must be between {MIN_DURATION} and {MAX_DURATION} days"
            )
        
        # 获取数据
        data = secure_get_stock_data(symbol, duration)
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail="Failed to fetch stock data"
            )
        
        if len(data) < 20:
            raise HTTPException(
                status_code=400,
                detail="Insufficient data for analysis"
            )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API endpoint error for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

# 使用示例和测试
def test_security_fixes():
    """测试安全修复"""
    print("🔒 测试安全修复...")
    
    # 测试符号验证
    test_symbols = [
        ("0700.HK", True),
        ("AAPL", True),
        ("invalid@symbol", False),
        ("<script>alert('xss')</script>", False),
        ("'; DROP TABLE users; --", False)
    ]
    
    print("\n📊 符号验证测试:")
    for symbol, expected in test_symbols:
        result = SecurityValidator.validate_symbol(symbol)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {symbol}: {result} (expected: {expected})")
    
    # 测试持续时间验证
    test_durations = [
        (30, True),
        (365, True),
        (5000, False),
        (-1, False),
        (0, False)
    ]
    
    print("\n⏰ 持续时间验证测试:")
    for duration, expected in test_durations:
        result = SecurityValidator.validate_duration(duration)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {duration} days: {result} (expected: {expected})")
    
    # 测试输入清理
    test_inputs = [
        ("normal input", "normal input"),
        ("<script>alert('xss')</script>", "scriptalert('xss')/script"),
        ("'; DROP TABLE users; --", "' DROP TABLE users; --"),
        ("test@email.com", "test@email.com")
    ]
    
    print("\n🧹 输入清理测试:")
    for input_text, expected in test_inputs:
        result = SecurityValidator.sanitize_input(input_text)
        print(f"  '{input_text}' -> '{result}'")
    
    print("\n✅ 安全修复测试完成!")

if __name__ == "__main__":
    test_security_fixes()
