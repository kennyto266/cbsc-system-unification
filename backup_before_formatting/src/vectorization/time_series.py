#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
時間序列向量化引擎
將非價格數據轉換為GPU友好的向量化格式
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class VectorizedData:
    """向量化數據容器"""
    values: np.ndarray          # 數值數組
    timestamps: np.ndarray      # 時間戳數組 (numpy datetime64)
    metadata: Dict[str, Any]    # 元數據
    source_id: str             # 數據源ID
    normalization_params: Optional[Dict[str, Any]] = None  # 標準化參數

class TimeSeriesVectorizer:
    """時間序列向量化器"""

    def __init__(self):
        self.scaling_methods = {
            'minmax': self._minmax_scale,
            'zscore': self._zscore_scale,
            'robust': self._robust_scale,
            'none': lambda x: x
        }

    def vectorize_dataframe(self, df: pd.DataFrame, source_id: str,
                           scaling_method: str = 'zscore',
                           fill_method: str = 'ffill') -> VectorizedData:
        """
        將DataFrame向量化

        Args:
            df: 輸入DataFrame
            source_id: 數據源ID
            scaling_method: 縮放方法
            fill_method: 填充方法

        Returns:
            向量化數據
        """
        try:
            if df.empty:
                raise ValueError("DataFrame is empty")

            # 處理缺失值
            df_filled = self._handle_missing_values(df, fill_method)

            # 確保數值列為float32
            if 'value' in df_filled.columns:
                values = df_filled['value'].astype(np.float32).values
            else:
                # 如果沒有value列，使用第一個數值列
                numeric_columns = df_filled.select_dtypes(include=[np.number]).columns
                if len(numeric_columns) > 0:
                    values = df_filled[numeric_columns[0]].astype(np.float32).values
                else:
                    raise ValueError("No numeric columns found in DataFrame")

            # 獲取時間戳
            timestamps = df_filled.index.values.astype('datetime64[ns]')

            # 標準化
            scaled_values, scaling_params = self._scale_values(values, scaling_method)

            # 創建元數據
            metadata = {
                'shape': scaled_values.shape,
                'dtype': str(scaled_values.dtype),
                'date_range': {
                    'start': str(timestamps[0]),
                    'end': str(timestamps[-1])
                },
                'record_count': len(values),
                'scaling_method': scaling_method,
                'fill_method': fill_method,
                'has_multi_columns': len(df_filled.columns) > 1
            }

            return VectorizedData(
                values=scaled_values,
                timestamps=timestamps,
                metadata=metadata,
                source_id=source_id,
                normalization_params=scaling_params
            )

        except Exception as e:
            logger.error(f"Failed to vectorize DataFrame: {e}")
            raise

    def vectorize_multiple_sources(self, data_dict: Dict[str, pd.DataFrame],
                                 scaling_method: str = 'zscore',
                                 fill_method: str = 'ffill') -> Dict[str, VectorizedData]:
        """
        向量化多個數據源

        Args:
            data_dict: 數據字典 {source_id: DataFrame}
            scaling_method: 縮放方法
            fill_method: 填充方法

        Returns:
            向量化數據字典
        """
        vectorized_data = {}

        for source_id, df in data_dict.items():
            try:
                if not df.empty:
                    vectorized_data[source_id] = self.vectorize_dataframe(
                        df, source_id, scaling_method, fill_method
                    )
                    logger.info(f"Vectorized {len(df)} records for {source_id}")

            except Exception as e:
                logger.error(f"Failed to vectorize {source_id}: {e}")

        return vectorized_data

    def create_gpu_arrays(self, vectorized_data: VectorizedData) -> Dict[str, Any]:
        """
        為GPU創建優化的數組格式

        Args:
            vectorized_data: 向量化數據

        Returns:
            GPU優化的數組字典
        """
        try:
            gpu_arrays = {
                'values': vectorized_data.values,  # 已經是numpy數組
                'timestamps': vectorized_data.timestamps,
                'length': len(vectorized_data.values),
                'source_id': vectorized_data.source_id,
                'metadata': vectorized_data.metadata
            }

            # 檢查是否可以轉換為CuPy數組
            try:
                import cupy as cp
                gpu_arrays['values_gpu'] = cp.asarray(vectorized_data.values)
                gpu_arrays['timestamps_gpu'] = cp.asarray(vectorized_data.timestamps)
                gpu_arrays['cupy_available'] = True
                logger.debug(f"Created CuPy arrays for {vectorized_data.source_id}")
            except ImportError:
                gpu_arrays['cupy_available'] = False
                logger.debug(f"CuPy not available, using numpy arrays for {vectorized_data.source_id}")

            return gpu_arrays

        except Exception as e:
            logger.error(f"Failed to create GPU arrays: {e}")
            raise

    def _handle_missing_values(self, df: pd.DataFrame, method: str) -> pd.DataFrame:
        """處理缺失值"""
        if method == 'ffill':
            return df.fillna(method='ffill').fillna(method='bfill')
        elif method == 'interpolate':
            return df.interpolate(method='linear')
        elif method == 'forward':
            return df.fillna(method='ffill')
        elif method == 'zero':
            return df.fillna(0)
        else:
            return df.dropna()

    def _scale_values(self, values: np.ndarray, method: str) -> Tuple[np.ndarray, Dict[str, Any]]:
        """縮放數值"""
        scaling_function = self.scaling_methods.get(method, lambda x: x)
        return scaling_function(values)

    def _minmax_scale(self, values: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """最小最大縮放"""
        min_val = np.min(values)
        max_val = np.max(values)

        if max_val == min_val:
            return np.zeros_like(values), {'method': 'minmax', 'min': min_val, 'max': max_val}

        scaled = (values - min_val) / (max_val - min_val)
        params = {'method': 'minmax', 'min': float(min_val), 'max': float(max_val)}
        return scaled, params

    def _zscore_scale(self, values: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Z-score標準化"""
        mean_val = np.mean(values)
        std_val = np.std(values)

        if std_val == 0:
            return np.zeros_like(values), {'method': 'zscore', 'mean': mean_val, 'std': std_val}

        scaled = (values - mean_val) / std_val
        params = {'method': 'zscore', 'mean': float(mean_val), 'std': float(std_val)}
        return scaled, params

    def _robust_scale(self, values: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """穩健縮放（使用中位數和IQR）"""
        median_val = np.median(values)
        q75, q25 = np.percentile(values, [75, 25])
        iqr = q75 - q25

        if iqr == 0:
            return np.zeros_like(values), {'method': 'robust', 'median': median_val, 'iqr': iqr}

        scaled = (values - median_val) / iqr
        params = {'method': 'robust', 'median': float(median_val), 'iqr': float(iqr)}
        return scaled, params

    def inverse_transform(self, scaled_values: np.ndarray,
                         params: Dict[str, Any]) -> np.ndarray:
        """
        反向標準化

        Args:
            scaled_values: 標準化後的值
            params: 標準化參數

        Returns:
            原始值
        """
        method = params.get('method', 'none')

        if method == 'minmax':
            min_val = params['min']
            max_val = params['max']
            if max_val != min_val:
                return scaled_values * (max_val - min_val) + min_val
            else:
                return scaled_values

        elif method == 'zscore':
            mean_val = params['mean']
            std_val = params['std']
            if std_val != 0:
                return scaled_values * std_val + mean_val
            else:
                return scaled_values

        elif method == 'robust':
            median_val = params['median']
            iqr = params['iqr']
            if iqr != 0:
                return scaled_values * iqr + median_val
            else:
                return scaled_values

        else:
            return scaled_values

    def create_windows(self, vectorized_data: VectorizedData,
                       window_size: int, step_size: Optional[int] = None) -> Dict[str, np.ndarray]:
        """
        創建滑動窗口

        Args:
            vectorized_data: 向量化數據
            window_size: 窗口大小
            step_size: 步長（默認為window_size）

        Returns:
            窗口化數據字典
        """
        if step_size is None:
            step_size = window_size

        values = vectorized_data.values
        length = len(values)

        if length < window_size:
            raise ValueError(f"Data length ({length}) is less than window size ({window_size})")

        # 計算窗口數量
        num_windows = (length - window_size) // step_size + 1

        # 創建窗口
        windows = np.zeros((num_windows, window_size), dtype=np.float32)
        for i in range(num_windows):
            start_idx = i * step_size
            end_idx = start_idx + window_size
            windows[i] = values[start_idx:end_idx]

        return {
            'windows': windows,
            'window_size': window_size,
            'step_size': step_size,
            'num_windows': num_windows,
            'original_length': length
        }

    def create_sequences(self, vectorized_data: VectorizedData,
                         sequence_length: int,
                         prediction_length: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """
        創建序列數據（用於機器學習）

        Args:
            vectorized_data: 向量化數據
            sequence_length: 輸入序列長度
            prediction_length: 預測序列長度

        Returns:
            (X, y) 序對
        """
        values = vectorized_data.values
        total_length = len(values)

        if total_length < sequence_length + prediction_length:
            raise ValueError(f"Data length ({total_length}) is insufficient for sequences")

        # 計算序列數量
        num_sequences = total_length - sequence_length - prediction_length + 1

        X = np.zeros((num_sequences, sequence_length), dtype=np.float32)
        y = np.zeros((num_sequences, prediction_length), dtype=np.float32)

        for i in range(num_sequences):
            start_idx = i
            end_idx = start_idx + sequence_length
            pred_start = end_idx
            pred_end = pred_start + prediction_length

            X[i] = values[start_idx:end_idx]
            y[i] = values[pred_start:pred_end].flatten()

        return X, y

class MultiSourceVectorizer:
    """多源數據向量化器"""

    def __init__(self):
        self.vectorizer = TimeSeriesVectorizer()
        self.alignment_methods = {
            'intersection': self._align_intersection,
            'union': self._align_union,
            'outer': self._align_outer
        }

    def align_multiple_sources(self, data_dict: Dict[str, pd.DataFrame],
                              alignment_method: str = 'intersection') -> Dict[str, pd.DataFrame]:
        """
        對齊多個數據源的時間索引

        Args:
            data_dict: 數據字典
            alignment_method: 對齊方法

        Returns:
            對齊後的數據字典
        """
        alignment_function = self.alignment_methods.get(alignment_method, self._align_intersection)
        return alignment_function(data_dict)

    def _align_intersection(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """交集對齊"""
        if not data_dict:
            return {}

        # 獲取所有數據源的時間索引交集
        common_index = None
        for df in data_dict.values():
            if not df.empty:
                if common_index is None:
                    common_index = df.index
                else:
                    common_index = common_index.intersection(df.index)

        if common_index is None or len(common_index) == 0:
            logger.warning("No common time index found")
            return data_dict

        # 重新索引所有數據源
        aligned_data = {}
        for source_id, df in data_dict.items():
            if not df.empty:
                aligned_data[source_id] = df.reindex(common_index)

        return aligned_data

    def _align_union(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """並集對齊"""
        if not data_dict:
            return {}

        # 獲取所有數據源的時間索引並集
        all_indices = []
        for df in data_dict.values():
            if not df.empty:
                all_indices.append(df.index)

        if not all_indices:
            return data_dict

        common_index = all_indices[0].union.reduce(lambda x, y: x.union(y), all_indices[1:])

        # 重新索引所有數據源
        aligned_data = {}
        for source_id, df in data_dict.items():
            if not df.empty:
                aligned_data[source_id] = df.reindex(common_index)

        return aligned_data

    def _align_outer(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """外連接對齊（同union）"""
        return self._align_union(data_dict)

    def create_combined_features(self, vectorized_data: Dict[str, VectorizedData],
                                feature_combination: str = 'concatenate') -> np.ndarray:
        """
        創建組合特徵

        Args:
            vectorized_data: 向量化數據字典
            feature_combination: 特徵組合方法

        Returns:
            組合特徵數組
        """
        if not vectorized_data:
            raise ValueError("No vectorized data provided")

        values_list = []
        lengths = []

        for source_id, data in vectorized_data.items():
            values_list.append(data.values)
            lengths.append(len(data.values))

        # 檢查長度一致性
        if len(set(lengths)) > 1:
            logger.warning(f"Inconsistent data lengths: {lengths}")
            # 截斷到最小長度
            min_length = min(lengths)
            values_list = [values[:min_length] for values in values_list]

        if feature_combination == 'concatenate':
            # 橫向連接特徵
            combined = np.column_stack(values_list)
        elif feature_combination == 'sum':
            # 特徵求和
            combined = np.sum(values_list, axis=0)
        elif feature_combination == 'mean':
            # 特徵平均
            combined = np.mean(values_list, axis=0)
        elif feature_combination == 'max':
            # 特徵最大值
            combined = np.maximum.reduce(values_list)
        else:
            raise ValueError(f"Unknown feature combination method: {feature_combination}")

        return combined

# 全局向量化器實例
_vectorizer = None
_multi_vectorizer = None

def get_time_series_vectorizer() -> TimeSeriesVectorizer:
    """獲取時間序列向量化器實例"""
    global _vectorizer
    if _vectorizer is None:
        _vectorizer = TimeSeriesVectorizer()
    return _vectorizer

def get_multi_source_vectorizer() -> MultiSourceVectorizer:
    """獲取多源向量化器實例"""
    global _multi_vectorizer
    if _multi_vectorizer is None:
        _multi_vectorizer = MultiSourceVectorizer()
    return _multi_vectorizer