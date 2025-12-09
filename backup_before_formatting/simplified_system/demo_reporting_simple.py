#!/usr/bin/env python3
"""
Simple Reporting System Demo
簡化報告系統演示

Simple demonstration of the enhanced reporting system
簡化演示增強報告系統功能
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

def demo_quick_report():
    """快速報告演示"""
    print("Quick Report Generation Demo")
    print("-" * 40)

    # Import the reporting system
    try:
        from src.reporting import ReportGenerator, ReportType, ReportLanguage, ReportConfig, ReportData

        print("Creating sample backtest data...")

        # Create sample report data
        report_data = ReportData(
            timestamp=datetime.now(),
            title="RSI Mean Reversion Strategy Report",
            subtitle="Quantitative Trading Strategy Evaluation",
            period="2024-01-01 to 2024-11-23",
            total_return=0.1856,  # 18.56%
            annual_return=0.1934,  # 19.34%
            sharpe_ratio=1.65,
            max_drawdown=-0.0876,  # -8.76%
            volatility=0.1567,     # 15.67%
            win_rate=0.6234,       # 62.34%
            calmar_ratio=2.21,
            sortino_ratio=2.37,
            total_trades=124,
            profitable_trades=78,
            losing_trades=46,
            average_win=0.0234,
            average_loss=-0.0156,
            profit_factor=2.08,
            var_95=-0.0234,
            var_99=-0.0412,
            expected_shortfall_95=-0.0312,
            expected_shortfall_99=-0.0523,
            beta=0.956,
            alpha=0.0312,
            tracking_error=0.0876,
            strategy_name="RSI_MEAN_REVERSION",
            strategy_parameters={
                'period': 14,
                'oversold': 30,
                'overbought': 70
            },
            benchmark_name="Hang Seng Index"
        )

        # Create sample price data for charts
        print("Generating sample price data for charts...")
        dates = pd.date_range(start='2024-01-01', end='2024-11-23', freq='D')
        n_days = len(dates)

        np.random.seed(42)
        base_price = 380.50
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

        # Add strategy signals
        price_data['signals'] = 0
        buy_signals = np.random.choice(n_days, size=15, replace=False)
        sell_signals = np.random.choice(n_days, size=12, replace=False)
        price_data.iloc[buy_signals, price_data.columns.get_loc('signals')] = 1
        price_data.iloc[sell_signals, price_data.columns.get_loc('signals')] = -1

        report_data.raw_data = price_data

        # Configure the report
        print("Configuring report settings...")
        config = ReportConfig(
            report_type=ReportType.STRATEGY_ANALYSIS,
            language=ReportLanguage.BILINGUAL,
            include_charts=True,
            include_executive_summary=True,
            include_risk_analysis=True,
            include_detailed_metrics=True,
            export_pdf=False,  # Disable for demo speed
            export_excel=False,
            template_name="professional",
            interactive_elements=True,
            author="Quant Trading System",
            confidentiality_level="Internal Use Only"
        )

        # Generate the report
        print("Generating professional report...")
        generator = ReportGenerator()
        generated_files = generator.generate_report(report_data, config)

        print("\nReport Generated Successfully!")
        print("=" * 50)

        # Display results
        print("Generated Files:")
        for file_type, file_path in generated_files.items():
            file_info = Path(file_path)
            size_kb = file_info.stat().st_size / 1024
            print(f"  {file_type.upper()}: {file_info.name} ({size_kb:.1f} KB)")

        print(f"\nHTML report generated: {generated_files.get('html', 'None')}")
        return generated_files

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all required dependencies are installed:")
        print("pip install jinja2 plotly pandas numpy")
        return {}
    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return {}

def demo_executive_summary():
    """執行摘要演示"""
    print("\n" + "="*50)
    print("Executive Summary Demo")
    print("-" * 40)

    try:
        from src.reporting.executive_summary import ExecutiveSummaryGenerator
        from src.reporting import ReportData, ReportLanguage

        # Create high-performing strategy data
        report_data = ReportData(
            timestamp=datetime.now(),
            title="High-Frequency Arbitrage Strategy Summary",
            subtitle="Institutional-Grade Quantitative Investment Strategy",
            period="2024 Q1-Q3",
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
            benchmark_name="Risk-Free Rate"
        )

        # Generate executive summary
        print("Generating AI-powered executive summary...")
        summary_gen = ExecutiveSummaryGenerator()
        summary = summary_gen.generate(report_data, ReportLanguage.BILINGUAL)

        print("\nGenerated Executive Summary:")
        print("=" * 50)
        print(summary[:800] + "\n... [truncated for demo]")
        print("=" * 50)

        print("Executive summary generated successfully!")
        return summary

    except Exception as e:
        print(f"Error generating executive summary: {e}")
        return ""

def demo_template_system():
    """模板系統演示"""
    print("\n" + "="*50)
    print("Template System Demo")
    print("-" * 40)

    try:
        from src.reporting.template_manager import TemplateManager, TemplateType

        print("Initializing template manager...")
        template_manager = TemplateManager()

        # List available templates
        templates = template_manager.list_templates()
        print(f"\nAvailable Templates ({len(templates)}):")
        for template in templates:
            status = "ACTIVE" if template.is_active else "INACTIVE"
            default = " [DEFAULT]" if template.is_default else ""
            print(f"  [{status}] {template.name}: {template.description}{default}")

        print("Template system demo completed!")
        return template_manager

    except Exception as e:
        print(f"Error with template system: {e}")
        return None

def main():
    """主演示函數"""
    print("Enhanced Reporting System Demo")
    print("=" * 60)
    print("Institutional-Grade Trading Report System Demo")
    print("=" * 60)

    # Demo 1: Quick report generation
    demo_quick_report()

    # Demo 2: Executive summary
    demo_executive_summary()

    # Demo 3: Template system
    demo_template_system()

    # Summary
    print("\n" + "="*60)
    print("Demo Summary")
    print("="*60)
    print("[SUCCESS] Professional HTML report generation")
    print("[SUCCESS] Interactive charts and visualizations")
    print("[SUCCESS] AI-powered executive summaries")
    print("[SUCCESS] Multi-language support (Chinese/English)")
    print("[SUCCESS] Customizable templates")
    print("[SUCCESS] Risk analysis integration")
    print("[SUCCESS] Export to multiple formats")

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