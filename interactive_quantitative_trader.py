#!/usr/bin/env python3
"""
香港量化交易系統 - 互動式CLI界面
優化版本，統一入口點，便於日常使用
"""

import sys
import os
import time
import json
import logging
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Import secure parameter parser
try:
    from src.security.secure_parameter_parser import parse_parameter_ranges_safe
    SECURE_PARSER_AVAILABLE = True
except ImportError:
    SECURE_PARSER_AVAILABLE = False
    logger.warning("Secure parameter parser not available, using fallback methods")

# Import secure input validator
try:
    from src.security.secure_input_validator import get_input_validator, safe_input_int, safe_input_float
    INPUT_VALIDATOR_AVAILABLE = True
except ImportError:
    INPUT_VALIDATOR_AVAILABLE = False
    logger.warning("Secure input validator not available, using fallback methods")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('interactive_trader.log')
    ]
)
logger = logging.getLogger(__name__)

class InteractiveQuantitativeTrader:
    """互動式量化交易系統主類"""

    def __init__(self):
        self.version = "1.0.0"
        self.config_dir = Path("config")
        self.config_file = self.config_dir / "user_preferences.json"
        self.gpu_available = False
        self.vectorbt_available = False
        self.data_cache = {}

        # 初始化系統配置
        self._init_config()
        self._check_dependencies()

    def _init_config(self):
        """初始化配置系統"""
        try:
            # 導入新的配置管理器
            sys.path.insert(0, str(Path(__file__).parent / "config"))
            from config_manager import ConfigManager
            from config_menu import ConfigMenu

            # 初始化配置管理器
            self.config_manager = ConfigManager(self.config_dir)
            self.config_menu = ConfigMenu(self.config_manager)

            # 為了向後兼容，保留config屬性
            self.config = self.config_manager.config

            logger.info("✅ 配置管理系統初始化成功")

        except Exception as e:
            logger.error(f"配置管理系統初始化失敗，使用緊急配置: {e}")
            # 緊急情況下使用簡單配置
            self.config = {
                "default_symbol": "0700.HK",
                "default_duration": 252,
                "output_format": "table",
                "auto_save_results": True,
                "chart_type": "ascii",
                "theme": "dark",
                "language": "zh-CN"
            }
            self.config_manager = None
            self.config_menu = None

    def _check_dependencies(self):
        """檢查系統依賴"""
        try:
            # 導入新的依賴管理器
            import os
            current_dir = Path(__file__).parent
            utils_path = current_dir / "src" / "utils"
            if str(utils_path) not in sys.path:
                sys.path.insert(0, str(utils_path))

            try:
                from dependency_manager import DependencyManager
                from dependency_menu import DependencyMenu
            except ImportError:
                # 嘗試絕對導入
                from src.utils.dependency_manager import DependencyManager
                from src.utils.dependency_menu import DependencyMenu

            # 初始化依賴管理器
            self.dependency_manager = DependencyManager()
            self.dependency_menu = DependencyMenu(self.dependency_manager)

            # 設置依賴狀態
            self.gpu_available = self.dependency_manager.gpu_available
            self.vectorbt_available = self.dependency_manager.vectorbt_available
            self.tabulate_available = self.dependency_manager.dependencies['tabulate']['available']
            self.pandas_available = self.dependency_manager.dependencies['pandas']['available']

            # 檢查simplified_system模塊
            try:
                sys.path.insert(0, str(Path(__file__).parent / "simplified_system"))
                from src.api.stock_api import get_hk_stock_data
                from src.indicators.core_indicators import CoreIndicators
                logger.info("Simplified System模塊檢查通過")
                self.simplified_system_available = True
            except Exception as e:
                logger.error(f"Simplified System模塊不可用: {e}")
                self.simplified_system_available = False

            # 顯示依賴摘要
            status = self.dependency_manager.get_dependency_status()
            if status['all_required_available']:
                logger.info("所有必需依賴已滿足")
            else:
                missing = self.dependency_manager.get_missing_dependencies()
                missing_names = [dep['name'] for dep in missing]
                logger.warning(f"缺失必需依賴: {', '.join(missing_names)}")

            if self.gpu_available:
                logger.info("GPU加速可用")
            if self.vectorbt_available:
                logger.info("VectorBT回測引擎可用")

        except Exception as e:
            logger.error(f"依賴管理系統初始化失敗，使用緊急檢查: {e}")
            # 緊急情況下使用簡單依賴檢查
            self._emergency_dependency_check()

    def _emergency_dependency_check(self):
        """緊急依賴檢查"""
        try:
            # 檢查simplified_system模塊
            sys.path.insert(0, str(Path(__file__).parent / "simplified_system"))
            from src.api.stock_api import get_hk_stock_data
            from src.indicators.core_indicators import CoreIndicators
            self.simplified_system_available = True
        except Exception as e:
            self.simplified_system_available = False
            logger.error(f"Emergency check - Simplified System不可用: {e}")

        try:
            import cupy as cp
            self.gpu_available = True
        except ImportError:
            self.gpu_available = False

        try:
            import vectorbt as vbt
            self.vectorbt_available = True
        except ImportError:
            self.vectorbt_available = False

        try:
            from tabulate import tabulate
            self.tabulate_available = True
        except ImportError:
            self.tabulate_available = False

        try:
            import pandas as pd
            self.pandas_available = True
        except ImportError:
            self.pandas_available = False

        # 設置為None表示依賴管理系統不可用
        self.dependency_manager = None
        self.dependency_menu = None

    def _get_colored_text(self, text: str, color: str = 'white') -> str:
        """獲取彩色文本"""
        color_codes = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'reset': '\033[0m'
        }
        return f"{color_codes.get(color, '')}{text}{color_codes['reset']}"

    def _print_header(self):
        """打印系統標題"""
        print("\n" + "="*60)
        print(self._get_colored_text("香港量化交易系統 - 互動式CLI界面", 'cyan'))
        print(self._get_colored_text(f"版本: {self.version}", 'yellow'))
        print("="*60)

        # 顯示系統狀態
        status_items = []
        if self.simplified_system_available:
            status_items.append(self._get_colored_text("✅ 簡化系統", 'green'))
        else:
            status_items.append(self._get_colored_text("❌ 簡化系統", 'red'))

        if self.gpu_available:
            status_items.append(self._get_colored_text("✅ GPU加速", 'green'))
        else:
            status_items.append(self._get_colored_text("⚠️  CPU模式", 'yellow'))

        if self.vectorbt_available:
            status_items.append(self._get_colored_text("✅ 回測引擎", 'green'))
        else:
            status_items.append(self._get_colored_text("⚠️  回測受限", 'yellow'))

        print(f"系統狀態: {' | '.join(status_items)}")
        print("="*60)

    def _print_main_menu(self):
        """顯示主菜單"""
        menu_items = [
            ("1", "📊 股票數據獲取"),
            ("2", "📈 技術指標分析"),
            ("3", "🔄 回測策略優化"),
            ("4", "🏛️ 政府數據查看"),
            ("5", "⚙️  系統狀態檢查"),
            ("6", "🛠️  配置管理"),
            ("7", "📦 依賴管理"),
            ("8", "🖥️  GPU加速支持"),
            ("0", "🚪 退出系統")
        ]

        print(f"{self._get_colored_text('主菜單:', 'bold')}")
        for key, description in menu_items:
            print(f"  {key}. {description}")

        # 使用新的配置管理器或向後兼容的配置
        default_symbol = self.config_manager.get('trading.default_symbol') if self.config_manager else self.config.get('default_symbol')
        default_duration = self.config_manager.get('trading.default_duration') if self.config_manager else self.config.get('default_duration')

        if default_symbol:
            print(f"\n{self._get_colored_text('默認股票:', 'yellow')} {default_symbol}")
        if default_duration:
            print(f"{self._get_colored_text('默認時長:', 'yellow')} {default_duration}天")
        print()

    def _get_user_input(self, prompt: str, valid_options: List[str] = None) -> str:
        """獲取用戶輸入並驗證"""
        while True:
            try:
                choice = input(f"{self._get_colored_text('→', 'cyan')} {prompt}: ").strip()

                if valid_options and choice not in valid_options:
                    print(f"{self._get_colored_text('⚠️  無效選擇，請重新輸入', 'yellow')}")
                    continue

                if choice == '':
                    print(f"{self._get_colored_text('⚠️  輸入不能為空，請重新輸入', 'yellow')}")
                    continue

                return choice
            except KeyboardInterrupt:
                print(f"\n{self._get_colored_text('👋 用戶中斷操作', 'yellow')}")
                return '0'  # 返回主菜單
            except EOFError:
                print(f"\n{self._get_colored_text('👋 輸入結束', 'yellow')}")
                return '0'  # 返回主菜單

    def _show_help(self):
        """顯示幫助信息"""
        help_text = f"""
{self._get_colored_text('📖 系統幫助', 'bold')}

{self._get_colored_text('基本操作:', 'yellow')}
• 使用數字鍵選擇菜單項目
• 輸入 '0' 返回主菜單
• 使用 'Ctrl+C' 中斷當前操作
• 輸入 'q' 或 'quit' 退出系統

{self.__colored_text('快捷操作:', 'yellow')}
• 直接輸入股票代碼快速查詢數據
• 輸入 'h' 或 'help' 顯示此幫助
• 輸入 's' 或 'settings' 進入設置

{self._get_coloredored_text('配置文件:', 'yellow')}
• 位置: {self.config_file}
• 支持自定義默認股票和參數
• 可重置為默認配置
"""
        print(help_text)

    def stock_data_menu(self):
        """增強的股票數據獲取菜單 - Phase 2 Task 2.1"""
        print(f"\n{self._get_colored_text('📊 股票數據獲取 - 增強版', 'bold')}")
        print("-" * 40)

        while True:
            print(f"\n{self._get_colored_text('股票數據操作選項:', 'yellow')}")
            print("1. 🔍 查詢單隻股票數據")
            print("2. 📋 批量查詢多隻股票")
            print("3. ⭐ 查看收藏股票列表")
            print("4. 📈 實時價格查詢")
            print("5. 📊 數據質量驗證")
            print("0. 🚪 返回主菜單")

            choice = self._get_user_input("請選擇操作 (0-5)", ['0', '1', '2', '3', '4', '5'])

            if choice == '0':
                break
            elif choice == '1':
                self._single_stock_query()
            elif choice == '2':
                self._batch_stock_query()
            elif choice == '3':
                self._show_favorite_stocks()
            elif choice == '4':
                self._real_time_price_query()
            elif choice == '5':
                self._data_quality_validation()

        input(f"\n{self._get_colored_text('按Enter繼續...', 'cyan')}")

    def _validate_stock_symbol(self, symbol: str) -> bool:
        """驗證股票代碼格式"""
        # 香港股票格式驗證 (例如: 0700.HK, 0941.HK)
        import re
        hk_pattern = r'^[0-9]{4}\.HK$'
        return bool(re.match(hk_pattern, symbol.upper()))

    def _format_currency(self, amount) -> str:
        """格式化貨幣顯示"""
        try:
            if isinstance(amount, (int, float)):
                return f"{amount:,.2f} HKD"
            else:
                return f"{amount} HKD"
        except:
            return f"{amount} HKD"

    def _format_percentage(self, value: float) -> str:
        """格式化百分比顯示"""
        try:
            return f"{value:+.2f}%"
        except:
            return "N/A"

    def _single_stock_query(self):
        """單隻股票查詢"""
        print(f"\n{self._get_colored_text('🔍 單隻股票數據查詢', 'bold')}")
        print("-" * 30)

        try:
            # 獲取股票代碼並驗證
            default_symbol = self.config_manager.get('trading.default_symbol') if self.config_manager else self.config.get('default_symbol', '0700.HK')
            symbol = self._get_user_input(f"請輸入股票代碼 (默認: {default_symbol})", None)

            if symbol.lower() in ['q', 'quit', '0']:
                return

            if not symbol:
                symbol = default_symbol

            # 驗證股票代碼格式
            if not self._validate_stock_symbol(symbol):
                print(f"{self._get_colored_text('❌ 股票代碼格式無效，請使用格式如 0700.HK', 'red')}")
                print(f"{self._get_colored_text('💡 常見港股代碼:', 'yellow')}")
                print("   0700.HK - 騰訊控股")
                print("   0941.HK - 中國移動")
                print("   1398.HK - 工商銀行")
                print("   0388.HK - 香港交易所")
                return

            # 獲取時間範圍
            duration_options = {
                '1': 30,    # 1個月
                '2': 90,    # 3個月
                '3': 180,   # 6個月
                '4': 252,   # 1年
                '5': 504,   # 2年
                '6': 1095   # 3年
            }

            print(f"\n{self._get_colored_text('📅 時間範圍選擇:', 'yellow')}")
            print("1. 最近1個月 (30天)")
            print("2. 最近3個月 (90天)")
            print("3. 最近6個月 (180天)")
            print("4. 最近1年 (252天) - 默認")
            print("5. 最近2年 (504天)")
            print("6. 最近3年 (1095天)")
            print("7. 自定義天數")

            duration_choice = self._get_user_input("請選擇時間範圍 (1-7)", ['1', '2', '3', '4', '5', '6', '7'])

            if duration_choice == '7':
                duration_input = self._get_user_input("請輸入自定義天數 (1-3650)", None)
                try:
                    # Use secure input validation
                    if INPUT_VALIDATOR_AVAILABLE:
                        duration = safe_input_int("請輸入自定義天數 (1-3650): ", min_val=1, max_val=3650)
                    else:
                        # Fallback validation
                        duration = int(duration_input)
                        if duration < 1 or duration > 3650:
                            raise ValueError("天數必須在1-3650之間")
                except Exception as e:
                    print(f"{self._get_colored_text('❌ 無效的天數，使用默認值252天', 'yellow')}")
                    duration = 252
            else:
                duration = duration_options.get(duration_choice, 252)

            print(f"\n{self._get_colored_text(f'🚀 正在獲取 {symbol} 數據，時間範圍: {duration}天...', 'yellow')}")

            if self.simplified_system_available:
                from simplified_system.src.api.stock_api import get_hk_stock_data, get_stock_prices_dataframe
                import pandas as pd

                # 顯示進度條
                print("   " + "█" * 0 + "░" * 20 + " 0%", end="\r")
                for i in range(1, 21):
                    time.sleep(0.05)
                    progress = "█" * i + "░" * (20 - i)
                    percent = (i / 20) * 100
                    print(f"   {progress} {percent:.0f}%", end="\r")
                    sys.stdout.flush()

                # 獲取原始數據和DataFrame
                raw_data = get_hk_stock_data(symbol, duration)
                df = get_stock_prices_dataframe(symbol, duration)

                print("   " + "█" * 20 + " 100% " + self._get_colored_text("✓", 'green'))

                if raw_data and df is not None and len(df) > 0:
                    print(f"\n{self._get_colored_text('✅ 數據獲取成功!', 'green')}")

                    # 顯示詳細統計信息
                    self._display_stock_statistics(symbol, df, raw_data)

                    # 顯示數據表格 (如果有tabulate)
                    if self.tabulate_available:
                        self._display_stock_table(df)

                    # 詢問後續操作
                    self._stock_data_followup_options(symbol, df)

                else:
                    print(f"\n{self._get_colored_text('❌ 未獲取到有效數據', 'red')}")
                    print(f"{self._get_colored_text('可能原因: 股票代碼不存在或網絡連接問題', 'yellow')}")
            else:
                print(f"{self._get_colored_text('❌ Simplified System不可用', 'red')}")

        except Exception as e:
            logger.error(f"股票查詢錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 查詢錯誤: {e}', 'red')}")

    def _display_stock_statistics(self, symbol: str, df, raw_data):
        """顯示股票統計信息"""
        print(f"\n{self._get_colored_text('📊 股票統計信息', 'bold')}")
        print("=" * 50)

        # 基本信息表格
        basic_info = [
            ("股票代碼", symbol),
            ("數據記錄數", f"{len(df)} 條"),
            ("數據時間範圍", f"{df.index[0].strftime('%Y-%m-%d')} 至 {df.index[-1].strftime('%Y-%m-%d')}"),
            ("交易天數", f"{len(df)} 天")
        ]

        # 價格統計
        if 'price' in df.columns:
            prices = df['price']
            latest_price = prices.iloc[-1]
            min_price = prices.min()
            max_price = prices.max()
            avg_price = prices.mean()

            # 計算漲跌幅
            if len(prices) > 1:
                price_change = latest_price - prices.iloc[-2]
                price_change_pct = (price_change / prices.iloc[-2]) * 100
            else:
                price_change = 0
                price_change_pct = 0

            price_stats = [
                ("最新價格", self._format_currency(latest_price)),
                ("最高價格", self._format_currency(max_price)),
                ("最低價格", self._format_currency(min_price)),
                ("平均價格", self._format_currency(avg_price)),
                ("日漲跌", self._format_currency(price_change)),
                ("日漲跌幅", self._format_percentage(price_change_pct))
            ]

            # 計算年度統計
            if len(df) >= 252:  # 有1年以上數據
                year_high = prices.max()
                year_low = prices.min()
                year_range = year_high - year_low
                volatility = prices.pct_change().std() * (252 ** 0.5) * 100  # 年化波動率

                advanced_stats = [
                    ("年度最高", self._format_currency(year_high)),
                    ("年度最低", self._format_currency(year_low)),
                    ("年度震幅", self._format_currency(year_range)),
                    ("年化波動率", f"{volatility:.2f}%")
                ]
            else:
                advanced_stats = [("數據不足", "需要至少1年數據")]

        # 顯示表格
        if self.tabulate_available:
            from tabulate import tabulate

            print(f"\n{self._get_colored_text('📋 基本信息', 'cyan')}")
            print(tabulate(basic_info, tablefmt="grid"))

            print(f"\n{self._get_colored_text('💰 價格統計', 'cyan')}")
            print(tabulate(price_stats, tablefmt="grid"))

            if len(df) >= 252:
                print(f"\n{self._get_colored_text('📈 高級統計', 'cyan')}")
                print(tabulate(advanced_stats, tablefmt="grid"))
        else:
            print(f"\n{self._get_colored_text('📋 基本信息', 'cyan')}")
            for label, value in basic_info:
                print(f"  {label}: {value}")

            print(f"\n{self._get_colored_text('💰 價格統計', 'cyan')}")
            for label, value in price_stats:
                print(f"  {label}: {value}")

    def _display_stock_table(self, df):
        """顯示股票數據表格"""
        print(f"\n{self._get_colored_text('📄 最近5個交易日數據', 'cyan')}")

        if self.tabulate_available:
            from tabulate import tabulate

            # 準備表格數據 (最近5天)
            recent_data = df.tail(5).copy()
            recent_data.reset_index(inplace=True)

            # 重命名列
            recent_data.columns = ['日期', '收盤價']
            recent_data['日期'] = recent_data['日期'].dt.strftime('%Y-%m-%d')
            recent_data['收盤價'] = recent_data['收盤價'].apply(lambda x: f"{x:.2f}")

            print(tabulate(recent_data.to_dict('records'), headers="keys", tablefmt="grid", showindex=False))
        else:
            # 簡單文本顯示
            for i, (date, row) in enumerate(df.tail(5).iterrows()):
                print(f"  {date.strftime('%Y-%m-%d')}: {row['price']:.2f} HKD")

    def _stock_data_followup_options(self, symbol: str, df):
        """股票數據後續操作選項"""
        print(f"\n{self._get_colored_text('🔧 後續操作選項:', 'yellow')}")
        print("1. 📈 技術指標分析")
        print("2. 💾 導出數據到文件")
        print("3. ⭐ 添加到收藏列表")
        print("4. 🔄 查詢其他時間範圍")
        print("5. 🚪 返回")

        choice = self._get_user_input("請選擇操作 (1-5)", ['1', '2', '3', '4', '5'])

        if choice == '1':
            self.technical_indicators_menu(symbol, df.to_dict())
        elif choice == '2':
            self._export_stock_data(symbol, df)
        elif choice == '3':
            self._add_to_favorites(symbol)
        elif choice == '4':
            self._single_stock_query()  # 遞歸調用

    def _export_stock_data(self, symbol: str, df):
        """導出股票數據"""
        try:
            import pandas as pd
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{timestamp}.csv"
            filepath = Path("results") / filename
            filepath.parent.mkdir(exist_ok=True)

            df.to_csv(filepath, encoding='utf-8-sig')
            print(f"{self._get_colored_text('✅ 數據已導出:', 'green')} {filepath}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 導出失敗: {e}', 'red')}")

    def _add_to_favorites(self, symbol: str):
        """添加到收藏列表"""
        try:
            favorites = self.config_manager.get('trading.favorite_symbols', [])

            if symbol not in favorites:
                favorites.append(symbol)
                self.config_manager.set('trading.favorite_symbols', favorites)
                self.config_manager.save_config()
                print(f"{self._get_colored_text(f'✅ {symbol} 已添加到收藏列表', 'green')}")
            else:
                print(f"{self._get_colored_text(f'⚠️ {symbol} 已在收藏列表中', 'yellow')}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 添加收藏失敗: {e}', 'red')}")

    def _batch_stock_query(self):
        """批量股票查詢"""
        print(f"\n{self._get_colored_text('📋 批量股票查詢', 'bold')}")
        print("-" * 30)

        try:
            # 獲取股票列表
            favorites = self.config_manager.get('trading.favorite_symbols', ['0700.HK', '0941.HK', '1398.HK'])
            print(f"{self._get_colored_text('當前收藏股票:', 'yellow')} {', '.join(favorites)}")

            use_favorites = self._get_user_input("使用收藏列表? (y/n)", ['y', 'n', 'Y', 'N'])

            if use_favorites.lower() in ['y', 'yes']:
                symbols = favorites
            else:
                symbols_input = self._get_user_input("請輸入股票代碼列表 (逗號分隔)", None)
                symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]

                # 驗證每個股票代碼
                valid_symbols = []
                for symbol in symbols:
                    if self._validate_stock_symbol(symbol):
                        valid_symbols.append(symbol)
                    else:
                        print(f"{self._get_colored_text(f'⚠️ 跳過無效代碼: {symbol}', 'yellow')}")
                symbols = valid_symbols

            if not symbols:
                print(f"{self._get_colored_text('❌ 沒有有效的股票代碼', 'red')}")
                return

            print(f"{self._get_colored_text(f'🚀 正在批量查詢 {len(symbols)} 隻股票...', 'yellow')}")

            if self.simplified_system_available:
                from simplified_system.src.api.stock_api import get_real_time_price

                results = []
                for i, symbol in enumerate(symbols, 1):
                    print(f"   查詢 {symbol} ({i}/{len(symbols)})...", end=" ")

                    try:
                        price = get_real_time_price(symbol)
                        if price:
                            results.append((symbol, price, "✅"))
                            print(f"{self._format_currency(price)}")
                        else:
                            results.append((symbol, "N/A", "❌"))
                            print("❌ 無數據")
                    except Exception as e:
                        results.append((symbol, "ERROR", "❌"))
                        print(f"❌ 錯誤")

                # 顯示結果表格
                if self.tabulate_available and results:
                    from tabulate import tabulate

                    table_data = [(symbol, self._format_currency(price) if isinstance(price, (int, float)) else price, status)
                                for symbol, price, status in results]

                    print(f"\n{self._get_colored_text('📊 批量查詢結果', 'bold')}")
                    headers = ["股票代碼", "實時價格", "狀態"]
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    print(f"\n{self._get_colored_text('查詢結果:', 'yellow')}")
                    for symbol, price, status in results:
                        print(f"  {symbol}: {price} {status}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 批量查詢錯誤: {e}', 'red')}")

    def _show_favorite_stocks(self):
        """顯示收藏股票列表"""
        print(f"\n{self._get_colored_text('⭐ 收藏股票列表', 'bold')}")
        print("-" * 30)

        try:
            favorites = self.config_manager.get('trading.favorite_symbols', [])

            if not favorites:
                print(f"{self._get_colored_text('📝 收藏列表為空', 'yellow')}")
                print(f"{self._get_colored_text('💡 提示: 查詢股票後可以添加到收藏', 'cyan')}")
                return

            print(f"{self._get_colored_text(f'共 {len(favorites)} 隻收藏股票:', 'yellow')}")
            for i, symbol in enumerate(favorites, 1):
                print(f"  {i}. {symbol}")

            # 提供操作選項
            print(f"\n{self._get_colored_text('操作選項:', 'yellow')}")
            print("1. 🚀 快速查詢所有收藏股票")
            print("2. 🗑️ 刪除收藏項目")
            print("3. ✏️ 編輯收藏列表")
            print("0. 🚪 返回")

            choice = self._get_user_input("請選擇操作 (0-3)", ['0', '1', '2', '3'])

            if choice == '1':
                self._batch_stock_query()
            elif choice == '2':
                self._remove_from_favorites()
            elif choice == '3':
                self._edit_favorites()

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 顯示收藏列表錯誤: {e}', 'red')}")

    def _real_time_price_query(self):
        """實時價格查詢"""
        print(f"\n{self._get_colored_text('📈 實時價格查詢', 'bold')}")
        print("-" * 30)

        try:
            if not self.simplified_system_available:
                print(f"{self._get_colored_text('❌ Simplified System不可用', 'red')}")
                return

            from simplified_system.src.api.stock_api import get_real_time_price

            symbol = self._get_user_input("請輸入股票代碼", None)
            if not symbol:
                return

            print(f"{self._get_colored_text(f'🔍 查詢 {symbol} 實時價格...', 'yellow')}")

            price = get_real_time_price(symbol)

            if price:
                print(f"{self._get_colored_text('✅ 實時價格:', 'green')} {self._format_currency(price)}")

                # 詢問是否添加到收藏
                add_to_fav = self._get_user_input("添加到收藏列表? (y/n)", ['y', 'n', 'Y', 'N'])
                if add_to_fav.lower() in ['y', 'yes']:
                    self._add_to_favorites(symbol)
            else:
                print(f"{self._get_colored_text('❌ 無法獲取實時價格', 'red')}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 實時價格查詢錯誤: {e}', 'red')}")

    def _data_quality_validation(self):
        """數據質量驗證 - Phase 2 Task 2.3"""
        print(f"\n{self._get_colored_text('🔍 數據質量驗證', 'bold')}")
        print("-" * 30)

        try:
            symbol = self._get_user_input("請輸入要驗證的股票代碼", None)
            if not symbol:
                return

            duration = 90  # 默認驗證最近90天數據

            print(f"{self._get_colored_text(f'🔍 驗證 {symbol} 最近{duration}天數據質量...', 'yellow')}")

            if self.simplified_system_available:
                from simplified_system.src.api.stock_api import get_stock_prices_dataframe
                import pandas as pd

                df = get_stock_prices_dataframe(symbol, duration)

                if df is None or len(df) == 0:
                    print(f"{self._get_colored_text('❌ 無法獲取數據進行驗證', 'red')}")
                    return

                # 執行數據質量檢查
                quality_report = self._perform_data_quality_checks(df)

                # 顯示質量報告
                self._display_quality_report(symbol, quality_report)

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 數據質量驗證錯誤: {e}', 'red')}")

    def _perform_data_quality_checks(self, df) -> dict:
        """執行數據質量檢查"""
        try:
            import pandas as pd

            report = {
                'total_records': len(df),
                'date_range': (df.index[0], df.index[-1]),
                'missing_values': df.isnull().sum().sum(),
                'duplicate_dates': df.index.duplicated().sum(),
                'price_anomalies': 0,
                'gaps': 0,
                'completeness_score': 0.0,
                'consistency_score': 0.0,
                'overall_quality': 'UNKNOWN'
            }

            # 檢查缺失值
            if report['missing_values'] == 0:
                report['completeness_score'] = 1.0
            else:
                report['completeness_score'] = (len(df) - report['missing_values']) / len(df)

            # 檢查重複日期
            if report['duplicate_dates'] == 0:
                report['consistency_score'] = 1.0
            else:
                report['consistency_score'] = (len(df) - report['duplicate_dates']) / len(df)

            # 檢查價格異常值
            if 'price' in df.columns:
                prices = df['price']
                Q1 = prices.quantile(0.25)
                Q3 = prices.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = prices[(prices < lower_bound) | (prices > upper_bound)]
                report['price_anomalies'] = len(outliers)

            # 檢查數據間隔 (日期間隙)
            if len(df) > 1:
                date_diffs = df.index.to_series().diff().dt.days.dropna()
                expected_diff = 1  # 期望每日數據

                # 考慮周末和假期，允許較大的間隔
                gaps = date_diffs[date_diffs > expected_diff + 3]  # 超過4天的間隔視為間隙
                report['gaps'] = len(gaps)

            # 計算總體質量評分
            quality_score = (report['completeness_score'] + report['consistency_score']) / 2

            # 根據異常值調整評分
            if report['price_anomalies'] > 0:
                quality_score *= 0.9
            if report['gaps'] > 0:
                quality_score *= 0.95

            # 確定質量等級
            if quality_score >= 0.95:
                report['overall_quality'] = 'EXCELLENT'
            elif quality_score >= 0.85:
                report['overall_quality'] = 'GOOD'
            elif quality_score >= 0.7:
                report['overall_quality'] = 'FAIR'
            else:
                report['overall_quality'] = 'POOR'

            report['final_score'] = round(quality_score, 3)

        except Exception as e:
            logger.error(f"數據質量檢查錯誤: {e}")
            report['error'] = str(e)
            report['overall_quality'] = 'ERROR'

        return report

    def _display_quality_report(self, symbol: str, report: dict):
        """顯示數據質量報告"""
        print(f"\n{self._get_colored_text('📊 數據質量報告', 'bold')}")
        print("=" * 50)
        print(f"股票代碼: {symbol}")
        print("=" * 50)

        # 基本信息
        basic_metrics = [
            ("總記錄數", report['total_records']),
            ("數據時間範圍", f"{report['date_range'][0].strftime('%Y-%m-%d')} 至 {report['date_range'][1].strftime('%Y-%m-%d')}"),
            ("缺失值數量", report['missing_values']),
            ("重複日期數量", report['duplicate_dates']),
            ("價格異常值", report['price_anomalies']),
            ("數據間隙", report['gaps'])
        ]

        # 質量評分
        quality_metrics = [
            ("完整性評分", f"{report['completeness_score']:.3f}"),
            ("一致性評分", f"{report['consistency_score']:.3f}"),
            ("總體評分", f"{report.get('final_score', 'N/A')}"),
            ("質量等級", report['overall_quality'])
        ]

        if self.tabulate_available:
            from tabulate import tabulate

            print(f"\n{self._get_colored_text('📋 基本指標', 'cyan')}")
            print(tabulate(basic_metrics, tablefmt="grid"))

            print(f"\n{self._get_colored_text('🎯 質量評分', 'cyan')}")
            print(tabulate(quality_metrics, tablefmt="grid"))
        else:
            print(f"\n{self._get_colored_text('📋 基本指標', 'cyan')}")
            for label, value in basic_metrics:
                print(f"  {label}: {value}")

            print(f"\n{self._get_colored_text('🎯 質量評分', 'cyan')}")
            for label, value in quality_metrics:
                print(f"  {label}: {value}")

        # 質量狀態顏色顯示
        quality_colors = {
            'EXCELLENT': 'green',
            'GOOD': 'cyan',
            'FAIR': 'yellow',
            'POOR': 'red',
            'ERROR': 'red'
        }

        color = quality_colors.get(report['overall_quality'], 'white')
        print(f"\n{self._get_colored_text('🎯 總體評估:', 'bold')} {self._get_colored_text(report['overall_quality'], color)}")

        # 根據質量等級給出建議
        if report['overall_quality'] in ['EXCELLENT', 'GOOD']:
            print(f"{self._get_colored_text('✅ 數據質量良好，可以進行分析', 'green')}")
        elif report['overall_quality'] == 'FAIR':
            print(f"{self._get_colored_text('⚠️ 數據質量一般，建議謹慎使用', 'yellow')}")
        else:
            print(f"{self._get_colored_text('❌ 數據質量較差，建議重新獲取數據', 'red')}")

    def _remove_from_favorites(self):
        """從收藏列表中刪除"""
        # 這是一個輔助方法，實現省略...
        pass

    def _edit_favorites(self):
        """編輯收藏列表"""
        # 這是一個輔助方法，實現省略...
        pass

    def technical_indicators_menu(self, symbol=None, data=None):
        """Phase 3 Task 3.1: 增強技術指標計算界面"""
        print(f"\n{self._get_colored_text('📈 技術指標分析 - Phase 3 增強版', 'bold')}")
        print("-" * 50)

        if not data:
            # 如果沒有數據，先獲取
            try:
                default_symbol = self.config_manager.get('trading.default_symbol') if self.config_manager else self.config.get('default_symbol', '0700.HK')
                default_duration = self.config_manager.get('trading.default_duration') if self.config_manager else self.config.get('default_duration', 252)

                symbol = symbol or default_symbol
                print(f"{self._get_colored_text('正在獲取股票數據...', 'yellow')}")

                if self.simplified_system_available:
                    from simplified_system.src.api.stock_api import get_hk_stock_data, get_stock_prices_dataframe
                    data = get_stock_prices_dataframe(symbol, default_duration)

                if data is None or len(data) == 0:
                    print(f"{self._get_colored_text('❌ 無法獲取股票數據', 'red')}")
                    return
            except Exception as e:
                print(f"{self._get_colored_text(f'❌ 錯誤: {e}', 'red')}")
                return

        try:
            if self.simplified_system_available:
                from simplified_system.src.indicators.core_indicators import CoreIndicators
                from simplified_system.src.indicators.technical_analyzer import TechnicalAnalyzer
                import pandas as pd

                # 轉換數據格式
                if not isinstance(data, pd.DataFrame) or 'close' not in data.columns:
                    print(f"{self._get_colored_text('❌ 數據格式不支援', 'red')}")
                    return

                # 主菜單循環
                while True:
                    print(f"\n{self._get_colored_text('📊 技術指標操作選項:', 'yellow')}")
                    print("1. 🔍 技術指標計算與展示")
                    print("2. 📈 趨勢分析功能")
                    print("3. ⚙️  指標參數設置")
                    print("4. 💡 交易信號分析")
                    print("5. 📊 綜合技術評分")
                    print("6. 📄 詳細數據報告")
                    print("0. 🚪 返回主菜單")

                    choice = self._get_user_input("請選擇操作 (0-6)", ['0', '1', '2', '3', '4', '5', '6'])

                    if choice == '0':
                        break
                    elif choice == '1':
                        self._show_indicator_calculations(symbol, data)
                    elif choice == '2':
                        self._show_trend_analysis(symbol, data)
                    elif choice == '3':
                        self._configure_indicators()
                    elif choice == '4':
                        self._show_trading_signals(symbol, data)
                    elif choice == '5':
                        self._show_technical_score(symbol, data)
                    elif choice == '6':
                        self._show_detailed_report(symbol, data)

        except Exception as e:
            logger.error(f"技術指標菜單錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 技術指標錯誤: {e}', 'red')}")

        input(f"\n{self._get_colored_text('按Enter返回主菜單...', 'cyan')}")

    def _show_indicator_calculations(self, symbol: str, data: pd.DataFrame):
        """Phase 3 Task 3.1: 技術指標計算與展示"""
        print(f"\n{self._get_colored_text('🔍 技術指標計算與展示', 'bold')}")
        print("-" * 40)

        try:
            from simplified_system.src.indicators.core_indicators import CoreIndicators

            # 初始化指標引擎
            indicators = CoreIndicators()

            # 獲取配置的指標參數
            rsi_config = self.config_manager.get('indicators.rsi', {}) if self.config_manager else {}
            sma_config = self.config_manager.get('indicators.sma', {}) if self.config_manager else {}
            macd_config = self.config_manager.get('indicators.macd', {}) if self.config_manager else {}
            bollinger_config = self.config_manager.get('indicators.bollinger', {}) if self.config_manager else {}

            print(f"{self._get_colored_text('正在計算技術指標...', 'yellow')}")

            # 計算各類指標
            close_prices = data['close']
            high_prices = data['high'] if 'high' in data.columns else close_prices
            low_prices = data['low'] if 'low' in data.columns else close_prices
            volume_prices = data['volume'] if 'volume' in data.columns else pd.Series([1] * len(data))

            # 1. 趨勢指標
            rsi_period = rsi_config.get('period', 14)
            rsi = indicators.calculate_rsi(close_prices, rsi_period)

            short_period = sma_config.get('short_period', 20)
            long_period = sma_config.get('long_period', 50)
            sma_20 = indicators.calculate_sma(close_prices, short_period)
            sma_50 = indicators.calculate_sma(close_prices, long_period)
            ema_12 = indicators.calculate_ema(close_prices, 12)
            ema_26 = indicators.calculate_ema(close_prices, 26)

            # 2. MACD指標
            macd_fast = macd_config.get('fast', 12)
            macd_slow = macd_config.get('slow', 26)
            macd_signal = macd_config.get('signal', 9)
            macd_results = indicators.calculate_macd(close_prices, macd_fast, macd_slow, macd_signal)

            # 3. 波動率指標
            bb_period = bollinger_config.get('period', 20)
            bb_std_dev = bollinger_config.get('std_dev', 2)
            bb_results = indicators.calculate_bollinger_bands(close_prices, bb_period, bb_std_dev)

            # 4. 動量指標
            stoch_results = indicators.calculate_stochastic(high_prices, low_prices, close_prices)
            williams_r = indicators.calculate_williams_r(high_prices, low_prices, close_prices)

            # 5. 成交量指標
            volume_ma = indicators.calculate_volume_ma(volume_prices, 20)

            # 準備顯示數據
            latest_price = close_prices.iloc[-1] if len(close_prices) > 0 else 0

            indicator_data = [
                # 基本價格信息
                ("🏷️ 股票代碼", symbol, ""),
                ("💰 最新價格", f"{latest_price:.2f} HKD", ""),
                ("📊 數據點數", f"{len(data)} 條", ""),
                ("", "", ""),  # 分隔線

                # 趨勢指標
                ("📈 RSI", f"{rsi.iloc[-1]:.2f}" if len(rsi) > 0 else "N/A", self._get_rsi_signal(rsi.iloc[-1]) if len(rsi) > 0 else "N/A"),
                (f"📊 SMA({short_period})", f"{sma_20.iloc[-1]:.2f}" if len(sma_20) > 0 else "N/A", self._get_ma_signal(sma_20.iloc[-1], latest_price) if len(sma_20) > 0 else "N/A"),
                (f"📊 SMA({long_period})", f"{sma_50.iloc[-1]:.2f}" if len(sma_50) > 0 else "N/A", self._get_ma_signal(sma_50.iloc[-1], latest_price) if len(sma_50) > 0 else "N/A"),
                ("📊 EMA(12)", f"{ema_12.iloc[-1]:.2f}" if len(ema_12) > 0 else "N/A", self._get_ma_signal(ema_12.iloc[-1], latest_price) if len(ema_12) > 0 else "N/A"),
                ("📊 EMA(26)", f"{ema_26.iloc[-1]:.2f}" if len(ema_26) > 0 else "N/A", self._get_ma_signal(ema_26.iloc[-1], latest_price) if len(ema_26) > 0 else "N/A"),
                ("", "", ""),  # 分隔線

                # MACD指標
                ("🔶 MACD線", f"{macd_results['macd'].iloc[-1]:.4f}" if len(macd_results['macd']) > 0 else "N/A", self._get_macd_signal(macd_results['macd'].iloc[-1]) if len(macd_results['macd']) > 0 else "N/A"),
                ("🔶 MACD信號", f"{macd_results['signal'].iloc[-1]:.4f}" if len(macd_results['signal']) > 0 else "N/A", self._get_macd_signal(macd_results['signal'].iloc[-1]) if len(macd_results['signal']) > 0 else "N/A"),
                ("🔶 MACD柱狀", f"{macd_results['histogram'].iloc[-1]:.4f}" if len(macd_results['histogram']) > 0 else "N/A", self._get_macd_histogram_signal(macd_results['histogram'].iloc[-1]) if len(macd_results['histogram']) > 0 else "N/A"),
                ("", "", ""),  # 分隔線

                # 波動率指標
                ("📊 布林上軌", f"{bb_results['upper'].iloc[-1]:.2f}" if len(bb_results['upper']) > 0 else "N/A", ""),
                ("📊 布林中軌", f"{bb_results['middle'].iloc[-1]:.2f}" if len(bb_results['middle']) > 0 else "N/A", ""),
                ("📊 布林下軌", f"{bb_results['lower'].iloc[-1]:.2f}" if len(bb_results['lower']) > 0 else "N/A", self._get_bollinger_signal(latest_price, bb_results) if len(bb_results['lower']) > 0 else "N/A"),
                ("📊 布林寬度", f"{bb_results['width'].iloc[-1]:.4f}" if len(bb_results['width']) > 0 else "N/A", self._get_bollinger_width_signal(bb_results['width'].iloc[-1]) if len(bb_results['width']) > 0 else "N/A"),
                ("", "", ""),  # 分隔線

                # 動量指標
                ("🔸 隨機K", f"{stoch_results['k_percent'].iloc[-1]:.2f}" if len(stoch_results['k_percent']) > 0 else "N/A", self._get_stoch_signal(stoch_results['k_percent'].iloc[-1]) if len(stoch_results['k_percent']) > 0 else "N/A"),
                ("🔸 隨機D", f"{stoch_results['d_percent'].iloc[-1]:.2f}" if len(stoch_results['d_percent']) > 0 else "N/A", self._get_stoch_signal(stoch_results['d_percent'].iloc[-1]) if len(stoch_results['d_percent']) > 0 else "N/A"),
                ("🔸 威廉%R", f"{williams_r.iloc[-1]:.2f}" if len(williams_r) > 0 else "N/A", self._get_williams_signal(williams_r.iloc[-1]) if len(williams_r) > 0 else "N/A"),
                ("", "", ""),  # 分隔線

                # 成交量指標
                ("📦 成交量MA", f"{volume_ma.iloc[-1]:.0f}" if len(volume_ma) > 0 else "N/A", ""),
            ]

            print(f"{self._get_colored_text('✅ 技術指標計算完成!', 'green')}")

            # 顯示結果表格
            if self.tabulate_available:
                from tabulate import tabulate

                # 過濾掉分隔線項目
                table_data = [row for row in indicator_data if row[0] != ""]
                headers = ["指標名稱", "數值", "信號/狀態"]
                print(f"\n{self._get_colored_text('📊 技術指標結果詳情', 'cyan')}")
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
            else:
                print(f"\n{self._get_colored_text('📊 技術指標結果', 'bold')}")
                for indicator, value, signal in indicator_data:
                    if indicator:  # 跳過分隔線
                        print(f"  {indicator}: {value} ({signal})" if signal else f"  {indicator}: {value}")

        except Exception as e:
            logger.error(f"技術指標計算錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 計算錯誤: {e}', 'red')}")

    def _show_trend_analysis(self, symbol: str, data: pd.DataFrame):
        """Phase 3 Task 3.2: 趨勢分析功能"""
        print(f"\n{self._get_colored_text('📈 趨勢分析功能', 'bold')}")
        print("-" * 40)

        try:
            from simplified_system.src.indicators.technical_analyzer import TechnicalAnalyzer
            from simplified_system.src.indicators.core_indicators import CoreIndicators

            # 初始化分析器
            analyzer = TechnicalAnalyzer()
            indicators = CoreIndicators()

            print(f"{self._get_colored_text('正在分析趨勢...', 'yellow')}")

            # 執行趨勢分析
            trend_analysis = analyzer.analyze_trend(data)
            multiple_timeframe = self._analyze_multiple_timeframes(data, indicators)
            trend_strength = self._calculate_trend_strength(data, indicators)

            # 顯示趨勢分析結果
            print(f"\n{self._get_colored_text('📊 趨勢分析結果', 'cyan')}")
            print("=" * 50)

            # 主要趨勢分析
            trend_data = [
                ("主要趨勢方向", trend_analysis.get('trend', 'UNKNOWN')),
                ("趨勢強度", trend_analysis.get('strength', 'WEAK')),
                ("趨勢置信度", f"{trend_analysis.get('confidence', 0):.2%}"),
                ("趨勢方向分數", f"{trend_analysis.get('direction', 0):.3f}"),
            ]

            if self.tabulate_available:
                from tabulate import tabulate
                print(tabulate(trend_data, headers=["分析項目", "結果"], tablefmt="grid"))
            else:
                for item, result in trend_data:
                    print(f"  {item}: {result}")

            # 多時間框架分析
            print(f"\n{self._get_colored_text('🕐 多時間框架分析', 'cyan')}")
            print("-" * 30)

            timeframe_analysis = []
            for timeframe, result in multiple_timeframe.items():
                trend_emoji = "📈" if result['trend'] == 'UP' else "📉" if result['trend'] == 'DOWN' else "➡️"
                timeframe_analysis.append((
                    timeframe,
                    result['trend'],
                    result['strength'],
                    f"{result['confidence']:.1%}"
                ))

            if self.tabulate_available:
                from tabulate import tabulate
                headers = ["時間框架", "趨勢", "強度", "置信度"]
                print(tabulate(timeframe_analysis, headers=headers, tablefmt="grid"))
            else:
                for timeframe, trend, strength, confidence in timeframe_analysis:
                    print(f"  {timeframe}: {trend} {strength} ({confidence})")

            # 趨勢強度評估
            print(f"\n{self._get_colored_text('💪 趨勢強度評估', 'cyan')}")
            print("-" * 25)

            strength_score = trend_strength.get('overall_strength', 0)
            strength_level = self._get_strength_level(strength_score)

            strength_indicators = [
                ("綜合強度分數", f"{strength_score:.3f}"),
                ("強度等級", strength_level),
                ("短期動量", f"{trend_strength.get('short_momentum', 0):.3f}"),
                ("中期動量", f"{trend_strength.get('medium_momentum', 0):.3f}"),
                ("長期動量", f"{trend_strength.get('long_momentum', 0):.3f}"),
            ]

            if self.tabulate_available:
                from tabulate import tabulate
                print(tabulate(strength_indicators, headers=["指標", "數值"], tablefmt="grid"))
            else:
                for indicator, value in strength_indicators:
                    print(f"  {indicator}: {value}")

            # 趨勢建議
            print(f"\n{self._get_colored_text('💡 趨勢交易建議', 'bold')}")
            print("-" * 25)

            recommendations = self._generate_trend_recommendations(trend_analysis, multiple_timeframe, trend_strength)
            for i, recommendation in enumerate(recommendations, 1):
                print(f"  {i}. {recommendation}")

        except Exception as e:
            logger.error(f"趨勢分析錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 趨勢分析錯誤: {e}', 'red')}")

    def _analyze_multiple_timeframes(self, data: pd.DataFrame, indicators) -> Dict[str, Dict]:
        """分析多時間框架趨勢"""
        try:
            timeframes = {
                '短期 (5日)': 5,
                '中期 (20日)': 20,
                '長期 (50日)': 50
            }

            results = {}
            close_prices = data['close']

            for name, period in timeframes.items():
                if len(close_prices) >= period:
                    sma = indicators.calculate_sma(close_prices, period)
                    current_price = close_prices.iloc[-1]
                    ma_value = sma.iloc[-1]

                    # 計算趨勢方向和強度
                    if current_price > ma_value:
                        trend = 'UP'
                        strength = 'STRONG' if (current_price / ma_value - 1) > 0.05 else 'MODERATE'
                    else:
                        trend = 'DOWN'
                        strength = 'STRONG' if (ma_value / current_price - 1) > 0.05 else 'MODERATE'

                    # 計算置信度 (基於歷史表現)
                    price_above_ma = (close_prices > sma).sum()
                    confidence = price_above_ma / len(close_prices)

                    results[name] = {
                        'trend': trend,
                        'strength': strength,
                        'confidence': confidence,
                        'ma_value': ma_value,
                        'price_vs_ma': (current_price / ma_value - 1) * 100
                    }
                else:
                    results[name] = {
                        'trend': 'UNKNOWN',
                        'strength': 'WEAK',
                        'confidence': 0.0
                    }

            return results

        except Exception as e:
            logger.error(f"多時間框架分析錯誤: {e}")
            return {}

    def _calculate_trend_strength(self, data: pd.DataFrame, indicators) -> Dict[str, float]:
        """計算趨勢強度指標"""
        try:
            close_prices = data['close']

            # 計算不同時間週期的動量
            periods = [5, 10, 20, 50]
            momentums = []

            for period in periods:
                if len(close_prices) > period:
                    momentum = (close_prices.iloc[-1] / close_prices.iloc[-period-1] - 1) * 100
                    momentums.append(momentum)

            # 計算綜合強度
            if momentums:
                short_momentum = momentums[0] if len(momentums) > 0 else 0
                medium_momentum = sum(momentums[1:3]) / len(momentums[1:3]) if len(momentums) > 2 else 0
                long_momentum = momentums[-1] if len(momentums) > 0 else 0
                overall_strength = sum(momentums) / len(momentums) / 100  # 正規化
            else:
                short_momentum = medium_momentum = long_momentum = overall_strength = 0

            return {
                'overall_strength': overall_strength,
                'short_momentum': short_momentum,
                'medium_momentum': medium_momentum,
                'long_momentum': long_momentum
            }

        except Exception as e:
            logger.error(f"趨勢強度計算錯誤: {e}")
            return {
                'overall_strength': 0,
                'short_momentum': 0,
                'medium_momentum': 0,
                'long_momentum': 0
            }

    def _get_rsi_signal(self, rsi):
        """獲取RSI信號"""
        if rsi < 30:
            return "超賣"
        elif rsi > 70:
            return "超買"
        else:
            return "中性"

    def _get_ma_signal(self, ma, price):
        """獲取移動平均線信號"""
        if price > ma:
            return "看漲"
        elif price < ma:
            return "看跌"
        else:
            return "中性"

    def _get_macd_signal(self, macd_value):
        """獲取MACD信號"""
        if macd_value > 0:
            return "看漲"
        elif macd_value < 0:
            return "看跌"
        else:
            return "中性"

    def _get_macd_histogram_signal(self, histogram_value):
        """獲取MACD柱狀信號"""
        if histogram_value > 0:
            return "動量增強"
        elif histogram_value < 0:
            return "動量減弱"
        else:
            return "動量平衡"

    def _get_bollinger_signal(self, price, bb_results):
        """獲取布林帶信號"""
        try:
            upper = bb_results['upper'].iloc[-1] if len(bb_results['upper']) > 0 else None
            lower = bb_results['lower'].iloc[-1] if len(bb_results['lower']) > 0 else None

            if upper and lower:
                if price > upper:
                    return "突破上軌"
                elif price < lower:
                    return "跌破下軌"
                else:
                    position = (price - lower) / (upper - lower)
                    if position > 0.8:
                        return "接近上軌"
                    elif position < 0.2:
                        return "接近下軌"
                    else:
                        return "區間內"
        except:
            pass
        return "N/A"

    def _get_bollinger_width_signal(self, width):
        """獲取布林帶寬度信號"""
        if width > 0.1:
            return "高波動"
        elif width < 0.05:
            return "低波動"
        else:
            return "正常波動"

    def _get_stoch_signal(self, stoch_value):
        """獲取隨機指標信號"""
        if stoch_value > 80:
            return "超買"
        elif stoch_value < 20:
            return "超賣"
        else:
            return "中性"

    def _get_williams_signal(self, williams_value):
        """獲取威廉指標信號"""
        if williams_value > -20:
            return "超買"
        elif williams_value < -80:
            return "超賣"
        else:
            return "中性"

    def _analyze_trend(self, short_ma, long_ma):
        """分析趨勢"""
        if short_ma > long_ma:
            return "上升趨勢 📈"
        elif short_ma < long_ma:
            return "下降趨勢 📉"
        else:
            return "橫盤整理 ➡️"

    def _get_strength_level(self, strength_score):
        """獲取強度等級"""
        if abs(strength_score) > 0.1:
            return "極強"
        elif abs(strength_score) > 0.05:
            return "強"
        elif abs(strength_score) > 0.02:
            return "中等"
        else:
            return "弱"

    def _generate_trend_recommendations(self, trend_analysis, multiple_timeframe, trend_strength):
        """生成趨勢交易建議"""
        recommendations = []

        main_trend = trend_analysis.get('trend', 'UNKNOWN')
        trend_strength_val = trend_strength.get('overall_strength', 0)

        if main_trend == 'UP':
            if trend_strength_val > 0.05:
                recommendations.append("🟢 強烈上升趨勢，考慮逢低買入")
            else:
                recommendations.append("🟡 上升趨勢較弱，謹慎做多")
        elif main_trend == 'DOWN':
            if trend_strength_val < -0.05:
                recommendations.append("🔴 強烈下降趨勢，考慮減倉或避險")
            else:
                recommendations.append("🟡 下降趨勢較弱，適合波段操作")
        else:
            recommendations.append("⚪ 趨勢不明朗，建議觀望")

        # 多時間框架一致性檢查
        up_count = sum(1 for result in multiple_timeframe.values() if result.get('trend') == 'UP')
        down_count = sum(1 for result in multiple_timeframe.values() if result.get('trend') == 'DOWN')
        total_count = len(multiple_timeframe)

        if up_count / total_count > 0.7:
            recommendations.append("📈 多時間框架普遍看漲，趨勢較為可靠")
        elif down_count / total_count > 0.7:
            recommendations.append("📉 多時間框架普遍看跌，警惕風險")
        else:
            recommendations.append("🔄 多時間框架意見分歧，可能面臨轉向")

        # 波動率建議
        if abs(trend_strength_val) > 0.1:
            recommendations.append("⚡ 波動率較高，注意倉位控制")
        else:
            recommendations.append("🛡️ 波動率適中，可正常操作")

        return recommendations

    def _configure_indicators(self):
        """配置指標參數"""
        print(f"\n{self._get_colored_text('⚙️ 指標參數設置', 'bold')}")
        print("-" * 30)

        while True:
            print(f"\n{self._get_colored_text('請選擇要配置的指標:', 'yellow')}")
            print("1. RSI (相對強弱指數)")
            print("2. SMA/EMA (移動平均線)")
            print("3. MACD (移動平均收斂背離)")
            print("4. 布林帶 (Bollinger Bands)")
            print("5. KDJ (隨機指標)")
            print("6. 查看當前配置")
            print("7. 重置為默認值")
            print("0. 返回上一級菜單")

            choice = self._get_user_input("請選擇 (0-7)", ['0', '1', '2', '3', '4', '5', '6', '7'])

            if choice == '0':
                break
            elif choice == '1':
                self._configure_rsi()
            elif choice == '2':
                self._configure_ma()
            elif choice == '3':
                self._configure_macd()
            elif choice == '4':
                self._configure_bollinger()
            elif choice == '5':
                self._configure_kdj()
            elif choice == '6':
                self._show_current_indicator_config()
            elif choice == '7':
                self._reset_indicator_config()

    def _configure_rsi(self):
        """配置RSI參數"""
        try:
            current_config = self.config_manager.get('indicators.rsi', {}) if self.config_manager else {}
            current_period = current_config.get('period', 14)
            current_oversold = current_config.get('oversold', 30)
            current_overbought = current_config.get('overbought', 70)

            print(f"\n{self._get_colored_text('RSI參數配置', 'cyan')}")
            print(f"當前週期: {current_period}")
            print(f"當前超賣線: {current_oversold}")
            print(f"當前超買線: {current_overbought}")

            period = self._get_user_input(f"RSI週期 (默認: {current_period})", None)
            oversold = self._get_user_input(f"超賣線 (默認: {current_oversold})", None)
            overbought = self._get_user_input(f"超買線 (默認: {current_overbought})", None)

            # 保存配置
            if period and period.isdigit():
                self.config_manager.set('indicators.rsi.period', int(period))
            if oversold and oversold.replace('.', '').isdigit():
                self.config_manager.set('indicators.rsi.oversold', float(oversold))
            if overbought and overbought.replace('.', '').isdigit():
                self.config_manager.set('indicators.rsi.overbought', float(overbought))

            self.config_manager.save_config()
            print(f"{self._get_colored_text('✅ RSI配置已保存', 'green')}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ RSI配置錯誤: {e}', 'red')}")

    def _configure_ma(self):
        """配置移動平均線參數"""
        try:
            current_config = self.config_manager.get('indicators.sma', {}) if self.config_manager else {}
            current_short = current_config.get('short_period', 20)
            current_long = current_config.get('long_period', 50)

            print(f"\n{self._get_colored_text('移動平均線參數配置', 'cyan')}")
            print(f"當前短期週期: {current_short}")
            print(f"當前長期週期: {current_long}")

            short = self._get_user_input(f"短期移動平均線週期 (默認: {current_short})", None)
            long = self._get_user_input(f"長期移動平均線週期 (默認: {current_long})", None)

            # 保存配置
            if short and short.isdigit():
                self.config_manager.set('indicators.sma.short_period', int(short))
            if long and long.isdigit():
                self.config_manager.set('indicators.sma.long_period', int(long))

            self.config_manager.save_config()
            print(f"{self._get_colored_text('✅ 移動平均線配置已保存', 'green')}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 移動平均線配置錯誤: {e}', 'red')}")

    def _configure_macd(self):
        """配置MACD參數"""
        try:
            current_config = self.config_manager.get('indicators.macd', {}) if self.config_manager else {}
            current_fast = current_config.get('fast', 12)
            current_slow = current_config.get('slow', 26)
            current_signal = current_config.get('signal', 9)

            print(f"\n{self._get_colored_text('MACD參數配置', 'cyan')}")
            print(f"當前快線週期: {current_fast}")
            print(f"當前慢線週期: {current_slow}")
            print(f"當前信號線週期: {current_signal}")

            fast = self._get_user_input(f"MACD快線週期 (默認: {current_fast})", None)
            slow = self._get_user_input(f"MACD慢線週期 (默認: {current_slow})", None)
            signal = self._get_user_input(f"MACD信號線週期 (默認: {current_signal})", None)

            # 保存配置
            if fast and fast.isdigit():
                self.config_manager.set('indicators.macd.fast', int(fast))
            if slow and slow.isdigit():
                self.config_manager.set('indicators.macd.slow', int(slow))
            if signal and signal.isdigit():
                self.config_manager.set('indicators.macd.signal', int(signal))

            self.config_manager.save_config()
            print(f"{self._get_colored_text('✅ MACD配置已保存', 'green')}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ MACD配置錯誤: {e}', 'red')}")

    def _configure_bollinger(self):
        """配置布林帶參數"""
        try:
            current_config = self.config_manager.get('indicators.bollinger', {}) if self.config_manager else {}
            current_period = current_config.get('period', 20)
            current_std_dev = current_config.get('std_dev', 2)

            print(f"\n{self._get_colored_text('布林帶參數配置', 'cyan')}")
            print(f"當前週期: {current_period}")
            print(f"當前標準差倍數: {current_std_dev}")

            period = self._get_user_input(f"布林帶週期 (默認: {current_period})", None)
            std_dev = self._get_user_input(f"標準差倍數 (默認: {current_std_dev})", None)

            # 保存配置
            if period and period.isdigit():
                self.config_manager.set('indicators.bollinger.period', int(period))
            if std_dev and std_dev.replace('.', '').isdigit():
                self.config_manager.set('indicators.bollinger.std_dev', float(std_dev))

            self.config_manager.save_config()
            print(f"{self._get_colored_text('✅ 布林帶配置已保存', 'green')}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 布林帶配置錯誤: {e}', 'red')}")

    def _configure_kdj(self):
        """配置KDJ參數"""
        try:
            current_config = self.config_manager.get('indicators.kdj', {}) if self.config_manager else {}
            current_k = current_config.get('k_period', 9)
            current_d = current_config.get('d_period', 3)
            current_j = current_config.get('j_period', 3)

            print(f"\n{self._get_colored_text('KDJ參數配置', 'cyan')}")
            print(f"當前K值週期: {current_k}")
            print(f"當前D值週期: {current_d}")
            print(f"當前J值週期: {current_j}")

            k_period = self._get_user_input(f"K值週期 (默認: {current_k})", None)
            d_period = self._get_user_input(f"D值週期 (默認: {current_d})", None)
            j_period = self._get_user_input(f"J值週期 (默認: {current_j})", None)

            # 保存配置
            if k_period and k_period.isdigit():
                self.config_manager.set('indicators.kdj.k_period', int(k_period))
            if d_period and d_period.isdigit():
                self.config_manager.set('indicators.kdj.d_period', int(d_period))
            if j_period and j_period.isdigit():
                self.config_manager.set('indicators.kdj.j_period', int(j_period))

            self.config_manager.save_config()
            print(f"{self._get_colored_text('✅ KDJ配置已保存', 'green')}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ KDJ配置錯誤: {e}', 'red')}")

    def _show_current_indicator_config(self):
        """顯示當前指標配置"""
        print(f"\n{self._get_colored_text('📋 當前指標配置', 'bold')}")
        print("-" * 30)

        try:
            indicators_config = [
                ("RSI", self.config_manager.get('indicators.rsi', {}) if self.config_manager else {}),
                ("移動平均線", self.config_manager.get('indicators.sma', {}) if self.config_manager else {}),
                ("MACD", self.config_manager.get('indicators.macd', {}) if self.config_manager else {}),
                ("布林帶", self.config_manager.get('indicators.bollinger', {}) if self.config_manager else {}),
                ("KDJ", self.config_manager.get('indicators.kdj', {}) if self.config_manager else {})
            ]

            config_data = []
            for indicator_name, config in indicators_config:
                if config:
                    for key, value in config.items():
                        config_data.append((f"{indicator_name}_{key}", value))

            if self.tabulate_available and config_data:
                from tabulate import tabulate
                headers = ["配置項", "數值"]
                print(tabulate(config_data, headers=headers, tablefmt="grid"))
            elif config_data:
                for config_item, value in config_data:
                    print(f"  {config_item}: {value}")
            else:
                print("  無配置數據")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 顯示配置錯誤: {e}', 'red')}")

    def _reset_indicator_config(self):
        """重置指標配置為默認值"""
        try:
            confirm = self._get_user_input("確認重置所有指標配置為默認值? (y/n)", ['y', 'n', 'Y', 'N'])
            if confirm.lower() in ['y', 'yes']:
                self.config_manager.reset_to_default('indicators')
                self.config_manager.save_config()
                print(f"{self._get_colored_text('✅ 指標配置已重置為默認值', 'green')}")
        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 重置配置錯誤: {e}', 'red')}")

    def _show_trading_signals(self, symbol: str, data: pd.DataFrame):
        """顯示交易信號分析"""
        print(f"\n{self._get_colored_text('💡 交易信號分析', 'bold')}")
        print("-" * 40)

        try:
            from simplified_system.src.indicators.core_indicators import CoreIndicators
            from simplified_system.src.indicators.technical_analyzer import TechnicalAnalyzer

            indicators = CoreIndicators()
            analyzer = TechnicalAnalyzer()

            print(f"{self._get_colored_text('正在分析交易信號...', 'yellow')}")

            # 計算各種指標
            close_prices = data['close']
            high_prices = data['high'] if 'high' in data.columns else close_prices
            low_prices = data['low'] if 'low' in data.columns else close_prices

            # 計算主要指標
            rsi = indicators.calculate_rsi(close_prices)
            macd_results = indicators.calculate_macd(close_prices)
            bb_results = indicators.calculate_bollinger_bands(close_prices)
            stoch_results = indicators.calculate_stochastic(high_prices, low_prices, close_prices)
            sma_20 = indicators.calculate_sma(close_prices, 20)
            sma_50 = indicators.calculate_sma(close_prices, 50)

            # 獲取最新值
            latest_price = close_prices.iloc[-1]
            latest_rsi = rsi.iloc[-1]
            latest_macd = macd_results['macd'].iloc[-1]
            latest_macd_signal = macd_results['signal'].iloc[-1]
            latest_stoch_k = stoch_results['k_percent'].iloc[-1]
            latest_stoch_d = stoch_results['d_percent'].iloc[-1]

            # 分析各種信號
            signals = []

            # RSI信號
            if latest_rsi < 30:
                signals.append(("RSI超賣", "強烈買入", "🟢"))
            elif latest_rsi > 70:
                signals.append(("RSI超買", "強烈賣出", "🔴"))
            elif latest_rsi < 40:
                signals.append(("RSI偏弱", "買入", "🟡"))
            elif latest_rsi > 60:
                signals.append(("RSI偏強", "賣出", "🟡"))
            else:
                signals.append(("RSI中性", "持有", "⚪"))

            # MACD信號
            if latest_macd > latest_macd_signal and latest_macd > 0:
                signals.append(("MACD黃金交叉", "買入", "🟢"))
            elif latest_macd < latest_macd_signal and latest_macd < 0:
                signals.append(("MACD死亡交叉", "賣出", "🔴"))
            elif latest_macd > latest_macd_signal:
                signals.append(("MACD看漲", "偏向買入", "🟡"))
            else:
                signals.append(("MACD看跌", "偏向賣出", "🟡"))

            # 布林帶信號
            upper = bb_results['upper'].iloc[-1]
            lower = bb_results['lower'].iloc[-1]
            if latest_price > upper:
                signals.append(("突破布林上軌", "賣出", "🔴"))
            elif latest_price < lower:
                signals.append(("跌破布林下軌", "買入", "🟢"))
            else:
                signals.append(("布林帶區間內", "持有", "⚪"))

            # 隨機指標信號
            if latest_stoch_k > 80 and latest_stoch_d > 80:
                signals.append(("隨機指標超買", "賣出", "🔴"))
            elif latest_stoch_k < 20 and latest_stoch_d < 20:
                signals.append(("隨機指標超賣", "買入", "🟢"))
            else:
                signals.append(("隨機指標中性", "持有", "⚪"))

            # 移動平均線信號
            ma_20 = sma_20.iloc[-1]
            ma_50 = sma_50.iloc[-1]
            if latest_price > ma_20 > ma_50:
                signals.append(("移動平均線排列", "強勢買入", "🟢"))
            elif latest_price < ma_20 < ma_50:
                signals.append(("移動平均線排列", "強勢賣出", "🔴"))
            else:
                signals.append(("移動平均線混亂", "觀望", "⚪"))

            # 顯示信號結果
            print(f"\n{self._get_colored_text('🎯 當前交易信號', 'cyan')}")
            print("=" * 50)

            if self.tabulate_available:
                from tabulate import tabulate
                headers = ["信號類型", "建議", "強度"]
                signal_data = [(signal_type, suggestion, strength) for signal_type, suggestion, strength in signals]
                print(tabulate(signal_data, headers=headers, tablefmt="grid"))
            else:
                for signal_type, suggestion, strength in signals:
                    print(f"  {strength} {signal_type}: {suggestion}")

            # 綜合建議
            buy_signals = len([s for s in signals if "買入" in s[1]])
            sell_signals = len([s for s in signals if "賣出" in s[1]])

            print(f"\n{self._get_colored_text('📊 綜合交易建議', 'bold')}")
            print("-" * 30)

            if buy_signals > sell_signals + 1:
                print("🟢 綜合建議: 偏向買入，多個指標顯示超賣或看漲信號")
            elif sell_signals > buy_signals + 1:
                print("🔴 綜合建議: 偏向賣出，多個指標顯示超買或看跌信號")
            else:
                print("⚪ 綜合建議: 觀望為主，信號混合，建議等待更明確的趨勢")

            print(f"\n信號統計: 買入信號 {buy_signals} 個, 賣出信號 {sell_signals} 個, 持有信號 {len(signals) - buy_signals - sell_signals} 個")

        except Exception as e:
            logger.error(f"交易信號分析錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 交易信號分析錯誤: {e}', 'red')}")

    def _show_technical_score(self, symbol: str, data: pd.DataFrame):
        """顯示綜合技術評分"""
        print(f"\n{self._get_colored_text('📊 綜合技術評分', 'bold')}")
        print("-" * 40)

        try:
            from simplified_system.src.indicators.core_indicators import CoreIndicators

            indicators = CoreIndicators()
            close_prices = data['close']
            high_prices = data['high'] if 'high' in data.columns else close_prices
            low_prices = data['low'] if 'low' in data.columns else close_prices

            print(f"{self._get_colored_text('正在計算技術評分...', 'yellow')}")

            # 計算各種指標
            rsi = indicators.calculate_rsi(close_prices)
            macd_results = indicators.calculate_macd(close_prices)
            bb_results = indicators.calculate_bollinger_bands(close_prices)
            stoch_results = indicators.calculate_stochastic(high_prices, low_prices, close_prices)
            sma_20 = indicators.calculate_sma(close_prices, 20)
            sma_50 = indicators.calculate_sma(close_prices, 50)

            # 計算技術評分 (0-100分)
            scores = {
                "趨勢評分": self._calculate_trend_score(close_prices, sma_20, sma_50),
                "動量評分": self._calculate_momentum_score(rsi, macd_results),
                "波動率評分": self._calculate_volatility_score(bb_results),
                "超買超賣評分": self._calculate_overbought_score(rsi, stoch_results),
                "成交量評分": self._calculate_volume_score(data),
            }

            # 計算總分
            total_score = sum(scores.values()) / len(scores)

            # 評級
            if total_score >= 80:
                grade = "A+"
                description = "極佳"
            elif total_score >= 70:
                grade = "A"
                description = "良好"
            elif total_score >= 60:
                grade = "B+"
                description = "中等偏上"
            elif total_score >= 50:
                grade = "B"
                description = "中等"
            elif total_score >= 40:
                grade = "C+"
                description = "中等偏下"
            elif total_score >= 30:
                grade = "C"
                description = "較弱"
            else:
                grade = "D"
                description = "弱"

            # 顯示評分結果
            print(f"\n{self._get_colored_text('🎯 技術分析評分結果', 'cyan')}")
            print("=" * 50)
            print(f"股票代碼: {symbol}")
            print(f"總體評分: {total_score:.1f}/100 ({grade}) - {description}")
            print("-" * 50)

            if self.tabulate_available:
                from tabulate import tabulate
                score_data = [(category, f"{score:.1f}/100") for category, score in scores.items()]
                print(tabulate(score_data, headers=["評分類別", "分數"], tablefmt="grid"))
            else:
                for category, score in scores.items():
                    print(f"  {category}: {score:.1f}/100")

            # 投資建議
            print(f"\n{self._get_colored_text('💡 基於評分的投資建議', 'bold')}")
            print("-" * 35)

            if total_score >= 75:
                print("🟢 技術面極佳，建議考慮建立倉位")
            elif total_score >= 60:
                print("🟡 技術面良好，可適量配置")
            elif total_score >= 45:
                print("⚪ 技術面一般，建議謹慎操作")
            else:
                print("🔴 技術面較弱，建議觀望或減倉")

        except Exception as e:
            logger.error(f"技術評分計算錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 技術評分計算錯誤: {e}', 'red')}")

    def _show_detailed_report(self, symbol: str, data: pd.DataFrame):
        """顯示詳細數據報告"""
        print(f"\n{self._get_colored_text('📄 詳細技術分析報告', 'bold')}")
        print("-" * 50)

        try:
            from simplified_system.src.indicators.core_indicators import CoreIndicators
            from datetime import datetime

            indicators = CoreIndicators()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"{self._get_colored_text('生成詳細報告...', 'yellow')}")

            # 計算各種指標
            close_prices = data['close']
            high_prices = data['high'] if 'high' in data.columns else close_prices
            low_prices = data['low'] if 'low' in data.columns else close_prices

            report_data = {
                "基本信息": {
                    "股票代碼": symbol,
                    "報告生成時間": timestamp,
                    "數據期間": f"{data.index[0].strftime('%Y-%m-%d')} 至 {data.index[-1].strftime('%Y-%m-%d')}",
                    "數據點數": len(data),
                    "最新價格": f"{close_prices.iloc[-1]:.2f} HKD",
                    "期間最高價": f"{close_prices.max():.2f} HKD",
                    "期間最低價": f"{close_prices.min():.2f} HKD",
                    "期間漲跌幅": f"{((close_prices.iloc[-1] / close_prices.iloc[0] - 1) * 100):.2f}%",
                },
                "技術指標": {
                    "RSI(14)": f"{indicators.calculate_rsi(close_prices).iloc[-1]:.2f}",
                    "MACD線": f"{indicators.calculate_macd(close_prices)['macd'].iloc[-1]:.4f}",
                    "SMA(20)": f"{indicators.calculate_sma(close_prices, 20).iloc[-1]:.2f}",
                    "SMA(50)": f"{indicators.calculate_sma(close_prices, 50).iloc[-1]:.2f}",
                    "布林上軌": f"{indicators.calculate_bollinger_bands(close_prices)['upper'].iloc[-1]:.2f}",
                    "布林下軌": f"{indicators.calculate_bollinger_bands(close_prices)['lower'].iloc[-1]:.2f}",
                    "隨機K值": f"{indicators.calculate_stochastic(high_prices, low_prices, close_prices)['k_percent'].iloc[-1]:.2f}",
                    "隨機D值": f"{indicators.calculate_stochastic(high_prices, low_prices, close_prices)['d_percent'].iloc[-1]:.2f}",
                }
            }

            # 顯示報告
            for section, content in report_data.items():
                print(f"\n{self._get_colored_text(f'📋 {section}', 'cyan')}")
                print("-" * 25)

                if self.tabulate_available:
                    from tabulate import tabulate
                    section_data = [(key, str(value)) for key, value in content.items()]
                    print(tabulate(section_data, headers=["項目", "數值"], tablefmt="grid"))
                else:
                    for key, value in content.items():
                        print(f"  {key}: {value}")

            # 詢問是否導出報告
            export_report = self._get_user_input("\n是否導出報告到文件? (y/n)", ['y', 'n', 'Y', 'N'])
            if export_report.lower() in ['y', 'yes']:
                self._export_technical_report(symbol, report_data)

        except Exception as e:
            logger.error(f"詳細報告生成錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 詳細報告生成錯誤: {e}', 'red')}")

    def _export_technical_report(self, symbol: str, report_data: dict):
        """導出技術分析報告"""
        try:
            import json
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_technical_report_{timestamp}.json"
            filepath = Path("results") / filename
            filepath.parent.mkdir(exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"{self._get_colored_text('✅ 報告已導出:', 'green')} {filepath}")

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 導出報告失敗: {e}', 'red')}")

    # 輔助評分計算方法
    def _calculate_trend_score(self, close_prices, sma_20, sma_50):
        """計算趨勢評分"""
        try:
            current_price = close_prices.iloc[-1]
            trend_score = 0

            # 價格相對移動平均線位置
            if current_price > sma_20.iloc[-1]:
                trend_score += 20
            if current_price > sma_50.iloc[-1]:
                trend_score += 20
            if sma_20.iloc[-1] > sma_50.iloc[-1]:
                trend_score += 30

            # 近期趨勢強度
            recent_change = (close_prices.iloc[-5:].mean() - close_prices.iloc[-20:-5].mean()) / close_prices.iloc[-20:-5].mean()
            trend_score += min(max(recent_change * 1000, 0), 30)

            return min(max(trend_score, 0), 100)
        except:
            return 50

    def _calculate_momentum_score(self, rsi, macd_results):
        """計算動量評分"""
        try:
            momentum_score = 0

            # RSI動量
            rsi_value = rsi.iloc[-1]
            if 40 <= rsi_value <= 60:
                momentum_score += 30  # 中性區間給分
            elif 30 <= rsi_value <= 70:
                momentum_score += 20  # 偏向正常區間

            # MACD動量
            macd_value = macd_results['macd'].iloc[-1]
            if macd_value > 0:
                momentum_score += 25

            # MACD信號線
            if macd_results['macd'].iloc[-1] > macd_results['signal'].iloc[-1]:
                momentum_score += 25

            return min(max(momentum_score, 0), 100)
        except:
            return 50

    def _calculate_volatility_score(self, bb_results):
        """計算波動率評分"""
        try:
            width = bb_results['width'].iloc[-1]
            current_price = bb_results['upper'].iloc[-1] - bb_results['lower'].iloc[-1]

            # 適中的波動率給較高分數
            if 0.05 <= width <= 0.15:
                return 80
            elif 0.02 <= width <= 0.2:
                return 60
            else:
                return 40
        except:
            return 50

    def _calculate_overbought_score(self, rsi, stoch_results):
        """計算超買超賣評分"""
        try:
            overbought_score = 0

            # RSI評分
            rsi_value = rsi.iloc[-1]
            if 30 <= rsi_value <= 70:
                overbought_score += 50  # 正常區間給高分
            elif 25 <= rsi_value <= 75:
                overbought_score += 30

            # 隨機指標評分
            stoch_k = stoch_results['k_percent'].iloc[-1]
            stoch_d = stoch_results['d_percent'].iloc[-1]
            if 20 <= stoch_k <= 80 and 20 <= stoch_d <= 80:
                overbought_score += 50

            return min(max(overbought_score, 0), 100)
        except:
            return 50

    def _calculate_volume_score(self, data):
        """計算成交量評分"""
        try:
            if 'volume' in data.columns:
                volume = data['volume']
                recent_volume = volume.iloc[-5:].mean()
                avg_volume = volume.iloc[-20:].mean()

                volume_ratio = recent_volume / avg_volume
                if 0.8 <= volume_ratio <= 1.5:
                    return 80  # 正常成交量
                elif 0.5 <= volume_ratio <= 2:
                    return 60
                else:
                    return 40
            else:
                return 50
        except:
            return 50

    def government_data_menu(self):
        """增強的政府數據查看菜單 - Phase 2 Task 2.2"""
        print(f"\n{self._get_colored_text('🏛️ 政府數據查看 - 增強版', 'bold')}")
        print("-" * 40)

        while True:
            print(f"\n{self._get_colored_text('政府數據操作選項:', 'yellow')}")
            print("1. 📈 查看HIBOR利率")
            print("2. 💱 查看匯率數據")
            print("3. 💰 查看貨幣基礎數據")
            print("4. 📊 查看銀行流動資金")
            print("5. 🏛️ 查看所有數據源")
            print("6. 🔄 更新政府數據")
            print("7. 📋 數據來源信息")
            print("0. 🚪 返回主菜單")

            choice = self._get_user_input("請選擇操作 (0-7)", ['0', '1', '2', '3', '4', '5', '6', '7'])

            if choice == '0':
                break
            elif choice == '1':
                self._show_hibor_data()
            elif choice == '2':
                self._show_exchange_rate_data()
            elif choice == '3':
                self._show_monetary_base_data()
            elif choice == '4':
                self._show_liquidity_data()
            elif choice == '5':
                self._show_all_government_data()
            elif choice == '6':
                self._update_government_data()
            elif choice == '7':
                self._show_data_sources_info()

        input(f"\n{self._get_colored_text('按Enter繼續...', 'cyan')}")

    def _show_hibor_data(self):
        """顯示HIBOR利率數據"""
        print(f"\n{self._get_colored_text('📈 HIBOR利率數據', 'bold')}")
        print("-" * 30)

        try:
            if self.simplified_system_available:
                from simplified_system.src.api.government_data import get_hibor_data, get_latest_hibor

                print(f"{self._get_colored_text('🔄 正在獲取HIBOR數據...', 'yellow')}")

                # 獲取最新數據
                latest_hibor = get_latest_hibor()

                if latest_hibor:
                    print(f"{self._get_colored_text('✅ HIBOR數據獲取成功!', 'green')}")

                    # 顯示最新利率表格
                    print(f"\n{self._get_colored_text('📊 最新HIBOR利率', 'cyan')}")
                    print("=" * 40)

                    if self.tabulate_available:
                        from tabulate import tabulate

                        # 準備表格數據
                        hibor_rates = []
                        for key, value in latest_hibor.items():
                            if key != 'date' and value is not None:
                                period_map = {
                                    'overnight': '隔夜',
                                    '1_week': '1週',
                                    '1_month': '1個月',
                                    '3_months': '3個月',
                                    '6_months': '6個月',
                                    '12_months': '12個月'
                                }
                                period = period_map.get(key, key)
                                rate = f"{value:.3f}%" if isinstance(value, (int, float)) else str(value)
                                trend = self._get_rate_trend_indicator(value) if isinstance(value, (int, float)) else "N/A"
                                hibor_rates.append([period, rate, trend])

                        if hibor_rates:
                            headers = ["期限", "利率", "趨勢"]
                            print(tabulate(hibor_rates, headers=headers, tablefmt="grid"))
                    else:
                        # 簡單文本顯示
                        for key, value in latest_hibor.items():
                            if key != 'date' and value is not None:
                                print(f"  {key}: {value}%")

                    # 顯示數據時間
                    if 'date' in latest_hibor:
                        print(f"\n{self._get_colored_text('📅 數據日期:', 'yellow')} {latest_hibor['date']}")

                else:
                    print(f"{self._get_colored_text('❌ 無法獲取HIBOR數據', 'red')}")

                # 詢問是否查看歷史數據
                show_history = self._get_user_input("\n查看最近30天歷史數據? (y/n)", ['y', 'n', 'Y', 'N'])
                if show_history.lower() in ['y', 'yes']:
                    self._show_hibor_history()

            else:
                print(f"{self._get_colored_text('❌ Simplified System不可用', 'red')}")

        except Exception as e:
            logger.error(f"HIBOR數據顯示錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 錯誤: {e}', 'red')}")

    def _show_hibor_history(self):
        """顯示HIBOR歷史數據"""
        try:
            from simplified_system.src.api.government_data import get_hibor_data

            print(f"\n{self._get_colored_text('📈 最近30天HIBOR歷史數據', 'cyan')}")
            print("-" * 40)

            hibor_history = get_hibor_data(30)

            if hibor_history and hibor_history.get('data'):
                history_data = hibor_history['data']

                if self.tabulate_available:
                    from tabulate import tabulate

                    # 準備表格數據 (最近10天)
                    recent_data = history_data[:10]
                    table_data = []

                    for record in recent_data:
                        date = record.get('date', 'N/A')
                        overnight = f"{record.get('overnight', 0):.3f}%" if record.get('overnight') else "N/A"
                        one_month = f"{record.get('1_month', 0):.3f}%" if record.get('1_month') else "N/A"
                        three_months = f"{record.get('3_months', 0):.3f}%" if record.get('3_months') else "N/A"

                        table_data.append([date, overnight, one_month, three_months])

                    headers = ["日期", "隔夜", "1個月", "3個月"]
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    # 簡單文本顯示
                    for i, record in enumerate(history_data[:5]):
                        date = record.get('date', 'N/A')
                        overnight = record.get('overnight', 'N/A')
                        print(f"  {date}: 隔夜 {overnight}%")
                print(f"\n{self._get_colored_text(f'總記錄數: {len(history_data)}', 'yellow')}")
            else:
                print(f"{self._get_colored_text('❌ 無歷史數據', 'red')}")

        except Exception as e:
            logger.error(f"HIBOR歷史數據錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 歷史數據錯誤: {e}', 'red')}")

    def _get_rate_trend_indicator(self, rate: float) -> str:
        """獲取利率趨勢指示器"""
        try:
            # 這是一個簡單的趨勢指示器，實際應用中需要與歷史數據比較
            if rate > 4.5:
                return "📈 上漲"
            elif rate < 3.5:
                return "📉 下跌"
            else:
                return "➡️ 穩定"
        except:
            return "❓ 未知"

    def _show_exchange_rate_data(self):
        """顯示匯率數據"""
        print(f"\n{self._get_colored_text('💱 匯率數據', 'bold')}")
        print("-" * 30)

        try:
            if self.simplified_system_available:
                from simplified_system.src.api.government_data import government_api

                print(f"{self._get_colored_text('🔄 正在獲取匯率數據...', 'yellow')}")

                # 獲取匯率數據
                exchange_data = government_api.get_exchange_rates(7)  # 最近7天

                if exchange_data and exchange_data.get('data'):
                    print(f"{self._get_colored_text('✅ 匯率數據獲取成功!', 'green')}")

                    # 顯示最新匯率
                    latest_rates = exchange_data['data'][0] if exchange_data['data'] else {}

                    print(f"\n{self._get_colored_text('💰 最新匯率', 'cyan')}")
                    print("=" * 40)

                    if self.tabulate_available:
                        from tabulate import tabulate

                        # 準備表格數據
                        rate_data = []
                        for key, value in latest_rates.items():
                            if key != 'date' and value is not None:
                                currency_map = {
                                    'usd_hkd': 'USD/HKD',
                                    'cny_hkd': 'CNY/HKD',
                                    'eur_hkd': 'EUR/HKD',
                                    'gbp_hkd': 'GBP/HKD'
                                }
                                currency = currency_map.get(key, key.upper())
                                rate = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
                                rate_data.append([currency, rate])

                        if rate_data:
                            headers = ["貨幣對", "匯率"]
                            print(tabulate(rate_data, headers=headers, tablefmt="grid"))
                    else:
                        # 簡單文本顯示
                        for key, value in latest_rates.items():
                            if key != 'date' and value is not None:
                                print(f"  {key}: {value}")

                    # 顯示數據時間
                    if 'date' in latest_rates:
                        print(f"\n{self._get_colored_text('📅 數據日期:', 'yellow')} {latest_rates['date']}")
                else:
                    print(f"{self._get_colored_text('❌ 無法獲取匯率數據', 'red')}")

            else:
                print(f"{self._get_colored_text('❌ Simplified System不可用', 'red')}")

        except Exception as e:
            logger.error(f"匯率數據顯示錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 錯誤: {e}', 'red')}")

    def _show_monetary_base_data(self):
        """顯示貨幣基礎數據"""
        print(f"\n{self._get_colored_text('💰 貨幣基礎數據', 'bold')}")
        print("-" * 30)

        try:
            if self.simplified_system_available:
                from simplified_system.src.api.government_data import government_api

                print(f"{self._get_colored_text('🔄 正在獲取貨幣基礎數據...', 'yellow')}")

                # 獲取貨幣基礎數據
                monetary_data = government_api.get_monetary_base(12)  # 最近12個月

                if monetary_data and monetary_data.get('data'):
                    print(f"{self._get_colored_text('✅ 貨幣基礎數據獲取成功!', 'green')}")

                    # 顯示最新數據
                    latest_monetary = monetary_data['data'][0] if monetary_data['data'] else {}

                    print(f"\n{self._get_colored_text('📊 最新貨幣基礎指標', 'cyan')}")
                    print("=" * 50)

                    if self.tabulate_available:
                        from tabulate import tabulate

                        # 準備表格數據
                        monetary_stats = []
                        for key, value in latest_monetary.items():
                            if key != 'date' and value is not None:
                                indicator_map = {
                                    'monetary_base_billion_hkd': '貨幣基礎',
                                    'm1_billion_hkd': 'M1貨幣供應',
                                    'm2_billion_hkd': 'M2貨幣供應',
                                    'm3_billion_hkd': 'M3貨幣供應'
                                }
                                indicator = indicator_map.get(key, key)
                                amount = f"{value:,.2f} 億港元" if isinstance(value, (int, float)) else str(value)
                                monetary_stats.append([indicator, amount])

                        if monetary_stats:
                            headers = ["指標", "金額"]
                            print(tabulate(monetary_stats, headers=headers, tablefmt="grid"))
                    else:
                        # 簡單文本顯示
                        for key, value in latest_monetary.items():
                            if key != 'date' and value is not None:
                                print(f"  {key}: {value} 億港元")

                    # 顯示數據時間
                    if 'date' in latest_monetary:
                        print(f"\n{self._get_colored_text('📅 數據月份:', 'yellow')} {latest_monetary['date']}")
                else:
                    print(f"{self._get_colored_text('❌ 無法獲取貨幣基礎數據', 'red')}")

            else:
                print(f"{self._get_colored_text('❌ Simplified System不可用', 'red')}")

        except Exception as e:
            logger.error(f"貨幣基礎數據顯示錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 錯誤: {e}', 'red')}")

    def _show_liquidity_data(self):
        """顯示銀行流動資金數據"""
        print(f"\n{self._get_colored_text('📊 銀行流動資金數據', 'bold')}")
        print("-" * 30)

        try:
            # 這裡可以擴展來顯示更多流動性數據
            print(f"{self._get_colored_text('🔄 正在獲取流動資金數據...', 'yellow')}")

            # 顯示數據來源信息
            print(f"\n{self._get_colored_text('📊 數據來源:', 'cyan')}")
            print("-" * 20)
            print("香港金融管理局 (HKMA)")
            print("銀行同業流動資金數據")
            print("https://api.hkma.gov.hk")

            # 顯示說明
            print(f"\n{self._get_colored_text('📖 數據說明:', 'yellow')}")
            print("-" * 15)
            print("銀行同業流動資金數據反映香港銀行系統的流動性狀況")
            print("包括結餘總額、外匯基金票據及債券等指標")

            # 詢問是否查看詳細數據
            show_detail = self._get_user_input("\n查看詳細流動性數據? (需要更多API集成) (y/n)", ['y', 'n', 'Y', 'N'])
            if show_detail.lower() in ['y', 'yes']:
                print(f"{self._get_colored_text('🔄 功能開發中...', 'yellow')}")
                print("詳細流動性數據分析功能將在後續版本中實現")

        except Exception as e:
            logger.error(f"流動資金數據顯示錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 錯誤: {e}', 'red')}")

    def _show_all_government_data(self):
        """顯示所有政府數據"""
        print(f"\n{self._get_colored_text('🏛️ 所有政府數據源概覽', 'bold')}")
        print("-" * 40)

        try:
            if self.simplified_system_available:
                from simplified_system.src.data.government_data import government_collector

                print(f"{self._get_colored_text('🔄 正在檢查所有數據源...', 'yellow')}")

                # 顯示所有可用的數據源
                data_sources = government_collector.data_sources

                print(f"\n{self._get_colored_text('📊 可用數據源列表', 'cyan')}")
                print("=" * 60)

                if self.tabulate_available:
                    from tabulate import tabulate

                    # 準備表格數據
                    source_data = []
                    for i, source in enumerate(data_sources, 1):
                        priority_map = {1: "高", 2: "中", 3: "低"}
                        priority = priority_map.get(source.priority, "未知")
                        source_data.append([
                            i,
                            source.name,
                            source.data_type,
                            priority,
                            source.refresh_interval
                        ])

                    headers = ["#", "數據源名稱", "數據類型", "優先級", "更新頻率"]
                    print(tabulate(source_data, headers=headers, tablefmt="grid"))
                else:
                    # 簡單文本顯示
                    for i, source in enumerate(data_sources, 1):
                        print(f"  {i}. {source.name} ({source.data_type})")

                # 顯示統計信息
                print(f"\n{self._get_colored_text('📈 數據源統計', 'yellow')}")
                print("-" * 20)
                print(f"  總數據源數量: {len(data_sources)}")
                print(f"  高優先級數據源: {len([s for s in data_sources if s.priority == 1])}")
                print(f"  中優先級數據源: {len([s for s in data_sources if s.priority == 2])}")
                print(f"  低優先級數據源: {len([s for s in data_sources if s.priority == 3])}")

                # 提供選擇查看特定數據源的選項
                print(f"\n{self._get_colored_text('🔍 查看特定數據源:', 'yellow')}")
                for i, source in enumerate(data_sources, 1):
                    print(f"  {i}. {source.name}")

                source_choice = self._get_user_input(f"選擇數據源 (1-{len(data_sources)}) 或 0 返回",
                                                   [str(i) for i in range(len(data_sources) + 1)])

                if source_choice != '0':
                    source_index = int(source_choice) - 1
                    if 0 <= source_index < len(data_sources):
                        selected_source = data_sources[source_index]
                        self._show_source_details(selected_source)

            else:
                print(f"{self._get_colored_text('❌ Simplified System不可用', 'red')}")

        except Exception as e:
            logger.error(f"所有政府數據顯示錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 錯誤: {e}', 'red')}")

    def _show_source_details(self, source):
        """顯示特定數據源詳細信息"""
        print(f"\n{self._get_colored_text('📊 數據源詳細信息', 'bold')}")
        print("-" * 30)

        # 顯示數據源信息
        details = [
            ("數據源名稱", source.name),
            ("數據類型", source.data_type),
            ("API URL", source.url),
            ("更新頻率", source.refresh_interval),
            ("優先級", {1: "高", 2: "中", 3: "低"}.get(source.priority, "未知"))
        ]

        if self.tabulate_available:
            from tabulate import tabulate
            print(tabulate(details, tablefmt="grid"))
        else:
            for label, value in details:
                print(f"  {label}: {value}")

    def _update_government_data(self):
        """更新政府數據"""
        print(f"\n{self._get_colored_text('🔄 更新政府數據', 'bold')}")
        print("-" * 30)

        try:
            print(f"{self._get_colored_text('⚠️ 注意: 數據更新將從HKMA官方API獲取最新數據', 'yellow')}")
            print(f"{self._get_colored_text('這可能需要幾分鐘時間...', 'yellow')}")

            confirm = self._get_user_input("\n確認更新所有政府數據? (y/n)", ['y', 'n', 'Y', 'N'])

            if confirm.lower() in ['y', 'yes']:
                print(f"\n{self._get_colored_text('🚀 開始更新政府數據...', 'yellow')}")

                # 顯示進度
                import asyncio
                from simplified_system.src.data.government_data import collect_all_government_data

                # 運行異步數據收集
                async def update_data():
                    print("   正在連接HKMA API...")
                    results = await collect_all_government_data()

                    successful = sum(1 for r in results if r.success)
                    total_records = sum(r.record_count for r in results if r.success)

                    print(f"\n{self._get_colored_text('✅ 數據更新完成!', 'green')}")
                    print(f"  成功收集: {successful}/{len(results)} 個數據源")
                    print(f"  總記錄數: {total_records}")

                    # 顯示詳細結果
                    if self.tabulate_available:
                        from tabulate import tabulate

                        result_data = []
                        for result in results:
                            status = "✅ 成功" if result.success else "❌ 失敗"
                            records = str(result.record_count) if result.success else result.error_message or "未知錯誤"
                            result_data.append([result.source_name, status, records])

                        headers = ["數據源", "狀態", "記錄數/錯誤"]
                        print(f"\n{self._get_colored_text('📊 更新結果詳情:', 'cyan')}")
                        print(tabulate(result_data, headers=headers, tablefmt="grid"))

                    return results

                # 運行更新
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        print(f"{self._get_colored_text('⚠️ 檢測到事件循環正在運行，使用其他方法...', 'yellow')}")
                        # 創建新的事件循環
                        asyncio.run(update_data())
                    else:
                        loop.run_until_complete(update_data())
                except Exception as async_error:
                    print(f"{self._get_colored_text(f'⚠️ 異步更新失敗: {async_error}', 'yellow')}")
                    print(f"{self._get_colored_text('嘗試使用同步方法...', 'yellow')}")
                    # 這裡可以添加同步方法的備用實現

            else:
                print(f"{self._get_colored_text('❌ 取消更新', 'red')}")

        except Exception as e:
            logger.error(f"政府數據更新錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 更新錯誤: {e}', 'red')}")

    def _show_data_sources_info(self):
        """顯示數據源信息"""
        print(f"\n{self._get_colored_text('📋 數據源信息', 'bold')}")
        print("-" * 30)

        try:
            print(f"\n{self._get_colored_text('🏛️ 香港金融管理局 (HKMA) 數據源', 'cyan')}")
            print("=" * 50)

            sources_info = [
                {
                    "name": "HIBOR利率",
                    "description": "香港銀行同業拆息利率",
                    "endpoint": "/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily",
                    "update_freq": "每日",
                    "priority": "高"
                },
                {
                    "name": "匯率數據",
                    "description": "港幣兌主要貨幣匯率",
                    "endpoint": "/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily",
                    "update_freq": "每日",
                    "priority": "高"
                },
                {
                    "name": "貨幣基礎",
                    "description": "香港貨幣基礎統計數據",
                    "endpoint": "/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-monetary-base",
                    "update_freq": "每日",
                    "priority": "高"
                },
                {
                    "name": "銀行流動資金",
                    "description": "銀行同業流動資金狀況",
                    "endpoint": "/public/market-data-and-statistics/daily-monetary-statistics/daily-figures-interbank-liquidity",
                    "update_freq": "每日",
                    "priority": "中"
                },
                {
                    "name": "外匯基金票據",
                    "description": "外匯基金票據及債券數據",
                    "endpoint": "/public/market-data-and-statistics/monthly-statistical-bulletin/efbn/efbn-yield-daily",
                    "update_freq": "每日",
                    "priority": "中"
                },
                {
                    "name": "人民幣流動資金",
                    "description": "人民幣流動資金安排使用情況",
                    "endpoint": "/public/market-data-and-statistics/daily-monetary-statistics/usage-rmb-liquidity-fac",
                    "update_freq": "每日",
                    "priority": "低"
                }
            ]

            if self.tabulate_available:
                from tabulate import tabulate

                # 準備表格數據
                table_data = []
                for source in sources_info:
                    table_data.append([
                        source["name"],
                        source["description"],
                        source["update_freq"],
                        source["priority"]
                    ])

                headers = ["數據源", "描述", "更新頻率", "優先級"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))

                print(f"\n{self._get_colored_text('🔗 API端點信息:', 'cyan')}")
                print("-" * 20)
                for source in sources_info:
                    print(f"{source['name']}: {source['endpoint']}")
            else:
                # 簡單文本顯示
                for source in sources_info:
                    print(f"\n📊 {source['name']} (優先級: {source['priority']})")
                    print(f"   描述: {source['description']}")
                    print(f"   更新頻率: {source['update_freq']}")

            print(f"\n{self._get_colored_text('🌐 API基礎URL:', 'yellow')}")
            print("https://api.hkma.gov.hk")

            print(f"\n{self._get_colored_text('📖 數據使用說明:', 'cyan')}")
            print("-" * 20)
            print("1. 所有數據均來自香港金融管理局官方API")
            print("2. 數據為公開信息，可用於研究和分析")
            print("3. 建議在商業使用前查看HKMA的使用條款")
            print("4. 數據更新頻率可能因HKMA維護而有所變化")

        except Exception as e:
            logger.error(f"數據源信息顯示錯誤: {e}")
            print(f"{self._get_colored_text(f'❌ 錯誤: {e}', 'red')}")

    def system_status_menu(self):
        """系統狀態檢查菜單"""
        print(f"\n{self._get_colored_text('⚙️ 系統狀態檢查', 'bold')}")
        print("-" * 30)

        print(f"{self._get_colored_text('🔧 依賴檢查', 'bold')}")
        print("-" * 20)

        # 檢查核心依賴
        dependencies = [
            ("Python", sys.version.split()[0], "✅" if True else "❌"),
            ("Pandas", self.pandas_available, "✅" if self.pandas_available else "❌"),
            ("Simplified System", self.simplified_system_available, "✅" if self.simplified_system_available else "❌"),
            ("GPU加速", self.gpu_available, "✅" if self.gpu_available else "❌"),
            ("VectorBT", self.vectorbt_available, "✅" if self.vectorbt_available else "❌"),
            ("Tabulate", self.tabulate_available, "✅" if self.tabulate_available else "❌")
        ]

        if self.tabulate_available:
            from tabulate import tabulate
            headers = ["組件", "版本/狀態", "可用性"]
            print(tabulate(dependencies, headers=headers, tablefmt="grid"))
        else:
            for name, status, available in dependencies:
                status_icon = "✅" if available else "❌"
                print(f"  {name}: {status} {status_icon}")

        print(f"\n{self._get_colored_text('📊 系統配置', 'bold')}")
        print("-" * 20)

        print(f"  配置文件: {self.config_file}")
        print(f"  配置存在: {'✅' if self.config_file.exists() else '❌'}")
        print(f"  默認股票: {self.config.get('default_symbol', 'N/A')}")
        print(f"  默認時長: {self.config.get('default_duration', 'N/A')} 天")
        print(f"  輸出格式: {self.config.get('output_format', 'table')}")

        print(f"\n{self._get_colored_text('🚀 性能指標', 'bold')}")
        print("-" * 20)

        # 顯示內存使用情況
        try:
            import psutil
            memory_info = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)

            print(f"  CPU使用率: {cpu_percent:.1f}%")
            print(f"  內存使用: {memory_info.percent:.1f}%")
            print(f"  可用內存: {memory_info.available / 1024**3:.1f} GB")
            print(f"  總內存: {memory_info.total / 1024**3:.1f} GB")
        except ImportError:
            print("  psutil庫不可用，無法獲取系統性能信息")
        except Exception as e:
            print(f"  系統性能檢查錯誤: {e}")

        input(f"\n{self._get_colored_text('按Enter繼續...', 'cyan')}")

    def run(self):
        """運行主程序"""
        try:
            while True:
                self._print_header()
                self._print_main_menu()

                choice = self._get_user_input(
                    "請選擇功能 (0-8)",
                    ['0', '1', '2', '3', '4', '5', '6', '7', '8', 'h', 'help', 'q', 'quit']
                )

                if choice in ['0', 'q', 'quit']:
                    print(f"\n{self._get_colored_text('感謝使用香港量化交易系統!', 'green')}")
                    print(f"{self._get_colored_text('再見! 👋', 'cyan')}")
                    break
                elif choice == '1':
                    self.stock_data_menu()
                elif choice == '2':
                    self.technical_indicators_menu()
                elif choice == '3':
                    self.backtest_menu()
                elif choice == '4':
                    self.government_data_menu()
                elif choice == '5':
                    self.system_status_menu()
                elif choice == '6':
                    self.config_management_menu()
                elif choice == '7':
                    self.dependency_management_menu()
                elif choice == '8':
                    self.gpu_acceleration_menu()
                elif choice in ['h', 'help']:
                    self._show_help()
                else:
                    # 支持快捷輸入股票代碼
                    if choice and choice[0].isdigit() and len(choice) <= 4:
                        # 可能是股票代碼，嘗試快速獲取
                        self.stock_data_menu()
                    else:
                        print(f"{self._get_colored_text('⚠️  無效選擇', 'yellow')}")
                        time.sleep(1)

        except KeyboardInterrupt:
            print(f"\n\n{self._get_colored_text('👋 用戶中斷，系統即將退出...', 'yellow')}")
        except Exception as e:
            logger.error(f"系統運行錯誤: {e}")
            print(f"\n{self._get_colored_text(f'系統錯誤: {e}', 'red')}")
        finally:
            print(f"\n{self._get_colored_text('系統已退出', 'bold')}")

    def config_management_menu(self):
        """配置管理菜單"""
        if self.config_menu:
            try:
                self.config_menu.show_config_menu(self)
            except Exception as e:
                print(f"{self._get_colored_text(f'❌ 配置管理錯誤: {e}', 'red')}")
                input(f"{self._get_colored_text('按Enter返回主菜單...', 'cyan')}")
        else:
            print(f"\n{self._get_colored_text('🛠️  配置管理', 'bold')}")
            print("-" * 30)
            print(f"{self._get_colored_text('配置管理系統不可用', 'red')}")
            print(f"請檢查配置管理模塊是否正確安裝")
            input(f"\n{self._get_colored_text('按Enter返回主菜單...', 'cyan')}")

    def dependency_management_menu(self):
        """依賴管理菜單"""
        if self.dependency_menu:
            try:
                self.dependency_menu.show_dependency_menu(self)
            except Exception as e:
                print(f"{self._get_colored_text(f'❌ 依賴管理錯誤: {e}', 'red')}")
                input(f"{self._get_colored_text('按Enter返回主菜單...', 'cyan')}")
        else:
            print(f"\n{self._get_colored_text('📦 依賴管理', 'bold')}")
            print("-" * 30)
            print(f"{self._get_colored_text('依賴管理系統不可用', 'red')}")
            print(f"請檢查依賴管理模塊是否正確安裝")
            input(f"\n{self._get_colored_text('按Enter返回主菜單...', 'cyan')}")

    def gpu_acceleration_menu(self):
        """GPU加速支持菜單 - Phase 4 Task 4.3"""
        try:
            # 導入GPU菜單系統
            sys.path.insert(0, str(Path(__file__).parent / "src" / "gpu"))
            from gpu_menu_system import show_gpu_menu

            # 顯示GPU菜單
            show_gpu_menu()

        except Exception as e:
            print(f"\n{self._get_colored_text('🖥️  GPU加速支持', 'bold')}")
            print("-" * 40)
            print(f"{self._get_colored_text(f'❌ GPU菜單系統錯誤: {e}', 'red')}")

            # 顯示基本的GPU狀態
            print(f"\n{self._get_colored_text('基本GPU狀態:', 'yellow')}")
            if self.gpu_available:
                print(f"✅ GPU檢測: 可用")
            else:
                print(f"❌ GPU檢測: 不可用")

            if self.vectorbt_available:
                print(f"✅ VectorBT GPU支持: 可用")
            else:
                print(f"❌ VectorBT GPU支持: 不可用")

            input(f"\n{self._get_colored_text('按Enter返回主菜單...', 'cyan')}")

    def backtest_menu(self):
        """回測策略優化菜單 - Phase 4實現"""
        while True:
            print(f"\n{self._get_colored_text('🔄 回測策略優化', 'bold')}")
            print("-" * 50)

            # 檢查VectorBT可用性
            vectorbt_status = self._check_vectorbt_availability()
            if vectorbt_status['available']:
                print(f"✅ VectorBT引擎: {vectorbt_status['version']}")
            else:
                print(f"❌ VectorBT引擎: 不可用 ({vectorbt_status['message']})")
                print(f"   請先安裝: pip install vectorbt")
                input(f"\n{self._get_colored_text('按Enter返回主菜單...', 'cyan')}")
                return

            print(f"\n{self._get_colored_text('📊 回測功能選項:', 'cyan')}")
            print("1. 單策略回測")
            print("2. 參數優化")
            print("3. 多策略對比")
            print("4. 策略性能分析")
            print("5. 回測配置管理")
            print("6. 批量回測")
            print("0. 返回主菜單")

            choice = input(f"\n{self._get_colored_text('請選擇功能 [0-6]:', 'yellow')}")

            if choice == "0":
                break
            elif choice == "1":
                self._single_strategy_backtest()
            elif choice == "2":
                self._parameter_optimization()
            elif choice == "3":
                self._multi_strategy_comparison()
            elif choice == "4":
                self._strategy_performance_analysis()
            elif choice == "5":
                self._backtest_configuration()
            elif choice == "6":
                self._batch_backtest()
            else:
                print(f"{self._get_colored_text('無效選擇，請重試', 'red')}")

    def _check_vectorbt_availability(self):
        """檢查VectorBT可用性"""
        try:
            # 使用依賴管理器檢查
            if hasattr(self, 'dependency_manager') and self.dependency_manager:
                vectorbt_info = self.dependency_manager.check_dependency('vectorbt')
                return vectorbt_info
            else:
                # 手動檢查
                import vectorbt as vbt
                return {
                    'available': True,
                    'version': getattr(vbt, '__version__', 'unknown'),
                    'message': 'OK'
                }
        except ImportError as e:
            return {
                'available': False,
                'version': None,
                'message': str(e)
            }
        except Exception as e:
            return {
                'available': False,
                'version': None,
                'message': f'Error: {e}'
            }

    def _single_strategy_backtest(self):
        """單策略回測"""
        print(f"\n{self._get_colored_text('📈 單策略回測', 'bold')}")
        print("-" * 40)

        try:
            # 選擇股票
            symbol = self._select_stock()
            if not symbol:
                return

            # 選擇策略
            strategy = self._select_strategy()
            if not strategy:
                return

            # 設置參數
            params = self._set_strategy_parameters(strategy)
            if params is None:
                return

            # 獲取數據
            print(f"\n{self._get_colored_text('正在獲取數據...', 'yellow')}")
            data = self._get_stock_data(symbol)
            if data is None or len(data) == 0:
                print(f"{self._get_colored_text('❌ 無法獲取數據', 'red')}")
                return

            print(f"✅ 獲取數據: {len(data)} 條記錄")

            # 執行回測
            print(f"\n{self._get_colored_text('正在執行回測...', 'yellow')}")
            result = self._execute_backtest(data, strategy, params, symbol)

            if result:
                # 顯示結果
                self._display_backtest_result(result)

                # 詢問是否保存
                if self._ask_save_result():
                    self._save_backtest_result(result)

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 回測失敗: {e}', 'red')}")
            logger.error(f"Single strategy backtest error: {e}")

        input(f"\n{self._get_colored_text('按Enter繼續...', 'cyan')}")

    def _select_stock(self):
        """選擇股票"""
        print(f"\n{self._get_colored_text('選擇股票:', 'cyan')}")
        print("1. 使用默認股票 (0700.HK)")
        print("2. 輸入股票代碼")
        print("3. 從常用股票選擇")
        print("0. 返回")

        choice = input(f"\n{self._get_colored_text('請選擇 [0-3]:', 'yellow')}")

        if choice == "0":
            return None
        elif choice == "1":
            return "0700.HK"
        elif choice == "2":
            symbol = input(f"{self._get_colored_text('請輸入股票代碼 (如 0700.HK):', 'yellow')}")
            return symbol.upper() if symbol else None
        elif choice == "3":
            return self._select_from_popular_stocks()
        else:
            return None

    def _select_from_popular_stocks(self):
        """從常用股票選擇"""
        popular_stocks = [
            ("0700.HK", "騰訊控股"),
            ("0941.HK", "中國移動"),
            ("1299.HK", "友邦保險"),
            ("2318.HK", "中國平安"),
            ("0388.HK", "港交所"),
            ("1398.HK", "工商銀行"),
            ("0939.HK", "建設銀行"),
            ("0005.HK", "匯豐控股")
        ]

        print(f"\n{self._get_colored_text('常用港股:', 'cyan')}")
        for i, (code, name) in enumerate(popular_stocks, 1):
            print(f"{i}. {code} - {name}")

        try:
            # Use secure input validation
            if INPUT_VALIDATOR_AVAILABLE:
                valid_options = [str(i) for i in range(1, len(popular_stocks) + 1)]
                choice_input = input(f"\n{self._get_colored_text('請選擇 [1-8]:', 'yellow')}").strip()

                if choice_input in valid_options:
                    choice = int(choice_input)
                    if 1 <= choice <= len(popular_stocks):
                        return popular_stocks[choice-1][0]
            else:
                # Fallback validation with additional safety
                try:
                    choice_input = input(f"\n{self._get_colored_text('請選擇 [1-8]:', 'yellow')}").strip()
                    # Additional safety check
                    if choice_input.isdigit():
                        choice = int(choice_input)
                    else:
                        raise ValueError("Invalid input format")
                    if 1 <= choice <= len(popular_stocks):
                        return popular_stocks[choice-1][0]
                except (ValueError, IndexError):
                    pass
        except (ValueError, IndexError):
            pass

        return None

    def _select_strategy(self):
        """選擇策略"""
        strategies = {
            "1": {
                "name": "RSI均值回歸",
                "code": "RSI_MEAN_REVERSION",
                "description": "基於RSI的超買超賣信號進行均值回歸交易"
            },
            "2": {
                "name": "雙移動平均",
                "code": "DUAL_MOVING_AVERAGE",
                "description": "基於短期和長期移動平均線的交叉信號"
            },
            "3": {
                "name": "MACD交叉",
                "code": "MACD_CROSSOVER",
                "description": "基於MACD指標的金叉死叉信號"
            },
            "4": {
                "name": "布林帶策略",
                "code": "BOLLINGER_BANDS",
                "description": "基於布林帶的突破信號"
            },
            "5": {
                "name": "動量突破",
                "code": "MOMENTUM_BREAKOUT",
                "description": "基於價格動量的突破策略"
            },
            "6": {
                "name": "波動率突破",
                "code": "VOLATILITY_BREAKOUT",
                "description": "基於ATR的波動率突破策略"
            }
        }

        print(f"\n{self._get_colored_text('可用策略:', 'cyan')}")
        for key, strategy in strategies.items():
            print(f"{key}. {strategy['name']} - {strategy['description']}")

        choice = input(f"\n{self._get_colored_text('請選擇策略 [1-6]:', 'yellow')}")

        if choice in strategies:
            return strategies[choice]['code']
        else:
            print(f"{self._get_colored_text('無效選擇', 'red')}")
            return None

    def _set_strategy_parameters(self, strategy):
        """設置策略參數"""
        print(f"\n{self._get_colored_text('設置策略參數:', 'cyan')}")

        # 預定義參數模板
        default_params = {
            "RSI_MEAN_REVERSION": {
                "period": 14,
                "oversold": 30,
                "overbought": 70
            },
            "DUAL_MOVING_AVERAGE": {
                "short_period": 20,
                "long_period": 50
            },
            "MACD_CROSSOVER": {
                "fast": 12,
                "slow": 26,
                "signal": 9
            },
            "BOLLINGER_BANDS": {
                "period": 20,
                "std_dev": 2.0
            },
            "MOMENTUM_BREAKOUT": {
                "lookback": 20,
                "threshold": 0.02
            },
            "VOLATILITY_BREAKOUT": {
                "atr_period": 14,
                "multiplier": 2.0
            }
        }

        params = default_params.get(strategy, {})

        print(f"當前參數: {params}")
        print(f"1. 使用默認參數")
        print(f"2. 自定義參數")
        print(f"3. 從配置加載參數")
        print(f"0. 返回")

        choice = input(f"\n{self._get_colored_text('請選擇 [0-3]:', 'yellow')}")

        if choice == "0":
            return None
        elif choice == "1":
            return params
        elif choice == "2":
            return self._customize_parameters(strategy, params)
        elif choice == "3":
            return self._load_parameters_from_config(strategy)

        return params

    def _customize_parameters(self, strategy, default_params):
        """自定義參數"""
        print(f"\n{self._get_colored_text('自定義策略參數:', 'cyan')}")

        try:
            customized_params = {}

            for param, default_value in default_params.items():
                while True:
                    user_input = input(
                        f"{param} (默認: {default_value}): "
                    ).strip()

                    if not user_input:
                        customized_params[param] = default_value
                        break

                    try:
                        if isinstance(default_value, float):
                            # Use secure float validation
                            if INPUT_VALIDATOR_AVAILABLE:
                                validator = get_input_validator()
                                # Determine parameter type for validation
                                if param.endswith('_period') or 'rsi' in param.lower():
                                    customized_params[param] = validator.validate_parameter_range(
                                        param, user_input, "float", 0.1, 100.0
                                    )
                                else:
                                    # Generic float validation
                                    customized_params[param] = safe_input_float(
                                        f"Please enter {param}: ", min_val=-1000.0, max_val=1000.0
                                    )
                            else:
                                # Fallback validation
                                customized_params[param] = float(user_input)
                        elif isinstance(default_value, int):
                            # Use secure integer validation
                            if INPUT_VALIDATOR_AVAILABLE:
                                validator = get_input_validator()
                                if 'period' in param.lower() or 'length' in param.lower():
                                    customized_params[param] = validator.validate_parameter_range(
                                        param, user_input, "int", 1, 1000
                                    )
                                else:
                                    # Generic integer validation
                                    customized_params[param] = safe_input_int(
                                        f"Please enter {param}: ", min_val=-10000, max_val=10000
                                    )
                            else:
                                # Fallback validation
                                customized_params[param] = int(user_input)
                        else:
                            customized_params[param] = user_input
                        break
                    except (ValueError, Exception) as e:
                        print(f"{self._get_colored_text('無效輸入，請重新輸入', 'red')}")

            return customized_params

        except Exception as e:
            print(f"{self._get_colored_text(f'參數設置失敗: {e}'), 'red'}")
            return default_params

    def _load_parameters_from_config(self, strategy):
        """從配置加載參數"""
        try:
            if hasattr(self, 'config_manager') and self.config_manager:
                # 從配置管理器加載策略參數
                strategy_params = self.config_manager.get(f"backtest.strategies.{strategy}", {})
                if strategy_params:
                    print(f"✅ 從配置加載參數: {strategy_params}")
                    return strategy_params

            print(f"{self._get_colored_text('未找到保存的參數，使用默認值', 'yellow')}")
            return self._set_strategy_parameters(strategy)

        except Exception as e:
            print(f"{self._get_colored_text(f'加載配置失敗: {e}', 'red')}")
            return None

    def _get_stock_data(self, symbol, duration=365):
        """獲取股票數據 - 集成Phase 2功能"""
        try:
            # 嘗試從simplified_system獲取數據
            from simplified_system.src.api.stock_api import get_hk_stock_data

            data = get_hk_stock_data(symbol, duration)
            if data is not None and len(data) > 0:
                return data

            # 如果simplified_system不可用，嘗試其他方法
            print(f"{self._get_colored_text('simplified_system不可用，嘗試其他方法...', 'yellow')}")

            # 可以在這裡添加其他數據源
            return None

        except Exception as e:
            print(f"{self._get_colored_text(f'獲取數據失敗: {e}', 'red')}")
            logger.error(f"Get stock data error: {e}")
            return None

    def _execute_backtest(self, data, strategy, params, symbol):
        """執行回測 - 集成VectorBT引擎"""
        try:
            # 導入VectorBT引擎
            from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine

            # 初始化引擎
            engine = VectorBTEngine()

            # 執行回測
            result = engine.backtest_strategy(data, strategy, params, symbol)

            return result

        except Exception as e:
            print(f"{self._get_colored_text(f'回測執行失敗: {e}', 'red')}")
            logger.error(f"Execute backtest error: {e}")
            return None

    def _display_backtest_result(self, result):
        """顯示回測結果"""
        try:
            from tabulate import tabulate

            print(f"\n{self._get_colored_text('📊 回測結果', 'bold')}")
            print("=" * 50)

            # 基本信息
            basic_info = [
                ["股票代碼", result.symbol],
                ["策略名稱", result.strategy_name],
                ["回測期間", f"{result.start_date} 至 {result.end_date}"],
                ["數據點數", result.data_points],
                ["執行時間", f"{result.execution_time:.3f}秒"]
            ]

            print(f"\n{self._get_colored_text('基本信息:', 'cyan')}")
            print(tabulate(basic_info, headers=["項目", "值"], tablefmt="grid"))

            # 性能指標
            performance_data = [
                ["總收益率", f"{result.total_return:.2%}"],
                ["年化收益率", f"{result.annual_return:.2%}"],
                ["夏普比率", f"{result.sharpe_ratio:.3f}"],
                ["最大回撤", f"{result.max_drawdown:.2%}"],
                ["Calmar比率", f"{result.calmar_ratio:.3f}"],
                ["Sortino比率", f"{result.sortino_ratio:.3f}"],
                ["勝率", f"{result.win_rate:.2%}"],
                ["盈利因子", f"{result.profit_factor:.2f}"],
                ["交易次數", result.total_trades]
            ]

            print(f"\n{self._get_colored_text('性能指標:', 'cyan')}")
            print(tabulate(performance_data, headers=["指標", "數值"], tablefmt="grid"))

            # 參數信息
            param_data = [[k, v] for k, v in result.parameters.items()]
            print(f"\n{self._get_colored_text('策略參數:', 'cyan')}")
            print(tabulate(param_data, headers=["參數", "數值"], tablefmt="grid"))

        except Exception as e:
            print(f"{self._get_colored_text(f'結果顯示失敗: {e}', 'red')}")
            logger.error(f"Display backtest result error: {e}")

    def _ask_save_result(self):
        """詢問是否保存結果"""
        choice = input(f"\n{self._get_colored_text('是否保存回測結果? [y/N]:', 'yellow')}").lower()
        return choice in ['y', 'yes', '是']

    def _save_backtest_result(self, result):
        """保存回測結果"""
        try:
            import json
            from datetime import datetime

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backtest_{result.symbol}_{result.strategy_name}_{timestamp}.json"
            filepath = Path("results") / filename

            # 創建results目錄
            filepath.parent.mkdir(exist_ok=True)

            # 保存結果
            result_data = result.to_dict()
            result_data['timestamp'] = timestamp

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 結果已保存至: {filepath}")

            # 保存到配置
            if hasattr(self, 'config_manager') and self.config_manager:
                self.config_manager.set(
                    f"backtest.last_results.{result.strategy_name}",
                    result_data
                )

        except Exception as e:
            print(f"{self._get_colored_text(f'保存失敗: {e}', 'red')}")
            logger.error(f"Save backtest result error: {e}")

    def _parameter_optimization(self):
        """Phase 4 參數優化集成系統"""
        print(f"\n{self._get_colored_text('🎯 Phase 4 參數優化集成系統', 'bold')}")
        print("-" * 60)

        try:
            # 導入優化菜單系統
            import sys
            from pathlib import Path

            # 添加優化模塊路徑
            optimization_path = Path(__file__).parent / "src" / "optimization"
            if str(optimization_path) not in sys.path:
                sys.path.insert(0, str(optimization_path))

            try:
                from optimization_menu import OptimizationMenu

                print(f"✅ 參數優化系統已啟動")
                print(f"🚀 支持功能:")
                print(f"   • 大規模參數優化 (1000+ 組合)")
                print(f"   • 實時進度顯示")
                print(f"   • 多策略並行比較")
                print(f"   • GPU加速支持")
                print(f"   • 結果分析和導出")

                input(f"\n{self._get_colored_text('按Enter進入參數優化菜單...', 'cyan')}")

                # 啟動優化菜單
                menu = OptimizationMenu()
                menu.show_menu()

            except ImportError as e:
                print(f"❌ 無法導入優化系統: {e}")
                print(f"🔄 降級到基礎優化功能...")

                # 使用基礎優化功能作為備用
                self._basic_parameter_optimization()

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 參數優化系統錯誤: {e}', 'red')}")
            logger.error(f"Parameter optimization system error: {e}")

            # 嘗試基礎功能作為備用
            try:
                print(f"\n{self._get_colored_text('🔄 嘗試基礎優化功能...', 'yellow')}")
                self._basic_parameter_optimization()
            except Exception as backup_e:
                print(f"{self._get_colored_text(f'❌ 基礎優化也失敗: {backup_e}', 'red')}")

    def _basic_parameter_optimization(self):
        """基礎參數優化（備用功能）"""
        print(f"\n{self._get_colored_text('⚡ 基礎參數優化', 'bold')}")
        print("-" * 40)

        try:
            # 選擇股票
            symbol = self._select_stock()
            if not symbol:
                return

            # 選擇策略
            strategy = self._select_strategy()
            if not strategy:
                return

            # 設置參數範圍
            param_ranges = self._set_parameter_ranges(strategy)
            if not param_ranges:
                return

            # 選擇優化指標
            optimization_metric = self._select_optimization_metric()
            if not optimization_metric:
                return

            # 獲取數據
            print(f"\n{self._get_colored_text('正在獲取數據...', 'yellow')}")
            data = self._get_stock_data(symbol)
            if data is None or len(data) == 0:
                print(f"{self._get_colored_text('❌ 無法獲取數據', 'red')}")
                return

            print(f"✅ 獲取數據: {len(data)} 條記錄")

            # 執行優化
            print(f"\n{self._get_colored_text('正在執行參數優化...', 'yellow')}")
            optimization_result = self._execute_optimization(
                data, strategy, param_ranges, symbol, optimization_metric
            )

            if optimization_result:
                # 顯示優化結果
                self._display_optimization_result(optimization_result)

                # 詢問是否保存
                if self._ask_save_result():
                    self._save_optimization_result(optimization_result)

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 基礎參數優化失敗: {e}', 'red')}")
            logger.error(f"Basic parameter optimization error: {e}")

        input(f"\n{self._get_colored_text('按Enter繼續...', 'cyan')}")

    def _set_parameter_ranges(self, strategy):
        """設置參數範圍"""
        print(f"\n{self._get_colored_text('設置參數範圍:', 'cyan')}")

        # 預定義參數範圍
        default_ranges = {
            "RSI_MEAN_REVERSION": {
                "period": "range(10, 31, 2)",  # 10-30，步長2
                "oversold": "[20, 25, 30, 35]",
                "overbought": "[65, 70, 75, 80]"
            },
            "DUAL_MOVING_AVERAGE": {
                "short_period": "range(10, 31, 5)",  # 10-30，步長5
                "long_period": "range(40, 101, 10)"  # 40-100，步長10
            },
            "MACD_CROSSOVER": {
                "fast": "range(8, 17, 2)",
                "slow": "range(20, 31, 3)",
                "signal": "range(7, 13, 2)"
            },
            "BOLLINGER_BANDS": {
                "period": "range(15, 26, 5)",
                "std_dev": "[1.5, 2.0, 2.5, 3.0]"
            },
            "MOMENTUM_BREAKOUT": {
                "lookback": "range(10, 31, 5)",
                "threshold": "[0.01, 0.015, 0.02, 0.025, 0.03]"
            },
            "VOLATILITY_BREAKOUT": {
                "atr_period": "range(10, 21, 5)",
                "multiplier": "[1.5, 2.0, 2.5, 3.0]"
            }
        }

        default_range = default_ranges.get(strategy, {})
        print(f"默認參數範圍: {default_range}")
        print(f"1. 使用默認範圍")
        print(f"2. 自定義範圍")
        print(f"0. 返回")

        choice = input(f"\n{self._get_colored_text('請選擇 [0-2]:', 'yellow')}")

        if choice == "0":
            return None
        elif choice == "1":
            return self._parse_parameter_ranges(default_range)
        elif choice == "2":
            return self._customize_parameter_ranges(default_range)

        return None

    def _parse_parameter_ranges(self, range_dict):
        """解析參數範圍"""
        try:
            # Use secure parameter parser if available
            if SECURE_PARSER_AVAILABLE:
                return parse_parameter_ranges_safe(range_dict)

            # Fallback to safe parsing without eval()
            parsed_ranges = {}
            for param, range_str in range_dict.items():
                # Validate parameter name
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param):
                    logger.warning(f"Invalid parameter name: {param}")
                    return None

                # Parse safely without eval()
                parsed_value = self._safe_parse_range_string(range_str)
                if parsed_value is None:
                    logger.warning(f"Failed to parse range for parameter {param}: {range_str}")
                    return None

                parsed_ranges[param] = parsed_value

            return parsed_ranges
        except Exception as e:
            print(f"{self._get_colored_text(f'參數範圍解析失敗: {e}', 'red')}")
            return None

    def _safe_parse_range_string(self, range_str):
        """Safely parse range string without eval()"""
        range_str = range_str.strip()

        # Handle range() function
        if range_str.startswith('range'):
            return self._parse_range_function(range_str)

        # Handle list literals
        elif range_str.startswith('['):
            return self._parse_list_literal(range_str)

        # Handle single values
        else:
            return [range_str]

    def _parse_range_function(self, range_str):
        """Parse range() function safely"""
        import re
        pattern = r'^range\(\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)$'
        match = re.match(pattern, range_str)

        if not match:
            logger.warning(f"Invalid range format: {range_str}")
            return None

        try:
            start = int(match.group(1))
            end = int(match.group(2))
            step = int(match.group(3)) if match.group(3) else 1

            # Validate range parameters
            if start < 0 or end < 0 or step <= 0:
                logger.warning(f"Invalid range parameters: start={start}, end={end}, step={step}")
                return None

            if start >= end:
                logger.warning(f"Range start must be less than end: start={start}, end={end}")
                return None

            # Limit range size
            range_size = (end - start + step - 1) // step
            if range_size > 10000:
                logger.warning(f"Range too large: {range_size} elements")
                return None

            return list(range(start, end, step))

        except ValueError as e:
            logger.warning(f"Invalid range parameters: {e}")
            return None

    def _parse_list_literal(self, list_str):
        """Parse list literal safely"""
        import re
        pattern = r'^\[\s*(.*?)\s*\]$'
        match = re.match(pattern, list_str)

        if not match:
            logger.warning(f"Invalid list format: {list_str}")
            return None

        try:
            content = match.group(1).strip()
            if not content:
                return []

            # Parse comma-separated values
            values = []
            for value_str in content.split(','):
                value_str = value_str.strip()
                if not value_str:
                    continue

                parsed_value = self._parse_single_value(value_str)
                if parsed_value is None:
                    return None
                values.append(parsed_value)

            # Limit list size
            if len(values) > 1000:
                logger.warning(f"List too large: {len(values)} elements")
                return None

            return values

        except Exception as e:
            logger.warning(f"List parsing failed: {e}")
            return None

    def _parse_single_value(self, value_str):
        """Parse single value safely"""
        value_str = value_str.strip()

        if not value_str:
            return None

        # Try integer
        if re.match(r'^-?\d+$', value_str):
            try:
                return int(value_str)
            except ValueError:
                pass

        # Try float
        if re.match(r'^-?\d*\.\d+$', value_str):
            try:
                return float(value_str)
            except ValueError:
                pass

        # Try string (quoted)
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]  # Remove quotes

        # Unquoted string (validate safety)
        if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value_str):
            return value_str

        logger.warning(f"Invalid value format: {value_str}")
        return None

    def _customize_parameter_ranges(self, default_range):
        """自定義參數範圍"""
        print(f"\n{self._get_colored_text('自定義參數範圍:', 'cyan')}")
        print("輸入格式示例:")
        print("  - range(10, 31, 2)  # 從10到30，步長2")
        print("  - [20, 25, 30, 35]  # 列表值")

        customized_ranges = {}
        for param, default_value in default_range.items():
            while True:
                user_input = input(f"{param} (默認: {default_value}): ").strip()

                if not user_input:
                    # 使用默認值
                    parsed = self._parse_parameter_ranges({param: default_value})
                    if parsed:
                        customized_ranges.update(parsed)
                        break
                    else:
                        continue

                # 驗證輸入
                try:
                    # 嘗試解析用戶輸入
                    test_ranges = {param: user_input}
                    parsed = self._parse_parameter_ranges(test_ranges)
                    if parsed:
                        customized_ranges.update(parsed)
                        break
                    else:
                        print(f"{self._get_colored_text('無效格式，請重新輸入', 'red')}")
                except:
                    print(f"{self._get_colored_text('無效格式，請重新輸入', 'red')}")

        return customized_ranges

    def _select_optimization_metric(self):
        """選擇優化指標"""
        metrics = {
            "1": {"name": "夏普比率", "code": "sharpe_ratio"},
            "2": {"name": "總收益率", "code": "total_return"},
            "3": {"name": "最大回撤", "code": "max_drawdown"},
            "4": {"name": "Calmar比率", "code": "calmar_ratio"},
            "5": {"name": "Sortino比率", "code": "sortino_ratio"}
        }

        print(f"\n{self._get_colored_text('優化目標:', 'cyan')}")
        for key, metric in metrics.items():
            print(f"{key}. {metric['name']}")

        choice = input(f"\n{self._get_colored_text('請選擇優化目標 [1-5]:', 'yellow')}")

        if choice in metrics:
            return metrics[choice]['code']
        else:
            return None

    def _execute_optimization(self, data, strategy, param_ranges, symbol, metric):
        """執行參數優化"""
        try:
            # 導入VectorBT引擎
            from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine

            # 初始化引擎
            engine = VectorBTEngine()

            # 執行優化
            result = engine.optimize_parameters(
                data=data,
                strategy=strategy,
                param_ranges=param_ranges,
                symbol=symbol,
                optimization_metric=metric,
                max_combinations=1000,  # 限制最大組合數
                use_vectorbt_opt=True  # 使用VectorBT原生優化
            )

            return result

        except Exception as e:
            print(f"{self._get_colored_text(f'優化執行失敗: {e}', 'red')}")
            logger.error(f"Execute optimization error: {e}")
            return None

    def _display_optimization_result(self, result):
        """顯示優化結果"""
        try:
            from tabulate import tabulate

            print(f"\n{self._get_colored_text('⚡ 參數優化結果', 'bold')}")
            print("=" * 50)

            # 優化統計
            stats_data = [
                ["策略", result['strategy']],
                ["股票", result['symbol']],
                ["總組合數", result['total_combinations']],
                ["成功組合數", result['successful_combinations']],
                ["優化時間", f"{result['optimization_time']:.2f}秒"],
                ["優化方法", result.get('optimization_method', 'Unknown')]
            ]

            print(f"\n{self._get_colored_text('優化統計:', 'cyan')}")
            print(tabulate(stats_data, headers=["項目", "值"], tablefmt="grid"))

            # 最佳參數
            best_params = result['best_parameters']
            param_data = [[k, v] for k, v in best_params.items()]
            print(f"\n{self._get_colored_text('最佳參數:', 'cyan')}")
            print(tabulate(param_data, headers=["參數", "數值"], tablefmt="grid"))

            # 最佳性能
            best_performance = result['best_performance']
            perf_data = [
                [k, f"{v:.3f}" if isinstance(v, float) else v]
                for k, v in best_performance.items()
            ]
            print(f"\n{self._get_colored_text('最佳性能:', 'cyan')}")
            print(tabulate(perf_data, headers=["指標", "數值"], tablefmt="grid"))

            # 性能統計
            if 'performance_statistics' in result:
                stats = result['performance_statistics']
                stats_table = [
                    ["平均值", f"{stats['mean']:.4f}"],
                    ["標準差", f"{stats['std']:.4f}"],
                    ["最小值", f"{stats['min']:.4f}"],
                    ["最大值", f"{stats['max']:.4f}"],
                    ["中位數", f"{stats['median']:.4f}"]
                ]
                print(f"\n{self._get_colored_text('性能統計:', 'cyan')}")
                print(tabulate(stats_table, headers=["統計項", "數值"], tablefmt="grid"))

        except Exception as e:
            print(f"{self._get_colored_text(f'優化結果顯示失敗: {e}', 'red')}")
            logger.error(f"Display optimization result error: {e}")

    def _save_optimization_result(self, result):
        """保存優化結果"""
        try:
            import json
            from datetime import datetime

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimization_{result['symbol']}_{result['strategy']}_{timestamp}.json"
            filepath = Path("results") / filename

            # 創建results目錄
            filepath.parent.mkdir(exist_ok=True)

            # 保存結果
            result_data = dict(result)
            result_data['timestamp'] = timestamp

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 優化結果已保存至: {filepath}")

            # 保存到配置
            if hasattr(self, 'config_manager') and self.config_manager:
                self.config_manager.set(
                    f"backtest.last_optimization.{result['strategy']}",
                    result_data
                )

        except Exception as e:
            print(f"{self._get_colored_text(f'優化結果保存失敗: {e}', 'red')}")
            logger.error(f"Save optimization result error: {e}")

    def _multi_strategy_comparison(self):
        """多策略對比功能"""
        print(f"\n{self._get_colored_text('📊 多策略對比', 'bold')}")
        print("-" * 40)

        try:
            # 選擇股票
            symbol = self._select_stock()
            if not symbol:
                return

            # 選擇多個策略
            strategies = self._select_multiple_strategies()
            if not strategies:
                return

            # 獲取數據
            print(f"\n{self._get_colored_text('正在獲取數據...', 'yellow')}")
            data = self._get_stock_data(symbol)
            if data is None or len(data) == 0:
                print(f"{self._get_colored_text('❌ 無法獲取數據', 'red')}")
                return

            print(f"✅ 獲取數據: {len(data)} 條記錄")

            # 執行多策略回測
            print(f"\n{self._get_colored_text('正在執行多策略回測...', 'yellow')}")
            comparison_results = self._execute_multi_strategy_comparison(
                data, strategies, symbol
            )

            if comparison_results:
                # 顯示對比結果
                self._display_comparison_results(comparison_results)

                # 詢問是否保存
                if self._ask_save_result():
                    self._save_comparison_results(comparison_results)

        except Exception as e:
            print(f"{self._get_colored_text(f'❌ 多策略對比失敗: {e}', 'red')}")
            logger.error(f"Multi strategy comparison error: {e}")

        input(f"\n{self._get_colored_text('按Enter繼續...', 'cyan')}")

    def _select_multiple_strategies(self):
        """選擇多個策略"""
        print(f"\n{self._get_colored_text('選擇多個策略 (用逗號分隔):', 'cyan')}")

        strategies = {
            "1": {"name": "RSI均值回歸", "code": "RSI_MEAN_REVERSION"},
            "2": {"name": "雙移動平均", "code": "DUAL_MOVING_AVERAGE"},
            "3": {"name": "MACD交叉", "code": "MACD_CROSSOVER"},
            "4": {"name": "布林帶策略", "code": "BOLLINGER_BANDS"},
            "5": {"name": "動量突破", "code": "MOMENTUM_BREAKOUT"},
            "6": {"name": "波動率突破", "code": "VOLATILITY_BREAKOUT"}
        }

        for key, strategy in strategies.items():
            print(f"{key}. {strategy['name']}")

        choice = input(f"\n{self._get_colored_text('請選擇策略 [1-6，多選用逗號分隔]:', 'yellow')}")

        try:
            selected_codes = []
            for c in choice.split(','):
                c = c.strip()
                if c in strategies:
                    selected_codes.append(strategies[c]['code'])

            if selected_codes:
                print(f"✅ 已選擇策略: {', '.join(selected_codes)}")
                return selected_codes
            else:
                print(f"{self._get_colored_text('未選擇有效策略', 'red')}")
                return None

        except Exception:
            print(f"{self._get_colored_text('輸入格式錯誤', 'red')}")
            return None

    def _execute_multi_strategy_comparison(self, data, strategies, symbol):
        """執行多策略對比"""
        try:
            from simplified_system.src.backtest.vectorbt_engine import VectorBTEngine

            # 初始化引擎
            engine = VectorBTEngine()

            # 預定義默認參數
            default_params = {
                "RSI_MEAN_REVERSION": {"period": 14, "oversold": 30, "overbought": 70},
                "DUAL_MOVING_AVERAGE": {"short_period": 20, "long_period": 50},
                "MACD_CROSSOVER": {"fast": 12, "slow": 26, "signal": 9},
                "BOLLINGER_BANDS": {"period": 20, "std_dev": 2.0},
                "MOMENTUM_BREAKOUT": {"lookback": 20, "threshold": 0.02},
                "VOLATILITY_BREAKOUT": {"atr_period": 14, "multiplier": 2.0}
            }

            results = []
            for strategy in strategies:
                try:
                    print(f"  正在測試: {strategy}")
                    params = default_params.get(strategy, {})
                    result = engine.backtest_strategy(data, strategy, params, symbol)
                    results.append(result)
                except Exception as e:
                    print(f"  ❌ {strategy} 測試失敗: {e}")
                    continue

            return results if results else None

        except Exception as e:
            print(f"{self._get_colored_text(f'多策略對比執行失敗: {e}', 'red')}")
            logger.error(f"Execute multi strategy comparison error: {e}")
            return None

    def _display_comparison_results(self, results):
        """顯示對比結果"""
        try:
            from tabulate import tabulate

            print(f"\n{self._get_colored_text('📊 多策略對比結果', 'bold')}")
            print("=" * 60)

            # 準備對比數據
            comparison_data = []
            for result in results:
                comparison_data.append([
                    result.strategy_name,
                    f"{result.total_return:.2%}",
                    f"{result.sharpe_ratio:.3f}",
                    f"{result.max_drawdown:.2%}",
                    f"{result.annual_return:.2%}",
                    f"{result.win_rate:.2%}",
                    result.total_trades,
                    f"{result.execution_time:.3f}s"
                ])

            # 排序（按夏普比率）
            comparison_data.sort(key=lambda x: float(x[2]), reverse=True)

            headers = [
                "策略", "總回報", "夏普比率", "最大回撤",
                "年化回報", "勝率", "交易次數", "執行時間"
            ]

            print(tabulate(comparison_data, headers=headers, tablefmt="grid"))

            # 找出最佳策略
            if comparison_data:
                best_strategy = comparison_data[0]
                print(f"\n🏆 {self._get_colored_text('最佳策略:', 'yellow')} {best_strategy[0]}")
                print(f"   夏普比率: {best_strategy[2]}, 總回報: {best_strategy[1]}")

        except Exception as e:
            print(f"{self._get_colored_text(f'對比結果顯示失敗: {e}', 'red')}")
            logger.error(f"Display comparison results error: {e}")

    def _save_comparison_results(self, results):
        """保存對比結果"""
        try:
            import json
            from datetime import datetime

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparison_multi_strategy_{timestamp}.json"
            filepath = Path("results") / filename

            # 創建results目錄
            filepath.parent.mkdir(exist_ok=True)

            # 準備保存數據
            save_data = {
                'timestamp': timestamp,
                'symbol': results[0].symbol if results else 'Unknown',
                'strategies_count': len(results),
                'results': [result.to_dict() for result in results]
            }

            # 保存結果
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 對比結果已保存至: {filepath}")

        except Exception as e:
            print(f"{self._get_colored_text(f'對比結果保存失敗: {e}', 'red')}")
            logger.error(f"Save comparison results error: {e}")

    def _strategy_performance_analysis(self):
        """策略性能分析功能"""
        print(f"\n{self._get_colored_text('📈 策略性能分析', 'bold')}")
        print("-" * 40)
        print(f"{self._get_colored_text('功能開發中...', 'yellow')}")
        input(f"\n{self._get_colored_text('按Enter返回...', 'cyan')}")

    def _backtest_configuration(self):
        """回測配置管理功能"""
        print(f"\n{self._get_colored_text('⚙️ 回測配置管理', 'bold')}")
        print("-" * 40)
        print(f"{self._get_colored_text('功能開發中...', 'yellow')}")
        input(f"\n{self._get_colored_text('按Enter返回...', 'cyan')}")

    def _batch_backtest(self):
        """批量回測功能"""
        print(f"\n{self._get_colored_text('🔄 批量回測', 'bold')}")
        print("-" * 40)
        print(f"{self._get_colored_text('功能開發中...', 'yellow')}")
        input(f"\n{self._get_colored_text('按Enter返回...', 'cyan')}")

def main():
    """主函數"""
    try:
        # 創建並運行互動式交易系統
        trader = InteractiveQuantitativeTrader()
        trader.run()
    except Exception as e:
        print(f"系統啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()