import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx


BASE_URL = os.environ.get("DASHBOARD_BASE_URL", "http://localhost:8000")


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tg_polling")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🤖 Bot online. Use /cursor_help or /integration_status.")


async def cmd_cursor_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🤖 Cursor CLI Integration Help\n\n"
        "Available Commands:\n"
        "/cursor_help - This help message\n"
        "/integration_status - Show integration status\n"
    )
    await update.message.reply_text(text)


async def cmd_integration_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📊 Integration Status\n\n"
        "Status: 🟢 Online\n"
        "Components: Bot polling active\n"
    )
    await update.message.reply_text(text)


# --- Integrated demo commands ---
async def cmd_trading_signals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 使用后端 /strategies/active 作为信号来源（示例）
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BASE_URL}/strategies/active")
            data = r.json()
        except Exception as e:
            await update.message.reply_text(f"❌ 获取策略失败: {e}")
            return
    strategies = data.get("strategies", [])
    if not strategies:
        await update.message.reply_text("📊 没有活跃策略/信号")
        return
    lines = ["📊 Active Strategies\n"]
    for s in strategies[:10]:
        sid = s.get("strategy_id", "unknown")
        lines.append(f"• {sid}")
    await update.message.reply_text("\n".join(lines))


async def cmd_portfolio_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BASE_URL}/portfolio/current")
            p = r.json()
        except Exception as e:
            await update.message.reply_text(f"❌ 获取投资组合失败: {e}")
            return
    total = p.get("total_value", 0)
    text = (
        "💼 Portfolio Status\n\n"
        f"Total Value: HKD {total:,.2f}\n"
    )
    await update.message.reply_text(text)


async def cmd_agent_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BASE_URL}/agents/status")
            data = r.json()
        except Exception as e:
            await update.message.reply_text(f"❌ 获取Agent状态失败: {e}")
            return
    agents = data.get("agents", [])
    if not agents:
        await update.message.reply_text("🤖 没有可用的 Agent 状态")
        return
    lines = ["🤖 Agent Status\n"]
    for a in agents[:10]:
        status_emoji = "🟢" if a.get("status") in ("running","active") else "🔴"
        lines.append(f"{status_emoji} {a.get('name', a.get('agent_id','unknown'))}")
    await update.message.reply_text("\n".join(lines))


async def cmd_system_metrics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BASE_URL}/monitoring/metrics")
            data = r.json()
        except Exception as e:
            await update.message.reply_text(f"❌ 获取系统指标失败: {e}")
            return
    m = data.get("system_metrics", {})
    text = (
        "📊 System Metrics\n\n"
        f"CPU Usage: {m.get('cpu_usage',0):.1f}%\n"
        f"Memory Usage: {m.get('memory_usage',0):.1f}%\n"
    )
    await update.message.reply_text(text)


async def cmd_risk_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.get(f"{BASE_URL}/alerts/active")
            data = r.json()
        except Exception as e:
            await update.message.reply_text(f"❌ 获取风险告警失败: {e}")
            return
    alerts = data.get("alerts", [])
    if not alerts:
        await update.message.reply_text("🚨 当前没有活动告警")
        return
    lines = ["🚨 Risk Alerts\n"]
    for a in alerts[:10]:
        lvl = a.get('level','INFO').upper()
        emoji = {'INFO':'ℹ️','WARNING':'⚠️','CRITICAL':'🚨'}.get(lvl,'ℹ️')
        lines.append(f"{emoji} {lvl}\n   {a.get('message','')}\n")
    await update.message.reply_text("\n".join(lines))


def main():
    env_path = os.environ.get("ENV_PATH", "config/bot.env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")

    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("cursor_help", cmd_cursor_help))
    app.add_handler(CommandHandler("integration_status", cmd_integration_status))
    app.add_handler(CommandHandler("trading_signals", cmd_trading_signals))
    app.add_handler(CommandHandler("portfolio_status", cmd_portfolio_status))
    app.add_handler(CommandHandler("agent_status", cmd_agent_status))
    app.add_handler(CommandHandler("system_metrics", cmd_system_metrics))
    app.add_handler(CommandHandler("risk_alerts", cmd_risk_alerts))

    logger.info("Starting polling... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()


