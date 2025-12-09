#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU数据处理管道
重构数据管道确保100%GPU兼容性
解决数据格式不兼容导致的CPU回退问题
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Union, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import warnings

from .gpu_data_validator import GPUDataValidator, get_gpu_data_validator

logger = logging.getLogger(__name__)

class GPUPipeline:
    """GPU数据处理管道"""

    def __init__(self, gpu_device: int = 0):
        self.gpu_device = gpu_device
        self.validator = get_gpu_data_validator(gpu_device)
        self.processing_cache = {}

        logger.info(f"GPU管道初始化，设备: {gpu_device}")

    def preprocess_stock_data(self, stock_data: Union[pd.DataFrame, Dict[str, Any]]) -> Dict[str, Any]:
        """
        股票数据预处理

        Args:
            stock_data: 股票OHLCV数据

        Returns:
            GPU兼容的股票数据字典
        """
        try:
            logger.info("开始股票数据预处理")

            # 数据标准化
            if isinstance(stock_data, pd.DataFrame):
                stock_data = self._standardize_dataframe(stock_data)

            # GPU转换
            gpu_stock_data = self.validator.validate_financial_data(stock_data)

            # 数据质量检查
            self._validate_stock_data_quality(gpu_stock_data)

            logger.info(f"股票数据预处理完成，包含 {len(gpu_stock_data)} 个字段")
            return gpu_stock_data

        except Exception as e:
            logger.error(f"股票数据预处理失败: {e}")
            raise

    def preprocess_government_data(self, gov_data: Union[pd.DataFrame, Dict[str, Any]]) -> Dict[str, Any]:
        """
        政府数据预处理

        Args:
            gov_data: 政府经济数据

        Returns:
            GPU兼容的政府数据字典
        """
        try:
            logger.info("开始政府数据预处理")

            # 数据标准化
            if isinstance(gov_data, pd.DataFrame):
                gov_data = self._standardize_government_dataframe(gov_data)

            # GPU转换
            gpu_gov_data = self.validator.validate_financial_data(gov_data)

            # 政府数据质量检查
            self._validate_government_data_quality(gpu_gov_data)

            logger.info(f"政府数据预处理完成，包含 {len(gpu_gov_data)} 个指标")
            return gpu_gov_data

        except Exception as e:
            logger.error(f"政府数据预处理失败: {e}")
            raise

    def align_data_sources(self, stock_data: Dict[str, Any], gov_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        多数据源时间对齐

        Args:
            stock_data: GPU股票数据
            gov_data: GPU政府数据

        Returns:
            时间对齐后的数据
        """
        try:
            logger.info("开始数据源时间对齐")

            # 获取时间索引
            stock_dates = self._extract_dates_from_stock_data(stock_data)
            gov_dates = self._extract_dates_from_government_data(gov_data)

            if stock_dates is None:
                raise ValueError("无法提取股票数据时间索引")

            # 政府数据对齐到股票数据
            if gov_dates is not None:
                aligned_gov_data = self._align_government_to_stock(gov_data, gov_dates, stock_dates)
            else:
                logger.warning("政府数据无时间索引，跳过对齐")
                aligned_gov_data = gov_data

            logger.info("数据源时间对齐完成")
            return stock_data, aligned_gov_data

        except Exception as e:
            logger.error(f"数据源对齐失败: {e}")
            raise

    def batch_convert_to_gpu(self, data_dict: Dict[str, Union[np.ndarray, pd.Series, list]]) -> Dict[str, Any]:
        """
        批量数据GPU转换

        Args:
            data_dict: 待转换数据字典

        Returns:
            GPU数据字典
        """
        try:
            logger.info(f"开始批量GPU转换，共 {len(data_dict)} 个数据项")

            gpu_data = {}
            conversion_stats = {'successful': 0, 'failed': 0, 'failed_items': []}

            for key, data in data_dict.items():
                try:
                    gpu_data[key] = self.validator.validate_and_convert(data)
                    conversion_stats['successful'] += 1
                except Exception as e:
                    logger.error(f"转换 {key} 失败: {e}")
                    conversion_stats['failed'] += 1
                    conversion_stats['failed_items'].append(key)

            # 转换统计
            success_rate = conversion_stats['successful'] / (conversion_stats['successful'] + conversion_stats['failed']) * 100
            logger.info(f"批量转换完成: 成功率 {success_rate:.1f}%")

            if conversion_stats['failed'] > 0:
                logger.warning(f"转换失败的项: {conversion_stats['failed_items']}")

            return gpu_data

        except Exception as e:
            logger.error(f"批量GPU转换失败: {e}")
            raise

    def prepare_for_technical_analysis(self, stock_data: Dict[str, Any], gov_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        为技术分析准备数据

        Args:
            stock_data: GPU股票数据
            gov_data: GPU政府数据（可选）

        Returns:
            技术分析就绪的数据
        """
        try:
            logger.info("开始技术分析数据准备")

            # 提取关键价格数据
            analysis_data = {}

            # OHLCV数据
            for key in ['open', 'high', 'low', 'close', 'volume']:
                if key in stock_data:
                    analysis_data[key] = stock_data[key]
                    logger.debug(f"添加 {key} 数据，长度: {len(stock_data[key])}")

            # 如果缺少某些字段，尝试从close推导
            self._fill_missing_ohlcv_fields(analysis_data)

            # 添加政府数据
            if gov_data:
                for key, value in gov_data.items():
                    if len(value) == len(analysis_data['close']):
                        analysis_data[f'gov_{key}'] = value
                        logger.debug(f"添加政府指标 {key}")

            # 数据完整性检查
            self._validate_analysis_data_integrity(analysis_data)

            logger.info(f"技术分析数据准备完成，包含 {len(analysis_data)} 个指标")
            return analysis_data

        except Exception as e:
            logger.error(f"技术分析数据准备失败: {e}")
            raise

    def get_processing_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'gpu_device': self.gpu_device,
            'memory_usage': self.validator.get_memory_usage(),
            'cache_size': len(self.processing_cache),
            'validator_status': 'active' if self.validator else 'inactive'
        }

    def cleanup(self):
        """清理资源"""
        try:
            self.validator.cleanup_memory()
            self.processing_cache.clear()
            logger.info("GPU管道资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")

    # 私有方法

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化DataFrame格式"""
        # 确保索引为日期时间
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            else:
                # 尝试将索引转换为日期时间
                df.index = pd.to_datetime(df.index)

        # 标准化列名
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adj_close'
        }

        df = df.rename(columns=column_mapping)

        # 移除完全为空的列
        df = df.dropna(axis=1, how='all')

        return df

    def _standardize_government_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化政府数据DataFrame格式"""
        # 政府数据处理逻辑
        if 'date' not in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            # 尝试第一列为日期
            first_col = df.columns[0]
            if 'date' in first_col.lower() or 'time' in first_col.lower():
                df = df.rename(columns={first_col: 'date'})
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)

        return df

    def _validate_stock_data_quality(self, gpu_data: Dict[str, Any]):
        """验证股票数据质量"""
        try:
            import cupy as cp

            # 检查必要字段
            required_fields = ['close']
            for field in required_fields:
                if field not in gpu_data:
                    raise ValueError(f"缺少必要字段: {field}")

            # 检查数据长度
            close_length = len(gpu_data['close'])
            for key, value in gpu_data.items():
                if len(value) != close_length:
                    logger.warning(f"字段 {key} 长度不匹配: {len(value)} vs {close_length}")

            # 检查价格合理性
            close_prices = gpu_data['close']
            if cp.any(close_prices <= 0):
                raise ValueError("价格数据包含非正值")

            # 检查数据连续性
            if 'high' in gpu_data and 'low' in gpu_data:
                high_prices = gpu_data['high']
                low_prices = gpu_data['low']
                if cp.any(high_prices < low_prices):
                    logger.warning("检测到 high < low 的异常数据")

        except Exception as e:
            logger.error(f"股票数据质量验证失败: {e}")
            raise

    def _validate_government_data_quality(self, gpu_data: Dict[str, Any]):
        """验证政府数据质量"""
        try:
            import cupy as cp

            for key, value in gpu_data.items():
                # 检查NaN值
                nan_count = cp.sum(cp.isnan(value))
                if nan_count > 0:
                    logger.warning(f"政府指标 {key} 包含 {nan_count} 个NaN值")

                # 检查无穷值
                inf_count = cp.sum(cp.isinf(value))
                if inf_count > 0:
                    logger.warning(f"政府指标 {key} 包含 {inf_count} 个无穷值")

        except Exception as e:
            logger.error(f"政府数据质量验证失败: {e}")

    def _extract_dates_from_stock_data(self, stock_data: Dict[str, Any]):
        """从股票数据提取时间索引"""
        # 查找日期相关字段
        date_fields = ['date', 'datetime', 'time', 'timestamp']
        for field in date_fields:
            if field in stock_data:
                return stock_data[field]

        # 如果没有日期字段，返回None
        return None

    def _extract_dates_from_government_data(self, gov_data: Dict[str, Any]):
        """从政府数据提取时间索引"""
        return self._extract_dates_from_stock_data(gov_data)

    def _align_government_to_stock(self, gov_data: Dict[str, Any], gov_dates, stock_dates):
        """政府数据对齐到股票数据时间"""
        try:
            import cupy as cp

            aligned_data = {}
            stock_dates_np = cp.asnumpy(stock_dates)
            gov_dates_np = cp.asnumpy(gov_dates)

            for key, value in gov_data.items():
                if key.endswith('_dates'):
                    continue  # 跳过日期字段

                # 对齐数据
                aligned_value = self._interpolate_to_dates(value, gov_dates_np, stock_dates_np)
                aligned_data[key] = aligned_value

            return aligned_data

        except Exception as e:
            logger.error(f"政府数据对齐失败: {e}")
            raise

    def _interpolate_to_dates(self, values, source_dates, target_dates):
        """数据插值到目标日期"""
        try:
            import cupy as cp

            values_np = cp.asnumpy(values)

            # 使用pandas进行插值
            source_series = pd.Series(values_np, index=pd.to_datetime(source_dates))
            target_index = pd.to_datetime(target_dates)

            # 前向填充 + 线性插值
            interpolated = source_series.reindex(target_index, method='ffill').interpolate(method='time')

            # 填充剩余NaN
            interpolated = interpolated.fillna(method='bfill').fillna(method='ffill')

            return cp.asarray(interpolated.values)

        except Exception as e:
            logger.error(f"数据插值失败: {e}")
            raise

    def _fill_missing_ohlcv_fields(self, analysis_data: Dict[str, Any]):
        """填补缺失的OHLCV字段"""
        if 'close' in analysis_data:
            close_data = analysis_data['close']

            # 从close推导其他字段
            if 'open' not in analysis_data:
                analysis_data['open'] = close_data  # 简化处理
                logger.debug("从close推导open字段")

            if 'high' not in analysis_data:
                analysis_data['high'] = close_data * 1.01  # 假设1%涨幅
                logger.debug("从close推导high字段")

            if 'low' not in analysis_data:
                analysis_data['low'] = close_data * 0.99  # 假设1%跌幅
                logger.debug("从close推导low字段")

            if 'volume' not in analysis_data:
                # 生成模拟成交量
                try:
                    import cupy as cp
                    analysis_data['volume'] = cp.ones_like(close_data) * 1000000
                    logger.debug("生成模拟volume字段")
                except:
                    pass

    def _validate_analysis_data_integrity(self, analysis_data: Dict[str, Any]):
        """验证分析数据完整性"""
        try:
            if 'close' not in analysis_data:
                raise ValueError("缺少close价格数据")

            close_length = len(analysis_data['close'])
            logger.debug(f"分析数据长度: {close_length}")

            for key, value in analysis_data.items():
                if len(value) != close_length:
                    logger.warning(f"分析数据 {key} 长度不匹配: {len(value)} vs {close_length}")

        except Exception as e:
            logger.error(f"分析数据完整性验证失败: {e}")
            raise


def get_gpu_pipeline(gpu_device: int = 0) -> GPUPipeline:
    """获取GPU管道实例"""
    return GPUPipeline(gpu_device)


# 测试代码
if __name__ == "__main__":
    # 创建测试数据
    test_stock_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'close': np.random.uniform(100, 200, 10),
        'volume': np.random.randint(1000, 5000, 10)
    })

    test_gov_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'hibor': np.random.uniform(2, 5, 10),
        'monetary_base': np.random.uniform(1000, 2000, 10)
    })

    # 测试GPU管道
    try:
        pipeline = get_gpu_pipeline()

        # 数据预处理
        gpu_stock = pipeline.preprocess_stock_data(test_stock_data)
        gpu_gov = pipeline.preprocess_government_data(test_gov_data)

        # 数据对齐
        aligned_stock, aligned_gov = pipeline.align_data_sources(gpu_stock, gpu_gov)

        # 技术分析准备
        analysis_data = pipeline.prepare_for_technical_analysis(aligned_stock, aligned_gov)

        print("GPU管道测试成功")
        print(f"分析数据字段: {list(analysis_data.keys())}")
        print(pipeline.get_processing_statistics())

        # 清理
        pipeline.cleanup()

    except Exception as e:
        print(f"GPU管道测试失败: {e}")