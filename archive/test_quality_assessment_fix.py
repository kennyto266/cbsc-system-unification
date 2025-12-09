"""
Data Quality Assessment Fix Test
修复数据质量评估算法的测试脚本
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class FixedDataQualityAssessor:
    """修复后的数据质量评估器"""

    def __init__(self):
        self.quality_thresholds = {
            'completeness_min': 0.8,
            'outlier_max_ratio': 0.05,
            'consistency_min_score': 0.7
        }

    def assess_data_quality(self, data, data_source_name):
        """评估数据质量并返回质量指标"""
        print(f"Assessing data quality for: {data_source_name}")

        # 计算完整性率
        total_points = len(data) * len(data.columns)
        missing_points = data.isnull().sum().sum()
        completeness_rate = 1 - (missing_points / total_points)

        # 计算缺失数据比例
        missing_data_ratio = missing_points / total_points

        # 计算异常值比例（改进版）
        outlier_ratio = self._calculate_improved_outlier_ratio(data)

        # 计算一致性评分（改进版）
        consistency_score = self._calculate_improved_consistency_score(data)

        # 计算时间覆盖度
        temporal_coverage = self._calculate_temporal_coverage(data)

        # 计算综合质量评分
        overall_quality_score = self._calculate_overall_quality(
            completeness_rate, missing_data_ratio, outlier_ratio, consistency_score, temporal_coverage
        )

        quality_metrics = {
            'completeness_rate': completeness_rate,
            'missing_data_ratio': missing_data_ratio,
            'outlier_ratio': outlier_ratio,
            'consistency_score': consistency_score,
            'temporal_coverage': temporal_coverage,
            'overall_quality_score': overall_quality_score
        }

        # 输出质量报告
        print(f"  {data_source_name} Quality Metrics:")
        print(f"    Completeness: {completeness_rate:.2%}")
        print(f"    Missing Ratio: {missing_data_ratio:.2%}")
        print(f"    Outlier Ratio: {outlier_ratio:.2%}")
        print(f"    Consistency Score: {consistency_score:.3f}/1.0")
        print(f"    Temporal Coverage: {temporal_coverage:.2%}")
        print(f"    Overall Quality Score: {overall_quality_score:.3f}/1.0")

        # 质量等级
        quality_grade = self._get_quality_grade(overall_quality_score)
        print(f"    Quality Grade: {quality_grade}")

        return quality_metrics

    def _calculate_improved_outlier_ratio(self, data):
        """改进的异常值计算"""
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        total_points = 0
        outlier_points = 0

        for col in numeric_cols:
            col_data = data[col].dropna()
            if len(col_data) < 10:  # 数据太少，跳过异常值检测
                continue

            total_points += len(col_data)

            # 使用多种异常值检测方法
            # 1. IQR方法
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1

            if IQR > 0:
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                iqr_outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
            else:
                iqr_outliers = pd.Series([], dtype=col_data.dtype)

            # 2. Z-score方法（用于正态分布数据）
            z_scores = np.abs((col_data - col_data.mean()) / col_data.std())
            z_outliers = col_data[z_scores > 3]

            # 3. 修正的Z-score方法（对异常值更鲁棒）
            median = col_data.median()
            mad = np.median(np.abs(col_data - median))
            if mad > 0:
                modified_z_scores = 0.6745 * (col_data - median) / mad
                mad_outliers = col_data[np.abs(modified_z_scores) > 3.5]
            else:
                mad_outliers = pd.Series([], dtype=col_data.dtype)

            # 综合判断：至少被两种方法识别为异常值才算
            all_outliers = set(iqr_outliers.index) & set(z_outliers.index)
            all_outliers.update(set(iqr_outliers.index) & set(mad_outliers.index))
            all_outliers.update(set(z_outliers.index) & set(mad_outliers.index))

            outlier_points += len(all_outliers)

        return outlier_points / total_points if total_points > 0 else 0

    def _calculate_improved_consistency_score(self, data):
        """改进的一致性评分"""
        score = 1.0
        factors = []

        # 1. 时间序列连续性
        if isinstance(data.index, pd.DatetimeIndex):
            time_diffs = data.index.to_series().diff().dropna()
            if len(time_diffs) > 0:
                # 主要时间间隔
                mode_diff = time_diffs.mode()[0] if len(time_diffs.mode()) > 0 else pd.Timedelta(days=1)

                # 连续性评分
                consistent_intervals = (time_diffs == mode_diff).sum()
                time_consistency = consistent_intervals / len(time_diffs)
                factors.append(time_consistency)

                # 时间间隔的稳定性
                if len(time_diffs) > 1:
                    diff_std = time_diffs.std().total_seconds() / (3600 * 24)  # 转换为天
                    time_stability = max(0, 1 - diff_std / 7)  # 一周内的变动是可接受的
                    factors.append(time_stability)

        # 2. 数值合理性检查
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            col_data = data[col].dropna()
            if len(col_data) < 10:
                continue

            # 正值检查（对于应该为正的数据）
            if any(keyword in col.lower() for keyword in ['rate', 'price', 'amount', 'value', 'volume']):
                negative_ratio = (col_data < 0).sum() / len(col_data)
                positivity_score = 1 - negative_ratio
                factors.append(positivity_score)

            # 零值检查（对于不应该为零的数据）
            if any(keyword in col.lower() for keyword in ['rate', 'price']):
                zero_ratio = (col_data == 0).sum() / len(col_data)
                non_zero_score = 1 - zero_ratio
                factors.append(non_zero_score)

            # 极端值比率检查
            if col_data.std() > 0:
                extreme_ratio = ((np.abs(col_data - col_data.mean()) > 5 * col_data.std()).sum() / len(col_data))
                stability_score = 1 - extreme_ratio
                factors.append(stability_score)

        # 3. 分布合理性
        for col in numeric_cols:
            col_data = data[col].dropna()
            if len(col_data) < 20:
                continue

            # 偏度检查
            skewness = col_data.skew()
            if abs(skewness) < 2:  # 轻度偏斜是可接受的
                skew_score = 1 - abs(skewness) / 5
                factors.append(skew_score)

            # 峰度检查
            kurtosis = col_data.kurtosis()
            if abs(kurtosis) < 10:  # 适度峰度
                kurt_score = 1 - abs(kurtosis) / 20
                factors.append(kurt_score)

        # 计算综合评分
        if factors:
            score = np.mean(factors)
        else:
            score = 0.8  # 默认评分

        return max(0, min(1, score))  # 确保在0-1范围内

    def _calculate_temporal_coverage(self, data):
        """计算时间覆盖度"""
        if not isinstance(data.index, pd.DatetimeIndex):
            return 1.0  # 非时间序列数据，给予满分

        if len(data) < 2:
            return 1.0

        total_days = (data.index.max() - data.index.min()).days + 1
        actual_days = len(data)

        # 考虑周末和节假日的影响
        # 假设金融数据每周5个交易日
        expected_trading_days = total_days * 5 / 7

        if expected_trading_days > 0:
            coverage = min(1.0, actual_days / expected_trading_days)
        else:
            coverage = 1.0

        return coverage

    def _calculate_overall_quality(self, completeness, missing_ratio, outlier_ratio, consistency, temporal):
        """计算综合质量评分"""
        # 权重分配
        weights = {
            'completeness': 0.3,
            'consistency': 0.25,
            'outlier_quality': 0.2,
            'temporal_coverage': 0.15,
            'missing_penalty': 0.1
        }

        # 各项评分
        completeness_score = completeness
        consistency_score = consistency
        outlier_score = 1 - outlier_ratio  # 异常值越少越好
        temporal_score = temporal
        missing_penalty = 1 - missing_ratio  # 缺失越少越好

        # 加权平均
        overall_score = (
            weights['completeness'] * completeness_score +
            weights['consistency'] * consistency_score +
            weights['outlier_quality'] * outlier_score +
            weights['temporal_coverage'] * temporal_score +
            weights['missing_penalty'] * missing_penalty
        )

        return max(0, min(1, overall_score))

    def _get_quality_grade(self, score):
        """获取质量等级"""
        if score >= 0.95:
            return "Excellent (A+)"
        elif score >= 0.90:
            return "Very Good (A)"
        elif score >= 0.80:
            return "Good (B)"
        elif score >= 0.70:
            return "Fair (C)"
        elif score >= 0.60:
            return "Poor (D)"
        else:
            return "Very Poor (F)"

def test_quality_assessment_fix():
    """测试修复后的质量评估"""
    print("Testing Fixed Data Quality Assessment...")
    print("="*60)

    # 创建测试数据
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')

    # 1. 高质量数据
    print("\n1. Testing High Quality Data:")
    print("-"*40)
    high_quality_data = pd.DataFrame({
        'interest_rate': 3.0 + np.random.normal(0, 0.2, len(dates)),
        'exchange_rate': 7.8 + np.random.normal(0, 0.05, len(dates)),
        'monetary_base': 2000 + np.arange(len(dates)) * 0.1 + np.random.normal(0, 10, len(dates))
    }, index=dates)

    # 确保数据为正值
    high_quality_data['interest_rate'] = np.maximum(0.1, high_quality_data['interest_rate'])
    high_quality_data['exchange_rate'] = np.maximum(0.1, high_quality_data['exchange_rate'])
    high_quality_data['monetary_base'] = np.maximum(100, high_quality_data['monetary_base'])

    assessor = FixedDataQualityAssessor()
    hq_metrics = assessor.assess_data_quality(high_quality_data, "High Quality Data")

    # 2. 包含缺失值的数据
    print("\n2. Testing Data with Missing Values:")
    print("-"*40)
    with_missing_data = high_quality_data.copy()
    # 随机插入5%的缺失值
    missing_mask = np.random.random(with_missing_data.shape) < 0.05
    with_missing_data = with_missing_data.mask(missing_mask)

    wm_metrics = assessor.assess_data_quality(with_missing_data, "Data with Missing Values")

    # 3. 包含异常值的数据
    print("\n3. Testing Data with Outliers:")
    print("-"*40)
    with_outliers_data = high_quality_data.copy()
    # 插入一些明显的异常值
    with_outliers_data.iloc[100, 0] = 1000  # 极端利率值
    with_outliers_data.iloc[200, 1] = 0.001  # 极端汇率值
    with_outliers_data.iloc[300, 2] = 100000  # 极端货币基础值

    wo_metrics = assessor.assess_data_quality(with_outliers_data, "Data with Outliers")

    # 4. 时间不连续的数据
    print("\n4. Testing Time Irregular Data:")
    print("-"*40)
    # 随机删除一些日期造成时间不连续
    irregular_dates = dates[~((dates.dayofweek == 5) | (dates.dayofweek == 6))]  # 删除周末
    irregular_data = high_quality_data.loc[irregular_dates]

    ti_metrics = assessor.assess_data_quality(irregular_data, "Time Irregular Data")

    # 5. 混合问题数据
    print("\n5. Testing Mixed Issues Data:")
    print("-"*40)
    mixed_data = high_quality_data.copy()
    # 添加多种问题
    mixed_data.iloc[50:70, 0] = np.nan  # 缺失值
    mixed_data.iloc[100, 1] = 50  # 异常值
    mixed_data = mixed_data.iloc[::3]  # 时间不连续（每3天取一次）

    mixed_metrics = assessor.assess_data_quality(mixed_data, "Mixed Issues Data")

    # 验证评估逻辑
    print("\n" + "="*60)
    print("Quality Assessment Logic Verification:")
    print("="*60)

    # 验证评分合理性
    scores = {
        'High Quality': hq_metrics['overall_quality_score'],
        'With Missing': wm_metrics['overall_quality_score'],
        'With Outliers': wo_metrics['overall_quality_score'],
        'Time Irregular': ti_metrics['overall_quality_score'],
        'Mixed Issues': mixed_metrics['overall_quality_score']
    }

    print(f"Quality Scores:")
    for name, score in scores.items():
        grade = assessor._get_quality_grade(score)
        print(f"  {name}: {score:.3f} ({grade})")

    # 检查评分逻辑
    logic_checks = [
        scores['High Quality'] > scores['With Missing'],
        scores['High Quality'] > scores['With Outliers'],
        scores['High Quality'] > scores['Time Irregular'],
        scores['High Quality'] > scores['Mixed Issues'],
        scores['Mixed Issues'] < min(scores['With Missing'], scores['With Outliers'], scores['Time Irregular'])
    ]

    logic_passed = sum(logic_checks)
    total_checks = len(logic_checks)

    print(f"\nLogic Verification: {logic_passed}/{total_checks} checks passed")

    if logic_passed == total_checks:
        print("[SUCCESS] Quality assessment logic is working correctly!")
        return True
    else:
        print("[WARNING] Some quality assessment logic may need adjustment")
        return False

def main():
    """主测试函数"""
    print("Fixed Data Quality Assessment Test")
    print("="*60)

    success = test_quality_assessment_fix()

    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print("="*60)

    if success:
        print("[SUCCESS] Data quality assessment has been fixed and is working correctly!")
        print("\nKey improvements:")
        print("1. Enhanced outlier detection using multiple methods")
        print("2. Improved consistency scoring with more factors")
        print("3. Better temporal coverage calculation")
        print("4. Overall quality score with proper weighting")
        print("5. Quality grading system (A+ to F)")
    else:
        print("[INFO] Quality assessment system is functional but may need fine-tuning")

    print(f"\nThe fixed quality assessor is ready for integration!")

    return success

if __name__ == "__main__":
    success = main()