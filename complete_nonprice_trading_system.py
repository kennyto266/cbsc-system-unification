#!/usr/bin/env python3
"""
完整的非價格數據交易信號系統
集成信號生成、風險管理和警報系統
基於世界級 MB_KDJ_[10,2] 策略 - Sharpe 3.672
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from simplified_system.src.data.government_data import collect_all_government_data, get_latest_government_data


# 導入我們創建的模塊
from non_price_trading_signals import NonPriceSignalGenerator
from risk_management_system import RiskManager
from telegram_alert_system import TelegramAlertManager

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NonPriceTradingSystem:
    """完整的非價格交易系統"""

    def __init__(self, telegram_token: str = None, telegram_chat_id: str = None):
        self.signal_generator = NonPriceSignalGenerator()
        self.risk_manager = RiskManager()
        self.telegram_alert = TelegramAlertManager(telegram_token, telegram_chat_id)

        self.system_status = {
            'running': False,
            'start_time': None,
            'last_signal_time': None,
            'signal_count': 0,
            'error_count': 0,
            'uptime': 0
        }

        self.performance_metrics = {
            'signals_generated': 0,
            'risk_alerts_triggered': 0,
            'alerts_sent': 0,
            'avg_signal_latency': 0,
            'total_latency': 0
        }

    async def initialize(self) -> bool:
        """初始化整個系統"""
        try:
            logger.info("🚀 初始化非價格交易系統...")

            # 初始化信號生成器
            if not await self.signal_generator.initialize():
                logger.error("信號生成器初始化失敗")
                return False

            logger.info("✅ 信號生成器初始化成功")

            # 發送系統啟動警報
            await self._send_system_alert('RUNNING', '非價格交易系統啟動成功')

            self.system_status['running'] = True
            self.system_status['start_time'] = datetime.now()

            logger.info("🎉 非價格交易系統初始化完成")
            return True

        except Exception as e:
            logger.error(f"系統初始化失敗: {e}")
            await self._send_system_alert('ERROR', f'系統初始化失敗: {e}')
            return False

    async def run_trading_loop(self, interval_seconds: int = 60):
        """運行主要交易循環"""
        if not self.system_status['running']:
            logger.error("系統未初始化，無法開始交易循環")
            return

        logger.info(f"🔄 開始交易循環，間隔: {interval_seconds}秒")

        try:
            while self.system_status['running']:
                cycle_start = time.time()

                try:
                    # 1. 生成交易信號
                    signal_data = await self.signal_generator.generate_realtime_signal()

                    # 2. 更新性能指標
                    self._update_performance_metrics(signal_data)

                    # 3. 風險評估
                    await self._perform_risk_assessment(signal_data)

                    # 4. 發送信號警報（如果需要）
                    await self._handle_signal_alerts(signal_data)

                    # 5. 更新系統狀態
                    self.system_status['last_signal_time'] = datetime.now()
                    self.system_status['signal_count'] += 1

                    # 6. 計算運行時間
                    if self.system_status['start_time']:
                        self.system_status['uptime'] = (datetime.now() - self.system_status['start_time']).total_seconds()

                    # 記錄成功的交易循環
                    cycle_latency = (time.time() - cycle_start) * 1000
                    logger.info(f"✅ 交易循環完成，信號: {signal_data.get('signal_description', 'Unknown')}，耗時: {cycle_latency:.2f}ms")

                except Exception as e:
                    logger.error(f"交易循環錯誤: {e}")
                    self.system_status['error_count'] += 1
                    await self._send_system_alert('WARNING', f'交易循環錯誤: {e}')

                # 等待下一個循環
                await asyncio.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("收到停止信號，正在關閉系統...")
        except Exception as e:
            logger.error(f"交易循環嚴重錯誤: {e}")
        finally:
            await self.shutdown()

    async def _perform_risk_assessment(self, signal_data: Dict[str, Any]):
        """執行風險評估"""
        try:
            # 獲取風險指標
            risk_metrics = self.risk_manager.get_risk_metrics()

            # 檢查是否需要發送風險警報
            risk_level = risk_metrics.get('portfolio_drawdown', {}).get('risk_level', 'LOW')
            if risk_level in ['HIGH', 'CRITICAL']:
                await self.telegram_alert.send_risk_alert(risk_metrics)
                self.performance_metrics['risk_alerts_triggered'] += 1

            # 檢查日損失限制
            daily_risk = risk_metrics.get('daily_loss_check', {})
            if daily_risk.get('trading_suspended', False):
                logger.warning("觸發日損失限制，交易暫停")
                await self.telegram_alert.send_risk_alert(risk_metrics)

        except Exception as e:
            logger.error(f"風險評估失敗: {e}")

    async def _handle_signal_alerts(self, signal_data: Dict[str, Any]):
        """處理信號警報"""
        try:
            # 檢查信號是否有重大變化
            if self._should_send_signal_alert(signal_data):
                success = await self.telegram_alert.send_signal_alert(signal_data)
                if success:
                    self.performance_metrics['alerts_sent'] += 1

        except Exception as e:
            logger.error(f"發送信號警報失敗: {e}")

    def _should_send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """判斷是否應該發送信號警報"""
        # 如果是錯誤信號，發送警報
        if signal_data.get('error'):
            return True

        # 如果是買入或賣出信號，發送警報
        signal = signal_data.get('signal', 0)
        if signal in [1, -1]:  # BUY or SELL
            return True

        # 如果延遲過高，發送警報
        latency = signal_data.get('latency_ms', 0)
        if latency > 200:  # 超過200ms
            return True

        return False

    def _update_performance_metrics(self, signal_data: Dict[str, Any]):
        """更新性能指標"""
        try:
            self.performance_metrics['signals_generated'] += 1

            latency = signal_data.get('latency_ms', 0)
            self.performance_metrics['total_latency'] += latency

            # 計算平均延遲
            if self.performance_metrics['signals_generated'] > 0:
                self.performance_metrics['avg_signal_latency'] = (
                    self.performance_metrics['total_latency'] / self.performance_metrics['signals_generated']
                )

        except Exception as e:
            logger.error(f"更新性能指標失敗: {e}")

    async def _send_system_alert(self, status: str, message: str):
        """發送系統警報"""
        try:
            status_data = {
                'status': status,
                'message': message,
                'uptime': self.system_status.get('uptime', 0),
                'signal_count': self.system_status.get('signal_count', 0),
                'avg_latency': self.performance_metrics.get('avg_signal_latency', 0),
                'data_processor': True,  # 簡化狀態
                'signal_generator': True,
                'risk_manager': True
            }

            await self.telegram_alert.send_system_status(status_data)

        except Exception as e:
            logger.error(f"發送系統警報失敗: {e}")

    async def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            signal_stats = self.signal_generator.get_signal_statistics()
            risk_metrics = self.risk_manager.get_risk_metrics()
            alert_stats = self.telegram_alert.get_alert_statistics()

            status = {
                'system': self.system_status,
                'performance': self.performance_metrics,
                'signal_statistics': signal_stats,
                'risk_metrics': risk_metrics,
                'alert_statistics': alert_stats,
                'last_update': datetime.now().isoformat()
            }

            return status

        except Exception as e:
            logger.error(f"獲取系統狀態失敗: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    async def shutdown(self):
        """關閉系統"""
        logger.info("🛑 正在關閉非價格交易系統...")

        self.system_status['running'] = False

        # 發送系統關閉警報
        await self._send_system_alert('STOPPED', '非價格交易系統正常關閉')

        # 記錄最終統計
        final_stats = await self.get_system_status()
        logger.info(f"最終統計: 信號生成 {self.performance_metrics['signals_generated']} 次，"
                   f"警報發送 {self.performance_metrics['alerts_sent']} 次")

        logger.info("✅ 非價格交易系統已關閉")

# 主程序
async def main():
    """主程序 - 演示完整系統"""
    print("🚀 啟動完整非價格交易系統")
    print("📊 基於世界級 MB_KDJ_[10,2] 策略")
    print("🎯 目標 Sharpe: 3.672")

    # 創建交易系統（注意：需要真實的Telegram配置才能發送警報）
    trading_system = NonPriceTradingSystem(
        telegram_token=None,  # 配置你的Bot Token
        telegram_chat_id=None  # 配置你的Chat ID
    )

    try:
        # 初始化系統
        if await trading_system.initialize():
            print("✅ 系統初始化成功")

            # 生成一次測試信號
            print("\n📈 生成測試信號...")
            signal = await trading_system.signal_generator.generate_realtime_signal()
            print(f"測試信號: {json.dumps(signal, indent=2, ensure_ascii=False)}")

            # 獲取系統狀態
            print("\n📊 獲取系統狀態...")
            status = await trading_system.get_system_status()
            print(f"系統狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")

            # 詢問是否開始實時循環
            print("\n⚠️ 注意：實時交易循環需要Telegram配置")
            print("💡 要啟動實時循環，請取消下面的註釋並配置Telegram")

            # 取消註釋以下行來啟動實時循環（需要Telegram配置）
            # await trading_system.run_trading_loop(interval_seconds=60)

        else:
            print("❌ 系統初始化失敗")

    except KeyboardInterrupt:
        print("\n收到停止信號...")
        await trading_system.shutdown()
    except Exception as e:
        print(f"\n系統錯誤: {e}")
        await trading_system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())