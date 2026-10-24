#!/usr/bin/env python3
"""
API Historical Limits Verification
验证各API的历史数据限制，确认5年以上数据的可用性
"""

import sys
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hkma_data_adapter import HKMADataAdapter
from vectorbt_engine import PersonalVectorBTEngine

class APIHistoricalLimitsVerifier:
    """API历史限制验证器"""

    def __init__(self):
        self.hkma_adapter = HKMADataAdapter()
        self.engine = PersonalVectorBTEngine()
        self.results = {}

    def verify_hkma_historical_limits(self):
        """验证HKMA API历史数据限制"""
        print("🔍 验证HKMA API历史数据限制...")

        hibor_results = {}
        test_years = [5, 7, 10]

        for years in test_years:
            print(f"  测试 {years} 年HIBOR数据...")
            start_date = datetime.now() - timedelta(days=years*365)
            end_date = datetime.now() - timedelta(days=1)

            try:
                start_time = time.time()
                hibor_data = self.hkma_adapter.get_hibor_data(start_date, end_date)
                end_time = time.time()

                data_points = len(hibor_data)
                date_range = (hibor_data.index.max() - hibor_data.index.min()).days
                completeness = self._calculate_data_completeness(hibor_data, start_date, end_date)

                hibor_results[years] = {
                    'data_points': data_points,
                    'date_range_days': date_range,
                    'completeness': completeness,
                    'fetch_time_seconds': end_time - start_time,
                    'success': data_points > 0,
                    'tenors_available': hibor_data['tenor'].nunique() if 'tenor' in hibor_data.columns else 0
                }

                print(f"    ✅ {years} 年: {data_points} 条记录, 覆盖 {date_range}天, 完整性: {completeness:.1%}")

            except Exception as e:
                hibor_results[years] = {
                    'success': False,
                    'error': str(e),
                    'data_points': 0,
                    'completeness': 0
                }
                print(f"    ❌ {years} 年: 失败 - {e}")

        self.results['hkma_hibor'] = hibor_results
        return hibor_results

    def verify_central_api_limits(self):
        """验证中央API历史数据限制"""
        print("\n🔍 验证中央API历史数据限制...")

        api_results = {}
        test_symbols = ['0700.hk', '0941.hk', '1398.hk']  # 腾讯、中移动、工行
        test_years = [5, 7, 10]

        for symbol in test_symbols:
            symbol_results = {}

            for years in test_years:
                print(f"  测试 {symbol} {years} 年数据...")

                try:
                    start_date = datetime.now() - timedelta(days=years*365)
                    end_date = datetime.now() - timedelta(days=1)

                    # 测试中央API
                    url = "http://18.180.162.113:9191/inst/getInst"
                    params = {
                        "symbol": symbol.lower(),
                        "duration": int(years * 365)
                    }

                    start_time = time.time()
                    response = requests.get(url, params=params, timeout=30)
                    end_time = time.time()

                    if response.status_code == 200:
                        data = response.json()

                        if isinstance(data, dict) and 'data' in data:
                            data_points = len(data['data'])
                        else:
                            # 可能是单个数据点
                            data_points = 1 if data else 0

                        symbol_results[years] = {
                            'data_points': data_points,
                            'fetch_time_seconds': end_time - start_time,
                            'success': True,
                            'response_structure': type(data).__name__
                        }

                            print(f"    ✅ {symbol} {years} 年: {data_points} 条记录")
                        else:
                            symbol_results[years] = {
                                'success': False,
                                'status_code': response.status_code,
                                'data_points': 0
                            }
                            print(f"    ❌ {symbol} {years} 年: HTTP {response.status_code}")
                    else:
                        symbol_results[years] = {
                            'success': False,
                            'status_code': response.status_code,
                            'data_points': 0
                        }
                        print(f"    ❌ {symbol} {years} 年: HTTP {response.status_code}")

                except Exception as e:
                    symbol_results[years] = {
                        'success': False,
                        'error': str(e),
                        'data_points': 0
                    }
                    print(f"    ❌ {symbol} {years} 年: 失败 - {e}")

            api_results[symbol] = symbol_results

        self.results['central_api'] = api_results
        return api_results

    def verify_alternative_data_sources(self):
        """验证备用数据源"""
        print("\n🔍 验证备用数据源...")

        alternative_sources = {}

        # Yahoo Finance测试
        try:
            print("  测试Yahoo Finance历史数据...")
            symbol = '0700.HK'
            start_date = datetime.now() - timedelta(days=5*365)

            # 使用yfinance库测试Yahoo Finance
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date)

                alternative_sources['yahoo_finance'] = {
                    'success': True,
                    'data_points': len(hist),
                    'date_range_days': (hist.index.max() - hist.index.min()).days,
                    'start_date': hist.index.min().date(),
                    'end_date': hist.index.max().date()
                }
                print(f"    ✅ Yahoo Finance: {len(hist)} 条记录")

            except ImportError:
                alternative_sources['yahoo_finance'] = {
                    'success': False,
                    'error': 'yfinance library not available'
                }
                print(f"    ❌ Yahoo Finance: yfinance库未安装")
            except Exception as e:
                alternative_sources['yahoo_finance'] = {
                    'success': False,
                    'error': str(e)
                }
                print(f"    ❌ Yahoo Finance: {e}")

        except Exception as e:
            alternative_sources['yahoo_finance'] = {
                'success': False,
                'error': f"Test failed: {e}"
            }

        # 本地缓存数据测试
        cache_dir = Path("C:/Users/Penguin8n/CODEX--/data/cache")
        if cache_dir.exists():
            hsi_file = cache_dir / "hsi_constituents_82.json"
            if hsi_file.exists():
                alternative_sources['local_cache'] = {
                    'success': True,
                    'file_path': str(hsi_file),
                    'file_size': hsi_file.stat().st_size
                }
                print(f"    ✅ 本地缓存: 找到恒指成分股数据")
            else:
                alternative_sources['local_cache'] = {
                    'success': False,
                    'reason': 'No cached data files found'
                }
                print(f"    ❌ 本地缓存: 未找到缓存文件")

        self.results['alternative_sources'] = alternative_sources
        return alternative_sources

    def analyze_data_quality(self, data: pd.DataFrame, data_type: str) -> dict:
        """分析数据质量"""
        if len(data) == 0:
            return {'quality_score': 0, 'issues': ['No data']}

        quality_analysis = {
            'total_records': len(data),
            'date_range_days': (data.index.max() - data.index.min()).days,
            'missing_data_percentage': data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100,
            'duplicates': data.index.duplicated().sum(),
            'outliers': self._detect_outliers(data),
            'data_consistency': self._check_data_consistency(data)
        }

        # 计算质量评分
        quality_score = 100
        if quality_analysis['missing_data_percentage'] > 5:
            quality_score -= 20
        if quality_analysis['duplicates'] > 0:
            quality_score -= 10
        if quality_analysis['outliers']['count'] > quality_analysis['total_records'] * 0.05:
            quality_score -= 15

        quality_analysis['quality_score'] = max(0, quality_score)
        return quality_analysis

    def _calculate_data_completeness(self, data: pd.DataFrame, start_date: datetime, end_date: datetime) -> float:
        """计算数据完整性"""
        expected_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        expected_weekdays = expected_dates[expected_dates.weekday < 5]  # 只计算工作日

        actual_dates = data.index.normalize() if hasattr(data.index, 'normalize') else data.index
        actual_weekdays = actual_dates[actual_dates.weekday < 5]

        if len(expected_weekdays) == 0:
            return 1.0

        return len(actual_weekdays) / len(expected_weekdays)

    def _detect_outliers(self, data: pd.DataFrame) -> dict:
        """检测异常值"""
        outliers = {}

        for column in data.select_dtypes(include=[np.number]).columns:
            Q1 = data[column].quantile(0.25)
            Q3 = data[column].quantile(0.75)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            outliers_column = ((data[column] < lower_bound) | (data[column] > upper_bound)).sum()
            outliers[column] = {
                'count': outliers_column,
                'percentage': outliers_column / len(data) * 100
            }

        return {
            'total_outliers': sum(outliers[col]['count'] for col in outliers),
            'outlier_details': outliers
        }

    def _check_data_consistency(self, data: pd.DataFrame) -> dict:
        """检查数据一致性"""
        consistency_checks = {}

        # 检查价格逻辑
        if all(col in data.columns for col in ['open', 'high', 'low', 'close']):
            # OHLC关系检查
            invalid_ohlc = (
                (data['high'] < data['open']).any() or
                (data['high'] < data['close']).any() or
                (data['high'] < data['low']).any() or
                (data['low'] > data['open']).any() or
                (data['low'] > data['close']).any()
            )
            consistency_checks['ohlc_logic'] = {
                'valid': not invalid_ohlc,
                'invalid_count': invalid_ohlc.sum() if invalid_ohlc.any() else 0
            }

        return consistency_checks

    def generate_verification_report(self):
        """生成验证报告"""
        print("\n📊 API历史限制验证报告")
        print("=" * 50)

        # HKMA结果总结
        if 'hkma_hibor' in self.results:
            print("\n🏛️ HKMA HIBOR数据:")
            hibor_results = self.results['hkma_hibor']

            successful_years = [year for year, result in hibor_results.items() if result['success']]
            print(f"  可用年份: {sorted(successful_years)}")
            print(f"  数据质量: '优秀' if len(successful_years) >= 3 else '需要改进'")

            for year, result in hibor_results.items():
                if result['success']:
                    print(f"    {year}年: {result['data_points']} 条记录, {result['completeness']:.1%} 完整性")

        # 中央API结果总结
        if 'central_api' in self.results:
            print("\n💻 中央股票API数据:")
            api_results = self.results['central_api']

            for symbol, symbol_results in api_results.items():
                successful_years = [year for year, result in symbol_results.items() if result['success']]
                total_points = sum(result.get('data_points', 0) for result in symbol_results.values() if result.get('success', False))

                print(f"  {symbol}: {len(successful_years)} 年可用, {total_points} 条总记录")

        # 备用数据源结果
        if 'alternative_sources' in self.results:
            print("\n🔄 备用数据源:")
            alt_results = self.results['alternative_sources']

            for source, result in alt_results.items():
                status = "✅ 可用" if result.get('success', False) else "❌ 不可用"
                print(f"  {source}: {status}")

        # 建议
        print("\n💡 建议:")

        # HKMA数据建议
        if 'hkma_hibor' in self.results:
            hibor_success = [r['success'] for r in self.results['hkma_hibor'].values()]
            if sum(hibor_success) >= 3:
                print("  ✅ HKMA数据质量良好，可支持5+年分析")
            else:
                print("  ⚠️ HKMA数据有限，建议补充其他数据源")

        # 中央API建议
        if 'central_api' in self.results:
            api_success = sum(sum(r['success'] for r in s.values()) for s in self.results['central_api'].values())
            if api_success >= 3 * len(self.results['central_api']):
                print("  ✅ 中央API支持度良好")
            else:
                print("  ⚠️ 中央API历史数据有限，建议整合Yahoo Finance")

        # 整体建议
        print("\n🎯 5+年回测可行性:")

        has_hkma = any(r.get('success', False) for r in self.results.get('hkma_hibor', {}).values())
        has_central = any(any(r.get('success', False) for r in s.values()) for s in self.results.get('central_api', {}).values())
        has_alternatives = any(r.get('success', False) for r in self.results.get('alternative_sources', {}).values())

        if has_hkma and (has_central or has_alternatives):
            print("  🟢 **可行**: 系统具备5+年回测的数据基础")
            print("     - HKMA政府数据支持多年历史分析")
            print("     - 股票数据可通过多源获取")
            print("     - 建议实施多数据源整合策略")
        else:
            print("  🟡 **受限**: 需要增强数据获取能力")
            print("     - 建议优先集成Yahoo Finance等备用数据源")
            print("     - 考虑实施数据缓存和历史归档机制")

        print("\n📈 下一步行动:")
        print("  1. 设计多数据源整合架构")
        print("  2. 实施数据质量监控系统")
        print("  3. 优化存储和缓存策略")
        print(" 4. 开始长期技术分析框架开发")

def main():
    """主函数"""
    verifier = APIHistoricalLimitsVerifier()

    print("🔍 开始API历史限制验证...")
    print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 验证HKMA数据
    verifier.verify_hkma_historical_limits()

    # 验证中央API数据
    verifier.verify_central_api_limits()

    # 验证备用数据源
    verifier.verify_alternative_data_sources()

    # 生成报告
    verifier.generate_verification_report()

    # 保存详细结果
    output_file = "api_limits_verification_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(verifier.results, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n💾 详细结果已保存到: {output_file}")
    print("🎯 验证完成!")

if __name__ == "__main__":
    main()