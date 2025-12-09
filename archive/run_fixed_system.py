#!/usr/bin/env python3
"""
修復版本 - 解決編碼問題的完整系統運行器
"""

import sys
import os
import codecs
import locale

# 設置UTF-8編碼
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 備用方案
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)

# 設置環境變量
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("正在啟動修復版的互動式量化交易系統...")
print("系統編碼已設置為UTF-8")

try:
    # 設置默認編碼
    if hasattr(locale, 'setlocale'):
        try:
            locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except:
                pass

    # 清理模塊緩存
    modules_to_reload = [
        'interactive_quantitative_trader',
        'src.core.config',
        'src.utils.dependency_manager'
    ]

    for module in modules_to_reload:
        if module in sys.modules:
            del sys.modules[module]

    print("正在導入主系統...")
    from interactive_quantitative_trader import InteractiveQuantitativeTrader

    print("正在初始化系統...")
    trader = InteractiveQuantitativeTrader()

    print("正在啟動互動式界面...")
    trader.run()

except Exception as e:
    print(f"系統啟動失敗: {e}")
    import traceback
    traceback.print_exc()

    # 啟動簡化版作為備用
    print("\n正在啟動簡化版作為備用...")
    from simple_test_trader import SimpleInteractiveTrader
    trader = SimpleInteractiveTrader()
    trader.run_simple_demo()