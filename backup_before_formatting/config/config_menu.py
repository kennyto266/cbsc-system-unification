#!/usr/bin/env python3
"""
配置菜單系統
提供用戶友好的配置管理界面
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from .config_manager import ConfigManager

class ConfigMenu:
    """配置菜單管理器"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.language = "zh-CN"

    def show_config_menu(self, trader_instance):
        """顯示配置管理菜單"""
        while True:
            trader_instance._print_header()

            menu_items = [
                ("1", "📋 查看當前配置"),
                ("2", "⚙️  修改交易配置"),
                ("3", "📊 修改指標配置"),
                ("4", "🎯 修改策略配置"),
                ("5", "🎨 修改界面配置"),
                ("6", "🔔 修改通知配置"),
                ("7", "💾 導入/導出配置"),
                ("8", "🔄 重置配置"),
                ("0", "🔙 返回主菜單")
            ]

            print(f"{trader_instance._get_colored_text('🛠️  配置管理', 'bold')}")
            print("="*50)

            for key, description in menu_items:
                print(f"  {key}. {description}")

            print(f"\n{trader_instance._get_colored_text('配置摘要:', 'yellow')}")
            summary = self.config_manager.get_config_summary()
            print(f"  默認股票: {summary['default_symbol']}")
            print(f"  主題: {summary['theme']}")
            print(f"  語言: {summary['language']}")
            print(f"  收藏股票: {', '.join(summary['favorite_symbols'][:3])}")

            choice = trader_instance._get_user_input("請選擇功能", [str(i) for i in range(9)])

            if choice == '0':
                break
            elif choice == '1':
                self._show_current_config(trader_instance)
            elif choice == '2':
                self._edit_trading_config(trader_instance)
            elif choice == '3':
                self._edit_indicators_config(trader_instance)
            elif choice == '4':
                self._edit_strategy_config(trader_instance)
            elif choice == '5':
                self._edit_ui_config(trader_instance)
            elif choice == '6':
                self._edit_notification_config(trader_instance)
            elif choice == '7':
                self._import_export_config(trader_instance)
            elif choice == '8':
                self._reset_config(trader_instance)

    def _show_current_config(self, trader_instance):
        """顯示當前配置"""
        print(f"\n{trader_instance._get_colored_text('📋 當前配置', 'bold')}")
        print("="*60)

        # 獲取配置摘要
        summary = self.config_manager.get_config_summary()

        # 基本信息配置
        print(f"{trader_instance._get_colored_text('🔧 基本配置', 'yellow')}")
        print("-" * 30)
        print(f"  配置版本: {summary['config_version']}")
        print(f"  用戶配置文件: {'✅ 存在' if summary['user_config_exists'] else '❌ 不存在'}")
        print(f"  系統配置文件: {'✅ 存在' if summary['system_config_exists'] else '❌ 不存在'}")
        if summary['last_backup']:
            print(f"  最新備份: {summary['last_backup']}")
        else:
            print(f"  最新備份: 無")

        errors = summary['validation_errors']
        print(f"  配置驗證: {'✅ 通過' if errors == 0 else f'⚠️  {errors}個錯誤'}")

        # 交易配置
        print(f"\n{trader_instance._get_colored_text('💼 交易配置', 'yellow')}")
        print("-" * 30)
        print(f"  默認股票: {self.config_manager.get('trading.default_symbol')}")
        print(f"  默認時長: {self.config_manager.get('trading.default_duration')}天")
        print(f"  自動刷新: {'開啟' if self.config_manager.get('trading.auto_refresh') else '關閉'}")
        print(f"  刷新間隔: {self.config_manager.get('trading.refresh_interval')}秒")

        # 指標配置
        print(f"\n{trader_instance._get_colored_text('📊 指標配置', 'yellow')}")
        print("-" * 30)
        rsi_config = self.config_manager.get('indicators.rsi', {})
        print(f"  RSI週期: {rsi_config.get('period', 14)}")
        print(f"  RSI超賣: {rsi_config.get('oversold', 30)}")
        print(f"  RSI超買: {rsi_config.get('overbought', 70)}")

        macd_config = self.config_manager.get('indicators.macd', {})
        print(f"  MACD快線: {macd_config.get('fast', 12)}")
        print(f"  MACD慢線: {macd_config.get('slow', 26)}")
        print(f"  MACD信號線: {macd_config.get('signal', 9)}")

        # 策略配置
        print(f"\n{trader_instance._get_colored_text('🎯 策略配置', 'yellow')}")
        print("-" * 30)
        enabled_strategies = self.config_manager.get('strategies.enabled', [])
        print(f"  啟用策略: {', '.join(enabled_strategies)}")
        print(f"  默認策略: {self.config_manager.get('strategies.default_strategy')}")

        risk_config = self.config_manager.get('strategies.risk_management', {})
        print(f"  最大持倉: {risk_config.get('max_position_size', 0.1):.1%}")
        print(f"  止損: {risk_config.get('stop_loss', 0.05):.1%}")
        print(f"  止盈: {risk_config.get('take_profit', 0.15):.1%}")

        # 界面配置
        print(f"\n{trader_instance._get_colored_text('🎨 界面配置', 'yellow')}")
        print("-" * 30)
        print(f"  主題: {self.config_manager.get('ui.theme')}")
        print(f"  語言: {self.config_manager.get('ui.language')}")
        print(f"  圖表類型: {self.config_manager.get('ui.chart_type')}")
        print(f"  表格格式: {self.config_manager.get('ui.table_format')}")

        # 通知配置
        print(f"\n{trader_instance._get_colored_text('🔔 通知配置', 'yellow')}")
        print("-" * 30)
        telegram_enabled = self.config_manager.get('notifications.enable_telegram', False)
        print(f"  Telegram通知: {'開啟' if telegram_enabled else '關閉'}")
        if telegram_enabled:
            print(f"  警報閾值: {self.config_manager.get('notifications.alert_threshold', 0.02):.1%}")

        input(f"\n{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_trading_config(self, trader_instance):
        """編輯交易配置"""
        print(f"\n{trader_instance._get_colored_text('⚙️  交易配置', 'bold')}")
        print("="*40)

        while True:
            config_options = [
                ("1", "默認股票代碼"),
                ("2", "默認時間範圍"),
                ("3", "收藏股票列表"),
                ("4", "自動刷新設置"),
                ("0", "返回上級菜單")
            ]

            for key, desc in config_options:
                print(f"  {key}. {desc}")

            choice = trader_instance._get_user_input("請選擇要修改的項目", ['0', '1', '2', '3', '4'])

            if choice == '0':
                break
            elif choice == '1':
                self._edit_default_symbol(trader_instance)
            elif choice == '2':
                self._edit_default_duration(trader_instance)
            elif choice == '3':
                self._edit_favorite_symbols(trader_instance)
            elif choice == '4':
                self._edit_auto_refresh(trader_instance)

    def _edit_default_symbol(self, trader_instance):
        """編輯默認股票代碼"""
        current = self.config_manager.get('trading.default_symbol', '0700.HK')
        new_symbol = trader_instance._get_user_input(f"默認股票代碼 (當前: {current})", None)

        if new_symbol and new_symbol.lower() not in ['q', 'quit', 'exit']:
            if self.config_manager.set('trading.default_symbol', new_symbol.upper()):
                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ 默認股票已更新', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('❌ 更新失敗', 'red')}")

            input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_default_duration(self, trader_instance):
        """編輯默認時間範圍"""
        current = self.config_manager.get('trading.default_duration', 252)
        new_duration = trader_instance._get_user_input(f"默認時間範圍天數 (當前: {current})", None)

        if new_duration and new_duration.lower() not in ['q', 'quit', 'exit']:
            try:
                duration = int(new_duration)
                if 1 <= duration <= 3650:
                    if self.config_manager.set('trading.default_duration', duration):
                        self.config_manager.save_config()
                        print(f"{trader_instance._get_colored_text('✅ 默認時長已更新', 'green')}")
                    else:
                        print(f"{trader_instance._get_colored_text('❌ 更新失敗', 'red')}")
                else:
                    print(f"{trader_instance._get_colored_text('⚠️  時長必須在1-3650天之間', 'yellow')}")
            except ValueError:
                print(f"{trader_instance._get_colored_text('⚠️  請輸入有效的數字', 'yellow')}")

            input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_favorite_symbols(self, trader_instance):
        """編輯收藏股票列表"""
        current = self.config_manager.get('trading.favorite_symbols', [])
        print(f"\n當前收藏股票: {', '.join(current) if current else '無'}")

        new_symbols = trader_instance._get_user_input("輸入股票代碼列表 (用逗號分隔)", None)

        if new_symbols and new_symbols.lower() not in ['q', 'quit', 'exit']:
            symbols = [s.strip().upper() for s in new_symbols.split(',') if s.strip()]
            if symbols:
                if self.config_manager.set('trading.favorite_symbols', symbols):
                    self.config_manager.save_config()
                    print(f"{trader_instance._get_colored_text('✅ 收藏股票已更新', 'green')}")
                else:
                    print(f"{trader_instance._get_colored_text('❌ 更新失敗', 'red')}")
            else:
                print(f"{trader_instance._get_colored_text('⚠️  未輸入有效股票代碼', 'yellow')}")

            input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_auto_refresh(self, trader_instance):
        """編輯自動刷新設置"""
        current_auto = self.config_manager.get('trading.auto_refresh', True)
        current_interval = self.config_manager.get('trading.refresh_interval', 60)

        print(f"\n當前自動刷新: {'開啟' if current_auto else '關閉'}")
        print(f"當前刷新間隔: {current_interval}秒")

        enable = trader_instance._get_user_input("是否啟用自動刷新? (y/n)", ['y', 'n', 'Y', 'N'])

        if enable.lower() == 'y':
            if self.config_manager.set('trading.auto_refresh', True):
                # 詢問刷新間隔
                interval = trader_instance._get_user_input(f"刷新間隔秒數 (當前: {current_interval})", None)
                try:
                    if interval:
                        interval_int = int(interval)
                        if 10 <= interval_int <= 3600:
                            self.config_manager.set('trading.refresh_interval', interval_int)
                        else:
                            print(f"{trader_instance._get_colored_text('⚠️  間隔範圍: 10-3600秒', 'yellow')}")
                except ValueError:
                    print(f"{trader_instance._get_colored_text('⚠️  保持原間隔設置', 'yellow')}")

                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ 自動刷新已啟用', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('❌ 更新失敗', 'red')}")
        else:
            if self.config_manager.set('trading.auto_refresh', False):
                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ 自動刷新已關閉', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('❌ 更新失敗', 'red')}")

        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_indicators_config(self, trader_instance):
        """編輯指標配置"""
        print(f"\n{trader_instance._get_colored_text('📊 指標配置', 'bold')}")
        print("="*40)

        indicator_options = [
            ("1", "RSI配置"),
            ("2", "MACD配置"),
            ("3", "移動平均線配置"),
            ("4", "布林帶配置"),
            ("5", "KDJ配置"),
            ("0", "返回上級菜單")
        ]

        while True:
            for key, desc in indicator_options:
                print(f"  {key}. {desc}")

            choice = trader_instance._get_user_input("請選擇要配置的指標", ['0', '1', '2', '3', '4', '5'])

            if choice == '0':
                break
            elif choice == '1':
                self._edit_rsi_config(trader_instance)
            elif choice == '2':
                self._edit_macd_config(trader_instance)
            elif choice == '3':
                self._edit_ma_config(trader_instance)
            elif choice == '4':
                self._edit_bollinger_config(trader_instance)
            elif choice == '5':
                self._edit_kdj_config(trader_instance)

    def _edit_rsi_config(self, trader_instance):
        """編輯RSI配置"""
        current = self.config_manager.get('indicators.rsi', {})
        print(f"\n{trader_instance._get_colored_text('RSI配置', 'bold')}")
        print("-" * 20)
        print(f"當前週期: {current.get('period', 14)}")
        print(f"當前超賣: {current.get('oversold', 30)}")
        print(f"當前超買: {current.get('overbought', 70)}")

        try:
            period = int(trader_instance._get_user_input("RSI週期 (2-100)", None))
            oversold = int(trader_instance._get_user_input("超賣線 (1-50)", None))
            overbought = int(trader_instance._get_user_input("超買線 (50-99)", None))

            if 2 <= period <= 100 and 1 <= oversold < overbought <= 99:
                self.config_manager.set('indicators.rsi.period', period)
                self.config_manager.set('indicators.rsi.oversold', oversold)
                self.config_manager.set('indicators.rsi.overbought', overbought)
                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ RSI配置已更新', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('⚠️  參數範圍無效', 'yellow')}")
        except ValueError:
            print(f"{trader_instance._get_colored_text('⚠️  請輸入有效數字', 'yellow')}")

        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_macd_config(self, trader_instance):
        """編輯MACD配置"""
        current = self.config_manager.get('indicators.macd', {})
        print(f"\n{trader_instance._get_colored_text('MACD配置', 'bold')}")
        print("-" * 20)
        print(f"當前快線: {current.get('fast', 12)}")
        print(f"當前慢線: {current.get('slow', 26)}")
        print(f"當前信號線: {current.get('signal', 9)}")

        try:
            fast = int(trader_instance._get_user_input("快線週期 (1-50)", None))
            slow = int(trader_instance._get_user_input("慢線週期 (51-300)", None))
            signal = int(trader_instance._get_user_input("信號線週期 (1-20)", None))

            if 1 <= fast <= 50 and 51 <= slow <= 300 and 1 <= signal <= 20 and fast < slow:
                self.config_manager.set('indicators.macd.fast', fast)
                self.config_manager.set('indicators.macd.slow', slow)
                self.config_manager.set('indicators.macd.signal', signal)
                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ MACD配置已更新', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('⚠️  參數範圍無效，快線必須小於慢線', 'yellow')}")
        except ValueError:
            print(f"{trader_instance._get_colored_text('⚠️  請輸入有效數字', 'yellow')}")

        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_ma_config(self, trader_instance):
        """編輯移動平均線配置"""
        current = self.config_manager.get('indicators.sma', {})
        print(f"\n{trader_instance._get_colored_text('移動平均線配置', 'bold')}")
        print("-" * 20)
        print(f"當前短期: {current.get('short_period', 20)}")
        print(f"當前長期: {current.get('long_period', 50)}")

        try:
            short = int(trader_instance._get_user_input("短期MA週期 (5-50)", None))
            long = int(trader_instance._get_user_input("長期MA週期 (51-300)", None))

            if 5 <= short <= 50 and 51 <= long <= 300 and short < long:
                self.config_manager.set('indicators.sma.short_period', short)
                self.config_manager.set('indicators.sma.long_period', long)
                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ 移動平均線配置已更新', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('⚠️  參數範圍無效，短期必須小於長期', 'yellow')}")
        except ValueError:
            print(f"{trader_instance._get_colored_text('⚠️  請輸入有效數字', 'yellow')}")

        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_bollinger_config(self, trader_instance):
        """編輯布林帶配置"""
        current = self.config_manager.get('indicators.bollinger', {})
        print(f"\n{trader_instance._get_colored_text('布林帶配置', 'bold')}")
        print("-" * 20)
        print(f"當前週期: {current.get('period', 20)}")
        print(f"當前標準差: {current.get('std_dev', 2)}")

        try:
            period = int(trader_instance._get_user_input("週期 (5-50)", None))
            std_dev = float(trader_instance._get_user_input("標準差 (1.0-3.0)", None))

            if 5 <= period <= 50 and 1.0 <= std_dev <= 3.0:
                self.config_manager.set('indicators.bollinger.period', period)
                self.config_manager.set('indicators.bollinger.std_dev', std_dev)
                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ 布林帶配置已更新', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('⚠️  參數範圍無效', 'yellow')}")
        except ValueError:
            print(f"{trader_instance._get_colored_text('⚠️  請輸入有效數字', 'yellow')}")

        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_kdj_config(self, trader_instance):
        """編輯KDJ配置"""
        current = self.config_manager.get('indicators.kdj', {})
        print(f"\n{trader_instance._get_colored_text('KDJ配置', 'bold')}")
        print("-" * 20)
        print(f"當前K週期: {current.get('k_period', 9)}")
        print(f"當前D平滑: {current.get('d_period', 3)}")
        print(f"當前J週期: {current.get('j_period', 3)}")

        try:
            k_period = int(trader_instance._get_user_input("K週期 (5-50)", None))
            d_period = int(trader_instance._get_user_input("D平滑週期 (1-10)", None))
            j_period = int(trader_instance._get_user_input("J週期 (1-10)", None))

            if 5 <= k_period <= 50 and 1 <= d_period <= 10 and 1 <= j_period <= 10:
                self.config_manager.set('indicators.kdj.k_period', k_period)
                self.config_manager.set('indicators.kdj.d_period', d_period)
                self.config_manager.set('indicators.kdj.j_period', j_period)
                self.config_manager.save_config()
                print(f"{trader_instance._get_colored_text('✅ KDJ配置已更新', 'green')}")
            else:
                print(f"{trader_instance._get_colored_text('⚠️  參數範圍無效', 'yellow')}")
        except ValueError:
            print(f"{trader_instance._get_colored_text('⚠️  請輸入有效數字', 'yellow')}")

        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_strategy_config(self, trader_instance):
        """編輯策略配置"""
        print(f"\n{trader_instance._get_colored_text('🎯 策略配置開發中...', 'yellow')}")
        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_ui_config(self, trader_instance):
        """編輯界面配置"""
        print(f"\n{trader_instance._get_colored_text('🎨 界面配置開發中...', 'yellow')}")
        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _edit_notification_config(self, trader_instance):
        """編輯通知配置"""
        print(f"\n{trader_instance._get_colored_text('🔔 通知配置開發中...', 'yellow')}")
        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _import_export_config(self, trader_instance):
        """導入導出配置"""
        print(f"\n{trader_instance._get_colored_text('💾 導入/導出配置開發中...', 'yellow')}")
        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")

    def _reset_config(self, trader_instance):
        """重置配置"""
        print(f"\n{trader_instance._get_colored_text('🔄 重置配置', 'bold')}")
        print("="*30)

        reset_options = [
            ("1", "重置交易配置"),
            ("2", "重置指標配置"),
            ("3", "重置所有配置"),
            ("0", "取消")
        ]

        for key, desc in reset_options:
            print(f"  {key}. {desc}")

        choice = trader_instance._get_user_input("請選擇重置範圍", ['0', '1', '2', '3'])

        if choice == '1':
            confirm = trader_instance._get_user_input("確認重置交易配置? (y/n)", ['y', 'n', 'Y', 'N'])
            if confirm.lower() == 'y':
                if self.config_manager.reset_to_default('trading'):
                    self.config_manager.save_config()
                    print(f"{trader_instance._get_colored_text('✅ 交易配置已重置', 'green')}")
                else:
                    print(f"{trader_instance._get_colored_text('❌ 重置失敗', 'red')}")
        elif choice == '2':
            confirm = trader_instance._get_user_input("確認重置指標配置? (y/n)", ['y', 'n', 'Y', 'N'])
            if confirm.lower() == 'y':
                if self.config_manager.reset_to_default('indicators'):
                    self.config_manager.save_config()
                    print(f"{trader_instance._get_colored_text('✅ 指標配置已重置', 'green')}")
                else:
                    print(f"{trader_instance._get_colored_text('❌ 重置失敗', 'red')}")
        elif choice == '3':
            confirm = trader_instance._get_user_input("確認重置所有配置? (y/n)", ['y', 'n', 'Y', 'N'])
            if confirm.lower() == 'y':
                if self.config_manager.reset_to_default():
                    self.config_manager.save_config()
                    print(f"{trader_instance._get_colored_text('✅ 所有配置已重置', 'green')}")
                else:
                    print(f"{trader_instance._get_colored_text('❌ 重置失敗', 'red')}")

        input(f"{trader_instance._get_colored_text('按Enter繼續...', 'cyan')}")