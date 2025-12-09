#!/usr/bin/env python3
"""
Reporting System Demo
報告系統演示

Demonstrate the enhanced reporting system capabilities
演示增強報告系統功能
"""

import sys
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import webbrowser

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

def demo_quick_report():
    """快速報告演示"""
    print("Quick Report Generation Demo")
    print("-" * 40)

    # Import the reporting system
    try:
        from src.reporting import ReportGenerator, ReportType, ReportLanguage, ReportConfig, ReportData

        # Create sample data similar to real backtest results
        print("📊 Creating sample backtest data...")

        # Simulate a successful trading strategy result
        report_data = ReportData(
            timestamp=datetime.now(),
            title="雙移動平均線策略分析報告",
            subtitle="基於港交所(0388.HK)的高頻量化交易策略",
            period="2024年1月1日 至 2024年11月23日",
            total_return=0.2456,  # 24.56%
            annual_return=0.2834,  # 28.34%
            sharpe_ratio=1.85,
            max_drawdown=-0.0876,  # -8.76%
            volatility=0.1567,     # 15.67%
            win_rate=0.6234,       # 62.34%
            calmar_ratio=3.23,
            sortino_ratio=2.67,
            total_trades=156,
            profitable_trades=98,
            losing_trades=58,
            average_win=0.0234,
            average_loss=-0.0156,
            profit_factor=2.08,
            var_95=-0.0234,
            var_99=-0.0412,
            expected_shortfall_95=-0.0312,
            expected_shortfall_99=-0.0523,
            beta=0.956,
            alpha=0.0412,
            tracking_error=0.0876,
            strategy_name="DUAL_MOVING_AVERAGE",
            strategy_parameters={
                'short_period': 20,
                'long_period': 50,
                'signal_threshold': 0.001
            },
            benchmark_name="恆生指數"
        )

        # Create some sample price data for charts
        print("📈 Generating sample price data for charts...")
        dates = pd.date_range(start='2024-01-01', end='2024-11-23', freq='D')
        n_days = len(dates)

        np.random.seed(42)
        base_price = 280.50
        returns = np.random.normal(0.0008, 0.025, n_days)
        prices = [base_price]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        # Create DataFrame with OHLCV data
        price_data = pd.DataFrame({
            'close': prices,
            'open': [p * (1 + np.random.normal(0, 0.008)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.015))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.015))) for p in prices],
            'volume': np.random.randint(500000, 2000000, n_days),
            'returns': returns
        }, index=dates)

        # Add some strategy signals
        price_data['signals'] = 0
        # Add some buy and sell signals
        buy_signals = np.random.choice(n_days, size=15, replace=False)
        sell_signals = np.random.choice(n_days, size=12, replace=False)
        price_data.iloc[buy_signals, price_data.columns.get_loc('signals')] = 1
        price_data.iloc[sell_signals, price_data.columns.get_loc('signals')] = -1

        report_data.raw_data = price_data

        # Configure the report
        print("⚙️ Configuring report settings...")
        config = ReportConfig(
            report_type=ReportType.STRATEGY_ANALYSIS,
            language=ReportLanguage.BILINGUAL,  # Chinese + English
            include_charts=True,
            include_executive_summary=True,
            include_risk_analysis=True,
            include_detailed_metrics=True,
            export_pdf=False,  # Disable for demo speed
            export_excel=True,
            template_name="professional",
            interactive_elements=True,
            author="量化交易分析系統",
            confidentiality_level="內部使用"
        )

        # Generate the report
        print("🚀 Generating professional report...")
        generator = ReportGenerator()
        generated_files = generator.generate_report(report_data, config)

        print("\n✅ Report Generated Successfully!")
        print("=" * 50)

        # Display results
        print("📁 Generated Files:")
        for file_type, file_path in generated_files.items():
            file_info = Path(file_path)
            size_kb = file_info.stat().st_size / 1024
            print(f"  📄 {file_type.upper()}: {file_info.name} ({size_kb:.1f} KB)")
            print(f"     Path: {file_path}")

        # Try to open the HTML report
        if 'html' in generated_files:
            html_file = generated_files['html']
            print(f"\n🌐 Opening report in browser...")
            try:
                webbrowser.open(f'file://{Path(html_file).absolute()}')
                print("✅ Report opened in browser!")
            except Exception as e:
                print(f"❌ Could not open browser: {e}")
                print(f"   Please manually open: {html_file}")

        return generated_files

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required dependencies are installed:")
        print("   pip install jinja2 plotly pandas numpy")
        return {}
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return {}

def demo_executive_summary():
    """執行摘要演示"""
    print("\n" + "="*50)
    print("🎯 Executive Summary Demo")
    print("-" * 40)

    try:
        from src.reporting.executive_summary import ExecutiveSummaryGenerator
        from src.reporting import ReportData, ReportLanguage

        # Create high-performing strategy data
        report_data = ReportData(
            timestamp=datetime.now(),
            title="高頻套利策略執行摘要",
            subtitle="機構級量化投資策略評估",
            period="2024年 Q1-Q3",
            total_return=0.3421,  # 34.21%
            annual_return=0.4567,  # 45.67%
            sharpe_ratio=2.87,
            max_drawdown=-0.0567,  # -5.67%
            volatility=0.1345,     # 13.45%
            win_rate=0.6892,       # 68.92%
            calmar_ratio=8.06,
            sortino_ratio=4.23,
            total_trades=892,
            profitable_trades=615,
            losing_trades=277,
            average_win=0.0187,
            average_loss=-0.0098,
            profit_factor=3.45,
            var_95=-0.0123,
            var_99=-0.0234,
            expected_shortfall_95=-0.0167,
            expected_shortfall_99=-0.0289,
            beta=0.234,
            alpha=0.0892,
            tracking_error=0.0456,
            strategy_name="HIGH_FREQUENCY_ARBITRAGE",
            strategy_parameters={
                'hold_period': 'intraday',
                'max_position': 0.02,
                'stop_loss': 0.005
            },
            benchmark_name="無風險利率"
        )

        # Generate executive summary
        print("🧠 Generating AI-powered executive summary...")
        summary_gen = ExecutiveSummaryGenerator()

        # Generate bilingual summary
        summary = summary_gen.generate(report_data, ReportLanguage.BILINGUAL)

        print("\n📋 Generated Executive Summary:")
        print("=" * 50)
        print(summary[:1000] + "\n... [truncated for demo]")
        print("=" * 50)

        print("✅ Executive summary generated successfully!")
        return summary

    except Exception as e:
        print(f"❌ Error generating executive summary: {e}")
        return ""

def demo_template_system():
    """模板系統演示"""
    print("\n" + "="*50)
    print("🎯 Template System Demo")
    print("-" * 40)

    try:
        from src.reporting.template_manager import TemplateManager, TemplateType

        print("📚 Initializing template manager...")
        template_manager = TemplateManager()

        # List available templates
        templates = template_manager.list_templates()
        print(f"\n📋 Available Templates ({len(templates)}):")
        for template in templates:
            status = "✅" if template.is_active else "❌"
            default = " [DEFAULT]" if template.is_default else ""
            print(f"  {status} {template.name}: {template.description}{default}")

        # Get default template
        default_template = template_manager.get_default_template(TemplateType.STRATEGY_ANALYSIS)
        if default_template:
            print(f"\n🎯 Default Strategy Template: {default_template.name}")

        # Show template preview
        if default_template:
            print("\n👁️ Template Preview (first 500 chars):")
            preview = template_manager.preview_template(default_template.name)
            print("-" * 30)
            print(preview[:500] + "...")
            print("-" * 30)

        print("✅ Template system demo completed!")
        return template_manager

    except Exception as e:
        print(f"❌ Error with template system: {e}")
        return None

def demo_multi_language():
    """多語言演示"""
    print("\n" + "="*50)
    print("🎯 Multi-Language Report Demo")
    print("-" * 40)

    try:
        from src.reporting import ReportGenerator, ReportType, ReportLanguage, ReportConfig, ReportData

        languages = [
            (ReportLanguage.CHINESE, "中文報告"),
            (ReportLanguage.ENGLISH, "English Report"),
            (ReportLanguage.BILINGUAL, "雙語報告 / Bilingual Report")
        ]

        for lang, lang_name in languages:
            print(f"\n🌍 Generating {lang_name}...")

            # Create report data
            report_data = ReportData(
                timestamp=datetime.now(),
                title="策略分析報告" if lang != ReportLanguage.ENGLISH else "Strategy Analysis Report",
                subtitle="量化交易評估" if lang != ReportLanguage.ENGLISH else "Quantitative Trading Evaluation",
                period="2024年度",
                total_return=0.1876,
                annual_return=0.1987,
                sharpe_ratio=1.56,
                max_drawdown=-0.0987,
                volatility=0.1234,
                win_rate=0.5876,
                calmar_ratio=2.01,
                sortino_ratio=1.89,
                total_trades=234,
                profitable_trades=137,
                losing_trades=97,
                average_win=0.0198,
                average_loss=-0.0134,
                profit_factor=1.87,
                var_95=-0.0298,
                var_99=-0.0456,
                expected_shortfall_95=-0.0345,
                expected_shortfall_99=-0.0523,
                beta=1.023,
                alpha=0.0234,
                tracking_error=0.0987,
                strategy_name="RSI_MEAN_REVERSION",
                strategy_parameters={'period': 14, 'oversold': 30, 'overbought': 70},
                benchmark_name="HSI"
            )

            config = ReportConfig(
                report_type=ReportType.STRATEGY_ANALYSIS,
                language=lang,
                include_charts=False,  # Disable for demo speed
                include_executive_summary=True,
                include_risk_analysis=True,
                export_pdf=False,
                template_name="professional"
            )

            generator = ReportGenerator()
            files = generator.generate_report(report_data, config)

            if files:
                print(f"  ✅ {lang_name} generated successfully")
                for file_type, path in files.items():
                    size_kb = Path(path).stat().st_size / 1024
                    print(f"     📄 {file_type}: {size_kb:.1f} KB")

        print("\n✅ Multi-language demo completed!")

    except Exception as e:
        print(f"❌ Multi-language demo error: {e}")

def main():
    """主演示函數"""
    print("Enhanced Reporting System Demo")
    print("=" * 60)
    print("機構級量化交易報告系統演示")
    print("Institutional-Grade Trading Report System Demo")
    print("=" * 60)

    # Demo 1: Quick report generation
    demo_quick_report()

    # Demo 2: Executive summary
    demo_executive_summary()

    # Demo 3: Template system
    demo_template_system()

    # Demo 4: Multi-language support
    demo_multi_language()

    # Summary
    print("\n" + "="*60)
    print("Demo Summary")
    print("="*60)
    print("[✓] Professional HTML report generation")
    print("[✓] Interactive charts and visualizations")
    print("[✓] AI-powered executive summaries")
    print("[✓] Multi-language support (Chinese/English)")
    print("[✓] Customizable templates")
    print("[✓] Risk analysis integration")
    print("[✓] Export to multiple formats")

    print("\nKey Features Demonstrated:")
    print("   - Real-time chart generation")
    print("   - Intelligent executive summaries")
    print("   - Professional styling and layout")
    print("   - Bilingual support")
    print("   - Responsive design")
    print("   - Customizable templates")
    print("   - Comprehensive metrics")

    print("\nNext Steps:")
    print("   1. Integrate with your backtest results")
    print("   2. Customize templates for your needs")
    print("   3. Set up automated report generation")
    print("   4. Configure PDF export with weasyprint")
    print("   5. Add email distribution capabilities")

    print("\n" + "="*60)
    print("Demo completed successfully!")
    print("="*60)

if __name__ == "__main__":
    main()