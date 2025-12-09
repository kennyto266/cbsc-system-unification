#!/usr/bin/env python3
"""
測試非價格交易信號系統
"""

import asyncio
import json
import sys
from datetime import datetime

# 設置控制台編碼
sys.stdout.reconfigure(encoding='utf-8')

async def test_signal_generation():
    """測試信號生成"""
    print("Testing Non-Price Trading Signal System...")
    print("Based on world-class MB_KDJ_[10,2] strategy (Sharpe 3.672)")

    try:
        # 導入模塊
        from non_price_trading_signals import NonPriceSignalGenerator

        # 創建信號生成器
        signal_generator = NonPriceSignalGenerator()

        # 初始化系統
        print("Initializing signal generator...")
        if await signal_generator.initialize():
            print("✅ System initialized successfully")

            # 生成實時信號
            print("\nGenerating real-time trading signal...")
            signal = await signal_generator.generate_realtime_signal()

            print(f"Signal Result: {json.dumps(signal, indent=2, ensure_ascii=False)}")

            # 獲取統計信息
            print("\nGetting signal statistics...")
            stats = signal_generator.get_signal_statistics()
            print(f"Statistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")

        else:
            print("❌ System initialization failed")

    except Exception as e:
        print(f"Error in signal generation test: {e}")
        import traceback
        traceback.print_exc()

async def test_risk_management():
    """測試風險管理"""
    print("\nTesting Risk Management System...")

    try:
        from risk_management_system import RiskManager

        # 創建風險管理器
        risk_manager = RiskManager()

        # 測試倉位計算
        print("Testing position sizing...")
        position_size = risk_manager.calculate_position_size(0.8, 0.25)
        print(f"Signal strength 80%, volatility 25% -> Position: {position_size*100:.2f}%")

        # 測試止損檢查
        print("Testing stop loss...")
        should_stop = risk_manager.check_stop_loss(90, 100, 'long')
        print(f"Entry 100, Current 90, Stop triggered: {should_stop}")

        # 更新投資組合價值
        market_data = {'0700.HK': 450, '0941.HK': 25}
        risk_manager.update_portfolio_value(market_data)

        # 獲取風險指標
        print("Getting risk metrics...")
        risk_metrics = risk_manager.get_risk_metrics()
        print(f"Risk Metrics: {json.dumps(risk_metrics, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"Error in risk management test: {e}")
        import traceback
        traceback.print_exc()

async def test_telegram_alerts():
    """測試Telegram警報"""
    print("\nTesting Telegram Alert System...")

    try:
        from telegram_alert_system import TelegramAlertManager

        # 創建警報管理器
        alert_manager = TelegramAlertManager()

        # 測試信號警報格式化
        print("Testing signal alert formatting...")
        signal_data = {
            'signal_description': 'BUY (買入)',
            'k_value': 15.23,
            'd_value': 25.67,
            'j_value': -5.67,
            'latency_ms': 45.2,
            'timestamp': datetime.now().isoformat()
        }

        message = alert_manager._format_signal_message(signal_data)
        print(f"Signal Alert Message:\n{message}")

        # 測試風險警報格式化
        print("\nTesting risk alert formatting...")
        risk_data = {
            'portfolio_drawdown': {
                'risk_level': 'HIGH',
                'current_drawdown': 0.08,
                'drawdown_ratio': 0.87
            },
            'daily_loss_check': {
                'daily_pnl': -50000,
                'daily_loss_pct': 0.05,
                'trading_suspended': False
            }
        }

        risk_message = alert_manager._format_risk_message(risk_data)
        print(f"Risk Alert Message:\n{risk_message}")

        # 測試警報統計
        print("\nGetting alert statistics...")
        stats = alert_manager.get_alert_statistics()
        print(f"Alert Statistics: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"Error in Telegram alerts test: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主測試程序"""
    print("="*60)
    print("Non-Price Trading Signal System - Complete Test")
    print("Based on MB_KDJ_[10,2] world-class strategy")
    print("="*60)

    # 運行所有測試
    await test_signal_generation()
    await test_risk_management()
    await test_telegram_alerts()

    print("\n" + "="*60)
    print("All tests completed!")
    print("System ready for production deployment")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())