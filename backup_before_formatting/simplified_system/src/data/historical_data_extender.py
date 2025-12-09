#!/usr/bin/env python3
"""
歷史數據擴展系統
Historical Data Extension System

基於現有數據生成擴展歷史數據集，支持1000+記錄
Generate extended historical datasets based on existing data, supporting 1000+ records
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoricalDataExtender:
    """歷史數據擴展器"""

    def __init__(self):
        self.data_cache = {}
        self.extension_methods = {
            'trend_preservation': self._extend_with_trend_preservation,
            'seasonal_adjustment': self._extend_with_seasonal_adjustment,
            'statistical_simulation': self._extend_with_statistical_simulation,
            'hybrid_approach': self._extend_with_hybrid_approach
        }

    def extend_historical_data(
        self,
        original_data: List[Dict[str, Any]],
        target_records: int = 1000,
        method: str = 'hybrid_approach'
    ) -> Dict[str, Any]:
        """
        擴展歷史數據到目標記錄數

        Args:
            original_data: 原始數據列表
            target_records: 目標記錄數
            method: 擴展方法

        Returns:
            擴展後的數據
        """
        if not original_data:
            return {'success': False, 'error': 'No original data provided'}

        if len(original_data) >= target_records:
            logger.info(f"Original data already has {len(original_data)} records, no extension needed")
            return {
                'success': True,
                'data': original_data[:target_records],
                'method': 'none',
                'original_count': len(original_data),
                'extended_count': 0,
                'final_count': len(original_data[:target_records])
            }

        try:
            logger.info(f"Extending {len(original_data)} records to {target_records} using {method} method")

            if method not in self.extension_methods:
                return {'success': False, 'error': f'Unknown extension method: {method}'}

            # 使用指定的擴展方法
            extended_data = self.extension_methods[method](original_data, target_records)

            result = {
                'success': True,
                'data': extended_data,
                'method': method,
                'original_count': len(original_data),
                'extended_count': len(extended_data) - len(original_data),
                'final_count': len(extended_data),
                'extension_ratio': len(extended_data) / len(original_data),
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'metadata': self._generate_metadata(extended_data, original_data, method)
            }

            logger.info(f"Successfully extended data: {result['original_count']} -> {result['final_count']} records")
            return result

        except Exception as e:
            logger.error(f"Error extending historical data: {e}")
            return {'success': False, 'error': str(e)}

    def _extend_with_trend_preservation(self, data: List[Dict[str, Any]], target: int) -> List[Dict[str, Any]]:
        """基於趨勢保持擴展數據"""
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')

        # 識別數值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_columns:
            # 如果沒有數值列，簡單重複數據
            return self._simple_repeat(data, target)

        extended_data = data.copy()

        for i in range(len(data), target):
            # 使用指數加權移動平均生成新數據
            base_idx = i % len(data)
            next_idx = (base_idx + 1) % len(data)

            new_record = data[base_idx].copy()

            # 計算新日期
            if len(extended_data) > 0:
                last_date = pd.to_datetime(extended_data[-1]['date'])
                new_date = last_date + timedelta(days=1)
                new_record['date'] = new_date.strftime('%Y-%m-%d')

            # 生成新的數值（基於趨勢）
            for col in numeric_columns:
                if col in new_record and new_record[col] is not None:
                    # 添加趨勢變化
                    trend_factor = 1 + np.random.normal(0, 0.01)  # 1%標準差的隨機變化
                    seasonal_factor = 1 + 0.05 * np.sin(2 * np.pi * i / 365)  # 年度季節性

                    if col in df.iloc[base_idx] and col in df.iloc[next_idx]:
                        # 基於相鄰值的趨勢
                        base_value = df.iloc[base_idx][col]
                        next_value = df.iloc[next_idx][col]
                        trend = (next_value - base_value) / base_value if base_value != 0 else 0

                        new_value = new_record[col] * (1 + trend * 0.3) * trend_factor * seasonal_factor
                        new_record[col] = max(0, new_value)  # 確保非負值

            extended_data.append(new_record)

        return extended_data

    def _extend_with_seasonal_adjustment(self, data: List[Dict[str, Any]], target: int) -> List[Dict[str, Any]]:
        """基於季節性調整擴展數據"""
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')

        # 識別數值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_columns:
            return self._simple_repeat(data, target)

        # 計算季節性模式
        seasonal_patterns = {}
        for col in numeric_columns:
            if len(df) > 30:  # 至少30天來計算季節性
                df['day_of_year'] = df['date'].dt.dayofyear
                seasonal_pattern = df.groupby('day_of_year')[col].mean().to_dict()
                seasonal_patterns[col] = seasonal_pattern

        extended_data = data.copy()

        for i in range(len(data), target):
            base_idx = i % len(data)
            new_record = data[base_idx].copy()

            # 計算新日期
            if len(extended_data) > 0:
                last_date = pd.to_datetime(extended_data[-1]['date'])
                new_date = last_date + timedelta(days=1)
                new_record['date'] = new_date.strftime('%Y-%m-%d')
                day_of_year = new_date.timetuple().tm_yday
            else:
                day_of_year = 1

            # 基於季節性模式調整數值
            for col in numeric_columns:
                if col in new_record and new_record[col] is not None and col in seasonal_patterns:
                    seasonal_avg = seasonal_patterns[col].get(day_of_year, new_record[col])
                    overall_avg = df[col].mean()

                    if overall_avg != 0:
                        seasonal_factor = seasonal_avg / overall_avg
                        random_variation = np.random.normal(1.0, 0.02)  # 2%隨機變化
                        new_record[col] = new_record[col] * seasonal_factor * random_variation
                        new_record[col] = max(0, new_record[col])

            extended_data.append(new_record)

        return extended_data

    def _extend_with_statistical_simulation(self, data: List[Dict[str, Any]], target: int) -> List[Dict[str, Any]]:
        """基於統計模擬擴展數據"""
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')

        # 識別數值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_columns:
            return self._simple_repeat(data, target)

        # 計算統計參數
        stats_params = {}
        for col in numeric_columns:
            if df[col].notna().sum() > 5:
                series = df[col].dropna()
                stats_params[col] = {
                    'mean': series.mean(),
                    'std': series.std(),
                    'min': series.min(),
                    'max': series.max(),
                    'autocorr': series.autocorr(lag=1) if len(series) > 1 else 0
                }

        extended_data = data.copy()
        last_values = {col: df[col].iloc[-1] if df[col].notna().any() else 0 for col in numeric_columns}

        for i in range(len(data), target):
            base_idx = i % len(data)
            new_record = data[base_idx].copy()

            # 計算新日期
            if len(extended_data) > 0:
                last_date = pd.to_datetime(extended_data[-1]['date'])
                new_date = last_date + timedelta(days=1)
                new_record['date'] = new_date.strftime('%Y-%m-%d')

            # 基於統計參數生成新數值
            for col in numeric_columns:
                if col in stats_params:
                    params = stats_params[col]

                    # 使用AR(1)模型生成新值
                    if col in last_values:
                        mean_reversion = 0.1
                        innovation = np.random.normal(0, params['std'] * 0.3)
                        new_value = (params['mean'] * mean_reversion +
                                    last_values[col] * (1 - mean_reversion) * params['autocorr'] +
                                    innovation)

                        # 限制在合理範圍內
                        new_value = max(params['min'], min(params['max'], new_value))
                        new_record[col] = new_value
                        last_values[col] = new_value

            extended_data.append(new_record)

        return extended_data

    def _extend_with_hybrid_approach(self, data: List[Dict[str, Any]], target: int) -> List[Dict[str, Any]]:
        """混合方法擴展數據"""
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')

        # 識別數值列
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

        if not numeric_columns:
            return self._simple_repeat(data, target)

        extended_data = data.copy()

        # 基於數據長度選擇策略
        if len(data) < 30:
            # 數據太少，使用統計模擬
            return self._extend_with_statistical_simulation(data, target)
        elif len(data) < 100:
            # 中等數據，使用趨勢保持
            return self._extend_with_trend_preservation(data, target)
        else:
            # 足夠數據，混合方法
            # 前50%使用趨勢保持，後50%使用季節性調整

            trend_target = min(target // 2, len(data) * 3)
            trend_extended = self._extend_with_trend_preservation(data, trend_target)

            if len(trend_extended) < target:
                remaining = target - len(trend_extended)
                seasonal_extended = self._extend_with_seasonal_adjustment(trend_extended, target)
                return seasonal_extended
            else:
                return trend_extended

    def _simple_repeat(self, data: List[Dict[str, Any]], target: int) -> List[Dict[str, Any]]:
        """簡單重複數據（用於無數值列的情況）"""
        extended_data = []
        i = 0

        while len(extended_data) < target:
            for record in data:
                if len(extended_data) >= target:
                    break

                new_record = record.copy()

                # 更新日期
                if len(extended_data) > 0:
                    last_date = pd.to_datetime(extended_data[-1]['date'])
                    new_date = last_date + timedelta(days=1)
                    new_record['date'] = new_date.strftime('%Y-%m-%d')

                extended_data.append(new_record)
                i += 1

        return extended_data[:target]

    def _generate_metadata(
        self,
        extended_data: List[Dict[str, Any]],
        original_data: List[Dict[str, Any]],
        method: str
    ) -> Dict[str, Any]:
        """生成擴展元數據"""
        df_extended = pd.DataFrame(extended_data)
        df_original = pd.DataFrame(original_data)

        numeric_columns = df_extended.select_dtypes(include=[np.number]).columns.tolist()

        quality_metrics = {}
        for col in numeric_columns:
            if col in df_original.columns:
                orig_mean = df_original[col].mean()
                orig_std = df_original[col].std()
                ext_mean = df_extended[col].mean()
                ext_std = df_extended[col].std()

                quality_metrics[col] = {
                    'mean_preservation': abs(ext_mean - orig_mean) / orig_mean if orig_mean != 0 else 0,
                    'std_preservation': abs(ext_std - orig_std) / orig_std if orig_std != 0 else 0,
                    'data_continuity': self._calculate_continuity(df_extended[col])
                }

        return {
            'method_used': method,
            'quality_metrics': quality_metrics,
            'data_types_detected': {
                'numeric_columns': len(numeric_columns),
                'total_columns': len(df_extended.columns)
            },
            'time_span': {
                'start_date': df_extended['date'].min() if 'date' in df_extended.columns else None,
                'end_date': df_extended['date'].max() if 'date' in df_extended.columns else None,
                'days_covered': len(df_extended)
            }
        }

    def _calculate_continuity(self, series: pd.Series) -> float:
        """計算數據連續性得分"""
        if len(series) < 2:
            return 1.0

        # 計算相鄰值變化的標準差
        changes = series.diff().dropna()
        if len(changes) == 0:
            return 1.0

        # 連續性得分：變化越小，連續性越好
        continuity_score = 1.0 / (1.0 + changes.std())
        return continuity_score

    def batch_extend_multiple_sources(
        self,
        data_sources: Dict[str, List[Dict[str, Any]]],
        target_records: int = 1000,
        method: str = 'hybrid_approach'
    ) -> Dict[str, Any]:
        """批量擴展多個數據源"""
        logger.info(f"Starting batch extension of {len(data_sources)} sources to {target_records} records each")

        results = {
            'success': True,
            'session_info': {
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'target_records': target_records,
                'method': method,
                'total_sources': len(data_sources)
            },
            'extended_data': {},
            'summary': {}
        }

        successful_extensions = 0
        total_original_records = 0
        total_extended_records = 0

        for source_name, source_data in data_sources.items():
            try:
                logger.info(f"Extending {source_name}...")

                extension_result = self.extend_historical_data(
                    source_data, target_records, method
                )

                if extension_result.get('success'):
                    results['extended_data'][source_name] = extension_result
                    successful_extensions += 1
                    total_original_records += extension_result['original_count']
                    total_extended_records += extension_result['extended_count']
                    logger.info(f"[OK] {source_name}: {extension_result['original_count']} -> {extension_result['final_count']} records")
                else:
                    logger.error(f"[FAIL] {source_name}: {extension_result.get('error', 'Unknown error')}")
                    results['extended_data'][source_name] = extension_result

            except Exception as e:
                logger.error(f"[ERROR] {source_name}: Exception - {e}")
                results['extended_data'][source_name] = {
                    'success': False,
                    'error': str(e)
                }

        # 更新總結
        results['session_info']['end_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        results['summary'] = {
            'successful_sources': successful_extensions,
            'failed_sources': len(data_sources) - successful_extensions,
            'total_original_records': total_original_records,
            'total_extended_records': total_extended_records,
            'total_final_records': total_original_records + total_extended_records,
            'success_rate': f"{(successful_extensions/len(data_sources)*100):.1f}%",
            'average_extension_ratio': (total_original_records + total_extended_records) / total_original_records if total_original_records > 0 else 1
        }

        logger.info(f"Batch extension complete: {successful_extensions}/{len(data_sources)} sources successful")
        logger.info(f"Total records: {total_original_records} -> {results['summary']['total_final_records']}")

        return results

# 全局實例
historical_extender = HistoricalDataExtender()

# 便捷函數
def extend_data_records(data: List[Dict[str, Any]], target: int = 1000, method: str = 'hybrid_approach') -> Dict[str, Any]:
    """擴展數據記錄"""
    return historical_extender.extend_historical_data(data, target, method)

def batch_extend_sources(data_sources: Dict[str, List[Dict[str, Any]]], target: int = 1000) -> Dict[str, Any]:
    """批量擴展多個數據源"""
    return historical_extender.batch_extend_multiple_sources(data_sources, target)

if __name__ == "__main__":
    print("=" * 80)
    print("Historical Data Extension System")
    print("歷史數據擴展系統")
    print("=" * 80)
    print("Testing historical data extension...")
    print()

    # 創建測試數據
    test_data = [
        {'date': '2025-01-01', 'value1': 100.0, 'value2': 50.0},
        {'date': '2025-01-02', 'value1': 102.0, 'value2': 51.0},
        {'date': '2025-01-03', 'value1': 101.0, 'value2': 52.0},
        {'date': '2025-01-04', 'value1': 103.0, 'value2': 51.5},
        {'date': '2025-01-05', 'value1': 104.0, 'value2': 53.0}
    ]

    print(f"Original data: {len(test_data)} records")
    print(f"Target records: 1000")
    print()

    # 測試不同的擴展方法
    methods = ['trend_preservation', 'seasonal_adjustment', 'statistical_simulation', 'hybrid_approach']

    for method in methods:
        print(f"=== Testing {method} method ===")
        result = extend_data_records(test_data, 1000, method)

        if result.get('success'):
            print(f"[OK] {method}: {result['original_count']} -> {result['final_count']} records")
            print(f"  Extension ratio: {result['extension_ratio']:.2f}x")
            print(f"  Quality score: {len(result.get('metadata', {}).get('quality_metrics', {}))}")
        else:
            print(f"[FAIL] {method}: {result.get('error', 'Unknown error')}")
        print()

    print("=== Batch Extension Test ===")
    # 測試批量擴展
    test_sources = {
        'source1': test_data,
        'source2': [
            {'date': '2025-01-01', 'price': 1000.0, 'volume': 1000000},
            {'date': '2025-01-02', 'price': 1010.0, 'volume': 1100000}
        ]
    }

    batch_result = batch_extend_sources(test_sources, 500)
    if batch_result.get('success'):
        summary = batch_result['summary']
        print(f"Batch extension: {summary['successful_sources']}/{summary['total_sources']} successful")
        print(f"Total records: {summary['total_original_records']} -> {summary['total_final_records']}")
        print(f"Success rate: {summary['success_rate']}")
    else:
        print("Batch extension failed")

    print("\n=== USAGE EXAMPLES ===")
    print("from historical_data_extender import extend_data_records, batch_extend_sources")
    print()
    print("# Extend single data source")
    print("extended_data = extend_data_records(original_data, 1000, 'hybrid_approach')")
    print("print(f'Extended from {extended_data[\"original_count\"]} to {extended_data[\"final_count\"]} records')")
    print()
    print("# Batch extend multiple sources")
    print("batch_result = batch_extend_sources({'source1': data1, 'source2': data2}, 1000)")
    print("print(f'Success rate: {batch_result[\"summary\"][\"success_rate\"]}')")