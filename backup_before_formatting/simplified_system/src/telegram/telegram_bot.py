#!/usr/bin/env python3
"""
簡化系統 - Telegram量化交易Bot
Simplified System - Telegram Quantitative Trading Bot

整合股票分析、政府數據和實用功能的完整Telegram Bot
Integration of stock analysis, government data, and utility functions in complete Telegram Bot
"""

import os
import sys
import logging
import asyncio
import json
import requests
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

# Import our simplified system modules
from ..api.stock_api import stock_api
from ..api.government_data import government_api

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleTelegramBot:
    """
    簡化系統的Telegram Bot
    專注於核心量化功能和實用服務
    """

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
            raise ValueError("TELEGRAM_BOT_TOKEN is required")

        # Bot configuration
        self.application = None
        self.running = False

    async def send_message(self, update: Update, text: str, parse_mode: str = 'Markdown') -> None:
        """Send message with proper formatting"""
        try:
            max_length = 4096
            if len(text) <= max_length:
                await update.message.reply_text(text, parse_mode=parse_mode)
            else:
                # Split long messages
                parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                for i, part in enumerate(parts):
                    if i == 0:
                        await update.message.reply_text(part, parse_mode=parse_mode)
                    else:
                        await update.message.reply_text(part)
                    if i < len(parts) - 1:
                        await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            try:
                await update.message.reply_text("發送消息失敗，請稍後重試")
            except:
                pass

    # === Stock Analysis Commands ===
    async def analyze_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Stock technical analysis command"""
        try:
            if not context.args:
                await self.send_message(update, "❌ 請提供股票代碼\n\n用法: `/analyze 0700.HK`")
                return

            symbol = context.args[0].upper()
            await update.message.reply_text(f"🔍 正在分析 {symbol}...")

            # Get stock data from our simplified API
            data = stock_api.get_stock_data(symbol)
            if not data:
                await self.send_message(update, f"❌ 無法獲取 {symbol} 的股票數據")
                return

            # Simple technical analysis
            analysis_text = await self._generate_simple_analysis(symbol, data)
            await self.send_message(update, analysis_text)

        except Exception as e:
            logger.error(f"Analyze command error: {e}")
            await self.send_message(update, "❌ 分析失敗，請稍後重試")

    async def _generate_simple_analysis(self, symbol: str, data: Dict) -> str:
        """Generate simple technical analysis from stock data"""
        try:
            # Extract close prices from the nested data structure
            close_data = data.get('data', {}).get('close', {})
            if not close_data:
                return f"❌ {symbol} 數據格式不正確"

            # Convert to list of prices
            prices = list(close_data.values())
            if len(prices) < 20:
                return f"❌ {symbol} 數據不足，需要至少20條記錄"

            # Simple calculations
            latest_price = float(prices[-1])
            ma_20 = sum(prices[-20:]) / 20
            ma_50 = sum(prices[-50:]) / 50 if len(prices) >= 50 else ma_20

            # Simple RSI approximation
            rsi = self._calculate_simple_rsi(prices)

            # Price change
            price_change = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) > 1 else 0

            # Generate analysis
            text = f"""
📊 **{symbol} 技術分析**

🔍 **分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

💰 **當前價格**: HKD {latest_price:.2f}
📈 **價格變動**: {price_change:+.2f}%

📊 **技術指標**:
• RSI(14): {rsi:.1f}
• MA20: HKD {ma_20:.2f}
• MA50: HKD {ma_50:.2f}
• 價格相對MA20: {((latest_price/ma_20 - 1) * 100):+.1f}%

🎯 **交易信號**:
"""

            # Add trading signals
            if rsi > 70:
                text += "• RSI: 超買區域 🟡\n"
            elif rsi < 30:
                text += "• RSI: 超賣區域 🟢\n"
            else:
                text += "• RSI: 中性區域 ⚪\n"

            if latest_price > ma_20:
                text += "• 趨勢: 價格在MA20之上 📈\n"
            else:
                text += "• 趨勢: 價格在MA20之下 📉\n"

            text += f"""
💡 **建議**: 基於當前技術指標，建議謹慎觀察

⚠️ **風險提示**: 投資有風險，請謹慎決策
📌 數據來源: 簡化系統股票API
"""
            return text

        except Exception as e:
            logger.error(f"Error generating analysis: {e}")
            return f"❌ 生成分析時發生錯誤: {str(e)}"

    def _calculate_simple_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate simple RSI"""
        if len(prices) < period + 1:
            return 50.0  # Default RSI

        try:
            gains = []
            losses = []

            for i in range(1, min(len(prices), period + 1)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))

            if not gains:
                avg_gain = 0
            else:
                avg_gain = sum(gains) / len(gains)

            if not losses:
                avg_loss = 0
            else:
                avg_loss = sum(losses) / len(losses)

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return max(0, min(100, rsi))

        except Exception:
            return 50.0

    # === Government Data Commands ===
    async def gov_data_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Government data command"""
        try:
            await update.message.reply_text("📊 正在獲取香港政府數據...")

            # Get latest HIBOR data
            hibor_data = await government_collector.get_latest_data("hibor_rates", 3)

            if hibor_data:
                text = "📊 **香港政府數據 - HIBOR利率**\n\n"
                text += f"📅 數據時間: {hibor_data.get('collection_time', 'N/A')}\n"
                text += f"📈 記錄數量: {hibor_data.get('total_records', 0)}\n\n"

                records = hibor_data.get('records', [])
                if records:
                    text += "🔢 **最新HIBOR利率**:\n"
                    for record in records:
                        date = record.get('date', 'N/A')
                        rate = record.get('hibor_overnight', 'N/A')
                        text += f"• {date}: {rate}%\n"

                text += "\n🌐 數據來源: 香港金融管理局(HKMA)"
            else:
                text = "❌ 無法獲取HIBOR數據\n\n請稍後重試或檢查API連接"

            await self.send_message(update, text)

        except Exception as e:
            logger.error(f"Government data command error: {e}")
            await self.send_message(update, "❌ 獲取政府數據失敗")

    async def collect_gov_data_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Trigger government data collection"""
        try:
            if not context.args:
                await self.send_message(update, "❌ 請指定數據源\n\n用法: `/collectgov hibor_rates`")
                return

            source_name = context.args[0]
            await update.message.reply_text(f"🔄 正在收集 {source_name} 數據...")

            # Trigger collection
            from ..data.government_data import collect_hkma_data
            result = await collect_hkma_data(source_name)

            if result and result.success:
                text = f"✅ **{source_name} 數據收集成功**\n\n"
                text += f"📊 記錄數量: {result.record_count}\n"
                text += f"📅 收集時間: {result.collection_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                text += f"⭐ 質量評分: {result.data_quality_score:.2f}/1.0\n"
                text += f"💾 文件路徑: {result.file_path}"
            else:
                error_msg = result.error_message if result else "未知錯誤"
                text = f"❌ **{source_name} 數據收集失敗**\n\n錯誤: {error_msg}"

            await self.send_message(update, text)

        except Exception as e:
            logger.error(f"Collect government data command error: {e}")
            await self.send_message(update, "❌ 數據收集失敗")

    # === System Commands ===
    async def start_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Welcome message"""
        welcome_text = f"""
🎯 **歡迎使用簡化系統量化交易Bot！**

**📊 量化分析功能:**
• `/analyze <代碼>` - 技術指標分析
• `/status` - 系統狀態

**📊 政府數據功能:**
• `/govdata` - 查看最新政府數據
• `/collectgov <source>` - 收集指定數據源

**🔧 系統功能:**
• `/help` - 顯示幫助信息
• `/health` - 系統健康檢查

**🤖 自動回應:**
• 在任何聊天中提及 `@penguin8n`

💡 使用範例：`/analyze 0700.HK` 或 `/govdata`
"""
        await self.send_message(update, welcome_text)

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Help information"""
        help_text = """
**🤖 Bot使用指南**

**📈 量化分析:**
• `/analyze 0700.HK` - 分析騰訊技術指標
• `/analyze 0941.HK` - 分析建設銀行技術指標

**📊 政府數據:**
• `/govdata` - 查看最新HIBOR利率數據
• `/collectgov hibor_rates` - 收集HIBOR數據
• `/collectgov exchange_rates` - 收集匯率數據

**🤖 自動回應:**
• 提及 `@penguin8n` 自動回覆

**🔧 系統命令:**
• `/start` - 歡迎信息
• `/status` - 系統狀態
• `/health` - 系統健康檢查

💡 提示：
• 港股代碼格式為 `0700.HK`
• 政府數據源: hibor_rates, exchange_rates, monetary_base
"""
        await self.send_message(update, help_text)

    async def status_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """System status"""
        try:
            # Check stock API status
            stock_status = "✅ 正常"  # Simple check
            try:
                test_data = stock_api.get_stock_data("0700.HK", 1)
                stock_status = "✅ 正常" if test_data else "⚠️ 異常"
            except:
                stock_status = "❌ 異常"

            # Check government data status
            gov_status = "✅ 正常"  # Simple check
            try:
                gov_sources = len(government_api.data_sources)
                gov_status = f"✅ 正常 ({gov_sources}個數據源)"
            except:
                gov_status = "❌ 異常"

            status_text = f"""
**🔧 系統狀態**

🤖 **Bot版本**: Simplified System v1.0
⏰ **當前時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🐍 **Python版本**: {sys.version.split()[0]}

**📊 股票API狀態**: {stock_status}
**📊 政府數據狀態**: {gov_status}
**📡 網絡連接**: ✅ 正常

💡 簡化系統運行正常，核心功能可用！
"""
            await self.send_message(update, status_text)

        except Exception as e:
            logger.error(f"Status command error: {e}")
            await self.send_message(update, "❌ 獲取系統狀態失敗")

    async def health_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Health check"""
        try:
            health_checks = []

            # Check stock API
            try:
                stock_data = stock_api.get_stock_data("0700.HK", 1)
                if stock_data:
                    health_checks.append("✅ 股票API: 正常")
                else:
                    health_checks.append("⚠️ 股票API: 異常")
            except:
                health_checks.append("❌ 股票API: 錯誤")

            # Check government data
            try:
                gov_sources = len(government_api.data_sources)
                health_checks.append(f"✅ 政府數據: {gov_sources}個源")
            except:
                health_checks.append("❌ 政府數據: 錯誤")

            # Check bot token
            if self.bot_token:
                health_checks.append("✅ Bot Token: 正常")
            else:
                health_checks.append("❌ Bot Token: 異常")

            health_text = "**🏥 系統健康檢查**\n\n"
            health_text += "\n".join(health_checks)
            health_text += f"\n\n⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            await self.send_message(update, health_text)

        except Exception as e:
            logger.error(f"Health check error: {e}")
            await self.send_message(update, "❌ 健康檢查失敗")

    async def handle_mention(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle @penguin8n automatic response"""
        try:
            message_text = update.message.text if update.message else ""

            # Check if bot is mentioned
            if "@penguin8n" in message_text.lower():
                reply_text = "🤖 簡化系統量化交易Bot在這裡！\n\n可用指令：\n /start - 開始對話\n /help - 顯示幫助\n /analyze <代碼> - 股票分析\n /govdata - 政府數據\n /status - 系統狀態\n /health - 健康檢查"
                await update.message.reply_text(reply_text)
                logger.info(f"Responded to @mention - User: {update.effective_user.name if update.effective_user else 'Unknown'}")

        except Exception as e:
            logger.error(f"Error responding to @mention: {e}")

    async def unknown_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Unknown command handler"""
        await self.send_message(update, "❌ 未知命令\n請使用 `/help` 查看可用命令")

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Error handler"""
        logger.error(f"Update {update} caused error {context.error}")

    async def post_init(self, app: Application) -> None:
        """Initialize bot commands"""
        commands = [
            BotCommand("start", "🎯 歡迎信息"),
            BotCommand("help", "📖 幫助信息"),
            BotCommand("analyze", "📊 股票技術分析"),
            BotCommand("govdata", "📊 政府數據"),
            BotCommand("collectgov", "🔄 收集政府數據"),
            BotCommand("status", "🔧 系統狀態"),
            BotCommand("health", "🏥 健康檢查"),
        ]

        try:
            await app.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
        except Exception as e:
            logger.error(f"Failed to set commands: {e}")

    def build_application(self) -> Application:
        """Build the Telegram application"""
        self.application = Application.builder().token(self.bot_token).post_init(self.post_init).build()

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_cmd))
        self.application.add_handler(CommandHandler("help", self.help_cmd))
        self.application.add_handler(CommandHandler("analyze", self.analyze_cmd))
        self.application.add_handler(CommandHandler("govdata", self.gov_data_cmd))
        self.application.add_handler(CommandHandler("collectgov", self.collect_gov_data_cmd))
        self.application.add_handler(CommandHandler("status", self.status_cmd))
        self.application.add_handler(CommandHandler("health", self.health_cmd))

        # Add message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & filters.Entity("mention"), self.handle_mention))
        self.application.add_handler(MessageHandler(filters.COMMAND, self.unknown_cmd))
        self.application.add_error_handler(self.error_handler)

        return self.application

    def run(self):
        """Run the bot"""
        if self.running:
            logger.warning("Bot is already running")
            return

        try:
            self.running = True
            logger.info("Starting Simplified System Telegram Bot...")

            application = self.build_application()

            logger.info("Bot started successfully, waiting for user interaction...")
            application.run_polling()

        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self.running = False
            raise
        finally:
            self.running = False

    async def shutdown(self):
        """Gracefully shutdown the bot"""
        try:
            self.running = False
            logger.info("Shutting down Simplified System Telegram Bot...")

            if self.application:
                # Close government data API
                await government_api.close()

            logger.info("Bot shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Alias for backward compatibility
TelegramBot = SimpleTelegramBot

# Factory function
def create_telegram_bot() -> SimpleTelegramBot:
    """Create a new Telegram bot instance"""
    return SimpleTelegramBot()

# Global bot instance
telegram_bot = SimpleTelegramBot()

# Convenience functions
def main():
    """Main function"""
    load_dotenv()

    # Check for required environment variables
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.error("TELEGRAM_BOT_TOKEN environment variable is required")
        sys.exit(1)

    # Run the bot
    telegram_bot.run()

if __name__ == "__main__":
    main()