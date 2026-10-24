"""
Enhanced Non-Price TA System - Enhanced Data Collector
增强数据收集器 - 测试和优化所有HKMA数据源的API获取能力

核心功能:
1. 测试所有HKMA数据源的最大页面大小和数据获取能力
2. 实现数据缓存机制避免重复API调用
3. 添加API调用的错误处理和重试机制
4. 记录每个数据源的实际数据范围和质量
5. 实现分批数据获取以处理大数据集
"""

import requests
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
import os
from pathlib import Path

@dataclass
class DataSourceCapability:
    """数据源能力记录"""
    source_name: str
    api_endpoint: str
    max_records: int
    date_range: Tuple[str, str]
    data_fields: List[str]
    sample_size: int
    api_response_time: float
    success_rate: float
    data_quality_score: float

@dataclass
class DataCollectionResult:
    """数据收集结果"""
    source_name: str
    success: bool
    data: pd.DataFrame
    metadata: Dict
    collection_time: datetime
    error_message: Optional[str] = None

class EnhancedDataCollector:
    """增强数据收集器"""

    def __init__(self, cache_dir: str = "data_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # HKMA数据源配置
        self.data_sources = {
            'hibor_rates': {
                'name': 'HIBOR利率',
                'endpoint': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily',
                'expected_fields': ['end_of_date', 'tenor', 'rate'],
                'test_pages': [100, 1000, 5000, 10000]
            },
            'exchange_rates': {
                'name': '汇率数据',
                'endpoint': 'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily',
                'expected_fields': ['end_of_date', 'currency', 'rate'],
                'test_pages': [100, 1000, 5000, 10000]
            },
            'monetary_base': {
                'name': '货币基础',
                'endpoint': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base',
                'expected_fields': ['end_of_date', 'figure_type', 'amount'],
                'test_pages': [100, 1000, 5000]
            },
            'interbank_liquidity': {
                'name': '银行同业流动资金',
                'endpoint': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity',
                'expected_fields': ['end_of_date', 'figure_type', 'amount'],
                'test_pages': [100, 1000, 5000]
            },
            'efbn_indicative': {
                'name': '外汇基金票据及债券',
                'endpoint': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/efbn-indicative-price',
                'expected_fields': ['end_of_date', 'tenor', 'price'],
                'test_pages': [100, 1000, 5000, 10000]
            },
            'rmb_liquidity': {
                'name': '人民币流动资金',
                'endpoint': 'https://api.hkma.gov.hk/public/market-data-and-statistics/daily-monetary-statistics/usage-rmb-liquidity-fac',
                'expected_fields': ['end_of_date', 'figure_type', 'amount'],
                'test_pages': [100, 1000]
            }
        }

        # 缓存配置
        self.cache_duration = 300  # 5分钟缓存
        self.retry_attempts = 3
        self.request_timeout = 60

    def test_all_sources_capability(self) -> Dict[str, DataSourceCapability]:
        """测试所有数据源的能力"""
        print("🔍 开始测试所有HKMA数据源能力...")
        print("=" * 80)

        capabilities = {}

        for source_key, source_config in self.data_sources.items():
            print(f"\n📊 测试数据源: {source_config['name']}")
            print("-" * 50)

            capability = self._test_single_source_capability(source_key, source_config)
            capabilities[source_key] = capability

            # 输出测试结果摘要
            self._print_capability_summary(capability)

        print("\n" + "=" * 80)
        print("✅ 所有数据源能力测试完成!")

        # 生成综合报告
        self._generate_capability_report(capabilities)

        return capabilities

    def _test_single_source_capability(self, source_key: str,
                                     source_config: Dict) -> DataSourceCapability:
        """测试单个数据源的能力"""
        start_time = time.time()

        # 测试不同的页面大小
        max_records = 0
        optimal_pagesize = 100
        date_range = (None, None)
        data_fields = []
        success_rate = 0
        api_response_time = 0

        for pagesize in source_config['test_pages']:
            print(f"  🧪 测试页面大小: {pagesize}")

            try:
                response_time_start = time.time()
                data = self._fetch_data(source_key, pagesize=pagesize)
                response_time = time.time() - response_time_start

                if data is not None and len(data) > 0:
                    success_rate = 1.0
                    max_records = len(data)
                    optimal_pagesize = pagesize
                    api_response_time = response_time

                    # 获取数据范围
                    if 'date' in data.columns:
                        date_range = (data['date'].min(), data['date'].max())
                    elif 'end_of_date' in data.columns:
                        date_range = (data['end_of_date'].min(), data['end_of_date'].max())

                    # 记录数据字段
                    data_fields = data.columns.tolist()

                    print(f"    ✅ 成功获取 {len(data)} 条记录")
                    print(f"    ⏱️  响应时间: {response_time:.2f}秒")

                    # 如果这个页面大小已经达到上限，停止测试更大的
                    if len(data) < pagesize * 0.9:  # 如果返回数据明显少于请求量
                        print(f"    📝 检测到数据上限，停止测试更大页面")
                        break

                else:
                    print(f"    ❌ 获取失败")

            except Exception as e:
                print(f"    ❌ 错误: {str(e)}")
                success_rate = 0

            # 添加延迟避免API限制
            time.sleep(1)

        # 计算数据质量评分
        data_quality_score = self._calculate_data_quality_score(
            max_records, success_rate, len(data_fields)
        )

        total_time = time.time() - start_time

        capability = DataSourceCapability(
            source_name=source_config['name'],
            api_endpoint=source_config['endpoint'],
            max_records=max_records,
            date_range=date_range,
            data_fields=data_fields,
            sample_size=max_records,
            api_response_time=api_response_time,
            success_rate=success_rate,
            data_quality_score=data_quality_score
        )

        return capability

    def _fetch_data(self, source_key: str, pagesize: int = 100,
                   from_date: str = None) -> Optional[pd.DataFrame]:
        """从API获取数据"""
        source_config = self.data_sources[source_key]

        # 构建API参数
        params = {
            'pagesize': pagesize
        }

        if from_date:
            params['from'] = from_date

        # 尝试从缓存获取
        cache_key = f"{source_key}_{pagesize}_{from_date or 'default'}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # API请求
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(
                    source_config['endpoint'],
                    params=params,
                    timeout=self.request_timeout
                )
                response.raise_for_status()

                data = response.json()

                # 解析数据
                parsed_data = self._parse_api_response(data, source_key)

                # 缓存结果
                if parsed_data is not None:
                    self._save_to_cache(cache_key, parsed_data)

                return parsed_data

            except requests.exceptions.RequestException as e:
                print(f"    ⚠️  API请求失败 (尝试 {attempt + 1}/{self.retry_attempts}): {str(e)}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    return None

            except Exception as e:
                print(f"    ❌ 数据解析错误: {str(e)}")
                return None

        return None

    def _parse_api_response(self, data: Dict, source_key: str) -> Optional[pd.DataFrame]:
        """解析API响应数据"""
        try:
            # 根据不同的数据源解析
            if source_key == 'hibor_rates':
                return self._parse_hibor_data(data)
            elif source_key == 'exchange_rates':
                return self._parse_exchange_rate_data(data)
            elif source_key in ['monetary_base', 'interbank_liquidity', 'efbn_indicative', 'rmb_liquidity']:
                return self._parse_monetary_data(data)
            else:
                # 通用解析
                return self._parse_generic_data(data)

        except Exception as e:
            print(f"    ❌ 数据解析错误: {str(e)}")
            return None

    def _parse_hibor_data(self, data: Dict) -> pd.DataFrame:
        """解析HIBOR数据"""
        if 'datas' not in data:
            return pd.DataFrame()

        records = []
        for item in data['datas']:
            records.append({
                'date': item.get('end_of_date'),
                'tenor': item.get('tenor'),
                'rate': float(item.get('rate', 0))
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

        return df

    def _parse_exchange_rate_data(self, data: Dict) -> pd.DataFrame:
        """解析汇率数据"""
        if 'datas' not in data:
            return pd.DataFrame()

        records = []
        for item in data['datas']:
            records.append({
                'date': item.get('end_of_date'),
                'currency': item.get('currency_code'),
                'rate': float(item.get('rate', 0))
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

        return df

    def _parse_monetary_data(self, data: Dict) -> pd.DataFrame:
        """解析货币数据"""
        if 'datas' not in data:
            return pd.DataFrame()

        records = []
        for item in data['datas']:
            records.append({
                'date': item.get('end_of_date'),
                'figure_type': item.get('figure_type_code'),
                'amount': float(item.get('amount', 0))
            })

        df = pd.DataFrame(records)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

        return df

    def _parse_generic_data(self, data: Dict) -> pd.DataFrame:
        """通用数据解析"""
        if 'datas' not in data:
            return pd.DataFrame()

        df = pd.DataFrame(data['datas'])
        if not df.empty:
            # 尝试找到日期字段
            date_cols = [col for col in df.columns if 'date' in col.lower()]
            if date_cols:
                df['date'] = pd.to_datetime(df[date_cols[0]])
                df = df.sort_values('date')

        return df

    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """从缓存获取数据"""
        cache_file = self.cache_dir / f"{cache_key}.parquet"

        if cache_file.exists():
            try:
                file_age = time.time() - cache_file.stat().st_mtime
                if file_age < self.cache_duration:
                    df = pd.read_parquet(cache_file)
                    print(f"    💾 从缓存加载 ({len(df)} 记录)")
                    return df
            except Exception as e:
                print(f"    ⚠️  缓存读取失败: {str(e)}")

        return None

    def _save_to_cache(self, cache_key: str, data: pd.DataFrame):
        """保存数据到缓存"""
        cache_file = self.cache_dir / f"{cache_key}.parquet"

        try:
            data.to_parquet(cache_file, index=False)
        except Exception as e:
            print(f"    ⚠️  缓存保存失败: {str(e)}")

    def _calculate_data_quality_score(self, max_records: int, success_rate: float,
                                    field_count: int) -> float:
        """计算数据质量评分"""
        # 基于记录数量的评分 (0-0.4)
        records_score = min(0.4, max_records / 10000 * 0.4)

        # 基于成功率的评分 (0-0.3)
        success_score = success_rate * 0.3

        # 基于字段数量的评分 (0-0.3)
        field_score = min(0.3, field_count / 10 * 0.3)

        return records_score + success_score + field_score

    def _print_capability_summary(self, capability: DataSourceCapability):
        """打印数据源能力摘要"""
        print(f"  📋 {capability.source_name} 能力摘要:")
        print(f"    最大记录数: {capability.max_records:,}")
        print(f"    API响应时间: {capability.api_response_time:.2f}秒")
        print(f"    成功率: {capability.success_rate:.1%}")
        print(f"    数据质量评分: {capability.data_quality_score:.3f}/1.0")

        if capability.date_range != (None, None):
            start_date, end_date = capability.date_range
            if start_date and end_date:
                days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
                years = days / 365.25
                print(f"    数据时间范围: {start_date} 至 {end_date} ({years:.1f}年)")

        print(f"    数据字段: {len(capability.data_fields)}个")
        print(f"    主要字段: {capability.data_fields[:3]}...")

    def _generate_capability_report(self, capabilities: Dict[str, DataSourceCapability]):
        """生成数据源能力报告"""
        print("\n📄 生成数据源能力报告...")

        # 创建报告数据
        report_data = {
            'test_timestamp': datetime.now().isoformat(),
            'total_sources_tested': len(capabilities),
            'sources': {}
        }

        summary_stats = {
            'total_records': 0,
            'average_response_time': 0,
            'average_quality_score': 0,
            'successful_sources': 0
        }

        for source_key, capability in capabilities.items():
            source_data = {
                'name': capability.source_name,
                'endpoint': capability.api_endpoint,
                'max_records': capability.max_records,
                'date_range': capability.date_range,
                'data_fields': capability.data_fields,
                'api_response_time': capability.api_response_time,
                'success_rate': capability.success_rate,
                'data_quality_score': capability.data_quality_score
            }

            report_data['sources'][source_key] = source_data

            # 更新统计
            summary_stats['total_records'] += capability.max_records
            summary_stats['average_response_time'] += capability.api_response_time
            summary_stats['average_quality_score'] += capability.data_quality_score
            if capability.success_rate > 0:
                summary_stats['successful_sources'] += 1

        # 计算平均值
        if len(capabilities) > 0:
            summary_stats['average_response_time'] /= len(capabilities)
            summary_stats['average_quality_score'] /= len(capabilities)

        report_data['summary_statistics'] = summary_stats

        # 保存报告
        report_file = f"data_capability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"  📊 报告已保存至: {report_file}")

        # 打印汇总统计
        print(f"\n📈 汇总统计:")
        print(f"  测试数据源: {summary_stats['total_sources_tested']} 个")
        print(f"  成功数据源: {summary_stats['successful_sources']} 个")
        print(f"  总记录数: {summary_stats['total_records']:,} 条")
        print(f"  平均响应时间: {summary_stats['average_response_time']:.2f} 秒")
        print(f"  平均质量评分: {summary_stats['average_quality_score']:.3f}/1.0")

    def collect_all_historical_data(self, capabilities: Dict[str, DataSourceCapability]) -> Dict[str, DataCollectionResult]:
        """收集所有数据源的完整历史数据"""
        print("\n🚀 开始收集所有数据源的完整历史数据...")
        print("=" * 80)

        results = {}

        for source_key, capability in capabilities.items():
            print(f"\n📊 收集数据: {capability.source_name}")

            if capability.success_rate == 0:
                print(f"  ❌ 跳过不可用的数据源")
                continue

            try:
                # 使用最优页面大小获取数据
                optimal_pagesize = min(capability.max_records, 10000)
                data = self._fetch_data(source_key, pagesize=optimal_pagesize)

                if data is not None and len(data) > 0:
                    # 保存到文件
                    output_file = f"historical_data_{source_key}_{datetime.now().strftime('%Y%m%d')}.parquet"
                    data.to_parquet(output_file, index=False)

                    result = DataCollectionResult(
                        source_name=capability.source_name,
                        success=True,
                        data=data,
                        metadata={
                            'source_key': source_key,
                            'records_count': len(data),
                            'date_range': (data['date'].min(), data['date'].max()) if 'date' in data.columns else (None, None),
                            'data_fields': data.columns.tolist(),
                            'output_file': output_file
                        },
                        collection_time=datetime.now()
                    )

                    results[source_key] = result
                    print(f"  ✅ 成功收集 {len(data)} 条记录")
                    print(f"  💾 保存至: {output_file}")

                else:
                    print(f"  ❌ 数据收集失败")
                    result = DataCollectionResult(
                        source_name=capability.source_name,
                        success=False,
                        data=pd.DataFrame(),
                        metadata={},
                        collection_time=datetime.now(),
                        error_message="API返回空数据"
                    )
                    results[source_key] = result

            except Exception as e:
                print(f"  ❌ 收集过程中出错: {str(e)}")
                result = DataCollectionResult(
                    source_name=capability.source_name,
                    success=False,
                    data=pd.DataFrame(),
                    metadata={},
                    collection_time=datetime.now(),
                    error_message=str(e)
                )
                results[source_key] = result

            # 添加延迟避免API限制
            time.sleep(2)

        print(f"\n✅ 数据收集完成! 成功收集 {sum(1 for r in results.values() if r.success)}/{len(capabilities)} 个数据源")

        return results

# 主函数和演示
def main():
    """主函数 - 执行完整的数据源测试和收集流程"""
    print("🎯 增强数据收集器 - HKMA数据源测试与收集")
    print("=" * 80)

    # 创建收集器
    collector = EnhancedDataCollector()

    # 步骤1: 测试所有数据源能力
    capabilities = collector.test_all_sources_capability()

    # 步骤2: 收集完整历史数据
    results = collector.collect_all_historical_data(capabilities)

    # 步骤3: 生成最终报告
    print("\n" + "=" * 80)
    print("📋 最终报告")
    print("=" * 80)

    successful_sources = [r for r in results.values() if r.success]
    failed_sources = [r for r in results.values() if not r.success]

    print(f"✅ 成功收集的数据源 ({len(successful_sources)}个):")
    for result in successful_sources:
        metadata = result.metadata
        print(f"  📊 {result.source_name}: {metadata['records_count']:,} 条记录")
        if metadata['date_range'] != (None, None):
            start, end = metadata['date_range']
            if start and end:
                days = (pd.to_datetime(end) - pd.to_datetime(start)).days
                years = days / 365.25
                print(f"      时间范围: {start} 至 {end} ({years:.1f}年)")

    if failed_sources:
        print(f"\n❌ 收集失败的数据源 ({len(failed_sources)}个):")
        for result in failed_sources:
            print(f"  ❌ {result.source_name}: {result.error_message}")

    total_records = sum(len(r.data) for r in successful_sources)
    print(f"\n📈 总计收集: {total_records:,} 条历史数据")

    print("\n🎉 数据收集任务完成!")
    return capabilities, results

if __name__ == "__main__":
    # 运行完整流程
    capabilities, results = main()