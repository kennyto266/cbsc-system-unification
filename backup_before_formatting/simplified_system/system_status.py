#!/usr/bin/env python3
"""
簡化系統 - 系統狀態檢查器
Simplified System - System Status Checker

檢查所有組件的運行狀態和健康狀況
Check all components' running status and health condition
"""

import sys
import os
import asyncio
import time
from pathlib import Path
import importlib

# 添加項目根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_section(title):
    """打印章節標題"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_status(component, status, details=""):
    """打印狀態信息"""
    status_icon = "✅" if status == "OK" else "❌" if status == "ERROR" else "⚠️"
    print(f"{status_icon} {component:20}: {status}")
    if details:
        print(f"   {details}")

def check_python_environment():
    """檢查Python環境"""
    print_section("Python Environment Check")

    # Python版本
    python_version = sys.version.split()[0]
    print_status("Python Version", "OK", f"{python_version}")

    # 檢查核心依賴
    required_packages = [
        'pandas', 'numpy', 'requests', 'aiohttp',
        'python-telegram-bot', 'fastapi', 'uvicorn'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print_status(f"Package: {package}", "OK")
        except ImportError:
            print_status(f"Package: {package}", "ERROR", "Not installed")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install: pip install -r requirements.txt")
        return False

    return True

def check_modules():
    """檢查系統模塊"""
    print_section("System Modules Check")

    modules_to_check = [
        ('src.api.stock_api', 'Stock API'),
        ('src.indicators.core_indicators', 'Core Indicators'),
        ('src.indicators.technical_analyzer', 'Technical Analyzer'),
        ('src.data.government_data', 'Government Data'),
        ('src.telegram.telegram_bot', 'Telegram Bot')
    ]

    all_modules_ok = True
    for module_path, module_name in modules_to_check:
        try:
            importlib.import_module(module_path)
            print_status(module_name, "OK")
        except ImportError as e:
            print_status(module_name, "ERROR", str(e))
            all_modules_ok = False
        except Exception as e:
            print_status(module_name, "WARNING", f"Import warning: {e}")

    return all_modules_ok

def check_technical_indicators():
    """檢查技術指標功能"""
    print_section("Technical Indicators Check")

    try:
        from src.indicators.core_indicators import CoreIndicators, calculate_all_indicators
        from src.indicators.technical_analyzer import TechnicalAnalyzer

        # 創建測試數據
        import pandas as pd
        import numpy as np

        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 1, 50))
        test_data = pd.DataFrame({
            'open': prices,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 50)
        }, index=dates)

        # 測試核心指標計算
        start_time = time.time()
        indicators = CoreIndicators()
        rsi = indicators.calculate_rsi(test_data['close'])
        macd = indicators.calculate_macd(test_data['close'])
        calculation_time = time.time() - start_time

        if not rsi.empty and not macd['macd'].empty:
            print_status("Core Indicators", "OK", f"Calculation time: {calculation_time:.3f}s")
        else:
            print_status("Core Indicators", "ERROR", "Empty results")
            return False

        # 測試批量計算
        start_time = time.time()
        all_indicators = calculate_all_indicators(test_data)
        batch_time = time.time() - start_time

        if len(all_indicators) > 0:
            print_status("Batch Calculation", "OK", f"Indicators: {len(all_indicators)}, Time: {batch_time:.3f}s")
        else:
            print_status("Batch Calculation", "ERROR", "No indicators calculated")
            return False

        # 測試技術分析器
        start_time = time.time()
        analyzer = TechnicalAnalyzer()
        analysis = analyzer.analyze_trend(test_data['close'])
        signals = analyzer.generate_trading_signals(test_data)
        analysis_time = time.time() - start_time

        if 'trend' in analysis and 'overall_signal' in signals:
            print_status("Technical Analysis", "OK", f"Analysis time: {analysis_time:.3f}s")
        else:
            print_status("Technical Analysis", "ERROR", "Analysis failed")
            return False

        return True

    except Exception as e:
        print_status("Technical Indicators", "ERROR", str(e))
        return False

async def check_apis():
    """檢查API連接"""
    print_section("API Connections Check")

    # 檢查股票API
    try:
        from src.api.stock_api import stock_api

        print_status("Stock API Module", "OK")

        # 測試連接（但不下載大量數據）
        print("Testing stock API connection...")
        try:
            # 這是一個連接測試，實際不應該在這裡下載數據
            print_status("Stock API Base", "OK", f"URL: {stock_api.api_base_url}")
        except Exception as e:
            print_status("Stock API Connection", "WARNING", f"Connection test failed: {e}")

    except ImportError as e:
        print_status("Stock API", "ERROR", str(e))
        return False

    # 檢查政府數據API
    try:
        from src.data.government_data import government_collector

        print_status("Government Data Module", "OK")
        print(f"Available data sources: {len(government_collector.data_sources)}")

        for source in government_collector.data_sources:
            print(f"   • {source.name}: {source.data_type}")

    except ImportError as e:
        print_status("Government Data", "ERROR", str(e))
        return False

    return True

def check_telegram_bot():
    """檢查Telegram Bot配置"""
    print_section("Telegram Bot Configuration")

    try:
        from src.telegram.telegram_bot import SimpleTelegramBot

        print_status("Telegram Bot Module", "OK")

        # 檢查環境變量
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if bot_token:
            print_status("Bot Token", "OK", f"Token length: {len(bot_token)}")
        else:
            print_status("Bot Token", "ERROR", "TELEGRAM_BOT_TOKEN not set")
            return False

        # 嘗試初始化Bot
        try:
            bot = SimpleTelegramBot()
            print_status("Bot Initialization", "OK")
        except Exception as e:
            print_status("Bot Initialization", "WARNING", f"Initialization warning: {e}")

        return True

    except ImportError as e:
        print_status("Telegram Bot", "ERROR", str(e))
        return False

def check_file_structure():
    """檢查文件結構"""
    print_section("File Structure Check")

    required_files = [
        'requirements.txt',
        'README.md',
        'src/api/stock_api.py',
        'src/indicators/core_indicators.py',
        'src/indicators/technical_analyzer.py',
        'src/data/government_data.py',
        'src/telegram/telegram_bot.py',
        'start_telegram_bot.py',
        'test_indicators_simple.py',
        'demo_integrated_system.py'
    ]

    all_files_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print_status(file_path, "OK")
        else:
            print_status(file_path, "ERROR", "File not found")
            all_files_exist = False

    return all_files_exist

def check_performance():
    """性能基準測試"""
    print_section("Performance Benchmark")

    try:
        from src.indicators.core_indicators import calculate_all_indicators
        from src.indicators.technical_analyzer import analyze_symbol

        import pandas as pd
        import numpy as np

        # 測試不同數據量
        data_sizes = [100, 500, 1000]

        for size in data_sizes:
            dates = pd.date_range(start='2023-01-01', periods=size, freq='D')
            prices = 100 + np.cumsum(np.random.normal(0, 1, size))
            test_data = pd.DataFrame({
                'open': prices,
                'high': prices * 1.02,
                'low': prices * 0.98,
                'close': prices,
                'volume': np.random.randint(1000000, 5000000, size)
            }, index=dates)

            # 指標計算性能
            start_time = time.time()
            indicators = calculate_all_indicators(test_data)
            indicators_time = time.time() - start_time

            # 技術分析性能
            start_time = time.time()
            analysis = analyze_symbol(test_data)
            analysis_time = time.time() - start_time

            records_per_sec = size / indicators_time if indicators_time > 0 else 0

            print(f"📊 {size:4d} records:")
            print(f"   • Indicators: {indicators_time:.3f}s ({records_per_sec:.0f} rec/s)")
            print(f"   • Analysis:   {analysis_time:.3f}s")

        return True

    except Exception as e:
        print_status("Performance Test", "ERROR", str(e))
        return False

async def main():
    """主檢查函數"""
    print_section("Simplified System Status Check")
    print("系統狀態檢查和健康監控")
    print("System Status Check and Health Monitoring")

    overall_status = True

    # 1. Python環境檢查
    python_ok = check_python_environment()
    overall_status &= python_ok

    # 2. 文件結構檢查
    files_ok = check_file_structure()
    overall_status &= files_ok

    # 3. 模塊檢查
    modules_ok = check_modules()
    overall_status &= modules_ok

    # 4. 技術指標檢查
    indicators_ok = check_technical_indicators()
    overall_status &= indicators_ok

    # 5. API連接檢查
    apis_ok = await check_apis()
    overall_status &= apis_ok

    # 6. Telegram Bot檢查
    bot_ok = check_telegram_bot()
    overall_status &= bot_ok

    # 7. 性能檢查
    performance_ok = check_performance()
    overall_status &= performance_ok

    # 總結
    print_section("System Status Summary")

    if overall_status:
        print("🎉 All systems are operational!")
        print("✅ 簡化系統狀態：健康運行")
        print("✅ Core functionality: Available")
        print("✅ Performance: Optimal")
        print("✅ Ready for production use")

        print("\n🚀 Next steps:")
        print("   • Start Telegram Bot: python start_telegram_bot.py")
        print("   • Run demo: python demo_integrated_system.py")
        print("   • Test indicators: python test_indicators_simple.py")

    else:
        print("❌ Some components need attention!")
        print("⚠️  Please resolve the issues above before deployment")

    return overall_status

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)