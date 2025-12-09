#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真實數據適配器
使用項目中真實的香港政府數據文件，不使用Mock數據
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import os
from pathlib import Path

from .base_adapter import BaseAdapter, DataSourceInfo, DataPoint

logger = logging.getLogger(__name__)

class RealDataAdapter(BaseAdapter):
    """真實數據適配器，使用已收集的真實政府數據"""

    def __init__(self):
        # 創建數據源信息
        source_info = DataSourceInfo(
            source_id="REAL_DATA",
            name="香港政府真實數據",
            description="從真實香港政府API收集的數據",
            frequency="mixed",
            unit="various"
        )
        super().__init__(source_info)

        # 設置基礎路徑
        self.base_path = Path(__file__).parent.parent.parent

        # 定義真實數據源路徑映射
        self.data_source_paths = {
            "HB": "gov_crawler/real_data/hibor_data.json",
            "MB": "data/final_real_indicators/hkma_real_data_with_indicators.csv",
            "GD": "data/final_real_indicators/hkma_real_data_with_indicators.csv",
            "RT": "data/unified_real_data/integrated_data/all_real_data_20251108.json",
            "TR": "data/unified_real_data/integrated_data/all_real_data_20251108.json",
            "TS": "data/unified_real_data/integrated_data/all_real_data_20251108.json",
            "CP": "data/unified_real_data/integrated_data/all_real_data_20251108.json",
            "UE": "data/unified_real_data/integrated_data/all_real_data_20251108.json"
        }

        # 定義真實數據源信息
        self.data_sources = {
            "HB": DataSourceInfo(
                source_id="HB",
                name="HIBOR利率",
                description="香港銀行同業拆放利率",
                frequency="daily",
                unit="percent"
            ),
            "MB": DataSourceInfo(
                source_id="MB",
                name="貨幣基礎",
                description="香港貨幣基礎",
                frequency="monthly",
                unit="hkd_billion"
            ),
            "GD": DataSourceInfo(
                source_id="GD",
                name="GDP數據",
                description="香港本地生產總值",
                frequency="quarterly",
                unit="hkd_billion"
            ),
            "RT": DataSourceInfo(
                source_id="RT",
                name="零售銷售數據",
                description="香港零售銷售總額",
                frequency="monthly",
                unit="hkd_billion"
            ),
            "TR": DataSourceInfo(
                source_id="TR",
                name="貿易數據",
                description="香港進出口貿易統計",
                frequency="monthly",
                unit="hkd_billion"
            ),
            "TS": DataSourceInfo(
                source_id="TS",
                name="旅遊數據",
                description="香港旅遊業統計",
                frequency="monthly",
                unit="count"
            ),
            "CP": DataSourceInfo(
                source_id="CP",
                name="CPI通脹數據",
                description="香港消費物價指數",
                frequency="monthly",
                unit="index"
            ),
            "UE": DataSourceInfo(
                source_id="UE",
                name="失業率數據",
                description="香港失業率統計",
                frequency="monthly",
                unit="percent"
            )
        }

    def get_source_info(self) -> DataSourceInfo:
        """獲取數據源信息"""
        return DataSourceInfo(
            source_id="REAL_DATA",
            name="香港政府真實數據",
            description="從真實香港政府API收集的數據",
            frequency="mixed",
            unit="various"
        )

    def fetch_data(self, start_date: datetime, end_date: datetime, source_id: Optional[str] = None) -> pd.DataFrame:
        """獲取真實數據"""
        if source_id and source_id in self.data_sources:
            return self._load_real_data(start_date, end_date, source_id)
        else:
            # 如果沒有指定source_id，返回所有數據源
            all_data = []
            for sid in self.data_sources.keys():
                try:
                    data = self._load_real_data(start_date, end_date, sid)
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    logger.warning(f"Failed to load data for {sid}: {e}")

            if all_data:
                return pd.concat(all_data, ignore_index=True)
            else:
                return pd.DataFrame()

    def _load_real_data(self, start_date: datetime, end_date: datetime, source_id: str) -> pd.DataFrame:
        """加載真實數據文件"""
        data_path = self.base_path / self.data_source_paths[source_id]

        if not data_path.exists():
            raise FileNotFoundError(f"Real data file not found: {data_path}")

        try:
            if source_id == "HB":
                return self._load_hibor_data(data_path, start_date, end_date)
            elif source_id in ["MB", "GD"]:
                return self._load_hkma_csv_data(data_path, start_date, end_date, source_id)
            else:
                return self._load_unified_json_data(data_path, start_date, end_date, source_id)
        except Exception as e:
            logger.error(f"Failed to load real data for {source_id}: {e}")
            raise

    def _load_hibor_data(self, file_path: Path, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """加載HIBOR真實數據"""
        with open(file_path, 'r', encoding='utf-8') as f:
            hibor_data = json.load(f)

        processed_data = []
        for record in hibor_data:
            record_date = datetime.strptime(record['date'], '%Y-%m-%d')
            if start_date <= record_date <= end_date:
                processed_data.append({
                    'timestamp': record_date,
                    'value': float(record['rate']),
                    'source_id': 'HB',
                    'tenor': record['tenor'],
                    'data_type': 'interest_rate'
                })

        df = pd.DataFrame(processed_data)
        logger.info(f"Loaded {len(df)} HIBOR records from {start_date.date()} to {end_date.date()}")
        return df

    def _load_hkma_csv_data(self, file_path: Path, start_date: datetime, end_date: datetime, source_id: str) -> pd.DataFrame:
        """加載HKMA CSV真實數據"""
        df = pd.read_csv(file_path)

        # 轉換日期格式
        df['timestamp'] = pd.to_datetime(df['Period_Date'], format='%Y-%m-%d')
        df = df[['timestamp', 'Figure_HKD_Billion', 'Frequency']]
        df.columns = ['timestamp', 'value', 'frequency']

        # 根據source_id篩選數據
        if source_id == "GD":
            # GDP數據通常是季度數據
            df = df[df['frequency'] == 'Q']
        elif source_id == "MB":
            # 貨幣基礎數據可能是日度或月度數據
            df = df[df['frequency'].isin(['D', 'M'])]

        # 篩選日期範圍
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]

        # 添加元數據
        df['source_id'] = source_id
        df['data_type'] = 'economic_indicator'

        logger.info(f"Loaded {len(df)} {source_id} records from {start_date.date()} to {end_date.date()}")
        return df

    def _load_unified_json_data(self, file_path: Path, start_date: datetime, end_date: datetime, source_id: str) -> pd.DataFrame:
        """加載統一JSON真實數據"""
        with open(file_path, 'r', encoding='utf-8') as f:
            unified_data = json.load(f)

        # 獲取特定數據源的數據
        if 'data' in unified_data and source_id in unified_data['data']:
            source_data = unified_data['data'][source_id]

            processed_data = []
            for record in source_data.get('data', []):
                if 'timestamp' in record and 'value' in record:
                    record_date = pd.to_datetime(record['timestamp'])
                    if start_date <= record_date <= end_date:
                        processed_data.append({
                            'timestamp': record_date,
                            'value': float(record['value']),
                            'source_id': source_id,
                            'data_type': 'economic_indicator'
                        })

            df = pd.DataFrame(processed_data)
            logger.info(f"Loaded {len(df)} {source_id} records from unified data")
            return df
        else:
            raise ValueError(f"Source {source_id} not found in unified data")

    def get_latest_data(self, source_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """獲取最新數據"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)  # 獲取指定天數的數據

        try:
            df = self.fetch_data(start_date, end_date, source_id)

            if df.empty:
                return {}

            # 按時間戳排序並獲取最新記錄
            df = df.sort_values('timestamp')
            latest = df.iloc[-1]

            return {
                'timestamp': latest['timestamp'].isoformat(),
                'value': latest['value'],
                'source_id': latest['source_id']
            }
        except Exception as e:
            logger.error(f"Failed to get latest data: {e}")
            return {}

    def get_statistics(self, source_id: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """獲取數據統計信息"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        try:
            df = self.fetch_data(start_date, end_date, source_id)

            if df.empty:
                return {}

            return {
                'record_count': len(df),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'mean_value': float(df['value'].mean()),
                'min_value': float(df['value'].min()),
                'max_value': float(df['value'].max()),
                'std_value': float(df['value'].std()),
                'latest_value': float(df['value'].iloc[-1])
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def validate_data(self, data: pd.DataFrame) -> bool:
        """驗證真實數據格式"""
        try:
            # 檢查DataFrame是否為空
            if data.empty:
                return False

            # 檢查必需的列是否存在
            required_columns = ['timestamp', 'value', 'source_id']
            for col in required_columns:
                if col not in data.columns:
                    logger.warning(f"Missing required column: {col}")
                    return False

            # 檢查數據類型
            if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
                logger.warning("timestamp column is not datetime type")
                return False

            if not pd.api.types.is_numeric_dtype(data['value']):
                logger.warning("value column is not numeric type")
                return False

            # 檢查是否有有效的數值
            if data['value'].isna().all():
                logger.warning("All values are NaN")
                return False

            return True

        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False

    def normalize_data(self, data: pd.DataFrame, source_id: Optional[str] = None) -> pd.DataFrame:
        """標準化數據格式"""
        if data.empty:
            return data

        # 確保有必需的列
        required_columns = ['timestamp', 'value', 'source_id']
        for col in required_columns:
            if col not in data.columns:
                if col == 'source_id' and source_id:
                    data[col] = source_id
                else:
                    logger.warning(f"Missing required column: {col}")
                    return pd.DataFrame()

        # 確保timestamp是datetime類型
        if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
            data['timestamp'] = pd.to_datetime(data['timestamp'])

        # 確保value是數值類型
        data['value'] = pd.to_numeric(data['value'], errors='coerce')

        # 按時間戳排序
        data = data.sort_values('timestamp').reset_index(drop=True)

        return data