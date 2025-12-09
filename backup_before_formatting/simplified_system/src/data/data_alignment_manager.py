#!/usr/bin/env python3
"""
Data Alignment Manager
數據時間對齊管理器 - 解决不同數據源時間長度不匹配的核心問題
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
import logging
from pathlib import Path
import json

class TemporalAligner:
    """時間軸對齊器 - 統一不同數據源的時間範圍"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def find_common_timeframe(self, data_dict: Dict[str, pd.DataFrame]) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """
        找到所有數據源的共同時間範圍

        Args:
            data_dict: 數據字典 {source_name: DataFrame}

        Returns:
            (start_date, end_date): 共同時間範圍
        """
        date_ranges = {}

        for source_name, df in data_dict.items():
            if df.empty:
                continue

            # 嘗試找到日期列
            date_col = self._identify_date_column(df)
            if date_col is None:
                self.logger.warning(f"No date column found in {source_name}")
                continue

            # 轉換為datetime
            dates = pd.to_datetime(df[date_col])
            valid_dates = dates.dropna()

            if not valid_dates.empty:
                date_ranges[source_name] = {
                    'start': valid_dates.min(),
                    'end': valid_dates.max(),
                    'count': len(valid_dates)
                }

        if not date_ranges:
            raise ValueError("No valid date ranges found in any dataset")

        # 找到交集
        start_dates = [info['start'] for info in date_ranges.values()]
        end_dates = [info['end'] for info in date_ranges.values()]

        common_start = max(start_dates)  # 最晚的開始日期
        common_end = min(end_dates)      # 最早的結束日期

        self.logger.info(f"Common timeframe: {common_start.date()} to {common_end.date()}")

        # 記錄每個數據源的時間範圍信息
        for source_name, info in date_ranges.items():
            self.logger.info(f"{source_name}: {info['start'].date()} to {info['end'].date()} ({info['count']} records)")

        return common_start, common_end

    def _identify_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """識別日期列"""
        possible_date_cols = ['date', 'end_of_date', 'end_of_day', 'time', 'datetime']

        # 首先檢查明確的日期列名
        for col in possible_date_cols:
            if col in df.columns:
                return col

        # 檢查包含日期關鍵詞的列
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time', 'end']):
                return col

        return None

    def align_to_timeframe(self, df: pd.DataFrame, start_date: pd.Timestamp,
                          end_date: pd.Timestamp, date_col: str = None) -> pd.DataFrame:
        """
        將DataFrame對齊到指定的時間範圍

        Args:
            df: 原始數據框
            start_date: 開始日期
            end_date: 結束日期
            date_col: 日期列名

        Returns:
            對齊後的DataFrame
        """
        if df.empty:
            return df

        # 識別日期列
        if date_col is None:
            date_col = self._identify_date_column(df)

        if date_col is None:
            self.logger.warning("No date column found, returning original dataframe")
            return df

        # 轉換日期列
        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])

        # 過濾到共同時間範圍
        mask = (df_copy[date_col] >= start_date) & (df_copy[date_col] <= end_date)
        aligned_df = df_copy[mask].copy()

        # 按日期排序
        aligned_df = aligned_df.sort_values(date_col).reset_index(drop=True)

        self.logger.info(f"Aligned data: {len(df)} -> {len(aligned_df)} records")

        return aligned_df


class MissingDataHandler:
    """缺失數據處理器 - 智能處理數據缺失問題"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def detect_missing_patterns(self, df: pd.DataFrame, date_col: str) -> Dict:
        """
        檢測缺失數據模式

        Args:
            df: 數據框
            date_col: 日期列名

        Returns:
            缺失模式報告
        """
        if df.empty:
            return {'missing_ratio': 1.0, 'patterns': []}

        # 確保日期列是datetime類型
        dates = pd.to_datetime(df[date_col])
        df_sorted = df.loc[dates.argsort()].reset_index(drop=True)
        df_sorted[date_col] = dates.sort_values()

        # 計算應有的日期範圍（假設是日級數據）
        start_date = dates.min()
        end_date = dates.max()
        expected_dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # 找到缺失的日期
        actual_dates = set(dates.dt.date)
        missing_dates = set(expected_dates.date) - actual_dates

        missing_ratio = len(missing_dates) / len(expected_dates) if len(expected_dates) > 0 else 0

        # 分析缺失模式
        patterns = []
        if missing_dates:
            missing_list = sorted(missing_dates)
            current_gap = [missing_list[0]]

            for i in range(1, len(missing_list)):
                if (missing_list[i] - current_gap[-1]).days == 1:
                    current_gap.append(missing_list[i])
                else:
                    patterns.append({
                        'start': current_gap[0],
                        'end': current_gap[-1],
                        'length': len(current_gap)
                    })
                    current_gap = [missing_list[i]]

            # 添加最後一個gap
            if current_gap:
                patterns.append({
                    'start': current_gap[0],
                    'end': current_gap[-1],
                    'length': len(current_gap)
                })

        report = {
            'total_records': len(df),
            'expected_records': len(expected_dates),
            'missing_records': len(missing_dates),
            'missing_ratio': missing_ratio,
            'patterns': patterns,
            'consecutive_gaps': len(patterns)
        }

        self.logger.info(f"Missing data analysis: {missing_ratio:.2%} missing, {len(patterns)} gaps")

        return report

    def fill_missing_data(self, df: pd.DataFrame, date_col: str, method: str = 'forward_fill',
                         value_columns: List[str] = None) -> pd.DataFrame:
        """
        填充缺失數據

        Args:
            df: 原始數據框
            date_col: 日期列名
            method: 填充方法 ('forward_fill', 'linear', 'spline', 'interpolate')
            value_columns: 需要填充的數值列

        Returns:
            填充後的DataFrame
        """
        if df.empty:
            return df

        df_copy = df.copy()
        df_copy[date_col] = pd.to_datetime(df_copy[date_col])

        # 創建完整的日期範圍
        start_date = df_copy[date_col].min()
        end_date = df_copy[date_col].max()
        full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        # 設置日期為索引
        df_copy = df_copy.set_index(date_col)

        # 重新索引到完整的日期範圍
        df_reindexed = df_copy.reindex(full_date_range)

        # 識別需要填充的列
        if value_columns is None:
            value_columns = df_reindexed.select_dtypes(include=[np.number]).columns.tolist()

        # 根據方法填充數據
        if method == 'forward_fill':
            df_reindexed[value_columns] = df_reindexed[value_columns].fillna(method='ffill')
        elif method == 'linear':
            df_reindexed[value_columns] = df_reindexed[value_columns].interpolate(method='linear')
        elif method == 'spline':
            df_reindexed[value_columns] = df_reindexed[value_columns].interpolate(method='spline', order=2)
        elif method == 'interpolate':
            df_reindexed[value_columns] = df_reindexed[value_columns].interpolate()
        else:
            self.logger.warning(f"Unknown fill method: {method}, using forward_fill")
            df_reindexed[value_columns] = df_reindexed[value_columns].fillna(method='ffill')

        # 重置索引
        df_filled = df_reindexed.reset_index()
        df_filled = df_filled.rename(columns={'index': date_col})

        # 記錄填充統計
        original_count = len(df)
        filled_count = len(df_filled)
        filled_records = filled_count - original_count

        self.logger.info(f"Filled {filled_records} missing records using {method} method")

        return df_filled


class DataQualityValidator:
    """數據質量驗證器 - 確保數據質量和一致性"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_data_quality(self, df: pd.DataFrame, data_source: str = None) -> Dict:
        """
        驗證數據質量

        Args:
            df: 數據框
            data_source: 數據源名稱

        Returns:
            質量評估報告
        """
        quality_report = {
            'data_source': data_source,
            'total_records': len(df),
            'total_columns': len(df.columns),
            'completeness_score': 0.0,
            'consistency_score': 0.0,
            'validity_score': 0.0,
            'overall_score': 0.0,
            'issues': [],
            'recommendations': []
        }

        if df.empty:
            quality_report['issues'].append("Empty dataset")
            quality_report['recommendations'].append("Check data collection process")
            return quality_report

        # 1. 完整性檢查
        null_ratios = df.isnull().sum() / len(df)
        completeness_score = max(0, 1 - null_ratios.mean())
        quality_report['completeness_score'] = completeness_score

        # 檢查嚴重缺失的列
        for col, ratio in null_ratios.items():
            if ratio > 0.5:
                quality_report['issues'].append(f"Column '{col}' has {ratio:.1%} missing values")
                quality_report['recommendations'].append(f"Consider imputing or removing '{col}' column")

        # 2. 一致性檢查
        consistency_issues = 0
        total_checks = 0

        # 檢查數值列的合理性
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            total_checks += 1
            values = df[col].dropna()
            if not values.empty:
                # 檢查異常值（使用IQR方法）
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((values < (Q1 - 1.5 * IQR)) | (values > (Q3 + 1.5 * IQR))).sum()
                outlier_ratio = outliers / len(values)

                if outlier_ratio > 0.1:  # 超過10%異常值
                    consistency_issues += 1
                    quality_report['issues'].append(f"Column '{col}' has {outlier_ratio:.1%} outliers")

        consistency_score = max(0, 1 - consistency_issues / total_checks) if total_checks > 0 else 1
        quality_report['consistency_score'] = consistency_score

        # 3. 有效性檢查
        validity_issues = 0
        total_validity_checks = 0

        # 檢查日期列的有效性
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['date', 'time']):
                total_validity_checks += 1
                try:
                    dates = pd.to_datetime(df[col])
                    if dates.isnull().all():
                        validity_issues += 1
                        quality_report['issues'].append(f"Date column '{col}' contains no valid dates")
                except:
                    validity_issues += 1
                    quality_report['issues'].append(f"Column '{col}' cannot be converted to datetime")

        # 檢查數值列的有效性
        for col in numeric_cols:
            total_validity_checks += 1
            values = df[col]
            if (values < 0).any() and 'rate' in col.lower():
                # 某些利率不應該為負
                negative_ratio = (values < 0).sum() / len(values)
                if negative_ratio > 0:
                    validity_issues += 1
                    quality_report['issues'].append(f"Rate column '{col}' has {negative_ratio:.1%} negative values")

        validity_score = max(0, 1 - validity_issues / total_validity_checks) if total_validity_checks > 0 else 1
        quality_report['validity_score'] = validity_score

        # 計算總體分數
        quality_report['overall_score'] = (completeness_score + consistency_score + validity_score) / 3

        # 添加建議
        if quality_report['overall_score'] < 0.7:
            quality_report['recommendations'].append("Overall data quality is below threshold")

        if not quality_report['issues']:
            quality_report['recommendations'].append("Data quality is acceptable")

        self.logger.info(f"Data quality validation for {data_source}: overall score {quality_report['overall_score']:.3f}")

        return quality_report


class DataAlignmentManager:
    """數據時間對齊管理器 - 統一管理數據對齊、缺失處理和質量驗證"""

    def __init__(self):
        self.temporal_aligner = TemporalAligner()
        self.missing_data_handler = MissingDataHandler()
        self.quality_validator = DataQualityValidator()
        self.logger = logging.getLogger(__name__)

    def align_multiple_sources(self, data_dict: Dict[str, pd.DataFrame],
                               fill_missing: bool = True,
                               fill_method: str = 'forward_fill',
                               validate_quality: bool = True) -> Dict:
        """
        對齊多個數據源到共同的時間範圍

        Args:
            data_dict: 數據字典 {source_name: DataFrame}
            fill_missing: 是否填充缺失數據
            fill_method: 填充方法
            validate_quality: 是否驗證數據質量

        Returns:
            對齊結果字典
        """
        alignment_result = {
            'success': False,
            'common_timeframe': None,
            'aligned_data': {},
            'missing_data_reports': {},
            'quality_reports': {},
            'summary': {},
            'errors': []
        }

        try:
            self.logger.info(f"Starting alignment for {len(data_dict)} data sources")

            # Step 1: 找到共同時間範圍
            common_start, common_end = self.temporal_aligner.find_common_timeframe(data_dict)
            alignment_result['common_timeframe'] = {
                'start': common_start.date(),
                'end': common_end.date(),
                'days': (common_end - common_start).days
            }

            # Step 2: 對每個數據源進行對齊
            for source_name, df in data_dict.items():
                if df.empty:
                    alignment_result['errors'].append(f"Data source '{source_name}' is empty")
                    continue

                try:
                    # 識別日期列
                    date_col = self.temporal_aligner._identify_date_column(df)
                    if date_col is None:
                        alignment_result['errors'].append(f"No date column found in '{source_name}'")
                        continue

                    # 對齊到共同時間範圍
                    aligned_df = self.temporal_aligner.align_to_timeframe(
                        df, common_start, common_end, date_col
                    )

                    # 檢測缺失數據模式
                    missing_report = self.missing_data_handler.detect_missing_patterns(aligned_df, date_col)
                    alignment_result['missing_data_reports'][source_name] = missing_report

                    # 填充缺失數據
                    if fill_missing and missing_report['missing_ratio'] > 0:
                        value_columns = aligned_df.select_dtypes(include=[np.number]).columns.tolist()
                        aligned_df = self.missing_data_handler.fill_missing_data(
                            aligned_df, date_col, fill_method, value_columns
                        )

                    # 數據質量驗證
                    if validate_quality:
                        quality_report = self.quality_validator.validate_data_quality(aligned_df, source_name)
                        alignment_result['quality_reports'][source_name] = quality_report

                    alignment_result['aligned_data'][source_name] = aligned_df

                except Exception as e:
                    error_msg = f"Error processing '{source_name}': {str(e)}"
                    alignment_result['errors'].append(error_msg)
                    self.logger.error(error_msg)

            # Step 3: 生成總結報告
            successful_sources = len(alignment_result['aligned_data'])
            total_sources = len(data_dict)

            alignment_result['success'] = successful_sources > 0

            # 計算平均質量分數
            if alignment_result['quality_reports']:
                avg_quality = np.mean([report['overall_score'] for report in alignment_result['quality_reports'].values()])
            else:
                avg_quality = 0

            # 計算總缺失率
            total_records_before = sum(len(df) for df in data_dict.values())
            total_records_after = sum(len(df) for df in alignment_result['aligned_data'].values())

            alignment_result['summary'] = {
                'total_sources': total_sources,
                'successful_sources': successful_sources,
                'success_rate': successful_sources / total_sources,
                'average_quality_score': avg_quality,
                'total_records_before': total_records_before,
                'total_records_after': total_records_after,
                'record_change_ratio': total_records_after / total_records_before if total_records_before > 0 else 0
            }

            self.logger.info(f"Alignment completed: {successful_sources}/{total_sources} sources successful")

        except Exception as e:
            error_msg = f"Alignment failed: {str(e)}"
            alignment_result['errors'].append(error_msg)
            self.logger.error(error_msg)

        return alignment_result

    def save_alignment_result(self, result: Dict, output_dir: str = None):
        """
        保存對齊結果

        Args:
            result: 對齊結果
            output_dir: 輸出目錄
        """
        if output_dir is None:
            output_dir = Path('data/aligned')
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存對齊後的數據
        for source_name, df in result['aligned_data'].items():
            csv_path = output_dir / f"{source_name}_aligned_{timestamp}.csv"
            df.to_csv(csv_path, index=False)
            self.logger.info(f"Saved aligned data: {csv_path}")

        # 保存報告
        report_path = output_dir / f"alignment_report_{timestamp}.json"

        # 準備可序列化的報告
        serializable_result = {
            'success': result['success'],
            'common_timeframe': result['common_timeframe'],
            'missing_data_reports': result['missing_data_reports'],
            'quality_reports': result['quality_reports'],
            'summary': result['summary'],
            'errors': result['errors'],
            'saved_files': [f"{name}_aligned_{timestamp}.csv" for name in result['aligned_data'].keys()]
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"Alignment report saved: {report_path}")
        return report_path


def main():
    """主測試函數"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # 創建對齊管理器
    manager = DataAlignmentManager()

    # 測試數據加載
    enhanced_data_dir = Path('data/enhanced')
    data_dict = {}

    # 加載已收集的增強數據
    for file_path in enhanced_data_dir.glob('*_enhanced_*.csv'):
        source_name = file_path.stem.split('_enhanced_')[0]
        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                data_dict[source_name] = df
                print(f"[LOADED] {source_name}: {len(df)} records, {len(df.columns)} columns")
        except Exception as e:
            print(f"[ERROR] Failed to load {source_name}: {e}")

    if not data_dict:
        print("[ERROR] No enhanced data found. Please run data collection first.")
        return

    print(f"\n[START] Data alignment for {len(data_dict)} sources")
    print("=" * 60)

    # 執行數據對齊
    alignment_result = manager.align_multiple_sources(
        data_dict,
        fill_missing=True,
        fill_method='forward_fill',
        validate_quality=True
    )

    # 顯示結果
    print("\n[RESULT] Alignment Results:")
    print(f"Success: {alignment_result['success']}")
    print(f"Common timeframe: {alignment_result['common_timeframe']}")

    if alignment_result['success']:
        print(f"\nAligned sources: {len(alignment_result['aligned_data'])}")
        for source_name, df in alignment_result['aligned_data'].items():
            quality_score = alignment_result['quality_reports'].get(source_name, {}).get('overall_score', 0)
            missing_ratio = alignment_result['missing_data_reports'].get(source_name, {}).get('missing_ratio', 0)
            print(f"  {source_name}: {len(df)} records, quality={quality_score:.3f}, missing={missing_ratio:.2%}")

        print(f"\nSummary: {alignment_result['summary']}")

        # 保存結果
        report_path = manager.save_alignment_result(alignment_result)
        print(f"\n[COMPLETE] Alignment results saved: {report_path}")
    else:
        print("\nErrors:")
        for error in alignment_result['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    main()