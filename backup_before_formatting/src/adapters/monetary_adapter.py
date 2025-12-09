#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
貨幣基礎數據適配器
從香港金融管理局API獲取貨幣基礎統計數據
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from .base_adapter import BaseAdapter, DataSourceInfo, DataPoint

logger = logging.getLogger(__name__)

class MonetaryBaseAdapter(BaseAdapter):
    """貨幣基礎數據適配器"""

    def __init__(self):
        source_info = DataSourceInfo(
            source_id="MB",
            name="貨幣基礎數據",
            description="香港貨幣基礎統計數據，包括貨幣基礎、負債證明書等",
            frequency="daily",
            unit="hkd_billion",
            api_endpoint="https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base"
        )
        super().__init__(source_info)

        # 貨幣基礎組件配置
        self.components = {
            "MB": "貨幣基礎總額",
            "CL": "負債證明書",
            "GC": "政府發行的銀行紙幣及硬幣",
            "EF": "其他負債",
            "BOJ": "從其他銀行借入款項",
            "BIL": "未償還外匯基金票據及債券",
            "IR": "利率"
        }

    def fetch_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        從HKMA API獲取貨幣基礎數據

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            DataFrame with monetary base data
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
            df = self._parse_monetary_response(data)

            logger.info(f"Fetched {len(df)} monetary base records from HKMA API")
            return df

        except requests.RequestException as e:
            logger.error(f"Failed to fetch monetary base data: {e}")
            # 嘗試使用備用數據源
            return self._get_fallback_data(start_date, end_date)

    def _parse_monetary_response(self, data: Dict[str, Any]) -> pd.DataFrame:
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

                # 提取貨幣基礎組件數據
                for component_code, component_name in self.components.items():
                    # 根據組件代碼構建API字段名
                    field_name = self._get_api_field_name(component_code)
                    value = record.get(field_name)

                    if value is not None:
                        # 轉換數值（可能是字符串格式）
                        try:
                            # 處理可能的單位（億港元）
                            if isinstance(value, str):
                                # 移除逗號和其他格式字符
                                value = value.replace(',', '').replace(' ', '')
                            numeric_value = float(value)
                        except (ValueError, TypeError):
                            continue

                        parsed_data.append({
                            'timestamp': date_obj,
                            'component': component_code,
                            'component_name': component_name,
                            'value': numeric_value
                        })

            except (ValueError, KeyError) as e:
                logger.debug(f"Failed to parse record: {e}")
                continue

        if not parsed_data:
            raise ValueError("No valid monetary base data found in response")

        # 創建DataFrame
        df = pd.DataFrame(parsed_data)

        # 設置時間索引
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        return df

    def _get_api_field_name(self, component_code: str) -> str:
        """根據組件代碼獲取API字段名"""
        # 根據HKMA API文檔的字段名映射
        field_mapping = {
            "MB": "monetary_base",
            "CL": "claims_on_banks",
            "GC": "gov_coins_notes",
            "EF": "other_liabilities",
            "BOJ": "borrowed_from_banks",
            "BIL": "efbn_outstanding"
        }
        return field_mapping.get(component_code, component_code.lower())

    def _get_fallback_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        獲取備用數據（本地文件或模擬數據）

        Args:
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            DataFrame with fallback monetary base data
        """
        logger.warning("Using fallback monetary base data source")

        # 嘗試讀取本地文件
        try:
            local_file = "data/real_data/monetary_base_data.json"
            with open(local_file, 'r', encoding='utf-8') as f:
                local_data = json.load(f)

            # 解析本地數據
            fallback_data = []
            for record in local_data:
                try:
                    date_obj = datetime.strptime(record['date'], "%Y-%m-%d")

                    if start_date <= date_obj <= end_date:
                        for component_code, component_name in self.components.items():
                            if component_code in record:
                                value = float(record[component_code])
                                fallback_data.append({
                                    'timestamp': date_obj,
                                    'component': component_code,
                                    'component_name': component_name,
                                    'value': value
                                })

                except (ValueError, KeyError) as e:
                    logger.debug(f"Failed to parse local record: {e}")
                    continue

            if fallback_data:
                df = pd.DataFrame(fallback_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                logger.info(f"Using {len(df)} records from local monetary base file")
                return df

        except FileNotFoundError:
            logger.warning("Local monetary base file not found")
        except Exception as e:
            logger.error(f"Failed to read local monetary base data: {e}")

        # 如果本地數據不可用，生成模擬數據
        return self._generate_mock_data(start_date, end_date)

    def _generate_mock_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """生成模擬貨幣基礎數據"""
        logger.warning("Generating mock monetary base data")

        # 生成日期範圍
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # 模擬各組件的基準值（億港元）
        base_values = {
            "MB": 1800.0,  # 貨幣基礎總額
            "CL": 1500.0,  # 負債證明書
            "GC": 500.0,   # 政府發行的銀行紙幣及硬幣
            "EF": 100.0,   # 其他負債
            "BOJ": 50.0,   # 從其他銀行借入款項
            "BIL": 800.0   # 未償還外匯基金票據及債券
        }

        mock_data = []
        import random

        for date in dates:
            # 跳過週末
            if date.weekday() >= 5:
                continue

            for component_code, base_value in base_values.items():
                # 添加隨機波動（±1%）
                variation = random.uniform(-0.01, 0.01)
                value = base_value * (1 + variation)

                mock_data.append({
                    'timestamp': date,
                    'component': component_code,
                    'component_name': self.components[component_code],
                    'value': round(value, 2)
                })

        df = pd.DataFrame(mock_data)
        df = df.set_index('timestamp')

        logger.info(f"Generated {len(df)} mock monetary base records")
        return df

    def validate_data(self, data: pd.DataFrame) -> bool:
        """驗證貨幣基礎數據"""
        if len(data) == 0:
            logger.error("No data to validate")
            return False

        # 檢查必要列
        required_columns = ['value', 'component']
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"Missing required column: {col}")
                return False

        # 檢查數據範圍（貨幣基礎應該是正值）
        invalid_values = data[data['value'] <= 0]
        if len(invalid_values) > 0:
            logger.warning(f"Found {len(invalid_values)} non-positive values")

        # 檢查組件
        valid_components = set(self.components.keys())
        invalid_components = set(data['component'].unique()) - valid_components
        if invalid_components:
            logger.error(f"Invalid components found: {invalid_components}")
            return False

        # 檢查數值合理性（貨幣基礎通常在1000-5000億港元範圍）
        monetary_base_data = data[data['component'] == 'MB']
        if not monetary_base_data.empty:
            unreasonable_values = monetary_base_data[
                (monetary_base_data['value'] < 500) | (monetary_base_data['value'] > 10000)
            ]
            if len(unreasonable_values) > 0:
                logger.warning(f"Found {len(unreasonable_values)} unreasonable monetary base values")

        logger.info(f"Monetary base data validation passed: {len(data)} records")
        return True

    def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """標準化貨幣基礎數據"""
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
        data = data.groupby('component')['value'].ffill()

        # 轉換單位為十億港元（如果原始數據是百萬）
        # 大部分HKMA數據已經是億港元單位，所以可能不需要轉換

        return data

    def get_component_data(self, component: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        獲取特定組件的貨幣基礎數據

        Args:
            component: 組件代碼 (MB, CL, GC, etc.)
            start_date: 開始日期
            end_date: 結束日期

        Returns:
            特定組件的貨幣基礎數據
        """
        if component not in self.components:
            raise ValueError(f"Invalid component: {component}")

        all_data = self.get_data(start_date, end_date)
        return all_data[all_data['component'] == component].copy()

    def get_latest_monetary_base(self) -> Dict[str, float]:
        """
        獲取最新的貨幣基礎數據

        Returns:
            最新貨幣基礎字典 {component: value}
        """
        try:
            latest_data = self.get_latest_data(days=7)
            latest_values = {}

            for component in self.components.keys():
                component_data = latest_data[latest_data['component'] == component]
                if not component_data.empty:
                    latest_values[component] = float(component_data['value'].iloc[-1])

            return latest_values

        except Exception as e:
            logger.error(f"Failed to get latest monetary base data: {e}")
            return {}

    def get_monetary_base_trend(self, days: int = 30) -> Dict[str, Any]:
        """
        獲取貨幣基礎趨勢分析

        Args:
            days: 分析天數

        Returns:
            趨勢分析字典
        """
        try:
            data = self.get_latest_data(days=days)
            mb_data = data[data['component'] == 'MB']

            if mb_data.empty:
                return {"error": "No monetary base data available"}

            values = mb_data['value'].values

            # 計算趨勢
            if len(values) >= 2:
                change = values[-1] - values[0]
                change_pct = (change / values[0]) * 100
            else:
                change = 0
                change_pct = 0

            return {
                "latest_value": float(values[-1]),
                "period_change": float(change),
                "period_change_pct": float(change_pct),
                "avg_value": float(values.mean()),
                "min_value": float(values.min()),
                "max_value": float(values.max()),
                "volatility": float(values.std()),
                "data_points": len(values)
            }

        except Exception as e:
            logger.error(f"Failed to analyze monetary base trend: {e}")
            return {"error": str(e)}

# 創建全局實例
_monetary_adapter = None

def get_monetary_adapter() -> MonetaryBaseAdapter:
    """獲取貨幣基礎適配器實例"""
    global _monetary_adapter
    if _monetary_adapter is None:
        _monetary_adapter = MonetaryBaseAdapter()
    return _monetary_adapter