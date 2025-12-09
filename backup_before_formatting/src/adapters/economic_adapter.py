#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
經濟數據適配器
從香港政府統計處API獲取GDP、貿易、零售銷售等經濟數據
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from .base_adapter import BaseAdapter, DataSourceInfo, DataPoint

logger = logging.getLogger(__name__)

class EconomicDataAdapter(BaseAdapter):
    """經濟數據適配器"""

    def __init__(self):
        # 使用多個經濟數據源
        self.data_sources = {
            "GD": DataSourceInfo(
                source_id="GD",
                name="GDP數據",
                description="香港本地生產總值",
                frequency="quarterly",
                unit="hkd_billion",
                api_endpoint="https://api.census.gov.hk/stock/v1/gdp.json"
            ),
            "RT": DataSourceInfo(
                source_id="RT",
                name="零售銷售數據",
                description="香港零售銷售總額",
                frequency="monthly",
                unit="hkd_billion",
                api_endpoint="https://api.census.gov.hk/stock/v1/retail-sales.json"
            ),
            "TR": DataSourceInfo(
                source_id="TR",
                name="貿易數據",
                description="香港進出口貿易統計",
                frequency="monthly",
                unit="hkd_billion",
                api_endpoint="https://api.census.gov.hk/stock/v1/trade.json"
            ),
            "TS": DataSourceInfo(
                source_id="TS",
                name="旅遊數據",
                description="香港旅遊業統計",
                frequency="monthly",
                unit="count",
                api_endpoint="https://api.census.gov.hk/stock/v1/tourism.json"
            ),
            "CP": DataSourceInfo(
                source_id="CP",
                name="CPI通脹數據",
                description="香港消費物價指數",
                frequency="monthly",
                unit="index",
                api_endpoint="https://api.census.gov.hk/stock/v1/cpi.json"
            ),
            "UE": DataSourceInfo(
                source_id="UE",
                name="失業率數據",
                description="香港失業率統計",
                frequency="monthly",
                unit="percent",
                api_endpoint="https://api.census.gov.hk/stock/v1/unemployment.json"
            )
        }

        # 使用第一個數據源作為主要信息
        primary_source = "GD"
        super().__init__(self.data_sources[primary_source])

        self.current_source = primary_source

    def set_source(self, source_id: str) -> None:
        """
        設置當前數據源

        Args:
            source_id: 數據源ID
        """
        if source_id not in self.data_sources:
            raise ValueError(f"Invalid source ID: {source_id}")

        self.current_source = source_id
        self.source_info = self.data_sources[source_id]
        logger.info(f"Switched to data source: {source_id}")

    def get_available_sources(self) -> List[DataSourceInfo]:
        """獲取所有可用數據源"""
        return list(self.data_sources.values())

    def fetch_data(self, start_date: datetime, end_date: datetime, source_id: str = None) -> pd.DataFrame:
        """
        從香港政府統計處API獲取經濟數據

        Args:
            start_date: 開始日期
            end_date: 結束日期
            source_id: 數據源ID（可選，默認使用當前源）

        Returns:
            DataFrame with economic data
        """
        if source_id:
            old_source = self.current_source
            self.set_source(source_id)

        try:
            # 構建API請求參數
            params = {
                "lang": "en",
                "from": start_date.strftime("%Y-%m"),
                "to": end_date.strftime("%Y-%m")
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
            df = self._parse_economic_response(data, self.current_source)

            logger.info(f"Fetched {len(df)} {self.current_source} records from census API")

            if source_id:
                self.set_source(old_source)  # 恢復原來的源

            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch {self.current_source} data: {e}")
            if source_id:
                self.set_source(old_source)
            return self._get_fallback_data(start_date, end_date, self.current_source)

    def fetch_all_sources(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """
        獲取所有數據源的數據

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            字典 {source_id: DataFrame}
        """
        all_data = {}

        for source_id in self.data_sources.keys():
            try:
                data = self.fetch_data(start_date, end_date, source_id)
                if not data.empty:
                    all_data[source_id] = data
            except Exception as e:
                logger.error(f"Failed to fetch data for {source_id}: {e}")

        return all_data

    def _parse_economic_response(self, data: Dict[str, Any], source_id: str) -> pd.DataFrame:
        """解析香港政府統計處API響應"""
        if source_id not in data or not isinstance(data[source_id], list):
            raise ValueError(f"Invalid API response format for {source_id}")

        records = data[source_id]
        parsed_data = []

        for record in records:
            try:
                # 根據不同數據源解析日期和數值
                if source_id == "GD":  # GDP數據
                    date_str = record.get('quarter', '')
                    value = record.get('gdp_value')
                    data_type = 'quarterly'

                elif source_id == "RT":  # 零售銷售數據
                    date_str = record.get('month', '')
                    value = record.get('retail_value')
                    data_type = 'monthly'

                elif source_id == "TR":  # 貿易數據
                    date_str = record.get('month', '')
                    value = record.get('total_trade')
                    data_type = 'monthly'

                elif source_id == "TS":  # 旅遊數據
                    date_str = record.get('month', '')
                    value = record.get('visitor_arrivals')
                    data_type = 'monthly'

                elif source_id == "CP":  # CPI數據
                    date_str = record.get('month', '')
                    value = record.get('cpi_index')
                    data_type = 'monthly'

                elif source_id == "UE":  # 失業率數據
                    date_str = record.get('month', '')
                    value = record.get('unemployment_rate')
                    data_type = 'monthly'

                else:
                    continue

                if not date_str or value is None:
                    continue

                # 解析日期
                date_obj = self._parse_date(date_str, data_type)

                # 轉換數值
                try:
                    numeric_value = float(value)
                except (ValueError, TypeError):
                    continue

                parsed_data.append({
                    'timestamp': date_obj,
                    'value': numeric_value,
                    'source_id': source_id,
                    'data_type': data_type
                })

            except (ValueError, KeyError) as e:
                logger.debug(f"Failed to parse record for {source_id}: {e}")
                continue

        if not parsed_data:
            raise ValueError(f"No valid {source_id} data found in response")

        # 創建DataFrame
        df = pd.DataFrame(parsed_data)

        # 設置時間索引
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        return df

    def _parse_date(self, date_str: str, data_type: str) -> datetime:
        """解析日期字符串"""
        if data_type == 'quarterly':
            # 格式: "2023Q1"
            year, quarter = date_str.split('Q')
            month = (int(quarter) - 1) * 3 + 1
            return datetime(int(year), month, 1)
        else:
            # 格式: "2023-01" 或 "2023/01"
            date_str = date_str.replace('/', '-')
            return datetime.strptime(date_str, "%Y-%m")

    def _get_fallback_data(self, start_date: datetime, end_date: datetime, source_id: str) -> pd.DataFrame:
        """
        獲取備用數據（本地文件或模擬數據）

        Args:
            start_date: 開始日期
            end_date: 結束日期
            source_id: 數據源ID

        Returns:
            DataFrame with fallback economic data
        """
        logger.warning(f"Using fallback {source_id} data source")

        # 嘗試讀取本地文件
        try:
            local_file = f"data/real_data/{source_id.lower()}_data.json"
            with open(local_file, 'r', encoding='utf-8') as f:
                local_data = json.load(f)

            # 解析本地數據
            fallback_data = []
            for record in local_data:
                try:
                    date_str = record.get('date', '')
                    if not date_str:
                        continue

                    # 解析日期
                    data_type = self.data_sources[source_id].frequency
                    date_obj = self._parse_date(date_str, data_type)

                    if start_date <= date_obj <= end_date:
                        value = float(record.get('value', 0))
                        fallback_data.append({
                            'timestamp': date_obj,
                            'value': value,
                            'source_id': source_id,
                            'data_type': data_type
                        })

                except (ValueError, KeyError) as e:
                    logger.debug(f"Failed to parse local record: {e}")
                    continue

            if fallback_data:
                df = pd.DataFrame(fallback_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                logger.info(f"Using {len(df)} records from local {source_id} file")
                return df

        except FileNotFoundError:
            logger.warning(f"Local {source_id} file not found")
        except Exception as e:
            logger.error(f"Failed to read local {source_id} data: {e}")

        # 如果本地數據不可用，生成模擬數據
        return self._generate_mock_data(start_date, end_date, source_id)

    def _generate_mock_data(self, start_date: datetime, end_date: datetime, source_id: str) -> pd.DataFrame:
        """生成模擬經濟數據"""
        logger.warning(f"Generating mock {source_id} data")

        # 根據數據源生成不同的日期頻率
        if self.data_sources[source_id].frequency == 'quarterly':
            dates = pd.date_range(start=start_date, end=end_date, freq='Q')
        else:
            dates = pd.date_range(start=start_date, end=end_date, freq='M')

        # 模擬各數據源的基準值
        base_values = {
            "GD": 700.0,    # GDP (十億港元)
            "RT": 35.0,     # 零售銷售 (十億港元)
            "TR": 80.0,     # 貿易總額 (十億港元)
            "TS": 3000000,  # 旅遊人次
            "CP": 105.0,    # CPI指數
            "UE": 3.0       # 失業率 (%)
        }

        base_value = base_values.get(source_id, 100.0)
        mock_data = []
        import random

        for date in dates:
            # 添加隨機波動和趨勢
            trend_factor = 1.0 + (date - dates[0]).days / 365.0 * 0.02  # 年增長2%
            random_factor = random.uniform(0.98, 1.02)  # ±2%隨機波動
            value = base_value * trend_factor * random_factor

            mock_data.append({
                'timestamp': date,
                'value': round(value, 2) if source_id != "TS" else int(value),
                'source_id': source_id,
                'data_type': self.data_sources[source_id].frequency
            })

        df = pd.DataFrame(mock_data)
        df = df.set_index('timestamp')

        logger.info(f"Generated {len(df)} mock {source_id} records")
        return df

    def validate_data(self, data: pd.DataFrame) -> bool:
        """驗證經濟數據"""
        if len(data) == 0:
            logger.error("No data to validate")
            return False

        # 檢查必要列
        required_columns = ['value', 'source_id']
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"Missing required column: {col}")
                return False

        # 檢查數據源ID
        valid_sources = set(self.data_sources.keys())
        data_sources = set(data['source_id'].unique())
        invalid_sources = data_sources - valid_sources
        if invalid_sources:
            logger.error(f"Invalid source IDs found: {invalid_sources}")
            return False

        # 檢查數值合理性（根據不同數據源）
        for source_id in data_sources:
            source_data = data[data['source_id'] == source_id]
            if source_id == "CP" and not source_data.empty:  # CPI應該在50-200範圍
                invalid_cpi = source_data[(source_data['value'] < 50) | (source_data['value'] > 200)]
                if len(invalid_cpi) > 0:
                    logger.warning(f"Found {len(invalid_cpi)} unreasonable CPI values")

            elif source_id == "UE" and not source_data.empty:  # 失業率應該在0-20%範圍
                invalid_ue = source_data[(source_data['value'] < 0) | (source_data['value'] > 20)]
                if len(invalid_ue) > 0:
                    logger.warning(f"Found {len(invalid_ue)} unreasonable unemployment rates")

        logger.info(f"Economic data validation passed: {len(data)} records")
        return True

    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """標準化經濟數據"""
        # 確保時間索引
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'timestamp' in data.columns:
                data['timestamp'] = pd.to_datetime(data['timestamp'])
                data = data.set_index('timestamp')
            else:
                raise ValueError("No valid timestamp column found")

        # 排序
        data = data.sort_index()

        # 按數據源分別處理缺失值
        for source_id in data['source_id'].unique():
            source_mask = data['source_id'] == source_id
            data.loc[source_mask, 'value'] = data.loc[source_mask, 'value'].ffill()

        return data

    def get_latest_values(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有數據源的最新數值

        Returns:
            字典 {source_id: {value: latest_value, date: latest_date}}
        """
        latest_values = {}

        for source_id in self.data_sources.keys():
            try:
                source_data = self.fetch_data(
                    datetime.now() - timedelta(days=365),
                    datetime.now(),
                    source_id
                )

                if not source_data.empty:
                    latest_record = source_data.iloc[-1]
                    latest_values[source_id] = {
                        'value': float(latest_record['value']),
                        'date': latest_record.name.isoformat(),
                        'name': self.data_sources[source_id].name,
                        'unit': self.data_sources[source_id].unit
                    }

            except Exception as e:
                logger.error(f"Failed to get latest data for {source_id}: {e}")

        return latest_values

# 創建全局實例
_economic_adapter = None

def get_economic_adapter() -> EconomicDataAdapter:
    """獲取經濟數據適配器實例"""
    global _economic_adapter
    if _economic_adapter is None:
        _economic_adapter = EconomicDataAdapter()
    return _economic_adapter