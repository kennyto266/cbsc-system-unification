#!/usr/bin/env python3
"""
Quick Start Strategy Development
快速啟動策略開發

一鍵運行策略開發環境和示例
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime, timedelta

def print_banner():
    """打印啟動橫幅"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    CBS-C 量化交易策略管理系統                                 ║
║    Quick Start Strategy Development                          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_requirements():
    """檢查系統要求"""
    print("\n🔍 檢查系統要求...")

    # 檢查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    print("✅ Python版本:", sys.version.split()[0])

    # 檢查必要的包
    required_packages = [
        'pandas', 'numpy', 'matplotlib', 'asyncio',
        'aiohttp', 'seaborn'
    ]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (需要安裝)")
            missing_packages.append(package)

    if missing_packages:
        print("\n請安裝缺失的包:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True

async def run_strategy_example():
    """運行策略示例"""
    print("\n🚀 運行策略開發示例...")
    print("="*60)

    try:
        # 運行策略開發示例
        from examples.strategy_development_example import main
        await main()

    except Exception as e:
        print(f"\n❌ 示例運行失敗: {str(e)}")
        print("\n請檢查:")
        print("1. 是否在正確的項目目錄中")
        print("2. 是否安裝了所有必要的依賴")
        print("3. 網絡連接是否正常（用於獲取數據）")

def show_next_steps():
    """顯示後續步驟"""
    print("\n" + "="*60)
    print("📋 後續開發步驟:")
    print("="*60)

    print("""
1. 創建自定義策略:
   - 繼承 QuantStrategyBase 類
   - 實現 initialize(), generate_signals(), calculate_position_size() 方法
   - 參考 examples/example_strategies.py

2. 運行回測:
   - 使用 BacktestEngine 進行歷史回測
   - 調整參數優化策略
   - 分析績效指標

3. 實盤交易:
   - 配置真實券商連接
   - 設置風險管理規則
   - 監控策略運行

4. 策略部署:
   - 使用 Docker 容器化部署
   - 設置監控和告警
   - 定期回顧和優化

📚 文檔和資源:
- API文檔: http://localhost:3004/docs
- 示例代碼: examples/strategy_development_example.py
- 策略模板: src/strategies/examples/example_strategies.py
- 數據接口: src/strategies/data_provider.py

💡 提示:
- 建議先用模擬數據測試策略
- 注意風險控制和倉位管理
- 定期回測驗證策略有效性
- 保持策略簡單易理解
    """)

def show_useful_commands():
    """顯示常用命令"""
    print("\n" + "="*60)
    print("🛠️ 常用命令:")
    print("="*60)

    print("""
# 啟動整個系統
python start_cbsc_system.py

# 運行策略示例
python quick_start_strategy.py

# 僅啟動後端服務
cd src/api && python -m uvicorn main:app --reload --port 3004

# 僅啟動前端
cd frontend && npm run dev

# 運行測試
python -m pytest tests/

# 查看API文檔
# 瀏覽器打開: http://localhost:3004/docs
    """)

async def main():
    """主函數"""
    print_banner()

    # 檢查要求
    if not check_requirements():
        sys.exit(1)

    print("\n✅ 系統檢查通過")

    # 詢問用戶意圖
    print("\n請選擇操作:")
    print("1. 運行策略開發示例")
    print("2. 查看幫助信息")
    print("3. 啟動完整系統")
    print("4. 退出")

    try:
        choice = input("\n請輸入選項 (1-4): ").strip()

        if choice == '1':
            await run_strategy_example()
        elif choice == '2':
            show_next_steps()
            show_useful_commands()
        elif choice == '3':
            print("\n啟動完整系統...")
            subprocess.run([sys.executable, "start_cbsc_system.py"])
        elif choice == '4':
            print("\n再見！")
        else:
            print("\n無效選項")

    except KeyboardInterrupt:
        print("\n\n操作已取消")
    except Exception as e:
        print(f"\n發生錯誤: {str(e)}")

if __name__ == "__main__":
    # 設置控制台編碼（Windows）
    if sys.platform == "win32":
        os.system('chcp 65001')

    asyncio.run(main())