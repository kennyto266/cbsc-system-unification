"""
AI 擴展功能模塊
為 Telegram Bot 提供更多專業化 AI 功能
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from .glm46_integration import get_glm46_instance


class AIExtensions:
    """AI 擴展功能類"""

    def __init__(self):
        self.glm46 = get_glm46_instance()
        self.logger = logging.getLogger(__name__)

        # 用戶會話記憶（簡化版）
        self.user_sessions = {}
        self.session_ttl = 1800  # 30分鐘過期

    async def analyze_stock(self, symbol: str) -> Optional[str]:
        """深度分析單個股票"""
        system_prompt = """您是一位專業的港股分析師。請基於提供的股票代碼進行全面分析。

分析內容應包括：
1. 公司基本面分析
2. 技術指標分析
3. 行業地位評估
4. 風險因素提示
5. 投資建議（買入 / 持有 / 賣出）
6. 目標價格區間

請使用繁體中文回應，控制在200字內。"""

        user_message = f"請詳細分析港股 {symbol} 的投資價值，包括技術面和基本面分析。"

        try:
            response = await self.glm46.chat_completion(user_message, system_prompt)
            return response
        except Exception as e:
            self.logger.error(f"股票分析失敗: {e}")
            return "抱歉，股票分析暫時無法使用，請稍後再試。"

    async def portfolio_advice(self, stocks: List[str]) -> Optional[str]:
        """投資組合建議"""
        system_prompt = """您是一位專業的投資組合經理。請基於提供的股票列表給出投資組合建議。

分析內容：
1. 投資組合風險評估
2. 資產配置建議
3. 個股權重建議
4. 止損策略建議
5. 預期收益範圍

請使用繁體中文回應，控制在250字內。"""

        stocks_str = ", ".join(stocks)
        user_message = f"請為以下股票提供投資組合建議：{stocks_str}"

        try:
            response = await self.glm46.chat_completion(user_message, system_prompt)
            return response
        except Exception as e:
            self.logger.error(f"投資組合分析失敗: {e}")
            return "抱歉，投資組合分析暫時無法使用，請稍後再試。"

    async def risk_assessment(self, strategy_description: str) -> Optional[str]:
        """投資策略風險評估"""
        system_prompt = """您是一位專業的風險管理專家。請評估提供的投資策略的風險。

評估內容：
1. 策略風險等級（低 / 中 / 高）
2. 主要風險因素
3. 風險控制建議
4. 適合人群評估
5. 最大可能損失估算

請使用繁體中文回應，控制在200字內。"""

        user_message = f"請評估以下投資策略的風險：{strategy_description}"

        try:
            response = await self.glm46.chat_completion(user_message, system_prompt)
            return response
        except Exception as e:
            self.logger.error(f"風險評估失敗: {e}")
            return "抱歉，風險評估暫時無法使用，請稍後再試。"

    async def market_sentiment(self, keyword: str) -> Optional[str]:
        """市場情緒分析"""
        system_prompt = """您是一位市場情緒分析專家。請基於關鍵詞分析當前市場情緒。

分析內容：
1. 市場情緒指數（0 - 100）
2. 情緒傾向（樂觀 / 中性 / 悲觀）
3. 影響因素分析
4. 短期預測
5. 投資建議

請使用繁體中文回應，控制在150字內。"""

        user_message = f"請分析關於「{keyword}」的市場情緒"

        try:
            response = await self.glm46.chat_completion(user_message, system_prompt)
            return response
        except Exception as e:
            self.logger.error(f"市場情緒分析失敗: {e}")
            return "抱歉，市場情緒分析暫時無法使用，請稍後再試。"

    async def strategy_recommendation(self, market_conditions: str) -> Optional[str]:
        """智能策略推薦"""
        system_prompt = """您是一位量化交易策略專家。請基於市場條件推薦合適的交易策略。

推薦內容：
1. 策略類型建議
2. 適合的時間週期
3. 關鍵技術指標
4. 入場和出場條件
5. 風險控制參數

請使用繁體中文回應，控制在200字內。"""

        user_message = f"當前市場條件：{market_conditions}，請推薦適合的交易策略"

        try:
            response = await self.glm46.chat_completion(user_message, system_prompt)
            return response
        except Exception as e:
            self.logger.error(f"策略推薦失敗: {e}")
            return "抱歉，策略推薦暫時無法使用，請稍後再試。"

    def _update_user_session(self, user_id: int, context: Dict[str, Any]):
        """更新用戶會話記憶"""
        self.user_sessions[user_id] = {"context": context, "timestamp": datetime.now()}

        # 清理過期會話
        self._cleanup_expired_sessions()

    def _get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """獲取用戶會話"""
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            if datetime.now() - session["timestamp"] < timedelta(
                seconds=self.session_ttl
            ):
                return session["context"]
            else:
                del self.user_sessions[user_id]
        return None

    def _cleanup_expired_sessions(self):
        """清理過期會話"""
        current_time = datetime.now()
        expired_users = []

        for user_id, session in self.user_sessions.items():
            if current_time - session["timestamp"] > timedelta(
                seconds=self.session_ttl
            ):
                expired_users.append(user_id)

        for user_id in expired_users:
            del self.user_sessions[user_id]

    async def contextual_response(self, user_id: int, message: str) -> Optional[str]:
        """基於上下文的回應"""
        # 獲取用戶會話上下文
        context = self._get_user_session(user_id) or {}

        # 構建包含上下文的系統提示
        system_prompt = """您是一位專業的投資顧問助手。請基於對話歷史提供個性化的回應。

回應要求：
- 保持專業和友好的語氣
- 考慮用戶之前的問題和偏好
- 提供實用且可操作的建議
- 使用繁體中文回應，控制在150字內。"""

        # 添加上下文信息
        if context:
            context_info = f"用戶之前的對話：{context}"
            user_message = f"{context_info}\n\n當前問題：{message}"
        else:
            user_message = message

        try:
            response = await self.glm46.chat_completion(user_message, system_prompt)

            # 更新會話記憶
            new_context = {
                "last_question": message,
                "last_response": response,
                "conversation_count": context.get("conversation_count", 0) + 1,
            }
            self._update_user_session(user_id, new_context)

            return response
        except Exception as e:
            self.logger.error(f"上下文回應失敗: {e}")
            return "抱歉，處理您的請求時遇到問題，請稍後再試。"


# 全局實例
_ai_extensions_instance: Optional[AIExtensions] = None


def get_ai_extensions() -> AIExtensions:
    """獲取 AI 擴展實例"""
    global _ai_extensions_instance
    if _ai_extensions_instance is None:
        _ai_extensions_instance = AIExtensions()
    return _ai_extensions_instance


# Telegram Bot 命令處理函數
async def ai_analyze_cmd(update, context):
    """分析股票命令 /ai_analyze <股票代碼>"""
    if not context.args:
        await update.message.reply_text(
            "用法：/ai_analyze <股票代碼>\n例如：/ai_analyze 0700.HK"
        )
        return

    symbol = context.args[0].upper()
    await update.message.reply_text(f"正在分析 {symbol}，請稍候...")

    try:
        ai_ext = get_ai_extensions()
        response = await ai_ext.analyze_stock(symbol)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"AI 分析失敗: {e}")
        await update.message.reply_text("分析失敗，請稍後再試。")


async def ai_portfolio_cmd(update, context):
    """投資組合建議命令 /ai_portfolio <股票1,股票2,...>"""
    if not context.args:
        await update.message.reply_text(
            "用法：/ai_portfolio <股票1,股票2,...>\n例如：/ai_portfolio 0700.HK,9988.HK,1398.HK"
        )
        return

    stocks = [arg.upper().replace(",", "") for arg in context.args]
    await update.message.reply_text(f"正在分析投資組合 {', '.join(stocks)}，請稍候...")

    try:
        ai_ext = get_ai_extensions()
        response = await ai_ext.portfolio_advice(stocks)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"投資組合分析失敗: {e}")
        await update.message.reply_text("分析失敗，請稍後再試。")


async def ai_risk_cmd(update, context):
    """風險評估命令 /ai_risk <策略描述>"""
    if not context.args:
        await update.message.reply_text(
            "用法：/ai_risk <策略描述>\n例如：/ai_risk 我計劃用30 % 資金投資港股科技股"
        )
        return

    strategy = " ".join(context.args)
    await update.message.reply_text("正在評估策略風險，請稍候...")

    try:
        ai_ext = get_ai_extensions()
        response = await ai_ext.risk_assessment(strategy)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"風險評估失敗: {e}")
        await update.message.reply_text("評估失敗，請稍後再試。")


async def ai_news_cmd(update, context):
    """新聞情緒分析命令 /ai_news <關鍵詞>"""
    if not context.args:
        await update.message.reply_text(
            "用法：/ai_news <關鍵詞>\n例如：/ai_news 恆生指數"
        )
        return

    keyword = " ".join(context.args)
    await update.message.reply_text(f"正在分析「{keyword}」的市場情緒，請稍候...")

    try:
        ai_ext = get_ai_extensions()
        response = await ai_ext.market_sentiment(keyword)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"市場情緒分析失敗: {e}")
        await update.message.reply_text("分析失敗，請稍後再試。")


async def ai_strategy_cmd(update, context):
    """策略推薦命令 /ai_strategy <市場條件>"""
    if not context.args:
        await update.message.reply_text(
            "用法：/ai_strategy <市場條件>\n例如：/ai_strategy 港股持續下跌，市場恐慌"
        )
        return

    conditions = " ".join(context.args)
    await update.message.reply_text("正在生成策略建議，請稍候...")

    try:
        ai_ext = get_ai_extensions()
        response = await ai_ext.strategy_recommendation(conditions)
        await update.message.reply_text(response)
    except Exception as e:
        logging.error(f"策略推薦失敗: {e}")
        await update.message.reply_text("推薦失敗，請稍後再試。")
