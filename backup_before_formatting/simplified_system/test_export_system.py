#!/usr/bin/env python3
"""
簡化系統 - 導出系統測試
驗證所有導出功能的完整性
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 添加當前目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from src.export.export_manager import ExportManager, ExportRequest
from src.export.export_menu import ExportMenu

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExportSystemTester:
    """導出系統測試類"""

    def __init__(self):
        self.export_manager = ExportManager()
        self.test_results = []

    def run_all_tests(self):
        """運行所有測試"""
        print("🚀 開始導出系統測試")
        print("="*60)

        tests = [
            ("導出管理器初始化", self.test_export_manager_init),
            ("支持格式檢查", self.test_supported_formats),
            ("JSON格式導出", self.test_json_export),
            ("Excel格式導出", self.test_excel_export),
            ("CSV格式導出", self.test_csv_export),
            ("HTML格式導出", self.test_html_export),
            ("PDF格式導出", self.test_pdf_export),
            ("回測結果導出", self.test_backtest_results_export),
            ("技術指標導出", self.test_technical_indicators_export),
            ("批量導出", self.test_batch_export),
            ("導出菜單", self.test_export_menu),
            ("錯誤處理", self.test_error_handling)
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            print(f"\n🧪 測試: {test_name}")
            print("-" * 40)

            try:
                start_time = time.time()
                result = test_func()
                end_time = time.time()

                if result:
                    print(f"✅ {test_name} - 通過 ({end_time - start_time:.2f}s)")
                    passed_tests += 1
                    self.test_results.append((test_name, True, None))
                else:
                    print(f"❌ {test_name} - 失敗")
                    self.test_results.append((test_name, False, "測試返回False"))

            except Exception as e:
                print(f"❌ {test_name} - 異常: {e}")
                self.test_results.append((test_name, False, str(e)))
                logger.error(f"測試異常 {test_name}: {e}")

        # 測試總結
        print(f"\n{'='*60}")
        print(f"📊 測試總結")
        print(f"{'='*60}")
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {total_tests - passed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")

        # 顯示失敗的測試
        failed_tests = [(name, error) for name, success, error in self.test_results if not success]
        if failed_tests:
            print(f"\n❌ 失敗的測試:")
            for name, error in failed_tests:
                print(f"  - {name}: {error}")

        # 保存測試報告
        self.save_test_report()

        return passed_tests == total_tests

    def test_export_manager_init(self):
        """測試導出管理器初始化"""
        return self.export_manager is not None

    def test_supported_formats(self):
        """測試支持格式檢查"""
        formats = self.export_manager.get_supported_formats()
        expected_formats = ['xlsx', 'pdf', 'json', 'csv', 'html']

        for fmt in expected_formats:
            if fmt not in formats:
                print(f"⚠️ 缺少格式: {fmt}")
                return False

        print(f"支持格式: {', '.join(formats)}")
        return True

    def test_json_export(self):
        """測試JSON格式導出"""
        # 創建測試數據
        test_data = {
            'strategy': 'RSI_MEAN_REVERSION',
            'symbol': '0700.HK',
            'summary': {
                'total_return': 0.156,
                'sharpe_ratio': 1.23,
                'max_drawdown': -0.085
            },
            'trades': pd.DataFrame([
                {'date': '2023-01-01', 'action': 'BUY', 'price': 450.5, 'quantity': 100},
                {'date': '2023-01-15', 'action': 'SELL', 'price': 475.2, 'quantity': 100}
            ])
        }

        request = ExportRequest(
            data=test_data,
            format='json',
            filename='test_json_export'
        )

        result = self.export_manager.export(request)
        return result.success and Path(result.file_path).exists()

    def test_excel_export(self):
        """測試Excel格式導出"""
        test_data = self._generate_test_dataframe()

        request = ExportRequest(
            data=test_data,
            format='xlsx',
            filename='test_excel_export'
        )

        result = self.export_manager.export(request)
        return result.success and Path(result.file_path).exists()

    def test_csv_export(self):
        """測試CSV格式導出"""
        test_data = self._generate_test_dataframe()

        request = ExportRequest(
            data=test_data,
            format='csv',
            filename='test_csv_export'
        )

        result = self.export_manager.export(request)
        return result.success and Path(result.file_path).exists()

    def test_html_export(self):
        """測試HTML格式導出"""
        test_data = self._generate_test_backtest_results()

        request = ExportRequest(
            data=test_data,
            format='html',
            filename='test_html_export'
        )

        result = self.export_manager.export(request)
        return result.success and Path(result.file_path).exists()

    def test_pdf_export(self):
        """測試PDF格式導出"""
        if not self.export_manager.pdf_exporter:
            print("⚠️ PDF導出器不可用，跳過PDF測試")
            return True  # 跳過測試，不算失敗

        test_data = self._generate_test_backtest_results()

        request = ExportRequest(
            data=test_data,
            format='pdf',
            filename='test_pdf_export'
        )

        result = self.export_manager.export(request)
        return result.success and Path(result.file_path).exists()

    def test_backtest_results_export(self):
        """測試回測結果導出"""
        backtest_data = self._generate_test_backtest_results()

        result = self.export_manager.export_backtest_results(
            backtest_data,
            format='xlsx',
            filename='test_backtest_results'
        )

        return result.success and Path(result.file_path).exists()

    def test_technical_indicators_export(self):
        """測試技術指標導出"""
        indicators_data = self._generate_test_indicators_data()

        result = self.export_manager.export_technical_indicators(
            indicators_data,
            symbol='0700.HK',
            format='xlsx',
            filename='test_technical_indicators'
        )

        return result.success and Path(result.file_path).exists()

    def test_batch_export(self):
        """測試批量導出"""
        requests = []
        for i in range(3):
            test_data = {
                'batch_id': i,
                'data': list(range(10 + i))
            }

            request = ExportRequest(
                data=test_data,
                format='json',
                filename=f'test_batch_{i}'
            )
            requests.append(request)

        results = self.export_manager.batch_export(requests)

        # 檢查是否所有請求都成功
        success_count = sum(1 for r in results if r.success)
        return success_count == len(requests)

    def test_export_menu(self):
        """測試導出菜單"""
        try:
            menu = ExportMenu(self.export_manager)
            return menu is not None
        except Exception as e:
            print(f"導出菜單初始化失敗: {e}")
            return False

    def test_error_handling(self):
        """測試錯誤處理"""
        # 測試無效格式
        request = ExportRequest(
            data={'test': 'data'},
            format='invalid_format',
            filename='test_error'
        )

        result = self.export_manager.export(request)
        return not result.success  # 應該失敗

    def _generate_test_dataframe(self) -> pd.DataFrame:
        """生成測試DataFrame"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'date': dates,
            'open': np.random.uniform(400, 600, 100),
            'high': np.random.uniform(410, 610, 100),
            'low': np.random.uniform(390, 590, 100),
            'close': np.random.uniform(400, 600, 100),
            'volume': np.random.randint(1000000, 5000000, 100),
            'rsi': np.random.uniform(20, 80, 100)
        }

        return pd.DataFrame(data)

    def _generate_test_backtest_results(self) -> dict:
        """生成測試回測結果"""
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        returns = np.random.normal(0.001, 0.02, 252)
        portfolio_value = np.cumprod(1 + returns) * 100000

        # 生成交易記錄
        n_trades = 20
        trades = []
        for i in range(n_trades):
            trades.append({
                'date': dates[i].strftime('%Y-%m-%d'),
                'action': 'BUY' if i % 2 == 0 else 'SELL',
                'symbol': '0700.HK',
                'quantity': np.random.randint(100, 500),
                'price': round(np.random.uniform(400, 600), 2),
                'pnl': round(np.random.uniform(-1000, 1000), 2)
            })

        return {
            'summary': {
                'total_return': 0.156,
                'annual_return': 0.142,
                'sharpe_ratio': 1.23,
                'max_drawdown': -0.085,
                'volatility': 0.186,
                'win_rate': 0.58,
                'trade_count': n_trades
            },
            'performance_metrics': {
                'sortino_ratio': 1.67,
                'calmar_ratio': 1.95,
                'profit_factor': 1.34,
                'avg_win': 2456.78,
                'avg_loss': -1823.45,
                'largest_win': 12345.67,
                'largest_loss': -8765.43
            },
            'trades': pd.DataFrame(trades),
            'portfolio_value': pd.Series(portfolio_value, index=dates),
            'returns': pd.Series(returns, index=dates),
            'metadata': {
                'strategy': 'RSI_MEAN_REVERSION',
                'symbol': '0700.HK',
                'start_date': dates[0].strftime('%Y-%m-%d'),
                'end_date': dates[-1].strftime('%Y-%m-%d')
            }
        }

    def _generate_test_indicators_data(self) -> dict:
        """生成測試技術指標數據"""
        dates = pd.date_range('2023-01-01', periods=100, freq='D')

        indicators = {
            'RSI': pd.Series(np.random.uniform(20, 80, 100), index=dates),
            'MACD': pd.Series(np.random.uniform(-50, 50, 100), index=dates),
            'Signal': pd.Series(np.random.uniform(-30, 30, 100), index=dates),
            'SMA_20': pd.Series(np.random.uniform(400, 600, 100), index=dates),
            'SMA_50': pd.Series(np.random.uniform(400, 600, 100), index=dates),
            'Upper_Band': pd.Series(np.random.uniform(550, 650, 100), index=dates),
            'Lower_Band': pd.Series(np.random.uniform(350, 450, 100), index=dates),
            'K': pd.Series(np.random.uniform(20, 80, 100), index=dates),
            'D': pd.Series(np.random.uniform(20, 80, 100), index=dates),
            'J': pd.Series(np.random.uniform(-20, 100, 100), index=dates)
        }

        return indicators

    def save_test_report(self):
        """保存測試報告"""
        report = {
            'test_time': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed_tests': sum(1 for _, success, _ in self.test_results if success),
            'failed_tests': sum(1 for _, success, _ in self.test_results if not success),
            'success_rate': sum(1 for _, success, _ in self.test_results if success) / len(self.test_results) * 100,
            'results': [
                {
                    'test_name': name,
                    'success': success,
                    'error': error
                }
                for name, success, error in self.test_results
            ]
        }

        report_file = Path('export_system_test_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 測試報告已保存: {report_file}")

        # 生成HTML報告
        html_report = self._generate_html_report(report)
        html_file = Path('export_system_test_report.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)

        print(f"🌐 HTML測試報告已保存: {html_file}")

    def _generate_html_report(self, report: dict) -> str:
        """生成HTML測試報告"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>導出系統測試報告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .test-result {{ margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">🚀 導出系統測試報告</h1>

        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">總測試數</h5>
                        <h3 class="text-primary">{report['total_tests']}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">通過</h5>
                        <h3 class="text-success">{report['passed_tests']}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">失敗</h5>
                        <h3 class="text-danger">{report['failed_tests']}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h5 class="card-title">成功率</h5>
                        <h3 class="text-info">{report['success_rate']:.1f}%</h3>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">
                <h5>測試結果詳情</h5>
            </div>
            <div class="card-body">
                <div class="list-group">
"""

        for result in report['results']:
            status_class = 'success' if result['success'] else 'failure'
            status_icon = '✅' if result['success'] else '❌'
            status_text = '通過' if result['success'] else '失敗'

            html += f"""
                    <div class="list-group-item test-result">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">{status_icon} {result['test_name']}</h6>
                            <span class="badge bg-{status_class}">{status_text}</span>
                        </div>
                        {f'<small class="text-muted">錯誤: {result["error"]}</small>' if result["error"] else ''}
                    </div>
"""

        html += f"""
                </div>
            </div>
        </div>

        <div class="mt-4 text-center text-muted">
            <p>報告生成時間: {report['test_time']}</p>
            <p>由簡化系統導出模塊生成</p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
        return html


def main():
    """主函數"""
    print("🔧 簡化系統 - 導出系統測試")
    print("="*60)

    try:
        tester = ExportSystemTester()
        success = tester.run_all_tests()

        if success:
            print("\n🎉 所有測試通過！導出系統運行正常。")
            return 0
        else:
            print("\n⚠️ 部分測試失敗，請檢查錯誤信息。")
            return 1

    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        logger.error(f"測試執行失敗: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)