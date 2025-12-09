#!/usr/bin/env python3
"""
完整系統測試 - 潛在問題識別
Comprehensive System Test - Potential Issues Identification
"""

import sys
import os
sys.path.append('src')

import json
import logging
from datetime import datetime
from pathlib import Path
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveSystemTest:
    """完整系統測試類"""

    def __init__(self):
        self.test_results = {
            'test_session': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'critical_issues': []
            },
            'module_tests': {},
            'api_tests': {},
            'data_tests': {},
            'performance_tests': {},
            'dependency_tests': {}
        }

    def run_all_tests(self):
        """運行所有測試"""
        print("=" * 60)
        print("完整系統測試 - 潛在問題識別")
        print("=" * 60)

        try:
            self.test_module_imports()
            self.test_api_connectivity()
            self.test_data_quality()
            self.test_performance()
            self.test_dependencies()
            self.test_local_files()
            self.test_integration()

            self.generate_report()

        except Exception as e:
            logger.error(f"測試執行失敗: {e}")
            traceback.print_exc()

        return self.test_results

    def test_module_imports(self):
        """測試模塊導入"""
        print("\n1. 模塊導入測試...")

        modules_to_test = [
            ('src.api.government_data', 'GovernmentDataAPI'),
            ('src.api.stock_api', 'get_hk_stock_data'),
            ('unified_data_architecture_standard', 'UnifiedDataArchitectureStandard'),
            ('improved_real_data_integration', 'ImprovedRealDataIntegration')
        ]

        for module_name, class_name in modules_to_test:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                self.test_results['module_tests'][module_name] = {
                    'status': 'PASS',
                    'message': 'Successfully imported'
                }
                print(f"[OK] {module_name}")
                self.test_results['test_session']['passed_tests'] += 1

            except Exception as e:
                self.test_results['module_tests'][module_name] = {
                    'status': 'FAIL',
                    'error': str(e),
                    'message': 'Import failed'
                }
                print(f"[FAIL] {module_name}: {e}")
                self.test_results['test_session']['failed_tests'] += 1
                self.test_results['test_session']['critical_issues'].append(f"Module import failed: {module_name}")

            self.test_results['test_session']['total_tests'] += 1

    def test_api_connectivity(self):
        """測試API連接性"""
        print("\n2. API連接性測試...")

        try:
            # 測試政府數據API
            from src.api.government_data import GovernmentDataAPI
            gov_api = GovernmentDataAPI()

            # HIBOR測試
            try:
                hibor = gov_api.get_hibor_data(5)
                if hibor and hibor.get('data'):
                    record_count = len(hibor['data'])
                    latest_rate = hibor['data'][0].get('hibor_overnight', 'N/A') if hibor['data'] else 'N/A'
                    self.test_results['api_tests']['hibor_api'] = {
                        'status': 'PASS',
                        'records': record_count,
                        'latest_rate': latest_rate,
                        'source': hibor.get('source', 'Unknown')
                    }
                    print(f"[OK] HIBOR API: {record_count} 條記錄, 最新利率: {latest_rate}")
                    self.test_results['test_session']['passed_tests'] += 1
                else:
                    self.test_results['api_tests']['hibor_api'] = {
                        'status': 'FAIL',
                        'error': 'No data returned'
                    }
                    print("[FAIL] HIBOR API: 無數據返回")
                    self.test_results['test_session']['failed_tests'] += 1
            except Exception as e:
                self.test_results['api_tests']['hibor_api'] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
                print(f"[FAIL] HIBOR API: {e}")
                self.test_results['test_session']['failed_tests'] += 1

            self.test_results['test_session']['total_tests'] += 1

            # 匯率API測試
            try:
                exchange = gov_api.get_exchange_rates(5)
                if exchange and exchange.get('data'):
                    record_count = len(exchange['data'])
                    self.test_results['api_tests']['exchange_api'] = {
                        'status': 'PASS',
                        'records': record_count,
                        'source': exchange.get('source', 'Unknown')
                    }
                    print(f"[OK] 匯率 API: {record_count} 條記錄")
                    self.test_results['test_session']['passed_tests'] += 1
                else:
                    self.test_results['api_tests']['exchange_api'] = {
                        'status': 'FAIL',
                        'error': 'No data returned'
                    }
                    print("[FAIL] 匯率 API: 無數據返回")
                    self.test_results['test_session']['failed_tests'] += 1
            except Exception as e:
                self.test_results['api_tests']['exchange_api'] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
                print(f"[FAIL] 匯率 API: {e}")
                self.test_results['test_session']['failed_tests'] += 1

            self.test_results['test_session']['total_tests'] += 1

            # 股票API測試
            try:
                from src.api.stock_api import get_hk_stock_data
                stock_data = get_hk_stock_data('0700.HK', 10)

                if stock_data is not None and len(stock_data) > 0:
                    latest_price = stock_data['close'].iloc[-1] if 'close' in stock_data.columns else 'N/A'
                    self.test_results['api_tests']['stock_api'] = {
                        'status': 'PASS',
                        'records': len(stock_data),
                        'latest_price': float(latest_price) if latest_price != 'N/A' else None,
                        'columns': list(stock_data.columns)
                    }
                    print(f"[OK] 股票 API: {len(stock_data)} 條記錄, 最新價格: {latest_price}")
                    self.test_results['test_session']['passed_tests'] += 1
                else:
                    self.test_results['api_tests']['stock_api'] = {
                        'status': 'FAIL',
                        'error': 'No stock data returned'
                    }
                    print("[FAIL] 股票 API: 無數據返回")
                    self.test_results['test_session']['failed_tests'] += 1
            except Exception as e:
                self.test_results['api_tests']['stock_api'] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
                print(f"[FAIL] 股票 API: {e}")
                self.test_results['test_session']['failed_tests'] += 1
                self.test_results['test_session']['critical_issues'].append(f"Stock API failed: {e}")

            self.test_results['test_session']['total_tests'] += 1

        except Exception as e:
            logger.error(f"API連接性測試失敗: {e}")
            self.test_results['test_session']['critical_issues'].append(f"API connectivity test failed: {e}")

    def test_data_quality(self):
        """測試數據質量"""
        print("\n3. 數據質量測試...")

        try:
            from unified_data_architecture_standard import UnifiedDataArchitectureStandard, DataSourceType

            standardizer = UnifiedDataArchitectureStandard()

            # 測試數據標準化
            test_data = [
                {'date': '2025-01-01', 'value': 100.0},
                {'date': '2025-01-02', 'value': 101.5},
                {'date': '2025-01-03', 'value': 99.8}
            ]

            try:
                standardized = standardizer.standardize_data(test_data, DataSourceType.GOVERNMENT_DATA)

                if standardized is not None and len(standardized) > 0:
                    self.test_results['data_tests']['standardization'] = {
                        'status': 'PASS',
                        'input_records': len(test_data),
                        'output_records': len(standardized),
                        'columns': list(standardized.columns)
                    }
                    print(f"[OK] 數據標準化: {len(test_data)} -> {len(standardized)} 條記錄")
                    print(f"     標準化列: {list(standardized.columns)}")
                    self.test_results['test_session']['passed_tests'] += 1
                else:
                    self.test_results['data_tests']['standardization'] = {
                        'status': 'FAIL',
                        'error': 'Standardization returned None'
                    }
                    print("[FAIL] 數據標準化返回None")
                    self.test_results['test_session']['failed_tests'] += 1
            except Exception as e:
                self.test_results['data_tests']['standardization'] = {
                    'status': 'FAIL',
                    'error': str(e)
                }
                print(f"[FAIL] 數據標準化異常: {e}")
                self.test_results['test_session']['failed_tests'] += 1

            self.test_results['test_session']['total_tests'] += 1

        except Exception as e:
            logger.error(f"數據質量測試失敗: {e}")
            self.test_results['test_session']['critical_issues'].append(f"Data quality test failed: {e}")

    def test_performance(self):
        """測試系統性能"""
        print("\n4. 系統性能測試...")

        try:
            import time
            import psutil

            # 內存使用檢查
            memory = psutil.virtual_memory()
            self.test_results['performance_tests']['memory'] = {
                'total_gb': round(memory.total / (1024**3), 2),
                'used_gb': round(memory.used / (1024**3), 2),
                'percent': memory.percent
            }

            if memory.percent > 80:
                print(f"[WARNING] 高內存使用: {memory.percent:.1f}%")
                self.test_results['test_session']['critical_issues'].append(f"High memory usage: {memory.percent}%")
            else:
                print(f"[OK] 內存使用: {memory.percent:.1f}%")

            # CPU使用檢查
            cpu_percent = psutil.cpu_percent(interval=1)
            self.test_results['performance_tests']['cpu'] = {
                'percent': cpu_percent
            }

            if cpu_percent > 80:
                print(f"[WARNING] 高CPU使用: {cpu_percent:.1f}%")
                self.test_results['test_session']['critical_issues'].append(f"High CPU usage: {cpu_percent}%")
            else:
                print(f"[OK] CPU使用: {cpu_percent:.1f}%")

            # API響應時間測試
            try:
                from src.api.government_data import GovernmentDataAPI
                gov_api = GovernmentDataAPI()

                start_time = time.time()
                hibor = gov_api.get_hibor_data(3)
                end_time = time.time()

                response_time = (end_time - start_time) * 1000  # ms

                self.test_results['performance_tests']['api_response_time'] = {
                    'hibor_api_ms': round(response_time, 2)
                }

                if response_time > 5000:  # 5 seconds
                    print(f"[WARNING] API響應緩慢: {response_time:.0f}ms")
                    self.test_results['test_session']['critical_issues'].append(f"Slow API response: {response_time:.0f}ms")
                else:
                    print(f"[OK] API響應時間: {response_time:.0f}ms")

            except Exception as e:
                print(f"[FAIL] API響應時間測試失敗: {e}")

            # 磁盘空間檢查
            disk = psutil.disk_usage('.')
            self.test_results['performance_tests']['disk'] = {
                'total_gb': round(disk.total / (1024**3), 2),
                'used_gb': round(disk.used / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent': round(disk.used / disk.total * 100, 2)
            }

            if disk.percent > 90:
                print(f"[WARNING] 磁盘空間不足: {disk.percent:.1f}%")
                self.test_results['test_session']['critical_issues'].append(f"Low disk space: {disk.percent}%")
            else:
                print(f"[OK] 磁盘使用: {disk.percent:.1f}%")

        except ImportError:
            print("[WARNING] psutil未安裝，跳過性能測試")
            self.test_results['test_session']['critical_issues'].append("psutil not installed for performance monitoring")

        except Exception as e:
            logger.error(f"性能測試失敗: {e}")

    def test_dependencies(self):
        """測試依賴包"""
        print("\n5. 依賴檢查...")

        required_packages = [
            'pandas',
            'numpy',
            'requests',
            'pathlib'
        ]

        optional_packages = [
            'psutil',
            'aiohttp',
            'vectorbt'
        ]

        for package in required_packages:
            try:
                __import__(package)
                self.test_results['dependency_tests'][package] = {
                    'status': 'PASS',
                    'type': 'required'
                }
                print(f"[OK] {package} (必需)")
            except ImportError:
                self.test_results['dependency_tests'][package] = {
                    'status': 'FAIL',
                    'type': 'required',
                    'error': 'Package not found'
                }
                print(f"[FAIL] {package} (必需) - 未安裝")
                self.test_results['test_session']['critical_issues'].append(f"Required package missing: {package}")
                self.test_results['test_session']['failed_tests'] += 1

            self.test_results['test_session']['total_tests'] += 1

        for package in optional_packages:
            try:
                __import__(package)
                self.test_results['dependency_tests'][package] = {
                    'status': 'PASS',
                    'type': 'optional'
                }
                print(f"[OK] {package} (可選)")
            except ImportError:
                self.test_results['dependency_tests'][package] = {
                    'status': 'WARNING',
                    'type': 'optional',
                    'error': 'Package not found'
                }
                print(f"[WARNING] {package} (可選) - 未安裝")

    def test_local_files(self):
        """測試本地文件"""
        print("\n6. 本地數據文件檢查...")

        data_dir = Path('data/government')

        if not data_dir.exists():
            print(f"[FAIL] 數據目錄不存在: {data_dir}")
            self.test_results['test_session']['critical_issues'].append(f"Data directory missing: {data_dir}")
            return

        # 獲取所有JSON文件
        json_files = list(data_dir.glob('*.json'))
        self.test_results['data_tests']['local_files'] = {
            'directory_exists': True,
            'total_files': len(json_files),
            'file_list': [f.name for f in json_files]
        }

        print(f"[OK] 本地數據文件: {len(json_files)} 個")

        # 檢查關鍵數據文件
        key_file_patterns = {
            'hibor_rates': 'HIBOR利率數據',
            'exchange_rates': '匯率數據',
            'monetary_base': '貨幣基礎數據',
            'interbank': '銀行流動性數據',
            'efbn': '外匯基金票據數據'
        }

        missing_files = []
        for pattern, description in key_file_patterns.items():
            matching_files = [f for f in json_files if pattern in f.name]
            if matching_files:
                print(f"     [OK] {description}: {len(matching_files)} 個文件")

                # 檢查文件內容
                try:
                    latest_file = max(matching_files, key=lambda f: f.stat().st_mtime)
                    with open(latest_file, 'r', encoding='utf-8') as file:
                        data = json.load(file)

                    if 'data' in data and data['data']:
                        record_count = len(data['data'])
                        print(f"         最新文件: {latest_file.name} ({record_count} 條記錄)")
                    else:
                        print(f"         [WARNING] 文件內容為空: {latest_file.name}")
                        missing_files.append(f"{description} (empty)")

                except Exception as e:
                    print(f"         [FAIL] 文件讀取失敗: {e}")
                    missing_files.append(f"{description} (read error)")
            else:
                print(f"     [FAIL] {description}: 缺失")
                missing_files.append(description)

        if missing_files:
            self.test_results['test_session']['critical_issues'].extend([f"Missing data: {item}" for item in missing_files])

    def test_integration(self):
        """測試系統集成"""
        print("\n7. 系統集成測試...")

        try:
            # 測試完整數據流程
            from improved_real_data_integration import ImprovedRealDataIntegration

            integration_system = ImprovedRealDataIntegration()

            # 簡單的Alpha信號測試
            print("     測試Alpha信號生成...")
            alpha_result = integration_system.create_alpha_signals_with_real_data("0700.HK", 30)

            if alpha_result and alpha_result.get('quality_score', 0) > 0:
                quality_score = alpha_result['quality_score']
                data_sources = len(alpha_result.get('data_sources_used', []))

                self.test_results['data_tests']['integration'] = {
                    'status': 'PASS',
                    'quality_score': quality_score,
                    'data_sources': data_sources,
                    'signals_generated': bool(alpha_result.get('signals'))
                }

                print(f"[OK] 系統集成測試: 質量評分 {quality_score:.2f}, 數據源 {data_sources} 個")
                self.test_results['test_session']['passed_tests'] += 1
            else:
                self.test_results['data_tests']['integration'] = {
                    'status': 'FAIL',
                    'error': 'Low quality score or no signals'
                }
                print("[FAIL] 系統集成測試: 低質量評分或無信號生成")
                self.test_results['test_session']['failed_tests'] += 1
                self.test_results['test_session']['critical_issues'].append("Integration test failed")

            self.test_results['test_session']['total_tests'] += 1

        except Exception as e:
            self.test_results['data_tests']['integration'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            print(f"[FAIL] 系統集成測試異常: {e}")
            self.test_results['test_session']['critical_issues'].append(f"Integration test error: {e}")

    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("測試結果摘要")
        print("=" * 60)

        session = self.test_results['test_session']
        total = session['total_tests']
        passed = session['passed_tests']
        failed = session['failed_tests']
        critical = session['critical_issues']

        print(f"總測試數: {total}")
        print(f"通過: {passed}")
        print(f"失敗: {failed}")
        print(f"成功率: {passed/total*100:.1f}%" if total > 0 else "N/A")

        if critical:
            print(f"\n關鍵問題 ({len(critical)} 個):")
            for i, issue in enumerate(critical, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n關鍵問題: 無")

        # 分類統計
        print(f"\n分類測試結果:")
        categories = {
            '模塊導入': self.test_results['module_tests'],
            'API連接': self.test_results['api_tests'],
            '數據質量': self.test_results['data_tests'],
            '系統性能': self.test_results['performance_tests'],
            '依賴檢查': self.test_results['dependency_tests']
        }

        for category, tests in categories.items():
            if tests:
                passed_count = sum(1 for test in tests.values() if test.get('status') == 'PASS')
                total_count = len(tests)
                status = "[OK]" if passed_count == total_count else "[PARTIAL]" if passed_count > 0 else "[FAIL]"
                print(f"  {category}: {passed_count}/{total_count} {status}")

        # 保存詳細報告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"comprehensive_system_test_report_{timestamp}.json"

        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n詳細報告已保存到: {report_file}")
        except Exception as e:
            print(f"\n報告保存失敗: {e}")

        print("\n" + "=" * 60)
        print("測試完成")
        print("=" * 60)

def main():
    """主函數"""
    tester = ComprehensiveSystemTest()
    results = tester.run_all_tests()

    return results

if __name__ == "__main__":
    test_results = main()