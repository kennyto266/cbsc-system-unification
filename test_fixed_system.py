#!/usr/bin/env python3
"""
测试修复后的系统功能
"""

import requests
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stock_data_fetch():
    """测试股票数据获取"""
    try:
        url = 'http://18.180.162.113:9191/inst/getInst'
        params = {'symbol': '0700.hk', 'duration': 1825}
        
        logger.info(f"Fetching stock data: 0700.hk")
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API response data type: {type(data)}")
            
            if 'data' in data and isinstance(data['data'], dict):
                time_series = data['data']
                timestamps = set()
                
                for key in time_series.keys():
                    if key in ['open', 'high', 'low', 'close', 'volume']:
                        timestamps.update(time_series[key].keys())
                
                if timestamps:
                    timestamps = sorted(list(timestamps))
                    logger.info(f"Found {len(timestamps)} timestamps")
                    
                    # 测试数据格式化
                    formatted_data = []
                    for ts in timestamps[:10]:  # 只处理前10个时间戳
                        row = {'timestamp': ts}
                        for price_type in ['open', 'high', 'low', 'close', 'volume']:
                            if price_type in time_series and ts in time_series[price_type]:
                                row[price_type] = time_series[price_type][ts]
                            else:
                                row[price_type] = None
                        
                        if all(row[key] is not None for key in ['open', 'high', 'low', 'close', 'volume']):
                            formatted_data.append(row)
                    
                    logger.info(f"Successfully formatted {len(formatted_data)} records")
                    return True
                else:
                    logger.error("No timestamps found")
                    return False
            else:
                logger.error("Invalid data format")
                return False
        else:
            logger.error(f"API request failed: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing fixed system functionality...")
    success = test_stock_data_fetch()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")
