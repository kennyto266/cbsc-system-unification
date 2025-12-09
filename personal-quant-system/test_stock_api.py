"""
测试股票数据API
"""

import requests
import json
from datetime import datetime

def test_stock_api():
    """测试股票数据API"""
    print("🧪 测试股票数据API...")
    
    # 测试API
    url = "http://18.180.162.113:9191/inst/getInst"
    params = {
        "symbol": "0700.hk",
        "duration": 1825
    }
    
    try:
        print(f"📡 请求URL: {url}")
        print(f"📊 参数: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        print(f"📈 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API调用成功!")
            print(f"📋 数据类型: {type(data)}")
            
            if isinstance(data, dict):
                print(f"🔑 数据键: {list(data.keys())}")
                
                if 'data' in data and isinstance(data['data'], list):
                    price_data = data['data']
                    print(f"📊 价格数据条数: {len(price_data)}")
                    
                    if price_data:
                        print("📈 最新价格数据:")
                        latest = price_data[-1]
                        for key, value in latest.items():
                            print(f"   {key}: {value}")
                        
                        # 计算简单统计
                        if 'close' in latest:
                            print(f"💰 最新收盘价: {latest['close']}")
                        
                        return True
                    else:
                        print("❌ 价格数据为空")
                        return False
                else:
                    print("❌ 数据格式错误，缺少price_data")
                    print(f"📄 完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    return False
            else:
                print(f"❌ 响应不是字典格式: {type(data)}")
                return False
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"📄 错误信息: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def test_technical_analysis():
    """测试技术分析功能"""
    print("\n🔬 测试技术分析功能...")
    
    # 获取数据
    url = "http://18.180.162.113:9191/inst/getInst"
    params = {
        "symbol": "0700.hk",
        "duration": 1825
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and isinstance(data['data'], list):
                price_data = data['data']
                print(f"📊 获取到 {len(price_data)} 条价格数据")
                
                # 简单的技术分析
                if len(price_data) >= 20:
                    closes = [float(item['close']) for item in price_data if 'close' in item]
                    
                    if closes:
                        # 计算简单移动平均
                        sma_20 = sum(closes[-20:]) / 20
                        current_price = closes[-1]
                        
                        print(f"💰 当前价格: {current_price}")
                        print(f"📈 20日均线: {sma_20:.2f}")
                        
                        if current_price > sma_20:
                            print("📊 趋势: 上涨 (价格高于20日均线)")
                        else:
                            print("📊 趋势: 下跌 (价格低于20日均线)")
                        
                        return True
                    else:
                        print("❌ 无法提取收盘价数据")
                        return False
                else:
                    print("❌ 数据不足，无法进行技术分析")
                    return False
            else:
                print("❌ 数据格式错误")
                return False
        else:
            print(f"❌ 获取数据失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 技术分析测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始测试个人量化交易系统...")
    print("=" * 50)
    
    # 测试股票数据API
    api_success = test_stock_api()
    
    # 测试技术分析
    analysis_success = test_technical_analysis()
    
    print("\n" + "=" * 50)
    print("📋 测试结果总结:")
    print(f"📡 股票数据API: {'✅ 成功' if api_success else '❌ 失败'}")
    print(f"🔬 技术分析功能: {'✅ 成功' if analysis_success else '❌ 失败'}")
    
    if api_success and analysis_success:
        print("🎉 所有测试通过！系统可以正常工作。")
    else:
        print("⚠️ 部分测试失败，需要修复问题。")
