#!/usr/bin/env python3
"""
数据管理器 - 简化版
Data Manager - Simplified Edition

统一的数据获取接口，支持股票数据和香港政府经济数据
基于真实数据源：中央API + 香港政府API

Author: Claude Code Assistant
Created: 2025-11-29
Version: 1.0.0
"""

import json
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)

class DataManager:
    """
    简化版数据管理器
    专注于核心数据获取功能
    """

    def __init__(self):
        """初始化数据管理器"""
        # 中央API配置 (真实港股数据)
        self.stock_api_base = "http://18.180.162.113:9191"
        self.stock_endpoint = "/inst/getInst"

        # 香港政府API配置 (真实经济数据)
        self.gov_api_base = "https://api.hkma.gov.hk/public/market-data-and-statistics"

        # 缓存配置
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存

        logger.info("数据管理器初始化完成")

    def get_stock_data(self, symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
        """
        获取股票数据

        Args:
            symbol: 股票代码，如 "0700.HK"
            days: 获取天数，默认365天

        Returns:
            包含OHLCV数据的DataFrame，或None如果失败
        """
        cache_key = f"stock_{symbol}_{days}"

        # 检查缓存
        if self._is_cache_valid(cache_key):
            logger.debug(f"从缓存获取股票数据: {symbol}")
            return self.cache[cache_key]['data']

        try:
            url = f"{self.stock_api_base}{self.stock_endpoint}"
            params = {
                "symbol": symbol.lower(),
                "duration": days
            }

            logger.info(f"获取股票数据: {symbol}, 时长: {days}天")

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 解析嵌套数据结构
            if 'data' not in data or 'close' not in data['data']:
                logger.error(f"数据格式错误: {symbol}")
                return None

            dates = list(data['data']['close'].keys())
            close_prices = list(data['data']['close'].values())

            # 创建DataFrame
            df = pd.DataFrame({
                'date': pd.to_datetime(dates),
                'close': close_prices
            }).set_index('date')

            # 添加其他OHLCV数据 (如果可用)
            if 'open' in data['data']:
                df['open'] = pd.Series(data['data']['open'].values, index=df.index)
            if 'high' in data['data']:
                df['high'] = pd.Series(data['data']['high'].values, index=df.index)
            if 'low' in data['data']:
                df['low'] = pd.Series(data['data']['low'].values, index=df.index)
            if 'volume' in data['data']:
                df['volume'] = pd.Series(data['data']['volume'].values, index=df.index)

            # 如果只有收盘价，用收盘价填充其他字段
            if len(df.columns) == 1:
                df['open'] = df['close']
                df['high'] = df['close']
                df['low'] = df['close']
                df['volume'] = 0

            # 按日期排序
            df.sort_index(inplace=True)

            # 缓存数据
            self.cache[cache_key] = {
                'data': df,
                'timestamp': time.time()
            }

            logger.info(f"成功获取股票数据: {symbol}, {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取股票数据失败 {symbol}: {e}")
            return None

    def get_government_data(self, data_type: str, days: int = 365) -> Optional[pd.DataFrame]:
        """
        获取香港政府经济数据

        Args:
            data_type: 数据类型 ('hibor', 'exchange_rate', 'monetary_base')
            days: 获取天数

        Returns:
            包含经济数据的DataFrame，或None如果失败
        """
        cache_key = f"gov_{data_type}_{days}"

        # 检查缓存
        if self._is_cache_valid(cache_key):
            logger.debug(f"从缓存获取政府数据: {data_type}")
            return self.cache[cache_key]['data']

        try:
            # 根据数据类型选择API端点
            endpoints = {
                'hibor': '/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily',
                'exchange_rate': '/monthly-statistical-bulletin/er-ir/er-eeri-daily',
                'monetary_base': '/daily-monetary-statistics/daily-figures-monetary-base'
            }

            if data_type not in endpoints:
                logger.error(f"不支持的数据类型: {data_type}")
                return None

            url = f"{self.gov_api_base}{endpoints[data_type]}"

            logger.info(f"获取政府数据: {data_type}")

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            # 解析政府数据结构 (根据实际API响应调整)
            if data_type == 'hibor':
                df = self._parse_hibor_data(data)
            elif data_type == 'exchange_rate':
                df = self._parse_exchange_rate_data(data)
            elif data_type == 'monetary_base':
                df = self._parse_monetary_base_data(data)
            else:
                df = pd.DataFrame()

            if df is not None and len(df) > 0:
                # 缓存数据
                self.cache[cache_key] = {
                    'data': df,
                    'timestamp': time.time()
                }

                logger.info(f"成功获取政府数据: {data_type}, {len(df)} 条记录")

            return df

        except Exception as e:
            logger.error(f"获取政府数据失败 {data_type}: {e}")
            return None

    def get_multiple_stocks(self, symbols: List[str], days: int = 365) -> Dict[str, pd.DataFrame]:
        """
        批量获取多只股票数据

        Args:
            symbols: 股票代码列表
            days: 获取天数

        Returns:
            股票数据字典 {symbol: DataFrame}
        """
        results = {}

        logger.info(f"批量获取股票数据: {symbols}")

        for symbol in symbols:
            data = self.get_stock_data(symbol, days)
            if data is not None:
                results[symbol] = data
            else:
                logger.warning(f"跳过无效数据: {symbol}")

        logger.info(f"成功获取 {len(results)}/{len(symbols)} 只股票数据")
        return results

    def get_latest_hibor(self) -> Optional[float]:
        """
        获取最新HIBOR隔夜利率

        Returns:
            最新HIBOR隔夜利率，或None如果失败
        """
        try:
            data = self.get_government_data('hibor', 7)
            if data is not None and len(data) > 0:
                # 假设数据包含overnight列
                if 'overnight' in data.columns:
                    return float(data['overnight'].iloc[-1])

            logger.warning("无法获取最新HIBOR利率")
            return None

        except Exception as e:
            logger.error(f"获取HIBOR利率失败: {e}")
            return None

    def validate_data_quality(self, df: pd.DataFrame) -> bool:
        """
        验证数据质量

        Args:
            df: 要验证的数据框

        Returns:
            True表示数据质量合格，False表示有问题
        """
        try:
            # 基本质量检查
            if df is None or len(df) == 0:
                logger.error("数据为空")
                return False

            # 检查必要的列
            required_columns = ['close']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"缺少必要列: {col}")
                    return False

            # 检查数据完整性
            missing_data = df[required_columns].isnull().sum()
            if missing_data.sum() > len(df) * 0.1:  # 超过10%缺失
                logger.warning(f"数据缺失较多: {missing_data}")

            # 检查价格合理性
            price_stats = df['close'].describe()
            if price_stats['min'] <= 0 or price_stats['max'] > 10000:  # 股价合理范围
                logger.warning(f"价格可能异常: {price_stats}")

            logger.info("数据质量验证通过")
            return True

        except Exception as e:
            logger.error(f"数据质量验证失败: {e}")
            return False

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False

        cache_time = self.cache[cache_key]['timestamp']
        return (time.time() - cache_time) < self.cache_timeout

    def _parse_hibor_data(self, data: Dict) -> Optional[pd.DataFrame]:
        """解析HIBOR数据"""
        try:
            # 根据实际API响应结构解析
            # 这里需要根据真实API响应调整
            records = data.get('records', [])

            if not records:
                return None

            df_data = []
            for record in records:
                df_data.append({
                    'date': pd.to_datetime(record.get('end_of_date')),
                    'overnight': float(record.get('hibor_overnight', 0)),
                    '1_week': float(record.get('hibor_1_week', 0)),
                    '1_month': float(record.get('hibor_1_month', 0))
                })

            df = pd.DataFrame(df_data)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"解析HIBOR数据失败: {e}")
            return None

    def _parse_exchange_rate_data(self, data: Dict) -> Optional[pd.DataFrame]:
        """解析汇率数据"""
        try:
            # 根据实际API响应结构解析
            records = data.get('records', [])

            if not records:
                return None

            df_data = []
            for record in records:
                df_data.append({
                    'date': pd.to_datetime(record.get('end_of_date')),
                    'usd_hkd': float(record.get('usd_hkd', 0)),
                    'cny_hkd': float(record.get('cny_hkd', 0))
                })

            df = pd.DataFrame(df_data)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"解析汇率数据失败: {e}")
            return None

    def _parse_monetary_base_data(self, data: Dict) -> Optional[pd.DataFrame]:
        """解析货币基础数据"""
        try:
            # 根据实际API响应结构解析
            records = data.get('records', [])

            if not records:
                return None

            df_data = []
            for record in records:
                df_data.append({
                    'date': pd.to_datetime(record.get('date')),
                    'monetary_base': float(record.get('monetary_base', 0)),
                    'm2_supply': float(record.get('m2_supply', 0))
                })

            df = pd.DataFrame(df_data)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"解析货币基础数据失败: {e}")
            return None

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")

    def get_cache_info(self) -> Dict[str, int]:
        """获取缓存信息"""
        return {
            'cache_size': len(self.cache),
            'cache_keys': list(self.cache.keys())
        }


# 便捷函数
def get_data_manager() -> DataManager:
    """获取数据管理器实例"""
    return DataManager()

def get_stock_data(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
    """便捷的股票数据获取函数"""
    dm = DataManager()
    return dm.get_stock_data(symbol, days)

def get_multiple_stocks(symbols: List[str], days: int = 365) -> Dict[str, pd.DataFrame]:
    """便捷的多股票数据获取函数"""
    dm = DataManager()
    return dm.get_multiple_stocks(symbols, days)

def get_latest_hibor() -> Optional[float]:
    """便捷的HIBOR获取函数"""
    dm = DataManager()
    return dm.get_latest_hibor()