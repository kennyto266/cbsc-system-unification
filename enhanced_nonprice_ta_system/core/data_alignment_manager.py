"""
Enhanced Non-Price TA System - Data Alignment Manager
负责多数据源的时间对齐和数据质量验证

核心功能:
1. TemporalAligner - 时间轴对齐器
2. MissingDataHandler - 缺失数据处理器
3. DataQualityValidator - 数据质量验证器
4. 自适应插值算法
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import warnings

@dataclass
class DataQualityMetrics:
    """数据质量指标"""
    completeness_rate: float  # 完整性率
    missing_data_ratio: float  # 缺失数据比例
    outlier_ratio: float  # 异常值比例
    consistency_score: float  # 一致性评分
    temporal_coverage: float  # 时间覆盖度

@dataclass
class AlignedDataset:
    """对齐后的数据集"""
    data: pd.DataFrame  # 对齐后的数据
    common_timeline: pd.DatetimeIndex  # 共同时间轴
    quality_metrics: Dict[str, DataQualityMetrics]  # 各数据源质量指标
    interpolation_methods: Dict[str, str]  # 使用的插值方法
    alignment_report: Dict  # 对齐报告

class TemporalAligner:
    """时间轴对齐器 - 负责将不同数据源对齐到共同时间范围"""

    def __init__(self):
        self.supported_frequencies = ['D', 'W', 'M', 'Q', 'Y']
        self.default_frequency = 'D'

    def find_common_timeline(self, datasets: Dict[str, pd.DataFrame],
                           min_coverage_ratio: float = 0.7) -> pd.DatetimeIndex:
        """找到所有数据源的共同时间轴"""
        print("🔍 寻找共同时间轴...")

        # 获取各数据源的时间范围
        timelines = {}
        for name, df in datasets.items():
            if df.index.name == 'date' or 'date' in df.columns:
                if df.index.name == 'date':
                    timelines[name] = df.index
                else:
                    timelines[name] = pd.to_datetime(df['date'])
            else:
                # 假设index已经是datetime
                timelines[name] = pd.to_datetime(df.index)

        # 找到交集时间范围
        if len(timelines) == 0:
            raise ValueError("没有找到有效的时间轴数据")

        # 计算共同时间范围
        start_dates = [timeline.min() for timeline in timelines.values()]
        end_dates = [timeline.max() for timeline in timelines.values()]

        common_start = max(start_dates)
        common_end = min(end_dates)

        print(f"📅 共同时间范围: {common_start.date()} 至 {common_end.date()}")

        # 检查时间覆盖度
        total_days = (common_end - common_start).days + 1
        coverage_ratios = {}

        for name, timeline in timelines.items():
            available_days = len(timeline[(timeline >= common_start) & (timeline <= common_end)])
            coverage_ratios[name] = available_days / total_days

        print(f"📊 各数据源时间覆盖度:")
        for name, ratio in coverage_ratios.items():
            status = "✅" if ratio >= min_coverage_ratio else "⚠️"
            print(f"  {status} {name}: {ratio:.2%}")

        # 创建共同时间轴
        common_timeline = pd.date_range(
            start=common_start,
            end=common_end,
            freq=self.default_frequency
        )

        return common_timeline

    def align_to_timeline(self, data: pd.DataFrame,
                         target_timeline: pd.DatetimeIndex,
                         method: str = 'forward_fill') -> pd.DataFrame:
        """将数据对齐到目标时间轴"""
        print(f"🔄 对齐数据到目标时间轴 (方法: {method})")

        # 确保数据索引是datetime类型
        if data.index.name != 'date' and 'date' in data.columns:
            data = data.set_index('date')

        data.index = pd.to_datetime(data.index)

        # 重新索引到目标时间轴
        aligned_data = data.reindex(target_timeline)

        # 应用插值方法
        if method == 'forward_fill':
            aligned_data = aligned_data.fillna(method='ffill')
        elif method == 'backward_fill':
            aligned_data = aligned_data.fillna(method='bfill')
        elif method == 'linear':
            aligned_data = aligned_data.interpolate(method='linear')
        elif method == 'spline':
            aligned_data = aligned_data.interpolate(method='spline', order=3)

        return aligned_data

class MissingDataHandler:
    """缺失数据处理器 - 处理各种类型的缺失数据"""

    def __init__(self):
        self.interpolation_methods = {
            'numeric': ['linear', 'spline', 'polynomial', 'forward_fill', 'backward_fill'],
            'categorical': ['forward_fill', 'backward_fill', 'mode']
        }

    def detect_missing_patterns(self, data: pd.DataFrame) -> Dict:
        """检测缺失数据模式"""
        print("🔍 检测缺失数据模式...")

        missing_info = {
            'total_missing': data.isnull().sum().sum(),
            'missing_by_column': data.isnull().sum().to_dict(),
            'missing_ratio_by_column': (data.isnull().sum() / len(data)).to_dict(),
            'consecutive_missing': {},
            'missing_patterns': []
        }

        # 检测连续缺失
        for col in data.columns:
            missing_series = data[col].isnull()
            consecutive_groups = self._find_consecutive_groups(missing_series)
            missing_info['consecutive_missing'][col] = consecutive_groups

        # 识别缺失模式
        if missing_info['total_missing'] > 0:
            if all(data[col].isnull().all() for col in data.columns if data[col].dtype == 'object'):
                missing_info['missing_patterns'].append('complete_missing')
            elif missing_info['total_missing'] / len(data) > 0.5:
                missing_info['missing_patterns'].append('extensive_missing')
            elif any(length > 30 for groups in missing_info['consecutive_missing'].values()
                    for length in groups):
                missing_info['missing_patterns'].append('long_consecutive_missing')
            else:
                missing_info['missing_patterns'].append('scattered_missing')

        print(f"📊 总缺失数据: {missing_info['total_missing']} 个点")
        return missing_info

    def _find_consecutive_groups(self, boolean_series: pd.Series) -> List[int]:
        """找到连续的True值组"""
        groups = []
        current_length = 0

        for value in boolean_series:
            if value:
                current_length += 1
            else:
                if current_length > 0:
                    groups.append(current_length)
                current_length = 0

        if current_length > 0:
            groups.append(current_length)

        return groups

    def suggest_interpolation_method(self, data: pd.DataFrame,
                                   column: str) -> str:
        """建议最佳插值方法"""
        col_data = data[column]
        missing_ratio = col_data.isnull().sum() / len(col_data)

        # 数值型数据
        if pd.api.types.is_numeric_dtype(col_data):
            if missing_ratio < 0.1:
                return 'linear'
            elif missing_ratio < 0.3:
                return 'spline'
            else:
                return 'forward_fill'

        # 分类数据
        else:
            if missing_ratio < 0.2:
                return 'forward_fill'
            else:
                return 'mode'

class DataQualityValidator:
    """数据质量验证器 - 评估和验证数据质量"""

    def __init__(self):
        self.quality_thresholds = {
            'completeness_min': 0.8,
            'outlier_max_ratio': 0.05,
            'consistency_min_score': 0.7
        }

    def validate_data_quality(self, data: pd.DataFrame,
                            data_source_name: str) -> DataQualityMetrics:
        """验证数据质量并返回质量指标"""
        print(f"🔍 验证数据源质量: {data_source_name}")

        # 计算完整性率
        completeness_rate = 1 - (data.isnull().sum().sum() / (len(data) * len(data.columns)))

        # 计算缺失数据比例
        missing_data_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))

        # 计算异常值比例（仅数值型数据）
        outlier_ratio = self._calculate_outlier_ratio(data)

        # 计算一致性评分
        consistency_score = self._calculate_consistency_score(data)

        # 计算时间覆盖度
        temporal_coverage = self._calculate_temporal_coverage(data)

        metrics = DataQualityMetrics(
            completeness_rate=completeness_rate,
            missing_data_ratio=missing_data_ratio,
            outlier_ratio=outlier_ratio,
            consistency_score=consistency_score,
            temporal_coverage=temporal_coverage
        )

        # 输出质量报告
        print(f"📊 {data_source_name} 质量指标:")
        print(f"  完整性: {completeness_rate:.2%}")
        print(f"  缺失率: {missing_data_ratio:.2%}")
        print(f"  异常值率: {outlier_ratio:.2%}")
        print(f"  一致性评分: {consistency_score:.2f}/1.0")
        print(f"  时间覆盖度: {temporal_coverage:.2%}")

        return metrics

    def _calculate_outlier_ratio(self, data: pd.DataFrame) -> float:
        """计算异常值比例"""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        total_points = 0
        outlier_points = 0

        for col in numeric_cols:
            col_data = data[col].dropna()
            if len(col_data) > 0:
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]

                total_points += len(col_data)
                outlier_points += len(outliers)

        return outlier_points / total_points if total_points > 0 else 0

    def _calculate_consistency_score(self, data: pd.DataFrame) -> float:
        """计算数据一致性评分"""
        score = 1.0

        # 检查时间序列的连续性
        if isinstance(data.index, pd.DatetimeIndex):
            time_diffs = data.index.to_series().diff().dropna()
            expected_freq = pd.Timedelta(days=1)  # 假设日频数据

            # 计算时间间隔的一致性
            consistent_intervals = (time_diffs == expected_freq).sum()
            total_intervals = len(time_diffs)

            if total_intervals > 0:
                time_consistency = consistent_intervals / total_intervals
                score *= time_consistency

        # 检查数值的合理性
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            col_data = data[col].dropna()
            if len(col_data) > 0:
                # 检查是否有负值不应该为负的情况
                if 'rate' in col.lower() or 'price' in col.lower():
                    negative_ratio = (col_data < 0).sum() / len(col_data)
                    score *= (1 - negative_ratio)

        return score

    def _calculate_temporal_coverage(self, data: pd.DataFrame) -> float:
        """计算时间覆盖度"""
        if isinstance(data.index, pd.DatetimeIndex):
            total_days = (data.index.max() - data.index.min()).days + 1
            actual_days = len(data)
            return actual_days / total_days if total_days > 0 else 1.0
        return 1.0

class DataAlignmentManager:
    """数据对齐管理器 - 统一管理多数据源的对齐和质量验证"""

    def __init__(self):
        self.temporal_aligner = TemporalAligner()
        self.missing_data_handler = MissingDataHandler()
        self.quality_validator = DataQualityValidator()

    def align_datasets(self, datasets: Dict[str, pd.DataFrame],
                      min_coverage_ratio: float = 0.7) -> AlignedDataset:
        """对齐多个数据集"""
        print("Starting data alignment process...")
        print("=" * 60)

        # 步骤1: 验证各数据源质量
        quality_metrics = {}
        for name, data in datasets.items():
            quality_metrics[name] = self.quality_validator.validate_data_quality(data, name)

        print("=" * 60)

        # 步骤2: 找到共同时间轴
        common_timeline = self.temporal_aligner.find_common_timeline(
            datasets, min_coverage_ratio
        )

        # 步骤3: 对齐各数据集
        aligned_datasets = {}
        interpolation_methods = {}

        for name, data in datasets.items():
            print(f"\n📊 处理数据源: {name}")

            # 检测缺失模式
            missing_patterns = self.missing_data_handler.detect_missing_patterns(data)

            # 建议插值方法
            suggested_method = self.missing_data_handler.suggest_interpolation_method(data, 'value')
            interpolation_methods[name] = suggested_method

            # 执行对齐
            aligned_data = self.temporal_aligner.align_to_timeline(
                data, common_timeline, suggested_method
            )
            aligned_datasets[name] = aligned_data

        # 步骤4: 创建合并数据集
        combined_data = pd.DataFrame(index=common_timeline)
        for name, aligned_data in aligned_datasets.items():
            for col in aligned_data.columns:
                combined_data[f"{name}_{col}"] = aligned_data[col]

        # 步骤5: 生成对齐报告
        alignment_report = {
            'original_data_sources': list(datasets.keys()),
            'common_timeline_start': common_timeline.min(),
            'common_timeline_end': common_timeline.max(),
            'total_aligned_days': len(common_timeline),
            'quality_metrics': {name: {
                'completeness': metrics.completeness_rate,
                'missing_ratio': metrics.missing_data_ratio,
                'outlier_ratio': metrics.outlier_ratio,
                'consistency_score': metrics.consistency_score
            } for name, metrics in quality_metrics.items()},
            'interpolation_methods': interpolation_methods,
            'final_data_shape': combined_data.shape
        }

        print("=" * 60)
        print("✅ 数据对齐完成!")
        print(f"📅 对齐时间范围: {common_timeline.min().date()} - {common_timeline.max().date()}")
        print(f"📊 最终数据形状: {combined_data.shape}")
        print(f"🔧 使用插值方法: {dict(list(interpolation_methods.items())[:3])}...")

        return AlignedDataset(
            data=combined_data,
            common_timeline=common_timeline,
            quality_metrics=quality_metrics,
            interpolation_methods=interpolation_methods,
            alignment_report=alignment_report
        )

    def export_alignment_report(self, aligned_dataset: AlignedDataset,
                               output_path: str):
        """导出对齐报告"""
        import json

        report = aligned_dataset.alignment_report
        report['export_timestamp'] = datetime.now().isoformat()

        # 转换datetime对象为字符串
        report['common_timeline_start'] = str(report['common_timeline_start'])
        report['common_timeline_end'] = str(report['common_timeline_end'])

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 对齐报告已导出至: {output_path}")

# 测试和演示功能
def demo_data_alignment():
    """演示数据对齐功能"""
    print("🎯 数据对齐管理器演示")
    print("=" * 60)

    # 创建示例数据集
    np.random.seed(42)

    # HIBOR数据（利率数据）
    hibor_dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    hibor_data = pd.DataFrame({
        'overnight_rate': np.random.uniform(1.5, 5.0, len(hibor_dates)),
        '1w_rate': np.random.uniform(2.0, 5.5, len(hibor_dates))
    }, index=hibor_dates)

    # 添加一些缺失值
    hibor_data.loc['2021-03':'2021-04', 'overnight_rate'] = np.nan
    hibor_data.loc['2023-07':'2023-08', '1w_rate'] = np.nan

    # 汇率数据（频率稍低）
    fx_dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')[:-50]  # 少50天
    fx_data = pd.DataFrame({
        'usd_hkd': np.random.uniform(7.7, 7.9, len(fx_dates))
    }, index=fx_dates)

    # 货币基础数据（有更多缺失）
    mb_dates = pd.date_range('2020-06-01', '2024-12-31', freq='D')
    mb_data = pd.DataFrame({
        'monetary_base': np.random.uniform(1800, 2200, len(mb_dates))
    }, index=mb_dates)

    # 添加大量缺失值
    mb_data.loc['2022-01':'2022-03', 'monetary_base'] = np.nan

    datasets = {
        'HIBOR': hibor_data,
        'FX_Rate': fx_data,
        'Monetary_Base': mb_data
    }

    # 创建数据对齐管理器
    manager = DataAlignmentManager()

    # 执行数据对齐
    aligned_result = manager.align_datasets(datasets)

    # 导出报告
    manager.export_alignment_report(
        aligned_result,
        'data_alignment_report_demo.json'
    )

    return aligned_result

if __name__ == "__main__":
    # 运行演示
    aligned_data = demo_data_alignment()

    print("\n🎉 演示完成!")
    print(f"对齐后的数据形状: {aligned_data.data.shape}")
    print(f"共同时间轴长度: {len(aligned_data.common_timeline)} 天")
    print("\n前5行数据预览:")
    print(aligned_data.data.head())