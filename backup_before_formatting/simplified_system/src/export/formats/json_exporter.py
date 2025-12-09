#!/usr/bin/env python3
"""
JSON格式導出器
支持結構化數據導出、元數據包含和壓縮選項
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class JSONExporter:
    """JSON導出器類"""

    def __init__(self, config: Dict):
        self.config = config
        self.indent = config.get('indent', 2)
        self.ensure_ascii = config.get('ensure_ascii', False)
        self.date_format = config.get('date_format', 'iso')
        self.include_metadata = config.get('include_metadata', True)
        self.compress = config.get('compress', False)

    def export(self, data: Any, output_path: Path, options: Dict = None) -> bool:
        """
        導出數據到JSON文件

        Args:
            data: 要導出的數據
            output_path: 輸出文件路徑
            options: 導出選項

        Returns:
            bool: 是否成功
        """
        try:
            # 轉換數據為JSON兼容格式
            json_data = self._convert_to_json_compatible(data)

            # 添加元數據
            if self.include_metadata:
                json_data = self._add_metadata(json_data, options)

            # 生成JSON字符串
            json_str = json.dumps(
                json_data,
                indent=self.indent,
                ensure_ascii=self.ensure_ascii,
                default=self._json_serializer,
                separators=(',', ': ') if self.indent > 0 else (',', ':')
            )

            # 寫入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

            # 如果需要壓縮
            if self.compress:
                self._compress_file(output_path)

            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            logger.info(f"✅ JSON文件導出成功: {output_path} ({file_size} bytes)")
            return True

        except Exception as e:
            logger.error(f"❌ JSON導出失敗: {e}")
            return False

    def _convert_to_json_compatible(self, data: Any) -> Any:
        """將數據轉換為JSON兼容格式"""
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, dict):
            return {key: self._convert_to_json_compatible(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._convert_to_json_compatible(item) for item in data]
        elif isinstance(data, pd.DataFrame):
            return self._dataframe_to_dict(data)
        elif isinstance(data, pd.Series):
            return self._series_to_dict(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (np.int64, np.int32)):
            return int(data)
        elif isinstance(data, (np.float64, np.float32)):
            return float(data)
        elif isinstance(data, datetime):
            return self._format_datetime(data)
        else:
            return str(data)

    def _dataframe_to_dict(self, df: pd.DataFrame) -> Dict:
        """將DataFrame轉換為字典"""
        try:
            # 使用records格式，每行為一個字典
            records = df.to_dict('records')

            # 處理NaN值
            for record in records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, datetime):
                        record[key] = self._format_datetime(value)

            return {
                'columns': list(df.columns),
                'index': df.index.tolist() if len(df) <= 10000 else df.index[:10000].tolist(),
                'data': records,
                'shape': df.shape,
                'dtypes': df.dtypes.astype(str).to_dict()
            }
        except Exception as e:
            logger.warning(f"DataFrame轉換失敗: {e}")
            return str(df)

    def _series_to_dict(self, series: pd.Series) -> Dict:
        """將Series轉換為字典"""
        try:
            # 處理NaN值
            data_dict = series.to_dict()
            for key, value in data_dict.items():
                if pd.isna(value):
                    data_dict[key] = None
                elif isinstance(value, datetime):
                    data_dict[key] = self._format_datetime(value)

            return {
                'name': series.name,
                'index': series.index.tolist() if len(series) <= 10000 else series.index[:10000].tolist(),
                'data': data_dict,
                'dtype': str(series.dtype),
                'length': len(series)
            }
        except Exception as e:
            logger.warning(f"Series轉換失敗: {e}")
            return str(series)

    def _format_datetime(self, dt: datetime) -> str:
        """格式化日期時間"""
        if self.date_format == 'iso':
            return dt.isoformat()
        elif self.date_format == 'timestamp':
            return int(dt.timestamp())
        else:
            return dt.strftime(self.date_format)

    def _add_metadata(self, data: Any, options: Dict = None) -> Dict:
        """添加元數據"""
        metadata = {
            'export_timestamp': datetime.now().isoformat(),
            'export_version': '1.0',
            'data_type': self._get_data_type(data),
            'record_count': self._count_records(data),
            'exporter': 'SimplifiedSystem-JSONExporter'
        }

        # 添加選項相關的元數據
        if options:
            metadata['export_options'] = {
                'include_charts': options.get('include_charts', False),
                'include_raw_data': options.get('include_raw_data', False),
                'format_version': options.get('format_version', '1.0')
            }

        return {
            'metadata': metadata,
            'data': data
        }

    def _get_data_type(self, data: Any) -> str:
        """獲取數據類型"""
        if isinstance(data, pd.DataFrame):
            return 'dataframe'
        elif isinstance(data, pd.Series):
            return 'series'
        elif isinstance(data, dict):
            return 'dictionary'
        elif isinstance(data, (list, tuple)):
            return 'array'
        else:
            return 'unknown'

    def _count_records(self, data: Any) -> int:
        """統計記錄數量"""
        try:
            if isinstance(data, pd.DataFrame):
                return len(data)
            elif isinstance(data, pd.Series):
                return len(data)
            elif isinstance(data, dict):
                return 1
            elif isinstance(data, (list, tuple)):
                return len(data)
            else:
                return 1
        except:
            return 0

    def _json_serializer(self, obj):
        """自定義JSON序列化器"""
        if isinstance(obj, datetime):
            return self._format_datetime(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif pd.isna(obj):
            return None
        else:
            return str(obj)

    def _compress_file(self, file_path: Path):
        """壓縮JSON文件"""
        try:
            import gzip

            # 創建壓縮文件路徑
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')

            # 讀取原始文件並寫入壓縮文件
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)

            # 刪除原始文件
            os.remove(file_path)

            logger.info(f"✅ JSON文件已壓縮: {compressed_path}")

        except ImportError:
            logger.warning("⚠️ gzip模塊不可用，無法壓縮文件")
        except Exception as e:
            logger.warning(f"⚠️ 文件壓縮失敗: {e}")

    def export_schema(self, data: Any, output_path: Path) -> bool:
        """
        導出數據模式描述

        Args:
            data: 數據
            output_path: 輸出路徑

        Returns:
            bool: 是否成功
        """
        try:
            schema = self._generate_schema(data)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(
                    schema,
                    f,
                    indent=self.indent,
                    ensure_ascii=self.ensure_ascii
                )

            logger.info(f"✅ JSON模式導出成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ JSON模式導出失敗: {e}")
            return False

    def _generate_schema(self, data: Any) -> Dict:
        """生成數據模式"""
        schema = {
            'schema_version': '1.0',
            'generated_at': datetime.now().isoformat()
        }

        if isinstance(data, pd.DataFrame):
            schema['type'] = 'dataframe'
            schema['columns'] = []
            schema['shape'] = data.shape

            for col in data.columns:
                col_info = {
                    'name': col,
                    'dtype': str(data[col].dtype),
                    'nullable': data[col].isna().any(),
                    'unique_values': data[col].nunique(),
                    'sample_values': data[col].dropna().head(3).tolist()
                }

                # 添加數值類型的統計信息
                if data[col].dtype in ['int64', 'float64']:
                    col_info.update({
                        'min': data[col].min(),
                        'max': data[col].max(),
                        'mean': data[col].mean(),
                        'std': data[col].std()
                    })

                # 添加字符串類型的信息
                elif data[col].dtype == 'object':
                    col_info.update({
                        'max_length': data[col].astype(str).str.len().max(),
                        'min_length': data[col].astype(str).str.len().min()
                    })

                schema['columns'].append(col_info)

        elif isinstance(data, dict):
            schema['type'] = 'dictionary'
            schema['keys'] = list(data.keys())
            schema['key_types'] = {key: type(value).__name__ for key, value in data.items()}

        elif isinstance(data, list):
            schema['type'] = 'array'
            schema['length'] = len(data)
            if data:
                schema['element_type'] = type(data[0]).__name__
                schema['sample_elements'] = data[:3]

        else:
            schema['type'] = 'unknown'
            schema['data_type'] = type(data).__name__
            schema['sample'] = str(data)[:100]

        return schema

    def validate_json_data(self, json_path: Path) -> bool:
        """
        驗證JSON文件的有效性

        Args:
            json_path: JSON文件路徑

        Returns:
            bool: 是否有效
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                json.load(f)

            logger.info(f"✅ JSON文件驗證通過: {json_path}")
            return True

        except Exception as e:
            logger.error(f"❌ JSON文件驗證失敗: {json_path} - {e}")
            return False

    def merge_json_files(self, file_paths: List[Path], output_path: Path) -> bool:
        """
        合併多個JSON文件

        Args:
            file_paths: 要合併的JSON文件路徑列表
            output_path: 輸出路徑

        Returns:
            bool: 是否成功
        """
        try:
            merged_data = {
                'merged_files': [str(path) for path in file_paths],
                'merge_timestamp': datetime.now().isoformat(),
                'data': []
            }

            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    merged_data['data'].append(file_data)

            # 寫入合併後的數據
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(
                    merged_data,
                    f,
                    indent=self.indent,
                    ensure_ascii=self.ensure_ascii,
                    default=self._json_serializer
                )

            logger.info(f"✅ JSON文件合併成功: {output_path}")
            return True

        except Exception as e:
            logger.error(f"❌ JSON文件合併失敗: {e}")
            return False