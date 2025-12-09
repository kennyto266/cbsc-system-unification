#!/usr/bin/env python3
"""
簡化測試版本 - 移除emoji字符，確保系統可以正常運行
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Setup logging with UTF-8 encoding
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('interactive_trader.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class SimpleInteractiveTrader:
    """簡化版互動式量化交易系統"""

    def __init__(self):
        self.version = "1.0.0-simple"
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "user_preferences.json"
        self.gpu_available = False
        self.vectorbt_available = False

        print("\n" + "="*60)
        print("香港量化交易系統 - 簡化測試版")
        print(f"版本: {self.version}")
        print("="*60)

        # 基本檢查
        self._basic_dependency_check()

    def _basic_dependency_check(self):
        """基本依賴檢查"""
        try:
            import pandas as pd
            print("✓ pandas 可用")
        except ImportError:
            print("✗ pandas 不可用")

        try:
            import numpy as np
            print("✓ numpy 可用")
        except ImportError:
            print("✗ numpy 不可用")

        try:
            import requests
            print("✓ requests 可用")
        except ImportError:
            print("✗ requests 不可用")

        # 檢查可選依賴
        try:
            import vectorbt as vbt
            self.vectorbt_available = True
            print("✓ vectorbt 可用")
        except ImportError:
            print("- vectorbt 不可用 (可選)")

        try:
            import cupy as cp
            self.gpu_available = True
            print("✓ cupy GPU加速 可用")
        except ImportError:
            print("- cupy GPU加速 不可用 (可選)")

    def _get_colored_text(self, text, color='default'):
        """簡單的彩色文字"""
        color_codes = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'bold': '\033[1m',
            'reset': '\033[0m'
        }
        return f"{color_codes.get(color, '')}{text}{color_codes['reset']}"

    def show_menu(self):
        """顯示主菜單"""
        menu_items = [
            ("1", "股票數據分析"),
            ("2", "技術指標分析"),
            ("3", "政府數據查看"),
            ("4", "回測功能"),
            ("5", "系統配置"),
            ("6", "導出功能"),
            ("7", "幫助系統"),
            ("0", "退出系統")
        ]

        print(f"\n{self._get_colored_text('主菜單', 'bold')}")
        print("-" * 30)
        for key, description in menu_items:
            print(f"  {key}. {description}")

    def test_basic_functions(self):
        """測試基本功能"""
        print(f"\n{self._get_colored_text('基本功能測試', 'cyan')}")
        print("-" * 40)

        # 測試1: 創建配置目錄
        try:
            self.config_dir.mkdir(exist_ok=True)
            print("✓ 配置目錄創建成功")
        except Exception as e:
            print(f"✗ 配置目錄創建失敗: {e}")

        # 測試2: 創建示例配置
        try:
            if not self.config_file.exists():
                sample_config = {
                    "trading": {
                        "default_symbol": "0700.HK",
                        "favorite_symbols": ["0700.HK", "0941.HK"]
                    },
                    "test_timestamp": datetime.now().isoformat()
                }
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(sample_config, f, indent=2, ensure_ascii=False)
                print("✓ 示例配置文件創建成功")
            else:
                print("✓ 配置文件已存在")
        except Exception as e:
            print(f"✗ 配置文件操作失敗: {e}")

        # 測試3: 檢查系統信息
        try:
            import platform
            import multiprocessing

            print(f"✓ 系統信息: {platform.system()} {platform.release()}")
            print(f"✓ Python版本: {platform.python_version()}")
            print(f"✓ CPU核心數: {multiprocessing.cpu_count()}")

        except Exception as e:
            print(f"✗ 系統信息獲取失敗: {e}")

    def test_data_api(self):
        """測試數據API"""
        print(f"\n{self._get_colored_text('數據API測試', 'cyan')}")
        print("-" * 40)

        # 測試中央API
        try:
            import requests
            url = "http://18.180.162.113:9191/inst/getInst"
            params = {"symbol": "0700.hk", "duration": 30}

            print(f"正在測試中央API: {url}")
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'close' in data['data']:
                    dates = list(data['data']['close'].keys())
                    prices = list(data['data']['close'].values())
                    print(f"✓ 中央API測試成功")
                    print(f"  獲取數據: {len(prices)} 條記錄")
                    print(f"  時間範圍: {dates[0]} 到 {dates[-1]}")
                    print(f"  價格範圍: {min(prices):.2f} - {max(prices):.2f}")
                else:
                    print("✗ 數據格式錯誤")
            else:
                print(f"✗ HTTP錯誤: {response.status_code}")

        except requests.exceptions.Timeout:
            print("✗ 請求超時")
        except requests.exceptions.ConnectionError:
            print("✗ 連接錯誤")
        except Exception as e:
            print(f"✗ API測試失敗: {e}")

    def show_system_status(self):
        """顯示系統狀態"""
        print(f"\n{self._get_colored_text('系統狀態', 'bold')}")
        print("-" * 40)

        print(f"版本: {self.version}")
        print(f"GPU加速: {'可用' if self.gpu_available else '不可用'}")
        print(f"VectorBT: {'可用' if self.vectorbt_available else '不可用'}")

        # 顯示配置信息
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"配置文件: {self.config_file}")
                print(f"默認股票: {config.get('trading', {}).get('default_symbol', 'N/A')}")
            except:
                print("配置文件讀取失敗")

    def run_simple_demo(self):
        """運行簡單演示"""
        print(f"\n{self._get_colored_text('開始運行簡化演示...', 'yellow')}")

        self.test_basic_functions()
        self.test_data_api()
        self.show_system_status()

        print(f"\n{self._get_colored_text('演示完成!', 'green')}")

    def run_interactive(self):
        """交互式菜單"""
        while True:
            try:
                self.show_menu()
                choice = input(f"\n{self._get_colored_text('請選擇功能', 'cyan')} (0-7): ").strip()

                if choice == '0':
                    print(f"\n{self._get_colored_text('系統即將退出...', 'yellow')}")
                    break
                elif choice == '1':
                    self.test_data_api()
                elif choice == '5':
                    self.show_system_status()
                elif choice == '6':
                    print(f"\n{self._get_colored_text('導出功能測試', 'cyan')}")
                    print("此功能在完整版本中可用")
                elif choice == '7':
                    print(f"\n{self._get_colored_text('幫助信息', 'cyan')}")
                    print("這是一個簡化測試版本")
                    print("完整版本包含完整的幫助系統")
                else:
                    print(f"\n{self._get_colored_text('無效選擇，請重試', 'yellow')}")

                input(f"\n按Enter繼續...")

            except KeyboardInterrupt:
                print(f"\n\n{self._get_colored_text('用戶中斷，系統即將退出...', 'yellow')}")
                break
            except Exception as e:
                print(f"\n{self._get_colored_text(f'錯誤: {e}', 'red')}")
                break

def main():
    """主函數"""
    try:
        print("香港量化交易系統 - 簡化版啟動中...")

        trader = SimpleInteractiveTrader()

        # 自動運行演示模式
        print(f"\n自動運行簡單演示...")
        trader.run_simple_demo()

    except Exception as e:
        print(f"系統啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()