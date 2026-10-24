#!/usr/bin/env python3
"""
HKMA Data Adapter
香港金管局数据适配器
基于现有实现的简化版本
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import requests
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class HKMADataAdapter:
    """
    HKMA数据适配器
    提供简化的香港金管局数据获取功能
    """

    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # HKMA API端点配置
        self.api_endpoints = {
            'hibor': {
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily',
                'name': '香港银行同业拆息率',
                'cache_file': 'hibor_data.json'
            },
            'monetary_base': {
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base',
                'name': '货币基础',
                'cache_file': 'monetary_base_data.json'
            },
            'exchange_rate': {
                'url': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily',
                'name': '汇率数据',
                'cache_file': 'exchange_rate_data.json'
            }
        }

        # HIBOR期限配置
        self.hibor_tenors = {
            'ON': '隔夜',
            '1W': '1週',
            '1M': '1個月',
            '2M': '2個月',
            '3M': '3個月',
            '6M': '6個月',
            '12M': '12個月',
        }

        logger.info("HKMA Data Adapter 初始化完成")

    def get_hibor_data(
        self,
        start_date: datetime,
        end_date: datetime,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取HIBOR利率数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            HIBOR数据DataFrame
        """
        return self._get_data('hibor', start_date, end_date, use_cache)

    def get_monetary_base_data(
        self,
        start_date: datetime,
        end_date: datetime,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取货币基础数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            货币基础数据DataFrame
        """
        return self._get_data('monetary_base', start_date, end_date, use_cache)

    def get_exchange_rate_data(
        self,
        start_date: datetime,
        end_date: datetime,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取汇率数据

        Args:
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            汇率数据DataFrame
        """
        return self._get_data('exchange_rate', start_date, end_date, use_cache)

    def _get_data(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        通用数据获取方法

        Args:
            data_type: 数据类型
            start_date: 开始日期
            end_date: 结束日期
            use_cache: 是否使用缓存

        Returns:
            数据DataFrame
        """
        if data_type not in self.api_endpoints:
            raise ValueError(f"不支持的数据类型: {data_type}")

        endpoint = self.api_endpoints[data_type]
        cache_file = self.cache_dir / endpoint['cache_file']

        # 尝试使用缓存数据
        if use_cache and cache_file.exists():
            cached_data = self._load_cached_data(cache_file, start_date, end_date)
            if cached_data is not None:
                logger.info(f"使用缓存数据: {data_type}")
                return cached_data

        # 从API获取数据
        try:
            logger.info(f"从HKMA API获取数据: {data_type}")
            api_data = self._fetch_from_api(endpoint['url'])

            if api_data is not None:
                # 保存到缓存
                self._save_cached_data(cache_file, api_data)

                # 转换为DataFrame
                df = self._parse_data(api_data, data_type)

                if df is not None:
                    # 按日期范围过滤
                    df = self._filter_by_date_range(df, start_date, end_date)
                    logger.info(f"成功获取 {len(df)} 条 {data_type} 数据")
                    return df

        except Exception as e:
            logger.error(f"获取 {data_type} 数据失败: {e}")

        # 回退到生成模拟数据
        logger.warning(f"生成模拟数据: {data_type}")
        return self._generate_mock_data(data_type, start_date, end_date)

    def _fetch_from_api(self, url: str) -> Optional[Dict]:
        """从HKMA API获取数据"""
        try:
            response = requests.get(
                url,
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return None

    def _parse_data(self, data: Dict, data_type: str) -> Optional[pd.DataFrame]:
        """解析API响应数据"""
        try:
            if data_type == 'hibor':
                return self._parse_hibor_data(data)
            elif data_type == 'monetary_base':
                return self._parse_monetary_base_data(data)
            elif data_type == 'exchange_rate':
                return self._parse_exchange_rate_data(data)
            else:
                logger.warning(f"未知数据类型: {data_type}")
                return None

        except Exception as e:
            logger.error(f"解析 {data_type} 数据失败: {e}")
            return None

    def _parse_hibor_data(self, data: Dict) -> pd.DataFrame:
        """解析HIBOR数据"""
        if "result" not in data or "records" not in data["result"]:
            raise ValueError("HIBOR数据格式错误")

        records = data["result"]["records"]
        parsed_data = []

        for record in records:
            try:
                date_str = record.get("end_of_date")
                if not date_str:
                    continue

                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                # 提取各期限利率
                for tenor_code, tenor_name in self.hibor_tenors.items():
                    rate_key = f"hibor_{tenor_code.lower()}"
                    rate_value = record.get(rate_key)

                    if rate_value is not None:
                        try:
                            rate = float(rate_value)
                        except (ValueError, TypeError):
                            continue

                        parsed_data.append({
                            'date': date_obj,
                            'tenor': tenor_code,
                            'tenor_name': tenor_name,
                            'rate': rate
                        })

            except (ValueError, KeyError) as e:
                logger.debug(f"解析HIBOR记录失败: {e}")
                continue

        if not parsed_data:
            raise ValueError("没有有效的HIBOR数据")

        df = pd.DataFrame(parsed_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df.sort_index()

    def _parse_monetary_base_data(self, data: Dict) -> pd.DataFrame:
        """解析货币基础数据"""
        if "result" not in data or "records" not in data["result"]:
            raise ValueError("货币基础数据格式错误")

        records = data["result"]["records"]
        parsed_data = []

        for record in records:
            try:
                date_str = record.get("end_of_date")
                if not date_str:
                    continue

                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                # 提取货币基础数据
                for key, value in record.items():
                    if key not in ['end_of_date'] and isinstance(value, (int, float, str)):
                        try:
                            amount = float(value)
                            parsed_data.append({
                                'date': date_obj,
                                'metric': key,
                                'value': amount
                            })
                        except (ValueError, TypeError):
                            continue

            except (ValueError, KeyError) as e:
                logger.debug(f"解析货币基础记录失败: {e}")
                continue

        if not parsed_data:
            raise ValueError("没有有效的货币基础数据")

        df = pd.DataFrame(parsed_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df.sort_index()

    def _parse_exchange_rate_data(self, data: Dict) -> pd.DataFrame:
        """解析汇率数据"""
        if "result" not in data or "records" not in data["result"]:
            raise ValueError("汇率数据格式错误")

        records = data["result"]["records"]
        parsed_data = []

        for record in records:
            try:
                date_str = record.get("end_of_date")
                if not date_str:
                    continue

                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                # 提取汇率数据
                for key, value in record.items():
                    if key not in ['end_of_date'] and isinstance(value, (int, float, str)):
                        try:
                            rate = float(value)
                            parsed_data.append({
                                'date': date_obj,
                                'currency': key,
                                'exchange_rate': rate
                            })
                        except (ValueError, TypeError):
                            continue

            except (ValueError, KeyError) as e:
                logger.debug(f"解析汇率记录失败: {e}")
                continue

        if not parsed_data:
            raise ValueError("没有有效的汇率数据")

        df = pd.DataFrame(parsed_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df.sort_index()

    def _filter_by_date_range(
        self,
        df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """按日期范围过滤数据"""
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        return df[(df.index >= start_dt) & (df.index <= end_dt)]

    def _load_cached_data(
        self,
        cache_file: Path,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """加载缓存数据"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)

            # 转换为DataFrame
            if cached_data:
                df = pd.DataFrame(cached_data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)

                # 按日期范围过滤
                return self._filter_by_date_range(df, start_date, end_date)

        except Exception as e:
            logger.warning(f"加载缓存数据失败: {e}")

        return None

    def _save_cached_data(self, cache_file: Path, data: Dict) -> None:
        """保存数据到缓存"""
        try:
            # 保存原始JSON数据
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"数据已缓存到: {cache_file}")

        except Exception as e:
            logger.warning(f"保存缓存数据失败: {e}")

    def _generate_mock_data(
        self,
        data_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """生成模拟数据"""
        logger.info(f"生成模拟数据: {data_type}")

        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        trading_days = dates[dates.weekday < 5]  # 工作日

        if data_type == 'hibor':
            # HIBOR模拟数据
            base_rates = {
                'ON': 3.15, '1W': 3.45, '1M': 3.78,
                '2M': 4.02, '3M': 4.25, '6M': 4.67, '12M': 5.12
            }
            mock_data = []
            for date in trading_days:
                for tenor_code, base_rate in base_rates.items():
                    rate = base_rate + np.random.normal(0, 0.05)
                    mock_data.append({
                        'date': date,
                        'tenor': tenor_code,
                        'tenor_name': self.hibor_tenors[tenor_code],
                        'rate': round(rate, 4)
                    })
            return pd.DataFrame(mock_data)

        else:
            # 其他数据类型的模拟
            mock_data = []
            for date in trading_days:
                mock_data.append({
                    'date': date,
                    'metric': 'mock_value',
                    'value': np.random.normal(1000000, 100000)
                })
            return pd.DataFrame(mock_data)

    def get_latest_hibor_rates(self) -> Dict[str, float]:
        """获取最新的HIBOR利率"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            hibor_data = self.get_hibor_data(start_date, end_date)

            if not hibor_data.empty:
                latest_rates = {}
                for tenor in self.hibor_tenors.keys():
                    tenor_data = hibor_data[hibor_data['tenor'] == tenor]
                    if not tenor_data.empty:
                        latest_rates[tenor] = float(tenor_data['rate'].iloc[-1])

                return latest_rates

        except Exception as e:
            logger.error(f"获取最新HIBOR利率失败: {e}")

        # 返回默认值
        return {
            'ON': 3.15, '1W': 3.45, '1M': 3.78,
            '2M': 4.02, '3M': 4.25, '6M': 4.67, '12M': 5.12
        }

    def get_comprehensive_data(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        获取所有类型的HKMA数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            包含所有数据类型的字典
        """
        logger.info("获取综合HKMA数据")

        data = {}
        for data_type in self.api_endpoints.keys():
            try:
                data[data_type] = self._get_data(data_type, start_date, end_date)
                logger.info(f"成功获取 {data_type} 数据: {len(data[data_type])} 条记录")
            except Exception as e:
                logger.warning(f"获取 {data_type} 数据失败: {e}")
                data[data_type] = pd.DataFrame()

        return data