#!/usr/bin/env python3
"""
Telegram量化交易系统Bot
集成完整的量化交易分析功能到Telegram Bot中
"""

import os
import sys
import logging
import asyncio
import json
import requests
import pandas as pd
import numpy as np
from typing import List, Final, Optional, Dict
from collections import deque
import io
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import UpdateType
from telegram.error import RetryAfter, BadRequest
from telegram.ext import (
    AIORateLimiter,
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# 可选依赖：Playwright 截图支持
try:
    from playwright.async_api import async_playwright  # type: ignore
    _PW_OK = True
except Exception:
    _PW_OK = False

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入量化交易系统
try:
    from complete_project_system import (
        get_stock_data, 
        run_strategy_optimization,
        calculate_technical_indicators,
        calculate_risk_metrics,
        calculate_sentiment_analysis
    )
    QUANT_SYSTEM_OK = True
except ImportError as e:
    logging.warning(f"量化交易系统导入失败: {e}")
    QUANT_SYSTEM_OK = False

# ========== 单实例与Webhook工具 ==========
def _acquire_single_instance_lock():
    """尝试通过占用本地端口实现单实例锁。端口可用环境变量覆盖。"""
    try:
        import socket
        port_str = os.getenv('BOT_SINGLETON_PORT', '39217').strip()
        port = int(port_str) if port_str.isdigit() else 39217
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', port))
        s.listen(1)
        logging.info("单实例锁已获取（端口 %s）", port)
        return s  # 保持引用，进程结束时自动释放
    except Exception as e:
        logging.error("无法获取单实例锁：%s", e)
        return None

def _cleanup_webhook(token: str) -> None:
    """删除Webhook，避免与 getUpdates 轮询冲突。"""
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    try:
        resp = requests.get(url, params={"drop_pending_updates": "true"}, timeout=10)
        if resp.status_code == 200 and resp.json().get('ok'):
            logging.info("已删除Webhook（drop_pending_updates=true）")
        else:
            logging.warning("删除Webhook返回非正常：%s", resp.text[:200])
    except Exception as e:
        logging.warning("删除Webhook请求异常：%s", e)

# ---------- Utils ----------
def chunk_text(text: str, limit: int = 4096) -> List[str]:
    if len(text) <= limit:
        return [text]
    parts: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        split = text.rfind("\n", start, end)
        if split == -1:
            split = text.rfind(" ", start, end)
        if split == -1 or split <= start:
            split = end
        parts.append(text[start:split])
        start = split
    return parts

async def reply_long(update: Update, text: str) -> None:
    if update.effective_message is None:
        return
    for part in chunk_text(text, 4096):
        await update.effective_message.reply_text(part)

def format_strategy_results(results: List[Dict], limit: int = 10) -> str:
    """格式化策略优化结果"""
    if not results:
        return "❌ 没有找到有效的策略结果"
    
    text = f"📊 **策略优化结果** (前{min(limit, len(results))}名)\n\n"
    
    for i, result in enumerate(results[:limit], 1):
        text += f"**{i}. {result.get('strategy_name', 'Unknown')}**\n"
        text += f"   Sharpe比率: {result.get('sharpe_ratio', 0):.3f}\n"
        text += f"   年化收益率: {result.get('annual_return', 0):.2f}%\n"
        text += f"   波动率: {result.get('volatility', 0):.2f}%\n"
        text += f"   最大回撤: {result.get('max_drawdown', 0):.2f}%\n"
        text += f"   胜率: {result.get('win_rate', 0):.2f}%\n"
        text += f"   交易次数: {result.get('trade_count', 0)}\n"
        text += f"   最终价值: ¥{result.get('final_value', 0):,.2f}\n\n"
    
    return text

def format_technical_analysis(data: Dict) -> str:
    """格式化技术分析结果"""
    if not data:
        return "❌ 无法获取技术分析数据"
    
    text = "📈 **技术分析结果**\n\n"
    
    # 基本指标
    if 'sma_20' in data:
        text += f"📊 **移动平均线**\n"
        text += f"   SMA(20): {data['sma_20']:.2f}\n"
        text += f"   SMA(50): {data['sma_50']:.2f}\n"
        text += f"   EMA(20): {data['ema_20']:.2f}\n\n"
    
    # RSI
    if 'rsi' in data:
        text += f"📊 **RSI指标**\n"
        text += f"   RSI(14): {data['rsi']:.2f}\n"
        if data['rsi'] > 70:
            text += "   🔴 超买区域\n"
        elif data['rsi'] < 30:
            text += "   🟢 超卖区域\n"
        else:
            text += "   🟡 中性区域\n"
        text += "\n"
    
    # MACD
    if 'macd' in data:
        text += f"📊 **MACD指标**\n"
        text += f"   MACD: {data['macd']:.4f}\n"
        text += f"   Signal: {data['macd_signal']:.4f}\n"
        text += f"   Histogram: {data['macd_histogram']:.4f}\n\n"
    
    # 布林带
    if 'bb_upper' in data:
        text += f"📊 **布林带指标**\n"
        text += f"   上轨: {data['bb_upper']:.2f}\n"
        text += f"   中轨: {data['bb_middle']:.2f}\n"
        text += f"   下轨: {data['bb_lower']:.2f}\n"
        text += f"   当前价格: {data.get('close', 0):.2f}\n\n"
    
    return text

# ---------- AI HTTP 调用（OpenAI 兼容） ----------
async def _call_ai_http(prompt: str, system_prompt: str, *, model_env: str = 'AI_MODEL') -> Optional[str]:
    try:
        import httpx  # type: ignore
    except Exception:
        return None

async def _call_cursor_agents_v0(prompt_text: str) -> Optional[str]:
    """调用 Cursor v0 Agents API：POST /v0/agents
    需环境变量：AI_API_BASE, AI_API_KEY
    可选：AGENT_SOURCE_REPO, AGENT_SOURCE_REF
    """
    try:
        import httpx  # type: ignore
    except Exception:
        return None

    base = os.getenv('AI_API_BASE', '').strip() or 'https://api.cursor.com'
    key = (os.getenv('AI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')).strip()
    if not key:
        return None

    payload: Dict = {
        'prompt': { 'text': prompt_text }
    }
    repo = os.getenv('AGENT_SOURCE_REPO', '').strip()
    ref = os.getenv('AGENT_SOURCE_REF', '').strip()
    if repo:
        payload['source'] = {'repository': repo}
        if ref:
            payload['source']['ref'] = ref  # type: ignore[index]

    def _ascii_safe(text: str) -> str:
        try:
            return text.encode('ascii', 'ignore').decode('ascii', 'ignore')
        except Exception:
            return 'unknown'

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                base.rstrip('/') + '/v0/agents',
                json=payload,
                headers={
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json',
                    'Accept-Charset': 'utf-8',
                },
            )
        if r.status_code != 200:
            txt = r.text if isinstance(r.text, str) else str(r.text)
            return f"Cursor v0 HTTP {r.status_code}: {_ascii_safe(txt)[:300]}"
        data = r.json()
        # 返回体结构可能不同，尽量提取常见字段；否则返回原文片段
        # 例如 data.get('result') 或 data.get('message') 等
        out = (
            data.get('result')
            or data.get('message')
            or data.get('output')
            or r.text
        )
        if isinstance(out, (dict, list)):
            import json as _json
            out = _json.dumps(out, ensure_ascii=False)[:4000]
        return str(out)[:4000]
    except Exception as e:
        return f"Cursor v0 call failed: {_ascii_safe(str(e))}"

    base = os.getenv('AI_API_BASE', '').strip()
    key = (os.getenv('AI_API_KEY', '') or os.getenv('OPENAI_API_KEY', '')).strip()
    model = os.getenv(model_env, '').strip() or 'gpt-4o'
    if not base or not key:
        return None
    try:
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt},
            ],
            'temperature': 0.3,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                base.rstrip('/') + '/v0/chat/completions',
                json=payload,
                headers={'Authorization': f'Bearer {key}'},
            )
        if resp.status_code != 200:
            return f"HTTP {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        return text.strip() or '（无输出）'
    except Exception as e:
        logging.getLogger(__name__).warning('AI HTTP 调用失败: %s', e)
        return None

# ---------- Handlers ----------
def _parse_allowed_user_ids(env_value: Optional[str]) -> Optional[set[int]]:
    if not env_value:
        return None
    try:
        ids = {int(x.strip()) for x in env_value.split(',') if x.strip()}
        return ids or None
    except Exception:
        return None

def _is_allowed_user_and_chat(update: Update) -> bool:
    allowed_u = _parse_allowed_user_ids(os.getenv('TG_ALLOWED_USER_IDS'))
    allowed_c = _parse_allowed_user_ids(os.getenv('TG_ALLOWED_CHAT_IDS'))
    if allowed_u is not None:
        uid = update.effective_user.id if update.effective_user else None
        if uid not in allowed_u:
            return False
    if allowed_c is not None:
        cid = update.effective_chat.id if update.effective_chat else None
        if cid not in allowed_c:
            return False
    return True
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = user.first_name if user and user.first_name else "朋友"
    text = (
        f"嗨 {name}! 👋\n\n"
        "🤖 **量化交易系统Bot**\n\n"
        "📊 **主要功能:**\n"
        "• 股票技术分析\n"
        "• 策略参数优化\n"
        "• 风险评估\n"
        "• 市场情绪分析\n\n"
        "输入 /help 查看所有可用指令"
    )
    await reply_long(update, text)

def build_help_text() -> str:
    lines = [
        "🤖 量化交易系统Bot - 帮助\n",
        "📊 功能分类：",
        "- 技术分析：/analyze <代码>、/risk <代码>、/sentiment <代码>",
        "- 策略优化：/optimize <代码>",
        "- 系统信息：/status、/id、/help",
        "- 实用工具：/echo、/history [n]",
        "- 高级功能：/summary、/cursor、/wsl、/tftcap\n",

        "📈 技术与风险：",
        "/analyze <股票代码>  分析技术指标（SMA/EMA/RSI/MACD/布林带）",
        "/risk <股票代码>      计算 VaR、波动率、最大回撤、风险评分",
        "/sentiment <股票代码> 市场情绪分析（趋势强度/波动情绪）",
        "/optimize <股票代码>  高计算量参数优化（Sharpe最大化）\n",

        "🧰 实用工具：",
        "/echo <文字>          原样回声（仅私聊回应）",
        "/history [n]          查看最近 n 条消息（默认20，上限200）\n",

        "🧠 高级：需要配置与白名单（详见README/规则）",
        "/summary              GPT-5 总结最近消息（需 CURSOR_API_KEY）",
        "/cursor <提示词>      调用 Cursor GPT-5 执行（需白名单与 CURSOR_API_KEY）",
        "/wsl <指令>           在WSL执行白名单命令（高风险，需白名单，可选密钥）",
        "/tftcap               浏览器截图指定区块（需安装 Playwright）\n",

        "🔑 权限与环境：",
        "- 需在虚拟环境(.venv310)与正确路径中运行",
        "- /summary、/cursor、/wsl 仅限白名单与已配置密钥",
        "- 可能需要环境变量：TELEGRAM_BOT_TOKEN、CURSOR_API_KEY\n",

        "💡 示例：",
        "/analyze 0700.HK",
        "/optimize 2800.HK",
        "/risk 0700.HK",
        "/echo hello",
        "/history 10",
        "/summary",
        "/cursor 使用中文总结以下要点…",
    ]
    return "\n".join(lines)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_long(update, build_help_text())

async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """股票技术分析"""
    if not QUANT_SYSTEM_OK:
        await reply_long(update, "❌ 量化交易系统未正确加载，请检查系统配置")
        return
    
    if not context.args:
        await reply_long(update, "用法：/analyze <股票代码>\n例如：/analyze 0700.HK")
        return
    
    symbol = context.args[0].upper()
    await update.effective_message.reply_text(f"🔍 正在分析 {symbol}...")
    
    try:
        # 获取股票数据
        data = get_stock_data(symbol)
        if not data:
            await reply_long(update, f"❌ 无法获取 {symbol} 的股票数据")
            return
        
        # 计算技术指标
        df = pd.DataFrame(data)
        if len(df) < 20:
            await reply_long(update, f"❌ {symbol} 数据不足，需要至少20条记录")
            return
        
        indicators = calculate_technical_indicators(df)
        
        # 格式化结果
        result_text = format_technical_analysis(indicators)
        await reply_long(update, result_text)
        
    except Exception as e:
        logging.error(f"分析 {symbol} 时出错: {e}")
        await reply_long(update, f"❌ 分析 {symbol} 时发生错误: {str(e)}")

async def optimize_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """策略参数优化"""
    if not QUANT_SYSTEM_OK:
        await reply_long(update, "❌ 量化交易系统未正确加载，请检查系统配置")
        return
    
    if not context.args:
        await reply_long(update, "用法：/optimize <股票代码>\n例如：/optimize 0700.HK")
        return
    
    symbol = context.args[0].upper()
    strategy_type = context.args[1] if len(context.args) > 1 else 'all'
    
    await update.effective_message.reply_text(f"🚀 正在为 {symbol} 运行策略优化...\n⏳ 这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 获取股票数据
        data = get_stock_data(symbol)
        if not data:
            await reply_long(update, f"❌ 无法获取 {symbol} 的股票数据")
            return
        
        # 运行策略优化
        results = run_strategy_optimization(data, strategy_type)
        
        if not results:
            await reply_long(update, f"❌ {symbol} 策略优化未找到有效结果")
            return
        
        # 格式化结果
        result_text = f"🎯 **{symbol} 策略优化完成**\n\n"
        result_text += f"📊 测试策略数量: {len(results)}\n"
        result_text += f"🏆 最佳Sharpe比率: {results[0].get('sharpe_ratio', 0):.3f}\n"
        result_text += f"⏰ 优化时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        result_text += format_strategy_results(results, 10)
        
        await reply_long(update, result_text)
        
    except Exception as e:
        logging.error(f"优化 {symbol} 时出错: {e}")
        await reply_long(update, f"❌ 优化 {symbol} 时发生错误: {str(e)}")

async def risk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """风险评估"""
    if not QUANT_SYSTEM_OK:
        await reply_long(update, "❌ 量化交易系统未正确加载，请检查系统配置")
        return
    
    if not context.args:
        await reply_long(update, "用法：/risk <股票代码>\n例如：/risk 0700.HK")
        return
    
    symbol = context.args[0].upper()
    await update.effective_message.reply_text(f"🔍 正在计算 {symbol} 的风险指标...")
    
    try:
        # 获取股票数据
        data = get_stock_data(symbol)
        if not data:
            await reply_long(update, f"❌ 无法获取 {symbol} 的股票数据")
            return
        
        # 计算风险指标
        df = pd.DataFrame(data)
        if len(df) < 20:
            await reply_long(update, f"❌ {symbol} 数据不足，需要至少20条记录")
            return
        
        risk_metrics = calculate_risk_metrics(df)
        
        # 格式化结果
        text = f"⚠️ **{symbol} 风险评估**\n\n"
        text += f"📊 **风险指标:**\n"
        text += f"   VaR(95%): {risk_metrics.get('var_95', 0):.2f}%\n"
        text += f"   VaR(99%): {risk_metrics.get('var_99', 0):.2f}%\n"
        text += f"   最大回撤: {risk_metrics.get('max_drawdown', 0):.2f}%\n"
        text += f"   波动率: {risk_metrics.get('volatility', 0):.2f}%\n"
        text += f"   风险评分: {risk_metrics.get('risk_score', 0):.1f}/10\n\n"
        
        # 风险等级
        risk_score = risk_metrics.get('risk_score', 5)
        if risk_score <= 3:
            text += "🟢 **风险等级: 低风险**\n"
        elif risk_score <= 6:
            text += "🟡 **风险等级: 中等风险**\n"
        else:
            text += "🔴 **风险等级: 高风险**\n"
        
        await reply_long(update, text)
        
    except Exception as e:
        logging.error(f"计算 {symbol} 风险时出错: {e}")
        await reply_long(update, f"❌ 计算 {symbol} 风险时发生错误: {str(e)}")

async def sentiment_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """市场情绪分析"""
    if not QUANT_SYSTEM_OK:
        await reply_long(update, "❌ 量化交易系统未正确加载，请检查系统配置")
        return
    
    if not context.args:
        await reply_long(update, "用法：/sentiment <股票代码>\n例如：/sentiment 0700.HK")
        return
    
    symbol = context.args[0].upper()
    await update.effective_message.reply_text(f"🔍 正在分析 {symbol} 的市场情绪...")
    
    try:
        # 获取股票数据
        data = get_stock_data(symbol)
        if not data:
            await reply_long(update, f"❌ 无法获取 {symbol} 的股票数据")
            return
        
        # 计算情绪分析
        df = pd.DataFrame(data)
        if len(df) < 20:
            await reply_long(update, f"❌ {symbol} 数据不足，需要至少20条记录")
            return
        
        sentiment = calculate_sentiment_analysis(df)
        
        # 格式化结果
        text = f"📊 **{symbol} 市场情绪分析**\n\n"
        text += f"📈 **情绪指标:**\n"
        text += f"   情绪评分: {sentiment.get('sentiment_score', 0):.2f}/10\n"
        text += f"   趋势强度: {sentiment.get('trend_strength', 0):.2f}\n"
        text += f"   波动情绪: {sentiment.get('volatility_sentiment', 0):.2f}\n\n"
        
        # 情绪等级
        score = sentiment.get('sentiment_score', 5)
        if score >= 7:
            text += "🟢 **市场情绪: 乐观**\n"
        elif score >= 4:
            text += "🟡 **市场情绪: 中性**\n"
        else:
            text += "🔴 **市场情绪: 悲观**\n"
        
        await reply_long(update, text)
        
    except Exception as e:
        logging.error(f"分析 {symbol} 情绪时出错: {e}")
        await reply_long(update, f"❌ 分析 {symbol} 情绪时发生错误: {str(e)}")

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """系统状态"""
    text = "🤖 **量化交易系统状态**\n\n"
    
    # 系统状态
    if QUANT_SYSTEM_OK:
        text += "✅ 量化交易系统: 正常运行\n"
    else:
        text += "❌ 量化交易系统: 未加载\n"
    
    # 当前时间
    text += f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    # 系统信息
    text += f"🐍 Python版本: {sys.version.split()[0]}\n"
    text += f"📊 Pandas版本: {pd.__version__}\n"
    text += f"🔢 NumPy版本: {np.__version__}\n"
    
    await reply_long(update, text)

async def echo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await reply_long(update, "用法：/echo <文字>")
        return
    await reply_long(update, " ".join(context.args))

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 仅在私聊回声；群组不回声但记录
    if update.effective_message and update.effective_message.text and (
        update.effective_chat and getattr(update.effective_chat, 'type', None) == 'private'
    ):
        await reply_long(update, update.effective_message.text)
    # 记录最近消息
    buf: deque = context.chat_data.get("recent_msgs")  # type: ignore[assignment]
    if buf is None:
        buf = deque(maxlen=200)
        context.chat_data["recent_msgs"] = buf
    user = update.effective_user
    author = (user.username and f"@{user.username}") or (user.first_name if user else "?")
    text = update.effective_message.text if update.effective_message else ""
    if text:
        buf.append({"author": author, "text": text})

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        n = int(context.args[0]) if context.args else 20
    except Exception:
        n = 20
    n = max(1, min(n, 200))
    buf: deque = context.chat_data.get("recent_msgs")  # type: ignore[assignment]
    items: List[Dict[str, str]] = list(buf)[-n:] if buf else []
    if not items:
        await reply_long(update, "目前没有可用的历史消息。")
        return
    lines: List[str] = [f"最近 {len(items)} 条消息（由旧到新）："]
    for it in items:
        author = it.get("author", "?")
        t = it.get("text", "")
        if len(t) > 300:
            t = t[:300] + "…"
        lines.append(f"- {author}: {t}")
    out = "\n".join(lines)
    if len(out) > 3500:
        out = out[:3500] + "\n…（输出过长，已截断）"
    await reply_long(update, out)

async def summary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    # 白名单（可选）
    allowed = _parse_allowed_user_ids(os.getenv('SUMMARY_ALLOWED_USER_IDS') or os.getenv('TG_ALLOWED_USER_IDS'))
    if allowed is not None:
        uid = update.effective_user.id if update.effective_user else None
        if uid not in allowed:
            await reply_long(update, "你没有使用 /summary 的权限。")
            return
    allowed_chats = _parse_allowed_user_ids(os.getenv('SUMMARY_ALLOWED_CHAT_IDS') or os.getenv('TG_ALLOWED_CHAT_IDS'))
    if allowed_chats is not None and chat_id not in allowed_chats:
        await reply_long(update, "此群未被授权使用 /summary。")
        return

    buf: deque = context.chat_data.get("recent_msgs")  # type: ignore[assignment]
    items: List[Dict[str, str]] = list(buf)[-50:] if buf else []
    if not items:
        await reply_long(update, "目前没有可用的历史消息（请先在群内对话后再试）。")
        return

    lines = [
        "你是群组对话的摘要助手，请用简明条列整理重点、结论与后续建议。",
        "--- 近期对话（由旧到新） ---",
    ]
    for it in items:
        author = it.get("author", "?")
        t = it.get("text", "")
        lines.append(f"{author}: {t}")
    lines.append("--- 请输出：\n1) 重点摘要（3-6 点）\n2) 共识/结论\n3) 待办与建议")
    prompt = "\n".join(lines)

    # 优先走 HTTP（Cursor v0 Agents 或 OpenAI 兼容）
    if (os.getenv('AI_API_MODE', '').strip().lower() == 'agents_v0'):
        text = await _call_cursor_agents_v0(prompt)
        if isinstance(text, str):
            await reply_long(update, text)
            return
    http_text = await _call_ai_http(prompt, '你是对话摘要助手，请用简洁中文条列输出重点、结论与建议。')
    if isinstance(http_text, str):
        await reply_long(update, http_text)
        return

    # 与 CURSOR CLI 对齐：使用 cursor-agent 二进制，传 -m/-a 与 --print/--output-format
    cursor_key = os.getenv('CURSOR_API_KEY', '').strip()
    if not cursor_key:
        await reply_long(update, "未设置 AI_API_BASE/AI_API_KEY，且缺少 CURSOR_API_KEY，无法执行。")
        return

    # 与环境兼容：不使用 -m/-a，改由环境变量传递
    bin_name = os.getenv('CURSOR_AGENT_BIN', 'cursor-agent')
    cursor_model = os.getenv('CURSOR_MODEL', '').strip() or os.getenv('AI_MODEL', '').strip() or 'gpt-5'
    base_args = [bin_name, '--print', '--output-format', 'text']

    async def _run_cmd(cmd: List[str]) -> Optional[str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'CURSOR_API_KEY': cursor_key, 'CURSOR_MODEL': cursor_model},
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(input=prompt.encode('utf-8')), timeout=60.0)
            if proc.returncode != 0:
                return f"执行失败：{stderr.decode('utf-8','ignore').strip() or '未知错误'}"
            return stdout.decode('utf-8', 'ignore').strip() or '（无输出）'
        except FileNotFoundError:
            # 尝试通过 bash -lc（兼容 WSL/类Unix 安装）
            try:
                shell_line = ' '.join(cmd)
                proc = await asyncio.create_subprocess_exec(
                    'bash', '-lc', shell_line,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, 'CURSOR_API_KEY': cursor_key, 'CURSOR_MODEL': cursor_model},
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(input=prompt.encode('utf-8')), timeout=60.0)
                if proc.returncode != 0:
                    return f"执行失败：{stderr.decode('utf-8','ignore').strip() or '未知错误'}"
                return stdout.decode('utf-8', 'ignore').strip() or '（无输出）'
            except Exception as e2:
                return f"找不到可执行文件（请安装 cursor-agent 或设置 CURSOR_AGENT_BIN）：{e2}"
        except asyncio.TimeoutError:
            return "执行超时（60 秒）。"
        except Exception as e:
            return f"执行发生异常：{e}"

    out = await _run_cmd(base_args)
    await reply_long(update, out or '执行失败')

async def cursor_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    # 专用白名单（优先），无设置时回退通用 TG_ALLOWED_*
    allowed = _parse_allowed_user_ids(os.getenv('CURSOR_ALLOWED_USER_IDS') or os.getenv('TG_ALLOWED_USER_IDS'))
    if allowed is not None:
        uid = update.effective_user.id if update.effective_user else None
        if uid not in allowed:
            await reply_long(update, "你没有使用 /cursor 的权限。")
            return
    allowed_chats = _parse_allowed_user_ids(os.getenv('CURSOR_ALLOWED_CHAT_IDS') or os.getenv('TG_ALLOWED_CHAT_IDS'))
    if allowed_chats is not None and chat_id not in allowed_chats:
        await reply_long(update, "此群未被授权使用 /cursor。")
        return

    if not context.args:
        await reply_long(update, "用法：/cursor <提示词>")
        return
    prompt = " ".join(context.args).strip()
    if not prompt:
        await reply_long(update, "用法：/cursor <提示词>")
        return

    # 优先走 HTTP（Cursor v0 Agents 或 OpenAI 兼容）
    if (os.getenv('AI_API_MODE', '').strip().lower() == 'agents_v0'):
        text = await _call_cursor_agents_v0(prompt)
        if isinstance(text, str):
            await reply_long(update, text)
            return
    http_text = await _call_ai_http(prompt, '你是一个中文助理，请用简洁中文回答用户问题。')
    if isinstance(http_text, str):
        await reply_long(update, http_text)
        return

    # 与 CURSOR CLI 对齐本地模式
    cursor_key = os.getenv('CURSOR_API_KEY', '').strip()
    if not cursor_key:
        await reply_long(update, "未设置 AI_API_BASE/AI_API_KEY，且缺少 CURSOR_API_KEY，本功能不可用。")
        return

    bin_name = os.getenv('CURSOR_AGENT_BIN', 'cursor-agent')
    cursor_model = os.getenv('CURSOR_MODEL', '').strip() or os.getenv('AI_MODEL', '').strip() or 'gpt-5'
    base_args = [bin_name, '--print', '--output-format', 'text']

    async def _run_cmd(cmd: List[str]) -> Optional[str]:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, 'CURSOR_API_KEY': cursor_key, 'CURSOR_MODEL': cursor_model},
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(input=prompt.encode('utf-8')), timeout=60.0)
            if proc.returncode != 0:
                return f"执行失败：{stderr.decode('utf-8','ignore').strip() or '未知错误'}"
            return stdout.decode('utf-8', 'ignore').strip() or '（无输出）'
        except FileNotFoundError:
            try:
                shell_line = ' '.join(cmd)
                proc = await asyncio.create_subprocess_exec(
                    'bash', '-lc', shell_line,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={**os.environ, 'CURSOR_API_KEY': cursor_key, 'CURSOR_MODEL': cursor_model},
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(input=prompt.encode('utf-8')), timeout=60.0)
                if proc.returncode != 0:
                    return f"执行失败：{stderr.decode('utf-8','ignore').strip() or '未知错误'}"
                return stdout.decode('utf-8', 'ignore').strip() or '（无输出）'
            except Exception as e2:
                return f"找不到可执行文件（请安装 cursor-agent 或设置 CURSOR_AGENT_BIN）：{e2}"
        except asyncio.TimeoutError:
            return "执行超时（60 秒）。"
        except Exception as e:
            return f"执行发生异常：{e}"

    out = await _run_cmd(base_args)
    await reply_long(update, out or '执行失败')

async def tftcap_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _PW_OK:
        await reply_long(update, (
            "尚未安装 Playwright。请先执行：\n"
            "pip install playwright && python -m playwright install chromium\n"
            "（WSL/服务器可能需 --with-deps）"
        ))
        return

    url = "https://tactics.tools/team-compositions"
    base_xpath = os.getenv(
        "TFT_XPATH_BASE",
        "/html/body/div[1]/div/div/div/div[2]/div/div[6]/div[2]/div/div[2]/div[2]/div[2]",
    ).strip()

    import re as _re
    m = list(_re.finditer(r"\[(\d+)\]", base_xpath))
    if not m:
        xpaths = [base_xpath]
    else:
        last = m[-1]
        prefix = base_xpath[: last.start(1)]
        suffix = base_xpath[last.end(1) :]
        xpaths = [f"{prefix}{i}{suffix}" for i in range(1, 5)]

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])  # type: ignore
            ctx = await browser.new_context(viewport={"width": 1400, "height": 1200}, device_scale_factor=2)
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle", timeout=45000)

            sent = 0
            for xp in xpaths:
                loc = page.locator(f"xpath={xp}")
                if await loc.count() == 0:
                    continue
                item = loc.first
                try:
                    await item.scroll_into_view_if_needed()
                    img_bytes = await item.screenshot(type="png")
                    bio = io.BytesIO(img_bytes)
                    bio.name = "tft.png"
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio)
                    sent += 1
                except Exception:
                    continue

            await ctx.close()
            await browser.close()
    except Exception as e:
        logging.getLogger(__name__).exception("/tftcap 截图错误: %s", e)

async def wsl_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # 高风险：需要白名单与可选密钥
    if not _is_allowed_user_and_chat(update):
        await reply_long(update, "此对话未被授权使用 /wsl。")
        return
    if not context.args:
        await reply_long(update, "用法：/wsl <指令>\n例如：/wsl ls -la ~")
        return

    prefixes = os.getenv(
        'WSL_ALLOWED_PREFIXES',
        'ls,cat,head,tail,grep,uname,df,du,free,uptime,whoami,pwd,echo,python3,python',
    )
    allowed = {p.strip() for p in prefixes.split(',') if p.strip()}
    user_cmd = " ".join(context.args).strip()
    first_token = user_cmd.split()[0]
    if first_token not in allowed:
        await reply_long(update, f"此指令不在白名单：{first_token}")
        return

    shared = os.getenv('WSL_SHARED_SECRET')
    if shared:
        parts = user_cmd.split()
        if len(parts) < 2 or parts[1] != shared:
            await reply_long(update, "缺少或错误的授权密钥。格式：/wsl <cmd> <SECRET> [args...]")
            return
        user_cmd = " ".join([parts[0]] + parts[2:])

    bash_cmd = ['bash', '-lc', user_cmd]
    try:
        proc = await asyncio.create_subprocess_exec(
            *bash_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=20.0)
        except asyncio.TimeoutError:
            proc.kill()
            await reply_long(update, "执行超时（20 秒）。")
            return
        out = stdout.decode('utf-8', 'ignore')
        err = stderr.decode('utf-8', 'ignore')
        text = (out if out.strip() else '') + ("\n" + err if err.strip() else '')
        text = text.strip() or "（无输出）"
        if len(text) > 3500:
            text = text[:3500] + "\n...（输出过长，已截断）"
        await reply_long(update, text)
    except Exception as e:
        logging.getLogger(__name__).exception("/wsl 执行错误: %s", e)
        await reply_long(update, "执行发生异常。")

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    cid = chat.id if chat else None
    ctype = getattr(chat, "type", None)
    title = getattr(chat, "title", None) or getattr(chat, "username", None) or getattr(chat, "first_name", None)
    uid = user.id if user else None
    uname = getattr(user, "username", None)
    text = (
        f"chat_id = {cid}\n"
        f"chat_type = {ctype}\n"
        f"chat_title = {title}\n"
        f"user_id = {uid}\n"
        f"username = @{uname}" if uname else f"user_id = {uid}"
    )
    await reply_long(update, text)

async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await reply_long(update, "未知指令。使用 /help 查看可用指令。")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        raise context.error  # type: ignore[misc]
    except RetryAfter as e:
        await context.application.bot.send_message(
            chat_id=update.effective_chat.id if isinstance(update, Update) and update.effective_chat else None,
            text=f"被限流，{getattr(e, 'retry_after', 1)} 秒後重試…",
        )
    except BadRequest:
        pass
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).exception("未處理錯誤: %s", e)

# ---------- App wiring ----------
async def post_init(app: Application) -> None:
    commands = [
        BotCommand("start", "问候与简介"),
        BotCommand("help", "显示帮助"),
        BotCommand("analyze", "股票技术分析"),
        BotCommand("optimize", "策略参数优化"),
        BotCommand("risk", "风险评估"),
        BotCommand("sentiment", "市场情绪分析"),
        BotCommand("status", "系统状态"),
        BotCommand("id", "显示ID信息"),
        BotCommand("echo", "原样回声（仅私聊回应）"),
        BotCommand("history", "查看最近消息"),
        BotCommand("summary", "总结最近消息（需API Key）"),
        BotCommand("cursor", "调用 Cursor（需白名单与API Key）"),
        BotCommand("wsl", "在WSL执行（需白名单）"),
        BotCommand("tftcap", "浏览器截图（需Playwright）"),
    ]
    await app.bot.set_my_commands(commands)

def build_app(token: str) -> Application:
    app = (
        Application.builder()
        .token(token)
        .rate_limiter(AIORateLimiter())
        .post_init(post_init)
        .build()
    )

    # 添加命令处理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("analyze", analyze_cmd))
    app.add_handler(CommandHandler("optimize", optimize_cmd))
    app.add_handler(CommandHandler("risk", risk_cmd))
    app.add_handler(CommandHandler("sentiment", sentiment_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("echo", echo_cmd))
    app.add_handler(CommandHandler("history", history_cmd))
    app.add_handler(CommandHandler("summary", summary_cmd))
    app.add_handler(CommandHandler("cursor", cursor_cmd))
    app.add_handler(CommandHandler("wsl", wsl_cmd))
    app.add_handler(CommandHandler("tftcap", tftcap_cmd))

    # 文本消息与未知命令处理
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))
    app.add_error_handler(error_handler)

    return app

def main() -> None:
    load_dotenv()

    # 日志配置
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # 单实例锁：占用本地端口，避免重复运行
    _lock_sock = _acquire_single_instance_lock()
    if _lock_sock is None:
        logging.critical("已检测到另一实例在运行，退出以避免冲突。")
        raise SystemExit(1)

    token: Final[str] = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        logging.critical("未设置 TELEGRAM_BOT_TOKEN 环境变量")
        raise SystemExit(1)

    # 启动前自动删除Webhook，避免与轮询冲突
    try:
        _cleanup_webhook(token)
    except Exception as e:
        logging.warning("删除Webhook失败（忽略继续）：%s", e)

    app = build_app(token)
    logging.info("🤖 量化交易系统Bot启动中...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=[UpdateType.MESSAGE],
    )

if __name__ == "__main__":
    main()

# ========== 单实例与Webhook工具 ==========
def _acquire_single_instance_lock():
    """尝试通过占用本地端口实现单实例锁。端口可用环境变量覆盖。"""
    try:
        import socket
        port_str = os.getenv('BOT_SINGLETON_PORT', '39217').strip()
        port = int(port_str) if port_str.isdigit() else 39217
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', port))
        s.listen(1)
        logging.info("单实例锁已获取（端口 %s）", port)
        return s  # 保持引用，进程结束时自动释放
    except Exception as e:
        logging.error("无法获取单实例锁：%s", e)
        return None

def _cleanup_webhook(token: str) -> None:
    """删除Webhook，避免与 getUpdates 轮询冲突。"""
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    try:
        resp = requests.get(url, params={"drop_pending_updates": "true"}, timeout=10)
        if resp.status_code == 200 and resp.json().get('ok'):
            logging.info("已删除Webhook（drop_pending_updates=true）")
        else:
            logging.warning("删除Webhook返回非正常：%s", resp.text[:200])
    except Exception as e:
        logging.warning("删除Webhook请求异常：%s", e)
