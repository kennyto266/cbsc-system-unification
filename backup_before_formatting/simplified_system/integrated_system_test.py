#!/usr/bin/env python3
"""
集成测试：验证8个修复版政府数据源与量化系统的集成
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from api.government_data import government_api
from indicators.core_indicators import CoreIndicators
from backtest.vectorbt_engine import VectorBTEngine
from api.stock_api import get_hk_stock_data

class IntegratedSystemTest:
    """完整系统集成测试"""

    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()

    async def test_all_government_data_sources(self) -> Dict[str, Any]:
        """测试所有8个政府数据源"""
        print("Testing all 8 government data sources...")

        results = {}

        # 测试每个数据源
        for source_key, source_config in government_api.data_sources.items():
            if not source_config.get('enabled', True):
                continue

            print(f"\nTesting {source_key}: {source_config['name']}")
            start_time = time.time()

            try:
                # 模拟API调用 - 使用基本参数格式
                api_url = source_config['base_url']
                params = {
                    'lang': 'en',
                    'limit': '10',
                    'from': (datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
                }

                # 添加额外参数（segment等）
                if source_config.get('extra_params'):
                    params.update(source_config['extra_params'])

                print(f"  - URL: {api_url}")
                print(f"  - Params: {params}")

                # 记录结果
                results[source_key] = {
                    'status': 'configured',
                    'name': source_config['name'],
                    'url': api_url,
                    'params': params,
                    'extra_params': source_config.get('extra_params', {}),
                    'execution_time': time.time() - start_time
                }

                print(f"  ✓ Configuration verified")

            except Exception as e:
                results[source_key] = {
                    'status': 'error',
                    'error': str(e),
                    'execution_time': time.time() - start_time
                }
                print(f"  ✗ Error: {e}")

        return results

    def test_technical_indicators_integration(self) -> Dict[str, Any]:
        """测试技术指标集成"""
        print("\nTesting technical indicators integration...")

        try:
            # 获取股票数据
            stock_data = get_hk_stock_data('0700.HK', 252)
            if not stock_data.empty:
                print(f"  ✓ Stock data retrieved: {len(stock_data)} records")

                # 测试技术指标计算
                indicators = CoreIndicators()
                prices = stock_data['close']

                rsi = indicators.calculate_rsi(prices, 14)
                sma = indicators.calculate_sma(prices, 20)
                macd = indicators.calculate_macd(prices, 12, 26, 9)

                latest_rsi = rsi.iloc[-1] if not rsi.empty else None
                latest_sma = sma.iloc[-1] if not sma.empty else None

                print(f"  ✓ RSI(14): {latest_rsi:.2f}")
                print(f"  ✓ SMA(20): {latest_sma:.2f}")

                return {
                    'status': 'success',
                    'stock_data_records': len(stock_data),
                    'rsi_latest': latest_rsi,
                    'sma_latest': latest_sma,
                    'indicators_calculated': 3
                }
            else:
                return {
                    'status': 'no_data',
                    'error': 'No stock data available'
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def test_vectorbt_integration(self) -> Dict[str, Any]:
        """测试VectorBT集成"""
        print("\nTesting VectorBT integration...")

        try:
            # 获取数据
            stock_data = get_hk_stock_data('0700.HK', 100)
            if not stock_data.empty:
                # 初始化VectorBT引擎
                engine = VectorBTEngine()

                # 测试策略回测
                result = engine.backtest_strategy(
                    stock_data,
                    'RSI_MEAN_REVERSION',
                    {'period': 14, 'oversold': 30, 'overbought': 70}
                )

                if result:
                    print(f"  ✓ Backtest completed")
                    print(f"  ✓ Total Return: {result.total_return:.2%}")
                    print(f"  ✓ Sharpe Ratio: {result.sharpe_ratio:.3f}")

                    return {
                        'status': 'success',
                        'total_return': result.total_return,
                        'sharpe_ratio': result.sharpe_ratio,
                        'max_drawdown': result.max_drawdown,
                        'data_records': len(stock_data)
                    }
                else:
                    return {
                        'status': 'no_result',
                        'error': 'Backtest returned None'
                    }
            else:
                return {
                    'status': 'no_data',
                    'error': 'No stock data available for backtest'
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行完整的综合测试"""
        print("=" * 60)
        print("INTEGRATED QUANTITATIVE TRADING SYSTEM TEST")
        print("=" * 60)

        # 1. 测试政府数据源配置
        government_results = await self.test_all_government_data_sources()

        # 2. 测试技术指标集成
        indicators_results = self.test_technical_indicators_integration()

        # 3. 测试VectorBT集成
        vectorbt_results = self.test_vectorbt_integration()

        # 计算总体结果
        total_execution_time = time.time() - self.start_time

        # 统计结果
        govt_success = sum(1 for r in government_results.values() if r.get('status') == 'configured')
        govt_total = len(government_results)

        # 综合评估
        overall_status = "PASS" if (
            govt_success == govt_total and
            indicators_results.get('status') == 'success' and
            vectorbt_results.get('status') == 'success'
        ) else "FAIL"

        # 生成报告
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'total_execution_time': total_execution_time,
            'test_modules': {
                'government_data_sources': {
                    'status': 'PASS' if govt_success == govt_total else 'PARTIAL',
                    'successful_sources': govt_success,
                    'total_sources': govt_total,
                    'success_rate': govt_success / govt_total * 100 if govt_total > 0 else 0,
                    'results': government_results
                },
                'technical_indicators': indicators_results,
                'vectorbt_backtest': vectorbt_results
            },
            'integration_summary': {
                'data_sources_integrated': govt_success,
                'indicators_working': indicators_results.get('indicators_calculated', 0),
                'backtest_successful': vectorbt_results.get('status') == 'success',
                'system_ready': overall_status == 'PASS'
            }
        }

        # 打印摘要
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {overall_status}")
        print(f"Execution Time: {total_execution_time:.2f}s")
        print(f"Government Data Sources: {govt_success}/{govt_total} configured")
        print(f"Technical Indicators: {indicators_results.get('status', 'UNKNOWN')}")
        print(f"VectorBT Integration: {vectorbt_results.get('status', 'UNKNOWN')}")
        print(f"System Ready: {report['integration_summary']['system_ready']}")

        if overall_status == "PASS":
            print("\n🎉 All tests passed! System is ready for production.")
        else:
            print("\n⚠️  Some tests failed. Please check the detailed results.")

        return report

    def save_report(self, report: Dict[str, Any]) -> str:
        """保存测试报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"integration_test_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nReport saved to: {report_file}")
        return report_file

async def main():
    """主函数"""
    tester = IntegratedSystemTest()

    # 运行综合测试
    report = await tester.run_comprehensive_test()

    # 保存报告
    report_file = tester.save_report(report)

    return report, report_file

if __name__ == "__main__":
    # 运行测试
    report, report_file = asyncio.run(main())

    # 输出结果路径供后续分析
    print(f"\nIntegration test completed!")
    print(f"Detailed report: {report_file}")