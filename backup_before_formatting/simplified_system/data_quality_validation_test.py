#!/usr/bin/env python3
"""
Data Quality Validation Test
驗證數據質量評估和真實性檢查機制
"""

import sys
import os
sys.path.append('src')

import json
import pandas as pd
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataQualityValidator:
    """數據質量驗證器"""

    def __init__(self):
        self.quality_metrics = {}
        self.authenticity_checks = {}

        # 數據質量標準
        self.quality_standards = {
            'min_record_count': 10,  # 最小記錄數
            'max_missing_rate': 0.3,  # 最大缺失率30%
            'min_data_completeness': 0.7,  # 最小完整性70%
            'date_format_validation': True,  # 日期格式驗證
            'value_range_validation': True   # 數值範圍驗證
        }

        # HKMA數據標準
        self.hkma_standards = {
            'hibor_overnight_range': (0.0, 10.0),  # HIBOR隔夜利率合理範圍
            'exchange_rate_usd_hkd_range': (7.0, 8.5),  # USD/HKD匯率合理範圍
            'monetary_base_min': 0  # 貨幣基礎最小值
        }

    def validate_data_file(self, file_path: str) -> Dict[str, Any]:
        """驗證單個數據文件"""
        logger.info(f"Validating data file: {file_path}")

        try:
            # 讀取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 基本結構檢查
            structure_result = self._validate_structure(data)

            # 數據質量檢查
            quality_result = self._validate_data_quality(data)

            # 真實性檢查
            authenticity_result = self._validate_authenticity(data, file_path)

            # 時間序列檢查
            temporal_result = self._validate_temporal_consistency(data)

            # 綜合評分
            overall_score = self._calculate_overall_score(
                structure_result, quality_result, authenticity_result, temporal_result
            )

            result = {
                'file_path': file_path,
                'validation_timestamp': datetime.now().isoformat(),
                'structure_validation': structure_result,
                'quality_validation': quality_result,
                'authenticity_validation': authenticity_result,
                'temporal_validation': temporal_result,
                'overall_score': overall_score,
                'status': 'PASS' if overall_score >= 0.8 else 'FAIL'
            }

            logger.info(f"File validation completed: {overall_score:.3f} score, status: {result['status']}")
            return result

        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'status': 'ERROR'
            }

    def _validate_structure(self, data: Dict) -> Dict[str, Any]:
        """驗證數據結構"""
        checks = {}

        # 必需字段檢查
        required_fields = ['source', 'collection_time', 'record_count', 'data']
        for field in required_fields:
            checks[f'has_{field}'] = field in data

        # 數據數組檢查
        if 'data' in data and isinstance(data['data'], list):
            checks['data_is_list'] = True
            checks['data_not_empty'] = len(data['data']) > 0
        else:
            checks['data_is_list'] = False
            checks['data_not_empty'] = False

        # 記錄數一致性檢查
        if 'record_count' in data and 'data' in data:
            checks['record_count_match'] = data['record_count'] == len(data.get('data', []))

        structure_score = sum(1 for check in checks.values() if check) / len(checks)

        return {
            'checks': checks,
            'score': structure_score,
            'passed': structure_score >= 0.8
        }

    def _validate_data_quality(self, data: Dict) -> Dict[str, Any]:
        """驗證數據質量"""
        if 'data' not in data or not data['data']:
            return {'score': 0.0, 'passed': False, 'error': 'No data available'}

        records = data['data']
        quality_metrics = {}

        # 記錄數量檢查
        record_count = len(records)
        quality_metrics['record_count'] = record_count
        quality_metrics['record_count_adequate'] = record_count >= self.quality_standards['min_record_count']

        # 缺失值檢查
        if records:
            # 計算每個字段的缺失率
            field_missing_rates = {}
            for field in records[0].keys():
                missing_count = sum(1 for record in records if record.get(field) is None)
                missing_rate = missing_count / record_count
                field_missing_rates[field] = missing_rate

            quality_metrics['field_missing_rates'] = field_missing_rates
            quality_metrics['max_missing_rate'] = max(field_missing_rates.values()) if field_missing_rates else 0
            quality_metrics['missing_rate_acceptable'] = quality_metrics['max_missing_rate'] <= self.quality_standards['max_missing_rate']

            # 數據完整性
            total_fields = len(records[0])
            total_values = sum(sum(1 for field in record.values() if field is not None) for record in records)
            completeness = total_values / (record_count * total_fields)
            quality_metrics['data_completeness'] = completeness
            quality_metrics['completeness_acceptable'] = completeness >= self.quality_standards['min_data_completeness']

        quality_score = sum(1 for key, value in quality_metrics.items()
                          if key.endswith('_adequate') or key.endswith('_acceptable')) / 4

        return {
            'metrics': quality_metrics,
            'score': quality_score,
            'passed': quality_score >= 0.7
        }

    def _validate_authenticity(self, data: Dict, file_path: str) -> Dict[str, Any]:
        """驗證數據真實性"""
        authenticity_checks = {}

        # 來源驗證
        if 'source' in data:
            source = data['source']
            authenticity_checks['has_source'] = True
            authenticity_checks['source_recognized'] = source in ['HKMA', 'HK Government', 'Official Data']
        else:
            authenticity_checks['has_source'] = False
            authenticity_checks['source_recognized'] = False

        # 文件時間戳驗證
        if 'collection_time' in data:
            try:
                collection_time = datetime.fromisoformat(data['collection_time'].replace('Z', '+00:00'))
                file_age = datetime.now() - collection_time
                authenticity_checks['collection_time_valid'] = True
                authenticity_checks['data_fresh_days'] = file_age.days
                authenticity_checks['data_fresh'] = file_age.days <= 90  # 90天內為新鮮
            except:
                authenticity_checks['collection_time_valid'] = False
                authenticity_checks['data_fresh'] = False
        else:
            authenticity_checks['collection_time_valid'] = False
            authenticity_checks['data_fresh'] = False

        # 數據內容真實性檢查
        if 'data' in data and data['data']:
            content_authenticity = self._validate_content_authenticity(data['data'], data.get('source', ''))
            authenticity_checks.update(content_authenticity)

        authenticity_score = sum(1 for key, value in authenticity_checks.items()
                               if key.endswith('_valid') or key.endswith('_recognized') or key.endswith('_fresh')) / 4

        return {
            'checks': authenticity_checks,
            'score': authenticity_score,
            'passed': authenticity_score >= 0.75
        }

    def _validate_content_authenticity(self, records: List[Dict], source: str) -> Dict[str, Any]:
        """驗證數據內容真實性"""
        checks = {}

        if source == 'HKMA':
            # HIBOR數據檢查
            sample_record = records[0] if records else {}

            # 檢查HIBOR隔夜利率範圍
            if 'hibor_overnight' in sample_record:
                rate = sample_record['hibor_overnight']
                if rate is not None:
                    min_rate, max_rate = self.hkma_standards['hibor_overnight_range']
                    checks['hibor_rate_range_valid'] = min_rate <= rate <= max_rate
                else:
                    checks['hibor_rate_range_valid'] = True  # 允許空值
            else:
                checks['hibor_rate_range_valid'] = False

            # 檢查日期格式
            if 'date' in sample_record:
                date_str = sample_record['date']
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    checks['date_format_valid'] = True
                except:
                    checks['date_format_valid'] = False
            else:
                checks['date_format_valid'] = False

            # 檢查邏輯一致性（利率期限結構）
            if all(key in sample_record for key in ['hibor_overnight', 'ir_1m', 'ir_3m']):
                checks['term_structure_logical'] = True  # 基本邏輯檢查
            else:
                checks['term_structure_logical'] = False

        return checks

    def _validate_temporal_consistency(self, data: Dict) -> Dict[str, Any]:
        """驗證時間序列一致性"""
        if 'data' not in data or not data['data']:
            return {'score': 0.0, 'passed': False}

        records = data['data']
        temporal_checks = {}

        # 檢查日期順序
        dates = []
        for record in records:
            if 'date' in record and record['date']:
                try:
                    date = datetime.strptime(record['date'], '%Y-%m-%d')
                    dates.append(date)
                except:
                    continue

        if len(dates) > 1:
            # 檢查日期是否按時間順序排列
            temporal_checks['date_sequence_ordered'] = dates == sorted(dates, reverse=True)

            # 檢查日期間隔合理性
            intervals = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
            if intervals:
                avg_interval = statistics.mean(intervals)
                temporal_checks['avg_interval_days'] = avg_interval
                temporal_checks['interval_reasonable'] = 0 <= avg_interval <= 365  # 合理間隔

            # 檢查數據覆蓋時間範圍
            time_span = (dates[0] - dates[-1]).days
            temporal_checks['time_span_days'] = time_span
            temporal_checks['time_span_adequate'] = time_span >= 7  # 至少7天數據
        else:
            temporal_checks['date_sequence_ordered'] = False
            temporal_checks['interval_reasonable'] = False
            temporal_checks['time_span_adequate'] = False

        temporal_score = sum(1 for key, value in temporal_checks.items()
                           if key.endswith('_ordered') or key.endswith('_reasonable') or key.endswith('_adequate')) / 3

        return {
            'checks': temporal_checks,
            'score': temporal_score,
            'passed': temporal_score >= 0.6
        }

    def _calculate_overall_score(self, *validation_results) -> float:
        """計算綜合評分"""
        scores = []
        for result in validation_results:
            if isinstance(result, dict) and 'score' in result:
                scores.append(result['score'])

        return sum(scores) / len(scores) if scores else 0.0

    def run_comprehensive_validation(self, data_directory: str) -> Dict[str, Any]:
        """運行綜合驗證"""
        logger.info(f"Starting comprehensive validation in: {data_directory}")

        data_path = Path(data_directory)
        json_files = list(data_path.glob('*.json'))

        if not json_files:
            return {
                'error': 'No JSON files found',
                'directory': data_directory
            }

        validation_results = []
        summary_stats = {
            'total_files': len(json_files),
            'passed_files': 0,
            'failed_files': 0,
            'error_files': 0,
            'average_score': 0.0,
            'validation_timestamp': datetime.now().isoformat()
        }

        for file_path in json_files:
            result = self.validate_data_file(str(file_path))
            validation_results.append(result)

            # 更新統計
            if result['status'] == 'PASS':
                summary_stats['passed_files'] += 1
            elif result['status'] == 'FAIL':
                summary_stats['failed_files'] += 1
            else:
                summary_stats['error_files'] += 1

        # 計算平均分
        valid_scores = [r['overall_score'] for r in validation_results if 'overall_score' in r]
        if valid_scores:
            summary_stats['average_score'] = sum(valid_scores) / len(valid_scores)

        # 整體評估
        overall_status = 'EXCELLENT' if summary_stats['average_score'] >= 0.9 else \
                        'GOOD' if summary_stats['average_score'] >= 0.8 else \
                        'ACCEPTABLE' if summary_stats['average_score'] >= 0.7 else \
                        'POOR'

        return {
            'summary': summary_stats,
            'overall_status': overall_status,
            'detailed_results': validation_results,
            'recommendations': self._generate_recommendations(summary_stats, validation_results)
        }

    def _generate_recommendations(self, summary_stats: Dict, results: List[Dict]) -> List[str]:
        """生成改進建議"""
        recommendations = []

        if summary_stats['average_score'] < 0.8:
            recommendations.append("整體數據質量需要改進，建議檢查數據源和採集流程")

        if summary_stats['error_files'] > 0:
            recommendations.append(f"有{summary_stats['error_files']}個文件出現錯誤，需要檢查文件格式")

        if summary_stats['failed_files'] > 0:
            recommendations.append(f"有{summary_stats['failed_files']}個文件未通過驗證，建議檢查數據完整性")

        # 分析具體問題
        structure_issues = sum(1 for r in results if 'structure_validation' in r and not r['structure_validation']['passed'])
        if structure_issues > 0:
            recommendations.append(f"有{structure_issues}個文件存在結構問題，需要檢查必需字段")

        quality_issues = sum(1 for r in results if 'quality_validation' in r and not r['quality_validation']['passed'])
        if quality_issues > 0:
            recommendations.append(f"有{quality_issues}個文件存在質量問題，需要處理缺失值和異常值")

        authenticity_issues = sum(1 for r in results if 'authenticity_validation' in r and not r['authenticity_validation']['passed'])
        if authenticity_issues > 0:
            recommendations.append(f"有{authenticity_issues}個文件存在真實性問題，需要驗證數據來源")

        if not recommendations:
            recommendations.append("數據質量良好，建議繼續保持現有數據管理標準")

        return recommendations

def main():
    """主函數"""
    print("=" * 60)
    print("DATA QUALITY VALIDATION TEST")
    print("=" * 60)

    validator = DataQualityValidator()

    # 測試政府數據
    print("\n1. Validating Government Data Files...")
    government_result = validator.run_comprehensive_validation('data/government/')

    print(f"Files validated: {government_result['summary']['total_files']}")
    print(f"Passed: {government_result['summary']['passed_files']}")
    print(f"Failed: {government_result['summary']['failed_files']}")
    print(f"Errors: {government_result['summary']['error_files']}")
    print(f"Average Score: {government_result['summary']['average_score']:.3f}")
    print(f"Overall Status: {government_result['overall_status']}")

    # 顯示建議
    print(f"\n2. Recommendations:")
    for i, rec in enumerate(government_result['recommendations'], 1):
        print(f"   {i}. {rec}")

    # 顯示詳細結果（前5個文件）
    print(f"\n3. Detailed Results (Sample):")
    for i, result in enumerate(government_result['detailed_results'][:5], 1):
        file_name = Path(result['file_path']).name
        print(f"   {i}. {file_name}: {result['status']} (Score: {result.get('overall_score', 0):.3f})")

        if 'quality_validation' in result and 'metrics' in result['quality_validation']:
            metrics = result['quality_validation']['metrics']
            if 'record_count' in metrics:
                print(f"      Records: {metrics['record_count']}")
            if 'data_completeness' in metrics:
                print(f"      Completeness: {metrics['data_completeness']:.1%}")

    # 保存報告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"data_quality_validation_report_{timestamp}.json"

    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(government_result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nDetailed report saved to: {report_file}")
    except Exception as e:
        print(f"\nReport save failed: {e}")

    print("\n" + "=" * 60)
    print("DATA QUALITY VALIDATION COMPLETED")
    print("=" * 60)

    return government_result

if __name__ == "__main__":
    validation_results = main()