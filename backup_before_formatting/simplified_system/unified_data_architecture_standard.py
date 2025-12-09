#!/usr/bin/env python3
"""
统一数据架构标准 (Unified Data Architecture Standard - UDAS)
解决数据格式不一致性问题的企业级数据标准框架
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime, date
import warnings
warnings.filterwarnings('ignore')

class DataSourceType(Enum):
    """数据源类型标准化"""
    STOCK_API = "stock_api"
    GOVERNMENT_DATA = "government_data"
    HISTORICAL_CSV = "historical_csv"
    REALTIME_FEED = "realtime_feed"
    CALCULATED_INDICATOR = "calculated_indicator"

class DataQualityLevel(Enum):
    """数据质量等级"""
    PRODUCTION = "production"      # 生产级质量
    VALIDATION = "validation"      # 验证级质量
    DEVELOPMENT = "development"    # 开发级质量
    TESTING = "testing"           # 测试级质量

@dataclass
class StandardizedColumnMapping:
    """标准化列映射配置"""
    standard_name: str
    aliases: List[str]
    data_type: str
    required: bool = True
    validation_rules: Optional[Dict] = None

@dataclass
class DataStandard:
    """数据标准定义"""
    source_type: DataSourceType
    quality_level: DataQualityLevel
    required_columns: List[str]
    column_mappings: Dict[str, StandardizedColumnMapping]
    validation_schema: Dict
    format_version: str = "1.0"

class UnifiedDataArchitectureStandard:
    """统一数据架构标准核心类"""

    def __init__(self):
        self.standards = self._initialize_standards()
        self.conversion_cache = {}
        self.validation_errors = []

    def _initialize_standards(self) -> Dict[DataSourceType, DataStandard]:
        """初始化各类数据标准"""
        standards = {}

        # 股票数据标准
        stock_columns = {
            'timestamp': StandardizedColumnMapping(
                'timestamp', ['date', 'datetime', 'time'], 'datetime'),
            'open': StandardizedColumnMapping(
                'open', ['Open', 'open_price', 'opening'], 'float'),
            'high': StandardizedColumnMapping(
                'high', ['High', 'high_price', 'maximum'], 'float'),
            'low': StandardizedColumnMapping(
                'low', ['Low', 'low_price', 'minimum'], 'float'),
            'close': StandardizedColumnMapping(
                'close', ['Close', 'price', 'closing', 'adj_close'], 'float'),
            'volume': StandardizedColumnMapping(
                'volume', ['Volume', 'vol', 'trading_volume'], 'int')
        }

        standards[DataSourceType.STOCK_API] = DataStandard(
            source_type=DataSourceType.STOCK_API,
            quality_level=DataQualityLevel.PRODUCTION,
            required_columns=['timestamp', 'close'],
            column_mappings=stock_columns,
            validation_schema={
                'timestamp': {'type': 'datetime', 'required': True},
                'close': {'type': 'float', 'min': 0, 'required': True},
                'volume': {'type': 'int', 'min': 0, 'required': False}
            }
        )

        # 政府数据标准
        gov_columns = {
            'date': StandardizedColumnMapping(
                'date', ['timestamp', 'datetime'], 'date'),
            'value': StandardizedColumnMapping(
                'value', ['rate', 'price', 'amount', 'indicator'], 'float'),
            'series': StandardizedColumnMapping(
                'series', ['category', 'type', 'name'], 'str', False)
        }

        standards[DataSourceType.GOVERNMENT_DATA] = DataStandard(
            source_type=DataSourceType.GOVERNMENT_DATA,
            quality_level=DataQualityLevel.PRODUCTION,
            required_columns=['date', 'value'],
            column_mappings=gov_columns,
            validation_schema={
                'date': {'type': 'date', 'required': True},
                'value': {'type': 'float', 'required': True}
            }
        )

        return standards

    def standardize_data(self, data: Union[pd.DataFrame, Dict, List],
                        source_type: DataSourceType) -> Optional[pd.DataFrame]:
        """
        标准化数据格式 - 核心转换函数
        """
        try:
            # 识别输入格式
            input_format = self._identify_input_format(data)

            # 转换为DataFrame
            df = self._convert_to_dataframe(data, input_format)

            if df is None or len(df) == 0:
                self._log_error("数据转换为DataFrame失败", "conversion_error")
                return None

            # 应用数据标准
            df_standardized = self._apply_data_standard(df, source_type)

            # 验证数据质量
            is_valid, errors = self._validate_data(df_standardized, source_type)

            if is_valid:
                print(f"SUCCESS Data standardization: {len(df_standardized)} records, quality: {self.standards[source_type].quality_level.value}")
                return df_standardized
            else:
                self._log_error(f"Data validation failed: {errors}", "validation_error")
                return df_standardized  # 仍然返回，但记录错误

        except Exception as e:
            self._log_error(f"Data standardization error: {str(e)}", "standardization_error")
            return None

    def _identify_input_format(self, data: Union[pd.DataFrame, Dict, List]) -> str:
        """识别输入数据格式"""
        if isinstance(data, pd.DataFrame):
            return "dataframe"
        elif isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], dict):
                return "nested_dict"
            elif all(isinstance(v, dict) for v in data.values()):
                return "dict_of_dicts"
            else:
                return "flat_dict"
        elif isinstance(data, list):
            return "list"
        else:
            return "unknown"

    def _convert_to_dataframe(self, data: Union[pd.DataFrame, Dict, List],
                             input_format: str) -> Optional[pd.DataFrame]:
        """将各种格式转换为DataFrame"""
        try:
            if input_format == "dataframe":
                return data.copy()

            elif input_format == "nested_dict":
                # 处理嵌套字典格式 {data: {close: {date: price}}}
                nested_data = data.get('data', {})

                # 寻找价格数据
                price_data = None
                for key in ['close', 'Close', 'price', 'Price']:
                    if key in nested_data:
                        price_data = nested_data[key]
                        break

                if price_data and isinstance(price_data, dict):
                    df = pd.DataFrame({
                        'close': list(price_data.values()),
                        'timestamp': pd.to_datetime(list(price_data.keys()))
                    })
                    return df.set_index('timestamp')

            elif input_format == "dict_of_dicts":
                # 处理字典字典格式 {date1: {close: price1, volume: vol1}}
                df = pd.DataFrame.from_dict(data, orient='index')
                df.index = pd.to_datetime(df.index)
                return df

            elif input_format == "flat_dict":
                # 处理平面字典格式 {date1: price1, date2: price2}
                df = pd.DataFrame({
                    'close': list(data.values()),
                    'timestamp': pd.to_datetime(list(data.keys()))
                })
                return df.set_index('timestamp')

            elif input_format == "list":
                # 处理列表格式 [{date: date1, close: price1}, ...]
                df = pd.DataFrame(data)
                if 'date' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['date'])
                    df = df.set_index('timestamp').drop('date', axis=1)
                return df

            print(f"ERROR Unsupported input format: {input_format}")
            return None

        except Exception as e:
            print(f"ERROR Data format conversion failed: {str(e)}")
            return None

    def _apply_data_standard(self, df: pd.DataFrame,
                           source_type: DataSourceType) -> pd.DataFrame:
        """应用数据标准到DataFrame"""
        standard = self.standards[source_type]
        df_standardized = df.copy()

        # 标准化列名
        column_mapping = {}
        for standard_col, mapping in standard.column_mappings.items():
            for alias in mapping.aliases:
                # 大小写不敏感匹配
                for col in df_standardized.columns:
                    if col.lower() == alias.lower():
                        column_mapping[col] = standard_col
                        break

        if column_mapping:
            df_standardized = df_standardized.rename(columns=column_mapping)
            print(f"INFO Column mapping: {column_mapping}")

        # 确保必需列存在
        missing_required = [col for col in standard.required_columns
                           if col not in df_standardized.columns]

        if missing_required:
            print(f"WARNING Missing required columns: {missing_required}")

            # 尝试智能填充
            if 'close' in df_standardized.columns and 'open' in missing_required:
                df_standardized['open'] = df_standardized['close']
            if 'close' in df_standardized.columns and 'high' in missing_required:
                df_standardized['high'] = df_standardized['close'] * 1.001
            if 'close' in df_standardized.columns and 'low' in missing_required:
                df_standardized['low'] = df_standardized['close'] * 0.999
            if 'close' in df_standardized.columns and 'volume' in missing_required:
                df_standardized['volume'] = 1000000  # 默认成交量

        # 数据类型转换
        for standard_col, mapping in standard.column_mappings.items():
            if standard_col in df_standardized.columns:
                try:
                    if mapping.data_type == 'datetime':
                        df_standardized[standard_col] = pd.to_datetime(df_standardized[standard_col])
                    elif mapping.data_type == 'date':
                        df_standardized[standard_col] = pd.to_datetime(df_standardized[standard_col]).dt.date
                    elif mapping.data_type == 'float':
                        df_standardized[standard_col] = pd.to_numeric(df_standardized[standard_col], errors='coerce')
                    elif mapping.data_type == 'int':
                        df_standardized[standard_col] = pd.to_numeric(df_standardized[standard_col], errors='coerce').fillna(0).astype(int)
                    elif mapping.data_type == 'str':
                        df_standardized[standard_col] = df_standardized[standard_col].astype(str)
                except Exception as e:
                    print(f"WARNING Data type conversion failed {standard_col}: {str(e)}")

        # 排序数据
        if df_standardized.index.name == 'timestamp' or 'timestamp' in df_standardized.columns:
            df_standardized = df_standardized.sort_index()

        return df_standardized

    def _validate_data(self, df: pd.DataFrame,
                      source_type: DataSourceType) -> tuple[bool, List[str]]:
        """验证数据质量"""
        errors = []
        standard = self.standards[source_type]

        # 检查必需列
        missing_cols = [col for col in standard.required_columns
                       if col not in df.columns]
        if missing_cols:
            errors.append(f"缺失必需列: {missing_cols}")

        # 检查数据类型和范围
        for col, schema in standard.validation_schema.items():
            if col in df.columns:
                if schema['type'] == 'float':
                    if 'min' in schema and (df[col] < schema['min']).any():
                        errors.append(f"{col} 包含负值")
                elif schema['type'] == 'int':
                    if 'min' in schema and (df[col] < schema['min']).any():
                        errors.append(f"{col} 包含无效值")

        # 检查空值
        for col in standard.required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > len(df) * 0.1:  # 超过10%空值
                    errors.append(f"{col} 空值过多: {null_count}/{len(df)}")

        # 检查重复数据
        if hasattr(df.index, 'duplicated'):
            dup_count = df.index.duplicated().sum()
            if dup_count > 0:
                errors.append(f"重复时间戳: {dup_count} 条")

        return len(errors) == 0, errors

    def _log_error(self, message: str, error_type: str):
        """记录错误信息"""
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message
        }
        self.validation_errors.append(error_record)
        print(f"ERROR {error_type}: {message}")

    def get_quality_report(self) -> Dict:
        """获取数据质量报告"""
        return {
            'total_errors': len(self.validation_errors),
            'error_types': pd.Series([e['error_type'] for e in self.validation_errors]).value_counts().to_dict(),
            'recent_errors': self.validation_errors[-5:],
            'supported_standards': list(self.standards.keys())
        }

    def save_standard_config(self, filename: str):
        """保存标准配置"""
        config = {
            'standards': {
                source_type.value: asdict(standard)
                for source_type, standard in self.standards.items()
            },
            'version': '1.0',
            'created_at': datetime.now().isoformat()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False, default=str)

        print(f"SUCCESS Data standard configuration saved to: {filename}")

def main():
    """主函数 - 测试统一数据架构标准"""
    print("Starting Unified Data Architecture Standard (UDAS)...")

    udas = UnifiedDataArchitectureStandard()

    # 测试不同的数据格式
    test_cases = [
        # 嵌套字典格式 (当前API格式)
        {
            'data': {
                'close': {
                    '2025-01-01': 400.0,
                    '2025-01-02': 410.0
                },
                'volume': {
                    '2025-01-01': 1000000,
                    '2025-01-02': 1200000
                }
            }
        },

        # 平面字典格式
        {
            '2025-01-01': 400.0,
            '2025-01-02': 410.0
        },

        # 列表格式
        [
            {'date': '2025-01-01', 'close': 400.0, 'volume': 1000000},
            {'date': '2025-01-02', 'close': 410.0, 'volume': 1200000}
        ]
    ]

    print("\nTESTING Data format standardization...")
    for i, test_data in enumerate(test_cases):
        print(f"\n--- Test Case {i+1} ---")
        result = udas.standardize_data(test_data, DataSourceType.STOCK_API)
        if result is not None:
            print(f"SUCCESS Standardization: {len(result)} rows, {len(result.columns)} columns")
            print(f"INFO Columns: {list(result.columns)}")
            print(f"DATA Sample:\n{result.head()}")
        else:
            print("FAILED Standardization")

    # 生成质量报告
    print("\nQUALITY REPORT:")
    report = udas.get_quality_report()
    print(f"Total errors: {report['total_errors']}")
    print(f"Error type distribution: {report['error_types']}")

    # 保存标准配置
    udas.save_standard_config('config/data_standard_config.json')

    return udas

if __name__ == "__main__":
    udas = main()