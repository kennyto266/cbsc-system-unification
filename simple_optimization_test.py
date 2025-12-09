#!/usr/bin/env python3
"""
简化的策略优化测试
"""

import pandas as pd
import numpy as np
import requests
import json

def test_optimization_api():
    """测试策略优化API"""
    try:
        print("🚀 测试策略优化API...")
        
        # 测试API端点
        url = "http://localhost:8001/api/strategy-optimization/0700.HK?strategy_type=ma"
        
        print(f"请求URL: {url}")
        response = requests.get(url, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API请求成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    test_optimization_api()
