#!/usr/bin/env python3
"""
Telegram警報系統
為非價格交易信號提供即時通知
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests

logger = logging.getLogger(__name__)

class TelegramAlertManager:
    """Telegram警報管理器"""

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if bot_token else None
        self.alert_history = []
        self.alert_rules = {
            'signal_changes': True,      # 信號變化警報
            'risk_alerts': True,         # 風險警報
            'performance_updates': True, # 績效更新
            'system_status': True        # 系統狀態
        }

    async def send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """發送交易信號警報"""
        if not self.api_url or not self.chat_id:
            logger.warning("Telegram配置缺失，跳過警報發送")
            return False

        try:
            # 構建警報消息
            message = self._format_signal_message(signal_data)

            # 發送消息
            success = await self._send_telegram_message(message)

            if success:
                self._log_alert('SIGNAL', f"交易信號: {signal_data.get('signal_description', 'Unknown')}")
                logger.info(f"成功發送交易信號警報: {signal_data.get('signal_description')}")

            return success

        except Exception as e:
            logger.error(f"發送信號警報失敗: {e}")
            return False

    async def send_risk_alert(self, risk_data: Dict[str, Any]) -> bool:
        """發送風險警報"""
        if not self.api_url or not self.chat_id:
            return False

        try:
            message = self._format_risk_message(risk_data)
            success = await self._send_telegram_message(message)

            if success:
                risk_level = risk_data.get('portfolio_drawdown', {}).get('risk_level', 'UNKNOWN')
                self._log_alert('RISK', f"風險警報: {risk_level}")

            return success

        except Exception as e:
            logger.error(f"發送風險警報失敗: {e}")
            return False

    async def send_performance_update(self, performance_data: Dict[str, Any]) -> bool:
        """發送績效更新"""
        if not self.api_url or not self.chat_id:
            return False

        try:
            message = self._format_performance_message(performance_data)
            success = await self._send_telegram_message(message)

            if success:
                sharpe = performance_data.get('sharpe_ratio', 0)
                self._log_alert('PERFORMANCE', f"績效更新: Sharpe {sharpe:.3f}")

            return success

        except Exception as e:
            logger.error(f"發送績效更新失敗: {e}")
            return False

    async def send_system_status(self, status_data: Dict[str, Any]) -> bool:
        """發送系統狀態"""
        if not self.api_url or not self.chat_id:
            return False

        try:
            message = self._format_system_message(status_data)
            success = await self._send_telegram_message(message)

            if success:
                status = status_data.get('status', 'Unknown')
                self._log_alert('SYSTEM', f"系統狀態: {status}")

            return success

        except Exception as e:
            logger.error(f"發送系統狀態失敗: {e}")
            return False

    def _format_signal_message(self, signal_data: Dict[str, Any]) -> str:
        """格式化交易信號消息"""
        emoji_map = {
            'BUY': '📈',
            'SELL': '📉',
            'HOLD': '⏸️',
            'ERROR': '❌'
        }

        signal = signal_data.get('signal_description', 'UNKNOWN')
        emoji = emoji_map.get(signal.split('(')[0].strip(), '📊')

        message = f"""
{emoji} **非價格交易信號警報**

🎯 **策略**: MB_KDJ_[10,2] (Sharpe 3.672)
📊 **信號**: {signal}
📈 **K值**: {signal_data.get('k_value', 0):.4f}
📉 **D值**: {signal_data.get('d_value', 0):.4f}
⚡ **J值**: {signal_data.get('j_value', 0):.4f}
⏱️ **延遲**: {signal_data.get('latency_ms', 0):.2f}ms
🕒 **時間**: {signal_data.get('timestamp', 'Unknown')}

💡 *基於香港政府貨幣基礎數據*
⚠️ *過往表現不保證未來結果*
        """.strip()

        return message

    def _format_risk_message(self, risk_data: Dict[str, Any]) -> str:
        """格式化風險警報消息"""
        portfolio_risk = risk_data.get('portfolio_drawdown', {})
        risk_level = portfolio_risk.get('risk_level', 'UNKNOWN')
        drawdown = portfolio_risk.get('current_drawdown', 0) * 100

        emoji_map = {
            'LOW': '✅',
            'MEDIUM': '⚠️',
            'HIGH': '🔥',
            'CRITICAL': '🚨'
        }
        emoji = emoji_map.get(risk_level, '📊')

        daily_risk = risk_data.get('daily_loss_check', {})
        daily_pnl = daily_risk.get('daily_pnl', 0)
        daily_loss_pct = daily_risk.get('daily_loss_pct', 0) * 100

        message = f"""
{emoji} **風險管理警報**

📊 **風險等級**: {risk_level}
📉 **當前回撤**: {drawdown:.2f}%
💰 **日損益**: {daily_pnl:,.0f} ({daily_loss_pct:+.2f}%)
📈 **回撤比率**: {portfolio_risk.get('drawdown_ratio', 0):.1%}
{'🛑 **交易已暫停**' if daily_risk.get('trading_suspended') else ''}

🎯 **風險限制**:
• 個股止損: 10%
• 投資組合最大回撤: 9.16%
• 日損失限制: 5%

💡 *嚴格遵守風險管理原則*
        """.strip()

        return message

    def _format_performance_message(self, performance_data: Dict[str, Any]) -> str:
        """格式化績效更新消息"""
        sharpe = performance_data.get('sharpe_ratio', 0)
        total_return = performance_data.get('total_return', 0) * 100
        max_drawdown = performance_data.get('max_drawdown', 0) * 100
        trade_count = performance_data.get('trade_count', 0)

        # 性能評估
        if sharpe >= 3.0:
            emoji = '🏆'
            assessment = '卓越'
        elif sharpe >= 2.0:
            emoji = '🥇'
            assessment = '優秀'
        elif sharpe >= 1.0:
            emoji = '🥈'
            assessment = '良好'
        else:
            emoji = '📊'
            assessment = '一般'

        message = f"""
{emoji} **策略績效更新**

🎯 **策略評估**: {assessment}
📈 **Sharpe比率**: {sharpe:.3f}
💰 **總回報**: {total_return:+.2f}%
📉 **最大回撤**: {max_drawdown:.2f}%
🔄 **交易次數**: {trade_count}

🏅 **基準比較**:
• 目標Sharpe: 3.0
• 當前Sharpe: {sharpe:.3f}
• 表現: {('超越' if sharpe >= 3.0 else '未達')}

⏰ **更新時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        return message

    def _format_system_message(self, status_data: Dict[str, Any]) -> str:
        """格式化系統狀態消息"""
        status = status_data.get('status', 'Unknown')
        uptime = status_data.get('uptime', 0)
        signal_count = status_data.get('signal_count', 0)
        latency = status_data.get('avg_latency', 0)

        status_emoji_map = {
            'RUNNING': '🟢',
            'STOPPED': '🔴',
            'WARNING': '🟡',
            'ERROR': '❌'
        }
        emoji = status_emoji_map.get(status.upper(), '📊')

        message = f"""
{emoji} **系統狀態更新**

🔄 **系統狀態**: {status}
⏱️ **運行時間**: {uptime:.0f}秒
📡 **信號次數**: {signal_count}
⚡ **平均延遲**: {latency:.2f}ms
🕒 **檢查時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

💻 **組件狀態**:
• 數據處理器: {'✅ 正常' if status_data.get('data_processor', True) else '❌ 異常'}
• 信號生成器: {'✅ 正常' if status_data.get('signal_generator', True) else '❌ 異常'}
• 風險管理器: {'✅ 正常' if status_data.get('risk_manager', True) else '❌ 異常'}

📊 **基於MB_KDJ_[10,2]世界級策略**
        """.strip()

        return message

    async def _send_telegram_message(self, message: str) -> bool:
        """發送Telegram消息"""
        if not self.api_url or not self.chat_id:
            return False

        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('ok', False)

        except Exception as e:
            logger.error(f"Telegram API調用失敗: {e}")
            return False

    def _log_alert(self, alert_type: str, description: str):
        """記錄警報"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'description': description,
            'success': True
        }

        self.alert_history.append(alert)

        # 保持最近1000條警報記錄
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """獲取警報統計"""
        if not self.alert_history:
            return {'message': '尚無警報記錄'}

        # 按類型統計
        type_counts = {}
        for alert in self.alert_history:
            alert_type = alert['type']
            type_counts[alert_type] = type_counts.get(alert_type, 0) + 1

        # 最近24小時統計
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > datetime.now() - timedelta(hours=24)
        ]

        return {
            'total_alerts': len(self.alert_history),
            'last_24h_alerts': len(recent_alerts),
            'alerts_by_type': type_counts,
            'last_alert': self.alert_history[-1] if self.alert_history else None,
            'alert_rules': self.alert_rules
        }

    def update_alert_rules(self, rules: Dict[str, bool]):
        """更新警報規則"""
        self.alert_rules.update(rules)
        logger.info(f"警報規則已更新: {rules}")

# 測試程序
async def main():
    """測試Telegram警報系統"""
    print("📱 測試Telegram警報系統")

    # 注意：需要真實的bot_token和chat_id才能實際發送
    # 這裡僅測試消息格式化功能
    alert_manager = TelegramAlertManager()

    # 測試信號警報格式化
    print("\n📊 測試信號警報格式...")
    signal_data = {
        'signal_description': 'BUY (買入)',
        'k_value': 15.23,
        'd_value': 25.67,
        'j_value': -5.67,
        'latency_ms': 45.2,
        'timestamp': datetime.now().isoformat()
    }

    message = alert_manager._format_signal_message(signal_data)
    print(f"信號警報消息:\n{message}")

    # 測試風險警報格式化
    print("\n🛡️ 測試風險警報格式...")
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
    print(f"風險警報消息:\n{risk_message}")

    # 測試警報統計
    print("\n📈 獲取警報統計...")
    stats = alert_manager.get_alert_statistics()
    print(f"警報統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")

    print("\n✅ Telegram警報系統測試完成")
    print("💡 要實際發送警報，請配置bot_token和chat_id")

if __name__ == "__main__":
    asyncio.run(main())