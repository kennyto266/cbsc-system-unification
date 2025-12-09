#!/usr/bin/env python3
"""
测试API连接和数据处理
"""

import requests
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_stock_api():
    """测试股票API"""
    try:
        url = 'http://18.180.162.113:9191/inst/getInst'
        params = {'symbol': '0700.hk', 'duration': 1825}
        
        logger.info(f"正在测试API: {url}")
        response = requests.get(url, params=params, timeout=10)
        logger.info(f"响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"数据类型: {type(data)}")
            logger.info(f"数据键: {list(data.keys())}")
            
            if 'data' in data:
                time_series = data['data']
                logger.info(f"时间序列键: {list(time_series.keys())}")
                
                # 检查数据格式
                for key in ['open', 'high', 'low', 'close', 'volume']:
                    if key in time_series:
                        sample_data = list(time_series[key].items())[:3]
                        logger.info(f"{key} 样本数据: {sample_data}")
                    else:
                        logger.warning(f"缺少 {key} 数据")
                
                # 计算时间戳
                timestamps = set()
                for key in time_series.keys():
                    if key in ['open', 'high', 'low', 'close', 'volume']:
                        timestamps.update(time_series[key].keys())
                
                logger.info(f"找到 {len(timestamps)} 个时间戳")
                if timestamps:
                    sample_timestamps = sorted(list(timestamps))[:5]
                    logger.info(f"样本时间戳: {sample_timestamps}")
                
                return True
            else:
                logger.error("数据中没有 'data' 字段")
                return False
        else:
            logger.error(f"API请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始测试股票API...")
    success = test_stock_api()
    print(f"测试结果: {'成功' if success else '失败'}")
