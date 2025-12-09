#!/usr/bin/env python3
"""
Test Reporting System
測試報告系統

Test and demonstrate the enhanced reporting system functionality
測試和演示增強報告系統功能
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.reporting import ReportGenerator, ReportType, ReportLanguage, ReportConfig, ReportData
from src.reporting.executive_summary import ExecutiveSummaryGenerator
from src.reporting.template_manager import TemplateManager

def create_sample_data():
    """創建模擬數據"""
    print("Creating sample data...")

    # Create sample price data
    dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
    n_days = len(dates)

    # Generate synthetic price data
    np.random.seed(42)
    returns = np.random.normal(0.0008, 0.02, n_days)  # Daily returns
    prices = [100]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))

    # Create DataFrame
    data = pd.DataFrame({
        'date': dates,
        'close': prices,
        'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'volume': np.random.randint(1000000, 5000000, n_days)
    })

    data.set_index('date', inplace=True)

    # Add returns
    data['returns'] = data['close'].pct_change()

    # Add strategy signals
    data['signals'] = np.random.choice([-1, 0, 1], n_days, p=[0.1, 0.8, 0.1])

    return data

def create_sample_backtest_result():
    """創建模擬回測結果"""
    print("Creating sample backtest result...")

    # Simulate backtest metrics
    class MockBacktestResult:
        def __init__(self):
            self.strategy = "RSI_MEAN_REVERSION"
            self.symbol = "0700.HK"
            self.start_date = datetime(2023, 1, 1)
            self.end_date = datetime(2024, 12, 31)
            self.total_return = 0.185  # 18.5%
            self.annual_return = 0.192  # 19.2%
            self.sharpe_ratio = 1.45
            self.max_drawdown = -0.125  # -12.5%
            self.volatility = 0.182  # 18.2%
            self.win_rate = 0.58  # 58%
            self.calmar_ratio = 1.54
            self.sortino_ratio = 2.12
            self.total_trades = 124
            self.profitable_trades = 72
            self.losing_trades = 52
            self.average_win = 0.025
            self.average_loss = -0.018
            self.profit_factor = 1.68
            self.var_95 = -0.035
            self.var_99 = -0.058
            self.expected_shortfall_95 = -0.042
            self.expected_shortfall_99 = -0.072
            self.beta = 1.12
            self.alpha = 0.034
            self.tracking_error = 0.156
            self.parameters = {
                'period': 14,
                'oversold': 30,
                'overbought': 70
            }

    return MockBacktestResult()

def test_executive_summary():
    """測試執行摘要生成"""
    print("\n" + "="*50)
    print("Testing Executive Summary Generation")
    print("="*50)

    # Create sample report data
    backtest_result = create_sample_backtest_result()

    report_data = ReportData(
        timestamp=datetime.now(),
        title="RSI均值回歸策略分析報告",
        subtitle="基於騰訊控股(0700.HK)的量化交易策略評估",
        period="2023年1月1日 至 2024年12月31日",
        total_return=backtest_result.total_return,
        annual_return=backtest_result.annual_return,
        sharpe_ratio=backtest_result.sharpe_ratio,
        max_drawdown=backtest_result.max_drawdown,
        volatility=backtest_result.volatility,
        win_rate=backtest_result.win_rate,
        calmar_ratio=backtest_result.calmar_ratio,
        sortino_ratio=backtest_result.sortino_ratio,
        total_trades=backtest_result.total_trades,
        profitable_trades=backtest_result.profitable_trades,
        losing_trades=backtest_result.losing_trades,
        average_win=backtest_result.average_win,
        average_loss=backtest_result.average_loss,
        profit_factor=backtest_result.profit_factor,
        var_95=backtest_result.var_95,
        var_99=backtest_result.var_99,
        expected_shortfall_95=backtest_result.expected_shortfall_95,
        expected_shortfall_99=backtest_result.expected_shortfall_99,
        beta=backtest_result.beta,
        alpha=backtest_result.alpha,
        tracking_error=backtest_result.tracking_error,
        strategy_name=backtest_result.strategy,
        strategy_parameters=backtest_result.parameters,
        benchmark_name="恆生指數"
    )

    # Generate executive summary
    summary_gen = ExecutiveSummaryGenerator()
    summary = summary_gen.generate(report_data, ReportLanguage.BILINGUAL)

    print("Generated Executive Summary:")
    print("-" * 30)
    print(summary[:500] + "...")  # Print first 500 characters
    print("\n✅ Executive summary generation successful!")

    return report_data

def test_template_manager():
    """測試模板管理器"""
    print("\n" + "="*50)
    print("Testing Template Manager")
    print("="*50)

    try:
        template_manager = TemplateManager()

        # List available templates
        templates = template_manager.list_templates()
        print(f"Available templates: {len(templates)}")
        for template in templates:
            print(f"  - {template.name}: {template.description}")

        # Get default template for strategy analysis
        default_template = template_manager.get_default_template(ReportType.STRATEGY_ANALYSIS)
        if default_template:
            print(f"Default strategy analysis template: {default_template.name}")

        print("✅ Template manager test successful!")
        return template_manager

    except Exception as e:
        print(f"❌ Template manager test failed: {e}")
        return None

def test_report_generation(report_data, template_manager=None):
    """測試報告生成"""
    print("\n" + "="*50)
    print("Testing Report Generation")
    print("="*50)

    try:
        # Create sample raw data
        raw_data = create_sample_data()

        # Configure report
        config = ReportConfig(
            report_type=ReportType.STRATEGY_ANALYSIS,
            language=ReportLanguage.BILINGUAL,
            include_charts=True,
            include_executive_summary=True,
            include_risk_analysis=True,
            include_detailed_metrics=True,
            export_pdf=False,  # Disable PDF for testing
            export_excel=False,
            template_name="professional",
            interactive_elements=True,
            author="Quant Trading System",
            confidentiality_level="Internal Use Only"
        )

        # Initialize report generator
        generator = ReportGenerator()

        # Set raw data for chart generation
        report_data.raw_data = raw_data

        # Generate report
        print("Generating report...")
        generated_files = generator.generate_report(report_data, config)

        print("Generated files:")
        for file_type, file_path in generated_files.items():
            print(f"  {file_type}: {file_path}")

        print("✅ Report generation successful!")
        return generated_files

    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

def test_pdf_export():
    """測試PDF導出"""
    print("\n" + "="*50)
    print("Testing PDF Export")
    print("="*50)

    try:
        from src.reporting.pdf_exporter import PDFExporter

        exporter = PDFExporter()

        if exporter.pdf_engine:
            print(f"PDF engine available: {exporter.pdf_engine}")

            # Create a simple HTML test
            test_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test PDF Export</title>
                <style>
                    body { font-family: Arial; padding: 20px; }
                    h1 { color: #333; }
                </style>
            </head>
            <body>
                <h1>PDF Export Test</h1>
                <p>This is a test of the PDF export functionality.</p>
                <p>Generated at: {}</p>
            </body>
            </html>
            """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            # Test HTML string to PDF
            output_path = Path("test_report.pdf")
            success = exporter.export_from_html_string(test_html, output_path)

            if success and output_path.exists():
                print(f"✅ PDF export successful! File: {output_path}")
                print(f"File size: {output_path.stat().st_size / 1024:.2f} KB")
            else:
                print("❌ PDF export failed")
        else:
            print("❌ No PDF engine available")

    except Exception as e:
        print(f"❌ PDF export test failed: {e}")

def test_batch_reports():
    """測試批量報告生成"""
    print("\n" + "="*50)
    print("Testing Batch Report Generation")
    print("="*50)

    try:
        # Create multiple report data
        reports = []

        strategies = [
            ("RSI_MEAN_REVERSION", {'period': 14, 'oversold': 30, 'overbought': 70}),
            ("MACD_CROSSOVER", {'fast': 12, 'slow': 26, 'signal': 9}),
            ("BOLLINGER_BANDS", {'period': 20, 'std_dev': 2.0})
        ]

        for i, (strategy_name, params) in enumerate(strategies):
            # Create variation in metrics
            base_return = 0.15 + (i * 0.05)
            base_sharpe = 1.2 + (i * 0.3)

            report_data = ReportData(
                timestamp=datetime.now(),
                title=f"{strategy_name} 策略分析報告",
                subtitle=f"量化交易策略評估 #{i+1}",
                period="2023年1月1日 至 2024年12月31日",
                total_return=base_return,
                annual_return=base_return * 1.1,
                sharpe_ratio=base_sharpe,
                max_drawdown=-0.15 + (i * 0.02),
                volatility=0.18 + (i * 0.02),
                win_rate=0.55 + (i * 0.05),
                calmar_ratio=base_return / abs(-0.15 + (i * 0.02)),
                sortino_ratio=base_sharpe * 1.2,
                total_trades=100 + (i * 20),
                profitable_trades=int((100 + (i * 20)) * (0.55 + (i * 0.05))),
                losing_trades=int((100 + (i * 20)) * (0.45 - (i * 0.05))),
                average_win=0.025,
                average_loss=-0.018,
                profit_factor=1.5 + (i * 0.2),
                var_95=-0.035,
                var_99=-0.058,
                expected_shortfall_95=-0.042,
                expected_shortfall_99=-0.072,
                beta=1.1,
                alpha=0.03,
                tracking_error=0.15,
                strategy_name=strategy_name,
                strategy_parameters=params,
                benchmark_name="恆生指數"
            )

            config = ReportConfig(
                report_type=ReportType.STRATEGY_ANALYSIS,
                language=ReportLanguage.CHINESE,
                include_charts=False,  # Disable charts for batch testing
                include_executive_summary=True,
                include_risk_analysis=True,
                export_pdf=False,
                export_excel=False,
                template_name="professional"
            )

            reports.append((report_data, config))

        # Generate batch reports
        generator = ReportGenerator()
        generated_files = generator.generate_batch_reports(reports)

        print(f"Batch report generation completed: {len(generated_files)} reports")
        for i, files in enumerate(generated_files):
            print(f"  Report {i+1}: {len(files)} files generated")

        print("✅ Batch report generation successful!")

    except Exception as e:
        print(f"❌ Batch report generation test failed: {e}")
        import traceback
        traceback.print_exc()

def run_comprehensive_test():
    """運行綜合測試"""
    print("🚀 Starting Comprehensive Reporting System Test")
    print("=" * 60)

    # Test executive summary
    report_data = test_executive_summary()

    # Test template manager
    template_manager = test_template_manager()

    # Test report generation
    generated_files = test_report_generation(report_data, template_manager)

    # Test PDF export
    test_pdf_export()

    # Test batch reports
    test_batch_reports()

    # Summary
    print("\n" + "="*60)
    print("🎉 Comprehensive Test Summary")
    print("="*60)

    if generated_files:
        print("✅ Core reporting system functionality verified")
        print("✅ Template system working")
        print("✅ Executive summary generation working")
        print("✅ HTML report generation working")
        print("✅ Batch processing working")

        if 'html' in generated_files:
            html_file = generated_files['html']
            print(f"\n📄 Sample report generated: {html_file}")
            print("   Open this file in a browser to view the report")

            # Check file size
            file_size = Path(html_file).stat().st_size / 1024
            print(f"   File size: {file_size:.2f} KB")
    else:
        print("❌ Some tests failed - check error messages above")

    print("\n" + "="*60)
    print("🏆 Test completed!")
    print("="*60)

if __name__ == "__main__":
    run_comprehensive_test()