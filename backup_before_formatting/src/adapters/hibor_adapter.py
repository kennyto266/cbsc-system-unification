#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HIBOR (香港銀行同業拆息) 數據適配器
從香港金融管理局API獲取HIBOR利率數據
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from .base_adapter import BaseAdapter, DataSourceInfo, DataPoint

logger = logging.getLogger(__name__)

class HIBORAdapter(BaseAdapter):
    """HIBOR數據適配器"""

    def __init__(self):
        source_info = DataSourceInfo(
            source_id="HB",
            name="HIBOR利率數據",
            description="香港銀行同業拆息利率",
            frequency="daily",
            unit="percent",
            api_endpoint="https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily"
        )
        super().__init__(source_info)

        # HIBOR期限配置
        self.tenors = {
            "ON": "隔夜",
            "1W": "1週",
            "1M": "1個月",
            "2M": "2個月",
            "3M": "3個月",
            "6M": "6個月",
            "12M": "12個月"
        }

    def fetch_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        從HKMA API獲取HIBOR數據

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            DataFrame with HIBOR rates for all tenors
        """
        try:
            # 構建API請求參數
            params = {
                "from": start_date.strftime("%d-%m-%Y"),
                "to": end_date.strftime("%d-%m-%Y")
            }

            # 發送API請求
            response = requests.get(
                self.source_info.api_endpoint,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            # 解析JSON響應
            data = response.json()

            # 轉換為DataFrame
            df = self._parse_hibor_response(data)

            logger.info(f"Fetched {len(df)} HIBOR records from HKMA API")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch HIBOR data: {e}")
            # 嘗試使用備用數據源或本地文件
            return self._get_fallback_data(start_date, end_date)

    def _parse_hibor_response(self, data: Dict[str, Any]) -> pd.DataFrame:
        """解析HKMA API響應"""
        if 'result' not in data or 'records' not in data['result']:
            raise ValueError("Invalid HKMA API response format")

        records = data['result']['records']
        parsed_data = []

        for record in records:
            try:
                # 提取日期
                date_str = record.get('end_of_date')
                if not date_str:
                    continue

                # 轉換日期格式
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

                # 提取各期限的利率
                for tenor_code, tenor_name in self.tenors.items():
                    rate_key = f"hibor_{tenor_code.lower()}"
                    rate_value = record.get(rate_key)

                    if rate_value is not None:
                        # 轉換利率值（可能是字符串格式）
                        try:
                            rate = float(rate_value)
                        except (ValueError, TypeError):
                            continue

                        parsed_data.append({
                            'timestamp': date_obj,
                            'tenor': tenor_code,
                            'tenor_name': tenor_name,
                            'value': rate
                        })

            except (ValueError, KeyError) as e:
                logger.debug(f"Failed to parse record: {e}")
                continue

        if not parsed_data:
            raise ValueError("No valid HIBOR data found in response")

        # 創建DataFrame
        df = pd.DataFrame(parsed_data)

        # 設置時間索引
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        return df

    def _get_fallback_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        獲取備用數據（本地文件或模擬數據）

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            DataFrame with fallback HIBOR data
        """
        logger.warning("Using fallback HIBOR data source")

        # 嘗試讀取本地文件
        try:
            local_file = "data/real_data/hibor_data.json"
            with open(local_file, 'r', encoding='utf-8') as f:
                local_data = json.load(f)

            # 解析本地數據
            fallback_data = []
            for record in local_data:
                try:
                    date_obj = datetime.strptime(record['date'], "%Y-%m-%d")

                    if start_date <= date_obj <= end_date:
                        for tenor_code, tenor_name in self.tenors.items():
                            rate_key = tenor_code.lower()
                            if rate_key in record:
                                rate = float(record[rate_key])
                                fallback_data.append({
                                    'timestamp': date_obj,
                                    'tenor': tenor_code,
                                    'tenor_name': tenor_name,
                                    'value': rate
                                })

                except (ValueError, KeyError) as e:
                    logger.debug(f"Failed to parse local record: {e}")
                    continue

            if fallback_data:
                df = pd.DataFrame(fallback_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                logger.info(f"Using {len(df)} records from local HIBOR file")
                return df

        except FileNotFoundError:
            logger.warning("Local HIBOR file not found")
        except Exception as e:
            logger.error(f"Failed to read local HIBOR data: {e}")

        # 如果本地數據不可用，生成模擬數據
        return self._generate_mock_data(start_date, end_date)

    def _generate_mock_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """生成模擬HIBOR數據"""
        logger.warning("Generating mock HIBOR data")

        # 生成日期範圍
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # 模擬各期限的基準利率
        base_rates = {
            "ON": 3.15,
            "1W": 3.45,
            "1M": 3.78,
            "2M": 4.02,
            "3M": 4.25,
            "6M": 4.67,
            "12M": 5.12
        }

        mock_data = []
        for date in dates:
            # 跳過週末（生成工作日數據）
            if date.weekday() >= 5:
                continue

            for tenor_code, base_rate in base_rates.items():
                # 添加隨機波動
                import random
                rate = base_rate + random.uniform(-0.05, 0.05)

                mock_data.append({
                    'timestamp': date,
                    'tenor': tenor_code,
                    'tenor_name': self.tenors[tenor_code],
                    'value': round(rate, 4)
                })

        df = pd.DataFrame(mock_data)
        df = df.set_index('timestamp')

        logger.info(f"Generated {len(df)} mock HIBOR records")
        return df

    def validate_data(self, data: pd.DataFrame) -> bool:
        """驗證HIBOR數據"""
        if len(data) == 0:
            logger.error("No data to validate")
            return False

        # 檢查必要列
        required_columns = ['value', 'tenor']
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"Missing required column: {col}")
                return False

        # 檢查數據範圍
        invalid_rates = data[(data['value'] < 0) | (data['value'] > 100)]
        if len(invalid_rates) > 0:
            logger.warning(f"Found {len(invalid_rates)} invalid rate values")
            # 不返回False，只是警告

        # 檢查期限
        valid_tenors = set(self.tenors.keys())
        invalid_tenors = set(data['tenor'].unique()) - valid_tenors
        if invalid_tenors:
            logger.error(f"Invalid tenors found: {invalid_tenors}")
            return False

        logger.info(f"HIBOR data validation passed: {len(data)} records")
        return True

    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """標準化HIBOR數據"""
        # 確保時間索引
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.set_index('timestamp')
            else:
                raise ValueError("No valid timestamp column found")

        # 排序
        data = data.sort_index()

        # 填充缺失值（使用前一個交易日的數據）
        data = data.groupby('tenor')['value'].ffill()

        # 轉換百分比為小數（可選，根據需要）
        # data['value'] = data['value'] / 100

        return data

    def get_tenor_data(self, tenor: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        獲取特定期限的HIBOR數據

        Args:
            tenor: 期限代碼 (ON, 1W, 1M, etc.)
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            特定期限的HIBOR數據
        """
        if tenor not in self.tenors:
            raise ValueError(f"Invalid tenor: {tenor}")

        all_data = self.get_data(start_date, end_date)
        return all_data[all_data['tenor'] == tenor].copy()

    def get_latest_rates(self) -> Dict[str, float]:
        """
        獲取最新的HIBOR利率

        Returns:
            最新利率字典 {tenor: rate}
        """
        try:
            latest_data = self.get_latest_data(days=7)
            latest_rates = {}

            for tenor in self.tenors.keys():
                tenor_data = latest_data[latest_data['tenor'] == tenor]
                if not tenor_data.empty:
                    latest_rates[tenor] = float(tenor_data['value'].iloc[-1])

            return latest_rates

        except Exception as e:
            logger.error(f"Failed to get latest HIBOR rates: {e}")
            return {}

# 創建全局實例
_hibor_adapter = None

def get_hibor_adapter() -> HIBORAdapter:
    """獲取HIBOR適配器實例"""
    global _hibor_adapter
    if _hibor_adapter is None:
        _hibor_adapter = HIBORAdapter()
    return _hibor_adapter