"""
数据处理测试
测试数据获取、转换、验证等功能
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestDataProcessing:
    """数据处理测试类"""
    
    def setup_method(self):
        """设置测试数据"""
        self.sample_api_response = {
            "data": {
                "open": {
                    "1640995200": 100.0,
                    "1641081600": 102.0,
                    "1641168000": 104.0
                },
                "high": {
                    "1640995200": 105.0,
                    "1641081600": 107.0,
                    "1641168000": 109.0
                },
                "low": {
                    "1640995200": 95.0,
                    "1641081600": 97.0,
                    "1641168000": 99.0
                },
                "close": {
                    "1640995200": 102.0,
                    "1641081600": 104.0,
                    "1641168000": 106.0
                },
                "volume": {
                    "1640995200": 1000,
                    "1641081600": 1200,
                    "1641168000": 1100
                }
            }
        }
        
        self.expected_formatted_data = [
            {
                'timestamp': '1640995200',
                'open': 100.0,
                'high': 105.0,
                'low': 95.0,
                'close': 102.0,
                'volume': 1000
            },
            {
                'timestamp': '1641081600',
                'open': 102.0,
                'high': 107.0,
                'low': 97.0,
                'close': 104.0,
                'volume': 1200
            },
            {
                'timestamp': '1641168000',
                'open': 104.0,
                'high': 109.0,
                'low': 99.0,
                'close': 106.0,
                'volume': 1100
            }
        ]
    
    def test_data_format_conversion(self):
        """测试数据格式转换"""
        # 模拟数据转换函数
        def convert_api_data_to_list(api_response):
            if 'data' not in api_response or not isinstance(api_response['data'], dict):
                return None
            
            time_series = api_response['data']
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
        
        result = convert_api_data_to_list(self.sample_api_response)
        
        assert result is not None
        assert len(result) == 3
        assert result == self.expected_formatted_data
    
    def test_data_validation(self):
        """测试数据验证"""
        def validate_stock_data(data):
            if not data:
                return False
            
            required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            for item in data:
                if not all(field in item for field in required_fields):
                    return False
                
                if not all(item[field] is not None for field in required_fields):
                    return False
                
                # 检查数值类型
                numeric_fields = ['open', 'high', 'low', 'close', 'volume']
                for field in numeric_fields:
                    if not isinstance(item[field], (int, float)):
                        return False
                
                # 检查价格逻辑
                if item['high'] < item['low']:
                    return False
                
                if item['close'] > item['high'] or item['close'] < item['low']:
                    return False
            
            return True
        
        # 测试有效数据
        assert validate_stock_data(self.expected_formatted_data) == True
        
        # 测试无效数据
        invalid_data = [
            {'timestamp': '1640995200', 'open': 100, 'high': 95, 'low': 105, 'close': 102, 'volume': 1000},  # high < low
            {'timestamp': '1640995200', 'open': 100, 'high': 105, 'low': 95, 'close': 110, 'volume': 1000},  # close > high
            {'timestamp': '1640995200', 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': None},  # None value
        ]
        
        for invalid_item in invalid_data:
            assert validate_stock_data([invalid_item]) == False
    
    def test_data_cleaning(self):
        """测试数据清理"""
        def clean_stock_data(data):
            if not data:
                return []
            
            cleaned_data = []
            for item in data:
                # 移除异常值
                if item['volume'] <= 0:
                    continue
                
                if item['open'] <= 0 or item['high'] <= 0 or item['low'] <= 0 or item['close'] <= 0:
                    continue
                
                # 检查价格变化是否合理（单日变化不超过50%）
                if item['open'] > 0:
                    price_change = abs(item['close'] - item['open']) / item['open']
                    if price_change > 0.5:
                        continue
                
                cleaned_data.append(item)
            
            return cleaned_data
        
        # 测试正常数据
        normal_data = self.expected_formatted_data
        cleaned = clean_stock_data(normal_data)
        assert len(cleaned) == 3
        
        # 测试包含异常值的数据
        data_with_outliers = normal_data + [
            {'timestamp': '1641254400', 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 0},  # 零交易量
            {'timestamp': '1641340800', 'open': 100, 'high': 105, 'low': 95, 'close': 200, 'volume': 1000},  # 异常价格变化
        ]
        
        cleaned = clean_stock_data(data_with_outliers)
        assert len(cleaned) == 3  # 应该过滤掉异常值
    
    def test_data_aggregation(self):
        """测试数据聚合"""
        def aggregate_daily_data(data):
            if not data:
                return []
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['timestamp'], unit='s').dt.date
            
            # 按日期聚合
            daily_data = df.groupby('date').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).reset_index()
            
            return daily_data.to_dict('records')
        
        # 创建多天数据
        multi_day_data = []
        for i in range(3):
            for j in range(3):  # 每天3条记录
                timestamp = 1640995200 + i * 86400 + j * 3600  # 每天间隔1小时
                multi_day_data.append({
                    'timestamp': str(timestamp),
                    'open': 100 + i,
                    'high': 105 + i,
                    'low': 95 + i,
                    'close': 102 + i,
                    'volume': 1000 + j * 100
                })
        
        aggregated = aggregate_daily_data(multi_day_data)
        
        assert len(aggregated) == 3  # 应该聚合为3天
        assert all('date' in item for item in aggregated)
        assert all('volume' in item for item in aggregated)
    
    def test_missing_data_handling(self):
        """测试缺失数据处理"""
        def handle_missing_data(data):
            if not data:
                return []
            
            df = pd.DataFrame(data)
            
            # 前向填充缺失值
            df = df.fillna(method='ffill')
            
            # 如果仍有缺失值，使用后向填充
            df = df.fillna(method='bfill')
            
            # 如果仍有缺失值，删除该行
            df = df.dropna()
            
            return df.to_dict('records')
        
        # 创建包含缺失值的数据
        data_with_missing = [
            {'timestamp': '1640995200', 'open': 100, 'high': 105, 'low': 95, 'close': 102, 'volume': 1000},
            {'timestamp': '1641081600', 'open': None, 'high': 107, 'low': 97, 'close': 104, 'volume': 1200},
            {'timestamp': '1641168000', 'open': 104, 'high': 109, 'low': 99, 'close': None, 'volume': 1100},
        ]
        
        handled = handle_missing_data(data_with_missing)
        
        assert len(handled) >= 1  # 至少应该有一些数据
        assert all(item['open'] is not None for item in handled)
        assert all(item['close'] is not None for item in handled)
    
    def test_data_type_conversion(self):
        """测试数据类型转换"""
        def convert_data_types(data):
            if not data:
                return []
            
            df = pd.DataFrame(data)
            
            # 转换数值列
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 转换时间戳
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', errors='coerce')
            
            # 删除转换失败的行
            df = df.dropna()
            
            return df.to_dict('records')
        
        # 创建包含字符串数值的数据
        string_data = [
            {'timestamp': '1640995200', 'open': '100.5', 'high': '105.0', 'low': '95.0', 'close': '102.0', 'volume': '1000'},
            {'timestamp': '1641081600', 'open': '102.0', 'high': '107.0', 'low': '97.0', 'close': '104.0', 'volume': '1200'},
        ]
        
        converted = convert_data_types(string_data)
        
        assert len(converted) == 2
        assert all(isinstance(item['open'], (int, float)) for item in converted)
        assert all(isinstance(item['volume'], (int, float)) for item in converted)
    
    def test_data_statistics(self):
        """测试数据统计"""
        def calculate_data_statistics(data):
            if not data:
                return {}
            
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df = df.dropna()
            
            if len(df) == 0:
                return {}
            
            stats = {
                'count': len(df),
                'mean_price': float(df['close'].mean()),
                'std_price': float(df['close'].std()),
                'min_price': float(df['close'].min()),
                'max_price': float(df['close'].max()),
                'price_range': float(df['close'].max() - df['close'].min())
            }
            
            return stats
        
        stats = calculate_data_statistics(self.expected_formatted_data)
        
        assert 'count' in stats
        assert 'mean_price' in stats
        assert 'std_price' in stats
        assert 'min_price' in stats
        assert 'max_price' in stats
        assert 'price_range' in stats
        
        assert stats['count'] == 3
        assert stats['min_price'] <= stats['mean_price'] <= stats['max_price']
        assert stats['price_range'] >= 0

class TestDataValidation:
    """数据验证测试"""
    
    def test_ohlc_validation(self):
        """测试OHLC数据验证"""
        def validate_ohlc(open_price, high, low, close):
            if any(price <= 0 for price in [open_price, high, low, close]):
                return False
            
            if high < low:
                return False
            
            if close > high or close < low:
                return False
            
            return True
        
        # 测试有效数据
        assert validate_ohlc(100, 105, 95, 102) == True
        assert validate_ohlc(100, 100, 100, 100) == True  # 所有价格相同
        
        # 测试无效数据
        assert validate_ohlc(100, 95, 105, 102) == False  # high < low
        assert validate_ohlc(100, 105, 95, 110) == False  # close > high
        assert validate_ohlc(100, 105, 95, 90) == False   # close < low
        assert validate_ohlc(0, 105, 95, 102) == False    # 零价格
    
    def test_volume_validation(self):
        """测试交易量验证"""
        def validate_volume(volume):
            return isinstance(volume, (int, float)) and volume >= 0
        
        # 测试有效交易量
        assert validate_volume(1000) == True
        assert validate_volume(0) == True
        assert validate_volume(1000000.5) == True
        
        # 测试无效交易量
        assert validate_volume(-1000) == False
        assert validate_volume("1000") == False
        assert validate_volume(None) == False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
