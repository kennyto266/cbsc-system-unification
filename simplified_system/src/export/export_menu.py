#!/usr / bin / env python3
"""
簡化系統 - 導出菜單集成模塊
提供用戶友好的導出功能界面
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)


class ExportMenu:
    """導出菜單類"""

    def __init__(self, export_manager = None):
        self.export_manager = export_manager
        if self.export_manager is None:
            # 初始化導出管理器
            try:
                from .export_manager import ExportManager

                self.export_manager = ExportManager()
            except Exception as e:
                logger.error(f"導出管理器初始化失敗: {e}")
                raise

        self.menu_options = {
            "1": "導出回測結果",
            "2": "導出技術指標數據",
            "3": "批量導出多股票數據",
            "4": "導出優化結果",
            "5": "導出自定義數據",
            "6": "導出設置管理",
            "7": "查看導出歷史",
            "8": "批量操作模式",
            "0": "返回主菜單",
        }

    def display_menu(self):
        """顯示導出菜單"""
        print("\n" + "=" * 60)
        print("           📊 量化交易系統 - 數據導出中心")
        print("=" * 60)

        for key, value in self.menu_options.items():
            icon = self._get_menu_icon(key)
            print(f"  {icon} {key}. {value}")

        print("\n" + "-" * 60)
        print(
            f"📁 默認輸出目錄: {self.export_manager.config.get('export_settings', {}).get('output_directory', 'exports')}"
        )
        print(
            f"📄 默認格式: {self.export_manager.config.get('export_settings', {}).get('default_format', 'xlsx')}"
        )
        print(
            f"⏰ 自動時間戳: {'啟用' if self.export_manager.config.get('export_settings', {}).get('auto_timestamp', True) else '禁用'}"
        )
        print("-" * 60)

    def _get_menu_icon(self, key: str) -> str:
        """獲取菜單項圖標"""
        icons = {
            "1": "📈",
            "2": "📊",
            "3": "📦",
            "4": "⚡",
            "5": "🔧",
            "6": "⚙️",
            "7": "📜",
            "8": "🚀",
            "0": "🔙",
        }
        return icons.get(key, "📋")

    def run_menu(self):
        """運行導出菜單"""
        while True:
            try:
                self.display_menu()
                choice = input("\n請選擇操作 (0 - 8): ").strip()

                if choice == "0":
                    print("👋 返回主菜單...")
                    break
                elif choice in self.menu_options:
                    self._handle_menu_choice(choice)
                else:
                    print("❌ 無效選擇，請輸入 0 - 8 之間的數字")
                    time.sleep(1)

            except KeyboardInterrupt:
                print("\n\n⚠️ 用戶中斷操作")
                break
            except Exception as e:
                logger.error(f"菜單操作錯誤: {e}")
                print(f"❌ 操作失敗: {e}")
                time.sleep(2)

    def _handle_menu_choice(self, choice: str):
        """處理菜單選擇"""
        handlers = {
            "1": self._export_backtest_results,
            "2": self._export_technical_indicators,
            "3": self._batch_export_stocks,
            "4": self._export_optimization_results,
            "5": self._export_custom_data,
            "6": self._manage_export_settings,
            "7": self._view_export_history,
            "8": self._batch_operation_mode,
        }

        handler = handlers.get(choice)
        if handler:
            print(f"\n🚀 {self.menu_options[choice]}")
            print("-" * 40)
            handler()

    def _export_backtest_results(self):
        """導出回測結果"""
        try:
            print("\n📈 導出回測結果")
            print("=" * 30)

            # 選擇數據源
            print("1. 使用模擬回測數據")
            print("2. 從文件加載回測結果")
            print("3. 從數據庫加載回測結果")

            data_source = input("請選擇數據源 (1 - 3): ").strip()

            # 獲取回測數據
            backtest_data = self._get_backtest_data(data_source)
            if backtest_data is None:
                return

            # 選擇導出格式
            format_choice = self._choose_export_format()
            if format_choice is None:
                return

            # 輸入文件名
            filename = input("請輸入文件名 (留空使用默認): ").strip()
            if not filename:
                filename = f"backtest_results_{time.strftime('%Y%m%d_%H%M%S')}"

            print(f"\n🔄 正在導出回測結果...")
            result = self.export_manager.export_backtest_results(
                backtest_data, format_choice, filename
            )

            self._display_export_result(result)

        except Exception as e:
            logger.error(f"導出回測結果失敗: {e}")
            print(f"❌ 導出失敗: {e}")

    def _export_technical_indicators(self):
        """導出技術指標數據"""
        try:
            print("\n📊 導出技術指標數據")
            print("=" * 30)

            # 輸入股票代碼
            symbol = input("請輸入股票代碼 (如 0700.HK): ").strip()
            if not symbol:
                symbol = "0700.HK"
                print(f"使用默認股票代碼: {symbol}")

            # 獲取技術指標數據
            print("📡 正在獲取技術指標數據...")
            indicators_data = self._get_technical_indicators_data(symbol)
            if indicators_data is None:
                print("❌ 無法獲取技術指標數據")
                return

            # 選擇導出格式
            format_choice = self._choose_export_format()
            if format_choice is None:
                return

            # 輸入文件名
            filename = input("請輸入文件名 (留空使用默認): ").strip()
            if not filename:
                filename = (
                    f"technical_indicators_{symbol}_{time.strftime('%Y%m%d_%H%M%S')}"
                )

            print(f"\n🔄 正在導出技術指標數據...")
            result = self.export_manager.export_technical_indicators(
                indicators_data, symbol, format_choice, filename
            )

            self._display_export_result(result)

        except Exception as e:
            logger.error(f"導出技術指標失敗: {e}")
            print(f"❌ 導出失敗: {e}")

    def _batch_export_stocks(self):
        """批量導出多股票數據"""
        try:
            print("\n📦 批量導出多股票數據")
            print("=" * 30)

            # 輸入股票列表
            stocks_input = input(
                "請輸入股票代碼列表 (用逗號分隔，如 0700.HK,0941.HK): "
            ).strip()
            if not stocks_input:
                stocks_input = "0700.HK,0941.HK,1398.HK"
                print(f"使用默認股票列表: {stocks_input}")

            symbols = [s.strip() for s in stocks_input.split(",") if s.strip()]

            # 選擇導出格式
            format_choice = self._choose_export_format()
            if format_choice is None:
                return

            print(f"\n🔄 正在批量導出 {len(symbols)} 只股票的數據...")
            results = []

            for i, symbol in enumerate(symbols, 1):
                print(f"處理第 {i}/{len(symbols)} 只股票: {symbol}")

                try:
                    # 獲取股票數據
                    stock_data = self._get_stock_data(symbol)
                    if stock_data is None:
                        print(f"⚠️ 跳過 {symbol}: 無法獲取數據")
                        continue

                    # 導出數據
                    filename = f"stock_data_{symbol}_{time.strftime('%Y%m%d_%H%M%S')}"
                    result = self.export_manager.export_technical_indicators(
                        stock_data, symbol, format_choice, filename
                    )
                    results.append((symbol, result))

                except Exception as e:
                    logger.error(f"處理 {symbol} 失敗: {e}")
                    results.append((symbol, None))

            # 顯示批量導出結果
            print(f"\n📊 批量導出結果:")
            print("-" * 40)
            success_count = 0
            for symbol, result in results:
                if result and result.success:
                    print(f"✅ {symbol}: {result.filename}")
                    success_count += 1
                else:
                    error_msg = result.error_message if result else "未知錯誤"
                    print(f"❌ {symbol}: {error_msg}")

            print(f"\n🎯 總計: {success_count}/{len(symbols)} 成功導出")

        except Exception as e:
            logger.error(f"批量導出失敗: {e}")
            print(f"❌ 批量導出失敗: {e}")

    def _export_optimization_results(self):
        """導出優化結果"""
        try:
            print("\n⚡ 導出優化結果")
            print("=" * 30)

            # 選擇優化結果文件
            optimization_files = self._find_optimization_files()
            if not optimization_files:
                print("❌ 未找到優化結果文件")
                return

            print("找到以下優化結果文件:")
            for i, file_path in enumerate(optimization_files[:10], 1):  # 最多顯示10個
                print(f"  {i}. {file_path.name}")

            if len(optimization_files) > 10:
                print(f"  ... 還有 {len(optimization_files) - 10} 個文件")

            choice = input(
                f"\n請選擇文件 (1-{min(10, len(optimization_files))}): "
            ).strip()
            try:
                file_index = int(choice) - 1
                if 0 <= file_index < min(10, len(optimization_files)):
                    selected_file = optimization_files[file_index]
                else:
                    print("❌ 無效選擇")
                    return
            except ValueError:
                print("❌ 請輸入有效數字")
                return

            # 加載優化結果
            print(f"📂 正在加載 {selected_file.name}...")
            optimization_data = self._load_optimization_results(selected_file)
            if optimization_data is None:
                return

            # 選擇導出格式
            format_choice = self._choose_export_format()
            if format_choice is None:
                return

            # 輸入文件名
            filename = input("請輸入文件名 (留空使用默認): ").strip()
            if not filename:
                filename = f"optimization_results_{selected_file.stem}_{time.strftime('%Y%m%d_%H%M%S')}"

            print(f"\n🔄 正在導出優化結果...")
            result = self.export_manager.export_backtest_results(
                optimization_data, format_choice, filename
            )

            self._display_export_result(result)

        except Exception as e:
            logger.error(f"導出優化結果失敗: {e}")
            print(f"❌ 導出失敗: {e}")

    def _export_custom_data(self):
        """導出自定義數據"""
        try:
            print("\n🔧 導出自定義數據")
            print("=" * 30)

            print("1. 導入JSON文件")
            print("2. 導入CSV文件")
            print("3. 手動輸入數據")
            print("4. 從API獲取數據")

            data_source = input("請選擇數據源 (1 - 4): ").strip()

            # 獲取自定義數據
            custom_data = self._get_custom_data(data_source)
            if custom_data is None:
                return

            # 選擇導出格式
            format_choice = self._choose_export_format()
            if format_choice is None:
                return

            # 輸入文件名
            filename = input("請輸入文件名: ").strip()
            if not filename:
                print("❌ 文件名不能為空")
                return

            print(f"\n🔄 正在導出自定義數據...")
            from .export_manager import ExportRequest

            request = ExportRequest(
                data = custom_data,
                format = format_choice,
                filename = filename,
                metadata={"source": "custom", "timestamp": time.time()},
            )

            result = self.export_manager.export(request)
            self._display_export_result(result)

        except Exception as e:
            logger.error(f"導出自定義數據失敗: {e}")
            print(f"❌ 導出失敗: {e}")

    def _manage_export_settings(self):
        """管理導出設置"""
        try:
            print("\n⚙️ 導出設置管理")
            print("=" * 30)

            settings = self.export_manager.config.get("export_settings", {})

            print(f"當前導出設置:")
            print(f"1. 默認格式: {settings.get('default_format', 'xlsx')}")
            print(f"2. 輸出目錄: {settings.get('output_directory', 'exports')}")
            print(
                f"3. 自動時間戳: {'啟用' if settings.get('auto_timestamp', True) else '禁用'}"
            )
            print(
                f"4. 包含圖表: {'啟用' if settings.get('include_charts', True) else '禁用'}"
            )
            print(
                f"5. 包含原始數據: {'啟用' if settings.get('include_raw_data', False) else '禁用'}"
            )
            print(f"6. 語言: {settings.get('language', 'zh - CN')}")

            print("\n選擇要修改的設置 (1 - 6) 或 0 返回:")
            choice = input("請選擇: ").strip()

            if choice == "0":
                return
            elif choice in ["1", "2", "3", "4", "5", "6"]:
                self._update_export_setting(choice)
            else:
                print("❌ 無效選擇")

        except Exception as e:
            logger.error(f"設置管理失敗: {e}")
            print(f"❌ 設置失敗: {e}")

    def _view_export_history(self):
        """查看導出歷史"""
        try:
            print("\n📜 導出歷史")
            print("=" * 30)

            output_dir = Path(
                self.export_manager.config.get("export_settings", {}).get(
                    "output_directory", "exports"
                )
            )
            if not output_dir.exists():
                print("❌ 輸出目錄不存在")
                return

            # 獲取導出文件列表
            export_files = []
            for ext in ["*.xlsx", "*.pdf", "*.json", "*.csv", "*.html"]:
                export_files.extend(output_dir.glob(ext))

            # 按修改時間排序
            export_files.sort(key = lambda x: x.stat().st_mtime, reverse = True)

            if not export_files:
                print("📭 暫無導出文件")
                return

            print(f"最近 {min(20, len(export_files))} 個導出文件:")
            print("-" * 60)
            print(f"{'文件名':<30} {'格式':<8} {'大小':<10} {'修改時間':<20}")
            print("-" * 60)

            for file_path in export_files[:20]:
                file_size = file_path.stat().st_size
                file_size_str = self._format_file_size(file_size)
                mod_time = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(file_path.stat().st_mtime)
                )
                file_ext = file_path.suffix[1:].upper()

                print(
                    f"{file_path.name:<30} {file_ext:<8} {file_size_str:<10} {mod_time:<20}"
                )

            print(f"\n📁 總共 {len(export_files)} 個導出文件")
            print(
                f"💾 總大小: {self._format_file_size(sum(f.stat().st_size for f in export_files))}"
            )

        except Exception as e:
            logger.error(f"查看導出歷史失敗: {e}")
            print(f"❌ 查看失敗: {e}")

    def _batch_operation_mode(self):
        """批量操作模式"""
        try:
            print("\n🚀 批量操作模式")
            print("=" * 30)

            print("批量操作功能:")
            print("1. 批量轉換格式")
            print("2. 批量合併文件")
            print("3. 批量生成報告")
            print("4. 批量壓縮文件")

            operation = input("請選擇操作 (1 - 4): ").strip()

            if operation == "1":
                self._batch_convert_format()
            elif operation == "2":
                self._batch_merge_files()
            elif operation == "3":
                self._batch_generate_reports()
            elif operation == "4":
                self._batch_compress_files()
            else:
                print("❌ 無效選擇")

        except Exception as e:
            logger.error(f"批量操作失敗: {e}")
            print(f"❌ 批量操作失敗: {e}")

    # 輔助方法
    def _choose_export_format(self) -> Optional[str]:
        """選擇導出格式"""
        formats = self.export_manager.get_supported_formats()
        print(f"\n📄 支持的導出格式:")
        for i, fmt in enumerate(formats, 1):
            print(f"  {i}. {fmt.upper()}")

        choice = input(f"請選擇格式 (1-{len(formats)}): ").strip()
        try:
            format_index = int(choice) - 1
            if 0 <= format_index < len(formats):
                return formats[format_index]
            else:
                print("❌ 無效選擇")
                return None
        except ValueError:
            print("❌ 請輸入有效數字")
            return None

    def _display_export_result(self, result):
        """顯示導出結果"""
        if result.success:
            print(f"\n✅ 導出成功!")
            print(f"📁 文件路徑: {result.file_path}")
            print(f"📊 文件大小: {self._format_file_size(result.file_size)}")
            if result.record_count is not None:
                print(f"📝 記錄數量: {result.record_count:,}")
            if result.export_time is not None:
                print(f"⏱️ 導出耗時: {result.export_time:.2f} 秒")

            # 詢問是否打開文件
            open_file = input("\n是否打開文件? (y / N): ").strip().lower()
            if open_file in ["y", "yes"]:
                self._open_file(result.file_path)
        else:
            print(f"\n❌ 導出失敗!")
            print(f"錯誤信息: {result.error_message}")

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _open_file(self, file_path: str):
        """打開文件"""
        try:
            import platform
            import subprocess

            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", file_path])
            else:  # Linux
                subprocess.run(["xdg - open", file_path])
        except Exception as e:
            logger.error(f"打開文件失敗: {e}")
            print(f"⚠️ 無法打開文件: {e}")

    # 數據獲取方法（這裡是模擬實現，實際應用中需要集成真實的數據源）
    def _get_backtest_data(self, source: str) -> Optional[Dict]:
        """獲取回測數據"""
        if source == "1":
            # 模擬回測數據
            return self._generate_mock_backtest_data()
        elif source == "2":
            # 從文件加載
            return self._load_backtest_from_file()
        elif source == "3":
            # 從數據庫加載
            return self._load_backtest_from_database()
        else:
            print("❌ 無效選擇")
            return None

    def _generate_mock_backtest_data(self) -> Dict:
        """生成模擬回測數據"""
        from datetime import datetime

        import numpy as np
        import pandas as pd

        # 生成日期範圍
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2024, 12, 31)
        dates = pd.date_range(start_date, end_date, freq="D")

        # 生成模擬數據
        n_days = len(dates)
        returns = np.random.normal(0.001, 0.02, n_days)
        portfolio_value = np.cumprod(1 + returns) * 100000

        # 創建交易記錄
        n_trades = 50
        trade_dates = np.random.choice(dates, n_trades, replace = False)
        trades = []
        for i, trade_date in enumerate(trade_dates):
            trades.append(
                {
                    "date": trade_date.strftime("%Y-%m-%d"),
                    "action": "BUY" if i % 2 == 0 else "SELL",
                    "symbol": "0700.HK",
                    "quantity": np.random.randint(100, 1000),
                    "price": round(np.random.uniform(300, 600), 2),
                    "pnl": round(np.random.uniform(-5000, 5000), 2),
                }
            )

        return {
            "summary": {
                "total_return": 0.156,
                "annual_return": 0.142,
                "sharpe_ratio": 1.23,
                "max_drawdown": -0.085,
                "volatility": 0.186,
                "win_rate": 0.58,
                "trade_count": n_trades,
            },
            "performance_metrics": {
                "sortino_ratio": 1.67,
                "calmar_ratio": 1.95,
                "profit_factor": 1.34,
                "avg_win": 2456.78,
                "avg_loss": -1823.45,
                "largest_win": 12345.67,
                "largest_loss": -8765.43,
            },
            "trades": pd.DataFrame(trades),
            "portfolio_value": pd.Series(portfolio_value, index = dates),
            "returns": pd.Series(returns, index = dates),
            "metadata": {
                "strategy": "RSI_MEAN_REVERSION",
                "symbol": "0700.HK",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
        }

    # 其他方法的實現略...
    def _load_backtest_from_file(self):
        """從文件加載回測數據"""
        print("📂 請輸入回測結果文件路徑:")
        file_path = input("文件路徑: ").strip()
        try:
            import json

            with open(file_path, "r", encoding="utf - 8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 文件加載失敗: {e}")
            return None

    def _load_backtest_from_database(self):
        """從數據庫加載回測數據"""
        print("🗄️ 數據庫功能尚未實現")
        return None

    def _get_technical_indicators_data(self, symbol: str):
        """獲取技術指標數據"""
        print("📡 正在獲取技術指標數據...")
        # 模擬技術指標數據
        import numpy as np
        import pandas as pd

        dates = pd.date_range("2023 - 01 - 01", "2024 - 12 - 31", freq="D")
        n_days = len(dates)

        indicators = {
            "RSI": pd.Series(np.random.uniform(20, 80, n_days), index = dates),
            "MACD": pd.Series(np.random.uniform(-50, 50, n_days), index = dates),
            "Signal": pd.Series(np.random.uniform(-30, 30, n_days), index = dates),
            "SMA_20": pd.Series(np.random.uniform(400, 600, n_days), index = dates),
            "SMA_50": pd.Series(np.random.uniform(400, 600, n_days), index = dates),
            "Upper_Band": pd.Series(np.random.uniform(550, 650, n_days), index = dates),
            "Lower_Band": pd.Series(np.random.uniform(350, 450, n_days), index = dates),
        }

        return indicators

    def _get_stock_data(self, symbol: str):
        """獲取股票數據"""
        return self._get_technical_indicators_data(symbol)

    def _find_optimization_files(self):
        """查找優化結果文件"""
        # 查找當前目錄下的優化結果文件

        patterns = ["*optimization*.json", "*results*.json", "*backtest*.json"]
        files = []
        for pattern in patterns:
            files.extend(Path(".").glob(pattern))
        return sorted(files, key = lambda x: x.stat().st_mtime, reverse = True)

    def _load_optimization_results(self, file_path: Path):
        """加載優化結果"""
        try:
            import json

            with open(file_path, "r", encoding="utf - 8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 文件加載失敗: {e}")
            return None

    def _get_custom_data(self, source: str):
        """獲取自定義數據"""
        if source == "1":
            # 導入JSON文件
            file_path = input("請輸入JSON文件路徑: ").strip()
            try:
                import json

                with open(file_path, "r", encoding="utf - 8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ 文件加載失敗: {e}")
                return None
        elif source == "2":
            # 導入CSV文件
            file_path = input("請輸入CSV文件路徑: ").strip()
            try:
                import pandas as pd

                return pd.read_csv(file_path)
            except Exception as e:
                print(f"❌ 文件加載失敗: {e}")
                return None
        else:
            print("❌ 該數據源尚未實現")
            return None

    def _update_export_setting(self, setting_choice: str):
        """更新導出設置"""
        settings_map = {
            "1": "default_format",
            "2": "output_directory",
            "3": "auto_timestamp",
            "4": "include_charts",
            "5": "include_raw_data",
            "6": "language",
        }

        setting_key = settings_map.get(setting_choice)
        if not setting_key:
            return

        current_value = self.export_manager.config.get("export_settings", {}).get(
            setting_key
        )
        print(f"當前值: {current_value}")

        if setting_key in ["auto_timestamp", "include_charts", "include_raw_data"]:
            new_value = input("新值 (true / false): ").strip().lower()
            new_value = new_value in ["true", "1", "yes", "y"]
        else:
            new_value = input("新值: ").strip()

        # 更新配置
        self.export_manager.config.setdefault("export_settings", {})[
            setting_key
        ] = new_value
        print(f"✅ 設置已更新: {setting_key} = {new_value}")

    def _batch_convert_format(self):
        """批量轉換格式"""
        print("批量格式轉換功能尚未實現")

    def _batch_merge_files(self):
        """批量合併文件"""
        print("批量文件合併功能尚未實現")

    def _batch_generate_reports(self):
        """批量生成報告"""
        print("批量報告生成功能尚未實現")

    def _batch_compress_files(self):
        """批量壓縮文件"""
        print("批量文件壓縮功能尚未實現")


if __name__ == "__main__":
    # 測試導出菜單
    menu = ExportMenu()
    menu.run_menu()
